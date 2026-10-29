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
    tools = [dict(name='agent_context', title='Captured context', description='Read the current project, page and selected objects.', readonly=True),
             dict(name='ts_records', title='Project records', description='Read records using the native project permissions.', readonly=True),
             dict(name='ts_tasks_save', title='Save tasks', description='Save task changes using native permissions and revision checks.', readonly=False)]
    editor._metadata.update(users=[dict(value='artist', label='Production artist'), dict(value='lead', label='Production lead')],
        agentTools=tools, mcpTools=tools, agentAdministratorRequired=True,
        effective=dict(checks=[dict(scope='search_type',label='Assets',attributes=dict(code='demo/asset'),required='view',allowed=True),dict(scope='search_type',label='Assets',attributes=dict(code='demo/asset'),required='edit',allowed=False)],login='artist', title='Production artist', administrator=False,
            groups=[dict(name='Artists 0',direct=True,default=False,paths=[['Artists 0']],accessLevel='low',project='demo'),
                    dict(name='Reviewers',direct=False,default=False,paths=[['Artists 0','Reviewers']],accessLevel='none',project='demo'),
                    dict(name='default',direct=True,default=False,paths=[['default']],accessLevel='low',project='demo'),
                    dict(name='default',direct=False,default=True,paths=[],accessLevel='low',project='')],
            rules=[dict(scope='builtin',key='edit?project=demo',access='view',attributes=dict(key='edit'),
                sources=[dict(group='Artists 0',access='deny'),dict(group='Reviewers',access='view'),dict(group='default',default=True,access='view')])],
            tools=dict(chat=['agent_context'],mcp=[])))
    editor._document_loaded()
    editor.stateChanged.emit()
