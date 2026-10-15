"""Worker-only metadata revert and optional bounded, recoverable local cleanup."""
from contextlib import closing
from pathlib import Path
import sqlite3
import uuid

from PySide6.QtCore import QFile
from thlib.side.client.tactic_client_lib.file_transfer import local_path


def revert_files(client, state, cache, action, values, cancelled):
    delete=values.get('delete_not_in_depot',False)
    if not isinstance(delete,bool):raise ValueError('Choose a boolean local cleanup option')
    if delete and (not state['root'] or not Path(state['root']).is_absolute()):
        raise ValueError('Choose an absolute workspace root before deleting local files')
    workspace=state['workspace'];root=Path(state['root']).resolve()
    full=action=='revert'
    change=values.get('change') or state['change'].get('code')
    revision=values.get('edit_revision',state['change'].get('edit_revision'))
    request=uuid.uuid4().hex
    if not delete:
        if cancelled.is_set():raise InterruptedError('Revert stopped')
        if full:client.rpc('revert',change=change,edit_revision=revision,request_id=request)
        else:
            plan=client.rpc('revert_plan',workspace=workspace,files=values['files'])
            if cancelled.is_set():raise InterruptedError('Revert stopped')
            client.rpc('revert_files',workspace=workspace,groups=plan['groups'],request_id=request)
        return
    journal=cache/('revert-'+request+'.sqlite')
    skipped=deleted=0;groups=None
    try:
        with closing(sqlite3.connect(journal)) as db:
            db.execute('CREATE TABLE cleanup (stream TEXT,path TEXT,local TEXT,size INTEGER,mtime INTEGER,inode INTEGER, PRIMARY KEY(stream,path))')
            after=''
            while delete or not full:
                if cancelled.is_set():raise InterruptedError('Revert stopped')
                options={'change':change,'edit_revision':revision,'after':after,'limit':1000} if full else {'files':values['files']}
                plan=client.rpc('revert_plan',workspace=workspace,**options)
                groups=plan['groups']
                if delete:
                    for row in plan['items']:
                        if not row['delete_local'] or not row['local_path']:continue
                        file=local_path(root,row['local_path'])
                        if not file.is_file():continue
                        stat=file.stat()
                        db.execute('INSERT OR IGNORE INTO cleanup VALUES (?,?,?,?,?,?)',
                            (row['stream'],row['path'],row['local_path'],stat.st_size,stat.st_mtime_ns,stat.st_ino))
                    db.commit()
                after=plan.get('after')
                if not full or not after:break
            if cancelled.is_set():raise InterruptedError('Revert stopped')
            if full:
                client.rpc('revert',change=change,edit_revision=revision,request_id=request)
            else:
                client.rpc('revert_files',workspace=workspace,groups=groups,request_id=request)
            # Never touch local bytes before the native transaction successfully commits.
            total=db.execute('SELECT COUNT(*) FROM cleanup').fetchone()[0]
            processed=0;stopped=False
            cursor=db.execute('SELECT stream,path,local,size,mtime,inode FROM cleanup ORDER BY stream,path')
            while True:
                batch=cursor.fetchmany(1000)
                if not batch:break
                if cancelled.is_set():skipped+=total-processed;break
                states=client.rpc('file_states',workspace=workspace,
                    paths=[{'stream':row[0],'path':row[1]} for row in batch])['items']
                for record,server in zip(batch,states):
                    if cancelled.is_set():
                        skipped+=total-processed;stopped=True;break
                    processed+=1
                    stream,path,name,size,mtime,inode=record
                    head=server.get('head')
                    if (head and not head.get('deleted') or server.get('local_path')!=name
                            or any(holder.get('workspace')==workspace for holder in server['holders'])):
                        skipped+=1;continue
                    try:
                        file=local_path(root,name)
                        if not file.is_file():continue
                        stat=file.stat()
                        if (stat.st_size,stat.st_mtime_ns,stat.st_ino)!=(size,mtime,inode):
                            skipped+=1;continue
                        success=QFile.moveToTrash(str(file))
                    except (OSError,ValueError):
                        skipped+=1;continue
                    if isinstance(success,tuple):success=success[0]
                    if success:deleted+=1
                    else:skipped+=1
                if stopped:break
            state['progress']={'state':'complete','files_done':processed,'files_total':total,'deleted_files':deleted,'files_kept':skipped,'total_known':True}
            if delete:state['local_dirty']=True
            if skipped:
                state['operation_notice']={'level':'WARNING','message':'Revert completed. Some local files were kept because cleanup stopped, they changed or could not be moved to Trash.'}
    finally:
        if journal.exists():journal.unlink()
