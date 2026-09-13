"""Run the complete non-destructive release gate."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "tests" / "contracts" / "release_acceptance.json"


def _run(command: list[str], timeout: int) -> int:
    display = " ".join(command)
    print(f"[release] {display}", flush=True)
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=os.environ.copy(),
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"[timeout] {display}", file=sys.stderr, flush=True)
        return 1
    if completed.returncode:
        print(
            f"[failed:{completed.returncode}] {display}",
            file=sys.stderr,
            flush=True,
        )
    return completed.returncode


def _git_check(allow_dirty: bool) -> int:
    for revision in (None, "HEAD^..HEAD"):
        command = [
            "git", "-c", f"safe.directory={ROOT.as_posix()}",
            "diff", "--check",
        ]
        if revision:
            command.append(revision)
        diff_check = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if diff_check.returncode:
            print(
                diff_check.stdout or diff_check.stderr,
                file=sys.stderr,
                end="",
            )
            return diff_check.returncode or 1
    status = subprocess.run(
        [
            "git", "-c", f"safe.directory={ROOT.as_posix()}",
            "status", "--porcelain",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if status.returncode:
        print(status.stderr, file=sys.stderr, end="")
        return status.returncode or 1
    if status.stdout and not allow_dirty:
        print(
            "[failed] working tree is not clean:\n" + status.stdout,
            file=sys.stderr,
            end="",
        )
        return 1
    if status.stdout:
        print("[release] working tree check: DIRTY (allowed)", flush=True)
    else:
        print("[release] working tree check: CLEAN", flush=True)
    return 0


def _manual_check(contract: dict, results_path: Path | None) -> int:
    required = [item for item in contract["manual"] if item.get("required")]
    if results_path is None:
        print(
            f"[release] {len(required)} environment-dependent checks remain; "
            "use --manual-results with --require-manual for a release candidate",
            flush=True,
        )
        return 0
    try:
        payload = json.loads(results_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"[release] cannot read manual results: {error}", file=sys.stderr)
        return 1
    records = payload.get("checks") if set(payload) == {"checks"} else None
    if not isinstance(records, dict):
        print("[release] unsupported manual results format", file=sys.stderr)
        return 1
    failed = []
    for item in required:
        record = records.get(item["id"]) or {}
        if record.get("status") != "passed":
            failed.append(item["id"])
            continue
        if not record.get("tester") or not record.get("testedAt") or not record.get("evidence"):
            failed.append(item["id"])
    if failed:
        print(
            "[release] manual acceptance is incomplete: " + ", ".join(failed),
            file=sys.stderr,
        )
        return 1
    print(f"[release] {len(required)} manual checks passed", flush=True)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow tracked or untracked work while iterating",
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument(
        "--manual-results",
        type=Path,
        help="acceptance evidence created by tests/record_release_acceptance.py",
    )
    parser.add_argument(
        "--require-manual",
        action="store_true",
        help="fail unless every required environment-dependent check has evidence",
    )
    arguments = parser.parse_args(argv)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    started_at = time.perf_counter()
    if _git_check(arguments.allow_dirty):
        return 1
    for check in contract["automated"]:
        command = [sys.executable, *check["command"]]
        if _run(command, arguments.timeout):
            return 1
    if arguments.require_manual and arguments.manual_results is None:
        print("[release] --require-manual needs --manual-results", file=sys.stderr)
        return 2
    if arguments.manual_results is not None or arguments.require_manual:
        if _manual_check(contract, arguments.manual_results):
            return 1
    duration = time.perf_counter() - started_at
    manual = [item for item in contract["manual"] if item.get("required")]
    print(
        f"[release] automated gate passed in {duration:.2f}s; "
        f"{len(manual)} environment-dependent acceptance checks declared",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
