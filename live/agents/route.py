from core.base_agent import BaseAgent

class RouteAgent(BaseAgent):
    department  = "live"
    name        = "ROUTE"
    description = "Tour routing and travel optimisation."

    FIELDS = [
        {"key": "cities",         "label": "Cities",          "type": "tags",   "placeholder": "e.g. London, Manchester, Glasgow", "required": True},
        {"key": "home_city",      "label": "Home City",       "type": "text",   "placeholder": "e.g. London",                     "required": True},
        {"key": "start_date",     "label": "Start Date",      "type": "text",   "placeholder": "e.g. 2026-04-01"},
        {"key": "end_date",       "label": "End Date",        "type": "text",   "placeholder": "e.g. 2026-04-30"},
        {"key": "transport_mode", "label": "Transport Mode",  "type": "select", "options": ["van", "fly", "train", "mixed"]},
    ]

    def run(self, context: dict) -> dict:
        return {"agent": self.name, "department": self.department,
                "status": "stub", "message": "ROUTE scaffolded — wire self.llm() to activate.",
                "context": context}