"""Owned subprocess lifecycle and the independently shipped agent client."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from uuid import uuid4

from thlib.local_agent import LocalAgents, RUNTIME


class LocalAgent(unittest.TestCase):
    def wait(self, owner, state):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            reports = owner.reports()
            if reports.get('one', {}).get('state') == state:
                return reports['one']
            time.sleep(.02)
        self.fail(str(reports))

    def test_owned_process_start_retry_stop_failure_and_ticket_redaction(self):
        with tempfile.TemporaryDirectory() as temporary:
            owner = LocalAgents(temporary)
            fixture = Path(temporary) / 'tactic_stream'
            fixture.mkdir()
            (fixture / '__init__.py').write_text('__path__.append(%r)' % str(RUNTIME / 'tactic_stream'))
            host = fixture / 'agent_host.py'
            host.write_text('import time\ndef main(*, connected=None):\n connected()\n while True: time.sleep(.05)\n')
            popen = subprocess.Popen
            commands = []
            def launch(command, **values):
                commands.append((command, values['env']))
                values['env']['PYTHONPATH'] = temporary
                values['cwd'] = temporary
                return popen(command, **values)
            try:
                with patch.object(owner, 'prepare', return_value=Path(sys.executable)), patch('thlib.local_agent.subprocess.Popen', side_effect=launch):
                    operation = str(uuid4())
                    owner.start('one', operation, 'http://127.0.0.1:9', 'private-test-ticket')
                    self.wait(owner, 'connected')
                    owner.start('one', operation, 'http://127.0.0.1:9', 'private-test-ticket')
                    self.assertEqual(len(commands), 1)
                    self.assertNotIn('private-test-ticket', ' '.join(commands[0][0]))
                    self.assertEqual(commands[0][1]['TACTIC_AGENT_TICKET'], 'private-test-ticket')
                    stop = str(uuid4())
                    owner.stop('one', stop)
                    self.assertEqual(self.wait(owner, 'stopped')['operation'], stop)
                    owner.runs['one']['thread'].join(timeout=3)
                    host.write_text('import os\ndef main(*, connected=None):\n raise RuntimeError(os.environ["TACTIC_AGENT_TICKET"])\n')
                    owner.start('one', str(uuid4()), 'http://127.0.0.1:9', 'private-test-ticket')
                    failed = self.wait(owner, 'failed')
                    self.assertIn('[REDACTED]', failed['error'])
                    self.assertNotIn('private-test-ticket', str(owner.reports()))
            finally:
                owner.close()
                owner.runs['one']['thread'].join(timeout=12)
            self.assertFalse(owner.runs['one']['thread'].is_alive())

    def test_bundle_references_and_no_server_imports(self):
        import ast
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        from sync_agent_runtime import MODULES
        for name in MODULES:
            tree = ast.parse((RUNTIME / 'tactic_stream' / (name + '.py')).read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse((node.module or '').startswith(('pyasm', 'tactic.ui', 'tactic_stream.server')))


if __name__ == '__main__':
    unittest.main()
