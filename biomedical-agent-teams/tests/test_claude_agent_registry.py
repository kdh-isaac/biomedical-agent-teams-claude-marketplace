"""Validate agent registry for Claude Code edition (no TOML templates)."""

import json
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent


def test_no_toml_template_paths():
    """Agent registry must not contain toml_template_path (Claude Code edition)."""
    registry_path = SKILL_ROOT / "agent-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    violations = [
        a["agent_id"]
        for a in registry.get("agents", [])
        if a.get("toml_template_path")
    ]
    assert not violations, f"Agents with legacy toml_template_path: {violations}"


def test_runtime_is_claude_code():
    """agent-registry.json runtime must be 'claude-code'."""
    registry_path = SKILL_ROOT / "agent-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry.get("runtime") == "claude-code", (
        f"Expected runtime='claude-code', got {registry.get('runtime')!r}"
    )


def test_no_codex_agents_directory():
    """codex-agents/ directory must not exist in Claude Code edition."""
    assert not (SKILL_ROOT / "codex-agents").exists(), (
        "codex-agents/ directory should be removed in Claude Code edition"
    )


def test_claude_plugin_directory_exists():
    """Marketplace root must have .claude-plugin/ directory."""
    marketplace_root = SKILL_ROOT.parent
    assert (marketplace_root / ".claude-plugin" / "marketplace.json").exists()
    assert (marketplace_root / ".claude-plugin" / "plugin.json").exists()
