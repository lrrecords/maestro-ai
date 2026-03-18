from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, jsonify, render_template, request

from studio.agents import REGISTRY

studio_bp = Blueprint("studio", __name__)
_DATA     = Path(__file__).parent / "data"


def _load(filename: str) -> list:
    path = _DATA / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


@studio_bp.get("/")
def index():
    sessions = _load("sessions.json")
    clients  = _load("clients.json")

    agent_fields = {
        slug: {
            "description": cls.description,
            "fields":      getattr(cls, "FIELDS", []),
        }
        for slug, cls in REGISTRY.items()
    }

    return render_template(
        "dept_studio.html",
        sessions=sessions,
        clients=clients,
        booked=len([s for s in sessions if s.get("status") == "booked"]),
        tentative=len([s for s in sessions if s.get("status") == "tentative"]),
        agent_fields=agent_fields,
    )


@studio_bp.post("/run/<agent_name>")
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


@studio_bp.get("/agents")
def list_agents():
    return jsonify({
        slug: {"name": cls.name, "description": cls.description,
               "department": cls.department, "fields": getattr(cls, "FIELDS", [])}
        for slug, cls in REGISTRY.items()
    })

@studio_bp.get("/schemas")
def schemas():
    from studio.agents.schema import STUDIO_AGENT_SCHEMAS
    return jsonify(STUDIO_AGENT_SCHEMAS)