"""
tests/test_llm_client.py
Unit tests for scripts/llm/client.py

Validates:
  - Ollama default timeout is 900 s (not the old 300 s)
  - Timeout error message contains both remediation options
  - Connection error message is actionable
  - Model-not-found (404) error is actionable
  - OLLAMA_TIMEOUT_SECONDS env var overrides the default
  - OLLAMA_MODEL env var is forwarded in the request payload
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import requests

# Put scripts/ on the path so `llm.client` can be imported without install
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from llm.client import _call_ollama, get_provider


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ok_response(content: str = '{"status": "ok"}') -> MagicMock:
    """Return a mock requests.Response with a successful Ollama payload."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"message": {"content": content}}
    resp.raise_for_status.return_value = None
    return resp


# ── Default timeout ────────────────────────────────────────────────────────────

class TestDefaultTimeout:
    """The default Ollama request timeout must be 900 s (not the old 300 s)."""

    def test_default_timeout_is_900(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_TIMEOUT_SECONDS", raising=False)

        captured = {}

        def fake_post(url, json, timeout):
            captured["timeout"] = timeout
            return _ok_response()

        with patch("llm.client.requests.post", side_effect=fake_post):
            _call_ollama("hello", max_tokens=16)

        assert captured["timeout"] == 900, (
            f"Expected default timeout 900, got {captured['timeout']}"
        )

    def test_custom_timeout_is_respected(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "1800")

        captured = {}

        def fake_post(url, json, timeout):
            captured["timeout"] = timeout
            return _ok_response()

        with patch("llm.client.requests.post", side_effect=fake_post):
            _call_ollama("hello", max_tokens=16)

        assert captured["timeout"] == 1800


# ── Timeout error message ──────────────────────────────────────────────────────

class TestTimeoutErrorMessage:
    """When Ollama times out the error message must offer two remediation paths."""

    def test_timeout_error_mentions_timeout_env_var(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_TIMEOUT_SECONDS", raising=False)

        with patch(
            "llm.client.requests.post",
            side_effect=requests.exceptions.Timeout,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                _call_ollama("hello", max_tokens=16)

        msg = str(exc_info.value)
        assert "OLLAMA_TIMEOUT_SECONDS" in msg, (
            "Timeout error should mention OLLAMA_TIMEOUT_SECONDS env var"
        )

    def test_timeout_error_mentions_smaller_model(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_TIMEOUT_SECONDS", raising=False)

        with patch(
            "llm.client.requests.post",
            side_effect=requests.exceptions.Timeout,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                _call_ollama("hello", max_tokens=16)

        msg = str(exc_info.value)
        assert "OLLAMA_MODEL" in msg, (
            "Timeout error should suggest switching to a smaller model via OLLAMA_MODEL"
        )

    def test_timeout_error_includes_actual_timeout_value(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "600")

        with patch(
            "llm.client.requests.post",
            side_effect=requests.exceptions.Timeout,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                _call_ollama("hello", max_tokens=16)

        msg = str(exc_info.value)
        assert "600" in msg, "Timeout error should include the actual timeout value"


# ── Connection error message ───────────────────────────────────────────────────

class TestConnectionErrorMessage:
    """Connection errors should tell the user how to start Ollama."""

    def test_connection_error_mentions_ollama_serve(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

        with patch(
            "llm.client.requests.post",
            side_effect=requests.exceptions.ConnectionError,
        ):
            with pytest.raises(RuntimeError) as exc_info:
                _call_ollama("hello", max_tokens=16)

        msg = str(exc_info.value)
        assert "ollama serve" in msg.lower(), (
            "Connection error should instruct the user to run 'ollama serve'"
        )


# ── Model not found ────────────────────────────────────────────────────────────

class TestModelNotFound:
    """A 404 from Ollama should produce a clear 'pull the model' error."""

    def test_404_error_suggests_pull(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5:3b")

        resp = MagicMock()
        resp.status_code = 404

        with patch("llm.client.requests.post", return_value=resp):
            with pytest.raises(RuntimeError) as exc_info:
                _call_ollama("hello", max_tokens=16)

        msg = str(exc_info.value)
        assert "pull" in msg.lower(), "404 error should suggest 'ollama pull <model>'"
        assert "qwen2.5:3b" in msg, "404 error should include the model name"


# ── Model env var forwarding ───────────────────────────────────────────────────

class TestModelEnvVar:
    """OLLAMA_MODEL is forwarded in the request payload."""

    def test_model_in_payload(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")

        captured = {}

        def fake_post(url, json, timeout):
            captured["payload"] = json
            return _ok_response()

        with patch("llm.client.requests.post", side_effect=fake_post):
            _call_ollama("hello", max_tokens=16)

        assert captured["payload"]["model"] == "llama3.2:3b"


# ── Provider detection ─────────────────────────────────────────────────────────

class TestGetProvider:
    def test_default_provider_is_anthropic(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        assert get_provider() == "anthropic"

    def test_ollama_provider(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        assert get_provider() == "ollama"

    def test_provider_is_lowercased(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "OLLAMA")
        assert get_provider() == "ollama"
