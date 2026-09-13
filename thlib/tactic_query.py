# Internal server-side sctipts

import thlib.global_functions as gf
import ast
import io
import inspect
from pprint import pformat


def _function_source_lines(func):
    """Read a top-level function by name from the current source file.

    ``inspect.getsourcelines`` relies on ``co_firstlineno``.  That offset is
    stale when a running application edits/reloads the source file, which
    previously made unrelated lines get sent to TACTIC as executable code.
    """
    try:
        source_path = inspect.getsourcefile(func) or inspect.getfile(func)
        with io.open(source_path, 'r', encoding='utf-8') as source_file:
            source = source_file.read()
        source_lines = source.splitlines(True)
        module = ast.parse(source, filename=source_path)
        function_nodes = (ast.FunctionDef,)
        if hasattr(ast, 'AsyncFunctionDef'):
            function_nodes += (ast.AsyncFunctionDef,)
        node = next(
            item for item in module.body
            if isinstance(item, function_nodes)
            and item.name == func.__name__
        )
        start = int(node.lineno) - 1
        end = getattr(node, 'end_lineno', None)
        if end is None:
            following = [
                int(item.lineno) - 1 for item in module.body
                if getattr(item, 'lineno', 0) > node.lineno
            ]
            end = min(following) if following else len(source_lines)
            while end > start and not source_lines[end - 1].strip():
                end -= 1
        return source_lines[start:int(end)]
    except Exception:
        return inspect.getsourcelines(func)[0]


def prepare_serverside_script(func, kwargs, return_dict=True, has_return=True, shrink=True, catch_traceback=True):
    func_lines = _function_source_lines(func)

    args_list = []
    for key, arg in kwargs.items():
        if isinstance(arg, str):
            args_list.append(u'{}={}'.format(key, pformat(arg)))
        else:
            # args_list.append(u'{}={}'.format(key, arg))
            # Workaround for slow MAKO with long lines
            args_list.append(u'{}={}'.format(key, pformat(arg)))

    var_stitch = u', '.join(args_list)

    call = u'{0}({1})'.format(func.__name__, var_stitch)
    ready_run_command = (u'return ' + call) if has_return else call
    if catch_traceback:
        traceback = _function_source_lines(get_traceback)
        handle = _function_source_lines(traceback_handle)
        code = u''.join(traceback) + u''.join(handle) + u'@traceback_handle \n' + ''.join(func_lines) + ready_run_command
    else:
        code = u''.join(func_lines) + ready_run_command
    if shrink:
        # minify is a bit slow
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

    def expression_values(expression):
        from pyasm.search import Search

        result = Search.eval(expression, single=False)
        if result is None:
            return []
        if isinstance(result, (list, tuple)):
            return list(result)
        return [result]

    def configured_values(value):
        if value in (None, ''):
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        return str(value).split('|')

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

    temprorary_ignore = []

    for i_widget in input_widgets:
        widget_dict = pop_classes(i_widget.__dict__)
        widget_dict['action_options'] = wdg_config.get_action_options(widget_dict.get('name'))
        widget_dict['class_name'] = i_widget.get_class_name()
        select_options = getattr(i_widget, 'kwargs', None) or {}
        option_labels = configured_values(select_options.get('labels'))
        option_values = configured_values(select_options.get('values'))
        values_expr = (
            select_options.get('values_expr')
            or widget_dict.get('values_expr')
        )
        labels_expr = (
            select_options.get('labels_expr')
            or widget_dict.get('labels_expr')
        )
        if values_expr:
            option_values = expression_values(values_expr)
        if labels_expr:
            option_labels = expression_values(labels_expr)
        if not option_values and not option_labels:
            get_select_values = getattr(
                i_widget, 'get_select_values', None
            )
            if get_select_values:
                native_options = get_select_values()
                if (
                        isinstance(native_options, (list, tuple))
                        and len(native_options) == 2
                        and all(isinstance(item, (list, tuple))
                                for item in native_options)
                ):
                    option_labels = list(native_options[0])
                    option_values = list(native_options[1])
        if option_values or option_labels:
            option_values = list(option_values or [])
            option_labels = list(option_labels or [])
            empty_label = (
                select_options.get('empty') or widget_dict.get('empty')
            )
            empty_flag = str(empty_label or '').strip().lower()
            if (
                empty_flag not in ('', '0', 'false', 'no', 'off')
                and (not option_values or option_values[0] not in ('', None))
            ):
                option_values.insert(0, '')
                option_labels.insert(
                    0, '' if empty_flag in ('1', 'true', 'yes', 'on')
                    else str(empty_label)
                )
            widget_dict['labels'] = option_labels
            widget_dict['values'] = option_values
        display_values = i_widget.get_values()

        if display_values:
            widget_dict['__display_values__'] = display_values
        else:
            # Special cases for different widgets
            if widget_dict['class_name'] == 'tactic.ui.input.process_group_select_wdg.ProcessGroupSelectWdg':
                select_wd = i_widget.get_display()
                select_wd.get_display()
                widget_dict['__display_values__'] = select_wd.__dict__

        # Special cases for different widgets
        if widget_dict['class_name'] == 'tactic.ui.widget.misc_input_wdg.TaskStatusSelectWdg':

            task_pipelines_result = []
            task_pipelines = widget_dict['task_pipelines']
            if task_pipelines:
                for tp in task_pipelines:
                    task_pipelines_result.append(tp.get_code())

            widget_dict['task_pipelines'] = task_pipelines_result

        elif widget_dict['class_name'] == 'tactic.ui.input.pipeline_input_wdg.PipelineInputWdg':
            select_wd = i_widget.get_display()
            select_wd.get_display()
            widget_dict['__display_values__'] = select_wd.__dict__

        if widget_dict['class_name'] not in temprorary_ignore:
            result_dict['InputWidgets'].append(widget_dict)

    return json.dumps(result_dict, separators=(',', ':'))


def ingest_rule_preflight(
        search_type, parent_key, filename, column='name',
        ignore_ext=True, extra_data=None,
        validation_script='',
        process_script='', search_key=''):
    """Run native ingest-rule hooks before TACTIC's IngestUploadCmd.

    The function is serialized and executed inside TACTIC. Keep it
    self-contained and compatible with the Python runtime shipped by TACTIC
    5.0. Object insertion and check-in remain owned by IngestUploadCmd; this
    preflight reproduces the config/ingest_rule script contract.
    """
    import os

    from pyasm.common import Environment
    from pyasm.search import Search, SearchType

    upload_path = os.path.join(Environment.get_upload_dir(), filename)
    if not os.path.isfile(upload_path):
        raise RuntimeError(
            'Uploaded ingest file does not exist: %s' % filename
        )

    mapped_name = os.path.basename(filename)
    if ignore_ext:
        mapped_name = os.path.splitext(mapped_name)[0]
    sobject = Search.get_by_search_key(search_key) if search_key else None
    if search_key and sobject is None:
        return {
            'accepted': False,
            'reason': 'Matching item no longer exists',
        }
    if sobject is None:
        sobject = SearchType.create(search_type)
    if sobject.column_exists(column):
        sobject.set_value(column, mapped_name)

    for name, value in (extra_data or {}).items():
        if sobject.column_exists(name):
            sobject.set_value(name, value)

    parent = Search.get_by_search_key(parent_key) if parent_key else None
    if parent is not None:
        try:
            sobject.set_sobject_value(parent)
        except Exception:
            # IngestUploadCmd has the same permissive parent behavior and can
            # still connect relation types that do not expose a direct column.
            pass

    snapshot = SearchType.create('sthpw/snapshot')
    script_input = {
        'path': upload_path,
        'sobject': sobject,
        'parent': parent,
        'snapshot': snapshot,
    }
    if validation_script:
        from tactic.command import PythonCmd
        ingest_exception_type = ()
        try:
            from tactic.command.ingestion_cmd import IngestException
            ingest_exception_type = IngestException
            command = PythonCmd(
                script_path=validation_script,
                input=script_input,
                IngestException=IngestException,
            )
        except ImportError:
            command = PythonCmd(
                script_path=validation_script,
                input=script_input,
            )
        try:
            validation_result = command.execute()
        except ingest_exception_type as error:
            return {
                'accepted': False,
                'reason': str(error),
            }
        if not validation_result:
            return {
                'accepted': False,
                'reason': 'Rejected by validation script',
            }

    if process_script:
        from tactic.command import PythonCmd
        command = PythonCmd(
            script_path=process_script,
            input=script_input,
        )
        if not command.execute():
            return {
                'accepted': False,
                'reason': 'Rejected by process script',
            }

    search_key = ''
    try:
        if int(sobject.get_id() or 0) > 0:
            search_key = sobject.get_search_key()
    except (TypeError, ValueError):
        pass
    return {
        'accepted': True,
        'search_key': search_key,
        'data': sobject.get_data(),
        'snapshot_data': snapshot.get_data(),
    }


def link_ingested_sobject(
        project_code, child_key, parent_key, relationship,
        instance_type='', instance_path=None):
    """Attach one newly ingested Search Object to its requested parent."""
    from pyasm.search import Search, SearchType

    server.set_project(project_code)
    child = Search.get_by_search_key(child_key)
    parent = Search.get_by_search_key(parent_key)
    if child is None or parent is None:
        raise RuntimeError('The ingested child or its parent no longer exists')

    if relationship == 'instance':
        if not instance_type:
            raise RuntimeError('The child relation has no instance Search Type')
        instance = SearchType.create(instance_type)
        instance.add_related_connection(
            child, parent, src_path=instance_path,
        )
        instance.commit()
    elif relationship in ('code', 'search_type', 'search_code', 'search_id'):
        child.set_sobject_value(parent)
        child.commit()
    else:
        raise RuntimeError(
            'Unsupported child relationship: %s' % relationship
        )
    return child.get_search_key()


def query_ingest_relation_matches(
        project_code, search_type, parent_key, column, names,
        instance_path=None):
    """Return filename matches that are children of one exact parent."""
    from pyasm.search import Search

    server.set_project(project_code)
    parent = Search.get_by_search_key(parent_key)
    if parent is None:
        raise RuntimeError('The ingest parent no longer exists')
    search = Search(search_type)
    search.add_relationship_filter(parent, path=instance_path)
    search.add_filters(column, list(names or []))
    records = []
    for sobject in search.get_sobjects():
        record = dict(sobject.get_data() or {})
        record['__search_key__'] = sobject.get_search_key()
        records.append(record)
    return records


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


def analyze_sobject_duplicate(search_key):
    """Return editable fields and copyable dependencies for one sObject."""
    import json
    from pyasm.biz import Schema, Snapshot, Task
    from pyasm.search import Search, SearchKey, SearchType

    sobject = SearchKey.get_by_search_key(search_key)
    if not sobject:
        raise Exception("SObject [%s] does not exist" % search_key)

    search_type = sobject.get_base_search_type()
    project_code = sobject.get_project_code()
    schema = Schema.get(project_code=project_code)
    source_data = dict(sobject.get_data() or {})
    columns = set(SearchType.get_columns(search_type) or [])
    protected = set([
        'id', 'code', 'timestamp', 'last_update', 'project_code',
        's_status', 'creator',
    ])
    try:
        search_type_object = SearchType.get(search_type)
        column_info = dict(
            search_type_object.get_column_info(search_type) or {}
        )
    except Exception:
        column_info = {}

    relationship_columns = set()
    related_specs = []
    seen_specs = set()
    for direction in ('parent', 'children'):
        related_types = schema.get_related_search_types(
            search_type, direction=direction
        ) or []
        for related_type in related_types:
            if not related_type or related_type == '*':
                continue
            attrs = dict(schema.get_relationship_attrs(
                search_type, related_type
            ) or {})
            relationship = attrs.get('relationship') or 'code'
            path = attrs.get('path') or ''
            instance_type = attrs.get('instance_type') or ''
            key = '|'.join([
                str(relationship), str(direction), str(related_type),
                str(instance_type), str(path),
            ])
            if relationship == 'instance':
                key = '|'.join([
                    'instance', str(related_type), str(instance_type),
                    str(path),
                ])
            if key in seen_specs:
                continue
            seen_specs.add(key)

            local_columns = []
            if attrs.get('from') == search_type:
                local_column = attrs.get('from_col')
            elif attrs.get('to') == search_type:
                local_column = attrs.get('to_col')
            else:
                local_column = None
            if local_column:
                local_columns.append(local_column)
            if direction == 'parent':
                if relationship in ('search_type', 'search_code'):
                    local_columns.extend([
                        'search_type', 'search_code', 'search_id'
                    ])
                elif relationship == 'search_id':
                    local_columns.extend(['search_type', 'search_id'])
                elif relationship == 'parent_code':
                    local_columns.append('parent_code')
                elif relationship == 'search_key':
                    local_columns.append('search_key')
            for column in local_columns:
                if column:
                    relationship_columns.add(column)

            try:
                related = list(sobject.get_related_sobjects(
                    related_type, path=path or None
                ) or [])
            except Exception:
                related = []
            if direction == 'parent' and not related:
                try:
                    parent = sobject.get_parent(related_type)
                except Exception:
                    parent = None
                if parent:
                    related = [parent]
            if not related:
                continue

            items = []
            for item in related[:24]:
                data = dict(item.get_data() or {})
                title = (
                    data.get('name') or data.get('title')
                    or data.get('code') or item.get_code()
                )
                items.append({
                    'searchKey': SearchKey.get_by_sobject(
                        item, use_id=False
                    ),
                    'title': str(title or ''),
                })
            try:
                stype = SearchType.get(related_type)
                related_title = (
                    stype.get_title() or stype.get_value('title')
                    or related_type
                )
            except Exception:
                related_title = related_type.rsplit('/', 1)[-1]
            kind = 'instance' if relationship == 'instance' else direction
            options = [
                {'value': 'none', 'label': 'Do not copy', 'icon': 'link-off'},
            ]
            default_mode = 'none'
            if kind == 'instance':
                options.append({
                    'value': 'link', 'label': 'Keep links', 'icon': 'link',
                })
                default_mode = 'link'
            elif kind == 'parent':
                options.append({
                    'value': 'link', 'label': 'Keep parent', 'icon': 'account-tree',
                })
                default_mode = 'link'
            else:
                options.append({
                    'value': 'copy', 'label': 'Duplicate children',
                    'icon': 'content-copy',
                })
            related_specs.append({
                'key': key,
                'direction': direction,
                'kind': kind,
                'relationship': relationship,
                'searchType': related_type,
                'title': str(related_title or related_type),
                'count': len(related),
                'mode': default_mode,
                'defaultMode': default_mode,
                'localColumn': ','.join(
                    str(column) for column in local_columns if column
                ),
                'path': str(path),
                'instanceType': str(instance_type),
                'options': options,
                'items': items,
            })

    ordered_names = ['name', 'title', 'description', 'keywords']
    ordered_names.extend(sorted(
        name for name in source_data
        if name not in ordered_names
    ))
    fields = []
    for name in ordered_names:
        if (
            name in protected or name in relationship_columns
            or name not in columns or name.startswith('__')
        ):
            continue
        value = source_data.get(name)
        if isinstance(value, (dict, list, tuple)):
            continue
        if value is None:
            value = ''
        metadata = dict(column_info.get(name) or {})
        data_type = str(
            metadata.get('data_type') or type(value).__name__
        )
        label = str(
            metadata.get('title') or metadata.get('label')
            or name.replace('_', ' ').strip().title()
        )
        fields.append({
            'name': name,
            'label': label,
            'value': str(value),
            'originalValue': str(value),
            'dataType': data_type,
            'multiline': name in ('description', 'keywords', 'notes'),
        })

    process_records = {}

    def process_record(process):
        process = str(process or 'publish')
        return process_records.setdefault(process, {
            'name': process,
            'snapshotCount': 0,
            'fileCount': 0,
            'taskCount': 0,
            'processMessageCount': 0,
            'taskMessageCount': 0,
            'processAttachmentCount': 0,
            'taskAttachmentCount': 0,
        })

    def identity(item):
        code = str(item.get_code() or '')
        return code or str(item.get_id() or '')

    def root_notes(target):
        target_type = str(
            target.get_base_search_type() or ''
        ).split('?', 1)[0]
        target_code = str(target.get_code() or '')
        target_id = str(target.get_id() or '')
        if not target_code and not target_id:
            return []
        note_search = Search('sthpw/note')
        note_search.add_filter(
            'search_code' if target_code else 'search_id',
            target_code or target_id,
        )
        if project_code:
            note_search.add_filter('project_code', project_code)
        roots = []
        for note in note_search.get_sobjects() or []:
            note_type = str(
                note.get_value('search_type') or ''
            ).split('?', 1)[0]
            if note_type and target_type and note_type != target_type:
                continue
            if note.get_value('parent_id') in (None, '', 0, '0'):
                roots.append(note)
        return roots

    def flatten_notes(notes):
        result = []
        pending = list(notes or [])
        seen = set()
        while pending:
            note = pending.pop(0)
            key = identity(note)
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            result.append(note)
            try:
                pending.extend(note.get_child_notes() or [])
            except Exception:
                pass
        return result

    def snapshot_file_count(snapshot):
        try:
            paths_by_type = snapshot.get_all_paths_dict() or {}
        except Exception:
            return 0
        count = 0
        for paths in paths_by_type.values():
            if isinstance(paths, str):
                count += bool(paths)
            else:
                count += len([path for path in paths or [] if path])
        return count

    tasks = list(Task.get_by_sobject(sobject) or [])
    task_processes = {}
    for task in tasks:
        process = str(task.get_value('process') or 'publish')
        record = process_record(process)
        record['taskCount'] += 1
        task_processes[identity(task)] = process

    process_notes = root_notes(sobject)
    process_note_trees = {}
    for note in process_notes:
        process = str(note.get_value('process') or 'publish')
        process_note_trees[identity(note)] = flatten_notes([note])
        process_record(process)['processMessageCount'] += len(
            process_note_trees[identity(note)]
        )

    task_note_trees = {}
    for task in tasks:
        task_key = identity(task)
        task_note_trees[task_key] = flatten_notes(root_notes(task))
        process = task_processes.get(task_key) or 'publish'
        process_record(process)['taskMessageCount'] += len(
            task_note_trees[task_key]
        )

    attachment_codes = set()

    def count_attachments(notes, process, task_scope=False):
        for note in notes:
            attachments = list(Snapshot.get_by_sobjects([note]) or [])
            known = set(
                str(snapshot.get_code() or '') for snapshot in attachments
            )
            for snapshot in note.get_connections(
                    context='attachment') or []:
                code = str(snapshot.get_code() or '')
                if snapshot and code not in known:
                    attachments.append(snapshot)
                    known.add(code)
            if not attachments:
                continue
            count = 0
            for snapshot in attachments:
                code = str(snapshot.get_code() or '')
                if code:
                    attachment_codes.add(code)
                count += snapshot_file_count(snapshot)
            key = (
                'taskAttachmentCount' if task_scope
                else 'processAttachmentCount'
            )
            process_record(process)[key] += count

    for root in process_notes:
        process = str(root.get_value('process') or 'publish')
        count_attachments(
            process_note_trees.get(identity(root), []), process,
            task_scope=False,
        )
    for task_key, notes in task_note_trees.items():
        process = task_processes.get(task_key) or 'publish'
        count_attachments(notes, process, task_scope=True)
        for snapshot in Snapshot.get_by_sobjects([
                next(task for task in tasks if identity(task) == task_key)
        ]) or []:
            process_record(process)['taskAttachmentCount'] += (
                snapshot_file_count(snapshot)
            )

    snapshots = []
    for snapshot in Snapshot.get_all_current_by_sobject(sobject) or []:
        if str(snapshot.get_code() or '') in attachment_codes:
            continue
        snapshots.append(snapshot)
    for snapshot in snapshots:
        context = str(snapshot.get_value('context') or 'publish')
        process = str(
            snapshot.get_value('process') or context.split('/', 1)[0]
            or 'publish'
        )
        record = process_record(process)
        record['snapshotCount'] += 1
        record['fileCount'] += snapshot_file_count(snapshot)

    processes = []
    for name in sorted(process_records):
        record = process_records[name]
        record.update({
            'copySnapshots': False,
            'copyTasks': False,
            'copyProcessMessages': False,
            'copyTaskMessages': False,
            'copyProcessAttachments': False,
            'copyTaskAttachments': False,
        })
        processes.append(record)

    source_title = (
        source_data.get('name') or source_data.get('title')
        or source_data.get('code') or sobject.get_code()
    )
    return json.dumps({
        'searchKey': search_key,
        'searchType': search_type,
        'projectCode': project_code,
        'title': str(source_title or ''),
        'fields': fields,
        'relations': related_specs,
        'processes': processes,
    })


def duplicate_sobject_advanced(search_key, options=None):
    """Duplicate one sObject using explicit relation and content choices."""
    import json
    from pyasm.biz import Schema, Snapshot, Task
    from pyasm.checkin import FileCheckin
    from pyasm.search import Search, SearchKey, SearchType

    options = dict(options or {})
    source = SearchKey.get_by_search_key(search_key)
    if not source:
        raise Exception("SObject [%s] does not exist" % search_key)

    search_type = source.get_base_search_type()
    project_code = source.get_project_code()
    server.set_project(project_code)
    schema = Schema.get(project_code=project_code)
    relation_options = dict(options.get('relations') or {})
    field_values = dict(options.get('fields') or {})
    process_options = dict(options.get('processes') or {})

    omitted_columns = set(['id', 'code', 'timestamp', 'last_update'])
    parent_specs = []
    child_specs = []
    instance_specs = []
    seen = set()
    for direction in ('parent', 'children'):
        for related_type in schema.get_related_search_types(
                search_type, direction=direction) or []:
            if not related_type or related_type == '*':
                continue
            attrs = dict(schema.get_relationship_attrs(
                search_type, related_type
            ) or {})
            relationship = attrs.get('relationship') or 'code'
            path = attrs.get('path') or ''
            instance_type = attrs.get('instance_type') or ''
            key = '|'.join([
                str(relationship), str(direction), str(related_type),
                str(instance_type), str(path),
            ])
            if relationship == 'instance':
                key = '|'.join([
                    'instance', str(related_type), str(instance_type),
                    str(path),
                ])
            if key in seen:
                continue
            seen.add(key)
            mode = str(relation_options.get(key) or (
                'link' if relationship == 'instance'
                or direction == 'parent' else 'none'
            ))
            spec = (related_type, path, attrs, mode)
            if relationship == 'instance':
                instance_specs.append(spec)
            elif direction == 'parent':
                parent_specs.append(spec)
                if mode == 'none':
                    local_columns = []
                    if attrs.get('from') == search_type:
                        local_column = attrs.get('from_col')
                    elif attrs.get('to') == search_type:
                        local_column = attrs.get('to_col')
                    else:
                        local_column = None
                    if local_column:
                        local_columns.append(local_column)
                    if relationship in ('search_type', 'search_code'):
                        local_columns.extend([
                            'search_type', 'search_code', 'search_id'
                        ])
                    elif relationship == 'search_id':
                        local_columns.extend([
                            'search_type', 'search_id'
                        ])
                    elif relationship == 'parent_code':
                        local_columns.append('parent_code')
                    elif relationship == 'search_key':
                        local_columns.append('search_key')
                    omitted_columns.update(
                        column for column in local_columns if column
                    )
            else:
                child_specs.append(spec)

    def identity(sobject):
        if not sobject:
            return ''
        code = str(sobject.get_code() or '')
        if code:
            return code
        return str(sobject.get_id() or '')

    def require_created(sobject, label):
        if not identity(sobject):
            raise RuntimeError('%s was not created by TACTIC' % label)
        return sobject

    def root_notes(target):
        target_type = str(
            target.get_base_search_type() or ''
        ).split('?', 1)[0]
        target_code = str(target.get_code() or '')
        target_id = str(target.get_id() or '')
        if not target_code and not target_id:
            return []
        note_search = Search('sthpw/note')
        note_search.add_filter(
            'search_code' if target_code else 'search_id',
            target_code or target_id,
        )
        if project_code:
            note_search.add_filter('project_code', project_code)
        roots = []
        for note in note_search.get_sobjects() or []:
            note_type = str(
                note.get_value('search_type') or ''
            ).split('?', 1)[0]
            if note_type and target_type and note_type != target_type:
                continue
            if note.get_value('parent_id') in (None, '', 0, '0'):
                roots.append(note)
        return roots

    source_tasks = list(Task.get_by_sobject(source) or [])
    process_notes = root_notes(source)
    task_notes = {}
    task_snapshots = {}
    for task in source_tasks:
        key = identity(task)
        task_notes[key] = root_notes(task)
        task_snapshots[key] = list(
            Snapshot.get_by_sobjects([task]) or []
        )

    def note_attachments(note):
        attachments = list(Snapshot.get_by_sobjects([note]) or [])
        known = set(
            str(snapshot.get_code() or '') for snapshot in attachments
        )
        for snapshot in note.get_connections(context='attachment') or []:
            code = str(snapshot.get_code() or '')
            if snapshot and code not in known:
                attachments.append(snapshot)
                known.add(code)
        return attachments

    attachment_codes = set()
    visited_notes = set()

    def note_tree(notes):
        result = []
        pending = list(notes or [])
        while pending:
            note = pending.pop(0)
            key = identity(note)
            if key and key in visited_notes:
                continue
            if key:
                visited_notes.add(key)
            result.append(note)
            try:
                pending.extend(note.get_child_notes() or [])
            except Exception:
                pass
        return result

    process_note_trees = {}
    process_note_tree = []
    for note in process_notes:
        branch = note_tree([note])
        process_note_trees[identity(note)] = branch
        process_note_tree.extend(branch)
    task_note_trees = {}
    for task_key, notes in task_notes.items():
        task_note_trees[task_key] = note_tree(notes)
    for note in process_note_tree:
        for snapshot in note_attachments(note):
            if identity(snapshot):
                attachment_codes.add(identity(snapshot))
    for notes in task_note_trees.values():
        for note in notes:
            for snapshot in note_attachments(note):
                if identity(snapshot):
                    attachment_codes.add(identity(snapshot))

    snapshot_plans = {}

    def snapshot_plan(snapshot):
        key = identity(snapshot)
        if key in snapshot_plans:
            return snapshot_plans[key]
        try:
            paths_by_type = dict(snapshot.get_all_paths_dict() or {})
        except Exception as error:
            raise RuntimeError(
                'Could not resolve files for snapshot [%s]: %s'
                % (key or 'unknown', error)
            )
        file_types = []
        file_paths = []
        for file_type in sorted(paths_by_type):
            paths = paths_by_type.get(file_type) or []
            if isinstance(paths, str):
                paths = [paths]
            for path in paths:
                path = str(path or '')
                if not path:
                    continue
                file_types.append(str(file_type or 'main'))
                file_paths.append(path)
        if not file_paths:
            raise RuntimeError(
                'Snapshot [%s] has no repository files to duplicate'
                % (key or 'unknown')
            )
        snapshot_plans[key] = (file_types, file_paths)
        return snapshot_plans[key]

    def checkin_snapshot(snapshot, target):
        context = str(snapshot.get_value('context') or 'publish')
        file_types, file_paths = snapshot_plan(snapshot)
        checkin = FileCheckin(
            target, context=context, file_paths=file_paths,
            file_types=file_types,
            snapshot_type=snapshot.get_value('snapshot_type'),
            mode='inplace'
        )
        created = require_created(
            checkin.execute(), 'Snapshot [%s]' % identity(snapshot)
        )
        return created, len(file_paths)

    source_snapshots = []
    for snapshot in Snapshot.get_all_current_by_sobject(source) or []:
        if identity(snapshot) in attachment_codes:
            continue
        source_snapshots.append(snapshot)

    # Resolve every selected repository path before the first write. This
    # avoids creating a root duplicate and only then discovering that a
    # selected snapshot or attachment cannot be copied.
    for snapshot in source_snapshots:
        context = str(snapshot.get_value('context') or 'publish')
        process = str(
            snapshot.get_value('process') or context.split('/', 1)[0]
            or 'publish'
        )
        if dict(process_options.get(process) or {}).get('copySnapshots'):
            snapshot_plan(snapshot)
    for note in process_notes:
        process = str(note.get_value('process') or 'publish')
        if dict(process_options.get(process) or {}).get(
                'copyProcessAttachments'):
            for branch_note in process_note_trees.get(identity(note), []):
                for snapshot in note_attachments(branch_note):
                    snapshot_plan(snapshot)
    for task in source_tasks:
        process = str(task.get_value('process') or 'publish')
        if not dict(process_options.get(process) or {}).get(
                'copyTaskAttachments'):
            continue
        for snapshot in task_snapshots.get(identity(task), []):
            snapshot_plan(snapshot)
        for note in task_note_trees.get(identity(task), []):
            for snapshot in note_attachments(note):
                snapshot_plan(snapshot)

    new_sobject = SearchType.create(search_type)
    columns = set(SearchType.get_columns(search_type) or [])
    for name, value in (source.get_data() or {}).items():
        if (
                name in omitted_columns or name not in columns
                or value is None):
            continue
        if isinstance(value, (dict, list)):
            new_sobject.set_json_value(name, value)
        else:
            new_sobject.set_value(name, value)
    for name, value in field_values.items():
        if name in columns and name not in omitted_columns:
            new_sobject.set_value(name, '' if value is None else value)
    new_sobject.commit()
    require_created(new_sobject, 'Duplicate sObject')

    relation_counts = {'linked': 0, 'children': 0}
    for related_type, path, attrs, mode in instance_specs:
        if mode != 'link':
            continue
        instance_type = str(attrs.get('instance_type') or '')
        if not instance_type:
            raise RuntimeError(
                'Instance relationship to [%s] has no instance type'
                % related_type
            )
        related = source.get_related_sobjects(
            related_type, path=path or None
        ) or []
        for related_sobject in related:
            from_type = str(attrs.get('from') or '').split('?', 1)[0]
            if from_type == search_type:
                from_sobject, to_sobject = new_sobject, related_sobject
            else:
                from_sobject, to_sobject = related_sobject, new_sobject
            instance = SearchType.create(instance_type)
            instance.add_related_connection(
                from_sobject, to_sobject, src_path=path or None
            )
            instance.commit()
            require_created(instance, 'Instance relationship')
            relation_counts['linked'] += 1

    for related_type, path, attrs, mode in child_specs:
        if mode != 'copy':
            continue
        children = source.get_related_sobjects(
            related_type, path=path or None
        ) or []
        for child in children:
            clone = child.clone(recursive=False, parent=new_sobject)
            require_created(clone, 'Child sObject')
            relation_counts['children'] += 1

    copied_snapshots = 0
    for snapshot in source_snapshots:
        context = str(snapshot.get_value('context') or 'publish')
        process = str(
            snapshot.get_value('process') or context.split('/', 1)[0]
            or 'publish'
        )
        choice = dict(process_options.get(process) or {})
        if not choice.get('copySnapshots'):
            continue
        checkin_snapshot(snapshot, new_sobject)
        copied_snapshots += 1

    task_map = {}
    copied_tasks = 0
    for task in source_tasks:
        process = str(task.get_value('process') or 'publish')
        choice = dict(process_options.get(process) or {})
        if not choice.get('copyTasks'):
            continue
        task_clone = require_created(
            task.clone(recursive=False, parent=new_sobject),
            'Task [%s]' % identity(task),
        )
        task_map[identity(task)] = task_clone
        copied_tasks += 1

    copied_attachments = 0

    def copy_attachments(note, note_clone):
        copied = 0
        for snapshot in note_attachments(note):
            created, file_count = checkin_snapshot(snapshot, note_clone)
            require_created(created, 'Note attachment')
            copied += file_count
        return copied

    def copy_note_branch(note, target, copy_files, parent_clone=None):
        clone = require_created(
            note.copy_note(target, parent=parent_clone),
            'Message [%s]' % identity(note),
        )
        files_copied = copy_attachments(note, clone) if copy_files else 0
        messages_copied = 1
        try:
            children = note.get_child_notes() or []
        except Exception:
            children = []
        for child_note in children:
            child_count, child_files = copy_note_branch(
                child_note, target, copy_files, parent_clone=clone
            )
            messages_copied += child_count
            files_copied += child_files
        return messages_copied, files_copied

    copied_process_messages = 0
    for note in process_notes:
        process = str(note.get_value('process') or 'publish')
        choice = dict(process_options.get(process) or {})
        if not choice.get('copyProcessMessages'):
            continue
        message_count, file_count = copy_note_branch(
            note, new_sobject,
            bool(choice.get('copyProcessAttachments')),
        )
        copied_process_messages += message_count
        copied_attachments += file_count

    copied_task_messages = 0
    if task_map:
        for task in source_tasks:
            task_key = identity(task)
            task_clone = task_map.get(task_key)
            if not task_clone:
                continue
            process = str(task.get_value('process') or 'publish')
            choice = dict(process_options.get(process) or {})
            if choice.get('copyTaskAttachments'):
                for snapshot in task_snapshots.get(task_key, []):
                    created, file_count = checkin_snapshot(
                        snapshot, task_clone
                    )
                    require_created(created, 'Task attachment')
                    copied_attachments += file_count
            if not choice.get('copyTaskMessages'):
                continue
            for note in task_notes.get(task_key, []):
                message_count, file_count = copy_note_branch(
                    note, task_clone,
                    bool(choice.get('copyTaskAttachments')),
                )
                copied_task_messages += message_count
                copied_attachments += file_count

    return json.dumps({
        'searchKey': SearchKey.get_by_sobject(new_sobject, use_id=False),
        'code': new_sobject.get_code(),
        'relationsLinked': relation_counts['linked'],
        'childrenCopied': relation_counts['children'],
        'snapshotsCopied': copied_snapshots,
        'tasksCopied': copied_tasks,
        'processMessagesCopied': copied_process_messages,
        'taskMessagesCopied': copied_task_messages,
        'attachmentFilesCopied': copied_attachments,
    })


def duplicate_sobjects(search_keys, data_dict=None):
    """Preserve the public field-only batch API for external callers."""
    import json

    if not isinstance(search_keys, list):
        search_keys = [search_keys]
    if not search_keys:
        raise ValueError("At least one sObject search key is required")
    data_dict = dict(data_dict or {})
    sobjects = server.server._get_sobjects(search_keys)
    if not sobjects:
        raise Exception("SObject [%s] does not exist" % search_keys[0])
    source = sobjects[0]
    project_code = source.get_project_code()
    server.set_project(project_code)
    final_data = {}
    for name, value in (source.get_data() or {}).items():
        if name in ('code', 'id', 'timestamp') or not value:
            continue
        final_data[name] = value
    if data_dict.get('new_name') is not None:
        final_data['name'] = data_dict.get('new_name')
    return json.dumps(server.insert(
        source.get_base_search_type(), final_data
    ))


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

    import json
    from tactic.ui.tools import DeleteCmd

    if not isinstance(search_keys, list):
        search_keys = [search_keys]

    sobjects = server.server._get_sobjects(search_keys)
    if not sobjects:
        raise Exception("SObject [%s] does not exist" % search_keys[0])

    PROJECT_CODE = sobjects[0].get_project_code()

    deleted_sobjects = []
    ex_list = ['sthpw/file']

    for sobject in sobjects:
        # almost any sobject should have project code
        # so it is better do delete it within their projects env
        # project_code = sobject.get_value('project_code', no_exception=True)

        if PROJECT_CODE:
            server.set_project(PROJECT_CODE)

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
    from pyasm.biz import Snapshot, Project
    from pyasm.common import Environment

    def get_sobjects_dict(sobjects):
        res = []
        if sobjects:
            search_keys = SearchKey.get_by_sobjects(sobjects, use_id=False)
            for j, sobject in enumerate(sobjects):
                sobj = sobject.get_data()

                sobj['__search_key__'] = search_keys[j]
                res.append(sobj)

        return res

    def get_sobject_dict(sobject):
        search_key = SearchKey.get_by_sobject(sobject, use_id=False)
        sobj = sobject.get_data()
        sobj['__search_key__'] = search_key

        return sobj

    # Getting all Projects from db
    search = Search('sthpw/project')
    search.add_filters('code', ['admin', 'sthpw'], op='in')
    builtin_projects = search.get_sobjects()
    builtin_project_codes = set(
        project.get_value('code') for project in builtin_projects
    )


    # getting only user projects
    user_projects = Project.get_user_projects()

    projects = builtin_projects + user_projects

    # Getting snapshots for projects previews
    snapshot_search = Search('sthpw/snapshot')
    snapshot_search.add_relationship_filters(projects, op='in')
    snapshot_search.add_op_filters([('process', ['icon', 'attachment', 'publish'])])
    snapshots_sobjects = snapshot_search.get_sobjects()

    snapshots_files_sobjects = Snapshot.get_files_dict_by_snapshots(snapshots_sobjects)

    projects = get_sobjects_dict(projects)

    for project in projects:
        project['__builtin__'] = project.get('code') in builtin_project_codes

        related_snapshots = []
        for snapshot in snapshots_sobjects:
            if snapshot.get_value('search_code') == project['code']:
                related_snapshots.append(snapshot)

        snapshots_list = []
        for snapshot in related_snapshots:

            if snapshot.get_version() in [-1, 0, '-1', '0'] or snapshot.is_latest():
                snapshot_dict = get_sobject_dict(snapshot)
                files_list = []
                snapshots_files = snapshots_files_sobjects.get(snapshot_dict['code'])
                if snapshots_files:
                    for fl in snapshots_files:
                        files_list.append(server.server._get_sobject_dict(fl))
                snapshot_dict['__files__'] = files_list
                snapshots_list.append(snapshot_dict)

        project['__snapshots__'] = snapshots_list

    # Getting all possible Logins from db

    search = Search('sthpw/login')
    search.add_op_filters([])
    logins_sobjects = search.get_sobjects()

    # Getting snapshots for logins previews
    snapshot_search = Search('sthpw/snapshot')
    snapshot_search.add_relationship_filters(logins_sobjects, op='in')
    snapshot_search.add_op_filters([('process', ['icon', 'attachment', 'publish'])])
    snapshots_sobjects = snapshot_search.get_sobjects()

    snapshots_files_sobjects = Snapshot.get_files_dict_by_snapshots(snapshots_sobjects)

    logins = get_sobjects_dict(logins_sobjects)
    security = Environment.get_security()
    session_login = security.get_user_name()
    session_is_admin = bool(security.is_admin())

    for login in logins:
        # Session authority comes from TACTIC, never a group/display-name guess.
        login['__is_admin__'] = (
            login.get('login') == session_login and session_is_admin
        )

        related_snapshots = []
        for snapshot in snapshots_sobjects:
            if snapshot.get_value('search_code') == login['code']:
                related_snapshots.append(snapshot)

        snapshots_list = []
        for snapshot in related_snapshots:

            if snapshot.get_version() in [-1, 0, '-1', '0'] or snapshot.is_latest():
                snapshot_dict = get_sobject_dict(snapshot)
                files_list = []
                snapshots_files = snapshots_files_sobjects.get(snapshot_dict['code'])
                if snapshots_files:
                    for fl in snapshots_files:
                        files_list.append(server.server._get_sobject_dict(fl))
                snapshot_dict['__files__'] = files_list
                snapshots_list.append(snapshot_dict)

        login['__snapshots__'] = snapshots_list

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


def get_tasks_and_notes(search_code, project_code, process=None,
                        include_all_tasks=False):
    import json
    from pyasm.search import Search, SearchKey
    from pyasm.biz import Snapshot

    server.set_project(project_code)

    def get_sobjects_dict(sobjects):
        res = []
        if sobjects:
            search_keys = SearchKey.get_by_sobjects(sobjects, use_id=False)
            for j, sobject in enumerate(sobjects):
                sobj = sobject.get_data()

                sobj['__search_key__'] = search_keys[j]
                res.append(sobj)

        return res

    def get_sobject_dict(sobject):
        search_key = SearchKey.get_by_sobject(sobject, use_id=False)
        sobj = sobject.get_data()
        sobj['__search_key__'] = search_key

        return sobj

    search = Search('sthpw/task')
    search.add_filter('search_code', search_code)
    search.add_filter('project_code', project_code)
    if process and not include_all_tasks:
        search.add_filter('process', process)

    elif not process:
        search.add_order_by('timestamp', direction='desc')

        single_task = search.get_sobject()
        if single_task:
            process = single_task.get_value('process')

        # if single task we found have process, and it exists we continue with this process
        if process:
            search = Search('sthpw/task')
            search.add_filter('search_code', search_code)
            search.add_filter('project_code', project_code)
            search.add_filter('process', process)

    tasks_sobjects = search.get_sobjects()

    tasks = get_sobjects_dict(tasks_sobjects)

    task_codes = [task.get('code') for task in tasks if task.get('code')]
    task_process_by_code = dict(
        (task.get('code'), task.get('process') or 'publish')
        for task in tasks if task.get('code')
    )
    task_count_by_process = {}
    for task_process in task_process_by_code.values():
        task_count_by_process[task_process] = (
            task_count_by_process.get(task_process, 0) + 1
        )
    task_note_codes = [
        task_code for task_code, task_process in task_process_by_code.items()
        if task_count_by_process.get(task_process, 0) > 1
    ]
    if task_codes:
        status_search = Search('sthpw/status_log')
        status_search.add_filters('search_code', task_codes)
        status_sobjects = status_search.get_sobjects()
        status_logs_by_task = {}
        for status_log in get_sobjects_dict(status_sobjects):
            task_code = status_log.get('search_code')
            if task_code:
                status_logs_by_task.setdefault(task_code, []).append(
                    status_log
                )
        for task in tasks:
            status_log_list = status_logs_by_task.get(task.get('code'))
            if status_log_list:
                task['__status_log__'] = status_log_list

    # Query the parent notes once for every process.  The caller only needs
    # full note payloads for the active process, while Task Inspector needs a
    # count for every task process before a manual refresh.
    search = Search('sthpw/note')
    search.add_filter('search_code', search_code)
    search.add_filter('project_code', project_code)
    if not include_all_tasks:
        search.add_filter('process', process)
    all_notes_sobjects = search.get_sobjects()

    task_notes_sobjects = []
    if task_note_codes:
        task_note_search = Search('sthpw/note')
        task_note_search.add_filters('search_code', task_note_codes)
        task_note_search.add_filter('project_code', project_code)
        if process and not include_all_tasks:
            task_note_search.add_filter('process', process)
        task_notes_sobjects = [
            note for note in task_note_search.get_sobjects()
            if str(note.get_value('search_type') or '').split('?', 1)[0]
            in ('', 'sthpw/task')
        ]

    notes_count_by_process = dict(
        (task.get('process') or 'publish', 0) for task in tasks
    )
    task_note_count_by_code = {}
    notes_sobjects = []
    for note_sobject in all_notes_sobjects:
        note_process = note_sobject.get_value('process')
        notes_count_by_process[note_process] = (
            notes_count_by_process.get(note_process, 0) + 1
        )
        if not process or note_process == process:
            notes_sobjects.append(note_sobject)

    for note_sobject in task_notes_sobjects:
        task_code = note_sobject.get_value('search_code')
        note_process = (
            note_sobject.get_value('process')
            or task_process_by_code.get(task_code) or 'publish'
        )
        task_note_count_by_code[task_code] = (
            task_note_count_by_code.get(task_code, 0) + 1
        )
        notes_count_by_process[note_process] = (
            notes_count_by_process.get(note_process, 0) + 1
        )
        if not process or note_process == process:
            notes_sobjects.append(note_sobject)

    notes = get_sobjects_dict(notes_sobjects)

    tasks_by_process = {}
    for task in tasks:
        tasks_by_process.setdefault(
            task.get('process') or 'publish', []
        ).append(task)

    for task_process, process_tasks in tasks_by_process.items():
        process_tasks.sort(key=lambda item: (
            0 if not item.get('context')
            or item.get('context') == task_process else 1,
            item.get('timestamp') or '', item.get('code') or '',
        ))
        primary_code = (
            process_tasks[0].get('code') if process_tasks else None
        )
        root_count = notes_count_by_process.get(task_process, 0) - sum(
            task_note_count_by_code.get(item.get('code'), 0)
            for item in process_tasks
        )
        for task in process_tasks:
            task['__primary_note_branch__'] = (
                task.get('code') == primary_code
            )
            task['__notes_count__'] = (
                root_count if task.get('code') == primary_code
                else task_note_count_by_code.get(task.get('code'), 0)
            )

    for note, note_sobject in zip(notes, notes_sobjects):

        # Getting snapshots for notes previews
        snapshots_sobjects = Snapshot.get_by_sobjects([note_sobject])
        connected_snapshots = note_sobject.get_connections(context='attachment')

        if connected_snapshots:
            for connected_snapshot in connected_snapshots:
                if connected_snapshot:
                    snapshots_sobjects.append(connected_snapshot)

        if snapshots_sobjects:
            snapshots_files_sobjects = Snapshot.get_files_dict_by_snapshots(snapshots_sobjects)

        snapshots_list = []
        for snapshot in snapshots_sobjects:

            snapshot_dict = get_sobject_dict(snapshot)
            files_list = []
            snapshots_files = snapshots_files_sobjects.get(snapshot_dict['code'])
            if snapshots_files:
                for fl in snapshots_files:
                    files_list.append(server.server._get_sobject_dict(fl))
            snapshot_dict['__files__'] = files_list
            snapshots_list.append(snapshot_dict)

        note['__snapshots__'] = snapshots_list

    result = {
        'notes': notes,
        'tasks': tasks,
        'noteCounts': notes_count_by_process,
    }

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


def get_notes_with_attachments(note_codes, project_code):
    """Return many notes and their native snapshot/connection attachments."""
    import json
    from pyasm.search import Search, SearchKey
    from pyasm.biz import Snapshot

    server.set_project(project_code)
    codes = list(dict.fromkeys(
        str(code) for code in (note_codes or []) if code
    ))
    if not codes:
        return json.dumps({'notes': []}, separators=(',', ':'))
    search = Search('sthpw/note')
    search.add_filters('code', codes)
    notes = search.get_sobjects()
    result = []
    for note in notes:
        data = note.get_data()
        data['__search_key__'] = SearchKey.get_by_sobject(
            note, use_id=False
        )
        snapshots = list(Snapshot.get_by_sobjects([note]) or [])
        known = set(
            str(snapshot.get_code() or '') for snapshot in snapshots
        )
        for snapshot in note.get_connections(context='attachment') or []:
            code = str(snapshot.get_code() or '')
            if snapshot and code not in known:
                snapshots.append(snapshot)
                known.add(code)
        files_by_snapshot = (
            Snapshot.get_files_dict_by_snapshots(snapshots)
            if snapshots else {}
        )
        decorated = []
        for snapshot in snapshots:
            snapshot_data = snapshot.get_data()
            snapshot_data['__search_key__'] = SearchKey.get_by_sobject(
                snapshot, use_id=False
            )
            snapshot_data['__files__'] = [
                server.server._get_sobject_dict(file_object)
                for file_object in (
                    files_by_snapshot.get(snapshot.get_code()) or []
                )
            ]
            decorated.append(snapshot_data)
        data['__snapshots__'] = decorated
        result.append(data)
    return json.dumps({'notes': result}, separators=(',', ':'))


def query_task_workspace_page(filters, order_bys, project_code,
                              limit=500, offset=0, query=None):
    """Load a task page and all of its parents in one XML-RPC call."""
    import json
    from pyasm.search import Search

    server.set_project(project_code)
    task_search = Search('sthpw/task')
    facets = {}
    if filters:
        task_search.add_op_filters(filters)
    if query:
        import re
        from datetime import date, timedelta
        from pyasm.search import SearchType, Sql

        query = dict(query)
        if not 1 <= int(limit) <= 500 or int(offset) < 0:
            raise ValueError('Task pages require a limit of 1..500 and a non-negative offset')
        panel = dict(query.get('filters') or {})
        quick = dict(query.get('quickFilters') or {})
        labels = dict(query.get('labels') or {})
        columns = {
            'process': 'process', 'status': 'status', 'assigned': 'assigned',
            'supervisor': 'supervisor', 'priority': 'priority',
            'milestone': 'milestone_code',
        }
        for name, values in quick.items():
            if name not in columns and name != 'preset':
                raise ValueError('Unknown task quick filter: %s' % name)
            if not isinstance(values, (list, tuple)):
                raise ValueError('Task quick filter %s requires a list of values' % name)
        if set(panel) - (set(columns) | {'text', 'due', 'day', 'hasNotes'}):
            raise ValueError('Unknown task filter fields')
        today = date.fromisoformat(str(query['today'])) if query.get('today') else date.today()

        def exact(column, values, search=None):
            search = search if search is not None else task_search
            values = list(values)
            search.add_op('begin')
            nonempty = [value for value in values if value != '']
            if nonempty:
                search.add_filters(column, nonempty)
            if '' in values:
                search.add_empty_filter(column)
            search.add_op('or')

        def due(value, search=None):
            search = search if search is not None else task_search
            if value == 'unscheduled':
                search.add_null_filter('bid_end_date')
                return
            boundaries = {
                'overdue': (None, today),
                'today': (today, today + timedelta(days=1)),
                'soon': (today + timedelta(days=1), today + timedelta(days=4)),
                'scheduled': (today + timedelta(days=4), None),
            }
            if value not in boundaries:
                raise ValueError('Unknown task deadline filter: %s' % value)
            start, end = boundaries[value]
            if start:
                search.add_filter('bid_end_date', start.isoformat(), op='>=')
            if end:
                search.add_filter('bid_end_date', end.isoformat(), op='<')

        def apply_preset(search, preset):
            search.add_op('begin')
            if preset == 'mine':
                if query.get('currentLogin'):
                    exact('assigned', [str(query['currentLogin'])], search)
                else:
                    search.add_where('1 = 0')
            elif preset == 'unassigned':
                search.add_empty_filter('assigned')
            elif preset in ('overdue', 'today'):
                due(preset, search)
            elif preset == 'recent':
                search.add_filter('timestamp', (today - timedelta(days=7)).isoformat(), op='>=')
                search.add_filter('timestamp', (today + timedelta(days=1)).isoformat(), op='<')
            elif preset == 'review':
                search.add_op('begin')
                for column in ('status', 'process', 'context', 'pipeline_code'):
                    search.add_regex_filter(column, 'approval|review')
                review_processes = [
                    item['value'] for item in labels.get('process', [])
                    if re.search('approval|review', str(item.get('type') or ''), re.I)
                ]
                if review_processes:
                    search.add_filters('process', review_processes)
                search.add_op('or')
            else:
                raise ValueError('Unknown task preset: %s' % preset)
            search.add_op('and')

        # Scope-wide aggregates keep choices available after filtering. Only
        # grouped values/counts cross the RPC boundary, not the task inventory.
        facets = {}
        for name, column in columns.items():
            facet_search = Search('sthpw/task')
            facet_search.add_op_filters(filters or [])
            facet_search.add_column(column)
            # TACTIC 4.9 quotes expressions as identifiers unless this Select
            # uses raw mode. All projection/table names here are fixed above.
            facet_search.get_select().set_quoted_mode('none')
            facet_search.add_column('count(*)', as_column='task_count')
            facet_search.add_group_by(column)
            label_map = {str(item['value']): item for item in labels.get(name, [])}
            options = []
            for item in facet_search.get_sobjects():
                raw_value = item.get_value(column)
                value = str(raw_value if raw_value is not None else '')
                label = label_map.get(value) or {}
                options.append({
                    'key': value, 'title': str(label.get('label') or value),
                    'count': int(item.get_value('task_count') or 0),
                    'accent': str(label.get('color') or ''),
                })
            facets[name] = sorted(options, key=lambda item: item['title'].casefold())
        facets['preset'] = {}
        for preset in ('mine', 'unassigned', 'overdue', 'today', 'recent', 'review'):
            preset_search = Search('sthpw/task')
            preset_search.add_op_filters(filters or [])
            apply_preset(preset_search, preset)
            facets['preset'][preset] = preset_search.get_count()

        for name, column in columns.items():
            if panel.get(name) not in (None, ''):
                exact(column, [str(panel[name])])
            if quick.get(name):
                exact(column, [str(value) for value in quick[name]])
        if panel.get('due'):
            due(panel['due'])
        if panel.get('day'):
            day = date.fromisoformat(str(panel['day']))
            task_search.add_filter('bid_end_date', day.isoformat(), op='>=')
            task_search.add_filter('bid_end_date', (day + timedelta(days=1)).isoformat(), op='<')
        presets = list(quick.get('preset') or [])
        if presets:
            task_search.add_op('begin')
            for preset in presets:
                apply_preset(task_search, preset)
            task_search.add_op('or')

        text = str(panel.get('text') or '').strip()
        sort_mode = str(query.get('sort') or 'due')
        group_mode = str(query.get('group') or 'none')
        parent_labels = []
        if text or sort_mode == 'object' or group_mode == 'object':
            # Discover only distinct parent types, never the task inventory.
            types_search = Search('sthpw/task')
            types_search.add_op_filters(filters or [])
            types_search.add_column('search_type', distinct=True)
            parent_types = {str(item.get_value('search_type') or '').split('?', 1)[0]
                            for item in types_search.get_sobjects()}
            if text:
                task_search.add_op('begin')
                for column in ('description', 'process', 'context', 'status', 'assigned', 'supervisor', 'search_code'):
                    task_search.add_regex_filter(column, re.escape(text))
                for name, column in columns.items():
                    matches = [str(item['value']) for item in labels.get(name, [])
                               if text.casefold() in str(item.get('label') or item['value']).casefold()]
                    if matches:
                        exact(column, matches)
            for parent_type in sorted(parent_types):
                if not parent_type:
                    continue
                parent_search = Search(parent_type)
                title_column = next((column for column in ('name', 'title', 'code')
                                     if SearchType.column_exists(parent_type, column)), 'code')
                parent_search.add_column('code')
                if text:
                    parent_search.add_regex_filter(title_column, re.escape(text))
                    task_search.add_op('begin')
                    task_search.add_regex_filter('search_type', '^' + re.escape(parent_type) + r'(\?|$)')
                    task_search.add_search_filter('search_code', parent_search)
                    task_search.add_op('and')
                if sort_mode == 'object' or group_mode == 'object':
                    parent_codes = Search('sthpw/task')
                    parent_codes.add_op_filters(filters or [])
                    parent_codes.add_regex_filter('search_type', '^' + re.escape(parent_type) + r'(\?|$)')
                    parent_codes.add_column('search_code', distinct=True)
                    ordering_search = Search(parent_type)
                    ordering_search.add_search_filter('code', parent_codes)
                    ordering_search.add_column('code')
                    ordering_search.add_column(title_column)
                    parent_labels.extend((parent_type, str(item.get_value('code')), str(item.get_value(title_column) or item.get_value('code')))
                                         for item in ordering_search.get_sobjects())
            if text:
                task_search.add_op('or')

        if panel.get('hasNotes'):
            # Match the same contextual branch used by the returned note count.
            # All tables here belong to sthpw; values are correlated, not user SQL.
            table = task_search.search_type_obj.get_table()
            task = '"%s"' % table.replace('"', '""')
            task_type = "split_part(%s.search_type, '?', 1)" % task
            primary_order = "(CASE WHEN {a}.context IS NULL OR {a}.context = '' OR {a}.context = COALESCE(NULLIF({a}.process, ''), 'publish') THEN 0 ELSE 1 END, COALESCE(CAST({a}.timestamp AS TEXT), ''), {a}.code)"
            primary = "NOT EXISTS (SELECT 1 FROM {table} sibling WHERE sibling.project_code = {task}.project_code AND split_part(sibling.search_type, '?', 1) = split_part({task}.search_type, '?', 1) AND sibling.search_code = {task}.search_code AND COALESCE(NULLIF(sibling.process, ''), 'publish') = COALESCE(NULLIF({task}.process, ''), 'publish') AND {left} < {right})".format(
                table=task, task=task, left=primary_order.format(a='sibling'), right=primary_order.format(a=task))
            task_search.add_where("""EXISTS (SELECT 1 FROM note n WHERE n.project_code = {task}.project_code AND (
                (n.search_code = {task}.search_code AND COALESCE(NULLIF(n.process, ''), 'publish') = COALESCE(NULLIF({task}.process, ''), 'publish')
                 AND (n.search_type IS NULL OR n.search_type = '' OR split_part(n.search_type, '?', 1) = {parent_type}) AND {primary})
                OR (n.search_code = {task}.code AND (n.search_type IS NULL OR n.search_type = '' OR split_part(n.search_type, '?', 1) = 'sthpw/task') AND NOT ({primary}))
            ))""".format(task=task, parent_type=task_type, primary=primary))

        def label_order(mode, descending=False):
            # Select preserves its native "( CASE ... END )" orders verbatim;
            # bare CASE/LOWER expressions are quoted as column identifiers.
            column = {'due': 'bid_end_date', 'recent': 'timestamp', 'user': 'assigned',
                      'object': 'search_code', 'search_type': 'search_type',
                      'project': 'project_code'}.get(mode, columns.get(mode))
            if not column:
                raise ValueError('Unknown task ordering: %s' % mode)
            direction = 'DESC' if descending else 'ASC'
            if mode == 'object' and parent_labels:
                branches = ["WHEN split_part(search_type, '?', 1) = %s AND search_code = %s THEN %s" %
                            (Sql.quote(kind), Sql.quote(code), Sql.quote(label.casefold()))
                            for kind, code, label in parent_labels]
                expression = '( CASE ' + ' '.join(branches) + ' ELSE LOWER(search_code) END )'
            elif mode in ('due', 'recent'):
                expression = '"%s"' % column
                if mode == 'due':
                    task_search.get_select().add_order_by('( CASE WHEN "bid_end_date" IS NULL THEN 1 ELSE 0 END )')
                else:
                    direction = 'ASC' if descending else 'DESC'
            else:
                choices = labels.get('assigned' if mode == 'user' else mode) or []
                branches = ['WHEN %s THEN %s' % (Sql.quote(str(item['value'])), Sql.quote(str(item.get('label') or item['value']).casefold()))
                            for item in choices]
                expression = 'LOWER(CAST("%s" AS TEXT))' % column
                if branches:
                    expression = '( CASE CAST("%s" AS TEXT) %s ELSE %s END )' % (column, ' '.join(branches), expression)
                else:
                    expression = '( CASE WHEN "%s" IS NOT NULL THEN %s END )' % (column, expression)
            task_search.get_select().add_order_by(expression, direction=direction)

        if group_mode != 'none':
            label_order(group_mode, bool(query.get('descending')) and group_mode == sort_mode)
            group_column = {'user': 'assigned', 'object': 'search_code',
                            'search_type': 'search_type', 'project': 'project_code'}.get(
                                group_mode, columns.get(group_mode))
            if group_mode == 'object':
                task_search.add_order_by('search_type')
            task_search.add_order_by(group_column)
        label_order(sort_mode, bool(query.get('descending')))
        if sort_mode == 'object':
            label_order('process', bool(query.get('descending')))
        if sort_mode != 'due':
            label_order('due')
        task_search.add_order_by('code')
        order_bys = []
    for order_by in order_bys or []:
        task_search.add_order_by(order_by)
    total = task_search.get_count()
    if limit:
        task_search.set_limit(int(limit))
    if offset:
        task_search.set_offset(int(offset))
    task_objects = task_search.get_sobjects()
    tasks = server.server._get_sobjects_dict(task_objects)

    page_groups = {}
    for info in tasks:
        parent_type = str(info.get('search_type') or '').split('?', 1)[0]
        parent_code = str(info.get('search_code') or '')
        process = str(info.get('process') or 'publish')
        if parent_code:
            page_groups.setdefault(
                (parent_type, parent_code, process), []
            ).append(info)

    all_group_tasks = dict((key, []) for key in page_groups)
    sibling_group_keys = {
        key for key, page_tasks in page_groups.items()
        if len(page_tasks) > 1 or any(
            task.get('context')
            and task.get('context') != key[2] for task in page_tasks
        )
    }
    sibling_search_codes = list(set(
        key[1] for key in sibling_group_keys
    ))
    sibling_processes = list(set(key[2] for key in sibling_group_keys))
    if sibling_search_codes and sibling_processes:
        sibling_search = Search('sthpw/task')
        sibling_search.add_filters('search_code', sibling_search_codes)
        sibling_search.add_filters('process', sibling_processes)
        sibling_search.add_filter('project_code', project_code)
        for task in sibling_search.get_sobjects():
            task_data = task.get_data()
            key = (
                str(task_data.get('search_type') or '').split('?', 1)[0],
                str(task_data.get('search_code') or ''),
                str(task_data.get('process') or 'publish'),
            )
            if key in all_group_tasks:
                all_group_tasks[key].append(task_data)

    for key, page_tasks in page_groups.items():
        group_tasks = all_group_tasks.get(key) or []
        known_codes = set(
            str(task.get('code') or '') for task in group_tasks
        )
        group_tasks.extend(
            task for task in page_tasks
            if str(task.get('code') or '') not in known_codes
        )
        all_group_tasks[key] = group_tasks

    search_codes = list(set(key[1] for key in page_groups))
    processes = list(set(key[2] for key in page_groups))
    root_note_counts = dict((key, 0) for key in page_groups)
    if search_codes and processes:
        note_search = Search('sthpw/note')
        note_search.add_filters('search_code', search_codes)
        note_search.add_filters('process', processes)
        note_search.add_filter('project_code', project_code)
        for note in note_search.get_sobjects():
            parent_type = str(
                note.get_value('search_type') or ''
            ).split('?', 1)[0]
            parent_code = str(note.get_value('search_code') or '')
            process = str(note.get_value('process') or 'publish')
            candidates = [
                key for key in root_note_counts
                if key[1] == parent_code and key[2] == process
                and (not parent_type or key[0] == parent_type)
            ]
            for key in candidates:
                root_note_counts[key] += 1

    task_parent_by_code = {}
    task_note_counts = {}
    primary_by_group = {}
    for key, group_tasks in all_group_tasks.items():
        group_tasks.sort(key=lambda item: (
            0 if not item.get('context')
            or item.get('context') == key[2] else 1,
            item.get('timestamp') or '', item.get('code') or '',
        ))
        primary_by_group[key] = (
            group_tasks[0].get('code') if group_tasks else None
        )
        if len(group_tasks) <= 1:
            continue
        for task in group_tasks:
            task_code = str(task.get('code') or '')
            if task_code:
                task_parent_by_code[task_code] = key

    if task_parent_by_code:
        task_note_search = Search('sthpw/note')
        task_note_search.add_filters(
            'search_code', list(task_parent_by_code)
        )
        task_note_search.add_filter('project_code', project_code)
        for note in task_note_search.get_sobjects():
            parent_type = str(
                note.get_value('search_type') or ''
            ).split('?', 1)[0]
            if parent_type not in ('', 'sthpw/task'):
                continue
            task_code = str(note.get_value('search_code') or '')
            if task_code in task_parent_by_code:
                task_note_counts[task_code] = (
                    task_note_counts.get(task_code, 0) + 1
                )

    for key, page_tasks in page_groups.items():
        primary_code = primary_by_group.get(key)
        for info in page_tasks:
            task_code = str(info.get('code') or '')
            is_primary = task_code == primary_code
            info['__primary_note_branch__'] = is_primary
            info['__notes_count__'] = (
                root_note_counts.get(key, 0) if is_primary
                else task_note_counts.get(task_code, 0)
            )
            info['__tasks_count__'] = 0

    parent_groups = {}
    for info in tasks:
        raw_type = str(info.get('search_type') or '')
        search_type = raw_type.split('?', 1)[0]
        code = str(info.get('search_code') or '')
        if search_type and code:
            parent_groups.setdefault(search_type, set()).add(code)
    parents = []
    for search_type, codes in parent_groups.items():
        parent_search = Search(search_type)
        parent_search.add_filters('code', list(codes))
        parents.extend(
            server.server._get_sobjects_dict(parent_search.get_sobjects())
        )
    return json.dumps({
        'tasks': tasks,
        'parents': parents,
        'total': total,
        'facets': facets,
        'offset': int(offset or 0),
        'limit': int(limit or 0),
    }, separators=(',', ':'))


def query_work_hours(task_codes, project_code, login=None, start_day=None,
                     end_day=None, statuses=None, include_rates=False,
                     parent_codes=None):
    import json
    from pyasm.search import Search, SearchKey
    from pyasm.biz import ProdSetting

    server.set_project(project_code)
    current_login = str(server.get_login() or '')
    is_admin = current_login.lower() == 'admin'
    groups = []
    if not is_admin:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        groups = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
    privileged = is_admin or any(
        group == 'admin' or 'supervisor' in group for group in groups
    )
    view_costs = is_admin or any(
        'finance' in group or 'account' in group for group in groups
    )

    search = Search('sthpw/work_hour')
    search.add_filter('project_code', project_code)
    task_codes = [str(value) for value in (task_codes or []) if value]
    parent_codes = [str(value) for value in (parent_codes or []) if value]
    if task_codes:
        search.add_filters('task_code', task_codes)
    elif parent_codes:
        search.add_filters('search_code', parent_codes)
    if login:
        search.add_filter('login', login)
    if start_day:
        search.add_filter('day', start_day, op='>=')
    if end_day:
        search.add_filter('day', end_day, op='<=')
    statuses = [str(value) for value in (statuses or []) if value]
    if statuses:
        search.add_filters('status', statuses)
    search.add_order_by('day')
    search.add_order_by('start_time')

    entries = []
    logins = set()
    for entry in search.get_sobjects():
        data = entry.get_data()
        owner = str(data.get('login') or '')
        status = str(data.get('status') or '').lower()
        data['__search_key__'] = SearchKey.get_by_sobject(
            entry, use_id=False
        )
        data['__can_edit__'] = bool(
            privileged or (owner == current_login and status != 'approved')
        )
        data['__can_approve__'] = bool(privileged)
        entries.append(data)
        if owner:
            logins.add(owner)

    rates = {}
    if include_rates and view_costs and logins:
        login_search = Search('sthpw/login')
        login_search.add_filters('login', list(logins))
        for login_object in login_search.get_sobjects():
            name = str(login_object.get_value('login') or '')
            rates[name] = login_object.get_value(
                'hourly_wage', no_exception=True
            )

    return json.dumps({
        'entries': entries,
        'bidDurationUnit': str(
            ProdSetting.get_value_by_key('bid_duration_unit') or 'hour'
        ),
        'permissions': {
            'manage': bool(privileged),
            'viewCosts': bool(view_costs),
        },
        'rates': rates,
    }, separators=(',', ':'))


def mutate_user_profile(login, values=None, password=None, groups=None,
                        group_access_levels=None, require_admin=False):
    """Update a TACTIC login through its native security object API."""
    import json
    from pyasm.common import Environment
    from pyasm.search import Search

    current_login = str(server.get_login() or '')
    target_login = str(login or '').strip()
    if not target_login:
        raise ValueError('A login is required')

    if require_admin and not Environment.get_security().is_admin():
        raise PermissionError('Only a TACTIC administrator can manage users')

    group_search = Search('sthpw/login_in_group')
    group_search.add_filter('login', current_login)
    current_groups = [
        str(item.get_value('login_group') or '').lower()
        for item in group_search.get_sobjects()
    ]
    privileged = Environment.get_security().is_admin() or current_login.lower() == 'admin' or any(
        group == 'admin' or 'supervisor' in group
        for group in current_groups
    )
    if target_login != current_login and not privileged:
        raise PermissionError('You may only edit your own profile')

    search = Search('sthpw/login')
    search.set_show_retired(privileged)
    search.add_filter('login', target_login)
    login_object = search.get_sobject()
    if not login_object:
        raise ValueError('The selected user does not exist')

    requested_status = dict(values or {}).get('s_status')
    if target_login == current_login and requested_status == 'retired':
        raise ValueError('You cannot retire the account you are signed in with')

    self_fields = {
        'first_name', 'last_name', 'display_name', 'email',
        'phone_number', 'address', 'department',
    }
    supervisor_fields = {
        'upn', 'namespace', 's_status', 'project_code',
        'license_type', 'hourly_wage',
    }
    allowed = self_fields | (supervisor_fields if privileged else set())
    changed = False
    for name, value in dict(values or {}).items():
        name = str(name or '')
        if name not in allowed or name == 's_status':
            continue
        login_object.set_value(name, value if value is not None else '')
        changed = True
    if changed:
        login_object.commit()

    if privileged and 's_status' in dict(values or {}):
        old_status = login_object.get_value('s_status', no_exception=True)
        if requested_status != old_status:
            if requested_status == 'retired':
                login_object.retire()
            elif old_status == 'retired' and not requested_status:
                login_object.reactivate()
            else:
                login_object.set_value('s_status', requested_status or '')
                login_object.commit()

    password = str(password or '')
    if password:
        setter = getattr(login_object, 'set_password', None)
        if not callable(setter):
            raise RuntimeError('This TACTIC server cannot change passwords')
        setter(password)

    if groups is not None:
        if not privileged:
            raise PermissionError('Only a supervisor can change user groups')
        desired = set(str(value or '') for value in groups if value)
        membership_search = Search('sthpw/login_in_group')
        membership_search.add_filter('login', target_login)
        existing = set(
            str(item.get_value('login_group') or '')
            for item in membership_search.get_sobjects()
        )
        add_to_group = getattr(login_object, 'add_to_group', None)
        remove_from_group = getattr(login_object, 'remove_from_group', None)
        if not callable(add_to_group) or not callable(remove_from_group):
            raise RuntimeError('This TACTIC server has no group membership API')
        for group in sorted(desired - existing):
            add_to_group(group)
        for group in sorted(existing - desired):
            remove_from_group(group)

    changed_access_levels = {}
    if group_access_levels is not None:
        if not privileged:
            raise PermissionError(
                'Only a supervisor can change group access levels'
            )
        requested = dict(group_access_levels or {})
        if len(requested) != len(set(str(key or '') for key in requested)):
            raise ValueError('Each login group may only be updated once')
        normalized_access_levels = {}
        for group_code, access_level in requested.items():
            group_code = str(group_code or '').strip()
            access_level = str(access_level or '').strip()
            if not group_code:
                raise ValueError('A login group code is required')
            if len(access_level) > 32 or any(
                    ord(character) < 32 for character in access_level):
                raise ValueError('Access level must be at most 32 characters')
            if access_level not in ('', 'high', 'medium', 'low', 'min', 'none'):
                raise ValueError(
                    'Access level must be high, medium, low, min, none, or empty'
                )
            normalized_access_levels[group_code] = access_level
        group_objects = {}
        if normalized_access_levels:
            group_search = Search('sthpw/login_group')
            group_search.add_filters(
                'login_group', list(normalized_access_levels)
            )
            group_objects = {
                str(item.get_value('login_group') or ''): item
                for item in group_search.get_sobjects()
            }
        for group_code, access_level in normalized_access_levels.items():
            group_object = group_objects.get(group_code)
            if not group_object:
                raise ValueError('Login group does not exist: %s' % group_code)
            current_level = str(
                group_object.get_value('access_level', no_exception=True) or ''
            )
            if current_level == access_level:
                continue
            group_object.set_value('access_level', access_level)
            group_object.commit()
            changed_access_levels[group_code] = access_level

    data = dict(login_object.get_data())
    data.pop('password', None)
    data['groups'] = sorted(
        set(str(value or '') for value in groups if value)
        if groups is not None else set()
    )
    data['group_access_levels'] = changed_access_levels
    return json.dumps(data, separators=(',', ':'), default=str)


def mutate_sidebar_security(project_code, updates=None):
    """Merge sidebar link visibility into native login-group access rules."""
    import json
    from xml.etree import ElementTree
    from pyasm.search import Search
    from pyasm.security import Sudo

    project_code = str(project_code or '').strip()
    if not project_code:
        raise ValueError('A project code is required')

    current_login = str(server.get_login() or '')
    membership_search = Search('sthpw/login_in_group')
    membership_search.add_filter('login', current_login)
    current_groups = [
        str(item.get_value('login_group') or '').lower()
        for item in membership_search.get_sobjects()
    ]
    privileged = current_login.lower() == 'admin' or any(
        group == 'admin' or 'supervisor' in group
        for group in current_groups
    )
    if not privileged:
        raise PermissionError(
            'Only an administrator or supervisor can edit sidebar security'
        )

    normalized = []
    for update in list(updates or []):
        element_name = str(update.get('element') or '').strip()
        group_code = str(update.get('group_code') or '').strip()
        if not element_name or not group_code:
            raise ValueError('Sidebar element and login group are required')
        normalized.append((
            element_name, group_code, bool(update.get('allowed'))
        ))

    group_codes = sorted(set(item[1] for item in normalized))
    if not group_codes:
        return json.dumps({}, separators=(',', ':'))

    sudo = Sudo()
    try:
        group_search = Search('sthpw/login_group')
        group_search.add_filters('code', group_codes)
        group_objects = {
            str(item.get_value('code') or ''): item
            for item in group_search.get_sobjects()
        }
        missing = [code for code in group_codes if code not in group_objects]
        if missing:
            fallback_search = Search('sthpw/login_group')
            fallback_search.add_filters('login_group', missing)
            for item in fallback_search.get_sobjects():
                group_objects[str(item.get_value('login_group') or '')] = item

        grouped = {}
        for element_name, group_code, allowed in normalized:
            grouped.setdefault(group_code, []).append((element_name, allowed))

        result = {}
        for group_code, group_updates in grouped.items():
            group_object = group_objects.get(group_code)
            if not group_object:
                raise ValueError('Login group does not exist: %s' % group_code)
            source = str(
                group_object.get_value('access_rules', no_exception=True) or ''
            ).strip()
            if source:
                try:
                    root = ElementTree.fromstring(source)
                except ElementTree.ParseError:
                    root = ElementTree.fromstring('<rules>%s</rules>' % source)
                if root.tag == 'rule':
                    wrapper = ElementTree.Element('rules')
                    wrapper.append(root)
                    root = wrapper
            else:
                root = ElementTree.Element('rules')

            for element_name, allowed in group_updates:
                matches = [
                    rule for rule in root.iter('rule')
                    if str(rule.get('group') or '') == 'link'
                    and str(rule.get('element') or '') == element_name
                    and str(rule.get('project') or '') == project_code
                ]
                for rule in matches:
                    for parent in root.iter():
                        if rule in list(parent):
                            parent.remove(rule)
                            break
                if allowed:
                    ElementTree.SubElement(root, 'rule', {
                        'group': 'link',
                        'element': element_name,
                        'access': 'allow',
                        'project': project_code,
                    })

            serialized = ElementTree.tostring(root, encoding='unicode')
            group_object.set_value('access_rules', serialized)
            group_object.commit()
            result[group_code] = serialized
        return json.dumps(result, separators=(',', ':'))
    finally:
        sudo.exit()


def create_user_profile(login, values=None, password=None, groups=None, require_admin=False):
    """Create a TACTIC login through the native login sObject API."""
    import json
    from pyasm.common import Environment
    from pyasm.search import Search
    from pyasm.security import Login

    if require_admin and not Environment.get_security().is_admin():
        raise PermissionError('Only a TACTIC administrator can manage users')

    current_login = str(server.get_login() or '')
    group_search = Search('sthpw/login_in_group')
    group_search.add_filter('login', current_login)
    current_groups = [
        str(item.get_value('login_group') or '').lower()
        for item in group_search.get_sobjects()
    ]
    privileged = Environment.get_security().is_admin() or current_login.lower() == 'admin' or any(
        group == 'admin' or 'supervisor' in group
        for group in current_groups
    )
    if not privileged:
        raise PermissionError('Only an administrator or supervisor can create users')

    target_login = str(login or '').strip()
    if not target_login:
        raise ValueError('A login is required')
    if any(character.isspace() for character in target_login):
        raise ValueError('A login cannot contain spaces')

    duplicate_search = Search('sthpw/login')
    duplicate_search.set_show_retired(True)
    duplicate_search.add_filter('login', target_login)
    if duplicate_search.get_sobject():
        raise ValueError('A user with this login already exists')

    allowed = {
        'first_name', 'last_name', 'display_name', 'email',
        'phone_number', 'address', 'department', 'upn', 'namespace', 's_status',
        'project_code', 'license_type', 'hourly_wage',
    }
    desired_groups = sorted(set(str(value) for value in (groups or []) if value))
    payload = {str(key): value for key, value in dict(values or {}).items()
               if key in allowed and value not in (None, '')}
    login_object = Login.create(target_login, str(password or ''), groups=desired_groups,
                                project_code=payload.get('project_code'))
    for name, value in payload.items():
        login_object.set_value(name, value)
    if payload:
        login_object.commit()

    data = dict(login_object.get_data())
    data.pop('password', None)
    data['groups'] = desired_groups
    return json.dumps(data, separators=(',', ':'), default=str)


def mutate_work_hour(action, project_code, task_code=None, work_hour_code=None,
                     values=None):
    import datetime
    from pyasm.search import Search, SearchType, SearchKey

    server.set_project(project_code)
    values = dict(values or {})
    current_login = str(server.get_login() or '')
    is_admin = current_login.lower() == 'admin'
    groups = []
    if not is_admin:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        groups = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
    privileged = is_admin or any(
        group == 'admin' or 'supervisor' in group for group in groups
    )

    def number(name, default=0.0):
        raw = values.get(name, default)
        if raw in (None, ''):
            return float(default)
        result = float(raw)
        if result < 0 or result > 24:
            raise ValueError('%s must be between 0 and 24 hours' % name)
        return result

    def clean_day(value):
        text = str(value or '')[:10]
        try:
            datetime.datetime.strptime(text, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Work date must use YYYY-MM-DD')
        return '%s 00:00:00' % text

    action = str(action or '').lower()
    approve_requested = bool(values.pop('approve', False))
    if approve_requested and not privileged:
        raise RuntimeError('Only a supervisor can approve work hours')
    entry = None
    if action != 'create':
        search = Search('sthpw/work_hour')
        search.add_filter('code', work_hour_code)
        entry = search.get_sobject()
        if not entry:
            raise RuntimeError('Work-hour entry does not exist')
        owner = str(entry.get_value('login') or '')
        approved = str(entry.get_value('status') or '').lower() == 'approved'
        if not privileged and (owner != current_login or approved):
            raise RuntimeError(
                'Only a supervisor can change this work-hour entry'
            )

    if action == 'delete':
        entry.delete()
        return {'deleted': str(work_hour_code or '')}

    if action in ('approve', 'reject'):
        if not privileged:
            raise RuntimeError('Only a supervisor can approve work hours')
        entry.set_value('status', 'approved' if action == 'approve' else '')
        entry.commit()
        data = entry.get_data()
        data['__search_key__'] = SearchKey.get_by_sobject(
            entry, use_id=False
        )
        return data

    existing_login = str(entry.get_value('login') or '') if entry else ''
    target_login = str(
        values.get('login') or existing_login or current_login
    )
    if target_login != current_login and not privileged:
        raise RuntimeError('Only a supervisor can log time for another user')
    existing_category = str(
        entry.get_value('category') or 'regular'
    ) if entry else 'regular'
    category = str(values.get('category') or existing_category).lower()
    if category not in ('regular', 'overtime'):
        raise ValueError('Unsupported work-hour category')
    existing_duration = (
        entry.get_value('straight_time') or 0 if entry else 0
    )
    duration = number('straight_time', existing_duration)
    if duration <= 0:
        raise ValueError('Duration must be greater than zero')
    day = clean_day(
        values.get('day') or (entry.get_value('day') if entry else None)
    )

    if action == 'create':
        task_search = Search('sthpw/task')
        task_search.add_filter('code', task_code)
        task_search.add_filter('project_code', project_code)
        task = task_search.get_sobject()
        if not task:
            raise RuntimeError('Task does not exist')
        parent = task.get_parent()
        if not parent:
            raise RuntimeError('Task parent does not exist')
        entry = SearchType.create('sthpw/work_hour')
        entry.set_parent(parent)
        entry.set_value('task_code', task.get_code())
        entry.set_value('process', task.get_value('process'))
        entry.set_value('project_code', project_code)
        entry.set_value('login', target_login)
        entry.set_value('status', 'approved' if approve_requested else '')
    elif action != 'update':
        raise ValueError('Unsupported work-hour action')

    entry.set_value('day', day)
    entry.set_value('category', category)
    entry.set_value('straight_time', duration)
    entry.set_value('over_time', duration if category == 'overtime' else 0)
    description = values.get('description')
    if description is None and action == 'update':
        description = entry.get_value('description')
    entry.set_value('description', str(description or ''))
    if values.get('start_time'):
        entry.set_value('start_time', values.get('start_time'))
    if values.get('end_time'):
        entry.set_value('end_time', values.get('end_time'))
    if approve_requested:
        entry.set_value('status', 'approved')

    daily_search = Search('sthpw/work_hour')
    daily_search.add_filter('project_code', project_code)
    daily_search.add_filter('login', target_login)
    daily_search.add_filter('day', day)
    daily_total = 0.0
    for other in daily_search.get_sobjects():
        if entry.get_code() and other.get_code() == entry.get_code():
            continue
        other_value = other.get_value('straight_time') or 0
        daily_total += float(other_value)
    if daily_total + duration > 24:
        raise ValueError('Daily work-hour total cannot exceed 24 hours')

    entry.commit()
    data = entry.get_data()
    data['__search_key__'] = SearchKey.get_by_sobject(entry, use_id=False)
    return data


def set_work_hour_statuses(work_hour_codes, approved, project_code):
    from pyasm.search import Search, SearchKey

    server.set_project(project_code)
    current_login = str(server.get_login() or '')
    is_admin = current_login.lower() == 'admin'
    groups = []
    if not is_admin:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        groups = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
    privileged = is_admin or any(
        group == 'admin' or 'supervisor' in group for group in groups
    )
    if not privileged:
        raise RuntimeError('Only a supervisor can approve work hours')

    codes = list(dict.fromkeys(
        str(value) for value in (work_hour_codes or []) if value
    ))
    if not codes:
        return []
    search = Search('sthpw/work_hour')
    search.add_filter('project_code', project_code)
    search.add_filters('code', codes)
    entries = search.get_sobjects()
    found = {str(entry.get_code() or '') for entry in entries}
    missing = [code for code in codes if code not in found]
    if missing:
        raise RuntimeError('Some work-hour entries no longer exist')

    result = []
    status = 'approved' if approved else ''
    for entry in entries:
        entry.set_value('status', status)
        entry.commit()
        data = entry.get_data()
        data['__search_key__'] = SearchKey.get_by_sobject(
            entry, use_id=False
        )
        result.append(data)
    return result


def query_work_hour_report(report_key, project_code, start_day=None,
                           end_day=None, login=None):
    import json
    from pyasm.search import Search
    from pyasm.biz import ProdSetting

    server.set_project(project_code)
    current_login = str(server.get_login() or '')
    is_admin = current_login.lower() == 'admin'
    groups = []
    if not is_admin:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        groups = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
    privileged = is_admin or any(
        group == 'admin' or 'supervisor' in group for group in groups
    )
    view_costs = is_admin or any(
        'finance' in group or 'account' in group for group in groups
    )

    report_key = str(report_key or 'my_hours')
    protected = report_key in ('approval', 'team', 'process')
    if protected and not privileged:
        raise RuntimeError('This report requires supervisor access')
    if report_key == 'labor_cost' and not view_costs:
        raise RuntimeError('This report requires financial reporting access')

    work_search = Search('sthpw/work_hour')
    work_search.add_filter('project_code', project_code)
    if start_day:
        work_search.add_filter('day', start_day, op='>=')
    if end_day:
        work_search.add_filter('day', end_day, op='<=')
    if report_key == 'my_hours':
        work_search.add_filter('login', login or current_login)
    work_hours = work_search.get_sobjects()

    rows = {}
    message = ''
    if report_key == 'bid_actual':
        task_search = Search('sthpw/task')
        task_search.add_filter('project_code', project_code)
        if start_day:
            task_search.add_filter('bid_end_date', start_day, op='>=')
        if end_day:
            task_search.add_filter('bid_end_date', end_day, op='<=')
        planned = sum(
            float(task.get_value('bid_duration') or 0)
            for task in task_search.get_sobjects()
        )
        unit = str(
            ProdSetting.get_value_by_key('bid_duration_unit') or 'hour'
        )
        if unit == 'minute':
            planned /= 60.0
        rows['Planned'] = planned
        rows['Logged'] = sum(
            float(item.get_value('straight_time') or 0)
            for item in work_hours
        )
    elif report_key == 'approval':
        for item in work_hours:
            label = (
                'Approved'
                if str(item.get_value('status') or '').lower() == 'approved'
                else 'Pending'
            )
            rows[label] = rows.get(label, 0.0) + float(
                item.get_value('straight_time') or 0
            )
    elif report_key == 'team':
        for item in work_hours:
            label = str(item.get_value('login') or 'Unassigned')
            rows[label] = rows.get(label, 0.0) + float(
                item.get_value('straight_time') or 0
            )
    elif report_key == 'process':
        for item in work_hours:
            label = str(item.get_value('process') or 'Unspecified')
            rows[label] = rows.get(label, 0.0) + float(
                item.get_value('straight_time') or 0
            )
    elif report_key == 'labor_cost':
        logins = list(set(
            str(item.get_value('login') or '')
            for item in work_hours if item.get_value('login')
        ))
        rates = {}
        if logins:
            login_search = Search('sthpw/login')
            login_search.add_filters('login', logins)
            rates = {
                str(item.get_value('login') or ''):
                float(item.get_value('hourly_wage') or 0)
                for item in login_search.get_sobjects()
            }
        if not any(rates.values()):
            message = 'No authorized hourly wages are configured.'
        for item in work_hours:
            label = str(item.get_value('login') or 'Unassigned')
            hours = float(item.get_value('straight_time') or 0)
            rows[label] = rows.get(label, 0.0) + hours * rates.get(label, 0)
    else:
        for item in work_hours:
            label = str(item.get_value('day') or '')[:10] or 'Unscheduled'
            rows[label] = rows.get(label, 0.0) + float(
                item.get_value('straight_time') or 0
            )

    result = [
        {'label': label, 'value': value}
        for label, value in sorted(
            rows.items(), key=lambda pair: pair[1], reverse=True
        )
    ]
    return json.dumps({
        'rows': result,
        'permissions': {
            'manage': bool(privileged),
            'viewCosts': bool(view_costs),
        },
        'unit': 'cost' if report_key == 'labor_cost' else 'hours',
        'message': message,
    }, separators=(',', ':'))


def query_chat_conversations():
    import json
    import re
    from pyasm.biz import Snapshot
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType

    current_login = str(server.get_login() or '')
    administrator = bool(Environment.get_security().is_admin())
    required_schema = (
        ('sthpw/message', 'metadata'),
        ('sthpw/message_log', 'metadata'),
    )

    def available_columns(search_type):
        try:
            return set(SearchType.get_columns(search_type) or [])
        except AttributeError as error:
            if 'undefined' not in str(error).lower():
                raise
            return set()

    missing_columns = []
    for search_type, column in required_schema:
        if column not in available_columns(search_type):
            missing_columns.append({
                'searchType': search_type,
                'column': column,
                'dataType': 'text',
            })
    if missing_columns:
        return json.dumps({
            'initialized': False,
            'canInitialize': administrator,
            'missingColumns': missing_columns,
            'conversations': [],
            'canCreateGroup': False,
            'canDeleteMessages': False,
        }, separators=(',', ':'))
    if str(current_login or '').lower() == 'admin':
        privileged = True
    else:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        group_codes = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
        privileged = any(
            group == 'admin' or 'supervisor' in group
            for group in group_codes
        )
    subscription_search = Search('sthpw/subscription')
    subscription_search.add_filter('login', current_login)
    subscription_search.add_filter('category', 'chat')
    own_subscriptions = subscription_search.get_sobjects()
    message_codes = list(set(
        subscription.get_value('message_code')
        for subscription in own_subscriptions
        if subscription.get_value('message_code')
    ))
    if not message_codes:
        return json.dumps({
            'initialized': True,
            'canInitialize': administrator,
            'conversations': [],
            'canCreateGroup': bool(privileged),
            'canDeleteMessages': bool(privileged),
        }, separators=(',', ':'))

    message_search = Search('sthpw/message')
    message_search.add_filters('code', message_codes)
    message_search.add_filter('category', 'chat')
    messages = dict(
        (message.get_code(), message)
        for message in message_search.get_sobjects()
    )
    active_codes = [
        code for code, message in messages.items()
        if message.get_value('status', no_exception=True) != 'deleted'
    ]
    if not active_codes:
        return json.dumps({
            'initialized': True,
            'canInitialize': administrator,
            'conversations': [],
            'canCreateGroup': bool(privileged),
            'canDeleteMessages': bool(privileged),
        }, separators=(',', ':'))

    members_search = Search('sthpw/subscription')
    members_search.add_filters('message_code', active_codes)
    members_search.add_filter('category', 'chat')
    members = members_search.get_sobjects()
    members_by_code = {}
    login_codes = set()
    for member in members:
        code = member.get_value('message_code')
        login = member.get_value('login')
        members_by_code.setdefault(code, []).append(member)
        if login:
            login_codes.add(login)

    display_names = {}
    if login_codes:
        login_search = Search('sthpw/login')
        login_search.add_filters('login', list(login_codes))
        for login in login_search.get_sobjects():
            code = login.get_value('login')
            display_names[code] = (
                login.get_value('display_name', no_exception=True) or code
            )

    metadata_by_code = {}
    for code, message in messages.items():
        raw_metadata = message.get_value('metadata') or {}
        if isinstance(raw_metadata, dict):
            value = dict(raw_metadata)
        else:
            try:
                value = json.loads(raw_metadata)
            except (TypeError, ValueError):
                value = {}
        metadata_by_code[code] = value

    own_by_code = dict(
        (subscription.get_value('message_code'), subscription)
        for subscription in own_subscriptions
    )

    summaries_by_code = {}
    missing_summary_codes = []
    for code in active_codes:
        summary = dict((metadata_by_code.get(code) or {}).get('summary') or {})
        if summary:
            summaries_by_code[code] = summary
        else:
            missing_summary_codes.append(code)

    missing_logs_by_code = {}
    if missing_summary_codes:
        log_search = Search('sthpw/message_log')
        log_search.add_filters('message_code', missing_summary_codes)
        log_search.add_filter('status', 'deleted', op='!=')
        log_search.add_order_by('timestamp', direction='desc')
        log_search.add_order_by('id', direction='desc')
        for message_log in log_search.get_sobjects():
            missing_logs_by_code.setdefault(
                message_log.get_value('message_code'), []
            ).append(message_log)

    attachments_by_code = {}
    missing_log_codes = [
        item.get_code()
        for values in missing_logs_by_code.values()
        for item in values if item.get_code()
    ]
    if missing_log_codes:
        connection_search = Search('sthpw/connection')
        connection_search.add_filter('context', 'chat_attachment')
        connection_search.add_filter('dst_search_type', 'sthpw/message_log')
        connection_search.add_filters('dst_search_code', missing_log_codes)
        log_to_chat = dict(
            (item.get_code(), item.get_value('message_code'))
            for values in missing_logs_by_code.values() for item in values
        )
        for connection in connection_search.get_sobjects():
            chat_code = log_to_chat.get(connection.get_value('dst_search_code'))
            if chat_code:
                attachments_by_code[chat_code] = (
                    attachments_by_code.get(chat_code, 0) + 1
                )

    for code in missing_summary_codes:
        values = missing_logs_by_code.get(code, [])
        latest = values[0] if values else None
        latest_metadata = {}
        if latest:
            raw_metadata = latest.get_value('metadata') or {}
            if isinstance(raw_metadata, dict):
                latest_metadata = dict(raw_metadata)
            else:
                try:
                    latest_metadata = json.loads(raw_metadata)
                except (TypeError, ValueError):
                    latest_metadata = {}
        summary = {
            'latestCode': str(latest.get_code() or '') if latest else '',
            'latestBody': str(latest.get_value('message') or '') if latest else '',
            'latestTimestamp': str(latest.get_value('timestamp') or '') if latest else '',
            'latestSender': str(latest.get_value('login') or '') if latest else '',
            'latestForwarded': bool(latest_metadata.get('forwardedFrom')),
            'messageCount': len(values),
            'attachmentCount': attachments_by_code.get(code, 0),
        }
        summaries_by_code[code] = summary
        message = messages.get(code)
        if message:
            metadata = dict(metadata_by_code.get(code) or {})
            metadata['summary'] = summary
            server.update(
                SearchKey.get_by_sobject(message, use_id=False),
                {'metadata': metadata}, triggers=False,
            )
            metadata_by_code[code] = metadata

    unread_by_code = {}
    mentions_by_code = {}
    cleared_values = [
        str(own_by_code[code].get_value(
            'last_cleared', no_exception=True
        ) or '')[:19]
        for code in active_codes if own_by_code.get(code)
    ]
    unread_search = Search('sthpw/message_log')
    unread_search.add_filters('message_code', active_codes)
    unread_search.add_filter('status', 'deleted', op='!=')
    if cleared_values and all(cleared_values):
        unread_search.add_filter('timestamp', min(cleared_values), op='>')
    unread_logs = unread_search.get_sobjects()
    members_count = dict(
        (code, len(members_by_code.get(code, []))) for code in active_codes
    )
    mention_pattern = re.compile(
        r'(^|[^A-Za-z0-9_.@-])@{0}($|[^A-Za-z0-9_.-])'.format(
            re.escape(str(current_login or ''))
        ), re.IGNORECASE,
    )
    for message_log in unread_logs:
        code = message_log.get_value('message_code')
        own = own_by_code.get(code)
        if not own or message_log.get_value('login') == current_login:
            continue
        timestamp = str(message_log.get_value('timestamp') or '')[:19]
        cleared = str(own.get_value(
            'last_cleared', no_exception=True
        ) or '')[:19]
        if cleared and timestamp <= cleared:
            continue
        unread_by_code[code] = unread_by_code.get(code, 0) + 1
        if members_count.get(code, 0) > 2 and mention_pattern.search(
                str(message_log.get_value('message') or '')):
            mentions_by_code[code] = mentions_by_code.get(code, 0) + 1

    previews_by_code = {}
    snapshot_search = Search('sthpw/snapshot')
    snapshot_search.add_filter('search_type', 'sthpw/message')
    snapshot_search.add_filters('search_code', active_codes)
    snapshot_search.add_filter('process', 'icon')
    snapshot_search.add_order_by('timestamp', direction='desc')
    preview_snapshots = snapshot_search.get_sobjects()
    preview_files = Snapshot.get_files_dict_by_snapshots(preview_snapshots)
    for snapshot in preview_snapshots:
        code = snapshot.get_value('search_code')
        if code in previews_by_code:
            continue
        snapshot_data = snapshot.get_data()
        snapshot_data['__files__'] = [
            file_object.get_data()
            for file_object in (preview_files.get(snapshot.get_code()) or [])
        ]
        previews_by_code[code] = snapshot_data

    conversations = []
    for code in active_codes:
        own = own_by_code.get(code)
        if not own:
            continue
        recipients = sorted(set(
            member.get_value('login')
            for member in members_by_code.get(code, [])
            if member.get_value('login') not in (None, '', current_login)
        ))
        recipient_names = [
            display_names.get(login, login) for login in recipients
        ]
        generated_title = ', '.join(recipient_names) or display_names.get(
            current_login, current_login
        )
        last_cleared = own.get_value('last_cleared', no_exception=True)
        unread = unread_by_code.get(code, 0)
        mention_count = mentions_by_code.get(code, 0)
        summary = summaries_by_code.get(code) or {}
        participants = len(recipients) + 1
        message = messages[code]
        custom_title = (
            (metadata_by_code.get(code) or {}).get('title') or ''
        )
        owner = message.get_value('login', no_exception=True) or ''
        personal_notes = participants == 1
        conversations.append({
            'conversationId': code,
            'title': 'Notes' if personal_notes else custom_title or generated_title,
            'customTitle': bool(custom_title) and not personal_notes,
            'recipients': recipients,
            'recipientNames': recipient_names,
            'status': message.get_value('status', no_exception=True) or '',
            'lastCleared': str(last_cleared or ''),
            'unread': unread,
            'mentionCount': mention_count,
            'lastMessage': (
                'Forwarded message'
                if summary.get('latestForwarded')
                else str(summary.get('latestBody') or '')
            ),
            'lastTimestamp': str(summary.get('latestTimestamp') or ''),
            'lastSender': str(summary.get('latestSender') or ''),
            'participantCount': participants,
            'messageCount': int(summary.get('messageCount') or 0),
            'attachmentCount': int(summary.get('attachmentCount') or 0),
            'createdBy': owner,
            'createdAt': str(message.get_value('timestamp', no_exception=True) or ''),
            'canManage': bool(privileged or owner == current_login),
            'canRename': bool(not personal_notes and (privileged or owner == current_login)),
            'canDelete': bool(privileged and not personal_notes),
            'canAddMembers': bool(privileged and not personal_notes),
            'canClearPersonal': bool(personal_notes),
            'isPersonalNotes': bool(personal_notes),
            'preview': previews_by_code.get(code) or {},
        })
    conversations.sort(
        key=lambda record: (record['lastTimestamp'], record['title']),
        reverse=True,
    )
    return json.dumps(
        {
            'initialized': True,
            'canInitialize': administrator,
            'conversations': conversations,
            'canCreateGroup': bool(privileged),
            'canDeleteMessages': bool(privileged),
        }, separators=(',', ':')
    )


def create_chat_conversation(recipients, title=''):
    import json
    import uuid
    from pyasm.search import Search

    current_login = server.get_login()
    if str(current_login or '').lower() == 'admin':
        privileged = True
    else:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        group_codes = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
        privileged = any(
            group == 'admin' or 'supervisor' in group
            for group in group_codes
        )
    participants = set(
        str(login).strip() for login in (recipients or []) if str(login).strip()
    )
    participants.add(current_login)
    if len(participants) > 2 and not privileged:
        raise RuntimeError(
            'Only administrators and supervisors can create group chats'
        )
    if isinstance(title, dict):
        title = title.get('value')
    title = (title or '').strip()
    if len(participants) > 2 and not title:
        raise ValueError('Group chat title is required')
    login_search = Search('sthpw/login')
    login_search.add_filters('login', list(participants))
    existing_logins = set(
        login.get_value('login') for login in login_search.get_sobjects()
    )
    missing = sorted(participants - existing_logins)
    if missing:
        raise ValueError('Unknown TACTIC login: {0}'.format(', '.join(missing)))

    own_search = Search('sthpw/subscription')
    own_search.add_filter('login', current_login)
    own_search.add_filter('category', 'chat')
    own_codes = list(set(
        subscription.get_value('message_code')
        for subscription in own_search.get_sobjects()
        if subscription.get_value('message_code')
    ))
    if own_codes:
        message_search = Search('sthpw/message')
        message_search.add_filters('code', own_codes)
        message_search.add_filter('category', 'chat')
        valid_codes = set(
            message.get_code() for message in message_search.get_sobjects()
            if message.get_value('status', no_exception=True) != 'deleted'
        )
        member_search = Search('sthpw/subscription')
        member_search.add_filters('message_code', list(valid_codes))
        member_search.add_filter('category', 'chat')
        grouped = {}
        for subscription in member_search.get_sobjects():
            grouped.setdefault(
                subscription.get_value('message_code'), set()
            ).add(subscription.get_value('login'))
        for code, members in grouped.items():
            if members == participants:
                return json.dumps(
                    {'conversationId': code, 'created': False},
                    separators=(',', ':'),
                )

    code = 'CHAT_{0}'.format(uuid.uuid4().hex.upper())
    metadata = {
        'summary': {
            'latestCode': '',
            'latestBody': '',
            'latestTimestamp': '',
            'latestSender': '',
            'latestForwarded': False,
            'messageCount': 0,
            'attachmentCount': 0,
        },
    }
    if title:
        metadata['title'] = title
    server.insert('sthpw/message', {
        'code': code,
        'category': 'chat',
        'login': current_login,
        'project_code': 'sthpw',
        'message': '',
        'metadata': metadata,
    }, triggers=True)
    for login in sorted(participants):
        server.insert('sthpw/subscription', {
            'message_code': code,
            'login': login,
            'project_code': 'sthpw',
            'category': 'chat',
        }, triggers=True)
    return json.dumps(
        {'conversationId': code, 'created': True}, separators=(',', ':')
    )


def update_chat_conversation(message_code, title):
    import json
    from pyasm.search import Search, SearchKey

    current_login = server.get_login()
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('login', current_login)
    member_search.add_filter('category', 'chat')
    if not member_search.get_sobject():
        raise RuntimeError('The current login is not a chat participant')
    message_search = Search('sthpw/message')
    message_search.add_filter('code', message_code)
    message_search.add_filter('category', 'chat')
    message = message_search.get_sobject()
    if not message or message.get_value('status', no_exception=True) == 'deleted':
        raise RuntimeError('Chat does not exist')
    if str(current_login or '').lower() == 'admin':
        privileged = True
    else:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        group_codes = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
        privileged = any(
            group == 'admin' or 'supervisor' in group
            for group in group_codes
        )
    owner = message.get_value('login', no_exception=True) or ''
    if owner != current_login and not privileged:
        raise RuntimeError('Only the chat owner or a supervisor can rename it')
    members = Search('sthpw/subscription')
    members.add_filter('message_code', message_code)
    members.add_filter('category', 'chat')
    if len(members.get_sobjects()) == 1:
        raise RuntimeError('The personal notes chat has a fixed title')
    if isinstance(title, dict):
        title = title.get('value')
    title = (title or '').strip()
    if not title:
        raise ValueError('Chat title cannot be empty')
    raw_metadata = message.get_value('metadata') or {}
    if isinstance(raw_metadata, dict):
        values = dict(raw_metadata)
    else:
        try:
            values = json.loads(raw_metadata)
        except (TypeError, ValueError):
            values = {}
    values['title'] = title
    server.update(
        SearchKey.get_by_sobject(message, use_id=False),
        {'metadata': values},
        triggers=True,
    )
    return json.dumps({'title': title}, separators=(',', ':'))


def add_chat_members(message_code, recipients, replace=False):
    import json
    from pyasm.search import Search, SearchKey

    current_login = server.get_login()
    member_access = Search('sthpw/subscription')
    member_access.add_filter('message_code', message_code)
    member_access.add_filter('login', current_login)
    member_access.add_filter('category', 'chat')
    if not member_access.get_sobject():
        raise RuntimeError('The current login is not a chat participant')
    message_search = Search('sthpw/message')
    message_search.add_filter('code', message_code)
    message_search.add_filter('category', 'chat')
    message = message_search.get_sobject()
    if not message or message.get_value('status', no_exception=True) == 'deleted':
        raise RuntimeError('Chat does not exist')
    all_members = Search('sthpw/subscription')
    all_members.add_filter('message_code', message_code)
    all_members.add_filter('category', 'chat')
    if len(all_members.get_sobjects()) == 1:
        raise RuntimeError('Members cannot be added to the personal notes chat')
    if str(current_login or '').lower() == 'admin':
        privileged = True
    else:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        group_codes = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
        privileged = any(
            group == 'admin' or 'supervisor' in group
            for group in group_codes
        )
    if not privileged:
        raise RuntimeError(
            'Only administrators and supervisors can add chat members'
        )
    recipients = set(
        str(login).strip() for login in (recipients or []) if str(login).strip()
    )
    recipients.discard(current_login)
    if replace and not recipients:
        raise ValueError('A group chat must have at least one other member')
    if not recipients:
        return json.dumps({'added': []}, separators=(',', ':'))
    login_search = Search('sthpw/login')
    login_search.add_filters('login', list(recipients))
    existing_logins = set(
        login.get_value('login') for login in login_search.get_sobjects()
    )
    missing = sorted(recipients - existing_logins)
    if missing:
        raise ValueError('Unknown TACTIC login: {0}'.format(', '.join(missing)))
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('category', 'chat')
    existing = set(
        item.get_value('login') for item in member_search.get_sobjects()
    )
    added = sorted(recipients - existing)
    for login in added:
        server.insert('sthpw/subscription', {
            'message_code': message_code,
            'login': login,
            'project_code': 'sthpw',
            'category': 'chat',
        }, triggers=True)
    removed = []
    if replace:
        removed = sorted(existing - recipients - set([current_login]))
        for subscription in member_search.get_sobjects():
            if subscription.get_value('login') in removed:
                server.delete_sobject(
                    SearchKey.get_by_sobject(subscription, use_id=False)
                )
    return json.dumps(
        {'added': added, 'removed': removed}, separators=(',', ':')
    )


def delete_chat_conversation(message_code):
    import json
    from pyasm.search import Search, SearchKey

    current_login = server.get_login()
    if str(current_login or '').lower() == 'admin':
        privileged = True
    else:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        group_codes = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
        privileged = any(
            group == 'admin' or 'supervisor' in group
            for group in group_codes
        )
    if not privileged:
        raise RuntimeError('Only administrators and supervisors can delete chats')
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('login', current_login)
    member_search.add_filter('category', 'chat')
    if not member_search.get_sobject():
        raise RuntimeError('The current login is not a chat participant')
    message_search = Search('sthpw/message')
    message_search.add_filter('code', message_code)
    message_search.add_filter('category', 'chat')
    message = message_search.get_sobject()
    if not message or message.get_value('status', no_exception=True) == 'deleted':
        raise RuntimeError('Chat does not exist')
    all_members = Search('sthpw/subscription')
    all_members.add_filter('message_code', message_code)
    all_members.add_filter('category', 'chat')
    if len(all_members.get_sobjects()) == 1:
        raise RuntimeError('The personal notes chat cannot be deleted')
    server.update(
        SearchKey.get_by_sobject(message, use_id=False),
        {'status': 'deleted'},
        triggers=True,
    )
    return json.dumps({'deleted': True}, separators=(',', ':'))


def clear_personal_chat(message_code):
    import json
    from pyasm.search import Search, SearchKey

    current_login = server.get_login()
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('category', 'chat')
    members = member_search.get_sobjects()
    member_logins = set(item.get_value('login') for item in members)
    if member_logins != set([current_login]):
        raise RuntimeError('Only a personal notes chat can be cleared')
    log_search = Search('sthpw/message_log')
    log_search.add_filter('message_code', message_code)
    cleared = 0
    for message_log in log_search.get_sobjects():
        if message_log.get_value('status', no_exception=True) == 'deleted':
            continue
        server.update(
            SearchKey.get_by_sobject(message_log, use_id=False),
            {'status': 'deleted'},
            triggers=True,
        )
        cleared += 1
    message_search = Search('sthpw/message')
    message_search.add_filter('code', message_code)
    message_search.add_filter('category', 'chat')
    conversation = message_search.get_sobject()
    if conversation:
        raw_metadata = conversation.get_value('metadata') or {}
        if isinstance(raw_metadata, dict):
            metadata = dict(raw_metadata)
        else:
            try:
                metadata = json.loads(raw_metadata)
            except (TypeError, ValueError):
                metadata = {}
        metadata['summary'] = {
            'latestCode': '',
            'latestBody': '',
            'latestTimestamp': '',
            'latestSender': '',
            'latestForwarded': False,
            'messageCount': 0,
            'attachmentCount': 0,
        }
        server.update(
            SearchKey.get_by_sobject(conversation, use_id=False),
            {'metadata': metadata}, triggers=False,
        )
    return json.dumps({'cleared': cleared}, separators=(',', ':'))


def delete_chat_message(message_log_code):
    import json
    from pyasm.search import Search, SearchKey

    current_login = server.get_login()
    message_log_ref = str(message_log_code or '')
    message_log = None
    if message_log_ref.startswith('sthpw/message_log'):
        search_type = server.split_search_key(message_log_ref)[0]
        if search_type == 'sthpw/message_log':
            message_log = Search.get_by_search_key(message_log_ref)
    else:
        log_search = Search('sthpw/message_log')
        log_search.add_filter('code', message_log_ref)
        message_log = log_search.get_sobject()
    if not message_log:
        raise RuntimeError('Message does not exist')
    if not message_log.get_code():
        raise RuntimeError('TACTIC message log has no code')
    message_code = message_log.get_value('message_code')
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('category', 'chat')
    member_logins = set(
        item.get_value('login') for item in member_search.get_sobjects()
    )
    if current_login not in member_logins:
        raise RuntimeError('The current login is not a chat participant')
    personal_notes = member_logins == set([current_login])
    if str(current_login or '').lower() == 'admin':
        privileged = True
    else:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        group_codes = [
            str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        ]
        privileged = any(
            group == 'admin' or 'supervisor' in group
            for group in group_codes
        )
    if not privileged and not personal_notes:
        raise RuntimeError(
            'Only administrators and supervisors can delete messages'
        )
    server.update(
        SearchKey.get_by_sobject(message_log, use_id=False),
        {'status': 'deleted'},
        triggers=True,
    )
    attachment_search = Search('sthpw/connection')
    attachment_search.add_filter('context', 'chat_attachment')
    attachment_search.add_filter('dst_search_type', 'sthpw/message_log')
    attachment_search.add_filter('dst_search_code', message_log.get_code())
    deleted_attachment_count = len(attachment_search.get_sobjects())
    conversation_search = Search('sthpw/message')
    conversation_search.add_filter('code', message_code)
    conversation_search.add_filter('category', 'chat')
    conversation = conversation_search.get_sobject()
    if conversation:
        raw_metadata = conversation.get_value('metadata') or {}
        if isinstance(raw_metadata, dict):
            conversation_metadata = dict(raw_metadata)
        else:
            try:
                conversation_metadata = json.loads(raw_metadata)
            except (TypeError, ValueError):
                conversation_metadata = {}
        summary = dict(conversation_metadata.get('summary') or {})
        summary['messageCount'] = max(
            0, int(summary.get('messageCount') or 0) - 1
        )
        summary['attachmentCount'] = max(
            0,
            int(summary.get('attachmentCount') or 0)
            - deleted_attachment_count,
        )
        if str(summary.get('latestCode') or '') == str(message_log.get_code() or ''):
            latest_search = Search('sthpw/message_log')
            latest_search.add_filter('message_code', message_code)
            latest_search.add_filter('status', 'deleted', op='!=')
            latest_search.add_order_by('timestamp', direction='desc')
            latest_search.add_order_by('id', direction='desc')
            latest_search.set_limit(1)
            latest = latest_search.get_sobject()
            latest_metadata = {}
            if latest:
                raw_latest_metadata = latest.get_value('metadata') or {}
                if isinstance(raw_latest_metadata, dict):
                    latest_metadata = dict(raw_latest_metadata)
                else:
                    try:
                        latest_metadata = json.loads(raw_latest_metadata)
                    except (TypeError, ValueError):
                        latest_metadata = {}
            summary.update({
                'latestCode': str(latest.get_code() or '') if latest else '',
                'latestBody': str(latest.get_value('message') or '') if latest else '',
                'latestTimestamp': str(
                    latest.get_value('timestamp') or ''
                ) if latest else '',
                'latestSender': str(
                    latest.get_value('login') or ''
                ) if latest else '',
                'latestForwarded': bool(
                    latest_metadata.get('forwardedFrom')
                ),
            })
        conversation_metadata['summary'] = summary
        server.update(
            SearchKey.get_by_sobject(conversation, use_id=False),
            {
                'metadata': conversation_metadata,
                'project_code': 'sthpw',
            }, triggers=False,
        )
    return json.dumps({
        'deleted': True,
        'messageCode': message_code,
    }, separators=(',', ':'))


def edit_chat_message(message_log_code, message):
    import datetime
    import json
    from pyasm.search import Search, SearchKey

    current_login = server.get_login()
    message_log_ref = str(message_log_code or '')
    if message_log_ref.startswith('sthpw/message_log'):
        message_log = Search.get_by_search_key(message_log_ref)
    else:
        log_search = Search('sthpw/message_log')
        log_search.add_filter('code', message_log_ref)
        message_log = log_search.get_sobject()
    if not message_log:
        raise RuntimeError('Message does not exist')
    if not message_log.get_code():
        raise RuntimeError('TACTIC message log has no code')
    message_code = message_log.get_value('message_code')
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('login', current_login)
    member_search.add_filter('category', 'chat')
    if not member_search.get_sobject():
        raise RuntimeError('The current login is not a chat participant')
    author = message_log.get_value('login')
    privileged = str(current_login or '').lower() == 'admin'
    if not privileged:
        group_search = Search('sthpw/login_in_group')
        group_search.add_filter('login', current_login)
        privileged = any(
            str(item.get_value('login_group') or '').lower() == 'admin'
            or 'supervisor' in str(item.get_value('login_group') or '').lower()
            for item in group_search.get_sobjects()
        )
    if current_login != author and not privileged:
        raise RuntimeError('A message can only be edited by its author or a supervisor')
    value = str(message or '').strip()
    if not value:
        raise ValueError('Message text cannot be empty')
    if value == str(message_log.get_value('message') or ''):
        return json.dumps({'edited': False}, separators=(',', ':'))

    message_log_key = SearchKey.get_by_sobject(message_log, use_id=False)
    raw_metadata = message_log.get_value('metadata') or {}
    if isinstance(raw_metadata, dict):
        metadata_values = dict(raw_metadata)
    else:
        try:
            metadata_values = json.loads(raw_metadata)
        except (TypeError, ValueError):
            metadata_values = {}
    history = list(metadata_values.get('editHistory') or [])
    edited_at = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    history.append({
        'body': str(message_log.get_value('message') or ''),
        'editedBy': current_login,
        'editedAt': edited_at,
    })
    metadata_values['editHistory'] = history
    server.update(
        message_log_key,
        {
            'message': value,
            'metadata': metadata_values,
        },
        triggers=True,
    )
    conversation_search = Search('sthpw/message')
    conversation_search.add_filter('code', message_code)
    conversation_search.add_filter('category', 'chat')
    conversation = conversation_search.get_sobject()
    if conversation:
        raw_conversation_metadata = conversation.get_value('metadata') or {}
        if isinstance(raw_conversation_metadata, dict):
            conversation_metadata = dict(raw_conversation_metadata)
        else:
            try:
                conversation_metadata = json.loads(raw_conversation_metadata)
            except (TypeError, ValueError):
                conversation_metadata = {}
        summary = dict(conversation_metadata.get('summary') or {})
        if str(summary.get('latestCode') or '') == str(message_log.get_code() or ''):
            summary['latestBody'] = value
            conversation_metadata['summary'] = summary
            server.update(
                SearchKey.get_by_sobject(conversation, use_id=False),
                {
                    'metadata': conversation_metadata,
                    'project_code': 'sthpw',
                }, triggers=False,
            )
    return json.dumps({
        'edited': True,
        'editedBy': current_login,
        'editedAt': edited_at,
        'editHistory': history,
    }, separators=(',', ':'))


def toggle_chat_message_reaction(message_log_code, emoji):
    import datetime
    import json
    from pyasm.search import Search, SearchKey

    current_login = str(server.get_login() or '')
    emoji = str(emoji or '').strip()
    if not emoji or len(emoji) > 16 or any(char.isspace() for char in emoji):
        raise ValueError('Invalid message reaction')

    message_log_ref = str(message_log_code or '')
    if message_log_ref.startswith('sthpw/message_log'):
        message_log = Search.get_by_search_key(message_log_ref)
    else:
        log_search = Search('sthpw/message_log')
        log_search.add_filter('code', message_log_ref)
        message_log = log_search.get_sobject()
    if not message_log or message_log.get_value(
            'status', no_exception=True) == 'deleted':
        raise RuntimeError('Message does not exist')

    message_code = str(message_log.get_value('message_code') or '')
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('login', current_login)
    member_search.add_filter('category', 'chat')
    if not member_search.get_sobject():
        raise RuntimeError('The current login is not a chat participant')

    raw_metadata = message_log.get_value('metadata') or {}
    if isinstance(raw_metadata, dict):
        metadata = dict(raw_metadata)
    else:
        try:
            metadata = json.loads(raw_metadata)
        except (TypeError, ValueError):
            metadata = {}
    reactions = dict(metadata.get('reactions') or {})
    logins = list(dict.fromkeys(
        str(login) for login in (reactions.get(emoji) or []) if login
    ))
    active = current_login not in logins
    if active:
        logins.append(current_login)
        reactions[emoji] = logins
    else:
        logins.remove(current_login)
        if logins:
            reactions[emoji] = logins
        else:
            reactions.pop(emoji, None)
    updated_at = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
    metadata['reactions'] = reactions
    metadata['reactionUpdatedAt'] = updated_at
    message_log_key = SearchKey.get_by_sobject(message_log, use_id=False)
    server.update(
        message_log_key, {'metadata': metadata}, triggers=True,
    )
    return json.dumps({
        'messageId': message_log_key,
        'messageCode': message_code,
        'reactions': reactions,
        'reactionUpdatedAt': updated_at,
        'active': active,
    }, separators=(',', ':'))


def pin_chat_message(message_log_code, unpin=False):
    import datetime
    import json
    from pyasm.search import Search, SearchKey

    current_login = server.get_login()
    message_log_ref = str(message_log_code or '')
    if message_log_ref.startswith('sthpw/message_log'):
        message_log = Search.get_by_search_key(message_log_ref)
    else:
        log_search = Search('sthpw/message_log')
        log_search.add_filter('code', message_log_ref)
        message_log = log_search.get_sobject()
    if not message_log:
        raise RuntimeError('Message does not exist')
    if not message_log.get_code():
        raise RuntimeError('TACTIC message log has no code')
    message_code = message_log.get_value('message_code')
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('login', current_login)
    member_search.add_filter('category', 'chat')
    if not member_search.get_sobject():
        raise RuntimeError('The current login is not a chat participant')

    conversation_search = Search('sthpw/message')
    conversation_search.add_filter('code', message_code)
    conversation_search.add_filter('category', 'chat')
    conversation = conversation_search.get_sobject()
    if not conversation:
        raise RuntimeError('Chat does not exist')
    raw_metadata = conversation.get_value('metadata') or {}
    if isinstance(raw_metadata, dict):
        value = dict(raw_metadata)
    else:
        try:
            value = json.loads(raw_metadata)
        except (TypeError, ValueError):
            value = {}
    if unpin:
        current = dict(value.get('pin') or {})
        current_id = str(current.get('messageId') or '')
        message_id = SearchKey.get_by_sobject(message_log, use_id=False)
        if current_id == message_id:
            value['pin'] = {}
            server.update(
                SearchKey.get_by_sobject(conversation, use_id=False),
                {'metadata': value},
                triggers=True,
            )
        return json.dumps(value, separators=(',', ':'))
    pinned_at = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    message_id = SearchKey.get_by_sobject(message_log, use_id=False)
    pinned = {
        'messageId': message_id,
        'pinnedBy': str(current_login or ''),
        'pinnedAt': pinned_at,
    }
    history = list(value.get('pinHistory') or [])
    history.append({
        'messageId': message_id,
        'body': str(message_log.get_value('message') or ''),
        'sender': str(message_log.get_value('login') or ''),
        'timestamp': str(message_log.get_value('timestamp') or ''),
        'pinnedBy': str(current_login or ''),
        'pinnedAt': pinned_at,
    })
    value['pin'] = pinned
    value['pinHistory'] = history
    server.update(
        SearchKey.get_by_sobject(conversation, use_id=False),
        {'metadata': value},
        triggers=True,
    )
    return json.dumps(value, separators=(',', ':'))


def query_chat_history(message_code, limit=31, offset=0, search_text=''):
    import json
    from datetime import datetime
    from pyasm.biz import Snapshot
    from pyasm.search import Search, SearchKey

    def aggregate_delivery(delivery):
        recipients = dict((delivery or {}).get('recipients') or {})
        receipts = list(recipients.values())
        if receipts and all(item.get('readAt') for item in receipts):
            return 'read'
        if receipts and all(item.get('deliveredAt') for item in receipts):
            return 'delivered'
        return 'sent'

    def delivery_record(delivery):
        value = dict(delivery or {})
        recipients = dict(value.get('recipients') or {})
        receipts = list(recipients.values())
        return {
            'status': aggregate_delivery(value),
            'sentAt': str(value.get('sentAt') or ''),
            'recipientCount': len(receipts),
            'deliveredCount': len([
                item for item in receipts if item.get('deliveredAt')
            ]),
            'readCount': len([
                item for item in receipts if item.get('readAt')
            ]),
        }

    current_login = str(server.get_login() or '')
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('login', current_login)
    member_search.add_filter('category', 'chat')
    if not member_search.get_sobject():
        raise RuntimeError('The current login is not a chat participant')

    history_search = Search('sthpw/message_log')
    history_search.add_filter('message_code', message_code)
    history_search.add_filter('status', 'deleted', op='!=')
    search_text = str(search_text or '').strip()
    if search_text:
        history_search.add_filter('message', '%{0}%'.format(search_text), op='like')
    history_search.add_order_by('timestamp', direction='desc')
    history_search.add_order_by('id', direction='desc')
    history_search.set_limit(int(limit))
    if offset:
        history_search.set_offset(int(offset))
    history = history_search.get_sobjects()
    history = [item for item in history if item.get_code()]
    history_codes = [item.get_code() for item in history if item.get_code()]

    metadata_by_log = {}
    delivery_updates = {}
    delivered_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    target_refs = set()
    for message_log in history:
        raw_metadata = message_log.get_value('metadata') or {}
        if isinstance(raw_metadata, dict):
            value = dict(raw_metadata)
        else:
            try:
                value = json.loads(raw_metadata)
            except (TypeError, ValueError):
                value = {}
        delivery = dict(value.get('delivery') or {})
        recipients = dict(delivery.get('recipients') or {})
        receipt = dict(recipients.get(str(current_login or '')) or {})
        sender = str(
            delivery.get('sender') or message_log.get_value('login') or ''
        )
        if (
                sender != current_login and receipt
                and not receipt.get('deliveredAt')):
            receipt['deliveredAt'] = delivered_at
            recipients[current_login] = receipt
            delivery['recipients'] = recipients
            value['delivery'] = delivery
            delivery_updates[SearchKey.get_by_sobject(
                message_log, use_id=False
            )] = {
                'metadata': value,
                'status': aggregate_delivery(delivery),
                'project_code': 'sthpw',
            }
        metadata_by_log[str(message_log.get_code() or '')] = value
        for field in ('replyTo', 'forwardedFrom'):
            target_ref = str(value.get(field) or '')
            if target_ref:
                target_refs.add(target_ref)
    if delivery_updates:
        # Receipt changes must create a change timestamp so the sender can
        # update the visible ticks without reloading the conversation.
        server.update_multiple(data=delivery_updates, triggers=True)

    reply_targets = {}
    target_codes = []
    for target_ref in target_refs:
        search_type, target_code = server.split_search_key(target_ref)
        if search_type == 'sthpw/message_log' and target_code:
            target_codes.append(target_code)
    if target_codes:
        target_search = Search('sthpw/message_log')
        target_search.add_filters('code', list(set(target_codes)))
        for target in target_search.get_sobjects():
            reply_targets[str(target.get_code())] = target

    attachments_by_log = {}
    attachment_codes = list(history_codes) + [
        target.get_code() for target in reply_targets.values() if target.get_code()
    ]
    if attachment_codes:
        connection_search = Search('sthpw/connection')
        connection_search.add_filter('context', 'chat_attachment')
        connection_search.add_filter('dst_search_type', 'sthpw/message_log')
        connection_search.add_filters(
            'dst_search_code', list(set(attachment_codes))
        )
        connections = connection_search.get_sobjects()
        snapshot_codes = []
        snapshot_to_logs = {}
        for connection in connections:
            if connection.get_value('src_search_type') != 'sthpw/snapshot':
                continue
            snapshot_code = connection.get_value('src_search_code')
            log_code = connection.get_value('dst_search_code')
            if snapshot_code:
                snapshot_codes.append(snapshot_code)
                snapshot_to_logs.setdefault(snapshot_code, []).append(log_code)
        if snapshot_codes:
            snapshot_search = Search('sthpw/snapshot')
            snapshot_search.add_filters('code', list(set(snapshot_codes)))
            snapshots = snapshot_search.get_sobjects()
            files = Snapshot.get_files_dict_by_snapshots(snapshots)
            for snapshot in snapshots:
                snapshot_data = snapshot.get_data()
                snapshot_data['__search_key__'] = SearchKey.get_by_sobject(
                    snapshot, use_id=False
                )
                snapshot_data['__files__'] = [
                    file_object.get_data()
                    for file_object in (files.get(snapshot.get_code()) or [])
                ]
                for log_code in snapshot_to_logs.get(snapshot.get_code(), []):
                    attachments_by_log.setdefault(log_code, []).append(
                        snapshot_data
                    )

    conversation_metadata = {}
    pin_search = Search('sthpw/message')
    pin_search.add_filter('code', message_code)
    pin_search.add_filter('category', 'chat')
    conversation = pin_search.get_sobject()
    if conversation:
        raw_metadata = conversation.get_value('metadata') or {}
        if isinstance(raw_metadata, dict):
            conversation_metadata = dict(raw_metadata)
        else:
            try:
                conversation_metadata = json.loads(raw_metadata)
            except (TypeError, ValueError):
                conversation_metadata = {}
    pin_value = dict(conversation_metadata.get('pin') or {})
    pin_message_id = str(pin_value.get('messageId') or '')
    if pin_message_id:
        pin_target = Search.get_by_search_key(pin_message_id)
        if pin_target and pin_target.get_value(
                'status', no_exception=True) != 'deleted':
            pin_value.update({
                'body': str(pin_target.get_value('message') or ''),
                'sender': str(pin_target.get_value('login') or ''),
                'timestamp': str(pin_target.get_value('timestamp') or ''),
            })
        else:
            pin_value = {}

    records = []
    for message_log in history:
        data = message_log.get_data()
        data['__search_key__'] = SearchKey.get_by_sobject(
            message_log, use_id=False
        )
        log_code = str(message_log.get_code() or '')
        data['__attachments__'] = attachments_by_log.get(log_code, [])
        message_metadata = metadata_by_log.get(
            log_code, {}
        )
        data['__edit_history__'] = list(
            message_metadata.get('editHistory') or []
        )
        data['__reactions__'] = dict(
            message_metadata.get('reactions') or {}
        )
        data['__delivery__'] = delivery_record(
            message_metadata.get('delivery') or {}
        )
        reply_ref = str(message_metadata.get('replyTo') or '')
        if reply_ref:
            target_code = server.split_search_key(reply_ref)[1]
            target = reply_targets.get(str(target_code))
            if target:
                data['__reply__'] = {
                    'messageId': SearchKey.get_by_sobject(target, use_id=False),
                    'sender': str(target.get_value('login') or ''),
                    'body': str(target.get_value('message') or ''),
                    'timestamp': str(target.get_value('timestamp') or ''),
                    'available': target.get_value(
                        'status', no_exception=True
                    ) != 'deleted',
                }
            else:
                data['__reply__'] = {
                    'messageId': reply_ref,
                    'sender': '',
                    'body': '',
                    'timestamp': '',
                    'available': False,
                }
        forward_ref = str(message_metadata.get('forwardedFrom') or '')
        if forward_ref:
            target_code = server.split_search_key(forward_ref)[1]
            target = reply_targets.get(str(target_code))
            if target:
                data['__forwarded_from__'] = {
                    'messageId': SearchKey.get_by_sobject(target, use_id=False),
                    'conversationId': str(target.get_value('message_code') or ''),
                    'sender': str(target.get_value('login') or ''),
                    'body': str(target.get_value('message') or ''),
                    'timestamp': str(target.get_value('timestamp') or ''),
                    'available': target.get_value(
                        'status', no_exception=True
                    ) != 'deleted',
                    'attachments': attachments_by_log.get(
                        str(target.get_code() or ''), []
                    ),
                }
            else:
                data['__forwarded_from__'] = {
                    'messageId': forward_ref,
                    'conversationId': '',
                    'sender': '',
                    'body': '',
                    'timestamp': '',
                    'available': False,
                    'attachments': [],
                }
        records.append(data)
    return json.dumps({
        'messages': records,
        'pinnedMessage': pin_value,
        'pinHistory': conversation_metadata.get('pinHistory') or [],
    }, separators=(',', ':'))


def mark_chat_read(message_code, timestamp):
    import json
    from datetime import datetime
    from pyasm.search import Search, SearchKey

    def aggregate_delivery(delivery):
        recipients = dict((delivery or {}).get('recipients') or {})
        receipts = list(recipients.values())
        if receipts and all(item.get('readAt') for item in receipts):
            return 'read'
        if receipts and all(item.get('deliveredAt') for item in receipts):
            return 'delivered'
        return 'sent'

    current_login = str(server.get_login() or '')
    search = Search('sthpw/subscription')
    search.add_filter('message_code', message_code)
    search.add_filter('login', current_login)
    search.add_filter('category', 'chat')
    subscription = search.get_sobject()
    if not subscription:
        raise RuntimeError('The current login is not a chat participant')
    current_value = subscription.get_value('last_cleared', no_exception=True)
    timestamp_second = str(timestamp or '')[:19]
    current_second = str(current_value or '')[:19]
    if timestamp_second and (
            not current_second or timestamp_second > current_second):
        server.update(
            SearchKey.get_by_sobject(subscription, use_id=False),
            {'last_cleared': timestamp_second},
            triggers=True,
        )
    receipt_updates = {}
    if timestamp_second:
        log_search = Search('sthpw/message_log')
        log_search.add_filter('message_code', message_code)
        log_search.add_filter('login', current_login, op='!=')
        log_search.add_filter('status', 'deleted', op='!=')
        log_search.add_filter('timestamp', timestamp_second, op='<=')
        read_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        for message_log in log_search.get_sobjects():
            raw_metadata = message_log.get_value('metadata') or {}
            if isinstance(raw_metadata, dict):
                metadata = dict(raw_metadata)
            else:
                try:
                    metadata = json.loads(raw_metadata)
                except (TypeError, ValueError):
                    metadata = {}
            delivery = dict(metadata.get('delivery') or {})
            recipients = dict(delivery.get('recipients') or {})
            receipt = dict(recipients.get(current_login) or {})
            if not receipt or receipt.get('readAt'):
                continue
            receipt['deliveredAt'] = str(
                receipt.get('deliveredAt') or read_at
            )
            receipt['readAt'] = read_at
            recipients[current_login] = receipt
            delivery['recipients'] = recipients
            metadata['delivery'] = delivery
            receipt_updates[SearchKey.get_by_sobject(
                message_log, use_id=False
            )] = {
                'metadata': metadata,
                'status': aggregate_delivery(delivery),
                'project_code': 'sthpw',
            }
    if receipt_updates:
        server.update_multiple(data=receipt_updates, triggers=True)
    return {
        'lastCleared': str(timestamp_second or current_value or ''),
        'receiptsUpdated': len(receipt_updates),
    }


def send_chat_message(message_code, message, attachment_keys=None, reply_to=None):
    import json
    from pyasm.search import Search, SearchKey

    def update_message_log(message_log, metadata=None):
        code = message_log.get_code()
        values = {}
        use_id = False
        if not code:
            record_id = message_log.get_id()
            if not record_id:
                raise RuntimeError('TACTIC message log has no code')
            code = 'MESSAGE_LOG{0:05d}'.format(int(record_id))
            values['code'] = code
            use_id = True
        values['project_code'] = 'sthpw'
        if metadata is not None:
            values['metadata'] = metadata
        if values:
            server.update(
                SearchKey.get_by_sobject(message_log, use_id=use_id),
                values,
                triggers=False,
            )
            if 'code' in values:
                message_log.set_value('code', values['code'])
        return code

    current_login = str(server.get_login() or '')
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('category', 'chat')
    members = member_search.get_sobjects()
    member_logins = set(
        str(item.get_value('login') or '') for item in members
        if item.get_value('login')
    )
    if current_login not in member_logins:
        raise RuntimeError('The current login is not a chat participant')

    reply_target = None
    if reply_to:
        reply_ref = str(reply_to)
        if reply_ref.startswith('sthpw/message_log'):
            reply_target = Search.get_by_search_key(reply_ref)
        else:
            reply_search = Search('sthpw/message_log')
            reply_search.add_filter('code', reply_ref)
            reply_target = reply_search.get_sobject()
        if (
            not reply_target
            or reply_target.get_value('message_code') != message_code
            or reply_target.get_value('status', no_exception=True) == 'deleted'
        ):
            raise RuntimeError('The replied message is not available in this chat')
        update_message_log(reply_target)

    valid_attachments = []
    for attachment_key in attachment_keys or []:
        search_type, code = server.split_search_key(attachment_key)
        if search_type != 'sthpw/snapshot':
            continue
        snapshot_search = Search('sthpw/snapshot')
        snapshot_search.add_filter('code', code)
        snapshot = snapshot_search.get_sobject()
        if not snapshot:
            continue
        if (
            snapshot.get_value('search_type') != 'sthpw/message'
            or snapshot.get_value('search_code') != message_code
        ):
            raise RuntimeError('Attachment does not belong to this chat')
        valid_attachments.append(attachment_key)

    if not str(message or '').strip() and not valid_attachments:
        raise ValueError('Message or attachment is required')
    server.log_message(
        message_code, message or '', status='sent',
        category='chat', log_history=True,
    )
    log_search = Search('sthpw/message_log')
    log_search.add_filter('message_code', message_code)
    log_search.add_filter('login', current_login)
    log_search.add_order_by('timestamp', direction='desc')
    log_search.set_limit(1)
    message_log = log_search.get_sobject()
    if not message_log:
        raise RuntimeError('TACTIC did not create a message log')
    sent_at = str(message_log.get_value('timestamp') or '')
    metadata_values = {
        'delivery': {
            'schemaVersion': 1,
            'sender': str(current_login or ''),
            'sentAt': sent_at,
            'recipients': dict(
                (login, {'deliveredAt': '', 'readAt': ''})
                for login in sorted(member_logins)
                if login != current_login
            ),
        },
    }
    if reply_target:
        metadata_values['replyTo'] = SearchKey.get_by_sobject(
            reply_target, use_id=False
        )
    update_message_log(message_log, metadata_values)
    message_log_key = SearchKey.get_by_sobject(message_log, use_id=False)
    for attachment_key in valid_attachments:
        server.connect_sobjects(
            attachment_key, message_log_key, context='chat_attachment'
        )
    data = message_log.get_data()
    data['__search_key__'] = message_log_key
    data['__delivery__'] = metadata_values['delivery']
    conversation_search = Search('sthpw/message')
    conversation_search.add_filter('code', message_code)
    conversation_search.add_filter('category', 'chat')
    conversation = conversation_search.get_sobject()
    if conversation:
        raw_metadata = conversation.get_value('metadata') or {}
        if isinstance(raw_metadata, dict):
            conversation_metadata = dict(raw_metadata)
        else:
            try:
                conversation_metadata = json.loads(raw_metadata)
            except (TypeError, ValueError):
                conversation_metadata = {}
        summary = dict(conversation_metadata.get('summary') or {})
        summary.update({
            'latestCode': str(message_log.get_code() or ''),
            'latestBody': str(message or ''),
            'latestTimestamp': str(message_log.get_value('timestamp') or ''),
            'latestSender': str(current_login or ''),
            'latestForwarded': False,
            'messageCount': int(summary.get('messageCount') or 0) + 1,
            'attachmentCount': (
                int(summary.get('attachmentCount') or 0)
                + len(valid_attachments)
            ),
        })
        conversation_metadata['summary'] = summary
        server.update(
            SearchKey.get_by_sobject(conversation, use_id=False),
            {
                'metadata': conversation_metadata,
                'project_code': 'sthpw',
            }, triggers=False,
        )
    return json.dumps({'message': data}, separators=(',', ':'))


def forward_chat_messages(message_log_keys, target_message_codes):
    import json
    from pyasm.search import Search, SearchKey

    def update_message_log(message_log, metadata=None):
        code = message_log.get_code()
        values = {}
        use_id = False
        if not code:
            record_id = message_log.get_id()
            if not record_id:
                raise RuntimeError('TACTIC message log has no code')
            code = 'MESSAGE_LOG{0:05d}'.format(int(record_id))
            values['code'] = code
            use_id = True
        values['project_code'] = 'sthpw'
        if metadata is not None:
            values['metadata'] = metadata
        if values:
            server.update(
                SearchKey.get_by_sobject(message_log, use_id=use_id),
                values,
                triggers=False,
            )
            if 'code' in values:
                message_log.set_value('code', values['code'])
        return code

    current_login = str(server.get_login() or '')
    source_refs = []
    source_messages = []
    seen_sources = set()
    for message_log_key in message_log_keys or []:
        message_log = Search.get_by_search_key(str(message_log_key or ''))
        if not message_log or server.split_search_key(
                SearchKey.get_by_sobject(message_log, use_id=False)
        )[0] != 'sthpw/message_log':
            raise RuntimeError('A forwarded message does not exist')
        if message_log.get_value('status', no_exception=True) == 'deleted':
            raise RuntimeError('A deleted message cannot be forwarded')
        update_message_log(message_log)
        source_ref = SearchKey.get_by_sobject(message_log, use_id=False)
        if source_ref in seen_sources:
            continue
        seen_sources.add(source_ref)
        source_refs.append(source_ref)
        source_messages.append(message_log)
    if not source_messages:
        raise ValueError('Select at least one message to forward')

    source_chats = set(
        message_log.get_value('message_code') for message_log in source_messages
    )
    access_search = Search('sthpw/subscription')
    access_search.add_filter('login', current_login)
    access_search.add_filter('category', 'chat')
    access_search.add_filters('message_code', list(source_chats))
    accessible_sources = set(
        item.get_value('message_code') for item in access_search.get_sobjects()
    )
    if accessible_sources != source_chats:
        raise RuntimeError('The current login cannot access a forwarded message')

    targets = []
    seen_targets = set()
    for message_code in target_message_codes or []:
        message_code = str(message_code or '').strip()
        if message_code and message_code not in seen_targets:
            seen_targets.add(message_code)
            targets.append(message_code)
    if not targets:
        raise ValueError('Select at least one destination chat')
    target_access = Search('sthpw/subscription')
    target_access.add_filter('category', 'chat')
    target_access.add_filters('message_code', targets)
    target_members = target_access.get_sobjects()
    members_by_target = {}
    for item in target_members:
        members_by_target.setdefault(
            str(item.get_value('message_code') or ''), set()
        ).add(str(item.get_value('login') or ''))
    accessible_targets = set(
        code for code, logins in members_by_target.items()
        if current_login in logins
    )
    if accessible_targets != set(targets):
        raise RuntimeError('The current login cannot access a destination chat')
    target_search = Search('sthpw/message')
    target_search.add_filter('category', 'chat')
    target_search.add_filter('status', 'deleted', op='!=')
    target_search.add_filters('code', targets)
    target_messages = dict(
        (item.get_code(), item) for item in target_search.get_sobjects()
    )
    active_targets = set(target_messages)
    if active_targets != set(targets):
        raise RuntimeError('A destination chat is not available')

    created = []
    for message_code in targets:
        latest_created = None
        for source_ref in source_refs:
            server.log_message(
                message_code, '', status='sent',
                category='chat', log_history=True,
            )
            log_search = Search('sthpw/message_log')
            log_search.add_filter('message_code', message_code)
            log_search.add_filter('login', current_login)
            log_search.add_order_by('timestamp', direction='desc')
            log_search.set_limit(len(source_refs) + 1)
            # Keep this as an explicit loop.  The legacy source minifier
            # corrupts a multiline next(generator, default) expression into
            # ``if ... not`` without its trailing colon.
            message_log = None
            for item in log_search.get_sobjects():
                item_key = SearchKey.get_by_sobject(item, use_id=False)
                if item_key not in created:
                    message_log = item
                    break
            if not message_log:
                raise RuntimeError('TACTIC did not create a forwarded message log')
            sent_at = str(message_log.get_value('timestamp') or '')
            update_message_log(message_log, {
                'forwardedFrom': source_ref,
                'delivery': {
                    'schemaVersion': 1,
                    'sender': str(current_login or ''),
                    'sentAt': sent_at,
                    'recipients': dict(
                        (login, {'deliveredAt': '', 'readAt': ''})
                        for login in sorted(
                            members_by_target.get(message_code, set())
                        ) if login and login != current_login
                    ),
                },
            })
            message_id = SearchKey.get_by_sobject(message_log, use_id=False)
            created.append(message_id)
            latest_created = message_log
        conversation = target_messages.get(message_code)
        if conversation and latest_created:
            raw_metadata = conversation.get_value('metadata') or {}
            if isinstance(raw_metadata, dict):
                conversation_metadata = dict(raw_metadata)
            else:
                try:
                    conversation_metadata = json.loads(raw_metadata)
                except (TypeError, ValueError):
                    conversation_metadata = {}
            summary = dict(conversation_metadata.get('summary') or {})
            summary.update({
                'latestCode': str(latest_created.get_code() or ''),
                'latestBody': '',
                'latestTimestamp': str(
                    latest_created.get_value('timestamp') or ''
                ),
                'latestSender': str(current_login or ''),
                'latestForwarded': True,
                'messageCount': (
                    int(summary.get('messageCount') or 0)
                    + len(source_refs)
                ),
                'attachmentCount': int(
                    summary.get('attachmentCount') or 0
                ),
            })
            conversation_metadata['summary'] = summary
            server.update(
                SearchKey.get_by_sobject(conversation, use_id=False),
                {
                    'metadata': conversation_metadata,
                    'project_code': 'sthpw',
                }, triggers=False,
            )
    return json.dumps({
        'forwarded': len(created),
        'destinations': len(targets),
        'messages': len(source_refs),
    }, separators=(',', ':'))


def authorize_chat_attachment(message_code, snapshot_code):
    import json
    from pyasm.search import Search

    current_login = server.get_login()
    member_search = Search('sthpw/subscription')
    member_search.add_filter('message_code', message_code)
    member_search.add_filter('login', current_login)
    member_search.add_filter('category', 'chat')
    if not member_search.get_sobject():
        return json.dumps({'allowed': False}, separators=(',', ':'))

    snapshot_search = Search('sthpw/snapshot')
    snapshot_search.add_filter('code', snapshot_code)
    snapshot = snapshot_search.get_sobject()
    if not snapshot:
        return json.dumps({'allowed': False}, separators=(',', ':'))
    connection_search = Search('sthpw/connection')
    connection_search.add_filter('context', 'chat_attachment')
    connection_search.add_filter('src_search_type', 'sthpw/snapshot')
    connection_search.add_filter('src_search_code', snapshot_code)
    connection_search.add_filter('dst_search_type', 'sthpw/message_log')
    connections = connection_search.get_sobjects()
    log_codes = [
        connection.get_value('dst_search_code')
        for connection in connections if connection.get_value('dst_search_code')
    ]
    allowed = False
    if log_codes:
        log_search = Search('sthpw/message_log')
        log_search.add_filters('code', log_codes)
        log_search.add_filter('message_code', message_code)
        allowed = bool(log_search.get_sobject())
    return json.dumps({'allowed': allowed}, separators=(',', ':'))


def query_server_updates(message_after='', activity_after='', project_code='',
                         limit=101, reaction_after='', include_activity=True,
                         include_reactions=True, include_presence=False,
                         presence_ttl=360, cache_after='',
                         include_cache_changes=False, include_messages=True,
                         heartbeat_presence=True):
    import hashlib
    import json
    from datetime import datetime, timezone
    from json import loads
    from pyasm.search import Search, SearchKey

    clock_started_utc = datetime.now(timezone.utc)
    chat_requested = bool(
        include_messages or include_reactions or include_presence
    )
    if chat_requested:
        from pyasm.search import SearchType

    def chat_search_type_available(search_type):
        try:
            columns = set(SearchType.get_columns(search_type) or [])
        except AttributeError as error:
            if 'undefined' not in str(error).lower():
                raise
            return False
        return 'metadata' in columns

    messages_initialized = (
        all(
            chat_search_type_available(search_type)
            for search_type in ('sthpw/message', 'sthpw/message_log')
        )
        if chat_requested else True
    )
    if not messages_initialized:
        # First-run servers do not have Handler's structured chat metadata.
        # Keep activity/cache polling alive, but do not read or write chat and
        # presence records until an administrator confirms schema bootstrap.
        include_messages = False
        include_reactions = False
        include_presence = False
        heartbeat_presence = False

    def database_local_now():
        """Read the wall clock used for TACTIC's naive DB timestamps."""
        try:
            from pyasm.search import SearchType

            sql = SearchType.get_sql_by_search_type('sthpw/message')
            rows = sql.do_query('SELECT CURRENT_TIMESTAMP')
            row = rows[0]
            if isinstance(row, dict):
                value = next(iter(row.values()))
            elif isinstance(row, (list, tuple)):
                value = row[0]
            else:
                value = row
            if isinstance(value, datetime):
                return value.replace(tzinfo=None)
            return datetime.fromisoformat(str(value).strip()).replace(
                tzinfo=None
            )
        except (AttributeError, IndexError, ImportError, TypeError, ValueError):
            # Old TACTIC SQL adapters do not all expose do_query().  The
            # process-local sample remains a safe compatibility fallback.
            return None

    def refresh_presence(ttl_seconds, publish_current):
        category = 'online_status'
        login = str(server.get_login() or '').strip()
        if not login:
            return []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        now_value = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        metadata = {
            'schemaVersion': 1,
            'login': login,
            'state': 'online',
            'lastSeen': now_value,
        }
        if publish_current:
            search = Search('sthpw/message')
            search.add_filter('category', category)
            search.add_filter('login', login)
            search.add_order_by('timestamp', direction='desc')
            search.set_limit(1)
            presence = search.get_sobject()
            if presence:
                server.update(
                    SearchKey.get_by_sobject(presence, use_id=False),
                    {
                        'message': now_value,
                        'status': 'online',
                        'metadata': metadata,
                    },
                    triggers=False,
                )
            else:
                digest = hashlib.sha1(login.encode('utf-8')).hexdigest()[:24]
                server.insert('sthpw/message', {
                    'code': 'ONLINE_STATUS_{0}'.format(digest.upper()),
                    'category': category,
                    'message': now_value,
                    'status': 'online',
                    'login': login,
                    'project_code': 'sthpw',
                    'metadata': metadata,
                })
        all_search = Search('sthpw/message')
        all_search.add_filter('category', category)
        all_search.add_order_by('timestamp', direction='desc')
        records = []
        seen_logins = set()
        ttl_seconds = max(30, int(ttl_seconds or 360))
        for item in all_search.get_sobjects():
            item_login = str(item.get_value('login') or '').strip()
            if not item_login or item_login in seen_logins:
                continue
            seen_logins.add(item_login)
            raw_metadata = item.get_value('metadata') or {}
            if isinstance(raw_metadata, dict):
                item_metadata = dict(raw_metadata)
            else:
                try:
                    item_metadata = json.loads(raw_metadata)
                except (TypeError, ValueError):
                    item_metadata = {}
            last_seen = str(
                item_metadata.get('lastSeen')
                or item.get_value('message') or ''
            )
            try:
                parsed = datetime.strptime(last_seen, '%Y-%m-%dT%H:%M:%SZ')
                age = max(0, int((now - parsed).total_seconds()))
            except (TypeError, ValueError):
                age = ttl_seconds + 1
            records.append({
                'login': item_login,
                'lastSeen': last_seen,
                'online': age <= ttl_seconds,
            })
        return records

    def event_timestamp(value):
        try:
            parsed = loads(value)
        except (TypeError, ValueError):
            parsed = value
        if isinstance(parsed, dict):
            parsed = parsed.get('view') or parsed.get('value') or ''
        return str(parsed or '')

    def metadata_value(item):
        raw_metadata = item.get_value('metadata') or {}
        if isinstance(raw_metadata, dict):
            return dict(raw_metadata)
        try:
            return json.loads(raw_metadata)
        except (TypeError, ValueError):
            return {}

    def aggregate_delivery(delivery):
        recipients = dict((delivery or {}).get('recipients') or {})
        receipts = list(recipients.values())
        if receipts and all(item.get('readAt') for item in receipts):
            return 'read'
        if receipts and all(item.get('deliveredAt') for item in receipts):
            return 'delivered'
        return 'sent'

    def delivery_record(delivery):
        value = dict(delivery or {})
        recipients = dict(value.get('recipients') or {})
        receipts = list(recipients.values())
        return {
            'status': aggregate_delivery(value),
            'sentAt': str(value.get('sentAt') or ''),
            'recipientCount': len(receipts),
            'deliveredCount': len([
                item for item in receipts if item.get('deliveredAt')
            ]),
            'readCount': len([
                item for item in receipts if item.get('readAt')
            ]),
        }

    def cache_change_records():
        """Return compact invalidation records for the persistent cache."""
        cursor = str(cache_after or '')
        cursor_timestamp = cursor.split('|', 1)[0]
        records = []
        retired = []
        newest = cursor
        scopes = list(dict.fromkeys(
            value for value in (project_code, 'sthpw') if value
        ))

        def search_type_project(search_type):
            value = str(search_type or '')
            base, separator, query = value.partition('?')
            if separator:
                for field in query.split('&'):
                    key, equals, field_value = field.partition('=')
                    if equals and key == 'project':
                        return field_value
            if base.startswith('sthpw/'):
                return 'sthpw'
            return ''

        def append_rows(search_type, target, kind, newest_value):
            for scope in scopes:
                search = Search(search_type)
                if kind == 'retire':
                    # retire_log has no project_code column. Project Search
                    # Types retain their project in ``?project=...`` while
                    # core records use the sthpw namespace. Filtering by the
                    # nonexistent column aborts the PostgreSQL transaction in
                    # TACTIC 4.9, so every later Search reports a misleading
                    # schema error for an unrelated table.
                    search.add_filter(
                        'search_type',
                        (
                            'sthpw/%' if scope == 'sthpw'
                            else '%project={0}%'.format(scope)
                        ),
                        op='like',
                    )
                else:
                    search.add_filter('project_code', scope)
                if cursor_timestamp:
                    search.add_filter(
                        'timestamp', cursor_timestamp, op='>='
                    )
                    search.add_order_by('timestamp')
                else:
                    search.add_order_by('timestamp', direction='desc')
                search.set_limit(limit)
                rows = search.get_sobjects()
                for item in rows:
                    data = item.get_data()
                    timestamp = event_timestamp(data.get('timestamp'))
                    raw_search_type = str(
                        data.get('search_type')
                        or data.get('search_type_code') or ''
                    )
                    changed_type = raw_search_type.split('?', 1)[0]
                    record_project = str(
                        data.get('project_code')
                        or search_type_project(raw_search_type)
                    )
                    if kind == 'retire' and record_project != scope:
                        continue
                    changed_code = str(
                        data.get('search_code')
                        or data.get('code') or data.get('id') or ''
                    )
                    token = '|'.join((
                        timestamp, changed_type, changed_code, kind,
                    ))
                    if cursor and token <= cursor:
                        continue
                    newest_value = max(newest_value, token)
                    target.append({
                        'searchType': changed_type,
                        'searchCode': changed_code,
                        'projectCode': record_project or scope,
                        'timestamp': timestamp,
                    })
            return newest_value

        newest = append_rows(
            'sthpw/change_timestamp', records, 'change', newest
        )
        newest = append_rows(
            'sthpw/retire_log', retired, 'retire', newest
        )
        if not cursor:
            records = []
            retired = []
        return records, retired, newest

    current_login = str(server.get_login() or '')
    limit = int(limit or 101)
    if include_cache_changes:
        cache_changes, cache_retired, cache_cursor = cache_change_records()
    else:
        cache_changes, cache_retired, cache_cursor = [], [], str(
            cache_after or ''
        )
    message_poll_attempted = bool(include_messages)
    message_codes = []
    if message_poll_attempted:
        own_search = Search('sthpw/subscription')
        own_search.add_filter('login', current_login)
        own_search.add_filter('category', 'chat')
        message_codes = list(set(
            subscription.get_value('message_code')
            for subscription in own_search.get_sobjects()
            if subscription.get_value('message_code')
        ))
    messages = []
    if message_codes:
        search = Search('sthpw/message_log')
        search.add_filters('message_code', message_codes)
        search.add_filter('status', 'deleted', op='!=')
        if message_after:
            search.add_filter('timestamp', message_after, op='>')
            search.add_order_by('timestamp')
        else:
            search.add_order_by('timestamp', direction='desc')
        search.set_limit(limit)
        message_logs = search.get_sobjects()
        message_logs = [item for item in message_logs if item.get_code()]
        delivery_by_code = {}
        delivery_updates = {}
        delivered_at = datetime.now(timezone.utc).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        for item in message_logs:
            metadata = metadata_value(item)
            delivery = dict(metadata.get('delivery') or {})
            recipients = dict(delivery.get('recipients') or {})
            receipt = dict(recipients.get(str(current_login or '')) or {})
            sender = str(
                delivery.get('sender') or item.get_value('login') or ''
            )
            if (
                    sender != current_login and receipt
                    and not receipt.get('deliveredAt')):
                receipt['deliveredAt'] = delivered_at
                recipients[current_login] = receipt
                delivery['recipients'] = recipients
                metadata['delivery'] = delivery
                delivery_updates[SearchKey.get_by_sobject(
                    item, use_id=False
                )] = {
                    'metadata': metadata,
                    'status': aggregate_delivery(delivery),
                    'project_code': 'sthpw',
                }
            delivery_by_code[str(item.get_code() or '')] = delivery_record(
                delivery
            )
        if delivery_updates:
            server.update_multiple(data=delivery_updates, triggers=True)
        attachment_counts = {}
        message_log_codes = [
            item.get_code() for item in message_logs if item.get_code()
        ]
        if message_log_codes:
            connection_search = Search('sthpw/connection')
            connection_search.add_filter('context', 'chat_attachment')
            connection_search.add_filter(
                'dst_search_type', 'sthpw/message_log'
            )
            connection_search.add_filters(
                'dst_search_code', message_log_codes
            )
            for connection in connection_search.get_sobjects():
                code = connection.get_value('dst_search_code')
                attachment_counts[code] = attachment_counts.get(code, 0) + 1
        for item in message_logs:
            data = item.get_data()
            data['__search_key__'] = SearchKey.get_by_sobject(
                item, use_id=False
            )
            data['__event_timestamp__'] = event_timestamp(
                data.get('timestamp')
            )
            data['__attachment_count__'] = attachment_counts.get(
                item.get_code(), 0
            )
            data['__delivery__'] = delivery_by_code.get(
                str(item.get_code() or ''), {}
            )
            if data['__delivery__']:
                data['status'] = data['__delivery__'].get('status') or 'sent'
            messages.append(data)

    reactions = []
    reaction_cursor = str(reaction_after or '')
    if message_codes and include_reactions:
        change_search = Search('sthpw/change_timestamp')
        change_search.add_filter('search_type', 'sthpw/message_log')
        if reaction_after:
            change_search.add_filter(
                'timestamp', str(reaction_after)[:19], op='>='
            )
            change_search.add_order_by('timestamp')
        else:
            change_search.add_order_by('timestamp', direction='desc')
        change_search.set_limit(limit)
        changes = change_search.get_sobjects()
        changed_codes = []
        event_by_code = {}
        for change in changes:
            code = str(change.get_value('search_code') or '')
            if not code:
                continue
            timestamp = event_timestamp(change.get_value('timestamp'))
            changed_codes.append(code)
            if timestamp > event_by_code.get(code, ''):
                event_by_code[code] = timestamp
            if timestamp > reaction_cursor:
                reaction_cursor = timestamp
        if changed_codes:
            changed_search = Search('sthpw/message_log')
            changed_search.add_filters('code', list(set(changed_codes)))
            for message_log in changed_search.get_sobjects():
                message_code = str(message_log.get_value('message_code') or '')
                if (
                    message_code not in message_codes
                    or message_log.get_value('status', no_exception=True) == 'deleted'
                ):
                    continue
                raw_metadata = message_log.get_value('metadata') or {}
                if isinstance(raw_metadata, dict):
                    metadata = dict(raw_metadata)
                else:
                    try:
                        metadata = loads(raw_metadata)
                    except (TypeError, ValueError):
                        metadata = {}
                reactions.append({
                    'messageId': SearchKey.get_by_sobject(
                        message_log, use_id=False
                    ),
                    'messageCode': message_code,
                    'reactions': dict(metadata.get('reactions') or {}),
                    'delivery': delivery_record(
                        metadata.get('delivery') or {}
                    ),
                    'status': aggregate_delivery(
                        metadata.get('delivery') or {}
                    ),
                    'reactionUpdatedAt': str(
                        metadata.get('reactionUpdatedAt') or ''
                    ),
                    '__event_timestamp__': event_by_code.get(
                        str(message_log.get_code() or ''), ''
                    ),
                })

    activity = []
    if project_code and include_activity:
        sources = (
            ('sthpw/status_log', 'status'),
            ('sthpw/snapshot', 'publication'),
            ('sthpw/note', 'note'),
            ('sthpw/task', 'task'),
            ('sthpw/change_timestamp', 'change'),
        )
        for search_type, kind in sources:
            search = Search(search_type)
            search.add_filter('project_code', project_code)
            timestamp_column = 'timestamp'
            if activity_after:
                search.add_filter(timestamp_column, activity_after, op='>')
                search.add_order_by(timestamp_column)
            else:
                search.add_order_by(timestamp_column, direction='desc')
            search.set_limit(limit)
            source_items = search.get_sobjects()
            for item in source_items:
                data = item.get_data()
                if (
                    kind == 'change'
                    and str(data.get('search_type') or '').split('?')[0]
                    == 'sthpw/task'
                ):
                    continue
                data['__search_key__'] = SearchKey.get_by_sobject(
                    item, use_id=False
                )
                data['__kind__'] = kind
                data['__event_timestamp__'] = event_timestamp(
                    data.get(timestamp_column)
                    or item.get_value(timestamp_column, no_exception=True)
                )
                activity.append(data)
        work_hour_changes = [
            item for item in activity
            if item.get('__kind__') == 'change'
            and str(item.get('search_type') or '').split('?', 1)[0]
            == 'sthpw/work_hour'
            and item.get('search_code')
        ]
        if work_hour_changes:
            work_hour_codes = list(set(
                str(item.get('search_code') or '')
                for item in work_hour_changes
            ))
            work_hour_search = Search('sthpw/work_hour')
            work_hour_search.add_filters('code', work_hour_codes)
            work_hours_by_code = {
                str(item.get_code() or ''): item
                for item in work_hour_search.get_sobjects()
            }
            task_codes = list(set(
                str(item.get_value('task_code') or '')
                for item in work_hours_by_code.values()
                if item.get_value('task_code')
            ))
            task_contexts = {}
            if task_codes:
                work_task_search = Search('sthpw/task')
                work_task_search.add_filters('code', task_codes)
                for task in work_task_search.get_sobjects():
                    task_data = task.get_data()
                    parent = task.get_parent()
                    task_contexts[str(task.get_code() or '')] = {
                        'process': str(task_data.get('process') or ''),
                        'context': str(
                            task_data.get('context')
                            or task_data.get('process') or ''
                        ),
                        'targetSearchKey': str(
                            SearchKey.get_by_sobject(parent, use_id=False)
                            if parent else ''
                        ),
                        'targetTitle': str((
                            parent.get_name()
                            or parent.get_value('name', no_exception=True)
                            or parent.get_value('title', no_exception=True)
                            or parent.get_code() or ''
                        ) if parent else ''),
                        'targetType': str(
                            task_data.get('search_type') or ''
                        ).split('?', 1)[0],
                    }
            retained_activity = []
            for info in activity:
                if info not in work_hour_changes:
                    retained_activity.append(info)
                    continue
                code = str(info.get('search_code') or '')
                work_hour = work_hours_by_code.get(code)
                if not work_hour:
                    continue
                event_time = str(info.get('__event_timestamp__') or '')
                changed_by = info.get('changed_by') or {}
                if not isinstance(changed_by, dict):
                    try:
                        changed_by = loads(changed_by)
                    except (TypeError, ValueError):
                        changed_by = {}
                actor = next((
                    str(value) for value in changed_by.values() if value
                ), '') if isinstance(changed_by, dict) else ''
                data = work_hour.get_data()
                task_code = str(data.get('task_code') or '')
                data.update(task_contexts.get(task_code, {}))
                data['__search_key__'] = str(
                    SearchKey.get_by_sobject(work_hour, use_id=False) or ''
                )
                data['__kind__'] = 'work_hour'
                data['__event_timestamp__'] = event_time
                data['__actor__'] = actor
                data['__work_hour_action__'] = 'change'
                retained_activity.append(data)
            activity = retained_activity
        publication_rows = [
            item for item in activity
            if item.get('__kind__') == 'publication' and item.get('code')
        ]
        if publication_rows:
            publication_by_code = dict(
                (str(item.get('code')), item) for item in publication_rows
            )
            file_search = Search('sthpw/file')
            file_search.add_filters(
                'snapshot_code', list(publication_by_code.keys())
            )
            file_search.add_filter('type', 'main')
            for file_item in file_search.get_sobjects():
                file_data = file_item.get_data()
                publication = publication_by_code.get(
                    str(file_data.get('snapshot_code') or '')
                )
                file_name = str(file_data.get('file_name') or '')
                if publication is not None and file_name:
                    publication.setdefault('__main_files__', []).append(
                        file_name
                    )
    activity.sort(key=lambda item: item.get('__event_timestamp__') or '')
    activity_page = activity[:limit] if activity_after else activity[-limit:]
    presence = refresh_presence(
        presence_ttl, bool(heartbeat_presence)
    ) if include_presence else []
    clock_ended_utc = datetime.now(timezone.utc)
    clock_ended_local = clock_ended_utc.astimezone().replace(tzinfo=None)
    clock_ended_database = database_local_now()
    return {
        'messages': messages,
        'reactions': reactions,
        'reactionCursor': reaction_cursor,
        'activity': activity_page,
        'presence': presence,
        'cacheChanges': cache_changes,
        'cacheRetired': cache_retired,
        'cacheCursor': cache_cursor,
        'messagePollAttempted': message_poll_attempted,
        'messagesInitialized': messages_initialized,
        'serverClock': {
            'utcStarted': clock_started_utc.strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ),
            'utcEnded': clock_ended_utc.strftime(
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ),
            'localEnded': clock_ended_local.strftime(
                '%Y-%m-%dT%H:%M:%S.%f'
            ),
            'databaseEnded': (
                clock_ended_database.strftime('%Y-%m-%dT%H:%M:%S.%f')
                if clock_ended_database else ''
            ),
        },
    }


def query_user_recent_activity(
        login='', project_code='', limit=25, offset=0, kinds=None,
        assigned_login='', include_day_counts=False, day='', logins=None,
        counts_only=False, counts_from_day='', instance_relations=None,
        object_scope=None, exclude_login=''):
    """Return one enriched, pageable activity shape for profiles and feeds."""
    import json
    import xml.etree.ElementTree as ElementTree
    from pyasm.search import Search, SearchKey

    login = str(login or '').strip()
    project_code = str(project_code or '').strip()
    limit = max(1, min(int(limit or 25), 100))
    offset = max(0, int(offset or 0))
    assigned_login = str(assigned_login or '').strip()
    exclude_login = str(exclude_login or '').strip().casefold()
    logins = list(dict.fromkeys(
        str(value or '').strip()
        for value in (logins or ())
        if str(value or '').strip()
    ))
    instance_relations = {
        clean_type: tuple(
            str(endpoint or '').split('?', 1)[0]
            for endpoint in endpoints or ()
            if str(endpoint or '').strip()
        )
        for raw_type, endpoints in dict(instance_relations or {}).items()
        for clean_type in (str(raw_type or '').split('?', 1)[0],)
        if clean_type
    }
    object_scope = dict(object_scope or {})
    scope_search_type = str(
        object_scope.get('searchType') or ''
    ).split('?', 1)[0]
    scope_search_code = str(object_scope.get('searchCode') or '')
    scope_search_id = str(object_scope.get('searchId') or '')
    scope_child_types = set(
        str(value or '').split('?', 1)[0]
        for value in object_scope.get('childTypes') or ()
        if str(value or '').strip()
    )
    scope_note_codes = set(
        str(value or '')
        for value in object_scope.get('noteCodes') or ()
        if str(value or '').strip()
    )
    scope_snapshot_codes = set(
        str(value or '')
        for value in object_scope.get('snapshotCodes') or ()
        if str(value or '').strip()
    )
    scope_work_hour_codes = set(
        str(value or '')
        for value in object_scope.get('workHourCodes') or ()
        if str(value or '').strip()
    )
    scope_indexed_objects = []
    for raw_reference in object_scope.get('indexedObjects') or ():
        reference = dict(raw_reference or {})
        reference_type = str(
            reference.get('searchType') or ''
        ).split('?', 1)[0]
        reference_code = str(reference.get('searchCode') or '')
        reference_id = str(reference.get('searchId') or '')
        if reference_type and (reference_code or reference_id):
            scope_indexed_objects.append({
                'searchType': reference_type,
                'searchCode': reference_code,
                'searchId': reference_id,
            })
    scope_task_ids = set(
        str(value or '')
        for value in object_scope.get('taskIds') or ()
        if str(value or '').strip()
    )
    scope_task_code_by_id = {}
    for reference in scope_indexed_objects:
        if reference.get('searchType') != 'sthpw/task':
            continue
        reference_id = str(reference.get('searchId') or '')
        reference_code = str(reference.get('searchCode') or '')
        if reference_id:
            scope_task_ids.add(reference_id)
            if reference_code:
                scope_task_code_by_id[reference_id] = reference_code
    scope_enabled = bool(scope_search_type and scope_search_code)
    scope_identity_values = {
        value for value in (scope_search_code, scope_search_id) if value
    }
    allowed_kinds = set(str(value or '') for value in (kinds or ()))
    counts_only = bool(counts_only)
    include_day_counts = bool(include_day_counts or counts_only)
    counts_from_day = str(counts_from_day or '').strip()
    day = str(day or '').strip()
    next_day = ''
    if day:
        import datetime
        next_day = (
            datetime.datetime.strptime(day, '%Y-%m-%d')
            + datetime.timedelta(days=1)
        ).strftime('%Y-%m-%d')

    records = []
    parent_refs = {}
    relation_refs = {}
    snapshot_codes = set()
    day_counts = {}
    message_codes = None
    sources = (
        ('sthpw/status_log', 'status', True),
        ('sthpw/snapshot', 'publication', True),
        ('sthpw/note', 'note', True),
        ('sthpw/task', 'task', True),
        ('sthpw/message_log', 'message', False),
    )

    technical_columns = {
        'id', 'code', 'search_type', 'search_id', 'search_code',
        'project_code', 'timestamp', 'login', 'transaction_code',
        'pipeline_code', '__search_key__',
    }

    def clean_search_type(value):
        return str(value or '').split('?', 1)[0]

    def actor_is_excluded(value):
        return bool(
            exclude_login
            and str(value or '').strip().casefold() == exclude_login
        )

    def source_actor(data, kind):
        if kind == 'task':
            return str(data.get('login') or data.get('changed_by') or '')
        return str(
            data.get('login') or data.get('assigned')
            or data.get('changed_by') or ''
        )

    def json_mapping(value):
        if isinstance(value, dict):
            return dict(value)
        if not value:
            return {}
        try:
            decoded = json.loads(str(value))
        except (TypeError, ValueError):
            return {}
        return dict(decoded) if isinstance(decoded, dict) else {}

    def transaction_xml(transaction, data):
        """Read transaction XML through TACTIC so zlib payloads are expanded."""
        getter = getattr(transaction, 'get_xml_value', None)
        if getter:
            try:
                xml_value = getter('transaction')
                serializer = getattr(xml_value, 'to_string', None)
                if serializer:
                    try:
                        value = serializer(pretty=False)
                    except TypeError:
                        value = serializer()
                    if isinstance(value, bytes):
                        return value.decode('utf-8', errors='replace')
                    return str(value or '')
            except (AttributeError, TypeError, ValueError):
                pass
        return str(data.get('transaction') or '')

    def parse_transaction(value):
        """Return the user-facing object mutations from a TACTIC transaction."""
        text = str(value or '').strip()
        if not text or '<' not in text:
            return []
        try:
            root = ElementTree.fromstring(text)
        except (ElementTree.ParseError, TypeError, ValueError):
            return []
        mutations = []
        for node in root.iter('sobject'):
            action = str(node.get('action') or '').strip().lower()
            if action not in ('insert', 'create', 'update', 'delete', 'remove'):
                continue
            changes = []
            field_values = {}
            for column in node.findall('column'):
                name = str(column.get('name') or '').strip()
                if not name:
                    continue
                before = str(column.get('from') or '').strip()
                after = str(column.get('to') or '').strip()
                if before == after:
                    continue
                field_values[name] = {
                    'before': before,
                    'after': after,
                }
                if name.lower() in technical_columns:
                    continue
                changes.append({
                    'field': name.replace('_', ' '),
                    'before': before,
                    'after': after,
                })
            display_title = ''
            for preferred_field in ('name', 'title'):
                title_change = next((
                    change for change in changes
                    if str(change.get('field') or '').lower()
                    == preferred_field
                ), None)
                if not title_change:
                    continue
                if action in ('delete', 'remove'):
                    display_title = str(title_change.get('before') or '')
                else:
                    display_title = str(
                        title_change.get('after')
                        or title_change.get('before') or ''
                    )
                break
            mutations.append({
                'action': action,
                'searchType': clean_search_type(node.get('search_type')),
                'searchCode': str(
                    node.get('search_code') or node.get('search_id') or ''
                ),
                'changes': changes[:4],
                'fieldValues': field_values,
                'displayTitle': display_title,
            })
        return mutations

    def mutation_value(mutation, field):
        change = dict(
            (mutation.get('fieldValues') or {}).get(field) or {}
        )
        if mutation_kind(mutation) == 'delete':
            return str(change.get('before') or change.get('after') or '')
        return str(change.get('after') or change.get('before') or '')

    def mutation_title(mutation):
        return str(mutation.get('displayTitle') or '')

    def audit_detail(mutation, transaction_data):
        changes = mutation.get('changes') or []
        if changes:
            parts = []
            for change in changes:
                field = change.get('field') or ''
                before = change.get('before') or ''
                after = change.get('after') or ''
                if before and after:
                    parts.append('{0}: {1} -> {2}'.format(
                        field, before, after
                    ))
                elif after:
                    parts.append('{0}: {1}'.format(field, after))
                elif before:
                    parts.append('{0}: {1} -> empty'.format(field, before))
            return '; '.join(parts)[:480]
        return str(
            transaction_data.get('description')
            or transaction_data.get('title') or ''
        )[:480]
    if not allowed_kinds or 'message' in allowed_kinds:
        subscription_search = Search('sthpw/subscription')
        subscription_search.add_filter('login', str(server.get_login() or ''))
        subscription_search.add_filter('category', 'chat')
        message_codes = list(set(
            item.get_value('message_code')
            for item in subscription_search.get_sobjects()
            if item.get_value('message_code')
        ))

    def apply_source_filters(search, kind, filter_project, filter_day=True):
        if kind == 'task' and assigned_login:
            search.add_filter('assigned', assigned_login)
        elif logins:
            search.add_filters(
                'assigned' if kind == 'task' else 'login', logins
            )
        elif login:
            search.add_filter('login', login)
        if exclude_login:
            search.add_filter('login', exclude_login, op='!=')
        if kind == 'message':
            search.add_filter('category', 'chat')
            search.add_filter('status', 'deleted', op='!=')
            if message_codes:
                search.add_filters('message_code', message_codes)
            else:
                search.add_filter('message_code', '__no_accessible_chat__')
        if project_code and filter_project:
            search.add_filter('project_code', project_code)
        if scope_enabled:
            if kind in ('task', 'publication'):
                search.add_filter('search_type', scope_search_type)
                if scope_search_id:
                    search.add_filter('search_id', scope_search_id)
                else:
                    search.add_filter('search_code', scope_search_code)
            elif kind in ('status', 'note'):
                if scope_search_id or scope_task_ids:
                    parent_ids = list(scope_task_ids)
                    if scope_search_id:
                        parent_ids.append(scope_search_id)
                    search.add_filters(
                        'search_id', list(dict.fromkeys(parent_ids))
                    )
                else:
                    parent_codes = list(scope_task_codes)
                    parent_codes.append(scope_search_code)
                    search.add_filters(
                        'search_code', list(dict.fromkeys(parent_codes))
                    )
        if filter_day and day:
            search.add_filter('timestamp', day + ' 00:00:00', op='>=')
            search.add_filter('timestamp', next_day + ' 00:00:00', op='<')
        elif not filter_day and counts_from_day:
            search.add_filter(
                'timestamp', counts_from_day + ' 00:00:00', op='>='
            )

    scope_task_codes = {
        str(value or '')
        for value in object_scope.get('taskCodes') or ()
        if str(value or '').strip()
    }
    if scope_enabled and not scope_task_codes:
        scope_task_search = Search('sthpw/task')
        scope_task_search.add_filter('search_type', scope_search_type)
        scope_task_search.add_filter('search_code', scope_search_code)
        if project_code:
            scope_task_search.add_filter('project_code', project_code)
        for scope_task in scope_task_search.get_sobjects():
            scope_task_data = scope_task.get_data()
            if (
                    clean_search_type(scope_task_data.get('search_type'))
                    != scope_search_type
                    or str(scope_task_data.get('search_code') or '')
                    != scope_search_code):
                continue
            scope_task_code = str(scope_task.get_code() or '')
            if scope_task_code:
                scope_task_codes.add(scope_task_code)
                scope_task_id = str(
                    scope_task_data.get('id') or scope_task.get_id() or ''
                )
                if scope_task_id:
                    scope_task_ids.add(scope_task_id)
                    scope_task_code_by_id[scope_task_id] = (
                        scope_task_code
                    )

    if scope_enabled and not scope_indexed_objects:
        scope_indexed_objects.append({
            'searchType': scope_search_type,
            'searchCode': scope_search_code,
            'searchId': scope_search_id,
        })

    for search_type, kind, filter_project in sources:
        if allowed_kinds and kind not in allowed_kinds:
            continue
        if include_day_counts:
            calendar_search = Search(search_type)
            apply_source_filters(
                calendar_search, kind, filter_project, filter_day=False
            )
            calendar_search.add_column('timestamp')
            for calendar_item in calendar_search.get_sobjects():
                if actor_is_excluded(source_actor(
                        calendar_item.get_data(), kind)):
                    continue
                day_key = str(
                    calendar_item.get_value('timestamp') or ''
                )[:10]
                if len(day_key) == 10:
                    day_counts[day_key] = day_counts.get(day_key, 0) + 1
        if counts_only:
            continue
        search = Search(search_type)
        apply_source_filters(search, kind, filter_project)
        search.add_order_by('timestamp', direction='desc')
        search.set_limit(offset + limit)
        for item in search.get_sobjects():
            data = item.get_data()
            item_code = str(data.get('code') or data.get('id') or '')
            if kind == 'publication' and item_code:
                snapshot_codes.add(item_code)
            process = str(data.get('process') or '')
            context = str(data.get('context') or process)
            version = data.get('version')
            parent_type = str(data.get('search_type') or '').split('?', 1)[0]
            parent_code = str(data.get('search_code') or '')
            parent_id = str(data.get('search_id') or '')
            if scope_enabled and not parent_code:
                if (
                        clean_search_type(parent_type) == scope_search_type
                        and parent_id == scope_search_id):
                    parent_code = scope_search_code
                elif clean_search_type(parent_type) == 'sthpw/task':
                    parent_code = str(
                        scope_task_code_by_id.get(parent_id) or ''
                    )
            if kind == 'message':
                parent_type = 'sthpw/message'
                parent_code = str(data.get('message_code') or '')
            if parent_type and parent_code:
                parent_refs.setdefault(parent_type, set()).add(parent_code)

            if kind == 'status':
                before = str(data.get('from_status') or '')
                after = str(
                    data.get('to_status') or data.get('status') or ''
                )
                title = 'Status changed'
                detail = ' -> '.join(
                    value for value in (before, after) if value
                )
            elif kind == 'publication':
                title = 'Published snapshot'
                detail = str(data.get('description') or '')[:480]
            elif kind == 'note':
                title = 'Added note'
                detail = str(data.get('note') or '')[:240]
            elif kind == 'message':
                title = 'Sent message'
                detail = str(data.get('message') or '')[:240]
            else:
                title = 'Updated task'
                detail = str(
                    data.get('description') or data.get('status') or ''
                )[:240]
            if kind == 'publication':
                item_title = ''
            elif kind == 'task':
                item_title = context or process
            else:
                item_title = str(
                    data.get('name') or data.get('title') or item_code
                )
            actor = source_actor(data, kind)
            records.append({
                'eventId': '{0}:{1}'.format(
                    kind, data.get('code') or data.get('id') or ''
                ),
                'searchKey': str(SearchKey.get_by_sobject(
                    item, use_id=(kind == 'status')
                ) or ''),
                'kind': kind,
                'title': title,
                'detail': detail,
                'actor': actor,
                'timestamp': str(data.get('timestamp') or ''),
                'itemCode': item_code,
                'itemTitle': item_title,
                'project': str(data.get('project_code') or project_code),
                'process': process,
                'context': context,
                'version': str(version if version not in (None, '') else ''),
                'statusBefore': before if kind == 'status' else '',
                'statusAfter': (
                    after if kind == 'status'
                    else str(data.get('status') or '') if kind == 'task'
                    else ''
                ),
                'taskCode': item_code if kind == 'task' else (
                    parent_code if kind == 'status'
                    and parent_type == 'sthpw/task' else ''
                ),
                'serverGenerated': bool(
                    kind == 'status' and not actor.strip()
                ),
                '_parentType': parent_type,
                '_parentCode': parent_code,
                '_taskId': str(data.get('id') or '') if kind == 'task' else '',
            })

    task_activity_records = [
        record for record in records
        if record.get('kind') == 'task' and record.get('taskCode')
    ]
    unresolved_task_codes = {
        str(record.get('taskCode') or ''): record
        for record in task_activity_records
    }
    if unresolved_task_codes:
        task_change_search = Search('sthpw/change_timestamp')
        task_change_search.add_filter('search_type', 'sthpw/task')
        task_change_search.add_filters(
            'search_code', list(unresolved_task_codes)
        )
        if project_code:
            task_change_search.add_filter('project_code', project_code)
        transaction_code_by_task = {}
        for task_change in task_change_search.get_sobjects():
            task_change_data = task_change.get_data()
            task_code = str(task_change_data.get('search_code') or '')
            transaction_code = str(
                task_change_data.get('transaction_code') or ''
            )
            if task_code in unresolved_task_codes and transaction_code:
                transaction_code_by_task[task_code] = transaction_code

        transaction_codes = set(transaction_code_by_task.values())
        transactions_by_code = {}
        if transaction_codes:
            task_transaction_search = Search('sthpw/transaction_log')
            task_transaction_search.add_filters(
                'code', list(transaction_codes)
            )
            for task_transaction in task_transaction_search.get_sobjects():
                task_transaction_data = task_transaction.get_data()
                transaction_code = str(
                    task_transaction_data.get('code') or ''
                )
                if transaction_code in transaction_codes:
                    transactions_by_code[transaction_code] = (
                        task_transaction_data
                    )

        resolved_task_codes = set()
        for task_code, transaction_code in transaction_code_by_task.items():
            transaction_data = transactions_by_code.get(transaction_code)
            if transaction_data is None:
                continue
            record = unresolved_task_codes[task_code]
            actor = str(transaction_data.get('login') or '')
            record['actor'] = actor
            record['serverGenerated'] = not bool(actor.strip())
            resolved_task_codes.add(task_code)

        unresolved_task_ids = {
            str(record.get('_taskId') or ''): record
            for task_code, record in unresolved_task_codes.items()
            if task_code not in resolved_task_codes
            and record.get('_taskId')
        }
        if unresolved_task_ids:
            task_log_search = Search('sthpw/sobject_log')
            task_log_search.add_filter('search_type', 'sthpw/task')
            task_log_search.add_filters(
                'search_id', list(unresolved_task_ids)
            )
            task_log_search.add_order_by('timestamp', direction='desc')
            for task_log in task_log_search.get_sobjects():
                task_log_data = task_log.get_data()
                if clean_search_type(
                        task_log_data.get('search_type')) != 'sthpw/task':
                    continue
                task_id = str(task_log_data.get('search_id') or '')
                record = unresolved_task_ids.pop(task_id, None)
                if record is None:
                    continue
                actor = str(task_log_data.get('login') or '')
                record['actor'] = actor
                record['serverGenerated'] = not bool(actor.strip())

    task_parent_records = [
        record for record in records
        if record.get('_parentType') == 'sthpw/task'
        and record.get('_parentCode')
    ]
    if task_parent_records:
        task_codes = list(set(
            record.get('_parentCode') for record in task_parent_records
        ))
        task_search = Search('sthpw/task')
        task_search.add_filters('code', task_codes)
        tasks_by_code = {
            str(item.get_code() or ''): item.get_data()
            for item in task_search.get_sobjects()
        }
        for record in task_parent_records:
            task_code = str(record.get('_parentCode') or '')
            task_data = tasks_by_code.get(task_code, {})
            root_type = clean_search_type(task_data.get('search_type'))
            root_code = str(task_data.get('search_code') or '')
            root_id = str(task_data.get('search_id') or '')
            if (
                    scope_enabled and not root_code
                    and root_type == scope_search_type
                    and root_id == scope_search_id):
                root_code = scope_search_code
            if not root_type or not root_code:
                continue
            record['_parentType'] = root_type
            record['_parentCode'] = root_code
            record['taskCode'] = task_code
            record['process'] = str(
                task_data.get('process') or record.get('process') or ''
            )
            record['context'] = str(
                task_data.get('context') or record.get('context')
                or record.get('process') or ''
            )
            record['itemTitle'] = str(
                record.get('context') or record.get('process') or ''
            )
            if record.get('kind') == 'status':
                record['serverGenerated'] = bool(
                    not str(record.get('actor') or '').strip()
                )
            parent_refs.setdefault(root_type, set()).add(root_code)

    audit_kinds = {'create', 'change', 'delete', 'work_hour'}
    audit_enabled = not allowed_kinds or bool(allowed_kinds & audit_kinds)
    if counts_only and not audit_enabled:
        return {
            'records': [],
            'countsFromDay': counts_from_day,
            'dayCounts': [
                {'dateKey': day_key, 'count': day_counts[day_key]}
                for day_key in sorted(day_counts, reverse=True)
            ],
        }
    audited_targets = set()
    if audit_enabled:
        def apply_transaction_filters(search, filter_day):
            if project_code:
                search.add_filter('namespace', project_code)
            if logins:
                search.add_filters('login', logins)
            elif login:
                search.add_filter('login', login)
            if exclude_login:
                search.add_filter('login', exclude_login, op='!=')
            if filter_day and day:
                search.add_filter(
                    'timestamp', day + ' 00:00:00', op='>='
                )
                search.add_filter(
                    'timestamp', next_day + ' 00:00:00', op='<'
                )
            elif not filter_day and counts_from_day:
                search.add_filter(
                    'timestamp', counts_from_day + ' 00:00:00', op='>='
                )

        def mutation_kind(mutation):
            action = mutation.get('action') or 'update'
            if action in ('insert', 'create'):
                return 'create'
            if action in ('delete', 'remove'):
                return 'delete'
            return 'change'

        instance_type_cache = {}

        def instance_relation_refs(mutation):
            """Resolve both semantic endpoints of an instance mutation."""
            instance_type = str(mutation.get('searchType') or '')
            if not instance_type:
                return None
            field_values = dict(mutation.get('fieldValues') or {})
            candidate_columns = [
                str(column) for column in field_values
                if str(column).endswith('_code')
            ]
            if len(field_values) < 2:
                return None
            endpoint_types = instance_type_cache.get(instance_type)
            if endpoint_types is None:
                endpoint_types = instance_relations.get(instance_type, ())
                instance_type_cache[instance_type] = endpoint_types
            if len(endpoint_types or ()) != 2:
                return None

            try:
                from pyasm.biz import Schema
                schema = Schema.get()
            except (AttributeError, ImportError, TypeError):
                schema = None

            used_columns = set()
            endpoint_refs = []
            for endpoint_type in endpoint_types:
                try:
                    foreign_keys = tuple(
                        schema.get_foreign_keys(
                            instance_type, endpoint_type
                        ) or ()
                    ) if schema is not None else ()
                except (AttributeError, KeyError, TypeError, ValueError):
                    foreign_keys = ()

                instance_column = next((
                    column for column in foreign_keys
                    if column in field_values and column not in used_columns
                ), '')
                if not instance_column:
                    conventional = '{0}_code'.format(
                        str(endpoint_type).split('/')[-1]
                    )
                    if (
                            conventional in field_values
                            and conventional not in used_columns):
                        instance_column = conventional
                if not instance_column:
                    instance_column = next((
                        column for column in candidate_columns
                        if column not in used_columns
                    ), '')
                if not instance_column:
                    return None

                endpoint_column = next((
                    column for column in foreign_keys
                    if column != instance_column
                    and column not in field_values
                ), 'code')
                change = dict(field_values.get(instance_column) or {})
                endpoint_value = str(
                    change.get('before')
                    if mutation_kind(mutation) == 'delete'
                    else change.get('after') or change.get('before') or ''
                )
                if not endpoint_value:
                    return None
                used_columns.add(instance_column)
                endpoint_refs.append((
                    str(endpoint_type), str(endpoint_column), endpoint_value
                ))
            return tuple(endpoint_refs)

        def scope_endpoint_matches(endpoint_ref):
            if not scope_enabled or not endpoint_ref:
                return False
            endpoint_type, _endpoint_column, endpoint_value = endpoint_ref
            return (
                clean_search_type(endpoint_type) == scope_search_type
                and str(endpoint_value or '') in scope_identity_values
            )

        def scoped_mutation_role(mutation, instance_refs=None):
            """Classify how one audit mutation belongs to the object scope."""
            if not scope_enabled:
                return 'object'
            parent_type = clean_search_type(mutation.get('searchType'))
            parent_code = str(mutation.get('searchCode') or '')
            if (
                    parent_type == scope_search_type
                    and parent_code == scope_search_code):
                return 'root'
            if instance_refs and any(
                    scope_endpoint_matches(endpoint)
                    for endpoint in instance_refs):
                return 'relation'

            field_values = dict(mutation.get('fieldValues') or {})
            relationship_values = {
                str(value or '')
                for field, change in field_values.items()
                if (
                    str(field or '').lower()
                    not in technical_columns
                    and str(field or '').lower().endswith(('_code', '_id'))
                )
                for value in (
                    dict(change or {}).get('before'),
                    dict(change or {}).get('after'),
                )
                if str(value or '')
            }
            parent_reference = bool(
                relationship_values.intersection(scope_identity_values)
            )
            generic_parent_reference = (
                mutation_value(mutation, 'search_code')
                in scope_identity_values
                or mutation_value(mutation, 'search_id')
                in scope_identity_values
            )
            if parent_type == 'sthpw/task':
                if (
                        parent_code in scope_task_codes
                        or mutation_value(mutation, 'search_code')
                        == scope_search_code):
                    return 'system'
                return ''
            if parent_type in ('sthpw/note', 'sthpw/snapshot'):
                parent_code_value = mutation_value(
                    mutation, 'search_code'
                )
                if (
                        parent_code in (
                            scope_note_codes
                            if parent_type == 'sthpw/note'
                            else scope_snapshot_codes
                        )
                        or
                        parent_code_value == scope_search_code
                        or parent_code_value in scope_task_codes):
                    return 'system'
                return ''
            if parent_type == 'sthpw/work_hour':
                if (
                        parent_code in scope_work_hour_codes
                        or mutation_value(
                            mutation, 'task_code'
                        ) in scope_task_codes):
                    return 'work_hour'
                return ''
            if (
                    parent_type in scope_child_types
                    and (parent_reference or generic_parent_reference)):
                return 'child'
            return ''

        if include_day_counts:
            calendar_audit_search = Search('sthpw/transaction_log')
            apply_transaction_filters(calendar_audit_search, False)
            for calendar_transaction in calendar_audit_search.get_sobjects():
                calendar_data = calendar_transaction.get_data()
                if actor_is_excluded(calendar_data.get('login')):
                    continue
                day_key = str(calendar_data.get('timestamp') or '')[:10]
                if len(day_key) != 10:
                    continue
                for mutation in parse_transaction(transaction_xml(
                        calendar_transaction, calendar_data)):
                    parent_type = mutation.get('searchType') or ''
                    instance_refs = (
                        instance_relation_refs(mutation)
                        if mutation_kind(mutation) in ('create', 'delete')
                        else None
                    )
                    if (
                            scope_enabled
                            and not scoped_mutation_role(
                                mutation, instance_refs
                            )):
                        continue
                    kind = (
                        'work_hour'
                        if parent_type == 'sthpw/work_hour'
                        else mutation_kind(mutation)
                    )
                    if (
                            not parent_type
                            or parent_type.startswith('sthpw/')
                            and parent_type != 'sthpw/work_hour'
                            and not (
                                scope_enabled
                                and scoped_mutation_role(
                                    mutation, instance_refs
                                ) == 'system'
                            )
                            or allowed_kinds and kind not in allowed_kinds):
                        continue
                    day_counts[day_key] = day_counts.get(day_key, 0) + 1

        if counts_only:
            return {
                'records': [],
                'countsFromDay': counts_from_day,
                'dayCounts': [
                    {'dateKey': day_key, 'count': day_counts[day_key]}
                    for day_key in sorted(day_counts, reverse=True)
                ],
            }

        transaction_limit = max((offset + limit) * 4, 100)
        scoped_object_logs = []
        transactions = []
        if scope_enabled:
            # transaction_log is project-wide.  Limiting that table before
            # checking the XML displaced older events of a selected object in
            # any active project.  sobject_log is the native per-object index;
            # query it first for all live records in this report, then fetch
            # the exact transactions it references.
            indexed_ids_by_type = {}
            for reference in scope_indexed_objects:
                reference_type = clean_search_type(
                    reference.get('searchType')
                )
                reference_id = str(reference.get('searchId') or '')
                if reference_type and reference_id:
                    indexed_ids_by_type.setdefault(
                        reference_type, set()
                    ).add(reference_id)

            indexed_transaction_ids = set()
            for reference_type, reference_ids in indexed_ids_by_type.items():
                indexed_log_search = Search('sthpw/sobject_log')
                indexed_log_search.add_filter(
                    'search_type', reference_type
                )
                indexed_log_search.add_filters(
                    'search_id', list(reference_ids)
                )
                indexed_log_search.add_order_by(
                    'timestamp', direction='desc'
                )
                indexed_log_search.set_limit(transaction_limit)
                for indexed_log in indexed_log_search.get_sobjects():
                    indexed_data = indexed_log.get_data()
                    transaction_id = str(
                        indexed_data.get('transaction_log_id') or ''
                    )
                    if not transaction_id:
                        continue
                    indexed_transaction_ids.add(transaction_id)
                    scoped_object_logs.append(indexed_data)

            if len(indexed_transaction_ids) > transaction_limit:
                ordered_index_ids = []
                seen_index_ids = set()
                for indexed_data in sorted(
                        scoped_object_logs,
                        key=lambda item: str(
                            item.get('timestamp') or ''
                        ),
                        reverse=True):
                    transaction_id = str(
                        indexed_data.get('transaction_log_id') or ''
                    )
                    if (
                            not transaction_id
                            or transaction_id in seen_index_ids):
                        continue
                    seen_index_ids.add(transaction_id)
                    ordered_index_ids.append(transaction_id)
                    if len(ordered_index_ids) >= transaction_limit:
                        break
                indexed_transaction_ids = set(ordered_index_ids)
                scoped_object_logs = [
                    indexed_data for indexed_data in scoped_object_logs
                    if str(
                        indexed_data.get('transaction_log_id') or ''
                    ) in indexed_transaction_ids
                ]

            if indexed_transaction_ids:
                indexed_transaction_search = Search(
                    'sthpw/transaction_log'
                )
                apply_transaction_filters(
                    indexed_transaction_search, True
                )
                indexed_transaction_search.add_filters(
                    'id', list(indexed_transaction_ids)
                )
                indexed_transaction_search.add_order_by(
                    'timestamp', direction='desc'
                )
                indexed_transaction_search.set_limit(transaction_limit)
                transactions.extend(
                    indexed_transaction_search.get_sobjects()
                )

            # Delete and unlink operations intentionally have no sobject_log
            # row.  Their uncompressed XML still contains the selected root
            # identity, so query that identity before applying the page limit.
            # Compressed updates are covered by the native index above.
            identity_transaction_search = Search(
                'sthpw/transaction_log'
            )
            apply_transaction_filters(
                identity_transaction_search, True
            )
            identity_transaction_search.add_filter(
                'transaction', '%{0}%'.format(scope_search_code),
                op='like',
            )
            identity_transaction_search.add_order_by(
                'timestamp', direction='desc'
            )
            identity_transaction_search.set_limit(transaction_limit)
            transactions.extend(
                identity_transaction_search.get_sobjects()
            )
        else:
            transaction_search = Search('sthpw/transaction_log')
            apply_transaction_filters(transaction_search, True)
            transaction_search.add_order_by(
                'timestamp', direction='desc'
            )
            transaction_search.set_limit(transaction_limit)
            transactions = transaction_search.get_sobjects()

        transaction_by_id = {}
        for transaction in transactions:
            transaction_data = transaction.get_data()
            transaction_data['_expandedTransaction'] = transaction_xml(
                transaction, transaction_data
            )
            transaction_id = str(
                transaction.get_id() or transaction_data.get('id') or ''
            )
            if transaction_id:
                transaction_by_id[transaction_id] = transaction_data
        if scope_enabled and len(transaction_by_id) > transaction_limit:
            ordered_transactions = sorted(
                transaction_by_id.items(),
                key=lambda item: str(
                    item[1].get('timestamp') or ''
                ),
                reverse=True,
            )[:transaction_limit]
            transaction_by_id = dict(ordered_transactions)
        if transaction_by_id:
            object_logs_by_transaction = {}
            if scope_enabled:
                object_log_values = scoped_object_logs
            else:
                object_log_search = Search('sthpw/sobject_log')
                object_log_search.add_filters(
                    'transaction_log_id', list(transaction_by_id.keys())
                )
                object_log_values = [
                    object_log.get_data()
                    for object_log in object_log_search.get_sobjects()
                ]
            for object_data in object_log_values:
                transaction_id = str(
                    object_data.get('transaction_log_id') or ''
                )
                object_logs_by_transaction.setdefault(
                    transaction_id, []
                ).append(object_data)

            for transaction_id, transaction_data in transaction_by_id.items():
                mutations = parse_transaction(
                    transaction_data.get('_expandedTransaction')
                )
                if not mutations:
                    continue
                indexed = object_logs_by_transaction.get(transaction_id, [])
                indexed_types = set(
                    clean_search_type(row.get('search_type'))
                    for row in indexed
                )
                for mutation_index, mutation in enumerate(mutations):
                    parent_type = mutation.get('searchType') or ''
                    parent_code = mutation.get('searchCode') or ''
                    mutation_action = mutation_kind(mutation)
                    instance_refs = (
                        instance_relation_refs(mutation)
                        if mutation_action in ('create', 'delete') else None
                    )
                    scope_role = scoped_mutation_role(
                        mutation, instance_refs
                    )
                    if scope_enabled and not scope_role:
                        continue
                    kind = (
                        'work_hour'
                        if parent_type == 'sthpw/work_hour'
                        else mutation_action
                    )
                    if allowed_kinds and kind not in allowed_kinds:
                        continue
                    if parent_type == 'sthpw/work_hour':
                        values = {}
                        for field, change in dict(
                                mutation.get('fieldValues') or {}).items():
                            value = (
                                change.get('before')
                                if mutation_action == 'delete'
                                else change.get('after')
                                or change.get('before')
                            )
                            if field:
                                values[field] = value
                        records.append({
                            'eventId': 'work_hour:{0}:{1}'.format(
                                transaction_data.get('code') or transaction_id,
                                mutation_index,
                            ),
                            'searchKey': '',
                            'kind': 'work_hour',
                            'title': 'Work hours',
                            'detail': str(values.get('description') or '')[:480],
                            'changes': [],
                            'actor': str(transaction_data.get('login') or ''),
                            'timestamp': str(
                                transaction_data.get('timestamp') or ''
                            ),
                            'itemCode': parent_code,
                            'itemTitle': '',
                            'project': project_code,
                            'process': str(values.get('process') or ''),
                            'context': str(values.get('process') or ''),
                            'version': '',
                            'statusBefore': '',
                            'statusAfter': '',
                            'workHourAction': mutation_action,
                            '_workHourValues': values,
                            '_workHourCode': parent_code,
                            '_parentType': '',
                            '_parentCode': '',
                            '_fallbackTitle': '',
                        })
                        continue
                    # Outside an object scope, dedicated sources provide
                    # richer task, note, snapshot, message and status events.
                    # A scoped history also needs system-record deletions and
                    # the individual non-status changes of its tasks.
                    scoped_system_type = (
                        parent_type
                        if scope_enabled and scope_role == 'system'
                        else ''
                    )
                    if (
                            parent_type.startswith('sthpw/')
                            and not scoped_system_type):
                        continue
                    if (
                            scoped_system_type in ('sthpw/note', 'sthpw/snapshot')
                            and kind == 'create'):
                        continue
                    if (
                            not scope_enabled and kind != 'delete'
                            and indexed_types
                            and parent_type not in indexed_types):
                        continue
                    if not parent_type or not parent_code:
                        continue
                    audited_targets.add((
                        str(transaction_data.get('code') or ''),
                        parent_type,
                        parent_code,
                    ))
                    visible_changes = list(mutation.get('changes') or [])
                    if scoped_system_type == 'sthpw/task':
                        visible_changes = [
                            change for change in visible_changes
                            if str(change.get('field') or '').lower()
                            != 'status'
                        ]
                        if kind == 'change' and not visible_changes:
                            continue
                    item_type = (
                        parent_type
                        if scope_enabled
                        and scope_role in ('child', 'system')
                        else ''
                    )
                    item_title = str(
                        mutation_title(mutation)
                        or mutation_value(mutation, 'process')
                        or mutation_value(mutation, 'context')
                        or mutation_value(mutation, 'description')
                        or mutation_value(mutation, 'note')
                        or parent_code
                    )
                    if instance_refs:
                        for (
                                endpoint_type, endpoint_column, endpoint_value
                        ) in instance_refs:
                            relation_refs.setdefault(
                                (endpoint_type, endpoint_column), set()
                            ).add(endpoint_value)
                    else:
                        resolved_parent_type = (
                            scope_search_type if item_type else parent_type
                        )
                        resolved_parent_code = (
                            scope_search_code if item_type else parent_code
                        )
                        parent_refs.setdefault(
                            resolved_parent_type, set()
                        ).add(resolved_parent_code)
                        if item_type:
                            parent_refs.setdefault(
                                item_type, set()
                            ).add(parent_code)
                    records.append({
                        'eventId': 'audit:{0}:{1}'.format(
                            transaction_data.get('code') or transaction_id,
                            mutation_index,
                        ),
                        'searchKey': '',
                        'kind': kind,
                        'title': (
                            'Created object' if kind == 'create'
                            else 'Deleted object' if kind == 'delete'
                            else 'Updated object'
                        ),
                        'detail': (
                            '' if instance_refs else
                            audit_detail(mutation, transaction_data)
                        ),
                        'changes': [] if instance_refs else visible_changes,
                        'actor': str(transaction_data.get('login') or ''),
                        'timestamp': str(
                            transaction_data.get('timestamp') or ''
                        ),
                        'itemCode': '' if instance_refs else parent_code,
                        'itemTitle': '' if instance_refs else item_title,
                        'itemType': item_type,
                        'project': project_code,
                        'process': (
                            mutation_value(mutation, 'process')
                            if scoped_system_type == 'sthpw/task' else ''
                        ),
                        'context': (
                            mutation_value(mutation, 'context')
                            or mutation_value(mutation, 'process')
                            if scoped_system_type == 'sthpw/task' else ''
                        ),
                        'version': '',
                        'statusBefore': '',
                        'statusAfter': '',
                        'taskCode': (
                            parent_code
                            if scoped_system_type == 'sthpw/task' else ''
                        ),
                        'statusAfter': (
                            mutation_value(mutation, 'status')
                            if scoped_system_type == 'sthpw/task' else ''
                        ),
                        '_parentType': (
                            '' if instance_refs else
                            scope_search_type if item_type else parent_type
                        ),
                        '_parentCode': (
                            '' if instance_refs else
                            scope_search_code if item_type else parent_code
                        ),
                        '_fallbackTitle': (
                            '' if instance_refs else mutation_title(mutation)
                        ),
                        '_relationFrom': (
                            instance_refs[0] if instance_refs else None
                        ),
                        '_relationTo': (
                            instance_refs[1] if instance_refs else None
                        ),
                        '_scopeItemType': item_type,
                        '_scopeItemCode': parent_code if item_type else '',
                        '_scopeItemTitle': item_title if item_type else '',
                        'relationAction': (
                            'unlink' if instance_refs and kind == 'delete'
                            else 'link' if instance_refs else ''
                        ),
                    })

        # change_timestamp is only a latest-change index.  Use it to fill gaps
        # where the transaction index did not yield a readable mutation.
        change_search = Search('sthpw/change_timestamp')
        if project_code:
            change_search.add_filter('project_code', project_code)
        if scope_enabled:
            change_search.add_filter('search_type', scope_search_type)
            change_search.add_filter('search_code', scope_search_code)
        if day:
            change_search.add_filter(
                'timestamp', day + ' 00:00:00', op='>='
            )
            change_search.add_filter(
                'timestamp', next_day + ' 00:00:00', op='<'
            )
        change_search.add_order_by('timestamp', direction='desc')
        change_search.set_limit(max((offset + limit) * 3, 75))
        requested_actors = set(logins or ([login] if login else []))
        for changed_item in change_search.get_sobjects():
            changed_data = changed_item.get_data()
            parent_type = clean_search_type(changed_data.get('search_type'))
            parent_code = str(changed_data.get('search_code') or '')
            transaction_code = str(
                changed_data.get('transaction_code') or ''
            )
            changed_on = json_mapping(changed_data.get('changed_on'))
            changed_by = json_mapping(changed_data.get('changed_by'))
            visible_fields = [
                field for field in changed_on
                if str(field or '').lower() not in technical_columns
            ]
            latest_field = max(
                visible_fields,
                key=lambda field: str(changed_on.get(field) or ''),
                default='',
            )
            actor = str(changed_by.get(latest_field) or '')
            if not actor:
                actor = next((
                    str(value) for value in changed_by.values() if value
                ), '')
            if actor_is_excluded(actor):
                continue
            if requested_actors and actor not in requested_actors:
                continue
            if (
                    not parent_type or not parent_code
                    or parent_type.startswith('sthpw/')
                    or scope_enabled and (
                        parent_type != scope_search_type
                        or parent_code != scope_search_code
                    )
                    or (transaction_code, parent_type, parent_code)
                    in audited_targets):
                continue
            parent_refs.setdefault(parent_type, set()).add(parent_code)
            records.append({
                'eventId': 'change:{0}'.format(
                    changed_data.get('code') or changed_data.get('id') or
                    '{0}:{1}'.format(parent_type, parent_code)
                ),
                'searchKey': '',
                'kind': 'change',
                'title': 'Updated object',
                'detail': '',
                'changes': [{
                    'field': str(field).replace('_', ' '),
                    'before': '',
                    'after': '',
                    'valuesKnown': False,
                } for field in visible_fields[:4]],
                'actor': actor,
                'timestamp': str(
                    changed_data.get('timestamp')
                    or changed_on.get(latest_field) or ''
                ),
                'itemCode': parent_code,
                'itemTitle': parent_code,
                'project': str(
                    changed_data.get('project_code') or project_code
                ),
                'process': '',
                'context': '',
                'version': '',
                'statusBefore': '',
                'statusAfter': '',
                '_parentType': parent_type,
                '_parentCode': parent_code,
                '_fallbackTitle': '',
            })

    if exclude_login:
        records = [
            record for record in records
            if not actor_is_excluded(record.get('actor'))
        ]

    work_hour_records = [
        record for record in records
        if record.get('kind') == 'work_hour'
    ]
    if work_hour_records:
        work_hour_codes = list(set(
            str(record.get('_workHourCode') or '')
            for record in work_hour_records
            if record.get('_workHourCode')
        ))
        current_work_hours = {}
        if work_hour_codes:
            work_hour_search = Search('sthpw/work_hour')
            work_hour_search.add_filters('code', work_hour_codes)
            for work_hour in work_hour_search.get_sobjects():
                work_hour_data = work_hour.get_data()
                work_hour_data['__search_key__'] = str(
                    SearchKey.get_by_sobject(work_hour, use_id=False) or ''
                )
                current_work_hours[str(work_hour.get_code() or '')] = (
                    work_hour_data
                )

        task_codes = set()
        for record in work_hour_records:
            values = dict(record.pop('_workHourValues', {}) or {})
            current = current_work_hours.get(
                str(record.pop('_workHourCode', '') or ''), {}
            )
            # Transaction values describe the state at that event; the
            # current row only fills fields absent from an older mutation.
            values = dict(current, **values)
            category = str(values.get('category') or 'regular').lower()
            try:
                straight_time = float(values.get('straight_time') or 0)
            except (TypeError, ValueError):
                straight_time = 0.0
            try:
                over_time = float(values.get('over_time') or 0)
            except (TypeError, ValueError):
                over_time = 0.0
            hours = (
                over_time
                if category == 'overtime'
                else straight_time + over_time
            )
            task_code = str(values.get('task_code') or '')
            if task_code:
                task_codes.add(task_code)
            record.update({
                'searchKey': str(values.get('__search_key__') or ''),
                'detail': str(values.get('description') or record.get('detail') or '')[:480],
                'itemTitle': '{0:g} h'.format(hours),
                'process': str(values.get('process') or record.get('process') or ''),
                'context': str(values.get('process') or record.get('context') or ''),
                'taskCode': task_code,
                'hours': hours,
                'workDay': str(values.get('day') or ''),
                'workHourCategory': category,
                'workHourStatus': str(values.get('status') or ''),
                'workHourOwner': str(values.get('login') or ''),
            })

        tasks_by_code = {}
        if task_codes:
            work_task_search = Search('sthpw/task')
            work_task_search.add_filters('code', list(task_codes))
            tasks_by_code = {
                str(item.get_code() or ''): item.get_data()
                for item in work_task_search.get_sobjects()
            }
        for record in work_hour_records:
            task_data = tasks_by_code.get(
                str(record.get('taskCode') or ''), {}
            )
            parent_type = clean_search_type(task_data.get('search_type'))
            parent_code = str(task_data.get('search_code') or '')
            parent_id = str(task_data.get('search_id') or '')
            if (
                    scope_enabled and not parent_code
                    and parent_type == scope_search_type
                    and parent_id == scope_search_id):
                parent_code = scope_search_code
            record['process'] = str(
                task_data.get('process') or record.get('process') or ''
            )
            record['context'] = str(
                task_data.get('context') or record.get('context')
                or record.get('process') or ''
            )
            record['_parentType'] = parent_type
            record['_parentCode'] = parent_code
            if parent_type and parent_code:
                parent_refs.setdefault(parent_type, set()).add(parent_code)

    main_files = {}
    if snapshot_codes:
        file_search = Search('sthpw/file')
        file_search.add_filters('snapshot_code', list(snapshot_codes))
        file_search.add_filter('type', 'main')
        for file_item in file_search.get_sobjects():
            file_data = file_item.get_data()
            snapshot_code = str(file_data.get('snapshot_code') or '')
            file_name = str(file_data.get('file_name') or '')
            if snapshot_code and file_name:
                main_files.setdefault(snapshot_code, []).append(file_name)

    parents = {}
    for parent_type, codes in parent_refs.items():
        parent_query_type = parent_type
        if (
            project_code and not parent_type.startswith('sthpw/')
            and '?project=' not in parent_type
        ):
            parent_query_type = '{0}?project={1}'.format(
                parent_type, project_code
            )
        parent_search = Search(parent_query_type)
        parent_search.add_filters('code', list(codes))
        for parent in parent_search.get_sobjects():
            parent_data = parent.get_data()
            parent_code = str(parent.get_code() or '')
            try:
                parent_title = str(parent.get_name() or '')
            except (AttributeError, TypeError):
                parent_title = ''
            parent_title = str(
                parent_title
                or parent_data.get('name')
                or parent_data.get('title')
                or parent_data.get('code')
                or parent_code
            )
            if parent_type == 'sthpw/message':
                raw_metadata = parent_data.get('metadata') or {}
                if isinstance(raw_metadata, dict):
                    parent_metadata = dict(raw_metadata)
                else:
                    try:
                        parent_metadata = json.loads(str(raw_metadata))
                    except (TypeError, ValueError):
                        parent_metadata = {}
                parent_title = str(
                    parent_metadata.get('title') or 'Conversation'
                )
            parents[(parent_type, parent_code)] = {
                'searchKey': str(SearchKey.get_by_sobject(
                    parent, use_id=False
                ) or ''),
                'title': parent_title,
                'type': parent_type,
                'pipelineCode': str(
                    parent_data.get('pipeline_code') or ''
                ),
            }

    relation_endpoints = {}
    for (endpoint_type, endpoint_column), values in relation_refs.items():
        endpoint_query_type = endpoint_type
        if (
            project_code and not endpoint_type.startswith('sthpw/')
            and '?project=' not in endpoint_type
        ):
            endpoint_query_type = '{0}?project={1}'.format(
                endpoint_type, project_code
            )
        endpoint_search = Search(endpoint_query_type)
        endpoint_search.add_filters(endpoint_column, list(values))
        for endpoint in endpoint_search.get_sobjects():
            endpoint_data = endpoint.get_data()
            endpoint_value = str(endpoint_data.get(endpoint_column) or '')
            if not endpoint_value and endpoint_column == 'code':
                endpoint_value = str(endpoint.get_code() or '')
            if not endpoint_value:
                continue
            try:
                endpoint_title = str(endpoint.get_name() or '')
            except (AttributeError, TypeError):
                endpoint_title = ''
            endpoint_title = str(
                endpoint_title
                or endpoint_data.get('name')
                or endpoint_data.get('title')
                or endpoint_data.get('code')
                or ''
            )
            relation_endpoints[(
                endpoint_type, endpoint_column, endpoint_value
            )] = {
                'searchKey': str(SearchKey.get_by_sobject(
                    endpoint, use_id=False
                ) or ''),
                'title': endpoint_title,
                'type': endpoint_type,
                'pipelineCode': str(
                    endpoint_data.get('pipeline_code') or ''
                ),
            }

    scoped_audit_task_codes = {
        str(record.get('taskCode') or '')
        for record in records
        if record.get('_scopeItemType') == 'sthpw/task'
        and record.get('taskCode')
    }
    if scoped_audit_task_codes:
        records = [
            record for record in records
            if not (
                record.get('kind') == 'task'
                and str(record.get('taskCode') or '')
                in scoped_audit_task_codes
            )
        ]

    resolved_records = []
    for record in records:
        relation_from_ref = record.pop('_relationFrom', None)
        relation_to_ref = record.pop('_relationTo', None)
        parent_type = record.pop('_parentType', '')
        parent_code = record.pop('_parentCode', '')
        item_type = record.pop('_scopeItemType', '')
        item_code = record.pop('_scopeItemCode', '')
        item_fallback_title = record.pop('_scopeItemTitle', '')
        record.pop('_taskId', None)
        fallback_title = record.pop('_fallbackTitle', '')
        if relation_from_ref and relation_to_ref:
            relation_from = relation_endpoints.get(
                tuple(relation_from_ref), {}
            )
            relation_to = relation_endpoints.get(
                tuple(relation_to_ref), {}
            )
            if scope_enabled and scope_endpoint_matches(relation_from_ref):
                relation_from, relation_to = relation_to, relation_from
                relation_from_ref, relation_to_ref = (
                    relation_to_ref, relation_from_ref
                )
            if scope_enabled and not scope_endpoint_matches(relation_to_ref):
                continue
            record.update({
                'searchKey': str(relation_from.get('searchKey') or ''),
                'itemTitle': str(relation_from.get('title') or ''),
                'itemType': str(
                    relation_from.get('type') or relation_from_ref[0]
                ),
                'targetSearchKey': str(
                    relation_to.get('searchKey') or ''
                ),
                'targetTitle': str(relation_to.get('title') or ''),
                'targetType': str(
                    relation_to.get('type') or relation_to_ref[0]
                ),
                'pipelineCode': str(
                    relation_to.get('pipelineCode') or ''
                ),
            })
            resolved_records.append(record)
            continue
        if scope_enabled and (
                clean_search_type(parent_type) != scope_search_type
                or str(parent_code or '') != scope_search_code):
            continue
        parent = parents.get((parent_type, parent_code), {})
        record['targetSearchKey'] = str(parent.get('searchKey') or '')
        record['targetTitle'] = str(
            parent.get('title') or fallback_title or parent_code
            or 'TACTIC object'
        )
        record['targetType'] = str(parent.get('type') or parent_type)
        record['pipelineCode'] = str(parent.get('pipelineCode') or '')
        if record.get('kind') == 'publication':
            record['itemTitle'] = ', '.join(sorted(
                main_files.get(str(record.get('itemCode') or ''), [])
            ))
        if item_type and item_code:
            item = parents.get((item_type, item_code), {})
            record['searchKey'] = str(item.get('searchKey') or '')
            record['itemTitle'] = str(
                (item_fallback_title or item.get('title') or item_code)
                if item_type.startswith('sthpw/') else
                (item.get('title') or item_fallback_title or item_code)
            )
            record['itemType'] = str(item.get('type') or item_type)
        resolved_records.append(record)

    records = resolved_records
    records.sort(key=lambda record: record.get('timestamp') or '', reverse=True)
    page = records[offset:offset + limit]
    if include_day_counts:
        return {
            'records': page,
            'dayCounts': [
                {'dateKey': day_key, 'count': day_counts[day_key]}
                for day_key in sorted(day_counts, reverse=True)
            ],
        }
    return page


def query_user_profile_data(login, project_code='', activity_limit=25):
    """Return profile aggregates; the shared journal owns recent activity."""
    import json
    from datetime import datetime, timedelta
    from pyasm.search import Search

    login = str(login or '').strip()
    project_code = str(project_code or '').strip()
    # Retain the deployed procedure signature while activity is now queried
    # through query_user_recent_activity by both profile and feed clients.
    del activity_limit
    if not login:
        return json.dumps({}, separators=(',', ':'))

    current_login = str(server.get_login() or '').strip()
    is_admin = current_login.lower() == 'admin'
    current_groups = []
    if not is_admin:
        membership_search = Search('sthpw/login_in_group')
        membership_search.add_filter('login', current_login)
        current_groups = [
            str(item.get_value('login_group') or '').lower()
            for item in membership_search.get_sobjects()
        ]
    can_manage_work_hours = is_admin or any(
        group == 'admin' or 'supervisor' in group
        for group in current_groups
    )
    can_view_work_hours = (
        current_login.casefold() == login.casefold()
        or can_manage_work_hours
    )

    task_search = Search('sthpw/task')
    task_search.add_filter('assigned', login)
    if project_code:
        task_search.add_filter('project_code', project_code)
    task_search.add_order_by('bid_end_date')
    task_search.add_order_by('timestamp', direction='desc')
    task_objects = task_search.get_sobjects()
    status_counts = {}
    process_counts = {}
    today = datetime.utcnow().date()
    week_end = today + timedelta(days=6 - today.weekday())
    incomplete = 0
    overdue = 0
    due_this_week = 0
    for task in task_objects:
        data = task.get_data()
        progress = int(data.get('completion') or 0)
        if progress < 100:
            incomplete += 1
        deadline_text = str(data.get('bid_end_date') or '')[:10]
        deadline = None
        try:
            deadline = datetime.strptime(deadline_text, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            pass
        if deadline and progress < 100:
            if deadline < today:
                overdue += 1
            if today <= deadline <= week_end:
                due_this_week += 1
        status = str(data.get('status') or 'Unspecified')
        status_entry = status_counts.setdefault(status, {
            'label': status, 'count': 0,
            'pipeline_code': str(data.get('pipeline_code') or ''),
            'search_type': str(data.get('search_type') or ''),
            'process': str(data.get('process') or ''),
            'status': status,
        })
        status_entry['count'] += 1
        process = str(data.get('process') or 'Unspecified')
        process_entry = process_counts.setdefault(process, {
            'label': process, 'count': 0,
            'pipeline_code': str(data.get('pipeline_code') or ''),
            'search_type': str(data.get('search_type') or ''),
            'process': process,
            'status': status,
        })
        process_entry['count'] += 1
    logged_hours = 0.0
    approved_hours = 0.0
    pending_hours = 0.0
    week_start = today - timedelta(days=today.weekday())
    if can_view_work_hours:
        hour_search = Search('sthpw/work_hour')
        hour_search.add_filter('login', login)
        if project_code:
            hour_search.add_filter('project_code', project_code)
        hour_search.add_filter('day', week_start.isoformat(), op='>=')
        hour_search.add_filter('day', week_end.isoformat(), op='<=')
        for entry in hour_search.get_sobjects():
            try:
                regular = float(entry.get_value('straight_time') or 0.0)
            except (TypeError, ValueError):
                regular = 0.0
            try:
                overtime = float(entry.get_value('over_time') or 0.0)
            except (TypeError, ValueError):
                overtime = 0.0
            value = regular + overtime
            logged_hours += value
            if str(entry.get_value('status') or '').lower() == 'approved':
                approved_hours += value
            else:
                pending_hours += value

    return json.dumps({
        'taskSummary': {
            'total': len(task_objects),
            'incomplete': incomplete,
            'overdue': overdue,
            'dueThisWeek': due_this_week,
        },
        'workHourSummary': {
            'loggedHours': round(logged_hours, 2),
            'approvedHours': round(approved_hours, 2),
            'pendingHours': round(pending_hours, 2),
            'periodStart': week_start.isoformat(),
            'periodEnd': week_end.isoformat(),
        },
        'permissions': {
            'viewWorkHours': bool(can_view_work_hours),
            'manageWorkHours': bool(can_manage_work_hours),
        },
        'statusSummary': list(status_counts.values()),
        'processSummary': list(process_counts.values()),
    }, separators=(',', ':'))


def heartbeat_user_presence(ttl_seconds=90):
    """Refresh the current login presence and return known user states.

    Presence is stored as one ``sthpw/message`` state container per TACTIC
    login.  It deliberately does not use ``message_log`` because heartbeats
    are current state, not user-visible message history.
    """
    import hashlib
    import json
    from datetime import datetime
    from pyasm.search import Search, SearchKey

    category = 'online_status'
    login = str(server.get_login() or '').strip()
    if not login:
        return []

    now = datetime.utcnow()
    now_value = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    presence_search = Search('sthpw/message')
    presence_search.add_filter('category', category)
    presence_search.add_filter('login', login)
    presence_search.add_order_by('timestamp', direction='desc')
    presence_search.set_limit(1)
    presence = presence_search.get_sobject()
    metadata = {
        'schemaVersion': 1,
        'login': login,
        'state': 'online',
        'lastSeen': now_value,
    }
    if presence:
        server.update(
            SearchKey.get_by_sobject(presence, use_id=False),
            {
                'message': now_value,
                'status': 'online',
                'metadata': metadata,
            },
            triggers=False,
        )
    else:
        digest = hashlib.sha1(login.encode('utf-8')).hexdigest()[:24]
        code = 'ONLINE_STATUS_{0}'.format(digest.upper())
        server.insert('sthpw/message', {
            'code': code,
            'category': category,
            'message': now_value,
            'status': 'online',
            'login': login,
            'project_code': 'sthpw',
            'metadata': metadata,
        })

    all_search = Search('sthpw/message')
    all_search.add_filter('category', category)
    all_search.add_order_by('timestamp', direction='desc')
    records = []
    seen_logins = set()
    ttl_seconds = max(30, int(ttl_seconds or 90))
    for item in all_search.get_sobjects():
        item_login = str(item.get_value('login') or '').strip()
        if not item_login or item_login in seen_logins:
            continue
        seen_logins.add(item_login)
        raw_metadata = item.get_value('metadata') or {}
        if isinstance(raw_metadata, dict):
            item_metadata = dict(raw_metadata)
        else:
            try:
                item_metadata = json.loads(str(raw_metadata))
            except (TypeError, ValueError):
                item_metadata = {}
        last_seen = str(
            item_metadata.get('lastSeen')
            or item.get_value('message') or ''
        )
        try:
            seen_at = datetime.strptime(last_seen, '%Y-%m-%dT%H:%M:%SZ')
            age_seconds = max(0, int((now - seen_at).total_seconds()))
            online = age_seconds <= ttl_seconds
        except (TypeError, ValueError):
            online = False
        records.append({
            'login': item_login,
            'presenceKnown': True,
            'online': bool(online),
            'lastSeen': last_seen,
        })
    return records


def get_notes_and_stypes_counts(process, search_key, stypes_list):
    # Count every requested process with two table queries rather than issuing
    # one COUNT query per process and table. Relationship counts still require
    # one query per child Search Type because they target different tables.
    from pyasm.search import Search, SearchKey

    search_type, search_code = server.split_search_key(search_key)
    search = Search(search_type)
    sobject = search.get_by_search_key(search_key)
    # Project-owned Search Types do not necessarily expose project_code as a
    # physical column. The project is transport context in the search key.
    project_code = ''
    if 'project=' in search_key:
        project_code = search_key.split('project=', 1)[1].split('&', 1)[0]

    processes = []
    for value in process or []:
        value = str(value or '')
        if value and value not in processes:
            processes.append(value)

    cnt = {
        'notes': dict((value, 0) for value in processes),
        'stypes': {},
        'tasks': dict((value, 0) for value in processes),
        'taskDetails': dict((value, []) for value in processes),
    }

    if processes:
        task_search = Search('sthpw/task')
        task_search.add_op_filters([
            ('process', processes),
            ('search_type', search_type),
            ('search_code', search_code),
        ])
        if project_code:
            task_search.add_filter('project_code', project_code)
        task_sobjects = task_search.get_sobjects()
        task_codes = []
        task_process_by_code = {}
        for item in task_sobjects:
            item_process = str(item.get_value('process') or '')
            item_code = str(item.get_value('code') or '')
            if item_process not in cnt['tasks']:
                continue
            cnt['tasks'][item_process] += 1
            task_data = item.get_data()
            task_data['__search_key__'] = SearchKey.get_by_sobject(
                item, use_id=False
            )
            cnt['taskDetails'][item_process].append(task_data)
            if item_code:
                task_codes.append(item_code)
                task_process_by_code[item_code] = item_process

        note_search = Search('sthpw/note')
        note_search.add_op_filters([
            ('process', processes),
            ('search_type', search_type),
            ('search_code', search_code),
        ])
        if project_code:
            note_search.add_filter('project_code', project_code)
        root_note_counts = dict((value, 0) for value in processes)
        for item in note_search.get_sobjects():
            item_process = str(item.get_value('process') or '')
            if item_process in root_note_counts:
                root_note_counts[item_process] += 1
                cnt['notes'][item_process] += 1

        task_note_counts = {}
        task_note_codes = [
            detail.get('code')
            for details in cnt['taskDetails'].values()
            if len(details) > 1
            for detail in details if detail.get('code')
        ]
        if task_note_codes:
            task_note_search = Search('sthpw/note')
            task_note_search.add_filters('search_code', task_note_codes)
            if project_code:
                task_note_search.add_filter('project_code', project_code)
            for item in task_note_search.get_sobjects():
                parent_type = str(
                    item.get_value('search_type') or ''
                ).split('?', 1)[0]
                if parent_type not in ('', 'sthpw/task'):
                    continue
                task_code = str(item.get_value('search_code') or '')
                item_process = str(
                    item.get_value('process')
                    or task_process_by_code.get(task_code) or ''
                )
                if item_process not in cnt['notes']:
                    continue
                task_note_counts[task_code] = (
                    task_note_counts.get(task_code, 0) + 1
                )
                cnt['notes'][item_process] += 1

        for item_process, details in cnt['taskDetails'].items():
            details.sort(key=lambda item: (
                0 if not item.get('context')
                or item.get('context') == item_process else 1,
                item.get('timestamp') or '', item.get('code') or '',
            ))
            primary_code = details[0].get('code') if details else None
            for detail in details:
                task_code = detail.get('code')
                detail['__primary_note_branch__'] = (
                    task_code == primary_code
                )
                detail['__notes_count__'] = (
                    root_note_counts.get(item_process, 0)
                    if task_code == primary_code
                    else task_note_counts.get(task_code, 0)
                )

    for stype in stypes_list:
        descriptor = stype if isinstance(stype, dict) else {}
        count_key = str(
            descriptor.get('key') or descriptor.get('searchType') or stype
        )
        search_type = str(descriptor.get('searchType') or stype)
        expression = str(descriptor.get('expression') or '')
        try:
            if expression:
                related = Search.eval(expression) or []
                count = len(set(
                    SearchKey.get_by_sobject(item, use_id=False)
                    for item in related
                ))
            else:
                search = Search(search_type)
                search.add_relationship_filter(sobject)
                count = search.get_count(True)
            if count == -1:
                count = 0
            cnt['stypes'][count_key] = count
        except (AttributeError, KeyError, TypeError, ValueError):
            cnt['stypes'][count_key] = 0

    return cnt


def query_search_types_extended(project_code):
    """
    This crazy stuff made to execute queries on server
    All needed info is getting almost half-time faster
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
                                    'sthpw/change_timestamp', 'config/custom_property', 'sthpw/ticket',
                                    'sthpw/transaction_log', 'sthpw/wdg_settings', 'sthpw/subscription',
                                    'sthpw/status_log', 'sthpw/sobject_log', 'sthpw/sobject_list', 'sthpw/connection',
                                    'sthpw/work_hour',])
        search.add_order_by('search_type')
        stypes = search.get_sobjects()
    else:
        prj = Project.get_by_code(project_code)
        stypes = prj.get_search_types(include_multi_project=True)

    # add_config_tables = False
    #
    # if add_config_tables:
    #     search = Search('sthpw/search_object')
    #     search.add_filters('code', ['config/naming'])
    #     search.add_order_by('search_type')
    #     stypes.extend(search.get_sobjects())

    all_stypes = []
    # longest time consuming part, don't know how to optimize yet
    for stype in stypes:
        stype_dict = get_sobject_dict(stype)
        stype_dict['column_info'] = stype.get_column_info(stype.get_code())
        all_stypes.append(stype_dict)

        # getting views for columns viewer
        # This is because some of built-in views hardcoded in source files
        if project_code == 'sthpw':
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

    # configs = WidgetDbConfig('').get_all_by_search_type('SideBarWdg')

    search = Search(WidgetDbConfig.SEARCH_TYPE)
    configs = search.get_sobjects()

    views_configs = []
    for config in configs:
        views_configs.append(get_sobject_dict(config))

    result = {'schema': schema, 'pipelines': pipelines, 'stypes': all_stypes, 'views': views_configs}

    return json.dumps(result, separators=(',', ':'))


def get_dirs_with_naming(search_key=None, process_list=None):
    import json
    from pyasm.biz import Snapshot
    from pyasm.biz import Project
    from pyasm.search import SearchType, Search

    search_type, search_code = server.split_search_key(search_key)
    project_code = Project.extract_project_code(search_type)
    server.set_project(project_code)

    search_type = search_type.split('?')[0]

    dir_naming = Project.get_dir_naming()

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
        pipeline = Pipeline.get_by_sobject(sobject)
        processes = pipeline.get_process_names()

        # getting sub processes
        pipeline.get_process_sobject('dummy')
        processes_sobjects = pipeline.process_sobjects
        for process_sobject in processes_sobjects.values():
            parent_process = process_sobject.get_value('code')
            if parent_process:
                search = Search('sthpw/pipeline')
                search.add_filter(name='parent_process', value=parent_process)
                sub_pipelines = search.get_sobjects()
                if sub_pipelines:
                    for sub_pipeline in sub_pipelines:
                        processes.extend(sub_pipeline.get_process_names())

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


def query_table_layout(search_type, search_keys=None, view='table',
                       project_code=None):
    """Resolve one table through TACTIC's native widget-config stack."""
    import json
    import re

    from pyasm.search import Search, SearchKey, SearchType, WidgetDbConfig
    from pyasm.widget import WidgetConfigView

    if project_code:
        server.set_project(project_code)
    base_search_type = str(search_type or '').split('?', 1)[0]
    if not base_search_type:
        raise ValueError('Search Type is required')
    config = WidgetConfigView.get_by_search_type(
        base_search_type, view, use_cache=False
    )
    definition_config = WidgetConfigView.get_by_search_type(
        base_search_type, 'definition', use_cache=False
    )
    edit_view_config = WidgetConfigView.get_by_search_type(
        base_search_type, 'edit', use_cache=False, layout='EditWdg'
    )
    edit_config = WidgetConfigView.get_by_search_type(
        base_search_type, 'edit_definition', use_cache=False,
        layout='EditWdg'
    )

    def json_value(value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, dict):
            return dict((str(key), json_value(item))
                        for key, item in value.items())
        if isinstance(value, (list, tuple)):
            return [json_value(item) for item in value]
        return str(value)

    def element_xml(source, element_name):
        value = source.get_element_xml(element_name)
        if not value:
            return ''
        return value if isinstance(value, str) else value.to_string()

    def object_value(sobject, name):
        value = sobject.get_value(name, no_exception=True)
        return '' if value is None else str(value)

    def task_cell_records(widget):
        records = []
        colors = getattr(widget, 'status_colors', {}) or {}
        for task in widget.get_tasks() or []:
            status = object_value(task, 'status')
            pipeline_code = object_value(task, 'pipeline_code') or 'task'
            status_colors = (
                colors.get(pipeline_code) or colors.get('task') or {}
            )
            records.append({
                'taskSearchKey': SearchKey.get_by_sobject(
                    task, use_id=False
                ),
                'taskCode': str(task.get_code() or ''),
                'process': object_value(task, 'process'),
                'context': object_value(task, 'context'),
                'status': status,
                'statusColor': str(status_colors.get(status) or ''),
                'assigned': object_value(task, 'assigned'),
                'bidStart': object_value(task, 'bid_start_date'),
                'bidEnd': object_value(task, 'bid_end_date'),
            })
        return records

    def action_cell_values(class_name, column, sobject, widget):
        options = column.get('displayOptions') or {}
        if class_name.endswith('.TaskElementWdg'):
            return {'tasks': task_cell_records(widget)}
        if class_name.endswith('.SObjectDetailElementWdg'):
            target = sobject
            if str(options.get('use_parent') or '').lower() == 'true':
                target = sobject.get_parent() or sobject
            return {
                'targetSearchKey': SearchKey.get_by_sobject(
                    target, use_id=False
                ),
            }
        if class_name.endswith((
                '.ExploreElementWdg', '.ExplorerElementWdg',
                '.ExplorerTableElementWdg')):
            from pyasm.biz import Project
            mode = str(options.get('mode') or 'sandbox')
            if mode == 'sandbox':
                path = Project.get_sandbox_base_dir(
                    sobject, decrement=int(options.get('decrement') or 0)
                )
            else:
                path = Project.get_project_client_lib_dir(sobject, None)
            return {
                'available': bool(path),
                'path': str(path or ''),
            }
        if class_name.endswith((
                '.SObjectFilesElementWdg', '.MetadataElementWdg')):
            return {
                'targetSearchKey': SearchKey.get_by_sobject(
                    sobject, use_id=False
                ),
            }
        if class_name.endswith('.DeleteElementWdg'):
            return {'available': not sobject.is_insert()}
        if not class_name.endswith('.CheckinButtonElementWdg'):
            return {}
        target = sobject
        process = str(options.get('process') or 'publish')
        context = process
        if sobject.get_base_search_type() in ('sthpw/task', 'sthpw/note'):
            process = object_value(sobject, 'process')
            context = object_value(sobject, 'context')
            if re.search(r'/(\d+)$', context):
                context = ''
            mode = str(options.get('sobject_mode') or 'parent')
            if mode == 'parent':
                target = sobject.get_parent()
            elif mode in ('connect', 'expression'):
                target = Search.eval('@SOBJECT(connect)', sobject, single=True)
            if not target:
                return {'available': False}
        return {
            'available': True,
            'targetSearchKey': SearchKey.get_by_sobject(
                target, use_id=False
            ),
            'process': process,
            'context': context or process,
            'checkinMode': str(options.get('mode') or ''),
            'transferMode': str(options.get('transfer_mode') or ''),
        }

    element_names = config.get_element_names()
    available_names = list(element_names)
    for element_name in definition_config.get_element_names():
        if element_name not in available_names:
            available_names.append(element_name)
    edit_element_names = edit_view_config.get_element_names()
    for element_name in edit_element_names + edit_config.get_element_names():
        if element_name not in available_names:
            available_names.append(element_name)
    for element_name in SearchType.get_columns(
            base_search_type, show_hidden=False):
        if element_name not in available_names:
            available_names.append(element_name)
    titles = config.get_element_titles()
    widths = config.get_element_widths()

    def describe_column(element_name, index=-1):
        attrs = json_value(config.get_element_attributes(element_name) or {})
        hidden = str(attrs.get('hidden') or '').lower() in ('true', '1', 'yes')
        display_handler = config.get_display_handler(element_name) or ''
        display_widget = config.get_widget_key(element_name, 'display') or ''
        edit_handler = edit_config.get_display_handler(element_name) or ''
        edit_widget = edit_config.get_widget_key(element_name, 'display') or ''
        data_type = config.get_type(element_name)
        if not data_type:
            data_type = SearchType.get_tactic_type(
                base_search_type, element_name
            )
        width = attrs.get('width') or (
            widths[index] if 0 <= index < len(widths) else None
        ) or 160
        return {
            'name': element_name,
            'title': attrs.get('title') or (
                titles[index] if 0 <= index < len(titles) else element_name
            ),
            'width': width,
            'selected': element_name in element_names and not hidden,
            'hidden': hidden,
            'dataType': data_type or '',
            'attributes': attrs,
            'displayWidget': display_widget,
            'displayClass': display_handler,
            'displayOptions': json_value(
                config.get_display_options(element_name) or {}
            ),
            'displayXml': element_xml(config, element_name),
            'editWidget': edit_widget,
            'editClass': edit_handler,
            'editOptions': json_value(
                edit_config.get_display_options(element_name) or {}
            ),
            'editXml': element_xml(edit_config, element_name),
            'editSelected': element_name in edit_element_names,
            'actionClass': edit_config.get_action_handler(element_name) or '',
            'actionOptions': json_value(
                edit_config.get_action_options(element_name) or {}
            ),
        }

    available_columns = [
        describe_column(
            element_name,
            element_names.index(element_name)
            if element_name in element_names else -1,
        )
        for element_name in available_names
    ]
    available_columns = [
        column for column in available_columns if not column['hidden']
    ]
    columns = [column for column in available_columns if column['selected']]

    sobjects = Search.get_by_search_keys(
        search_keys or [], keep_order=True
    ) or []
    widgets = {}
    widget_errors = {}
    for column in columns:
        name = column['name']
        column['sortable'] = False
        try:
            widget = config.get_display_widget(name)
            widget.set_sobjects(sobjects)
            widget.preprocess()
            widgets[name] = widget
            column['resolvedClass'] = '%s.%s' % (
                widget.__class__.__module__, widget.__class__.__name__
            )
            if (
                column['resolvedClass'].endswith('.TaskElementWdg')
                and not column['attributes'].get('width')
            ):
                column['width'] = widget.get_width()
            is_sortable = getattr(widget, 'is_sortable', None)
            if is_sortable:
                column['sortable'] = bool(is_sortable())
        except Exception as error:
            column['resolvedClass'] = column['displayClass']
            widget_errors[name] = str(error)

    rows = {}
    for index, sobject in enumerate(sobjects):
        search_key = SearchKey.get_by_sobject(sobject, use_id=False)
        cells = {}
        for column in columns:
            name = column['name']
            error = widget_errors.get(name, '')
            value = None
            widget = widgets.get(name)
            if widget:
                try:
                    widget.set_current_index(index)
                    value = widget.get_text_value()
                except Exception as widget_error:
                    error = str(widget_error)
            if value is None:
                value = sobject.get_value(name, no_exception=True)
            text = '' if value is None else str(value)
            cell = {
                'text': text,
                'error': error,
            }
            if widget:
                try:
                    cell.update(action_cell_values(
                        column.get('resolvedClass') or '',
                        column,
                        sobject,
                        widget,
                    ))
                except Exception as widget_error:
                    cell['error'] = str(widget_error)
            cells[name] = cell
        rows[search_key] = cells

    database_views = {}
    for view_name in (view, 'definition', 'edit', 'edit_definition', 'color'):
        db_config = WidgetDbConfig.get_by_search_type(
            base_search_type, view_name
        )
        if db_config:
            database_views[view_name] = {
                'code': db_config.get_code() or '',
                'config': db_config.get_xml().to_string(),
            }

    return json.dumps({
        'searchType': base_search_type,
        'view': view,
        'columns': columns,
        'availableColumns': available_columns,
        'rows': rows,
        'databaseViews': database_views,
    }, separators=(',', ':'))


def save_widget_config(search_type, view, config_xml=None,
                       element_xml=None, project_code=None):
    """Save a TACTIC view or one element using WidgetConfig semantics."""
    import json

    from pyasm.common import TacticException, Xml
    from pyasm.search import Search, SearchType
    from pyasm.widget import WidgetConfig

    if project_code:
        server.set_project(project_code)
    search_type_object = SearchType.get(search_type)
    base_search_type = search_type_object.get_base_key()

    search = Search('config/widget_config')
    search.add_filter('search_type', base_search_type)
    search.add_filter('view', view)
    config_sobject = search.get_sobject()
    if config_sobject:
        source_xml = config_sobject.get_value('config')
    else:
        config_sobject = SearchType.create('config/widget_config')
        config_sobject.set_value('search_type', base_search_type)
        config_sobject.set_value('view', view)
        source_xml = '<config><%s/></config>' % view

    if element_xml:
        element = Xml()
        element.read_string(element_xml)
        element_name = element.get_value('element/@name')
        if not element_name:
            raise TacticException('Widget element requires a name')
        config = WidgetConfig.get(view, xml=source_xml)
        config.alter_xml_element(
            element_name, config_xml=element.to_string()
        )
        output_xml = config.get_xml().to_string()
    else:
        config = WidgetConfig.get(view, xml=config_xml)
        element_names = config.get_element_names()
        if len(element_names) != len(set(element_names)):
            raise TacticException('Widget view contains duplicate elements')
        output_xml = config.get_xml().to_string()

    config_sobject.set_value('config', output_xml)
    config_sobject.commit()
    return json.dumps({
        'code': config_sobject.get_code() or '',
        'searchType': base_search_type,
        'view': view,
        'config': output_xml,
    }, separators=(',', ':'))


def query_sobjects(search_type, filters=[], order_bys=[], project_code=None, limit=None, offset=None, get_all_snapshots=False, check_snapshots_updates=False, include_info=True, include_snapshots=True, compressed_return=True, include_status_log=False, include_progress=False, include_total_count=True, snapshot_timestamps=None):
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
    import zlib
    import binascii

    from pyasm.search import Search, SearchKey
    from pyasm.biz import Snapshot
    from pyasm.biz import Schema

    if filters:
        if not isinstance(filters, list):
            filters = json.loads(filters)

    if project_code:
        server.set_project(project_code)

    if check_snapshots_updates:
        schema = Schema.get()
        splitted_search_type = server.split_search_key(search_type)[0]
        related_search_types = schema.get_related_search_types(splitted_search_type, 'children')
        check_snapshots_updates_dict = dict(check_snapshots_updates)

    if snapshot_timestamps:
        if isinstance(snapshot_timestamps, str):
            snapshot_timestamps = json.loads(snapshot_timestamps)
        snapshot_timestamps_dict = dict(snapshot_timestamps or {})
    else:
        snapshot_timestamps_dict = {}

    def timestamp_key(value):
        return ''.join(
            character for character in str(value or '')
            if character.isdigit()
        )[:14]

    def get_sobject_dict(sobject):
        search_key = SearchKey.get_by_sobject(sobject, use_id=False)
        sobj = sobject.get_data()
        sobj['__search_key__'] = search_key

        return sobj

    if search_type.startswith('sthpw'):
        splitted_search_type = search_type
    else:
        splitted_search_type, project_code = server.split_search_key(search_type)

    search = Search(splitted_search_type)

    if include_info and include_total_count:
        # Getting count of all sobjects of this stype
        total_sobjects_count = search.get_count()

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

    if filters_list:
        search.add_op_filters(filters_list)

    if order_bys:
        for order_by in order_bys:
            search.add_order_by(order_by)

    if expressions_filters_list:

        for op, expression_filter in expressions_filters_list:
            if op in ['in', 'not in']:
                eval_sobjects = Search.eval(expression_filter)
                if eval_sobjects:
                    search.add_relationship_filters(eval_sobjects, op=op)
                elif op == 'in':
                    search.set_null_filter()
            else:
                if op == 'do not match':
                    op = 'not in'
                else:
                    op = 'in'

                codes = []
                sobjects = Search(search.get_search_type()).get_sobjects()

                for sobject in sobjects:
                    eval_sobjects = Search.eval(expression_filter, sobject, single=True)
                    if eval_sobjects == True:
                        codes.append(sobject.get_code())

                if not codes:
                    search.set_null_filter()
                else:
                    search.add_filters('code', codes, op=op)

    if include_info:
        total_sobjects_query_count = search.get_count()

    if limit:
        search.set_limit(limit)

    if offset:
        search.set_offset(offset)

    sobjects_list = search.get_sobjects()

    sobjects_dicts_list = server.server._get_sobjects_dict(sobjects_list)

    if include_info:
        result = {
            'total_sobjects_count': (
                total_sobjects_count if include_total_count else None
            ),
            'total_sobjects_query_count': total_sobjects_query_count,
            'sobjects_list': sobjects_dicts_list,
            'limit': limit,
            'offset': offset,
        }
    else:
        result = {
            'sobjects_list': sobjects_dicts_list,
            'limit': limit,
            'offset': offset,
        }

    have_search_code = False
    if sobjects_dicts_list:
        if sobjects_dicts_list[0].get('code'):
            have_search_code = True

    if include_progress:
        progress_results = {}
        if sobjects_list:
            # Resolve project pipelines and their config/process records once
            # per distinct code.  The legacy loop queried the same immutable
            # workflow rows again for every result item and every progress
            # process, producing an N x process database query pattern.
            contexts = []
            pipeline_codes_by_scope = {}
            for sobject in sobjects_list:
                search_key = sobject.get_search_key()
                progress_results[search_key] = {}
                pipeline_code = sobject.get_value(
                    'pipeline_code', no_exception=True
                )
                scope = (
                    sobject.get_base_search_type(),
                    sobject.get_project_code(),
                )
                contexts.append((sobject, search_key, scope, pipeline_code))
                if pipeline_code:
                    pipeline_codes_by_scope.setdefault(scope, set()).add(
                        pipeline_code
                    )

            pipelines = {}
            for scope, pipeline_codes in pipeline_codes_by_scope.items():
                search = Search('sthpw/pipeline')
                search.add_filter('search_type', scope[0])
                search.add_filter('project_code', scope[1])
                search.add_filters('code', list(pipeline_codes))
                for pipeline in search.get_sobjects():
                    pipelines[(
                        scope[0], scope[1], pipeline.get_value('code')
                    )] = pipeline

            process_codes = set()
            for _sobject, _search_key, scope, pipeline_code in contexts:
                pipeline = pipelines.get((
                    scope[0], scope[1], pipeline_code
                ))
                if not pipeline:
                    continue
                for process_name in pipeline.get_process_names(
                        type='progress'):
                    pipeline_process = pipeline.get_process(process_name)
                    if pipeline_process:
                        process_code = pipeline_process.get_attribute(
                            'process_code'
                        )
                        if process_code:
                            process_codes.add(process_code)

            processes = {}
            if process_codes:
                search = Search('config/process')
                search.add_filters('code', list(process_codes))
                for process in search.get_sobjects():
                    processes[process.get_value('code')] = process

            behavior_keys = set()
            for process in processes.values():
                workflow = process.get_value('workflow')
                if not workflow or not workflow.get('process'):
                    continue
                behavior_keys.add((
                    workflow.get('process'), workflow.get('pipeline_code')
                ))

            process_behaviors = {}
            behavior_processes = set(
                key[0] for key in behavior_keys if key[0]
            )
            behavior_pipelines = set(
                key[1] for key in behavior_keys if key[1]
            )
            if behavior_processes and behavior_pipelines:
                search = Search('config/process')
                search.add_filters('process', list(behavior_processes))
                search.add_filters(
                    'pipeline_code', list(behavior_pipelines)
                )
                for process in search.get_sobjects():
                    key = (
                        process.get_value('process'),
                        process.get_value('pipeline_code'),
                    )
                    if key in behavior_keys and key not in process_behaviors:
                        process_behaviors[key] = process

            task_pipeline_codes = set()
            for process_behavior in process_behaviors.values():
                workflow = process_behavior.get_value('workflow')
                if workflow and workflow.get('task_pipeline'):
                    task_pipeline_codes.add(workflow.get('task_pipeline'))

            task_behaviors = {}
            if task_pipeline_codes:
                search = Search('config/process')
                search.add_filters(
                    'pipeline_code', list(task_pipeline_codes)
                )
                for process in search.get_sobjects():
                    task_behaviors.setdefault(
                        process.get_value('pipeline_code'), []
                    ).append(process)

            related_cache = {}
            related_tasks_cache = {}
            for sobject, search_key, scope, pipeline_code in contexts:
                pipeline = pipelines.get((
                    scope[0], scope[1], pipeline_code
                ))
                if not pipeline:
                    continue
                processes_result = progress_results[search_key]
                for process_name in pipeline.get_process_names(
                        type='progress'):
                    pipeline_process = pipeline.get_process(process_name)
                    if not pipeline_process:
                        continue
                    process = processes.get(
                        pipeline_process.get_attribute('process_code')
                    )
                    if not process:
                        continue
                    workflow = process.get_value('workflow')
                    if not workflow:
                        continue
                    related_search_type = workflow.get('search_type')
                    if not related_search_type:
                        continue
                    related_key = (search_key, related_search_type)
                    if related_key not in related_cache:
                        related_cache[related_key] = (
                            sobject.get_related_sobjects(related_search_type)
                        )
                    related_sobjects = related_cache[related_key]
                    related_process = workflow.get('process')
                    tasks_filters = []
                    if related_process:
                        behavior_key = (
                            related_process, workflow.get('pipeline_code')
                        )
                        process_behavior = process_behaviors.get(behavior_key)
                        if not process_behavior:
                            continue
                        workflow_behavior = process_behavior.get_value(
                            'workflow'
                        )
                        if not workflow_behavior:
                            continue
                        task_pipeline = workflow_behavior.get('task_pipeline')
                        if not task_pipeline:
                            continue
                        task_statuses = []
                        for task_process_behavior in task_behaviors.get(
                                task_pipeline, []):
                            task_workflow = task_process_behavior.get_value(
                                'workflow'
                            )
                            if task_workflow and task_workflow.get('mapping'):
                                task_statuses.append(
                                    task_process_behavior.get_value('process')
                                )
                        tasks_filters = [('process', related_process)]
                        if task_statuses:
                            tasks_filters.append((
                                'status', 'in', u'|'.join(task_statuses)
                            ))

                    approved_tasks = []
                    filters_key = tuple(tasks_filters)
                    for related_sobject in related_sobjects:
                        task_key = (
                            related_sobject.get_search_key(), filters_key
                        )
                        if task_key not in related_tasks_cache:
                            related_tasks_cache[task_key] = (
                                related_sobject.get_related_sobjects(
                                    'sthpw/task', filters=tasks_filters
                                )
                            )
                        approved_tasks.extend(related_tasks_cache[task_key])

                    if related_sobjects:
                        processes_result[process_name] = {
                            'tc': len(related_sobjects),
                            'ac': len(approved_tasks),
                        }

    if include_snapshots:

        snapshots_sobjects = []
        if get_all_snapshots:
            snapshot_search = Search('sthpw/snapshot')
            snapshot_search.add_relationship_filters(sobjects_list, op='in')
            object_codes = [
                sobject_dict.get('code')
                for sobject_dict in sobjects_dicts_list
                if sobject_dict.get('code')
            ]
            timestamps = [
                snapshot_timestamps_dict.get(code) for code in object_codes
            ]
            if (
                    object_codes and len(timestamps) == len(object_codes)
                    and all(timestamps)):
                snapshot_search.add_op_filters([
                    (
                        'timestamp', 'is after',
                        min(timestamps, key=timestamp_key),
                    )
                ])
            snapshots_sobjects = snapshot_search.get_sobjects()
        else:
            thumb_snapshot_search = Search('sthpw/snapshot')
            thumb_snapshot_search.add_relationship_filters(sobjects_list, op='in')

            thumb_snapshots_sobjects = thumb_snapshot_search.get_sobjects()

            if thumb_snapshots_sobjects:
                thumbs_list = []
                added_list = []
                for snapshot in thumb_snapshots_sobjects:

                    search_code = snapshot.get_value('search_code')
                    process = snapshot.get_value('process')

                    if process in ['icon', 'publish', 'attachment']:
                        thumbs_list.append(snapshot)
                        if search_code not in added_list:
                            added_list.append(search_code)
                    elif search_code not in added_list:
                        # getting any with preview
                        if snapshot.get_file_code_by_type('web'):
                            added_list.append(search_code)
                            thumbs_list.append(snapshot)

                snapshots_sobjects.extend(thumbs_list)

        snapshots_files_sobjects = Snapshot.get_files_dict_by_snapshots(snapshots_sobjects)
        snapshots_by_parent = {}
        parent_column = 'search_code' if have_search_code else 'search_id'
        for snapshot in snapshots_sobjects:
            parent_key = snapshot.get_value(parent_column)
            timestamp = snapshot_timestamps_dict.get(parent_key)
            if (
                    timestamp
                    and timestamp_key(snapshot.get_value('timestamp'))
                    <= timestamp_key(timestamp)):
                continue
            snapshots_by_parent.setdefault(parent_key, []).append(snapshot)

    notes_count_by_key = {}
    tasks_count_by_key = {}
    notes_count_by_process = {}
    tasks_count_by_process = {}
    task_details_by_key = {}
    task_note_counts_by_code = {}
    task_primary_by_code = {}
    if include_info and sobjects_dicts_list:
        if search_type == 'sthpw/task':
            key_column = 'search_code' if have_search_code else 'search_id'
            lookup_values = list(set(
                sobject_dict.get(key_column)
                for sobject_dict in sobjects_dicts_list
                if sobject_dict.get(key_column) not in (None, '')
            ))
            processes = list(set(
                sobject_dict.get('process')
                for sobject_dict in sobjects_dicts_list
                if sobject_dict.get('process') not in (None, '')
            ))
            if lookup_values and processes:
                note_search = Search('sthpw/note')
                note_search.add_filters(key_column, lookup_values)
                note_search.add_filters('process', processes)
                for note in note_search.get_sobjects():
                    key = (
                        note.get_value(key_column),
                        note.get_value('process'),
                    )
                    notes_count_by_key[key] = notes_count_by_key.get(key, 0) + 1

            task_groups = {}
            for task_info in sobjects_dicts_list:
                group_key = (
                    task_info.get(key_column),
                    str(task_info.get('process') or 'publish'),
                )
                task_groups.setdefault(group_key, []).append(task_info)
            task_codes = []
            for group_key, group_tasks in task_groups.items():
                group_tasks.sort(key=lambda item: (
                    0 if not item.get('context')
                    or item.get('context') == group_key[1] else 1,
                    item.get('timestamp') or '', item.get('code') or '',
                ))
                primary_code = (
                    group_tasks[0].get('code') if group_tasks else None
                )
                for task_info in group_tasks:
                    task_code = task_info.get('code')
                    if task_code:
                        if len(group_tasks) > 1:
                            task_codes.append(task_code)
                        task_primary_by_code[task_code] = (
                            task_code == primary_code
                        )
            if task_codes:
                task_note_search = Search('sthpw/note')
                task_note_search.add_filters('search_code', task_codes)
                task_note_search.add_column('search_code')
                task_note_search.add_column('search_type')
                for note in task_note_search.get_sobjects():
                    parent_type = str(
                        note.get_value('search_type') or ''
                    ).split('?', 1)[0]
                    if parent_type not in ('', 'sthpw/task'):
                        continue
                    task_code = note.get_value('search_code')
                    task_note_counts_by_code[task_code] = (
                        task_note_counts_by_code.get(task_code, 0) + 1
                    )
        else:
            key_column = 'search_code' if have_search_code else 'search_id'
            lookup_values = list(set(
                sobject_dict.get('code' if have_search_code else 'id')
                for sobject_dict in sobjects_dicts_list
                if sobject_dict.get('code' if have_search_code else 'id')
                not in (None, '')
            ))
            if lookup_values:
                for table, totals, process_counts in (
                        ('sthpw/note', notes_count_by_key,
                         notes_count_by_process),
                        ('sthpw/task', tasks_count_by_key,
                         tasks_count_by_process)):
                    count_search = Search(table)
                    count_search.add_filter('search_type', search_type)
                    count_search.add_filters(key_column, lookup_values)
                    count_search.add_column(key_column)
                    count_search.add_column('process')
                    if table == 'sthpw/task':
                        for column in (
                                'code', 'context', 'assigned',
                                'status', 'timestamp'):
                            count_search.add_column(column)
                    for item in count_search.get_sobjects():
                        key = item.get_value(key_column)
                        process = str(
                            item.get_value('process') or 'publish'
                        )
                        totals[key] = totals.get(key, 0) + 1
                        process_key = (key, process)
                        process_counts[process_key] = (
                            process_counts.get(process_key, 0) + 1
                        )
                        if table == 'sthpw/task':
                            task_detail = get_sobject_dict(item)
                            task_details_by_key.setdefault(
                                key, {}
                            ).setdefault(process, []).append(task_detail)

                task_codes = [
                    detail.get('code')
                    for process_groups in task_details_by_key.values()
                    for details in process_groups.values()
                    if len(details) > 1
                    for detail in details
                    if detail.get('code')
                ]
                root_notes_count_by_process = dict(notes_count_by_process)
                task_parent_by_code = dict(
                    (detail.get('code'), (parent_key, process))
                    for parent_key, process_groups
                    in task_details_by_key.items()
                    for process, details in process_groups.items()
                    for detail in details
                    if detail.get('code')
                )
                if task_codes:
                    task_note_search = Search('sthpw/note')
                    task_note_search.add_filters('search_code', task_codes)
                    task_note_search.add_column('search_code')
                    task_note_search.add_column('search_type')
                    for note in task_note_search.get_sobjects():
                        parent_type = str(
                            note.get_value('search_type') or ''
                        ).split('?', 1)[0]
                        if parent_type not in ('', 'sthpw/task'):
                            continue
                        task_code = note.get_value('search_code')
                        task_note_counts_by_code[task_code] = (
                            task_note_counts_by_code.get(task_code, 0) + 1
                        )
                        parent_process = task_parent_by_code.get(task_code)
                        if parent_process:
                            parent_key, process = parent_process
                            notes_count_by_key[parent_key] = (
                                notes_count_by_key.get(parent_key, 0) + 1
                            )
                            notes_count_by_process[parent_process] = (
                                notes_count_by_process.get(parent_process, 0)
                                + 1
                            )

                for parent_key, process_groups in task_details_by_key.items():
                    for process, details in process_groups.items():
                        details.sort(key=lambda item: (
                            0 if not item.get('context')
                            or item.get('context') == process else 1,
                            item.get('timestamp') or '', item.get('code') or '',
                        ))
                        primary_code = (
                            details[0].get('code') if details else None
                        )
                        for detail in details:
                            task_code = detail.get('code')
                            detail['__primary_note_branch__'] = (
                                task_code == primary_code
                            )
                            detail['__notes_count__'] = (
                                root_notes_count_by_process.get(
                                    (parent_key, process), 0
                                ) if task_code == primary_code
                                else task_note_counts_by_code.get(task_code, 0)
                            )

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

        if include_info:
            if search_type == 'sthpw/task':
                key_column = 'search_code' if have_search_code else 'search_id'
                count_key = (
                    sobject_dict.get(key_column),
                    sobject_dict.get('process'),
                )
                task_code = sobject_dict.get('code')
                is_primary = task_primary_by_code.get(task_code, True)
                sobject_dict['__primary_note_branch__'] = is_primary
                sobject_dict['__notes_count__'] = (
                    notes_count_by_key.get(count_key, 0) if is_primary
                    else task_note_counts_by_code.get(task_code, 0)
                )
                # there is no reason to search for tasks of tasks, this is never used
                sobject_dict['__tasks_count__'] = 0

                if include_status_log:
                    status_search = Search('sthpw/status_log')
                    if have_search_code:
                        status_search.add_op_filters([('search_code', sobject_dict['code'])])
                    else:
                        status_search.add_op_filters([('search_id', sobject_dict['id'])])

                    status_sobjects = status_search.get_sobjects()

                    status_log_list = []
                    if status_sobjects:

                        for status in status_sobjects:
                            status_dict = get_sobject_dict(status)
                            status_log_list.append(status_dict)

                    sobject_dict['__status_log__'] = status_log_list
            else:
                count_key = sobject_dict.get(
                    'code' if have_search_code else 'id'
                )
                sobject_dict['__notes_count__'] = notes_count_by_key.get(
                    count_key, 0
                )
                sobject_dict['__tasks_count__'] = tasks_count_by_key.get(
                    count_key, 0
                )
                sobject_dict['__notes_count_by_process__'] = dict(
                    (process, count)
                    for (key, process), count
                    in notes_count_by_process.items()
                    if key == count_key
                )
                sobject_dict['__tasks_count_by_process__'] = dict(
                    (process, count)
                    for (key, process), count
                    in tasks_count_by_process.items()
                    if key == count_key
                )
                sobject_dict['__task_details_by_process__'] = dict(
                    (process, list(details))
                    for process, details
                    in task_details_by_key.get(count_key, {}).items()
                )

        if include_snapshots:
            parent_key = sobject_dict.get(
                'code' if have_search_code else 'id'
            )
            related_snapshots = snapshots_by_parent.get(parent_key, [])

            snapshots_list = []
            for snapshot in related_snapshots:

                if snapshot.get_version() in [-1, 0, '-1', '0'] or snapshot.is_latest() or get_all_snapshots:
                    snapshot_dict = get_sobject_dict(snapshot)
                    files_list = []
                    snapshots_files = snapshots_files_sobjects.get(snapshot_dict['code'])
                    if snapshots_files:
                        for fl in snapshots_files:
                            files_list.append(server.server._get_sobject_dict(fl))
                    snapshot_dict['__files__'] = files_list
                    snapshots_list.append(snapshot_dict)
            sobject_dict['__snapshots__'] = snapshots_list

        if include_progress:
            sobject_dict['__progress__'] = progress_results.get(
                sobject.get_search_key(),
                {},
            )

    if compressed_return:
        return '{0}{1}'.format('zlib:', binascii.b2a_hex(zlib.compress(json.dumps(result, separators=(',', ':')).encode(), 9)).decode())
    else:
        return json.dumps(result, separators=(',', ':'))


def query_group_sobjects(search_type, project_code=None, groups_list=[]):

    import json
    from pyasm.search import Search

    if project_code:
        server.set_project(project_code)

    search_type = server.split_search_key(search_type)[0]

    group_bys = []
    for group in groups_list:

        search = Search(search_type)
        search.add_column(group, distinct=True)
        search.add_group_by(group)

        all_groups = []
        for sobject in search.get_sobjects():
            all_groups.append(sobject.data[group])

        group_bys.append((group, all_groups))

    return json.dumps(group_bys, separators=(',', ':'))


def insert_sobjects(
        search_type, project_code, data, metadata={}, parent_key=None,
        instance_type=None, info={}, use_id=False, triggers=True,
        instance_path=None):

    from pyasm.search import SearchType

    server.set_project(project_code)

    multiple = isinstance(data, (list, tuple))
    if multiple:
        metadata_list = metadata
        if isinstance(metadata, dict):
            metadata_list = [dict(metadata) for _item in data]
        result = server.insert_multiple(
            search_type, list(data), metadata_list or [], parent_key,
            use_id, triggers)
        if not isinstance(result, (list, tuple)) or len(result) != len(data):
            raise RuntimeError(
                'TACTIC did not return every batch-created sObject')
    else:
        result = server.insert(
            search_type, data, metadata, parent_key, info, use_id, triggers)

    if instance_type:
        for inserted in result if multiple else [result]:
            instance_search_type, instance_code = server.split_search_key(
                inserted['__search_key__'])
            parent_search_type, parent_code = server.split_search_key(
                parent_key)
            dst_sobject = server.query(
                parent_search_type, [('code', parent_code)],
                return_sobjects=True)[0]
            src_sobject = server.query(
                instance_search_type, [('code', instance_code)],
                return_sobjects=True)[0]
            instance = SearchType.create(instance_type)
            instance.add_related_connection(
                src_sobject, dst_sobject, src_path=instance_path)
            instance.commit()

        return result
    else:
        return result

def edit_multiple_instance_sobjects(
        project_code, insert_search_keys=None, exclude_search_keys=None,
        parent_key=None, instance_type=None, path=None):

    from pyasm.search import SearchType, Search

    server.set_project(project_code)

    def related_instances(child_sobject, parent_sobject):
        parent_relation = instance_type
        child_relation = instance_type
        if path:
            parent_relation = 'child:' + instance_type
            child_relation = 'parent:' + instance_type
        parent_instances = Search.eval(
            '@SOBJECT({0})'.format(parent_relation), parent_sobject
        ) or []
        child_instance_keys = {
            instance.get_search_key()
            for instance in Search.eval(
                '@SOBJECT({0})'.format(child_relation), child_sobject
            ) or []
        }
        return [
            instance for instance in parent_instances
            if instance.get_search_key() in child_instance_keys
        ]

    for search_key in insert_search_keys or ():

        child_search_type, child_code = server.split_search_key(search_key)
        parent_search_type, parent_code = server.split_search_key(parent_key)

        dst_sobject= server.query(parent_search_type, [('code', parent_code)], return_sobjects=True)[0]
        src_sobject = server.query(child_search_type, [('code', child_code)], return_sobjects=True)[0]

        if related_instances(src_sobject, dst_sobject):
            continue

        instance = SearchType.create(instance_type)
        instance.add_related_connection(src_sobject, dst_sobject, src_path=path)
        instance.commit()

    for search_key in exclude_search_keys or ():

        child_search_type, child_code = server.split_search_key(search_key)
        parent_search_type, parent_code = server.split_search_key(parent_key)

        child_sobject = server.query(child_search_type, [('code', child_code)], return_sobjects=True)[0]
        parent_sobject = server.query(parent_search_type, [('code', parent_code)], return_sobjects=True)[0]

        if path:
            for instance in related_instances(child_sobject, parent_sobject):
                instance.delete()
        else:
            child_sobject.remove_instance(parent_sobject)

    return 'ok'


def edit_multiple_tasks_sobjects(project_code, parent_search_keys=None, data=None):
    import json
    from pyasm.search import SearchKey

    server.set_project(project_code)
    parent_search_keys = list(parent_search_keys or [])
    values = dict(data or {})
    process = values.pop('process', None)
    if not process:
        raise ValueError('A process is required for task editing')
    if not parent_search_keys:
        return json.dumps({'updated': 0, 'created': 0})

    parents = []
    parent_codes = []
    for parent_key in parent_search_keys:
        search_type, code = server.split_search_key(parent_key)
        search_type = search_type.split('?', 1)[0]
        parents.append((parent_key, search_type, code))
        parent_codes.append(code)

    filters = [
        ('search_code', 'in', '|'.join(parent_codes)),
        ('project_code', project_code),
        ('process', process),
    ]
    tasks = server.query('sthpw/task', filters, return_sobjects=True) or []
    tasks_by_parent = {}
    for task in tasks:
        key = (
            str(task.get_value('search_type') or '').split('?', 1)[0],
            str(task.get_value('search_code') or ''),
        )
        tasks_by_parent.setdefault(key, []).append(task)

    updates = {}
    created = 0
    for parent_key, search_type, code in parents:
        matches = tasks_by_parent.get((search_type, code), [])
        if not matches:
            # Older task rows may not store search_type. Code is still the
            # canonical relation value, so use it only when unambiguous.
            code_matches = [
                task for (task_type, task_code), task_list in tasks_by_parent.items()
                if not task_type and task_code == code
                for task in task_list
            ]
            matches = code_matches
        if matches:
            for task in matches:
                updates[SearchKey.get_by_sobject(task, use_id=False)] = dict(values)
            continue
        insert_data = dict(values)
        insert_data['process'] = process
        server.insert(
            'sthpw/task', insert_data, parent_key=parent_key, triggers=True,
        )
        created += 1

    if updates:
        server.update_multiple(data=updates, triggers=True)
    return json.dumps({
        'updated': len(updates),
        'created': created,
    }, separators=(',', ':'))


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


def create_snapshot_extended(search_key, context, project_code=None, snapshot_type=None, is_revision=False, is_latest=True, is_current=False, description=None, version=None, level_key=None, update_versionless=True, only_versionless=False, keep_file_name=True, repo_name=None, files_info=None, mode=None, create_icon=True):
    import os
    import shutil
    import json
    from pyasm.biz import Snapshot, IconCreator
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

    if context.startswith('icon'):
        # This is for TACTIC 4.8 >
        update_versionless = False

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

        upload_file_names = files_info.get('upload_file_names') or []

        def file_name_with_extension(name, extension):
            name = os.path.basename(str(name or '').replace('\\', '/'))
            extension = os.path.basename(
                str(extension or '').replace('\\', '/')
            ).lstrip('.')
            if extension:
                return '{0}.{1}'.format(name, extension)
            return name

        for index, (metadata, types) in enumerate(zip(
                files_info['version_metadata'], files_info['files_types'])):
            original_name = file_name_with_extension(
                metadata.get('filename'), metadata.get('new_file_ext'))
            upload_name = (
                os.path.basename(str(upload_file_names[index]).replace('\\', '/'))
                if index < len(upload_file_names) and upload_file_names[index]
                else file_name_with_extension(
                    metadata.get('new_filename'), metadata.get('new_file_ext'))
            )
            original_files_paths.append('{0}/{1}'.format(lib_dir, original_name))
            file_paths.append('{0}/{1}'.format(lib_dir, upload_name))
            file_types.append(types)

        # generating previews if it's not explicitly passed
        if any(i in file_types for i in ['web', 'icon']):
            create_icon = False

        for original_file in file_paths[:]:
            # if this is a file, then try to create an icon
            if os.path.isfile(original_file) and create_icon:
                icon_creator = IconCreator(original_file)
                icon_creator.execute()

                web_path = icon_creator.get_web_path()
                icon_path = icon_creator.get_icon_path()

                # If this is pure icon context, then don't check in icon
                # as the main file.
                if context == 'icon':
                    if web_path:
                        shutil.copy(web_path, original_file)
                    elif icon_path:
                        shutil.copy(icon_path, original_file)

                # If web file is not generated and icon is, use original as web.
                if icon_path and not web_path:
                    base, ext = os.path.splitext(original_file)
                    web_path = "%s_web.%s" % (base, ext)
                    shutil.copy(original_file, web_path)

                if web_path:
                    file_paths.append(web_path)
                    file_types.append('web')
                    original_files_paths.append(web_path)
                    files_info['file_sizes'].append(65536)
                    files_info['version_metadata'].append('')
                    files_info['versionless_metadata'].append('')

                if icon_path:
                    file_paths.append(icon_path)
                    file_types.append('icon')
                    original_files_paths.append(icon_path)
                    files_info['file_sizes'].append(65536)
                    files_info['version_metadata'].append('')
                    files_info['versionless_metadata'].append('')

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

    snapshot_dict = api._get_sobject_dict(snapshot)

    return snapshot_dict

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
