# module Tactic Classes
# file tactic_classes.py
# Global TACTIC Functions Module

import os
import sys
import time
import errno
import urlparse
import collections
from pprint import pprint
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import environment as env
import global_functions as gf
import lib.client.tactic_client_lib as tactic_client_lib
import xml.etree.ElementTree as Et
import ui_conf_classes

if env.Mode().get == 'maya':
    import ui_maya_dock
    import maya.cmds as cmds


class ServerThread(QtCore.QThread):
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)

        self.kwargs = None
        self.result = None

    def routine(self, **kwargs):
        pass

    def run(self):
        self.result = self.routine(**(self.kwargs or {}))


# server functions
def server_auth(host, project, login, password, new_ticket=False):
    tactic_srv = tactic_client_lib.TacticServerStub.get(setup=False)
    srv = host
    prj = project
    tactic_srv.set_server(srv)
    tactic_srv.set_project(prj)
    log = login
    psw = password
    ticket = env.Env().get_ticket()
    if not ticket:
        ticket = tactic_srv.get_ticket(log, psw)
        env.Env().set_ticket(ticket)
    if new_ticket:
        ticket = tactic_srv.get_ticket(log, psw)
        env.Env().set_ticket(ticket)
    tactic_srv.set_ticket(ticket)
    return tactic_srv


def get_server(new_ticket=False):
    return server_auth(
        env.Env().get_server(),
        env.Env().get_project(),
        env.Env().get_user(),
        env.Env().get_pass(),
        new_ticket,
    )


def server_start(first_run=False):
    try:
        server = get_server()
        return server
    except Exception as expected:
        if expected.errno == errno.ECONNREFUSED:
            server_restart(first_run)


def server_restart(first_run=False):
    def run_bat(restart=False):
        path = os.path.normpath(os.environ['TACTIC_INSTALL_DIR'] + os.sep + os.pardir)
        print('Starting TACTIC Server...')
        os.system(path + '/ServerRun.bat')
        print('Hold on for 3 seconds until server start...')
        time.sleep(3)
        server = get_server()

        if restart:
            ui_maya_dock.startup()
            conf_dialog.close()
        return server

    msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'TACTIC Server not running!',
                            "<p>Looks like TACTIC Server isn't running!</p> <p>Start Server?</p>",
                            QtGui.QMessageBox.NoButton, env.Inst().ui_main)
    msb.addButton("Yes", QtGui.QMessageBox.YesRole)
    msb.addButton("Retry", QtGui.QMessageBox.ApplyRole)
    msb.addButton("Open config", QtGui.QMessageBox.AcceptRole)
    msb.addButton("No", QtGui.QMessageBox.NoRole)
    msb.exec_()
    reply = msb.buttonRole(msb.clickedButton())

    if reply == QtGui.QMessageBox.YesRole:
        run_bat()
    if reply == QtGui.QMessageBox.AcceptRole:
        # print('OPEN CONFIG')
        conf_dialog = ui_conf_classes.Ui_configuration_dialogWidget()
        conf_dialog.configToolBox.setCurrentIndex(1)
        try_run = conf_dialog.buttonBox.addButton("Try Run", QtGui.QDialogButtonBox.YesRole)
        try_run.clicked.connect(lambda: run_bat(True))
        conf_dialog.show()

    if reply == QtGui.QMessageBox.NoRole:
        if env.Mode().get == 'maya':
            cmds.warning('Failed to run TACTIC Handler. TACTIC Server not running!')
        elif env.Mode().get == 'standalone':
            msg = QtGui.QMessageBox(QtGui.QMessageBox.Warning, 'Failed to run TACTIC Handler',
                                    'TACTIC Server not running!', QtGui.QMessageBox.NoButton, env.Inst().ui_main)
            msg.addButton("Close", QtGui.QMessageBox.AcceptRole)
            msg.exec_()
            rpl = msg.buttonRole(msg.clickedButton())
            if rpl == QtGui.QMessageBox.AcceptRole:
                sys.exit()
        else:
            print('Failed to run TACTIC Handler. TACTIC Server not running!')
        if first_run:
            sys.exit()


def ping_srv():
    try:
        result = server_start(True).fast_ping()
        print('TACTIC Server Ping: ' + result)
    except Exception as expected:
        result = False
        print(expected)
        server_restart(True)

    return result


# Query functions

def server_query(search_type, filters):
    """
    Server start and query
    :param search_type: query search type
    :param filters: query filters
    :return: dictionary
    """
    assets = None
    server = server_start()
    try:
        assets = server.query(search_type, filters)
    except Exception as exception:

        # Catch xmlrpc exception, ticket error
        if str(type(exception)) == "<class 'xmlrpclib.Fault'>":
            if exception.faultCode == 1:
                get_server(True)
                assets = server.query(search_type, filters)

        # Catch socket exception, connection error
        if str(type(exception)) == "<class 'socket.error'>":
            server_restart(False)

    return assets


def query_assets_names():
    search_type = 'sthpw/search_object'
    namespace = [env.Env().get_namespace(), env.Env().get_project()]

    filters = [('namespace', namespace)]

    assets = server_query(search_type, filters)

    result_tree = collections.defaultdict(list)

    for asset in assets:
        result_tree[asset['type']].append(asset)

    return result_tree


def query_tab_names(full_list=False):
    """
    Create Tabs from maya-type sTypes
    """
    search_type = 'sthpw/search_object'
    namespace = [env.Env().get_namespace(), env.Env().get_project()]

    if env.Mode().get == 'standalone':
        filters = [('type', env.Env().get_types_list()), ('namespace', namespace)]
    else:
        filters = [('type', env.Mode().get), ('namespace', namespace)]

    if full_list:
        filters = [('namespace', namespace)]

    assets = server_query(search_type, filters)

    out_tabs = {
        'names': [],
        'codes': [],
        'layouts': [],
        'colors': [],
    }
    if assets:
        for asset in assets:
            asset_get = asset.get
            out_tabs['names'].append(asset_get('title'))
            out_tabs['codes'].append(asset_get('code'))
            out_tabs['layouts'].append(asset_get('layout'))
            out_tabs['colors'].append(asset_get('color'))

    return out_tabs


# SObject class
class SObject(object):
    """
    Main class for all types of sobjects
    creates structured tree of objects
    to see all output:

    sobjects = get_sobjects(sobjects_list, snapshots_list)

    # test particular output example, outputs versioned and versionless snapshots
    for c, v in sobjects['PROPS00001'].process['Modeling'].contexts.iteritems():
        pprint(c)
        pprint(v.versionless)
        pprint(v.versions)

    # Test full output example, outputs all versioned and versionless snapshots
    for read in sobjects.iterkeys():
        print('____________________________________________:'+read+'____________________________________________')
        for key, value in sobjects[read].process.iteritems():
            for key2, val2 in value.contexts.iteritems():
                print('Process: {0},\n\nContext: {1}, \n\nSnapshot versionless: {2},\n\nSnapshot versions: {
                3}'.format(key, key2, value.contexts[key2].versionless, value.contexts[key2].versions))

    # Usage variants:
    # .get_snapshots()
    # .process['sculpt'].snapshots['maya']()  # gets all versionless snapshots per context typed 'maya'
    # .process['sculpt'].snapshots['context'].versions() # gets all dependent to context versions

    # .get_tasks()
    # .tasks['sculpt'].contexts['sculpt'].task['context'].get_notes() # gets notes per task context
    # .tasks['sculpt'].contexts['sculpt'].task['context'].notes # return all notes per task context

    # .get_notes()
    # .notes['sculpt'].notes()
    """

    def __init__(self, in_sobj=None, in_process=None):
        """
        :param in_sobj: input list with info on particular sobject
        :param in_process: list of current sobject possible process, need to query tasks per process
        :return:
        """

        # INPUT VARS
        self.info = in_sobj
        self.all_process = in_process

        # OUTPUT VARS
        self.process = {}
        self.tasks = {}
        self.notes = {}
        self.snapshots = {}

    # Snapshots by search code
    @staticmethod
    def query_snapshots(s_code, process=None, user=None):
        """
        Query for Snapshots
        :param s_code: Code of asset related to snapshot
        :param process: Process code
        :param user: Optional users names
        :return:
        """

        if process:
            filters = [('search_code', s_code), ('process', process), ('project_code', env.Env().get_project())]
        else:
            filters = [('search_code', s_code), ('project_code', env.Env().get_project())]

        return server_start().query_snapshots(filters=filters, include_files=True)

    # Tasks by search code
    @staticmethod
    def query_tasks(s_code, process=None, user=None):
        """
        Query for Task
        :param s_code: Code of asset related to task
        :param process: Process code
        :param user: Optional users names
        :return:
        """

        search_type = 'sthpw/task'
        if process:
            filters = [('search_code', s_code), ('process', process), ('project_code', env.Env().get_project())]
        else:
            filters = [('search_code', s_code), ('project_code', env.Env().get_project())]

        return server_query(search_type, filters)

    # Notes by search code
    @staticmethod
    def query_notes(s_code, process=None):
        """
        Query for Notes
        :param s_code: Code of asset related to note
        :param process: Process code
        :return:
        """
        search_type = 'sthpw/note'
        if process:
            filters = [('search_code', s_code), ('process', process), ('project_code', env.Env().get_project())]
        else:
            filters = [('search_code', s_code), ('project_code', env.Env().get_project())]

        return server_query(search_type, filters)

    # Query snapshots to update current
    def update_snapshots(self):
        snapshot_dict = query_snapshots(self.all_process, self.info['code'])
        self.init_snapshots(snapshot_dict)

    # Initial Snapshots by process without query
    def init_snapshots(self, snapshot_dict):
        process_set = set(snapshot['process'] for snapshot in snapshot_dict)

        for process in process_set:
            self.process[process] = Process(snapshot_dict, process)

    # Snapshots by SObject
    def get_snapshots(self):
        snapshots_list = self.query_snapshots(self.info['code'])
        process_set = set(snapshot['process'] for snapshot in snapshots_list)

        for process in process_set:
            self.snapshots[process] = Process(snapshots_list, process)

    # Tasks by SObject
    def get_tasks(self):
        tasks_list = self.query_tasks(self.info['code'])
        process_set = set(task['process'] for task in tasks_list)

        for process in process_set:
            self.tasks[process] = Process(tasks_list, process, True)

    # Notes by SObject
    def get_notes(self):
        notes_list = self.query_notes(self.info['code'])
        process_set = set(note['process'] for note in notes_list)

        for process in process_set:
            self.notes[process] = Process(notes_list, process, True)


class Process(object):
    def __init__(self, in_dict, process, single=False):
        # Contexts
        self.contexts = {}
        contexts = set()
        if single:
            items = collections.defaultdict(list)
            for item in in_dict:
                items[item['context']].append(item)
                if item['process'] == process:
                    contexts.add(item['context'])
            for context in contexts:
                self.contexts[context] = Contexts(single=items[context])
        else:
            versions = collections.defaultdict(list)
            versionless = collections.defaultdict(list)

            for snapshot in in_dict:
                if snapshot['process'] == process and snapshot['version'] == -1:
                    versionless[snapshot['context']].append(snapshot)
                elif snapshot['process'] == process and snapshot['version'] != -1:
                    versions[snapshot['context']].append(snapshot)
                if snapshot['process'] == process:
                    contexts.add(snapshot['context'])

            for context in contexts:
                self.contexts[context] = Contexts(versionless[context], versions[context])


class Contexts(object):
    def __init__(self, versionless=None, versions=None, single=None):
        if single:
            self.items = collections.OrderedDict()
            for item in single:
                self.items[item['code']] = SObject(item)
        else:
            self.versions = collections.OrderedDict()
            self.versionless = collections.OrderedDict()
            for sn in versions:
                self.versions[sn['code']] = Snapshot(sn)
            for sn in versionless:
                self.versionless[sn['code']] = Snapshot(sn)


class Snapshot(SObject, object):
    def __init__(self, snapshot):
        super(self.__class__, self).__init__(snapshot)

        self.files = collections.defaultdict(list)
        for fl in snapshot['__files__']:
            self.files[fl['type']].append(fl)

        self.snapshot = snapshot
        # delete unused big entries
        del self.snapshot['__files__'], self.snapshot['snapshot']


def get_sobjects(process_list=None, sobjects_list=None, get_snapshots=True):
    """
    Filters snapshot by search codes, and sobjects codes
    :param sobjects_list: full list of stypes
    :param get_snapshots: query for snapshots per sobject or not
    :return: dict of sObjects objects
    """
    sobjects = {}
    if get_snapshots:
        s_code = [s['code'] for s in sobjects_list]
        snapshots_list = query_snapshots(process_list, s_code)
        snapshots = collections.defaultdict(list)

        # filter snapshots by search_code
        for snapshot in snapshots_list:
            snapshots[snapshot['search_code']].append(snapshot)

        # append sObject info to the end of each search_code filtered list
        for sobject in sobjects_list:
            snapshots[sobject['code']].append(sobject)

        # creating dict or ready SObjects
        for k, v in snapshots.iteritems():
            sobjects[k] = SObject(v[-1], process_list)
            sobjects[k].init_snapshots(v[:-1])
    else:
        # Create list of Sobjects
        for sobject in sobjects_list:
            sobjects[sobject['code']] = SObject(sobject)

    return sobjects


def query_snapshots(process_list=None, s_code=None):
    """
    Query for snapshots belongs to asset
    :return: list of snapshots
    """
    process_codes = list(process_list)
    process_codes.extend(['icon', 'attachment', 'publish'])

    filters_snapshots = [
        ('process', process_codes),
        ('project_code', env.Env().get_project()),
        ('search_code', s_code),
    ]

    return server_start().query_snapshots(filters=filters_snapshots, include_files=True)


def assets_query(query, process, raw=False):
    """
    Query for searching assets
    """
    filters = []
    expr = ''
    if query[1] == 0:
        filters = [('name', 'EQI', query[0])]
    if query[1] == 1:
        filters = [('code', query[0])]
    if query[1] == 2:
        filters = None
        parents_codes = ['scenes_code', 'sets_code']
        for parent in parents_codes:
            expr += '@SOBJECT(cgshort/shot["{0}", "{1}"]), '.format(parent, query[0])
    if query[1] == 3:
        filters = [('description', 'EQI', query[0])]
    if query[1] == 4:
        filters = [('keywords', 'EQI', query[0])]

    if filters:
        assets = server_query(process, filters)
    else:
        assets = server_start().eval(expr)

    if raw:
        return assets
    out_assets = {
        'names': [],
        'codes': [],
        'description': [],
        'timestamp': [],
        'pipeline_code': [],
    }
    for asset in assets:
        # pprint(asset)
        asset_get = asset.get
        out_assets['names'].append(asset_get('name'))
        out_assets['codes'].append(asset_get('code'))
        out_assets['description'].append(asset_get('description'))
        out_assets['timestamp'].append(asset_get('timestamp'))
        out_assets['pipeline_code'].append(asset_get('pipeline_code'))

    return out_assets


def get_notes_count(sobject, process):
    expr = ''

    code = sobject.info['code']
    stub = server_start()
    search_type = stub.build_search_type(sobject.info['__search_key__'].split('?')[0])
    for proc in process:
        expr += '{' + "@COUNT(sthpw/note['process','{0}']['search_type', '{2}']['search_code', '{1}'])".format(proc,
                                                                                                               code,
                                                                                                               search_type) + '},'
    counts = stub.eval(expr)
    return counts


def context_query(process):
    """
    Query for Context elements
    Creating one list of lists, to reduce count of queries to the server
    :param process - list of tab names (vfx/asset)
    """

    search_type = 'sthpw/pipeline'

    filters = [('search_type', process), ('project_code', env.Env().get_project())]
    assets = server_query(search_type, filters)

    from lib.bs4 import BeautifulSoup

    if assets:
        # TODO may be worth it to simplify this
        # contexts = collections.OrderedDict()
        #
        # for proc in process:
        #     contexts[proc] = []
        #
        # items = contexts.copy()
        # for context in contexts:
        #     for asset in assets:
        #         if context == asset['search_type']:
        #             contexts[context] = Et.fromstring(asset['pipeline'].encode('utf-8'))
        #
        # for key, val in contexts.iteritems():
        #     if len(val):
        #         for element in val.iter('process'):
        #             items[key].append(element.attrib['name'])

        items = collections.OrderedDict()

        for proc in process:
            items[proc] = []

        for asset in assets:
            if asset['search_type'] in process:
                pipeline = BeautifulSoup(asset['pipeline'], 'html.parser')
                all_pipeline = []
                for pipe in pipeline.find_all('process'):
                    all_pipeline.append(pipe['name'])
                items[asset['search_type']] = all_pipeline

        return items


def users_query():
    """
    Query for Users
    :param asset_code: Code of asset related to task
    :param user: Optional users names
    :return:
    """
    search_type = 'sthpw/login'
    filters = []
    logins = server_query(search_type, filters)

    result = collections.OrderedDict()
    for login in logins:
        result[login['login']] = login

    return result


def create_sobject(name, description, keywords, search_type):
    data = {
        'name': name,
        'description': description,
        'keywords': keywords,
    }
    sobject = server_start().insert(search_type, data)

    return sobject


def checkin_playblast(snapshot_code, file_name):
    """
    :return:
    """

    # code = [('code', 'cgshort/props?project=the_pirate&code=PROPS00001')]
    # search_type = 'sthpw/message'
    #
    # message = server_query(search_type, code)
    #
    # from pprint import pprint
    # pprint(message[0]['message'])
    #
    # import json
    # data = json.loads(message[0]['message'])
    #
    # pprint(data)

    # subs = 'cgshort/props?project=the_pirate&code=PROPS00004'

    # subscribe = server_start().subscribe(subs, 'sobject')
    # print(subscribe)

    # snapshot_code = 'SNAPSHOT00000213'
    # path = 'D:/mountain.jpg'

    playblast = server_start().add_file(snapshot_code, file_name, file_type='playblast', mode='move', create_icon=True,
                                        file_naming='{sobject.name}_{snapshot.context}_{file.type}_v{version}.{ext}',
                                        checkin_type='auto')
    return playblast


def checkin_icon(snapshot_code, file_name):
    """
    :return:
    """

    icon = server_start().add_file(snapshot_code, file_name, file_type='main', mode='copy', create_icon=True,
                                   file_naming='{sobject.name}_{file.type}_v{version}.{ext}',
                                   checkin_type='auto')
    return icon


def create_snapshot(search_key, context):
    """
    :return:
    """
    snapshot = server_start().create_snapshot(search_key, context)
    return snapshot


def checkin_snapshot(search_key, context, file_path, file_type='main', is_current=True, description='', mode='move'):
    """
    :return:
    """

    snapshot = server_start().simple_checkin(
        search_key=search_key,
        context=context,
        file_path=file_path,
        description=description,
        file_type=file_type,
        is_current=is_current,
        mode=mode,
        create_icon=True,
    )

    return snapshot


def checkin_file():
    """
    :return:
    """

    snapshot_code = 'SNAPSHOT00000213'
    path = 'D:/empty.ma'
    playblast = server_start().add_file(snapshot_code, path, file_type='maya', mode='copy', create_icon=False,
                                        checkin_type='auto')
    return playblast


def update_description(search_key, description):
    data = {
        'description': description
    }
    transaction = server_start().update(search_key, data)

    return transaction


def add_note(search_key, process, context, note, note_html, login):
    search_type = "sthpw/note"

    data = {
        'process': process,
        'context': context,
        'note': note,
        'note_html': gf.html_to_hex(note_html),
        'login': login,
    }

    transaction = server_start().insert(search_type, data, parent_key=search_key, triggers=False)

    return transaction


def task_process_query(seach_key):
    # TODO Query task process per process
    from pprint import pprint
    processes = {}
    default_processes = ['Assignment', 'Pending', 'In Progress', 'Waiting', 'Need Assistance', 'Revise', 'Reject',
                         'Complete', 'Approved']
    default_colors = ['#ecbf7f', '#8ad3e5', '#e9e386', '#a96ccf', '#a96ccf', '#e84a4d', '#e84a4d', '#a3d991', '#a3d991']

    processes['process'] = default_processes
    processes['color'] = default_colors

    # process_expr = "@SOBJECT(sthpw/pipeline['search_type', 'sthpw/task'].config/process)"
    # process_expr = "@SOBJECT(sthpw/pipeline['code', 'the_pirate/Concept'].config/process)"
    # process_expr = "@SOBJECT(sthpw/pipeline['code', 'cgshort/props'].config/process)"
    # process_expr = "@SOBJECT(sthpw/subscription['login','{0}'])".format('admin')
    # process_expr = "@SOBJECT(sthpw/message_log['message_code','cgshort/characters?project=the_pirate&code=CHARACTERS00001'])"
    # process_list = server_start().eval(process_expr)
    # print(dir(thread_server_start()))
    # thr = ServerThread()
    # print(ServerThread().isRunning())

    # def rt():
    #
    #     filters = [('search_code', ['PROPS00001', 'PROPS00002', 'PROPS00003', 'PROPS00004','PROPS00005','PROPS00006','PROPS00007','PROPS00008','PROPS00009','PROPS00010','PROPS00011','PROPS00012','PROPS00013','PROPS00014','PROPS00015','PROPS00016','PROPS00017','PROPS00018','PROPS00019','PROPS00021']), ('project_code', 'the_pirate')]
    #     return thr.server.query_snapshots(filters=filters, include_files=True)
    # return thr.server.get_all_children('cgshort/props?project=the_pirate&code=PROPS00001', 'sthpw/snapshot')
    # return asd
    # thr.routine = rt
    # print(thr.isRunning())
    # thr.start()
    # print(thr.isRunning())
    #
    # def print_result():
    #     print(thr.result)
    #
    # thr.finished.connect(print_result)
    # pprint(asd)


    code = [('message_code', 'cgshort/characters?project=the_pirate&code=CHARACTERS00001')]
    search_type = 'sthpw/message_log'

    message = server_query(search_type, code)

    # from pprint import pprint
    print('from task_process_query!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    # pprint(message)
    print(message[0])
    import json
    data = json.loads(message[0]['message'])
    pprint(data)
    # if (len(process_list) == 0):
    #     process_list = default_processes


    # print('from task_process_query!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    # pprint(process_list)

    return processes


def task_priority_query(seach_key):
    """
    Takes info from html widget, to get priority values
    :return: tuple lavel - value
    """
    # TODO Use this method, and make it templates
    # defin = server_start().get_config_definition('sthpw/task', 'edit_definition', 'priority')
    # print('from task_priority_query')
    # print(defin)

    class_name = 'tactic.ui.manager.EditElementDefinitionWdg'

    args = {
        'config_xml': '',
        'element_name': 'priority',
        'path': '/Edit/priority',
        'search_type': 'sthpw/task',
        'view': 'edit_definition',
    }

    widget_html = server_start().get_widget(class_name, args, [])

    import re

    values_expr = '<values>(.*?)</values>'
    values_pattern = re.compile(values_expr)
    values_result = re.findall(values_pattern, widget_html)
    values = values_result[0].split('|')

    labels_expr = '<labels>(.*?)</labels>'
    labels_pattern = re.compile(labels_expr)
    labels_result = re.findall(labels_pattern, widget_html)
    labels = labels_result[0].split('|')

    result = zip(labels, values)

    return result


# Skey funtions

def parce_skey(skey):
    skey_splitted = urlparse.urlparse(skey)
    skey_dict = dict(urlparse.parse_qsl(skey_splitted.query))
    skey_dict['namespace'] = skey_splitted.netloc
    skey_dict['pipeline_code'] = skey_splitted.path[1:]

    if skey_splitted.scheme == 'skey':
        if skey_dict['pipeline_code'] == 'snapshot':
            skey_dict['type'] = 'snapshot'
            snapshot = server_query('sthpw/snapshot', [('code', skey_dict.get('code'))])
            if snapshot:
                snapshot = snapshot[0]
                skey_dict['pipeline_code'] = snapshot['search_type'].split('/')[-1].split('?')[0]
                skey_dict['namespace'] = snapshot['search_type'].split('/')[0]
                skey_dict['project'] = snapshot['project_code']
                skey_dict['context'] = snapshot['context']
                skey_dict['code'] = snapshot['search_code']
                skey_dict['item_code'] = snapshot['code']
        else:
            skey_dict['type'] = 'sobject'
            if not skey_dict.get('context'):
                skey_dict['context'] = '_no_context_'
        return skey_dict
    else:
        return None


def generate_skey(pipeline_code=None, code=None):
    skey = 'skey://{0}/{1}?project={2}&code={3}'.format(env.Env().get_namespace(),
                                                        pipeline_code,
                                                        env.Env().get_project(),
                                                        code)

    return skey
