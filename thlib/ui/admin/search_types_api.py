"""Search Type registry and physical-column operations on the TACTIC server."""


def search_types_request(action: str, project_code: str, identity: str = '',
                         document: dict = None, expected_revision: str = '',
                         schema_revision: str = None) -> str:
    """Serialized as one server procedure; never import client UI modules here."""
    import hashlib
    import json
    import re
    import unicodedata
    import xml.etree.ElementTree as ET
    from pyasm.biz import Project, Schema
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType
    from tactic_client_lib import TacticServerStub

    if not Environment.get_security().is_admin():
        raise PermissionError('TACTIC administrator access is required')
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select a project before editing Search Types')
    if action not in ('list', 'load', 'save'):
        raise ValueError('Unknown Search Type operation')
    if schema_revision is not None:
        if action != 'save' or identity:
            raise ValueError('Schema context is only valid when creating a Search Type')
        schema = Schema.get_by_code(project_code)
        xml = schema.get_value('schema') if schema else '<schema/>'
        if hashlib.sha256(xml.encode()).hexdigest() != schema_revision:
            raise ValueError('Schema changed on the server. Reload before creating a Search Type.')

    def generated_table_name(title):
        transliteration = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
            'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
            'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
            'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
            'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
            'э': 'e', 'ю': 'yu', 'я': 'ya', 'і': 'i', 'ї': 'yi', 'є': 'ye',
            'ґ': 'g',
        }
        transliterated = ''.join(
            transliteration.get(character, character)
            for character in str(title or '').casefold()
        )
        normalized = unicodedata.normalize('NFKD', transliterated)
        identifier = ''.join(
            character if ('a' <= character <= 'z' or '0' <= character <= '9') else '_'
            for character in normalized if not unicodedata.combining(character)
        )
        identifier = re.sub(r'_+', '_', identifier).strip('_')
        if not identifier:
            identifier = 'search_type_' + hashlib.sha1(
                str(title or '').encode('utf-8')).hexdigest()[:10]
        reserved = {
            'all', 'analyse', 'analyze', 'and', 'any', 'array', 'as', 'asc',
            'authorization', 'between', 'binary', 'both', 'case', 'cast',
            'check', 'collate', 'column', 'constraint', 'create', 'current_date',
            'current_time', 'current_timestamp', 'default', 'deferrable',
            'desc', 'distinct', 'do', 'else', 'end', 'except', 'false', 'for',
            'foreign', 'from', 'grant', 'group', 'having', 'in', 'initially',
            'intersect', 'into', 'leading', 'limit', 'localtime',
            'localtimestamp', 'new', 'not', 'null', 'off', 'offset', 'old',
            'on', 'only', 'or', 'order', 'placing', 'primary', 'references',
            'select', 'session_user', 'some', 'table', 'then', 'to', 'trailing',
            'true', 'union', 'unique', 'user', 'using', 'variadic', 'when',
            'where', 'window', 'with',
        }
        if identifier[0].isdigit() or identifier in reserved:
            identifier = 'type_' + identifier
        return identifier[:55].rstrip('_')

    def catalog():
        # Native discovery preserves project namespaces but does not check
        # physical tables for sthpw registry entries.
        project = Project.get()
        types = project.get_search_types(
            include_multi_project=True, include_sthpw=True, include_config=True)
        database = project.get_database_name()
        # Schema.get includes built-in projects; parents and the system schema
        # remain distinct documents. Never infer a link table from its name.
        pending = [Schema.get(reset_cache=action == 'save', project_code=project_code)]
        seen_schemas, seen_connections = set(), set()
        nodes, connections = {}, []
        while pending:
            schema = pending.pop(0)
            if schema is None:
                continue
            xml = schema.get_value('schema') or '<schema/>'
            schema_key = schema.get_code() or hashlib.sha256(xml.encode()).hexdigest()
            if schema_key in seen_schemas:
                continue
            seen_schemas.add(schema_key)
            root = ET.fromstring(xml)
            for node in root.findall('search_type'):
                nodes.setdefault(node.get('name'), dict(node.attrib))
            for edge in root.findall('connect'):
                key = tuple(sorted(edge.attrib.items()))
                if key in seen_connections:
                    continue
                seen_connections.add(key)
                many = (edge.get('relationship') in ('instance', 'many_to_many')
                        or edge.get('type') == 'many_to_many')
                instance = edge.get('instance_type') or (
                    edge.get('path') if edge.get('relationship') == 'instance' else '')
                connections.append(dict(edge.attrib, schema=schema.get_code() or 'sthpw',
                                        manyToMany=many, instanceType=instance or ''))
            pending.extend([schema.get_parent_schema(), schema.sthpw_schema])
        rows = []
        for item in types:
            code = item.get_code()
            attrs = nodes.get(code, {})
            relations = [edge for edge in connections
                         if code in (edge.get('from'), edge.get('to'), edge['instanceType'])]
            link_table = (attrs.get('type') == 'instance' or attrs.get('node_type') == 'instance'
                          or any(edge['instanceType'] == code for edge in relations))
            type_database = item.get_database()
            rows.append({
                'identity': code, 'label': item.get_value('title') or code,
                'description': item.get_value('description') or '',
                'color': item.get_value('color', no_exception=True) or '',
                'namespace': item.get_value('namespace'), 'table': item.get_table(),
                'database': type_database, 'projectLocal': type_database == database,
                'linkTable': link_table,
                'manyToMany': link_table or any(edge['manyToMany'] for edge in relations),
                'relationships': relations,
            })
        return sorted(rows, key=lambda row: row['label'])

    rows = catalog()
    if action == 'list':
        return json.dumps({'catalog': rows, 'canWrite': True})
    permitted = {item['identity'] for item in rows}
    if identity and identity not in permitted:
        raise ValueError('This Search Type is not registered in the selected project')
    item = SearchType.get(identity) if identity else None
    fields = ('title', 'description', 'color')
    table_available = True
    if item:
        # Use the owning database's table catalog, not a SELECT LIMIT 0 probe:
        # failed probes leave PostgreSQL transactions in an aborted state.
        sql = SearchType.get_sql_by_search_type(SearchType.build_search_type(identity, project_code))
        table_available = bool(item.get_table() and sql.table_exists(item.get_table()))
        if action == 'save' and not table_available:
            raise ValueError('Search Type %s is registered, but its database table %s is absent. '
                             'Reload and check the server schema before editing.' % (identity, item.get_table()))

    def snapshot(obj):
        if not obj:
            return {}
        return {field: obj.get_value(field, no_exception=True) or '' for field in fields}

    def revision(obj):
        value = snapshot(obj)
        if obj and table_available:
            value['columns'] = SearchType.get_column_info(identity)
        return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

    def removal_blocks(obj, columns):
        if obj.get_value('namespace') in ('sthpw', 'config'):
            return {name: 'system_type' for name in columns}
        blocks = {'id': 'identity', 'code': 'identity', obj.get_search_type_id_col(): 'identity',
                  's_status': 'tactic', 'pipeline_code': 'tactic'}
        selected = next(row for row in rows if row['identity'] == identity)
        schema = Schema.get(project_code=project_code)
        for relation in selected['relationships']:
            pairs = [(relation['from'], relation['to'], relation.get('path'))]
            if relation['instanceType'] == identity:
                pairs = [(identity, endpoint, None) for endpoint in (relation['from'], relation['to'])]
            attributes = [relation]
            for source, target, path in pairs:
                if schema is not None and '*' not in (source, target):
                    # Native resolution supplies implicit keys and inherited
                    # relationships; do not invent foreign keys from labels.
                    attributes.append(schema.get_relationship_attrs(source, target, path=path, cache=False))
            for attrs in attributes:
                for side in ('from', 'to'):
                    column = attrs.get(side + '_col')
                    if attrs.get(side) == identity and column:
                        blocks.setdefault(column, 'schema')
        return {name: reason for name, reason in blocks.items() if name in columns}

    if action == 'save':
        data = dict(document or {})
        if set(data) - {'title', 'description', 'hasPipeline', 'columns', 'removedColumns', 'color'}:
            raise ValueError('Unknown Search Type setting')
        title = str(data.get('title') or '').strip()
        if not title:
            raise ValueError('Enter a Search Type title')
        color = str(data.get('color') or '')
        if color and not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
            raise ValueError('Use a color in #RRGGBB format or leave it empty')
        removals = data.get('removedColumns', [])
        if (not isinstance(removals, list) or any(
                not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name)
                for name in removals) or len(set(removals)) != len(removals)):
            raise ValueError('Columns to delete must be a list of unique SQL identifiers')
        if removals and not item:
            raise ValueError('Create the Search Type before deleting its columns')
        additions = list(data.get('columns') or [])
        allowed_types = {'varchar(256)', 'text', 'integer', 'numeric', 'boolean', 'timestamp'}
        names = set()
        for column in additions:
            name = str(column.get('name') or '')
            if not re.fullmatch(r'[a-z][a-z0-9_]*', name) or name in names:
                raise ValueError('Column names must be unique lowercase SQL identifiers')
            if column.get('type') not in allowed_types:
                raise ValueError('Unsupported column type')
            names.add(name)
        api = TacticServerStub.get(protocol='local')
        if item:
            if removals:
                SearchType.clear_column_cache(identity)
            if revision(item) != expected_revision:
                raise ValueError('Search Type changed on the server. Reload before saving.')
            if any(name in SearchType.get_columns(identity) for name in names):
                raise ValueError('A column with this name already exists')
            if removals:
                current_columns = SearchType.get_column_info(identity)
                blocks = removal_blocks(item, current_columns)
                for name in removals:
                    if name not in current_columns:
                        raise ValueError('Column %s no longer exists. Reload before saving.' % name)
                    if name in blocks:
                        raise ValueError('Column %s is protected (%s) and cannot be deleted.' % (name, blocks[name]))
                for name in removals:
                    # Same command as TACTIC's Search Type Manager: native
                    # ColumnDropCmd plus definition widget_config cleanup.
                    api.execute_cmd('tactic.ui.panel.AlterSearchTypeCbk', {'alter_mode': 'Remove Column'}, values={
                        'target_search_type': SearchType.build_search_type(identity, project_code),
                        'column_name': name, 'config_mode': 'simple', 'view': 'db_column', 'config_constraint': ''})
            item.set_value('title', title)
            item.set_value('description', str(data.get('description') or ''))
            item.set_value('color', color)
            item.commit()
        else:
            name = generated_table_name(title)
            identity = project_code + '/' + name
            search = Search('sthpw/search_object')
            search.add_filter('code', identity)
            if search.get_sobject():
                raise ValueError('This Search Type already exists. Reload the catalog.')
            api.create_search_type(name, title, str(data.get('description') or ''),
                                   bool(data.get('hasPipeline')))
            item = SearchType.get(identity)
            if color:
                item.set_value('color', color)
                item.commit()
        for column in additions:
            api.add_column_to_search_type(identity, column['name'], column['type'])
        SearchType.clear_column_cache(identity)
        rows = catalog()

    if not item:
        raise ValueError('Select a Search Type')
    values = snapshot(item)
    column_info = SearchType.get_column_info(identity) if table_available else {}
    metadata = {'columns': column_info, 'table': item.get_table(),
                'tableAvailable': table_available,
                'namespace': item.get_value('namespace'),
                'columnRemovalBlocks': removal_blocks(item, column_info) if table_available else {},
                'searchKey': SearchKey.get_by_sobject(item, use_id=False)}
    selected = next(row for row in rows if row['identity'] == identity)
    metadata.update({key: selected[key] for key in (
        'database', 'projectLocal', 'linkTable', 'manyToMany', 'relationships')})
    # Count in the selected project's native database; never fetch all objects
    # to produce a summary. System types without s_status have no retired rows.
    summary = {}
    if table_available:
        objects = Search(identity)
        objects.set_show_retired(True)
        total = objects.get_count()
        retired = 0
        if 's_status' in column_info:
            objects.add_filter('s_status', 'retired')
            retired = objects.get_count()
        summary.update(total=total, active=total - retired, retired=retired, fields=len(column_info))
    pipelines = Search('sthpw/pipeline')
    pipelines.add_filter('search_type', identity)
    related = []
    for pipeline in pipelines.get_sobjects():
        owner = pipeline.get_value('project_code')
        if owner not in (project_code, '', None):
            continue
        graph = ET.fromstring(pipeline.get_value('pipeline') or '<pipeline/>')
        related.append({
            'identity': pipeline.get_code(),
            'label': pipeline.get_value('name') or pipeline.get_code(),
            'description': pipeline.get_value('description') or '',
            'color': pipeline.get_value('color') or '',
            'shared': not bool(owner),
            'processCount': len(graph.findall('process')),
        })
    summary.update(pipelines=len(related), processes=sum(row['processCount'] for row in related))
    metadata.update(
        summary=summary,
        pipelines=sorted(related, key=lambda row: (row['shared'], row['label'])),
        hasPipeline='pipeline_code' in column_info,
    )
    if schema_revision is not None:
        # The native creator commits a schema node as well as the table. Return
        # that new baseline so the canvas can retain its unsaved edits safely.
        schema = Schema.get_by_code(project_code)
        xml = schema.get_value('schema')
        metadata['schema'] = {'xml': xml, 'revision': hashlib.sha256(xml.encode()).hexdigest()}
        Schema.get(reset_cache=True, project_code=project_code)
    return json.dumps({
        'identity': identity, 'revision': revision(item), 'canWrite': table_available,
        'catalog': rows,
        'document': {'title': values['title'], 'description': values['description'],
                     'color': values['color'], 'columns': [], 'removedColumns': []},
        'metadata': metadata,
    }, default=str)
