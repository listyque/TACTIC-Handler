from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QSG_RENDER_LOOP", "basic")

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
        from PySide6.QtGui import QFontDatabase
        fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
        for name in ('segoeui.ttf', 'segoeuib.ttf'):
            if (fonts / name).is_file():
                QFontDatabase.addApplicationFont(str(fonts / name))

    def test_splitter_drag_persists_and_actions_fit_when_panels_shrink(self):
        from PySide6.QtCore import QPoint, Qt
        from thlib.environment import env_mode, env_write_config
        from test_commit_queue import payload

        translator = CatalogTranslator(QML.parent / 'translations/ru.json')
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        with tempfile.TemporaryDirectory() as directory, patch.object(env_mode, 'current_path', directory):
            source = Path(directory) / 'source.txt'
            source.write_bytes(b'content')
            controller = CommitQueueController()
            controller._server_queue = True
            ids = controller.add_prepared_many([(payload(source, str(i)), str(i)) for i in range(3)])
            controller._set_record(ids[0], status='Completed')
            controller._set_record(ids[2], status='Failed', error='test failure')
            engine = QQmlEngine()
            warnings = []
            engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
            context = engine.rootContext()
            from thlib.ui.icon_font import qml_icon_bindings
            bindings = qml_icon_bindings(ROOT, engine)
            for name, value in bindings.items():
                context.setContextProperty(name, value)
            context.setContextProperty('commitQueueController', controller)
            context.setContextProperty('commitQueueModel', controller.model)
            hosts = [_ScreenshotController(engine), _NamingEditorController(engine), _WindowModel(engine)]
            for name, host in zip(('screenshotController', 'namingEditorController', 'windowModel'), hosts):
                context.setContextProperty(name, host)
            theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')))
            theme = theme_component.createWithInitialProperties({'dark': True})
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'CommitQueueView.qml')))
            view = component.createWithInitialProperties({'theme': theme})
            self.assertIsNotNone(view, [e.toString() for e in component.errors()])
            window = QQuickWindow()
            view.setParentItem(window.contentItem())
            window.show()
            restored = None
            try:
                files = view.findChild(QObject, 'commitQueueFilesDock')
                details = view.findChild(QObject, 'commitQueueDetailsPanel')
                left_actions = ('commitQueueHelpButton', 'commitQueueAutoCleanSwitch',
                    'commitQueueMoveUpButton', 'commitQueueMoveDownButton',
                    'commitQueueClearCompletedButton', 'commitQueueClearButton', 'commitQueueServerSwitch')
                right_actions = ('commitQueuePrimarySendButton', 'commitQueueSendOverflowButton',
                    'commitQueueApplyToChecked')
                for width in (1280, 760, 640):
                    window.resize(width, 640); view.setWidth(width); view.setHeight(640)
                    QTest.qWait(30)
                    for preferred_ratio in (0.15, 0.85):
                        controller.set_splitter_ratio(preferred_ratio)
                        QTest.qWait(30)
                        for pane, names in ((files, left_actions), (details, right_actions)):
                            edge = pane.mapToItem(view, QPointF(pane.width(), pane.height()))
                            self.assertLessEqual(edge.x(), width, pane.objectName())
                            self.assertLessEqual(edge.y(), 640, pane.objectName())
                            for name in names:
                                item = view.findChild(QObject, name)
                                self.assertTrue(item.property('visible'), name)
                                position = item.mapToItem(pane, QPointF(0, 0))
                                self.assertGreaterEqual(position.x(), -0.1, (width, name))
                                self.assertLessEqual(position.x() + item.width(), pane.width() + 0.1, (width, name))
                                self.assertGreaterEqual(position.y(), -0.1, (width, name))
                                self.assertLessEqual(position.y() + item.height(), pane.height() + 0.1, (width, name))
                controller.set_splitter_ratio(0.36)
                window.resize(1280, 640); view.setWidth(1280); QTest.qWait(30)
                handle = view.findChild(QObject, 'splitterGripVisual').parentItem()
                center = handle.mapToItem(view, QPointF(handle.width()/2, handle.height()/2))
                start = QPoint(round(center.x()), round(center.y()))
                finish = start + QPoint(120, 0)
                before = files.width()
                with patch('thlib.ui.commit_queue.env_write_config', wraps=env_write_config) as writes:
                    QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start)
                    QTest.mouseMove(window, finish, 20)
                    self.app.processEvents()
                    self.assertGreater(files.width(), before + 60)
                    self.assertEqual(writes.call_count, 0)
                    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, finish)
                    self.app.processEvents()
                    self.assertEqual(writes.call_count, 1)
                dragged = files.width()
                ratio = controller.splitterRatio
                self.assertAlmostEqual(ratio, dragged / (view.width() - 30), places=2)
                window.resize(760,640);view.setWidth(760);QTest.qWait(30)
                self.assertLessEqual(details.mapToItem(view,QPointF(details.width(),0)).x(),760)
                self.assertEqual(controller.splitterRatio, ratio)
                window.resize(1280,640);view.setWidth(1280);QTest.qWait(30)
                self.assertAlmostEqual(files.width(), dragged, delta=2)
                view.setParentItem(None);view.deleteLater()
                self.app.sendPostedEvents(None, QEvent.DeferredDelete)
                controller.shutdown()
                restored = CommitQueueController()
                self.assertEqual(restored.splitterRatio, ratio)
                context.setContextProperty('commitQueueController', restored)
                context.setContextProperty('commitQueueModel', restored.model)
                view = component.createWithInitialProperties({'theme':theme})
                view.setParentItem(window.contentItem());view.setWidth(1280);view.setHeight(640)
                QTest.qWait(30)
                self.assertAlmostEqual(view.findChild(QObject,'commitQueueFilesDock').width(), dragged, delta=2)
                self.assertFalse(warnings, warnings)
            finally:
                if restored is not None:
                    restored.shutdown()
                else:
                    controller.shutdown()
                window.close();view.deleteLater();window.deleteLater()
                controller.deleteLater()
                if restored is not None:
                    restored.deleteLater()
                theme.deleteLater();engine.deleteLater()
                self.app.sendPostedEvents(None, QEvent.DeferredDelete)
                self.app.processEvents()

    def test_special_checkins_disable_versionless_controls_and_regular_file_keeps_them(self):
        from PySide6.QtCore import QPoint, Qt
        from test_commit_queue import payload
        from test_checkin_versionless_policy import SPECIAL

        with tempfile.TemporaryDirectory() as directory, patch(
            'thlib.ui.commit_queue.env_read_config', return_value={}
        ), patch('thlib.ui.commit_queue.env_write_config'):
            source = Path(directory) / 'source.txt'
            source.write_bytes(b'content')
            controller = CommitQueueController()
            controller.set_advanced_options_expanded(True)
            engine = QQmlEngine()
            engine.addImportPath(str(QML))
            context = engine.rootContext()
            objects = {'commitQueueController': controller, 'commitQueueModel': controller.model,
                       'screenshotController': _ScreenshotController(engine),
                       'namingEditorController': _NamingEditorController(engine),
                       'windowModel': _WindowModel(engine)}
            for name, obj in objects.items():
                context.setContextProperty(name, obj)
            theme_component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')))
            theme = theme_component.createWithInitialProperties({'dark': True})
            component = QQmlComponent(engine, QUrl.fromLocalFile(str(QML / 'CommitQueueView.qml')))
            view = component.createWithInitialProperties({'theme': theme})
            self.assertIsNotNone(view, str(component.errors()))
            window = QQuickWindow()
            window.resize(1280, 1400)
            view.setParentItem(window.contentItem())
            view.setWidth(1280)
            view.setHeight(1400)
            window.show()
            try:
                for index, options in enumerate(SPECIAL + [dict(checkinType='file')]):
                    identity = controller.add_prepared(dict(payload(source), **options, context=str(index)), 'Asset')
                    controller.select_row(index)
                    QTest.qWait(30)
                    for name, field in (('commitQueueUpdateVersionless', 'updateVersionless'),
                                        ('commitQueueOnlyVersionless', 'onlyVersionless')):
                        control = view.findChild(QQuickItem, name)
                        self.assertIsNotNone(control)
                        allowed = index == len(SPECIAL)
                        self.assertEqual(control.isEnabled(), allowed)
                        before = bool(controller.operation(identity).get(field))
                        point = control.mapToItem(view, QPointF(control.width()/2, control.height()/2))
                        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier,
                                         QPoint(round(point.x()), round(point.y())))
                        self.app.processEvents()
                        after = bool(controller.operation(identity).get(field))
                        self.assertEqual(after, not before if allowed else False)
            finally:
                controller.shutdown()
                window.hide()
                view.setParentItem(None)
                view.deleteLater()
                window.deleteLater()
                theme.deleteLater()
                engine.deleteLater()
                self.app.sendPostedEvents(None, QEvent.DeferredDelete)
                self.app.processEvents()

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
                grip = view.findChild(QObject, "commitQueueFilesGripVisual")
                self.assertIsNotNone(grip)
                self.assertEqual(
                    (grip.property("width"), grip.property("height")),
                    (40, 3),
                )
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
