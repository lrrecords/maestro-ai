# scripts/agents/vinyl.py
# VINYL - Music Operations Agent
# Detail-oriented, systematic, process-driven

import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from llm.client import call_llm

load_dotenv()


class VinylAgent:
    """
    VINYL — Music Operations Specialist
    Handles: release coordination, checklists, timelines, distro management
    """

    NAME = "VINYL"
    DESCRIPTION = "Music Operations Specialist"

    def __init__(self):
        self.output_dir = Path("data/vinyl")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Data extraction ──────────────────────────────────────────

    def _extract_project_info(self, artist_data):
        """Safely extract project info with sensible defaults"""
        artist_info = artist_data.get("artist_info", {})
        project = artist_data.get("current_project", {})

        return {
            "artist_name": artist_info.get("name", "Unknown Artist"),
            "genres": artist_info.get("genres", []),
            "project_name": project.get("name", "Current Release"),
            "project_type": project.get("type", "Release"),
            "target_date": project.get("target_date", "TBD"),
            "status": project.get("status", "Active"),
            "blockers": project.get("blockers", []),
            "distribution": artist_data.get("distribution", "The Orchard"),
        }

    # ── Core method ──────────────────────────────────────────────

    def generate_checklist(self, artist_data):
        """Generate a comprehensive release checklist for an artist's current project"""

        info = self._extract_project_info(artist_data)
        today = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""You are VINYL, a music operations specialist at LRRecords, \
an independent label in Rockingham, Western Australia.

Generate a comprehensive release checklist for:

ARTIST        : {info['artist_name']}
PROJECT       : {info['project_name']}
TYPE          : {info['project_type']}
RELEASE DATE  : {info['target_date']}
GENRES        : {', '.join(info['genres']) if info['genres'] else 'Not specified'}
DISTRIBUTION  : {info['distribution']}
STATUS        : {info['status']}
BLOCKERS      : {', '.join(info['blockers']) if info['blockers'] else 'None'}
TODAY         : {today}

Return a JSON checklist using EXACTLY this structure:

{{
  "artist": "{info['artist_name']}",
  "project": "{info['project_name']}",
  "project_type": "{info['project_type']}",
  "release_date": "{info['target_date']}",
  "generated": "{today}",
  "phases": [
    {{
      "phase": "Phase name",
      "timeline": "Timing relative to release date (e.g. 8 weeks before, Release Day)",
      "tasks": [
        {{
          "task": "Specific actionable task",
          "priority": "HIGH or MEDIUM or LOW",
          "status": "PENDING or IN_PROGRESS or COMPLETE or BLOCKED",
          "notes": "Context, blockers, or specific details"
        }}
      ]
    }}
  ],
  "critical_path": [
    "The single most important dependency or task"
  ],
  "immediate_actions": [
    "Something that must happen THIS week"
  ],
  "blockers": [
    "Any current blocking issue"
  ]
}}

Include 4-6 phases covering: Pre-Production, Distribution & Metadata, \
Marketing & Promo, Release Day, Post-Release.
Be specific to this release type and genres. Flag known blockers immediately.
Return ONLY valid JSON — no other text, no markdown fences."""

        checklist = self._parse_json(call_llm(prompt, max_tokens=2500))

        # Save
        slug = info["artist_name"].lower().replace(" ", "_")
        output_path = self.output_dir / f"{slug}_checklist.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(checklist, f, indent=2, ensure_ascii=False)

        return checklist, str(output_path)

    # ── Display ──────────────────────────────────────────────────

    def format_display(self, checklist):
        """Format checklist for terminal display"""
        P = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        S = {"COMPLETE": "✅", "IN_PROGRESS": "🔄", "BLOCKED": "🚫", "PENDING": "⏳"}

        lines = [
            "",
            "=" * 62,
            "🎵  VINYL — RELEASE CHECKLIST",
            "=" * 62,
            f"  Artist  : {checklist.get('artist')}",
            f"  Project : {checklist.get('project')} ({checklist.get('project_type')})",
            f"  Release : {checklist.get('release_date')}",
            f"  Built   : {checklist.get('generated')}",
        ]

        if checklist.get("blockers"):
            lines.append("\n🚫  BLOCKERS — RESOLVE FIRST:")
            for b in checklist["blockers"]:
                lines.append(f"  ⚠️   {b}")

        if checklist.get("immediate_actions"):
            lines.append("\n⚡  IMMEDIATE ACTIONS (This Week):")
            for a in checklist["immediate_actions"]:
                lines.append(f"  →  {a}")

        if checklist.get("critical_path"):
            lines.append("\n🎯  CRITICAL PATH:")
            for c in checklist["critical_path"]:
                lines.append(f"  •  {c}")

        lines.append("\n📋  FULL CHECKLIST:")
        for phase in checklist.get("phases", []):
            lines.append(f"\n  ── {phase.get('phase','').upper()}  ({phase.get('timeline','')})")
            lines.append("  " + "─" * 52)
            for task in phase.get("tasks", []):
                p_e = P.get(task.get("priority", "MEDIUM"), "⚪")
                s_e = S.get(task.get("status", "PENDING"), "⏳")
                lines.append(f"  {s_e} {p_e}  {task.get('task', '')}")
                note = task.get("notes", "")
                if note and note.lower() not in ("none", "n/a", ""):
                    lines.append(f"        └─ {note}")

        lines.append("\n" + "=" * 62)
        return "\n".join(lines)

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_json(text):
        """Robustly parse JSON from Claude's response"""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())