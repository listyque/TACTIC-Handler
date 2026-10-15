from __future__ import annotations

import json
import os
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_CONTROLS_STYLE', 'Basic')
from PySide6.QtGui import QGuiApplication
from thlib.ui.server_event_stream import ServerEventStream


class ServerEventStreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QGuiApplication.instance() or QGuiApplication([])

    def wait(self, condition, timeout=5):
        deadline = time.monotonic() + timeout
        while not condition() and time.monotonic() < deadline:
            self.application.processEvents()
            time.sleep(.005)
        self.assertTrue(condition(), 'Async Qt condition timed out')

    def test_real_stream_coalescing_utf8_and_shutdown(self):
        frames, calls = queue.Queue(), []
        release = threading.Event()
        batch = dict(messages=[], activity=[], reactions=[], cacheChanges=[], cacheRetired=[], presence=[], cacheCursor='')
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def log_message(self, *_):
                pass
            def do_POST(self):
                values = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                calls.append((self.path, values))
                if self.path == '/admin/server-events':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.end_headers()
                    self.wfile.write(('event: updates\r\ndata: ' + json.dumps(dict(batch, text='Привет'), ensure_ascii=False) + '\r\n\r\n').encode())
                    self.wfile.flush()
                    while True:
                        frame = frames.get()
                        if frame is None:
                            return
                        try:
                            self.wfile.write(frame)
                            self.wfile.flush()
                        except (BrokenPipeError, ConnectionResetError):
                            return
                else:
                    release.wait(5)
                    body = json.dumps(dict(result=batch)).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        stream = ServerEventStream('http://127.0.0.1:' + str(server.server_port), dict(ticket='private', project='one'), {}, batch_delay=500)
        batches, errors = [], []
        stream.batchReady.connect(batches.append)
        stream.failed.connect(errors.append)
        try:
            stream.start()
            self.wait(lambda: len(batches) == 1)
            self.assertEqual(batches[0]['text'], 'Привет')
            for index in range(100):
                frames.put(('event: changes\ndata: ' + json.dumps(dict(channels=['cache'], search_types=['cg/assets' if index % 2 else 'cg/scenes'])) + '\n\n').encode())
            self.wait(lambda: len(calls) == 2)
            self.assertEqual(stream.debounce.interval(), 500)
            self.assertEqual(calls[1][1]['invalidated_types'], ['cg/assets', 'cg/scenes'])
            self.assertFalse(calls[1][1]['heartbeat'])
            release.set()
            self.wait(lambda: len(batches) == 2)
            self.assertEqual(len(calls), 2)
            self.assertFalse(errors)
            frames.put(b'event: error\ndata: {"error":"Session ended","error_code":"authentication_failed","status":403}\n\n')
            self.wait(lambda: len(errors) == 1)
            self.assertEqual(errors[0]['exception'].code, 'authentication_failed')
            self.assertFalse(stream.active)
            self.assertIsNone(stream.reply)
            self.assertIsNone(stream.fetch)
        finally:
            stream.cancel()
            release.set()
            frames.put(None)
            server.shutdown()
            server.server_close()
            thread.join(3)
            self.assertFalse(thread.is_alive())

    def test_closed_http_200_and_http_errors_keep_diagnostics_without_tickets(self):
        for status, body, content_type, code in (
            (200, b': keepalive\n\n', 'text/event-stream', 'stream_closed'),
            (503, b'upstream unavailable', 'text/plain', ''),
            (403, b'{"error":"Session ended","error_code":"authentication_failed"}', 'application/json', 'authentication_failed'),
            (200, b'event: updates\ndata: broken-json\n\n', 'text/event-stream', ''),
        ):
            with self.subTest(status=status, code=code, body=body):
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self, *_): pass
                    def do_POST(self):
                        self.rfile.read(int(self.headers['Content-Length']))
                        self.send_response(status)
                        self.send_header('Content-Type', content_type)
                        self.send_header('Content-Length', str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                stream = ServerEventStream('http://127.0.0.1:'+str(server.server_port),
                    dict(ticket='never-log-this-ticket', project='demo', channels=['cache']), {})
                errors = []
                stream.failed.connect(errors.append)
                try:
                    stream.start()
                    self.wait(lambda: bool(errors))
                    self.assertEqual(len(errors), 1)
                    self.assertEqual(getattr(errors[0]['exception'], 'code', ''), code)
                    details = errors[0]['details']
                    self.assertEqual(details['endpoint'], '/admin/server-events')
                    self.assertEqual(details['http_status'], status)
                    self.assertEqual(details['project'], 'demo')
                    self.assertIn('network_error', details)
                    self.assertNotIn('never-log-this-ticket', str(errors))
                    if b'broken-json' in body:
                        self.assertIn('JSONDecodeError', errors[0]['stacktrace'])
                    if status == 503:
                        self.assertIn('503', str(errors[0]['exception']))
                    self.assertFalse(stream.active)
                    self.assertIsNone(stream.reply)
                finally:
                    stream.cancel()
                    server.shutdown();server.server_close();thread.join(3)

    def test_failed_batch_records_its_endpoint_and_network_error(self):
        for truncated in (False, True):
            with self.subTest(truncated=truncated):
                class Handler(BaseHTTPRequestHandler):
                    def log_message(self, *_): pass
                    def do_POST(self):
                        self.rfile.read(int(self.headers['Content-Length']))
                        body = b'{"result":' if truncated else b'upstream unavailable'
                        self.send_response(200 if truncated else 503)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Content-Length', str(len(body)+(100 if truncated else 0)))
                        self.end_headers()
                        self.wfile.write(body)
                server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
                thread = threading.Thread(target=server.serve_forever)
                thread.start()
                stream = ServerEventStream('http://127.0.0.1:'+str(server.server_port), dict(ticket='private', project='demo'), {})
                errors = []
                stream.failed.connect(errors.append)
                try:
                    stream.channels.add('cache')
                    stream._read_changes()
                    self.wait(lambda: bool(errors))
                    self.assertEqual(len(errors), 1)
                    self.assertEqual(errors[0]['details']['endpoint'], '/admin/server-updates')
                    self.assertEqual(errors[0]['details']['http_status'], 200 if truncated else 503)
                    if truncated:
                        self.assertEqual(errors[0]['exception'].code, 'transport_error')
                        self.assertNotEqual(errors[0]['details']['network_error'], 'NoError')
                finally:
                    stream.cancel();server.shutdown();server.server_close();thread.join(3)


if __name__ == '__main__':
    unittest.main()
