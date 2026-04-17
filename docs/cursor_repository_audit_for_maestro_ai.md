# Repository audit for Maestro AI
_Exported on 4/17/2026 at 12:51:56 GMT+8 from Cursor (3.1.15)_

---

**User**

## Context
You are reviewing the Maestro AI repository — an open-source multi-agent business operating system for independent music labels, built on Flask, CrewAI, Ollama/Anthropic API, and n8n. The platform has four departments (Label, Studio, Live, Platform Ops) with ~25 agents. Current version: v1.4.0. The owner is preparing for MVP deployment on Railway and open-source marketing launch.

## Task
Perform a full repository audit and produce a structured report with exactly these five sections:

### 1. CURRENT STATE — Completion %
For each department (Label, Studio, Live, Platform Ops), assess: what is production-ready vs stub/incomplete. Assign a rough completion % per department. Flag any agents listed in README that have no real implementation.

### 2. BLOCKING ISSUES — MVP Blockers Only
List ONLY issues that would break the app for a first-time user or external deployer. Do not include nice-to-haves. For each blocker: file path, what is broken, one-line fix.

### 3. DEPLOYMENT READINESS
Audit these specific items and give a PASS / FAIL / PARTIAL per item:
- requirements.txt completeness
- .env.example covers all referenced env vars
- app.py entry point works as documented (dashboard/app.py)
- Playwright install step (is it actually needed at runtime?)
- No hardcoded credentials or local paths
- Docker/containerization readiness

### 4. PRIORITISED TODO LIST
Generate a flat, numbered TODO list ordered by impact for MVP. Group into: [MUST — blocks deployment], [SHOULD — needed for real use], [NICE — post-launch]. Max 20 items total.

### 5. MVP SCOPE RECOMMENDATION
Based on what is actually working, define the smallest deployable MVP: which departments and agents should be ON by default, which should be hidden or flagged as "coming soon" in the dashboard. Be specific.

## Constraints
- Only report on what you can verify in the code. If uncertain, write [UNCERTAIN] next to the claim.
- Do not refactor or change any code. Audit only.
- Output as structured Markdown.
- Flag any security issues (exposed keys, missing auth checks) as [SECURITY] priority.

---

**Cursor**

I’m going to run a read-only codebase audit now: first I’ll map real agent implementations vs README claims, then verify deployment-critical files (`requirements.txt`, `.env.example`, entrypoint, Docker/runtime dependencies, and security risks). After that I’ll deliver the five requested sections with only verifiable findings and `[UNCERTAIN]` where needed.

I’ve got an initial map of departments/agents; next I’m validating deployment-critical files directly (entrypoint behavior, env var coverage, dependencies, container readiness, and runtime security/deploy risks).

I found concrete deployment concerns already (missing container config, env mismatch, auth gaps). I’m now pulling precise code evidence for mission stubs, route protection, and documented startup assumptions to keep the blocker list strict.

I’ve gathered enough verified evidence and I’m now compiling the final five-section audit with strict MVP blockers, PASS/FAIL deployment checks, and a concrete default-on MVP scope based on what’s actually runnable.## 1. CURRENT STATE — Completion %

### Label — **~70% complete**
- **Production-ready:** dashboard blueprint/routes, agent run flows, output persistence, and core Label agent set in `scripts/agents/`.
- **Stub/incomplete:** CEO Mission execution is intentionally stubbed (tasks are not actually executed) in `label/web.py`.
- **Notes:** This is a major capability gap because mission orchestration is a headline feature.
- **README agents without real implementation:** none found in Label set (`ATLAS`, `VINYL`, `ECHO`, `FORGE`, `BRIDGE`, `SAGE`) based on current code.

### Studio — **~82% complete**
- **Production-ready:** `studio/web.py` routes, registry wiring, and runnable agents (`CLIENT`, `SESSION`, `SOUND`, `SIGNAL`, `CRAFT`, `RATE`, `MIX`, `ASK_AI`).
- **Stub/incomplete:** `SCHEMA` is metadata-only in `studio/agents/schema.py`, not a runnable agent class.
- **README mismatch:** README lists `LLM`, but registry exposes `ask_ai` instead (`studio/agents/__init__.py`). Likely alias mismatch `[UNCERTAIN]`.

### Live — **~85% complete**
- **Production-ready:** `live/web.py` routes, runnable registry agents (`BOOK`, `MERCH`, `PROMO`, `RIDER`, `ROUTE`, `SETTLE`, `TOUR`), and apply-to-data flows for booking/tour updates.
- **Stub/incomplete:** `SCHEMA` is metadata-only in `live/agents/schema.py`, not a runnable agent class.
- **Operationally usable:** most flows are coherent for MVP if secured.

### Platform Ops — **~75% complete**
- **Production-ready:** settings persistence + health endpoints in `platform_ops/web.py`, login guard present on Platform Ops routes.
- **Incomplete:** no agent-style execution layer (appears intentional by design), mostly control/health UI.

### README agents with no real implementation
- **Studio `SCHEMA`** (metadata only, not runnable).
- **Live `SCHEMA`** (metadata only, not runnable).
- **Studio `LLM`** appears not present as a runnable class; closest implementation is `ASK_AI` `[UNCERTAIN]`.

---

## 2. BLOCKING ISSUES — MVP Blockers Only

1. **`label/web.py`** — Mission endpoint is debug-stubbed (no real task execution), so flagship mission orchestration cannot function.  
   **Fix:** replace debug placeholder loop with actual crew/task execution and persist true task results.

2. **`dashboard/app.py`** — `.env` is not loaded (`load_dotenv()` missing), so documented `.env` setup can fail for first-time launch (token/provider keys not read unless OS env already set).  
   **Fix:** call `load_dotenv()` at startup before reading env vars.

3. **`dashboard/app.py`** — App ignores `PORT` env and hardcodes `8080`, which can break hosted environments expecting assigned port.  
   **Fix:** bind to `int(os.getenv("PORT", "8080"))`.

4. **`dashboard/app.py`** + `label/web.py`/`studio/web.py`/`live/web.py` — **[SECURITY]** non-Platform APIs are not protected by auth middleware; external deploy exposes write/action endpoints.  
   **Fix:** apply consistent auth guard to all department routes (especially `/run/*`, mission, apply, approval endpoints).

5. **`webhook_server.py`** and `scripts/webhook_server.py` — **[SECURITY]** webhook POST endpoints accept unauthenticated payloads (no signature/token validation).  
   **Fix:** require and verify shared secret or HMAC signature on inbound webhooks.

6. **Repository root** — no container artifacts (`Dockerfile`, compose, Procfile, railway config), while deployment target is Railway.  
   **Fix:** add minimal production container config and documented start command.

---

## 3. DEPLOYMENT READINESS

- **requirements.txt completeness:** **PARTIAL**  
  - Core imports are represented for dashboard flow (`Flask`, `requests`, `python-dotenv`, `anthropic`, `crewai`, `litellm`).
  - But it includes `playwright` though runtime use is not evident, and there is no production server dependency (e.g. `gunicorn`) for hosted deployment `[UNCERTAIN: if Railway command uses Flask dev server intentionally]`.

- **.env.example covers all referenced env vars:** **FAIL**  
  - Code references many vars missing from `.env.example` (e.g. `SECRET_KEY`, `MAESTRO_DEV_MODE`, `MAESTRO_BASE_URL`, `N8N_BASE_URL`, `OLLAMA_NUM_CTX`, `OLLAMA_TIMEOUT_SECONDS`, `ANTHROPIC_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `GOOGLE_MAPS_API_KEY`, email SMTP vars, Telegram vars, etc.).

- **app.py entry point works as documented (`dashboard/app.py`):** **PARTIAL**  
  - `python dashboard/app.py` should boot locally.
  - But it runs `debug=True`, hardcodes port 8080, and does not load `.env`, which weakens deploy correctness.

- **Playwright install step (needed at runtime?):** **FAIL**  
  - README requires `playwright install chromium`, but runtime dashboard routes do not show active Playwright use.
  - This appears unnecessary for MVP runtime and adds setup friction.

- **No hardcoded credentials or local paths:** **PARTIAL**  
  - No confirmed live API keys committed.
  - However, hardcoded external fallback webhook URL exists in `label/web.py` (to `webhook.site`), and several localhost defaults are embedded; these are risky for production behavior.

- **Docker/containerization readiness:** **FAIL**  
  - No `Dockerfile`/compose/Procfile/railway config detected.

---

## 4. PRIORITISED TODO LIST

1. **[MUST — blocks deployment]** Implement real mission execution in `label/web.py` (remove debug placeholder behavior).  
2. **[MUST — blocks deployment]** Add auth protection across Label/Studio/Live endpoints. **[SECURITY]**  
3. **[MUST — blocks deployment]** Add webhook signature/secret validation for inbound webhook servers. **[SECURITY]**  
4. **[MUST — blocks deployment]** Load `.env` in `dashboard/app.py` before reading env vars.  
5. **[MUST — blocks deployment]** Respect `PORT` env var in `dashboard/app.py`.  
6. **[MUST — blocks deployment]** Add container deploy artifacts (at least `Dockerfile` + start command for Railway).  
7. **[MUST — blocks deployment]** Remove hardcoded `webhook.site` fallback and fail safely when webhook env is missing. **[SECURITY]**  
8. **[SHOULD — needed for real use]** Expand `.env.example` to include all referenced env vars.  
9. **[SHOULD — needed for real use]** Align README agent list with actual registries (`LLM` vs `ASK_AI`, `SCHEMA` metadata-only).  
10. **[SHOULD — needed for real use]** Add production-safe run mode (disable `debug=True`, document proper WSGI launch).  
11. **[SHOULD — needed for real use]** Clarify/trim Playwright setup in docs and dependencies if not runtime-critical.  
12. **[SHOULD — needed for real use]** Add minimal deploy smoke tests for core routes and agent run endpoints.  
13. **[SHOULD — needed for real use]** Add rate limiting/basic abuse protection on write endpoints. **[SECURITY]**  
14. **[NICE — post-launch]** Add persistent mission/job store (Redis/DB) replacing in-memory tracker for reliability.  
15. **[NICE — post-launch]** Add role-based permissions for CEO approval actions. **[SECURITY]**  
16. **[NICE — post-launch]** Add OpenAPI or endpoint reference for external integrators.  
17. **[NICE — post-launch]** Add CI check to detect README-vs-registry drift for agent names.

---

## 5. MVP SCOPE RECOMMENDATION

Smallest reliable deployable MVP based on current verified code:

- **ON by default**
  - **Studio:** `CLIENT`, `SESSION`, `SOUND`, `SIGNAL`, `CRAFT`, `RATE`, `MIX`, `ASK_AI`
  - **Live:** `BOOK`, `MERCH`, `PROMO`, `RIDER`, `ROUTE`, `SETTLE`, `TOUR`
  - **Platform Ops:** settings + health pages/endpoints

- **Hidden or flagged “Coming Soon”**
  - **Label “CEO Mission / Fire Mission”** until mission execution is real (currently debug stub).
  - Any UI references to **`SCHEMA` as an agent** (Studio/Live) — keep schema as internal metadata only.
  - **`LLM` label in Studio UI/docs** unless mapped explicitly to `ASK_AI`.

- **MVP posture**
  - Treat MVP as **Studio + Live operational copilot**, with Platform Ops for configuration and health.
  - Keep Label enabled only for non-mission features, or gate Label entirely behind “beta” until mission and auth hardening are complete.



