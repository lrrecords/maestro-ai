from __future__ import annotations
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from core.base_agent import BaseAgent

class LedgerAgent(BaseAgent):
    name = "LEDGER"
    department = "label"
    description = "Financial tracking, session costs, and revenue reporting."

    FIELDS = [
        {"key": "period", "label": "Reporting Period", "type": "select", "options": ["last_30_days", "this_month", "last_month", "this_year", "all_time"], "default": "last_30_days"},
        {"key": "artist_slug", "label": "Filter by Artist", "type": "text", "placeholder": "e.g. aria_velvet (optional)"},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # LEDGER needs access to multiple data roots
        self.root_dir = Path(__file__).parent.parent
        self.live_data = self.root_dir / "live" / "data"
        self.studio_data = self.root_dir / "studio" / "data"
        self.artist_data = self.root_dir / "data" / "artists"

    def run(self, context: dict) -> dict:
        period = context.get("period", "last_30_days")
        artist_slug = context.get("artist_slug")

        # 1. Load Data
        shows = self._load_json(self.live_data / "shows.json", [])
        # Studio sessions are often in studio/data/sessions.json
        sessions = self._load_json(self.studio_data / "sessions.json", [])
        # Also check for individual session files if they exist
        session_dir = self.studio_data / "session"
        if session_dir.exists():
            for f in session_dir.glob("*.json"):
                sessions.append(self._load_json(f, {}))

        # 2. Filter by Artist if requested
        if artist_slug:
            shows = [s for s in shows if s.get("artist_slug") == artist_slug or s.get("artist") == artist_slug]
            sessions = [s for s in sessions if s.get("artist_slug") == artist_slug or s.get("artist") == artist_slug]

        # 3. Calculate Live Revenue
        live_summary = self._summarize_live(shows)
        
        # 4. Calculate Session Costs
        session_summary = self._summarize_sessions(sessions)

        # 5. Artist Count
        artists = list(self.artist_data.glob("*.json"))
        artist_count = len(artists)

        result_data = {
            "period": period,
            "artist_filter": artist_slug or "all",
            "live_revenue": live_summary,
            "session_costs": session_summary,
            "artist_count": artist_count,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        # Save output using BaseAgent's method
        saved_path = self.save_output(result_data, slug=f"summary_{period}")

        return {
            "agent": self.name,
            "department": self.department,
            "status": "complete",
            "message": f"Financial summary generated for {period}.",
            "data": result_data,
            "saved_to": saved_path,
            "context": context
        }

    def _load_json(self, path: Path, default: any) -> any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _summarize_live(self, shows: list) -> dict:
        total_gross = 0.0
        total_net = 0.0
        show_list = []

        for s in shows:
            gross = float(s.get("gross_box_office") or s.get("gross") or 0)
            net = float(s.get("net_box_office") or s.get("net") or 0)
            total_gross += gross
            total_net += net
            show_list.append({
                "date": s.get("date"),
                "artist": s.get("artist"),
                "venue": s.get("venue"),
                "gross": gross,
                "net": net
            })

        return {
            "total_gross": round(total_gross, 2),
            "total_net": round(total_net, 2),
            "shows": show_list
        }

    def _summarize_sessions(self, sessions: list) -> dict:
        total_cost = 0.0
        session_list = []

        for s in sessions:
            # Try to find cost in various fields
            cost = float(s.get("cost") or s.get("total_cost") or s.get("grand_total") or 0)
            # If no cost, estimate based on type (placeholder logic)
            if cost == 0:
                stype = (s.get("session_type") or s.get("type") or "").lower()
                rates = {"tracking": 650, "mixing": 350, "mastering": 120}
                cost = rates.get(stype, 0)

            total_cost += cost
            session_list.append({
                "date": s.get("session_date") or s.get("date"),
                "artist": s.get("artist"),
                "type": s.get("session_type") or s.get("type"),
                "cost": cost
            })

        return {
            "total": round(total_cost, 2),
            "sessions": session_list
        }
