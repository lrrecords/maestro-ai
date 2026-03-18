from __future__ import annotations

import json
import os
import requests
from datetime import datetime, timezone
from core.base_agent import BaseAgent


class SignalAgent(BaseAgent):
    name = "SIGNAL"
    department = "studio"
    description = "Studio marketing, social content, and brand positioning."

    FIELDS = [
        {"key": "track_or_project", "label": "Track / Project",  "type": "text",     "required": True,  "placeholder": "e.g. Midnight Signal EP"},
        {"key": "key_message",      "label": "Key Message",      "type": "textarea", "required": True,  "placeholder": "What is the core story or hook to communicate?"},
        {"key": "target_audience",  "label": "Target Audience",  "type": "text",     "required": False, "placeholder": "e.g. 18–34 indie fans, UK/US"},
        {"key": "channels",         "label": "Channels",         "type": "text",     "required": False, "placeholder": "e.g. Instagram, TikTok, Spotify"},
        {"key": "tone",             "label": "Tone",             "type": "select",   "required": False,
         "options": ["professional", "casual", "hype", "intimate", "editorial"]},
        {"key": "release_date",     "label": "Release Date",     "type": "text",     "required": False, "placeholder": "e.g. 2026-05-01"},
        {"key": "budget",           "label": "Marketing Budget", "type": "number",   "required": False, "placeholder": "e.g. 500"},
        {"key": "notes",            "label": "Notes",            "type": "textarea", "required": False, "placeholder": "Campaign history, prior posts, brand notes"},
    ]

    def run(self, context: dict) -> dict:
        track_or_project = context.get("track_or_project", "").strip()
        key_message      = context.get("key_message",      "").strip()
        target_audience  = context.get("target_audience",  "").strip()
        channels         = context.get("channels",         "").strip()
        tone             = context.get("tone",             "professional").strip()
        release_date     = context.get("release_date",     "").strip()
        budget           = context.get("budget",           "")
        notes            = context.get("notes",            "").strip()

        missing = [f for f, v in [
            ("track_or_project", track_or_project),
            ("key_message",      key_message),
        ] if not v]

        if missing:
            return {
                "agent":      self.name,
                "department": self.department,
                "status":     "error",
                "error":      f"Missing required fields: {', '.join(missing)}",
                "context":    context,
                "recommendations": [
                    "Provide the track or project name and a core key message to generate a campaign plan.",
                    "Add target audience and channels for more focused recommendations.",
                    "Include the release date so SIGNAL can work backwards on campaign timing.",
                ],
            }

        campaigns_file = self.data_root / "campaigns.json"
        campaigns = []
        if campaigns_file.exists():
            try:
                campaigns = json.loads(campaigns_file.read_text(encoding="utf-8"))
                if not isinstance(campaigns, list):
                    campaigns = []
            except Exception:
                campaigns = []

        now_iso = datetime.now(timezone.utc).isoformat()
        campaign_record = {
            "track_or_project": track_or_project,
            "key_message":      key_message,
            "target_audience":  target_audience,
            "channels":         channels,
            "tone":             tone,
            "release_date":     release_date,
            "budget":           budget,
            "notes":            notes,
        }

        existing = next(
            (c for c in campaigns if c.get("track_or_project") == track_or_project),
            None,
        )

        if existing:
            existing.update(campaign_record)
            existing["updated_at"] = now_iso
            action = "updated"
            saved_record = existing
        else:
            campaign_record["created_at"] = now_iso
            campaigns.append(campaign_record)
            action = "created"
            saved_record = campaign_record

        campaigns_file.write_text(
            json.dumps(campaigns, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        recommendations = self._generate_recommendations(saved_record)

        return {
            "agent":      self.name,
            "department": self.department,
            "status":     "ok",
            "context":    context,
            "result": {
                "action":   action,
                "campaign": {
                    "project":   track_or_project,
                    "message":   key_message,
                    "audience":  target_audience or "—",
                    "channels":  channels or "—",
                    "tone":      tone,
                    "release":   release_date or "—",
                    "budget":    budget or "—",
                    "notes":     notes or "—",
                },
                "recommendations": recommendations,
            },
        }

    def _generate_recommendations(self, record: dict) -> list[str]:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback(record)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx  = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout  = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        prompt = f"""
You are a music marketing strategist specialising in independent artists and recording studios.

Generate a practical marketing campaign plan for the following project.

Campaign details:
- Project: {record.get("track_or_project", "")}
- Key message: {record.get("key_message", "")}
- Target audience: {record.get("target_audience", "")}
- Channels: {record.get("channels", "")}
- Tone: {record.get("tone", "")}
- Release date: {record.get("release_date", "")}
- Budget: {record.get("budget", "")}
- Notes: {record.get("notes", "")}

Return:
- A short intro sentence summarising the campaign opportunity
- 5 bullet recommendations covering content, timing, channels, and messaging
- 3 suggested next actions

Be concise and actionable. Do not use markdown headings.
""".strip()

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model":   model,
                    "prompt":  prompt,
                    "stream":  False,
                    "options": {"num_ctx": num_ctx, "temperature": 0.7},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            text = (resp.json().get("response") or "").strip()
            lines = [l.strip("•- \t") for l in text.splitlines() if l.strip()]
            return lines[:9] or self._fallback(record)
        except Exception as exc:
            return self._fallback(record) + [f"LLM unavailable; using fallback. ({exc})"]

    def _fallback(self, record: dict) -> list[str]:
        tone     = (record.get("tone") or "professional").lower()
        channels = (record.get("channels") or "").lower()
        budget   = str(record.get("budget") or "").strip()
        recs = [
            "Define a clear release timeline — work backwards from the drop date with weekly milestones.",
            "Create a content bank of at least 10 assets (clips, stills, quotes) before the campaign begins.",
            "Pin the key message to every piece of content so the narrative stays consistent across channels.",
        ]
        if "tiktok" in channels:
            recs.append("Prioritise short-form video on TikTok — 15–30s clips with the hook in the first 2 seconds.")
        if "instagram" in channels:
            recs.append("Use Instagram Reels for reach and Stories for behind-the-scenes engagement.")
        if "spotify" in channels:
            recs.append("Submit to Spotify editorial playlists via Spotify for Artists at least 7 days before release.")
        if tone == "intimate":
            recs.append("Lead with personal storytelling — share the 'why' behind the project on long-form posts.")
        elif tone == "hype":
            recs.append("Build anticipation with countdowns, teaser clips, and exclusive previews for followers.")
        if budget:
            recs.append(f"Allocate the {budget} budget — prioritise paid social in the first 48 hours post-release for maximum algorithmic lift.")
        recs.append("Track engagement daily in the first week and adjust channel focus based on what is performing.")
        return recs[:7]