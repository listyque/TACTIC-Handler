"""Workspace layouts reuse the native renderer without becoming document windows."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QGuiApplication, QInputMethodEvent
from tests import test_frame_table as frames
from tests.test_columns_table_view import _TableController, _TableColumns
from tests.test_table_service_workflows import Application
from thlib.ui.table.services import TableServicesController


class WorkspacePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close
    click = frames.FrameTableTests.click
    item = frames.FrameTableTests.item

    def owner(self):
        app = Application()
        app.tab.layout_view = 'dashboard.review'
        app.tab.tab_id = 'dashboard-tab'
        app.tab.title = 'Review'
        app.tab.layout_target = ''
        app._sessions = {'dashboard': SimpleNamespace(tabs=[app.tab])}
        services = TableServicesController(app)
        self.addCleanup(services.shutdown)
        return app, services

    def model(self):
        return dict(title='Review', targetSearchKey='sthpw/project?code=demo', layoutRecord={}, layoutView='dashboard.review',
            layoutNodes=[dict(kind='row', children=[dict(kind='metric',text='Assets',value=12),dict(kind='metric',text='Tasks',value=3)]),
                dict(kind='table',text='Assets',table=dict(searchType='demo/asset',parentKey='sthpw/project?code=demo'))])

    def load(self, scope):
        scope._model.update(columns=[dict(name='name',title='Name',width=180,cell=dict(kind='text'))],
            rows=[dict(key='demo/asset?project=demo&code=A',nodeId='nested:A',record=dict(name='Robot'),cells=dict(name=dict(text='Robot')))],
            selected=[],busy=False)

    def test_page_uses_widgets_and_real_nested_selection_without_a_window(self):
        app, services = self.owner()
        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            services.workspaceLayout.open_result(self.model(),'Review',app.tab.tab_id)
        for scope in services.workspaceLayout.scopes.values():
            self.load(scope)
        app.open_window.assert_not_called()
        self.assertTrue(services.workspaceLayout.active)
        self.assertEqual(services.document,{})
        window, view = self.create('features/table/WorkspacePage.qml',dict(
            services=services,controller=_TableController(),columnsController=_TableColumns(),users=None,administration=None),width=1000,height=700)
        self.assertEqual(self.item(view,'workspacePageTitle').property('text'),'Review')
        self.assertEqual(self.item(view,'customLayout_0_0_value').property('text'),'12')
        scope=services.workspaceLayout.table('customLayout_1')
        self.click(window,self.item(view,'nestedSelect'))
        self.assertEqual(scope.model['selected'],['demo/asset?project=demo&code=A'])
        self.click(window,self.item(view,'nestedFilter'))
        event=QInputMethodEvent();event.setCommitString('Robot')
        QGuiApplication.sendEvent(window.activeFocusItem(),event);frames.frame(window)
        self.assertEqual(scope.model['filter'],'Robot')
        with patch.object(scope,'reload') as reload:
            self.click(window,self.item(view,'nestedReload'))
            reload.assert_called_once()
        view.setWidth(400);window.resize(400,700);frames.frame(window)
        first=self.item(view,'customLayout_0_0');second=self.item(view,'customLayout_0_1')
        self.assertEqual(first.mapToScene(QPointF()).x(),second.mapToScene(QPointF()).x())
        self.assertGreater(second.mapToScene(QPointF()).y(),first.mapToScene(QPointF()).y())

    def test_modal_document_close_does_not_destroy_workspace_scopes(self):
        app, services = self.owner()
        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            services.workspaceLayout.open_result(self.model(),'Review',app.tab.tab_id)
            page_scope=services.workspaceLayout.table('customLayout_1')
            page_scope._model['filter']='Robot'
            services.customLayout.open_result(self.model(),'Details','details')
        app.open_window.assert_called_once_with('table_document')
        self.assertTrue(services.scope_visible(page_scope))
        services._document_visibility('table_document',False)
        self.assertTrue(services.scope_visible(page_scope))
        self.assertTrue(services.workspaceLayout.active)
        original=app.tab
        app.tab=SimpleNamespace(layout_view='',table_view='table')
        app._sessions['normal']=SimpleNamespace(tabs=[app.tab])
        app.results_view_changed.emit()
        self.assertFalse(services.workspaceLayout.active)
        self.assertFalse(services.scope_visible(page_scope))
        app.tab=original
        services.workspaceLayout.open_view('dashboard.review','Review',original.tab_id)
        self.assertTrue(services.scope_visible(page_scope))
        self.assertEqual(page_scope.model['filter'],'Robot')

    def test_navigation_uses_the_page_owner_without_querying_records(self):
        from thlib.ui.controllers.navigation import NavigationMixin
        app, services = self.owner()
        app._table_services=services
        app.navigation_model=SimpleNamespace(entry=lambda key:None)
        app._current_section_key='dashboard'
        app._set_loading=lambda value:None
        calls=[]
        with patch.object(services.workspaceLayout,'open_view',side_effect=lambda *args,**kwargs:calls.append((args,kwargs))):
            NavigationMixin._show_or_load_tab(app,app.tab)
        self.assertEqual(calls,[(('dashboard.review',app.tab.title,app.tab.tab_id),dict(search_key=''))])
        app.open_window.assert_not_called()

    def test_late_page_reply_cannot_replace_the_new_page_or_open_a_window(self):
        app,services=self.owner()
        replies=[]
        with patch('thlib.tactic_classes.server_start',return_value=object()),patch.object(services,'_run',side_effect=lambda read,loaded,**kwargs:replies.append(loaded)):
            services.workspaceLayout.open_view('dashboard.first','First','first')
            app.tab=SimpleNamespace(layout_view='dashboard.second',tab_id='second',title='Second')
            services.workspaceLayout.open_view('dashboard.second','Second','second')
        replies[0](self.model())
        self.assertEqual(services.workspaceLayout.document['title'],'Second')
        self.assertTrue(services.workspaceLayout.document['layoutBusy'])
        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            replies[1](dict(self.model(),layoutView='dashboard.second'))
        self.assertEqual(services.workspaceLayout.document['title'],'Second')
        self.assertNotIn('first',services.workspaceLayout.pages)
        self.assertIn('second',services.workspaceLayout.pages)
        app.open_window.assert_not_called()

    def test_page_script_close_closes_its_section_without_closing_object_documents(self):
        app,services=self.owner()
        app._current_section_key='dashboard'
        app.close_section=Mock();app.refresh_current=Mock()
        runner=Mock();runner.run.return_value=dict(commands=[dict(type='close-layout')])
        with patch('thlib.ui.table.nested.NestedTableController.reload'):
            services.workspaceLayout.open_result(self.model(),'Review',app.tab.tab_id)
            with patch('thlib.tactic_classes.server_start',return_value=object()),patch('thlib.ui.table.scripts.TableScriptRunner',return_value=runner),patch.object(services,'_run',side_effect=lambda read,loaded,settled:loaded(read())):
                services.workspaceLayout.run('close configured layout')
        app.close_section.assert_called_once_with('dashboard')
        app.window_model.close_window.assert_not_called()
