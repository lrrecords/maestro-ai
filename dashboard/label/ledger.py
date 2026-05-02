from flask import Blueprint, render_template, jsonify, current_app, session
from pathlib import Path
import json
import os
from premium_agents.ledger import LedgerAgent

ledger_bp = Blueprint("ledger", __name__)

@ledger_bp.route("/")
def index():
    """Renders the ledger dashboard template."""
    # In a real app, we'd check permissions here
    return render_template("label/ledger.html")

@ledger_bp.route("/api/summary")
def summary():
    """Returns JSON financial summary using the LedgerAgent."""
    try:
        agent = LedgerAgent()
        # Default to last 30 days for the dashboard summary
        result = agent.run({"period": "last_30_days"})
        return jsonify(result["data"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
