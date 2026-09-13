"""Real Search badge-to-popup input path, with an optional latency benchmark."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import statistics
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")
if os.name == "nt":
    os.environ.setdefault(
        "QT_QPA_FONTDIR", str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"),
    )

from PySide6.QtCore import (
    QCoreApplication, QEvent, QEventLoop, QObject, QPointF, Property, Qt,
    QTimer, QUrl,
    Signal, Slot,
)
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QSignalSpy, QTest

from thlib.environment import env_mode
from thlib.ui.controller import ApplicationController
from thlib.ui.controllers.types import SearchTabSession, SectionSession
from thlib.ui.filter_editor import FilterEditorController
from thlib.ui.icon_font import qml_icon_bindings
from thlib.ui.quick_filter_editor import QuickFilterEditorController
from thlib.ui.user import UserController
from thlib.ui.workspace_models.results_types import WorkspaceNode
from tests.profile_ui_responsiveness import frame
from tests.test_workspace_process_count_menu import _Source


QML = Path(__file__).resolve().parents[1] / "thlib/ui/qml"


class _MeasuredController(ApplicationController):
    processOpened = Signal()

    def __init__(self):
        super().__init__()
        self.action_times = []
        self.opened_processes = []

    @Slot(str, str, result="QVariantList")
    def process_count_actions(self, node_id, panel):
        started = time.perf_counter()
        result = super().process_count_actions(node_id, panel)
        self.action_times.append((time.perf_counter() - started) * 1000)
        return result

    @Slot(str, str, str)
    def open_process_details(self, node_id, panel, process):
        self.opened_processes.append((node_id, panel, process))
        self.processOpened.emit()


class _ShelfHost(QObject):
    def __init__(self, shelf=None):
        super().__init__()
        self._shelf = shelf

    @Property(QObject, constant=True)
    def scriptShelf(self):
        return self._shelf


def visual_items(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from visual_items(child)


class _PopupFrameProbe(QObject):
    """Observe the popup's actual window, including an embedded owner's frame."""

    presented = Signal()

    def __init__(self, repeater, source_window, windowed):
        super().__init__()
        self.started = time.perf_counter()
        self.activated = None
        self.source_window = source_window
        self.windowed = windowed
        self.repeater = repeater
        self.available_rows = repeater.property("count")
        repeater.countChanged.connect(self.update_rows)
        self.first_frame = None
        self.content_frame = None
        self.dispatch_ms = None
        self.frame_rows = 0
        self.frame_is_current = False
        self.phases = {}
        self.connections = []
        self.loop = QEventLoop()
        self.presented.connect(self.loop.quit, Qt.QueuedConnection)
        if not windowed:
            self.observe(source_window)

    def event(self, event):
        if event.type() == QEvent.User:
            self.dispatch_ms = (time.perf_counter() - self.activated) * 1000
            if self.content_frame is not None:
                self.loop.quit()
            return True
        return super().event(event)

    @Slot()
    def update_rows(self):
        self.available_rows = self.repeater.property("count")

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonRelease and watched is self.source_window:
            # The badge activates on release. Time spent holding/painting the
            # pressed button is separate from the menu's opening latency.
            self.activated = time.perf_counter()
            if not self.windowed:
                QGuiApplication.instance().removeEventFilter(self)
        if (event.type() == QEvent.Show and isinstance(watched, QQuickWindow)
                and (watched.flags() & Qt.WindowType_Mask) == Qt.Popup):
            QGuiApplication.instance().removeEventFilter(self)
            self.observe(watched)
        return False

    def observe(self, window):
        for name in (
            "beforeSynchronizing", "afterSynchronizing",
            "beforeRendering", "afterRendering", "frameSwapped",
        ):
            def record(name=name):
                if name == "beforeSynchronizing":
                    self.frame_is_current = self.activated is not None
                if not self.frame_is_current:
                    return
                elapsed = (time.perf_counter() - self.activated) * 1000
                self.phases.setdefault(name, round(elapsed, 3))
                if name == "beforeSynchronizing":
                    # The render thread must not read QML properties. The
                    # owning GUI thread publishes the count synchronously.
                    self.frame_rows = self.available_rows
                    self.phases.setdefault("firstFrameRows", self.frame_rows)
                if name == "frameSwapped" and self.first_frame is None:
                    self.first_frame = elapsed
                if (name == "frameSwapped" and self.frame_rows > 0
                        and self.content_frame is None):
                    self.content_frame = elapsed
                    if self.dispatch_ms is not None:
                        self.presented.emit()
            signal = getattr(window, name)
            signal.connect(record, Qt.DirectConnection)
            self.connections.append((signal, record))

    def detach(self):
        self.repeater.countChanged.disconnect(self.update_rows)
        for signal, callback in self.connections:
            signal.disconnect(callback)
        self.connections.clear()


class ProcessMenuLatencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])
        cls.icon_bindings = qml_icon_bindings(QML.parents[2], cls.app)

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(env_mode, "current_path", directory))
        self.controller = _MeasuredController()
        self.addCleanup(self.controller.shutdown)
        self.controller._current_project_code = "demo"
        tab = SearchTabSession(tab_id="assets", title="Assets", loaded=True)
        section = SectionSession(
            entry_key="demo/asset", title="Assets", accent="#ef5350",
            search_type="demo/asset", tabs=[tab], current_tab_id=tab.tab_id,
        )
        self.controller._sessions = {section.entry_key: section}
        self.controller._current_section_key = section.entry_key
        self.source = _Source(
            notes={"model": 2, "rig": 1},
            tasks={"model": 2, "rig": 1, "__total__": 3},
            task_summaries={"model": [
                {
                    "code": "TASK001", "process": "model",
                    "context": "model", "assigned": "artist",
                    "status": "In Progress",
                    "__primary_note_branch__": True,
                },
                {
                    "code": "TASK002", "process": "model",
                    "context": "client-review", "assigned": "lead",
                    "status": "Review",
                    "__primary_note_branch__": False,
                },
            ]},
        )
        self.node = WorkspaceNode(
            node_id="asset", node_type="sobject", title="Firetruck",
            search_key="demo/asset?project=demo&code=ASSET001", code="ASSET001",
            tasks=2, comments=3, source=self.source,
            preview_requested=True, card_preview_requested=True,
        )
        self.controller.workspace_model.replace_nodes([self.node])
        self.controller.workspace_state.set_result_surfaces([{
            "surfaceKey": "assets", "current": True,
            "resultModel": self.controller.workspace_model,
            "viewMode": "continious", "splitterRatio": 0.58,
        }])
        self.rpc = self.enterContext(patch(
            "thlib.tactic_classes.execute_procedure_serverside",
            side_effect=AssertionError("Opening the picker must not call TACTIC"),
        ))

    @contextmanager
    def scene(self, width=900, animated=True, height=650, shelf=None):
        engine = QQmlEngine()
        warnings = []
        engine.warnings.connect(
            lambda errors: warnings.extend(error.toString() for error in errors)
        )
        users = UserController(self.controller)
        filters = FilterEditorController(
            self.controller.workspace_state.filter_model,
            lambda: [], lambda: [], lambda *_: None,
        )
        editor = QuickFilterEditorController(self.controller, users)
        shelf_host = _ShelfHost(shelf)
        state = self.controller.workspace_state
        bindings = {
            **self.icon_bindings,
            "appController": self.controller, "workspaceState": state,
            "workspaceTabsModel": state.tabs_model,
            "workspaceResultSurfacesModel": state.result_surfaces_model,
            "searchSuggestionModel": state.search_suggestion_model,
            "versionsModel": self.controller.versions_model,
            "filterEditorController": filters, "filterPresetModel": filters.presets,
            "quickFilterEditorController": editor, "userController": users,
            "sidebarEditorController": shelf_host,
            "userPickerModel": users.users, "userListModel": users.users,
            "windowModel": self.controller.window_model,
            "dockModel": self.controller.dock_model,
        }
        for name, value in bindings.items():
            engine.rootContext().setContextProperty(name, value)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml")),
        )
        theme = theme_component.createWithInitialProperties({
            "dark": True, "clickAnimationsEnabled": animated,
            "hoverAnimationsEnabled": animated, "fadeAnimationsEnabled": animated,
            "popupAnimationsEnabled": animated,
        })
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "SearchWorkspaceView.qml")),
        )
        view = component.createWithInitialProperties({
            "theme": theme, "pageTitle": "Search",
        })
        self.assertIsNotNone(view, [error.toString() for error in component.errors()])
        window = QQuickWindow()
        window.resize(width, height)
        view.setParentItem(window.contentItem())
        view.setSize(window.size())
        window.show()
        window.requestActivate()
        QTest.qWaitForWindowActive(window)
        frame(window)
        try:
            yield window, view
            self.assertEqual(warnings, [])
            self.rpc.assert_not_called()
        finally:
            for popup in view.findChildren(QObject):
                if popup.property("processPickerStyle"):
                    popup.close()
            window.close()
            view.setParentItem(None)
            view.deleteLater()
            theme.deleteLater()
            window.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def badge(self, view, panel):
        name = "workspaceTaskCountButton" if panel == "tasks" else "workspaceNoteCountButton"
        return next(item for item in visual_items(view) if item.objectName() == name)

    def picker(self, view):
        return next(
            item for item in view.findChildren(QObject)
            if item.property("processPickerStyle") and item.property("visible")
        )

    def close_menu(self, menu):
        closed = QSignalSpy(menu.closed)
        menu.close()
        if menu.property("visible"):
            self.assertTrue(closed.wait(1000), "Picker did not close")
        QCoreApplication.processEvents()

    def measure_open(self, window, view, panel):
        badge = self.badge(view, panel)
        # Benchmarks repeat genuine clicks faster than a person. Exclude the
        # duplicate-input rejection window from the measured work.
        badge.findChild(QObject, "compactIconButtonCursorArea").setProperty(
            "lastActivationAt", -1000.0,
        )
        position = badge.mapToScene(QPointF(badge.width() / 2, badge.height() / 2))
        menu = view.findChild(QObject, "workspaceProcessCountMenu")
        menu.setProperty("lastClosedAt", 0.0)
        probe = _PopupFrameProbe(
            menu.findChild(QObject, "actionMenuRepeater"), window,
            menu.property("usePopupWindow"),
        )
        self.app.installEventFilter(probe)
        guard = QTimer()
        guard.setSingleShot(True)
        guard.timeout.connect(probe.loop.quit)
        try:
            # Deliver the real mouse events through Qt's event loop. Holding
            # Python's GIL across a synchronous QTest click can stall native
            # threaded rendering and measure the test harness instead of UI.
            for kind, buttons in (
                (QEvent.MouseButtonPress, Qt.LeftButton),
                (QEvent.MouseButtonRelease, Qt.NoButton),
            ):
                QCoreApplication.postEvent(window, QMouseEvent(
                    kind, position, window.mapToGlobal(position),
                    Qt.LeftButton, buttons, Qt.NoModifier,
                ))
            QCoreApplication.postEvent(probe, QEvent(QEvent.User))
            guard.start(3000)
            probe.loop.exec()
            self.assertIsNotNone(probe.dispatch_ms, "Mouse input was not dispatched")
            menu = self.picker(view)
            self.assertIsNotNone(probe.content_frame, "Picker did not render its rows")
        finally:
            guard.stop()
            self.app.removeEventFilter(probe)
            probe.detach()
        return menu, {
            "dispatchMs": round(probe.dispatch_ms, 3),
            "dataMs": round(self.controller.action_times[-1], 3),
            "popupFrameMs": round(probe.first_frame, 3),
            "contentFrameMs": round(probe.content_frame, 3),
            "pressToActivationMs": round((probe.activated - probe.started) * 1000, 3),
            "rows": menu.findChild(QObject, "actionMenuRepeater").property("count"),
            "phases": probe.phases,
        }

    def test_badge_opens_picker_from_loaded_counts_without_selecting_object(self):
        for width, animated in ((430, False), (1400, True)):
            with self.subTest(width=width, animated=animated), \
                    self.scene(width, animated) as (window, view):
                menu, sample = self.measure_open(window, view, "tasks")
                self.assertEqual(sample["rows"], 4)
                self.assertEqual(sample["phases"]["firstFrameRows"], 4)
                self.assertEqual(sample["popupFrameMs"], sample["contentFrameMs"])
                self.assertTrue(menu.property("opened"))
                self.assertEqual(menu.property("opacity"), 1)
                self.assertEqual(menu.property("scale"), 1)
                self.assertEqual(self.controller._current_tab().selected_node_ids, [])
                self.assertEqual(self.controller.opened_processes, [])
                self.assertEqual(menu.property("preferredWidth"), 212)
                self.assertIs(menu.property("contentItem").window(), window)
                self.assertEqual(menu.property("anchorPointerEdge"), "top")
                badge = self.badge(view, "tasks")
                center = badge.mapToScene(QPointF(badge.width() / 2, 0))
                self.assertAlmostEqual(
                    menu.property("x") + menu.property("anchorPointerCenter"),
                    center.x(), delta=1,
                )
                self.assertFalse(menu.findChild(
                    QObject, "actionMenuScrollBar",
                ).isVisible())
                content = menu.property("contentItem")
                for row in visual_items(content):
                    if row.objectName() != "actionMenuRowSurface" or not row.isVisible():
                        continue
                    point = row.mapToItem(content, QPointF())
                    self.assertGreaterEqual(point.x(), 0)
                    self.assertGreaterEqual(point.y(), 0)
                    self.assertLessEqual(point.x() + row.width(), content.width())
                    self.assertLessEqual(point.y() + row.height(), content.height())

    def test_overflow_tab_cross_closes_that_tab(self):
        section = self.controller._current_section()
        section.tabs.append(SearchTabSession(
            tab_id="extra", title="Extra long search tab", loaded=True,
        ))
        self.controller.workspace_state.set_tabs([
            {
                "entryKey": tab.tab_id, "title": tab.title,
                "closable": True, "current": tab is section.tabs[0],
            }
            for tab in section.tabs
        ])
        self.enterContext(patch.object(self.controller, "_sync_search_tabs"))
        self.enterContext(patch.object(
            QuickFilterEditorController, "ensure_current",
        ))

        with self.scene(width=430, animated=False) as (window, view):
            button = view.findChild(QQuickItem, "searchTabsOverflowButton")
            self.assertTrue(button.isVisible())
            point = button.mapToScene(QPointF(
                button.width() / 2, button.height() / 2,
            )).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
            QCoreApplication.processEvents()

            menu = view.findChild(QObject, "searchTabsOverflowMenu")
            target = next(
                item for item in visual_items(menu.property("contentItem"))
                if item.objectName() == "actionMenuSecondaryTarget"
                and item.isVisible()
                and item.parentItem().property("modelData").toVariant().get(
                    "title"
                ) == "Extra long search tab"
            )
            point = target.mapToScene(QPointF(
                target.width() / 2, target.height() / 2,
            )).toPoint()
            QTest.mouseClick(
                target.window(), Qt.LeftButton, Qt.NoModifier, point,
            )
            frame(window)

            self.assertNotIn(
                "Extra long search tab", [tab.title for tab in section.tabs],
            )

    def test_compact_result_actions_open_sort_and_group_submenus(self):
        with self.scene(width=430, animated=False) as (window, view):
            button = view.findChild(
                QQuickItem, "searchTabActionsOverflowButton",
            )
            point = button.mapToScene(QPointF(
                button.width() / 2, button.height() / 2,
            )).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point)
            QCoreApplication.processEvents()

            menu = view.findChild(QObject, "searchTabActionsMenu")

            def open_submenu(title):
                target = next(
                    item for item in visual_items(menu.property("contentItem"))
                    if item.objectName() == "actionMenuPrimaryTarget"
                    and item.isVisible()
                    and item.parentItem().property("modelData").toVariant().get(
                        "title"
                    ) == title
                )
                point = target.mapToScene(QPointF(
                    target.width() / 2, target.height() / 2,
                )).toPoint()
                QTest.mouseClick(
                    target.window(), Qt.LeftButton, Qt.NoModifier, point,
                )
                QTest.qWait(30)
                return menu.property("activeSubmenu")

            for title, child_title in (
                ("Sort items", "Name A-Z"),
                ("Group items", "No grouping"),
            ):
                submenu = open_submenu(title)
                self.assertTrue(submenu.property("opened"))
                self.assertIn(child_title, [
                    item.property("text")
                    for item in visual_items(submenu.property("contentItem"))
                    if item.objectName() == "actionMenuTitleLabel"
                ])
                submenu.close()
                QCoreApplication.processEvents()

    def test_refresh_precedes_the_search_field(self):
        for width in (430, 900):
            with self.subTest(width=width), self.scene(
                    width=width, animated=False) as (_window, view):
                refresh = view.findChild(QQuickItem, "searchRefreshButton")
                field = view.findChild(QQuickItem, "searchField")
                refresh_position = refresh.mapToItem(view, QPointF())
                field_position = field.mapToItem(view, QPointF())
                self.assertGreaterEqual(refresh_position.x(), 38)
                self.assertLessEqual(
                    refresh_position.x() + refresh.width(), field_position.x(),
                )
                self.assertAlmostEqual(
                    refresh_position.y() + refresh.height() / 2,
                    field_position.y() + field.height() / 2,
                    delta=1,
                )

    def test_context_task_picker_drills_in_without_closing_popup(self):
        with self.scene(width=900, animated=False) as (window, view):
            def click(position):
                for kind, buttons in (
                    (QEvent.MouseButtonPress, Qt.LeftButton),
                    (QEvent.MouseButtonRelease, Qt.NoButton),
                ):
                    QCoreApplication.postEvent(window, QMouseEvent(
                        kind,
                        position,
                        window.mapToGlobal(position),
                        Qt.LeftButton,
                        buttons,
                        Qt.NoModifier,
                    ))
                QCoreApplication.processEvents()
                QTest.qWait(30)

            menu, _sample = self.measure_open(window, view, "tasks")
            content = menu.property("contentItem")
            secondary = next(
                item for item in visual_items(content)
                if item.objectName() == "actionMenuSecondaryTarget"
                and item.isVisible() and item.isEnabled()
            )
            closed = QSignalSpy(menu.closed)
            position = secondary.mapToScene(QPointF(
                secondary.width() / 2, secondary.height() / 2,
            )).toPoint()

            click(position)

            self.assertTrue(menu.property("opened"))
            self.assertEqual(closed.count(), 0)
            titles = [
                str(item.property("text"))
                for item in visual_items(content)
                if item.objectName() == "actionMenuTitleLabel"
                and item.isVisible()
            ]
            self.assertEqual(
                titles,
                ["model", "All processes", "model", "client-review"],
            )

            back = next(
                item for item in visual_items(content)
                if item.objectName() == "actionMenuPrimaryTarget"
                and item.isVisible() and item.isEnabled()
            )
            back_position = back.mapToScene(QPointF(
                back.width() / 2, back.height() / 2,
            )).toPoint()
            click(back_position)

            self.assertTrue(menu.property("opened"))
            self.assertEqual(closed.count(), 0)
            root_titles = [
                str(item.property("text"))
                for item in visual_items(content)
                if item.objectName() == "actionMenuTitleLabel"
                and item.isVisible()
            ]
            self.assertEqual(root_titles, ["Tasks", "Publish", "Model", "Rig"])

    def test_embedded_menu_flips_at_window_edge_and_dismisses_without_click_through(self):
        with self.scene(width=430, height=350) as (window, view):
            # A Search dock at the bottom of its owner window.
            view.setY(120)
            view.setHeight(230)
            frame(window)
            menu, _sample = self.measure_open(window, view, "tasks")
            self.assertEqual(menu.property("anchorPointerEdge"), "bottom")
            self.assertGreaterEqual(menu.property("x"), 4)
            self.assertGreaterEqual(menu.property("y"), 4)
            self.assertLessEqual(menu.property("x") + menu.property("width"), window.width() - 4)
            self.assertLessEqual(menu.property("y") + menu.property("height"), window.height() - 4)
            QTest.keyClick(window, Qt.Key_Escape)
            self.assertFalse(menu.property("visible"))
            menu, _sample = self.measure_open(window, view, "tasks")
            # Click the original badge below the menu. This closes the modal
            # overlay without reopening it or selecting the card behind it.
            badge = self.badge(view, "tasks")
            point = badge.mapToScene(QPointF(badge.width() / 2, badge.height() / 2))
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point.toPoint(), 0)
            self.assertFalse(menu.property("visible"))
            self.assertEqual(self.controller._current_tab().selected_node_ids, [])
            self.assertEqual(self.controller.opened_processes, [])

    def test_compact_picker_reuses_rows_and_updates_loaded_counts(self):
        with self.scene() as (window, view):
            menu, _sample = self.measure_open(window, view, "tasks")
            content = menu.property("contentItem")
            rows = [item for item in visual_items(content)
                    if item.objectName() == "actionMenuRowSurface"]
            self.assertEqual(len(rows), 4)
            self.close_menu(menu)
            self.assertEqual(
                menu.findChild(QObject, "actionMenuRepeater").property("count"), 4,
            )
            self.source.notes["model"] = 9
            reopened, _sample = self.measure_open(window, view, "notes")
            self.assertIs(reopened, menu)
            self.assertEqual(
                [item for item in visual_items(content)
                 if item.objectName() == "actionMenuRowSurface"], rows,
            )
            self.assertEqual(sorted(
                item.property("countValue") for item in visual_items(content)
                if item.objectName() == "actionMenuBadge" and item.isVisible()
            ), [0, 1, 9])
            self.close_menu(menu)
            self.source.notes["layout"] = 2
            menu, sample = self.measure_open(window, view, "notes")
            self.assertEqual(sample["phases"]["firstFrameRows"], 5)
            self.close_menu(menu)
            self.source.notes = {"rig": 3}
            menu, sample = self.measure_open(window, view, "notes")
            self.assertEqual(sample["phases"]["firstFrameRows"], 3)
            self.assertEqual(
                [item.property("text") for item in visual_items(content)
                 if item.objectName() == "actionMenuTitleLabel"],
                ["Messages", "Publish", "Rig"],
            )

    def test_first_repo_sync_menu_updates_when_presets_arrive(self):
        class Project:
            @staticmethod
            def get_code():
                return "demo"

        class SearchType:
            @staticmethod
            def get_code():
                return "demo/asset"

            @staticmethod
            def get_project():
                return Project()

        self.source.get_stype = lambda: SearchType()
        self.controller.repository_sync.request_presets = Mock()
        self.node.controls_signature = (
            "sobject", False, "none", (), "", False, 0,
        )
        self.node.controls_cache = [{
            "command": "repo_sync",
            "icon": "repository-sync",
            "tip": "Open Repository Sync Dialog",
            "persistent": True,
        }]

        with self.scene() as (window, view):
            button = next(
                item for item in visual_items(view)
                if item.objectName() == "workspaceItemAction_repo_sync"
            )
            point = button.mapToScene(QPointF(
                button.width() / 2, button.height() / 2,
            )).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, point, 0)
            QCoreApplication.processEvents()
            menu = self.picker(view)
            self.assertEqual(
                [action.get("command") for action in menu.property("actions")],
                ["repo_sync", None, "repo_sync_preset:default"],
            )

            self.controller.repository_sync.cache_presets(self.source, [
                {
                    "pretty_preset_name": "Default",
                    "preset_name": "default",
                },
                {
                    "pretty_preset_name": "Animation",
                    "preset_name": "animation",
                },
            ])
            QCoreApplication.processEvents()

            self.assertTrue(menu.property("opened"))
            self.assertEqual(
                [action.get("command") for action in menu.property("actions")],
                [
                    "repo_sync", None, "repo_sync_preset:default",
                    None, "repo_sync_preset:animation",
                ],
            )

    def test_retained_rows_activate_current_panel_with_mouse_keyboard_and_touch(self):
        for input_kind in ("mouse", "keyboard", "touch"):
            with self.subTest(input_kind=input_kind), self.scene() as (window, view):
                menu, _sample = self.measure_open(window, view, "tasks")
                self.close_menu(menu)
                self.source.notes = {"render": 3, "layout": 1}
                menu, _sample = self.measure_open(window, view, "notes")
                content = menu.property("contentItem")
                targets = [item for item in visual_items(content)
                           if item.objectName() == "actionMenuPrimaryTarget"
                           and item.isEnabled()]
                render_target = targets[1]  # Publish remains the first process.
                popup_window = content.window()
                point = render_target.mapToScene(QPointF(
                    render_target.width() / 2, render_target.height() / 2,
                )).toPoint()
                opened = QSignalSpy(self.controller.processOpened)
                if input_kind == "keyboard":
                    render_target.forceActiveFocus()
                    QTest.keyClick(popup_window, Qt.Key_Return)
                elif input_kind == "touch":
                    device = QTest.createTouchDevice()
                    tap = QTest.touchEvent(popup_window, device, autoCommit=False)
                    tap.press(0, point, popup_window).commit()
                    tap.release(0, point, popup_window).commit()
                else:
                    QTest.mouseClick(popup_window, Qt.LeftButton, Qt.NoModifier, point, 0)
                if not opened.count():
                    self.assertTrue(opened.wait(1000))
                self.assertEqual(self.controller.opened_processes[-1], (
                    self.node.node_id, "notes", "render",
                ))
                self.assertFalse(menu.property("visible"))
                self.assertEqual(self.controller._current_tab().selected_node_ids, [])

    def test_popup_transitions_are_disabled_for_compact_menus(self):
        if QQuickStyle.name() != "Material":
            self.skipTest("Run separately with QT_QUICK_CONTROLS_STYLE=Material")
        with self.scene() as (_window, view):
            menus = [item for item in view.findChildren(QObject)
                     if item.property("processPickerStyle") is not None]
            self.assertTrue(any(not item.property("processPickerStyle") for item in menus))
            for menu in menus:
                self.assertEqual(menu.property("usePopupWindow"), not menu.property("processPickerStyle"))
                for transition in ("enter", "exit"):
                    expression = QQmlExpression(
                        QQmlEngine.contextForObject(menu), menu,
                        f"{transition} !== null && {transition}.enabled",
                    )
                    value, undefined = expression.evaluate()
                    self.assertFalse(expression.hasError(), expression.error().toString())
                    self.assertFalse(undefined)
                    self.assertEqual(value, not menu.property("processPickerStyle"))


def benchmark():
    from thlib.ui.rendering import apply_render_backend

    apply_render_backend("automatic", environment=os.environ)
    QQuickWindow.setTextRenderType(QQuickWindow.NativeTextRendering)
    ProcessMenuLatencyTests.setUpClass()
    test = ProcessMenuLatencyTests()
    test.setUp()
    try:
        with test.scene() as (window, view):
            samples = []
            for index in range(12):
                menu, sample = test.measure_open(
                    window, view, "tasks" if index % 2 == 0 else "notes",
                )
                samples.append(sample)
                test.close_menu(menu)
                # Measure a settled click, not an immediate reopen while the
                # owner is still presenting the previous popup's close.
                presented = QSignalSpy(window.frameSwapped)
                window.update()
                if not presented.count():
                    test.assertTrue(presented.wait(1000), "Owner did not present a frame")
            print(json.dumps({
                "platform": os.environ["QT_QPA_PLATFORM"],
                "backend": str(window.rendererInterface().graphicsApi()),
                "style": QQuickStyle.name(),
                "cold": samples[0],
                "warmMedian": {
                    key: round(statistics.median(s[key] for s in samples[1:]), 3)
                    for key in ("dataMs", "dispatchMs", "popupFrameMs", "contentFrameMs")
                },
                "samples": samples,
            }, indent=2))
    finally:
        test.doCleanups()


if __name__ == "__main__":
    if "--benchmark" in sys.argv:
        benchmark()
    else:
        unittest.main()
