"""Actual modal rule editor input, layouts, paging and saved-node context."""

import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QPointF, Qt
from PySide6.QtTest import QTest

from tests import test_administration_qml as fixture_module
from tests import test_sidebar_editor_qml as sidebar_fixture
from tests.profile_ui_responsiveness import frame


class ProcessRulesQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_module.AdministrationQmlTests.setUpClass()

    def setUp(self):
        self.fixture = fixture_module.AdministrationQmlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.editor = self.fixture.admin.workflowEditor.rulesEditor
        self.editor._project = 'demo'
        self.editor._can_write = self.editor._loaded = True
        fixture_module.AdministrationQmlTests.seed(self.editor, 'PR1', {'rules': []}, {
            'process': 'model', 'pipeline': 'demo/assets', 'searchType': 'demo/asset',
            'sourceStatuses': ['Work', 'Done'], 'processes': [
                {'identity': 'model', 'label': 'model', 'statuses': ['Work', 'Done']},
                {'identity': 'review', 'label': 'review', 'statuses': ['Review', 'Approved']}],
            'outputs': ['review'], 'scriptPaths': ['workflow/example'], 'naming': [],
            'items': [{'key': 'demo/asset?code=A1', 'label': 'Asset one'}], 'itemCount': 121, 'itemOffset': 0})
        self.fixture.fixture.application.window_model.show_child_window('process_dependencies', 'administration')
        self.window = self.fixture.fixture.window('process_dependencies')
        self.window.resize(1100, 800)
        frame(self.window)

    def item(self, name):
        return next(item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())
                    if item.objectName() == name and item.isVisible())

    def reveal(self, name):
        item = self.item(name)
        parent = item.parentItem()
        while parent:
            if parent.inherits('QQuickFlickable'):
                y = item.mapToItem(parent, QPointF()).y()
                if y < 0 or y + item.height() > parent.height():
                    parent.setProperty('contentY', max(0, min(parent.property('contentHeight') - parent.height(),
                        parent.property('contentY') + y - 8)))
                    frame(self.window)
            parent = parent.parentItem()
        return item

    def click(self, name):
        self.fixture.fixture.click(self.window, self.reveal(name))

    def enter(self, name, text):
        self.click(name)
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for character in text:
            QTest.keyClick(self.window, character)
        frame(self.window)

    def choose(self, name, value):
        combo = self.reveal(name)
        model = combo.property('model')
        if hasattr(model, 'toVariant'):
            model = model.toVariant()
        index = next(index for index, row in enumerate(model) if (row.get('identity') if isinstance(row, dict) else row) == value)
        combo.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Home)
        for _ in range(index):
            QTest.keyClick(self.window, Qt.Key_Down)
        frame(self.window)

    def test_modal_opens_and_process_rule_uses_native_task_status_choices(self):
        self.assertEqual(self.window.modality(), Qt.WindowModal)
        self.click('adminAddProcessRule')
        self.enter('adminRule_title', 'Render complete')
        self.choose('adminRuleSourceStatus', 'Done')
        self.click('adminRuleTarget_review')
        self.choose('adminRuleTargetStatus_review', 'Approved')
        self.assertEqual(self.editor.selectedRule['title'], 'Render complete')
        self.assertEqual(self.editor.selectedRule['srcStatus'], 'Done')
        self.assertEqual(self.editor.selectedRule['targets'], [{'process': 'review', 'status': 'Approved'}])
        self.click('segmentedButtonSegment_global')
        self.assertEqual(self.editor.selectedRule['scope'], 'global')
        with patch.object(self.editor, '_request') as save:
            self.click('adminSaveDocument')
            self.assertFalse(save.called)
            self.click('adminConfirmSave')
            save.assert_called_once_with('save', 'PR1')
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_notifications_have_body_recipients_template_and_ticket_settings(self):
        self.click('segmentedButtonSegment_notifications')
        self.click('adminAddProcessRule')
        self.enter('adminRule_title', 'Notify reviewer')
        self.enter('adminRule_subject', 'Review ready')
        self.enter('adminRule_mailTo', '{$LOGIN}')
        self.enter('adminRule_body', 'Ready for review')
        self.click('adminRuleTicket')
        self.assertEqual(self.editor.selectedRule['kind'], 'notification')
        self.assertEqual(self.editor.selectedRule['body'], 'Ready for review')
        self.assertEqual(self.editor.selectedRule['mailTo'], '{$LOGIN}')
        self.assertTrue(self.editor.selectedRule['loginTicket'])
        self.editor.request_close()
        self.assertTrue(self.window.isVisible())
        self.assertTrue(self.editor.error)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_switching_rule_tabs_selects_matching_rule_without_losing_drafts(self):
        self.item('adminAddProcessRule').setProperty('duplicateWindow', 0)
        self.click('adminAddProcessRule')
        self.enter('adminRule_title', 'Trigger draft')
        self.click('segmentedButtonSegment_notifications')
        self.assertEqual(self.editor.selectedRule, {})
        self.click('adminAddProcessRule')
        self.enter('adminRule_title', 'Notification draft')
        self.click('segmentedButtonSegment_triggers')
        self.assertEqual(self.editor.selectedRule['title'], 'Trigger draft')
        self.click('segmentedButtonSegment_notifications')
        self.assertEqual(self.editor.selectedRule['title'], 'Notification draft')
        self.assertEqual(len(self.editor.document['rules']), 2)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_all_action_forms_and_narrow_layout_have_no_warnings(self):
        self.click('adminAddProcessRule')
        for width, height in ((860, 600), (1400, 940)):
            self.window.resize(width, height)
            for action, name in [('task_create', 'adminRuleOutput_review'), ('task_date', 'adminRuleDate'),
                                 ('python_class', 'adminRule_classPath'), ('custom_script', 'adminRuleScript'),
                                 ('parent_status', 'adminRule_targetStatus'), ('task_status', 'adminRuleTarget_review')]:
                self.choose('adminRuleAction', action)
                item = self.reveal(name)
                origin = item.mapToScene(QPointF())
                self.assertGreaterEqual(origin.x(), 0, name)
                self.assertLessEqual(origin.x() + item.width(), self.window.width(), name)
                self.assertGreater(item.width(), 70, name)
            output = os.environ.get('ADMIN_RULE_SCREENSHOTS')
            if output:
                directory = Path(output)
                directory.mkdir(parents=True, exist_ok=True)
                self.window.grabWindow().save(str(directory / ('rules_' + str(width) + '.png')))
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_paging_preserves_rule_draft_and_does_not_request_while_dirty(self):
        self.click('segmentedButtonSegment_objects')
        with patch.object(self.editor, '_request') as request:
            self.click('adminObjectsNext')
            request.assert_called_once_with('load', 'PR1', item_offset=50)
            self.editor.add_rule('trigger')
            before = copy.deepcopy(self.editor.document)
            request.reset_mock()
            self.editor.show_item_page(100)
            self.assertFalse(request.called)
            self.assertEqual(self.editor.document, before)
        self.assertEqual(self.fixture.fixture.warnings, [])

    def test_rule_removal_is_confirmed_and_staged_until_save(self):
        self.click('adminAddProcessRule')
        self.enter('adminRule_title', 'Remove me')
        self.editor._original = copy.deepcopy(self.editor.document)
        self.editor.stateChanged.emit()
        with patch.object(self.editor, '_request') as request:
            self.click('adminRemoveProcessRule')
            self.assertEqual(len(self.editor.document['rules']), 1)
            ok_text = QCoreApplication.translate('QQuickDialogButtonBox', 'OK')
            button = next(item for item in sidebar_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())
                          if item.isVisible() and item.inherits('QQuickAbstractButton') and item.property('text') == ok_text)
            self.fixture.fixture.click(self.window, button)
            self.assertEqual(self.editor.document['rules'], [])
            self.assertTrue(self.editor.dirty)
            request.assert_not_called()
            self.editor.discard()
            self.assertEqual(self.editor.selectedRule['title'], 'Remove me')
        self.assertEqual(self.fixture.fixture.warnings, [])
