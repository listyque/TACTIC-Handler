import thlib.tactic_classes as tc
from thlib.environment import dl

# TODO Widgets matching TACTIC Standard widgets

# TODO WIDGETS:
# <tactic.ui.input.process_context_wdg.ProcessInputWdg object at 0x7fcca9553ad0>,
#  '<tactic.ui.input.process_context_wdg.SubContextInputWdg object at 0x7f94ea537d90>',
#  '<tactic.ui.widget.misc_input_wdg.TaskStatusSelectWdg object at 0x7f94ea537850>'


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

        self.class_name = None
        self.label = None
        self.name = None
        self.title = None
        self.values = None
        self.display_values = None

        self.kwargs = None
        self.options_dict = None

        self.action_options = None

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

    def set_display_values(self, display_values):
        self.display_values = display_values

    def get_display_values(self):
        return self.display_values

    def get_default_values(self):
        if self.display_values:
            return self.display_values[0]

    def set_parent_search_key(self, parent_key):
        self.parent_key = parent_key

    def get_parent_search_key(self):
        return self.parent_key

    def set_search_key(self, search_key):
        self.search_key = search_key

    def get_search_key(self):
        return self.search_key

    def set_search_type(self, search_type):
        self.search_type = search_type

    def get_search_type(self):
        return self.search_type

    def set_action_options(self, action_options):
        self.action_options = action_options

    def get_action_options(self):
        return self.action_options

    def get_options(self):
        return self.options_dict

    # def get_empty_label(self):
    #     if self.has_empty_value():
    #         return self.options_dict.get('empty_option_label')
    #     else:
    #         return ''
    #
    # def has_empty_value(self):
    #     if self.kwargs:
    #         if self.kwargs.get('empty'):
    #             return True
    #     elif self.options_dict.get('empty'):
    #         return True
    #     else:
    #         return False

    def set_base_widget_options(self, options_dict):

        options_dict_get = options_dict.get
        self.options_dict = options_dict

        self.set_parent_sobject(options_dict_get('parent_sobject'))
        self.set_sobject(options_dict_get('sobject'))
        self.set_stype(options_dict_get('stype'))

        self.kwargs = options_dict_get('kwargs')
        self.set_current_index(options_dict_get('current_index'))
        self.set_label(options_dict_get('label'))
        self.set_name(options_dict_get('name'))
        self.set_title(options_dict_get('title'))
        self.set_values(options_dict_get('values'))
        self.set_display_values(options_dict_get('__display_values__'))

        self.set_action_options(options_dict_get('action_options'))

        if self.kwargs:
            self.set_search_type(self.kwargs.get('search_type'))
            self.set_search_key(self.kwargs.get('search_key'))
            self.set_parent_search_key(self.kwargs.get('parent_key'))


class TacticEditWdg(TacticBaseWidget):
    def __init__(self, options_dict=None):
        super(TacticEditWdg, self).__init__(options_dict=options_dict)

        self.mode = None
        self.input_prefix = None
        self.view = None

        if options_dict:
            self.set_base_edit_options(options_dict)

    def commit(self, data):
        # TODO make with threads
        # print 'BEGIN SAVING', data
        stype = self.get_stype()
        project = stype.get_project()

        if self.view == 'edit':
            # Logging info
            dl.log('Making Commit Update for {}'.format(stype.get_pretty_name()), group_id=stype.get_code())
            runtime_command = 'thenv.get_tc().server_start(project="{0}").update("{1}", {2})'.format(
                project.get_code(), self.get_search_key(), str(data))
            dl.info(runtime_command, group_id=stype.get_code())

            return tc.server_start(project=project.get_code()).update(self.get_search_key(), data)
        else:
            instance_type = None
            instance_type_str = None

            sobject = self.get_sobject()

            if sobject:
                parent_stype = sobject.get_stype()

                schema = self.stype.get_schema()
                child = schema.get_child(self.get_search_type(), parent_stype.get_code())

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

            runtime_command = 'thenv.get_tc().insert_sobjects("{0}", "{1}", {2}, parent_key={3}, instance_type={4})'.format(
                self.get_search_type(), project.get_code(), str(data), parent_key, instance_type_str)
            dl.info(runtime_command, group_id=stype.get_code())

            return tc.insert_sobjects(self.get_search_type(), project.get_code(), data, parent_key=self.get_parent_search_key(), instance_type=instance_type)

    def set_base_edit_options(self, options_dict):
        options_dict_get = options_dict.get
        self.options_dict = options_dict

        self.mode = options_dict_get('mode')
        self.input_prefix = self.kwargs.get('input_prefix')
        self.view = self.kwargs.get('view')


class TacticBaseInputWdg(TacticBaseWidget):
    def __init__(self, options_dict=None):
        super(TacticBaseInputWdg, self).__init__(options_dict=options_dict)


class TacticTextWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('pyasm.widget.input_wdg.TextWdg')


class TacticTextAreaWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('pyasm.widget.input_wdg.TextAreaWdg')


class TacticSimpleUploadWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('tactic.ui.widget.upload_wdg.SimpleUploadWdg')


class TacticSelectWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('pyasm.widget.input_wdg.SelectWdg')

        self.labels = None
        self.values = None

        self.required = None
        self.empty = None

        if options_dict:
            self.set_select_widget_options(options_dict)

    def set_labels(self, labels):
        self.labels = labels

    def get_labels(self):
        return self.labels

    def set_values(self, values):
        self.values = values

    def get_values(self):
        return self.values

    def set_required(self, required):
        self.required = required

    def get_required(self):
        return self.required

    def set_empty(self, empty):
        self.empty = empty

    def get_empty(self):
        return self.empty

    def set_select_widget_options(self, options_dict):
        options_dict_get = options_dict.get

        self.set_values(options_dict_get('values'))
        self.set_labels(options_dict_get('labels'))

        self.set_required(self.kwargs.get('required'))
        self.set_empty(self.kwargs.get('empty'))


class TacticCheckboxWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('pyasm.widget.input_wdg.CheckboxWdg')


class TacticCurrentCheckboxWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('pyasm.prod.web.prod_input_wdg.CurrentCheckboxWdg')


class TacticTaskSObjectInputWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('tactic.ui.input.task_input_wdg.TaskSObjectInputWdg')


class TacticCalendarInputWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('tactic.ui.widget.calendar_wdg.CalendarInputWdg')


class TacticProcessGroupSelectWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('tactic.ui.input.process_group_select_wdg.ProcessGroupSelectWdg')

        self.labels = []
        self.values = []

        self.required = None
        self.empty = None

        # if options_dict:
        #     self.set_select_widget_options(options_dict)

    def set_labels(self, labels):
        self.labels = labels

    def get_labels(self):
        return self.labels

    def set_values(self, values):
        self.values = values

    def get_values(self):
        return self.values

    def set_required(self, required):
        self.required = required

    def get_required(self):
        return self.required

    def set_empty(self, empty):
        self.empty = empty

    def get_empty(self):
        return self.empty

    def set_select_widget_options(self, options_dict):
        options_dict_get = options_dict['__display_values__'].get

        self.set_values(options_dict_get('values'))
        self.set_labels(options_dict_get('labels'))


class TacticProjectSelectWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('tactic.ui.input.process_group_select_wdg.ProcessGroupSelectWdg')

        self.labels = None
        self.values = None

        self.required = None
        self.empty = None

        if options_dict:
            self.set_select_widget_options(options_dict)

    def set_labels(self, labels):
        self.labels = labels

    def get_labels(self):
        return self.labels

    def set_values(self, values):
        self.values = values

    def get_values(self):
        return self.values

    def set_required(self, required):
        self.required = required

    def get_required(self):
        return self.required

    def set_empty(self, empty):
        self.empty = empty

    def get_empty(self):
        return self.empty

    def set_select_widget_options(self, options_dict):

        options_dict_get = options_dict.get

        self.set_values(options_dict_get('values'))
        self.set_labels(options_dict_get('labels'))


def get_widget_name(tactic_class='', type=''):
    if type == 'input':
        tactic_classes = input_classes
    else:
        tactic_classes = None

    if tactic_classes:
        result_class = None
        for i, cls in enumerate(tactic_classes['tactic']):
            if tactic_class == cls:
                result_class = tactic_classes['handler'][i]

        return result_class
