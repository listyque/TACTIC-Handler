"""Actual pixels of the shared graph on software and RHI, without MSAA layers."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from tests.profile_ui_responsiveness import frame
from thlib.environment import env_mode


ROOT = Path(__file__).resolve().parents[1]


class NodeGraphRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        os.environ.setdefault('QT_QUICK_BACKEND', 'software')
        os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Material')
        if os.name == 'nt':
            os.environ.setdefault('QT_QPA_FONTDIR', str(Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'))
        cls.app = QGuiApplication.instance() or QGuiApplication([])

    def setUp(self):
        original_text_rendering = QQuickWindow.textRenderType()
        QQuickWindow.setTextRenderType(QQuickWindow.NativeTextRendering)
        self.addCleanup(QQuickWindow.setTextRenderType, original_text_rendering)
        directory = self.enterContext(TemporaryDirectory(prefix='tactic-graph-render-'))
        self.enterContext(patch.object(env_mode, 'current_path', directory))
        self.enterContext(patch('socket.create_connection', side_effect=AssertionError('Offline graph test')))
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda errors: self.warnings.extend(error.toString() for error in errors))
        qml = ROOT / 'thlib/ui/qml'
        self.engine.addImportPath(str(qml))
        self.theme_component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(qml / 'Theme.qml')))
        self.theme = self.theme_component.createWithInitialProperties({'dark': True})
        self.component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(qml / 'controls/NodeGraph.qml')))
        self.graph = self.component.createWithInitialProperties({
            'theme': self.theme, 'width': 900, 'height': 620,
            'nodes': [
                {'identity': 'source', 'label': 'Source node', 'nodeX': 50, 'nodeY': 40,
                 'kind': 'manual', 'color': '#78a6c4', 'referenceOnly': False},
                {'identity': 'target', 'label': 'Progress', 'nodeX': 470, 'nodeY': 280,
                 'kind': 'progress', 'color': '#9977aa', 'referenceOnly': False},
            ],
            'edges': [{'from': 'source', 'to': 'target', 'edgeIndex': 0}],
        })
        self.assertIsNotNone(self.graph, [error.toString() for error in self.component.errors()])
        self.window = QQuickWindow()
        self.window.resize(900, 620)
        self.graph.setParentItem(self.window.contentItem())
        self.addCleanup(self.close_graph)
        self.window.show()
        frame(self.window)

    def close_graph(self):
        self.window.close()
        self.graph.setParentItem(None)
        self.graph.deleteLater()
        self.window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.theme.deleteLater()
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def evaluate(self, item, expression):
        self.assertIsNotNone(item)
        context = QQmlEngine.contextForObject(item)
        self.assertIsNotNone(context)
        evaluator = QQmlExpression(context, item, expression)
        value, _undefined = evaluator.evaluate()
        self.assertFalse(evaluator.hasError(), evaluator.error().toString())
        return value

    @staticmethod
    def descendants(item):
        for child in item.childItems():
            yield child
            yield from NodeGraphRenderingTests.descendants(child)

    def item(self, name):
        return next(item for item in self.descendants(self.graph) if item.objectName() == name)

    def assert_edge_coverage(self, image, center, accent, radius=10):
        """A diagonal solid path must have coverage pixels, not a binary stair edge."""
        # Software grabWindow returns physical pixels but may leave the QImage
        # DPR metadata at 1. Use the actual window/image geometry on every backend.
        ratio = image.width() / self.window.width()
        self.assertAlmostEqual(ratio, image.height() / self.window.height())
        x, y = round(center.x() * ratio), round(center.y() * ratio)
        size = round(radius * ratio)
        self.assertTrue(size <= x < image.width() - size)
        self.assertTrue(size <= y < image.height() - size)
        background = self.theme.property('workspace')
        colors = {image.pixelColor(px, py).rgb()
                  for px in range(x - size, x + size)
                  for py in range(y - size, y + size)}
        coverage = colors - {background.rgb(), accent.rgb()}
        self.assertGreater(len(coverage), 4, 'No smooth pixel coverage at the diagonal edge')

    @staticmethod
    def variant(value):
        return value.toVariant() if hasattr(value, 'toVariant') else value

    def bind_selection(self):
        self.selection_events = []
        def update(identities, primary):
            identities = self.variant(identities)
            self.selection_events.append((identities, primary))
            self.graph.setProperty('selectedNode', primary)
            self.graph.setProperty('selectedNodes', identities)

        self.graph.nodesSelected.connect(update)

    def test_curves_and_direction_arrows_have_smooth_edges_at_fractional_zoom(self):
        connector = self.item('graphConnection_0')
        arrow = self.item('graphDirectionArrow')
        for zoom in (0.65, 1.0, 1.6):
            with self.subTest(zoom=zoom):
                self.graph.setProperty('zoom', zoom)
                QTest.mouseMove(self.window, QPoint(10, 610))
                frame(self.window)
                image = self.window.grabWindow()
                self.assertFalse(image.isNull())
                output = os.environ.get('NODE_GRAPH_RENDER_SCREENSHOTS')
                if output:
                    directory = Path(output)
                    directory.mkdir(parents=True, exist_ok=True)
                    self.assertTrue(image.save(str(directory / f'graph-{zoom}.png')))
                point = self.evaluate(connector, 'curvePoint(0.25)')
                curve_center = connector.mapToScene(QPointF(point.x() - connector.x(),
                                                            point.y() - connector.y()))
                self.assert_edge_coverage(image, curve_center, connector.property('accent'))
                arrow_center = arrow.mapToScene(QPointF(arrow.width() / 2, arrow.height() / 2))
                self.assert_edge_coverage(image, arrow_center, connector.property('accent'))
        self.assertEqual(self.warnings, [])

    def test_graph_uses_local_curve_antialiasing_and_scalable_node_labels(self):
        shapes = [item for item in self.descendants(self.graph) if item.inherits('QQuickShape')]
        self.assertEqual(len(shapes), 2)
        renderer = 'SoftwareRenderer' if os.environ.get('QT_QUICK_BACKEND') == 'software' else 'CurveRenderer'
        for shape in shapes:
            self.assertTrue(self.evaluate(shape, 'preferredRendererType === Shape.CurveRenderer'))
            self.assertTrue(self.evaluate(shape, 'rendererType === Shape.' + renderer))
            self.assertTrue(shape.property('antialiasing'))
            self.assertFalse(self.evaluate(shape, 'layer.enabled'))
        self.assertFalse(self.evaluate(self.graph, 'layer.enabled'))
        node = self.item('graphNode_source')
        labels = [item for item in self.descendants(node) if item.inherits('QQuickText')]
        self.assertEqual(len(labels), 2)
        for label in labels:
            self.assertTrue(self.evaluate(label, 'renderType === Text.QtRendering'))
        for item in self.descendants(node):
            if item.inherits('QQuickRectangle'):
                self.assertTrue(item.property('antialiasing'))
                self.assertFalse(self.evaluate(item, 'border.pixelAligned'))
        self.assertEqual(self.warnings, [])

    def test_pending_connection_keeps_smooth_edges_while_following_the_pointer(self):
        port = self.item('graphOutput_source')
        center = port.mapToScene(QPointF(port.width() / 2, port.height() / 2)).toPoint()
        QTest.mouseClick(self.window, Qt.LeftButton, pos=center)
        frame(self.window)
        self.assertEqual(self.graph.property('pendingConnection'), 'source')
        for cursor in (QPoint(680, 430), QPoint(640, 510)):
            QTest.mouseMove(self.window, cursor)
            frame(self.window)
            connector = self.item('graphPendingConnection')
            point = self.evaluate(connector, 'curvePoint(0.25)')
            center = connector.mapToScene(QPointF(point.x() - connector.x(), point.y() - connector.y()))
            self.assert_edge_coverage(self.window.grabWindow(), center, connector.property('accent'))
        QTest.keyClick(self.window, Qt.Key_Escape)
        frame(self.window)
        self.assertEqual(self.graph.property('pendingConnection'), '')
        self.assertEqual(self.warnings, [])

    def test_modifier_selection_and_group_drag_emit_one_atomic_position_set(self):
        self.bind_selection()
        source = self.item('graphNode_source')
        target = self.item('graphNode_target')
        QTest.mouseClick(self.window, Qt.LeftButton, pos=source.mapToScene(
            QPointF(source.width() / 2, source.height() / 2)).toPoint())
        frame(self.window)
        self.assertEqual(self.variant(self.graph.property('selectedNodes')), ['source'])
        QTest.keyPress(self.window, Qt.Key_Shift)
        self.assertTrue(self.graph.property('activeSelectionModifiers') & Qt.ShiftModifier.value)
        QTest.mouseClick(self.window, Qt.LeftButton, pos=target.mapToScene(
            QPointF(target.width() / 2, target.height() / 2)).toPoint())
        QTest.keyRelease(self.window, Qt.Key_Shift)
        frame(self.window)
        self.assertEqual(self.variant(self.graph.property('selectedNodes')), ['source', 'target'],
                         self.selection_events)

        moved = QSignalSpy(self.graph.nodesMoved)
        start = source.mapToScene(QPointF(source.width() / 2, source.height() / 2)).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        QTest.mouseMove(self.window, start + QPoint(35, 20))
        QTest.mouseMove(self.window, start + QPoint(70, 40))
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=start + QPoint(70, 40))
        frame(self.window)
        self.assertEqual(moved.count(), 1)
        positions = self.variant(moved.at(0)[0])
        self.assertEqual({row['identity'] for row in positions}, {'source', 'target'})
        for row in positions:
            original = {'source': (50, 40), 'target': (470, 280)}[row['identity']]
            self.assertAlmostEqual(row['nodeX'], original[0] + 70, delta=0.1)
            self.assertAlmostEqual(row['nodeY'], original[1] + 40, delta=0.1)

        source = self.item('graphNode_source')
        QTest.qWait(200)
        QTest.keyPress(self.window, Qt.Key_Control)
        QTest.mouseClick(self.window, Qt.LeftButton, pos=source.mapToScene(
            QPointF(source.width() / 2, source.height() / 2)).toPoint())
        QTest.keyRelease(self.window, Qt.Key_Control)
        frame(self.window)
        self.assertEqual(self.variant(self.graph.property('selectedNodes')), ['target'])
        self.assertEqual(self.warnings, [])

    def test_background_drag_draws_marquee_and_selects_both_nodes(self):
        self.bind_selection()
        canvas = self.item('adminGraphCanvas')
        rectangle = self.item('graphSelectionRectangle')
        start = canvas.mapToScene(QPointF(12, 12)).toPoint()
        end = canvas.mapToScene(QPointF(canvas.width() - 40, canvas.height() - 80)).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        QTest.mouseMove(self.window, (start + end) / 2)
        QTest.mouseMove(self.window, end)
        frame(self.window)
        self.assertTrue(rectangle.isVisible())
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=end)
        frame(self.window)
        self.assertFalse(rectangle.isVisible())
        self.assertEqual(self.variant(self.graph.property('selectedNodes')), ['source', 'target'])
        source = self.item('graphNode_source')
        source_start = source.mapToScene(QPointF(-45, -20)).toPoint()
        source_end = source.mapToScene(QPointF(source.width() + 45, source.height() + 20)).toPoint()
        QTest.keyPress(self.window, Qt.Key_Control)
        QTest.mousePress(self.window, Qt.LeftButton, pos=source_start)
        QTest.mouseMove(self.window, source_end)
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=source_end)
        QTest.keyRelease(self.window, Qt.Key_Control)
        frame(self.window)
        self.assertEqual(self.variant(self.graph.property('selectedNodes')), ['target'])
        QTest.keyPress(self.window, Qt.Key_Shift)
        QTest.mousePress(self.window, Qt.LeftButton, pos=source_start)
        QTest.mouseMove(self.window, source_end)
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=source_end)
        QTest.keyRelease(self.window, Qt.Key_Shift)
        frame(self.window)
        self.assertEqual(self.variant(self.graph.property('selectedNodes')), ['target', 'source'])
        self.assertEqual(self.warnings, [])


if __name__ == '__main__':
    unittest.main()
