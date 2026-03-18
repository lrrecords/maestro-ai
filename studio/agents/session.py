from pathlib import Path
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
        {
            "key": "session_type",
            "label": "Type",
            "type": "select",
            "options": ["tracking", "mixing", "mastering", "overdubs"],
        },
        {
            "key": "status",
            "label": "Status",
            "type": "select",
            "options": ["booked", "tentative", "completed", "cancelled"],
        },
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
            "name": (ctx.get("session_name", "") or "").strip(),
            "artist": (ctx.get("artist", "") or "").strip(),
            "date": (ctx.get("session_date", "") or "").strip(),
            "time": time_range,
            "room": (ctx.get("room", "") or "").strip() or "—",
            "engineer": (ctx.get("engineer", "") or "").strip() or "—",
            "type": (ctx.get("session_type", "tracking") or "tracking").strip(),
            "status": (ctx.get("status", "booked") or "booked").strip(),
            "notes": (ctx.get("notes", "") or "").strip() or "—",
        }

        result = {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "result": {
                "action": "created",
                "session": session,
                "recommendations": [
                    "Prepare studio setup and signal chain.",
                    "Confirm artist references and tracking plan.",
                    "Check room availability and conflicting bookings.",
                    "Arrange catering or breaks if needed.",
                    "Sync session calendar and send reminders.",
                ],
            },
        }

        self.update_summary(
            filename="sessions.json",
            record={
                "session_name": session["name"],
                "artist": session["artist"],
                "session_date": session["date"],
                "engineer": session["engineer"],
                "room": session["room"],
                "status": session["status"],
            },
            key_field="session_name",
        )

        return result