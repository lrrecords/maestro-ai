# 🎼 RASCALWORKS OS — Release History

## v1.5.2 (August 2026) — Branding Completion + Palette Refresh

**Highlights:**
- **Landing-page branding completion:** Final legacy footer and pricing/waitlist naming on the docs landing page were aligned to Rascalworks naming (including brand-mark glyph and tier copy updates).
- **Rascalworks palette rollout:** App-facing UI styling now uses a centralized Rascalworks token palette (`--rw-*`) for primary headers, buttons, active states, links, and brand accents.
- **Blue-to-orange brand direction applied:** Primary interactions now follow the logo-aligned metallic blue-to-orange gradient treatment across key templates.
- **Semantic status colors preserved:** Success/approved (green), warning/pending (amber), and destructive/error (red) indicators were intentionally left unchanged.
- **Styling-only scope:** Updates were constrained to templates and stylesheet token usage; no application logic, route behavior, or workflow changes were introduced.

**Migration:**
- No database migration required.
- Clear browser cache (or hard refresh) if old CSS appears after deploy.
- If you maintain custom theme overrides, update them to reference the new `--rw-*` custom properties to stay aligned with core styling.

## v1.5.1 (August 2026) — Multi-Provider LLM Routing + Marketing Update Pack

**Highlights:**
- **LLM provider expansion:** Runtime routing now supports `openai` (ChatGPT), `deepseek`, `gemini`, `openai_compatible`, and `litellm` in addition to existing `ollama` and `anthropic` paths.
- **Provider aliases added:** `chatgpt`/`gpt` map to `openai`, and `claude` maps to `anthropic` for smoother config migration.
- **Crew orchestration parity:** Crew-level LLM configuration now mirrors provider flexibility so the same business workflows can run across local-first and cloud model backends.
- **Platform Ops provider options updated:** Provider selector now lists expanded model backends, with API key handling kept in environment secrets.
- **New setup guide:** Added a dedicated provider matrix and copy/paste env blocks at `docs/LLM_PROVIDER_SETUP_MATRIX.md`, linked from README and quickstart.
- **Marketing update pack added:** `docs/MAESTRO_MARKETING_PLAN.md` now includes an August 2026 ready-to-post Discord/LinkedIn update set, plus three alternate variants.
- **Repository hygiene:** `.specstory` artifacts were removed from git tracking to prevent noisy non-product file churn.

**Migration:**
- No database migration required.
- Review `.env.example` and choose `LLM_PROVIDER` based on your deployment goals.
- For cloud providers, set the corresponding API key env vars (`OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`, or generic OpenAI-compatible values).

## v1.5.0 (July 2026) — Open Core Maturity, SCRIBE Pipeline, and Hosted Operations

**Highlights:**
- **Open Core release maturity:** Clearer boundary between open core and premium modules, with release and maintenance documentation tightened for public contributors.
- **Hosted operations validated:** Live hosted environment (`https://maestro-ai.up.railway.app`) verified with smoke testing workflows and reporting artifacts for repeatable checks.
- **Canonical deployment path standardized:** `Procfile -> app.py -> dashboard.app:app` documented as the authoritative launch chain for Railway and production-aligned environments.
- **SCRIBE content pipeline expanded:** Dedicated SCRIBE dashboard/approval/edit/admin workflows documented and integrated (`/label/scribe/`, approvals, normalization, export).
- **FOCUS Brief hardening:** Config-driven data sources, API endpoint, and widget flow documented and tested (`/label/api/focus/brief`, `tests/test_focus_brief.py`).
- **Documentation refresh:** README and onboarding flow streamlined for both self-hosted and hosted users, with consolidated auth/security guidance.
- **Compliance evidence archive:** ISO 27001 evidence pack, crosswalk, release approval, backup restore proof, incident drill, and supplier review records were added for audit-oriented traceability.

**Migration:**
- No database migration required.
- Pull latest changes, review `.env.example`, and verify required auth values (`MAESTRO_TOKEN`, `WEBHOOK_SECRET`, `SECRET_KEY`) before production deploy.

---

## v1.4.0 (April 9, 2026) — CrewAI, CEO Command Centre, and Modular Workflow Release

**Highlights:**
- **CrewAI Integration:** Modular, role-based agent orchestration for Label, Studio, Live, and Platform Ops. Easily extend or customize agents and workflows per user or label.
- **CEO Command Centre:** One-click mission orchestration for campaigns, releases, emergencies, and more. Handles approvals, cancellations, and multi-step workflows.
- **Stepwise Mission Runner:** Improved backend logic for instant cancellation and per-task execution, with robust error handling.
- **Approval Queue:** All protected actions (mass email, public posts, spend, etc.) routed through a CEO approval queue, with dashboard management.
- **Run Agents & Full Pipeline:** Directly run any agent or the full pipeline for granular control and testing.
- **n8n & API Automation:** Seamless integration with n8n and external APIs for notifications, CRM, distribution, and more.
- **Modernized UI:** “Nice card” output, agent icons, live streaming, and improved navigation.
- **Documentation Overhaul:** Updated README.md, IMPLEMENTATION_GUIDE.md, and mission briefs for onboarding and demo use.
- **Artist Onboarding:** Add artist JSON files to `data/artists/` for instant dashboard integration.

**Migration:**
- No database migration required.
- Update your repo, install new dependencies, and review `.env.example` for new settings.

---
## What is RASCALWORKS OS?

RASCALWORKS OS is an AI-powered, multi-agent business operating system designed for independent labels, studios, and live music organizations. The platform provides a unified web dashboard, organizing core operations into four domains (Label, Studio, Live, Platform Ops) each with pluggable agents for end-to-end workflow automation.

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

## 🚦 Project Current State (as of July 2026)

**Core Features:**
- **Department Hub:** A central page for navigation between four business domains (Label, Studio, Live, Platform Ops), each with its own dashboard and agent suite.
- **Multi-Agent Framework:** Pluggable, Python-based agents for business process automation (e.g., client management, audio session coordination, tour routing).
- **Web Interface:** Central Flask app with modular blueprints per department and standardized cross-department navigation.
- **LLM & Service Configuration:** In-app management of language model settings and service health monitoring.
- **Real-Time Operations:** Agent tasks and business workflows update dashboards live.
- **Robust Agent Output (NEW):** Agents now use LLM streaming to generate, validate, and persist actionable checklists and recommendations as structured JSON, automatically saved for artist/project history and dashboard integration.
- **Hosted Access (NEW):** Railway-hosted MVP is available for guided onboarding and operational smoke testing.
- **SCRIBE Content Operations (NEW):** Structured proposal generation, approval queue, editor flow, and admin normalization/export paths are active.
- **Containerized Deployment (NEW):** Dockerfile and Procfile paths are documented and operational for deployment workflows.

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
- [Changelog for v1.5.0](https://github.com/lrrecords/maestro-ai/releases/tag/v1.5.0)
- [Changelog for v0.8.0](https://github.com/lrrecords/maestro-ai/releases/tag/v0.8.0)
- [Changelog for v0.7.0](https://github.com/lrrecords/maestro-ai/releases/tag/v0.7.0)

---