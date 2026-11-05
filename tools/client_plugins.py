"""Build or publish desktop-only plugins using a running TH's native legacy API."""
import argparse
from getpass import getpass
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from thlib.client_plugins import build_package


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    build = sub.add_parser('build')
    build.add_argument('--source', type=Path, default=ROOT / 'plugins/batch_render')
    build.add_argument('--version', required=True)
    build.add_argument('--output', type=Path, required=True)
    publish = sub.add_parser('publish')
    publish.add_argument('archive', type=Path)
    publish.add_argument('--server', required=True)
    publish.add_argument('--project', required=True)
    publish.add_argument('--login', required=True)
    arguments = parser.parse_args()
    if arguments.action == 'build':
        print(build_package(arguments.source, arguments.version, arguments.output))
        return
    from thlib.side.client.tactic_client_lib import TacticServerStub
    from thlib.client_plugin_server import publish as publish_package
    if input('Publish to ' + arguments.server + ' / ' + arguments.project + '? Type yes: ') != 'yes':
        return
    server = TacticServerStub(setup=False, protocol='xmlrpc')
    server.set_server(arguments.server)
    server.set_project(arguments.project)
    server.set_ticket(server.get_ticket(arguments.login, getpass('Password: ')))
    result = publish_package(server, arguments.project, arguments.archive)
    print('Published', result['code'], result['version'])


if __name__ == '__main__':
    main()
