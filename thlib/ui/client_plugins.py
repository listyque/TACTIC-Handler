"""Project-scoped desktop plugins; downloads run in workers, entry points on Qt."""
from __future__ import annotations

import hashlib
import importlib.util
from importlib.abc import MetaPathFinder
from importlib.machinery import SourceFileLoader
from pathlib import Path
import sys
from types import SimpleNamespace

from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer
from PySide6.QtWidgets import QFileDialog

from thlib import client_plugin_server as remote
from thlib.client_plugins import build_package, install_payload, installation_root
from thlib.environment import env_inst, env_mode, env_server, env_read_config, env_write_config


class _SourceOnlyLoader(SourceFileLoader):
    def get_code(self, fullname):
        return self.source_to_code(self.get_data(self.path), self.path)


class _PluginSources(MetaPathFinder):
    """Keep verified plugin sources independent of the host's bytecode policy."""
    def __init__(self, namespace, folder):
        self.namespace, self.folder = namespace, folder

    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith(self.namespace + '.'):
            return None
        relative = fullname[len(self.namespace) + 1:].split('.')
        candidate = self.folder.joinpath(*relative)
        package = candidate / '__init__.py'
        file = package if package.is_file() else candidate.with_suffix('.py')
        if not file.is_file():
            return None
        return importlib.util.spec_from_file_location(
            fullname, file, loader=_SourceOnlyLoader(fullname, str(file)),
            submodule_search_locations=[str(candidate)] if file == package else None,
        )


class ClientPluginsController(QObject):
    stateChanged = Signal()
    publishRequested = Signal(str)

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self._application = application
        self._rows = []
        self._busy = False
        self._error = self._message = ''
        self._admin = False
        self._closed = False
        self._generation = 0
        self._runs = {}
        self._last_archive = ''
        self._observed_context = None
        self._autostart_attempted = set()
        for signal in (application.project_changed, application.authentication_changed):
            signal.connect(self._session_changed)
        QTimer.singleShot(0, self._session_changed)

    def _context(self):
        return (env_server.get_server(), self._application.current_project_code,
                env_server.get_ticket(), env_server.get_user())

    @staticmethod
    def _server(context):
        from thlib.side.client.tactic_client_lib import TacticServerStub
        server = TacticServerStub(setup=False, protocol='xmlrpc')
        server.set_server(context[0])
        server.set_project(context[1])
        server.set_ticket(context[2])
        return server

    @staticmethod
    def _scope(context):
        return hashlib.sha256((context[0].rstrip('/') + '\n' + context[1]).encode()).hexdigest()

    def _disabled(self):
        values = env_read_config(filename='ui_client_plugins', unique_id='ui_main', long_abs_path=True) or {}
        return values, set(values.get(self._scope(self._context()), []))

    @Property('QVariantList', notify=stateChanged)
    def rows(self):
        values, disabled = self._disabled()
        scope = self._scope(self._context())
        autostart = values.get('autostart', {}).get(scope, [])
        return [{**row, 'enabled': row['code'] not in disabled,
                 'autostart': row['code'] in autostart,
                 'running': (scope, row['code']) in self._runs,
                 'runningVersion': self._runs.get((scope, row['code']), {}).get('version', '')} for row in self._rows]

    @Property('QVariantList', notify=stateChanged)
    def launchActions(self):
        return [dict(title=row['title'], icon='movie', command='client_plugin:' + row['code'],
                     enabled=not self._busy)
                for row in self.rows if row['enabled'] and row.get('allowed') and not row.get('error')]

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=stateChanged)
    def canPublish(self):
        return self._admin

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(str, notify=stateChanged)
    def message(self):
        return self._message

    @staticmethod
    def _catalog(context):
        from thlib import tactic_classes as tc
        from thlib.script_access import query_runner_access
        server = ClientPluginsController._server(context)
        access = tc.execute_procedure_serverside(query_runner_access, {'project_code': context[1]},
                                                project=context[1], server=server)
        denied = set(access['denied'])
        rows = remote.catalog(server)
        for row in rows:
            row['allowed'] = '*' not in denied and row.get('access_script', '') not in denied
        admin = tc.execute_procedure_serverside(remote.plugin_administrator, {'project_code': context[1]},
                                               project=context[1], server=server)
        return rows, bool(admin)

    def _session_changed(self, *_):
        if not self._closed and self._context() != self._observed_context:
            self.refresh()

    @Slot()
    def refresh(self, *_):
        if self._closed:
            return
        self._generation += 1
        self._rows = []
        self._admin = False
        self._busy = False
        self._error = self._message = ''
        context = self._context()
        self._observed_context = context
        if context[1] and context[2]:
            self._run('catalog', '', lambda: self._catalog(context))
        else:
            self.stateChanged.emit()

    @Slot(str, bool)
    def set_enabled(self, code, enabled):
        if self._busy or not any(row['code'] == code for row in self._rows):
            return
        try:
            values, disabled = self._disabled()
            disabled.discard(code) if enabled else disabled.add(code)
            values[self._scope(self._context())] = sorted(disabled)
            env_write_config(values, filename='ui_client_plugins', unique_id='ui_main', long_abs_path=True)
        except (OSError, ValueError) as error:
            self._error = self.tr(str(error))
        self.stateChanged.emit()

    @Slot(str, bool)
    def set_autostart(self, code, enabled):
        if self._busy or not any(row['code'] == code for row in self._rows):
            return
        try:
            values, _ = self._disabled()
            scopes = values.setdefault('autostart', {})
            scope = self._scope(self._context())
            codes = set(scopes.get(scope, []))
            codes.add(code) if enabled else codes.discard(code)
            scopes[scope] = sorted(codes)
            env_write_config(values, filename='ui_client_plugins', unique_id='ui_main', long_abs_path=True)
        except (OSError, ValueError) as error:
            self._error = self.tr(str(error))
        self.stateChanged.emit()

    def _autostart_next(self):
        if self._closed or self._busy or env_inst.ui_main is None:
            return
        scope = self._scope(self._context())
        for row in self.rows:
            key = scope, row['code']
            if (row['autostart'] and row['enabled'] and row.get('allowed')
                    and not row.get('error') and key not in self._autostart_attempted):
                self._autostart_attempted.add(key)
                if key not in self._runs:
                    self.open_plugin(row['code'])
                    return

    @Slot(str)
    def open_plugin(self, code):
        if self._busy or code in self._disabled()[1]:
            return
        context = self._context()
        key = self._scope(context), code
        root = installation_root(Path(env_mode.get_current_path()), context[0], context[1])
        running = key in self._runs
        def prepare():
            rows, admin = self._catalog(context)
            row = next((row for row in rows if row['code'] == code), None)
            if not row or row['error'] or not row['allowed']:
                raise PermissionError('This plugin is unavailable for your account')
            folder = None
            if not running:
                folder = install_payload(remote.download(self._server(context), row), row, root)
            return rows, admin, row, folder
        self._run('open', code, prepare)

    @Slot()
    def choose_publish(self):
        if not self._admin or self._busy:
            return
        path, _ = QFileDialog.getOpenFileName(None, self.tr('Publish client plugin'), self._last_archive,
                                             self.tr('Plugin ZIP files (*.zip)'))
        if path:
            self.publishRequested.emit(path)

    @Slot(str)
    def publish(self, path):
        if not self._admin or self._busy:
            return
        context = self._context()
        self._run('publish', '', lambda: remote.publish(self._server(context), context[1], Path(path)))

    @Slot(str)
    def build(self, version):
        if self._busy or not self._admin:
            return
        source = QFileDialog.getExistingDirectory(None, self.tr('Plugin source folder'))
        if not source:
            return
        output = QFileDialog.getExistingDirectory(None, self.tr('Release output folder'))
        if output:
            self._run('build', '', lambda: str(build_package(Path(source), version, Path(output))))

    def _run(self, kind, code, function):
        self._busy, self._error, self._message = True, '', ''
        generation, context = self._generation, self._context()
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(function)
        def done(value):
            if self._closed or generation != self._generation or context != self._context():
                return
            self._busy = False
            try:
                if kind == 'catalog':
                    self._rows, self._admin = value
                elif kind == 'build':
                    self._last_archive = value
                    self._message = self.tr('Plugin ZIP created: %1').replace('%1', value)
                elif kind == 'publish':
                    self.refresh()
                    self._message = self.tr('Published plugin version: %1').replace('%1', value['version'])
                elif kind == 'open':
                    self._rows, self._admin, row, folder = value
                    self._open(context, code, row, folder)
            except Exception as error:
                self._error = self.tr(str(error))
            if kind == 'open' and self._error:
                self._application.notify(self._error)
            self.stateChanged.emit()
            QTimer.singleShot(0, self._autostart_next)
        def failed(value):
            if not self._closed and generation == self._generation and context == self._context():
                self._busy = False
                self._error = self.tr(str(value.get('exception') or 'Client plugin operation failed')).replace(str(context[2]), '[redacted]')
                if kind == 'open':
                    self._application.notify(self._error)
                self.stateChanged.emit()
                QTimer.singleShot(0, self._autostart_next)
        worker.result.connect(done)
        worker.error.connect(failed)
        worker.start()

    def _open(self, context, code, row, folder):
        key = self._scope(context), code
        if key in self._runs:
            self._runs[key]['window'].showNormal()
            self._runs[key]['window'].requestActivate()
            self._message = self.tr('The running plugin keeps its version. Updates apply after closing it.')
            return
        namespace = '_th_plugin_' + key[0] + '_' + code + '_' + row['sha256']
        finder = _PluginSources(namespace, folder)
        sys.meta_path.insert(0, finder)
        spec = importlib.util.spec_from_file_location(
            namespace, folder / 'entry.py', loader=_SourceOnlyLoader(namespace, str(folder / 'entry.py')),
            submodule_search_locations=[str(folder)],
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[namespace] = module
        try:
            spec.loader.exec_module(module)
            window = module.open_plugin(SimpleNamespace(window=env_inst.ui_main, project=context[1]))
            if window is None or not callable(getattr(window, 'showNormal', None)):
                raise TypeError('Plugin entry point must return its native window')
        except Exception:
            sys.meta_path.remove(finder)
            for name in list(sys.modules):
                if name == namespace or name.startswith(namespace + '.'):
                    sys.modules.pop(name, None)
            raise
        self._runs[key] = {'window': window, 'version': row['version'], 'module': module}
        def released(*_):
            sys.meta_path.remove(finder)
            self._runs.pop(key, None)
            for name in list(sys.modules):
                if name == namespace or name.startswith(namespace + '.'):
                    sys.modules.pop(name, None)
            if not self._closed:
                self.stateChanged.emit()
        window.destroyed.connect(released)

    def shutdown(self):
        self._closed = True
        self._generation += 1
