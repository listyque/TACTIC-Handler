"""Configuration through real Frame controls and the existing draft owners."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
from PySide6.QtCore import QObject, QPoint, QPointF, QMetaObject, Qt, QUrl
from PySide6.QtGui import QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from thlib.environment import env_server
from thlib.ui.localization import CatalogTranslator
from tests.frame_configuration_fixture import Surface, QML
from tests import test_configuration_appearance as appearance_fixture

ROOT = Path(__file__).resolve().parents[1]


class ConfigurationLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        appearance_fixture.AppearanceConfigurationTests.setUpClass()
        cls.app = appearance_fixture.AppearanceConfigurationTests.app

    def surface(self, screen, width=800, **kwargs):
        surface = Surface(screen, width, 740, **kwargs)
        self.addCleanup(surface.close)
        self.addCleanup(lambda: self.assertEqual(surface.warnings, []))
        return surface

    def reveal(self, surface, name):
        item = surface.item(name)
        parent = item.parentItem()
        while parent:
            if parent.property("contentY") is not None:
                point = item.mapToItem(parent, QPointF(0, 0))
                offset = parent.property("contentY")
                if point.y() < 0:
                    parent.setProperty("contentY", offset + point.y())
                elif point.y() + item.height() > parent.height():
                    parent.setProperty(
                        "contentY", offset + point.y() + item.height() - parent.height()
                    )
            parent = parent.parentItem()
        surface.settle()
        return item

    def click(self, surface, name):
        item = self.reveal(surface, name)
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
        QTest.mouseClick(surface.window, Qt.LeftButton, pos=point)
        surface.settle()
        return item

    def type(self, surface, name, text):
        item = self.click(surface, name)
        QTest.keyClick(surface.window, Qt.Key_A, Qt.ControlModifier)
        for character in text:
            QTest.keyClick(surface.window, character)
        surface.settle()
        return item

    def test_global_page_handler_server_autostart_switch(self):
        surface = self.surface("global")
        self.click(surface, "setting_autoStartHandlerServer")
        self.assertFalse(
            surface.case.config.page_values("global_preferences")[
                "autoStartHandlerServer"
            ]
        )
        self.assertTrue(surface.case.config.dirty)
        self.assertTrue(surface.case.config.apply_current())
        self.assertFalse(surface.case.config.dirty)

    def test_server_transport_labels_in_russian(self):
        surface = self.surface("server", language="ru")
        combo = surface.item("setting_rpcTransport")
        self.assertEqual(combo.property("currentValue"), "xmlrpc")
        combo.forceActiveFocus()
        QTest.keyClick(surface.window, Qt.Key_Down)
        surface.settle()
        self.assertEqual(
            surface.case.config.page_values("server")["rpcTransport"], "json"
        )
        self.assertIn("JSON", combo.property("displayText"))

    def test_server_page_uses_one_background_interval_at_both_widths(self):
        surface = self.surface("server")
        self.assertEqual(
            surface.item("setting_serverUpdateInterval").property("currentValue"), 30
        )
        self.assertFalse(
            any(
                field.get("field") == "serverUpdateInterval"
                and field.get("when") is False
                for field in surface.evaluate("fields")
            )
        )
        for width in (360, 980):
            surface.window.setWidth(width)
            surface.view.setWidth(width)
            surface.settle()
            item = self.reveal(surface, "setting_serverUpdateInterval")
            point = item.mapToScene(QPointF(0, 0))
            self.assertGreaterEqual(point.x(), 0)
            self.assertLessEqual(point.x() + item.width(), width)

    def test_configuration_header_help_opens_current_page_article(self):
        surface = self.surface("configuration", 1100)
        for page, topic in [
            ("cache", "configuration.cache"),
            ("appearance", "appearance"),
            ("global_preferences", "configuration.global"),
        ]:
            surface.case.config.select_page(page)
            surface.settle()
            self.click(surface, "configurationHelp")
            self.assertEqual(surface.windows.calls[-1], ("help", topic))

    def test_manifest_dcc_preferences_render_and_update(self):
        surface = self.surface("dcc")
        page_id = surface.view.property("pageId")
        field = self.reveal(surface, "setting_current_workdir")
        self.assertTrue(field.property("readOnly"))
        before = surface.case.config.page_values(page_id)["focus_after_open"]
        self.click(surface, "setting_focus_after_open")
        self.assertEqual(
            surface.case.config.page_values(page_id)["focus_after_open"], not before
        )

    def test_configuration_dirty_confirmation_keeps_or_discards_the_real_draft(self):
        surface = self.surface("configuration")
        config = surface.case.config
        values = config.page_values("appearance")
        values["darkTheme"] = not values["darkTheme"]
        config.update_page("appearance", values)

        def popup_click(name):
            dialog = surface.evaluate("unsavedDialog")
            self.assertTrue(dialog.property("modal"))
            self.assertTrue(dialog.property("visible"))
            content = dialog.property("contentItem")
            children = [content]
            for item in children:
                children.extend(item.childItems())
            control = next(item for item in children if item.objectName() == name)
            QTest.mouseClick(
                control.window(),
                Qt.LeftButton,
                pos=control.mapToScene(
                    QPointF(control.width() / 2, control.height() / 2)
                ).toPoint(),
            )
            surface.settle()
            self.assertFalse(dialog.property("visible"))

        config.request_close()
        surface.settle()
        popup_click("configurationConfirm_keep")
        self.assertTrue(config.dirty)
        config.request_close()
        surface.settle()
        popup_click("configurationConfirm_discard")
        self.assertFalse(config.dirty)

    def test_cache_and_connection_busy_states_use_their_existing_owners(self):
        surface = self.surface("cache")
        surface.cache._busy = True
        surface.cache._message = "Clearing fixture cache"
        surface.cache.stateChanged.emit()
        surface.settle()
        self.assertFalse(surface.item("setting_clearData").isEnabled())
        self.assertEqual(
            surface.item("configurationNotice").property("text"),
            "Clearing fixture cache",
        )
        surface.cache._clear_finished(None)
        surface.settle()
        self.assertTrue(surface.item("setting_clearData").isEnabled())
        self.assertEqual(
            surface.item("configurationNotice").property("text"),
            "Cached server data cleared",
        )
        server = self.surface("server")
        server.case.config._set_server_test(
            True, "testing", "Testing fixture connection"
        )
        server.settle()
        self.assertFalse(server.item("setting_test").isEnabled())
        self.assertFalse(server.item("setting_signIn").isEnabled())

    def test_long_setting_captions_keep_complete_word_wrapped_lines(self):
        surface = self.surface("tasks", 800)
        for language in ("en", "ru"):
            surface.case.localization.set_language(language)
            for width in (360, 800, 1100):
                surface.window.setWidth(width)
                surface.view.setWidth(width)
                surface.settle()
                for name in ("sortMode", "groupMode", "quickViewMode"):
                    item = surface.item("setting_" + name + "Description")
                    self.assertLessEqual(
                        item.property("contentHeight"), item.height() + 0.5
                    )

    def test_task_preferences_load_surface_and_quick_view_choices(self):
        surface = self.surface("tasks")
        combo = surface.item("setting_workspaceSurface")
        old = combo.property("currentValue")
        combo.forceActiveFocus()
        QTest.keyClick(surface.window, Qt.Key_Down)
        surface.settle()
        self.assertNotEqual(
            surface.case.config.page_values("tasks_preferences")["workspaceSurface"],
            old,
        )
        quick = surface.item("setting_quickViewMode")
        self.assertIn(quick.property("currentValue"), ("cards", "compact"))

    def test_appearance_picker_updates_independent_preferences(self):
        surface = self.surface("appearance")
        self.click(surface, "setting_popupAnimations")
        self.assertFalse(
            surface.case.config.page_values("appearance")["popupAnimations"]
        )
        self.assertTrue(surface.case.config.dirty)
        surface.case.config.reset_current()
        surface.settle()
        self.assertTrue(surface.item("setting_popupAnimations").property("checked"))
        self.assertFalse(surface.case.config.dirty)

    def test_server_presets_save_preserves_other_configuration_drafts(self):
        surface = self.surface("appearance")
        self.click(surface, "setting_popupAnimations")
        surface.case.config.refresh_server_presets()
        self.assertFalse(
            surface.case.config.page_values("appearance")["popupAnimations"]
        )
        self.assertIn("appearance", surface.case.config.dirty_pages)

    def test_checkin_rows_have_width_and_do_not_overlap(self):
        surface = self.surface("checkin")
        definitions = surface.evaluate("fields")
        self.assertGreaterEqual(
            len([field for field in definitions if field.get("field")]), 35
        )
        for width in (360, 1100):
            surface.window.setWidth(width)
            surface.view.setWidth(width)
            surface.settle()
            for name in (
                "setting_displayLimitInput",
                "setting_descriptionLimitInput",
                "setting_sequencePaddingInput",
                "setting_minimumFramePaddingInput",
            ):
                item = self.reveal(surface, name)
                point = item.mapToScene(QPointF(0, 0))
                self.assertGreater(item.width(), 20)
                self.assertGreaterEqual(point.x(), 0)
                self.assertLessEqual(point.x() + item.width(), width)

    def test_team_repository_sync_requires_dialog_acceptance(self):
        with patch.object(env_server, "is_team_local_repository", return_value=True):
            surface = self.surface("repository_editor", 1100)
            self.click(surface, "repositorySync")
            dialog = surface.view.findChild(QObject, "teamRepositorySyncDialog")
            self.assertTrue(dialog.property("opened"))
            self.assertEqual(surface.repositories.sync_calls, 0)
            QMetaObject.invokeMethod(dialog, "reject")
            surface.settle()
            self.assertEqual(surface.repositories.sync_calls, 0)
            self.click(surface, "repositorySync")
            QMetaObject.invokeMethod(dialog, "accept")
            surface.settle()
            self.assertEqual(surface.repositories.sync_calls, 1)

    def test_cache_page_reflows_and_keeps_its_shared_scrollbar(self):
        surface = self.surface("cache", 360)
        bar = surface.item("configurationSettingsScrollBar")
        self.assertTrue(bar.property("hasOverflow"))
        self.assertGreater(bar.width(), 0)
        switch = self.reveal(surface, "setting_cacheProcessTabs")
        point = switch.mapToScene(
            QPointF(switch.width() / 2, switch.height() / 2)
        ).toPoint()
        device = QTest.createTouchDevice()
        tap = QTest.touchEvent(surface.window, device, autoCommit=False)
        tap.press(0, point, surface.window).commit()
        self.app.processEvents()
        tap.release(0, point, surface.window).commit()
        surface.settle()
        self.assertFalse(surface.case.config.page_values("cache")["cacheProcessTabs"])

    def test_settings_scroll_with_mouse_wheel_and_trackpad(self):
        for screen in ("cache", "server", "checkin"):
            with self.subTest(screen=screen):
                surface = self.surface(screen, 360)
                view = surface.item("configurationSettings")
                bar = surface.item("configurationSettingsScrollBar")
                self.assertTrue(bar.isVisible())
                self.assertTrue(bar.property("hasOverflow"))
                point = view.mapToScene(QPointF(20, view.height() / 2))
                for pixels, angle, expected in ((0, -120, 148), (-40, 0, 214), (0, 120, 66)):
                    event = QWheelEvent(
                        point, QPointF(surface.window.mapToGlobal(point.toPoint())),
                        QPoint(0, pixels), QPoint(0, angle), Qt.NoButton,
                        Qt.NoModifier, Qt.NoScrollPhase, False,
                    )
                    self.app.sendEvent(surface.window, event)
                    surface.settle()
                    self.assertAlmostEqual(view.property("contentY"), expected)
                surface.close()

    def test_repository_page_reflows_and_keeps_primary_action_visible(self):
        surface = self.surface("repositories", 360)
        self.click(surface, "setting_edit")
        self.assertEqual(surface.windows.calls[-1], ("show", "repository_editor"))

    def test_project_list_reflows_without_clipping_on_narrow_and_wide_windows(self):
        surface = self.surface("projects", 360)
        self.click(surface, "configurationProject_cg")
        self.assertEqual(surface.evaluate("selected.code"), "cg")
        surface.window.setWidth(1100)
        surface.view.setWidth(1100)
        surface.settle()
        self.click(surface, "configurationProjectAction_edit")
        self.assertEqual(surface.evaluate("selected.code"), "cg")
        self.assertGreater(surface.item("configurationProjects").width(), 300)
        for width in (360, 1100):
            surface.window.setWidth(width)
            surface.view.setWidth(width)
            surface.settle()
            panel = surface.item("configurationProjectsPanel")
            listing = surface.item("configurationProjects")
            details = surface.item("configurationProjectDetailsPanel")
            self.assertEqual(listing.mapToScene(QPointF()).x() -
                             panel.mapToScene(QPointF()).x(), 12)
            self.assertEqual(panel.width() - listing.width(), 24)
            self.assertGreaterEqual(panel.height(), listing.height() + 48)
            self.assertTrue(details.isVisible())
            self.assertTrue(surface.item("configurationProjectsFooterDivider").isVisible())

    def test_missing_repository_opens_one_modal_setup_prompt(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b"""import QtQuick
import QtQuick.Window
import "." as App

Window {
    width: 640
    height: 480
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: applicationController
        signal server_state_changed()
        property string server_state: "online"
    }
    QtObject {
        id: configurationController
        function select_page(pageId) {}
    }
    QtObject {
        id: repositoryController
        signal configurationChanged()
        property bool configuration_loaded: true
        property bool configuration_required: true
        function begin_edit() {}
    }
    QtObject {
        id: windows
        function show_window(windowId) {}
    }

    App.RepositorySetupPrompt {
        anchors.fill: parent
        theme: theme
        applicationController: applicationController
        configurationController: configurationController
        repositoryController: repositoryController
        windows: windows
        smokeMode: false
    }
}
""",
            QUrl.fromLocalFile(str(QML / "_RepositoryPromptTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(80)
            prompt = owner.findChild(QObject, "repositorySetupPrompt")
            self.assertIsNotNone(prompt)
            self.assertTrue(prompt.property("opened"))
            self.assertTrue(prompt.property("modal"))
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()

    def test_quick_project_chooser_keeps_filters_and_square_previews_separate(self):
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        component = QQmlComponent(engine)
        component.setData(
            b"""import QtQuick
import QtQuick.Controls
import "." as App

ApplicationWindow {
    width: 540
    height: 700
    visible: true

    App.Theme { id: theme; dark: true }
    QtObject {
        id: projectModel
        property bool showRetired: false
        property bool showTemplates: false
        property bool showBuiltins: false
        property int retiredCount: 1
        property int templateCount: 1
        property int builtinCount: 1
        property int visibleCount: 3
        property int totalCount: 5
        property var groups: [{
            "title": "Production",
            "projects": [
                {"code": "one", "title": "Project One",
                 "category": "Production", "projectType": "Animation",
                 "description": "First project", "preview": "",
                 "initials": "PO", "isBuiltin": false,
                 "isTemplate": false, "isRetired": false},
                {"code": "two", "title": "Project Two",
                 "category": "Production", "projectType": "VFX",
                 "description": "Second project", "preview": "",
                 "initials": "PT", "isBuiltin": false,
                 "isTemplate": false, "isRetired": false},
                {"code": "sthpw", "title": "TACTIC system",
                 "category": "System", "projectType": "built-in",
                 "description": "Built-in project", "preview": "",
                 "initials": "TS", "isBuiltin": true,
                 "isTemplate": false, "isRetired": false}
            ]
        }]
        function setShowRetired(value) { showRetired = value }
        function setShowTemplates(value) { showTemplates = value }
        function setShowBuiltins(value) { showBuiltins = value }
    }

    App.ProjectChooser {
        id: chooser
        theme: theme
        model: projectModel
    }
    Component.onCompleted: chooser.open()
}
""",
            QUrl.fromLocalFile(str(QML / "_ProjectChooserLayoutTest.qml")),
        )
        owner = component.create()
        self.assertIsNotNone(
            owner,
            "\n".join(error.toString() for error in component.errors()),
        )
        try:
            QTest.qWait(150)
            scene = owner.findChild(QObject, "projectChooser").property("contentItem")
            visual_items = []
            pending = [scene]
            while pending:
                item = pending.pop()
                visual_items.append(item)
                pending.extend(item.childItems())
            title = next(
                item
                for item in visual_items
                if item.objectName() == "projectChooserTitle"
            )
            filters = next(
                item
                for item in visual_items
                if item.objectName() == "projectFilterToggles"
            )
            previews = [
                item
                for item in visual_items
                if item.objectName() == "projectGridPreview" and item.isVisible()
            ]
            title_position = title.mapToItem(scene, QPointF(0, 0))
            filter_position = filters.mapToItem(scene, QPointF(0, 0))
            self.assertLessEqual(
                title_position.y() + title.height(),
                filter_position.y() + 0.1,
            )
            self.assertEqual(len(previews), 3)
            for preview in previews:
                position = preview.mapToItem(scene, QPointF(0, 0))
                self.assertAlmostEqual(preview.width(), preview.height())
                self.assertGreaterEqual(position.x(), -0.1)
                self.assertLessEqual(position.x() + preview.width(), 540.1)
            image = owner.grabWindow()
            self.assertFalse(image.isNull())
            self.assertEqual((image.width(), image.height()), (540, 700))
        finally:
            owner.close()
            owner.deleteLater()
            engine.deleteLater()
