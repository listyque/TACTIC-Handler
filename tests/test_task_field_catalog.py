import unittest

from thlib.ui.task_workspace.field_catalog import (
    _choices,
    _ensure_empty_choice,
)


class TaskFieldCatalogTests(unittest.TestCase):
    def test_priority_choices_from_display_values(self):
        self.assertEqual(
            _choices({
                "__display_values__": {
                    "values": ["0", "1", "2"],
                    "labels": ["Normal", "High", "Urgent"],
                },
            }),
            [
                {"value": "0", "label": "Normal", "color": ""},
                {"value": "1", "label": "High", "color": ""},
                {"value": "2", "label": "Urgent", "color": ""},
            ],
        )

    def test_priority_choices_from_widget_config_strings(self):
        self.assertEqual(
            _choices({
                "action_options": {
                    "values": "0|1|2",
                    "labels": "Normal|High|Urgent",
                },
            })[2]["label"],
            "Urgent",
        )

    def test_blank_priority_option_receives_a_visible_label(self):
        choices = _ensure_empty_choice([
            {"value": "", "label": "", "color": ""},
            {"value": "3", "label": "Important", "color": ""},
        ], "No priority")

        self.assertEqual(choices[0]["label"], "No priority")
        self.assertEqual(len(choices), 2)


if __name__ == "__main__":
    unittest.main()
