# file global_functions.py
# Global Functions Module

import sys
import os
import time
from stat import ST_SIZE
import subprocess
import copy
import ast
import json
import zlib
import zipfile
import binascii
import collections
import re
import traceback
import datetime
#from thlib.side.Qt import QtNetwork
from thlib.color_hash import color_hash
from thlib.time_presentation import get_full_datetime, get_pretty_datetime
from thlib.side.watchdog.observers import Observer

from thlib.environment import env_mode, env_tactic, dl


def __getattr__(name):
    if name == 'EventHandler':
        from thlib.filesystem_signals import EventHandler
        return EventHandler
    raise AttributeError(name)


class FSObserver(Observer):

    def __init__(self, timeout=1):
        super(self.__class__, self).__init__(timeout=timeout)

        from thlib.filesystem_signals import EventHandler
        self.event_handler = EventHandler()
        self.started = False

        self.observers_dict = {}

    def set_created_signal(self, func):
        self.event_handler.created.connect(func)

    def append_watch(self, watch_name, paths=None, repos=None, pipeline=None, recursive=None):

        if watch_name not in list(self.observers_dict.keys()):

            for i, path in enumerate(paths):
                watch = self.schedule(self.event_handler, path=path, recursive=recursive)
                watch.watch_name = watch_name
                watch.repo = repos[i]
                watch.pipeline = pipeline
                self.observers_dict.setdefault(watch_name, []).append(watch)
                dl.info(u'Enabled Watching path: {0}'.format(path),
                        group_id='watch_folders_ui')

    def remove_watch(self, watch_name):

        if watch_name in list(self.observers_dict.keys()):
            for observer in self.observers_dict.pop(watch_name):
                self.unschedule(observer)
                dl.info(u'Disabling Watch: {0}'.format(observer.path),
                        group_id='watch_folders_ui')

    def stop(self):
        self.started = False
        super(FSObserver, self).stop()

    def is_started(self):
        return self.started

    def start(self):
        self.started = True
        super(FSObserver, self).start()

    def dispatch_events(self, event_queue, timeout):
        # OVERRIDEN, to see which watch handles event
        event, watch = event_queue.get(block=True, timeout=timeout)

        with self._lock:
            # To allow unschedule/stop and safe removal of event handlers
            # within event handlers itself, check if the handler is still
            # registered after every dispatch.
            for handler in list(self._handlers.get(watch, [])):
                if handler in self._handlers.get(watch, []):
                    handler.dispatch(event, watch)
        event_queue.task_done()


def emit_progress(current_state, info_dict, progress_signal=None):
    if progress_signal:
        progress_signal.emit((current_state, info_dict))


def catch_error(func):
    def __tryexcept__(*args, **kwargs):

        try:
            func(*args, **kwargs)
        except Exception as expected:
            traceback.print_exc(file=sys.stdout)
            stacktrace = traceback.format_exc()

            exception = {
                'exception': expected,
                'stacktrace': stacktrace,
            }

            dl.exception(stacktrace, group_id='{0}/{1}'.format(
                'exceptions',
                func.__name__,))

            error_handle((exception, None))

    return __tryexcept__


def error_handle(args):
    stacktrace_dict, _worker = args
    stacktrace = stacktrace_dict.get('stacktrace') or repr(
        stacktrace_dict.get('exception')
    )
    dl.exception(stacktrace, group_id='exceptions/error_handle')





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

    if str(exception).find('getaddrinfo failed') != -1:
        error = 'connection_refused'

    if str(exception).find('Login/Password combination incorrect') != -1:
        error = 'login_pass_error'

    if str(exception).find('connect to MySQL server') != -1:
        error = 'sql_connection_error'

    if str(exception).find('ProtocolError') != -1:
        error = 'protocol_error'

    if str(exception).find('object has no attribute') != -1:
        error = 'attribute_error'

    return error


def parce_timestamp(timestamp):
    """Parse TACTIC and ISO-8601 timestamps for shared UI presentation."""
    if isinstance(timestamp, datetime.datetime):
        return timestamp
    text = str(timestamp or '').strip()
    if not text:
        return None

    # Presence and newer server procedures use UTC ISO-8601, while legacy
    # TACTIC objects commonly return a space-separated naive timestamp.
    normalized = text[:-1] + '+00:00' if text.endswith(('Z', 'z')) else text
    try:
        return datetime.datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(
            'Unsupported timestamp format: {!r}'.format(text)
        ) from error


def restart_app():
    os.system('{0} {1}'.format(sys.executable, ' '.join(sys.argv)))


def hex_to_rgb(hex_v, alpha=None, tuple=False):
    """
    Converts hex color to rgb/a
    Usage: hex_to_rgb('#9f8acf', 128)
    :param hex_v: string like "#9f8acf"
    :param alpha: string or int alpha ex: 128
    :return: rgba(r,g,b,a) or rgb(r,g,b)
    """
    r = int('0x' + hex_v[1:3], 0)
    g = int('0x' + hex_v[3:5], 0)
    b = int('0x' + hex_v[5:7], 0)
    if alpha:
        a = int(alpha)
        if tuple:
            return r, g, b, a
        else:
            return 'rgba({},{},{},{})'.format(r, g, b, a)
    else:
        if tuple:
            return r, g, b
        else:
            return 'rgb({},{},{})'.format(r, g, b)


def sub_urls(text):
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;!$()~_?\+-=\\\.&]*)", re.MULTILINE | re.UNICODE)
    value = urls.sub(r'<a href="\1" style="color:#66a3ff;text-decoration:none;">\1</a>', text)

    return value


def get_prc(prc, number):
    return int(prc * number / 100)


def sizes(size, precision=2):
    if size not in ['', None]:
        size = int(size)
    else:
        size = 0
    suffixes = [' b', ' Kb', ' Mb', ' Gb', ' Tb']
    suffix_index = 0

    while size > 1024 and suffix_index < 4:
        suffix_index += 1
        if not size:
            size = 0
        size /= 1024.0

    return '{1:.{0}f} {2}'.format(precision, size, suffixes[suffix_index])


def do_str(string):
    return string.decode('utf-8', 'ignore') if isinstance(string, bytes) else str(string)


def html_to_hex(text_html):
    source = (
        bytes(text_html)
        if isinstance(text_html, (bytes, bytearray))
        else str(text_html).encode('utf-8')
    )
    text_html_cmp = zlib.compress(source, 9)
    text_html_hex = 'zlib:' + binascii.hexlify(text_html_cmp).decode('ascii')

    if len(text_html_hex) > len(text_html):
        text_html_hex = text_html

    return text_html_hex


def hex_to_html(text_hex, return_bytes=False):
    if text_hex:
        if isinstance(text_hex, bytes):
            text_hex = text_hex.decode('utf-8', 'ignore')
        detect_zlib = text_hex.rfind('zlib:', 0, 5)
        if detect_zlib == 0:
            hex_to_text = zlib.decompress(binascii.a2b_hex(text_hex[5:]))
        else:
            hex_to_text = text_hex

        if return_bytes:
            # For ast end eval parcers
            return hex_to_text
        else:
            # For json
            if isinstance(hex_to_text, bytes):
                return hex_to_text.decode('utf-8', 'ignore')
            return str(hex_to_text)


def to_json(obj, pretty=False, use_ast=False):

    if use_ast:
        return str(obj)
    else:
        indent = None
        separators = (',', ':')
        if pretty:
            indent = 4
            separators = (', ', ': ')
        return json.dumps(obj, indent=indent, separators=separators)


def from_json(obj, use_ast=False):
    if obj:
        if use_ast:
            return ast.literal_eval(str(obj))
        else:
            return json.loads(obj)


def pp(text):
    from pprint import pprint
    return pprint(text)


def gen_acronym(word, length=2):
    acronym = ''
    if not word:
        return 'E'
    word = word[0].upper() + word[1:]

    for k, v in enumerate(word):
        if v.isupper() and len(acronym) < length:
            acronym += v
            if v == acronym[:-1]:
                acronym = acronym[:-1]

    if len(acronym) < length:
        acronym += word[1:length]
    return acronym


def gen_color(word):
    return color_hash(word)


def natural_sort_key(value):
    return tuple(
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r'(\d+)', value)
    )


def prettify_text(text, first_letter=False):
    if text:
        if first_letter:
            text = text.replace('_', ' ').split(' ')
            final_text = []
            for word in text:
                word = word[:1].upper() + word[1:]
                final_text.append(word)
            return u' '.join(final_text)
        else:
            return text.replace('_', ' ').title()


def minify_code(source):
    return source


def time_it(start_time=None, message='Code flow running time:'):
    if start_time:
        print('{0} {1}'.format(message, time.time() - start_time))
    else:
        return time.time()


def dtime_it(func):
    def wrap(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        print('Code flow running time for {0}: {1}'.format(func.__name__, time.time() - start_time))
        return result
    return wrap


def get_ver_rev(ver=None, rev=None):
    if ver > 0 and rev > 0:
        result = '<span style="color:#008498;">Ver: {0:03d};</span><span style="color:#0a9800;"> Rev: {1:03d}</span>'.format(
            ver,
            rev)
    elif ver > 0 and rev == 0:
        result = '<span style="color:#008498;">Ver: {0:03d}</span>'.format(ver)
    elif ver == 0 and rev > 0:
        result = '<span style="color:#0a9800;"> Rev: {0:03d}</span>'.format(rev)
    else:
        result = ''

    return result


def group_dict_by(dicts_list, group_by):
    grouped = collections.defaultdict(list)
    for dic in dicts_list:
        grouped[dic.get(group_by)].append(dic)

    return grouped




def get_value_from_config(config_dict, control, default_value=None):
    if config_dict:
        if default_value:
            result = None
            for all_values in config_dict.values():
                for obj_name, value in zip(all_values['obj_name'], all_values['value']):
                    if control == obj_name:
                        result = value
                        break
            if not result:
                return default_value
            else:
                return result
        else:
            for all_values in config_dict.values():
                for obj_name, value in zip(all_values['obj_name'], all_values['value']):
                    if control == obj_name:
                        return value
    else:
        return default_value






























# New QTreeWidget funcs






































# files etc routine
def file_format(ext):
    formats = {
        'ma': ['ma', 'mayaAscii', 'main', 'file'],
        'mb': ['mb', 'mayaBinary', 'main', 'file'],
        'hip': ['hip', 'Houdini', 'main', 'file'],
        '3b': ['3b', '3D-Coat', 'main', 'file'],
        'max': ['max', '3DSMax scene', 'main', 'file'],
        'scn': ['scn', 'Softimage XSI', 'main', 'file'],
        'mud': ['mud', 'Mudbox', 'main', 'file'],
        'abc': ['abc', 'Alembic', 'main', 'file'],
        'obj': ['obj', 'OBJ', 'main', 'file'],
        '3ds': ['3ds', '3DSMax model', 'main', 'file'],
        'nk': ['nk', 'Nuke', 'main', 'file'],
        'fbx': ['fbx', 'FBX', 'main', 'file'],
        'dae': ['dae', 'COLLADA', 'main', 'file'],
        'rs': ['rs', 'Redshift Proxy', 'main', 'file'],
        'vdb': ['vdb', 'Open VDB', 'main', 'file'],
        'jpg': ['jpg', 'JPEG Image', 'main', 'preview'],
        'jpeg': ['jpeg', 'JPEG Image', 'main', 'preview'],
        'psd': ['psd', 'Photoshop PSD', 'main', 'file'],
        'tif': ['tif', 'TIFF Image', 'main', 'preview'],
        'tiff': ['tiff', 'TIFF Image', 'main', 'preview'],
        'png': ['png', 'PNG Image', 'main', 'preview'],
        'tga': ['tga', 'TARGA Image', 'main', 'file'],
        'exr': ['exr', 'EXR Image', 'main', 'file'],
        'hdr': ['hdr', 'HDR Image', 'main', 'file'],
        'dpx': ['dpx', 'DPX Image', 'main', 'file'],
        'mov': ['mov', 'MOV Animation', 'main', 'file'],
        'avi': ['avi', 'AVI Animation', 'main', 'file'],
        'mp4': ['mp4', 'MP4 Animation', 'main', 'file'],
    }
    low_case_ext = ext.lower()
    if low_case_ext in list(formats.keys()):
        return formats[low_case_ext]
    else:
        return [low_case_ext, low_case_ext, 'main', 'file']


def extract_extension(filename):
    base_filename = os.fsdecode(os.path.basename(filename))
    ext = base_filename.split('.', -1)
    if not os.path.isdir(filename):
        if base_filename == ext[0]:
            return ['', 'No Ext', 'main', 'file']
        elif len(ext) > 1:
            return file_format(ext[-1])
    elif os.path.isdir(filename):
        return ['', 'Folder', 'folder', 'folder']


def extract_filename(filename, no_ext=False):
    name = os.fsdecode(os.path.basename(filename)).split('.')
    if len(name) > 1:
        if no_ext:
            return u'.'.join(name[:-1])
        else:
            return u'.'.join(name)
    else:
        return name[0]


def extract_dirname(filename):
    dir = os.fsdecode(os.path.realpath(filename)).split('.', 1)
    if dir[0] == filename:
        return os.path.dirname(filename)
    if len(dir) == 1 and not os.path.isdir(filename):
        return dir[0]
    else:
        return os.path.dirname(filename)


def extract_zip_archive(zip_file_path, destination_path):
    zp = zipfile.ZipFile(zip_file_path, "r")

    members = []
    for member in zp.infolist():
        member.filename = member.filename.replace('\\', '/')
        members.append(member)

    zp.extractall(destination_path, members)
    zp.close()


def open_file_associated(filepath):
    if filepath and os.path.exists(filepath):
        if env_mode.get_platform() == 'Linux':
            subprocess.Popen(('xdg-open', filepath), stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        else:
            os.startfile(filepath)


def open_folder(filepath, highlight=True):

    if filepath and os.path.exists(filepath):
        if env_mode.get_platform() == 'Linux':
            if highlight:
                subprocess.call(('nautilus', '-s', filepath))
            else:
                subprocess.call(('xdg-open', filepath))
        elif env_mode.get_platform() == 'Windows':
            if highlight:
                subprocess.call(u'explorer /select, "{0}"'.format(filepath))
            else:
                os.startfile(filepath)
        else:
            os.startfile(filepath)


def form_date_time(datetime_string, return_obj=False):
    if len(datetime_string.split('.')) > 1:
        datetime_object = datetime.datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S.%f')
    else:
        datetime_object = datetime.datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')

    if return_obj:
        return datetime_object
    else:
        return datetime_object.strftime('%Y-%m-%d %H:%M:%S')


def form_path(path, tp=None):
    if tp == 'web':
        return path.replace('\\', '/').replace('\\\\', '/').replace('//', '/').replace(':/', '://')

    elif env_mode.get_platform() == 'Linux' or tp == 'linux':
        formed_path = path.replace('\\', '/').replace('\\\\', '/').replace('//', '/')

        if env_mode.get_platform() == 'Windows':
            if formed_path.startswith('/'):
                formed_path = '/' + formed_path

        return formed_path

    elif env_mode.get_platform() == 'Windows' or tp == 'win':

        # guess if path is in local network
        if path.startswith('\\\\'):
            return '\\' + path.replace('/', '\\').replace('\\\\', '\\')
        elif path.startswith('/'):
            return '\\' + path.replace('/', '\\').replace('\\\\', '\\')
        elif path.startswith('//'):
            return '\\' + path.replace('/', '\\').replace('\\\\', '\\')
        else:
            return path.replace('//', '\\').replace('/', '\\').replace('\\\\', '\\')

    else:
        return path.replace('\\', '/')


def get_st_size(file_path):
    if isinstance(file_path, list):
        total_size = 0
        for fl in file_path:
            if os.path.isfile(fl):
                total_size += os.stat(fl)[ST_SIZE]
        return total_size
    else:
        if os.path.isfile(file_path):
            return os.stat(file_path)[ST_SIZE]


def get_file_asset_dir(item):
    repo_name = item.snapshot.get('repo')
    base_dir = env_tactic.get_base_dir('base')
    if repo_name:
        current_dir = env_tactic.get_base_dir(repo_name)
        if current_dir:
            asset_dir = current_dir.get('value')[0]
        else:
            asset_dir = base_dir.get('value')[0]
    else:
        asset_dir = base_dir.get('value')[0]
    return asset_dir


def get_abs_path(item, file_type=None):
    if file_type:
        modes = file_type
    else:
        modes = env_mode.modes
    modes.append('main')

    for mode in modes:
        if item.files.get(mode):
            main_file = item.files[mode][0]
            asset_dir = get_file_asset_dir(item)
            file_path = form_path(
                '{0}/{1}/{2}'.format(asset_dir, main_file['relative_dir'], main_file['file_name']))

            return file_path


def get_snapshot_asset_dir(snapshot_dict):
    repo_name = snapshot_dict.get('repo')
    base_dir = env_tactic.get_base_dir('base')
    if repo_name:
        current_dir = env_tactic.get_base_dir(repo_name)
        if current_dir:
            asset_dir = current_dir.get('value')[0]
        else:
            asset_dir = base_dir.get('value')[0]
    else:
        asset_dir = base_dir.get('value')[0]
    return asset_dir


def get_abs_file_path_name(snapshot_dict, file_dict):
    asset_dir = get_snapshot_asset_dir(snapshot_dict)
    file_path = form_path(
        '{0}/{1}/{2}'.format(asset_dir, file_dict['relative_dir'], file_dict['file_name']))

    return file_path


def to_plain_text(html, strip=80):
    from thlib.side.Qt import QtGui as Qt4Gui
    text_doc = Qt4Gui.QTextDocument()
    text_doc.setHtml(html)
    if strip:
        plain_text = text_doc.toPlainText()[:strip]
        if len(plain_text) > strip - 1:
            plain_text += ' ...'
    else:
        plain_text = text_doc.toPlainText()

    return plain_text


def qsize_to_tuple(qsize):
    return qsize.toTuple()


def tuple_to_qsize(qtuple, qtype='size'):
    from thlib.side.Qt import QtCore
    if qtype == 'size':
        return QtCore.QSize(qtuple[0], qtuple[1])
    elif qtype == 'pos':
        return QtCore.QPoint(qtuple[0], qtuple[1])
    elif qtype == 'rect':
        return QtCore.QRect(qtuple[0], qtuple[1], qtuple[2], qtuple[3])


def check_config(ref_config_dict, config_dict):

    if config_dict:
        # First simple check
        if len(ref_config_dict.keys()) != len(config_dict.keys()):
            return ref_config_dict
        else:
            # Check per items
            if set(config_dict.keys()) == set(ref_config_dict.keys()):
                return config_dict
            else:
                return ref_config_dict
    else:
        return ref_config_dict


# CLASSES #

class FileObject(object):
    """Meta File Object"""
    def __init__(self, file_=None, template_=None):

        self._file = file_
        self._template = template_
        self._type = None
        self._previewable = None
        self._file_type = None
        self._files_list = []
        self._file_path = None
        self._file_name = None
        self._sizes_list = []
        self._new_filename = None
        self._new_filepath = None
        self._new_frame_padding = None
        self._new_template = None
        self._abs_file_name = None
        self._pretty_file_name = None
        self._file_ext = None
        self._layer = None
        self._base_file_type_pretty_name = None
        self._base_file_type = None
        self._tactic_file_type = None
        self._sequence_length = None
        self._sequence_padding = None
        self._sequence_frames = []
        self._sequence_start = None
        self._sequence_end = None
        self._sequence_missing_frames = None
        self._app_info = None

        self._tiles_count = None
        self._tiles = []

        if self._file:
            self.init_files()

    def get_abs_file_name(self, file_dict=None, pretty=False, filename=False, no_ext=False):

        if not file_dict:
            file_dict = self.get_all_files_dicts(True)

        if not file_dict and self._abs_file_name:
            return self._abs_file_name

        separators = self._template['pattern_separators']
        order = self._template['order']

        if len(order) - len(separators) > 0:
            separators.insert(0, '')

        order_format = u''.join('%s{%s}' % (k, j) for j, k in zip(order, separators))

        if pretty:
            self._abs_file_name = order_format.format(**self.get_pretty_frames_and_udims(file_dict.copy()))
        else:
            self._abs_file_name = order_format.format(**file_dict)
        if filename:
            if no_ext:
                return self.__get_filename(file_dict.copy(), no_ext=True).get('filename')
            else:
                return order_format.format(**self.__get_filename(file_dict.copy()))

        return self._abs_file_name

    @staticmethod
    def __get_filename(file_dict, no_ext=False):
        if file_dict.get('filename'):
            file_dict['filename'] = file_dict.get('filename').split('/')[-1]
            if no_ext and file_dict.get('ext'):
                file_dict['filename'].replace('.{0}'.format(file_dict['ext']), '')
        return file_dict

    def get_pretty_frames_and_udims(self, file_dict):
        if file_dict.get('frame'):
            file_dict['frame'] = '[{}]'.format('#' * self.get_sequence_padding())
        if file_dict.get('udim'):
            file_dict['udim'] = '[UUVV]'
        if file_dict.get('uv'):
            file_dict['uv'] = '[u<>_v<>]'

        return file_dict

    def get_metadata(self):
        metadata_dict = {}
        if self.get_file_name(True):
            metadata_dict['filename'] = self.get_file_name(True)
        if self.get_file_ext():
            metadata_dict['ext'] = self.get_file_ext()
        if self.get_layer():
            metadata_dict['layer'] = self.get_layer()
        if self.get_sequence_frameranges():
            metadata_dict['frameranges'] = self.get_sequence_frameranges()
        if self.get_sequence_frame_range():
            metadata_dict['frame_range'] = self.get_sequence_frame_range()
        if self.get_sequence_padding():
            metadata_dict['padding'] = self.get_sequence_padding()
        if self.get_tiles():
            metadata_dict['udims'] = self.get_tiles()
        if self.get_type():
            metadata_dict['type'] = self.get_type()
        if not self._sizes_list:
            metadata_dict['st_sizes'] = self.get_sizes_list()
        if self._sizes_list:
            metadata_dict['st_size'] = self.get_sizes_list(together=True)
        if self.get_app_info():
            metadata_dict['app_info'] = self.get_app_info()
        if self._template:
            metadata_dict['template'] = self._template['pattern_string']
        if self._new_filename:
            metadata_dict['new_filename'] = self._new_filename[0]
            metadata_dict['new_file_part'] = self._new_filename[1]
            metadata_dict['new_file_ext'] = self._new_filename[2].replace('.', '')
        if self._new_template:
            metadata_dict['new_template'] = self._new_template
        if self._new_frame_padding:
            metadata_dict['new_padding'] = self._new_frame_padding

        return metadata_dict

    def get_app_info(self):
        return self._app_info

    def set_app_info(self, app_info_dict):
        if app_info_dict:
            self._app_info = app_info_dict
        else:
            self._app_info = None

    def get_type(self):
        return self._type

    def set_type(self, type_):
        if type_:
            self._type = type_['type']
        else:
            self._type = 'file'

    def get_sizes_list(self, together=False, files_list=None):
        if self._sizes_list:
            if together:
                return sum(self._sizes_list)
            else:
                return self._sizes_list

        sizes_list = []
        if not files_list:
            files_list = self.get_all_files_list()
        for fl in files_list:
            size = get_st_size(fl)
            if size:
                sizes_list.append(size)

        if sizes_list:
            if together:
                return sum(sizes_list)
            else:
                return sizes_list

    def set_sizes_list(self, _sizes_list):
        if _sizes_list:
            self._sizes_list = _sizes_list

    def get_file_type(self):
        return extract_extension(self.get_abs_file_name())

    def get_file_path(self):
        return extract_dirname(self.get_abs_file_name())

    def get_all_files_list(self, first=False, filenames=False, no_ext=False):

        if filenames:
            # Only for external calls
            file_names_list = []
            for fld in self.get_all_files_dicts():
                file_names_list.append(form_path(self.get_abs_file_name(fld, filename=True, no_ext=no_ext)))
            return sorted(file_names_list)

        if not self._files_list:
            for fld in self.get_all_files_dicts():
                self._files_list.append(form_path(self.get_abs_file_name(fld)))
            self._files_list = sorted(self._files_list)

        if first:
            return form_path(self._files_list[0])
        else:
            return sorted(self._files_list)

    def get_all_files_dicts(self, first=False):
        if first:
            return self._file[1][0]
        else:
            return self._file[1]

    def get_file_name(self, no_ext=False):
        if not self._file_name:
            self._file_name = self.get_abs_file_name(filename=True, no_ext=no_ext)
        return self._file_name

    def get_name_part(self, frame_padding=4, template='.$LAYER_$UDIM/UV.$FRAME'):
        pattern, separators = self.split_template(template)

        order_format = ''
        for file_dict in self.get_all_files_dicts():
            order_format = ''
            for item, sep in zip(reversed(pattern), reversed(separators)):
                if item == '$UDIM/UV':
                    if file_dict.get('udim'):
                        item = '[UUVV]'
                    elif file_dict.get('uv'):
                        item = 'u<>_v<>'
                if item == '$FRAME':
                    item = '[{}]'.format('#' * frame_padding)
                if item == '$LAYER':
                    item = file_dict['layer']

                order_format = sep + item + order_format

        return order_format

    def get_all_new_files_list(self, new_filename=None, new_filepath=None, new_frame_padding=None, no_ext=False, new_template='$FILENAME.$LAYER_$UDIM/UV.$FRAME.$EXT'):
        """
        This can only be used once, it creates metadata with new data, and returning list with new file names.

        :param new_filename:
        :param new_filepath:
        :param new_frame_padding:
        :param no_ext:
        :param new_template:
        :return:
        """
        if new_filename:
            self._new_filename = new_filename
        if new_filepath:
            self._new_filepath = new_filepath
        if new_frame_padding:
            self._new_frame_padding = new_frame_padding

        pattern, separators = self.split_template(new_template)

        order_format_list = []

        for file_dict in self.get_all_files_dicts():
            order_format = ''
            template = ''
            for item, sep in zip(reversed(pattern), reversed(separators)):
                temp = ''
                if item == '$FILENAME':
                    item = u'{0}/{1}'.format(self._new_filepath, self._new_filename[0])
                    temp = '$FILENAME'
                if item == '$UDIM/UV':
                    if file_dict.get('udim'):
                        item = file_dict['udim']
                        temp = '$UDIM'
                    elif file_dict.get('uv'):
                        item = file_dict['uv']
                        temp = '$UV'
                if item == '$FRAME':
                    item = file_dict['frame'].zfill(self._new_frame_padding)
                    temp = '$FRAME'
                if item == '$LAYER':
                    item = file_dict['layer']
                    temp = '$LAYER'
                if item == '$EXT' and not no_ext:
                    item = self._new_filename[2].replace('.', '')
                    temp = '$EXT'

                order_format = sep + item + order_format
                template = sep + temp + template

            order_format_list.append(order_format)

            self._new_template = template

        return order_format_list

    def split_template(self, template):
        match_template = MatchTemplate([template])

        template = list(match_template.split_patterns.values())[0][0]

        pattern = template[0]
        separators = template[1]
        if len(pattern) - len(separators) > 0:
            separators.insert(0, '')

        new_pattern = []
        new_separators = []
        for cp, cp_sep in zip(pattern, separators):
            for i, op in enumerate(self._template['pattern']):
                if op in ['$UDIM', '$UV']:
                    op = '$UDIM/UV'
                if cp == op:
                    new_pattern.append(cp)
                    new_separators.append(cp_sep)

        return new_pattern, new_separators

    def get_file_id(self):
        return self._file[0]

    def get_pretty_file_name(self):
        if self.get_type() not in ['layer_file', 'file', 'no_ext']:
            return extract_filename(self.get_abs_file_name(pretty=True))
        return extract_filename(self.get_abs_file_name())

    def get_file_ext(self):
        if not self._file_ext:
            self._file_ext = self.get_file_type()[0]
        return self._file_ext

    def get_layer(self):
        return self._layer

    def get_base_file_type_pretty_name(self):
        if not self._base_file_type_pretty_name:
            self._base_file_type_pretty_name = self.get_file_type()[1]
        return self._base_file_type_pretty_name

    def get_base_file_type(self):
        if not self._base_file_type:
            self._base_file_type = self.get_file_type()[2]
        return self._base_file_type

    def get_tactic_file_type(self):
        if not self._tactic_file_type:
            self._tactic_file_type = self.get_file_type()[3]
        return self._tactic_file_type

    def get_sequence_frameranges(self, padding=False):

        if self._sequence_frames:
            if self.get_type() in ['layer_uv_sequence', 'layer_udim_sequence', 'uv_sequence', 'udim_sequence']:

                self._sequence_length = collections.defaultdict(list)
                self._sequence_start = collections.defaultdict(list)
                self._sequence_end = collections.defaultdict(list)
                self._sequence_missing_frames = collections.defaultdict(list)
                sequence_ranges = collections.defaultdict(list)
                for uv, frames in self._sequence_frames:
                    frame_list = sorted(frames)
                    first_frame = min(frame_list)
                    last_frame = max(frame_list)
                    frames_buffer = []
                    missing_frames = []

                    for frame in range(first_frame, last_frame + 2):

                        frames_buffer.append(frame)
                        if frame not in frame_list:

                            if frames_buffer[0] == frame - 1:
                                if padding:
                                    sequence_ranges[uv].append(self.get_frame_with_padding(frames_buffer[0]))
                                else:
                                    sequence_ranges[uv].append(str(frames_buffer[0]))
                            elif frame - 1 in frame_list:
                                if padding:
                                    sequence_ranges[uv].append(
                                        '{0}-{1}'.format(self.get_frame_with_padding(frames_buffer[0]),
                                                         self.get_frame_with_padding(frame - 1)))
                                else:
                                    sequence_ranges[uv].append('{0}-{1}'.format(frames_buffer[0], frame - 1))
                            frames_buffer = []

                            if last_frame > frame:
                                missing_frames.append(frame)

                    self._sequence_length[uv].append(len(frame_list))
                    self._sequence_start[uv].append(first_frame)
                    self._sequence_end[uv].append(last_frame)
                    self._sequence_missing_frames[uv].append(missing_frames)

                return sequence_ranges.items()

            elif self.get_type() in ['sequence', 'layer_sequence']:

                frame_list = sorted(self._sequence_frames)
                first_frame = min(frame_list)
                last_frame = max(frame_list)
                frames_buffer = []
                sequence_ranges = []
                missing_frames = []

                for frame in range(first_frame, last_frame + 2):

                    frames_buffer.append(frame)
                    if frame not in frame_list:

                        if frames_buffer[0] == frame - 1:
                            if padding:
                                sequence_ranges.append(self.get_frame_with_padding(frames_buffer[0]))
                            else:
                                sequence_ranges.append(str(frames_buffer[0]))
                        elif frame - 1 in frame_list:
                            if padding:
                                sequence_ranges.append('{0}-{1}'.format(self.get_frame_with_padding(frames_buffer[0]),
                                                                        self.get_frame_with_padding(frame - 1)))
                            else:
                                sequence_ranges.append('{0}-{1}'.format(frames_buffer[0], frame - 1))
                        frames_buffer = []

                        if last_frame > frame:
                            missing_frames.append(self.get_frame_with_padding(frame))

                self._sequence_length = len(frame_list)
                self._sequence_start = first_frame
                self._sequence_end = last_frame
                self._sequence_missing_frames = missing_frames

                return sequence_ranges

    def get_sequence_frame_range(self):
        if self._sequence_frames:
            if self.get_type() in ['layer_uv_sequence', 'layer_udim_sequence', 'uv_sequence', 'udim_sequence']:
                sequence_ranges = []
                for start, end in zip(self.get_sequence_start().items(), self.get_sequence_end().items()):
                    sequence_ranges.append((start[0], '{0}-{1}'.format(start[1][0], end[1][-1])))
                return sequence_ranges
            elif self.get_type() in ['sequence', 'layer_sequence']:
                return '{0}-{1}'.format(self.get_sequence_start(), self.get_sequence_end())

    def get_frame_with_padding(self, frame):
        return '%0*d' % (self.get_sequence_padding(), int(frame))

    def get_sequence_frameranges_string(self, brackets=None):
        frames = self.get_sequence_frameranges()
        if frames:
            if self.get_type() in ['layer_uv_sequence', 'layer_udim_sequence', 'uv_sequence', 'udim_sequence']:
                framerange_strings = []
                for uv, frame in frames:
                    framerange_string = '{1} ({0})'.format(uv, ', '.join(frame))
                    if brackets:
                        framerange_string = '%s%s%s' % (brackets[0], framerange_string, brackets[1])
                    framerange_strings.append(framerange_string)

                return ', '.join(framerange_strings)

            elif self.get_type() in ['sequence', 'layer_sequence']:
                framerange_string = ', '.join(frames)
                if brackets:
                    return '%s%s%s' % (brackets[0], framerange_string, brackets[1])

                return framerange_string

    def init_files(self):
        if self._template:
            self.set_type(self._template)
        if self._sequence_frames:
            return self._sequence_frames
        else:
            all_files_dicts = self.get_all_files_dicts()
            if self.get_type() in ['layer_file', 'file', 'no_ext']:
                for fld in all_files_dicts:
                    self._layer = fld.get('layer')

            elif self.get_type() in ['layer_uv', 'layer_udim', 'uv', 'udim']:
                for fld in all_files_dicts:
                    udim = fld.get('udim')
                    if not udim:
                        udim = fld.get('uv')
                    self._tiles.append(udim)
                    self._layer = fld.get('layer')
                self._tiles_count = len(self._tiles)

            elif self.get_type() in ['sequence', 'layer_sequence']:
                for fld in all_files_dicts:
                    self._sequence_padding = len(fld['frame'])
                    self._sequence_frames.append(int(fld['frame']))
                    self._layer = fld.get('layer')

            elif self.get_type() in ['layer_uv_sequence', 'layer_udim_sequence', 'uv_sequence', 'udim_sequence']:
                frames_by_udims = collections.defaultdict(list)
                for fld in all_files_dicts:
                    self._sequence_padding = len(fld['frame'])
                    udim = fld.get('udim')
                    if not udim:
                        udim = fld.get('uv')
                    frames_by_udims[udim].append(int(fld['frame']))
                    self._layer = fld.get('layer')
                self._sequence_frames = frames_by_udims.items()
                self._tiles = list(frames_by_udims.keys())
                self._tiles_count = len(self._tiles)

            return self._sequence_frames

    def get_sequence_lenght(self):
        return self._sequence_length

    def get_sequence_padding(self):
        return self._sequence_padding

    def get_sequence_start(self):
        return self._sequence_start

    def get_sequence_end(self):
        return self._sequence_end

    def get_sequence_missing_frames(self):
        return self._sequence_missing_frames

    def get_tiles_count(self):
        return self._tiles_count

    def get_tiles(self):
        return self._tiles

    def is_exists(self, check_all_files=False):
        if check_all_files:
            exists = False
            for fl in self.get_all_files_list():
                exists = os.path.isfile(fl)
            return exists
        else:
            return os.path.isfile(self.get_all_files_list(True))

    def is_previewable(self):
        if self._previewable:
            return True

        ext = self.get_file_type()
        if ext[3] == 'preview':
            self._previewable = True

        return self._previewable

    def open_file(self):
        open_file_associated(self.get_all_files_list(True))

    def open_folder(self):
        open_folder(self.get_all_files_list(first=True), highlight=True)


class MatchTemplate(object):
    default_patterns = [
        '$FILENAME',
        '$FILENAME.$EXT'
    ]

    def __init__(self, patterns=None, padding=3, add_default_patterns=False):

        if patterns:
            self.patterns = list(dict.fromkeys(patterns))
        else:
            self.patterns = None
        if add_default_patterns:
            if patterns:
                patterns.extend(self.default_patterns)
                self.patterns = list(dict.fromkeys(patterns))
            else:
                self.patterns = list(self.default_patterns)
        self.padding = padding
        self.split_patterns = None

        if self.patterns:
            self.parse_patterns()

    def get_preview_string(self):

        return self.patterns.pop()\
            .replace('$FILENAME', 'Filename')\
            .replace('$EXT', 'tif')\
            .replace('$UDIM', '[UUVV]')\
            .replace('$UV', '[u<>_v<>]')\
            .replace('$FRAME', '[###]')\
            .replace('$LAYER', 'layer')

    def get_type_string(self):
        return list(self.split_patterns.keys())[0].replace('_', ' | ')

    def get_template(self, template):
        templates = {
            '$EXT': ['(?P<ext>[0-9A-z]+)', 'ext'],
            '$FILENAME': ['(?P<filename>.+)', 'filename'],
            '$UDIM': ['(?P<udim>(?P<u>[0-9]{2})(?P<v>[0-9]{2}))', 'udim'],
            '$UV': ['(?P<uv>u(?P<u>[0-9]{1,2})_v(?P<v>[0-9]{1,2}))', 'uv'],
            '$FRAME': ['(?P<frame>[0-9]{%s,})' % self.padding, 'frame'],  # must be at least 3 frames by default
            '$LAYER': ['(?P<layer>[A-z0-9]*[A-z]+[A-z0-9]*)', 'layer'],  # layer must not have digits only
        }

        return templates.get(template)

    @staticmethod
    def get_type(keys_list):
        if all(('$UV' in keys_list, '$FRAME' in keys_list, '$LAYER' in keys_list)):
            return 'layer_uv_sequence'
        if all(('$UDIM' in keys_list, '$FRAME' in keys_list, '$LAYER' in keys_list)):
            return 'layer_udim_sequence'
        if all(('$UV' in keys_list, '$FRAME' in keys_list)):
            return 'uv_sequence'
        if all(('$UDIM' in keys_list, '$FRAME' in keys_list)):
            return 'udim_sequence'
        if all(('$LAYER' in keys_list, '$FRAME' in keys_list)):
            return 'layer_sequence'
        if all(('$LAYER' in keys_list, '$UV' in keys_list)):
            return 'layer_uv'
        if all(('$LAYER' in keys_list, '$UDIM' in keys_list)):
            return 'layer_udim'
        if '$FRAME' in keys_list:
            return 'sequence'
        if '$UV' in keys_list:
            return 'uv'
        if '$UDIM' in keys_list:
            return 'udim'
        if '$LAYER' in keys_list:
            return 'layer_file'
        if '$EXT' in keys_list:
            return 'file'
        return 'no_ext'

    def parse_patterns(self, patterns=None):
        if patterns:
            self.patterns = patterns

        values_pattern = re.compile('[.|_]')
        split_patterns = collections.defaultdict(list)

        for ptn in self.patterns:
            key = re.split(values_pattern, ptn)
            split_patterns[self.get_type(key)].append((key, re.findall(values_pattern, ptn), ptn))

        self.split_patterns = split_patterns

        return self.split_patterns

    def get_re_patterns(self, patterns):
        re_temp = []
        re_seps = []
        order = []

        for i, key in enumerate(patterns[0]):
            if len(patterns[1]) > i and patterns[1][i]:
                re_seps.append('[{}]'.format(patterns[1][i]))
            else:
                re_seps.append('')
            template = self.get_template(key)
            if template:
                re_temp.append(template[0])
                order.append(template[1])
            else:
                re_temp.append(key)

        pattern = '^{0}$'.format(''.join(j + k for j, k in zip(re_temp, re_seps)))

        return pattern, order

    @staticmethod
    def get_unique_name(group_dict, order, separators):

        if len(order) - len(separators) > 0:
            separators.insert(0, '')

        order_format = ''
        for item, sep in zip(order, separators):
            if item == 'frame':
                item = '[$FRAME' + str(len(group_dict['frame'])) + '$]'
            if item == 'uv':
                item = '[$UV$]'
            if item == 'udim':
                item = '[$UDIM$]'
            if item == 'ext':
                item = group_dict['ext']
            if item == 'filename':
                item = group_dict['filename']
            if item == 'layer':
                item = group_dict['layer']

            order_format = order_format + sep + item

        return order_format

    def match_by_template(self, files_list, templates, template_names):
        match_dicts = []
        tpls_names = []

        for i, template in enumerate(templates):
            values_pattern = re.compile(template[0])
            def_dict = collections.OrderedDict()
            not_matched = []
            while files_list:
                fl = files_list.pop()
                # for windows os
                fl_norm = fl.replace('\\', '/')
                search_result = re.search(values_pattern, fl_norm)
                if search_result:
                    group_dict = search_result.groupdict()
                    unique_filename = self.get_unique_name(group_dict, template[1], template_names[i][1][1])
                    group_dict['orig_file'] = fl_norm
                    def_dict.setdefault(unique_filename, []).append(group_dict)
                else:
                    not_matched.append(fl_norm)

            # if not found, match with next template
            files_list = not_matched
            if def_dict:
                match_dicts.append(def_dict)
                template_dict = {
                    'type': template_names[i][0],
                    're_string': template[0],
                    'order': template[1],
                    'pattern': template_names[i][1][0],
                    'pattern_separators': template_names[i][1][1],
                    'pattern_string': template_names[i][1][2],
                }
                tpls_names.append(template_dict)

        return zip(match_dicts, tpls_names)

    def get_files(self, files_list=None, default_types=False):
        templates = []
        template_names = []

        # this is needed, because we need to get uv sequences first, then others
        types = [
            'layer_uv_sequence',
            'layer_udim_sequence',
            'uv_sequence',
            'udim_sequence',
            'layer_sequence',
            'layer_uv',
            'layer_udim',
            'sequence',
            'uv',
            'udim',
            'layer_file',
            'file',
            'no_ext'
        ]

        def_types = [
            'file',
            'no_ext'
        ]

        if default_types:
            types = def_types

        for tp in types:
            if self.split_patterns.get(tp):
                for patterns in self.split_patterns.get(tp):
                    templates.append(self.get_re_patterns(patterns))
                    template_names.append((tp, patterns))

        return self.match_by_template(files_list, templates, template_names)

    def get_files_objects(self, files_list, allow_single_sequence=False, allow_single_udim=False, sort=True):
        if sort:
            found_files = self.get_files(sorted(files_list, key=natural_sort_key))
        else:
            found_files = self.get_files(files_list)
        out_dict = collections.OrderedDict()

        single_sequences_and_udims = []

        for files, tpl in found_files:
            for fl in files.items():
                if not allow_single_sequence or allow_single_udim:
                    if tpl['type'] in ['layer_uv_sequence', 'layer_udim_sequence', 'uv_sequence', 'udim_sequence', 'layer_sequence', 'sequence'] and len(fl[1]) == 1:
                        single_sequences_and_udims.append(fl[1][0]['orig_file'])
                    elif tpl['type'] in ['layer_uv', 'layer_udim', 'sequence', 'uv', 'udim'] and len(fl[1]) == 1:
                        single_sequences_and_udims.append(fl[1][0]['orig_file'])
                    else:
                        file_obj = FileObject(fl, tpl)
                        out_dict.setdefault(tpl['type'], []).append(file_obj)

        # getting all single sequences or udims/uvs
        if single_sequences_and_udims:
            single_found_files = self.get_files(single_sequences_and_udims, default_types=True)
            for files, tpl in single_found_files:
                for fl in files.items():
                    file_obj = FileObject(fl, tpl)
                    out_dict.setdefault(tpl['type'], []).append(file_obj)

        return out_dict

    def init_from_tactic_file_object(self, tactic_file_object):
        metadata = tactic_file_object.get_metadata()
        path = tactic_file_object.get_abs_path()
        template = list(self.parse_patterns([metadata.get('new_template')]).values())[0][0]
        pattern = template[0]
        separators = template[1]
        if len(pattern) - len(separators) > 0:
            separators.insert(0, '')

        files_list = []
        if metadata.get('type') in ['layer_uv_sequence', 'layer_udim_sequence', 'uv_sequence', 'udim_sequence']:
            udims_list = self.unpack_udims(metadata.get('frameranges'))
            for udim, frames in udims_list:
                for frame in frames:
                    name = self.unpack_name(
                        pattern,
                        separators,
                        metadata.get('new_filename'),
                        metadata.get('new_file_ext'),
                        udim,
                        '%0*d' % (metadata.get('new_padding'), int(frame)),
                        metadata.get('layer'),
                    )
                    files_list.append('%s/%s' % (path, name))
        elif metadata.get('type') in ['layer_uv', 'layer_udim', 'uv', 'udim']:
            udims_list = metadata.get('udims')
            for udim in udims_list:
                name = self.unpack_name(
                    pattern,
                    separators,
                    metadata.get('new_filename'),
                    metadata.get('new_file_ext'),
                    udim,
                    None,
                    metadata.get('layer'),
                )
                files_list.append('%s/%s' % (path, name))
        elif metadata.get('type') in ['sequence', 'layer_sequence']:
            frames_list = self.unpack_frames(metadata.get('frameranges'))
            for frame in frames_list:
                name = self.unpack_name(
                    pattern,
                    separators,
                    metadata.get('new_filename'),
                    metadata.get('new_file_ext'),
                    None,
                    '%0*d' % (metadata.get('new_padding'), int(frame)),
                    metadata.get('layer'),
                )
                files_list.append('%s/%s' % (path, name))
        elif metadata.get('type') in ['layer_file', 'file', 'no_ext']:
            name = self.unpack_name(
                pattern,
                separators,
                metadata.get('new_filename'),
                metadata.get('new_file_ext'),
                None,
                None,
                metadata.get('layer'),
            )
            files_list.append('%s/%s' % (path, name))

        self.__init__(
            [metadata.get('new_template')],
            padding=metadata.get('new_padding'),
            # add_default_patterns=True
        )
        files_objects_dict = self.get_files_objects(files_list)

        return files_objects_dict

    @staticmethod
    def unpack_name(pattern, separators, file_name=None, file_ext=None, udim=None, frame=None, layer=None):
        result_name = []

        for p, s in zip(pattern, separators):
            if p == '$FILENAME':
                result_name.append(s + file_name)
            if p in ['$UDIM', '$UV']:
                result_name.append(s + udim)
            if p == '$LAYER':
                result_name.append(s + layer)
            if p == '$FRAME':
                result_name.append(s + frame)
            if p == '$EXT':
                result_name.append(s + file_ext)

        return ''.join(result_name)

    def unpack_udims(self, udims):

        udims_list = []
        for udim, frames in udims:
            udims_list.append((udim, self.unpack_frames(frames)))

        return udims_list

    @staticmethod
    def unpack_frames(frameranges):
        # does not support negative values
        frames = []
        for frame in frameranges:
            split = frame.split('-')
            if len(split) > 1:
                frames.extend(range(int(split[0]), int(split[1])+1))
            else:
                frames.append(int(frame))
        return frames


# Widgets Styles
