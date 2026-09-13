from __future__ import annotations

from collections import OrderedDict
import os
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QObject, QPoint, QPointF, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from thlib.ui.sobject_link import (
    LinkObjectModel,
    SObjectLinkController,
    configured_instance_relation,
)
from tests.support.async_scenarios import SignalStub


class _Project:
    def __init__(self, code="demo"):
        self._code = code

    def get_code(self):
        return self._code


class _Schema:
    def __init__(self, path="assets_in_episode"):
        self.path = path
        self.calls = []

    def get_parent_instance(self, instance_type, target_code):
        self.calls.append((instance_type, target_code))
        return {"path": self.path}


class _Stype:
    def __init__(self, code, project="demo", schema=None, title=None):
        self._code = code
        self._project = _Project(project)
        self._schema = schema or _Schema()
        self._title = title or code
        self.info = {"title": self._title}

    def get_code(self):
        return self._code

    def get_project(self):
        return self._project

    def get_schema(self):
        return self._schema

    def get_pretty_name(self):
        return self._title

    def get_stype_color(self, fmt=None):
        assert fmt == "hex"
        return "#445566"

    def get_columns_info(self):
        return {
            "name": {},
            "keywords": {},
            "code": {},
            "description": {},
        }


class _SObject:
    def __init__(self, code, stype=None, title=None):
        self.code = code
        self._stype = stype
        self._title = title or code
        self.related_calls = []

    def get_search_key(self):
        return "skey://demo/item?code={}".format(self.code)

    def get_title(self):
        return self._title

    def get_code(self):
        return self.code

    def get_stype(self):
        return self._stype

    def get_info(self):
        return {"code": self.code, "name": self._title}

    def get_all_processes(self):
        return {}

    def get_related_sobjects(self, **kwargs):
        self.related_calls.append(dict(kwargs))
        return []


class _DescribedSObject(_SObject):
    def get_info(self):
        return {
            "code": self.code,
            "name": self._title,
            "description": (
                "A deliberately long object description\nthat must stay "
                "inside the list row and never enter the drag preview."
            ),
            "status": "Approved",
        }


def _context(*, relationship="instance", instance_type="asset_in_episode",
             target_project="demo", path="assets_in_episode"):
    schema = _Schema(path)
    target = _Stype("demo/asset", target_project, schema, "Assets")
    parent_stype = _Stype("demo/episode", "demo", _Schema(), "Episodes")
    parent = _SObject("EPISODE001", parent_stype, "Episode 1")
    return {
        "stype": target,
        "parent_sobject": parent,
        "project_code": "demo",
        "relation": {
            "relationship": relationship,
            "instance_type": instance_type,
        },
    }, schema, parent


def _ready_controller(initial=(), available=()):
    context, _schema, _parent = _context()
    controller = SObjectLinkController(lambda: context)
    controller._reset()
    controller._context_data = controller._validated_context(context)
    controller._linked = OrderedDict(
        (item.get_search_key(), item) for item in initial
    )
    controller._initial_keys = set(controller._linked)
    controller._available = OrderedDict(
        (item.get_search_key(), item) for item in available
    )
    controller._sync_models()
    return controller


class LinkObjectModelTests(unittest.TestCase):
    def test_role_and_extended_selection_contract(self):
        model = LinkObjectModel()
        model.replace([
            {"searchKey": "A", "title": "A", "selected": False},
            {"searchKey": "B", "title": "B", "selected": False},
            {"searchKey": "C", "title": "C", "selected": False},
        ])

        self.assertEqual(model.roleNames()[model.SearchKeyRole], b"searchKey")
        self.assertEqual(model.roleNames()[model.PreviewUrlRole], b"previewUrl")
        self.assertEqual(model.roleNames()[model.SelectedRole], b"selected")
        self.assertTrue(model.toggle(0, additive=False))
        self.assertTrue(model.toggle(2, additive=True))
        self.assertEqual(model.selected_keys(), ["A", "C"])
        self.assertEqual(model.selected_count, 2)
        model.clear_selection()
        self.assertEqual(model.selected_keys(), [])

    def test_shift_selects_range_and_append_preserves_selection(self):
        model = LinkObjectModel()
        records = [
            {"searchKey": key, "title": key, "selected": False}
            for key in ("A", "B", "C", "D")
        ]
        model.replace(records[:3])

        self.assertTrue(model.select(0, 0))
        self.assertTrue(model.select(2, Qt.ShiftModifier.value))
        self.assertEqual(model.selected_keys(), ["A", "B", "C"])

        model.replace(records)
        self.assertEqual(model.selected_keys(), ["A", "B", "C"])



class SObjectLinkControllerTests(unittest.TestCase):
    def test_record_does_not_repeat_code_when_object_has_title(self):
        candidate = _DescribedSObject("ASSET001", title="Excavator")
        controller = _ready_controller([], [candidate])

        record = controller._record(candidate)

        self.assertEqual(record["title"], "Excavator")
        self.assertIn("deliberately long", record["subtitle"])
        self.assertIn("Approved", record["subtitle"])
        self.assertNotIn("ASSET001", record["subtitle"])
        self.assertIn("\n", record["subtitle"])

    def test_worker_results_update_models_on_the_ui_thread(self):
        app = QGuiApplication.instance() or QGuiApplication([])
        controller = _ready_controller()
        candidate = _SObject("A")
        handled = []
        main_thread = QThread.currentThread()

        class ThreadWorker(QObject):
            result = Signal(object)
            error = Signal(object)

            def __init__(self, operation):
                super().__init__()
                self.operation = operation
                self.thread = None

            def start(self):
                def run():
                    try:
                        self.result.emit(self.operation())
                    except Exception as error:
                        self.error.emit(error)

                self.thread = threading.Thread(target=run)
                self.thread.start()
                self.thread.join()

        class ThreadPool:
            is_stopped = False

            def add_task(self, operation):
                return ThreadWorker(operation)

        from thlib.environment import env_inst

        def handle(result):
            controller._available[result.get_search_key()] = result
            controller._sync_models()
            handled.append((result, QThread.currentThread()))

        with patch.object(env_inst, "server_pool", ThreadPool()):
            controller._start_worker(
                lambda: candidate,
                handle,
            )

        self.assertEqual(handled, [])
        for _pass in range(10):
            app.processEvents()
            if handled:
                break
        self.assertEqual(handled[0][0], candidate)
        self.assertEqual(handled[0][1], main_thread)
        self.assertEqual(controller.available_model.count, 1)

    def test_session_exposes_explicit_target_and_parent_identity(self):
        context, _schema, _parent = _context()
        controller = SObjectLinkController(lambda: context)

        with patch.object(controller, "_load_linked"), patch.object(
            controller, "_load_available"
        ):
            controller.begin_session()

        self.assertEqual(controller.target_title, "Assets")
        self.assertEqual(controller.target_code, "demo/asset")
        self.assertEqual(controller.parent_title, "Episode 1")
        self.assertEqual(controller.parent_code, "EPISODE001")
        self.assertEqual(controller.parent_type_title, "Episodes")

    def test_instance_relation_without_reverse_schema_path_is_linkable(self):
        class MissingInstanceSchema:
            @staticmethod
            def get_parent_instance(_instance_type, _target_code):
                return None

        stype = _Stype("demo/asset", schema=MissingInstanceSchema())
        relation = {
            "relationship": "instance",
            "instance_type": "asset_in_episode",
        }

        self.assertEqual(
            configured_instance_relation(relation, stype),
            {"instance_type": "asset_in_episode", "path": None},
        )

        context, _schema, _parent = _context()
        context["stype"] = stype
        validated = SObjectLinkController._validated_context(context)

        self.assertEqual(validated["instance_type"], "asset_in_episode")
        self.assertIsNone(validated["path"])

    def test_validation_accepts_only_configured_instance_relation_and_derives_path(self):
        context, schema, _parent = _context(path="episode_assets")

        validated = SObjectLinkController._validated_context(context)

        self.assertEqual(schema.calls, [("asset_in_episode", "demo/asset")])
        self.assertEqual(validated["path"], "episode_assets")
        self.assertEqual(validated["instance_type"], "asset_in_episode")
        self.assertEqual(validated["parent_key"],
                         "skey://demo/item?code=EPISODE001")
        self.assertEqual(validated["search_type"], "demo/asset")
        self.assertIs(validated["parent_stype"], context["parent_sobject"].get_stype())

        bad_relationship, _schema, _parent = _context(relationship="search")
        with self.assertRaisesRegex(ValueError, "instance relations only"):
            SObjectLinkController._validated_context(bad_relationship)

        missing_type, _schema, _parent = _context(instance_type="")
        with self.assertRaisesRegex(ValueError, "no instance type"):
            SObjectLinkController._validated_context(missing_type)

        wrong_project, _schema, _parent = _context(target_project="other")
        with self.assertRaisesRegex(ValueError, "another project"):
            SObjectLinkController._validated_context(wrong_project)

    def test_linked_load_uses_native_related_sobjects_contract(self):
        context, _schema, parent = _context()
        controller = SObjectLinkController(lambda: context)
        controller._reset()
        controller._context_data = controller._validated_context(context)

        def run_immediately(operation, result_handler, failure_handler=None):
            result_handler(operation())

        with patch.object(controller, "_start_worker", side_effect=run_immediately):
            controller._load_linked()

        self.assertEqual(parent.related_calls, [{
            "child_stype": context["stype"],
            "parent_stype": parent.get_stype(),
            "path": "child",
            "get_all_snapshots": False,
        }])

    def test_multi_add_then_multi_remove_back_cancels_staged_delta(self):
        linked = _SObject("A")
        candidate_b = _SObject("B")
        candidate_c = _SObject("C")
        controller = _ready_controller([linked], [candidate_b, candidate_c])

        controller.select_available(0, False)
        controller.select_available(1, True)
        self.assertEqual(controller.selected_count, 2)
        controller.transfer_selected()

        self.assertEqual(set(controller._linked), {
            linked.get_search_key(), candidate_b.get_search_key(),
            candidate_c.get_search_key(),
        })
        self.assertTrue(controller.dirty)

        controller.select_linked(1, False)
        controller.select_linked(2, True)
        self.assertEqual(controller.transfer_direction, "remove")
        self.assertEqual(controller.selected_count, 2)
        controller.transfer_selected()

        self.assertEqual(list(controller._linked), [linked.get_search_key()])
        self.assertFalse(controller.dirty)

    def test_save_computes_deterministic_delta_and_calls_native_mutation_once(self):
        initial_a = _SObject("A")
        retained_b = _SObject("B")
        inserted_c = _SObject("C")
        controller = _ready_controller([initial_a, retained_b], [inserted_c])
        controller._remove_keys([initial_a.get_search_key()])
        controller._add_keys([inserted_c.get_search_key()])
        self.assertTrue(controller.dirty)
        native_result = Mock()

        def run_immediately(operation, result_handler, failure_handler=None):
            result_handler(operation())

        with patch("thlib.tactic_classes.edit_multiple_instance_sobjects",
                   return_value=native_result) as mutate:
            with patch.object(controller, "_start_worker",
                              side_effect=run_immediately):
                controller.save()

        mutate.assert_called_once_with(
            "demo",
            insert_search_keys=[inserted_c.get_search_key()],
            exclude_search_keys=[initial_a.get_search_key()],
            parent_key="skey://demo/item?code=EPISODE001",
            instance_type="asset_in_episode",
            path="assets_in_episode",
        )
        self.assertFalse(controller.dirty)
        self.assertFalse(controller.busy)
        self.assertEqual(controller._initial_keys, set(controller._linked))

    def test_available_results_are_paged_and_never_duplicate_linked_objects(self):
        linked_a = _SObject("A")
        candidate_b = _SObject("B")
        candidate_c = _SObject("C")
        candidate_d = _SObject("D")
        candidate_e = _SObject("E")
        controller = _ready_controller([linked_a], [])
        session = controller._session_token
        model_resets = Mock()
        rows_inserted = Mock()
        controller.available_model.modelReset.connect(model_resets)
        controller.available_model.rowsInserted.connect(rows_inserted)

        controller._loading_available = True
        controller._available_loaded(
            session, 1, "", 0, False,
            ([linked_a, candidate_b], {"total_sobjects_count": 5}),
        )
        self.assertEqual(list(controller._available), [candidate_b.get_search_key()])
        self.assertEqual(controller._available_offset, 2)
        self.assertEqual(controller.available_total, 5)
        self.assertTrue(controller.can_load_more)
        self.assertEqual(model_resets.call_count, 1)

        controller._loading_available = True
        controller._available_loaded(
            session, 2, "", 2, True,
            ([candidate_c, candidate_d], {"total_sobjects_query_count": 5}),
        )
        self.assertEqual(list(controller._available), [
            candidate_b.get_search_key(), candidate_c.get_search_key(),
            candidate_d.get_search_key(),
        ])
        self.assertEqual(controller._available_offset, 4)
        self.assertTrue(controller.can_load_more)
        self.assertEqual(model_resets.call_count, 1)

        controller._loading_available = True
        controller._available_loaded(
            session, 3, "", 4, True,
            ([candidate_e], {"total_sobjects_count": 5}),
        )
        self.assertEqual(controller._available_offset, 5)
        self.assertFalse(controller.can_load_more)
        self.assertEqual(controller.available_model.count, 4)
        self.assertEqual(model_resets.call_count, 1)
        self.assertEqual(rows_inserted.call_count, 2)

    def test_stale_result_is_ignored_and_server_failure_keeps_staged_state(self):
        linked_a = _SObject("A")
        candidate_b = _SObject("B")
        controller = _ready_controller([linked_a], [candidate_b])
        controller._add_keys([candidate_b.get_search_key()])
        before = list(controller._linked)
        self.assertTrue(controller.dirty)

        controller._available_loaded(
            "stale-session", 99, "", 0, False,
            ([_SObject("STALE")], {"total_sobjects_count": 1}),
        )
        self.assertEqual(list(controller._linked), before)

        controller._busy = True
        controller._save_failed(
            controller._session_token,
            ({"exception": "TACTIC unavailable"},),
        )
        self.assertEqual(list(controller._linked), before)
        self.assertTrue(controller.dirty)
        self.assertFalse(controller.busy)
        self.assertEqual(controller.error, "TACTIC unavailable")

    def test_failed_available_request_still_runs_latest_queued_search(self):
        controller = _ready_controller([], [])
        controller._loading_available = True
        controller._available_query = "older"
        controller._pending_available_query = "latest"

        with patch.object(controller, "_load_available") as load:
            controller._available_failed(
                controller._session_token,
                1,
                ({"exception": "temporary failure"},),
            )

        self.assertEqual(controller._available_query, "latest")
        self.assertIsNone(controller._pending_available_query)
        load.assert_called_once_with(0, append=False)


    def test_available_search_populates_shared_suggestion_model(self):
        controller = _ready_controller([], [])

        class Worker:
            def __init__(self, operation):
                self.operation = operation
                self.result = SignalStub()
                self.error = SignalStub()
                self.settled = SignalStub()
                self.metadata = None

            def add_result_data(self, metadata):
                self.metadata = metadata

            def cancel(self):
                pass

            def start(self):
                result = self.operation()
                self.result.emit(result + (self.metadata,))
                self.settled.emit(self)

        workers = []
        pool = SimpleNamespace(is_stopped=False)

        def add_task(operation):
            worker = Worker(operation)
            workers.append(worker)
            return worker

        pool.add_task = add_task
        from thlib.environment import env_inst

        records = [{
            "name": "Asset One",
            "code": "ASSET001",
            "description": "Suggested asset",
            "keywords": "hero",
        }]
        with patch.object(env_inst, "server_pool", pool), patch(
            "thlib.tactic_classes.server_query",
            return_value=records,
        ):
            controller.available_search.request_search_suggestions("asset")

        self.assertEqual(len(workers), 1)
        self.assertEqual(controller.available_search.suggestions.count(), 1)
        self.assertEqual(
            controller.available_search.suggestions.get(0)["title"],
            "Asset One",
        )

    def test_drop_transfer_deduplicates_search_keys(self):
        candidate = _SObject("A")
        key = candidate.get_search_key()
        controller = _ready_controller([], [candidate])

        controller.add_keys([key, key])
        controller.add_keys([key])

        self.assertEqual(list(controller._linked), [key])
        self.assertEqual(list(controller._available), [])
        self.assertTrue(controller.dirty)

    def test_drop_transfer_works_while_next_available_page_loads(self):
        candidate = _SObject("A")
        key = candidate.get_search_key()
        controller = _ready_controller([], [candidate])
        controller._loading_available = True
        controller._busy = True

        controller.add_keys([key])

        self.assertEqual(list(controller._linked), [key])
        self.assertEqual(list(controller._available), [])
        next_candidate = _SObject("B")
        controller._available_loaded(
            controller._session_token,
            1,
            "",
            1,
            True,
            ([candidate, next_candidate], {"total_sobjects_count": 2}),
        )
        self.assertEqual(list(controller._linked), [key])
        self.assertEqual(
            list(controller._available), [next_candidate.get_search_key()]
        )


class LinkSObjectsQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    @staticmethod
    def _visual_children(item, object_name):
        children = [item]
        matches = []
        for child in children:
            children.extend(child.childItems())
            if child.objectName() == object_name:
                matches.append(child)
        return matches

    def test_link_list_scrollbar_drag_keeps_delegate_geometry_dense(self):
        candidates = [
            _SObject(f"ITEM{index:03d}", title=f"Asset {index:03d}")
            for index in range(80)
        ]
        controller = _ready_controller([], candidates)
        controller._available_total = len(candidates)
        engine = QQmlEngine()
        qml_dir = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"
        engine.rootContext().setContextProperty(
            "linkAvailableModel", controller.available_model
        )
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    width: 440
    height: 540
    visible: true
    Theme { id: theme; dark: true }
    Item { id: dragPreview }
    LinkList {
        objectName: "linkListTest"
        anchors.fill: parent
        theme: theme
        title: "Available"
        emptyText: "Empty"
        sourceModel: linkAvailableModel
        totalCount: 120
        canLoadMore: true
        dragPreview: dragPreview
        dropDirection: "remove"
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_LinkListScrollTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            object_list = window.findChild(
                QQuickItem, "linkObjectList-remove"
            )
            scroll_bar = window.findChild(
                QQuickItem, "linkObjectScrollBar-remove"
            )
            link_list = window.findChild(QObject, "linkListTest")
            self.assertIsNotNone(object_list)
            self.assertIsNotNone(scroll_bar)
            self.assertIsNotNone(link_list)
            self.assertGreater(object_list.property("contentHeight"), 5000)
            pagination_requests = []
            link_list.loadMoreRequested.connect(
                lambda: pagination_requests.append(True)
            )
            object_list.scrollWithWheel(0, -120)
            QTest.qWait(10)
            self.assertTrue(object_list.property("interactionMoving"))

            start = scroll_bar.mapToScene(QPointF(
                scroll_bar.width() / 2,
                max(4, scroll_bar.height() * 0.06),
            ))
            finish = scroll_bar.mapToScene(QPointF(
                scroll_bar.width() / 2, scroll_bar.height() * 0.92
            ))
            QTest.mousePress(
                window, Qt.LeftButton, Qt.NoModifier,
                QPoint(round(start.x()), round(start.y())),
            )
            QTest.qWait(5)
            self.assertFalse(object_list.property("interactionMoving"))
            for step in range(1, 9):
                ratio = step / 8.0
                QTest.mouseMove(window, QPoint(
                    round(start.x() + (finish.x() - start.x()) * ratio),
                    round(start.y() + (finish.y() - start.y()) * ratio),
                ), delay=8)
                self.app.processEvents()
            self.assertTrue(scroll_bar.property("paginationBlocked"))
            QTest.mouseRelease(
                window, Qt.LeftButton, Qt.NoModifier,
                QPoint(round(finish.x()), round(finish.y())),
            )
            QTest.qWait(80)

            self.assertGreater(object_list.property("contentY"), 4000)
            self.assertEqual(pagination_requests, [])
            content_y = float(object_list.property("contentY"))
            additions = [
                controller._record(_SObject(
                    f"ITEM{index:03d}", title=f"Asset {index:03d}"
                ))
                for index in range(80, 100)
            ]
            controller.available_model.append(additions)
            QTest.qWait(50)
            self.assertAlmostEqual(
                float(object_list.property("contentY")), content_y, delta=1.0
            )
            rows = self._visual_children(object_list, "linkRow-remove")
            visible_rows = sorted(
                (
                    (float(row.mapToItem(
                        object_list, QPointF(0, 0)
                    ).y()), row)
                    for row in rows
                    if row.property("visible")
                    and -64 <= float(row.mapToItem(
                        object_list, QPointF(0, 0)
                    ).y()) <= float(object_list.height())
                ),
                key=lambda entry: entry[0],
            )
            self.assertGreaterEqual(len(visible_rows), 6)
            for previous, current in zip(visible_rows, visible_rows[1:]):
                self.assertAlmostEqual(
                    current[0] - previous[0],
                    68.0,
                    delta=1.0,
                )

            object_list.scrollWithWheel(0, -12000)
            QTest.qWait(10)
            self.assertTrue(
                scroll_bar.property("paginationArmed"),
                (
                    object_list.property("interactionMoving"),
                    object_list.property("contentY"),
                    object_list.property("contentHeight"),
                ),
            )
            QTest.qWait(170)
            self.assertEqual(pagination_requests, [True])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()

    def test_link_panels_render_and_center_button_transfers_selection(self):
        candidate = _DescribedSObject("ASSET001", title="Excavator")
        controller = _ready_controller([], [candidate])
        preview_url = (
            "data:image/svg+xml;base64,"
            "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdp"
            "ZHRoPSI4IiBoZWlnaHQ9IjgiPjxyZWN0IHdpZHRoPSI4IiBoZWlnaHQ9"
            "IjgiIGZpbGw9IiNmZjAwMDAiLz48L3N2Zz4="
        )
        controller.available_model._records[0]["previewUrl"] = preview_url

        class WindowModel(QObject):
            @Slot(str)
            def close_window(self, _window_id):
                pass

        window_model = WindowModel()
        engine = QQmlEngine()
        qml_dir = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"
        engine.rootContext().setContextProperty(
            "sobjectLinkController", controller
        )
        engine.rootContext().setContextProperty(
            "linkAvailableModel", controller.available_model
        )
        engine.rootContext().setContextProperty(
            "linkCurrentModel", controller.linked_model
        )
        engine.rootContext().setContextProperty("windowModel", window_model)
        component = QQmlComponent(engine)
        component.setData(
            b'''import QtQuick
import QtQuick.Window
Window {
    width: 820
    height: 620
    visible: true
    Theme { id: theme; dark: true }
    LinkSObjectsView {
        anchors.fill: parent
        theme: theme
    }
}
''',
            QUrl.fromLocalFile(str(qml_dir / "_LinkSObjectsRuntimeTest.qml")),
        )
        window = component.create()
        self.assertIsNotNone(
            window,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            for _pass in range(8):
                self.app.processEvents()
            available_pane = window.findChild(QObject, "availableLinkPane")
            linked_pane = window.findChild(QObject, "linkedLinkPane")
            transfer = window.findChild(QQuickItem, "linkTransferButton")
            available_search = window.findChild(
                QQuickItem, "availableLinkSearch"
            )
            self.assertIsNotNone(available_pane)
            self.assertIsNotNone(linked_pane)
            self.assertIsNotNone(transfer)
            self.assertGreater(available_pane.property("radius"), 0)
            self.assertIsNotNone(available_search)
            search_input = available_search.findChild(
                QQuickItem, "tacticSearchInput"
            )
            self.assertIsNotNone(search_input)
            search_input.forceActiveFocus()
            controller.available_search.suggestions.replace([{
                "title": "Asset suggestion",
                "description": "Suggested result",
                "keyword": "asset",
                "code": "ASSET001",
                "values": {"name": "Asset suggestion"},
                "selected": False,
            }])
            for _pass in range(4):
                self.app.processEvents()
            self.assertTrue(available_search.property("popupOpen"))
            controller.available_search.clear_search_suggestions()
            self.assertGreater(linked_pane.property("radius"), 0)
            self.assertAlmostEqual(
                available_pane.property("width"),
                linked_pane.property("width"),
                delta=2.0,
            )

            def center(item):
                point = item.mapToScene(QPointF(
                    item.property("width") / 2,
                    item.property("height") / 2,
                ))
                return QPoint(round(point.x()), round(point.y()))

            def visual_child(item, object_name):
                children = [item]
                for child in children:
                    children.extend(child.childItems())
                    if child.objectName() == object_name:
                        return child
                return None

            def drag(source, target):
                start = center(source)
                finish = center(target)
                QTest.mousePress(
                    window, Qt.LeftButton, Qt.NoModifier, start
                )
                for step in range(1, 9):
                    ratio = step / 8.0
                    point = QPoint(
                        round(start.x() + (finish.x() - start.x()) * ratio),
                        round(start.y() + (finish.y() - start.y()) * ratio),
                    )
                    QTest.mouseMove(window, point, delay=8)
                QTest.mouseRelease(
                    window, Qt.LeftButton, Qt.NoModifier, finish
                )
                for _pass in range(4):
                    self.app.processEvents()

            linked_drop = window.findChild(
                QQuickItem, "linkDropArea-add"
            )
            available_list = window.findChild(
                QQuickItem, "linkObjectList-remove"
            )
            available_row = visual_child(available_list, "linkRow-remove")
            self.assertIsNotNone(available_row)
            self.assertIsNotNone(linked_drop)

            drag_preview = window.findChild(
                QQuickItem, "linkDragPreview"
            )
            row_preview = visual_child(
                available_row, "linkRowPreview-remove"
            )
            row_subtitle = visual_child(
                available_row, "linkRowSubtitle-remove"
            )
            self.assertIsNotNone(drag_preview)
            self.assertIsNotNone(row_preview)
            self.assertIsNotNone(row_subtitle)
            self.assertEqual(row_subtitle.property("maximumLineCount"), 1)
            self.assertNotIn("\n", row_subtitle.property("text"))
            row_source_image = row_preview.findChild(
                QQuickItem, "previewSourceImage"
            )
            row_mask = row_preview.findChild(
                QQuickItem, "previewMaskLoader"
            )
            self.assertIsNotNone(row_source_image)
            self.assertIsNotNone(row_mask)
            for _pass in range(10):
                self.app.processEvents()
                if row_mask.property("opacity") >= 0.99:
                    break
                QTest.qWait(5)
            self.assertGreaterEqual(row_mask.property("opacity"), 0.99)
            start = center(available_row)
            QTest.mousePress(
                window, Qt.LeftButton, Qt.NoModifier, start
            )
            for step in range(1, 7):
                QTest.mouseMove(
                    window,
                    QPoint(start.x() + step * 12, start.y()),
                    delay=12,
                )
            self.app.processEvents()
            self.assertTrue(drag_preview.property("visible"))
            self.assertTrue(drag_preview.property("clip"))
            self.assertLessEqual(drag_preview.property("width"), 276)
            self.assertLessEqual(drag_preview.property("height"), 58)
            self.assertEqual(available_row.property("opacity"), 1.0)
            drag_title = drag_preview.findChild(
                QQuickItem, "linkDragTitle"
            )
            drag_details = drag_preview.findChild(
                QQuickItem, "linkDragDetails"
            )
            drag_item_preview = drag_preview.findChild(
                QQuickItem, "linkDragItemPreview"
            )
            self.assertEqual(drag_title.property("text"), "Excavator")
            self.assertEqual(drag_details.property("text"), "")
            self.assertFalse(drag_details.property("visible"))
            self.assertEqual(
                drag_item_preview.property("source").toString(), preview_url
            )
            drag_mask = drag_item_preview.findChild(
                QQuickItem, "previewMaskLoader"
            )
            for _pass in range(10):
                self.app.processEvents()
                if drag_mask.property("opacity") >= 0.99:
                    break
                QTest.qWait(5)
            self.assertGreaterEqual(row_mask.property("opacity"), 0.99)
            self.assertGreaterEqual(drag_mask.property("opacity"), 0.99)
            QTest.mouseRelease(
                window, Qt.LeftButton, Qt.NoModifier,
                QPoint(start.x() + 72, start.y())
            )
            self.app.processEvents()
            drag(available_row, linked_drop)
            self.assertEqual(
                list(controller._linked), [candidate.get_search_key()]
            )

            linked_list = window.findChild(
                QQuickItem, "linkObjectList-add"
            )
            linked_row = visual_child(linked_list, "linkRow-add")
            available_drop = window.findChild(
                QQuickItem, "linkDropArea-remove"
            )
            self.assertIsNotNone(linked_row)
            self.assertIsNotNone(available_drop)
            drag(linked_row, available_drop)
            self.assertEqual(list(controller._linked), [])

            controller.select_available(0, 0)
            self.app.processEvents()
            self.assertEqual(controller.selected_count, 1)
            self.assertTrue(transfer.property("enabled"))

            QTest.mouseClick(
                window, Qt.LeftButton, Qt.NoModifier, center(transfer)
            )
            self.app.processEvents()
            self.assertEqual(
                list(controller._linked), [candidate.get_search_key()]
            )
            self.assertEqual(list(controller._available), [])
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()

    def test_shared_search_continuous_loading_and_drag_contracts(self):
        qml_dir = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"
        view = (qml_dir / "LinkSObjectsView.qml").read_text(
            encoding="utf-8"
        )
        link_list = (qml_dir / "LinkList.qml").read_text(encoding="utf-8")
        item_surface = (qml_dir / "controls" / "ItemSurface.qml").read_text(
            encoding="utf-8"
        )

        self.assertEqual(view.count("TacticSearchField {"), 2)
        self.assertNotIn("Controls.TextField {", view)
        self.assertNotIn("DragHandler {", link_list)
        self.assertIn(
            "Drag.active: sourcePointer ? sourcePointer.drag.active : false",
            view,
        )
        self.assertIn("drag.target: root.dragPreview", link_list)
        self.assertIn("DropArea {", link_list)
        self.assertIn("onContentYChanged:", link_list)
        self.assertNotIn('qsTr("Load more")', link_list)
        self.assertNotIn("SplitView {", view)
        self.assertIn('objectName: "linkTransferButton"', view)
        self.assertIn('objectName: "availableLinkPane"', view)
        self.assertIn('objectName: "linkedLinkPane"', view)
        self.assertIn('qsTr("Parent object")', view)
        self.assertIn("sobjectLinkController.parent_type_title", view)
        self.assertIn("sobjectLinkController.parent_code", view)
        self.assertIn("Drag.dragType: Drag.Internal", view)
        self.assertIn(
            "Drag.supportedActions: Qt.MoveAction", view
        )
        self.assertIn("Drag.proposedAction: Qt.MoveAction", view)
        self.assertIn("anchors.rightMargin: 10", link_list)
        self.assertIn(
            "property color selectedColor: theme.contentSelection",
            item_surface,
        )


if __name__ == "__main__":
    unittest.main()
