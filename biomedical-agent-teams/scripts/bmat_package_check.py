#!/usr/bin/env python3
"""Validate the Biomedical Agent Teams package layout (Claude Code edition).

This checks the plugin package itself, not an individual BMAT workflow artifact
bundle. It is intentionally dependency-free so it can run in source checkouts,
marketplace sources, and installed cache roots.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str
    path: str = ""


COUNT_KEYS = {
    "agent_count": ("agents", "*.md"),
    "command_count": ("commands", "*.md"),
    "template_count": ("templates", "*.md"),
    "contract_count": ("contracts", "*.json"),
    "reference_count": ("references", "*.md"),
    "loop_count": ("loops", "*.md"),
    "script_count": ("scripts", "*.py"),
}
SOURCE_MANIFEST_COLLECTIONS = {
    "commands": ("commands", ".md"),
    "agent_roster": ("agents", ".md"),
    "contracts": ("contracts", ".json"),
    "templates": ("templates", ".md"),
    "references": ("references", ".md"),
    "loops": ("loops", ".md"),
    "scripts": ("scripts", ".py"),
}
SKILL_ROUTER_MAX_BYTES = 16_000
ROUTER_ROOT_GUARD_PHRASE = (
    "Resolve every command recipe path relative to the directory containing this `SKILL.md`"
)
LAZY_LOAD_GUARD_PHRASES = {
    "ROUTER_LAZY_LOAD_GUARD_MISSING": "Do not load every agent, command, reference, contract, or template by default.",
    "ROUTER_INVENTORY_DISCOVERY_GUARD_MISSING": "Use `source-manifest.json` and `scripts/bmat_docs_list.py` for inventory discovery.",
    "VALIDATOR_RUNTIME_DOWNGRADE_GUARD_MISSING": "validator_unavailable_due_to_runtime",
    "VALIDATOR_FULL_PROTOCOL_CEILING_MISSING": "Do not claim `Full protocol followed`",
}


def count_golden_tasks(skill_root: Path, findings: list[Finding]) -> int:
    path = skill_root / "evals" / "golden_tasks.jsonl"
    text = read_text(path, findings)
    return sum(1 for line in text.splitlines() if line.strip())


def special_counts(skill_root: Path, findings: list[Finding]) -> dict[str, int]:
    return {
        "test_fixture_count": len([path for path in (skill_root / "tests" / "fixtures").iterdir() if path.is_dir()])
        if (skill_root / "tests" / "fixtures").exists()
        else 0,
        "eval_count": len(list((skill_root / "evals").glob("*.py"))),
        "golden_task_count": count_golden_tasks(skill_root, findings),
        "agent_registry_count": 1 if (skill_root / "agent-registry.json").exists() else 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a BMAT plugin package (Claude Code edition).")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="BMAT skill root, plugin root, marketplace repo root, or installed cache root.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable findings.")
    return parser.parse_args()


def read_json(path: Path, findings: list[Finding]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.append(Finding("ERROR", "FILE_MISSING", "JSON file missing", str(path)))
    except json.JSONDecodeError as exc:
        findings.append(Finding("ERROR", "INVALID_JSON", f"invalid JSON: {exc}", str(path)))
    return None


def read_text(path: Path, findings: list[Finding]) -> str:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        findings.append(Finding("ERROR", "FILE_MISSING", "file missing", str(path)))
        return ""
    if raw.startswith(b"\xef\xbb\xbf"):
        findings.append(
            Finding(
                "ERROR",
                "BOM_PRESENT",
                "file starts with a UTF-8 BOM; leading BOM breaks Markdown frontmatter parsing",
                str(path),
            )
        )
        raw = raw[3:]
    return raw.decode("utf-8")


def resolve_skill_root(root: Path, findings: list[Finding]) -> Path:
    root = root.resolve()
    candidates = [
        root,
        root / "biomedical-agent-teams",
        root / "skills" / "biomedical-agent-teams",
        root / "plugins" / "biomedical-agent-teams" / "skills" / "biomedical-agent-teams",
    ]
    for candidate in candidates:
        if (candidate / "SKILL.md").exists() and (candidate / "VERSION").exists():
            return candidate
    findings.append(
        Finding(
            "ERROR",
            "SKILL_ROOT_NOT_FOUND",
            "could not resolve BMAT skill root from --root",
            str(root),
        )
    )
    return root


def plugin_root_for(skill_root: Path) -> Path:
    """Return the plugin/marketplace root (where .claude-plugin/ lives)."""
    candidate = skill_root
    for _ in range(4):
        if (candidate / ".claude-plugin").exists():
            return candidate
        candidate = candidate.parent
    return skill_root


def frontmatter_value(frontmatter: str, key: str) -> str | None:
    match = re.search(rf"^{key}:\s*(.*)$", frontmatter, re.M)
    if not match:
        return None
    value = match.group(1).strip()
    if value and value not in {">", "|", ">-", "|-"}:
        return value.strip('"')

    tail = frontmatter[match.end() :].splitlines()
    block: list[str] = []
    for line in tail:
        if line and not line.startswith((" ", "\t")):
            break
        stripped = line.strip()
        if stripped:
            block.append(stripped)
    return " ".join(block) if block else None


def extract_frontmatter(text: str, path: Path, findings: list[Finding]) -> dict[str, str]:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
    if not match:
        findings.append(Finding("ERROR", "FRONTMATTER_MISSING", "frontmatter missing", str(path)))
        return {}
    frontmatter = match.group(1)
    out: dict[str, str] = {}
    for key in ("name", "description"):
        value = frontmatter_value(frontmatter, key)
        if value:
            out[key] = value
        else:
            findings.append(Finding("ERROR", "FRONTMATTER_FIELD_MISSING", f"{key} missing", str(path)))
    version_match = re.search(r'^\s*version:\s*"([^"]+)"\s*$', frontmatter, re.M)
    if version_match:
        out["version"] = version_match.group(1)
    else:
        findings.append(Finding("ERROR", "FRONTMATTER_VERSION_MISSING", "metadata.version missing", str(path)))
    return out


def expect_equal(
    actual: Any,
    expected: Any,
    code: str,
    message: str,
    path: Path | str,
    findings: list[Finding],
) -> None:
    if actual != expected:
        findings.append(
            Finding("ERROR", code, f"{message}: expected {expected!r}, found {actual!r}", str(path))
        )


def validate_versions(skill_root: Path, findings: list[Finding]) -> str:
    version = read_text(skill_root / "VERSION", findings).strip()
    plugin_root = plugin_root_for(skill_root)
    plugin_json_path = plugin_root / ".claude-plugin" / "plugin.json"
    plugin = read_json(plugin_json_path, findings)
    manifest = read_json(skill_root / "manifest.json", findings)
    source_manifest = read_json(skill_root / "source-manifest.json", findings)
    registry = read_json(skill_root / "agent-registry.json", findings)
    skill_text = read_text(skill_root / "SKILL.md", findings)
    frontmatter = extract_frontmatter(skill_text, skill_root / "SKILL.md", findings)

    if isinstance(plugin, dict):
        expect_equal(plugin.get("version"), version, "VERSION_MISMATCH", "plugin.json version mismatch", plugin_json_path, findings)
    if isinstance(manifest, dict):
        expect_equal(manifest.get("version"), version, "VERSION_MISMATCH", "manifest version mismatch", skill_root / "manifest.json", findings)
        expect_equal(manifest.get("adapter_version"), version, "VERSION_MISMATCH", "manifest adapter_version mismatch", skill_root / "manifest.json", findings)
    if isinstance(source_manifest, dict):
        expect_equal(source_manifest.get("version"), version, "VERSION_MISMATCH", "source-manifest version mismatch", skill_root / "source-manifest.json", findings)
    if isinstance(registry, dict):
        expect_equal(registry.get("version"), version, "VERSION_MISMATCH", "agent-registry version mismatch", skill_root / "agent-registry.json", findings)
    if frontmatter:
        expect_equal(frontmatter.get("version"), version, "VERSION_MISMATCH", "SKILL metadata version mismatch", skill_root / "SKILL.md", findings)

    return version


def validate_plugin_interface(skill_root: Path, findings: list[Finding]) -> None:
    """Validate Claude Code .claude-plugin/plugin.json and marketplace.json."""
    plugin_root = plugin_root_for(skill_root)
    plugin_json_path = plugin_root / ".claude-plugin" / "plugin.json"
    plugin = read_json(plugin_json_path, findings)
    if not isinstance(plugin, dict):
        return
    for required_field in ("name", "version", "description"):
        if not plugin.get(required_field):
            findings.append(
                Finding(
                    "ERROR",
                    "PLUGIN_FIELD_MISSING",
                    f"plugin.json missing required field: {required_field}",
                    str(plugin_json_path),
                )
            )
    marketplace_path = plugin_root / ".claude-plugin" / "marketplace.json"
    marketplace = read_json(marketplace_path, findings)
    if isinstance(marketplace, dict):
        if not marketplace.get("plugins"):
            findings.append(
                Finding(
                    "ERROR",
                    "MARKETPLACE_PLUGINS_MISSING",
                    "marketplace.json plugins array missing or empty",
                    str(marketplace_path),
                )
            )


def validate_counts(skill_root: Path, findings: list[Finding]) -> None:
    manifest = read_json(skill_root / "manifest.json", findings)
    source_manifest = read_json(skill_root / "source-manifest.json", findings)
    for key, (folder, pattern) in COUNT_KEYS.items():
        count = len(list((skill_root / folder).glob(pattern)))
        if isinstance(manifest, dict):
            expect_equal(manifest.get(key), count, "COUNT_MISMATCH", f"manifest {key} mismatch", skill_root / "manifest.json", findings)
        if isinstance(source_manifest, dict):
            expect_equal(source_manifest.get(key), count, "COUNT_MISMATCH", f"source-manifest {key} mismatch", skill_root / "source-manifest.json", findings)

    for key, count in special_counts(skill_root, findings).items():
        if isinstance(manifest, dict):
            expect_equal(manifest.get(key), count, "COUNT_MISMATCH", f"manifest {key} mismatch", skill_root / "manifest.json", findings)
        if isinstance(source_manifest, dict):
            expect_equal(source_manifest.get(key), count, "COUNT_MISMATCH", f"source-manifest {key} mismatch", skill_root / "source-manifest.json", findings)

    if isinstance(source_manifest, dict):
        for collection, (folder, suffix) in SOURCE_MANIFEST_COLLECTIONS.items():
            entries = source_manifest.get(collection, [])
            if not isinstance(entries, list):
                findings.append(
                    Finding(
                        "ERROR",
                        "SOURCE_MANIFEST_COLLECTION_INVALID",
                        f"{collection} must be a list",
                        str(skill_root / "source-manifest.json"),
                    )
                )
                continue
            invalid_entries = [entry for entry in entries if not isinstance(entry, str) or not entry.strip()]
            if invalid_entries:
                findings.append(
                    Finding(
                        "ERROR",
                        "SOURCE_MANIFEST_COLLECTION_INVALID",
                        f"{collection} contains non-string or blank entries",
                        str(skill_root / "source-manifest.json"),
                    )
                )
                continue
            listed = {entry.strip() for entry in entries}
            actual = {
                path.stem
                for path in (skill_root / folder).glob(f"*{suffix}")
                if path.is_file()
            }
            if listed != actual:
                findings.append(
                    Finding(
                        "ERROR",
                        "SOURCE_MANIFEST_SET_MISMATCH",
                        (
                            f"{collection} must exactly match {folder} resource stems; "
                            f"missing_from_manifest={sorted(actual - listed)!r}; "
                            f"stale_in_manifest={sorted(listed - actual)!r}"
                        ),
                        str(skill_root / "source-manifest.json"),
                    )
                )


def validate_registry(skill_root: Path, findings: list[Finding]) -> None:
    registry = read_json(skill_root / "agent-registry.json", findings)
    if not isinstance(registry, dict):
        return
    seen: set[str] = set()
    for index, agent in enumerate(registry.get("agents", [])):
        if not isinstance(agent, dict):
            findings.append(Finding("ERROR", "AGENT_REGISTRY_INVALID", f"agents[{index}] is not an object", str(skill_root / "agent-registry.json")))
            continue
        agent_id = str(agent.get("agent_id", "")).strip()
        if not agent_id:
            findings.append(Finding("ERROR", "AGENT_ID_MISSING", f"agents[{index}] missing agent_id", str(skill_root / "agent-registry.json")))
            continue
        if agent_id in seen:
            findings.append(Finding("ERROR", "AGENT_ID_DUPLICATE", f"duplicate agent_id: {agent_id}", str(skill_root / "agent-registry.json")))
        seen.add(agent_id)
        prompt_path = agent.get("prompt_path")
        if not prompt_path or not (skill_root / str(prompt_path)).exists():
            findings.append(Finding("ERROR", "PROMPT_PATH_MISSING", f"{agent_id} prompt_path missing or file not found", str(skill_root / "agent-registry.json")))
        # toml_template_path is not used in Claude Code edition
        if agent.get("toml_template_path"):
            findings.append(Finding("WARN", "LEGACY_TOML_PATH", f"{agent_id} has leftover toml_template_path (unused in Claude Code)", str(skill_root / "agent-registry.json")))


def validate_registry_schema(skill_root: Path, findings: list[Finding]) -> None:
    """Validate agent-registry.json against its own contract schema.

    Regression guard for contract drift: the runtime enum in
    contracts/agent-registry.schema.json once said ["codex"] while the shipped
    agent-registry.json declared runtime "claude-code", so the registry failed
    validation against its own schema. This check catches that class of bug at
    package time. It is optional: if `jsonschema` is not importable (the script
    is otherwise dependency-free), it is skipped silently.
    """
    schema_path = skill_root / "contracts" / "agent-registry.schema.json"
    registry_path = skill_root / "agent-registry.json"
    if not schema_path.exists() or not registry_path.exists():
        return
    try:
        import jsonschema  # type: ignore
    except Exception:
        return
    schema = read_json(schema_path, findings)
    registry = read_json(registry_path, findings)
    if not isinstance(schema, dict) or not isinstance(registry, dict):
        return
    try:
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema)
    except Exception as exc:
        findings.append(Finding("ERROR", "REGISTRY_SCHEMA_INVALID", f"agent-registry.schema.json is not a usable schema: {exc}", str(schema_path)))
        return
    for error in sorted(validator.iter_errors(registry), key=lambda e: list(e.path)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        findings.append(Finding("ERROR", "REGISTRY_SCHEMA_VIOLATION", f"agent-registry.json violates schema at {location}: {error.message}", str(registry_path)))


def validate_router_mentions(skill_root: Path, findings: list[Finding]) -> None:
    skill_path = skill_root / "SKILL.md"
    skill_text = read_text(skill_path, findings)
    source_manifest = read_json(skill_root / "source-manifest.json", findings)
    try:
        skill_size = len(skill_path.read_bytes())
    except FileNotFoundError:
        skill_size = 0
    if skill_size > SKILL_ROUTER_MAX_BYTES:
        findings.append(
            Finding(
                "ERROR",
                "SKILL_ROUTER_TOO_LARGE",
                (
                    "SKILL.md must remain a lightweight router and lazy-load "
                    f"command/reference docs: maximum {SKILL_ROUTER_MAX_BYTES} bytes, found {skill_size}"
                ),
                str(skill_path),
            )
        )
    normalized_skill_text = re.sub(r"\s+", " ", skill_text)
    if ROUTER_ROOT_GUARD_PHRASE not in skill_text:
        findings.append(
            Finding(
                "ERROR",
                "ROUTER_ROOT_GUARD_MISSING",
                "router must require command recipes to resolve relative to the active SKILL.md directory",
                str(skill_path),
            )
        )
    for code, phrase in LAZY_LOAD_GUARD_PHRASES.items():
        if phrase not in normalized_skill_text:
            findings.append(
                Finding(
                    "ERROR",
                    code,
                    f"router missing required lazy-load/runtime downgrade guard phrase: {phrase}",
                    str(skill_path),
                )
            )
    if not isinstance(source_manifest, dict):
        return
    for command in source_manifest.get("commands", []):
        if f"commands/{command}.md" not in skill_text:
            findings.append(Finding("ERROR", "ROUTER_REFERENCE_MISSING", f"router does not mention command {command}", str(skill_path)))


PROMPT_FRONTMATTER_REQUIRED = {
    "commands": ("description",),
    "agents": ("name", "description"),
}


def validate_prompt_frontmatter(skill_root: Path, findings: list[Finding]) -> None:
    """Command and agent prompts must open with a parseable frontmatter block.

    A leading UTF-8 BOM (flagged separately by read_text) or a missing `---`
    block causes Claude Code to drop the frontmatter, silently discarding
    command metadata (description/argument-hint/allowed-tools) or agent
    metadata (name/description/tools). Enforce it as an ERROR here so the
    package check catches it before publish.
    """
    for folder, required in PROMPT_FRONTMATTER_REQUIRED.items():
        for path in sorted((skill_root / folder).glob("*.md")):
            text = read_text(path, findings)
            match = re.match(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
            if not match:
                findings.append(
                    Finding(
                        "ERROR",
                        "PROMPT_FRONTMATTER_MISSING",
                        f"{folder} prompt is missing a parseable frontmatter block",
                        str(path),
                    )
                )
                continue
            frontmatter = match.group(1)
            for key in required:
                if not frontmatter_value(frontmatter, key):
                    findings.append(
                        Finding(
                            "ERROR",
                            "PROMPT_FRONTMATTER_FIELD_MISSING",
                            f"{folder} prompt frontmatter missing '{key}'",
                            str(path),
                        )
                    )


def validate_docs_inventory(skill_root: Path, findings: list[Finding]) -> None:
    for folder in ("commands", "references", "loops", "templates"):
        for path in sorted((skill_root / folder).glob("*.md")):
            text = read_text(path, findings)
            match = re.match(r"\A---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.S)
            if not match:
                continue
            frontmatter = match.group(1)
            if not (frontmatter_value(frontmatter, "summary") or frontmatter_value(frontmatter, "description")):
                findings.append(
                    Finding(
                        "WARN",
                        "DOC_FRONTMATTER_FIELD_MISSING",
                        "optional docs inventory summary or description missing",
                        str(path),
                    )
                )


def main() -> int:
    args = parse_args()
    findings: list[Finding] = []
    skill_root = resolve_skill_root(args.root, findings)
    if skill_root.exists():
        validate_versions(skill_root, findings)
        validate_plugin_interface(skill_root, findings)
        validate_counts(skill_root, findings)
        validate_registry(skill_root, findings)
        validate_registry_schema(skill_root, findings)
        validate_router_mentions(skill_root, findings)
        validate_prompt_frontmatter(skill_root, findings)
        validate_docs_inventory(skill_root, findings)

    if args.json:
        print(json.dumps([finding.__dict__ for finding in findings], indent=2, sort_keys=True))
    else:
        if findings:
            for finding in findings:
                print(f"{finding.level}: {finding.code}: {finding.message} {finding.path}".rstrip())
        else:
            print(f"BMAT package check passed (Claude Code edition): {skill_root}")

    return 1 if any(finding.level == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
