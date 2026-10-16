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
        artist_info = artist_data.get("artist_info") or {}
        project = artist_data.get("current_project") or {}
        platforms = artist_data.get("platforms") or {}
        musical_identity = artist_data.get("musical_identity") or {}
        upcoming_release = artist_data.get("upcoming_release") or {}
        audience = artist_data.get("audience") or {}
        catalogue = artist_data.get("catalogue") or []

        if not isinstance(artist_info, dict):
            artist_info = {}
        if not isinstance(project, dict):
            project = {}
        if not isinstance(platforms, dict):
            platforms = {}
        if not isinstance(musical_identity, dict):
            musical_identity = {}
        if not isinstance(upcoming_release, dict):
            upcoming_release = {}
        if not isinstance(audience, dict):
            audience = {}
        if not isinstance(catalogue, list):
            catalogue = []

        members = artist_info.get("members") or []
        if not isinstance(members, list):
            members = []

        catalogue_tracks = [
            {
                "release": item.get("title") or item.get("name") or "[placeholder]",
                "tracks": item.get("tracks") or "[placeholder]",
            }
            for item in catalogue
            if isinstance(item, dict)
        ]

        return {
            "artist_name": artist_info.get("name", "Unknown Artist"),
            "genres": artist_info.get("genres", []),
            "members": members,
            "location": artist_info.get("location") or "[placeholder]",
            "voice_description": musical_identity.get("voice_description") or "[placeholder]",
            "influences": musical_identity.get("influences") or [],
            "catalogue_tracks": catalogue_tracks,
            "title_meaning": self._find_title_meaning(project, upcoming_release, catalogue),
            "listener_profile": audience.get("listener_profile") or "[placeholder]",
            "audience_timezone": (
                artist_data.get("audience_timezone")
                or audience.get("audience_timezone")
                or "Australia/Perth"
            ),
            "project_name": project.get("name", "Current Release"),
            "project_type": project.get("type", "Release"),
            "target_date": project.get("target_date", "TBD"),
            "instagram": platforms.get("instagram", "@little_rascal_records"),
            "facebook": platforms.get("facebook", "LRRecords"),
            "youtube": platforms.get("youtube", "LRRecords Studio"),
        }

    # ── Core method ──────────────────────────────────────────────

    @staticmethod
    def _find_title_meaning(project, upcoming_release, catalogue):
        """Return the artist-supplied meaning of the release title, or [placeholder].

        Checks upcoming_release first, then the catalogue entry whose title
        matches the current project or upcoming release.
        """
        meaning = upcoming_release.get("title_meaning")
        if meaning:
            return meaning
        wanted = {
            str(name).strip().lower()
            for name in (project.get("name"), upcoming_release.get("title"))
            if name
        }
        for item in catalogue:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("name") or "").strip().lower()
            if title in wanted and item.get("title_meaning"):
                return item["title_meaning"]
        return "[placeholder]"

    @staticmethod
    def _release_status(target_date, today):
        """Describe whether the release is upcoming or already out."""
        try:
            release = datetime.strptime(str(target_date), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return "Unknown release date - do not write countdown or 'out now' copy"
        if release <= today.date():
            return f"ALREADY RELEASED on {target_date} - write 'out now' copy, never countdown or pre-release copy"
        return f"UPCOMING on {target_date} - build anticipation toward the release date"

    def generate_content_plan(self, artist_data, days=14):
        """Generate a 2-week content plan for an artist"""

        info = self._extract_artist_info(artist_data)
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=days - 1)).strftime("%Y-%m-%d")
        members = ", ".join(
            f"{member.get('name') or '[placeholder]'} ({member.get('role') or '[placeholder]'})"
            if isinstance(member, dict)
            else str(member)
            for member in info["members"]
        ) or "[placeholder]"
        influences = ", ".join(info["influences"]) if info["influences"] else "[placeholder]"
        catalogue_tracks = (
            json.dumps(info["catalogue_tracks"], ensure_ascii=False)
            if info["catalogue_tracks"]
            else "[placeholder]"
        )

        release_status = self._release_status(info["target_date"], today)

        prompt = f"""You are ECHO, a creative content and marketing specialist at LRRecords, \
an independent label in Rockingham, Western Australia.

Build a 2-week content calendar to promote:

ARTIST        : {info['artist_name']}
PROJECT       : {info['project_name']} ({info['project_type']})
RELEASE DATE  : {info['target_date']}
GENRES        : {', '.join(info['genres']) if info['genres'] else 'Not specified'}
MEMBERS       : {members}
LOCATION      : {info['location']}
VOICE          : {info['voice_description']}
INFLUENCES    : {influences}
CATALOGUE TRACKS: {catalogue_tracks}
RELEASE STATUS: {release_status}
TITLE MEANING : {info['title_meaning']}
LISTENER PROFILE: {info['listener_profile']}
AUDIENCE TIMEZONE: {info['audience_timezone']}

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
          "best_time": "Best posting time in {info['audience_timezone']}"
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
- Give all posting times in {info['audience_timezone']}
- If TITLE MEANING is provided, describe the title only using that meaning; never add a dictionary definition
- If TITLE MEANING is [placeholder], do not define, translate or explain the title at all
- Follow RELEASE STATUS: an already-released or re-released project is promoted as out now
- Never invent facts, including runtime, gear, quotes, or fan comments; use [placeholder] for anything missing

Return ONLY valid JSON — no other text, no markdown fences."""

        plan = self._parse_json(call_llm(prompt, max_tokens=8000))

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
                lines.append(f"  Time    : {post.get('best_time', post.get('best_time_awst', ''))}")

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