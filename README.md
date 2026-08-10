# Cadre AI Chatbot

A customer support chatbot for [Cadre AI](https://cadreai.com), an AI strategy and implementation consultancy — built for Cadre's AI Engineer & FDE take-home challenge.

**Live app:** https://frontend-production-82ea.up.railway.app
**Backend API:** https://backend-production-900e.up.railway.app
**Repo:** https://github.com/maugarciavar/cadre-ai-chatbot

See [`CLAUDE.md`](CLAUDE.md) for the full engineering conventions and guardrails, and [`plan.md`](plan.md) for the phased build log with verification results for every phase.

## Architecture & stack

```
React (TS, Vite) → FastAPI (Python) → OpenRouter (OpenAI-compatible API)
```

- **Frontend:** React + TypeScript + Vite. Plain React state — no Redux/Zustand, no router, no UI framework.
- **Backend:** Python + FastAPI + Pydantic, fully stateless (no database).
- **AI provider:** [OpenRouter](https://openrouter.ai), not OpenAI directly (see [Model & provider choice](#model--provider-choice) below).
- **Deployment:** two independent Railway services from this one monorepo — `frontend/` and `backend/` each as their own service, split via Railway's per-service Root Directory setting.
- **Knowledge:** a single curated markdown file compiled into the system prompt at request time — not RAG, not a vector database. The knowledge base is ~8 topics; retrieval infrastructure would be over-engineering at this scope.

```
backend/app/
  main.py                    FastAPI app, CORS, route registration
  models.py                  ChatMessage / ChatRequest / ChatResult (Pydantic)
  routers/chat.py             POST /api/chat -- validates request, enforces
                              limits, delegates to the service layer. No
                              OpenAI SDK usage here.
  services/openrouter_client.py   The only file that imports the OpenAI SDK
                              (pointed at OpenRouter's base_url).
  knowledge/
    cadre_knowledge.md        Curated source of truth, source-cited
    system_prompt.py          Assembles persona + grounding rules + knowledge
  tests/                      pytest suite (mocked client) + golden-set eval
                              (real calls to the deployed model)

frontend/src/
  components/                 ChatWindow, MessageBubble, MessageInput,
                              EscalationBanner
  lib/api.ts                  fetch wrapper to the backend
  types.ts                    shared TS types matching the API contract
```

## Local setup

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements-dev.txt
cp .env.example .env   # fill in OPENROUTER_API_KEY
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev
```

**Tests:**
```bash
cd backend
pytest                              # unit tests, OpenRouter client mocked -- no network, no cost
python -m tests.eval_golden_set     # golden-set eval against a REAL deployed backend -- real cost, non-deterministic
```

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `ALLOWED_ORIGINS` | backend | Comma-separated CORS allowlist (the frontend's origin) |
| `OPENROUTER_API_KEY` | backend | OpenRouter API key. **Never committed** — set directly in Railway's dashboard/CLI |
| `OPENROUTER_MODEL` | backend | Model id, e.g. `openai/gpt-5.6-luna`. Config-driven, no code change needed to swap models |
| `VITE_API_URL` | frontend | Base URL of the backend API |

## Deployment

Both services are deployed on **Railway**, from this single repo, as two independent services (`backend/` and `frontend/` set as each service's Root Directory). Frontend was intentionally kept on Railway rather than split to Vercel — one platform, less operational surface area, and the developer already had Railway experience.

- Backend: `uvicorn app.main:app` via a `Procfile`, Nixpacks auto-detects Python from `requirements.txt`.
- Frontend: `vite build` then served via `vite preview --host 0.0.0.0 --port $PORT` (see `package.json`'s `start` script).
- Both auto-redeploy on every push to `main`.

## Model & provider choice

The assessment's provided API key is an **OpenRouter** key (confirmed with the recruiter mid-build — the original assumption was direct OpenAI access), with a **$5 total budget, 7-day expiry**. OpenRouter exposes an OpenAI-compatible **Chat Completions API** (not the newer Responses API, which OpenRouter doesn't support), so the official `openai` Python SDK is used unmodified, just pointed at `base_url=https://openrouter.ai/api/v1`.

**Model:** `openai/gpt-5.6-luna`, selected via `OPENROUTER_MODEL` (never hardcoded). Verified directly against OpenRouter's own `/api/v1/models` catalog — $0.10 input / $0.60 output per 1M tokens, with `structured_outputs` support confirmed in the model's `supported_parameters`. At that price the $5 budget covers roughly 14,000+ typical exchanges, so budget wasn't the deciding factor among cheap candidates. Luna was chosen because this is a grounding-and-instruction-following task (stay inside a curated knowledge file, know when to escalate), not one that needs frontier reasoning. If the golden-set eval had shown quality issues, the fix is a one-line env var change to a stronger model (e.g. `openai/gpt-5.6-terra`) — **there is no automatic runtime fallback between models.**

## Grounding & escalation approach

- `backend/app/knowledge/cadre_knowledge.md` is the single source of truth, built from two sources only: the challenge brief (authoritative) and verified direct fetches of cadreai.com (2026-08-10, cited inline per section). Three sections — pricing, certifications, and the exact AI Maturity Index/portal mechanics — are **explicitly marked "not published"** rather than left as silent gaps, so the model has something concrete to ground an honest answer in instead of a hole it might fill with a guess.
- The system prompt (`system_prompt.py`) instructs the model to answer **only** from that knowledge file, and to escalate rather than guess when something isn't covered.
- The model's response is bound to a structured Pydantic schema, `ChatResult { reply: str, escalate: bool }`, via OpenRouter's structured-output support — not free text parsed with regex/keywords.
- `escalate: true` is explicitly framed in the prompt as **not a failure signal** — it means a human should also follow up (e.g. to give an actual price quote), not that the bot failed to answer. A "this isn't publicly specified" answer is still a complete, confident answer.

## Testing & evaluation strategy

Two distinct layers, deliberately not merged:

1. **Unit tests (`pytest`, 20 tests)** — the OpenRouter client is mocked, so these run with no network calls and no cost. They cover: system-prompt assembly and grounding-rule presence, the chat endpoint's request validation (message-length rejection, history truncation), escalation-path handling, and SDK-error-to-HTTP-error translation.
2. **Golden-set evaluation (`eval_golden_set.py`, 10 scenarios)** — a *scripted*, not automated-CI, check that makes real calls to the real deployed model. Covers the challenge brief's own example scenarios (what Cadre does, industries, booking a call, the AI Maturity Index, LLM/data-security approach, an unanswerable question) plus pricing/certification escalation tone and multi-turn context resolution. Stable at 10/10 across repeated runs at time of writing.
   - **Known limitation:** the eval's forbidden-keyword checks are naive substring matches, and two scenarios initially "failed" only because the check couldn't distinguish the model *honestly citing an example of what's unknown* ("...whether it's a self-serve quiz or consultant-led is not specified") from *asserting it as fact*. A proper LLM-judge eval would handle this correctly; substring matching can't. Scenarios were corrected after manually reading the actual replies rather than trusting the naive check — worth knowing before trusting this script's output blindly on a knowledge-file edit.

Frontend verification was done by driving a real headless-Chromium browser (Playwright) against the live deployed URL and inspecting screenshots — not just checking that `fetch` calls returned 200. This caught one real bug (see [Trade-offs](#key-trade-offs--out-of-scope) below) that a curl-only check would have missed entirely.

## Key trade-offs & out-of-scope

Deliberately **not** built, and why:

- **No RAG / vector database.** The knowledge base is ~8 topics; a curated markdown file in the system prompt is the right-sized solution, not an under-engineered one.
- **No database, no auth, no persistent conversation history.** The backend is stateless; the frontend holds history in React state and resends it every request, with server-side `MAX_HISTORY_MESSAGES` / `MAX_MESSAGE_LENGTH` caps.
- **No real CRM/ticketing integration.** Escalation means a clear, honest message plus a real contact path (email/contact form) — not a fake ticket number.
- **No automatic model fallback.** `OPENROUTER_MODEL` is a single configured value; switching models is a deliberate human decision after reviewing the eval, not silent runtime logic.
- **No LangGraph or multi-agent orchestration.** A single system prompt with structured output is sufficient for this task's complexity.

One real bug found and fixed during Phase 3: the message list rendered behind the fixed input box on longer conversations (a nested flex container missing `min-height: 0`) — invisible to an API-only check, caught by actually looking at a browser screenshot rather than trusting that requests succeeded.

**Known limitations at submission:**
- The eval script's keyword matching is naive (see above) — a real LLM-judge eval would be a natural next step with more time.
- `gpt-5.6-luna`, being a smaller/cheaper model, occasionally showed minor non-determinism in escalate-flag consistency on borderline "already fully answered" follow-ups during testing (not a hard failure — over-escalating is a safe direction, not a harmful one).
- No rate limiting on `/api/chat` — acceptable for a scoped take-home demo, would be a first addition before any real-world exposure.
