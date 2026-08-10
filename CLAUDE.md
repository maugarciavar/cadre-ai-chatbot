# CLAUDE.md

## Project
Customer support chatbot for Cadre AI, an AI strategy and implementation
consultancy. A prospective or existing client should be able to ask common
questions (what Cadre does, industries served, how to book a strategy call,
portal access, the AI Maturity Index, LLM selection and data security
approach) and get answers grounded in real, verifiable Cadre content — with
a clear, honest handoff to a human when the bot doesn't know.

The authoritative requirements source is
`docs/Cadre_AI_Chatbot_Take_Home_Candidate.docx.pdf` (kept locally,
gitignored). cadreai.com may supplement factual company knowledge, never
override or extend beyond what the challenge doc and site actually state.

## Architecture
React (TS, Vite) -> FastAPI (Python) -> OpenRouter (OpenAI-compatible API)

- Frontend and backend are **two separate Railway services deployed from
  the same monorepo** (Root Directory set per service: `frontend/` and
  `backend/`). Not Vercel — kept on a single platform the developer already
  has operational experience with, per explicit scope decision.
- Backend is fully stateless: no database, no server-side session storage.
  The frontend holds conversation history in React state and resends it
  with every request, with server-side history/length limits (see below).
- Knowledge is a curated markdown file compiled into the system prompt at
  request time — not RAG, not a vector store. The corpus is ~8 topics;
  retrieval infrastructure would be over-engineering at this scope.
- The model returns structured output (JSON bound to a Pydantic schema,
  `ChatResult { reply: str, escalate: bool }`) instead of free text parsed
  with regex/keywords. This is the same schema used for the API response.

## Stack
- Frontend: React + TypeScript + Vite, deployed to Railway (service 1)
- Backend: Python + FastAPI + Pydantic, deployed to Railway (service 2)
- AI provider: **OpenRouter**, not OpenAI directly — the provided API key
  is an OpenRouter key with a **$5 total budget, expiring 7 days** from
  issue (2026-08-10). OpenRouter exposes an OpenAI-compatible Chat
  Completions API (not the newer Responses API — OpenRouter doesn't
  support that), so the `openai` Python SDK is used unmodified, just
  pointed at `base_url=https://openrouter.ai/api/v1`.
- Model: selected via the `OPENROUTER_MODEL` environment variable — never
  hardcoded in application code. Default: `openai/gpt-5.6-luna`
  (OpenRouter requires a `provider/` prefix). Verified directly against
  OpenRouter's own `/api/v1/models` catalog (fetched and parsed as raw
  JSON, not a summarized page) on 2026-08-10: $0.10 input / $0.60 output
  per 1M tokens, `structured_outputs` and `response_format` both present
  in `supported_parameters`. At this price the $5 budget covers roughly
  14,000+ typical exchanges, so budget was not the deciding factor among
  cheap candidates — Luna was chosen because a constrained,
  curated-knowledge support task needs reliable instruction-following,
  not frontier reasoning. Run the golden-set eval (see plan.md Phase 4)
  against it. If quality or grounding is insufficient, manually change
  `OPENROUTER_MODEL` to a stronger model (e.g. `openai/gpt-5.6-terra`,
  $1.00/$6.00 on OpenRouter) and re-run the eval — there is **no
  automatic runtime fallback** between models.
  - Model lineups and prices change. Re-verify against
    `https://openrouter.ai/api/v1/models` (a public, unauthenticated
    endpoint — fetch and parse the JSON directly rather than trusting a
    summarized page) before relying on the figures above if significant
    time has passed.
- No database. No auth. No RAG / vector store. No LangGraph or any
  multi-agent orchestration framework.

## Directory map
```
cadre-ai-chatbot/
  frontend/src/components/     Chat UI components
  frontend/src/lib/api.ts      fetch wrapper to backend
  backend/app/main.py          FastAPI app, CORS, route registration
  backend/app/models.py        ChatMessage / ChatRequest / ChatResult schemas
  backend/app/routers/chat.py  POST /api/chat — validates request, calls the
                                service layer, returns ChatResult. No OpenAI
                                SDK usage here.
  backend/app/services/
    openrouter_client.py       The only file that imports the OpenAI SDK
                                (pointed at OpenRouter's base_url). Builds
                                the request, calls the model, returns a
                                ChatResult. Swappable for a fake in tests.
  backend/app/knowledge/       cadre_knowledge.md + system_prompt.py
  backend/tests/                pytest suite + golden-set eval script
```

## Commands
- Frontend dev:      `cd frontend && npm install && npm run dev`
- Frontend check:    `cd frontend && npm run build` (tsc --noEmit + vite build)
- Backend dev:       `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
- Backend tests:     `cd backend && pytest`
- Golden-set eval:   `cd backend && python -m tests.eval_golden_set`

## API contract
```
POST /api/chat
  request:  { "message": string, "history": [{ "role": "user"|"assistant", "content": string }] }
  response: ChatResult -> { "reply": string, "escalate": boolean }

GET /api/health -> { "status": "ok" }
```

## Conventions
- Backend: Pydantic models for every request/response — no bare dicts
  crossing the API boundary. Settings via `pydantic-settings` reading env
  vars; never hardcode keys.
- The OpenAI SDK is only ever imported and instantiated in
  `backend/app/services/openrouter_client.py` (pointed at OpenRouter, not
  api.openai.com). Routes (`routers/chat.py`) call into that service and
  never touch the SDK directly — this keeps the route thin and makes the
  Phase 2 mocked-client unit tests possible without patching SDK
  internals.
- Frontend: functional components + hooks only. No Redux/Zustand, no
  router unless a real need appears, no UI framework beyond what saves
  real time — React state is sufficient at this scope.
- Commits: small, one logical change each, imperative mood
  ("Add chat endpoint", not "added" or "adds").
- Every phase in plan.md ends with an explicit verification step (test
  pass, typecheck pass, or a manual check against the deployed URL) before
  moving to the next phase.

## Guardrails
- The Cadre challenge document is the authoritative requirements source.
  cadreai.com may supplement factual company knowledge (what we do,
  industries, services) but must never be used to invent or infer:
  **pricing, customers, case studies, certifications, security
  guarantees, policies, or capabilities** that aren't explicitly stated
  somewhere real.
- Never invent facts about Cadre AI that are not present in
  `backend/app/knowledge/cadre_knowledge.md`.
- The system prompt must explicitly instruct the model to answer
  Cadre-specific questions **only** from the curated knowledge, and to
  acknowledge uncertainty and set `escalate: true` when the answer is
  unsupported — never guess.
- The backend enforces `MAX_HISTORY_MESSAGES` and `MAX_MESSAGE_LENGTH` on
  incoming requests as simple safeguards. This is not token-counting
  infrastructure — just a hard cap enforced before the request reaches
  OpenRouter.
- Don't add anything from the Phase 5 stretch list until Phases 0–4 are
  done and verified.
- Don't introduce a database, auth system, RAG pipeline, or agent
  framework (e.g. LangGraph). If a task seems to need one, stop and flag
  it instead of building it.
- Don't use subagents to demonstrate subagents. Use them where the work
  is genuinely independent (research) or is a distinct verification pass
  (code review, compliance review) — not to parallelize work that's
  actually sequential.

## Out of scope (explicit)
- RAG / vector database
- User accounts / authentication
- Persistent conversation history (server-side) / database
- LangGraph or any multi-agent orchestration framework
- Real CRM / ticketing integration for escalation
- Multi-language support
- Admin UI for editing the knowledge base
- Automatic model fallback logic
- Token-counting infrastructure, Redis, server-side persistence
