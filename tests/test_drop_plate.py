import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QObject, QUrl, Signal

from tests.qt_application import gui_test_application
from thlib.ui.drop_plate import DropPlateController
from thlib.ui.checkin_out import CheckinOutController
from thlib.ui.controllers.item_operations import ItemOperationsMixin
from thlib.ui.workspace_models.records import RecordListModel


class _Checkin(QObject):
    stateChanged = Signal()
    actionAvailable = True
    process = "publish"
    context = "publish"
    currentObject = {"title": "Asset", "code": "ASSET001"}

    @staticmethod
    def operation_payload():
        return {
            "searchKey": "skey://project/asset?code=ASSET001",
            "process": "publish",
            "context": "publish",
        }


class _Queue(QObject):
    operationCompleted = Signal(dict)

    def __init__(self):
        super().__init__()
        self.payloads = []

    def add_prepared(self, payload, title):
        self.payloads.append((payload, title))
        return str(len(self.payloads))


class _TriggerRecorder:
    def __init__(self):
        self.calls = []

    def run_before(self, action, context, finished):
        self.calls.append(("before", action, dict(context)))
        finished(True, "")

    def run_after(self, action, context, finished=None):
        self.calls.append(("after", action, dict(context)))
        if finished:
            finished(True, "")


class _Templates(QObject):
    templatesChanged = Signal()

    @staticmethod
    def active_patterns(_process, _context):
        return ["$FILENAME.$EXT"]


class _WindowModel:
    opened = ""

    def show_window(self, window_id):
        self.opened = window_id


class _Application:
    debug_log = None

    def __init__(self):
        self.window_model = _WindowModel()
        self.checkin_refreshes = []

    def refresh_checkin_result(self, payload, snapshot):
        self.checkin_refreshes.append((dict(payload), dict(snapshot)))


class _FileObject:
    @staticmethod
    def get_all_files_list():
        return ["D:/plate/image.png"]

    @staticmethod
    def get_file_ext():
        return "png"

    @staticmethod
    def get_base_file_type():
        return "file"

    @staticmethod
    def get_metadata():
        return {}

    @staticmethod
    def get_name_part():
        return "image"

    @staticmethod
    def get_file_path():
        return "D:/plate/image.png"

    @staticmethod
    def get_file_name(_with_ext):
        return "image.png"


class DropPlateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_handed_items_leave_plate_immediately(self):
        queue = _Queue()
        controller = DropPlateController(
            _Application(), _Checkin(), queue, _Templates()
        )
        controller._group_checkin = False
        controller._objects["group"] = _FileObject()
        controller.model.replace([{
            "groupId": "group",
            "title": "image.png",
            "path": "D:/plate/image.png",
            "fileCount": 1,
            "size": "1 KB",
            "process": "publish",
            "context": "publish",
            "checked": True,
            "status": "Matched",
            "matchingType": "file",
            "sequenceInfo": "",
            "extension": "png",
            "mappedTarget": False,
            "error": "",
        }])

        controller.add_selected_to_queue()

        self.assertEqual(controller.count, 0)
        self.assertNotIn("group", controller._objects)
        self.assertEqual(len(queue.payloads), 1)
        self.assertEqual(
            queue.payloads[0][0]["files"][0]["path"],
            "D:/plate/image.png",
        )

    def test_process_contexts_come_from_pipeline_options(self):
        class Pipeline:
            pipeline = {"model": {}, "texture": {}}

            @staticmethod
            def get_pipeline_process(process):
                return {
                    "process": process,
                    "context_options": "main|secondary",
                    "checkin_mode": "sequence",
                }

        pipeline = Pipeline()
        stype = SimpleNamespace(
            get_pipeline=lambda: {"asset_pipe": pipeline},
            get_workflow=lambda: None,
        )
        source = SimpleNamespace(
            get_stype=lambda: stype,
            get_pipeline_code=lambda: "asset_pipe",
        )
        with patch.object(
            CheckinOutController, "_show_builtin_processes",
            return_value=False,
        ):
            self.assertEqual(
                CheckinOutController._source_processes(source, "model"),
                ["model", "texture"],
            )
        self.assertEqual(
            CheckinOutController._source_contexts(source, "model"),
            ["model/main", "model/secondary"],
        )
        self.assertEqual(
            CheckinOutController._source_checkin_type(source, "model"),
            "sequence",
        )

    def test_sequence_process_payload_disables_versionless(self):
        class Pipeline:
            pipeline = {"model": {}}

            @staticmethod
            def get_pipeline_process(_process):
                return {"checkin_mode": "sequence"}

        pipeline = Pipeline()
        source = SimpleNamespace(
            get_stype=lambda: SimpleNamespace(
                get_pipeline=lambda: {"asset_pipe": pipeline},
                get_workflow=lambda: None,
            ),
            get_pipeline_code=lambda: "asset_pipe",
        )
        controller = CheckinOutController.__new__(CheckinOutController)
        QObject.__init__(controller)
        controller._tabs = [{"searchKey": "project/asset?code=ASSET001"}]
        controller._current_tab = 0
        controller._repository = {
            "value": ["D:/repo", "General", "", "base", True]
        }
        controller._source = source
        controller._process = "model"
        controller._context = "model"
        controller._description = ""
        controller._version = 0
        controller._is_revision = False
        controller._update_versionless = True
        controller._keep_file_name = False
        controller._generate_previews = True
        controller.files = SimpleNamespace(_records=[])

        with patch.object(controller, "_checkin_mode", return_value="upload"):
            result = controller.operation_payload()

        self.assertEqual(result["checkinType"], "sequence")
        self.assertFalse(result["updateVersionless"])

        controller._checkin_type_override = "multi_file"
        controller._transfer_mode_override = "move"
        overridden = controller.operation_payload()
        self.assertEqual(overridden["checkinType"], "multi_file")
        self.assertEqual(overridden["mode"], "move")

    def test_extensionless_file_keeps_empty_transport_extension(self):
        controller = CheckinOutController.__new__(CheckinOutController)
        QObject.__init__(controller)
        controller.files = RecordListModel((
            "name", "path", "size", "extension", "fileType",
            "namingVersioned", "namingVersionless", "error",
        ))
        controller._naming_error = ""
        controller._tabs = [{
            "searchKey": "project/asset?code=ASSET001",
        }]
        controller._current_tab = 0
        controller._repository = {
            "value": ["D:/repo", "General", "", "base", True]
        }
        controller._source = None
        controller._process = "model"
        controller._context = "model"
        controller._description = ""
        controller._version = 0
        controller._is_revision = False
        controller._update_versionless = True
        controller._keep_file_name = False
        controller._generate_previews = False

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "aid_kit_model"
            source.write_bytes(b"model")
            with patch.object(controller, "_schedule_naming"):
                controller.add_files([QUrl.fromLocalFile(str(source))])

        record = controller.files.get(0)
        self.assertEqual(record["extension"], "")
        with patch.object(controller, "_checkin_mode", return_value="upload"):
            payload = controller.operation_payload()
        self.assertEqual(payload["filesDict"][0][1]["e"], [""])
        self.assertEqual(payload["files"][0]["extension"], "")
        self.assertEqual(payload["files"][0]["template"], "$FILENAME")

    def test_finished_checkin_routes_only_live_session_result_to_tree(self):
        def controller_for(payload, queued):
            application = _Application()
            controller = CheckinOutController.__new__(CheckinOutController)
            QObject.__init__(controller)
            controller._application = application
            controller._operation_id = 7
            controller._operation_payload = dict(payload)
            controller._operation_worker = object()
            controller._worker_stages = {"snapshot": object()}
            controller._operation_inputs = {}
            controller._operation_repository = {}
            controller._queue_operation = queued
            return controller, application

        live, live_application = controller_for({
            "searchKey": "demo/asset?code=ASSET001",
            "process": "render",
            "context": "render",
        }, queued=False)
        live._script_triggers = _TriggerRecorder()
        live._checkin_finished(7, {
            "code": "SNAPSHOT002",
            "__search_key__": "sthpw/snapshot?code=SNAPSHOT002",
        })
        self.assertEqual(len(live_application.checkin_refreshes), 1)
        self.assertEqual(
            [
                (phase, action)
                for phase, action, _context
                in live._script_triggers.calls
            ],
            [
                ("after", "snapshot.save"),
            ],
        )

        restored, restored_application = controller_for({
            "searchKey": "demo/asset?code=ASSET001",
            "process": "render",
            "context": "render",
            "_refreshTreeOnComplete": False,
        }, queued=True)
        restored._checkin_finished(7, {
            "code": "SNAPSHOT003",
            "__search_key__": "sthpw/snapshot?code=SNAPSHOT003",
        })
        self.assertEqual(restored_application.checkin_refreshes, [])

    def test_handler_snapshot_save_hook_runs_before_checkin(self):
        controller = CheckinOutController.__new__(CheckinOutController)
        QObject.__init__(controller)
        controller._script_triggers = _TriggerRecorder()
        controller._before_hook_pending = False
        controller._operation_state = "idle"
        payload = {
            "searchKey": "demo/asset?code=ASSET001",
            "projectCode": "demo",
            "process": "model",
            "context": "model/main",
        }

        with patch.object(
            CheckinOutController, "_start_operation_now"
        ) as start:
            controller._start_operation(payload, {"code": "base"}, False)

        self.assertEqual(
            [
                (phase, action)
                for phase, action, _context
                in controller._script_triggers.calls
            ],
            [
                ("before", "snapshot.save"),
            ],
        )
        start.assert_called_once_with(
            controller, payload, {"code": "base"}, False
        )

    def test_item_target_uses_clicked_process(self):
        source = object()
        root = SimpleNamespace(
            node_id="root", node_type="sobject", parent_id="",
            source=source, search_key="project/asset?code=ASSET001",
            title="Asset", code="ASSET001", process="", context="",
        )
        process = SimpleNamespace(
            node_id="process", node_type="process", parent_id="root",
            source=None, search_key=root.search_key, title="Model",
            code="model", process="model", context="",
        )

        class Operations(ItemOperationsMixin):
            _current_project_code = "project"

            @staticmethod
            def _node_for_any(node_id):
                return root if node_id == "root" else None

        target = Operations()._checkin_target_for_node(process)
        self.assertEqual(target["process"], "model")
        self.assertEqual(target["context"], "model")

    def test_selected_snapshot_version_is_used_only_for_a_revision(self):
        class Checkin:
            def __init__(self):
                self.requests = []

            def prepare_workspace_target(self, **request):
                self.requests.append(request)

        class Operations(ItemOperationsMixin):
            def __init__(self):
                self._checkin_controller = Checkin()
                self._drop_plate_controller = object()

        target = {
            "searchKey": "project/asset?code=ASSET001",
            "source": object(),
            "projectCode": "project",
            "title": "Asset",
            "code": "ASSET001",
            "process": "publish",
            "context": "publish",
            "description": "",
            "version": 6,
        }
        operations = Operations()

        operations._prepare_checkin_target(target, save_revision=False)
        operations._prepare_checkin_target(target, save_revision=True)

        self.assertIsNone(
            operations._checkin_controller.requests[0]["snapshot_version"]
        )
        self.assertEqual(
            operations._checkin_controller.requests[1]["snapshot_version"],
            6,
        )

    def test_item_drop_opens_commit_queue_and_queues_immediately(self):
        node = SimpleNamespace(
            node_id="asset", node_type="sobject", process="", context="",
        )

        class Checkin:
            target = None

            def set_process_and_context(self, process, context):
                self.target = (process, context)

        class Plate:
            request = None

            def add_dropped_paths(self, paths, icon_target=False):
                self.request = (list(paths), icon_target)

        class Window:
            opened = ""

            def show_window(self, window_id):
                self.opened = window_id

        class Operations(ItemOperationsMixin):
            def __init__(self):
                self.workspace_model = SimpleNamespace(
                    node_for=lambda _node_id: node
                )
                self._checkin_controller = Checkin()
                self._drop_plate_controller = Plate()
                self.window_model = Window()

            @staticmethod
            def _begin_item_checkin(_node):
                return True

            @staticmethod
            def _notify(_message):
                pass

        operations = Operations()
        path = "D:/plate/preview.png"
        operations.queue_dropped_files(
            "asset", [QUrl.fromLocalFile(path)], "icon"
        )

        self.assertEqual(operations.window_model.opened, "commit_queue")
        self.assertEqual(
            operations._drop_plate_controller.request, ([path], True)
        )
        self.assertEqual(
            operations._checkin_controller.target, ("icon", "icon")
        )

    def test_relation_drop_uses_quiet_child_ingest_without_commit_queue(self):
        node = SimpleNamespace(
            node_id="asset:children:shots",
            node_type="relation",
            process="",
            context="",
        )

        class Ingest:
            request = None

            def quick_ingest(self, node_id, paths):
                self.request = (node_id, list(paths))

        class Operations(ItemOperationsMixin):
            def __init__(self):
                self.workspace_model = SimpleNamespace(
                    node_for=lambda _node_id: node
                )
                self._ingest_controller = Ingest()
                self.opened = []
                self.window_model = SimpleNamespace(
                    show_window=self.opened.append
                )

            @staticmethod
            def _notify(_message):
                pass

        operations = Operations()
        path = "D:/plate/shot_010.mov"
        operations.queue_dropped_files(
            node.node_id, [QUrl.fromLocalFile(path)], "ingest"
        )

        self.assertEqual(
            operations._ingest_controller.request,
            (node.node_id, [path]),
        )
        self.assertEqual(operations.opened, [])

    def test_process_drop_prepares_parent_object_for_clicked_process(self):
        source = object()
        root = SimpleNamespace(
            node_id="asset", node_type="sobject", parent_id="",
            source=source, search_key="project/asset?code=ASSET001",
            title="Asset", code="ASSET001", process="", context="",
        )
        process = SimpleNamespace(
            node_id="asset:process:render", node_type="process",
            parent_id="asset", source=None, search_key=root.search_key,
            title="Render", code="render", process="render", context="",
        )

        class Checkin:
            prepared = None
            target = None

            def prepare_workspace_target(self, **values):
                self.prepared = values

            def set_process_and_context(self, process_name, context):
                self.target = (process_name, context)

        class Plate:
            request = None

            def add_dropped_paths(self, paths, icon_target=False):
                self.request = (list(paths), icon_target)

        class Operations(ItemOperationsMixin):
            _current_project_code = "project"

            def __init__(self):
                nodes = {root.node_id: root, process.node_id: process}
                self.workspace_model = SimpleNamespace(node_for=nodes.get)
                self._checkin_controller = Checkin()
                self._drop_plate_controller = Plate()
                self.window_model = SimpleNamespace(
                    show_window=lambda _window_id: None
                )

            def _node_for_any(self, node_id):
                return self.workspace_model.node_for(node_id)

            @staticmethod
            def _notify(_message):
                pass

        operations = Operations()
        path = "D:/plate/render.mov"
        operations.queue_dropped_files(
            process.node_id, [QUrl.fromLocalFile(path)], "render"
        )

        self.assertIs(operations._checkin_controller.prepared["source"], source)
        self.assertEqual(
            operations._checkin_controller.prepared["process"], "render"
        )
        self.assertEqual(
            operations._checkin_controller.prepared["context"], "render"
        )
        self.assertEqual(
            operations._checkin_controller.target, ("render", "render")
        )
        self.assertEqual(
            operations._drop_plate_controller.request, ([path], False)
        )

    def test_icon_drop_uses_tactic_preview_image_formats(self):
        operations = ItemOperationsMixin()

        self.assertTrue(operations.can_drop_as_icon([
            QUrl.fromLocalFile("D:/plate/preview.JPG"),
            QUrl.fromLocalFile("D:/plate/matte.tif"),
            QUrl.fromLocalFile("D:/plate/alpha.png"),
        ]))
        for path in (
            "D:/plate/scene.ma",
            "D:/plate/render.exr",
            "D:/plate/texture.tga",
            "D:/plate/no_extension",
        ):
            with self.subTest(path=path):
                self.assertFalse(operations.can_drop_as_icon([
                    QUrl.fromLocalFile(path)
                ]))

    def test_unsupported_image_cannot_be_queued_as_object_icon(self):
        node = SimpleNamespace(
            node_id="asset", node_type="sobject", process="", context="",
        )

        class Operations(ItemOperationsMixin):
            def __init__(self):
                self.workspace_model = SimpleNamespace(
                    node_for=lambda _node_id: node
                )
                self.window_model = SimpleNamespace(
                    show_window=lambda _window_id: self.opened.append(
                        _window_id
                    )
                )
                self._drop_plate_controller = SimpleNamespace(
                    add_dropped_paths=lambda *_args, **_kwargs: (
                        self.queued.append((_args, _kwargs))
                    )
                )
                self.opened = []
                self.queued = []
                self.notifications = []

            @staticmethod
            def _begin_item_checkin(_node):
                return True

            def _notify(self, message):
                self.notifications.append(message)

        operations = Operations()
        operations.queue_dropped_files(
            "asset",
            [QUrl.fromLocalFile("D:/plate/render.exr")],
            "icon",
        )

        self.assertEqual(operations.opened, [])
        self.assertEqual(operations.queued, [])
        self.assertIn("JPEG, PNG, or TIFF", operations.notifications[-1])

    def test_sobject_open_uses_cached_publish_snapshot_without_expansion(self):
        main_file = object()
        fallback_file = object()

        class Snapshot:
            def __init__(self, file_object):
                self.file_object = file_object

            def get_files_objects(self, group_by=None):
                self.assert_group = group_by
                return {"main": [self.file_object]}

        class Context:
            def __init__(self, snapshot):
                self.snapshot = snapshot

            def get_versionless(self):
                return {"versionless": self.snapshot}

            @staticmethod
            def get_versions():
                return {}

        class Process:
            def __init__(self, context):
                self.context = context

            def get_contexts(self):
                return {"publish": self.context}

        source = SimpleNamespace(process={
            "model": Process(Context(Snapshot(fallback_file))),
            "publish": Process(Context(Snapshot(main_file))),
        })
        root = SimpleNamespace(
            node_id="asset", node_type="sobject", source=source,
            children=[], process="", parent_id="",
        )

        class Operations(ItemOperationsMixin):
            @staticmethod
            def _node_for_any(node_id):
                return root if node_id == "asset" else None

        self.assertIs(Operations()._file_object_for_node("asset"), main_file)

    def test_sobject_save_and_preview_actions_reach_checkin_workflow(self):
        node = SimpleNamespace(
            node_id="asset", node_type="sobject", source=object(),
        )

        class Checkin:
            def __init__(self):
                self.process = ""
                self.context = ""

            def set_process(self, value):
                self.process = value

            def set_context(self, value):
                self.context = value

        class Dock:
            shown = []

            def show_panel(self, panel):
                self.shown.append(panel)

        class Operations(ItemOperationsMixin):
            def __init__(self):
                self.debug_log = None
                self._checkin_controller = Checkin()
                self.dock_model = Dock()
                self.prepared = []
                self.choose_count = 0

            @staticmethod
            def _node_for_any(node_id):
                return node if node_id == "asset" else None

            @staticmethod
            def _file_object_for_node(_node_id):
                return None

            def _begin_item_checkin(self, selected, save_revision=False):
                self.prepared.append((selected, save_revision))
                return True

            def _queue_drop_plate_or_choose_files(self):
                self.choose_count += 1

        operations = Operations()
        operations.invoke_item_action("save", "asset")
        operations.invoke_item_action("preview", "asset")

        self.assertEqual(operations.prepared, [(node, False), (node, False)])
        self.assertEqual(operations.choose_count, 2)
        self.assertEqual(operations._checkin_controller.process, "icon")
        self.assertEqual(operations._checkin_controller.context, "icon")
        self.assertEqual(operations.dock_model.shown, ["drop_plate"])

    def test_multiple_selected_files_wait_for_per_batch_checkin_choice(self):
        class Requested:
            counts = []

            def emit(self, count):
                self.counts.append(count)

        class Plate:
            requests = []

            def add_paths_and_queue(self, values, group_checkin=None):
                self.requests.append((list(values), group_checkin))

        class Operations(ItemOperationsMixin):
            def __init__(self):
                self._drop_plate_controller = Plate()
                self.multiFileCheckinModeRequested = Requested()
                self._pending_multi_file_checkin = {}

        operations = Operations()
        values = [
            QUrl.fromLocalFile("D:/plate/one.png"),
            QUrl.fromLocalFile("D:/plate/two.png"),
        ]

        operations.submit_checkin_files(values)

        self.assertEqual(
            operations.multiFileCheckinModeRequested.counts, [2]
        )
        self.assertEqual(operations._drop_plate_controller.requests, [])

        operations.resolve_multi_file_checkin("group")
        self.assertEqual(
            operations._drop_plate_controller.requests,
            [(values, True)],
        )

        operations.submit_checkin_files(values)
        operations.resolve_multi_file_checkin("individual")
        self.assertEqual(
            operations._drop_plate_controller.requests[-1],
            (values, False),
        )

        operations.submit_checkin_files(values)
        operations.resolve_multi_file_checkin("cancel")
        self.assertEqual(len(operations._drop_plate_controller.requests), 2)

    def test_separate_file_choice_disables_sequence_matching_for_batch(self):
        class Plate:
            request = None

            def _start_add_paths(self, *args, **kwargs):
                self.request = (args, kwargs)

        plate = Plate()
        values = ["D:/plate/render.0001.exr", "D:/plate/render.0002.exr"]

        DropPlateController.add_paths_and_queue(plate, values, False)

        self.assertEqual(plate.request[0], (values, True))
        self.assertEqual(
            plate.request[1]["patterns"],
            ("$FILENAME.$EXT", "$FILENAME"),
        )
        self.assertFalse(plate.request[1]["queue_options"]["groupCheckin"])

    def test_save_snapshot_prompts_for_checked_drop_plate_groups(self):
        class Requested:
            counts = []

            def emit(self, count):
                self.counts.append(count)

        class Plate:
            hasChecked = True
            checkedCount = 3
            choices = []

            def add_selected_to_queue(self, group_checkin=None):
                self.choices.append(group_checkin)

        class Operations(ItemOperationsMixin):
            def __init__(self):
                self._drop_plate_controller = Plate()
                self.multiFileCheckinModeRequested = Requested()
                self._pending_multi_file_checkin = {}

        operations = Operations()
        operations._queue_drop_plate_or_choose_files()

        self.assertEqual(
            operations.multiFileCheckinModeRequested.counts, [3]
        )
        self.assertEqual(operations._drop_plate_controller.choices, [])

        operations.resolve_multi_file_checkin("individual")
        self.assertEqual(
            operations._drop_plate_controller.choices, [False]
        )

    def test_multiple_item_drop_waits_before_preparing_target(self):
        node = SimpleNamespace(
            node_id="asset:process:render",
            node_type="process",
            process="render",
            context="",
        )

        class Requested:
            counts = []

            def emit(self, count):
                self.counts.append(count)

        class Plate:
            request = None

            def add_dropped_paths(
                self, paths, icon_target=False, group_checkin=False,
            ):
                self.request = (
                    list(paths), icon_target, group_checkin
                )

        class Operations(ItemOperationsMixin):
            def __init__(self):
                self.workspace_model = SimpleNamespace(
                    node_for=lambda _node_id: node
                )
                self._drop_plate_controller = Plate()
                self.multiFileCheckinModeRequested = Requested()
                self._pending_multi_file_checkin = {}
                self._checkin_controller = SimpleNamespace(
                    set_process_and_context=lambda *_args: None
                )
                self.window_model = _WindowModel()
                self.prepared = []

            def _begin_item_checkin(self, selected):
                self.prepared.append(selected)
                return True

            @staticmethod
            def _notify(_message):
                pass

        operations = Operations()
        paths = ["D:/plate/one.mov", "D:/plate/two.mov"]
        operations.queue_dropped_files(
            node.node_id,
            [QUrl.fromLocalFile(path) for path in paths],
            "render",
        )

        self.assertEqual(
            operations.multiFileCheckinModeRequested.counts, [2]
        )
        self.assertEqual(operations.prepared, [])
        self.assertIsNone(operations._drop_plate_controller.request)
        self.assertEqual(operations.window_model.opened, "")

        operations.resolve_multi_file_checkin("group")

        self.assertEqual(operations.prepared, [node])
        self.assertEqual(
            operations._drop_plate_controller.request,
            (paths, False, True),
        )
        self.assertEqual(operations.window_model.opened, "commit_queue")

    def test_per_batch_individual_choice_overrides_group_preference(self):
        class File(_FileObject):
            def __init__(self, path):
                self.path = path

            def get_all_files_list(self):
                return [self.path]

            def get_file_path(self):
                return self.path

            def get_file_name(self, _with_ext):
                return self.path.rsplit("/", 1)[-1]

        queue = _Queue()
        controller = DropPlateController(
            _Application(), _Checkin(), queue, _Templates()
        )
        controller._group_checkin = True
        records = []
        for group_id, filename in (("one", "one.png"), ("two", "two.png")):
            path = f"D:/plate/{filename}"
            controller._objects[group_id] = File(path)
            records.append({
                "groupId": group_id, "title": filename, "path": path,
                "fileCount": 1, "size": "1 KB", "process": "",
                "context": "", "checked": True, "status": "Matched",
                "matchingType": "file", "sequenceInfo": "",
                "extension": "png", "mappedTarget": False, "error": "",
            })
        controller.model.replace(records)

        controller._add_group_ids_to_queue(["one", "two"], {
            "description": "Drag-Drop Checkin",
            "groupCheckin": False,
            "updateVersionless": False,
        })

        self.assertEqual(len(queue.payloads), 2)
        self.assertEqual(controller.count, 0)
        for payload, _title in queue.payloads:
            self.assertEqual(payload["description"], "Drag-Drop Checkin")
            self.assertFalse(payload["updateVersionless"])

    def test_per_batch_group_choice_overrides_individual_preference(self):
        class File(_FileObject):
            def __init__(self, path):
                self.path = path

            def get_all_files_list(self):
                return [self.path]

            def get_file_path(self):
                return self.path

            def get_file_name(self, _with_ext):
                return self.path.rsplit("/", 1)[-1]

        queue = _Queue()
        controller = DropPlateController(
            _Application(), _Checkin(), queue, _Templates()
        )
        controller._group_checkin = False
        records = []
        for group_id, filename in (("one", "one.png"), ("two", "two.png")):
            path = f"D:/plate/{filename}"
            controller._objects[group_id] = File(path)
            records.append({
                "groupId": group_id, "title": filename, "path": path,
                "fileCount": 1, "size": "1 KB", "process": "",
                "context": "", "checked": True, "status": "Matched",
                "matchingType": "file", "sequenceInfo": "",
                "extension": "png", "mappedTarget": False, "error": "",
            })
        controller.model.replace(records)

        controller._add_group_ids_to_queue(
            ["one", "two"], {"groupCheckin": True}
        )

        self.assertEqual(len(queue.payloads), 1)
        self.assertEqual(
            [entry["path"] for entry in queue.payloads[0][0]["files"]],
            ["D:/plate/one.png", "D:/plate/two.png"],
        )
        self.assertEqual(controller.count, 0)


if __name__ == "__main__":
    unittest.main()
