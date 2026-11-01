"""Configuration uses real native controls and asynchronous filesystem workers."""

import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from PySide6.QtCore import QPointF, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from thlib.environment import env_inst
from thlib.ui.maya_integrations import MayaIntegrationsController
from tactic_handler_dcc import maya_integration
from tactic_handler_dcc import connectors
from thlib.ui.dcc_plugins import initialize_plugins, read_disabled_plugins
from thlib.ui.workspace_models.state import WorkspaceState
from tests.frame_configuration_fixture import Surface


class MayaIntegrationsUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait(self, controller):
        deadline = time.monotonic() + 15
        while controller.busy and time.monotonic() < deadline:
            self.app.processEvents()
            QTest.qWait(5)
        self.assertFalse(controller.busy)
        self.assertEqual(controller.error, "")

    def test_worker_installs_removes_and_does_not_apply_stale_results_after_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "launch.pyw").touch()
            icon = root / "thlib/ui/gliph/maya_shelf/tactic_logo.png"
            icon.parent.mkdir(parents=True)
            icon.write_bytes((Path(maya_integration.__file__).parents[1] /
                             "thlib/ui/gliph/maya_shelf/tactic_logo.png").read_bytes())
            profile = root / "maya/2023"
            profile.mkdir(parents=True)
            original = maya_integration.discover
            with patch.object(maya_integration, "discover", side_effect=lambda: original(
                    app_directory=profile.parent, executables=[], processes=[])):
                controller = MayaIntegrationsController(handler_root=root)
                try:
                    controller.reload()
                    self.wait(controller)
                    self.assertEqual(controller.selected["version"], "2023")
                    controller.install()
                    self.wait(controller)
                    self.assertEqual(controller.selected["status"], "Installed")
                    controller.remove()
                    self.wait(controller)
                    self.assertEqual(controller.selected["status"], "Not installed")
                    rows = controller.rows
                    controller.shutdown()
                    controller._finished(("scan", []))
                    self.assertEqual(controller.rows, rows)
                finally:
                    controller.shutdown()
                    self.assertTrue(env_inst.local_pool.exit(5000))
                    env_inst.local_pool.reopen()

    def test_maya_page_renders_rows_actions_and_long_russian_layout(self):
        for width in (360, 980):
            surface = Surface("dcc", width, 740, language="ru")
            try:
                controller = surface.case.config.page_integration("dcc.maya")
                controller._finished(("scan", [{
                    "id": "maya-2023", "profile": "C:/Users/Test/Documents/maya/2023",
                    "version": "2023", "pids": [], "supported": True,
                    "status": "Installed", "managed": True,
                    "handlerRoot": "D:/TH folder with spaces/TACTIC-Handler",
                }]))
                surface.settle()
                self.assertEqual(surface.warnings, [])
                for name in ("mayaIntegrationFind", "mayaIntegrationInstall", "mayaIntegrationRemove"):
                    item = surface.item(name)
                    self.assertTrue(item.isEnabled())
                    self.assertGreaterEqual(item.width(), item.implicitWidth())
                    point = item.mapToScene(QPointF(0, 0))
                    self.assertGreaterEqual(point.x(), 0)
                    self.assertLessEqual(point.x() + item.width(), width)
                with patch.object(controller, "install") as install:
                    item = surface.item("mayaIntegrationInstall")
                    QTest.mouseClick(surface.window, Qt.LeftButton, pos=item.mapToScene(
                        QPointF(item.width() / 2, item.height() / 2)).toPoint())
                    surface.settle()
                    install.assert_called_once()
                controller._busy = True
                controller.stateChanged.emit()
                surface.settle()
                self.assertFalse(surface.item("mayaIntegrationInstall").isEnabled())
                self.assertFalse(surface.item("mayaIntegrationRemove").isEnabled())
                self.assertEqual(surface.warnings, [])
            finally:
                surface.close()

    def test_plugin_page_toggle_persists_and_next_start_removes_plugin_surfaces(self):
        surface = Surface("configuration", 980, 740, language="ru")
        try:
            config = surface.case.config
            config.select_page("dcc.maya")
            surface.settle()
            self.assertTrue(surface.item("mayaIntegrationFind").isVisible())
            config.select_page("dcc_plugins")
            surface.settle()
            self.assertTrue(surface.item("dccPluginToggle_maya").isVisible())
            config.select_page("dcc.maya")
            surface.settle()
            self.assertTrue(surface.item("mayaIntegrationFind").isVisible())
            config.select_page("dcc_plugins")
            surface.settle()
            toggle = surface.item("dccPluginToggle_maya")
            self.assertTrue(toggle.property("checked"))
            toggle.forceActiveFocus()
            QTest.keyClick(surface.window, Qt.Key_Space)
            surface.settle()
            self.assertIn("maya", read_disabled_plugins())
            self.assertTrue(config.page_integration("dcc_plugins").restartRequired)
            self.assertTrue(any(page["id"] == "dcc.maya" for page in connectors.dcc_configuration_pages()))
            initialize_plugins()
            self.assertFalse(any(page["id"] == "dcc.maya" for page in connectors.dcc_configuration_pages()))
            state = WorkspaceState()
            self.assertFalse(any(row["target"] == "dcc.maya" for row in state.configuration_page_model._records))
            self.assertTrue(any(row["target"] == "dcc_plugins" for row in state.configuration_page_model._records))
            self.assertEqual(connectors.dcc_item_actions("maya"), ())
            self.assertEqual(connectors.dcc_trigger_actions(), ())
            self.assertEqual(surface.warnings, [])
        finally:
            connectors.configure_plugins()
            surface.close()


if __name__ == "__main__":
    unittest.main()
