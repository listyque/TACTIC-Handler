import thlib.tactic_classes as tc
from thlib.environment import dl

input_classes = {
    'tactic': [
        'tactic.ui.widget.upload_wdg.SimpleUploadWdg',
        'pyasm.widget.input_wdg.TextWdg',
        'pyasm.widget.input_wdg.TextAreaWdg',
        'pyasm.widget.input_wdg.SelectWdg',
        'pyasm.widget.input_wdg.CheckboxWdg',
        'pyasm.prod.web.prod_input_wdg.CurrentCheckboxWdg',
        'tactic.ui.input.task_input_wdg.TaskSObjectInputWdg',
        'tactic.ui.widget.calendar_wdg.CalendarInputWdg',
        'tactic.ui.input.process_group_select_wdg.ProcessGroupSelectWdg',
        'pyasm.prod.web.prod_input_wdg.ProjectSelectWdg',
        'tactic.ui.input.process_context_wdg.ProcessInputWdg',
        'tactic.ui.input.process_context_wdg.SubContextInputWdg',
        'tactic.ui.widget.misc_input_wdg.TaskStatusSelectWdg',
        'tactic.ui.input.pipeline_input_wdg.PipelineInputWdg',
        'pyasm.widget.input_wdg.ThumbInputWdg',
        'pyasm.widget.input_wdg.PasswordWdg',
    ],
    'handler': [
        'TacticSimpleUploadWdg',
        'TacticTextWdg',
        'TacticTextAreaWdg',
        'TacticSelectWdg',
        'TacticCheckboxWdg',
        'TacticCurrentCheckboxWdg',
        'TacticTaskSObjectInputWdg',
        'TacticCalendarInputWdg',
        'TacticProcessGroupSelectWdg',
        'TacticProjectSelectWdg',
        'TacticProcessInputWdg',
        'TacticSubContextInputWdg',
        'TacticTaskStatusSelectWdg',
        'TacticPipelineInputWdg',
        'TacticThumbInputWdg',
        'TacticPasswordWdg',
    ],
}

panel_classes = ['tactic.ui.panel.edit_wdg.EditWdg']


class TacticBaseWidget(object):
    def __init__(self, options_dict=None, parent=None):
        # basic properties

        self.parent_widget = parent

        self.project = None
        self.stype = None
        self.sobject = None
        self.parent_sobject = None
        self.sobjects = None

        self.search_type = None
        self.search_key = None

        self.parent_key = None

        self.type = None
        self.current_index = None
        self.state = None
        self.read_only = False

        self.class_name = None
        self.label = None
        self.name = None
        self.title = None
        self.values = None
        self.display_values = None

        self.kwargs = {}
        self.options_dict = {}

        self.action_options = {}

        self.info_dict = None

        if options_dict:
            self.set_base_widget_options(options_dict)

    def set_current_index(self, current_index):
        self.current_index = current_index

    def get_current_index(self):
        return self.current_index

    def set_class_name(self, class_name):
        self.class_name = class_name

    def get_class_name(self):
        return self.class_name

    def set_stype(self, stype):
        self.stype = stype

    def get_stype(self):
        return self.stype

    def set_sobject(self, sobject):
        self.sobject = sobject

    def get_sobject(self):
        return self.sobject

    def set_parent_sobject(self, parent_sobject):
        self.parent_sobject = parent_sobject

    def get_parent_sobject(self):
        return self.parent_sobject

    def set_parent_widget(self, parent_widget):
        self.parent_widget = parent_widget

    def get_parent_widget(self):
        return self.parent_widget

    def set_label(self, label):
        self.label = label

    def get_label(self):
        return self.label

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_title(self, title):
        self.title = title

    def get_title(self):
        return self.title

    def set_values(self, values):
        self.values = values

    def get_values(self):
        return self.values

    def get_value(self, value):
        return self.options_dict.get(value)

    def set_display_values(self, display_values):
        self.display_values = display_values

    def get_display_values(self):
        return self.display_values

    def get_default_values(self):
        display_values = self.display_values
        if isinstance(display_values, dict):
            for key in ('value', 'current_value', 'default'):
                value = display_values.get(key)
                if value not in (None, ''):
                    return value
            return None
        if isinstance(display_values, (list, tuple)) and display_values:
            return display_values[0]
        if display_values not in (None, ''):
            return display_values
        return self.kwargs.get('default')

    def set_parent_search_key(self, parent_key):
        self.parent_key = parent_key

    def get_parent_search_key(self):
        return self.parent_key

    def get_parent_stype(self):
        if self.parent_sobject:
            return self.parent_sobject.get_stype()

    def set_search_key(self, search_key):
        self.search_key = search_key

    def get_search_key(self):
        return self.search_key

    def set_search_type(self, search_type):
        if search_type:
            self.search_type = search_type
        else:
            if self.stype:
                self.search_type = self.stype.get_code()

    def get_search_type(self):
        return self.search_type

    def set_action_options(self, action_options):
        self.action_options = action_options or {}

    def get_action_options(self):
        return self.action_options

    def get_options(self):
        return self.options_dict

    def get_info_dict(self):
        return self.info_dict

    def set_info_dict(self, info_dict):
        self.info_dict = info_dict

    def set_base_widget_options(self, options_dict):

        options_dict_get = options_dict.get
        self.options_dict = options_dict

        self.set_parent_sobject(options_dict_get('parent_sobject'))
        self.set_sobject(options_dict_get('sobject'))
        self.set_stype(options_dict_get('stype'))

        self.kwargs = options_dict_get('kwargs') or {}
        self.set_current_index(options_dict_get('current_index'))
        self.set_label(options_dict_get('label'))
        self.set_name(options_dict_get('name'))
        self.set_title(options_dict_get('title'))
        self.set_values(options_dict_get('values'))
        self.set_display_values(options_dict_get('__display_values__'))

        self.set_action_options(options_dict_get('action_options'))
        self.set_info_dict(options_dict_get('info_dict'))

        if self.kwargs:
            self.set_search_type(self.kwargs.get('search_type'))
            self.set_search_key(self.kwargs.get('search_key'))
            self.set_parent_search_key(self.kwargs.get('parent_key'))

    @staticmethod
    def _flag(value):
        if isinstance(value, str):
            return value.strip().lower() in {'1', 'true', 'yes', 'on'}
        return bool(value)

    def get_submit_name(self):
        return self.action_options.get('column') or self.name

    def get_required(self):
        return any(
            self._flag(value) for value in (
                self.options_dict.get('required'),
                self.kwargs.get('required'),
                self.action_options.get('required'),
            )
        )

    def get_read_only(self):
        return any(
            self._flag(value) for value in (
                self.options_dict.get('read_only'),
                self.kwargs.get('read_only'),
                self.action_options.get('read_only'),
            )
        )

    def get_editor_kind(self, data_type='text'):
        return 'string'

    def get_editor_options(self):
        return []

    def get_description(self):
        return str(
            self.options_dict.get('description')
            or self.kwargs.get('description')
            or self.kwargs.get('help')
            or self.action_options.get('description')
            or ''
        )


class TacticEditWdg(TacticBaseWidget):
    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)

        self.mode = None
        self.input_prefix = None
        self.view = None

        if options_dict:
            self.set_base_edit_options(options_dict)

    def commit(self, data):
        # print 'BEGIN SAVING', data
        stype = self.get_stype()
        parent_stype = self.get_parent_stype()
        if parent_stype:
            project = parent_stype.get_project()
        else:
            project = stype.get_project()

        if self.input_prefix == 'edit':
            # Logging info
            dl.log('Making Commit Update for {}'.format(stype.get_pretty_name()), group_id=stype.get_code())
            runtime_command = 'thenv.get_tc().server_start(project="{0}").update("{1}", {2})'.format(
                project.get_code(), self.get_search_key(), str(data))
            dl.info(runtime_command, group_id=stype.get_code())

            return tc.server_start(project=project.get_code()).update(self.get_search_key(), data)
        else:
            instance_type = self.options_dict.get('instance_type')
            instance_path = self.options_dict.get('instance_path')
            instance_type_str = None

            sobject = self.get_sobject()

            if sobject and not instance_type:
                parent_stype = sobject.get_stype()

                schema = self.stype.get_schema()
                child = schema.get_child(
                    self.stype.get_code(), parent_stype.get_code())

                if child:
                    relationship = child.get('relationship')
                    if relationship == 'instance':
                        instance_type = child.get('instance_type')

            # Logging info
            dl.log('Making Commit Insert for {}'.format(stype.get_pretty_name()), group_id=stype.get_code())
            parent_key = self.get_parent_search_key()
            if parent_key:
                parent_key = '"{}"'.format(parent_key)

            if instance_type:
                instance_type_str = '"{}"'.format(instance_type)

            runtime_command = (
                u'thenv.get_tc().insert_sobjects("{0}", "{1}", {2}, '
                u'parent_key={3}, instance_type={4}, instance_path={5})'
            ).format(
                self.get_search_type(), project.get_code(), str(data),
                parent_key, instance_type_str, repr(instance_path))
            dl.info(runtime_command, group_id=stype.get_code())

            return tc.insert_sobjects(
                self.get_search_type(), project.get_code(), data,
                parent_key=self.get_parent_search_key(),
                instance_type=instance_type, instance_path=instance_path)

    def set_base_edit_options(self, options_dict):
        self.options_dict = options_dict

        self.mode = self.options_dict.get('mode')
        self.input_prefix = self.kwargs.get('input_prefix')
        self.view = self.kwargs.get('view')


class TacticBaseInputWdg(TacticBaseWidget):
    _data_type_kinds = {
        'integer': 'integer',
        'int': 'integer',
        'serial': 'integer',
        'float': 'float',
        'double': 'float',
        'decimal': 'float',
        'numeric': 'float',
        'boolean': 'bool',
        'bool': 'bool',
        'date': 'date',
        'datetime': 'datetime',
        'timestamp': 'datetime',
        'text': 'string',
    }
    editor_kind = ''

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)

    def get_editor_kind(self, data_type='text'):
        if self.editor_kind:
            return self.editor_kind
        return self._data_type_kinds.get(
            str(data_type or 'text').lower(), 'string'
        )


class TacticTextWdg(TacticBaseInputWdg):
    tactic_class = 'pyasm.widget.input_wdg.TextWdg'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name(self.tactic_class)


class TacticTextAreaWdg(TacticTextWdg):
    tactic_class = 'pyasm.widget.input_wdg.TextAreaWdg'
    editor_kind = 'multiline'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)


class TacticSimpleUploadWdg(TacticBaseInputWdg):
    editor_kind = 'preview'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name('tactic.ui.widget.upload_wdg.SimpleUploadWdg')


class TacticSelectWdg(TacticBaseInputWdg):
    tactic_class = 'pyasm.widget.input_wdg.SelectWdg'
    editor_kind = 'enum'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name(self.tactic_class)
        self.labels = []
        self.values = []
        self.required = False
        self.empty = False
        self.set_select_widget_options(self.options_dict)

    def set_labels(self, labels):
        self.labels = list(labels or [])

    def get_labels(self):
        return self.labels

    def set_values(self, values):
        self.values = list(values or [])

    def get_values(self):
        return self.values

    def set_required(self, required):
        self.required = self._flag(required)

    def get_required(self):
        return self.required

    def set_empty(self, empty):
        self.empty = self._flag(empty)

    def get_empty(self):
        return self.empty

    def set_select_widget_options(self, options_dict):
        options_dict = options_dict or {}
        display_values = options_dict.get('__display_values__')
        display_values = (
            display_values if isinstance(display_values, dict) else {}
        )
        self.set_values(
            options_dict.get('values') or display_values.get('values')
        )
        self.set_labels(
            options_dict.get('labels') or display_values.get('labels')
        )
        self.set_required(super().get_required())
        self.set_empty(self.kwargs.get('empty'))

    def get_editor_options(self):
        options = []
        for index, value in enumerate(self.values):
            label = self.labels[index] if index < len(self.labels) else value
            options.append({'label': str(label), 'value': value})
        return options


class TacticCheckboxWdg(TacticBaseInputWdg):
    tactic_class = 'pyasm.widget.input_wdg.CheckboxWdg'
    editor_kind = 'bool'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name(self.tactic_class)


class TacticCurrentCheckboxWdg(TacticCheckboxWdg):
    tactic_class = 'pyasm.prod.web.prod_input_wdg.CurrentCheckboxWdg'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)


class TacticTaskSObjectInputWdg(TacticBaseInputWdg):
    editor_kind = 'parent'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name('tactic.ui.input.task_input_wdg.TaskSObjectInputWdg')

    def get_read_only(self):
        return True


class TacticCalendarInputWdg(TacticBaseInputWdg):
    editor_kind = 'datetime'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name('tactic.ui.widget.calendar_wdg.CalendarInputWdg')


class TacticProcessGroupSelectWdg(TacticSelectWdg):
    tactic_class = (
        'tactic.ui.input.process_group_select_wdg.ProcessGroupSelectWdg'
    )
    editor_kind = 'user'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)


class TacticProjectSelectWdg(TacticSelectWdg):
    tactic_class = 'pyasm.prod.web.prod_input_wdg.ProjectSelectWdg'
    editor_kind = 'project'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)


class TacticProcessInputWdg(TacticBaseInputWdg):
    editor_kind = 'process'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name(
            'tactic.ui.input.process_context_wdg.ProcessInputWdg'
        )


class TacticSubContextInputWdg(TacticTextWdg):
    tactic_class = 'tactic.ui.input.process_context_wdg.SubContextInputWdg'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)


class TacticTaskStatusSelectWdg(TacticBaseInputWdg):
    editor_kind = 'status'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name('tactic.ui.widget.misc_input_wdg.TaskStatusSelectWdg')


class TacticPipelineInputWdg(TacticSelectWdg):
    tactic_class = 'tactic.ui.input.pipeline_input_wdg.PipelineInputWdg'
    editor_kind = 'pipeline'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)

    def get_current_value(self):
        display_values = self.get_display_values()
        if not isinstance(display_values, dict):
            return None
        current_value = display_values.get('value')

        if current_value:
            return current_value

    def get_current_label(self):
        current_value = self.get_current_value()

        for i, value in enumerate(self.get_values() or []):
            if value == current_value:
                labels = self.get_labels() or []
                if i < len(labels):
                    return labels[i]

    def get_default_values(self):
        default = self.get_current_value() or self.kwargs.get('default')
        if default in self.get_values():
            return default
        for index, label in enumerate(self.get_labels()):
            if label == default and index < len(self.get_values()):
                return self.get_values()[index]
        return default


class TacticThumbInputWdg(TacticBaseInputWdg):
    editor_kind = 'thumbnail'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)
        self.set_class_name('pyasm.widget.input_wdg.ThumbInputWdg')

    def get_read_only(self):
        return True


class TacticPasswordWdg(TacticTextWdg):
    tactic_class = 'pyasm.widget.input_wdg.PasswordWdg'
    editor_kind = 'password'

    def __init__(self, options_dict=None):
        super().__init__(options_dict=options_dict)

    def get_default_values(self):
        return ''


_input_widget_classes = {
    tactic_name: globals()[handler_name]
    for tactic_name, handler_name in zip(
        input_classes['tactic'], input_classes['handler']
    )
}


def get_widget_class(tactic_class='', type=''):
    if type != 'input':
        return None
    return _input_widget_classes.get(tactic_class)


def get_widget_name(tactic_class='', type=''):
    widget_class = get_widget_class(tactic_class, type)
    return widget_class.__name__ if widget_class else None
