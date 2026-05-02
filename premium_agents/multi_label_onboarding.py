from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from core.base_agent import BaseAgent


class MultiLabelOnboardingAgent(BaseAgent):
    """Multi-label SaaS onboarding agent.

    Generates a structured onboarding checklist and welcome brief for a new
    label joining the Maestro AI platform. Optionally uses the LLM to
    personalise the checklist based on the label's genre and goals.
    """

    name = "MULTI_LABEL_ONBOARDING"
    department = "premium"
    description = "SaaS onboarding for new labels: checklist, setup guide, and welcome brief."

    FIELDS = [
        {"key": "label_name", "label": "Label Name", "type": "text", "placeholder": "e.g. Neon Horizon Records"},
        {"key": "label_slug", "label": "Label Slug", "type": "text", "placeholder": "e.g. neon_horizon"},
        {"key": "owner_name", "label": "Owner / CEO Name", "type": "text", "placeholder": "e.g. Jordan Lee"},
        {"key": "owner_email", "label": "Owner Email", "type": "text", "placeholder": "e.g. jordan@neonhorizon.com"},
        {
            "key": "genre_focus",
            "label": "Primary Genre Focus",
            "type": "text",
            "placeholder": "e.g. Indie Pop, Hip-Hop",
        },
        {
            "key": "artist_count",
            "label": "Number of Artists on Roster",
            "type": "text",
            "placeholder": "e.g. 5",
        },
        {
            "key": "use_llm",
            "label": "Personalise with AI (requires LLM)",
            "type": "select",
            "options": ["yes", "no"],
            "default": "no",
        },
    ]

    # Standard onboarding steps every new label must complete
    STANDARD_CHECKLIST = [
        {"step": 1, "category": "setup", "task": "Configure .env with MAESTRO_TOKEN and LLM_PROVIDER.", "status": "pending"},
        {"step": 2, "category": "setup", "task": "Add at least one artist profile to data/artists/.", "status": "pending"},
        {"step": 3, "category": "setup", "task": "Verify the dashboard loads at http://localhost:8080 (or your deployed URL).", "status": "pending"},
        {"step": 4, "category": "data", "task": "Import artist catalog (use artist_import_template.csv).", "status": "pending"},
        {"step": 5, "category": "data", "task": "Add upcoming shows to live/data/shows.json.", "status": "pending"},
        {"step": 6, "category": "data", "task": "Add studio sessions to studio/data/sessions.json.", "status": "pending"},
        {"step": 7, "category": "agents", "task": "Run the LEDGER agent and confirm financial summaries load.", "status": "pending"},
        {"step": 8, "category": "agents", "task": "Run the SAGE agent and review the first daily brief.", "status": "pending"},
        {"step": 9, "category": "agents", "task": "Run the FOCUS agent and action the first priority queue.", "status": "pending"},
        {"step": 10, "category": "integrations", "task": "Connect webhook endpoint (WEBHOOK_URL) if using n8n or Zapier.", "status": "pending"},
        {"step": 11, "category": "integrations", "task": "Add social/streaming API keys to .env as needed.", "status": "pending"},
        {"step": 12, "category": "review", "task": "Complete a test mission for one artist and approve via the CEO queue.", "status": "pending"},
    ]

    def run(self, context: dict) -> dict:
        label_name = context.get("label_name") or "New Label"
        label_slug = context.get("label_slug") or re.sub(r"\W+", "_", label_name.lower()).strip("_")
        owner_name = context.get("owner_name") or "Label Owner"
        owner_email = context.get("owner_email") or ""
        genre_focus = context.get("genre_focus") or "General"
        artist_count = context.get("artist_count") or "unknown"
        use_llm = str(context.get("use_llm", "no")).lower() == "yes"

        # Deep-copy the standard checklist so each run is independent
        checklist = [dict(item) for item in self.STANDARD_CHECKLIST]

        # Optional: personalise with LLM
        ai_welcome = None
        if use_llm:
            try:
                ai_welcome = self._generate_welcome(label_name, owner_name, genre_focus, artist_count)
            except Exception as e:
                ai_welcome = f"[AI personalisation unavailable: {e}]"

        result_data = {
            "label_name": label_name,
            "label_slug": label_slug,
            "owner_name": owner_name,
            "owner_email": owner_email,
            "genre_focus": genre_focus,
            "artist_count": artist_count,
            "onboarding_checklist": checklist,
            "checklist_total": len(checklist),
            "welcome_message": ai_welcome or self._default_welcome(label_name, owner_name),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        saved_path = self.save_output(result_data, slug=f"onboarding_{label_slug}")

        return {
            "agent": self.name,
            "department": self.department,
            "status": "complete",
            "message": (
                f"Onboarding package created for {label_name}. "
                f"{len(checklist)} setup steps generated."
            ),
            "data": result_data,
            "saved_to": saved_path,
            "context": context,
        }

    def _default_welcome(self, label_name: str, owner_name: str) -> str:
        return (
            f"Welcome to Maestro AI, {owner_name}! "
            f"{label_name} is now set up on the platform. "
            "Work through the onboarding checklist to get your first agents running. "
            "If you need help, see docs/quickstart.md."
        )

    def _generate_welcome(self, label_name: str, owner_name: str, genre: str, artist_count: str) -> str:
        prompt = (
            f"You are Maestro AI's onboarding assistant. Write a warm, professional, "
            f"one-paragraph welcome message (max 80 words) for a new label joining the platform.\n\n"
            f"Label: {label_name}\n"
            f"Owner: {owner_name}\n"
            f"Genre focus: {genre}\n"
            f"Roster size: {artist_count} artist(s)\n\n"
            "Do NOT use markdown. Return plain text only."
        )
        return self.llm(prompt).strip()

