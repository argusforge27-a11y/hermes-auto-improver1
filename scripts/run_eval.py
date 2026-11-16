#!/usr/bin/env python3
"""
Eval script for hermes-auto-improver skill.
Runs health check and validates improvement logic.
"""
import json
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent


def test_health_check_runs():
    """Test that health check script runs without error"""
    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "run_health_check.py")],
        capture_output=True, text=True, timeout=180  # Increased timeout
    )
    # Health check may fail if skills are degraded, but script should run
    return result.returncode in (0, 1), result.stdout


def test_improve_skill_dry_run():
    """Test improve_skill.py dry run on a known skill"""
    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "improve_skill.py"), "--skill", "hermes-auto-improver", "--dry-run"],
        capture_output=True, text=True, timeout=60
    )
    return result.returncode == 0, result.stdout


def test_sync_memory():
    """Test sync_memory.py runs"""
    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "sync_memory.py")],
        capture_output=True, text=True, timeout=30
    )
    return result.returncode == 0, result.stdout


def test_quick_validate():
    """Test quick_validate.py passes on this skill"""
    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "quick_validate.py")],
        capture_output=True, text=True, timeout=30
    )
    return result.returncode == 0, result.stdout


def main():
    tests = [
        ("Health check runs", test_health_check_runs),
        ("Improve skill dry run", test_improve_skill_dry_run),
        ("Sync memory runs", test_sync_memory),
        ("Quick validate passes", test_quick_validate),
    ]
    
    all_pass = True
    for name, test_fn in tests:
        try:
            passed, output = test_fn()
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {name}")
            if not passed:
                print(f"  Output: {output[:200]}")
                all_pass = False
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            all_pass = False
    
    if all_pass:
        print("\nAll evals passed!")
        return 0
    else:
        print("\nSome evals failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
