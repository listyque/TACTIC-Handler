"""Native group access rules, including custom scopes and inherited defaults."""


def security_request(action: str, project_code: str, identity: str = '',
                     document: dict = None, expected_revision: str = '', login: str = '') -> str:
    import hashlib
    import json
    import xml.etree.ElementTree as ET
    from pyasm.common import Environment
    from pyasm.biz import Project
    from pyasm.search import Search
    from pyasm.security import AccessManager, Login, LoginGroup
    from tactic.ui.panel.security_manager_wdg import permission_list

    security = Environment.get_security()
    if not security.is_admin():
        raise PermissionError('TACTIC administrator access is required')
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select a project before editing access rules')
    if action not in ('load', 'save', 'effective'):
        raise ValueError('Unknown security operation')
    groups = Search('sthpw/login_group').get_sobjects()
    catalog = [{'identity': project_code, 'label': project_code}]
    group_catalog = [{'identity': row.get_code(), 'label': row.get_value('login_group')}
                     for row in groups if row.get_value('login_group') != 'admin']
    metadata = {'groups': group_catalog,
                'builtinPermissions': [row for row in permission_list if 'key' in row],
                'accessLevels': list(LoginGroup.ACCESS_DICT)}
    metadata['users'] = [dict(value=row.get_login(), label=row.get_full_name() or row.get_login())
                         for row in Search('sthpw/login').get_sobjects() if not row.is_retired()]
    try:
        from tactic_stream.server.mcp_access import tool_catalog
        from tactic_stream.server.agent_security import permissions
    except ImportError:
        metadata['agentTools'], metadata['mcpTools'] = [], []
    else:
        metadata['agentTools'], metadata['mcpTools'] = tool_catalog('chat'), tool_catalog('mcp')
    metadata['agentAdministratorRequired'] = True
    def effective_security(login_name, inspect_tools=None, targets=None, builtin=None):
        from pyasm.common import Environment
        from pyasm.security import AccessManager, Login
        from pyasm.security.security import Security

        caller = Environment.get_security()
        if not caller or not caller.is_admin():
            raise PermissionError('TACTIC administrator access is required')
        if not isinstance(login_name, str) or not login_name or len(login_name) > 256:
            raise ValueError('Choose an active user')
        login = Login.get_by_login(login_name)
        if not login or login.is_retired():
            raise ValueError('Choose an active user')
        direct = login.get_sub_group_names()
        subject = Security()
        subject._login = login
        # No ticket, impersonation RPC, writes or caller-manager mutation.
        Environment.set_security(subject)
        try:
            subject._do_login()
            manager = subject.get_access_manager()
            groups = subject.get_groups()
            paths = {}
            by_name = {group.get_login_group(): group for group in groups if group.get_id() != -1}

            def visit(name, path):
                if name in paths or name not in by_name:
                    return
                route = path + [name]
                paths.setdefault(name, []).append(route)
                for child in by_name[name].get_sub_group_names():
                    visit(child, route)

            for name in direct:
                visit(name, [])
            memberships, sources = [], {}
            tool_manager = AccessManager() if subject.is_admin() else None
            for group in groups:
                name = group.get_login_group()
                default = group.get_id() == -1
                memberships.append(dict(name=name, direct=name in direct, default=default,
                    paths=paths.get(name, []), accessLevel=group.get_value('access_level', no_exception=True),
                    project=group.get_value('project_code', no_exception=True) or ''))
                own = AccessManager()
                own.add_xml_rules(group)
                if tool_manager is not None:
                    tool_manager.add_xml_rules(group)
                for scope, rules in own.groups.items():
                    for key, entry in rules.items():
                        access = entry if key == '__DEFAULT__' else entry[0]
                        sources.setdefault((scope, key), []).append(dict(group=name, access=access,
                            default=default, paths=paths.get(name, [])))
            rows, compiled = [], dict(manager.groups)
            if tool_manager is not None:
                for scope in ('agent_tool', 'mcp_tool'):
                    if scope in tool_manager.groups:
                        compiled[scope] = tool_manager.groups[scope]
            for scope, rules in sorted(compiled.items()):
                for key, entry in sorted(rules.items()):
                    access = entry if key == '__DEFAULT__' else entry[0]
                    attributes = {} if key == '__DEFAULT__' else entry[1]
                    rows.append(dict(scope=scope, key=key, access=access or '', attributes=attributes,
                        sources=sources.get((scope, key), [])))
            result = dict(login=login.get_login(), title=login.get_full_name() or login.get_login(),
                          administrator=subject.is_admin(), groups=memberships, rules=rows)
            checks = []
            from pyasm.biz import Project
            project = Project.get_project_code()
            for scope in ('project', 'search_type', 'link', 'gear_menu', 'process', 'tasks', 'builtin'):
                catalog = (targets or {}).get(scope, []) if scope != 'builtin' else [
                    dict(label=entry['title'], attributes=dict(key=entry['key'])) for entry in builtin or []]
                for entry in catalog:
                    if entry.get('all'):
                        continue
                    attrs = {key: value for key, value in entry['attributes'].items() if key != 'project'}
                    wildcard = {key: '*' for key in attrs}
                    native_scope = 'process' if scope == 'tasks' else scope
                    if scope == 'project':
                        keys = [attrs, wildcard]
                    elif scope == 'tasks':
                        keys = [dict(process='*', pipeline=attrs['pipeline']), wildcard, attrs]
                    elif scope == 'gear_menu':
                        keys = [dict(wildcard, project=project), dict(attrs, project=project)]
                    elif scope == 'search_type':
                        keys = [attrs, dict(attrs, project=project), wildcard, dict(wildcard, project=project)]
                    elif scope == 'builtin':
                        keys = [dict(attrs, project=project), dict(attrs, project='*')]
                    else:
                        keys = [dict(attrs, project=project), dict(attrs, project='*'),
                                dict(wildcard, project=project), dict(wildcard, project='*')]
                    levels = ('allow',) if scope in ('project', 'link', 'gear_menu', 'builtin') else ('view', 'edit', 'insert', 'retire', 'delete')
                    for level in levels:
                        checks.append(dict(scope=scope, label=entry['label'], attributes=entry['attributes'],
                            required=level, allowed=subject.check_access(native_scope, keys, level,
                                default='edit' if scope == 'builtin' else 'deny')))
            result['checks'] = checks
            if inspect_tools:
                result['tools'] = inspect_tools(subject)
            return result
        finally:
            Environment.set_security(caller)
    types = Project.get().get_search_types(include_multi_project=True)
    type_targets = [{'label': row.get_value('title') or row.get_code(),
                     'attributes': {'search_type': row.get_code()}} for row in types]
    metadata['targets'] = {
        'project': [{'label': row.get_value('title') or row.get_code(),
                     'attributes': {'code': row.get_code()}}
                    for row in Search('sthpw/project').get_sobjects()],
        'search_type': [{'label': row['label'], 'attributes': {'code': row['attributes']['search_type']}}
                        for row in type_targets],
        'sobject_column': type_targets, 'search_filter': type_targets,
        'sobject': [{'label': row['label'], 'attributes': {'key': row['attributes']['search_type']}}
                    for row in type_targets],
    }
    if identity != project_code:
        raise ValueError('Select the current project security matrix')

    editable_groups = {row.get_code(): row for row in groups
                       if row.get_value('login_group') != 'admin'}

    def read_document():
        return {'groups': {code: {
            'xml': row.get_value('access_rules') or '<rules/>',
            'accessLevel': row.get_value('access_level') or Login.get_default_security_level(),
            'project': row.get_value('project_code', no_exception=True) or '',
            'subGroups': row.get_value('sub_groups', no_exception=True) or '',
        } for code, row in editable_groups.items()}}

    current = read_document()

    def revision():
        return hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest()

    if action == 'save':
        if revision() != expected_revision:
            raise ValueError('Group permissions changed on the server. Reload before saving.')
        proposed = (document or {}).get('groups', {})
        if set(proposed) != set(current['groups']):
            raise ValueError('The group list changed. Reload before saving.')
    else:
        proposed = current['groups']

    def validate_group(code, data):
        group = editable_groups[code]
        xml = str(data.get('xml') or '')
        if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
            raise ValueError('Document types and XML entities are not supported')
        root = ET.fromstring(xml)
        if root.tag != 'rules':
            raise ValueError('Access rules must have a rules root')
        allowed = {'deny', 'allow', 'view', 'edit', 'insert', 'retire', 'delete', 'true', 'false'}
        for rule in root.findall('rule'):
            scope = rule.get('group') or rule.get('category')
            filter_without_access = scope == 'search_filter' and rule.get('access') is None
            native_default = rule.get('default') in allowed
            if not scope or (not filter_without_access and not native_default and rule.get('access') not in allowed):
                raise ValueError('Every rule needs a scope and a valid access level')
        if data.get('accessLevel') not in LoginGroup.ACCESS_DICT:
            raise ValueError('Select a native group access level')
        names = {row.get_value('login_group') for row in groups}
        if data.get('project') and not Project.get_by_code(data['project']):
            raise ValueError('The group project does not exist')
        children = {name for name in str(data.get('subGroups') or '').split('|') if name}
        if children - names or group.get_value('login_group') in children:
            raise ValueError('Subgroups must exist and cannot include the group itself')
        # Validate with the native parser before changing any group fields.
        manager = AccessManager()
        manager.add_xml_rules(xml, project_code=data.get('project') or None)

    if action == 'save':
        changed = [code for code, data in proposed.items() if data != current['groups'][code]]
        for code in changed:
            validate_group(code, proposed[code])
        graph = {row.get_value('login_group'): set(filter(None, str(
            proposed.get(row.get_code(), {}).get('subGroups',
                row.get_value('sub_groups', no_exception=True)) or '').split('|'))) for row in groups}

        def visit(name, path):
            if name in path:
                raise ValueError('Subgroup membership cannot contain a cycle')
            for child in graph.get(name, ()):
                visit(child, path | {name})

        for code in changed:
            visit(editable_groups[code].get_value('login_group'), set())
        # execute_python_script owns the transaction: validate the entire draft
        # before the first commit; never save columns through separate RPCs.
        for code in changed:
            group = editable_groups[code]
            for key, field in (('xml', 'access_rules'), ('accessLevel', 'access_level'),
                               ('project', 'project_code'), ('subGroups', 'sub_groups')):
                group.set_value(field, str(proposed[code].get(key) or ''))
            group.commit()
        security.reset_access_manager()
        current = read_document()
    metadata['globalDefaultRulesByLevel'] = {
        level: LoginGroup.get_default_access_rule(value, [], add_root=True)
        for level, value in LoginGroup.ACCESS_DICT.items()
    }

    # Use the same catalogs as native Link/Gear/Process/Task Security. No web
    # widgets are instantiated, and a broken catalog is an error, not empty UI.
    from tactic.ui.panel import SideBarBookmarkMenuWdg
    from tactic.ui.startup.security_wdg import GearMenuSecurityWdg

    links, seen_links, seen_views = [], set(), set()

    def read_links(view, depth=0):
        if view in seen_views:
            return
        seen_views.add(view)
        config = SideBarBookmarkMenuWdg.get_config('SideBarWdg', view)
        for name in config.get_element_names():
            if not name:
                continue
            attrs = config.get_element_attributes(name)
            handler = config.get_display_handler(name)
            if name not in seen_links:
                seen_links.add(name)
                links.append({'label': attrs.get('title') or name, 'depth': depth,
                              'attributes': {'element': name, 'project': project_code}})
            if handler not in ('LinkWdg', 'SeparatorWdg'):
                read_links(config.get_display_options(name).get('view') or name, depth + 1)

    read_links('project_view')
    targets = metadata['targets']
    script_paths = set()
    script_search = Search('config/custom_script')
    if hasattr(script_search, 'add_columns'):
        script_search.add_columns(['folder', 'title', 's_status'])
    for item in script_search.get_sobjects():
        folder = (item.get_value('folder') or '').replace('\\', '/').strip('/')
        title = item.get_value('title') or ''
        if item.get_value('s_status', no_exception=True) != 'retired':
            script_paths.add('/'.join(filter(None, (folder, title))))
    targets['script_runner'] = [
        {'label': path, 'attributes': {'key': path, 'project': project_code}}
        for path in sorted(script_paths, key=str.casefold)
    ]
    targets['link'] = links
    targets['gear_menu'] = [
        {'label': label, 'detail': submenu,
         'attributes': {'submenu': submenu, 'label': label, 'project': project_code}}
        for submenu, info in GearMenuSecurityWdg.get_all_menu_names()
        for label in info['label'] if label != '*'
    ]
    pipelines = {row.get_code(): row for row in Search('sthpw/pipeline').get_sobjects()}
    task_pipelines = {code for code, row in pipelines.items()
                      if row.get_value('search_type') == 'sthpw/task'} | {'task'}
    targets['process'], targets['tasks'] = [], []
    process_names = set()
    for row in Search('config/process').get_sobjects():
        process, pipeline = row.get_value('process'), row.get_value('pipeline_code')
        if not process:
            continue
        if pipeline in task_pipelines:
            targets['tasks'].append({'label': process, 'detail': pipeline,
                                    'attributes': {'process': process, 'pipeline': pipeline}})
        elif process not in process_names:
            process_names.add(process)
            # Native Process Security is project/process scoped (not pipeline
            # scoped). Do not show independent cells for the same native key.
            targets['process'].append({'label': process,
                                      'attributes': {'process': process, 'project': project_code}})
    for row in targets['search_type']:
        row['attributes']['project'] = project_code
    wildcards = {'project': {'code': '*'}, 'search_type': {'code': '*', 'project': project_code},
                 'link': {'element': '*', 'project': project_code},
                 'gear_menu': {'submenu': '*', 'label': '*', 'project': project_code},
                 'process': {'process': '*', 'project': project_code},
                 'tasks': {'process': '*', 'pipeline': '*'},
                 'script_runner': {'key': '*', 'project': project_code}}
    for scope, attrs in wildcards.items():
        targets[scope].insert(0, {'label': '', 'all': True, 'attributes': attrs})
    if action == 'effective':
        inspect_tools = None
        if metadata['agentTools']:
            inspect_tools = lambda subject: {
                'chat': permissions(subject, [tool['name'] for tool in metadata['agentTools']], 'chat'),
                'mcp': permissions(subject, [tool['name'] for tool in metadata['mcpTools']], 'mcp')}
        metadata['effective'] = effective_security(login, inspect_tools, metadata['targets'], metadata['builtinPermissions'])
    return json.dumps({'identity': identity, 'revision': revision(), 'catalog': catalog,
                       'metadata': metadata, 'canWrite': True, 'document': current})
