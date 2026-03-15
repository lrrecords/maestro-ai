"""
scripts/llm/client.py (compat shim)

Legacy code/tests import `llm.client` by adding `scripts/` to sys.path.
The real implementation lives in `core.llm_client`.

Compatibility requirements:
- Keep names: get_provider, call_llm, _call_anthropic, _call_ollama
- Keep `requests` import available so tests can patch `llm.client.requests.post`
"""

from __future__ import annotations

# Keep `requests` bound in this module so tests can patch `llm.client.requests.post`.
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