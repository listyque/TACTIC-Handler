"""Versioned desktop-only plugin packages over native TACTIC plugin records."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
from xml.etree import ElementTree as ET
import zipfile

API_VERSION = 1
MAX_PACKAGE = 8 * 1024 * 1024
MAX_CONTENT = 32 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest_metadata(text: str) -> dict | None:
    if len(text.encode('utf-8')) > 65536 or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('Invalid plugin manifest')
    root = ET.fromstring(text)
    if root.tag != 'manifest':
        raise ValueError('Expected a plugin manifest')
    client = root.findtext('data/th_client')
    if client is None:
        return None
    if [node.tag for node in root] != ['data']:
        raise ValueError('Client packages cannot contain server installation actions')
    metadata = json.loads(client)
    if set(metadata) != {'api', 'targets', 'sha256', 'size', 'access_script'}:
        raise ValueError('Invalid client plugin metadata')
    if type(metadata['api']) is not int or metadata['api'] != API_VERSION or metadata['targets'] != ['th']:
        raise ValueError('This plugin requires another Handler plugin API')
    if not re.fullmatch(r'[0-9a-f]{64}', str(metadata['sha256'])):
        raise ValueError('Invalid plugin checksum')
    if type(metadata['size']) is not int or not 0 < metadata['size'] <= MAX_PACKAGE:
        raise ValueError('Plugin package exceeds the size limit')
    for name, pattern in [('code', r'[a-z][a-z0-9_]{0,63}'), ('version', r'\d+\.\d+\.\d+')]:
        value = root.findtext('data/' + name, '')
        if not re.fullmatch(pattern, value):
            raise ValueError('Invalid plugin ' + name)
        metadata[name] = value
    access = metadata['access_script']
    if not isinstance(access, str) or (access and (access.startswith('/') or '\\' in access or any(part in ('', '.', '..') for part in access.split('/')))):
        raise ValueError('Invalid plugin access script')
    metadata['title'] = root.findtext('data/title') or metadata['code']
    metadata['description'] = root.findtext('data/description') or ''
    return metadata


def payload_files(payload: bytes) -> dict[str, bytes]:
    if not 0 < len(payload) <= MAX_PACKAGE:
        raise ValueError('Plugin package exceeds the size limit')
    files = {}
    total = 0
    normalized_names = set()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if len(archive.infolist()) > 256:
            raise ValueError('Too many plugin files')
        for member in archive.infolist():
            name = member.filename
            path = PurePosixPath(name)
            parts = name.split('/')
            if (member.is_dir() or name.casefold() in normalized_names or path.is_absolute() or '\\' in name
                    or any(part in ('', '.', '..') or ':' in part or part.rstrip(' .') != part for part in parts)
                    or stat.S_ISLNK(member.external_attr >> 16)
                    or path.suffix.lower() not in {'.py', '.qml', '.json', '.png', '.svg', '.ico', '.txt', '.md'}):
                raise ValueError('Unsafe plugin archive path: ' + name)
            normalized_names.add(name.casefold())
            total += member.file_size
            if total > MAX_CONTENT:
                raise ValueError('Plugin contents exceed the size limit')
            data = archive.read(member)
            if path.suffix == '.py':
                compile(data, name, 'exec')
            files[name] = data
    if 'entry.py' not in files:
        raise ValueError('Plugin entry.py is missing')
    return files


def _zip(files: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return stream.getvalue()


def build_package(source: Path, version: str, output: Path) -> Path:
    """Build a legacy-installable release without importing any plugin code."""
    source = source.resolve()
    values = json.loads((source / 'plugin.json').read_text(encoding='utf-8-sig'))
    files = {}
    for path in source.rglob('*'):
        relative = path.relative_to(source)
        if any(part.startswith('.') or part in {'__pycache__', 'settings', 'log', 'secrets'} for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError('Plugin source cannot contain links')
        if path.is_file() and relative.as_posix() != 'plugin.json':
            files[relative.as_posix()] = path.read_bytes()
    payload = _zip(files)
    payload_files(payload)
    root = ET.Element('manifest')
    data = ET.SubElement(root, 'data')
    for name, value in [('code', values['code']), ('title', values['title']),
                        ('description', values.get('description', '')), ('version', version), ('type', 'config')]:
        ET.SubElement(data, name).text = value
    ET.SubElement(data, 'th_client').text = json.dumps({
        'api': API_VERSION, 'targets': ['th'], 'sha256': digest(payload), 'size': len(payload),
        'access_script': values.get('access_script', ''),
    }, separators=(',', ':'))
    manifest = ET.tostring(root, encoding='unicode')
    metadata = manifest_metadata(manifest)
    directory = metadata['code'] + '-' + metadata['version'] + '-' + metadata['sha256'][:12]
    package = _zip({directory + '/manifest.xml': manifest.encode(), directory + '/payload.zip': payload})
    output.mkdir(parents=True, exist_ok=True)
    target = output / (directory + '.zip')
    with target.open('xb') as stream:
        stream.write(package)
    target.with_suffix('.zip.sha256').write_text(digest(package) + '  ' + target.name + '\n', encoding='utf-8')
    return target


def read_package(path: Path) -> dict:
    if path.stat().st_size > MAX_PACKAGE + 65536:
        raise ValueError('Plugin package exceeds the size limit')
    with zipfile.ZipFile(path) as archive:
        expected = {path.stem + '/manifest.xml', path.stem + '/payload.zip'}
        if len(archive.infolist()) != 2 or set(archive.namelist()) != expected:
            raise ValueError('Choose a built Handler client plugin ZIP')
        if any(member.file_size > MAX_PACKAGE or stat.S_ISLNK(member.external_attr >> 16) for member in archive.infolist()):
            raise ValueError('Plugin package exceeds the size limit')
        manifest = archive.read(path.stem + '/manifest.xml').decode('utf-8-sig')
        metadata = manifest_metadata(manifest)
        if metadata is None:
            raise ValueError('This is not a Handler client plugin')
        payload = archive.read(path.stem + '/payload.zip')
    if digest(payload) != metadata['sha256'] or len(payload) != metadata['size']:
        raise ValueError('Plugin checksum does not match')
    directory = metadata['code'] + '-' + metadata['version'] + '-' + metadata['sha256'][:12]
    if directory != path.stem:
        raise ValueError('Plugin filename does not match its release')
    payload_files(payload)
    return dict(metadata=metadata, manifest=manifest, directory=directory)


def cache_payload(payload: bytes, metadata: dict, cache: Path) -> Path:
    """Stage and verify immutable source files before making them importable."""
    if len(payload) != metadata['size'] or digest(payload) != metadata['sha256']:
        raise ValueError('Plugin checksum does not match')
    files = payload_files(payload)
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / metadata['sha256']
    if destination.is_symlink():
        raise ValueError('Plugin cache cannot be a directory link')
    if destination.exists():
        for name, data in files.items():
            path = destination / name
            if not path.resolve().is_relative_to(destination.resolve()) or path.read_bytes() != data:
                raise ValueError('Cached plugin files were modified; preserve them before retrying')
        actual = {p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
        if actual != set(files):
            raise ValueError('Cached plugin contains unexpected files')
        return destination
    stage = Path(tempfile.mkdtemp(prefix='.plugin-', dir=cache))
    try:
        for name, data in files.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        os.replace(stage, destination)
    finally:
        if stage.exists():
            if stage.parent.resolve() != cache.resolve():
                raise ValueError('Invalid plugin staging cleanup path')
            shutil.rmtree(stage)
    return destination
