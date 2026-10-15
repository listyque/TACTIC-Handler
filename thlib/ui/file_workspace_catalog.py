"""Paged permitted metadata and graph views; all filesystem work stays elsewhere."""
def catalog_page(client, state: dict, values: dict) -> None:
    source=values.get('source') or state.get('catalog_source') or 'workspaces'
    if source not in ('workspaces','streams','depots','stream_graph','storage'):
        raise ValueError('Choose a supported catalog view.')
    after=state.get('catalog_after') or '' if values.get('more') else ''
    options={'after':after,'limit':200}
    if values.get('edges'):
        options.update(after=state.get('catalog_cursor',''),edge_after=state.get('graph_after'),heads=state.get('graph_heads'))
    capabilities,result=client.rpc('read_batch',requests=[
        {'action':'capabilities','values':{}},
        {'action':'storage_status' if source=='storage' else source,'values':options}])['items']
    state['administrator']=capabilities['administrator']
    state['catalog_capabilities']=capabilities
    state['catalog_source']=source
    if source=='storage':
        state['storage_info']=result
        state['catalog_rows']=[];state['catalog_detail']=result;state['catalog_after']=None
        return
    state.update(catalog_rows=(state['catalog_rows']+result['items'])[:2000] if source=='streams' and values.get('more') else result['items'],catalog_after=result.get('after'),catalog_cursor=options['after'],
                 catalog_detail={},graph_after=result.get('edge_after'),graph_heads=result.get('heads',{}))
    if source=='stream_graph':
        state['graph_nodes']=result['items']
        state['graph_edges']=result['edges']


def edit_stream(client, state, action, values):
    from urllib.error import URLError
    request=values.pop('request')
    try:
        if action=='stream_editor':
            requests=[{'action':'capabilities','values':{}}, {'action':'depots','values':{'limit':1000}},
                      {'action':'streams','values':{'limit':1000}}]
            if values.get('stream'):
                requests.append({'action':'stream_status','values':{'stream':values['stream']}})
            result=client.rpc('read_batch',requests=requests)['items']
            state['stream_editor']={'request':request,'info':result[3] if len(result)>3 else {},
                'types':result[0].get('stream_types',[]),'depots':result[1]['items'],
                'parents':result[2]['items'],'more':bool(result[1].get('after') or result[2].get('after')),'error':''}
        else:
            operation='update_stream' if values.get('stream') else 'create_stream'
            if 'spec_revision' in values:values['spec_revision']=int(values['spec_revision'])
            result=client.rpc(operation,**values)
            state['stream_editor']={'request':request,'saved':True,'info':result,'error':''}
            for field in ('streams','catalog_rows','graph_nodes'):
                rows=state[field]
                state[field]=[{**row,**result} if row['code']==result['code'] else row for row in rows]
            state['catalog_detail']=result
    except (URLError,ValueError,TimeoutError,ConnectionError) as error:
        state['stream_editor']={'request':request,'error':str(error)}
        state['operation_notice']={'level':'WARNING','message':str(error)}
    return state


def depot_editor(client, state, action, values):
    from copy import deepcopy
    if action == 'depot_editor':
        info = client.rpc('depot_status', depot=values['depot']) if values.get('depot') else {}
        draft = dict(creating=not bool(info), code=info.get('code',''), title=info.get('title',''),
                     repository=(info.get('storage') or {}).get('repository',''), revision=info.get('revision',0))
        state.update(depot_draft=draft, depot_original=deepcopy(draft))
    else:
        draft = state['depot_draft']
        values = dict(title=draft['title'], repository=draft['repository'] or None)
        if draft['creating']: values['code'] = draft['code'].strip()
        else: values.update(depot=draft['code'], revision=draft['revision'])
        result = client.rpc('create_depot' if draft['creating'] else 'update_depot', **values)
        catalog_page(client, state, {'source':'depots'})
        state.update(depot_draft={}, depot_original={}, catalog_detail=result)
    return state


def storage_admin(client, state, values, cancelled):
    operation = values.get('operation','storage_status')
    if operation not in ('storage_status','storage_policy','storage_upgrade','storage_index','gc_begin','gc_cancel'):
        raise ValueError('Unknown storage operation')
    options = {}
    if operation == 'storage_policy':
        draft = state['storage_draft']
        options = dict(revision=draft['revision'], policy=draft['policy'])
    elif operation == 'gc_begin': options['dry_run'] = values.get('dry_run',True)
    elif operation == 'gc_cancel': options['task'] = state['storage_info']['gc']['code']
    client.rpc(operation, **options)
    state['storage_info'] = client.rpc('storage_status')
    while operation == 'storage_index' and not state['storage_info']['indexed'] and not cancelled.is_set():
        client.rpc('storage_index')
        state['storage_info'] = client.rpc('storage_status')
    if operation == 'storage_policy':
        state['storage_draft'] = {}; state['storage_original'] = {}
    return state
