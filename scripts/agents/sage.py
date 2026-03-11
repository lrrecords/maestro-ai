#!/usr/bin/env python3
"""
SAGE — Weekly Priority Planner & PA Layer
MAESTRO AI · LR Records

Ingests most recent outputs from ALL five other agents:
  VINYL  — release tasks outstanding
  ECHO   — content posts due this week
  ATLAS  — revenue anomalies and platform health
  FORGE  — automation opportunities and build backlog
  BRIDGE — artist relationship health and contact priorities

Synthesises everything into a single ranked weekly action plan.
Output saved to data/sage/ as JSON.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

from llm.client import call_llm, get_provider
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).resolve().parent.parent.parent
DATA_DIR   = BASE_DIR / "data"
VINYL_DIR  = DATA_DIR / "vinyl"
ECHO_DIR   = DATA_DIR / "echo"
ATLAS_DIR  = DATA_DIR / "atlas"
FORGE_DIR  = DATA_DIR / "forge"
BRIDGE_DIR = DATA_DIR / "bridge"
SAGE_DIR   = DATA_DIR / "sage"


# ── Helpers ────────────────────────────────────────────────────────────────────

def find_latest_output(folder: Path, artist_slug: str) -> tuple[dict | None, str | None]:
    """Return the most recently modified JSON for this artist in the given folder."""
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


def build_prompt(
    artist_name: str,
    today_str: str,
    week_start: str,
    vinyl_data:  dict | None,
    echo_data:   dict | None,
    atlas_data:  dict | None,
    forge_data:  dict | None,
    bridge_data: dict | None,
    sources_used: list[str],
    missing: list[str],
) -> str:

    sections = []
    if vinyl_data:
        sections.append(f"### VINYL — Release Checklist\n{json.dumps(vinyl_data, indent=2)}")
    if echo_data:
        sections.append(f"### ECHO — Social Content Plan\n{json.dumps(echo_data, indent=2)}")
    if atlas_data:
        sections.append(f"### ATLAS — Analytics Report\n{json.dumps(atlas_data, indent=2)}")
    if forge_data:
        sections.append(f"### FORGE — Automation Report\n{json.dumps(forge_data, indent=2)}")
    if bridge_data:
        sections.append(f"### BRIDGE — Artist Relationship Health\n{json.dumps(bridge_data, indent=2)}")

    context = "\n\n".join(sections)

    missing_note = (
        f"\n⚠️ Missing agent outputs: {', '.join(missing)}. "
        "Note in flags and proceed with available data. If BRIDGE is missing, "
        "use artist profile data to estimate relationship priority."
        if missing else ""
    )

    return f"""You are SAGE, the weekly planning and PA layer for LR Records.
Today is {today_str}. Generating the weekly action plan for: {artist_name}

You synthesise outputs from up to five specialist agents into one focused weekly brief.
CRITICAL RULE: If BRIDGE reports a Critical health score (<40), relationship recovery 
becomes the highest priority this week — above release tasks and content.

{context}
{missing_note}

Return ONLY a valid JSON object — no markdown fences, no commentary:

{{
  "artist": "{artist_name}",
  "week_commencing": "{week_start}",
  "weekly_brief": "<3-5 sentences. Cover: relationship health + release status + \
content due + revenue/anomalies + any automation wins landing this week. \
A label manager reads this in 30 seconds and knows exactly where things stand.>",
  "action_list": [
    {{
      "priority": 1,
      "urgency": "NOW",
      "category": "VINYL | ECHO | ATLAS | FORGE | BRIDGE | ADMIN",
      "action": "<Specific, concrete task — never generic>",
      "context": "<Why this matters this week or what it unblocks>",
      "owner": "TEAM | ARTIST | LABEL"
    }}
  ],
  "relationship_priority": {{
    "health_score": "<score from BRIDGE or null>",
    "status": "Healthy | At Risk | Critical | Unknown",
    "contact_urgency": "NOW | THIS WEEK | MONITOR",
    "recommended_contact": "<Specific suggested message approach or null>",
    "reason": "<Why this urgency level this week>"
  }},
  "automation_wins_this_week": [
    "<Specific FORGE item implementable or testable this week — not long-term backlog>"
  ],
  "blocked_items": [
    {{
      "item": "<Task that cannot proceed>",
      "blocked_by": "<What is needed to unblock>",
      "requires_human_decision": true
    }}
  ],
  "flags": [
    "<Anomalies, risks, missing agents, data concerns — be specific>"
  ],
  "data_sources_used": {json.dumps(sources_used)}
}}

Sorting rules:
- urgency values: NOW (do today) | THIS WEEK (before week end) | MONITOR (watch, no action)
- action_list: all NOW items before THIS WEEK, sorted by importance within each group
- BRIDGE Critical status overrides all other priorities — relationship recovery goes first
- automation_wins_this_week: only items achievable this week, empty array if none
- relationship_priority: always populate — use BRIDGE if available, else infer from profile"""


# ── Core agent ─────────────────────────────────────────────────────────────────

def run(artist_profile: dict, artist_slug: str) -> dict | None:
    """
    Run SAGE for a single artist.
    Loads the most recent output from each of the five other agents.
    Proceeds with whatever is available — no agent output is strictly required.
    """

    artist_name = artist_profile.get("artist_info", {}).get("name", artist_slug)
    today_str   = datetime.now(timezone.utc).strftime("%A, %d %B %Y")
    week_start  = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # ── Load all available agent outputs ──────────────────────────────────────

    vinyl_data,  vinyl_file  = find_latest_output(VINYL_DIR,  artist_slug)
    echo_data,   echo_file   = find_latest_output(ECHO_DIR,   artist_slug)
    atlas_data,  atlas_file  = find_latest_output(ATLAS_DIR,  artist_slug)
    forge_data,  forge_file  = find_latest_output(FORGE_DIR,  artist_slug)
    bridge_data, bridge_file = find_latest_output(BRIDGE_DIR, artist_slug)

    sources_used: list[str] = []
    missing:      list[str] = []

    def track(data, file, label):
        if data: sources_used.append(f"{label} ({file})")
        else:    missing.append(label)

    track(vinyl_data,  vinyl_file,  "VINYL")
    track(echo_data,   echo_file,   "ECHO")
    track(atlas_data,  atlas_file,  "ATLAS")
    track(forge_data,  forge_file,  "FORGE")
    track(bridge_data, bridge_file, "BRIDGE")

    if not sources_used:
        print(f"  ⚠️  No agent outputs found for {artist_name}.")
        print(f"       Run other agents first, or run: full \"{artist_name}\"")
        return None

    if missing:
        print(f"  ⚠️  Missing outputs: {', '.join(missing)} — proceeding with available data")
        if "BRIDGE" in missing:
            print(f"       Tip: run bridge \"{artist_name}\" for relationship health data")

    print(f"  📥 Sources loaded: {', '.join(sources_used)}")

    # ── Call Claude ────────────────────────────────────────────────────────────

    prompt = build_prompt(
        artist_name, today_str, week_start,
        vinyl_data, echo_data, atlas_data, forge_data, bridge_data,
        sources_used, missing,
    )

    print(f"  🤖 Calling {get_provider().upper()}...")
    response_text = call_llm(prompt, max_tokens=4096).strip()
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1]).strip()

    # ── Parse ──────────────────────────────────────────────────────────────────

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"  ❌ JSON parse error: {e}")
        SAGE_DIR.mkdir(parents=True, exist_ok=True)
        err = SAGE_DIR / f"{artist_slug}_error.txt"
        err.write_text(response_text, encoding="utf-8")
        print(f"     Raw response saved → {err.relative_to(BASE_DIR)}")
        return None

    result["built_at_utc"] = datetime.now(timezone.utc).isoformat()

    # ── Save ───────────────────────────────────────────────────────────────────

    SAGE_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = SAGE_DIR / f"{artist_slug}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  ✅ Saved → {path.relative_to(BASE_DIR)}")
    return result