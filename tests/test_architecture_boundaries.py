from __future__ import annotations

import ast
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_DEBT = ROOT / "tests/contracts/ui_architecture_debt.json"


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
    def test_application_facade_debt_does_not_grow(self):
        budget = json.loads(ARCHITECTURE_DEBT.read_text(encoding="utf-8"))
        controller_path = ROOT / "thlib/ui/controller.py"
        controller_tree = _tree(controller_path)
        imports = {}
        for node in controller_tree.body:
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            module = (
                "thlib.ui." + node.module
                if node.level
                else node.module
            )
            imports.update((alias.name, module) for alias in node.names)
        controller = next(
            node for node in controller_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "ApplicationController"
        )
        owners = [(controller_path, controller)]
        for base in controller.bases:
            if not isinstance(base, ast.Name) or base.id == "QObject":
                continue
            module = imports[base.id]
            path = ROOT / Path(*module.split(".")).with_suffix(".py")
            tree = _tree(path)
            owners.append((path, next(
                node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == base.id
            )))
        methods = {
            node.name
            for _path, owner in owners
            for node in owner.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertLessEqual(
            len(methods),
            budget["application_controller_max_methods"],
            "ApplicationController/mixin callable surface grew; put the "
            "behavior on a feature-owned controller",
        )

        action_path = ROOT / "thlib/ui/controllers/item_operations.py"
        action = next(
            node for node in ast.walk(_tree(action_path))
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "invoke_item_action"
        )
        action_lines = action.end_lineno - action.lineno + 1
        self.assertLessEqual(
            action_lines,
            budget["invoke_item_action_max_lines"],
            "invoke_item_action grew; move one complete command into its "
            "feature handler instead of adding another branch",
        )

    def test_ui_global_environment_dependency_does_not_grow(self):
        budget = json.loads(ARCHITECTURE_DEBT.read_text(encoding="utf-8"))[
            "env_inst_max_modules"
        ]
        consumers = []
        for path in _python_files("thlib/ui"):
            source = path.read_text(encoding="utf-8", errors="replace")
            if re.search(r"\benv_inst\b", source):
                consumers.append(str(path.relative_to(ROOT)))
        self.assertLessEqual(
            len(consumers),
            budget,
            "env_inst service-locator use grew; inject the narrow dependency "
            "into the feature controller instead:\n" + "\n".join(consumers),
        )

    def test_application_ui_uses_only_pyside6(self):
        paths = [ROOT / "thlib/ui/application.py", *_python_files("thlib/ui")]
        violations = []
        for path in paths:
            for module in _imported_modules(path):
                if (
                    module.startswith(("PySide", "PyQt"))
                    and not _matches(module, ("PySide6",))
                ):
                    violations.append(
                        f"{path.relative_to(ROOT)} -> {module}"
                    )
        self.assertEqual([], violations, "\n".join(violations))

    def test_application_entrypoint_pins_pyside6_for_core(self):
        tree = _tree(ROOT / "thlib/ui/application.py")
        assignments = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
        ]
        pinned = any(
            any(
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Attribute)
                and isinstance(target.value.value, ast.Name)
                and target.value.value.id == "os"
                and target.value.attr == "environ"
                and isinstance(target.slice, ast.Constant)
                and target.slice.value == "QT_PREFERRED_BINDING"
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and node.value.value == "PySide6"
            for node in assignments
        )
        self.assertTrue(pinned)

    def test_source_does_not_import_removed_ui_namespace(self):
        removed_namespace = "modern" + "_ui"
        violations = []
        for folder in ("thlib", "handler_server", "tactic_handler_dcc"):
            for path in _python_files(folder, exclude_side=folder == "thlib"):
                source = path.read_text(encoding="utf-8", errors="replace")
                if re.search(
                    rf"^\s*(?:from\s+{removed_namespace}(?:\.|\s)"
                    rf"|import\s+{removed_namespace}(?:\.|\s|$))",
                    source,
                    flags=re.MULTILINE,
                ):
                    violations.append(str(path.relative_to(ROOT)))
        self.assertEqual([], violations, "\n".join(violations))

    def test_ui_python_does_not_open_removed_qwidget_modules(self):
        forbidden = ("thlib.ui_classes", "thlib.ui_misc")
        violations = []
        for path in _python_files("thlib/ui"):
            for module in _imported_modules(path):
                if _matches(module, forbidden):
                    violations.append(f"{path.relative_to(ROOT)} -> {module}")
        self.assertEqual([], violations, "\n".join(violations))

    def test_qtwidgets_is_confined_to_application_boundaries(self):
        allowed = {Path("thlib/ui/application.py"), Path("thlib/ui/tray.py")}
        violations = []
        for path in _python_files("thlib/ui"):
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
        for path in (ROOT / "thlib/ui/qml").rglob("*.qml"):
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
            "handler_server.server",
            "handler_server.router",
            "handler_server.launcher",
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
        for path in _python_files("thlib/ui"):
            tree = _tree(path)
            is_application_mixin = (
                path.parent == ROOT / "thlib" / "ui" / "controllers"
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
