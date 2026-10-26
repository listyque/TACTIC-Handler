"""Real native history input against an owned temporary Stream API fixture."""
import json
import os
from pathlib import Path
import time
import tempfile
import unittest
from urllib.request import Request, urlopen
from unittest.mock import patch

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from tests.test_frame_script_tools import ScriptToolsTests, QML
from tests.test_agent_request import Application
from tests.profile_ui_responsiveness import frame
from thlib.environment import env_inst
from thlib.ui.agent_request import AgentRequestController
from thlib.ui.icon_font import qml_icon_bindings


@unittest.skipUnless(os.environ.get('TACTIC_AGENT_TEST_URL'), 'Run with the owned HTTP fixture')
class AgentHistoryInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ScriptToolsTests.setUpClass()
        if os.name=='nt':
            for name in ('segoeui.ttf','segoeuib.ttf'):
                QFontDatabase.addApplicationFont(str(Path(os.environ['WINDIR'])/'Fonts'/name))
            ScriptToolsTests.app.setFont(QFont('Segoe UI'))

    def test_sidebar_native_names_groups_pins_archive_and_switching_drafts(self):
        base=os.environ['TACTIC_AGENT_TEST_URL'];ticket=os.environ.pop('TACTIC_AGENT_TEST_TICKET')
        class Server:
            project='empty'
            def get_project(self):return self.project
            def set_project(self,project):self.project=project
            def execute_cmd(self,command,values):
                payload=dict(method='execute_cmd',args=[dict(ticket=ticket,project=self.project),command,values],kwargs={})
                with urlopen(Request(base+'/admin/rpc',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}),timeout=10) as response:
                    value=json.load(response)
                return value['result']
        surface=ScriptToolsTests();surface.setUp();self.addCleanup(surface.doCleanups)
        for name,value in qml_icon_bindings(QML.parents[2],surface.engine).items():surface.engine.rootContext().setContextProperty(name,value)
        app=Application();app.current_project_code='empty'
        app.keys=[]
        controller=AgentRequestController(app,env_inst.server_pool);self.addCleanup(controller.reset)
        with patch('thlib.tactic_classes.server_start',return_value=Server()):
            controller.open()
            view=surface.create(QML/'features/scripts/AgentRequestView.qml',dict(theme=surface.theme,controller=controller,width=1200,height=760))
            window=QQuickWindow();window.resize(1200,760);window.setColor(surface.theme.property('workspace'));surface.windows.append(window)
            view.setParentItem(window.contentItem());window.show();window.requestActivate()
            def wait():
                until=time.monotonic()+10
                while (controller._in_flight or controller._history_timer.isActive()) and time.monotonic()<until:QTest.qWait(10)
                self.assertFalse(controller._in_flight)
                self.assertFalse(controller.model['error'],controller.model['error'])
                frame(window)
            def click(name):surface.click(window,surface.item(view,name));wait()
            wait()
            self.assertGreater(len(controller.model['requests']),2)
            self.assertEqual(controller.model['history']['project'],'')
            old=next(row for row in controller.model['requests'] if row['title']=='Previous delivery')
            click('agentHistoryOpen_'+old['key'])
            self.assertEqual(controller.model['context']['project'],'one')
            with tempfile.TemporaryDirectory(prefix='agent-cross-project-file-') as directory:
                source=Path(directory)/'reference.txt';source.write_text('Own conversation attachment')
                controller.add_files([QUrl.fromLocalFile(str(source))]);wait()
                file=controller.model['attachments'][0]
                self.assertEqual(file['name'],'reference.txt')
                downloaded=controller._download_file(controller._server,'one',file['attachment_id'],controller._generation)
                self.assertNotIn('error',downloaded)
                result=Path(downloaded['directory'])/'reference.txt'
                self.assertEqual(result.read_text(),'Own conversation attachment')
                result.unlink();result.parent.rmdir()
            if os.environ.get('TACTIC_AGENT_CAPTURE'):
                window.grabWindow().save(str(Path(os.environ['TACTIC_AGENT_CAPTURE'])/'native-history-initial.png'))
            click('agentHistoryNew')
            identity=controller.model['selected']
            self.assertEqual(controller.model['request']['status'],'draft')
            click('agentRequestRename')
            surface.fill(window,surface.item(view,'setting_title'),'Named review')
            click('agentHistorySave')
            self.assertEqual(controller.model['request']['library']['title'],'Named review')
            click('agentHistoryOptions');click('agentHistoryNewGroup')
            surface.fill(window,surface.item(view,'setting_name'),'Production')
            click('agentHistorySave')
            group=next(row for row in controller.model['groups'] if row['name']=='Production')
            click('agentRequestRename')
            choice=surface.item(view,'setting_group');choice.forceActiveFocus();QTest.keyClick(window,Qt.Key_Down);frame(window)
            surface.click(window,surface.item(view,'setting_pinned'));frame(window)
            click('agentHistorySave')
            saved=controller.model['request']['library']
            self.assertTrue(saved['pinned']);self.assertEqual(saved['group'],group['id'])
            surface.fill(window,surface.item(view,'agentRequestPrompt'),'Unsent native message')
            click('agentHistoryNew')
            other=controller.model['selected'];self.assertNotEqual(other,identity)
            controller.handle('select',identity);wait()
            self.assertEqual(controller.model['prompt'],'Unsent native message')
            controller.set_history(dict(controller.model['history'],project='one'));wait()
            old=next(row for row in controller.model['requests'] if row['title']=='Shot review')
            click('agentHistoryOpen_'+old['key'])
            self.assertEqual(controller.model['context']['project'],'one')
            click('agentHistoryNew')
            self.assertEqual(controller.model['context']['project'],'one')
            self.assertEqual(controller.model['context']['search_keys'],[])
            controller.set_history(dict(controller.model['history'],project='empty'));wait()
            controller.handle('select',dict(request_id=identity,project='empty'));wait()
            self.assertEqual(controller.model['prompt'],'Unsent native message')
            self.assertEqual(controller.model['context']['project'],'empty')
            controller.set_history(dict(controller.model['history'],project=''));wait()
            click('agentRequestRename');click('agentHistoryArchive')
            self.assertTrue(controller.model['request']['library']['archived'])
            click('agentRequestRename');click('agentHistoryArchive')
            self.assertFalse(controller.model['request']['library']['archived'])
            for width in (520,1200):
                window.resize(width,760);view.setWidth(width);frame(window)
                if width<940:
                    click('agentRequestHistoryToggle');self.assertIsNotNone(surface.item(view,'agentHistoryList'))
                    click('agentHistoryClose')
            self.assertFalse(surface.warnings,list(dict.fromkeys(surface.warnings)))
