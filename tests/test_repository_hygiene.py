from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (
    ROOT / "modern_ui",
    ROOT / "handler_server",
    ROOT / "tactic_handler_dcc",
)
SOURCE_FILES = (ROOT / "main_qml.py", ROOT / "launch.py")


def _source_paths():
    for root in SOURCE_ROOTS:
        for pattern in ("*.py", "*.qml"):
            yield from root.rglob(pattern)
    yield from SOURCE_FILES


class RepositoryHygieneTests(unittest.TestCase):
    def test_temporary_and_private_runtime_artifacts_are_not_tracked(self):
        completed = subprocess.run(
            [
                "git", "-c", f"safe.directory={ROOT.as_posix()}",
                "ls-files", "-z",
            ],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        tracked = {
            Path(value.decode("utf-8"))
            for value in completed.stdout.split(b"\0")
            if value
        }
        forbidden_suffixes = {
            ".pyc", ".pyo", ".tmp", ".bak", ".orig", ".rej", ".jsonl",
        }
        forbidden_roots = {"settings", "log", "custom_scripts", "__pycache__"}
        invalid = sorted(
            str(path) for path in tracked
            if path.suffix.lower() in forbidden_suffixes
            or any(part.lower() in forbidden_roots for part in path.parts)
        )
        self.assertEqual(invalid, [])

    def test_modern_source_has_no_debug_placeholders_or_workspace_paths(self):
        invalid = []
        markers = re.compile(r"\b(?:TODO|FIXME|XXX)\b|(?<![A-Za-z])print\s*\(")
        workspace_path = re.compile(r"[A-Za-z]:\\\\")
        for path in _source_paths():
            text = path.read_text(encoding="utf-8-sig")
            for number, line in enumerate(text.splitlines(), 1):
                if path == ROOT / "handler_server" / "launcher.py" and (
                    "HANDLER_SERVER_READY" in line
                ):
                    continue
                if markers.search(line) or workspace_path.search(line):
                    invalid.append(f"{path.relative_to(ROOT)}:{number}")
                if line.startswith(("<<<<<<<", "=======", ">>>>>>>")):
                    invalid.append(f"{path.relative_to(ROOT)}:{number}")
        self.assertEqual(invalid, [])

    def test_modern_source_does_not_embed_credential_literals(self):
        assignment = re.compile(
            r"(?i)\b(password|ticket|secret|api[_-]?key)\s*=\s*"
            r"(?P<quote>['\"])(?P<value>[^'\"]+)(?P=quote)"
        )
        invalid = []
        allowed = {"none", "null", "password", "ticket", "secret", "<redacted>"}
        for path in _source_paths():
            text = path.read_text(encoding="utf-8-sig")
            for match in assignment.finditer(text):
                value = match.group("value").strip().lower()
                if value not in allowed:
                    line = text.count("\n", 0, match.start()) + 1
                    invalid.append(f"{path.relative_to(ROOT)}:{line}")
        self.assertEqual(invalid, [])


if __name__ == "__main__":
    unittest.main()
