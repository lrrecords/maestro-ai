from pathlib import Path
from datetime import datetime, timezone
import json
import os
import requests
from core.base_agent import BaseAgent

class SignalAgent(BaseAgent):
    name = "SIGNAL"
    department = "studio"
    description = "Studio marketing, social content, and brand positioning."

    FIELDS = [
        {"key": "track_or_project", "label": "Track / Project",  "type": "text",     "placeholder": "e.g. Midnight Signal EP", "required": True},
        {"key": "key_message",      "label": "Key Message",      "type": "textarea", "placeholder": "What is the core story or hook?", "required": True},
        {"key": "target_audience",  "label": "Target Audience",  "type": "text",     "placeholder": "e.g. 18–34 indie fans, UK/US"},
        {"key": "channels",         "label": "Channels",         "type": "text",     "placeholder": "e.g. Instagram, TikTok, Spotify"},
        {"key": "genre",            "label": "Genre",            "type": "text",     "placeholder": "e.g. Drum and Bass, Indie"},
        {"key": "artist_story",     "label": "Artist/Project Story", "type": "textarea", "placeholder": "A brief narrative or artist bio (feeds LLM context)"},
        {"key": "release_date",     "label": "Release Date",     "type": "text",     "placeholder": "e.g. 2026-05-01"},
        {"key": "budget",           "label": "Marketing Budget", "type": "number",   "placeholder": "e.g. 500"},
        {"key": "notes",            "label": "Notes",            "type": "textarea", "placeholder": "Campaign history, prior posts, brand notes"},
    ]

    def run(self, context: dict) -> dict:
        ctx = context or {}

        # ----------- Validation -----------
        requireds = [
            ("track_or_project", ctx.get("track_or_project", "")),
            ("key_message", ctx.get("key_message", "")),
        ]
        missing = [k for k, v in requireds if not v]
        if missing:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "error": f"Missing required fields: {', '.join(missing)}",
                "context": context,
                "result": {
                    "action": "error",
                    "campaign": {},
                    "strategy": {},
                    "recommendations": [
                        "Provide the project name and a clear 'key message' for campaign planning.",
                        "Specify your target audience, main channels, and release date for stronger plans.",
                    ]
                }
            }

        # ----------- Audit/history logging -----------
        campaigns_file = self.data_root / "campaigns.json"
        campaigns = []
        if campaigns_file.exists():
            try:
                campaigns = json.loads(campaigns_file.read_text(encoding="utf-8"))
                if not isinstance(campaigns, list): campaigns = []
            except Exception:
                campaigns = []

        project = ctx.get("track_or_project", "").strip()
        previous_campaigns = [
            c for c in campaigns if c.get("track_or_project") == project
        ]

        campaign_record = {
            "track_or_project": project,
            "key_message":      ctx.get("key_message", "").strip(),
            "target_audience":  ctx.get("target_audience", "").strip(),
            "channels":         ctx.get("channels", "").strip(),
            "genre":            ctx.get("genre", "").strip(),
            "artist_story":     ctx.get("artist_story", "").strip(),
            "release_date":     ctx.get("release_date", "").strip(),
            "budget":           ctx.get("budget", ""),
            "notes":            ctx.get("notes", "").strip(),
            "created_at":       datetime.now(timezone.utc).isoformat(),
        }
        campaigns.append(campaign_record)
        campaigns_file.write_text(json.dumps(campaigns, indent=2, ensure_ascii=False), encoding="utf-8")

        # ----------- LLM/campaign strategy -----------
        strategy = self._generate_strategy(campaign_record, previous_campaigns)

        return {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "context": context,
            "result": {
                "action": "planned",
                "campaign": campaign_record,
                "strategy": strategy,
                "recommendations": strategy.get("recommendations", []) or [
                    "Create a campaign timeline, working back from the release date.",
                    "Define the key marketing channels and tone for messaging.",
                    "Assign owners for each campaign action early.",
                ],
                "audit_trail": [
                    {k: v for k,v in pc.items() if k not in ("notes", "created_at")} for pc in previous_campaigns[-5:]
                ],  # UI can expand/collapse these for review!
                "saved_to": str(campaigns_file),
            }
        }

    def _generate_strategy(self, record: dict, previous_campaigns: list) -> dict:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback_strategy(record, previous_campaigns)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx  = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout  = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        prompt = self._build_prompt(record, previous_campaigns)

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
            return self._parse_strategy(text, record, previous_campaigns)
        except Exception as exc:
            fallback = self._fallback_strategy(record, previous_campaigns)
            fallback["llm_error"] = str(exc)
            return fallback

    def _build_prompt(self, record: dict, previous_campaigns: list) -> str:
        prev = "\n\n-- Previous campaigns for this project --\n" + "\n".join(
            f"- {c.get('release_date','?')}: {c.get('key_message', '')[:80]}..." for c in previous_campaigns[-3:]
        ) if previous_campaigns else ""
        return f"""
You are a music marketing strategist for a professional studio.

Generate a concise campaign plan for the following:

- Project: {record.get("track_or_project", "")}
- Key message: {record.get("key_message", "")}
- Target audience: {record.get("target_audience", "")}
- Channels: {record.get("channels", "")}
- Genre: {record.get("genre", "")}
- Artist story: {record.get("artist_story", "")}
- Release date: {record.get("release_date", "")}
- Budget: {record.get("budget", "")}
- Internal notes: {record.get("notes", "")}
{prev}

Structure your response as follows (plain text, no markdown headings):

OVERVIEW
A one paragraph summary of the campaign approach.

CONTENT
3-4 bullets about the kinds of content to create and emphasize.

CHANNELS
Up to 3 marketing channels to focus on.

ACTIONS
3 immediate next actions for the team.

RECOMMENDATIONS
3-4 bullet-point practical suggestions for maximizing campaign impact.

Return only these sections in this exact order. Be specific and reference genre, prior outcomes or lessons if possible.
""".strip()

    def _parse_strategy(self, text: str, record: dict, previous_campaigns: list) -> dict:
        sections = {
            "overview": [],
            "content": [],
            "channels": [],
            "actions": [],
            "recommendations": [],
        }
        current = None
        key_map = {
            "OVERVIEW": "overview",
            "CONTENT": "content",
            "CHANNELS": "channels",
            "ACTIONS": "actions",
            "RECOMMENDATIONS": "recommendations",
        }
        for line in text.splitlines():
            stripped = line.strip()
            upper = stripped.upper()
            matched = next((v for k, v in key_map.items() if upper.startswith(k)), None)
            if matched:
                current = matched
                continue
            if current and stripped:
                sections[current].append(stripped.lstrip("•-–1234567890. \t"))
        return {
            "overview":        " ".join(sections["overview"]) or self._fallback_strategy(record, previous_campaigns)["overview"],
            "content":         sections["content"] or self._fallback_strategy(record, previous_campaigns)["content"],
            "channels":        sections["channels"] or self._fallback_strategy(record, previous_campaigns)["channels"],
            "actions":         sections["actions"] or self._fallback_strategy(record, previous_campaigns)["actions"],
            "recommendations": sections["recommendations"] or self._fallback_strategy(record, previous_campaigns)["recommendations"],
        }

    def _fallback_strategy(self, record: dict, previous_campaigns: list) -> dict:
        lessons = []
        if previous_campaigns:
            lessons.append("Review previous campaign engagement to see which content and channels performed best.")
        artist_story = (record.get("artist_story") or "").strip()
        if artist_story:
            lessons.append(f"Leverage artist story: {artist_story[:90]}...")
        genre = (record.get("genre") or "").strip().lower()
        if genre:
            lessons.append(f"Tap into {genre}-specific blogs, playlists, and communities.")
        lessons.append("Time paid promotions for a 48hr lift right after release.")
        return {
            "overview": (
                f"Run an integrated campaign focused on telling the story of '{record.get('track_or_project','[project]')}' using the '{record.get('key_message','')}' message. Prioritize owned and paid channels just before and after release."
            ),
            "content": [
                "Short video teasers, behind-the-scenes clips, and artwork reveals.",
                "Interviews or testimonials from key figures in the target scene.",
                "Countdown and feature posts targeting the chosen audience.",
            ],
            "channels": [
                record.get("channels") or "Instagram & TikTok for social; email list for core audience.",
            ],
            "actions": [
                "Draft campaign timeline with key milestone dates.",
                "Assign ownership for content, posting, and paid media.",
                "Prep all content assets at least two weeks in advance.",
            ],
            "recommendations": lessons[:4]
        }