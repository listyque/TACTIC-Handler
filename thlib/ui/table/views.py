"""Native saved-view manager; XML and revisions stay with the TACTIC command."""
from copy import deepcopy
import json

from PySide6.QtCore import QObject, Property, Signal, Slot

COMMAND = 'tactic.ui.table.views.TableViewsCmd'


class TableViewsController(QObject):
    changed = Signal()

    def __init__(self, application, pool, parent=None):
        super().__init__(parent)
        self.application, self.pool = application, pool
        self._generation = 0
        self._columns = None
        self._context = None
        self._model = dict(views=[], busy=False, error='', uncertain=False, project='', searchType='', current='table', revision='')
        application.project_changed.connect(self.reset)
        application.signing_out.connect(self.reset)

    @Property('QVariantMap', notify=changed)
    def model(self):
        return deepcopy(self._model)

    @Slot(QObject)
    def open(self, columns):
        if not self.application.can_administer:
            self.application._notify(self.tr('Administrator access required'))
            return
        if columns.busy or columns.dirty:
            self.application._notify(self.tr('Save or discard column changes before managing views.'))
            return
        self._generation += 1
        self._columns = columns
        self._context = dict(project=self.application._current_project_code,
                             search_type=columns._stype_code, current=columns._view)
        self._model = dict(views=[], busy=False, error='', uncertain=False,
                           project=self._context['project'], searchType=self._context['search_type'],
                           current=self._context['current'])
        self.application.window_model.show_window('table_views')
        self.run(dict(action='read'))

    @Slot()
    def reset(self):
        self._generation += 1
        self._columns = self._context = None
        self._model = dict(views=[], busy=False, error='', uncertain=False, project='', searchType='', current='table', revision='')
        self.application.window_model.close_window('table_views')
        self.changed.emit()

    @Slot('QVariantMap')
    def run(self, command):
        command = dict(command)
        if not self._context or self._model['busy']:
            return
        action = command.get('action')
        if action in ('use', 'configure'):
            view = str(command.get('view') or 'table')
            if not any(row['view'] == view for row in self._model['views']):
                return
            self._columns._table_views = [dict(row, current=row['view'] == self._columns._view)
                                          for row in self._model['views']]
            if action == 'configure':
                self._columns.open_scoped_definition(self._context['search_type'], view, self._context['project'])
                self.application.open_columns_editor()
            else:
                index = next(index for index, row in enumerate(self._columns._table_views) if row['view'] == view)
                self._columns.select_table_view(index)
            self.application.window_model.close_window('table_views')
            return
        self._generation += 1
        generation, context = self._generation, dict(self._context)
        self._model.update(busy=True, error='')
        self.changed.emit()
        if self.pool.is_stopped:
            self.pool.start()
        worker = self.pool.add_task(self.load, context, command, generation)
        if worker is None:
            self._model.update(busy=False, error='Server worker is unavailable')
            self.changed.emit()
            return
        worker.result.connect(self.done)
        worker.start()

    @staticmethod
    def load(context, command, generation):
        try:
            from thlib import tactic_classes as tc
            server = tc.server_start(project=context['project'])
            result = server.execute_cmd(COMMAND, dict(search_type=context['search_type'], current=context['current'], **command))
            if result.get('status') != 'OK':
                raise ValueError(result.get('description') or 'Table views could not be loaded')
            info = json.loads(result['info']) if isinstance(result['info'], str) else result['info']
            if command['action'] != 'read':
                fresh = server.execute_cmd(COMMAND, dict(search_type=context['search_type'], current=info['current'], action='read'))
                if fresh.get('status') != 'OK':
                    raise ValueError(fresh.get('description') or 'Table views could not be loaded')
                state = json.loads(fresh['info']) if isinstance(fresh['info'], str) else fresh['info']
                info = dict(state, selected=info['selected'])
            records = list(server.query('config/widget_config', [('search_type', context['search_type'])]) or []) if command['action'] != 'read' else None
            return dict(generation=generation, info=info, records=records, action=command['action'])
        except Exception as error:
            return dict(generation=generation, error=str(error), action=command['action'])

    @Slot(object)
    def done(self, result):
        if isinstance(result, tuple):
            result = result[0]
        if result['generation'] != self._generation:
            return
        if 'error' in result:
            self._model.update(busy=False, error=result['error'], uncertain=result['action'] != 'read')
        else:
            self._model = dict(result['info'], busy=False, error='', uncertain=False)
            self._context['current'] = self._model['current']
            if result['records'] is not None and self._columns:
                cached = self._columns._current_stype().get_project().get_config_views().config_dict
                cached[:] = [row for row in cached if row.get('search_type') != self._context['search_type']] + result['records']
                if self._model['current'] != self._columns._view:
                    self._columns._remember_table_view(self._model['current'])
                self._columns.reload()
        self.changed.emit()
