from pathlib import Path
import re
import unittest

from modern_ui.workspace_models.windows import FloatingWindowModel


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "modern_ui" / "qml"


class ModernUiStructureTests(unittest.TestCase):
    def test_window_model_is_the_only_standalone_content_registry(self):
        for window in FloatingWindowModel._defaults():
            source = FloatingWindowModel._content_source(window)
            self.assertTrue(source.endswith(".qml"))
            self.assertTrue(
                (QML / source).is_file(), (window.window_id, source)
            )

        host = (QML / "WindowContent.qml").read_text(encoding="utf-8")
        self.assertNotIn("Component {", host)
        self.assertNotIn("ConfigurationView", host)
        self.assertNotIn("MessagesView", host)

    def test_dock_host_only_owns_layout_and_routes_content(self):
        host = (QML / "DockHost.qml").read_text(encoding="utf-8")
        self.assertLess(len(host.splitlines()), 600)
        self.assertIn("DockContentRegistry", host)
        self.assertNotIn("TaskDockView", host)
        self.assertNotIn("CommunicationView", host)

    def test_project_qml_uses_shared_controls_for_common_primitives(self):
        forbidden = re.compile(
            r"^\s*(?:Button|TextField|TextArea|Dialog|Popup|BusyIndicator)\s*\{",
            re.MULTILINE,
        )
        offenders = []
        for path in QML.glob("*.qml"):
            if forbidden.search(path.read_text(encoding="utf-8")):
                offenders.append(path.name)
        self.assertEqual(offenders, [])

    def test_inline_busy_indicators_receive_the_active_theme(self):
        pattern = re.compile(
            r"Md3BusyIndicator\s*\{([^{}]|\{[^{}]*\})*\}", re.DOTALL
        )
        offenders = []
        for path in QML.glob("*.qml"):
            if path.name == "Md3BusyIndicator.qml":
                continue
            for block in pattern.finditer(path.read_text(encoding="utf-8")):
                if "uiTheme:" not in block.group(0):
                    offenders.append(path.name)
                    break
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
