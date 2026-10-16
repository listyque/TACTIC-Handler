"""Real native support controls and their existing command boundaries."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PySide6.QtCore import QPointF, Qt, QObject
from PySide6.QtTest import QTest
from tests.frame_support_fixture import Surface, SCREENS, evaluate, variant, controls
from tests import test_sidebar_editor_qml as sidebar_fixture


class FrameSupportTests(unittest.TestCase):
    def surface(self, screen, width=1100, height=740):
        value = Surface(screen, width, height)
        self.addCleanup(value.close)
        return value

    def controller(self, surface, name):
        return surface.controllers.findChild(QObject, name)

    def raw(self, surface, name):
        return next(
            item
            for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
                surface.window.contentItem()
            )
            if item.objectName() == name
        )

    def reveal(self, surface, name):
        item = self.raw(surface, name)
        parent = item.parentItem()
        while parent:
            offset = parent.property("contentY")
            if offset is not None and parent.height() > 0:
                top = item.mapToItem(parent, QPointF()).y()
                bottom = top + item.height()
                if top < 8:
                    parent.setProperty("contentY", max(0, float(offset) + top - 8))
                elif bottom > parent.height() - 8:
                    parent.setProperty(
                        "contentY", float(offset) + bottom - parent.height() + 8
                    )
                surface.settle()
            parent = parent.parentItem()
        return item

    def click(self, surface, name):
        item = self.reveal(surface, name)
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(surface.window, Qt.LeftButton, pos=point)
        surface.settle()
        return item

    def text(self, surface, name, value):
        item = self.click(surface, name)
        item.forceActiveFocus()
        QTest.keyClick(surface.window, Qt.Key_A, Qt.ControlModifier)
        QTest.keyClick(surface.window, Qt.Key_Backspace)
        for char in value:
            QTest.keyClick(surface.window, char)
        surface.settle()
        return item

    def test_all_production_views_create_without_warnings_at_three_widths(self):
        for screen in SCREENS:
            for width in (360, 800, 1100):
                with self.subTest(screen=screen, width=width):
                    surface = Surface(screen, width, 740)
                    try:
                        self.assertFalse(surface.warnings, surface.warnings)
                        self.assertFalse(surface.window.grabWindow().isNull())
                    finally:
                        surface.close()

    def test_debug_search_levels_selection_and_read_only_inspection(self):
        surface = self.surface("debug")
        self.click(surface, "debugEvent_1")
        self.assertEqual(surface.debug.selected_entry["eventId"], 1)
        self.text(surface, "debugSearch", "no match")
        self.assertEqual(surface.debug.entries_model.rowCount(), 0)
        self.text(surface, "debugSearch", "")
        self.click(surface, "debugLevel_ERROR")
        self.assertEqual(surface.debug.entries_model.rowCount(), 0)
        self.click(surface, "debugLevel_ERROR")
        self.click(surface, "debugEvent_1")
        self.click(surface, "debugInspect")
        self.assertTrue(surface.debug.error_visible)
        self.assertFalse(surface.debug.can_retry)
        self.assertEqual(surface.debug.error_command, "print('fixture')")
        self.assertFalse(surface.warnings, surface.warnings)

    def test_model_list_uses_declared_gap_between_real_rows(self):
        surface = self.surface("debug")
        surface.debug.log("ERROR", "Second fixture event")
        surface.settle()
        first = self.raw(surface, "debugEvent_1")
        second = self.raw(surface, "debugEvent_2")
        self.assertEqual(
            second.mapToScene(QPointF()).y() - first.mapToScene(QPointF()).y(), 62
        )
        self.assertEqual(first.height(), 60)
        self.assertFalse(surface.warnings, surface.warnings)

    def test_debug_command_and_details_are_not_truncated(self):
        surface = self.surface("debug")
        command = "print(" + repr("payload" * 20000) + ")"
        surface.debug.log(
            "ERROR", "Large diagnostic", command=command, details="detail" * 20000
        )
        surface.settle()
        surface.debug.select_entry(surface.debug.entries_model.rowCount() - 1)
        surface.settle()
        self.assertEqual(self.raw(surface, "debugCommand").property("text"), command)
        surface.debug.copy_selected_command()
        self.assertEqual(surface.app.clipboard().text(), command)
        self.assertFalse(surface.warnings, surface.warnings)

    def test_performance_selection_recording_and_clear_use_real_monitor(self):
        surface = self.surface("performance")
        self.click(surface, "sample_1")
        self.assertIn(
            "Fixture details",
            self.raw(surface, "uiMeasurementDetails").property("text"),
        )
        self.click(surface, "pauseUiMeasurements")
        self.assertTrue(surface.performance.recording)
        self.click(surface, "clearUiMeasurements")
        self.assertEqual(surface.performance.summary["count"], 0)
        self.assertIn(
            "Select a measurement",
            self.raw(surface, "uiMeasurementDetails").property("text"),
        )
        self.assertFalse(surface.warnings, surface.warnings)

    def test_keyboard_reveals_virtualized_measurement_before_focusing(self):
        surface = self.surface("performance")
        sample = surface.performance.model.get(0)
        surface.performance._samples.clear()
        surface.performance._samples.extend(
            dict(sample, sampleId=index, action="Sample " + str(index))
            for index in range(1, 251)
        )
        surface.performance.set_visible(True)
        surface.settle()
        self.click(surface, "sample_1")
        QTest.keyClick(surface.window, Qt.Key_End)
        surface.settle()
        self.assertEqual(
            variant(surface.view.property("selectedSample"))["sampleId"], 250
        )
        self.assertTrue(self.raw(surface, "sample_250").hasActiveFocus())
        self.assertGreater(
            self.raw(surface, "uiPerformanceSamples").property("contentY"), 0
        )
        QTest.keyClick(surface.window, Qt.Key_Home)
        surface.settle()
        self.assertEqual(
            variant(surface.view.property("selectedSample"))["sampleId"], 1
        )
        self.assertTrue(self.raw(surface, "sample_1").hasActiveFocus())
        self.assertFalse(surface.warnings, surface.warnings)

    def test_profile_tasks_use_viewed_login_and_server_values(self):
        surface = self.surface("profile")
        controller = self.controller(surface, "userController")
        profile = variant(controller.property("profile"))
        profile.update(login="other_artist", current=False)
        controller.setProperty("profile", profile)
        surface.settle()
        self.click(surface, "profileOpenTasks")
        self.assertEqual(
            variant(
                self.controller(surface, "tasksController").property("lastCommand")
            )["login"],
            "other_artist",
        )
        evaluate(
            surface.engine,
            self.raw(surface, "profileTask_statusSummary_0"),
            "focusEditor()",
        )
        QTest.keyClick(surface.window, Qt.Key_Space)
        surface.settle()
        command = variant(
            self.controller(surface, "tasksController").property("lastCommand")
        )
        self.assertEqual(
            command, {"login": "other_artist", "key": "status", "value": "in_progress"}
        )
        self.assertFalse(surface.warnings, surface.warnings)

    def test_profile_and_memberships_use_one_existing_mutation(self):
        from thlib.environment import env_inst
        from thlib.ui.user import UserController
        import thlib.tactic_classes as tc

        controller = UserController.__new__(UserController)
        QObject.__init__(controller)
        controller._profile = {"login": "artist", "current": False}
        controller._current_login = lambda: "admin"
        controller._edit_busy = False
        operations = []
        worker = SimpleNamespace(result=Mock(), error=Mock(), start=Mock())
        pool = SimpleNamespace(
            is_stopped=False,
            add_task=lambda operation: operations.append(operation) or worker,
        )
        with (
            patch.object(env_inst, "server_pool", pool),
            patch.object(tc, "mutate_user_profile") as mutate,
        ):
            self.assertTrue(
                controller.save_profile(
                    {
                        "address": "Studio",
                        "password": "fixture",
                        "unexpected": "ignored",
                    },
                    ["artists"],
                    {" artists ": " high "},
                )
            )
            self.assertFalse(controller.save_profile({"address": "Second"}))
            self.assertEqual(len(operations), 1)
            operations[0]()
            mutate.assert_called_once_with(
                "artist",
                values={"address": "Studio"},
                password="fixture",
                groups=["artists"],
                group_access_levels={"artists": "high"},
            )
            controller._edit_busy = False
            mutate.reset_mock()
            self.assertTrue(controller.save_group_settings(None, None))
            operations[1]()
            mutate.assert_called_once_with(
                "artist", values={}, password="", groups=[], group_access_levels={}
            )
        controller.deleteLater()

    def test_profile_editor_preserves_address_and_guards_dirty_close(self):
        surface = self.surface("editor")
        self.text(surface, "profileField_address", "Studio 8")
        self.text(surface, "profileField_password", "temporary-fixture")
        self.click(surface, "userProfileEditorCancel")
        self.assertTrue(surface.view.property("confirmClose"))
        self.assertTrue(surface.view.property("visible"))
        self.click(surface, "profileKeepEditing")
        self.click(surface, "userProfileEditorSave")
        command = variant(
            self.controller(surface, "userController").property("lastCommand")
        )
        self.assertEqual(command["type"], "save")
        self.assertEqual(command["values"]["address"], "Studio 8")
        self.assertEqual(command["values"]["password"], "temporary-fixture")
        self.assertIsNone(
            command.get("groups"), "A profile-only edit must not rewrite memberships"
        )
        self.assertEqual(variant(surface.view.property("draft"))["password"], "")
        self.controller(surface, "userController").profileSaved.emit()
        surface.settle()
        self.assertFalse(surface.view.property("visible"))
        self.assertEqual(variant(surface.view.property("draft")), None)
        self.assertFalse(surface.warnings, surface.warnings)

    def test_profile_editor_memberships_and_unknown_write_lock(self):
        surface = self.surface("editor")
        self.text(surface, "profileField_address", "Retained across tabs")
        self.click(surface, "profileEditorTab_groups")
        self.click(surface, "profileGroup_reviewers")
        self.click(surface, "userProfileEditorSave")
        controller = self.controller(surface, "userController")
        self.assertEqual(
            set(variant(controller.property("lastCommand"))["groups"]),
            {"artists", "reviewers"},
        )
        self.assertEqual(
            variant(controller.property("lastCommand"))["values"]["address"],
            "Retained across tabs",
        )
        controller.setProperty("editingError", "Request result is unknown")
        controller.stateChanged.emit()
        surface.settle()
        self.assertTrue(surface.view.property("uncertain"))
        self.assertFalse(self.raw(surface, "userProfileEditorSave").property("enabled"))
        self.click(surface, "userProfileEditorCancel")
        self.click(surface, "profileDiscard")
        self.assertEqual(variant(surface.view.property("draft")), None)
        self.assertFalse(surface.warnings, surface.warnings)

    def test_touch_help_and_parent_close_guard_use_real_controls(self):
        surface = self.surface("sign_in", 440, 470)
        item = self.reveal(surface, "signInHelp")
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        QTest.touchEvent(surface.window, device).press(
            0, point, surface.window
        ).commit()
        surface.settle()
        QTest.touchEvent(surface.window, device).release(
            0, point, surface.window
        ).commit()
        surface.settle()
        self.assertEqual(
            self.controller(surface, "windowModel").property("lastHelp"),
            "getting_started",
        )
        self.assertFalse(surface.warnings, surface.warnings)
        surface.close()
        surface = self.surface("profile")
        self.click(surface, "profileEdit")
        self.text(surface, "profileField_address", "Unsaved studio")
        self.assertFalse(evaluate(surface.engine, surface.view, "requestClose()"))
        surface.settle()
        self.assertTrue(surface.window.isVisible())
        self.click(surface, "profileKeepEditing")
        self.assertEqual(
            self.raw(surface, "profileField_address").property("text"), "Unsaved studio"
        )
        self.assertFalse(evaluate(surface.engine, surface.view, "requestClose()"))
        surface.settle()
        self.click(surface, "profileDiscard")
        self.assertFalse(surface.window.isVisible())
        self.assertFalse(surface.warnings, surface.warnings)

    def test_login_actual_return_submits_only_complete_credentials_and_clears_secret(
        self,
    ):
        surface = self.surface("sign_in", 440, 470)
        controller = self.controller(surface, "appController")
        self.assertFalse(self.raw(surface, "signInSubmit").property("enabled"))
        self.text(surface, "signIn_password", "temporary-fixture")
        QTest.keyClick(surface.window, Qt.Key_Return)
        surface.settle()
        command = variant(controller.property("lastCommand"))
        self.assertEqual(
            command,
            {
                "type": "authenticate",
                "login": "artist",
                "password": "temporary-fixture",
            },
        )
        controller.setProperty("authentication_dialog_visible", False)
        surface.settle()
        self.assertEqual(surface.view.property("password"), "")
        self.assertFalse(surface.warnings, surface.warnings)

    def test_presets_protect_default_and_push_draft_without_saving(self):
        surface = self.surface("presets")
        controller = self.controller(surface, "serverPresetsController")
        transport = self.raw(surface, "preset_rpcTransport")
        self.assertEqual(transport.property("currentValue"), "xmlrpc")
        transport.forceActiveFocus()
        QTest.keyClick(surface.window, Qt.Key_Down)
        surface.settle()
        self.assertEqual(
            variant(controller.property("lastCommand"))["values"]["rpcTransport"],
            "json",
        )
        self.text(surface, "preset_serverUrl", "https://another.example.test")
        command = variant(controller.property("lastCommand"))
        self.assertEqual(command["type"], "update")
        self.assertEqual(command["values"]["serverUrl"], "https://another.example.test")
        self.assertFalse(self.raw(surface, "presetRemove_default").property("enabled"))
        self.click(surface, "presetCancel")
        self.assertEqual(variant(controller.property("lastCommand"))["type"], "cancel")
        self.assertEqual(variant(surface.view.property("values")), {})
        self.assertFalse(surface.warnings, surface.warnings)

    def test_update_generator_resolves_every_visible_icon(self):
        surface = self.surface("updates")
        surface.view.setProperty("createMode", True)
        surface.settle()
        for item in sidebar_fixture.SidebarEditorQmlTests.descendants(
            surface.window.contentItem()
        ):
            if item.objectName() == "materialIconGlyph" and item.isVisible():
                self.assertTrue(
                    any(
                        item.property(field)
                        for field in ("fontAwesomeName", "materialName", "catalogGlyph")
                    ),
                    item.parentItem().property("name"),
                )
        self.assertFalse(surface.warnings, surface.warnings)

    def test_update_confirmation_cancel_and_accept_use_existing_owner(self):
        surface = self.surface("updates")
        controller = self.controller(surface, "updateController")
        self.click(surface, "installSelectedVersion")
        self.click(surface, "confirmationReject")
        self.assertNotEqual(
            variant(controller.property("lastCommand")).get("type"), "install"
        )
        self.click(surface, "installSelectedVersion")
        self.click(surface, "confirmationAccept")
        self.assertEqual(variant(controller.property("lastCommand"))["type"], "install")
        self.assertFalse(surface.warnings, surface.warnings)

    def test_update_generator_steps_and_rejects_invalid_version(self):
        surface = self.surface("updates")
        surface.view.setProperty("createMode", True)
        surface.settle()
        self.text(surface, "update_revision", "999")
        self.click(surface, "updatePlus_revision")
        self.assertEqual(variant(surface.view.property("draft"))["revision"], "999")
        self.text(surface, "update_revision", "no")
        self.assertFalse(
            self.raw(surface, "createUpdateArchiveButton").property("enabled")
        )
        self.text(surface, "update_revision", "108")
        self.click(surface, "createUpdateArchiveButton")
        command = variant(
            self.controller(surface, "updateController").property("lastCommand")
        )
        self.assertEqual(command["type"], "create")
        self.assertEqual(command["revision"], 108)
        self.assertFalse(surface.warnings, surface.warnings)

    def test_error_keeps_full_trace_copy_and_contextual_help(self):
        surface = self.surface("error")
        surface.debug._error_stacktrace = "Traceback fixture\n" + "detail" * 20000
        surface.debug._error_message = "Fixture error"
        surface.debug._error_title = "Application error"
        surface.debug.error_changed.emit()
        surface.settle()
        self.click(surface, "copyErrorStacktrace")
        self.assertEqual(surface.app.clipboard().text(), surface.debug.error_stacktrace)
        self.click(surface, "toggleErrorStacktrace")
        self.assertEqual(
            self.raw(surface, "errorStacktrace").property("text"),
            surface.debug.error_stacktrace,
        )
        self.click(surface, "errorHelp")
        self.assertEqual(
            self.controller(surface, "windowModel").property("lastHelp"), "errors"
        )
        self.assertFalse(surface.warnings, surface.warnings)


if __name__ == "__main__":
    unittest.main()
