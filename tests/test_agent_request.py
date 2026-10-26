"""Actual native request controls and captured context; no provider is required."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import os
import time
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, Qt, Signal, QMimeData, QUrl, QPoint, QPointF, QCoreApplication
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication, QImage, QColor, QDragEnterEvent, QDropEvent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.test_frame_script_tools import ScriptToolsTests, QML
from tests.profile_ui_responsiveness import frame
from thlib.ui.agent_request import AgentRequestController
from thlib.ui.controllers.types import ActionRegistry
from thlib.ui.workspace_models.windows import FloatingWindowModel
from thlib.ui.icon_font import qml_icon_bindings
from thlib.environment import env_inst
from thlib.ui.controllers.item_actions import ItemActionsMixin
from thlib.ui.controllers.item_operations import ItemOperationsMixin


class Application(QObject, ItemActionsMixin, ItemOperationsMixin):
    authentication_changed = Signal()
    signing_out = Signal()
    notification_changed = Signal(str)
    agentRequestRequested = Signal(str)

    def __init__(self):
        super().__init__()
        self._registry = ActionRegistry()
        self.window_model = FloatingWindowModel({})
        self.current_project_code = 'one'
        self.can_administer = True
        self.section = SimpleNamespace(entry_key='cg/shot@shots', title='Shots', search_type='cg/shot')
        self.tab = SimpleNamespace(table_view='table')
        self.keys = ['cg/shot?project=one&code=SH001']

    def _current_section(self):
        return self.section

    def _current_tab(self):
        return self.tab

    def script_shelf_context(self):
        return dict(search_keys=list(self.keys))


class Server:
    def __init__(self):
        self.requests = {}
        self.last = None
        self.files = {}

    def execute_cmd(self, command, values):
        action = values['action']
        if 'AgentAttachmentCmd' in command:
            code = values['attachment_id']
            if action == 'preview':
                return dict(status='OK', info=dict(url='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC'))
            if action == 'start':
                self.files[code] = dict(attachment_id=code, name=values['name'], size=values['size'], media_type=values['media_type'])
            result = self.files[code]
        elif action == 'state':
            result = dict(hosts=[dict(host_id='host', label='Codex', capabilities=dict(changes=True, trials=False, steering=True, web_search=True, models=[dict(id='fixture',label='Fixture model', is_default=True, efforts=['low', 'high'])]))],
                requests=[dict(request_id=key, prompt=row['document']['prompt'], title=row['document']['prompt'] or 'Attachments',
                    activity=1000,search_type='cg/shot',type_title='Shots',pinned=False,group='',archived=False,status=row['status']) for key, row in self.requests.items()],
                groups=[],groups_revision='fixture',total=len(self.requests),next_offset=None)
        elif action == 'submit':
            result = dict(request_id=values['request_id'], document=deepcopy(values['document']),
                          model=values['document'].get('model', ''), effort=values['document'].get('effort', ''), provider=values['document'].get('provider','codex'),
                          status='running', events=['External agent started', 'reference_read: inProgress'], answer='', error='',
                          messages=[dict(id=values['request_id'], role='user', text=values['document']['prompt'],
                              attachments=[self.files[code] for code in values['document'].get('attachments', [])])])
            self.requests[result['request_id']] = result
            self.last = result
        elif action == 'message':
            result = self.requests[values['request_id']]
            result.update(model=values.get('model', ''), effort=values.get('effort', ''))
            result['messages'].append(dict(id=values['message_id'], role='user', text=values['text'], attachments=[]))
            result['status'] = 'running'
        elif action == 'cancel':
            result = self.requests[values['request_id']]
            result['status'] = 'cancelled'
        else:
            result = self.requests[values['request_id']]
        return dict(status='OK', info=deepcopy(result))


class AgentRequestTransport(unittest.TestCase):
    def test_new_saved_draft_uses_the_newly_captured_project(self):
        calls=[]
        context=dict(project='other',client='TH',search_type='cg/shot')
        row=dict(request_id='new-draft',document=dict(context=context),messages=[],status='draft')
        class CapturedServer:
            def execute_cmd(self, command, values):
                calls.append(values)
                return dict(status='OK',info=dict(hosts=[],requests=[],groups=[]) if values['action']=='state' else row)
        result=AgentRequestController._load(CapturedServer(),'old','library','old-chat',None,1,
            library_operation=dict(action='draft',values=dict(request_id='new-draft',context=context)))
        self.assertNotIn('error',result)
        self.assertEqual(result['selected'],'new-draft')
        self.assertTrue(all(call['project_code']=='other' for call in calls))


class AgentRequestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ScriptToolsTests.setUpClass()

    def test_item_menu_captures_clicked_or_selected_objects_and_keeps_draft(self):
        app=Application()
        from tests.test_sobject_info_entrypoint import _sobject_node
        nodes={key:_sobject_node() for key in ('one','two')}
        for index,(key,node) in enumerate(nodes.items(),1):
            node.node_id=key;node.search_key=f'cg/shot?project=one&code=SH00{index}'
        app._node_for_any=nodes.get
        app.tab.selected_node_ids=['two']
        app.debug_log=None
        controller=AgentRequestController(app,env_inst.server_pool);self.addCleanup(controller.reset)
        notices=[];app.notification_changed.connect(notices.append)
        with patch('thlib.tactic_classes.server_start',return_value=Server()),patch.object(controller,'refresh'):
            menu=app.item_menu_actions('one')
            action=next(row for row in menu if row.get('command')=='agent_request')
            self.assertFalse(action['advanced'])
            app.invoke_item_action('agent_request','one')
            self.assertEqual(controller.model['context']['search_keys'],[nodes['one'].search_key])
            app.tab.selected_node_ids=['one','two']
            app.invoke_item_action('agent_request','one')
            self.assertEqual(controller.model['context']['search_keys'],[node.search_key for node in nodes.values()])
            controller.handle('prompt','Keep this draft')
            app.tab.selected_node_ids=['two']
            app.invoke_item_action('agent_request','two')
            self.assertEqual(controller.model['prompt'],'Keep this draft')
            self.assertEqual(len(controller.model['context']['search_keys']),2)
            self.assertIn('Send or clear',notices[-1])
            controller.handle('prompt','')
            controller._model['attachments']=[dict(attachment_id='fixture',name='draft.txt')]
            app.invoke_item_action('agent_request','two')
            self.assertEqual(controller.model['attachments'][0]['name'],'draft.txt')
            app.can_administer=False
            self.assertFalse(any(row.get('command')=='agent_request' for row in app.item_menu_actions('one')))

    def test_provider_selection_filters_models_and_freezes_during_turn(self):
        surface=ScriptToolsTests();surface.setUp();self.addCleanup(surface.doCleanups)
        for name,value in qml_icon_bindings(QML.parents[2],surface.engine).items():
            surface.engine.rootContext().setContextProperty(name,value)
        app=Application();controller=AgentRequestController(app,env_inst.server_pool);self.addCleanup(controller.reset)
        server=Server();original=server.execute_cmd
        def execute(command,values):
            result=original(command,values)
            if values['action']=='state':
                result['info']['hosts'][0]['capabilities'].update(default_provider='codex',providers=[dict(id='codex',name='Codex',kind='codex'),dict(id='local',name='Local fixture',kind='local')],models=[
                    dict(id='fixture',label='Account model',provider='codex',is_default=True,efforts=['low','high']),
                    dict(id='fixture',label='Local model',provider='local',is_default=True,efforts=[])])
            return result
        with patch.object(server,'execute_cmd',side_effect=execute),patch('thlib.tactic_classes.server_start',return_value=server):
            controller.open()
            until=time.monotonic()+10
            while controller._in_flight and time.monotonic()<until:QTest.qWait(10)
            self.assertFalse(controller._in_flight)
            view=surface.create(QML/'features/scripts/AgentRequestView.qml',dict(theme=surface.theme,controller=controller,width=1000,height=650))
            window=QQuickWindow();window.resize(1000,650);surface.windows.append(window);view.setParentItem(window.contentItem());window.show();frame(window)
            choice=surface.item(view,'agentRequestProvider');choice.forceActiveFocus();QTest.keyClick(window,Qt.Key_Down);frame(window)
            self.assertEqual(controller.model['provider'],'local')
            self.assertEqual(surface.item(view,'agentRequestModel').property('currentText'),'Agent default')
            surface.item(view,'agentRequestModel').forceActiveFocus();QTest.keyClick(window,Qt.Key_Down);frame(window)
            self.assertEqual(controller.model['model'],'fixture')
            surface.fill(window,surface.item(view,'agentRequestPrompt'),'Read the selected objects')
            surface.click(window,surface.item(view,'agentRequestSend'))
            until=time.monotonic()+10
            while controller._in_flight and time.monotonic()<until:QTest.qWait(10)
            frame(window)
            self.assertEqual(server.last['document']['provider'],'local')
            self.assertFalse(surface.item(view,'agentRequestProvider').isEnabled())
            controller.handle(dict(type='provider',value='codex'))
            self.assertEqual(controller.model['provider'],'local')
            self.assertFalse(surface.warnings,surface.warnings)

    def test_context_real_input_submission_cancel_reopen_and_stale_reply(self):
        surface = ScriptToolsTests()
        surface.setUp()
        self.addCleanup(surface.doCleanups)
        for name, value in qml_icon_bindings(QML.parents[2], surface.engine).items():
            surface.engine.rootContext().setContextProperty(name, value)
        if os.name == 'nt':
            for name in ('segoeui.ttf', 'segoeuib.ttf'):
                QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR'])/'Fonts'/name))
            surface.app.setFont(QFont('Segoe UI'))
        app = Application()
        notices = []
        app.notification_changed.connect(notices.append)
        controller = AgentRequestController(app, env_inst.server_pool)
        self.addCleanup(controller.reset)
        server = Server()
        with patch('thlib.tactic_classes.server_start', return_value=server):
            controller.open()
            view = surface.create(QML/'features/scripts/AgentRequestView.qml',
                dict(theme=surface.theme, controller=controller, width=1000, height=650))
            window = QQuickWindow()
            window.resize(1000, 650)
            window.setColor(surface.theme.property('workspace'))
            surface.windows.append(window)
            view.setParentItem(window.contentItem())
            window.show()
            window.requestActivate()

            def wait():
                deadline = time.monotonic() + 10
                while controller._in_flight and time.monotonic() < deadline:
                    QTest.qWait(10)
                self.assertFalse(controller._in_flight)
                self.assertFalse(controller.model['error'], controller.model)
                frame(window)

            wait()
            choice = surface.item(view, 'agentRequestModel')
            choice.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertEqual(controller.model['model'], 'fixture')
            effort = surface.item(view, 'agentRequestEffort')
            effort.forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            surface.item(view, 'agentRequestEffort').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            self.assertEqual(controller.model['effort'], 'high')
            clipboard = QGuiApplication.clipboard()
            saved_clipboard = QMimeData()
            original = clipboard.mimeData()
            for format in original.formats() if original else []:
                saved_clipboard.setData(format, original.data(format))
            if original and original.formats():
                self.addCleanup(clipboard.setMimeData, saved_clipboard)
            else:
                self.addCleanup(clipboard.clear)
            image = QImage(32, 32, QImage.Format_RGB32)
            image.fill(QColor('red'))
            clipboard.setImage(image)
            surface.item(view, 'agentRequestPrompt').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_V, Qt.ControlModifier)
            wait()
            self.assertEqual(len(controller.model['attachments']), 1)
            self.assertTrue(controller.model['previews'])
            with tempfile.TemporaryDirectory(prefix='native-agent-drop-') as directory:
                path = Path(directory)/'dropped.bin'
                path.write_bytes(b'Native drop fixture')
                mime = QMimeData()
                mime.setUrls([QUrl.fromLocalFile(str(path))])
                enter = QDragEnterEvent(QPoint(400, 250), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
                QCoreApplication.sendEvent(window, enter)
                surface.app.processEvents()
                drop = QDropEvent(QPointF(400, 250), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
                QCoreApplication.sendEvent(window, drop)
                wait()
                self.assertTrue(drop.isAccepted())
                self.assertEqual(len(controller.model['attachments']), 2)
            surface.fill(window, surface.item(view, 'agentRequestPrompt'), 'Explain the selected shots')
            surface.click(window, surface.item(view, 'agentRequestChanges'))
            self.assertTrue(controller.model['allowChanges'])
            self.assertEqual(controller.model['prompt'], 'Explain the selected shots')
            controller._request('poll')
            wait()
            self.assertEqual(controller.model['prompt'], 'Explain the selected shots')
            surface.fill(window, surface.item(view, 'agentRequestPrompt'), '')
            QTest.keyClick(window, Qt.Key_Backspace)
            QTest.keyClick(window, Qt.Key_Return)
            wait()
            self.assertEqual(server.last['document']['prompt'], '')
            self.assertEqual(server.last['document']['context']['search_keys'], app.keys)
            self.assertEqual(server.last['document']['effort'], 'high')
            self.assertFalse(surface.item(view, 'agentRequestEffort').isEnabled())
            status = surface.item(view, 'agentRequestStatus')
            self.assertEqual(status.property('text'), 'Agent working')
            ancestor = status.parentItem()
            while ancestor and ancestor.objectName() != 'agentTranscript':ancestor = ancestor.parentItem()
            self.assertIsNotNone(ancestor)
            if os.environ.get('TACTIC_AGENT_CAPTURE'):
                Path(os.environ['TACTIC_AGENT_CAPTURE']).mkdir(parents=True, exist_ok=True)
                window.grabWindow().save(str(Path(os.environ['TACTIC_AGENT_CAPTURE'])/'working-native.png'))
            self.assertEqual(server.last['document']['context']['page'], 'cg/shot@shots')
            self.assertEqual(len(server.last['document']['attachments']), 2)
            surface.fill(window, surface.item(view, 'agentRequestPrompt'), 'Use the reference process')
            surface.click(window, surface.item(view, 'agentRequestSend'))
            wait()
            self.assertEqual(server.last['messages'][-1]['text'], 'Use the reference process')
            server.last.update(status='completed', outcome='completed', answer='**Done**')
            server.last['messages'].append(dict(id='answer', role='assistant', text='**Done**', attachments=[]))
            server.last['events'] = ['ts_records_create: completed']
            controller._request('poll')
            wait()
            self.assertIn('Task completed', notices)
            for width in (520, 1000):
                view.setWidth(width)
                window.resize(width, 650)
                frame(window)
                answer = surface.item(view, 'agentAssistantMessage')
                details = surface.item(view, 'agentOperationDetails')
                events = surface.item(view, 'agentOperationEvents')
                status = surface.item(view, 'agentRequestStatusRow')
                self.assertEqual(surface.item(view, 'agentRequestStatus').property('text'), 'Task completed')
                self.assertAlmostEqual(answer.mapToScene(QPointF()).x(), status.mapToScene(QPointF()).x(), delta=1)
                self.assertAlmostEqual(answer.width(), status.width(), delta=1)
                self.assertAlmostEqual(answer.mapToScene(QPointF()).x(), details.mapToScene(QPointF()).x(), delta=1)
                self.assertAlmostEqual(answer.width(), details.width(), delta=1)
                self.assertAlmostEqual(answer.width(), events.width(), delta=1)
            surface.item(view, 'agentRequestModel').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Up)
            frame(window)
            self.assertEqual(controller.model['model'], '')
            self.assertEqual(controller.model['effort'], '')
            self.assertEqual(surface.item(view, 'agentRequestEffort').property('currentIndex'), 0)
            surface.item(view, 'agentRequestEffort').forceActiveFocus()
            QTest.keyClick(window, Qt.Key_Down)
            frame(window)
            surface.fill(window, surface.item(view, 'agentRequestPrompt'), 'Summarize the result')
            surface.click(window, surface.item(view, 'agentRequestSend'))
            wait()
            self.assertEqual(len(server.last['messages']), 4)
            self.assertEqual(server.last['model'], '')
            self.assertEqual(server.last['effort'], 'low')
            app.current_project_code = 'two'
            app.keys = ['cg/shot?project=two&code=OTHER']
            self.assertEqual(controller.model['request']['document']['context']['project'], 'one')
            surface.click(window, surface.item(view, 'agentRequestCancel'))
            wait()
            self.assertEqual(controller.model['request']['status'], 'cancelled')
            controller.application.window_model.close_window('agent_request')
            controller._model['previews'] = {}
            controller.open()
            wait()
            self.assertTrue(controller.model['previews'])
            self.assertEqual(controller.model['request']['document']['context']['project'], 'one')
            for width in (520, 1000):
                view.setWidth(width)
                window.resize(width, 650)
                frame(window)
                self.assertGreater(surface.item(view, 'agentRequestOutput').height(), 0)
            output = os.environ.get('TACTIC_AGENT_CAPTURE')
            if output:
                capture = dict(controller.model)
                Path(output).mkdir(parents=True, exist_ok=True)
                Path(output, 'native-model.json').write_text(json.dumps(capture, ensure_ascii=False), encoding='utf-8')
                paired = Path(output, 'browser-model.json')
                if paired.is_file():
                    controller._model = dict(controller.initial(),**json.loads(paired.read_text(encoding='utf-8')))
                    controller.changed.emit()
                    frame(window)
                    self.assertIsNotNone(surface.item(view, 'agentHistoryList'))
                window.grabWindow().save(str(Path(output, 'native.png')))
            generation = controller._generation
            controller.reset()
            controller._done(dict(generation=generation, selected='stale', request={}, hosts=[], requests=[]))
            self.assertEqual(controller.model['selected'], '')
            with patch('thlib.tactic_classes.server_start', side_effect=PermissionError('Session expired')):
                controller.open()
                self.assertEqual(controller.model['error'], 'Session expired')
            controller.deleteLater()
            app.deleteLater()
            self.assertFalse(surface.warnings, surface.warnings)


if __name__ == '__main__':
    unittest.main()
