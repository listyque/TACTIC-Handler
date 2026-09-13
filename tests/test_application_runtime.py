from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from thlib.ui.application_runtime import LifecycleRegistry, QmlBindingRegistry


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_DEBT = ROOT / "tests/contracts/ui_architecture_debt.json"


class _Context:
    def __init__(self):
        self.values = []

    def setContextProperty(self, name, value):
        self.values.append((name, value))


class _Service:
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def shutdown(self):
        self.calls.append(self.name)


class ApplicationRuntimeTests(unittest.TestCase):
    def test_qml_bindings_publish_once_in_declaration_order(self):
        registry = QmlBindingRegistry()
        first = object()
        second = object()
        registry.add_group("core", {"first": first})
        registry.add_group("feature", {"second": second})
        context = _Context()

        registry.publish(context)

        self.assertEqual(registry.names, ("first", "second"))
        self.assertEqual(context.values, [("first", first), ("second", second)])

    def test_qml_bindings_reject_duplicate_and_empty_names(self):
        registry = QmlBindingRegistry()
        registry.add_group("core", {"shared": object()})
        with self.assertRaises(ValueError):
            registry.add_group("feature", {"shared": object()})
        with self.assertRaises(ValueError):
            registry.add_group("feature", {"": object()})

    def test_lifecycle_is_ordered_and_idempotent(self):
        calls = []
        lifecycle = LifecycleRegistry()
        lifecycle.add_services((_Service("first", calls), _Service("second", calls)))

        lifecycle.shutdown()
        lifecycle.shutdown()

        self.assertEqual(calls, ["first", "second"])

    def test_entrypoint_delegates_composition_and_qml_contract(self):
        application = (ROOT / "thlib/ui/application.py").read_text(encoding="utf-8")
        composition = (ROOT / "thlib/ui/application_composition.py").read_text(
            encoding="utf-8"
        )
        binding_names = []
        for tree in (ast.parse(composition), ast.parse(application)):
            for node in ast.walk(tree):
                owns_bindings = (
                    isinstance(node, ast.FunctionDef) and node.name == "qml_bindings"
                ) or (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add_group"
                )
                if not owns_bindings:
                    continue
                for child in ast.walk(node):
                    if isinstance(child, ast.Dict):
                        binding_names.extend(
                            key.value
                            for key in child.keys
                            if (
                                isinstance(key, ast.Constant)
                                and isinstance(key.value, str)
                            )
                        )

        self.assertIn("build_application_runtime", application)
        self.assertIn("runtime.publish_qml_bindings", application)
        self.assertIn("runtime.shutdown", application)
        self.assertNotIn("setContextProperty", application)
        context_property_budget = json.loads(
            ARCHITECTURE_DEBT.read_text(encoding="utf-8")
        )["context_property_max"]
        self.assertLessEqual(len(binding_names), context_property_budget)
        for name in (
            "sobjectDuplicateController", "sobjectDuplicateFieldModel",
            "sobjectDuplicateRelationModel", "sobjectDuplicateProcessModel",
            "workspaceLayoutPresets", "workspaceLayoutPresetModel",
            "knowledgeController", "knowledgeNavigationModel",
            "knowledgeAttachments", "knowledgeAttachmentDraftModel",
            "knowledgeRichText", "skeyPreviewResolver",
            "helpController",
        ):
            self.assertIn(name, binding_names)
        self.assertEqual(len(binding_names), len(set(binding_names)))

    def test_entrypoint_captures_viewport_before_destroying_qml(self):
        source = (ROOT / "thlib/ui/application.py").read_text(encoding="utf-8")
        destroy = next(
            node for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.FunctionDef) and node.name == "destroy_qml"
        )
        calls = [
            node for node in ast.walk(destroy)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        ]
        capture = next(
            node for node in calls if node.func.attr == "_capture_current_tree_state"
        )
        native_destroy = next(
            node for node in ast.walk(destroy)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_destroy_transient_windows"
        )
        deletion = next(node for node in calls if node.func.attr == "deleteLater")
        self.assertLess(capture.lineno, native_destroy.lineno)
        self.assertLess(native_destroy.lineno, deletion.lineno)


if __name__ == "__main__":
    unittest.main()
