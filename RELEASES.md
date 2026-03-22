# 🎼 MAESTRO AI — Release History

## What is MAESTRO AI?

MAESTRO AI is an AI-powered music industry operations platform built for independent labels, studios, and live music organisations. It provides a unified dashboard ecosystem where specialised AI agents handle complex operational tasks across four core departments: Label, Studio, Live, and Platform Ops. Each department features its own dashboard, data layer, and suite of intelligent agents that can be configured, executed, and monitored through a single authenticated web interface. MAESTRO AI is designed to scale from solo operators to multi-department teams, automating everything from artist development and session booking to tour routing and infrastructure management.

---

## v0.8.0 — Hub & Platform Ops (In Progress: March 20, 2026)

**Navigation overhaul and new department** — MAESTRO adds a centralised Department Hub, introduces Platform Ops as the fourth department, and standardises cross-department navigation.

### 🏢 Updated Department Structure (4 Departments)

MAESTRO now operates as four distinct departments, each implemented as Flask Blueprints:

- **LABEL** (`/`) — Core artist and release operations (original maestro-ai dashboard)
- **STUDIO** (`/studio/`) — Recording and production operations (7 agents)
- **LIVE** (`/live/`) — Performance and touring operations (7 agents)
- **PLATFORM OPS** (`/platform/`) — Infrastructure, model configuration, and system health

### 🆕 What's New

**Department Hub (`/hub`)**
- New centralised landing page after login with four department cards
- Acts as the main navigation point between all departments
- Clean card-based UI consistent with MAESTRO design language

**Platform Ops Department**
- LLM settings management (provider, model, temperature, context window, timeout)
- Service health monitoring (Ollama and n8n status checks)
- Centralised configuration saved to `platform_ops/data/platform_settings.json`
- Real-time health check endpoint (`/platform/api/health`)

**"Back to Departments" Navigation**
- All four dashboards now include a "← Departments" button linking back to `/hub`
- Consistent navigation pattern across the entire platform

**Login Flow Update**
- Authentication now redirects to `/hub` instead of directly to the Label dashboard
- Protected routes redirect to `/login?next=<path>` to preserve intended destination

### 🏗️ Architecture Changes

**Hub-and-Spoke Navigation Model**
- Login → Hub → Department → Hub (back button)
- Label dashboard remains at root (`/`) for backward compatibility
- Hub available at `/hub` as the central navigation point

**Files Added**
- `templates/hub.html` — Department hub page
- `dashboard/app.py` — Updated main application with hub route and blueprint registration

**Files Modified**
- `templates/dept_live.html` (line 113) — Back button now points to `/hub`
- `templates/dept_studio.html` (line 113) — Back button now points to `/hub`
- `platform_ops/web.py` — Added back button to inline HTML template
- `templates/index.html` — Added back button to Label dashboard

### 🔴 Known Issues

- **Label Dashboard — Artist click UI broken:** Clicking on artist cards in the Label dashboard does not load the expected detail view. Root cause under investigation. May be related to route registration changes or template modifications during this release.
- **Label "Back to Departments" button:** Added but not yet fully verified.

### 🎯 Next Steps (v0.8.1)

1. Fix Label dashboard artist click functionality (Priority 1)
2. Verify Label dashboard back button placement and styling
3. Full end-to-end navigation and functionality test across all departments
4. Confirm all agent runners still function correctly after routing changes

---

## v0.7.0 — Department Architecture (Released: March 18, 2026)

**Major architectural evolution** — MAESTRO transitions from a flat 6-agent system to a modular 3-department structure with specialized agent suites.

### 🏢 New Department Structure

MAESTRO now operates as three distinct departments, each implemented as Flask Blueprints:

- **MAESTRO** — Core platform (dashboard, login, agent runner, artist relations)
- **STUDIO** — Recording and production operations (8 agents)
- **LIVE** — Performance and touring operations (8 agents)

### 🤖 Agent Expansion: 6 → 16+

**STUDIO Department (8 agents):**
- `client` — Client relationship management
- `craft` — Creative process optimization
- `llm` — Language model integration
- `mix` — Mixing and mastering workflows
- `rate` — Pricing and rate management
- `schema` — Data structure validation
- `session` — Recording session coordination
- `signal` — Audio signal processing
- `sound` — Sound design and library management

**LIVE Department (8 agents):**
- `book` — Booking and venue management
- `merch` — Merchandise planning and sales
- `promo` — Live event promotion
- `rider` — Technical and hospitality riders
- `route` — Tour routing and logistics
- `schema` — Live event data structures
- `settle` — Financial settlement and reconciliation
- `tour` — Tour planning and management

**MAESTRO Department:**
- Core dashboard and navigation
- User authentication and session management
- Cross-department agent runner
- Artist relationship tracking

### 🏗️ Infrastructure Improvements

**BaseAgent Architecture**
- New `core/base_agent.py` class — all agents inherit shared functionality
- Standardized agent lifecycle and execution patterns
- Unified error handling and logging across departments

**Department Templates & Rendering**
- Department-specific UI templates (`dept_studio.html`, `dept_live.html`)
- Shared renderer layer (`renderers.css`, `renderers.js`)
- Live agent output streaming in browser dashboard

**Blueprint Routing**
- Each department registers as a Flask Blueprint
- Clean URL structure: `/studio/`, `/live/`, `/maestro/`
- Case-insensitive agent resolution (client/CLIENT both work)

### ✅ Verified Functionality

- **ClientAgent** (STUDIO) — fully functional via dashboard
- **SessionAgent** (STUDIO) — confirmed working with live output
- Department navigation and agent discovery working
- Blueprint registration and routing stable
- Agent registry resolves correctly across all departments

### 🔧 Technical Notes

- Repository clean after resolving binary rebase conflict on `docs/assets/MAESTRO_Run_Agents.jpg`
- `.gitignore` updated to exclude `live/data` and `studio/data`
- `update_summary` attribute resolved on BaseAgent class
- Agent execution confirmed through dashboard interface

### 🎯 Migration Path

Existing v0.6.x installations will need to:
1. Update dependencies (`pip install -r requirements.txt`)
2. Restart web dashboard to load new Blueprint structure
3. Navigate to department-specific URLs (`/studio/`, `/live/`)

No data migration required — existing artist profiles and agent outputs remain compatible.

---

*Full changelog and technical details available at: https://github.com/lrrecords/maestro-ai/releases/tag/v0.7.0*