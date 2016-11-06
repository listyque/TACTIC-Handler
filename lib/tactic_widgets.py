import lib.tactic_classes as tc

# TODO Widgets matching TACTIC Standard widgets

input_classes = {
    'tactic': [
        'tactic.ui.widget.upload_wdg.SimpleUploadWdg',
        'pyasm.widget.input_wdg.TextWdg',
        'pyasm.widget.input_wdg.TextAreaWdg',
        'pyasm.widget.input_wdg.SelectWdg',
        'pyasm.prod.web.prod_input_wdg.CurrentCheckboxWdg',
    ],
    'handler': [
        'TacticSimpleUploadWdg',
        'TacticTextWdg',
        'TacticTextAreaWdg',
        'TacticSelectWdg',
        'TacticCurrentCheckboxWdg',
    ],
}

panel_classes = ['tactic.ui.panel.edit_wdg.EditWdg']


class TacticBaseWidget(object):
    def __init__(self, options_dict=None):
        # basic properties

        # from pprint import pprint
        # pprint(options_dict)
        self.parent_widget = None

        self.project = None
        self.stype = None
        self.sobject = None
        self.sobjects = None

        self.search_type = None
        self.search_key = None

        self.type = None
        self.current_index = None
        self.state = None

        self.class_name = None
        self.label = None
        self.name = None
        self.title = None
        self.values = None

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

    def set_base_widget_options(self, options_dict):
        options_dict_get = options_dict.get
        self.options_dict = options_dict

        self.kwargs = options_dict_get('kwargs')
        self.set_current_index(options_dict_get('current_index'))
        self.set_label(options_dict_get('label'))
        self.set_name(options_dict_get('name'))
        self.set_title(options_dict_get('title'))
        self.set_values(options_dict_get('values'))

        self.set_action_options(options_dict_get('action_options'))

        if self.kwargs:
            self.set_search_key(self.kwargs.get('search_key'))
            self.set_search_type(self.kwargs.get('search_type'))


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
        if self.view == 'edit':
            tc.server_start().update(self.get_search_key(), data)
        else:
            tc.server_start().insert(self.get_search_type(), data)

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


class TacticCurrentCheckboxWdg(TacticBaseInputWdg):
    def __init__(self, options_dict=None):
        super(self.__class__, self).__init__(options_dict=options_dict)

        self.set_class_name('pyasm.prod.web.prod_input_wdg.CurrentCheckboxWdg')


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
