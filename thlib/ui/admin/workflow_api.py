"""Workflow documents and the native process/trigger save lifecycle."""


def workflow_request(action: str, project_code: str, identity: str = '',
                     document: dict = None, expected_revision: str = '') -> str:
    import copy
    import hashlib
    import json
    import math
    import posixpath
    import xml.etree.ElementTree as ET
    from pyasm.biz import Pipeline, Project
    from pyasm.common import Environment
    from pyasm.search import Search, SearchType
    from tactic.ui.tools.pipeline_wdg import NewProcessInfoCmd

    if not Environment.get_security().is_admin():
        raise PermissionError('TACTIC administrator access is required to edit workflows and scripts')
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select a project before editing workflows')
    if action not in ('list', 'new', 'load', 'save'):
        raise ValueError('Unknown workflow operation')

    def catalog():
        query = Search('sthpw/pipeline')
        return sorted([
            {'identity': row.get_code(), 'label': row.get_value('name') or row.get_code(),
             'searchType': row.get_value('search_type') or '',
             'color': row.get_value('color') or '',
             'shared': not bool(row.get_value('project_code'))}
            for row in query.get_sobjects()
            if row.get_value('project_code') in (project_code, '', None)
        ], key=lambda row: (row['shared'], row['label']))

    def process_catalog(pipelines):
        if not pipelines:
            return []
        query = Search('config/process')
        query.add_filters('pipeline_code', [row['identity'] for row in pipelines])
        return sorted([
            {'identity': row.get_code(), 'label': row.get_value('process'),
             'pipeline': row.get_value('pipeline_code')}
            for row in query.get_sobjects()], key=lambda row: (row['pipeline'], row['label']))

    types = Project.get().get_search_types(
        include_multi_project=True, include_sthpw=True, include_config=True)
    # These are native engine node kinds, not translated project process names.
    kinds = ['manual', 'action', 'condition', 'approval', 'hierarchy',
             'dependency', 'progress', 'status']
    widgets = Search('config/widget_config')
    widgets.add_filter('category', 'workflow')
    for row in widgets.get_sobjects():
        name = row.get_value('view')
        if name and name not in kinds:
            kinds.append(name)
    pipelines = catalog()
    groups = Search('sthpw/login_group')
    logins = Search('sthpw/login')
    metadata = {'nodeTypes': kinds, 'searchTypes': [
        {'identity': row.get_code(), 'label': row.get_value('title') or row.get_code()}
        for row in types] + ([] if any(row.get_code() == 'sthpw/task' for row in types)
                            else [{'identity': 'sthpw/task', 'label': 'sthpw/task'}]),
        'pipelines': pipelines, 'processes': process_catalog(pipelines),
        'groups': sorted([
            {'identity': row.get_value('login_group'), 'label': row.get_value('login_group')}
            for row in groups.get_sobjects()], key=lambda row: row['label']),
        'users': sorted([
            {'identity': row.get_value('login'),
             'label': row.get_value('display_name') or row.get_value('login')}
            for row in logins.get_sobjects()], key=lambda row: row['label']),
        'canCreate': True}
    if action == 'list':
        return json.dumps({'catalog': pipelines, 'metadata': metadata, 'canWrite': True})
    if action == 'new':
        if identity not in {row['identity'] for row in metadata['searchTypes']}:
            raise ValueError('Choose a registered Search Type')
        # Prepare editor catalogs only; a pipeline is persisted by Save.
        return json.dumps({'identity': '', 'revision': '', 'document': {},
                           'catalog': pipelines, 'metadata': metadata, 'canWrite': True})
    item = Pipeline.get_by_code(identity) if identity else None
    if identity and (not item or item.get_value('project_code') not in (project_code, '', None)):
        raise ValueError('This pipeline does not belong to the selected project')
    shared = bool(item and not item.get_value('project_code'))
    if shared and action == 'save':
        raise PermissionError('Shared pipelines are read-only here. Select a project-owned pipeline to edit.')
    metadata['shared'] = shared

    def processes():
        query = Search('config/process')
        query.add_filter('pipeline_code', identity)
        return query.get_sobjects() if identity else []

    def read_document():
        if not item:
            return {}
        records = processes()
        settings = {row.get_value('process'): row.get_json_value('workflow') or {}
                    for row in records}
        # Native installations can keep action code only in custom_script,
        # rather than duplicating it in workflow JSON. Hydrate that source so
        # editing a description cannot accidentally disconnect its trigger.
        for row in records:
            query = Search('config/trigger')
            query.add_filter('process', row.get_code())
            query.add_filter('event', 'process|action')
            trigger = query.get_sobject()
            if not trigger:
                continue
            defaults = settings[row.get_value('process')].setdefault('default', {})
            defaults['execute_mode'] = trigger.get_value('mode') or ''
            if trigger.get_value('class_name'):
                defaults.update(action='command', on_action_class=trigger.get_value('class_name'))
            elif trigger.get_value('script_path'):
                path = trigger.get_value('script_path')
                folder, title = posixpath.split(path)
                scripts = Search('config/custom_script')
                scripts.add_filter('folder', folder)
                scripts.add_filter('title', title)
                script = scripts.get_sobject()
                defaults.update(action='create_new', script_path=path,
                                script=script.get_value('script') if script else '',
                                language=script.get_value('language') if script else 'python')
        descriptions = {row.get_value('process'): row.get_value('description') or ''
                        for row in records}
        return {'xml': item.get_value('pipeline') or '<pipeline/>',
                'name': item.get_value('name') or '',
                'description': item.get_value('description') or '',
                'color': item.get_value('color') or '',
                'searchType': item.get_value('search_type') or '',
                'processSettings': settings, 'processDescriptions': descriptions}

    def trigger_data():
        records = processes()
        codes = [row.get_code() for row in records]
        if not codes:
            return []
        query = Search('config/trigger')
        query.add_filters('process', codes)
        result = {row.get_code(): row.get_data() for row in query.get_sobjects()}
        listeners = [(row.get_json_value('workflow') or {}).get('progress', {}).get('trigger_code')
                     for row in records]
        listeners = [code for code in listeners if code]
        if listeners:
            query = Search('config/trigger')
            query.add_filters('code', listeners)
            result.update({row.get_code(): row.get_data() for row in query.get_sobjects()})
        return list(result.values())

    current = read_document()
    triggers = trigger_data()

    def revision():
        owned_triggers = [row for row in triggers if row.get('event') == 'process|action'
                          or row.get('class_name') == 'pyasm.command.ProcessStatusTrigger']
        return hashlib.sha256(json.dumps([current, owned_triggers], sort_keys=True,
                                        default=str).encode()).hexdigest()

    if action == 'save':
        data = copy.deepcopy(document or {})
        if item and revision() != expected_revision:
            raise ValueError('Workflow or triggers changed on the server. Reload before saving.')
        search_type = str(data.get('searchType') or '')
        if not search_type:
            raise ValueError('Create a workflow from a saved Search Type.')
        if item and search_type != current['searchType']:
            raise ValueError('A pipeline belongs to its original Search Type. Create a workflow from the required Search Type instead.')
        if search_type not in {row.get_code() for row in types} | {'sthpw/task'}:
            raise ValueError('Select a Search Type from this project')
        xml = str(data.get('xml') or '')
        if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
            raise ValueError('Document types and XML entities are not supported')
        root = ET.fromstring(xml)
        if root.tag != 'pipeline':
            raise ValueError('The document must have a pipeline root')
        names = set()
        nodes = root.findall('process')
        if search_type == 'sthpw/task':
            for node in nodes:
                node.set('type', 'status')
            xml = ET.tostring(root, encoding='unicode')
        previous_nodes = {node.get('name'): node.get('type') or 'manual'
                          for node in ET.fromstring(current.get('xml') or '<pipeline/>').findall('process')}
        process_codes = {row.get_value('process'): row.get_code() for row in processes()}
        for node in nodes:
            name = node.get('name', '').strip()
            if not name or name in names:
                raise ValueError('Process names must be non-empty and unique')
            names.add(name)
            if node.get('process_code') and node.get('process_code') != process_codes.get(name):
                raise ValueError('Process codes are generated by TACTIC and cannot be edited')
            kind = node.get('type') or 'manual'
            if kind not in kinds and kind != previous_nodes.get(name):
                raise ValueError('Select a node type installed on this server')
            for axis in ('xpos', 'ypos'):
                if not math.isfinite(float(node.get(axis, '0'))):
                    raise ValueError('Node positions must be finite')
        for edge in root.findall('connect'):
            if edge.get('from') not in names or edge.get('to') not in names:
                raise ValueError('Connection %s → %s refers to a missing process. Add the process or remove this connection before saving.'
                                 % (edge.get('from') or '?', edge.get('to') or '?'))
        changed = {}
        for node in nodes:
            name = node.get('name')
            settings = data.get('processSettings', {}).get(name, {})
            if not isinstance(settings, dict):
                raise ValueError('Process settings must be a JSON object')
            if any(key in settings and not isinstance(settings[key], dict)
                   for key in ('properties', 'default', 'hierarchy', 'progress')):
                raise ValueError('Process setting sections must be JSON objects')
            previous = current.get('processSettings', {}).get(name, {})
            properties = settings.get('properties') or {}
            old_properties = previous.get('properties') or {}
            for key in ('assigned_group', 'supervisor_group'):
                value = properties.get(key)
                if (value and value != old_properties.get(key)
                        and value not in {row['identity'] for row in metadata['groups']}):
                    raise ValueError('Choose an existing login group for %s' % key)
            task_pipeline = properties.get('task_pipeline')
            if (task_pipeline and task_pipeline != old_properties.get('task_pipeline')
                    and task_pipeline not in {row['identity'] for row in pipelines
                                              if row['searchType'] == 'sthpw/task'}):
                raise ValueError('Choose a task pipeline from this project or the shared catalog')
            description = data.get('processDescriptions', {}).get(name, '')
            previous_description = current.get('processDescriptions', {}).get(name, '')
            kind = node.get('type') or 'manual'
            if (settings != previous or description != previous_description
                    or kind != previous_nodes.get(name)):
                if settings.get('version', 2) != 2:
                    raise ValueError('This process uses an unsupported native workflow format')
                defaults = settings.get('default') or {}
                if (kind in ('action', 'condition') and defaults.get('script_path')
                        and defaults.get('action') != 'command' and not defaults.get('script')):
                    raise ValueError('The action script is empty or unavailable. Load its body or explicitly clear its path before saving.')
                changed[name] = dict(settings, process=name, pipeline_code=identity,
                                     node_type=kind,
                                     description=description, version=2)
        # Native update_dependencies removes config/process records for removed
        # nodes. Reject deletion/renaming while operational data still uses them.
        for process in processes():
            name = process.get_value('process')
            if name in names:
                continue
            if any(row.get('process') == process.get_code() for row in triggers):
                raise ValueError('Process %s still has triggers; remove them in process dependencies first' % name)
            for logical in ('sthpw/task', 'sthpw/snapshot'):
                query = Search(logical)
                query.add_filter('project_code', project_code)
                query.add_filter('process', name)
                if current.get('searchType'):
                    query.add_filter('search_type', current['searchType'])
                query.set_limit(1)
                if query.get_sobject():
                    raise ValueError('Process %s is used by tasks or snapshots and cannot be removed' % name)
        if not item:
            item = SearchType.create('sthpw/pipeline')
            item.set_value('project_code', project_code)
        for key, field in (('name', 'name'), ('description', 'description'),
                           ('color', 'color'), ('searchType', 'search_type')):
            item.set_value(field, str(data.get(key) or ''))
        # The native model accepts valid XML directly. PipelineSaveCbk's web
        # pre-escaping is deliberately not applied to already escaped XML.
        item.set_value('pipeline', xml)
        item.commit()
        if not identity:
            identity = str(item.get_code() or '')
            if not identity:
                raise RuntimeError('TACTIC did not generate a pipeline code')
        # set_pipeline() only populates a cached in-memory XML graph. Persist
        # the field first, then reacquire the native owner with a fresh graph.
        Pipeline.clear_cache(search_key=item.get_search_key())
        item = Pipeline.get_by_code(identity)
        item.update_dependencies()
        for kwargs in changed.values():
            kwargs['pipeline_code'] = identity
            NewProcessInfoCmd(**kwargs).execute()
        Pipeline.clear_cache(search_key=item.get_search_key())
        item = Pipeline.get_by_code(identity)
        current = read_document()
        triggers = trigger_data()
        metadata['pipelines'] = catalog()
        metadata['processes'] = process_catalog(metadata['pipelines'])
    if not item:
        raise ValueError('Select a pipeline')
    metadata['processCodes'] = {row.get_value('process'): row.get_code() for row in processes()}
    return json.dumps({'identity': identity, 'revision': revision(),
                       'canWrite': not shared and bool(current['searchType']),
                       'catalog': metadata['pipelines'], 'metadata': metadata,
                       'document': current}, default=str)
