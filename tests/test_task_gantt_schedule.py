from datetime import date
from pathlib import Path
import unittest

from thlib.ui.task_workspace.gantt_schedule import (
    add_workdays,
    batch_schedule_edits,
    schedule_dates,
    shifted_selection_edits,
)


class TaskGanttScheduleTests(unittest.TestCase):
    def test_schedule_module_stays_ui_and_server_independent(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "thlib/ui/task_workspace/gantt_schedule.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("PySide6", source)
        self.assertNotIn("thlib.environment", source)
    def test_schedule_preserves_times_and_skips_weekends(self):
        result = schedule_dates(
            {
                "start": "2026-08-20 09:30:00",
                "end": "2026-08-20 18:15:00",
            },
            "2026-08-17 00:00:00",
            4,
            2,
            True,
        )

        self.assertEqual(result, {
            "start": "2026-08-21 09:30:00",
            "end": "2026-08-24 18:15:00",
        })

    def test_add_workdays_handles_both_directions(self):
        friday = date(2026, 8, 21)
        self.assertEqual(add_workdays(friday, 1), date(2026, 8, 24))
        self.assertEqual(add_workdays(friday, -1), date(2026, 8, 20))

    def test_selected_move_uses_primary_delta(self):
        edits = shifted_selection_edits(
            {"start": "2026-08-20 10:00:00"},
            "2026-08-22 10:00:00",
            [(
                "TASK2",
                {
                    "start": "2026-08-18 08:00:00",
                    "end": "2026-08-19 17:00:00",
                },
            )],
        )

        self.assertEqual(edits["TASK2"], {
            "start": "2026-08-20 08:00:00",
            "end": "2026-08-21 17:00:00",
        })

    def test_batch_sequence_preserves_each_duration(self):
        edits = batch_schedule_edits([
            (
                "TASK1",
                {
                    "start": "2026-08-17 09:00:00",
                    "end": "2026-08-18 18:00:00",
                },
            ),
            (
                "TASK2",
                {
                    "start": "2026-08-20 10:00:00",
                    "end": "2026-08-20 16:00:00",
                },
            ),
        ], "sequence", working_days=True)

        self.assertEqual(edits["TASK1"]["start"], "2026-08-17 09:00:00")
        self.assertEqual(edits["TASK1"]["end"], "2026-08-18 18:00:00")
        self.assertEqual(edits["TASK2"]["start"], "2026-08-19 10:00:00")
        self.assertEqual(edits["TASK2"]["end"], "2026-08-19 16:00:00")


if __name__ == "__main__":
    unittest.main()
