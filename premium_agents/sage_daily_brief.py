from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from core.base_agent import BaseAgent

class SageAgent(BaseAgent):
    name = "SAGE"
    department = "label"
    description = "Daily intelligence brief and executive summary."

    FIELDS = [
        {"key": "scope", "label": "Brief Scope", "type": "select", "options": ["daily", "weekly", "artist_specific"], "default": "daily"},
        {"key": "artist_slug", "label": "Artist Slug", "type": "text", "placeholder": "e.g. aria_velvet (optional)"},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_dir = Path(__file__).parent.parent
        self.data_dir = self.root_dir / "data"
        self.live_data = self.root_dir / "live" / "data"
        self.studio_data = self.root_dir / "studio" / "data"

    def run(self, context: dict) -> dict:
        scope = context.get("scope", "daily")
        artist_slug = context.get("artist_slug")

        # 1. Gather Inputs
        inputs = self._gather_inputs(artist_slug)

        # 2. Build Prompt
        prompt = self._build_brief_prompt(inputs, scope)

        # 3. Call LLM
        try:
            llm_response = self.llm(prompt)
            brief_data = self.parse_json(llm_response)
        except Exception as e:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "message": f"SAGE LLM error: {str(e)}",
                "context": context
            }

        # 4. Save Output
        saved_path = self.save_output(brief_data, slug=f"{scope}_brief")

        return {
            "agent": self.name,
            "department": self.department,
            "status": "complete",
            "message": f"SAGE {scope} brief generated.",
            "data": brief_data,
            "saved_to": saved_path,
            "context": context
        }

    def _gather_inputs(self, artist_slug: str | None) -> dict:
        inputs = {
            "artists": [],
            "upcoming_shows": [],
            "recent_sessions": [],
            "flags": []
        }

        # Load Artists
        artist_files = list((self.data_dir / "artists").glob("*.json"))
        for f in artist_files:
            data = self._load_json(f)
            if data:
                if not artist_slug or data.get("artist_info", {}).get("slug") == artist_slug:
                    inputs["artists"].append({
                        "name": data.get("artist_info", {}).get("name"),
                        "slug": data.get("artist_info", {}).get("slug"),
                        "status": data.get("artist_info", {}).get("status"),
                        "upcoming_release": data.get("upcoming_release", {}).get("title")
                    })

        # Load Shows
        shows = self._load_json(self.live_data / "shows.json", [])
        for s in shows:
            if not artist_slug or s.get("artist") == artist_slug:
                inputs["upcoming_shows"].append(s)

        # Load Sessions
        sessions = self._load_json(self.studio_data / "sessions.json", [])
        for s in sessions:
            if not artist_slug or s.get("artist") == artist_slug:
                inputs["recent_sessions"].append(s)

        return inputs

    def _load_json(self, path: Path, default: any = None) -> any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _build_brief_prompt(self, inputs: dict, scope: str) -> str:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"""You are SAGE, the intelligence layer for Maestro AI.
Today is {today}. Generate a concise {scope} executive brief for the label CEO.

Input Data:
{json.dumps(inputs, indent=2)}

Output format — respond ONLY with valid JSON, no markdown, no preamble:
{{
  "date": "{today}",
  "headline": "One sentence summary of today's priority",
  "priority_actions": [
    {{ "rank": 1, "action": "...", "context": "...", "urgency": "high|medium|low" }},
    {{ "rank": 2, "action": "...", "context": "...", "urgency": "high|medium|low" }},
    {{ "rank": 3, "action": "...", "context": "...", "urgency": "high|medium|low" }}
  ],
  "flags": ["..."],
  "upcoming_in_7_days": ["..."],
  "one_win": "Something positive from the last 24 hours"
}}

Rules:
- Maximum 3 priority actions.
- Be specific — name the artist, mission, or task.
- Never invent data not present in the input.
- If input is empty or sparse, say so in headline and return minimal JSON.
"""
