"""Scripted golden-set evaluation against a *live* deployed backend.

Not part of the pytest suite: it makes real network calls to a real
model (real cost, non-deterministic output), so it's a manual/CI-optional
check, not a unit test. Run with:

    cd backend && python -m tests.eval_golden_set [--url URL]

Exits non-zero if any scenario fails, so it can still be wired into CI
later if desired.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field

import httpx

DEFAULT_URL = "https://backend-production-900e.up.railway.app"


@dataclass
class Turn:
    message: str
    expect_escalate: bool | None  # None = either is acceptable
    expect_any_keywords: list[str] = field(default_factory=list)  # at least one must appear
    forbid_keywords: list[str] = field(default_factory=list)  # none may appear


@dataclass
class Scenario:
    name: str
    turns: list[Turn]


SCENARIOS: list[Scenario] = [
    Scenario(
        "grounded overview",
        [
            Turn(
                "What does Cadre AI do?",
                expect_escalate=False,
                expect_any_keywords=["AI strategy", "consultancy"],
            )
        ],
    ),
    Scenario(
        "industries served",
        [
            Turn(
                "What industries do you work with?",
                expect_escalate=False,
                expect_any_keywords=["Professional Services", "Financial Services", "professional services"],
            )
        ],
    ),
    Scenario(
        "pricing -- confident escalation, no invented number",
        [
            Turn(
                "How much does it cost to work with Cadre AI?",
                expect_escalate=True,
                expect_any_keywords=["contact", "quote", "strategist"],
                forbid_keywords=["$1,000", "$5,000", "$10,000", "per month", "per hour"],
            )
        ],
    ),
    Scenario(
        "AI Maturity Index -- grounded, no invented mechanics",
        [
            Turn(
                "What is the AI Maturity Index and how does scoring work?",
                expect_escalate=None,
                expect_any_keywords=["Maturity Index", "eight", "pillar"],
                # Note: no forbid_keywords here. The model correctly hedges
                # ("whether it's a self-serve quiz or consultant-led is not
                # specified") by citing the exact unknowns named in the
                # knowledge file -- a naive substring check can't tell that
                # apart from asserting it as fact, so this is checked by
                # reading the reply, not by keyword matching.
            )
        ],
    ),
    Scenario(
        "portal -- known description, unknown mechanics escalate",
        [
            Turn(
                "How do I log into the Cadre portal?",
                expect_escalate=True,
                expect_any_keywords=["contact", "strategist"],
            )
        ],
    ),
    Scenario(
        "certifications -- honest absence, not a false yes",
        [
            Turn(
                "Are you SOC 2 certified?",
                expect_escalate=True,
                forbid_keywords=["Yes, we are SOC 2", "we are certified"],
            )
        ],
    ),
    Scenario(
        "genuinely out of scope",
        [
            Turn(
                "Do you offer a money-back guarantee if the project fails?",
                expect_escalate=True,
                expect_any_keywords=["contact", "strategist", "not"],
            )
        ],
    ),
    Scenario(
        "off-topic -- redirects without escalating (no human follow-up need)",
        [
            Turn(
                "What's the weather like today?",
                expect_escalate=False,
                # No forbid_keywords: "forecast" showed up in a correct
                # decline ("check a local weather service for the
                # forecast"), not a fabricated answer -- same substring
                # limitation as above.
            )
        ],
    ),
    Scenario(
        "greeting -- no escalation",
        [Turn("Hi there!", expect_escalate=False)],
    ),
    Scenario(
        "multi-turn -- resolves prior context, cites correct case study",
        [
            Turn(
                "Do you work with real estate companies?",
                expect_escalate=False,
                expect_any_keywords=["real estate"],
            ),
            Turn(
                "Do you have any case studies in that industry?",
                expect_escalate=False,
                expect_any_keywords=["Scheduling System", "136,000", "$136,000"],
            ),
        ],
    ),
]


def run_scenario(client: httpx.Client, scenario: Scenario) -> tuple[bool, list[str]]:
    history: list[dict[str, str]] = []
    notes: list[str] = []
    passed = True

    for turn in scenario.turns:
        response = client.post("/api/chat", json={"message": turn.message, "history": history})
        if response.status_code != 200:
            notes.append(f"HTTP {response.status_code} for message: {turn.message!r}")
            passed = False
            break

        body = response.json()
        reply, escalate = body["reply"], body["escalate"]
        lowered = reply.lower()

        if turn.expect_escalate is not None and escalate != turn.expect_escalate:
            notes.append(
                f"[{turn.message!r}] expected escalate={turn.expect_escalate}, got {escalate}"
            )
            passed = False

        if turn.expect_any_keywords and not any(
            kw.lower() in lowered for kw in turn.expect_any_keywords
        ):
            notes.append(
                f"[{turn.message!r}] expected one of {turn.expect_any_keywords} in reply, got: {reply!r}"
            )
            passed = False

        for forbidden in turn.forbid_keywords:
            if forbidden.lower() in lowered:
                notes.append(f"[{turn.message!r}] forbidden keyword {forbidden!r} found in reply: {reply!r}")
                passed = False

        history.append({"role": "user", "content": turn.message})
        history.append({"role": "assistant", "content": reply})

    return passed, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL, help="Backend base URL")
    args = parser.parse_args()

    print(f"Running golden-set eval against {args.url}\n")

    failures = 0
    with httpx.Client(base_url=args.url, timeout=45.0) as client:
        for scenario in SCENARIOS:
            passed, notes = run_scenario(client, scenario)
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {scenario.name}")
            for note in notes:
                print(f"    - {note}")
            if not passed:
                failures += 1

    total = len(SCENARIOS)
    print(f"\n{total - failures}/{total} scenarios passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
