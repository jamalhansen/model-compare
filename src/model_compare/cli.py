import os
from typing import Annotated

import typer
from local_first_common.tracking import register_tool
from rich.console import Console
from rich.table import Table

from .core import CompareError, parse_calls, run_compare

TOOL_NAME = "model-compare"
_TOOL = register_tool(TOOL_NAME)

console = Console(stderr=True)
app = typer.Typer(
    help="Ask multiple LLM providers the same prompt concurrently via "
    "llm-gateway-service and show their answers side by side."
)

DEFAULT_GATEWAY_URL = os.environ.get("LLM_GATEWAY_URL", "http://127.0.0.1:8788")


@app.command()
def main(
    user: Annotated[str, typer.Argument(help="The prompt to send to every model")],
    calls: Annotated[
        list[str],
        typer.Option(
            "--call",
            "-c",
            help='"provider" or "provider:model", repeatable, e.g. -c anthropic:claude-haiku-4-5-20251001 -c ollama:llama3.2:3b',
        ),
    ] = [],  # noqa: B006 - typer reads this at decoration time, never mutated per-call
    system: Annotated[str, typer.Option("--system", "-s", help="System prompt")] = "Answer concisely.",
    gateway_url: Annotated[str, typer.Option("--gateway-url", help="llm-gateway-service URL")] = DEFAULT_GATEWAY_URL,
) -> None:
    """Send one prompt to every named provider/model concurrently and print each answer."""
    if not calls:
        console.print("[red]Error: pass at least one --call provider[:model][/red]")
        raise typer.Exit(1)

    parsed_calls = parse_calls(calls)
    try:
        outcome = run_compare(gateway_url, system, user, parsed_calls)
    except CompareError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e

    table = Table("provider", "model", "answer", "duration_ms")
    for r in outcome.results:
        answer = r["text"] if r["text"] else f"[red]ERROR: {r['error']}[/red]"
        table.add_row(r["provider"], r["model"], answer, str(r["duration_ms"]))
    console.print(table)
    console.print(f"[dim]trace_id: {outcome.trace_id}[/dim]")


if __name__ == "__main__":
    app()
