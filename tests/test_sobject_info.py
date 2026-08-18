import unittest

from PySide6.QtCore import QObject, Signal

from modern_ui.sobject_info import SObjectInfoController
from modern_ui.workspace_models.records import RecordListModel
from modern_ui.workspace_models.state import WorkspaceState


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

    def open_search_key(self, search_key):
        self.opened.append(search_key)


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


class SObjectInfoControllerTests(unittest.TestCase):
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
        self.assertEqual(controller.participants.get(0)["displayName"], "Ada Artist")
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

    def test_empty_selection_clears_the_report(self):
        application = FakeApplication()
        controller = SObjectInfoController(application, users=FakeUsers())

        self.assertFalse(controller.hasObject)
        self.assertEqual(controller.summary, {})
        self.assertEqual(controller.files.count(), 0)


if __name__ == "__main__":
    unittest.main()
