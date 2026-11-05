"""Native legacy TACTIC catalogue, file delivery and publication; no server patch."""
from pathlib import Path
from xml.etree import ElementTree as ET
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

from thlib.client_plugins import MAX_PACKAGE, manifest_metadata, read_package, release_directory, digest


def plugin_administrator(project_code):
    from pyasm.biz import Project
    from pyasm.common import Environment
    if Project.get_project_code() != project_code:
        raise ValueError('Select the plugin project first')
    return Environment.get_security().is_admin()


def catalog(server) -> list[dict]:
    rows = server.query('config/plugin', columns=['code', 'version', 'manifest', 'rel_dir'])
    result = []
    for row in rows:
        text = row.get('manifest') or ''
        if '<th_client>' not in text:
            continue
        item = {'code': row['code'], 'title': row['code'], 'error': ''}
        try:
            metadata = manifest_metadata(text)
            directory = release_directory(metadata)
            if row['code'] != metadata['code'] or row['version'] != metadata['version'] or row['rel_dir'] != directory:
                raise ValueError('The active plugin record does not match its manifest')
            item.update(metadata, directory=directory)
        except (ValueError, TypeError, KeyError, ET.ParseError) as error:
            item['error'] = str(error)
        result.append(item)
    return result


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        raise ValueError('Plugin downloads cannot redirect to another location')


def download(server, metadata: dict) -> bytes:
    address = server.server_name
    if '://' not in address:
        address = 'http://' + address
    origin = urlsplit(address)
    if origin.scheme not in {'http', 'https'} or origin.username or origin.password:
        raise ValueError('Invalid plugin server address')
    url = urlunsplit((origin.scheme, origin.netloc,
                     '/tactic/plugins/' + quote(metadata['directory'], safe='') + '/payload.zip', '', ''))
    with build_opener(_NoRedirect).open(url, timeout=30) as response:
        data = response.read(MAX_PACKAGE + 1)
    if len(data) != metadata['size']:
        raise ValueError('Incomplete plugin download')
    return data


def publish(server, project: str, path: Path) -> dict:
    from thlib import tactic_classes as tc
    if not tc.execute_procedure_serverside(plugin_administrator, {'project_code': project}, project=project, server=server):
        raise PermissionError('Only a server administrator can publish client plugins')
    package = read_package(path)
    metadata = package['metadata']
    previous = server.query('config/plugin', filters=[['code', metadata['code']]], limit=2)
    if len(previous) > 1:
        raise ValueError('Duplicate plugin registration')
    if previous:
        before = manifest_metadata(previous[0].get('manifest') or '')
        if before is None:
            raise ValueError('This plugin code is already owned by a server plugin')
        if before['version'] == metadata['version']:
            if before['sha256'] != metadata['sha256']:
                raise ValueError('Use a new version number for changed plugin files')
            if previous[0]['rel_dir'] == package['directory']:
                return metadata
    # A readable version directory is immutable even when another release is active.
    try:
        existing = download(server, dict(metadata, directory=package['directory']))
    except HTTPError as error:
        if error.code != 404:
            raise
        error.close()
    except ValueError as error:
        raise ValueError('Use a new version number for changed plugin files') from error
    else:
        if digest(existing) != metadata['sha256']:
            raise ValueError('Use a new version number for changed plugin files')
    server.start('Publish Handler client plugin')
    try:
        latest = server.query('config/plugin', filters=[['code', metadata['code']]], limit=2)
        if latest != previous:
            raise ValueError('The active plugin changed; refresh before publishing')
        server.upload_file(str(path))
        server.execute_cmd('tactic.command.plugin.PluginInstaller', args={
            'upload_file_name': path.name, 'register': True, 'verbose': False,
        })
        current = next(row for row in catalog(server) if row['code'] == metadata['code'])
        if current.get('sha256') != metadata['sha256']:
            raise ValueError('Server did not register the expected plugin release')
        server.finish('Published ' + metadata['code'] + ' ' + metadata['version'])
    except Exception:
        server.abort()
        raise
    return metadata
