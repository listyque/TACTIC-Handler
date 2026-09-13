"""Keyboard commands through the real schema/workflow canvas and dialogs."""

import copy
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPointF, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest

from tests import test_admin_graph_forms as graph_fixture
from tests.profile_ui_responsiveness import frame


class NodeGraphShortcutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph_fixture.AdminGraphFormsTests.setUpClass()

    def setUp(self):
        self.ui = graph_fixture.AdminGraphFormsTests()
        self.ui.setUp()
        self.addCleanup(self.ui.doCleanups)
        self.window = self.ui.window
        self.enterContext(patch(
            'socket.create_connection', side_effect=AssertionError('Graph tests must run offline')))

    def open_graph(self, mode):
        self.ui.click('adminSection_' + mode)
        editor = self.ui.admin.schemaEditor if mode == 'schema' else self.ui.admin.workflowEditor
        return editor, self.ui.item('adminGraphCanvas').parentItem()

    def key(self, key, modifiers=Qt.NoModifier):
        QTest.keyClick(self.window, key, modifiers)
        frame(self.window)

    def dialog_visible(self, name):
        return any(dialog.property('visible') for dialog in self.window.findChildren(QObject, name))

    def test_delete_node_confirms_and_only_changes_the_current_draft_in_both_editors(self):
        for mode, identity in (('schema', 'demo/asset'), ('workflow', 'model')):
            with self.subTest(mode=mode):
                editor, _graph = self.open_graph(mode)
                original = copy.deepcopy(editor.document)
                with patch.object(editor, '_request') as request:
                    self.ui.click('graphNode_' + identity)
                    self.key(Qt.Key_Delete)
                    self.assertTrue(self.dialog_visible('adminRemoveGraphConfirmation'))
                    self.assertEqual(editor.document, original)
                    self.key(Qt.Key_Escape)
                    self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
                    self.assertEqual(editor.document, original)
                    self.key(Qt.Key_Delete)
                    self.assertTrue(self.dialog_visible('adminRemoveGraphConfirmation'))
                    self.ui.click('adminConfirmRemoveGraph')
                    self.assertNotIn(identity, [node['identity'] for node in editor.nodes])
                    self.assertEqual(editor.edges, [])
                    self.assertTrue(editor.dirty)
                    request.assert_not_called()
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_delete_connection_keeps_its_nodes_in_both_editors(self):
        for mode in ('schema', 'workflow'):
            with self.subTest(mode=mode):
                editor, _graph = self.open_graph(mode)
                nodes = copy.deepcopy(editor.nodes)
                self.ui.click('graphEdge_0')
                self.key(Qt.Key_Delete)
                self.assertTrue(self.dialog_visible('adminRemoveGraphConfirmation'))
                self.ui.click('adminConfirmRemoveGraph')
                self.assertEqual(editor.nodes, nodes)
                self.assertEqual(editor.edges, [])
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_delete_edits_text_in_the_inspector_and_technical_xml_not_the_graph(self):
        for mode, identity, field in (('schema', 'demo/asset', 'adminSelectionAttributesEditor'),
                                      ('workflow', 'model', 'adminProcessDescription')):
            with self.subTest(mode=mode):
                editor, _graph = self.open_graph(mode)
                nodes, edges = copy.deepcopy(editor.nodes), copy.deepcopy(editor.edges)
                self.ui.click('graphNode_' + identity)
                # The JSON editor owns a nested TextArea; a normal field is
                # directly focusable. Click its actual input surface.
                item = self.ui.reveal(field)
                if mode == 'schema':
                    item = self.ui.item((field, 'adminNativeDocumentText'))
                else:
                    self.ui.enter(field, 'Description')
                self.ui.fixture.fixture.click(self.window, item)
                original_text = item.property('text')
                self.key(Qt.Key_Home, Qt.ControlModifier if mode == 'schema' else Qt.NoModifier)
                self.assertEqual(item.property('cursorPosition'), 0)
                self.key(Qt.Key_Delete)
                self.assertEqual(item.property('text'), original_text[1:])
                self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
                self.assertEqual(editor.nodes, nodes)
                self.assertEqual(editor.edges, edges)
                self.key(Qt.Key_S, Qt.ControlModifier)
                self.assertFalse(self.dialog_visible('adminSaveConfirmation'))
                self.ui.click('segmentedButtonSegment_technical')
                text = self.ui.item('adminNativeDocumentText')
                self.ui.fixture.fixture.click(self.window, text)
                original_text = text.property('text')
                self.key(Qt.Key_Home, Qt.ControlModifier)
                self.key(Qt.Key_Delete)
                self.assertEqual(text.property('text'), original_text[1:])
                self.key(Qt.Key_S, Qt.ControlModifier)
                self.assertFalse(self.dialog_visible('adminSaveConfirmation'))
                self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
                self.assertEqual(editor.nodes, nodes)
                self.assertEqual(editor.edges, edges)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_navigation_keys_and_repeated_arrow_moves_keep_focus_on_the_canvas(self):
        editor, graph = self.open_graph('schema')
        self.ui.click('graphNode_demo/asset')
        self.key(Qt.Key_Right)
        self.key(Qt.Key_Right)
        self.assertEqual(editor.nodes[0]['nodeX'], 40)
        original = copy.deepcopy(editor.document)
        self.key(Qt.Key_Plus)
        self.assertAlmostEqual(graph.property('zoom'), 1.1)
        self.key(Qt.Key_Minus)
        self.assertAlmostEqual(graph.property('zoom'), 1)
        self.key(Qt.Key_F)
        node = self.ui.item('graphNode_demo/asset')
        canvas = self.ui.item('adminGraphCanvas')
        position = node.mapToItem(canvas, QPointF(node.width() / 2, node.height() / 2))
        self.assertAlmostEqual(position.x(), canvas.width() / 2, delta=1)
        self.assertAlmostEqual(position.y(), canvas.height() / 2, delta=1)
        self.key(Qt.Key_Home)
        self.assertEqual(graph.property('zoom'), 1)
        self.assertAlmostEqual(canvas.property('contentX'), 0)
        self.assertAlmostEqual(canvas.property('contentY'), 0)
        self.assertEqual(editor.document, original)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_ctrl_s_uses_existing_save_confirmation_without_sending_until_confirmed(self):
        for mode, identity in (('schema', 'demo/asset'), ('workflow', 'model')):
            with self.subTest(mode=mode):
                editor, _graph = self.open_graph(mode)
                self.ui.click('graphNode_' + identity)
                with patch.object(editor, '_request') as request:
                    self.key(Qt.Key_S, Qt.ControlModifier)
                    self.assertFalse(self.dialog_visible('adminSaveConfirmation'))
                    self.key(Qt.Key_Right)
                    self.key(Qt.Key_S, Qt.ControlModifier)
                    self.assertTrue(self.dialog_visible('adminSaveConfirmation'))
                    request.assert_not_called()
                    self.ui.click('adminConfirmSave')
                    request.assert_called_once_with('save', editor.identity)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_delete_respects_readonly_empty_selection_and_pending_connection(self):
        editor, graph = self.open_graph('schema')
        self.ui.click('graphNode_demo/asset')
        original = copy.deepcopy(editor.document)
        self.ui.click('graphOutput_demo/asset')
        self.key(Qt.Key_Delete)
        self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
        self.assertEqual(graph.property('pendingConnection'), 'demo/asset')
        self.key(Qt.Key_Escape)
        self.assertEqual(graph.property('pendingConnection'), '')
        self.assertEqual(editor.selectedNode, 'demo/asset', 'Escape cancels the connection first')
        self.key(Qt.Key_Escape)
        self.assertEqual(editor.selectedNode, '')
        self.key(Qt.Key_Delete)
        self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
        editor._can_write = False
        editor.stateChanged.emit()
        self.ui.click('graphNode_demo/asset')
        self.key(Qt.Key_Delete)
        self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
        self.assertEqual(editor.document, original)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_tab_focused_node_is_the_delete_target_not_the_previous_selection(self):
        editor, graph = self.open_graph('schema')
        self.ui.click('graphNode_demo/asset')
        graph.forceActiveFocus(Qt.TabFocusReason)
        for _ in range(24):
            self.key(Qt.Key_Tab)
            if self.window.activeFocusItem().objectName() == 'graphNode_demo/shot':
                break
        self.assertEqual(self.window.activeFocusItem().objectName(), 'graphNode_demo/shot')
        self.key(Qt.Key_Delete)
        self.assertEqual(editor.selectedNode, 'demo/shot')
        self.assertTrue(self.dialog_visible('adminRemoveGraphConfirmation'))
        self.ui.click('adminConfirmRemoveGraph')
        self.assertEqual([node['identity'] for node in editor.nodes], ['demo/asset'])
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_reference_node_and_busy_document_cannot_be_removed_with_delete(self):
        editor, _graph = self.open_graph('workflow')
        editor.apply_xml('<pipeline><process name="model"/>'
                         '<connect from="model" to="texture"/></pipeline>')
        frame(self.window)
        original = copy.deepcopy(editor.document)
        self.ui.click('graphNode_texture')
        self.assertTrue(editor.selectedReference)
        self.key(Qt.Key_Delete)
        self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
        self.key(Qt.Key_Right)
        self.assertEqual(editor.document, original)
        self.ui.click('graphNode_model')
        editor._worker = QObject()
        try:
            editor.stateChanged.emit()
            self.key(Qt.Key_Delete)
            self.key(Qt.Key_S, Qt.ControlModifier)
            self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
            self.assertFalse(self.dialog_visible('adminSaveConfirmation'))
            self.assertEqual(editor.document, original)
        finally:
            editor._worker = None
            editor.stateChanged.emit()
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_delete_and_save_ignore_key_autorepeat(self):
        editor, _graph = self.open_graph('schema')
        self.ui.click('graphNode_demo/asset')
        self.key(Qt.Key_Right)
        original = copy.deepcopy(editor.document)
        for key, modifiers in ((Qt.Key_Delete, Qt.NoModifier), (Qt.Key_S, Qt.ControlModifier)):
            event = QKeyEvent(QEvent.KeyPress, key, modifiers, '', True)
            QCoreApplication.sendEvent(self.window, event)
            frame(self.window)
            self.assertFalse(self.dialog_visible('adminRemoveGraphConfirmation'))
            self.assertFalse(self.dialog_visible('adminSaveConfirmation'))
        self.assertEqual(editor.document, original)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_f_centers_the_actual_circular_progress_node(self):
        editor, _graph = self.open_graph('workflow')
        editor.select_node('model')
        editor.set_attribute('type', 'progress')
        frame(self.window)
        self.ui.click('graphNode_model')
        original = copy.deepcopy(editor.document)
        self.key(Qt.Key_F)
        node = self.ui.item('graphNode_model')
        canvas = self.ui.item('adminGraphCanvas')
        center = node.mapToItem(canvas, QPointF(node.width() / 2, node.height() / 2))
        self.assertEqual(node.width(), node.height())
        self.assertAlmostEqual(center.x(), canvas.width() / 2, delta=1)
        self.assertAlmostEqual(center.y(), canvas.height() / 2, delta=1)
        self.assertEqual(editor.document, original)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])

    def test_delete_dialog_is_reachable_and_bounded_in_narrow_and_wide_editors(self):
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            for mode, identity in (('schema', 'demo/asset'), ('workflow', 'model')):
                with self.subTest(mode=mode, width=width):
                    editor, _graph = self.open_graph(mode)
                    original = copy.deepcopy(editor.document)
                    self.ui.click('graphNode_' + identity)
                    self.key(Qt.Key_Delete)
                    self.assertTrue(self.dialog_visible('adminRemoveGraphConfirmation'))
                    self.ui.assert_inside('adminConfirmRemoveGraph')
                    self.ui.assert_inside('adminCancelRemoveGraph')
                    self.key(Qt.Key_Escape)
                    self.assertEqual(editor.document, original)
        self.assertEqual(self.ui.fixture.fixture.warnings, [])


if __name__ == '__main__':
    unittest.main()
