from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (
    ROOT / "thlib" / "ui",
    ROOT / "handler_server",
    ROOT / "tactic_handler_dcc",
)
SOURCE_FILES = (ROOT / "thlib/ui/application.py", ROOT / "launch.py")


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

    def test_application_source_has_no_debug_placeholders_or_workspace_paths(self):
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
                if path == ROOT / "tactic_handler_dcc" / "maya.py" and (
                    'print(f"TACTIC Handler [' in line
                ):
                    # Maya Script Editor fallback when in-view UI is unavailable.
                    continue
                if markers.search(line) or workspace_path.search(line):
                    invalid.append(f"{path.relative_to(ROOT)}:{number}")
                if line.startswith(("<<<<<<<", "=======", ">>>>>>>")):
                    invalid.append(f"{path.relative_to(ROOT)}:{number}")
        self.assertEqual(invalid, [])

    def test_application_source_does_not_embed_credential_literals(self):
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

    def test_removed_internal_compatibility_paths_do_not_return(self):
        forbidden = {
            "floatingWindowsV1",
            "dockLayoutV2",
            "processFilterCompactGeometryVersion",
            "treeCacheV1",
            "sessionStateV1",
            "snapshotContentV2",
            "get_sobjects_new",
            "_query_user_recent_activity_legacy",
            "reset_poll_timer",
            "TEMPORARY_TOOL_WINDOWS",
            "TEMPORARY_TOOL_DOCKS",
            "show_temporary_tools",
            "temporary_tools_requested",
            "CACHE_SCHEMA_VERSION",
            "CALENDAR_CACHE_VERSION",
            "entryVersion",
            "entry_version",
        }
        invalid = []
        roots = (ROOT / "thlib", ROOT / "docs")
        for root in roots:
            patterns = ("*.py", "*.qml", "*.md")
            for pattern in patterns:
                for path in root.rglob(pattern):
                    if "side" in path.relative_to(ROOT).parts:
                        continue
                    text = path.read_text(encoding="utf-8-sig")
                    for marker in forbidden.intersection(text.split()):
                        invalid.append(
                            f"{path.relative_to(ROOT).as_posix()}: {marker}"
                        )
                    for marker in forbidden:
                        if marker in text and marker not in text.split():
                            invalid.append(
                                f"{path.relative_to(ROOT).as_posix()}: {marker}"
                            )
        self.assertEqual(sorted(set(invalid)), [])

    def test_developer_markdown_is_english(self):
        cyrillic = re.compile(r"[А-Яа-яЁё]")
        invalid = []
        for path in ROOT.rglob("*.md"):
            for number, line in enumerate(
                path.read_text(encoding="utf-8-sig").splitlines(), 1
            ):
                if cyrillic.search(line):
                    invalid.append(f"{path.relative_to(ROOT)}:{number}")
        self.assertEqual(invalid, [])
    def test_source_has_no_unexpected_control_characters(self):
        allowed = {"\n", "\r", "\t"}
        invalid = []
        roots = (*SOURCE_ROOTS, ROOT / "tests")
        for root in roots:
            for pattern in ("*.py", "*.qml", "*.md", "*.json"):
                for path in root.rglob(pattern):
                    text = path.read_text(
                        encoding="utf-8-sig", errors="replace"
                    )
                    for offset, character in enumerate(text):
                        if ord(character) >= 32 or character in allowed:
                            continue
                        line = text.count("\n", 0, offset) + 1
                        invalid.append(
                            f"{path.relative_to(ROOT)}:{line} "
                            f"U+{ord(character):04X}"
                        )
        self.assertEqual(invalid, [])


if __name__ == "__main__":
    unittest.main()
