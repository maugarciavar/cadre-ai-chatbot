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
React (TS, Vite) -> FastAPI (Python) -> OpenAI API

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
- Model: selected via the `OPENAI_MODEL` environment variable — never
  hardcoded in application code. Initial default: `gpt-5.6-luna`
  ($0.20 input / $1.20 output per 1M tokens) — appropriate for a
  constrained, curated-knowledge customer-support task. Confirmed against
  OpenAI's official pricing docs:
  https://developers.openai.com/api/docs/pricing (verified 2026-08-10).
  Run the golden-set eval (see plan.md Phase 4) against it. If quality or
  grounding is insufficient, manually change `OPENAI_MODEL` to a stronger
  model (e.g. `gpt-5.6-terra`, $2.00/$12.00) and re-run the eval — there is
  **no automatic runtime fallback** between models.
  - Before implementation, re-check the pricing page above — prices and
    the model lineup can change, and this project has already seen one
    lookup return stale/conflicting data before a second lookup confirmed
    the figures above.
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
    openai_client.py           The only file that imports the OpenAI SDK.
                                Builds the request, calls the model, returns
                                a ChatResult. Swappable for a fake in tests.
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
  `backend/app/services/openai_client.py`. Routes (`routers/chat.py`) call
  into that service and never touch the SDK directly — this keeps the
  route thin and makes the Phase 2 mocked-client unit tests possible
  without patching SDK internals.
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
  OpenAI.
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
