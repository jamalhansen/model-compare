from unittest.mock import patch

from typer.testing import CliRunner

from model_compare.cli import app
from model_compare.core import CompareError, CompareResult


class TestCli:
    def test_requires_at_least_one_call(self):
        result = CliRunner().invoke(app, ["hello"])
        assert result.exit_code == 1
        assert "at least one --call" in result.output

    def test_prints_results_table(self):
        fake_result = CompareResult(
            trace_id="abc-123",
            results=[
                {
                    "provider": "anthropic",
                    "model": "claude-haiku",
                    "text": "hi there",
                    "error": None,
                    "duration_ms": 100,
                },
                {"provider": "ollama", "model": "llama3.2:3b", "text": None, "error": "boom", "duration_ms": 50},
            ],
        )
        with patch("model_compare.cli.run_compare", return_value=fake_result):
            result = CliRunner().invoke(app, ["hello", "-c", "anthropic:claude-haiku", "-c", "ollama:llama3.2:3b"])
        assert result.exit_code == 0
        assert "hi there" in result.output
        assert "boom" in result.output
        assert "abc-123" in result.output

    def test_compare_error_exits_nonzero(self):
        with patch("model_compare.cli.run_compare", side_effect=CompareError("gateway down")):
            result = CliRunner().invoke(app, ["hello", "-c", "anthropic"])
        assert result.exit_code == 1
        assert "gateway down" in result.output
