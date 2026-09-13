from contextlib import contextmanager
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
    os.environ.setdefault(
        "QT_QPA_FONTDIR", str(Path(os.environ["WINDIR"]) / "Fonts"),
    )

from PySide6.QtCore import (
    Q_ARG, QEventLoop, QMetaObject, QPoint, QPointF, Property, Qt, QTimer,
    QUrl, Slot,
    qInstallMessageHandler,
)
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from thlib import environment
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode
from tests.test_workspace_result_item import _WorkspaceAppController


QML = Path(__file__).parents[1] / "thlib" / "ui" / "qml"


class _PagedController(_WorkspaceAppController):
    def __init__(self, view_mode):
        super().__init__()
        self.view_mode = view_mode
        self.requests = 0

    @Property(str, constant=True)
    def results_view_mode(self):
        return self.view_mode

    @Property(str, constant=True)
    def loading_mode(self):
        return "infinite"

    @Property(bool, constant=True)
    def has_more(self):
        return True

    @Property("QVariantList", constant=True)
    def selected_result_node_ids(self):
        return ["asset-0"]

    @Slot()
    def load_more(self):
        self.requests += 1


class SearchPaginationQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.enterContext(patch.object(
            environment.env_mode, "current_path", directory,
        ))
        self.warnings = []
        previous = qInstallMessageHandler(
            lambda _kind, _context, message: self.warnings.append(message)
        )
        self.addCleanup(qInstallMessageHandler, previous)

    def wait_frame(self, window, predicate=lambda: True):
        loop = QEventLoop()
        timeout = QTimer()
        timeout.setSingleShot(True)
        timeout.timeout.connect(loop.quit)

        def presented():
            if predicate():
                loop.quit()

        window.frameSwapped.connect(presented)
        window.update()
        timeout.start(2000)
        loop.exec()
        timeout.stop()
        window.frameSwapped.disconnect(presented)
        self.assertTrue(predicate(), "Expected view state was not reached")

    @contextmanager
    def scene(
        self, mode="continious", animated=True, width=640, count=30,
        node_type="sobject", controller=None, result_model=None,
    ):
        engine = QQmlEngine()
        if controller is None:
            controller = _PagedController(mode)
        engine.rootContext().setContextProperty("appController", controller)
        theme_component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "Theme.qml")),
        )
        theme = theme_component.createWithInitialProperties({
            "dark": True,
            "fadeAnimationsEnabled": animated,
            "clickAnimationsEnabled": animated,
            "hoverAnimationsEnabled": animated,
        })
        model = result_model
        if model is None:
            model = WorkspaceItemModel()
            model.replace_nodes([WorkspaceNode(
                node_id=f"asset-{index}", node_type=node_type,
                search_key="",
                code=f"ASSET{index}", title=f"Asset {index}",
                preview_requested=True, card_preview_requested=True,
            ) for index in range(count)])
        component = QQmlComponent(
            engine, QUrl.fromLocalFile(str(QML / "SearchResultSurface.qml")),
        )
        surface = component.createWithInitialProperties({
            "theme": theme, "controller": controller, "resultModel": model,
            "current": True, "viewMode": mode, "splitterRatio": 0.58,
            "presentationActive": True, "width": width, "height": 360,
        })
        self.assertIsNotNone(
            surface, "\n".join(error.toString() for error in component.errors()),
        )
        window = QQuickWindow()
        window.resize(width, 360)
        surface.setParentItem(window.contentItem())
        window.show()
        try:
            view = surface.findChild(QQuickItem, (
                "searchResultsGridView" if mode == "tiles"
                else "searchResultsListView"
            ))
            self.assertIsNotNone(view)
            self.wait_frame(window, lambda: view.property("opacity") == 1)
            yield controller, model, surface, view, window
            self.assertEqual(self.warnings, [])
        finally:
            window.close()
            surface.setParentItem(None)
            surface.deleteLater()
            theme.deleteLater()
            window.deleteLater()
            self.app.processEvents()

    def wheel(self, view, window, angle=-12000, pixels=0):
        position = view.mapToScene(QPointF(view.width() / 2, view.height() / 2))
        event = QWheelEvent(
            position, QPointF(window.mapToGlobal(position.toPoint())),
            QPoint(0, pixels), QPoint(0, angle), Qt.NoButton, Qt.NoModifier,
            Qt.NoScrollPhase, False,
        )
        self.app.sendEvent(window, event)

    def test_wheel_reaching_bottom_requests_next_page(self):
        for mode in ("continious", "tiles"):
            for animated in (True, False):
                with self.subTest(mode=mode, animated=animated), self.scene(
                    mode, animated,
                ) as (controller, _model, _surface, view, window):
                    self.assertEqual(controller.requests, 0)
                    self.wheel(view, window)
                    self.wait_frame(window, lambda: (
                        view.property("atYEnd")
                        and not view.property("interactionMoving")
                    ))
                    self.assertEqual(controller.requests, 1)

    def test_created_snapshot_reveal_scrolls_without_animation(self):
        with self.scene(
            "continious", animated=False, count=40,
        ) as (_controller, _model, surface, view, window):
            self.assertLessEqual(view.property("contentY"), 1)

            invoked = QMetaObject.invokeMethod(
                surface,
                "revealNode",
                Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", "asset-39"),
            )

            self.assertTrue(invoked)
            self.wait_frame(
                window,
                lambda: view.property("contentY") > 0,
            )

    def test_short_page_can_load_from_trackpad_without_animation(self):
        for mode in ("continious", "tiles"):
            with self.subTest(mode=mode), self.scene(
                mode, animated=False, width=320, count=1,
            ) as (controller, _model, _surface, view, window):
                self.assertTrue(view.property("atYEnd"))
                self.assertEqual(controller.requests, 0)
                self.wheel(view, window, angle=0, pixels=-60)
                self.wait_frame(window)
                self.assertEqual(controller.requests, 1)

    def test_thumb_drag_does_not_load_but_following_wheel_does(self):
        for mode in ("continious", "tiles"):
            with self.subTest(mode=mode), self.scene(
                mode, animated=False,
            ) as (controller, _model, _surface, view, window):
                bar = next(
                    child for child in view.findChildren(QQuickItem)
                    if child.property("paginationBlocked") is not None
                )
                self.assertTrue(bar.isVisible())
                start = bar.mapToScene(QPointF(
                    bar.width() / 2,
                    max(4, bar.height() * bar.property("size") / 2),
                )).toPoint()
                end = bar.mapToScene(QPointF(
                    bar.width() / 2, bar.height() - 2,
                )).toPoint()
                QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
                for step in range(1, 9):
                    QTest.mouseMove(
                        window, start + (end - start) * (step / 8), delay=0,
                    )
                    self.app.processEvents()
                self.assertTrue(bar.property("paginationBlocked"))
                QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, end)
                self.wait_frame(window)
                self.wait_frame(window)
                self.assertTrue(view.property("atYEnd"))
                self.assertEqual(controller.requests, 0)
                self.wheel(view, window, angle=-120)
                self.wait_frame(window)
                self.assertEqual(controller.requests, 1)

    def test_restoring_bottom_and_switching_tabs_do_not_load(self):
        with self.scene(animated=False) as (
            controller, _model, surface, view, window,
        ):
            surface.restoreContentY(
                view.property("contentHeight"), 0, True, False,
            )
            self.wait_frame(window)
            self.assertTrue(view.property("atYEnd"))
            surface.setProperty("current", False)
            self.wait_frame(window)
            surface.setProperty("current", True)
            self.wait_frame(window)
            self.assertEqual(controller.requests, 0)
            self.wheel(view, window, angle=-120)
            self.wait_frame(window)
            self.assertEqual(controller.requests, 1)

    def test_touch_drag_reaching_bottom_requests_next_page(self):
        device = QTest.createTouchDevice()
        for mode in ("continious", "tiles"):
            with self.subTest(mode=mode), self.scene(
                mode, animated=False, node_type="group",
            ) as (controller, _model, _surface, view, window):
                # Start on a group header, not an sObject's drag-and-drop area.
                view.setProperty("contentY", (
                    view.property("originY") + view.property("contentHeight")
                    - view.height() - 100
                ))
                self.wait_frame(window)
                self.assertEqual(controller.requests, 0)
                start = view.mapToScene(QPointF(120, view.height() - 30)).toPoint()
                gesture = QTest.touchEvent(window, device, autoCommit=False)
                gesture.press(0, start, window).commit()
                self.wait_frame(window)
                for distance in (40, 80, 140, 220):
                    gesture.move(0, start - QPoint(0, distance), window).commit()
                    self.wait_frame(window)
                gesture.release(0, start - QPoint(0, 220), window).commit()
                self.wait_frame(window)
                self.assertTrue(view.property("atYEnd"))
                self.assertEqual(controller.requests, 1)

    def test_appended_page_keeps_tree_selection_and_scroll(self):
        from thlib.tactic_classes import SObject

        with self.scene(animated=False) as (
            controller, model, _surface, view, window,
        ):
            expanded = model.node_for("asset-0")
            child = WorkspaceNode(
                node_id="process-0", node_type="process", search_key="",
                code="model", title="model", depth=1, parent_id=expanded.node_id,
            )
            expanded.children = [child]
            expanded.expanded = True
            model.replace_nodes(list(model._roots))
            self.wait_frame(window)
            # Expanded rows can change ListView's estimated extent as the
            # first offscreen delegates are measured during scrolling.
            for _ in range(4):
                self.wheel(view, window)
                self.wait_frame(window)
                if view.property("atYEnd"):
                    break
            self.assertEqual(controller.requests, 1)
            content_y = view.property("contentY")
            reset = QSignalSpy(model.modelReset)
            model.append_sobjects([SObject({
                "code": f"NEW{index}", "name": f"New asset {index}",
                "__search_key__": f"demo/asset?project=demo&code=NEW{index}",
            }) for index in range(10)])
            self.wait_frame(window)

            self.assertEqual(reset.count(), 0)
            self.assertEqual(model.rowCount(), 41)
            self.assertIs(model.node_for("asset-0"), expanded)
            self.assertIs(model.node_for("process-0"), child)
            self.assertTrue(expanded.expanded)
            self.assertEqual(controller.selected_result_node_ids, ["asset-0"])
            self.assertAlmostEqual(view.property("contentY"), content_y, delta=1)
            self.assertEqual(controller.requests, 1)
            self.wheel(view, window)
            self.wait_frame(window)
            self.assertEqual(controller.requests, 2)

    def test_sorted_append_keeps_visible_rows_alive(self):
        from thlib.tactic_classes import SObject

        with self.scene(animated=False) as (
            _controller, model, _surface, view, window,
        ):
            self.wheel(view, window)
            self.wait_frame(window)
            anchor = next(
                child for child in view.property("contentItem").childItems()
                if child.property("nodeId") == "asset-29"
            )
            before_y = anchor.mapToScene(QPointF(0, 0)).y()
            removed = QSignalSpy(model.rowsRemoved)
            reset = QSignalSpy(model.modelReset)

            # SQL and natural name ordering differ. New page records can land
            # between loaded rows, not just at the end of the visible model.
            model.append_sobjects([SObject({
                "code": f"NEW{index}", "name": name,
                "__search_key__": f"demo/asset?project=demo&code=NEW{index}",
            }) for index, name in enumerate((
                "Asset 2.5", "Asset 10.5", "Z tail",
            ))])
            self.wait_frame(window)

            self.assertEqual(removed.count(), 0)
            self.assertEqual(reset.count(), 0)
            self.assertEqual(model.rowCount(), 33)
            self.assertEqual(anchor.property("nodeId"), "asset-29")
            self.assertAlmostEqual(
                anchor.mapToScene(QPointF(0, 0)).y(), before_y, delta=1,
            )

    def test_final_page_stops_requests_through_real_controller(self):
        from thlib.environment import env_inst
        from thlib.tactic_classes import SObject
        from thlib.ui.controller import ApplicationController
        from thlib.ui.controllers.types import SearchTabSession, SectionSession

        for page_size in (20, 3, 0):
            with self.subTest(final_page_size=page_size):
                controller = ApplicationController()
                self.addCleanup(controller.shutdown)
                initial = [SObject({
                    "code": f"ASSET{i}", "name": f"Asset {i}",
                    "__search_key__": f"demo/asset?project=demo&code=ASSET{i}",
                }) for i in range(30)]
                tab = SearchTabSession(
                    tab_id="assets", title="Assets", loaded=True,
                    sobjects=initial, next_offset=30, limit=20, total=50,
                )
                section = SectionSession(
                    entry_key="demo/asset", title="Assets", accent="#607d8b",
                    search_type="demo/asset", tabs=[tab],
                    current_tab_id=tab.tab_id,
                )
                controller._sessions = {section.entry_key: section}
                controller._current_section_key = section.entry_key
                controller._loading_mode = "infinite"
                controller.workspace_model.replace_sobjects(initial)
                for node in controller.workspace_model._roots:
                    node.preview_requested = True
                    node.card_preview_requested = True

                with (
                    patch.object(env_inst.server_pool, "start"),
                    patch.object(
                        env_inst.server_pool, "add_task", return_value=Mock(),
                    ) as query,
                    patch.object(controller, "request_item_preview"),
                    patch.object(controller, "request_item_card_preview"),
                    self.scene(
                        animated=False, controller=controller,
                        result_model=controller.workspace_model,
                    ) as (_controller, model, _surface, view, window),
                ):
                    self.wheel(view, window)
                    self.wait_frame(window)
                    self.assertEqual(query.call_count, 1)
                    self.assertEqual(query.call_args.kwargs["offset"], 30)
                    self.assertTrue(controller.loading_more)
                    self.wheel(view, window)
                    self.wait_frame(window)
                    self.assertEqual(query.call_count, 1)
                    removed = QSignalSpy(model.rowsRemoved)
                    final_page = [SObject({
                        "code": f"LAST{i}", "name": f"Z last {i}",
                        "__search_key__": f"demo/asset?project=demo&code=LAST{i}",
                    }) for i in range(page_size)]
                    controller._async_query_result((
                        final_page, {"total_sobjects_query_count": 50}, None,
                        (section.entry_key, tab.tab_id, True, tab.request_id, 30),
                    ))
                    self.wait_frame(window)
                    self.assertTrue(tab.exhausted)
                    self.assertFalse(controller.has_more)
                    self.assertFalse(controller.loading_more)
                    for _ in range(4):
                        self.wheel(view, window)
                        self.wait_frame(window)
                    self.assertEqual(query.call_count, 1)
                    self.assertTrue(view.property("atYEnd"))
                    self.assertEqual(removed.count(), 0)


if __name__ == "__main__":
    unittest.main()
