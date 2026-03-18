from __future__ import annotations
from core.base_agent import BaseAgent

class BookAgent(BaseAgent):
    department  = "live"
    name        = "BOOK"
    description = "Venues, holds, deal negotiation, contract tracking."

    FIELDS = [
        {"key": "artist",    "label": "Artist",        "type": "text",   "placeholder": "e.g. Bicep",               "required": True},
        {"key": "dates",     "label": "Target Dates",  "type": "tags",   "placeholder": "e.g. 2026-04-02, 2026-04-15"},
        {"key": "capacity",  "label": "Min. Capacity", "type": "number", "placeholder": "e.g. 500"},
        {"key": "territory", "label": "Territory",     "type": "text",   "placeholder": "e.g. UK"},
        {"key": "deal_type", "label": "Deal Type",     "type": "select", "options": ["flat", "versus", "guarantee"]},
    ]

    def run(self, context: dict) -> dict:
        return {"agent": self.name, "department": self.department,
                "status": "stub", "message": "BOOK scaffolded — wire self.llm() to activate.",
                "context": context}