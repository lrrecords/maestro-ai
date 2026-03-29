# live/agents/book.py
import os, json
from datetime import datetime, timezone
from core.base_agent import BaseAgent

class BookAgent(BaseAgent):
    department  = "live"
    name        = "BOOK"
    description = "Venues, holds, deal negotiation, contract tracking."

    FIELDS = [
        {"key": "artist",    "label": "Artist",        "type": "text",   "placeholder": "e.g. Bicep",               "required": True},
        {"key": "dates",     "label": "Target Dates",  "type": "tags",   "placeholder": "e.g. 2026-04-02, 2026-04-15", "required": True},
        {"key": "capacity",  "label": "Min. Capacity", "type": "number", "placeholder": "e.g. 500"},
        {"key": "territory", "label": "Territory",     "type": "text",   "placeholder": "e.g. UK"},
        {"key": "deal_type", "label": "Deal Type",     "type": "select", "options": ["flat", "versus", "guarantee"], "required": True},
        {"key": "notes",     "label": "Notes",         "type": "textarea", "placeholder": "Constraints, dream venues, supports..."},
    ]

    def run(self, context: dict) -> dict:
        ctx = context or {}
        # Validation
        errors = [k for k in ("artist", "dates", "deal_type") if not ctx.get(k)]
        if errors:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "error": f"Missing required fields: {', '.join(errors)}",
                "context": context,
                "result": {
                    "action": "error",
                    "booking": {},
                    "recommendations": [
                        "Fill all required fields: artist, dates, deal type.",
                        "Add territory/capacity/notes for more tailored results.",
                    ]
                }
            }

        booking = {
            "artist": ctx.get("artist", "").strip(),
            "dates": [d.strip() for d in (ctx.get("dates") or []) if d.strip()],
            "capacity": ctx.get("capacity") or "—",
            "territory": ctx.get("territory") or "—",
            "deal_type": ctx.get("deal_type") or "—",
            "notes": ctx.get("notes") or "—"
        }

        # Write to audit
        file = self.data_root / "booking_history.json"
        bookings = []
        if file.exists():
            try:
                bookings = json.loads(file.read_text(encoding="utf-8"))
                if not isinstance(bookings, list): bookings = []
            except Exception:
                bookings = []
        now_iso = datetime.now(timezone.utc).isoformat()
        record = {**booking, "created_at": now_iso}
        bookings.append(record)
        file.write_text(json.dumps(bookings, indent=2, ensure_ascii=False), encoding="utf-8")

        # Last runs as audit trail
        audit_trail = bookings[-5:]

        # Recommendations placeholder — wire in LLM when ready
        recommendations = [
            "Double-check availability for all requested dates before sending holds.",
            "Clarify deal type (flat/versus/guarantee) to align artist/promoter expectations up front.",
            "Record all offers and counter-offers for audit trail and deal reporting.",
        ]

        return {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "context": context,
            "result": {
                "action": "created",
                "booking": booking,
                "recommendations": recommendations,
                "audit_trail": audit_trail,
                "saved_to": str(file),
            }
        }