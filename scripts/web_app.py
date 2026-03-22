# scripts/web_app.py
import sys
import os
import re
import json
import subprocess
import requests as req_lib
import logging
import time
from pathlib import Path
from datetime import datetime
from functools import wraps
from flask import (
    Flask, Blueprint, render_template, request, session,
    redirect, url_for, jsonify, Response, stream_with_context, current_app,
)
from dotenv import load_dotenv

# --- Paths ---
ROOT        = Path(__file__).parent.parent          # maestro-ai/
TEMPLATES   = ROOT / "templates"
STATIC      = ROOT / "static"
DATA        = ROOT / "data"
ARTISTS_DIR = DATA / "artists"
BRIDGE_DIR  = DATA / "bridge"
AGENTS      = ["vinyl", "echo", "atlas", "forge", "sage", "bridge"]

# --- Config ---
load_dotenv(ROOT / ".env")
MAESTRO_TOKEN = os.getenv("MAESTRO_TOKEN")
PORT          = int(os.getenv("WEB_PORT", 8080))
SECRET_KEY    = os.getenv("SECRET_KEY", os.urandom(24).hex())
WEBHOOK_URL   = os.getenv("WEBHOOK_URL", "http://localhost:5678/webhook/health-update")

# --- Flask Blueprint for LABEL Dashboard ---
# This blueprint contains the "4 department cards" index and related routes.
bp = Blueprint("label", __name__)

# --- ANSI Stripping & Login Required Decorator ---
ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # This relies on 'login_page' being an endpoint name accessible in the main app's context.
        if not session.get("authenticated"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            # Use url_for to dynamically get the login route's URL.
            # It must be named 'login_page' in the main app.
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated

# --- Routes for the 'label' blueprint ---
# In scripts/web_app.py
@bp.route("/")
@login_required
def index():
    # read from app.config instead of an attribute -- THIS IS THE KEY FOR THE FRONT-END
    prefix = current_app.config.get("LABEL_URL_PREFIX", "") 
    return render_template("index.html", api_prefix=prefix)

# Placeholder for other API routes that belong to the LABEL blueprint
# You will need to copy these from your original scripts/web_app.py if they are needed.
# Example:
@bp.route("/api/dashboard")
@login_required
def api_dashboard():
    return jsonify(build_dashboard_rows())
# ... (Copy all other routes that were originally under bp.route) ...

# ------------------------------------------------------------------
# Additional routes required by the front-end
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Additional routes required by the front-end
# ------------------------------------------------------------------
                           

# In scripts/web_app.py
@bp.route("/api/artist/<slug>")
@login_required
def api_artist(slug):
    raw_artist_data = load_artist(slug)
    if not raw_artist_data:
        return jsonify({"error": "Artist not found"}), 404

    bridge = get_latest_output(slug, "bridge")
    
    # We must wrap the JSON in "profile" for the frontend 'Overview' tab
    payload = {
        "profile": raw_artist_data, 
        "score":   parse_bridge_score(bridge),
        "trend":   parse_bridge_trend(bridge),
        "status":  score_to_status(parse_bridge_score(bridge)),
        "history": get_bridge_history(slug),
        "outputs": {ag: get_latest_output(slug, ag) for ag in AGENTS}
    }
    return jsonify(payload)


@bp.route("/api/stream/<agent>/<slug>")
@login_required
def api_stream(agent, slug):
    """Dummy SSE stream; replace with real agent execution."""
    def generate():
        yield f'data: {{"line":"▶ Starting {agent.upper()} for {slug}"}}\n\n'
        for i in range(1, 6):
            time.sleep(0.6)
            yield f'data: {{"line":"Processing step {i}/5..."}}\n\n'
        yield 'data: {"line":"✓ Done","done":true,"ok":true}\n\n'

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream")


@bp.route("/api/checkin/<slug>", methods=["POST"])
@login_required
def api_checkin(slug):
    note = (request.json or {}).get("note", "")
    ts   = datetime.utcnow().isoformat()
    logging.info("Check-in logged for %s: %s", slug, note)
    return jsonify({"success": True, "output": f"Check-in saved at {ts}"})


@bp.route("/api/webhook/<slug>", methods=["POST"])
@login_required
def api_webhook(slug):
    payload = {
        "artist":    slug_to_name(slug),
        "slug":      slug,
        "timestamp": datetime.utcnow().isoformat(),
        "source":    "maestro-web-ui",
    }
    try:
        r = req_lib.post(WEBHOOK_URL, json=payload, timeout=6)
        return jsonify({"sent": True, "http_status": r.status_code})
    except Exception as e:
        logging.exception("Webhook error")
        return jsonify({"sent": False, "error": str(e)}), 500


# --- Data Helper Functions (can be outside create_app as they don't depend on app instance) ---
def get_artist_slugs() -> list:
    if not ARTISTS_DIR.exists(): return []
    return [f.stem for f in sorted(ARTISTS_DIR.glob("*.json"))]

def load_artist(slug: str) -> dict | None:
    path = ARTISTS_DIR / f"{slug}.json"
    if not path.exists():
        print(f"DEBUG: File does not exist at {path}")
        return None
    try:
        # utf-8-sig is the "magic" for Windows text files
        with open(path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError as e:
        print(f"CRITICAL: {slug}.json has a syntax error: {e}")
        return None
    except Exception as e:
        print(f"CRITICAL: Could not read {slug}.json: {e}")
        return None

def slug_to_name(slug: str) -> str:
    artist = load_artist(slug)
    if artist: return artist.get("artist_info", {}).get("name", slug)
    return slug.replace("_", " ").title()

def get_latest_output(slug: str, agent: str) -> dict | None:
    agent_dir = DATA / agent
    if not agent_dir.exists(): return None
    files = sorted(agent_dir.glob(f"{slug}_*.json"), reverse=True)
    if not files: return None
    try: return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception: return None

def parse_bridge_score(bridge_data: dict) -> int | None:
    if not bridge_data:
        return None
    health = bridge_data.get("health_assessment", bridge_data.get("health", {}))
    score = health.get("overall_score", health.get("score"))
    return int(score) if score is not None else None

def parse_bridge_trend(bridge_data: dict) -> str:
    if not bridge_data:
        return "—"
    health = bridge_data.get("health_assessment", bridge_data.get("health", {}))
    return health.get("trend", "—")

def score_to_status(score: int | None) -> str:
    if score is None: return "no-data"
    if score >= 70: return "good"
    if score >= 40: return "monitor"
    return "critical"

def parse_file_timestamp(slug: str, filepath: Path) -> str:
    try:
        suffix = filepath.stem[len(slug) + 1:]
        dt = datetime.strptime(suffix, "%Y%m%d_%H%M%S")
        return dt.strftime("%d %b %Y %H:%M")
    except Exception: return "—"

def get_bridge_history(slug: str) -> list:
    if not BRIDGE_DIR.exists(): return []
    history = []
    for f in sorted(BRIDGE_DIR.glob(f"{slug}_*.json")):
        try:
            data  = json.loads(f.read_text(encoding="utf-8"))
            score = parse_bridge_score(data)
            if score is None: continue
            suffix = f.stem[len(slug) + 1:]
            try:
                dt = datetime.strptime(suffix, "%Y%m%d_%H%M%S")
                ts = dt.strftime("%d %b %H:%M")
            except Exception: ts = suffix
            history.append({"timestamp": ts, "score": score})
        except Exception: continue
    return history

def build_dashboard_rows() -> list:
    print("DEBUG ARTISTS_DIR =", ARTISTS_DIR)
    print("DEBUG artist files =", list(ARTISTS_DIR.glob("*.json")))
    rows = []
    slugs = get_artist_slugs()
    print("DEBUG slugs:", slugs)
    for slug in slugs:
        artist = load_artist(slug)
        print("DEBUG loaded artist:", slug, artist)
        if not artist: continue
        name    = artist.get("artist_info", {}).get("name", slug)
        genre   = artist.get("musical_identity", {}).get("primary_genre", "—")
        release = artist.get("upcoming_release", {}).get("title", "—")

        bridge   = get_latest_output(slug, "bridge")
        score    = parse_bridge_score(bridge)
        trend    = parse_bridge_trend(bridge)
        last_run = "Never"

        if BRIDGE_DIR.exists():
            files = sorted(BRIDGE_DIR.glob(f"{slug}_*.json"), reverse=True)
            if files:
                last_run = parse_file_timestamp(slug, files[0])

        rows.append({
            "slug":     slug,
            "name":     name,
            "genre":    genre,
            "release":  release,
            "score":    score,
            "trend":    trend,
            "status":   score_to_status(score),
            "last_run": last_run,
        })
    order = {"critical": 0, "monitor": 1, "good": 2, "no-data": 3}
    rows.sort(key=lambda r: (order.get(r["status"], 9), -(r["score"] or -1)))
    return rows


# --- App Factory ---
def create_app(url_prefix: str = "") -> Flask:
    """
    App factory function. Creates and configures a Flask app instance.
    This factory is primarily for running scripts/web_app.py directly.
    """
    app = Flask(__name__, template_folder=str(TEMPLATES), static_folder=str(STATIC))
    app.secret_key = SECRET_KEY

    # Set an attribute used by the blueprint for context
    app.LABEL_URL_PREFIX = url_prefix or ""

    # Register the LABEL blueprint.
    # If url_prefix is "", routes like bp.index() will be at the root /.
    app.register_blueprint(bp, url_prefix=url_prefix)

    # Define global routes (login, logout) on THIS app instance.
    # These must match what `login_required` expects via `url_for("login_page")`.
    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        error = None
        # Default redirect after login is to the label index, unless 'next' is provided.
        next_url = request.form.get("next") or request.args.get("next", url_for("label.index"))
        if request.method == "POST":
            token = request.form.get("token", "").strip()
            if token == MAESTRO_TOKEN:
                session["authenticated"] = True
                return redirect(next_url)
            error = "Invalid token. Try again."
        # render_template looks for login.html relative to app.template_folder
        return render_template("login.html", error=error, next_url=next_url)

    @app.route("/logout")
    def logout():
        session.clear()
        # Redirect back to the login page endpoint
        return redirect(url_for("login_page"))

    # Ensure MAESTRO_TOKEN is set when this factory is used.
    if not MAESTRO_TOKEN:
        raise ValueError("MAESTRO_TOKEN not set in .env file")

    return app

# --- Legacy Entry Point Execution Guard ---
# This block only runs if scripts/web_app.py is executed directly (e.g., `python scripts/web_app.py`).
if __name__ == "__main__":
    # Check token for direct execution
    if not MAESTRO_TOKEN:
        raise ValueError("MAESTRO_TOKEN not set in .env file for direct execution")

    # Create the app for direct execution.
    # Registering bp at root (url_prefix="").
    # The login/logout routes are already part of create_app.
    app = create_app("")

    # --- Direct execution specific configuration ---
    import socket
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "your-local-ip"

    print(f"""
  ╔══════════════════════════════════════╗
  ║       MAESTRO AI — Web Dashboard     ║
  ╠══════════════════════════════════════╣
  ║  Local:    http://127.0.0.1:{PORT}      ║
  ║  Network:  http://{local_ip}:{PORT}  ║
  ║  Token:    MAESTRO_TOKEN from .env   ║
  ╚══════════════════════════════════════╝
""")
    # Run the app directly. Debug=True for development.
    app.run(host="0.0.0.0", port=PORT, debug=True, threaded=True)