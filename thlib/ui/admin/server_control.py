"""Remote server worker settings using the existing administration draft owner."""
import time
from uuid import uuid4

from PySide6.QtCore import Property, QTimer, Signal, Slot

from .editor import AdminDocumentEditor


def server_control_request(configuration, action):
    setting = next(setting for group in configuration['groups'] for setting in group['settings']
                   if setting['path'] == 'services/process_count')
    result = dict(identity='server', revision=configuration['revision'], canWrite=True,
        document={'workers': setting['value'] or setting['default']},
        metadata={'runtime': configuration['runtime']})
    if action == 'list':
        result['catalog'] = [{'identity': 'server', 'title': 'Backend server'}]
    return result


class ServerControlEditor(AdminDocumentEditor):
    statusChanged = Signal()

    def __init__(self, application, parent=None):
        super().__init__(application, server_control_request, parent)
        self._restart_id = ''
        self._restart_instance = ''
        self._restart_deadline = 0
        self._notice = ''
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(lambda: self._request('runtime', request_id=self._restart_id))
        self.stateChanged.connect(self._restart_state)
        self.stateChanged.connect(self.statusChanged.emit)

    def _execute_request(self, arguments, project, original):
        import json
        from urllib.error import HTTPError
        from urllib.request import Request
        from thlib import tactic_classes as tc
        from ..server_address import normalize_tactic_server_url
        server = tc.server_start(project='admin')
        action = arguments['action']
        payload = {'ticket': server.login_ticket}
        suffix = ''
        if action == 'save':
            suffix = '/save'
            payload.update(changes={'services/process_count': arguments['document']['workers']}, revision=arguments['expected_revision'])
        elif action in ('restart', 'runtime'):
            suffix = '/' + action
            if action == 'restart':
                payload.update(revision=arguments['expected_revision'], instance_id=arguments['instance_id'], request_id=arguments['request_id'])
        url = normalize_tactic_server_url(server.get_server_name()) + '/admin/configuration' + suffix
        request = Request(url, json.dumps(payload).encode('utf-8'), {'Content-Type': 'application/json'})
        try:
            with server.transport.open(request, timeout=3 if action == 'runtime' else 10) as response:
                result = json.load(response)['result']
        except HTTPError as error:
            with error:
                message = json.load(error).get('error', 'Server request failed')
            if action not in ('restart', 'runtime'):
                raise RuntimeError(message) from error
            result = {'restart_id': arguments['request_id'], 'restart_error': message}
        if action in ('restart', 'runtime'):
            return dict(identity='server', revision=arguments['expected_revision'], canWrite=True,
                document=original, metadata={'runtime': result})
        return server_control_request(result, action)

    @Property(bool, notify=statusChanged)
    def restarting(self):
        return bool(self._restart_id)

    @Property(str, notify=statusChanged)
    def notice(self):
        return self._notice

    @Slot()
    def restart(self):
        if self.busy or self.dirty or self._restart_id or not self.canWrite:
            return
        runtime = self._metadata.get('runtime', {})
        if not runtime.get('available') or runtime.get('state') != 'running':
            return
        self._restart_id = str(uuid4())
        self._restart_instance = runtime['instance_id']
        self._restart_deadline = time.monotonic() + 90
        self._notice = ''
        self._request('restart', instance_id=self._restart_instance, request_id=self._restart_id)

    def _restart_state(self):
        if not self._restart_id or self.busy:
            return
        state = self._metadata.get('runtime', {})
        if state.get('restart_id') == self._restart_id and state.get('restart_error'):
            self._error = state['restart_error']
            self._restart_id = ''
        elif state.get('restart_id') == self._restart_id and state.get('instance_id') != self._restart_instance and state.get('state') == 'running':
            self._restart_id = ''
            self._notice = 'TACTIC Stream restarted'
        elif time.monotonic() >= self._restart_deadline:
            self._restart_id = ''
            self._error = 'The server has not returned yet. Reconnect and check its status.'
        else:
            self._error = ''
            self._timer.start()
            return
        self.stateChanged.emit()

    def reset(self, project=''):
        self._timer.stop()
        self._restart_id = ''
        self._notice = ''
        super().reset(project)

    @Slot()
    def discard(self):
        if self.busy or self.restarting:
            return
        self._write_uncertain = False
        super().discard()
        self.reload()

    def shutdown(self):
        self._timer.stop()
        self._restart_id = ''
        super().shutdown()
