import unittest

from tests.qt_application import gui_test_application
from thlib.ui.naming_editor import NamingEditorController


class _Application:
    debug_log = None


class _CheckinController:
    currentObject = {
        "searchKey": "skey://niki_friends/dolly3d/assets?code=ASSETS00001",
        "title": "Example Asset",
    }
    process = "publish"
    context = "publish"
    processes = ["model", "publish"]
    contexts = ["publish", "publish/review"]

    def set_process(self, process):
        self.process = process

    def contexts_for_process(self, process):
        return [process, f"{process}/review"]


class _CommitQueue:
    def operation(self, _operation_id):
        return None


class NamingEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def setUp(self):
        self.controller = NamingEditorController(
            _Application(), _CheckinController(), _CommitQueue()
        )
        self.controller._target = {
            "searchKey": _CheckinController.currentObject["searchKey"],
            "searchType": "dolly3d/assets",
            "projectCode": "niki_friends",
            "code": "ASSETS00001",
            "title": "Example Asset",
        }
        self.controller._object_data = {
            "code": "ASSETS00001",
            "name": "hero_asset",
            "parent_code": "PIPELINE",
        }
        self.controller._project_data = {"code": "niki_friends"}
        self.controller._preview_process = "publish"
        self.controller._preview_context = "publish/review"

    def test_common_rule_tokens_are_previewed(self):
        self.controller.create_rule()
        self.controller.set_sample_file("scene.ma")
        self.assertEqual(
            self.controller.previewFilename,
            "hero_asset_v1.ma",
        )
        self.assertIn("niki_friends/assets/ASSETS00001", self.controller.previewPath)

    def test_file_type_case_expression_is_previewed(self):
        expression = (
            "root{@CASE(@GET(file.type) == 'playblast', "
            "'/'+'__preview', @GET(file.type) == 'icon', '/'+'__preview/icon')}"
        )
        rendered = self.controller._render_expression(
            expression, {"file.type": "icon"}
        )
        self.assertEqual(rendered, "root/__preview/icon")

    def test_new_rule_uses_current_object_type_and_context(self):
        self.controller.create_rule()
        rule = self.controller.selectedRule
        self.assertEqual(rule["search_type"], "dolly3d/assets")
        self.assertEqual(rule["context"], "publish/review")
        self.assertTrue(self.controller.isNew)
        self.assertTrue(self.controller.dirty)

    def test_preview_process_does_not_change_checkin_preparation(self):
        self.controller._processes = ["model", "publish"]
        self.controller.set_preview_process("model")
        self.assertEqual(self.controller.previewProcess, "model")
        self.assertEqual(self.controller.contexts, ["model", "model/review"])
        self.assertEqual(self.controller._checkin.process, "publish")


if __name__ == "__main__":
    unittest.main()
