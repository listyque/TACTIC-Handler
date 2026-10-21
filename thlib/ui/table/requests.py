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
        # CG binds `parent` to its JSON search key, before any output; never expose Mako's parent namespace.
        for tree in trees[:1]:
            if not isinstance(tree, ast.Module):
                continue
            for statement in tree.body:
                if (isinstance(statement, ast.Assign) and len(statement.targets) == 1
                        and isinstance(statement.targets[0], ast.Name) and statement.targets[0].id == 'parent'
                        and isinstance(statement.value, ast.Call)
                        and isinstance(statement.value.func, ast.Attribute)
                        and isinstance(statement.value.func.value, ast.Name) and statement.value.func.value.id == 'sobject'
                        and statement.value.func.attr == 'get' and len(statement.value.args) == 1
                        and isinstance(statement.value.args[0], ast.Constant) and statement.value.args[0].value == '__search_key__'
                        and not statement.value.keywords):
                    reserved.discard('parent')
                    break
                if any(isinstance(item, ast.Name) and item.id == 'parent' for item in ast.walk(statement)):
                    break
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
            elif handler in ('tactic.ui.panel.TableLayoutWdg', 'tactic.ui.panel.FastTableLayoutWdg', 'tactic.ui.panel.ViewPanelWdg'):
                allowed = {'search_type','search_key','view','expression','show_search_limit','show_insert',
                           'show_row_select','show_select','show_gear','show_search','show_shelf','init_load_num'}
                if set(options) - allowed or not options.get('search_type'):
                    raise ValueError('Unsupported CustomLayout table options')
                nodes.append(dict(kind='table', text=attrs.get('name') or 'Table View', table=dict(
                    searchType=options['search_type'], parentKey=options.get('search_key') or search_key,
                    view=options.get('view') or 'table', expression=options.get('expression') or '',
                    selection=options.get('show_row_select',options.get('show_select')) not in (False,'false'),
                    insert=options.get('show_insert') not in (False,'false'))))
            elif handler in ('pyasm.widget.ThumbWdg', 'ThumbWdg'):
                from pyasm.widget import ThumbWdg
                widget = ThumbWdg(name=attrs.get('name') or 'preview', **options)
                widget.set_sobjects([obj]); widget.preprocess(); widget.set_current_index(0)
                value = widget.get_cell_value() if hasattr(widget, 'get_cell_value') else dict(image=widget.get_data(obj) or '')
                nodes.append(dict(kind='preview', text=str(obj.get_display_value()), value=value,
                                  javascript=behaviors.get(attrs.get('name'), '')))
            else:
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


def read_nested_scope(parent_key, search_type, view='table', expression='', offset=0,
                      limit=50, filters=None, order_by=None):
    """Self-contained original-server procedure; never return an unscoped table."""
    import re
    from pyasm.biz import Project
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey, SearchType

    if not Environment.get_security().is_admin():
        raise PermissionError('Administration requires administrator access')
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('Invalid nested table page')
    if not isinstance(view, str) or not re.fullmatch(r'[A-Za-z_][\w.@-]{0,127}', view):
        raise ValueError('Invalid view name')
    if SearchKey.extract_project(parent_key) not in (None, '', Project.get_project_code(), 'sthpw', 'admin'):
        raise ValueError('The configured table target belongs to another project')
    requested = SearchType.breakup_search_type(search_type)
    if requested.get('project') not in (None, '', Project.get_project_code(), 'sthpw', 'admin'):
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
    if parent.get_base_search_type() == 'sthpw/project' and base in (
            'sthpw/task', 'sthpw/snapshot', 'sthpw/note', 'sthpw/work_hour') and not expression:
        search.add_filter('project_code', parent.get_code())
    elif base == parent.get_base_search_type() and not expression:
        search.add_id_filter(parent.get_id())
    elif expression:
        # Only reads enter a nested table. Mutating expressions belong to actions.
        if not isinstance(expression, str) or not re.fullmatch(r'\s*@SOBJECT\([^@;{}]*\)\s*', expression, re.I):
            raise ValueError('A nested table requires an @SOBJECT expression')
        records = Search.eval(expression, sobjects=parent)
        if not isinstance(records, (list, tuple)):
            records = [records] if records else []
        if len(records) > 10000 or any(item.get_base_search_type() != base for item in records):
            raise ValueError('The nested expression returned an invalid scope')
        search.add_filters('id', [item.get_id() for item in records] or [-1])
    else:
        owner = parent.get_parent()
        if owner is not None and owner.get_base_search_type() == base:
            search.add_id_filter(owner.get_id())
        else:
            search.add_parent_filter(parent)
    columns = SearchType.get_column_info(base)
    if not isinstance(filters or [], list) or len(filters or []) > 20:
        raise ValueError('Invalid nested table filters')
    for item in filters or []:
        if not isinstance(item, (tuple, list)) or len(item) != 3 or item[0] not in columns or item[1] not in ('=', '!=', '<', '<=', '>', '>=', 'like'):
            raise ValueError('Invalid nested table filter')
        search.add_filter(item[0], item[2], op=item[1])
    if not isinstance(order_by or [], list) or len(order_by or []) > 4:
        raise ValueError('Invalid nested table ordering')
    for item in order_by or []:
        parts = str(item).split()
        if not parts or len(parts) > 2 or parts[0] not in columns or (len(parts) == 2 and parts[1].lower() not in ('asc', 'desc')):
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
    return dict(searchType=base, view=view, parentKey=parent_key, offset=offset,
                hasNext=len(records) > limit,
                records=values)


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

    if not Environment.get_security().is_admin():
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


def read_snapshot_files(search_key):
    """Read a captured concrete snapshot using only original server methods."""
    import json
    from pyasm.biz import Project, Snapshot
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey

    if not Environment.get_security().is_admin():
        raise PermissionError('Administration requires administrator access')
    if SearchKey.extract_base_search_type(search_key) != 'sthpw/snapshot':
        raise ValueError('Check out requires a snapshot')
    snapshot = Search.get_by_search_key(search_key)
    if snapshot is None:
        raise LookupError('Snapshot is no longer available')
    if snapshot.get_value('project_code') != Project.get_project_code():
        raise ValueError('Open the snapshot in its own project before checking out files')
    if str(snapshot.get_value('search_type') or '').split('?')[0] in ('sthpw/message', 'sthpw/message_log'):
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
    files = snapshot.get_all_file_objects()
    if any(file.get_value('file_range', no_exception=True) or (
            file.get_metadata_dict().get('template') and
            file.get_metadata_dict().get('type') not in ('file', 'layer_file', 'no_ext')) for file in files):
        raise ValueError('Sequence and UDIM checkout is not available in this table yet')
    data = snapshot.get_sobject_dict()
    data['__files__'] = [file.get_sobject_dict() for file in files]
    return json.loads(json.dumps(data, default=str))


def read_connection_cells(search_keys, direction='dst', icon_size=60):
    import hashlib
    import json
    from pyasm.biz import Project, SObjectConnection
    from pyasm.common import Environment
    from pyasm.search import Search, SearchKey
    from pyasm.widget import ThumbWdg

    if not Environment.get_security().is_admin():
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

    if not Environment.get_security().is_admin():
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
