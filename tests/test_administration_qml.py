"""Actual native-window input and layout for the project administration editors."""

import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from xmlrpc.client import Fault

from PySide6.QtCore import QCoreApplication, QObject, QPoint, QPointF, Qt, Signal
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
        self.fixture.columns._definition_catalog_loaded = True
        self.fixture.columns._definition_catalog_project = 'demo'
        for editor in self.admin._editors.values():
            editor._project = 'demo'
            editor._loaded = editor._can_write = True
        self.admin.usersEditor._project = 'sthpw'
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
        name={'adminGraphVerticalBar':'adminGraphCanvasVerticalBar','adminGraphHorizontalBar':'adminGraphCanvasHorizontalBar','adminWorkflowList':'adminWorkflowCatalog','adminWorkflowListPanel':'adminWorkflowCatalogPanel','adminSelectionAttributesEditor':'graph_attributesEditor','sidebarSaveButton':'adminSaveDocument'}.get(name,name)
        return next(item for item in windows_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())
                    if item.objectName() == name and item.isVisible())

    def choose_page(self, prefix, value):
        try:self.click(prefix+'_'+value)
        except StopIteration:
            picker=self.item(prefix);rows=picker.property('model')
            rows=rows.toVariant() if hasattr(rows,'toVariant') else rows
            index=next(index for index,row in enumerate(rows) if row['value']==value)
            self.fixture.choose_combo_option(self.window,picker,index)

    def click(self, name):
        self.window.requestActivate()
        frame(self.window)
        if name.startswith('segmentedButtonSegment_entity_'):
            self.choose_page('searchTypePages',name[len('segmentedButtonSegment_entity_'):]);return
        if name.startswith('adminSection_'):
            pickers = [item for item in windows_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())
                       if item.objectName() == 'administrationSectionSelector' and item.isVisible()]
            if pickers:
                picker = pickers[0]
                rows = picker.property('model')
                rows = rows.toVariant() if hasattr(rows, 'toVariant') else rows
                target = next(index for index, row in enumerate(rows) if row['value'] == name[13:])
                self.fixture.choose_combo_option(self.window, picker, target)
                return
        item = self.item(name)
        if name.startswith('adminSection_') and any(item.objectName() == 'administrationNavigation' and item.isVisible()
                for item in windows_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())):
            navigation = self.item('administrationNavigation')
            top = item.mapToItem(navigation, QPointF()).y()
            if top < 0 or top + item.height() > navigation.height():
                offset = navigation.property('contentY') + top - (navigation.height() - item.height()) / 2
                navigation.setProperty('contentY', max(0, min(offset,
                    navigation.property('contentHeight') - navigation.height())))
                frame(self.window)
        self.fixture.click(self.window, item)

    def test_project_choice_keeps_a_server_value_missing_from_the_catalog(self):
        self.admin._project = 'external_only'
        self.admin.stateChanged.emit()
        frame(self.window)
        selector = self.item('administrationProjectSelector')
        self.assertEqual(selector.property('currentIndex'), -1)
        self.assertEqual(selector.property('displayText'), 'external_only')
        self.assertEqual(self.admin.project, 'external_only')
        self.assertEqual(self.fixture.warnings, [])

    def test_configuration_style_shell_keeps_aligned_headers_and_navigation(self):
        self.window.resize(1400,940);frame(self.window)
        self.click('adminSection_types')
        header=self.item('administrationHeader');content=self.item('administrationContent')
        self.assertEqual(header.x(),0)
        self.assertEqual(header.height(),77)
        self.assertGreater(header.width(),content.width()+200)
        self.assertGreaterEqual(content.mapToScene(QPointF()).y(),header.mapToScene(QPointF(0,header.height())).y()+12)
        self.assertGreater(header.width(),300)
        self.assertTrue(self.item('administrationProjectSelector').isEnabled())
        self.assertEqual(self.fixture.warnings,[])

    def test_header_actions_center_on_full_header_height(self):
        for section in ('types','schema','workflow','groups'):
         self.click('adminSection_'+section)
         toolbar=self.item('administrationHeaderSaveBar')
         help=self.item('administrationHelpButton')
         self.assertEqual(toolbar.height(),38)
         header=self.item('administrationHeader')
         for item in (toolbar,help):
          point=item.mapToScene(QPointF())
          self.assertGreaterEqual(point.y(),header.mapToScene(QPointF()).y())
          self.assertLessEqual(point.y()+item.height(),header.mapToScene(QPointF(0,header.height())).y())

    def test_sections_create_real_views_without_warnings_at_narrow_and_wide_sizes(self):
        for width,height in ((900,620),(1400,940)):
         self.window.resize(width,height);frame(self.window)
         for section in ('types','schema','workflow','rules','groups','raw','sidebar','columns','users','layouts'):
          self.click('adminSection_'+section)
          self.assertEqual(self.admin.section,section)
          content=self.item('administrationContent')
          self.assertGreater(content.width(),300);self.assertGreater(content.height(),200)
          self.assertFalse(any(item.objectName()=='layoutEditorBrowser' for item in windows_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem())))
          self.assertEqual(self.fixture.warnings,[])

    def test_document_actions_share_header_without_an_extra_toolbar(self):
        for section in ('types','schema','workflow','rules','groups','sidebar','columns','raw','users','layouts'):
         self.click('adminSection_'+section)
         toolbars=[item for item in windows_fixture.SidebarEditorQmlTests.descendants(self.window.contentItem()) if item.objectName()=='administrationHeaderSaveBar' and item.isVisible()]
         self.assertEqual(len(toolbars),1,section)
         content=self.item('administrationContent')
         self.assertLessEqual(toolbars[0].mapToScene(QPointF(0,38)).y(),content.mapToScene(QPointF()).y())

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
        thumb=bar.mapToScene(QPointF(bar.width()/2,bar.height()*bar.property('size')/2)).toPoint()
        QTest.mousePress(self.window,Qt.LeftButton,pos=thumb)
        QTest.mouseMove(self.window,thumb+QPointF(0,60).toPoint())
        QTest.mouseRelease(self.window,Qt.LeftButton,pos=thumb+QPointF(0,60).toPoint())
        frame(self.window)
        self.assertGreater(self.item('adminGraphCanvasViewport').property('contentY'), 0)

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
                        self.assertTrue(self.item('adminToggleWorkflowList').isVisible())
                        if width >= 1400:
                            self.assertTrue(self.item('adminWorkflowList').isVisible())
                    self.assertTrue(self.item('administrationProjectSelector').isVisible())
                    self.assertEqual(self.admin.project, 'demo')
                    self.assertEqual(self.admin.schemaEditor.identity, 'demo')
                    self.assertGreater(self.item('adminGraphCanvas').height(), 120)
                    self.assertEqual(self.fixture.warnings, [])

    def test_workflow_list_and_inspector_resize_without_collapsing_admin_navigation(self):
        self.window.resize(1400,940);self.click('adminSection_workflow')
        graph=self.item('adminGraphCanvas');width=graph.width()
        self.click('adminToggleGraphProperties');self.assertGreater(self.item('adminGraphCanvas').width(),width)
        self.click('adminToggleGraphProperties');self.assertAlmostEqual(self.item('adminGraphCanvas').width(),width)
        library = self.item('adminWorkflowCatalogPanel')
        sidebar = self.item('administrationSidebar')
        self.assertLess(library.mapToScene(QPointF(library.width(), 0)).x(), self.item('adminGraphCanvas').mapToScene(QPointF()).x())
        self.assertGreater(library.mapToScene(QPointF()).x(),sidebar.mapToScene(QPointF(sidebar.width(),0)).x())
        self.assertTrue(self.item('adminSectionTitle_workflow').isVisible())
        self.click('adminToggleWorkflowList')
        self.assertGreater(self.item('adminGraphCanvas').width(), width)
        with self.assertRaises(StopIteration): self.item('adminWorkflowSearch')
        self.assertTrue(self.item('adminSection_groups').isVisible())
        self.click('adminToggleWorkflowList')
        self.assertTrue(self.item('adminWorkflowSearch').isVisible())
        self.click('adminToggleNavigation')
        self.assertGreater(self.item('adminGraphCanvas').width(), width)
        self.click('adminToggleNavigation')
        self.assertAlmostEqual(self.item('adminGraphCanvas').width(), width)
        sidebar_width = sidebar.width()
        split = self.item('adminCatalogSplit')
        start = split.mapToScene(QPointF(split.width() / 2, split.height() / 2)).toPoint()
        QTest.mousePress(self.window, Qt.LeftButton, pos=start)
        QTest.mouseMove(self.window, start + QPoint(45, 0), 40)
        QTest.mouseRelease(self.window, Qt.LeftButton, pos=start + QPoint(45, 0))
        frame(self.window)
        self.assertAlmostEqual(self.item('administrationSidebar').width(),sidebar_width)
        self.assertLess(self.item('adminGraphCanvas').width(), width)
        self.assertEqual(self.fixture.warnings, [])

    def test_sidebar_entry_selects_groups_even_after_another_admin_section(self):
        self.click('adminSection_types')
        self.fixture.sidebar.open_group_manager()
        self.assertEqual(self.admin.section, 'groups')

    def test_columns_editor_is_available_from_administration(self):
        self.click('adminSection_columns')
        self.assertEqual(self.admin.section,'columns')
        editor=self.item('administrationColumnsEditor')
        self.assertTrue(editor.property('saveActionsInHeader'))
        self.assertGreater(editor.width(),300)
        self.assertTrue(self.item('administrationProjectSelector').isVisible())
        self.assertEqual(self.fixture.warnings,[])

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

    def test_sidebar_editor_is_embedded_in_admin_navigation(self):
        self.click('adminSection_sidebar')
        frame(self.window)
        self.assertEqual(self.admin.section, 'sidebar')
        self.assertTrue(self.item('administrationSidebarEditor').isVisible())
        self.assertLessEqual(
            self.item('sidebarSaveButton').mapToScene(QPointF()).y()
            + self.item('sidebarSaveButton').height(),
            self.item('administrationContent').mapToScene(
                QPointF()).y() + 1,
        )
        self.assertFalse(any(window.property('kind') == 'sidebar_editor'
                             for window in self.fixture.app.allWindows()))
        with patch.object(self.fixture.application.window_model, 'open_help') as open_help:
            self.click('administrationHelpButton')
        open_help.assert_called_once_with('sidebar_editor')
        for width, height in ((900, 620), (1400, 940)):
            self.window.resize(width, height)
            frame(self.window)
            self.assertTrue(self.item('administrationSidebarEditor').isVisible())
            self.assertEqual(self.fixture.warnings, [])

    def test_regular_user_cannot_open_admin(self):
        self.fixture.admin_access.return_value = False
        self.fixture.application.server_state_changed.emit()
        self.assertFalse(self.fixture.application.window_model.is_window_visible('administration'))
        self.fixture.application._registry.invoke('show_sidebar_editor')
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
        self.assertTrue(self.item('adminConfirmSave').isVisible())
        with patch.object(env_inst, 'server_pool', type('Pool', (), {
                'is_stopped': False, 'add_task': lambda *_: worker})()), \
                patch.object(self.admin, '_refresh_pending_metadata'):
            self.click('adminConfirmSave')
            frame(self.window)
            QCoreApplication.processEvents()
        self.assertEqual(calls, ['save'])
        self.assertFalse(editor.dirty)
        self.assertEqual(editor._revision, 'saved')

    def test_builtin_schema_is_inspectable_but_cannot_be_edited(self):
        editor=self.admin.schemaEditor;editor._can_write=False;editor.stateChanged.emit()
        self.click('adminSection_schema');graph=self.item('adminGraphCanvas')
        self.assertTrue(graph.property('readOnly'));node=self.item('graphNode_demo/asset')
        self.fixture.click(self.window,node);self.assertEqual(editor.selectedNode,'demo/asset')
        original=copy.deepcopy(editor.document)
        start=node.mapToScene(QPointF(node.width()/2,node.height()/2)).toPoint()
        QTest.mousePress(self.window,Qt.LeftButton,pos=start);QTest.mouseMove(self.window,start+QPointF(45,20).toPoint());QTest.mouseRelease(self.window,Qt.LeftButton,pos=start+QPointF(45,20).toPoint());frame(self.window)
        self.assertEqual(editor.document,original);self.assertFalse(self.item('adminSaveDocument').isEnabled())

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
        self.window.resize(1400,940);self.click('adminSection_schema')
        editor=self.admin.schemaEditor;node=self.item('graphNode_demo/asset');graph=self.item('adminGraphCanvas')
        original=editor.nodes[0]['nodeX'];changes=QSignalSpy(editor.graphChanged)
        start=node.mapToScene(QPointF(node.width()/2,node.height()/2)).toPoint()
        QTest.mousePress(self.window,Qt.LeftButton,pos=start)
        QTest.mouseMove(self.window,start+QPointF(35,15).toPoint());QTest.mouseMove(self.window,start+QPointF(85,35).toPoint());frame(self.window)
        try:
         state=graph.property('ui').toVariant()
         self.assertTrue(state['pointer']['active']);self.assertGreater(state['pointer']['positions'][0]['nodeX'],original)
         self.assertEqual(editor.nodes[0]['nodeX'],original);self.assertEqual(changes.count(),0)
        finally:QTest.mouseRelease(self.window,Qt.LeftButton,pos=start+QPointF(85,35).toPoint())
        frame(self.window);self.assertEqual(changes.count(),1);self.assertGreater(editor.nodes[0]['nodeX'],original)

    def test_security_add_rule_and_discard_use_real_buttons(self):
        self.click('adminSection_rules')
        self.click('adminSecurityTab_search_filter')
        count = len(self.admin.securityEditor.rules)
        self.click('adminAddAccessRule')
        self.assertEqual(len(self.admin.securityEditor.rules), count + 1)
        self.assertTrue(self.admin.securityEditor.dirty)
        self.click('adminDiscardDocument')
        self.click('adminConfirmSave')
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
            self.item('adminSearchTypeForm')) if item.objectName() == 'adminSearchTypeHasPipeline' and item.isVisible()]
        self.assertEqual(checkboxes, [])

        self.click('adminCreateDocument')
        self.assertEqual(set(self.admin.typesEditor.document), {
            'title', 'description', 'color', 'hasPipeline', 'columns'})
        self.assertFalse(any(
            item.objectName() == 'adminSearchTypeName' and item.isVisible()
            for item in windows_fixture.SidebarEditorQmlTests.descendants(
                self.window.contentItem())))
        checkboxes = [item for item in windows_fixture.SidebarEditorQmlTests.descendants(
            self.item('adminSearchTypeForm')) if item.objectName() == 'adminSearchTypeHasPipeline' and item.isVisible()]
        self.assertEqual(len(checkboxes), 1)
        self.assertTrue(checkboxes[0].property('checked'))
        viewport=self.item('adminSearchTypeForm')
        viewport.setProperty('contentY',max(0,min(viewport.property('contentHeight')-viewport.height(),viewport.property('contentY')+checkboxes[0].mapToItem(viewport,QPointF()).y()-12)))
        frame(self.window)
        toggle=checkboxes[0]
        QTest.mouseClick(self.window,Qt.LeftButton,pos=toggle.mapToScene(QPointF(21,toggle.height()/2)).toPoint())
        frame(self.window)
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
        self.choose_page('searchTypePages','details')
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
        self.window.resize(1400,940);self.click('adminSection_schema')
        for prefix in ('graphInput_','graphOutput_'):
         port=self.item(prefix+'demo/asset');self.assertEqual(port.width(),36);self.assertEqual(port.height(),36)
         point=port.mapToScene(QPointF(port.width()/2,port.height()/2))
         self.assertGreater(point.x(),0);self.assertLess(point.x(),self.window.width())
        self.click('graphOutput_demo/asset')
        state=self.item('adminGraphCanvas').property('ui').toVariant();self.assertIsNotNone(state['pending'])
        self.item('adminGraphCanvas').forceActiveFocus();QTest.keyClick(self.window,Qt.Key_Escape);frame(self.window)
        self.assertIsNone(self.item('adminGraphCanvas').property('ui').toVariant()['pending'])


    def test_layouts_navigation_hosts_one_editor_and_protects_project(self):
        self.click('adminSection_layouts')
        self.assertTrue(self.item('administrationLayoutEditor').isVisible())
        self.assertTrue(self.item('administrationHeaderSaveBar').isVisible())
        host=self.admin.layoutEditor
        host.set_presentation_dirty(True)
        self.assertTrue(self.admin.projectLocked)
        self.assertFalse(self.item('administrationProjectSelector').isEnabled())
        host.set_presentation_dirty(False)
        self.assertFalse(self.admin.projectLocked)
        self.assertEqual(self.fixture.warnings,[])


    def test_shell_close_reveals_hidden_draft_and_does_not_destroy_it(self):
        from PySide6.QtQml import QQmlEngine, QQmlExpression
        self.admin.typesEditor.set_field('title','A hidden draft')
        self.click('adminSection_schema')
        shell=self.item('administrationFrameShell')
        expression=QQmlExpression(QQmlEngine.contextForObject(shell),shell,'dispatch({type:"close"})')
        expression.evaluate();self.assertFalse(expression.hasError(),expression.error().toString())
        frame(self.window)
        self.assertTrue(self.window.isVisible());self.assertEqual(self.admin.section,'types')
        self.assertTrue(self.admin.typesEditor.dirty)
        self.assertEqual(self.admin.typesEditor.document['title'],'A hidden draft')

    def test_clean_child_editor_locks_project_until_its_window_closes(self):
        windows=self.fixture.application.window_model
        self.assertFalse(self.admin.projectLocked)
        windows.show_child_window('process_dependencies','administration');frame(self.window)
        self.assertTrue(self.admin.projectLocked)
        self.assertFalse(self.item('administrationProjectSelector').isEnabled())
        windows.close_window('process_dependencies');frame(self.window)
        self.assertFalse(self.admin.projectLocked)
        self.assertTrue(self.item('administrationProjectSelector').isEnabled())

if __name__ == '__main__':
    unittest.main()
