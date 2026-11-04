"""Disk-backed bulk client; native commands for metadata, streaming HTTP for bytes."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from hashlib import sha256
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener
import json
import os
import shutil
import sqlite3
from stat import S_ISREG, S_IWUSR, S_IWGRP, S_IWOTH
import tarfile
import threading
import time
import uuid
from collections import deque

COMMAND = 'tactic.command.file_project_cmd.FileProjectCmd'
SMALL = 4 * 1024 * 1024
BLOCK = 64 * 1024 * 1024


def poll_progress(status):
    return tuple(status.get(key) for key in ('state', 'phase', 'bytes_done', 'files_done',
        'bytes_total', 'files_total', 'scanned_files', 'verified_bytes', 'verified_files',
        'staged_files', 'path', 'reason', 'error'))


class FileOperationError(ValueError):
    def __init__(self, message, *, path, operation):
        super().__init__(message)
        self.file_error = {'path':path, 'operation':operation, 'cause':message}


def fingerprint(path):
    stat = path.lstat()
    if not S_ISREG(stat.st_mode):
        raise ValueError('Transfer requires regular files: ' + str(path))
    return stat.st_size, stat.st_mtime_ns


def digest_file(path, *, cancelled=lambda: False):
    digest = sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(SMALL), b''):
            if cancelled():
                raise InterruptedError('File hashing stopped')
            digest.update(block)
    return digest.hexdigest()


def local_path(root, name):
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or any(part in ('..', '.', '') for part in name.split('/')) or '\\' in name or ':' in name:
        raise ValueError('Unsafe local transfer path')
    target = root.joinpath(*relative.parts)
    if not target.resolve().is_relative_to(root) or target.is_symlink():
        raise ValueError('Transfer path escapes workspace')
    return target


class FileTransferClient:
    def __init__(self, url, ticket, project, *, rpc=None, parallel=4, progress=None, opener_factory=build_opener):
        if not 1 <= parallel <= 16:
            raise ValueError('parallel must be in 1..16')
        self.url, self.ticket, self.project = url.rstrip('/'), ticket, project
        self.parallel, self._progress_callback = parallel, progress or (lambda value: None)
        self._metrics_lock = threading.Lock()
        self._samples = deque(maxlen=20)
        self._metrics_key = None
        self._inflight = {}
        self.progress = self.report_progress
        self.opener_factory = opener_factory
        self.local = threading.local()
        self.status, self.progress_lock = {}, threading.Lock()
        if rpc is None:
            def rpc(action, **kwargs):
                body = json.dumps({'action': action, **kwargs}, ensure_ascii=False).encode('utf-8')
                deadline = time.monotonic() + 120
                while True:
                    try:
                        with self.open('command', data=body, length=len(body), method='POST', headers={'Content-Type': 'application/json'}) as response:
                            return json.load(response)
                    except HTTPError as error:
                        if not self.wait_busy(error, deadline):
                            raise
        self.rpc = rpc

    def report_progress(self, value):
        value = dict(value)
        phase = value.get('phase') or value.get('state')
        if phase == 'running':
            phase = 'staging' if value.get('verified_files',0) >= value.get('files_total',1) else 'verifying'
        elif phase == 'collecting':
            phase = 'uploading'
        elif phase == 'streaming':
            phase = 'downloading'
        value['phase'] = phase
        stages = ('discovering', 'manifest', 'uploading', 'queued', 'verifying', 'staging', 'submitting')
        if value.get('kind') == 'upload' and phase in stages:
            value.update(operation_stage=stages.index(phase)+1, operation_stages=len(stages))
        files = value.get('files_done',0)
        done = value.get('bytes_done',0)
        if phase == 'verifying':
            files = value.get('verified_files',0)
            done = value.get('verified_bytes',0)+value.get('verifying_bytes',0)
            value['path'] = value.get('verifying_path') or value.get('verify_after') or ''
        elif phase == 'staging':
            files = value.get('staged_files',0)
            done = 0
            value['path'] = value.get('stage_after') or ''
        elif phase == 'manifest':
            files=value.get('files_manifested',value.get('files_done',0))
            done=value.get('bytes_manifested',0)
        key = (value.get('task'), phase)
        now = time.monotonic()
        with self._metrics_lock:
            if key != self._metrics_key:
                self._metrics_key = key
                self._samples.clear()
                self._inflight.clear()
            thread = threading.get_ident()
            partial = value.get('block_bytes_done') if phase == 'uploading' else value.get('file_bytes_done') if phase == 'downloading' else None
            if partial is not None:
                self._inflight[thread] = partial
            else:
                self._inflight.pop(thread,None)
            done += sum(self._inflight.values())
            if value.get('total_known'):
                done = min(done,value.get('bytes_total',done))
            value.update(phase_files_done=files,phase_bytes_done=done)
            if self._samples and done < self._samples[-1][1]:
                self._samples.clear()
            if not self._samples or now-self._samples[-1][0]>=.1:
                self._samples.append((now,done))
            elapsed = now-self._samples[0][0]
            if elapsed >= 1 and done > self._samples[0][1] and phase in ('uploading','downloading','verifying'):
                value['bytes_per_second'] = (done-self._samples[0][1])/elapsed
                if value.get('total_known') and value.get('bytes_total',0)>done:
                    value['eta_seconds'] = (value['bytes_total']-done)/value['bytes_per_second']
        self._progress_callback(value)

    def wait_busy(self, error, deadline):
        if not isinstance(error, HTTPError) or error.code != 503 or (error.headers or {}).get('X-Tactic-Error') != 'file_project_busy':
            return False
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise error
        with self.progress_lock:
            self.progress({**self.status, 'phase': 'waiting', 'state': 'waiting'})
        time.sleep(min(1, remaining))
        return True

    def open(self, route, *, data=None, length=None, headers=None, method=None, **query):
        if not hasattr(self.local, 'opener'):
            self.local.opener = self.opener_factory()
        request = Request(self.url + '/file-project/' + route + '?' + urlencode({'project': self.project, **query}),
            data=data, method=method or ('PUT' if data is not None else 'GET'),
            headers={'X-Tactic-Ticket': self.ticket, **({'Content-Length': str(length)} if length is not None else {}), **(headers or {})})
        try:
            return self.local.opener.open(request, timeout=120)
        except HTTPError as error:
            try:
                body = error.read(65536)
                details = json.loads(body)
                error.msg = str(error.reason) + ': ' + details.get('error', '')
                if isinstance(details.get('file_error'), dict):error.file_error=details['file_error']
            except (ValueError, OSError):
                pass
            finally:
                error.close()
            raise

    def put(self, task, stream, size, *, display_path=None, payload_size=None, **query):
        def blocks():
            remaining = size
            while remaining:
                block = stream.read(min(SMALL, remaining))
                if not block:
                    raise OSError('Local file became shorter during upload')
                remaining -= len(block)
                with self.progress_lock:
                    self.progress({**self.status, 'task': task, 'phase': 'uploading',
                        'path': display_path or self.status.get('path'),
                        'block_bytes_done': (size-remaining) if payload_size is None else (size-remaining)*payload_size/max(1,size),
                        'block_bytes_total': size if payload_size is None else payload_size})
                yield block
        with self.open('transfer-upload', task=task, data=blocks(), length=size, **query) as response:
            result = json.load(response)
        if result.get('task'):
            with self.progress_lock:
                if result['bytes_done'] >= self.status.get('bytes_done', 0):
                    self.status.update({key: value for key, value in result.items() if key != 'items'})
                self.progress(self.status.copy())
        return result

    def wait(self, task, *, timeout=86400):
        deadline = time.monotonic() + timeout
        service_checked = False
        previous, delay = None, .25
        while True:
            status = self.rpc('transfer_status', task=task)
            self.status = status
            self.progress(status)
            if status['state'] in ('ready', 'submitted', 'complete'):
                return status
            if status['state'] in ('error', 'cancelled', 'expired'):
                details = status.get('file_error')
                if details and details.get('path'):
                    raise FileOperationError(status.get('error', 'Transfer failed'), path=details['path'], operation=details.get('operation', 'transfer'))
                raise ValueError(status.get('error', 'Transfer stopped: ' + status['state']))
            if status['state'] == 'queued' and not service_checked:
                self.require_files_service()
                service_checked = True
            if time.monotonic() >= deadline:
                raise TimeoutError('Transfer remains queued; check services/enable=tactic|files')
            remaining = status.get('files_total', 0) - status.get('staged_files', 0)
            progress = poll_progress(status)
            base = .1 if status.get('phase') == 'staging' and 0 < remaining <= 1000 else .25
            delay = base if progress != previous else min(2, delay * 1.5)
            previous = progress
            time.sleep(delay)

    def require_files_service(self):
        if self.rpc('capabilities').get('files_service_configured') is False:
            raise ValueError('File processing is disabled: enable files in services/enable and restart the server. Keep the upload journal to resume.')

    def wait_bulk(self, task, *, timeout=86400):
        deadline=time.monotonic()+timeout
        previous,delay=None,.25
        while True:
            result=self.rpc('bulk_status',task=task)
            self.progress(result)
            if result['state'] in ('complete','cancelled','error'):
                if result['state']=='error':
                    raise ValueError(result['error'])
                return result
            if time.monotonic()>=deadline:
                raise TimeoutError('Bulk task continues on the server; refresh or resume waiting.')
            progress=poll_progress(result)
            delay=.25 if progress!=previous else min(2,delay*1.5)
            previous=progress
            time.sleep(delay)

    def bulk(self, *, timeout=86400, **options):
        if not self.rpc('capabilities')['files_service_configured']:
            raise ValueError('Enable the files service before starting server bulk operations.')
        result=self.rpc('bulk_begin',**options)
        self.progress(result)
        return self.wait_bulk(result['task'],timeout=timeout)

    def submit(self, change, *, edit_revision, **options):
        """Reconcile a lost reply against the same changelist before publishing again."""
        status = self.rpc('status', change=change)
        if status['state'] == 'submitted':
            return {'change':change, 'state':'submitted', 'revision':status['submitted_revision']}
        self.progress({'state':'submitting','change':change,'total_known':False})
        try:
            return self.rpc('submit', change=change, edit_revision=edit_revision, **options)
        except (URLError, TimeoutError, ConnectionError) as error:
            if isinstance(error, HTTPError) and error.code < 500:
                raise
            self.progress({'state':'recovering', 'change':change, 'total_known':False})
            try:
                status = self.rpc('status', change=change)
            except (URLError, TimeoutError, ConnectionError):
                raise error
            if status['state'] != 'submitted':
                raise
            return {'change':change, 'state':'submitted', 'revision':status['submitted_revision']}

    def prepare_change(self, change, root, review, *, paths=None, cancelled=lambda: False):
        """Inspect opened local files before review without allocating an upload."""
        root, review = Path(root).resolve(), Path(review)
        review.parent.mkdir(parents=True, exist_ok=True)
        status = self.rpc('status', change=change)
        expected_revision = status['edit_revision']
        count = dirty = 0
        with closing(sqlite3.connect(review)) as db:
            db.execute('CREATE TABLE files (path TEXT PRIMARY KEY, local TEXT NOT NULL, sha TEXT NOT NULL, dirty INTEGER NOT NULL, fingerprint TEXT NOT NULL, selected INTEGER NOT NULL DEFAULT 1, resolved_sha TEXT)')
            after = ''
            while True:
                if cancelled():
                    raise InterruptedError('Local preparation stopped')
                page = self.rpc('change_files', change=change, edit_revision=status['edit_revision'], after=after, limit=1000)
                rows = [row for row in page['items'] if row.get('action') not in ('delete', 'move/delete') and (paths is None or row['path'] in paths)]
                if rows:
                    mapped = self.rpc('workspace_paths', workspace=status['workspace'], paths=[{'stream':status['stream'], 'path':row['path']} for row in rows])['items']
                    for row, mapping in zip(rows, mapped):
                        if cancelled():
                            raise InterruptedError('Local preparation stopped')
                        if mapping.get('excluded') or not mapping.get('writable'):
                            raise ValueError('Opened file is outside writable workspace mappings: ' + row['path'])
                        file = local_path(root, mapping['path'])
                        if not file.is_file():
                            raise ValueError('Local copy is absent. Get Latest before preparing this changelist: ' + str(file))
                        before = fingerprint(file)
                        digest = digest_file(file)
                        if before != fingerprint(file):
                            raise ValueError('Local file changed during preparation: ' + str(file))
                        changed = digest != (row.get('file') or {}).get('sha256')
                        db.execute('INSERT INTO files (path,local,sha,dirty,fingerprint,resolved_sha) VALUES (?,?,?,?,?,?)', (row['path'], mapping['path'], digest, changed, json.dumps(before), row.get('resolved_sha256')))
                        count += 1
                        dirty += changed
                        self.progress({'state':'preparing', 'files_done':count, 'path':mapping['path'], 'total_known':False})
                db.commit()
                after = page['after']
                if not after:
                    break
        if self.rpc('status',change=change)['edit_revision']!=expected_revision:
            raise ValueError('Changelist changed; review the files again.')
        return {'review':str(review), 'change':change, 'root':str(root),
                'edit_revision':expected_revision, 'files':count, 'pending_uploads':dirty}

    def configure_submit_review(self, snapshot, options):
        """Keep selection exceptions on disk; never materialize the full manifest."""
        all_files = options.get('selection_all', True)
        paths = options.get('selection_paths', [])
        if not isinstance(all_files, bool) or not isinstance(paths, list) or len(paths) > 1000:
            raise ValueError('Invalid submit file selection')
        with closing(sqlite3.connect(snapshot['review'])) as db:
            db.execute('UPDATE files SET selected=?', (int(all_files),))
            db.executemany('UPDATE files SET selected=? WHERE path=?', ((int(not all_files), path) for path in paths))
            if options.get('guard_resolved') and db.execute('SELECT 1 FROM files WHERE selected=1 AND resolved_sha IS NOT NULL AND resolved_sha!=sha LIMIT 1').fetchone():
                raise ValueError('A resolved file changed after resolution; review or resolve it again.')
            db.commit()

    def upload_prepared_change(self, snapshot, *, cancelled=lambda: False):
        """Transfer the reviewed bytes only after Submit/Shelve is confirmed."""
        root, review = Path(snapshot['root']).resolve(), Path(snapshot['review'])
        self.validate_change(root, review, cancelled=cancelled)
        status = self.rpc('status', change=snapshot['change'])
        if status['edit_revision'] != snapshot['edit_revision']:
            raise ValueError('Changelist changed; review the files again.')
        revision = status['edit_revision']
        with closing(sqlite3.connect(review)) as db:
            if db.execute('SELECT 1 FROM files WHERE dirty=1 AND selected=1 LIMIT 1').fetchone():
                sources = ((path, local_path(root, name)) for path, name in db.execute('SELECT path,local FROM files WHERE dirty=1 AND selected=1 ORDER BY path'))
                staged = self.upload(snapshot['change'], root, review.with_suffix('.upload.sqlite'),
                    sources=sources, edit_revision=revision)
                revision = staged['expected_edit_revision']
                db.execute('ATTACH DATABASE ? AS uploaded', (str(review.with_suffix('.upload.sqlite')),))
                if db.execute('SELECT 1 FROM files AS expected JOIN uploaded.files AS actual USING(path) WHERE expected.dirty=1 AND expected.selected=1 AND expected.sha!=actual.sha LIMIT 1').fetchone():
                    raise ValueError('Local file changed during upload; review the changelist again.')
        self.validate_change(root, review, cancelled=cancelled)
        if self.rpc('status', change=snapshot['change'])['edit_revision'] != revision:
            raise ValueError('Changelist changed; review the files again.')
        return revision

    @staticmethod
    def validate_change(root, review, *, cancelled=lambda: False):
        """Do not submit bytes that differ from the local contents shown for approval."""
        if not Path(review).is_file():
            raise ValueError('Local review expired; review the changelist again.')
        with closing(sqlite3.connect(review)) as db:
            for name, expected in db.execute('SELECT local,sha FROM files WHERE selected=1 ORDER BY path'):
                if cancelled():
                    raise InterruptedError('Local validation stopped')
                file = local_path(Path(root).resolve(), name)
                if not file.is_file() or digest_file(file) != expected:
                    raise ValueError('Local file changed after review; review the changelist again: ' + str(file))

    def upload(self, change, root, journal, *, submit=False, timeout=86400, sources=None, edit_revision=None):
        """Keep the journal to resume this exact task; new files need a new journal."""
        root, journal = Path(root).resolve(), Path(journal).resolve()
        journal.parent.mkdir(parents=True, exist_ok=True)
        self.progress({'state':'discovering','phase':'discovering','kind':'upload','journal':str(journal),
                       'change':change,'files_done':0,'total_known':False})
        # Local SQLite is only a client outbox; all server persistence uses native commands.
        with closing(sqlite3.connect(journal)) as db:
            db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)')
            db.execute('CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, size INTEGER, mtime INTEGER, sha TEXT, blob TEXT)')
            def get(key):
                row = db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
                return json.loads(row[0]) if row else None
            def set_value(key, value):
                db.execute('INSERT OR REPLACE INTO meta VALUES (?,?)', (key, json.dumps(value)))
                db.commit()
            identity = [self.url, self.project, change, str(root), submit]
            if get('identity') not in (None, identity):
                raise ValueError('Journal belongs to another transfer')
            set_value('identity', identity)
            if not get('task'):
                self.require_files_service()
            db.execute('CREATE TABLE IF NOT EXISTS sources (path TEXT PRIMARY KEY, local_path TEXT NOT NULL)')
            source_names = {}
            def source_path(name):
                return local_path(root, source_names.get(name, name))
            if not get('scanned'):
                db.execute('DELETE FROM files')
                db.execute('DELETE FROM sources')
                count = 0
                from .file_workspace import workspace_files
                selected = sources if sources is not None else ((path.relative_to(root).as_posix(), path) for path in workspace_files(root)
                    if path != journal and not str(path).startswith(str(journal) + '-'))
                for name, path in selected:
                    path = Path(path)
                    local_name = path.relative_to(root).as_posix()
                    local_path(root, name)
                    path = local_path(root, local_name)
                    size, mtime = fingerprint(path)
                    value = digest_file(path) if size <= SMALL else None
                    if fingerprint(path) != (size, mtime):
                        raise ValueError('Local file changed during discovery')
                    db.execute('INSERT INTO files VALUES (?,?,?,?,NULL)', (name, size, mtime, value))
                    db.execute('INSERT INTO sources VALUES (?,?)', (name, local_name))
                    count += 1
                    if count % 1000 == 0:
                        db.commit()
                        self.progress({'state': 'discovering', 'files_done': count, 'total_known': False})
                set_value('scanned', True)
                self.progress({'state':'manifest','phase':'manifest','kind':'upload','files_done':count,
                               'path':str(root),'total_known':False})
            task = get('task')
            if not task:
                request_id = get('request_id') or uuid.uuid4().hex
                set_value('request_id', request_id)
                total_files, total_bytes = db.execute('SELECT COUNT(*), COALESCE(SUM(size),0) FROM files').fetchone()
                task = self.rpc('transfer_begin', change=change, request_id=request_id, submit=submit,
                    expected_files=total_files, expected_bytes=total_bytes,
                    **({'edit_revision':edit_revision} if edit_revision is not None else {}))['task']
                set_value('task', task)
            status = self.rpc('transfer_status', task=task)
            self.status = status
            self.progress(status)
            if status.get('sealed'):
                return self.wait(task, timeout=timeout)
            after = ''
            while True:
                rows = db.execute('SELECT path,size,mtime,sha,blob FROM files WHERE path>? ORDER BY path LIMIT 1000', (after,)).fetchall()
                if not rows:
                    break
                if sum(len(row[0]) for row in rows) > 60000:
                    while len(json.dumps([row[0] for row in rows]).encode()) > 256 * 1024:
                        rows = rows[:max(1, len(rows) // 2)]
                if not rows[0][4]:
                    self.progress({**status,'phase':'manifest','path':rows[0][0],
                                   'chunk_files':len(rows),'manifest_after':after})
                    manifest = self.rpc('transfer_manifest', task=task, request_id='manifest-' + sha256(after.encode()).hexdigest(),
                        files=[{'path': row[0], 'size': row[1], **({'sha256': row[3]} if row[3] else {})} for row in rows])
                    self.status.update({key:value for key,value in manifest.items() if key!='items'})
                    db.executemany('UPDATE files SET blob=? WHERE path=?', [(entry['blob'], entry['path']) for entry in manifest['items']])
                    db.commit()
                planned = self.rpc('transfer_next', task=task, after=after)['items'][:len(rows)]
                local = {row[0]: row for row in rows}
                source_names = dict(db.execute('SELECT s.path,s.local_path FROM sources s JOIN files f ON f.path=s.path WHERE f.path>=? AND f.path<=?', (rows[0][0], rows[-1][0])))
                for entry in planned:
                    path = source_path(entry['path'])
                    if fingerprint(path) != (local[entry['path']][1], local[entry['path']][2]):
                        raise FileOperationError('Local file changed; use a new transfer: ' + str(path),path=entry['path'],operation='upload')
                small, large = [], []
                for entry in planned:
                    if entry['state'] == 'ready' or entry['state'] == 'uploaded' and entry.get('expected_sha256'):
                        continue
                    (small if entry['size'] <= SMALL else large).append(entry)
                def send_small(entries):
                    def archive():
                        for entry in entries:
                            path = source_path(entry['path'])
                            with self.progress_lock:
                                self.status['path'] = entry['path']
                            header = tarfile.TarInfo(entry['blob'])
                            header.size = entry['size']
                            yield header.tobuf(format=tarfile.USTAR_FORMAT)
                            with path.open('rb') as source:
                                remaining = entry['size']
                                while remaining:
                                    block = source.read(min(SMALL, remaining))
                                    if not block:
                                        raise OSError('Local batch file became shorter')
                                    remaining -= len(block)
                                    yield block
                            if fingerprint(path) != (local[entry['path']][1], local[entry['path']][2]):
                                raise FileOperationError('Local file changed during packing',path=entry['path'],operation='upload')
                            yield bytes((512 - entry['size'] % 512) % 512)
                        yield bytes(1024)
                    class Reader:
                        def __init__(self):
                            self.blocks, self.buffer = iter(archive()), bytearray()
                        def read(self, size):
                            while len(self.buffer) < size:
                                block = next(self.blocks, None)
                                if block is None:
                                    break
                                self.buffer.extend(block)
                            result = bytes(self.buffer[:size])
                            del self.buffer[:size]
                            return result
                    length = 1024 + sum(512 + (entry['size'] + 511) // 512 * 512 for entry in entries)
                    deadline, attempt = time.monotonic() + 120, 0
                    while True:
                        try:
                            self.put(task, Reader(), length, payload_size=sum(entry['size'] for entry in entries), batch=1)
                            break
                        except (URLError, OSError) as error:
                            if self.wait_busy(error, deadline):
                                continue
                            if attempt == 3:
                                raise
                            attempt += 1
                            time.sleep(.25 * attempt)
                group, size = [], 10240
                for entry in small:
                    required = 512 + (entry['size'] + 511) // 512 * 512
                    if size + required > BLOCK:
                        send_small(group)
                        group, size = [], 10240
                    group.append(entry)
                    size += required
                if group:
                    send_small(group)
                def send_large(entry):
                    path = source_path(entry['path'])
                    offset = entry['received']
                    digest = sha256()
                    with path.open('rb') as source:
                        remaining = offset
                        while remaining:
                            part = source.read(min(SMALL, remaining))
                            if not part:
                                raise OSError('Local upload prefix disappeared')
                            digest.update(part)
                            remaining -= len(part)
                        class Reader:
                            def read(self, size):
                                block = source.read(size)
                                digest.update(block)
                                return block
                        while offset < entry['size']:
                            length = min(BLOCK, entry['size'] - offset)
                            original = digest.copy()
                            deadline, attempt = time.monotonic() + 120, 0
                            while True:
                                try:
                                    self.put(task, Reader(), length, display_path=entry['path'], blob=entry['blob'], offset=offset)
                                    break
                                except (URLError, OSError) as error:
                                    confirmed = self.rpc('transfer_received', task=task, blob=entry['blob'])['received']
                                    if confirmed == offset + length:
                                        source.seek(offset)
                                        digest = original.copy()
                                        remaining = length
                                        while remaining:
                                            part = Reader().read(min(SMALL, remaining))
                                            if not part:
                                                raise OSError('Local upload changed')
                                            remaining -= len(part)
                                        break
                                    if confirmed != offset:
                                        raise
                                    digest = original.copy()
                                    source.seek(offset)
                                    if self.wait_busy(error, deadline):
                                        continue
                                    if attempt == 3:
                                        raise
                                    attempt += 1
                                    time.sleep(.25 * attempt)
                            offset += length
                    value = digest.hexdigest()
                    if fingerprint(path) != (local[entry['path']][1], local[entry['path']][2]):
                        raise ValueError('Local file changed during upload')
                    return entry['blob'], value
                parallel = min(self.parallel, status.get('max_parallel', 4))
                digests = []
                with ThreadPoolExecutor(max_workers=parallel) as pool:
                    # Each window is bounded independently of the total manifest size.
                    for start in range(0, len(large), parallel):
                        for blob, value in pool.map(send_large, large[start:start + parallel]):
                            digests.append({'blob': blob, 'sha256': value})
                if digests:
                    self.rpc('transfer_digests', task=task, items=digests)
                self.status = self.rpc('transfer_status', task=task)
                self.progress(self.status)
                after = rows[-1][0]
            self.rpc('transfer_seal', task=task)
            return self.wait(task, timeout=timeout)

    def download(self, workspace, root, *, task=None, force=False, prefix='', paths=None, source_stream=None, source_depot=None, revision=None, changelist=None, at_date=None, file_revision=None, path=None):
        """Resume by task ID; return blocked for local edits without overwriting them."""
        if task and force:
            raise ValueError('Force starts a scoped download; omit task and repeat its selection')
        root = Path(root)
        if not root.is_absolute():
            raise ValueError('Choose an absolute local workspace root.')
        if any(parent.is_symlink() for parent in (root, *root.parents)):
            raise ValueError('Local workspace root must not follow symlinks.')
        existing = root
        while not existing.exists() and existing.parent != existing:
            existing = existing.parent
        if not existing.is_dir():
            raise ValueError('Local workspace root or its parent is not a directory.')
        root = root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        task = task or self.rpc('transfer_begin', kind='download', workspace=workspace, client_root=str(root),prefix=prefix,paths=paths,force=force,source_stream=source_stream,source_depot=source_depot,revision=revision,changelist=changelist,at_date=at_date,file_revision=file_revision,path=path)['task']
        self.status = self.rpc('transfer_status', task=task)
        if self.status.get('client_root') not in (None, str(root)):
            raise ValueError('Download task belongs to another local root')
        if task:force=bool(self.status.get('force',force))
        self.progress(self.status)
        plan = None
        try:
            while self.rpc('transfer_status', task=task)['state'] not in ('complete', 'cancelled'):
                plan = None
                plan = self.rpc('transfer_next', task=task)
                items = plan['items']
                targets, before, present = {}, {}, set()
                required = 0
                for entry in items:
                    name = entry.get('local_path', entry['path'])
                    target = local_path(root, name)
                    before[name] = fingerprint(target) if target.exists() else None
                    if target.exists() and not force:
                        actual = digest_file(target)
                        have = entry.get('_have')
                        if not force and actual != entry.get('sha256') and (not have or actual != have.get('sha256')):
                            self.status = self.rpc('transfer_pause',task=task,ack_revision=plan['ack_revision'],
                                reason='local_modified_or_untracked',path=target.as_posix())
                            self.progress(self.status)
                            return self.status
                        if actual == entry.get('sha256'):
                            present.add(name)
                    if not entry.get('deleted'):
                        targets[name] = entry
                        if name not in present:
                            temporary = target.with_name(target.name + '.tactic-' + entry['blob'] + '.part')
                            if temporary.is_symlink() or not temporary.resolve().is_relative_to(root):
                                raise ValueError('Unsafe partial file')
                            offset = fingerprint(temporary)[0] if temporary.exists() else 0
                            if entry['size'] <= SMALL or offset >= entry['size']:
                                offset = 0
                            required += entry['size'] - offset
                # Estimate this bounded page conservatively; old targets stay until replacement.
                free = shutil.disk_usage(root).free
                if required > free:
                    self.status = self.rpc('transfer_pause', task=task, ack_revision=plan['ack_revision'],
                        reason='insufficient_disk_space', path=root.as_posix(),
                        required_bytes=required, available_bytes=free)
                    self.progress(self.status)
                    return self.status
                def receive(entry, source, *, offset=0, length=None):
                    target = local_path(root, entry.get('local_path', entry['path']))
                    target.parent.mkdir(parents=True, exist_ok=True)
                    temporary = target.with_name(target.name + '.tactic-' + entry['blob'] + '.part')
                    if temporary.is_symlink() or not temporary.resolve().is_relative_to(root):
                        raise ValueError('Unsafe partial file')
                    remaining = entry['size'] - offset if length is None else length
                    stream_digest = sha256() if not offset else None
                    with temporary.open('r+b' if offset else 'wb') as output:
                        output.truncate(offset)
                        output.seek(offset)
                        while remaining:
                            block = source.read(min(SMALL, remaining))
                            if not block:
                                raise OSError('Download interrupted; partial file retained')
                            output.write(block)
                            if stream_digest is not None:
                                stream_digest.update(block)
                            remaining -= len(block)
                            with self.progress_lock:
                                self.progress({**self.status, 'phase': 'downloading', 'path': entry['path'],
                                    'file_bytes_done': entry['size'] - remaining, 'file_bytes_total': entry['size']})
                        output.flush()
                        os.fsync(output.fileno())
                    actual_sha = stream_digest.hexdigest() if stream_digest is not None else digest_file(temporary)
                    if temporary.stat().st_size != entry['size'] or actual_sha != entry['sha256']:
                        temporary.unlink(missing_ok=True)
                        raise FileOperationError('Downloaded file checksum mismatch',path=entry['path'],operation='download')
                    if (fingerprint(target) if target.exists() else None) != before[entry.get('local_path', entry['path'])]:
                        raise FileOperationError('Local file changed during download',path=entry['path'],operation='download')
                    previous_mode = target.stat().st_mode if target.exists() else None
                    if previous_mode is not None and not previous_mode & S_IWUSR:
                        target.chmod(previous_mode | S_IWUSR)
                    try:
                        os.replace(temporary, target)
                    except OSError:
                        if previous_mode is not None:
                            target.chmod(previous_mode)
                        raise
                    if entry.get('writable') is False:
                        target.chmod(target.stat().st_mode & ~(S_IWUSR | S_IWGRP | S_IWOTH))
                small = {name: entry for name, entry in targets.items() if entry['size'] <= SMALL and name not in present}
                if small:
                    body = json.dumps({'sync': plan['sync'], 'ack_revision': plan['ack_revision'],
                        'paths': [entry['path'] for entry in small.values()]}, ensure_ascii=False).encode('utf-8')
                    with self.open('sync-download', data=body, length=len(body), method='POST', headers={'Content-Type': 'application/json'}) as response:
                        if int(response.headers['X-Tactic-Ack-Revision']) != plan['ack_revision']:
                            raise ValueError('Download plan changed')
                        seen = set()
                        with tarfile.open(fileobj=response, mode='r|', bufsize=SMALL) as archive:
                            for member in archive:
                                entry = small.get(member.name)
                                if not entry or member.name in seen or not member.isfile() or member.size != entry['size']:
                                    raise ValueError('Archive differs from pinned manifest')
                                seen.add(member.name)
                                receive(entry, archive.extractfile(member))
                        if seen != set(small):
                            raise ValueError('Download archive is incomplete')
                def download_large(entry):
                    target = local_path(root, entry.get('local_path', entry['path']))
                    if not force and target.exists() and target.stat().st_size == entry['size'] and digest_file(target) == entry['sha256']:
                        return
                    temporary = target.with_name(target.name + '.tactic-' + entry['blob'] + '.part')
                    if temporary.is_symlink():
                        raise ValueError('Unsafe partial file')
                    offset = temporary.stat().st_size if temporary.exists() else 0
                    if offset >= entry['size']:
                        temporary.unlink()
                        offset = 0
                    query = {'sync':plan['sync'],'path':entry['path'],'ack_revision':plan['ack_revision']}
                    if entry.get('source_path'):query['source_path']=entry['source_path']
                    with self.open('download', headers={'Range': 'bytes=%s-' % offset} if offset else {}, **query) as response:
                        if offset and response.status != 206:
                            raise ValueError('Server did not honor resumed download range')
                        receive(entry, response, offset=offset)
                large = [entry for name, entry in targets.items() if entry['size'] > SMALL and name not in present]
                parallel = min(self.parallel, self.status.get('max_parallel', 4))
                with ThreadPoolExecutor(max_workers=parallel) as pool:
                    for start in range(0, len(large), parallel):
                        list(pool.map(download_large, large[start:start + parallel]))
                for entry in items:
                    if entry.get('deleted'):
                        name = entry.get('local_path', entry['path'])
                        target = local_path(root, name)
                        if (fingerprint(target) if target.exists() else None) != before[name]:
                            raise ValueError('Local file changed during download')
                        target.unlink(missing_ok=True)
                status = self.rpc('transfer_ack', task=task, ack_revision=plan['ack_revision'], paths=[entry['path'] for entry in items])
                self.status = status
                self.progress(status)
        except (OSError, ValueError) as error:
            if plan is not None:
                try:
                    self.status=self.rpc('transfer_pause',task=task,ack_revision=plan['ack_revision'],
                        reason='interrupted' if isinstance(error,InterruptedError) else 'download_error')
                except (OSError, ValueError) as pause_error:
                    error.add_note('Could not record stopped download: '+str(pause_error))
            raise
        return self.rpc('transfer_status', task=task)
