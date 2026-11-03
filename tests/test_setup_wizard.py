"""Setup uses real config/integration files, authenticated policy, and native input."""

import copy
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from urllib.error import URLError, HTTPError
from xmlrpc.client import Fault
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from PySide6.QtCore import QPointF, QUrl, Qt, QObject, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from thlib.environment import (
    env_mode,
    env_server,
    env_tactic,
    env_inst,
    env_read_config,
)
from thlib.ui.setup_service import (
    SetupSession,
    apply_setup,
    read_initial,
    shelf_buttons,
    SetupTransport,
)
from thlib.ui.setup_wizard import SetupController
from thlib.ui.localization import CatalogTranslator
from tactic_handler_dcc import maya_integration

ROOT = Path(__file__).resolve().parents[1]


class SetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        QQuickStyle.setStyle("Material")
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.old_path = env_mode.get_current_path()
        env_mode.set_current_path(str(self.directory))
        env_server.reload()
        env_tactic.reset()

    def tearDown(self):
        env_mode.set_current_path(self.old_path)
        env_server.reload()
        env_tactic.reset()
        self.temp.cleanup()

    def fixtures(self):
        profile = self.directory / "maya/2023"
        profile.mkdir(parents=True)
        repository = self.directory / "repository"
        repository.mkdir()
        session = SetupSession()
        session.url, session.login, session.project = (
            "http://example.invalid",
            "artist",
            "demo",
        )
        session.server = Mock(login_ticket="TEST-SESSION-TICKET")
        session.load_project = Mock(
            return_value=[
                {
                    "id": "global",
                    "buttons": [
                        {"title": "Save", "script": "tools/save", "icon": "save"}
                    ],
                }
            ]
        )
        values = dict(
            project="demo",
            repository=str(repository),
            shelf="global",
            plugins=["maya"],
            mayaProfiles=[str(profile.resolve())],
            shortcuts=False,
            language="en",
            darkTheme=False,
            closeToTray=False,
        )
        original_discover = maya_integration.discover
        discovery = lambda: original_discover(
            app_directory=profile.parent, executables=[], processes=[]
        )
        return session, values, profile, discovery

    def test_filter_respects_all_denials_and_metadata_without_touching_configuration(
        self,
    ):
        source = {
            "buttons": [
                {"script": path}
                for path in ("tools/ok", "tools/denied", "missing", "tools/js")
            ]
        }
        original = copy.deepcopy(source)
        scripts = [
            {"folder": "tools", "title": title, "language": language}
            for title, language in (
                ("ok", "dcc_python"),
                ("denied", "python"),
                ("js", "javascript"),
            )
        ]
        self.assertEqual(
            shelf_buttons(source, scripts, ["tools/denied"]), [{"script": "tools/ok"}]
        )
        self.assertEqual(shelf_buttons(source, scripts, ["*"]), [])
        self.assertEqual(source, original)

    def test_install_rerun_and_remove_with_native_config_and_managed_shelf(self):
        from thlib.ui.setup_service import create_shortcuts

        session, values, profile, discover = self.fixtures()
        desktop = self.directory / "desktop"
        bundle = self.directory / "bundle"
        bundle.mkdir(parents=True)
        (bundle / "TACTIC Handler.exe").write_bytes(b"MZ")
        create_shortcuts(desktop, bundle)
        self.assertTrue((desktop / "TACTIC Handler.lnk").exists())
        self.assertFalse((desktop / "TACTIC Handler Setup.lnk").exists())
        with patch.object(maya_integration, "discover", side_effect=discover):
            apply_setup(session, ROOT, values, desktop)
            apply_setup(session, ROOT, values, desktop)
        self.assertEqual(read_initial()["repository"], values["repository"])
        self.assertEqual(env_server.get_user(), "artist")
        self.assertEqual(
            env_tactic.base_dirs["asset_base_dir"][0], values["repository"]
        )
        self.assertEqual(read_initial()["repositoryAlias"], "base")
        self.assertEqual(read_initial()["language"], "en")
        self.assertFalse(read_initial()["darkTheme"])
        self.assertFalse(read_initial()["closeToTray"])
        self.assertEqual(
            SetupController(ROOT).state["repository"], values["repository"]
        )
        ui_cfg = env_read_config(
            filename="ui_settings", unique_id="ui_main", long_abs_path=True
        )
        self.assertEqual(ui_cfg["server/currentProject"], "demo")
        self.assertEqual(ui_cfg["appearance/language"], "en")
        self.assertFalse(ui_cfg["appearance/darkTheme"])
        self.assertFalse(ui_cfg["application/closeToTray"])
        mel = profile / "prefs/shelves/shelf_TACTIC_Stream.mel"
        self.assertIn("tools/save", mel.read_text())
        # Native Maya changes whitespace/visuals when saving preferences.
        mel.write_text(mel.read_text().replace("-width 35", "-width 36"))
        self.assertEqual(
            maya_integration.integration_state(profile)["status"], "Installed"
        )
        maya_integration.remove(profile)
        self.assertFalse(mel.exists())

    def test_default_repository_tracks_installation_and_next_does_not_create_it(self):
        root = self.directory / "Chosen TH folder" / "TACTIC-Handler"
        controller = SetupController(root)
        expected = root.parent / "repo"
        self.assertEqual(controller.state["repository"], str(expected))
        controller._state.update(step=1, project="demo", projects=[{"code": "demo"}])
        with patch.object(controller, "_run") as run:
            controller.next()
            self.assertEqual(run.call_args.args[0], "project")
        self.assertFalse(expected.exists())
        controller.shutdown()

    def test_default_repository_created_on_apply_and_empty_folder_rolled_back(self):
        session, values, profile, discover = self.fixtures()
        root = self.directory / "Chosen TH folder" / "TACTIC-Handler"
        root.mkdir(parents=True)
        expected = root.parent / "repo"
        values.update(repository=str(expected), mayaProfiles=[], shortcuts=True)
        with (
            patch.object(maya_integration, "discover", side_effect=discover),
            patch(
                "thlib.ui.setup_service.create_shortcuts",
                side_effect=OSError("desktop denied"),
            ),
        ):
            with self.assertRaisesRegex(OSError, "desktop denied"):
                apply_setup(session, root, values, self.directory / "desktop")
        self.assertFalse(expected.exists())
        values["shortcuts"] = False
        with patch.object(maya_integration, "discover", side_effect=discover):
            apply_setup(session, root, values, self.directory / "desktop")
            self.assertTrue(expected.is_dir())
            marker = expected / "keep.txt"
            marker.write_text("repository data")
            apply_setup(session, root, values, self.directory / "desktop")
        self.assertEqual(marker.read_text(), "repository data")

    def test_rollback_restores_settings_and_integration_when_shortcut_creation_fails(
        self,
    ):
        session, values, profile, discover = self.fixtures()
        settings = self.directory / "settings"
        before = {
            p.relative_to(settings): p.read_bytes()
            for p in settings.rglob("*")
            if p.is_file()
        }
        values["shortcuts"] = True
        with (
            patch.object(maya_integration, "discover", side_effect=discover),
            patch(
                "thlib.ui.setup_service.create_shortcuts",
                side_effect=OSError("desktop denied"),
            ),
        ):
            with self.assertRaisesRegex(OSError, "desktop denied"):
                apply_setup(session, ROOT, values, self.directory / "desktop")
        after = {
            p.relative_to(settings): p.read_bytes()
            for p in settings.rglob("*")
            if p.is_file()
        }
        self.assertEqual(after, before)
        self.assertEqual(
            maya_integration.integration_state(profile)["status"], "Not installed"
        )

    def test_apply_refreshes_policy_and_does_not_install_buttons_from_the_old_preview(
        self,
    ):
        session, values, profile, discover = self.fixtures()
        session.load_project.return_value = [{"id": "global", "buttons": []}]
        with patch.object(maya_integration, "discover", side_effect=discover):
            apply_setup(session, ROOT, values, self.directory / "desktop")
        session.load_project.assert_called_once_with("demo")
        self.assertNotIn(
            "tools/save",
            (profile / "prefs/shelves/shelf_TACTIC_Stream.mel").read_text(),
        )

    def test_failed_sign_in_discards_previous_authenticated_session_and_redacts_fault(
        self,
    ):
        session = SetupSession()
        session.server = Mock()
        with patch(
            "thlib.side.client.tactic_client_lib.tactic_server_stub.TacticServerStub"
        ) as stub:
            stub.return_value.get_ticket.side_effect = RuntimeError(
                "secret-password echoed by server"
            )
            with self.assertRaisesRegex(RuntimeError, "Sign-in failed") as error:
                session.authenticate(
                    "http://example.invalid", "artist", "secret-password"
                )
            self.assertNotIn("secret-password", str(error.exception))
        self.assertIsNone(session.server)

    def test_connection_fields_start_empty_even_with_a_configured_account(self):
        env_server.set_server("http://example.invalid")
        env_server.set_user("admin")
        env_server.save_defaults()
        controller = SetupController(ROOT)
        self.assertEqual(controller.state["server"], "")
        self.assertEqual(controller.state["login"], "")
        controller.shutdown()

    def test_back_forward_preserves_choices_but_new_account_resets_them(self):
        controller = SetupController(ROOT)
        controller.session.url, controller.session.login = (
            "http://example.invalid",
            "artist",
        )
        controller._state.update(project="demo", projects=[{"code": "demo"}])
        catalog = {
            "shelves": [{"id": "one", "title": "One"}, {"id": "two", "title": "Two"}],
            "maya": [{"id": "maya2023", "supported": True, "pids": []}],
            "pluginCatalog": [{"id": "maya"}, {"id": "nuke"}],
            "disabled": ["nuke"],
        }
        controller._finished(("project", copy.deepcopy(catalog)))
        controller.edit("shelf", "two")
        controller.toggle("plugins", "nuke", True)
        controller.toggle("mayaProfiles", "maya2023", True)
        controller.toggle("shortcuts", "", False)
        controller.back()
        controller.back()
        controller._finished(("login", [{"code": "demo"}]))
        controller._finished(("project", copy.deepcopy(catalog)))
        self.assertEqual(controller.state["shelf"], "two")
        self.assertEqual(controller.state["plugins"], ["maya", "nuke"])
        self.assertEqual(controller.state["mayaProfiles"], ["maya2023"])
        self.assertFalse(controller.state["shortcuts"])
        controller.edit("shelf", "")
        controller.toggle("plugins", "maya", False)
        controller.toggle("plugins", "nuke", False)
        controller.back()
        controller._finished(("project", copy.deepcopy(catalog)))
        self.assertEqual(controller.state["shelf"], "")
        self.assertEqual(controller.state["plugins"], [])
        self.assertEqual(controller.state["mayaProfiles"], [])
        controller.session.login = "other_artist"
        controller._finished(("project", copy.deepcopy(catalog)))
        self.assertEqual(controller.state["shelf"], "one")
        self.assertEqual(controller.state["plugins"], ["maya"])
        self.assertEqual(controller.state["mayaProfiles"], [])
        controller.shutdown()

    def test_sign_in_distinguishes_credentials_connection_and_project_list_errors(self):
        for fault, message in (
            (
                Fault(1, "Login/Password combination incorrect"),
                "Incorrect login or password",
            ),
            (URLError("connection refused"), "Cannot connect to the server"),
            (
                HTTPError("http://example.invalid", 404, "Not Found", None, None),
                "HTTP 404",
            ),
        ):
            with (
                self.subTest(fault=type(fault).__name__),
                patch(
                    "thlib.side.client.tactic_client_lib.tactic_server_stub.TacticServerStub"
                ) as stub,
            ):
                stub.return_value.get_ticket.side_effect = fault
                with self.assertRaisesRegex(RuntimeError, message):
                    SetupSession().authenticate(
                        "http://example.invalid", "artist", "secret"
                    )
        with patch(
            "thlib.side.client.tactic_client_lib.tactic_server_stub.TacticServerStub"
        ) as stub:
            stub.return_value.get_ticket.return_value = "TEST-TICKET"
            stub.return_value.query.side_effect = Fault(1, "Permission denied")
            with self.assertRaisesRegex(
                RuntimeError, "Signed in, but the project list"
            ):
                SetupSession().authenticate(
                    "http://example.invalid", "artist", "secret"
                )

    def test_authentication_transport_keeps_https_and_bounds_connection_timeout(self):
        transport = SetupTransport("https://example.invalid")
        with (
            patch.object(transport._http, "open") as request,
            patch.object(transport, "parse_response", return_value={"ok": True}),
        ):
            result = transport.request(
                "example.invalid", "/tactic/default/Api/", b"test request"
            )
        self.assertEqual(result, {"ok": True})
        self.assertEqual(
            request.call_args.args[0].full_url,
            "https://example.invalid/tactic/default/Api/",
        )
        self.assertEqual(request.call_args.kwargs["timeout"], 20)

    def test_native_wizard_mouse_navigation_and_narrow_russian_layout(self):
        translator = CatalogTranslator(ROOT / "thlib/ui/translations/ru.json")
        self.app.installTranslator(translator)
        env_inst.start_pools()
        controller = SetupController(ROOT)
        engine = QQmlApplicationEngine()
        from thlib.ui.icon_font import qml_icon_bindings

        for name, value in qml_icon_bindings(ROOT, controller).items():
            engine.rootContext().setContextProperty(name, value)
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        engine.setInitialProperties({"controller": controller})
        engine.load(
            QUrl.fromLocalFile(
                str(ROOT / "thlib/ui/qml/features/setup/SetupWizard.qml")
            )
        )
        self.assertTrue(engine.rootObjects(), warnings)
        window = engine.rootObjects()[0]

        def item(name):
            return window.findChild(QObject, name)

        try:
            controller.session.authenticate = Mock(
                return_value=[{"code": "demo", "title": "Demo"}]
            )
            for name, value in (
                ("setupServer", "http://example.invalid"),
                ("setupLogin", "artist"),
                ("setupPassword", "secret"),
            ):
                field = item(name)
                field.forceActiveFocus()
                QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
                self.app.sendEvent(
                    window, QKeyEvent(QEvent.KeyPress, 0, Qt.NoModifier, value)
                )
            button = item("setupSignIn")
            QTest.mouseClick(
                window,
                Qt.LeftButton,
                pos=button.mapToScene(
                    QPointF(button.width() / 2, button.height() / 2)
                ).toPoint(),
            )
            deadline = time.monotonic() + 5
            while controller.state["busy"] and time.monotonic() < deadline:
                self.app.processEvents()
                QTest.qWait(5)
            self.assertEqual(controller.state["step"], 1)
            self.assertEqual(item("setupPassword").property("text"), "secret")
            QTest.qWait(30)
            back = item("setupBack")
            QTest.mouseClick(
                window,
                Qt.LeftButton,
                pos=back.mapToScene(
                    QPointF(back.width() / 2, back.height() / 2)
                ).toPoint(),
            )
            QTest.qWait(30)
            self.assertEqual(controller.state["step"], 0)
            self.assertEqual(
                item("setupServer").property("text"), "http://example.invalid"
            )
            self.assertEqual(item("setupLogin").property("text"), "artist")
            self.assertEqual(item("setupPassword").property("text"), "secret")
            controller._failed(
                RuntimeError(
                    "Incorrect login or password. Check these fields and try again."
                )
            )
            QTest.qWait(30)
            self.assertIn(
                "Неверный логин или пароль", item("setupError").property("text")
            )
            for width in (500, 900):
                window.setWidth(width)
                for step in range(5):
                    controller._state["step"] = step
                    controller.stateChanged.emit()
                    QTest.qWait(30)
                    next_button = item("setupNext")
                    if next_button.isVisible():
                        edge = next_button.mapToScene(
                            QPointF(next_button.width(), 0)
                        ).x()
                        self.assertLessEqual(edge, width)
                    self.assertEqual(warnings, [])
            self.assertEqual(item("setupPassword").property("text"), "")
            self.assertIsNone(item("setupRepositoryAlias"))
            controller._state.update(
                step=2,
                shelf="",
                shelves=[],
            )
            controller.stateChanged.emit()
            QTest.qWait(30)
            self.assertTrue(item("setupNoShelvesNote").property("visible"))
            controller._state.update(
                step=2,
                shelf="one",
                shelves=[{"id": "one", "title": "Assets Shelf", "buttons": []}],
            )
            controller.stateChanged.emit()
            QTest.qWait(30)
            self.assertFalse(item("setupNoShelvesNote").property("visible"))
            self.assertEqual(item("setupShelf").property("currentText"), "Assets Shelf")
            controller.attach_localization(self.app, translator, engine)
            controller.edit("language", "en")
            controller.toggle("darkTheme", "", False)
            controller.toggle("closeToTray", "", False)
            QTest.qWait(30)
            self.assertEqual(controller.state["language"], "en")
            self.assertFalse(controller.state["darkTheme"])
            self.assertFalse(controller.state["closeToTray"])
            self.assertEqual(window.property("title"), "TACTIC Handler Setup")
            controller.edit("language", "ru")
            QTest.qWait(30)
            self.assertEqual(window.property("title"), "Настройка TACTIC Handler")
        finally:
            controller.shutdown()
            window.close()
            engine.deleteLater()
            self.app.processEvents()
            env_inst.exit_pools()
            env_inst.local_pool.reopen()
            self.app.removeTranslator(translator)


if __name__ == "__main__":
    unittest.main()
