"""Native authoring lifecycle and nonretrying writes; no browser or live database."""
import copy
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from tests import test_frame_table as frames
from tests.test_columns_table_view import _visual_items
from PySide6.QtCore import QObject, Signal, QCoreApplication
from tests.qt_application import gui_test_application
from thlib import tactic_classes as tc
from thlib.environment import env_inst, env_server
from thlib.ui.layout_editor import LayoutEditorHost, layout_tree
from thlib.ui.admin.layout_editor_api import layout_editor_request

XML='<config><!--custom--><cards_example layout="sobject-layout"><element name="title" custom="kept"><display class="title"/></element></cards_example></config>'
class Worker(QObject):
    result=Signal(object)
    error=Signal(object)
    def __init__(self,operation):
        super().__init__();self.operation=operation;self.cancelled=False
    def start(self):
        pass
    def cancel(self):
        self.cancelled=True
class Pool:
    is_stopped=False
    def __init__(self):self.workers=[]
    def add_task(self,operation):
        worker=Worker(operation);self.workers.append(worker);return worker

class LayoutEditorTests(unittest.TestCase):
    close = frames.FrameTableTests.close
    @classmethod
    def setUpClass(cls):cls.app=gui_test_application()
    def setUp(self):
        self.application=SimpleNamespace(is_stream_server=True, can_manage_tools=True,debug_log=None,_current_tab=lambda:None)
        self.host=LayoutEditorHost(self.application);self.addCleanup(self.host.shutdown)
        stype=SimpleNamespace(get_code=lambda:'demo/asset',get_info=lambda:{'title':'Assets'})
        self.enterContext(patch.object(env_inst,'projects',{'demo':stype}))
        self.project=SimpleNamespace(stypes={'demo/asset':stype},get_stypes=Mock(side_effect=AssertionError('No network discovery on the UI thread')))
        self.enterContext(patch.object(env_inst,'get_project_by_code',return_value=self.project))
        self.pool=Pool();self.enterContext(patch.object(env_inst,'server_pool',self.pool))
        self.enterContext(patch.object(env_server,'get_server',return_value='http://localhost:9123'))
        self.server=object();self.enterContext(patch.object(tc,'server_start',return_value=self.server))
        self.read=self.enterContext(patch.object(tc,'_execute_read_only_procedure_serverside'))
        self.write=self.enterContext(patch.object(tc,'execute_procedure_serverside'))
        self.enterContext(patch('thlib.server_cache.invalidate_domains'))
        self.host.reset('demo');self.host._view='cards_example'
    def configuration(self):
        return dict(revision='R1',sources=[dict(id=7,xml=XML,priority=0)],layers=[],layout_templates=[],views=['cards_example'],resolved={'configured':True})
    def loaded(self):
        self.host.activate('demo');worker=self.pool.workers[-1]
        worker.result.emit({'stypes':[{'code':'demo/asset','title':'Assets'}]})
        QCoreApplication.processEvents();worker=self.pool.workers[-1]
        worker.result.emit(dict(configuration=self.configuration(),sampleItems=[]))
        QCoreApplication.processEvents()
        self.assertTrue(self.host.canWrite)
    def test_live_preview_keeps_edits_and_rejects_stale_reply_without_saving(self):
        self.loaded()
        self.host._draft_timer.stop()
        self.host._resolve_draft()
        old = self.pool.workers[-1]
        self.assertFalse(self.host.busy)
        self.host.set_xml(XML.replace('custom="kept"', 'custom="changed"'))
        old.result.emit({'interface': {'table': {'item_layout': {'elements': []}}}})
        QCoreApplication.processEvents()
        self.assertIsNone(self.host.model['preview'])
        self.host._draft_timer.stop()
        self.host._resolve_draft()
        resolved = {'table': {'item_layout': {'elements': [{'name':'title'}]}}}
        self.pool.workers[-1].result.emit({'interface': resolved})
        QCoreApplication.processEvents()
        self.assertEqual(self.host.model['liveInterface'], resolved)
        self.assertEqual(self.host.model['checked'], '')
        self.host.set_xml(XML.replace('custom="kept"', 'custom="newer"'))
        self.assertEqual(self.host.model['liveInterface'], resolved)
        self.assertIsNone(self.host.model['preview'])
        self.assertTrue(self.host.dirty)
        self.write.assert_not_called()
    def test_cold_project_discovers_types_only_in_the_worker_with_captured_server(self):
        self.project.stypes=None
        self.host.reset('demo')
        self.project.get_stypes.assert_not_called()
        self.assertEqual(self.host.model['searchTypes'],[])
        self.read.assert_not_called()
        self.host.activate('demo');worker=self.pool.workers[-1]
        response={'stypes':[{'code':'demo/hidden','title':'Hidden','__record_read__':{'available':False}},{'code':'demo/asset','title':'Assets'}]}
        self.read.return_value=response
        self.assertEqual(worker.operation(),response)
        self.assertIs(self.read.call_args.args[0],layout_editor_request)
        self.assertEqual(self.read.call_args.args[1]['action'],'catalog')
        self.assertEqual(self.read.call_args.args[1]['project_code'],'demo')
        self.assertIs(self.read.call_args.kwargs['server'],self.server)
        worker.result.emit(response);QCoreApplication.processEvents()
        self.assertEqual(self.host.model['searchTypes'],[{'value':'demo/asset','label':'Assets'}])
        self.assertEqual(self.host._search_type,'demo/asset')
        self.assertEqual(len(self.pool.workers),2)
        self.assertTrue(self.host.busy)
    def test_warm_project_validates_cached_types_before_reading_a_layout(self):
        foreign=SimpleNamespace(get_code=lambda:'other/activity',get_info=lambda:{'title':'Activity'})
        self.project.stypes['other/activity']=foreign
        self.host.reset('demo');self.host.activate('demo')
        worker=self.pool.workers[-1]
        response={'stypes':[{'code':'demo/asset','title':'Assets'}]}
        self.read.return_value=response
        worker.operation()
        self.assertIs(self.read.call_args.args[0],layout_editor_request)
        self.assertEqual(self.read.call_args.args[1]['action'],'catalog')
        worker.result.emit(response);QCoreApplication.processEvents()
        self.assertEqual(self.host.model['searchTypes'],[{'value':'demo/asset','label':'Assets'}])
        self.assertEqual(self.host._search_type,'demo/asset')
        self.read.return_value=dict(configuration=self.configuration(),sampleItems=[])
        self.pool.workers[-1].operation()
        self.assertEqual(self.read.call_args.args[1]['search_type'],'demo/asset')
    def test_preview_displays_read_failure_instead_of_loading_forever(self):
        self.loaded();self.host._draft_timer.stop()
        self.host._error='Registered table does not exist'
        window,view=frames.FrameTableTests.create(self,'features/administration/layouts/LayoutEditorView.qml',
            dict(controller=self.host),width=1200,height=800)
        texts=[item.property('text') for item in _visual_items(view) if item.isVisible()]
        self.assertNotIn('Loading interface...',texts)
        self.assertIn(self.host._error,texts)
    def test_page_card_focus_loads_catalog_and_preserves_type_view_and_filters(self):
        filters=[['code','=','CARD001']]
        self.host.preview_scope('demo','demo/card','cards_example',filters)
        self.pool.workers[-1].operation()
        self.assertEqual(self.read.call_args.args[1]['action'],'catalog')
        self.pool.workers[-1].result.emit({'stypes':[
            {'code':'demo/asset','title':'Assets'},{'code':'demo/card','title':'Cards'}]})
        QCoreApplication.processEvents()
        self.pool.workers[-1].operation()
        request=self.read.call_args.args[1]
        self.assertEqual((request['action'],request['search_type'],request['view']),
                         ('read','demo/card','cards_example'))
        self.assertEqual(request['filters'],filters)
        self.assertEqual(len(self.host.model['searchTypes']),2)
    def test_cancelled_catalog_cannot_repopulate_another_project(self):
        self.project.stypes=None;self.host.reset('demo');self.host.activate('demo');worker=self.pool.workers[-1]
        self.host.reset('other');self.assertTrue(worker.cancelled)
        worker.result.emit({'stypes':[{'code':'demo/asset','title':'Assets'}]});QCoreApplication.processEvents()
        self.assertEqual(self.host.model['searchTypes'],[])
        with self.assertRaisesRegex(RuntimeError,'cancelled'):worker.operation()
        self.read.assert_not_called()
    def test_empty_or_invalid_catalog_does_not_loop_or_load_an_invalid_type(self):
        self.project.stypes=None;self.host.reset('demo');self.host.activate('demo')
        self.pool.workers[-1].result.emit({'stypes':[{'title':'missing code'}]});QCoreApplication.processEvents()
        self.assertIn('Invalid Search Type catalog',self.host._error)
        self.assertFalse(self.host.busy);self.host.reload()
        self.pool.workers[-1].result.emit({'stypes':[]});QCoreApplication.processEvents()
        count=len(self.pool.workers);self.host.activate('demo');self.assertEqual(len(self.pool.workers),count)
    def test_parser_preserves_custom_nodes_and_rejects_entities(self):
        tree=layout_tree(XML);self.assertEqual(tree['children'][0]['children'][0]['type'],8)
        for text in ['<!DOCTYPE config [<!ENTITY x "private">]><config/>','<wrong/>','<config>','<config>'+('a'*524289)+'</config>']:
            with self.assertRaises(Exception):layout_tree(text)
    def test_source_id_uses_server_integer_and_rejects_unknowns(self):
        self.loaded();self.host.select_source(7.0)
        self.assertIs(type(self.host._source),int)
        for source in [True,8,'7',{},None]:
            self.host.select_source(source);self.assertEqual(self.host._source,7)
        self.host.select_source('');self.assertEqual(self.host._source,'')
    def test_stale_context_and_shutdown_cancel_read_without_mutation(self):
        self.host.activate('demo');worker=self.pool.workers[-1]
        self.host.reset('other');self.assertTrue(worker.cancelled)
        worker.result.emit(dict(configuration=self.configuration(),sampleItems=[]))
        QCoreApplication.processEvents()
        self.assertIsNone(self.host._configuration);self.assertEqual(self.host._project,'other')
        with self.assertRaisesRegex(RuntimeError,'cancelled'):worker.operation()
        self.read.assert_not_called()
        self.host.shutdown();self.assertFalse(self.host.busy)
    def test_save_requires_exact_checked_buffer_and_never_retries(self):
        self.loaded();self.host.set_xml(XML.replace('kept','changed'));self.host.save()
        self.assertEqual(len(self.pool.workers),2)
        self.host._checked=self.host._xml;self.host.save();worker=self.pool.workers[-1]
        self.write.return_value=self.configuration();worker.operation()
        self.write.assert_called_once();self.read.assert_not_called()
        self.assertIs(self.write.call_args.kwargs['server'],self.server)
        worker.error.emit(({'exception':TimeoutError('unacknowledged write'),'stacktrace':''},worker))
        QCoreApplication.processEvents()
        self.assertTrue(self.host.writeUncertain)
        previous=self.host._xml;self.host.set_xml(XML);self.host.save()
        self.assertEqual(self.host._xml,previous);self.assertEqual(len(self.pool.workers),3)
        self.host.reload(True);self.pool.workers[-1].result.emit(dict(configuration=self.configuration(),sampleItems=[]))
        QCoreApplication.processEvents()
        self.assertFalse(self.host.writeUncertain);self.assertFalse(self.host.dirty)
    def test_malformed_save_acknowledgement_remains_uncertain(self):
        self.loaded();self.host.set_xml(XML.replace('kept','changed'));self.host._checked=self.host._xml
        self.host.save();self.pool.workers[-1].result.emit({'sources':[]})
        QCoreApplication.processEvents()
        self.assertTrue(self.host.writeUncertain);self.assertTrue(self.host.dirty)
    def test_permission_and_changed_context_block_mutations(self):
        self.loaded();self.application.can_manage_tools=False;self.host.set_xml('<config/>');self.host.check()
        self.assertEqual(self.host._xml,XML);self.assertEqual(len(self.pool.workers),2)
        self.application.can_manage_tools=True;self.host._view='other';self.host.set_xml('<config/>');self.assertEqual(self.host._xml,XML)
    def test_external_view_contains_no_session_ticket(self):
        self.loaded()
        with patch('thlib.ui.layout_editor.QDesktopServices.openUrl') as open_url:
            self.host.open_view();self.assertEqual(open_url.call_count,1)
            url=open_url.call_args.args[0].toString();self.assertIn('/projects/demo/',url);self.assertNotIn('ticket',url)
            self.host.set_xml(XML+' ');self.host.open_view();self.assertEqual(open_url.call_count,1)
