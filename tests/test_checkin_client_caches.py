from __future__ import annotations

import concurrent.futures
import io
import os
from pathlib import Path
import tempfile
import textwrap
import unittest
import urllib.request
from unittest.mock import patch
from urllib.error import URLError

from thlib import proxy, tactic_query as tq


def procedure(value):
    return value


class ProcedureSourceCacheTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / 'procedures.py'
        self.source.write_text("def procedure(value):\n    return ('first', value)\n", encoding='utf-8')
        self.source_patch = patch.object(tq.inspect, 'getsourcefile', return_value=str(self.source))
        self.source_patch.start()
        self.addCleanup(self.source_patch.stop)

    def execute(self, value):
        code = tq.prepare_serverside_script(procedure, {'value': value},
                                           shrink=False, catch_traceback=False)['code']
        namespace = {}
        exec('def run():\n' + textwrap.indent(code, '    '), namespace)
        return namespace['run']()

    def test_same_source_parsed_once_with_fresh_arguments(self):
        with patch.object(tq.ast, 'parse', wraps=tq.ast.parse) as parse:
            self.assertEqual(self.execute(11), ('first', 11))
            self.assertEqual(self.execute(22), ('first', 22))
        self.assertEqual(parse.call_count, 1)

    def test_changed_source_with_identical_timestamp_and_size_is_used(self):
        before = self.source.stat()
        self.assertEqual(self.execute(11), ('first', 11))
        self.source.write_text("def procedure(value):\n    return ('fresh', value)\n", encoding='utf-8')
        os.utime(self.source, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(self.source.stat().st_size, before.st_size)
        self.assertEqual(self.execute(22), ('fresh', 22))
        self.source.write_text('def renamed(value):\n    return value\n', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'no longer exists'):
            self.execute(33)

    def test_bundled_source_is_parsed_once(self):
        self.source.rename(self.source.with_suffix('.source'))
        with patch.object(tq.ast, 'parse', wraps=tq.ast.parse) as parse:
            self.assertEqual(self.execute('one'), ('first', 'one'))
            self.assertEqual(self.execute('two'), ('first', 'two'))
        self.assertEqual(parse.call_count, 1)


class FakeOpener:
    def __init__(self):
        self.requests = []
        self.responses = []

    def open(self, request, data=None, timeout=None):
        self.requests.append((request, timeout))
        response = io.BytesIO(b'XML response')
        self.responses.append(response)
        return response


class TransportOpenerTests(unittest.TestCase):
    def setUp(self):
        global_opener = patch.object(urllib.request, '_opener', None)
        global_opener.start()
        self.addCleanup(global_opener.stop)
        configuration = patch.object(proxy.env_server, 'get_proxy', return_value=None)
        configuration.start()
        self.addCleanup(configuration.stop)
        timeout = patch.object(proxy.env_server, 'get_timeout', return_value=17)
        timeout.start()
        self.addCleanup(timeout.stop)
        parser = patch.object(proxy.UrllibTransport, 'parse_response', lambda self, response: response.read())
        parser.start()
        self.addCleanup(parser.stop)

    def request(self, transport, host='server.test'):
        return transport.request(host, '/tactic/default/Api/', b'RPC body')

    def test_opener_is_lazy_reused_and_responses_closed(self):
        opener = FakeOpener()
        with patch.object(proxy, 'build_opener', return_value=opener) as build, \
                patch('urllib.request.install_opener') as install:
            transport = proxy.UrllibTransport()
            self.assertEqual(build.call_count, 0)
            self.assertEqual(self.request(transport), b'XML response')
            self.assertEqual(self.request(transport), b'XML response')
            self.assertEqual(build.call_count, 1)
            install.assert_not_called()
        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(opener.requests[0][1], 17)
        self.assertTrue(all(response.closed for response in opener.responses))

    def test_sdk_preserves_https_and_switches_scheme_with_the_server(self):
        from thlib.side.client.tactic_client_lib.tactic_server_stub import TacticServerStub

        opener = FakeOpener()
        transport = proxy.UrllibTransport()
        client = TacticServerStub(setup=False)
        client.set_transport(transport)
        with patch.object(proxy, 'build_opener', return_value=opener):
            for server in ('https://server.test:443', 'http://other.test:8081'):
                client.set_server(server)
                self.assertEqual(client.server.ping('private-test-ticket'), b'XML response')
                request = opener.requests[-1][0]
                self.assertEqual(request.full_url, server + '/tactic/default/Api/')
                self.assertIn(b'private-test-ticket', request.data)
        self.assertTrue(all(response.closed for response in opener.responses))

    def test_proxy_auth_and_host_changes_rebuild_opener(self):
        openers = []
        handlers = []
        def build(*values):
            handlers.append(values)
            opener = FakeOpener()
            openers.append(opener)
            return opener
        with patch.object(proxy, 'build_opener', side_effect=build):
            transport = proxy.UrllibTransport()
            self.request(transport)
            transport.update_proxy(dict(server='proxy.test:8080', login='', **{'pass': '', 'enabled': True}))
            self.request(transport)
            self.request(transport)
            self.assertEqual(len(openers), 2)
            proxy_handler = next(handler for handler in handlers[-1] if isinstance(handler, proxy.ProxyHandler))
            self.assertEqual(proxy_handler.proxies['http'], 'http://proxy.test:8080')
            transport.disable_proxy()
            self.request(transport)
            transport.enable_proxy()
            self.request(transport)
            with patch.object(proxy, 'httpAuthPassword', 'changed-for-test'):
                self.request(transport)
                self.request(transport)
            self.request(transport, host='other.test')
        self.assertEqual(len(openers), 6)

    def test_proxy_without_auth_uses_configured_host(self):
        opener = FakeOpener()
        with patch.object(proxy, 'build_opener', return_value=opener) as build, \
                patch.object(proxy, 'useAuthOnProxy', False):
            transport = proxy.UrllibTransport()
            transport.update_proxy(dict(server='proxy.test:8080', enabled=True))
            self.request(transport)
            self.request(transport)
        self.assertEqual(build.call_count, 1)
        handler = next(value for value in build.call_args.args if isinstance(value, proxy.ProxyHandler))
        self.assertEqual(handler.proxies['http'], 'http://proxy.test:8080')
        self.assertIsNone(opener.requests[0][0].get_header('Proxy-authorization'))

    def test_authenticated_proxy_header_is_present_on_cached_requests(self):
        opener = FakeOpener()
        with patch.object(proxy, 'build_opener', return_value=opener) as build:
            transport = proxy.UrllibTransport()
            transport.update_proxy(dict(server='proxy.test:8080', login='test', **{'pass': 'value', 'enabled': True}))
            self.request(transport)
            self.request(transport)
        self.assertEqual(build.call_count, 1)
        self.assertEqual(opener.requests[0][0].get_header('Proxy-authorization'),
                         opener.requests[1][0].get_header('Proxy-authorization'))
        self.assertTrue(opener.requests[1][0].get_header('Proxy-authorization'))

    def test_separate_worker_transports_keep_their_openers(self):
        left, right = proxy.UrllibTransport(), proxy.UrllibTransport()
        with patch.object(proxy, 'build_opener', side_effect=lambda *args: FakeOpener()) as build:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as workers:
                result = list(workers.map(self.request, (left, right)))
        self.assertEqual(result, [b'XML response', b'XML response'])
        self.assertEqual(build.call_count, 2)
        self.assertIsNot(left._opener, right._opener)

    def test_failed_mutating_request_is_not_retried(self):
        opener = FakeOpener()
        with patch.object(proxy, 'build_opener', return_value=opener), \
                patch.object(opener, 'open', side_effect=URLError('disconnected')) as send:
            transport = proxy.UrllibTransport()
            with self.assertRaises(URLError):
                self.request(transport)
            self.assertEqual(send.call_count, 1)

    def test_response_closed_when_parsing_fails(self):
        opener = FakeOpener()
        with patch.object(proxy, 'build_opener', return_value=opener), \
                patch.object(proxy.UrllibTransport, 'parse_response', side_effect=ValueError('bad XML')):
            transport = proxy.UrllibTransport()
            with self.assertRaises(ValueError):
                self.request(transport)
        self.assertTrue(opener.responses[0].closed)

    def test_native_download_uses_its_transport(self):
        from thlib.side.client.tactic_client_lib.tactic_server_stub import TacticServerStub
        opener = FakeOpener()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(proxy, 'build_opener', return_value=opener), \
                patch('urllib.request.urlopen', side_effect=AssertionError('Global opener used')):
            client = TacticServerStub(protocol='xmlrpc', setup=False)
            client.set_transport(proxy.UrllibTransport())
            path = client.download('http://server.test/file.md', to_dir=directory)
            self.assertEqual(Path(path).read_bytes(), b'XML response')
        self.assertTrue(opener.responses[0].closed)

    def test_native_file_download_uses_configured_proxy_transport(self):
        from types import SimpleNamespace
        from thlib import tactic_classes as tc
        opener = FakeOpener()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(proxy, 'build_opener', return_value=opener), \
                patch('urllib.request.urlopen', side_effect=AssertionError('Global opener used')):
            target = str(Path(directory) / 'file.md')
            file_object = SimpleNamespace(prepare_repo=lambda path: target,
                                          get_full_web_path=lambda: 'http://server.test/file.md')
            self.assertEqual(tc.File.download_file(file_object), target)
            self.assertEqual(Path(target).read_bytes(), b'XML response')
        self.assertTrue(opener.responses[0].closed)


if __name__ == '__main__':
    unittest.main()
