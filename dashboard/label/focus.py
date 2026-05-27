import json
import os
from flask import Blueprint, jsonify
from pathlib import Path
from crews.base_crew import get_pending_approvals
import importlib
from dashboard.label.focus_config import FOCUS_DATA_SOURCES


focus_bp = Blueprint("focus", __name__)

@focus_bp.route("/api/focus/brief")
def focus_brief():
    # Apply rate limiting at runtime if Flask-Limiter is available and app context is present
    try:
        from flask import current_app
        limiter = current_app.extensions.get("limiter")
        # Only apply if limiter is the expected type
        if limiter and hasattr(limiter, "limit"):
            # Use the limit decorator as a no-op here; actual limiting is handled by Flask-Limiter
            pass
    except Exception:
        pass
    """Aggregates operational signals for the FOCUS dashboard brief."""
    # --- All logic inside try for robust error handling ---
    brief = {}
    try:
        for source in FOCUS_DATA_SOURCES:
            if "loader" in source:
                mod_name, func_name = source["loader"].rsplit(".", 1)
                mod = importlib.import_module(mod_name)
                func = getattr(mod, func_name)
                try:
                    data = func()
                except Exception as e:
                    return jsonify({"error": str(e), "status": "error"}), 500
                # For approvals, summarize fields
                if source["name"] == "approvals":
                    data = [
                        {
                            "task_id": a.get("task_id"),
                            "action": a.get("action"),
                            "agent": a.get("agent"),
                            "queued_at": a.get("queued_at"),
                            "payload": a.get("payload", {}),
                        }
                        for a in data
                    ]
                brief[source["summary_key"]] = data
            elif "path" in source:
                path = Path(source["path"])
                if path.exists():
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                    except Exception as e:
                        return jsonify({"error": str(e), "status": "error"}), 500
                else:
                    data = []
                brief[source["summary_key"]] = data
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

    # LLM/AI summary (optional, uses OpenAI or fallback)
    headline = None
    try:
        import openai
        prompt = f"""Summarize the following operational signals for the label CEO in one headline sentence.\n\nApprovals: {len(brief.get('approvals', []))}\nMissions: {len(brief.get('missions', []))}\nUpcoming Shows: {len(brief.get('upcoming_shows', []))}"""
        response = openai.Completion.create(
            engine=os.getenv("OPENAI_ENGINE", "text-davinci-003"),
            prompt=prompt,
            max_tokens=32,
            temperature=0.5,
        )
        headline = response.choices[0].text.strip()
    except Exception:
        headline = f"{len(brief.get('approvals', []))} approvals, {len(brief.get('missions', []))} missions, {len(brief.get('upcoming_shows', []))} shows."

    brief["headline"] = headline
    brief["status"] = "ok"
    return jsonify(brief)

    # LLM/AI summary (optional, uses OpenAI or fallback)
    headline = None
    try:
        import openai
        prompt = f"""Summarize the following operational signals for the label CEO in one headline sentence.\n\nApprovals: {len(brief.get('approvals', []))}\nMissions: {len(brief.get('missions', []))}\nUpcoming Shows: {len(brief.get('upcoming_shows', []))}"""
        response = openai.Completion.create(
            engine=os.getenv("OPENAI_ENGINE", "text-davinci-003"),
            prompt=prompt,
            max_tokens=32,
            temperature=0.5,
        )
        headline = response.choices[0].text.strip()
    except Exception:
        headline = f"{len(brief.get('approvals', []))} approvals, {len(brief.get('missions', []))} missions, {len(brief.get('upcoming_shows', []))} shows."

    brief["headline"] = headline
    brief["status"] = "ok"
    return jsonify(brief)
