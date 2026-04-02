# Agents

Maestro AI agents are organized by **department**, mirroring how independent music operations run day-to-day.

This repo currently includes agents in these locations:

## Label (roster + release operations)

Located in: `scripts/agents/`

- `bridge.py` — **BRIDGE** (artist relations / follow-ups / health checks)
- `vinyl.py` — **VINYL** (release operations / checklists / timelines)
- `echo.py` — **ECHO** (content & marketing planning)
- `atlas.py` — **ATLAS** (analytics / reporting)
- `forge.py` — **FORGE** (automation / tooling)
- `sage.py` — **SAGE** (weekly planning / priorities)

## Studio (sessions + production ops)

Located in: `studio/agents/`

- `ask_ai.py` — **ASK_AI** (general studio assistant / Q&A)
- `client.py` — **CLIENT** (client management)
- `craft.py` — **CRAFT** (production workflow / checklists)
- `mix.py` — **MIX** (mix workflow support)
- `rate.py` — **RATE** (pricing / quoting)
- `schema.py` — **SCHEMA** (data/schema utilities)
- `session.py` — **SESSION** (session coordination)
- `signal.py` — **SIGNAL** (comms / follow-ups / notifications)
- `sound.py` — **SOUND** (audio-related workflow support)

## Live (shows + touring ops)

Located in: `live/agents/`

- `book.py` — **BOOK** (booking workflow)
- `merch.py` — **MERCH** (merch planning)
- `promo.py` — **PROMO** (promotion workflow)
- `rider.py` — **RIDER** (rider generation / parsing)
- `route.py` — **ROUTE** (routing / travel sanity)
- `schema.py` — **SCHEMA** (data/schema utilities)
- `settle.py` — **SETTLE** (settlement reconciliation)
- `tour.py` — **TOUR** (tour synthesis / planning)

## Platform Ops

Platform Ops is intentionally focused on **configuration, model routing, and health monitoring** rather than “agents” in the same sense as Label/Studio/Live.

---