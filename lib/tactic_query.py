def query_EditWdg(args=None, search_type=''):
    import json
    from pyasm.widget.widget_config import WidgetConfigView

    def pop_classes(in_dict):
        out_dict = {}
        for key, val in in_dict.iteritems():
            if not (hasattr(val, '__dict__') or key.startswith('_')):
                out_dict[key] = val
        return out_dict

    class_name = 'tactic.ui.panel.EditWdg'

    args_array = []

    from pyasm.common import Common

    # from pyasm.common import Container
    widget = Common.create_from_class_path(class_name, args_array, args)
    widget.explicit_display()
    result_dict = {
        'EditWdg': {
            'element_descriptions': widget.element_descriptions,
            'element_names': widget.element_names,
            'element_titles': widget.element_titles,
            'input_prefix': widget.input_prefix,
            'kwargs': widget.kwargs,
            'mode': widget.mode,
            'security_denied': widget.security_denied,
            'title': widget.title,
        },
        'InputWidgets': [],
        'sobject': '',
    }
    input_widgets = widget.get_widgets()
    wdg_config = WidgetConfigView.get_by_element_names(search_type, widget.element_names, base_view=args['view'])
    for i_widget in input_widgets:
        widget_dict = pop_classes(i_widget.__dict__)
        widget_dict['action_options'] = wdg_config.get_action_options(widget_dict.get('name'))
        widget_dict['class_name'] = i_widget.get_class_name()
        widget_dict['values'] = i_widget.get_values()
        result_dict['InputWidgets'].append(widget_dict)

    return json.dumps(result_dict, separators=(',', ':'))
    # return str(widget.get_widgets())
    # return (dir(widget))

    # Container.put("request_top_wdg", widget)
    # html = widget.get_buffer_display()
    # m = Container.get_instance()
    # m.get_data()
    # print m.get('SearchType:virtual_stypes')

    # widget_html = server.get_widget(class_name, args, [])
    # return widget_html
