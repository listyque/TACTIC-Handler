"""Per-process rules use TACTIC's native trigger/notification save commands."""


def process_rules_request(action: str, project_code: str, identity: str = '',
                          document: dict = None, expected_revision: str = '',
                          item_offset: int = 0) -> str:
    import hashlib
    import json
    import xml.etree.ElementTree as ET
    from pyasm.biz import Pipeline, Project
    from pyasm.common import Environment
    from pyasm.search import Search, SearchType
    from tactic.ui.tools import trigger_wdg

    if not Environment.get_security().is_admin():
        raise PermissionError('Administration requires administrator access')
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select a project before editing workflows')
    if action not in ('load', 'save'):
        raise ValueError('Unknown process rule operation')
    query = Search('config/process')
    query.add_filter('code', identity)
    process = query.get_sobject()
    pipeline = Pipeline.get_by_code(process.get_value('pipeline_code')) if process else None
    if not pipeline or pipeline.get_value('project_code') not in (project_code, '', None):
        raise ValueError('Save the process before editing its dependencies')
    shared = not bool(pipeline.get_value('project_code'))
    name, pipeline_code = process.get_value('process'), pipeline.get_code()
    search_type = pipeline.get_value('search_type') or ''
    commands = {
        'task_status': trigger_wdg.StatusTriggerEditCbk,
        'parent_status': trigger_wdg.TriggerParentStatusEditCbk,
        'task_create': trigger_wdg.TriggerCreateCbk,
        'task_date': trigger_wdg.TriggerDateCbk,
        'custom_script': trigger_wdg.PythonScriptTriggerEditCbk,
        'python_class': trigger_wdg.PythonClassTriggerEditCbk,
        'notification': trigger_wdg.NotificationTriggerEditCbk,
    }
    classes = {
        'tactic.command.PipelineTaskStatusTrigger': 'task_status',
        'tactic.command.PipelineParentStatusTrigger': 'parent_status',
        'tactic.command.PipelineTaskCreateTrigger': 'task_create',
        'tactic.command.PipelineTaskDateTrigger': 'task_date',
    }

    def records():
        result = []
        for logical in ('config/trigger', 'sthpw/notification'):
            query = Search(logical)
            query.add_filters('process', [identity, name])
            if logical == 'sthpw/notification':
                query.add_filter('project_code', project_code)
            result.extend(query.get_sobjects())
        # A progress listener listens to ANOTHER process. Its native code is
        # held by this node's workflow JSON, not by trigger.process.
        progress = (process.get_json_value('workflow') or {}).get('progress') or {}
        if progress.get('trigger_code'):
            query = Search('config/trigger')
            query.add_filter('code', progress['trigger_code'])
            listener = query.get_sobject()
            if listener and listener.get_search_key() not in {row.get_search_key() for row in result}:
                result.append(listener)
        return result

    def project_rule(row):
        notification = row.get_base_search_type() == 'sthpw/notification'
        data = row.get_json_value('data') or {}
        values = (data[0] if data else {}) if isinstance(data, list) else data
        if not isinstance(values, dict):
            raise ValueError('Rule data must be a JSON object or a list of objects')
        class_name = '' if notification else row.get_value('class_name') or ''
        script_path = '' if notification else row.get_value('script_path') or ''
        action_name = 'notification' if notification else classes.get(class_name, 'python_class')
        if script_path:
            action_name = 'custom_script'
        elif values.get('class_path'):
            action_name = 'python_class'
        managed = (not notification and (
            row.get_value('event') == 'process|action'
            or class_name == 'pyasm.command.ProcessStatusTrigger'))
        return {
            'key': row.get_search_key(), 'kind': 'notification' if notification else 'trigger',
            'title': row.get_value('title') or '', 'description': row.get_value('description') or '',
            'event': row.get_value('event') or '', 'scope': 'local' if row.get_value('process') == identity else 'global',
            'action': action_name, 'managed': managed,
            'srcStatus': values.get('src_status') or '',
            'targets': [{'process': value.get('dst_process', ''), 'status': value.get('dst_status', '')}
                        for value in data] if isinstance(data, list) else [],
            'outputs': values.get('output') or [], 'column': values.get('column') or '',
            'targetStatus': values.get('dst_status') or '',
            'scriptPath': script_path, 'classPath': values.get('class_path') or class_name,
            'subject': row.get_value('subject') or '' if notification else '',
            'body': row.get_value('message') or '' if notification else '',
            'mailTo': row.get_value('mail_to') or '' if notification else '',
            'mailCc': row.get_value('mail_cc') or '' if notification else '',
            'loginTicket': bool(values.get('login_ticket_create')), 'useTemplate': False,
            'mode': row.get_value('mode') or '' if not notification else '',
            'rules': row.get_value('rules') or '' if notification else '',
        }

    def fingerprint(rows):
        # Include context: saving against a renamed process or changed task
        # workflow is just as unsafe as overwriting a concurrently edited rule.
        data = [pipeline.get_data(), process.get_data(),
                sorted([row.get_data() for row in rows], key=lambda row: str(row.get('code', row.get('id'))))]
        return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()

    current_rows = records()
    current = {row.get_search_key(): project_rule(row) for row in current_rows}
    native = {row.get_search_key(): row for row in current_rows}
    process_query = Search('config/process')
    process_query.add_filter('pipeline_code', pipeline_code)
    native_processes = {row.get_value('process'): row for row in process_query.get_sobjects()}
    processes = []
    for node in pipeline.get_processes():
        record = native_processes.get(node.get_name())
        properties = ((record.get_json_value('workflow') or {}).get('properties') or {}) if record else {}
        # TaskGenerator honors an explicitly assigned task workflow, including
        # approval nodes; Process.get_task_pipeline otherwise supplies defaults.
        task_pipeline = Pipeline.get_by_code(properties.get('task_pipeline') or node.get_task_pipeline())
        processes.append({'identity': node.get_name(), 'label': node.get_name(),
                          'statuses': [status.get_name() for status in task_pipeline.get_processes()]
                          if task_pipeline else []})
    outputs = [node.get_name() for node in pipeline.get_output_processes(name)]
    source_statuses = next((row['statuses'] for row in processes if row['identity'] == name), [])

    if action == 'save':
        if shared:
            raise PermissionError('Shared pipelines are read-only here. Select a project-owned pipeline to edit.')
        if fingerprint(current_rows) != expected_revision:
            raise ValueError('Process dependencies changed on the server. Reload before saving.')
        rules = (document or {}).get('rules')
        if not isinstance(rules, list):
            raise ValueError('Process rules must be a list')
        seen, changed = set(), []
        for rule in rules:
            if not isinstance(rule, dict):
                raise ValueError('Invalid process rule')
            key = rule.get('key', '')
            if key in seen or (key and key not in current):
                raise ValueError('This rule does not belong to the selected process')
            if key:
                seen.add(key)
            old = current.get(key)
            if rule == old:
                continue
            if old and old['managed']:
                raise ValueError('Edit generated workflow triggers in the node parameters')
            if rule.get('action') not in commands or rule.get('scope') not in ('local', 'global'):
                raise ValueError('Choose a rule action and scope')
            if (rule.get('kind') not in ('trigger', 'notification')
                    or (rule.get('kind') == 'notification') != (rule.get('action') == 'notification')
                    or (old and rule.get('kind') != old['kind'])):
                raise ValueError('A trigger cannot be converted into a notification')
            if not str(rule.get('title') or '').strip() or not str(rule.get('event') or '').strip():
                raise ValueError('Enter a rule name and event')
            if rule['event'] == 'process|action':
                raise ValueError('Edit generated workflow triggers in the node parameters')
            if rule.get('srcStatus') and rule['srcStatus'] not in source_statuses and (
                    not old or rule['srcStatus'] != old['srcStatus']):
                raise ValueError('Choose a status from this process task workflow')
            if rule['action'] == 'task_status':
                if not rule.get('targets'):
                    raise ValueError('Select at least one destination process and status')
                for target in rule['targets']:
                    statuses = next((row['statuses'] for row in processes if row['identity'] == target.get('process')), [])
                    if target.get('status') not in statuses:
                        raise ValueError('Choose a status from the destination task workflow')
            if rule['action'] == 'task_create' and (not rule.get('outputs') or any(
                    output not in outputs for output in rule['outputs'])):
                raise ValueError('Choose output processes connected to this node')
            if rule['action'] == 'task_date' and rule.get('column') not in ('actual_start_date', 'actual_end_date'):
                raise ValueError('Choose the actual start or end date')
            if rule['action'] == 'parent_status' and not rule.get('targetStatus'):
                raise ValueError('Enter the destination status')
            if rule['action'] in ('custom_script', 'python_class') and not rule.get(
                    'scriptPath' if rule['action'] == 'custom_script' else 'classPath'):
                raise ValueError('Enter a server script path or command class')
            if rule.get('mode') and rule['mode'] not in (
                    'same process,same transaction', 'separate process,blocking',
                    'separate process,non-blocking', 'separate process,queued') and (
                    not old or rule['mode'] != old['mode']):
                raise ValueError('Choose a native trigger execution mode')
            if rule['kind'] == 'notification':
                # Validate authored rules as XML without evaluating expressions.
                xml = rule.get('rules') or ''
                if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
                    raise ValueError('Document types and XML entities are not supported')
                if xml and ET.fromstring(xml).tag != 'rules':
                    raise ValueError('Notification conditions must have a rules root')
            changed.append(rule)
        deleted = set(current) - seen
        if any(current[key]['managed'] for key in deleted):
            raise ValueError('Edit generated workflow triggers in the node parameters')
        # All validation precedes mutations. execute_python_script supplies the
        # native command transaction; exceptions roll back the whole save.
        for rule in changed:
            old = current.get(rule.get('key'))
            kwargs = dict(search_key=rule.get('key') or None, pipeline_code=pipeline_code,
                          process=name, scope=rule['scope'], title=rule['title'],
                          description=rule.get('description', ''), event=rule['event'],
                          src_status=rule.get('srcStatus', ''),
                          dst_process=[row['process'] for row in rule.get('targets', [])],
                          dst_status=[row['status'] for row in rule.get('targets', [])],
                          output=rule.get('outputs', []), column=rule.get('column', ''),
                          script_path=rule.get('scriptPath', ''), class_path=rule.get('classPath', ''),
                          subject=rule.get('subject', ''), body=rule.get('body', ''),
                          mail_to=rule.get('mailTo', ''), mail_cc=rule.get('mailCc', ''),
                          default='on' if rule.get('useTemplate') else '',
                          login_ticket_create='on' if rule.get('loginTicket') else '')
            if rule['action'] == 'parent_status':
                kwargs['dst_status'] = rule['targetStatus']
            # The native notification callback interpolates src_status into
            # XML unescaped. Build that one field safely below instead.
            if rule['kind'] == 'notification':
                kwargs['src_status'] = ''
            command = commands[rule['action']](**kwargs)
            command.execute()
            saved = Search.get_by_search_key(command.info['search_key'])
            if rule['kind'] == 'notification':
                values = saved.get_json_value('data') or {}
                src = rule.get('srcStatus', '')
                if src:
                    values.update(src_status=src, src_process=name)
                else:
                    values.pop('src_status', None)
                    values.pop('src_process', None)
                saved.set_json_value('data', values)
                condition = rule.get('rules') or ''
                if not old or src != old['srcStatus']:
                    root = ET.fromstring(condition or '<rules/>', parser=ET.XMLParser(
                        target=ET.TreeBuilder(insert_comments=True)))
                    previous_status = old['srcStatus'] if old else ''
                    if previous_status:
                        automatic = {'@GET(.status) == ' + repr(previous_status),
                                     "@GET(.status) == '%s'" % previous_status}
                        for clause in list(root):
                            if clause.tag == 'rule' and (clause.text or '').strip() in automatic:
                                root.remove(clause)
                    if src:
                        ET.SubElement(root, 'rule').text = '@GET(.status) == ' + repr(src)
                    condition = ET.tostring(root, encoding='unicode') if len(root) else ''
                saved.set_value('rules', condition)
            else:
                # Upstream callbacks reset the transaction mode. Preserve an
                # existing mode unless explicitly edited in this form.
                saved.set_value('mode', rule.get('mode') or 'same process,same transaction')
            saved.commit()
        for key in deleted:
            native[key].delete()
        current_rows = records()
        current = {row.get_search_key(): project_rule(row) for row in current_rows}

    naming = Search('config/naming')
    naming.add_filter('context', name + '/%', op='like')
    naming_rows = [{'context': row.get_value('context'), 'file': row.get_value('file_naming'),
                    'directory': row.get_value('dir_naming'), 'searchType': row.get_value('search_type')}
                   for row in naming.get_sobjects()]
    item_offset = max(0, int(item_offset))
    items, item_count = [], 0
    if search_type and SearchType.column_exists(search_type, 'pipeline_code'):
        query = Search(search_type)
        query.add_filter('pipeline_code', pipeline_code)
        item_count = query.get_count()
        query.set_offset(item_offset)
        query.set_limit(50)
        items = [{'key': row.get_search_key(), 'label': row.get_display_value() or row.get_code()}
                 for row in query.get_sobjects()]
    scripts = Search('config/custom_script')
    scripts.add_column('folder')
    scripts.add_column('title')
    script_paths = sorted('/'.join(filter(None, [row.get_value('folder'), row.get_value('title')]))
                          for row in scripts.get_sobjects())
    metadata = dict(process=name, pipeline=pipeline_code, searchType=search_type,
                    processes=processes, sourceStatuses=source_statuses, outputs=outputs,
                    naming=naming_rows, items=items, itemCount=item_count, itemOffset=item_offset,
                    scriptPaths=script_paths)
    return json.dumps(dict(identity=identity, revision=fingerprint(current_rows),
                           canWrite=not shared, metadata=metadata,
                           document={'rules': list(current.values())}), default=str)
