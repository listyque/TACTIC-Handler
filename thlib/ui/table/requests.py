"""Native table procedures remain executable on an original TACTIC server."""

def edit_drop_links(search_type, view, column, parent_key, target_keys=None, expected_revision=None, action='prepare'):
    """Self-contained procedure also executed against an original TACTIC server."""
    import hashlib
    import json
    import re
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType
    from pyasm.widget import WidgetConfigView
    if not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_admin() and (not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_logged_in() or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().get_user_name() == 'admin' or not (__import__('pyasm.biz', fromlist=['Project']).Project.get_project_code() in ('admin', 'sthpw') or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().check_access('project', [{'code': '*'}, {'code': __import__('pyasm.biz', fromlist=['Project']).Project.get_project_code()}], 'allow', default='deny'))):
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


def read_custom_layout(
    search_key='', view='', html='', include_mako=True, _depth=0, _behaviors=None, filter_values=None
):
    import ast
    import json
    import textwrap
    import re
    import html as entities
    from html.parser import HTMLParser
    from xml.etree import ElementTree as ET
    from mako.template import Template
    from mako.lexer import Lexer
    from mako.exceptions import MakoException
    from pyasm.search import Search
    from pyasm.common import Environment

    if not Environment.get_security().is_admin():
        raise PermissionError('Administration requires administrator access')
    if _depth >= 8:
        raise ValueError('CustomLayout nesting exceeds eight levels')
    if not search_key:
        from pyasm.biz import Project

        project = Project.get_by_code(Project.get_project_code())
        if project is None:
            raise ValueError('Project is no longer available')
        search_key = project.get_search_key()
    obj = Search.get_by_search_key(search_key)
    if obj is None:
        raise ValueError('Object is no longer available')
    view = str(view).replace('/', '.')
    behaviors = dict(_behaviors or {})
    references = {}
    load_actions = []
    mako = ''
    if not html:
        search = Search('config/widget_config')
        search.add_filter('view', view)
        configs = [
            row
            for row in search.get_sobjects()
            if row.get_value('category', no_exception=True) == 'CustomLayoutWdg'
            or (
                not row.get_value('category', no_exception=True)
                and row.get_value('search_type') == 'CustomLayoutWdg'
            )
        ]
        configs.sort(
            key=lambda row: float(row.get_value('priority', no_exception=True) or 0),
            reverse=True,
        )
        if not configs:
            raise ValueError('CustomLayout is not configured: ' + view)
        root = ET.fromstring(configs[0].get_value('config'))
        definition = next(
            (node for node in root if node.tag == view or node.get('name') == view),
            None,
        )
        if definition is not None and definition.find('dashboard') is not None:
            from tactic_stream.server.dashboards import dashboard_layout
            return dashboard_layout(json.loads(definition.findtext('dashboard')), view, search_key, filter_values=filter_values)
        if definition is None or definition.find('html') is None:
            raise ValueError('CustomLayout has no HTML definition: ' + view)
        mako = definition.findtext('mako') or ''
        body = definition.find('html')
        references = {
            child.get('name'): ET.tostring(child, encoding='unicode')
            for child in definition.findall('element')
        }
        html = (body.text or '') + ''.join(
            ET.tostring(child, encoding='unicode') for child in body
        )
        for behavior in definition.findall('behavior'):
            source = behavior.text or ''
            if behavior.get('event'):
                if behavior.get('event') not in ('click_up', 'load'):
                    raise ValueError(
                        'CustomLayout behavior requires a portable click action'
                    )
                code = source
            else:
                try:
                    data = json.loads(source)
                except ValueError:
                    data = ast.literal_eval(source)
                if data.get('type') not in ('click_up', 'load'):
                    raise ValueError(
                        'CustomLayout behavior requires a portable click action'
                    )
                code = data['cbjs_action']
            selector = behavior.get('class') or behavior.get('relay_class')
            if not selector:
                raise ValueError('CustomLayout click action needs a class selector')
            if (behavior.get('event') or data.get('type')) == 'load':
                load_actions.append(dict(selector=selector, javascript=code))
            else:
                behaviors[selector] = code
    html = entities.unescape(html)
    if include_mako not in (False, 'false') and (mako or '${' in html or '<%' in html):
        template_source = ('<%\n' + mako + '\n%>' if mako else '') + html
        # Table reads can retry: layout expressions must never perform a write or I/O.
        allowed = (
            ast.Module,
            ast.Expression,
            ast.Assign,
            ast.Name,
            ast.Load,
            ast.Store,
            ast.Constant,
            ast.Call,
            ast.Attribute,
            ast.keyword,
            ast.If,
            ast.IfExp,
            ast.Compare,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Is,
            ast.IsNot,
            ast.In,
            ast.NotIn,
            ast.BoolOp,
            ast.And,
            ast.Or,
            ast.UnaryOp,
            ast.Not,
            ast.USub,
            ast.UAdd,
            ast.BinOp,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.FloorDiv,
            ast.Mod,
            ast.Subscript,
            ast.Slice,
            ast.List,
            ast.Tuple,
            ast.Dict,
            ast.JoinedStr,
            ast.FormattedValue,
        )
        pure_builtins = {'str', 'int', 'float', 'bool', 'len'}
        data_names = {'sobject', 'sobjects', 'kwargs', 'data', 'plugin', 'server'}
        reserved = (
            data_names
            | pure_builtins
            | {
                'context',
                'self',
                'local',
                'parent',
                'next',
                'pageargs',
                'loop',
                'caller',
                'capture',
                'UNDEFINED',
                'STOP_RENDERING',
            }
        )
        pure_methods = {
            'get',
            'format',
            'replace',
            'find',
            'strip',
            'upper',
            'lower',
            'join',
        }
        trees = []
        try:
            for part in Lexer(template_source).parse().nodes:
                kind = type(part).__name__
                if kind in ('Text', 'Comment'):
                    continue
                if kind not in ('Code', 'Expression') or (
                    kind == 'Code' and part.ismodule
                ):
                    raise ValueError(
                        'CustomLayout supports data-only Mako; use a configured action for code execution'
                    )
                if kind == 'Expression' and any(
                    name.strip() not in ('n', 'h', 'str', 'trim', 'u', 'entity')
                    for name in part.escapes.split(',')
                    if name.strip()
                ):
                    raise ValueError('CustomLayout Mako filter is not supported')
                trees.append(
                    ast.parse(
                        textwrap.dedent(part.text).strip(),
                        mode='eval' if kind == 'Expression' else 'exec',
                    )
                )
        except (SyntaxError, MakoException):
            raise ValueError(
                'CustomLayout supports data-only Mako; use a configured action for code execution'
            ) from None
        local_names = {
            target.id
            for tree in trees
            for item in ast.walk(tree)
            if isinstance(item, ast.Assign)
            for target in item.targets
            if isinstance(target, ast.Name)
        }
        # CG binds `parent` to its JSON search key, before any output; never expose Mako's parent namespace.
        for tree in trees[:1]:
            if not isinstance(tree, ast.Module):
                continue
            for statement in tree.body:
                if (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and statement.targets[0].id == 'parent'
                    and isinstance(statement.value, ast.Call)
                    and isinstance(statement.value.func, ast.Attribute)
                    and isinstance(statement.value.func.value, ast.Name)
                    and statement.value.func.value.id == 'sobject'
                    and statement.value.func.attr == 'get'
                    and len(statement.value.args) == 1
                    and isinstance(statement.value.args[0], ast.Constant)
                    and statement.value.args[0].value == '__search_key__'
                    and not statement.value.keywords
                ):
                    reserved.discard('parent')
                    break
                if any(
                    isinstance(item, ast.Name) and item.id == 'parent'
                    for item in ast.walk(statement)
                ):
                    break
        if local_names & reserved:
            raise ValueError(
                'CustomLayout supports data-only Mako; use a configured action for code execution'
            )
        for tree in trees:
            for item in ast.walk(tree):
                valid = isinstance(item, allowed)
                if isinstance(item, ast.Assign):
                    valid = all(isinstance(target, ast.Name) for target in item.targets)
                if isinstance(item, ast.Name):
                    valid = (
                        valid
                        and not item.id.startswith('_')
                        and item.id in (local_names | data_names | pure_builtins)
                    )
                read_call = isinstance(item, (ast.Attribute, ast.Call)) and isinstance(
                    item.func if isinstance(item, ast.Call) else item, ast.Attribute
                )
                attribute = item.func if isinstance(item, ast.Call) else item
                snapshot_read = (
                    read_call
                    and isinstance(attribute.value, ast.Name)
                    and attribute.value.id == 'server'
                    and attribute.attr in ('get_snapshot', 'get_path_from_snapshot')
                )
                if isinstance(item, ast.Attribute):
                    valid = valid and (item.attr in pure_methods or snapshot_read)
                if isinstance(item, ast.Call):
                    valid = valid and (
                        (
                            isinstance(item.func, ast.Name)
                            and item.func.id in pure_builtins
                        )
                        or (
                            isinstance(item.func, ast.Attribute)
                            and item.func.attr in pure_methods
                        )
                        or snapshot_read
                    )
                if not valid:
                    raise ValueError(
                        'CustomLayout supports data-only Mako; use a configured action for code execution'
                    )
        record = json.loads(json.dumps(obj.get_sobject_dict(), default=str))

        class SnapshotReads:
            # Only this layout's object and the snapshots discovered for it are readable.
            def __init__(self):
                self.snapshots = {}

            def get_snapshot(self, value, context='publish'):
                from pyasm.biz import Snapshot

                if value != record:
                    raise ValueError('CustomLayout snapshot target must be its object')
                snapshot = Snapshot.get_snapshot(
                    obj.get_search_type(),
                    obj.get_code() or obj.get_id(),
                    context=context,
                )
                if not snapshot:
                    return {}
                self.snapshots[snapshot.get_code()] = snapshot
                return snapshot.get_sobject_dict()

            def get_path_from_snapshot(self, code, mode='web'):
                if mode != 'web':
                    raise ValueError('CustomLayout previews require web paths')
                if not code:
                    return ''
                if code not in self.snapshots:
                    raise ValueError(
                        'CustomLayout snapshot is outside the current object'
                    )
                return self.snapshots[code].get_web_path_by_type() or ''

        html = Template(template_source).render(
            sobject=record,
            sobjects=[record],
            kwargs=dict(search_key=search_key, view=view),
            data={},
            plugin={},
            server=SnapshotReads(),
        )

    def expression(match):
        source = match.group(1).strip()
        if not re.fullmatch(r'\{\$(PROJECT|TODAY)\}|@GET\(\.[A-Za-z_]\w*\)', source):
            raise ValueError('CustomLayout supports read-only field expressions')
        return entities.escape(
            str(Search.eval(source, sobjects=obj, single=True) or ''), quote=True
        )

    html = re.sub(r'\[expr\](.*?)\[/expr\]', expression, html, flags=re.S)
    html = html.replace(
        '{@GET(state.search_key)}', entities.escape(search_key, quote=True)
    )

    class Markup(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.root = dict(tag='root', attrs={}, children=[])
            self.stack = [self.root]

        def handle_starttag(self, tag, attrs):
            if len(self.stack) > 32:
                raise ValueError('CustomLayout markup exceeds 32 levels')
            item = dict(tag=tag, attrs=dict(attrs), children=[])
            self.stack[-1]['children'].append(item)
            if tag not in ('br', 'embed', 'img', 'hr', 'input'):
                self.stack.append(item)

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

        def handle_endtag(self, tag):
            for index in range(len(self.stack) - 1, 0, -1):
                if self.stack[index]['tag'] == tag:
                    self.stack = self.stack[:index]
                    break

        def handle_data(self, data):
            self.stack[-1]['children'].append(data)

    if len(html.encode('utf-8')) > 1024 * 1024:
        raise ValueError('CustomLayout output exceeds one MiB')
    parser = Markup()
    parser.feed(html)
    nodes = []
    count = 0
    controls = []
    form = ''

    def text(item):
        return (
            item
            if isinstance(item, str)
            else ''.join(text(child) for child in item['children'])
        )

    def markup(item):
        if isinstance(item, str):
            return entities.escape(item, quote=False)
        tag = item['tag']
        attrs = ''.join(
            ' %s="%s"' % (key, entities.escape(value or '', quote=True))
            for key, value in item['attrs'].items()
        )
        content = ''.join(markup(child) for child in item['children'])
        return '<' + tag + attrs + '>' + content + '</' + tag + '>'

    def visit(item):
        nonlocal nodes, count, form
        count += 1
        if count > 512:
            raise ValueError('CustomLayout supports at most 512 markup nodes')
        if isinstance(item, str):
            if item.strip():
                nodes.append(dict(kind='text', text=item.strip()))
            return
        tag, attrs = item['tag'], item['attrs']
        selector = next(
            (name for name in attrs.get('class', '').split() if name in behaviors), ''
        )
        if selector and tag != 'element':
            nodes.append(
                dict(
                    kind='action',
                    text=attrs.get('value') or text(item).strip(),
                    selector=selector,
                    javascript=behaviors[selector],
                )
            )
            return
        if tag == 'element':
            display = next(
                (
                    child
                    for child in item['children']
                    if isinstance(child, dict) and child['tag'] == 'display'
                ),
                None,
            )
            if display is None and attrs.get('name') in references:
                referenced = Markup()
                referenced.feed(
                    references[attrs['name']].replace(
                        '{@GET(state.search_key)}',
                        entities.escape(search_key, quote=True),
                    )
                )
                visit(referenced.root['children'][0])
                return
            if display is None:
                raise ValueError('CustomLayout element has no display')
            handler = display['attrs'].get('class') or display['attrs'].get('widget')
            options = {
                child['tag']: (
                    ''.join(markup(part) for part in child['children'])
                    if child['tag'] == 'html'
                    else text(child).strip()
                )
                for child in display['children']
                if isinstance(child, dict)
            }
            if handler in (
                'tactic.ui.panel.CustomLayoutWdg',
                'tactic.ui.table.CustomLayoutElementWdg',
                'custom_layout',
            ):
                if set(options) - {
                    'view',
                    'html',
                    'include_mako',
                    'show_resize_scroll',
                    'icon_size',
                    'search_key',
                }:
                    raise ValueError('Unsupported CustomLayout options')
                nodes.extend(
                    read_custom_layout(
                        options.get('search_key') or search_key,
                        view=options.get('view') or '',
                        html=options.get('html') or '',
                        include_mako=options.get('include_mako', True),
                        _depth=_depth + 1,
                        _behaviors=behaviors,
                    )['layoutNodes']
                )
            elif handler in (
                'tactic.ui.panel.TableLayoutWdg',
                'tactic.ui.panel.FastTableLayoutWdg',
                'tactic.ui.panel.ViewPanelWdg',
            ):
                allowed = {
                    'search_type',
                    'search_key',
                    'view',
                    'expression',
                    'show_search_limit',
                    'show_insert',
                    'show_row_select',
                    'show_select',
                    'show_gear',
                    'show_search',
                    'show_shelf',
                    'init_load_num',
                    'width',
                    'mode',
                    'search_view',
                    'simple_search_view',
                }
                if set(options) - allowed or not options.get('search_type'):
                    raise ValueError('Unsupported CustomLayout table options')
                if options.get('width') not in (None, '', '100%') or options.get(
                    'mode'
                ) not in (None, '', 'simple'):
                    raise ValueError(
                        'CustomLayout table must fill its native container'
                    )
                flags = (
                    'show_row_select',
                    'show_select',
                    'show_gear',
                    'show_insert',
                    'show_shelf',
                    'show_search',
                    'show_search_limit',
                )
                if any(
                    options.get(flag, '') not in ('', True, False, 'true', 'false')
                    for flag in flags
                ):
                    raise ValueError('Invalid CustomLayout table display flag')
                initial = str(options.get('init_load_num') or '50')
                if not initial.isdecimal() or not 1 <= int(initial) <= 100:
                    raise ValueError(
                        'CustomLayout initial page must contain one to one hundred rows'
                    )
                nodes.append(
                    dict(
                        kind='table',
                        text=attrs.get('title') or attrs.get('name') or 'Table View',
                        table=dict(
                            searchType=options['search_type'],
                            parentKey=options.get('search_key') or search_key,
                            view=options.get('view') or 'table',
                            expression=options.get('expression') or '',
                            projectScope=handler == 'tactic.ui.panel.ViewPanelWdg'
                            and not options.get('search_key'),
                            searchView=options.get('search_view') or '',
                            simpleSearchView=options.get('simple_search_view') or '',
                            embedded=True,
                            initialLimit=int(initial),
                            shelf=options.get('show_shelf') not in (False, 'false'),
                            search=options.get('show_search') not in (False, 'false'),
                            searchLimit=options.get('show_search_limit')
                            not in (False, 'false'),
                            selection=options.get(
                                'show_row_select', options.get('show_select')
                            )
                            not in (False, 'false'),
                            gear=options.get('show_gear') not in (False, 'false'),
                            insert=options.get('show_insert') not in (False, 'false'),
                        ),
                    )
                )
            elif handler in ('pyasm.widget.ThumbWdg', 'ThumbWdg'):
                from pyasm.widget import ThumbWdg

                widget = ThumbWdg(name=attrs.get('name') or 'preview', **options)
                widget.set_sobjects([obj])
                widget.preprocess()
                widget.set_current_index(0)
                value = (
                    widget.get_cell_value()
                    if hasattr(widget, 'get_cell_value')
                    else dict(image=widget.get_data(obj) or '')
                )
                nodes.append(
                    dict(
                        kind='preview',
                        text=str(obj.get_display_value()),
                        value=value,
                        javascript=behaviors.get(attrs.get('name'), ''),
                    )
                )
            else:
                raise ValueError(
                    'CustomLayout embedded widget is not migrated: ' + str(handler)
                )
        elif tag == 'a':
            source = next(
                (
                    behaviors[name]
                    for name in attrs.get('class', '').split()
                    if name in behaviors
                ),
                '',
            )
            nodes.append(
                dict(
                    kind='action' if source else 'link',
                    text=text(item).strip(),
                    href=attrs.get('href') or '',
                    javascript=source,
                )
            )
        elif tag in ('object', 'embed'):
            address = attrs.get('data') or attrs.get('src')
            if address:
                nodes.append(
                    dict(
                        kind='link',
                        text='Open external document',
                        href=address,
                        translate=True,
                    )
                )
        elif tag == 'img':
            nodes.append(
                dict(
                    kind='preview',
                    text=str(obj.get_display_value()),
                    value=dict(image=attrs.get('src') or ''),
                    size=300,
                )
            )
        elif tag == 'select':
            control = dict(
                selector=(attrs.get('class') or attrs.get('name') or '').split()[0],
                name=attrs.get('name') or '',
                kind='choice',
                options=[],
                value='',
            )
            if not control['selector']:
                raise ValueError('CustomLayout select requires a name')
            controls.append(control)
            nodes.append(control)
        elif tag == 'style':
            return
        elif tag in ('table', 'tr', 'td', 'th'):
            previous, nodes = nodes, []
            for child in item['children']:
                visit(child)
            children, nodes = nodes, previous
            nodes.append(
                dict(
                    kind='row' if tag == 'tr' else 'group',
                    children=children,
                    weight=int(attrs.get('colspan') or 1),
                    width=attrs.get('width') or '',
                )
            )
        elif tag in (
            'root',
            'html',
            'body',
            'div',
            'span',
            'p',
            'strong',
            'b',
            'small',
            'br',
            'hr',
            'h4',
            'form',
        ):
            if tag == 'form':
                form = attrs.get('name') or ''
            if attrs.get('class') and not text(item).strip():
                control = dict(kind='text', text='', selector=attrs['class'].split()[0])
                controls.append(control)
                nodes.append(control)
            for child in item['children']:
                visit(child)
        else:
            raise ValueError('CustomLayout markup is not migrated: ' + tag)

    visit(parser.root)
    return dict(
        text='',
        layoutNodes=nodes,
        targetSearchKey=search_key,
        layoutView=view,
        layoutControls=controls,
        layoutLoad=load_actions,
        layoutForm=form,
        layoutUser=Environment.get_security().get_user_name(),
        layoutRecord=dict(
            __search_key__=search_key,
            code=obj.get_code(),
            name=obj.get_value('name', no_exception=True),
            title=obj.get_value('title', no_exception=True),
        ),
        externalDocuments=any(node['kind'] == 'link' for node in nodes),
    )


def read_nested_scope(
    parent_key,
    search_type,
    view='table',
    expression='',
    offset=0,
    limit=50,
    filters=None,
    order_by=None,
    search_view='',
    project_scope=False,
    simple_view='',
    simple_values=None,
    keyword='',
    keyword_relation='EQI',
):
    """Self-contained original-server procedure; never return an unscoped table."""
    import re
    from pyasm.biz import Project, Snapshot
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType

    if not Environment.get_security().is_admin() and (
        not Environment.get_security().is_logged_in()
        or Environment.get_security().get_user_name() == 'admin'
        or not (
            Project.get_project_code() in ('admin', 'sthpw')
            or Environment.get_security().check_access(
                'project',
                [{'code': '*'}, {'code': Project.get_project_code()}],
                'allow',
                default='deny',
            )
        )
    ):
        raise PermissionError('Administration requires administrator access')
    if (
        type(offset) is not int
        or offset < 0
        or type(limit) is not int
        or not 1 <= limit <= 100
    ):
        raise ValueError('Invalid nested table page')
    if not isinstance(view, str) or not re.fullmatch(r'[A-Za-z_][\w.@-]{0,127}', view):
        raise ValueError('Invalid view name')
    if SearchKey.extract_project(parent_key) not in (
        None,
        '',
        Project.get_project_code(),
        'sthpw',
        'admin',
    ):
        raise ValueError('The configured table target belongs to another project')
    requested = SearchType.breakup_search_type(search_type)
    if requested.get('project') not in (
        None,
        '',
        Project.get_project_code(),
        'sthpw',
        'admin',
    ):
        raise ValueError('The nested table belongs to another project')
    base = SearchType.get(search_type).get_base_key()
    if base in ('sthpw/message', 'sthpw/message_log'):
        raise ValueError('Open private messages from Messages')
    if base.startswith(('prod/', 'flash/')):
        raise ValueError('The legacy production subsystem is excluded')
    parent = Search.get_by_search_key(parent_key)
    if parent is None:
        raise LookupError('Object is no longer available')
    if parent.get_base_search_type() in ('sthpw/message', 'sthpw/message_log'):
        raise ValueError('Open private messages from Messages')
    search = Search(search_type)
    if type(project_scope) is not bool or (project_scope and expression):
        raise ValueError('Invalid project table scope')
    if project_scope:
        if base.startswith(('sthpw/', 'config/')):
            raise ValueError('Project panels require a project-owned Search Type')
    elif base == 'sthpw/file' and view == 'snapshot_files' and not expression:
        # shortcut: directory packages remain file records; recursive disk browsing stays in File Workspace.
        snapshots = (
            [parent]
            if parent.get_base_search_type() == 'sthpw/snapshot'
            else Snapshot.get_by_sobject(parent, 'publish')
        )
        files = [
            file for snapshot in snapshots for file in snapshot.get_all_file_objects()
        ]
        search.add_filters('id', [file.get_id() for file in files] or [-1])
    elif (
        parent.get_base_search_type() == 'sthpw/project'
        and base in ('sthpw/task', 'sthpw/snapshot', 'sthpw/note', 'sthpw/work_hour')
        and not expression
    ):
        search.add_filter('project_code', parent.get_code())
    elif base == parent.get_base_search_type() and not expression:
        search.add_id_filter(parent.get_id())
    elif expression:
        # Only reads enter a nested table. Mutating expressions belong to actions.
        if not isinstance(expression, str) or not re.fullmatch(
            r'\s*@SOBJECT\([^@;{}]*\)\s*', expression, re.I
        ):
            raise ValueError('A nested table requires an @SOBJECT expression')
        records = Search.eval(expression, sobjects=parent)
        if not isinstance(records, (list, tuple)):
            records = [records] if records else []
        if len(records) > 10000 or any(
            item.get_base_search_type() != base for item in records
        ):
            raise ValueError('The nested expression returned an invalid scope')
        search.add_filters('id', [item.get_id() for item in records] or [-1])
    else:
        owner = parent.get_parent()
        if owner is not None and owner.get_base_search_type() == base:
            search.add_id_filter(owner.get_id())
        else:
            search.add_parent_filter(parent)
    columns = SearchType.get_column_info(base)
    simple_filters = []
    if simple_view:
        from xml.etree import ElementTree as ET
        from pyasm.search import WidgetDbConfig

        if not isinstance(simple_view, str) or not re.fullmatch(
            r'[A-Za-z_][\w.@-]{0,127}', simple_view
        ):
            raise ValueError('Invalid simple search view')
        config = WidgetDbConfig.get_by_search_type(search_type, simple_view)
        if config is not None:
            root = ET.fromstring(config.get_value('config'))
            for element in root.findall('./' + simple_view + '/element'):
                display = element.find('display')
                if display is None and element.get('name') == 'keywords':
                    continue  # The existing keyword field remains the native text-search control.
                if (
                    display is None
                    or display.get('class') != 'tactic.ui.filter.SelectFilterElementWdg'
                ):
                    raise ValueError('Simple search widget is not migrated')
                column, expression = (
                    (display.findtext('column') or '').strip(),
                    (display.findtext('values_expr') or '').strip(),
                )
                if not re.fullmatch(
                    r'(?:[A-Za-z_]\w*/[A-Za-z_]\w*\.)?[A-Za-z_]\w*', column
                ):
                    raise ValueError('Unsupported simple search relationship')
                if not re.fullmatch(
                    r'@GET\([A-Za-z_]\w*/[A-Za-z_]\w*\.[A-Za-z_]\w*\)', expression
                ):
                    raise ValueError(
                        'Simple search choices require a read-only field expression'
                    )
                from pyasm.common import Container
                from tactic_stream.server.api import check_record_access
                from tactic_stream.server.search_configuration import (
                    deny_expression_write,
                )

                previous_read = Container.get('Expression:check_record_access')
                previous_write = Container.get('Expression:check_method_access')
                Container.put('Expression:check_record_access', check_record_access)
                Container.put('Expression:check_method_access', deny_expression_write)
                try:
                    values = Search.eval(expression)
                finally:
                    Container.put('Expression:check_record_access', previous_read)
                    Container.put('Expression:check_method_access', previous_write)
                values = values if isinstance(values, list) else [values]
                values = list(
                    dict.fromkeys(str(value) for value in values if value is not None)
                )
                if len(values) > 1000:
                    raise ValueError('Simple search exceeds one thousand choices')
                simple_filters.append(
                    dict(
                        name=element.get('name'),
                        title=element.get('title') or element.get('name'),
                        column=column,
                        options=[dict(value=value, label=value) for value in values],
                    )
                )
    if (simple_values is not None and not isinstance(simple_values, dict)) or set(
        simple_values or {}
    ) - {item['name'] for item in simple_filters}:
        raise ValueError('Unknown simple search filter')
    for item in simple_filters:
        value = (simple_values or {}).get(item['name'], '')
        if not isinstance(value, str) or len(value) > 512:
            raise ValueError('Invalid simple search value')
        if value:
            if value not in [choice['value'] for choice in item['options']]:
                raise ValueError('The filter value is no longer available')
            related, separator, column = item['column'].rpartition('.')
            if separator:
                subset = Search(related)
                subset.add_filter(column, value)
                search.add_relationship_search_filter(subset)
            else:
                if column not in columns:
                    raise ValueError('Simple search column is no longer available')
                search.add_filter(column, value)
    if search_view:
        if not isinstance(search_view, str) or not re.fullmatch(
            r'[A-Za-z_][\w.:@-]{0,255}', search_view
        ):
            raise ValueError('Invalid search view name')
        try:
            from tactic_stream.server.search_configuration import (
                apply_filters,
                unpack_filters,
                validate_filters,
            )
        except ImportError:
            from tactic.ui.app import SearchWdg

            saved = Search(search_type)
            SearchWdg(
                search_type=search_type, view=search_view, display=True
            ).alter_search(saved)
            saved.add_column('id')
            search.add_search_filter('id', saved)
        else:
            from pyasm.search import WidgetDbConfig
            from pyasm.common import Container
            from tactic_stream.server.api import check_record_access
            from tactic_stream.server.search_configuration import deny_expression_write

            config = WidgetDbConfig.get_by_search_type(search_type, search_view)
            if config is None:
                raise ValueError('Search view is not available')
            conditions, packed = unpack_filters(config.get_value('config'))
            conditions = [row for row in conditions if row['column']]
            validate_filters(conditions, columns)
            previous_read = Container.get('Expression:check_record_access')
            previous_write = Container.get('Expression:check_method_access')
            Container.put('Expression:check_record_access', check_record_access)
            Container.put('Expression:check_method_access', deny_expression_write)
            try:
                # Keep saved OR conditions inside the mandatory parent scope.
                saved = Search(search_type)
                apply_filters(saved, conditions)
                saved.add_column('id')
                search.add_search_filter('id', saved)
            finally:
                Container.put('Expression:check_record_access', previous_read)
                Container.put('Expression:check_method_access', previous_write)
            if not order_by:
                order = next(
                    (
                        row.get('order', '')
                        for row in packed
                        if row.get('prefix') == 'group'
                    ),
                    '',
                )
                order_by = [part.strip() for part in order.split(',') if part.strip()]
    if not isinstance(filters or [], list) or len(filters or []) > 20:
        raise ValueError('Invalid nested table filters')
    for item in filters or []:
        if (
            not isinstance(item, (tuple, list))
            or len(item) != 3
            or item[0] not in columns
            or item[1] not in ('=', '!=', '<', '<=', '>', '>=', 'like', 'is empty', 'is not empty')
        ):
            raise ValueError('Invalid nested table filter')
        if item[1] in ('is empty', 'is not empty'):
            search.add_filter(item[0], 'NULL', op='is' if item[1] == 'is empty' else 'is not', quoted=False)
        else:
            search.add_filter(item[0], item[2], op=item[1])
    if not isinstance(keyword, str) or len(keyword) > 4096 or keyword_relation not in ('EQI', '='):
        raise ValueError('Invalid nested search text')
    primary = next((name for name in ('name', 'title', 'file_name', 'code', 'login') if name in columns), '')
    if keyword.strip():
        fields = [name for name in (primary, 'keywords', 'description') if name and name in columns]
        if not fields:
            raise ValueError('This Search Type has no searchable title')
        # Keep the normal suggestion OR group inside all mandatory scope conditions.
        matching = Search(search_type)
        matching.add_op_filters(['begin'] + [(name, keyword_relation, keyword.strip()) for name in fields] + ['or'])
        matching.add_column('id')
        search.add_search_filter('id', matching)
    if not isinstance(order_by or [], list) or len(order_by or []) > 4:
        raise ValueError('Invalid nested table ordering')
    for item in order_by or []:
        parts = str(item).split()
        if (
            not parts
            or len(parts) > 2
            or parts[0] not in columns
            or (len(parts) == 2 and parts[1].lower() not in ('asc', 'desc'))
        ):
            raise ValueError('Invalid nested table ordering')
        search.add_order_by(parts[0], parts[1] if len(parts) == 2 else 'asc')
    search.add_order_by('id')
    search.set_limit(limit + 1)
    search.set_offset(offset)
    records = search.get_sobjects()
    values = [item.get_sobject_dict() for item in records[:limit]]
    if base == 'sthpw/login':
        for record in values:
            record.pop('password', None)
    return dict(
        searchType=base,
        view=view,
        parentKey=parent_key,
        offset=offset,
        hasNext=len(records) > limit,
        simpleFilters=simple_filters,
        searchColumn=primary,
        records=values,
    )


def append_snapshot_files(search_key, action='prepare', expected_revision='',
                          filenames=None, file_type='attachment', keep_file_name=False,
                          upload_directory=''):
    """Self-contained procedure for Stream and an original TACTIC server."""
    import hashlib
    import json
    import os
    import re
    import uuid
    from pyasm.biz import Project, Snapshot
    from pyasm.checkin import FileAppendCheckin
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey

    if not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_admin() and (not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_logged_in() or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().get_user_name() == 'admin' or not (__import__('pyasm.biz', fromlist=['Project']).Project.get_project_code() in ('admin', 'sthpw') or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().check_access('project', [{'code': '*'}, {'code': __import__('pyasm.biz', fromlist=['Project']).Project.get_project_code()}], 'allow', default='deny'))):
        raise PermissionError('Administration requires administrator access')
    if action not in ('prepare', 'save'):
        raise ValueError('Invalid snapshot append action')
    if SearchKey.extract_base_search_type(search_key) != 'sthpw/snapshot':
        raise ValueError('Append files requires a snapshot')
    snapshot = Search.get_by_search_key(search_key)
    if snapshot is None:
        raise LookupError('Snapshot is no longer available')
    if snapshot.get_value('project_code') != Project.get_project_code():
        raise ValueError('Open the snapshot in its own project before attaching files')
    alias_version = int(snapshot.get_value('version'))
    if alias_version <= 0:
        if action != 'prepare':
            raise ValueError('Reload the concrete snapshot version before attaching files')
        parent = snapshot.get_sobject()
        if parent is None:
            raise LookupError('Snapshot owner is no longer available')
        snapshot = Snapshot.get_snapshot(parent.get_search_type(), parent.get_code() or parent.get_id(),
            context=snapshot.get_value('context'), version=alias_version, revision=-1,
            level_type=snapshot.get_value('level_type'), level_id=snapshot.get_value('level_id'),
            process=snapshot.get_value('process') or None, use_cache=False, level_parent_search=False)
        if snapshot is None or int(snapshot.get_value('version')) <= 0:
            raise LookupError('No concrete snapshot version is available')
    if action == 'save':
        sql = snapshot.get_sql()
        lock = getattr(sql.get_database_impl(), 'lock_collection_table', None)
        if lock:
            lock(sql, 'snapshot')
        elif sql.get_database_type() == 'PostgreSQL':
            sql.do_update('LOCK TABLE "snapshot" IN EXCLUSIVE MODE')
        else:
            raise ValueError('Snapshot revisions require a transactional database lock')
        snapshot = Search.get_by_search_key(snapshot.get_search_key())
        if snapshot is None:
            raise LookupError('Snapshot is no longer available')
        if snapshot.get_value('project_code') != Project.get_project_code():
            raise ValueError('Open the snapshot in its own project before attaching files')
    files = snapshot.get_all_file_objects()
    revision = hashlib.sha256(json.dumps([snapshot.get_data(), sorted(
        (item.get_data() for item in files), key=lambda item: str(item.get('code') or item.get('id')))],
        sort_keys=True, default=str).encode()).hexdigest()
    existing = [str(item.get_value('file_name') or '') for item in files]
    if action == 'prepare':
        parent = snapshot.get_sobject()
        if parent is None:
            raise LookupError('Snapshot owner is no longer available')
        return dict(searchKey=snapshot.get_search_key(), snapshotCode=snapshot.get_code(),
            version=snapshot.get_value('version'), expectedRevision=revision, existingNames=existing,
            uploadDirectory='append_' + uuid.uuid4().hex,
            ownerKey=parent.get_search_key(), ownerTitle=str(parent.get_display_value()),
            context=snapshot.get_value('context'), process=snapshot.get_value('process') or
            str(snapshot.get_value('context') or '').split('/')[0])
    if not expected_revision or revision != expected_revision:
        raise ValueError('Snapshot changed. Reload before attaching files.')
    if not isinstance(filenames, list) or not 1 <= len(filenames) <= 50:
        raise ValueError('Choose between one and 50 files')
    if not isinstance(file_type, str) or not file_type.strip() or len(file_type) > 128 or any(
            ord(character) < 32 for character in file_type):
        raise ValueError('Choose a valid file type')
    if type(keep_file_name) is not bool:
        raise ValueError('Invalid keep-file-name option')
    if not isinstance(upload_directory, str) or not re.fullmatch(r'append_[a-f0-9]{32}', upload_directory):
        raise ValueError('Reload the attachment session before uploading files')
    names, paths = set(), []
    upload_root = os.path.realpath(Environment.get_upload_dir())
    directory = os.path.realpath(os.path.join(upload_root, upload_directory))
    if os.path.normcase(os.path.commonpath([directory, upload_root])) != os.path.normcase(upload_root):
        raise ValueError('Uploaded files must remain in the ticket upload directory')
    for name in filenames:
        if not isinstance(name, str) or name in ('', '.', '..') or any(
                character in name for character in ('/', '\\', ':', '\x00')) or any(
                ord(character) < 32 for character in name):
            raise ValueError('Uploaded files must be named without directory paths')
        folded = name.casefold()
        if folded in names or folded in {value.casefold() for value in existing}:
            raise ValueError('Choose file names that are not already in the snapshot')
        names.add(folded)
        path = os.path.realpath(os.path.join(directory, name))
        if os.path.normcase(os.path.commonpath([path, directory])) != os.path.normcase(directory) or not os.path.isfile(path):
            raise ValueError('Uploaded file is unavailable: ' + name)
        paths.append(path)
    # All names, the complete revision and ticket-owned uploads are checked before a write.
    checkin = FileAppendCheckin(snapshot.get_code(), paths, [file_type.strip()] * len(paths),
        mode='create', keep_file_name=keep_file_name, source_paths=list(filenames))
    checkin.execute()
    return dict(state='saved', searchKey=checkin.get_snapshot().get_search_key())


def read_snapshot_files(search_key, file_code='', expected_revision=''):
    """Read a captured concrete snapshot using only original server methods."""
    import json
    import hashlib
    import os
    from pyasm.biz import FileGroup, FileRange, Project, Snapshot
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey

    if not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_admin() and (not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_logged_in() or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().get_user_name() == 'admin' or not (__import__('pyasm.biz', fromlist=['Project']).Project.get_project_code() in ('admin', 'sthpw') or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().check_access('project', [{'code': '*'}, {'code': __import__('pyasm.biz', fromlist=['Project']).Project.get_project_code()}], 'allow', default='deny'))):
        raise PermissionError('Administration requires administrator access')
    if SearchKey.extract_base_search_type(search_key) != 'sthpw/snapshot':
        raise ValueError('Check out requires a snapshot')
    snapshot = Search.get_by_search_key(search_key)
    if snapshot is None:
        raise LookupError('Snapshot is no longer available')
    if snapshot.get_value('project_code') != Project.get_project_code():
        raise ValueError('Open the snapshot in its own project before checking out files')
    if SearchKey.extract_base_search_type(snapshot.get_value('search_type') or '') in ('sthpw/message', 'sthpw/message_log'):
        raise ValueError('Download private message attachments from Messages')
    version = int(snapshot.get_value('version'))
    if version <= 0:
        parent = snapshot.get_sobject()
        if parent is None:
            raise LookupError('Snapshot owner is no longer available')
        snapshot = Snapshot.get_snapshot(parent.get_search_type(), parent.get_code() or parent.get_id(),
            context=snapshot.get_value('context'), version=version, revision=-1,
            level_type=snapshot.get_value('level_type'), level_id=snapshot.get_value('level_id'),
            process=snapshot.get_value('process') or None, use_cache=False, level_parent_search=False)
        if snapshot is None or int(snapshot.get_value('version')) <= 0:
            raise LookupError('No concrete snapshot version is available')
    if snapshot.get_value('project_code') != Project.get_project_code():
        raise ValueError('Open the snapshot in its own project before checking out files')
    if expected_revision and hashlib.sha256(json.dumps(snapshot.get_data(), sort_keys=True, default=str).encode()).hexdigest() != expected_revision:
        raise ValueError('Dependencies changed. Reload this snapshot.')
    files = snapshot.get_all_file_objects()
    if file_code:
        files = [file for file in files if file.get_code() == file_code]
        if len(files) != 1:
            raise LookupError('Dependency file is no longer available')
    rows = []
    for file in files:
        row = file.get_sobject_dict()
        meta = file.get_metadata_dict()
        file_range = str(file.get_value('file_range', no_exception=True) or '').strip()
        template = str(meta.get('new_template') or meta.get('template') or '').strip()
        group_type = str(meta.get('type') or '').strip()
        if file_range or (template and group_type not in ('', 'file', 'layer_file', 'no_ext')):
            if file_code:
                raise ValueError('Sequence and UDIM files require Snapshot Checkout')
            name = file.get_full_file_name()
            names = []
            if file_range:
                rng = FileRange.get(file_range)
                if rng.get_num_frames() > 5000:
                    raise ValueError('Sequence or UDIM group exceeds the checkout limit')
                names = FileGroup.expand_paths(name, rng)
            else:
                stem, suffix = os.path.splitext(name)
                base = str(meta.get('new_filename') or meta.get('filename') or stem)
                ext = str(meta.get('new_file_ext') or meta.get('ext') or suffix.lstrip('.'))
                layer = str(meta.get('layer') or '')
                pad = int(meta.get('new_padding') or meta.get('padding') or 4)
                render = lambda udim='', frame=None: (template
                    .replace('$FILENAME', base).replace('$LAYER', layer)
                    .replace('$UDIM', str(udim)).replace('$UV', str(udim))
                    .replace('$FRAME', '' if frame is None else str(frame).zfill(pad))
                    .replace('$EXT', ext))
                parse_span = lambda item: (int(item[0]), int(item[1])) if isinstance(item, (list, tuple)) else [int(part) for part in str(item).split('-')]
                if group_type in ('sequence', 'layer_sequence'):
                    for item in meta.get('frameranges') or []:
                        start, end = parse_span(item)
                        if end < start or len(names) + (end - start + 1) > 5000:
                            raise ValueError('Sequence or UDIM group exceeds the checkout limit')
                        names.extend(render(frame=frame) for frame in range(start, end + 1))
                elif group_type in ('udim', 'uv', 'layer_udim', 'layer_uv'):
                    for udim in meta.get('udims') or []:
                        if len(names) + 1 > 5000:
                            raise ValueError('Sequence or UDIM group exceeds the checkout limit')
                        names.append(render(udim=udim))
                elif group_type in ('udim_sequence', 'uv_sequence', 'layer_udim_sequence', 'layer_uv_sequence'):
                    for pair in meta.get('frameranges') or []:
                        udim, ranges = pair[0], pair[1]
                        for item in ranges or []:
                            start, end = parse_span(item)
                            if end < start or len(names) + (end - start + 1) > 5000:
                                raise ValueError('Sequence or UDIM group exceeds the checkout limit')
                            names.extend(render(udim=udim, frame=frame) for frame in range(start, end + 1))
            if not names or len(set(names)) != len(names):
                raise ValueError('Sequence or UDIM group has no valid member files')
            sizes = meta.get('files_sizes') or []
            row['__member_files__'] = [
                dict(file_name=member, st_size=int(sizes[idx] or 0) if idx < len(sizes) else 0)
                for idx, member in enumerate(names)
            ]
        rows.append(row)
    data = snapshot.get_sobject_dict()
    data['__files__'] = rows
    return json.loads(json.dumps(data, default=str))


def read_connection_cells(search_keys, direction='dst', icon_size=60):
    import hashlib
    import json
    from pyasm.biz import Project, SObjectConnection
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey
    from pyasm.widget import ThumbWdg

    if not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_admin() and (not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_logged_in() or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().get_user_name() == 'admin' or not (__import__('pyasm.biz', fromlist=['Project']).Project.get_project_code() in ('admin', 'sthpw') or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().check_access('project', [{'code': '*'}, {'code': __import__('pyasm.biz', fromlist=['Project']).Project.get_project_code()}], 'allow', default='deny'))):
        raise PermissionError('Administration requires administrator access')
    if direction not in ('src', 'dst'):
        raise ValueError('Invalid connection direction')
    if type(icon_size) is not int or not 16 <= icon_size <= 256:
        raise ValueError('Invalid connection icon size')
    if not isinstance(search_keys, list) or len(search_keys) > 500:
        raise ValueError('Invalid connection table scope')
    project = Project.get_project_code()
    for key in search_keys:
        if not isinstance(key, str) or SearchKey.extract_project(key) not in (None, '', 'sthpw', 'admin', project):
            raise ValueError('The configured table target belongs to another project')
    parents = Search.get_by_search_keys(search_keys, keep_order=True)
    if len(parents) != len(search_keys) or any(parent is None for parent in parents):
        raise LookupError('Object is no longer available')
    private_types = ('sthpw/message', 'sthpw/message_log')
    if any(parent.get_base_search_type() in private_types for parent in parents):
        raise ValueError('Open private messages from Messages')
    grouped = {}
    connections = {}
    result = {}
    for parent in parents:
        key = parent.get_search_key()
        result[key] = dict(text='', targetSearchKey=key, direction=direction, iconSize=icon_size, connectionRows=[])
        if parent.get_base_search_type() == 'sthpw/connection':
            if parent.get_value('project_code') == project:
                connections[key] = [(parent, direction)]
        else:
            grouped.setdefault(parent.get_search_type(), []).append(parent)
    for search_type, group in grouped.items():
        query = Search(SObjectConnection)
        query.add_filter('project_code', project)
        query.add_filter(direction + '_search_type', search_type)
        query.add_filters(direction + '_search_id', [parent.get_id() for parent in group])
        by_id = {parent.get_id(): parent.get_search_key() for parent in group}
        for connection in query.get_sobjects():
            key = by_id[connection.get_value(direction + '_search_id')]
            connections.setdefault(key, []).append((connection, 'src' if direction == 'dst' else 'dst'))
    target_groups = {}
    for group in connections.values():
        for connection, endpoint in group:
            search_type = connection.get_value(endpoint + '_search_type')
            if SearchKey.extract_base_search_type(search_type) in private_types:
                raise ValueError('Open private messages from Messages')
            target_groups.setdefault(search_type, set()).add(connection.get_value(endpoint + '_search_id'))
    targets = {}
    for search_type, identities in target_groups.items():
        for target in Search.get_by_id(search_type, list(identities)):
            targets[(search_type, target.get_id())] = target
    thumbs = list({target.get_search_key(): target for target in targets.values()}.values())
    thumb = ThumbWdg(name='preview')
    thumb.set_sobjects(thumbs)
    thumb.preprocess()
    previews = {}
    for index, target in enumerate(thumbs):
        thumb.set_current_index(index)
        if hasattr(thumb, 'get_cell_value'):
            previews[target.get_search_key()] = thumb.get_cell_value()
        else:
            from urllib.parse import unquote, urlsplit
            link = thumb.get_data(target) or ''
            image = thumb.info.get('icon') or thumb.info.get('web') or link
            if urlsplit(image).path.lower().rsplit('.', 1)[-1] not in ('png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'avif'):
                image = ''
            previews[target.get_search_key()] = dict(image=image, text=link,
                filename=unquote(urlsplit(link).path.rsplit('/', 1)[-1]))
    for parent_key, group in connections.items():
        for connection, endpoint in group:
            target = targets.get((connection.get_value(endpoint + '_search_type'), connection.get_value(endpoint + '_search_id')))
            revision = hashlib.sha256(json.dumps(connection.get_data(), sort_keys=True, default=str).encode()).hexdigest()
            row = dict(connectionKey=connection.get_search_key(), expectedRevision=revision, available=target is not None)
            if target is not None:
                target_key = target.get_search_key()
                row.update(searchKey=target_key, code=target.get_code(),
                    name=target.get_value('name', no_exception=True) or target.get_display_value(),
                    description=target.get_value('title', no_exception=True) or target.get_value('description', no_exception=True) or '',
                    keywords=target.get_value('keywords', no_exception=True) or '',
                    retired=target.is_retired(), preview=previews[target_key])
            result[parent_key]['connectionRows'].append(row)
    return result


def remove_connection(parent_key, connection_key, expected_revision, direction='dst'):
    import hashlib
    import json
    from pyasm.biz import Project
    from pyasm.common import Environment, UserException
    from pyasm.search import Search, SearchKey

    if not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_admin() and (not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_logged_in() or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().get_user_name() == 'admin' or not (__import__('pyasm.biz', fromlist=['Project']).Project.get_project_code() in ('admin', 'sthpw') or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().check_access('project', [{'code': '*'}, {'code': __import__('pyasm.biz', fromlist=['Project']).Project.get_project_code()}], 'allow', default='deny'))):
        raise PermissionError('Administration requires administrator access')
    if direction not in ('src', 'dst'):
        raise ValueError('Invalid connection direction')
    if not isinstance(parent_key, str) or SearchKey.extract_project(parent_key) not in (None, '', 'sthpw', 'admin', Project.get_project_code()):
        raise ValueError('The configured table target belongs to another project')
    if not isinstance(connection_key, str) or SearchKey.extract_base_search_type(connection_key) != 'sthpw/connection':
        raise ValueError('Select a connection before removing it')
    if not isinstance(expected_revision, str) or not expected_revision or len(expected_revision) > 128:
        raise ValueError('Reload the connection before removing it')
    selected = Search.get_by_search_key(connection_key)
    parent = Search.get_by_search_key(parent_key)
    if parent is None and not (selected is None and SearchKey.extract_base_search_type(parent_key) == 'sthpw/connection'):
        raise LookupError('Object is no longer available')
    private_types = ('sthpw/message', 'sthpw/message_log')
    if parent is not None and parent.get_base_search_type() in private_types:
        raise ValueError('Open private messages from Messages')
    removed = dict(state='removed', parentKey=parent_key, connectionKey=connection_key)
    if selected is None:
        return removed
    if selected.get_value('project_code') != Project.get_project_code():
        raise ValueError('The connection belongs to another project')
    sql = selected.get_sql()
    lock = getattr(sql.get_database_impl(), 'lock_collection_table', None)
    if lock:
        lock(sql, 'connection')
    elif sql.get_database_type() == 'PostgreSQL':
        sql.do_update('LOCK TABLE "connection" IN EXCLUSIVE MODE')
    else:
        raise ValueError('Connection revisions require a transactional database lock')
    # Identity reads can retain the pre-lock object in the request cache.
    fresh = Search('sthpw/connection')
    fresh.add_id_filter(selected.get_id())
    selected = fresh.get_sobject()
    if selected is None:
        return removed
    if selected.get_value('project_code') != Project.get_project_code():
        raise ValueError('The connection belongs to another project')
    if any(SearchKey.extract_base_search_type(selected.get_value(endpoint + '_search_type')) in private_types for endpoint in ('src', 'dst')):
        raise ValueError('Open private messages from Messages')
    if parent.get_base_search_type() == 'sthpw/connection':
        belongs = parent.get_id() == selected.get_id()
    else:
        belongs = (selected.get_value(direction + '_search_type') == parent.get_search_type()
            and selected.get_value(direction + '_search_id') == parent.get_id())
    revision = hashlib.sha256(json.dumps(selected.get_data(), sort_keys=True, default=str).encode()).hexdigest()
    if not belongs or revision != expected_revision:
        raise UserException('Connection changed. Reload before removing it.')
    selected.delete()
    return removed


def read_dependency_node(search_key, offset=0, limit=50, expected_revision='', file_index=None):
    import hashlib
    import json
    from pyasm.biz import FileGroup, FileRange, Project, Snapshot, SObjectNotFoundException
    from pyasm.common import Environment, UserException, Xml
    from pyasm.search import Search, SearchKey

    if not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_admin() and (not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_logged_in() or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().get_user_name() == 'admin' or not (__import__('pyasm.biz', fromlist=['Project']).Project.get_project_code() in ('admin', 'sthpw') or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().check_access('project', [{'code': '*'}, {'code': __import__('pyasm.biz', fromlist=['Project']).Project.get_project_code()}], 'allow', default='deny'))):
        raise PermissionError('Administration requires administrator access')
    project = Project.get_project_code()
    if not isinstance(search_key, str) or SearchKey.extract_project(search_key) not in (None, '', 'sthpw', 'admin', project):
        raise ValueError('Open dependencies in the source project')
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError('Invalid dependency page')
    if file_index is not None and (type(file_index) is not int or file_index < 0):
        raise ValueError('Invalid dependency file')

    def check_type(search_type):
        base = SearchKey.extract_base_search_type(search_type)
        if base in ('sthpw/message', 'sthpw/message_log') or base.startswith(('prod/', 'flash/')):
            raise ValueError('This object is not available in Dependencies')
        return base

    def owner(value):
        try:
            return value.get_sobject()
        except SObjectNotFoundException:
            return None

    def concrete(value, source_project=project):
        check_type(value.get_value('search_type'))
        if value.get_value('project_code') != source_project:
            raise ValueError('Open dependencies in the snapshot project')
        if int(value.get_value('version')) > 0:
            return value
        parent = owner(value)
        if parent is None:
            raise LookupError('Snapshot owner is no longer available')
        result = Snapshot.get_snapshot(
            parent.get_search_type(), parent.get_code() or parent.get_id(),
            context=value.get_value('context'), version=int(value.get_value('version')), revision=-1,
            level_type=value.get_value('level_type'), level_id=value.get_value('level_id'),
            process=value.get_value('process') or None, use_cache=False, level_parent_search=False)
        if result is None or int(result.get_value('version')) <= 0:
            raise LookupError('No concrete snapshot version is available')
        return result

    def revision(value):
        return hashlib.sha256(json.dumps(value.get_data(), sort_keys=True, default=str).encode()).hexdigest()

    source = Search.get_by_search_key(search_key)
    if source is None:
        raise LookupError('Object is no longer available')
    source_type = check_type(source.get_search_type())
    snapshot = source if source_type == 'sthpw/snapshot' else Snapshot.get_latest(source.get_search_type(), source.get_id())
    if snapshot is None:
        return dict(title='Dependencies', identity=source.get_display_value(), rows=[], hasNext=False, message='No snapshot found')
    snapshot = concrete(snapshot)
    current = revision(snapshot)
    if expected_revision and expected_revision != current:
        raise UserException('Dependencies changed. Reload this snapshot.')
    xml = snapshot.get_snapshot_xml()
    files = xml.get_nodes('snapshot/file')
    result = dict(title='Dependencies', identity=snapshot.get_code(), snapshotKey=snapshot.get_search_key(),
        projectCode=project, version=snapshot.get_value('version'), context=snapshot.get_value('context'),
        revision=current, offset=offset)
    parent = owner(snapshot)
    result['owner'] = dict(searchKey=parent.get_search_key(), title=parent.get_display_value()) if parent else None
    if file_index is not None:
        if file_index >= len(files):
            raise LookupError('Dependency file is no longer available')
        file_node = files[file_index]
        file_range = FileRange.get(Xml.get_attribute(file_node, 'file_range'))
        start, end, step = file_range.get_values()
        if step <= 0 or start > end:
            raise ValueError('Invalid dependency file range')
        count = (end - start) // step + 1
        # Expand only this page, even if the snapshot contains millions of frames.
        first, last = start + offset * step, min(end, start + (offset + limit - 1) * step)
        paths = FileGroup.expand_paths(Xml.get_attribute(file_node, 'name'), FileRange(first, last, step)) if first <= end else []
        result.update(rows=[dict(key=str(offset + index), kind='member', title=path, group='Files')
            for index, path in enumerate(paths)], hasNext=offset + len(paths) < count)
        return result
    nodes = []
    for group, path in (
            ('Files', 'snapshot/file'), ('Upstream', 'snapshot/ref'), ('Inputs', 'snapshot/input_ref'),
            ('Downstream', 'snapshot/fref'), ('File references', 'snapshot/file/ref'),
            ('Unresolved references', 'snapshot/unknown_ref')):
        nodes.extend((group, node) for node in xml.get_nodes(path))
    rows = []
    for index, (group, node) in enumerate(nodes[offset:offset + limit], offset):
        row = dict(key=str(index), group=group, kind='reference')
        if group == 'Files':
            row.update(kind='file', fileCode=Xml.get_attribute(node, 'file_code'), filename=Xml.get_attribute(node, 'name'),
                fileType=Xml.get_attribute(node, 'type'), fileRange=Xml.get_attribute(node, 'file_range'),
                fileIndex=index, snapshotKey=snapshot.get_search_key(), projectCode=project)
        elif group == 'Unresolved references':
            row.update(kind='missing', title=Xml.get_attribute(node, 'path'))
        else:
            row.update(instance=Xml.get_attribute(node, 'instance'), node=(Xml.get_attribute(node, 'node') or '')[:100])
            if group == 'File references':
                row['origin'] = Xml.get_attribute(Xml.get_parent(node), 'name')
            code = Xml.get_attribute(node, 'snapshot_code')
            # Legacy code-only nodes have no numeric search_id for the contextual resolver.
            target = Snapshot.get_by_code(code, show_retired=True) if code and not Xml.get_attribute(node, 'level_type') else Snapshot.get_ref_snapshot_by_node(node, show_retired=True)
            if target is None:
                row.update(kind='missing', title=code or Xml.get_attribute(node, 'search_code') or Xml.get_attribute(node, 'search_id'))
            else:
                check_type(target.get_value('search_type'))
                target_project = target.get_value('project_code')
                target = concrete(target, target_project)
                parent = owner(target)
                row.update(snapshotKey=target.get_search_key(), projectCode=target_project,
                    version=target.get_value('version'), context=target.get_value('context'),
                    parentType=SearchKey.extract_base_search_type(target.get_value('search_type')),
                    parentCode=parent.get_code() if parent else '', ownerMissing=parent is None,
                    current=bool(target.is_current()), retired=target.is_retired(), revision=revision(target))
        rows.append(row)
    result.update(rows=rows, hasNext=len(nodes) > offset + limit)
    return result


def read_parent_cells(search_keys):
    """Self-contained read for Stream and Handler's original-server fallback."""
    import hashlib
    import json
    from pyasm.biz import Project
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType
    from pyasm.widget import ThumbWdg

    if not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_admin() and (not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_logged_in() or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().get_user_name() == 'admin' or not (__import__('pyasm.biz', fromlist=['Project']).Project.get_project_code() in ('admin', 'sthpw') or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().check_access('project', [{'code': '*'}, {'code': __import__('pyasm.biz', fromlist=['Project']).Project.get_project_code()}], 'allow', default='deny'))):
        raise PermissionError('Administration requires administrator access')
    if not isinstance(search_keys, list) or len(search_keys) > 500:
        raise ValueError('Invalid parent table scope')
    project = Project.get_project_code()

    def check_type(search_type):
        base = SearchKey.extract_base_search_type(search_type)
        if base in ('sthpw/message', 'sthpw/message_log', 'sthpw/ticket') or base.startswith(('prod/', 'flash/')):
            raise ValueError('This object is not available in parent groups')
        metadata = SearchType.get(base, no_exception=True)
        if metadata is None:
            return False
        if str(metadata.get_value('class_name') or '').startswith('pyasm.prod.'):
            raise ValueError('This object is not available in parent groups')
        if hasattr(metadata, 'get_record_read_options') and metadata.get_record_read_options().get('command'):
            raise ValueError('This object is not available in parent groups')
        return True

    for key in search_keys:
        if not isinstance(key, str) or SearchKey.extract_project(key) not in (None, '', 'sthpw', 'admin', project):
            raise ValueError('The configured table target belongs to another project')
        check_type(key)
    objects = Search.get_by_search_keys(search_keys, keep_order=True)
    if len(objects) != len(search_keys) or any(obj is None for obj in objects):
        raise LookupError('Object is no longer available')
    parents, cells = {}, {}
    for obj in objects:
        key = obj.get_search_key()
        own_project = obj.get_value('project_code', no_exception=True) or SearchKey.extract_project(key) or project
        parent_type = obj.get_value('search_type', no_exception=True)
        requested_key = ''
        if parent_type:
            registered = check_type(parent_type)
            # Old global records can store a bare type; their project belongs to the row.
            if not SearchKey.extract_project(parent_type):
                parent_type = SearchType.build_search_type(parent_type, own_project)
            code = obj.get_value('search_code', no_exception=True)
            identity = code or obj.get_value('search_id', no_exception=True)
            parent = None
            if identity not in (None, '', -1, '-1'):
                requested_key = SearchKey.build_search_key(parent_type, identity, column='code' if code else 'id')
                if registered:
                    parent = Search.get_by_search_key(requested_key)
        else:
            parent = obj.get_parent()
        cell = dict(text='', projectCode=own_project, targetSearchKey=key, sourceId=str(obj.get_id()),
            sourceRevision=hashlib.sha256(json.dumps(obj.get_data(), sort_keys=True, default=str).encode()).hexdigest(),
            groupKey='missing:' + requested_key if requested_key else 'no-parent', parent=None)
        if parent is not None:
            check_type(parent.get_search_type())
            parent_key = parent.get_search_key()
            record = {name: parent.get_value(name, no_exception=True) for name in
                ('id', 'code', 'name', 'title', 'description', 'project_code', 'pipeline_code', 'process', 'context')}
            record['__search_key__'] = parent_key
            cell.update(text=parent.get_code() or str(parent.get_id()), groupKey=parent_key,
                parent=dict(searchKey=parent_key, code=parent.get_code() or '',
                    name=parent.get_value('name', no_exception=True) or '',
                    description=parent.get_value('description', no_exception=True) or '',
                    retired=parent.is_retired(), record=record))
            parents[parent_key] = parent
        elif requested_key:
            cell['missingParentKey'] = requested_key
        cells[key] = cell
    records = list(parents.values())
    thumb = ThumbWdg(name='preview', latest_icon='true')
    thumb.set_sobjects(records)
    thumb.preprocess()
    previews = {}
    for index, parent in enumerate(records):
        thumb.set_current_index(index)
        if hasattr(thumb, 'get_cell_value'):
            preview = thumb.get_cell_value()
        else:
            from urllib.parse import urlsplit
            link = thumb.get_data(parent) or ''
            image = thumb.info.get('icon') or thumb.info.get('web') or link
            if urlsplit(image).path.lower().rsplit('.', 1)[-1] not in ('png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'avif'):
                image = ''
            preview = dict(image=image, text=link)
        previews[parent.get_search_key()] = preview
    for cell in cells.values():
        if cell['parent']:
            cell['parent']['preview'] = previews[cell['groupKey']]
    return cells


def edit_parent_group(search_key, view, column, action='prepare', source_revision='',
                      expected_revision='', parent_type='', query='', offset=0,
                      parent_key='', parent_revision='', source_id=None):
    """Self-contained procedure for both clients; writes join the caller's Command."""
    import hashlib
    import json
    import re
    from pyasm.biz import Project
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType
    from pyasm.widget import WidgetConfigView

    if not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_admin() and (not __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().is_logged_in() or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().get_user_name() == 'admin' or not (__import__('pyasm.biz', fromlist=['Project']).Project.get_project_code() in ('admin', 'sthpw') or __import__('pyasm.common', fromlist=['Environment']).Environment.get_security().check_access('project', [{'code': '*'}, {'code': __import__('pyasm.biz', fromlist=['Project']).Project.get_project_code()}], 'allow', default='deny'))):
        raise PermissionError('Administration requires administrator access')
    if action not in ('prepare', 'candidates', 'save', 'check'):
        raise ValueError('Invalid parent operation')
    if any(not isinstance(value, str) or not value for value in (search_key, view, column)):
        raise ValueError('Choose a configured parent column')
    if not re.fullmatch(r'[A-Za-z_][\w.@-]{0,127}', view) or len(column) > 256:
        raise ValueError('Choose a configured parent column')
    if not isinstance(query, str) or len(query) > 200 or type(offset) is not int or offset < 0:
        raise ValueError('Invalid parent search')
    project = Project.get_project_code()

    def check_key(key):
        if not isinstance(key, str) or not key or SearchKey.extract_project(key) not in (None, '', 'sthpw', 'admin', project):
            raise ValueError('The parent belongs to another project')
        base = SearchKey.extract_base_search_type(key)
        if base in ('sthpw/message', 'sthpw/message_log', 'sthpw/ticket') or base.startswith(('prod/', 'flash/')):
            raise ValueError('This object is not available in parent groups')
        metadata = SearchType.get(base)
        if str(metadata.get_value('class_name') or '').startswith('pyasm.prod.'):
            raise ValueError('This object is not available in parent groups')
        if hasattr(metadata, 'get_record_read_options') and metadata.get_record_read_options().get('command'):
            raise ValueError('This object is not available in parent groups')
        return base

    def revision(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

    def parent_of(record, missing_ok=False):
        from pyasm.search import SearchException
        related = record.get_value('search_type', no_exception=True)
        if not related:
            return record.get_parent()
        try:
            check_key(related)
        except SearchException:
            if missing_ok:
                return None
            raise LookupError('Parent is no longer available')
        if not SearchKey.extract_project(related):
            related = SearchType.build_search_type(related, record.get_value('project_code', no_exception=True) or project)
        code = record.get_value('search_code', no_exception=True)
        identity = code or record.get_value('search_id', no_exception=True)
        if identity in (None, '', -1, '-1'):
            return None
        return Search.get_by_search_key(SearchKey.build_search_key(related, identity, column='code' if code else 'id'))

    base = check_key(search_key)
    obj = Search.get_by_search_key(search_key)
    if obj is None:
        raise LookupError('Object is no longer available')
    if source_id is not None and str(source_id) != str(obj.get_id()):
        raise LookupError('Object is no longer available')
    if action == 'save':
        sql = obj.get_sql()
        table = SearchType.get(base).get_table()
        lock = getattr(sql.get_database_impl(), 'lock_collection_table', None)
        if lock:
            lock(sql, table)
        elif sql.get_database_type() == 'PostgreSQL':
            sql.do_update('LOCK TABLE "%s" IN EXCLUSIVE MODE' % table.replace('"', '""'))
        else:
            raise ValueError('Parent revisions require a transactional database lock')
    fresh = Search(obj.get_search_type())
    fresh.add_id_filter(obj.get_id())
    obj = fresh.get_sobject()
    if obj is None:
        raise LookupError('Object is no longer available')
    if source_id is not None and str(source_id) != str(obj.get_id()):
        raise LookupError('Object is no longer available')
    if obj.get_value('project_code', no_exception=True) not in (None, '', project):
        raise ValueError('Open parent editing in the source project')
    config = WidgetConfigView.get_by_search_type(base, view, use_cache=False)
    if column not in config.get_element_names() or config.get_action_handler(column) not in (
            'ParentGroupAction', 'tactic.ui.table.ParentGroupAction', 'tactic.ui.table.group_element_wdg.ParentGroupAction'):
        raise ValueError('The configured parent action changed. Reload before saving.')
    if config.get_action_options(column):
        raise ValueError('Unsupported parent action options')
    definition = [config.get_display_handler(column), config.get_display_options(column),
                  config.get_action_handler(column), config.get_action_options(column)]
    current = revision([obj.get_data(), definition])
    if action == 'prepare' and source_revision and revision(obj.get_data()) != source_revision:
        raise ValueError('Parent changed. Reload before saving.')
    parent = parent_of(obj, missing_ok=True)
    current_key = parent.get_search_key() if parent else ''
    schema = obj.get_schema()

    def allowed_type(value):
        target = check_key(value)
        declared = schema.get_parent_type(base)
        if declared not in ('*', target):
            raise ValueError('The configured parent relationship is unavailable')
        if schema.get_relationship(base, target) not in (
                'search_type', 'search_code', 'search_id', 'foreign_key', 'code', 'id', 'parent_code', 'search_key'):
            raise ValueError('The configured parent relationship is unavailable')
        return target

    def candidate(record):
        return dict(searchKey=record.get_search_key(), code=record.get_code() or '',
            title=record.get_value('name', no_exception=True) or record.get_value('title', no_exception=True)
                or record.get_code() or str(record.get_id()), retired=record.is_retired(), revision=revision(record.get_data()))

    if action == 'prepare':
        types = {}
        for metadata in Search('sthpw/search_object').get_sobjects():
            value = metadata.get_value('search_type') or metadata.get_code()
            try:
                target = allowed_type(value)
            except ValueError:
                continue
            types[target] = dict(value=target, label=metadata.get_value('title') or target)
        types = list(types.values())
        types.sort(key=lambda item: (item['label'].casefold(), item['value']))
        selected = None
        if parent_key:
            allowed_type(parent_key)
            chosen = Search.get_by_search_key(parent_key)
            if chosen is None:
                raise LookupError('Parent is no longer available')
            selected = candidate(chosen)
        return dict(expectedRevision=current, sourceRevision=revision(obj.get_data()), sourceId=str(obj.get_id()),
            sourceTitle=obj.get_value('name', no_exception=True) or obj.get_value('title', no_exception=True)
                or obj.get_code() or str(obj.get_id()), parentTypes=types,
            currentParentKey=current_key, currentParent=candidate(parent) if parent else None, selectedParent=selected,
            parentType=SearchKey.extract_base_search_type(parent_key or current_key) if parent_key or current_key else '')
    if action == 'candidates':
        if not expected_revision or expected_revision != current:
            raise ValueError('Parent changed. Reload before saving.')
        target = allowed_type(parent_type)
        search = Search(SearchType.build_search_type(target, project))
        if SearchType.column_exists(target, 'project_code'):
            search.add_filter('project_code', project)
        if target == base:
            search.add_filter('id', obj.get_id(), '!=')
        if query:
            fields = [name for name in ('code', 'name', 'title') if SearchType.column_exists(target, name)]
            if fields:
                search.add_op('begin')
                for name in fields:
                    search.add_regex_filter(name, re.escape(query))
                search.add_op('or')
            else:
                search.add_id_filter(int(query) if query.isdecimal() else -1)
        search.add_order_by('code' if SearchType.column_exists(target, 'code') else 'id')
        search.set_offset(offset)
        search.set_limit(51)
        records = search.get_sobjects()
        return dict(rows=[candidate(record) for record in records[:50]], offset=offset, hasNext=len(records) > 50)
    allowed_type(parent_key)
    chosen = Search.get_by_search_key(parent_key)
    if chosen is None:
        raise LookupError('Parent is no longer available')
    if chosen.get_value('project_code', no_exception=True) not in (None, '', project):
        raise ValueError('The parent belongs to another project')
    if chosen.get_search_key() == current_key:
        return dict(state='saved', searchKey=obj.get_search_key())
    if action == 'check':
        return dict(state='unchanged' if expected_revision == current else 'conflict')
    if not expected_revision or expected_revision != current or not parent_revision or parent_revision != revision(chosen.get_data()):
        raise ValueError('Parent changed. Reload before saving.')
    if chosen.is_retired():
        raise ValueError('Choose a current parent')
    ancestor, visited = chosen, {obj.get_search_key()}
    while ancestor is not None:
        identity = ancestor.get_search_key()
        if identity in visited:
            raise ValueError('Parent relationship is cyclic')
        visited.add(identity)
        ancestor = parent_of(ancestor)
    obj.add_relationship(chosen)
    obj.commit()
    return dict(state='saved', searchKey=obj.get_search_key())


def ingest_drop_files(
    search_key,
    files=None,
    dirs=None,
    upload_directory=None,
    transfer_mode=None,
    checkin_mode=None,
    context=None,
    subcontext_mode=None,
    subcontext=None,
):
    """Self-contained procedure also executed against an original TACTIC server."""
    import os
    from pyasm.biz import Project
    from pyasm.checkin import FileCheckin
    from pyasm.common import Environment
    from pyasm.search import SearchKey

    if not search_key:
        raise ValueError('Select a target item')
    if SearchKey.extract_project(search_key) not in (None, '', Project.get_project_code()):
        raise ValueError('The configured table target belongs to another project')
    sobject = SearchKey.get_by_search_key(search_key)
    if not sobject or sobject.is_insert():
        raise ValueError('The configured table target is unavailable')

    base_dir = os.path.abspath(Environment.get_upload_dir())
    if upload_directory:
        if upload_directory in ('.', '..') or any(sep in str(upload_directory) for sep in ('/', '\\')):
            raise ValueError('Invalid staged upload path')
        base_dir = os.path.abspath(os.path.join(base_dir, str(upload_directory)))

    raw_items = [str(item) for item in (files or dirs or []) if str(item or '').strip()]
    if not raw_items:
        raise ValueError('Select at least one file')

    checkin_mode = str(checkin_mode or 'default').strip() or 'default'
    if checkin_mode not in ('default', 'file', 'file_group'):
        raise ValueError(f'Unsupported checkin mode: {checkin_mode}')
    subcontext_mode = str(subcontext_mode or '{none}').strip() or '{none}'
    if subcontext_mode not in ('{none}', '{leaf}', '{folder}', '{custom}'):
        raise ValueError(f'Unsupported subcontext mode: {subcontext_mode}')
    transfer_mode = str(transfer_mode or 'free_copy').strip() or 'free_copy'
    if transfer_mode not in ('upload', 'uploaded', 'free_copy', 'copy', 'free_move', 'move'):
        raise ValueError(f'Unsupported transfer mode: {transfer_mode}')
    transfer_mode = {'upload': 'uploaded', 'free_copy': 'copy', 'free_move': 'move'}.get(transfer_mode, transfer_mode)
    context = str(context or 'publish').strip('/') or 'publish'
    subcontext = str(subcontext or '').strip('/')

    paths = []
    rel_dirs = {}
    for item in raw_items:
        rel_norm = os.path.normpath(item.replace('\\', '/')).lstrip('/\\')
        if not rel_norm or rel_norm in ('.', '..') or rel_norm.startswith('..'):
            raise ValueError('Invalid staged upload path')
        full_path = os.path.abspath(os.path.join(base_dir, rel_norm))
        if os.path.commonpath([base_dir, full_path]) != base_dir:
            raise ValueError('Invalid staged upload path')
        if not os.path.exists(full_path):
            alt_path = os.path.abspath(os.path.join(base_dir, os.path.basename(rel_norm)))
            if os.path.commonpath([base_dir, alt_path]) == base_dir and os.path.exists(alt_path):
                full_path = alt_path
            else:
                raise ValueError(f'File [{item}] does not exist in staged uploads')
        if os.path.isdir(full_path):
            for root, _dirnames, filenames in sorted(os.walk(full_path)):
                for filename in sorted(filenames):
                    member = os.path.abspath(os.path.join(root, filename))
                    paths.append(member)
                    rel_dirs[member] = os.path.relpath(root, base_dir).replace('\\', '/').strip('.')
        else:
            paths.append(full_path)
            rel_dirs[full_path] = os.path.dirname(rel_norm).replace('\\', '/').strip('.')
    if not paths:
        raise ValueError('Select at least one file')

    if not sobject.get_value('code', no_exception=True):
        sobject.set_value('code', os.path.basename(paths[0]))
        sobject.commit()

    snapshots = []
    if checkin_mode in ('file_group', 'file'):
        folder_part = rel_dirs.get(paths[0], '').strip('/')
        if subcontext_mode == '{folder}' and folder_part:
            checkin_context = f"{context}/{folder_part.replace('/', '_')}"
        elif subcontext:
            checkin_context = f'{context}/{subcontext}'
        else:
            checkin_context = context
        file_types = [f'ingest{idx}' for idx in range(len(paths))]
        checkin = FileCheckin(
            sobject,
            file_paths=paths,
            file_types=file_types,
            context=checkin_context,
            mode=transfer_mode,
            description=f'Ingest Files as group check-in [{sobject.get_code()}]',
        )
        checkin.execute()
        if checkin.get_snapshot():
            snapshots.append(checkin.get_snapshot())
    elif subcontext_mode == '{none}' and not subcontext:
        used_types = set()
        file_types = []
        for idx, path in enumerate(paths):
            ext = os.path.splitext(path)[1].lstrip('.') or 'main'
            file_type = ext if ext not in used_types else f'{ext}_{idx}'
            used_types.add(file_type)
            file_types.append(file_type)
        checkin = FileCheckin(
            sobject,
            file_paths=paths,
            file_types=file_types,
            context=context,
            mode=transfer_mode,
            description=f'Ingest check-in [{sobject.get_code()}]',
        )
        checkin.execute()
        if checkin.get_snapshot():
            snapshots.append(checkin.get_snapshot())
    else:
        for path in paths:
            folder_part = rel_dirs.get(path, '').strip('/')
            if subcontext_mode == '{leaf}':
                checkin_context = f'{context}/{os.path.basename(path)}'
            elif subcontext_mode == '{folder}' and folder_part:
                checkin_context = f"{context}/{folder_part.replace('/', '_')}"
            elif subcontext:
                checkin_context = f'{context}/{subcontext}'
            else:
                checkin_context = context
            checkin = FileCheckin(
                sobject,
                file_paths=[path],
                file_types=['main'],
                context=checkin_context,
                mode=transfer_mode,
                description=f'Ingest file [{os.path.basename(path)}]',
            )
            checkin.execute()
            if checkin.get_snapshot():
                snapshots.append(checkin.get_snapshot())

    return dict(
        search_key=sobject.get_search_key(),
        code=sobject.get_code(),
        snapshot_codes=[snap.get_code() for snap in snapshots],
        file_count=len(paths),
    )

