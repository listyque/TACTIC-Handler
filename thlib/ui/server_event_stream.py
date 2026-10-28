"""Async Qt SSE transport; committed invalidations trigger one coalesced read."""
from __future__ import annotations

import codecs
import json
import time
import traceback
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkRequest

from .server_address import normalize_tactic_server_url


class ServerEventStream(QObject):
    batchReady = Signal(object)
    clockSample = Signal(object, float, float)
    failed = Signal(object)

    def __init__(self, server: str, payload: dict, proxy: dict, parent=None, batch_delay: int = 200):
        super().__init__(parent)
        self.url = normalize_tactic_server_url(server)
        self.batch_delay = batch_delay
        self.payload = dict(payload)
        self.manager = QNetworkAccessManager(self)
        if proxy.get('enabled'):
            address = urlsplit(proxy['server'] if '://' in proxy['server'] else 'http://' + proxy['server'])
            self.manager.setProxy(QNetworkProxy(QNetworkProxy.HttpProxy, address.hostname or '', address.port or 8080,
                                              proxy.get('login', ''), proxy.get('pass', '')))
        else:
            self.manager.setProxy(QNetworkProxy(QNetworkProxy.NoProxy))
        self.reply = self.fetch = None
        self.active = True
        self.buffer = ''
        self.decoder = codecs.getincrementaldecoder('utf-8')()
        self.event = ''
        self.data = []
        self.channels, self.types = set(), set()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self._fail(TimeoutError('Server update stream timed out.')))
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.timeout.connect(self._read_changes)

    def _post(self, path: str, values: dict):
        request = QNetworkRequest(QUrl(self.url + path))
        request.setRawHeader(b'Content-Type', b'application/json')
        request.setRawHeader(b'X-Tactic-Client', b'TACTIC Handler')
        request.setAttribute(QNetworkRequest.RedirectPolicyAttribute, QNetworkRequest.ManualRedirectPolicy)
        request.setTransferTimeout(30000)
        return self.manager.post(request, json.dumps(values).encode('utf-8'))

    def start(self):
        started = time.monotonic()
        self.reply = self._post('/admin/server-events', self.payload)
        self.reply.metaDataChanged.connect(lambda: self._clock_headers(started))
        self.reply.readyRead.connect(self._received)
        self.reply.finished.connect(self._finished)
        self.timer.start(30000)

    def _clock_headers(self, started):
        if self.active and self.reply is not None:
            sample = {
                'utcStarted': bytes(self.reply.rawHeader('X-Tactic-UTC-Started')).decode(),
                'utcEnded': bytes(self.reply.rawHeader('X-Tactic-UTC-Ended')).decode(),
            }
            self.clockSample.emit(sample, started, time.monotonic())

    def cancel(self):
        self.active = False
        self.timer.stop()
        self.debounce.stop()
        self.channels.clear()
        self.types.clear()
        for reply in (self.reply, self.fetch):
            if reply is not None:
                reply.abort()
                reply.deleteLater()
        self.reply = self.fetch = None

    def _fail(self, error, reply=None):
        if self.active:
            reply = reply if reply is not None else self.reply
            details = {'project': self.payload.get('project', ''),
                       'channels': self.payload.get('channels', []),
                       'error_code': getattr(error, 'code', ''),
                       'status': getattr(error, 'status', 0)}
            if reply is not None:
                # Never include the POST ticket, proxy credentials or URL user info.
                url = reply.url()
                details.update(endpoint=url.path(), host=url.host(), port=url.port(),
                               http_status=reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) or 0,
                               network_error=reply.error().name, network_message=reply.errorString())
            trace = ''.join(traceback.format_exception(error)) if error.__traceback__ else ''
            self.cancel()
            self.failed.emit({'exception': error, 'stacktrace': trace, 'details': details})

    @staticmethod
    def _error(data, status=0):
        error = ConnectionError(data.get('error') or f'Server update request failed (HTTP {status or "unavailable"}).')
        error.code = data.get('error_code', '')
        error.status = status
        return error

    def _received(self):
        if not self.active:
            return
        status = self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if status != 200:
            return
        if not bytes(self.reply.rawHeader('Content-Type')).startswith(b'text/event-stream'):
            self._fail(ValueError('Invalid server update stream.'))
            return
        self.timer.start(45000)
        try:
            self.buffer += self.decoder.decode(bytes(self.reply.readAll()))
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                line = line.rstrip('\r')
                if not line:
                    if self.data:
                        value = json.loads('\n'.join(self.data))
                        if self.event == 'error':
                            self._fail(self._error(value, value.get('status', 0)))
                            return
                        if self.event == 'updates':
                            self._deliver(value)
                        elif self.event == 'changes':
                            self.channels.update(value['channels'])
                            self.types.update(value['search_types'])
                            if self.fetch is None and not self.debounce.isActive():
                                self.debounce.start(self.batch_delay)
                    self.event, self.data = '', []
                elif line.startswith('event:'):
                    self.event = line[6:].strip()
                elif line.startswith('data:'):
                    self.data.append(line[5:].lstrip())
        except (ValueError, KeyError, UnicodeError) as error:
            self._fail(error)

    def _deliver(self, value: dict):
        for name, rows in [('message_after', value.get('messages', [])), ('activity_after', value.get('activity', []))]:
            times = [row.get('__event_timestamp__') or row.get('timestamp') for row in rows]
            if any(times):
                self.payload[name] = max(item for item in times if item)
        for name, field in [('cache_after', 'cacheCursor'), ('reaction_after', 'reactionCursor')]:
            if value.get(field):
                self.payload[name] = value[field]
        self.batchReady.emit(value)

    def _read_changes(self):
        if not self.active or self.fetch is not None or not self.channels:
            return
        values = dict(self.payload, channels=sorted(self.channels), invalidated_types=sorted(self.types), heartbeat=False)
        self.channels.clear()
        self.types.clear()
        started = time.monotonic()
        reply = self._post('/admin/server-updates', values)
        self.fetch = reply
        def finished():
            if not self.active or self.fetch is not reply:
                return
            self.fetch = None
            try:
                raw = bytes(reply.readAll())
                status = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) or 0
                if status != 200 or reply.error() != reply.NetworkError.NoError:
                    try:
                        data = json.loads(raw)
                    except ValueError:
                        data = {}
                    if status == 200:
                        data = dict(data, error=reply.errorString(), error_code='transport_error')
                    self._fail(self._error(data, status), reply)
                    return
                value = json.loads(raw)['result']
                value['__clientClockStartedMonotonic'] = started
                value['__clientClockReceivedMonotonic'] = time.monotonic()
                self._deliver(value)
                if self.channels:
                    self.debounce.start(self.batch_delay)
            except (ValueError, KeyError) as error:
                self._fail(error, reply)
            finally:
                reply.deleteLater()
        reply.finished.connect(finished)

    def _finished(self):
        if not self.active:
            return
        status = self.reply.attribute(QNetworkRequest.HttpStatusCodeAttribute) or 0
        try:
            data = json.loads(bytes(self.reply.readAll())) if status != 200 else {}
        except ValueError:
            data = {}
        if status == 200:
            data = {'error': 'Server update stream closed; reconnecting.', 'error_code': 'stream_closed'}
        self._fail(self._error(data, status))
