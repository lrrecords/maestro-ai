# LLM Provider Setup Matrix

This guide provides copy-paste environment variable blocks for each supported provider.

## Common Required Variables

These are required no matter which provider you use:

```env
MAESTRO_TOKEN=replace-with-strong-token
WEBHOOK_SECRET=replace-with-strong-secret
SECRET_KEY=replace-with-random-secret-key
LLM_PROVIDER=<provider>
```

## Provider Matrix

| Provider | `LLM_PROVIDER` | Required Keys | Optional Keys | Example Model |
|---|---|---|---|---|
| Ollama | `ollama` | None (local server) | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_NUM_CTX`, `OLLAMA_TIMEOUT_SECONDS`, `OLLAMA_TEMPERATURE` | `qwen2.5:3b` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL`, `ANTHROPIC_MODEL_CANDIDATES` | `claude-3-5-haiku-20241022` |
| OpenAI / ChatGPT | `openai` | `OPENAI_API_KEY` | `OPENAI_MODEL`, `OPENAI_BASE_URL` | `gpt-4o-mini` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL` | `deepseek-chat` |
| Gemini | `gemini` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | `GEMINI_MODEL`, `GEMINI_BASE_URL` | `gemini-2.5-flash` |
| OpenAI-compatible | `openai_compatible` | `LLM_API_KEY` | `LLM_API_BASE_URL`, `LLM_MODEL`, `OPENAI_COMPAT_API_KEY`, `OPENAI_COMPAT_BASE_URL`, `OPENAI_COMPAT_MODEL` | `gpt-4o-mini` |
| LiteLLM router | `litellm` | Usually provider-specific (often in model/env) | `LITELLM_MODEL`, `LITELLM_API_KEY`, `LITELLM_API_BASE`, `LLM_MODEL` | `openai/gpt-4o-mini` |

## Copy-Paste Env Blocks

### Ollama (local)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_NUM_CTX=8192
OLLAMA_TEMPERATURE=0.7
OLLAMA_TIMEOUT_SECONDS=900
```

### Anthropic

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-...
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
```

### OpenAI / ChatGPT

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### DeepSeek

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

### Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

### OpenAI-compatible endpoint (OpenRouter or self-hosted gateway)

```env
LLM_PROVIDER=openai_compatible
LLM_API_KEY=...
LLM_API_BASE_URL=https://your-endpoint/v1
LLM_MODEL=gpt-4o-mini
```

### LiteLLM router

```env
LLM_PROVIDER=litellm
LITELLM_MODEL=openai/gpt-4o-mini
# Optional overrides:
# LITELLM_API_KEY=...
# LITELLM_API_BASE=https://your-endpoint/v1
```

## Aliases Supported

`LLM_PROVIDER` aliases currently supported by runtime routing:

- `chatgpt` maps to `openai`
- `gpt` maps to `openai`
- `claude` maps to `anthropic`

## Notes

- Ollama health checks are only active in Platform Ops when `LLM_PROVIDER=ollama`.
- API keys are read from environment variables, not stored in Platform Ops settings.
- `LLM_MODEL` can be used as a generic fallback model in some provider paths.
