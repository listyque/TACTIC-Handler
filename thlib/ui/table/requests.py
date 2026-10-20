"""Native table procedures remain executable on an original TACTIC server."""

def edit_drop_links(search_type, view, column, parent_key, target_keys=None, expected_revision=None, action='prepare'):
    """Self-contained procedure also executed against an original TACTIC server."""
    import hashlib
    import json
    import re
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType
    from pyasm.widget import WidgetConfigView
    if not Environment.get_security().is_admin():
        raise PermissionError('Administration requires administrator access')
    if action not in ('prepare', 'save', 'check'):
        raise ValueError('Invalid link operation')
    from pyasm.biz import Project
    if SearchKey.extract_project(parent_key) not in (None, '', Project.get_project_code()):
        raise ValueError('The configured table target belongs to another project')
    if SearchKey.extract_base_search_type(parent_key) != SearchType.get(search_type).get_base_key():
        raise ValueError('The configured table target is unavailable')
    config = WidgetConfigView.get_by_search_type(search_type, view, use_cache=False)
    if column not in config.get_element_names() or config.get_display_handler(column) not in (
        'tactic.ui.table.DropElementWdg', 'tactic.ui.table.drop_element_wdg.DropElementWdg'):
        raise ValueError('The configured drop column changed. Reload before saving.')
    options = dict(config.get_display_options(column) or {})
    if options.get('cbjs_drop_action'):
        raise ValueError('Custom DOM drop callbacks require a Frame action before they can run in both clients')
    instance_type, accepted = options.get('instance_type'), options.get('accepted_drop_type')
    if not instance_type or not accepted:
        raise ValueError('Configure an instance type and accepted Search Type')
    if action == 'save':
        sql = Search(instance_type).get_sql()
        lock = getattr(sql.get_database_impl(), 'lock_collection_table', None)
        if lock:
            lock(sql, SearchType.get(instance_type).get_table())
        elif sql.get_database_type() == 'PostgreSQL':
            sql.do_update('LOCK TABLE "%s" IN EXCLUSIVE MODE' % SearchType.get(instance_type).get_table().replace('"','""'))
        else:
            raise ValueError('Instance revisions require a transactional database lock')
    parent = Search.get_by_search_key(parent_key)
    if parent is None:
        raise ValueError('The configured table target is unavailable')
    path = options.get('path') or None
    for target in (parent.get_base_search_type(), accepted):
        if not parent.get_schema().get_relationship_attrs(instance_type,target,path=path):
            raise ValueError('The configured instance relationship is unavailable')
    instances = parent.get_related_sobjects(instance_type, path=path)
    revision = hashlib.sha256(json.dumps([options, sorted((row.get_data() for row in instances),
        key=lambda row: str(row.get('id') or row.get('code')))], sort_keys=True, default=str).encode()).hexdigest()
    current = {}
    for instance in instances:
        targets = instance.get_related_sobjects(accepted)
        if len(targets) != 1:
            raise ValueError('An instance must refer to exactly one accepted object')
        current.setdefault(targets[0].get_search_key(), []).append(instance)
    if action == 'prepare':
        return dict(expected_revision=revision, target_keys=list(current))
    if not isinstance(target_keys,list) or len(target_keys)>500 or any(not isinstance(key,str) or not key for key in target_keys):
        raise ValueError('Choose at most 500 linked objects')
    wanted = {}
    for key in target_keys:
        if SearchKey.extract_base_search_type(key) != accepted:
            raise ValueError('Dropped objects belong to another Search Type')
        if SearchKey.extract_project(key) not in (None, '', Project.get_project_code()):
            raise ValueError('Dropped objects belong to another project')
        target = Search.get_by_search_key(key)
        if target is None:
            raise ValueError('A linked object is no longer available')
        wanted[target.get_search_key()] = target
    if action == 'check':
        return dict(state='saved' if set(wanted)==set(current) else 'unchanged' if revision==expected_revision else 'conflict')
    if not expected_revision or revision != expected_revision:
        raise ValueError('Instance links or their definition changed. Reload before saving.')
    # All targets and the entire relation revision are checked before deleting an instance.
    for key, rows in current.items():
        if key not in wanted:
            for instance in rows:
                instance.delete()
    for key, target in wanted.items():
        if key not in current:
            instance = SearchType.create(instance_type)
            instance.add_related_connection(parent,target,src_path=path)
            instance.commit()
    return dict(state='saved', search_key=parent.get_search_key())


def read_group_summary(search_key):
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey
    if not Environment.get_security().is_admin():
        raise PermissionError('Administration requires administrator access')
    if SearchKey.extract_base_search_type(search_key) != 'sthpw/login':
        raise ValueError('Select a user before opening the security summary')
    user = Search.get_by_search_key(search_key)
    if user is None:
        raise ValueError('User is no longer available')
    memberships = Search('sthpw/login_in_group')
    memberships.add_filter('login', user.get_value('login'))
    groups = sorted({row.get_value('login_group') for row in memberships.get_sobjects()})
    sections = []
    for code in groups:
        search = Search('sthpw/login_group')
        search.add_filter('login_group',code)
        group = search.get_sobject()
        if group:
            sections.append(dict(title=code, text=group.get_value('access_rules') or '<rules/>', syntax='xml'))
    return dict(title='Security Summary', identity=user.get_value('display_name') or user.get_value('login'), sections=sections)


def read_custom_layout(search_key, view='', html='', include_mako=True, _depth=0, _behaviors=None):
    import ast
    import json
    import textwrap
    import html as entities
    from html.parser import HTMLParser
    from xml.etree import ElementTree as ET
    from mako.template import Template
    from mako.lexer import Lexer
    from pyasm.search import Search
    from pyasm.common import Environment
    if not Environment.get_security().is_admin():
        raise PermissionError('Administration requires administrator access')
    if _depth >= 8:
        raise ValueError('CustomLayout nesting exceeds eight levels')
    obj = Search.get_by_search_key(search_key)
    if obj is None:
        raise ValueError('Object is no longer available')
    view = str(view).replace('/', '.')
    behaviors = dict(_behaviors or {})
    mako = ''
    if not html:
        search = Search('config/widget_config')
        search.add_filter('view', view)
        configs = [row for row in search.get_sobjects() if row.get_value('category', no_exception=True) == 'CustomLayoutWdg']
        configs.sort(key=lambda row: float(row.get_value('priority', no_exception=True) or 0), reverse=True)
        if not configs:
            raise ValueError('CustomLayout is not configured: ' + view)
        root = ET.fromstring(configs[0].get_value('config'))
        definition = next((node for node in root if node.tag == view or node.get('name') == view), None)
        if definition is None or definition.find('html') is None:
            raise ValueError('CustomLayout has no HTML definition: ' + view)
        mako = definition.findtext('mako') or ''
        body = definition.find('html')
        html = (body.text or '') + ''.join(ET.tostring(child, encoding='unicode') for child in body)
        for behavior in definition.findall('behavior'):
            source = behavior.text or ''
            if behavior.get('event'):
                if behavior.get('event') != 'click_up':
                    raise ValueError('CustomLayout behavior requires a portable click action')
                code = source
            else:
                try:
                    data = json.loads(source)
                except ValueError:
                    data = ast.literal_eval(source)
                if data.get('type') != 'click_up':
                    raise ValueError('CustomLayout behavior requires a portable click action')
                code = data['cbjs_action']
            selector = behavior.get('class') or behavior.get('relay_class')
            if not selector:
                raise ValueError('CustomLayout click action needs a class selector')
            behaviors[selector] = code
    if include_mako not in (False, 'false') and (mako or '${' in html or '<%' in html):
        template_source = ('<%\n' + mako + '\n%>' if mako else '') + html
        # Table reads can retry: layout expressions must never perform a write or I/O.
        allowed = (ast.Module, ast.Expression, ast.Assign, ast.Name, ast.Load, ast.Store,
            ast.Constant, ast.Call, ast.Attribute, ast.keyword, ast.If, ast.IfExp,
            ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is,
            ast.IsNot, ast.In, ast.NotIn, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp,
            ast.Not, ast.USub, ast.UAdd, ast.BinOp, ast.Add, ast.Sub, ast.Mult,
            ast.Div, ast.FloorDiv, ast.Mod, ast.Subscript, ast.Slice, ast.List,
            ast.Tuple, ast.Dict, ast.JoinedStr, ast.FormattedValue)
        pure_builtins = {'str','int','float','bool','len'}
        data_names = {'sobject','sobjects','kwargs','data','plugin'}
        reserved = data_names | pure_builtins | {'context','self','local','parent','next','pageargs','loop','caller','capture','UNDEFINED','STOP_RENDERING'}
        pure_methods = {'get','format','replace','find','strip','upper','lower','join'}
        trees = []
        for part in Lexer(template_source).parse().nodes:
            kind = type(part).__name__
            if kind in ('Text', 'Comment'):
                continue
            if kind not in ('Code', 'Expression') or (kind=='Code' and part.ismodule):
                raise ValueError('CustomLayout supports data-only Mako; use a configured action for code execution')
            if kind=='Expression' and any(name.strip() not in ('n','h','str','trim','u','entity') for name in part.escapes.split(',') if name.strip()):
                raise ValueError('CustomLayout Mako filter is not supported')
            trees.append(ast.parse(textwrap.dedent(part.text).strip(),mode='eval' if kind=='Expression' else 'exec'))
        local_names = {target.id for tree in trees for item in ast.walk(tree) if isinstance(item,ast.Assign)
                       for target in item.targets if isinstance(target,ast.Name)}
        if local_names & reserved:
            raise ValueError('CustomLayout supports data-only Mako; use a configured action for code execution')
        for tree in trees:
            for item in ast.walk(tree):
                valid = isinstance(item,allowed)
                if isinstance(item,ast.Assign):
                    valid = all(isinstance(target,ast.Name) for target in item.targets)
                if isinstance(item,ast.Name):
                    valid = valid and not item.id.startswith('_') and item.id in (local_names | data_names | pure_builtins)
                if isinstance(item,ast.Attribute):
                    valid = valid and item.attr in pure_methods
                if isinstance(item,ast.Call):
                    valid = valid and ((isinstance(item.func,ast.Name) and item.func.id in pure_builtins)
                        or (isinstance(item.func,ast.Attribute) and item.func.attr in pure_methods))
                if not valid:
                    raise ValueError('CustomLayout supports data-only Mako; use a configured action for code execution')
        record = json.loads(json.dumps(obj.get_sobject_dict(),default=str))
        html = Template(template_source).render(
            sobject=record, sobjects=[record],
            kwargs=dict(search_key=search_key, view=view), data={}, plugin={})
    html = entities.unescape(html)
    class Markup(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.root = dict(tag='root', attrs={}, children=[])
            self.stack = [self.root]
        def handle_starttag(self, tag, attrs):
            if len(self.stack)>32:
                raise ValueError('CustomLayout markup exceeds 32 levels')
            item = dict(tag=tag, attrs=dict(attrs), children=[])
            self.stack[-1]['children'].append(item)
            if tag not in ('br', 'embed', 'img', 'hr', 'input'):
                self.stack.append(item)
        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)
        def handle_endtag(self, tag):
            for index in range(len(self.stack)-1, 0, -1):
                if self.stack[index]['tag'] == tag:
                    self.stack = self.stack[:index]
                    break
        def handle_data(self, data):
            self.stack[-1]['children'].append(data)
    if len(html.encode('utf-8')) > 1024*1024:
        raise ValueError('CustomLayout output exceeds one MiB')
    parser = Markup()
    parser.feed(html)
    nodes = []
    def text(item):
        return item if isinstance(item, str) else ''.join(text(child) for child in item['children'])
    def markup(item):
        if isinstance(item, str):
            return entities.escape(item, quote=False)
        tag = item['tag']
        attrs = ''.join(' %s="%s"' % (key, entities.escape(value or '', quote=True)) for key,value in item['attrs'].items())
        content = ''.join(markup(child) for child in item['children'])
        return '<'+tag+attrs+'>'+content+'</'+tag+'>'
    def visit(item):
        if len(nodes)>=128:
            raise ValueError('CustomLayout supports at most 128 controls')
        if isinstance(item, str):
            if item.strip():
                nodes.append(dict(kind='text', text=item.strip()))
            return
        tag, attrs = item['tag'], item['attrs']
        if tag == 'element':
            display = next((child for child in item['children'] if isinstance(child, dict) and child['tag']=='display'), None)
            if display is None:
                raise ValueError('CustomLayout element has no display')
            handler = display['attrs'].get('class') or display['attrs'].get('widget')
            options = {child['tag']: (''.join(markup(part) for part in child['children']) if child['tag']=='html' else text(child).strip()) for child in display['children'] if isinstance(child, dict)}
            if handler in ('tactic.ui.panel.CustomLayoutWdg', 'tactic.ui.table.CustomLayoutElementWdg', 'custom_layout'):
                nodes.extend(read_custom_layout(search_key, _depth=_depth+1, _behaviors=behaviors, **options)['layoutNodes'])
            elif handler in ('pyasm.widget.ThumbWdg', 'ThumbWdg'):
                from pyasm.widget import ThumbWdg
                widget = ThumbWdg(name=attrs.get('name') or 'preview', **options)
                widget.set_sobjects([obj]); widget.preprocess(); widget.set_current_index(0)
                value = widget.get_cell_value() if hasattr(widget, 'get_cell_value') else dict(image=widget.get_data(obj) or '')
                nodes.append(dict(kind='preview', text=str(obj.get_display_value()), value=value,
                                  javascript=behaviors.get(attrs.get('name'), '')))
            else:
                # shortcut: nested TableLayout belongs to the hidden-row/table migration in stage 2.
                raise ValueError('CustomLayout embedded widget is not migrated: ' + str(handler))
        elif tag == 'a':
            source = next((behaviors[name] for name in attrs.get('class','').split() if name in behaviors), '')
            nodes.append(dict(kind='action' if source else 'link', text=text(item).strip(),
                              href=attrs.get('href') or '', javascript=source))
        elif tag in ('object','embed'):
            address = attrs.get('data') or attrs.get('src')
            if address:
                nodes.append(dict(kind='link', text='Open external document', href=address, translate=True))
        elif tag in ('root','html','div','span','p','strong','b','small','br','hr'):
            for child in item['children']:
                visit(child)
        else:
            raise ValueError('CustomLayout markup is not migrated: ' + tag)
    visit(parser.root)
    return dict(text='', layoutNodes=nodes, targetSearchKey=search_key, layoutView=view,
                externalDocuments=any(node['kind']=='link' for node in nodes))
