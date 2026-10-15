"""Bounded tree retention and direct restoration of off-page directory paths."""
from pathlib import Path

TREE_LIMIT = 8192


def trim_tree(tree, protected):
    ancestors = set()
    for index, row in enumerate(tree):
        if row['id'] == protected:
            depth = row['depth']
            for parent in reversed(tree[:index]):
                if parent['depth'] < depth:
                    ancestors.add(parent['id'])
                    depth = parent['depth']
            break
    removed = False
    while len(tree) > TREE_LIMIT:
        index = next((i for i, row in enumerate(tree)
                      if row['depth'] > 1 and row['id'] not in ancestors | {protected}), None)
        if index is None:
            break
        end = index + 1
        while end < len(tree) and tree[end]['depth'] > tree[index]['depth']:
            end += 1
        del tree[index:end]
        removed = True
    return removed


def restore_directories(controller, client, state, cache):
    from thlib.side.client.tactic_client_lib.file_workspace import local_browse
    for workspace, field in ((False, 'depot'), (True, 'workspace')):
        tree = state[field + '_tree']
        for identity in sorted(state[field + '_expanded'], key=lambda value: (value.count('/'), value))[:TREE_LIMIT]:
            supplied=state.get('directory_pages',{}).get(identity,{})
            node = next((row for row in tree if row['id'] == identity), None)
            if not node:
                if workspace and identity.startswith('workspace-path/'):
                    path = identity[len('workspace-path/'):]
                    prefix, stream = 'workspace-path/', None
                elif not workspace and identity.startswith('path/'):
                    _, stream, path = identity.split('/', 2)
                    prefix = 'path/' + stream + '/'
                else:
                    continue
                if not path.endswith('/'):
                    continue
                directory = path.rstrip('/').rpartition('/')[0]
                directory = directory + '/' if directory else ''
                parent_id = prefix + directory if directory else 'workspace/' + state['workspace'] if workspace else 'stream/' + stream
                parent = next((row for row in tree if row['id'] == parent_id), None)
                if not parent:
                    continue
                options = {'directory': directory, 'after': path[:-1], 'limit': 1}
                if supplied.get('seek') is not None:
                    page=supplied['seek']
                elif workspace:
                    if (cache / 'local.sqlite').is_file():
                        page = local_browse(cache / 'local.sqlite', **options)
                    else:
                        page = client.rpc('workspace_browse', workspace=state['workspace'], root=state['workspace_tree_root'] or None, **options)
                else:
                    page = client.rpc('browse', stream=stream, published_change=state['depot_heads'].get(stream), **options)
                row = next((row for row in page['items'] if row['path'] == path and row['kind'] == 'directory'), None)
                if not row:
                    continue
                node = {**row, 'id': identity, 'directory': path, 'depth': parent['depth'] + 1,
                        'workspace': workspace, 'stream': stream, 'expanded': False}
                tree.insert(tree.index(parent) + 1, node)
            if not node.get('expanded'):
                if workspace:
                    controller._workspace_branch(client, state, cache, identity,page=supplied.get('page'))
                else:
                    controller._depot_branch(client, state, identity,page=supplied.get('page'))
    for reference in state['selection_records'].values():
        code, path = reference.get('parent'), reference.get('path')
        if not code or not path or code not in state['change_children']:
            continue
        page = state['change_children'][code]
        if any(row['path'] == path for row in page['items']):
            continue
        change = next((row for row in state['changes'] if row['code'] == code), None)
        if not change:
            continue
        options = {'shelf' if change['state'] == 'shelved' else 'change': code, 'prefix': path, 'limit': 1}
        if change['state'] == 'pending':
            options['edit_revision'] = page['edit_revision']
        selected = client.rpc('inspect_change_files', **options)
        row = next((row for row in selected['items'] if row['path'] == path), None)
        if row:
            controller._file_states(client, state, cache, [row], change['stream'])
            page['items'].append(row)
            protected = {value.get('path') for value in state['selection_records'].values() if value.get('parent') == code}
            while len(page['items']) > 1000:
                page['items'].pop(next(index for index,value in enumerate(page['items']) if value['path'] not in protected))
            page['items'].sort(key=lambda row: row['path'])
    controller._tree(state)
