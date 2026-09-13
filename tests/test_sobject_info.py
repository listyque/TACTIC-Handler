import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal

from thlib.ui.sobject_info import SObjectInfoController
from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.workspace_models.state import WorkspaceState


class FakeRepositorySync(QObject):
    task_finished = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.scheduled = []

    def schedule_file_object(self, file_object, **kwargs):
        self.scheduled.append((file_object, kwargs))


class FakeWorkspaceModel:
    @staticmethod
    def preview_url_for_search_key(_search_key):
        return "file:///object-preview.png"

    @staticmethod
    def _root_preview(_sobject):
        return ""

    @staticmethod
    def _snapshot_preview(_snapshot):
        return "file:///snapshot-preview.png"

    @staticmethod
    def _preview_url(file_object):
        return "file:///" + file_object.get_filename_with_ext()


class FakeApplication(QObject):
    def __init__(self):
        super().__init__()
        self.workspace_state = WorkspaceState()
        self.workspace_model = FakeWorkspaceModel()
        self.repository_sync = FakeRepositorySync()
        self.opened = []
        self.opened_files = []

    def open_search_key(self, search_key):
        self.opened.append(search_key)

    def open_file_object(self, file_object):
        self.opened_files.append(file_object)


class FakeUsers:
    def __init__(self):
        self.users = RecordListModel((
            "login", "displayName", "initials", "avatarUrl",
        ))
        self.users.replace([
            {
                "login": "artist", "displayName": "Ada Artist",
                "initials": "AA", "avatarUrl": "file:///ada.png",
            },
            {
                "login": "reviewer", "displayName": "Ray Reviewer",
                "initials": "RR", "avatarUrl": "",
            },
        ])
        self.opened = []

    def open_profile(self, login):
        self.opened.append(login)


class FakeTaskPipeline:
    pipeline = {"Approved": {"color": "#21a366"}}


class FakeWorkflow:
    @staticmethod
    def get_by_pipeline_code(_search_type, _pipeline_code):
        return FakeTaskPipeline()


class FakePipeline:
    @staticmethod
    def get_process_info(process):
        return {"label": process.title(), "color": "#4ea5d9"}

    @staticmethod
    def get_pipeline_process(_process):
        return {"color": "#4ea5d9"}


class FakeSType:
    @staticmethod
    def get_pretty_name():
        return "Assets"

    @staticmethod
    def get_stype_color(fmt="hex"):
        return "#ef5350"

    @staticmethod
    def get_pipeline():
        return {"asset": FakePipeline()}

    @staticmethod
    def get_workflow():
        return FakeWorkflow()


class FakeProject:
    @staticmethod
    def get_title():
        return "Demo Project"

    @staticmethod
    def get_code():
        return "demo"


class FakeRecord:
    def __init__(self, search_key, **info):
        self._search_key = search_key
        self._info = dict(info)

    def get_info(self):
        return dict(self._info)

    def get_search_key(self):
        return self._search_key

    def get_notes_count(self):
        return dict(self._info.get("__notes_count__") or {})

    def get_status_log(self):
        return list(self._info.get("__status_logs__") or [])


class FakeFile(FakeRecord):
    def __init__(self, filename, file_type="main", size=1024, exists=True):
        super().__init__(f"skey://sthpw/file?code={filename}")
        self.filename = filename
        self.file_type = file_type
        self.size = size
        self.exists = exists

    def get_type(self):
        return self.file_type

    def get_file_size(self):
        return self.size

    def get_filename_with_ext(self):
        return self.filename

    def get_ext(self):
        return self.filename.rsplit(".", 1)[-1]

    def get_full_abs_path(self):
        return "D:/repo/" + self.filename

    def is_exists(self):
        return self.exists

    def get_web_preview(self):
        return None

    def get_icon_preview(self):
        return None


class FakeSnapshot:
    def __init__(self, code, version, login, files, versionless=False):
        self.code = code
        self.version = version
        self.login = login
        self.files = files
        self.versionless = versionless

    def get_code(self):
        return self.code

    def get_search_key(self):
        return f"skey://sthpw/snapshot?code={self.code}"

    def get_version(self):
        return self.version

    def is_versionless(self):
        return self.versionless

    def is_latest(self):
        return not self.versionless

    def get_files_objects(self):
        return list(self.files)

    def get_snapshot(self):
        return {
            "context": "model/main", "login": self.login,
            "timestamp": "2026-08-10 12:00:00", "repo": "base",
        }


class FakeContext:
    def __init__(self, versions, versionless):
        self.versions = versions
        self.versionless = versionless

    def get_versions(self):
        return {item.code: item for item in self.versions}

    def get_versionless(self):
        return {item.code: item for item in self.versionless}


class FakeProcess:
    def __init__(self, context):
        self.context = context

    def get_contexts(self):
        return {"model/main": self.context}


class FakeSObject(FakeRecord):
    def __init__(self, process):
        super().__init__(
            "skey://demo/assets?code=ASSET0001",
            code="ASSET0001", name="Hero", pipeline_code="asset",
            description="Presentation asset", category="character",
            __search_type__="demo/assets",
        )
        self.process = process
        self.server_task_reads = 0

    def get_title(self):
        return "Hero"

    def get_code(self):
        return "ASSET0001"

    def get_stype(self):
        return FakeSType()

    def get_project(self):
        return FakeProject()

    def get_pipeline_code(self):
        return "asset"

    def get_all_processes(self):
        return {"model": self.process}

    def get_tasks_sobjects(self, **_kwargs):
        self.server_task_reads += 1
        return []


class FakeWindowModel:
    def __init__(self, visible=False):
        self.visible = visible

    def is_window_visible(self, window_id):
        return window_id == "sobject_info" and self.visible


class CountingSObject(FakeSObject):
    def __init__(self, process):
        super().__init__(process)
        self.info_reads = 0

    def get_info(self):
        self.info_reads += 1
        return super().get_info()


class SObjectInfoControllerTests(unittest.TestCase):
    def test_projection_restore_does_not_build_intermediate_report(self):
        sobject = CountingSObject(FakeProcess(FakeContext([], [])))
        application = FakeApplication()
        application.window_model = FakeWindowModel(visible=True)
        application.workspace_state._selected_sobject = sobject
        controller = SObjectInfoController(application)
        reads_before_restore = sobject.info_reads
        application.workspace_state._selection_projection_restoring = True

        controller._rebuild()

        self.assertEqual(sobject.info_reads, reads_before_restore)
        self.assertTrue(controller._projection_dirty)

    def test_hidden_report_does_not_rebuild_on_workspace_selection(self):
        sobject = CountingSObject(FakeProcess(FakeContext([], [])))
        application = FakeApplication()
        application.window_model = FakeWindowModel(visible=False)
        application.workspace_state._selected_sobject = sobject

        controller = SObjectInfoController(application)

        self.assertEqual(sobject.info_reads, 0)
        self.assertTrue(controller._projection_dirty)

        application.window_model.visible = True
        controller._rebuild()

        self.assertGreater(sobject.info_reads, 0)
        self.assertFalse(controller._projection_dirty)

    def test_activate_file_uses_shared_download_and_open_operation(self):
        application = FakeApplication()
        controller = SObjectInfoController(application)
        file_object = FakeFile("scene.ma", exists=False)
        controller._file_objects["scene-token"] = file_object

        controller.activate_file("scene-token")

        self.assertEqual(application.opened_files, [file_object])
        self.assertEqual(application.repository_sync.scheduled, [])

    def test_refresh_requests_activity_scoped_to_selected_object(self):
        from thlib.environment import env_inst

        class PendingWorker(QObject):
            result = Signal(object)
            error = Signal(object)

            def __init__(self, operation):
                super().__init__()
                self.operation = operation

            def start(self):
                pass

        class Pool:
            is_stopped = False

            def __init__(self):
                self.worker = None

            def add_task(self, operation):
                self.worker = PendingWorker(operation)
                return self.worker

        sobject = FakeSObject(FakeProcess(FakeContext([], [])))
        sobject.update_snapshots = lambda **_kwargs: None
        application = FakeApplication()
        application.workspace_state._selected_sobject = sobject
        controller = SObjectInfoController(application)
        pool = Pool()
        activity_records = [{
            "eventId": "audit:one",
            "kind": "change",
            "targetSearchKey": sobject.get_search_key(),
        }]

        with patch.object(env_inst, "server_pool", pool), patch.object(
            SObjectInfoController,
            "_query_related_children",
            return_value=[],
        ), patch(
            "thlib.tactic_classes.get_sobjects", return_value=[]
        ), patch(
            "thlib.tactic_classes.query_work_hours", return_value={}
        ), patch(
            "thlib.tactic_classes.get_user_recent_activity",
            return_value=activity_records,
        ) as activity_query:
            controller.refresh()
            result = pool.worker.operation()

        self.assertEqual(result["activity"], activity_records)
        activity_query.assert_called_once()
        kwargs = activity_query.call_args.kwargs
        self.assertEqual(kwargs["object_scope"]["searchType"], "demo/assets")
        self.assertEqual(kwargs["object_scope"]["searchCode"], "ASSET0001")
        self.assertEqual(kwargs["object_scope"]["taskCodes"], [])
        self.assertEqual(kwargs["object_scope"]["noteCodes"], [])
        self.assertEqual(kwargs["object_scope"]["snapshotCodes"], [])
        self.assertEqual(kwargs["object_scope"]["workHourCodes"], [])
        self.assertEqual(
            kwargs["object_scope"]["indexedObjects"],
            [{
                "searchType": "demo/assets",
                "searchCode": "ASSET0001",
                "searchId": "",
            }],
        )
        self.assertEqual(kwargs["limit"], 51)
        self.assertEqual(kwargs["offset"], 0)
        self.assertIn("task", kwargs["kinds"])
        self.assertIn("delete", kwargs["kinds"])

    def test_activity_load_more_uses_raw_offset_and_appends_unique_page(self):
        from thlib.environment import env_inst

        class PendingWorker(QObject):
            result = Signal(object)
            error = Signal(object)

            def __init__(self, operation):
                super().__init__()
                self.operation = operation

            def start(self):
                pass

        class Pool:
            is_stopped = False

            def __init__(self):
                self.worker = None

            def add_task(self, operation):
                self.worker = PendingWorker(operation)
                return self.worker

        sobject = FakeSObject(FakeProcess(FakeContext([], [])))
        application = FakeApplication()
        application.workspace_state._selected_sobject = sobject
        controller = SObjectInfoController(application)
        controller._refreshed_tasks = []
        controller._refreshed_notes = []
        controller._refreshed_children = []
        controller._refreshed_work_hours = {}
        controller._refreshed_activity = [{
            "eventId": "event-{0}".format(index),
            "kind": "change",
            "timestamp": "2026-08-25 12:{0:02d}:00".format(index),
            "targetSearchKey": sobject.get_search_key(),
            "targetTitle": "Hero",
            "targetType": "demo/assets",
        } for index in range(50)]
        controller._activity_offset = 50
        controller._activity_has_more = True
        pool = Pool()
        next_page = [{
            "eventId": "event-50",
            "kind": "change",
            "timestamp": "2026-08-24 12:00:00",
            "targetSearchKey": sobject.get_search_key(),
            "targetTitle": "Hero",
            "targetType": "demo/assets",
        }, {
            "eventId": "event-51",
            "kind": "delete",
            "timestamp": "2026-08-23 12:00:00",
            "targetSearchKey": sobject.get_search_key(),
            "targetTitle": "Hero",
            "targetType": "demo/assets",
        }]

        with patch.object(env_inst, "server_pool", pool), patch(
            "thlib.tactic_classes.get_user_recent_activity",
            return_value=next_page,
        ) as activity_query:
            controller.load_more_activity()
            self.assertTrue(controller.activityLoadingMore)
            request_id = controller._activity_request_id
            result = pool.worker.operation()
            controller._activity_page_ready(request_id, 50, result)

        kwargs = activity_query.call_args.kwargs
        self.assertEqual(kwargs["offset"], 50)
        self.assertEqual(kwargs["limit"], 51)
        controller.set_page(4)
        self.assertEqual(controller.activity.count(), 52)
        self.assertEqual(controller._activity_offset, 52)
        self.assertFalse(controller.activityHasMore)
        self.assertFalse(controller.activityLoadingMore)

    def test_summary_uses_shared_friendly_updated_date(self):
        sobject = FakeSObject(FakeProcess(FakeContext([], [])))
        sobject._info["last_updated"] = "2026-08-10 12:00:00"
        application = FakeApplication()
        application.workspace_state._selected_sobject = sobject

        with patch(
            "thlib.ui.sobject_info.activity_timestamp_labels",
            return_value=("2 wk ago", "10 August 2026, 12:00:00"),
        ):
            controller = SObjectInfoController(application)

        self.assertEqual(controller.summary["updatedPretty"], "2 wk ago")
        self.assertEqual(
            controller.summary["updatedFull"],
            "10 August 2026, 12:00:00",
        )

    def test_cached_native_objects_build_full_report_without_server_reads(self):
        main_file = FakeFile("hero.ma", size=2048)
        web_file = FakeFile("hero_web.jpg", file_type="web", size=400)
        version = FakeSnapshot("SNAP001", 3, "artist", [main_file, web_file])
        current = FakeSnapshot(
            "SNAP002", -1, "artist", [main_file], versionless=True
        )
        sobject = FakeSObject(FakeProcess(FakeContext([version], [current])))
        status_log = FakeRecord(
            "skey://sthpw/status_log?code=STATUS001",
            from_status="In Progress", to_status="Approved", login="reviewer",
            timestamp="2026-08-11 09:30:00",
        )
        task = FakeRecord(
            "skey://sthpw/task?code=TASK001", process="model",
            status="Approved", assigned="artist", pipeline_code="task",
            timestamp="2026-08-11 10:00:00", progress=100,
            __status_logs__=[status_log],
        )
        note = FakeRecord(
            "skey://sthpw/note?code=NOTE001", process="model",
            login="reviewer", note="Looks good",
            timestamp="2026-08-11 11:00:00",
        )
        application = FakeApplication()
        users = FakeUsers()
        application.workspace_state._selected_sobject = sobject
        application.workspace_state._task_sobjects = [task]
        application.workspace_state._note_sobjects = [note]

        controller = SObjectInfoController(application, users=users)

        self.assertEqual(controller.summary["title"], "Hero")
        self.assertEqual(controller.summary["previewUrl"], "file:///object-preview.png")
        self.assertEqual(controller.metrics["tasks"], 1)
        self.assertEqual(controller.metrics["notes"], 1)
        self.assertEqual(controller.metrics["snapshots"], 2)
        self.assertEqual(controller.metrics["files"], 2)
        self.assertEqual(controller.metrics["participants"], 2)
        self.assertEqual(controller.metrics["latestVersion"], "v003")
        self.assertEqual(controller.snapshot_processes.count(), 0)
        controller._file_metadata = controller._inspect_files([main_file, web_file])
        controller.set_page(3)
        self.assertEqual(controller.snapshot_processes.count(), 1)
        snapshot_branch = controller.snapshot_processes.get(0)
        self.assertEqual(len(snapshot_branch["snapshots"]), 2)
        self.assertEqual(len(snapshot_branch["files"]), 2)
        self.assertTrue(snapshot_branch["snapshots"][0]["timestampPretty"])
        self.assertTrue(snapshot_branch["snapshots"][0]["timestampFull"])
        self.assertEqual(
            [record["modelIndex"] for record in snapshot_branch["snapshots"]],
            [0, 1],
        )
        self.assertEqual(controller.metrics["completedTasks"], 1)
        self.assertEqual(controller.metrics["activeTasks"], 0)
        self.assertEqual(sobject.server_task_reads, 0)
        self.assertEqual(controller.tasks.count(), 1)
        self.assertEqual(controller.task_statuses.get(0)["accent"], "#21a366")
        self.assertEqual(controller.task_statuses.get(0)["label"], "Approved")
        self.assertEqual(controller.task_statuses.get(0)["count"], 1)
        self.assertEqual(controller.task_processes.get(0)["label"], "Model")
        self.assertEqual(controller.task_processes.get(0)["count"], 1)
        self.assertEqual(controller.files.get(0)["path"], "D:/repo/hero.ma")
        controller.set_page(1)
        self.assertTrue(controller.notes.get(0)["timestampPretty"])
        self.assertTrue(controller.notes.get(0)["timestampFull"])
        self.assertEqual(controller.participants.get(0)["displayName"], "Ada Artist")
        controller.set_page(4)
        self.assertGreaterEqual(controller.activity.count(), 4)
        activity_kinds = {
            controller.activity.get(row)["kind"]
            for row in range(controller.activity.count())
        }
        self.assertIn("status", activity_kinds)
        self.assertNotIn("task", activity_kinds)
        for row in range(controller.activity.count()):
            activity = controller.activity.get(row)
            self.assertEqual(activity["targetTitle"], "Hero")
            self.assertEqual(
                activity["targetSearchKey"],
                "skey://demo/assets?code=ASSET0001",
            )
        activity_by_actor = {
            controller.activity.get(row)["actor"]: controller.activity.get(row)
            for row in range(controller.activity.count())
        }
        self.assertEqual(activity_by_actor["artist"]["actorLabel"], "Ada Artist")
        self.assertEqual(
            activity_by_actor["artist"]["actorAvatar"], "file:///ada.png"
        )
        self.assertEqual(activity_by_actor["reviewer"]["actorInitials"], "RR")

    def test_task_activity_and_filters_keep_the_project_object_scope(self):
        class Tasks:
            def __init__(self):
                self.contexts = []
                self.filters = []

            def open_object_context(self, *values):
                self.contexts.append(values)

            def open_object_filter(self, *values):
                self.filters.append(values)

        class Navigation:
            def __init__(self):
                self.contexts = []

            def open_in_context(self, *values):
                self.contexts.append(values)

        tasks = Tasks()
        navigation = Navigation()
        application = FakeApplication()
        controller = SObjectInfoController(
            application, tasks=tasks, navigation=navigation
        )
        root_key = "skey://demo/assets?code=ASSET0001"
        controller._summary = {"searchKey": root_key}
        controller.activity.replace([{
            "searchKey": "skey://sthpw/status_log?code=STATUS001",
            "targetSearchKey": root_key, "targetTitle": "Hero",
            "targetType": "demo/assets", "kind": "status",
            "title": "Approved", "detail": "Model", "actor": "reviewer",
            "timestamp": "2026-08-20", "project": "demo",
            "process": "model", "context": "", "version": "",
            "canOpen": True, "taskCode": "TASK001",
        }, {
            "searchKey": "skey://sthpw/note?code=NOTE001",
            "targetSearchKey": root_key, "targetTitle": "Hero",
            "targetType": "demo/assets", "kind": "note",
            "title": "Added note", "detail": "Review", "actor": "reviewer",
            "timestamp": "2026-08-20", "project": "demo",
            "process": "model", "context": "", "version": "",
            "canOpen": True, "taskCode": "TASK001",
        }])

        controller.open_task("TASK001", "model")
        controller.open_tasks_filter("status", "Approved")
        controller.open_activity(0)
        controller.open_activity(1)

        self.assertEqual(tasks.contexts[0], (root_key, "TASK001", "model"))
        self.assertEqual(tasks.contexts[1], (root_key, "TASK001", "model"))
        self.assertEqual(len(tasks.contexts), 2)
        self.assertEqual(tasks.filters, [(root_key, "status", "Approved")])
        self.assertEqual(
            navigation.contexts,
            [(
                "skey://sthpw/note?code=NOTE001", root_key, "model",
                "TASK001",
            )],
        )
        self.assertEqual(application.opened, [])

    def test_note_row_navigation_keeps_task_and_process_context(self):
        class Navigation:
            def __init__(self):
                self.contexts = []

            def open_in_context(self, *values):
                self.contexts.append(values)

        navigation = Navigation()
        controller = SObjectInfoController(
            FakeApplication(), navigation=navigation
        )
        root_key = "skey://demo/assets?code=ASSET0001"
        note_key = "skey://sthpw/note?code=NOTE001"
        controller._summary = {"searchKey": root_key}
        controller.notes.replace([{
            "searchKey": note_key,
            "process": "model",
            "taskCode": "TASK001",
        }])

        controller.open_note(0)

        self.assertEqual(
            navigation.contexts,
            [(note_key, root_key, "model", "TASK001")],
        )

    def test_server_activity_replaces_partial_local_projection(self):
        class Tasks:
            def __init__(self):
                self.contexts = []

            def open_object_context(self, *values):
                self.contexts.append(values)

        sobject = FakeSObject(FakeProcess(FakeContext([], [])))
        application = FakeApplication()
        application.workspace_state._selected_sobject = sobject
        tasks = Tasks()
        controller = SObjectInfoController(
            application, users=FakeUsers(), tasks=tasks
        )
        controller._refreshed_tasks = []
        controller._refreshed_notes = []
        controller._refreshed_children = []
        controller._refreshed_work_hours = {}
        controller._refreshed_activity = [{
            "eventId": "audit:child:create",
            "kind": "create",
            "actor": "artist",
            "timestamp": "2026-08-25 16:00:00",
            "searchKey": "skey://demo/shot?code=SHOT001",
            "targetSearchKey": sobject.get_search_key(),
            "targetTitle": "Hero",
            "targetType": "demo/assets",
            "itemCode": "SHOT001",
            "itemTitle": "Shot 001",
            "itemType": "demo/shot",
        }, {
            "eventId": "audit:task:update",
            "kind": "change",
            "actor": "reviewer",
            "timestamp": "2026-08-25 15:00:00",
            "targetSearchKey": sobject.get_search_key(),
            "targetTitle": "Hero",
            "targetType": "demo/assets",
            "itemCode": "TASK001",
            "itemTitle": "model",
            "itemType": "sthpw/task",
            "taskCode": "TASK001",
            "process": "model",
            "changes": [{
                "field": "assigned", "before": "artist",
                "after": "reviewer",
            }],
        }, {
            "eventId": "work:one",
            "kind": "work_hour",
            "actor": "artist",
            "timestamp": "2026-08-25 14:00:00",
            "targetSearchKey": sobject.get_search_key(),
            "targetTitle": "Hero",
            "targetType": "demo/assets",
            "taskCode": "TASK001",
            "process": "model",
            "hours": 2.5,
            "workDay": "2026-08-25 00:00:00",
            "workHourAction": "create",
            "workHourCategory": "regular",
            "workHourStatus": "approved",
            "workHourOwner": "artist",
        }]

        controller._rebuild()

        controller.set_page(4)
        self.assertEqual(controller.activity.count(), 3)
        child_event = controller.activity.get(0)
        self.assertEqual(child_event["itemTitle"], "Shot 001")
        self.assertEqual(child_event["actorLabel"], "Ada Artist")
        work_event = controller.activity.get(2)
        self.assertEqual(work_event["hours"], 2.5)
        self.assertTrue(work_event["workDayPretty"])

        controller.open_activity(0)
        controller.open_activity(1)
        controller.open_activity(2)

        self.assertEqual(
            application.opened,
            ["skey://demo/shot?code=SHOT001"],
        )
        self.assertEqual(tasks.contexts, [
            (sobject.get_search_key(), "TASK001", "model"),
            (sobject.get_search_key(), "TASK001", "model"),
        ])

    def test_activity_scope_describes_direct_and_instance_children(self):
        class Schema:
            @staticmethod
            def get_children():
                return [{
                    "from": "demo/shot",
                    "to": "demo/assets",
                    "relationship": "code",
                }, {
                    "from": "demo/texture",
                    "to": "demo/assets",
                    "relationship": "instance",
                    "instance_type": "demo/texture_in_assets",
                }]

            @staticmethod
            def get_parents():
                return []

        class SType(FakeSType):
            @staticmethod
            def get_schema():
                return Schema()

        sobject = FakeSObject(FakeProcess(FakeContext([], [])))
        sobject._info["id"] = 17
        sobject.get_stype = lambda: SType()

        scope, relations = SObjectInfoController._activity_scope(sobject)

        self.assertEqual(scope, {
            "searchType": "demo/assets",
            "searchCode": "ASSET0001",
            "searchId": "17",
            "childTypes": ["demo/shot", "demo/texture"],
        })
        self.assertEqual(relations, {
            "demo/texture_in_assets": ["demo/texture", "demo/assets"],
        })

    def test_qml_uses_report_models_and_safe_task_snapshot_entrypoints(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "thlib" / "ui" / "qml" / "SObjectInfoView.qml"
        ).read_text(encoding="utf-8")
        snapshot_tree_source = (
            Path(__file__).resolve().parents[1]
            / "thlib" / "ui" / "qml" / "SObjectSnapshotTree.qml"
        ).read_text(encoding="utf-8")
        activity_card_source = (
            Path(__file__).resolve().parents[1]
            / "thlib" / "ui" / "qml" / "ActivityEventCard.qml"
        ).read_text(encoding="utf-8")

        self.assertIn("model: sobjectNoteModel", source)
        self.assertIn("model: sobjectChildModel", source)
        self.assertIn("snapshotProcessModel: sobjectSnapshotProcessModel", source)
        self.assertIn("model: root.snapshotProcessModel", snapshot_tree_source)
        self.assertIn("id: snapshotProcessRepeater", snapshot_tree_source)
        self.assertIn(
            "visible: snapshotProcessRepeater.count === 0",
            snapshot_tree_source,
        )
        self.assertIn("property bool expanded: false", snapshot_tree_source)
        self.assertNotIn("headerCollapsed", source)
        self.assertNotIn("component ReportPageScroll: Flickable", source)
        self.assertIn("component ReportPageHost: Item", source)
        self.assertIn("flickableTarget: reportScroll", source)
        self.assertIn("Math.max(0, reportPages.width)", source)
        self.assertIn('objectName: "sobjectInfoReportScroll"', source)
        self.assertIn(
            'objectName: "sobjectInfoPresentationHeader"', source
        )
        self.assertIn("Controls.SegmentedButton", source)
        self.assertIn("model: root.reportSections", source)
        self.assertIn('"icon": "task"', source)
        self.assertIn('"icon": "notes"', source)
        self.assertIn('"icon": "account-tree"', source)
        self.assertIn('"icon": "snapshot"', source)
        self.assertIn('"icon": "activity-feed"', source)
        self.assertNotIn(
            "onCurrentIndexChanged: reportScroll.contentY = 0", source
        )
        self.assertIn("readonly property color objectAccent", source)
        self.assertIn("accent: root.objectAccent", source)
        self.assertIn("expandedHeaderContent.implicitHeight + 28", source)
        self.assertIn("columns: eventBubble.width >= 520 ? 2 : 1", activity_card_source)
        self.assertIn("readonly property real bubbleExtent", activity_card_source)
        self.assertIn(
            "implicitHeight: Math.max(72, eventBubble.implicitHeight + 8)",
            activity_card_source,
        )
        self.assertNotIn("activePage:", source)
        self.assertNotIn("syncHeaderToScroll", source)
        self.assertNotIn("Collapse object header", source)
        self.assertNotIn("Expand object header", source)
        self.assertIn("active: processRow.expanded", snapshot_tree_source)
        self.assertNotIn("model: sobjectSnapshotModel", source)
        self.assertNotIn("model: sobjectFileModel", source)
        self.assertIn("model: sobjectParticipantModel", source)
        for repeater in (
            "participantRepeater", "taskRepeater", "noteRepeater",
            "childRepeater", "activityRepeater",
        ):
            self.assertIn(f"visible: {repeater}.count === 0", source)
        self.assertNotIn("Model.count() === 0", source)
        self.assertIn('qsTr("PEOPLE AND WORK HOURS")', source)
        self.assertIn("participantRow.hours.toFixed(1)", source)
        self.assertIn("open_participant(participantRow.login)", source)
        self.assertNotIn('qsTr("OBJECT DETAILS")', source)
        self.assertEqual(source.count("value: root.summary.project"), 1)
        self.assertEqual(source.count("value: root.summary.pipeline"), 1)
        self.assertEqual(source.count("value: root.summary.code"), 1)
        self.assertIn("open_task(taskRow.taskCode, taskRow.process)", source)
        self.assertIn("open_snapshot(snapshotRow.modelIndex)", snapshot_tree_source)
        self.assertNotIn("open_search_key(taskRow.searchKey)", source)
        self.assertNotIn("open_search_key(snapshotRow.searchKey)", source)

    def test_children_use_lazy_project_search_type_catalog(self):
        relation = {
            "from": "demo/shot",
            "to": "demo/asset",
            "relationship": "code",
        }

        class ChildSType:
            pass

        child_stype = ChildSType()

        class Project:
            stypes = None
            calls = 0

            @classmethod
            def get_stypes(cls):
                cls.calls += 1
                return {"demo/shot": child_stype}

        class Schema:
            @staticmethod
            def get_children():
                return [relation]

        class RootSType:
            @staticmethod
            def get_project():
                return Project()

            @staticmethod
            def get_schema():
                return Schema()

        child = FakeRecord(
            "skey://demo/shot?code=SHOT010", code="SHOT010"
        )

        class Root:
            request = None

            @staticmethod
            def get_stype():
                return RootSType()

            @classmethod
            def get_related_sobjects(cls, **kwargs):
                cls.request = dict(kwargs)
                return {"SHOT010": child}, {}

        result = SObjectInfoController._query_related_children(Root())

        self.assertEqual(Project.calls, 1)
        self.assertEqual(len(result), 1)
        self.assertIs(result[0][1], child_stype)
        self.assertIs(result[0][2], child)
        self.assertEqual(Root.request["path"], "child")
        self.assertTrue(Root.request["get_all_snapshots"])

    def test_children_skip_many_to_many_and_keep_direct_relations(self):
        many_to_many_stype = object()
        direct_stype = object()

        class Project:
            @staticmethod
            def get_stypes():
                return {
                    "demo/tag": many_to_many_stype,
                    "demo/shot": direct_stype,
                }

        class Schema:
            @staticmethod
            def get_children():
                return [{
                    "from": "demo/tag",
                    "to": "demo/asset",
                    "type": "many_to_many",
                    "relationship": "instance",
                }, {
                    "from": "demo/shot",
                    "to": "demo/asset",
                    "relationship": "code",
                }]

        class RootSType:
            @staticmethod
            def get_project():
                return Project()

            @staticmethod
            def get_schema():
                return Schema()

        child = FakeRecord(
            "skey://demo/shot?code=SHOT010", code="SHOT010"
        )

        class Root:
            requests = []

            @staticmethod
            def get_stype():
                return RootSType()

            @classmethod
            def get_related_sobjects(cls, **kwargs):
                cls.requests.append(dict(kwargs))
                if kwargs["child_stype"] is many_to_many_stype:
                    raise ValueError("many-to-many needs an instance owner")
                return {"SHOT010": child}, {}

        result = SObjectInfoController._query_related_children(Root())

        self.assertEqual(len(result), 1)
        self.assertIs(result[0][1], direct_stype)
        self.assertIs(result[0][2], child)
        self.assertEqual(len(Root.requests), 1)
        self.assertIs(Root.requests[0]["child_stype"], direct_stype)

    def test_task_notes_children_hours_and_cost_are_aggregated(self):
        class ChildSType:
            @staticmethod
            def get_code():
                return "demo/shot"

            @staticmethod
            def get_pretty_name():
                return "Shots"

            @staticmethod
            def get_stype_color(fmt="hex"):
                return "#8e6ccf"

        class Child(FakeRecord):
            def get_title(self):
                return "Shot 010"

            def get_code(self):
                return "SHOT010"

        class WorkHour:
            def get_value(self, name):
                return {"task_code": "TASK001", "login": "artist"}.get(name)

            @staticmethod
            def get_total_hours():
                return 6.5

            @staticmethod
            def get_labor_cost(rate):
                return 6.5 * float(rate or 0)

        sobject = FakeSObject(FakeProcess(FakeContext([], [])))
        task = FakeRecord(
            "skey://sthpw/task?code=TASK001", code="TASK001",
            process="model", status="Approved", assigned="artist",
            pipeline_code="task", bid_duration=8,
            bid_end_date="2026-08-30",
        )
        note = FakeRecord(
            "skey://sthpw/note?code=NOTE001", search_code="TASK001",
            process="model", login="reviewer", note="Task review",
            timestamp="2026-08-20 10:00:00",
        )
        child = Child(
            "skey://demo/shot?code=SHOT010", code="SHOT010",
            description="Linked shot", status="In Progress",
        )
        application = FakeApplication()
        application.workspace_state._selected_sobject = sobject
        controller = SObjectInfoController(application, users=FakeUsers())
        controller._refreshed_tasks = [task]
        controller._refreshed_notes = [note]
        controller._refreshed_children = [(
            {"from": "demo/shot", "relationship": "code"},
            ChildSType(), child,
        )]
        controller._refreshed_work_hours = {
            "entries": [WorkHour()],
            "permissions": {"viewCosts": True},
            "rates": {"artist": 20},
        }

        controller._rebuild()

        self.assertEqual(controller.metrics["taskNotes"], 1)
        self.assertEqual(controller.metrics["objectNotes"], 0)
        self.assertEqual(controller.tasks.get(0)["notesCount"], 1)
        self.assertTrue(controller.tasks.get(0)["endPretty"])
        self.assertTrue(controller.tasks.get(0)["endFull"])
        controller.set_page(1)
        self.assertEqual(controller.notes.get(0)["taskCode"], "TASK001")
        self.assertTrue(controller.notes.get(0)["isTaskNote"])
        self.assertEqual(controller.metrics["children"], 1)
        controller.set_page(2)
        self.assertEqual(controller.children.get(0)["title"], "Shot 010")
        self.assertEqual(controller.metrics["workHours"], 6.5)
        self.assertEqual(controller.metrics["totalCost"], 130.0)
        self.assertTrue(controller.metrics["canViewCosts"])
        artist = next(
            record for record in controller.participants._records
            if record["login"] == "artist"
        )
        self.assertEqual(artist["hours"], 6.5)
        self.assertEqual(artist["cost"], 130.0)

    def test_empty_selection_clears_the_report(self):
        application = FakeApplication()
        controller = SObjectInfoController(application, users=FakeUsers())

        self.assertFalse(controller.hasObject)
        self.assertEqual(controller.summary, {})
        self.assertEqual(controller.files.count(), 0)


if __name__ == "__main__":
    unittest.main()
