"""scripts/llm/client.py
MAESTRO AI — LLM provider abstraction.

Routes agent prompts to either Anthropic Claude or a local Ollama server,
selected via the PLATFORM settings (or env var LLM_PROVIDER).

Supported providers:
  anthropic  — Anthropic Claude API (requires ANTHROPIC_API_KEY)
  ollama     — Local Ollama HTTP server (requires Ollama running locally)

Usage:
    from llm.client import call_llm

    text = call_llm(prompt, max_tokens=2048)
"""

import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# Path to PLATFORM settings (repo root / platform / data / platform_settings.json)
PLATFORM_SETTINGS_PATH = (
    Path(__file__).resolve().parents[2]
    / "platform"
    / "data"
    / "platform_settings.json"
)

def _plat_settings() -> dict:
    """Load PLATFORM settings from JSON, fall back to empty dict."""
    if not PLATFORM_SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(PLATFORM_SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _get_plat_val(section: str, key: str, default: str | None = None) -> str | None:
    """Helper to pluck a setting from PLATFORM settings; returns None if not present."""
    settings = _plat_settings().get(section, {})
    return str(settings.get(key)) if key in settings else default

def get_provider() -> str:
    """Return the active LLM provider name ('anthropic' or 'ollama') from env or PLATFORM settings."""
    # Env takes precedence
    provider = os.getenv("LLM_PROVIDER")
    if provider is not None:
        return provider.lower().strip()
    # Fall back to PLATFORM settings
    plat_llm = _get_plat_val("llm", "provider", "anthropic")
    return plat_llm.lower().strip() if plat_llm else "anthropic"

def _env_or_plat(section: str, key: str, default: str) -> str:
    """Env → PLATFORM → default."""
    val = os.getenv(key)
    if val is not None:
        return val
    plat_val = _get_plat_val(section, key, default)
    return plat_val or default

def call_llm(prompt: str, max_tokens: int = 2048) -> str:
    """
    Send *prompt* to LLM provider (anthropic or ollama), honoring env *and*
    PLATFORM settings for provider/model/timeouts/etc.
    """
    provider = get_provider()
    if provider == "anthropic":
        return _call_anthropic(prompt, max_tokens)
    if provider == "ollama":
        return _call_ollama(prompt, max_tokens)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Set it in .env or PLATFORM settings.")

# ── Anthropic provider — unchanged from your existing code
def _call_anthropic(prompt: str, max_tokens: int) -> str:
    try:
        import anthropic as _anthropic
    except ImportError as exc:
        raise ImportError("The 'anthropic' package is required when LLM_PROVIDER=anthropic. Run: pip install anthropic") from exc
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key is None:
        raise ValueError("ANTHROPIC_API_KEY is required for anthropic provider.")
    model   = _env_or_plat("llm", "anthropic_model", "claude-sonnet-4-20250514")
    client  = _anthropic.Anthropic(api_key=api_key)
    msg     = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

# ── Ollama provider — updated to pull from PLATFORM settings/env
def _call_ollama(prompt: str, max_tokens: int) -> str:
    base_url    = _env_or_plat("llm", "base_url", "http://127.0.0.1:11434").rstrip("/")
    model       = _env_or_plat("llm", "model", "qwen2.5:3b")
    temperature = float(_env_or_plat("llm", "temperature", "0.7"))
    num_ctx     = int(_env_or_plat("llm", "num_ctx", "8192"))
    timeout     = int(_env_or_plat("llm", "timeout_seconds", "900"))

    url = f"{base_url}/api/chat"
    payload = {
        "model":    model,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
        "format":   "json",
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
            "num_ctx":     num_ctx,
        },
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(f"Cannot connect to Ollama at {base_url}.")
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama request timed out after {timeout} s. "
            "Increase OLLAMA_TIMEOUT_SECONDS in your .env or PLATFORM settings."
        )
    if resp.status_code == 404:
        raise RuntimeError(f"Model '{model}' not found in Ollama. Pull it with: ollama pull {model}")
    resp.raise_for_status()
    return resp.json()["message"]["content"]