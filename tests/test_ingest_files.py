from __future__ import annotations

import os
from pathlib import Path
import tempfile
import textwrap
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from thlib import tactic_query as tq
from thlib.ui.ingest import IngestFilesController, _RULE_OPTION_DEFAULTS
from thlib.ui.ingest_preflight import find_ingest_conflicts
from thlib.ui.localization import CatalogTranslator


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class _WindowModel(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.shown = []

    @Slot(str)
    def show_window(self, window_id):
        self.shown.append(str(window_id))

    @Slot(str)
    def hide_window(self, _window_id):
        pass


class _Application(QObject):
    def __init__(self):
        super().__init__()
        self.workspace_model = SimpleNamespace(node_for=lambda _node_id: None)
        self.window_model = _WindowModel(self)
        self.notifications = []

    def notify(self, message):
        self.notifications.append(str(message))

    def refresh_current(self):
        pass


class _Server:
    def __init__(self, query_result=None, command_result=None):
        self.uploads = []
        self.commands = []
        self.queries = []
        self.query_result = list(query_result or [])
        self.command_result = command_result or {
            "snapshots": [{"code": "SNAPSHOT0001"}],
        }
        self.transactions = []

    def upload_file(self, path):
        self.uploads.append(str(path))

    def execute_cmd(self, command, arguments):
        self.commands.append((command, dict(arguments)))
        return self.command_result

    def start(self, title, description=""):
        self.transactions.append(("start", title, description))

    def finish(self, description=""):
        self.transactions.append(("finish", description))

    def abort(self):
        self.transactions.append(("abort",))

    def query(self, search_type, filters, parent_key=None):
        self.queries.append((search_type, list(filters), parent_key))
        return list(self.query_result)

    @staticmethod
    def build_search_key(
        search_type, code, project_code=None, column="code",
    ):
        return (
            f"{search_type}?project={project_code}&{column}={code}"
        )


class IngestFilesControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_native_batch_creates_one_child_per_file_in_publish(self):
        server = _Server()
        with tempfile.TemporaryDirectory() as folder:
            paths = []
            for name in ("shot_010.mov", "shot_020.exr"):
                path = Path(folder, name)
                path.write_bytes(b"fixture")
                paths.append(str(path))
            options = dict(_RULE_OPTION_DEFAULTS)
            options["extraData"] = {}
            with (
                patch(
                    "thlib.tactic_classes.server_start",
                    return_value=server,
                ),
                patch("thlib.server_cache.invalidate_domains") as invalidate,
            ):
                result = IngestFilesController._ingest_batch(
                    {
                        "projectCode": "demo",
                        "searchType": "demo/shot",
                        "parentKey": "demo/episode?code=EP01",
                        "paths": paths,
                        "options": options,
                    },
                    threading.Event(),
                )

        self.assertEqual([row["status"] for row in result], [
            "Completed", "Completed",
        ])
        self.assertEqual(server.uploads, paths)
        self.assertEqual(len(server.commands), 2)
        for index, (command, arguments) in enumerate(server.commands):
            self.assertEqual(command, "tactic.ui.tools.IngestUploadCmd")
            self.assertEqual(arguments["search_type"], "demo/shot")
            self.assertEqual(
                arguments["parent_key"], "demo/episode?code=EP01"
            )
            self.assertEqual(arguments["filenames"], [Path(paths[index]).name])
            self.assertEqual(arguments["ignore_ext"], "true")
            self.assertEqual(arguments["process"], "publish")
            self.assertEqual(arguments["context"], "publish")
            self.assertEqual(arguments["update_data"], {})
            self.assertTrue(arguments["message_key"].startswith(
                "IngestUploadCmd|demo/episode?code=EP01|"
            ))
        invalidate.assert_called_once_with(
            ("search", "snapshots", "relations", "activity"), "demo"
        )

    def test_relation_context_keeps_instance_metadata_for_the_drop_target(self):
        class Stype:
            @staticmethod
            def get_project():
                return SimpleNamespace(get_code=lambda: "demo")

            @staticmethod
            def get_code():
                return "demo/shot"

            @staticmethod
            def get_pretty_name():
                return "Shots"

            @staticmethod
            def column_exists(column):
                return column in {"name", "code"}

            @staticmethod
            def get_schema():
                return SimpleNamespace(get_parent_instance=lambda *_args: {
                    "path": "episode",
                })

        parent = SimpleNamespace(
            get_search_key=lambda: "demo/episode?code=EP01",
            get_title=lambda: "Episode 01",
        )
        node = SimpleNamespace(
            node_type="relation",
            source=parent,
            relation={
                "stype": Stype(),
                "definition": {
                    "relationship": "instance",
                    "instance_type": "demo/episode_in_shot",
                },
            },
        )
        application = _Application()
        application.workspace_model = SimpleNamespace(
            node_for=lambda _node_id: node
        )
        controller = IngestFilesController(application)

        context = controller._relation_context("relation-node")

        self.assertEqual(context["parentKey"], "demo/episode?code=EP01")
        self.assertEqual(context["relation"], {
            "relationship": "instance",
            "instanceType": "demo/episode_in_shot",
            "instancePath": "episode",
        })

    def test_ingest_rule_pattern_and_scripts_feed_native_command(self):
        server = _Server()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "shot_030_anim.mov")
            path.write_bytes(b"fixture")
            options = dict(_RULE_OPTION_DEFAULTS)
            options.update({
                "extraData": {"status": "Pending"},
                "usePattern": True,
                "pattern": "{sobject.name}_{snapshot.context}.mov",
                "validationScript": "rules/validate.py",
                "processScript": "rules/enrich.py",
            })
            preflight = {
                "accepted": True,
                "data": {
                    "description": "Prepared by rule",
                    "id": 99,
                },
                "snapshot_data": {"context": "animation"},
                "search_key": "",
            }
            with (
                patch(
                    "thlib.tactic_classes.server_start",
                    return_value=server,
                ),
                patch(
                    "thlib.tactic_classes.execute_procedure_serverside",
                    return_value=preflight,
                ) as execute_procedure,
                patch("thlib.server_cache.invalidate_domains"),
            ):
                result = IngestFilesController._ingest_batch(
                    {
                        "projectCode": "demo",
                        "searchType": "demo/shot",
                        "parentKey": "demo/episode?code=EP01",
                        "paths": [str(path)],
                        "options": options,
                    },
                    threading.Event(),
                )

        self.assertEqual(result[0]["status"], "Completed")
        execute_procedure.assert_called_once()
        arguments = server.commands[0][1]
        self.assertEqual(arguments["context"], "animation")
        self.assertNotIn('"id"', arguments["extra_data"])
        self.assertIn('"name": "shot_030"', arguments["extra_data"])
        self.assertIn(
            '"description": "Prepared by rule"', arguments["extra_data"]
        )

    def test_selecting_a_saved_rule_keeps_its_payload(self):
        controller = IngestFilesController(_Application())
        controller._target_search_type = "demo/shot"
        controller._replace_rules([{
            "code": "shot-rule",
            "__search_key__": "config/ingest_rule?code=shot-rule",
            "title": "Shot filenames",
            "data": {
                "search_type": "demo/shot",
                "filter": ".mov",
                "validation_script": "rules/shot.py",
            },
        }])

        controller.select_rule(1)
        self.assertEqual(controller.options["filter"], ".mov")
        self.assertEqual(
            controller.options["validationScript"], "rules/shot.py"
        )
        controller.select_rule(0)
        controller.select_rule(1)
        self.assertEqual(controller.options["filter"], ".mov")

    def test_ingest_preflight_is_a_self_contained_server_script(self):
        code = tq.prepare_serverside_script(
            tq.ingest_rule_preflight,
            {
                "search_type": "demo/shot",
                "parent_key": "demo/episode?code=EP01",
                "filename": "shot_010.mov",
                "validation_script": "rules/validate.py",
            },
            shrink=False,
            catch_traceback=False,
        )["code"]

        compile(
            "def execute():\n" + textwrap.indent(code, "    "),
            "<ingest-rule-preflight>",
            "exec",
        )
        self.assertIn("SearchType.create(search_type)", code)
        self.assertIn("PythonCmd", code)

        link_code = tq.prepare_serverside_script(
            tq.link_ingested_sobject,
            {
                "project_code": "demo",
                "child_key": "demo/shot?code=SHOT010",
                "parent_key": "demo/episode?code=EP01",
                "relationship": "instance",
                "instance_type": "demo/episode_in_shot",
            },
            shrink=False,
            catch_traceback=False,
        )["code"]
        compile(
            "def execute():\n" + textwrap.indent(link_code, "    "),
            "<link-ingested-sobject>",
            "exec",
        )
        self.assertIn("add_related_connection", link_code)

        query_code = tq.prepare_serverside_script(
            tq.query_ingest_relation_matches,
            {
                "project_code": "demo",
                "search_type": "demo/shot",
                "parent_key": "demo/episode?code=EP01",
                "column": "name",
                "names": ["shot_010"],
                "instance_path": "episode",
            },
            shrink=False,
            catch_traceback=False,
        )["code"]
        compile(
            "def execute():\n" + textwrap.indent(query_code, "    "),
            "<query-ingest-relation-matches>",
            "exec",
        )
        self.assertIn("add_relationship_filter", query_code)

    def test_new_ingest_is_linked_to_its_instance_parent_atomically(self):
        server = _Server(command_result={
            "info": {
                "snapshots": [{
                    "search_type": "demo/shot?project=demo",
                    "search_code": "SHOT010",
                }],
            },
        })
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "shot_010.mov")
            path.write_bytes(b"fixture")
            options = dict(_RULE_OPTION_DEFAULTS)
            options["extraData"] = {}
            with (
                patch(
                    "thlib.tactic_classes.server_start",
                    return_value=server,
                ),
                patch(
                    "thlib.tactic_classes.execute_procedure_serverside",
                    return_value="demo/shot?project=demo&code=SHOT010",
                ) as execute_procedure,
                patch("thlib.server_cache.invalidate_domains"),
            ):
                result = IngestFilesController._ingest_batch(
                    {
                        "projectCode": "demo",
                        "searchType": "demo/shot",
                        "parentKey": "demo/episode?code=EP01",
                        "paths": [str(path)],
                        "options": options,
                        "relation": {
                            "relationship": "instance",
                            "instanceType": "demo/episode_in_shot",
                            "instancePath": "episode",
                        },
                    },
                    threading.Event(),
                )

        self.assertEqual(result[0]["status"], "Completed")
        self.assertEqual(
            [entry[0] for entry in server.transactions],
            ["start", "finish"],
        )
        procedure, values = execute_procedure.call_args.args[:2]
        self.assertIs(procedure, tq.link_ingested_sobject)
        self.assertEqual(
            values["child_key"],
            "demo/shot?project=demo&code=SHOT010",
        )
        self.assertEqual(values["parent_key"], "demo/episode?code=EP01")
        self.assertEqual(values["instance_type"], "demo/episode_in_shot")
        self.assertEqual(values["instance_path"], "episode")

    def test_failed_child_link_aborts_the_ingest_transaction(self):
        server = _Server(command_result={
            "info": {
                "snapshots": [{
                    "search_type": "demo/shot?project=demo",
                    "search_code": "SHOT010",
                }],
            },
        })
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "shot_010.mov")
            path.write_bytes(b"fixture")
            options = dict(_RULE_OPTION_DEFAULTS)
            options["extraData"] = {}
            with (
                patch(
                    "thlib.tactic_classes.server_start",
                    return_value=server,
                ),
                patch(
                    "thlib.tactic_classes.execute_procedure_serverside",
                    side_effect=RuntimeError("Could not create relation"),
                ),
                patch("thlib.server_cache.invalidate_domains"),
            ):
                result = IngestFilesController._ingest_batch(
                    {
                        "projectCode": "demo",
                        "searchType": "demo/shot",
                        "parentKey": "demo/episode?code=EP01",
                        "paths": [str(path)],
                        "options": options,
                        "relation": {
                            "relationship": "instance",
                            "instanceType": "demo/episode_in_shot",
                        },
                    },
                    threading.Event(),
                )

        self.assertEqual(result[0]["status"], "Failed")
        self.assertEqual(
            [entry[0] for entry in server.transactions],
            ["start", "abort"],
        )

    def test_collision_scan_is_parent_scoped_and_catches_batch_names(self):
        existing_key = "demo/shot?project=demo&code=SHOT010"
        server = _Server([{
            "__search_key__": existing_key,
            "code": "SHOT010",
            "name": "shot_010",
        }])
        with tempfile.TemporaryDirectory() as folder:
            mov_path = Path(folder, "shot_010.mov")
            exr_path = Path(folder, "shot_010.exr")
            new_path = Path(folder, "shot_020.mov")
            for path in (mov_path, exr_path, new_path):
                path.write_bytes(b"fixture")
            options = dict(_RULE_OPTION_DEFAULTS)
            options["extraData"] = {}
            with (
                patch(
                    "thlib.tactic_classes.server_start", return_value=server,
                ),
                patch(
                    "thlib.tactic_classes.execute_procedure_serverside",
                    return_value=server.query_result,
                ) as execute_procedure,
            ):
                result = find_ingest_conflicts({
                    "projectCode": "demo",
                    "searchType": "demo/shot",
                    "parentKey": "demo/episode?code=EP01",
                    "paths": [str(mov_path), str(exr_path), str(new_path)],
                    "options": options,
                })

        procedure, values = execute_procedure.call_args.args[:2]
        self.assertIs(procedure, tq.query_ingest_relation_matches)
        self.assertEqual(values["search_type"], "demo/shot")
        self.assertEqual(values["parent_key"], "demo/episode?code=EP01")
        self.assertEqual(values["column"], "name")
        self.assertEqual(values["names"], ["shot_010", "shot_020"])
        self.assertEqual(
            {row["path"] for row in result["conflicts"]},
            {str(mov_path), str(exr_path)},
        )
        self.assertEqual(
            result["existingByPath"][str(mov_path)], [existing_key]
        )

    def test_skip_conflicts_never_uploads_or_mutates_them(self):
        server = _Server()
        with tempfile.TemporaryDirectory() as folder:
            old_path = Path(folder, "shot_010.mov")
            new_path = Path(folder, "shot_020.mov")
            old_path.write_bytes(b"old")
            new_path.write_bytes(b"new")
            options = dict(_RULE_OPTION_DEFAULTS)
            options["extraData"] = {}
            with (
                patch(
                    "thlib.tactic_classes.server_start",
                    return_value=server,
                ),
                patch("thlib.server_cache.invalidate_domains"),
            ):
                result = IngestFilesController._ingest_batch(
                    {
                        "projectCode": "demo",
                        "searchType": "demo/shot",
                        "parentKey": "demo/episode?code=EP01",
                        "paths": [str(old_path), str(new_path)],
                        "skipPaths": {str(old_path)},
                        "options": options,
                    },
                    threading.Event(),
                )

        self.assertEqual(
            [row["status"] for row in result], ["Skipped", "Completed"]
        )
        self.assertEqual(server.uploads, [str(new_path)])
        self.assertEqual(len(server.commands), 1)

    def test_exact_collision_updates_the_selected_child_and_reports_errors(self):
        server = _Server()
        existing_key = "demo/shot?project=demo&code=SHOT010"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "shot_010.mov")
            path.write_bytes(b"new")
            options = dict(_RULE_OPTION_DEFAULTS)
            options["extraData"] = {}
            with (
                patch(
                    "thlib.tactic_classes.server_start",
                    return_value=server,
                ),
                patch(
                    "thlib.tactic_classes.execute_procedure_serverside",
                    return_value={
                        "accepted": True,
                        "data": {},
                        "snapshot_data": {},
                        "search_key": existing_key,
                    },
                ) as execute_procedure,
                patch("thlib.server_cache.invalidate_domains"),
            ):
                result = IngestFilesController._ingest_batch(
                    {
                        "projectCode": "demo",
                        "searchType": "demo/shot",
                        "parentKey": "demo/episode?code=EP01",
                        "paths": [str(path)],
                        "existingByPath": {str(path): [existing_key]},
                        "options": options,
                    },
                    threading.Event(),
                )

        self.assertEqual(result[0]["status"], "Completed")
        procedure_values = execute_procedure.call_args.args[1]
        self.assertEqual(procedure_values["search_key"], existing_key)
        arguments = server.commands[0][1]
        self.assertEqual(arguments["search_key"], existing_key)
        self.assertEqual(arguments["update_mode"], "true")
        self.assertTrue(arguments["message_key"])

    def test_quick_ingest_waits_for_an_explicit_collision_decision(self):
        application = _Application()
        controller = IngestFilesController(application)
        controller._silent = True
        controller._generation = 4
        controller._busy = True
        job = {"paths": ["shot_010.mov"], "options": {}}
        result = {
            "conflicts": [{
                "path": "shot_010.mov",
                "name": "shot_010",
                "searchKeys": ["demo/shot?code=SHOT010"],
            }],
            "existingByPath": {
                "shot_010.mov": ["demo/shot?code=SHOT010"],
            },
        }
        controller.files.replace([{
            "path": "shot_010.mov",
            "title": "shot_010.mov",
            "extension": "mov",
            "status": "Checking",
            "error": "",
        }])

        with patch.object(controller, "_start_batch") as start_batch:
            controller._preflight._ready(4, job, result)
            self.assertTrue(controller.conflictPending)
            self.assertFalse(controller.busy)
            self.assertEqual(application.window_model.shown, ["ingest_files"])
            start_batch.assert_not_called()
            controller.resolve_ingest_conflict("skip")

        self.assertFalse(controller.conflictPending)
        resolved_job = start_batch.call_args.args[1]
        self.assertEqual(resolved_job["skipPaths"], {"shot_010.mov"})

    def test_ingest_window_qml_creates_with_real_controller(self):
        application = _Application()
        controller = IngestFilesController(application)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        context = engine.rootContext()
        context.setContextProperty("ingestFilesController", controller)
        context.setContextProperty("ingestFileModel", controller.files)
        context.setContextProperty("ingestRuleModel", controller.rules)
        context.setContextProperty("windowModel", application.window_model)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "IngestFilesView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        try:
            self.assertIsNotNone(
                view,
                "\n".join(error.toString() for error in component.errors()),
            )
            view.setProperty("width", 760)
            view.setProperty("height", 560)
            self.app.processEvents()
            files_panel = view.findChild(QObject, "ingestFilesPanel")
            rule_panel = view.findChild(QObject, "ingestRulePanel")
            self.assertIsNotNone(files_panel)
            self.assertIsNotNone(rule_panel)
            self.assertTrue(view.property("wideLayout"))

            view.setProperty("width", 680)
            view.setProperty("height", 760)
            self.app.processEvents()
            self.assertFalse(view.property("wideLayout"))
        finally:
            if view is not None:
                view.deleteLater()
            theme.deleteLater()

    def test_conflict_dialog_cancels_through_a_real_pointer_click(self):
        application = _Application()
        controller = IngestFilesController(application)
        controller._preflight.pending = {
            "generation": 1,
            "job": {"paths": ["shot_010.mov"], "options": {}},
            "conflicts": [{"path": "shot_010.mov"}],
            "existingByPath": {
                "shot_010.mov": ["demo/shot?code=SHOT010"],
            },
            "canUpdate": True,
        }
        controller._generation = 1
        translator = CatalogTranslator(
            QML.parent / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        context = engine.rootContext()
        context.setContextProperty("ingestFilesController", controller)
        context.setContextProperty("ingestFileModel", controller.files)
        context.setContextProperty("ingestRuleModel", controller.rules)
        context.setContextProperty("windowModel", application.window_model)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "IngestFilesView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        window = QQuickWindow()
        try:
            self.assertIsNotNone(
                view,
                "\n".join(error.toString() for error in component.errors()),
            )
            window.setWidth(760)
            window.setHeight(560)
            view.setParentItem(window.contentItem())
            view.setProperty("width", 760)
            view.setProperty("height", 560)
            window.show()
            controller.stateChanged.emit()
            self.app.processEvents()
            dialog = view.findChild(QObject, "ingestConflictDialog")
            button = view.findChild(QObject, "cancelIngestConflictButton")
            self.assertIsNotNone(dialog)
            self.assertIsNotNone(button)
            self.assertTrue(dialog.property("opened"))
            for width in (360, 760):
                window.setWidth(width)
                view.setProperty("width", width)
                self.app.processEvents()
                self.assertLessEqual(dialog.property("width"), width - 24)
                for object_name in (
                    "cancelIngestConflictButton",
                    "duplicateIngestConflictButton",
                    "skipIngestConflictButton",
                    "updateIngestConflictButton",
                ):
                    action = view.findChild(QObject, object_name)
                    top_left = action.mapToScene(QPointF(0, 0))
                    bottom_right = action.mapToScene(QPointF(
                        action.property("width"), action.property("height"),
                    ))
                    self.assertGreaterEqual(top_left.x(), 0)
                    self.assertLessEqual(bottom_right.x(), width)
            scene_point = button.mapToScene(QPointF(
                button.property("width") / 2,
                button.property("height") / 2,
            ))
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                QPoint(round(scene_point.x()), round(scene_point.y())),
            )
            self.app.processEvents()
            self.assertFalse(controller.conflictPending)
        finally:
            window.close()
            if view is not None:
                view.deleteLater()
            theme.deleteLater()
            self.app.removeTranslator(translator)


if __name__ == "__main__":
    unittest.main()
