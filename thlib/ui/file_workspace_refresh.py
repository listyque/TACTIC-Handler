"""Apply one bounded native snapshot; filesystem inspection remains in the worker."""
from copy import deepcopy


def refresh(controller, client, state, cache, *, catalog=True, operation=''):
    from thlib.environment import env_server
    from thlib.side.client.tactic_client_lib.file_workspace import local_page, local_browse, pending_local_counts, local_change_counts
    from .file_workspace_recovery import cache_directory, load_operation, save_operation
    from .file_workspace_tree_state import restore_directories
    from .file_workspace import VIEW_PRESETS
    tab=next((row for row in state['tabs'] if row['id']==state['active_tab']),{})
    if catalog and not operation and tab.get('kind')=='files':
        state.update(view=state['files_source'] if tab.get('source')=='selection' else tab.get('source','depot'),
                     stream=state['files_stream'] or state['stream'],
                     prefix=(tab.get('prefix') or state['files_prefix']) if tab.get('source')=='selection' else tab.get('prefix',''))
    elif catalog and not operation and tab.get('kind')=='changes':
        state.update(view='change',state=tab['state'])
    state['depot_expanded']=[row['id'] for row in state['depot_tree'] if row.get('expanded')] if state['depot_tree'] else state['depot_expanded']
    state['workspace_expanded']=[row['id'] for row in state['workspace_tree'] if row.get('expanded')] if state['workspace_tree'] else state['workspace_expanded']
    directories=[]
    if catalog:
        for identity in sorted(state['depot_expanded'],key=lambda value:(value.count('/'),value)):
            if identity.startswith('stream/'):
                directories.append({'id':identity,'action':'browse','values':{'stream':identity.split('/',1)[1],'directory':''}})
            elif identity.startswith('path/'):
                _,stream,directory=identity.split('/',2)
                directories.append({'id':identity,'action':'browse','values':{'stream':stream,'directory':directory}})
        if not (cache/'local.sqlite').is_file():
            for identity in state['workspace_expanded']:
                if identity.startswith('workspace/') or identity.startswith('workspace-path/'):
                    directories.append({'id':identity,'action':'workspace_browse','values':{'directory':identity[len('workspace-path/'):] if identity.startswith('workspace-path/') else ''}})
    directories=directories[:16]
    snapshot=client.rpc('workspace_snapshot',catalog=catalog,reason=operation,tab=tab,
        workspace=state['workspace'],active_revision=state['active_revision'],stream=state['stream'],
        state=state['state'],view=state['view'],prefix=state['prefix'],change=state['change'].get('code'),
        expanded=state['expanded_changes'][:32],directories=directories,history_path=state['history_path'],history_stream=state['history_stream'],
        files_after=state['cursor'] if tab.get('kind')=='files' and tab.get('source')=='selection' else '')
    metadata=snapshot['catalog']
    if catalog:
        state['administrator']=metadata['capabilities']['administrator']
        for field in ('workspaces','streams','depots'):
            state[field]=metadata[field]['items'];state[field+'_after']=metadata[field].get('after')
    state['tasks']=metadata['tasks']['items'];state['tasks_after']=metadata['tasks'].get('after')
    active=metadata['active'];state['active_revision']=active['revision']
    state['workspace']=snapshot['workspace'] or state['workspace']
    ws=active.get('info') or next((row for row in state['workspaces'] if row['code']==state['workspace']),None)
    if ws:
        state['stream']=snapshot['stream'] or ws['stream'];state['root']=state['root'] or ws['local_root']
        if not any(row['code']==ws['code'] for row in state['workspaces']):state['workspaces'].append(ws)
    state['targets']=metadata['targets']['items']
    if catalog or operation=='submit':controller._depot_roots(state)
    state['locks']={}
    if catalog:
        cache=cache.with_name(cache_directory('',client.url,env_server.get_user(),client.project,state['workspace'],state['root']).name)
    state['local_cache']=str(cache/'local.sqlite')
    if catalog:
        state['recovery']=load_operation(cache,state)
        if state['recovery']:
            state['connection_state']='recovery_available'
            task=state['recovery']['progress'].get('task')
            if task:
                retained=client.rpc('transfer_status',task=task)
                if retained['state'] in ('complete','ready','submitted'):
                    save_operation(cache,{});state['recovery']={}
                else:state['progress']={**retained,'phase':'offline'}
    state['changes']=snapshot['changes']['items'];state['changes_after']=snapshot['changes'].get('after')
    if snapshot.get('change'):
        clean=state['description']==state['change'].get('description','')
        state['change']=snapshot['change']
        if clean:state['description']=state['change'].get('description','')
    if snapshot.get('active_state') in ('submitted','reverted'):
        state['state']=snapshot['active_state'];state['active_tab']=state['state'];state['view']='change'
        if not any(row['id']==state['active_tab'] for row in state['tabs']):
            state['tabs'].append(deepcopy(next(row for row in VIEW_PRESETS if row['id']==state['state'])))
    state['expanded_changes']=[code for code in state['expanded_changes'] if code in snapshot['pages']]
    state['change_children']={}
    for code,page in snapshot['pages'].items():
        stream=page['info']['stream']
        controller._file_states(client,state,cache,page['items'],stream)
        controller._locks(client,state,page['items'],stream)
        state['change_children'][code]=page
        if code not in state['expanded_changes']:state['expanded_changes'].append(code)
        if state['change'].get('code')==code:
            state['change'].update(page['info'])
    if state['view']=='local':
        if tab.get('kind')=='files' and tab.get('source')=='selection':
            page=local_browse(cache/'local.sqlite',directory=state['prefix'],after=state['cursor'])
            page['items']=[row for row in page['items'] if row['kind']=='file']
        else:
            page=local_page(cache/'local.sqlite',changes_only=False,prefix=state['prefix'],local_changes_only=tab.get('reconcile_only',False))
        state['rows']=page['items'];state['after']=page.get('after')
    elif state['view']=='change':
        page=snapshot['pages'].get(state['change'].get('code'),{'items':[],'after':None})
        state['rows']=page['items'];state['after']=page.get('after')
    else:
        page=snapshot.get('files',{'items':[],'after':None})
        state['rows']=page['items'];state['after']=page.get('after')
        controller._file_states(client,state,cache,state['rows'],state['stream'])
        controller._locks(client,state,state['rows'],state['stream'])
    if tab.get('kind')!='files' or tab.get('source')!='selection':
        state['cursor']=''
    state['conflicts']=snapshot.get('conflicts',{}).get('items',[])
    state['conflicts_after']=snapshot.get('conflicts',{}).get('after')
    state['resolved_conflicts']=snapshot.get('resolved',{}).get('items',[])
    state['conflict_selected']=[path for path in state['conflict_selected'] if any(row['path']==path for row in state['conflicts'])]
    if 'history' in snapshot:state.update(history=snapshot['history']['items'],history_more=snapshot['history'].get('more',False))
    if 'catalog_view' in snapshot:
        page=snapshot['catalog_view'];state['catalog_source']=tab['source']
        state.update(catalog_rows=page.get('items',[]),catalog_after=page.get('after'),catalog_cursor='',
                     catalog_detail=page if tab['source']=='storage' else {},graph_after=page.get('edge_after'),graph_heads=page.get('heads',{}))
        if tab['source']=='stream_graph':
            state['graph_nodes']=page['items']
            state['graph_edges']=page['edges']
    state['local_counts']=local_change_counts(cache/'local.sqlite',state['stream'])
    for row in state['changes']:
        if row['state']=='pending' and row.get('workspace')==state['workspace']:
            row['local_counts']=pending_local_counts(cache/'local.sqlite',row['code'],row['edit_revision'])
    controller._sort_rows(state);controller._tree(state)
    if catalog:
        state['directory_pages']=snapshot.get('directories',{})
        restore_directories(controller,client,state,cache)
        state.pop('directory_pages',None)
    return state
