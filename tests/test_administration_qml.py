"""Actual native-window input and layout for the project administration editors."""

import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from xmlrpc.client import Fault

from PySide6.QtCore import QCoreApplication, QObject, QPointF, Qt, Signal
from PySide6.QtTest import QSignalSpy, QTest

import tests.test_editor_windows_qml as windows_fixture
from tests.profile_ui_responsiveness import frame
from tests.test_administration_documents import SCHEMA, WORKFLOW


class AdministrationQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        windows_fixture.EditorWindowQmlTests.setUpClass()

    def setUp(self):
        self.fixture = windows_fixture.EditorWindowQmlTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.admin = self.fixture.admin
        self.admin._project = 'demo'
        for editor in self.admin._editors.values():
            editor._project = 'demo'
            editor._loaded = editor._can_write = True
        self.seed(self.admin.schemaEditor, 'demo', {'xml': SCHEMA}, {
            'searchTypes': [{'identity': 'demo/asset', 'label': 'Assets'},
                            {'identity': 'demo/shot', 'label': 'Shots'}]})
        # General canvas tests have already loaded the endpoint catalog. The
        # connection suite exercises the real asynchronous request separately.
        self.admin.schemaEditor.connectionEditor._column_catalog = {
            'demo/asset': {'table': 'asset', 'database': 'demo', 'tableAvailable': True,
                           'columns': [{'name': 'code', 'type': 'varchar'}, {'name': 'shot_code', 'type': 'varchar'}]},
            'demo/shot': {'table': 'shot', 'database': 'demo', 'tableAvailable': True,
                          'columns': [{'name': 'code', 'type': 'varchar'}, {'name': 'id', 'type': 'integer'}]}}
        self.seed(self.admin.workflowEditor, 'demo/assets', {
            'xml': WORKFLOW, 'name': 'Assets', 'searchType': 'demo/asset',
            'processSettings': {}, 'processDescriptions': {}}, {
                'searchTypes': [{'identity': 'demo/asset', 'label': 'Assets'}],
                'nodeTypes': ['manual', 'action', 'condition', 'approval', 'hierarchy', 'dependency', 'progress', 'status'],
                'groups': [{'identity': 'artists', 'label': 'Artists'}, {'identity': 'leads', 'label': 'Team leads'}],
                'users': [{'identity': 'artist', 'label': 'An artist'}],
                'pipelines': [{'identity': 'demo/assets', 'label': 'Assets', 'searchType': 'demo/asset', 'color': '#6688aa'},
                              {'identity': 'demo/tasks', 'label': 'Task statuses', 'searchType': 'sthpw/task'},
                              {'identity': 'demo/sub', 'label': 'Subworkflow', 'searchType': 'demo/asset'}],
                'processes': [{'identity': 'PR2', 'label': 'review', 'pipeline': 'demo/sub'}],
                'canCreate': True})
        self.seed(self.admin.typesEditor, 'demo/asset', {
            'title': 'Assets', 'description': 'Project assets', 'columns': [], 'color': ''},
            {'columns': {'code': {'data_type': 'varchar'}}})
        self.admin.typesEditor._catalog[0].update(namespace='demo', projectLocal=True)
        from tests.security_matrix_fixture import seed_security
        seed_security(self.admin.securityEditor)
        self.admin.open()
        self.window = self.fixture.window('administration')
        frame(self.window)

    @staticmethod
    def seed(editor, identity, document, metadata):
        editor._identity = identity
        editor._catalog = [{'identity': identity, 'label': identity}]
        editor._document = copy.deepcopy(document)
        editor._original = copy.deepcopy(document)
        editor._metadata = metadata
        editor._document_loaded()
        editor.stateChanged.emit()

    def item(self, name):
        return next(item for item in windows_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())
                    if item.objectName() == name and item.isVisible())

    def click(self, name):
        self.fixture.click(self.window, self.item(name))

    def test_sections_create_real_views_without_warnings_at_narrow_and_wide_sizes(self):
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            for section in ('types', 'schema', 'workflow', 'rules', 'groups'):
                with self.subTest(section=section, width=width):
                    self.click('adminSection_' + section)
                    frame(self.window)
                    self.assertEqual(self.admin.section, section)
                    if section != 'groups':
                        button = self.item('adminSaveDocument')
                        point = button.mapToScene(QPointF())
                        self.assertGreaterEqual(point.x(), 0)
                        self.assertLessEqual(point.x() + button.width(), width)
                        self.assertLessEqual(point.y() + button.height(), height)
                    if section in ('schema', 'workflow'):
                        canvas = self.item('adminGraphCanvas')
                        self.assertGreaterEqual(canvas.width(), 180)
                        bar = self.item('adminGraphVerticalBar')
                        self.assertGreaterEqual(bar.mapToScene(QPointF()).x(),
                                                canvas.mapToScene(QPointF()).x() + canvas.width())
                    self.assertEqual(self.fixture.warnings, [])
                    output = os.environ.get('ADMIN_SCREENSHOTS')
                    if output:
                        Path(output).mkdir(parents=True, exist_ok=True)
                        self.window.grabWindow().save(str(Path(output) / (section + '_' + str(width) + '.png')))

    def test_document_actions_use_one_frameless_toolbar(self):
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            for section in ('types', 'schema', 'workflow', 'rules'):
                with self.subTest(section=section, width=width):
                    self.click('adminSection_' + section)
                    frame(self.window)
                    toolbar = self.item('adminDocumentToolbar')
                    self.assertLessEqual(toolbar.height(), 36)
                    names = {
                        item.objectName()
                        for item in windows_fixture.SidebarEditorQmlTests.descendants(
                            self.window.contentItem()
                        )
                        if item.isVisible()
                    }
                    self.assertNotIn('adminDocumentHeader', names)
                    self.assertNotIn('adminDocumentFooter', names)
                    self.assertGreater(
                        self.item('adminDocumentBody').height(),
                        height * 0.70,
                    )
                    self.assertEqual(self.fixture.warnings, [])

    def test_graph_ports_create_connection_and_canvas_scrolls_inside_its_gutters(self):
        self.admin.schemaEditor.apply_xml('<schema><search_type name="demo/asset" xpos="20" ypos="30"/><search_type name="demo/shot" xpos="350" ypos="30"/></schema>')
        self.window.resize(1400, 940)
        self.click('adminSection_schema')
        self.click('graphOutput_demo/asset')
        self.click('graphInput_demo/shot')
        self.assertEqual(len(self.admin.schemaEditor.edges), 1)
        self.assertEqual(self.admin.schemaEditor.edges[0]['from'], 'demo/asset')
        self.window.resize(900, 620)
        frame(self.window)
        bar = self.item('adminGraphVerticalBar')
        point = bar.mapToScene(QPointF(bar.width() / 2, bar.height() - 3))
        QTest.mouseClick(self.window, Qt.LeftButton, pos=point.toPoint())
        frame(self.window)
        self.assertGreater(self.item('adminGraphCanvas').property('contentY'), 0)

    def test_schema_uses_selected_project_without_a_document_picker(self):
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            for section in ('schema', 'workflow', 'schema'):
                with self.subTest(section=section, width=width):
                    self.click('adminSection_' + section)
                    frame(self.window)
                    selectors = [
                        item for item in windows_fixture.SidebarEditorQmlTests.descendants(
                            self.window.contentItem())
                        if item.objectName() == 'adminDocumentSelector' and item.isVisible()
                    ]
                    self.assertEqual(selectors, [])
                    if section == 'workflow':
                        self.assertTrue(self.item('adminWorkflowList').isVisible())
                    self.assertTrue(self.item('administrationProjectSelector').isVisible())
                    self.assertEqual(self.admin.project, 'demo')
                    self.assertEqual(self.admin.schemaEditor.identity, 'demo')
                    self.assertGreater(self.item('adminGraphCanvas').height(), 120)
                    self.assertEqual(self.fixture.warnings, [])

    def test_sidebar_entry_selects_groups_even_after_another_admin_section(self):
        self.click('adminSection_types')
        self.fixture.sidebar.open_group_manager()
        self.assertEqual(self.admin.section, 'groups')

    def test_project_selector_includes_hidden_projects_without_changing_workspace_filters(self):
        from thlib.tactic_classes import Project

        model = self.fixture.application.project_model
        projects = [Project({'code': code, 'name': title, 'is_template': template,
                             's_status': status, '__builtin__': builtin})
                    for code, title, template, status, builtin in (
                        ('demo', 'Demo', False, '', False),
                        ('archived', 'Archived project', False, 'retired', False),
                        ('template', 'Template project', True, '', False),
                        ('admin', 'Administration', False, '', True),
                        ('sthpw', 'TACTIC', False, '', True))]
        model.replace(projects)
        frame(self.window)
        selector = self.item('administrationProjectSelector')
        self.assertEqual(selector.property('count'), 5)
        self.assertEqual(selector.property('currentValue'), 'demo')
        self.assertEqual(model.rowCount(), 1)
        self.assertFalse(model.showBuiltins)
        self.assertFalse(model.showTemplates)
        self.assertFalse(model.showRetired)

        # Pick the hidden builtin with the same keyboard path as the user.
        selector.forceActiveFocus()
        for _ in range(4):
            QTest.keyClick(self.window, Qt.Key_Down)
        QTest.keyClick(self.window, Qt.Key_Return)
        frame(self.window)
        self.assertEqual(self.admin.project, 'sthpw')
        self.assertEqual(selector.property('currentValue'), 'sthpw')
        self.assertEqual(model.rowCount(), 1)

        # A catalog refresh preserves the selection even when indexes change.
        model.replace(list(reversed(projects)))
        frame(self.window)
        self.assertEqual(selector.property('currentValue'), 'sthpw')
        self.assertEqual(selector.property('currentIndex'), 0)
        self.assertFalse(selector.property('translateDisplayText'))

    def test_permission_failure_opens_an_operable_child_error_and_keeps_the_editor_usable(self):
        from thlib.environment import env_inst, env_mode
        from thlib.ui.debug_logging import DebugLogController

        log = DebugLogController(Path(env_mode.current_path))
        self.addCleanup(log.shutdown)
        self.fixture.application.debug_log = log
        context = self.fixture.engine.rootContext()
        for name, value in {'debugLog': log, 'debugLogModel': log.entries_model,
                            'debugGroupModel': log.groups_model}.items():
            context.setContextProperty(name, value)
        model = self.fixture.application.window_model

        def sync_error():
            # Main.qml uses this same show/close route.
            if log.error_visible:
                model.show_window('error')
            else:
                model.close_window('error')

        log.error_changed.connect(sync_error)
        log.show_requested.connect(lambda: model.show_window('debug_log'))
        self.addCleanup(log.error_changed.disconnect, sync_error)
        self.addCleanup(model.close_window, 'debug_log')
        self.addCleanup(model.close_window, 'error')
        failure = Fault(1, 'TACTIC administrator access is required')
        trace = 'Traceback (most recent call last):\nxmlrpc.client.Fault: ' + str(failure)

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)

            def start(self):
                self.error.emit(({'exception': failure, 'stacktrace': trace}, self))

            def cancel(self):
                pass

        worker = Worker()
        self.click('adminSection_types')
        with patch.object(env_inst.server_pool, 'add_task', return_value=worker):
            self.admin.typesEditor.reload()
            QCoreApplication.processEvents()
        error_window = self.fixture.window('error')
        frame(error_window)
        self.assertIs(error_window.transientParent(), self.window)
        self.assertFalse(self.admin.typesEditor.busy)
        self.assertEqual(log.error_type, 'permission_error')
        self.assertEqual(log.error_stacktrace, trace)
        clipboard = self.fixture.app.clipboard()
        self.addCleanup(clipboard.setText, clipboard.text())
        copy_button = self.fixture.item(error_window, 'copyErrorStacktrace')
        self.fixture.click(error_window, copy_button)
        self.assertEqual(self.fixture.app.clipboard().text(), trace)
        dismiss = self.fixture.item(error_window, 'dismissError')
        point = dismiss.mapToScene(QPointF(dismiss.width() / 2, dismiss.height() / 2))
        QTest.mouseClick(error_window, Qt.LeftButton, pos=point.toPoint())
        self.assertFalse(log.error_visible)

        frame(self.window)
        self.click('adminSection_schema')
        self.assertEqual(self.admin.section, 'schema')

        # A second denial also remains dismissible with keyboard input.
        log.raise_error(Fault(1, 'Only a TACTIC administrator can change access rules'))
        error_window = self.fixture.window('error')
        frame(error_window)
        dismiss = self.fixture.item(error_window, 'dismissError')
        dismiss.forceActiveFocus()
        QTest.keyClick(error_window, Qt.Key_Space)
        frame(self.window)
        self.assertFalse(log.error_visible)
        log.raise_error(PermissionError('Permission denied'), stacktrace=trace)
        error_window = self.fixture.window('error')
        frame(error_window)
        button = self.fixture.item(error_window, 'openErrorDebugLog')
        point = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
        QTest.mouseClick(error_window, Qt.LeftButton, pos=point.toPoint())
        debug_window = self.fixture.window('debug_log')
        frame(debug_window)
        self.assertIs(debug_window.transientParent(), self.window)
        self.assertFalse(log.error_visible)

    def test_missing_project_database_unlocks_project_selection(self):
        from thlib.environment import env_inst

        failure = Fault(1, 'This database [complex] does not exist')

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)

            def start(self):
                self.error.emit(({
                    'exception': failure,
                    'stacktrace': 'xmlrpc.client.Fault: ' + str(failure),
                }, self))

            def cancel(self):
                pass

        editor = self.admin.workflowEditor
        self.admin._section = 'workflow'
        self.admin._project = 'complex'
        editor.reset('complex')
        self.admin.stateChanged.emit()
        with (patch.object(self.fixture.application, 'debug_log') as debug_log,
              patch.object(env_inst.server_pool, 'add_task', return_value=Worker())):
            editor.reload()
            QCoreApplication.processEvents()
        frame(self.window)

        self.assertTrue(editor.projectUnavailable)
        self.assertFalse(editor.busy)
        self.assertFalse(self.admin.projectLocked)
        self.assertTrue(self.item('administrationProjectSelector').isEnabled())
        self.assertEqual(editor.error, editor.tr(
            'Project "%s" is unavailable because its database no longer exists. '
            'Choose another project.') % 'complex')
        debug_log.raise_error.assert_called_once()
        self.assertIs(debug_log.raise_error.call_args.args[0], failure)
        self.assertIn(str(failure), debug_log.raise_error.call_args.kwargs['stacktrace'])

        editor._document = {'xml': '<pipeline/>'}
        editor.stateChanged.emit()
        frame(self.window)
        self.assertTrue(self.admin.projectLocked)
        self.assertFalse(self.item('administrationProjectSelector').isEnabled())
        editor.discard()
        frame(self.window)
        self.assertTrue(editor.projectUnavailable)
        self.assertFalse(self.admin.projectLocked)

        with patch.object(self.admin, 'select_section'):
            self.admin.select_project('demo')
        self.assertEqual(self.admin.project, 'demo')
        self.assertFalse(editor.projectUnavailable)

    def test_server_timeout_shows_localized_guidance_and_keeps_raw_diagnostics(self):
        from pathlib import Path
        from urllib.error import URLError

        from thlib.environment import env_mode
        from thlib.ui.debug_logging import DebugLogController

        log = DebugLogController(Path(env_mode.current_path))
        log.set_recording_levels(["EXCEPTION"])
        self.addCleanup(log.shutdown)
        previous_log = self.fixture.application.debug_log
        self.fixture.application.debug_log = log
        self.addCleanup(
            setattr, self.fixture.application, "debug_log", previous_log
        )
        context = self.fixture.engine.rootContext()
        for name, value in {
            "debugLog": log,
            "debugLogModel": log.entries_model,
            "debugGroupModel": log.groups_model,
        }.items():
            context.setContextProperty(name, value)
        model = self.fixture.application.window_model

        def sync_error():
            if log.error_visible:
                model.show_window("error")
            else:
                model.close_window("error")

        log.error_changed.connect(sync_error)
        self.addCleanup(log.error_changed.disconnect, sync_error)
        self.addCleanup(model.close_window, "error")

        class FakeServer:
            project_code = "sthpw"

        failure = URLError(TimeoutError("Удалённый компьютер не ответил"))

        def unavailable(_server):
            raise failure

        wrapped = log._server_wrapper("execute_python_script", unavailable)
        with self.assertRaises(URLError):
            wrapped(FakeServer())
        error_window = self.fixture.window("error")
        frame(error_window)

        source = (
            "The TACTIC server is unreachable or did not respond in time. "
            "Check the server address, network connection, VPN or proxy, "
            "and make sure the server is running. Then try again."
        )
        translated = self.fixture.translator.translate(
            "DebugLogController", source
        )
        self.assertNotEqual(translated, source)
        self.assertEqual(
            self.fixture.item(error_window, "errorMessage").property("text"),
            translated,
        )
        for width, height in ((560, 400), (900, 620)):
            error_window.resize(width, height)
            frame(error_window)
            message = self.fixture.item(error_window, "errorMessage")
            origin = message.mapToScene(QPointF())
            self.assertGreaterEqual(origin.x(), 0)
            self.assertGreaterEqual(origin.y(), 0)
            self.assertLessEqual(origin.x() + message.width(), width)
            self.assertLessEqual(origin.y() + message.height(), height)
        self.assertEqual(log.error_type, "connection_timeout")
        self.assertIn("urllib.error.URLError", log.error_stacktrace)
        self.assertIn("Удалённый компьютер не ответил", log.error_stacktrace)
        self.assertEqual(log._live_entries[-1]["message"], str(failure))
        self.assertEqual(self.fixture.warnings, [])

        dismiss = self.fixture.item(error_window, "dismissError")
        point = dismiss.mapToScene(
            QPointF(dismiss.width() / 2, dismiss.height() / 2)
        )
        QTest.mouseClick(error_window, Qt.LeftButton, pos=point.toPoint())
        frame(self.window)
        self.assertFalse(log.error_visible)

    def test_non_admin_cannot_see_sidebar_group_management_or_open_admin(self):
        self.fixture.admin_access.return_value = False
        self.fixture.application.server_state_changed.emit()
        self.assertFalse(self.fixture.application.window_model.is_window_visible('administration'))
        self.fixture.application.window_model.show_window('sidebar_editor')
        sidebar_window = self.fixture.window('sidebar_editor')
        frame(sidebar_window)
        self.fixture.click(sidebar_window, self.fixture.item(
            sidebar_window, 'segmentedButtonSegment_access'))
        button = self.fixture.item(sidebar_window, 'manageSidebarGroups')
        self.assertFalse(button.isVisible())
        self.fixture.sidebar.open_group_manager()
        self.assertFalse(self.fixture.application.window_model.is_window_visible('administration'))

    def test_touch_selects_node_once_without_moving_it(self):
        self.window.resize(1400, 940)
        self.click('adminSection_schema')
        node = self.item('graphNode_demo/asset')
        point = node.mapToScene(QPointF(node.width() / 2, node.height() / 2)).toPoint()
        device = QTest.createTouchDevice()
        sequence = QTest.touchEvent(self.window, device, autoCommit=False)
        sequence.press(0, point, self.window).commit()
        frame(self.window)
        sequence.release(0, point, self.window).commit()
        frame(self.window)
        self.assertEqual(self.admin.schemaEditor.selectedNode, 'demo/asset')
        self.assertFalse(self.admin.schemaEditor.dirty)

    def test_save_requires_confirmation_and_applies_worker_result(self):
        from thlib.environment import env_inst

        editor = self.admin.typesEditor
        self.click('adminSection_types')
        editor.set_field('title', 'Updated')
        calls = []

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)

            def start(self):
                calls.append('save')
                self.result.emit(dict(identity='demo/asset', revision='saved', canWrite=True,
                                      document=copy.deepcopy(editor.document), metadata=editor.metadata))

            def cancel(self):
                pass

        worker = Worker()
        self.click('adminSaveDocument')
        self.assertEqual(calls, [])
        # Focus starts on Cancel; Tab reaches the shared Save button.
        dialog = self.window.findChild(QObject, 'adminSaveConfirmation')
        self.assertIsNotNone(dialog)
        self.assertTrue(dialog.property('visible'))
        with patch.object(env_inst, 'server_pool', type('Pool', (), {
                'is_stopped': False, 'add_task': lambda *_: worker})()), \
                patch.object(self.admin, '_refresh_pending_metadata'):
            QTest.keyClick(self.window, Qt.Key_Tab)
            QTest.keyClick(self.window, Qt.Key_Space)
            frame(self.window)
            QCoreApplication.processEvents()
        self.assertEqual(calls, ['save'])
        self.assertFalse(editor.dirty)
        self.assertEqual(editor._revision, 'saved')

    def test_schema_select_keyboard_and_mouse_drag_keep_native_xml_positions(self):
        self.window.resize(1400, 940)
        self.click('adminSection_schema')
        node = self.item('graphNode_demo/asset')
        self.fixture.click(self.window, node)
        self.assertEqual(self.admin.schemaEditor.selectedNode, 'demo/asset')
        QTest.keyClick(self.window, Qt.Key_Right)
        frame(self.window)
        self.assertEqual(self.admin.schemaEditor.nodes[0]['nodeX'], 30)
        node = self.item('graphNode_demo/asset')
        start = node.mapToScene(QPointF(node.width() / 2, node.height() / 2)).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        QTest.mouseMove(self.window, start + QPointF(30, 15).toPoint())
        QTest.mouseMove(self.window, start + QPointF(70, 30).toPoint())
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=start + QPointF(70, 30).toPoint())
        frame(self.window)
        self.assertGreater(self.admin.schemaEditor.nodes[0]['nodeX'], 30)
        self.assertIn('custom="edge"', self.admin.schemaEditor.document['xml'])

    def test_graph_connections_follow_drag_before_committing_node_position(self):
        self.window.resize(1400, 940)
        self.click('adminSection_schema')
        editor = self.admin.schemaEditor
        node = self.item('graphNode_demo/asset')
        connector = next(
            item for item in windows_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem())
            if item.property('startX') is not None
            and item.property('endX') is not None
            and item.property('source') is not None)
        original_x = editor.nodes[0]['nodeX']
        graph_changes = QSignalSpy(editor.graphChanged)
        start = node.mapToScene(QPointF(node.width() / 2, node.height() / 2)).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        QTest.mouseMove(self.window, start + QPointF(35, 15).toPoint())
        QTest.mouseMove(self.window, start + QPointF(85, 35).toPoint())
        frame(self.window)
        try:
            self.assertGreater(node.x(), original_x)
            self.assertEqual(editor.nodes[0]['nodeX'], original_x)
            self.assertEqual(graph_changes.count(), 0)
            self.assertAlmostEqual(connector.property('startX'), node.x() + node.width())
            self.assertAlmostEqual(connector.property('startY'), node.y() + node.height() / 2)
        finally:
            QTest.mouseRelease(self.window, Qt.LeftButton,
                               pos=start + QPointF(85, 35).toPoint())
        frame(self.window)
        self.assertEqual(graph_changes.count(), 1)
        self.assertGreater(editor.nodes[0]['nodeX'], original_x)
        self.assertEqual(self.fixture.warnings, [])

    def test_security_add_rule_and_discard_use_real_buttons(self):
        self.click('adminSection_rules')
        self.click('adminSecurityTab_search_filter')
        count = len(self.admin.securityEditor.rules)
        self.click('adminAddAccessRule')
        self.assertEqual(len(self.admin.securityEditor.rules), count + 1)
        self.assertTrue(self.admin.securityEditor.dirty)
        self.click('adminDiscardDocument')
        self.assertEqual(len(self.admin.securityEditor.rules), count)
        self.assertFalse(self.admin.securityEditor.dirty)

    def test_committed_rules_publish_without_discarding_a_group_draft(self):
        self.admin.set_field('description', 'Unsaved membership work')
        self.assertTrue(self.admin.dirty)
        self.admin.securityEditor._document['groups']['G0']['xml'] = '<rules><rule group="project" code="demo" access="view"/></rules>'
        with patch.object(self.admin, '_publish_catalog') as publish:
            self.admin.securityEditor.committed.emit()
        publish.assert_called_once_with()
        self.assertTrue(self.admin.dirty)
        self.assertEqual(self.admin.draft['description'], 'Unsaved membership work')
        self.assertIn('access="view"', self.admin._catalog['groups'][0]['access_rules'])

    def test_entity_metadata_edit_retains_draft_between_sections(self):
        self.click('adminSection_types')
        self.click('segmentedButtonSegment_entity_details')
        self.click('adminSearchTypeTitle')
        QTest.keyClick(self.window, Qt.Key_A, Qt.ControlModifier)
        for char in 'New title':
            QTest.keyClick(self.window, char)
        frame(self.window)
        self.assertEqual(self.admin.typesEditor.document['title'], 'New title')
        self.admin.typesEditor.set_field('color', '#336699')
        frame(self.window)
        self.assertEqual(self.admin.typesEditor.document['color'], '#336699')
        self.click('adminSection_schema')
        self.click('adminSection_types')
        self.assertEqual(self.item('adminSearchTypeTitle').property('text'), 'New title')
        self.assertTrue(self.admin.projectLocked)

    def test_search_type_form_offers_only_native_fields_for_existing_and_new_types(self):
        self.click('adminSection_types')
        checkboxes = [item for item in windows_fixture.SidebarEditorQmlTests.descendants(
            self.item('adminSearchTypeForm')) if item.inherits('QQuickCheckBox') and item.isVisible()]
        self.assertEqual(checkboxes, [])

        self.click('adminCreateDocument')
        self.assertEqual(set(self.admin.typesEditor.document), {
            'title', 'description', 'color', 'hasPipeline', 'columns'})
        self.assertFalse(any(
            item.objectName() == 'adminSearchTypeName' and item.isVisible()
            for item in windows_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem())))
        checkboxes = [item for item in windows_fixture.SidebarEditorQmlTests.descendants(
            self.item('adminSearchTypeForm')) if item.inherits('QQuickCheckBox') and item.isVisible()]
        self.assertEqual(len(checkboxes), 1)
        self.assertTrue(checkboxes[0].property('checked'))
        self.fixture.click(self.window, checkboxes[0])
        self.assertFalse(self.admin.typesEditor.document['hasPipeline'])
        self.assertEqual(self.fixture.warnings, [])

    def test_search_type_table_filters_native_titles_and_opens_separate_editor(self):
        editor = self.admin.typesEditor
        editor._catalog = [
            {'identity': 'demo/asset', 'label': 'Asset library', 'table': 'asset',
             'namespace': 'demo', 'color': '#d15c73', 'projectLocal': True},
            {'identity': 'demo/shot', 'label': 'Shot library', 'table': 'shot',
             'namespace': 'demo', 'color': '#568acc', 'projectLocal': True},
        ]
        editor.stateChanged.emit()
        self.click('adminSection_types')
        self.window.resize(1400, 940)
        self.click('segmentedButtonSegment_entity_details')
        frame(self.window)
        catalog = self.item('adminSearchTypesList')
        self.assertEqual(catalog.property('count'), 2)
        with patch.object(editor, '_request') as request:
            self.click('adminSearchType_demo/shot')
        request.assert_called_once_with('load', 'demo/shot')
        self.assertEqual(self.item('adminSearchTypeTitle').property('text'), 'Assets')

        self.click('adminSearchTypeFilter')
        for char in 'Shot library':
            QTest.keyClick(self.window, char)
        frame(self.window)
        self.assertEqual(catalog.property('count'), 1)
        row = self.item('adminSearchType_demo/shot')
        row.forceActiveFocus()
        with patch.object(editor, '_request') as request:
            QTest.keyClick(self.window, Qt.Key_Return)
            frame(self.window)
        request.assert_called_once_with('load', 'demo/shot')
        editor.set_field('description', 'Unsaved detail')
        self.assertFalse(row.isEnabled())
        self.assertEqual(self.fixture.warnings, [])

    def test_create_search_type_from_fields_opens_title_at_top(self):
        self.window.resize(900, 620)
        self.click('adminSection_types')
        self.click('segmentedButtonSegment_entity_fields')
        viewport = self.item('adminSearchTypeForm')
        viewport.setProperty('contentY', 40)
        self.click('adminCreateDocument')
        identifier = self.item('adminSearchTypeTitle')
        self.assertEqual(viewport.property('contentY'), 0)
        point = identifier.mapToScene(QPointF())
        self.assertGreaterEqual(point.y(), viewport.mapToScene(QPointF()).y())
        self.assertLessEqual(point.y() + identifier.height(),
                             viewport.mapToScene(QPointF()).y() + viewport.height())
        self.click('adminSearchTypeTitle')
        for char in 'New Asset':
            QTest.keyClick(self.window, char)
        frame(self.window)
        self.assertEqual(self.admin.typesEditor.document['title'], 'New Asset')
        self.assertEqual(self.fixture.warnings, [])

    def test_round_ports_keep_native_colors_and_remain_reachable_at_canvas_origin(self):
        editor = self.admin.schemaEditor
        editor._metadata['searchTypes'][0]['color'] = '#c95075'
        editor.apply_xml('<schema><search_type name="demo/asset" xpos="0" ypos="0"/>'
                         '<search_type name="demo/shot" xpos="350" ypos="0"/></schema>')
        self.window.resize(1400, 940)
        self.click('adminSection_schema')
        canvas = self.item('adminGraphCanvas')
        port = self.item('graphInput_demo/asset')
        self.assertGreaterEqual(port.mapToScene(QPointF()).x(), canvas.mapToScene(QPointF()).x())
        self.assertEqual(port.property('accent').name(), '#c95075')
        ring = next(item for item in windows_fixture.SidebarEditorQmlTests.descendants(port)
                    if item.objectName() == 'graphPortRing')
        self.assertEqual(ring.width(), ring.height())
        self.assertEqual(ring.property('radius'), ring.width() / 2)

        output = self.item('graphOutput_demo/asset')
        output.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Return)
        frame(self.window)
        target = self.item('graphInput_demo/shot')
        self.assertTrue(target.isEnabled())
        target.forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Space)
        frame(self.window)
        self.assertEqual(len(editor.edges), 1)
        self.assertEqual(self.item('graphConnection_0').property('accent').name(), '#c95075')
        self.assertGreater(self.item('graphDirectionArrow').width(), 0)
        self.item('graphOutput_demo/asset').forceActiveFocus()
        QTest.keyClick(self.window, Qt.Key_Return)
        QTest.keyClick(self.window, Qt.Key_Escape)
        frame(self.window)
        self.assertFalse(self.item('graphInput_demo/shot').property('activePort'))
        self.assertEqual(self.item('adminGraphCanvas').parentItem().property('pendingConnection'), '')
        self.assertEqual(self.fixture.warnings, [])


if __name__ == '__main__':
    unittest.main()
