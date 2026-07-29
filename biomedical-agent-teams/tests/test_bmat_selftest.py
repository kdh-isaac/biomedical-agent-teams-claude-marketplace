from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SELFTEST = SKILL_ROOT / "scripts" / "bmat_selftest.py"


def run_selftest(*extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SELFTEST), "--root", str(SKILL_ROOT), *extra_args],
        text=True,
        capture_output=True,
        check=False,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def test_selftest_passes_against_the_installed_skill_root() -> None:
    result = run_selftest()

    assert result.returncode == 0, combined_output(result)
    assert "BMAT self-test passed." in result.stdout


def test_selftest_skip_golden_still_passes() -> None:
    result = run_selftest("--skip-golden")

    assert result.returncode == 0, combined_output(result)
    assert "BMAT self-test passed." in result.stdout
    assert "offline golden eval sample" not in result.stdout


def test_selftest_fails_on_missing_root() -> None:
    result = subprocess.run(
        [sys.executable, str(SELFTEST), "--root", str(SKILL_ROOT / "does-not-exist")],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "could not resolve BMAT skill root" in combined_output(result)
