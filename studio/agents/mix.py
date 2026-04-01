from __future__ import annotations

import json
import os
import requests
from datetime import datetime, timezone
from core.base_agent import BaseAgent


class MixAgent(BaseAgent):
    name = "MIX"
    department = "studio"
    description = "Strategy synthesiser — coordinates all studio agents."

    FIELDS = [
        {"key": "artist",    "label": "Artist / Project",  "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
        {"key": "goal",      "label": "Primary Goal",      "type": "textarea", "required": True,  "placeholder": "e.g. Plan a 3-day tracking session, generate a quote, and prep marketing for debut EP release"},
        {"key": "timeframe", "label": "Timeframe",         "type": "text",     "required": False, "placeholder": "e.g. Sessions start 2026-04-12"},
        {"key": "budget",    "label": "Budget",            "type": "number",   "required": False, "placeholder": "e.g. 5000"},
        {"key": "agents",    "label": "Agents to Include", "type": "text",     "required": False, "placeholder": "e.g. session, rate, signal — or leave blank for all"},
        {"key": "notes",     "label": "Notes",             "type": "textarea", "required": False, "placeholder": "Any context MIX should factor in"},
    ]

    def run(self, context: dict) -> dict:
        artist    = (context.get("artist") or "").strip()
        goal      = (context.get("goal") or "").strip()
        timeframe = (context.get("timeframe") or "").strip()
        budget    = context.get("budget", "")
        agents    = (context.get("agents") or "").strip()
        notes     = (context.get("notes") or "").strip()

        missing = [f for f, v in [("artist", artist), ("goal", goal)] if not v]
        if missing:
            # Consistently include .result and .context keys, even for error cases!
            return {
                "agent":      self.name,
                "department": self.department,
                "status":     "error",
                "error":      f"Missing required fields: {', '.join(missing)}",
                "context":    context,
                "result":     {
                    "artist": artist or "—",
                    "goal": goal or "—",
                    "timeframe": timeframe or "—",
                    "budget": budget or "—",
                    "agents": agents or "all",
                    "strategy": {},
                },
                "recommendations": [
                    "Provide artist name and a clear goal for MIX to synthesise a strategy.",
                    "Include timeframe and budget for a more complete strategic overview.",
                    "Name specific agents (session, rate, signal) or leave blank to consult all.",
                ],
            }

        mix_file = self.data_root / "mix_runs.json"
        runs = []
        if mix_file.exists():
            try:
                runs = json.loads(mix_file.read_text(encoding="utf-8"))
                if not isinstance(runs, list):
                    runs = []
            except Exception:
                runs = []

        now_iso = datetime.now(timezone.utc).isoformat()
        run_record = {
            "artist":    artist,
            "goal":      goal,
            "timeframe": timeframe,
            "budget":    budget,
            "agents":    agents,
            "notes":     notes,
            "created_at": now_iso,
        }
        runs.append(run_record)
        mix_file.write_text(
            json.dumps(runs, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        strategy = self._generate_strategy(run_record)

        return {
            "agent":      self.name,
            "department": self.department,
            "status":     "ok",
            "context":    context,
            "result": {
                "artist":    artist,
                "goal":      goal,
                "timeframe": timeframe or "—",
                "budget":    budget or "—",
                "agents":    agents or "all",
                "strategy":  strategy,
            },
        }

    def _generate_strategy(self, record: dict) -> dict:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback_strategy(record)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx  = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout  = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        prompt = f"""
You are MAESTRO MIX — a senior studio strategy synthesiser coordinating session planning,
pricing, marketing, and operations for a professional recording studio.

Produce a concise strategic plan for the following project.

Project details:
- Artist / Project: {record.get("artist", "")}
- Goal: {record.get("goal", "")}
- Timeframe: {record.get("timeframe", "")}
- Budget: {record.get("budget", "")}
- Agents to include: {record.get("agents", "all")}
- Notes: {record.get("notes", "")}

Structure your response as follows (plain text, no markdown headings):

OVERVIEW
One paragraph summary of the strategic approach.

SESSION
3 bullet points on session planning and scheduling.

RATE
3 bullet points on pricing and contract recommendations.

SIGNAL
3 bullet points on marketing and release strategy.

NEXT ACTIONS
5 immediate next actions numbered 1 to 5.

Be direct, practical, and specific to a professional recording studio context.
""".strip()

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model":   model,
                    "prompt":  prompt,
                    "stream":  False,
                    "options": {"num_ctx": num_ctx, "temperature": 0.65},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            text = (resp.json().get("response") or "").strip()
            return self._parse_strategy(text, record)
        except Exception as exc:
            s = self._fallback_strategy(record)
            s["llm_error"] = str(exc)
            return s

    def _parse_strategy(self, text: str, record: dict) -> dict:
        sections = {
            "overview": [],
            "session":  [],
            "rate":     [],
            "signal":   [],
            "next_actions": [],
        }
        current = None
        key_map = {
            "OVERVIEW": "overview",
            "SESSION":  "session",
            "RATE":     "rate",
            "SIGNAL":   "signal",
            "NEXT ACTIONS": "next_actions",
            "NEXT ACTION":  "next_actions",
        }
        for line in text.splitlines():
            stripped = line.strip()
            upper    = stripped.upper()
            matched  = next((v for k, v in key_map.items() if upper.startswith(k)), None)
            if matched:
                current = matched
                continue
            if current and stripped:
                sections[current].append(stripped.lstrip("•-–1234567890. \t"))

        # Fallback if parsing produced nothing useful
        if not any(sections.values()):
            return {"raw": text, **self._fallback_strategy(record)}

        return {
            "overview":     " ".join(sections["overview"]) or "See full strategy below.",
            "session":      sections["session"][:3]  or self._fallback_strategy(record)["session"],
            "rate":         sections["rate"][:3]     or self._fallback_strategy(record)["rate"],
            "signal":       sections["signal"][:3]   or self._fallback_strategy(record)["signal"],
            "next_actions": sections["next_actions"][:5] or self._fallback_strategy(record)["next_actions"],
        }

    def _fallback_strategy(self, record: dict) -> dict:
        artist    = record.get("artist", "the artist")
        budget    = str(record.get("budget") or "").strip()
        timeframe = record.get("timeframe", "")
        return {
            "overview": (
                f"Coordinate session booking, pricing, and campaign planning for {artist}. "
                f"{'Budget of ' + budget + ' should guide scope decisions. ' if budget else ''}"
                f"{'Target timeframe: ' + timeframe + '.' if timeframe else ''}"
            ),
            "session": [
                "Confirm room availability and engineer schedule before committing dates to the client.",
                "Book the session in stages — tracking first, mixing and mastering once tracking is approved.",
                "Send a session prep brief to the artist at least 5 days before the first date.",
            ],
            "rate": [
                "Generate a full itemised quote via the RATE agent before any verbal confirmation.",
                "Require a 50% deposit to confirm the booking — do not hold dates without it.",
                "Include cancellation terms: 25% retained within 14 days, 50% within 7 days.",
            ],
            "signal": [
                "Begin building content assets now — behind-the-scenes, studio process, and artist story.",
                "Plan a 4-week release campaign: tease, announce, pre-save, release, post-release push.",
                "Submit to Spotify editorial playlist consideration at least 7 days before the release date.",
            ],
            "next_actions": [
                "Run the SESSION agent to create and confirm the booking.",
                "Run the RATE agent to generate an itemised quote for the client.",
                "Run the CLIENT agent to log or update the client record.",
                "Run the SIGNAL agent to draft a campaign plan aligned to the release date.",
                "Run the SOUND agent to catalogue any existing tracks for rights and sync readiness.",
            ],
        }