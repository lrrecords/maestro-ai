from __future__ import annotations

import json
import os
import requests
from datetime import datetime, timezone
from core.base_agent import BaseAgent


class CraftAgent(BaseAgent):
    name = "CRAFT"
    department = "studio"
    description = "Internal tooling and workflow automation."

    FIELDS = [
        {"key": "tool_name", "label": "Tool / Script Name", "type": "text",     "required": True,  "placeholder": "e.g. Invoice Generator"},
        {"key": "purpose",   "label": "Purpose",            "type": "textarea", "required": True,  "placeholder": "What problem does this tool solve?"},
        {"key": "trigger",   "label": "Trigger",            "type": "select",   "required": False,
         "options": ["manual", "scheduled", "webhook", "event-driven", "other"]},
        {"key": "owner",     "label": "Owner",              "type": "text",     "required": False, "placeholder": "e.g. Brett"},
        {"key": "stack",     "label": "Tech Stack",         "type": "text",     "required": False, "placeholder": "e.g. Python, Flask, n8n"},
        {"key": "status",    "label": "Status",             "type": "select",   "required": False,
         "options": ["idea", "in_progress", "active", "deprecated"]},
        {"key": "notes",     "label": "Notes",              "type": "textarea", "required": False, "placeholder": "Links, dependencies, known issues"},
    ]

    def run(self, context: dict) -> dict:
        tool_name = context.get("tool_name", "").strip()
        purpose   = context.get("purpose",   "").strip()
        trigger   = context.get("trigger",   "manual").strip()
        owner     = context.get("owner",     "").strip()
        stack     = context.get("stack",     "").strip()
        status    = context.get("status",    "idea").strip()
        notes     = context.get("notes",     "").strip()

        missing = [f for f, v in [
            ("tool_name", tool_name),
            ("purpose",   purpose),
        ] if not v]

        if missing:
            return {
                "agent":      self.name,
                "department": self.department,
                "status":     "error",
                "error":      f"Missing required fields: {', '.join(missing)}",
                "context":    context,
                "recommendations": [
                    "Provide a tool name and purpose to log a CRAFT entry.",
                    "Describe the problem clearly — this becomes the brief for building the tool.",
                    "Add the tech stack if known so dependencies can be assessed early.",
                ],
            }

        tools_file = self.data_root / "tools.json"
        tools = []
        if tools_file.exists():
            try:
                tools = json.loads(tools_file.read_text(encoding="utf-8"))
                if not isinstance(tools, list):
                    tools = []
            except Exception:
                tools = []

        now_iso = datetime.now(timezone.utc).isoformat()
        tool_record = {
            "tool_name": tool_name,
            "purpose":   purpose,
            "trigger":   trigger,
            "owner":     owner,
            "stack":     stack,
            "status":    status,
            "notes":     notes,
        }

        existing = next(
            (t for t in tools if t.get("tool_name") == tool_name),
            None,
        )

        if existing:
            existing.update(tool_record)
            existing["updated_at"] = now_iso
            action = "updated"
            saved_record = existing
        else:
            tool_record["created_at"] = now_iso
            tools.append(tool_record)
            action = "created"
            saved_record = tool_record

        tools_file.write_text(
            json.dumps(tools, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        recommendations = self._generate_recommendations(saved_record)

        return {
            "agent":      self.name,
            "department": self.department,
            "status":     "ok",
            "context":    context,
            "result": {
                "action": action,
                "tool": {
                    "name":    tool_name,
                    "purpose": purpose,
                    "trigger": trigger,
                    "owner":   owner or "—",
                    "stack":   stack or "—",
                    "status":  status,
                    "notes":   notes or "—",
                },
                "recommendations": recommendations,
            },
        }

    def _generate_recommendations(self, record: dict) -> list[str]:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback(record)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx  = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout  = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        prompt = f"""
You are a software tooling and workflow automation advisor for a recording studio.

Generate practical build and deployment recommendations for this internal tool.

Tool details:
- Name: {record.get("tool_name", "")}
- Purpose: {record.get("purpose", "")}
- Trigger: {record.get("trigger", "")}
- Owner: {record.get("owner", "")}
- Tech stack: {record.get("stack", "")}
- Status: {record.get("status", "")}
- Notes: {record.get("notes", "")}

Return:
- A short intro sentence
- 5 bullet recommendations covering build approach, reliability, maintenance, and documentation
- 3 suggested next actions

Be concise and practical. Do not use markdown headings.
""".strip()

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model":   model,
                    "prompt":  prompt,
                    "stream":  False,
                    "options": {"num_ctx": num_ctx, "temperature": 0.6},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            text = (resp.json().get("response") or "").strip()
            lines = [l.strip("•- \t") for l in text.splitlines() if l.strip()]
            return lines[:9] or self._fallback(record)
        except Exception as exc:
            return self._fallback(record) + [f"LLM unavailable; using fallback. ({exc})"]

    def _fallback(self, record: dict) -> list[str]:
        status  = (record.get("status") or "idea").lower()
        trigger = (record.get("trigger") or "manual").lower()
        stack   = (record.get("stack") or "").lower()
        recs = [
            "Write a one-paragraph brief for the tool before writing a single line of code.",
            "Define success criteria upfront — what does 'working correctly' look like?",
            "Keep the tool single-purpose; resist scope creep during the build phase.",
        ]
        if status == "idea":
            recs.append("Validate the idea by mapping the current manual process step by step first.")
        elif status == "in_progress":
            recs.append("Set a hard MVP deadline — ship a working minimal version before adding features.")
        elif status == "active":
            recs.append("Document the tool's inputs, outputs, and failure modes for anyone who maintains it later.")
        elif status == "deprecated":
            recs.append("Archive the tool's code and document why it was deprecated for future reference.")
        if trigger == "scheduled":
            recs.append("Add logging and alerting so failures in scheduled runs are caught immediately.")
        if "python" in stack:
            recs.append("Pin all dependency versions in requirements.txt to avoid breakage on future installs.")
        recs.append("Store the tool in version control from day one, even for small scripts.")
        return recs[:7]