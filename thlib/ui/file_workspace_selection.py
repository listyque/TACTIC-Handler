"""Show a bounded sibling page for the file selected in either tree."""


def selected_tree_files(controller, client, state, cache):
    focus = next((row for row in state['files_selection'] if row.get('id')==state['tree_selection']), state['files_selection'][-1])
    tree = state['workspace_tree'] if state['files_source'] in ('local', 'have') else state['depot_tree']
    siblings = [row for row in tree if row.get('kind') in ('file', 'directory')
                and row.get('stream', state['files_stream']) == state['files_stream']
                and row.get('path', '').rstrip('/').rpartition('/')[0] == state['files_prefix'].rstrip('/')]
    position = next((index for index, row in enumerate(siblings) if row['path'] == focus.get('path')), 0)
    start = position // 200 * 200
    after = siblings[start - 1]['path'] if start else ''
    state.update(view=state['files_source'], prefix=state['files_prefix'], stream=state['files_stream'],
                 cursors=[''] if after else [])
    controller._files(client, state, cache, after=after)
