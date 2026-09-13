# module Environment
# file environment.py
# Global constants with defaults
import sys
import os
import io
import locale
import datetime
import time
import inspect
import collections
import platform
import json
import tempfile
import threading


CFG_FORMAT = 'json'  # set this to 'ini' if you want to use QSettings instead of json
SERVER_THREADS_COUNT = 4  # max connections to remote tactic server (recommended to match number server cores)
HTTP_THREADS_COUNT = 1  # max connections to http (depending on the speed of internet)
LOCAL_THREADS_COUNT = 4  # max local threads (recommended to match number of local machine cores)
SPECIALIZED = 'full'  # can be string, made for personal script packs, e.g. to create pre-configured pack

THREAD_COUNT_MIN = 1
THREAD_COUNT_MAX = 32


_CONFIG_IO_LOCK = threading.RLock()
_CONFIG_REPLACE_RETRY_DELAYS = (0.01, 0.02, 0.04, 0.08, 0.16)


def _write_json_atomic(full_path, obj):
    """Write one JSON document without exposing a partially written file."""
    directory = os.path.dirname(full_path)
    descriptor, temporary_path = tempfile.mkstemp(
        prefix=u'.{0}.'.format(os.path.basename(full_path)),
        suffix=u'.tmp',
        dir=directory,
    )
    try:
        with io.open(descriptor, 'w', encoding='utf-8') as json_file:
            json.dump(
                obj,
                json_file,
                indent=2,
                separators=(',', ': '),
                ensure_ascii=False,
            )
            json_file.flush()
            os.fsync(json_file.fileno())
        for attempt in range(len(_CONFIG_REPLACE_RETRY_DELAYS) + 1):
            try:
                os.replace(temporary_path, full_path)
                break
            except OSError as error:
                # Windows/SMB readers outside our process lock can briefly
                # deny delete-sharing (including WinError 5 on rename).
                # Retry only the completed file's atomic replacement: never
                # truncate the destination or repeat the caller's operation.
                if (
                    getattr(error, 'winerror', None) not in (5, 32, 33)
                    or attempt == len(_CONFIG_REPLACE_RETRY_DELAYS)
                ):
                    raise
                time.sleep(_CONFIG_REPLACE_RETRY_DELAYS[attempt])
    except Exception:
        try:
            os.remove(temporary_path)
        except OSError:
            pass
        raise


def _config_base_path(long_abs_path):
    root = os.path.abspath(env_mode.get_current_path())
    if not long_abs_path:
        return os.path.join(root, 'settings')
    components = (
        env_mode.node,
        env_server.get_cur_srv_preset(),
        env_mode.get_mode(),
    )
    normalized = []
    for component in components:
        value = str(component or '')
        if (
            not value
            or value in ('.', '..')
            or '/' in value
            or '\\' in value
            or os.path.isabs(value)
            or bool(os.path.splitdrive(value)[0])
        ):
            raise ValueError('Invalid config path component: {0!r}'.format(value))
        normalized.append(value)
    return os.path.join(root, 'settings', *normalized)


def _config_directory(abs_path, unique_id):
    value = str(unique_id or '').replace('\\', '/')
    parts = [part for part in value.split('/') if part]
    if any(part in ('.', '..') for part in parts):
        raise ValueError('Config unique_id cannot escape settings: {0!r}'.format(
            unique_id
        ))
    directory = os.path.abspath(os.path.join(abs_path, *parts))
    try:
        contained = os.path.commonpath((os.path.abspath(abs_path), directory))
    except ValueError:
        contained = ''
    if contained != os.path.abspath(abs_path):
        raise ValueError('Config unique_id cannot escape settings: {0!r}'.format(
            unique_id
        ))
    return directory


def _remove_json_documents(directory):
    """Remove owned JSON documents below one validated config directory."""
    if not os.path.isdir(directory):
        return
    for entry in os.scandir(directory):
        if entry.is_dir(follow_symlinks=False):
            _remove_json_documents(entry.path)
            try:
                os.rmdir(entry.path)
            except OSError:
                pass
        elif (
            entry.is_file(follow_symlinks=False)
            and entry.name.endswith('.json')
        ):
            os.remove(entry.path)

def tc():
    import thlib.tactic_classes
    return thlib.tactic_classes


def gf():
    import thlib.global_functions
    return thlib.global_functions


def env_write_config(
        obj=None, filename='settings', unique_id='', sub_id=None,
        update_file=False, long_abs_path=False, remove=False):
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
    :param remove: remove the exact JSON file, or every JSON document below
        the exact ``unique_id`` directory when ``filename`` is empty
    """

    filename = str(filename or '').replace('/', '_').replace('\\', '_')

    abs_path = _config_base_path(long_abs_path)

    if CFG_FORMAT == u'json':
        full_abs_path = _config_directory(abs_path, unique_id)
        if remove:
            if sub_id or update_file:
                raise ValueError(
                    'Config removal does not accept sub_id or update_file'
                )
            with _CONFIG_IO_LOCK:
                if filename:
                    full_path = os.path.join(
                        full_abs_path, u'{0}.json'.format(filename)
                    )
                    try:
                        os.remove(full_path)
                    except FileNotFoundError:
                        pass
                    return
                if not str(unique_id or '').strip():
                    raise ValueError('Refusing to remove the settings root')
                if not os.path.isdir(full_abs_path):
                    return
                _remove_json_documents(full_abs_path)
                try:
                    os.rmdir(full_abs_path)
                except OSError:
                    # The group may contain a nested config scope or a
                    # non-JSON file that this API does not own.
                    pass
                return
        if not os.path.isdir(full_abs_path):
            try:
                os.makedirs(full_abs_path)
            except OSError:
                if not os.path.isdir(full_abs_path):
                    raise

        full_path = os.path.join(full_abs_path, u'{0}.json'.format(filename))

        with _CONFIG_IO_LOCK:
            obj_from_file = None

            if update_file and sub_id and os.path.isfile(full_path):
                try:
                    with io.open(full_path, 'r', encoding='utf-8') as json_file:
                        obj_from_file = json.load(json_file)
                except Exception as expected:
                    dl.exception(expected, group_id='configs')
                    raise

            if sub_id:
                if isinstance(obj_from_file, dict):
                    obj_from_file[sub_id] = obj
                    obj = obj_from_file
                elif obj_from_file is not None:
                    raise TypeError(
                        'Config with sub_id must contain a JSON object: {0}'.format(
                            full_path
                        )
                    )
                else:
                    obj = {sub_id: obj}

            obj_str = obj
            if isinstance(obj, (bytes, bytearray)):
                obj_str = obj.decode('utf-8', errors='ignore')

            _write_json_atomic(full_path, obj_str)

    elif CFG_FORMAT == u'ini':
        if remove:
            raise ValueError('Config removal is only supported for JSON')
        full_path = u'{0}/{1}.ini'.format(abs_path, filename)
        from thlib.side.Qt import QtCore
        settings = QtCore.QSettings(full_path, QtCore.QSettings.IniFormat)
        settings.beginGroup(filename)
        if sub_id:
            settings.beginGroup(sub_id)

        if isinstance(obj, (bytes, bytearray)):
            obj = obj.decode('utf-8', 'ignore')

        settings.setValue(unique_id, json.dumps(obj, separators=(',', ':')))
        settings.endGroup()


def env_read_config(filename='settings', unique_id='', sub_id=None, long_abs_path=False):

    filename = filename.replace('/', '_').replace('\\', '_')

    abs_path = _config_base_path(long_abs_path)

    if CFG_FORMAT == u'json':
        full_path = os.path.join(
            _config_directory(abs_path, unique_id),
            u'{0}.json'.format(filename),
        )

        if os.path.isfile(full_path):
            with _CONFIG_IO_LOCK:
                try:
                    with io.open(full_path, 'r', encoding='utf-8') as json_file:
                        obj = json.load(json_file)
                except Exception as expected:
                    dl.exception(expected, group_id='configs')
                    obj = {}

            if sub_id:
                return obj.get(sub_id)
            else:
                return obj

    elif CFG_FORMAT == u'ini':
        full_path = u'{0}/{1}.ini'.format(abs_path, filename)
        from thlib.side.Qt import QtCore
        settings = QtCore.QSettings(full_path, QtCore.QSettings.IniFormat)
        settings.beginGroup(filename)

        if sub_id:
            settings.beginGroup(sub_id)

        value = settings.value(unique_id, None)
        settings.endGroup()

        if value:
            obj = json.loads(value)
            return obj


def configured_thread_counts():
    settings = env_read_config(
        filename='ui_settings', unique_id='ui_main', long_abs_path=True
    ) or {}

    def count(key, default):
        try:
            value = int(settings.get(key, default))
        except (TypeError, ValueError):
            value = default
        return max(THREAD_COUNT_MIN, min(THREAD_COUNT_MAX, value))

    return {
        'server': count('performance/serverThreads', SERVER_THREADS_COUNT),
        'local': count('performance/localThreads', LOCAL_THREADS_COUNT),
    }


def _file_timestamp(value):
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        parsed = value
    else:
        text = str(value).strip()
        normalized = text[:-1] + '+00:00' if text.endswith(('Z', 'z')) else text
        parsed = datetime.datetime.fromisoformat(normalized)
    return parsed.timestamp()


def env_write_file(data, file_relative_path, file_name, sub_path='',
                   modified_at=None):
    if sub_path:
        relative_path = u'{0}/{1}'.format(sub_path, file_relative_path)
    else:
        relative_path = file_relative_path

    file_path = u'{0}/custom_scripts/{1}'.format(
        env_mode.get_current_path(),
        relative_path
    )

    if not os.path.isdir(file_path):
        os.makedirs(file_path)

    full_path = u'{0}/{1}'.format(file_path, file_name)
    try:
        modified_timestamp = _file_timestamp(modified_at)
    except (TypeError, ValueError):
        modified_timestamp = None
    if modified_timestamp is not None and os.path.isfile(full_path):
        if abs(os.path.getmtime(full_path) - modified_timestamp) < 0.001:
            return False

    with io.open(full_path, 'w+', encoding='utf8') as data_file:
        data_file.write(data)
    if modified_timestamp is not None:
        try:
            os.utime(full_path, (modified_timestamp, modified_timestamp))
        except OSError:
            pass
    return True


class Inst(object):
    """
    This class stores all instances of interfaces classes
    """
    def __init__(self):
        self.projects = None
        self.logins = None
        self.current_project = None
        self.ui_debuglog = None
        self.ui_script_editor = None
        self.ui_messages = None
        self.ui_notify = None
        self.ui_super = None
        self.ui_maya_dock = None
        self.ui_main = None
        self.ui_main_tabs = {}
        self.ui_tasks = None
        self.ui_notes = None
        self.ui_conf = None
        self.ui_repo_sync_queue = None
        self.check_tree = {}
        self.control_tabs = {}
        self.watch_folders = {}
        self.commit_queue = {}
        self.thread_pools = {}
        self._pool_lock = threading.Lock()

    def __getattr__(self, name):
        # Legacy UI pools are constructed only when a UI consumer asks for one.
        counts = configured_thread_counts()
        sizes = {
            'server_pool': counts['server'],
            'commit_pool': counts['server'],
            'local_pool': counts['local'],
        }
        if name not in sizes:
            raise AttributeError(name)
        with self._pool_lock:
            if name not in self.__dict__:
                from thlib.pool import ThreadsPool
                self.__dict__[name] = ThreadsPool(max_threads=sizes[name])
            return self.__dict__[name]

    def set_thread_counts(self, server, local):
        sizes = {
            'server_pool': server,
            'commit_pool': server,
            'local_pool': local,
        }
        for name, size in sizes.items():
            pool = self.__dict__.get(name)
            if pool is not None:
                pool.set_max_threads(size)

    def start_pools(self):
        if self.server_pool.is_stopped:
            self.server_pool.reopen()
            self.server_pool.setParent(self.ui_super)
            self.server_pool.start()

        # if self.http_pool.is_stopped:
            # self.http_pool.setParent(self.ui_super)
            # self.http_pool.start()

        if self.commit_pool.is_stopped:
            self.commit_pool.reopen()
            self.commit_pool.setParent(self.ui_super)
            self.commit_pool.start()

        if self.local_pool.is_stopped:
            self.local_pool.reopen()
            self.local_pool.setParent(self.ui_super)
            self.local_pool.start()

    def exit_pools(self, timeout_ms=15000):
        deadline = time.monotonic() + max(0, int(timeout_ms)) / 1000.0
        completed = True
        for name in ('server_pool', 'commit_pool', 'local_pool'):
            pool = self.__dict__.get(name)
            if pool is None:
                continue
            remaining = max(0, round((deadline - time.monotonic()) * 1000))
            completed = pool.exit(remaining) and completed
        return completed

    def get_current_project(self):
        return self.current_project

    def set_current_project(self, project_code):
        self.current_project = project_code

    def get_project_by_code(self, project_code=None):
        if not project_code:
            project_code = self.current_project

        return self.projects.get(project_code)

    def get_current_login(self):
        return env_server.get_user()

    def get_current_login_object(self):
        return (self.logins or {}).get(env_server.get_user())

    def get_all_logins(self, login_code=None):
        if login_code:
            return self.logins.get(login_code)
        else:
            return self.logins

    def get_stypes(self, project_code='sthpw'):
        return self.projects.get(project_code).stypes

    def get_current_stypes(self):
        # this is bad practice using this func
        return self.projects.get(self.current_project).stypes

    def get_current_stype_by_code(self, code):
        stypes = self.projects.get(self.current_project).get_stypes()
        return stypes.get(code)

    def get_stype_by_code(self, code, project_code='sthpw'):
        if code.startswith('sthpw'):
            stypes = self.projects.get('sthpw').get_stypes()
        else:
            stypes = self.projects.get(project_code).get_stypes()

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

    def cleanup(self, project_code=None):
        if project_code:
            if self.ui_main_tabs.get(project_code):
                del self.ui_main_tabs[project_code]
            if self.check_tree.get(project_code):
                del self.check_tree[project_code]
            if self.control_tabs.get(project_code):
                del self.control_tabs[project_code]


env_inst = Inst()


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
    write_log = True
    session_start = datetime.datetime.today()

    @staticmethod
    def _accepts(message_type):
        ui_debuglog = env_inst.ui_debuglog
        if ui_debuglog and hasattr(ui_debuglog, 'accepts_level'):
            return ui_debuglog.accepts_level(message_type)
        # Before the application diagnostic bus is installed, use the production
        # default as well so bootstrap INFO/API noise cannot grow unbounded.
        return str(message_type or '').upper() in {
            'ERROR', 'CRITICAL'
        }

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
        if not self._accepts('INFO'):
            return
        self.logs_order += 1
        trace = self.get_trace(message, 'info', caller, group_id)
        if self.info_dict.get(trace[1]['module_path']):
            self.info_dict[trace[1]['module_path']].append(trace)
        else:
            self.info_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ INF ]', self.write_log)

    def warning(self, message, caller=2, group_id=None):
        if not self._accepts('WARNING'):
            return
        self.logs_order += 1
        trace = self.get_trace(message, 'warning', caller, group_id)
        if self.warning_dict.get(trace[1]['module_path']):
            self.warning_dict[trace[1]['module_path']].append(trace)
        else:
            self.warning_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ WRN ]', self.write_log)

    def log(self, message, caller=2, group_id=None):
        if not self._accepts('LOG'):
            return
        self.logs_order += 1
        trace = self.get_trace(message, 'log', caller, group_id)
        if self.log_dict.get(trace[1]['module_path']):
            self.log_dict[trace[1]['module_path']].append(trace)
        else:
            self.log_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ LOG ]', self.write_log)

    def exception(self, message, caller=2, group_id=None):
        if not self._accepts('EXCEPTION'):
            return
        self.logs_order += 1
        trace = self.get_trace(message, 'exception', caller, group_id)
        if self.exception_dict.get(trace[1]['module_path']):
            self.exception_dict[trace[1]['module_path']].append(trace)
        else:
            self.exception_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ EXC ]', self.write_log)

    def error(self, message, caller=2, group_id=None):
        if not self._accepts('ERROR'):
            return
        self.logs_order += 1
        trace = self.get_trace(message, 'error', caller, group_id)
        if self.error_dict.get(trace[1]['module_path']):
            self.error_dict[trace[1]['module_path']].append(trace)
        else:
            self.error_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ ERR ]', self.write_log)

    def critical(self, message, caller=2, group_id=None):
        if not self._accepts('CRITICAL'):
            return
        self.logs_order += 1
        trace = self.get_trace(message, 'critical', caller, group_id)
        if self.critical_dict.get(trace[1]['module_path']):
            self.critical_dict[trace[1]['module_path']].append(trace)
        else:
            self.critical_dict[trace[1]['module_path']] = [trace]

        if env_inst.ui_debuglog:
            env_inst.ui_debuglog.add_debuglog(trace, '[ CRL ]', self.write_log)


dl = DebugLog()


class Mode(object):
    """
    Current working environment
    Available modes listed in self.mods
    """
    def __init__(self):
        self.modes = ['maya', 'houdini', '3dsmax', 'nuke', 'standalone', 'api_server']
        self.status = False
        self.current_mode = 'standalone'
        self.current_path = None
        self.current_python_path = None
        self.get_current_path()
        self.platform = platform.system()

    @property
    def node(self):
        if SPECIALIZED:
            return SPECIALIZED
        else:
            return platform.node()

    def set_mode(self, mode):
        if mode in self.modes:
            self.current_mode = mode

    def get_mode(self):
        return self.current_mode

    def set_current_path(self, current_path):
        self.current_path = current_path

    def get_current_path(self):
        if self.current_path:
            if isinstance(self.current_path, str):
                return self.current_path
            else:
                return self.current_path.decode(locale.getpreferredencoding())
        else:
            isolated_path = os.environ.get(
                'TACTIC_QML_TEST_SETTINGS_DIR', ''
            ).strip()
            self.current_path = (
                os.path.abspath(isolated_path)
                if isolated_path
                else os.path.dirname(os.path.split(__file__)[0])
            )
            if isinstance(self.current_path, str):
                return self.current_path
            else:
                return self.current_path.decode(locale.getpreferredencoding())

    def get_current_python_path(self):
        if self.current_python_path:
            return self.current_python_path
        else:
            self.current_python_path = sys.executable
            return self.current_python_path

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
        if self.status is False:
            return True
        else:
            return False


env_mode = Mode()


class Env(object):
    default_preset = {
            'user': 'admin',
            'server': '127.0.0.1:9123',
            'ticket': None,
            'site': {'site_name': '', 'enabled': False},
            'proxy': {'login': '', 'pass': '', 'server': '', 'enabled': False},
            'timeout': 120,
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
        unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
        self.defaults = env_read_config(filename=self.get_cur_srv_preset(), unique_id=unique_id)

        if not self.defaults:
            # if default is not exists, so generate new empty config
            self.defaults = self.get_default_preset()
            self.save_defaults(True)

    def load_current_preset(self, preserve_values=False):
        preserved = None
        if preserve_values:
            preserved = (self.user, self.site, self.proxy)
        self.user = None
        self.site = None
        self.server = None
        self.ticket = None
        self.proxy = None
        self.timeout = None
        self.config_format = None
        self.get_defaults()
        if preserved:
            self.user, self.site, self.proxy = preserved

    def save_defaults(self, defaults=False):
        if not defaults:
            self.defaults['user'] = self.user
            self.defaults['server'] = self.server
            self.defaults['ticket'] = self.ticket
            self.defaults['site'] = self.site
            self.defaults['proxy'] = self.proxy
            self.defaults['timeout'] = self.timeout

        unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
        env_write_config(self.defaults, filename=self.get_cur_srv_preset(), unique_id=unique_id)

    def get_proxy(self):
        configured = self.proxy
        if not isinstance(configured, dict):
            configured = (self.defaults or {}).get('proxy')
        normalized = dict(self.default_preset['proxy'])
        if isinstance(configured, dict):
            normalized.update(configured)
        normalized['login'] = str(normalized.get('login') or '')
        normalized['pass'] = str(normalized.get('pass') or '')
        normalized['server'] = str(normalized.get('server') or '')
        normalized['enabled'] = bool(
            normalized.get('enabled') and normalized['server']
        )
        self.proxy = normalized
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
        configured = self.site
        if not isinstance(configured, dict):
            configured = (self.defaults or {}).get('site')
        normalized = dict(self.default_preset['site'])
        if isinstance(configured, dict):
            normalized.update(configured)
        normalized['site_name'] = str(normalized.get('site_name') or '')
        normalized['enabled'] = bool(
            normalized.get('enabled') and normalized['site_name']
        )
        self.site = normalized
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
        unique_id = '{0}/environment_config'.format(env_mode.node)
        env_write_config(self.server_presets_defaults, filename='presets_conf', unique_id=unique_id)

    def get_server_presets_defaults(self):
        unique_id = '{0}/environment_config'.format(env_mode.node)
        self.server_presets_defaults = env_read_config(filename='presets_conf', unique_id=unique_id)
        if not self.server_presets_defaults:
            self.server_presets_defaults = {'server_presets': {'presets_list': ['default'], 'current': 'default'}}

    def get_server_presets(self):
        if not self.server_presets:
            self.server_presets = self.server_presets_defaults['server_presets']
        return self.server_presets

    @staticmethod
    def get_server_preset(preset_name):
        unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
        return env_read_config(filename=preset_name, unique_id=unique_id)

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


class Tactic(object):

    def __init__(self):

        self.base_dirs = None
        self.default_base_dirs = None

        self.custom_dirs = None

    def reset(self):
        self.base_dirs = None
        self.default_base_dirs = None
        self.custom_dirs = None

    def query_base_dirs(self):
        import thlib.tactic_classes as tc
        default_base_dirs = tc.server_start().get_base_dirs()
        self.default_base_dirs = default_base_dirs

        unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
        tactic_dirs_filename = 'tactic_dirs_{}'.format(env_server.get_cur_srv_preset())
        env_write_config(default_base_dirs, filename=tactic_dirs_filename, unique_id=unique_id, sub_id='TACTIC_DEFAULT_DIRS', update_file=True)

        return default_base_dirs

    def get_default_base_dirs(self, force=False):
        if not self.default_base_dirs or force:

            unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
            tactic_dirs_filename = 'tactic_dirs_{}'.format(env_server.get_cur_srv_preset())
            self.default_base_dirs = env_read_config(filename=tactic_dirs_filename, unique_id=unique_id, sub_id='TACTIC_DEFAULT_DIRS')

            if not self.default_base_dirs:
                self.default_base_dirs = self.query_base_dirs()
            return self.default_base_dirs
        else:
            return self.default_base_dirs

    def get_base_dirs(self, force=False):
        if not self.base_dirs or force:

            unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
            tactic_dirs_filename = 'tactic_dirs_{}'.format(env_server.get_cur_srv_preset())
            self.base_dirs = env_read_config(filename=tactic_dirs_filename, unique_id=unique_id, sub_id='TACTIC_BASE_DIRS')

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
                if not force:
                    # Saving only first time, when forced we just read from configs
                    self.save_base_dirs()

        return self.base_dirs

    def save_base_dirs(self):
        unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
        tactic_dirs_filename = 'tactic_dirs_{}'.format(env_server.get_cur_srv_preset())
        env_write_config(self.base_dirs, filename=tactic_dirs_filename, unique_id=unique_id, sub_id='TACTIC_BASE_DIRS', update_file=True)

    def get_custom_dir(self):
        if env_mode.get_platform() == 'Linux':
            return {'name': 'linux_custom_asset_dir', 'value': self.custom_dirs['linux_custom_asset_dir']}
        else:
            return {'name': 'win32_custom_asset_dir', 'value': self.custom_dirs['win32_custom_asset_dir']}

    def get_custom_dirs(self):
        unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
        tactic_dirs_filename = 'tactic_dirs_{}'.format(env_server.get_cur_srv_preset())
        self.custom_dirs = env_read_config(filename=tactic_dirs_filename, unique_id=unique_id, sub_id='TACTIC_CUSTOM_DIRS')

        if not self.custom_dirs:

            self.custom_dirs = {
                    'linux_custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'color': [], 'enabled': False},
                    'win32_custom_asset_dir': {'path': [], 'name': [], 'current': [], 'visible': [], 'color': [], 'enabled': False},
                }

            unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
            tactic_dirs_filename = 'tactic_dirs_{}'.format(env_server.get_cur_srv_preset())
            env_write_config(self.custom_dirs, filename=tactic_dirs_filename, unique_id=unique_id, sub_id='TACTIC_CUSTOM_DIRS', update_file=True)

        return self.custom_dirs

    def save_custom_dirs(self):
        unique_id = '{0}/environment_config/server_presets'.format(env_mode.node)
        tactic_dirs_filename = 'tactic_dirs_{}'.format(env_server.get_cur_srv_preset())
        env_write_config(
            self.custom_dirs,
            filename=tactic_dirs_filename,
            unique_id=unique_id,
            sub_id='TACTIC_CUSTOM_DIRS',
            update_file=True,
        )

    def get_all_base_dirs(self):
        aliases = ['base', 'client', 'local', 'sandbox']

        all_base_dirs = []

        for alias in aliases:
            all_base_dirs.append((alias, self.get_base_dir(alias)))

        custom = self.get_custom_dir()['value'] if self.custom_dirs else {}
        if custom.get('enabled'):
            paths = list(custom.get('path') or [])
            names = list(custom.get('name') or [])
            visible = list(custom.get('visible') or [])
            colors = list(custom.get('color') or [])
            current = list(custom.get('current') or range(len(paths)))
            for index in current:
                if not 0 <= index < len(paths):
                    continue
                if index < len(visible) and not visible[index]:
                    continue
                alias = 'custom_{0}'.format(index)
                all_base_dirs.append((alias, {
                    'name': alias,
                    'value': [
                        paths[index],
                        names[index] if index < len(names) else alias,
                        colors[index] if index < len(colors) else '',
                        alias,
                        True,
                    ],
                }))

        return all_base_dirs

    def get_base_dir(self, repo_name, override_base_dirs=None):

        base_dirs = self.base_dirs
        if override_base_dirs:
            base_dirs = override_base_dirs

        if repo_name in 'base':
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

        elif str(repo_name).startswith('custom_'):
            try:
                index = int(str(repo_name).split('_', 1)[1])
            except (TypeError, ValueError):
                return None
            custom = self.get_custom_dir()['value']
            paths = list(custom.get('path') or [])
            if not 0 <= index < len(paths):
                return None
            names = list(custom.get('name') or [])
            colors = list(custom.get('color') or [])
            visible = list(custom.get('visible') or [])
            active = bool(custom.get('enabled')) and (
                index >= len(visible) or bool(visible[index])
            )
            alias = 'custom_{0}'.format(index)
            return {
                'name': alias,
                'value': [
                    paths[index],
                    names[index] if index < len(names) else alias,
                    colors[index] if index < len(colors) else '',
                    alias,
                    active,
                ],
            }

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

    def get_current_repo(self, value=None):

        from thlib.global_functions import get_value_from_config

        base_dirs = self.get_all_base_dirs()

        active_repos = []

        for _key, val in base_dirs:
            values = val.get('value') or []
            if len(values) > 4 and values[4]:
                active_repos.append(val)

        if not active_repos:
            return None

        try:
            current_repo = int(get_value_from_config(
                cfg_controls.get_checkin(), 'repositoryComboBox'
            ))
        except (TypeError, ValueError):
            current_repo = 0
        if not 0 <= current_repo < len(active_repos):
            current_repo = 0

        repository = active_repos[current_repo]
        values = repository['value']
        if value == 'path':
            return values[0]
        elif value == 'title':
            return values[1]
        elif value == 'color':
            return values[2]
        elif value == 'name':
            return values[3]
        elif value == 'active':
            return values[4]
        elif value == 'base_name':
            return repository['name']
        return repository


    @staticmethod
    def max_threads(type='xmlrpc'):
        if type == 'xmlrpc':
            return configured_thread_counts()['server']
        elif type == 'http':
            return HTTP_THREADS_COUNT


env_tactic = Tactic()


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

    def reset(self):
        self.server = None
        self.project = None
        self.checkin = None
        self.checkout = None
        self.checkin_out = None
        self.checkin_out_projects = None
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

    def set_checkin_out_projects(self, checkin_out_projects, persist=True):
        self.checkin_out_projects = checkin_out_projects
        if persist:
            env_write_config(filename='checkin_out_projects', unique_id='ui_conf', obj=checkin_out_projects, long_abs_path=True)

    def get_maya_scene(self):
        self.maya_scene = env_read_config(filename='maya_scene', unique_id='ui_conf', long_abs_path=True)
        return self.maya_scene

    def set_maya_scene(self, maya_scene):
        self.maya_scene = maya_scene
        env_write_config(filename='maya_scene', unique_id='ui_conf', obj=maya_scene, long_abs_path=True)


cfg_controls = Controls()
