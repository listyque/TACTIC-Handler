import os
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal

import thlib.tactic_classes as tc
from modern_ui.work_hours import WorkHoursController


class _DockModel:
    def __init__(self):
        self.opened = []

    def show_panel(self, panel_id):
        self.opened.append(panel_id)


class _Application(QObject):
    def __init__(self):
        super().__init__()
        self.dock_model = _DockModel()
        self.debug_log = None


class _TaskRecordModel:
    def __init__(self, records=None):
        self._records = list(records or [])

    def count(self):
        return len(self._records)

    def update_record(self, row, values):
        self._records[row].update(values)


class _Tasks(QObject):
    visibleTaskSetChanged = Signal()
    advancedChanged = Signal()

    def __init__(self, records=None):
        super().__init__()
        records = list(records or [])
        self.advanced_model = _TaskRecordModel(records)
        self.table_model = _TaskRecordModel([
            dict(record) for record in records
        ])


class _Project:
    def get_code(self):
        return "test"


class _Task:
    def __init__(self, hours=8):
        self.info = {"code": "TASK0001", "bid_duration": hours}
        self.project = _Project()

    def get_info(self):
        return self.info

    def get_code(self):
        return self.info["code"]

    def get_project(self):
        return self.project


def _entry(code, hours, category="regular", status="", can_approve=True):
    return tc.WorkHour({
        "code": code,
        "__search_key__": "skey://sthpw/work_hour?code={}".format(code),
        "straight_time": hours,
        "over_time": hours if category == "overtime" else 0,
        "category": category,
        "status": status,
        "task_code": "TASK0001",
        "login": "artist",
        "day": "2026-08-09 00:00:00",
        "__can_edit__": True,
        "__can_approve__": can_approve,
    }, project=_Project())


class WorkHourObjectTests(unittest.TestCase):
    def test_parent_and_task_queries_use_their_native_relationships(self):
        parent = tc.SObject({
            "code": "ASSET0001", "__search_type__": "test/asset"
        }, project=_Project())
        task = tc.Task({
            "code": "TASK0001", "__search_type__": "sthpw/task"
        }, project=_Project())
        with patch("thlib.tactic_classes.query_work_hours") as query:
            query.return_value = {"entries": []}
            parent.get_work_hours()
            self.assertEqual(query.call_args.kwargs["parent_codes"], [
                "ASSET0001"
            ])
            self.assertEqual(query.call_args.args[0], [])

            task.get_work_hours()
            self.assertEqual(query.call_args.args[0], ["TASK0001"])
            self.assertNotIn("parent_codes", query.call_args.kwargs)

    def test_regular_and_overtime_hours_do_not_double_count(self):
        regular = _entry("WORK0001", 6)
        overtime = _entry("WORK0002", 2, "overtime")

        self.assertEqual(regular.get_regular_hours(), 6)
        self.assertEqual(regular.get_overtime_hours(), 0)
        self.assertEqual(regular.get_total_hours(), 6)
        self.assertEqual(overtime.get_regular_hours(), 0)
        self.assertEqual(overtime.get_overtime_hours(), 2)
        self.assertEqual(overtime.get_total_hours(), 2)

    def test_labor_cost_uses_overtime_factor(self):
        regular = _entry("WORK0001", 6)
        overtime = _entry("WORK0002", 2, "overtime")

        self.assertEqual(
            regular.get_labor_cost(Decimal("10")), Decimal("60.0")
        )
        self.assertEqual(
            overtime.get_labor_cost(Decimal("10"), Decimal("1.5")),
            Decimal("30.00"),
        )

    def test_partial_update_uses_native_object_mutation(self):
        entry = _entry("WORK0001", 6)
        with patch("thlib.tactic_classes.mutate_work_hour") as mutate:
            mutate.return_value = {"code": "WORK0001", "straight_time": 7}
            entry.update_entry(straight_time=7)

        mutate.assert_called_once_with(
            "update", "test", work_hour_code="WORK0001",
            values={"straight_time": 7},
        )
        self.assertEqual(entry.get_value("straight_time"), 7)

    def test_create_can_approve_in_the_same_server_mutation(self):
        task = _Task()
        with patch("thlib.tactic_classes.mutate_work_hour") as mutate:
            mutate.return_value = {
                "code": "WORK0002", "status": "approved"
            }
            entry = tc.WorkHour.create(
                task, "2026-08-09", 4, login="supervisor",
                approve=True,
            )

        values = mutate.call_args.kwargs["values"]
        self.assertTrue(values["approve"])
        self.assertEqual(entry.get_value("status"), "approved")


class WorkHoursControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = WorkHoursController(_Application())

    def tearDown(self):
        self.controller.shutdown()

    def test_summary_separates_logged_approved_and_over_plan(self):
        task = _Task(hours=8)
        entries = [
            _entry("WORK0001", 7, status="approved"),
            _entry("WORK0002", 2, "overtime"),
            _entry("WORK0003", 3, status="approved"),
        ]

        summary = self.controller._summary(task, entries)

        self.assertEqual(summary["planned"], 8)
        self.assertEqual(summary["logged"], 12)
        self.assertEqual(summary["approved"], 10)
        self.assertEqual(summary["pending"], 2)
        self.assertEqual(summary["remaining"], 0)
        self.assertEqual(summary["overPlan"], 2)
        self.assertEqual(summary["overtime"], 2)
        self.assertEqual(summary["label"], "10.0 / 8.0 h")

    def test_empty_summary_uses_same_hours_format_as_task_records(self):
        summary = self.controller._empty_summary(_Task(hours=0))

        self.assertEqual(summary["label"], "0.0 / 0.0 h")

    def test_minute_bid_duration_is_normalized_to_hours(self):
        self.controller._bid_duration_unit = "minute"
        summary = self.controller._summary(_Task(hours=480), [])
        self.assertEqual(summary["planned"], 8)

    def test_virtual_task_keeps_workflow_bid_duration(self):
        code = "__new_task__draft"
        tasks = _Tasks([{
            "taskCode": code,
            "isNew": True,
            "plannedHours": 24.0,
            "remainingHours": 24.0,
            "hoursLabel": "0.0 / 24.0 h",
        }])
        controller = WorkHoursController(_Application(), tasks=tasks)
        self.addCleanup(controller.shutdown)

        self.assertEqual(controller._visible_task_codes(), [])
        controller._summary_by_task[code] = {
            "planned": 0.0,
            "logged": 0.0,
            "approved": 0.0,
            "pending": 0.0,
            "remaining": 0.0,
            "overPlan": 0.0,
            "label": "0.0 / 0.0 h",
        }
        controller._apply_task_model_summaries()

        for model in (tasks.advanced_model, tasks.table_model):
            record = model._records[0]
            self.assertEqual(record["plannedHours"], 24.0)
            self.assertEqual(record["remainingHours"], 24.0)
            self.assertEqual(record["hoursLabel"], "0.0 / 24.0 h")

    def test_virtual_task_does_not_query_work_hours(self):
        tasks = _Tasks([{
            "taskCode": "__new_task__draft",
            "isNew": True,
            "plannedHours": 24.0,
        }])
        controller = WorkHoursController(_Application(), tasks=tasks)
        self.addCleanup(controller.shutdown)

        with patch.object(controller, "_load") as load:
            controller._load_visible_tasks()

        load.assert_not_called()

    def test_task_context_accepts_a_generic_tactic_sobject(self):
        task = SimpleNamespace(
            get_info=lambda: {"code": "TASK0002", "bid_duration": 6},
            get_project=lambda: _Project(),
        )
        self.controller._communication = SimpleNamespace(
            selected_task_object=lambda: task
        )

        with patch.object(self.controller, "refresh_current") as refresh:
            self.controller.sync_task_context()

        self.assertTrue(self.controller.hasTask)
        self.assertEqual(self.controller.taskCode, "TASK0002")
        self.assertEqual(self.controller.currentSummary["planned"], 6)
        refresh.assert_called_once_with()

    def test_report_catalog_keeps_costs_permission_gated(self):
        descriptors = {
            record["key"]: record
            for record in self.controller.report_descriptors._records
        }
        self.assertEqual(descriptors["my_hours"]["permission"], "user")
        self.assertEqual(descriptors["labor_cost"]["permission"], "finance")

    def test_report_and_timesheet_docks_use_shared_infrastructure(self):
        self.controller._busy = True
        self.controller.open_timesheet()
        self.controller.open_work_reports()
        self.assertIn("timesheet", self.controller._application.dock_model.opened)
        self.assertIn(
            "work_reports", self.controller._application.dock_model.opened
        )

    def test_supervisor_can_select_multiple_timesheet_entries(self):
        self.controller.timesheet_entries.replace([
            self.controller._entry_record(_entry("WORK0001", 2)),
            self.controller._entry_record(_entry("WORK0002", 3)),
        ])

        self.controller.toggle_timesheet_selected(0)
        self.controller.toggle_timesheet_selected(1)

        self.assertEqual(self.controller.selectedCount, 2)
        self.controller.clear_timesheet_selection()
        self.assertEqual(self.controller.selectedCount, 0)


if __name__ == "__main__":
    unittest.main()
