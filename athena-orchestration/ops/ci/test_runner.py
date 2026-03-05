"""Test runner for CI/CD pipelines."""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_tests(
    test_path: str = "tests",
    verbose: bool = True,
    cov: bool = True,
    cov_report: str = "term",
) -> int:
    """
    Run pytest with common options.
    
    Args:
        test_path: Path to tests directory
        verbose: Enable verbose output
        cov: Enable coverage reporting
        cov_report: Coverage report format (term, xml, html)
        
    Returns:
        Exit code
    """
    args = ["python", "-m", "pytest", test_path]

    if verbose:
        args.append("-v")

    if cov:
        args.extend(["--cov=. --cov-report", cov_report])

    result = subprocess.run(args)
    return result.returncode


def run_linting() -> int:
    """Run ruff linting."""
    result = subprocess.run(["python", "-m", "ruff", "check", "."])
    return result.returncode


def run_format_check() -> int:
    """Run ruff format check."""
    result = subprocess.run(["python", "-m", "ruff", "format", "--check", "."])
    return result.returncode


def run_type_check() -> int:
    """Run mypy type checking."""
    result = subprocess.run(["python", "-m", "mypy", "."])
    return result.returncode


def run_security_scan() -> int:
    """Run security scan with bandit."""
    result = subprocess.run(["python", "-m", "bandit", "-r", "."])
    return result.returncode


def run_all_checks() -> int:
    """Run all CI checks in order."""
    checks = [
        ("Linting", run_linting),
        ("Format", run_format_check),
        ("Type Check", run_type_check),
        ("Security Scan", run_security_scan),
        ("Tests", run_tests),
    ]

    for name, check_func in checks:
        print(f"\n{'=' * 50}")
        print(f"Running: {name}")
        print("=" * 50)
        result = check_func()
        if result != 0:
            print(f"FAILED: {name}")
            return result

    print("\n" + "=" * 50)
    print("All checks passed!")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(run_all_checks())
