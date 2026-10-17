"""Native TACTIC ProjectCreateWdg workflow for the standalone application."""

from pathlib import Path
import re
from urllib.parse import quote

from PySide6.QtCore import QObject, Property, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices


def project_identifier(value: str) -> str:
    """Match spt.convert_to_alpha_numeric (not a transliteration scheme)."""
    value = re.sub(r'''[?.!@#$%^&*()'",;+=]''', '', value)
    return re.sub(r'[\\_-]+', '_', value.replace(' ', '_').lower())


def creation_command(values: dict) -> tuple[str, dict]:
    title = str(values.get('title') or '').strip()
    code = str(values.get('code') or '').strip()
    if not title or len(title) > 100:
        raise ValueError('Project title is required and cannot exceed 100 characters')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,29}', code):
        raise ValueError('Project code must use letters, numbers and underscores, must not start with a number, and cannot exceed 30 characters')
    source = str(values.get('source') or '')
    if not source:
        raise ValueError('Select a template or an empty project')
    options = {
        'project_code': code, 'project_title': title,
        'project_theme': str(values.get('theme') or ''),
    }
    if source != '_empty':
        template, separator, path = source.partition('|')
        options.update(template_code=template, force_database=True)
        if separator:
            options['path'] = path
        return 'tactic.command.ProjectTemplateInstallerCmd', options
    namespace = str(values.get('namespace') or '').strip()
    if namespace in ('sthpw', 'prod'):
        raise ValueError('The sthpw and prod namespaces are reserved')
    options.update(
        project_type=namespace or code,
        is_template=bool(values.get('isTemplate')),
        is_main_project=bool(values.get('isMainProject')),
    )
    return 'tactic.command.CreateProjectCmd', options


class ProjectCreationController(QObject):
    stateChanged = Signal()
    sessionStarted = Signal()
    completed = Signal()

    def __init__(self, application, parent=None) -> None:
        super().__init__(parent)
        self._application = application
        self._worker = None
        self._generation = 0
        self._operation = ''
        self._busy = False
        self._error = ''
        self._catalog = {}
        self._draft = {}
        self._step = 0
        self._created_code = ''
        self._reset_draft()

    def _reset_draft(self) -> None:
        self._draft = {
            'title': '', 'code': '', 'description': '', 'category': '',
            'source': '_empty', 'namespace': '',
            'theme': '', 'isTemplate': False,
            'isMainProject': bool(self._catalog.get('isMainProject')),
            'previewPath': '',
        }
        self._step = 0
        self._created_code = ''
        self._uncertain = False
        self._error = ''

    @Slot()
    def begin_session(self) -> None:
        if self._busy:
            return
        self._catalog = {}
        self._reset_draft()
        self.sessionStarted.emit()
        self.reload_catalog()

    @Slot()
    def reload_catalog(self) -> None:
        self._start(self._load_catalog, (), 'catalog')

    @staticmethod
    def _load_catalog() -> dict:
        from thlib import tactic_classes as tc, tactic_query as tq
        from thlib.environment import env_server
        catalog = tc.execute_procedure_serverside(tq.get_project_creation_catalog, {})
        base = QUrl.fromUserInput(str(env_server.get_server()))
        for row in catalog.get('themes', []):
            row['preview'] = base.resolved(QUrl(row['preview'])).toString()
        return catalog

    @Slot(str, bool)
    def window_visibility_changed(self, window_id: str, visible: bool) -> None:
        if window_id == 'project_wizard':
            if visible:
                self.begin_session()
            elif self._busy and self._operation == 'catalog':
                self.shutdown()
        elif window_id == 'project_templates' and visible:
            self.reload_catalog()

    @Slot(str, 'QVariant')
    def set_value(self, key: str, value) -> None:
        if self._busy or self._created_code or self._uncertain or key not in self._draft:
            return
        if key == 'previewPath':
            if isinstance(value, QUrl):
                value = value.toLocalFile() or value.toString()
            else:
                url = QUrl(str(value or ''))
                value = url.toLocalFile() if url.isLocalFile() else str(value or '')
        self._draft[key] = value
        if key == 'title' and len(str(value)) <= 100:
            self._draft['code'] = project_identifier(str(value))[:30]
        self._error = ''
        self.stateChanged.emit()

    @Slot()
    def next_step(self) -> None:
        if self._busy or self._step >= 3:
            return
        self._draft['code'] = project_identifier(str(self._draft['code']))
        try:
            creation_command(self._draft)
            if self._draft['code'] in self._catalog.get('projectCodes', []):
                raise ValueError('A project with this code already exists, including retired projects')
        except ValueError as error:
            self._error = self.tr(str(error))
            self.stateChanged.emit()
            return
        self._step += 1
        self._error = ''
        self.stateChanged.emit()

    @Slot()
    def previous_step(self) -> None:
        self.select_step(max(0, self._step - 1))

    @Slot(int)
    def select_step(self, step: int) -> None:
        if self._busy or self._created_code or not 0 <= step < self._step:
            return
        self._step = step
        self._error = ''
        self.stateChanged.emit()

    @Slot()
    def submit(self) -> None:
        if self._busy or self._uncertain or self._step != 3:
            return
        if self._created_code:
            self._start(self._load_created_project, (), 'finish')
            return
        try:
            command, options = creation_command(self._draft)
            if not any(row['value'] == self._draft['source'] for row in self.templates):
                raise ValueError('Select a template or an empty project')
        except ValueError as error:
            self._error = self.tr(str(error))
            self.stateChanged.emit()
            return
        self._start(self._create, (
            command, options, str(self._draft['previewPath']),
        ), 'create')

    @staticmethod
    def _create(command: str, options: dict, image: str) -> str:
        from thlib import tactic_classes as tc
        server = tc.server_start(project='admin')
        # Both native creation branches own their database/schema side effects.
        # Never retry this mutation automatically: it can partially commit.
        if image:
            if not Path(image).is_file():
                raise ValueError('The selected preview file does not exist')
            server.upload_file(image)
            result = server.execute_cmd('tactic.command.CopyFileToAssetTempCmd', args={
                'filename': Path(image).name,
                'ticket': server.get_transaction_ticket(),
            })
            path = result['info'].get('lib_path')
            if not path:
                raise ValueError('TACTIC could not prepare the project preview')
            options = {**options, 'project_image_path': path}
        server.execute_cmd(command, args=options)
        return options['project_code']

    def _load_created_project(self) -> dict:
        projects = self._application._load_projects(force=True)
        project = next(item for item in projects if item.get_code() == self._created_code)
        values = {key: str(self._draft[key]).strip() for key in ('description', 'category')}
        changed = {
            key: value for key, value in values.items()
            if str(project.get_info().get(key) or '') != value
        }
        if changed:
            # Idempotent metadata updates override copied template values.
            # Opening retries never repeat the native creation command.
            for key, value in changed.items():
                project.set_value(key, value)
            project.commit()
        prepared = self._application._prepare_project_selection(
            self._created_code, project.get_title(),
        )
        return {'projects': projects, 'prepared': prepared}

    def _start(self, function, arguments: tuple, operation: str) -> None:
        if self._busy:
            return
        from thlib.environment import env_inst
        self._generation += 1
        worker = env_inst.server_pool.add_task(function, *arguments)
        if worker is None:
            self._error = self.tr('Project worker pool is unavailable')
            self.stateChanged.emit()
            return
        self._worker = worker
        self._operation = operation
        self._busy = True
        self._error = ''
        worker.add_result_data(self._generation)
        worker.result.connect(self._result, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(self._failed, Qt.ConnectionType.QueuedConnection)
        self.stateChanged.emit()
        worker.start()

    @Slot(object)
    def _result(self, envelope) -> None:
        result, generation = envelope
        if generation != self._generation:
            return
        operation = self._operation
        self._worker = None
        self._busy = False
        if operation == 'catalog':
            self._catalog = dict(result)
            if self._uncertain:
                if self._draft['code'] in self._catalog.get('projectCodes', []):
                    self._created_code = self._draft['code']
                self._uncertain = False
            if not self._draft['title']:
                self._draft['isMainProject'] = bool(result.get('isMainProject'))
            themes = [row['value'] for row in result.get('themes', [])]
            if self._draft['theme'] not in themes:
                self._draft['theme'] = ''
        elif operation == 'create':
            self._created_code = result
            self._start(self._load_created_project, (), 'finish')
        elif operation == 'finish':
            self._application.project_model.replace(result['projects'])
            prepared = result['prepared']
            if prepared:
                self._application._apply_selected_project(*prepared)
            self._application.notify(self.tr('Project created') + ': ' + self._created_code)
            self.completed.emit()
        elif operation == 'download':
            QDesktopServices.openUrl(QUrl(result))
        elif operation == 'export':
            self._application.notify(self.tr('Template archive created'))
            if self.ready:
                self.reload_catalog()
        else:
            self.reload_catalog()
        self.stateChanged.emit()

    @Slot(object)
    def _failed(self, error) -> None:
        if self._worker is None or self.sender() is not self._worker:
            return
        worker = self._worker
        if self._operation == 'create':
            self._uncertain = True
        self._worker = None
        self._busy = False
        payload = error[0] if isinstance(error, (tuple, list)) else error
        message = str(payload.get('exception') or payload.get('message') or payload) if isinstance(payload, dict) else str(payload)
        self._error = message
        if self._created_code:
            self._error = self.tr('Project created. Retry opening it; creation will not be repeated.') + '\n' + message
        # Generic error-dialog retries bypass controller state and can repeat
        # a partially committed creation. Retry through the wizard instead.
        worker.cancel()
        self._application._report_error_payload(payload, 'server/project_creation')
        self.stateChanged.emit()

    @Slot(str, 'QVariant')
    def template_action(self, action: str, value) -> None:
        if action == 'install':
            url = value if isinstance(value, QUrl) else QUrl(str(value))
            path = url.toLocalFile() if url.isLocalFile() else str(value)
            if not path.lower().endswith('.zip'):
                self._error = self.tr('A template file must be a ZIP archive')
                self.stateChanged.emit()
                return
            self._start(self._install_template, (path,), 'install')
            return
        if action not in ('delete', 'download'):
            return
        rows = self._catalog.get('installedTemplates', [])
        row = next((row for row in rows if row.get('code', row.get('value')) == str(value)), None)
        if row is not None:
            self._start(self._template_command, (action, dict(row)), action)

    @Slot(str)
    def export_project(self, project_code: str) -> None:
        from thlib.environment import env_inst

        project = (env_inst.projects or {}).get(project_code)
        if project is None or project.is_builtin():
            self._error = self.tr('Select an editable project first')
            self.stateChanged.emit()
            return
        self._start(self._template_command, ('export', {'value': project_code}), 'export')

    @staticmethod
    def _install_template(path: str) -> None:
        from thlib import tactic_classes as tc
        server = tc.server_start(project='admin')
        server.upload_file(path)
        server.execute_cmd('tactic.ui.app.ProjectTemplateInstallCmd', args={'paths': [path]})

    @staticmethod
    def _template_command(action: str, row: dict):
        from thlib import tactic_classes as tc
        from thlib.environment import env_server
        server = tc.server_start(project='admin')
        if action == 'export':
            return server.execute_cmd('tactic.command.ProjectTemplateCreatorCmd', args={
                'project_code': row['value'],
            })
        if action == 'delete':
            return server.execute_cmd('tactic.ui.app.ProjectTemplateDeleteCmd', args={
                'template': row['code'],
            })
        result = server.execute_cmd('tactic.ui.app.ProjectTemplateDownloadCmd', args={
            'template_dir': row['path'],
        })
        filename = result['info'].get('filename')
        if not filename:
            raise ValueError('No template archive is available for download')
        return str(env_server.get_server()).rstrip('/') + '/assets/_cache/' + quote(
            server.get_transaction_ticket(), safe=''
        ) + '/' + quote(filename, safe='')

    def shutdown(self) -> None:
        self._generation += 1
        if self._worker is not None:
            self._worker.result.disconnect(self._result)
            self._worker.error.disconnect(self._failed)
            self._worker.cancel()
            self._worker = None
        self._busy = False
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def ready(self) -> bool:
        return bool(self._catalog)

    @Property(str, notify=stateChanged)
    def previewUrl(self) -> str:
        path = self._draft.get('previewPath')
        return QUrl.fromLocalFile(path).toString() if path else ''

    @Property('QVariantMap', notify=stateChanged)
    def draft(self) -> dict:
        return dict(self._draft)

    @Property('QVariantMap', notify=stateChanged)
    def catalog(self) -> dict:
        return dict(self._catalog)

    @Property('QVariantList', notify=stateChanged)
    def templates(self) -> list:
        rows = [{'value': '_empty', 'label': self.tr('Empty project'), 'kind': 'empty'}]
        for template in self._catalog.get('templates', []):
            row = dict(template)
            if row['kind'] == 'builtin':
                row['label'] += ' (' + self.tr('Built-in') + ')'
            elif row['kind'] == 'file':
                row['label'] += ' (' + self.tr('From file') + ')'
            rows.append(row)
        return rows

    @Property('QVariantList', notify=stateChanged)
    def themes(self) -> list:
        return [{'value': '', 'label': self.tr('No theme')}, *self._catalog.get('themes', [])]

    @Property(int, notify=stateChanged)
    def step(self) -> int:
        return self._step

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(bool, notify=stateChanged)
    def uncertain(self) -> bool:
        return self._uncertain

    @Property(str, notify=stateChanged)
    def createdCode(self) -> str:
        return self._created_code
