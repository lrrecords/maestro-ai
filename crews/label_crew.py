# crews/label_crew.py
"""
CrewAI crew for the Label department.
Wraps existing Maestro agents (BRIDGE, VINYL, ECHO, SAGE) as CrewAI role-playing agents.
Each agent's tools call the existing Maestro Flask endpoints — no duplication of logic.
"""
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from crews.base_crew import queue_for_approval
import requests, os, json


MAESTRO_BASE = os.getenv("MAESTRO_BASE_URL", "http://localhost:8080")
MAESTRO_TOKEN = (os.getenv("MAESTRO_TOKEN") or "").strip()


def _auth_headers() -> dict:
    if not MAESTRO_TOKEN:
        return {}
    return {"X-MAESTRO-TOKEN": MAESTRO_TOKEN}


def _make_crew_llm() -> LLM:
    """
    Build a crewai.LLM instance from environment variables.

    Supported providers (via LLM_PROVIDER env var):
      - ollama  (default): uses OLLAMA_BASE_URL + OLLAMA_MODEL
      - openai           : uses OPENAI_API_KEY
      - anthropic        : uses ANTHROPIC_API_KEY + ANTHROPIC_MODEL
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        return LLM(
            model=f"ollama/{model}",
            base_url=base_url,
            api_key="ollama",
        )

    if provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
        return LLM(
            model=f"anthropic/{model}",
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        )

    # openai / default
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return LLM(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )


# ─── Tools ────────────────────────────────────────────────────────────────────

@tool("Run BRIDGE health check for an artist")
def run_bridge(artist_slug: str) -> str:
    """
    Run BRIDGE agent to assess artist relationship health score and draft a check-in.
    Returns health score (0-100), trend, and a personalised check-in message draft.
    """
    r = requests.get(
        f"{MAESTRO_BASE}/label/api/artist/{artist_slug}",
        headers=_auth_headers(),
        timeout=30,
    )
    data = r.json()
    bridge_output = data.get("outputs", {}).get("bridge", {})
    return json.dumps(bridge_output, indent=2) if bridge_output else f"No BRIDGE data for {artist_slug}. Run BRIDGE agent first."


@tool("Run VINYL release checklist for an artist")
def run_vinyl(artist_slug: str) -> str:
    """
    Generate a complete release checklist for the artist's current project.
    Includes pre-production, distribution metadata, marketing, and post-release phases.
    """
    r = requests.get(
        f"{MAESTRO_BASE}/label/api/stream/vinyl/{artist_slug}",
        headers=_auth_headers(),
        stream=True,
        timeout=120,
    )
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
    r = requests.get(
        f"{MAESTRO_BASE}/label/api/artist/{artist_slug}",
        headers=_auth_headers(),
        timeout=15,
    )
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

def _make_agents(llm: LLM):
    """Instantiate all label CrewAI agents with the given LLM."""
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
        llm=llm,
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
        llm=llm,
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
        llm=llm,
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
        llm=llm,
        verbose=True,
        allow_delegation=True,
    )

    return bridge_agent, vinyl_agent, echo_agent, sage_agent


# ─── Crew Builders ────────────────────────────────────────────────────────────

def build_release_campaign_crew(artist_slug: str, release_title: str) -> Crew:
    """
    Full release campaign crew: VINYL → ECHO → BRIDGE → SAGE
    Use for: new single/EP/album release preparation
    """
    llm = _make_crew_llm()
    bridge_agent, vinyl_agent, echo_agent, sage_agent = _make_agents(llm)

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

    from datetime import date
    today = date.today().isoformat()
    task_content = Task(
        description=(
            f"Using the release checklist context, build a 14-day content calendar "
            f"for '{artist_slug}' releasing '{release_title}'. "
            f"Start the calendar from today ({today}) and ensure all dates are in the next 2 weeks (no past dates). "
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
    llm = _make_crew_llm()
    bridge_agent, _, _, sage_agent = _make_agents(llm)

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
