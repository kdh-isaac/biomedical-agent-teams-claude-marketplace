from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUDGET_CHECK = SKILL_ROOT / "scripts" / "bmat_budget_check.py"
FIXTURES = SKILL_ROOT / "tests" / "fixtures"


def run_budget_check(fixture_name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUDGET_CHECK), str(FIXTURES / fixture_name / "tournament.json")],
        text=True,
        capture_output=True,
        check=False,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def test_selftest_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(BUDGET_CHECK), "--selftest"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, combined_output(result)
    assert "all assertions passed" in result.stdout


def test_valid_bounded_tournament_passes() -> None:
    result = run_budget_check("budget_valid_bounded")
    assert result.returncode == 0, combined_output(result)
    assert "ERROR" not in result.stdout


def test_dishonest_label_is_flagged() -> None:
    result = run_budget_check("budget_invalid_dishonest_label")
    assert result.returncode == 1
    assert "BUDGET_LABEL_DISHONEST" in combined_output(result)


def test_exceeded_budget_is_flagged() -> None:
    result = run_budget_check("budget_invalid_exceeded")
    assert result.returncode == 1
    assert "BUDGET_EXCEEDED" in combined_output(result)


def test_missing_file_is_flagged() -> None:
    result = subprocess.run(
        [sys.executable, str(BUDGET_CHECK), str(FIXTURES / "does_not_exist" / "tournament.json")],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "TOURNAMENT_MISSING" in combined_output(result)
