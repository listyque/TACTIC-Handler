"""Copy the portable HTTP/MCP host, never the Stream server, into Handler."""
import argparse
import ast
from pathlib import Path

MODULES = ('__init__', 'admin_agent', 'agent_host', 'agent_worker', 'codex_session',
           'project_plan', 'automation_plan', 'dashboard_plan', 'sidebar_plan',
           'automation_trial', 'provider_host', 'provider_api', 'provider_credentials')


def files(stream):
    source = stream / 'src/tactic_stream'
    result = {'tactic_stream/' + name + '.py': (source / (name + '.py')).read_bytes() for name in MODULES}
    tree = ast.parse((source / 'admin_agent.py').read_text(encoding='utf-8'))
    references = next(ast.literal_eval(node.value) for node in tree.body
                      if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'REFERENCES'
                                                             for target in node.targets))
    for owner, path in references.values():
        if owner == 'TS':
            result[path] = (stream / path).read_bytes()
    result['requirements.txt'] = b'mcp==2.3.0\ncryptography>=46\n'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stream-root', required=True, type=Path)
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / 'thlib/agent_runtime'
    mismatches = []
    for path, content in files(options.stream_root).items():
        target = destination / path
        if not target.is_file() or target.read_bytes() != content:
            mismatches.append(path)
            if not options.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    if options.check and mismatches:
        raise SystemExit('Agent runtime copies differ: ' + ', '.join(mismatches))
    print('Agent runtime copies verified' if options.check else 'Agent runtime synchronized')


if __name__ == '__main__':
    main()
