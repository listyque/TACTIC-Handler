"""Run one user workflow through its isolated regression modules."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.support.vertical_workflows import modules_for, vertical_names


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vertical", choices=(*vertical_names(), "all"))
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    arguments = parser.parse_args(argv)
    started_at = time.perf_counter()
    modules = modules_for(arguments.vertical)
    for module in modules:
        command = [sys.executable, "-m", "unittest", module]
        command.append("-v" if arguments.verbose else "-q")
        print(f"[{arguments.vertical}] {module}", flush=True)
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                timeout=arguments.timeout,
                check=False,
                capture_output=not arguments.verbose,
                text=not arguments.verbose,
            )
        except subprocess.TimeoutExpired:
            print(f"[timeout] {module}", file=sys.stderr)
            return 1
        if completed.returncode:
            if not arguments.verbose:
                print(completed.stdout or "", file=sys.stderr, end="")
                print(completed.stderr or "", file=sys.stderr, end="")
            return completed.returncode or 1
    duration = time.perf_counter() - started_at
    print(
        f"[{arguments.vertical}] {len(modules)} modules passed "
        f"in {duration:.2f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
