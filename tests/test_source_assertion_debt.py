from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
CONTRACT = TESTS / "contracts" / "source_assertion_debt.json"
SOURCE_READ_CALLS = {"getsource", "read_text"}


def _is_source_read(call: ast.Call) -> bool:
    function = call.func
    return (
        isinstance(function, ast.Attribute)
        and function.attr in SOURCE_READ_CALLS
    ) or (
        isinstance(function, ast.Name)
        and function.id in SOURCE_READ_CALLS
    )


def _is_assertion(node: ast.AST) -> bool:
    if isinstance(node, ast.Assert):
        return True
    if not isinstance(node, ast.Call):
        return False
    function = node.func
    return (
        isinstance(function, ast.Attribute)
        and function.attr.startswith("assert")
    )


def source_assertion_counts() -> dict[str, dict[str, int]]:
    counts: dict[str, Counter] = {}
    for path in sorted(TESTS.glob("test_*.py")):
        if path.resolve() == Path(__file__).resolve():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue
            nodes = list(ast.walk(node))
            if not any(
                _is_source_read(item)
                for item in nodes
                if isinstance(item, ast.Call)
            ):
                continue
            assertions = sum(_is_assertion(item) for item in nodes)
            if assertions:
                counter = counts.setdefault(relative, Counter())
                counter["tests"] += 1
                counter["assertions"] += assertions
    return {
        path: dict(sorted(values.items()))
        for path, values in sorted(counts.items())
    }


class SourceAssertionDebtTests(unittest.TestCase):
    def test_source_coupled_test_debt_only_decreases(self):
        budget = json.loads(CONTRACT.read_text(encoding="utf-8"))
        actual = source_assertion_counts()
        regressions = {}
        for path, values in actual.items():
            maximum = budget["max_by_file"].get(
                path, {"tests": 0, "assertions": 0}
            )
            growth = {
                metric: (value, maximum.get(metric, 0))
                for metric, value in values.items()
                if value > maximum.get(metric, 0)
            }
            if growth:
                regressions[path] = growth

        totals = {
            metric: sum(values.get(metric, 0) for values in actual.values())
            for metric in ("tests", "assertions")
        }
        total_growth = {
            metric: (value, budget["total_max"].get(metric, 0))
            for metric, value in totals.items()
            if value > budget["total_max"].get(metric, 0)
        }
        stale_limits = {}
        for path, maximum in budget["max_by_file"].items():
            values = actual.get(path, {"tests": 0, "assertions": 0})
            reduction = {
                metric: (values.get(metric, 0), limit)
                for metric, limit in maximum.items()
                if values.get(metric, 0) < limit
            }
            if reduction:
                stale_limits[path] = reduction
        stale_totals = {
            metric: (totals.get(metric, 0), limit)
            for metric, limit in budget["total_max"].items()
            if totals.get(metric, 0) < limit
        }
        self.assertEqual(
            {},
            regressions,
            "Source-coupled test debt grew by file (actual, maximum): "
            + repr(regressions),
        )
        self.assertEqual(
            {},
            total_growth,
            "Total source-coupled test debt grew (actual, maximum): "
            + repr(total_growth),
        )
        self.assertEqual(
            ({}, {}),
            (stale_limits, stale_totals),
            "Source-coupled test debt decreased; lower the stored baseline "
            "in the same change (actual, maximum): "
            + repr((stale_limits, stale_totals)),
        )


if __name__ == "__main__":
    unittest.main()
