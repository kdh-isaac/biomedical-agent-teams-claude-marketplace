from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ENTAILMENT_CHECK = SKILL_ROOT / "scripts" / "bmat_entailment_check.py"
FIXTURES = SKILL_ROOT / "tests" / "fixtures"


def copytree_writable(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)
    for path in dst.rglob("*"):
        if path.is_dir():
            os.chmod(path, 0o755)
        else:
            os.chmod(path, 0o644)
    os.chmod(dst, 0o755)


def run_entailment_check(bundle: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENTAILMENT_CHECK), "--bundle", str(bundle), *extra_args],
        text=True,
        capture_output=True,
        check=False,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def test_valid_bundle_passes(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    copytree_writable(FIXTURES / "valid_full_protocol_bundle", bundle)

    result = run_entailment_check(bundle)

    assert result.returncode == 0, combined_output(result)
    assert "ERROR" not in result.stdout


def test_scope_mismatch_blocks_high_confidence_claim(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    copytree_writable(FIXTURES / "valid_full_protocol_bundle", bundle)
    ledger_path = bundle / "claim_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["claims"][0]["scope_match"]["species"] = "mismatch"
    ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    result = run_entailment_check(bundle)

    assert result.returncode == 1
    assert "SCOPE_MISMATCH_BLOCKS_HIGH_CONFIDENCE" in combined_output(result)


def test_json_output_is_valid_json(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    copytree_writable(FIXTURES / "valid_full_protocol_bundle", bundle)

    result = run_entailment_check(bundle, "--json")

    assert result.returncode == 0, combined_output(result)
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
