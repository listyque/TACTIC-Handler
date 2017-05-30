# module Environment
# file environment.py
# Global constants with defaults

import os
import platform
import json

from lib.side.Qt import QtCore

# import PySide.QtCore as QtCore


def singleton(cls):
    instances = {}

    def get_instance():
        if cls not in instances:
            instances[cls] = cls
        return instances[cls]
    return get_instance()


def to_json(obj, pretty=False):
    indent = None
    separators = (',', ':')
    if pretty:
        indent = 4
        separators = (', ', ': ')
    return json.dumps(obj, indent=indent, separators=separators)


def from_json(obj):
    if obj:
        return json.loads(obj)


@singleton
class Inst(object):
    """
    This class stores all instances of interfaces classes
    """
    projects = None  # all projects Classes
    current_project = None  # ONLY and ONLY to see which project dock is active
    ui_super = None  # maya main window, or standalone main window
    ui_maya_dock = None  # maya docked window
    ui_main = None  # main widget inside dock, or standalone main window
    ui_main_tabs = {}  # tabbed widgets, with check-in, checkout etc.
    ui_tasks = None
    ui_notes = None
    ui_conf = None  # configuration window instance
    check_tree = {}
    control_tabs = {}
    ui_addsobject = None

    def get_current_project(self):
        return self.current_project

    def get_current_stypes(self):
        return self.projects.get(self.current_project).stypes

    def get_current_stype_by_code(self, code):
        stypes = self.projects.get(self.current_project).stypes
        return stypes.get(code)

    def set_current_project(self, project_code):
        self.current_project = project_code

    def set_control_tab(self, project_code, tab_code, tab_widget):
        if not self.control_tabs.get(project_code):
            self.control_tabs[project_code] = {}

        self.control_tabs[project_code][tab_code] = tab_widget

    def get_control_tab(self, project_code=None, tab_code=None):
        if not project_code:
            project_code = self.current_project

        all_tabs = self.control_tabs.get(project_code)
        if tab_code and all_tabs:
            return all_tabs.get(tab_code)
        else:
            return all_tabs

    def set_check_tree(self, project_code, tab_code, wdg_code, widget):
        if not self.check_tree.get(project_code):
            self.check_tree[project_code] = {}

        if not self.check_tree[project_code].get(tab_code):
            self.check_tree[project_code][tab_code] = {}

        self.check_tree[project_code][tab_code][wdg_code] = widget

    def get_check_tree(self, project_code=None, tab_code=None, wdg_code=None):
        if not project_code:
            project_code = self.current_project
        if wdg_code:
            return self.check_tree[project_code][tab_code][wdg_code]
        else:
            return self.check_tree[project_code][tab_code]

    def cleanup(self, project_code=None):
        if project_code:
            if self.ui_main_tabs.get(project_code):
                del self.ui_main_tabs[project_code]
            if self.check_tree.get(project_code):
                del self.check_tree[project_code]
            if self.control_tabs.get(project_code):
                del self.control_tabs[project_code]

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
        self.defaults = from_json(self.settings.value('TACTIC_DEFAULTS', 'null'))
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
        self.settings.setValue('TACTIC_DEFAULTS', to_json(self.defaults))
        print('Done set_defaults settings write')
        self.settings.endGroup()

    def get_proxy(self):
        if self.proxy:
            return self.proxy
        else:
            self.settings.beginGroup(env_mode.get_node() + '/server_environment')
            self.proxy = from_json(self.settings.value('TACTIC_PROXY', to_json(self.defaults['proxy'])))
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
        self.settings.setValue('TACTIC_PROXY', to_json(self.proxy))
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
            self.site = from_json(self.settings.value('TACTIC_SITE', to_json(self.defaults['site'])))
            self.settings.endGroup()
            return self.site

    def set_site(self, site_name, enabled=False):
        site = {
            'site_name': site_name,
            'enabled': enabled,
        }
        self.site = site
        self.settings.beginGroup(env_mode.get_node() + '/server_environment/' + self.get_cur_srv_preset())
        self.settings.setValue('TACTIC_SITE', to_json(self.site))
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
            self.server_presets = from_json(self.settings.value('SERVER_PRESETS', to_json(self.defaults['server_presets'])))
            self.settings.endGroup()
            return self.server_presets

    def set_server_presets(self, presets_list, current_idx):
        server_presets = {
            'presets_list': presets_list,
            'current_idx': current_idx,
        }
        self.server_presets = server_presets

        self.settings.beginGroup(env_mode.get_node() + '/server_environment')
        self.settings.setValue('SERVER_PRESETS', to_json(server_presets))
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
            self.default_base_dirs = json.loads(self.settings.value('TACTIC_DEFAULT_DIRS', 'null'))
            self.settings.endGroup()
            if not self.default_base_dirs or force:
                self.default_base_dirs = self.query_base_dirs()
            return self.default_base_dirs
        else:
            return self.default_base_dirs

    def get_base_dirs(self, force=False):
        if not self.base_dirs:
            self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
            self.base_dirs = from_json(self.settings.value('TACTIC_BASE_DIRS', 'null'))
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
                        'asset_base_dir': [base_dirs['asset_base_dir'], 'General', (128, 128, 128), 'base', True],
                        'web_base_dir': [base_dirs['web_base_dir'], 'Web', (128, 128, 128), 'web', False],
                        'win32_sandbox_dir': [base_dirs['win32_sandbox_dir'], 'Sandbox', (128, 64, 64), 'sandbox', False],
                        'linux_sandbox_dir': [base_dirs['linux_sandbox_dir'], 'Sandbox', (128, 64, 64), 'sandbox', False],
                        'win32_client_repo_dir': [base_dirs['win32_client_repo_dir'], 'Client', (31, 143, 0), 'client', False],
                        'linux_client_repo_dir': [base_dirs['linux_client_repo_dir'], 'Client', (31, 143, 0), 'client', False],
                        'win32_local_repo_dir': [base_dirs[win32_local_dir], 'Local', (255, 140, 40), 'local', True],
                        'linux_local_repo_dir': [base_dirs[linux_local_dir], 'Local', (255, 140, 40), 'local', True],
                        'win32_client_handoff_dir': [base_dirs['win32_client_handoff_dir'], 'Handoff', '', 'client_handoff', False],
                        'linux_client_handoff_dir': [base_dirs['linux_client_handoff_dir'], 'Handoff', '', 'client_handoff', False],
                        'win32_server_handoff_dir': [base_dirs['win32_server_handoff_dir'], 'Handoff', '', 'server_handoff', False],
                        'linux_server_handoff_dir': [base_dirs['linux_server_handoff_dir'], 'Handoff', '', 'server_handoff', False],
                    }

                self.save_base_dirs()

        return self.base_dirs

    def save_base_dirs(self):
        self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
        self.settings.setValue('TACTIC_BASE_DIRS', to_json(self.base_dirs))
        self.settings.endGroup()

    def get_custom_dir(self):
        if env_mode.get_platform() == 'Linux':
            return {'name': 'linux_custom_asset_dir', 'value': self.custom_dirs['linux_custom_asset_dir']}
        else:
            return {'name': 'win32_custom_asset_dir', 'value': self.custom_dirs['win32_custom_asset_dir']}

    def get_custom_dirs(self):
        self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
        self.custom_dirs = from_json(self.settings.value('TACTIC_CUSTOM_DIRS', 'null'))
        self.settings.endGroup()

        if not self.custom_dirs:

            self.custom_dirs = {
                    'linux_custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'color': [], 'enabled': False},
                    'win32_custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'color': [], 'enabled': False},
                }

            self.settings.beginGroup(env_mode.get_node() + '/tactic_environment')
            self.settings.setValue('TACTIC_CUSTOM_DIRS', to_json(self.custom_dirs))
            self.settings.endGroup()

        return self.custom_dirs

    def get_all_base_dirs(self):
        aliases = ['base', 'client', 'local', 'sandbox']

        all_base_dirs = []

        for alias in aliases:
            all_base_dirs.append((alias, self.get_base_dir(alias)))

        return all_base_dirs

    def get_base_dir(self, repo_name, override_base_dirs=None):

        base_dirs = self.base_dirs
        if override_base_dirs:
            base_dirs = override_base_dirs

        if repo_name == 'base':
            return {'name': 'asset_base_dir', 'value': base_dirs['asset_base_dir']}

        elif repo_name == 'web':
            return {'name': 'web_base_dir', 'value': base_dirs['web_base_dir']}

        elif repo_name == 'sandbox':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_sandbox_dir', 'value': base_dirs['linux_sandbox_dir']}
            else:
                return {'name': 'win32_sandbox_dir', 'value': base_dirs['win32_sandbox_dir']}

        elif repo_name == 'client':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_client_repo_dir', 'value': base_dirs['linux_client_repo_dir']}
            else:
                return {'name': 'win32_client_repo_dir', 'value': base_dirs['win32_client_repo_dir']}

        elif repo_name == 'local':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_local_repo_dir', 'value': base_dirs['linux_local_repo_dir']}
            else:
                return {'name': 'win32_local_repo_dir', 'value': base_dirs['win32_local_repo_dir']}

        elif repo_name == 'client_handoff':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_client_handoff_dir', 'value': base_dirs['linux_client_handoff_dir']}
            else:
                return {'name': 'win32_client_handoff_dir', 'value': base_dirs['win32_client_handoff_dir']}

        elif repo_name == 'server_handoff':
            if env_mode.get_platform() == 'Linux':
                return {'name': 'linux_server_handoff_dir', 'value': base_dirs['linux_server_handoff_dir']}
            else:
                return {'name': 'win32_server_handoff_dir', 'value': base_dirs['win32_server_handoff_dir']}

    def set_base_dir(self, repo_name, value, override_base_dirs=None):

        base_dirs = self.base_dirs
        if override_base_dirs:
            base_dirs = override_base_dirs

        if repo_name == 'base':
            base_dirs['asset_base_dir'] = value

        elif repo_name == 'web':
            base_dirs['web_base_dir'] = value

        elif repo_name == 'sandbox':
            if env_mode.get_platform() == 'Linux':
                base_dirs['linux_sandbox_dir'] = value
            else:
                base_dirs['win32_sandbox_dir'] = value

        elif repo_name == 'client':
            if env_mode.get_platform() == 'Linux':
                base_dirs['linux_client_repo_dir'] = value
            else:
                base_dirs['win32_client_repo_dir'] = value

        elif repo_name == 'local':
            if env_mode.get_platform() == 'Linux':
                base_dirs['linux_local_repo_dir'] = value
            else:
                base_dirs['win32_local_repo_dir'] = value

        elif repo_name == 'client_handoff':
            if env_mode.get_platform() == 'Linux':
                base_dirs['linux_client_handoff_dir'] = value
            else:
                base_dirs['win32_client_handoff_dir'] = value

        elif repo_name == 'server_handoff':
            if env_mode.get_platform() == 'Linux':
                base_dirs['linux_server_handoff_dir'] = value
            else:
                base_dirs['win32_server_handoff_dir'] = value


# print 'getting tactic env'
env_tactic = Tactic()
# print env_tactic.get_base_dirs()
# print 'getting tactic env done'
