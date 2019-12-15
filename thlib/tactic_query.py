# Internal server-side sctipts

import global_functions as gf
import inspect


def prepare_serverside_script(func, kwargs, return_dict=True, has_return=True, shrink=True, catch_traceback=True):
    func_lines = inspect.getsourcelines(func)
    if has_return:
        run_command = func_lines[0][0].replace(u'def ', u'return ')[:-2]
    else:
        run_command = func_lines[0][0].replace(u'def ', u'')[:-2]
    # i don't want 're' here, so try to understand logic, with love to future me :-*
    # TODO multiline bug

    args_list = []
    for key, arg in kwargs.items():
        if isinstance(arg, (str, unicode)):
            args_list.append(u"{}='{}'".format(key, arg.replace('"', '\"')))
        else:
            args_list.append(u'{}={}'.format(key, arg))

    var_stitch = u', '.join(args_list)
    ready_run_command = u'{0}({1})'.format(run_command[:run_command.find(u'(')], var_stitch)
    if catch_traceback:
        traceback = inspect.getsourcelines(get_traceback)
        handle = inspect.getsourcelines(traceback_handle)
        code = u''.join(traceback[0]) + u''.join(handle[0]) + u'@traceback_handle \n' + ''.join(func_lines[0]) + ready_run_command
    else:
        code = u''.join(func_lines[0]) + ready_run_command
    if shrink:
        code = gf.minify_code(source=code)
    if return_dict:
        code_dict = {
            'code': code
        }
        return code_dict
    else:
        return code


def traceback_handle(func):
    def traceback_handle_wrap(*arg, **kwarg):
        try:
            result = func(*arg, **kwarg)
        except:
            result = get_traceback()
        return result

    return traceback_handle_wrap


def get_traceback():
    result = u''
    import traceback, sys
    exception_type, exception_value, exception_traceback = sys.exc_info()

    exception_type_string = exception_type is not None and exception_type.__name__ or u'UnknownError'
    exception_value_string = exception_value is not None and exception_value.message or u'Unknown error handled'

    format_traceback = traceback.format_exception(exception_type, exception_value, exception_traceback, limit=100)
    if format_traceback:
        if isinstance(format_traceback, (list, set, tuple)):
            format_traceback_list = list(format_traceback)
        else:
            format_traceback_list = [format_traceback]
        for format_traceback in format_traceback_list:
            if isinstance(format_traceback, (basestring, unicode)):
                result += format_traceback
            else:
                try:
                    result += format_traceback.__repr__()
                except:
                    try:
                        result += unicode(format_traceback)
                    except:
                        result += u'( Failed to decode Exception data )'
    if not result:
        result = u'Error: ' + exception_value_string + u'\n' + exception_type_string + u': ' + exception_value_string

    return result


def query_EditWdg(args=None, search_type='', project=''):
    import json
    from pyasm.widget.widget_config import WidgetConfigView

    if project:
        server.set_project(project)

    def pop_classes(in_dict):
        out_dict = {}

        ignore_columns = ['sobjects_for_options', 'pipelines', '_sobjects']
        for key, val in in_dict.items():
            if not (hasattr(val, '__dict__') or key.startswith('_')) and key not in ignore_columns:
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

    temprorary_ignore = ['tactic.ui.input.process_context_wdg.ProcessInputWdg', 'tactic.ui.input.process_context_wdg.SubContextInputWdg', 'tactic.ui.widget.misc_input_wdg.TaskStatusSelectWdg']

    for i_widget in input_widgets:
        widget_dict = pop_classes(i_widget.__dict__)
        widget_dict['action_options'] = wdg_config.get_action_options(widget_dict.get('name'))
        widget_dict['class_name'] = i_widget.get_class_name()
        display_values = i_widget.get_values()
        if display_values:
            widget_dict['__display_values__'] = display_values
        else:
            # Special cases for different widgets
            if widget_dict['class_name'] == 'tactic.ui.input.process_group_select_wdg.ProcessGroupSelectWdg':
                select_wd = i_widget.get_display()
                select_wd.get_display()
                widget_dict['__display_values__'] = select_wd.__dict__

        if widget_dict['class_name'] not in temprorary_ignore:
            result_dict['InputWidgets'].append(widget_dict)

    return json.dumps(result_dict, separators=(',', ':'))


def get_all_dependency(search_keys, project_code=None):
    from pyasm.search import Search, SearchType
    from pyasm.biz import Project
    import json

    if not project_code:
        search_type, search_code = server.split_search_key(search_keys[0])
        project_code = Project.extract_project_code(search_type)

    server.set_project(project_code)

    result = {}
    for search_key in search_keys:
        sobject = Search.get_by_search_key(search_key)
        base_search_type = sobject.get_base_search_type()
        related_types = SearchType.get_related_types(base_search_type, direction='children')

        for related_type in related_types:
            sobjects = sobject.get_related_sobjects(related_type)
            result.setdefault(related_type, []).append(server.server._get_sobjects_dict(sobjects))
            # result[related_type] = server.server._get_sobjects_dict(sobjects)

    return json.dumps(result)


def delete_sobjects(search_keys, include_dependencies=False, list_dependencies=None):
    '''Invokes the delete method.  Note: this function may fail due
    to dependencies.  Tactic will not cascade delete.  This function
    should be used with extreme caution because, if successful, it will
    permenently remove the existence of an sobject

    @params
    search_key - the key identifying
                  the search_type table.
    list_dependencies - dependency dict {
        'related_types': ["sthpw/note", "sthpw/file"],
    } etc...

    @return
    sobject - a dictionary that represents values of the sobject in the
        form name/value pairs
    '''

    from pyasm.biz import Project
    from tactic.ui.tools import DeleteCmd
    import json

    if not isinstance(search_keys, list):
        search_keys = [search_keys]

    search_type, search_code = server.split_search_key(search_keys[0])
    project_code = Project.extract_project_code(search_type)
    server.set_project(project_code)

    sobjects = server.server._get_sobjects(search_keys)
    if not sobjects:
        raise Exception("SObject [%s] does not exist" % search_keys[0])

    deleted_sobjects = []
    ex_list = ['sthpw/file']

    for sobject in sobjects:
        if include_dependencies:
            cmd = DeleteCmd(sobject=sobject, auto_discover=True)
            cmd.execute()
        elif list_dependencies and sobject.get_base_search_type() not in ex_list:
            cmd = DeleteCmd(sobject=sobject, values=list_dependencies, auto_discover=False)
            cmd.execute()
        else:
            sobject.delete()

        deleted_sobjects.append(server.server._get_sobject_dict(sobject))

    return json.dumps(deleted_sobjects)


def get_projects_and_logins(current_login='admin'):
    import json
    from pyasm.search import Search, SearchKey

    def get_sobjects_dict(sobjects):
        res = []
        if sobjects:
            search_keys = SearchKey.get_by_sobjects(sobjects, use_id=False)
            for j, sobject in enumerate(sobjects):
                sobj = sobject.get_data()

                sobj['__search_key__'] = search_keys[j]
                res.append(sobj)

        return res

    # Getting all Projects from db
    search = Search('sthpw/project')
    search.add_op_filters([])
    projects = get_sobjects_dict(search.get_sobjects())

    # Getting all possible Logins from db

    search = Search('sthpw/login')
    search.add_op_filters([])
    logins = get_sobjects_dict(search.get_sobjects())

    search = Search('sthpw/login_group')
    search.add_op_filters([])
    logins_group = get_sobjects_dict(search.get_sobjects())

    search = Search('sthpw/login_in_group')
    search.add_op_filters([])
    logins_in_group = get_sobjects_dict(search.get_sobjects())

    # search = Search('sthpw/subscription')
    # search.add_op_filters([('login', current_login)])
    #
    # subscriptions = get_sobjects_dict(search.get_sobjects())

    result = {'projects': projects, 'logins': logins, 'login_groups': logins_group, 'login_in_groups': logins_in_group}

    return json.dumps(result, separators=(',', ':'))


def get_subscriptions_and_messages(current_login='admin', update_logins=False):
    import json
    from pyasm.search import Search, SearchKey

    def get_sobjects_dict(sobjects):
        res = []
        if sobjects:
            search_keys = SearchKey.get_by_sobjects(sobjects, use_id=False)
            for j, sobject in enumerate(sobjects):
                sobj = sobject.get_data()

                sobj['__search_key__'] = search_keys[j]
                res.append(sobj)

        return res

    # Getting all possible Logins from db
    if update_logins:
        search = Search('sthpw/login')
        search.add_op_filters([])
        logins = get_sobjects_dict(search.get_sobjects())

        search = Search('sthpw/login_group')
        search.add_op_filters([])
        logins_group = get_sobjects_dict(search.get_sobjects())

        search = Search('sthpw/login_in_group')
        search.add_op_filters([])
        logins_in_group = get_sobjects_dict(search.get_sobjects())

    search = Search('sthpw/subscription')
    search.add_op('begin')
    search.add_filter(name='login', value=current_login)
    search.add_filter(name='category', value='chat')
    search.add_op('or')

    subscriptions = get_sobjects_dict(search.get_sobjects())

    # getting all messages
    search = Search('sthpw/message')
    search.add_op('begin')
    search.add_filter(name='login', value=current_login)
    search.add_filter(name='category', value='chat')
    search.add_op('or')

    messages = get_sobjects_dict(search.get_sobjects())

    if update_logins:
        result = {
            'logins': logins,
            'login_groups': logins_group,
            'login_in_groups': logins_in_group,
            'subscriptions': subscriptions,
            'messages': messages,
        }
    else:
        result = {
            'subscriptions': subscriptions,
            'messages': messages,
        }

    return json.dumps(result, separators=(',', ':'))


def get_notes_and_stypes_counts(process, search_key, stypes_list):
    # getting notes by search_type process and count of stypes from stypes_list
    from pyasm.search import Search

    search_type, search_code = server.split_search_key(search_key)
    search = Search(search_type)
    sobject = search.get_by_search_key(search_key)

    cnt = {
        'notes': {},
        'stypes': {},
    }

    for p in process:
        search = Search('sthpw/note')
        search.add_op_filters([('process', p), ('search_type', search_type), ('search_code', search_code)])
        cnt['notes'][p] = search.get_count(True)

    for stype in stypes_list:
        try:
            search = Search(stype)
            search.add_relationship_filter(sobject)
            count = search.get_count(True)
            if count == -1:
                count = 0
            cnt['stypes'][stype] = count
        except:
            cnt['stypes'][stype] = 0

    return cnt


def query_search_types_extended(project_code):
    """
    This crazy stuff made to execute queries on server
    All needed info is getting almost half time faster
    :return:
    """
    import json
    from pyasm.biz import Project
    from pyasm.search import Search
    from pyasm.search import SearchKey
    from pyasm.biz import Pipeline

    from pyasm.widget import WidgetConfigView
    from pyasm.search import WidgetDbConfig

    def get_sobject_dict(sobject):
        search_key = SearchKey.get_by_sobject(sobject, use_id=False)
        sobj = sobject.get_data()
        sobj['__search_key__'] = search_key

        return sobj

    if project_code == 'sthpw':
        search = Search('sthpw/search_object')
        search.add_filters('code', ['sthpw/task', 'sthpw/login', 'sthpw/snapshot', 'sthpw/file', 'sthpw/search_type',
                                    'sthpw/search_object', 'sthpw/schema', 'sthpw/retire_log', 'sthpw/repo',
                                    'sthpw/project_type', 'sthpw/project', 'sthpw/pref_setting', 'sthpw/pref_list',
                                    'sthpw/pipeline', 'sthpw/notification_login', 'sthpw/notification_log',
                                    'sthpw/notification', 'sthpw/note', 'sthpw/milestone', 'sthpw/message_log',
                                    'sthpw/message', 'sthpw/login_in_group', 'sthpw/login_group', 'sthpw/login',
                                    'sthpw/exception_log', 'sthpw/debug_log', 'sthpw/custom_script', 'sthpw/clipboard',
                                    'sthpw/change_timestamp', 'config/custom_property', 'sthpw/ticket'])
        search.add_order_by('search_type')
        stypes = search.get_sobjects()
    else:
        prj = Project.get_by_code(project_code)
        stypes = prj.get_search_types()

    all_stypes = []
    # longest time consuming part, don't know how to optimize yet
    for stype in stypes:
        stype_dict = get_sobject_dict(stype)
        stype_dict['column_info'] = stype.get_column_info(stype.get_code())
        all_stypes.append(stype_dict)

        # getting views for columns viewer
        views = ['table', 'definition', 'color', 'edit', 'edit_definition']
        definition = {}
        full_search_type = Project.get_full_search_type(stype)
        for view in views:

            db_config = WidgetDbConfig.get_by_search_type(full_search_type, view)
            if db_config:
                config = db_config.get_xml()
            else:
                config_view = WidgetConfigView.get_by_search_type(stype, view)
                config = config_view.get_config()

            definition[view] = config.to_string()

        stype_dict['definition'] = definition

    search = Search('sthpw/pipeline')
    search.add_op('begin')
    search.add_filter(name='project_code', value=project_code)
    search.add_filter(name='project_code', value=None)  # also searching NULL projects to get site-wide pipelines
    search.add_op('or')

    stypes_pipelines = search.get_sobjects()

    # Adding default tasks pipelines
    stypes_pipelines.append(Pipeline.get_by_code('task'))
    stypes_pipelines.append(Pipeline.get_by_code('approval'))
    stypes_pipelines.append(Pipeline.get_by_code('dependency'))
    stypes_pipelines.append(Pipeline.get_by_code('progress'))

    # getting processes info
    pipelines = []
    for pipeline in stypes_pipelines:
        stypes_dict = get_sobject_dict(pipeline)

        processes = []
        for process in pipeline.get_process_names():
            process_sobject = pipeline.get_process_sobject(process)
            if process_sobject:
                processes.append(get_sobject_dict(process_sobject))

        task_processes = []
        for process in pipeline.get_processes():
            process_obj = process.get_task_pipeline()
            if process_obj != 'task':
                task_processes.append(process_obj)

        stypes_dict['tasks_processes'] = task_processes
        stypes_dict['stypes_processes'] = processes
        pipelines.append(stypes_dict)

    # getting project schema
    schema = server.query('sthpw/schema', [('code', project_code)])

    if project_code == 'sthpw':
        from pyasm.biz import Schema
        admin_schema = Schema.get()
        admin_schema_dict = {
            '__search_key__': u'sthpw/schema?code=sthpw',
            'code': u'sthpw',
            'description': u'Schema for project [sthpw]',
            'id': 1,
            'login': u'admin',
            'project_code': u'sthpw',
            's_status': None,
            'schema': admin_schema.get_admin_schema().get_xml().to_string(),
            'timestamp': '2005-01-01 00:00:00'}

        schema.append(admin_schema_dict)

    result = {'schema': schema, 'pipelines': pipelines, 'stypes': all_stypes}

    return json.dumps(result, separators=(',', ':'))


def get_dirs_with_naming(search_key=None, process_list=None):
    import json
    from pyasm.biz import Snapshot
    from pyasm.biz import Project
    from pyasm.search import SearchType

    dir_naming = Project.get_dir_naming()
    # Project.get_file_naming()

    dirs_dict = {
        'versions': [],
        'versionless': [],
    }

    if process_list:
        processes = process_list
    else:
        from pyasm.biz import Pipeline
        sobjects = server.server._get_sobjects(search_key)
        sobject = sobjects[0]
        pipelines = Pipeline.get_by_search_type(sobject.get_base_search_type())
        processes = pipelines[0].get_process_names()

    search_type, search_code = server.split_search_key(search_key)
    search_type = search_type.split('?')[0]

    for process in processes:
        # querying sobjects every time because we need to refresh naming
        sobject = server.query(search_type, filters=[('code', search_code)], return_sobjects=True, single=True)
        dir_naming.set_sobject(sobject)
        file_object = SearchType.create('sthpw/file')
        dir_naming.set_file_object(file_object)
        snapshot = Snapshot.create(sobject, snapshot_type='file', process=process, context=process, commit=False)
        dir_naming.set_snapshot(snapshot)
        dirs_dict['versions'].append(dir_naming.get_dir('relative'))

        snapshot_versionless = Snapshot.create(sobject, snapshot_type='file', context=process, process=process,
                                               commit=False, version=-1)
        dir_naming.set_snapshot(snapshot_versionless)
        dirs_dict['versionless'].append(dir_naming.get_dir('relative'))

    return json.dumps(dirs_dict, separators=(',', ':'))


def query_sobjects_snapshots_updated(search_type, filters=[], order_bys=[], project_code=None, last_timestamp=''):
    import json
    from pyasm.search import Search, SearchKey
    from pyasm.biz import Snapshot

    if project_code:
        server.set_project(project_code)

    def get_sobject_dict(sobject):
        search_key = SearchKey.get_by_sobject(sobject, use_id=False)
        sobj = sobject.get_data()
        sobj['__search_key__'] = search_key

        return sobj

    if search_type.startswith('sthpw'):
        splitted_search_type = search_type
    else:
        splitted_search_type, project_code = server.split_search_key(search_type)

    # Getting count of all sobjects of this stype
    search = Search(splitted_search_type)

    # checking if search filters have expression and separate it
    expressions_filters_list = []
    filters_list = []

    for fltr in filters:
        if fltr[0] == '_expression':
            expressions_filters_list.append((fltr[1], fltr[2]))
        else:
            filters_list.append(fltr)

    # now evaluate all expressions and add them to our search
    search.add_op('begin')
    # search.add_op('and')

    if filters_list:
        search.add_op_filters(filters_list)

    if order_bys:
        for order_by in order_bys:
            search.add_order_by(order_by)

    if expressions_filters_list:

        for op, expression_filter in expressions_filters_list:
            eval_sobjects = Search.eval(expression_filter)
            if eval_sobjects:
                search.add_relationship_filters(eval_sobjects, op=op)
            elif op == 'in':
                search.set_null_filter()

    sobjects_list = search.get_sobjects()

    sobjects_dicts_list = server.server._get_sobjects_dict(sobjects_list)

    result = {
        'sobjects_list': sobjects_dicts_list,
    }
    have_search_code = False
    if sobjects_dicts_list:
        if sobjects_dicts_list[0].get('code'):
            have_search_code = True

    for sobject in sobjects_dicts_list:

        search = Search('sthpw/snapshot')

        snapshots_filters = [('search_type', search_type)]
        if have_search_code:
            snapshots_filters.append(('search_code', sobject['code']))
        else:
            snapshots_filters.append(('search_id', sobject['id']))

        if not get_all_snapshots:
            snapshots_filters.append(('process', ['icon', 'attachment', 'publish']))
        search.add_op_filters(snapshots_filters)

        snapshots = search.get_sobjects()

        snapshot_files = Snapshot.get_files_dict_by_snapshots(snapshots)

        snapshots_list = []
        for snapshot in snapshots:
            if get_all_snapshots:
                snapshot_dict = get_sobject_dict(snapshot)
                files_list = []
                files = snapshot_files.get(snapshot_dict['code'])
                if files:
                    for fl in files:
                        files_list.append(server.server._get_sobject_dict(fl))
                snapshot_dict['__files__'] = files_list
                snapshots_list.append(snapshot_dict)
            else:
                # limiting snapshots to just latest version and versionless
                if snapshot.get_version() in [-1, 0, '-1', '0'] or snapshot.is_latest():
                    snapshot_dict = get_sobject_dict(snapshot)
                    files_list = []
                    files = snapshot_files.get(snapshot_dict['code'])
                    if files:
                        for fl in files:
                            files_list.append(server.server._get_sobject_dict(fl))
                    snapshot_dict['__files__'] = files_list
                    snapshots_list.append(snapshot_dict)

        sobject['__snapshots__'] = snapshots_list

    return json.dumps(result, separators=(',', ':'))


def query_sobjects(search_type, filters=[], order_bys=[], project_code=None, limit=None, offset=None, get_all_snapshots=False, check_snapshots_updates=False):
    """

    :param search_type:
    :param filters:
    :param order_bys:
    :param project_code:
    :param limit:
    :param offset:
    :param get_all_snapshots:
    :param check_snapshots_updates: tuples list [('CODE000000', '2019.11.10 00:00:00'),] Checks for new snapshots to date, including related children
    :return:
    """
    import json
    from pyasm.search import Search, SearchKey
    from pyasm.biz import Snapshot
    from pyasm.biz import Schema

    if project_code:
        server.set_project(project_code)

    if check_snapshots_updates:
        schema = Schema.get()
        splitted_search_type = server.split_search_key(search_type)[0]
        related_search_types = schema.get_related_search_types(splitted_search_type, 'children')
        check_snapshots_updates_dict = dict(check_snapshots_updates)

    def get_sobject_dict(sobject):
        search_key = SearchKey.get_by_sobject(sobject, use_id=False)
        sobj = sobject.get_data()
        sobj['__search_key__'] = search_key

        return sobj

    if search_type.startswith('sthpw'):
        splitted_search_type = search_type
    else:
        splitted_search_type, project_code = server.split_search_key(search_type)

    # Getting count of all sobjects of this stype
    search = Search(splitted_search_type)
    total_sobjects_count = search.get_count()

    # sobjects_dicts_list = []
    # total_sobjects_query_count = 0

    # # getting only related sobjects of instance type given
    # if instance_type:
    #     search = Search(related_type)
    #     sobject_code = None
    #     for fltr in filters:
    #         if fltr[0] == 'code':
    #             sobject_code = fltr[-1]
    #             break
    #     search_key = server.build_search_key(related_type, sobject_code, project_code)
    #     # return search_key
    #     sobject = search.get_by_search_key(search_key)
    #
    #     search = Search(splitted_search_type)
    #
    #     if limit:
    #         search.set_limit(limit)
    #
    #     if offset:
    #         search.set_offset(offset)
    #
    #     search.add_relationship_filter(sobject)
    #
    #     related_sobjects = search.get_sobjects()
    #
    #     total_sobjects_query_count = search.get_count()
    #
    #     if related_sobjects:
    #         for related_sobject in related_sobjects:
    #             sobjects_dicts_list.append(get_sobject_dict(related_sobject))
    # else:
    # checking if search filters have expression and separate it
    expressions_filters_list = []
    filters_list = []

    for fltr in filters:
        if fltr[0] == '_expression':
            expressions_filters_list.append((fltr[1], fltr[2]))
        else:
            filters_list.append(fltr)

    # now evaluate all expressions and add them to our search
    search.add_op('begin')
    # search.add_op('and')

    if filters_list:
        search.add_op_filters(filters_list)

    if order_bys:
        for order_by in order_bys:
            search.add_order_by(order_by)

    if expressions_filters_list:

        for op, expression_filter in expressions_filters_list:
            eval_sobjects = Search.eval(expression_filter)
            if eval_sobjects:
                search.add_relationship_filters(eval_sobjects, op=op)
            elif op == 'in':
                search.set_null_filter()

    total_sobjects_query_count = search.get_count()

    if limit:
        search.set_limit(limit)

    if offset:
        search.set_offset(offset)

    sobjects_list = search.get_sobjects()

    sobjects_dicts_list = server.server._get_sobjects_dict(sobjects_list)

    result = {
        'total_sobjects_count': total_sobjects_count,
        'total_sobjects_query_count': total_sobjects_query_count,
        'sobjects_list': sobjects_dicts_list,
        'limit': limit,
        'offset': offset,
    }
    have_search_code = False
    if sobjects_dicts_list:
        if sobjects_dicts_list[0].get('code'):
            have_search_code = True

    for sobject_dict, sobject in zip(sobjects_dicts_list, sobjects_list):

        if check_snapshots_updates:
            timestamp = check_snapshots_updates_dict.get(sobject_dict.get('code'))
            if timestamp:
                all_related_sobjects_list = []

                for related_search_type in related_search_types:
                    all_related_sobjects_list.extend(sobject.get_related_sobjects(related_search_type))

                snapshot_search = Search('sthpw/snapshot')
                snapshot_search.add_relationship_filters(all_related_sobjects_list, op='in')
                snapshot_search.set_limit(1)

                snapshot_search.add_op_filters([('timestamp', 'is after', timestamp)])
                snapshot_search.add_op_filters([('login', '!=', server.get_login())])
                if snapshot_search.get_sobjects():
                    sobject_dict['__have_updates__'] = True

        search = Search('sthpw/note')
        if have_search_code:
            search.add_op_filters(
                [('process', 'publish'), ('search_type', search_type), ('search_code', sobject_dict['code'])])
        else:
            search.add_op_filters(
                [('process', 'publish'), ('search_type', search_type), ('search_id', sobject_dict['id'])])

        sobject_dict['__notes_count__'] = search.get_count()

        search = Search('sthpw/task')
        if have_search_code:
            search.add_op_filters([('search_type', search_type), ('search_code', sobject_dict['code'])])
        else:
            search.add_op_filters([('search_type', search_type), ('search_id', sobject_dict['id'])])

        sobject_dict['__tasks_count__'] = search.get_count()

        search = Search('sthpw/snapshot')

        snapshots_filters = [('search_type', search_type)]
        if have_search_code:
            snapshots_filters.append(('search_code', sobject_dict['code']))
        else:
            snapshots_filters.append(('search_id', sobject_dict['id']))

        if not get_all_snapshots:
            snapshots_filters.append(('process', ['icon', 'attachment', 'publish']))
        search.add_op_filters(snapshots_filters)

        snapshots = search.get_sobjects()

        snapshot_files = Snapshot.get_files_dict_by_snapshots(snapshots)

        snapshots_list = []
        for snapshot in snapshots:
            if get_all_snapshots:
                snapshot_dict = get_sobject_dict(snapshot)
                files_list = []
                files = snapshot_files.get(snapshot_dict['code'])
                if files:
                    for fl in files:
                        files_list.append(server.server._get_sobject_dict(fl))
                snapshot_dict['__files__'] = files_list
                snapshots_list.append(snapshot_dict)
            else:
                # limiting snapshots to just latest version and versionless
                if snapshot.get_version() in [-1, 0, '-1', '0'] or snapshot.is_latest():
                    snapshot_dict = get_sobject_dict(snapshot)
                    files_list = []
                    files = snapshot_files.get(snapshot_dict['code'])
                    if files:
                        for fl in files:
                            files_list.append(server.server._get_sobject_dict(fl))
                    snapshot_dict['__files__'] = files_list
                    snapshots_list.append(snapshot_dict)

        sobject_dict['__snapshots__'] = snapshots_list

    return json.dumps(result, separators=(',', ':'))


def insert_sobjects(search_type, project_code, data, metadata={}, parent_key=None, instance_type=None, info={}, use_id=False, triggers=True):

    from pyasm.search import SearchType

    server.set_project(project_code)

    result = server.insert(search_type, data, metadata, parent_key, info, use_id, triggers)

    if instance_type:
        instance_search_type, instance_code = server.split_search_key(result['__search_key__'])
        parent_search_type, parent_code = server.split_search_key(parent_key)

        dst_sobject= server.query(parent_search_type, [('code', parent_code)], return_sobjects=True)[0]

        src_sobject = server.query(instance_search_type, [('code', instance_code)], return_sobjects=True)[0]

        instance = SearchType.create(instance_type)
        instance.add_related_connection(src_sobject, dst_sobject)

        instance.commit()

        return result
    else:
        return result


def insert_instance_sobjects(search_key, project_code, parent_key=None, instance_type=None):

    from pyasm.search import SearchType

    server.set_project(project_code)

    instance_search_type, instance_code = server.split_search_key(search_key)
    parent_search_type, parent_code = server.split_search_key(parent_key)

    dst_sobject= server.query(parent_search_type, [('code', parent_code)], return_sobjects=True)[0]

    src_sobject = server.query(instance_search_type, [('code', instance_code)], return_sobjects=True)[0]

    instance = SearchType.create(instance_type)
    instance.add_related_connection(src_sobject, dst_sobject)

    instance.commit()

    return 'ok'


def edit_multiple_instance_sobjects(project_code, insert_search_keys=[], exclude_search_keys=[], parent_key=None, instance_type=None):

    from pyasm.search import SearchType

    server.set_project(project_code)

    for search_key in insert_search_keys:

        child_search_type, child_code = server.split_search_key(search_key)
        parent_search_type, parent_code = server.split_search_key(parent_key)

        dst_sobject= server.query(parent_search_type, [('code', parent_code)], return_sobjects=True)[0]
        src_sobject = server.query(child_search_type, [('code', child_code)], return_sobjects=True)[0]

        instance = SearchType.create(instance_type)
        instance.add_related_connection(src_sobject, dst_sobject)
        instance.commit()

    for search_key in exclude_search_keys:

        child_search_type, child_code = server.split_search_key(search_key)
        parent_search_type, parent_code = server.split_search_key(parent_key)

        child_sobject = server.query(child_search_type, [('code', child_code)], return_sobjects=True)[0]
        parent_sobject = server.query(parent_search_type, [('code', parent_code)], return_sobjects=True)[0]

        child_sobject.remove_instance(parent_sobject)

    return 'ok'


def get_virtual_snapshot_extended(search_key, context, files_dict, snapshot_type="file", is_revision=False, level_key=None, keep_file_name=False, explicit_filename=None, version=None, update_versionless=True, ignore_keep_file_name=False, checkin_type='file'):
    '''creates a virtual snapshot and returns a path that this snapshot
    would generate through the naming conventions''

    @params
    snapshot creation:
    -----------------
    search_key - a unique identifier key representing an sobject
    context - the context of the checkin
    snapshot_type - [optional] descibes what kind of a snapshot this is.
        More information about a snapshot type can be found in the
        prod/snapshot_type sobject
    level_key - the unique identifier of the level that this
        is to be checked into

    path creation:
    --------------
    file_type: the type of file that will be checked in.  Some naming
        conventions make use of this information to separate directories
        for different file types
    file_name: the desired file name of the preallocation.  This information
        may be ignored by the naming convention or it may use this as a
        base for the final file name
    ext: force the extension of the file name returned

    @return
    path as determined by the naming conventions
    '''
    # getting virtual snapshots
    import json
    from pyasm.biz import Snapshot
    from pyasm.biz import Project
    from pyasm.search import SearchType, SearchKey, Search
    api = server.server

    sobject = SearchKey.get_by_search_key(search_key)

    # get the level object
    if level_key:
        levels = api._get_sobjects(level_key)
        level = levels[0]
        level_type = level.get_search_type()
        level_id = level.get_id()
    else:
        level_type = None
        level_id = None

    description = "No description"
    files_dict = json.loads(files_dict)

    # this is only to avoid naming intersection
    if checkin_type == 'file':
        if len(files_dict) > 1 and not ignore_keep_file_name:
            keep_file_name = True

    # if checkin_type == 'multi_file':
    #     keep_file_name = False

    # if len(set(file_type)) != 1:
    #     keep_file_name = False

    def get_max_version(context, search_key):
        # faster way to get max snapshot version
        search = Search('sthpw/snapshot')
        search_type, search_code = server.split_search_key(search_key)
        search.add_op_filters([('context', context), ('search_code', search_code), ('search_type', search_type)])
        snaps = search.get_sobjects()
        versions = []
        for sn in snaps:
            versions.append(sn.get_attr_value('version'))

        if versions:
            return max(versions)

    if not version:
        ver = get_max_version(context=context, search_key=search_key)
        if ver is not None:
            if is_revision:
                version = int(ver)
            else:
                version = int(ver) + 1
        else:
            version = 1

    file_naming = Project.get_file_naming()
    file_naming.set_sobject(sobject)

    snapshot_versioned = Snapshot.create(sobject, snapshot_type=snapshot_type, context=context, description=description,
                                         is_revision=is_revision, level_type=level_type, level_id=level_id,
                                         commit=False, version=version)

    if is_revision:
        snapshot_versioned.set_value('version', version)

    if update_versionless:
        snapshot_versionless = Snapshot.create(sobject, snapshot_type=snapshot_type, context=context,
                                               description=description, is_revision=False, level_type=level_type,
                                               level_id=level_id, commit=False, version=-1)

    def prepare_filename(filenaming, f_l, ext, postfix, metadata):

        if keep_file_name:
            file_type = filenaming.get_file_type()
            if file_type in ['web', 'icon']:
                postfix = file_type
            if postfix:
                result_file_name = f_l + '_' + postfix + '.' + ext
            else:
                if ext:
                    result_file_name = f_l + '.' + ext
                else:
                    result_file_name = f_l
        else:
            name_ext = filenaming.get_file_name()

            # filenaming.get_file_name()
            if postfix:
                result_file_name = name_ext.replace(filenaming.get_ext(), '_{0}.{1}'.format(postfix, ext))
            else:
                result_file_name = name_ext

        # first_part = result_file_name.replace(filenaming.get_ext(), '')
        first_part = result_file_name.split('.')
        if len(first_part) > 1:
            first_part = '.'.join(first_part[:-1])
        else:
            first_part = first_part[0]

        if metadata:
            return first_part, metadata.get('name_part'), filenaming.get_ext()
        else:
            return first_part, '', filenaming.get_ext()

    def prepare_folder(d, sub):
        if sub:
            return d + '/' + sub
        else:
            return d

    file_object = SearchType.create("sthpw/file")

    result_list = []

    # fl::file, t::type, e::extension, s::sub-folder, p::postfix, m::metadata
    for fl, val in files_dict:

        result_dict = {'versionless': {'paths': [], 'names': []}, 'versioned': {'paths': [], 'names': []}}

        if not fl:
            fl = sobject.get_code()
        elif not fl:
            fl = sobject.get_name()
        elif not fl:
            fl = "unknown"

        if explicit_filename:
            keep_file_name = True
            fl = explicit_filename

        for t, e, s, p in zip(val['t'], val['e'], val['s'], val['p']):
            file_object.set_value("file_name", fl)
            file_object.set_value("type", t)
            if val['m']:
                file_object.set_value("metadata", json.dumps(val['m'], separators=(',', ':')))

            file_naming.set_snapshot(snapshot_versioned)
            # snapshot_versioned.add_file('', t)
            file_naming.set_ext(e)
            file_naming.set_file_object(file_object)
            result_dict['versioned']['paths'].append(prepare_folder(snapshot_versioned.get_dir('relative', file_type=str(t), file_object=file_object), s))
            result_dict['versioned']['names'].append(prepare_filename(file_naming, fl, e, p, val['m']))
            # result_dict['versioned']['names'].append(file_naming.get_file_name())

            if update_versionless:
                file_naming.set_snapshot(snapshot_versionless)
                # snapshot_versionless.add_file('', t)
                file_naming.set_ext(e)
                file_naming.set_file_object(file_object)

                result_dict['versionless']['paths'].append(prepare_folder(snapshot_versionless.get_dir('relative', file_type=str(t), file_object=file_object), s))
                result_dict['versionless']['names'].append(prepare_filename(file_naming, fl, e, p, val['m']))
                # result_dict['versionless']['names'].append(file_naming.get_file_name())

        result_list.append((fl, result_dict))

    return json.dumps(result_list, separators=(',', ':'))


def create_snapshot_extended(search_key, context, project_code=None, snapshot_type=None, is_revision=False, is_latest=True, is_current=False, description=None, version=None, level_key=None, update_versionless=True, only_versionless=False, keep_file_name=True, repo_name=None, files_info=None, mode=None, create_icon=False):
    import json
    from pyasm.biz import Snapshot
    from pyasm.checkin import FileAppendCheckin
    from pyasm.search import Search
    from pyasm.common import Environment

    if project_code:
        server.set_project(project_code)

    # mode = 'local'

    api = server.server

    sobject = api._get_sobjects(search_key)[0]

    # get the level object
    if level_key:
        levels = api._get_sobjects(level_key)
        level = levels[0]
        level_type = level.get_search_type()
        level_id = level.get_id()
    else:
        level_type = None
        level_id = None

    if not description:
        description = 'No description'
    if not snapshot_type:
        snapshot_type = 'file'

    files_info = json.loads(files_info, strict=False)

    def get_max_version(context, search_key):
        # faster way to get max snapshot version
        search = Search('sthpw/snapshot')
        search_type, search_code = server.split_search_key(search_key)
        search.add_op_filters([('context', context), ('search_code', search_code), ('search_type', search_type)])
        snaps = search.get_sobjects()
        versions = []
        for sn in snaps:
            versions.append(sn.get_attr_value('version'))

        if versions:
            return max(versions)

    if not version:
        ver = get_max_version(context=context, search_key=search_key)
        if ver is not None:
            if is_revision:
                version = int(ver)
            else:
                version = int(ver) + 1
        else:
            version = 1

    snapshot = Snapshot.create(sobject, snapshot_type=snapshot_type, context=context, description=description, is_revision=is_revision, is_latest=is_latest, is_current=is_current, level_type=level_type, level_id=level_id, commit=False, version=version)

    if repo_name:
        snapshot.set_value('repo', repo_name)
    if is_latest:
        snapshot.set_value('is_latest', 1)
    if is_current:
        snapshot.set_value('is_current', 1)

    if is_revision:
        snapshot_code = server.eval("@GET(sthpw/snapshot['version', {0}].code)".format(version),
                                    search_keys=[search_key], single=True)
        revision = server.eval("@MAX(sthpw/snapshot.revision)",
                               search_keys=['sthpw/snapshot?code={0}'.format(snapshot_code)])

        snapshot.set_value('version', version)
        snapshot.set_value('revision', revision + 1)

    if mode == 'upload':
        checkin_mode = 'uploaded'

        # SOME KIND OF HACK!
        if is_revision:
            checkin_mode = 'preallocate'

        env = Environment.get()
        lib_dir = env.get_upload_dir()

        file_paths = []
        original_files_paths = []
        file_types = []

        for metadata, types in zip(files_info['version_metadata'], files_info['files_types']):
            original_files_paths.append('{0}/{1}.{2}'.format(lib_dir, metadata['filename'], metadata['new_file_ext']))
            file_paths.append('{0}/{1}.{2}'.format(lib_dir, metadata['new_filename'], metadata['new_file_ext']))
            file_types.append(types)

        snapshot.commit(triggers=True, log_transaction=True)

        # we keep file name as we already got name from virtual snapshot
        checkin = FileAppendCheckin(snapshot.get_code(), file_paths, file_types,
                                    keep_file_name=True, mode=checkin_mode, source_paths=file_paths,
                                    checkin_type='auto', do_update_versionless=False)

        checkin.file_sizes = files_info['file_sizes']
        checkin.execute()

        files_list = checkin.get_file_objects()

        for i, fl in enumerate(files_list):
            fl.set_value(name='source_path', value=original_files_paths[i])
            fl.set_value(name='metadata', value=json.dumps(files_info['version_metadata'][i], separators=(',', ':')))
            fl.commit(triggers=False, log_transaction=False)

        if update_versionless:

            snapshot.update_versionless('latest', sobject=sobject, checkin_type='strict')
            versionless_snapshot = snapshot.get_by_sobjects([sobject], context, version=-1)

            if repo_name:
                versionless_snapshot[0].set_value('repo', repo_name)
            versionless_snapshot[0].set_value('login', snapshot.get_attr_value('login'))
            versionless_snapshot[0].set_value('timestamp', snapshot.get_attr_value('timestamp'))
            versionless_snapshot[0].set_value('description', description)
            versionless_snapshot[0].commit(triggers=False, log_transaction=False)
            file_objects = versionless_snapshot[0].get_all_file_objects()

            for i, file_object in enumerate(file_objects):
                file_object.set_value(name='project_code', value=snapshot.get_project_code())
                file_object.set_value(name='metadata',
                                      value=json.dumps(files_info['versionless_metadata'][i], separators=(',', ':')))
                file_object.set_value(name='source_path', value=original_files_paths[i])
                file_object.commit(triggers=False, log_transaction=False)

    elif mode == 'inplace':

        if only_versionless:
            snapshot.set_value('version', -1)
            snapshot.set_value('is_current', 1)
            snapshot.set_value('is_latest', 1)
            update_versionless = False
            existing_versionless_snapshot = snapshot.get_by_sobjects([sobject], context, version=-1)
            if existing_versionless_snapshot:
                from tactic.ui.tools import DeleteCmd
                cmd = DeleteCmd(sobject=existing_versionless_snapshot[0], auto_discover=True)
                cmd.execute()

            snapshot.commit(triggers=True, log_transaction=True)

            checkin = FileAppendCheckin(snapshot.get_code(), files_info['versionless_files'], files_info['files_types'],
                                        keep_file_name=True, mode=mode, source_paths=files_info['versionless_files'],
                                        checkin_type='auto', do_update_versionless=False)
            checkin.execute()

            files_list = checkin.get_file_objects()

            for i, fl in enumerate(files_list):
                fl.set_value(name='st_size', value=files_info['file_sizes'][i])
                fl.set_value(name='relative_dir', value=files_info['versionless_files_paths'][i])
                fl.set_value(name='metadata', value=json.dumps(files_info['versionless_metadata'][i], separators=(',', ':')))
                fl.commit(triggers=False, log_transaction=False)

        else:

            snapshot.commit(triggers=True, log_transaction=True)
            # we keep file name as we already got name from virtual snapshot
            checkin = FileAppendCheckin(snapshot.get_code(), files_info['version_files'], files_info['files_types'],
                                        keep_file_name=True, mode=mode, source_paths=files_info['version_files'],
                                        checkin_type='auto', do_update_versionless=False)
            checkin.execute()

            files_list = checkin.get_file_objects()

            for i, fl in enumerate(files_list):
                fl.set_value(name='st_size', value=files_info['file_sizes'][i])
                fl.set_value(name='relative_dir', value=files_info['version_files_paths'][i])
                fl.set_value(name='metadata', value=json.dumps(files_info['version_metadata'][i], separators=(',', ':')))
                fl.commit(triggers=False, log_transaction=False)

        if update_versionless:
            existing_versionless_snapshot = snapshot.get_by_sobjects([sobject], context, version=-1)
            if existing_versionless_snapshot:
                from tactic.ui.tools import DeleteCmd
                cmd = DeleteCmd(sobject=existing_versionless_snapshot[0], auto_discover=True)
                cmd.execute()

            versionless = Snapshot.create(sobject, snapshot_type=snapshot_type, context=context, description=description,
                                       is_revision=is_revision, is_latest=is_latest, is_current=is_current,
                                       level_type=level_type, level_id=level_id, commit=False, version=version)

            if repo_name:
                versionless.set_value('repo', repo_name)
                versionless.set_value('version', -1)
                # snapshot.set_value('is_current', 1)
                versionless.set_value('is_latest', 1)

            versionless.commit(triggers=False, log_transaction=False)

            checkin = FileAppendCheckin(versionless.get_code(), files_info['versionless_files'], files_info['files_types'],
                                        keep_file_name=True, mode=mode, source_paths=files_info['versionless_files'],
                                        checkin_type='auto', do_update_versionless=False)
            checkin.execute()

            from pyasm.checkin import SnapshotBuilder
            builder = SnapshotBuilder()

            files_list = checkin.get_file_objects()

            for i, fl in enumerate(files_list):
                fl.set_value(name='st_size', value=files_info['file_sizes'][i])
                fl.set_value(name='relative_dir', value=files_info['versionless_files_paths'][i])
                fl.set_value(name='metadata', value=json.dumps(files_info['versionless_metadata'][i], separators=(',', ':')))
                info = {'type': files_info['files_types'][i]}
                builder.add_file(fl, info=info)
                fl.commit(triggers=False, log_transaction=False)

            builder.add_root_attr('ref_snapshot_code', snapshot.get_code())

            versionless.set_value("snapshot", builder.to_string())

            versionless.commit(triggers=False, log_transaction=False)

    return 'OK'

"""

# get all snapshots dicts with files dicts ver 1

import collections
from pyasm.search import Search
from pyasm.prod.service import ApiXMLRPC
xml_api = ApiXMLRPC()
search = Search('sthpw/snapshot')
filters = [('process', [u'Concept', u'Sculpt', u'Rigging', u'Hairs', u'Texturing', u'Final', u'Modeling', u'Dynamics', u'Blocking', 'icon', 'attachment', 'publish']), ('project_code', u'the_pirate'), ('search_code', [u'CHARACTERS00003', u'CHARACTERS00002', u'CHARACTERS00001'])]
search.add_op_filters(filters)
snapshots_sobjects = search.get_sobjects()

snapshots_def = collections.defaultdict(list)
files_def = collections.defaultdict(list)

for snapshot in snapshots_sobjects:
   snapshot_dict = xml_api.get_sobject_dict(snapshot)
   snapshot_files = snapshot.get_files_by_snapshots([snapshot])
   files_list = []
   for file in snapshot_files:
      files_list.append(xml_api.get_sobject_dict(file))
   snapshots_def[snapshot_dict['code']].append(snapshot_dict)
   files_def[snapshot_dict['code']].append(files_list)

return 'OK'


# get all snapshots dicts with files dicts ver 2 (Faster)

import collections
from pyasm.search import Search
from pyasm.biz import Snapshot
from pyasm.prod.service import ApiXMLRPC

xml_api = ApiXMLRPC()
search = Search('sthpw/snapshot')
filters = [('process',
            [u'Concept', u'Sculpt', u'Rigging', u'Hairs', u'Texturing', u'Final', u'Modeling', u'Dynamics',
             u'Blocking', 'icon', 'attachment', 'publish']), ('project_code', u'the_pirate'),
           ('search_code', [u'CHARACTERS00003', u'CHARACTERS00002', u'CHARACTERS00001'])]
search.add_op_filters(filters)
snapshots_sobjects = search.get_sobjects()
snapshots_files = Snapshot.get_files_dict_by_snapshots(snapshots_sobjects)

snapshots_def = collections.defaultdict(list)

for snapshot in snapshots_sobjects:
    snapshot_dict = xml_api.get_sobject_dict(snapshot, use_id=True)
    snapshot_files = snapshots_files.get(snapshot_dict['code'])
    files_list = []
    if snapshot_files:
        for file in snapshot_files:
            files_list.append(xml_api.get_sobject_dict(file, use_id=True))
    snapshot_dict['files'] = files_list
    snapshots_def[snapshot_dict['code']].append(snapshot_dict)

return snapshots_def.values()

"""

# from pyasm.biz import Snapshot
# import time
# start = time.time()
# api = server.server
# search_key = 'cgshort/props?project=portfolio&code=PROPS00012'
#
# for i in range(100):
#     sobjects = api._get_sobjects(search_key)
#     sobject = sobjects[0]
#     Snapshot.create(sobject, snapshot_type='file', context='publish', description='', is_revision=False, level_type=None, level_id=None, commit=False, version=None)
#
# end = time.time()
# return(end - start)
# 13.653764963150024 CHERRYPY


# class_name = 'tactic.ui.manager.EditElementDefinitionWdg'
#
# args = {
# 	'config_xml': '',
# 	'element_name': 'priority',
# 	'path': '/Edit/priority',
# 	'search_type': 'sthpw/task',
# 	'view': 'edit_definition',
# }
# args_array = []
# from pyasm.common import Common
# from pyasm.common import Container
# widget = Common.create_from_class_path(class_name, args_array, args)
#
# Container.put("request_top_wdg", widget)
# html = widget.get_buffer_display()
# m = Container.get_instance()
# print m.get('WidgetConfigView:display_options_cache')
# return str(m.info)
#
# #widget_html = server.get_widget(class_name, args, [])
# #return widget_html

# class_name = 'tactic.ui.panel.EditWdg'
#
# args = {
# 	'input_prefix': 'edit',
# 	'search_key': 'cgshort/scenes?project=the_pirate&id=2',
# 	'view': 'edit',
# }
# args_array = []
# from pyasm.common import Common
# from pyasm.common import Container
# widget = Common.create_from_class_path(class_name, args_array, args)
#
# Container.put("request_top_wdg", widget)
# html = widget.get_buffer_display()
# m = Container.get_instance()
# #print m.get('WidgetConfigView:display_options_cache')
# return str(m.get_data())
#
# #widget_html = server.get_widget(class_name, args, [])
# #return widget_html


# class_name = 'tactic.ui.panel.EditWdg'
#
# args = {
# 	'input_prefix': 'edit',
# 	'search_key': 'cgshort/textures?project=the_pirate&id=1',
# 	'view': 'edit',
# }
# args_array = []
# from pyasm.common import Common
# from pyasm.common import Container
# widget = Common.create_from_class_path(class_name, args_array, args)
#
# Container.put("request_top_wdg", widget)
# #widget.get_buffer_display()
# widget.explicit_display()
# m = Container.get_instance()
# return m.get_data().keys()
# #return (m.get('WidgetConfigView:display_options_cache'))
# return str(m.get("Expression:@GET(cgshort/props.name)|['cgshort/props']|[]"))
# return str(m.get("Expression:@GET(cgshort/applications_list.name)|['cgshort/applications_list']|[]"))
# return str(m.get("Expression:@GET(cgshort/applications_list.code)|['cgshort/applications_list']|[]"))
# return str(m.get("Expression:@GET(cgshort/props.name)|['cgshort/props']|[]"))
# return str(m.get("Expression:@GET(cgshort/props.code)|['cgshort/props']|[]"))
#
# widget_html = server.get_widget(class_name, args, [])
# return widget_html


# class_name = 'tactic.ui.panel.EditWdg'
#
# args = {
# 	'input_prefix': 'edit',
# 	'search_key': 'cgshort/textures?project=the_pirate&id=1',
# 	'view': 'edit',
# }
# args_array = []
# from pyasm.common import Common
# from pyasm.common import Container
# widget = Common.create_from_class_path(class_name, args_array, args)
#
# Container.put("request_top_wdg", widget)
# #widget.get_buffer_display()
# widget.explicit_display()
# edit_widgets = widget.get_widgets()
# return (edit_widgets[5].values)
# m = Container.get_instance()
# return m.get_data().keys()
# return (m.get('WidgetConfigView:display_options_cache'))
# return str(m.get("Expression:@GET(cgshort/props.name)|['cgshort/props']|[]"))
# return str(m.get("Expression:@GET(cgshort/applications_list.name)|['cgshort/applications_list']|[]"))
# return str(m.get("Expression:@GET(cgshort/applications_list.code)|['cgshort/applications_list']|[]"))
# return str(m.get("Expression:@GET(cgshort/props.name)|['cgshort/props']|[]"))
# return str(m.get("Expression:@GET(cgshort/props.code)|['cgshort/props']|[]"))
#
# widget_html = server.get_widget(class_name, args, [])
# return widget_html

# from tactic.ui.app import SearchWdg
# server.set_project('dolly3d')
#
# search_type = 'complex/scenes'
# view = 'auto_search:table'
#
# filter = [
#  {'filter_mode': 'or', 'prefix': 'filter_mode'},
#  {'prefix': 'quick', 'quick_enabled': '', 'quick_search_text': ''},
#  {'main_body_column': 'name',
#   'main_body_enabled': 'on',
#   'main_body_relation': 'is',
#   'main_body_value': 'Episode01',
#   'prefix': 'main_body'},
#  {'main_body_column': 'description',
#   'main_body_enabled': '',
#   'main_body_relation': 'contains',
#   'main_body_value': 'description',
#   'prefix': 'main_body'},
#  {'main_body_column': 'keywords',
#   'main_body_enabled': '',
#   'main_body_relation': 'starts with',
#   'main_body_value': 'epica',
#   'prefix': 'main_body'},
#  {'children_column': 'assigned',
#   'children_enabled': '',
#   'children_relation': 'is',
#   'children_search_type': 'sthpw/task',
#   'children_value': '{$LOGIN}',
#   'prefix': 'children'},
#  {'levels': [0, 0],
#   'modes': ['sobject', 'sobject'],
#   'ops': ['and', 'and'],
#   'prefix': 'search_ops'},
#  {'': '', 'prefix': 'keyword', 'value': ''},
#  {'Next': '',
#   'Prev': '',
#   'Showing': '',
#   'Showing_last_search_offset': '0',
#   'custom_limit': '',
#   'limit_select': '50',
#   'prefix': 'search_limit',
#   'search_limit': '20'},
#   ]
#
# search_wdg = SearchWdg(search_type=search_type, use_last_search=False, view=view, filter=filter)
#
# #search_wdg.explicit_display()
#
# search = search_wdg.search
# sobjects = search.get_sobjects()
#
# return str(search_wdg.filters[1].prefix)
