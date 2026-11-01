"""New RPC commands, Stream imports and HTTP routes require a legacy policy."""
import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'docs/tactic_compatibility/stream_boundaries.json'


def boundaries():
    result = set()
    for path in (ROOT / 'thlib').rglob('*.py'):
        relative = path.relative_to(ROOT).as_posix()
        local_runtime = relative.startswith('thlib/agent_runtime/')
        if relative.startswith('thlib/side/') and path.parent != ROOT / 'thlib/side/client/tactic_client_lib':
            continue  # Third-party libraries do not own Handler's server workflows.
        tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=relative)
        constants = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        constants[target.id] = node.value.value
        for node in ast.walk(tree):
            if not local_runtime and isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                offset = {'execute_cmd': 0, '_stream_command': 1}.get(node.func.attr)
                if node.func.attr == 'execute_cmd' and relative.endswith('/tactic_server_stub.py'):
                    offset = 1  # Wire arguments start with the ticket.
                if offset is not None and len(node.args) > offset:
                    target = node.args[offset]
                    value = target.value if isinstance(target, ast.Constant) else constants.get(getattr(target, 'id', ''))
                    result.add(('command', relative, str(value) if value is not None else ast.unparse(target)))
            if not local_runtime and isinstance(node, ast.ImportFrom) and ((node.module or '').startswith('tactic_stream')
                    or node.module in ('pyasm.biz.file_project', 'pyasm.common.errors')):
                result.add(('import', relative, node.module))
            if not local_runtime and isinstance(node, ast.Import):
                for name in node.names:
                    if name.name.startswith('tactic_stream'):
                        result.add(('import', relative, name.name))
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.startswith(('/admin/', '/file-project/')) and '\n' not in node.value:
                    result.add(('http', relative, node.value))
    return result


class StreamApiInventoryTests(unittest.TestCase):
    def test_every_boundary_has_a_reviewed_legacy_policy(self):
        records = json.loads(INVENTORY.read_text(encoding='utf-8'))
        recorded = {(row['kind'], row['path'], row['target']) for row in records}
        actual = boundaries()
        self.assertEqual(actual - recorded, set(), 'Classify new boundaries and test their legacy behavior')
        self.assertEqual(recorded - actual, set(), 'Remove stale boundary records')
        self.assertEqual(len(records), len(recorded), 'Duplicate boundary records')
        for record in records:
            self.assertTrue(record['legacy'], record)
