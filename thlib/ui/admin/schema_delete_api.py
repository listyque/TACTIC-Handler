"""Guarded deletion of an unused Search Type's table in the selected project."""


def schema_delete_request(action: str, project_code: str, identity: str = '',
                          document: dict = None, expected_revision: str = '') -> str:
    """Run in TACTIC's outer transaction; never cascade through production data."""
    import hashlib
    import json
    import xml.etree.ElementTree as ET
    from pyasm.biz import Project, Schema
    from pyasm.common import Environment
    from pyasm.search import Search, SearchType
    from tactic_client_lib import TacticServerStub

    if not Environment.get_security().is_admin():
        memberships = Search('sthpw/login_in_group')
        memberships.add_filter('login', server.get_login())  # noqa: F821 - injected by execute_python_script
        if not any(group == 'admin' or 'supervisor' in group for group in (
                str(row.get_value('login_group') or '').lower()
                for row in memberships.get_sobjects())):
            raise PermissionError('TACTIC administrator or supervisor access is required')
    if not project_code or Project.get_project_code() != project_code:
        raise ValueError('Select a project before deleting a Search Type')
    if action not in ('load', 'save'):
        raise ValueError('Unknown Search Type deletion operation')
    if project_code in ('admin', 'sthpw'):
        raise ValueError('The built-in system schema is read-only')
    if action == 'save':
        from pyasm.search import DbContainer
        registry_sql = DbContainer.get('sthpw')
        # Same ordering as SchemaCmd and SearchTypesCmd. Serialize schema and
        # registry changes before fetching a fresh review/revision.
        registry_sql.get_database_impl().lock_collection_table(
            registry_sql, SearchType.get('sthpw/search_object').get_table(), timeout=3000)
        Schema.get(reset_cache=True, project_code=project_code)
    registrations = Search('sthpw/search_object')
    registrations.set_show_retired(True)
    registry = {row.get_code(): row for row in registrations.get_sobjects()}
    obj = registry.get(identity)
    if not obj or obj.get_value('namespace') in ('sthpw', 'config'):
        raise ValueError('System and configuration Search Types cannot be deleted here')
    qualified = SearchType.build_search_type(identity, project_code)
    sql = SearchType.get_sql_by_search_type(identity)
    if sql.get_db_resource().get_key() != Project.get().get_project_db_resource().get_key():
        raise ValueError('This Search Type belongs to another database')
    schema = Schema.get_by_code(project_code)
    if not schema:
        raise ValueError('Select a Search Type node in the project schema')
    xml = schema.get_value('schema')
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True, insert_pis=True))
    root = ET.fromstring(xml, parser=parser)
    if not any(node.get('name') == identity for node in root.findall('search_type')):
        raise ValueError('The Search Type is no longer on this schema. Reload it.')
    table = obj.get_table()
    if not table or not sql.table_exists(table):
        raise ValueError('The Search Type table is absent. Remove its node from the canvas instead.')
    if action == 'save':
        if not sql.is_in_transaction():
            raise RuntimeError('Search Type deletion must run inside a TACTIC transaction')
        # A count alone is not a deletion guard: a check-in could insert an
        # object between the check and the native DROP. Hold the target table
        # until the outer transaction finishes, with a bounded lock wait.
        sql.get_database_impl().lock_table_for_drop(sql, table, timeout=3000)
        # ponytail: lock whole dependency tables during this rare operation;
        # use finer locks only if concurrent authoring throughput requires it.
        for name in ('sthpw/schema', 'sthpw/pipeline', 'sthpw/task', 'sthpw/note',
                     'sthpw/snapshot', 'sthpw/file', 'sthpw/work_hour',
                     'config/trigger', 'config/notification', 'config/process'):
            item = registry.get(name)
            if item is not None:
                owner = SearchType.get_sql_by_search_type(name)
                if owner.table_exists(item.get_table()):
                    owner.get_database_impl().lock_collection_table(owner, item.get_table(), timeout=3000)

    def count(search_type, field=None, values=None):
        query = Search(search_type)
        query.set_show_retired(True)
        if field:
            query.add_filters(field, values)
        return query.get_count()

    objects = count(qualified)
    aliases = sorted(row.get_code() for row in registry.values()
                     if row.get_code() != identity and row.get_table() == table
                     and row.get_database() == obj.get_database())
    pipelines = []
    pipeline_query = Search('sthpw/pipeline')
    pipeline_query.set_show_retired(True)
    pipeline_query.add_filter('search_type', identity)
    for row in pipeline_query.get_sobjects():
        if row.get_value('project_code') == project_code:
            pipelines.append(row)
    used_pipelines = [row.get_code() for row in pipelines
                      if len(ET.fromstring(row.get_value('pipeline') or '<pipeline/>'))]
    references = []
    # Optional tables are checked through the native catalog, never a failed
    # SELECT probe (which aborts the surrounding PostgreSQL transaction).
    for name in ('sthpw/task', 'sthpw/note', 'sthpw/snapshot', 'sthpw/file',
                 'sthpw/work_hour', 'config/trigger', 'config/notification'):
        item = registry.get(name)
        if item is None:
            continue
        owner_sql = SearchType.get_sql_by_search_type(name)
        if not owner_sql.table_exists(item.get_table()):
            continue
        columns = owner_sql.get_column_info(item.get_table(), use_cache=False)
        if 'search_type' in columns:
            found = count(name, 'search_type', [identity, qualified])
            if found:
                references.append({'type': name, 'count': found})
    codes = [row.get_code() for row in pipelines]
    if codes:
        for name in ('config/process', 'sthpw/task'):
            item = registry.get(name)
            if item is not None:
                owner = SearchType.get_sql_by_search_type(name)
                if not owner.table_exists(item.get_table()) or 'pipeline_code' not in owner.get_column_info(item.get_table(), use_cache=False):
                    continue
            found = count(name, 'pipeline_code', codes)
            if found:
                references.append({'type': name, 'count': found})
    shared = obj.get_value('database') == '{project}'
    other_schemas = []
    if not shared:
        schemas = Search('sthpw/schema')
        schemas.set_show_retired(True)
        for other in schemas.get_sobjects():
            if other.get_code() == project_code:
                continue
            other_root = ET.fromstring(other.get_value('schema') or '<schema/>')
            if any(identity in (node.get('name'), node.get('from'), node.get('to'), node.get('instance_type'))
                   for node in other_root.iter()):
                other_schemas.append(other.get_code())
    details = {'title': obj.get_value('title') or identity, 'table': table,
               'project': project_code, 'objects': objects, 'aliases': aliases,
               'pipelines': codes, 'usedPipelines': used_pipelines,
               'references': references, 'otherSchemas': sorted(other_schemas),
               'sharedRegistration': shared, 'schemaRevision': hashlib.sha256(xml.encode()).hexdigest()}
    revision = hashlib.sha256(json.dumps(details, sort_keys=True).encode()).hexdigest()
    allowed = not (objects or aliases or used_pipelines or references or other_schemas)
    if action == 'save':
        if not allowed:
            raise ValueError('The Search Type is in use. Remove its objects and dependencies before deleting it.')
        if revision != expected_revision:
            raise ValueError('Deletion details changed on the server. Review them again.')
        if (document or {}).get('confirmation') != identity:
            raise ValueError('Enter the complete Search Type identifier to confirm deletion')
        api = TacticServerStub.get(protocol='local')
        # Undo restores the registry/table before restoring pipelines: their
        # native defaults resolve the Search Type during SObjectUndo.commit().
        for pipeline in pipelines:
            pipeline.delete()
        # The native command owns table undo and deletion; SQL errors propagate.
        api.execute_cmd('tactic.ui.tools.DeleteSearchTypeCmd',
                        {'search_type': identity, 'values': {'related_types': []}})
        sql.clear_table_cache()
        if sql.table_exists(table):
            raise RuntimeError('TACTIC did not delete the table. The operation has been rolled back.')
        if not shared:
            query = Search('sthpw/search_object')
            query.add_filter('code', identity)
            if query.get_sobject():
                raise RuntimeError('TACTIC did not remove the Search Type registration. The operation has been rolled back.')
        for node in list(root):
            if ((node.tag == 'search_type' and node.get('name') == identity)
                    or (node.tag == 'connect' and identity in (
                        node.get('from'), node.get('to'), node.get('instance_type')))):
                root.remove(node)
        xml = ET.tostring(root, encoding='unicode')
        schema.set_xml(xml)
        schema.commit()
        Schema.get(reset_cache=True, project_code=project_code)
        details['schema'] = {'xml': xml, 'revision': hashlib.sha256(xml.encode()).hexdigest()}
    return json.dumps({'identity': identity, 'revision': revision,
                       'document': {'confirmation': ''}, 'metadata': details, 'canWrite': allowed})
