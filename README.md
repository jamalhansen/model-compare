# model-compare

Ask multiple LLM providers the same prompt concurrently via
`llm-gateway-service`'s `/compare` endpoint and see every answer side by
side. Built specifically to give `/compare` a real caller -- see BrainSync
tool doc 51 for why `model-comparison-harness` (sequential batch backtesting
against historical data) wasn't the right home for this.

## Quickstart

```bash
export LLM_GATEWAY_API_KEY=$(security find-generic-password -a "$USER" -s "llm-gateway-api-key" -w)
model-compare "What is the capital of France?" \
  -c anthropic:claude-haiku-4-5-20251001 \
  -c ollama:llama3.2:3b
```

Each `--call`/`-c` is `provider` or `provider:model`, repeatable. `--system`
sets the system prompt (default: "Answer concisely."). `--gateway-url`
overrides the gateway URL (default: `$LLM_GATEWAY_URL` or `http://127.0.0.1:8788`).

## Output

A table: provider, model, answer, duration_ms -- plus the `trace_id` so the
same batch can be found together later in `processing_log` (or, if the
gateway call itself used `trace: true`, in its separate trace database --
this tool doesn't currently expose that flag, since ad-hoc comparisons are
usually exactly the kind of thing you look at once and move on from).

## Status

Built 2026-09-19. 10 tests, 94% coverage, clean ruff. Verified for real
against the live gateway: a real concurrent call to Anthropic and local
Ollama, both answered correctly.
