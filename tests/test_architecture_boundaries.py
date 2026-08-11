from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _python_files(folder: str, *, exclude_side: bool = False):
    for path in (ROOT / folder).rglob("*.py"):
        relative = path.relative_to(ROOT)
        if exclude_side and "side" in relative.parts:
            continue
        yield path


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_modules(path: Path) -> set[str]:
    current = _module_name(path).split(".")
    package = current[:-1]
    result: set[str] = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            keep = max(0, len(package) - node.level + 1)
            base = package[:keep]
            if node.module:
                base.extend(node.module.split("."))
            module = ".".join(base)
            if module:
                result.add(module)
            if not node.module:
                result.update(
                    ".".join((*base, alias.name)) for alias in node.names
                )
        elif node.module:
            result.add(node.module)
    return result


def _matches(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(module == prefix or module.startswith(prefix + ".") for prefix in prefixes)


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_thlib_does_not_depend_on_modern_ui(self):
        violations = []
        for path in _python_files("thlib", exclude_side=True):
            source = path.read_text(encoding="utf-8", errors="replace")
            if re.search(
                r"^\s*(?:from\s+modern_ui(?:\.|\s)|import\s+modern_ui(?:\.|\s|$))",
                source,
                flags=re.MULTILINE,
            ):
                violations.append(str(path.relative_to(ROOT)))
        self.assertEqual([], violations, "\n".join(violations))

    def test_modern_python_does_not_open_legacy_qwidget_ui(self):
        forbidden = ("thlib.ui", "thlib.ui_classes", "thlib.ui_misc")
        violations = []
        for path in _python_files("modern_ui"):
            for module in _imported_modules(path):
                if _matches(module, forbidden):
                    violations.append(f"{path.relative_to(ROOT)} -> {module}")
        self.assertEqual([], violations, "\n".join(violations))

    def test_qtwidgets_is_confined_to_platform_adapter(self):
        allowed = {Path("modern_ui/tray.py")}
        violations = []
        for path in _python_files("modern_ui"):
            relative = path.relative_to(ROOT)
            imports = _imported_modules(path)
            if "PySide6.QtWidgets" in imports and relative not in allowed:
                violations.append(str(relative))
        self.assertEqual([], violations, "\n".join(violations))

    def test_qml_has_no_transport_or_server_business_logic(self):
        forbidden = (
            "XMLHttpRequest",
            "WebSocket",
            "LocalStorage",
            "WorkerScript",
            "execute_python_script",
            "tactic_classes",
            "tactic_query",
            "thlib.",
        )
        violations = []
        for path in (ROOT / "modern_ui/qml").rglob("*.qml"):
            text = path.read_text(encoding="utf-8")
            found = sorted(token for token in forbidden if token in text)
            if found:
                violations.append(
                    f"{path.relative_to(ROOT)} -> {', '.join(found)}"
                )
        self.assertEqual([], violations, "\n".join(violations))

    def test_thin_dcc_sdk_does_not_depend_on_full_handler(self):
        forbidden = (
            "thlib",
            "modern_ui",
            "handler_server",
            "main_qml",
            "main_standalone",
        )
        violations = []
        for path in _python_files("tactic_handler_dcc"):
            for module in _imported_modules(path):
                if _matches(module, forbidden):
                    violations.append(f"{path.relative_to(ROOT)} -> {module}")
        self.assertEqual([], violations, "\n".join(violations))

    def test_domain_controllers_have_no_import_cycles(self):
        domain: dict[str, Path] = {}
        suffixes = ("Controller", "Service", "Resolver")
        for path in _python_files("modern_ui"):
            tree = _tree(path)
            is_application_mixin = (
                path.parent == ROOT / "modern_ui/controllers"
                and path.name != "__init__.py"
            )
            is_domain_api = any(
                isinstance(node, ast.ClassDef) and node.name.endswith(suffixes)
                for node in tree.body
            )
            if is_application_mixin or is_domain_api:
                domain[_module_name(path)] = path

        graph = {
            module: {
                imported
                for imported in _imported_modules(path)
                if imported in domain
            }
            for module, path in domain.items()
        }
        active: list[str] = []
        active_set: set[str] = set()
        complete: set[str] = set()
        cycles: set[tuple[str, ...]] = set()

        def visit(module: str) -> None:
            if module in complete:
                return
            if module in active_set:
                start = active.index(module)
                cycles.add(tuple((*active[start:], module)))
                return
            active.append(module)
            active_set.add(module)
            for dependency in sorted(graph[module]):
                visit(dependency)
            active.pop()
            active_set.remove(module)
            complete.add(module)

        for module in sorted(graph):
            visit(module)
        self.assertEqual(
            set(),
            cycles,
            "\n".join(" -> ".join(cycle) for cycle in sorted(cycles)),
        )


if __name__ == "__main__":
    unittest.main()
