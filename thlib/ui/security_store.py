"""Server-owned group metadata and native Login membership operations."""


def query_security_groups() -> str:
    import hashlib
    import json
    from pyasm.search import Search

    objects = Search('sthpw/login_group').get_sobjects()
    markers = {}
    if objects:
        log = Search('sthpw/sobject_log')
        log.add_filter('search_type', 'sthpw/login_group')
        log.add_filters('search_code', [str(item.get_value('code')) for item in objects])
        log.add_column('search_code')
        log.add_column('MAX(id)', as_column='id', quoted=False)
        log.add_group_by('search_code')
        log.order_by = False  # The journal's default timestamp sort would split the aggregate.
        markers = {str(item.get_value('search_code')): item.get_value('id') for item in log.get_sobjects()}
    groups = []
    for item in objects:
        data = dict(item.get_data())
        marker = markers.get(str(data['code']), 0)
        data['revision'] = hashlib.sha256(json.dumps([data, marker], sort_keys=True, default=str).encode()).hexdigest()
        groups.append(data)
    memberships = [{
        'login': str(item.get_value('login') or ''),
        'login_group': str(item.get_value('login_group') or ''),
    } for item in Search('sthpw/login_in_group').get_sobjects()]
    search = Search('sthpw/login')
    search.set_show_retired(True)
    users = [{
        'login': str(item.get_value('login') or ''),
        'retired': item.get_value('s_status', no_exception=True) == 'retired',
        'displayName': str(
            item.get_value('display_name', no_exception=True)
            or ' '.join(str(item.get_value(field) or '')
                        for field in ('first_name', 'last_name')).strip()
            or item.get_value('login') or ''
        ),
    } for item in search.get_sobjects()]
    return json.dumps({'groups': groups, 'memberships': memberships, 'users': users},
                      default=str)


def save_security_group(
        group_code: str, login_group: str, description: str,
        add_members: list, remove_members: list, expected_revision: str) -> str:
    """One RPC transaction; membership deltas preserve unrelated concurrent edits."""
    import hashlib
    import json
    import re
    from pyasm.common import Environment
    from pyasm.search import Search, SearchType

    if not Environment.get_security().is_admin():
        memberships = Search('sthpw/login_in_group')
        memberships.add_filter('login', server.get_login())  # noqa: F821 - injected by execute_python_script
        if not any(group == 'admin' or 'supervisor' in group for group in (
                str(row.get_value('login_group') or '').lower()
                for row in memberships.get_sobjects())):
            raise PermissionError('Only administrators and supervisors can manage user groups')
    if not all(isinstance(value, str) for value in (group_code, login_group, description, expected_revision)):
        raise ValueError('Invalid group details')
    if len(group_code) > 256 or len(description.encode()) > 65536:
        raise ValueError('Group details are too large')
    for values in (add_members, remove_members):
        if not isinstance(values, list) or len(values) > 10000 or any(not isinstance(value, str) or not value or len(value) > 256 for value in values):
            raise ValueError('Invalid group members')
    code = group_code.strip()
    group_name = str(login_group or '').strip()
    description = str(description or '').strip()
    if not group_name or len(group_name) > 100 or re.search(r'[\s/\\<>]', group_name):
        raise ValueError('Enter a group identifier without spaces or slashes')
    additions = set(str(value) for value in add_members)
    removals = set(str(value) for value in remove_members)
    if additions & removals:
        raise ValueError('A user cannot be added and removed at the same time')

    search = Search('sthpw/login_group')
    search.add_filter('code' if code else 'login_group', code or group_name)
    group = search.get_sobject()
    if code and not group:
        raise ValueError('The selected group no longer exists. Refresh the list.')
    if group and str(group.get_value('login_group')) != group_name:
        raise ValueError('An existing group identifier cannot be changed')
    if group and not code:
        search = Search('sthpw/login_in_group')
        search.add_filter('login_group', group_name)
        members = {str(item.get_value('login')) for item in search.get_sobjects()}
        if (str(group.get_value('description') or '') == description
                and additions <= members and not removals):
            return json.dumps({'code': str(group.get_value('code') or '')})
        raise ValueError('A group with this identifier already exists')
    if code:
        log = Search('sthpw/sobject_log')
        log.add_filter('search_type', 'sthpw/login_group')
        log.add_filter('search_code', code)
        log.add_order_by('id desc')
        log.add_limit(1)
        latest = log.get_sobject()
        marker = latest.get_value('id') if latest else 0
        revision = hashlib.sha256(json.dumps([group.get_data(), marker], sort_keys=True, default=str).encode()).hexdigest()
        if not expected_revision or expected_revision != revision:
            raise ValueError('Group details changed. Reload before saving.')
    # Resolve every login before writing anything. Native Login methods own
    # login_in_group identity, access checks and membership notifications.
    logins = {}
    if additions or removals:
        search = Search('sthpw/login')
        search.set_show_retired(True)
        search.add_filters('login', sorted(additions | removals))
        logins = {str(item.get_value('login')): item for item in search.get_sobjects()}
        missing = (additions | removals) - set(logins)
        if missing:
            raise ValueError('Users no longer exist: %s' % ', '.join(sorted(missing)))
    if group is None:
        group = SearchType.create('sthpw/login_group')
        group.set_value('login_group', group_name)
    group.set_value('description', description)
    group.commit()
    search = Search('sthpw/login_in_group')
    search.add_filter('login_group', group_name)
    existing = {str(item.get_value('login')) for item in search.get_sobjects()}
    for login in sorted(additions - existing):
        logins[login].add_to_group(group_name)
    for login in sorted(removals & existing):
        logins[login].remove_from_group(group_name)
    return json.dumps({'code': str(group.get_value('code') or '')})
