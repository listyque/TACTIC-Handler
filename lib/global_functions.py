# file global_functions.py
# Global Functions Module
import subprocess
import os
import sys
import zlib
import binascii

import PySide.QtGui as QtGui
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


def form_path(path):
    if env.Env.platform == 'Linux':
        formed_path = path.replace('\\', '/').replace('\\\\', '/').replace('//', '/')
        return formed_path
    else:
        formed_path = path.replace('\\', '/')
        return formed_path


def get_ver_rev(ver, rev):
    if ver > 0 and rev > 0:
        result = '<span style="color:#008498;">Ver: {0:03d};</span><span style="color:#0a9800;"> Rev: {1:03d}</span>'.format(ver,
                                                                                                                rev)
    elif ver > 0 and rev == 0:
        result = '<span style="color:#008498;">Ver: {0:03d}</span>'.format(ver, rev)
    else:
        result = ''

    return result


# QTreeWidget func
def add_items_to_tree(parent, tree_widget, item_widget, sobjects, process,
                      searh_all=False, row=0, snapshots=True, sep_versions=False):
    def add_items_and_widgets(item=None, widget=None, text=''):
        tree_item = QtGui.QTreeWidgetItem()
        tree_item.setText(0, text)
        item.addChild(tree_item)
        widget.tree_item = tree_item
        tree_widget.setItemWidget(tree_item, 0, widget)

    parent.progres_bar.show()
    tree_widget.clear()

    root_items_count = []

    # top level items routine
    for i, (sobject_code, sobject) in enumerate(sobjects.iteritems(), start=row):

        main_item = QtGui.QTreeWidgetItem()
        tree_widget.insertTopLevelItem(i, main_item)
        main_widget_items = item_widget.Ui_itemWidget(i, sobject, main_item, parent)
        tree_widget.setItemWidget(
            tree_widget.topLevelItem(i), 0, main_widget_items)

        current_progress = 100 * i / len(sobjects)
        parent.progres_bar.setValue(current_progress)

        # allowing to show all process, or particular
        if searh_all:
            iter_process = process
        else:
            iter_process = sobject.process.iterkeys()

        # adds top level root snapshot items, returns count of them
        # if process == 'publish':
        # print iter_process

        if main_widget_items.sobject.process.get('publish'):
            root_items_count.append(add_root_items_to_tree(parent, tree_widget, main_item, item_widget, main_widget_items, 'publish', sep_versions) + 1)
            print root_items_count
        else:
            # root_items_count = [0]
            # print 'Nope'
            root_items_count.append(0)

        # second level, items with items process
        for j, p in enumerate(iter_process):
            process_item = tree_widget.topLevelItem(i)
            process_widget = item_widget.Ui_processItemWidget(i, p, sobject, process_item, parent)
            add_items_and_widgets(process_item, process_widget, p)

            # third level, items with items context, and versionless
            if sobject.process.get(p) and snapshots:
                for k, (key1, context1) in enumerate(sobject.process[p].contexts.iteritems()):
                    tree_v_item = tree_widget.topLevelItem(i).child(j)
                    item_v_widget = item_widget.Ui_snapshotItemWidget(i, context1.versionless, sobject, parent)
                    add_items_and_widgets(tree_v_item, item_v_widget)

                    # fourth level, versions of items by each versionless, and context
                    for l, (key2, context2) in enumerate(
                            sobject.process[p].contexts[key1].versions.iteritems()):
                        tree_vs_item = tree_widget.topLevelItem(i).child(j).child(k)
                        item_vs_widget = item_widget.Ui_snapshotItemWidget(i, dict(key=context2), sobject, parent)
                        add_items_and_widgets(tree_vs_item, item_vs_widget)

    parent.progres_bar.setValue(100)
    parent.progres_bar.hide()
    return root_items_count


def add_snapshots_items_to_tree(parent, tree_widget, child_widget, item_widget, parent_widget, process, offset=0, sep_versions=False):
    def add_items_and_widgets(item=None, widget=None, text=''):
        tree_item = QtGui.QTreeWidgetItem()
        tree_item.setText(0, text)
        item.addChild(tree_item)
        widget.tree_item = tree_item
        tree_widget.setItemWidget(tree_item, 0, widget)

    for j, p in enumerate(process):
        pos = j + offset

        # third level, items with items context, and versionless
        if parent_widget.sobject.process.get(p):
            child_widget.child(pos).takeChildren()
            for k, (key1, context1) in enumerate(parent_widget.sobject.process[p].contexts.iteritems()):
                tree_v_item = child_widget.child(pos)
                item_v_widget = item_widget.Ui_snapshotItemWidget(parent_widget.row, context1.versionless,
                                                                  parent_widget.sobject, tree_v_item, parent)
                add_items_and_widgets(tree_v_item, item_v_widget)

                # fourth level, versions of items by each versionless, and context
                # TODO: make versions collapsable by revisions
                # snapshots = {
                #     'versions': collections.defaultdict(list),
                #     'revisions': collections.defaultdict(list),
                # }
                if not sep_versions:
                    for l, (key2, context2) in enumerate(
                            parent_widget.sobject.process[p].contexts[key1].versions.iteritems()):
                        # snapshots[context2.snapshot['version']].append(context2)

                        tree_vs_item = child_widget.child(pos).child(k)
                        item_vs_widget = item_widget.Ui_snapshotItemWidget(parent_widget.row, dict(key=context2),
                                                                           parent_widget.sobject, tree_vs_item, parent)
                        add_items_and_widgets(tree_vs_item, item_vs_widget)

                # print revisions


def add_root_items_to_tree(parent, tree_widget, child_widget, item_widget, parent_widget, process, sep_versions=False):
    def add_items_and_widgets(item=None, widget=None, text=''):
        tree_item = QtGui.QTreeWidgetItem()
        tree_item.setText(0, text)
        item.addChild(tree_item)
        widget.tree_item = tree_item
        tree_widget.setItemWidget(tree_item, 0, widget)

    i = 0

    for i, (key1, context1) in enumerate(parent_widget.sobject.process[process].contexts.iteritems()):
        print i, key1, context1
        item_v_widget = item_widget.Ui_snapshotItemWidget(parent_widget.row, context1.versionless,
                                                          parent_widget.sobject, child_widget, parent)
        add_items_and_widgets(child_widget, item_v_widget)
        if not sep_versions:
            for j, (key2, context2) in enumerate(parent_widget.sobject.process[process].contexts[key1].versions.iteritems()):
                print j, key2, context2
                tree_vs_item = child_widget.child(i)
                item_vs_widget = item_widget.Ui_snapshotItemWidget(parent_widget.row, dict(key=context2),
                                                                   parent_widget.sobject, tree_vs_item, parent)
                add_items_and_widgets(tree_vs_item, item_vs_widget)

    return i


def add_versions_items_to_tree(parent, tree_widget, item_widget, parent_widget, process, context):
    tree_widget.clear()
    for i, (key, context) in enumerate(parent_widget.sobject.process[process].contexts[context].versions.iteritems()):
        tree_vs_item = QtGui.QTreeWidgetItem()
        tree_widget.insertTopLevelItem(i, tree_vs_item)
        item_vs_widget = item_widget.Ui_snapshotItemWidget(parent_widget.row, dict(key=context),
                                                           parent_widget.sobject, tree_vs_item, parent)

        tree_widget.setItemWidget(tree_widget.topLevelItem(i), 0, item_vs_widget)
        tree_widget.setRootIsDecorated(False)


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


def revert_expanded_state(tree, state, select=False, expand=False):
    """
    Self explanatory
    :param tree: treeWidget
    :param state: dict of true or false
    """
    lv = tree.topLevelItemCount()

    for i in range(lv):

        t = tree.topLevelItem(i).childCount()
        if state['lv'][lv + i][0]:
            if expand:
                tree.expandItem(tree.topLevelItem(i))
            if select:
                tree.topLevelItem(i).setSelected(True)
                tree.scrollToItem(tree.topLevelItem(i))

        for j in range(t):

            l = tree.topLevelItem(i).child(j).childCount()
            if state['lv'][i]['t'][t + j]:
                if expand:
                    tree.expandItem(tree.topLevelItem(i).child(j))
                if select:
                    tree.topLevelItem(i).child(j).setSelected(True)
                    tree.scrollToItem(tree.topLevelItem(i).child(j))

            for x in range(l):

                s = tree.topLevelItem(i).child(j).child(x).childCount()
                if state['lv'][i]['t'][j]['l'][l + x]:
                    if expand:
                        tree.expandItem(tree.topLevelItem(i).child(j).child(x))
                    if select:
                        tree.topLevelItem(i).child(j).child(x).setSelected(True)
                        tree.scrollToItem(tree.topLevelItem(i).child(j).child(x))

                for y in range(s):
                    if select:
                        if state['lv'][i]['t'][j]['l'][x]['s'][y]:
                            tree.topLevelItem(i).child(j).child(x).child(y).setSelected(True)
                            tree.scrollToItem(tree.topLevelItem(i).child(j).child(x).child(y))


def expanded_state(tree, is_expanded=False, is_selected=False):
    """
    Saving full tree of Tree Widget
    :param tree: treeWidget
    :return: dict of true/false
    """
    # TODO Make it recursive

    lv = tree.topLevelItemCount()

    results = dict(
        lv=[
            {'t': [{'l': [{'s': []}
                          for c in range(tree.topLevelItem(a).child(b).childCount())]}
                   for b in range(tree.topLevelItem(a).childCount())]}
            for a in range(tree.topLevelItemCount())],
    )

    for i in range(lv):
        if is_expanded:
            results['lv'].append([tree.isItemExpanded(tree.topLevelItem(i))])
        if is_selected:
            results['lv'].append([tree.isItemSelected(tree.topLevelItem(i))])

        t = tree.topLevelItem(i).childCount()
        for j in range(t):
            if is_expanded:
                results['lv'][i]['t'].append(tree.isItemExpanded(tree.topLevelItem(i).child(j)))
            if is_selected:
                results['lv'][i]['t'].append(tree.isItemSelected(tree.topLevelItem(i).child(j)))

            l = tree.topLevelItem(i).child(j).childCount()
            for x in range(l):
                if is_expanded:
                    results['lv'][i]['t'][j]['l'].append(
                        tree.isItemExpanded(tree.topLevelItem(i).child(j).child(x)))
                if is_selected:
                    results['lv'][i]['t'][j]['l'].append(
                        tree.isItemSelected(tree.topLevelItem(i).child(j).child(x)))

                s = tree.topLevelItem(i).child(j).child(x).childCount()
                for y in range(s):
                    if is_selected:
                        results['lv'][i]['t'][j]['l'][x]['s'].append(
                            tree.isItemSelected(tree.topLevelItem(i).child(j).child(x).child(y)))

    return results


def save(tree):
    cache = []
    expanded = []
    for i in range(tree.topLevelItemCount()):
        cache.append(tree.topLevelItem(i))
    while cache:
        item = cache.pop()
        if item.isExpanded():
            expanded.append(hash('asd'))
        for row in range(item.childCount()):
            child = item.child(row)
            cache.append(child)

    return expanded


# files etc routine
def open_file_associated(filepath):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filepath))
    elif os.name == 'nt':
        os.startfile(filepath)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))


def version(major=0, minor=0, build=0, revision=0):
    return str(str(major) + '.' + str(minor) + '.' + str(build) + '.' + str(revision))


def simplify_html(html, pretty=False):
    from bs4 import BeautifulSoup
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
