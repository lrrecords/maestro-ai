from core.base_agent import BaseAgent

class MerchAgent(BaseAgent):
    department = "live"
    name = "MERCH"
    description = "Merchandise planning, inventory, and settlement."

    FIELDS = [
        {"key": "artist",              "label": "Artist",              "type": "text",     "placeholder": "e.g. Bicep",                  "required": True},
        {"key": "expected_attendance", "label": "Expected Attendance", "type": "number",   "placeholder": "e.g. 800"},
        {"key": "show_dates",          "label": "Show Dates",          "type": "tags",     "placeholder": "e.g. 2026-04-02, 2026-04-15"},
        {"key": "price_points",        "label": "Price Points",        "type": "text",     "placeholder": "e.g. 10, 25, 40"},
        {"key": "existing_inventory",  "label": "Existing Inventory",  "type": "textarea", "placeholder": "e.g. 50x T-shirts (L), 20x hoodies (M)"},
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
                "message": f"MERCH LLM error: {str(e)}",
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
        expected_attendance = context.get("expected_attendance", "[unknown]")
        show_dates = ", ".join(context.get("show_dates", [])) if isinstance(context.get("show_dates"), list) else str(context.get("show_dates", ""))
        price_points = context.get("price_points", "[unknown]")
        inventory = context.get("existing_inventory", "[none]")

        return (
            f"You are a professional music tour merchandising manager. Plan for merchandise needs for the following context:\n"
            f"Artist: {artist}\n"
            f"Expected attendance per show: {expected_attendance}\n"
            f"Show dates: {show_dates}\n"
            f"Price points: {price_points}\n"
            f"Existing inventory: {inventory}\n"
            "Output strictly valid JSON in this schema:\n"
            "{\n"
            "  \"order_quantities\": [\n"
            "    {\"item\": string, \"quantity\": number, \"size\": string, \"price_point\": number}\n"
            "  ],\n"
            "  \"settlement_estimate\": {\n"
            "    \"expected_gross\": number, \"expected_net\": number, \"notes\": string\n"
            "  },\n"
            "  \"inventory_warnings\": [string], // e.g. 'low on L T-shirts', 'check hoodies'\n"
            "  \"strategy_notes\": string // human readable summary\n"
            "}\n"
            "Arrays may be empty if not enough data, but never omit any field. No markdown, no explanations outside JSON."
        )