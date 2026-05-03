# Maestro AI — Next Actions Checklist

**Generated:** 2026-05-03

This is a single, ordered checklist you (or any AI agent) can follow to finish MVP hardening, validate deploy readiness, and then move into post-MVP roadmap work.

---

## Agent: do this in order (with file targets + acceptance criteria)

> Scope: This section focuses on tasks that are best done by an AI agent via code/doc changes, tests, and repo-wide consistency checks.

### 1) Confirm MUST items are truly complete in `main`
**Targets (likely):**
- `dashboard/app.py`
- `label/web.py`
- `studio/web.py`
- `live/web.py`
- `webhook_server.py`
- `scripts/webhook_server.py`
- `Dockerfile`, `.dockerignore`, `Procfile`
- `requirements.txt`

**Work**
- [ ] Review current implementations for:
  - `.env` loading
  - `PORT` binding
  - auth middleware on all sensitive endpoints
  - webhook secret validation on all inbound webhook routes
  - mission execution is not stubbed
  - no unsafe hardcoded webhook fallbacks

**Acceptance criteria**
- [ ] A short “verification note” is added to `docs/handover_summary_for_chat_mode.md` (append-only) stating:
  - what was verified
  - how to reproduce verification (commands/tests)
  - any remaining gaps (if any)

---

### 2) Make security posture explicit in docs (so deployers don’t guess)
**Targets (likely):**
- `README.md`
- `docs/quickstart.md`
- `.env.example`

**Work**
- [ ] Add/verify a dedicated section that states:
  - required auth header(s) and where they apply
  - required webhook auth header(s) and where they apply
  - which env vars are *mandatory* vs optional
  - what defaults exist (localhost URLs, dev mode flags)

**Acceptance criteria**
- [ ] README contains a clear “Security & Auth” section with:
  - exact header names
  - example `curl` calls (unauth → denied, auth → allowed)
- [ ] `.env.example` includes every referenced env var in code (or the docs state why it’s omitted).

---

### 3) Add/expand automated smoke tests for deploy safety
**Targets (likely):**
- `tests/` (existing smoke tests, e.g. `tests/test_api.py`)

**Work**
- [ ] Ensure there are automated tests that validate:
  - protected routes reject missing auth
  - protected routes succeed with auth
  - webhook routes reject missing/invalid secret
  - mission create/list/status endpoints behave correctly (or are skipped with a clear message if external dependencies aren’t configured)

**Acceptance criteria**
- [ ] `pytest -q` passes locally with documented env vars.
- [ ] Tests are deterministic: no reliance on external internet; local services (Redis/Ollama) are either mocked or cleanly skipped.

---

### 4) Reconcile doc claims with runtime reality (reduce onboarding friction)
**Targets (likely):**
- `README.md`
- `docs/quickstart.md`
- any OpenAPI/Swagger docs already in repo

**Work**
- [ ] Ensure the docs do not require Playwright unless a feature explicitly needs it.
- [ ] Ensure agent naming is consistent:
  - Studio uses `ASK_AI` (not `LLM`) unless you intentionally alias it
  - `SCHEMA` is documented as metadata-only where applicable

**Acceptance criteria**
- [ ] A first-time user can follow Quickstart without hitting missing/incorrect steps (as validated by the human checklist below).

---

### 5) (Optional / Roadmap) Implement “SAGE Daily Brief / FOCUS” endpoint + Hub widget
**Targets (as suggested in `docs/MAESTRO_IWAI_SYNTHESIS.md`):**
- `dashboard/label/routes.py` (or equivalent label API file)
- `templates/hub.html`

**Work**
- [ ] Add `GET /label/api/focus/brief` that aggregates operational signals (approvals, missions, upcoming shows) and returns JSON.
- [ ] Add Hub “Command Strip” widget that fetches and displays the brief.

**Acceptance criteria**
- [ ] Brief endpoint returns valid JSON quickly (<2s without LLM; <10–30s with LLM depending on hardware).
- [ ] Widget degrades gracefully: if API fails, shows a helpful message.

---

## Human: do this in order (with exact commands to run + what to look for)

> Run these steps in a clean terminal. If you can, do them twice:
> 1) on your dev machine
> 2) on a clean server/VM (or Docker-only) to simulate a real deploy.

### 1) Pull latest `main` and confirm working tree is clean
```bash
git checkout main
git pull origin main
git status
```
**Look for**
- `On branch main` and `working tree clean`.

---

### 2) Create/refresh your local `.env`
```bash
cp .env.example .env
```
(Windows PowerShell alternative)
```powershell
Copy-Item .env.example .env
```
**Look for**
- `.env` created.

Then edit `.env` and set at minimum:
- `SECRET_KEY=...`
- `MAESTRO_TOKEN=...` (or the token your auth middleware expects)
- `WEBHOOK_SECRET=...`
- If using Ollama: `OLLAMA_MODEL=...`

---

### 3) Create a clean virtualenv and install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
(Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
**Look for**
- No install failures.
- If mission creation uses CrewAI, ensure `crewai` installs successfully.

---

### 4) Run tests
```bash
pytest -q
```
**Look for**
- All tests pass.
- If any tests are skipped due to missing services, confirm the skip message tells you exactly what to configure.

---

### 5) Run the app locally (dev)
```bash
python dashboard/app.py
```
**Look for**
- App boots without errors.
- Log line indicates it bound to the correct port (or honors `PORT`).

**Port check (optional)**
```bash
export PORT=8080
python dashboard/app.py
```
(Windows PowerShell)
```powershell
$env:PORT=8080
python dashboard/app.py
```

---

### 6) Validate auth protection (unauth should fail, auth should succeed)
Replace `$BASE` and `$TOKEN` accordingly.

```bash
BASE=http://localhost:8080
TOKEN=your-token-here

# Unauthenticated request (should be denied)
curl -i "$BASE/label/api/mission/list"

# Authenticated request (should succeed)
curl -i -H "X-MAESTRO-TOKEN: $TOKEN" "$BASE/label/api/mission/list"
```
**Look for**
- Unauth: 401/403
- Auth: 200 and JSON

If your repo uses a different header name (e.g. `Authorization: Bearer ...`), use the header your README specifies.

---

### 7) Validate webhook secret validation
```bash
BASE=http://localhost:8080
SECRET=your-webhook-secret-here

# Expect failure without secret
curl -i -X POST "$BASE/webhook/maestro-approved-action" -H "Content-Type: application/json" -d '{}'

# Expect success with secret (adjust header based on implementation)
curl -i -X POST "$BASE/webhook/maestro-approved-action" \
  -H "Content-Type: application/json" \
  -H "X-WEBHOOK-SECRET: $SECRET" \
  -d '{"workflow":"noop","payload":{}}'
```
**Look for**
- Missing secret: 401/403
- Valid secret: 200 with JSON acknowledgement

---

### 8) Persistence test (restart + confirm data retention)
> This is the MVP-plan flagged human validation.

If you use Redis:
1. Start app + create a mission/job.
2. Stop Flask.
3. Restart Redis.
4. Restart Flask.
5. Verify mission/job list endpoints still show prior data.

**What to look for**
- After restart, mission/job data is still present (or if intentionally ephemeral, docs say so explicitly).

---

### 9) Docker build/run on a clean environment
```bash
docker build -t maestro-ai:local .
docker run --rm -p 8080:8080 --env-file .env maestro-ai:local
```
**Look for**
- Image builds successfully.
- Container starts and serves the app.
- Auth checks still work from Step 6.

---

### 10) Final MVP readiness checks (manual)
- [ ] Walk through dashboard UI flows (missions, jobs, approvals, CRUD) referenced in the MVP plan.
- [ ] Confirm Swagger UI (if enabled) renders and lists endpoints correctly.
- [ ] Onboard one test user/artist workflow and note friction points.

---

## Notes / Decisions Log (fill in as you go)
- LLM provider in use (Ollama vs Anthropic):
- Ollama model:
- Token header format chosen:
- Production host target (Railway / VPS / other):

