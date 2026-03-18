from core.base_agent import BaseAgent

class SettleAgent(BaseAgent):
    department  = "live"
    name        = "SETTLE"
    description = "Financial settlement and reconciliation."

    FIELDS = [
        {"key": "gross_box_office", "label": "Gross Box Office (£)", "type": "number",   "placeholder": "e.g. 12000",                        "required": True},
        {"key": "deal_memo",        "label": "Deal Memo",             "type": "textarea", "placeholder": "e.g. 70/30 vs £3,000 guarantee"},
        {"key": "expenses",         "label": "Deductible Expenses (£)","type": "number",  "placeholder": "e.g. 1500"},
        {"key": "currency",         "label": "Currency",              "type": "select",   "options": ["GBP", "USD", "EUR"]},
    ]

    def run(self, context: dict) -> dict:
        return {"agent": self.name, "department": self.department,
                "status": "stub", "message": "SETTLE scaffolded — wire self.llm() to activate.",
                "context": context}