"""Project/group permission projection; native XML remains owned by the editor.

TACTIC combines identical keys using the highest access level. Key fallback is
ordered by the consuming widget (Task/Gear wildcards precede individual keys).
The matrix must not advertise a deny that those native checks would ignore.
"""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Slot

from .documents import RulesDocument


SCOPES = ('project', 'link', 'gear_menu', 'search_type', 'process', 'tasks')
ACCESS = {'deny': 0, 'false': 0, 'view': 1, 'true': 1, 'edit': 2,
          'insert': 3, 'retire': 4, 'delete': 5, 'allow': 5}
RULE_META = {'group', 'category', 'access', 'project', 'ruleIndex'}


def native_key(scope, attributes, project='*'):
    return (scope, tuple(sorted((key, value) for key, value in attributes.items()
                                if key not in RULE_META)),
            '*' if scope == 'project' else project or '*')


def lookup_keys(scope, attributes, project):
    """Match the ordered native sidebar/search/process/task/menu lookups."""
    attrs = {key: value for key, value in attributes.items() if key != 'project'}
    wildcard = {key: '*' for key in attrs}
    if scope == 'project':
        return [native_key(scope, attrs), native_key(scope, wildcard)]
    if scope == 'tasks':
        return [native_key('process', {'process': '*', 'pipeline': attrs['pipeline']}),
                native_key('process', wildcard), native_key('process', attrs)]
    if scope == 'gear_menu':
        return [native_key(scope, wildcard, project), native_key(scope, attrs, project)]
    if scope == 'search_type':
        return [native_key(scope, attrs), native_key(scope, attrs, project),
                native_key(scope, wildcard), native_key(scope, wildcard, project)]
    return [native_key(scope, attrs, project), native_key(scope, attrs),
            native_key(scope, wildcard, project), native_key(scope, wildcard)]


def compile_group(editor, identity, omit=()):
    """A small read-only index of native rule keys, including subgroup grants."""
    result, visited = {}, set()
    groups = editor.document.get('groups', {})
    names = {row['label']: row['identity'] for row in editor.groupCatalog}

    def add_rules(records, bound_project):
        for rule in records:
            scope = rule.get('group') or rule.get('category')
            if rule.get('default') in ACCESS:
                result[(scope, (), '__DEFAULT__')] = rule['default']
                continue
            if rule.get('access') not in ACCESS:
                continue
            key = native_key(scope, rule, bound_project or rule.get('project', '*'))
            if ACCESS.get(result.get(key), -1) < ACCESS[rule['access']]:
                result[key] = rule['access']

    def collect(code):
        if code in visited or code not in groups:
            return
        visited.add(code)
        document = groups[code]
        bound_project = document['project']
        records = editor._group_rules[code].records()
        add_rules([row for row in records if code != identity or row['ruleIndex'] not in omit],
                  bound_project)
        defaults = editor.metadata.get('globalDefaultRulesByLevel', {}).get(document['accessLevel'], '<rules/>')
        default_rules = RulesDocument(defaults)
        # Native defaults use the group's project list, not the project open
        # in this editor. A global low-level group grants no project by itself.
        if bound_project:
            for rule in default_rules.root.findall('rule'):
                if (rule.get('group') or rule.get('category')) == 'project':
                    default_rules.root.remove(rule)
            default_rules.set_rule(-1, {'group': 'project', 'code': bound_project, 'access': 'allow'})
        add_rules(default_rules.records(), bound_project)
        for name in document['subGroups'].split('|'):
            if name == 'admin':
                result[('__admin__', (), '*')] = 'allow'
            elif name in names:
                collect(names[name])

    collect(identity)
    return result


def resolve(index, keys):
    if ('__admin__', (), '*') in index:
        return 'allow'
    for key in keys:
        values = [index[key]] if key in index else []
        if key[0] != 'project' and key[2] != '*':
            global_key = (key[0], key[1], '*')
            if global_key in index:
                values.append(index[global_key])
        if values:
            return max(values, key=ACCESS.get)
    return index.get((keys[-1][0], (), '__DEFAULT__'), 'deny') if keys else 'deny'


class SecurityMatrixModel(QAbstractTableModel):
    """Virtualized cells; edits publish dataChanged, never reset a scrolled grid."""

    CELL = Qt.UserRole + 1

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.scope = 'project'
        self.query = self.group_query = ''
        self.targets, self.groups, self.cells = [], [], []

    def roleNames(self):
        return {self.CELL: b'cell', Qt.DisplayRole: b'display'}

    @Slot(int, int, result='QVariantMap')
    def cell_at(self, row, column):
        return self.cells[row][column] if 0 <= row < len(self.cells) and 0 <= column < len(self.groups) else {}

    @Slot(int, int, result=str)
    def cell_label(self, row, column):
        if not self.cell_at(row, column):
            return ''
        target = self.targets[row]
        return '%s · %s' % (self.groups[column]['label'], self.tr('All') if target.get('all') else target['label'])

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.targets)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.groups)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == self.CELL:
            return self.cells[index.row()][index.column()]
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        rows = self.groups if orientation == Qt.Horizontal else self.targets
        return rows[section] if 0 <= section < len(rows) else None

    @Slot(str, str, str)
    def filter(self, scope, query, group_query):
        if scope not in SCOPES:
            return
        values = scope, query.casefold().strip(), group_query.casefold().strip()
        if values != (self.scope, self.query, self.group_query):
            self.scope, self.query, self.group_query = values
            self.refresh(reset=True)

    def refresh(self, reset=False):
        previous = self.cells
        if reset:
            self.beginResetModel()
            self.targets = [row for row in self.editor.metadata.get('targets', {}).get(self.scope, [])
                            if not self.query or self.query in str(row).casefold()]
            self.groups = [row for row in self.editor.groupCatalog
                           if row['identity'] in self.editor._group_rules
                           and self.group_query in row['label'].casefold()]
        self.cells = [[{} for _ in self.groups] for _ in self.targets]
        for column, group in enumerate(self.groups):
            identity = group['identity']
            index = compile_group(self.editor, identity)
            records = self.editor._group_rules[identity].records()
            for row, target in enumerate(self.targets):
                self.cells[row][column] = self.cell_state(identity, target, index, records)
        if reset:
            self.endResetModel()
        else:
            for row, cells in enumerate(self.cells):
                for column, cell in enumerate(cells):
                    if cell != previous[row][column]:
                        index = self.index(row, column)
                        self.dataChanged.emit(index, index, [self.CELL])

    def cell_state(self, identity, target, index, records):
        document = self.editor.document['groups'][identity]
        scope = 'process' if self.scope == 'tasks' else self.scope
        attrs = target['attributes']
        bound = document['project']
        target_key = native_key(scope, attrs, bound or attrs.get('project', '*'))
        exact = [record for record in records
                 if native_key(record.get('group') or record.get('category'), record,
                               bound or record.get('project', '*')) == target_key]
        keys = lookup_keys(self.scope, attrs, self.editor._project)
        access = resolve(index, keys)
        # Limited/custom access is never silently promoted to full access.
        custom = any(record.get('access') not in ('allow', 'deny', 'false') for record in exact)
        baseline = compile_group(self.editor, identity, [record['ruleIndex'] for record in exact]) if exact else index
        desired = 'deny' if ACCESS[access] > 0 else 'allow'
        proposed = dict(baseline)
        proposed[target_key] = max((baseline.get(target_key, 'deny'), desired), key=ACCESS.get)
        locked = (custom or (bound and bound != self.editor._project and scope != 'project')
                  or (ACCESS[resolve(proposed, keys)] > 0) == (ACCESS[access] > 0))
        return {'group': identity, 'checked': ACCESS[access] > 0,
                'inherited': not exact, 'locked': bool(locked), 'custom': custom,
                'access': access, 'explicit': bool(exact),
                'ruleIndices': [record['ruleIndex'] for record in exact]}

    @Slot(int, int, bool)
    def set_allowed(self, row, column, allowed):
        if (not self.editor.canWrite or self.editor.busy
                or not 0 <= row < len(self.targets) or not 0 <= column < len(self.groups)):
            return
        state = self.cells[row][column]
        if state['locked'] or state['checked'] == allowed:
            return
        rules = self.editor._group_rules[state['group']]
        for index in reversed(state['ruleIndices']):
            rules.remove(index)
        rules.set_rule(-1, {'group': 'process' if self.scope == 'tasks' else self.scope,
                           **self.targets[row]['attributes'], 'access': 'allow' if allowed else 'deny'})
        self.editor.group_rules_changed(state['group'])

    @Slot(int, int)
    def inherit(self, row, column):
        if (not self.editor.canWrite or self.editor.busy
                or not 0 <= row < len(self.targets) or not 0 <= column < len(self.groups)):
            return
        state = self.cells[row][column]
        if state['custom']:
            return
        for index in reversed(state['ruleIndices']):
            self.editor._group_rules[state['group']].remove(index)
        self.editor.group_rules_changed(state['group'])
