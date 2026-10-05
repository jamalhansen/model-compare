"""Ad-hoc multi-model comparison via llm-gateway-service's /compare endpoint.

The gateway's own /compare mode (concurrent calls, one result per model) had
no real caller anywhere in the ecosystem -- model-comparison-harness is a
sequential batch backtest against historical data, a fundamentally different
shape (one model at a time, many items) from "ask N models the same thing
right now and see all the answers." This is the small tool that shape
actually wants.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class Call:
    provider: str
    model: str | None = None


@dataclass
class CompareResult:
    trace_id: str
    results: list[dict]


class CompareError(RuntimeError):
    """Raised when llm-gateway-service is unreachable or returns an error."""


def parse_calls(specs: list[str]) -> list[Call]:
    """Parse "provider" or "provider:model" strings into Call objects."""
    calls = []
    for spec in specs:
        if ":" in spec:
            provider, model = spec.split(":", 1)
        else:
            provider, model = spec, None
        calls.append(Call(provider=provider, model=model))
    return calls


def run_compare(gateway_url: str, system: str, user: str, calls: list[Call], timeout: float = 120.0) -> CompareResult:
    headers = {}
    api_key = os.environ.get("LLM_GATEWAY_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "system": system,
        "user": user,
        "calls": [{"provider": c.provider, "model": c.model} for c in calls],
    }
    try:
        response = httpx.post(f"{gateway_url.rstrip('/')}/compare", json=payload, headers=headers, timeout=timeout)
    except httpx.HTTPError as e:
        raise CompareError(f"llm-gateway-service request failed: {type(e).__name__}: {e}") from e
    if response.status_code != 200:
        raise CompareError(f"llm-gateway-service returned {response.status_code}: {response.text}")

    data = response.json()
    return CompareResult(trace_id=data["trace_id"], results=data["results"])
