# module Tree widget item Classes
# file ui_item_classes.py
# Main Item for TreeWidget

import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from lib.configuration import cfg_controls
import lib.global_functions as gf
import lib.tactic_classes as tc
import lib.ui.items.ui_item as ui_item
import lib.ui.items.ui_item_children as ui_item_children
import lib.ui.items.ui_item_process as ui_item_process
import lib.ui.items.ui_item_snapshot as ui_item_snapshot
import ui_tasks_classes as tasks_widget
import ui_notes_classes as notes_widget
import ui_addsobject_classes as addsobject_widget

reload(ui_item)
reload(ui_item_process)
reload(ui_item_snapshot)
reload(tasks_widget)
reload(notes_widget)


class Ui_itemWidget(QtGui.QWidget, ui_item.Ui_item):
    def __init__(self, sobject, stype, info, tree_item, ignore_dict, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'sobject'
        self.sobject = sobject
        self.stype = stype
        self.info = info
        self.tree_item = tree_item
        self.process_items = []
        self.root_snapshot_items = []
        self.process_snapshot_items = []
        self.child_items = []
        self.parent_ui = parent
        self.sep_versions = self.parent_ui.get_is_separate_versions()
        self.project = self.parent_ui.project
        self.relates_to = self.parent_ui.relates_to
        self.ignore_dict = ignore_dict

        if self.sobject:
            self.fill_sobject_info()

        self.controls_actions()

        self.parents_stypes = None
        self.children_stypes = None
        self.check_for_children()

    def controls_actions(self):
        self.tasksToolButton.setHidden(True)  # Temporaty hide tasks button
        self.tasksToolButton.clicked.connect(lambda: self.create_tasks_window())
        self.relationsToolButton.clicked.connect(self.drop_down_children)

    def fill_sobject_info(self):
        title = 'No Title'
        if self.sobject.info.get('name'):
            title = self.sobject.info.get('name')
        elif self.sobject.info.get('title'):
            title = self.sobject.info.get('title')
        elif self.sobject.info.get('code'):
            title = self.sobject.info.get('code')

        self.fileNameLabel.setText(title)
        self.commentLabel.setText(gf.to_plain_text(self.sobject.info.get('description')))
        # timestamp = datetime.strptime(self.sobject.info.get('timestamp').split('.')[0], '%Y-%m-%d %H:%M:%S')
        date = str(self.sobject.info.get('timestamp')).split('.')[0]
        self.dateLabel.setText(date)

    def drop_down_children(self):
        self.relationsToolButton.showMenu()

    def check_for_children(self):
        if self.stype.schema.parents:
            self.parents_stypes = self.stype.schema.parents
            for parent in self.stype.schema.parents:
                parent_code = parent.get('to')
                parent_title = self.project.stypes.get(parent_code)
                if parent_title:
                    parent_title = parent_title.info.get('title')
                else:
                    parent_title = parent_code
                parent_action = QtGui.QAction(parent_title, self.relationsToolButton)
                self.relationsToolButton.addAction(parent_action)

        if self.stype.schema.children:
            self.children_stypes = self.stype.schema.children
            child_sep = QtGui.QAction('Children', self.relationsToolButton)
            child_sep.setSeparator(True)
            self.relationsToolButton.addAction(child_sep)

            for child in self.stype.schema.children:
                child_code = child.get('from')
                child_title = self.project.stypes.get(child_code)
                if child_title:
                    child_title = child_title.info.get('title')
                else:
                    child_title = child_code
                child_action = QtGui.QAction(child_title, self.relationsToolButton)
                self.relationsToolButton.addAction(child_action)

        if not (self.stype.schema.children or self.stype.schema.parents):
            self.relationsToolButton.hide()

    def create_tasks_window(self):
        try:
            self.tasks_widget.show()
        except:
            self.tasks_widget = tasks_widget.Ui_tasksWidgetMain(self.sobject, self)
            self.tasks_widget.show()

    def get_current_tree_widget(self):
        current_tree = self.parent_ui.get_current_tree_widget()
        return current_tree.resultsTreeWidget

    def get_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item.parent())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_tree_widget()
        parent_item_widget = current_tree.itemWidget(self.tree_item.parent(), 0)
        return parent_item_widget

    def collapse_self(self):
        parent = self.get_parent_item()
        return parent.takeChild(self.get_index().row())

    def collapse_all_children(self):
        return self.tree_item.takeChildren()

    def update_items(self):
        self.sobject.update_snapshots()

        self.collapse_all_children()

        self.child_items = []
        self.process_items = []
        self.root_snapshot_items = []
        self.process_snapshot_items = []

        self.fill_child_items()
        self.fill_process_items()
        self.fill_snapshots_items()

        self.get_notes_count()

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return u'{0}/{1}'.format('publish', custom)
            else:
                return 'publish'
        else:
            return ''

    def get_skey(self, skey=False, only=False, parent=False):
        """skey://cgshort/props?project=the_pirate&code=PROPS00001"""
        if parent or only:
            return self.sobject.info['__search_key__']
        if skey:
            return 'skey://' + self.sobject.info['__search_key__']

    def get_description(self):
        return self.sobject.info.get('description')

    def update_description(self, new_description):
        self.sobject.info['description'] = new_description
        self.commentLabel.setText(new_description)

    def fill_child_items(self):

        # adding child items
        # child_items = []
        if self.children_stypes:
            for child in self.children_stypes:
                child_stype = self.project.stypes[child.get('from')]
                ignored = False
                if self.ignore_dict:
                    if child_stype.info['code'] in self.ignore_dict['children']:
                        ignored = True

                if not ignored:
                    self.child_items.append(gf.add_child_item(
                        self.tree_item,
                        self.parent_ui,
                        self.sobject,
                        child_stype,
                        child,
                        self.info
                    ))
        # self.child_items = child_items

    def fill_process_items(self):

        # getting all possible processes here
        processes = []
        pipeline_code = self.sobject.info.get('pipeline_code')
        if pipeline_code and self.stype.pipeline:
            processes = self.stype.pipeline.get(pipeline_code)
            if processes:
                processes = processes.process.keys()

        if self.ignore_dict:
            if self.ignore_dict['show_builtins']:
                show_all = True
                for builtin in ['icon', 'attachment', 'publish']:
                    if builtin not in self.ignore_dict['builtins']:
                        processes.append(builtin)
                        show_all = False
                if show_all:
                    processes.extend(['icon', 'attachment', 'publish'])

        for process in processes:
            ignored = False
            if self.ignore_dict:
                if process in self.ignore_dict['processes'].get(pipeline_code):
                    ignored = True
            if not ignored:
                process_item = gf.add_process_item(
                    self.tree_item,
                    self.parent_ui,
                    self.sobject,
                    self.stype,
                    process,
                    self.info
                )
                self.process_items.append(process_item)
                # filling sub processes
                process_item.fill_subprocesses()

        # if process_items:
        #     self.process_items = process_items
        # else:
        #     # this loads root 'publish' items on expand !my favorite duct tape!
        #     self.tree_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)

    def fill_snapshots_items(self):
        # current_widget = self.get_current_widget()
        # current_tree_widget = current_widget.resultsTreeWidget
        # print current_tree_widget
        # tree_widget = self.resultsTreeWidget.itemWidget(tree_item, 0)
        # tree_widget = self.get_current_tree_widget()

        # TODO Show All Process
        # process = []
        # if self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked():
        #     process = self.process
        # else:
        #     for p in tree_widget.sobject.process.iterkeys():
        #         process.append(p)

        # if self.type == 'sobject' and not self.info['is_expanded']:
        #     self.info['is_expanded'] = True

        for proc in self.process_items:
            for key, val in self.sobject.process.iteritems():
                # because it is dict, items could be in any position
                if key == proc.process:
                    self.process_snapshot_items.append(proc.add_snapshots_items(val))
                    # MOVED TO PROCESS ITEM
                    # self.process_snapshot_items.append(gf.add_snapshot_item(
                    #     proc.tree_item,
                    #     self.parent_ui,
                    #     proc.sobject,
                    #     proc.stype,
                    #     proc.process,
                    #     val,
                    #     proc.info,
                    #     self.sep_versions,
                    #     False,
                    # ))

        for key, val in self.sobject.process.iteritems():
            if key == 'publish':
                self.root_snapshot_items.append(gf.add_snapshot_item(
                        self.tree_item,
                        self.parent_ui,
                        self.sobject,
                        self.stype,
                        'publish',
                        val,
                        self.info,
                        self.sep_versions,
                        True,
                    ))

    def get_process_list(self):
        process = []
        for process_widget in self.process_items:
            process.append(process_widget.process)
        return process

    def get_children_list(self):
        children_list = []
        if self.children_stypes:
            for child in self.children_stypes:
                children_list.append(child.get('from'))
            return children_list
        else:
            return []

    def get_notes_count(self):

        def notes_fill():
            notes_counts = notes_counts_query.result['notes']
            process_items_dict = {item.process: item for item in self.process_items}
            for key, val in notes_counts.iteritems():
                process_item = process_items_dict.get(key)
                if process_item:
                    process_item.set_notes_count(val)

        def children_fill():
            children_counts = notes_counts_query.result['stypes']
            child_items_dict = {item.child.get('from'): item for item in self.child_items}
            for key, val in children_counts.iteritems():
                child_item = child_items_dict.get(key)
                if child_item:
                    child_item.set_child_count_title(val)

        notes_counts_query = tc.ServerThread(self)

        notes_counts_query.kwargs = dict(
            sobject=self.sobject,
            process=self.get_process_list(),
            children_stypes=self.get_children_list()
        )
        notes_counts_query.routine = tc.get_notes_count
        notes_counts_query.msleep(10)
        notes_counts_query.start()
        notes_counts_query.setPriority(QtCore.QThread.NormalPriority)

        notes_counts_query.finished.connect(notes_fill)
        notes_counts_query.finished.connect(children_fill)

    def expand_tree_item(self):
        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            self.fill_child_items()
            self.fill_process_items()
            self.fill_snapshots_items()

        self.get_notes_count()

    def collapse_tree_item(self):
        pass

    def get_search_key(self):
        return self.sobject.info.get('__search_key__')

    def get_parent_search_key(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_search_key()

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

    def mouseDoubleClickEvent(self, event):
        do_dbl_click = None
        if self.relates_to == 'checkin':
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin(), 'doubleClickSaveCheckBox')

        if not do_dbl_click:
            super(Ui_itemWidget, self).mouseDoubleClickEvent(event)
        else:
            if self.relates_to == 'checkin':
                self.parent_ui.save_file()


class Ui_processItemWidget(QtGui.QWidget, ui_item_process.Ui_processItem):
    def __init__(self, sobject, stype, process, info, tree_item, pipeline, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'process'
        self.sobject = sobject
        self.stype = stype
        self.process = process
        self.pipeline = pipeline
        self.process_info = self.get_current_process_info()
        self.workflow = self.stype.project.workflow
        self.info = info
        self.tree_item = tree_item
        self.snapshot_items = []
        self.process_items = []
        self.process_snapshot_items = []
        # print(tree_item.text(0))
        # self.item_info = {}

        self.parent_ui = parent
        self.relates_to = self.parent_ui.relates_to

        self.sep_versions = self.parent_ui.get_is_separate_versions()

        # self.item_info[
        #     'description'] = 'This is {0} process item, there is no description, better click on Notes button'.format(
        #     self.process)

        self.controls_actions()

        self.create_ui()

    def get_notes_count(self):

        def notes_fill():
            notes_counts = notes_counts_query.result['notes']
            process_items_dict = {item.process: item for item in self.process_items}
            for key, val in notes_counts.iteritems():
                process_item = process_items_dict.get(key)
                if process_item:
                    process_item.set_notes_count(val)

        notes_counts_query = tc.ServerThread(self)
        notes_counts_query.kwargs = dict(
            sobject=self.sobject,
            process=self.get_process_list(),
            children_stypes=[]
        )
        notes_counts_query.routine = tc.get_notes_count
        notes_counts_query.start()

        notes_counts_query.finished.connect(notes_fill)

    def get_process_list(self):
        process = []
        for process_widget in self.process_items:
            process.append(process_widget.process)
        return process

    def get_current_process_info(self):
        pipeline = self.get_current_process_pipeline()
        process_info = None
        if pipeline:
            process_info = pipeline.process.get(self.process)

        return process_info

    def get_current_process_pipeline(self):
        if self.pipeline:
            return self.pipeline
        else:
            pipeline_code = self.sobject.info.get('pipeline_code')
            pipeline = self.stype.pipeline.get(pipeline_code)
            return pipeline

    def controls_actions(self):
        self.notesToolButton.clicked.connect(lambda: self.create_notes_widget())

    def create_ui(self):
        if self.process:
            title = self.process.capitalize()
        else:
            title = 'Unnamed'
        if self.process_info.get('type') == 'hierarchy':
            title = '{0} (hierarchy)'.format(title)
        self.tree_item.setText(0, title)

        self.notesToolButton.setIcon(gf.get_icon('commenting-o'))

    def fill_subprocesses(self):
        if self.process_info:
            if self.process_info.get('type') == 'hierarchy':
                child_pipeline = self.workflow.get_child_pipeline_by_process_code(
                    self.get_current_process_pipeline(),
                    self.process
                )
                self.add_process_items(child_pipeline)

    def set_notes_count(self, notes_count):
        if notes_count > 0:
            self.notesToolButton.setIcon(gf.get_icon('commenting'))
        self.notesToolButton.setText('| {0}'.format(notes_count))

    def create_notes_widget(self):
        self.note_widget = notes_widget.Ui_notesOwnWidget(self)
        self.note_widget.setWindowTitle(
            'Notes for: {0}, with process: {1}'.format(self.sobject.info['name'], self.process))
        self.sobject.info['process'] = self.process
        self.sobject.info['context'] = self.process
        # print(self.sobject.info)
        if self.sobject:
            self.note_widget.ui_notes.task_item = self.sobject
            self.note_widget.ui_notes.fill_notes()
        self.note_widget.show()
        self.note_widget.ui_notes.conversationScrollArea.verticalScrollBar().setValue(
            self.note_widget.ui_notes.conversationScrollArea.verticalScrollBar().maximum())

    def get_current_tree_widget(self):
        current_tree = self.parent_ui.get_current_tree_widget()
        return current_tree.resultsTreeWidget

    def get_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item.parent())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_tree_widget()
        parent_item_widget = current_tree.itemWidget(self.tree_item.parent(), 0)
        return parent_item_widget

    def collapse_self(self):
        parent = self.get_parent_item()
        return parent.takeChild(self.get_index().row())

    def collapse_all_children(self):
        return self.tree_item.takeChildren()

    def add_process_items(self, pipeline):

        # TODO when i get my hands to recursive filtering, make it respect filtering.

        # processes = []
        # pipeline_code = self.sobject.info.get('pipeline_code')
        # if pipeline_code and self.stype.pipeline:
        processes = []
        if pipeline:
            processes = pipeline.process.keys()

        # if self.ignore_dict:
        #     if self.ignore_dict['show_builtins']:
        #         show_all = True
        #         for builtin in ['icon', 'attachment', 'publish']:
        #             if builtin not in self.ignore_dict['builtins']:
        #                 processes.append(builtin)
        #                 show_all = False
        #         if show_all:
        #             processes.extend(['icon', 'attachment', 'publish'])

        for process in processes:
            ignored = False
            # if self.ignore_dict:
            #     if process in self.ignore_dict['processes'].get(pipeline_code):
            #         ignored = True
            if not ignored:
                # print self.tree_item.treeWidget()
                # print 'adding', process
                process_item = gf.add_process_item(
                    self.tree_item,
                    self.parent_ui,
                    self.sobject,
                    self.stype,
                    process,
                    self.info,
                    pipeline=pipeline
                )
                self.process_items.append(process_item)
                process_item.fill_subprocesses()

    def fill_snapshots_items(self):
        # BIG TODO, MAKE THREADING HERE and load only necessary processes snapshots
        self.sobject.update_snapshots()
        for proc in self.process_items:
            for key, val in self.sobject.process.iteritems():
                # because it is dict, items could be in any position
                if key == proc.process:
                    self.process_snapshot_items.append(proc.add_snapshots_items(val))

    def add_snapshots_items(self, snapshots):
        snapshot_items = gf.add_snapshot_item(
            self.tree_item,
            self.parent_ui,
            self.sobject,
            self.stype,
            self.process,
            snapshots,
            self.info,
            self.sep_versions,
            False,
        )

        return snapshot_items

    def update_items(self):
        self.sobject.update_snapshots()
        self.collapse_all_children()

        gf.add_snapshot_item(
            self.tree_item,
            self.parent_ui,
            self.sobject,
            self.stype,
            self.process,
            self.sobject.process.get(self.process),
            self.info,
            self.sep_versions,
            False,
        )

    def prnt(self):
        # print(str(self.item_index))
        # print(self.tree_item.parent().setExpanded(False))
        print(self.sobject.process)
        self.sobject.update_snapshots()
        print(self.sobject.process)

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return u'{0}/{1}'.format(self.process, custom)
            else:
                return self.process
                # else:
                #     return ''

    def get_description(self):
        return 'No Description for this item "{0}"'.format(self.process)

    def get_skey(self, skey=False, only=False, parent=False):
        if parent or only:
            return self.sobject.info['__search_key__']
        if skey:
            return 'skey://' + self.sobject.info['__search_key__']

    def get_search_key(self):
        return self.sobject.info.get('__search_key__')

    def get_parent_search_key(self):
        pass

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

    def expand_tree_item(self):
        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            self.fill_snapshots_items()

        self.get_notes_count()

    def collapse_tree_item(self):
        pass

    def mouseDoubleClickEvent(self, event):
        do_dbl_click = None
        if self.relates_to == 'checkin':
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin(), 'doubleClickSaveCheckBox')

        if not do_dbl_click:
            super(Ui_processItemWidget, self).mouseDoubleClickEvent(event)
        else:
            if self.relates_to == 'checkin':
                self.parent_ui.save_file()


class Ui_snapshotItemWidget(QtGui.QWidget, ui_item_snapshot.Ui_snapshotItem):
    def __init__(self, sobject, stype, process, context, snapshot, info, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'snapshot'
        self.sobject = sobject
        self.stype = stype
        self.process = process
        self.context = context
        self.snapshot = None
        self.info = info
        self.tree_item = tree_item

        self.parent_ui = parent
        self.relates_to = self.parent_ui.relates_to

        self.files = {}

        if snapshot:
            self.snapshot = snapshot[0].snapshot
            self.files = snapshot[0].files
        hidden = ['icon', 'web', 'playblast']

        if self.snapshot:
            abs_path = gf.get_abs_path(self)

            if abs_path:
                if not os.path.exists(abs_path):
                    self.setDisabled(True)
            else:
                self.setDisabled(True)

            self.commentLabel.setText(gf.to_plain_text(self.snapshot['description'], 80))
            self.dateLabel.setText(self.snapshot['timestamp'].split('.')[0].replace(' ', ' \n'))
            self.authorLabel.setText(self.snapshot['login'] + ':')
            self.verRevLabel.setText(gf.get_ver_rev(self.snapshot['version'], self.snapshot['revision']))

            for key, fl in self.files.iteritems():
                if key not in hidden:
                    # TODO Repo color
                    if self.snapshot.get('repo'):
                        self.sizeLabel.setStyleSheet(self.get_repo_color())
                    if not self.isEnabled():
                        self.fileNameLabel.setText('{0}, (File Missing)'.format(fl[0]['file_name']))
                    else:
                        self.fileNameLabel.setText(fl[0]['file_name'])
                    self.sizeLabel.setText(gf.sizes(fl[0]['st_size']))
        else:
            self.fileNameLabel.setText('Versionless for {0} not found'.format(self.context))
            self.commentLabel.setText('Check this snapshot, and update versionless')
            self.dateLabel.deleteLater()
            self.sizeLabel.deleteLater()
            self.authorLabel.deleteLater()

    def resizeEvent(self, event):
        self.tree_item.setSizeHint(0, QtCore.QSize(self.width(), 25 + self.commentLabel.height()))

    def get_current_tree_widget(self):
        current_tree = self.parent_ui.get_current_tree_widget()
        return current_tree.resultsTreeWidget

    def get_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item.parent())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_tree_widget()
        parent_item_widget = current_tree.itemWidget(self.tree_item.parent(), 0)
        return parent_item_widget

    def collapse_self(self):
        parent = self.get_parent_item()
        return parent.takeChild(self.get_index().row())

    def collapse_all_children(self):
        return self.tree_item.takeChildren()

    def update_items(self):
        self.sobject.update_snapshots()

        parent_item_widget = self.get_parent_item_widget()
        if parent_item_widget:
            if parent_item_widget.type == 'snapshot':
                # if we have snapshot, so go upper to get parent of upper snapshot
                parent_item_widget = parent_item_widget.get_parent_item_widget()
                parent_item_widget.update_items()
            else:
                parent_item_widget.update_items()

    def get_repo_color(self):
        config = cfg_controls.get_checkin()
        if config:
            if self.snapshot['repo'] == 'base':
                repo = gf.get_value_from_config(config, 'assetBaseDirColorToolButton', 'QToolButton')
            if self.snapshot['repo'] == 'local':
                repo = gf.get_value_from_config(config, 'localRepoDirColorToolButton', 'QToolButton')
            # if self.snapshot['repo'] == 'win32_sandbox_dir':
            #     repo = gf.get_value_from_config(config, 'sandboxDirColorToolButton', 'QToolButton')
            # if self.snapshot['repo'] == 'win32_client_repo_dir':
            #     repo = gf.get_value_from_config(config, 'clientRepoDirColorToolButton', 'QToolButton')
            # if self.snapshot['repo'] == 'custom_asset_dir':
            #     repo = gf.get_value_from_config(config, 'customRepoDirColorToolButton', 'QToolButton')

            color = repo[repo.find('rgb'):repo.find('rgb') + 16]
            repo_colors = color.replace('rgb(', '').replace(')', '').split(',')
        else:
            repo_colors = [96, 96, 96]

        stylesheet = 'QLabel{background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(%s, %s, %s, 96));' \
                     'border - bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));' \
                     'padding: 0px;}' % tuple(repo_colors)

        return stylesheet

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return u'{0}/{1}'.format(self.snapshot['process'], custom)
            else:
                return self.snapshot['process']
        else:
            context = self.snapshot['context'].split('/')[-1]
            if context == self.snapshot['process']:
                context = ''
            return context

    def get_search_key(self):
        return self.snapshot.get('__search_key__')

    def get_parent_search_key(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_search_key()

    def get_sobject(self):
        return self.snapshot

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

    def get_skey(self, skey=False, only=False, parent=False):
        """skey://sthpw/snapshot?code=SNAPSHOT00000028"""
        if self.snapshot:
            if only:
                return self.snapshot['__search_key__']
            if skey:
                return 'skey://{0}'.format(self.snapshot['__search_key__'])
            if parent:
                return self.sobject.info['__search_key__']
        else:
            return 'No skey for this item!'

    def get_description(self):
        if self.snapshot:
            return self.snapshot['description']
        else:
            return 'No Description for this item!'

    def update_description(self, new_description):
        self.snapshot['description'] = new_description
        self.commentLabel.setText(new_description)

    def expand_tree_item(self):
        pass

    def collapse_tree_item(self):
        pass

    def mouseDoubleClickEvent(self, event):
        if self.relates_to == 'checkin':
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin(), 'doubleClickSaveCheckBox')
        else:
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkout(), 'doubleClickOpenCheckBox')

        if not do_dbl_click:
            super(Ui_snapshotItemWidget, self).mouseDoubleClickEvent(event)
        else:
            if self.relates_to == 'checkin':
                self.parent_ui.save_file()
            else:
                self.parent_ui.open_file()


class Ui_childrenItemWidget(QtGui.QWidget, ui_item_children.Ui_childrenItem):
    def __init__(self, sobject, stype, child, info, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'child'
        self.sobject = sobject
        self.stype = stype
        self.child = child
        self.info = info
        self.tree_item = tree_item
        self.tree_item.setExpanded = self.tree_item_set_expanded_override
        self.childrenToolButton.setCheckable(False)

        self.parent_ui = parent
        self.project = self.parent_ui.project
        # self.parent_stype = self.parent_ui.stype

        self.title = '{0} ({1})'.format(self.stype.info.get('title'), self.child.get('from'))
        self.childrenToolButton.setText(self.title)
        # self.childrenToolButton.setStyleSheet("QToolButton {color: blue;background-color: transparent;}")

        self.set_style()
        self.controls_actions()

        self.create_ui()

    def create_ui(self):
        self.addNewSObjectToolButton.setIcon(gf.get_icon('plus-square-o'))

    def tree_item_set_expanded_override(self, state):
        if state:
            self.toggle_cildren_button()
        self.tree_item.treeWidget().setItemExpanded(self.tree_item, state)

    def controls_actions(self):
        self.childrenToolButton.clicked.connect(self.toggle_cildren_button)
        self.addNewSObjectToolButton.clicked.connect(self.add_new_sobject)

    def set_child_count_title(self, count):
        if count > 0:
            self.addNewSObjectToolButton.setIcon(gf.get_icon('plus-square'))
        self.addNewSObjectToolButton.setText('| {0}'.format(count))

    def set_style(self):
        # tab_label = QtGui.QLabel(tab_name)
        # tab_label.setAlignment(QtCore.Qt.AlignCenter)
        # tab_color = stype.info['color']
        button_color = '0000ff'

        if button_color:
            effect = QtGui.QGraphicsDropShadowEffect(self.childrenToolButton)
            # blur = QtGui.QGraphicsBlurEffect(tab_label)
            # QtGui.QGraphicsItemAnimation

            t_c = gf.hex_to_rgb(button_color, alpha=255, tuple=True)
            # print t_c
            effect.setOffset(1, 1)
            effect.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
            # blur.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
            # print blur.strength()
            # blur.setStrength(.5)
            # blur.setBlurRadius()
            # print blur.blurHints()
            # print blur.blurRadius()
            # blur.setBlurRadius(2)

            effect.setBlurRadius(20)
            self.childrenToolButton.setGraphicsEffect(effect)
            # tab_label.setGraphicsEffect(blur)

            # tab_color_rgb = gf.hex_to_rgb(button_color, alpha=8)
            self.childrenToolButton.setStyleSheet('QToolButton {background-color: transparent;}')

    def add_new_sobject(self):
        self.add_sobject = addsobject_widget.Ui_addTacticSobjectWidget(stype=self.stype, item=self, parent=self.parent_ui)
        self.add_sobject.show()

    def expand_tree_item(self):
        self.childrenToolButton.setChecked(True)
        # self.childrenToolButton.setArrowType(QtCore.Qt.DownArrow)

    def collapse_tree_item(self):
        self.childrenToolButton.setChecked(False)
        # self.childrenToolButton.setArrowType(QtCore.Qt.RightArrow)

    def get_current_tree_widget(self):
        current_tree = self.parent_ui.get_current_tree_widget()
        return current_tree.resultsTreeWidget

    def get_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item.parent())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_tree_widget()
        parent_item_widget = current_tree.itemWidget(self.tree_item.parent(), 0)
        return parent_item_widget

    def toggle_cildren_button(self):
        if self.tree_item.isExpanded():
            self.tree_item.treeWidget().setItemExpanded(self.tree_item, False)
            self.childrenToolButton.setChecked(False)
            # self.childrenToolButton.setArrowType(QtCore.Qt.RightArrow)
        else:
            self.add_child_sobjects()
            if self.tree_item.childCount() > 0:
                self.childrenToolButton.setCheckable(True)
                self.tree_item.treeWidget().setItemExpanded(self.tree_item, True)
                self.childrenToolButton.setChecked(True)
                # self.childrenToolButton.setArrowType(QtCore.Qt.DownArrow)

    def add_child_sobjects(self):
        if not self.info['is_expanded']:

            self.info['is_expanded'] = True

            server = tc.server_start()
            built_process = server.build_search_type(self.child.get('from'), self.project.info.get('code'))

            child_code = None

            relationship = self.child.get('relationship')
            if relationship:
                if relationship == 'search_type':
                    child_code = 'search_code'
                elif relationship == 'code':
                    child_code = '{0}_code'.format(self.child.get('to').split('/')[-1])

            if not child_code:
                child_code = self.child.get('from_col')

            filters = [(child_code, self.sobject.info.get('code'))]

            assets = server.query(built_process, filters)

            if self.stype.pipeline:
                process = []
                for pipe in self.stype.pipeline.values():
                    process.extend(pipe.process.keys())
            else:
                process = []

            sobjects = tc.get_sobjects(process, assets, project_code=self.project.info.get('code'))
            stype = self.stype
            sobject_item_widget = self.get_parent_item_widget()

            for sobject in sobjects.itervalues():
                item_info = {
                    'relates_to': self.info['relates_to'],
                    'is_expanded': False,
                }
                gf.add_sobject_item(
                    self.tree_item,
                    self.parent_ui,
                    sobject,
                    stype,
                    item_info,
                    ignore_dict=sobject_item_widget.ignore_dict
                )

    def get_skey(self, skey=False, only=False, parent=False):
        pass

    def get_description(self):
        return 'No Description for this item "{0}"'.format('AZAZAZ')

    def get_search_key(self):
        return self.sobject.info.get('__search_key__')

    def get_parent_search_key(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_search_key()

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

# from tactic.ui.panel import TableLayoutWdg
#
# table = TableLayoutWdg(search_type='cgshort/textures', view='table', search_limit=8, init_load_num=8)
# table.get_display()
# return str(table.table.render())
