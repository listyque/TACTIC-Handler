from __future__ import annotations

import importlib
from hashlib import sha256
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch
from xmlrpc.client import Fault
from zipfile import ZipFile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from server_plugin.build_plugin import MODULE_NAME, SOURCE, build, server_source
from server_plugin import deploy as plugin_deploy
from thlib import environment
from thlib import tactic_classes as tc
from thlib import tactic_query as tq
from thlib.ui.configuration import ConfigurationController
from thlib.ui.workspace_models.records import RecordListModel


class ServerQueryPluginTests(unittest.TestCase):
    def test_compiled_plugin_build_uses_bundled_source(self):
        with TemporaryDirectory() as directory:
            source_path = Path(directory) / "tactic_query.py"
            source_path.with_suffix(".source").write_bytes(SOURCE.read_bytes())
            with patch("server_plugin.build_plugin.SOURCE", source_path):
                server_source.cache_clear()
                try:
                    self.assertIn(
                        b"def get_projects_and_logins(", server_source()
                    )
                finally:
                    server_source.cache_clear()

    def test_compiled_plugin_build_uses_bundled_package_files(self):
        from server_plugin.build_plugin import PACKAGE

        with TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / MODULE_NAME
            package.mkdir()
            for name in ("__init__.py", "command.py"):
                (package / name).with_suffix(".source").write_bytes(
                    (PACKAGE / name).read_bytes()
                )
            (package / "manifest.xml").write_bytes(
                (PACKAGE / "manifest.xml").read_bytes()
            )
            with patch("server_plugin.build_plugin.PACKAGE", package):
                archive_path = build(root / "plugin.zip")
            with ZipFile(archive_path) as archive:
                self.assertIn(f"{MODULE_NAME}/__init__.py", archive.namelist())
                self.assertIn(f"{MODULE_NAME}/command.py", archive.namelist())

    def test_server_procedure_change_keeps_stable_package_name(self):
        with TemporaryDirectory() as directory:
            with patch("server_plugin.build_plugin.server_source",
                       return_value=server_source() + b"\n# update\n"):
                archive = build(Path(directory) / "queries.zip")
            with ZipFile(archive) as packaged:
                self.assertIn(f"{MODULE_NAME}/api.py", packaged.namelist())
                self.assertTrue(packaged.read(f"{MODULE_NAME}/api.py").endswith(
                    b"# update\n"
                ))

    def test_deploy_uploads_built_package_before_installing(self):
        server = Mock()

        def install(_func, _kwargs, **_options):
            path = Path(server.upload_file.call_args.args[0])
            self.assertTrue(path.is_file())
            self.assertEqual(path.name, MODULE_NAME + ".zip")
            self.assertEqual(_kwargs["expected_sha256"],
                             sha256(path.read_bytes()).hexdigest())
            self.assertNotIn("module_name", _kwargs)
            return "installed"

        with patch.object(tc, "execute_procedure_serverside",
                          side_effect=install) as execute:
            self.assertEqual(plugin_deploy.deploy(server), "installed")
        server.upload_file.assert_called_once()
        self.assertIs(execute.call_args.args[0],
                      plugin_deploy._install_uploaded_plugin)
        self.assertIs(execute.call_args.kwargs["server"], server)

    def test_install_procedure_requires_server_admin(self):
        pyasm = ModuleType("pyasm")
        common = ModuleType("pyasm.common")
        tactic = ModuleType("tactic")
        command = ModuleType("tactic.command")
        common.Environment = SimpleNamespace(
            get_security=lambda: SimpleNamespace(is_admin=lambda: False)
        )
        command.PluginInstaller = Mock()
        with patch.dict(sys.modules, {
            "pyasm": pyasm, "pyasm.common": common,
            "tactic": tactic, "tactic.command": command,
        }):
            with self.assertRaisesRegex(PermissionError, "administrator"):
                plugin_deploy._install_uploaded_plugin("unused")
        command.PluginInstaller.assert_not_called()

    def test_install_procedure_uses_tactic_plugin_directory_and_is_idempotent(self):
        pyasm = ModuleType("pyasm")
        common = ModuleType("pyasm.common")
        tactic = ModuleType("tactic")
        command = ModuleType("tactic.command")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            uploads = root / "uploads"
            plugins = root / "plugins"
            uploads.mkdir()
            plugins.mkdir()
            archive = build(uploads / (MODULE_NAME + ".zip"))
            digest = sha256(archive.read_bytes()).hexdigest()
            common.Environment = SimpleNamespace(
                get_security=lambda: SimpleNamespace(is_admin=lambda: True),
                get_upload_dir=lambda: str(uploads),
                get_plugin_dir=lambda: str(plugins),
            )

            class Installer:
                calls = 0

                def __init__(self, **kwargs):
                    self.asserted_kwargs = kwargs

                def execute(self):
                    Installer.calls += 1
                    with ZipFile(archive) as packaged:
                        for name in packaged.namelist():
                            path = plugins / name
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(packaged.read(name))

            command.PluginInstaller = Installer
            with patch.dict(sys.modules, {
                "pyasm": pyasm, "pyasm.common": common,
                "tactic": tactic, "tactic.command": command,
            }):
                self.assertEqual(plugin_deploy._install_uploaded_plugin(digest),
                                 "installed")
                self.assertEqual(plugin_deploy._install_uploaded_plugin(digest),
                                 "unchanged")
            self.assertEqual(Installer.calls, 1)

    def test_unchanged_install_does_not_reload_loaded_module(self):
        pyasm = ModuleType("pyasm")
        common = ModuleType("pyasm.common")
        tactic = ModuleType("tactic")
        command = ModuleType("tactic.command")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            uploads = root / "uploads"
            plugins = root / "plugins"
            uploads.mkdir()
            plugins.mkdir()
            archive = build(uploads / (MODULE_NAME + ".zip"))
            with ZipFile(archive) as packaged:
                for name in packaged.namelist():
                    path = plugins / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(packaged.read(name))
            common.Environment = SimpleNamespace(
                get_security=lambda: SimpleNamespace(is_admin=lambda: True),
                get_upload_dir=lambda: str(uploads),
                get_plugin_dir=lambda: str(plugins),
            )
            command.PluginInstaller = Mock()
            modules = {
                "pyasm": pyasm, "pyasm.common": common,
                "tactic": tactic, "tactic.command": command,
                "tactic_handler_queries": ModuleType("tactic_handler_queries"),
                "tactic_handler_queries.api": ModuleType("tactic_handler_queries.api"),
                "tactic_handler_queries.command": ModuleType("tactic_handler_queries.command"),
            }
            with patch.dict(sys.modules, modules):
                self.assertEqual(
                    plugin_deploy._install_uploaded_plugin(
                        sha256(archive.read_bytes()).hexdigest()
                    ),
                    "unchanged",
                )
            command.PluginInstaller.assert_not_called()

    def test_install_procedure_rejects_unexpected_archive_entry(self):
        pyasm = ModuleType("pyasm")
        common = ModuleType("pyasm.common")
        tactic = ModuleType("tactic")
        command = ModuleType("tactic.command")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / (MODULE_NAME + ".zip")
            with ZipFile(archive, "w") as packaged:
                packaged.writestr("../outside.py", "pass")
            common.Environment = SimpleNamespace(
                get_security=lambda: SimpleNamespace(is_admin=lambda: True),
                get_upload_dir=lambda: str(root),
            )
            command.PluginInstaller = Mock()
            with patch.dict(sys.modules, {
                "pyasm": pyasm, "pyasm.common": common,
                "tactic": tactic, "tactic.command": command,
            }):
                with self.assertRaisesRegex(ValueError, "archive contents"):
                    plugin_deploy._install_uploaded_plugin(
                        sha256(archive.read_bytes()).hexdigest()
                    )
        command.PluginInstaller.assert_not_called()

    def test_built_package_uses_exact_client_procedure_source(self):
        with TemporaryDirectory() as directory:
            archive_path = build(Path(directory) / "queries.zip")
            with ZipFile(archive_path) as archive:
                self.assertEqual(
                    archive.read(f"{MODULE_NAME}/api.py"),
                    server_source(),
                )
                api_source = archive.read(f"{MODULE_NAME}/api.py")
                self.assertIn(b"def get_projects_and_logins(", api_source)
                self.assertNotIn(b"def prepare_serverside_script(", api_source)
                self.assertNotIn(b"def _function_source_lines(", api_source)
                self.assertNotIn(b"def _parse_procedure_module(", api_source)
                self.assertNotIn(b"def traceback_handle(", api_source)
                self.assertNotIn(b"def get_traceback(", api_source)
                self.assertIn(
                    f"{MODULE_NAME}/command.py", archive.namelist()
                )
                self.assertIn(
                    f"<code>{MODULE_NAME}</code>".encode(),
                    archive.read(f"{MODULE_NAME}/manifest.xml"),
                )

    def test_updated_api_loads_only_on_version_mismatch(self):
        from server_plugin.build_plugin import PACKAGE

        original = b"def probe():\n    return server.marker\n"
        updated = b"def probe():\n    return server.marker + '-new'\n"
        with TemporaryDirectory() as directory:
            package = Path(directory) / MODULE_NAME
            package.mkdir()
            (package / "__init__.py").write_bytes(
                (PACKAGE / "__init__.py").read_bytes()
            )
            api_path = package / "api.py"
            api_path.write_bytes(original)
            sys.path.insert(0, directory)
            try:
                plugin = importlib.import_module(MODULE_NAME)
                server = SimpleNamespace(marker="ok")
                first_hash = sha256(original).hexdigest()
                self.assertEqual(plugin.invoke("probe", {}, server, first_hash), "ok")
                self.assertEqual(
                    plugin.invoke("probe", {}, SimpleNamespace(marker="two"),
                                  first_hash),
                    "two",
                )
                with self.assertRaises(LookupError):
                    _ = plugin._RequestServer().marker
                with self.assertRaisesRegex(ValueError, "Unknown"):
                    plugin.invoke("missing", {}, server, first_hash)
                with self.assertRaisesRegex(TypeError, "dictionary"):
                    plugin.invoke("probe", None, server, first_hash)
                with patch("builtins.open", side_effect=AssertionError("disk read")):
                    self.assertEqual(
                        plugin.invoke("probe", {}, server, first_hash), "ok"
                    )
                invalid = b"def probe(:\n"
                api_path.write_bytes(invalid)
                with self.assertRaises(SyntaxError):
                    plugin.invoke("probe", {}, server, sha256(invalid).hexdigest())
                self.assertEqual(plugin.invoke("probe", {}, server, first_hash), "ok")
                api_path.write_bytes(updated)
                self.assertEqual(
                    plugin.invoke("probe", {}, server, sha256(updated).hexdigest()),
                    "ok-new",
                )
                with self.assertRaisesRegex(RuntimeError, "out of date"):
                    plugin.invoke("probe", {}, server, first_hash)
            finally:
                sys.path.remove(directory)
                for name in list(sys.modules):
                    if name == MODULE_NAME or name.startswith(
                        MODULE_NAME + "."
                    ):
                        del sys.modules[name]

    def test_plugin_mode_routes_only_bundled_queries(self):
        server = Mock()
        server.execute_cmd.return_value = {"info": "ok"}
        with (
            patch.object(tc, "env_read_config", return_value={
                "modes": {"http://test": "plugin"}
            }),
            patch.object(tc.env_server, "get_server", return_value="http://test"),
        ):
            result = tc.execute_procedure_serverside(
                tq.get_projects_and_logins, {"current_login": "admin"},
                server=server, return_dict=False,
            )
        self.assertEqual(result, "ok")
        server.execute_python_script.assert_not_called()
        self.assertEqual(
            server.execute_cmd.call_args.args[0],
            MODULE_NAME + ".command.QueryCommand",
        )
        payload = server.execute_cmd.call_args.kwargs["args"]
        self.assertEqual(payload["procedure"], "get_projects_and_logins")
        self.assertEqual(payload["arguments"], {"current_login": "admin"})
        self.assertEqual(payload["source_sha256"], tc._query_source_sha256())
        self.assertNotIn("code", payload)

    def test_local_mode_keeps_existing_source_shipping(self):
        server = Mock()
        server.execute_python_script.return_value = {
            "info": {"spt_ret_val": "ok"}
        }
        with (
            patch.object(tc, "env_read_config", return_value={
                "modes": {"http://another-server": "plugin"}
            }),
            patch.object(tc.env_server, "get_server", return_value="http://test"),
        ):
            tc.execute_procedure_serverside(
                tq.get_projects_and_logins, {}, server=server,
                return_dict=False,
            )
        payload = server.execute_python_script.call_args.kwargs["kwargs"]
        self.assertIn("def get_projects_and_logins", payload["code"])
        self.assertNotIn("procedure", payload)

    def test_native_server_traceback_is_preserved(self):
        server = Mock()
        server.execute_cmd.side_effect = Fault(
            1, 'Traceback (most recent call last):\n'
               '  File "command.py", line 20, in execute\n'
               'TypeError: bad arguments'
        )
        with (
            patch.object(tc, "env_read_config", return_value={
                "modes": {"http://test": "plugin"}
            }),
            patch.object(tc.env_server, "get_server", return_value="http://test"),
            patch.object(tc.dl, "exception"),
        ):
            with self.assertRaises(tc.TacticProcedureError) as raised:
                tc.execute_procedure_serverside(
                    tq.get_projects_and_logins, {}, server=server,
                )
        self.assertIn("command.py", raised.exception.server_traceback)
        self.assertIn("TypeError", raised.exception.server_traceback)

    def test_missing_plugin_install_failure_does_not_use_local_for_data_queries(self):
        server = Mock()
        server.execute_cmd.side_effect = Fault(
            1, "No module named 'tactic_handler_queries'"
        )
        with (
            patch.object(tc, "env_read_config", return_value={
                "modes": {"http://test": "plugin"}
            }),
            patch.object(tc.env_server, "get_server", return_value="http://test"),
            patch.object(plugin_deploy, "deploy", side_effect=Fault(
                1, "TACTIC administrator access is required"
            )),
        ):
            with self.assertRaisesRegex(PermissionError, "Local"):
                tc.execute_procedure_serverside(
                    tq.query_sobjects, {}, server=server,
                )
        server.execute_python_script.assert_not_called()

    def test_missing_plugin_bootstraps_once_then_retries_native_command(self):
        server = Mock()
        server.execute_cmd.side_effect = [
            Fault(1, "No module named 'tactic_handler_queries'"),
            Fault(1, "No module named 'tactic_handler_queries'"),
            {"info": "ok"},
        ]
        with (
            patch.object(tc, "env_read_config", return_value={
                "modes": {"http://test": "plugin"}
            }),
            patch.object(tc.env_server, "get_server", return_value="http://test"),
            patch.object(plugin_deploy, "deploy", return_value="installed") as deploy,
        ):
            result = tc.execute_procedure_serverside(
                tq.get_projects_and_logins, {}, server=server,
                return_dict=False,
            )
        self.assertEqual(result, "ok")
        deploy.assert_called_once_with(server)
        self.assertEqual(server.execute_cmd.call_count, 3)
        server.execute_python_script.assert_not_called()

    def test_existing_plugin_recovers_when_new_module_becomes_importable(self):
        server = Mock()
        missing = Fault(
            1, "No module named 'tactic_handler_queries'"
        )
        server.execute_cmd.side_effect = [missing, missing, missing, {"info": "ok"}]
        with (
            patch.object(plugin_deploy, "deploy", return_value="unchanged") as deploy,
            patch("time.sleep") as sleep,
        ):
            result = tc._execute_plugin_command(server, {})
        self.assertEqual(result, {"info": "ok"})
        deploy.assert_called_once_with(server)
        sleep.assert_called()

    def test_installer_invalidates_python_import_caches(self):
        pyasm = ModuleType("pyasm")
        common = ModuleType("pyasm.common")
        tactic = ModuleType("tactic")
        command = ModuleType("tactic.command")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            uploads = root / "uploads"
            plugins = root / "plugins"
            uploads.mkdir()
            plugins.mkdir()
            archive = build(uploads / (MODULE_NAME + ".zip"))
            common.Environment = SimpleNamespace(
                get_security=lambda: SimpleNamespace(is_admin=lambda: True),
                get_upload_dir=lambda: str(uploads),
                get_plugin_dir=lambda: str(plugins),
            )

            class Installer:
                def __init__(self, **kwargs):
                    pass

                def execute(self):
                    with ZipFile(archive) as packaged:
                        packaged.extractall(plugins)

            command.PluginInstaller = Installer
            sys.path.insert(0, str(plugins))
            try:
                with self.assertRaises(ModuleNotFoundError):
                    importlib.import_module(MODULE_NAME)
                with (
                    patch.dict(sys.modules, {
                        "pyasm": pyasm, "pyasm.common": common,
                        "tactic": tactic, "tactic.command": command,
                    }),
                    patch("importlib.invalidate_caches",
                          wraps=importlib.invalidate_caches) as invalidate,
                ):
                    plugin_deploy._install_uploaded_plugin(
                        sha256(archive.read_bytes()).hexdigest()
                    )
                    self.assertIsNotNone(importlib.import_module(MODULE_NAME))
                    plugin_deploy._install_uploaded_plugin(
                        sha256(archive.read_bytes()).hexdigest()
                    )
                self.assertEqual(invalidate.call_count, 2)
            finally:
                sys.path.remove(str(plugins))
                for name in list(sys.modules):
                    if name == MODULE_NAME or name.startswith(MODULE_NAME + "."):
                        del sys.modules[name]

    def test_import_failure_after_retries_requests_service_restart(self):
        server = Mock()
        server.execute_cmd.side_effect = Fault(
            1, "No module named 'tactic_handler_queries'"
        )
        with (
            patch.object(plugin_deploy, "deploy", return_value="installed"),
            patch("time.sleep") as sleep,
        ):
            with self.assertRaisesRegex(RuntimeError, "Restart the TACTIC service"):
                tc._execute_plugin_command(server, {})
        self.assertEqual(server.execute_cmd.call_count, 5)
        self.assertEqual(sleep.call_count, 2)

    def test_stale_plugin_cannot_block_bootstrap_queries(self):
        server = Mock()
        server.execute_cmd.side_effect = Fault(
            1, "TACTIC-Handler query plugin is out of date"
        )
        server.execute_python_script.return_value = {
            "info": {"spt_ret_val": {"projects": [], "logins": []}}
        }
        with (
            patch.object(tc, "env_read_config", return_value={
                "modes": {"http://test": "plugin"}
            }),
            patch.object(tc.env_server, "get_server", return_value="http://test"),
            patch.object(plugin_deploy, "deploy", return_value="installed"),
        ):
            result = tc.execute_procedure_serverside(
                tq.get_projects_and_logins, {}, server=server,
            )
        self.assertEqual(result, {"projects": [], "logins": []})
        self.assertIn(
            "def get_projects_and_logins",
            server.execute_python_script.call_args.kwargs["kwargs"]["code"],
        )

    def test_missing_plugin_cannot_block_nonadmin_sign_in(self):
        server = Mock()
        server.execute_cmd.side_effect = Fault(
            1, "No module named 'tactic_handler_queries'"
        )
        server.execute_python_script.return_value = {
            "info": {"spt_ret_val": {"projects": []}}
        }
        with (
            patch.object(tc, "env_read_config", return_value={
                "modes": {"http://test": "plugin"}
            }),
            patch.object(tc.env_server, "get_server", return_value="http://test"),
            patch.object(plugin_deploy, "deploy", side_effect=Fault(
                1, "TACTIC administrator access is required"
            )),
        ):
            result = tc.execute_procedure_serverside(
                tq.get_projects_and_logins, {}, server=server,
            )
        self.assertEqual(result, {"projects": []})
        server.execute_python_script.assert_called_once()

    def test_outdated_data_query_does_not_silently_use_local(self):
        server = Mock()
        server.execute_cmd.side_effect = Fault(
            1, "TACTIC-Handler query plugin is out of date"
        )
        with (
            patch.object(tc, "env_read_config", return_value={
                "modes": {"http://test": "plugin"}
            }),
            patch.object(tc.env_server, "get_server", return_value="http://test"),
            patch.object(plugin_deploy, "deploy",
                         return_value="installed") as deploy,
        ):
            with self.assertRaises(tc.TacticProcedureError):
                tc.execute_procedure_serverside(
                    tq.query_server_updates, {"include_activity": True},
                    server=server,
                )
        deploy.assert_called_once_with(server)
        self.assertEqual(server.execute_cmd.call_count, 3)
        server.execute_python_script.assert_not_called()

    def test_sobject_filters_are_xmlrpc_command_safe(self):
        with patch.object(tc, "_execute_read_only_procedure_serverside",
                          return_value=None) as execute:
            tc.get_sobjects(
                "sthpw/task?project=sthpw",
                filters=[("description", "кириллица")],
                project_code="sthpw",
            )
        self.assertIsInstance(execute.call_args.args[1]["filters"], str)
        self.assertEqual(
            execute.call_args.args[1]["filters"],
            '[["description", "кириллица"]]',
        )

    def test_query_mode_is_saved_on_server_configuration_page(self):
        with patch("thlib.ui.configuration.env_read_config", return_value={}):
            controller = ConfigurationController(Mock(), Mock())
        controller._pending_values["server"] = controller._normalize_server({
            "serverUrl": "http://127.0.0.1:9123",
            "presetName": "default",
            "queryMode": "plugin",
        })
        controller._dirty_pages.add("server")
        with (
            patch("thlib.environment.env_server.get_server_presets",
                  return_value={"presets_list": ["default"]}),
            patch("thlib.ui.configuration.env_read_config", return_value={}),
            patch("thlib.ui.configuration.env_write_config") as write,
        ):
            self.assertTrue(controller._apply_page("server"))
        write.assert_called_once_with(
            {"modes": {"http://127.0.0.1:9123": "plugin"}},
            filename="server_query",
            unique_id="ui_conf", long_abs_path=True,
            scope="installation",
        )

    def test_saved_query_mode_survives_login_change(self):
        server_url = "http://127.0.0.1:9123"
        current_user = [""]
        with (
            TemporaryDirectory() as directory,
            patch.object(environment.env_mode, "get_current_path",
                         return_value=directory),
            patch.object(environment.env_server, "get_user",
                         side_effect=lambda: current_user[0]),
            patch.object(environment.env_server, "get_server",
                         return_value=server_url),
            patch.object(environment.env_server, "get_server_presets",
                         return_value={"presets_list": ["default"]}),
        ):
            controller = ConfigurationController(Mock(), Mock())
            controller._pending_values["server"] = controller._normalize_server({
                "serverUrl": server_url,
                "presetName": "default",
                "queryMode": "plugin",
            })
            controller._dirty_pages.add("server")
            self.assertTrue(controller._apply_page("server"))

            current_user[0] = "admin"
            self.assertEqual(
                ConfigurationController(Mock(), Mock())._server_values()[
                    "queryMode"
                ],
                "plugin",
            )
            server = Mock()
            server.execute_cmd.return_value = {"info": "ok"}
            tc.execute_procedure_serverside(
                tq.get_projects_and_logins, {}, server=server,
                return_dict=False,
            )
            server.execute_cmd.assert_called_once()
            server.execute_python_script.assert_not_called()

    def test_server_page_renders_plugin_selector_at_two_widths(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        qml_dir = SOURCE.parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        engine.addImportPath(str(qml_dir))
        presets = RecordListModel(("label",), [{"label": "Default"}])
        engine.rootContext().setContextProperty("serverPresetModel", presets)
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "." as App

ApplicationWindow {
    width: 880
    height: 700
    visible: true
    App.Theme { id: theme; dark: true }
    QtObject {
        id: appController
        property bool has_ticket: false
        property bool authentication_required: true
        property string login_name: ""
    }
    QtObject {
        id: windowModel
        function show_window(name) {}
    }
    QtObject {
        id: configurationController
        objectName: "queryConfigurationController"
        signal sessionStarted()
        signal pageReset(string pageId)
        property bool server_test_busy: false
        property string server_test_status: "idle"
        property string server_test_message: ""
        property var updatedValues: ({})
        function page_values(pageId) {
            return ({"serverUrl": "http://127.0.0.1:9123",
                     "presetName": "Default", "queryMode": "plugin"})
        }
        function server_preset_values(name) { return page_values("server") }
        function update_page(pageId, values) { updatedValues = values }
        function test_server(values) {}
    }
    App.ConfigurationServerPage {
        id: page
        objectName: "serverPage"
        anchors.fill: parent
        theme: theme
        managed: true
    }
}
''', QUrl.fromLocalFile(str(qml_dir / "_ServerQueryModeTest.qml")))
        owner = component.create()
        self.assertIsNotNone(owner, [error.toString() for error in component.errors()])
        try:
            for width in (880, 520):
                owner.setProperty("width", width)
                QTest.qWait(30)
                combo = owner.findChild(QObject, "queryModeCombo")
                self.assertIsNotNone(combo)
                self.assertEqual(combo.property("currentIndex"), 1)
                self.assertGreater(combo.property("width"), 0)
            owner.setProperty("width", 880)
            QTest.qWait(30)
            combo = owner.findChild(QQuickItem, "queryModeCombo")
            QTest.mouseClick(
                owner, Qt.LeftButton,
                pos=combo.mapToScene(QPointF(
                    combo.width() / 2, combo.height() / 2,
                )).toPoint(),
            )
            QTest.keyClick(owner, Qt.Key_Up)
            QTest.keyClick(owner, Qt.Key_Return)
            self.assertEqual(combo.property("currentIndex"), 0)
            controller = owner.findChild(
                QObject, "queryConfigurationController"
            )
            self.assertEqual(
                controller.property("updatedValues").toVariant()["queryMode"],
                "local",
            )
        finally:
            owner.close()
            owner.deleteLater()
            presets.deleteLater()
            engine.deleteLater()


if __name__ == "__main__":
    unittest.main()
