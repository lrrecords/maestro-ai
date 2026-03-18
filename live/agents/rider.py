from core.base_agent import BaseAgent

class RiderAgent(BaseAgent):
    department  = "live"
    name        = "RIDER"
    description = "Technical and hospitality rider management."

    FIELDS = [
        {"key": "artist",                   "label": "Artist",             "type": "text",     "placeholder": "e.g. Bicep",           "required": True},
        {"key": "show_dates",               "label": "Show Dates",         "type": "tags",     "placeholder": "e.g. 2026-04-02"},
        {"key": "stage_plot",               "label": "Stage Plot Notes",   "type": "textarea", "placeholder": "e.g. 2x CDJs, 1x DJM mixer, monitors L/R"},
        {"key": "hospitality_requirements", "label": "Hospitality Notes",  "type": "textarea", "placeholder": "e.g. Vegan catering, 2 private dressing rooms"},
    ]

    def run(self, context: dict) -> dict:
        return {"agent": self.name, "department": self.department,
                "status": "stub", "message": "RIDER scaffolded — wire self.llm() to activate.",
                "context": context}