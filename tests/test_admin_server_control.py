"""Real native worker settings input and the async administration boundary."""
from copy import deepcopy
from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch

from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from tests.test_agent_request import isolate_chat_settings
from tests import test_frame_script_tools as script_tools
QML = script_tools.QML
from tests.profile_ui_responsiveness import frame
from thlib.ui.configuration_server import ServerControlEditor
from thlib.ui.icon_font import qml_icon_bindings


class ServerControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_tools.ScriptToolsTests.setUpClass()

    def test_native_adapter_uses_authenticated_http_and_bounded_status_requests(self):
        import json
        import threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from thlib.proxy import UrllibTransport
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args): pass
            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                calls.append((self.path, data))
                result = dict(revision='r1', runtime={'available':True,'state':'running','web_workers':2},
                    groups=[{'settings':[{'path':'services/process_count','value':'2','default':'3'}]}])
                if self.path.endswith('/runtime'): result = {'available':True,'state':'running','web_workers':3}
                self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
                self.wfile.write(json.dumps({'result':result}).encode())
        http = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread = threading.Thread(target=http.serve_forever,daemon=True); thread.start()
        controller = ServerControlEditor(SimpleNamespace(can_manage_tools=True,is_stream_server=True,debug_log=None))
        try:
            with patch('thlib.environment.env_server.get_proxy',return_value={}): transport=UrllibTransport()
            server=SimpleNamespace(login_ticket='fixture-ticket',transport=transport,
                get_server_name=lambda:'http://127.0.0.1:'+str(http.server_port))
            with patch('thlib.tactic_classes.server_start',return_value=server), patch.object(transport,'open',wraps=transport.open) as opened:
                args=dict(action='load',expected_revision='r1')
                loaded=controller._execute_request(args,'one',{})
                self.assertEqual(loaded['document']['workers'],'2')
                controller._execute_request(dict(args,action='save',document={'workers':'3'}),'one',{'workers':'2'})
                self.assertEqual(calls[-1][1]['changes'],{'services/process_count':'3'})
                runtime=controller._execute_request(dict(args,action='runtime',request_id='one'),'one',{'workers':'3'})
                self.assertEqual(runtime['metadata']['runtime']['web_workers'],3)
                self.assertEqual(opened.call_args.kwargs['timeout'],3)
                self.assertTrue(all(data['ticket']=='fixture-ticket' for _,data in calls))
        finally:
            controller.shutdown(); http.shutdown(); thread.join(3); http.server_close()

    def test_save_confirm_restart_and_narrow_input(self):
        isolate_chat_settings(self)
        surface = script_tools.ScriptToolsTests(); surface.setUp(); self.addCleanup(surface.doCleanups)
        for name, value in qml_icon_bindings(QML.parents[2], surface.engine).items():
            surface.engine.rootContext().setContextProperty(name, value)
        controller = ServerControlEditor(SimpleNamespace(can_manage_tools=True, is_stream_server=True, debug_log=None))
        self.addCleanup(controller.shutdown)
        calls = []
        workers = '2'
        restart = ''
        instance = '11111111-1111-4111-8111-111111111111'
        def execute(_function, args, **_kwargs):
            nonlocal workers, restart, instance
            calls.append(deepcopy(args))
            if args['action'] == 'save': workers = args['document']['workers']
            if args['action'] == 'restart': restart = args['request_id']
            if args['action'] == 'runtime': instance = '22222222-2222-4222-8222-222222222222'
            result = dict(identity='server', revision='revision-'+workers, canWrite=True,
                document={'workers': workers}, metadata={'runtime': dict(available=True, state='running',
                    instance_id=instance, restart_id=restart, web_workers=int(workers))})
            if args['action'] == 'list': result['catalog'] = [{'identity': 'server', 'title': 'Server'}]
            return result
        def wait():
            deadline = time.monotonic()+8
            while (controller.busy or controller.restarting) and time.monotonic()<deadline: QTest.qWait(5)
            self.assertFalse(controller.busy or controller.restarting, controller.error)
        with patch.object(controller, '_execute_request', side_effect=lambda args, _project, _original: execute(None, args)):
            controller.activate('admin'); wait()
            view = surface.create(QML/'features/configuration/ServerControl.qml',
                dict(theme=surface.theme, controller=controller, width=800, height=650))
            window = QQuickWindow(); window.resize(800,650); surface.windows.append(window)
            view.setParentItem(window.contentItem()); window.show(); frame(window)
            surface.fill(window, surface.item(view, 'serverWorkerCount'), '3')
            self.assertTrue(controller.dirty)
            self.assertFalse(surface.item(view,'serverRestart').isEnabled())
            surface.click(window,surface.item(view,'serverWorkersSave')); wait(); frame(window)
            self.assertFalse(controller.dirty)
            self.assertEqual(sum(row['action']=='restart' for row in calls),0)
            surface.click(window,surface.item(view,'serverRestart')); frame(window)
            surface.click(window,surface.item(view,'serverRestartCancel')); frame(window)
            self.assertFalse(controller.restarting)
            surface.click(window,surface.item(view,'serverRestart')); frame(window)
            surface.click(window,surface.item(view,'serverRestartAccept')); wait(); frame(window)
            self.assertEqual(controller.notice,'TACTIC Stream restarted')
            self.assertEqual(sum(row['action']=='restart' for row in calls),1)
            window.resize(344,650); view.setWidth(344); frame(window)
            for name in ('serverWorkersSave','serverRestart'):
                item=surface.item(view,name)
                self.assertLessEqual(item.x()+item.width(),344)
            self.assertFalse(surface.warnings,surface.warnings)


if __name__ == '__main__':
    unittest.main()
