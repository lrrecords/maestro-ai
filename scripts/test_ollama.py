#!/usr/bin/env python3
"""
scripts/test_ollama.py
MAESTRO AI — LLM provider connectivity checker.

Verifies that the configured LLM provider is reachable and can respond
to a simple prompt. Run this after updating your .env file to confirm
everything is wired up correctly before running the full pipeline.

Usage:
    python scripts/test_ollama.py
"""

import sys
import os
from pathlib import Path

# Ensure scripts/ is on the path so `llm.client` can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm.client import call_llm, get_provider

TEST_PROMPT = 'Return this exact JSON and nothing else: {"status": "ok", "agent": "MAESTRO"}'


def main():
    provider = get_provider()

    print("=" * 60)
    print("🎵 MAESTRO — LLM Provider Connectivity Check")
    print("=" * 60)
    print(f"  Provider : {provider.upper()}")

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        print(f"  URL      : {base_url}")
        print(f"  Model    : {model}")
    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        key   = os.getenv("ANTHROPIC_API_KEY", "")
        masked = key[:8] + "..." if len(key) > 8 else "(not set)"
        print(f"  Model    : {model}")
        print(f"  API Key  : {masked}")

    print()
    print("  Sending test prompt...")

    try:
        response = call_llm(TEST_PROMPT, max_tokens=64)
    except Exception as exc:
        print(f"\n❌  FAILED: {exc}")
        sys.exit(1)

    print(f"\n✅  Response received:")
    print(f"    {response.strip()}")
    print()
    print("=" * 60)
    print(f"🎉  {provider.upper()} is working — MAESTRO is ready!")
    print("=" * 60)


if __name__ == "__main__":
    main()
