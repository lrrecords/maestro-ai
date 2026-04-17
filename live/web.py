from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, jsonify, render_template, request, redirect, session, url_for

from live.agents import REGISTRY   # ← module-level import now

live_bp = Blueprint("live", __name__)
_DATA   = Path(__file__).parent / "data"

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


@live_bp.before_request
def require_auth():
    if _is_authorized():
        return None
    if (
        request.path.startswith("/live/run/")
        or request.path.startswith("/live/apply/")
        or request.path.startswith("/live/api/")
    ):
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    return redirect(url_for("login_page", next=request.path))


def _load(filename: str) -> list:
    path = _DATA / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_list(filename: str, data: list) -> None:
    path = _DATA / filename
    tmp  = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


@live_bp.get("/")
def index():
    shows = _load("shows.json")
    tours = _load("tours.json")

    # Build structured agent info dict — embedded into the template as JS
    agent_fields = {
        slug: {
            "description": cls.description,
            "fields":      getattr(cls, "FIELDS", []),
        }
        for slug, cls in REGISTRY.items()
    }

    return render_template(
        "dept_live.html",
        shows=shows,
        tours=tours,
        confirmed=len([s for s in shows if (s.get("status") or "").lower() == "confirmed"]),
        on_hold=len([s for s in shows if (s.get("status") or "").lower() == "hold"]),
        pending=len([s for s in shows if (s.get("status") or "").lower() == "pending"]),
        agent_fields=agent_fields,
    )


@live_bp.post("/run/<agent_name>")
def run_agent(agent_name: str):
    slug      = agent_name.lower().strip()
    agent_cls = REGISTRY.get(slug)
    if not agent_cls:
        return jsonify({"ok": False, "error": f"Unknown agent '{agent_name}'.",
                        "available": sorted(REGISTRY.keys())}), 404
    context = request.get_json(silent=True) or {}
    try:
        agent  = agent_cls(data_root=_DATA)
        result = agent.run(context)
        saved  = agent.save_output(result, slug=slug)
        return jsonify({"ok": True, "agent": slug.upper(),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "saved_to": str(saved), "result": result})
    except Exception as exc:
        return jsonify({"ok": False, "agent": slug.upper(), "error": str(exc)}), 500


@live_bp.post("/apply/book")
def apply_book():
    payload = request.get_json(silent=True) or {}
    booking = payload.get("booking") or {}

    artist    = booking.get("artist") or "—"
    territory = booking.get("territory") or "—"
    dates     = booking.get("dates") or []

    if not isinstance(dates, list) or not dates:
        return jsonify({"ok": False, "error": "Missing booking.dates[]"}), 400

    shows = _load("shows.json")

    added = []
    for d in dates:
        if not isinstance(d, str) or not d:
            continue

        # ✅ DEDUPE: prevent duplicate artist/date rows
        exists = any((s.get("date") == d and s.get("artist") == artist) for s in shows)
        if exists:
            continue

        show = {
            "date": d,
            "artist": artist,
            "venue": "—",
            "city": "—",
            "territory": territory,
            "status": "pending",
        }
        shows.append(show)
        added.append(show)

    _save_list("shows.json", shows)
    return jsonify({"ok": True, "added": len(added), "shows": added})


@live_bp.post("/apply/tour")
def apply_tour():
    payload = request.get_json(silent=True) or {}

    # accept either explicit tour fields OR a TOUR envelope's context/data
    artist = payload.get("artist") or payload.get("context", {}).get("artist") or "—"
    start  = payload.get("start") or payload.get("context", {}).get("start_date") or "—"
    end    = payload.get("end") or payload.get("context", {}).get("end_date") or "—"

    show_count = payload.get("show_count")
    if show_count is None:
        show_count = payload.get("context", {}).get("show_count")

    try:
        show_count = int(show_count) if show_count is not None else 0
    except Exception:
        show_count = 0

    name = payload.get("name") or payload.get("tour_name") or f"{artist} Tour"

    tours = _load("tours.json")

    tour = {
        "name": name,
        "artist": artist,
        "start": start,
        "end": end,
        "show_count": show_count,
        "status": "pending",
    }
    tours.append(tour)
    _save_list("tours.json", tours)

    return jsonify({"ok": True, "added": 1, "tour": tour})


@live_bp.get("/agents")
def list_agents():
    return jsonify({
        slug: {"name": cls.name, "description": cls.description,
               "department": cls.department, "fields": getattr(cls, "FIELDS", [])}
        for slug, cls in REGISTRY.items()
    })

@live_bp.get("/schemas")
def schemas():
    from live.agents.schema import LIVE_AGENT_SCHEMAS
    return jsonify(LIVE_AGENT_SCHEMAS)