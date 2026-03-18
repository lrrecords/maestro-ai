from __future__ import annotations

import json
import os
import requests
from datetime import datetime, timezone
from core.base_agent import BaseAgent


class ClientAgent(BaseAgent):
    name = "CLIENT"
    department = "studio"
    description = "Client relationship management, onboarding, and communication."

    FIELDS = [
        {
            "key": "client_name",
            "label": "Client Name",
            "type": "text",
            "placeholder": "e.g. Jordan Blake",
            "required": True,
        },
        {
            "key": "contact_person",
            "label": "Contact Person",
            "type": "text",
            "placeholder": "e.g. Alex Smith",
            "required": True,
        },
        {
            "key": "email",
            "label": "Email Address",
            "type": "text",
            "placeholder": "e.g. alex@example.com",
            "required": True,
        },
        {
            "key": "phone",
            "label": "Phone",
            "type": "text",
            "placeholder": "Optional",
            "required": False,
        },
        {
            "key": "company_label",
            "label": "Company/Label",
            "type": "text",
            "placeholder": "Optional",
            "required": False,
        },
        {
            "key": "relationship_type",
            "label": "Relationship Type",
            "type": "select",
            "options": ["artist", "label", "producer", "publisher", "manager", "other"],
            "required": True,
        },
        {
            "key": "budget",
            "label": "Budget",
            "type": "number",
            "placeholder": "Optional",
            "required": False,
        },
        {
            "key": "notes",
            "label": "Notes",
            "type": "textarea",
            "placeholder": "Special requirements or history",
            "required": False,
        },
    ]

    def run(self, context: dict) -> dict:
        """Load, create, or update client record, then generate recommendations."""
        client_name = context.get("client_name", "").strip()
        contact_person = context.get("contact_person", "").strip()
        email = context.get("email", "").strip().lower()
        phone = context.get("phone", "").strip()
        company_label = context.get("company_label", "").strip()
        relationship_type = context.get("relationship_type", "").strip()
        budget = context.get("budget", "")
        notes = context.get("notes", "").strip()

        missing = []
        if not client_name:
            missing.append("client_name")
        if not contact_person:
            missing.append("contact_person")
        if not email:
            missing.append("email")
        if not relationship_type:
            missing.append("relationship_type")

        if missing:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "error": f"Missing required fields: {', '.join(missing)}",
                "context": context,
                "recommendations": [
                    "Fill in all required fields before running CLIENT.",
                    "Include relationship type so onboarding suggestions can be tailored.",
                    "Add notes or budget for more useful recommendations.",
                ],
            }

        # Load existing clients
        clients_file = self.data_root / "clients.json"
        clients = []
        if clients_file.exists():
            try:
                clients = json.loads(clients_file.read_text(encoding="utf-8"))
                if not isinstance(clients, list):
                    clients = []
            except Exception:
                clients = []

        # Find or create
        existing = next((c for c in clients if c.get("email") == email), None)
        now_iso = datetime.now(timezone.utc).isoformat()

        client_record = {
            "client_name": client_name,
            "contact_person": contact_person,
            "email": email,
            "phone": phone,
            "company_label": company_label,
            "relationship_type": relationship_type,
            "budget": budget,
            "notes": notes,
        }

        if existing:
            existing.update(client_record)
            existing["updated_at"] = now_iso
            action = "updated"
            saved_record = existing
        else:
            client_record["created_at"] = now_iso
            clients.append(client_record)
            action = "created"
            saved_record = client_record

        # Save
        clients_file.write_text(
            json.dumps(clients, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Generate recommendations via Ollama
        recommendations = self._generate_recommendations(saved_record)

        return {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "context": context,
            "result": {
                "action": action,
                "client": {
                    "name": client_name,
                    "contact": contact_person,
                    "email": email,
                    "phone": phone or "—",
                    "company": company_label or "—",
                    "relationship": relationship_type,
                    "budget": budget or "—",
                    "notes": notes or "—",
                },
                "recommendations": recommendations,
            },
        }

    def _generate_recommendations(self, client_record: dict) -> list[str]:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback_recommendations(client_record)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        prompt = self._build_prompt(client_record)

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": num_ctx,
                        "temperature": 0.6,
                    },
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            text = (data.get("response") or "").strip()
            parsed = self._parse_recommendations(text)
            return parsed or self._fallback_recommendations(client_record)
        except Exception as exc:
            return self._fallback_recommendations(client_record) + [
                f"LLM unavailable; using fallback recommendations. ({exc})"
            ]

    def _build_prompt(self, client_record: dict) -> str:
        return f"""
You are a studio operations assistant.

Generate practical onboarding recommendations for a recording studio client.

Client details:
- Client name: {client_record.get("client_name", "")}
- Contact person: {client_record.get("contact_person", "")}
- Relationship type: {client_record.get("relationship_type", "")}
- Company/Label: {client_record.get("company_label", "")}
- Budget: {client_record.get("budget", "")}
- Notes: {client_record.get("notes", "")}

Return exactly:
- A short intro sentence
- Then 5 bullet recommendations
- Then 3 suggested next actions

Keep it concise, practical, and specific to studio onboarding, communication, scheduling, budgeting, and expectations.
Do not use markdown headings.
""".strip()

    def _parse_recommendations(self, text: str) -> list[str]:
        lines = [line.strip("•- \t") for line in text.splitlines() if line.strip()]
        return lines[:9] if lines else []

    def _fallback_recommendations(self, client_record: dict) -> list[str]:
        relationship = (client_record.get("relationship_type") or "").lower()
        budget = str(client_record.get("budget") or "").strip()
        notes = (client_record.get("notes") or "").strip()

        recs = [
            "Send a welcome email confirming the studio’s process, timelines, and key contact details.",
            "Collect reference tracks, project goals, and technical requirements before booking sessions.",
            "Confirm session scope, deliverables, and revision expectations in writing.",
        ]

        if relationship == "artist":
            recs.append("Ask about creative vision, influences, and release goals to shape the onboarding plan.")
        elif relationship == "label":
            recs.append("Clarify approval workflow, decision-makers, and reporting expectations with the label team.")
        elif relationship == "producer":
            recs.append("Align early on session workflow, file handoff structure, and production responsibilities.")
        elif relationship == "publisher":
            recs.append("Confirm rights, splits, and metadata delivery requirements before project kickoff.")
        elif relationship == "manager":
            recs.append("Set communication cadence and approval checkpoints with management from the outset.")

        if budget:
            recs.append(f"Use the stated budget ({budget}) to frame a realistic scope and session plan.")

        if notes:
            recs.append("Review the client notes carefully and flag any special requirements before confirming dates.")

        recs.append("Prepare a simple onboarding checklist covering contacts, files, dates, and payment terms.")
        return recs[:7]