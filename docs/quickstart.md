# Quickstart: Maestro AI

## Prerequisites

- Python 3.11+ (recommended)
- [Ollama](https://ollama.com/) (optional — for local LLM support)
- Node.js (only needed for deep frontend customisation)

---

## 1. Clone & Install

```bash
git clone https://github.com/lrrecords/maestro-ai.git
cd maestro-ai
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows PowerShell:
# venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Configure Environment

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set at minimum:

| Variable | Purpose | Example |
|---|---|---|
| `MAESTRO_TOKEN` | Dashboard login token | `my-secret-token` |
| `LLM_PROVIDER` | LLM backend | `ollama` or `anthropic` |
| `PREMIUM_FEATURES_ENABLED` | Enable premium agents | `true` |

For local development you can instead set `MAESTRO_DEV_MODE=1` to bypass token login (any token accepted).

### LLM options

**Ollama (local, free):**
```bash
ollama pull llama3.1:8b   # or any supported model
```
Set `LLM_PROVIDER=ollama` in `.env`.

**Anthropic (cloud):**
Set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=sk-...` in `.env`.

**OpenAI (cloud):**
Set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=sk-...` in `.env`.

---

## 3. Start the Dashboard

```bash
python dashboard/app.py
```

Visit [http://localhost:8080](http://localhost:8080) and log in with your `MAESTRO_TOKEN`.

For production use gunicorn (already in `requirements.txt`):

```bash
gunicorn -w 2 -b 0.0.0.0:8080 dashboard.app:app
```

---

## 4. Demo Data

Three demo artists are included out of the box:

- `data/artists/aria_velvet.json` — Alt Pop artist, upcoming single
- `data/artists/king_juno.json`
- `data/artists/nova_saint.json`

To add your own artist, copy one of the demo files and edit the fields. Use
`artist_import_template.csv` for bulk imports.

---

## 5. Running Agents

### Via the Dashboard

After login, navigate to `/agents` to see all discovered agents. Click
**Run** next to any agent to execute it with a default (empty) context.

For LEDGER, SAGE, FOCUS, and MULTI_LABEL_ONBOARDING premium agents, use the
dedicated dashboard pages under `/label/ledger` and `/label/sage`, or hit
the `/agents/run/<AgentName>` API endpoint directly.

### Via the CLI

```bash
# LEDGER — financial summary
python -c "
from premium_agents.ledger import LedgerAgent
import json
r = LedgerAgent().run({'period': 'last_30_days'})
print(json.dumps(r['data'], indent=2))
"

# FOCUS — CEO priority queue
python -c "
from premium_agents.focus import FocusAgent
import json
r = FocusAgent().run({})
print(json.dumps(r['data'], indent=2))
"

# MULTI_LABEL_ONBOARDING — new label onboarding package
python -c "
from premium_agents.multi_label_onboarding import MultiLabelOnboardingAgent
import json
r = MultiLabelOnboardingAgent().run({'label_name': 'My Label', 'owner_name': 'Jane'})
print(json.dumps(r['data'], indent=2))
"
```

---

## 6. Running Tests

```bash
python -m pytest tests/ -v
```

All tests should pass. No external services (LLM, Redis) are required —
all network calls are mocked in the test suite.

---

## 6b. API Documentation (Swagger/OpenAPI)

Maestro AI ships with full interactive API docs via Flasgger.

Start the dashboard, then visit:

```
http://localhost:8080/apidocs/
```

The Swagger UI lists every endpoint with request/response schemas. You can
execute requests directly from the browser.

The raw OpenAPI spec JSON is available at:

```
http://localhost:8080/apispec_1.json
```


## 7. Docker

Build and run the Docker image locally:

```bash
docker build -t maestro-ai .
docker run -p 8080:8080 --env-file .env maestro-ai
```

Visit [http://localhost:8080](http://localhost:8080).

---

## 8. Open Core vs Premium

| Area | Open Core | Premium |
|---|---|---|
| Dashboard & routing | ✅ | ✅ |
| Base agent framework | ✅ | ✅ |
| LEDGER (financials) | — | ✅ |
| SAGE (daily brief) | — | ✅ |
| FOCUS (CEO queue) | — | ✅ |
| MULTI_LABEL_ONBOARDING | — | ✅ |

Toggle premium features with `PREMIUM_FEATURES_ENABLED=true/false` in `.env`.

---

## 9. Extending Maestro AI

See [`docs/EXTENDING.md`](EXTENDING.md) for the full guide on adding your own
agents and plugins.

---

## 10. Security & Auth

### Dashboard access

All dashboard pages and API routes require authentication. Set `MAESTRO_TOKEN` in `.env`.

**Headers accepted by API clients (no browser session):**

```bash
# Custom header
curl -H "X-MAESTRO-TOKEN: your-token" http://localhost:8080/label/api/mission/list

# Bearer token
curl -H "Authorization: Bearer your-token" http://localhost:8080/label/api/mission/list
```

Without auth, API routes return `401 Unauthorized`. Browser routes redirect to `/login`.

For local development, set `MAESTRO_DEV_MODE=1` to bypass strict token matching (any token accepted).

### Inbound webhook validation

All routes under `/webhook/*` (served by `webhook_server.py`) require a shared `WEBHOOK_SECRET`.

```bash
# Without secret — returns 401
curl -X POST http://localhost:8080/webhook/maestro-approved-action \
  -H "Content-Type: application/json" -d '{}'

# With X-WEBHOOK-SECRET header — returns 200
curl -X POST http://localhost:8080/webhook/maestro-approved-action \
  -H "Content-Type: application/json" \
  -H "X-WEBHOOK-SECRET: your-webhook-secret" \
  -d '{"workflow":"noop","payload":{}}'
```

### Required env vars summary

| Variable | Required for | Notes |
|---|---|---|
| `MAESTRO_TOKEN` | Dashboard login | Mandatory in production |
| `WEBHOOK_SECRET` | Inbound webhooks | All webhook routes return 401 if unset |
| `SECRET_KEY` | Session security | Auto-generated if omitted (sessions reset on restart) |
| `LLM_PROVIDER` | Running agents | `ollama` or `anthropic` |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Dashboard not configured: MAESTRO_TOKEN is missing` | Set `MAESTRO_TOKEN` in `.env`, or set `MAESTRO_DEV_MODE=1` |
| `LLM returned empty response` | Start Ollama (`ollama serve`) or check your API key |
| `Agent not found` | Ensure `PREMIUM_FEATURES_ENABLED=true` and the agent file exists in `premium_agents/` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside your virtual environment |

