"""Native group access rules, including custom scopes and inherited defaults."""


def security_request(action: str, project_code: str, identity: str = '',
                     document: dict = None, expected_revision: str = '') -> str:
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
        raise PermissionError('Only a TACTIC administrator can change access rules')
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select a project before editing access rules')
    if action not in ('load', 'save'):
        raise ValueError('Unknown security operation')
    groups = Search('sthpw/login_group').get_sobjects()
    catalog = [{'identity': project_code, 'label': project_code}]
    group_catalog = [{'identity': row.get_code(), 'label': row.get_value('login_group')}
                     for row in groups if row.get_value('login_group') != 'admin']
    metadata = {'groups': group_catalog,
                'builtinPermissions': [row for row in permission_list if 'key' in row],
                'accessLevels': list(LoginGroup.ACCESS_DICT)}
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
                 'tasks': {'process': '*', 'pipeline': '*'}}
    for scope, attrs in wildcards.items():
        targets[scope].insert(0, {'label': '', 'all': True, 'attributes': attrs})
    return json.dumps({'identity': identity, 'revision': revision(), 'catalog': catalog,
                       'metadata': metadata, 'canWrite': True, 'document': current})
