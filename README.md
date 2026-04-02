<p align="center">
  <img src="docs/assets/MAESTRO_LOGO.png" alt="Maestro AI logo" width="120">
</p>

# 🎼 Maestro AI — Multi-Agent Business OS for Music Labels

**A powerful, extensible, open-source platform that automates and streamlines operations for modern independent labels, studios, and music organizations using multi-agent AI orchestration.**

[![License](https://img.shields.io/github/license/lrrecords/maestro-ai.svg)](LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/lrrecords/maestro-ai?sort=semver)](https://github.com/lrrecords/maestro-ai/releases)
[![Build Status](https://github.com/lrrecords/maestro-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/lrrecords/maestro-ai/actions)

---

## 🚀 Overview

Maestro AI brings together specialized AI agents—each handling real music business tasks—under a unified, modular web dashboard. Built for working labels and teams, Maestro AI orchestrates artist management, studio production, live event logistics, and platform operations in one extensible system.

**No demo fluff—deployed by working indie labels.**

---

## 🏛️ Platform Architecture

- **Department Hub:** Central landing page after login. Navigate between departments (Label, Studio, Live, Platform Ops) with ease.
- **Flask + Modular Blueprints:** Each department is a self-contained module with its agents, routing, and templates.
- **Agent Registry:** Python-driven framework for pluggable, composable agent logic per business domain.
- **Live Dashboards:** Browser-based dashboard for real-time agent orchestration, workflow viz, and data inspection.

---

## ✨ Key Features

- Unified navigation and department hub
- Modular, extensible multi-agent system
- Automated artist analytics, release checklists, content planning, and more
- Web-based control panel: run, monitor, and review any agent or pipeline
- Live output streaming and workflow visualization
- No cloud dependency: runs fully local (or integrates with Anthropic/Ollama for model inference)
- Health monitoring for core platform services

---

## 🖼️ Screenshots

A few snapshots of the web dashboards:

![Departments Hub](docs/assets/Screenshot%20Departments.jpg)
![LIVE Agents](docs/assets/LIVE_Agents.jpg)
![STUDIO Agents](docs/assets/STUDIO_Agents.jpg)

More screenshots: see `docs/assets/`.

## 🏢 Departments & Agents

| Department     | Description / Agents                                                       |
|----------------|---------------------------------------------------------------------------|
| **Label**      | Core artist and release operations<br>_Agents:_ ATLAS, VINYL, ECHO, FORGE, BRIDGE, SAGE |
| **Studio**     | Recording, creative, and production ops<br>_Agents:_ CLIENT, CRAFT, LLM, MIX, RATE, SCHEMA, SESSION, SIGNAL, SOUND |
| **Live**       | Performance and tour management<br>_Agents:_ BOOK, MERCH, PROMO, RIDER, ROUTE, SCHEMA, SETTLE, TOUR |
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

## ⚡ Quick Start

1. **Clone & Set Up**

    ```bash
    git clone https://github.com/lrrecords/maestro-ai.git
    cd maestro-ai
    python -m venv venv
    source venv/bin/activate        # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

2. **Configure Environment**

    ```
    cp .env.example .env
    # Edit .env for Anthropic (cloud) or Ollama (fast, local)
    ```

    _See below for full configuration._

3. **Launch Dashboard**

    ```bash
    python scripts/web_app.py
    # Visit http://127.0.0.1:8080
    ```

4. **Or Use CLI**

    ```bash
    python scripts/maestro.py <agent> "Artist Name"
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
- [ ] Containerized/Docker deployment
- [ ] Multi-label & SaaS onboarding

---

## 🤝 Contributing

We welcome PRs! See [`CONTRIBUTING.md`](CONTRIBUTING.md).  
Please don’t commit real artist/label data or any credentials.

---

## 📖 More Information

- [RELEASES.md](./RELEASES.md) — detailed changelog & migration notes
- [LICENSE](./LICENSE)
- [Quickstart Guide](./docs/quickstart.md) (coming soon)

---

## 🏷️ License

MIT License © [LRRecords](https://github.com/lrrecords), 2026

---