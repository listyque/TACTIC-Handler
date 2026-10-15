"""Bounded local reconciliation for GUI clients; all server state uses native commands."""
from contextlib import closing, nullcontext
from pathlib import Path
from fnmatch import fnmatchcase
import json
import os
import sqlite3
import uuid

from .file_transfer import digest_file, fingerprint, local_path


def revert_unchanged_files(client, change, root, journal, *, paths=None, cancelled=lambda: False):
    """Compare against checkout bases, then remove only matching opens; keep local bytes."""
    root, journal = Path(root), Path(journal)
    if not root.is_absolute():
        raise ValueError('Choose an absolute workspace root')
    root = root.resolve()
    if journal.resolve().is_relative_to(root):
        raise ValueError('Keep the comparison journal outside the workspace')
    status = client.rpc('status', change=change)
    revision = status['edit_revision']
    if status['state'] != 'pending' or status.get('active_transfer') or status.get('active_bulk') or status.get('integration'):
        raise ValueError('Choose an idle pending changelist')
    if paths is not None:
        paths = set(paths)
    journal.parent.mkdir(parents=True, exist_ok=True)
    scanned = count = 0
    task = None
    try:
        with closing(sqlite3.connect(journal)) as db:
            db.execute('CREATE TABLE candidates (path TEXT PRIMARY KEY, local TEXT NOT NULL, sha TEXT NOT NULL)')
            after = ''
            while True:
                if cancelled():
                    raise InterruptedError('Revert unchanged files stopped')
                page = client.rpc('change_files', change=change, edit_revision=revision, after=after, limit=1000)
                rows = [row for row in page['items'] if row.get('action') in ('checkout', 'write')
                        and (row.get('base') or {}).get('sha256') and not row['base'].get('deleted')
                        and (paths is None or row['path'] in paths)]
                if rows:
                    mapped = client.rpc('workspace_paths', workspace=status['workspace'],
                        paths=[{'stream':status['stream'], 'path':row['path']} for row in rows])['items']
                    for index, (row, mapping) in enumerate(zip(rows, mapped), 1):
                        if cancelled():
                            raise InterruptedError('Revert unchanged files stopped')
                        if mapping.get('excluded') or not mapping.get('writable'):
                            continue
                        client.progress({'state':'preparing', 'files_done':scanned+index-1, 'files_total':page['files'], 'total_known':True, 'path':mapping['path']})
                        file = local_path(root, mapping['path'])
                        if not file.is_file():
                            continue
                        before = fingerprint(file)
                        digest = digest_file(file, cancelled=cancelled)
                        if before == fingerprint(file) and digest == row['base']['sha256']:
                            db.execute('INSERT INTO candidates VALUES (?,?,?)', (row['path'], mapping['path'], digest))
                            count += 1
                scanned += len(page['items'])
                client.progress({'state':'preparing', 'files_done':scanned, 'files_total':page['files'], 'total_known':True})
                db.commit()
                after = page['after']
                if not after:
                    break
            if not count:
                return {'state':'complete', 'files_done':0, 'files_total':0, 'total_known':True}
            # Recheck every candidate before releasing any checkout, including earlier pages.
            for name, digest in db.execute('SELECT local,sha FROM candidates ORDER BY path'):
                if cancelled():
                    raise InterruptedError('Revert unchanged files stopped')
                file = local_path(root, name)
                if not file.is_file() or digest_file(file, cancelled=cancelled) != digest:
                    raise ValueError('Local file changed during comparison; retry Revert unchanged files: ' + name)
            request = uuid.uuid4().hex
            if count <= 1000:
                if cancelled():
                    raise InterruptedError('Revert unchanged files stopped')
                client.rpc('remove_files', change=change, edit_revision=revision, request_id=request,
                    paths=[row[0] for row in db.execute('SELECT path FROM candidates ORDER BY path')])
                return {'state':'complete', 'files_done':count, 'files_total':count, 'total_known':True}
            if not client.rpc('capabilities')['files_service_configured']:
                raise ValueError('Enable the files service before starting server bulk operations.')
            cursor = db.execute('SELECT path,sha FROM candidates ORDER BY path')
            selection = None
            chunk = 0
            while batch := cursor.fetchmany(1000):
                if cancelled():
                    raise InterruptedError('Revert unchanged files stopped')
                selection = client.rpc('select_unchanged', change=change, edit_revision=revision,
                    selection=selection, request_id=request+'-'+str(chunk),
                    files=[{'path':path, 'sha256':digest} for path,digest in batch])['selection']
                chunk += 1
            if cancelled():
                raise InterruptedError('Revert unchanged files stopped')
            task = client.rpc('bulk_begin', change=change, edit_revision=revision, selection=selection,
                operation='remove_files', request_id=request)['task']
            return client.wait_bulk(task)
    except InterruptedError:
        if task:
            client.rpc('bulk_cancel', task=task)
        raise
    finally:
        if journal.exists():
            journal.unlink()


def workspace_files(root, *, directory=None):
    entries=[os.scandir(root)]
    try:
        while entries:
            try:entry=next(entries[-1])
            except StopIteration:
                entries.pop().close()
                continue
            if entry.is_symlink():
                raise ValueError('Workspace scan does not follow symlinks: ' + entry.path)
            if entry.is_dir(follow_symlinks=False):
                if directory:
                    if directory(Path(entry.path)) is False:
                        continue
                entries.append(os.scandir(entry.path))
            elif entry.is_file(follow_symlinks=False):
                yield Path(entry.path)
    finally:
        for iterator in entries:iterator.close()


def open_local_files(client, change, root, cache, sources, *, cancelled=lambda: False):
    """Open paths and cache comparisons in bounded batches; never transfer contents."""
    from itertools import islice
    root, cache = Path(root).resolve(), Path(cache)
    if cache.resolve().is_relative_to(root):
        raise ValueError('Reconciliation cache must be outside the workspace')
    cache.parent.mkdir(parents=True, exist_ok=True)
    workspace = client.rpc('workspace_status', workspace=change['workspace'])
    revision, count, heads = change['edit_revision'], 0, {}
    sources = iter(sources)
    with closing(sqlite3.connect(cache)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS local (path TEXT PRIMARY KEY, data TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS directories (path TEXT PRIMARY KEY)')
        while True:
            page = list(islice(sources, 1000))
            if not page:
                break
            descriptors, fingerprints = [], {}
            for path, source in page:
                if cancelled():
                    raise InterruptedError('Local preparation stopped')
                name = source.resolve().relative_to(root).as_posix()
                file = local_path(root, name)
                before = fingerprint(file)
                digest = digest_file(file, cancelled=cancelled)
                if before != fingerprint(file):
                    raise ValueError('Local file changed during preparation: ' + name)
                fingerprints[name] = list(before)
                descriptors.append({'path':name, 'size':before[0], 'sha256':digest})
            result = client.rpc('checkout', change=change['code'], edit_revision=revision,
                request_id=uuid.uuid4().hex, mode='ordinary', paths=[path for path, source in page])
            revision = result['edit_revision']
            comparison = client.rpc('reconcile', workspace=change['workspace'], files=descriptors,
                heads=heads, have_root=workspace['have_root'], view_revision=workspace.get('view_revision', 0))
            heads.update(comparison['heads'])
            for row, descriptor in zip(comparison['items'], descriptors):
                head = row.get('head') or {}
                row.update(descriptor, fingerprint=fingerprints[row['path']])
                # Without Have, compare an existing local copy with published Head.
                if not row.get('have') and head and not head.get('deleted'):
                    row['local_status'] = 'clean' if descriptor['sha256'] == head['sha256'] else 'modified'
                db.execute('INSERT OR REPLACE INTO local VALUES (?,?)', (row['path'], json.dumps(row)))
                parent = Path(row['path']).parent
                while parent.as_posix() != '.':
                    db.execute('INSERT OR IGNORE INTO directories VALUES (?)', (parent.as_posix()+'/',))
                    parent = parent.parent
            db.execute("INSERT OR REPLACE INTO meta VALUES ('summary_valid','false')")
            db.commit()
            count += len(page)
            client.progress({'state':'preparing', 'files_done':count, 'total_known':False})
    return {'state':'complete', 'files_done':count, 'edit_revision':revision}


def reconcile_workspace(client, workspace, root, cache, *, cancelled=lambda: False):
    root = Path(root).resolve()
    cache = Path(cache).resolve()
    if cache.is_relative_to(root):
        raise ValueError('Reconciliation cache must be outside the workspace')
    cache.parent.mkdir(parents=True, exist_ok=True)
    ws = client.rpc('workspace_status', workspace=workspace)
    ignore_file = root / '.tacticignore'
    rules = []
    if ignore_file.is_file():
        if ignore_file.stat().st_size > 1048576:
            raise ValueError('Workspace ignore file exceeds 1 MiB')
        rules = [line.strip() for line in ignore_file.read_text(encoding='utf-8').splitlines() if line.strip() and not line.lstrip().startswith('#')]
    def ignored(path):
        matched = None
        for rule in rules:
            pattern = rule.lstrip('!').lstrip('/').rstrip('/')
            if fnmatchcase(path, pattern) or '/' not in pattern and any(fnmatchcase(part, pattern) for part in path.split('/')):
                matched = None if rule.startswith('!') else rule
        return matched
    heads, count, fingerprints, summary = {}, 0, {}, {}
    with closing(sqlite3.connect(cache)) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA temp_store=FILE')
        db.execute('CREATE TABLE IF NOT EXISTS local (path TEXT PRIMARY KEY, data TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS directories (path TEXT PRIMARY KEY)')
        db.execute('DROP TABLE IF EXISTS local_next')
        db.execute('DROP TABLE IF EXISTS directories_next')
        db.execute('CREATE TABLE local_next (path TEXT PRIMARY KEY, data TEXT NOT NULL)')
        db.execute('CREATE TABLE directories_next (path TEXT PRIMARY KEY)')
        db.execute('CREATE TEMP TABLE change_counts (code TEXT PRIMARY KEY, revision INTEGER, files INTEGER, bytes INTEGER, valid INTEGER)')
        db.commit()

        def flush(files):
            nonlocal heads, count
            if cancelled():
                raise InterruptedError('Workspace scan stopped')
            result = client.rpc('reconcile', workspace=workspace, files=files, heads=heads,
                                have_root=ws['have_root'], view_revision=ws.get('view_revision', 0))
            heads.update(result['heads'])
            descriptors = {item['path']: item for item in files}
            for item in result['items']:
                item['fingerprint']=fingerprints.get(item['path'])
                item.update({key: descriptors[item['path']][key] for key in ('size', 'sha256') if key in descriptors[item['path']]})
                if item.get('stream') and item['local_status'] in ('modified','missing','added'):
                    counts=summary.setdefault(item['stream'],{'files':0,'bytes':0,'modified':0,'missing':0,'added':0})
                    counts[item['local_status']]+=1;counts['files']+=1;counts['bytes']+=item.get('size',0)
                for pending in item.get('pending',[]):
                    dirty=not pending['staged_current']
                    db.execute('INSERT INTO change_counts VALUES (?,?,?,?,1) ON CONFLICT(code) DO UPDATE SET files=files+excluded.files,bytes=bytes+excluded.bytes,valid=valid AND revision=excluded.revision',
                        (pending['change'],pending['edit_revision'],int(dirty),item.get('size',0) if dirty else 0))
            db.executemany('INSERT INTO local_next VALUES (?,?)', [(item['path'], json.dumps(item)) for item in result['items']])
            count += len(files)
            fingerprints.clear()
            db.commit()
            client.progress({'state': 'reconciling', 'files_done': count, 'path': files[-1]['path'], 'total_known': False})

        chunk = []
        directories = 0
        def directory(path):
            nonlocal directories
            if cancelled():
                raise InterruptedError('Workspace scan stopped')
            db.execute('INSERT INTO directories_next VALUES (?)', (path.relative_to(root).as_posix() + '/',))
            rule = ignored(path.relative_to(root).as_posix())
            if rule and not any(pattern.startswith('!') for pattern in rules):
                return False
            directories += 1
            if directories % 1000 == 0:
                db.commit()
                client.progress({'state':'reconciling','files_done':count,'directories_done':directories,'path':str(path),'total_known':False})
        for path in workspace_files(root, directory=directory):
            if cancelled():
                raise InterruptedError('Workspace scan stopped')
            relative = path.relative_to(root).as_posix()
            rule = ignored(relative)
            if rule:
                db.execute('INSERT INTO local_next VALUES (?,?)', (relative, json.dumps({'path':relative,
                    'local_status':'ignored','server_status':'ignored','writable':False,'ignore_rule':rule})))
                continue
            before = fingerprint(path)
            digest = digest_file(path, cancelled=cancelled)
            if fingerprint(path) != before:
                raise ValueError('Local file changed during reconciliation: ' + str(path))
            fingerprints[path.relative_to(root).as_posix()]=list(before)
            chunk.append({'path': path.relative_to(root).as_posix(), 'size': before[0], 'sha256': digest})
            if len(chunk) == 1000:
                flush(chunk)
                chunk = []
        if chunk:
            flush(chunk)
        after = ''
        while True:
            if cancelled():
                raise InterruptedError('Workspace scan stopped')
            page = client.rpc('have', workspace=workspace, after=after, root=ws['have_root'])
            missing = [{'path': entry.get('local_path', entry['path']), 'missing': True} for entry in page['items']
                       if not ignored(entry.get('local_path', entry['path'])) and not local_path(root, entry.get('local_path', entry['path'])).exists()]
            if missing:
                flush(missing)
            after = page['after']
            if not after:
                break
        # Unique content pairs are rename candidates; ambiguous copies stay add/delete.
        db.execute('CREATE TEMP TABLE rename_candidates (path TEXT, stream TEXT, digest TEXT, status TEXT)')
        db.execute("INSERT INTO rename_candidates SELECT path,json_extract(data,'$.stream'),CASE WHEN json_extract(data,'$.local_status')='missing' THEN json_extract(data,'$.have.sha256') ELSE json_extract(data,'$.sha256') END,json_extract(data,'$.local_status') FROM local_next WHERE json_extract(data,'$.local_status') IN ('added','missing') AND json_extract(data,'$.writable')=1")
        db.execute('CREATE INDEX rename_digest ON rename_candidates(stream,digest,status)')
        pairs = db.execute("SELECT min(CASE WHEN status='added' THEN path END),min(CASE WHEN status='missing' THEN path END) FROM rename_candidates WHERE digest IS NOT NULL GROUP BY stream,digest HAVING sum(status='added')=1 AND sum(status='missing')=1")
        for added, missing in pairs:
            if cancelled():
                raise InterruptedError('Workspace scan stopped')
            fresh = json.loads(db.execute('SELECT data FROM local_next WHERE path=?',(added,)).fetchone()[0])
            previous = json.loads(db.execute('SELECT data FROM local_next WHERE path=?',(missing,)).fetchone()[0])
            fresh.update(reconcile_action='rename',rename_from=previous['source_path'],rename_local=missing)
            previous['rename_target'] = fresh['source_path']
            db.executemany('UPDATE local_next SET data=? WHERE path=?',[(json.dumps(fresh),added),(json.dumps(previous),missing)])
        if cancelled():
            raise InterruptedError('Workspace scan stopped')
        db.execute('DROP TABLE local')
        db.execute('ALTER TABLE local_next RENAME TO local')
        db.execute('DROP TABLE directories')
        db.execute('ALTER TABLE directories_next RENAME TO directories')
        db.execute("INSERT OR REPLACE INTO meta VALUES ('state','complete')")
        db.execute("DELETE FROM meta WHERE name LIKE 'summary/%'")
        db.executemany('INSERT INTO meta VALUES (?,?)', [('summary/'+stream,json.dumps(values)) for stream,values in summary.items()])
        db.execute("DELETE FROM meta WHERE name LIKE 'change_summary/%'")
        db.executemany('INSERT INTO meta VALUES (?,?)', (('change_summary/'+code,json.dumps({'known':bool(valid),'edit_revision':revision,'files':files,'bytes':size}))
            for code,revision,files,size,valid in db.execute('SELECT code,revision,files,bytes,valid FROM change_counts')))
        db.execute("INSERT OR REPLACE INTO meta VALUES ('summary_valid','true')")
        db.commit()
    return {'state': 'complete', 'files_done': count, 'workspace': workspace}


def local_page(cache, after='', *, changes_only=True, limit=200, prefix='', local_changes_only=False):
    if not Path(cache).is_file():
        return {'items': [], 'after': None}
    with closing(sqlite3.connect(cache)) as db:
        condition=" AND json_extract(data,'$.local_status') IN ('added','modified','missing')" if local_changes_only else ''
        rows = db.execute('SELECT path,data FROM local WHERE path>? AND path>=? AND (?="" OR path<?)'+condition+' ORDER BY path LIMIT ?',
                          (after, prefix, prefix, prefix + '\U0010ffff', limit + 1)).fetchall()
    items = [json.loads(data) for _, data in rows[:limit]]
    if changes_only:
        items = [item for item in items if item['local_status'] != 'clean' or item['server_status'] != 'current']
    return {'items': items, 'after': rows[limit - 1][0] if len(rows) > limit else None}


def local_browse(cache, directory='', after='', limit=200):
    """Seek immediate cached children, skipping whole descendant ranges."""
    if directory and not directory.endswith('/') or not 1 <= limit <= 1000:
        raise ValueError('Choose a directory and a bounded page')
    if after and (not after.startswith(directory) or '/' in after[len(directory):].rstrip('/')):
        raise ValueError('Directory cursor must be an immediate child')
    if not Path(cache).is_file():
        return {'items': [], 'after': None}
    items = []
    start = after[:-1] + '0' if after.endswith('/') else after
    after = after or directory
    with closing(sqlite3.connect(cache)) as db:
        has_directories = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='directories'").fetchone()
        while len(items) <= limit:
            row = db.execute('SELECT path,data FROM local WHERE path>? AND path>=? AND (?="" OR path<?) ORDER BY path LIMIT 1',
                             (after, max(start, directory), directory, directory + '\U0010ffff')).fetchone()
            folder = db.execute('SELECT path FROM directories WHERE path>? AND path>=? AND (?="" OR path<?) ORDER BY path LIMIT 1',
                                (after, max(start,directory), directory, directory+'\U0010ffff')).fetchone() if has_directories else None
            if folder and (not row or folder[0] < row[0]):
                row = (folder[0], '{}')
            if not row:
                break
            path = directory + row[0][len(directory):].split('/', 1)[0]
            if row[0] == path:
                items.append({**json.loads(row[1]), 'kind': 'file', 'name': path[len(directory):]})
                after, start = path, path
            else:
                items.append({'kind': 'directory', 'name': path[len(directory):], 'path': path + '/'})
                after, start = '', path + '0'
    return {'items': items[:limit], 'after': items[limit - 1]['path'] if len(items) > limit else None}


def local_sources(cache, root, stream, paths=None):
    """Read a disk cursor instead of retaining a million paths in the GUI."""
    with closing(sqlite3.connect(cache)) as db:
        state = db.execute("SELECT value FROM meta WHERE name='state'").fetchone()
        if not state or state[0] != 'complete':
            raise ValueError('Finish workspace reconciliation before uploading.')
        for _, data in db.execute('SELECT path,data FROM local ORDER BY path'):
            item = json.loads(data)
            if (item.get('stream') == stream and item.get('writable') and item['local_status'] in ('added', 'modified')
                    and (paths is None or item['path'] in paths)):
                yield item['source_path'], local_path(Path(root).resolve(), item['path'])


def rename_workspace_file(client, change, root, source, target, journal):
    """Replay the native receipt before a local move; never overwrite another copy."""
    root, journal = Path(root).resolve(), Path(journal)
    identity = [client.url, client.project, change, str(root), source, target]
    local_path(root, source);local_path(root, target)
    if journal.exists():
        if journal.is_symlink() or journal.stat().st_size > 32768:
            raise ValueError('Unsafe local move journal')
        saved = json.loads(journal.read_text(encoding='utf-8'))
        if saved['identity'] != identity:
            raise ValueError('Local move journal belongs to another operation')
    else:
        info = client.rpc('status', change=change)
        mapped = client.rpc('workspace_paths', workspace=info['workspace'], paths=[
            {'stream':info['stream'], 'path':path} for path in (source, target)])['items']
        if any(row.get('excluded') or not row.get('writable') for row in mapped):
            raise ValueError('Rename requires writable workspace mappings')
        before, after = [local_path(root, row['path']) for row in mapped]
        if not before.is_file():
            raise ValueError('Local copy is absent. Get Latest before renaming: ' + str(before))
        if after.exists() or after.is_symlink():
            raise ValueError('Local rename destination already exists: ' + str(after))
        saved = {'identity':identity, 'source':mapped[0]['path'], 'target':mapped[1]['path'],
                 'edit_revision':info['edit_revision'], 'request_id':uuid.uuid4().hex}
        journal.parent.mkdir(parents=True, exist_ok=True)
        with journal.open('x', encoding='utf-8') as output:
            json.dump(saved, output)
            output.flush();os.fsync(output.fileno())
    result = client.rpc('rename_files', change=change, edit_revision=saved['edit_revision'],
                        request_id=saved['request_id'], renames=[{'source':source, 'target':target}])
    before, after = [local_path(root, saved[key]) for key in ('source', 'target')]
    if before.exists():
        fingerprint(before)
        after.parent.mkdir(parents=True, exist_ok=True)
        # A hard link refuses an existing destination and retains bytes if unlink is interrupted.
        if not after.exists():
            os.link(before, after)
        if after.is_symlink() or not os.path.samefile(before, after):
            raise ValueError('Local rename destination already exists: ' + str(after))
        before.unlink()
    elif not after.is_file():
        raise ValueError('Local move copies are missing; keep the journal and restore the local file.')
    journal.unlink()
    return result


def cache_prepared_change(cache, review):
    """Retain the reviewed fingerprints so uploaded files are not marked dirty by old cache entries."""
    if not Path(cache).is_file():
        return
    with closing(sqlite3.connect(cache)) as db, closing(sqlite3.connect(review)) as inspected:
        for name, digest, observed in inspected.execute('SELECT local,sha,fingerprint FROM files WHERE selected=1'):
            cached=db.execute('SELECT data FROM local WHERE path=?',(name,)).fetchone()
            if cached:
                data=json.loads(cached[0])
                data.update(sha256=digest,fingerprint=json.loads(observed))
                db.execute('UPDATE local SET data=? WHERE path=?',(json.dumps(data),name))
        db.commit()


def inspect_local(cache, root, rows):
    """Inspect only loaded rows; content comparison stays with Reconcile."""
    root=Path(root).resolve()
    with closing(sqlite3.connect(cache)) if Path(cache).is_file() else nullcontext(None) as db:
        for row in rows:
            if row.get('excluded'):
                row['local_status']='unmapped'
                continue
            path=row.get('local_path')
            if not path:continue
            local=local_path(root,path)
            cached=db.execute('SELECT data FROM local WHERE path=?',(path,)).fetchone() if db else None
            data=json.loads(cached[0]) if cached else {}
            if not local.is_file():row['local_status']='missing'
            elif data.get('fingerprint') and list(fingerprint(local))!=data['fingerprint']:row['local_status']='modified'
            elif data:row['local_status']=data['local_status']
            have = row.get('have') or data.get('have') or {}
            row['local_number'] = have.get('number') if local.is_file() else None
            row['local_modified'] = row.get('local_status') in ('modified','added','untracked')
            staged = row.get('file') or {}
            if row.get('action') in ('write', 'move/add'):
                if data.get('fingerprint'):
                    row['staged_current'] = bool(data.get('sha256') == staged.get('sha256') and local.is_file() and
                                                 list(fingerprint(local)) == data['fingerprint'])
                elif data.get('local_status') in ('modified','missing'):
                    row['staged_current'] = False
                else:
                    row['staged_current'] = None
                if row['staged_current'] is False:
                    row['server_status'] = 'modified_after_upload'
    return rows


def local_change_counts(cache, stream):
    """Count indexed local edits without walking the workspace or fetching its files."""
    if not Path(cache).is_file():
        return {'known':False, 'files':None, 'bytes':None, 'modified':None, 'missing':None, 'added':None}
    with closing(sqlite3.connect(cache)) as db:
        valid=db.execute("SELECT value FROM meta WHERE name='summary_valid'").fetchone()
        counts=db.execute('SELECT value FROM meta WHERE name=?',('summary/'+stream,)).fetchone()
    if not valid or valid[0]!='true':
        return {'known':False,'files':None,'bytes':None,'modified':None,'missing':None,'added':None}
    return {'known':True,**(json.loads(counts[0]) if counts else {'files':0,'bytes':0,'modified':0,'missing':0,'added':0})}


def pending_local_counts(cache, change, revision):
    if not Path(cache).is_file():return {'known':False,'files':None,'bytes':None}
    with closing(sqlite3.connect(cache)) as db:
        valid=db.execute("SELECT value FROM meta WHERE name='summary_valid'").fetchone()
        value=db.execute('SELECT value FROM meta WHERE name=?',('change_summary/'+change,)).fetchone()
    result=json.loads(value[0]) if value else {}
    if not valid or valid[0]!='true' or not result.get('known') or result['edit_revision']!=revision:
        return {'known':False,'files':None,'bytes':None}
    return result


def watched_changes(cache, root, paths):
    """Compare notification metadata against the last complete index, in a worker."""
    root = Path(root).resolve()
    changed = {}
    with closing(sqlite3.connect(cache)) if Path(cache).is_file() else nullcontext(None) as db:
        for path in paths:
            file = local_path(root,path)
            if file.is_dir():
                continue
            row = db.execute('SELECT data FROM local WHERE path=?',(path,)).fetchone() if db else None
            data = json.loads(row[0]) if row else {}
            if data.get('local_status') == 'ignored':
                continue
            if not file.is_file():
                if data.get('local_status') != 'missing':
                    changed[path] = 'missing'
            else:
                # A writer can preserve size and timestamps; notifications invalidate cached content.
                changed[path] = 'modified' if data else 'added'
            if path in changed and row:
                data['local_status']=changed[path]
                data.pop('sha256',None)
                data.pop('fingerprint',None)
                db.execute('UPDATE local SET data=? WHERE path=?',(json.dumps(data),path))
        if db:
            if changed:db.execute("INSERT OR REPLACE INTO meta VALUES ('summary_valid','false')")
            db.commit()
    return changed


def checkout_local(client, change, root, *, paths=None, cancelled=lambda: False, materialize=False):
    """Prepare mapped opened files for editing, preserving existing local bytes."""
    if not root:
        return
    change=client.rpc('status',change=change)
    client.progress({'state':'preparing','change':change['code'],'workspace':change['workspace'],'total_known':False})
    root=Path(root).resolve()
    after=''
    while True:
        if cancelled():
            raise InterruptedError('Checkout permission update stopped')
        if paths is None:
            # shortcut: recursive checkout visits all opened paths; use a server selection for large unrelated changelist contents.
            page=client.rpc('change_files',change=change['code'],edit_revision=change['edit_revision'],after=after,limit=1000)
            selected=[row['path'] for row in page['items']]
        else:
            page={'after':None}
            selected=paths
        if selected:
            mapped=client.rpc('workspace_paths',workspace=change['workspace'],paths=[{'stream':change['stream'],'path':path} for path in selected])['items']
            missing=[row['path'] for row in mapped if row.get('writable') and not row.get('excluded') and not local_path(root,row['path']).exists()]
            if materialize and missing:
                result=client.download(change['workspace'],root,paths=missing,source_stream=change['stream'],revision=change['base_revision'])
                if result.get('state')!='complete':
                    raise ValueError('Checkout remains open; finish the blocked download before editing.')
            for row in mapped:
                if row.get('writable') and not row.get('excluded'):
                    file=local_path(root,row['path'])
                    if file.is_file():
                        file.chmod(file.stat().st_mode | 0o200)
        after=page['after']
        if not after:
            break
