from pathlib import Path
import io
import json
import tempfile
import unittest
import zipfile
from thlib.client_plugins import build_package, read_package, cache_payload, payload_files, manifest_metadata


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
        cached = cache_payload(payload, package['metadata'], self.root / 'cache')
        self.assertTrue((cached / 'entry.py').is_file())
        self.assertEqual(cache_payload(payload, package['metadata'], self.root / 'cache'), cached)
        (cached / 'entry.py').write_text('modified')
        with self.assertRaisesRegex(ValueError, 'modified'):
            cache_payload(payload, package['metadata'], self.root / 'cache')

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

    def test_vm_dispatcher_body_is_preserved(self):
        source = Path(__file__).parents[1] / 'plugins/batch_render/dispatcher.py'
        import hashlib
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         '15b45a92abb641c66fdd4fd1a4eda7c2fb9c9e0cb694cf8b4d9b20c1a1d5df48')
