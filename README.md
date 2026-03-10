# 🎼 MAESTRO AI — Multi-Agent Label Orchestrator

An AI-powered operations system for independent record labels. MAESTRO
runs a suite of specialised agents to handle artist analytics, release
planning, content strategy, automation, relationship health, and
executive decision-making — from the command line or a live web dashboard.

Built for real label workflows. Not a demo.

---

## What MAESTRO Does

MAESTRO coordinates six AI agents, each responsible for a specific
domain of label operations. Agents run individually or together as a
full pipeline. Every run produces structured JSON output that downstream
agents can consume — forming a chain from raw data to actionable insight.

| Agent      | Role                                              |
|-----------|---------------------------------------------------|
| **ATLAS** | Analyses streaming and social metrics from CSVs   |
| **VINYL** | Generates phased release checklists               |
| **ECHO**  | Produces platform-specific content calendars      |
| **FORGE** | Specifies automation workflows for n8n            |
| **BRIDGE**| Scores relationship health and generates check-ins|
| **SAGE**  | Synthesises everything into a weekly action plan  |

---

## Web Dashboard

MAESTRO includes a browser-based dashboard (Flask) that lets you:

- view the full artist roster
- run any agent or the full pipeline
- stream live agent output in real time
- inspect saved JSON outputs
- review health scores and summaries

No cloud account required — everything runs locally.

---

## System Requirements

- Python 3.11+
- Anthropic API key
- Virtual environment (recommended)

---

## Setup

### 1. Clone and activate environment

```bash
git clone https://github.com/your-org/maestro-ai.git
cd maestro-ai
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Copy the example environment file and add your keys:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
MAESTRO_TOKEN=your_secure_dashboard_token
```

> ⚠️ Never commit your `.env` file. It is excluded by `.gitignore`.

### 4. Launch

Start the web dashboard:

```bash
python scripts/web_app.py
```

Then open `http://127.0.0.1:8080` in your browser.

Or use the CLI:

```bash
python scripts/maestro.py
```

On Windows you can also double-click `start.bat`.

---

## CLI Commands

### Dashboard

```bash
python scripts/maestro.py report
```

Colour-coded health dashboard for all artists. Pulls the latest BRIDGE
snapshot per artist and displays score, status, trend, and last contact.
Sorted worst-first so critical relationships surface immediately.

### Roster

```bash
python scripts/maestro.py artists
```

Lists all artists in `data/artists/` with genre and next release.

### Single-agent runs

All single-artist commands follow this pattern:

```bash
python scripts/maestro.py <agent> "Artist Name"
```

| Command                        | Agent  | Output                              |
|-------------------------------|--------|-------------------------------------|
| `vinyl  "Artist Name"`       | VINYL  | Release checklist by phase          |
| `echo   "Artist Name"`       | ECHO   | 2-week social content plan          |
| `atlas  "Artist Name"`       | ATLAS  | Analytics report from CSV data      |
| `forge  "Artist Name"`       | FORGE  | Automation workflow specifications  |
| `sage   "Artist Name"`       | SAGE   | Weekly prioritised action plan      |
| `bridge "Artist Name"`       | BRIDGE | Relationship health snapshot        |

### Roster-wide runs

```bash
python scripts/maestro.py bridge --all
python scripts/maestro.py sage   --all
```

### Full pipeline (single artist)

```bash
python scripts/maestro.py full "Artist Name"
```

Runs VINYL → ECHO → ATLAS → FORGE → SAGE in sequence and saves
a manifest file linking all outputs.

### Check-in logging

```bash
python scripts/maestro.py checkin "Artist Name"
```

Logs a contact event for an artist. Updates health tracking data
used by BRIDGE on next run.

---

## Agent Reference

### ATLAS
Analyses streaming and social metrics from CSV files in
`data/metrics/`. Surfaces trends, anomalies, and growth signals.
Add CSVs exported from Bandcamp, The Orchard, LabelGrid,
Spotify for Artists, DistroKid, etc.

### VINYL
Generates a phased release checklist tailored to the artist's
upcoming release. Covers pre-release, launch week, and post-release
phases with specific tasks and owners.

### ECHO
Produces a 14-day social content calendar. Posts are matched to the
artist's voice, genre, and audience. Includes platform-specific
copy and recommended posting times.

### FORGE
Specifies automation workflows for n8n or similar tools. Outputs
structured specs that can be imported or built manually.

### SAGE
Synthesises all available agent outputs into a prioritised weekly
action plan. Designed to be the first thing you read on Monday.

### BRIDGE
Relationship health agent. Analyses contact history, communication
patterns, and project status. Produces a health score (0–100),
trend direction, risk assessment, and a ready-to-send check-in
message. Snapshots are saved and used to power the dashboard.

---

## Health Dashboard

```bash
python scripts/maestro.py report
```

Score bands:

| Score     | Status   | Colour | Meaning                                  |
|----------|----------|--------|------------------------------------------|
| 70–100   | Good     | Green  | Relationship healthy                     |
| 40–69    | Monitor  | Yellow | Worth watching                           |
| 0–39     | Critical | Red    | Needs immediate attention                |
| N/A      | No Data  | White  | No BRIDGE snapshot — run bridge first    |

The dashboard always uses the most recent BRIDGE snapshot per artist.
Run `bridge "Artist Name"` after any significant contact or project
update to keep scores current.

---

## Adding an Artist

1. Create a JSON profile in `data/artists/`:

```json
{
  "artist_info": {
    "name": "Artist Name",
    "email": "artist@example.com"
  },
  "musical_identity": {
    "primary_genre": "Genre"
  },
  "upcoming_release": {
    "title": "Release Title"
  },
  "communication_history": []
}
```

2. Generate a health baseline:

```bash
python scripts/maestro.py bridge "Artist Name"
```

3. Verify on the dashboard:

```bash
python scripts/maestro.py report
```

---

## Project Structure

```text
maestro-ai/
├── scripts/
│   ├── maestro.py            # Main CLI entry point
│   ├── web_app.py            # Flask web dashboard
│   ├── run_pipeline.py       # Pipeline runner
│   ├── checkin.py            # Contact logging
│   ├── dashboard.py          # Dashboard helper
│   ├── webhook_server.py     # Local webhook receiver
│   └── agents/
│       ├── atlas.py
│       ├── vinyl.py
│       ├── echo.py
│       ├── forge.py
│       ├── bridge.py
│       └── sage.py
├── data/
│   ├── artists/              # Artist profile JSONs
│   ├── bridge/               # BRIDGE snapshots
│   ├── vinyl/                # VINYL checklists
│   ├── echo/                 # ECHO content plans
│   ├── atlas/                # ATLAS analytics reports
│   ├── forge/                # FORGE automation specs
│   ├── sage/                 # SAGE weekly plans
│   ├── metrics/              # Raw CSVs for ATLAS (add yours here)
│   └── manifests/            # Full pipeline run logs
├── templates/                # Dashboard HTML templates
├── static/                   # Dashboard CSS/JS
├── health_alert_workflow.json
├── start.bat
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Webhook / n8n Integration

BRIDGE fires a webhook after each run to notify connected automations.

Default endpoint: `http://localhost:5678/webhook/health-update`

To enable:

1. Import `health_alert_workflow.json` into n8n
2. Ensure n8n is running before executing bridge commands
3. The webhook warning in terminal is harmless if n8n is not running

Payload sent on each BRIDGE run:

```json
{
  "artist":     "Artist Name",
  "score":      72,
  "status":     "Good",
  "trend":      "improving",
  "timestamp":  "2026-03-10T14:30:00+00:00"
}
```

---

## Environment Variables

| Variable            | Required | Description                          |
|--------------------|----------|--------------------------------------|
| ANTHROPIC_API_KEY  | Yes      | Anthropic Claude API key             |
| MAESTRO_TOKEN      | Yes      | Dashboard access token               |
| WEBHOOK_URL        | No       | Override default webhook endpoint    |
| PORT               | No       | Dashboard port (default: 8080)       |
| DEBUG              | No       | Flask debug mode (default: False)    |

---

## Model

All agents use: `claude-sonnet-4-20250514`

---

## Open Source

MAESTRO AI is open source to support independent labels and encourage
experimentation with AI-driven music industry workflows.

The open-source release includes the full agent framework, CLI,
web dashboard, and local file-based output system.

### Planned extensions

- Hosted SaaS dashboard (no setup required)
- Multi-user authentication and role-based access
- Roster-wide analytics and historical trends
- Premium agent packs
- DSP, CRM, and distributor integrations

---

## Roadmap

- [x] Six-agent pipeline (ATLAS, VINYL, ECHO, FORGE, BRIDGE, SAGE)
- [x] CLI with single-artist and roster-wide commands
- [x] Web dashboard with live streaming
- [x] Health scoring and relationship tracking
- [x] n8n webhook integration
- [ ] Demo mode with sample artist data
- [ ] Versioned output schemas
- [ ] Run history and audit logs
- [ ] Docker deployment
- [ ] Plugin agent system
- [ ] Hosted multi-tenant deployment

---

## Contributing

Contributions are welcome. Fork the repo, create a feature branch,
and submit a PR with a clear description.

Please do not commit real artist data, financial records, or
API keys.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Built by

**LRRecords** — 2026