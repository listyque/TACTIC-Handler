# module Environment
# file environment.py
# Global constants with defaults

import os
import datetime
import inspect
import collections
import platform
import json
from thlib.side.Qt import QtCore

CFG_FORMAT = 'json'  # set this to 'ini' if you want to use QSettings instead of json
SERVER_THREADS_COUNT = 4  # max connections to remote tactic server


def singleton(cls):
    instances = {}

    def get_instance():
        if cls not in instances:
            instances[cls] = cls
        return instances[cls]
    return get_instance()


def get_tc():
    import tactic_classes as tc
    return tc


def env_write_config(obj=None, filename='settings', unique_id='', sub_id=None, update_file=False, long_abs_path=False):
    """
    Converts python objects to json, then writes it to disk.
    Supported writing formats: 'json', 'ini'. Format can be set via global var CFG_FORMAT.
    If ini used, there will be less sub folders created.

    :param obj: any dict, list etc...
    :param filename: name of the file to be written, without ext. 'settings'
    :param unique_id: if format set to json will create sub dirs to ensure uniqueness. 'a/b/c'
    :param sub_id: unique id inside dump. 'abc'
    :param update_file: updates json instead of rewriting
    :param long_abs_path: if set to true path for saving will match current environment paths
    """

    if long_abs_path:
        abs_path = '{0}/settings/{1}/{2}/{3}'.format(
                    env_mode.get_current_path(),
                    env_mode.get_node(),
                    env_server.get_cur_srv_preset(),
                    env_mode.get_mode())
    else:
        abs_path = '{0}/settings'.format(env_mode.get_current_path())

    if CFG_FORMAT == 'json':
        full_abs_path = '{0}/{1}'.format(abs_path, unique_id)
        if not os.path.exists(full_abs_path):
            os.makedirs(full_abs_path)

        full_path = '{0}/{1}.json'.format(full_abs_path, filename)

        obj_from_file = None

        if update_file and sub_id:
            if os.path.exists(full_path):
                with open(full_path, 'r') as json_file:
                    obj_from_file = json.load(json_file)

        if sub_id:
            if obj_from_file:
                obj_from_file[sub_id] = obj
                obj = obj_from_file
            else:
                obj = {sub_id: obj}

        with open(full_path, 'w') as json_file:
            json.dump(obj, json_file, indent=2, separators=(',', ': '))

    elif CFG_FORMAT == 'ini':
        full_path = '{0}/{1}.ini'.format(abs_path, filename)
        settings = QtCore.QSettings(full_path, QtCore.QSettings.IniFormat)
        settings.beginGroup(filename)
        if sub_id:
            settings.beginGroup(sub_id)
        settings.setValue(unique_id, json.dumps(obj, separators=(',', ':')))
        settings.endGroup()


def env_read_config(filename='settings', unique_id='', sub_id=None, long_abs_path=False):
    if long_abs_path:
        abs_path = '{0}/settings/{1}/{2}/{3}'.format(
                    env_mode.get_current_path(),
                    env_mode.get_node(),
                    env_server.get_cur_srv_preset(),
                    env_mode.get_mode())
    else:
        abs_path = '{0}/settings'.format(env_mode.get_current_path())

    if CFG_FORMAT == 'json':
        if unique_id:
            full_path = '{0}/{1}/{2}.json'.format(abs_path, unique_id, filename)
        else:
            full_path = '{0}/{1}.json'.format(abs_path, filename)

        if os.path.exists(full_path):
            with open(full_path, 'r') as json_file:
                obj = json.load(json_file)

            if sub_id:
                return obj.get(sub_id)
            else:
                return obj

    elif CFG_FORMAT == 'ini':
        full_path = '{0}/{1}.ini'.format(abs_path, filename)
        settings = QtCore.QSettings(full_path, QtCore.QSettings.IniFormat)
        settings.beginGroup(filename)

        if sub_id:
            settings.beginGroup(sub_id)

        value = settings.value(unique_id, None)
        settings.endGroup()

        if value:
            obj = json.loads(value)
            return obj


@singleton
class Inst(object):
    """
    This class stores all instances of interfaces classes
    """
    projects = None  # all projects Classes
    current_project = None  # ONLY and ONLY to see which project dock is active
    ui_debuglog = None
    ui_super = None  # maya main window, or standalone main window
    ui_maya_dock = None  # maya docked window
    ui_main = None  # main widget inside dock, or standalone main window
    ui_main_tabs = {}  # tabbed widgets, with check-in/checkout etc.
    ui_tasks = None
    ui_notes = None
    ui_conf = None  # configuration window instance
    check_tree = {}
    control_tabs = {}
    watch_folders = {}
    commit_queue = {}
    thread_pools = {}
    ui_addsobject = None

    def get_current_project(self):
        return self.current_project

    def set_current_project(self, project_code):
        self.current_project = project_code

    def get_current_stypes(self):
        # this is bad practice using this func
        return self.projects.get(self.current_project).stypes

    def get_current_stype_by_code(self, code):
        stypes = self.projects.get(self.current_project).stypes
        return stypes.get(code)

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
            wdg = self.check_tree[project_code].get(tab_code)
            if wdg:
                return wdg.get(wdg_code)
        else:
            return self.check_tree[project_code].get(tab_code)

    def get_watch_folder(self, project_code=None):
        if not project_code:
            project_code = self.current_project
        return self.watch_folders.get(project_code)

    def get_commit_queue(self, project_code=None):
        if not project_code:
            project_code = self.current_project
        return self.commit_queue.get(project_code)

    def set_thread_pool(self, thread_pool, name='main'):
        # first created thread poll will be live until deleted manually
        if not self.thread_pools.get(name):
            self.thread_pools[name] = thread_pool

    def get_thread_pool(self, name='main'):
        return self.thread_pools.get(name)

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
class DebugLog(object):
    """
    This is Debug Log singleton
    """
    info_dict = collections.OrderedDict()
    warning_dict = collections.OrderedDict()
    log_dict = collections.OrderedDict()
    exception_dict = collections.OrderedDict()
    error_dict = collections.OrderedDict()
    critical_dict = collections.OrderedDict()
    logs_order = 0
    print_log = False

    def get_trace(self, message_text, message_type, caller=2, group_id=None):
        """
        Getting trace info from code inspecting
        :param message_text: Useful message in log
        :param message_type: Message type [info, warning, etc..]
        :param caller: getting deeper to stack
        :param group_id: group and subgroup for uniqueness, for ex. 'Group/SubGroup/SubSubGroup'
        :return:
        """
        stack = inspect.stack()

        if stack[caller][0]:
            return (self.logs_order, {
                'datetime': datetime.datetime.today(),
                'unique_id': group_id,
                'message_text': message_text,
                'line_number': int(stack[caller][0].f_lineno),
                'module_path': os.path.basename(stack[caller][0].f_code.co_filename),
                'function_name': stack[caller][0].f_code.co_name,
                'message_type': message_type,
            })

    def info(self, message, caller=2, group_id=None):
        self.logs_order += 1
        trace = self.get_trace(message, 'info', caller, group_id)
        if self.info_dict.get(trace[1]['module_path']):
            self.info_dict[trace[1]['module_path']].append(trace)
        else:
            self.info_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ INF ]', self.print_log)

    def warning(self, message, caller=2, group_id=None):
        self.logs_order += 1
        trace = self.get_trace(message, 'warning', caller, group_id)
        if self.warning_dict.get(trace[1]['module_path']):
            self.warning_dict[trace[1]['module_path']].append(trace)
        else:
            self.warning_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ WRN ]', self.print_log)

    def log(self, message, caller=2, group_id=None):
        self.logs_order += 1
        trace = self.get_trace(message, 'log', caller, group_id)
        if self.log_dict.get(trace[1]['module_path']):
            self.log_dict[trace[1]['module_path']].append(trace)
        else:
            self.log_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ LOG ]', self.print_log)

    def exception(self, message, caller=2, group_id=None):
        self.logs_order += 1
        trace = self.get_trace(message, 'exception', caller, group_id)
        if self.exception_dict.get(trace[1]['module_path']):
            self.exception_dict[trace[1]['module_path']].append(trace)
        else:
            self.exception_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ EXC ]', self.print_log)

    def error(self, message, caller=2, group_id=None):
        self.logs_order += 1
        trace = self.get_trace(message, 'error', caller, group_id)
        if self.error_dict.get(trace[1]['module_path']):
            self.error_dict[trace[1]['module_path']].append(trace)
        else:
            self.error_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ ERR ]', self.print_log)

    def critical(self, message, caller=2, group_id=None):
        self.logs_order += 1
        trace = self.get_trace(message, 'critical', caller, group_id)
        if self.critical_dict.get(trace[1]['module_path']):
            self.critical_dict[trace[1]['module_path']].append(trace)
        else:
            self.critical_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ CRL ]', self.print_log)


dl = DebugLog()


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
        self.current_path = None
        self.get_current_path()
        self.platform = platform.system()
        self.node = platform.node()

    def set_mode(self, mode):
        if mode in self.modes:
            self.current_mode = mode

    def get_mode(self):
        return self.current_mode

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
    default_preset = {
            'user': 'admin',
            'server': '127.0.0.1:9123',
            'ticket': None,
            'site': {'site_name': '', 'enabled': False},
            'proxy': {'login': '', 'pass': '', 'server': '', 'enabled': False},
            'timeout': 20,
            'config_format': 'json',
        }

    def __init__(self):
        self.defaults = None
        self.server_presets_defaults = None
        self.server_presets = None
        self.user = None
        self.site = None
        self.server = None
        self.ticket = None
        self.proxy = None
        self.timeout = None
        self.config_format = None

        self.get_server_presets_defaults()
        self.get_server_presets()

        self.get_defaults()

    def reload(self):
        self.__init__()

    def get_default_preset(self):
        return self.default_preset.copy()

    def save_default_preset(self):
        self.defaults = self.get_default_preset()

    def get_defaults(self):
        unique_id = '{0}/environment_config/server_presets'.format(env_mode.get_node())
        self.defaults = env_read_config(filename=self.get_cur_srv_preset(), unique_id=unique_id)

        if not self.defaults:
            # if default is not exists, so generate new empty config
            self.defaults = self.get_default_preset()
            self.save_defaults(True)

    def save_defaults(self, defaults=False):
        if not defaults:
            self.defaults['user'] = self.user
            self.defaults['server'] = self.server
            self.defaults['ticket'] = self.ticket
            self.defaults['site'] = self.site
            self.defaults['proxy'] = self.proxy
            self.defaults['timeout'] = self.timeout

        unique_id = '{0}/environment_config/server_presets'.format(env_mode.get_node())
        env_write_config(self.defaults, filename=self.get_cur_srv_preset(), unique_id=unique_id)

    def get_proxy(self):
        if self.proxy:
            return self.proxy
        else:
            self.proxy = self.defaults.get('proxy')
            return self.proxy

    def set_proxy(self, proxy_login, proxy_pass, proxy_server, enabled=False):
        proxy = {
            'login': proxy_login,
            'pass': proxy_pass,
            'server': proxy_server,
            'enabled': enabled,
        }
        self.proxy = proxy

    def set_timeout(self, timeout=None):
        self.timeout = timeout

    def get_timeout(self):
        if not self.timeout:
            self.timeout = self.default_preset['timeout']
            return float(self.timeout)
        else:
            return float(self.timeout)

    def get_user(self):
        if self.user:
            return self.user
        else:
            self.user = self.defaults.get('user')
            return self.user

    def set_user(self, user_name):
        self.user = user_name

    def get_site(self):
        if self.site:
            return self.site
        else:
            self.site = self.defaults.get('site')
            return self.site

    def set_site(self, site_name, enabled=False):
        site = {
            'site_name': site_name,
            'enabled': enabled,
        }
        self.site = site

    def get_server(self):
        if self.server:
            return self.server
        else:
            self.server = self.defaults.get('server')
            return self.server

    def set_server(self, server_name):
        self.server = server_name

    def save_server_presets_defaults(self):
        unique_id = '{0}/environment_config'.format(env_mode.get_node())
        env_write_config(self.server_presets_defaults, filename='presets_conf', unique_id=unique_id)

    def get_server_presets_defaults(self):
        unique_id = '{0}/environment_config'.format(env_mode.get_node())
        self.server_presets_defaults = env_read_config(filename='presets_conf', unique_id=unique_id)
        if not self.server_presets_defaults:
            self.server_presets_defaults = {'server_presets': {'presets_list': ['default'], 'current': 'default'}}

    def get_server_presets(self):
        if self.server_presets:
            return self.server_presets
        else:
            self.server_presets = self.server_presets_defaults['server_presets']

    def set_cur_srv_preset(self, current):
        self.server_presets['current'] = current

    def get_cur_srv_preset(self):
        return self.server_presets['current']

    def add_server_preset(self, preset_name, set_current=False):
        self.server_presets['presets_list'].append(preset_name)
        if set_current:
            self.server_presets['current'] = preset_name

    def remove_server_preset(self, preset_name):
        self.server_presets['presets_list'].remove(preset_name)
        self.server_presets['current'] = 'default'

    def get_ticket(self):
        if self.ticket:
            return self.ticket
        else:
            self.ticket = self.defaults.get('ticket')
            return self.ticket

    def set_ticket(self, ticket_name):
        self.ticket = ticket_name

    def get_config_format(self):
        if self.config_format:
            return self.config_format
        else:
            self.config_format = self.defaults.get('config_format')
            return self.config_format

    def set_config_format(self, config_format):
        self.config_format = config_format


env_server = Env()


@singleton
class Tactic(object):

    def __init__(self):

        self.base_dirs = None
        self.default_base_dirs = None

        self.custom_dirs = None

    def query_base_dirs(self):
        import tactic_classes as tc
        default_base_dirs = tc.server_start().get_base_dirs()
        self.default_base_dirs = default_base_dirs

        unique_id = '{0}/environment_config'.format(env_mode.get_node())
        env_write_config(default_base_dirs, filename='tactic_dirs', unique_id=unique_id, sub_id='TACTIC_DEFAULT_DIRS', update_file=True)

        return default_base_dirs

    def get_default_base_dirs(self, force=False):
        if not self.default_base_dirs:

            unique_id = '{0}/environment_config'.format(env_mode.get_node())
            self.default_base_dirs = env_read_config(filename='tactic_dirs', unique_id=unique_id, sub_id='TACTIC_DEFAULT_DIRS')

            if not self.default_base_dirs or force:
                self.default_base_dirs = self.query_base_dirs()
            return self.default_base_dirs
        else:
            return self.default_base_dirs

    def get_base_dirs(self, force=False):
        if not self.base_dirs:

            unique_id = '{0}/environment_config'.format(env_mode.get_node())
            self.base_dirs = env_read_config(filename='tactic_dirs', unique_id=unique_id, sub_id='TACTIC_BASE_DIRS')

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
        unique_id = '{0}/environment_config'.format(env_mode.get_node())
        env_write_config(self.base_dirs, filename='tactic_dirs', unique_id=unique_id, sub_id='TACTIC_BASE_DIRS', update_file=True)

    def get_custom_dir(self):
        if env_mode.get_platform() == 'Linux':
            return {'name': 'linux_custom_asset_dir', 'value': self.custom_dirs['linux_custom_asset_dir']}
        else:
            return {'name': 'win32_custom_asset_dir', 'value': self.custom_dirs['win32_custom_asset_dir']}

    def get_custom_dirs(self):
        unique_id = '{0}/environment_config'.format(env_mode.get_node())
        self.custom_dirs = env_read_config(filename='tactic_dirs', unique_id=unique_id, sub_id='TACTIC_CUSTOM_DIRS')

        if not self.custom_dirs:

            self.custom_dirs = {
                    'linux_custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'color': [], 'enabled': False},
                    'win32_custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'color': [], 'enabled': False},
                }

            unique_id = '{0}/environment_config'.format(env_mode.get_node())
            env_write_config(self.custom_dirs, filename='tactic_dirs', unique_id=unique_id, sub_id='TACTIC_CUSTOM_DIRS', update_file=True)

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

    @staticmethod
    def max_threads():
        return SERVER_THREADS_COUNT


env_tactic = Tactic()


@singleton
class Controls(object):
    def __init__(self):
        self.server = None
        self.project = None
        self.checkin = None
        self.checkout = None
        self.checkin_out = None
        self.checkin_out_projects = None
        self.checkin = None
        self.maya_scene = None

    def get_server(self):
        if self.server:
            return self.server
        else:
            self.server = env_read_config(filename='server', unique_id='ui_conf', long_abs_path=True)
            return self.server

    def set_server(self, server):
        self.server = server
        env_write_config(server, 'server', unique_id='ui_conf', long_abs_path=True)

    def get_project(self):
        if self.project:
            return self.project
        else:
            self.project = env_read_config(filename='project', unique_id='ui_conf', long_abs_path=True)
            return self.project

    def set_project(self, project):
        self.project = project
        env_write_config(project, 'project', unique_id='ui_conf', long_abs_path=True)

    def get_checkin(self):
        if self.checkin:
            return self.checkin
        else:
            self.checkin = env_read_config(filename='checkin', unique_id='ui_conf', long_abs_path=True)
            return self.checkin

    def set_checkin(self, checkin):

        self.checkin = checkin
        env_write_config(filename='checkin', unique_id='ui_conf', obj=checkin, long_abs_path=True)

    def get_checkin_out(self):
        if self.checkin_out:
            return self.checkin_out
        else:
            self.checkin_out = env_read_config(filename='checkin_out', unique_id='ui_conf', long_abs_path=True)
            return self.checkin_out

    def set_checkin_out(self, checkin_out):
        self.checkin_out = checkin_out
        env_write_config(filename='checkin_out', unique_id='ui_conf', obj=checkin_out, long_abs_path=True)

    def get_checkin_out_projects(self):
        if self.checkin_out_projects:
            return self.checkin_out_projects
        else:
            self.checkin_out_projects = env_read_config(filename='checkin_out_projects', unique_id='ui_conf', long_abs_path=True)
            return self.checkin_out_projects

    def set_checkin_out_projects(self, checkin_out_projects):
        self.checkin_out_projects = checkin_out_projects
        env_write_config(filename='checkin_out_projects', unique_id='ui_conf', obj=checkin_out_projects, long_abs_path=True)

    def get_maya_scene(self):
        self.maya_scene = env_read_config(filename='maya_scene', unique_id='ui_conf', long_abs_path=True)
        return self.maya_scene

    def set_maya_scene(self, maya_scene):
        self.maya_scene = maya_scene
        env_write_config(filename='maya_scene', unique_id='ui_conf', obj=maya_scene, long_abs_path=True)


cfg_controls = Controls()
