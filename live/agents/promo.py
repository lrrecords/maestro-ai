from core.base_agent import BaseAgent

class PromoAgent(BaseAgent):
    """
    PROMO — Marketing & promotional strategy for shows and tours.

    Context keys: artist, show_dates, cities, target_audience, budget
    """
    department  = "live"
    name        = "PROMO"
    description = "Marketing and promotional strategy."

    def run(self, context: dict) -> dict:
        return {"agent": self.name, "department": self.department,
                "status": "stub", "message": "PROMO scaffolded — wire self.llm() to activate.",
                "context": context}