from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = SKILL_ROOT.parent  # marketplace root: contains .claude-plugin/ and biomedical-agent-teams/
PACKAGE_CHECK = SKILL_ROOT / "scripts" / "bmat_package_check.py"
PLUGIN_JSON = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
ROUTER_ROOT_GUARD_PHRASE = (
    "Resolve every command recipe path relative to the directory containing this `SKILL.md`"
)
ROUTER_LAZY_LOAD_GUARD_PHRASE = (
    "Do not load every agent, command, reference, contract, or template by default."
)
ROUTER_INVENTORY_DISCOVERY_GUARD_PHRASE = (
    "Use `source-manifest.json` and `scripts/bmat_docs_list.py` for inventory discovery."
)
VALIDATOR_RUNTIME_DOWNGRADE_TOKEN = "validator_unavailable_due_to_runtime"
SKILL_ROUTER_MAX_BYTES = 16_000


def run_package_check(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PACKAGE_CHECK), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


def copy_plugin(tmp_path: Path) -> Path:
    target = tmp_path / "biomedical-agent-teams"
    ignore = shutil.ignore_patterns("__pycache__", ".pytest_cache")
    shutil.copytree(PLUGIN_ROOT, target, ignore=ignore)
    return target


def test_current_plugin_json_has_required_fields() -> None:
    payload = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))

    assert "name" in payload, "plugin.json missing 'name'"
    assert "version" in payload, "plugin.json missing 'version'"
    assert "description" in payload, "plugin.json missing 'description'"


def test_current_package_check_passes() -> None:
    result = run_package_check(PLUGIN_ROOT)

    assert result.returncode == 0, result.stdout + result.stderr


def test_current_skill_router_stays_under_loader_budget() -> None:
    skill_path = SKILL_ROOT / "SKILL.md"

    assert len(skill_path.read_bytes()) <= SKILL_ROUTER_MAX_BYTES


def test_package_check_flags_missing_plugin_field(tmp_path: Path) -> None:
    plugin_root = copy_plugin(tmp_path)
    plugin_json = plugin_root / ".claude-plugin" / "plugin.json"
    payload = json.loads(plugin_json.read_text(encoding="utf-8"))
    del payload["description"]
    plugin_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = run_package_check(plugin_root)

    assert result.returncode == 1
    assert "PLUGIN_FIELD_MISSING" in result.stdout


def test_package_check_flags_missing_skill_root_relative_router_guard(tmp_path: Path) -> None:
    plugin_root = copy_plugin(tmp_path)
    skill_path = plugin_root / "biomedical-agent-teams" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    skill_path.write_text(text.replace(ROUTER_ROOT_GUARD_PHRASE, ""), encoding="utf-8")

    result = run_package_check(plugin_root)

    assert result.returncode == 1
    assert "ROUTER_ROOT_GUARD_MISSING" in result.stdout


def test_package_check_flags_bloated_skill_router(tmp_path: Path) -> None:
    plugin_root = copy_plugin(tmp_path)
    skill_path = plugin_root / "biomedical-agent-teams" / "SKILL.md"
    skill_path.write_text(
        skill_path.read_text(encoding="utf-8") + "\n" + ("x" * (SKILL_ROUTER_MAX_BYTES + 1)),
        encoding="utf-8",
    )

    result = run_package_check(plugin_root)

    assert result.returncode == 1
    assert "SKILL_ROUTER_TOO_LARGE" in result.stdout


def test_package_check_flags_missing_lazy_load_guard(tmp_path: Path) -> None:
    plugin_root = copy_plugin(tmp_path)
    skill_path = plugin_root / "biomedical-agent-teams" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    skill_path.write_text(text.replace(ROUTER_LAZY_LOAD_GUARD_PHRASE, ""), encoding="utf-8")

    result = run_package_check(plugin_root)

    assert result.returncode == 1
    assert "ROUTER_LAZY_LOAD_GUARD_MISSING" in result.stdout


def test_package_check_flags_missing_inventory_discovery_guard(tmp_path: Path) -> None:
    plugin_root = copy_plugin(tmp_path)
    skill_path = plugin_root / "biomedical-agent-teams" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    skill_path.write_text(
        text.replace(ROUTER_INVENTORY_DISCOVERY_GUARD_PHRASE, ""),
        encoding="utf-8",
    )

    result = run_package_check(plugin_root)

    assert result.returncode == 1
    assert "ROUTER_INVENTORY_DISCOVERY_GUARD_MISSING" in result.stdout


def test_package_check_flags_missing_validator_runtime_downgrade_guard(tmp_path: Path) -> None:
    plugin_root = copy_plugin(tmp_path)
    skill_path = plugin_root / "biomedical-agent-teams" / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    skill_path.write_text(
        text.replace(VALIDATOR_RUNTIME_DOWNGRADE_TOKEN, "validator-runtime-token-removed"),
        encoding="utf-8",
    )

    result = run_package_check(plugin_root)

    assert result.returncode == 1
    assert "VALIDATOR_RUNTIME_DOWNGRADE_GUARD_MISSING" in result.stdout


def test_package_check_flags_source_manifest_missing_actual_command(tmp_path: Path) -> None:
    plugin_root = copy_plugin(tmp_path)
    source_manifest_path = plugin_root / "biomedical-agent-teams" / "source-manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest["commands"] = [
        command for command in source_manifest["commands"] if command != "omics-analysis-team"
    ]
    source_manifest_path.write_text(json.dumps(source_manifest, indent=2), encoding="utf-8")

    result = run_package_check(plugin_root)

    assert result.returncode == 1
    assert "SOURCE_MANIFEST_SET_MISMATCH" in result.stdout
