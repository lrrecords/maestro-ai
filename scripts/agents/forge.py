#!/usr/bin/env python3
"""
FORGE — Development & Automation Agent
MAESTRO AI · LR Records

Ingests artist profile + most recent outputs from all other agents:
  VINYL  — release workflow steps to automate
  ECHO   — content scheduling and posting to automate
  ATLAS  — reporting and data ingestion to automate
  SAGE   — weekly tasks that could be systematised (from previous run)
  BRIDGE — relationship management to automate (check-ins, health monitoring)

Note on pipeline order: in `full` (VINYL→ECHO→ATLAS→FORGE→SAGE), SAGE output
will not yet exist for this run. FORGE picks up SAGE from a previous run if
available. BRIDGE is standalone — run it before `full` for richest FORGE output.

Output saved to data/forge/ as JSON.
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
SAGE_DIR   = DATA_DIR / "sage"
BRIDGE_DIR = DATA_DIR / "bridge"
FORGE_DIR  = DATA_DIR / "forge"


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


def build_prompt(
    artist_name: str,
    today_str: str,
    artist_profile: dict,
    vinyl_data:  dict | None,
    echo_data:   dict | None,
    atlas_data:  dict | None,
    sage_data:   dict | None,
    bridge_data: dict | None,
    sources_used: list[str],
    missing: list[str],
) -> str:

    sections = [f"### ARTIST PROFILE\n{json.dumps(artist_profile, indent=2)}"]
    if vinyl_data:
        sections.append(f"### VINYL — Release Checklist\n{json.dumps(vinyl_data, indent=2)}")
    if echo_data:
        sections.append(f"### ECHO — Content Plan\n{json.dumps(echo_data, indent=2)}")
    if atlas_data:
        sections.append(f"### ATLAS — Analytics Report\n{json.dumps(atlas_data, indent=2)}")
    if sage_data:
        sections.append(f"### SAGE — Weekly Plan (previous run)\n{json.dumps(sage_data, indent=2)}")
    if bridge_data:
        sections.append(f"### BRIDGE — Artist Relationship Data\n{json.dumps(bridge_data, indent=2)}")

    context = "\n\n".join(sections)

    bridge_instruction = ""
    if bridge_data:
        bridge_instruction = """
BRIDGE DATA IS AVAILABLE. In addition to release and content automation, generate specs for:
- Automated health score monitoring (scheduled health checks against artist JSON profiles)
- Check-in message generation queue (auto-draft + human approval before send)
- Email/notification triggers for At Risk (<60) and Critical (<40) health scores
- Contact frequency tracker and alert system
The standalone BRIDGE autopilot (maestro_autopilot.py) already exists in the project.
Reference it as existing infrastructure. Spec integrations and extensions — not duplicates.
Where BRIDGE has flagged a check-in message or action item, spec the automation to deliver it."""

    missing_note = (
        f"\n⚠️ Missing outputs from: {', '.join(missing)}. "
        "Note in technical_flags what additional automations become possible once those agents run."
        if missing else ""
    )

    return f"""You are FORGE, the development and automation specialist for LR Records.
Today is {today_str}. Generating a technical automation report for: {artist_name}

Analyse ALL available agent data and identify specific, immediately implementable automation 
opportunities. Be concrete — name the actual APIs, exact n8n node types, endpoints, auth 
methods, and field mappings. Every recommendation must reference real details from this 
artist's data. Nothing generic.
{bridge_instruction}
{context}
{missing_note}

Return ONLY a valid JSON object — no markdown fences, no commentary:

{{
  "artist": "{artist_name}",
  "automation_opportunities": [
    {{
      "priority": 1,
      "title": "<Short, specific title>",
      "type": "n8n_workflow | api_integration | script | webhook",
      "effort": "LOW | MEDIUM | HIGH",
      "impact": "LOW | MEDIUM | HIGH",
      "time_saved_per_week": "<e.g. 2 hours>",
      "description": "<What this automates, referencing real data from this artist>",
      "implementation_notes": "<Exact tools, API names, n8n nodes, endpoints, credentials>"
    }}
  ],
  "n8n_workflow_specs": [
    {{
      "workflow_name": "<Name>",
      "trigger": "Schedule | Webhook | Manual",
      "trigger_detail": "<e.g. Every Monday 09:00 AWST | POST /webhook/release-update>",
      "steps": [
        {{
          "step": 1,
          "node_type": "<Exact n8n node: HTTP Request | Gmail | Code | IF | Set | Webhook | etc.>",
          "action": "<Exactly what this step does, with what data, to what endpoint>"
        }}
      ],
      "estimated_time_saved_per_week": "<e.g. 3 hours>",
      "notes": "<Credentials, config, or dependencies required before this workflow runs>"
    }}
  ],
  "api_integrations_recommended": [
    {{
      "platform": "<Platform name>",
      "api_doc_url": "<URL or null>",
      "use_case": "<What it enables for this artist specifically>",
      "auth_method": "API Key | OAuth 2.0 | Bearer Token | Basic Auth",
      "rate_limits": "<Known limits or null>",
      "priority": "NOW | NEXT | LATER"
    }}
  ],
  "build_backlog": [
    {{
      "item": "<Specific, actionable technical task>",
      "category": "AUTOMATION | INTEGRATION | REFACTOR | DATA | INFRASTRUCTURE | BRIDGE",
      "effort": "LOW | MEDIUM | HIGH",
      "depends_on": "<What must exist first, or null>"
    }}
  ],
  "technical_flags": [
    "<Blockers, missing credentials, data gaps, architecture concerns — be specific>"
  ],
  "data_sources_used": {json.dumps(sources_used)}
}}

Sorting rules:
- automation_opportunities: impact DESC then effort ASC — high impact + low effort = priority 1
- n8n_workflow_specs: only include workflows buildable NOW with currently available data
- api_integrations_recommended: include platforms relevant to this artist's actual 
  release_history, social_presence, and distribution (The Orchard, Bandcamp, Spotify for 
  Artists, Instagram Graph API, Meta Business API, Gmail SMTP, Mailchimp, etc.)
- build_backlog BRIDGE category: use for any automation extending the BRIDGE/autopilot system
- technical_flags: name the specific credential or config item missing — never vague"""


# ── Core agent ─────────────────────────────────────────────────────────────────

def run(artist_profile: dict, artist_slug: str) -> dict | None:
    """
    Run FORGE for a single artist.
    FORGE can operate on artist profile alone — every additional agent output
    unlocks more specific automation recommendations.
    """

    artist_name = artist_profile.get("artist_info", {}).get("name", artist_slug)
    today_str   = datetime.now(timezone.utc).strftime("%A, %d %B %Y")

    # ── Load all available agent outputs ──────────────────────────────────────

    vinyl_data,  vinyl_file  = find_latest_output(VINYL_DIR,  artist_slug)
    echo_data,   echo_file   = find_latest_output(ECHO_DIR,   artist_slug)
    atlas_data,  atlas_file  = find_latest_output(ATLAS_DIR,  artist_slug)
    sage_data,   sage_file   = find_latest_output(SAGE_DIR,   artist_slug)
    bridge_data, bridge_file = find_latest_output(BRIDGE_DIR, artist_slug)

    sources_used: list[str] = []
    missing:      list[str] = []

    def track(data, file, label):
        if data: sources_used.append(f"{label} ({file})")
        else:    missing.append(label)

    track(vinyl_data,  vinyl_file,  "VINYL")
    track(echo_data,   echo_file,   "ECHO")
    track(atlas_data,  atlas_file,  "ATLAS")
    track(sage_data,   sage_file,   "SAGE")
    track(bridge_data, bridge_file, "BRIDGE")

    source_summary = "artist profile" + (f" + {', '.join(sources_used)}" if sources_used else " only")
    print(f"  📥 Sources: {source_summary}")

    if missing:
        print(f"  ℹ️  No outputs yet from: {', '.join(missing)}")
        if "BRIDGE" in missing:
            print(f"       Tip: run bridge \"{artist_name}\" first for relationship automation specs")

    # ── Call Claude ────────────────────────────────────────────────────────────

    prompt = build_prompt(
        artist_name, today_str, artist_profile,
        vinyl_data, echo_data, atlas_data, sage_data, bridge_data,
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
        FORGE_DIR.mkdir(parents=True, exist_ok=True)
        err = FORGE_DIR / f"{artist_slug}_error.txt"
        err.write_text(response_text, encoding="utf-8")
        print(f"     Raw response saved → {err.relative_to(BASE_DIR)}")
        return None

    result["built_at_utc"] = datetime.now(timezone.utc).isoformat()

    # ── Save ───────────────────────────────────────────────────────────────────

    FORGE_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = FORGE_DIR / f"{artist_slug}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  ✅ Saved → {path.relative_to(BASE_DIR)}")
    return result