# MAESTRO AI — LR Records Orchestrator

An AI-powered artist management system for LR Records. Maestro runs 
a suite of intelligent agents to manage artist relationships, release 
planning, content strategy, analytics, and health monitoring — all 
from a single command-line interface.

---

## System Requirements

- Python 3.11+
- Anthropic API key
- Virtual environment (recommended)

---

## Setup

### 1. Clone & activate environment

git clone https://github.com/your-repo/maestro-ai.git
cd maestro-ai
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

### 2. Install dependencies

pip install -r requirements.txt

### 3. Set your API key

Create a `.env` file in the project root:

ANTHROPIC_API_KEY=sk-ant-...

### 4. Launch

Double-click `start.bat` — or from terminal:

python scripts\maestro.py

---

## Commands

### Dashboard

python scripts\maestro.py report

Colour-coded health dashboard for all artists. Pulls latest BRIDGE 
snapshot per artist and displays score, status, trend, and last contact.
Sorted worst-first so critical relationships surface immediately.

### Roster

python scripts\maestro.py artists

Lists all artists in data/artists/ with genre and next release.

---

### Agent Commands

All single-artist commands follow this pattern:

python scripts\maestro.py <agent> "Artist Name"

| Command                        | Agent  | Output                              |
|-------------------------------|--------|-------------------------------------|
| vinyl  "Artist Name"          | VINYL  | Release checklist by phase          |
| echo   "Artist Name"          | ECHO   | 2-week social content plan          |
| atlas  "Artist Name"          | ATLAS  | Analytics report from CSV data      |
| forge  "Artist Name"          | FORGE  | Automation workflow specifications  |
| sage   "Artist Name"          | SAGE   | Weekly prioritised action plan      |
| bridge "Artist Name"          | BRIDGE | Relationship health snapshot        |

### Roster-wide runs

python scripts\maestro.py bridge --all    # BRIDGE for every artist
python scripts\maestro.py sage   --all    # SAGE for every artist

### Full pipeline (single artist)

python scripts\maestro.py full "Artist Name"

Runs VINYL → ECHO → ATLAS → FORGE → SAGE in sequence and saves 
a manifest file linking all outputs.

### Check-in logging

python scripts\maestro.py checkin "Artist Name"

Logs a contact event for an artist. Updates health tracking data 
used by BRIDGE on next run.

---

## Agent Reference

### VINYL
Generates a phased release checklist tailored to the artist's 
upcoming release. Covers pre-release, launch week, and post-release 
phases with specific tasks and owners.

### ECHO
Produces a 14-day social content calendar. Posts are matched to the 
artist's voice, genre, and audience. Includes platform-specific 
copy and recommended posting times.

### ATLAS
Analyses streaming and social metrics from CSV files in 
data/metrics/. Surfaces trends, anomalies, and growth signals. 
Add CSVs exported from Spotify for Artists, DistroKid, etc.

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

python scripts\maestro.py report

Score bands:

  70–100   Good      Green    Relationship healthy
  40–69    Monitor   Yellow   Worth watching
  0–39     Critical  Red      Needs immediate attention
  N/A      No Data   White    No BRIDGE snapshot found — run bridge first

The dashboard always uses the most recent BRIDGE snapshot per artist.
Run `bridge "Artist Name"` after any significant contact or project 
update to keep scores current.

---

## File Structure

maestro-ai/
├── data/
│   ├── artists/          # Artist profile JSONs (one per artist)
│   ├── bridge/           # BRIDGE snapshots  (slug_YYYYMMDD_HHMMSS.json)
│   ├── vinyl/            # VINYL checklists
│   ├── echo/             # ECHO content plans
│   ├── atlas/            # ATLAS analytics reports
│   ├── forge/            # FORGE automation specs
│   ├── sage/             # SAGE weekly plans
│   ├── metrics/          # Raw CSVs for ATLAS (add yours here)
│   └── manifests/        # Full pipeline run logs
├── scripts/
│   ├── maestro.py        # Main CLI entry point
│   ├── checkin.py        # Contact logging
│   ├── dashboard.py      # Dashboard helper
│   ├── webhook_server.py # Local webhook receiver
│   └── agents/
│       ├── vinyl.py
│       ├── echo.py
│       ├── atlas.py
│       ├── forge.py
│       ├── sage.py
│       └── bridge.py
├── health_alert_workflow.json   # n8n import — health alert automation
├── start.bat                    # Quick launch (Windows)
├── requirements.txt
└── .env                         # API key (not committed)

---

## Adding an Artist

1. Create a JSON profile in data/artists/artist_slug.json

Minimum required structure:

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

2. Run bridge to generate a health baseline:

python scripts\maestro.py bridge "Artist Name"

3. Verify on the dashboard:

python scripts\maestro.py report

---

## Webhook / n8n Integration

BRIDGE fires a webhook after each run to notify connected automations.

Default endpoint: http://localhost:5678/webhook/health-update

To enable:
- Import health_alert_workflow.json into n8n
- Ensure n8n is running before executing bridge commands
- The webhook warning in terminal is harmless if n8n is not running

Payload sent on each BRIDGE run:

{
  "artist":     "Artist Name",
  "score":      14,
  "status":     "Critical",
  "trend":      "declining",
  "timestamp":  "2026-03-07T02:30:00+00:00"
}

---

## Environment Variables

| Variable            | Required | Description                    |
|--------------------|----------|--------------------------------|
| ANTHROPIC_API_KEY  | Yes      | Claude API key                 |
| WEBHOOK_URL        | No       | Override default webhook URL   |

---

## Current Roster

| Artist               | Status   | Last Score |
|---------------------|----------|------------|
| Brendananis Monster  | Critical | 14/100     |
| Jerry Mane           | Critical | 14/100     |

---

## Model

All agents use:  claude-sonnet-4-20250514

---

## Built by

LR Records — March 2026