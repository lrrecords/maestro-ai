import os
import json
import logging
from flask import Flask, request, jsonify
import requests as _req
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

def _webhook_authorized() -> bool:
    secret = (os.getenv("WEBHOOK_SECRET") or "").strip()
    if not secret:
        return False
    header_secret = (request.headers.get("X-WEBHOOK-SECRET") or "").strip()
    bearer = (request.headers.get("Authorization") or "").strip()
    if bearer.startswith("Bearer ") and bearer[7:].strip() == secret:
        return True
    return header_secret == secret

# ── Inbound: EasyFunnels → n8n → Maestro ──────────────────────────────────────

@app.route("/webhook/easyfunnels/crm-update", methods=["POST"])
def ef_crm_update():
    if not _webhook_authorized():
        return jsonify({"error": "Unauthorized webhook"}), 401
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
    if not _webhook_authorized():
        return jsonify({"error": "Unauthorized webhook"}), 401
    """EasyFunnels store order received → queue for ATLAS revenue tracking."""
    data = request.json or {}
    _save_to_queue("store_order", data)
    return jsonify({"received": True})

@app.route("/webhook/easyfunnels/appointment", methods=["POST"])
def ef_appointment():
    if not _webhook_authorized():
        return jsonify({"error": "Unauthorized webhook"}), 401
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
    if not _webhook_authorized():
        return jsonify({"error": "Unauthorized webhook"}), 401
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
