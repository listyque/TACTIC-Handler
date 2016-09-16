# file global_functions.py
# Global Functions Module
import subprocess
import os
import sys
import copy
import zlib
import binascii
import collections
from lib.side.bs4 import BeautifulSoup

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import environment as env


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
        # size = size / 1024.0

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

    return copy.deepcopy(controls_dict)


def get_value_from_config(config_dict, control, control_type=None):
    if control_type:
        config_dict = dict(key=config_dict[control_type])
    for all_values in config_dict.itervalues():
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
        in_dict['QLineEdit']['value'].append(str(widget.text()))
        in_dict['QLineEdit']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QCheckBox):
        in_dict['QCheckBox']['value'].append(int(bool(widget.checkState())))
        in_dict['QCheckBox']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QComboBox):
        in_dict['QComboBox']['value'].append(int(widget.count()))
        in_dict['QComboBox']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QTreeWidget):
        in_dict['QTreeWidget']['value'].append(int(widget.topLevelItemCount()))
        in_dict['QTreeWidget']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QToolButton):
        in_dict['QToolButton']['value'].append(str(widget.styleSheet()))
        in_dict['QToolButton']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QGroupBox):
        in_dict['QGroupBox']['value'].append(int(bool(widget.isChecked())))
        in_dict['QGroupBox']['obj_name'].append(widget.objectName())

    if isinstance(widget, QtGui.QRadioButton):
        in_dict['QRadioButton']['value'].append(int(bool(widget.isChecked())))
        in_dict['QRadioButton']['obj_name'].append(widget.objectName())


def change_property_by_widget_type(widget, in_dict):
    if isinstance(widget, QtGui.QLineEdit):
        for name, val in zip(in_dict['QLineEdit']['obj_name'], in_dict['QLineEdit']['value']):
            if widget.objectName() == name:
                widget.setText(val)

    if isinstance(widget, QtGui.QCheckBox):
        for name, val in zip(in_dict['QCheckBox']['obj_name'], in_dict['QCheckBox']['value']):
            if widget.objectName() == name:
                widget.setChecked(val)

    if isinstance(widget, QtGui.QGroupBox):
        for name, val in zip(in_dict['QGroupBox']['obj_name'], in_dict['QGroupBox']['value']):
            if widget.objectName() == name:
                widget.setChecked(val)

    if isinstance(widget, QtGui.QRadioButton):
        for name, val in zip(in_dict['QRadioButton']['obj_name'], in_dict['QRadioButton']['value']):
            if widget.objectName() == name:
                widget.setChecked(val)


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
                       QtGui.QGroupBox)):
            store_property_by_widget_type(widget, out_dict)
            widget.installEventFilter(parent)


def apply_dict_values(widgets, in_dict):
    for widget in widgets:
        # print widget
        # print isinstance(widget, QtGui.QToolButton)
        if isinstance(widget,
                      (QtGui.QLineEdit,
                       QtGui.QCheckBox,
                       QtGui.QComboBox,
                       QtGui.QTreeWidget,
                       QtGui.QToolButton,
                       QtGui.QRadioButton,
                       QtGui.QGroupBox)):
            change_property_by_widget_type(widget, in_dict)


def collect_defaults(defaults_dict=None, init_dict=None, layouts_list=None, get_values=False, apply_values=False,
                     store_defaults=False, undo_changes=False, parent=None, ignore_list=None):
    widgets = walk_through_layouts(layouts_list, ignore_list)

    if undo_changes:
        apply_dict_values(widgets, defaults_dict)

    if apply_values:
        apply_dict_values(widgets, init_dict)

    if get_values:
        store_dict_values(widgets, init_dict, parent)

    if store_defaults:
        store_dict_values(widgets, defaults_dict, parent)

    if not defaults_dict:
        # defaults_dict = copy.deepcopy(controls_dict)
        defaults_dict = get_controls_dict(ignore_list)
        store_dict_values(widgets, defaults_dict, parent)

    if not init_dict:
        # init_dict = copy.deepcopy(controls_dict)
        init_dict = get_controls_dict(ignore_list)

    return defaults_dict, init_dict


def create_tab_label(tab_name, stype):
    tab_label = QtGui.QLabel(tab_name)
    tab_label.setAlignment(QtCore.Qt.AlignCenter)
    tab_color = stype.info['color']
    if tab_color:
        effect = QtGui.QGraphicsDropShadowEffect(tab_label)
        t_c = hex_to_rgb(tab_color, alpha=255, tuple=True)
        effect.setOffset(1, 1)
        effect.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
        effect.setBlurRadius(20)
        tab_label.setGraphicsEffect(effect)

        tab_color_rgb = hex_to_rgb(tab_color, alpha=8)
        tab_label.setStyleSheet('QLabel {' +
                                'background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 0), stop:0.2 {0}, stop:0.8 {0}, stop:1 rgba(0, 0, 0, 0));'.format(
                                    tab_color_rgb) +
                                '}')
    return tab_label


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


def add_sobject_item(parent_item, parent_widget, sobject, stype, process, item_info):
    from lib.ui_classes.ui_item_classes import Ui_itemWidget

    tree_item = QtGui.QTreeWidgetItem()
    tree_item_widget = Ui_itemWidget(sobject, stype, item_info, tree_item, parent_widget)

    add_item_to_tree(parent_item, tree_item, tree_item_widget)

    # adding child items
    child_items = []
    if tree_item_widget.children_stypes:
        for child in tree_item_widget.children_stypes:
            child_stype = parent_widget.project.stypes[child.get('from')]
            child_items.append(add_child_item(
                tree_item_widget.tree_item,
                parent_widget,
                sobject,
                child_stype,
                child,
                item_info
            ))
    tree_item_widget.child_items = child_items

    # adding process items
    process_items = []
    if process:
        process_keys = process
    elif stype.pipeline:
        process_keys = stype.pipeline.process.iterkeys()
    else:
        process_keys = []

    for process in process_keys:
        process_items.append(add_process_item(
            tree_item_widget.tree_item,
            parent_widget,
            sobject,
            stype,
            process,
            item_info
        ))

    tree_item_widget.process_items = process_items

    return tree_item_widget


def add_process_item(tree_widget, parent_widget, sobject, stype, process, item_info):
    from lib.ui_classes.ui_item_classes import Ui_processItemWidget

    tree_item = QtGui.QTreeWidgetItem()
    item_info = {
        'relates_to': item_info['relates_to'],
        'is_expanded': False,
    }
    tree_item_widget = Ui_processItemWidget(sobject, stype, process, item_info, tree_item, parent_widget)

    add_item_to_tree(tree_widget, tree_item, tree_item_widget)

    return tree_item_widget


def add_snapshot_item(tree_widget, parent_widget, sobject, stype, process, snapshots, item_info, sep_versions=False,
                      insert_at_top=True):
    from lib.ui_classes.ui_item_classes import Ui_snapshotItemWidget
    # print id(item_info)

    snapshots_items = []

    for key, context in snapshots.contexts.iteritems():
        tree_item = QtGui.QTreeWidgetItem()
        item_info = {
            'relates_to': item_info['relates_to'],
            'is_expanded': False,
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
    }
    tree_item_widget = Ui_childrenItemWidget(sobject, stype, child, item_info, tree_item, parent_widget)

    add_item_to_tree(tree_widget, tree_item, tree_item_widget)

    return tree_item_widget


def expand_to_snapshot(parent, tree_widget):
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
        for i in range(lv):
            if state_dict.get(i):
                item = wdg.topLevelItem(i)
                item.setExpanded(state_dict[i]['d']['e'])
                item.setSelected(state_dict[i]['d']['s'])
                if item.childCount() > 0:
                    tree_state_revert(item, state_dict[i]['s'])
                # Scrolling to item
                if item.isSelected():
                    item_tree_widget = item.treeWidget()
                    item_tree_widget.scrollToItem(item)
    else:
        lv = wdg.childCount()
        for i in range(lv):
            item = wdg.child(i)
            if state_dict:
                if state_dict.get(i):
                    item.setExpanded(state_dict[i]['d']['e'])
                    item.setSelected(state_dict[i]['d']['s'])

                    if item.childCount() > 0:
                        tree_state_revert(item, state_dict[i]['s'])
            # Scrolling to item
            if item.isSelected():
                item_tree_widget = item.treeWidget()
                item_tree_widget.scrollToItem(item)


# files etc routine
def open_file_associated(filepath):
    # TODO message if file not exists
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filepath))
    elif os.name == 'nt':
        os.startfile(filepath)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))


def form_path(path):
    if env.Env.platform == 'Linux':
        formed_path = path.replace('\\', '/').replace('\\\\', '/').replace('//', '/')
        return formed_path
    else:
        formed_path = path.replace('\\', '/')
        return formed_path


def get_file_asset_dir(item):
    if item.snapshot.get('repo'):
        asset_dir = env.Env.rep_dirs[item.snapshot.get('repo')][0]
    else:
        asset_dir = env.Env.rep_dirs['asset_base_dir'][0]

    return asset_dir


def get_abs_path(item, file_type=None):
    if file_type:
        modes = file_type
    else:
        modes = env.Mode.mods
    modes.append('main')

    for mode in modes:
        if item.files.get(mode):
            main_file = item.files[mode][0]
            asset_dir = get_file_asset_dir(item)
            file_path = form_path(
                '{0}/{1}/{2}'.format(asset_dir, main_file['relative_dir'], main_file['file_name']))

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
