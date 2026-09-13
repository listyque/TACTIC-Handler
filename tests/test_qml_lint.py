from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
QML_ROOT = ROOT / "thlib/ui/qml"
ARCHITECTURE_DEBT = ROOT / "tests/contracts/ui_architecture_debt.json"


def _qmllint_path() -> str:
    executable = shutil.which("pyside6-qmllint")
    if executable:
        return executable
    candidate = Path(sys.executable).with_name(
        "pyside6-qmllint.exe" if sys.platform == "win32" else "pyside6-qmllint"
    )
    if candidate.is_file():
        return str(candidate)
    raise AssertionError("pyside6-qmllint is missing from the pinned PySide6 toolchain")


class QmlLintTests(unittest.TestCase):
    def test_qml_warning_debt_only_decreases(self):
        budget = json.loads(ARCHITECTURE_DEBT.read_text(encoding="utf-8"))[
            "qmllint_max_warnings"
        ]
        qml_files = sorted(str(path) for path in QML_ROOT.rglob("*.qml"))
        result = subprocess.run(
            [
                _qmllint_path(), "--json", "-", "-I", str(QML_ROOT),
                *qml_files,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            "qmllint could not analyze the QML tree:\n" + result.stderr,
        )
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            self.fail(f"qmllint returned invalid JSON: {error}\n{result.stdout}")
        counts = Counter(
            warning.get("id", "")
            for file_result in report.get("files", [])
            for warning in file_result.get("warnings", [])
        )
        regressions = {
            category: (counts[category], maximum)
            for category, maximum in budget.items()
            if counts[category] > maximum
        }
        self.assertEqual(
            {},
            regressions,
            "QML warning debt grew (actual, maximum): " + repr(regressions),
        )


if __name__ == "__main__":
    unittest.main()
