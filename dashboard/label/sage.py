from flask import Blueprint, render_template, jsonify, current_app, session
from pathlib import Path
import json
import os
from premium_agents.sage_daily_brief import SageAgent

sage_bp = Blueprint("sage", __name__)

@sage_bp.route("/api/brief")
def brief():
    """Returns JSON daily brief using the SageAgent."""
    try:
        agent = SageAgent()
        result = agent.run({"scope": "daily"})
        return jsonify(result["data"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
