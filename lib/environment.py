# module Environment
# file environment.py
# Global constants with defaults

import os
import platform
import ast

import PySide.QtCore as QtCore


def singleton(cls):
    instances = {}

    def get_instance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return get_instance()


@singleton
class Inst(object):
    """
    This class stores all instances of interfaces classes
    """
    offline = False
    projects = None
    current_project = None  # only to see which project dock is active
    ui_super = None
    ui_maya_dock = None
    ui_main = None
    ui_main_tabs = {}
    ui_tasks = None
    ui_notes = None
    ui_conf = None
    ui_check_tree = {
        'checkin': {},
        'checkout': {},
    }
    ui_check_tabs = {}
    ui_addsobject = None


@singleton
class Mode(object):
    """
    Current working environment
    Available modes listed in self.mods
    """
    get = None
    mods = ['maya', 'houdini', '3dsmax', 'nuke', 'standalone']

    def set_mode(self, name):
        if name in self.mods:
            self.get = name


@singleton
class Env(object):
    def __init__(self):
        self.settings = QtCore.QSettings('settings/environment_config.ini', QtCore.QSettings.IniFormat)
        self.platform = platform.system()
        self.defaults = None
        self.rep_dirs = None
        self.get_defaults()

        self.user = None
        self.server = None
        self.ticket = None
        self.data_dir = None
        self.install_dir = None
        # self.types_list = None

    def get_defaults(self):
        self.settings.beginGroup('environment')
        self.defaults = ast.literal_eval(self.settings.value('TACTIC_DEFAULTS', 'None'))
        self.settings.endGroup()

        if self.platform == 'Linux':
            data_dir = '/mnt/drive_d/Alexey/Dropbox/Work/CGProjects/tacticbase_dev/TACTIC-handler'
            install_dir = '/mnt/drive_d/Alexey/Dropbox/Work/CGProjects/tacticbase_dev/TACTIC-handler'
        else:
            data = os.environ.get('TACTIC_DATA_DIR')
            inst = os.environ.get('TACTIC_INSTALL_DIR')

            if data:
                data_dir = str(data).replace('\\', '/')
            else:
                data_dir = None

            if inst:
                install_dir = str(inst).replace('\\', '/')
            else:
                install_dir = None

        if self.defaults is None:
            self.defaults = {
                'user': 'admin',
                # 'pass': 'admin',
                'server': '127.0.0.1:9123',
                'ticket': None,
                'data_dir': data_dir,
                'install_dir': install_dir,
                # 'types_list': ['maya', 'houdini', '3dsmax', 'nuke', ''],
            }
            self.set_defaults()

    def set_defaults(self):
        self.settings.beginGroup('environment')
        self.settings.setValue('TACTIC_DEFAULTS', str(self.defaults))
        print('Done set_defaults settings write')
        self.settings.endGroup()

    def get_default_dirs(self):
        self.settings.beginGroup('environment')
        self.rep_dirs = ast.literal_eval(self.settings.value('TACTIC_DEFAULT_DIRS', 'None'))
        self.settings.endGroup()

        if self.rep_dirs is None:
            import tactic_classes as tc
            # print tc.server_start()
            base_dirs = tc.server_start().get_base_dirs()

            # from pprint import pprint
            # pprint(base_dirs)
            #if os.environ['TACTIC_ASSET_DIR']:
            #    base_dirs['asset_base_dir'] = str(os.environ['TACTIC_ASSET_DIR']).replace('\\', '/')

            if base_dirs.get('win32_local_base_dir'):
                win32_local_dir = 'win32_local_base_dir'
                linux_local_dir = 'linux_local_base_dir'
            else:
                win32_local_dir = 'win32_local_repo_dir'
                linux_local_dir = 'linux_local_repo_dir'

            self.rep_dirs = {
                'asset_base_dir': [base_dirs['asset_base_dir'], 'General', True],
                'web_base_dir': [base_dirs['web_base_dir'], 'Web', False],
                'win32_sandbox_dir': [base_dirs['win32_sandbox_dir'], 'Sandbox', False],
                'linux_sandbox_dir': [base_dirs['linux_sandbox_dir'], 'Sandbox', False],
                'win32_client_repo_dir': [base_dirs['win32_client_repo_dir'], 'Client', False],
                'linux_client_repo_dir': [base_dirs['linux_client_repo_dir'], 'Client', False],
                'win32_local_repo_dir': [base_dirs[win32_local_dir], 'Local', True],
                'linux_local_repo_dir': [base_dirs[linux_local_dir], 'Local', True],
                'win32_client_handoff_dir': [base_dirs['win32_client_handoff_dir'], 'Handoff', False],
                'linux_client_handoff_dir': [base_dirs['linux_client_handoff_dir'], 'Handoff', False],
                'win32_server_handoff_dir': [base_dirs['win32_server_handoff_dir'], 'Handoff', False],
                'linux_server_handoff_dir': [base_dirs['linux_server_handoff_dir'], 'Handoff', False],
                'custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'enabled': False}
            }
            self.set_default_dirs()

    def set_default_dirs(self):
        self.settings.beginGroup('environment')
        self.settings.setValue('TACTIC_DEFAULT_DIRS', str(self.rep_dirs))
        print('Done set_default_dirs settings write')
        self.settings.endGroup()

    def get_user(self):
        if self.user:
            return self.user
        else:
            self.settings.beginGroup('environment')
            self.user = self.settings.value('TACTIC_USER', self.defaults['user'])
            self.settings.endGroup()
            return self.user

    def set_user(self, user_name):
        self.user = user_name
        self.settings.beginGroup('environment')
        self.settings.setValue('TACTIC_USER', user_name)
        print('Done set_user settings write')
        self.settings.endGroup()

    # def get_pass(self):
    #     self.settings.beginGroup('environment')
    #     self.password = self.settings.value('TACTIC_PASS', self.defaults['pass'])
    #     self.settings.endGroup()
    #     return self.password
    #
    # def set_pass(self, pass_name):
    #     self.settings.beginGroup('environment')
    #     self.settings.setValue('TACTIC_PASS', pass_name)
    #     print('Done set_pass settings write')
    #     self.settings.endGroup()

    def get_server(self):
        if self.server:
            return self.server
        else:
            self.settings.beginGroup('environment')
            self.server = self.settings.value('TACTIC_SERVER', self.defaults['server'])
            self.settings.endGroup()
            return self.server

    def set_server(self, server_name):
        self.server = server_name
        self.settings.beginGroup('environment')
        self.settings.setValue('TACTIC_SERVER', server_name)
        print('Done set_server settings write')
        self.settings.endGroup()

    def get_ticket(self):
        if self.ticket:
            return self.ticket
        else:
            self.settings.beginGroup('environment')
            self.ticket = self.settings.value('TACTIC_TICKET', self.defaults['ticket'])
            self.settings.endGroup()
            return self.ticket

    def set_ticket(self, ticket_name):
        self.ticket = ticket_name
        self.settings.beginGroup('environment')
        self.settings.setValue('TACTIC_TICKET', ticket_name)
        print('Done set_ticket settings write')
        self.settings.endGroup()

    def get_data_dir(self):
        if self.data_dir:
            return self.data_dir
        else:
            self.settings.beginGroup('environment')
            self.data_dir = self.settings.value('TACTIC_DATA_DIR', self.defaults['data_dir'])
            self.settings.endGroup()
            return self.data_dir

    def set_data_dir(self, data_dir_name):
        self.data_dir = data_dir_name
        self.settings.beginGroup('environment')
        self.settings.setValue('TACTIC_DATA_DIR', data_dir_name)
        print('Done set_data_dir settings write')
        self.settings.endGroup()

    def get_install_dir(self):
        if self.install_dir:
            return self.install_dir
        else:
            self.settings.beginGroup('environment')
            self.install_dir = self.settings.value('TACTIC_INSTALL_DIR', self.defaults['install_dir'])
            self.settings.endGroup()
            return self.install_dir

    def set_install_dir(self, install_dir_name):
        self.install_dir = install_dir_name
        self.settings.beginGroup('environment')
        self.settings.setValue('TACTIC_INSTALL_DIR', install_dir_name)
        print('Done set_install_dir settings write')
        self.settings.endGroup()

    # def get_types_list(self):
    #     if self.types_list:
    #         return self.types_list
    #     else:
    #         self.settings.beginGroup('environment')
    #         self.types_list = self.settings.value('TACTIC_TYPES_LIST', self.defaults['types_list'])
    #         self.settings.endGroup()
    #         return self.types_list
    #
    # def set_types_list(self, types_list_name):
    #     self.types_list = types_list_name
    #     self.settings.beginGroup('environment')
    #     self.settings.setValue('TACTIC_TYPES_LIST', types_list_name)
    #     print('Done set_types_list settings write')
    #     self.settings.endGroup()
