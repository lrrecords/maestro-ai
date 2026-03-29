from core.base_agent import BaseAgent

class RiderAgent(BaseAgent):
    department = "live"
    name = "RIDER"
    description = "Technical, hospitality, guest list, security, and logistics rider management."

    FIELDS = [
        {"key": "artist",                   "label": "Artist",              "type": "text",     "placeholder": "e.g. Bicep",           "required": True},
        {"key": "show_dates",               "label": "Show Dates",          "type": "tags",     "placeholder": "e.g. 2026-04-02"},
        {"key": "stage_plot",               "label": "Stage Plot Notes",    "type": "textarea", "placeholder": "e.g. 2x CDJs, 1x DJM mixer, monitors L/R"},
        {"key": "hospitality_requirements", "label": "Hospitality Notes",   "type": "textarea", "placeholder": "e.g. Vegan catering, 2 private dressing rooms"},
        {"key": "guest_list",               "label": "Guest List",          "type": "textarea", "placeholder": "Per show: city and names, e.g. Perth: Jason M, Randy L"},
        {"key": "security_notes",           "label": "Security Notes",      "type": "textarea", "placeholder": "e.g. Afterparty protocols, artist anonymity"},
        {"key": "logistics_notes",          "label": "Logistics Notes",     "type": "textarea", "placeholder": "e.g. Parking for van, load-in time, hotel"},
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
                "message": f"RIDER LLM error: {str(e)}",
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
        show_dates = ", ".join(context.get("show_dates", [])) if isinstance(context.get("show_dates"), list) else str(context.get("show_dates", ""))
        stage_plot = context.get("stage_plot", "No stage plot info provided")
        hospitality = context.get("hospitality_requirements", "No hospitality info provided")
        guest_list = context.get("guest_list", "No guests specified")
        security = context.get("security_notes", "No security requirements provided")
        logistics = context.get("logistics_notes", "No logistics info provided")

        # LLM prompt with maximal field/sample safety
        return (
            f"You are an expert live music and touring event manager. "
            f"Build a complete, strictly valid JSON rider for the following:\n"
            f"- Artist: {artist}\n"
            f"- Show Dates: {show_dates}\n"
            f"- Stage Plot Notes: {stage_plot}\n"
            f"- Hospitality Requirements: {hospitality}\n"
            f"- Guest List (by city/show): {guest_list}\n"
            f"- Security Notes: {security}\n"
            f"- Logistics Notes: {logistics}\n"
            "\n"
            "SCHEMA: Respond ONLY with JSON, matching this structure. For any field with no info, use an empty array or empty string, but never omit fields:\n"
            "{\n"
            "  \"technical_rider\": [\n"
            "    {\"date\": \"YYYY-MM-DD\", \"equipment\": [string], \"backline_notes\": string}\n"
            "  ],\n"
            "  \"hospitality_rider\": [\n"
            "    {\"date\": \"YYYY-MM-DD\", \"requirements\": [string], \"special_notes\": string}\n"
            "  ],\n"
            "  \"guest_list\": [\n"
            "    {\"date\": \"YYYY-MM-DD\", \"city\": string, \"names\": [string], \"notes\": string}\n"
            "  ],\n"
            "  \"security\": [\n"
            "    {\"date\": \"YYYY-MM-DD\", \"measures\": [string], \"notes\": string}\n"
            "  ],\n"
            "  \"logistics\": [\n"
            "    {\"date\": \"YYYY-MM-DD\", \"arrangements\": [string], \"notes\": string}\n"
            "  ],\n"
            "  \"overall_notes\": string\n"
            "}\n"
            "JSON ONLY. No code fences, no explanations, no markdown. "
            "All list fields must always be arrays, even for a single item. "
            "In guest_list, split city into a separate field, not inside names. Fill all dates present in show_dates; if a section has no details for a date, still list the date with empty arrays/strings."
        )