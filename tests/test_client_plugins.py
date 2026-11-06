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
        self.assertEqual(cached, self.root / 'cache/test_tool')
        self.assertEqual(archive.stem, 'test_tool-1.0.0')
        self.assertEqual(install_payload(payload, package['metadata'], self.root / 'cache'), cached)
        (cached / 'entry.py').write_text('modified')
        with self.assertRaisesRegex(ValueError, 'modified'):
            install_payload(payload, package['metadata'], self.root / 'cache')

    def test_selected_plugin_must_match_the_source_manifest(self):
        output = self.root / 'releases'
        with self.assertRaisesRegex(ValueError, 'another plugin'):
            build_package(self.source, '1.0.0', output, expected_code='another_tool')
        self.assertFalse(output.exists())
        archive = build_package(self.source, '1.0.0', output, expected_code='test_tool')
        self.assertEqual(read_package(archive)['metadata']['code'], 'test_tool')

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


    def test_connections_share_one_plain_plugins_folder(self):
        expected = self.root / 'plugins'
        for server, project in [('http://EXAMPLE.ORG:18080/', 'niki_friends'),
                                ('https://other.example', 'another')]:
            self.assertEqual(installation_root(self.root, server, project), expected)
        for server in ('http://user:secret@example.org', 'http://example.org/path', 'file:///temp'):
            with self.assertRaises(ValueError):
                installation_root(self.root, server, 'niki')

    def test_updates_replace_one_folder_and_remove_old_files(self):
        def install(version):
            archive = build_package(self.source, version, self.root / 'releases')
            package = read_package(archive)
            with zipfile.ZipFile(archive) as stream:
                payload = stream.read(archive.stem + '/payload.zip')
            return install_payload(payload, package['metadata'], self.root / 'plugins')
        (self.source / 'old.py').write_text('old = True')
        first = install('1.0.0')
        (self.source / 'old.py').unlink()
        (self.source / 'entry.py').write_text('def open_plugin(context): return "updated"')
        second = install('1.0.1')
        self.assertEqual(first, second)
        self.assertFalse((second / 'old.py').exists())
        self.assertIn('updated', (second / 'entry.py').read_text())
        self.assertEqual(list((self.root / 'plugins').iterdir()), [second])

    def test_unmanaged_or_modified_folders_are_never_replaced(self):
        archive = build_package(self.source, '1.0.0', self.root / 'releases')
        package = read_package(archive)
        with zipfile.ZipFile(archive) as stream:
            payload = stream.read(archive.stem + '/payload.zip')
        folder = self.root / 'plugins/test_tool';folder.mkdir(parents=True)
        (folder / 'own.py').write_text('user_data = True')
        with self.assertRaisesRegex(ValueError, 'preserved'):
            install_payload(payload, package['metadata'], self.root / 'plugins')
        self.assertTrue((folder / 'own.py').exists())

    def test_failed_replacement_restores_the_previous_code(self):
        import os
        from unittest.mock import patch
        def package(version):
            archive=build_package(self.source,version,self.root/'releases')
            values=read_package(archive)['metadata']
            with zipfile.ZipFile(archive) as stream:
                return values,stream.read(archive.stem+'/payload.zip')
        before,payload=package('1.0.0')
        installed=install_payload(payload,before,self.root/'plugins')
        original=(installed/'entry.py').read_bytes()
        (self.source/'entry.py').write_text('def open_plugin(context): return None')
        after,payload=package('1.0.1')
        replace=os.replace
        def fail_stage(source,target):
            if Path(source).name.startswith('.updating-'):
                raise OSError('simulated filesystem failure')
            return replace(source,target)
        with patch('thlib.client_plugins.os.replace',side_effect=fail_stage):
            with self.assertRaisesRegex(OSError,'simulated'):
                install_payload(payload,after,self.root/'plugins')
        self.assertEqual((installed/'entry.py').read_bytes(),original)
        self.assertEqual(list((self.root/'plugins').iterdir()),[installed])

    def test_batch_folder_is_plain_and_origin_is_metadata(self):
        (self.source/'plugin.json').write_text(json.dumps({'code':'th_batch_render','title':'Batch Render'}))
        archive=build_package(self.source,'1.0.0',self.root/'releases')
        values=read_package(archive)['metadata']
        with zipfile.ZipFile(archive) as stream:payload=stream.read(archive.stem+'/payload.zip')
        installed=install_payload(payload,dict(values,scope='first-server'),self.root/'plugins')
        other=install_payload(payload,dict(values,scope='other-server'),self.root/'plugins')
        self.assertEqual(installed,self.root/'plugins/batch_render')
        self.assertEqual(other,installed)
        self.assertEqual(json.loads((installed/'.release.json').read_text())['scope'],'other-server')
        self.assertEqual(list((self.root/'plugins').iterdir()),[installed])

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
                with self.assertRaisesRegex(ValueError,'new version'):
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
