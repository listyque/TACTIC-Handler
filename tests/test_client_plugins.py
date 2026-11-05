from pathlib import Path
import io
import json
import tempfile
import unittest
import zipfile
from thlib.client_plugins import build_package, read_package, install_payload, payload_files, manifest_metadata, installation_root, release_directory


class ClientPluginPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'plugin.json').write_text(json.dumps({'code': 'test_tool', 'title': 'Test tool'}))
        (self.source / 'entry.py').write_text('def open_plugin(context): return context.window\n')

    def tearDown(self):
        self.temporary.cleanup()

    def test_build_native_manifest_without_server_actions_and_cache(self):
        archive = build_package(self.source, '1.0.0', self.root / 'releases')
        package = read_package(archive)
        self.assertEqual(package['metadata']['targets'], ['th'])
        self.assertNotIn('<python', package['manifest'])
        self.assertIn('<type>config</type>', package['manifest'])
        with zipfile.ZipFile(archive) as source:
            payload = source.read(archive.stem + '/payload.zip')
        cached = install_payload(payload, package['metadata'], self.root / 'cache')
        self.assertTrue((cached / 'entry.py').is_file())
        self.assertEqual(cached, self.root / 'cache/test_tool/1.0.0')
        self.assertEqual(archive.stem, 'test_tool-1.0.0')
        self.assertEqual(install_payload(payload, package['metadata'], self.root / 'cache'), cached)
        (cached / 'entry.py').write_text('modified')
        with self.assertRaisesRegex(ValueError, 'modified'):
            install_payload(payload, package['metadata'], self.root / 'cache')

    def test_versions_have_separate_paths_and_releases_are_not_overwritten(self):
        first = build_package(self.source, '1.0.0', self.root / 'releases')
        second = build_package(self.source, '1.0.1', self.root / 'releases')
        self.assertNotEqual(first, second)
        with self.assertRaises(FileExistsError):
            build_package(self.source, '1.0.0', self.root / 'releases')

    def test_invalid_version_and_missing_entry_are_rejected(self):
        with self.assertRaises(ValueError):
            build_package(self.source, '../escape', self.root / 'releases')
        (self.source / 'entry.py').unlink()
        with self.assertRaisesRegex(ValueError, 'entry.py'):
            build_package(self.source, '1.0.0', self.root / 'releases')

    def test_archive_paths_duplicates_and_bombs_are_rejected(self):
        for name in ('../entry.py', '/entry.py', 'C:/entry.py', 'a\\entry.py', 'a/../entry.py'):
            with self.subTest(name=name):
                data = io.BytesIO()
                with zipfile.ZipFile(data, 'w') as archive:
                    archive.writestr(name, 'pass')
                with self.assertRaises(ValueError):
                    payload_files(data.getvalue())

    def test_legacy_manifest_is_not_a_client_plugin(self):
        self.assertIsNone(manifest_metadata('<manifest><data><code>old</code></data></manifest>'))
        with self.assertRaises(ValueError):
            manifest_metadata('<!DOCTYPE manifest><manifest/>')


    def test_readable_installation_scopes_do_not_merge_servers_or_projects(self):
        expected = self.root / 'plugins/installed/http/example.org_port-18080/project-niki_friends'
        self.assertEqual(installation_root(self.root, 'http://EXAMPLE.ORG:18080/', 'niki_friends'), expected)
        for server, project in [('example.org:80', 'niki_friends'), ('https://example.org:18080', 'niki_friends'),
                                ('other.example:18080', 'niki_friends'), ('example.org:18080', '../niki')]:
            path = installation_root(self.root, server, project)
            self.assertNotEqual(path, expected)
            self.assertTrue(path.resolve().is_relative_to(self.root.resolve()))
        for server in ('http://user:secret@example.org', 'http://example.org/path', 'file:///temp'):
            with self.assertRaises(ValueError):
                installation_root(self.root, server, 'niki')

    def test_old_release_layout_remains_readable_for_rollback(self):
        from xml.etree import ElementTree as ET
        from thlib.client_plugins import _zip
        package = read_package(build_package(self.source, '1.0.0', self.root / 'new'))
        manifest = ET.fromstring(package['manifest'])
        node = manifest.find('data/th_client')
        metadata = json.loads(node.text)
        metadata['api'] = 1
        node.text = json.dumps(metadata)
        values = manifest_metadata(ET.tostring(manifest, encoding='unicode'))
        directory = release_directory(values)
        self.assertTrue(directory.startswith('test_tool-1.0.0-'))
        with zipfile.ZipFile(self.root / 'new/test_tool-1.0.0.zip') as archive:
            payload = archive.read('test_tool-1.0.0/payload.zip')
        old = self.root / (directory + '.zip')
        old.write_bytes(_zip({directory + '/manifest.xml': ET.tostring(manifest), directory + '/payload.zip': payload}))
        self.assertEqual(read_package(old)['metadata']['api'], 1)
        from thlib.client_plugin_server import catalog
        from unittest.mock import Mock
        server = Mock()
        server.query.return_value = [dict(code='test_tool', version='1.0.0', manifest=ET.tostring(manifest,encoding='unicode'),rel_dir=directory)]
        self.assertFalse(catalog(server)[0]['error'])

    def test_same_version_cannot_replace_installed_contents(self):
        one = read_package(build_package(self.source, '1.0.0', self.root / 'first'))
        (self.source / 'entry.py').write_text('def open_plugin(context): return None')
        two = read_package(build_package(self.source, '1.0.0', self.root / 'second'))
        for package in (one, two):
            with zipfile.ZipFile(self.root / ('first' if package is one else 'second') / 'test_tool-1.0.0.zip') as archive:
                payload = archive.read('test_tool-1.0.0/payload.zip')
            if package is one:
                installed = install_payload(payload,package['metadata'],self.root / 'installed')
            else:
                with self.assertRaisesRegex(ValueError,'modified'):
                    install_payload(payload,package['metadata'],self.root / 'installed')
        self.assertIn('context.window',(installed / 'entry.py').read_text())

    def test_publish_refuses_to_overwrite_an_inactive_version(self):
        from unittest.mock import Mock, patch
        from thlib.client_plugin_server import publish
        from thlib import tactic_classes as tc
        archive=build_package(self.source,'1.0.0',self.root/'release')
        previous=read_package(archive)
        server=Mock()
        server.query.return_value=[]
        with patch.object(tc,'execute_procedure_serverside',return_value=True), patch('thlib.client_plugin_server.download',return_value=b'different previous release'):
            with self.assertRaisesRegex(ValueError,'new version'):
                publish(server,'test',archive)
        server.start.assert_not_called()
        server.upload_file.assert_not_called()
