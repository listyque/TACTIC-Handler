"""Legacy System Info facts and explicit tests through the authenticated API."""
from PySide6.QtCore import QObject, Property, Signal, Slot, qVersion
from PySide6.QtGui import QGuiApplication
from threading import Event

CLASS = 'tactic.ui.app.system_info_wdg.SystemInfoWdg'


class SystemInfoController(QObject):
    changed = Signal()
    navigationCleared = Signal(str)

    def __init__(self, application, pool):
        super().__init__(application)
        self.application, self.pool = application, pool
        self._generation = 0
        self._worker = None
        self._cancel = Event()
        self._model = dict(busy=False, pending='', error='', sections=[], results={})
        application.authentication_changed.connect(self.reset)
        application.signing_out.connect(self.reset)
        application.project_changed.connect(lambda *_: self.reset())
        application.window_model.windowVisibilityChanged.connect(self.visibility)
        application._registry.register('show_system_info', self.open)

    @Property('QVariantMap', notify=changed)
    def model(self):
        return self._model

    @Slot()
    def open(self):
        if not self.application.can_administer:
            return
        self.application.window_model.show_window('system_info')

    @Slot(str, bool)
    def visibility(self, code, visible):
        if code == 'system_info':
            if visible:
                self.refresh()
            else:
                self.reset()

    @Slot()
    def reset(self):
        self._generation += 1
        self._cancel.set()
        if self._worker:
            self._worker.cancel()
            self._worker = None
        self._model = dict(busy=False, pending='', error='', sections=[], results={})
        self.application.window_model.close_window('system_info')
        self.changed.emit()

    @Slot()
    def refresh(self):
        self.request('info')

    def request(self, kind, plan=None):
        if self._model['busy'] or not self.application.can_administer:
            return
        self._generation += 1
        generation = self._generation
        project = self.application.current_project_code or 'admin'
        self._cancel = Event()
        self._model.update(busy=True, pending=kind, error='')
        if self.pool.is_stopped:
            self.pool.start()
        values = dict(sender=self._model.get('sender', ''), recipients=self._model.get('recipients', ''),
                      path=self._model.get('scriptPath', ''), directories=self._model.get('directories', {}))
        worker = self.pool.add_task(self.load, project, generation, kind, values, plan or {}, self._cancel)
        if worker is None:
            self._model.update(busy=False, error=self.tr('Server worker pool is unavailable'))
        else:
            self._worker = worker
            worker.result.connect(self.done)
            worker.start()
        self.changed.emit()

    @staticmethod
    def load(project, generation, kind='info', values=None, plan=None, cancelled=None):
        from thlib import tactic_classes as tc
        from thlib.update_functions import current_version, version_text
        import platform
        import sys
        try:
            server = tc.server_start(project=project)
            def call(method, **kwargs):
                if cancelled and cancelled.is_set():
                    raise RuntimeError('Test cancelled')
                return server.execute_class_method(CLASS, method, kwargs)
            if kind == 'info':
                result = call('get_info')
                result['sections'].append(dict(title='TACTIC Handler', fields=[
                    ['Version', version_text(current_version())],
                    ['OS', platform.platform()], ['Python', sys.version], ['Qt', qVersion()],
                ]))
            elif kind == 'balance':
                samples = []
                for _ in range(50):
                    samples.append(call('connection_probe'))
                    if len(samples) >= 11 and len({(row['node'], row['pid'], row['port']) for row in samples}) == 1:
                        break
                result = dict(samples=samples)
            elif kind == 'performance':
                from concurrent.futures import ThreadPoolExecutor
                from time import perf_counter
                from thlib import proxy
                count = max(1, min(256, int((plan or {}).get('iterations', 1))))
                started = perf_counter()
                for _ in range(count):
                    call('performance_probe')
                sequential = (perf_counter() - started) * 1000
                def probe(_):
                    if cancelled and cancelled.is_set():
                        return None
                    client = tc.TacticServerStub(protocol=server.protocol, setup=False)
                    transport = proxy.UrllibTransport()
                    transport.update_proxy(server.transport.proxy)
                    client.set_transport(transport)
                    client.set_server(server.get_server())
                    client.set_project(project)
                    client.set_ticket(server.login_ticket)
                    try:
                        return client.execute_class_method(CLASS, 'performance_probe', {})
                    except Exception:
                        if cancelled:
                            cancelled.set()
                        raise
                started = perf_counter()
                with ThreadPoolExecutor(max_workers=min(8,count)) as executor:
                    list(executor.map(probe, range(count)))
                result = dict(sequentialMs=sequential, parallelMs=(perf_counter()-started)*1000,
                              count=count, parallel=min(8,count))
            elif kind == 'handoff':
                import os
                from pathlib import Path
                paths = (values or {}).get('directories', {}).get('win32' if os.name == 'nt' else 'linux', {})
                result = dict(paths=[])
                for name in ('client_repo_dir', 'client_handoff_dir'):
                    configured = paths.get(name) or ''
                    entries = configured.values() if isinstance(configured, dict) else [configured]
                    for path in entries:
                        result['paths'].append(dict(path=path or name,
                            available=bool(path) and Path(path).is_dir() and os.access(path, os.R_OK)))
            else:
                payload = {key: values[key] for key in ('sender','recipients')} if kind == 'email' else \
                    {'path': values['path']} if kind == 'script' else {}
                result = call('run_test', action=kind, values=payload)
            return dict(generation=generation, kind=kind, data=result)
        except Exception as error:
            # Remote failures are data at the worker boundary, never GUI exceptions.
            return dict(generation=generation, kind=kind, error=str(error))

    @Slot(object)
    def done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self._generation:
            return
        self._worker = None
        kind = result.get('kind', 'info')
        self._model.update(busy=False, pending='')
        if kind == 'info':
            self._model.update(error=result.get('error', ''), sections=[])
            if 'data' in result:
                self._model.update(result['data'])
                if not self._model.get('loaded'):
                    self._model['sender'] = self._model['recipients'] = result['data'].get('mailFrom', '')
                self._model['loaded'] = True
        else:
            self._model.setdefault('results', {})[kind] = dict(error=result['error']) if 'error' in result else result['data']
            if kind == 'clear_sidebar' and 'error' not in result:
                self.navigationCleared.emit(self._model.get('project') or self.application.current_project_code)
        self.changed.emit()

    @Slot('QVariantMap')
    def handle(self, action):
        if self._model['busy']:
            return
        kind = action.get('type')
        if kind == 'field' and action.get('field') in ('sender','recipients','scriptPath','includeInternal'):
            self._model[action['field']] = action.get('value', '')
        elif kind == 'refresh':
            self.refresh()
        elif kind == 'openLink':
            self.open_link(action.get('url', ''))
        elif kind == 'test':
            name = action.get('name')
            if name == 'links':
                links = self._model.get('internalLinks' if self._model.get('includeInternal') else 'links', [])
                opened = sum(bool(self.open_link(link['url'])) for link in links)
                self._model.setdefault('results', {})['links'] = dict(opened=opened,total=len(links),blocked=opened<len(links))
            else:
                self.request(name, action.get('plan'))
        self.changed.emit()

    def open_link(self, url):
        from urllib.parse import urljoin
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        allowed = {row['url'] for row in self._model.get('internalLinks', []) + self._model.get('links', [])}
        if url not in allowed or not url.startswith('/projects/') or any(c in url for c in '\r\n\0'):
            return False
        return QDesktopServices.openUrl(QUrl(urljoin(self.application.server_url, url)))

    @Slot(str)
    def copy(self, report):
        QGuiApplication.clipboard().setText(report)

    def shutdown(self):
        self.reset()
