#!/usr/bin/env python3
"""Validate a BMAT tool-binding registry and tool-call ledger.

This local checker enforces the execution-layer policy
(``references/execution-layer-policy.md``): tools are declared in a registry,
every recorded call references a registered tool, and every tool-backed claim
has at least one matching successful call. It is intentionally deterministic —
it does not call models, browse the web, or transmit workspace context — and it
never fabricates a result: an assertion that a tool was used without a matching
call is flagged, not assumed true.

Usage:
    python3 scripts/bmat_tool_ledger_check.py binding.json [--json]
    python3 scripts/bmat_tool_ledger_check.py --selftest
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

try:
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover - depends on local environment
    jsonschema = None


ALLOWED_SURFACES = {"mcp", "skill", "code", "web"}
ALLOWED_STATUSES = {"success", "failure", "downgraded", "skipped"}
ALLOWED_DOWNGRADE_LABELS = {
    "not-checked",
    "plan-only",
    "inline-only",
    "partial",
    "source-corpus-gap",
    "validator_unavailable_due_to_runtime",
}
ALLOWED_OUTPUT_KINDS = {
    "citation_set",
    "record",
    "dataset_metadata",
    "statistic",
    "figure",
    "table",
    "text",
    "structured_json",
}
# A ledger status that counts as "the tool actually ran and produced output".
BACKING_STATUSES = {"success"}


@dataclass
class Finding:
    level: str
    code: str
    message: str
    path: str = ""


def read_json(path: Path, findings: list[Finding]) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        findings.append(Finding("ERROR", "LEDGER_FILE_MISSING", f"File not found: {path}"))
    except json.JSONDecodeError as exc:
        findings.append(Finding("ERROR", "LEDGER_JSON_INVALID", f"Invalid JSON in {path}: {exc}"))
    return {}


def _schema_path() -> Path:
    return Path(__file__).resolve().parent.parent / "contracts" / "tool-binding.schema.json"


def validate_schema(instance: dict[str, Any], findings: list[Finding]) -> None:
    if jsonschema is None:
        findings.append(
            Finding(
                "INFO",
                "LEDGER_SCHEMA_SKIPPED",
                "jsonschema not installed; structural schema check skipped (invariant checks still run)",
            )
        )
        return
    schema_path = _schema_path()
    try:
        with schema_path.open(encoding="utf-8") as handle:
            schema = json.load(handle)
    except FileNotFoundError:
        findings.append(Finding("ERROR", "LEDGER_SCHEMA_MISSING", f"Schema not found: {schema_path}"))
        return
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in error.path)
        findings.append(Finding("ERROR", "LEDGER_SCHEMA_VIOLATION", error.message, loc))


def validate_registry(registry: list[dict[str, Any]], findings: list[Finding]) -> set[str]:
    """Return the set of registered tool_ids; append findings for problems."""
    tool_ids: set[str] = set()
    for idx, entry in enumerate(registry):
        loc = f"tool_registry[{idx}]"
        tid = entry.get("tool_id", "")
        if not tid:
            findings.append(Finding("ERROR", "REGISTRY_TOOL_ID_MISSING", "tool_registry entry lacks tool_id", loc))
            continue
        if tid in tool_ids:
            findings.append(Finding("ERROR", "REGISTRY_TOOL_ID_DUPLICATE", f"Duplicate tool_id: {tid}", loc))
        tool_ids.add(tid)
        if not entry.get("capability"):
            findings.append(Finding("ERROR", "REGISTRY_CAPABILITY_MISSING", f"{tid} lacks capability", loc))
        surface = entry.get("surface", "")
        if surface not in ALLOWED_SURFACES:
            findings.append(
                Finding("ERROR", "REGISTRY_SURFACE_INVALID", f"{tid} surface {surface!r} not in {sorted(ALLOWED_SURFACES)}", loc)
            )
        output_kind = entry.get("output_kind", "")
        if output_kind and output_kind not in ALLOWED_OUTPUT_KINDS:
            findings.append(
                Finding("ERROR", "REGISTRY_OUTPUT_KIND_INVALID", f"{tid} output_kind {output_kind!r} not allowed", loc)
            )
        dl = entry.get("downgrade_label")
        if dl is not None and dl not in ALLOWED_DOWNGRADE_LABELS:
            findings.append(
                Finding("ERROR", "REGISTRY_DOWNGRADE_LABEL_INVALID", f"{tid} downgrade_label {dl!r} not allowed", loc)
            )
    return tool_ids


def validate_ledger(
    ledger: list[dict[str, Any]],
    tool_ids: set[str],
    findings: list[Finding],
) -> dict[str, set[str]]:
    """Return mapping claim_id -> set of statuses of calls that touched it."""
    claim_status: dict[str, set[str]] = {}
    seen_call_ids: set[str] = set()
    for idx, entry in enumerate(ledger):
        loc = f"tool_call_ledger[{idx}]"
        cid = entry.get("call_id", "")
        if not cid:
            findings.append(Finding("ERROR", "LEDGER_CALL_ID_MISSING", "ledger entry lacks call_id", loc))
        elif cid in seen_call_ids:
            findings.append(Finding("ERROR", "LEDGER_CALL_ID_DUPLICATE", f"Duplicate call_id: {cid}", loc))
        else:
            seen_call_ids.add(cid)

        tid = entry.get("tool_id", "")
        if not tid:
            findings.append(Finding("ERROR", "LEDGER_TOOL_ID_MISSING", "ledger entry lacks tool_id", loc))
        elif tid not in tool_ids:
            findings.append(
                Finding("ERROR", "LEDGER_TOOL_ID_UNREGISTERED", f"call {cid} references unregistered tool_id {tid!r}", loc)
            )

        status = entry.get("status", "")
        if status not in ALLOWED_STATUSES:
            findings.append(
                Finding("ERROR", "LEDGER_STATUS_INVALID", f"call {cid} status {status!r} not in {sorted(ALLOWED_STATUSES)}", loc)
            )

        # A downgraded/skipped row must carry an allowed downgrade_label.
        if status in {"downgraded", "skipped"}:
            dl = entry.get("downgrade_label")
            if dl is None:
                findings.append(
                    Finding("ERROR", "LEDGER_DOWNGRADE_LABEL_REQUIRED", f"call {cid} is {status} but has no downgrade_label", loc)
                )
            elif dl not in ALLOWED_DOWNGRADE_LABELS:
                findings.append(
                    Finding("ERROR", "LEDGER_DOWNGRADE_LABEL_INVALID", f"call {cid} downgrade_label {dl!r} not allowed", loc)
                )

        # A successful call should record an output reference (provenance anchor).
        if status == "success" and not entry.get("output_ref"):
            findings.append(
                Finding("WARN", "LEDGER_SUCCESS_NO_OUTPUT_REF", f"call {cid} succeeded but records no output_ref", loc)
            )

        for claim_id in entry.get("affected_claim_ids", []) or []:
            claim_status.setdefault(claim_id, set()).add(status)
    return claim_status


def validate_claim_backing(
    tool_backed_claim_ids: list[str],
    claim_status: dict[str, set[str]],
    findings: list[Finding],
) -> None:
    """Every claim asserted to be tool-backed must have >=1 successful call.

    This is the anti-fabrication invariant: a "used"/"checked"/"queried"
    assertion without a matching successful ledger row is flagged.
    """
    for claim_id in tool_backed_claim_ids:
        statuses = claim_status.get(claim_id, set())
        if not statuses:
            findings.append(
                Finding(
                    "ERROR",
                    "CLAIM_NO_TOOL_CALL",
                    f"tool-backed claim {claim_id!r} has no ledger entry (unbacked 'used' assertion)",
                )
            )
        elif not (statuses & BACKING_STATUSES):
            findings.append(
                Finding(
                    "ERROR",
                    "CLAIM_NO_SUCCESSFUL_CALL",
                    f"tool-backed claim {claim_id!r} has calls {sorted(statuses)} but none succeeded",
                )
            )


def validate_binding(instance: dict[str, Any], findings: list[Finding]) -> None:
    registry = instance.get("tool_registry", [])
    ledger = instance.get("tool_call_ledger", [])
    if not isinstance(registry, list):
        findings.append(Finding("ERROR", "REGISTRY_NOT_LIST", "tool_registry must be a list"))
        registry = []
    if not isinstance(ledger, list):
        findings.append(Finding("ERROR", "LEDGER_NOT_LIST", "tool_call_ledger must be a list"))
        ledger = []
    tool_ids = validate_registry(registry, findings)
    claim_status = validate_ledger(ledger, tool_ids, findings)
    # tool_backed_claim_ids is an optional top-level hint: claims that final
    # wording asserts are tool-backed. When absent, we derive it from any claim
    # that appears in the ledger (so an unbacked wording elsewhere is caught by
    # the writer's own claim-ledger gate, not here).
    declared = instance.get("tool_backed_claim_ids")
    if declared is None:
        declared = sorted(claim_status)
    validate_claim_backing(declared, claim_status, findings)


def emit(findings: list[Finding], as_json: bool) -> None:
    if not findings:
        findings = [Finding("INFO", "LEDGER_CHECK_PASSED", "BMAT tool-ledger validation passed")]
    if as_json:
        print(json.dumps([asdict(f) for f in findings], indent=2, sort_keys=True))
        return
    for f in findings:
        suffix = f" ({f.path})" if f.path else ""
        print(f"{f.level} {f.code}: {f.message}{suffix}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a BMAT tool-binding registry and tool-call ledger.")
    parser.add_argument("binding", nargs="?", help="Path to a tool-binding JSON instance.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    parser.add_argument("--selftest", action="store_true", help="Run built-in assertions and exit.")
    return parser.parse_args()


def _errors(findings: list[Finding]) -> list[str]:
    return [f.code for f in findings if f.level == "ERROR"]


def run_selftest() -> int:  # noqa: C901 - linear assertion block by design
    # 1. Clean instance: one registered tool, one successful call backing a claim.
    clean = {
        "tool_registry": [
            {"tool_id": "pubmed.lookup", "capability": "PMID metadata", "surface": "mcp",
             "output_kind": "citation_set", "downgrade_label": "not-checked"},
        ],
        "tool_call_ledger": [
            {"call_id": "C1", "tool_id": "pubmed.lookup", "status": "success",
             "output_ref": "PMID:1", "affected_claim_ids": ["H1"]},
        ],
    }
    f: list[Finding] = []
    validate_binding(clean, f)
    assert _errors(f) == [], f"clean instance should pass, got {_errors(f)}"

    # 2. Registry set correctly returned.
    f = []
    ids = validate_registry(clean["tool_registry"], f)
    assert ids == {"pubmed.lookup"}, ids
    assert _errors(f) == [], _errors(f)

    # 3. Duplicate tool_id flagged.
    dup = [dict(clean["tool_registry"][0]), dict(clean["tool_registry"][0])]
    f = []
    validate_registry(dup, f)
    assert "REGISTRY_TOOL_ID_DUPLICATE" in _errors(f), _errors(f)

    # 4. Missing tool_id in registry flagged.
    f = []
    validate_registry([{"capability": "x", "surface": "mcp", "output_kind": "text"}], f)
    assert "REGISTRY_TOOL_ID_MISSING" in _errors(f), _errors(f)

    # 5. Missing capability flagged.
    f = []
    validate_registry([{"tool_id": "t", "surface": "mcp", "output_kind": "text"}], f)
    assert "REGISTRY_CAPABILITY_MISSING" in _errors(f), _errors(f)

    # 6. Invalid surface flagged.
    f = []
    validate_registry([{"tool_id": "t", "capability": "c", "surface": "telepathy", "output_kind": "text"}], f)
    assert "REGISTRY_SURFACE_INVALID" in _errors(f), _errors(f)

    # 7. Invalid output_kind flagged.
    f = []
    validate_registry([{"tool_id": "t", "capability": "c", "surface": "mcp", "output_kind": "vibes"}], f)
    assert "REGISTRY_OUTPUT_KIND_INVALID" in _errors(f), _errors(f)

    # 8. Invalid registry downgrade_label flagged.
    f = []
    validate_registry([{"tool_id": "t", "capability": "c", "surface": "mcp",
                        "output_kind": "text", "downgrade_label": "nope"}], f)
    assert "REGISTRY_DOWNGRADE_LABEL_INVALID" in _errors(f), _errors(f)

    # 9. Ledger referencing unregistered tool flagged.
    f = []
    cs = validate_ledger(
        [{"call_id": "C1", "tool_id": "ghost", "status": "success", "output_ref": "x"}],
        {"pubmed.lookup"}, f)
    assert "LEDGER_TOOL_ID_UNREGISTERED" in _errors(f), _errors(f)

    # 10. Ledger claim_status mapping is correct.
    f = []
    cs = validate_ledger(
        [{"call_id": "C1", "tool_id": "pubmed.lookup", "status": "success",
          "output_ref": "x", "affected_claim_ids": ["H1", "H2"]}],
        {"pubmed.lookup"}, f)
    assert cs == {"H1": {"success"}, "H2": {"success"}}, cs

    # 11. Duplicate call_id flagged.
    f = []
    validate_ledger(
        [{"call_id": "C1", "tool_id": "pubmed.lookup", "status": "success", "output_ref": "x"},
         {"call_id": "C1", "tool_id": "pubmed.lookup", "status": "success", "output_ref": "y"}],
        {"pubmed.lookup"}, f)
    assert "LEDGER_CALL_ID_DUPLICATE" in _errors(f), _errors(f)

    # 12. Missing call_id flagged.
    f = []
    validate_ledger([{"tool_id": "pubmed.lookup", "status": "success", "output_ref": "x"}], {"pubmed.lookup"}, f)
    assert "LEDGER_CALL_ID_MISSING" in _errors(f), _errors(f)

    # 13. Missing tool_id in ledger flagged.
    f = []
    validate_ledger([{"call_id": "C1", "status": "success", "output_ref": "x"}], {"pubmed.lookup"}, f)
    assert "LEDGER_TOOL_ID_MISSING" in _errors(f), _errors(f)

    # 14. Invalid status flagged.
    f = []
    validate_ledger([{"call_id": "C1", "tool_id": "pubmed.lookup", "status": "maybe"}], {"pubmed.lookup"}, f)
    assert "LEDGER_STATUS_INVALID" in _errors(f), _errors(f)

    # 15. Downgraded without label flagged.
    f = []
    validate_ledger([{"call_id": "C1", "tool_id": "pubmed.lookup", "status": "downgraded"}], {"pubmed.lookup"}, f)
    assert "LEDGER_DOWNGRADE_LABEL_REQUIRED" in _errors(f), _errors(f)

    # 16. Downgraded with invalid label flagged.
    f = []
    validate_ledger(
        [{"call_id": "C1", "tool_id": "pubmed.lookup", "status": "downgraded", "downgrade_label": "bogus"}],
        {"pubmed.lookup"}, f)
    assert "LEDGER_DOWNGRADE_LABEL_INVALID" in _errors(f), _errors(f)

    # 17. Skipped with valid label passes (no error).
    f = []
    validate_ledger(
        [{"call_id": "C1", "tool_id": "pubmed.lookup", "status": "skipped", "downgrade_label": "not-checked"}],
        {"pubmed.lookup"}, f)
    assert _errors(f) == [], _errors(f)

    # 18. Success without output_ref warns (not error).
    f = []
    validate_ledger([{"call_id": "C1", "tool_id": "pubmed.lookup", "status": "success"}], {"pubmed.lookup"}, f)
    assert _errors(f) == [], _errors(f)
    assert any(x.code == "LEDGER_SUCCESS_NO_OUTPUT_REF" for x in f), [x.code for x in f]

    # 19. Anti-fabrication: declared tool-backed claim with no ledger entry.
    f = []
    validate_claim_backing(["H_ghost"], {}, f)
    assert "CLAIM_NO_TOOL_CALL" in _errors(f), _errors(f)

    # 20. Anti-fabrication: claim with only failed/downgraded calls (no success).
    f = []
    validate_claim_backing(["H1"], {"H1": {"failure", "downgraded"}}, f)
    assert "CLAIM_NO_SUCCESSFUL_CALL" in _errors(f), _errors(f)

    # 21. Claim with a success among others passes.
    f = []
    validate_claim_backing(["H1"], {"H1": {"failure", "success"}}, f)
    assert _errors(f) == [], _errors(f)

    # 22. End-to-end: unbacked declared claim caught through validate_binding.
    bad = {
        "tool_registry": clean["tool_registry"],
        "tool_call_ledger": [],
        "tool_backed_claim_ids": ["H_missing"],
    }
    f = []
    validate_binding(bad, f)
    assert "CLAIM_NO_TOOL_CALL" in _errors(f), _errors(f)

    # 23. End-to-end: downgraded call backing a claim => no success => flagged
    #     only when the claim is declared tool-backed.
    dg = {
        "tool_registry": clean["tool_registry"],
        "tool_call_ledger": [
            {"call_id": "C1", "tool_id": "pubmed.lookup", "status": "downgraded",
             "downgrade_label": "not-checked", "affected_claim_ids": ["H1"]},
        ],
        "tool_backed_claim_ids": ["H1"],
    }
    f = []
    validate_binding(dg, f)
    assert "CLAIM_NO_SUCCESSFUL_CALL" in _errors(f), _errors(f)

    # 24. Non-list registry/ledger flagged.
    f = []
    validate_binding({"tool_registry": {}, "tool_call_ledger": {}}, f)
    assert "REGISTRY_NOT_LIST" in _errors(f) and "LEDGER_NOT_LIST" in _errors(f), _errors(f)

    # 25. Allowed-set constants are internally consistent (no accidental drift).
    assert "success" in BACKING_STATUSES and BACKING_STATUSES <= ALLOWED_STATUSES
    assert ALLOWED_SURFACES == {"mcp", "skill", "code", "web"}
    assert "validator_unavailable_due_to_runtime" in ALLOWED_DOWNGRADE_LABELS

    # 26. Parametric: every allowed surface is accepted by the registry.
    for surface in sorted(ALLOWED_SURFACES):
        f = []
        validate_registry([{"tool_id": "t", "capability": "c", "surface": surface, "output_kind": "text"}], f)
        assert "REGISTRY_SURFACE_INVALID" not in _errors(f), f"surface {surface} should be valid: {_errors(f)}"

    # 27. Parametric: representative invalid surfaces are rejected.
    for surface in ("MCP", "api", "", "shell", "notebook"):
        f = []
        validate_registry([{"tool_id": "t", "capability": "c", "surface": surface, "output_kind": "text"}], f)
        assert "REGISTRY_SURFACE_INVALID" in _errors(f), f"surface {surface!r} should be invalid"

    # 28. Parametric: every allowed output_kind is accepted.
    for ok in sorted(ALLOWED_OUTPUT_KINDS):
        f = []
        validate_registry([{"tool_id": "t", "capability": "c", "surface": "mcp", "output_kind": ok}], f)
        assert "REGISTRY_OUTPUT_KIND_INVALID" not in _errors(f), f"output_kind {ok} should be valid: {_errors(f)}"

    # 29. Parametric: representative invalid output_kinds are rejected.
    for ok in ("Table", "json", "plot", "number", "vibes"):
        f = []
        validate_registry([{"tool_id": "t", "capability": "c", "surface": "mcp", "output_kind": ok}], f)
        assert "REGISTRY_OUTPUT_KIND_INVALID" in _errors(f), f"output_kind {ok!r} should be invalid"

    # 30. Parametric: every allowed downgrade_label is accepted in the registry.
    for dl in sorted(ALLOWED_DOWNGRADE_LABELS):
        f = []
        validate_registry(
            [{"tool_id": "t", "capability": "c", "surface": "mcp", "output_kind": "text", "downgrade_label": dl}], f)
        assert "REGISTRY_DOWNGRADE_LABEL_INVALID" not in _errors(f), f"label {dl} should be valid: {_errors(f)}"

    # 31. Parametric: every allowed ledger status is accepted (status not flagged invalid).
    for status in sorted(ALLOWED_STATUSES):
        entry = {"call_id": "C1", "tool_id": "pubmed.lookup", "status": status, "output_ref": "x"}
        if status in {"downgraded", "skipped"}:
            entry["downgrade_label"] = "not-checked"
        f = []
        validate_ledger([entry], {"pubmed.lookup"}, f)
        assert "LEDGER_STATUS_INVALID" not in _errors(f), f"status {status} should be valid: {_errors(f)}"

    # 32. Parametric: representative invalid statuses are rejected.
    for status in ("ok", "SUCCESS", "done", "error", ""):
        f = []
        validate_ledger([{"call_id": "C1", "tool_id": "pubmed.lookup", "status": status}], {"pubmed.lookup"}, f)
        assert "LEDGER_STATUS_INVALID" in _errors(f), f"status {status!r} should be invalid"

    # 33. Parametric: each downgrade status requires a label (both flagged when absent).
    for status in ("downgraded", "skipped"):
        f = []
        validate_ledger([{"call_id": "C1", "tool_id": "pubmed.lookup", "status": status}], {"pubmed.lookup"}, f)
        assert "LEDGER_DOWNGRADE_LABEL_REQUIRED" in _errors(f), f"{status} without label should flag"

    # 34. Parametric: claim backed by exactly one status behaves correctly.
    for status in sorted(ALLOWED_STATUSES):
        f = []
        validate_claim_backing(["H1"], {"H1": {status}}, f)
        if status == "success":
            assert _errors(f) == [], f"single success should pass, got {_errors(f)}"
        else:
            assert "CLAIM_NO_SUCCESSFUL_CALL" in _errors(f), f"single {status} should flag"

    # 35. The shipped schema file itself is a valid Draft 2020-12 schema and
    #     accepts the clean instance / rejects a structurally broken one.
    if jsonschema is not None:
        sp = _schema_path()
        if sp.exists():
            with sp.open(encoding="utf-8") as handle:
                shipped = json.load(handle)
            jsonschema.Draft202012Validator.check_schema(shipped)
            sv = jsonschema.Draft202012Validator(shipped)
            assert list(sv.iter_errors(clean)) == [], "clean instance must satisfy shipped schema"
            # Missing required top-level key must fail schema validation.
            assert list(sv.iter_errors({"tool_registry": []})), "missing tool_call_ledger must fail schema"
            # Unknown top-level property must fail (additionalProperties: false).
            assert list(sv.iter_errors({**clean, "surprise": 1})), "unknown property must fail schema"
            # Every allowed surface/output_kind/status round-trips through the schema.
            for surface in sorted(ALLOWED_SURFACES):
                inst = {"tool_registry": [{"tool_id": "t", "capability": "c",
                        "surface": surface, "output_kind": "text"}], "tool_call_ledger": []}
                assert list(sv.iter_errors(inst)) == [], f"schema should accept surface {surface}"
            for ok in sorted(ALLOWED_OUTPUT_KINDS):
                inst = {"tool_registry": [{"tool_id": "t", "capability": "c",
                        "surface": "mcp", "output_kind": ok}], "tool_call_ledger": []}
                assert list(sv.iter_errors(inst)) == [], f"schema should accept output_kind {ok}"
            for status in sorted(ALLOWED_STATUSES):
                entry = {"call_id": "C1", "tool_id": "t", "status": status}
                inst = {"tool_registry": [{"tool_id": "t", "capability": "c",
                        "surface": "mcp", "output_kind": "text"}], "tool_call_ledger": [entry]}
                assert list(sv.iter_errors(inst)) == [], f"schema should accept status {status}"

    # 36. Multi-tool end-to-end: two registered tools, mixed statuses, two claims
    #     each backed by >=1 success -> clean.
    multi = {
        "tool_registry": [
            {"tool_id": "pubmed.lookup", "capability": "PMID metadata", "surface": "mcp",
             "output_kind": "citation_set"},
            {"tool_id": "skill.pydeseq2", "capability": "bulk DEG", "surface": "skill",
             "output_kind": "table", "downgrade_label": "plan-only"},
        ],
        "tool_call_ledger": [
            {"call_id": "C1", "tool_id": "pubmed.lookup", "status": "success",
             "output_ref": "PMID:1", "affected_claim_ids": ["H1"]},
            {"call_id": "C2", "tool_id": "skill.pydeseq2", "status": "success",
             "output_ref": "artifact://deg.csv", "affected_claim_ids": ["H2"]},
            {"call_id": "C3", "tool_id": "skill.pydeseq2", "status": "downgraded",
             "downgrade_label": "plan-only", "affected_claim_ids": ["H2"]},
        ],
        "tool_backed_claim_ids": ["H1", "H2"],
    }
    f = []
    validate_binding(multi, f)
    assert _errors(f) == [], f"multi-tool clean instance should pass: {_errors(f)}"

    # 37. Registered-but-never-called tool is allowed (declaration != usage).
    f = []
    validate_binding({
        "tool_registry": [{"tool_id": "unused.tool", "capability": "c",
                           "surface": "web", "output_kind": "text"}],
        "tool_call_ledger": [],
    }, f)
    assert _errors(f) == [], f"registered-but-uncalled tool should pass: {_errors(f)}"

    # 38. Called-but-unregistered tool is always rejected, across every surface's
    #     worth of ledger statuses.
    for status in sorted(ALLOWED_STATUSES):
        entry = {"call_id": "C1", "tool_id": "ghost.tool", "status": status, "output_ref": "x"}
        if status in {"downgraded", "skipped"}:
            entry["downgrade_label"] = "not-checked"
        f = []
        validate_binding({"tool_registry": [], "tool_call_ledger": [entry]}, f)
        assert "LEDGER_TOOL_ID_UNREGISTERED" in _errors(f), f"unregistered tool with status {status} must flag"

    print("bmat_tool_ledger_check selftest: all assertions passed")
    return 0


def main() -> int:
    args = parse_args()
    if args.selftest:
        return run_selftest()
    if not args.binding:
        print("ERROR: provide a binding JSON path or --selftest", flush=True)
        return 2
    findings: list[Finding] = []
    instance = read_json(Path(args.binding), findings)
    if instance:
        validate_schema(instance, findings)
        validate_binding(instance, findings)
    emit(findings, args.json)
    return 1 if any(f.level == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
