from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


class BaseAgent:
    name = "BASE"
    department = "core"
    description = ""
    FIELDS: list[dict[str, Any]] = []

    def __init__(self, *args, **kwargs):
        cfg = args[0] if args and isinstance(args[0], dict) else {}

        self.agent_name = kwargs.get(
            "agent_name",
            cfg.get("agent_name", getattr(self, "name", self.__class__.__name__.replace("Agent", "").upper())),
        )

        data_root = kwargs.get("data_root", cfg.get("data_root"))
        if data_root is None and args:
            first = args[0]
            if isinstance(first, (str, Path)):
                data_root = first
            elif hasattr(first, "data_root"):
                data_root = getattr(first, "data_root")

        self.data_root = Path(data_root) if data_root else Path("studio") / "data"
        self.data_root.mkdir(parents=True, exist_ok=True)

        self.ollama_base_url = kwargs.get(
            "ollama_base_url",
            cfg.get("ollama_base_url", os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")),
        )
        self.ollama_model = kwargs.get(
            "ollama_model",
            cfg.get("ollama_model", os.getenv("OLLAMA_MODEL", "llama3.1:8b")),
        )

    def run(self, context: dict) -> dict:
        raise NotImplementedError("Agent must implement run(context).")

    def llm(self, prompt: str, system: str | None = None, model: str | None = None) -> str:
        payload = {
            "model": model or self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        if system:
            payload["system"] = system

        url = f"{self.ollama_base_url.rstrip('/')}/api/generate"
        r = requests.post(url, json=payload, timeout=90)
        r.raise_for_status()
        data = r.json()
        text = (data.get("response") or "").strip()

        if os.getenv("MAESTRO_DEBUG_LLM") == "1":
            self._save_debug_raw(text)

        if not text:
            raise RuntimeError("LLM returned empty response")
        return text

    def parse_json(self, raw: str):
        if raw is None:
            raise ValueError("parse_json received None")
        text = raw.strip()

        text = re.sub(r"^\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
        if not starts:
            raise ValueError(f"No JSON found in model output: {text[:300]}")

        start = min(starts)
        opener = text[start]
        closer = "}" if opener == "{" else "]"

        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    chunk = text[start : i + 1]
                    return json.loads(chunk)

        raise ValueError(f"Incomplete JSON in model output: {text[:300]}")

    def save_output(self, result: dict, slug: str | None = None) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_slug = (slug or "run").strip().replace(" ", "-")
        folder = self.data_root / self.agent_name.lower()
        folder.mkdir(parents=True, exist_ok=True)

        path = folder / f"{self.agent_name.lower()}_{safe_slug}_{ts}.json"
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def update_summary(self, filename: str, record: dict, key_field: str | None = None):
        path = self.data_root / filename
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except FileNotFoundError:
            data = []
        except json.JSONDecodeError:
            data = []

        if key_field and key_field in record:
            data = [d for d in data if not isinstance(d, dict) or d.get(key_field) != record.get(key_field)]

        data.append(record)

        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _save_debug_raw(self, raw_text: str):
        dbg_dir = self.data_root / "_debug"
        dbg_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = dbg_dir / f"{self.agent_name.lower()}_raw_{ts}.txt"
        path.write_text(raw_text or "", encoding="utf-8")