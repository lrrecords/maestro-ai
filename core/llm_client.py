"""core/llm_client.py
MAESTRO AI — LLM provider abstraction.

Routes agent prompts to either Anthropic Claude or a local Ollama server,
selected via the PLATFORM settings (or env vars).

Supported providers:
  anthropic  — Anthropic Claude API (requires ANTHROPIC_API_KEY)
  ollama     — Local Ollama HTTP server (requires Ollama running locally)

Usage:
    from core.llm_client import call_llm

    text = call_llm(prompt, max_tokens=2048)
"""

import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# Path to PLATFORM settings (repo root / platform_ops / data / platform_settings.json)
PLATFORM_SETTINGS_PATH = (
    Path(__file__).resolve().parents[1]
    / "platform_ops"
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


def _get_plat_val(section: str, key: str, default=None):
    """Helper to pluck a setting from PLATFORM settings."""
    settings = _plat_settings().get(section, {})
    return settings.get(key, default)


def get_provider() -> str:
    """Return the active LLM provider name ('anthropic' or 'ollama')."""
    provider = os.getenv("LLM_PROVIDER")
    if provider is not None:
        return provider.lower().strip()

    plat_llm = _get_plat_val("llm", "provider", "anthropic")
    return str(plat_llm).lower().strip() if plat_llm else "anthropic"


def call_llm(prompt: str, max_tokens: int = 2048) -> str:
    """
    Send *prompt* to the configured LLM provider and return response text.
    """
    provider = get_provider()
    if provider == "anthropic":
        return _call_anthropic(prompt, max_tokens)
    if provider == "ollama":
        return _call_ollama(prompt, max_tokens)
    raise ValueError(
        f"Unknown LLM provider: {provider!r}. "
        "Set LLM_PROVIDER in .env or PLATFORM settings."
    )


# ── Anthropic ────────────────────────────────────────────────────────────────

def _call_anthropic(prompt: str, max_tokens: int) -> str:
    try:
        import anthropic as _anthropic
    except ImportError as exc:
        raise ImportError(
            "The 'anthropic' package is required when LLM_PROVIDER=anthropic. "
            "Run: pip install anthropic"
        ) from exc

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is required for anthropic provider."
        )

    model = os.getenv(
        "ANTHROPIC_MODEL",
        str(_get_plat_val("llm", "anthropic_model", "claude-sonnet-4-20250514"))
    )

    client = _anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── Ollama ───────────────────────────────────────────────────────────────────

def _call_ollama(prompt: str, max_tokens: int) -> str:
    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        str(_get_plat_val("llm", "base_url", "http://127.0.0.1:11434"))
    ).rstrip("/")

    model = os.getenv(
        "OLLAMA_MODEL",
        str(_get_plat_val("llm", "model", "qwen2.5:3b"))
    )

    temperature = float(os.getenv(
        "OLLAMA_TEMPERATURE",
        str(_get_plat_val("llm", "temperature", 0.7))
    ))

    num_ctx = int(os.getenv(
        "OLLAMA_NUM_CTX",
        str(_get_plat_val("llm", "num_ctx", 8192))
    ))

    timeout = int(os.getenv(
        "OLLAMA_TIMEOUT_SECONDS",
        str(_get_plat_val("llm", "timeout_seconds", 900))
    ))

    url = f"{base_url}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
            "num_ctx": num_ctx,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot connect to Ollama at {base_url}."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama request timed out after {timeout} s. "
            "Increase OLLAMA_TIMEOUT_SECONDS in your .env or PLATFORM settings."
        )

    if resp.status_code == 404:
        raise RuntimeError(
            f"Model '{model}' not found in Ollama. Pull it with: ollama pull {model}"
        )

    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Ollama API error ({resp.status_code}): {exc}") from exc

    data = resp.json()
    return data["message"]["content"]