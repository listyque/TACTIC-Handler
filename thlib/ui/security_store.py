"""Server-owned group metadata and native Login membership operations."""


def query_security_groups() -> str:
    import json
    from pyasm.search import Search

    groups = [item.get_data() for item in Search('sthpw/login_group').get_sobjects()]
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
        add_members: list, remove_members: list) -> str:
    """One RPC transaction; membership deltas preserve unrelated concurrent edits."""
    import json
    import re
    from pyasm.common import Environment
    from pyasm.search import Search, SearchType

    if not Environment.get_security().is_admin():
        raise PermissionError('Only a TACTIC administrator can manage user groups')
    code = str(group_code or '').strip()
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
