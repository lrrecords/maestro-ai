from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.llm_client import call_llm


class BaseAgent:
    name = "BASE"
    department = "core"
    description = ""
    FIELDS: list[dict[str, Any]] = []

    def __init__(self, *args, **kwargs):
        cfg = args[0] if args and isinstance(args[0], dict) else {}

        # NOTE: subclasses (e.g. ScribeAgent) call
        #   super().__init__(name=..., department=..., role=..., system_prompt=..., job_store=...)
        # Previously these kwargs landed in **kwargs and were silently
        # discarded — the subclass never actually got self.department,
        # self.role, or (critically) self.system_prompt set. Map them
        # explicitly here so any agent's system prompt reaches BaseAgent.llm().
        self.agent_name = (
            kwargs.get("agent_name")
            or kwargs.get("name")
            or cfg.get("agent_name")
            or cfg.get("name")
            or getattr(self, "name", self.__class__.__name__.replace("Agent", "").upper())
        )
        self.department = (
            kwargs.get("department")
            or cfg.get("department")
            or getattr(self, "department", "core")
        )
        self.role = kwargs.get("role") or cfg.get("role") or getattr(self, "role", "")
        self.system_prompt = (
            kwargs.get("system_prompt")
            or cfg.get("system_prompt")
            or getattr(self, "system_prompt", None)
        )
        # Some agents pass job_store to BaseAgent.__init__ even though they
        # also stash it themselves right after super().__init__() returns.
        # Set it here too so it's available even if a subclass forgets to.
        if "job_store" in kwargs and getattr(self, "job_store", None) is None:
            self.job_store = kwargs["job_store"]

        data_root = kwargs.get("data_root", cfg.get("data_root"))
        if data_root is None and args:
            first = args[0]
            if isinstance(first, (str, Path)):
                data_root = first
            elif hasattr(first, "data_root"):
                data_root = getattr(first, "data_root")

        self.data_root = Path(data_root) if data_root else Path("studio") / "data"
        self.data_root.mkdir(parents=True, exist_ok=True)

    def run(self, context: dict) -> dict:
        raise NotImplementedError("Agent must implement run(context).")

    def llm(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """
        Send prompt through the centralized LLM client.

        Notes:
        - Uses core.llm_client.call_llm(), which honors env vars and PLATFORM OPS settings.
        - `system` defaults to self.system_prompt (set via BaseAgent.__init__) when not
          passed explicitly, and is forwarded to call_llm() as a native system prompt
          (Anthropic's `system` field / a leading `role: system` message elsewhere) —
          it is no longer silently dropped or hand-concatenated into the user prompt.
        - `model` is still accepted for call-site compatibility; call_llm() currently
          selects the model from env/PLATFORM settings rather than per-call.
        """
        if system is None:
            system = self.system_prompt

        text = call_llm(prompt, max_tokens=2048, system=system, temperature=temperature)

        if os.getenv("MAESTRO_DEBUG_LLM") == "1":
            self._save_debug_raw(text)

        if not text:
            raise RuntimeError("LLM returned empty response")

        return text

    def parse_json(self, raw: str, required_keys: list[str] | None = None):
        """
        Extract and parse a JSON object/array from raw LLM output.

        required_keys: when given and the parsed result is a dict, every key
            in this list must be present, otherwise a ValueError is raised.
            This is opt-in schema validation (Only Institute review: "parse_json
            accepts ANY JSON-like structure ... no schema validation against
            expected fields") — callers that know what shape they expect back
            should pass it; callers that intentionally accept loosely-shaped
            output (e.g. SCRIBE's normalize_topics, which exists precisely to
            tolerate several different LLM output shapes) can leave it unset.
        """
        if raw is None:
            raise ValueError("parse_json received None")
        text = raw.strip()

        text = re.sub(r"^\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text).strip()

        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            pass

        if parsed is None:
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
                        parsed = json.loads(chunk)
                        break
            else:
                raise ValueError(f"Incomplete JSON in model output: {text[:300]}")

        if required_keys:
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Expected a JSON object with keys {required_keys!r}, "
                    f"got {type(parsed).__name__}: {str(parsed)[:300]}"
                )
            missing = [k for k in required_keys if k not in parsed]
            if missing:
                raise ValueError(
                    f"Model output JSON is missing required keys {missing!r}: {str(parsed)[:300]}"
                )

        return parsed

    def call_llm_json(
        self,
        prompt: str,
        required_keys: list[str],
        system: str | None = None,
        retry_note: str | None = None,
    ):
        raw = self.llm(prompt, system=system)
        self._last_llm_json_raws = [raw]
        try:
            return self.parse_json(raw, required_keys=required_keys)
        except ValueError as exc:
            correction = retry_note or (
                f"Your previous response was invalid: {exc}. "
                f"Return valid JSON with ALL of these keys: {required_keys}."
            )
            retry_prompt = f"{prompt}\n\n{correction}"
            retry_raw = self.llm(retry_prompt, system=system)
            self._last_llm_json_raws.append(retry_raw)
            return self.parse_json(retry_raw, required_keys=required_keys)

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