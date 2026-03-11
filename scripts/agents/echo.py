# scripts/agents/echo.py
# ECHO - Content & Marketing Agent
# Creative, brand-conscious, engaging

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

from llm.client import call_llm

load_dotenv()


class EchoAgent:
    """
    ECHO — Content & Marketing Specialist
    Handles: content calendars, social media copy, campaign planning
    """

    NAME = "ECHO"
    DESCRIPTION = "Content & Marketing Specialist"

    def __init__(self):
        self.output_dir = Path("data/echo")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Data extraction ──────────────────────────────────────────

    def _extract_artist_info(self, artist_data):
        """Safely extract all relevant info for content planning"""
        artist_info = artist_data.get("artist_info", {})
        project = artist_data.get("current_project", {})
        platforms = artist_data.get("platforms", {})

        return {
            "artist_name": artist_info.get("name", "Unknown Artist"),
            "genres": artist_info.get("genres", []),
            "project_name": project.get("name", "Current Release"),
            "project_type": project.get("type", "Release"),
            "target_date": project.get("target_date", "TBD"),
            "instagram": platforms.get("instagram", "@little_rascal_records"),
            "facebook": platforms.get("facebook", "LRRecords"),
            "youtube": platforms.get("youtube", "LRRecords Studio"),
        }

    # ── Core method ──────────────────────────────────────────────

    def generate_content_plan(self, artist_data, days=14):
        """Generate a 2-week content plan for an artist"""

        info = self._extract_artist_info(artist_data)
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=days - 1)).strftime("%Y-%m-%d")

        prompt = f"""You are ECHO, a creative content and marketing specialist at LRRecords, \
an independent label in Rockingham, Western Australia.

Build a 2-week content calendar to promote:

ARTIST        : {info['artist_name']}
PROJECT       : {info['project_name']} ({info['project_type']})
RELEASE DATE  : {info['target_date']}
GENRES        : {', '.join(info['genres']) if info['genres'] else 'Not specified'}

PLATFORMS:
  Instagram   : {info['instagram']}
  Facebook    : {info['facebook']}
  YouTube     : {info['youtube']}

PERIOD        : {start_date} to {end_date}

Return a JSON content calendar using EXACTLY this structure:

{{
  "artist": "{info['artist_name']}",
  "project": "{info['project_name']}",
  "period": "{start_date} to {end_date}",
  "generated": "{today.strftime('%Y-%m-%d')}",
  "strategy_summary": "2-3 sentence overview of content strategy for this period",
  "posting_cadence": "Recommended posting frequency",
  "content_pillars": ["Pillar 1", "Pillar 2", "Pillar 3"],
  "content_plan": [
    {{
      "date": "YYYY-MM-DD",
      "day_theme": "Theme for this day",
      "posts": [
        {{
          "platform": "Instagram or Facebook or YouTube",
          "content_type": "Teaser / BTS / Announcement / Reel / Story / etc.",
          "caption": "Full ready-to-post caption. Authentic, not corporate.",
          "hashtags": ["tag1", "tag2", "tag3"],
          "call_to_action": "What you want the audience to do",
          "visual_direction": "Specific description of what to film or photograph",
          "best_time_awst": "Best posting time in AWST"
        }}
      ]
    }}
  ],
  "key_dates": [
    {{
      "date": "YYYY-MM-DD",
      "event": "What happens on this date",
      "content_note": "What content to push on this day"
    }}
  ],
  "content_notes": "Additional creative notes or recommendations"
}}

GUIDELINES:
- Quality over quantity — 3 to 4 posts per week, not every single day
- Only include dates that have actual posts — skip empty days entirely
- Captions should feel authentic to an independent label, not like a press release
- Mix content types across the 2 weeks
- Hashtags relevant to: {', '.join(info['genres']) if info['genres'] else 'electronic music'}
- All times in AWST (Australian Western Standard Time)

Return ONLY valid JSON — no other text, no markdown fences."""

        plan = self._parse_json(call_llm(prompt, max_tokens=3500))

        # Save
        slug = info["artist_name"].lower().replace(" ", "_")
        output_path = self.output_dir / f"{slug}_content_plan.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        return plan, str(output_path)

    # ── Display ──────────────────────────────────────────────────

    def format_display(self, plan):
        """Format content plan for terminal display"""
        platform_emoji = {"Instagram": "📸", "Facebook": "👥", "YouTube": "🎥"}

        lines = [
            "",
            "=" * 62,
            "📣  ECHO — CONTENT PLAN",
            "=" * 62,
            f"  Artist  : {plan.get('artist')}",
            f"  Project : {plan.get('project')}",
            f"  Period  : {plan.get('period')}",
            f"  Built   : {plan.get('generated')}",
        ]

        if plan.get("strategy_summary"):
            lines.append("\n💡  STRATEGY:")
            lines.append(f"  {plan['strategy_summary']}")

        if plan.get("content_pillars"):
            lines.append("\n🏛️   CONTENT PILLARS:")
            for p in plan["content_pillars"]:
                lines.append(f"  •  {p}")

        if plan.get("posting_cadence"):
            lines.append(f"\n📅  CADENCE: {plan['posting_cadence']}")

        if plan.get("key_dates"):
            lines.append("\n⭐  KEY DATES:")
            for kd in plan["key_dates"]:
                lines.append(f"  📌  {kd.get('date')} — {kd.get('event')}")
                lines.append(f"      → {kd.get('content_note')}")

        lines.append("\n📅  CONTENT CALENDAR:")
        lines.append("─" * 62)

        active_days = [d for d in plan.get("content_plan", []) if d.get("posts")]

        for day in active_days:
            lines.append(f"\n🗓️   {day['date']}  —  {day.get('day_theme', '')}")
            for post in day.get("posts", []):
                platform = post.get("platform", "")
                emoji = platform_emoji.get(platform, "📱")
                lines.append(f"\n  {emoji}  {platform} | {post.get('content_type', '')}")

                caption = post.get("caption", "")
                display_caption = caption[:120] + "..." if len(caption) > 120 else caption
                lines.append(f"  Caption : {display_caption}")

                tags = post.get("hashtags", [])
                if tags:
                    tag_str = " ".join("#" + t.lstrip("#") for t in tags[:5])
                    lines.append(f"  Tags    : {tag_str}")

                lines.append(f"  CTA     : {post.get('call_to_action', '')}")
                lines.append(f"  Visual  : {post.get('visual_direction', '')}")
                lines.append(f"  Time    : {post.get('best_time_awst', '')}")

        if plan.get("content_notes"):
            lines.append(f"\n📝  NOTES: {plan['content_notes']}")

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