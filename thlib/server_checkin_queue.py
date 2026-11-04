"""Chunk transport for optional native server check-ins; legacy execution stays separate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import uuid
import time
from urllib.error import HTTPError
from urllib.request import Request
from thlib.proxy import UrllibTransport

from thlib.checkin_operation import prepare_checkin, _check_cancel

PART_SIZE = 16 * 1024 * 1024
CHUNK_SIZE = 32 * 1024 * 1024
CHUNK_FILES = 50


def request(server: str, ticket: str, project: str, action: str,
            payload: dict, uploads=None, opener=None) -> dict:
    address = server.rstrip('/')
    if not address.startswith(('http://', 'https://')):
        address = 'http://' + address
    url = address + '/admin/checkin-queue/' + action
    values = dict(ticket=ticket, project=project, **payload)
    if uploads is None:
        body = json.dumps(values).encode('utf-8')
        content_type = 'application/json'
    else:
        boundary = 'checkin_' + uuid.uuid4().hex
        body = bytearray()
        for name, value in values.items():
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            body.extend(('--' + boundary + '\r\nContent-Disposition: form-data; name="' + name + '"\r\n\r\n').encode())
            body.extend(value.encode('utf-8')); body.extend(b'\r\n')
        for index, content in enumerate(uploads):
            body.extend(('--' + boundary + '\r\nContent-Disposition: form-data; name="file' + str(index) + '"; filename="part"\r\nContent-Type: application/octet-stream\r\n\r\n').encode())
            body.extend(content); body.extend(b'\r\n')
        body.extend(('--' + boundary + '--\r\n').encode())
        content_type = 'multipart/form-data; boundary=' + boundary
    try:
        with (opener or UrllibTransport()).open(Request(url, data=body, headers={'Content-Type':content_type}), timeout=120) as response:
            result = json.load(response)
    except HTTPError as error:
        try:
            message = json.load(error).get('error')
        except (ValueError, UnicodeError):
            message = None
        finally:
            error.close()
        if error.code in (404, 405, 501):
            message = 'This server does not support bulk check-ins. Use the legacy mode or update TACTIC Stream.'
        raise RuntimeError(message or 'Server check-in request failed: HTTP ' + str(error.code)) from error
    if not isinstance(result, dict) or result.get('error'):
        raise RuntimeError(str(result.get('error') if isinstance(result, dict) else 'Invalid server check-in response'))
    return result.get('result', result)


def operation_manifest(operation_id: str, payload: dict, cancel_event=None, progress_callback=None) -> tuple[dict, list[str]]:
    if payload.get('dccScene') or payload.get('snapshotType', 'file') != 'file':
        raise ValueError('DCC scene preparation and other snapshot types require the legacy check-in mode')
    repository = payload.get('repository') or 'default'
    if repository in ('local','sandbox') or repository.startswith('custom_'):
        raise ValueError('Client-only repositories require the legacy check-in mode')
    if repository in ('base','client'):
        repository = 'default'
    inputs = prepare_checkin(payload, cancel_event=cancel_event, resolve_naming=False)
    payload = inputs["payload"]
    records, sources, templates = [], [], []
    for group_index, (record, paths) in enumerate(zip(payload['files'], inputs['filePaths'])):
        template = record.get('template') or '$FILENAME.$EXT'
        if template not in templates:
            templates.append(template)
        values = inputs['filesDict'][group_index][1]
        kind = (values.get('t') or [record.get('type') or 'main'])[0]
        for name in paths:
            _check_cancel(cancel_event)
            source = Path(name)
            sha = hashlib.sha256()
            before = source.stat()
            hashed = 0
            if progress_callback is not None:
                progress_callback(name, hashed, before.st_size)
            with source.open('rb') as stream:
                while content := stream.read(4 * 1024 * 1024):
                    _check_cancel(cancel_event); sha.update(content)
                    hashed += len(content)
                    if progress_callback is not None:
                        progress_callback(name, hashed, before.st_size)
            after = source.stat()
            if (before.st_size,before.st_mtime_ns) != (after.st_size,after.st_mtime_ns):
                raise OSError('Source file changed while preparing the upload: ' + name)
            records.append(dict(path=str(group_index) + '/' + source.name, size=after.st_size,
                                file_type=kind, sha256=sha.hexdigest()))
            if payload.get('mode') == 'move':
                records[-1]['source_path'] = source.as_posix()
            sources.append(name)
    explicit = inputs['payload'].get('explicitFilename') or None
    if payload.get('contextAsFilename'):
        explicit = str(payload.get('context') or '').rsplit('/', 1)[-1]
    options = dict(search_key=inputs['payload']['searchKey'], context=payload['context'],
        process=payload.get('process') or payload['context'].split('/', 1)[0],
        description=payload.get('description') or '', source_files=records, templates=templates,
        padding=int(payload.get('sequencePadding') or 3), repository_alias=repository,
        keep_file_name=bool(payload.get('keepFileName')) and not bool(payload.get('ignoreKeepFileName')), is_revision=bool(payload.get('isRevision')),
        version=payload.get('version') or None, explicit_filename=explicit,
        update_versionless=bool(payload.get('updateVersionless')), only_versionless=bool(payload.get('onlyVersionless')),
        create_icon=bool(payload.get('generatePreviews')), versionless_mode=inputs['payload']['versionlessMode'],
        application_info=payload.get('applicationInfo') or {})
    return dict(operation_id=operation_id,options=options), sources


def submit_batch(server: str, ticket: str, project: str, batch_id: str,
                 operations: list[dict], progress_signal=None, cancel_event=None) -> dict:
    # Prepare the entire manifest before sending any work; reject unsupported contracts early.
    progress = dict(batch_id=batch_id, phase='preparing', filename='',
                    totalFiles=0, filesDone=0, totalBytes=0, bytesDone=0)
    last_emit = 0.0

    def report(*, force=False, **values):
        nonlocal last_emit
        progress.update(values)
        now = time.monotonic()
        if progress_signal is not None and (force or now - last_emit >= 0.1):
            progress_signal.emit((progress['bytesDone'], dict(progress)))
            last_emit = now

    def hashed(name, done, size):
        report(filename=name, hashedBytes=done, fileBytes=size)

    report(force=True)
    prepared = []
    for item in operations:
        prepared.append((operation_manifest(item['operation_id'], item['payload'], cancel_event, hashed), item['payload']))
    manifests = [manifest for (manifest, _paths), _payload in prepared]
    report(force=True, phase='uploading', totalFiles=sum(len(m['options']['source_files']) for m in manifests),
           totalBytes=sum(f['size'] for m in manifests for f in m['options']['source_files']))
    pending, definitions, contents = [], [], []
    bytes_pending, sent, files_pending = 0, 0, 0
    opener = UrllibTransport()

    def flush():
        nonlocal pending, definitions, contents, bytes_pending, sent, files_pending
        _check_cancel(cancel_event)
        chunk_id = hashlib.sha256(json.dumps(pending,sort_keys=True).encode()).hexdigest()
        report(force=True)
        request(server, ticket, project, 'submit', dict(batch_id=batch_id,chunk_id=chunk_id,
                operations=definitions,pieces=pending), uploads=contents, opener=opener)
        sent += 1
        report(force=True, bytesDone=progress['bytesDone'] + bytes_pending, filesDone=progress['filesDone'] + files_pending, chunks=sent)
        files_pending = 0
        pending, definitions, contents, bytes_pending = [], [], [], 0

    for (manifest, paths), _payload in prepared:
        needs_definition = True
        for index, name in enumerate(paths):
            _check_cancel(cancel_event)
            size = manifest['options']['source_files'][index]['size']
            report(filename=name)
            offset = 0
            with Path(name).open('rb') as source:
                while offset < size or size == 0 and offset == 0:
                    content = source.read(min(PART_SIZE, size - offset))
                    if not content and size:
                        raise OSError('Source file became shorter during upload: ' + name)
                    if pending and bytes_pending + len(content) > CHUNK_SIZE:
                        flush()
                    if needs_definition:
                        definitions.append(manifest); needs_definition = False
                    pending.append(dict(operation_id=manifest['operation_id'],file_index=index,offset=offset))
                    contents.append(content); bytes_pending += len(content); offset += len(content)
                    if offset == size:
                        files_pending += 1
                    if len(pending) >= CHUNK_FILES or bytes_pending >= CHUNK_SIZE:
                        flush()
                    if size == 0:
                        break
            if Path(name).stat().st_size != size:
                raise OSError('Source file changed size during upload: ' + name)
    if pending:
        flush()
    report(force=True, phase='uploaded', filename='')
    return dict(batch_id=batch_id,chunks=sent)


def submit_batches(server: str, ticket: str, batches: list[dict], progress_signal=None, cancel_event=None) -> list[dict]:
    return [submit_batch(server,ticket,batch['project'],batch['batch_id'],batch['operations'],
                         progress_signal,cancel_event) for batch in batches]


def remove_committed_sources(payload: dict) -> None:
    if payload.get('mode') != 'move':
        return
    # Move-mode sources are removed only after the server confirmed the saved bytes.
    expected = payload.get('_serverSourceHashes') or {}
    sources = {Path(name).as_posix() for record in payload['files'] for name in (record.get('paths') or [record['path']])}
    if set(expected) != sources:
        raise RuntimeError('Snapshot was saved, but source cleanup has no matching upload manifest')
    for name, checksum in expected.items():
        path = Path(name)
        if not path.exists():
            continue
        sha = hashlib.sha256()
        with path.open('rb') as source:
            while content := source.read(4 * 1024 * 1024):
                sha.update(content)
        if sha.hexdigest() != checksum:
            raise OSError('Snapshot was saved, but a changed source was kept: ' + name)
        path.unlink()
