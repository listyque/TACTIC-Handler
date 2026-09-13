from __future__ import annotations

import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, QPointF, Property, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from thlib.ui.process_filter_editor import ProcessFilterEditorController
from thlib.ui.workspace import RecordListModel


class _Pipeline:
    def __init__(self, code, processes):
        self.info = {"code": code, "name": code.title()}
        self.pipeline = processes

    def get_process_info(self, code):
        return self.pipeline.get(code) or {}

    def get_process_label(self, code):
        return code.title()


class _Schema:
    children = [{"from": "demo/shot"}]


class _SType:
    def __init__(self, code, pipelines, project=None):
        self.info = {"code": code, "title": code.split("/")[-1].title()}
        self.pipeline = pipelines
        self.schema = _Schema()
        self._project = project

    def get_project(self):
        return self._project


class _Project:
    def __init__(self):
        self.stypes = {}


class ProcessFilterEditorControllerTests(unittest.TestCase):
    def make_controller(self):
        project = _Project()
        child = _SType(
            "demo/shot",
            {"shot": _Pipeline("shot", {"animation": {"type": "manual"}})},
            project,
        )
        stype = _SType(
            "demo/asset",
            {"asset": _Pipeline("asset", {"model": {"type": "manual"}})},
            project,
        )
        project.stypes = {"demo/shot": child, "demo/asset": stype}
        context = {
            "project": project,
            "project_code": "demo",
            "project_type": "prod",
            "search_type": "demo/asset",
            "tab_name": "demo/asset@assets",
            "stype": stype,
        }
        applied = []
        controller = ProcessFilterEditorController(
            lambda: context, applied.append, lambda _message: None
        )
        return controller, applied

    @patch("thlib.environment.env_read_config", return_value={})
    def test_legacy_tree_contains_children_pipelines_processes_and_builtins(
        self, _read
    ):
        controller, _applied = self.make_controller()

        controller.begin_session()

        kinds = [record["kind"] for record in controller.model._records]
        self.assertIn("child", kinds)
        self.assertIn("pipeline", kinds)
        self.assertIn("process", kinds)
        self.assertEqual(kinds.count("builtin"), 9)
        self.assertEqual(kinds, [
            "builtin", "builtin", "builtin",
            "pipeline", "process", "child",
            "builtin", "builtin", "builtin",
            "pipeline", "process", "child",
            "builtin", "builtin", "builtin",
            "pipeline", "process",
        ])
        self.assertTrue(all(
            record["dataKey"].endswith((":{b}", ":{pp}", ":{pr}", ":{s}"))
            for record in controller.model._records
        ))

    @patch("thlib.environment.env_read_config", return_value={})
    def test_shift_expansion_changes_the_complete_branch(self, _read):
        controller, _applied = self.make_controller()
        controller.begin_session()
        child_row = next(
            index for index, record in enumerate(controller.model._records)
            if record["kind"] == "child"
        )

        controller.toggle_expanded(child_row, True)

        child_id = controller.model._records[child_row]["nodeId"]
        self.assertFalse(controller.model._records[child_row]["expanded"])
        self.assertTrue(all(
            not record["rowVisible"]
            for record in controller.model._records
            if record["parentId"] == child_id
        ))

    @patch("thlib.environment.env_read_config", return_value={})
    def test_loaded_project_resolves_stype_during_tab_bootstrap(self, _read):
        controller, _applied = self.make_controller()
        context = dict(controller._context())
        context["stype"] = None
        controller._context = lambda: context

        controller.begin_session()

        self.assertTrue(controller.valid_context)
        self.assertTrue(controller.model._records)
        self.assertEqual(
            controller.model._records[0]["dataKey"], "publish:{b}"
        )

    @patch("thlib.environment.env_write_config")
    @patch("thlib.environment.env_read_config", return_value={})
    def test_save_writes_legacy_process_ignore_contract(
        self, _read, write
    ):
        controller, applied = self.make_controller()
        controller.begin_session()
        model_row = next(
            index for index, record in enumerate(controller.model._records)
            if record["kind"] == "process" and record["key"] == "model"
        )
        controller.set_checked(model_row, False)

        self.assertTrue(controller.save())

        ignore = write.call_args.args[0]
        self.assertEqual(ignore["processes"]["asset"], ["model"])
        self.assertEqual(applied[-1], ignore)
        self.assertIn(
            "ui_search/checkin_out/prod/demo/demo/asset@assets",
            write.call_args.kwargs["unique_id"],
        )


class _EditorStub(QObject):
    @Property(str, constant=True)
    def context_title(self):
        return "Assets"

    @Property(bool, constant=True)
    def valid_context(self):
        return True

    @Property(bool, constant=True)
    def dirty(self):
        return False


class _WindowModelStub(QObject):
    pass


class ProcessFilterEditorQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_compact_window_instantiates_with_dense_runtime_geometry(self):
        from pathlib import Path

        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine = QQmlEngine()
        controller = _EditorStub()
        window_model = _WindowModelStub()
        model = RecordListModel((
            "nodeId", "parentId", "dataKey", "key", "title", "subtitle",
            "kind", "group", "depth", "checkable", "checked",
            "expanded", "rowVisible", "selected", "accent",
            "hasChildren",
        ))
        model.reset_records([
            {
                "nodeId": "pipeline:asset", "parentId": "",
                "dataKey": "asset:{pp}", "key": "asset",
                "title": "Asset", "subtitle": "Pipeline",
                "kind": "pipeline", "group": "asset", "depth": 0,
                "checkable": False, "checked": True, "expanded": True,
                "rowVisible": True, "selected": False, "accent": "",
                "hasChildren": True,
            },
            {
                "nodeId": "pipeline:asset:process:model",
                "parentId": "pipeline:asset", "dataKey": "model:{pr}",
                "key": "model", "title": "Model",
                "subtitle": "Process", "kind": "process",
                "group": "asset", "depth": 1, "checkable": True,
                "checked": True, "expanded": True, "rowVisible": True,
                "selected": False, "accent": "#5c9bd5",
                "hasChildren": False,
            },
        ])
        engine.rootContext().setContextProperty(
            "processFilterEditorController", controller
        )
        engine.rootContext().setContextProperty("processFilterModel", model)
        engine.rootContext().setContextProperty("windowModel", window_model)

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "ProcessFilterEditorView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme, "windowId": "process_filter_editor",
        })
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.setWidth(440)
        window.setHeight(360)
        view.setParentItem(window.contentItem())
        view.setWidth(440)
        view.setHeight(360)
        window.show()
        QTest.qWait(30)

        header = view.findChild(QObject, "processFilterHeader")
        tree = view.findChild(QObject, "processFilterTree")
        footer = view.findChild(QObject, "processFilterFooter")

        def visual_child(item, object_name):
            if not isinstance(item, QQuickItem):
                return None
            for child in item.childItems():
                if child.objectName() == object_name:
                    return child
                found = visual_child(child, object_name)
                if found is not None:
                    return found
            return None

        row = None
        for _attempt in range(10):
            row = visual_child(tree, "processFilterRow")
            if row is not None:
                break
            QTest.qWait(20)
        self.assertEqual(header.property("height"), 42.0)
        self.assertGreaterEqual(tree.property("height"), 150.0)
        self.assertEqual(footer.property("height"), 48.0)
        self.assertIsNotNone(
            row,
            "tree count={}, model rows={}".format(
                tree.property("count"), model.rowCount()
            ),
        )
        self.assertEqual(row.property("height"), 30.0)
        process_icon = visual_child(
            tree, "processSelectionIcon_process"
        )
        pipeline_title = visual_child(
            tree, "processSelectionTitle_pipeline"
        )
        process_title = visual_child(
            tree, "processSelectionTitle_process"
        )
        self.assertIsNotNone(process_icon)
        self.assertTrue(process_icon.property("forceSolid"))
        self.assertIsNotNone(pipeline_title)
        self.assertIsNotNone(process_title)
        pipeline_x = pipeline_title.mapToScene(QPointF()).x()
        process_x = process_title.mapToScene(QPointF()).x()
        self.assertGreaterEqual(pipeline_x, 48.0)
        self.assertGreaterEqual(process_x - pipeline_x, 18.0)

        window.close()
        window.deleteLater()
        view.deleteLater()
        theme.deleteLater()


if __name__ == "__main__":
    unittest.main()
