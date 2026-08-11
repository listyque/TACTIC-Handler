import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QObject, QUrl, Signal

from modern_ui.drop_plate import DropPlateController
from modern_ui.checkin_out import CheckinOutController
from modern_ui.controllers.item_operations import ItemOperationsMixin


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
        cls.app = QCoreApplication.instance() or QCoreApplication([])

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

    def test_item_drop_forces_individual_queue_operations(self):
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
            "forceIndividual": True,
            "updateVersionless": False,
        })

        self.assertEqual(len(queue.payloads), 2)
        self.assertEqual(controller.count, 0)
        for payload, _title in queue.payloads:
            self.assertEqual(payload["description"], "Drag-Drop Checkin")
            self.assertFalse(payload["updateVersionless"])


if __name__ == "__main__":
    unittest.main()
