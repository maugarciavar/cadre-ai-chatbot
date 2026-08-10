# plan.md

## Goal
Ship a deployed, publicly accessible Cadre AI support chatbot inside a
4–6 hour budget, following plan -> build -> deploy -> iterate, in small
verifiable phases with early deployment.

## Scope
See CLAUDE.md "Out of scope" for the full list and reasoning. In scope:
chat UI, stateless `/api/chat` backed by OpenAI, curated knowledge layer,
structured `ChatResult { reply, escalate }` with a real contact path on
escalation, client-held history with server-side length/count limits,
public deployment as two Railway services, backend tests + golden-set
eval.

## Phase 0 — Deploy the skeleton (45–60 min) — ✅ DONE 2026-08-10
Goal: prove two Railway services (frontend + backend), deployed from the
same monorepo, talk to each other — before any chatbot logic exists.
- [x] `backend/` FastAPI app with `GET /api/health`
- [x] `frontend/` Vite React TS app that fetches and displays it
- [x] Create two Railway services from this repo: backend (Root Directory
      `backend/`) and frontend (Root Directory `frontend/`) — separate
      Railway project `cadre-ai-chatbot`, isolated from unrelated projects
      in the same account
- [x] Set backend service env vars: `OPENAI_API_KEY` (placeholder, unused
      until Phase 2), `ALLOWED_ORIGINS`
- [x] Set frontend service env var: `VITE_API_URL` pointing at the backend
      service's Railway URL
- [x] Add the frontend Railway URL to backend `ALLOWED_ORIGINS`, redeploy
Verify: frontend Railway URL shows a live "backend status: ok" fetched
from the backend Railway URL. **Confirmed** — CORS validated with the
real deployed origin, and the built JS bundle was checked directly to
confirm it targets the correct backend URL.
- Backend: https://backend-production-900e.up.railway.app (`/api/health` → `{"status":"ok"}`)
- Frontend: https://frontend-production-82ea.up.railway.app
Commits: "Add backend skeleton: FastAPI health check endpoint",
"Add frontend skeleton: Vite React TS shell with backend health check"

## Phase 1 — Knowledge layer & system prompt (45 min) — ✅ DONE 2026-08-10
Goal: ground the bot in real, verifiable Cadre AI content. The challenge
doc is authoritative; the live site only supplements factual gaps.
- [x] Explore subagent reviews the challenge brief (authoritative) and
      supplements only factual gaps from cadreai.com (verified with two
      independent direct fetches for the highest-stakes facts: contact
      info, case-study metrics) — no invented pricing, customers, case
      studies, certifications, security guarantees, or policies
- [x] Write `backend/app/knowledge/cadre_knowledge.md` — pricing,
      certifications, and exact AI Maturity Index/portal mechanics
      explicitly marked "not published" rather than left as gaps
- [x] Write `system_prompt.py`: persona + knowledge + grounding rules.
      Revised after manual review: `escalate: true` is explicitly defined
      as "not a failure signal," with a worked pricing example, and a
      rule for when `escalate: false` is correct (answer already fully
      resolves the question)
- [x] Unit test: assembled prompt contains required knowledge fragments,
      explicitly-unpublished facts, and the non-failure escalation
      language (6 tests total)
Verify: **6/6 tests pass.** Knowledge file reviewed by hand twice — once
before the manual content review, once after applying its two fixes (case
study metrics trimmed to one headline figure each; escalation tone
rewritten). No unsupported claims present; AI Maturity Index section
deliberately left unchanged after a quoted phrase couldn't be verified
against any available source.
Commit: "Add curated Cadre knowledge base and system prompt assembly"

## Phase 2 — Chat endpoint + OpenRouter integration (60–75 min) — ✅ DONE 2026-08-10
Goal: wire the real conversation path with typed, structured output, and
a configurable, not hardcoded, model.

**Provider correction mid-phase:** the assessment's chatbot API key is an
OpenRouter key ($5 budget, 7-day expiry), not a direct OpenAI key —
confirmed with the recruiter. OpenRouter exposes an OpenAI-compatible
Chat Completions API only (no Responses API), so the plan below was
adjusted: `client.chat.completions.parse()` instead of
`client.responses.parse()`, `base_url` pointed at OpenRouter, and
`OPENAI_*` env vars/module names renamed to `OPENROUTER_*` throughout.
- [x] `ChatMessage` / `ChatRequest` / `ChatResult` Pydantic models
      (`ChatResult`: `reply: str`, `escalate: bool`)
- [x] `services/openrouter_client.py`: model id read from
      `OPENROUTER_MODEL` env var (single configured value, no automatic
      fallback logic), structured output bound to `ChatResult` via
      `chat.completions.parse()`. This is the only module that imports
      the OpenAI SDK.
- [x] `routers/chat.py` (`POST /api/chat`): enforce `MAX_HISTORY_MESSAGES`
      (truncate oldest turns) and `MAX_MESSAGE_LENGTH` (reject), then
      delegate to `services/openrouter_client.py` — no direct SDK calls
      in the route
- [x] Unit tests against a mocked client: normal path, escalation path,
      history-truncation, oversized-message handling (15 tests total,
      covering both the route and the service layer)
Verify: **15/15 pytest pass.** Live smoke test against the deployed
backend with the real `OPENROUTER_API_KEY`, covering 6 scenarios: normal
grounded Q&A, pricing (confident tone + escalate:true, matching the
Phase 1 review fix), a genuinely out-of-scope question (honest escalation,
no invented policy), a greeting (no escalation), multi-turn history
(correctly used prior context to identify "that industry" and cited the
right case study), and the oversized-message guardrail (422, confirmed
the request never reached OpenRouter).
Commit: "Add /api/chat endpoint with structured OpenRouter responses and history/length guardrails"

## Phase 3 — Frontend chat UI (60–75 min) — ✅ DONE 2026-08-10
Goal: a usable interface a real prospective client could hold a
conversation in — intentionally simple.
- [x] `ChatWindow`, `MessageBubble`, `MessageInput`, `EscalationBanner`
      (plus starter-question chips, inline in ChatWindow — not a
      separate file, only used in one place)
- [x] Client-side history in React state, resent each request
- [x] Loading state (typing-dots indicator, input disabled while
      waiting), network/HTTP-error state (inline error banner),
      escalation banner on `escalate: true`, Enter-to-send
      (Shift+Enter for newline), send disabled on empty/whitespace input
- [x] No Redux/Zustand, no router, no UI framework — plain React state
      and hand-written CSS
Verify: `tsc -b && vite build` passes. Deployed and driven with a real
headless-Chromium browser (Playwright, since `chromium-cli` wasn't
available on this machine) against the live URL — not just curl. Covered
initial load, a starter-question click (normal grounded reply), a
pricing question (escalation banner + confident tone), a multi-turn
follow-up (correctly resolved prior context, cited the right case
study), disabled-while-loading and disabled-on-empty input states, and
zero browser console errors. **Found and fixed a real bug this way**:
the message list overflowed behind the fixed input box on longer
conversations (missing `min-height: 0` on the nested flex scroll
container) — invisible to a curl-only check, caught by looking at an
actual screenshot.
Commit: "Build chat UI with escalation handling"

## Phase 4 — Eval pass, polish, compliance review, README (30–45 min) — ✅ DONE 2026-08-10
Goal: verify behavior against the brief's own scenarios, confirm the
challenge's own deliverables are met, then make it presentable.
- [x] Golden-set eval script (`tests/eval_golden_set.py`, 10 scenarios)
      run against the deployed `OPENROUTER_MODEL`. Two initial "failures"
      turned out to be wrong test expectations, not app bugs (see below)
      — corrected the eval, not the app. 10/10 passing, stable across
      repeated runs, both before and after the code-review fixes below.
- [x] `/code-review high` pass on the full diff (`cd2f6d3..HEAD`) — 8
      parallel finder agents, manually triaged since the skill's own
      verification/synthesis step never returned a result (waited,
      proceeded per candidate's explicit instruction). 3 real,
      low-regression-risk bugs fixed; the rest were style opinions,
      already-decided trade-offs, or non-issues given Railway's actual
      deployment model (see PR/commit for full triage)
- [x] Final challenge-compliance review pass (subagent): confirmed
      deployed URLs work, `CLAUDE.md`/`plan.md`/README present and
      accurate (spot-checked, not just assumed), no secrets in git
      history, out-of-scope items genuinely absent from the codebase
      (grepped, not just asserted). Caught one real issue: a favicon
      change was uncommitted at audit time — fixed immediately.
- [x] Light UI polish (favicon, page title, meta description, mobile
      responsiveness check). Cadre's real favicon is used — the
      challenge brief says nothing about brand/logo restrictions; an
      earlier self-imposed "no imitation" caution didn't apply here
      since this is Cadre's own chatbot, not third-party impersonation
      (confirmed with the candidate before doing so)
- [x] README.md with architecture, local setup, env vars, deployment,
      model/provider rationale, grounding/escalation approach, testing
      strategy, and explicit trade-offs/limitations
Verify: **10/10 golden-set scenarios pass** on the live URL, both before
and after the code-review fixes. **17/17 backend unit tests pass**
(3 added this phase). Frontend `tsc -b && vite build` passes. Manually
re-verified the full normal/escalation/multi-turn flow and the new
error-rollback behavior in a real browser against the live deployment
after every change in this phase.
Commit: "Polish, README, final eval and compliance review" (actually
landed as 5 separate commits — README, golden-set eval, favicon/plan.md
cleanup, and the 3 code-review fixes — smaller and more descriptive than
one combined commit)

## Post-Phase-4 — Engineering hygiene (pre-submission) — ✅ DONE 2026-08-10
Goal: a focused hygiene pass (linting, CI, API docs) requested before
final submission. Reviewed first (what exists / what's missing / risk
per change), approved, then implemented exactly the approved scope --
nothing else.
- [x] `ruff` added as a backend dev dependency (no config file needed).
      One legitimate finding (unused `pytest` import in a test file),
      fixed.
- [x] `.github/workflows/ci.yml`: backend (install → ruff → pytest) and
      frontend (npm ci → lint → build) on push/PR. No live OpenRouter
      calls -- `eval_golden_set.py` was never pytest-discoverable in
      the first place (doesn't match `test_*.py`), so nothing needed
      excluding. **Verified green on GitHub itself** (`gh run watch`),
      not just assumed from a working local command.
- [x] Swagger/OpenAPI: `Field(description=...)` on every request/response
      model field (especially `escalate` and `history`, the two least
      self-explanatory), documented `422`/`503` responses with examples
      on `POST /api/chat`, `GET /api/health` now returns a typed
      `HealthStatus` model instead of a bare dict, real app
      `description`/`version`. Fetched the actual live `/openapi.json`
      after deploying to confirm every change rendered correctly, not
      just read from source.
Verify: 17/17 backend tests + ruff clean + frontend lint/build clean,
locally and in the now-green CI run. Live `/docs`, `/openapi.json`, and
`/api/health` inspected post-deploy. Full normal/escalation/multi-turn
browser verification re-run against the live app -- unaffected, as
expected (no application logic changed).
Commit: "Add ruff, GitHub Actions CI, and improved Swagger/OpenAPI docs"

## Phase 5 — Stretch (optional, only if time remains)
- [ ] Simple in-memory per-IP rate limiting on `/api/chat`
- [ ] Streaming responses (SSE) instead of one JSON blob
- [ ] A handful of Vitest component smoke tests

## Risk log
- Frontend/backend Railway service misconfiguration (CORS, env vars
  between the two services) — mitigated by Phase 0.
- Model hallucinating facts not in the knowledge file — mitigated by the
  system-prompt guardrail + golden-set eval in Phase 4.
- Model lineup/pricing assumptions going stale — `openai/gpt-5.6-luna`
  pricing on OpenRouter was confirmed 2026-08-10 directly against
  https://openrouter.ai/api/v1/models (the actual provider used, per the
  Phase 2 correction below -- not developers.openai.com, which was the
  pre-correction assumption). `OPENROUTER_MODEL` stays fully
  config-driven; re-verify against that endpoint if significant time has
  passed.
- Running over budget — Phase 5 is explicitly cuttable; Phases 0–4 are the
  real MVP.
