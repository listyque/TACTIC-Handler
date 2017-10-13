# file global_functions.py
# Global Functions Module

import sys
import os
import subprocess
import copy
import ast
import json
import zlib
import binascii
import collections
import re
import traceback
import side.qtawesome as qta
from lib.side.bs4 import BeautifulSoup
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

from environment import env_mode, env_tactic
from side.pyseq import get_sequences


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

            stacktrace_handle(exception)

    return __tryexcept__


def stacktrace_handle(exception):

    expected = exception['exception']

    error_type = catch_error_type(expected)

    exception_text = u'{0}<p>{1}</p><p><b>Catched Error: {2}</b></p>'.format(
        unicode(str(expected.__doc__), 'utf-8', errors='ignore'),
        unicode(str(expected.message), 'utf-8', errors='ignore'),
        str(error_type))

    title = u'{0}'.format(unicode(str(expected.__doc__), 'utf-8', errors='ignore'))
    message = u'{0}<p>{1}</p>'.format(
        u"<p>Exception appeared:</p>",
        exception_text)
    buttons = [('Ok', QtGui.QMessageBox.AcceptRole)]

    reply = show_message_predefined(
        title=title,
        message=message,
        stacktrace=exception['stacktrace'],
        buttons=buttons,
        parent=None,
        message_type='warning',
    )
    if reply == QtGui.QMessageBox.YesRole:
        pass

    # return thread


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

        from lib.ui_classes import ui_misc_classes

        collapse_wdg = ui_misc_classes.Ui_collapsableWidget()
        collapse_wdg.setLayout(layout)
        collapse_wdg.setText('Hide Stacktrace')
        collapse_wdg.setCollapsedText('Show Stacktrace')
        collapse_wdg.setCollapsed(True)

        msb_layot = message_box.layout()

        # workaround for pyside2
        wdg_list = []

        for i in range(msb_layot.count()):
            wdg = msb_layot.itemAt(i).widget()
            if wdg:
                wdg_list.append(wdg)

        msb_layot.addWidget(wdg_list[0], 0, 0)
        msb_layot.addWidget(wdg_list[1], 0, 1)
        msb_layot.addWidget(wdg_list[2], 2, 1)
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

    if str(exception).find('object has no attribute') != -1:
        error = 'attribute_error'

    return error


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


def get_prc(prc, number):
    return int(prc * number / 100)


def sizes(size, precision=2):
    if size != '':
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


def html_to_hex(text_html):
    text_html_cmp = zlib.compress(text_html.encode('utf-8'), 9)
    text_html_hex = 'zlib:' + binascii.b2a_hex(text_html_cmp)
    if len(text_html_hex) > len(text_html):
        text_html_hex = text_html

    return text_html_hex


def hex_to_html(text_hex):
    if text_hex:
        detect_zlib = text_hex.rfind('zlib:')
        if detect_zlib == 0:
            hex_to_text = zlib.decompress(binascii.a2b_hex(text_hex[5:]))
        else:
            hex_to_text = text_hex

        return hex_to_text


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


def split_files_and_dirs(filename):
    dirs_list = []
    files_list = []
    for single in filename:
        if os.path.isdir(single):
            dirs_list.append(single)
        else:
            files_list.append(single)

    return dirs_list, files_list


def get_sequences_from_files(files_list):
    sequences = get_sequences(files_list)

    out_files = {
        'seq': [],
        'fl': []
    }

    for seq in sequences:
        if seq.length() > 1:
            out_files['seq'].append(seq)
        else:
            out_files['fl'].append(seq.path())

    return out_files


def get_udims_from_files(files_list):
    values_pattern = re.compile('u([0-9]+)_v([0-9]+)')
    # mari_values_pattern = re.compile('[_|.](([0-9][0-9])([0-9][0-9]))[.]')

    udims_dict = {
        'udim': collections.defaultdict(list),
        'noudim': []
    }

    for file in files_list:
        values_result = re.findall(values_pattern, file)
        # if not values_result:
        #     values_result = re.findall(mari_values_pattern, file)
        split_result = re.split(values_pattern, file)
        # print split_result, 'split_result'
        # print values_result, 'values_result'
        udim_collection = u'{0}u<>_v<>{1}'.format(split_result[0], split_result[-1])

        if values_result:
            udims_dict['udim'][udim_collection].append(split_result)
        else:
            udims_dict['noudim'].append(file)

    return udims_dict


def get_files_objects(items):
    udims_dict = get_udims_from_files(items)
    sequence_items = get_sequences_from_files(udims_dict['noudim'])
    print sequence_items
    nosequence_items = sequence_items.get('fl')
    sequence_items = sequence_items.get('seq')
    udim_items = udims_dict['udim']

    out_dict = {
        'seq': [],
        'fl': [],
        'udim': [],
    }

    for seq in sequence_items:
        file_obj = FileObject(seq)
        file_obj.init_as_sequence()
        out_dict['seq'].append(file_obj)

    for fl in nosequence_items:
        file_obj = FileObject(fl)
        file_obj.init_as_file()
        out_dict['fl'].append(file_obj)

    for name, udim in udim_items.items():
        file_obj = FileObject((name, udim))
        file_obj.init_as_udim()
        out_dict['udim'].append(file_obj)

    return out_dict


def file_format(ext):
    formats = {
        'ma': ['ma', 'mayaAscii', 'maya', 'file'],
        'mb': ['mb', 'mayaBinary', 'maya', 'file'],
        'hip': ['hip', 'Houdini', 'houdini', 'file'],
        '3b': ['3b', '3D-Coat', 'coat', 'file'],
        'max': ['max', '3DSMax scene', 'max', 'file'],
        'scn': ['scn', 'Softimage XSI', 'xsi', 'file'],
        'mud': ['mud', 'Mudbox', 'mudbox', 'file'],
        'abc': ['abc', 'Alembic', 'cache', 'file'],
        'obj': ['obj', 'OBJ', 'obj', 'file'],
        '3ds': ['3ds', '3DSMax model', 'obj', 'file'],
        'nk': ['nk', 'Nuke', 'nuke', 'file'],
        'fbx': ['fbx', 'FBX', 'obj', 'file'],
        'dae': ['dae', 'COLLADA', 'cache', 'file'],
        'rs': ['rs', 'Redshift Proxy', 'cache', 'file'],
        'vdb': ['vdb', 'Open VDB', 'cache', 'file'],
        'jpg': ['jpg', 'JPEG Image', 'image', 'preview'],
        'jpeg': ['jpeg', 'JPEG Image', 'image', 'preview'],
        'psd': ['psd', 'Photoshop PSD', 'image', 'file'],
        'tif': ['tif', 'TIFF Image', 'image', 'preview'],
        'tiff': ['tiff', 'TIFF Image', 'image', 'preview'],
        'png': ['png', 'PNG Image', 'image', 'preview'],
        'tga': ['tga', 'TARGA Image', 'image', 'file'],
        'exr': ['exr', 'EXR Image', 'image', 'file'],
        'hdr': ['hdr', 'HDR Image', 'image', 'file'],
        'dpx': ['dpx', 'DPX Image', 'image', 'file'],
        'mov': ['mov', 'MOV Animation', 'movie', 'file'],
        'avi': ['avi', 'AVI Animation', 'movie', 'file'],
    }
    low_case_ext = ext.lower()
    if low_case_ext in formats.keys():
        return formats[low_case_ext]
    else:
        return [low_case_ext, low_case_ext, 'main', 'file']


def get_ext(file_name):
    # func for possible future needs
    return file_name.split('.', -1)[-1]


def extract_extension(filename):
    base_filename = unicode(os.path.basename(filename))
    ext = base_filename.split('.', -1)
    if not os.path.isdir(filename):
        if base_filename == ext[0]:
            return ['', 'No Ext', 'main', 'file']
        elif len(ext) > 1:
            return file_format(ext[-1])
    elif os.path.isdir(filename):
        return ['', 'Folder', 'folder', 'folder']


def extract_filename(filename, no_ext=False):
    name = unicode(os.path.basename(filename)).split('.')
    if len(name) > 1:
        if no_ext:
            return u''.join(name[:-1])
        else:
            return u'.'.join(name)
    else:
        return name[0]


def extract_dirname(filename):
    dir = unicode(os.path.realpath(filename)).split('.', 1)
    if dir[0] == filename:
        return os.path.dirname(filename)
    if len(dir) == 1 and not os.path.isdir(filename):
        return dir[0]
    else:
        return os.path.dirname(filename)


def minify_code(source, pack=False):
    import side.pyminifier as pyminifier
    cleanup_comments = pyminifier.minification.remove_comments_and_docstrings(source)
    cleanup_blanks = pyminifier.minification.remove_blank_lines(cleanup_comments)
    multi_line = pyminifier.minification.join_multiline_pairs(cleanup_blanks)
    dedent = pyminifier.minification.dedent(multi_line)
    reduce_op = pyminifier.minification.reduce_operators(dedent)
    if pack:
        return pyminifier.compression.gz_pack(reduce_op)
    else:
        return reduce_op


def get_ver_rev(ver, rev):
    if ver > 0 and rev > 0:
        result = '<span style="color:#008498;">Ver: {0:03d};</span><span style="color:#0a9800;"> Rev: {1:03d}</span>'.format(
            ver,
            rev)
    elif ver > 0 and rev == 0:
        result = '<span style="color:#008498;">Ver: {0:03d}</span>'.format(ver, rev)
    else:
        result = ''

    return result


def group_dict_by(dicts_list, group_by):
    grouped = collections.defaultdict(list)
    for dic in dicts_list:
        grouped[dic.get(group_by)].append(dic)

    return grouped


def get_controls_dict(ignore_list=None):
    controls_dict = {
        'QLineEdit': {'obj_name': [], 'value': []},
        'QCheckBox': {'obj_name': [], 'value': []},
        'QComboBox': {'obj_name': [], 'value': []},
        'QTreeWidget': {'obj_name': [], 'value': []},
        'QToolButton': {'obj_name': [], 'value': []},
        'QRadioButton': {'obj_name': [], 'value': []},
        'QGroupBox': {'obj_name': [], 'value': []},
        'QSpinBox': {'obj_name': [], 'value': []},
    }
    if ignore_list:
        for item in ignore_list:
            if item == QtGui.QLineEdit:
                controls_dict.pop('QLineEdit')
            if item == QtGui.QCheckBox:
                controls_dict.pop('QCheckBox')
            if item == QtGui.QComboBox:
                controls_dict.pop('QComboBox')
            if item == QtGui.QTreeWidget:
                controls_dict.pop('QTreeWidget')
            if item == QtGui.QToolButton:
                controls_dict.pop('QToolButton')
            if item == QtGui.QRadioButton:
                controls_dict.pop('QRadioButton')
            if item == QtGui.QGroupBox:
                controls_dict.pop('QGroupBox')
            if item == QtGui.QGroupBox:
                controls_dict.pop('QSpinBox')

    return copy.deepcopy(controls_dict)


def get_value_from_config(config_dict, control, control_type=None):
    # if control_type:
    #     config_dict = {'key': config_dict[control_type]}
    # print config_dict
    if config_dict:
        for all_values in config_dict.itervalues():
            # print all_values
            for obj_name, value in zip(all_values['obj_name'], all_values['value']):
                if control == obj_name:
                    return value


def walk_through_layouts(args=None, ignore_list=None):
    all_widgets = []
    if not ignore_list:
        ignore_list = []
    for layout in args:
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if type(widget) not in ignore_list:
                all_widgets.append(layout.itemAt(i).widget())

    return all_widgets


def clear_property_dict(in_dict):
    # clearing all dict
    for i in in_dict.itervalues():
        for val in i.itervalues():
            val[:] = []


def campare_dicts(dict_one, dict_two):
    result = True

    for key, val in dict_one.iteritems():
        for key1, val1 in dict_two.iteritems():
            if key == key1:
                for i, j in enumerate(val['value']):
                    if j != val1['value'][i]:
                        result = False
                        break

    return result


def store_property_by_widget_type(widget, in_dict):
    if isinstance(widget, QtGui.QLineEdit):
        if not in_dict.get('QLineEdit'):
            in_dict['QLineEdit'] = {'value': [], 'obj_name': []}
        in_dict['QLineEdit']['value'].append(str(widget.text()))
        in_dict['QLineEdit']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QCheckBox):
        if not in_dict.get('QCheckBox'):
            in_dict['QCheckBox'] = {'value': [], 'obj_name': []}
        in_dict['QCheckBox']['value'].append(int(bool(widget.checkState())))
        in_dict['QCheckBox']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QComboBox):
        if not in_dict.get('QComboBox'):
            in_dict['QComboBox'] = {'value': [], 'obj_name': []}
        in_dict['QComboBox']['value'].append(int(widget.currentIndex()))
        in_dict['QComboBox']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QTreeWidget):
        if not in_dict.get('QTreeWidget'):
            in_dict['QTreeWidget'] = {'value': [], 'obj_name': []}
        in_dict['QTreeWidget']['value'].append(int(widget.topLevelItemCount()))
        in_dict['QTreeWidget']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QToolButton):
        if not in_dict.get('QToolButton'):
            in_dict['QToolButton'] = {'value': [], 'obj_name': []}
        in_dict['QToolButton']['value'].append(str(widget.styleSheet()))
        in_dict['QToolButton']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QGroupBox):
        if not in_dict.get('QGroupBox'):
            in_dict['QGroupBox'] = {'value': [], 'obj_name': []}
        in_dict['QGroupBox']['value'].append(int(bool(widget.isChecked())))
        in_dict['QGroupBox']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QRadioButton):
        if not in_dict.get('QRadioButton'):
            in_dict['QRadioButton'] = {'value': [], 'obj_name': []}
        in_dict['QRadioButton']['value'].append(int(bool(widget.isChecked())))
        in_dict['QRadioButton']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QSpinBox):
        if not in_dict.get('QSpinBox'):
            in_dict['QSpinBox'] = {'value': [], 'obj_name': []}
        in_dict['QSpinBox']['value'].append(int(widget.value()))
        in_dict['QSpinBox']['obj_name'].append(widget.objectName())


def change_property_by_widget_type(widget, in_dict):
    if isinstance(widget, QtGui.QLineEdit) and in_dict.get('QLineEdit'):
        if widget.objectName() in in_dict['QLineEdit']['obj_name']:
            val = in_dict['QLineEdit']['value'][in_dict['QLineEdit']['obj_name'].index(widget.objectName())]
            widget.setText(val)
            # for name, val in zip(in_dict['QLineEdit']['obj_name'], in_dict['QLineEdit']['value']):
            #     if widget.objectName() == name:
            #         widget.setText(val)
            #         break

    elif isinstance(widget, QtGui.QCheckBox) and in_dict.get('QCheckBox'):
        if widget.objectName() in in_dict['QCheckBox']['obj_name']:
            val = in_dict['QCheckBox']['value'][in_dict['QCheckBox']['obj_name'].index(widget.objectName())]
            widget.setChecked(val)
        # for name, val in zip(in_dict['QCheckBox']['obj_name'], in_dict['QCheckBox']['value']):
        #     if widget.objectName() == name:
        #         widget.setChecked(val)
        #         break

    elif isinstance(widget, QtGui.QGroupBox) and in_dict.get('QGroupBox'):
        if widget.objectName() in in_dict['QGroupBox']['obj_name']:
            val = in_dict['QGroupBox']['value'][in_dict['QGroupBox']['obj_name'].index(widget.objectName())]
            widget.setChecked(val)
        # for name, val in zip(in_dict['QGroupBox']['obj_name'], in_dict['QGroupBox']['value']):
        #     if widget.objectName() == name:
        #         widget.setChecked(val)
        #         break

    elif isinstance(widget, QtGui.QRadioButton) and in_dict.get('QRadioButton'):
        if widget.objectName() in in_dict['QRadioButton']['obj_name']:
            val = in_dict['QRadioButton']['value'][in_dict['QRadioButton']['obj_name'].index(widget.objectName())]
            widget.setChecked(val)
        # for name, val in zip(in_dict['QRadioButton']['obj_name'], in_dict['QRadioButton']['value']):
        #     if widget.objectName() == name:
        #         widget.setChecked(val)
        #         break

    elif isinstance(widget, QtGui.QSpinBox) and in_dict.get('QSpinBox'):
        if widget.objectName() in in_dict['QSpinBox']['obj_name']:
            val = in_dict['QSpinBox']['value'][in_dict['QSpinBox']['obj_name'].index(widget.objectName())]
            widget.setValue(int(val))
        # for name, val in zip(in_dict['QSpinBox']['obj_name'], in_dict['QSpinBox']['value']):
        #     if widget.objectName() == name:
        #         widget.setValue(int(val))
        #         break

    elif isinstance(widget, QtGui.QComboBox) and in_dict.get('QComboBox'):
        if widget.objectName() in in_dict['QComboBox']['obj_name']:
            val = in_dict['QComboBox']['value'][in_dict['QComboBox']['obj_name'].index(widget.objectName())]
            widget.setCurrentIndex(int(val))

    elif isinstance(widget, QtGui.QToolButton) and in_dict.get('QToolButton'):
        if widget.objectName() in in_dict['QToolButton']['obj_name']:
            val = in_dict['QToolButton']['value'][in_dict['QToolButton']['obj_name'].index(widget.objectName())]
            widget.setStyleSheet(val)


def dockwidget_area_to_str(main_window, dockwidget):
    if main_window.dockWidgetArea(dockwidget) == QtCore.Qt.TopDockWidgetArea:
        return 'top'
    if main_window.dockWidgetArea(dockwidget) == QtCore.Qt.BottomDockWidgetArea:
        return 'bottom'
    if main_window.dockWidgetArea(dockwidget) == QtCore.Qt.LeftDockWidgetArea:
        return 'left'
    if main_window.dockWidgetArea(dockwidget) == QtCore.Qt.RightDockWidgetArea:
        return 'right'


def str_to_dockwidget_area(area):
    if area == 'top':
        return QtCore.Qt.TopDockWidgetArea
    elif area == 'bottom':
        return QtCore.Qt.BottomDockWidgetArea
    elif area == 'left':
        return QtCore.Qt.LeftDockWidgetArea
    elif area == 'right':
        return QtCore.Qt.RightDockWidgetArea


def toolbar_area_to_str(main_window, toolbar):
    if main_window.toolBarArea(toolbar) == QtCore.Qt.TopToolBarArea:
        return 'top'
    elif main_window.toolBarArea(toolbar) == QtCore.Qt.BottomToolBarArea:
        return 'bottom'
    elif main_window.toolBarArea(toolbar) == QtCore.Qt.LeftToolBarArea:
        return 'left'
    elif main_window.toolBarArea(toolbar) == QtCore.Qt.RightToolBarArea:
        return 'right'


def str_to_toolbar_area(area):
    if area == 'top':
        return QtCore.Qt.TopToolBarArea
    elif area == 'bottom':
        return QtCore.Qt.BottomToolBarArea
    elif area == 'left':
        return QtCore.Qt.LeftToolBarArea
    elif area == 'right':
        return QtCore.Qt.RightToolBarArea


def store_dict_values(widgets, out_dict, parent):
    clear_property_dict(out_dict)
    for widget in widgets:
        if isinstance(widget,
                      (QtGui.QLineEdit,
                       QtGui.QCheckBox,
                       QtGui.QComboBox,
                       QtGui.QTreeWidget,
                       QtGui.QToolButton,
                       QtGui.QRadioButton,
                       QtGui.QGroupBox,
                       QtGui.QSpinBox,)):
            store_property_by_widget_type(widget, out_dict)
            widget.installEventFilter(parent)


def apply_dict_values(widgets, in_dict):
    for widget in widgets:
        if isinstance(widget,
                      (QtGui.QLineEdit,
                       QtGui.QCheckBox,
                       QtGui.QComboBox,
                       QtGui.QTreeWidget,
                       QtGui.QToolButton,
                       QtGui.QRadioButton,
                       QtGui.QGroupBox,
                       QtGui.QSpinBox,)):
            change_property_by_widget_type(widget, in_dict)


def collect_defaults(defaults_dict=None, init_dict=None, layouts_list=None, get_values=False, apply_values=False,
                     store_defaults=False, undo_changes=False, parent=None, ignore_list=None):
    widgets = walk_through_layouts(layouts_list, ignore_list)

    if not init_dict:
        init_dict = get_controls_dict(ignore_list)

    if undo_changes:
        apply_dict_values(widgets, defaults_dict)

    if apply_values:
        apply_dict_values(widgets, init_dict)

    if get_values:
        store_dict_values(widgets, init_dict, parent)

    if store_defaults:
        store_dict_values(widgets, defaults_dict, parent)

    if not defaults_dict:
        defaults_dict = get_controls_dict(ignore_list)
        store_dict_values(widgets, defaults_dict, parent)

    return defaults_dict, init_dict


def create_tab_label(tab_name, stype):
    tab_label = QtGui.QLabel(tab_name)
    tab_label.setAlignment(QtCore.Qt.AlignCenter)
    tab_color = stype.info['color']
    if tab_color:
        effect = QtGui.QGraphicsDropShadowEffect(tab_label)
        t_c = hex_to_rgb(tab_color, alpha=8, tuple=True)
        effect.setOffset(2, 2)
        effect.setColor(Qt4Gui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
        effect.setBlurRadius(8)
        tab_label.setGraphicsEffect(effect)

        tab_color_rgb = hex_to_rgb(tab_color, alpha=20)
        tab_label.setStyleSheet('QLabel {' +
                                'background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 0), stop:0.2 {0}, stop:0.8 {0}, stop:1 rgba(0, 0, 0, 0));'.format(
                                    tab_color_rgb) +
                                '}')
    return tab_label


def get_icon(icon_name, icon_name_active=None, color=None, color_active=None, icons_set='fa', **kwargs):

    if not color:
        color = Qt4Gui.QColor(200, 200, 200)
    if not color_active:
        color_active = Qt4Gui.QColor(240, 240, 240)
    if not icon_name_active:
        icon_name_active = icon_name
    styling_icon = qta.icon(
        '{0}.{1}'.format(icons_set, icon_name),
        active='{0}.{1}'.format(icons_set, icon_name_active),
        color=color,
        color_active=color_active,
        **kwargs)

    return styling_icon


# New QTreeWidget funcs

def add_item_to_tree(tree_widget, tree_item, tree_item_widget=None, insert_pos=None):
    if type(tree_widget) == QtGui.QTreeWidget:
        if insert_pos is not None:
            tree_widget.insertTopLevelItem(insert_pos, tree_item)
        else:
            tree_widget.addTopLevelItem(tree_item)
        if tree_item_widget:
            tree_widget.setItemWidget(tree_item, 0, tree_item_widget)
    else:
        if insert_pos is not None:
            tree_widget.insertChild(insert_pos, tree_item)
        else:
            tree_widget.addChild(tree_item)
        if tree_item_widget:
            tree_widget.treeWidget().setItemWidget(tree_item, 0, tree_item_widget)


def add_sobject_item(parent_item, parent_widget, sobject, stype, item_info, insert_pos=None, ignore_dict=None):
    from lib.ui_classes.ui_item_classes import Ui_itemWidget

    tree_item = QtGui.QTreeWidgetItem()
    item_info = {
        'relates_to': item_info['relates_to'],
        'is_expanded': False,
        'sep_versions': item_info['sep_versions']
    }

    tree_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
    tree_item_widget = Ui_itemWidget(sobject, stype, item_info, tree_item, ignore_dict, parent_widget)

    add_item_to_tree(parent_item, tree_item, tree_item_widget, insert_pos=insert_pos)

    return tree_item_widget


def add_process_item(tree_widget, parent_widget, sobject, stype, process, item_info, insert_pos=None, pipeline=None):
    from lib.ui_classes.ui_item_classes import Ui_processItemWidget

    tree_item = QtGui.QTreeWidgetItem()
    item_info = {
        'relates_to': item_info['relates_to'],
        'is_expanded': False,
        'sep_versions': item_info['sep_versions']
    }

    tree_item_widget = Ui_processItemWidget(sobject, stype, process, item_info, tree_item, pipeline, parent_widget)

    add_item_to_tree(tree_widget, tree_item, tree_item_widget, insert_pos=insert_pos)

    return tree_item_widget


def add_snapshot_item(tree_widget, parent_widget, sobject, stype, process, pipeline, snapshots, item_info, sep_versions=False,
                      insert_at_top=True):
    from lib.ui_classes.ui_item_classes import Ui_snapshotItemWidget

    snapshots_items = []

    for key, context in snapshots.contexts.iteritems():
        tree_item = QtGui.QTreeWidgetItem()
        item_info = {
            'relates_to': item_info['relates_to'],
            'is_expanded': False,
            'sep_versions': item_info['sep_versions']
        }
        snapshot_item = Ui_snapshotItemWidget(
            sobject,
            stype,
            process,
            pipeline,
            key,
            context.versionless.values(),
            item_info,
            tree_item,
            parent_widget
        )

        insert_pos = 0
        if insert_at_top:
            add_item_to_tree(tree_widget, snapshot_item.tree_item, snapshot_item, insert_pos)
        else:
            add_item_to_tree(tree_widget, snapshot_item.tree_item, snapshot_item)

        snapshots_items.append(snapshot_item)

        if not sep_versions:
            for versions in context.versions.itervalues():
                tree_item_versions = QtGui.QTreeWidgetItem()
                item_info = {
                    'relates_to': item_info['relates_to'],
                    'is_expanded': False,
                    'sep_versions': item_info['sep_versions']
                }
                snapshot_item_versions = Ui_snapshotItemWidget(
                    sobject,
                    stype,
                    process,
                    pipeline,
                    key,
                    [versions],
                    item_info,
                    tree_item_versions,
                    parent_widget
                )
                add_item_to_tree(snapshot_item.tree_item, snapshot_item_versions.tree_item, snapshot_item_versions)

    return snapshots_items


def add_versions_snapshot_item(tree_widget, parent_widget, sobject, stype, process, pipeline, context, snapshots, item_info):

    from lib.ui_classes.ui_item_classes import Ui_snapshotItemWidget

    for key, snapshot in snapshots.iteritems():
        tree_item = QtGui.QTreeWidgetItem()
        item_info = {
            'relates_to': item_info['relates_to'],
            'is_expanded': False,
            'sep_versions': item_info['sep_versions']
        }
        snapshot_item = Ui_snapshotItemWidget(
            sobject,
            stype,
            process,
            pipeline,
            context,
            [snapshot],
            item_info,
            tree_item,
            parent_widget
        )

        add_item_to_tree(tree_widget, snapshot_item.tree_item, snapshot_item)


def add_child_item(tree_widget, parent_widget, sobject, stype, child, item_info):
    from lib.ui_classes.ui_item_classes import Ui_childrenItemWidget

    tree_item = QtGui.QTreeWidgetItem()
    item_info = {
        'relates_to': item_info['relates_to'],
        'is_expanded': False,
        'sep_versions': item_info['sep_versions']
    }
    tree_item_widget = Ui_childrenItemWidget(sobject, stype, child, item_info, tree_item, parent_widget)

    add_item_to_tree(tree_widget, tree_item, tree_item_widget)

    return tree_item_widget


def expand_to_snapshot(parent, tree_widget):
    # TODO make it infinite
    top_item = tree_widget.topLevelItem(0)
    skey_context = parent.go_by_skey[1]['context']
    skey_process = skey_context.split('/')[0]
    skey_code = parent.go_by_skey[1].get('item_code')

    if skey_context and top_item:
        top_item.setExpanded(True)

        for i in range(top_item.childCount()):
            process_title = top_item.child(i).text(0)
            if process_title == skey_process:
                process_item = top_item.child(i)
                process_item.setExpanded(True)
                for j in range(process_item.childCount()):
                    child_item = process_item.child(j)
                    child_widget = tree_widget.itemWidget(child_item, 0)
                    if child_widget.snapshot['context'] == skey_context:
                        child_item.setExpanded(True)
                        child_item.setSelected(True)
                        for k in range(child_item.childCount()):
                            last_item = child_item.child(k)
                            last_widget = tree_widget.itemWidget(last_item, 0)
                            if last_widget.snapshot['code'] == skey_code:
                                child_item.setSelected(False)
                                last_item.setSelected(True)
                                tree_widget.scrollToItem(child_item)


def tree_state(wdg, state_dict):
    """ Recursive getting data from each tree item"""

    if type(wdg) == QtGui.QTreeWidget:
        lv = wdg.topLevelItemCount()
        for i in range(lv):
            item = wdg.topLevelItem(i)
            d = {
                'd': {'s': item.isSelected(), 'e': item.isExpanded()},
                's': {}
            }
            if item.childCount() > 0:
                tree_state(item, d)
            state_dict[i] = d
    else:
        lv = wdg.childCount()
        for i in range(lv):
            item = wdg.child(i)
            d = {
                'd': {'s': item.isSelected(), 'e': item.isExpanded()},
                's': {}
            }
            if item.childCount() > 0:
                tree_state(item, d)
            state_dict['s'][i] = d

    return state_dict


def tree_state_revert(wdg, state_dict):
    """ Recursive setting data to each tree item"""

    if type(wdg) == QtGui.QTreeWidget:
        lv = wdg.topLevelItemCount()
        tree_item = wdg.topLevelItem
        tree_wdg = wdg
    else:
        lv = wdg.childCount()
        tree_item = wdg.child
        tree_wdg = wdg.treeWidget()

    for i in range(lv):
        if state_dict.get(i):
            item = tree_item(i)
            item_widget = tree_wdg.itemWidget(item, 0)
            item_widget.set_expand_state(state_dict[i]['d']['e'])
            item_widget.set_selected_state(state_dict[i]['d']['s'])
            item_widget.set_children_states(state_dict[i]['s'])
            if item.childCount() > 0:
                tree_state_revert(item, state_dict[i]['s'])
            # Scrolling to item
            if item.isSelected():
                tree_wdg.scrollToItem(item)


# files etc routine
def open_file_associated(filepath):
    # TODO message if file not exists
    # if sys.platform.startswith('darwin'):
    #     subprocess.call(('open', filepath))
    if filepath:
        if env_mode.get_platform() == 'Linux':
            subprocess.call(('xdg-open', filepath))
        else:
            os.startfile(filepath)


def form_path(path):
    if env_mode.get_platform() == 'Linux':
        formed_path = path.replace('\\', '/').replace('\\\\', '/').replace('//', '/')
    else:
        formed_path = path.replace('\\', '/')
        # return formed_path
    # else:
    #     formed_path = path.replace('\\', '/').replace('//', '/')
    return formed_path


def get_st_size(file_path):
    from stat import ST_SIZE
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


def simplify_html(html, pretty=False):
    soup = BeautifulSoup(html, "html.parser")
    if pretty:
        return unicode(soup.body.prettify())
    else:
        return unicode(soup.body)


def to_plain_text(html, strip=80):
    text_doc = Qt4Gui.QTextDocument()
    text_doc.setHtml(html)
    plain_text = text_doc.toPlainText()[:strip]
    if len(plain_text) > strip - 1:
        plain_text += ' ...'

    return plain_text


# CLASSES #


class FileObject(object):
    def __init__(self, file_):

        self._file = file_
        self._type = None
        self._file_type = None
        self._files_list = []
        self._file_path = None
        self._file_name = None
        self._pretty_file_name = None
        self._file_ext = None
        self._base_file_type_pretty_name = None
        self._base_file_type = None
        self._tactic_file_type = None
        self._sequence_length = None
        self._sequence_frames = None
        self._sequence_padding = None
        self._sequence_start = None
        self._sequence_end = None
        self._sequence_missing_frames = None

        self._udim_tiles_count = None
        self._udim_tiles = None

    def init_as_sequence(self):
        """ Init as sequence file object
            This i very basic wrap for pyseq.Sequence """
        self.set_type('seq')
        self.set_file_path(self._file.directory())
        self.set_file_name(self._file.head())
        self.set_pretty_file_name(self._file.format('%h%r%t'))

        for seq in self._file:
            full_path = u'{0}{1}'.format(self.get_file_path(), seq)
            self._files_list.append(full_path)

        self.set_file_type(extract_extension(self._files_list[0]))

        file_type = self.get_file_type()

        self.set_file_ext(file_type[0])
        self.set_base_file_type_pretty_name(file_type[1])
        self.set_base_file_type('sequence')
        self.set_tactic_file_type(file_type[3])

        self.set_sequence_frames(self._file.frames())
        self.set_sequence_padding(self._file._get_padding())
        self.set_sequence_length(self._file.size)
        self.set_sequence_start(self._file.start())
        self.set_sequence_end(self._file.end())
        self.set_sequence_missing_frames(self._file.missing())

    def init_as_file(self):
        """ Init as sequence file object
            This i very basic wrap for pyseq.Sequence, without any sequences"""
        self.set_type('fl')
        self.set_file_path(extract_dirname(self._file))
        self.set_pretty_file_name(extract_filename(self._file))
        self.set_file_name(extract_filename(self._file, no_ext=True))

        self._files_list.append(self._file)

        self.set_file_type(extract_extension(self._file))

        file_type = self.get_file_type()

        self.set_file_ext(file_type[0])
        self.set_base_file_type_pretty_name(file_type[1])
        self.set_base_file_type(file_type[2])
        self.set_tactic_file_type(file_type[3])

    def init_as_udim(self):
        """ Init as sequence file object"""
        self.set_type('udim')

        self.set_file_path(extract_dirname(self._file[0]))
        self.set_pretty_file_name(extract_filename(self._file[0]))

        udim_tiles = []

        for fl in self._file[1]:
            full_path = u'{0}u{1}_v{2}{3}'.format(*fl)
            self._files_list.append(full_path)
            udim_tile = '.'.join(fl[1:3])
            udim_tiles.append(udim_tile)

        self.set_file_type(extract_extension(self._files_list[0]))
        self.set_file_name(extract_filename(self._file[1][0][0], no_ext=True))

        file_type = self.get_file_type()

        self.set_file_ext(file_type[0])
        self.set_base_file_type_pretty_name(file_type[1])
        self.set_base_file_type('udim')
        self.set_tactic_file_type(file_type[3])

        self.set_udim_tiles_count(len(self._files_list))
        self.set_udim_tiles(udim_tiles)

    def get_metadata(self):
        metadata_dict = {

        }
        return metadata_dict

    def get_type(self):
        return self._type

    def set_type(self, type_):
        self._type = type_

    def get_file_type(self):
        return self._file_type

    def set_file_type(self, file_type_):
        self._file_type = file_type_

    def get_file_path(self):
        return self._file_path

    def set_file_path(self, path_):
        self._file_path = path_

    def get_all_files_list(self, first=False):
        if first:
            return self._files_list[0]
        else:
            return self._files_list

    def set_all_files_list(self, files_list_):
        self._files_list = files_list_

    def get_file_name(self):
        return self._file_name

    def set_file_name(self, name_):
        self._file_name = name_

    def get_pretty_file_name(self):
        return self._pretty_file_name

    def set_pretty_file_name(self, pretty_name_):
        self._pretty_file_name = pretty_name_

    def get_file_ext(self):
        return self._file_ext

    def set_file_ext(self, ext_):
        self._file_ext = ext_

    def get_base_file_type_pretty_name(self):
        return self._base_file_type_pretty_name

    def set_base_file_type_pretty_name(self, base_file_type_pretty_name_):
        self._base_file_type_pretty_name = base_file_type_pretty_name_

    def get_base_file_type(self):
        return self._base_file_type

    def set_base_file_type(self, base_file_type_):
        self._base_file_type = base_file_type_

    def get_tactic_file_type(self):
        return self._tactic_file_type

    def set_tactic_file_type(self, tactic_file_type_):
        self._tactic_file_type = tactic_file_type_

    def get_sequence_framerange(self):
        return self._file._get_framerange(self.get_sequence_frames())

    def get_sequence_frames(self):
        return self._sequence_frames

    def set_sequence_frames(self, sequence_frames_):
        self._sequence_frames = sequence_frames_

    def get_sequence_padding(self):
        return self._sequence_padding

    def set_sequence_padding(self, sequence_padding_):
        self._sequence_padding = sequence_padding_

    def get_sequence_lenght(self):
        return self._sequence_length

    def set_sequence_length(self, sequence_length_):
        self._sequence_length = sequence_length_

    def get_sequence_start(self):
        return self._sequence_start

    def set_sequence_start(self, sequence_start_):
        self._sequence_start = sequence_start_

    def get_sequence_end(self):
        return self._sequence_end

    def set_sequence_end(self, sequence_end_):
        self._sequence_end = sequence_end_

    def get_sequence_missing_frames(self):
        return self._sequence_missing_frames

    def set_sequence_missing_frames(self, sequence_missing_frames_):
        self._sequence_missing_frames = sequence_missing_frames_

    def get_udim_tiles_count(self):
        return self._udim_tiles_count

    def set_udim_tiles_count(self, udim_tiles_count_):
        self._udim_tiles_count = udim_tiles_count_

    def get_udim_tiles(self):
        return self._udim_tiles

    def set_udim_tiles(self, udim_tiles_):
        self._udim_tiles = udim_tiles_

    def open_file(self):
        open_file_associated(self.get_all_files_list()[0])

    def open_folder(self):
        open_file_associated(self.get_file_path())
