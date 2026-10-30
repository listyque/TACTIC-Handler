"""Plugin manager transport on the existing administration draft lifecycle."""
from pathlib import Path
from urllib.parse import quote

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtQml import QJSValue

from .editor import AdminDocumentEditor
from ..source_editor import SourceEditorService

COMMAND = 'tactic.ui.app.plugin_wdg.PluginManagerCmd'


def plugin_request(**arguments):
    from thlib import tactic_classes as tc
    server = tc.server_start(project=arguments['project_code'])
    return server.execute_cmd(COMMAND, args=arguments)['info']


class PluginsEditor(AdminDocumentEditor):
    downloadReady = Signal(str)
    operationCompleted = Signal(str)
    sessionReset = Signal()

    def __init__(self, application, parent=None):
        super().__init__(application, plugin_request, parent)
        self._source_editor = SourceEditorService(self)
        self._mutating = False
        self._download = ''
        self.downloadReady.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))

    @property
    def uncertain(self):
        return self.writeUncertain

    def reset(self, project: str = '') -> None:
        super().reset(project)
        self.sessionReset.emit()

    @Property(QObject, constant=True)
    def sourceEditor(self):
        return self._source_editor

    @Slot(str, 'QVariant')
    def set_field(self, name, value):
        if isinstance(value, QJSValue):
            value = value.toVariant()
        if name in ('resource_source', 'resource_palette'):
            if not self.busy and self.canWrite and self._document.get('resource'):
                self._document['resource']['source' if name == 'resource_source' else 'palette'] = value
                self.stateChanged.emit()
        elif name == 'file_content':
            if not self.busy and self.canWrite and self._document.get('file'):
                self._document['file']['content'] = value
                self.stateChanged.emit()
        else:
            super().set_field(name, value)

    @Slot(str, 'QVariantMap')
    def perform(self, action, values):
        if self.busy:
            return
        if (self.dirty or self.writeUncertain) and action not in ('save', 'discard', 'list'):
            self.fail(self.tr('Apply or discard unsaved changes first'))
            return
        self._mutating = action not in ('list', 'load', 'new', 'browse', 'open_file', 'open_resource')
        if action == 'create':
            values = dict(values, document=self.document)
        self._request(action, self.identity, **values)

    @Slot()
    def save(self):
        if self._metadata.get('new'):
            if not self.busy and not self.writeUncertain:
                self._mutating = True
                self._request('create', document=self.document)
        else:
            self._mutating = True
            super().save()

    @Slot()
    def discard(self):
        if self.writeUncertain or self._metadata.get('new'):
            if not self.busy:
                self._write_uncertain = False
                self._document = self._original = {}
                self._metadata = {}
                self._identity = ''
                self.reload()
        else:
            super().discard()

    def _execute_request(self, arguments, project, original):
        from thlib import server_cache, tactic_classes as tc
        from thlib.environment import env_server
        server = tc.server_start(project=project)
        upload_path = arguments.pop('upload_path', '')
        if upload_path:
            server.upload_file(upload_path)
            arguments['upload_file_name'] = Path(upload_path).name
        if arguments['action'] == 'save':
            arguments['changed_fields'] = [key for key in ('title', 'description')
                                           if arguments['document'].get(key) != original.get(key)]
        result = server.execute_cmd(COMMAND, args=arguments)['info']
        result.setdefault('metadata', {})['_completedAction'] = arguments['action']
        if arguments['action'] not in ('list', 'load', 'new', 'browse', 'open_file', 'open_resource'):
            server_cache.invalidate_domains(('reference', 'search', 'relations', 'tasks'), project)
        download = result.pop('download', None)
        if download:
            result['metadata']['downloadUrl'] = str(env_server.get_server()).rstrip('/') + '/assets/_cache/' + '/'.join(
                quote(part, safe='') for part in (server.login_ticket, download['directory'], download['filename']))
        return result

    def _document_loaded(self):
        self._mutating = False
        action = self._metadata.pop('_completedAction', '')
        changed = self._metadata.pop('changed', False)
        download = self._metadata.pop('downloadUrl', '')
        if download:
            self.downloadReady.emit(download)
        if changed:
            self.committed.emit()
        if action:
            self.operationCompleted.emit(action)

    def fail(self, error):
        if self._mutating:
            self._write_uncertain = True
            self._mutating = False
        super().fail(error)

    @Slot(QUrl, bool, bool)
    def upload(self, url, package, replace=False):
        if not url.isLocalFile():
            self.fail(self.tr('Select a local file'))
            return
        path = url.toLocalFile()
        folder = self.metadata.get('folder', '')
        values = dict(upload_path=path, folder=folder)
        if not package:
            values['path'] = self.document['file']['path'] if replace else '/'.join(part for part in (folder, Path(path).name) if part)
            values['confirmation'] = replace
        self.perform('install' if package else 'upload', values)
