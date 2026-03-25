from flask import (
    Blueprint, render_template, request, jsonify, Response,
    stream_with_context, current_app, session, redirect, url_for
)
from datetime import datetime
import logging
import time
import json
import os
import requests
from pathlib import Path

label_bp = Blueprint("label", __name__)

# --- CONFIG AND PATH CONSTANTS ---
ROOT        = Path(__file__).parent.parent          # maestro-ai/
TEMPLATES   = ROOT / "templates"
STATIC      = ROOT / "static"
DATA        = ROOT / "data"
ARTISTS_DIR = DATA / "artists"
BRIDGE_DIR  = DATA / "bridge"
AGENTS      = ["vinyl", "echo", "atlas", "forge", "sage", "bridge"]

# --- DASHBOARD INDEX ---
@label_bp.route("/")
def index():
    # Pass the API prefix for frontend JS usage
    prefix = current_app.config.get("LABEL_URL_PREFIX", "/label")
    return render_template("index.html", api_prefix=prefix)

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

def build_agent_prompt(agent, artist):
    name = artist.get('artist_info', {}).get('name') or artist.get('artist_name', '(unknown artist)')
    release = artist.get('upcoming_release', {}).get('title', '(no title)')
    release_date = artist.get('upcoming_release', {}).get('date', '')
    example_json = '''{
      "agent": "VINYL",
      "artist": "Nova Saint",
      ...
    }'''
    prompt = (
        f"You are the {agent.upper()} release operations agent for {name}.\n"
        f"The upcoming release is '{release}' on {release_date}.\n"
        f"Generate the full release operations JSON calendar in this format:\n\n"
        f"{example_json}\n\n"
        "Output ONLY MINIFIED JSON ON A SINGLE LINE, with NO spaces, indentation, or trailing commas. Do NOT explain. Do NOT include anything except the JSON."
    )
    return prompt

# --- AGENT STREAM ROUTE ---
import requests

@label_bp.route("/api/stream/<agent>/<slug>")
def api_stream(agent, slug):
    artist = load_artist(slug)
    if not artist:
        def error_stream():
            part = '{"error": "Artist not found"}'
            print("YIELDING TO FRONTEND:", part)
            yield f'data: {part}\n\n'
        return Response(stream_with_context(error_stream()), mimetype="text/event-stream")

    # Build the prompt
    prompt = build_agent_prompt(agent, artist)

    # Ollama config from environment or .env
    ollama_url   = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    ollama_model = os.environ.get('OLLAMA_MODEL', 'qwen2.5:3b')
    ollama_timeout = int(os.environ.get('OLLAMA_TIMEOUT_SECONDS', '1800'))

    # API endpoint
    generate_url = f"{ollama_url}/api/generate"
    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": True
    }

    import re

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
                            output_json = json.loads(json_buffer)
                            yield f'data: {json.dumps({"result": output_json, "done": True})}\n\n'
                        except Exception as e:
                            yield f'data: {json.dumps({"error": "Failed to parse JSON from LLM", "output": json_buffer, "done": True})}\n\n'
                        # ADD THIS:
                        yield 'data: [DONE]\n\n'
                        return
        except Exception as e:
            yield f'data: {json.dumps({"error": "LLM error: " + str(e)})}\n\n'

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

# --- CHECK-IN ---
@label_bp.route("/api/checkin/<slug>", methods=["POST"])
def api_checkin(slug):
    note = (request.json or {}).get("note", "")
    ts   = datetime.utcnow().isoformat()
    logging.info("Check-in logged for %s: %s", slug, note)
    return jsonify({"success": True, "output": f"Check-in saved at {ts}"})

# --- WEBHOOK ---
@label_bp.route("/api/webhook/<slug>", methods=["POST"])
def api_webhook(slug):
    # You may need to update these variables to match your project context
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:5678/webhook/health-update")
    payload = {
        "artist":    slug_to_name(slug),
        "slug":      slug,
        "timestamp": datetime.utcnow().isoformat(),
        "source":    "maestro-web-ui",
    }
    try:
        import requests as req_lib
        r = req_lib.post(WEBHOOK_URL, json=payload, timeout=6)
        return jsonify({"sent": True, "http_status": r.status_code})
    except Exception as e:
        logging.exception("Webhook error")
        return jsonify({"sent": False, "error": str(e)}), 500

# --- HELPERS (These can be moved to a utils.py if you prefer) ---
def get_artist_slugs():
    if not ARTISTS_DIR.exists(): return []
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
    if artist: return artist.get("artist_info", {}).get("name", slug)
    return slug.replace("_", " ").title()

def get_latest_output(slug, agent):
    agent_dir = DATA / agent
    if not agent_dir.exists(): return None
    files = sorted(agent_dir.glob(f"{slug}_*.json"), reverse=True)
    if not files: return None
    try: return json.loads(files[0].read_text(encoding="utf-8"))
    except Exception: return None

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
    if score is None: return "no-data"
    if score >= 70: return "good"
    if score >= 40: return "monitor"
    return "critical"

def parse_file_timestamp(slug, filepath):
    try:
        suffix = filepath.stem[len(slug) + 1:]
        dt = datetime.strptime(suffix, "%Y%m%d_%H%M%S")
        return dt.strftime("%d %b %Y %H:%M")
    except Exception: return "—"

def get_bridge_history(slug):
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

def build_dashboard_rows():
    rows = []
    slugs = get_artist_slugs()
    for slug in slugs:
        artist = load_artist(slug)
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