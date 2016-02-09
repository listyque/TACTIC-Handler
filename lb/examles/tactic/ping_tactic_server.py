import sys

sys.path.append('D:/tactic/tactic-4.4/src/client')

from tactic_client_lib import TacticServerStub
import xml.etree.ElementTree as ET

def server_auth(server = 'localhost:9123', project='', login='', password=''):
    tactic_serv = TacticServerStub.get(setup=False)
    srv = server
    prj = project
    tactic_serv.set_server(srv)
    tactic_serv.set_project(prj)
    log = login
    psw = password
    ticket = tactic_serv.get_ticket(log, psw)
    tactic_serv.set_ticket(ticket)

    return tactic_serv


def start_server(command='start'):
    server = server_auth('localhost:9123', 'exam', 'admin', 'admin')
    if command == 'start':
        server.start('Start server as Singleton')
    elif command == 'finish':
        server.finish('Server finish!')
    elif command == 'auth':
        pass
    else:
        server.abort()
    return server

server = start_server()


def ping():
    print server.ping()


def query():
    # search_type = 'exam/props'
    search_type = 'sthpw/search_object?code=exam'
    filters = []
    filters.append(('type', 'maya'))
    assets = server.query(search_type, filters)
    print('found [%s] assets' % len(assets) )
    # print(assets)
    for asset in assets:
        code = asset.get('title')
        print(code)

def query_pipeline():
    # search_type = 'exam/props'
    search_type = 'sthpw/pipeline?code=exam/props'
    filters = [('search_type', 'exam/props')]
    assets = server.query(search_type, filters)
    xml = assets[0].get('pipeline')
    root = ET.fromstring(xml)
    for neighbor in root.iter('process'):
        print neighbor.attrib['name']


def main():
    # ping()
    query_pipeline()

    start_server('finish')

if __name__ == '__main__':
    main()

