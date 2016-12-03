# Internal server-side sctipts

import global_functions as gf


def prepare_serverside_script(func, kwargs, return_dict=True, has_return=True, shrink=True):
    import inspect
    func_lines = inspect.getsourcelines(func)
    if has_return:
        run_command = func_lines[0][0].replace('def ', 'return ')[:-2]
    else:
        run_command = func_lines[0][0].replace('def ', '')[:-2]

    # i don't want 're' here, so try to understand logic, with love to future me :-*
    # TODO multiline bug
    val_split = run_command.split(',')
    left_part = val_split[0].split('(')
    right_part = val_split[-1][:-1]
    full_list = [left_part[1]] + val_split[1:-1] + [right_part]

    all_vars = []
    for split in full_list:
        # split keys and values, and add to list keys which values need update
        fltr = split.split('=')[0].replace(' ', '')
        if fltr in kwargs.keys():
            all_vars.append(fltr)

    for i, k in enumerate(all_vars):
        for key, val in kwargs.items():
            if k == key:
                all_vars[i] = '{0}={1}'.format(key, repr(val))

    var_stitch = ', '.join(all_vars)
    ready_run_command = '{0}({1})'.format(run_command[:run_command.find('(')], var_stitch)

    code = ''.join(func_lines[0]) + ready_run_command

    # print code

    if shrink:
        code = gf.minify_code(source=code, pack=False)

    # print code

    if return_dict:
        code_dict = {
            'code': code
        }
        return code_dict
    else:
        return code


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
        item_values = i_widget.get_values()
        if item_values:
            widget_dict['values'] = item_values
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


def get_notes_and_stypes_counts(process, search_key, stypes_list):
    # getting notes by search_type process and count of stypes from stypes_list
    from pyasm.search import Search

    search_type, search_code = server.split_search_key(search_key)

    cnt = {
        'notes': {},
        'stypes': {},
    }
    for p in process:
        search = Search('sthpw/note')
        search.add_op_filters([('process', p), ('search_type', search_type), ('search_code', search_code)])
        cnt['notes'][p] = search.get_count()

    for stype in stypes_list:
        search = Search(stype)
        search.add_parent_filter(search_key)
        cnt['stypes'][stype] = search.get_count()

    return cnt


def query_search_types_extended(project_code, namespace):
    """
    This crazy stuff made to execute queries on server
    All needed info is getting almost half time faster
    :return:
    """
    # TODO remove query, and dig deeper to get more info about pipelines, processes, stypes
    # from pyasm.search import Search
    # from pyasm.biz import Pipeline
    #
    # search_type = 'cgshort/scenes'
    # search = Search("sthpw/pipeline")
    # search.add_filter("search_type", search_type)
    # pipelines = search.get_sobjects()
    #
    # return str(pipelines)
    import json
    from pyasm.biz import Project
    api = server.server
    get_sobject_dict = api.get_sobject_dict

    prj = Project.get_by_code(project_code)

    stypes = prj.get_search_types()

    all_stypes = []
    for stype in stypes:
        stype_dict = get_sobject_dict(stype)
        stype_dict['column_info'] = stype.get_column_info(stype.get_code())
        all_stypes.append(stype_dict)

    # getting pipeline process
    # stypes_codes = []
    # for stype in all_stypes:
    #     stypes_codes.append(stype['code'])
    # stypes_codes.append('sthpw/task')
    search_type = 'sthpw/pipeline'
    # filters = [('search_type', stypes_codes), ('project_code', project_code)]
    filters = [('project_code', project_code)]
    stypes_pipelines = server.query(search_type, filters, return_sobjects=True)

    # getting processes info
    pipelines = []
    for stype in stypes_pipelines:
        stypes_dict = stype.get_sobject_dict()

        processes = []
        for process in stype.get_process_names():
            process_sobject = stype.get_process_sobject(process)
            if process_sobject:
                processes.append(api.get_sobject_dict(process_sobject))

        task_processes = []
        for process in stype.get_processes():
            process_obj = process.get_task_pipeline()
            if process_obj != 'task':
                task_processes.append(process_obj)

        stypes_dict['tasks_processes'] = task_processes
        stypes_dict['stypes_processes'] = processes
        pipelines.append(stypes_dict)

    # getting project schema
    schema = server.query('sthpw/schema', [('code', project_code)])

    result = {'schema': schema, 'pipelines': pipelines, 'stypes': all_stypes}

    return json.dumps(result, separators=(',', ':'))


def get_virtual_snapshot_extended(search_key, context, snapshot_type="file", is_revision=False, level_key=None, file_type=['main'], file_name=[''], postfixes=None, subfolders=None, keep_file_name=False, ext=[''], version=None):
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
    from pyasm.search import SearchType
    api = server.server

    sobjects = api._get_sobjects(search_key)
    sobject = sobjects[0]

    result_dict = {'versionless': {'paths': [], 'names': []}, 'versioned': {'paths': [], 'names': []}}

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

    if len(file_name) > 1:
        keep_file_name = True
    if len(set(file_type)) != 1:
        keep_file_name = False

    if not postfixes:
        postfixes = []
        for fn in range(len(file_name)):
            postfixes.append('')

    if not subfolders:
        subfolders = []
        for fn in range(len(file_name)):
            subfolders.append('')

    def prepare_filename(filenaming, f_l, ex, postfix):
        if keep_file_name:
            if postfix:
                result_file_name = f_l + '_' + postfix + '.' + ex
            else:
                result_file_name = f_l + '.' + ex
        else:
            name_ext = filenaming.get_file_name()
            if postfix:
                result_file_name = name_ext.replace('.' + ex, '_' + postfix + '.' + ex)
            else:
                result_file_name = name_ext
        return result_file_name

    def prepare_folder(d, sub):
        if sub:
            return d + '/' + sub
        else:
            return d

    for i, fl in enumerate(file_name):
        if not fl:
            fl = sobject.get_code()
            if not fl:
                fl = sobject.get_name()
            if not fl:
                fl = "unknown"

        file_object = SearchType.create("sthpw/file")
        file_object.set_value("file_name", fl)
        file_object.set_value("type", file_type[i])
        file_naming = Project.get_file_naming()
        file_naming.set_sobject(sobject)
        if not version:
            ver = server.eval("@MAX(sthpw/snapshot['context', '{0}'].version)".format(context), search_keys=[search_key])
            if ver:
                version = int(ver) + 1
            else:
                version = 1
        snapshot_versioned = Snapshot.create(sobject, snapshot_type=snapshot_type, context=context, description=description, is_revision=is_revision, level_type=level_type, level_id=level_id, commit=False, version=version)
        file_naming.set_snapshot(snapshot_versioned)
        file_naming.set_ext(ext[i])
        file_naming.set_file_object(file_object)
        result_dict['versioned']['paths'].append(prepare_folder(snapshot_versioned.get_dir('relative', file_type=file_type[i]), subfolders[i]))
        result_dict['versioned']['names'].append(prepare_filename(file_naming, fl, ext[i], postfixes[i]))

        snapshot_versionless = Snapshot.create(sobject, snapshot_type=snapshot_type, context=context, description=description, is_revision=False, level_type=level_type, level_id=level_id, commit=False, version=-1)
        file_naming.set_snapshot(snapshot_versionless)
        file_naming.set_file_object(file_object)
        file_naming.set_ext(ext[i])
        result_dict['versionless']['paths'].append(prepare_folder(snapshot_versionless.get_dir('relative', file_type=file_type[i]), subfolders[i]))
        result_dict['versionless']['names'].append(prepare_filename(file_naming, fl, ext[i], postfixes[i]))

    return json.dumps(result_dict, separators=(',', ':'))


def create_snapshot_extended(search_key, context, snapshot_type=None, is_revision=False, is_latest=True, is_current=False, description=None, version=None, level_key=None, update_versionless=True, file_types=None, file_names=None, file_paths=None, relative_paths=None, source_paths=None, file_sizes=None, exts=None, keep_file_name=True, repo_name=None, virtual_snapshot=None, mode=None, create_icon=False):
    from pyasm.biz import Snapshot
    from pyasm.checkin import FileAppendCheckin
    from pyasm.search import Search

    api = server.server

    sobjects = api._get_sobjects(search_key)
    sobject = sobjects[0]

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

    if mode == 'inplace':
        version_file_paths = []
        versionless_file_paths = []
        version_relative_paths = []
        versionless_relative_paths = []
        for p, fn in zip(virtual_snapshot['versioned']['paths'], virtual_snapshot['versioned']['names']):
            version_file_paths.append('{0}/{1}'.format(p, fn))
            version_relative_paths.append(p)
        for p, fn in zip(virtual_snapshot['versionless']['paths'], virtual_snapshot['versionless']['names']):
            versionless_file_paths.append('{0}/{1}'.format(p, fn))
            versionless_relative_paths.append(p)
    if not version:
        ver = server.eval("@MAX(sthpw/snapshot['context', '{0}'].version)".format(context), search_keys=[search_key])
        if ver:
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

    snapshot.commit(triggers=True, log_transaction=True)

    dir_naming = None
    file_naming = None

    checkin = FileAppendCheckin(snapshot.get_code(), version_file_paths, file_types, keep_file_name=keep_file_name, mode=mode,
                                source_paths=source_paths, dir_naming=dir_naming, file_naming=file_naming,
                                checkin_type='auto', do_update_versionless=False)
    checkin.execute()

    files_list = checkin.get_file_objects()
    for i, fl in enumerate(files_list):
        fl.set_value(name='st_size', value=file_sizes[i])
        fl.set_value(name='relative_dir', value=version_relative_paths[i])
        fl.commit()

    # update_versionless = False

    if update_versionless:
        # snapshot.update_versionless(snapshot_mode='latest', sobject=sobject, checkin_type='auto')
        versionless_snapshot = snapshot.get_by_sobjects([sobject], context, version=-1)
        if not versionless_snapshot:
            versionless_snapshot = [
                Snapshot.create(sobject, snapshot_type=snapshot_type, context=context, description=description,
                                is_revision=False, is_latest=is_latest, level_type=level_type, level_id=level_id,
                                commit=False, version=-1)]
        if repo_name:
            versionless_snapshot[0].set_value('repo', repo_name)

        # file_objects = versionless_snapshot[0].get_all_file_objects()
        # for file_object in file_objects:
        #     file_object.delete(triggers=False)

        search = Search('sthpw/file')
        search.add_op_filters([('snapshot_code', versionless_snapshot[0].get_code())])
        file_objects = search.get_sobjects()
        for file_object in file_objects:
            file_object.delete(triggers=False)

        versionless_snapshot[0].set_value('snapshot', '<snapshot/>')
        versionless_snapshot[0].set_value('login', snapshot.get_attr_value('login'))
        versionless_snapshot[0].set_value('timestamp', snapshot.get_attr_value('timestamp'))
        versionless_snapshot[0].set_value('description', description)
        versionless_snapshot[0].commit(triggers=True, log_transaction=True)
        #snapshot.update_versionless(snapshot_mode='latest', sobject=sobject, checkin_type='auto')

        checkin_versionless = FileAppendCheckin(versionless_snapshot[0].get_code(), versionless_file_paths, file_types, keep_file_name=keep_file_name, mode=mode,
                                    source_paths=source_paths, dir_naming=dir_naming, file_naming=file_naming,
                                    checkin_type='auto', do_update_versionless=False)
        checkin_versionless.execute()

        versionless_files_list = checkin_versionless.get_file_objects()
        for i, fl_versionless in enumerate(versionless_files_list):
            fl_versionless.set_value(name='st_size', value=file_sizes[i])
            fl_versionless.set_value(name='relative_dir', value=versionless_relative_paths[i])
            fl_versionless.commit()

    return str('OKEEDOKEE')

# ['lib', 'client_repo', 'sandbox', 'local_repo', 'web', 'relative', 'custom_blabla']
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