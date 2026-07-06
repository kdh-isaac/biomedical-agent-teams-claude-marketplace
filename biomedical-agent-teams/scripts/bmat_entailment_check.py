#!/usr/bin/env python3
"""Run BMAT semantic scope and entailment policy checks for a bundle."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import bmat_validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate BMAT claim entailment and scope policy.")
    parser.add_argument("--bundle", type=Path, required=True, help="Directory containing BMAT bundle artifacts.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON findings.")
    return parser.parse_args()


def input_namespace(bundle: Path) -> SimpleNamespace:
    values: dict[str, object] = {"bundle": bundle}
    for key in tuple(bmat_validate.BUNDLE_FILES) + tuple(bmat_validate.OPTIONAL_BUNDLE_FILES):
        values[key] = None
    return SimpleNamespace(**values)


def main() -> int:
    args = parse_args()
    findings: list[bmat_validate.Finding] = []
    paths = bmat_validate.input_paths(input_namespace(args.bundle))
    artifacts = bmat_validate.load_artifacts(paths, findings)
    bmat_validate.validate_schemas(artifacts, findings)
    bmat_validate.validate_semantic_scope_policy(artifacts, findings)
    bmat_validate.emit(findings, args.json)
    return 1 if any(finding.level == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
