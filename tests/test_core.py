from unittest.mock import patch

import pytest

from model_compare.core import Call, CompareError, parse_calls, run_compare


class TestParseCalls:
    def test_provider_only(self):
        assert parse_calls(["anthropic"]) == [Call(provider="anthropic", model=None)]

    def test_provider_and_model(self):
        assert parse_calls(["ollama:llama3.2:3b"]) == [Call(provider="ollama", model="llama3.2:3b")]

    def test_multiple_calls(self):
        result = parse_calls(["anthropic:claude-haiku", "ollama"])
        assert result == [
            Call(provider="anthropic", model="claude-haiku"),
            Call(provider="ollama", model=None),
        ]


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json_body = json_body or {}
        self.text = text

    def json(self):
        return self._json_body


class TestRunCompare:
    def test_returns_results_on_success(self):
        response = _FakeResponse(
            200,
            {
                "trace_id": "abc-123",
                "results": [
                    {"provider": "anthropic", "model": "claude-haiku", "text": "hi", "error": None, "duration_ms": 100}
                ],
            },
        )
        with patch("httpx.post", return_value=response) as mock_post:
            result = run_compare("http://127.0.0.1:8788", "sys", "hello", [Call("anthropic")])
        assert result.trace_id == "abc-123"
        assert result.results[0]["text"] == "hi"
        sent = mock_post.call_args.kwargs["json"]
        assert sent["calls"] == [{"provider": "anthropic", "model": None}]

    def test_sends_bearer_token_when_api_key_set(self, monkeypatch):
        monkeypatch.setenv("LLM_GATEWAY_API_KEY", "secret")
        response = _FakeResponse(200, {"trace_id": "x", "results": []})
        with patch("httpx.post", return_value=response) as mock_post:
            run_compare("http://127.0.0.1:8788", "sys", "hello", [Call("anthropic")])
        assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer secret"

    def test_non_200_raises_compare_error(self):
        response = _FakeResponse(502, text="bad gateway")
        with patch("httpx.post", return_value=response), pytest.raises(CompareError, match="502"):
            run_compare("http://127.0.0.1:8788", "sys", "hello", [Call("anthropic")])

    def test_request_failure_raises_compare_error(self):
        import httpx

        with (
            patch("httpx.post", side_effect=httpx.ConnectError("refused")),
            pytest.raises(CompareError, match="request failed"),
        ):
            run_compare("http://127.0.0.1:8788", "sys", "hello", [Call("anthropic")])
