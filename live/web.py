from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, jsonify, render_template, request

from live.agents import REGISTRY   # ← module-level import now

live_bp = Blueprint("live", __name__)
_DATA   = Path(__file__).parent / "data"


def _load(filename: str) -> list:
    path = _DATA / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


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
        confirmed=len([s for s in shows if s.get("status") == "confirmed"]),
        on_hold=len([s for s in shows if s.get("status") == "hold"]),
        pending=len([s for s in shows if s.get("status") == "pending"]),
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