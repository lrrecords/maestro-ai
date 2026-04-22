from flask import (
    Blueprint, render_template, request, jsonify, Response,
    stream_with_context, current_app, session, redirect, url_for, abort
)
import datetime
import logging
import threading
import time
import json
import os
import requests
import pathlib
from pathlib import Path
from functools import wraps
import base64
import json as _json
from crews.base_crew import get_pending_approvals, approve_task
from core.telegram_utils import send_telegram_message

label_bp = Blueprint("label", __name__)

# --- CONFIG AND PATH CONSTANTS ---
ROOT        = Path(__file__).parent.parent          # maestro-ai/
TEMPLATES   = ROOT / "templates"
STATIC      = ROOT / "static"
DATA        = ROOT / "data"
ARTISTS_DIR = DATA / "artists"
BRIDGE_DIR  = DATA / "bridge"
AGENTS      = ["vinyl", "echo", "atlas", "forge", "sage", "bridge"]

# --- Configurable roles/permissions (could be loaded from DB or file) ---
ROLE_CONFIG = {
    "admin": {"inherits": ["ceo", "user"], "permissions": ["can_approve", "can_edit", "can_view"]},
    "ceo":   {"inherits": ["user"], "permissions": ["can_approve", "can_view"]},
    "user":  {"inherits": [], "permissions": ["can_view"]},
}


def _load_role_config():
    """Placeholder for loading role config from file or DB."""
    return ROLE_CONFIG


def _get_jwt_payload():
    """Extract JWT payload from Authorization header if present."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        try:
            payload_b64 = token.split(".")[1]
            payload_b64 += '=' * (-len(payload_b64) % 4)
            payload = base64.urlsafe_b64decode(payload_b64)
            return _json.loads(payload)
        except Exception:
            return {}
    return {}


def get_user_role():
    """
    Returns the user's role. Checks JWT, session, or header.
    In production this should check session, JWT, or user DB.
    """
    # 1. JWT claim
    payload = _get_jwt_payload()
    if "role" in payload:
        return payload["role"].lower()
    # 2. Session
    if session.get("role"):
        return session["role"]
    # 3. Custom header for dev/testing
    role = request.headers.get("X-MAESTRO-ROLE")
    if role:
        return role.lower()
    return "user"


def get_user_permissions(role=None):
    """Return all permissions for a role, including inherited."""
    config = _load_role_config()
    role = role or get_user_role()
    perms = set(config.get(role, {}).get("permissions", []))
    for parent in config.get(role, {}).get("inherits", []):
        perms.update(get_user_permissions(parent))
    return perms


# --- ROLE/PERMISSION DECORATOR (supports permission kwarg) ---
def require_role_with_permission(*roles, permission=None):
    """
    Decorator to require a user role or permission for a route.
    Usage: @require_role_with_permission("ceo", permission="can_approve")
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_role = get_user_role()
            user_perms = get_user_permissions(user_role)
            config = _load_role_config()
            allowed = user_role in roles or any(
                r in roles for r in config.get(user_role, {}).get("inherits", [])
            )
            if not allowed and roles:
                logging.warning(f"Permission denied: role '{user_role}' not in {roles}")
                return jsonify({"ok": False, "error": f"Forbidden: {', '.join(roles)} role required"}), 403
            if permission and permission not in user_perms:
                logging.warning(f"Permission denied: role '{user_role}' lacks permission '{permission}'")
                return jsonify({"ok": False, "error": f"Forbidden: '{permission}' permission required"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def require_role(*roles):
    """
    Decorator to require a user role for a route.
    Usage: @require_role("ceo", "admin")
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_role = get_user_role()
            if user_role not in roles:
                return jsonify({"ok": False, "error": f"Forbidden: {', '.join(roles)} role required"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def _is_authorized() -> bool:
    if session.get("authenticated"):
        return True
    token = (os.getenv("MAESTRO_TOKEN") or "").strip()
    if not token:
        return False
    auth_header = (request.headers.get("Authorization") or "").strip()
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip() == token
    return (request.headers.get("X-MAESTRO-TOKEN") or "").strip() == token


@label_bp.before_request
def require_auth():
    if _is_authorized():
        return None
    if request.path.startswith("/label/api/"):
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    return redirect(url_for("login_page", next=request.path))


# --- DASHBOARD INDEX ---
@label_bp.route("/")
def index():
    prefix = current_app.config.get("LABEL_URL_PREFIX", "/label")
    return render_template("index.html", api_prefix=prefix)


@label_bp.route("/api/session")
def api_session():
    """Expose current user's role and permissions for frontend UI logic."""
    role = get_user_role()
    permissions = list(get_user_permissions(role))
    return jsonify({
        "role": role,
        "permissions": permissions,
        "ok": True
    })


# --- DASHBOARD DATA ---
@label_bp.route("/api/dashboard")
def api_dashboard():
    return jsonify(build_dashboard_rows())


@label_bp.route("/api/artist/<slug>")
def api_artist(slug):
    raw_artist_data = load_artist(slug)
    if not raw_artist_data:
        return jsonify({"error": "Artist not found"}), 404

    bridge = get_latest_output(slug, "bridge")
    payload = {
        "profile": raw_artist_data,
        "score":   parse_bridge_score(bridge),
        "trend":   parse_bridge_trend(bridge),
        "status":  score_to_status(parse_bridge_score(bridge)),
        "history": get_bridge_history(slug),
        "outputs": {ag: get_latest_output(slug, ag) for ag in AGENTS}
    }
    return jsonify(payload)


# --- AGENT PROMPT BUILDER ---
def build_agent_prompt(agent, artist):
    name = artist.get('artist_info', {}).get('name') or artist.get('artist_name', '(unknown artist)')
    release = artist.get('upcoming_release', {}).get('title', '(no title)')
    release_date = artist.get('upcoming_release', {}).get('date', '') or 'TBD'
    today = datetime.date.today().isoformat()

    example_json = f'''{{
  "artist": "{name}",
  "project": "{release}",
  "project_type": "Release",
  "release_date": "{release_date}",
  "generated": "{today}",
  "phases": [
    {{
      "phase": "Pre-Production",
      "timeline": "8 weeks before release date",
      "tasks": [
        {{
          "task": "Identify and finalize track list for the single",
          "priority": "HIGH",
          "status": "PENDING",
          "notes": "Must happen 4 months in advance to align with distribution schedule"
        }},
        {{
          "task": "Finalize artwork, including cover art, lyric sheets, and album concept design",
          "priority": "MEDIUM",
          "status": "PENDING",
          "notes": "Artwork needs to be approved by label and distributors 3 weeks before release date"
        }}
      ]
    }},
    {{
      "phase": "Distribution & Metadata",
      "timeline": "4 weeks before release date",
      "tasks": [
        {{
          "task": "Complete digital metadata for The Orchard, including song titles, artist names, and track IDs",
          "priority": "HIGH",
          "status": "PENDING",
          "notes": "Needs to be completed 1 month in advance of release date"
        }},
        {{
          "task": "Submit single artwork and metadata files to The Orchard for digital distribution",
          "priority": "MEDIUM",
          "status": "PENDING",
          "notes": "Artwork approval process can take up to 2 weeks, so must be submitted early"
        }}
      ]
    }},
    {{
      "phase": "Marketing & Promo",
      "timeline": "3 weeks before release date",
      "tasks": [
        {{
          "task": "Develop and distribute pre-release singles for radio airplay and playlist submissions",
          "priority": "HIGH",
          "status": "PENDING",
          "notes": "Must be submitted 1 month in advance of release date"
        }},
        {{
          "task": "Create and execute a social media campaign with artist interviews, behind-the-scenes content, and exclusive sneak peeks",
          "priority": "MEDIUM",
          "status": "IN_PROGRESS",
          "notes": "Focus on generating buzz among the target audience for maximum impact"
        }}
      ]
    }},
    {{
      "phase": "Release Day",
      "timeline": "2 weeks before release date (day of release)",
      "tasks": [
        {{
          "task": "Coordinate with The Orchard for final distribution setup and activation",
          "priority": "MEDIUM",
          "status": "IN_PROGRESS",
          "notes": "Ensure all digital platforms are live and ready to go by the day of release"
        }},
        {{
          "task": "Prepare promotional materials such as posters, flyers, and social media graphics for physical releases (if applicable)",
          "priority": "LOW",
          "status": "PENDING",
          "notes": "Not required if only digital distribution is planned"
        }}
      ]
    }},
    {{
      "phase": "Post-Release",
      "timeline": "1 week after release date",
      "tasks": [
        {{
          "task": "Analyze pre-release metrics and adjust marketing strategy for future releases (if applicable)",
          "priority": "LOW",
          "status": "PENDING",
          "notes": "Based on data from the current release to optimize upcoming strategies"
        }},
        {{
          "task": "Send out post-release surveys to collect feedback from listeners/patrons",
          "priority": "MEDIUM",
          "status": "IN_PROGRESS",
          "notes": "Helps gauge listener satisfaction and identify areas for improvement in future releases"
        }}
      ]
    }}
  ],
  "critical_path": [
    "Finalize track list and artwork by the end of Phase Pre-Production"
  ],
  "immediate_actions": [
    "Submit all digital metadata to The Orchard no later than 4 weeks before release date"
  ],
  "blockers": [
    "No known blockers at this time"
  ],
  "recommendations": [
    "Plan press outreach 2 weeks before release.",
    "Engage fans with exclusive behind-the-scenes content.",
    "Double-check distributor deadline alignment."
  ]
}}'''
    prompt = (
        f"You are the {agent.upper()} release operations agent for {name}."
        f" The upcoming release is '{release}' on {release_date}."
        "\nReply ONLY with one valid JSON object (no preamble, no explanation, no markdown/code block fences), using the following format:"
        f"\n{example_json}"
        "\nAll keys and string values must use double quotes."
        "\nOutput must be strictly valid JSON, parseable by Python's json.loads, and must include all the fields and structure in the sample (even if they must be empty)."
        "\nPopulate recommendations with 2-3 actionable tips for this artist/release. Absolutely do not add any commentary, blank lines, or prefix/suffix-just pure JSON."
    )
    return prompt


def extract_json_from_llm(raw):
    """Strip code block markup and whitespace from LLM output."""
    s = raw.strip()
    if s.startswith("```json"):
        s = s[len("```json"):]
    if s.startswith("```"):
        s = s[len("```"):]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def validate_release_json(obj):
    """Schema validator stub — expand to real schema as needed."""
    top_keys = ["artist", "phases", "critical_path", "immediate_actions", "blockers", "recommendations"]
    for key in top_keys:
        if key not in obj:
            raise ValueError(f"Missing top-level key: {key}")
    return True


def save_agent_output(agent, artist_slug, output_object, data_dir="data"):
    now = datetime.date.today().isoformat()
    dated_filename = f"{data_dir}/{agent}/{artist_slug}_checklist_{now}.json"
    latest_filename = f"{data_dir}/{agent}/{artist_slug}_checklist_latest.json"
    pathlib.Path(f"{data_dir}/{agent}").mkdir(parents=True, exist_ok=True)
    with open(dated_filename, "w", encoding="utf-8") as f:
        json.dump(output_object, f, ensure_ascii=False, indent=2)
    with open(latest_filename, "w", encoding="utf-8") as f:
        json.dump(output_object, f, ensure_ascii=False, indent=2)
    return dated_filename, latest_filename


def handle_agent_llm_output(agent, artist, artist_slug, raw_llm_output):
    try:
        cleaned = extract_json_from_llm(raw_llm_output)
        obj = json.loads(cleaned)
        validate_release_json(obj)
        save_agent_output(agent, artist_slug, obj)
        return obj
    except Exception as ex:
        print("LLM output parse/validate failed:", ex)
        return None


# --- AGENT STREAM ROUTE ---
@label_bp.route("/api/stream/<agent>/<slug>")
def api_stream(agent, slug):
    artist = load_artist(slug)
    if not artist:
        def error_stream():
            part = '{"error": "Artist not found"}'
            print("YIELDING TO FRONTEND:", part)
            yield f'data: {part}\n\n'
        return Response(stream_with_context(error_stream()), mimetype="text/event-stream")

    prompt = build_agent_prompt(agent, artist)

    ollama_url     = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    ollama_model   = os.environ.get('OLLAMA_MODEL', 'qwen2.5:3b')
    ollama_timeout = int(os.environ.get('OLLAMA_TIMEOUT_SECONDS', '1800'))
    generate_url   = f"{ollama_url}/api/generate"

    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": True
    }

    def generate():
        buffer = ""
        try:
            with requests.post(generate_url, json=payload, stream=True, timeout=ollama_timeout) as r:
                for line in r.iter_lines():
                    if not line:
                        continue
                    part = line.decode()
                    data = json.loads(part)
                    if "response" in data:
                        buffer += data["response"]
                    if data.get("done"):
                        json_buffer = buffer.strip()
                        try:
                            cleaned = extract_json_from_llm(json_buffer)
                            print("DEBUG: Cleaned LLM output:\n", cleaned)
                            obj = json.loads(cleaned)
                            validate_release_json(obj)
                            dated_fn, latest_fn = save_agent_output(agent, slug, obj)
                            yield f'data: {json.dumps({"result": obj, "done": True})}\n\n'
                            print(f"Agent output saved to: {dated_fn} and {latest_fn}")
                        except Exception as e:
                            print("PARSE ERROR DEBUG: raw json_buffer=\n", repr(json_buffer))
                            print("PARSE ERROR EXCEPTION:", e)
                            err_info = {
                                "error": "Failed to parse or save JSON from LLM",
                                "output": json_buffer,
                                "exception": str(e),
                                "done": True
                            }
                            yield f'data: {json.dumps(err_info)}\n\n'
                        yield 'data: [DONE]\n\n'
                        return
        except Exception as e:
            err_info = {
                "error": "LLM error: " + str(e),
                "done": True
            }
            print("Stream error:", e)
            yield f'data: {json.dumps(err_info)}\n\n'
            yield 'data: [DONE]\n\n'

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


# --- CHECK-IN ---
@label_bp.route("/api/checkin/<slug>", methods=["POST"])
def api_checkin(slug):
    if not slug or slug == "undefined":
        return jsonify({"success": False, "error": "No artist selected or slug undefined."}), 400
    note = (request.json or {}).get("note", "")
    ts = datetime.datetime.utcnow().isoformat()
    logging.info("Check-in logged for %s: %s", slug, note)
    return jsonify({"success": True, "output": f"Check-in saved at {ts}"})


# --- WEBHOOK ---
@label_bp.route("/api/webhook/<slug>", methods=["POST"])
def api_webhook(slug):
    if not slug or slug == "undefined":
        return jsonify({"sent": False, "error": "No artist selected or slug undefined."}), 400
    webhook_url = (os.getenv("WEBHOOK_URL") or "").strip()
    if not webhook_url:
        return jsonify({"sent": False, "error": "WEBHOOK_URL not configured."}), 503
    payload = {
        "artist":    slug_to_name(slug),
        "slug":      slug,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "source":    "maestro-web-ui",
    }
    try:
        import requests as req_lib
        r = req_lib.post(webhook_url, json=payload, timeout=6)
        return jsonify({"sent": True, "http_status": r.status_code})
    except Exception as e:
        logging.warning(f"Webhook call failed: {e}")
        return jsonify({
            "sent": False,
            "error": "Webhook feature temporarily unavailable (no endpoint reachable). This does not affect dashboard operation."
        }), 200


# --- HELPERS ---
def get_artist_slugs():
    if not ARTISTS_DIR.exists():
        return []
    return [f.stem for f in sorted(ARTISTS_DIR.glob("*.json"))]


def load_artist(slug):
    path = ARTISTS_DIR / f"{slug}.json"
    if not path.exists():
        print(f"DEBUG: File does not exist at {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError as e:
        print(f"CRITICAL: {slug}.json has a syntax error: {e}")
        return None
    except Exception as e:
        print(f"CRITICAL: Could not read {slug}.json: {e}")
        return None


def slug_to_name(slug):
    artist = load_artist(slug)
    if artist:
        return artist.get("artist_info", {}).get("name", slug)
    return slug.replace("_", " ").title()


def get_latest_output(slug, agent):
    agent_dir = DATA / agent
    if not agent_dir.exists():
        return None
    files = sorted(agent_dir.glob(f"{slug}_*.json"), reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_bridge_score(bridge_data):
    if not bridge_data:
        return None
    health = bridge_data.get("health_assessment", bridge_data.get("health", {}))
    score = health.get("overall_score", health.get("score"))
    return int(score) if score is not None else None


def parse_bridge_trend(bridge_data):
    if not bridge_data:
        return "—"
    health = bridge_data.get("health_assessment", bridge_data.get("health", {}))
    return health.get("trend", "—")


def score_to_status(score):
    if score is None:
        return "no-data"
    if score >= 70:
        return "good"
    if score >= 40:
        return "monitor"
    return "critical"


def parse_file_timestamp(slug, filepath):
    try:
        suffix = filepath.stem[len(slug) + 1:]
        dt = datetime.datetime.strptime(suffix, "%Y%m%d_%H%M%S")
        return dt.strftime("%d %b %Y %H:%M")
    except Exception:
        return "—"


def get_bridge_history(slug):
    if not BRIDGE_DIR.exists():
        return []
    history = []
    for f in sorted(BRIDGE_DIR.glob(f"{slug}_*.json")):
        try:
            data  = json.loads(f.read_text(encoding="utf-8"))
            score = parse_bridge_score(data)
            if score is None:
                continue
            suffix = f.stem[len(slug) + 1:]
            try:
                dt = datetime.datetime.strptime(suffix, "%Y%m%d_%H%M%S")
                ts = dt.strftime("%d %b %H:%M")
            except Exception:
                ts = suffix
            history.append({"timestamp": ts, "score": score})
        except Exception:
            continue
    return history


def build_dashboard_rows():
    rows = []
    for slug in get_artist_slugs():
        artist = load_artist(slug)
        if not artist:
            continue
        name    = artist.get("artist_info", {}).get("name", slug)
        genre   = artist.get("artist_info", {}).get("genre", "—")
        release = artist.get("upcoming_release", {}).get("title", "—")
        bridge  = get_latest_output(slug, "bridge")
        score   = parse_bridge_score(bridge)
        trend   = parse_bridge_trend(bridge)
        status  = score_to_status(score)
        # Find last_run from bridge files
        last_run  = "—"
        agent_dir = DATA / "bridge"
        files     = sorted(agent_dir.glob(f"{slug}_*.json"), reverse=True)
        if files:
            last_run = parse_file_timestamp(slug, files[0])
        rows.append({
            "slug":     slug,
            "name":     name,
            "genre":    genre,
            "release":  release,
            "score":    score,
            "trend":    trend,
            "status":   status,
            "last_run": last_run,
        })
    order = {"critical": 0, "monitor": 1, "good": 2, "no-data": 3}
    rows.sort(key=lambda r: (order.get(r["status"], 9), -(r["score"] if r["score"] is not None else -1)))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# CrewAI Mission & CEO Approval Routes
# ─────────────────────────────────────────────────────────────────────────────

from core.job_store import JobStore
job_store = JobStore()


# List all missions/jobs endpoint
@label_bp.route("/api/mission/list", methods=["GET"])
def api_mission_list():
    """List all missions/jobs."""
    jobs = job_store.all_jobs()
    return jsonify({"ok": True, "jobs": jobs})


@label_bp.route("/api/mission", methods=["POST"])
def api_mission():
    """
    Create a new mission and launch CrewAI crew asynchronously.
    ---
    tags:
      - Mission
    parameters:
      - name: body
        in: body
        required: true
        description: Mission payload.
        schema:
          type: object
          required:
            - artist_slug
          properties:
            artist_slug:
              type: string
            mission:
              type: string
            release_title:
              type: string
    responses:
      200:
        description: Mission created and job started.
      400:
        description: artist_slug required.
    """
    data          = request.json or {}
    slug          = data.get("artist_slug", "")
    mission       = data.get("mission", "")
    release_title = data.get("release_title", "")

    if not slug:
        return jsonify({"error": "artist_slug required"}), 400

    from crews.label_crew import build_release_campaign_crew

    _now = datetime.datetime.now(datetime.timezone.utc)
    now  = _now.isoformat()

    job_id   = f"mission_{slug}_{_now.strftime('%Y%m%d_%H%M%S')}"
    job_data = {
        "job_id":        job_id,
        "status":        "running",
        "slug":          slug,
        "mission":       mission,
        "release_title": release_title,
        "result":        None,
        "created_at":    now,
        "updated_at":    now,
        "finished_at":   None,
        "cancelled":     False,
    }
    job_store.add_job(job_id, job_data)

    # Send Telegram notification for Fire Mission
    try:
        send_telegram_message(
            f"🚀 CEO Fire Mission launched for {slug}!\nMission: {mission}\nRelease: {release_title}"
        )
    except Exception as e:
        print(f"[Telegram Notify Error] {e}")

    def run_crew():
        try:
            job = job_store.get_job(job_id)
            if job and job.get("cancelled"):
                job["status"]      = "cancelled"
                job["result"]      = "Mission cancelled by user."
                job["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                job["updated_at"]  = job["finished_at"]
                job_store.add_job(job_id, job)
                return

            crew           = build_release_campaign_crew(slug, release_title or mission)
            kickoff_output = crew.kickoff()
            result_payload = {
                "mission":       mission,
                "release_title": release_title,
                "output":        str(kickoff_output),
            }
            job = job_store.get_job(job_id)
            if job:
                done_at            = datetime.datetime.now(datetime.timezone.utc).isoformat()
                job["result"]      = result_payload
                job["status"]      = "complete"
                job["finished_at"] = done_at
                job["updated_at"]  = done_at
                job_store.add_job(job_id, job)
        except Exception as e:
            done_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            job     = job_store.get_job(job_id)
            if job:
                job["status"]      = "error"
                job["result"]      = str(e)
                job["finished_at"] = done_at
                job["updated_at"]  = done_at
                job_store.add_job(job_id, job)

    threading.Thread(target=run_crew, daemon=True).start()
    return jsonify({"ok": True, "job_id": job_id, "status": "running"})


@label_bp.route("/api/mission/<job_id>", methods=["GET"])
def api_mission_status(job_id):
    """Poll mission status."""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found"}), 404
    return jsonify({"ok": True, "job": job})


@label_bp.route("/api/mission/<job_id>/cancel", methods=["POST"])
def api_mission_cancel(job_id):
    """Soft-cancel a running mission."""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found"}), 404
    if job.get("status") != "running":
        return jsonify({"ok": False, "error": "Job is not running"}), 409
    now                = datetime.datetime.now(datetime.timezone.utc).isoformat()
    job["status"]      = "cancelled"
    job["finished_at"] = now
    job["updated_at"]  = now
    job["cancelled"]   = True
    job_store.add_job(job_id, job)
    return jsonify({"ok": True, "job": job})


@label_bp.route("/api/mission/<job_id>", methods=["DELETE"])
def api_mission_delete(job_id):
    """Delete / clear a mission record."""
    job = job_store.get_job(job_id)
    if not job:
        return jsonify({"ok": False, "error": "Job not found"}), 404
    job_store.delete_job(job_id)
    return jsonify({"ok": True, "cleared": True, "job_id": job_id})


@label_bp.route("/api/ceo/queue", methods=["GET"])
def api_approval_queue():
    """Get all pending CEO approvals."""
    return jsonify(get_pending_approvals())


@label_bp.route("/api/ceo/approve/<task_id>", methods=["POST"])
@require_role_with_permission("ceo", permission="can_approve")
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

    if approved:
        action  = result.get("action")
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
                n8n_base = os.getenv("N8N_BASE_URL", "http://localhost:5678")
                requests.post(
                    f"{n8n_base}/webhook/maestro-approved-action",
                    json={"workflow": n8n_workflow, "payload": payload},
                    timeout=5,
                )
            except Exception as e:
                logging.warning(f"n8n trigger failed after approval: {e}")

    return jsonify(result)
