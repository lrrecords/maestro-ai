#!/usr/bin/env python3
"""
BRIDGE — Artist Relations Intelligence Agent
MAESTRO AI · LR Records

Python-side calculations (no API needed):
  - Health scoring 0-100 (contact recency, frequency, momentum)
  - Pattern detection (improving / stable / declining)

LLM handles:
  - Relationship interpretation
  - Predictions and opportunity identification
  - Draft check-in message in the label owner's voice
  - Risk assessment and action items

Output saved to data/bridge/ as JSON.
"""

import json
import os
from math import floor
from pathlib import Path
from datetime import datetime, timezone, timedelta

from llm.client import call_llm, get_provider
from dotenv import load_dotenv

load_dotenv()


def post_health_webhook(artist_name: str, health: dict, patterns: dict, result: dict | None):
    """POST health score data to n8n webhook. Fails silently if not configured."""
    webhook_url = os.getenv("N8N_WEBHOOK_URL")
    if not webhook_url:
        return

    try:
        import requests as _req

        # Pull top action item from LLM result if available
        actions    = (result or {}).get("action_items", [])
        top_action = actions[0].get("action", "Review artist profile") if actions else "Review artist profile"

        check_in = (result or {}).get("check_in_message", {})

        payload = {
            "artist":             artist_name,
            "score":              health["score"],
            "status":             health["status"],
            "days_since_contact": health.get("days_since_contact"),
            "trend":              patterns.get("trend", "unknown"),
            "anomalies":          patterns.get("anomalies", []),
            "top_action":         top_action,
            "check_in_channel":   check_in.get("channel", ""),
            "check_in_message":   check_in.get("message", ""),
            "timestamp":          datetime.now(timezone.utc).isoformat(),
        }

        response = _req.post(webhook_url, json=payload, timeout=5)
        print(f"  Webhook -> n8n  [{response.status_code}]")

    except Exception as e:
        print(f"  Webhook skipped: {e}")




# ── Paths ──────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Allow private/local data dir override (keeps public repo demo-safe)
DATA_DIR = Path(os.getenv("MAESTRO_DATA_DIR", str(BASE_DIR / "data")))
if not DATA_DIR.is_absolute():
    DATA_DIR = (BASE_DIR / DATA_DIR).resolve()

BRIDGE_DIR = DATA_DIR / "bridge"
ATLAS_DIR  = DATA_DIR / "atlas"
SAGE_DIR   = DATA_DIR / "sage"


# ── Helpers ────────────────────────────────────────────────────────────────────

def find_latest_output(folder: Path, artist_slug: str) -> tuple[dict | None, str | None]:
    if not folder.exists():
        return None, None
    matches = sorted(
        folder.glob(f"{artist_slug}*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        return None, None
    with open(matches[0], encoding="utf-8") as f:
        return json.load(f), matches[0].name


def parse_date(date_str) -> datetime | None:
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        # If date has no timezone info, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


# ── Health Scorer ──────────────────────────────────────────────────────────────

def calculate_health(profile: dict) -> dict:
    """
    Score 0-100:
      Recency   40 pts — how recently contact was made
      Frequency 30 pts — contacts in last 90 days
      Momentum  30 pts — active project + recent releases
    """
    score   = 0
    factors = []
    now     = datetime.now(timezone.utc)

    # Recency (40 pts)
    raw_date = (
        profile.get("last_contact_date")
        or profile.get("artist_info", {}).get("last_contact_date")
    )
    last_contact_dt = parse_date(raw_date)
    days_since      = None

    if last_contact_dt:
        days_since = (now - last_contact_dt).days
        if   days_since <= 7:   pts = 40
        elif days_since <= 14:  pts = 32
        elif days_since <= 30:  pts = 20
        elif days_since <= 60:  pts = 10
        else:                   pts = 0
        score += pts
        factors.append(f"Last contact {days_since}d ago (+{pts}/40)")
    else:
        factors.append("Last contact: no date recorded (+0/40)")

    # Frequency (30 pts)
    cutoff_90 = now - timedelta(days=90)
    history   = profile.get("communication_history", [])
    recent    = sum(
        1 for e in history
        if parse_date(e.get("date") or e.get("timestamp")) and
           parse_date(e.get("date") or e.get("timestamp")) >= cutoff_90
    )

    if   recent >= 6: pts = 30
    elif recent >= 4: pts = 22
    elif recent >= 2: pts = 14
    elif recent >= 1: pts = 7
    else:             pts = 0
    score += pts
    factors.append(f"{recent} contacts in last 90 days (+{pts}/30)")

    # Momentum (30 pts)
    mom      = 0
    upcoming = profile.get("upcoming_release", {})
    if upcoming and upcoming.get("title"):
        mom += 15
        factors.append(f"Active upcoming release: {upcoming.get('title')} (+15)")

    cutoff_180      = now - timedelta(days=180)
    recent_releases = sum(
        1 for r in profile.get("release_history", [])
        if parse_date(r.get("date") or r.get("release_date")) and
           parse_date(r.get("date") or r.get("release_date")) >= cutoff_180
    )
    if recent_releases:
        mom += 15
        factors.append(f"{recent_releases} release(s) in last 6 months (+15)")

    score += mom

    if   score >= 70: status, emoji = "Healthy",  "[OK]"
    elif score >= 45: status, emoji = "At Risk",   "[!]"
    else:             status, emoji = "Critical",  "[!!]"

    return {
        "score":               score,
        "status":              status,
        "status_emoji":        emoji,
        "factors":             factors,
        "days_since_contact":  days_since,
        "recent_contacts_90d": recent,
    }


# ── Pattern Detector ───────────────────────────────────────────────────────────

def detect_patterns(profile: dict) -> dict:
    history = profile.get("communication_history", [])
    now     = datetime.now(timezone.utc)

    dated = sorted(
        [
            (parse_date(e.get("date") or e.get("timestamp")), e)
            for e in history
            if parse_date(e.get("date") or e.get("timestamp"))
        ],
        key=lambda x: x[0],
    )

    if len(dated) < 2:
        return {
            "trend":                "insufficient_data",
            "avg_contact_gap_days": None,
            "most_recent_gap_days": (now - dated[0][0]).days if dated else None,
            "total_interactions":   len(dated),
            "anomalies":            [],
        }

    gaps       = [(dated[i][0] - dated[i - 1][0]).days for i in range(1, len(dated))]
    avg_gap    = sum(gaps) / len(gaps)
    recent_gap = (now - dated[-1][0]).days

    anomalies = []
    if recent_gap > avg_gap * 2:
        anomalies.append(
            f"Silence extending: {recent_gap}d since last contact vs avg {floor(avg_gap)}d"
        )

    if len(gaps) >= 3:
        mid       = len(gaps) // 2
        early_avg = sum(gaps[:mid]) / mid
        late_avg  = sum(gaps[mid:]) / (len(gaps) - mid)
        if   late_avg < early_avg * 0.8: trend = "improving"
        elif late_avg > early_avg * 1.3: trend = "declining"
        else:                            trend = "stable"
    else:
        trend = "stable"

    return {
        "trend":                trend,
        "avg_contact_gap_days": floor(avg_gap),
        "most_recent_gap_days": recent_gap,
        "total_interactions":   len(dated),
        "anomalies":            anomalies,
    }


# ── Single artist prompt ───────────────────────────────────────────────────────

def build_prompt(
    artist_name: str,
    today_str: str,
    profile: dict,
    health: dict,
    patterns: dict,
    atlas_data:  dict | None,
    sage_data:   dict | None,
) -> str:

    sections = [
        f"### ARTIST PROFILE\n{json.dumps(profile, indent=2)}",
        f"### HEALTH SCORE (Python-calculated)\n{json.dumps(health, indent=2)}",
        f"### COMMUNICATION PATTERNS (Python-calculated)\n{json.dumps(patterns, indent=2)}",
    ]
    if atlas_data:
        sections.append(f"### ATLAS — Revenue Context\n{json.dumps(atlas_data, indent=2)}")
    if sage_data:
        sections.append(f"### SAGE — Weekly Plan Context\n{json.dumps(sage_data, indent=2)}")

    context = "\n\n".join(sections)

    return f"""You are BRIDGE, the artist relations intelligence agent for LR Records.
Today is {today_str}. Artist under analysis: {artist_name}

Interpret the pre-calculated relationship data and craft one perfect check-in message
in the label owner's authentic voice. The owner is direct, warm, action-oriented,
and genuinely celebratory of wins. No corporate language — like texting a mate who
happens to be their label.

{context}

Return ONLY a valid JSON object — no markdown fences, no commentary:

{{
  "artist": "{artist_name}",
  "health": {{
    "score": {health["score"]},
    "status": "{health["status"]}",
    "interpretation": "<1-2 sentences: what this score means for THIS relationship right now>"
  }},
  "pattern_analysis": {{
    "trend": "{patterns.get("trend", "unknown")}",
    "summary": "<What the communication pattern tells you about this specific relationship>",
    "key_concern": "<Single most important thing to address, or null if none>"
  }},
  "predictions": [
    {{
      "timeframe": "<e.g. This week | Next 30 days | This quarter>",
      "prediction": "<Specific, artist-relevant prediction>",
      "recommended_action": "<Concrete action to take>"
    }}
  ],
  "opportunities": [
    "<Specific, actionable opportunity for this artist — achievable in next 30 days>"
  ],
  "check_in_message": {{
    "channel": "Email | SMS | DM",
    "subject": "<Subject line if Email, else null>",
    "message": "<Actual check-in message. Warm, direct, specific to this artist. 2-4 sentences. Written AS the label owner. Must reference real project details from the profile.>",
    "tone_notes": "<Why this tone and approach for this artist right now>"
  }},
  "action_items": [
    {{
      "priority": 1,
      "action": "<Specific task>",
      "deadline": "<e.g. Today | This week | Before release>",
      "owner": "LABEL | ARTIST"
    }}
  ],
  "risk_assessment": {{
    "churn_risk": "LOW | MEDIUM | HIGH",
    "churn_risk_reason": "<Why>",
    "intervention_needed": true
  }},
  "built_at_utc": null
}}

Non-negotiables:
- check_in_message.message MUST reference specific details from this artist profile
- A message that could be sent to ANY artist must be rewritten until it cannot
- predictions must reflect THIS artist's actual situation and release history
- opportunities must be genuinely achievable in the next 30 days"""


# ── Roster briefing prompt ─────────────────────────────────────────────────────

def build_briefing_prompt(today_str: str, roster_health: list[dict]) -> str:
    return f"""You are BRIDGE, the artist relations intelligence agent for LR Records.
Today is {today_str}. Generate a full roster health briefing.

### ROSTER HEALTH DATA (Python-calculated, sorted worst-first)
{json.dumps(roster_health, indent=2)}

Return ONLY a valid JSON object — no markdown fences, no commentary:

{{
  "briefing_date": "{today_str}",
  "roster_summary": "<2-3 sentences: overall health of the roster today>",
  "critical_alerts": [
    {{
      "artist": "<name>",
      "alert": "<What is wrong and why it is urgent>",
      "immediate_action": "<What to do today>"
    }}
  ],
  "at_risk_artists": [
    {{
      "artist": "<name>",
      "concern": "<Specific concern>",
      "recommended_action": "<What to do this week>"
    }}
  ],
  "healthy_artists": ["<names of artists with Healthy status>"],
  "opportunities": [
    {{
      "artist": "<name>",
      "opportunity": "<Specific, achievable opportunity>",
      "window": "<How long this window lasts>"
    }}
  ],
  "weekly_contact_priorities": [
    {{
      "priority": 1,
      "artist": "<name>",
      "action": "<Specific contact action>",
      "why": "<Why this artist is priority this week>"
    }}
  ],
  "roster_trend": "IMPROVING | STABLE | DECLINING",
  "roster_trend_reason": "<Brief explanation>"
}}"""


# ── Core: single artist ────────────────────────────────────────────────────────

def run(artist_profile: dict, artist_slug: str) -> dict | None:
    artist_name = artist_profile.get("artist_info", {}).get("name", artist_slug)
    today_str   = datetime.now(timezone.utc).strftime("%A, %d %B %Y")

    # Python calculations — no API call needed
    health   = calculate_health(artist_profile)
    patterns = detect_patterns(artist_profile)

    print(f"  {health['status_emoji']} Health: {health['score']}/100 ({health['status']})")
    print(f"  Trend:  {patterns.get('trend', 'unknown')}")
    if patterns.get("anomalies"):
        for a in patterns["anomalies"]:
            print(f"  ALERT:  {a}")

    atlas_data, _ = find_latest_output(ATLAS_DIR, artist_slug)
    sage_data,  _ = find_latest_output(SAGE_DIR,  artist_slug)

    ctx_parts = ["artist profile", "health score", "patterns"]
    if atlas_data: ctx_parts.append("ATLAS")
    if sage_data:  ctx_parts.append("SAGE")
    print(f"  Context: {', '.join(ctx_parts)}")

    prompt = build_prompt(
        artist_name, today_str, artist_profile,
        health, patterns, atlas_data, sage_data,
    )

    print(f"  Calling {get_provider().upper()}...")
    response_text = call_llm(prompt, max_tokens=4096).strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1]).strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"  ERROR parsing JSON: {e}")
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        err = BRIDGE_DIR / f"{artist_slug}_error.txt"
        err.write_text(response_text, encoding="utf-8")
        print(f"  Raw response saved -> {err.relative_to(BASE_DIR)}")
        return None

    result["built_at_utc"] = datetime.now(timezone.utc).isoformat()

    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = BRIDGE_DIR / f"{artist_slug}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  Saved -> {path.relative_to(BASE_DIR)}")
        # Post to n8n (no-op if N8N_WEBHOOK_URL not set)
    post_health_webhook(artist_name, health, patterns, result)

    return result

# ── Core: full roster briefing ─────────────────────────────────────────────────

def run_roster_briefing(all_artists: list[tuple[dict, str]]) -> dict | None:
    today_str    = datetime.now(timezone.utc).strftime("%A, %d %B %Y")
    roster_health = []

    for profile, slug in all_artists:
        name     = profile.get("artist_info", {}).get("name", slug)
        health   = calculate_health(profile)
        patterns = detect_patterns(profile)
        roster_health.append({
            "name": name, "slug": slug,
            "health": health, "patterns": patterns,
        })
        print(f"  {health['status_emoji']} {name}: {health['score']}/100 ({health['status']})")

    # Worst first so LLM prioritises correctly
    roster_health.sort(key=lambda x: x["health"]["score"])

    prompt  = build_briefing_prompt(today_str, roster_health)
    print(f"\n  Calling {get_provider().upper()} for roster briefing...")
    response_text = call_llm(prompt, max_tokens=4096).strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1]).strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"  ERROR parsing JSON: {e}")
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        err = BRIDGE_DIR / "roster_briefing_error.txt"
        err.write_text(response_text, encoding="utf-8")
        return None

    result["built_at_utc"]  = datetime.now(timezone.utc).isoformat()
    result["roster_detail"] = roster_health
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = BRIDGE_DIR / f"roster_briefing_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  Saved -> {path.relative_to(BASE_DIR)}")
    return result
    