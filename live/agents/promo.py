from core.base_agent import BaseAgent

class PromoAgent(BaseAgent):
    """
    PROMO — Marketing & promotional strategy for shows and tours.
    Inputs: artist, show_dates, cities, target_audience, budget, platforms, objectives
    """
    department = "live"
    name = "PROMO"
    description = "Marketing and promotional strategy."

    FIELDS = [
        {"key": "artist",          "label": "Artist",               "type": "text",     "placeholder": "e.g. Bicep", "required": True},
        {"key": "cities",          "label": "Cities",               "type": "tags",     "placeholder": "London, Manchester, Glasgow"},
        {"key": "show_dates",      "label": "Show Dates",           "type": "tags",     "placeholder": "2026-04-02, 2026-04-15"},
        {"key": "target_audience", "label": "Target Audience",      "type": "text",     "placeholder": "Fans of X / genre / scene"},
        {"key": "budget",          "label": "Budget",               "type": "number",   "placeholder": "500"},
        {"key": "platforms",       "label": "Platforms",            "type": "tags",     "placeholder": "instagram, tiktok"},
        {"key": "objectives",      "label": "Objectives",           "type": "textarea", "placeholder": "Sell out first three dates, grow mailing list, etc."},
    ]

    def run(self, context: dict) -> dict:
        prompt = self.build_prompt(context)
        try:
            llm_result = self.llm(prompt)
            structured = self.parse_json(llm_result)
        except Exception as e:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "message": f"PROMO LLM error: {str(e)}",
                "context": context,
            }
        return {
            "agent": self.name,
            "department": self.department,
            "status": "complete",
            "message": llm_result,
            "data": structured,
            "context": context,
        }

    def build_prompt(self, context: dict) -> str:
        artist = context.get("artist", "[artist]")
        cities = ", ".join(context.get("cities", [])) if isinstance(context.get("cities"), list) else str(context.get("cities", ""))
        show_dates = ", ".join(context.get("show_dates", [])) if isinstance(context.get("show_dates"), list) else str(context.get("show_dates", ""))
        target_audience = context.get("target_audience", "")
        budget = context.get("budget", "[unknown]")
        platforms = ", ".join(context.get("platforms", [])) if isinstance(context.get("platforms"), list) else str(context.get("platforms", ""))
        objectives = context.get("objectives", "")

        return (
            f"You are an expert music marketing agent. Plan a marketing and promo campaign for this tour:\n"
            f"Artist: {artist}\n"
            f"Cities: {cities}\n"
            f"Show dates: {show_dates}\n"
            f"Target audience: {target_audience}\n"
            f"Budget: {budget}\n"
            f"Platforms: {platforms}\n"
            f"Objectives: {objectives}\n"
            "Respond ONLY with strict JSON using this schema:\n"
            "{\n"
            "  \"highlights\": [string],              // e.g. 'sell out 3x London shows', 'grow TikTok by 1000 fans'\n"
            "  \"priority_channels\": [string],       // e.g. 'instagram', 'tiktok', 'email', 'press'\n"
            "  \"action_items\": [                    // main concrete marketing moves\n"
            "    {\"label\": string, \"deadline\": string, \"assigned_to\": string, \"notes\": string}\n"
            "  ],\n"
            "  \"budget_breakdown\": [                // suggested spend by category\n"
            "    {\"category\": string, \"amount\": number, \"notes\": string}\n"
            "  ],\n"
            "  \"risk_notes\": [string],              // e.g. 'budget tight for TikTok ads', 'press window is short'\n"
            "  \"strategy_notes\": string             // short summary\n"
            "}\n"
            "Always fill all fields, leave lists empty for N/A, but never omit keys. JSON only, no markdown nor explanations outside JSON."
        )