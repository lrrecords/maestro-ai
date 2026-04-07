# MAESTRO AI — Full Implementation Guide
> All code produced in the design session. Ready to paste into your repo.

---

## Step 1 — Install New Dependencies

```bash
pip install crewai playwright google-analytics-data requests
playwright install chromium  # for browser automation fallback
```

Add to `requirements.txt`:
```
crewai>=0.80.0
playwright>=1.40.0
google-analytics-data>=0.18.0
```

---

## Step 2 — Create `crews/` Module

### `crews/__init__.py`
```python
"""
Maestro AI — CrewAI integration layer.
Maps existing Maestro agents to CrewAI role-based crews.
DO NOT import from here at app startup — import inside route handlers to avoid circular deps.
"""
```

---

### `crews/base_crew.py` — CEO Approval Infrastructure

```python
# crews/base_crew.py
"""
CEO approval queue — all protected actions must pass through here.
Protected actions: mass email, public posts, money spend, NFT mint, bulk CRM updates.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

APPROVAL_QUEUE_PATH = Path("data/ceo_approval_queue.json")

# Tasks that ALWAYS require CEO sign-off before execution
PROTECTED_ACTIONS = {
    "send_mass_email",
    "publish_public_content",
    "spend_money",
    "bulk_crm_update",
    "mint_nft",
    "post_social_media",
    "sign_contract",
    "orchard_submission",
    "spotify_playlist_pitch",
    "press_outreach",
}


def requires_approval(action_type: str) -> bool:
    return action_type in PROTECTED_ACTIONS


def queue_for_approval(action_type: str, payload: dict, agent_name: str) -> str:
    """Add a task to the CEO approval queue. Returns task_id."""
    queue = _load_queue()
    ts = datetime.now(timezone.utc).isoformat()
    task_id = f"{agent_name}_{action_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    queue.append({
        "task_id":   task_id,
        "action":    action_type,
        "agent":     agent_name,
        "payload":   payload,
        "status":    "pending",
        "queued_at": ts,
    })
    _save_queue(queue)
    return task_id


def approve_task(task_id: str, approved: bool, note: str = "") -> dict:
    queue = _load_queue()
    for item in queue:
        if item["task_id"] == task_id:
            item["status"]     = "approved" if approved else "rejected"
            item["ceo_note"]   = note
            item["actioned_at"] = datetime.now(timezone.utc).isoformat()
            _save_queue(queue)
            return item
    return {"error": "Task not found"}


def get_pending_approvals() -> list:
    return [t for t in _load_queue() if t["status"] == "pending"]


def get_all_approvals(limit: int = 50) -> list:
    return _load_queue()[-limit:]


def _load_queue() -> list:
    if APPROVAL_QUEUE_PATH.exists():
        try:
            return json.loads(APPROVAL_QUEUE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_queue(queue: list):
    APPROVAL_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    APPROVAL_QUEUE_PATH.write_text(
        json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8"
    )
```

---

### `crews/label_crew.py` — Label Department Crew

```python
# crews/label_crew.py
"""
CrewAI crew for the Label department.
Wraps existing Maestro agents (BRIDGE, VINYL, ECHO, SAGE) as CrewAI role-playing agents.
Each agent's tools call the existing Maestro Flask endpoints — no duplication of logic.
"""
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crews.base_crew import queue_for_approval
import requests, os, json


MAESTRO_BASE = os.getenv("MAESTRO_BASE_URL", "http://localhost:8080")


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool("Run BRIDGE health check for an artist")
def run_bridge(artist_slug: str) -> str:
    """
    Run BRIDGE agent to assess artist relationship health score and draft a check-in.
    Returns health score (0-100), trend, and a personalised check-in message draft.
    """
    r = requests.get(f"{MAESTRO_BASE}/label/api/artist/{artist_slug}", timeout=30)
    data = r.json()
    bridge_output = data.get("outputs", {}).get("bridge", {})
    return json.dumps(bridge_output, indent=2) if bridge_output else f"No BRIDGE data for {artist_slug}. Run BRIDGE agent first."


@tool("Run VINYL release checklist for an artist")
def run_vinyl(artist_slug: str) -> str:
    """
    Generate a complete release checklist for the artist's current project.
    Includes pre-production, distribution metadata, marketing, and post-release phases.
    """
    r = requests.get(f"{MAESTRO_BASE}/label/api/stream/vinyl/{artist_slug}", stream=True, timeout=120)
    result = ""
    for line in r.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            if decoded.startswith("data: ") and "[DONE]" not in decoded:
                try:
                    chunk = json.loads(decoded[6:])
                    if chunk.get("result"):
                        result = json.dumps(chunk["result"], indent=2)
                except Exception:
                    pass
    return result or "VINYL agent returned no result. Check Ollama is running."


@tool("Get artist profile and metadata")
def get_artist_profile(artist_slug: str) -> str:
    """Get full artist profile including upcoming release, genre, communication history."""
    r = requests.get(f"{MAESTRO_BASE}/label/api/artist/{artist_slug}", timeout=15)
    data = r.json()
    profile = data.get("profile", {})
    return json.dumps({
        "name":     profile.get("artist_info", {}).get("name"),
        "genre":    profile.get("musical_identity", {}).get("primary_genre"),
        "release":  profile.get("upcoming_release", {}),
        "score":    data.get("score"),
        "trend":    data.get("trend"),
        "status":   data.get("status"),
    }, indent=2)


@tool("Queue content for CEO approval")
def queue_content_approval(content_type: str, content: str, artist: str) -> str:
    """
    Queue any public-facing content for CEO sign-off BEFORE scheduling or publishing.
    content_type: 'social_post' | 'email_campaign' | 'blog_post' | 'press_release'
    """
    task_id = queue_for_approval(
        "publish_public_content",
        {"content_type": content_type, "content": content, "artist": artist},
        "ECHO"
    )
    return f"✅ Content queued for CEO approval. Task ID: {task_id}. Will NOT publish until approved."


@tool("Queue email campaign for CEO approval")
def queue_email_campaign(artist: str, subject: str, body: str, segment: str = "all") -> str:
    """
    Queue an email campaign brief for CEO approval before sending via EasyFunnels.
    NEVER sends directly — always queued.
    """
    task_id = queue_for_approval(
        "send_mass_email",
        {"artist": artist, "subject": subject, "body": body, "segment": segment},
        "ECHO"
    )
    return f"✅ Email campaign queued for CEO approval. Task ID: {task_id}. Will NOT send until approved."


@tool("Queue check-in message for CEO approval")
def queue_checkin_message(artist: str, channel: str, message: str) -> str:
    """Queue an artist check-in message for CEO review before sending."""
    task_id = queue_for_approval(
        "send_mass_email",
        {"artist": artist, "channel": channel, "message": message, "type": "artist_checkin"},
        "BRIDGE"
    )
    return f"✅ Check-in message queued for CEO approval. Task ID: {task_id}"


# ─── Agent Definitions ────────────────────────────────────────────────────────

bridge_agent = Agent(
    role="Artist Relations Director",
    goal="Monitor every artist's relationship health and ensure no one falls through the cracks",
    backstory=(
        "You are BRIDGE — LRRecords' artist intelligence agent. "
        "You score relationships 0-100 based on recency, frequency, and momentum. "
        "You detect trends (improving/stable/declining) and draft personalised check-in messages "
        "in Brett's direct, warm, action-oriented voice. No corporate language. "
        "You NEVER send anything without CEO approval."
    ),
    tools=[run_bridge, get_artist_profile, queue_checkin_message],
    verbose=True,
    allow_delegation=False,
)

vinyl_agent = Agent(
    role="Music Operations Director",
    goal="Keep every release on track from pre-production through post-release metrics",
    backstory=(
        "You are VINYL — the label's release operations specialist. "
        "You generate phased release checklists, track distribution deadlines, "
        "and coordinate metadata submissions to The Orchard. "
        "You are systematic, checklist-driven, and deadline-obsessed. "
        "You know that artwork approval via The Orchard takes up to 2 weeks — you plan for it."
    ),
    tools=[run_vinyl, get_artist_profile],
    verbose=True,
    allow_delegation=False,
)

echo_agent = Agent(
    role="Content and Marketing Chief",
    goal="Plan and draft content that builds real audience and drives release momentum",
    backstory=(
        "You are ECHO — LRRecords' content strategist. "
        "You build 2-week content calendars, write captions for Instagram/TikTok/X, "
        "and craft email campaign briefs. You understand the indie doom/electronic music "
        "audience. You post quality over quantity. "
        "You ALWAYS queue public-facing content for CEO approval — never publish directly."
    ),
    tools=[queue_content_approval, queue_email_campaign],
    verbose=True,
    allow_delegation=True,
)

sage_agent = Agent(
    role="Chief of Staff and Weekly Planner",
    goal="Synthesise all agent outputs into the CEO's ranked weekly action list",
    backstory=(
        "You are SAGE — Brett's AI chief of staff. "
        "You read every other agent's output and distil it into a 30-second CEO briefing: "
        "top 5 actions this week, blockers, approvals needed, and wins to celebrate. "
        "You never bury the lead. The most urgent item is always first."
    ),
    tools=[],
    verbose=True,
    allow_delegation=True,
)


# ─── Crew Builders ────────────────────────────────────────────────────────────

def build_release_campaign_crew(artist_slug: str, release_title: str) -> Crew:
    """
    Full release campaign crew: VINYL → ECHO → BRIDGE → SAGE
    Use for: new single/EP/album release preparation
    """
    task_checklist = Task(
        description=(
            f"Generate a complete release checklist for artist '{artist_slug}' "
            f"and their upcoming release '{release_title}'. "
            f"Cover all phases: Pre-Production, Distribution & Metadata, "
            f"Marketing & Promo, Release Day, Post-Release. "
            f"Flag any immediate blockers."
        ),
        expected_output="Structured JSON release checklist with phases, tasks, priorities, statuses, and deadlines.",
        agent=vinyl_agent,
    )

    task_content = Task(
        description=(
            f"Using the release checklist context, build a 14-day content calendar "
            f"for '{artist_slug}' releasing '{release_title}'. "
            f"Plan posts for Instagram, TikTok, and X. "
            f"Queue ALL posts for CEO approval — do not schedule directly. "
            f"Also draft one email campaign announcement brief and queue for CEO approval."
        ),
        expected_output=(
            "14-day content plan (date, platform, content type, copy, visual direction) "
            "plus one email campaign brief. All queued for CEO approval with task IDs."
        ),
        agent=echo_agent,
        context=[task_checklist],
    )

    task_health = Task(
        description=(
            f"Run a BRIDGE health check on '{artist_slug}'. "
            f"Assess the relationship score and trend. "
            f"Draft a personalised check-in message that references the upcoming release '{release_title}'. "
            f"Queue the check-in for CEO approval — do not send."
        ),
        expected_output=(
            "Health score (0-100), trend, key factors, and a draft check-in message "
            "specific to this release. Check-in queued for CEO approval with task ID."
        ),
        agent=bridge_agent,
    )

    task_brief = Task(
        description=(
            f"Synthesise the release checklist, 14-day content plan, and artist health check "
            f"into Brett's weekly CEO brief for '{artist_slug}'. "
            f"Rank the 5 most urgent actions. List what needs Brett's approval. "
            f"Surface any blockers. Flag anything at risk of missing the release date."
        ),
        expected_output=(
            "CEO brief: top 5 ranked actions, approval queue summary, "
            "blockers list, and release risk assessment."
        ),
        agent=sage_agent,
        context=[task_checklist, task_content, task_health],
    )

    return Crew(
        agents=[vinyl_agent, echo_agent, bridge_agent, sage_agent],
        tasks=[task_checklist, task_content, task_health, task_brief],
        process=Process.sequential,
        verbose=True,
    )


def build_roster_health_crew(artist_slugs: list) -> Crew:
    """
    Weekly roster health check across all artists.
    Use for: Monday morning CEO briefing
    """
    task_health = Task(
        description=(
            f"Run BRIDGE health checks for these artists: {', '.join(artist_slugs)}. "
            f"Rank them from most critical to healthiest. "
            f"For any artist below 40 (Critical), draft an urgent check-in and queue for CEO. "
            f"For any artist between 40-70 (At Risk), draft a check-in and queue for CEO."
        ),
        expected_output=(
            "Ranked artist health table with scores, trends, and status. "
            "Draft check-ins queued for Critical and At-Risk artists."
        ),
        agent=bridge_agent,
    )

    task_brief = Task(
        description=(
            "Create the CEO Monday Morning Roster Brief. "
            "Which artist needs attention most urgently and why? "
            "What are the top 3 relationship actions this week?"
        ),
        expected_output="Monday brief: ranked artist priority list with specific recommended actions.",
        agent=sage_agent,
        context=[task_health],
    )

    return Crew(
        agents=[bridge_agent, sage_agent],
        tasks=[task_health, task_brief],
        process=Process.sequential,
        verbose=True,
    )
```

---

### `crews/internet_crew.py` — Internet Expansion Agent

```python
# crews/internet_crew.py
"""
CrewAI internet presence agent.
Monitors and grows LRRecords across social media, music platforms, Web3, and the internet.
All posting actions require CEO approval before execution.
"""
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crews.base_crew import queue_for_approval
import requests, os, json


# ─── Social Media Tools ───────────────────────────────────────────────────────

@tool("Get Instagram engagement insights")
def get_instagram_insights(page_id: str = "") -> str:
    """Read Instagram impressions, reach, and follower count via Meta Graph API."""
    token   = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    page_id = page_id or os.getenv("INSTAGRAM_PAGE_ID_DEFAULT")
    if not token or not page_id:
        return "Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_PAGE_ID_DEFAULT in .env [verify: Meta Graph API access]"
    r = requests.get(
        f"https://graph.facebook.com/v19.0/{page_id}/insights",
        params={"metric": "impressions,reach,follower_count", "period": "week", "access_token": token}
    )
    return json.dumps(r.json(), indent=2)


@tool("Queue Instagram post for CEO approval")
def queue_instagram_post(image_url: str, caption: str, artist: str) -> str:
    """Queue an Instagram post for CEO approval. Will NOT post until approved."""
    task_id = queue_for_approval(
        "post_social_media",
        {"platform": "instagram", "image_url": image_url, "caption": caption, "artist": artist},
        "ECHO"
    )
    return f"✅ Instagram post queued for CEO approval. Task ID: {task_id}"


@tool("Queue X/Twitter post for CEO approval")
def queue_x_post(text: str, artist: str) -> str:
    """Queue an X/Twitter post for CEO approval. Will NOT post until approved."""
    task_id = queue_for_approval(
        "post_social_media",
        {"platform": "x_twitter", "text": text, "artist": artist},
        "ECHO"
    )
    return f"✅ X post queued for CEO approval. Task ID: {task_id}"


@tool("Monitor X/Twitter mentions and keywords")
def monitor_x_mentions(query: str) -> str:
    """Search recent X posts for artist name or release keywords."""
    bearer = os.getenv("X_BEARER_TOKEN")
    if not bearer:
        return "Set X_BEARER_TOKEN in .env [verify: X/Twitter API v2 access]"
    r = requests.get(
        "https://api.twitter.com/2/tweets/search/recent",
        headers={"Authorization": f"Bearer {bearer}"},
        params={"query": query, "max_results": 10, "tweet.fields": "public_metrics"}
    )
    return json.dumps(r.json(), indent=2)


# ─── Music Platform Tools ─────────────────────────────────────────────────────

@tool("Get Spotify top tracks and stream data")
def get_spotify_streams(artist_id: str) -> str:
    """Pull Spotify top tracks and approximate stream counts."""
    token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    if not token:
        return "Set SPOTIFY_ACCESS_TOKEN in .env. Run OAuth client credentials flow first [verify]"
    r = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"market": "AU"}
    )
    return json.dumps(r.json(), indent=2)


@tool("Get Bandcamp sales from exported CSV")
def get_bandcamp_sales(artist_slug: str) -> str:
    """
    Read Bandcamp sales from a pre-downloaded CSV.
    Bandcamp has no public API [verify current status].
    To update: Bandcamp dashboard → Sales → Export CSV → save to data/metrics/bandcamp/
    """
    import glob
    files = glob.glob(f"data/metrics/bandcamp/*{artist_slug}*.csv")
    if not files:
        return (
            f"No Bandcamp CSV for {artist_slug}. "
            f"Download: Bandcamp → Fan Dashboard → Sales → Export CSV. "
            f"Save to data/metrics/bandcamp/{artist_slug}_YYYY-MM.csv"
        )
    latest = max(files)
    with open(latest) as f:
        rows = f.readlines()
    return f"File: {latest}\nFirst 6 rows:\n" + "".join(rows[:6])


@tool("Check The Orchard release status")
def get_orchard_release_status(release_upc: str) -> str:
    """
    Check release delivery status via The Orchard API [verify: requires Orchard API credentials].
    Contact your Orchard label rep to request API access.
    """
    api_key = os.getenv("ORCHARD_API_KEY")
    if not api_key:
        return (
            "ORCHARD_API_KEY not set [verify]. "
            "Contact The Orchard label services team to request API/portal access. "
            "Alternative: log into The Orchard portal manually and export reports."
        )
    # Endpoint approximate [verify with Orchard API docs]
    r = requests.get(
        f"https://api.theorchard.com/v1/releases/{release_upc}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return json.dumps(r.json(), indent=2)


@tool("Queue Spotify editorial playlist pitch")
def queue_spotify_pitch(track_uri: str, pitch_notes: str, release_date: str) -> str:
    """
    Queue a Spotify editorial playlist pitch for CEO approval.
    Must be submitted within 7 days before release date [verify: Spotify for Artists API].
    """
    task_id = queue_for_approval(
        "spotify_playlist_pitch",
        {"track_uri": track_uri, "pitch_notes": pitch_notes, "release_date": release_date},
        "VINYL"
    )
    return f"✅ Spotify playlist pitch queued for CEO approval. Task ID: {task_id}"


@tool("Draft Doom Charts press submission")
def draft_doomcharts_submission(artist: str, release: str, genre: str, press_text: str) -> str:
    """
    Draft a press submission for doomcharts.com and queue for CEO approval before sending.
    Doom Charts covers: doom, sludge, stoner, death metal [verify current submission process at doomcharts.com].
    """
    task_id = queue_for_approval(
        "press_outreach",
        {
            "outlet": "Doom Charts",
            "url": "https://doomcharts.com",
            "artist": artist,
            "release": release,
            "genre": genre,
            "press_text": press_text,
            "note": "Verify current submission method at doomcharts.com/contact before sending"
        },
        "ECHO"
    )
    return f"✅ Doom Charts submission drafted and queued for CEO approval. Task ID: {task_id}"


# ─── General Internet Tools ───────────────────────────────────────────────────

@tool("Get Google Analytics traffic data for lrrecords.com.au")
def get_ga4_traffic(property_id: str, days: str = "7daysAgo") -> str:
    """
    Pull GA4 traffic data for the EasyFunnels-hosted site.
    Requires: GOOGLE_APPLICATION_CREDENTIALS set to path of service account JSON [verify: GA4 API setup].
    """
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        return (
            "GOOGLE_APPLICATION_CREDENTIALS not set [verify]. "
            "Steps: Google Cloud Console → Create service account → "
            "Grant GA4 Viewer role → Download JSON → set path in .env"
        )
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Dimension, Metric
        )
        client = BetaAnalyticsDataClient()
        response = client.run_report(RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
            date_ranges=[DateRange(start_date=days, end_date="today")]
        ))
        rows = [
            {"page": r.dimension_values[0].value,
             "sessions": r.metric_values[0].value,
             "users": r.metric_values[1].value}
            for r in response.rows[:10]
        ]
        return json.dumps(rows, indent=2)
    except ImportError:
        return "Run: pip install google-analytics-data"


@tool("Queue blog post for CEO approval before publishing")
def queue_blog_post(title: str, content: str, seo_keywords: list, artist: str) -> str:
    """
    Queue an SEO blog post for CEO approval before publishing to EasyFunnels blog [verify: EasyFunnels blog API].
    """
    task_id = queue_for_approval(
        "publish_public_content",
        {"type": "blog", "title": title, "content": content,
         "seo_keywords": seo_keywords, "artist": artist},
        "ECHO"
    )
    return f"✅ Blog post '{title}' queued for CEO approval. Task ID: {task_id}"


@tool("Queue NFT mint for CEO approval")
def queue_nft_mint(contract_address: str, metadata: dict, recipient_wallet: str) -> str:
    """
    Queue an NFT mint for CEO approval [verify: Thirdweb Python SDK, gas cost applies].
    Will NOT mint until CEO explicitly approves — this spends gas.
    """
    task_id = queue_for_approval(
        "mint_nft",
        {"contract": contract_address, "metadata": metadata, "recipient": recipient_wallet},
        "FORGE"
    )
    return f"✅ NFT mint queued for CEO approval. GAS COST APPLIES. Task ID: {task_id}"


# ─── Internet Agent ───────────────────────────────────────────────────────────

internet_agent = Agent(
    role="Digital Presence and Internet Expansion Agent",
    goal=(
        "Monitor and grow LRRecords across social media, music platforms, Web3, and the internet. "
        "Pull analytics, identify opportunities, draft outreach, and surface everything for CEO decision."
    ),
    backstory=(
        "You are the internet arm of Maestro AI. "
        "You track Spotify streams, Instagram engagement, Bandcamp sales, and website traffic. "
        "You know the heavy music press scene — Doom Charts is a key target. "
        "You draft content and press pitches but NEVER publish without CEO approval. "
        "You speak in data and opportunities, not hype."
    ),
    tools=[
        get_instagram_insights,
        queue_instagram_post,
        queue_x_post,
        monitor_x_mentions,
        get_spotify_streams,
        get_bandcamp_sales,
        get_orchard_release_status,
        queue_spotify_pitch,
        draft_doomcharts_submission,
        get_ga4_traffic,
        queue_blog_post,
        queue_nft_mint,
    ],
    verbose=True,
    allow_delegation=False,
)


def build_weekly_internet_report(artist_slug: str) -> Crew:
    """Pull all platform data and surface top 3 opportunities for the week."""
    task = Task(
        description=(
            f"For artist '{artist_slug}':\n"
            f"1. Pull Spotify top-tracks data\n"
            f"2. Get Instagram insights (reach, follower trend)\n"
            f"3. Check Bandcamp sales CSV\n"
            f"4. Pull Google Analytics traffic for lrrecords.com.au\n"
            f"5. Monitor X for artist name mentions\n"
            f"6. Identify the top 3 opportunities this week "
            f"(e.g. playlist pitch window, Doom Charts submission, content angle)\n"
            f"7. Draft one Doom Charts submission if there is an active release — queue for CEO\n"
            f"8. Queue one Instagram post idea for CEO approval"
        ),
        expected_output=(
            "JSON report containing: {spotify_data, instagram_insights, bandcamp_summary, "
            "ga_traffic, x_mentions, top_3_opportunities, actions_queued_for_approval}"
        ),
        agent=internet_agent,
    )
    return Crew(agents=[internet_agent], tasks=[task], process=Process.sequential, verbose=True)
```

---

## Step 3 — New Routes in `label/web.py`

Add these routes to your existing `label_bp` blueprint in `label/web.py`:

```python
# Add at top of label/web.py (after existing imports)
import threading
import datetime
from crews.base_crew import get_pending_approvals, approve_task

# In-memory job tracker — swap for Redis in production
_crew_jobs: dict = {}


@label_bp.route("/api/mission", methods=["POST"])
def api_mission():
    """
    CEO fires a high-level mission brief.
    CrewAI crew runs asynchronously. Returns job_id for polling.
    """
    data         = request.json or {}
    slug         = data.get("artist_slug") or ""
    mission      = data.get("mission", "")
    release_title = data.get("release_title", "")

    if not slug:
        return jsonify({"error": "artist_slug required"}), 400

    from crews.label_crew import build_release_campaign_crew

    job_id = f"mission_{slug}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    _crew_jobs[job_id] = {
        "status": "running", "slug": slug, "mission": mission, "result": None, "started_at": datetime.datetime.utcnow().isoformat()
    }

    def run_crew():
        try:
            crew   = build_release_campaign_crew(slug, release_title or mission)
            result = crew.kickoff()
            _crew_jobs[job_id]["status"] = "complete"
            _crew_jobs[job_id]["result"] = str(result)
        except Exception as e:
            _crew_jobs[job_id]["status"] = "error"
            _crew_jobs[job_id]["result"] = str(e)

    threading.Thread(target=run_crew, daemon=True).start()
    return jsonify({"job_id": job_id, "status": "running"})


@label_bp.route("/api/mission/<job_id>", methods=["GET"])
def api_mission_status(job_id):
    """Poll mission status."""
    job = _crew_jobs.get(job_id, {"error": "Job not found"})
    return jsonify(job)


@label_bp.route("/api/mission/list", methods=["GET"])
def api_mission_list():
    """List all missions."""
    return jsonify(list(_crew_jobs.values()))


@label_bp.route("/api/ceo/queue", methods=["GET"])
def api_approval_queue():
    """Get all pending CEO approvals."""
    return jsonify(get_pending_approvals())


@label_bp.route("/api/ceo/approve/<task_id>", methods=["POST"])
def api_approve_task(task_id):
    """
    Approve or reject a queued agent action.
    If approved, fires the action via n8n (for mass emails, social posts, etc.)
    """
    data     = request.json or {}
    approved = data.get("approved", False)
    note     = data.get("note", "")
    result   = approve_task(task_id, approved, note)

    if result.get("error"):
        return jsonify(result), 404

    # If approved, execute the action via n8n
    if approved:
        action = result.get("action")
        payload = result.get("payload", {})

        n8n_action_map = {
            "send_mass_email":       "send_email_campaign",
            "publish_public_content": "publish_blog_post",
            "post_social_media":     "post_social_media",
            "press_outreach":        "send_email_campaign",
        }

        n8n_workflow = n8n_action_map.get(action)
        if n8n_workflow:
            try:
                import os, requests as req
                n8n_base = os.getenv("N8N_BASE_URL", "http://localhost:5678")
                req.post(
                    f"{n8n_base}/webhook/maestro-approved-action",
                    json={"workflow": n8n_workflow, "payload": payload},
                    timeout=5
                )
            except Exception as e:
                logging.warning(f"n8n trigger failed after approval: {e}")

    return jsonify(result)
```

---

## Step 4 — CEO Dashboard UI (add to `templates/index.html`)

Paste this block inside `#view-dashboard`, after your stats row:

```html
<!-- ══ CEO MISSION BRIEF PANEL ══ -->
<div style="background:var(--surface);border:1px solid var(--border);
            border-left:3px solid var(--cyan);border-radius:10px;
            padding:22px;margin-bottom:22px;">
  <div style="font-size:.65rem;font-weight:700;letter-spacing:.1em;
              text-transform:uppercase;color:var(--cyan);margin-bottom:12px;">
    🎯 Mission Brief — CEO Command Centre
  </div>
  <div style="display:grid;grid-template-columns:1fr 160px auto;gap:10px;margin-bottom:10px;">
    <textarea id="mission-input"
      style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
             color:var(--white);font-family:var(--mono);font-size:.82rem;
             padding:10px;resize:none;height:64px;outline:none;"
      placeholder="e.g. Run full release campaign for Aria Velvet — Neon Letters, dropping April 18"></textarea>
    <input id="mission-slug" type="text"
      style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
             color:var(--white);font-family:var(--mono);font-size:.82rem;padding:10px;"
      placeholder="artist_slug">
    <button onclick="fireMission()"
      style="background:linear-gradient(135deg,var(--cyan-dim),#005f65);
             border:1px solid var(--cyan-dim);border-radius:8px;color:var(--white);
             font-family:var(--mono);font-size:.78rem;font-weight:700;
             padding:0 20px;cursor:pointer;white-space:nowrap;">
      ▶ FIRE MISSION
    </button>
  </div>
  <div id="mission-status" style="font-family:var(--mono);font-size:.74rem;
       color:var(--muted);min-height:18px;"></div>
</div>

<!-- ══ CEO APPROVAL QUEUE ══ -->
<div style="background:var(--surface);border:1px solid var(--border);
            border-left:3px solid var(--yellow);border-radius:10px;
            padding:22px;margin-bottom:22px;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
    <div style="font-size:.65rem;font-weight:700;letter-spacing:.1em;
                text-transform:uppercase;color:var(--yellow);">
      ⏳ CEO Approval Queue
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
      <span id="queue-count" style="font-family:var(--mono);font-size:.7rem;
            background:rgba(245,200,66,.1);border:1px solid rgba(245,200,66,.3);
            border-radius:999px;padding:2px 10px;color:var(--yellow);"></span>
      <button onclick="loadApprovalQueue()"
        style="background:none;border:1px solid var(--border);border-radius:6px;
               color:var(--muted);font-size:.7rem;padding:4px 10px;cursor:pointer;">
        ↺
      </button>
    </div>
  </div>
  <div id="approval-queue">
    <div style="color:var(--muted);font-size:.8rem;padding:8px 0;">Loading...</div>
  </div>
</div>

<script>
// ── Mission Brief ──────────────────────────────────────────────────────
async function fireMission() {
  const mission = document.getElementById('mission-input').value.trim();
  const slug    = document.getElementById('mission-slug').value.trim() || STATE.slug;
  const statusEl = document.getElementById('mission-status');

  if (!mission) { toast('Enter a mission brief', 'err'); return; }
  if (!slug)    { toast('Select an artist or enter a slug', 'err'); return; }

  statusEl.innerHTML = '🚀 <span style="color:var(--cyan)">Launching CrewAI crew...</span>';

  const resp = await fetch(API_PREFIX + '/api/mission', {
    method:  'POST',
    headers: {'Content-Type': 'application/json'},
    body:    JSON.stringify({ artist_slug: slug, mission, release_title: mission })
  });
  const data = await resp.json();

  if (data.job_id) {
    pollMissionStatus(data.job_id, statusEl);
  } else {
    statusEl.textContent = '❌ Launch failed: ' + JSON.stringify(data);
  }
}

function pollMissionStatus(jobId, statusEl) {
  statusEl.innerHTML = `⏳ Job: <span style="color:var(--cyan);font-family:var(--mono)">${jobId}</span> — running...`;
  const iv = setInterval(async () => {
    const r    = await fetch(API_PREFIX + '/api/mission/' + jobId);
    const data = await r.json();
    if (data.status === 'complete') {
      clearInterval(iv);
      statusEl.innerHTML = `✅ Mission complete — <span style="color:var(--yellow)">check Approval Queue for tasks needing sign-off</span>`;
      loadApprovalQueue();
      toast('Mission complete!', 'ok');
    } else if (data.status === 'error') {
      clearInterval(iv);
      statusEl.innerHTML = `❌ Error: ${data.result}`;
    }
  }, 3000);
}

// ── Approval Queue ─────────────────────────────────────────────────────
async function loadApprovalQueue() {
  const r     = await fetch(API_PREFIX + '/api/ceo/queue');
  const tasks = await r.json();
  const el    = document.getElementById('approval-queue');
  const countEl = document.getElementById('queue-count');

  countEl.textContent = tasks.length ? `${tasks.length} pending` : '';

  if (!tasks.length) {
    el.innerHTML = '<div style="color:var(--muted);font-size:.8rem;padding:4px 0;">✅ No pending approvals</div>';
    return;
  }

  const actionIcons = {
    send_mass_email: '📧', publish_public_content: '📝',
    post_social_media: '📱', press_outreach: '📰',
    mint_nft: '🔷', spend_money: '💰',
    bulk_crm_update: '👥', orchard_submission: '🎵',
    spotify_playlist_pitch: '🎧',
  };

  el.innerHTML = tasks.map(t => `
    <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
                padding:12px 14px;margin-bottom:8px;
                display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:start;">
      <div>
        <div style="font-size:.76rem;font-weight:700;color:var(--white);margin-bottom:3px;">
          ${actionIcons[t.action] || '⚡'} [${t.agent}] ${t.action.replaceAll('_',' ').toUpperCase()}
        </div>
        <div style="font-size:.7rem;color:var(--muted);font-family:var(--mono);
                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:400px;">
          ${JSON.stringify(t.payload).slice(0, 140)}${JSON.stringify(t.payload).length > 140 ? '…' : ''}
        </div>
        <div style="font-size:.64rem;color:#444;margin-top:4px;">${t.queued_at}</div>
      </div>
      <button onclick="actionApproval('${t.task_id}', true)"
        style="background:rgba(0,201,122,.08);border:1px solid var(--green);
               border-radius:6px;color:var(--green);padding:7px 16px;
               font-size:.76rem;font-weight:700;cursor:pointer;white-space:nowrap;">
        ✓ Approve
      </button>
      <button onclick="actionApproval('${t.task_id}', false)"
        style="background:rgba(232,69,69,.08);border:1px solid var(--red);
               border-radius:6px;color:var(--red);padding:7px 16px;
               font-size:.76rem;font-weight:700;cursor:pointer;white-space:nowrap;">
        ✗ Reject
      </button>
    </div>`).join('');
}

async function actionApproval(taskId, approved) {
  await fetch(API_PREFIX + '/api/ceo/approve/' + taskId, {
    method:  'POST',
    headers: {'Content-Type': 'application/json'},
    body:    JSON.stringify({ approved, note: '' })
  });
  toast(approved ? '✅ Approved — executing via n8n' : '✗ Rejected', approved ? 'ok' : 'err');
  setTimeout(loadApprovalQueue, 500);
}

// Auto-load and auto-refresh
document.addEventListener('DOMContentLoaded', () => {
  loadApprovalQueue();
  setInterval(loadApprovalQueue, 30000);
});
</script>
```

---

## Step 5 — Extend `webhook_server.py` for EasyFunnels Events

```python
# Add to webhook_server.py

import requests as _req

# ── Inbound: EasyFunnels → n8n → Maestro ──────────────────────────────────────

@app.route("/webhook/easyfunnels/crm-update", methods=["POST"])
def ef_crm_update():
    """EasyFunnels CRM contact created or updated → log to BRIDGE."""
    data    = request.json or {}
    contact = data.get("contact", {})
    slug    = contact.get("custom_field_artist_slug")  # [verify: EasyFunnels custom field name]
    if slug:
        maestro_url = os.getenv("MAESTRO_BASE_URL", "http://localhost:8080")
        _req.post(f"{maestro_url}/label/api/checkin/{slug}",
                  json={"note": f"EasyFunnels CRM updated: {contact.get('email', '')}"}, timeout=5)
    return jsonify({"received": True, "slug": slug})


@app.route("/webhook/easyfunnels/order", methods=["POST"])
def ef_store_order():
    """EasyFunnels store order received → queue for ATLAS revenue tracking."""
    data = request.json or {}
    _save_to_queue("store_order", data)
    return jsonify({"received": True})


@app.route("/webhook/easyfunnels/appointment", methods=["POST"])
def ef_appointment():
    """EasyFunnels appointment booked → trigger SESSION agent."""
    data        = request.json or {}
    maestro_url = os.getenv("MAESTRO_BASE_URL", "http://localhost:8080")
    _req.post(f"{maestro_url}/studio/run/session", json={
        "session_name": data.get("title", "New Booking"),
        "artist":       data.get("contact_name", ""),
        "session_date": data.get("date", ""),
        "start_time":   data.get("start_time", ""),
        "end_time":     data.get("end_time", ""),
        "status":       "tentative",
        "notes":        data.get("notes", ""),
    }, timeout=10)
    return jsonify({"received": True})


@app.route("/webhook/maestro-approved-action", methods=["POST"])
def handle_approved_action():
    """
    Called by n8n AFTER CEO approves a task.
    Routes the approved action to the correct EasyFunnels endpoint.
    """
    data     = request.json or {}
    workflow = data.get("workflow")
    payload  = data.get("payload", {})
    logging.info(f"Executing approved action: {workflow} — {payload}")
    # n8n handles the actual EasyFunnels API call after receiving this
    return jsonify({"executing": workflow, "payload": payload})


# ── Outbound helper: Maestro → n8n ────────────────────────────────────────────

def trigger_n8n_workflow(workflow_name: str, payload: dict) -> dict:
    """Fire an n8n workflow by name. Returns n8n response."""
    n8n_base = os.getenv("N8N_BASE_URL", "http://localhost:5678")
    webhook_map = {
        "send_email_campaign":  f"{n8n_base}/webhook/ef-send-campaign",
        "update_crm_contact":   f"{n8n_base}/webhook/ef-crm-update",
        "publish_blog_post":    f"{n8n_base}/webhook/ef-blog-publish",
        "post_social_media":    f"{n8n_base}/webhook/social-post",
    }
    url = webhook_map.get(workflow_name)
    if not url:
        return {"error": f"No n8n workflow registered for: {workflow_name}"}
    try:
        r = _req.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def _save_to_queue(event_type: str, data: dict):
    from pathlib import Path
    from datetime import datetime, timezone
    q_dir = Path("data/n8n_queue")
    q_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    (q_dir / f"{event_type}_{ts}.json").write_text(
        json.dumps({"type": event_type, "data": data, "ts": ts}, indent=2)
    )
```
