"""Record environment-dependent release checks with explicit evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "tests" / "contracts" / "release_acceptance.json"
DEFAULT_RESULTS = ROOT / ".release" / "acceptance.json"


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _results(path: Path) -> dict:
    if not path.exists():
        return {"checks": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"checks"} or not isinstance(
            payload.get("checks"), dict):
        raise ValueError("Unsupported acceptance results format")
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--pass", dest="passed")
    parser.add_argument("--fail")
    parser.add_argument("--tester", default="")
    parser.add_argument("--evidence", default="")
    arguments = parser.parse_args(argv)

    contract = _contract()
    checks = {item["id"]: item for item in contract["manual"]}
    try:
        results = _results(arguments.results)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"[acceptance] {error}", file=sys.stderr)
        return 1

    selected = arguments.passed or arguments.fail
    if selected:
        if selected not in checks:
            parser.error(f"unknown check: {selected}")
        if not arguments.tester.strip() or not arguments.evidence.strip():
            parser.error("--tester and --evidence are required when recording a result")
        results["checks"][selected] = {
            "status": "passed" if arguments.passed else "failed",
            "testedAt": datetime.now(timezone.utc).isoformat(),
            "tester": arguments.tester.strip(),
            "evidence": arguments.evidence.strip(),
        }
        arguments.results.parent.mkdir(parents=True, exist_ok=True)
        arguments.results.write_text(
            json.dumps(results, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    for identifier, item in checks.items():
        record = results["checks"].get(identifier) or {}
        status = record.get("status", "pending").upper()
        print(f"{status:7} {identifier}: {item['label']}")
        if record.get("evidence"):
            print(f"         {record['evidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
