"""core/llm_client.py
RASCALWORKS OS — LLM provider abstraction.

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
    text = call_llm(prompt, max_tokens=2048, system="You are SCRIBE...")

Determinism (Only Institute review, "Non-Determinism" section):
    Every provider call now defaults to temperature=0 instead of the
    provider's own default (usually ~1.0). Override globally with the
    LLM_TEMPERATURE env var, or per-call via the temperature= kwarg.
    Set LLM_SEED to forward a seed to providers that support one
    (OpenAI-compatible endpoints and Ollama; the Anthropic API has no
    seed parameter as of this writing, so it's accepted but ignored there).
    Note that temperature=0 + seed makes output *more* reproducible, not
    perfectly deterministic — provider-side model updates, floating point
    non-associativity across GPU batches, etc. can still cause drift. Every
    call is also written to a local audit log (core.llm_audit) recording
    the provider, the model that actually responded, params, prompt, and
    response, so a run can be inspected or replayed after the fact.
"""

import logging
import os
import json
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from core.llm_audit import log_call as _audit_log_call

load_dotenv()

logger = logging.getLogger(__name__)

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


def _default_temperature() -> float:
    """Global default sampling temperature. 0 unless LLM_TEMPERATURE overrides it."""
    raw = os.getenv("LLM_TEMPERATURE")
    if raw is None:
        plat = _get_plat_val("llm", "temperature", 0)
        raw = str(plat) if plat is not None else "0"
    try:
        return float(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid LLM_TEMPERATURE=%r, falling back to 0", raw)
        return 0.0


def _default_seed() -> int | None:
    """Global default seed. Unset (None) unless LLM_SEED is provided."""
    raw = os.getenv("LLM_SEED")
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid LLM_SEED=%r, ignoring", raw)
        return None


def call_llm(
    prompt: str,
    max_tokens: int = 2048,
    system: str | None = None,
    temperature: float | None = None,
    seed: int | None = None,
) -> str:
    """
    Send *prompt* to the configured LLM provider and return response text.

    system: optional system prompt, passed natively to the provider (as the
        Anthropic `system` field, or a leading `role: system` message for
        OpenAI-compatible/Ollama/LiteLLM) rather than concatenated into the
        user prompt.
    temperature: defaults to LLM_TEMPERATURE env var, or 0 if unset.
    seed: defaults to LLM_SEED env var if set; otherwise no seed is sent.
    """
    provider = get_provider()
    if temperature is None:
        temperature = _default_temperature()
    if seed is None:
        seed = _default_seed()

    meta: dict[str, Any] = {"model": None}
    started = time.monotonic()
    error_text: str | None = None
    text: str | None = None
    try:
        if provider == "anthropic":
            text = _call_anthropic(prompt, max_tokens, system=system, temperature=temperature, seed=seed, _meta=meta)
        elif provider == "ollama":
            text = _call_ollama(prompt, max_tokens, system=system, temperature=temperature, seed=seed, _meta=meta)
        elif provider == "openai":
            text = _call_openai(prompt, max_tokens, system=system, temperature=temperature, seed=seed, _meta=meta)
        elif provider == "deepseek":
            text = _call_deepseek(prompt, max_tokens, system=system, temperature=temperature, seed=seed, _meta=meta)
        elif provider == "gemini":
            text = _call_gemini(prompt, max_tokens, system=system, temperature=temperature, seed=seed, _meta=meta)
        elif provider == "openai_compatible":
            text = _call_openai_compatible(prompt, max_tokens, system=system, temperature=temperature, seed=seed, _meta=meta)
        elif provider == "litellm":
            text = _call_litellm(prompt, max_tokens, system=system, temperature=temperature, seed=seed, _meta=meta)
        else:
            raise ValueError(
                f"Unknown LLM provider: {provider!r}. "
                "Set LLM_PROVIDER in .env or PLATFORM settings."
            )
        return text
    except Exception as exc:
        error_text = str(exc)
        raise
    finally:
        duration = time.monotonic() - started
        model_used = meta.get("model")
        if error_text:
            logger.warning(
                "[llm_client] provider=%s model=%s FAILED after %.2fs: %s",
                provider, model_used, duration, error_text,
            )
        else:
            logger.info(
                "[llm_client] provider=%s model=%s responded in %.2fs",
                provider, model_used, duration,
            )
        _audit_log_call(
            provider=provider,
            model=model_used,
            system=system,
            prompt=prompt,
            response=text,
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens,
            duration_s=duration,
            error=error_text,
        )


def _call_openai(prompt: str, max_tokens: int, *, system=None, temperature=0.0, seed=None, _meta=None) -> str:
    model = os.getenv("OPENAI_MODEL", _llm_model("gpt-4o-mini"))
    return _call_openai_sdk(
        prompt=prompt,
        max_tokens=max_tokens,
        model=model,
        api_key_env="OPENAI_API_KEY",
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        provider_name="OpenAI",
        system=system,
        temperature=temperature,
        seed=seed,
        _meta=_meta,
    )


def _call_deepseek(prompt: str, max_tokens: int, *, system=None, temperature=0.0, seed=None, _meta=None) -> str:
    model = os.getenv("DEEPSEEK_MODEL", _llm_model("deepseek-chat"))
    return _call_openai_sdk(
        prompt=prompt,
        max_tokens=max_tokens,
        model=model,
        api_key_env="DEEPSEEK_API_KEY",
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        provider_name="DeepSeek",
        system=system,
        temperature=temperature,
        seed=seed,
        _meta=_meta,
    )


def _call_gemini(prompt: str, max_tokens: int, *, system=None, temperature=0.0, seed=None, _meta=None) -> str:
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
        system=system,
        temperature=temperature,
        seed=seed,
        _meta=_meta,
    )


def _call_openai_compatible(prompt: str, max_tokens: int, *, system=None, temperature=0.0, seed=None, _meta=None) -> str:
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
        system=system,
        temperature=temperature,
        seed=seed,
        _meta=_meta,
    )


def _call_openai_sdk(
    prompt: str,
    max_tokens: int,
    model: str,
    provider_name: str,
    base_url: str,
    api_key_env: str | None = None,
    api_key: str | None = None,
    *,
    system: str | None = None,
    temperature: float = 0.0,
    seed: int | None = None,
    _meta: dict | None = None,
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

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    create_kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if seed is not None:
        create_kwargs["seed"] = seed

    if _meta is not None:
        _meta["model"] = model

    response = client.chat.completions.create(**create_kwargs)

    if _meta is not None:
        # Some OpenAI-compatible gateways report back the model that actually
        # served the request (useful when `model` is an alias/router target).
        responded_model = getattr(response, "model", None)
        if responded_model:
            _meta["model"] = responded_model

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError(f"{provider_name} returned an empty response.")
    return text


def _call_litellm(prompt: str, max_tokens: int, *, system=None, temperature=0.0, seed=None, _meta=None) -> str:
    try:
        from litellm import completion
    except ImportError as exc:
        raise ImportError(
            "The 'litellm' package is required when LLM_PROVIDER=litellm. "
            "Run: pip install litellm"
        ) from exc

    model = os.getenv("LITELLM_MODEL", _llm_model("openai/gpt-4o-mini"))

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if seed is not None:
        kwargs["seed"] = seed

    # Optional generic overrides for custom endpoints.
    api_key = os.getenv("LITELLM_API_KEY")
    api_base = os.getenv("LITELLM_API_BASE")
    if api_key:
        kwargs["api_key"] = api_key
    if api_base:
        kwargs["api_base"] = api_base.rstrip("/")

    if _meta is not None:
        _meta["model"] = model

    response = completion(**kwargs)

    if _meta is not None:
        responded_model = getattr(response, "model", None)
        if responded_model:
            _meta["model"] = responded_model

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("LiteLLM returned an empty response.")
    return text


# ── Anthropic ────────────────────────────────────────────────────────────────

def _call_anthropic(prompt: str, max_tokens: int, *, system=None, temperature=0.0, seed=None, _meta=None) -> str:
    try:
        import anthropic as _anthropic
    except ImportError as exc:
        raise ImportError(
            "The 'anthropic' package is required when LLM_PROVIDER=anthropic. "
            "Run: pip install anthropic"
        ) from exc

    # Anthropic's API has no `seed` parameter — silently accepted here for a
    # uniform call_llm() signature across providers, but it has no effect.
    del seed

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
            create_kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                create_kwargs["system"] = system
            msg = client.messages.create(**create_kwargs)
            if model != configured_model:
                # This is the silent-fallback case the review flagged: the
                # configured model wasn't available and we served from a
                # different one. Make it loud instead of silent.
                logger.warning(
                    "[llm_client] Anthropic fell back from configured model=%r to model=%r",
                    configured_model, model,
                )
            if _meta is not None:
                _meta["model"] = model
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
                logger.info("[llm_client] Anthropic model %r unavailable, trying next candidate", model)
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

def _call_ollama(prompt: str, max_tokens: int, *, system=None, temperature=None, seed=None, _meta=None) -> str:
    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        str(_get_plat_val("llm", "base_url", "http://127.0.0.1:11434"))
    ).rstrip("/")

    model = os.getenv(
        "OLLAMA_MODEL",
        str(_get_plat_val("llm", "model", "qwen2.5:3b"))
    )

    # OLLAMA_TEMPERATURE (if explicitly set) wins for backward compatibility;
    # otherwise fall back to whatever call_llm() resolved (LLM_TEMPERATURE / 0).
    env_temperature = os.getenv("OLLAMA_TEMPERATURE")
    if env_temperature is not None:
        temperature = float(env_temperature)
    elif temperature is None:
        temperature = float(_get_plat_val("llm", "temperature", 0.0))

    num_ctx = int(os.getenv(
        "OLLAMA_NUM_CTX",
        str(_get_plat_val("llm", "num_ctx", 8192))
    ))

    timeout = int(os.getenv(
        "OLLAMA_TIMEOUT_SECONDS",
        str(_get_plat_val("llm", "timeout_seconds", 900))
    ))

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    options: dict[str, Any] = {
        "num_predict": max_tokens,
        "temperature": temperature,
        "num_ctx": num_ctx,
    }
    if seed is not None:
        options["seed"] = seed

    url = f"{base_url}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": options,
    }

    if _meta is not None:
        _meta["model"] = model

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
