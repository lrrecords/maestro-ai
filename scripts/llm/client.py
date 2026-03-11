"""scripts/llm/client.py
MAESTRO AI — LLM provider abstraction.

Routes agent prompts to either Anthropic Claude or a local Ollama server,
selected via the LLM_PROVIDER environment variable (default: anthropic).

Supported providers:
  anthropic  — Anthropic Claude API (requires ANTHROPIC_API_KEY)
  ollama     — Local Ollama HTTP server (requires Ollama running locally)

Usage:
    from llm.client import call_llm, get_provider

    text = call_llm(prompt, max_tokens=2048)
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def get_provider() -> str:
    """Return the active LLM provider name ('anthropic' or 'ollama')."""
    return os.getenv("LLM_PROVIDER", "anthropic").lower().strip()


def call_llm(prompt: str, max_tokens: int = 2048) -> str:
    """
    Send *prompt* to the configured LLM provider and return the response text.

    Provider is determined by LLM_PROVIDER in the environment (default: anthropic):
      anthropic  — Anthropic Claude API
      ollama     — Local Ollama server

    Raises:
        ImportError  — anthropic package not installed (LLM_PROVIDER=anthropic)
        ValueError   — unknown provider value or missing credentials
        RuntimeError — provider unreachable (Ollama not running, wrong model, etc.)
    """
    provider = get_provider()
    if provider == "anthropic":
        return _call_anthropic(prompt, max_tokens)
    if provider == "ollama":
        return _call_ollama(prompt, max_tokens)
    raise ValueError(
        f"Unknown LLM_PROVIDER: {provider!r}. "
        "Set LLM_PROVIDER to 'anthropic' or 'ollama' in your .env file."
    )


# ── Anthropic ──────────────────────────────────────────────────────────────────

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
            "ANTHROPIC_API_KEY is not set in your .env file.\n"
            "Either add your Anthropic key or switch to a local model:\n"
            "  LLM_PROVIDER=ollama\n"
            "  OLLAMA_MODEL=qwen2.5:3b"
        )

    model  = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    client = _anthropic.Anthropic(api_key=api_key)
    msg    = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── Ollama ─────────────────────────────────────────────────────────────────────

def _call_ollama(prompt: str, max_tokens: int) -> str:
    base_url    = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model       = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    num_ctx     = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
    timeout     = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "900"))

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
        raise RuntimeError(
            f"Cannot connect to Ollama at {base_url}.\n"
            "Make sure Ollama is running:\n"
            "  - Windows: start Ollama from the system tray, or run 'ollama serve'\n"
            "  - Mac/Linux: run 'ollama serve' in a terminal\n"
            "See https://ollama.com for installation instructions."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama request timed out after {timeout} s.\n"
            "Options to fix this:\n"
            "  1. Increase the timeout:  set OLLAMA_TIMEOUT_SECONDS=1800 in your .env file\n"
            "  2. Use a smaller model:   set OLLAMA_MODEL=qwen2.5:3b in your .env file"
        )

    if resp.status_code == 404:
        raise RuntimeError(
            f"Model '{model}' not found in Ollama.\n"
            f"Pull it with: ollama pull {model}"
        )

    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Ollama API error ({resp.status_code}): {exc}") from exc

    data = resp.json()
    return data["message"]["content"]
