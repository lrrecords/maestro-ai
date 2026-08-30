"""core/llm_audit.py
RASCALWORKS OS — lightweight audit log for LLM calls.

Every call to core.llm_client.call_llm() appends one JSON line to
data/llm_audit/<date>.jsonl recording the provider, the model that actually
responded, the sampling params, the prompt, the response, and a content
hash of each. This is a forensic/replay trail, not a validator — it exists
so a specific run can be reconstructed and inspected after the fact.

This addresses (partially) the "Only Institute Review of Rascalworks OS"
findings:
  - TC-006 Audit Log Completeness: prompt+response pairs are now persisted.
  - TC-007 Provenance Traceability: each record carries a sha256 of the
    prompt and response for content-integrity checks.
  - TC-011 Explanation & Decision Traceability: the model that actually
    responded (after any provider-side fallback) is recorded, not just the
    model that was requested.

It intentionally does NOT depend on Redis/JobStore — agents that never see
a JobStore (or run outside Flask entirely, e.g. scripts/) still get an
audit trail. Failures to write the audit log are swallowed (logged, not
raised) so a disk/permissions problem never breaks an agent call.

Data written here can include full prompts/response text, which may
contain business-sensitive content — data/llm_audit/ is excluded from git
via the existing blanket `data/**` .gitignore rule (nothing needed to add).
Set LLM_AUDIT_LOG=0 to disable entirely (e.g. in constrained CI runners).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AUDIT_DIR = Path(__file__).resolve().parents[1] / "data" / "llm_audit"


def _enabled() -> bool:
    return os.getenv("LLM_AUDIT_LOG", "1") != "0"


def _sha256(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def log_call(
    *,
    provider: str,
    model: str | None,
    system: str | None,
    prompt: str,
    response: str | None,
    temperature: float | None,
    seed: int | None,
    max_tokens: int,
    duration_s: float,
    error: str | None = None,
) -> None:
    """Append one audit record. Never raises — logs and swallows on failure."""
    if not _enabled():
        return
    try:
        ts = datetime.now(timezone.utc)
        record: dict[str, Any] = {
            "timestamp": ts.isoformat(),
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "max_tokens": max_tokens,
            "duration_s": round(duration_s, 3),
            "system": system,
            "prompt": prompt,
            "response": response,
            "error": error,
            "prompt_sha256": _sha256(prompt),
            "response_sha256": _sha256(response),
        }
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        path = AUDIT_DIR / f"{ts.strftime('%Y-%m-%d')}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("Failed to write LLM audit log entry (call itself succeeded)")
