"""Owned desktop operation journals, reconnect and explicit transfer recovery."""
from contextlib import closing
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sqlite3
import time
import uuid


def cache_directory(base, server: str, owner: str, project: str, workspace: str, root: str) -> Path:
    identity=sha256(('\0'.join((server,str(owner),project,workspace,root))).encode()).hexdigest()
    return Path(base)/'cache/file_workspaces'/identity


RECOVERABLE={'shelve','shelve_selected','shelve_revert','update_shelf','get_latest','get_revision','sync_selected','sync_folder',
             'submit','bulk_query','bulk_target','bulk_resume','rename_file','resume_local_moves','target_files','drop_files'}


def save_operation(cache: Path, values: dict, filename: str='operation'):
    from thlib.environment import env_write_config
    env_write_config(values,unique_id='cache/file_workspaces/'+cache.name,filename=filename,long_abs_path=True)


def operation_context(state: dict, action: str, values: dict) -> dict:
    fields=('workspace','root','stream','view','prefix','selection_scope','selected','context_row','selection_query')
    context={key:deepcopy(state[key]) for key in fields}
    context['change']={key:value for key,value in state['change'].items() if key in ('code','edit_revision','stream','workspace','state','number','description')}
    references=('path','source_path','local_path','kind','stream','parent','workspace','change_state','fingerprint',
                'sha256','size','local_status','rename_from','rename_local','rename_target')
    context['selection_ids']=list(state['selection_ids'])
    context['selection_records']={identity:{key:value for key,value in row.items() if key in references}
                                  for identity,row in state['selection_records'].items()}
    context['description']=state['description']
    if 'urls' in values:
        values={**values,'urls':[url.toString() if hasattr(url,'toString') else str(url) for url in values['urls']]}
    return {'action':action,'values':deepcopy(values),'snapshot':context,'created_at':time.time()}


def load_operation(cache: Path, state: dict) -> dict:
    from thlib.environment import env_read_config
    key='cache/file_workspaces/'+cache.name
    request=env_read_config(unique_id=key,filename='operation',long_abs_path=True) or {}
    if not request:return {}
    snapshot=request.get('snapshot',{})
    if snapshot.get('workspace')!=state['workspace'] or snapshot.get('root')!=state['root'] or request.get('action') not in RECOVERABLE:
        return {}
    return {**request,'progress':env_read_config(unique_id=key,filename='operation_progress',long_abs_path=True) or {}}


def resume_operation(client, state: dict, cache: Path, cancelled) -> tuple[str, dict]:
    saved=state.get('recovery') or {}
    if not saved.get('action'):saved=load_operation(cache,state)
    if not saved:raise ValueError('No interrupted operation in this workspace.')
    snapshot=saved['snapshot']
    if (snapshot['workspace'],snapshot['root'])!=(state['workspace'],state['root']):
        raise ValueError('Recovery belongs to another workspace.')
    progress=saved.get('progress',{})
    if progress.get('change'):
        state['change']=client.rpc('status',change=progress['change'])
        state['description']=state['change'].get('description','')
    if saved['action'] in ('rename_file','resume_local_moves'):
        return 'resume_local_moves',{}
    if progress.get('task'):
        status=client.rpc('transfer_status',task=progress['task'])
        if status['kind']=='mutation':
            if status['state']=='error':
                state.update(deepcopy(snapshot));return saved['action'],saved['values']
            state['progress']=client.wait_bulk(status['task']);return 'refresh',{}
        if status['kind']=='download':
            state['progress']=client.download(state['workspace'],state['root'],task=status['task'])
            if state['progress'].get('state')=='blocked':state['operation_blocked']=True
            return 'refresh',{}
        journal=Path(progress.get('journal',''))
        if not journal.is_file():raise ValueError('Upload journal is missing; keep it to resume this task.')
        if status['state'] in ('error','expired','cancelled'):
            journal=Path(progress.get('source_journal') or journal)
            client.progress({'state':'discovering','source_journal':str(journal),'change':status['change']})
            root=Path(state['root']).resolve()
            if not journal.resolve().is_relative_to(cache.resolve()):raise ValueError('Upload journal is outside this workspace cache.')
            with closing(sqlite3.connect(journal)) as db:
                from thlib.side.client.tactic_client_lib.file_transfer import local_path
                sources=((name,local_path(root,local)) for name,local in db.execute('SELECT path,local_path FROM sources ORDER BY path'))
                state['progress']=client.upload(status['change'],root,cache/('retry-'+uuid.uuid4().hex+'.sqlite'),sources=sources)
        else:
            state['progress']=client.upload(status['change'],state['root'],journal)
        state['change']=client.rpc('status',change=status['change'])
        state['description']=state['change'].get('description','')
        return 'refresh',{}
    if progress.get('source_journal') and not progress.get('task'):
        journal=Path(progress['source_journal'])
        if not journal.resolve().is_relative_to(cache.resolve()):raise ValueError('Upload journal is outside this workspace cache.')
        with closing(sqlite3.connect(journal)) as db:
            from thlib.side.client.tactic_client_lib.file_transfer import local_path
            sources=((name,local_path(Path(state['root']).resolve(),local)) for name,local in db.execute('SELECT path,local_path FROM sources ORDER BY path'))
            state['progress']=client.upload(progress.get('change') or snapshot['change']['code'],state['root'],cache/('retry-'+uuid.uuid4().hex+'.sqlite'),sources=sources)
        return 'refresh',{}
    if progress.get('journal'):
        journal=Path(progress['journal'])
        if not journal.resolve().is_relative_to(cache.resolve()):raise ValueError('Upload journal is outside this workspace cache.')
        with closing(sqlite3.connect(journal)) as db:
            scanned=db.execute("SELECT value FROM meta WHERE key='scanned'").fetchone()
        if scanned and scanned[0]=='true':
            state['progress']=client.upload(progress.get('change') or snapshot['change']['code'],state['root'],journal)
            return 'refresh',{}
    state.update(deepcopy(snapshot))
    state['resuming_operation']=True
    if saved['action'] in ('submit','shelve','shelve_selected','shelve_revert','update_shelf'):
        current=client.rpc('status',change=state['change']['code'])
        state.update(change=current,description=current.get('description',''))
        if current['state']=='submitted':state.update(state='submitted',view='change');return 'refresh',{}
        return 'review_change',{'operation':saved['action'],**saved['values']}
    return saved['action'],saved['values']
