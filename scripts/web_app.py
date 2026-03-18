# scripts/web_app.py
# MAESTRO AI — Web Dashboard Backend
# Run: python scripts/web_app.py

import sys
import os
import re
import json
import subprocess
import requests as req_lib
from pathlib import Path
from datetime import datetime
from functools import wraps
from flask import (
    Flask, Blueprint, render_template, request, session,
    redirect, url_for, jsonify, Response, stream_with_context, current_app,
)
from dotenv import load_dotenv

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent          # C:\Users\brett\...\maestro-ai
TEMPLATES   = ROOT / "templates"
STATIC      = ROOT / "static"
DATA        = ROOT / "data"
ARTISTS_DIR = DATA / "artists"
BRIDGE_DIR  = DATA / "bridge"
AGENTS      = ["vinyl", "echo", "atlas", "forge", "sage", "bridge"]

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv(ROOT / ".env")
MAESTRO_TOKEN = os.getenv("MAESTRO_TOKEN")
if not MAESTRO_TOKEN:
    raise ValueError("MAESTRO_TOKEN not set in .env")
WEBHOOK_URL   = os.getenv("WEBHOOK_URL", "http://localhost:5678/webhook/health-update")
PORT          = int(os.getenv("WEB_PORT", 8080))
SECRET_KEY    = os.getenv("SECRET_KEY", os.urandom(24).hex())

# ── Flask App ─────────────────────────────────────────────────────────────────
bp = Blueprint("maestro", __name__)

def create_app(url_prefix: str = "") -> Flask:
    app = Flask(__name__, template_folder=str(TEMPLATES), static_folder=str(STATIC))
    app.secret_key = SECRET_KEY
    app.MAESTRO_URL_PREFIX = url_prefix or ""

    app.register_blueprint(bp, url_prefix=url_prefix)

    # ── Global auth routes (shared across departments) ─────────────────────────
    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        ...
        error = None
        if request.method == "POST":
            token = request.form.get("token", "").strip()
            if token == MAESTRO_TOKEN:
                session["authenticated"] = True
                # If user came from a prefixed department, let Flask redirect back.
                return redirect(request.args.get("next") or url_for("maestro.index"))
            error = "Invalid token. Try again."
        return render_template("login.html", error=error)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login_page"))

    return app



# ── ANSI stripping (colorama output → clean text) ─────────────────────────────
ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)

# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated

# ── Data helpers ──────────────────────────────────────────────────────────────
def get_artist_slugs() -> list:
    if not ARTISTS_DIR.exists():
        return []
    return [f.stem for f in sorted(ARTISTS_DIR.glob("*.json"))]

def load_artist(slug: str) -> dict | None:
    path = ARTISTS_DIR / f"{slug}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def slug_to_name(slug: str) -> str:
    artist = load_artist(slug)
    if artist:
        return artist.get("artist_info", {}).get("name", slug)
    return slug.replace("_", " ").title()

def get_latest_output(slug: str, agent: str) -> dict | None:
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

def parse_bridge_score(bridge_data: dict) -> int | None:
    if not bridge_data:
        return None
    health = bridge_data.get("health_assessment", bridge_data.get("health", {}))
    score  = health.get("overall_score", health.get("score", None))
    return int(score) if score is not None else None

def parse_bridge_trend(bridge_data: dict) -> str:
    if not bridge_data:
        return "—"
    health = bridge_data.get("health_assessment", bridge_data.get("health", {}))
    return health.get("trend", "—")

def score_to_status(score: int | None) -> str:
    if score is None:
        return "no-data"
    if score >= 70:
        return "good"
    if score >= 40:
        return "monitor"
    return "critical"

def parse_file_timestamp(slug: str, filepath: Path) -> str:
    """Extract datetime from slug_YYYYMMDD_HHMMSS.json filename."""
    try:
        suffix = filepath.stem[len(slug) + 1:]   # strip slug_ prefix
        dt = datetime.strptime(suffix, "%Y%m%d_%H%M%S")
        return dt.strftime("%d %b %Y %H:%M")
    except Exception:
        return "—"

def get_bridge_history(slug: str) -> list:
    """Return list of {timestamp, score} dicts sorted oldest → newest."""
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
                dt = datetime.strptime(suffix, "%Y%m%d_%H%M%S")
                ts = dt.strftime("%d %b %H:%M")
            except Exception:
                ts = suffix
            history.append({"timestamp": ts, "score": score})
        except Exception:
            continue
    return history

def build_dashboard_rows() -> list:
    rows = []
    for slug in get_artist_slugs():
        artist = load_artist(slug)
        if not artist:
            continue
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

    # Sort: critical first, then monitor, then good, then no-data
    order = {"critical": 0, "monitor": 1, "good": 2, "no-data": 3}
    rows.sort(key=lambda r: (order.get(r["status"], 9), -(r["score"] or -1)))
    return rows

# ── Page routes ───────────────────────────────────────────────────────────────
@bp.route("/")
@login_required
def index():
    prefix = getattr(current_app, "MAESTRO_URL_PREFIX", "")
    return render_template("index.html", api_prefix=prefix)

# ── API routes ────────────────────────────────────────────────────────────────
@bp.route("/api/dashboard")
@login_required
def api_dashboard():
    return jsonify(build_dashboard_rows())

@bp.route("/api/artists")
@login_required
def api_artists():
    out = []
    for slug in get_artist_slugs():
        a = load_artist(slug)
        if a:
            out.append({
                "slug": slug,
                "name": a.get("artist_info", {}).get("name", slug),
            })
    return jsonify(out)

@bp.route("/api/artist/<slug>")
@login_required
def api_artist(slug):
    artist = load_artist(slug)
    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    outputs = {}
    for agent in AGENTS:
        data = get_latest_output(slug, agent)
        if data:
            outputs[agent] = data

    bridge  = outputs.get("bridge", {})
    score   = parse_bridge_score(bridge)
    trend   = parse_bridge_trend(bridge)
    history = get_bridge_history(slug)

    return jsonify({
        "slug":    slug,
        "profile": artist,
        "score":   score,
        "trend":   trend,
        "status":  score_to_status(score),
        "outputs": outputs,
        "history": history,
    })

@bp.route("/api/stream/<agent>/<slug>")
@login_required
def api_stream(agent, slug):
    """SSE endpoint — streams live agent output to browser."""
    if agent not in AGENTS + ["full"]:
        return jsonify({"error": "Unknown agent"}), 400

    name = slug_to_name(slug)
    cmd = [sys.executable, "scripts/maestro.py", "full" if agent == "full" else agent, name]

    def generate():
        try:
            yield f"data: {json.dumps({'line': f'▶  {agent.upper()}  →  {name}'})}\n\n"
            yield f"data: {json.dumps({'line': '─' * 48})}\n\n"

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(ROOT),
                env=env,
            )

            for raw in iter(proc.stdout.readline, ""):
                line = strip_ansi(raw.rstrip())
                if line:
                    yield f"data: {json.dumps({'line': line})}\n\n"

            proc.wait()
            ok     = proc.returncode == 0
            symbol = "✓" if ok else "✗"
            msg    = f"{symbol}  Finished — exit code {proc.returncode}"
            yield f"data: {json.dumps({'line': '─' * 48})}\n\n"
            yield f"data: {json.dumps({'line': msg, 'done': True, 'ok': ok})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'line': f'ERROR: {e}', 'done': True, 'ok': False})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@bp.route("/api/webhook/<slug>", methods=["POST"])
@login_required
def api_webhook(slug):
    """Fire a health-update webhook for this artist."""
    artist = load_artist(slug)
    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    bridge = get_latest_output(slug, "bridge")
    score  = parse_bridge_score(bridge)
    trend  = parse_bridge_trend(bridge)

    payload = {
        "artist":    artist.get("artist_info", {}).get("name", slug),
        "slug":      slug,
        "score":     score,
        "status":    score_to_status(score),
        "trend":     trend,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source":    "maestro-web-ui",
    }

    try:
        resp = req_lib.post(WEBHOOK_URL, json=payload, timeout=5)
        return jsonify({"sent": True, "http_status": resp.status_code, "payload": payload})
    except req_lib.exceptions.ConnectionError:
        return jsonify({"sent": False, "error": "Endpoint unreachable (is n8n running?)", "payload": payload})
    except Exception as e:
        return jsonify({"sent": False, "error": str(e), "payload": payload})

@bp.route("/api/checkin/<slug>", methods=["POST"])
@login_required
def api_checkin(slug):
    name = slug_to_name(slug)
    body = request.get_json(silent=True) or {}
    note = body.get("note", "")

    try:
        result = subprocess.run(
            [sys.executable, "scripts/maestro.py", "checkin", name],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=30,
        )
        return jsonify({
            "success": result.returncode == 0,
            "note":    note,
            "output":  strip_ansi(result.stdout + result.stderr).strip(),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Legacy entrypoint still works: python scripts/web_app.py
app = create_app("")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
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
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)