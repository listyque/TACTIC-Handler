# module Tactic Classes
# file tactic_classes.py
# Global TACTIC Functions Module

import os
import sys
import io
import shutil
import urllib
from urllib.parse import urlparse, parse_qsl
import collections
import copy
import json
import datetime
from decimal import Decimal, InvalidOperation
from thlib.tactic_xml import parse_tactic_xml
import time
import thlib.proxy as proxy
from thlib.request_retry import run_read_only_request
from thlib.environment import env_mode, env_server, env_inst, env_tactic, env_write_config, env_read_config, env_write_file, dl
import thlib.global_functions as gf
import thlib.tactic_query as tq
from thlib.side.client.tactic_client_lib.tactic_server_stub import TacticServerStub


def server_auth(host, project=None, login=None, password=None, site=None, get_ticket=False):
    server = TacticServerStub(protocol='xmlrpc', setup=False)
    server.set_transport(proxy.UrllibTransport())
    if env_server.get_proxy()['enabled']:
        server.transport.enable_proxy()
    else:
        server.transport.disable_proxy()

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
    from thlib.side.Qt import QtWidgets as QtGui
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

    if proxy_dict.get('enabled'):

        transport = proxy.UrllibTransport()
        server.set_transport(transport)

        server.transport.update_proxy(proxy_dict)
        server.transport.enable_proxy()
    # else:
    #     server.transport.update_proxy(proxy_dict)
    #     server.transport.disable_proxy()
    #     server.set_transport(None)

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


def get_match_list_by_type(column_type):
    match_list = [
        ('Is', '='),
        ('Is not', '!='),
        ('Contains', 'EQI'),
        ('Does not contain', 'NEQI'),
        ('Is empty', None),
        ('Is not empty', 'like'),
        ('Starts with', 'like'),
        ('Ends with', 'like'),
        ('Does not starts with', 'not like'),
        ('Does not end with', 'not like'),
        ('In', 'in'),
        ('Not in', 'not in'),
        ('Is distinct', ''),
    ]

    if column_type == 'boolean':
        match_list = [
            ('Is', '='),
            ('Is not', '!='),
            ('Is empty', None),
            ('Is not empty', None),
        ]
    elif column_type in ['integer', 'float', 'currency']:
        match_list = [
            ('is equal to', ''),
            ('is greater than', ''),
            ('is less than', ''),
            ('in', 'in'),
            ('not in', 'not in'),
            ('is empty', None),
            ('is not empty', ''),
            ('is distinct', ''),
        ]
    elif column_type in ['time', 'timestamp', 'datetime2']:
        match_list = [
            ('is newer than', ''),
            ('is older than', ''),
            ('is on', ''),
            ('is empty', None),
            ('is not empty', ''),
        ]
    elif column_type in ['login']:
        match_list = [
            ('is', '='),
            ('is not', '!='),
            ('contains', 'EQI'),
            ('does not contain', 'NEQI'),
            ('is empty', None),
            ('is not empty', ''),
            ('starts with', ''),
            ('ends with', ''),
        ]
    elif column_type in ['_expression']:
        match_list = [
            ('Have', 'in'),
            ('Do not have', 'not in'),
            ('Match (slow)', 'match'),
            ('Do not match (slow)', 'do not match'),
        ]
    elif column_type in ['timecode']:
        match_list = [
            ('is timecode before', '<='),
            ('is timecode after', '>='),
            ('is timecode equal', '='),
            ('is empty', None),
        ]

    return match_list


def get_search_relation(relation):

    possible_relations = get_match_list_by_type('all')
    for possible_relation in possible_relations:
        if possible_relation[0].lower() == relation.lower():
            return possible_relation[1]


def unpack_tactic_search_view(search_view):
    filters_list = []

    js_string = search_view.values.string
    if js_string:
        filters_list = gf.from_json(js_string)

    if filters_list:

        filters_dict = {}

        # breaking filters by prefix
        for fl in filters_list:
            filters_dict.setdefault(fl['prefix'], []).append(fl)

        filters = filters_dict['main_body']

        final_filters_list = []

        for fltr in filters:

            relation_name = fltr['main_body_relation']
            if relation_name == 'expression':
                relation_name = fltr['main_body_op']
            relation = get_search_relation(relation_name)

            column = fltr['main_body_column']
            value = fltr['main_body_value']

            filter_list = (column, relation, value)

            final_filters_list.append(filter_list)

        return final_filters_list


def pack_tactic_search_view(filters_list):
    ops_list = []

    # adding filter mode, by now it is always "and"
    tactic_filters_list = [{'prefix': 'filter_mode', 'filter_mode': 'and'}]

    # breaking filters by prefix
    for enabled, filters, op in filters_list:

        if op != 'begin':
            ops_list.append(op)

        filter_dict = {'prefix': 'main_body', 'main_body_enabled': 'on'}

        column = filters[0]
        relation = filters[1]
        value = filters[2]

        if column == '_expression':

            filter_dict['main_body_relation'] = 'expression'
            filter_dict['main_body_op'] = relation
        elif column == 'timestamp':
            filter_dict['main_body_relation'] = relation
            filter_dict['main_body_select'] = ''
        else:
            filter_dict['main_body_relation'] = relation

            filter_dict['filter_type'] = '_column'

        filter_dict['filter_type'] = '_column'
        filter_dict['main_body_column'] = column
        filter_dict['main_body_value'] = value
        if enabled:
            filter_dict['main_body_enabled'] = 'on'
        else:
            filter_dict['main_body_enabled'] = ''

        tactic_filters_list.append(filter_dict)

    # TACTIC Search Views store flat operators in a parallel search_ops row.
    ops_dict = {'prefix': 'search_ops', 'levels': [], 'ops': [], 'modes': []}
    for op in ops_list:
        ops_dict['levels'].append(0)
        ops_dict['ops'].append(op)
        ops_dict['modes'].append('child')

    tactic_filters_list.append(ops_dict)

    return json.dumps(tactic_filters_list)


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
        if search_type_object is None:
            # System/config tables can be opened and queried without a
            # project SearchType object. They do not own repository-sync
            # snapshot state, so there is no local update list to read.
            return []

        group_path = u'ui_search/{0}/{1}/{2}/sobjects_conf'.format(
            search_type_object.project.info['type'],
            search_type_object.project.info['code'],
            search_type_object.get_code().split('/')[1]
        )

        # Repository Sync stores all per-sObject checkpoints in one
        # file to avoid thousands of tiny config reads.
        aggregate = env_read_config(
            filename='repository_sync_state',
            unique_id=group_path,
            long_abs_path=True,
        ) or {}
        timestamps = dict(aggregate) if isinstance(aggregate, dict) else {}

        return sorted(timestamps.items())

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

    # .get_notes()
    # .notes['sculpt'].notes()
    """

    def __init__(self, in_sobj=None, project=None):
        """
        :param in_sobj: input list with info on particular sobject
        :return:
        """

        # INPUT VARS
        self.info = in_sobj
        self.project = project

        # OUTPUT VARS
        self.process = {}
        self.tasks_sobjects = None
        self.task_summaries = {}
        self.notes_sobjects = None
        self.snapshots_sobjects = None
        self.files_sobjects = None
        self.notes = {}
        self.status_log = []
        self.progress_counts_dict = {}

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

    # Query snapshots to update current
    def update_snapshots(self, order_bys=None, filters=None, force=False):

        from thlib import server_cache

        project_code = str(self.project.get_code() or '')
        cache_key = json.dumps({
            'target': self.get_search_key(),
            'orderBys': list(order_bys or []),
            'filters': list(filters or []),
        }, ensure_ascii=False, default=str, separators=(',', ':'),
            sort_keys=True)
        if force:
            server_cache.invalidate_domains(('snapshots',), project_code)
        cache_token = server_cache.token('snapshots', project_code)
        snapshot_dict = None if force else server_cache.read_entry(
            'snapshots', cache_key, project_code,
        )
        if not isinstance(snapshot_dict, list):
            if self.info.get('code'):
                snapshot_dict = self.query_snapshots(
                    s_code=self.info['code'], order_bys=order_bys,
                    filters=filters,
                )
            else:
                snapshot_dict = self.query_snapshots(
                    s_id=self.info['id'], order_bys=order_bys,
                    filters=filters,
                )
            if cache_token is not None:
                server_cache.write_entry(
                    'snapshots', cache_key, snapshot_dict, project_code,
                    expected_token=cache_token,
                )
        self.process = {}
        self.init_snapshots(snapshot_dict)

    # Initial Snapshots by process without query
    def init_snapshots(self, snapshot_dict):
        process_set = set(snapshot['process'].split('/')[-1] for snapshot in snapshot_dict)

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

    def get_work_hours(self, login=None, start_day=None, end_day=None,
                       statuses=None):
        result = query_work_hours(
            [], self.project.get_code(), login=login,
            start_day=start_day, end_day=end_day, statuses=statuses,
            parent_codes=[self.get_code()],
        )
        return result['entries']

    @staticmethod
    def get_multiple_work_hours(sobjects_list, login=None, start_day=None,
                                end_day=None, statuses=None,
                                include_rates=False):
        if not sobjects_list:
            return {'entries': [], 'permissions': {}, 'rates': {}}
        project = sobjects_list[0].get_project()
        task_objects = all(
            str(sobject.get_search_type() or '').split('?')[0]
            == Task.SEARCH_TYPE
            for sobject in sobjects_list
        )
        return query_work_hours(
            [sobject.get_code() for sobject in sobjects_list]
            if task_objects else [],
            project.get_code(), login=login, start_day=start_day,
            end_day=end_day, statuses=statuses,
            include_rates=include_rates,
            parent_codes=[] if task_objects else [
                sobject.get_code() for sobject in sobjects_list
            ],
        )

    def set_tasks_count(self, process, count):
        self.tasks_count[process] = count

    def get_tasks_count(self, process=None):
        if process:
            return self.tasks_count.get(process)
        else:
            return self.tasks_count

    def set_task_summaries(self, process, records):
        self.task_summaries[str(process or 'publish')] = [
            dict(record or {}) for record in (records or [])
        ]

    def get_task_summaries(self, process=None):
        if process:
            return list(self.task_summaries.get(str(process), ()))
        return {
            key: list(records)
            for key, records in self.task_summaries.items()
        }

    def set_status_log(self, status_log):

        for status in status_log:
            self.status_log.append(SObject(status, project=self.project))

    def set_progress_counts(self, counts_dict):
        self.progress_counts_dict = counts_dict

    def get_progress_count(self, process, count_type='total_count'):
        result = self.progress_counts_dict.get(process)

        if result:
            if count_type == 'total_count':
                return result['tc']

            if count_type == 'approved_count':
                return result['ac']

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

    def delete_sobject(self, include_dependencies=False,
                       list_dependencies=None):
        """Delete this object after the calling UI has confirmed the action."""
        dependencies_dict = None
        if list_dependencies:
            dependencies_dict = {
                'related_types': list_dependencies
            }

        kwargs = {
            'search_keys': self.get_search_key(),
            'include_dependencies': include_dependencies,
            'list_dependencies': dependencies_dict,
        }
        return execute_procedure_serverside(tq.delete_sobjects, kwargs)

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

    def get_info(self, value=None):
        if value:
            return self.info.get(value)
        else:
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
            return gf.get_full_datetime(dateime)
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


        if not relations:
            raise ValueError(
                'No {0} relationship between {1} and {2}'.format(
                    path, parent_stype.get_code(), child_stype.get_code()
                )
            )

        relationship = relations.get('relationship')

        if relationship:

            if relationship in ['code', 'search_type']:
                # Schema relations are directed from child to parent.  A
                # search_type relationship uses the standard search_code
                # column; a direct code relationship uses the declared
                # foreign key (or the conventional <parent>_code column).
                related_from_column = relations.get('from_col')
                if not related_from_column:
                    if relationship == 'search_type':
                        related_from_column = 'search_code'
                    else:
                        related_from_column = '{0}_code'.format(
                            relations.get('to').split('/')[-1]
                        )
                related_to_column = relations.get('to_col') or 'code'

                if path == 'parent':
                    related_value = self.info.get(related_from_column)
                    query_column = related_to_column
                else:
                    related_value = self.info.get(related_to_column)
                    query_column = related_from_column

                if related_value is None:
                    raise ValueError(
                        'Relationship column {0} is missing on {1}'.format(
                            related_from_column if path == 'parent'
                            else related_to_column,
                            self.get_search_key(),
                        )
                    )

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

        if relationship not in ('code', 'search_type', 'instance'):
            raise ValueError(
                'Unsupported relationship {0} between {1} and {2}'.format(
                    relationship,
                    parent_stype.get_code(),
                    child_stype.get_code(),
                )
            )

        if relationship == 'instance':
            if path == 'parent':
                return u"@SOBJECT({0}['{1}', '{2}'].{3})".format(instance_type, related_from_column, related_code, related_type)
            else:
                return u"@SOBJECT({0}['{1}', '{2}'].{3})".format(instance_type, related_to_column, related_code, related_type)
        else:
            return u"@SOBJECT({0}['{1}', '{2}'])".format(
                related_type, query_column, related_value
            )

    def get_related_sobjects(self, child_stype=None, parent_stype=None, get_all_snapshots=False, path='child', filters=None, force=False):

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

        from thlib import server_cache

        project_code = str(self.project.get_code() or '')
        cache_key = json.dumps({
            'target': self.get_search_key(),
            'childType': child_stype.get_code(),
            'parentType': parent_stype.get_code(),
            'path': path,
            'filters': list(filters or []),
            'snapshots': bool(get_all_snapshots),
        }, ensure_ascii=False, default=str, separators=(',', ':'),
            sort_keys=True)
        if force:
            server_cache.invalidate_domains(('relations',), project_code)
        cache_token = server_cache.token('relations', project_code)
        can_cache = bool(
            cache_token is not None
            and (
                not get_all_snapshots
                or server_cache.domain_enabled('snapshots')
            )
        )
        payload = None if force or not can_cache else server_cache.read_entry(
            'relations', cache_key, project_code,
        )
        if isinstance(payload, dict):
            return hydrate_sobjects_payload(
                payload, project_code, include_info=True,
                include_snapshots=True,
            )
        fetched = get_sobjects(
            search_type=built_process,
            filters=expr_filters,
            order_bys=order_bys,
            project_code=project_code,
            get_all_snapshots=get_all_snapshots,
            return_payload=True,
        )
        if not fetched:
            result = (collections.OrderedDict(), {})
            payload = {
                'sobjects_list': [], 'limit': 0, 'offset': 0,
                'total_sobjects_count': 0,
                'total_sobjects_query_count': 0,
            }
        else:
            result, payload = fetched
        if can_cache:
            server_cache.write_entry(
                'relations', cache_key, payload, project_code,
                expected_token=cache_token,
            )
        return result

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
        self.views = ViewsConfig([], project=self)
        self.sidebar = None

        self.process = {}
        self.update_dict = {}

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

    def get_config_views(self):
        return self.views

    def get_type(self):
        return self.info.get('type')

    def is_template(self):
        return self.info.get('is_template')

    def is_builtin(self):
        return bool(self.info.get('__builtin__'))

    def commit(self, triggers=True):
        data = dict(self.update_dict)
        if not data:
            return self.info
        result = server_start(project='sthpw').update(
            self.get_search_key(),
            data=data,
            triggers=triggers,
        )
        self.info.update(data)
        self.update_dict.clear()
        if isinstance(result, dict):
            self.info.update(result)
        return result

    def get_stypes(self):
        if self.stypes is None:
            return self.query_search_types()
        else:
            return self.stypes

    def get_search_type(self, search_type):
        return self.stypes[search_type]

    def query_search_types(self, force=False, cache_only=False):

        # Project configuration is safe to restore for presentation while a
        # fresh authoritative copy is requested in the background.
        use_cache = env_mode.get_mode() != 'api_server'
        stypes_result = None
        cache_key = 'search_types:{0}'.format(self.get_code())

        if use_cache and not force:
            from thlib import server_cache

            stypes_result = server_cache.read_entry(
                'reference', cache_key, self.get_code(),
            )
            if not stypes_result and cache_only:
                return []
            if not stypes_result:
                return self.query_search_types(True)
        else:
            from thlib import server_cache

            if use_cache and force:
                server_cache.invalidate_domains(
                    ('reference',), self.get_code()
                )
            cache_token = (
                server_cache.token('reference', self.get_code())
                if use_cache else None
            )
            kwargs = {
                'project_code': self.get_code(),
            }

            stypes_result = execute_procedure_serverside(tq.query_search_types_extended, kwargs, project=self.get_code(), return_dict=False)

            if stypes_result and cache_token is not None:
                server_cache.write_entry(
                    'reference', cache_key, stypes_result, self.get_code(),
                    expected_token=cache_token,
                )

        stypes = json.loads(stypes_result)

        views = stypes.get('views') or []
        schema = stypes.get('schema')
        pipelines = stypes.get('pipelines') or []
        stypes = stypes.get('stypes') or []
        prj_schema = (schema[0]['schema'] if schema else '') or ''

        # System and newly created projects need not have a production schema
        # or pipelines. Their Search Types and views are still valid metadata.
        return self.get_all_search_types(stypes, pipelines, prj_schema, views)

    def get_all_search_types(self, stype_list, process_list, schema, views):
        pipeline = parse_tactic_xml(schema)
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
        workflow = Workflow(process_list)

        # getting stypes processes here
        stypes_objects = collections.OrderedDict()
        for stype in stype_list:
            stype_process = collections.OrderedDict()
            stype_schema = dct.get(stype['code'])

            for process in process_list:
                if process.get('search_type') == stype['code']:
                    stype_process[process['code']] = process

            stype_obj = SType(stype, stype_schema, stype_process, project=self)
            stypes_objects[stype['code']] = stype_obj

        self.stypes = stypes_objects
        self.workflow = workflow

        # getting definition for sidebar
        self.views = ViewsConfig(views, project=self)

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

        # This is because some of built-in views hardcoded in source files
        definition_xml = self.info.get('definition')

        if not definition_xml:
            views = self.project.get_config_views()
            return views.get_view(search_type=self.get_code(), view=definition, processed=processed, bs=bs)

        if bs:
            return parse_tactic_xml(self.info['definition'].get(definition))

        if processed:

            definition_bs = parse_tactic_xml(self.info['definition'].get(definition))

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


class ViewsConfig(SObject):
    def __init__(self, config_dict, project=None):
        super(self.__class__, self).__init__(project=project)

        self.config_dict = config_dict

    def has_definition(self):

        if self.config_dict:
            return True
        else:
            return False

    def update_views(self, filters=None):
        if filters:
            views = self.query_views(filters)
        else:
            views = self.query_views([])

        def merge_dict_lists(list1, list2):
            merged_list = list1.copy()

            for dict2 in list2:
                if dict2 not in merged_list:
                    merged_list.append(dict2)

            return merged_list

        if views:
            if filters:
                self.config_dict = merge_dict_lists(self.config_dict, views)
            else:
                # if there were no filters, so just update whole config
                self.config_dict = views

            return views

    def query_views(self, filters=None):

        server = server_start(project=self.project.info['code'])

        presets = server.query('config/widget_config', filters)

        return presets

    def get_view(self, search_type, view='definition', login='', processed=True, bs=False):

        view_xml = ''

        for config in self.config_dict:
            if config['search_type'] == search_type:
                if login:
                    if config['login'] == login:
                        if config['view'] == view:
                            view_xml = config['config']
                            break
                if config['view'] == view:
                    view_xml = config['config']
                    break

        if bs:
            return parse_tactic_xml(view_xml)

        if processed:
            view_bs = parse_tactic_xml(view_xml)

            all_elements = []
            for element in view_bs.find_all(name='element'):
                all_elements.append(element)

            return all_elements
        else:
            return view_xml

    def get_views(self, config_list=None, processed=True, bs=False):

        if bs:
            if config_list:

                out_list = []
                for config in config_list:
                    view_xml = config['config']
                    out_list.append(parse_tactic_xml(view_xml))

                return out_list
            else:
                out_list = []
                for config in self.config_dict:
                    view_xml = config['config']
                    out_list.append(parse_tactic_xml(view_xml))

                return out_list

        if processed:
            if config_list:

                out_list = []
                for config in config_list:
                    view_xml = config['config']

                    view_bs = parse_tactic_xml(view_xml)

                    all_elements = []
                    for element in view_bs.find_all(name='element'):
                        all_elements.append(element)

                    out_list.append(all_elements)
            else:
                out_list = []
                for config in self.config_dict:
                    view_xml = config['config']

                    view_bs = parse_tactic_xml(view_xml)

                    all_elements = []
                    for element in view_bs.find_all(name='element'):
                        all_elements.append(element)

                    out_list.append(all_elements)


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
        self.__pipeline_by_parent_process = {}

        self.sort_by_search_types()

    def __get_by_stype(self, search_type_code):
        tasks_pipeliens = {}
        for pipe in self.__pipeline_list:
            if pipe['search_type'] == search_type_code:
                tasks_pipeliens[pipe['code']] = Pipeline(pipe)

        return tasks_pipeliens

    def sort_by_search_types(self):
        self.__pipeline_by_codes = {}
        self.__pipeline_by_parent_process = {}
        for pipe in self.__pipeline_list:
            search_type_code = pipe.get('search_type')
            if search_type_code:
                pipeline = Pipeline(pipe)
                self.__pipeline_by_codes.setdefault(search_type_code, {})[
                    pipe['code']
                ] = pipeline
                parent_process = pipe.get('parent_process')
                if parent_process and parent_process not in self.__pipeline_by_parent_process:
                    self.__pipeline_by_parent_process[parent_process] = pipeline

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
        parent_process = parent_pipeline.get_pipeline_process(process)
        if parent_process:
            return self.get_pipeline_by_parent(parent_process)

    def get_pipeline_by_parent(self, parent_process):
        if isinstance(parent_process, dict):
            parent_process = parent_process.get('code')
        return self.__pipeline_by_parent_process.get(parent_process)


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

        pipeline = parse_tactic_xml(self.info['pipeline'])

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

    def get_processes_info_by_type(self, type):
        """
        Returns all possible processes with given type of node:
        For example to get all "progress" nodes
        get_processes_info_by_type("progress")

        Args:
            type: string with node type

        Returns:
            list of all found processes with info dicts

        """

        processes = self.get_all_pipeline_names()

        processes_list = []

        for process in processes:
            process_info = self.pipeline.get(process)
            if process_info['type'] == type:
                processes_list.append(process_info)

        return processes_list

    def get_process_label(self, process):
        process_info = self.get_process_info(process)
        if process_info:
            process_label = process_info.get('label')
            process_name = process_info.get('name')
            if process_label:
                return process_label
            elif process_name:
                return process_name
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

        self.process = {}

        self.__init_login_groups()

    def get_object_type(self):
        return self.object_type

    def get_all_login_groups(self):
        return self.login_groups

    def get_login_groups(self):
        # get all login groups related to current login
        current_login_groups = []
        for login_group in self.login_groups:
            for login_in_group in self.login_in_groups:
                if self.info['login'] == login_in_group['login']:
                    if login_group.get_login_group() == login_in_group['login_group']:
                        current_login_groups.append(login_group)

        return current_login_groups

    def get_login_group(self, login_group_code):
        # getting login group by group code
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

    def get_hourly_wage(self):
        try:
            return Decimal(str(self.info.get('hourly_wage') or 0))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal('0')

    def get_info(self):
        return self.info

    def __init_login_groups(self):
        # Build the reverse LoginGroup -> Login membership once. Task and
        # editor user pickers consume LoginGroup.get_logins().
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

    def check_security(self, group, path, project=None):
        if self.get_code() == 'admin':
            return 'allow'

        current_login_groups = self.get_login_groups()

        for login_group in current_login_groups:
            if login_group:
                security_group = login_group.get_security_group(group, project)
                if security_group:
                    for security in security_group:
                        attr, name = path.split(':')
                        if security.attrs[attr] == name:
                            return security.attrs['access']


class LoginGroup(SObject):
    object_type = 'login_group'

    def __init__(self, login_group):

        self.info = login_group
        self.group_logins = []
        self.security = {}
        self.projects_security = {}

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

    def get_security(self, project=None):
        if project:
            if self.projects_security.get(project):
                return self.projects_security[project]
        elif self.security:
            return self.security

        bs = parse_tactic_xml(self.info['access_rules'])

        self.security = {}
        for element in bs.find_all(name='rule'):
            if project:
                if element.get('project') == project:
                    self.security.setdefault(element.attrs['group'], []).append(element)
            else:
                self.security.setdefault(element.attrs['group'], []).append(element)

        self.projects_security[project] = self.security

        if project:
            return self.projects_security.get(project)
        else:
            return self.security

    def get_security_group(self, group, project=None):
        security = self.get_security(project)

        if security:
            return security.get(group)


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
    def __init__(self, in_dict, process):
        # Contexts
        self.contexts = {}
        contexts = set()
        versions = collections.defaultdict(list)
        versionless = collections.defaultdict(list)
        for snapshot in in_dict:
            if snapshot['process'].split('/')[-1] == process and (
                    snapshot['version'] == -1 or snapshot['version'] == 0):
                versionless[snapshot['context']].append(snapshot)
            elif snapshot['process'].split('/')[-1] == process:
                versions[snapshot['context']].append(snapshot)
            if snapshot['process'].split('/')[-1] == process:
                contexts.add(snapshot['context'])

        for context in contexts:
            self.contexts[context] = Contexts(
                versionless[context], versions[context]
            )

    def get_contexts(self):
        return self.contexts


class Contexts(object):
    def __init__(self, versionless=None, versions=None):

        self.versions = None
        self.versionless = None
        self.versions = collections.OrderedDict()
        self.versionless = collections.OrderedDict()
        for sn in versions or ():
            self.versions[sn['code']] = Snapshot(sn)
        for sn in versionless or ():
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
            if group_by not in list(self.goupped_by_files_objects.keys()):
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
    """
    This class is wrap for TACTIC File SObject
    It can contain Meta-File object. Which is created from templates and can be complicated:
    Sequences, UDIM, folder and etc. Meta is more powerful, and is preffered to use instead of File class
    Typical use: query files > create File class > if there is meta info (only with TH) it creates FileObject class
    """

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

    def get_md5(self):
        """Return the checksum recorded by TACTIC for this file, if present."""
        return str(self.info.get('md5') or '').strip().lower()

    def get_snapshot(self):
        return self.__snapshot

    def get_metadata(self):
        metadata = self.info.get('metadata')
        # Simple check if this is json dumpable
        if isinstance(metadata, str):
            if metadata.startswith(('{', '"', '[')):
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
        # for this who interested what is meta object go to class implementation
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
        if not server_address.startswith(('http://', 'https://')):
            server_address = u'http://{}'.format(server_address)
        asset_path = u'{0}/{1}'.format(server_address, env_tactic.get_base_dir('web')['value'][0])

        abs_path = gf.form_path(u'{0}/{1}'.format(asset_path, self.info['relative_dir']), tp='web')
        return abs_path

    def get_full_web_path(self):
        return '{0}/{1}'.format(self.get_web_path(), self.info['file_name'])

    def is_exists(self):
        return os.path.isfile(self.get_full_abs_path())

    def is_local_current(self, timestamp_tolerance=2.0):
        """Return whether the repository copy matches this TACTIC file row."""
        try:
            local_stat = os.stat(self.get_full_abs_path())
        except OSError:
            return False

        try:
            expected_size = int(self.get_file_size() or 0)
        except (KeyError, TypeError, ValueError):
            expected_size = 0
        if expected_size > 0 and local_stat.st_size != expected_size:
            return False

        try:
            server_timestamp = self.get_timestamp(obj=True)
            server_mtime = (
                server_timestamp.timestamp()
                if isinstance(server_timestamp, datetime.datetime) else 0.0
            )
        except (KeyError, TypeError, ValueError, OSError):
            server_mtime = 0.0
        return (
            server_mtime <= 0
            or abs(local_stat.st_mtime - server_mtime)
            <= float(timestamp_tolerance or 0.0)
        )

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

        # Repository sync may prepare several files from the same snapshot in
        # parallel.  The original check-then-create sequence races when two
        # workers create the shared preview directory at the same time.
        os.makedirs(dest_path, exist_ok=True)

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


class Task(SObject):
    SEARCH_TYPE = 'sthpw/task'

    def get_bid_duration(self, unit='hour'):
        try:
            duration = Decimal(str(self.get_value('bid_duration') or 0))
        except (InvalidOperation, TypeError, ValueError):
            duration = Decimal('0')
        source_unit = str(
            self.get_value('__bid_duration_unit__') or 'hour'
        ).lower()
        if source_unit == unit:
            return duration
        if source_unit == 'minute' and unit == 'hour':
            return duration / Decimal('60')
        if source_unit == 'hour' and unit == 'minute':
            return duration * Decimal('60')
        return duration

    def log_work_hours(self, day, hours, description='',
                       category='regular', login=None):
        return WorkHour.create(
            self, day, hours, description=description,
            category=category, login=login,
        )

    def get_work_hours(self, login=None, start_day=None, end_day=None,
                       statuses=None):
        result = query_work_hours(
            [self.get_code()], self.project.get_code(), login=login,
            start_day=start_day, end_day=end_day, statuses=statuses,
        )
        return result['entries']


class WorkHour(SObject):
    SEARCH_TYPE = 'sthpw/work_hour'
    REGULAR = 'regular'
    OVERTIME = 'overtime'
    APPROVED = 'approved'

    @classmethod
    def create(cls, task, day, hours, description='', category=REGULAR,
               login=None, start_time=None, end_time=None, approve=False):
        project = task.get_project()
        result = mutate_work_hour(
            'create', project.get_code(), task_code=task.get_code(),
            values={
                'day': day,
                'straight_time': hours,
                'description': description,
                'category': category,
                'login': login,
                'start_time': start_time,
                'end_time': end_time,
                'approve': bool(approve),
            },
        )
        return cls(result, project=project)

    def get_regular_hours(self):
        if self.get_value('category') == self.OVERTIME:
            return 0.0
        return float(self.get_value('straight_time') or 0)

    def get_overtime_hours(self):
        value = float(self.get_value('over_time') or 0)
        if value:
            return value
        if self.get_value('category') == self.OVERTIME:
            return float(self.get_value('straight_time') or 0)
        return 0.0

    def get_total_hours(self):
        if self.get_value('category') == self.OVERTIME:
            return self.get_overtime_hours()
        return self.get_regular_hours() + float(self.get_value('over_time') or 0)

    def get_labor_cost(self, hourly_rate, overtime_factor=1):
        try:
            rate = Decimal(str(hourly_rate or 0))
            factor = Decimal(str(overtime_factor or 1))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal('0')
        regular = Decimal(str(self.get_regular_hours()))
        overtime = Decimal(str(self.get_overtime_hours()))
        return regular * rate + overtime * rate * factor

    def is_approved(self):
        return str(self.get_value('status') or '').lower() == self.APPROVED

    def can_edit(self):
        return bool(self.get_value('__can_edit__'))

    def can_approve(self):
        return bool(self.get_value('__can_approve__'))

    def update_entry(self, **values):
        result = mutate_work_hour(
            'update', self.project.get_code(),
            work_hour_code=self.get_code(), values=values,
        )
        self.info.update(result)
        return self

    def approve(self, approved=True):
        result = mutate_work_hour(
            'approve' if approved else 'reject', self.project.get_code(),
            work_hour_code=self.get_code(),
        )
        self.info.update(result)
        return self

    def delete(self):
        return mutate_work_hour(
            'delete', self.project.get_code(),
            work_hour_code=self.get_code(),
        )


class TacticProcedureError(RuntimeError):
    """A server-side TACTIC procedure returned a Python traceback."""

    def __init__(self, procedure, server_traceback, project=None):
        self.procedure = str(procedure or 'unknown')
        self.project = project
        self.server_traceback = str(server_traceback or '')
        lines = [line.strip() for line in self.server_traceback.splitlines()
                 if line.strip()]
        summary = lines[-1] if lines else 'Unknown server error'
        super(TacticProcedureError, self).__init__(
            'TACTIC procedure {0} failed: {1}'.format(
                self.procedure, summary
            )
        )


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

    if isinstance(ret_val, str) and ret_val.lstrip().startswith('Traceback'):
        procedure_name = getattr(func, '__name__', str(func))
        dl.exception(
            ret_val,
            group_id='{0}/{1}'.format('exceptions', procedure_name),
        )
        raise TacticProcedureError(procedure_name, ret_val, project=project)

    if return_dict:
        if isinstance(ret_val, str):
            # Simple check if this is json dumpable
            if ret_val.startswith(('{', '"', '[')):
                final_result = json.loads(ret_val, strict=False)
            else:
                final_result = ret_val

            if isinstance(final_result, str) and return_dict:
                # Decompress long query
                js = gf.hex_to_html(final_result)
                if js:
                    if js.startswith(('{', '"', '[')):
                        final_result = json.loads(js, strict=False)
        else:
            final_result = ret_val
    else:
        final_result = ret_val

    return final_result


def _execute_read_only_procedure_serverside(
        func, kwargs, project=None, return_dict=True, server=None):
    """Execute a procedure whose server implementation is strictly read-only."""
    procedure_name = getattr(func, '__name__', str(func))

    def report_retry(exception, attempt, attempts, delay):
        dl.warning(
            'Temporary server failure while reading {0}; attempt {1}/{2} '
            'failed, retrying in {3:.2f} s: {4}'.format(
                procedure_name, attempt, attempts, delay, exception
            ),
            caller=3,
            group_id='server/retry/{0}'.format(procedure_name),
        )

    return run_read_only_request(
        lambda: execute_procedure_serverside(
            func, kwargs, project=project, return_dict=return_dict,
            server=server,
        ),
        on_retry=report_retry,
    )


def _project_object(project_code):
    project = env_inst.projects.get(project_code)
    if project is None and project_code == 'sthpw':
        project = env_inst.projects.get(env_server.get_project())
    return project


def _work_hour_objects(values, project_code):
    project = _project_object(project_code)
    return [WorkHour(value, project=project) for value in (values or [])]


def query_work_hours(task_codes, project_code, login=None, start_day=None,
                     end_day=None, statuses=None, include_rates=False,
                     parent_codes=None, return_payload=False, payload=None):
    if payload is None:
        result = execute_procedure_serverside(
            tq.query_work_hours,
            {
            'task_codes': list(task_codes or []),
            'project_code': project_code,
            'login': login,
            'start_day': start_day,
            'end_day': end_day,
            'statuses': list(statuses or []),
            'include_rates': bool(include_rates),
            'parent_codes': list(parent_codes or []),
            },
            project=project_code,
        ) or {}
    else:
        result = copy.deepcopy(payload)
    raw_payload = copy.deepcopy(result)
    result['entries'] = _work_hour_objects(
        result.get('entries'), project_code
    )
    return (result, raw_payload) if return_payload else result


def mutate_user_profile(login, values=None, password=None, groups=None,
                        group_access_levels=None, require_admin=False):
    return execute_procedure_serverside(
        tq.mutate_user_profile,
        {
            'login': str(login or ''),
            'values': dict(values or {}),
            'password': str(password or ''),
            'groups': None if groups is None else list(groups),
            'group_access_levels': (
                None if group_access_levels is None
                else dict(group_access_levels)
            ),
            'require_admin': bool(require_admin),
        },
        project='sthpw',
    )


def create_user_profile(login, values=None, password=None, groups=None, require_admin=False):
    return execute_procedure_serverside(
        tq.create_user_profile,
        {
            'login': str(login or ''),
            'values': dict(values or {}),
            'password': str(password or ''),
            'groups': list(groups or []),
            'require_admin': bool(require_admin),
        },
        project='sthpw',
    )


def mutate_sidebar_security(project_code, updates=None):
    return execute_procedure_serverside(
        tq.mutate_sidebar_security,
        {
            'project_code': str(project_code or ''),
            'updates': [dict(item) for item in (updates or [])],
        },
        project='sthpw',
    )


def mutate_work_hour(action, project_code, task_code=None,
                     work_hour_code=None, values=None):
    return execute_procedure_serverside(
        tq.mutate_work_hour,
        {
            'action': action,
            'project_code': project_code,
            'task_code': task_code,
            'work_hour_code': work_hour_code,
            'values': dict(values or {}),
        },
        project=project_code,
    )


def set_work_hour_statuses(work_hour_codes, approved, project_code):
    result = execute_procedure_serverside(
        tq.set_work_hour_statuses,
        {
            'work_hour_codes': list(work_hour_codes or []),
            'approved': bool(approved),
            'project_code': project_code,
        },
        project=project_code,
    )
    return _work_hour_objects(result, project_code)


def query_work_hour_report(report_key, project_code, start_day=None,
                           end_day=None, login=None):
    return execute_procedure_serverside(
        tq.query_work_hour_report,
        {
            'report_key': report_key,
            'project_code': project_code,
            'start_day': start_day,
            'end_day': end_day,
            'login': login,
        },
        project=project_code,
    )


def get_all_projects_and_logins(force=False, cache_only=False):

    if env_mode.get_mode() == 'api_server':
        use_cache = False
    else:
        use_cache = True

    from thlib import server_cache

    cache_key = 'projects_and_logins'
    projects_and_users = None
    if use_cache and not force:
        projects_and_users = server_cache.read_entry(
            'reference', cache_key, 'sthpw',
        )
        if not isinstance(projects_and_users, dict):
            if cache_only:
                return collections.OrderedDict()
            return get_all_projects_and_logins(True)
    if projects_and_users is None:
        if use_cache and force:
            server_cache.invalidate_domains(('reference',), 'sthpw')
        cache_token = (
            server_cache.token('reference', 'sthpw') if use_cache else None
        )
        kwargs = {
            'current_login': env_inst.get_current_login()
        }
        projects_and_users = execute_procedure_serverside(tq.get_projects_and_logins, kwargs)

        if cache_token is not None and isinstance(projects_and_users, dict):
            server_cache.write_entry(
                'reference', cache_key, projects_and_users, 'sthpw',
                expected_token=cache_token,
            )

    projects = projects_and_users.get('projects') or []
    logins = projects_and_users.get('logins') or []
    login_groups = projects_and_users.get('login_groups') or []
    login_in_groups = projects_and_users.get('login_in_groups') or []

    projects_dict = collections.OrderedDict()

    for project in projects:
        project_sobject = Project(project)
        project_sobject.init_snapshots(project.get('__snapshots__') or [])
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
        login_sobject = Login(login, login_groups_list, login_in_groups_list)
        login_sobject.init_snapshots(login.get('__snapshots__') or [])
        logins_dict[login.get('code')] = login_sobject

    env_inst.logins = logins_dict

    return projects_dict


def get_tasks_and_notes(
        sobject=None, search_code=None, project_code=None,
        process='publish', include_all_tasks=False, return_payload=False,
        payload=None):

    if sobject:
        search_code = sobject.get_code()
        project_code = sobject.get_project().get_code()

    kwargs = {
        'search_code': search_code,
        'project_code': project_code,
    }

    if process != '__latest__':
        kwargs['process'] = process
    if include_all_tasks:
        kwargs['include_all_tasks'] = True

    if payload is None:
        tasks_and_notes = execute_procedure_serverside(
            tq.get_tasks_and_notes, kwargs
        )
    else:
        tasks_and_notes = copy.deepcopy(payload)
    raw_payload = copy.deepcopy(tasks_and_notes or {})

    notes = tasks_and_notes.get('notes') or []

    # Making Notes sObjects
    notes_dict = collections.OrderedDict()

    for note in notes:
        note_sobject = SObject(note, project=env_inst.projects[project_code])
        note_sobject.init_snapshots(note['__snapshots__'])
        notes_dict[note.get('code')] = note_sobject

    # Making Tasks sObjects
    tasks = tasks_and_notes.get('tasks') or []
    tasks_dict = collections.OrderedDict()

    for task in tasks:
        task_sobject = Task(task, project=env_inst.projects[project_code])
        task_process = str(task.get('process') or 'publish')
        note_count = int(task.get('__notes_count__') or 0)
        task_sobject.set_notes_count(task_process, note_count)
        tasks_dict[task.get('code')] = task_sobject
        status_log = task.get('__status_log__')
        if status_log:
            task_sobject.set_status_log(status_log)

    if sobject:
        # Make aggregate branch counts visible before selection_changed emits.
        note_counts = dict(raw_payload.get('noteCounts') or {})
        if not note_counts:
            for task in tasks:
                task_process = str(task.get('process') or 'publish')
                note_counts[task_process] = (
                    note_counts.get(task_process, 0)
                    + int(task.get('__notes_count__') or 0)
                )
        for task_process, note_count in note_counts.items():
            sobject.set_notes_count(task_process, int(note_count or 0))
        for task_process in set(
                str(task.get('process') or 'publish') for task in tasks):
            sobject.set_task_summaries(task_process, [
                task for task in tasks
                if str(task.get('process') or 'publish') == task_process
            ])

    hydrated = (tasks_dict, notes_dict)
    return (hydrated, raw_payload) if return_payload else hydrated


def get_notes_with_attachments(note_codes, project_code):
    """Batch-load note attachment objects without querying each parent."""
    payload = execute_procedure_serverside(
        tq.get_notes_with_attachments,
        {
            'note_codes': list(note_codes or []),
            'project_code': project_code,
        },
        project=project_code,
    )
    project = env_inst.get_project_by_code(project_code)
    notes = collections.OrderedDict()
    for info in (payload or {}).get('notes') or []:
        note = SObject(info, project=project)
        note.init_snapshots(info.get('__snapshots__') or [])
        notes[str(info.get('code') or '')] = note
    return notes


def get_task_workspace_page(filters, order_bys, project_code,
                            limit=500, offset=0, query=None):
    """Return native Task/SObject instances from one batched RPC."""
    payload = execute_procedure_serverside(
        tq.query_task_workspace_page,
        {
            'filters': list(filters or []),
            'order_bys': list(order_bys or []),
            'project_code': project_code,
            'limit': limit,
            'offset': offset,
            'query': dict(query or {}),
        },
        project=project_code,
    ) or {}
    project = env_inst.get_project_by_code(project_code)
    tasks = []
    for info in payload.get('tasks') or []:
        task = Task(info, project)
        task.set_notes_count(
            str(info.get('process') or 'publish'),
            int(info.get('__notes_count__') or 0),
        )
        tasks.append(task)
    parents = [
        SObject(info, project) for info in payload.get('parents') or []
    ]
    return {
        'tasks': tasks,
        'parents': parents,
        'total': payload.get('total'),
        'facets': dict(payload.get('facets') or {}),
        'offset': int(payload.get('offset') or 0),
        'limit': int(payload.get('limit') or 0),
    }


def get_subscriptions_and_messages(current_login='admin', update_logins=False):

    kwargs = {
        'current_login': current_login,
        'update_logins': update_logins,
    }

    return execute_procedure_serverside(tq.get_subscriptions_and_messages, kwargs)


def get_chat_conversations():
    return execute_procedure_serverside(
        tq.query_chat_conversations, {}, project='sthpw'
    )


def create_chat_conversation(recipients, title=''):
    return execute_procedure_serverside(
        tq.create_chat_conversation,
        {
            'recipients': list(recipients or []),
            'title': {'value': title},
        },
        project='sthpw',
    )


def update_chat_conversation(message_code, title):
    return execute_procedure_serverside(
        tq.update_chat_conversation,
        {'message_code': message_code, 'title': {'value': title}},
        project='sthpw',
    )


def add_chat_members(message_code, recipients):
    return execute_procedure_serverside(
        tq.add_chat_members,
        {'message_code': message_code, 'recipients': list(recipients or [])},
        project='sthpw',
    )


def set_chat_members(message_code, recipients):
    return execute_procedure_serverside(
        tq.add_chat_members,
        {
            'message_code': message_code,
            'recipients': list(recipients or []),
            'replace': True,
        },
        project='sthpw',
    )


def delete_chat_conversation(message_code):
    return execute_procedure_serverside(
        tq.delete_chat_conversation,
        {'message_code': message_code},
        project='sthpw',
    )


def clear_personal_chat(message_code):
    return execute_procedure_serverside(
        tq.clear_personal_chat,
        {'message_code': message_code},
        project='sthpw',
    )


def delete_chat_message(message_log_code):
    return execute_procedure_serverside(
        tq.delete_chat_message,
        {'message_log_code': message_log_code},
        project='sthpw',
    )


def edit_chat_message(message_log_code, message):
    return execute_procedure_serverside(
        tq.edit_chat_message,
        {'message_log_code': message_log_code, 'message': message},
        project='sthpw',
    )


def toggle_chat_message_reaction(message_log_code, emoji):
    return execute_procedure_serverside(
        tq.toggle_chat_message_reaction,
        {'message_log_code': message_log_code, 'emoji': emoji},
        project='sthpw',
    )


def pin_chat_message(message_log_code):
    return execute_procedure_serverside(
        tq.pin_chat_message,
        {'message_log_code': message_log_code},
        project='sthpw',
    )


def unpin_chat_message(message_log_code):
    return execute_procedure_serverside(
        tq.pin_chat_message,
        {'message_log_code': message_log_code, 'unpin': True},
        project='sthpw',
    )


def get_chat_history(message_code, limit=31, offset=0, search_text=''):
    return execute_procedure_serverside(
        tq.query_chat_history,
        {
            'message_code': message_code,
            'limit': limit,
            'offset': offset,
            'search_text': search_text,
        },
        project='sthpw',
    )


def mark_chat_read(message_code, timestamp):
    return execute_procedure_serverside(
        tq.mark_chat_read,
        {'message_code': message_code, 'timestamp': timestamp},
        project='sthpw',
    )


def send_chat_message(message_code, message, attachment_keys=None, reply_to=None):
    return execute_procedure_serverside(
        tq.send_chat_message,
        {
            'message_code': message_code,
            'message': message,
            'attachment_keys': list(attachment_keys or []),
            'reply_to': reply_to,
        },
        project='sthpw',
    )


def forward_chat_messages(message_log_keys, target_message_codes):
    return execute_procedure_serverside(
        tq.forward_chat_messages,
        {
            'message_log_keys': list(message_log_keys or []),
            'target_message_codes': list(target_message_codes or []),
        },
        project='sthpw',
    )


def authorize_chat_attachment(message_code, snapshot_code):
    return execute_procedure_serverside(
        tq.authorize_chat_attachment,
        {
            'message_code': message_code,
            'snapshot_code': snapshot_code,
        },
        project='sthpw',
    )


def get_server_updates(message_after='', activity_after='', project_code='',
                       limit=101, reaction_after='', include_activity=True,
                       include_reactions=True, include_presence=False,
                       presence_ttl=360, cache_after='',
                       include_messages=True, heartbeat_presence=True):
    return execute_procedure_serverside(
        tq.query_server_updates,
        {
            'message_after': message_after,
            'activity_after': activity_after,
            'reaction_after': reaction_after,
            'project_code': project_code,
            'limit': limit,
            'include_activity': include_activity,
            'include_reactions': include_reactions,
            'include_presence': include_presence,
            'heartbeat_presence': bool(heartbeat_presence),
            'presence_ttl': int(presence_ttl or 360),
            'cache_after': str(cache_after or ''),
            'include_cache_changes': True,
            'include_messages': bool(include_messages),
        },
        project='sthpw',
    )


def get_user_recent_activity(
        login='', project_code='', limit=25, offset=0, kinds=None,
        assigned_login='', include_day_counts=False, day='', logins=None,
        counts_only=False, counts_from_day='', instance_relations=None,
        object_scope=None, exclude_login=''):
    """Return enriched activity using the shared profile/feed API."""
    return _execute_read_only_procedure_serverside(
        tq.query_user_recent_activity,
        {
            'login': login,
            'project_code': project_code,
            'limit': limit,
            'offset': offset,
            'kinds': list(kinds or ()),
            'assigned_login': assigned_login,
            'include_day_counts': bool(include_day_counts),
            'counts_only': bool(counts_only),
            'counts_from_day': str(counts_from_day or ''),
            'day': str(day or ''),
            'logins': list(logins or ()),
            'instance_relations': dict(instance_relations or {}),
            'object_scope': dict(object_scope or {}),
            'exclude_login': str(exclude_login or ''),
        },
        project='sthpw',
    )


def get_user_profile_data(login='', project_code='', activity_limit=25):
    return _execute_read_only_procedure_serverside(
        tq.query_user_profile_data,
        {
            'login': login,
            'project_code': project_code,
            'activity_limit': activity_limit,
        },
        project='sthpw',
    )


def heartbeat_user_presence(ttl_seconds=90):
    """Refresh current-login presence and return known login states."""
    return execute_procedure_serverside(
        tq.heartbeat_user_presence,
        {'ttl_seconds': int(ttl_seconds or 90)},
        project='sthpw',
    )


def duplicate_sobjects(search_keys, data_dict):
    """
    Deletes bunch of sobjects
    !!! SEARCH KEYS MUST BE SAME SEARCH TYPE !!!
    :param search_keys: ['sthpw/snapshot?code=SNAPSHOT000000']
    :param data_dict: {'search_types': [u'sthpw/snapshot', 'sthpw/notes', 'sthps/file'], 'new_name': 'name'}
    :return: deleted sobjects dict
    """

    if not isinstance(search_keys, list):
        search_keys = [search_keys]
    if not search_keys:
        raise ValueError('At least one sObject search key is required')
    data_dict = dict(data_dict or {})
    fields = {}
    if data_dict.get('new_name') is not None:
        fields['name'] = data_dict.get('new_name')
    return duplicate_sobject_advanced(
        search_keys[0], {'fields': fields}
    )


def analyze_sobject_duplicate(search_key):
    """Inspect editable values, schema relations and copyable content."""
    project_code = split_search_key(search_key).get('project_code')
    return _execute_read_only_procedure_serverside(
        tq.analyze_sobject_duplicate,
        {'search_key': search_key},
        project=project_code,
    )


def duplicate_sobject_advanced(search_key, options=None):
    """Duplicate one sObject using the explicit wizard selections."""
    project_code = split_search_key(search_key).get('project_code')
    return execute_procedure_serverside(
        tq.duplicate_sobject_advanced,
        {'search_key': search_key, 'options': dict(options or {})},
        project=project_code,
    )


def delete_sobjects(search_keys, list_dependencies):
    """
    Deletes bunch of sobjects
    !!! SEARCH KEYS MUST BE SAME SEARCH TYPE !!!
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


def hydrate_sobjects_payload(
        payload, project_code, include_info=True, include_snapshots=True,
        include_status_log=False, include_progress=False):
    """Build native Handler objects from a raw ``query_sobjects`` payload.

    Persistent caches store only server dictionaries.  Rehydrating through
    this function preserves the native SObject/File/Snapshot API and avoids
    serializing live QObject-adjacent object graphs.
    """
    sobjects_list = copy.deepcopy(payload or {})
    if not isinstance(sobjects_list, dict):
        return (collections.OrderedDict(), {}) if include_info else collections.OrderedDict()

    info = {
        'total_sobjects_count': sobjects_list.get('total_sobjects_count'),
        'total_sobjects_query_count': sobjects_list.get(
            'total_sobjects_query_count'
        ),
        'limit': sobjects_list.get('limit'),
        'offset': sobjects_list.get('offset'),
    }
    sobjects = collections.OrderedDict()
    project = env_inst.projects.get(project_code)
    if project is None:
        project = _project_object(project_code)
    for sobject in sobjects_list.get('sobjects_list') or []:
        object_type = str(
            sobject.get('__search_type__')
            or sobject.get('__search_key__') or ''
        )
        if object_type.startswith('skey://'):
            object_type = object_type[7:]
        object_type = object_type.split('?', 1)[0]
        object_class = {
            WorkHour.SEARCH_TYPE: WorkHour,
            Task.SEARCH_TYPE: Task,
        }.get(object_type, SObject)
        search_key = sobject.get('__search_key__')
        if not search_key:
            continue
        native = object_class(sobject, project)
        sobjects[search_key] = native

        if include_snapshots:
            native.init_snapshots(sobject.get('__snapshots__') or [])
        if include_info:
            if object_type == Task.SEARCH_TYPE:
                process = str(sobject.get('process') or 'publish')
                native.set_notes_count(
                    process, int(sobject.get('__notes_count__') or 0)
                )
                native.set_tasks_count('__total__', 0)
            else:
                native.notes_count = {}
                native.tasks_count = {}
                for process, count in dict(
                        sobject.get('__notes_count_by_process__') or {}
                ).items():
                    native.set_notes_count(str(process), int(count or 0))
                for process, count in dict(
                        sobject.get('__tasks_count_by_process__') or {}
                ).items():
                    native.set_tasks_count(str(process), int(count or 0))
                for process, records in dict(
                        sobject.get('__task_details_by_process__') or {}
                ).items():
                    native.set_task_summaries(str(process), records)
                native.set_tasks_count(
                    '__total__', int(sobject.get('__tasks_count__') or 0)
                )
        if include_status_log:
            native.set_status_log(sobject.get('__status_log__') or [])
        if include_progress:
            native.set_progress_counts(sobject.get('__progress__') or {})

    return (sobjects, info) if include_info else sobjects


def get_sobjects(search_type, filters=[], order_bys=[], project_code=None, limit=None, offset=None, get_all_snapshots=False, check_snapshots_updates=False, include_info=True, include_snapshots=True, compressed_return=True, include_status_log=False, include_progress=False, include_total_count=True, snapshot_timestamps=None, return_payload=False):
    """
    Filters snapshot by search codes, and sobjects codes
    :param search_type: search_type or search_key (if using search_type project_code should to be provided)
    :param project_code: assign project class to particular sObject
    :return: tuple : (dict, dict) of sObjects objects
    """

    filters = json.dumps(filters, ensure_ascii=False).encode('utf-8')

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
        'include_progress': include_progress,
        'include_total_count': include_total_count,
        'snapshot_timestamps': snapshot_timestamps or [],
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

    sobjects_list = _execute_read_only_procedure_serverside(
        tq.query_sobjects, kwargs, project=project_code
    )

    if sobjects_list:
        if isinstance(sobjects_list, str):
            if sobjects_list.startswith('Traceback'):
                sobjects_list = {'sobjects_list': []}
        if not isinstance(sobjects_list, dict):
            return None
        raw_payload = copy.deepcopy(sobjects_list)
        hydrated = hydrate_sobjects_payload(
            raw_payload,
            project_code,
            include_info=include_info,
            include_snapshots=include_snapshots,
            include_status_log=include_status_log,
            include_progress=include_progress,
        )
        if return_payload:
            return hydrated, raw_payload
        return hydrated


# Legacy custom scripts use this public name.
get_sobjects_new = get_sobjects


def get_table_layout(search_type, search_keys=None, view='table',
                     project_code=None):
    """Return native TACTIC table definitions and rendered text cells."""
    if not project_code:
        project_code = (
            'sthpw' if search_type.startswith('sthpw')
            else split_search_key(search_type)['project_code']
        )
    return _execute_read_only_procedure_serverside(
        tq.query_table_layout,
        {
            'search_type': search_type,
            'search_keys': list(search_keys or []),
            'view': str(view or 'table'),
            'project_code': project_code,
        },
        project=project_code,
    )


def save_widget_config(search_type, view, config_xml=None,
                       element_xml=None, project_code=None):
    if not project_code:
        project_code = (
            'sthpw' if search_type.startswith('sthpw')
            else split_search_key(search_type)['project_code']
        )
    return execute_procedure_serverside(
        tq.save_widget_config,
        {
            'search_type': search_type,
            'view': str(view or 'table'),
            'config_xml': config_xml,
            'element_xml': element_xml,
            'project_code': project_code,
        },
        project=project_code,
    )

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

    return result


def get_sobjects_objects(sobjects_list, project_code):
    result = {}

    for searc_type, sobjects_list in sobjects_list.items():

        sobjects_dict = collections.OrderedDict()
        # Create ordered dict of Sobject class Objects
        for sobjects in sobjects_list:
            for sobject in sobjects:
                sobjects_dict[sobject['__search_key__']] = SObject(
                    sobject, env_inst.projects[project_code]
                )

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

    # TACTIC's XML-RPC query implementation passes the result of an
    # _expression filter to add_relationship_filters one object at a time on
    # some server versions. A Task is therefore treated as an iterable and
    # the request fails with "'Task' object is not iterable".
    # Our normal query_sobjects procedure evaluates TEL as one relationship
    # collection, so keep expression queries on that native Handler path.
    has_expression = any(
        isinstance(value, (list, tuple))
        and len(value) >= 1
        and value[0] == '_expression'
        for value in (filters or [])
    )
    if has_expression:
        order_by_values = (
            [order_bys] if isinstance(order_bys, str)
            else list(order_bys or [])
        )
        sobjects = get_sobjects(
            built_process,
            filters=filters,
            order_bys=order_by_values,
            project_code=project,
            limit=limit or None,
            offset=offset or None,
            include_info=False,
            include_snapshots=False,
        ) or collections.OrderedDict()
        if columns:
            return [
                {
                    column: sobject.get_value(column)
                    for column in columns
                }
                for sobject in sobjects.values()
            ]
        return [
            dict(sobject.get_info() or {})
            for sobject in sobjects.values()
        ]

    return server.query(built_process, filters, columns, order_bys, limit=limit, offset=offset)


def get_notes_count(sobject, process, children_stypes):

    kwargs = {
        'process': process,
        'search_key': sobject.get_search_key(),
        'stypes_list': children_stypes,
    }

    project_code = split_search_key(kwargs['search_key'])
    result = execute_procedure_serverside(tq.get_notes_and_stypes_counts, kwargs, project_code['project_code'])

    for task_process, records in (
            (result or {}).get('taskDetails') or {}).items():
        sobject.set_task_summaries(task_process, records)

    return result


def _custom_script_value(script, name):
    if isinstance(script, dict):
        return script.get(name)
    return script.get_value(name)


def normalize_custom_script_path(folder, title):
    path = '{}/{}'.format(folder or '', title or '').replace('\\', '/')
    parts = [part.strip() for part in path.split('/') if part.strip()]
    if not parts or any(part in ('.', '..') for part in parts):
        raise ValueError('Invalid custom script path: {!r}'.format(path))
    return '/'.join(parts[:-1]), parts[-1]


def _custom_script_local_path(script, project):
    folder, title = normalize_custom_script_path(
        _custom_script_value(script, 'folder'),
        _custom_script_value(script, 'title'),
    )
    extension = (
        'js' if _custom_script_value(script, 'language') == 'javascript'
        else 'py'
    )
    root = os.path.abspath(os.path.join(
        env_mode.get_current_path(), 'custom_scripts', str(project or '')
    ))
    path = os.path.abspath(os.path.join(root, folder, '{}.{}'.format(
        title, extension
    )))
    if os.path.commonpath((root, path)) != root:
        raise ValueError('Custom script path escapes its project directory')
    return path


def _custom_script_mirror_is_current(scripts, project):
    expected = set()
    for script in scripts:
        path = _custom_script_local_path(script, project)
        expected.add(os.path.normcase(path))
        try:
            timestamp = gf.parce_timestamp(
                _custom_script_value(script, 'timestamp')
            )
        except (TypeError, ValueError):
            return False
        if (
                timestamp is None
                or not os.path.isfile(path)
                or abs(os.path.getmtime(path) - timestamp.timestamp()) >= 0.001):
            return False

    root = os.path.abspath(os.path.join(
        env_mode.get_current_path(), 'custom_scripts', str(project or '')
    ))
    if not os.path.isdir(root):
        return not expected
    for folder, _directories, files in os.walk(root):
        for file_name in files:
            if file_name == '__init__.py' or not file_name.endswith(('.py', '.js')):
                continue
            if os.path.normcase(os.path.join(folder, file_name)) not in expected:
                return False
    return True


def get_custom_scripts_manifest(project=None):
    project = project or env_inst.get_current_project()
    tactic = server_start(project=project)
    search_type = tactic.build_search_type(
        'config/custom_script', project_code=project
    )
    scripts = tactic.query(
        search_type,
        columns=['code', 'folder', 'title', 'language', 'timestamp'],
        order_bys=['folder', 'title'],
    ) or []
    return list(scripts)


def sync_custom_scripts(project=None):
    project = project or env_inst.get_current_project()
    manifest = get_custom_scripts_manifest(project)
    if _custom_script_mirror_is_current(manifest, project):
        return None, False
    return get_custom_scripts(store_locally=True, project=project), True


def _prune_custom_script_mirror(scripts, project):
    expected = {
        os.path.normcase(_custom_script_local_path(script, project))
        for script in scripts
    }
    root = os.path.abspath(os.path.join(
        env_mode.get_current_path(), 'custom_scripts', str(project or '')
    ))
    if not os.path.isdir(root):
        return
    for folder, _directories, files in os.walk(root):
        for file_name in files:
            if file_name == '__init__.py' or not file_name.endswith(('.py', '.js')):
                continue
            path = os.path.abspath(os.path.join(folder, file_name))
            if os.path.normcase(path) not in expected:
                os.remove(path)


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

        for _folder_path, sobjects_list in scripts_sobjects_by_folder.items():
            for sobject in sobjects_list:
                folder_path, title = normalize_custom_script_path(
                    sobject.get_value('folder'), sobject.get_value('title')
                )
                ext = 'py'
                if sobject.get_value('language') == 'javascript':
                    ext = 'js'
                file_name = u'{}.{}'.format(title, ext)
                env_write_file(
                    sobject.get_value('script'),
                    folder_path,
                    file_name,
                    project,
                    modified_at=sobject.get_value('timestamp'),
                )
                path_parts = u''
                for path in filter(None, folder_path.split('/')):
                    path_parts = u'{}/{}'.format(path_parts, path)
                    if project:
                        full_path = u'{0}/custom_scripts/{1}/{2}/__init__.py'.format(
                            env_mode.get_current_path(), project, path_parts)
                    else:
                        full_path = u'{0}/custom_scripts/{1}/__init__.py'.format(
                            env_mode.get_current_path(), path_parts)
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

        if not scripts_codes_list:
            _prune_custom_script_mirror(
                list(scripts_sobjects.values())
                if isinstance(scripts_sobjects, dict)
                else list(scripts_sobjects or []),
                project,
            )

    return scripts_sobjects


def execute_custom_script(script_path, kwargs=None, project=None,
                          local_execution=True, refresh_scripts=True):
    """Execute a published custom script or an explicit local Python file.

    ``folder/title`` keeps the legacy TACTIC-backed workflow. An existing
    local file path is executed directly and is never refreshed from TACTIC;
    this is the development path for scripts that have not been published.
    """

    if not local_execution:
        return server_start(project).execute_python_script(
            script_path, kwargs=kwargs
        )

    requested_path = os.path.abspath(os.path.expandvars(os.path.expanduser(
        os.fsdecode(script_path)
    )))
    explicit_local_file = os.path.isfile(requested_path)

    if project:
        # Keep the project environment identical to the legacy runner.
        env_inst.set_current_project(project)
        project_obj = env_inst.get_project_by_code(project)
        project_obj.get_stypes()

        if refresh_scripts and not explicit_local_file:
            get_custom_scripts(project=project)

    if explicit_local_file:
        module_path = requested_path
    elif project:
        module_path = u'{0}/custom_scripts/{1}/{2}.py'.format(
            env_mode.get_current_path(), project, script_path
        )
    else:
        module_path = u'{0}/custom_scripts/{1}.py'.format(
            env_mode.get_current_path(), script_path
        )

    with io.open(module_path, 'r', encoding='utf-8') as py_file:
        source_code = py_file.read()

    return env_inst.ui_script_editor.execute_source_code(
        str(source_code)
    )


def insert_sobjects(
        search_type, project_code, data, metadata={}, parent_key=None,
        instance_type=None, info={}, use_id=False, triggers=True,
        instance_path=None):

    kwargs = {
        'search_type': search_type,
        'project_code': project_code,
        'data': data,
        'metadata': metadata,
        'parent_key': parent_key,
        'instance_type': instance_type,
        'info': info,
        'use_id': use_id,
        'triggers': triggers,
        'instance_path': instance_path,
    }

    return execute_procedure_serverside(tq.insert_sobjects, kwargs, project=project_code)

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


def edit_multiple_tasks_sobjects(project_code, parent_keys=None, data=None):
    kwargs = {
        'project_code': project_code,
        'parent_search_keys': list(parent_keys or []),
        'data': dict(data or {}),
    }
    return execute_procedure_serverside(
        tq.edit_multiple_tasks_sobjects, kwargs, project=project_code,
    )


def get_dirs_with_naming(search_key, process_list=None):
    kwargs = {
        'search_key': search_key,
        'process_list': process_list
    }
    project_code = split_search_key(search_key)

    return execute_procedure_serverside(tq.get_dirs_with_naming, kwargs, project=project_code['project_code'])


def get_virtual_snapshot(search_key, context, files_dict, snapshot_type='file', is_revision=False, keep_file_name=False,
                         explicit_filename=None, version=None, checkin_type='file', ignore_keep_file_name=False, progress_signal=None):

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

    # dl.log('Getting Virtual Snapshot', group_id='server/checkin')
    info_dict = {
        'status_text': 'Updating Snapshot Info',
        'total_count': 2
    }
    gf.emit_progress(0, info_dict, progress_signal)

    virtual_snapshot = execute_procedure_serverside(tq.get_virtual_snapshot_extended, kwargs, project=project_code['project_code'], return_dict=True)

    gf.emit_progress(1, info_dict, progress_signal)

    return virtual_snapshot


def checkin_snapshot(search_key, context, snapshot_type=None, is_revision=False, description=None, version=None,
                     update_versionless=True, only_versionless=False, keep_file_name=False, repo_name=None, virtual_snapshot=None,
                     files_dict=None, mode=None, create_icon=False, files_objects=None, progress_signal=None):
    files_info = {
        'version_files': [],
        'version_files_paths': [],
        'versionless_files': [],
        'versionless_files_paths': [],
        'files_types': [],
        'file_sizes': [],
        'upload_file_names': [],
        'version_metadata': [],
        'versionless_metadata': []
    }

    repo = repo_name['value'][0]

    if not (
        len(virtual_snapshot) == len(files_dict) == len(files_objects)
    ):
        raise ValueError(
            'Check-in payload does not match the virtual snapshot'
        )

    for (k1, v1), (k2, v2), file_object in zip(virtual_snapshot, files_dict, files_objects):
        versioned = v1.get('versioned') or {}
        versionless = v1.get('versionless') or {}
        lengths = {
            len(versioned.get('paths') or []),
            len(versioned.get('names') or []),
            len(versionless.get('paths') or []),
            len(versionless.get('names') or []),
            len(v2.get('t') or []),
        }
        if len(lengths) != 1 or not next(iter(lengths)):
            raise ValueError(
                'TACTIC naming returned inconsistent file destinations'
            )
        for path_v, name_v, path_vs, name_vs, tp in zip(v1['versioned']['paths'],
                                                        v1['versioned']['names'],
                                                        v1['versionless']['paths'],
                                                        v1['versionless']['names'],
                                                        v2['t']):
            file_path_v = u'{0}/{1}'.format(repo, path_v)
            file_full_path_v = u'{0}/{1}'.format(file_path_v, ''.join(name_v))
            files_info['version_files'].append(gf.form_path(file_full_path_v, 'linux'))
            files_info['upload_file_names'].append(os.path.basename(
                files_info['version_files'][-1]
            ))
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
        # Every queue operation owns its transaction so a failed or cancelled
        # snapshot cannot roll back unrelated operations in the queue.
        s = gf.time_it()
        # dl.log('Starting Upload Checkin ' + str(server), group_id='server/checkin')
        server.start('Upload Checkin', u'Upload Checkin from Tactic Handler by: {}'.format(env_inst.get_current_login()))
        gf.time_it(s, message='Transaction start: ')

        try:
            for version_file in files_info['version_files']:
                server.upload_file(version_file, progress_signal=progress_signal)

            gf.time_it(s, message='Upload time: ')
            result = execute_procedure_serverside(
                tq.create_snapshot_extended,
                kwargs,
                project=project_code['project_code'],
                return_dict=False,
                server=server,
            )
            gf.time_it(s, message='On Server execution: ')
        except Exception:
            abort = getattr(server, 'abort', None)
            if callable(abort):
                try:
                    abort()
                except Exception as abort_error:
                    dl.exception(
                        abort_error, group_id='exceptions/checkin_abort'
                    )
            raise
        else:
            server.finish(u'Upload Checkin from Tactic Handler by: {}. Finished.'.format(env_inst.get_current_login()))
        gf.time_it(s, message='Transaction End: ')
    elif mode in ['inplace', 'preallocate']:
        server.start('Inplace Checkin', u'Inplace Checkin from Tactic Handler by: {}'.format(env_inst.get_current_login()))
        try:
            result = execute_procedure_serverside(
                tq.create_snapshot_extended,
                kwargs,
                project=project_code['project_code'],
                return_dict=False,
                server=server,
            )
        except Exception:
            abort = getattr(server, 'abort', None)
            if callable(abort):
                try:
                    abort()
                except Exception as abort_error:
                    dl.exception(
                        abort_error, group_id='exceptions/checkin_abort'
                    )
            raise
        else:
            server.finish(u'Inplace Checkin from Tactic Handler by: {}. Finished.'.format(env_inst.get_current_login()))
    else:
        raise ValueError('Unsupported check-in mode: {0}'.format(mode))

    if result:
        if isinstance(result, str):
            if result.startswith('Traceback'):
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


def add_note(search_key, process, context, note, login, attachments=None,
             project_code=None):
    search_type = 'sthpw/note'

    data = {
        'process': process,
        'context': context,
        'note': note,
        'login': login,
    }
    target_project = str(
        project_code or split_search_key(search_key)['project_code'] or ''
    )
    server = server_start(project=target_project)
    transaction = server.insert(
        search_type, data, parent_key=search_key, triggers=True
    )
    if not transaction:
        raise RuntimeError('TACTIC did not create the note')

    if attachments:
        for attachment in attachments:
            server.connect_sobjects(
                attachment, transaction, context='attachment'
            )

    return transaction


def get_all_dependency(search_keys, project_code=None, return_sobjects=True):

    if not project_code:
        project_code = split_search_key(search_keys[0])['project_code']

    result = execute_procedure_serverside(tq.get_all_dependency, {'search_keys': search_keys}, project=project_code)

    if return_sobjects:
        return get_sobjects_objects(result, project_code)
    else:
        return result

def generate_image(image, save_path, scaled=640):
        from thlib.side.Qt import QtCore
        if scaled:
            image = image.scaledToWidth(scaled, QtCore.Qt.SmoothTransformation)

        image.save(save_path)

        return save_path

def generate_web_and_icon(source_image_path, web_save_path=None, icon_save_path=None):
    from thlib.side.Qt import QtCore, QtGui as Qt4Gui

    image = Qt4Gui.QImage(0, 0, Qt4Gui.QImage.Format_ARGB32)

    if not image.load(source_image_path):
        raise ValueError(
            'Unable to decode preview image: {0}'.format(source_image_path)
        )
    if web_save_path:
        web = image.scaledToWidth(640, QtCore.Qt.SmoothTransformation)
        if not web.save(web_save_path):
            raise OSError(
                'Unable to save web preview: {0}'.format(web_save_path)
            )
    if icon_save_path:
        icon = image.scaledToWidth(120, QtCore.Qt.SmoothTransformation)
        if not icon.save(icon_save_path):
            raise OSError(
                'Unable to save icon preview: {0}'.format(icon_save_path)
            )
    return True


def inplace_checkin(file_paths, virtual_snapshot, repo_name, update_versionless, only_versionless=False, generate_icons=True,
                    files_objects=None, padding=None, progress_signal=None):
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
        info_dict = {
            'status_text': key,
            'total_count': len(virtual_snapshot)
        }
        gf.emit_progress(i, info_dict, progress_signal)
        for ver in versions:
            dest_path_vers = repo_name['value'][0] + '/' + val[ver]['paths'][0]
            dest_files_vers = files_objects[i].get_all_new_files_list(val[ver]['names'][0], dest_path_vers, new_frame_padding=padding)

            # create dest dirs
            if not os.path.exists(dest_path_vers):
                os.makedirs(dest_path_vers)

            # copy files to dest dir
            for j, fl in enumerate(file_paths[i]):
                check_ok = copy_file(gf.form_path(dest_files_vers[j]), gf.form_path(fl))
                info_dict = {
                    'status_text': gf.extract_filename(fl),
                    'total_count': len(file_paths[i])
                }
                gf.emit_progress(j, info_dict, progress_signal)

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
        from thlib.side.Qt import QtCore
        commit_queue = env_inst.get_commit_queue('global_commit_queue')
        if not commit_queue:
            raise RuntimeError('No check-in queue is registered')

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

    skey_splitted = urlparse(skey)
    skey_dict = dict(parse_qsl(skey_splitted.query))
    skey_dict['namespace'] = skey_splitted.netloc
    skey_dict['pipeline_code'] = skey_splitted.path[1:]

    if skey_splitted.scheme == 'skey':
        if skey_dict['pipeline_code'] == 'snapshot':
            skey_dict['type'] = 'snapshot'
            identifier = 'code' if skey_dict.get('code') else 'id'
            snapshot = server_start().query(
                'sthpw/snapshot',
                [(identifier, skey_dict.get(identifier))],
            )
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
            identifier = 'code' if skey_dict.get('code') else 'id'
            identifier_value = skey_dict.get(identifier)
            if not identifier_value:
                return skey_dict, None
            filters = [(identifier, '=', identifier_value)]
            search_type = server_start().build_search_type(u'{namespace}/{pipeline_code}'.format(**skey_dict), project_code=skey_dict.get('project'))

            sobjects = get_sobjects(search_type, filters)[0]
            sobject = None
            if sobjects:
                sobject = list(sobjects.values())[0]
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
        sobjects = list(sobjects_dict.values())

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
