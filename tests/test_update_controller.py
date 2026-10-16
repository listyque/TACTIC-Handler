"""Release polling and one-time notification checks."""

import ast
import os
from types import SimpleNamespace
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")
if os.name == 'nt':
    os.environ.setdefault(
        'QT_QPA_FONTDIR', str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'),
    )

from shiboken6 import isValid
from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from thlib.ui.update_controller import UpdateController
from thlib.ui.localization import CatalogTranslator
from thlib.ui.icon_font import qml_icon_bindings
from thlib.environment import env_mode
from tests.profile_ui_responsiveness import frame
from tests import test_sidebar_editor_qml as sidebar_fixture
from thlib import tactic_query


QML = Path(__file__).resolve().parents[1] / "thlib" / "ui" / "qml"


class UpdateControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def make_controller(self):
        application = SimpleNamespace(
            authentication_required=False, login_name="alice",
            server_state="online", can_manage_tools=False,
            opened=[],
        )
        application.open_window = application.opened.append
        return UpdateController(application, SimpleNamespace())

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.enterContext(patch.object(env_mode, 'current_path', temporary.name))

    def test_tactic_release_query_is_valid_server_python(self):
        script = tactic_query.prepare_serverside_script(
            tactic_query.query_application_update_snapshots,
            {"search_key": "demo/object?project=demo&code=UPDATE"},
            shrink=False, catch_traceback=False,
        )["code"]
        ast.parse(script)

    def test_polling_starts_only_after_online_authentication(self):
        with patch("thlib.ui.update_controller.env_read_config",
                   return_value={"searchKey": "demo/object?code=UPDATE"}), patch(
            "thlib.environment.env_server.get_ticket", return_value="ticket"
        ):
            controller = self.make_controller()
            controller._application.server_state = "connecting"
            controller.sync_authentication()
            self.assertFalse(controller._timer.isActive())
            controller._application.server_state = "online"
            with patch.object(controller, "refresh_remote") as refresh:
                controller.sync_authentication()
                controller.sync_authentication()  # Online ping must not recheck.
                refresh.assert_called_once_with()
                controller._application.login_name = "bob"
                controller.sync_authentication()
                self.assertEqual(refresh.call_count, 2)
            self.assertTrue(controller._timer.isActive())
            self.assertEqual(controller._timer.interval(), 24 * 60 * 60 * 1000)
            controller._application.authentication_required = True
            controller.sync_authentication()
            self.assertFalse(controller._timer.isActive())

    def test_new_release_is_selected_and_announced_once(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "thlib.ui.update_controller.env_read_config",
                   return_value={"searchKey": "demo/object?code=UPDATE"}), patch(
            "thlib.ui.update_controller.releases.portable_root",
            return_value=Path(temporary),
        ), patch(
            'thlib.ui.update_controller.releases.current_version',
            return_value=(1, 0, 0, 0),
        ):
            controller = self.make_controller()
            releases = [{
                "code": "SNAP1", "timestamp": "2026-09-22 10:00:00",
                "description": "New release", "__files__": [
                    {"code": "FILE1", "file_name": "handler_1_0_0_1.zip"},
                ],
            }]
            announced = []
            controller.updateAvailable.connect(announced.append)
            controller._show_releases(releases)
            self.assertEqual(controller.model._records[0]["version"], "1.0.0.1")
            self.assertTrue(controller.model._records[0]["selected"])
            controller._show_releases(releases)
            self.assertEqual(announced, ["1.0.0.1"])

    def find(self, view, name):
        return next(item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(view) if item.objectName() == name)

    def make_view(self, controller, create_mode=False):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        engine.rootContext().setContextProperty('updateController', controller)
        engine.rootContext().setContextProperty('updateModel', controller.model)
        for name, value in qml_icon_bindings(QML.parents[2], parent=engine).items():
            engine.rootContext().setContextProperty(name, value)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / 'Theme.qml')),
        )
        theme = theme_component.createWithInitialProperties({
            'dark': True, 'popupAnimationsEnabled': False,
            'suppressTransientMotion': True,
        })
        theme.setParent(engine)
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / 'UpdateView.qml')),
        )
        view = component.createWithInitialProperties({
            'theme': theme, 'createMode': create_mode,
        })
        self.assertIsNotNone(view, [error.toString() for error in component.errors()])
        window = QQuickWindow()
        window.resize(640, 520)
        view.setParent(window)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        frame(window)

        def cleanup():
            controller._timer.stop()
            window.close()
            window.deleteLater()
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
            engine.deleteLater()
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
            self.assertEqual(warnings, [])

        self.addCleanup(cleanup)
        return window, view

    def test_offline_changelog_tab_wraps_and_scrolls_in_narrow_and_wide_windows(self):
        translator = CatalogTranslator(QML.parent / 'translations/ru.json')
        self.app.installTranslator(translator)
        self.addCleanup(self.app.removeTranslator, translator)
        controller = self.make_controller()
        controller._application.authentication_required = True
        controller._changelog += '\n' + ('- A long release note with detailed changes.\n' * 80)
        window, view = self.make_view(controller)
        items, pending = {}, [view]
        while pending:
            item = pending.pop()
            items[item.objectName()] = item
            pending.extend(item.childItems())
        changelog_tab = items['updatePage_changelog']
        updates_tab = items['updatePage_updates']

        for width in (460, 980):
            window.resize(width, 520)
            view.setSize(window.size())
            frame(window)
            point = changelog_tab.mapToScene(QPointF(
                changelog_tab.width() / 2, changelog_tab.height() / 2,
            )).toPoint()
            frame(window, lambda: QTest.mouseClick(window, Qt.LeftButton, pos=point))
            self.assertEqual(view.property('currentPage'), 'changelog')
            scroll = self.find(view, 'updateChangelogScroll')
            body = self.find(scroll, 'documentBody')
            scrollbar = self.find(scroll, 'documentScrollbar')
            self.assertTrue(body.isVisible())
            self.assertIn(controller.currentVersion, body.property('text'))
            self.assertTrue(scrollbar.property('hasOverflow'))
            self.assertTrue(scrollbar.isVisible())
            self.assertGreater(scrollbar.height(), 0)
            self.assertGreaterEqual(scroll.width() - body.width(), scrollbar.property('reservedExtent'))
            bar_left = scrollbar.mapToScene(QPointF()).x()
            body_right = body.mapToScene(QPointF(body.width(), 0)).x()
            self.assertGreaterEqual(bar_left, body_right)
            self.assertLessEqual(bar_left + scrollbar.width(), width - 14)
            self.assertLessEqual(changelog_tab.x() + changelog_tab.width(), width)
            flickable = scroll.property('contentItem')
            flickable.setProperty('contentY', 0)
            frame(window)
            screenshots = os.environ.get('UPDATE_WINDOW_SCREENSHOTS')
            if screenshots:
                window.grabWindow().save(str(Path(screenshots) / f'changelog-{width}.png'))
            moved = QSignalSpy(flickable.contentYChanged)
            point = scroll.mapToScene(QPointF(scroll.width() / 2, scroll.height() / 2))
            QTest.mouseMove(window, point.toPoint())
            wheel = QWheelEvent(
                point, QPointF(window.mapToGlobal(point.toPoint())),
                QPoint(), QPoint(0, -120), Qt.NoButton, Qt.NoModifier,
                Qt.NoScrollPhase, False,
            )
            wheel.setTimestamp(time.monotonic_ns() // 1_000_000)
            frame(window, lambda: self.app.sendEvent(window, wheel))
            if flickable.property('contentY') <= 0:
                self.assertTrue(moved.wait(1000))
            self.assertGreater(flickable.property('contentY'), 0, (
                flickable.property('contentHeight'), flickable.property('height'),
                flickable.property('interactive'), wheel.isAccepted(), point,
            ))
            updates_tab.forceActiveFocus()
            frame(window, lambda: QTest.keyClick(window, Qt.Key_Space))
            self.assertEqual(view.property('currentPage'), 'updates')
            self.assertTrue(not isValid(body) or not body.isVisible())

    def test_generator_prefills_current_version_and_changelog_notes(self):
        controller = self.make_controller()
        controller._application.can_manage_tools = True
        window, view = self.make_view(controller, create_mode=True)
        self.assertEqual(
            int(self.find(view, 'update_revision').property('text')),
            int(controller.currentVersion.split('.')[-1]),
        )
        self.assertEqual(
            self.find(view, 'updateChanges').property('text'),
            controller.currentChanges,
        )
        area = self.find(view, 'updateChanges')
        scrollbar = next(item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(area) if item.property('orientation') == Qt.Vertical and item.property('hasOverflow') is not None)
        button = self.find(view, 'createUpdateArchiveButton')
        for width in (460, 980):
            window.resize(width, 520)
            view.setSize(window.size())
            frame(window)
            self.assertTrue(scrollbar.property('hasOverflow'))
            self.assertTrue(scrollbar.isVisible())
            self.assertLessEqual(
                button.mapToScene(QPointF(button.width(), button.height())).x(),
                width - 14,
            )
        with patch.object(controller, '_start', return_value=True) as create:
            point = button.mapToScene(QPointF(
                button.width() / 2, button.height() / 2,
            )).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, pos=point)
            create.assert_called_once_with(
                controller._create_archive,
                tuple(map(int, controller.currentVersion.split('.'))),
                controller.currentChanges, '', stage='Creating update archive',
            )

    def test_only_maintainers_can_open_or_run_update_generator(self):
        controller = self.make_controller()

        controller.open_generator()
        self.assertEqual(controller._application.opened, [])
        self.assertFalse(controller.create_update(1, 0, 0, 0, "", ""))

        controller._application.can_manage_tools = True
        controller.open_generator()
        self.assertEqual(controller._application.opened, ["create_update"])

    def test_ctrl_double_click_on_version_opens_generator(self):
        controller = self.make_controller()
        controller._application.can_manage_tools = True
        engine = QQmlEngine()
        engine.addImportPath(str(QML))
        engine.rootContext().setContextProperty(
            "updateController", controller
        )
        engine.rootContext().setContextProperty("updateModel", controller.model)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml"))
        )
        theme = theme_component.createWithInitialProperties({"dark": True})
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "UpdateView.qml"))
        )
        view = component.createWithInitialProperties({
            "theme": theme,
            "createMode": False,
        })
        self.assertIsNotNone(
            view,
            "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(640, 520)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        QTest.qWait(40)
        label = self.find(view, "currentVersionLabel")
        self.assertIsNotNone(label)

        QTest.mouseDClick(
            window,
            Qt.LeftButton,
            Qt.ControlModifier,
            label.mapToScene(QPointF(
                label.width() / 2, label.height() / 2,
            )).toPoint(),
        )
        QTest.qWait(20)

        self.assertEqual(controller._application.opened, ["create_update"])
        window.close()


if __name__ == "__main__":
    unittest.main()
