"""Native value snapshots and resize batching, using real QML and input state."""

import copy
from types import SimpleNamespace
import unittest

from PySide6.QtCore import Property, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression

from tests.profile_ui_responsiveness import frame
from tests.qt_application import gui_test_application
from tests import test_frame_table as frames
from tests.test_page_layout_editor import DOCUMENT
from thlib.ui.admin.dashboard import DashboardEditor


class CountingEditor(DashboardEditor):
    reads = 0

    @Property('QVariantMap', notify=DashboardEditor.stateChanged)
    def document(self):
        self.reads += 1
        return self._document

    @Property('QVariantMap', notify=DashboardEditor.stateChanged)
    def metadata(self):
        self.reads += 1
        return self._metadata


class NativeSnapshotTests(unittest.TestCase):
    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close

    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_page_snapshot_is_detached_and_updates_at_the_same_identity(self):
        host = CountingEditor(SimpleNamespace(can_manage_tools=True, debug_log=None))
        self.addCleanup(host.shutdown)
        host._document = copy.deepcopy(DOCUMENT)
        host._original = copy.deepcopy(DOCUMENT)
        host._identity = 'review'
        host._can_write = host._loaded = True
        owner = QObject(host)
        host._metadata = dict(
            dataBusy=False, application=owner, sourceXml='<config/>',
            checkedDocument=copy.deepcopy(DOCUMENT),
        )
        window, view = self.create(
            'features/administration/layouts/PageLayoutEditorView.qml',
            dict(controller=host), width=1400, height=900,
        )
        engine = QQmlEngine.contextForObject(view).engine()

        def evaluate(source):
            expression = QQmlExpression(engine.rootContext(), view, source)
            result, _ = expression.evaluate()
            self.assertFalse(expression.hasError(), expression.error().toString())
            return result

        self.assertLess(
            host.reads, 100, 'Nested rendering must not re-fetch QVariant properties'
        )
        self.assertTrue(evaluate(
            'editorSnapshot.metadata.application === '
            'controller.metadata.application'
        ))
        evaluate("editorSnapshot.document.title = 'Local mutation'")
        evaluate("editorSnapshot.document.blocks[0].title = 'Nested mutation'")
        self.assertEqual(host._document, DOCUMENT)
        host._document['title'] = 'Updated page'
        host._metadata['dataBusy'] = True
        host.stateChanged.emit()
        frame(window)
        self.assertEqual(evaluate('editorSnapshot.document.title'), 'Updated page')
        self.assertTrue(evaluate('editorSnapshot.metadata.dataBusy'))
        self.assertLess(host.reads, 100)


class NativeResizeTests(unittest.TestCase):
    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    item = frames.FrameTableTests.item

    @classmethod
    def setUpClass(cls):
        cls.app = gui_test_application()

    def test_resize_batch_reaches_deep_children_in_one_frame(self):
        window, view = self.create('tactic_frame/core/FrameView.qml', {})
        engine = QQmlEngine.contextForObject(view).engine()
        component = QQmlComponent(engine, QUrl.fromLocalFile(str(
            frames.QML / 'tactic_frame/core/FrameViewport.qml'
        )))
        viewport = component.createWithInitialProperties(dict(target=view))
        self.assertIsNotNone(
            viewport, [error.toString() for error in component.errors()]
        )
        viewport.setParent(view)
        engine.rootContext().setContextProperty('resizeViewport', viewport)

        def evaluate(source):
            expression = QQmlExpression(QQmlEngine.contextForObject(view), view, source)
            result, _ = expression.evaluate()
            self.assertFalse(expression.hasError(), expression.error().toString())
            return result
        nested = """
            function nested(width, height) {
                let child = Contract.label('resizeLeaf', Contract.rect(0, 0, width, height), 'Stable');
                for (let depth = 0; depth < 8; depth++)
                    child = Contract.node('Box', 'resizeBox' + depth, Contract.rect(0, 0, width, height), {children: [child]});
                return {nodes: [child]};
            }
        """
        evaluate(nested + 'scene = Qt.binding(() => '
                 'nested(resizeViewport.size.width, resizeViewport.size.height));')
        frame(window)
        leaf = self.item(view, 'resizeLeaf')
        changes = []
        leaf.widthChanged.connect(lambda: changes.append(leaf.width()))
        for size in range(201, 221):
            view.setWidth(size)
            view.setHeight(size - 100)
        frame(window)
        self.assertIs(self.item(view, 'resizeLeaf'), leaf)
        self.assertEqual(leaf.width(), 220)
        self.assertEqual(leaf.height(), 120)
        self.assertEqual(changes, [220])
        view.setWidth(220.5)
        view.setHeight(120.25)
        frame(window)
        self.assertEqual(leaf.width(), 220.5)
        self.assertEqual(leaf.height(), 120.25)
        evaluate("scene = {nodes: [Contract.label('now', Contract.rect(0, 0, 80, 20), 'Immediate')]};")
        self.assertEqual(self.item(view, 'now').property('text'), 'Immediate')


if __name__ == '__main__':
    unittest.main()
