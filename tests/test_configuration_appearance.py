"""Independent Appearance/Global drafts through their owners and real QML routes."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import (
    QEvent, QObject, QPointF, Property, Qt, QUrl, Signal, Slot,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from thlib.environment import env_mode
from thlib.ui.application_composition import ConfigurationBridge
from thlib.ui.configuration import ConfigurationController
from thlib.ui.controller import ApplicationController
from thlib.ui.localization import LocalizationController


QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


def visual_items(item):
    yield item
    for child in item.childItems():
        yield from visual_items(child)


class _NotificationPreference(QObject):
    notificationsEnabledChanged = Signal()

    def __init__(self):
        super().__init__()
        self._enabled = True

    @Property(bool, notify=notificationsEnabledChanged)
    def notificationsEnabled(self):
        return self._enabled

    @Slot(bool)
    def set_notifications_enabled(self, value):
        self._enabled = bool(value)
        self.notificationsEnabledChanged.emit()


class AppearanceConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))
        for method in ("_server_values", "_checkin_values"):
            self.enterContext(patch.object(ConfigurationController, method, return_value={}))
        self.controller = ApplicationController()
        self.addCleanup(self.controller.shutdown)
        self.localization = LocalizationController(self.app, self.controller)
        self.localization.set_language("ru")
        self.addCleanup(self.localization.set_language, "en")
        bridge = ConfigurationBridge(SimpleNamespace(
            controller=self.controller, localization=self.localization,
        ), None, None, None)
        self.config = ConfigurationController(
            lambda *_args: self.fail("Unexpected server write"), self.fail,
            global_values=bridge.global_values,
            apply_global_configuration=bridge.apply_global,
            appearance_values=bridge.appearance_values,
            apply_appearance_configuration=bridge.apply_appearance,
        )
        self.config.begin_session()
        self.addCleanup(self.config.deleteLater)
        self.activity_notifications = _NotificationPreference()
        self.message_notifications = _NotificationPreference()

    def draft(self, page, **changes):
        values = self.config.page_values(page)
        values.update(changes)
        self.config.update_page(page, values)

    def test_applying_one_page_preserves_other_pending_and_persisted_values(self):
        self.draft("global_preferences", closeToTray=False)
        self.draft("appearance", popupAnimations=False, renderBackend="software")
        self.config.select_page("global_preferences")
        self.assertTrue(self.config.apply_current())
        self.assertFalse(self.controller.close_to_tray_enabled())
        self.assertTrue(self.controller.popup_animations_enabled)
        self.assertEqual(self.controller.configuration_appearance_values()["renderBackend"], "automatic")
        self.assertFalse(self.config.page_values("appearance")["popupAnimations"])
        self.assertTrue(self.config.dirty)

        self.config.select_page("appearance")
        self.assertTrue(self.config.apply_current())
        self.assertFalse(self.controller.popup_animations_enabled)
        self.assertFalse(self.controller.close_to_tray_enabled())
        self.assertFalse(self.config.dirty)
        self.assertNotIn("renderBackend", self.config.page_values("global_preferences"))
        self.assertNotIn("closeToTray", self.config.page_values("appearance"))

        restored = ApplicationController()
        try:
            self.assertFalse(restored.popup_animations_enabled)
            self.assertFalse(restored.close_to_tray_enabled())
            self.assertEqual(restored.configuration_appearance_values()["renderBackend"], "software")
        finally:
            restored.shutdown()

    def test_reset_discard_and_save_keep_page_drafts_independent(self):
        original = self.config.page_values("appearance")
        self.draft("appearance", popupAnimations=False)
        self.draft("global_preferences", closeToTray=False)
        self.config.select_page("appearance")
        self.assertTrue(self.config.can_reset_current_page)
        self.config.reset_current()
        self.assertEqual(self.config.page_values("appearance"), original)
        self.assertFalse(self.config.page_values("global_preferences")["closeToTray"])
        self.config.discard_and_close()
        self.assertTrue(self.controller.close_to_tray_enabled())
        self.assertFalse(self.config.dirty)

        self.config.begin_session()
        self.draft("global_preferences", closeToTray=False)
        self.draft("appearance", popupAnimations=False)
        closed = QSignalSpy(self.config.closeAllowed)
        self.config.save_and_close()
        self.assertEqual(closed.count(), 1)
        self.assertFalse(self.controller.close_to_tray_enabled())
        self.assertFalse(self.controller.popup_animations_enabled)

    def test_sidebar_loads_separate_forms_and_preserves_edits_between_them(self):
        self.config.select_page("appearance")
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(lambda items: warnings.extend(w.toString() for w in items))
        for name, value in {
            "appController": self.controller,
            "configurationController": self.config,
            "localizationController": self.localization,
            "activityFeedController": self.activity_notifications,
            "messagesController": self.message_notifications,
            "configPageModel": self.controller.workspace_state.configuration_page_model,
        }.items():
            engine.rootContext().setContextProperty(name, value)
        component = QQmlComponent(engine)
        component.setData(b'''import QtQuick
import QtQuick.Window
import "." as App
Window {
    width: 1000; height: 720; visible: true
    App.Theme { id: theme; dark: true }
    App.ConfigurationView {
        anchors.fill: parent; theme: theme; windowId: "configuration"
    }
}''', QUrl.fromLocalFile(str(QML / "_AppearanceConfigurationTest.qml")))
        window = component.create()
        self.assertIsNotNone(window, "\n".join(e.toString() for e in component.errors()))
        try:
            self.assertTrue(QTest.qWaitForWindowExposed(window))
            popup = window.findChild(QObject, "popupAnimationsSwitch")
            self.assertIsNotNone(popup)
            self.assertIsNotNone(window.findChild(QObject, "renderBackendCombo"))
            self.assertEqual(window.findChildren(QObject, "closeToTraySwitch"), [])
            popup.setProperty("checked", False)
            popup.toggled.emit()
            self.assertTrue(self.config.dirty)

            for page in ("global_preferences", "appearance"):
                item = next(item for item in visual_items(window.contentItem())
                            if item.objectName() == "configurationPage_" + page)
                point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
                QTest.mouseClick(window, Qt.LeftButton, pos=point.toPoint())
                self.app.processEvents()
                self.assertEqual(self.config.current_page, page)
                if page == "global_preferences":
                    self.assertIsNone(window.findChild(QObject, "popupAnimationsSwitch"))
                    self.assertIsNone(window.findChild(QObject, "renderBackendCombo"))
                    self.assertIsNotNone(
                        window.findChild(QObject, "serverThreadsSpinBox")
                    )
                    self.assertIsNotNone(
                        window.findChild(QObject, "localThreadsSpinBox")
                    )
                    activity_switch = window.findChild(
                        QQuickItem, "activityFeedNotificationsSwitch"
                    )
                    self.assertIsNotNone(activity_switch)
                    self.assertTrue(activity_switch.property("checked"))
                    point = activity_switch.mapToScene(QPointF(
                        activity_switch.width() / 2,
                        activity_switch.height() / 2,
                    ))
                    QTest.mouseClick(
                        window, Qt.LeftButton, pos=point.toPoint()
                    )
                    self.assertFalse(
                        self.activity_notifications.notificationsEnabled
                    )
                    message_switch = window.findChild(
                        QQuickItem, "messageNotificationsSwitch"
                    )
                    self.assertIsNotNone(message_switch)
                    self.assertTrue(message_switch.property("checked"))
                    point = message_switch.mapToScene(QPointF(
                        message_switch.width() / 2,
                        message_switch.height() / 2,
                    ))
                    QTest.mouseClick(
                        window, Qt.LeftButton, pos=point.toPoint()
                    )
                    self.assertFalse(
                        self.message_notifications.notificationsEnabled
                    )
                else:
                    popup = window.findChild(QObject, "popupAnimationsSwitch")
                    self.assertFalse(popup.property("checked"))
                    apply = window.findChild(QQuickItem, "configurationApply")
                    point = apply.mapToScene(QPointF(apply.width() / 2, apply.height() / 2))
                    QTest.mouseClick(window, Qt.LeftButton, pos=point.toPoint())
                    self.assertFalse(self.controller.popup_animations_enabled)
                    self.assertFalse(self.config.dirty)
        finally:
            window.close()
            window.deleteLater()
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
            engine.deleteLater()
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertEqual(warnings, [])
