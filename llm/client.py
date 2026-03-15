"""
llm/client.py (top-level compat shim)

Allows `from llm.client import ...` to work when running from repo root
(without adding `scripts/` to sys.path).

Implementation lives in `core.llm_client`.
"""

from __future__ import annotations

import requests  # noqa: F401

from core.llm_client import (  # noqa: F401
    get_provider,
    call_llm,
    _call_anthropic,
    _call_ollama,
)

__all__ = [
    "get_provider",
    "call_llm",
    "_call_anthropic",
    "_call_ollama",
]