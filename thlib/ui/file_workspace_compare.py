"""Bounded inline comparison and verified copies for a user-selected desktop tool."""
import base64
from difflib import unified_diff
from hashlib import sha256
from pathlib import Path
import os
import shutil
import subprocess
import uuid

from PySide6.QtCore import QUrl
from thlib.side.client.tactic_client_lib.file_transfer import local_path,fingerprint,SMALL


def compare_files(client,state,cache,values,cancelled):
    mode=values['mode']
    path=values.get('path') or state['context_row'].get('source_path',state['context_row'].get('path'))
    stream=values.get('stream') or state['context_row'].get('stream') or state['change'].get('stream') or state['stream']
    if mode in ('local_head','local_have'):
        mapped=client.rpc('workspace_paths',workspace=state['workspace'],paths=[{'stream':stream,'path':path}])['items'][0]
        if mapped.get('excluded'):
            raise ValueError('The file is not mapped to this workspace.')
        file=local_path(Path(state['root']).resolve(),mapped['path'])
        if not file.is_file():
            raise ValueError('The local file is missing. Sync it first.')
        before=fingerprint(file)
        right={'stream':stream,'path':path}
        if mode=='local_have':
            right.update(workspace=state['workspace'],have=True)
        descriptor=client.rpc('transfer',**right)
        if descriptor.get('published_change'):
            right['published_change']=descriptor['published_change']
        result={'left':{'path':file.as_posix(),'size':before[0]},'right':descriptor,'left_selector':{'local':file.as_posix(),'fingerprint':list(before)},'right_selector':right,'kind':'binary','text':'','identical':None}
        if before[0]<=262144 and descriptor['size']<=262144:
            ours=file.read_bytes()
            theirs=base64.b64decode(client.rpc('read',**right,offset=0,length=262144)['data'])
            if fingerprint(file)!=before:
                raise ValueError('Local file changed; compare it again.')
            result['left']['sha256']=sha256(ours).hexdigest()
            result['identical']=result['left']['sha256']==descriptor['sha256']
            try:
                if b'\0' in ours or b'\0' in theirs:
                    raise UnicodeError()
                result.update(kind='text',text=''.join(unified_diff(theirs.decode('utf-8').splitlines(keepends=True),ours.decode('utf-8').splitlines(keepends=True),fromfile='//'+stream+'/'+path,tofile=file.as_posix())))
            except UnicodeError:
                pass
    else:
        if mode=='revisions':
            rows=[row for row in state['selection_records'].values() if row.get('code') in state['selection_ids']]
            if len(rows)!=2:
                raise ValueError('Select exactly two published revisions.')
            left,right=[{'stream':row['stream'],'path':row['path'],'published_change':row['change']} for row in rows]
        elif mode=='pending_shelf':
            left={'path':path,'stream':stream,'shelf':values['shelf']}
            right={'path':path,'stream':stream,'change':state['change']['code']}
        elif mode=='conflict':
            job=state['change']['integration']
            common={'path':path,'change':state['change']['code'],'integration':job['code'],'edit_revision':state['change']['edit_revision']}
            left={**common,'conflict_side':values.get('left','base')}
            right={**common,'conflict_side':values.get('right','ours')}
        else:
            raise ValueError('Choose a supported comparison.')
        result=client.rpc('compare_files',left=left,right=right)
        result.update(left_selector=left,right_selector=right)
    result['token']=uuid.uuid4().hex
    state['comparison']=result


def external_compare(client,state,cache,values,cancelled):
    comparison=state['comparison']
    application=Path(QUrl(values['application']).toLocalFile())
    if not application.is_file():
        raise ValueError('Choose an installed comparison application.')
    directory=cache/('compare-'+uuid.uuid4().hex)
    directory.mkdir(parents=True)
    required=sum(comparison[side].get('size',0) for side in ('left','right') if 'local' not in comparison[side+'_selector'])
    if required>shutil.disk_usage(directory).free:
        raise ValueError('Not enough free disk space for comparison copies.')
    try:
        files=[]
        for side in ('left','right'):
            selector=comparison[side+'_selector']
            descriptor=comparison[side]
            if 'local' in selector:
                file=Path(selector['local'])
                if list(fingerprint(file))!=selector['fingerprint']:
                    raise ValueError('Local file changed; compare it again.')
            else:
                file=directory/(side+Path(descriptor['path']).suffix)
                if descriptor.get('deleted') or descriptor.get('absent'):
                    file.write_bytes(b'')
                    files.append(file.as_posix())
                    continue
                digest,size=sha256(),0
                with client.open('download',**selector) as source,file.open('xb') as output:
                    while True:
                        if cancelled.is_set():
                            raise InterruptedError('Comparison download stopped')
                        block=source.read(SMALL)
                        if not block:
                            break
                        output.write(block);digest.update(block);size+=len(block)
                        client.progress({'state':'downloading','path':descriptor['path'],'bytes_done':size,'bytes_total':descriptor['size'],'total_known':True})
                    output.flush();os.fsync(output.fileno())
                if size!=descriptor['size'] or digest.hexdigest()!=descriptor.get('sha256'):
                    file.unlink(missing_ok=True)
                    raise ValueError('Server revision changed; compare it again.')
            files.append(file.as_posix())
    except Exception:
        shutil.rmtree(directory)
        raise
    # shortcut: detached viewers keep their copies in the workspace cache; add retention when cache cleanup is implemented.
    subprocess.Popen([str(application),*files])
