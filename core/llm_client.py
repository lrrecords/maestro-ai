"""core/llm_client.py
MAESTRO AI — LLM provider abstraction.

Routes agent prompts to the configured provider, selected via env vars or
PLATFORM settings.

Supported providers:
    anthropic         — Anthropic Claude API (requires ANTHROPIC_API_KEY)
    ollama            — Local Ollama HTTP server
    openai            — OpenAI Chat Completions API (ChatGPT)
    deepseek          — DeepSeek Chat API
    gemini            — Gemini OpenAI-compatible endpoint
    openai_compatible — Generic OpenAI-compatible endpoint
    litellm           — LiteLLM router for broad provider support

Usage:
    from core.llm_client import call_llm

    text = call_llm(prompt, max_tokens=2048)
"""

import os
import json
from pathlib import Path
from typing import Any

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
    """Return the active LLM provider name (canonicalized)."""
    provider = os.getenv("LLM_PROVIDER")
    if provider is not None:
        return _canonical_provider(provider)

    plat_llm = _get_plat_val("llm", "provider", "anthropic")
    return _canonical_provider(str(plat_llm)) if plat_llm else "anthropic"


def _canonical_provider(provider: str) -> str:
    normalized = (provider or "anthropic").lower().strip()
    aliases = {
        "claude": "anthropic",
        "chatgpt": "openai",
        "gpt": "openai",
    }
    return aliases.get(normalized, normalized)


def _llm_model(default: str = "") -> str:
    model = os.getenv("LLM_MODEL")
    if model:
        return model.strip()
    from_platform = _get_plat_val("llm", "model", default)
    return str(from_platform).strip() if from_platform else str(default)


def call_llm(prompt: str, max_tokens: int = 2048) -> str:
    """
    Send *prompt* to the configured LLM provider and return response text.
    """
    provider = get_provider()
    if provider == "anthropic":
        return _call_anthropic(prompt, max_tokens)
    if provider == "ollama":
        return _call_ollama(prompt, max_tokens)
    if provider == "openai":
        return _call_openai(prompt, max_tokens)
    if provider == "deepseek":
        return _call_deepseek(prompt, max_tokens)
    if provider == "gemini":
        return _call_gemini(prompt, max_tokens)
    if provider == "openai_compatible":
        return _call_openai_compatible(prompt, max_tokens)
    if provider == "litellm":
        return _call_litellm(prompt, max_tokens)
    raise ValueError(
        f"Unknown LLM provider: {provider!r}. "
        "Set LLM_PROVIDER in .env or PLATFORM settings."
    )


def _call_openai(prompt: str, max_tokens: int) -> str:
    model = os.getenv("OPENAI_MODEL", _llm_model("gpt-4o-mini"))
    return _call_openai_sdk(
        prompt=prompt,
        max_tokens=max_tokens,
        model=model,
        api_key_env="OPENAI_API_KEY",
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        provider_name="OpenAI",
    )


def _call_deepseek(prompt: str, max_tokens: int) -> str:
    model = os.getenv("DEEPSEEK_MODEL", _llm_model("deepseek-chat"))
    return _call_openai_sdk(
        prompt=prompt,
        max_tokens=max_tokens,
        model=model,
        api_key_env="DEEPSEEK_API_KEY",
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        provider_name="DeepSeek",
    )


def _call_gemini(prompt: str, max_tokens: int) -> str:
    model = os.getenv("GEMINI_MODEL", _llm_model("gemini-2.5-flash"))
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is required for gemini provider."
        )
    return _call_openai_sdk(
        prompt=prompt,
        max_tokens=max_tokens,
        model=model,
        api_key=api_key,
        base_url=os.getenv(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        ),
        provider_name="Gemini",
    )


def _call_openai_compatible(prompt: str, max_tokens: int) -> str:
    model = _llm_model(os.getenv("OPENAI_COMPAT_MODEL", "gpt-4o-mini"))
    base_url = os.getenv(
        "LLM_API_BASE_URL",
        os.getenv("OPENAI_COMPAT_BASE_URL", "https://api.openai.com/v1"),
    )
    api_key = os.getenv("LLM_API_KEY", os.getenv("OPENAI_COMPAT_API_KEY"))
    if not api_key:
        raise ValueError(
            "LLM_API_KEY (or OPENAI_COMPAT_API_KEY) is required when "
            "LLM_PROVIDER=openai_compatible."
        )
    return _call_openai_sdk(
        prompt=prompt,
        max_tokens=max_tokens,
        model=model,
        api_key=api_key,
        base_url=base_url,
        provider_name="OpenAI-compatible",
    )


def _call_openai_sdk(
    prompt: str,
    max_tokens: int,
    model: str,
    provider_name: str,
    base_url: str,
    api_key_env: str | None = None,
    api_key: str | None = None,
) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "The 'openai' package is required for OpenAI-compatible providers. "
            "Run: pip install openai"
        ) from exc

    if api_key is None and api_key_env:
        api_key = os.getenv(api_key_env)
    if not api_key:
        required = api_key_env or "LLM_API_KEY"
        raise ValueError(f"{required} is required for {provider_name} provider.")

    client = OpenAI(api_key=api_key, base_url=base_url.rstrip("/"))

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError(f"{provider_name} returned an empty response.")
    return text


def _call_litellm(prompt: str, max_tokens: int) -> str:
    try:
        from litellm import completion
    except ImportError as exc:
        raise ImportError(
            "The 'litellm' package is required when LLM_PROVIDER=litellm. "
            "Run: pip install litellm"
        ) from exc

    model = os.getenv("LITELLM_MODEL", _llm_model("openai/gpt-4o-mini"))

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    # Optional generic overrides for custom endpoints.
    api_key = os.getenv("LITELLM_API_KEY")
    api_base = os.getenv("LITELLM_API_BASE")
    if api_key:
        kwargs["api_key"] = api_key
    if api_base:
        kwargs["api_base"] = api_base.rstrip("/")

    response = completion(**kwargs)
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("LiteLLM returned an empty response.")
    return text


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

    configured_model = os.getenv("ANTHROPIC_MODEL")
    if not configured_model:
        # Platform Ops currently saves model under llm.model; keep llm.anthropic_model for compatibility.
        configured_model = str(
            _get_plat_val("llm", "anthropic_model", _get_plat_val("llm", "model", ""))
        )

    # Optional comma-separated fallback list for account-specific model access.
    # Example: ANTHROPIC_MODEL_CANDIDATES=claude-3-5-sonnet-20241022,claude-3-haiku-20240307
    env_candidates = [
        m.strip()
        for m in (os.getenv("ANTHROPIC_MODEL_CANDIDATES") or "").split(",")
        if m.strip()
    ]

    model_candidates = [
        configured_model,
        *env_candidates,
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-20241022",
        "claude-3-5-haiku-latest",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]
    seen = set()
    model_candidates = [m for m in model_candidates if m and not (m in seen or seen.add(m))]

    client = _anthropic.Anthropic(api_key=api_key)
    last_exc = None
    for model in model_candidates:
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception as exc:
            last_exc = exc
            text = str(exc).lower()
            if (
                "not_found_error" in text
                or "model:" in text
                or "model_not_found" in text
                or "invalid model" in text
            ):
                continue
            raise

    attempted = ", ".join(model_candidates) if model_candidates else "(none)"
    raise RuntimeError(
        "Anthropic model not found for this account. "
        f"Attempted: {attempted}. "
        "Set ANTHROPIC_MODEL (or Platform Ops model) to a model your Anthropic account can access. "
        "You can also set ANTHROPIC_MODEL_CANDIDATES as a comma-separated fallback list."
    ) from last_exc


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
            f"Cannot connect to Ollama at {base_url}. "
            "Is Ollama running? Start it with: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama request timed out after {timeout} s. "
            "Increase OLLAMA_TIMEOUT_SECONDS in your .env or PLATFORM settings, "
            "or switch to a smaller model via OLLAMA_MODEL."
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