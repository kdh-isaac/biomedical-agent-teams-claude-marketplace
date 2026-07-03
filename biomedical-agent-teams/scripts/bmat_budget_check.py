#!/usr/bin/env python3
"""Validate a BMAT tournament's compute-budget honesty.

This local checker enforces the compute-budget policy
(``references/compute-budget-policy.md``): a budget is a ceiling not a target,
the loop never exceeds it, and a result produced under an exhausted budget is
labelled ``budget_bounded`` rather than presented as converged. It is
deterministic — it does not call models, browse the web, or transmit workspace
context — and it never fabricates a verdict: a budget-bounded ranking that is
mislabelled as converged is flagged, not assumed honest.

The check couples three facts a tournament records:
  * the budget it ran under (``iteration_budget`` / ``max_pairwise_matches`` /
    ``max_candidates``),
  * how much it actually spent (``iterations_used``, per-round match counts),
  * and how it stopped (``stop_reason``) and labelled the result
    (``result_label``).

Usage:
    python3 scripts/bmat_budget_check.py tournament.json [--json]
    python3 scripts/bmat_budget_check.py --selftest
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

try:
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover - depends on local environment
    jsonschema = None


ALLOWED_STOP_REASONS = {
    "top_k_stable",
    "no_new_survivors",
    "budget_exhausted",
    "single_pass",
    "audit_only",
}
ALLOWED_RESULT_LABELS = {"converged", "budget_bounded", "single_pass", "audit_only"}
# Stop reasons that mean the loop reached its own convergence criterion — the
# result is NOT budget-bounded.
CONVERGED_STOP_REASONS = {"top_k_stable", "no_new_survivors"}
# Non-negative integer budget axes.
BUDGET_INT_FIELDS = ("iteration_budget", "max_pairwise_matches", "max_candidates")


@dataclass
class Finding:
    level: str
    code: str
    message: str
    path: str = ""


def read_json(path: Path, findings: list[Finding]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.append(Finding("ERROR", "TOURNAMENT_MISSING", "tournament artifact not found", str(path)))
    except json.JSONDecodeError as exc:
        findings.append(Finding("ERROR", "INVALID_JSON", f"tournament is not valid JSON: {exc}", str(path)))
    return None


def validate_schema(instance: Any, findings: list[Finding]) -> None:
    if jsonschema is None:
        findings.append(
            Finding("WARN", "SCHEMA_VALIDATION_SKIPPED", "install jsonschema to validate tournament schema shape")
        )
        return
    schema_path = Path(__file__).resolve().parent.parent / "contracts" / "hypothesis-tournament.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.validate(instance, schema)
    except FileNotFoundError:
        findings.append(Finding("WARN", "SCHEMA_FILE_MISSING", "tournament schema file missing", str(schema_path)))
    except jsonschema.ValidationError as exc:  # type: ignore[union-attr]
        findings.append(Finding("ERROR", "SCHEMA_VALIDATION_FAILED", f"tournament: {exc.message}", str(schema_path)))


def _int_or_none(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def validate_budget_fields(tournament: dict[str, Any], findings: list[Finding]) -> None:
    """Every declared budget axis is a non-negative integer."""
    for field_name in BUDGET_INT_FIELDS:
        if field_name not in tournament:
            continue
        value = tournament[field_name]
        if _int_or_none(value) is None:
            findings.append(
                Finding("ERROR", "BUDGET_NOT_INTEGER", f"{field_name} must be an integer, got {value!r}", field_name)
            )
        elif value < 0:
            findings.append(
                Finding("ERROR", "BUDGET_NEGATIVE", f"{field_name} must be >= 0, got {value}", field_name)
            )


def validate_not_exceeded(tournament: dict[str, Any], findings: list[Finding]) -> None:
    """The loop never spends more than its declared ceiling."""
    budget = _int_or_none(tournament.get("iteration_budget"))
    used = _int_or_none(tournament.get("iterations_used"))
    if budget is not None and used is not None and used > budget:
        findings.append(
            Finding(
                "ERROR",
                "BUDGET_EXCEEDED",
                f"iterations_used ({used}) exceeds iteration_budget ({budget}) — a budget is a hard ceiling",
                "iterations_used",
            )
        )


def validate_label_honesty(tournament: dict[str, Any], findings: list[Finding]) -> None:
    """stop_reason and result_label must agree: a budget-bounded result is
    never reported as converged, and vice versa."""
    stop_reason = tournament.get("stop_reason")
    result_label = tournament.get("result_label")

    if stop_reason is not None and stop_reason not in ALLOWED_STOP_REASONS:
        findings.append(
            Finding("ERROR", "STOP_REASON_INVALID", f"stop_reason '{stop_reason}' is not an allowed value", "stop_reason")
        )
    if result_label is not None and result_label not in ALLOWED_RESULT_LABELS:
        findings.append(
            Finding("ERROR", "RESULT_LABEL_INVALID", f"result_label '{result_label}' is not an allowed value", "result_label")
        )

    # Core honesty coupling: budget_exhausted <-> budget_bounded.
    if stop_reason == "budget_exhausted":
        if result_label is None:
            findings.append(
                Finding(
                    "ERROR",
                    "BUDGET_LABEL_MISSING",
                    "stop_reason is 'budget_exhausted' but no result_label is set — a budget-bounded result must be labelled 'budget_bounded'",
                    "result_label",
                )
            )
        elif result_label != "budget_bounded":
            findings.append(
                Finding(
                    "ERROR",
                    "BUDGET_LABEL_DISHONEST",
                    f"stop_reason is 'budget_exhausted' but result_label is '{result_label}' — must be 'budget_bounded'",
                    "result_label",
                )
            )

    if result_label == "budget_bounded" and stop_reason is not None and stop_reason != "budget_exhausted":
        findings.append(
            Finding(
                "ERROR",
                "BUDGET_LABEL_INCONSISTENT",
                f"result_label is 'budget_bounded' but stop_reason is '{stop_reason}' — expected 'budget_exhausted'",
                "stop_reason",
            )
        )

    # A converged stop reason must not be dressed as budget-bounded, and a
    # budget-bounded label must not claim convergence.
    if stop_reason in CONVERGED_STOP_REASONS and result_label == "budget_bounded":
        findings.append(
            Finding(
                "ERROR",
                "BUDGET_LABEL_INCONSISTENT",
                f"stop_reason '{stop_reason}' means the loop converged, but result_label claims 'budget_bounded'",
                "result_label",
            )
        )


def validate_tournament(tournament: Any, findings: list[Finding]) -> None:
    if not isinstance(tournament, dict):
        findings.append(Finding("ERROR", "TOURNAMENT_NOT_OBJECT", "tournament must be a JSON object"))
        return
    validate_budget_fields(tournament, findings)
    validate_not_exceeded(tournament, findings)
    validate_label_honesty(tournament, findings)


def emit(findings: list[Finding], as_json: bool) -> None:
    if not findings:
        findings = [Finding("INFO", "BUDGET_CHECK_PASSED", "BMAT compute-budget validation passed")]
    if as_json:
        print(json.dumps([asdict(f) for f in findings], indent=2, sort_keys=True))
        return
    for f in findings:
        suffix = f" ({f.path})" if f.path else ""
        print(f"{f.level} {f.code}: {f.message}{suffix}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a BMAT tournament's compute-budget honesty.")
    parser.add_argument("tournament", nargs="?", help="Path to a hypothesis-tournament JSON instance.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    parser.add_argument("--selftest", action="store_true", help="Run built-in assertions and exit.")
    return parser.parse_args()


def _errors(findings: list[Finding]) -> list[str]:
    return [f.code for f in findings if f.level == "ERROR"]


def run_selftest() -> int:  # noqa: C901 - linear assertion block by design
    # 1. Clean converged tournament: within budget, labelled converged.
    clean = {
        "tournament_id": "T1",
        "iteration_budget": 4,
        "iterations_used": 2,
        "max_candidates": 24,
        "max_pairwise_matches": 160,
        "stop_reason": "top_k_stable",
        "result_label": "converged",
    }
    f: list[Finding] = []
    validate_tournament(clean, f)
    assert _errors(f) == [], f"clean converged instance should pass, got {_errors(f)}"

    # 2. Clean budget-bounded tournament: exhausted + budget_bounded label.
    bounded = {
        "tournament_id": "T2",
        "iteration_budget": 2,
        "iterations_used": 2,
        "stop_reason": "budget_exhausted",
        "result_label": "budget_bounded",
    }
    f = []
    validate_tournament(bounded, f)
    assert _errors(f) == [], f"honest budget-bounded instance should pass, got {_errors(f)}"

    # 3. Budget exceeded flagged.
    f = []
    validate_tournament(dict(bounded, iterations_used=5), f)
    assert "BUDGET_EXCEEDED" in _errors(f), _errors(f)

    # 4. Exhausted but no label flagged.
    f = []
    validate_tournament({"stop_reason": "budget_exhausted"}, f)
    assert "BUDGET_LABEL_MISSING" in _errors(f), _errors(f)

    # 5. Exhausted but dishonestly labelled converged flagged.
    f = []
    validate_tournament({"stop_reason": "budget_exhausted", "result_label": "converged"}, f)
    assert "BUDGET_LABEL_DISHONEST" in _errors(f), _errors(f)

    # 6. budget_bounded label with a converged stop_reason flagged.
    f = []
    validate_tournament({"stop_reason": "top_k_stable", "result_label": "budget_bounded"}, f)
    assert "BUDGET_LABEL_INCONSISTENT" in _errors(f), _errors(f)

    # 7. budget_bounded label with a non-exhausted stop_reason flagged.
    f = []
    validate_tournament({"stop_reason": "single_pass", "result_label": "budget_bounded"}, f)
    assert "BUDGET_LABEL_INCONSISTENT" in _errors(f), _errors(f)

    # 8. Negative budget flagged.
    f = []
    validate_tournament({"max_candidates": -1}, f)
    assert "BUDGET_NEGATIVE" in _errors(f), _errors(f)

    # 9. Non-integer budget flagged.
    f = []
    validate_tournament({"iteration_budget": "lots"}, f)
    assert "BUDGET_NOT_INTEGER" in _errors(f), _errors(f)

    # 10. Invalid stop_reason flagged.
    f = []
    validate_tournament({"stop_reason": "ran_out_of_coffee"}, f)
    assert "STOP_REASON_INVALID" in _errors(f), _errors(f)

    # 11. Invalid result_label flagged.
    f = []
    validate_tournament({"result_label": "vibes"}, f)
    assert "RESULT_LABEL_INVALID" in _errors(f), _errors(f)

    # 12. Legacy tournament with no budget/label fields at all passes (backward compat).
    f = []
    validate_tournament({"tournament_id": "legacy"}, f)
    assert _errors(f) == [], f"legacy instance should pass, got {_errors(f)}"

    # 13. Boolean is not accepted as an integer budget (True == 1 guard).
    f = []
    validate_tournament({"iteration_budget": True}, f)
    assert "BUDGET_NOT_INTEGER" in _errors(f), _errors(f)

    # 14. iterations_used == iteration_budget is allowed (ceiling is inclusive).
    f = []
    validate_tournament(
        {"iteration_budget": 3, "iterations_used": 3, "stop_reason": "budget_exhausted", "result_label": "budget_bounded"},
        f,
    )
    assert _errors(f) == [], f"used==budget should pass, got {_errors(f)}"

    # 15. Non-object tournament flagged.
    f = []
    validate_tournament(["not", "an", "object"], f)
    assert "TOURNAMENT_NOT_OBJECT" in _errors(f), _errors(f)

    print("bmat_budget_check selftest: all assertions passed")
    return 0


def main() -> int:
    args = parse_args()
    if args.selftest:
        return run_selftest()
    if not args.tournament:
        print("ERROR: provide a tournament JSON path or --selftest", flush=True)
        return 2
    findings: list[Finding] = []
    instance = read_json(Path(args.tournament), findings)
    if instance is not None:
        validate_schema(instance, findings)
        validate_tournament(instance, findings)
    emit(findings, args.json)
    return 1 if any(f.level == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
