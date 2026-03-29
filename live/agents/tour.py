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
        prompt = self.build_prompt(context)
        try:
            llm_result = self.llm(prompt)
            structured = self.parse_json(llm_result)
        except Exception as e:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "message": f"TOUR LLM error: {str(e)}",
                "sub_agents": self.SUB_AGENTS,
                "context": context,
            }
        return {
            "agent": self.name,
            "department": self.department,
            "status": "complete",
            "message": llm_result,
            "sub_agents": self.SUB_AGENTS,
            "data": structured,
            "context": context,
        }

    def build_prompt(self, context: dict) -> str:
        artist = context.get("artist", "[artist]")
        territory = context.get("territory", "[territory]")
        start_date = context.get("start_date", "[start]")
        end_date = context.get("end_date", "[end]")
        show_count = context.get("show_count", "[targets]")
        notes = context.get("notes", "")

        return (
            f"You are a senior tour manager. Synthesize a master plan for a music tour.\n"
            f"Artist: {artist}\n"
            f"Territory: {territory}\n"
            f"Start date: {start_date}\n"
            f"End date: {end_date}\n"
            f"Target shows: {show_count}\n"
            f"Notes/constraints/priorities: {notes}\n"
            "\n"
            "Output ONLY valid JSON in this format:\n"
            "{\n"
            "  \"summary\": string,         // concise 2-sentence overview\n"
            "  \"recommended_agents\": [string], // names of sub-agents to activate (see below)\n"
            "  \"agent_tasks\": [\n"
            "    { \"agent\": string, \"task\": string } // task delegated to sub-agent (e.g. 'route': plan best cities, 'settle': estimate financials)\n"
            "  ],\n"
            "  \"milestones\": [string],    // key stages (e.g. booking, routing, settlement, etc.)\n"
            "  \"overall_notes\": string    // optional context, warnings, or priorities for the whole tour\n"
            "}\n"
            f"Recommended sub-agents: {', '.join(self.SUB_AGENTS)}.\n"
            "No markdown, no explanation, no extra fields—JSON only, all sections present."
        )