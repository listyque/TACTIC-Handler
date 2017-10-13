# module Tree widget item Classes
# file ui_item_classes.py
# Main Item for TreeWidget

import os
# import PySide.QtGui as QtGui
# import PySide.QtCore as QtCore
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

from lib.environment import env_tactic
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
        self.sep_versions = self.info['sep_versions']
        self.process_items = []
        self.root_snapshot_items = []
        self.process_snapshot_items = []
        self.child_items = []
        self.search_widget = parent

        self.project = self.search_widget.project
        self.relates_to = 'checkin_out'
        self.ignore_dict = ignore_dict

        self.expand_state = False
        self.selected_state = False
        self.children_states = None

        if self.sobject:
            self.fill_sobject_info()

        self.controls_actions()

        self.parents_stypes = None
        self.children_stypes = None
        self.check_for_children()

        self.create_ui()

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.expand_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def set_children_states(self, states):
        self.children_states = states

    def create_ui(self):
        self.previewLabel.setText('<span style=" font-size:14pt; font-weight:600; color:#828282;">{0}</span>'.format(
            gf.gen_acronym(self.get_title()))
        )
        self.set_preview()

    def set_preview(self):
        snapshots = self.get_snapshot()
        if snapshots:
            preview_files_objects = snapshots.values()[0].get_previewable_files_objects()
            if preview_files_objects:
                icon_previw = preview_files_objects[0].get_icon_preview()
                if icon_previw:
                    previw_abs_path = icon_previw.get_full_abs_path()
                    pixmap = Qt4Gui.QPixmap(previw_abs_path)
                    if not pixmap.isNull():
                        self.previewLabel.setPixmap(pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation))

    def controls_actions(self):
        # self.tasksToolButton.setHidden(True)  # Temporaty hide tasks button
        self.tasksToolButton.clicked.connect(lambda: self.create_tasks_window())
        self.relationsToolButton.clicked.connect(self.drop_down_children)

    def fill_sobject_info(self):

        self.fileNameLabel.setText(self.get_title())
        self.commentLabel.setText(gf.to_plain_text(self.sobject.info.get('description')))
        # timestamp = datetime.strptime(self.sobject.info.get('timestamp').split('.')[0], '%Y-%m-%d %H:%M:%S')
        date = str(self.sobject.info.get('timestamp')).split('.')[0]
        self.dateLabel.setText(date)

    def get_title(self):
        title = 'No Title'
        if self.sobject.info.get('name'):
            title = self.sobject.info.get('name')
        elif self.sobject.info.get('title'):
            title = self.sobject.info.get('title')
        elif self.sobject.info.get('code'):
            title = self.sobject.info.get('code')

        return title

    def get_snapshot(self):
        icons = None
        icons_process = self.sobject.process.get('icon')
        if icons_process:
            icons = icons_process.contexts.get('icon')
        if icons:
            return icons.versions

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
        current_tree = self.search_widget.get_current_tree_widget()
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
        self.fill_snapshots_items(publish=True)
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

    def get_context_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process('publish')
        if process:
            context_options = process.get('context_options')
            if context_options:
                return context_options.split('|')

    def get_checkin_mode_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process('publish')

        if process:
            return process.get('checkin_mode')

    @staticmethod
    def get_current_process_info():
        process_info = {'name': 'publish'}
        return process_info

    def get_current_process_pipeline(self):

        search_type = self.stype.info.get('search_type')
        if search_type and self.stype.pipeline:
            return self.stype.pipeline.get(search_type)

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
                child_stype = self.project.stypes.get(child.get('from'))
                if child_stype:
                    ignored = False
                    if self.ignore_dict:
                        if child_stype.info['code'] in self.ignore_dict['children']:
                            ignored = True

                    if not ignored:
                        self.child_items.append(gf.add_child_item(
                            self.tree_item,
                            self.search_widget,
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
                    self.search_widget,
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

    def query_snapshots(self):
        query_thread = tc.ServerThread(self.search_widget)

        query_thread.finished.connect(self.fill_snapshots_items)
        query_thread.kwargs = {}
        query_thread.routine = self.sobject.update_snapshots
        # query_thread.msleep(10)
        query_thread.start()
        query_thread.setPriority(QtCore.QThread.NormalPriority)

    def fill_snapshots_items(self, publish=False):
        # print self.children_states, 'CHILDREN STATES, fill_snapshots_items'

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

        # adding snapshots per process
        if not publish:
            for proc in self.process_items:
                if proc.process_items:
                    # may be buggy...
                    proc.info['is_expanded'] = True
                    proc.fill_snapshots_items()

                for key, val in self.sobject.process.iteritems():
                    # because it is dict, items could be in any position
                    if key == proc.process:
                        self.process_snapshot_items.append(proc.add_snapshots_items(val))
        else:
            # adding snapshots to publish
            for key, val in self.sobject.process.iteritems():
                if key == 'publish':
                    self.root_snapshot_items.append(gf.add_snapshot_item(
                            self.tree_item,
                            self.search_widget,
                            self.sobject,
                            self.stype,
                            'publish',
                            None,
                            val,
                            self.info,
                            self.sep_versions,
                            True,
                        ))

    def get_full_process_list(self):
        pipeline = self.get_current_process_pipeline()
        if pipeline:
            return pipeline.process

    def get_process_list(self, include_builtins=False, include_hierarchy=False):
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

    @gf.catch_error
    def get_notes_count(self):

        @gf.catch_error
        def notes_fill():
            notes_counts = notes_counts_query.result['notes']
            process_items_dict = {item.process: item for item in self.process_items}
            for key, val in notes_counts.iteritems():
                process_item = process_items_dict.get(key)
                if process_item:
                    process_item.set_notes_count(val)

        @gf.catch_error
        def children_fill():
            children_counts = notes_counts_query.result['stypes']
            child_items_dict = {item.child.get('from'): item for item in self.child_items}
            for key, val in children_counts.iteritems():
                child_item = child_items_dict.get(key)
                if child_item:
                    child_item.set_child_count_title(val)

        notes_counts_query = tc.ServerThread(self.search_widget)

        notes_counts_query.kwargs = dict(
            sobject=self.sobject,
            process=self.get_process_list(),
            children_stypes=self.get_children_list()
        )
        notes_counts_query.routine = tc.get_notes_count
        # notes_counts_query.msleep(10)
        notes_counts_query.start()
        notes_counts_query.setPriority(QtCore.QThread.LowPriority)

        notes_counts_query.finished.connect(notes_fill)
        notes_counts_query.finished.connect(children_fill)

    @gf.catch_error
    def expand_tree_item(self):
        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            self.fill_child_items()
            self.fill_process_items()
            self.fill_snapshots_items(publish=True)
            self.query_snapshots()

        self.get_notes_count()

        # Duct tape, to fix buggy items drawings
        tree_widget = self.get_current_tree_widget()
        tree_widget.resize(tree_widget.width() + 1, tree_widget.height())
        tree_widget.resize(tree_widget.width() - 1, tree_widget.height())

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

    def delete_current_sobject(self):

        sobject = self.get_sobject()
        print 'DELETING', sobject
        sobject.delete_sobject()

    def delete_current_snapshot_sobject(self):

        print 'DELETING SNAPSHOT', self.get_sobject()

    def mouseDoubleClickEvent(self, event):
        do_dbl_click = None
        if self.relates_to == 'checkin':
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin(), 'doubleClickSaveCheckBox')

        if not do_dbl_click:
            super(Ui_itemWidget, self).mouseDoubleClickEvent(event)
        else:
            if self.relates_to == 'checkin':
                self.search_widget.save_file()


class Ui_processItemWidget(QtGui.QWidget, ui_item_process.Ui_processItem):
    def __init__(self, sobject, stype, process, info, tree_item, pipeline, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'process'
        self.sobject = sobject
        self.stype = stype
        self.process = process
        self.pipeline = pipeline
        self.info = info
        self.tree_item = tree_item
        self.sep_versions = self.info['sep_versions']
        self.process_info = self.get_current_process_info()
        self.workflow = self.stype.project.workflow
        self.snapshot_items = []
        self.process_items = []
        self.process_snapshot_items = []
        # print(tree_item.text(0))
        # self.item_info = {}

        self.expand_state = False
        self.selected_state = False
        self.children_states = None

        self.search_widget = parent
        self.relates_to = 'checkin_out'


        # self.item_info[
        #     'description'] = 'This is {0} process item, there is no description, better click on Notes button'.format(
        #     self.process)

        self.controls_actions()

        self.create_ui()

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.expand_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def set_children_states(self, states):
        self.children_states = states

    def get_notes_count(self):

        def notes_fill():
            notes_counts = notes_counts_query.result['notes']
            process_items_dict = {item.process: item for item in self.process_items}
            for key, val in notes_counts.iteritems():
                process_item = process_items_dict.get(key)
                if process_item:
                    process_item.set_notes_count(val)

        notes_counts_query = tc.ServerThread(self.search_widget)
        notes_counts_query.kwargs = dict(
            sobject=self.sobject,
            process=self.get_process_list(),
            children_stypes=[]
        )
        notes_counts_query.routine = tc.get_notes_count
        notes_counts_query.start()

        notes_counts_query.finished.connect(notes_fill)

    def get_full_process_list(self):
        pipeline = self.get_current_process_pipeline()
        if pipeline:
            return pipeline.process

    def get_process_list(self):
        process = []
        for process_widget in self.process_items:
            process.append(process_widget.process)
        return process

    def get_snapshot(self):
        return None

    def get_current_process_info(self):
        pipeline = self.get_current_process_pipeline()
        process_info = None
        if pipeline:
            process_info = pipeline.process.get(self.process)

        return process_info

    def get_current_process_pipeline(self):
        # pipeline_code = self.sobject.info.get('pipeline_code')
        # pipeline = self.stype.pipeline.get(pipeline_code)
        if self.pipeline:
            return self.pipeline
        else:
            pipeline_code = self.sobject.info.get('pipeline_code')
            pipeline = self.stype.pipeline.get(pipeline_code)
            return pipeline

    def controls_actions(self):
        self.notesToolButton.clicked.connect(lambda: self.create_notes_widget())

    def create_ui(self):
        item_color = Qt4Gui.QColor(200, 200, 200)
        pipeline = self.get_current_process_pipeline()
        process = pipeline.get_process(self.process)
        if process:
            hex_color = process.get('color')
            color = None
            if hex_color:
                color = gf.hex_to_rgb(hex_color, tuple=True)
            if color:
                item_color = Qt4Gui.QColor(*color)

        if self.process:
            title = self.process.capitalize()
        else:
            title = 'Unnamed'
        if self.process_info.get('type') == 'hierarchy':
            self.tree_item.setIcon(0, gf.get_icon('fork', icons_set='ei', color=item_color, scale_factor=0.9))
        else:
            self.tree_item.setIcon(0, gf.get_icon('circle', color=item_color, scale_factor=0.55))

        self.label.setContentsMargins(4, 0, 0, 0)
        self.label.setText(title)

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
        title = self.sobject.info.get('name')
        if not title:
            title = self.sobject.info.get('title')
        if not title:
            title = self.sobject.info.get('code')
        self.note_widget.setWindowTitle(
            'Notes for: {0}, with process: {1}'.format(title, self.process))
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
        current_tree = self.search_widget.get_current_tree_widget()
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
                    self.search_widget,
                    self.sobject,
                    self.stype,
                    process,
                    self.info,
                    pipeline=pipeline
                )
                self.process_items.append(process_item)
                process_item.fill_subprocesses()

    def fill_snapshots_items(self):
        # print self.children_states, 'CHILDREN STATES, fill_snapshots_items'
        # adding snapshots per process
        for proc in self.process_items:
            for key, val in self.sobject.process.iteritems():
                # because it is dict, items could be in any position
                if key == proc.process:
                    self.process_snapshot_items.append(proc.add_snapshots_items(val))

    def add_snapshots_items(self, snapshots):

        snapshot_items = gf.add_snapshot_item(
            self.tree_item,
            self.search_widget,
            self.sobject,
            self.stype,
            self.process,
            self.pipeline,
            snapshots,
            self.info,
            self.sep_versions,
            False,
        )

        if self.children_states:
            gf.tree_state_revert(self.tree_item, self.children_states)

        return snapshot_items

    def update_items(self):
        self.sobject.update_snapshots()
        self.collapse_all_children()

        gf.add_snapshot_item(
            self.tree_item,
            self.search_widget,
            self.sobject,
            self.stype,
            self.process,
            self.pipeline,
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

        # pipeline = self.get_current_process_pipeline()
        # print pipeline.get_pipeline()
        # print pipeline.get_process(self.process)
        # print pipeline.get_info()
        # print pipeline.get_processes()

        if process:
            if custom:
                return u'{0}/{1}'.format(self.process, custom)
            else:
                return self.process
                # else:
                #     return ''

    def get_context_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process(self.process)
        if process:
            context_options = process.get('context_options')
            if context_options:
                return context_options.split('|')

    def get_checkin_mode_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process(self.process)
        if process:
            return process.get('checkin_mode')

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

    @gf.catch_error
    def expand_tree_item(self):
        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            self.fill_snapshots_items()

        self.get_notes_count()

        # Duct tape, to fix buggy items drawings
        tree_widget = self.get_current_tree_widget()
        tree_widget.resize(tree_widget.width() + 1, tree_widget.height())
        tree_widget.resize(tree_widget.width() - 1, tree_widget.height())

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
                self.search_widget.save_file()


class Ui_snapshotItemWidget(QtGui.QWidget, ui_item_snapshot.Ui_snapshotItem):
    def __init__(self, sobject, stype, process, pipeline, context, snapshot, info, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'snapshot'
        self.sobject = sobject
        self.stype = stype
        self.process = process
        self.pipeline = pipeline
        self.context = context
        self.snapshot = None
        self.current_snapshot = snapshot
        self.info = info
        self.tree_item = tree_item
        self.expand_state = False
        self.selected_state = False
        self.children_states = None

        self.search_widget = parent
        self.relates_to = 'checkin_out'

        self.files = {}

        if snapshot:
            self.snapshot = snapshot[0].snapshot
            self.files = snapshot[0].files

        self.create_ui()

    def create_ui(self):
        hidden = ['icon', 'web', 'playblast']

        if self.snapshot:
            self.check_main_file()

            self.commentLabel.setText(gf.to_plain_text(self.snapshot['description'], 80))
            self.dateLabel.setText(self.snapshot['timestamp'].split('.')[0].replace(' ', ' \n'))
            self.authorLabel.setText(self.snapshot['login'] + ':')
            self.verRevLabel.setText(gf.get_ver_rev(self.snapshot['version'], self.snapshot['revision']))

            file_ext = 'err'
            for key, fl in self.files.iteritems():
                if key not in hidden:
                    if self.snapshot.get('repo'):
                        self.sizeLabel.setStyleSheet(self.get_repo_color())
                    if not self.isEnabled():
                        self.fileNameLabel.setText('{0}, (File Missing)'.format(fl[0]['file_name']))
                    else:
                        self.fileNameLabel.setText(fl[0]['file_name'])
                    file_ext = gf.get_ext(fl[0]['file_name'])
                    # print fl
                    self.sizeLabel.setText(gf.sizes(fl[0]['st_size']))

            if not self.set_preview():
                self.previewLabel.setText(
                    '<span style=" font-size:12pt; font-weight:600; color:#828282;">{0}</span>'.format(file_ext)
                )
        else:
            if self.get_checkin_mode_options() == 'multi_file':
                self.set_multiple_files_view()
            else:
                self.set_no_versionless_view()

    def is_versionless(self):
        snapshot = self.get_snapshot()
        if snapshot:
            return snapshot.is_versionless()
        else:
            # only versionless can be displayed without snapshot!
            return True

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.expand_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def set_children_states(self, states):
        self.children_states = states

    def check_main_file(self):
        snapshot = self.get_snapshot()
        if snapshot:
            files_objects = snapshot.get_files_objects()
            if files_objects:
                first_file = files_objects[0]
                if first_file:
                    if os.path.exists(first_file.get_full_abs_path()):
                        self.setEnabled(True)
                    else:
                        self.setDisabled(True)

    def set_multiple_files_view(self):
        pixmap = gf.get_icon('folder-sign', icons_set='ei', opacity=0.5, scale_factor=0.5).pixmap(64, Qt4Gui.QIcon.Normal)
        self.previewLabel.setPixmap(pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation))
        self.fileNameLabel.setText('Multiple checkin: {0} '.format(self.context))
        self.commentLabel.setText('Snapshots count: {0}; Files count: {1};'.format(len(self.get_all_versions_snapshots()), len(self.get_all_versions_files())))

        self.dateLabel.deleteLater()
        self.sizeLabel.deleteLater()
        self.authorLabel.deleteLater()

    def set_no_versionless_view(self):
        pixmap = gf.get_icon('exclamation-circle', opacity=0.5, scale_factor=0.6).pixmap(64, Qt4Gui.QIcon.Normal)
        self.previewLabel.setPixmap(pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation))
        self.fileNameLabel.setText('Versionless for {0} not found'.format(self.context))
        self.commentLabel.setText('Check this snapshot, and update versionless')
        self.dateLabel.deleteLater()
        self.sizeLabel.deleteLater()
        self.authorLabel.deleteLater()

    def set_preview(self):
        snapshot = self.get_snapshot()
        if snapshot:
            preview_files_objects = snapshot.get_previewable_files_objects()
            if preview_files_objects:
                icon_previw = preview_files_objects[0].get_icon_preview()
                if icon_previw:
                    previw_abs_path = icon_previw.get_full_abs_path()
                    pixmap = Qt4Gui.QPixmap(previw_abs_path)
                    if not pixmap.isNull():
                        self.previewLabel.setPixmap(pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation))
                        return True
                    else:
                        return False

    def get_all_versions_snapshots(self):
        process = self.sobject.process.get(self.process)
        context = process.contexts.get(self.context)
        # print context.versions
        # print context.versionless
        return context.versions

    def get_all_versions_files(self):
        files = []
        for sn in self.get_all_versions_snapshots().values():
            files.extend(sn.get_files_objects())

        return files

    def get_snapshot(self):
        if self.current_snapshot:
            return self.current_snapshot[0]

    def get_current_tree_widget(self):
        current_tree = self.search_widget.get_current_tree_widget()
        return current_tree.resultsTreeWidget

    def get_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_tree_widget()
        return current_tree.indexFromItem(self.get_parent_item())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_tree_widget()
        parent_item_widget = current_tree.itemWidget(self.get_parent_item(), 0)
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
            repo_colors = env_tactic.get_base_dir(self.snapshot['repo'])['value'][2]
        else:
            repo_colors = [96, 96, 96]

        stylesheet = 'QLabel{background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(%s, %s, %s, 96));' \
                     'border - bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));' \
                     'padding: 0px;}' % tuple(repo_colors)

        return stylesheet

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return u'{0}/{1}'.format(self.process, custom)
            else:
                return self.process
        else:
            context = self.context.split('/')[-1]
            if context == self.process:
                context = ''
            return context

    def get_context_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process(self.process)
        if process:
            context_options = process.get('context_options')
            if context_options:
                return context_options.split('|')

    def get_checkin_mode_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process(self.process)
        if process:
            return process.get('checkin_mode')

    def get_current_process_pipeline(self):
        if self.pipeline:
            return self.pipeline
        else:
            pipeline_code = self.sobject.info.get('pipeline_code')
            if pipeline_code and self.stype.pipeline:
                return self.stype.pipeline.get(pipeline_code)

    def get_current_process_info(self):
        pipeline = self.get_current_process_pipeline()
        process_info = None
        if pipeline:
            process_info = pipeline.process.get(self.process)
        if not process_info and self.process:
            process_info = {'name': self.process}

        return process_info

    def get_full_process_list(self):
        pipeline = self.get_current_process_pipeline()
        if pipeline:
            return pipeline.process

    def get_process_list(self):
        pipeline = self.get_current_process_pipeline()
        if pipeline:
            return pipeline.process.keys()
        else:
            return []

    def get_search_key(self):
        return self.snapshot.get('__search_key__')

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

    def delete_current_sobject(self):

        snapshot = self.get_snapshot()
        print 'DELETING', snapshot
        snapshot.delete_sobject()

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
            return 'skey://{0}'.format(self.sobject.info['__search_key__'])

    def get_description(self):
        if self.snapshot:
            return self.snapshot['description']
        else:
            return 'No Description for this item!'

    def update_description(self, new_description):
        self.snapshot['description'] = new_description
        self.commentLabel.setText(new_description)

    @gf.catch_error
    def expand_tree_item(self):
        # Duct tape, to fix buggy items drawings
        tree_widget = self.get_current_tree_widget()
        tree_widget.resize(tree_widget.width() + 1, tree_widget.height())
        tree_widget.resize(tree_widget.width() - 1, tree_widget.height())

    def collapse_tree_item(self):
        pass

    def resizeEvent(self, event):
        self.tree_item.setSizeHint(0, QtCore.QSize(self.width(), 25 + self.commentLabel.height()))

    def mouseDoubleClickEvent(self, event):
        if self.relates_to == 'checkin':
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin(), 'doubleClickSaveCheckBox')
        else:
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkout(), 'doubleClickOpenCheckBox')

        if not do_dbl_click:
            super(Ui_snapshotItemWidget, self).mouseDoubleClickEvent(event)
        else:
            if self.relates_to == 'checkin':
                self.search_widget.save_file()
            else:
                self.search_widget.open_file()


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

        self.expand_state = False
        self.selected_state = False
        self.children_states = None

        self.search_widget = parent
        self.project = self.search_widget.project

        self.create_children_button()

        self.controls_actions()

        self.create_ui()

    def create_ui(self):
        self.addNewSObjectToolButton.setIcon(gf.get_icon('plus-square-o'))

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.expand_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def set_children_states(self, states):
        self.children_states = states

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
            self.tree_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        self.addNewSObjectToolButton.setText('| {0}'.format(count))

    def create_children_button(self):
        title = self.stype.info.get('title')
        if not title:
            title = 'untitled'
        self.title = title.capitalize()
        self.childrenToolButton.setIcon(gf.get_icon('list', icons_set='ei', scale_factor=0.8))
        self.childrenToolButton.setText(self.title)

        self.set_style()

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
            effect.setColor(Qt4Gui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
            # blur.setColor(Qt4Gui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
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

    @gf.catch_error
    def add_new_sobject(self):
        self.add_sobject = addsobject_widget.Ui_addTacticSobjectWidget(
            stype=self.stype,
            parent_stype=self.search_widget.stype,
            item=self,
            parent=self)
        self.add_sobject.show()

    @gf.catch_error
    def expand_tree_item(self):
        self.add_child_sobjects()
        self.childrenToolButton.setCheckable(True)
        self.childrenToolButton.setChecked(True)

        # Duct tape, to fix buggy items drawings
        tree_widget = self.get_current_tree_widget()
        tree_widget.resize(tree_widget.width() + 1, tree_widget.height())
        tree_widget.resize(tree_widget.width() - 1, tree_widget.height())

    def collapse_tree_item(self):
        self.childrenToolButton.setChecked(False)

    def get_current_tree_widget(self):
        current_tree = self.search_widget.get_current_tree_widget()
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

    @gf.catch_error
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
        # TODO Threading here
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
                gf.add_sobject_item(
                    self.tree_item,
                    self.search_widget,
                    sobject,
                    stype,
                    self.info,
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
