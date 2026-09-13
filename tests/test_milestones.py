import unittest
import os
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

from thlib.ui.milestones import MilestoneController


class FakeApplication(QObject):
    def __init__(self):
        super().__init__()
        self._current_project_code = "demo"
        self.debug_log = Mock()
        self.opened = []

    def open_window(self, window_id):
        self.opened.append(window_id)


class FakeMilestone:
    def __init__(self, code="MILESTONE001", description="Review", due="2026-08-12"):
        self.info = {
            "code": code,
            "description": description,
            "due_date": due,
        }
        self.committed = False
        self.deleted = False

    def get_info(self):
        return dict(self.info)

    def set_value(self, key, value):
        self.info[key] = value

    def commit(self, triggers=True):
        self.committed = triggers
        return self

    def delete_sobject(self):
        self.deleted = True
        return True


class FakeStatusAttr:
    def __init__(self, completion):
        self.completion = completion

    def get_percent_completion(self):
        return self.completion


class FakeTask:
    def __init__(self, milestone, completion, process="model", start="2026-08-01"):
        self.info = {
            "code": "TASK{}".format(completion),
            "milestone_code": milestone,
            "process": process,
            "bid_start_date": start,
            "bid_end_date": "2099-08-10",
            "bid_duration": 8,
            # Deliberately different: native status completion must win.
            "completion": 1,
        }
        self.status_attr = FakeStatusAttr(completion)

    def get_info(self):
        return dict(self.info)

    def get_attr(self, name):
        if name != "status":
            raise KeyError(name)
        return self.status_attr


class MilestoneControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        self.application = FakeApplication()
        self.controller = MilestoneController(self.application)

    def test_open_manager_uses_single_registered_window(self):
        with patch.object(self.controller, "refresh") as refresh:
            self.controller.open_manager()
        self.assertEqual(self.application.opened, ["milestone_manager"])
        refresh.assert_called_once_with()

    def test_records_are_project_objects_and_keep_code(self):
        item = FakeMilestone()
        self.controller._request_id = "load"
        self.controller._busy = True
        self.controller._records_loaded("load", ({item.info["code"]: item}, {}))
        self.assertEqual(self.controller.model.count(), 1)
        self.assertEqual(self.controller.model.get(0)["code"], "MILESTONE001")
        self.assertIs(self.controller._objects["MILESTONE001"], item)

    def test_plan_uses_original_status_completion_average(self):
        item = FakeMilestone()
        tasks = [
            FakeTask("MILESTONE001", 25, "model"),
            FakeTask("MILESTONE001", 100, "publish", "2026-08-03"),
            FakeTask("MILESTONE001", -10, "review", "2026-08-02"),
        ]
        self.controller._request_id = "load"
        self.controller._busy = True
        self.controller._records_loaded("load", {
            "milestones": [item], "tasks": tasks,
        })

        record = self.controller.model.get(0)
        self.assertEqual(record["completion"], 42)
        self.assertEqual(record["taskCount"], 3)
        self.assertEqual(record["completedCount"], 1)
        self.assertEqual(record["planStartDate"], "2026-08-01")
        self.assertEqual(record["plannedHours"], 24.0)
        self.assertEqual(record["processSummary"], "model / publish / review")
        self.assertEqual(self.controller.ganttMarkers, [{
            "code": "MILESTONE001",
            "label": "Review",
            "dueDate": "2026-08-12",
            "completion": 42,
            "taskCount": 3,
        }])
        self.assertTrue(self.controller.loaded)

    def test_new_milestone_is_virtual_until_saved(self):
        self.controller.create_milestone()
        record = self.controller.model.get(0)
        self.assertTrue(record["isNew"])
        self.assertTrue(record["dirty"])
        self.controller.stage_value(record["code"], "description", "Delivery")
        self.assertEqual(self.controller.model.get(0)["description"], "Delivery")
        self.controller.discard(record["code"])
        self.assertEqual(self.controller.model.count(), 0)

    def test_duplicate_name_is_rejected_case_insensitively(self):
        first = FakeMilestone(description="Delivery")
        self.controller._request_id = "load"
        self.controller._busy = True
        self.controller._records_loaded("load", ({first.info["code"]: first}, {}))
        self.controller.create_milestone()
        draft = self.controller.model.get(0)
        self.controller.stage_value(draft["code"], "description", " delivery ")
        with patch.object(self.controller, "_start_worker") as start_worker:
            self.controller.save(draft["code"])
        start_worker.assert_not_called()
        self.assertEqual(
            self.controller.model.get(0)["error"],
            "A milestone with this name already exists",
        )

    def test_worker_state_cannot_re_dirty_a_saved_row(self):
        item = FakeMilestone()
        self.controller._request_id = "load"
        self.controller._busy = True
        self.controller._records_loaded("load", ({item.info["code"]: item}, {}))
        self.controller._busy = True
        self.controller.stage_value(
            "MILESTONE001", "description", "Late editingFinished value"
        )
        self.assertFalse(self.controller.model.get(0)["dirty"])
        self.assertEqual(self.controller.model.get(0)["description"], "Review")

    def test_existing_milestone_uses_native_object_commit(self):
        item = FakeMilestone()
        result = self.controller._update_record(item, "Final", "2026-08-30")
        self.assertIs(result, item)
        self.assertEqual(item.info["description"], "Final")
        self.assertEqual(item.info["due_date"], "2026-08-30")
        self.assertTrue(item.committed)

    def test_delete_refuses_milestone_linked_to_task(self):
        item = FakeMilestone()
        with patch("thlib.tactic_classes.get_sobjects", return_value=[Mock()]):
            with self.assertRaisesRegex(RuntimeError, "assigned to tasks"):
                self.controller._delete_record("demo", "MILESTONE001", item)
        self.assertFalse(item.deleted)

    def test_delete_uses_native_sobject_when_unlinked(self):
        item = FakeMilestone()
        with patch("thlib.tactic_classes.get_sobjects", return_value=[]):
            self.controller._delete_record("demo", "MILESTONE001", item)
        self.assertTrue(item.deleted)

    def test_manager_qml_centers_empty_state(self):
        self.application._current_project_code = ""
        engine = QQmlEngine()
        qml_dir = Path(__file__).parents[1] / "thlib" / "ui" / "qml"
        engine.addImportPath(str(qml_dir))
        engine.rootContext().setContextProperty(
            "milestoneController", self.controller
        )
        engine.rootContext().setContextProperty(
            "milestoneModel", self.controller.model
        )
        engine.rootContext().setContextProperty("fontAwesomeSolidGlyphs", {})
        engine.rootContext().setContextProperty("fontAwesomeSolidFontFamily", "")
        engine.rootContext().setContextProperty("fontAwesomeRegularGlyphs", {})
        engine.rootContext().setContextProperty("fontAwesomeRegularFontFamily", "")
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(qml_dir / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(qml_dir / "MilestoneManagerView.qml")),
        )
        view = component.createWithInitialProperties(
            {"theme": theme, "width": 800, "height": 640}
        )
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        empty_state = view.findChild(QObject, "milestoneEmptyState")
        content = view.findChild(QObject, "milestoneEmptyStateContent")
        self.assertIsNotNone(empty_state)
        self.assertIsNotNone(content)
        for width in (420, 800):
            view.setProperty("width", width)
            QGuiApplication.processEvents()
            self.assertAlmostEqual(
                content.property("x") + content.property("width") / 2,
                empty_state.property("width") / 2,
                delta=1,
            )


if __name__ == "__main__":
    unittest.main()
