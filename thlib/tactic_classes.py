# module Tactic Classes
# file tactic_classes.py
# Global TACTIC Functions Module

import os
import sys
import io
import glob
import shutil
import urllib
try:
    import urlparse
except:
    from urllib.parse import urlparse
import collections
import json
from pickle import dumps, loads
if sys.version_info[0] > 2:
    from bs4 import BeautifulSoup
else:
    from bs42 import BeautifulSoup
import time
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore
import thlib.proxy as proxy
from thlib.environment import env_mode, env_server, env_inst, env_tactic, env_write_config, env_read_config, env_write_file, dl
import thlib.global_functions as gf
import thlib.tactic_query as tq
from thlib.side.client.tactic_client_lib.tactic_server_stub import TacticServerStub


if env_mode.get_mode() == 'maya':
    import maya_functions as mf
    reload(mf)


def server_auth(host, project=None, login=None, password=None, site=None, get_ticket=False):
    server = TacticServerStub(protocol='xmlrpc', setup=False)
    # server.set_transport(proxy.UrllibTransport())
    # if env_server.get_proxy()['enabled']:
    #     server.transport.enable_proxy()
    # else:
    #     server.transport.disable_proxy()

    server.set_server(host)
    server.set_project(project)
    server.set_site(site)

    ticket = env_server.get_ticket()

    if not ticket or get_ticket:
        ticket = server.get_ticket(login, password, site)
        if isinstance(ticket, dict):
            if ticket.get('exception'):
                return server
        else:
            env_server.set_ticket(ticket)

    server.set_ticket(ticket)

    return server


def server_start(get_ticket=False, project=None):
    if not project:
        project = 'sthpw'
    server = server_auth(
        env_server.get_server(),
        project,
        env_server.get_user(),
        '',
        env_server.get_site()['site_name'],
        get_ticket=get_ticket,
    )
    return server


def generate_new_ticket(explicit_username=None, parent=None):
    login_pass_dlg = QtGui.QMessageBox(
        QtGui.QMessageBox.Question,
        'Updating ticket',
        'Enter Your Login and Password.',
        QtGui.QMessageBox.NoButton,
        parent,
    )

    login_pass_dlg.addButton('Ok', QtGui.QMessageBox.YesRole)
    login_pass_dlg.addButton('Cancel', QtGui.QMessageBox.NoRole)

    layout = QtGui.QGridLayout()

    widget = QtGui.QWidget()
    widget.setLayout(layout)

    msb_layot = login_pass_dlg.layout()

    # workaround for pyside2
    wdg_list = []

    for i in range(msb_layot.count()):
        wdg = msb_layot.itemAt(i).widget()
        if wdg:
            wdg_list.append(wdg)

    msb_layot.addWidget(wdg_list[0], 0, 0)
    msb_layot.addWidget(wdg_list[1], 0, 1)
    msb_layot.addWidget(wdg_list[2], 2, 1)
    msb_layot.addWidget(widget, 1, 1)

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
    project = 'sthpw'
    login = login_line_edit.text()
    password = pass_line_edit.text()
    site = env_server.get_site()['site_name']

    kwargs = dict(
        host=host,
        project=project,
        login=login,
        password=password,
        site=site,
        get_ticket=True
    )

    reply = login_pass_dlg.buttonRole(login_pass_dlg.clickedButton())

    if reply == QtGui.QMessageBox.YesRole:
        return kwargs


def server_ping():
    if server_start():
        if server_start().ping() == 'OK':
            return True
        else:
            return False
    else:
        return False


def server_fast_ping_predefined(server_url, proxy_dict=None):
    server = TacticServerStub.get(protocol='xmlrpc', setup=False)

    transport = proxy.UrllibTransport()
    server.set_transport(transport)

    if proxy_dict.get('enabled'):
        server.transport.update_proxy(proxy_dict)
        server.transport.enable_proxy()
    else:
        server.transport.update_proxy(proxy_dict)
        server.transport.disable_proxy()
        # server.set_transport(None)

    server.set_server(server_url)

    if server.fast_ping() == 'OK':
        del server
        return 'ping_ok'
    else:
        del server
        return 'ping_fail'


def server_fast_ping():
    server = TacticServerStub.get(protocol='xmlrpc', setup=False)
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


def split_search_key(search_key):

    server = server_start()

    if search_key.startswith('sthpw'):
        search_type, asset_code = server.split_search_key(search_key)
        return {
            'search_type': search_type,
            'asset_code': asset_code,
            'pipeline_code': None,
            'project_code': 'sthpw'
        }

    search_type, asset_code = server.split_search_key(search_key)
    if len(search_type.split('?project=')) > 1:
        pipeline_code, project_code = search_type.split('?project=')
    else:
        search_type, project_code = server.split_search_key(search_key)
        asset_code = None
        pipeline_code = None

    return {
        'search_type': search_type,
        'asset_code': asset_code,
        'pipeline_code': pipeline_code,
        'project_code': project_code
    }

# checking for updates on server routine
def get_snapshots_updates_list(search_type_code, project_code):

        search_type_object = env_inst.get_stype_by_code(search_type_code, project_code)

        group_path = u'ui_search/{0}/{1}/{2}/sobjects_conf'.format(
            search_type_object.project.info['type'],
            search_type_object.project.info['code'],
            search_type_object.get_code().split('/')[1]
        )

        abs_path = u'{0}/settings/{1}/{2}/{3}/{4}'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode(),
            group_path)

        json_files = glob.glob1(abs_path, '*.json')

        update_snapshots_timestamp_list = []

        for js in json_files:
            full_path = u'{}/{}'.format(abs_path, js)
            with open(full_path, 'r') as json_file:
                date_time_string = json.load(json_file)

            json_file.close()

            update_snapshots_timestamp_list.append((js.split('.')[0], date_time_string))

        return update_snapshots_timestamp_list


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
        self.all_process = in_process  # TODO Should be deprecated almost not used
        self.project = project

        # OUTPUT VARS
        self.process = {}
        self.tasks = {}
        self.tasks_sobjects = None
        self.notes_sobjects = None
        self.snapshots_sobjects = None
        self.files_sobjects = None
        self.notes = {}
        self.status_log = []

        # INFO VARS
        self.tasks_count = {'__total__': 0}
        self.notes_count = {'publish': 0}

        # INTERNAL VARS
        self.update_dict = {}

    # Snapshots by search code
    def query_snapshots(self, s_code=None, s_id=None, process=None, order_bys=None, filters=None):
        """
        Query for Snapshots
        :param s_code: Code of asset related to snapshot
        :param process: Process code
        :param order_bys: Order By
        :param filters: Optional filters
        :return:
        """

        if process:
            if s_code:
                filters_expr = [('search_code', s_code), ('process', process), ('project_code', self.project.info['code'])]
            elif s_id:
                filters_expr = [('search_id', s_id), ('process', process), ('project_code', self.project.info['code'])]
        else:
            if s_code:
                filters_expr = [('search_code', s_code), ('project_code', self.project.info['code'])]
            elif s_id:
                filters_expr = [('search_id', s_id), ('project_code', self.project.info['code'])]

        if filters:
            filters_expr.extend(filters)

        return server_start(project=self.project.info['code']).query_snapshots(filters=filters_expr, order_bys=order_bys, include_files=True)

    # Tasks by search code
    # DEPRECATED
    def query_tasks(self, s_code, process=None, user=None):
        """
        Query for Task
        :param s_code: Code of asset related to task
        :param process: Process code
        :param user: Optional users names
        :return:
        """
        server = server_start(project=self.project.info['code'])

        search_type = 'sthpw/task'
        if process:
            filters = [('search_code', s_code), ('process', process), ('project_code', self.project.info['code'])]
        else:
            filters = [('search_code', s_code), ('project_code', self.project.info['code'])]

        return server.query(search_type, filters)

    # Notes by search code
    # DEPRECATED
    # def query_notes(self, s_code, process=None):
    #     """
    #     Query for Notes
    #     :param s_code: Code of asset related to note
    #     :param process: Process code
    #     :return:
    #     """
    #     server = server_start(project=self.project.info['code'])
    #
    #     search_type = 'sthpw/note'
    #     if process:
    #         filters = [('search_code', s_code), ('process', process), ('project_code', self.project.info['code'])]
    #     else:
    #         filters = [('search_code', s_code), ('project_code', self.project.info['code'])]
    #
    #     return server.query(search_type, filters)

    # Query snapshots to update current
    def update_snapshots(self, order_bys=None, filters=None):
        if self.info.get('code'):
            snapshot_dict = self.query_snapshots(s_code=self.info['code'], order_bys=order_bys, filters=filters)
        else:
            snapshot_dict = self.query_snapshots(s_id=self.info['id'], order_bys=order_bys, filters=filters)

        self.init_snapshots(snapshot_dict)

    # Initial Snapshots by process without query
    def init_snapshots(self, snapshot_dict):
        process_set = set(snapshot['process'] for snapshot in snapshot_dict)

        for process in process_set:
            self.process[process] = Process(snapshot_dict, process)

    # Snapshots by SObject
    def get_snapshots(self, order_bys=None):

        # Getting all snapshots available for this sobject
        # This will return processes classes dict, which will contain contexts classes
        # Useful for fast query all snapshots with files

        # snapshots = sobject.get_snapshots() :: dict {'publish': Process()}
        # publish_process = snapshots['publish']
        # contexts = publish_process.get_contexts() :: dict {'publish/context': Contexts()}
        # preview = contexts['publish/preview']
        # versionless_snapshots = preview.get_versionless()

        snapshots_list = self.query_snapshots(self.info['code'], order_bys=order_bys)
        process_set = set(snapshot['process'] for snapshot in snapshots_list)

        for process in process_set:
            self.process[process] = Process(snapshots_list, process)

        return self.process

    def get_snapshots_sobjects(self, process=None):
        """
            This is only returning SObjects of snapshots, classes without files, use get_snapshots for files instead
            Use this only if need to delete or edit snapshot info
            Use group_sobject_by() for easier management

            Example:

                snapshots, info = sobject.get_snapshots_sobjects()
                by_context = tc.group_sobject_by(snapshots, 'context')
        """
        search_type = 'sthpw/snapshot'
        if process:
            filters = [('search_code', self.info['code']), ('process', process), ('project_code', self.project.info['code'])]
        else:
            filters = [('search_code', self.info['code']), ('project_code', self.project.info['code'])]

        self.snapshots_sobjects = get_sobjects(search_type, filters, project_code=self.project.info['code'])

        return self.snapshots_sobjects

    def get_files_sobjects(self, type=None):
        # Getting files sobjects for particular Sobject useful if needed to delete or edit

        search_code = self.info.get('search_code')
        if not search_code:
            search_code = self.info.get('code')

        filters = [('search_code', search_code), ('project_code', self.project.info['code'])]

        search_type = 'sthpw/file'
        if type:
            filters.append(('type', type))
        if self.info.get('__search_type__') == 'sthpw/snapshot':
            filters.append(('snapshot_code', self.info['code']))

        self.files_sobjects = get_sobjects(search_type, filters, project_code=self.project.info['code'])

        return self.files_sobjects

    # Tasks by SObject
    # DEPRECATED
    def get_tasks(self):
        tasks_list = self.query_tasks(self.info['code'])
        process_set = set(task['process'] for task in tasks_list)

        for process in process_set:
            self.tasks[process] = Process(tasks_list, process, True)

    def is_snapshots_need_update(self):
        return self.info.get('__have_updates__')

    @staticmethod
    def get_multiple_tasks_sobjects(sobjects_list, process=None):

        sobjects_codes = []
        project_code = sobjects_list[0].project.info['code']
        for sobject in sobjects_list:
            sobjects_codes.append(sobject.info['code'])

        search_type = 'sthpw/task'
        if process:
            filters = [('search_code', 'in', '|'.join(sobjects_codes)), ('process', process), ('project_code', project_code)]
        else:
            filters = [('search_code', 'in', '|'.join(sobjects_codes)), ('project_code', project_code)]

        sobjects, info = get_sobjects(search_type, filters, include_snapshots=False, project_code=project_code)

        if sobjects:
            return group_sobject_by(sobjects, 'search_code')
        else:
            return {}

    def get_tasks_sobjects(self, process=None, include_status_log=False):

        # Use group_sobject_by()
        search_type = 'sthpw/task'
        if process:
            filters = [('search_code', self.info['code']), ('process', process), ('project_code', self.project.info['code'])]
        else:
            filters = [('search_code', self.info['code']), ('project_code', self.project.info['code'])]

        self.tasks_sobjects = get_sobjects(search_type, filters, include_snapshots=False, project_code=self.project.info['code'], include_status_log=include_status_log)

        return self.tasks_sobjects

    def set_tasks_count(self, process, count):
        self.tasks_count[process] = count

    def get_tasks_count(self, process=None):
        if process:
            return self.tasks_count.get(process)
        else:
            return self.tasks_count

    def set_status_log(self, status_log):

        for status in status_log:
            self.status_log.append(SObject(status, project=self.project))

    def get_status_log(self):
        return self.status_log

    def get_stype(self, code=None):
        stypes = self.project.get_stypes()
        if stypes:
            if code:
                return stypes.get(code)
            else:
                return stypes.get(self.info['__search_key__'].split('?')[0])

    def get_plain_search_type(self):
        return self.info['__search_key__'].split('?')[0]

    # Notes by SObject
    #DEPRECATED
    # def get_notes(self):
    #     notes_list = self.query_notes(self.info['code'])
    #     process_set = set(note['process'] for note in notes_list)
    #
    #     for process in process_set:
    #         self.notes[process] = Process(notes_list, process, True)

    def get_notes_sobjects(self, process=None):

        search_type = 'sthpw/note'
        if process:
            filters = [('search_code', self.info['code']), ('process', process), ('project_code', self.project.info['code'])]
        else:
            filters = [('search_code', self.info['code']), ('project_code', self.project.info['code'])]

        self.notes_sobjects = get_sobjects(search_type, filters, include_snapshots=False, project_code=self.project.info['code'])

        return self.notes_sobjects

    def set_notes_count(self, process, count):
        self.notes_count[process] = count

    def get_notes_count(self, process=None):
        if process:
            return self.notes_count.get(process)
        else:
            return self.notes_count

    def get_search_key(self):
        return self.info.get('__search_key__')

    def delete_sobject(self, include_dependencies=False, list_dependencies=None, confirm=True):
        if list_dependencies:
            confirm = False

        if confirm:
            del_confirm = sobject_delete_confirm(self)
        else:
            del_confirm = True

        if del_confirm:
            if isinstance(del_confirm, dict):
                list_dependencies = del_confirm['search_types']

                dependencies_dict = {
                    'related_types': list_dependencies
                }

            kwargs = {
                'search_keys': self.get_search_key(),
                'include_dependencies': include_dependencies,
                'list_dependencies': dependencies_dict,
            }

            return execute_procedure_serverside(tq.delete_sobjects, kwargs)
        else:
            return False

    def get_pipeline_code(self):
        return self.info.get('pipeline_code')

    def get_title(self, pretty=False):
        title = self.info.get('name')
        if not title:
            title = self.info.get('title')
        if not title:
            title = self.info.get('code')
        if pretty:
            return title.replace('_', ' ').capitalize()
        else:
            return title

    def get_code(self):
        return self.info['code']

    def get_info(self):
        return self.info

    def get_value(self, column):
        return self.info.get(column)

    def set_value(self, column, data):
        self.update_dict[column] = data

    def get_timestamp(self, obj=False, pretty=False, simple=False):

        if obj:
            return gf.parce_timestamp(self.info['timestamp'])
        elif pretty:
            dateime = gf.parce_timestamp(self.info['timestamp'])
            return gf.get_pretty_datetime(dateime)
        elif simple:
            dateime = gf.parce_timestamp(self.info['timestamp'])
            return dateime.strftime('%Y %B %d %H:%M:%S')
        else:
            return self.info['timestamp']

    def get_project(self):
        return self.project

    def get_process(self, process):
        return self.process.get(process)

    def get_all_processes(self):
        # returning dict with all processes if it's have snapshots
        return self.process

    def get_schema(self, stype=None):

        return self.get_stype(stype).get_schema()

    def get_related_sobjects_tel_string(self, child_stype=None, parent_stype=None, path='child'):

        """
        Getting related Search Type
        This methrod relies on Schema, and not supposed to be used for built in Search Types

        :param child_stype: Children Search Type
        :param parent_stype: Parent Search Type
        :param path: path for relationship for asset to asset relationship
        :return: TEL string "@SOBJECT()"
        """

        instance_type = None
        related_type = None

        if path == 'parent':
            schema = child_stype.get_schema()
            relations = schema.get_parent(parent_stype.get_code(), child_stype.get_code())

            related_type = parent_stype.get_code()
        else:
            schema = parent_stype.get_schema()
            relations = schema.get_child(child_stype.get_code(), parent_stype.get_code())

            related_type = child_stype.get_code()


        relationship = relations.get('relationship')

        if relationship:

            # if relationship == 'search_type':
            #     child_col = 'search_code'
            # TODO Need special case for search_type relationship
            if relationship in ['code', 'search_type']:
                if relations.get('from_col'):
                    related_from_column = relations.get('from_col')
                else:
                    related_from_column = '{0}_code'.format(relations.get('to').split('/')[-1])

                if relations.get('from_col'):
                    related_to_column = relations.get('to_col')
                else:
                    related_to_column = '{0}_code'.format(relations.get('from').split('/')[-1])

                related_from_code = self.info.get(related_from_column)
                related_to_code = self.info.get(related_to_column)

                # if there is no found code even with explicit columns
                if not related_from_code:
                    related_from_code = self.info.get('code')

                if not related_to_code:
                    related_to_code = self.info.get('code')

            elif relationship == 'instance':

                # Trying to get instance type
                instance_type = relations.get('instance_type')

                instance_schema = self.get_schema(instance_type)

                if path == 'parent':
                    instance_relationship = instance_schema.get_parent_instance(instance_type, related_type)
                else:
                    instance_relationship = instance_schema.get_child_instance(instance_type, related_type)

                if instance_relationship:
                    relations = instance_relationship

                if relations.get('from_col'):
                    related_from_column = relations.get('from_col')
                else:
                    related_from_column = '{0}_code'.format(relations.get('from').split('/')[-1])

                if relations.get('to_col'):
                    related_to_column = relations.get('to_col')
                else:
                    related_to_column = '{0}_code'.format(relations.get('to').split('/')[-1])

                if relations.get('path'):
                    if path == 'parent':
                        instance_type = 'parent:' + instance_type
                        related_type = 'child:' + related_type
                    else:
                        instance_type = 'child:' + instance_type
                        related_type = 'parent:' + related_type

                        # some kind of hack
                        related_to_column = related_from_column

                related_code = self.info.get('code')


        if relationship == 'instance':
            if path == 'parent':
                return u"@SOBJECT({0}['{1}', '{2}'].{3})".format(instance_type, related_from_column, related_code, related_type)
            else:
                return u"@SOBJECT({0}['{1}', '{2}'].{3})".format(instance_type, related_to_column, related_code, related_type)
        else:
            if path == 'parent':
                return u"@SOBJECT({0}['{1}', '{2}'])".format(related_type, related_to_column, related_from_code)
            else:
                return u"@SOBJECT({0}['{1}', '{2}'])".format(related_type, related_from_column, related_to_code)

    def get_related_sobjects(self, child_stype=None, parent_stype=None, get_all_snapshots=False, path='child', filters=None):

        if not child_stype:
            child_stype = self.get_stype()
        elif not parent_stype:
            parent_stype = self.get_stype()

        order_bys = ['name']
        built_process = server_start(
            project=self.project.get_code()).build_search_type(
            child_stype.get_code(),
            self.project.get_code()
        )

        expr_filters = [('_expression', 'in', self.get_related_sobjects_tel_string(child_stype, parent_stype, path=path))]

        if filters:
            expr_filters.extend(filters)

        return get_sobjects(
            search_type=built_process,
            filters=expr_filters,
            order_bys=order_bys,
            get_all_snapshots=get_all_snapshots,
        )

    def commit(self, triggers=True):

        # filling actual info to sobject
        for column, value in self.update_dict.items():
            self.info[column] = value

        return server_start(project=self.project.get_code()).update(
            self.get_search_key(),
            data=self.update_dict,
            triggers=triggers
        )


# Projects related classes
class Project(SObject):
    def __init__(self, project):

        self.info = project
        self.stypes = None
        self.workflow = None
        self.sidebar = None

        self.process = {}

    def get_title(self, pretty=False):
        title = self.info.get('name')
        if not title:
            title = self.info.get('title')
        if not title:
            title = self.info.get('code')
        if pretty:
            return title.replace('_', ' ').capitalize()
        else:
            return title

    def get_workflow(self):
        return self.workflow

    def get_sidebar(self):
        return self.sidebar

    def get_type(self):
        return self.info.get('type')

    def is_template(self):
        return self.info.get('is_template')

    def get_stypes(self):
        if not self.stypes:
            return self.query_search_types()
        else:
            return self.stypes

    def query_search_types(self, force=False):

        use_cache = True
        stypes_result = None

        if use_cache and not force:
            # reading cache from file
            stypes_cache = env_read_config(
                filename='stypes_cache',
                unique_id='cache/{0}'.format(self.get_code()),
                long_abs_path=True
            )
            if stypes_cache:
                stypes_result = gf.hex_to_html(stypes_cache)
            else:
                return self.query_search_types(True)
        else:
            kwargs = {
                'project_code': self.get_code(),
            }

            stypes_result = execute_procedure_serverside(tq.query_search_types_extended, kwargs, project=self.get_code(), return_dict=False)

            if stypes_result:
                pass
                print('SKIP WRITING')
                # writing result to cache
                # env_write_config(
                #     gf.html_to_hex(stypes_result),
                #     filename='stypes_cache',
                #     unique_id='cache/{0}'.format(self.get_code()),
                #     long_abs_path=True
                # )

        stypes = json.loads(stypes_result)

        sidebar = stypes.get('sidebar')
        schema = stypes.get('schema')
        pipelines = stypes.get('pipelines')
        stypes = stypes.get('stypes')


        if schema:
            prj_schema = schema[0]['schema']
        else:
            prj_schema = None

        # Empty until it needed
        if self.get_code() == 'sthpw':
            prj_schema = 'dummy'
            pipelines = [{None: None}]

        if not pipelines or not prj_schema:
            return []
        else:
            return self.get_all_search_types(stypes, pipelines, prj_schema, sidebar)

    def get_all_search_types(self, stype_list, process_list, schema, sidebar):
        pipeline = BeautifulSoup(schema, 'html.parser')
        all_connections_list = []

        dct = collections.OrderedDict()

        for pipe in pipeline.find_all(name='connect'):
            all_connections_list.append(pipe.attrs)

        for pipe in pipeline.find_all(name='search_type'):
            dct.setdefault(pipe.attrs['name'], []).append({'search_type': pipe.attrs})

            conn = {
                'children': [],
                'parents': [],
            }
            for connect in all_connections_list:

                if pipe.attrs['name'] == connect['from']:

                    # special case for "path"
                    if connect.get('path'):
                        if connect['path'] == 'parent':
                            conn['parents'].append(connect)
                        if connect['path'] == 'child':
                            conn['children'].append(connect)
                    else:
                        conn['parents'].append(connect)

                if pipe.attrs['name'] == connect['to']:
                    if connect.get('path'):
                        if connect['path'] == 'parent':
                            conn['parents'].append(connect)
                        if connect['path'] == 'child':
                            conn['children'].append(connect)
                    else:
                        conn['children'].append(connect)

            # dct[pipe.attrs['name']].append(conn)
            dct.setdefault(pipe.attrs['name'], []).append(conn)

        # getting workflow here
        self.workflow = Workflow(process_list)

        # getting stypes processes here
        stypes_objects = collections.OrderedDict()
        for stype in stype_list:
            stype_process = collections.OrderedDict()
            stype_schema = dct.get(stype['code'])

            for process in process_list:
                if dct.get(stype['code']):
                    if process['search_type'] == dct.get(stype['code'])[0]['search_type']['name']:
                        stype_process[process['code']] = process

            stype_obj = SType(stype, stype_schema, stype_process, project=self)
            stypes_objects[stype['code']] = stype_obj

        self.stypes = stypes_objects

        # getting definition for sidebar
        self.sidebar = Sidebar(sidebar)

        return self.stypes


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
        self.schema = schema
        self.pipeline = self.__init_pipelines(pipelines)

        if self.schema:
            self.schema = Schema(schema)

    @staticmethod
    def __init_pipelines(pipelines):

        ready_pipeline = collections.OrderedDict()
        if pipelines:
            for key, pipeline in pipelines.items():
                ready_pipeline[key] = Pipeline(pipeline)

        if ready_pipeline:
            return ready_pipeline

    def get_pretty_name(self):
        title = self.info.get('title')
        if title:
            return title.title()
        else:
            title = self.info.get('code').split('/')[-1]
            if title:
                return title.replace('_', ' ').title()
            else:
                return self.info['table_name'].title()

    def get_stype_color(self, fmt='rgb', alpha=None, tuple=False):
        color = self.info['color']
        if color:
            if fmt == 'rgb':
                return gf.hex_to_rgb(color, alpha=alpha, tuple=tuple)
            else:
                return color

    def get_code(self):
        return self.info['code']

    def get_project(self):
        return self.project

    def get_info(self):
        return self.info

    def get_schema(self):
        return self.schema

    def get_pipeline(self):
        return self.pipeline

    def get_workflow(self):
        return self.project.get_workflow()

    def get_column_info(self, column):
        column_info = self.info.get('column_info')
        if column_info:
            return column_info.get(column)

    def get_columns_info(self):
        return self.info.get('column_info')

    def get_column_data_type(self, column):
        if column == '_expression':
            return '_expression'
        if self.get_columns_info():
            if self.info['column_info'].get(column):
                return self.info['column_info'][column]['data_type']

    def get_definition(self, definition='table', processed=True, bs=False):

        if bs:
            return BeautifulSoup(self.info['definition'].get(definition), 'html.parser')

        if processed:

            definition_bs = BeautifulSoup(self.info['definition'].get(definition), 'html.parser')

            all_elements = []
            for element in definition_bs.find_all(name='element'):
                all_elements.append(element.attrs)

            return all_elements

        else:
            return self.info['definition'].get(definition)

    def get_children_stypes(self):
        children_list = []

        if self.schema.children:
            for child in self.schema.children:
                children_list.append(self.project.stypes.get(child.get('from')))

        return children_list

    def get_parent_stypes(self):
        parents_list = []

        if self.schema.parents:
            for parent in self.schema.parents:
                parents_list.append(self.project.stypes.get(parent.get('to')))

        return parents_list


class Sidebar():
    def __init__(self, config_dict):

        self.config_dict = config_dict

    def has_definition(self):

        if self.config_dict:
            return True
        else:
            return False

    def get_definition(self, definition='definition', login='', processed=True, bs=False):

        definition_xml = ''

        for config in self.config_dict:
            if login:
                if config['login'] == login:
                    if config['view'] == definition:
                        definition_xml = config['config']
            elif config['login'] is None:
                if config['view'] == definition:
                    definition_xml = config['config']

        if bs:
            definition_bs = BeautifulSoup(definition_xml, 'html.parser')

            all_elements = []
            for element in definition_bs.find_all(name='element'):
                all_elements.append(element)

            return all_elements

        if processed:

            definition_bs = BeautifulSoup(definition_xml, 'html.parser')

            all_elements = []
            for element in definition_bs.find_all(name='element'):
                all_elements.append(element.attrs)

            return all_elements

        else:
            return definition_xml


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

    def get_child(self, child_stype, parent_stype):
        for child in self.children:
            if child['from'] == child_stype and child['to'] == parent_stype:
                return child

    def get_parent(self, parent_stype, child_stype):

        for parent in self.parents:
            if parent['to'] == parent_stype and parent['from'] == child_stype:
                return parent

    def get_child_instance(self, instance_type, related_type):
        for child in self.children:
            if child['from'] == instance_type and child['to'] == related_type:
                return child

    def get_parent_instance(self, instance_type, related_type):
        for parent in self.parents:
            if parent['from'] == instance_type and parent['to'] == related_type:
                return parent

class Workflow(object):
    def __init__(self, pipeline):

        self.__pipeline_list = pipeline
        self.__pipeline_by_codes = {}

        self.sort_by_search_types()

    def __get_by_stype(self, search_type_code):
        tasks_pipeliens = {}
        for pipe in self.__pipeline_list:
            if pipe['search_type'] == search_type_code:
                tasks_pipeliens[pipe['code']] = Pipeline(pipe)

        return tasks_pipeliens

    def sort_by_search_types(self):
        for pipe in self.__pipeline_list:
            search_type_code = pipe.get('search_type')
            if search_type_code:
                self.__pipeline_by_codes[search_type_code] = self.__get_by_stype(search_type_code)

    def get_all_pipelines(self):
        return self.__pipeline_by_codes

    def get_by_stype_code(self, code):
        return self.__pipeline_by_codes.get(code)

    def get_by_pipeline_code(self, stype_code, pipeline_code):
        return self.get_by_stype_code(stype_code).get(pipeline_code)

    def get_by_process_node_type(self, stype_code, node_type):
        if node_type in [None, 'manual']:
            node_type = 'task'

        return self.get_by_stype_code(stype_code).get(node_type)

    def get_child_pipeline_by_process_code(self, parent_pipeline, process):
        parent_process = None
        if parent_pipeline.get_all_pipeline_process():
            for proc in parent_pipeline.get_all_pipeline_process():
                if proc['process'] == process:
                    parent_process = proc
        if parent_process:
            # TODO SOMETHING WRONG WITH THIS, may be it query too much pipelines
            return self.get_pipeline_by_parent(parent_process)

    def get_pipeline_by_parent(self, parent_process):
        for pipe in self.__pipeline_list:
            if pipe.get('parent_process'):
                if pipe['parent_process'] == parent_process['code']:
                    return Pipeline(pipe)


class Pipeline(object):

    def __init__(self, process):

        self.info = process

        self.pipeline = collections.OrderedDict()

        if self.info.get('pipeline'):
            self.init_pipeline()

    def get_all_pipeline_process(self):
        return self.info['stypes_processes']

    def get_info(self):
        return self.info

    def get_pipeline_process(self, process_code):
        # what if we have duplicated processes?
        for process in self.info['stypes_processes']:
            if process['process'] == process_code:
                return process

    def get_all_pipeline_names(self):
        process_names_list = []

        for process in self.pipeline:
            process_names_list.append(process)

        return process_names_list

    def get_all_tasks_pipelines_names(self):
        tasks_pipelines_names_list = set()

        for process in self.pipeline.values():
            task_pipeline = process.get('task_pipeline')
            if task_pipeline:
                tasks_pipelines_names_list.add(task_pipeline)

        return list(tasks_pipelines_names_list)

    def init_pipeline(self):

        all_connectionslist = []

        pipeline = BeautifulSoup(self.info['pipeline'], 'html.parser')

        for pipe in pipeline.find_all(name='connect'):
            all_connectionslist.append(pipe.attrs)

        for pipe in pipeline.find_all(name='process'):
            self.pipeline[pipe.attrs.get('name')] = pipe.attrs

            for connect in all_connectionslist:
                if pipe.attrs['name'] == connect['from']:
                    self.pipeline[pipe.attrs.get('name')]['parents'] = connect
                if pipe.attrs['name'] == connect['to']:
                    self.pipeline[pipe.attrs.get('name')]['children'] = connect

    def get_process_info(self, process):
        return self.pipeline.get(process)

    def get_process_label(self, process):
        process_info = self.get_process_info(process)
        if process_info:
            process_label = process_info.get('label')
            if process_label:
                return process_label
            else:
                return process.capitalize()
        else:
            return process.capitalize()


# Login related classes
class Login(SObject):
    object_type = 'login'

    def __init__(self, login, login_groups=None, login_in_groups=None):

        self.info = login
        self.login_groups = login_groups
        self.login_in_groups = login_in_groups
        self.all_subscriptions = None
        self.all_messages = None

        self.__init_login_groups()

    def get_object_type(self):
        return self.object_type

    def get_login_groups(self):
        return self.login_groups

    def get_login_group(self, login_group_code):
        login_groups = self.login_groups
        for login_group in login_groups:
            if login_group_code == login_group.get_code():
                return login_group

    def get_display_name(self):
        return self.info['display_name']

    def get_login(self):
        return self.info['login']

    def get_code(self):
        return self.info['code']

    def get_project_code(self):
        return self.info['project_code']

    def get_info(self):
        return self.info

    def __init_login_groups(self):

        for login_group in self.login_groups:
            for login_in_group in self.login_in_groups:
                if self.info['login'] == login_in_group['login']:
                    if login_group.get_login_group() == login_in_group['login_group']:
                        login_group.add_login_to_group(self)

    # Query Methods
    def query_subscriptions_and_messages(self):
        subscriptions_and_messages = get_subscriptions_and_messages(
                current_login=self.info['code'],
                update_logins=False
            )

        subscriptions_list = []

        for subscription in subscriptions_and_messages['subscriptions']:
            exist_subs = self.check_subscription_exists(subscription)
            if not exist_subs:
                subscriptions_list.append(Subscription(subscription=subscription))
            else:
                subscriptions_list.append(exist_subs)

        messages_list = []

        for message in subscriptions_and_messages['messages']:
            exist_mess = self.check_message_exists(message)
            if not exist_mess:
                messages_list.append(Message(message=message))
            else:
                messages_list.append(exist_mess)

        return subscriptions_list, messages_list

    def check_subscription_exists(self, subs):
        if self.all_subscriptions:
            for subscription in self.all_subscriptions:
                if subscription.get_info() == subs:
                    return subscription

    def check_message_exists(self, mess):
        if self.all_messages:
            for message in self.all_messages:
                if message.get_info() == mess:
                    return message

    def get_subscriptions_and_messages(self, force_update=False):
        if not self.all_subscriptions or not self.all_messages:
            self.all_subscriptions, self.all_messages = self.query_subscriptions_and_messages()
            return self.all_subscriptions, self.all_messages
        if force_update:
            self.all_subscriptions, self.all_messages = self.query_subscriptions_and_messages()

        return self.all_subscriptions, self.all_messages

    def get_subscriptions_by_category(self, category=None):
        self.get_subscriptions_and_messages()

        subscriptions = []
        for subscription in self.all_subscriptions:
            if subscription.get_category() == category:
                subscriptions.append(subscription)

        return subscriptions


class LoginGroup(SObject):
    object_type = 'login_group'

    def __init__(self, login_group):

        self.info = login_group
        self.group_logins = []

    def get_object_type(self):
        return self.object_type

    def get_pretty_name(self):
        title = self.info.get('name')
        if title:
            return title.title()
        else:
            title = self.get_login_group()
            if title:
                return title.replace('_', ' ').title()
            else:
                return self.get_code().replace('_', ' ').title()

    def get_description(self):
        return self.info.get('description')

    def get_login_group(self):
        return self.info['login_group']

    def get_code(self):
        return self.info['code']

    def get_project_code(self):
        return self.info['project_code']

    def get_info(self):
        return self.info

    def get_logins(self):
        return self.group_logins

    def add_login_to_group(self, login_obj):
        self.group_logins.append(login_obj)


class Subscription(SObject):
    object_type = 'subscription'

    def __init__(self, subscription):

        self.info = subscription
        self.messages = None

    def get_message_code(self):
        return self.info['message_code']

    def get_code(self):
        return self.info['code']

    def get_project_code(self):
        return self.info['project_code']

    def get_info(self):
        return self.info

    def get_category(self):
        return self.info['category']

    def get_last_cleared(self):
        return self.info['last_cleared']

    def get_login(self):
        return self.info['login']

    # Query Methods
    def query_messages(self):

        search_type = 'sthpw/message'
        filters = [('category', self.get_category()), ('code', self.get_message_code())]

        messages = server_start().query(search_type, filters)

        messages_list = []

        for message in messages:
            messages_list.append(Message(message=message))

        return messages_list

    def get_messages(self):
        if not self.messages:
            self.messages = self.query_messages()

        return self.messages


class Message(SObject):
    object_type = 'message'

    def __init__(self, message):

        self.info = message
        self.message_log = None

    def get_message(self):
        return self.info['message']

    def get_login(self):
        return self.info['login']

    def get_code(self):
        return self.info['code']

    def get_project_code(self):
        return self.info['project_code']

    def get_category(self):
        return self.info['category']

    def get_status(self):
        return self.info['status']

    def get_info(self):
        return self.info

    # Query Methods
    def query_message_log(self):

        search_type = 'sthpw/message_log'
        filters = [('message_code', self.get_code())]

        message_logs = server_start().query(search_type, filters)

        message_logs_list = []

        for message_log in message_logs:
            message_logs_list.append(MessageLog(message_log=message_log))

        return message_logs_list

    def get_message_log(self, force=False):
        if not self.message_log:
            self.message_log = self.query_message_log()
        elif force:
            self.message_log = self.query_message_log()

        return self.message_log


class MessageLog(Message):
    object_type = 'message_log'

    def __init__(self, message_log):

        self.info = message_log


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

    def get_contexts(self):
        return self.contexts


class Contexts(object):
    def __init__(self, versionless=None, versions=None, single=None):

        self.versions = None
        self.versionless = None

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

    def get_versions(self):
        return self.versions

    def get_versionless(self):
        return self.versionless


class Snapshot(SObject, object):
    def __init__(self, snapshot):
        super(self.__class__, self).__init__(snapshot)

        self.__files = snapshot['__files__']
        self.files = collections.OrderedDict()

        self.files_objects = []
        self.goupped_by_files_objects = {}
        self.preview_files_objects = None

        for fl in self.__files:
            self.files.setdefault(fl['type'], []).append(fl)

        self.snapshot = snapshot
        # delete unused big entries
        del self.snapshot['__files__'], self.snapshot['snapshot']

    def get_files(self):
        return self.files

    def get_code(self):
        return self.snapshot.get('code')

    def get_search_key(self):
        return self.snapshot['__search_key__']

    def get_files_objects(self, group_by=None):

        if not self.files_objects:
            for fl in self.__files:
                self.files_objects.append(File(fl, self))

        if group_by:
            if group_by not in self.goupped_by_files_objects.keys():
                files_objects = collections.OrderedDict()
                for fl in self.__files:
                    files_objects.setdefault(fl[group_by], []).append(File(fl, self))

                self.goupped_by_files_objects[group_by] = files_objects

            return self.goupped_by_files_objects[group_by]
        else:
            return self.files_objects

    def get_previewable_files_objects(self):
        if self.preview_files_objects:
            return self.preview_files_objects

        files_objects = self.get_files_objects()
        preview_objects = []
        for fo in files_objects:
            if fo.get_type() not in ['web', 'icon']:
                if fo.is_previewable():
                    preview_objects.append(fo)

        self.preview_files_objects = preview_objects

        return preview_objects

    def get_snapshot(self):
        return self.snapshot

    def get_version(self):
        return self.snapshot.get('version')

    def is_latest(self):
        return self.snapshot.get('is_latest')

    def is_versionless(self):
        if self.get_version() == -1:
            return True
        else:
            return False


class File(SObject, object):
    def __init__(self, file_dict, snapshot=None):

        self.downloaded = False

        self.info = file_dict
        self.__snapshot = snapshot
        self.previewable = False
        self.meta_file_object = False
        self.get_meta_file_object()

    def get_dict(self):
        return self.info

    def get_unique_id(self):
        return id(self)

    def get_file_size(self, check_real_size=False):
        if check_real_size:
            return gf.get_st_size(self.get_full_abs_path())
        else:
            return self.info['st_size']

    def get_snapshot(self):
        return self.__snapshot

    def get_metadata(self):
        metadata = self.info.get('metadata')
        # Simple check if this is json dumpable
        print('HERE IS UNICODE CHECK PY2')
        if isinstance(metadata, str):
            if metadata.startswith(('{', '"')):
                metadata = json.loads(metadata)

        return metadata

    def get_meta_file_object(self):
        file_object = None
        metadata = self.get_metadata()
        if metadata:
            if metadata.get('template'):
                match_template = gf.MatchTemplate()
                file_object = match_template.init_from_tactic_file_object(self)

        if file_object:
            self.meta_file_object = True
            return list(file_object.values())[0][0]

    def is_meta_file_obj(self):
        return self.meta_file_object

    def get_type(self):
        return self.info['type']

    def get_base_type(self):
        return self.info['base_type']

    def get_ext(self):
        ext = gf.extract_extension(self.info['file_name'])
        return ext[0]

    def get_filename_with_ext(self):
        return self.info['file_name']

    def get_filename(self):
        filename = self.info['file_name']
        ext = gf.extract_extension(filename)
        if ext:
            return filename.replace('.' + ext[0], '')
        else:
            return filename

    def get_filename_no_type_prefix(self):
        # guess right only if type at the end
        filename = self.get_filename()
        prefix = self.info['type']
        if prefix:
            if filename.endswith(prefix):
                no_prefix_name = filename.split('_')
                return '_'.join(no_prefix_name[:-1])
            else:
                return filename
        else:
            return filename

    def get_repo_path(self):
        snapshot = self.__snapshot.get_snapshot()
        repo_name = snapshot.get('repo')

        # if repo not explicitly written in snapshot or disabled in config we choose base repo
        if not repo_name or not env_tactic.get_base_dir(repo_name)['value'][4]:
            repo_name = 'base'

        asset_dir = env_tactic.get_base_dir(repo_name)['value'][0]

        return gf.form_path(asset_dir)

    def get_abs_path(self):
        snapshot = self.__snapshot.get_snapshot()
        repo_name = snapshot.get('repo')

        # if repo not explicitly written in snapshot or disabled in config we choose base repo
        if not repo_name or not env_tactic.get_base_dir(repo_name)['value'][4]:
            repo_name = 'base'

        asset_dir = env_tactic.get_base_dir(repo_name)['value'][0]

        abs_path = gf.form_path(
            '{0}/{1}'.format(asset_dir, self.info['relative_dir']))

        return abs_path

    def get_full_abs_path(self):
        return gf.form_path('{0}/{1}'.format(self.get_abs_path(), self.info['file_name']))

    def get_web_path(self):
        server_address = env_server.get_server()
        if not server_address.startswith('http://'):
            server_address = u'http://{}'.format(server_address)
        asset_path = u'{0}/{1}'.format(server_address, env_tactic.get_base_dir('web')['value'][0])

        abs_path = gf.form_path(u'{0}/{1}'.format(asset_path, self.info['relative_dir']), tp='web')
        return abs_path

    def get_full_web_path(self):
        return '{0}/{1}'.format(self.get_web_path(), self.info['file_name'])

    def is_exists(self):
        return os.path.isfile(self.get_full_abs_path())

    def is_previewable(self):
        if self.previewable:
            return True

        previewable = False
        ext = gf.extract_extension(self.info['file_name'])
        if self.info['type'] in ['icon', 'web', 'image', 'playblast']:
            return True
        elif ext[3] == 'preview':
            previewable = True

        self.previewable = previewable

        return previewable

    def get_web_preview(self):
        # return web file object related to this file
        if self.info['type'] != 'web':
            files = self.__snapshot.get_files_objects()
            # filename = self.get_filename_no_type_prefix()
            for fl in files:
                if fl.get_type() == 'web':
                    # if filename in fl.get_filename():
                    return fl
        else:
            return self

    def get_icon_preview(self):
        # return icon file object related to this file
        if self.info['type'] != 'icon':
            files = self.__snapshot.get_files_objects()
            # filename = self.get_filename_no_type_prefix()
            for fl in files:
                if fl.get_type() == 'icon':
                    # if filename in fl.get_filename():
                    return fl
        else:
            return self

    def download_file(self, dest_path=None):

        full_abs_path = self.prepare_repo(dest_path)

        with urllib.urlopen(self.get_full_web_path()) as download:
            with open(full_abs_path, "wb") as downloaded_file:
                downloaded_file.write(download.read())

            downloaded_file.close()

        download.close()

        return full_abs_path

    def prepare_repo(self, dest_path=None):
        if not dest_path:
            dest_path = self.get_abs_path()

        full_abs_path = self.get_full_abs_path()

        if not os.path.isdir(dest_path):
            os.makedirs(dest_path)

        return full_abs_path

    def open_file(self):
        gf.open_file_associated(self.get_full_abs_path())

    def open_folder(self):
        gf.open_folder(gf.form_path(self.get_full_abs_path()), highlight=True)

    def is_downloaded(self):
        return self.downloaded

    def set_downloaded(self):
        self.downloaded = True

# End of SObject Class


def execute_procedure_serverside(func, kwargs, project=None, return_dict=True, server=None):
    # This is for TACTIC 4.7 compatibility
    if kwargs.get('code'):
        code = kwargs
    else:
        code = tq.prepare_serverside_script(func, kwargs, shrink=False, catch_traceback=False)
    if not server:
        server = server_start(project=project)
    code['_debug_args'] = False
    result = server.execute_python_script('', kwargs=code)

    if isinstance(result['info'], dict):
        if result['info'].get('spt_ret_val'):
            ret_val = result['info']['spt_ret_val']
        else:
            ret_val = result['info']
    else:
        ret_val = result['info']

    if return_dict:
        print('PY2 UNICODE CHECK')
        if isinstance(ret_val, str):
            if ret_val.startswith('Traceback'):
                # TODO need to decide how we handle tracebacks
                dl.exception(ret_val, group_id='{0}/{1}'.format('exceptions', func.func_name))
                final_result = ret_val
            else:
                # Simple check if this is json dumpable
                if ret_val.startswith(('{', '"', '[')):
                    final_result = json.loads(ret_val, strict=False)
                else:
                    final_result = ret_val

                print('PY2 CHECK UNICODE')
                if isinstance(final_result, str) and return_dict:
                    # Decompress long query
                    js = gf.hex_to_html(final_result)
                    if js:
                        print(js)
                        print(type(js))
                        if js.startswith((b'{', b'"', b'[')):
                            final_result = json.loads(js, strict=False)
        else:
            final_result = ret_val
    else:
        final_result = ret_val

    return final_result


def get_all_projects_and_logins(force=False):

    use_cache = True

    if use_cache and not force:
        # reading cache from file
        projects_cache = env_read_config(
            filename='projects_cache',
            unique_id='cache',
            long_abs_path=True
        )
        logins_cache = env_read_config(
            filename='logins_cache',
            unique_id='cache',
            long_abs_path=True
        )
        projects_cache = None
        logins_cache = None

        if projects_cache and logins_cache:
            projects_dict = loads(gf.hex_to_html(bytearray(projects_cache, 'utf-8')))
            logins_dict = loads(gf.hex_to_html(bytearray(logins_cache, 'utf-8')))

            env_inst.projects = projects_dict
            env_inst.logins = logins_dict

            return projects_dict
        else:
            return get_all_projects_and_logins(True)
    else:
        kwargs = {
            'current_login': env_inst.get_current_login()
        }
        projects_and_users = execute_procedure_serverside(tq.get_projects_and_logins, kwargs)

        projects = projects_and_users.get('projects')
        logins = projects_and_users.get('logins')
        login_groups = projects_and_users.get('login_groups')
        login_in_groups = projects_and_users.get('login_in_groups')
        # subscriptions = projects_and_users.get('subscriptions')

        # Making Projects objects
        projects_dict = collections.OrderedDict()
        exclude_list = ['unittest', 'admin']
        if len(projects) == 2:
            exclude_list = []

        for project in projects:
            if project.get('code') not in exclude_list:
                project_sobject = Project(project)
                project_sobject.init_snapshots(project['__snapshots__'])
                projects_dict[project.get('code')] = project_sobject

        env_inst.projects = projects_dict

        logins_dict = collections.OrderedDict()
        login_groups_list = []
        login_in_groups_list = []

        for login_group in login_groups:
            login_groups_list.append(LoginGroup(login_group))

        for login_in_group in login_in_groups:
            login_in_groups_list.append(login_in_group)

        for login in logins:
            login_object = Login(login, login_groups_list, login_in_groups_list)
            # if login_object.get_login() == env_inst.get_current_login():
            #     login_object.all_subscriptions = subscriptions
            logins_dict[login.get('code')] = login_object

        env_inst.logins = logins_dict

        # writing result to cache
        env_write_config(
            gf.html_to_hex(dumps(projects_dict)),
            filename='projects_cache',
            unique_id='cache',
            long_abs_path=True
        )
        env_write_config(
            gf.html_to_hex(dumps(logins_dict)),
            filename='logins_cache',
            unique_id='cache',
            long_abs_path=True
        )

        return projects_dict


def get_subscriptions_and_messages(current_login='admin', update_logins=False):

    kwargs = {
        'current_login': current_login,
        'update_logins': update_logins,
    }

    return execute_procedure_serverside(tq.get_subscriptions_and_messages, kwargs)


def delete_sobjects(search_keys, list_dependencies):
    """
    Deletes bunch of sobjects
    !!! SEARCH KEYS MUST ME SAME TYPE !!!
    :param search_keys: ['sthpw/snapshot?code=SNAPSHOT000000']
    :param list_dependencies: {'search_types': [u'sthpw/snapshot', 'sthpw/notes', 'sthps/file']}
    :return: deleted sobjects dict
    """

    kwargs = {
        'search_keys': search_keys,
        'include_dependencies': False,
        'list_dependencies': list_dependencies,
    }

    return execute_procedure_serverside(tq.delete_sobjects, kwargs)


def get_sobjects(search_type, filters=[], order_bys=[], project_code=None, limit=None, offset=None, process_list=[], get_all_snapshots=False, check_snapshots_updates=False, include_info=True, include_snapshots=True, compressed_return=True, include_status_log=False):
    """
    Filters snapshot by search codes, and sobjects codes
    :param search_type: search_type or search_key (if using search_type project_code should to be provided)
    :param project_code: assign project class to particular sObject
    :return: tuple : (dict, dict) of sObjects objects
    """

    kwargs = {
        'search_type': search_type,
        'filters': filters,
        'order_bys': order_bys,
        'project_code': project_code,
        'limit': limit,
        'offset': offset,
        'get_all_snapshots': get_all_snapshots,
        'check_snapshots_updates': check_snapshots_updates,
        'include_info': include_info,
        'include_snapshots': include_snapshots,
        'compressed_return': compressed_return,
        'include_status_log': include_status_log,
    }

    if not project_code:
        if search_type.startswith('sthpw'):
            project_code = 'sthpw'
        else:
            project_code = split_search_key(search_type)['project_code']

        kwargs['project_code'] = project_code
    else:
        if search_type.find('?') == -1:
            kwargs['search_type'] = server_start(project=project_code).build_search_type(search_type, project_code)

    sobjects_list = execute_procedure_serverside(tq.query_sobjects, kwargs, project=project_code)

    print(type(sobjects_list))

    if sobjects_list:
        print('PY2 UNICODE CHECK 5')
        if isinstance(sobjects_list, str):
            if sobjects_list.startswith('Traceback'):
                sobjects_list = {'sobjects_list': []}
                info = None
        else:
            info = {
                'total_sobjects_count': sobjects_list.get('total_sobjects_count'),
                'total_sobjects_query_count': sobjects_list.get('total_sobjects_query_count'),
                'limit': sobjects_list['limit'],
                'offset': sobjects_list['offset'],
            }

        sobjects = collections.OrderedDict()

        process_codes = list(process_list)
        for builtin in ['icon', 'attachment', 'publish']:
            if builtin not in process_codes:
                process_codes.append(builtin)

        # Create ordered dict of Sobject class Objects with snapshots, and some counts
        for sobject in sobjects_list['sobjects_list']:
            sobjects[sobject['__search_key__']] = SObject(sobject, process_codes, env_inst.projects[project_code])

            if include_snapshots:
                sobjects[sobject['__search_key__']].init_snapshots(sobject['__snapshots__'])

            if include_info:
                if sobject.get('process'):
                    sobjects[sobject['__search_key__']].set_notes_count(sobject['process'], sobject['__notes_count__'])
                else:
                    sobjects[sobject['__search_key__']].set_notes_count('publish', sobject['__notes_count__'])
                sobjects[sobject['__search_key__']].set_tasks_count('__total__', sobject['__tasks_count__'])
            if include_status_log:
                sobjects[sobject['__search_key__']].set_status_log(sobject['__status_log__'])

        if include_info:
            return sobjects, info
        else:
            return sobjects

# TEMPORARY
get_sobjects_new = get_sobjects
# TEMPORARY


def get_group_sobjects(search_type, project_code=None, groups_list=[]):

    kwargs = {
        'search_type': search_type,
        'project_code': project_code,
        'groups_list': groups_list,
    }

    if not project_code:
        if search_type.startswith('sthpw'):
            project_code = 'sthpw'
        else:
            project_code = split_search_key(search_type)['project_code']

        kwargs['project_code'] = project_code
    else:
        if search_type.find('?') == -1:
            kwargs['search_type'] = server_start(project=project_code).build_search_type(search_type, project_code)

    result = execute_procedure_serverside(tq.query_group_sobjects, kwargs, project=project_code)

    print(kwargs)

    return result


def get_sobjects_objects(sobjects_list, project_code):
    result = {}

    for searc_type, sobjects_list in sobjects_list.items():

        sobjects_dict = collections.OrderedDict()
        # Create ordered dict of Sobject class Objects
        for sobjects in sobjects_list:
            for sobject in sobjects:
                sobjects_dict[sobject['__search_key__']] = SObject(sobject, [], env_inst.projects[project_code])

        result[searc_type] = sobjects_dict

    return result

def server_query(filters, stype, columns=None, project=None, limit=0, offset=0, order_bys='timestamp desc'):
    """
    Query for searching assets
    """
    if not columns:
        columns = []

    server = server_start(project=project)

    built_process = server.build_search_type(stype, project)

    return server.query(built_process, filters, columns, order_bys, limit=limit, offset=offset)


def get_notes_count(sobject, process, children_stypes):

    kwargs = {
        'process': process,
        'search_key': sobject.get_search_key(),
        'stypes_list': children_stypes,
    }

    project_code = split_search_key(kwargs['search_key'])
    result = execute_procedure_serverside(tq.get_notes_and_stypes_counts, kwargs, project_code['project_code'])

    return result


def get_custom_scripts(store_locally=True, project=None, scripts_codes_list=None):
    if not project:
        project = env_inst.get_current_project()

    filters = []

    if scripts_codes_list:
        folders = []
        titles = []
        for script_code in scripts_codes_list:
            splitted = script_code.split('/')

            folders.append('/'.join(splitted[:-1]))
            titles.append(''.join(splitted[-1]))

        filters = (['folder', 'in', '|'.join(folders)], ['title', 'in', '|'.join(titles)])

    search_type = server_start().build_search_type('config/custom_script', project_code=project)

    scripts_sobjects, data = get_sobjects(search_type, filters)

    if store_locally:
        # writing scripts to local folder

        paths_to_create_init_set = set()
        scripts_sobjects_by_folder = group_sobject_by(scripts_sobjects, 'folder')

        for folder_path, sobjects_list in scripts_sobjects_by_folder.items():
            for sobject in sobjects_list:
                ext = 'py'
                if sobject.get_value('language') == 'javascript':
                    ext = 'js'
                file_name = u'{}.{}'.format(sobject.get_value('title'), ext)
                env_write_file(
                    sobject.get_value('script'),
                    folder_path,
                    file_name,
                    project
                )
            paths_list = folder_path.split('/')

            if paths_list:
                path_parts = u''
                for path in paths_list:
                    path_parts = u'{}/{}'.format(path_parts, path)
                    if path_parts:
                        if project:
                            full_path = u'{0}/custom_scripts/{1}/{2}/__init__.py'.format(
                                env_mode.get_current_path(),
                                project,
                                path_parts)
                        else:
                            full_path = u'{0}/custom_scripts/{1}/__init__.py'.format(
                                env_mode.get_current_path(),
                                path_parts)
                        paths_to_create_init_set.add(full_path)

        if project:
            paths_to_create_init_set.add(u'{0}/custom_scripts/{1}/__init__.py'.format(
                env_mode.get_current_path(),
                project))

        paths_to_create_init_set.add(u'{0}/custom_scripts/__init__.py'.format(
            env_mode.get_current_path()))

        # create __init__ files so we can access files from script editor
        for init_path in paths_to_create_init_set:
            formed_init_path = gf.form_path(init_path)
            if not os.path.isdir(formed_init_path):
                init_folder_path = gf.extract_dirname(formed_init_path)
                if not os.path.isdir(init_folder_path):
                    os.mkdir(init_folder_path)
                with io.open(formed_init_path, 'w+') as init_py_file:
                    init_py_file.write(u'')
                init_py_file.close()

    return scripts_sobjects


def execute_custom_script(script_path, kwargs=None, project=None, local_execution=True, refresh_scripts=True):
    """
    Use example:
    import thlib.environment as thenv
    thenv.tc().execute_custom_script('tools/runners/render_setup_runner', project='project_code')

    :param script_path: path to script e.g. 'folder/title'
    :param kwargs: kwarg for script executed on server
    :param project: project code string
    :param local_execution: execute locally or server-side
    :return:
    """

    if local_execution:

        if project:
            # making shure we have all environment for project ready
            env_inst.set_current_project(project)
            project_obj = env_inst.get_project_by_code(project)
            project_obj.get_stypes()

            if refresh_scripts:
                get_custom_scripts(project=project)

            module_path = u'{0}/custom_scripts/{1}/{2}.py'.format(env_mode.get_current_path(), project, script_path)
        else:
            module_path = u'{0}/custom_scripts/{1}.py'.format(env_mode.get_current_path(), script_path)

        with open(module_path, 'r') as py_file:
            source_code = py_file.read()
        py_file.close()

        env_inst.ui_script_editor.execute_source_code(source_code.decode('utf-8'))
    else:
        return server_start(project).execute_python_script(script_path, kwargs=kwargs)


def insert_sobjects(search_type, project_code, data, metadata={}, parent_key=None, instance_type=None,  info={}, use_id=False, triggers=True):

    kwargs = {
        'search_type': search_type,
        'project_code': project_code,
        'data': data,
        'metadata': metadata,
        'parent_key': parent_key,
        'instance_type': instance_type,
        'info': info,
        'use_id': use_id,
        'triggers': triggers
    }

    return execute_procedure_serverside(tq.insert_sobjects, kwargs, project=project_code)

# DEPRECATED
def insert_instance_sobjects(search_key, project_code, parent_key=None, instance_type=None):

    kwargs = {
        'search_key': search_key,
        'project_code': project_code,
        'parent_key': parent_key,
        'instance_type': instance_type,
    }

    return execute_procedure_serverside(tq.insert_instance_sobjects, kwargs, project=project_code)


def edit_multiple_instance_sobjects(project_code, insert_search_keys=[], exclude_search_keys=[], parent_key=None, instance_type=None, path=None):

    kwargs = {
        'project_code': project_code,
        'insert_search_keys': insert_search_keys,
        'exclude_search_keys': exclude_search_keys,
        'parent_key': parent_key,
        'instance_type': instance_type,
        'path': path,
    }

    return execute_procedure_serverside(tq.edit_multiple_instance_sobjects, kwargs, project=project_code)


# def delete_sobject_snapshot(sobject, delete_snapshot=True, search_keys=None, files_paths=None):
#     dep_list = {
#         'related_types': ['sthpw/file'],
#         'files_list': {'search_key': search_keys,
#                        'file_path': files_paths,
#                        'delete_snapshot': delete_snapshot,
#                        },
#     }
#     try:
#         print server_start().delete_sobject(sobject, list_dependencies=dep_list), 'delete_sobject_snapshot'
#         return True
#     except Exception as err:
#         print(err, 'delete_sobject_snapshot')
#         return False


def sobject_delete_confirm(sobjects):

    multiple_delete = False
    if isinstance(sobjects, list):
        if len(sobjects) > 1:
            multiple_delete = True
        else:
            multiple_delete = False
    else:
        sobjects = [sobjects]

    if multiple_delete:
        sobjects_list = []
        for i, sobject in enumerate(sobjects):
            if i > 15:
                sobjects_list.append(u'and <b>{0}</b> more sobjects'.format(len(sobjects) - i))
                break

            sobjects_list.append(u'<b>{0}</b>'.format(sobject.get_title()))

        msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Confirm Deleting',
                                u'<p>Do you really want to delete:<br><b>{0}</b> ?</p><p>Also remove dependencies?</p>'.format(u'<br>'.join(sobjects_list)),
                                QtGui.QMessageBox.NoButton, env_inst.ui_main)
    else:
        msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Confirm Deleting',
                                u'<p>Do you really want to delete:<br><b>{0}</b>?</p><p>Also remove dependencies?</p>'.format(
                                    sobjects[0].get_title()),
                                QtGui.QMessageBox.NoButton, env_inst.ui_main)

    msb.addButton("Delete", QtGui.QMessageBox.YesRole)
    msb.addButton("Cancel", QtGui.QMessageBox.NoRole)

    layout = QtGui.QVBoxLayout()

    widget = QtGui.QWidget()
    widget.setLayout(layout)

    msb_layot = msb.layout()

    # workaround for pyside2
    wdg_list = []

    for i in range(msb_layot.count()):
        wdg = msb_layot.itemAt(i).widget()
        if wdg:
            wdg_list.append(wdg)

    msb_layot.addWidget(wdg_list[0], 0, 0)
    msb_layot.addWidget(wdg_list[1], 0, 1)
    msb_layot.addWidget(wdg_list[2], 2, 1)
    msb_layot.addWidget(widget, 1, 1)

    from thlib.ui_classes.ui_delete_sobject_classes import deleteSobjectWidget

    delete_sobj_widget = deleteSobjectWidget(sobjects=sobjects)

    layout.addWidget(delete_sobj_widget)

    msb.exec_()
    reply = msb.buttonRole(msb.clickedButton())

    if reply == QtGui.QMessageBox.YesRole:
        return delete_sobj_widget.get_data_dict()
    else:
        return None


def snapshot_delete_confirm(snapshot, files):
    ver_rev = gf.get_ver_rev(snapshot['version'], snapshot['revision'])

    msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'Confirm deleting',
                            '<p><p>Do you really want to delete snapshot, with context:</p>{0}<p>Version: {1}</p>Also remove selected Files?</p>'.format(
                                snapshot['context'], ver_rev),
                            QtGui.QMessageBox.NoButton, env_inst.ui_main)

    msb.addButton("Delete", QtGui.QMessageBox.YesRole)
    msb.addButton("Cancel", QtGui.QMessageBox.NoRole)

    layout = QtGui.QVBoxLayout()

    widget = QtGui.QWidget()
    widget.setLayout(layout)

    msb_layot = msb.layout()

    # workaround for pyside2
    wdg_list = []

    for i in range(msb_layot.count()):
        wdg = msb_layot.itemAt(i).widget()
        if wdg:
            wdg_list.append(wdg)

    msb_layot.addWidget(wdg_list[0], 0, 0)
    msb_layot.addWidget(wdg_list[1], 0, 1)
    msb_layot.addWidget(wdg_list[2], 2, 1)
    msb_layot.addWidget(widget, 1, 1)

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


def get_dirs_with_naming(search_key, process_list=None):
    kwargs = {
        'search_key': search_key,
        'process_list': process_list
    }
    project_code = split_search_key(search_key)

    return execute_procedure_serverside(tq.get_dirs_with_naming, kwargs, project=project_code['project_code'])


def get_virtual_snapshot(search_key, context, files_dict, snapshot_type='file', is_revision=False, keep_file_name=False,
                         explicit_filename=None, version=None, checkin_type='file', ignore_keep_file_name=False):

    virtual_snapshot = {'versionless': {'paths': [], 'names': []}, 'versioned': {'paths': [], 'names': []}}

    kwargs = {
        'search_key': search_key,
        'context': context,
        'snapshot_type': snapshot_type,
        'is_revision': is_revision,
        'files_dict': json.dumps(files_dict),
        'keep_file_name': keep_file_name,
        'explicit_filename': explicit_filename,
        'version': version,
        'checkin_type': checkin_type,
        'ignore_keep_file_name': ignore_keep_file_name,
    }

    project_code = split_search_key(search_key)

    dl.log('Getting Virtual Snapshot', group_id='server/checkin')

    virtual_snapshot = execute_procedure_serverside(tq.get_virtual_snapshot_extended, kwargs, project=project_code['project_code'], return_dict=True)

    return virtual_snapshot


def checkin_snapshot(search_key, context, snapshot_type=None, is_revision=False, description=None, version=None,
                     update_versionless=True, only_versionless=False, keep_file_name=False, repo_name=None, virtual_snapshot=None,
                     files_dict=None, mode=None, create_icon=False, files_objects=None):
    files_info = {
        'version_files': [],
        'version_files_paths': [],
        'versionless_files': [],
        'versionless_files_paths': [],
        'files_types': [],
        'file_sizes': [],
        'version_metadata': [],
        'versionless_metadata': []
    }

    repo = repo_name['value'][0]

    for (k1, v1), (k2, v2), file_object in zip(virtual_snapshot, files_dict, files_objects):
        for path_v, name_v, path_vs, name_vs, tp in zip(v1['versioned']['paths'],
                                                        v1['versioned']['names'],
                                                        v1['versionless']['paths'],
                                                        v1['versionless']['names'],
                                                        v2['t']):
            file_path_v = u'{0}/{1}'.format(repo, path_v)
            file_full_path_v = u'{0}/{1}'.format(file_path_v, ''.join(name_v))
            files_info['version_files'].append(gf.form_path(file_full_path_v, 'linux'))
            files_info['version_files_paths'].append(gf.form_path(path_v, 'linux'))
            file_path_vs = u'{0}/{1}'.format(repo, path_vs)
            file_full_path_vs = u'{0}/{1}'.format(file_path_vs, ''.join(name_vs))
            files_info['versionless_files'].append(gf.form_path(file_full_path_vs, 'linux'))
            files_info['versionless_files_paths'].append(gf.form_path(path_vs, 'linux'))
            files_info['files_types'].append(tp)

            if only_versionless:
                new_files_list = file_object.get_all_new_files_list(name_vs, file_path_vs)

            else:
                new_files_list = file_object.get_all_new_files_list(name_v, file_path_v)

            files_info['file_sizes'].append(file_object.get_sizes_list(together=False, files_list=new_files_list))
            files_info['version_metadata'].append(file_object.get_metadata())
            file_object.get_all_new_files_list(name_vs, file_path_vs)
            files_info['versionless_metadata'].append(file_object.get_metadata())

    project_code = split_search_key(search_key)

    kwargs = {
        'search_key': search_key,
        'context': context,
        'project_code': project_code['project_code'],
        'snapshot_type': snapshot_type,
        'is_revision': is_revision,
        'description': description,
        'version': version,
        'update_versionless': update_versionless,
        'only_versionless': only_versionless,
        'keep_file_name': keep_file_name,
        'files_info': json.dumps(files_info, separators=(',', ':')),
        'repo_name': repo_name['value'][3],
        'mode': mode,
        'create_icon': create_icon,
    }

    server = server_start(project=project_code['project_code'])

    if mode == 'upload':
        s = gf.time_it()
        dl.log('Starting Upload Checkin ' + str(server), group_id='server/checkin')
        server.start('Upload Checkin', u'Upload Checkin from Tactic Handler by: {}'.format(env_inst.get_current_login()))
        gf.time_it(s, message='Transaction start: ')

        for version_file in files_info['version_files']:
            dl.log('Uploading File ' + version_file + ' ' + str(server), group_id='server/checkin')
            server.upload_file(version_file)
            dl.log('Done Uploading File ' + version_file + ' ' + str(server), group_id='server/checkin')

        gf.time_it(s, message='Upload time: ')
        dl.log('Begin Snapshot creation ' + search_key + ' ' + str(server), group_id='server/checkin')

        result = execute_procedure_serverside(tq.create_snapshot_extended, kwargs, project=project_code['project_code'], return_dict=False, server=server)
        gf.time_it(s, message='On Server execution: ')
        dl.log('Upload Finished' + ' ' + str(server), group_id='server/checkin')
        server.finish(u'Upload Checkin from Tactic Handler by: {}. Finished.'.format(env_inst.get_current_login()))
        gf.time_it(s, message='Transaction End: ')
    elif mode in ['inplace', 'preallocate']:
        server.start('Inplace Checkin', u'Inplace Checkin from Tactic Handler by: {}'.format(env_inst.get_current_login()))

        result = execute_procedure_serverside(tq.create_snapshot_extended, kwargs, project=project_code['project_code'], return_dict=False, server=server)

        server.finish(u'Inplace Checkin from Tactic Handler by: {}. Finished.'.format(env_inst.get_current_login()))

    if result:
        if isinstance(result, (str, unicode)):
            if result.startswith('Traceback'):
                dl.exception(result, group_id='{0}/{1}'.format('exceptions', get_virtual_snapshot.func_name))
                exception = Exception()
                exception.message = 'Tactic Exception when checkin snapshot'
                stacktrace_dict = {
                    'exception': exception,
                    'stacktrace': result
                }
                gf.error_handle((stacktrace_dict, None))
            else:
                return result
        else:
            return result


def update_description(search_key, description):
    data = {
        'description': description
    }
    return server_start().update(search_key, data)


def add_note(search_key, process, context, note, login):
    search_type = 'sthpw/note'

    data = {
        'process': process,
        'context': context,
        'note': note,
        'login': login,
    }
    project_code = split_search_key(search_key)
    transaction = server_start(project=project_code['project_code']).insert(search_type, data, parent_key=search_key, triggers=True)

    return transaction

def get_all_dependency(search_keys, project_code=None, return_sobjects=True):

    if not project_code:
        project_code = split_search_key(search_keys[0])['project_code']

    result = execute_procedure_serverside(tq.get_all_dependency, {'search_keys': search_keys}, project=project_code)

    if return_sobjects:
        return get_sobjects_objects(result, project_code)
    else:
        return result

def generate_web_and_icon(source_image_path, web_save_path=None, icon_save_path=None):

    image = Qt4Gui.QImage(0, 0, Qt4Gui.QImage.Format_ARGB32)

    if image.load(source_image_path):
        if web_save_path:
            web = image.scaledToWidth(640, QtCore.Qt.SmoothTransformation)
            web.save(web_save_path)
        if icon_save_path:
            icon = image.scaledToWidth(120, QtCore.Qt.SmoothTransformation)
            icon.save(icon_save_path)


def inplace_checkin(file_paths, virtual_snapshot, repo_name, update_versionless, only_versionless=False, generate_icons=True,
                    files_objects=None, padding=None, progress_callback=None):
    check_ok = False

    def copy_file(dest_path, source_path):
        if dest_path == source_path:
            print('Destination path is equal to source path, skipping...', dest_path)
        else:
            try:
                shutil.copyfile(source_path, dest_path)
            except Exception as err:
                print(err)
                print('File in the Local Structure is the Same! Just creating checkin and do nothing.')
        if not os.path.exists(dest_path):
            return False
        else:
            return True

    versions = ['versioned']
    if update_versionless:
        versions.extend(['versionless'])

    if only_versionless:
        versions = ['versionless']

    for i, (key, val) in enumerate(virtual_snapshot):
        if progress_callback:
            info_dict = {
                'status_text': key,
                'total_count': len(virtual_snapshot)
            }
            progress_callback(i, info_dict)
        for ver in versions:
            dest_path_vers = repo_name['value'][0] + '/' + val[ver]['paths'][0]
            dest_files_vers = files_objects[i].get_all_new_files_list(val[ver]['names'][0], dest_path_vers, new_frame_padding=padding)

            # create dest dirs
            if not os.path.exists(dest_path_vers):
                os.makedirs(dest_path_vers)

            # copy files to dest dir
            for j, fl in enumerate(file_paths[i]):
                check_ok = copy_file(gf.form_path(dest_files_vers[j]), gf.form_path(fl))
                if progress_callback:
                    info_dict = {
                        'status_text': gf.extract_filename(fl),
                        'total_count': len(file_paths[i])
                    }
                    progress_callback(j, info_dict)

            if generate_icons and len(val[ver]['paths']) > 1:
                dest_web_path_vers = gf.form_path(
                    repo_name['value'][0] + '/' +
                    val[ver]['paths'][1]
                )
                dest_web_file_vers = files_objects[i].get_all_new_files_list(val[ver]['names'][1], dest_web_path_vers)

                dest_icon_path_vers = gf.form_path(
                    repo_name['value'][0] + '/' +
                    val[ver]['paths'][2]
                )
                dest_icon_file_vers = files_objects[i].get_all_new_files_list(val[ver]['names'][2], dest_icon_path_vers)
                if not os.path.exists(dest_web_path_vers):
                    os.makedirs(dest_web_path_vers)
                if not os.path.exists(dest_icon_path_vers):
                    os.makedirs(dest_icon_path_vers)

                # convert original to web and icon format
                # TODO at this moment it converting twice when doing versionless
                for k, fl in enumerate(file_paths[i]):
                    generate_web_and_icon(fl, dest_web_file_vers[k], dest_icon_file_vers[k])
                    # if ver == 'versioned':
                    #     generate_web_and_icon(fl, dest_web_file_vers[k], dest_icon_file_vers[k])
                    # else:
                    #     copy_file(dest_files_vers[j], fl)

    return check_ok


# Checkin functions
def checkin_file(search_key, context, snapshot_type='file', is_revision=False, description=None, version=None,
                 only_versionless=False, update_versionless=True, file_types=None, file_names=None, file_paths=None,
                 exts=None, subfolders=None, postfixes=None, metadata=None, padding=None, keep_file_name=False,
                 repo_name=None, mode=None, create_icon=True, ignore_keep_file_name=False, checkin_app='standalone',
                 selected_objects=False, ext_type='mayaAscii', setting_workspace=False, checkin_type='file',
                 files_dict=None, item_widget=None, files_objects=None, explicit_filename=None, commit_silently=False,
                 run_before_checkin=None, run_after_checkin=None, single_threaded=False):

    if not files_dict:
        files_dict = []

        for i, fn in enumerate(file_names):
            file_dict = dict()
            file_dict['t'] = [file_types[i]]
            file_dict['s'] = [subfolders[i]]
            file_dict['e'] = [exts[i]]
            file_dict['p'] = [postfixes[i]]
            if metadata:
                file_dict['m'] = metadata[i]
            else:
                file_dict['m'] = None

            files_dict.append((fn, file_dict))

        # extending files which can have thumbnails
        for key, val in files_dict:
            if gf.file_format(val['e'][0])[3] == 'preview':
                val['t'].extend(['web', 'icon'])
                val['s'].extend(['', ''])
                val['e'].extend(['jpg', 'png'])
                val['p'].extend(['', ''])

    args_dict = {
        'search_key': search_key,
        'context': context,
        'snapshot_type': snapshot_type,
        'is_revision': is_revision,
        'description': description,
        'version': version,
        'update_versionless': update_versionless,
        'only_versionless': only_versionless,
        'file_paths': file_paths,
        'padding': padding,
        'files_dict': files_dict,
        'keep_file_name': keep_file_name,
        'explicit_filename': explicit_filename,
        'repo_name': repo_name,
        'mode': mode,
        'create_icon': create_icon,
        'ignore_keep_file_name': ignore_keep_file_name,
        'checkin_app': checkin_app,
        'selected_objects': selected_objects,
        'ext_type': ext_type,
        'setting_workspace': setting_workspace,
        'checkin_type': checkin_type,
        'item_widget': item_widget,
        'files_objects': files_objects,
        'run_before_checkin': run_before_checkin,
        'run_after_checkin': run_after_checkin,
    }

    search_key_split = split_search_key(search_key)

    checkin_wdg = env_inst.get_check_tree(
        search_key_split['project_code'],
        'checkin_out',
        search_key_split['pipeline_code'])

    if commit_silently:
        commit_queue = env_inst.get_commit_queue('global_commit_queue')
        if not commit_queue:
            from thlib.ui_classes.ui_commit_queue_classes import Ui_commitQueueWidget
            commit_queue = Ui_commitQueueWidget(parent=checkin_wdg)
            env_inst.commit_queue['global_commit_queue'] = commit_queue

        commit_queue.setParent(checkin_wdg)
        commit_queue.add_item_to_queue(args_dict, commit_queue)
        commit_queue.setWindowModality(QtCore.Qt.ApplicationModal)
        commit_queue.splitter.moveSplitter(2000, 0)
        commit_queue.show()
    elif single_threaded:
        commit_queue = env_inst.get_commit_queue(search_key_split['project_code'])
        commit_queue.set_single_threaded(True)
        commit_queue.add_item_to_queue(args_dict)
        commit_queue.show()
    else:
        commit_queue = env_inst.get_commit_queue(search_key_split['project_code'])
        commit_queue.set_single_threaded(False)
        commit_queue.add_item_to_queue(args_dict)
        commit_queue.show()

    return commit_queue


# Skey functions
def parce_skey(skey, get_skey_and_context=False, return_sobject=True):

    if get_skey_and_context:
        skey_list = skey[7:].split('&context=')
        return {'search_key': skey_list[0], 'context': skey_list[1]}

    skey_splitted = urlparse.urlparse(skey)
    skey_dict = dict(urlparse.parse_qsl(skey_splitted.query))
    skey_dict['namespace'] = skey_splitted.netloc
    skey_dict['pipeline_code'] = skey_splitted.path[1:]

    if skey_splitted.scheme == 'skey':
        if skey_dict['pipeline_code'] == 'snapshot':
            skey_dict['type'] = 'snapshot'
            snapshot = server_start().query('sthpw/snapshot', [('code', skey_dict.get('code'))])
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

        if return_sobject:
            filters = [('code', '=', skey_dict.get('code'))]
            search_type = server_start().build_search_type(u'{namespace}/{pipeline_code}'.format(**skey_dict), project_code=skey_dict.get('project'))

            sobjects = get_sobjects(search_type, filters)[0]
            if sobjects:
                sobject = sobjects.values()[0]
            return skey_dict, sobject
        else:
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


def group_sobject_by(sobjects_dict, group_by):
    grouped = collections.defaultdict(list)

    if isinstance(sobjects_dict, list):
        sobjects = sobjects_dict
    else:
        sobjects = sobjects_dict.values()

    if group_by == 'timestamp':
        # Special case for timestamp group by
        for sobject in sobjects:
            timestamp = sobject.get_timestamp(obj=True)
            seconds = time.mktime(timestamp.timetuple())
            grouped[seconds].append(sobject)

        return sorted(grouped.items())
    else:
        for sobject in sobjects:
            dic = sobject.info
            grouped[dic.get(group_by)].append(sobject)

    return grouped
