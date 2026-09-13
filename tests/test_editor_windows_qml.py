"""Native administration/search preview windows with real QML and input."""

import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import PropertyMock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Material')
os.environ.setdefault('QT_QPA_FONTDIR', 'C:/Windows/Fonts')

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPointF, Qt, QUrl, Signal
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from shiboken6 import getCppPointer

from thlib.ui.administration import AdministrationController
from thlib.tactic_classes import execute_procedure_serverside as execute_server_procedure
from thlib.ui.application import _destroy_transient_windows
from thlib.ui.filter_editor import FilterEditorController
from thlib.ui.process_filter_editor import ProcessFilterEditorController
from thlib.ui.localization import CatalogTranslator
from thlib.ui.user import UserController
from thlib.ui.workspace_models.windows import VisibleFloatingWindowModel
from tests.test_sidebar_search_workspace import SidebarSearchWorkspaceTests
from tests.test_sidebar_editor_qml import SidebarEditorQmlTests
from tests.profile_ui_responsiveness import frame

QML = Path(__file__).resolve().parents[1] / 'thlib/ui/qml'


class EditorWindowQmlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SidebarEditorQmlTests.setUpClass()
        SidebarSearchWorkspaceTests.setUpClass()
        cls.app = QGuiApplication.instance()
        cls.app.setFont(QFont('Segoe UI', 10))

    def setUp(self):
        self.fixture = SidebarSearchWorkspaceTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.application = self.fixture.application
        self.admin_access = self.enterContext(patch.object(
            type(self.application), 'can_administer', new_callable=PropertyMock,
            return_value=True,
        ))
        self.application._performance = None
        self.sidebar = self.fixture.sidebar
        self.enterContext(patch.object(self.sidebar, 'begin_session'))
        self.enterContext(patch.object(self.sidebar, 'refresh_search_presets'))
        self.state = self.application.workspace_state
        self.users = UserController(self.application)
        self.admin = AdministrationController(self.application, self.users)
        self.enterContext(patch.object(self.admin, '_publish_catalog'))
        self.admin._loaded({
            'groups': [dict(code='G%s' % n, login_group='group_%02d' % n, description='Team %s' % n)
                       for n in range(40)],
            'memberships': [dict(login='user_0', login_group='group_00')],
            'users': [dict(login='user_%s' % n, displayName='Participant %02d' % n)
                      for n in range(80)],
        })
        self.enterContext(patch.object(self.admin, 'reload'))
        self.sidebar.groupManagementRequested.connect(self.admin.show_groups)
        self.filter_editor = FilterEditorController(
            self.state.filter_model.records, self.state.filter_column_model.records,
            self.application.search_filter_relations, self.application.notify,
            self.application.has_active_search_tab, self.application.filter_editor_context,
            self.application.stage_filter_editor_records,
        )
        self.enterContext(patch.object(self.filter_editor, 'load_presets'))
        self.sidebar.attach_filter_editor(self.filter_editor)
        self.process_filters = ProcessFilterEditorController(
            self.application.filter_editor_context,
            self.application.apply_process_filter_settings,
            self.application.notify,
        )
        self.translator = CatalogTranslator(QML.parent / 'translations/ru.json')
        self.app.installTranslator(self.translator)
        self.addCleanup(self.app.removeTranslator, self.translator)
        self.engine = QQmlEngine()
        self.warnings = []
        self.engine.warnings.connect(lambda errors: self.warnings.extend(e.toString() for e in errors))
        self.visible_windows = VisibleFloatingWindowModel(self.application.window_model)
        context = self.engine.rootContext()
        for name, value in {
            **SidebarEditorQmlTests.icons,
            'appController': self.application, 'workspaceState': self.state,
            'projectModel': self.application.project_model,
            'versionsModel': self.application.versions_model,
            'windowModel': self.application.window_model, 'visibleWindowModel': self.visible_windows,
            'sidebarEditorController': self.sidebar,
            'sidebarEntryModel': self.sidebar.entries,
            'sidebarSecurityGroupModel': self.sidebar.security_groups,
            'administrationController': self.admin, 'administrationGroupModel': self.admin.groups,
            'administrationMemberModel': self.admin.members,
            'filterEditorController': self.filter_editor, 'filterPresetModel': self.filter_editor.presets,
            'processFilterEditorController': self.process_filters,
            'processFilterModel': self.process_filters.model,
            'filterModel': self.state.filter_model, 'filterColumnModel': self.state.filter_column_model,
            'advancedFilterSuggestionModel': self.state.advanced_filter_suggestion_model,
            'quickFilterEditorController': self.fixture.filters,
            'userController': self.users, 'userListModel': self.users.users,
        }.items():
            context.setContextProperty(name, value)
        self.component = QQmlComponent(self.engine)
        self.component.setData(b'''
import QtQuick
import QtQuick.Controls
import "." as App
ApplicationWindow {
    id: owner
    width: 1100; height: 780; visible: true
    QtObject { id: windowAppearanceController; function apply(w, d, b, f) {} }
    QtObject { id: configurationController; signal closeAllowed() }
    App.Theme {
        id: theme; dark: true; popupAnimationsEnabled: false
        fadeAnimationsEnabled: false; clickAnimationsEnabled: false; hoverAnimationsEnabled: false
    }
    App.WindowHost { anchors.fill: parent; theme: theme; ownerWindow: owner }
}
''', QUrl.fromLocalFile(str(QML / '_EditorWindowsTest.qml')))
        self.owner = self.component.create()
        self.assertIsNotNone(self.owner, [e.toString() for e in self.component.errors()])
        owner_pointer = getCppPointer(self.owner)[0]
        self.native_windows = self.app.allWindows()
        self.owner = next(w for w in self.native_windows if getCppPointer(w)[0] == owner_pointer)
        self.addCleanup(self.close)
        frame(self.owner)

    def close(self):
        self.admin.shutdown()
        for key in ('process_filter_editor', 'quick_filter_editor', 'sidebar_search_preview', 'administration'):
            self.application.window_model.close_window(key)
        QCoreApplication.processEvents()
        self.owner.close()
        self.owner.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.fixture.tearDown()
        self.assertEqual(self.warnings, [])

    def test_nested_modals_are_owned_by_the_invoking_editor(self):
        self.application.window_model.show_window('sidebar_editor')
        sidebar_window = self.window('sidebar_editor')
        self.sidebar.open_group_manager()
        groups_window = self.window('administration')
        self.assertIs(groups_window.transientParent(), sidebar_window)
        self.application.window_model.close_window('administration')
        self.sidebar.open_search()
        QCoreApplication.processEvents()
        preview_window = self.window('sidebar_search_preview')
        self.assertIs(preview_window.transientParent(), sidebar_window)
        self.application.window_model.show_child_window('quick_filter_editor', 'sidebar_search_preview')
        filters_window = self.window('quick_filter_editor')
        self.assertIs(filters_window.transientParent(), preview_window)
        self.application.window_model.close_window('sidebar_search_preview')
        self.assertFalse(self.application.window_model.is_window_visible('quick_filter_editor'))

    def test_teardown_destroys_nested_windows_before_their_owner(self):
        self.application.window_model.show_window('sidebar_editor')
        sidebar_window = self.window('sidebar_editor')
        self.sidebar.open_group_manager()
        administration_window = self.window('administration')
        hidden = []
        administration_window.visibleChanged.connect(
            lambda visible: hidden.append('administration') if not visible else None
        )
        sidebar_window.visibleChanged.connect(
            lambda visible: hidden.append('sidebar_editor') if not visible else None
        )

        _destroy_transient_windows(self.owner)
        QCoreApplication.processEvents()

        self.assertFalse(administration_window.isVisible())
        self.assertFalse(sidebar_window.isVisible())
        self.assertTrue(self.owner.isVisible())
        self.assertEqual(hidden, ['administration', 'sidebar_editor'])

    def test_debug_log_filters_wrap_inside_the_narrow_window(self):
        from thlib.environment import env_mode
        from thlib.ui.debug_logging import DebugLogController

        debug_log = DebugLogController(Path(env_mode.current_path))
        self.debug_log = debug_log
        self.addCleanup(debug_log.shutdown)
        context = self.engine.rootContext()
        for name, value in {
            'debugLog': debug_log,
            'debugLogModel': debug_log.entries_model,
            'debugGroupModel': debug_log.groups_model,
        }.items():
            context.setContextProperty(name, value)
        self.application.window_model.show_window('debug_log')
        self.addCleanup(
            self.application.window_model.close_window, 'debug_log'
        )
        window = self.window('debug_log')
        for width, expected_rows in ((680, 2), (1100, 1)):
            with self.subTest(width=width):
                window.resize(width, 480)
                frame(window)
                filters = self.item(window, 'debugLogLevelFilters')
                chips = [
                    item for item in SidebarEditorQmlTests.descendants(filters)
                    if item.objectName() == 'debugLogLevelChip'
                ]
                self.assertEqual(len(chips), 8)
                self.assertEqual(filters.height(), expected_rows * 28 +
                                 (expected_rows - 1) * 6)
                for chip in chips:
                    position = chip.mapToScene(QPointF())
                    self.assertGreaterEqual(position.x(), 12)
                    self.assertLessEqual(
                        position.x() + chip.width(), window.width() - 12
                    )

    def test_server_change_cancels_group_draft_and_stale_worker(self):
        self.admin.set_member('user_1', True)
        self.assertTrue(self.admin.dirty)
        from unittest.mock import Mock
        worker = Mock()
        self.admin._worker = worker
        self.admin._server_key = ('a different server', 'other login')
        previous_generation = self.admin._generation
        self.admin._server_changed()
        worker.cancel.assert_called_once()
        self.assertGreater(self.admin._generation, previous_generation)
        self.assertEqual(self.admin.groups.rowCount(), 0)
        self.assertFalse(self.admin.dirty)

    def test_existing_group_save_uses_the_real_server_procedure_envelope(self):
        import json
        from thlib import tactic_classes as tc
        scripts = []

        def execute(_path, kwargs):
            script = kwargs['code']
            scripts.append(script)
            # execute_procedure_serverside reserves `code` for executable
            # source. An object's identity must not occupy that argument.
            self.assertTrue(script.startswith('def '), script)
            if 'def save_security_group(' in script:
                return {'info': {'spt_ret_val': json.dumps({'code': 'G0'})}}
            return {'info': {'spt_ret_val': json.dumps(self.admin._catalog)}}

        self.admin.set_member('user_1', True)
        with patch.object(tc, 'execute_procedure_serverside', execute_server_procedure), \
                patch.object(tc, 'server_start', return_value=SimpleNamespace(execute_python_script=execute)), \
                patch.object(self.admin, '_run', side_effect=lambda operation, completed: completed(operation())):
            self.admin.save()
        self.assertEqual(len(scripts), 2)
        self.assertIn("group_code='G0'", scripts[0])
        self.assertIn("add_members=['user_1']", scripts[0])

    def test_group_worker_is_disconnected_and_late_results_are_ignored(self):
        from thlib.environment import env_inst

        class Worker(QObject):
            result = Signal(object)
            error = Signal(object)
            cancelled = False

            def start(self):
                pass

            def cancel(self):
                self.cancelled = True

        worker = Worker()
        completed = []
        pool = SimpleNamespace(is_stopped=False, add_task=lambda *_: worker)
        with patch.object(env_inst, 'server_pool', pool):
            self.admin._run(lambda: {}, completed.append)
        worker.result.emit({'queued': True})
        self.admin.shutdown()
        worker.result.emit({'late': True})
        QCoreApplication.processEvents()
        self.assertTrue(worker.cancelled)
        self.assertIsNone(self.admin._worker_callbacks)
        self.assertEqual(completed, [])

    def test_committed_catalog_updates_both_native_membership_directions(self):
        from thlib.environment import env_inst
        from thlib.tactic_classes import Login
        native = Login({'login': 'user_0', 'code': 'user_0'}, [], [])
        with patch.object(env_inst, 'logins', {'user_0': native}), patch.object(self.users, '_rebuild'):
            # Call the real publisher (setup only mocks it while loading fixtures).
            self.admin._users = self.users
            AdministrationController._publish_catalog(self.admin)
            self.assertEqual(native.get_login_groups()[0].get_login_group(), 'group_00')
            self.assertEqual(native.get_login_groups()[0].get_logins(), [native])

    def window(self, kind):
        self.native_windows = self.app.allWindows()
        return next(w for w in self.native_windows if w.isVisible() and w.property('kind') == kind)

    def item(self, window, name):
        return next(item for item in SidebarEditorQmlTests.descendants(window.contentItem())
                    if item.objectName() == name)

    def click(self, window, item):
        point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
        QTest.mouseClick(window, Qt.LeftButton, pos=point.toPoint())
        frame(window)

    def choose_combo_option(self, window, combo, index):
        self.click(window, combo)
        self.native_windows = self.app.allWindows()
        popup_window = next(w for w in self.native_windows
                            if w.isVisible() and w.transientParent() is window
                            and (w.flags() & Qt.WindowType_Mask) == Qt.Popup)
        options = combo.findChild(QQuickItem, 'comboBoxPopupList')
        option = next(item for item in SidebarEditorQmlTests.descendants(options)
                      if item.metaObject().className().startswith('ItemDelegate')
                      and item.property('index') == index)
        point = option.mapToScene(QPointF(option.width() / 2, option.height() / 2))
        QTest.mouseClick(popup_window, Qt.LeftButton, pos=point.toPoint())
        frame(window)

    def open_preview_filter_menu(self):
        self.sidebar.open_search()
        QCoreApplication.processEvents()
        window = self.window('sidebar_search_preview')
        button = self.item(window, 'previewSearchFiltersButton')
        for width, height in ((1360, 880), (960, 620)):
            window.resize(width, height)
            frame(window)
            position = button.mapToScene(QPointF())
            self.assertGreaterEqual(position.x(), 12)
            self.assertLessEqual(position.x() + button.width(), window.width() - 12)
            self.assertGreater(button.width(), 25)
            self.assertGreater(button.height(), 25)
        self.filter_editor.load_presets.reset_mock()
        self.application._load_tab.reset_mock()
        self.click(window, button)
        menu = window.findChild(QObject, 'searchResultFiltersMenu')
        self.assertTrue(menu.property('opened'))
        self.native_windows = self.app.allWindows()
        popup = next(w for w in self.native_windows
                     if w.isVisible() and w.transientParent() is window
                     and (w.flags() & Qt.WindowType_Mask) == Qt.Popup)
        self.filter_editor.load_presets.assert_not_called()
        self.application._load_tab.assert_not_called()
        return window, menu, popup

    def click_filter_menu_action(self, popup, command):
        def action_command(item):
            data = item.property('modelData')
            if hasattr(data, 'toVariant'):
                data = data.toVariant()
            return data.get('command') if isinstance(data, dict) else None

        row = next(item for item in SidebarEditorQmlTests.descendants(popup.contentItem())
                   if action_command(item) == command)
        owner = popup.transientParent()
        point = row.mapToScene(QPointF(row.width() / 2, row.height() / 2))
        QTest.mouseClick(popup, Qt.LeftButton, pos=point.toPoint())
        QCoreApplication.processEvents()
        frame(owner)

    def test_preview_filter_menu_opens_existing_process_editor_for_custom_tab(self):
        window, _menu, popup = self.open_preview_filter_menu()
        self.click_filter_menu_action(popup, 'filter_processes')
        editor = self.window('process_filter_editor')
        frame(editor)
        self.assertIs(editor.transientParent(), window)
        self.assertEqual(editor.modality(), Qt.WindowModal)
        self.assertTrue(self.process_filters.valid_context,
                        (self.process_filters._context_key,
                         self.application.filter_editor_context(), self.process_filters.model.rowCount()))
        self.assertEqual(self.process_filters._context_key,
                         ('demo', 'demo/asset', 'demo/asset@my_tasks'))
        rows = self.process_filters.model._records
        index = next(n for n, row in enumerate(rows)
                     if row['kind'] == 'process' and row['key'] == 'storyboard')
        row = next(item for item in SidebarEditorQmlTests.descendants(editor.contentItem())
                   if item.objectName() == 'processFilterRow' and item.property('index') == index)
        checkbox = next(item for item in SidebarEditorQmlTests.descendants(row)
                        if item.metaObject().className().startswith('CheckBox'))
        self.click(editor, checkbox)
        self.assertFalse(self.process_filters.model._records[index]['checked'])
        save = next(item for item in SidebarEditorQmlTests.descendants(editor.contentItem())
                    if item.property('text') == 'Сохранить и закрыть')
        point = save.mapToScene(QPointF(save.width() / 2, save.height() / 2))
        QTest.mouseClick(editor, Qt.LeftButton, pos=point.toPoint())
        frame(window)
        tab = self.application._current_tab()
        self.assertIn('storyboard', next(iter(tab.process_ignore['processes'].values())))
        self.assertFalse(self.application.window_model.is_window_visible('process_filter_editor'))
        from thlib.environment import env_read_config
        persisted = env_read_config(
            filename='process_ignore_dict',
            unique_id=self.process_filters._settings_path(self.application.filter_editor_context()),
            long_abs_path=True,
        )
        self.assertEqual(persisted, tab.process_ignore)
        self.assertEqual(self.application._sessions['demo/asset'].tabs[0].process_ignore, {})

    def test_preview_filter_menu_selects_shared_preset_and_executes_one_search(self):
        window, _menu, popup = self.open_preview_filter_menu()
        self.state.filter_column_model.replace([
            {'value': 'category', 'label': 'Category', 'dataType': 'text'}])
        self.filter_editor.presets.replace([{
            'code': 'P1', 'title': 'Lighting review', 'view': 'link_search:review:demo/asset',
            'records': [{'column': 'category', 'relation': 'is', 'value': 'props',
                         'rowEnabled': True, 'operator': 'begin', 'isDefault': True}],
        }])
        frame(popup)
        self.click_filter_menu_action(popup, 'preset:0')
        self.assertEqual(self.filter_editor.selected_preset, 0)
        self.assertEqual(self.application._current_tab().filter_records[0]['value'], 'props')
        self.assertEqual(self.state.filter_model.records()[0]['value'], 'props')
        self.application._load_tab.assert_called_once()
        self.filter_editor.load_presets.assert_not_called()
        self.assertTrue(self.filter_editor._search_type_library)
        self.assertEqual(self.application.current_section_key, 'demo/asset@my_tasks')

    def test_preview_filter_menu_refresh_preserves_search_type_library(self):
        _window, _menu, popup = self.open_preview_filter_menu()
        self.click_filter_menu_action(popup, 'refresh_presets')
        self.filter_editor.load_presets.assert_called_once()
        self.assertTrue(self.filter_editor._search_type_library)
        self.assertEqual(self.filter_editor._current_context()['preset_scope'], '')
        self.application._load_tab.assert_not_called()

    def test_preview_long_preset_menu_reserves_its_scrollbar_gutter(self):
        _window, menu, popup = self.open_preview_filter_menu()
        self.filter_editor.presets.replace([{
            'code': 'P%s' % n, 'title': 'Saved search %s' % n,
            'view': 'link_search:search%s:demo/asset' % n,
        } for n in range(30)])
        frame(popup)
        flickable = menu.findChild(QQuickItem, 'actionMenuFlickable')
        scrollbar = menu.findChild(QQuickItem, 'actionMenuScrollBar')
        self.assertTrue(scrollbar.isVisible())
        self.assertGreater(flickable.property('contentHeight'), flickable.height())
        self.assertLessEqual(popup.height(), popup.screen().availableGeometry().height())
        target = next(item for item in SidebarEditorQmlTests.descendants(popup.contentItem())
                      if item.objectName() == 'actionMenuPrimaryTarget')
        self.assertLessEqual(target.mapToScene(QPointF(target.width(), 0)).x(),
                             scrollbar.mapToScene(QPointF()).x() - 4)
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QWheelEvent
        from PySide6.QtTest import QSignalSpy
        position = flickable.mapToScene(QPointF(flickable.width() / 2, flickable.height() / 2))
        event = QWheelEvent(
            position, QPointF(popup.mapToGlobal(position.toPoint())),
            QPoint(), QPoint(0, -720), Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False,
        )
        moved = QSignalSpy(flickable.contentYChanged)
        self.app.sendEvent(popup, event)
        if flickable.property('contentY') <= 0:
            self.assertTrue(moved.wait(1000))
        self.assertGreater(flickable.property('contentY'), 0)
        self.filter_editor.load_presets.assert_not_called()
        self.application._load_tab.assert_not_called()

    def test_preview_filter_menu_reveals_its_existing_search_editor(self):
        window, _menu, popup = self.open_preview_filter_menu()
        editor = self.item(window, 'previewSearchEditor')
        editor.setProperty('filtersExpanded', False)
        self.click_filter_menu_action(popup, 'advanced_search')
        self.assertTrue(editor.property('filtersExpanded'))
        self.assertTrue(editor.property('activeFocus'))
        self.application._load_tab.assert_not_called()

    def test_preview_sorting_and_grouping_use_the_active_result_model(self):
        from tests.test_result_organization import _node

        self.sidebar.open_search()
        QCoreApplication.processEvents()
        window = self.window('sidebar_search_preview')
        model = self.application.workspace_model
        model.replace_nodes([
            _node('A2', 'Asset 2', status='Review'),
            _node('A1', 'Asset 1', status='Done'),
            _node('A3', 'Asset 3', status='Review'),
        ])
        for width, height in ((960, 620), (1360, 880)):
            window.resize(width, height)
            frame(window)
            for name in ('previewSearchFiltersButton', 'previewSortButton', 'previewGroupButton'):
                button = self.item(window, name)
                position = button.mapToScene(QPointF())
                self.assertTrue(button.isVisible())
                self.assertGreaterEqual(position.x(), 12)
                self.assertLessEqual(position.x() + button.width(), window.width() - 12)
        self.application._load_tab.reset_mock()
        for button_name, command in (('previewSortButton', 'name_desc'),
                                     ('previewGroupButton', 'status')):
            self.click(window, self.item(window, button_name))
            self.native_windows = self.app.allWindows()
            popup = next(w for w in self.native_windows
                         if w.isVisible() and w.transientParent() is window
                         and (w.flags() & Qt.WindowType_Mask) == Qt.Popup)
            self.click_filter_menu_action(popup, command)
            if command == 'name_desc':
                self.assertEqual([node.title for node in model._roots],
                                 ['Asset 3', 'Asset 2', 'Asset 1'])
        self.assertEqual(self.application._current_tab().sort_mode, 'name_desc')
        self.assertEqual(self.application._current_tab().group_mode, 'status')
        groups = [node for node in model._items if node.node_type == 'group']
        self.assertEqual([(node.title, node.child_count) for node in groups],
                         [('Done', 1), ('Review', 2)])
        self.assertIs(self.sidebar.previewSurfaces.data(
            self.sidebar.previewSurfaces.index(0, 0),
            next(role for role, name in self.sidebar.previewSurfaces.roleNames().items()
                 if name == b'resultModel')), model)
        self.application._load_tab.assert_called_once()
        self.assertEqual(self.application._sessions['demo/asset'].tabs[0].group_mode, 'none')
        screenshot = os.environ.get('EDITOR_WINDOW_SCREENSHOTS')
        if screenshot:
            window.grabWindow().save(str(Path(screenshot) / 'search-preview-tools.png'))

    def test_preview_uses_real_object_views_and_stages_the_sidebar_default(self):
        self.sidebar.open_search()
        QCoreApplication.processEvents()
        window = self.window('sidebar_search_preview')
        from thlib.ui.workspace_models.results_types import WorkspaceNode
        nodes = [WorkspaceNode(
            'asset_%s' % n, 'sobject', 'demo/asset?code=A%s' % n,
            'A%s' % n, 'Asset %02d' % n, subtitle='Object description',
            preview_requested=True, card_preview_requested=True,
        ) for n in range(30)]
        model = self.application.workspace_model
        model.replace_nodes(nodes)
        frame(window)
        pane = self.item(window, 'sidebarPreviewResults')
        combo = self.item(window, 'previewResultViewMode')
        for width, height in ((960, 620), (1360, 880)):
            window.resize(width, height)
            frame(window)
            for index, mode in enumerate(self.sidebar.resultViewOptions):
                self.choose_combo_option(window, combo, index)
                self.assertEqual(self.application.results_view_mode, mode['value'])
                self.assertEqual(self.sidebar.selectedEntry['resultViewMode'], mode['value'])
                surface = pane.property('activeResultSurface')
                self.assertIs(surface.property('resultModel'), model)
                grid = self.item(window, 'searchResultsGridView')
                rows = self.item(window, 'searchResultsListView')
                table = self.item(window, 'searchResultsTableView')
                self.assertEqual(grid.isVisible(), mode['value'] == 'tiles')
                self.assertEqual(table.isVisible(), mode['value'] == 'table')
                self.assertEqual(
                    rows.isVisible(), mode['value'] not in ('tiles', 'table')
                )
                view = table if table.isVisible() else grid if grid.isVisible() else rows
                expected = 'WorkspaceCard' if grid.isVisible() else 'WorkspaceResultItem'
                delegates = [
                    item for item in SidebarEditorQmlTests.descendants(view)
                    if item.objectName() == 'searchResultTableRow'
                    or item.metaObject().className().startswith(expected)
                ]
                self.assertTrue(delegates)
                self.assertEqual(view.property('count'), 30)
                self.assertGreater(view.property('contentHeight'), view.height())
                self.assertEqual(pane.property('splitView'), mode['value'].startswith('splitted_'))
                if grid.isVisible():
                    self.assertTrue(any(item.property('text') == 'Результаты поиска'
                                        for item in SidebarEditorQmlTests.descendants(pane)))
                self.assertGreaterEqual(combo.mapToScene(QPointF()).x(), 0)
                self.assertLessEqual(combo.mapToScene(QPointF()).x() + combo.width(), width)
                screenshot = os.environ.get('EDITOR_WINDOW_SCREENSHOTS')
                if screenshot and mode['value'] in ('continious', 'tiles'):
                    window.grabWindow().save(str(Path(screenshot) /
                        ('search-preview-%s-%s.png' % (mode['value'], width))))
        self.choose_combo_option(window, combo, 0)
        row = next(item for item in SidebarEditorQmlTests.descendants(pane)
                   if item.metaObject().className().startswith('WorkspaceResultItem')
                   and item.property('nodeId') == 'asset_0' and item.isVisible())
        self.click(window, row)
        self.assertEqual(self.application.selected_result_node_ids, ['asset_0'])
        self.application.window_model.close_window('sidebar_search_preview')
        QCoreApplication.processEvents()
        self.assertTrue(self.sidebar.dirty)
        self.assertEqual(self.sidebar.selectedEntry['resultViewMode'], 'continious')
        self.fixture.fixture.rpc.assert_not_called()

    def test_group_window_layout_search_membership_and_save_input(self):
        self.admin.open()
        window = self.window('administration')
        self.assertEqual(window.modality(), Qt.WindowModal)
        self.assertIs(window.transientParent(), self.owner)
        writes = []
        self.enterContext(patch.object(self.admin, '_run', side_effect=lambda *args: writes.append(args)))
        for width, height in ((900, 620), (1280, 900)):
            window.resize(width, height)
            frame(window)
            groups = self.item(window, 'securityGroupsList')
            members = self.item(window, 'securityMembersList')
            self.assertGreater(groups.height(), height * .5)
            self.assertGreater(members.height(), 160)
            for name in ('createSecurityGroup', 'saveSecurityGroup', 'securityMemberSearch'):
                item = self.item(window, name)
                pos = item.mapToScene(QPointF())
                self.assertGreaterEqual(pos.x(), 0)
                self.assertLessEqual(pos.x() + item.width(), width)
                self.assertLessEqual(pos.y() + item.height(), height)
        field = self.item(window, 'securityMemberSearch')
        self.click(window, field)
        for character in 'Participant 01':
            QTest.keyClick(window, character)
        frame(window)
        self.assertEqual(self.admin.members.rowCount(), 1)
        self.click(window, self.item(window, 'securityMember_user_1'))
        self.assertEqual(self.admin.memberCount, 2)
        self.click(window, self.item(window, 'saveSecurityGroup'))
        self.assertEqual(len(writes), 1)
        screenshot = os.environ.get('EDITOR_WINDOW_SCREENSHOTS')
        if screenshot:
            window.grabWindow().save(str(Path(screenshot) / 'administration.png'))

    def test_create_group_form_keeps_members_and_save_reachable(self):
        self.admin.open()
        window = self.window('administration')
        self.click(window, self.item(window, 'createSecurityGroup'))
        name = self.item(window, 'securityGroupName')
        self.assertFalse(name.property('readOnly'))
        self.click(window, name)
        for character in 'lighting':
            QTest.keyClick(window, character)
        frame(window)
        self.click(window, self.item(window, 'segmentedButtonSegment_members'))
        self.click(window, self.item(window, 'securityMember_user_1'))
        self.assertEqual(self.admin.draft['name'], 'lighting')
        self.assertEqual(self.admin.memberCount, 1)
        self.assertTrue(self.item(window, 'saveSecurityGroup').isEnabled())
        self.admin.discard()
        self.assertFalse(self.admin.dirty)

    def test_preview_has_real_preset_query_quick_filters_and_modal_lifetime(self):
        self.sidebar.open_search()
        QCoreApplication.processEvents()
        window = self.window('sidebar_search_preview')
        self.assertEqual(window.modality(), Qt.WindowModal)
        self.assertIs(window.transientParent(), self.owner)
        from thlib.ui.workspace_models.results_types import WorkspaceNode
        self.application.workspace_model.replace_nodes([
            WorkspaceNode('asset_%s' % n, 'sobject', 'demo/asset?code=A%s' % n,
                          'A%s' % n, 'Asset %02d' % n)
            for n in range(35)
        ])
        self.state.filter_column_model.replace([
            {'value': 'category', 'label': 'Category', 'dataType': 'text'}])
        self.filter_editor.presets.replace([{
            'code': 'P%s' % n, 'title': 'Saved search %02d' % n,
            'view': 'link_search:p%s:demo/asset' % n,
            'records': [{'column': 'category', 'relation': 'is', 'value': 'props',
                         'rowEnabled': True, 'operator': 'begin', 'isDefault': True}],
        } for n in range(20)])
        self.filter_editor._set_busy(False)
        for width, height in ((960, 620), (1360, 880)):
            window.resize(width, height)
            frame(window)
            self.assertGreater(self.item(window, 'sidebarPreviewResults').width(), 350)
            self.assertGreater(self.item(window, 'previewSearchEditor').height(), 400)
            self.assertEqual(self.item(window, 'sidebarPreviewResults').property('activeResultCount'), 35)
        combo = self.item(window, 'advancedSearchPresetCombo')
        self.click(window, combo)
        self.native_windows = self.app.allWindows()
        popup_window = next(w for w in self.native_windows
                            if w.isVisible() and w is not window and w is not self.owner)
        options = combo.findChild(QQuickItem, 'comboBoxPopupList')
        self.assertGreater(options.height(), 100)
        self.assertIs(popup_window.transientParent(), window)
        option = next(item for item in SidebarEditorQmlTests.descendants(options)
                      if item.metaObject().className().startswith('ItemDelegate')
                      and item.property('index') == 1)
        point = option.mapToScene(QPointF(option.width() / 2, option.height() / 2))
        QTest.mouseClick(popup_window, Qt.LeftButton, pos=point.toPoint())
        frame(window)
        self.assertGreaterEqual(self.filter_editor.selected_preset, 0)
        self.assertEqual(self.application._current_tab().filter_records[0]['value'], 'props')
        if QGuiApplication.platformName() != 'offscreen':
            window.requestActivate()
            self.assertTrue(QTest.qWaitForWindowActive(window))
            combo.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertEqual(self.filter_editor.selected_preset, 2)
        self.click(window, self.item(window, 'previewQuickFiltersButton'))
        popup = window.findChild(QObject, 'previewQuickFiltersPopup')
        self.assertTrue(popup.property('opened'))
        from PySide6.QtCore import QMetaObject
        QMetaObject.invokeMethod(popup, 'close')
        screenshot = os.environ.get('EDITOR_WINDOW_SCREENSHOTS')
        if screenshot:
            frame(window)
            window.grabWindow().save(str(Path(screenshot) / 'search-preview.png'))


if __name__ == '__main__':
    unittest.main()
