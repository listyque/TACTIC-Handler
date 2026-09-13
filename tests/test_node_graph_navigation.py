"""Real pointer navigation and port/body arbitration in the shared graph."""

import copy
import os
from pathlib import Path
import time
import unittest

from PySide6.QtCore import QCoreApplication, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QSignalSpy, QTest

from tests.profile_ui_responsiveness import frame
from tests import test_administration_qml as administration_fixture


class NodeGraphNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        administration_fixture.AdministrationQmlTests.setUpClass()

    def setUp(self):
        self.fixture = administration_fixture.AdministrationQmlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.window = self.fixture.window
        self.window.resize(1400, 940)
        self.editor = self.fixture.admin.schemaEditor
        self.editor.apply_xml('<schema><search_type name="demo/asset" xpos="20" ypos="30"/>'
                              '<search_type name="demo/shot" xpos="360" ypos="100"/></schema>')
        self.fixture.click('adminSection_schema')
        self.canvas = self.fixture.item('adminGraphCanvas')
        self.graph = self.canvas.parentItem()

    def center(self, item):
        return item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()

    def drag(self, start, delta, button):
        QTest.mousePress(self.window, button, pos=start)
        QTest.mouseMove(self.window, start + delta / 2)
        QTest.mouseMove(self.window, start + delta)
        frame(self.window)
        QTest.mouseRelease(self.window, button, pos=start + delta)
        frame(self.window)

    def click(self, item, modifiers=Qt.NoModifier):
        QTest.mouseClick(self.window, Qt.LeftButton, modifiers, pos=self.center(item))
        frame(self.window)

    def wheel(self, point, delta):
        event = QWheelEvent(QPointF(point), QPointF(self.window.mapToGlobal(point)),
                            QPoint(), QPoint(0, delta), Qt.NoButton, Qt.NoModifier,
                            Qt.NoScrollPhase, False)
        event.setTimestamp(time.monotonic_ns() // 1_000_000)
        QCoreApplication.sendEvent(self.window, event)
        frame(self.window)

    def test_wheel_zooms_at_the_cursor_without_mutating_nodes(self):
        node = self.fixture.item('graphNode_demo/asset')
        cursor = self.center(node)
        original = copy.deepcopy(self.editor.document)
        self.wheel(cursor, 120)
        self.assertGreater(self.graph.property('zoom'), 1)
        self.assertLessEqual((self.center(node) - cursor).manhattanLength(), 2)
        self.wheel(cursor, -120)
        self.assertAlmostEqual(self.graph.property('zoom'), 1)
        self.assertLessEqual((self.center(node) - cursor).manhattanLength(), 2)
        self.assertEqual(self.editor.document, original)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_middle_drag_pans_over_nodes_and_extends_in_all_directions(self):
        node = self.fixture.item('graphNode_demo/asset')
        original = copy.deepcopy(self.editor.document)
        start = self.center(node)
        self.drag(start, QPoint(110, 55), Qt.MiddleButton)
        self.assertLessEqual((self.center(node) - start - QPoint(110, 55)).manhattanLength(), 2)
        for delta in (QPoint(180, 100), QPoint(180, 100), QPoint(-350, -200),
                      QPoint(-350, -200), QPoint(340, 200)):
            before = self.center(node)
            self.drag(self.center(self.canvas), delta, Qt.MiddleButton)
            self.assertLessEqual((self.center(node) - before - delta).manhattanLength(), 2)
        self.assertEqual(self.editor.document, original)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_port_press_with_pointer_movement_never_drags_the_node(self):
        node = self.fixture.item('graphNode_demo/asset')
        output = self.fixture.item('graphOutput_demo/asset')
        before = copy.deepcopy(self.editor.document)
        start = self.center(output) - QPoint(1, 0)
        self.drag(start, QPoint(-12, 0), Qt.LeftButton)
        self.assertEqual(self.editor.document, before)
        self.assertEqual(node.x(), 20)
        self.assertEqual(self.graph.property('pendingConnection'), 'demo/asset')
        self.fixture.click('graphInput_demo/shot')
        self.assertEqual(self.editor.edges[0]['from'], 'demo/asset')
        self.assertEqual(self.editor.edges[0]['to'], 'demo/shot')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_input_can_start_a_connection_without_selecting_or_moving_the_node(self):
        self.fixture.click('graphInput_demo/shot')
        self.assertEqual(self.graph.property('pendingConnection'), 'demo/shot')
        self.fixture.click('graphOutput_demo/asset')
        self.assertEqual(len(self.editor.edges), 1)
        self.assertEqual(self.editor.edges[0]['from'], 'demo/asset')
        self.assertEqual(self.editor.edges[0]['to'], 'demo/shot')
        self.assertEqual(self.editor.selectedNode, '')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def assert_preview_endpoints(self, port, cursor, input_port=False):
        preview = self.fixture.item('graphPendingConnection')
        start = preview.mapToScene(QPointF(preview.property('startX') - preview.x(),
                                          preview.property('startY') - preview.y())).toPoint()
        end = preview.mapToScene(QPointF(preview.property('endX') - preview.x(),
                                        preview.property('endY') - preview.y())).toPoint()
        fixed, moving = (end, start) if input_port else (start, end)
        self.assertLessEqual((fixed - self.center(port)).manhattanLength(), 2)
        self.assertLessEqual((moving - cursor).manhattanLength(), 2)
        self.assertEqual(preview.property('accent'), port.property('accent'))
        self.assertFalse(preview.property('selected'))

    def test_connection_preview_follows_cursor_from_either_port_before_committing(self):
        for input_port in (False, True):
            with self.subTest(input_port=input_port):
                original = copy.deepcopy(self.editor.document)
                changes = QSignalSpy(self.editor.graphChanged)
                port_name = 'graphInput_demo/shot' if input_port else 'graphOutput_demo/asset'
                other_port = 'graphOutput_demo/asset' if input_port else 'graphInput_demo/shot'
                port = self.fixture.item(port_name)
                self.fixture.click(port_name)
                self.assert_preview_endpoints(port, self.center(port), input_port)
                for offset in (QPoint(80, 110), QPoint(180, 150), QPoint(-60, 160)):
                    cursor = self.center(port) + offset
                    QTest.mouseMove(self.window, cursor)
                    frame(self.window)
                    self.assert_preview_endpoints(port, cursor, input_port)
                self.assertEqual(changes.count(), 0)
                self.assertEqual(self.editor.document, original)
                self.fixture.click(other_port)
                self.assertEqual(self.editor.edges[0]['from'], 'demo/asset')
                self.assertEqual(self.editor.edges[0]['to'], 'demo/shot')
                self.assertEqual(len(self.editor.edges), 1)
                with self.assertRaises(StopIteration):
                    self.fixture.item('graphPendingConnection')
                self.editor.apply_xml(original['xml'])
                frame(self.window)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_preview_tracks_pan_zoom_and_scroll_without_rebuilding_connections(self):
        self.editor.connect_nodes('demo/asset', 'demo/shot')
        frame(self.window)
        original = copy.deepcopy(self.editor.document)
        for width, height in ((900, 620), (1400, 940)):
            with self.subTest(width=width):
                self.window.resize(width, height)
                frame(self.window)
                self.fixture.click('graphOutput_demo/asset')
                port = self.fixture.item('graphOutput_demo/asset')
                connection = self.fixture.item('graphConnection_0')
                cursor = self.canvas.mapToScene(QPointF(
                    self.canvas.width() - 60, self.canvas.height() - 50)).toPoint()
                QTest.mouseMove(self.window, cursor)
                frame(self.window)
                self.assert_preview_endpoints(port, cursor)
                self.wheel(cursor, 120)
                self.assert_preview_endpoints(port, cursor)
                self.drag(cursor, QPoint(-35, -20), Qt.MiddleButton)
                cursor -= QPoint(35, 20)
                self.assert_preview_endpoints(port, cursor)
                self.canvas.setProperty('contentX', self.canvas.property('contentX') + 20)
                self.canvas.setProperty('contentY', self.canvas.property('contentY') + 15)
                frame(self.window)
                self.assert_preview_endpoints(port, cursor)
                self.assertIs(self.fixture.item('graphConnection_0'), connection)
                self.assertTrue(self.canvas.property('clip'))
                output = os.environ.get('NODE_GRAPH_SCREENSHOTS')
                if output:
                    directory = Path(output)
                    directory.mkdir(parents=True, exist_ok=True)
                    self.window.grabWindow().save(str(directory / ('connection_preview_' + str(width) + '.png')))
                QTest.keyClick(self.window, Qt.Key_Escape)
                frame(self.window)
                self.assertEqual(self.graph.property('pendingConnection'), '')
        self.assertEqual(self.editor.document, original)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_pending_preview_cancels_without_creating_a_connection(self):
        original = copy.deepcopy(self.editor.document)
        for action in ('escape', 'same_port', 'hide', 'readonly', 'reload'):
            with self.subTest(action=action):
                self.fixture.click('graphOutput_demo/asset')
                self.assertEqual(self.graph.property('pendingConnection'), 'demo/asset')
                if action == 'escape':
                    QTest.keyClick(self.window, Qt.Key_Escape)
                elif action == 'same_port':
                    self.fixture.click('graphOutput_demo/asset')
                elif action == 'hide':
                    self.fixture.click('segmentedButtonSegment_technical')
                elif action == 'readonly':
                    self.editor._can_write = False
                    self.editor.stateChanged.emit()
                else:
                    self.editor.apply_xml(original['xml'])
                frame(self.window)
                self.assertEqual(self.graph.property('pendingConnection'), '')
                with self.assertRaises(StopIteration):
                    self.fixture.item('graphPendingConnection')
                self.assertEqual(self.editor.document, original)
                if action == 'hide':
                    self.fixture.click('segmentedButtonSegment_canvas')
                elif action == 'readonly':
                    self.editor._can_write = True
                    self.editor.stateChanged.emit()
                    frame(self.window)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_drag_preserves_negative_world_coordinates_and_publishes_once(self):
        node = self.fixture.item('graphNode_demo/asset')
        changes = QSignalSpy(self.editor.graphChanged)
        self.drag(self.center(node), QPoint(-90, -75), Qt.LeftButton)
        self.assertLess(self.editor.nodes[0]['nodeX'], 0)
        self.assertLess(self.editor.nodes[0]['nodeY'], 0)
        self.assertEqual(changes.count(), 1)
        saved = self.editor.document['xml']
        self.editor.apply_xml(saved)
        self.assertLess(self.editor.nodes[0]['nodeX'], 0)
        self.assertLess(self.editor.nodes[0]['nodeY'], 0)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_shift_ctrl_selection_and_group_drag_share_one_atomic_move(self):
        asset = self.fixture.item('graphNode_demo/asset')
        shot = self.fixture.item('graphNode_demo/shot')
        self.click(asset)
        self.click(shot, Qt.ShiftModifier)
        self.assertEqual(self.editor.selectedNodes, ['demo/asset', 'demo/shot'])
        before = {row['identity']: (row['nodeX'], row['nodeY']) for row in self.editor.nodes}
        changes = QSignalSpy(self.editor.graphChanged)
        self.drag(self.center(asset), QPoint(70, 45), Qt.LeftButton)
        after = {row['identity']: (row['nodeX'], row['nodeY']) for row in self.editor.nodes}
        for identity in before:
            self.assertAlmostEqual(after[identity][0], before[identity][0] + 70, delta=0.1)
            self.assertAlmostEqual(after[identity][1], before[identity][1] + 45, delta=0.1)
        self.assertEqual(changes.count(), 1)
        asset = self.fixture.item('graphNode_demo/asset')
        self.click(asset, Qt.ControlModifier)
        self.assertEqual(self.editor.selectedNodes, ['demo/shot'])
        self.assertEqual(self.editor.selectedNode, 'demo/shot')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_background_marquee_selects_intersecting_nodes(self):
        asset = self.fixture.item('graphNode_demo/asset')
        shot = self.fixture.item('graphNode_demo/shot')
        start = asset.mapToScene(QPointF(-45, -25)).toPoint()
        end = shot.mapToScene(QPointF(shot.width() + 45, shot.height() + 25)).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        try:
            QTest.mouseMove(self.window, (start + end) / 2)
            QTest.mouseMove(self.window, end)
            frame(self.window)
            self.assertTrue(self.fixture.item('graphSelectionRectangle').isVisible())
        finally:
            QTest.mouseRelease(self.window, Qt.LeftButton, pos=end)
        frame(self.window)
        self.assertEqual(self.editor.selectedNodes, ['demo/asset', 'demo/shot'])
        self.assertFalse(self.fixture.item('graphSelectionRectangle').isVisible())
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_arrange_button_opens_the_shared_layout_picker(self):
        self.fixture.click('adminArrangeGraph')
        menu = self.window.findChild(QObject, 'adminArrangeMenu')
        self.assertIsNotNone(menu)
        self.assertTrue(menu.property('visible'))
        QTest.keyClick(menu.property('contentItem').window(), Qt.Key_Escape)
        frame(self.window)
        self.assertFalse(menu.property('visible'))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_drag_near_viewport_edge_expands_and_pans_before_release(self):
        node = self.fixture.item('graphNode_demo/asset')
        start = self.center(node)
        end = self.canvas.mapToScene(QPointF(self.canvas.width() - 2, self.canvas.height() / 2)).toPoint()
        old_width = self.canvas.property('contentWidth')
        changes = QSignalSpy(self.editor.graphChanged)
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        try:
            QTest.mouseMove(self.window, (start + end) / 2)
            QTest.mouseMove(self.window, end)
            frame(self.window)
            first_position = node.x()
            for _ in range(3):
                frame(self.window)
            self.assertGreater(node.x(), first_position)
            self.assertGreater(self.canvas.property('contentWidth'), old_width)
            self.assertEqual(changes.count(), 0)
            self.assertEqual(self.editor.nodes[0]['nodeX'], 20)
            self.assertLessEqual(abs(self.center(node).x() - end.x()), 2)
        finally:
            QTest.mouseRelease(self.window, Qt.LeftButton, pos=end)
        frame(self.window)
        self.assertEqual(changes.count(), 1)
        self.assertGreater(self.editor.nodes[0]['nodeX'], 20)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_node_drag_after_zoom_and_pan_uses_world_not_screen_units(self):
        node = self.fixture.item('graphNode_demo/asset')
        self.wheel(self.center(node), 480)
        zoom = self.graph.property('zoom')
        self.drag(self.center(node), QPoint(100, 80), Qt.MiddleButton)
        self.drag(self.center(node), QPoint(70, 45), Qt.LeftButton)
        self.assertAlmostEqual(self.editor.nodes[0]['nodeX'], 20 + 70 / zoom, delta=0.1)
        self.assertAlmostEqual(self.editor.nodes[0]['nodeY'], 30 + 45 / zoom, delta=0.1)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_touch_connects_ports_once_and_readonly_keeps_navigation(self):
        device = QTest.createTouchDevice()
        for name in ('graphOutput_demo/asset', 'graphInput_demo/shot'):
            point = self.center(self.fixture.item(name))
            sequence = QTest.touchEvent(self.window, device, autoCommit=False)
            sequence.press(0, point, self.window).commit()
            frame(self.window)
            sequence.release(0, point, self.window).commit()
            frame(self.window)
            if name == 'graphOutput_demo/asset':
                self.assert_preview_endpoints(self.fixture.item(name), point)
            else:
                self.assertEqual(self.graph.property('pendingConnection'), '')
        self.assertEqual(len(self.editor.edges), 1)
        self.editor._can_write = False
        self.editor.stateChanged.emit()
        frame(self.window)
        self.assertFalse(self.fixture.item('graphOutput_demo/asset').isEnabled())
        original = copy.deepcopy(self.editor.document)
        self.wheel(self.center(self.canvas), 120)
        self.assertGreater(self.graph.property('zoom'), 1)
        self.drag(self.center(self.canvas), QPoint(100, 50), Qt.MiddleButton)
        self.assertEqual(self.editor.document, original)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_navigation_keeps_gutters_and_clipping_at_narrow_and_wide_sizes(self):
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            frame(self.window)
            self.drag(self.center(self.canvas), QPoint(80, 60), Qt.MiddleButton)
            self.wheel(self.center(self.canvas), 120)
            self.assertTrue(self.canvas.property('clip'))
            top_left = self.canvas.mapToScene(QPointF())
            right = top_left.x() + self.canvas.width()
            bottom = top_left.y() + self.canvas.height()
            vertical = self.fixture.item('adminGraphVerticalBar')
            horizontal = self.fixture.item('adminGraphHorizontalBar')
            self.assertGreaterEqual(vertical.mapToScene(QPointF()).x(), right)
            self.assertGreaterEqual(horizontal.mapToScene(QPointF()).y(), bottom)
            self.assertLessEqual(right, self.window.width())
            self.assertLessEqual(bottom, self.window.height())
            output = os.environ.get('NODE_GRAPH_SCREENSHOTS')
            if output:
                directory = Path(output)
                directory.mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(directory / ('navigation_' + str(width) + '.png')))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_hidden_canvas_cancels_uncommitted_drag_and_stops_autopan(self):
        node = self.fixture.item('graphNode_demo/asset')
        start = self.center(node)
        original = copy.deepcopy(self.editor.document)
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        try:
            QTest.mouseMove(self.window, start + QPoint(30, 15))
            QTest.mouseMove(self.window, start + QPoint(80, 35))
            frame(self.window)
            self.assertGreater(node.x(), 20)
            self.graph.setProperty('visible', False)
            frame(self.window)
            self.assertIsNone(self.graph.property('draggedNode'))
            self.assertFalse(self.graph.findChild(QObject, 'graphDragAutoPan').property('running'))
            self.assertEqual(node.x(), 20)
            self.assertEqual(node.y(), 30)
        finally:
            QTest.mouseRelease(self.window, Qt.LeftButton, pos=start + QPoint(80, 35))
        self.graph.setProperty('visible', True)
        frame(self.window)
        self.assertEqual(self.editor.document, original)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_escape_cancels_a_drag_even_when_the_node_was_not_selected(self):
        node = self.fixture.item('graphNode_demo/asset')
        start = self.center(node)
        original = copy.deepcopy(self.editor.document)
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        try:
            QTest.mouseMove(self.window, start + QPoint(30, 15))
            QTest.mouseMove(self.window, start + QPoint(80, 35))
            frame(self.window)
            self.assertGreater(node.x(), 20)
            QTest.keyClick(self.window, Qt.Key_Escape)
            frame(self.window)
            self.assertIsNone(self.graph.property('draggedNode'))
            self.assertEqual(node.x(), 20)
        finally:
            QTest.mouseRelease(self.window, Qt.LeftButton, pos=start + QPoint(80, 35))
        frame(self.window)
        self.assertEqual(self.editor.document, original)
        self.assertEqual(self.fixture.fixture.warnings, [])


if __name__ == '__main__':
    unittest.main()
