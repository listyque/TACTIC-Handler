"""System Info through the shipped SDK and real XML/JSON HTTP transports."""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from xmlrpc.client import Fault, dumps, loads

from tests import test_system_info as fixtures
from thlib import proxy, tactic_classes as tc
from thlib.side.client.tactic_client_lib.rpc_json import CODEC, decode, encode


class SystemInfoTransportTests(unittest.TestCase):
    def setUp(self):
        remote = fixtures.Server()
        self.remote = remote
        self.sessions = []
        sessions = self.sessions

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                body = self.rfile.read(int(self.headers['Content-Length']))
                is_json = self.path == '/admin/rpc'
                if is_json:
                    request = json.loads(body)
                    method, args = request['method'], decode(request['args'])
                else:
                    args, method = loads(body)
                try:
                    if method != 'execute_class_method':
                        raise ValueError('Unexpected API method: ' + method)
                    auth, class_name, name, kwargs = args
                    sessions.append(auth)
                    if auth['ticket'] != 'fixture-ticket' or auth['project'] != 'one':
                        raise ValueError('Invalid session')
                    result = remote.execute_class_method(class_name, name, kwargs)
                    data = (json.dumps(dict(codec=CODEC, result=encode(result))).encode()
                            if is_json else dumps((result,), methodresponse=True, allow_none=True).encode())
                    status = 200
                except Exception as error:
                    data = (json.dumps(dict(error=str(error))).encode() if is_json
                            else dumps(Fault(403, str(error))).encode())
                    status = 403 if is_json else 200
                self.send_response(status)
                self.send_header('Content-Type', 'application/json' if is_json else 'text/xml')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)

    def close_server(self):
        self.http.shutdown()
        self.thread.join(3)
        self.http.server_close()

    def client(self, protocol):
        client = tc.TacticServerStub(protocol=protocol, setup=False)
        transport = proxy.UrllibTransport()
        transport.update_proxy({})
        client.set_transport(transport)
        client.set_server('http://127.0.0.1:' + str(self.http.server_port))
        client.set_project('one')
        client.set_ticket('fixture-ticket')
        return client

    def test_facts_balance_and_parallel_performance_use_real_sdk(self):
        for protocol in ('xmlrpc', 'json'):
            with self.subTest(protocol=protocol), patch.object(proxy.env_server, 'get_proxy', return_value={}):
                client = self.client(protocol)
                with patch.object(tc, 'server_start', return_value=client):
                    for kind in ('info', 'balance', 'performance'):
                        result = fixtures.SystemInfoController.load('one', 7, kind, plan={'iterations': 2})
                        self.assertNotIn('error', result, (protocol, kind, result))
                        self.assertEqual(result['generation'], 7)
                        if kind == 'info':
                            self.assertEqual(result['data']['sections'][0], fixtures.FACTS['sections'][0])
                        elif kind == 'balance':
                            self.assertEqual(len(result['data']['samples']), 11)
                        else:
                            self.assertEqual(result['data']['count'], 2)
                            self.assertEqual(result['data']['parallel'], 2)
        self.assertEqual(len(self.sessions), 32)
        self.assertEqual(sum(name == 'performance_probe' for name, _ in self.remote.log), 8)

    def test_kwargs_default_and_remote_denial_are_preserved(self):
        for protocol in ('xmlrpc', 'json'):
            with self.subTest(protocol=protocol), patch.object(proxy.env_server, 'get_proxy', return_value={}):
                client = self.client(protocol)
                self.assertIn('pid', client.execute_class_method(fixtures.CLASS, 'connection_probe'))
                values = {'action': 'script', 'values': {'path': 'tests/probe'}}
                client.execute_class_method(fixtures.CLASS, 'run_test', values)
                self.assertEqual(self.remote.log[-1], ('run_test', values))
                self.remote.error = 'System Info requires administrator access'
                with self.assertRaisesRegex(Fault, 'requires administrator access'):
                    client.execute_class_method(fixtures.CLASS, 'get_info')
                with patch.object(tc, 'server_start', return_value=client):
                    result = fixtures.SystemInfoController.load('one', 8)
                self.assertIn('requires administrator access', result['error'])
                self.remote.error = ''


if __name__ == '__main__':
    unittest.main()
