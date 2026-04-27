# 🎼 MAESTRO AI — IWAI Survey Synthesis & Feature Expansion Plan
> Generated: April 22, 2026 | For: Brett @ LRRecords / Maestro AI v1.4.0+

---

## 0. TL;DR — What The Survey Is Really Saying (For Us)

The IWAI survey of 200+ high-performance professionals mirrors exactly what an independent music label founder/CEO faces:

| Survey Theme | Brett's Reality |
|---|---|
| "I know what to do — I just can't get it all done" | Running a label, studio, live ops + building Maestro |
| Capacity & throughput dominate short-term pain | Release cycles, artist comms, session scheduling, admin |
| Quality pressure never goes away | "Faster with AI — but will the work stay excellent?" |
| Personal life taking silent hits | Nights, weekends, creative energy drained by admin |
| Long-term: become a better human, not just faster | More music. More gardening. More life. |

**The insight that hits hardest:**
> *"The real ROI often comes from back-office and operational improvements — not flashy front-of-house demos."*

That is Maestro's core value proposition, stated externally, validated by 200+ peers. This is your positioning language.

---

## 1. IWAI Insights → Maestro Feature Map

### 1A. Immediate (0–3 Months): "Keep the wheels from coming off"

| Survey Want | Maestro Now | Maestro Enhancement |
|---|---|---|
| Focus & Productivity Flow | Hub navigation | **FOCUS Agent** — weekly priority brief, "your 3 most important things today" |
| Decision Support Dashboard | CEO Approval Queue | **Decision Inbox** — pending decisions surfaced with context, not just raw approvals |
| Meeting/Calendar Management | *(not yet)* | **SCHEDULE Agent** — calendar brief, prep notes, follow-up generator |
| Executive Briefing & Intelligence | SAGE (partial) | **SAGE Daily Brief** — morning digest of label health, artist flags, pending actions |
| Stakeholder Communication | BRIDGE | **BRIDGE Comms Queue** — draft emails/messages for CEO review before send |

### 1B. Medium-Term (3–12 Months): "Systemize my value"

| Survey Want | Maestro Now | Maestro Enhancement |
|---|---|---|
| Strategic Planning | CEO Command Centre | **CEO Mission Templates** — pre-built missions for release campaigns, quarter planning |
| Market Intelligence | ECHO | **ECHO Market Pulse** — weekly genre/streaming trend brief relevant to label roster |
| Reports & Presentations | *(outputs exist, no assembly)* | **REPORT Agent** — assembles agent outputs into a shareable PDF/deck brief |
| Financial Strategy & Budgeting | *(not yet)* | **LEDGER Agent** — session costs, royalty projections, tour P&L, budget tracking |
| Professional Network | BRIDGE | **BRIDGE Relationship Map** — industry contact log, follow-up reminders |

### 1C. Long-Term (1–3 Years): "Become a better human"

| Survey Want | Maestro Opportunity |
|---|---|
| Innovation & Transformation | Maestro IS this — dog-food it for LRRecords first, then SaaS |
| Leadership & Skill Development | **MENTOR Mode** — weekly CEO reflection prompts, goal check-ins |
| Personal Growth & Mastery | **Life Tab** in Hub — energy, creative output tracking, non-work wins |
| Legacy & Culture Building | **FORGE Culture** — artist onboarding, label values, brand voice docs |
| Long-term Financial Planning | **LEDGER Vision** — 3-year label revenue projections, SaaS revenue modelling |

---

## 2. New Agents & Enhancements — Build Plan

### 🆕 FOCUS Agent (Label Department)
**What it does:** Surfaces the CEO's 3 highest-priority actions for the day/week. Pulls from: pending missions, approval queue, artist flags, upcoming releases.
**Tech:** Aggregates Redis job store + shows/tours JSON + artist data → Qwen2.5 brief
**UI:** Card on Hub landing page. Refreshes on login.
**Value:** Saves 20–30 min/day of "where was I?" cognitive load.

---

### 🔧 SAGE Enhancement — Daily Brief
**Current state:** SAGE exists as an agent.
**Enhancement:** Make SAGE the morning intelligence layer.
- Pulls: pending approvals, overdue missions, artist analytics flags, upcoming release dates
- Generates: 5-bullet executive brief in plain English
- Delivers via: Hub widget + optional n8n webhook → email/Slack
**Prompt hook for Qwen2.5:** See Section 4A.

---

### 🆕 LEDGER Agent (Platform Ops or Label)
**What it does:** Financial tracking for label operations.
- Session cost tracking (from STUDIO/SESSION data)
- Tour P&L summary (from LIVE/SETTLE data)
- Royalty projection estimates
- Budget vs actual tracking
**Tech:** Reads from existing data JSONs, generates structured financial summary
**UI:** New card in Label dashboard, exportable as CSV/PDF
**Value:** Eliminates spreadsheet hell for label finances.

---

### 🔧 BRIDGE Enhancement — Comms Queue
**Current state:** BRIDGE handles communications.
**Enhancement:** Staged comms workflow.
- Draft → CEO Review → Approve/Edit → Send via n8n
- Tracks sent history per artist/contact
- Templates for: release announcements, booking enquiries, press pitches, fan comms
**Value:** Nothing goes out unreviewed. Human always in loop on external comms.

---

### 🆕 REPORT Agent (Label Department)
**What it does:** Assembles outputs from other agents into a formatted report.
- Inputs: VINYL, ECHO, ATLAS, SAGE outputs for a given artist or period
- Output: Markdown → PDF brief (via existing PDF skill)
- Use cases: Artist review deck, label quarterly report, investor brief
**Value:** Hours saved assembling context across agents.

---

### 🆕 SCHEDULE Agent (Studio or Platform Ops)
**What it does:** Calendar-aware session and task management.
- Reads: upcoming sessions, show dates, release milestones
- Generates: weekly schedule brief, conflict alerts, prep notes
- Integrates with: n8n → Google Calendar webhook
**Value:** The "Meeting Optimization" item from the survey — applied to studio/label life.

---

## 3. Dashboard & Hub Enhancements

### Hub — "Command Strip" (Priority View)
Add a persistent top section to the Hub showing:
```
[ 🔴 2 Pending Approvals ] [ 🟡 1 Artist Flag ] [ 🟢 Next Release: 14 days ] [ SAGE Brief ▼ ]
```
One-click access to the things that matter most. No hunting.

---

### CEO Command Centre — Decision Context Panel
Current: Approvals show action type + requestor.
Enhancement: Show **why** the decision matters.
- Risk level (low/medium/high)
- Suggested action from SAGE
- Related mission context
- One-click Approve / Edit & Approve / Reject with note

---

### Label Dashboard — Artist Health Cards
Each artist card gets a health signal:
- 🟢 On track (release schedule, analytics trending up)
- 🟡 Needs attention (upcoming deadline, content gap)
- 🔴 Flagged (overdue deliverable, analytics drop)
**Driven by:** ATLAS + VINYL + ECHO outputs aggregated per artist.

---

### New Tab: "Life" (Hub Level)
Inspired by the survey's "become a better human" theme.
A lightweight personal layer for the CEO:
- Weekly creative output log (tracks what music you actually made)
- Energy check-in (1–5 scale, stored in Redis)
- "Hours saved by Maestro this week" counter (gamification)
- Upcoming personal milestones (not just label milestones)
**This is low-code, high-meaning.** It makes Maestro feel like a partner, not just a tool.

---

## 4. Prompts for AI Build Partners

### 4A. Qwen2.5 (Ollama) — SAGE Daily Brief System Prompt

```
You are SAGE, the intelligence layer for a professional music label management system called Maestro AI.

Your role: Generate a concise daily executive brief for the label CEO.

Input data will be provided as JSON. It may include: pending approval queue items, active missions, upcoming show dates, artist flags, and recent agent outputs.

Output format — respond ONLY with valid JSON, no markdown, no preamble:
{
  "date": "YYYY-MM-DD",
  "headline": "One sentence summary of today's priority",
  "priority_actions": [
    { "rank": 1, "action": "...", "context": "...", "urgency": "high|medium|low" },
    { "rank": 2, "action": "...", "context": "...", "urgency": "high|medium|low" },
    { "rank": 3, "action": "...", "context": "...", "urgency": "high|medium|low" }
  ],
  "flags": ["..."],
  "upcoming_in_7_days": ["..."],
  "one_win": "Something positive from the last 24 hours"
}

Rules:
- Maximum 3 priority actions
- Be specific — name the artist, mission, or task
- Never invent data not present in the input
- If input is empty or sparse, say so in headline and return minimal JSON
```

---

### 4B. Cursor — FOCUS Agent Implementation Prompt

```
## Context (carry forward)
- Project: Maestro AI v1.4.0 — Flask, CrewAI, Redis, Ollama/Anthropic API
- Stack: Flask blueprints per department, Jinja2 templates, Redis for job/mission store
- Data sources: live/data/shows.json, data/artists/, Redis mission store, label approval queue
- LLM: Ollama with Qwen2.5.8 (local), Anthropic as fallback
- Existing agents: ATLAS, VINYL, ECHO, FORGE, BRIDGE, SAGE (Label); full Studio and Live suites
- Auth: MAESTRO_TOKEN middleware on all department endpoints
- DO NOT modify existing agent logic, templates, or data structures unless explicitly required

## Task
Implement a new FOCUS agent endpoint and Hub widget for Maestro AI.

## Deliverables

1. New Flask route: GET /label/api/focus/brief
   - Aggregates: Redis pending missions (status=pending), label approval queue items, artists with flags, shows within 14 days from live/data/shows.json
   - Calls Ollama (model from OLLAMA_MODEL env var) with the SAGE daily brief system prompt
   - Returns JSON: { priority_actions: [...], flags: [...], upcoming_in_7_days: [...], headline: "..." }
   - Auth: requires MAESTRO_TOKEN

2. Hub template widget: templates/hub.html
   - Add a "Command Strip" section at the top of the hub page
   - Shows: pending approval count (badge), FOCUS brief headline, "View Brief" expandable panel
   - Fetches /label/api/focus/brief on page load via fetch()
   - Renders priority_actions as ranked cards (rank, action, urgency colour: red/amber/green)
   - Graceful degradation: if API call fails, show "Brief unavailable — check Maestro logs"

3. File scope: touch ONLY these files
   - dashboard/label/routes.py (add route)
   - templates/hub.html (add widget)
   - Do NOT modify any other files

After each step output: ✅ [what was completed]
Stop and ask before: creating new files outside the above list, modifying existing agent logic, or touching data files.
```

---

### 4C. Copilot — LEDGER Agent Scaffold Prompt

```
## Context
- Project: Maestro AI v1.4.0, Flask + Redis + JSON data store
- Existing data: live/data/shows.json (has settle/gross fields), data/artists/ (artist JSON files)
- Studio SESSION agent outputs saved to: studio/data/session/*.json
- DO NOT modify existing endpoints or data structures
- Match existing Flask blueprint pattern used in dashboard/label/ and dashboard/live/

## Task
Scaffold a new LEDGER agent for financial tracking in the Label department.

## Deliverables

1. New file: dashboard/label/ledger.py
   - Flask Blueprint: ledger_bp, url_prefix='/label/ledger'
   - Route GET /label/ledger/ — renders ledger dashboard template
   - Route GET /label/api/ledger/summary — returns JSON financial summary:
     {
       "session_costs": { "total": 0, "this_month": 0, "sessions": [] },
       "live_revenue": { "total_gross": 0, "total_net": 0, "shows": [] },
       "artist_count": 0,
       "period": "last_30_days"
     }
   - Reads from: live/data/shows.json (gross/net/expenses fields if present), studio session JSONs
   - If fields missing in source data, default to 0 and note as "no data yet"
   - Auth: requires MAESTRO_TOKEN header check (match pattern in existing routes)

2. New file: templates/label/ledger.html
   - Extends base template (match existing label dashboard pattern)
   - Shows: summary cards (total session costs, live gross, live net)
   - Table: recent shows with gross/expenses/net columns
   - "No data yet" empty state if JSON files are empty or missing fields
   - Style consistent with existing label dashboard cards

3. Register blueprint in dashboard/app.py (add import + app.register_blueprint)

After each step output: ✅ [what was completed]
Stop and ask before: modifying shows.json or any artist data files, changing auth middleware, or touching any file not listed above.
```

---

### 4D. Claude (this chat) — CEO Mission Template Generator

```
You are the Maestro AI mission planning system. Your job is to generate CEO Mission briefs for an independent music label.

A CEO Mission is a structured multi-step workflow that Maestro will orchestrate across agents. It must be specific, achievable, and map to real agent capabilities.

Available agents: ATLAS (artist analytics), VINYL (release planning), ECHO (content/social), FORGE (brand/creative), BRIDGE (communications), SAGE (intelligence), BOOK (live booking), ROUTE (tour routing), SETTLE (financial settlement), MERCH (merchandise), PROMO (promotion), CLIENT (studio client management), SESSION (studio scheduling).

Generate a CEO Mission brief for: [MISSION_TYPE]

Output format:
{
  "mission_name": "...",
  "mission_type": "...",
  "trigger": "What initiates this mission",
  "agents_involved": ["AGENT1", "AGENT2"],
  "steps": [
    { "step": 1, "agent": "...", "task": "...", "output": "...", "requires_approval": true|false }
  ],
  "success_criteria": "...",
  "estimated_time_saved": "X hours/week",
  "human_touchpoints": ["List of moments where CEO reviews/approves before proceeding"]
}
```

**Pre-built Mission Types to generate first:**
- `new_artist_onboarding`
- `single_release_campaign`
- `tour_planning_initiation`
- `quarterly_label_review`
- `emergency_artist_issue`

---

## 5. n8n Automation Opportunities

Based on the survey's "operational back-office" insight, these n8n workflows will save the most time:

| Workflow | Trigger | Action | Time Saved |
|---|---|---|---|
| SAGE Morning Brief | Daily 7am | Generate brief → email to Brett | 20 min/day |
| Approval Alert | New item in CEO queue | Push notification → phone | Instant awareness |
| Release Countdown | 14 days before release date | Trigger VINYL + ECHO checklist mission | Hours of manual tracking |
| Session Confirmation | New SESSION booking | Email to artist/client via BRIDGE | 10 min/booking |
| Tour Settlement | SETTLE agent completes | Generate PDF → save to Drive | 30 min/show |
| Artist Analytics Alert | ATLAS flags anomaly | Alert to Brett via email | Catch issues early |

All of these are webhook-driven from existing Maestro endpoints — no new backend work required.

---

## 6. Positioning Language (For GitHub, Community, SaaS)

The IWAI survey gave us free market research. Use this language:

**Tagline options:**
- *"The back-office AI your label actually needs — not just demos."*
- *"Multi-agent operations for music professionals who care about quality, not just speed."*
- *"Maestro AI: so you can make more music and spend less time on everything else."*

**For Discord/community outreach:**
> "Built Maestro AI for my own label — it's a multi-agent OS (Flask + CrewAI + Ollama/Anthropic) that handles the operational stuff so I can focus on the creative. Open source, built for independent music orgs. Would love feedback from other agent builders."

---

## 7. Recommended Build Sequence

Given crewai dependency issue is the current blocker:

### Sprint 0 (This Week) — Unblock & Stabilise
1. `pip install crewai` → resolve 500 on mission creation
2. `git commit -am "v1.4.0 final" && git push` — get GitHub in sync
3. Smoke test all endpoints per handover checklist
4. Confirm Qwen2.5.8 is pulled and OLLAMA_MODEL is set

### Sprint 1 (Week 2) — FOCUS + SAGE Brief
1. SAGE Daily Brief endpoint (Prompt 4A for Qwen + Prompt 4B Step 1 for Cursor)
2. Hub Command Strip widget (Prompt 4B Step 2)
3. Wire SAGE brief to n8n morning email

### Sprint 2 (Week 3–4) — LEDGER + BRIDGE Comms Queue
1. LEDGER agent scaffold (Prompt 4C for Copilot)
2. BRIDGE comms queue enhancement
3. Artist Health Card signals on Label dashboard

### Sprint 3 (Month 2) — CEO Mission Templates + REPORT Agent
1. Generate pre-built CEO Missions using Prompt 4D
2. REPORT agent — assembles outputs into PDF brief
3. SCHEDULE agent scaffold

### Ongoing — Life Tab + SaaS Prep
1. "Life" tab in Hub (personal layer)
2. Docker deployment to Railway
3. Multi-label onboarding flow (SaaS foundation)

---

## 8. For Brett — The Human in the Loop

The survey said it best:
> *"You're not asking AI to make you capable. You're asking AI to help you stay excellent without sacrificing your health, relationships, and sense of self."*

Maestro's job — for you personally, before any SaaS — is to:
- **Save 2+ hours/day** of label admin (approvals, comms, scheduling, reporting)
- **Protect creative time** — block it, don't let admin bleed into it
- **Surface what matters** — SAGE brief means no more "where was I?" mornings
- **Give you back weekends** — n8n handles the overnight and weekend monitoring

That's the real product. The SaaS comes after you've lived it.

---

*Document generated by Claude (Maestro AI build partner) | April 22, 2026*
*For questions, next steps, or to continue building: open a new chat with this doc attached.*
