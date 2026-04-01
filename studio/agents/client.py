from pathlib import Path
from datetime import datetime, timezone
import json
from core.base_agent import BaseAgent

class ClientAgent(BaseAgent):
    name = "CLIENT"
    department = "studio"
    description = "Client relationship management, onboarding, and communication."

    FIELDS = [
        {"key": "client_name",       "label": "Client Name",       "type": "text",    "required": True,  "placeholder": "e.g. Jordan Blake"},
        {"key": "contact_person",    "label": "Contact Person",    "type": "text",    "placeholder": "e.g. Alex Lee"},
        {"key": "email",             "label": "Email",             "type": "email",   "required": True,  "placeholder": "e.g. artist@email.com"},
        {"key": "genre",             "label": "Genre / Focus",     "type": "text",    "placeholder": "e.g. Indie Rock"},
        {"key": "relationship_type", "label": "Relationship Type", "type": "select",
            "options": ["artist", "producer", "manager", "label", "studio"], "required": True},
        {"key": "company_label",     "label": "Company / Label",   "type": "text",    "placeholder": "e.g. Good Vibes Music"},
        {"key": "budget",            "label": "Budget (GBP)",      "type": "number",  "placeholder": "e.g. 1200"},
        {"key": "notes",             "label": "Notes",             "type": "textarea","placeholder": "Any context or requirements"},
    ]

    def run(self, context: dict) -> dict:
        ctx = context or {}

        # --- Required field checking ---
        requireds = [
            ("client_name", ctx.get("client_name", "")),
            ("email", ctx.get("email", "")),
            ("relationship_type", ctx.get("relationship_type", "")),
        ]
        missing = [k for k, v in requireds if not v]
        if missing:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "error": f"Missing required fields: {', '.join(missing)}",
                "context": context,
                "result": {
                    "client": {},
                    "action": "error",
                    "recommendations": [
                        "Fill all required fields before running CLIENT.",
                        "Include relationship type so onboarding suggestions can be tailored.",
                        "Add budget or notes for more useful recommendations."
                    ]
                }
            }

        # --- Normalize fields ---
        try:
            budget = float(ctx.get("budget") or 0)
        except (TypeError, ValueError):
            budget = 0.0

        client = {
            "name": (ctx.get("client_name", "") or "").strip(),
            "contact": (ctx.get("contact_person", "") or "").strip() or "—",
            "email": (ctx.get("email", "") or "").strip(),
            "genre": (ctx.get("genre", "") or "").strip() or "—",
            "type": (ctx.get("relationship_type", "artist") or "artist").strip(),
            "company_label": (ctx.get("company_label", "") or "").strip() or "—",
            "budget": budget,
            "notes": (ctx.get("notes", "") or "").strip() or "—",
            "status": "active",
        }

        # --- Logging for audit/history (optional/uncomment if you want) ---
        clients_file = self.data_root / "clients.json"
        clients = []
        if clients_file.exists():
            try:
                clients = json.loads(clients_file.read_text(encoding="utf-8"))
                if not isinstance(clients, list): clients = []
            except Exception:
                clients = []
        
        # De-duplicate by email
        already = next((c for c in clients if c.get("email") == client["email"]), None)
        now_iso = datetime.now(timezone.utc).isoformat()
        if already:
            already.update(client)
            already["updated_at"] = now_iso
            action = "updated"
        else:
            client["created_at"] = now_iso
            clients.append(client)
            action = "created"
        clients_file.write_text(json.dumps(clients, indent=2, ensure_ascii=False), encoding="utf-8")

        # --- Return robust, UI+API safe structure ---
        return {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "context": context,
            "result": {
                "client": client,
                "action": action,
                "recommendations": [
                    "Send welcome email and onboarding pack.",
                    "Create client folder and permissions.",
                    "Schedule initial kickoff call.",
                    "Add client to CRM and calendar.",
                    "Confirm project scope and first milestone.",
                ],
            }
        }