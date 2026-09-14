"""The single registry of agent providers mapify can target.

Adding a provider is one entry here plus a dispatcher arm in
``skills_eval.dispatcher.dispatcher_for``; nothing else may spell the provider
names or their directories.
"""

from __future__ import annotations

from pathlib import Path

PROVIDER_SKILL_DIR: dict[str, str] = {"claude": ".claude", "codex": ".agents"}
"""Project directory that holds ``skills/`` for each provider."""

PROVIDER_TEMPLATE_SKILL_ROOT: dict[str, str] = {
    "claude": "skills",
    "codex": "codex/skills",
}
"""``templates_src``-relative skill root for each provider."""

SUPPORTED_PROVIDERS: frozenset[str] = frozenset(PROVIDER_SKILL_DIR)


def require_provider(provider: str) -> str:
    """Return *provider* or raise ``ValueError`` naming the supported set."""
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"unsupported provider {provider!r}; expected one of "
            f"{sorted(SUPPORTED_PROVIDERS)}"
        )
    return provider


def provider_dir(root: Path, provider: str) -> Path:
    """``<root>/.claude`` or ``<root>/.agents``."""
    return root / PROVIDER_SKILL_DIR[require_provider(provider)]


def skill_dir(root: Path, provider: str) -> Path:
    """``<root>/.claude/skills`` or ``<root>/.agents/skills``."""
    return provider_dir(root, provider) / "skills"


def template_skill_root(provider: str) -> Path:
    """``skills`` or ``codex/skills`` below ``templates_src``."""
    return Path(PROVIDER_TEMPLATE_SKILL_ROOT[require_provider(provider)])
