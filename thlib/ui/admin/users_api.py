"""Read the administrator's Login directory, including native retired records."""


def query_admin_users() -> str:
    import json
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType
    from pyasm.biz import Snapshot

    if not Environment.get_security().is_admin():
        raise PermissionError('Only a TACTIC administrator can manage users')

    search = Search('sthpw/login')
    search.set_show_retired(True)
    logins = search.get_sobjects()
    # Explicit projection: credentials and arbitrary login metadata must never
    # enter the admin draft, QML, logs or local configuration.
    fields = ('code', 'login', 'display_name', 'first_name', 'last_name', 'email',
              'phone_number', 'address', 'department', 'upn', 'namespace',
              's_status', 'project_code', 'license_type', 'hourly_wage')
    columns = set(SearchType.get_columns('sthpw/login'))
    fields = [field for field in fields if field in columns]
    catalog = []
    by_code = {}
    for login in logins:
        data = {field: login.get_value(field) for field in fields}
        data = {key: value if value is not None else '' for key, value in data.items()}
        data['__search_key__'] = SearchKey.get_by_sobject(login, use_id=False)
        row = {'identity': str(data['login']), 'document': data, 'snapshots': []}
        catalog.append(row)
        by_code[str(data['code'])] = row

    if logins:
        search = Search('sthpw/snapshot')
        search.add_relationship_filters(logins, op='in')
        search.add_filters('process', ['icon', 'publish'])
        snapshots = [item for item in search.get_sobjects()
                     if item.get_version() in (-1, 0) or item.is_latest()]
        files = Snapshot.get_files_dict_by_snapshots(snapshots)
        for snapshot in snapshots:
            row = by_code.get(str(snapshot.get_value('search_code')))
            if row is not None:
                data = snapshot.get_data()
                data['__search_key__'] = SearchKey.get_by_sobject(
                    snapshot, use_id=False)
                data['__files__'] = []
                for item in files.get(data['code'], []):
                    file_data = item.get_data()
                    file_data['__search_key__'] = SearchKey.get_by_sobject(
                        item, use_id=False)
                    data['__files__'].append(file_data)
                row['snapshots'].append(data)

    search = Search('sthpw/login_in_group')
    groups = {}
    for item in search.get_sobjects():
        groups.setdefault(str(item.get_value('login')), []).append(str(item.get_value('login_group')))
    group_catalog = [item.get_data() for item in Search('sthpw/login_group').get_sobjects()]
    return json.dumps({'catalog': catalog, 'canWrite': True,
                       'metadata': {'groups': groups, 'fields': fields,
                                    'groupCatalog': group_catalog}}, default=str)
