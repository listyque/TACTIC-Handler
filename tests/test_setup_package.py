"""Installer presets stay public, reproducible, bounded and independent of a compiler."""

import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from thlib.ui.setup_package import (
    MAGIC,
    MAX_CONFIG,
    initialize_installer,
    build_installer,
    read_installer,
    read_setup_defaults,
    validate_defaults,
    default_repository,
)
from thlib.ui.setup_builder import SetupBuilderController

from PySide6.QtCore import QObject, QUrl, QPointF, Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from thlib.environment import env_inst


class SetupPackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.base = self.root / "base.exe"
        self.original = b"MZ" + b"test executable payload" * 80
        self.base.write_bytes(self.original)
        initialize_installer(self.base, "0.6.0.375")

    def tearDown(self):
        self.temp.cleanup()

    def test_regenerate_installer_retains_payload_without_accumulating_old_defaults(
        self,
    ):
        first, second = self.root / "team.exe", self.root / "updated.exe"
        config = {
            "server": "studio.invalid/tactic",
            "project": "demo",
            "repository_name": "Репозиторий",
            "plugins": ["maya"],
            "shelf": "Assets Shelf",
            "shortcuts": False,
        }
        build_installer(self.base, first, config)
        first_metadata, first_end = read_installer(first)
        self.assertEqual(first.read_bytes()[:first_end], self.original)
        self.assertEqual(first_metadata["defaults"]["server"], "http://studio.invalid")
        self.assertEqual(first_metadata["defaults"]["repository_name"], "Репозиторий")
        build_installer(first, second, {**config, "server": "https://new.invalid"})
        metadata, end = read_installer(second)
        self.assertEqual(second.read_bytes()[:end], self.original)
        self.assertEqual(end, first_end)
        self.assertEqual(metadata["defaults"]["server"], "https://new.invalid")
        self.assertNotIn(b"http://studio.invalid", second.read_bytes())
        self.assertTrue(second.with_name(second.name + ".sha256").is_file())

    def test_rejects_credentials_unsafe_repository_names_and_bad_server_urls(self):
        for value in (
            {"password": "do-not-package"},
            {"ticket": "do-not-package"},
            {"login": "admin"},
            {"server": "https://admin:secret@studio.invalid"},
            {"server": "http://studio.invalid/path"},
            *(
                {"repository_name": name}
                for name in (
                    "..",
                    "../repo",
                    "runtime",
                    "TACTIC-Handler",
                    "C:repo",
                    "NUL",
                    "repo.",
                )
            ),
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_defaults(value)

    def test_bad_input_never_overwrites_existing_output_or_template(self):
        target = self.root / "existing.exe"
        target.write_bytes(b"keep old installer")
        with self.assertRaises(ValueError):
            build_installer(self.base, target, {"password": "do-not-package"})
        self.assertEqual(target.read_bytes(), b"keep old installer")
        before = self.base.read_bytes()
        with self.assertRaises(ValueError):
            build_installer(self.base, self.base, {})
        self.assertEqual(self.base.read_bytes(), before)
        self.assertEqual(list(self.root.glob(".th-setup-*")), [])

    def test_template_checksum_and_footer_bounds_are_verified(self):
        self.base.with_name(self.base.name + ".sha256").write_text(
            "0" * 64 + "  base.exe\n"
        )
        with self.assertRaisesRegex(ValueError, "checksum"):
            build_installer(self.base, self.root / "bad.exe", {})
        self.base.write_bytes(self.original + struct.pack("<Q", MAX_CONFIG + 1) + MAGIC)
        with self.assertRaises(ValueError):
            read_installer(self.base)

    def test_deployment_defaults_resolve_only_the_installed_repository_subfolder(self):
        app = self.root / "TH/TACTIC-Handler"
        app.mkdir(parents=True)
        self.assertEqual(read_setup_defaults(app)["server"], "")
        (app.parent / "setup-defaults.json").write_text(
            json.dumps(
                {
                    "format": 1,
                    "version": "0.6.0.375",
                    "defaults": {
                        "server": "studio.invalid",
                        "repository_name": "studio_repo",
                    },
                }
            )
        )
        self.assertEqual(default_repository(app), app.parent / "studio_repo")
        self.assertEqual(read_setup_defaults(app)["server"], "http://studio.invalid")

    def test_wizard_controller_applies_public_presets_and_keeps_login_empty(self):
        from thlib.environment import env_mode
        from thlib.ui.setup_wizard import SetupController

        app = self.root / "TH/TACTIC-Handler"
        app.mkdir(parents=True)
        old = env_mode.get_current_path()
        env_mode.set_current_path(str(self.root / "clean-profile"))
        try:
            (app.parent / "setup-defaults.json").write_text(
                json.dumps(
                    {
                        "format": 1,
                        "version": "0.6.0.375",
                        "defaults": {
                            "server": "https://studio.invalid",
                            "project": "demo",
                            "repository_name": "studio_repo",
                            "plugins": ["maya"],
                            "shelf": "Assets Shelf",
                            "shortcuts": False,
                            "language": "en",
                            "dark_theme": False,
                            "close_to_tray": False,
                        },
                    }
                )
            )
            controller = SetupController(app)
            try:
                self.assertEqual(controller.state["server"], "https://studio.invalid")
                self.assertEqual(controller.state["login"], "")
                self.assertEqual(controller.state["project"], "demo")
                self.assertEqual(
                    controller.state["repository"], str(app.parent / "studio_repo")
                )
                self.assertFalse(controller.state["shortcuts"])
                self.assertEqual(controller.state["language"], "en")
                self.assertFalse(controller.state["darkTheme"])
                self.assertFalse(controller.state["closeToTray"])
                controller._finished(
                    (
                        "project",
                        {
                            "shelves": [
                                {"id": "other", "title": "Other"},
                                {"id": "assets", "title": "Assets Shelf"},
                            ],
                            "maya": [],
                            "pluginCatalog": [{"id": "maya"}, {"id": "nuke"}],
                            "disabled": [],
                        },
                    )
                )
                self.assertEqual(controller.state["shelf"], "assets")
                self.assertEqual(controller.state["plugins"], ["maya"])
            finally:
                controller.shutdown()
        finally:
            env_mode.set_current_path(old)

    def test_selecting_a_new_base_preserves_parameters_the_user_has_edited(self):
        app = self.root / "TH/TACTIC-Handler"
        app.mkdir(parents=True)
        controller = SetupBuilderController(app)
        metadata = read_installer(self.base)[0]
        controller._finished(("template", metadata))
        controller.edit("server", "https://team.invalid")
        controller._finished(("template", {**metadata, "version": "0.6.0.376"}))
        self.assertEqual(controller.state["defaults"]["server"], "https://team.invalid")
        self.assertEqual(controller.state["version"], "0.6.0.376")
        controller.shutdown()

    def test_real_builder_controls_generate_an_installer_with_the_entered_defaults(
        self,
    ):
        if QApplication.instance() is None:
            QQuickStyle.setStyle("Material")
        app = QApplication.instance() or QApplication([])
        env_inst.start_pools()
        handler = self.root / "application/TACTIC-Handler"
        handler.mkdir(parents=True)
        controller = SetupBuilderController(handler)
        controller._state.update(
            template=str(self.base), output=str(self.root / "output/team.exe")
        )
        controller._finished(("template", read_installer(self.base)[0]))
        source = Path(__file__).resolve().parents[1]
        engine = QQmlApplicationEngine()
        from thlib.ui.icon_font import qml_icon_bindings

        for name, value in qml_icon_bindings(source, controller).items():
            engine.rootContext().setContextProperty(name, value)
        warnings = []
        engine.warnings.connect(
            lambda values: warnings.extend(value.toString() for value in values)
        )
        engine.setInitialProperties({"controller": controller})
        engine.load(
            QUrl.fromLocalFile(
                str(source / "thlib/ui/qml/features/setup/SetupBuilder.qml")
            )
        )
        self.assertTrue(engine.rootObjects(), warnings)
        window = engine.rootObjects()[0]
        try:
            field = window.findChild(QObject, "builderServer")
            field.forceActiveFocus()
            app.sendEvent(
                window,
                QKeyEvent(QEvent.KeyPress, 0, Qt.NoModifier, "https://team.invalid"),
            )
            self.assertEqual(
                controller.state["defaults"]["server"], "https://team.invalid"
            )
            checkbox = window.findChild(QObject, "builderShortcuts")
            checkbox.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Space)
            self.assertFalse(controller.state["defaults"]["shortcuts"])
            QTest.qWait(30)
            build = window.findChild(QObject, "builderBuild")
            QTest.mouseClick(
                window,
                Qt.LeftButton,
                pos=build.mapToScene(
                    QPointF(build.width() / 2, build.height() / 2)
                ).toPoint(),
            )
            deadline = time.monotonic() + 5
            while controller.state["busy"] and time.monotonic() < deadline:
                app.processEvents()
                QTest.qWait(5)
            self.assertEqual(controller.state["error"], "")
            generated = Path(controller.state["result"])
            self.assertTrue(generated.is_file())
            defaults = read_installer(generated)[0]["defaults"]
            self.assertEqual(defaults["server"], "https://team.invalid")
            self.assertFalse(defaults["shortcuts"])
            for width in (500, 900):
                window.setWidth(width)
                QTest.qWait(20)
                edge = build.mapToScene(QPointF(build.width(), 0)).x()
                self.assertLessEqual(edge, width)
            self.assertEqual(warnings, [])
        finally:
            controller.shutdown()
            window.close()
            engine.deleteLater()
            app.processEvents()
            env_inst.exit_pools()
            env_inst.local_pool.reopen()


if __name__ == "__main__":
    unittest.main()
