# file global_functions.py
# Global Functions Module

import subprocess
import os
import sys
import copy
import json
import zlib
import binascii
import collections
import side.qtawesome as qta
from lib.side.bs4 import BeautifulSoup
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from PySide import QtSvg
from environment import env_mode, env_tactic


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
            files_list.append(extract_filename(single))

    return dirs_list, files_list


def sequences_from_files(files_list):
    print(files_list)


def sequences_from_dirs(files_list):
    print(files_list)


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
            return [filename, 'No Ext', 'main', 'file']
        elif len(ext) > 1:
            return file_format(ext[-1])
    elif os.path.isdir(filename):
        return [filename, 'Folder', 'folder', 'folder']


def extract_filename(filename, no_ext=False):
    name = unicode(os.path.basename(filename)).split('.', 1)
    if len(name) > 1:
        if not no_ext:
            return name[0] + '.' + name[1]
        else:
            return name[0]
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
        effect.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
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
        color = QtGui.QColor(200, 200, 200)
    if not color_active:
        color_active = QtGui.QColor(240, 240, 240)
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


def add_snapshot_item(tree_widget, parent_widget, sobject, stype, process, snapshots, item_info, sep_versions=False,
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
                    key,
                    [versions],
                    item_info,
                    tree_item_versions,
                    parent_widget
                )
                add_item_to_tree(snapshot_item.tree_item, snapshot_item_versions.tree_item, snapshot_item_versions)

    return snapshots_items


def add_versions_snapshot_item(tree_widget, parent_widget, sobject, stype, process, context, snapshots, item_info):

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
    text_doc = QtGui.QTextDocument()
    text_doc.setHtml(html)
    plain_text = text_doc.toPlainText()[:strip]
    if len(plain_text) > strip - 1:
        plain_text += ' ...'

    return plain_text