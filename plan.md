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

## Phase 1 — Knowledge layer & system prompt (45 min)
Goal: ground the bot in real, verifiable Cadre AI content. The challenge
doc is authoritative; the live site only supplements factual gaps.
- [ ] Explore subagent reviews
      `docs/Cadre_AI_Chatbot_Take_Home_Candidate.docx.pdf` (authoritative)
      and supplements only factual gaps (what Cadre does, industries,
      services) from cadreai.com — must NOT infer pricing, customers, case
      studies, certifications, security guarantees, or policies that
      aren't explicitly stated
- [ ] Write `backend/app/knowledge/cadre_knowledge.md`
- [ ] Write `system_prompt.py`: persona + knowledge + explicit "answer
      only from curated knowledge; acknowledge uncertainty and escalate
      when unsupported" instruction
- [ ] Unit test: assembled prompt contains required knowledge fragments
      and the escalation instruction
Verify: test passes; knowledge file reviewed by hand — no unsupported
claims present.
Commit: "Add curated Cadre knowledge base and system prompt assembly"

## Phase 2 — Chat endpoint + OpenAI integration (60–75 min)
Goal: wire the real conversation path with typed, structured output, and
a configurable, not hardcoded, model.
- [ ] `ChatMessage` / `ChatRequest` / `ChatResult` Pydantic models
      (`ChatResult`: `reply: str`, `escalate: bool`)
- [ ] `services/openai_client.py`: model id read from `OPENAI_MODEL` env
      var (single configured value, no automatic fallback logic),
      structured output bound to `ChatResult`. This is the only module
      that imports the OpenAI SDK.
- [ ] `routers/chat.py` (`POST /api/chat`): enforce `MAX_HISTORY_MESSAGES`
      (truncate oldest turns) and `MAX_MESSAGE_LENGTH` (reject/trim), then
      delegate to `services/openai_client.py` — no direct SDK calls in the
      route
- [ ] Unit tests against a mocked client: normal path, escalation path,
      history-truncation, oversized-message handling
Verify: `pytest` green; manual curl smoke test against the deployed
backend Railway URL.
Commit: "Add /api/chat endpoint with structured OpenAI responses and history/length guardrails"

## Phase 3 — Frontend chat UI (60–75 min)
Goal: a usable interface a real prospective client could hold a
conversation in — intentionally simple.
- [ ] `ChatWindow`, `MessageBubble`, `MessageInput`, `EscalationBanner`
- [ ] Client-side history in React state, resent each request
- [ ] Loading state, network-error state, escalation banner on
      `escalate: true`
- [ ] No Redux/Zustand, no router, no UI framework beyond what genuinely
      saves time
Verify: `tsc --noEmit` + build pass; golden-set scenarios walked through
by hand in the deployed UI.
Commit: "Build chat UI with escalation handling"

## Phase 4 — Eval pass, polish, compliance review, README (30–45 min)
Goal: verify behavior against the brief's own scenarios, confirm the
challenge's own deliverables are met, then make it presentable.
- [ ] Run the golden-set eval script against the currently configured
      `OPENAI_MODEL` on the deployed instance; if grounding/escalation is
      insufficient, manually try a stronger `OPENAI_MODEL` value (env var
      change only, no code change) and re-run
- [ ] `/code-review` pass on the full diff
- [ ] Final challenge-compliance review pass (subagent): confirms the
      deployed URL works, `CLAUDE.md` and `plan.md` are present at repo
      root, no secrets/`.env` files are committed, out-of-scope items are
      genuinely absent, README is present and accurate
- [ ] Light UI polish (responsive layout, favicon, page title) — no
      imitation of Cadre's real brand identity
- [ ] README with setup / run / deploy instructions (two Railway
      services)
Verify: all golden-set scenarios behave as expected on the live URL;
compliance review has no open findings.
Commit: "Polish, README, final eval and compliance review"

## Phase 5 — Stretch (optional, only if time remains)
- [ ] Simple in-memory per-IP rate limiting on `/api/chat`
- [ ] Streaming responses (SSE) instead of one JSON blob
- [ ] A handful of Vitest component smoke tests

## Risk log
- Frontend/backend Railway service misconfiguration (CORS, env vars
  between the two services) — mitigated by Phase 0.
- Model hallucinating facts not in the knowledge file — mitigated by the
  system-prompt guardrail + golden-set eval in Phase 4.
- Model lineup/pricing assumptions going stale — `gpt-5.6-luna` pricing
  was confirmed 2026-08-10 against
  https://developers.openai.com/api/docs/pricing, but `OPENAI_MODEL`
  stays fully config-driven; re-verify against that page before
  implementation if time has passed.
- Running over budget — Phase 5 is explicitly cuttable; Phases 0–4 are the
  real MVP.
