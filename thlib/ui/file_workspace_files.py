"""Worker-only file-view actions, using the native file API and bounded local work."""
from pathlib import Path
import json
import os
import uuid

from PySide6.QtCore import QFile, QUrl
from thlib.side.client.tactic_client_lib.file_transfer import digest_file, local_path
from thlib.side.client.tactic_client_lib.file_workspace import workspace_files


WORKSPACE_DROP_MESSAGE = 'Only files and folders inside the active workspace can be added by drag and drop. No files were added.'


def workspace_drop_roots(root: Path, urls: list[str | QUrl]) -> list[Path] | None:
    if not isinstance(urls,list) or not 1 <= len(urls) <= 1000:
        raise ValueError('Drop 1..1000 selected file or folder roots.')
    roots=[]
    for value in urls:
        if not isinstance(value,(str,QUrl)):raise ValueError('Drop local file URLs.')
        url=QUrl(value)
        if not url.isLocalFile():return None
        source=Path(url.toLocalFile())
        if not source.is_absolute():return None
        resolved=source.resolve()
        if not resolved.is_relative_to(root):return None
        if source.is_symlink() or any(parent.is_symlink() for parent in source.parents) or not source.exists():
            raise ValueError('Drop existing local files or directories without symlinks.')
        roots.append(resolved)
    return sorted(set(roots),key=lambda source:source.parts)


def execute_files(client, state, cache, action, values, cancelled):
    """Return True for actions owned by basic file interaction."""
    if action not in ('mark_delete', 'delete_local', 'open_local', 'reveal_local',
                      'revert_unchanged', 'revert_unchanged_change', 'drop_files', 'delete_change', 'navigate', 'target_files', 'rename_file', 'resume_local_moves', 'copy_local_paths', 'export_query','reveal_tree'):
        return False
    from .file_workspace_interaction import selected_rows
    scope = state['selection_scope']
    local_root=Path(state['root']).resolve()
    drop_roots=None
    if action=='drop_files' and not values.get('payload'):
        state.pop('drop_rejected',None)
        drop_roots=workspace_drop_roots(local_root,values.get('urls',[]))
        if drop_roots is None:
            state['drop_rejected']=WORKSPACE_DROP_MESSAGE
            state['operation_notice']={'level':'WARNING','message':WORKSPACE_DROP_MESSAGE}
            return True
    rows = [row for row in selected_rows(state) if row.get('path') and row.get('kind','file')=='file']
    change = state['change']
    if action=='reveal_tree':
        if len(rows)!=1:raise ValueError('Select one file to reveal.')
        row=rows[0];stream=row.get('stream') or state['stream'];path=row.get('source_path',row['path'])
        info=client.rpc('file_states',workspace=state['workspace'],paths=[{'stream':stream,'path':path}])['items'][0]
        workspace=state['tree_view']=='depot'
        if workspace and info['excluded']:raise ValueError('The file is not mapped to this workspace.')
        if not workspace and not info['head']:raise ValueError('The file is not on the server yet.')
        if workspace:
            tree=[{'id':'workspace/'+state['workspace'],'kind':'workspace','name':state['workspace'],'directory':'','depth':0,'expanded':True}]
            path=info['local_path'];prefix='workspace-path/';depth=1
        else:
            metadata=client.rpc('stream_status',stream=stream)
            tree=[{'id':'depot/'+metadata['depot'],'kind':'depot','name':metadata['depot'],'depth':0,'expanded':True},
                  {'id':'stream/'+stream,'kind':'stream','name':stream,'stream':stream,'directory':'','depth':1,'expanded':True}]
            prefix='path/'+stream+'/';depth=2
        parts=path.split('/');directory=''
        for part in parts[:-1]:
            directory+=part+'/'
            tree.append({'id':prefix+directory,'kind':'directory','name':part,'path':directory,'directory':directory,'stream':stream,'workspace':workspace,'depth':depth,'expanded':True})
            depth+=1
        item={**row,**info,'id':prefix+path,'kind':'file','name':parts[-1],'path':path,'source_path':info['path'],'stream':stream,'directory':'','depth':depth,'workspace':workspace}
        if workspace:item['local_status']='missing' if not local_path(local_root,path).is_file() else row.get('local_status','')
        for key in ('parent','change_state'):item.pop(key,None)
        tree.append(item)
        state.update(tree_view='workspace' if workspace else 'depot',tree_selection=item['id'],selection_scope='workspace' if workspace else 'depot',selection_ids=[item['id']],selection_records={item['id']:item},selected=[path])
        state['workspace_tree' if workspace else 'depot_tree']=tree
        return True
    if action=='export_query':
        destination=Path(QUrl(values['destination']).toLocalFile())
        temporary=destination.with_name(destination.name+'.'+uuid.uuid4().hex+'.tmp')
        try:
            after=''
            with temporary.open('x',encoding='utf-8') as output:
                while True:
                    if cancelled.is_set():raise InterruptedError('Workspace operation stopped')
                    page=client.rpc('selection_page',selection=state['selection_query']['selection'],after=after,limit=1000)
                    for row in page['items']:output.write(json.dumps(row,ensure_ascii=False)+'\n')
                    after=page['after']
                    client.progress({'state':'collecting','path':str(destination),'total_known':False})
                    if not after:break
            os.replace(temporary,destination)
        finally:temporary.unlink(missing_ok=True)
        return True
    if action == 'target_files':
        operation=values['operation']
        if operation not in ('checkout','mark_delete','move_files','restore_file','apply_reconcile'):
            raise ValueError('Choose a supported file operation')
        if not rows:raise ValueError('Select files first.')
        if not values.get('target') and not values.get('creating'):raise ValueError('Choose a target changelist or create one explicitly.')
        destination=client.rpc('status',change=values['target']) if values.get('target') else client.rpc(
            'create_change',workspace=state['workspace'],stream=rows[0].get('stream') or state['stream'],description=values.get('description',''))
        if destination['state']!='pending':
            raise ValueError('Choose a pending target changelist')
        if any(row.get('stream',destination['stream'])!=destination['stream'] or row.get('writable') is False for row in rows):
            raise ValueError('Select writable files from one changelist stream.')
        paths=[row.get('source_path',row['path']) for row in rows]
        if operation=='apply_reconcile':
            from thlib.side.client.tactic_client_lib.file_transfer import digest_file, fingerprint
            if state['selection_scope']!='files' or state['view']!='local':
                raise ValueError('Select files in the local Reconcile results.')
            root=Path(state['root']).resolve()
            renames=[row for row in rows if row.get('rename_from')]
            for row in rows:
                if cancelled.is_set():
                    raise InterruptedError('Workspace operation stopped')
                file=local_path(root,row['path'])
                if row.get('local_status') in ('added','modified') and (not file.is_file() or list(fingerprint(file))!=row.get('fingerprint')):
                    raise ValueError('Local file changed; Reconcile again: '+row['path'])
            for offset in range(0,len(renames),1000):
                batch=renames[offset:offset+1000]
                originals=client.rpc('file_entries',stream=destination['stream'],change=destination['code'],
                    paths=[row['rename_from'] for row in batch])['items']
                for row,original in zip(batch,originals):
                    if not original['file'] or original['file'].get('sha256')!=row['sha256']:
                        raise ValueError('Rename source changed on the server; sync and Reconcile again: '+row['rename_from'])
            if renames:
                client.rpc('rename_files',change=destination['code'],edit_revision=destination['edit_revision'],request_id=uuid.uuid4().hex,
                           renames=[{'source':row['rename_from'],'target':row['source_path']} for row in renames])
                destination=client.rpc('status',change=destination['code'])
            deletions=[row['source_path'] for row in rows if row.get('local_status')=='missing' and row['source_path'] not in {rename['rename_from'] for rename in renames}]
            if deletions:
                client.rpc('edit',change=destination['code'],edit_revision=destination['edit_revision'],chunk=uuid.uuid4().hex,
                           operations=[{'path':path,'delete':True} for path in deletions])
            uploads=[row for row in rows if row.get('local_status') in ('added','modified') and not row.get('rename_from')]
            if uploads:
                from thlib.side.client.tactic_client_lib.file_workspace import open_local_files
                destination=client.rpc('status',change=destination['code'])
                state['progress']=open_local_files(client,destination,root,cache/'local.sqlite',
                    ((row['source_path'],local_path(root,row['path'])) for row in uploads),cancelled=cancelled.is_set)
        elif operation=='restore_file':
            revision=values['revision']
            client.rpc('restore_file',change=destination['code'],edit_revision=destination['edit_revision'],request_id=uuid.uuid4().hex,path=revision['path'],published_change=revision['change'])
        elif operation=='move_files':
            client.rpc('move_files',change=change['code'],edit_revision=change['edit_revision'],
                target_change=destination['code'],target_edit_revision=destination['edit_revision'],paths=paths,request_id=uuid.uuid4().hex)
        elif operation=='checkout':
            client.rpc('checkout',change=destination['code'],edit_revision=destination['edit_revision'],
                paths=paths,mode=values.get('mode','ordinary'),request_id=uuid.uuid4().hex)
            from thlib.side.client.tactic_client_lib.file_workspace import checkout_local
            checkout_local(client,destination['code'],state['root'],paths=paths,cancelled=cancelled.is_set,materialize=True)
        else:
            client.rpc('edit',change=destination['code'],edit_revision=destination['edit_revision'],
                chunk=uuid.uuid4().hex,operations=[{'path':path,'delete':True} for path in paths])
        state['change']=destination
        state['description']=destination.get('description','')
        return True
    if action in ('rename_file', 'resume_local_moves'):
        from hashlib import sha256
        from thlib.side.client.tactic_client_lib.file_workspace import rename_workspace_file
        if action == 'rename_file':
            if len(rows) != 1:
                raise ValueError('Select one file to rename.')
            source, target = rows[0].get('source_path', rows[0]['path']), values['target']
            key = sha256((change['code']+'\0'+source+'\0'+target).encode()).hexdigest()
            rename_workspace_file(client, change['code'], state['root'], source, target, cache/('move-'+key+'.json'))
        else:
            for journal in cache.glob('move-*.json'):
                if cancelled.is_set():
                    raise InterruptedError('Workspace operation stopped')
                saved = json.loads(journal.read_text(encoding='utf-8'))
                identity = saved['identity']
                rename_workspace_file(client, identity[2], state['root'], identity[4], identity[5], journal)
        state.update(selected=[], selection_ids=[], selection_records={}, file_focus={})
        return True
    if action in ('revert_unchanged', 'revert_unchanged_change'):
        from thlib.side.client.tactic_client_lib.file_workspace import revert_unchanged_files
        if change.get('workspace') != state['workspace']:
            raise ValueError('Choose a changelist in the active workspace.')
        paths = None
        if action == 'revert_unchanged':
            if not rows or any(row.get('parent', change.get('code')) != change.get('code')
                               or row.get('stream', change.get('stream')) != change.get('stream') for row in rows):
                raise ValueError('Select files from one changelist.')
            paths = [row.get('source_path', row['path']) for row in rows]
        state['progress'] = revert_unchanged_files(client, change['code'], state['root'],
            cache/('revert-unchanged-'+uuid.uuid4().hex+'.sqlite'), paths=paths, cancelled=cancelled.is_set)
        state['operation_notice'] = {'level':'INFO', 'message':'Revert unchanged files cancelled. No files were reverted.' if state['progress']['state']=='cancelled'
                                    else 'No unchanged files found.' if not state['progress']['files_done']
                                    else 'Unchanged files reverted. Local files were kept.'}
        state.update(selected=[], selection_ids=[], selection_records={})
    elif action == 'mark_delete':
        if not rows:
            raise ValueError('Select files first.')
        if any(row.get('writable') is False or row.get('stream', change.get('stream')) != change.get('stream')
               or row.get('parent', change.get('code')) != change.get('code') for row in rows):
            raise ValueError('Select writable files from one changelist stream.')
        paths = [row.get('source_path', row['path']) for row in rows]
        client.rpc('edit', change=change['code'], edit_revision=change['edit_revision'],
                   chunk=uuid.uuid4().hex, operations=[{'path': path, 'delete': True} for path in paths])
    elif action == 'delete_change':
        targets = values.get('changes')
        if targets is None:
            selected = selected_rows(state) if scope == 'changes' else []
            if any(row.get('path') or not row.get('code') for row in selected):
                raise ValueError('Select changelist headers')
            targets = [{'change': row['code'], 'edit_revision': row['edit_revision']}
                       for row in (selected or [change])]
        client.rpc(action, changes=targets, request_id=uuid.uuid4().hex)
        state.update(change={}, description='', selected=[], selection_ids=[],
                     selection_records={}, context_row={})
    elif action in ('open_local', 'reveal_local', 'delete_local', 'copy_local_paths'):
        if not rows:
            context = state.get('context_row', {})
            rows = [context] if context.get('path') else []
        if not rows:
            raise ValueError('Select files first.')
        if not state['root']:
            state['progress'] = {'state': 'unavailable', 'reason': 'workspace_root_missing'}
            state['operation_notice'] = {'level': 'WARNING', 'message': 'Choose a local workspace folder first.'}
            return True
        if scope == 'workspace' or scope == 'files' and state['view'] == 'local':
            paths=[local_path(local_root,row.get('local_path',row['path'])) for row in rows]
        else:
            mapped=client.rpc('workspace_paths',workspace=state['workspace'],paths=[
                {'stream':row.get('stream') or change.get('stream') or state['stream'],
                 'path':row.get('source_path',row['path'])} for row in rows])['items']
            if any(row.get('excluded') for row in mapped):
                raise ValueError('The selected file is not mapped to this workspace.')
            paths=[local_path(local_root,row['path']) for row in mapped]
        if action=='copy_local_paths':
            state['clipboard_text']='\n'.join(str(path) for path in paths)
            return True
        if action == 'reveal_local':
            import subprocess
            target = paths[0]
            if not local_root.is_dir():
                state['progress'] = {'state': 'unavailable', 'reason': 'workspace_root_missing', 'path': str(local_root)}
                state['operation_notice'] = {'level': 'WARNING', 'message': 'The local workspace folder does not exist. Use Get Latest to create it.', 'path': str(local_root)}
                return True
            existing_file = target.is_file()
            folder = target.parent
            while not folder.is_dir() and folder != local_root:
                folder = folder.parent
            if os.name == 'nt':
                command = ['explorer.exe', '/select,', str(target)] if existing_file else ['explorer.exe', str(folder)]
            else:
                command = ['xdg-open', str(folder)]
            subprocess.Popen(command)
            state['progress'] = {'state': 'complete', 'path': str(folder)}
            if not existing_file:
                state['operation_notice'] = {'level': 'INFO', 'message': 'Local copy is absent. Opened the nearest existing folder: %1.', 'folder': str(folder), 'path': str(target)}
            return True
        missing = next((path for path in paths if not path.is_file()), None)
        if missing is not None:
            state['progress'] = {'state': 'unavailable', 'reason': 'local_file_missing', 'path': str(missing)}
            state['operation_notice'] = {'level': 'WARNING', 'message': 'Local copy is absent. Use Get Latest to download it if needed.', 'path': str(missing)}
            return True
        if action == 'delete_local':
            for path in paths:
                if cancelled.is_set():raise InterruptedError('Workspace operation stopped')
                success = QFile.moveToTrash(str(path))
                if not success:
                    raise OSError('Could not move the local file to Trash: ' + str(path))
            for row in rows:row['local_status']='missing'
            local_cache=cache/'local.sqlite'
            if local_cache.is_file():
                import sqlite3
                from contextlib import closing
                with closing(sqlite3.connect(local_cache)) as db:
                    for path in paths:
                        key=path.relative_to(Path(state['root']).resolve()).as_posix()
                        cached=db.execute('SELECT data FROM local WHERE path=?',(key,)).fetchone()
                        if cached:
                            data=json.loads(cached[0]);data['local_status']='missing'
                            db.execute('UPDATE local SET data=? WHERE path=?',(json.dumps(data),key))
                    db.commit()
            state['selected'], state['selection_ids'] = [], []
        else:
            if os.name == 'nt':
                for path in paths:
                    os.startfile(path)
            else:
                import subprocess
                for path in paths:
                    subprocess.Popen(['xdg-open', str(path)])
    elif action == 'navigate':
        path = values['path'].strip()
        if path.startswith('//'):
            stream, separator, prefix = path[2:].partition('/')
            if stream not in {row['code'] for row in state['streams']}:
                raise ValueError('Select a stream available in this project.')
            state.update(stream=stream, prefix=prefix, view='depot', files_stream=stream,
                         files_prefix=prefix, files_source='depot', cursors=[])
        else:
            root = Path(state['root']).resolve()
            directory = Path(path).resolve()
            if not directory.is_relative_to(root) or not directory.is_dir():
                raise ValueError('Select a directory inside the active workspace.')
            relative = directory.relative_to(root).as_posix()
            prefix = '' if relative == '.' else relative + '/'
            state.update(prefix=prefix, files_prefix=prefix, files_source='local', view='local', cursors=[])
        history = state['navigation']
        if not values.get('restore'):
            del history[state['navigation_index'] + 1:]
            history.append(values['path'])
            state['navigation'] = history[-100:]
            state['navigation_index'] = len(state['navigation']) - 1
    elif action == 'drop_files':
        target = values['target']
        target_info = client.rpc('status', change=target)
        if target_info.get('workspace')!=state['workspace']:raise ValueError('Drop files into the current workspace.')
        if target_info['state'] != 'pending':
            raise ValueError('Drop files onto a pending changelist.')
        payload = values.get('payload')
        if payload:
            payload = json.loads(payload)
            if payload['workspace'] != state['workspace'] or payload['project'] != values['project']:
                raise ValueError('Drag files within the current project and workspace.')
            selected = payload['rows']
            if not isinstance(selected, list) or not 1 <= len(selected) <= 1000:
                raise ValueError('Drop 1..1000 selected file or folder roots.')
            parents = {row.get('parent') for row in selected}
            local_selection=payload['scope']=='workspace' or payload['scope']=='files' and payload.get('source')=='local'
            if local_selection:
                from itertools import islice
                def local_files():
                    roots=[]
                    for row in selected:
                        kind=row.get('kind','file')
                        if kind not in ('file','directory','workspace'):raise ValueError('Select local files or folders.')
                        name=row.get('local_path') or row.get('directory') or row.get('path','')
                        source=local_root if kind=='workspace' else local_path(local_root,name.rstrip('/'))
                        if not (source.is_file() if kind=='file' else source.is_dir()):
                            raise ValueError('Selected local file or folder is missing: '+str(source))
                        roots.append((source,kind))
                    previous=None;directory=None
                    for source,kind in sorted(roots,key=lambda value:value[0].parts):
                        if cancelled.is_set():raise InterruptedError('Workspace import stopped')
                        if source==previous or directory and source.is_relative_to(directory):continue
                        previous=source
                        if kind=='file':yield source
                        else:
                            directory=source
                            yield from workspace_files(source)
                def local_sources():
                    files=iter(local_files())
                    while True:
                        page=list(islice(files,1000))
                        if not page:break
                        if cancelled.is_set():raise InterruptedError('Workspace import stopped')
                        names=[file.relative_to(local_root).as_posix() for file in page]
                        mappings=client.rpc('workspace_paths',workspace=state['workspace'],paths=[{'local_path':name} for name in names])['items']
                        for file,mapping in zip(page,mappings):
                            if mapping.get('excluded'):continue
                            if not mapping.get('writable') or mapping['stream']!=target_info['stream']:
                                raise ValueError('Select writable files from one changelist stream: '+str(file))
                            yield mapping['source_path'],file
                from thlib.side.client.tactic_client_lib.file_workspace import open_local_files
                state['progress']=open_local_files(client,target_info,local_root,cache/'local.sqlite',
                    local_sources(),cancelled=cancelled.is_set)
            elif len(parents) == 1 and None not in parents and all(row.get('kind','file')=='file' and row.get('change_state','pending')=='pending' for row in selected):
                source = client.rpc('status', change=next(iter(parents)))
                client.rpc('move_files', change=source['code'], edit_revision=source['edit_revision'],
                    target_change=target, target_edit_revision=target_info['edit_revision'],
                    request_id=uuid.uuid4().hex, paths=[row['path'] for row in selected])
            elif all(row.get('state') == 'shelved' for row in selected) and len(selected) == 1:
                client.rpc('unshelve_begin', change=target, edit_revision=target_info['edit_revision'],
                           shelf=selected[0]['code'], request_id=uuid.uuid4().hex)
            else:
                if any(row.get('stream', target_info['stream']) != target_info['stream'] for row in selected):
                    raise ValueError('Select writable files from one changelist stream.')
                paths, directories, local_directories = [], [], []
                for row in selected:
                    kind = row.get('kind', 'file')
                    if kind == 'file':
                        paths.append(row.get('source_path', row['path']))
                    elif kind in ('directory', 'stream', 'workspace'):
                        prefix = row.get('directory', row.get('path', ''))
                        (local_directories if payload['scope'] == 'workspace' else directories).append(prefix)
                    else:
                        raise ValueError('Drop files, folders or one stream into a pending changelist.')
                result = client.rpc('checkout', change=target, edit_revision=target_info['edit_revision'],
                                    request_id=uuid.uuid4().hex, mode='ordinary',
                                    paths=paths, directories=directories, local_directories=local_directories)
                from thlib.side.client.tactic_client_lib.file_workspace import checkout_local
                checkout_local(client,target,state['root'],cancelled=cancelled.is_set,materialize=True)
                state['progress'] = {'state': 'complete', 'files_done': result['paths']}
        else:
            root = local_root
            def imported():
                count=0
                previous_directory=None
                for source in drop_roots:
                    if previous_directory and source.is_relative_to(previous_directory):continue
                    if source.is_dir():
                        previous_directory=source
                        sources=workspace_files(source)
                    else:sources=iter([source])
                    for file in sources:
                        if cancelled.is_set():raise InterruptedError('Workspace import stopped')
                        name=file.resolve().relative_to(root).as_posix()
                        target_file=local_path(root,name)
                        count+=1
                        client.progress({'state':'discovering','files_done':count,'path':str(file)})
                        yield name,target_file
            def mapped_imports():
                from itertools import islice
                files=iter(imported())
                while True:
                    page=list(islice(files,1000))
                    if not page:break
                    mappings=client.rpc('workspace_paths',workspace=state['workspace'],paths=[{'local_path':name} for name,file in page])['items']
                    for (name,file),mapping in zip(page,mappings):
                        if mapping.get('excluded') or not mapping.get('writable') or mapping['stream']!=target_info['stream']:
                            raise ValueError('Drop files into writable mappings of the changelist stream: '+name)
                        yield mapping['source_path'],file
            from thlib.side.client.tactic_client_lib.file_workspace import open_local_files
            state['progress']=open_local_files(client,target_info,root,cache/'local.sqlite',mapped_imports(),cancelled=cancelled.is_set)
        state['change'] = client.rpc('status', change=target)
        state['description'] = state['change'].get('description', '')
    return True
