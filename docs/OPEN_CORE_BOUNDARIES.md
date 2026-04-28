# Maestro AI Open Core Boundaries

This document defines which modules, agents, and features are part of the open core (open source) and which are premium/proprietary for the Open Core model.

---

## Open Core (Open Source)

**Included:**
- Orchestration framework (core/)
  - base_agent.py, job_store.py, llm_client.py, etc.
- Agent registry and loader
- Dashboard and modular blueprints (dashboard/)
- Basic agents (examples from agents/, studio/agents/, live/agents/)
- Data models and storage (data/)
- CLI tools and pipeline runners (scripts/)
- Documentation (README.md, CONTRIBUTING.md, docs/)
- Templates and static assets (templates/, static/)
- Integration hooks (webhooks, n8n, etc.)

---

## Premium/Proprietary

**Not included in open core:**
- Advanced/specialized agents (e.g., advanced Label Ops, Studio Intelligence, Tour Logistics)
- Premium analytics, reporting, and integrations
- Managed SaaS/cloud deployment scripts and configs
- Enterprise features (multi-label, advanced permissions, onboarding)
- Any code in `premium_agents/`, `enterprise/`, or private repositories
- Example: `FocusAgent` (CEO Priority Queue, premium_agents/focus.py)

---

## Notes
- The open core must run and be useful without any premium code present.
- Premium features are loaded dynamically if available, but their absence does not break the platform.
- Dynamic agent discovery is implemented; agents are listed at `/agents` and can be executed via `/agents/run/<agent_name>`.
- Extension points and APIs are documented for community and third-party contributions.

---

_Last updated: April 28, 2026_
