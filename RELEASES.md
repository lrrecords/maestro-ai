# 🎼 MAESTRO AI — Release History

## What is MAESTRO AI?

MAESTRO AI is an AI-powered, multi-agent business operating system designed for independent labels, studios, and live music organizations. The platform provides a unified web dashboard, organizing core operations into four domains (Label, Studio, Live, Platform Ops) each with pluggable agents for end-to-end workflow automation.

---
## v1.3.0 (April 1, 2026) — LIVE Dashboard Agent Cards + Apply Workflow

**Highlights:**
- LIVE dashboard agent result rendering significantly improved:
  - Added polished generic agent result card rendering (arrays, objects, primitives).
  - ISO date formatting now includes a stable UTC weekday label (e.g., `2026-05-12 (Tue)`).
- Added LIVE agent “sanity check” sections to make outputs more actionable and easier to validate:
  - **ROUTE:** reconciles inconsistent travel-time fields (prefers `result.data`, falls back to parsed `result.message` when needed) and adds implied travel-time sanity check.
  - **SETTLE:** gross/expenses/net/share reconciliation plus deal memo split parsing (e.g., `70/30`).
  - **MERCH:** settlement estimate sanity lines (per-attendee, per-show).
- Added explicit operational write workflow (safer than auto-writing from agent runs):
  - **BOOK → “Add to Shows”** button writes schedule rows to `live/data/shows.json`.
  - **TOUR → “Add to Tours”** button writes a tour row to `live/data/tours.json`.
  - Backend endpoints: `POST /live/apply/book` and `POST /live/apply/tour` with atomic JSON writes.
  - Optional dedupe support to prevent duplicate BOOK entries by `(artist, date)`.
- LIVE Shows table now displays **Territory** (supports values like “UK and Europe”), with backwards-compatible fallback for legacy `country` fields.

**Notes / Behavioral changes:**
- Running an agent (`▶ Run`) continues to save per-run outputs under `live/data/<agent>/...` for audit/debug.
- Schedule tables (Shows/Tours) update only when using the explicit **Apply** actions.

**Migration:**
- No database migration required.
- If you have legacy `live/data/shows.json` entries using `country`, they will continue to display via fallback.
  - Optional: migrate data by renaming `country` → `territory` in `shows.json` for consistency.

---
## v1.2.0 (March 27, 2026) — Dashboard Hardening & Team-Ready Release

**Highlights:**
- Check-in and webhook endpoints fully robust against invalid/missing artist slugs (no more `/undefined` API calls).
- All artist actions guarded in frontend (`STATE.slug` required for API).
- Friendly toast and inline error handling for all main dashboard actions.
- Minimal automated backend tests for check-in/webhook (see `/tests/test_api.py`).
- Improved CONTRIBUTING and .env.example for new dev onboarding.
- Updated README and test coverage guidelines.

**Migration:**  
Just update local repo, install any new dependencies, and copy `.env.example` to `.env` as needed.

## 🚦 Project Current State (as of March 27, 2026)

**Core Features:**
- **Department Hub:** A central page for navigation between four business domains (Label, Studio, Live, Platform Ops), each with its own dashboard and agent suite.
- **Multi-Agent Framework:** Pluggable, Python-based agents for business process automation (e.g., client management, audio session coordination, tour routing).
- **Web Interface:** Central Flask app with modular blueprints per department and standardized cross-department navigation.
- **LLM & Service Configuration:** In-app management of language model settings and service health monitoring.
- **Real-Time Operations:** Agent tasks and business workflows update dashboards live.
- **Robust Agent Output (NEW):** Agents now use LLM streaming to generate, validate, and persist actionable checklists and recommendations as structured JSON, automatically saved for artist/project history and dashboard integration.

**Recent Focus Areas:**
- Navigation overhaul: Hub-and-spoke navigation, department blueprints, and improved dashboard “Back to Departments” UX.
- Department and agent expansion: Increasing the granularity and number of business agents; all departments are now accessible via a unified hub.
- Platform Ops: Integrated admin, model config, and health checks for a system overview.
- **LLM Agent Runner Overhaul (NEW):** Reliable agent output streaming and validation, persistent JSON file writing, improved error handling, and schema-first agent output.

- Departmental structuring: MAESTRO split into 3 business domains (Label, Studio, Live), each with specialized agent suites and dashboards.
- Pluggable agent framework: Python base class (`core/base_agent.py`); over 16 agents for client, studio, and live operations.
- Flask blueprint system for clean, modular, and extensible routing.
- Unified error handling, live output streaming, and UI improvements.

**Migration:**  
No data migration required; dependency update and web dashboard restart only.

---

## 🚧 Known Limitations / Open TODOs

- **Artist Card UI**: Still under repair—affects Label dashboard details.
- **Role Management:** User/admin role-based permissions are basic.
- **Analytics:** Advanced platform metrics visualizations are in progress, basic stats only.
- **Testing:** End-to-end and cross-department test coverage incomplete but improving.
- **Agent Extensibility:** Some agents are stubs awaiting full implementation.

---

## 🗺️ Roadmap (2026+)

| Timeframe | Milestone                                                                |
|-----------|-------------------------------------------------------------------------|
| Q2 2026   | Documentation overhaul; test suite expansion; agent workflow hardening   |
| Q3 2026   | New connectors/adapters (music metadata, CRMs, finance); richer analytics|
| Q4 2026   | Plugin/extension API for custom agents; advanced permissioning           |
| 2027+     | Multi-label SaaS launch; enterprise features; third-party integrations   |

---

## 📝 How To Upgrade / Contribute

- Always review [README.md](./README.md) and [docs/assets/] for latest onboarding steps and screenshots.
- For issues or improvements, open a [GitHub issue](https://github.com/lrrecords/maestro-ai/issues) or submit a PR.

---

**Full changelogs:**  
- [Releases page](https://github.com/lrrecords/maestro-ai/releases)
- [Changelog for v0.8.0](https://github.com/lrrecords/maestro-ai/releases/tag/v0.8.0)
- [Changelog for v0.7.0](https://github.com/lrrecords/maestro-ai/releases/tag/v0.7.0)

---