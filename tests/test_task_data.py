import unittest
from datetime import date

from thlib.ui.task_data import (
    calendar_cells,
    due_state,
    filtered_records,
    gantt_layout,
    parent_search_key,
    sort_and_group,
    task_record,
)


class _Task:
    def __init__(self, code, process="model", context=""):
        self._info = {
            "code": code,
            "process": process,
            "context": context,
            "search_type": "prod/asset",
            "search_code": "ASSET0001",
            "project_code": "niki",
        }

    def get_info(self):
        return dict(self._info)

    def get_search_key(self):
        return "skey://sthpw/task?project=niki&code={}".format(
            self._info["code"]
        )

    def get_notes_count(self):
        return {}


class TaskDataTests(unittest.TestCase):
    def test_parent_key_uses_code(self):
        self.assertEqual(
            parent_search_key({
                "search_type": "prod/asset?project=niki",
                "search_code": "ASSET0001",
                "project_code": "niki",
            }),
            "skey://prod/asset?project=niki&code=ASSET0001",
        )

    def test_due_state_is_deterministic(self):
        today = date(2026, 8, 4)
        self.assertEqual(due_state("2026-08-03 18:00:00", today), "overdue")
        self.assertEqual(due_state("2026-08-04 18:00:00", today), "today")
        self.assertEqual(due_state("2026-08-06 18:00:00", today), "soon")
        self.assertEqual(due_state("", today), "unscheduled")

    def test_filters_are_local_and_composable(self):
        records = [
            {
                "taskCode": "TASK1", "parentTitle": "Robot",
                "process": "model", "processLabel": "Model",
                "status": "In Progress", "assigned": "artist",
                "assignedLabel": "Artist", "description": "Body pass",
                "dueState": "today", "notes": 2,
                "end": "2026-08-04 18:00:00",
            },
            {
                "taskCode": "TASK2", "parentTitle": "Tree",
                "process": "texture", "processLabel": "Texture",
                "status": "Pending", "assigned": "other",
                "assignedLabel": "Other", "description": "",
                "dueState": "scheduled", "notes": 0,
                "end": "2026-08-10 18:00:00",
            },
        ]
        result = filtered_records(records, {
            "text": "robot", "process": "model", "status": "",
            "assigned": "artist", "due": "today", "hasNotes": True,
            "day": "2026-08-04",
        })
        self.assertEqual([item["taskCode"] for item in result], ["TASK1"])

    def test_quick_filters_compose_by_group_without_mutating_records(self):
        records = [
            {
                "taskCode": "TASK1", "parentTitle": "Robot",
                "process": "model", "processLabel": "Model",
                "status": "In Progress", "assigned": "artist",
                "assignedLabel": "Artist", "description": "",
                "dueState": "today", "notes": 0, "end": "2026-08-04",
            },
            {
                "taskCode": "TASK2", "parentTitle": "Tree",
                "process": "texture", "processLabel": "Texture",
                "status": "Pending", "assigned": "",
                "assignedLabel": "Not assigned", "description": "",
                "dueState": "overdue", "notes": 0, "end": "2026-08-03",
            },
        ]
        filters = {
            "text": "", "process": "", "status": "", "assigned": "",
            "due": "", "hasNotes": False, "day": "",
        }

        mine = filtered_records(
            records, filters,
            {"preset": {"mine"}, "status": {"In Progress"}},
            "artist",
        )
        self.assertEqual([item["taskCode"] for item in mine], ["TASK1"])
        unassigned = filtered_records(
            records, filters,
            {"preset": {"unassigned", "overdue"}}, "artist",
        )
        self.assertEqual([item["taskCode"] for item in unassigned], ["TASK2"])
        self.assertNotIn("group", records[0])

    def test_grouping_does_not_mutate_source(self):
        records = [{
            "taskCode": "TASK1", "processLabel": "Model",
            "assignedLabel": "Artist", "end": "2026-08-04 18:00:00",
        }]
        result = sort_and_group(records, "due", "process")
        self.assertEqual(result[0]["group"], "Model")
        self.assertNotIn("group", records[0])

    def test_group_headers_have_counts_and_collapse_without_removing_rows(self):
        records = [
            {
                "taskCode": "TASK1", "status": "Pending",
                "statusColor": "#aa0000", "end": "2026-08-05",
            },
            {
                "taskCode": "TASK2", "status": "Approved",
                "statusColor": "#00aa00", "end": "2026-08-04",
            },
            {
                "taskCode": "TASK3", "status": "Pending",
                "statusColor": "#aa0000", "end": "2026-08-03",
            },
        ]

        grouped = sort_and_group(
            records, "due", "status", collapsed_groups={"Pending"}
        )
        self.assertEqual(len(grouped), 3)
        pending = [item for item in grouped if item["groupKey"] == "Pending"]
        self.assertEqual(len(pending), 2)
        self.assertEqual(sum(item["groupFirst"] for item in pending), 1)
        self.assertTrue(all(item["groupCount"] == 2 for item in pending))
        self.assertTrue(all(item["groupCollapsed"] for item in pending))
        self.assertEqual(
            [item["taskCode"] for item in pending], ["TASK3", "TASK1"]
        )

    def test_process_group_uses_one_header_when_pipeline_labels_differ(self):
        records = [
            {
                "taskCode": "TASK1", "process": "light",
                "processLabel": "LIGHT", "processColor": "#607d8b",
            },
            {
                "taskCode": "TASK2", "process": "model",
                "processLabel": "MODEL", "processColor": "#ef5350",
            },
            {
                "taskCode": "TASK3", "process": "light",
                "processLabel": "СВЕТ", "processColor": "#5e4db2",
            },
            {
                "taskCode": "TASK4", "process": "light",
                "processLabel": "LIGHT", "processColor": "#607d8b",
            },
        ]

        grouped = sort_and_group(records, "due", "process")
        light = [item for item in grouped if item["groupKey"] == "light"]

        self.assertEqual(len(light), 3)
        self.assertEqual(sum(item["groupFirst"] for item in light), 1)
        self.assertTrue(all(item["group"] == "LIGHT" for item in light))
        self.assertTrue(all(item["groupCount"] == 3 for item in light))
        self.assertTrue(all(item["groupColor"] == "#607d8b" for item in light))
        self.assertEqual(
            [item["groupKey"] for item in grouped],
            ["light", "light", "light", "model"],
        )
        collapsed = sort_and_group(
            records, "due", "process", collapsed_groups={"light"}
        )
        self.assertTrue(all(
            item["groupCollapsed"]
            for item in collapsed if item["groupKey"] == "light"
        ))

    def test_search_type_group_uses_configured_title_and_code_identity(self):
        records = [{
            "taskCode": "TASK1",
            "parentSearchType": "complex/scenes",
            "parentSearchTypeLabel": "Scenes",
        }, {
            "taskCode": "TASK2",
            "parentSearchType": "complex/shot",
            "parentSearchTypeLabel": "Shots",
        }]

        grouped = sort_and_group(records, "due", "search_type")

        self.assertEqual(
            [(item["groupKey"], item["group"]) for item in grouped],
            [("complex/scenes", "Scenes"), ("complex/shot", "Shots")],
        )

    def test_column_sort_direction_reverses_text_and_group_order(self):
        records = [
            {
                "taskCode": "TASK1", "status": "Approved",
                "end": "2026-08-05",
            },
            {
                "taskCode": "TASK2", "status": "Pending",
                "end": "2026-08-04",
            },
            {
                "taskCode": "TASK3", "status": "In Progress",
                "end": "2026-08-03",
            },
        ]

        descending = sort_and_group(
            records, "status", "status", descending=True
        )

        self.assertEqual(
            [item["status"] for item in descending],
            ["Pending", "In Progress", "Approved"],
        )

    def test_tasks_on_same_process_keep_distinct_code_identity(self):
        tasks = [
            _Task("TASK0001", context="model/main"),
            _Task("TASK0002", context="model/review"),
        ]
        records = [task_record(task) for task in tasks]

        self.assertEqual(
            [record["taskCode"] for record in records],
            ["TASK0001", "TASK0002"],
        )
        self.assertEqual({record["process"] for record in records}, {"model"})
        self.assertEqual(len({record["searchKey"] for record in records}), 2)

    def test_task_record_exposes_planned_hours_without_server_queries(self):
        task = _Task("TASK0001")
        task._info["bid_duration"] = 12.5
        record = task_record(task)
        self.assertEqual(record["plannedHours"], 12.5)
        self.assertEqual(record["hoursLabel"], "0.0 / 12.5 h")

    def test_task_record_keeps_zero_hours_label_stable(self):
        task = _Task("TASK0001")
        task._info["bid_duration"] = 0

        record = task_record(task)

        self.assertEqual(record["hoursLabel"], "0.0 / 0.0 h")

    def test_grouping_preserves_task_identity_for_every_mode(self):
        records = [
            {
                "taskCode": "TASK0001", "processLabel": "Model",
                "assignedLabel": "Artist", "status": "In Progress",
                "parentTitle": "Robot", "end": "2026-08-04 18:00:00",
            },
            {
                "taskCode": "TASK0002", "processLabel": "Model",
                "assignedLabel": "Artist", "status": "In Progress",
                "parentTitle": "Robot", "end": "2026-08-05 18:00:00",
            },
        ]

        for mode in ("process", "status", "user", "object", "none"):
            with self.subTest(mode=mode):
                grouped = sort_and_group(records, "due", mode)
                self.assertEqual(
                    {record["taskCode"] for record in grouped},
                    {"TASK0001", "TASK0002"},
                )

    def test_new_task_drafts_stay_above_every_group_and_sort(self):
        records = [
            {
                "taskCode": "TASK0001", "process": "model",
                "processLabel": "Model", "status": "In Progress",
                "assignedLabel": "Artist", "end": "2026-08-04",
            },
            {
                "taskCode": "__new_task__1", "process": "publish",
                "processLabel": "Publish", "status": "Pending",
                "assignedLabel": "Not assigned", "end": "",
                "isNew": True,
            },
            {
                "taskCode": "TASK0002", "process": "animation",
                "processLabel": "Animation", "status": "Approved",
                "assignedLabel": "Reviewer", "end": "2026-08-03",
            },
        ]

        for group_mode in ("process", "status", "user", "object", "none"):
            for sort_mode in ("due", "recent", "user", "status", "object"):
                with self.subTest(group=group_mode, sort=sort_mode):
                    grouped = sort_and_group(
                        records, sort_mode, group_mode,
                        collapsed_groups={"publish", "Pending"},
                    )
                    self.assertEqual(grouped[0]["taskCode"], "__new_task__1")
                    self.assertEqual(grouped[0]["groupKey"], "")
                    self.assertFalse(grouped[0]["groupCollapsed"])

    def test_calendar_always_has_six_weeks(self):
        cells = calendar_cells(2026, 8, [{
            "taskCode": "TASK0001", "parentKey": "asset-key",
            "parentTitle": "Robot", "process": "model",
            "processLabel": "Model", "status": "In Progress",
            "statusColor": "#33a1fd", "assignedLabel": "Artist",
            "end": "2026-08-04 18:00:00", "dueState": "overdue",
        }], today=date(2026, 8, 4))
        self.assertEqual(len(cells), 42)
        target = next(item for item in cells if item["date"] == "2026-08-04")
        self.assertEqual(target["taskCount"], 1)
        self.assertEqual(target["overdueCount"], 1)
        self.assertTrue(target["today"])
        self.assertEqual(target["tasks"][0]["taskCode"], "TASK0001")
        self.assertEqual(target["tasks"][0]["statusColor"], "#33a1fd")

    def test_calendar_places_milestone_plan_on_due_date(self):
        cells = calendar_cells(
            2026, 8, [], today=date(2026, 8, 4),
            milestones=[{
                "code": "MILESTONE001", "label": "Client delivery",
                "dueDate": "2026-08-12", "completion": 75,
                "taskCount": 4,
            }],
        )

        target = next(item for item in cells if item["date"] == "2026-08-12")
        self.assertEqual(target["milestoneCount"], 1)
        self.assertEqual(target["milestones"][0]["label"], "Client delivery")
        self.assertEqual(target["milestones"][0]["completion"], 75)

    def test_calendar_uses_deadlines_and_does_not_mutate_records(self):
        records = [{
            "taskCode": "TASK0001", "parentTitle": "Robot",
            "start": "2026-08-01", "end": "2026-08-09",
            "status": "Pending", "dueState": "scheduled",
        }]

        cells = calendar_cells(2026, 8, records, today=date(2026, 8, 4))

        self.assertEqual(
            sum(cell["taskCount"] for cell in cells), 1
        )
        self.assertEqual(
            next(cell for cell in cells if cell["taskCount"])["date"],
            "2026-08-09",
        )
        self.assertNotIn("tasks", records[0])

    def test_gantt_layout_builds_geometry_without_mutating_records(self):
        records = [{
            "taskCode": "TASK1", "start": "2026-08-04 09:00:00",
            "end": "2026-08-06 18:00:00", "groupKey": "model",
            "group": "Model", "statusColor": "#33a1fd",
        }]

        layout = gantt_layout(records, today=date(2026, 8, 4))

        self.assertEqual(layout["rangeStart"], "2026-07-27")
        self.assertEqual(layout["rangeEnd"], "2026-08-23")
        self.assertEqual(layout["days"], 28)
        self.assertEqual(layout["todayDay"], 8)
        self.assertEqual(
            set(layout["tickSets"]),
            {"days", "weeks", "months", "quarters"},
        )
        self.assertTrue(layout["tickSets"]["days"])
        self.assertTrue(layout["tickSets"]["weeks"])
        self.assertTrue(layout["tickSets"]["months"])
        self.assertTrue(layout["tickSets"]["quarters"])
        self.assertEqual(layout["scheduled"], 1)
        self.assertEqual(layout["unscheduled"], 0)
        self.assertEqual(layout["records"][0]["ganttStartDay"], 8)
        self.assertEqual(layout["records"][0]["ganttDurationDays"], 3)
        self.assertNotIn("ganttScheduled", records[0])

    def test_gantt_layout_exposes_project_milestone_markers(self):
        layout = gantt_layout([{
            "taskCode": "TASK1", "start": "2026-08-04",
            "end": "2026-08-06", "groupKey": "model",
        }], today=date(2026, 8, 4), milestones=[
            {"value": "", "label": "No milestone", "dueDate": ""},
            {
                "value": "MILESTONE001", "label": "Client review",
                "dueDate": "2026-08-20",
            },
        ])

        self.assertEqual(layout["milestones"], [{
            "code": "MILESTONE001",
            "label": "Client review",
            "dueDate": "2026-08-20",
            "offsetDay": 24,
            "completion": 0,
            "taskCount": 0,
        }])

    def test_gantt_layout_separates_unscheduled_and_invalid_tasks(self):
        layout = gantt_layout([
            {
                "taskCode": "TASK1", "start": "2026-08-04",
                "end": "2026-08-05", "groupKey": "model",
                "group": "Model",
            },
            {
                "taskCode": "TASK2", "start": "",
                "end": "2026-08-06", "groupKey": "model",
                "group": "Model",
            },
            {
                "taskCode": "TASK3", "start": "2026-08-08",
                "end": "2026-08-07", "groupKey": "model",
                "group": "Model",
            },
        ], today=date(2026, 8, 4))

        self.assertEqual(layout["scheduled"], 1)
        self.assertEqual(layout["unscheduled"], 2)
        self.assertEqual(
            [record["taskCode"] for record in layout["records"]],
            ["TASK1", "TASK2", "TASK3"],
        )
        self.assertTrue(layout["records"][0]["ganttSectionFirst"])
        self.assertTrue(layout["records"][1]["ganttSectionFirst"])
        self.assertEqual(layout["records"][1]["ganttIssue"], "Start is not set")
        self.assertEqual(
            layout["records"][2]["ganttIssue"], "Deadline precedes start"
        )

    def test_gantt_layout_keeps_a_valid_draft_in_its_persisted_section(self):
        layout = gantt_layout([{
            "taskCode": "TASK1",
            "start": "2026-08-04",
            "end": "2026-08-05",
            "_ganttSectionScheduled": False,
            "groupKey": "model",
            "group": "Model",
        }], today=date(2026, 8, 4))

        record = layout["records"][0]
        self.assertTrue(record["ganttScheduled"])
        self.assertEqual(record["ganttSection"], "unscheduled")
        self.assertEqual(record["ganttDurationDays"], 2)
        self.assertEqual(layout["scheduled"], 0)
        self.assertEqual(layout["unscheduled"], 1)

    def test_gantt_layout_builds_overview_summaries_and_warnings(self):
        layout = gantt_layout([
            {
                "taskCode": "TASK1", "start": "2026-08-03",
                "end": "2026-08-08", "groupKey": "model",
                "group": "Model", "assigned": "artist",
                "progress": 20, "statusColor": "#33a1fd",
            },
            {
                "taskCode": "TASK2", "start": "2026-08-05",
                "end": "2026-08-07", "groupKey": "model",
                "group": "Model", "assigned": "artist",
                "progress": 60, "statusColor": "#33a1fd",
            },
        ], today=date(2026, 8, 9))

        first, second = layout["records"]
        self.assertEqual(first["ganttGroupStartDay"], 7)
        self.assertEqual(first["ganttGroupDurationDays"], 6)
        self.assertEqual(first["ganttGroupProgress"], 40)
        self.assertEqual(second["ganttGroupProgress"], 40)
        self.assertIn("Task is overdue", first["ganttWarning"])
        self.assertIn("Deadline falls on a weekend", first["ganttWarning"])
        self.assertIn("overlapping tasks", second["ganttWarning"])
        self.assertEqual(len(layout["overview"]), 2)
        self.assertGreaterEqual(layout["warnings"], 2)
        self.assertTrue(layout["weekends"])


if __name__ == "__main__":
    unittest.main()
