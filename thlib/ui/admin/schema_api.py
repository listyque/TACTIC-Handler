"""The selected project's own native schema XML, preserving inheritance."""


def schema_request(action: str, project_code: str, identity: str = '',
                   document: dict = None, expected_revision: str = '') -> str:
    import hashlib
    import json
    import math
    import re
    import xml.etree.ElementTree as ET
    from pyasm.biz import Project, Schema
    from pyasm.common import Environment
    from pyasm.search import Search, SearchType

    if not Environment.get_security().is_admin():
        raise PermissionError('TACTIC administrator access is required')
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select a project before editing its schema')
    if action not in ('list', 'load', 'save'):
        raise ValueError('Unknown schema operation')
    catalog = [{'identity': project_code, 'label': project_code}]

    def metadata():
        types = Project.get().get_search_types(include_multi_project=True, include_sthpw=True, include_config=True)
        return {'searchTypes': [{'identity': row.get_code(), 'table': row.get_table(),
                                'label': row.get_value('title') or row.get_code(),
                                'color': row.get_value('color', no_exception=True) or ''}
                               for row in types]}

    if action == 'list':
        return json.dumps({'catalog': catalog, 'metadata': metadata(), 'canWrite': True})
    identity = identity or project_code
    if identity != project_code:
        raise ValueError('This schema is not part of the selected project')
    item = Schema.get_by_code(project_code)
    original = item.get_value('schema') if item else '<schema/>'
    revision = hashlib.sha256(original.encode()).hexdigest()
    if action == 'save':
        if revision != expected_revision:
            raise ValueError('Schema changed on the server. Reload before saving.')
        xml = str((document or {}).get('xml') or '')
        if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():
            raise ValueError('Document types and XML entities are not supported')
        root = ET.fromstring(xml)
        if root.tag != 'schema':
            raise ValueError('The document must have a schema root')
        new_types = (document or {}).get('newTypes', {})
        create_columns = (document or {}).get('createColumns', [])
        if not isinstance(new_types, dict) or not isinstance(create_columns, list):
            raise ValueError('Invalid schema creation plan')
        registered = {row.get_code() for row in Search('sthpw/search_object').get_sobjects()} if new_types else set()
        for name in new_types:
            if not re.fullmatch(re.escape(project_code) + r'/[a-z][a-z0-9_]*', name):
                raise ValueError('Instance Search Types must use the current project and a lowercase table name')
            if name in registered or Project.get().get_sql().table_exists(name.split('/')[1]):
                raise ValueError('Search Type or table %s already exists. Choose another instance name.' % name)
        names = set()
        for node in root.findall('search_type'):
            name = node.get('name')
            if not name or name in names:
                raise ValueError('Schema nodes must have unique Search Type identities')
            if name != '*' and name not in new_types:
                SearchType.get(name)
            names.add(name)
            for axis in ('xpos', 'ypos'):
                if not math.isfinite(float(node.get(axis, '0'))):
                    raise ValueError('Node positions must be finite')
        previous_edges = [dict(edge.attrib) for edge in ET.fromstring(original).findall('connect')]
        edges = root.findall('connect')
        for name in new_types:
            node = next((node for node in root.findall('search_type') if node.get('name') == name), None)
            links = [edge for edge in edges if name in (edge.get('from'), edge.get('to'))]
            if (node is None or node.get('type') != 'instance' or len(links) != 2
                    or len({edge.get('to') for edge in links}) != 2
                    or len({edge.get('from_col') for edge in links}) != 2
                    or any(edge.get('from') != name or edge.get('to') in new_types
                           or edge.get('to') == '*' or edge.get('relationship') != 'code' for edge in links)):
                raise ValueError('Each new instance needs a node and two code connections to distinct existing Search Types')
        column_info = {}
        additions = {}

        def columns(name):
            if name not in column_info:
                if name in new_types:
                    column_info[name] = {}
                else:
                    obj = SearchType.get(name)
                    sql = SearchType.get_sql_by_search_type(name)
                    if not sql.table_exists(obj.get_table()):
                        raise ValueError('The database table for %s is absent' % name)
                    column_info[name] = sql.get_column_info(obj.get_table(), use_cache=False)
            return column_info[name]

        def column_type(info):
            # Native column creation accepts SQL types; only emit known types,
            # never pass an arbitrary metadata string through to native DDL.
            value = str(info.get('data_type', 'varchar')).lower()
            types = {'text': 'text', 'integer': 'integer', 'int4': 'integer',
                     'bigint': 'bigint', 'int8': 'bigint', 'smallint': 'smallint',
                     'numeric': 'numeric', 'boolean': 'boolean', 'uuid': 'uuid'}
            if value in ('varchar', 'character varying'):
                size = info.get('size')
                if size is None:
                    return 'varchar'
                if not isinstance(size, int) or size <= 0:
                    raise ValueError('Invalid key column length')
                return 'varchar(%s)' % size
            if re.fullmatch(r'varchar\([1-9][0-9]*\)', value):
                return value
            if value not in types:
                raise ValueError('Choose an existing column for key type %s' % value)
            return types[value]

        for edge in edges:
            source, target = edge.get('from'), edge.get('to')
            for endpoint in (source, target):
                if not endpoint:
                    raise ValueError('Every relationship needs a source and a target')
                if endpoint != '*' and endpoint not in new_types:
                    SearchType.get(endpoint)
            if edge.get('relationship') == 'many_to_many' and dict(edge.attrib) not in previous_edges:
                raise ValueError('Use an instance Search Type with two code connections for many-to-many')
            if dict(edge.attrib) not in previous_edges and edge.get('relationship', 'code') in ('code', 'id'):
                if not edge.get('from_col') or not edge.get('to_col'):
                    raise ValueError('Choose both key columns for the new relationship before saving')
            for search_type, field in ((source, 'from_col'), (target, 'to_col')):
                column = edge.get(field)
                if not column or search_type == '*' or column in columns(search_type):
                    continue
                key = {key: edge.get(key, '') for key in ('from', 'to', 'path')}
                if search_type not in new_types and key not in create_columns:
                    raise ValueError('Column %s does not exist on %s. Enable Create missing columns or choose an existing column.' % (column, search_type))
                if not re.fullmatch(r'[a-z][a-z0-9_]*', column) or (search_type in new_types and column in (
                        'id', 'code', 'name', 'description', 'keywords', 's_status', 'timestamp', 'login')):
                    raise ValueError('New relationship columns must be non-reserved lowercase SQL identifiers')
                opposite, other_field = (target, 'to_col') if field == 'from_col' else (source, 'from_col')
                other = columns(opposite).get(edge.get(other_field), {}) if opposite != '*' else {}
                datatype = column_type(other)
                identity_column = (search_type, column)
                if identity_column in additions and additions[identity_column] != datatype:
                    raise ValueError('Conflicting types for column %s on %s' % (column, search_type))
                additions[identity_column] = datatype
        # The enclosing native PythonCmd owns the transaction, including table
        # registration, key creation and XML. Validate every edge before writes.
        from tactic_client_lib import TacticServerStub
        api = TacticServerStub.get(protocol='local')
        for name in new_types:
            table = name.split('/')[1]
            api.create_search_type(table, table, 'Many-to-many relationship', has_pipeline=False)
        for (name, column), datatype in additions.items():
            api.add_column_to_search_type(name, column, datatype)
            SearchType.clear_column_cache(name)
        # Native SearchTypeCreatorCmd also modifies this schema. Fetch its
        # current object before replacing it with the complete authored draft.
        if new_types:
            item = Schema.get_by_code(project_code)
        if not item:
            item = Schema.create(project_code, 'Project schema', xml)
        else:
            item.set_xml(xml)
            item.commit()
        Schema.get(reset_cache=True, project_code=project_code)
        original = item.get_value('schema')
        revision = hashlib.sha256(original.encode()).hexdigest()
    return json.dumps({'identity': identity, 'catalog': catalog, 'metadata': metadata(),
                       'canWrite': True, 'revision': revision,
                       'document': {'xml': original}}, default=str)


def schema_columns_request(project_code: str, search_types: list) -> str:
    """Read each endpoint's availability and columns without probing absent tables."""
    import json
    from pyasm.biz import Project
    from pyasm.common import Environment
    from pyasm.search import SearchType

    if not Environment.get_security().is_admin():
        raise PermissionError('TACTIC administrator access is required')
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select a project before editing its schema')
    if not isinstance(search_types, list) or not 1 <= len(search_types) <= 2:
        raise ValueError('Choose the two Search Types of a connection')
    result = {}
    for name in search_types:
        obj = SearchType.get(name)
        # Native resolution uses the current project for {project} types and
        # the registered database for fixed/shared types. Forcing ?project
        # would incorrectly redirect those shared tables to the current DB.
        sql = SearchType.get_sql_by_search_type(name)
        table = obj.get_table()
        available = bool(table and sql.table_exists(table))
        columns = sql.get_column_info(table, use_cache=False) if available else {}
        result[name] = {
            'table': table, 'database': sql.get_database_name(), 'tableAvailable': available,
            'columns': [{'name': column, 'type': str(info.get('data_type') or '')}
                        for column, info in columns.items()],
        }
    return json.dumps(result, default=str)
