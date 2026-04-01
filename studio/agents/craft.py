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
        {"key": "trigger",   "label": "Trigger",            "type": "select",   "options": ["manual", "scheduled", "webhook", "event-driven", "other"]},
        {"key": "owner",     "label": "Owner",              "type": "text",     "placeholder": "e.g. Brett"},
        {"key": "stack",     "label": "Tech Stack",         "type": "text",     "placeholder": "e.g. Python, Flask, n8n"},
        {"key": "status",    "label": "Status",             "type": "select",   "options": ["idea", "in_progress", "active", "deprecated"]},
        {"key": "notes",     "label": "Notes",              "type": "textarea", "placeholder": "Links, dependencies, known issues"},
    ]

    def run(self, context: dict) -> dict:
        ctx = context or {}
        tool_name = (ctx.get("tool_name") or "").strip()
        purpose   = (ctx.get("purpose")   or "").strip()
        trigger   = (ctx.get("trigger")   or "manual").strip()
        owner     = (ctx.get("owner")     or "").strip()
        stack     = (ctx.get("stack")     or "").strip()
        status    = (ctx.get("status")    or "idea").strip()
        notes     = (ctx.get("notes")     or "").strip()

        missing = [field for field, val in [("tool_name", tool_name), ("purpose", purpose)] if not val]
        if missing:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "error": f"Missing required fields: {', '.join(missing)}",
                "context": context,
                "result": {
                    "action": "error",
                    "tool": {},
                    "recommendations": [
                        "Provide both a tool name and purpose to record a CRAFT tooling entry.",
                        "Describe the problem clearly; this becomes the brief for future automation.",
                        "Add a tech stack if known, to help future maintainers.",
                    ]
                }
            }

        tools_file = self.data_root / "tools.json"
        tools = []
        if tools_file.exists():
            try:
                tools = json.loads(tools_file.read_text(encoding="utf-8"))
                if not isinstance(tools, list): tools = []
            except Exception:
                tools = []

        # Support updates/overwrite on matching tool_name
        existing = next((t for t in tools if t.get("tool_name") == tool_name), None)
        now_iso  = datetime.now(timezone.utc).isoformat()
        tool_record = {
            "tool_name": tool_name,
            "purpose":   purpose,
            "trigger":   trigger,
            "owner":     owner,
            "stack":     stack,
            "status":    status,
            "notes":     notes,
        }
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

        tools_file.write_text(json.dumps(tools, indent=2, ensure_ascii=False), encoding="utf-8")

        # Build audit/history (last 5 runs for same owner or status, for context or UI audit)
        audit_trail = [
            {k: v for k, v in t.items() if k not in ("notes", "created_at", "updated_at")}
            for t in tools if (t.get("owner") == owner and owner) or t.get("status") == status
        ][-5:]

        recommendations = self._generate_recommendations(saved_record, audit_trail)

        return {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "context": context,
            "result": {
                "action": action,
                "tool": {
                    "tool_name": tool_name,
                    "purpose": purpose,
                    "trigger": trigger,
                    "owner": owner or "—",
                    "stack": stack or "—",
                    "status": status,
                    "notes": notes or "—",
                    "created_at": saved_record.get("created_at"),
                    "updated_at": saved_record.get("updated_at", ""),
                },
                "recommendations": recommendations,
                "audit_trail": audit_trail if audit_trail else [],
                "saved_to": str(tools_file),
            },
        }

    def _generate_recommendations(self, record: dict, audit_trail: list) -> list[str]:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback(record, audit_trail)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx  = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout  = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        # Optionally include audit context for the LLM
        audit_lines = ""
        if audit_trail:
            audit_lines = "\n- Recent similar tools: " + "; ".join(t.get("tool_name", "") for t in audit_trail if t.get("tool_name"))
        prompt = f"""
You are a software tooling and workflow automation advisor for a recording studio.

Generate practical build and deployment recommendations for this internal tool.
{audit_lines}

Tool details:
- Name: {record.get("tool_name", "")}
- Purpose: {record.get("purpose", "")}
- Trigger: {record.get("trigger", "")}
- Owner: {record.get("owner", "")}
- Tech stack: {record.get("stack", "")}
- Status: {record.get("status", "")}
- Notes: {record.get("notes", "")}

Return in this order:
- One short intro sentence.
- Five actionable bullet recommendations (covering build approach, reliability, maintenance, documentation, use of audit trail if helpful).
- Three prioritized next actions.

Plain text only, no markdown headings.
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
            # Parse to separate intro, recs, and actions
            lines = [l.strip("•- \t") for l in text.splitlines() if l.strip()]
            return lines[:9] or self._fallback(record, audit_trail)
        except Exception as exc:
            return self._fallback(record, audit_trail) + [f"LLM unavailable; using fallback. ({exc})"]

    def _fallback(self, record: dict, audit_trail: list) -> list[str]:
        status  = (record.get("status") or "idea").lower()
        trigger = (record.get("trigger") or "manual").lower()
        stack   = (record.get("stack") or "").lower()
        recs = [
            "Write a one-paragraph brief for the tool before writing a single line of code.",
            "Define success criteria upfront — what does 'working correctly' look like?",
            "Keep the tool single-purpose to minimize bugs during automation.",
        ]
        if status == "idea":
            recs.append("Validate the idea by mapping the current manual process step by step first.")
        elif status == "in_progress":
            recs.append("Set a hard MVP deadline — ship a working minimal version before adding features.")
        elif status == "active":
            recs.append("Document the tool's inputs, outputs, and error states for future maintainers.")
        elif status == "deprecated":
            recs.append("Archive the tool's code and document why it was deprecated for future reference.")
        if trigger == "scheduled":
            recs.append("Add logging and alerting so failures in scheduled runs are caught immediately.")
        if "python" in stack:
            recs.append("Pin all dependency versions in requirements.txt to avoid breakage on future installs.")
        recs.append("Store even small scripts in version control from day one.")
        if audit_trail:
            recs.append("Review recent similar tools to avoid duplication and leverage learnings.")
        return recs[:9]