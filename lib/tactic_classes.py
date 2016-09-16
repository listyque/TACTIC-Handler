# module Tactic Classes
# file tactic_classes.py
# Global TACTIC Functions Module

import os
import sys
import traceback
import urlparse
import collections
from lib.side.bs4 import BeautifulSoup
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import environment as env
import global_functions as gf
import lib.ui_classes.ui_misc_classes as ui_misc_classes
import side.client.tactic_client_lib as tactic_client_lib


if env.Mode.get == 'maya':
    import maya.cmds as cmds


class ServerThread(QtCore.QThread):
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent=parent)

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


def treat_result(thread):
    if thread.isFailed():
        print 'ERROR TREATING'
        return error_handle(thread)
    else:
        return thread


def server_auth(host, project, login, password, get_ticket=False):
    server = tactic_client_lib.TacticServerStub.get(protocol='xmlrpc', setup=False)
    server.set_server(host)
    server.set_project(project)
    ticket = env.Env.get_ticket()
    if not ticket or get_ticket:
        ticket = server.get_ticket(login, password)
        if type(ticket) == dict:
            if ticket.get('exception'):
                return server
        else:
            env.Env.set_ticket(ticket)

    server.set_ticket(ticket)

    return server


def server_start(get_ticket=False):
    server = server_auth(
        env.Env.get_server(),
        env.Inst.current_project,
        env.Env.get_user(),
        '',
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
    print('Some exception appeared!', str(type(exception)), str(exception))

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


def generate_new_ticket(explicit_username=None):
    login_pass_dlg = QtGui.QMessageBox(
        QtGui.QMessageBox.Question,
        'Updating ticket',
        'Enter Your Login and Password.',
        QtGui.QMessageBox.NoButton,
        None,
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
        login_line_edit.setText(env.Env.get_user())
    pass_line_edit = QtGui.QLineEdit()

    layout.addWidget(login_label, 0, 0)
    layout.addWidget(login_line_edit, 0, 1)
    layout.addWidget(pass_label, 1, 0)
    layout.addWidget(pass_line_edit, 1, 1)

    pass_line_edit.setFocus()

    login_pass_dlg.exec_()

    host = env.Env.get_server()
    #TODO SOMETHING
    project = 'sthpw'
    login = login_line_edit.text()
    password = pass_line_edit.text()

    thread = get_server_thread(dict(), lambda: server_auth(host, project, login, password, get_ticket=True), server_ping)
    thread.start()
    treat_result(thread)
    thread.wait()
    return thread


def run_tactic_team_server():

    path = os.path.normpath(env.Env.get_install_dir() + os.sep + os.pardir)
    print('Starting TACTIC Server... Press Retry after server started!', path)
    os.system(path + '/ServerRun.bat')


def error_handle(thread):
    expected = thread.result['exception']

    error = catch_error_type(expected)

    exception_text = 'Exception type: {0},<p>{1}</p><p><b>Catched Error: {2}</b></p>'.format(str(type(expected)),
                                                                                             str(expected), str(error))
    if (error == 'connection_refused') or (error == 'connection_timeout'):
        title = '{0}, {1}'.format("Cannot connect to TACTIC Server!", error)
        message = '{0}<p>{1}</p>'.format(
            "<p>Looks like TACTIC Server isn't running! May be You need to set up Right Server port and address</p>"
            "<p>Start Server? (Only TACTIC Team)</p>",
            exception_text)
        buttons = [('Yes', QtGui.QMessageBox.YesRole),
                   ('No', QtGui.QMessageBox.NoRole),
                   ('Retry', QtGui.QMessageBox.ApplyRole)]

        if not env.Inst.ui_conf:
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
        message = '{0}<p>{1}</p>'.format(
            "<p>This is no usual type of Exception! See stacktrace for information</p>",
            exception_text)
        buttons = [('Ok', QtGui.QMessageBox.NoRole),
                   ('Retry', QtGui.QMessageBox.ApplyRole)]

        if not env.Inst.ui_conf:
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
        message = '{0}<p>{1}</p>'.format(
            "<p>Wrong ticket, or session may have expired!</p> <p>Generate new ticket?</p>",
            exception_text)
        buttons = [('Yes', QtGui.QMessageBox.YesRole),
                   ('No', QtGui.QMessageBox.NoRole)]

        if not env.Inst.ui_conf:
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
        message = '{0}<p>{1}</p>'.format(
            "<p>You set up wrong Porject Name, or Project not exist!</p> <p>Reset Project to \"sthpw\"?</p>",
            exception_text)
        buttons = [('Yes', QtGui.QMessageBox.YesRole),
                   ('No', QtGui.QMessageBox.NoRole)]

        if not env.Inst.ui_conf:
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
            env.Env.set_project('sthpw')
            env.Inst.ui_main.restart_ui_main()
        if reply == QtGui.QMessageBox.ActionRole:
            thread.result = reply

        return thread

    if error == 'login_pass_error':
        title = '{0}, {1}'.format("Wrong user Login or Password for TACTIC Server!", error)
        message = '{0}<p>{1}</p>'.format(
            "<p>You need to open config, and type correct Login and Password!</p>",
            exception_text)
        buttons = [('Ok', QtGui.QMessageBox.NoRole)]

        if not env.Inst.ui_conf:
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
        message = '{0}<p>{1}</p>'.format(
            "<p>TACTIC Server can't connect to SQL server, may be SQL Server Down! Or wrong server port/ip </p>",
            exception_text)
        buttons = [('Ok', QtGui.QMessageBox.NoRole)]

        if not env.Inst.ui_conf:
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
        message = '{0}<p>{1}</p>'.format("<p>Something wrong!</p>", exception_text)
        buttons = [('Ok', QtGui.QMessageBox.NoRole),
                   ('Retry', QtGui.QMessageBox.ApplyRole)]

        if not env.Inst.ui_conf:
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


# Projects related classes
class Project(object):
    def __init__(self, project):

        self.info = project
        self.stypes = None

    def get_stypes(self):

        self.stypes = self.query_search_types()
        return self.stypes

    def query_search_types(self):
        # getting all stypes

        # import time
        #
        # start = time.time()
        # print("start")
        #
        # for i in range(20):
        #     server_start().query('sthpw/schema', [('code', 'the_pirate')])
        #
        # end = time.time()
        # print(end - start)

        empty_tab = [{'__search_key__': u'sthpw/search_object?code=empty/empty',
                      'class_name': u'pyasm.search.SObject',
                      'code': u'empty/empty',
                      'color': None,
                      'database': u'{project}',
                      'default_layout': u'table',
                      'description': None,
                      'id': 84,
                      'id_column': None,
                      'message_event': None,
                      'metadata_parser': None,
                      'namespace': u'empty',
                      'schema': u'public',
                      'search_type': u'empty/empty',
                      'table_name': u'characters',
                      'title': u'empty',
                      'type': None}, ]

        search_type = 'sthpw/search_object'
        project_code = self.info.get('code')
        namespace = [self.info.get('type'), project_code]

        filters = [('namespace', namespace)]

        # if server:
        all_stypes = server_start().query(search_type, filters)

        if not all_stypes:
            all_stypes = server_start().query(search_type, filters)
            if not all_stypes:
                all_stypes = empty_tab

        # getting pipeline process
        stypes_codes = []
        for stype in all_stypes:
            stypes_codes.append(stype['code'])

        search_type = 'sthpw/pipeline'

        filters = [('search_type', stypes_codes), ('project_code', project_code)]
        stypes_pipelines = server_start().query(search_type, filters)

        # getting project schema
        schema = server_start().query('sthpw/schema', [('code', project_code)])

        if schema:
            prj_schema = schema[0]['schema']
        else:
            prj_schema = None

        if not (stypes_pipelines or schema):
            return None
        else:
            return self.get_all_search_types(all_stypes, stypes_pipelines, prj_schema)

    @staticmethod
    def get_all_search_types(stype_list, process_list, schema):

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

        stypes_objects = collections.OrderedDict()

        for stype in stype_list:
            stype_process = None
            stype_schema = dct.get(stype['code'])

            for process in process_list:
                if dct.get(stype['code']):
                    if process['search_type'] == dct.get(stype['code'])[0]['search_type']['name']:
                        stype_process = process

            stype_obj = SType(stype, stype_schema, stype_process)
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
    def __init__(self, stype, schema=None, process=None):

        self.info = stype

        if process:
            self.pipeline = Pipeline(process)
        else:
            self.pipeline = None

        if schema:
            self.schema = Schema(schema)
        else:
            self.schema = None


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


class Pipeline(object):
    def __init__(self, process):

        self.__process_dict = process

        self.process = collections.defaultdict(list)

        self.get_pipeline()
        self.info = self.get_info()

    def get_info(self):
        info = self.__process_dict
        del info['pipeline']
        return info

    def get_pipeline(self):

        all_connectionslist = []
        pipeline = BeautifulSoup(self.__process_dict['pipeline'], 'html.parser')

        for pipe in pipeline.find_all(name='connect'):
            all_connectionslist.append(pipe.attrs)

        for pipe in pipeline.find_all(name='process'):
            self.process[pipe.attrs.get('name')] = pipe.attrs

            # print pipe

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


def query_projects():
    server = server_start()
    search_type = 'sthpw/project'
    filters = []
    projects = server.query(search_type, filters)

    exclude_list = ['sthpw', 'unittest', 'admin']

    projects_by_category = collections.defaultdict(list)

    for project in projects:
        if project['code'] not in exclude_list:
            projects_by_category[project['category']].append(project)

    return projects_by_category


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
        process_codes.extend(['icon', 'attachment', 'publish'])
        s_code = [s['code'] for s in sobjects_list]
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
            sobjects[k] = SObject(v[-1], process_codes, env.Inst.projects[project_code])
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


# def assets_query(query, process, raw=False, project=None):
#     """
#     Query for searching assets
#     """
#     server = server_start()
#     filters = []
#     expr = ''
#     if query[1] == 0:
#         filters = [('name', 'EQI', query[0])]
#     if query[1] == 1:
#         filters = [('code', query[0])]
#     if query[1] == 2:
#         filters = None
#         parents_codes = ['scenes_code', 'sets_code']
#         for parent in parents_codes:
#             expr += '@SOBJECT(cgshort/shot["{0}", "{1}"]), '.format(parent, query[0])
#     if query[1] == 3:
#         filters = [('description', 'EQI', query[0])]
#     if query[1] == 4:
#         filters = [('keywords', 'EQI', query[0])]
#
#     if query[0] == '*':
#         filters = [[]]
#
#     builded_process = server.build_search_type(process, project)
#
#     if filters:
#         assets = server.query(builded_process, filters)
#     elif expr:
#         assets = server.eval(expr)
#     else:
#         assets = {}
#
#     if raw:
#         return assets
#     out_assets = {
#         'names': [],
#         'codes': [],
#         'description': [],
#         'timestamp': [],
#         'pipeline_code': [],
#     }
#     for asset in assets:
#         # pprint(asset)
#         asset_get = asset.get
#         out_assets['names'].append(asset_get('name'))
#         out_assets['codes'].append(asset_get('code'))
#         out_assets['description'].append(asset_get('description'))
#         out_assets['timestamp'].append(asset_get('timestamp'))
#         out_assets['pipeline_code'].append(asset_get('pipeline_code'))
#
#     return out_assets


def get_notes_count(sobject, process):
    expr = ''

    stub = server_start()
    for proc in process:
        expr += '{' + "@COUNT(sthpw/note['process','{0}'])".format(proc) + '},'

    counts = stub.eval(expr, sobject.info['__search_key__'])

    return counts


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


def create_sobject(name, description, keywords, search_type):
    data = {
        'name': name,
        'description': description,
        'keywords': keywords,
    }
    sobject = server_start().insert(search_type, data)

    return sobject


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


def create_snapshot(search_key, context):
    """
    :return:
    """
    snapshot = server_start().create_snapshot(search_key, context)
    return snapshot


def snapshot_delete_confirm(snapshot, files):
    ver_rev = gf.get_ver_rev(snapshot['version'], snapshot['revision'])

    msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Confirm deleting',
                            '<p><p>Do you really want to delete snapshot, with context:</p>{0}<p>Version: {1}</p>Also remove selected Files?</p>'.format(
                                snapshot['context'], ver_rev),
                            QtGui.QMessageBox.NoButton, env.Inst.ui_main)

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
            asset_dir = env.Env.rep_dirs[snapshot.get('repo')][0]
        else:
            asset_dir = env.Env.rep_dirs['asset_base_dir'][0]

        for i, checkbox in enumerate(checkboxes):
            if checkbox.isChecked():
                files_filtered_search_keys.append(files_list[i]['__search_key__'])
                files_filtered_file_paths.append(
                    gf.form_path(
                        '{0}/{1}/{2}'.format(asset_dir, files_list[i]['relative_dir'], files_list[i]['file_name'])))

        return True, files_filtered_search_keys, files_filtered_file_paths, delete_snapshot_checkbox.isChecked()
    else:
        return False, None


def save_confirm(paths, visible_ext, repo, update_versionless=True):
    if update_versionless:
        update_vs = '<p>Versionless will be <span style="color:#00aa00;"><b>Updated</b></span></p>'
    else:
        update_vs = '<p>Versionless will <span style="color:#aa0000;"><b>not be</b></span> Updated</p>'

    full_path = gf.form_path(env.Env.rep_dirs[repo][0] + '/' + paths['relative_path'])

    msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Confirm saving',
                            '<p><p>Files will be saved to:</p>{0}<p>Filename: {1}</p>{2}Continue?</p>'.format(
                                full_path,
                                paths['file_name'] + '.' + visible_ext,
                                update_vs
                                ),
                            QtGui.QMessageBox.NoButton,
                            env.Inst.ui_main
                            )

    msb.addButton("Yes", QtGui.QMessageBox.YesRole)
    msb.addButton("No", QtGui.QMessageBox.NoRole)
    msb.exec_()
    reply = msb.buttonRole(msb.clickedButton())

    if reply == QtGui.QMessageBox.YesRole:
        return True
    else:
        return False


def checkin_virtual_snapshot(search_key, context, ext='', visible_ext='', file_type='main', is_revision=False,
                             repo=None, update_versionless=True, version=None):

    if repo == 'asset_base_dir' or 'win32_local_repo_dir':
        virtual_snapshot = server_start().get_virtual_snapshot_extended(
            search_key,
            context,
            checkin_type='auto',
            is_revision=is_revision,
            ext=ext,
            file_type=file_type,
            mkdirs=False,
            protocol=None,
            version=version,
        )

        if save_confirm(virtual_snapshot, visible_ext, repo, update_versionless):
            return virtual_snapshot
        else:
            return None


def add_repo_info(search_key, context, snapshot, repo):
    # adding repository info
    splitted_skey = server_start().split_search_key(search_key)
    filters_snapshots = [
        ('context', context),
        ('search_code', splitted_skey[1]),
        ('search_type', splitted_skey[0]),
        ('version', -1),
    ]
    parent = server_start().query_snapshots(filters=filters_snapshots, include_files=False)[0]

    data = {
        snapshot.get('__search_key__'): {'repo': repo['name']},
        parent.get('__search_key__'): {'repo': repo['name']},
    }
    server_start().update_multiple(data, False)


def new_checkin_snapshot(search_key, context, ext='', file_type='main', is_current=True, is_revision=False,
                         description=None, repo=None, version=None):
    if repo['name'] == 'asset_base_dir' or 'win32_local_repo_dir':
        # creating snapshot
        snapshot = server_start().create_snapshot(
            search_key=search_key,
            context=context,
            description=description,
            is_current=is_current,
            is_revision=is_revision,
            snapshot_type='file',
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
        'note_html': gf.html_to_hex(note_html),
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
        env.Env.get_namespace(),
        pipeline_code,
        env.Env.get_project(),
        code
    )

    return skey
