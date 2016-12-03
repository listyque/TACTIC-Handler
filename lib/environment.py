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
            instances[cls] = cls
        return instances[cls]
    return get_instance()


@singleton
class Inst(object):
    """
    This class stores all instances of interfaces classes
    """
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

env_inst = Inst()


@singleton
class Mode(object):
    """
    Current working environment
    Available modes listed in self.mods
    """
    def __init__(self):
        self.modes = ['maya', 'houdini', '3dsmax', 'nuke', 'standalone']
        self.status = False

        self.current_mode = 'standalone'
        self.current_project = 'sthpw'
        self.current_path = None
        self.get_current_path()
        self.platform = platform.system()
        self.node = platform.node()

    def set_mode(self, mode):
        if mode in self.modes:
            self.current_mode = mode

    def get_mode(self):
        return self.current_mode

    def set_current_project(self, project_code):
        self.current_project = project_code

    def get_current_project(self):
        return self.current_project

    def set_current_path(self, current_path):
        self.current_path = current_path

    def get_current_path(self):
        if self.current_path:
            return self.current_path
        else:
            self.current_path = os.path.dirname(os.path.split(__file__)[0])
            return self.current_path

    def get_platform(self):
        return self.platform

    def get_node(self):
        return self.node

    def set_online(self):
        self.status = True
        # if we online, lets get defaults, from server
        env_tactic.get_base_dirs()
        env_tactic.get_custom_dirs()

    def set_offline(self):
        self.status = False

    def is_online(self):
        if self.status:
            return True
        else:
            return False

    def is_offline(self):
        if self.status:
            return False
        else:
            return True


env_mode = Mode()


@singleton
class Env(object):
    def __init__(self):
        self.settings = QtCore.QSettings('{0}/settings/environment_config.ini'.format(env_mode.get_current_path()), QtCore.QSettings.IniFormat)
        self.defaults = None
        self.get_defaults()

        self.server_presets = None
        self.get_server_presets()

        self.user = None
        self.site = None
        self.server = None
        self.ticket = None
        self.proxy = None

    def get_defaults(self):
        self.settings.beginGroup(env_mode.get_node() + '/server_environment')
        self.defaults = ast.literal_eval(self.settings.value('TACTIC_DEFAULTS', 'None'))
        self.settings.endGroup()

        if self.defaults is None:
            self.defaults = {
                'user': 'admin',
                'server': '127.0.0.1:9123',
                'ticket': None,
                'site': {'site_name': '', 'enabled': False},
                'proxy': {'login': '', 'pass': '', 'server': '', 'enabled': False},
                'server_presets': {'presets_list': ['default'], 'current_idx': 0},
            }
            self.set_defaults()

    def set_defaults(self):
        self.settings.beginGroup(env_mode.get_node() + '/server_environment')
        self.settings.setValue('TACTIC_DEFAULTS', str(self.defaults))
        print('Done set_defaults settings write')
        self.settings.endGroup()

    def get_proxy(self):
        if self.proxy:
            return self.proxy
        else:
            self.settings.beginGroup(env_mode.get_node() + '/server_environment')
            self.proxy = ast.literal_eval(self.settings.value('TACTIC_PROXY', str(self.defaults['proxy'])))
            self.settings.endGroup()
            return self.proxy

    def set_proxy(self, proxy_login, proxy_pass, proxy_server, enabled=False):
        proxy = {
            'login': proxy_login,
            'pass': proxy_pass,
            'server': proxy_server,
            'enabled': enabled,
        }
        self.proxy = proxy
        self.settings.beginGroup(env_mode.get_node() + '/server_environment')
        self.settings.setValue('TACTIC_PROXY', str(self.proxy))
        print('Done set_proxy settings write')
        self.settings.endGroup()

    def get_user(self):
        if self.user:
            return self.user
        else:
            self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
            self.user = self.settings.value('TACTIC_USER', self.defaults['user'])
            self.settings.endGroup()
            return self.user

    def set_user(self, user_name):
        self.user = user_name
        self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
        self.settings.setValue('TACTIC_USER', user_name)
        print('Done set_user settings write')
        self.settings.endGroup()

    def get_site(self):
        if self.site:
            return self.site
        else:
            self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
            self.site = ast.literal_eval(self.settings.value('TACTIC_SITE', str(self.defaults['site'])))
            self.settings.endGroup()
            return self.site

    def set_site(self, site_name, enabled=False):
        site = {
            'site_name': site_name,
            'enabled': enabled,
        }
        self.site = site
        self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
        self.settings.setValue('TACTIC_SITE', str(self.site))
        print('Done set_site settings write')
        self.settings.endGroup()

    def get_server(self):
        if self.server:
            return self.server
        else:
            self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
            self.server = self.settings.value('TACTIC_SERVER', self.defaults['server'])
            self.settings.endGroup()
            return self.server

    def set_server(self, server_name):
        self.server = server_name
        self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
        self.settings.setValue('TACTIC_SERVER', server_name)
        print('Done set_server settings write')
        self.settings.endGroup()

    def get_server_presets(self):
        if self.server_presets:
            return self.server_presets
        else:
            self.settings.beginGroup(env_mode.get_node() + '/server_environment')
            self.server_presets = ast.literal_eval(self.settings.value('SERVER_PRESETS', str(self.defaults['server_presets'])))
            self.settings.endGroup()
            return self.server_presets

    def set_server_presets(self, presets_list, current_idx):
        server_presets = {
            'presets_list': presets_list,
            'current_idx': current_idx,
        }
        self.server_presets = server_presets

        self.settings.beginGroup(env_mode.get_node() + '/server_environment')
        self.settings.setValue('SERVER_PRESETS', str(server_presets))
        print('Done set_server_presets settings write')
        self.settings.endGroup()

    def set_cur_srv_preset(self, current_idx):
        self.set_server_presets(self.server_presets['presets_list'], current_idx)

    def get_cur_srv_preset(self):
        idx = int(self.server_presets['current_idx'])
        current_server_preset = self.server_presets['presets_list'][idx]
        return current_server_preset

    def get_ticket(self):
        if self.ticket:
            return self.ticket
        else:
            self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
            self.ticket = self.settings.value('TACTIC_TICKET', self.defaults['ticket'])
            self.settings.endGroup()
            return self.ticket

    def set_ticket(self, ticket_name):
        self.ticket = ticket_name
        self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
        self.settings.setValue('TACTIC_TICKET', ticket_name)
        print('Done set_ticket settings write')
        self.settings.endGroup()

env_server = Env()


@singleton
class Tactic(object):

    def __init__(self):
        self.settings = QtCore.QSettings('{0}/settings/environment_config.ini'.format(env_mode.get_current_path()), QtCore.QSettings.IniFormat)

        self.base_dirs = None
        self.default_base_dirs = None

        self.custom_dirs = None

    def query_base_dirs(self):
        import tactic_classes as tc
        default_base_dirs = tc.server_start().get_base_dirs()
        self.default_base_dirs = default_base_dirs
        self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
        self.settings.setValue('TACTIC_DEFAULT_DIRS', str(default_base_dirs))
        self.settings.endGroup()
        return default_base_dirs

    def get_default_base_dirs(self, force=False):
        if not self.default_base_dirs:
            self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
            self.default_base_dirs = ast.literal_eval(self.settings.value('TACTIC_DEFAULT_DIRS', 'None'))
            self.settings.endGroup()
            if not self.default_base_dirs or force:
                self.default_base_dirs = self.query_base_dirs()
            return self.default_base_dirs
        else:
            return self.default_base_dirs

    def get_base_dirs(self, force=False):
        if not self.base_dirs:
            self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
            self.base_dirs = ast.literal_eval(self.settings.value('TACTIC_BASE_DIRS', 'None'))
            self.settings.endGroup()

            if not self.base_dirs or force:
                base_dirs = self.get_default_base_dirs(force)

                if base_dirs.get('win32_local_base_dir'):
                    win32_local_dir = 'win32_local_base_dir'
                    linux_local_dir = 'linux_local_base_dir'
                else:
                    win32_local_dir = 'win32_local_repo_dir'
                    linux_local_dir = 'linux_local_repo_dir'

                self.base_dirs = {
                        'asset_base_dir': [base_dirs['asset_base_dir'], 'General', 'rgb(128,128,128)', 'base', True],
                        'web_base_dir': [base_dirs['web_base_dir'], 'Web', 'rgb(128,128,128)', 'web', False],
                        'win32_sandbox_dir': [base_dirs['win32_sandbox_dir'], 'Sandbox', 'rgb(128,128,128)', 'sandbox', False],
                        'linux_sandbox_dir': [base_dirs['linux_sandbox_dir'], 'Sandbox', 'rgb(128,128,128)', 'sandbox', False],
                        'win32_client_repo_dir': [base_dirs['win32_client_repo_dir'], 'Client', 'rgb(128,128,128)', 'client', False],
                        'linux_client_repo_dir': [base_dirs['linux_client_repo_dir'], 'Client', 'rgb(128,128,128)', 'client', False],
                        'win32_local_repo_dir': [base_dirs[win32_local_dir], 'Local', 'rgb(128,128,128)', 'local', True],
                        'linux_local_repo_dir': [base_dirs[linux_local_dir], 'Local', 'rgb(128,128,128)', 'local', True],
                        'win32_client_handoff_dir': [base_dirs['win32_client_handoff_dir'], 'Handoff', '', 'client_handoff', False],
                        'linux_client_handoff_dir': [base_dirs['linux_client_handoff_dir'], 'Handoff', '', 'client_handoff', False],
                        'win32_server_handoff_dir': [base_dirs['win32_server_handoff_dir'], 'Handoff', '', 'server_handoff', False],
                        'linux_server_handoff_dir': [base_dirs['linux_server_handoff_dir'], 'Handoff', '', 'server_handoff', False],
                    }

                self.save_base_dirs()

        return self.base_dirs

    def save_base_dirs(self):
        self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
        self.settings.setValue('TACTIC_BASE_DIRS', str(self.base_dirs))
        self.settings.endGroup()

    def get_custom_dir(self):
        if env_mode.get_platform() == 'Linux':
            return {'name': 'linux_custom_asset_dir', 'value': self.custom_dirs['linux_custom_asset_dir']}
        else:
            return {'name': 'win32_custom_asset_dir', 'value': self.custom_dirs['win32_custom_asset_dir']}

    def get_custom_dirs(self):
        self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
        self.custom_dirs = ast.literal_eval(self.settings.value('TACTIC_CUSTOM_DIRS', 'None'))
        self.settings.endGroup()

        if not self.custom_dirs:

            self.custom_dirs = {
                    'linux_custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'color': [], 'enabled': False},
                    'win32_custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'color': [], 'enabled': False},
                }

            self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
            self.settings.setValue('TACTIC_CUSTOM_DIRS', str(self.custom_dirs))
            self.settings.endGroup()

        return self.custom_dirs

    def get_all_base_dirs(self):
        aliases = ['base', 'client', 'local', 'sandbox']

        all_base_dirs = []

        for alias in aliases:
            all_base_dirs.append((alias, self.get_base_dir(alias)))

        return all_base_dirs

    def get_base_dir(self, repo_name):
        if repo_name == 'base':
            return {'name': 'asset_base_dir', 'value': self.base_dirs['asset_base_dir']}

        if repo_name == 'web':
            return {'name': 'web_base_dir', 'value': self.base_dirs['web_base_dir']}

        if repo_name == 'sandbox':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_sandbox_dir', 'value': self.base_dirs['linux_sandbox_dir']}
            else:
                return {'name': 'win32_sandbox_dir', 'value': self.base_dirs['win32_sandbox_dir']}

        if repo_name == 'client':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_client_repo_dir', 'value': self.base_dirs['linux_client_repo_dir']}
            else:
                return {'name': 'win32_client_repo_dir', 'value': self.base_dirs['win32_client_repo_dir']}

        if repo_name == 'local':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_local_repo_dir', 'value': self.base_dirs['linux_local_repo_dir']}
            else:
                return {'name': 'win32_local_repo_dir', 'value': self.base_dirs['win32_local_repo_dir']}

        if repo_name == 'client_handoff':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_client_handoff_dir', 'value': self.base_dirs['linux_client_handoff_dir']}
            else:
                return {'name': 'win32_client_handoff_dir', 'value': self.base_dirs['win32_client_handoff_dir']}

        if repo_name == 'server_handoff':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_server_handoff_dir', 'value': self.base_dirs['linux_server_handoff_dir']}
            else:
                return {'name': 'win32_server_handoff_dir', 'value': self.base_dirs['win32_server_handoff_dir']}

    def set_base_dir(self, repo_name, value):
        if repo_name == 'base':
            self.base_dirs['asset_base_dir'] = value

        if repo_name == 'web':
            self.base_dirs['web_base_dir'] = value

        if repo_name == 'sandbox':
            if env_mode.get_platform() == 'Linux':
                self.base_dirs['linux_sandbox_dir'] = value
            else:
                self.base_dirs['win32_sandbox_dir'] = value

        if repo_name == 'client':
            if env_mode.get_platform() == 'Linux':
                self.base_dirs['linux_client_repo_dir'] = value
            else:
                self.base_dirs['win32_client_repo_dir'] = value

        if repo_name == 'local':
            if env_mode.get_platform() == 'Linux':
                self.base_dirs['linux_local_repo_dir'] = value
            else:
                self.base_dirs['win32_local_repo_dir'] = value

        if repo_name == 'client_handoff':
            if env_mode.get_platform() == 'Linux':
                self.base_dirs['linux_client_handoff_dir'] = value
            else:
                self.base_dirs['win32_client_handoff_dir'] = value

        if repo_name == 'server_handoff':
            if env_mode.get_platform() == 'Linux':
                self.base_dirs['linux_server_handoff_dir'] = value
            else:
                self.base_dirs['win32_server_handoff_dir'] = value


# print 'getting tactic env'
env_tactic = Tactic()
# print env_tactic.get_base_dirs()
# print 'getting tactic env done'
