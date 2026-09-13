"""Offline native group documents and catalogs for security matrix tests."""

import copy


RULES = '''<rules><!--preserve-->
<rule group="project" code="demo" access="allow"/>
<rule group="link" element="assets" project="demo" access="allow"/>
<rule group="process" process="model" project="demo" access="view"/>
<rule group="process" process="review" pipeline="demo/tasks" access="insert"/>
<rule group="search_filter" search_type="demo/asset" column="assigned" op="=" value="user"/>
<rule category="studio_custom" key="review_gate" access="edit" extra="keep"/>
<extension name="unchanged"/></rules>'''


def seed_security(editor, group_count=3, row_count=4):
    editor._project = editor._identity = 'demo'
    editor._loaded = editor._can_write = True
    editor._catalog = [{'identity': 'demo', 'label': 'Demo'}]
    editor._document = {'groups': {
        'G%s' % index: {'xml': RULES if index == 0 else '<rules/>',
                       'accessLevel': 'none', 'project': '', 'subGroups': ''}
        for index in range(group_count)}}
    editor._original = copy.deepcopy(editor._document)
    editor._metadata = {
        'groups': [{'identity': 'G%s' % index, 'label': 'Artists %s' % index} for index in range(group_count)],
        'accessLevels': ['none', 'low', 'high'],
        'globalDefaultRulesByLevel': {
            'none': '<rules/>',
            'low': '<rules><rule group="search_type" code="*" access="allow"/></rules>',
            'high': '<rules><rule group="project" code="*" access="allow"/></rules>'},
        'targets': {
            'project': [{'label': 'Demo project', 'attributes': {'code': 'demo'}}] + [
                {'label': 'Project %s' % index, 'attributes': {'code': 'project_%s' % index}}
                for index in range(row_count - 1)],
            'link': [{'label': 'Assets', 'attributes': {'element': 'assets', 'project': 'demo'}}],
            'search_type': [{'label': 'Assets', 'attributes': {'code': 'demo/asset', 'project': 'demo'}}],
            'gear_menu': [{'label': 'Export Selected ...', 'attributes': {
                'submenu': 'File', 'label': 'Export Selected ...', 'project': 'demo'}}],
            'process': [{'label': 'model', 'attributes': {'process': 'model', 'project': 'demo'}}],
            'tasks': [{'label': 'review', 'detail': 'demo/tasks', 'attributes': {'process': 'review', 'pipeline': 'demo/tasks'}}],
            'search_filter': [{'label': 'Assets', 'attributes': {'search_type': 'demo/asset'}}],
        },
        'builtinPermissions': [{'key': 'view_side_bar', 'title': 'View Side Bar'}],
    }
    editor._document_loaded()
    editor.stateChanged.emit()
