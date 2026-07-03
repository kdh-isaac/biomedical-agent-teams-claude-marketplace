from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
LEDGER_CHECK = SKILL_ROOT / "scripts" / "bmat_tool_ledger_check.py"
FIXTURES = SKILL_ROOT / "tests" / "fixtures"


def run_ledger_check(fixture_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LEDGER_CHECK), str(FIXTURES / fixture_name / "binding.json")],
        text=True,
        capture_output=True,
        check=False,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def test_selftest_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(LEDGER_CHECK), "--selftest"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, combined_output(result)
    assert "all assertions passed" in result.stdout


def test_valid_binding_passes() -> None:
    result = run_ledger_check("tool_ledger_valid")
    assert result.returncode == 0, combined_output(result)
    assert "ERROR" not in result.stdout


def test_unregistered_tool_is_flagged() -> None:
    result = run_ledger_check("tool_ledger_invalid_unregistered_tool")
    assert result.returncode == 1
    assert "LEDGER_TOOL_ID_UNREGISTERED" in combined_output(result)


def test_unbacked_claim_is_flagged() -> None:
    result = run_ledger_check("tool_ledger_invalid_unbacked_claim")
    assert result.returncode == 1
    assert "CLAIM_NO_SUCCESSFUL_CALL" in combined_output(result)


def test_missing_file_is_flagged() -> None:
    result = subprocess.run(
        [sys.executable, str(LEDGER_CHECK), str(FIXTURES / "does_not_exist" / "binding.json")],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "LEDGER_FILE_MISSING" in combined_output(result)
