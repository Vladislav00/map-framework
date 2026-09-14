"""Single owner of the ``codex exec --json`` wire format.

Every non-interactive Codex invocation in mapify (memory finalize, skill-eval
dispatch, description proposer) builds its argv here and folds the JSONL event
stream through :func:`parse_codex_exec_events`. A Codex schema change is then
one edit, and the parser is a pure function testable with a string.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

_CODEX_EXEC_BASE_ARGV: tuple[str, ...] = (
    "codex",
    "exec",
    "--json",
    "--sandbox",
    "read-only",
    "--ephemeral",
    "--ignore-user-config",
    "--ignore-rules",
    "--skip-git-repo-check",
)


def codex_exec_argv(*, model: str | None = None) -> list[str]:
    """argv for a read-only, non-interactive ``codex exec`` reading stdin."""
    argv = list(_CODEX_EXEC_BASE_ARGV)
    if model:
        argv += ["--model", model]
    argv.append("-")
    return argv


@dataclass
class CodexExecResult:
    """The parts of a ``codex exec --json`` stream mapify consumes."""

    response: str = ""
    """Text of the last completed ``agent_message`` item ("" when absent)."""
    usage: dict[str, int] = field(default_factory=dict)
    """Normalised token usage from ``turn.completed`` ({} when absent)."""


def normalize_codex_usage(raw_usage: dict[str, Any]) -> dict[str, int]:
    """Map Codex usage counters onto mapify's Claude-shaped token fields.

    Codex reports ``input_tokens`` as the total including cached prompt tokens;
    mapify (like the Claude API) counts uncached and cached input separately.
    """
    total_input = int(raw_usage.get("input_tokens", 0) or 0)
    cached_input = int(raw_usage.get("cached_input_tokens", 0) or 0)
    return {
        "input_tokens": max(0, total_input - cached_input),
        "cache_read_input_tokens": max(0, cached_input),
        "cache_creation_input_tokens": 0,
        "output_tokens": int(raw_usage.get("output_tokens", 0) or 0),
    }


def parse_codex_exec_events(stdout: str) -> CodexExecResult:
    """Fold ``codex exec --json`` JSONL into the final message and usage.

    Unknown event types and malformed lines are ignored for forward
    compatibility; the LAST completed ``agent_message`` wins.
    """
    result = CodexExecResult()
    for raw_line in stdout.splitlines():
        try:
            event: Any = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "item.completed":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    result.response = text
        elif event.get("type") == "turn.completed":
            usage = event.get("usage")
            if isinstance(usage, dict):
                result.usage = normalize_codex_usage(usage)
    return result
