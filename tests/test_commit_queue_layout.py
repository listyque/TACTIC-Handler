from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import (
    QMetaObject,
    QObject,
    QPointF,
    Property,
    QEvent,
    QUrl,
    Slot,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtTest import QTest

from thlib.ui.commit_queue import CommitQueueController
from thlib.ui.localization import CatalogTranslator


ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "thlib" / "ui" / "qml"


class _ScreenshotController(QObject):
    @Property(bool, constant=True)
    def clipboardHasImage(self):
        return False

    @Slot(str)
    def prepare_for_operation(self, _operation_id):
        pass

    @Slot(str)
    def paste_preview_from_clipboard(self, _operation_id):
        pass


class _NamingEditorController(QObject):
    @Slot(str)
    def prepare_operation(self, _operation_id):
        pass


class _WindowModel(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.child_calls = []
        self.help_calls = []
        self.help_calls = []

    @Slot(str)
    def show_window(self, _window_id):
        pass

    @Slot(str, str)
    def show_child_window(self, window_id, parent_id):
        self.child_calls.append((window_id, parent_id))

    @Slot(str)
    def open_help(self, topic):
        self.help_calls.append(topic)

    @Slot(str)
    def open_help(self, topic):
        self.help_calls.append(topic)


class CommitQueueLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def test_narrow_split_panels_keep_their_content_inside_bounds(self):
        translator = CatalogTranslator(
            QML.parent / "translations" / "ru.json"
        )
        self.app.installTranslator(translator)
        with (
            patch(
                "thlib.ui.commit_queue.env_read_config",
                side_effect=lambda **kwargs: (
                    [] if kwargs.get("filename") == "pending" else {}
                ),
            ),
            patch("thlib.ui.commit_queue.env_write_config"),
        ):
            controller = CommitQueueController()

        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        context = engine.rootContext()
        context.setContextProperty("commitQueueController", controller)
        context.setContextProperty("commitQueueModel", controller.model)
        screenshot_controller = _ScreenshotController(engine)
        naming_editor_controller = _NamingEditorController(engine)
        window_model = _WindowModel(engine)
        context.setContextProperty(
            "screenshotController", screenshot_controller
        )
        context.setContextProperty(
            "namingEditorController", naming_editor_controller
        )
        context.setContextProperty("windowModel", window_model)

        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "CommitQueueView.qml"))
        )
        view = component.createWithInitialProperties({"theme": theme})
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )

        window = QQuickWindow()
        window.resize(760, 640)
        view.setParentItem(window.contentItem())
        view.setWidth(760)
        view.setHeight(640)
        window.show()
        try:
            QTest.qWait(80)
            files_dock = view.findChild(QObject, "commitQueueFilesDock")
            details = view.findChild(QObject, "commitQueueDetailsPanel")
            self.assertIsNotNone(files_dock)
            self.assertIsNotNone(details)

            welcome = view.findChild(QObject, "commitQueueWelcomeState")
            editor = view.findChild(QObject, "commitQueueEditorScroll")
            files_panel = view.findChild(QObject, "commitQueueFilesPanel")
            self.assertIsNotNone(welcome)
            self.assertIsNotNone(editor)
            self.assertIsNotNone(files_panel)
            self.assertTrue(welcome.property("visible"))
            self.assertFalse(editor.property("visible"))
            self.assertFalse(files_panel.property("visible"))
            for object_name in (
                "commitQueueMoveUpButton",
                "commitQueueMoveDownButton",
                "commitQueueClearButton",
                "commitQueueClearCompletedButton",
            ):
                action = view.findChild(QObject, object_name)
                self.assertIsNotNone(action)
                self.assertFalse(action.property("visible"), object_name)

            for object_name in (
                "commitQueueToolbar",
                "commitQueueAutoCleanSwitch",
                "commitQueueFilesPanel",
            ):
                item = view.findChild(QObject, object_name)
                self.assertIsNotNone(item)
                position = item.mapToItem(files_dock, QPointF(0, 0))
                self.assertGreaterEqual(position.x(), -0.1, object_name)
                self.assertLessEqual(
                    position.x() + item.width(),
                    files_dock.width() + 0.1,
                    object_name,
                )

            footer = view.findChild(QObject, "commitQueueActionFooter")
            self.assertIsNotNone(footer)
            footer_position = footer.mapToItem(details, QPointF(0, 0))
            self.assertGreaterEqual(footer_position.x(), -0.1)
            self.assertLessEqual(
                footer_position.x() + footer.width(),
                details.width() + 0.1,
            )
            self.assertTrue(files_dock.property("compactActions"))
            self.assertTrue(details.property("compactActions"))
            self.assertTrue(
                view.findChild(
                    QObject, "commitQueueAutoCleanSwitch"
                ).property("text")
            )
            help_button = view.findChild(
                QObject, "commitQueueHelpButton"
            )
            self.assertIsNotNone(help_button)
            self.assertTrue(help_button.property("visible"))
            self.assertTrue(QMetaObject.invokeMethod(help_button, "clicked"))
            self.assertEqual(window_model.help_calls, ["commit_queue"])

            with tempfile.NamedTemporaryFile(suffix=".ma") as source:
                with patch("thlib.ui.commit_queue.env_write_config"):
                    controller.add_prepared({
                        "searchKey": (
                            "demo/asset?project=demo&code=ASSET001"
                        ),
                        "context": "publish",
                        "process": "publish",
                        "repository": "repo",
                        "mode": "upload",
                        "files": [{
                            "path": source.name,
                            "type": "file",
                        }],
                        "filesDict": [("source", {
                            "t": ["file"], "s": [""], "e": ["ma"],
                            "p": [""], "m": None,
                        })],
                        "updateVersionless": True,
                    }, "Asset publish")
                QTest.qWait(60)
                self.assertFalse(welcome.property("visible"))
                self.assertTrue(editor.property("visible"))
                self.assertTrue(files_panel.property("visible"))
                self.assertTrue(
                    view.findChild(
                        QObject, "commitQueueClearButton"
                    ).property("visible")
                )
                confirmation = view.findChild(
                    QObject, "commitQueueClearConfirmation"
                )
                confirmation_actions = view.findChild(
                    QObject, "commitQueueClearActions"
                )
                self.assertIsNotNone(confirmation)
                self.assertIsNotNone(confirmation_actions)
                self.assertEqual(
                    confirmation_actions.property("horizontalMargin"), 20.0
                )
                self.assertEqual(
                    confirmation_actions.property("verticalMargin"), 16.0
                )
                self.assertTrue(
                    QMetaObject.invokeMethod(confirmation, "open")
                )
                QTest.qWait(40)
                clear_message = view.findChild(
                    QObject, "commitQueueClearMessage"
                )
                cancel_clear = view.findChild(
                    QObject, "commitQueueClearCancelButton"
                )
                accept_clear = view.findChild(
                    QObject, "commitQueueClearAcceptButton"
                )
                self.assertIsNotNone(clear_message)
                self.assertIsNotNone(cancel_clear)
                self.assertIsNotNone(accept_clear)
                accept_position = accept_clear.mapToItem(
                    confirmation_actions, QPointF(0, 0)
                )
                self.assertGreaterEqual(
                    confirmation_actions.width()
                    - accept_position.x() - accept_clear.width(),
                    19.5,
                )
                self.assertGreaterEqual(
                    confirmation_actions.height()
                    - accept_position.y() - accept_clear.height(),
                    15.5,
                )
                self.assertTrue(
                    QMetaObject.invokeMethod(confirmation, "close")
                )
                summary = view.findChild(
                    QObject, "commitQueueOperationSummary"
                )
                settings = view.findChild(
                    QObject, "commitQueuePrimarySettings"
                )
                context_field = view.findChild(
                    QObject, "commitQueueContextField"
                )
                context_chip = view.findChild(
                    QObject, "commitQueueContextChip"
                )
                primary_send = view.findChild(
                    QObject, "commitQueuePrimarySendButton"
                )
                send_overflow = view.findChild(
                    QObject, "commitQueueSendOverflowButton"
                )
                self.assertIsNotNone(summary)
                self.assertIsNotNone(settings)
                self.assertIsNotNone(context_field)
                self.assertIsNotNone(context_chip)
                self.assertIsNotNone(primary_send)
                self.assertIsNotNone(send_overflow)
                advanced_toggle = view.findChild(
                    QObject, "commitQueueAdvancedToggle"
                )
                naming_toggle = view.findChild(
                    QObject, "commitQueueNamingToggle"
                )
                naming_file_name = view.findChild(
                    QObject, "commitQueueNamingFileName"
                )
                self.assertIsNotNone(advanced_toggle)
                self.assertIsNotNone(naming_toggle)
                self.assertIsNotNone(naming_file_name)
                naming_details = view.findChild(QObject, "commitQueueNamingDetails")
                def naming_rows():
                    items = [naming_details]
                    for item in items:
                        if isinstance(item, QQuickItem):
                            items.extend(item.childItems())
                    return [item for item in items if item.objectName().startswith("commitQueueNamingPreviewRow_")]

                self.assertFalse(naming_details.property("active"))
                self.assertEqual(naming_rows(), [])
                view.setProperty("namingPreviewExpanded", True)
                QGuiApplication.processEvents()
                self.assertTrue(naming_details.property("active"))
                self.assertEqual(len(naming_rows()), 1)
                view.setProperty("namingPreviewExpanded", False)
                QGuiApplication.processEvents()
                self.assertEqual(naming_rows(), [])
                self.assertAlmostEqual(
                    advanced_toggle.property("height"),
                    naming_toggle.property("height"),
                    delta=0.1,
                )
                self.assertNotEqual(
                    naming_file_name.property("text"), "ИМЕНОВАНИЕ"
                )
                self.assertFalse(any(
                    child.property("text") == "По умолчанию"
                    for child in view.findChildren(QObject)
                ))
                summary_position = summary.mapToItem(
                    details, QPointF(0, 0)
                )
                self.assertGreaterEqual(summary_position.x(), -0.1)
                self.assertLessEqual(
                    summary_position.x() + summary.width(),
                    details.width() + 0.1,
                )
                self.assertFalse(context_field.property("visible"))
                self.assertTrue(context_chip.property("visible"))
                self.assertEqual(context_chip.property("text"), "Добавить контекст")
                self.assertTrue(
                    QMetaObject.invokeMethod(summary, "beginContextEdit")
                )
                QTest.qWait(20)
                self.assertTrue(context_field.property("visible"))
                self.assertFalse(context_chip.property("visible"))
                self.assertEqual(context_field.property("text"), "")
                context_field.setProperty("text", "review pass")
                self.assertTrue(
                    QMetaObject.invokeMethod(summary, "finishContextEdit")
                )
                QTest.qWait(20)
                self.assertEqual(
                    controller.operation(controller.selectedId)["context"],
                    "publish/review_pass",
                )
                self.assertEqual(
                    context_chip.property("text"),
                    "Контекст: review_pass",
                )
                self.assertEqual(primary_send.property("text"), "Отправить все")
                self.assertFalse(primary_send.property("compact"))
                self.assertTrue(send_overflow.property("visible"))
                for object_name, owner in (
                    ("commitQueueAutoCleanSwitch", files_dock),
                    ("commitQueueClearButton", files_dock),
                    ("commitQueuePreviewButton", summary),
                    ("commitQueuePreviewOverflowButton", summary),
                ):
                    control = view.findChild(QObject, object_name)
                    self.assertIsNotNone(control)
                    position = control.mapToItem(owner, QPointF(0, 0))
                    self.assertGreaterEqual(position.x(), -0.1, object_name)
                    self.assertLessEqual(
                        position.x() + control.width(),
                        owner.width() + 0.1,
                        object_name,
                    )
                window.resize(1280, 760)
                view.setWidth(1280)
                view.setHeight(760)
                QTest.qWait(80)
                for object_name in (
                    "commitQueueCapturePreviewButton",
                    "commitQueueChoosePreviewButton",
                    "commitQueuePastePreviewButton",
                    "commitQueueManagePreviewButton",
                    "commitQueueClearPreviewsButton",
                ):
                    self.assertTrue(
                        view.findChild(QObject, object_name).property(
                            "visible"
                        ),
                        object_name,
                    )
                capture_button = view.findChild(
                    QObject, "commitQueueCapturePreviewButton"
                )
                self.assertTrue(
                    QMetaObject.invokeMethod(capture_button, "clicked")
                )
                QTest.qWait(20)
                self.assertEqual(
                    window_model.child_calls[-1],
                    ("screenshot_maker", "commit_queue"),
                )
                rendered = window.grabWindow()
                self.assertFalse(rendered.isNull())
        finally:
            window.close()
            window.deleteLater()
            view.deleteLater()
            theme.deleteLater()
            controller.deleteLater()
            engine.deleteLater()
            self.app.removeTranslator(translator)
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
