from pathlib import Path
from core.base_agent import BaseAgent


class ClientAgent(BaseAgent):
    name = "CLIENT"
    department = "studio"
    description = "Client relationship management, onboarding, and communication."

    FIELDS = [
        {"key": "client_name", "label": "Client name", "type": "text", "required": True},
        {"key": "contact_person", "label": "Contact person", "type": "text"},
        {"key": "email", "label": "Email", "type": "email", "required": True},
        {"key": "genre", "label": "Genre / focus", "type": "text"},
        {
            "key": "relationship_type",
            "label": "Relationship type",
            "type": "select",
            "options": ["artist", "producer", "manager", "label", "studio"],
        },
        {"key": "company_label", "label": "Company / Label", "type": "text"},
        {"key": "budget", "label": "Budget (GBP)", "type": "number"},
        {"key": "notes", "label": "Notes", "type": "textarea"},
    ]

    def __init__(self, data_root: str | Path | None = None):
        self.agent_name = self.name
        self.data_root = Path(data_root) if data_root else Path("studio") / "data"
        self.ollama_base_url = "http://localhost:11434"
        self.ollama_model = "llama3"
        self.data_root.mkdir(parents=True, exist_ok=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    

    def run(self, context: dict) -> dict:
        ctx = context or {}

        raw_budget = ctx.get("budget", 0)
        try:
            budget = float(raw_budget or 0)
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

        result = {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "result": {
                "action": "created",
                "client": client,
                "recommendations": [
                    "Send welcome email and onboarding pack.",
                    "Create client folder and permissions.",
                    "Schedule initial kickoff call.",
                    "Add client to CRM and calendar.",
                    "Confirm project scope and first milestone.",
                ],
            },
        }

        self.update_summary(
            filename="clients.json",
            record={
                "client_name": client["name"],
                "contact_person": client["contact"],
                "email": client["email"],
                "relationship_type": client["type"],
                "company_label": client["company_label"],
            },
            key_field="client_name",
        )

        return result