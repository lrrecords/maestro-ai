from pathlib import Path
from datetime import datetime, timezone
import os
import json
import requests
from core.base_agent import BaseAgent

class SessionAgent(BaseAgent):
    name = "SESSION"
    department = "studio"
    description = "Session planning, scheduling, and resource allocation."

    FIELDS = [
        {"key": "session_name", "label": "Session name", "type": "text", "required": True},
        {"key": "artist", "label": "Artist / client", "type": "text", "required": True},
        {"key": "session_date", "label": "Date", "type": "date", "required": True},
        {"key": "start_time", "label": "Start", "type": "time"},
        {"key": "end_time", "label": "End", "type": "time"},
        {"key": "room", "label": "Room", "type": "text"},
        {"key": "engineer", "label": "Engineer", "type": "text"},
        {"key": "session_type", "label": "Type", "type": "select",
         "options": ["tracking", "mixing", "mastering", "overdubs"]},
        {"key": "status", "label": "Status", "type": "select",
         "options": ["booked", "tentative", "completed", "cancelled"]},
        {"key": "notes", "label": "Notes", "type": "textarea"},
    ]

    def __init__(self, data_root: str | Path | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_name = self.name
        self.data_root = Path(data_root) if data_root else Path("studio") / "data"
        self.ollama_base_url = "http://localhost:11434"
        self.ollama_model = "llama3"
        self.data_root.mkdir(parents=True, exist_ok=True)

    def run(self, context: dict) -> dict:
        ctx = context or {}
        # --- Validation ---
        required = [
            ('session_name', ctx.get('session_name', '')),
            ('artist', ctx.get('artist', '')),
            ('session_date', ctx.get('session_date',''))
        ]
        missing = [k for k,v in required if not v]
        if missing:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "error": f"Missing required fields: {', '.join(missing)}",
                "context": context,
                "result": {
                    "action": "error",
                    "session": {},
                    "recommendations": [
                        "Please fill in all required fields: session name, artist, and date.",
                        "Specify engineer, room, and times for better scheduling.",
                        "Add session type for resource allocation."
                    ]
                }
            }

        start_time = (ctx.get("start_time", "") or "").strip()
        end_time = (ctx.get("end_time", "") or "").strip()
        if start_time and end_time:
            time_range = f"{start_time} → {end_time}"
        elif start_time:
            time_range = start_time
        elif end_time:
            time_range = end_time
        else:
            time_range = "—"

        session = {
            "session_name": (ctx.get("session_name", "") or "").strip(),
            "artist": (ctx.get("artist", "") or "").strip(),
            "session_date": (ctx.get("session_date", "") or "").strip(),
            "time": time_range,
            "room": (ctx.get("room", "") or "").strip() or "—",
            "engineer": (ctx.get("engineer", "") or "").strip() or "—",
            "session_type": (ctx.get("session_type", "tracking") or "tracking").strip(),
            "status": (ctx.get("status", "booked") or "booked").strip(),
            "notes": (ctx.get("notes", "") or "").strip() or "—",
        }

        # --- Audit/History logging: Save to sessions.json ---
        sessions_file = self.data_root / "sessions.json"
        sessions = []
        if sessions_file.exists():
            try:
                sessions = json.loads(sessions_file.read_text(encoding="utf-8"))
                if not isinstance(sessions, list):
                    sessions = []
            except Exception:
                sessions = []
        now_iso = datetime.now(timezone.utc).isoformat()
        session_record = {**session, "created_at": now_iso}
        sessions.append(session_record)
        sessions_file.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")

        # Audit trail: last 5 sessions for the same artist or room
        artist = session["artist"]
        room = session["room"]
        audit_trail = [
            {k: v for k, v in s.items() if k not in ("notes", "created_at")}
            for s in sessions if s.get("artist") == artist or s.get("room") == room
        ][-5:]

        recommendations = self._generate_recommendations(session, audit_trail)

        return {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "context": context,
            "result": {
                "action": "created",
                "session": session,
                "recommendations": recommendations,
                "audit_trail": audit_trail,
                "saved_to": str(sessions_file),
            }
        }

    def _generate_recommendations(self, session: dict, audit_trail: list) -> list[str]:
        # LLM-powered or fallback scheduling/session prep advice
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback(session, audit_trail)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        audit_lines = ""
        if audit_trail:
            audit_lines = "\nRecent similar sessions: " + " | ".join(
                f"{s.get('session_name','')} ({s.get('room','')} {s.get('session_date','')})"
                for s in audit_trail
            )
        prompt = f"""
You are an expert in studio session management and logistics.

Generate practical session prep and scheduling recommendations for the following:

- Session name: {session.get("session_name", "")}
- Artist: {session.get("artist", "")}
- Date: {session.get("session_date", "")}
- Time: {session.get("time", "")}
- Room: {session.get("room", "")}
- Engineer: {session.get("engineer", "")}
- Type: {session.get("session_type", "")}
- Notes: {session.get("notes", "")}
{audit_lines}

Return:
- One summary/overview sentence
- Five actionable bullet points on session planning, prep, and logistics
- Three next actions before and after the session

Plain text only, no markdown headings.
""".strip()

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_ctx": num_ctx, "temperature": 0.7},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            text = (resp.json().get("response") or "").strip()
            lines = [l.strip("•- \t") for l in text.splitlines() if l.strip()]
            return lines[:9] or self._fallback(session, audit_trail)
        except Exception as exc:
            return self._fallback(session, audit_trail) + [f"LLM unavailable; using fallback. ({exc})"]

    def _fallback(self, session: dict, audit_trail: list) -> list[str]:
        """Fallback recs if LLM is down/unset."""
        recs = [
            f"Confirm all session details with {session.get('artist','the artist')} at least 48 hours before.",
            "Prepare a detailed signal chain and patch sheet.",
            "Verify engineer and room assignments; avoid double-bookings.",
            "Check all equipment, cables, and backups for each session.",
            "Send calendar invites to all involved, with directions/parking info.",
            "Arrange any hospitality needs (water, coffee, catering, breaks).",
            "Log in the studio register upon start/end for records."
        ]
        if session.get('status') == "tentative":
            recs.append("Mark as tentative until deposit has cleared and all client preferences are confirmed.")
        if audit_trail:
            recs.append("Review recent sessions for repeat technical/hospitality issues.")
        return recs[:9]
