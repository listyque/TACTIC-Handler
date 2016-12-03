# module Tactic Classes
# file tactic_classes.py
# Global TACTIC Functions Module

import os
import sys
import shutil
import traceback
import urlparse
import collections
import json
from lib.side.bs4 import BeautifulSoup
from lib.side.Qt import QtGui
from lib.side.Qt import QtCore
import lib.proxy as proxy
from lib.environment import env_mode, env_server, env_inst
import global_functions as gf
import tactic_query as tq
import lib.ui_classes.ui_misc_classes as ui_misc_classes
import side.client.tactic_client_lib as tactic_client_lib


if env_mode.get_mode() == 'maya':
    import maya.cmds as cmds


class ServerThread(QtCore.QThread):
    def __init__(self, parent=None):
        super(ServerThread, self).__init__(parent=parent)

        self.kwargs = None
        self.result = None
        self.connected = False
        self.failed = False

    def isConnected(self):
        return self.connected

    def setConnected(self, boolean):
        self.connected = boolean

    def isFailed(self):
        return self.failed

    def setFailed(self, boolean):
        self.failed = boolean

    def routine(self, **kwargs):
        pass

    def run(self):
        try:
            self.result = self.routine(**(self.kwargs or {}))
            self.setFailed(False)
        except Exception as expected:
            self.setFailed(True)

            traceback.print_exc(file=sys.stdout)
            stacktrace = traceback.format_exc()

            exception = {
                'exception': expected,
                'stacktrace': stacktrace,
            }
            self.result = exception


def get_server_thread(kwargs_dict, runnable_func, connected_func, parent=None):
    thread = ServerThread(parent)

    if not thread.isRunning():
        thread.kwargs = kwargs_dict
        thread.routine = runnable_func

        if not thread.isConnected():
            thread.finished.connect(connected_func)
            thread.setConnected(True)
            # thread.start()

    return thread


def treat_result(thread, silent=False):
    if silent:
        return thread
    if thread.isFailed():
        print 'ERROR TREATING'
        return error_handle(thread)
    else:
        return thread


def server_auth(host, project=None, login=None, password=None, site=None, get_ticket=False):
    server = tactic_client_lib.TacticServerStub.get(protocol='xmlrpc', setup=False)
    if env_server.get_proxy()['enabled']:
        transport = proxy.UrllibTransport()
        server.set_transport(transport)
    else:
        if server.transport:
            server.transport.update_proxy()
        server.set_transport(None)

    server.set_server(host)
    server.set_project(project)
    server.set_site(site)

    ticket = env_server.get_ticket()
    if not ticket or get_ticket:
        ticket = server.get_ticket(login, password, site)
        if type(ticket) == dict:
            if ticket.get('exception'):
                return server
        else:
            env_server.set_ticket(ticket)

    server.set_ticket(ticket)

    return server


def server_start(get_ticket=False):
    server = server_auth(
        env_server.get_server(),
        env_inst.current_project,
        env_server.get_user(),
        '',
        env_server.get_site()['site_name'],
        get_ticket=get_ticket,
    )
    return server


def show_message_predefined(title, message, stacktrace=None, buttons=None, parent=None, message_type='question'):
    """
    Showing message with title, text and returns pressed button
    :param title: 'Message Title'
    :param message: 'Message Text'
    :param message_type: 'question', 'warning', etc...
    :param buttons: tuple of buttons: (('Yes', QtGui.QMessageBox.YesRole), ('No', QtGui.QMessageBox.NoRole)), etc...
    :return: button role
    """
    if not buttons:
        buttons = (('Yes', QtGui.QMessageBox.YesRole), ('No', QtGui.QMessageBox.NoRole))

    if message_type == 'warning':
        msb_type = QtGui.QMessageBox.Warning
    elif message_type == 'information':
        msb_type = QtGui.QMessageBox.Information
    elif message_type == 'critical':
        msb_type = QtGui.QMessageBox.Critical
    else:
        msb_type = QtGui.QMessageBox.Question

    message_box = QtGui.QMessageBox(
        msb_type,
        title,
        message,
        QtGui.QMessageBox.NoButton,
        parent,
    )

    if stacktrace:
        layout = QtGui.QVBoxLayout()

        collapse_wdg = ui_misc_classes.Ui_collapsableWidget()
        collapse_wdg.setLayout(layout)
        collapse_wdg.setText('Hide Stacktrace')
        collapse_wdg.setCollapsedText('Show Stacktrace')
        collapse_wdg.setCollapsed(True)

        msb_layot = message_box.layout()
        msb_layot.addWidget(collapse_wdg, 1, 1)

        text_edit = QtGui.QPlainTextEdit()
        text_edit.setMinimumWidth(600)
        text_edit.setPlainText(stacktrace)

        layout.addWidget(text_edit)

    for title, role in buttons:
        message_box.addButton(title, role)

    message_box.exec_()
    return message_box.buttonRole(message_box.clickedButton())


def catch_error_type(exception):
    # print('Some exception appeared!', str(type(exception)), unicode(str(exception), 'utf-8', errors='ignore'))

    error = 'unknown_error'

    # Catch project existance
    if str(exception).find('No project') != -1:
        error = 'no_project_error'

    # Catch ticket error
    if str(exception).find('Cannot login with key:') != -1:
        error = 'ticket_error'

    # Catch socket exception, connection error
    if str(exception).find(
            'A connection attempt failed because the connected party did not properly respond after a period of time') != -1:
        error = 'connection_timeout'

    # Catch Connection refused
    if str(exception).find('No connection could be made because the target machine actively refused it') != -1:
        error = 'connection_refused'

    if str(exception).find('Connection refused') != -1:
        error = 'connection_refused'

    if str(exception).find('Login/Password combination incorrect') != -1:
        error = 'login_pass_error'

    if str(exception).find('connect to MySQL server') != -1:
        error = 'sql_connection_error'

    if str(exception).find('ProtocolError') != -1:
        error = 'protocol_error'

    return error


def generate_new_ticket(explicit_username=None, parent=None):
    login_pass_dlg = QtGui.QMessageBox(
        QtGui.QMessageBox.Question,
        'Updating ticket',
        'Enter Your Login and Password.',
        QtGui.QMessageBox.NoButton,
        parent,
    )
    layout = QtGui.QGridLayout()

    wdg = QtGui.QWidget()
    wdg.setLayout(layout)

    msb_layot = login_pass_dlg.layout()
    msb_layot.addWidget(wdg, 1, 1)

    # Labels
    login_label = QtGui.QLabel('Login: ')
    pass_label = QtGui.QLabel('Password: ')

    # Line Edits
    login_line_edit = QtGui.QLineEdit()
    if explicit_username:
        login_line_edit.setText(explicit_username)
    else:
        login_line_edit.setText(env_server.get_user())
    pass_line_edit = QtGui.QLineEdit()
    pass_line_edit.setEchoMode(QtGui.QLineEdit.Password)

    layout.addWidget(login_label, 0, 0)
    layout.addWidget(login_line_edit, 0, 1)
    layout.addWidget(pass_label, 1, 0)
    layout.addWidget(pass_line_edit, 1, 1)

    pass_line_edit.setFocus()

    login_pass_dlg.exec_()

    host = env_server.get_server()
    #TODO SOMETHING
    project = 'sthpw'
    login = login_line_edit.text()
    password = pass_line_edit.text()
    site = env_server.get_site()['site_name']

    thread = get_server_thread(
        dict(),
        lambda: server_auth(host, project, login, password, site, get_ticket=True),
        server_ping,
        parent=parent
    )
    thread.start()
    treat_result(thread)
    thread.wait()
    return thread


def run_tactic_team_server():

    path = os.path.normpath(env_server.get_install_dir() + os.sep + os.pardir)
    print('Starting TACTIC Server... Press Retry after server started!', path)
    os.system(path + '/ServerRun.bat')


def error_handle(thread):
    expected = thread.result['exception']

    error = catch_error_type(expected)

    exception_text = u'Exception type: {0},<p>{1}</p><p><b>Catched Error: {2}</b></p>'.format(unicode(str(type(expected)), 'utf-8', errors='ignore'),
                                                                                              unicode(str(expected), 'utf-8', errors='ignore'),
                                                                                              str(error))
    if (error == 'connection_refused') or (error == 'connection_timeout'):
        title = '{0}, {1}'.format("Cannot connect to TACTIC Server!", error)
        message = u'{0}<p>{1}</p>'.format(
            u"<p>Looks like TACTIC Server isn't running! May be You need to set up Right Server port and address</p>"
            u"<p>Start Server? (Only TACTIC Team)</p>",
            exception_text)
        buttons = [('Yes', QtGui.QMessageBox.YesRole),
                   ('No', QtGui.QMessageBox.NoRole),
                   ('Retry', QtGui.QMessageBox.ApplyRole)]

        if not env_inst.ui_conf:
            buttons.append(('Open Config', QtGui.QMessageBox.ActionRole))

        reply = show_message_predefined(
            title=title,
            message=message,
            stacktrace=thread.result['stacktrace'],
            buttons=buttons,
            parent=None,
            message_type='critical',
        )
        if reply == QtGui.QMessageBox.YesRole:
            run_tactic_team_server()
            thread.result = QtGui.QMessageBox.ApplyRole
        if reply == QtGui.QMessageBox.ApplyRole:
            thread.result = reply
        if reply == QtGui.QMessageBox.ActionRole:
            thread.result = reply

        return thread

    if error == 'unknown_error':
        title = '{0}, {1}'.format("Unknown Error!", error)
        message = u'{0}<p>{1}</p>'.format(
            u"<p>This is no usual type of Exception! See stacktrace for information</p>",
            exception_text)
        buttons = [('Ok', QtGui.QMessageBox.NoRole),
                   ('Retry', QtGui.QMessageBox.ApplyRole)]

        if not env_inst.ui_conf:
            buttons.append(('Open Config', QtGui.QMessageBox.ActionRole))

        reply = show_message_predefined(
            title=title,
            message=message,
            stacktrace=thread.result['stacktrace'],
            buttons=buttons,
            parent=None,
            message_type='question',
        )
        if reply == QtGui.QMessageBox.ApplyRole:
            thread.result = reply
        if reply == QtGui.QMessageBox.ActionRole:
            thread.result = reply

        return thread

    if error == 'ticket_error':
        title = '{0}, {1}'.format("Ticket Error!", error)
        message = u'{0}<p>{1}</p>'.format(
            u"<p>Wrong ticket, or session may have expired!</p> <p>Generate new ticket?</p>",
            exception_text)
        buttons = [('Yes', QtGui.QMessageBox.YesRole),
                   ('No', QtGui.QMessageBox.NoRole)]

        if not env_inst.ui_conf:
            buttons.append(('Open Config', QtGui.QMessageBox.ActionRole))

        reply = show_message_predefined(
            title=title,
            message=message,
            stacktrace=thread.result['stacktrace'],
            buttons=buttons,
            parent=None,
            message_type='question',
        )
        if reply == QtGui.QMessageBox.YesRole:
            generate_new_ticket()
            thread.result = QtGui.QMessageBox.ApplyRole
        if reply == QtGui.QMessageBox.ActionRole:
            thread.result = reply

        return thread

    if error == 'no_project_error':
        title = '{0}, {1}'.format("This Project does not exists!", error)
        message = u'{0}<p>{1}</p>'.format(
            u"<p>You set up wrong Porject Name, or Project not exist!</p> <p>Reset Project to \"sthpw\"?</p>",
            exception_text)
        buttons = [('Yes', QtGui.QMessageBox.YesRole),
                   ('No', QtGui.QMessageBox.NoRole)]

        if not env_inst.ui_conf:
            buttons.append(('Open Config', QtGui.QMessageBox.ActionRole))

        reply = show_message_predefined(
            title=title,
            message=message,
            stacktrace=thread.result['stacktrace'],
            buttons=buttons,
            parent=None,
            message_type='critical',
        )
        if reply == QtGui.QMessageBox.YesRole:
            env_server.set_project('sthpw')
            env_inst.ui_main.restart_ui_main()
        if reply == QtGui.QMessageBox.ActionRole:
            thread.result = reply

        return thread

    if error == 'login_pass_error':
        title = '{0}, {1}'.format("Wrong user Login or Password for TACTIC Server!", error)
        message = u'{0}<p>{1}</p>'.format(
            u"<p>You need to open config, and type correct Login and Password!</p>",
            exception_text)
        buttons = [('Ok', QtGui.QMessageBox.NoRole)]

        if not env_inst.ui_conf:
            buttons.append(('Open Config', QtGui.QMessageBox.ActionRole))

        reply = show_message_predefined(
            title=title,
            message=message,
            stacktrace=thread.result['stacktrace'],
            buttons=buttons,
            parent=None,
            message_type='critical',
        )
        if reply == QtGui.QMessageBox.ActionRole:
            thread.result = reply

        return thread

    if error == 'sql_connection_error':
        title = '{0}, {1}'.format("SQL Server Error!", error)
        message = u'{0}<p>{1}</p>'.format(
            u"<p>TACTIC Server can't connect to SQL server, may be SQL Server Down! Or wrong server port/ip </p>",
            exception_text)
        buttons = [('Ok', QtGui.QMessageBox.NoRole)]

        if not env_inst.ui_conf:
            buttons.append(('Open Config', QtGui.QMessageBox.ActionRole))

        reply = show_message_predefined(
            title=title,
            message=message,
            stacktrace=thread.result['stacktrace'],
            buttons=buttons,
            parent=None,
            message_type='critical',
        )
        if reply == QtGui.QMessageBox.ActionRole:
            thread.result = reply

        return thread

    if error == 'protocol_error':
        title = '{0}, {1}'.format("Error with the Protocol!", error)
        message = u'{0}<p>{1}</p>'.format(u"<p>Something wrong!</p>", exception_text)
        buttons = [('Ok', QtGui.QMessageBox.NoRole),
                   ('Retry', QtGui.QMessageBox.ApplyRole)]

        if not env_inst.ui_conf:
            buttons.append(('Open Config', QtGui.QMessageBox.ActionRole))

        reply = show_message_predefined(
            title=title,
            message=message,
            stacktrace=thread.result['stacktrace'],
            buttons=buttons,
            parent=None,
            message_type='critical',
        )
        if reply == QtGui.QMessageBox.ActionRole:
            thread.result = reply
        if reply == QtGui.QMessageBox.ApplyRole:
            thread.result = reply

        return thread


def server_ping():
    if server_start():
        if server_start().fast_ping() == 'OK':
            return True
        else:
            return False
    else:
        return False


def server_fast_ping():
    server = tactic_client_lib.TacticServerStub.get(protocol='xmlrpc', setup=False)
    if env_server.get_proxy()['enabled']:
        transport = proxy.UrllibTransport()
        server.set_transport(transport)
    else:
        if server.transport:
            server.transport.update_proxy()
        server.set_transport(None)
    server.set_server(env_server.get_server())

    if server.fast_ping() == 'OK':
        del server
        return 'ping_ok'
    else:
        del server
        return 'ping_fail'


# Projects related classes
class Project(object):
    def __init__(self, project):

        self.info = project
        self.stypes = None
        self.workflow = None

    def get_stypes(self):
        # import time
        #
        # start = time.time()
        # print("start")

        self.stypes = self.query_search_types()

        # end = time.time()
        # print(end - start)

        return self.stypes

    def query_search_types(self):

        kwargs = {
            'project_code': self.info.get('code'),
            'namespace': self.info.get('type')
        }
        code = tq.prepare_serverside_script(tq.query_search_types_extended, kwargs, return_dict=True)

        result = server_start().execute_python_script('', kwargs=code)

        stypes = json.loads(result['info']['spt_ret_val'])

        schema = stypes.get('schema')
        pipelines = stypes.get('pipelines')
        stypes = stypes.get('stypes')

        if schema:
            prj_schema = schema[0]['schema']
        else:
            prj_schema = None

        if not (pipelines or schema):
            return None
        else:
            return self.get_all_search_types(stypes, pipelines, prj_schema)

    def get_all_search_types(self, stype_list, process_list, schema):

        pipeline = BeautifulSoup(schema, 'html.parser')
        all_connectionslist = []
        dct = collections.defaultdict(list)

        for pipe in pipeline.find_all(name='connect'):
            all_connectionslist.append(pipe.attrs)

        for pipe in pipeline.find_all(name='search_type'):
            dct[pipe.attrs['name']].append({'search_type': pipe.attrs})

            conn = {
                'children': [],
                'parents': [],
            }
            for connect in all_connectionslist:
                if pipe.attrs['name'] == connect['from']:
                    conn['parents'].append(connect)
                if pipe.attrs['name'] == connect['to']:
                    conn['children'].append(connect)

            dct[pipe.attrs['name']].append(conn)

        # getting workflow here
        self.workflow = Workflow(process_list)

        # getting stypes processes here
        stypes_objects = collections.OrderedDict()
        for stype in stype_list:
            stype_process = collections.OrderedDict()
            stype_schema = dct.get(stype['code'])

            for process in process_list:
                # print process
                if dct.get(stype['code']):
                    if process['search_type'] == dct.get(stype['code'])[0]['search_type']['name']:
                        stype_process[process['code']] = process
            # print stype_process
            stype_obj = SType(stype, stype_schema, stype_process, project=self)
            stypes_objects[stype['code']] = stype_obj

        return stypes_objects


# sTypes related classes
class SType(object):
    """

    .schema.info
    .schema.parents
    .schema.children

    .pipeline.info
    .pipeline.process
    .pipeline.process['Blocking'].get('parents')
    .pipeline.process['Blocking'].get('children')

    """
    def __init__(self, stype, schema=None, pipelines=None, project=None):

        self.info = stype
        self.project = project
        self.schema = None
        self.pipeline = self.get_pipelines(pipelines)

        if schema:
            self.schema = Schema(schema)

    @staticmethod
    def get_pipelines(pipelines):

        ready_pipeline = collections.OrderedDict()
        if pipelines:
            for key, pipeline in pipelines.iteritems():
                ready_pipeline[key] = Pipeline(pipeline)

        if ready_pipeline:
            return ready_pipeline


class Schema(object):
    def __init__(self, schema_dict):

        self.__schema_dict = schema_dict
        self.info = self.get_info()

        self.parents = self.get_parents()
        self.children = self.get_children()

    def get_info(self):
        return self.__schema_dict[0]['search_type']

    def get_parents(self):
        return self.__schema_dict[1].get('parents')

    def get_children(self):
        return self.__schema_dict[1].get('children')


class Workflow(object):
    def __init__(self, pipeline):

        self.__pipeline_list = pipeline

    def get_child_pipeline_by_process_code(self, parent_pipeline, process):
        parent_process = None
        if parent_pipeline.processes:
            for proc in parent_pipeline.processes:
                if proc['process'] == process:
                    parent_process = proc

        return self.get_pipeline_by_parent(parent_process)

    def get_pipeline_by_parent(self, parent_process):
        for pipe in self.__pipeline_list:
            if pipe['parent_process'] == parent_process['code']:
                return Pipeline(pipe)

    def get_by_stype(self):
        pass

    def get_pipeline(self):

        from pprint import pprint

        for pipe in self.__pipeline_list:
            pprint(pipe)

        return self.__pipeline_list


class Pipeline(object):
    def __init__(self, process):

        self.__process_dict = process

        self.process = collections.OrderedDict()

        self.get_pipeline()
        self.processes = self.get_processes()
        self.info = self.get_info()

    def get_processes(self):
        return self.__process_dict['stypes_processes']

    def get_info(self):
        return self.__process_dict

    def get_pipeline(self):

        all_connectionslist = []
        pipeline = BeautifulSoup(self.__process_dict['pipeline'], 'html.parser')

        for pipe in pipeline.find_all(name='connect'):
            all_connectionslist.append(pipe.attrs)

        for pipe in pipeline.find_all(name='process'):
            self.process[pipe.attrs.get('name')] = pipe.attrs

            for connect in all_connectionslist:
                if pipe.attrs['name'] == connect['from']:
                    self.process[pipe.attrs.get('name')]['parents'] = connect
                if pipe.attrs['name'] == connect['to']:
                    self.process[pipe.attrs.get('name')]['children'] = connect


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

    def __init__(self, in_sobj=None, in_process=None, project=None):
        """
        :param in_sobj: input list with info on particular sobject
        :param in_process: list of current sobject possible process, need to query tasks per process
        :return:
        """

        # INPUT VARS
        self.info = in_sobj
        self.all_process = in_process
        self.project = project

        # OUTPUT VARS
        self.process = {}
        self.tasks = {}
        self.notes = {}
        self.snapshots = {}

    # Snapshots by search code
    def query_snapshots(self, s_code, process=None, user=None):
        """
        Query for Snapshots
        :param s_code: Code of asset related to snapshot
        :param process: Process code
        :param user: Optional users names
        :return:
        """

        if process:
            filters = [('search_code', s_code), ('process', process), ('project_code', self.project.info['code'])]
        else:
            filters = [('search_code', s_code), ('project_code', self.project.info['code'])]

        return server_start().query_snapshots(filters=filters, include_files=True)

    # Tasks by search code
    def query_tasks(self, s_code, process=None, user=None):
        """
        Query for Task
        :param s_code: Code of asset related to task
        :param process: Process code
        :param user: Optional users names
        :return:
        """
        server = server_start()

        search_type = 'sthpw/task'
        if process:
            filters = [('search_code', s_code), ('process', process), ('project_code', self.project.info['code'])]
        else:
            filters = [('search_code', s_code), ('project_code', self.project.info['code'])]

        return server.query(search_type, filters)

    # Notes by search code
    def query_notes(self, s_code, process=None):
        """
        Query for Notes
        :param s_code: Code of asset related to note
        :param process: Process code
        :return:
        """
        server = server_start()

        search_type = 'sthpw/note'
        if process:
            filters = [('search_code', s_code), ('process', process), ('project_code', self.project.info['code'])]
        else:
            filters = [('search_code', s_code), ('project_code', self.project.info['code'])]

        return server.query(search_type, filters)

    # Query snapshots to update current
    def update_snapshots(self):
        snapshot_dict = self.query_snapshots(self.info['code'])
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
                if snapshot['process'] == process and (snapshot['version'] == -1 or snapshot['version'] == 0):
                    versionless[snapshot['context']].append(snapshot)
                elif snapshot['process'] == process and (snapshot['version'] != -1 or snapshot['version'] != 0):
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

# End of SObject Class

#DEPRECATED
# def query_projects():
#     server = server_start()
#     search_type = 'sthpw/project'
#     filters = []
#     projects = server.query(search_type, filters)
#
#     exclude_list = ['sthpw', 'unittest', 'admin']
#
#     projects_by_category = collections.defaultdict(list)
#
#     for project in projects:
#         if project['code'] not in exclude_list:
#             projects_by_category[project['category']].append(project)
#
#     return projects_by_category


def query_all_projects():
    server = server_start()
    search_type = 'sthpw/project'
    filters = []
    projects = server.query(search_type, filters)

    return projects


def get_all_projects():

    projects_list = query_all_projects()

    dct = collections.defaultdict(list)

    exclude_list = ['sthpw', 'unittest', 'admin']
    if len(projects_list) == 2:
        exclude_list = []

    for project in projects_list:
        if project.get('code') not in exclude_list:
            dct[project.get('code')] = Project(project)

    return dct


def get_sobjects(process_list=None, sobjects_list=None, get_snapshots=True, project_code=None):
    """
    Filters snapshot by search codes, and sobjects codes
    :param sobjects_list: full list of stypes
    :param get_snapshots: query for snapshots per sobject or not
    :param project_code: assign project class to particular sObject
    :return: dict of sObjects objects
    """
    sobjects = {}
    if get_snapshots:
        process_codes = list(process_list)
        for builtin in ['icon', 'attachment', 'publish']:
            if builtin not in process_codes:
                process_codes.append(builtin)

        # print sobjects_list
        # search_codes = []
        # for s in sobjects_list:
        #     if s.get('code'):
        #         search_codes.append(s['code'])
        #     elif s.get('id'):
        #         search_codes.append(s['id'])
        #     elif s.get('name'):
        #         search_codes.append(s['name'])

        s_code = [s['code'] for s in sobjects_list]
        # print s_code
        snapshots_list = query_snapshots(process_codes, s_code, project_code)

        snapshots = collections.defaultdict(list)
        # filter snapshots by search_code
        for snapshot in snapshots_list:
            snapshots[snapshot['search_code']].append(snapshot)

        # append sObject info to the end of each search_code filtered list
        for sobject in sobjects_list:
            snapshots[sobject['code']].append(sobject)

        # creating dict or ready SObjects
        for k, v in snapshots.iteritems():
            sobjects[k] = SObject(v[-1], process_codes, env_inst.projects[project_code])
            sobjects[k].init_snapshots(v[:-1])
    else:
        # Create list of Sobjects
        for sobject in sobjects_list:
            sobjects[sobject['code']] = SObject(sobject)

    return sobjects


def query_snapshots(process_list=None, s_code=None, project_code=None):
    """
    Query for snapshots belongs to asset
    :return: list of snapshots
    """

    filters_snapshots = [
        ('process', process_list),
        ('project_code', project_code),
        ('search_code', s_code),
    ]
    return server_start().query_snapshots(filters=filters_snapshots, include_files=True)


def assets_query_new(query, stype, columns=None, project=None, limit=0, offset=0, order_bys='timestamp desc'):
    """
    Query for searching assets
    """
    if not columns:
        columns = []

    server = server_start()
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

    if query[0] == '*':
        filters = []

    built_process = server.build_search_type(stype, project)

    assets_list = server.query(built_process, filters, columns, order_bys, limit=limit, offset=offset)

    # print assets_list
    return assets_list


def get_notes_count(sobject, process, children_stypes):
    kwargs = {
        'process': process,
        'search_key': sobject.info['__search_key__'],
        'stypes_list': children_stypes
    }
    code = tq.prepare_serverside_script(tq.get_notes_and_stypes_counts, kwargs, return_dict=True)
    result = server_start().execute_python_script('', kwargs=code)

    return result['info']['spt_ret_val']


def users_query():
    """
    Query for Users
    :param asset_code: Code of asset related to task
    :param user: Optional users names
    :return:
    """
    server = server_start()
    search_type = 'sthpw/login'
    filters = []
    logins = server.query(search_type, filters)

    result = collections.OrderedDict()
    for login in logins:
        result[login['login']] = login

    return result


def delete_sobject_snapshot(sobject, delete_snapshot=True, search_keys=None, files_paths=None):
    dep_list = {
        'related_types': ['sthpw/file'],
        'files_list': {'search_key': search_keys,
                       'file_path': files_paths,
                       'delete_snapshot': delete_snapshot,
                       },
    }
    try:
        server_start().delete_sobject(sobject, list_dependencies=dep_list), 'delete_sobject_snapshot'
        return True
    except Exception as err:
        print(err, 'delete_sobject_snapshot')
        return False


def delete_sobject_item(skey, delete_files=False):
    server_start().delete_sobject(skey, delete_files)


def snapshot_delete_confirm(snapshot, files):
    ver_rev = gf.get_ver_rev(snapshot['version'], snapshot['revision'])

    msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Confirm deleting',
                            '<p><p>Do you really want to delete snapshot, with context:</p>{0}<p>Version: {1}</p>Also remove selected Files?</p>'.format(
                                snapshot['context'], ver_rev),
                            QtGui.QMessageBox.NoButton, env_inst.ui_main)

    msb.addButton("Delete", QtGui.QMessageBox.YesRole)
    msb.addButton("Cancel", QtGui.QMessageBox.NoRole)

    layout = QtGui.QVBoxLayout()

    wdg = QtGui.QWidget()
    wdg.setLayout(layout)

    msb_layot = msb.layout()
    msb_layot.addWidget(wdg, 1, 1)

    checkboxes = []
    files_list = []
    files_filtered_search_keys = []
    files_filtered_file_paths = []

    delete_snapshot_checkbox = QtGui.QCheckBox('Delete snapshot')
    delete_snapshot_checkbox.setChecked(True)
    layout.addWidget(delete_snapshot_checkbox)

    for i, fl in enumerate(files.itervalues()):
        checkboxes.append(QtGui.QCheckBox(fl[0]['file_name']))
        files_list.append(fl[0])
        checkboxes[i].setChecked(True)
        layout.addWidget(checkboxes[i])

    msb.exec_()
    reply = msb.buttonRole(msb.clickedButton())

    if reply == QtGui.QMessageBox.YesRole:

        if snapshot.get('repo'):
            asset_dir = env_server.rep_dirs[snapshot.get('repo')][0]
        else:
            asset_dir = env_server.rep_dirs['asset_base_dir'][0]

        for i, checkbox in enumerate(checkboxes):
            if checkbox.isChecked():
                files_filtered_search_keys.append(files_list[i]['__search_key__'])
                files_filtered_file_paths.append(
                    gf.form_path(
                        '{0}/{1}/{2}'.format(asset_dir, files_list[i]['relative_dir'], files_list[i]['file_name'])))

        return True, files_filtered_search_keys, files_filtered_file_paths, delete_snapshot_checkbox.isChecked()
    else:
        return False, None


def save_confirm(paths, repo, update_versionless=True):
    if update_versionless:
        update_vs = '<p>Versionless files will be <span style="color:#00aa00;"><b>Updated</b></span></p>'
    else:
        update_vs = '<p>Versionless files will <span style="color:#aa0000;"><b>not be</b></span> Updated</p>'

    message = '<p><p>You are about to save {1} file(s).</p><p>{0}</p><p>Continue?</p>'.format(update_vs, len(paths['versioned']['names']))

    msb = QtGui.QMessageBox(
        QtGui.QMessageBox.Question,
        'Confirm saving',
        message,
        QtGui.QMessageBox.NoButton,
        env_inst.ui_main
        )

    widgets = QtGui.QWidget()
    widgets_layout = QtGui.QGridLayout()
    widgets.setLayout(widgets_layout)

    collapse_wdg_vers = ui_misc_classes.Ui_collapsableWidget()
    layout_vers = QtGui.QVBoxLayout()
    collapse_wdg_vers.setLayout(layout_vers)
    collapse_wdg_vers.setText('Hide Versions Files')
    collapse_wdg_vers.setCollapsedText('Show Versions Files')
    collapse_wdg_vers.setCollapsed(True)

    collapse_wdg_vls = ui_misc_classes.Ui_collapsableWidget()
    layout_vls = QtGui.QVBoxLayout()
    collapse_wdg_vls.setLayout(layout_vls)
    collapse_wdg_vls.setText('Hide Versionless Files')
    collapse_wdg_vls.setCollapsedText('Show Versionless Files')
    collapse_wdg_vls.setCollapsed(True)

    widgets_layout.addWidget(collapse_wdg_vers, 0, 0)
    widgets_layout.addWidget(collapse_wdg_vls, 1, 0)

    msb_layot = msb.layout()
    msb_layot.addWidget(widgets, 1, 1)

    treeWidget_vers = QtGui.QTreeWidget()
    treeWidget_vers.setAlternatingRowColors(True)
    treeWidget_vers.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
    treeWidget_vers.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
    treeWidget_vers.setRootIsDecorated(False)
    treeWidget_vers.headerItem().setText(0, "File")
    treeWidget_vers.headerItem().setText(1, "Path")
    treeWidget_vers.setStyleSheet('QTreeView::item {padding: 2px;}')
    layout_vers.addWidget(treeWidget_vers)
    for i, fl in enumerate(paths['versioned']['names']):
        full_path = gf.form_path(repo['value'][0] + '/' + paths['versioned']['paths'][i])
        item = QtGui.QTreeWidgetItem()
        item.setText(0, fl)
        item.setText(1, full_path)
        treeWidget_vers.addTopLevelItem(item)
    treeWidget_vers.setMinimumWidth(treeWidget_vers.columnWidth(0)+treeWidget_vers.columnWidth(1) + 150)
    treeWidget_vers.setMinimumHeight(250)
    treeWidget_vers.resizeColumnToContents(0)
    treeWidget_vers.resizeColumnToContents(1)

    treeWidget_vls = QtGui.QTreeWidget()
    treeWidget_vls.setAlternatingRowColors(True)
    treeWidget_vls.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
    treeWidget_vls.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
    treeWidget_vls.setRootIsDecorated(False)
    treeWidget_vls.headerItem().setText(0, "File")
    treeWidget_vls.headerItem().setText(1, "Path")
    treeWidget_vls.setStyleSheet('QTreeView::item {padding: 2px;}')
    for i, fl in enumerate(paths['versionless']['names']):
        full_path = gf.form_path(repo['value'][0] + '/' + paths['versionless']['paths'][i])
        item = QtGui.QTreeWidgetItem()
        item.setText(0, fl)
        item.setText(1, full_path)
        treeWidget_vls.addTopLevelItem(item)
    treeWidget_vls.setMinimumWidth(treeWidget_vls.columnWidth(0) + treeWidget_vls.columnWidth(1) + 150)
    treeWidget_vls.setMinimumHeight(250)
    treeWidget_vls.resizeColumnToContents(0)
    treeWidget_vls.resizeColumnToContents(1)

    layout_vls.addWidget(treeWidget_vls)

    msb.addButton("Yes", QtGui.QMessageBox.YesRole)
    msb.addButton("No", QtGui.QMessageBox.NoRole)
    msb.exec_()
    reply = msb.buttonRole(msb.clickedButton())

    if reply == QtGui.QMessageBox.YesRole:
        return True
    else:
        return False


def checkin_virtual_snapshot(search_key, context, snapshot_type='file', ext=None, file_name=None, file_postfix=None, subfolders=None, file_type='main', is_revision=False,
                             repo=None, update_versionless=True, keep_file_name=False, version=None):

    kwargs = {
        'search_key': search_key,
        'context': context,
        'snapshot_type': snapshot_type,
        'is_revision': is_revision,
        'file_type': file_type,
        'file_name': file_name,
        'postfixes': file_postfix,
        'subfolders': subfolders,
        'ext': ext,
        'keep_file_name': keep_file_name,
        'version': version,
    }

    code = tq.prepare_serverside_script(tq.get_virtual_snapshot_extended, kwargs, return_dict=True)
    result = server_start().execute_python_script('', kwargs=code)

    virtual_snapshot = json.loads(result['info']['spt_ret_val'])

    if save_confirm(virtual_snapshot, repo, update_versionless):
        return virtual_snapshot
    else:
        return None


def checkin_snapshot(search_key, context, snapshot_type=None, is_revision=False, description=None,
                     version=None, update_versionless=True, file_types=None, file_names=None,
                     file_paths=None, relative_paths=None, file_sizes=None, exts=None, keep_file_name=False,
                     repo_name=None, virtual_snapshot=None, mode=None, create_icon=False):

    kwargs = {
        'search_key': search_key,
        'context': context,
        'snapshot_type': snapshot_type,
        'is_revision': is_revision,
        'description': description,
        'version': version,
        'update_versionless': update_versionless,
        'file_types': file_types,
        'file_names': file_names,
        'file_paths': file_paths,
        'relative_paths': relative_paths,
        'exts': exts,
        'file_sizes': file_sizes,
        'keep_file_name': keep_file_name,
        'repo_name': repo_name,
        'virtual_snapshot': virtual_snapshot,
        'mode': mode,
        'create_icon': create_icon,
    }

    # print kwargs

    code = tq.prepare_serverside_script(tq.create_snapshot_extended, kwargs, return_dict=True)
    # # print code
    result = server_start().execute_python_script('', kwargs=code)
    # # snapshot = eval(result['info']['spt_ret_val'])

    return result


def add_repo_info(search_key, context, snapshot, repo):
    server = server_start()
    # adding repository info
    splitted_skey = server.split_search_key(search_key)
    filters_snapshots = [
        ('context', context),
        ('search_code', splitted_skey[1]),
        ('search_type', splitted_skey[0]),
        ('version', -1),
    ]
    parent = server.query_snapshots(filters=filters_snapshots, include_files=False)[0]

    data = {
        snapshot.get('__search_key__'): {'repo': repo['name']},
        parent.get('__search_key__'): {'repo': repo['name']},
    }
    server.update_multiple(data, False)


def new_checkin_snapshot(search_key, context, ext='', snapshot_type='file', is_current=True, is_revision=False,
                         description=None, version=None):
    # creating snapshot
    snapshot = server_start().create_snapshot(
        search_key=search_key,
        context=context,
        description=description,
        is_current=is_current,
        is_revision=is_revision,
        snapshot_type=snapshot_type,
        version=version,
    )

    return snapshot


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
        # 'note_html': gf.html_to_hex(note_html),
        'login': login,
    }

    transaction = server_start().insert(search_type, data, parent_key=search_key, triggers=False)

    return transaction


def task_process_query(seach_key):
    # TODO Query task process per process
    # from pprint import pprint
    server = server_start()
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

    message = server.query(search_type, code)

    # from pprint import pprint
    print('from task_process_query!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    # pprint(message)
    # print(message[0])
    # import json
    # data = json.loads(message[0]['message'])
    # pprint(data)
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


def generate_web_and_icon(source_image_path, web_save_path=None, icon_save_path=None):

    image = QtGui.QImage(0, 0, QtGui.QImage.Format_ARGB32)

    image.load(source_image_path)
    if web_save_path:
        web = image.scaledToWidth(640, QtCore.Qt.SmoothTransformation)
        web.save(web_save_path)
    if icon_save_path:
        icon = image.scaledToWidth(120, QtCore.Qt.SmoothTransformation)
        icon.save(icon_save_path)


def inplace_checkin(file_paths, progres_bar, virtual_snapshot, repo_name, update_versionless, check_ok=True):
    def copy_file(dest_path, source_path):
        if dest_path == source_path:
            print('Destination path is equal to source path, skipping...', dest_path)
        else:
            shutil.copyfile(source_path, dest_path)
        if not os.path.exists(dest_path):
            return False
        else:
            return True

    for i, fl in enumerate(file_paths):
        progres_bar.setValue(int(i * 100 / len(file_paths)))
        dest_file_vers = gf.form_path(
            repo_name['value'][0] + '/' +
            virtual_snapshot['versioned']['paths'][i] + '/' +
            virtual_snapshot['versioned']['names'][i]
        )
        dest_path_vers = gf.form_path(
            repo_name['value'][0] + '/' +
            virtual_snapshot['versioned']['paths'][i]
        )

        # create dest dirs
        if not os.path.exists(dest_path_vers):
            os.makedirs(dest_path_vers)

        # copy file to dest dir
        check_ok = copy_file(dest_file_vers, file_paths[i])

        if update_versionless:
            dest_file_vls = gf.form_path(
                repo_name['value'][0] + '/' +
                virtual_snapshot['versionless']['paths'][i] + '/' +
                virtual_snapshot['versionless']['names'][i]
            )
            dest_path_vls = gf.form_path(
                repo_name['value'][0] + '/' +
                virtual_snapshot['versionless']['paths'][i]
            )

            if not os.path.exists(dest_path_vls):
                os.makedirs(dest_path_vls)

            check_ok = copy_file(dest_file_vls, file_paths[i])

    return check_ok


# Checkin functions
def checkin_file(search_key, context, snapshot_type='file', is_revision=False, description=None, version=None,
                 update_versionless=True, file_types='main', file_names=None, file_paths=None, file_sizes=None,
                 exts=None, keep_file_name=False, repo_name=None, mode=None, create_icon=False):

    if create_icon:
        exts.extend(['jpg', 'png'])
        file_types.extend(['web', 'icon'])
        file_names.extend(['', ''])

    virtual_snapshot = checkin_virtual_snapshot(
        search_key,
        context,
        snapshot_type=snapshot_type,
        ext=exts,
        file_type=file_types,
        file_name=file_names,
        is_revision=is_revision,
        repo=repo_name,
        update_versionless=update_versionless,
        keep_file_name=keep_file_name,
        version=version,
    )

    progres_bar = env_inst.ui_check_tree['checkin'][search_key.split('?')[0]].progres_bar
    check_ok = False
    if virtual_snapshot:
        check_ok = True
        progres_bar.setVisible(True)

        # for in-place checkin
        check_ok = inplace_checkin(
            file_paths,
            progres_bar,
            virtual_snapshot,
            repo_name,
            update_versionless,
            check_ok
        )

        if create_icon:
            dest_path = gf.form_path(repo_name['value'][0] + '/' + virtual_snapshot['versioned']['paths'][0])
            dest_playblast_ver = dest_path + '/' + virtual_snapshot['versioned']['names'][0]
            dest_web_ver = dest_path + '/' + virtual_snapshot['versioned']['names'][1]
            dest_icon_ver = dest_path + '/' + virtual_snapshot['versioned']['names'][2]

            file_paths = [dest_playblast_ver, dest_web_ver, dest_icon_ver]
            generate_web_and_icon(dest_playblast_ver, dest_web_ver, dest_icon_ver)

            # copy newly generated icons
            check_ok = inplace_checkin(
                file_paths,
                progres_bar,
                virtual_snapshot,
                repo_name,
                update_versionless,
                check_ok
            )

        if check_ok:
            relative_paths = []
            file_sizes = []
            for fp in file_paths:
                file_sizes.append(gf.get_st_size(fp))

            checkin_snapshot(
                search_key,
                context,
                snapshot_type=snapshot_type,
                is_revision=is_revision,
                description=description,
                version=version,
                update_versionless=update_versionless,
                file_types=file_types,
                file_names=file_names,
                file_paths=file_paths,
                relative_paths=relative_paths,
                file_sizes=file_sizes,
                exts=exts,
                keep_file_name=keep_file_name,
                repo_name=repo_name['value'][3],
                virtual_snapshot=virtual_snapshot,
                mode=mode,
                create_icon=create_icon
            )
            progres_bar.setValue(100)

    progres_bar.setVisible(False)

    return check_ok

    # DEPRECATED
    # dest_file = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['relative_path'] + '/' + virtual_snapshot['file_name'] + '.' + ext)
    # dest_path = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['relative_path'])
    #
    # # create dest dirs
    # if not os.path.exists(dest_path):
    #     os.makedirs(dest_path)
    #
    # # if In-Place checkin copy file to dest dir
    # shutil.copyfile(file_path, dest_file)
    #
    # #create empty snapshot
    # snapshot = new_checkin_snapshot(
    #     search_key,
    #     context,
    #     is_current=is_current,
    #     is_revision=is_revision,
    #     ext='',
    #     description=description,
    #     snapshot_type='file',
    #     version=version,
    # )
    #
    # # checkin saved scene to dest path
    # # ['upload', 'copy', 'move', 'preallocate', 'inplace']
    # server_start().add_file(
    #     snapshot.get('code'),
    #     dest_file,
    #     file_type='main',
    #     create_icon=False,
    #     checkin_type='auto',
    #     mode='preallocate',
    #     custom_repo_path=repo['value'][0],
    #     do_update_versionless=update_versionless,
    # )
    #
    # # adding info about repository to snapshots
    # add_repo_info(search_key, context, snapshot, repo)


def checkin_playblast(snapshot_code, file_name, custom_repo_path):
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

    playblast = server_start().add_file(
        snapshot_code,
        file_name,
        file_type='playblast',
        mode='preallocate',
        create_icon=True,
        # dir_naming='{project.code}/{search_type.table_name}/{sobject.name}/work/{snapshot.process}/versions/asd',
        # file_naming='{sobject.name}_{snapshot.context}_{file.type}_v{version}.{ext}',
        checkin_type='auto',
        custom_repo_path=custom_repo_path,
        do_update_versionless=True,
    )
    return playblast


def checkin_icon(snapshot_code, file_name):
    """
    :return:
    """

    icon = server_start().add_file(snapshot_code, file_name, file_type='main', mode='copy', create_icon=True,
                                   file_naming='{sobject.name}_{file.type}_v{version}.{ext}',
                                   checkin_type='auto')
    return icon


# Skey functions
def parce_skey(skey):
    server = server_start()
    skey_splitted = urlparse.urlparse(skey)
    skey_dict = dict(urlparse.parse_qsl(skey_splitted.query))
    skey_dict['namespace'] = skey_splitted.netloc
    skey_dict['pipeline_code'] = skey_splitted.path[1:]

    if skey_splitted.scheme == 'skey':
        if skey_dict['pipeline_code'] == 'snapshot':
            skey_dict['type'] = 'snapshot'
            snapshot = server.query('sthpw/snapshot', [('code', skey_dict.get('code'))])
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
    skey = 'skey://{0}/{1}?project={2}&code={3}'.format(
        env_server.get_namespace(),
        pipeline_code,
        env_server.get_project(),
        code
    )

    return skey

