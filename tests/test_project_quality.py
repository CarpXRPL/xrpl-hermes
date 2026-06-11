"""Run the project quality audit (scripts/audit_project_quality.py) as a pytest gate.

Each audit check becomes one test, so a regression (a committed seed, hostile
wording, command-count drift, version drift, or an unsafe long currency
literal) fails the suite and CI instead of waiting for a manual audit run.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_project_quality import CHECKS, _tracked_files


@pytest.fixture(scope="module")
def tracked_files():
    try:
        return _tracked_files()
    except Exception:
        pytest.skip("git not available — audit needs a git checkout")


@pytest.mark.parametrize("name,check", CHECKS, ids=[name for name, _ in CHECKS])
def test_audit_check(name, check, tracked_files):
    findings = check(tracked_files)
    assert not findings, f"audit check '{name}' failed:\n" + "\n".join(findings)
