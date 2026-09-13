"""Run every test module in a fresh process to isolate Qt/QML global state."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def _excluded_module_names(excluded):
    return {
        value.removeprefix("tests.").removesuffix(".py")
        for value in excluded
    }


def test_modules(pattern="test_*.py", excluded=()):
    excluded_names = _excluded_module_names(excluded)
    return [
        f"tests.{path.stem}"
        for path in sorted(TESTS.glob(pattern))
        if path.stem != "run_isolated_suite"
        and path.stem not in excluded_names
    ]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="test module name to skip; may be passed more than once",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--timeout", type=int, default=120)
    arguments = parser.parse_args(argv)
    environment = os.environ.copy()
    started_at = time.perf_counter()
    passed = 0
    for module in test_modules(arguments.pattern, arguments.exclude):
        command = [sys.executable, "-m", "unittest", module]
        command.append("-v" if arguments.verbose else "-q")
        print(f"[isolated] {module}", flush=True)
        try:
            result = subprocess.run(
                command, cwd=ROOT, env=environment,
                timeout=arguments.timeout, check=False,
                capture_output=not arguments.verbose,
                text=not arguments.verbose,
            )
        except subprocess.TimeoutExpired:
            print(f"[timeout] {module}", file=sys.stderr, flush=True)
            return 1
        if result.returncode:
            if not arguments.verbose:
                if result.stdout:
                    print(result.stdout, file=sys.stderr, end="")
                if result.stderr:
                    print(result.stderr, file=sys.stderr, end="")
            print(
                f"[failed:{result.returncode}] {module}",
                file=sys.stderr, flush=True,
            )
            return result.returncode or 1
        passed += 1
    duration = time.perf_counter() - started_at
    print(
        f"[isolated] {passed} modules passed in {duration:.2f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
