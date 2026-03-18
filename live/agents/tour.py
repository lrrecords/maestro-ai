from __future__ import annotations
from core.base_agent import BaseAgent

class TourAgent(BaseAgent):
    department  = "live"
    name        = "TOUR"
    description = "Strategy synthesiser — coordinates all LIVE agents."

    SUB_AGENTS = ["book", "route", "settle", "rider", "merch", "promo"]

    FIELDS = [
        {"key": "artist",     "label": "Artist",        "type": "text",     "placeholder": "e.g. Bicep",        "required": True},
        {"key": "territory",  "label": "Territory",     "type": "text",     "placeholder": "e.g. UK & Europe"},
        {"key": "start_date", "label": "Start Date",    "type": "text",     "placeholder": "e.g. 2026-04-01"},
        {"key": "end_date",   "label": "End Date",      "type": "text",     "placeholder": "e.g. 2026-04-30"},
        {"key": "show_count", "label": "Target Shows",  "type": "number",   "placeholder": "e.g. 10"},
        {"key": "notes",      "label": "Notes",         "type": "textarea", "placeholder": "Constraints, priorities, any context"},
    ]

    def run(self, context: dict) -> dict:
        return {"agent": self.name, "department": self.department,
                "status": "stub", "message": "TOUR synthesiser scaffolded — will coordinate all LIVE agents when built.",
                "sub_agents": self.SUB_AGENTS, "context": context}