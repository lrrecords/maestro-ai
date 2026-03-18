from core.base_agent import BaseAgent

class MerchAgent(BaseAgent):
    department  = "live"
    name        = "MERCH"
    description = "Merchandise planning, inventory, and settlement."

    FIELDS = [
        {"key": "artist",              "label": "Artist",              "type": "text",     "placeholder": "e.g. Bicep",                  "required": True},
        {"key": "expected_attendance", "label": "Expected Attendance", "type": "number",   "placeholder": "e.g. 800"},
        {"key": "show_dates",          "label": "Show Dates",          "type": "tags",     "placeholder": "e.g. 2026-04-02, 2026-04-15"},
        {"key": "existing_inventory",  "label": "Existing Inventory",  "type": "textarea", "placeholder": "e.g. 50x T-shirts (L), 20x hoodies (M)"},
    ]

    def run(self, context: dict) -> dict:
        return {"agent": self.name, "department": self.department,
                "status": "stub", "message": "MERCH scaffolded — wire self.llm() to activate.",
                "context": context}