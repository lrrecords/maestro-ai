

</p>

<p align="center">
  <img src="docs/assets/maestro_ai_logo_metallic_neon.png" alt="Maestro AI logo" width="120">
</p>
<h1 align="center">🎼 Maestro AI — The AI Operating System for Independent Music</h1>

**A powerful, extensible, open-source platform that automates and streamlines operations for modern independent labels, studios, and music organizations using multi-agent AI orchestration.**

[![License](https://img.shields.io/github/license/lrrecords/maestro-ai.svg)](LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/lrrecords/maestro-ai?sort=semver)](https://github.com/lrrecords/maestro-ai/releases)


## 🚀 What is Maestro AI?

Maestro AI is a modular, production-ready platform that brings together specialized AI agents—each handling real music business tasks—under a unified, web-based dashboard. It’s built for working labels, studios, and live event teams, not just demos.


## 🆕 Current State — v1.4.0 (April 2026)

Maestro AI is live and running operations at [LRRecords](https://lrrecords.com.au) in Rockingham, Western Australia.

**What's working now:**
- CEO Command Centre with mission orchestration and approval queue
- 25+ agents across Label, Studio, Live, and Platform Ops departments
- Redis-backed persistent job store
- Role-based permissions (CEO / admin / user)
- Full Swagger/OpenAPI documentation
- Ollama (local, private) and Anthropic API (cloud) support

**What's coming:**
- LEDGER agent (financial tracking)
- SAGE Daily Brief (morning intelligence digest)
- FOCUS agent (CEO priority queue)
- Docker deployment to Railway
- Multi-label SaaS onboarding

If you're running an independent label, studio, or live music organisation and want to try Maestro — star the repo and open an issue. We're actively building from real-world feedback.
---

## 🏛️ Platform Architecture

- **Department Hub:** Central landing page after login. Navigate between departments (Label, Studio, Live, Platform Ops) with ease.
- **Flask + Modular Blueprints:** Each department is a self-contained module with its agents, routing, and templates.
- **Agent Registry:** Python-driven framework for pluggable, composable agent logic per business domain.
- **Live Dashboards:** Browser-based dashboard for real-time agent orchestration, workflow viz, and data inspection.

---

## 🏢 Departments & Agents

| Department     | Description / Agents                                                       |
|----------------|---------------------------------------------------------------------------|
| **Label**      | Core artist and release operations<br>_Agents:_ ATLAS, VINYL, ECHO, FORGE, BRIDGE, SAGE |
| **Studio**     | Recording, creative, and production ops<br>_Agents:_ CLIENT, CRAFT, ASK_AI, MIX, RATE, SESSION, SIGNAL, SOUND<br>_Schema metadata:_ SCHEMA |
| **Live**       | Performance and tour management<br>_Agents:_ BOOK, MERCH, PROMO, RIDER, ROUTE, SETTLE, TOUR<br>_Schema metadata:_ SCHEMA |
| **Platform Ops** | Infra/config, model tuning, system health monitoring                     |

_Switch between departments from the Hub. Each dashboard includes agents and real-time data views._

---

## 🗂️ Project Structure

```
maestro-ai/
├── dashboard/           # Main Flask app, blueprints, route logic
├── scripts/             # CLI tools and pipeline runners
├── templates/           # Jinja HTML templates (modular per department)
├── static/              # CSS/JS for dashboards
├── core/                # Agent base classes, runners, utils
├── data/                # Artist records, analytics, manifest/logs
├── docs/assets/         # All screenshots and documentation images
├── requirements.txt
├── ...
```

---

## ✨ Key Features

- Unified navigation and department hub
- Modular, extensible multi-agent system (CrewAI)
- Automated artist analytics, release checklists, content planning, and more
- CEO approval queue for protected actions (email, public posts, spend, etc.)
- Web-based control panel: run, monitor, and review any agent or pipeline
- Live output streaming and workflow visualization
- No cloud dependency: runs fully local (or integrates with Anthropic/Ollama for model inference)
- Health monitoring for core platform services
- Easy integration with n8n and external automations

---

## ⚡ Quick Start

1. **Clone & Set Up**

    ```bash
    git clone https://github.com/lrrecords/maestro-ai.git
    cd maestro-ai
    python -m venv venv
    source venv/bin/activate        # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

    Playwright (`playwright install chromium`) is optional and only needed for browser automation workflows, not for core dashboard runtime.

2. **Configure Environment**

    ```bash
    # macOS/Linux
    cp .env.example .env
    # Windows PowerShell
    Copy-Item .env.example .env
    # Edit .env for Anthropic (cloud) or Ollama (fast, local)
    ```

    _See below for full configuration._

3. **Launch Dashboard**

    ```bash
    python dashboard/app.py
    # Visit http://127.0.0.1:8080
    ```

4. **Or Use CLI**

    ```bash
    python scripts/maestro.py <agent> "Artist Name"
    ```

5. **Container Run (optional)**

    ```bash
    docker build -t maestro-ai .
    docker run --env-file .env -p 8080:8080 maestro-ai
    ```

---

## ⚙️ Configuration (.env example)

- `LLM_PROVIDER` = anthropic | ollama
- `ANTHROPIC_API_KEY` (if using Anthropic)
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL` (if using Ollama – free, local)
- `MAESTRO_TOKEN` = your secure dashboard token
- `PORT` = dashboard port (default: 8080)
- _See `.env.example` for all available settings_

_Ollama runs on Mac, Linux, or Windows and requires downloading a model._

---

## 🧬 Typical Workflows

- **Run a pipeline for one artist:**  
  `python scripts/maestro.py full "Artist Name"`

- **Review all artists in dashboard:**  
  Launch the web app and login; navigate between Label/Studio/Live for roster-wide ops.

- **Automate n8n/No-code integrations:**  
  Webhook support for agent event triggers.

---

## 🖼️ Screenshots

A few snapshots of the web dashboards:

### Hub
![Hub dashboard](docs/screenshots/Hub.png)

### LABEL — “Nice cards” output
![LABEL agent result cards](docs/screenshots/label-nice-card.png)

### Agent Cards (icons + orchestration)
![Agent cards with icons](docs/screenshots/studio-agent-cards.png)

### LIVE - BOOK Agent card
![BOOK agent card](docs/screenshots/live-book-card.png)

More screenshots: see `docs/assets/`.

---

## 🧩 Extending Maestro AI

- **Add new agents:** See `crews/` for examples. Agents are modular and can be customized per user or label.
- **Integrate with n8n:** Trigger automations, notifications, and external workflows from CrewAI or Flask endpoints.
- **Customize workflows:** Use the CEO Command Centre for orchestrated, multi-step missions, or Run Agents for direct control.
- **Add Artists:** Place artist JSON files in `data/artists/` and they’ll appear in the dashboard roster.

---

## LIVE dashboard

The LIVE dashboard (`/live/`) shows operational tables (Shows, Tours) plus a modal runner for LIVE agents (BOOK, ROUTE, SETTLE, MERCH, PROMO, RIDER, TOUR).

### Running agents vs updating the schedule

Running an agent (`▶ Run`) generates an output JSON payload and saves it under `live/data/<agent>/...` for audit/debug. These agent runs do **not** automatically update the Shows/Tours tables.

To update the schedule tables, use the explicit **Apply** buttons in the result modal:

- **BOOK → “Add to Shows”**
  - Creates one row in `live/data/shows.json` per booked date.
  - Default fields for unknown details:
    - `venue: "—"`
    - `city: "—"`
    - `status: "pending"`
  - Writes `territory` (supports values like `UK and Europe`).

- **TOUR → “Add to Tours”**
  - Appends a tour row to `live/data/tours.json`
  - Default `status: "pending"`

This explicit “apply” step keeps the dashboard safe: agent runs can be evaluated before writing operational data.

### Data files

- `live/data/shows.json` — drives the Shows table and stats
- `live/data/tours.json` — drives the Tours table and stats
- `live/data/booking_history.json` — BOOK agent audit history
- `live/data/<agent>/*.json` — per-run saved outputs (debug/audit)

---

## 🗺️ Roadmap (2026+)

- [x] Modular department system (Hub & navigation)
- [x] Platform Ops (model config, health monitoring)
- [x] Pluggable agent registry
- [x] Ollama/Anthropic support for LLMs
- [ ] Advanced analytics & reporting
- [ ] Plugin/extension API for custom agents
- [ ] Improved onboarding & demo mode
- [x] Containerized/Docker deployment
- [ ] Multi-label & SaaS onboarding

---

## 🤝 Contributing

We welcome PRs! See [`CONTRIBUTING.md`](CONTRIBUTING.md).  
Please don’t commit real artist/label data or any credentials.

---

## 📚 Documentation

- [IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md): Full CrewAI and approval queue setup.
- [MISSION_BRIEFS_EXAMPLES.md](docs/mission_briefs_examples.md): Example mission briefs for testing and demos.
- [RELEASES.md](./RELEASES.md) — detailed changelog & migration notes
- [LICENSE](./LICENSE)
- [Quickstart Guide](./docs/quickstart.md) (coming soon)

---

## 🏷️ License

MIT License © [LRRecords](https://github.com/lrrecords), 2026

---
