"""The compiled Windows launcher preserves explicit and edition-specific profiles."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == 'nt', 'Windows native launcher')
class WindowsLaunchers(unittest.TestCase):
    def test_profile_ownership_in_standalone_combined_and_demo(self):
        root = Path(__file__).resolve().parents[1]
        compiler = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / 'пакет с пробелами'
            application = bundle / 'TACTIC-Handler'
            application.mkdir(parents=True)
            (application / 'launch.py').write_text('# launch target')
            runtime = bundle / 'runtime'
            runtime.mkdir()
            probe = bundle / 'Probe.cs'
            probe.write_text('using System; using System.IO; class Probe { static void Main() { '
                'File.WriteAllText(Environment.GetEnvironmentVariable("TH_TEST_OUTPUT"), '
                'Environment.GetEnvironmentVariable("TACTIC_HANDLER_SETTINGS_DIR")); } }')
            for source, target, references in [
                (probe, runtime / 'pythonw.exe', []),
                (root / 'tools/setup/Launcher.cs', bundle / 'TACTIC Handler.exe', ['/reference:System.Windows.Forms.dll']),
            ]:
                subprocess.run([str(compiler), '/nologo', '/utf8output', '/target:winexe', '/platform:x64',
                    '/out:' + str(target), *references, str(source)], check=True, capture_output=True, timeout=30)
            output = bundle / 'profile.txt'
            environment = {key: value for key, value in os.environ.items() if key != 'TACTIC_HANDLER_SETTINGS_DIR'}
            environment['TH_TEST_OUTPUT'] = str(output)
            def run():
                subprocess.run([str(bundle / 'TACTIC Handler.exe')], env=environment,
                    check=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
                return output.read_text(encoding='utf-8-sig')
            self.assertEqual(Path(run()), application)
            (bundle / 'TACTIC Stream.exe').write_bytes(b'edition marker')
            self.assertTrue(run().endswith('TACTIC Stream\\handler'))
            (bundle / 'demo').mkdir()
            (bundle / 'demo/manifest.json').write_text('{}')
            self.assertTrue(run().endswith('TACTIC Stream Demo\\handler'))
            profile = bundle / 'выбранный профиль'
            environment['TACTIC_HANDLER_SETTINGS_DIR'] = str(profile)
            self.assertEqual(Path(run()), profile)
