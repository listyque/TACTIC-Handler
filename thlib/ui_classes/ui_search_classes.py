# -*- coding: utf-8 -*-
# Search UI classes and methods

# Copyright (c) 2019, Krivospitskiy Alexey, <listy@live.ru>, https://github.com/listyque/TACTIC-Handler
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0


__all__ = ['Ui_navigationWidget', 'Ui_searchWidget', 'Ui_searchOptionsWidget',
           'Ui_filterWidget', 'Ui_processFilterDialog', 'Ui_advancedSearchWidget']


import collections
import itertools
from functools import partial
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_inst, env_server, cfg_controls, env_read_config, env_write_config
import thlib.global_functions as gf
import thlib.tactic_classes as tc
from thlib.ui_classes.ui_custom_qwidgets import SuggestedLineEdit, Ui_horizontalCollapsableWidget, Ui_collapsableWidget, Ui_extendedTreeWidget, Ui_extendedTabBarWidget, StyledToolButton, StyledComboBox
from thlib.ui_classes.ui_assets_browser_classes import Ui_assetsBrowserWidget

DEFAULT_FILTER = ('name', 'EQI', '')
EXPR_FILTER = ('_expression', 'in', "@SOBJECT(sthpw/task['assigned', $LOGIN])")


def get_suggestion_filter(column, search_text, possible_columns, default_filter=None):
    filters = ['begin', (column, 'EQI', search_text)]

    if 'keywords' in possible_columns:
        filters.append(('keywords', 'EQI', search_text))

    if 'description' in possible_columns:
        filters.append(('description', 'EQI', search_text))

    filters.append('or')

    if default_filter:
        filters.append(default_filter)
        filters.append('and')

    return filters


def get_match_list_by_type(column_type):
    match_list = [
        ('Is', '='),
        ('Is not', '!='),
        ('Contains', 'EQI'),
        ('Does not contain', 'NEQI'),
        ('Is empty', None),
        ('Is not empty', 'like'),
        ('Starts with', 'like'),
        ('Ends with', 'like'),
        ('Does not starts with', 'not like'),
        ('Does not end with', 'not like'),
        ('In', 'in'),
        ('Not in', 'not in'),
        ('Is distinct', ''),
    ]

    if column_type == 'boolean':
        match_list = [
            ('Is', '='),
            ('Is not', '!='),
            ('Is empty', None),
            ('Is not empty', None),
        ]
    elif column_type in ['integer', 'float', 'currency']:
        match_list = [
            ('is equal to', ''),
            ('is greater than', ''),
            ('is less than', ''),
            ('in', 'in'),
            ('not in', 'not in'),
            ('is empty', None),
            ('is not empty', ''),
            ('is distinct', ''),
        ]
    elif column_type in ['time', 'timestamp', 'datetime2']:
        match_list = [
            ('is newer than', ''),
            ('is older than', ''),
            ('is on', ''),
            ('is empty', None),
            ('is not empty', ''),
        ]
    elif column_type in ['login']:
        match_list = [
            ('is', '='),
            ('is not', '!='),
            ('contains', 'EQI'),
            ('does not contain', 'NEQI'),
            ('is empty', None),
            ('is not empty', ''),
            ('starts with', ''),
            ('ends with', ''),
        ]
    elif column_type in ['_expression']:
        match_list = [
            ('Have', 'in'),
            ('Do not have', 'not in'),
            # ('Match (slow)', 'match'),
            # ('Do not match (slow)', 'do not match'),
        ]
    elif column_type in ['timecode']:
        match_list = [
            ('is timecode before', '<='),
            ('is timecode after', '>='),
            ('is timecode equal', '='),
            ('is empty', None),
        ]

    return match_list


class Ui_processFilterDialog(QtGui.QDialog):
    def __init__(self, parent_ui, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setSizeGripEnabled(True)
        # self.setWindowFlags(QtCore.Qt.ToolTip)
        # self.setWindowFlags(QtCore.Qt.Popup)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.checkin_out_widget = parent_ui
        self.project = project
        self.stype = stype
        self.all_items_dict = {
            'children': [],
            'processes': {},
            'builtins': [],
        }

        title = self.stype.info.get('title')
        if not title:
            title = self.stype.info.get('name')
        elif not title:
            title = self.stype.info.get('code')

        self.setWindowTitle('Pipeline for: {0}'.format(title))

        self.create_tree_widget()
        self.fill_tree_widget()
        self.fit_to_content_tree_widget()
        self.create_buttons()

        self.none = False

        self.controls_actions()
        self.readSettings()

    def get_ignore_dict(self):
        ignore_dict = {
            'children': [],
            'processes': {},
            'builtins': [],
            'show_builtins': False
        }

        build_dict = False

        # get builtins ignore list
        for builtin in self.all_items_dict['builtins']:
            if builtin.checkState(0) == QtCore.Qt.Unchecked:
                build_dict = True
                ignore_dict['builtins'].append(builtin.data(1, 0))

        # get children ignore list
        for child in self.all_items_dict['children']:
            if child.checkState(0) == QtCore.Qt.Unchecked:
                build_dict = True
                ignore_dict['children'].append(child.data(1, 0))

        # get processes ignore list
        for name, processes in self.all_items_dict['processes'].items():
            ignored_process = []
            for process in processes:
                if process.checkState(0) == QtCore.Qt.Unchecked:
                    build_dict = True
                    ignored_process.append(process.data(1, 0))
            ignore_dict['processes'][name] = ignored_process

        if build_dict:
            return ignore_dict
        else:
            return ''

    def set_from_ignore_dict(self, ignore_dict):
        if ignore_dict:
            # return from builtins ignore list
            for builtin in self.all_items_dict['builtins']:
                if builtin.data(1, 0) in ignore_dict['builtins']:
                    builtin.setCheckState(0, QtCore.Qt.Unchecked)

            # get children ignore list
            for child in self.all_items_dict['children']:
                if child.data(1, 0) in ignore_dict['children']:
                    child.setCheckState(0, QtCore.Qt.Unchecked)

            # get processes ignore list
            for name, processes in self.all_items_dict['processes'].items():
                for process in processes:
                    ignore_list = ignore_dict['processes'].get(name)
                    if not ignore_list:
                        ignore_list = []
                    if process.data(1, 0) in ignore_list:
                        process.setCheckState(0, QtCore.Qt.Unchecked)

    def controls_actions(self):

        self.none_button.clicked.connect(lambda: self.switch_items('none'))
        self.all_process_button.clicked.connect(lambda: self.switch_items('process'))
        self.all_with_builtins_button.clicked.connect(lambda: self.switch_items('builtins'))
        self.all_children_button.clicked.connect(lambda: self.switch_items('children'))

        self.save_button.clicked.connect(self.save_and_refresh)
        self.save_close_button.clicked.connect(self.close)

        self.tree_widget.itemChanged.connect(self.check_tree_items)

    def check_tree_items(self, changed_item):
        if len(self.tree_widget.selectedItems()) > 1:
            for item in self.tree_widget.selectedItems():
                item.setCheckState(0, changed_item.checkState(0))

    def switch_items(self, item_type='none'):

        # TODO Remove this, and make it work through ignore dict

        if self.none:
            self.none = False
        else:
            self.none = True

        if item_type == 'none':
            for item in self.child_items + self.process_items + self.builtin_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

        if item_type == 'process':
            for item in self.process_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

        if item_type == 'builtins':
            for item in self.builtin_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

        if item_type == 'children':
            for item in self.child_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

    def create_buttons(self):

        self.none_button = QtGui.QPushButton('None / All')
        self.all_process_button = QtGui.QPushButton('Toggle Process')
        self.all_with_builtins_button = QtGui.QPushButton('Toggle Builtins')
        self.all_children_button = QtGui.QPushButton('Toggle Children')

        self.save_button = QtGui.QPushButton('Save')
        self.save_close_button = QtGui.QPushButton('Save and close')

        self.grid.addWidget(self.none_button, 1, 0, 1, 1)
        self.grid.addWidget(self.all_process_button, 1, 1, 1, 1)
        self.grid.addWidget(self.all_with_builtins_button, 2, 0, 1, 1)
        self.grid.addWidget(self.all_children_button, 2, 1, 1, 1)

        self.grid.addWidget(self.save_button, 3, 0, 1, 1)
        self.grid.addWidget(self.save_close_button, 3, 1, 1, 1)

    def create_tree_widget(self):

        self.grid = QtGui.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.setLayout(self.grid)

        self.tree_widget = QtGui.QTreeWidget(self)
        self.tree_widget.setTabKeyNavigation(True)
        self.tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tree_widget.setAllColumnsShowFocus(True)
        self.tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setObjectName('tree_widget')
        self.tree_widget.setStyleSheet(gf.get_qtreeview_style())
        # self.tree_widget.setRootIsDecorated(False)

        self.grid.addWidget(self.tree_widget, 0, 0, 1, 2)

    def fill_tree_widget(self):
        self.child_items = []
        self.process_items = []
        self.builtin_items = []

        # Children process
        for child in self.stype.schema.children:
            child_stype = self.project.stypes.get(child['from'])
            if child_stype:
                stype_title = child_stype.info.get('title')
                if not stype_title:
                    stype_title = child_stype.info.get('code')
                top_item = QtGui.QTreeWidgetItem()
                top_item.setText(0, stype_title.capitalize() + ' (child)')
                top_item.setCheckState(0, QtCore.Qt.Checked)
                top_item.setData(1, 0, child_stype.info.get('code'))
                self.tree_widget.addTopLevelItem(top_item)
                self.child_items.append(top_item)
                if child_stype.pipeline:
                    for pipeline in child_stype.pipeline.itervalues():
                        title = pipeline.info.get('name')
                        if not title:
                            title = pipeline.info.get('code')

                        item = QtGui.QTreeWidgetItem()
                        item.setText(0, title.capitalize())
                        item.setData(1, 0, pipeline.info.get('code'))
                        top_item.addChild(item)
                        top_item.setExpanded(True)
                        child_items = []
                        for key, val in pipeline.process.items():
                            child_item = QtGui.QTreeWidgetItem()
                            child_item.setText(0, key.capitalize())
                            child_item.setCheckState(0, QtCore.Qt.Checked)
                            child_item.setData(1, 0, key)
                            item.addChild(child_item)
                            item.setExpanded(True)
                            self.process_items.append(child_item)
                            child_items.append(child_item)

                        self.all_items_dict['processes'][pipeline.info.get('code')] = child_items
                self.all_items_dict['children'].append(top_item)

        # Actual process
        if self.stype.pipeline:

            for pipeline in self.stype.pipeline.itervalues():
                title = pipeline.info.get('name')
                if not title:
                    title = pipeline.info.get('code')

                top_item = QtGui.QTreeWidgetItem()
                top_item.setText(0, title.capitalize())
                top_item.setData(1, 0, pipeline.info.get('code'))
                self.tree_widget.addTopLevelItem(top_item)

                child_items = []
                for key, val in pipeline.process.items():
                    child_item = QtGui.QTreeWidgetItem()
                    child_item.setText(0, key.capitalize())
                    child_item.setCheckState(0, QtCore.Qt.Checked)
                    child_item.setData(1, 0, key)
                    top_item.addChild(child_item)
                    top_item.setExpanded(True)
                    self.process_items.append(child_item)
                    child_items.append(child_item)

                self.all_items_dict['processes'][pipeline.info.get('code')] = child_items

        # Hidden process
        builtin_items = []
        for key in ['publish', 'attachment', 'icon']:
            top_item = QtGui.QTreeWidgetItem()
            top_item.setText(0, key.capitalize() + ' (builtin)')
            top_item.setCheckState(0, QtCore.Qt.Checked)
            top_item.setData(1, 0, key)
            self.tree_widget.addTopLevelItem(top_item)
            self.builtin_items.append(top_item)
            builtin_items.append(top_item)

        self.all_items_dict['builtins'] = builtin_items

    def fit_to_content_tree_widget(self):

        items_count = 0
        for item in QtGui.QTreeWidgetItemIterator(self.tree_widget):
            items_count += 1

        row_height = items_count * self.tree_widget.sizeHintForRow(0) + 80
        mouse_pos = Qt4Gui.QCursor.pos()
        self.setGeometry(mouse_pos.x(), mouse_pos.y(), 250, row_height)

    def readSettings(self):
        tab_name = self.checkin_out_widget.objectName().split('/')
        group_path = 'ui_search/{0}/{1}/{2}/{3}'.format(
            self.checkin_out_widget.relates_to,
            self.project.info['type'],
            self.project.info['code'],
            tab_name[1]
        )

        self.set_from_ignore_dict(
            env_read_config(
                filename='process_ignore_dict',
                unique_id=group_path,
                long_abs_path=True
            )
        )

    def writeSettings(self):
        tab_name = self.checkin_out_widget.objectName().split('/')
        group_path = 'ui_search/{0}/{1}/{2}/{3}'.format(
            self.checkin_out_widget.relates_to,
            self.project.info['type'],
            self.project.info['code'],
            tab_name[1]
        )
        env_write_config(
            self.get_ignore_dict(),
            filename='process_ignore_dict',
            unique_id=group_path,
            long_abs_path=True
        )

    def save_and_refresh(self):
        self.writeSettings()

        search_wdg = self.checkin_out_widget.get_search_widget()
        search_wdg.search_results_widget.refresh_current_results()
        # self.parent_ui.refresh_current_results()

    # def mousePressEvent(self, event):
    #     self.offset = event.pos()
    #
    # def mouseMoveEvent(self, event):
    #     x = event.globalX()
    #     y = event.globalY()
    #     x_w = self.offset.x()
    #     y_w = self.offset.y()
    #     self.move(x - x_w, y - y_w)

    def closeEvent(self, event):
        self.save_and_refresh()
        event.accept()


class Ui_searchWidget(QtGui.QWidget):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.stype = stype
        self.project = project

        self.group_by_columns = []
        self.sort_by = None

        self.create_ui()

    def create_ui(self):

        self.searchWidgetGridLayout = QtGui.QGridLayout(self)
        self.searchWidgetGridLayout.setContentsMargins(0, 0, 0, 0)
        self.searchWidgetGridLayout.setSpacing(0)
        self.searchWidgetGridLayout.setObjectName("searchWidgetGridLayout")
        self.expandingLayout = QtGui.QVBoxLayout()
        self.expandingLayout.setObjectName("expandingLayout")
        self.searchWidgetGridLayout.addLayout(self.expandingLayout, 0, 1, 1, 1)
        self.gearMenuToolButton = StyledToolButton()
        self.gearMenuToolButton.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.gearMenuToolButton.setArrowType(QtCore.Qt.NoArrow)
        self.gearMenuToolButton.setObjectName("gearMenuToolButton")
        self.searchWidgetGridLayout.addWidget(self.gearMenuToolButton, 0, 2, 1, 1)
        self.searchFiltersVerticalLayout = QtGui.QVBoxLayout()
        self.searchFiltersVerticalLayout.setSpacing(0)
        self.searchFiltersVerticalLayout.setObjectName("searchFiltersVerticalLayout")
        self.searchWidgetGridLayout.addLayout(self.searchFiltersVerticalLayout, 1, 0, 1, 3)
        self.searchWidgetGridLayout.setColumnStretch(0, 1)

        self.create_search_line_edit()

        self.create_search_results_widget()
        self.create_gear_menu_popup()
        self.create_collapsable_toolbar()

        self.controls_actions()

    def controls_actions(self):
        self.search_line_edit.returnPressed.connect(self.do_search)
        self.search_line_edit.textEdited.connect(self.search_line_edit_text_edited)
        self.search_line_edit.item_selected.connect(self.do_search)
        self.search_line_edit.item_clicked.connect(self.do_search)

        self.add_new_tab_button.clicked.connect(self.add_tab_button_click)
        self.refresh_tab_button.clicked.connect(self.update_current_search_results)

        self.results_tab_widget.tabCloseRequested.connect(self.close_tab)
        self.results_tab_widget.middle_mouse_pressed.connect(self.close_tab)
        self.results_tab_widget.currentChanged.connect(self.current_tab_changed)

    def create_search_line_edit(self):
        self.search_line_edit = SuggestedLineEdit(self.stype, self.project, parent=self)
        self.search_line_edit.setObjectName('search_line_edit')
        self.search_line_edit.setToolTip('Enter Your search query here')
        self.searchWidgetGridLayout.addWidget(self.search_line_edit, 0, 0, 1, 1)

    def create_search_results_widget(self):

        self.search_results_widget = QtGui.QWidget(self)

        self.resultsLayout = QtGui.QVBoxLayout()
        self.resultsLayout.setSpacing(0)
        self.resultsLayout.setContentsMargins(0, 0, 0, 0)
        self.search_results_widget.setLayout(self.resultsLayout)

        self.create_results_tab_widget()
        self.create_tool_buttons()

        self.searchWidgetGridLayout.addWidget(self.search_results_widget, 2, 0, 1, 3)
        self.searchWidgetGridLayout.setRowStretch(2, 1)

    def create_results_tab_widget(self):
        self.results_tab_widget = Ui_extendedTabBarWidget(self)
        self.results_tab_widget.setMovable(True)
        self.results_tab_widget.setObjectName('results_tab_widget')
        self.results_tab_widget.customize_ui()
        self.results_tab_widget.set_corner_offset(72)

        self.resultsLayout.addWidget(self.results_tab_widget)

    def add_tab_button_click(self):
        self.search_line_edit.setFocus()
        self.add_tab()

    def fill_tasks_tastuses_menu(self, menu):

        # Filling users tasks filter
        current_login = env_inst.get_current_login_object()
        # print env_inst.get_all_logins()
        # print current_login.get_login_groups()

        menu.addSeparator()
        users_menu = menu.addMenu('Pick User')
        users_menu.setIcon(gf.get_icon('account', icons_set='mdi', scale_factor=1.1))

        for login_group in current_login.get_login_groups():
            group_menu = users_menu.addMenu(login_group.get_pretty_name())
            group_menu.setIcon(gf.get_icon('account-multiple', icons_set='mdi', scale_factor=1.1))

            default_group_action = QtGui.QAction('Whole Group', self)
            default_group_action.setIcon(gf.get_icon('account-multiple-plus', icons_set='mdi', scale_factor=1.1))
            group_menu.addAction(default_group_action)

            group_logins = login_group.get_logins()
            if group_logins:
                group_menu.addSeparator()
                for login in group_logins:
                    login_action = QtGui.QAction(login.get_display_name(), self)
                    login_action.setIcon(gf.get_icon('account-plus', icons_set='mdi', scale_factor=1.1))
                    group_menu.addAction(login_action)

        workflow = self.stype.get_workflow()
        tasks_workflow = workflow.get_by_stype_code('sthpw/task')

        stype_pipelines = self.stype.get_pipeline()

        # filling all possible tasks statuses by processes
        if stype_pipelines:

            menu.addSeparator()
            for stype_pipeline in stype_pipelines.values():
                for stype_process in stype_pipeline.get_all_pipeline_names():
                    process_menu = menu.addMenu(stype_pipeline.get_process_label(stype_process))

                    # colorizing processes
                    process_info = stype_pipeline.get_process_info(stype_process)
                    process_hex_color = process_info.get('color')
                    if process_hex_color:
                        process_color = gf.hex_to_rgb(process_hex_color, tuple=True)
                        if process_color:
                            process_color = Qt4Gui.QColor(*process_color)
                            process_menu.setIcon(gf.get_icon('circle', color=process_color, scale_factor=0.6))
                    else:
                        process_menu.setIcon(gf.get_icon('circle', scale_factor=0.6))

                    task_pipeline = process_info.get('task_pipeline')

                    # use default tasks pipeline
                    if not task_pipeline:
                        task_pipeline = 'task'

                    default_task_action = QtGui.QAction('Show All Statuses', self)
                    default_task_action.setIcon(gf.get_icon('circle', scale_factor=0.6))
                    process_menu.addAction(default_task_action)
                    process_menu.addSeparator()
                    if tasks_workflow.get(task_pipeline):
                        for task_process in tasks_workflow[task_pipeline].get_all_pipeline_names():
                            task_status_action = QtGui.QAction(task_process, self)

                            # colorizing processes
                            task_process_info = tasks_workflow[task_pipeline].get_process_info(task_process)
                            task_process_hex_color = task_process_info.get('color')
                            if task_process_hex_color:
                                task_process_color = gf.hex_to_rgb(task_process_hex_color, tuple=True)
                                if task_process_color:
                                    task_process_color = Qt4Gui.QColor(*task_process_color)
                                    task_status_action.setIcon(gf.get_icon('circle', color=task_process_color, scale_factor=0.6))
                            else:
                                task_status_action.setIcon(gf.get_icon('circle', scale_factor=0.6))

                            process_menu.addAction(task_status_action)

                menu.addSeparator()

                # Filling task statuses by all pipelines used with this search type
                task_pipelines = stype_pipeline.get_all_tasks_pipelines_names()
                task_pipelines.append('task')

                for task_pipeline in task_pipelines:
                    pipeline_menu = menu.addMenu(task_pipeline)
                    if tasks_workflow.get(task_pipeline):
                        for task_process in tasks_workflow[task_pipeline].get_all_pipeline_names():

                            task_status_action = QtGui.QAction(task_process, self)

                            # colorizing processes
                            task_process_info = tasks_workflow[task_pipeline].get_process_info(task_process)
                            task_process_hex_color = task_process_info.get('color')
                            if task_process_hex_color:
                                task_process_color = gf.hex_to_rgb(task_process_hex_color, tuple=True)
                                if task_process_color:
                                    task_process_color = Qt4Gui.QColor(*task_process_color)
                                    task_status_action.setIcon(
                                        gf.get_icon('circle', color=task_process_color, scale_factor=0.6))
                            else:
                                task_status_action.setIcon(gf.get_icon('circle', scale_factor=0.6))

                            pipeline_menu.addAction(task_status_action)

    def create_tool_buttons(self):
        self.left_buttons_layout = QtGui.QHBoxLayout()
        self.left_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.left_buttons_layout.setSpacing(0)

        self.left_buttons_widget = QtGui.QWidget(self)
        self.left_buttons_widget.setLayout(self.left_buttons_layout)
        self.left_buttons_widget.setMinimumSize(36, 36)

        self.add_new_tab_button = StyledToolButton(small=True, shadow_enabled=True, square_type=False)
        self.add_new_tab_button.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1.2))
        self.add_new_tab_button.setToolTip('Add new Search Tab')

        self.add_filter_button = StyledToolButton(small=True, shadow_enabled=True, square_type=True)
        self.add_filter_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.add_filter_button.setIcon(gf.get_icon('filter', icons_set='mdi', scale_factor=0.9))
        self.add_filter_button.setToolTip('Add Filter to Tab')

        self.filter_by_tasks_menu = QtGui.QMenu('Tasks', self.add_filter_button)
        self.filter_by_tasks_menu.setIcon(gf.get_icon('calendar-check', icons_set='mdi', scale_factor=1))
        self.my_tasks_action = QtGui.QAction('My Tasks', self.add_filter_button)
        self.my_tasks_action.setIcon(gf.get_icon('account-details', icons_set='mdi', scale_factor=1.1))
        self.my_tasks_action.triggered.connect(self.do_my_tasks_action)
        self.filter_by_tasks_menu.addAction(self.my_tasks_action)
        self.filter_by_tasks_menu.setTearOffEnabled(True)
        self.filter_by_tasks_menu.setWindowTitle('Tasks Filters: {0}'.format(self.stype.get_pretty_name()))
        self.fill_tasks_tastuses_menu(self.filter_by_tasks_menu)

        self.filter_by_snapshots_menu = QtGui.QMenu('Snapshots', self.add_filter_button)
        self.filter_by_snapshots_menu.setIcon(gf.get_icon('file-document-outline', icons_set='mdi', scale_factor=1))
        self.my_snapshots_action = QtGui.QAction('My Snapshots', self.add_filter_button)
        self.my_snapshots_action.setIcon(gf.get_icon('account-check', icons_set='mdi', scale_factor=1.1))
        self.filter_by_snapshots_menu.addAction(self.my_snapshots_action)

        # TODO snapshots by users, snapshots by processes, snapshots by date
        #self.fill_snapshot_filters_menu(self.filter_by_snapshots_menu)

        self.filter_by_preset_menu = QtGui.QMenu('Presets', self.add_filter_button)
        self.filter_by_preset_menu.setIcon(gf.get_icon('heart', icons_set='mdi', scale_factor=1))
        self.edit_presets_action = QtGui.QAction('Edit Presets', self.add_filter_button)
        self.edit_presets_action.setIcon(gf.get_icon('circle-edit-outline', icons_set='mdi', scale_factor=1))
        self.filter_by_preset_menu.addAction(self.edit_presets_action)

        self.add_filter_button.addAction(self.filter_by_tasks_menu.menuAction())
        self.add_filter_button.addAction(self.filter_by_snapshots_menu.menuAction())
        self.add_filter_button.addAction(self.filter_by_preset_menu.menuAction())

        self.left_buttons_layout.addWidget(self.add_new_tab_button)
        self.left_buttons_layout.addWidget(self.add_filter_button)

        self.history_tab_button = StyledToolButton(small=True, shadow_enabled=True, square_type=False)
        self.history_tab_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.history_tab_button.setIcon(gf.get_icon('history', icons_set='mdi', scale_factor=1.2))
        self.history_tab_button.setToolTip('History of closed Search Results')

        self.refresh_tab_button = StyledToolButton(small=True, shadow_enabled=True, square_type=False)
        self.refresh_tab_button.setIcon(gf.get_icon('refresh', icons_set='mdi', scale_factor=1.2))
        self.refresh_tab_button.setToolTip('Refresh current Results')

        self.right_buttons_layout = QtGui.QHBoxLayout()
        self.right_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.right_buttons_layout.setSpacing(0)

        self.right_buttons_widget = QtGui.QWidget()
        self.right_buttons_widget.setLayout(self.right_buttons_layout)
        self.right_buttons_widget.setMinimumSize(20, 36)

        self.group_by_button = StyledToolButton(small=True, shadow_enabled=True, square_type=True)
        self.group_by_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.group_by_button.setIcon(gf.get_icon('group', icons_set='mdi', scale_factor=1))
        self.group_by_button.setToolTip('Group Items By')

        self.no_grouping_button = QtGui.QAction('No Grouping', self.group_by_button, checkable=True)
        self.no_grouping_button.setIcon(gf.get_icon('check-circle', icons_set='mdi', scale_factor=1))
        self.no_grouping_button.triggered.connect(partial(self.toggle_goups_by, self.no_grouping_button))
        self.no_grouping_button.setCheckable(True)
        self.no_grouping_button.setChecked(True)

        columns = self.stype.get_columns_info()

        if columns:

            temporary_ignore = ['timestamp', 's_status', 'id']
            self.group_by_actions = [self.no_grouping_button]
            for column, types in columns.items():
                if column not in temporary_ignore:
                    column_action = QtGui.QAction(column.replace('_', ' ').title(), self.group_by_button, checkable=True)
                    column_action.setData(column)
                    column_action.setIcon(gf.get_icon('checkbox-blank-circle-outline', icons_set='mdi', scale_factor=1))
                    column_action.triggered.connect(partial(self.toggle_goups_by, column_action))
                    column_action.setCheckable(True)
                    self.group_by_actions.append(column_action)

        self.group_by_button.addActions(self.group_by_actions)

        self.sobject_items_sorting_button = StyledToolButton(small=True, shadow_enabled=True, square_type=True)
        self.sobject_items_sorting_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.sobject_items_sorting_button.setIcon(gf.get_icon('sort-alphabetical', icons_set='mdi', scale_factor=1))
        self.sobject_items_sorting_button.setToolTip('SObject Items Sorting')

        self.sort_so_by_name_action = QtGui.QAction('Sort by Name', self.sobject_items_sorting_button, checkable=True)
        self.sort_so_by_name_action.setIcon(gf.get_icon('sort-alphabetical', icons_set='mdi', scale_factor=1))
        self.sort_so_by_name_action.triggered.connect(lambda: self.change_items_sorting('sobject', 'name'))
        self.sort_so_by_name_action.setChecked(True)

        self.sobject_items_sorting_button.addAction(self.sort_so_by_name_action)

        self.snapshot_items_sorting_button = StyledToolButton(small=True, shadow_enabled=True, square_type=True)
        self.snapshot_items_sorting_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.snapshot_items_sorting_button.setIcon(gf.get_icon('sort-alphabetical', icons_set='mdi', scale_factor=1))
        self.snapshot_items_sorting_button.setToolTip('Snapshot Items Sorting')

        self.sort_sn_by_name_action = QtGui.QAction('Sort by Name', self.snapshot_items_sorting_button, checkable=True)
        self.sort_sn_by_name_action.setIcon(gf.get_icon('sort-alphabetical', icons_set='mdi', scale_factor=1))
        self.sort_sn_by_name_action.triggered.connect(lambda: self.change_items_sorting('snapshot', 'name'))
        self.sort_sn_by_name_action.setChecked(True)

        self.snapshot_items_sorting_button.addAction(self.sort_sn_by_name_action)

        self.change_view_tab_button = StyledToolButton(small=True, shadow_enabled=True, square_type=True)
        self.change_view_tab_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.change_view_tab_button.setIcon(gf.get_icon('view-list', icons_set='mdi', scale_factor=1))
        self.change_view_tab_button.setToolTip('Change Search Results View Style')

        # self.items_view_action = QtGui.QMenu('Items View', self.change_view_tab_button)
        # self.items_view_action.setIcon(gf.get_icon('view-list', icons_set='mdi', scale_factor=1))
        # self.items_view_action.triggered.connect(self.clear_tabs_history)

        self.split_view_horizontal_action = QtGui.QAction('Splitted Horizontal View', self.change_view_tab_button, checkable=True)
        self.split_view_horizontal_action.setIcon(gf.get_icon('view-sequential', icons_set='mdi', scale_factor=1))
        self.split_view_horizontal_action.triggered.connect(lambda: self.toggle_current_view('splitted_horizontal'))

        self.split_view_vertical_action = QtGui.QAction('Splitted Vertical View', self.change_view_tab_button, checkable=True)
        self.split_view_vertical_action.setIcon(gf.get_icon('view-parallel', icons_set='mdi', scale_factor=1))
        self.split_view_vertical_action.triggered.connect(lambda: self.toggle_current_view('splitted_vertical'))
        self.split_view_vertical_action.setChecked(True)

        self.continious_view_action = QtGui.QAction('Continious View', self.change_view_tab_button, checkable=True)
        self.continious_view_action.setIcon(gf.get_icon('view-dashboard-variant', icons_set='mdi', scale_factor=1))
        self.continious_view_action.triggered.connect(lambda: self.toggle_current_view('continious'))

        # self.items_view_action.addAction(self.split_view_horizontal_action)
        # self.items_view_action.addAction(self.split_view_vertical_action)
        # self.items_view_action.addAction(self.continious_view_action)
        # print self.get_current_results_widget()

        self.tiles_view_action = QtGui.QAction('Tiles View', self.change_view_tab_button, checkable=True)
        self.tiles_view_action.setIcon(gf.get_icon('view-grid', icons_set='mdi', scale_factor=1))
        self.tiles_view_action.triggered.connect(lambda: self.toggle_current_view('tiles'))

        # self.change_view_tab_button.addAction(self.items_view_action.menuAction())
        self.change_view_actions_group = QtGui.QActionGroup(self)
        self.change_view_actions_group.addAction(self.split_view_horizontal_action)
        self.change_view_actions_group.addAction(self.split_view_vertical_action)
        self.change_view_actions_group.addAction(self.continious_view_action)
        self.change_view_actions_group.addAction(self.tiles_view_action)

        self.change_view_tab_button.addAction(self.split_view_horizontal_action)
        self.change_view_tab_button.addAction(self.split_view_vertical_action)
        self.change_view_tab_button.addAction(self.continious_view_action)
        self.change_view_tab_button.addAction(self.tiles_view_action)

        self.additional_collapsable_toolbar = Ui_horizontalCollapsableWidget()
        self.additional_buttons_layout = QtGui.QHBoxLayout()
        self.additional_buttons_layout.setSpacing(0)
        self.additional_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.additional_collapsable_toolbar.setLayout(self.additional_buttons_layout)
        self.additional_collapsable_toolbar.setCollapsed(True)

        self.additional_buttons_layout.addWidget(self.sobject_items_sorting_button)
        self.additional_buttons_layout.addWidget(self.snapshot_items_sorting_button)
        self.additional_buttons_layout.addWidget(self.change_view_tab_button)
        self.additional_buttons_layout.addWidget(self.group_by_button)

        self.main_collapsable_toolbar = Ui_horizontalCollapsableWidget()
        self.main_buttons_layout = QtGui.QHBoxLayout()
        self.main_buttons_layout.setSpacing(0)
        self.main_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.main_collapsable_toolbar.setLayout(self.main_buttons_layout)
        self.main_collapsable_toolbar.setCollapsed(False)

        self.main_buttons_layout.addWidget(self.refresh_tab_button)
        self.main_buttons_layout.addWidget(self.history_tab_button)

        self.right_buttons_layout.addWidget(self.additional_collapsable_toolbar)
        self.right_buttons_layout.addWidget(self.main_collapsable_toolbar)

        self.results_tab_widget.setCornerWidget(self.right_buttons_widget, QtCore.Qt.TopRightCorner)
        self.results_tab_widget.setCornerWidget(self.left_buttons_widget, QtCore.Qt.TopLeftCorner)

    def do_my_tasks_action(self):
        stype_widget = env_inst.get_check_tree(tab_code='checkin_out', wdg_code=self.stype.get_code())

        print stype_widget

        checkin_out_control = env_inst.get_control_tab(tab_code='checkin_out')

        checkin_out_control.toggle_stype_tab(tab=stype_widget, hide=False)
        checkin_out_control.raise_stype_tab(tab=stype_widget)

        # search_widget = stype_widget.get_search_widget()
        advanced_search_widget = stype_widget.get_advanced_search_widget()

        # sthpw_project = env_inst.get_project_by_code('sthpw')
        # print sthpw_project
        # print sthpw_project.get_stypes()
        # print sthpw_project.stypes.get('sthpw/task')

        # task_stype = sthpw_project.stypes.get('sthpw/task')
        # env_inst.get_current_login()

        related_filter = ('_expression', 'in', "@SOBJECT(sthpw/task['assigned', '$LOGIN'])")

        advanced_search_widget.add_predefined_filter(related_filter)

        # tab_title = '{0} related to {1}'.format(self.stype.get_pretty_name(), self.sobject.get_title())
        # search_widget.add_tab(
        #     search_title=tab_title,
        #     filters=[related_filter],
        # )
        stype_widget.refresh_current_results()

    def change_items_sorting(self, items_type='sobject', sort='name'):
        print('MAKING SORT BY ', items_type, sort)

    def toggle_current_view(self, view='splitted_vertical'):

        current_results_widget = self.get_current_results_widget()
        current_results_widget.set_results_view(view)

    def toggle_goups_by(self, action):

        for group_action in self.group_by_actions:
            group_action.setChecked(False)
            group_action.setIcon(gf.get_icon('checkbox-blank-circle-outline', icons_set='mdi', scale_factor=1))

        action.setChecked(True)
        action.setIcon(gf.get_icon('check-circle', icons_set='mdi', scale_factor=1))

        self.set_group_by_column(action.data())

    def set_group_by_column(self, column):

        print 'Setting group by: ', column
        self.group_by_columns = [column]
        # if column not in self.group_by_columns:
        #     self.group_by_columns.append(column)

        self.add_tab('test_groups', [('name', 'EQI', 'fgsfds')])

    @gf.catch_error
    def add_tab(self, search_title='', filters=[], state=None, offset=0, limit=None, reverting=False, items_count=0, search_line_text='', current_index=0, view='splitted_vertical'):

        if not limit:
            limit = self.get_display_limit()

        # ONLY FOR ANIMATORS!
        from thlib.environment import SPECIALIZED

        if SPECIALIZED == 'animators':
            filters = [DEFAULT_FILTER, EXPR_FILTER]

        info = {
            'title': search_title,
            'filters': filters,
            'state': state,
            'offset': offset,
            'limit': limit,
            'items_count': items_count,
            'search_line_text': search_line_text,
            'current_index': current_index,
            'group_by': self.group_by_columns,
            'sort_by': self.sort_by,
            'view': view
        }

        search_results_widget = Ui_searchResultsWidget(
            project=self.project,
            stype=self.stype,
            info=info,
            parent=self.results_tab_widget
        )
        tab_label = gf.create_tab_label(search_title)
        tab_label.setParent(self)
        self.results_tab_widget.add_tab(search_results_widget, tab_label)

        if not reverting:
            self.results_tab_widget.setCurrentWidget(search_results_widget)

    def set_current_tab_title(self, title):
        current_results_widget = self.get_current_results_widget()
        current_results_widget.set_tab_title(title)

    def get_current_tab_title(self):
        current_results_widget = self.get_current_results_widget()
        return current_results_widget.get_tab_title()

    def get_display_limit(self):
        display_limit = gf.get_value_from_config(cfg_controls.get_checkin(), 'displayLimitSpinBox')
        if not display_limit:
            display_limit = 10
        return display_limit

    def get_results_tab_widget(self):
        return self.results_tab_widget

    def add_to_history_list(self, tab_title, widget):
        if tab_title:
            filter_process = QtGui.QAction(tab_title, self.history_tab_button)
            filter_process.triggered.connect(lambda: self.restore_tab_from_history(filter_process, widget))
            filter_process.setData(widget)

            try:
                if self.clear_history:
                    pass
            except:
                self.clear_history = QtGui.QAction('Clear History', self.history_tab_button)
                self.clear_history.triggered.connect(self.clear_tabs_history)
                self.history_tab_button.addAction(self.clear_history)
                self.sep = QtGui.QAction('', self.history_tab_button)
                self.sep.setSeparator(True)
                self.history_tab_button.addAction(self.sep)

            self.history_tab_button.addAction(filter_process)

    def clear_tabs_history(self):
        for action in self.history_tab_button.actions():
            results_wdg = action.data()
            if results_wdg:
                results_wdg.clear_tree_widgets()
                results_wdg.close()
                results_wdg.deleteLater()
            self.history_tab_button.removeAction(action)

        del self.clear_history

    def restore_tab_from_history(self, action, widget):

        self.results_tab_widget.addTab(widget, action.text())
        self.results_tab_widget.setCurrentWidget(widget)
        self.history_tab_button.removeAction(action)

    @gf.catch_error
    def close_tab(self, tab_index):
        if self.results_tab_widget.count() > 1:
            self.add_to_history_list(self.results_tab_widget.tabText(tab_index), self.results_tab_widget.widget(tab_index))
            self.results_tab_widget.removeTab(tab_index)

    def current_tab_changed(self, idx):

        search_results_widget = self.results_tab_widget.widget(idx)

        checkin_out_widget = self.get_current_checkin_out_widget()
        adv_search_widget = checkin_out_widget.get_advanced_search_widget()
        adv_search_widget.clear_all_filters()

        filters = search_results_widget.get_filters()
        if filters:
            adv_search_widget.set_filters(filters)
        else:
            adv_search_widget.add_default_filter(DEFAULT_FILTER)

        search_line_text = search_results_widget.get_search_line_text()
        if search_line_text is not None:
            self.search_line_edit.setText(search_line_text, block_event=True)

        title = search_results_widget.get_tab_title()
        if title is not None:
            checkin_out_widget = self.get_current_checkin_out_widget()
            adv_search_widget = checkin_out_widget.get_advanced_search_widget()
            tab_search_options_widget = adv_search_widget.get_tab_search_options_widget()
            tab_search_options_widget.set_edit_tab_title(title)

    def get_current_checkin_out_widget(self):
        return env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

    def get_current_results_widget(self):
        return self.results_tab_widget.currentWidget()

    def search_line_edit_text_edited(self, edited_text):

        checkin_out_widget = self.get_current_checkin_out_widget()
        adv_search_widget = checkin_out_widget.get_advanced_search_widget()
        tab_search_options_widget = adv_search_widget.get_tab_search_options_widget()
        tab_search_options_widget.set_edit_tab_title(edited_text)

        current_results_widget = self.get_current_results_widget()
        if current_results_widget:
            current_results_widget.set_search_line_text(edited_text)

    @gf.catch_error
    def do_search(self, search_kwargs=None):

        search_query = self.search_line_edit.text()
        filters = self.search_line_edit.get_search_filters()

        checkin_out_widget = self.get_current_checkin_out_widget()
        adv_search_widget = checkin_out_widget.get_advanced_search_widget()

        if search_query.startswith('skey://'):
            self.go_by_skey(search_query)
        elif search_kwargs:

            s_col = self.search_line_edit.get_suggest_column()

            explicit_filters = ['begin', (s_col, '=', search_kwargs.get(s_col))]
            for column, value in search_kwargs.items():
                filter = (column, '=', value)
                if filter not in explicit_filters:
                    explicit_filters.append(filter)
            explicit_filters.append('and')

            adv_search_widget.set_filters(explicit_filters)
            self.set_current_tab_title(search_kwargs.get(s_col))
            self.update_current_search_results(True)

        elif search_query is not None:

            adv_search_widget.set_filters(filters)

            self.set_current_tab_title(search_query)
            self.update_current_search_results(True)

    @gf.catch_error
    def update_current_search_results(self, reset_offset=False):
        results_widget = self.get_current_results_widget()

        # collecting current advanced search options
        results_widget.update_filters(True)
        if reset_offset:
            results_widget.update_search_results(refresh=True, offset=0)
        else:
            results_widget.update_search_results(refresh=True, offset=results_widget.collect_offset())

    def go_by_skey(self, skey_in=None):

        skey, sobject = tc.parce_skey(skey_in)

        print(skey)

        common_pipeline_codes = ['snapshot', 'task']

        if skey:
            if skey.get('pipeline_code') and skey.get('project'):
                if skey.get('project') == env_inst.get_current_project():
                    if skey['pipeline_code'] not in common_pipeline_codes:
                        pipeline_code = u'{namespace}/{pipeline_code}'.format(**skey)

                        parent_stype = self.project.stypes.get(pipeline_code)

                        stype_widget = env_inst.get_check_tree(tab_code='checkin_out', wdg_code=parent_stype.get_code())

                        checkin_out_control = env_inst.get_control_tab(tab_code='checkin_out')

                        checkin_out_control.toggle_stype_tab(tab=stype_widget, hide=False)
                        checkin_out_control.raise_stype_tab(tab=stype_widget)

                        search_widget = stype_widget.get_search_widget()

                        search_filter = ('code', '=', skey.get('code'))

                        search_widget.add_tab(search_title=sobject.get_title(), filters=[search_filter])

                else:
                    self.wrong_project_message(skey)

    def wrong_project_message(self, skey):
        msb = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                'Item {code}, not belongs to current project!'.format(**skey),
                                '<p>Current project is <b>{0}</b>, switch to <b>{project}</b> related to this item?</p>'.format(
                                    env_inst.get_current_project(), **skey) + '<p>This will restart TACTIC Handler!</p>',
                                QtGui.QMessageBox.NoButton, env_inst.ui_main)
        msb.addButton("Switch to Project", QtGui.QMessageBox.YesRole)
        msb.addButton("Cancel", QtGui.QMessageBox.NoRole)
        msb.exec_()

        reply = msb.buttonRole(msb.clickedButton())

        if reply == QtGui.QMessageBox.YesRole:
            env_server.set_project(skey['project'])
            skey_link = self.skeyLineEdit.text()
            self.close()
            self.create_ui_main()
            self.show()
            self.skeyLineEdit.setText(skey_link)
            self.go_by_skey()

    def create_gear_menu_popup(self):
        self.gearMenuToolButton.setIcon(gf.get_icon('settings', icons_set='mdi'))

    def add_action_to_gear_menu(self, action):
        self.gearMenuToolButton.addAction(action)

    def create_collapsable_toolbar(self):
        self.collapsable_toolbar = Ui_horizontalCollapsableWidget()
        self.collapsable_toolbar.setCollapsed(False)

        self.buttons_layout = QtGui.QHBoxLayout()
        self.buttons_layout.setSpacing(0)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.collapsable_toolbar.setLayout(self.buttons_layout)
        self.collapsable_toolbar.setCollapsed(True)

        self.expandingLayout.addWidget(self.collapsable_toolbar)

    def add_widget_to_collapsable_toolbar(self, widget):
        self.buttons_layout.addWidget(widget)

    def set_search_cache(self, search_cache, current_index=0):
        search_cache = gf.hex_to_html(search_cache)

        # work around for preventing tab widgets showing when tab adding
        self.results_tab_widget.setHidden(True)

        if search_cache:
            search_cache = gf.from_json(search_cache, use_ast=True)

            tab_added = 0
            for cache in search_cache:
                tab_added += 1
                self.add_tab(
                    search_title=cache['title'],
                    filters=cache['filters'],
                    state=cache['state'],
                    offset=cache['offset'],
                    limit=cache['limit'],
                    items_count=cache['items_count'],
                    search_line_text=cache['search_line_text'],
                    current_index=cache['current_index'],
                    reverting=True
                )

            if not tab_added:
                self.add_tab()

            if current_index:
                self.results_tab_widget.setCurrentIndex(current_index)
        else:
            self.add_tab()

        self.results_tab_widget.setHidden(False)

    def get_search_cache(self):

        tab_info_list = []

        for tab in range(self.results_tab_widget.count()):
            results_form_widget = self.results_tab_widget.widget(tab)

            tab_info_list.append(results_form_widget.get_info_dict())

        return gf.html_to_hex(gf.to_json(tab_info_list, use_ast=True))

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'collapsable_toolbar': True,
                'search_cache': None,
                'results_tab_widget_current_index': 0,
            }

        self.collapsable_toolbar.setCollapsed(settings_dict['collapsable_toolbar'])
        self.set_search_cache(settings_dict.get('search_cache'), settings_dict.get('results_tab_widget_current_index'))

    def get_settings_dict(self):

        settings_dict = {
            'collapsable_toolbar': int(self.collapsable_toolbar.isCollapsed()),
            'search_cache': self.get_search_cache(),
            'results_tab_widget_current_index': self.results_tab_widget.currentIndex(),
        }

        return settings_dict

    def showEvent(self, event):
        self.search_line_edit.setFocus()

        event.accept()

    def closeEvent(self, event):

        event.accept()
        self.search_results_widget.close()


class Ui_filterWidget(QtGui.QWidget):
    def __init__(self, stype, project, filter, default, op='begin', parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project

        self.default = default
        self.filter = filter
        self.op = op

        self.create_ui()

    def create_ui(self):

        self.setMaximumHeight(44)
        self.setMinimumHeight(44)

        self.create_main_layout()

        self.create_enabled_check_box()
        self.create_column_combo_box()
        self.create_match_by_combo_box()
        self.create_op_combo_box()
        self.create_query_line_edit()
        self.create_link_button()
        self.create_remove_self_tool_button()
        self.create_add_filter_tool_button()

        self.fill_column_combo_box()
        self.fill_match_by_combo_box()
        self.fill_op_combo_box()

        self.init_filter()

        self.controls_actions()

    def controls_actions(self):
        self.remove_self_tool_button.clicked.connect(self.close_self)
        self.add_filter_tool_button.clicked.connect(self.add_filter_widget)
        self.enabled_check_box.stateChanged.connect(self.change_enable_state)

        self.column_combo_box.currentIndexChanged.connect(self.changed_column_combo_box_index)
        self.match_combo_box.currentIndexChanged.connect(self.changed_match_by_combo_box_index)
        self.op_combo_box.currentIndexChanged.connect(self.changed_op_combo_box_index)
        self.query_line_edit.textChanged.connect(self.changed_line_edit_text)
        self.query_line_edit.returnPressed.connect(self.edited_line_edit_text)

    def get_checkin_out_widget(self):
        return env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

    def get_search_widget(self):
        checkin_out_widget = self.get_checkin_out_widget()
        return checkin_out_widget.get_search_widget()

    def get_advanced_search_widget(self):
        checkin_out_widget = self.get_checkin_out_widget()
        return checkin_out_widget.get_advanced_search_widget()

    def create_main_layout(self):
        self.main_layout = QtGui.QHBoxLayout()
        self.main_layout.setSpacing(9)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def create_enabled_check_box(self):
        self.enabled_check_box = QtGui.QCheckBox()
        self.main_layout.addWidget(self.enabled_check_box)
        self.enabled_check_box.setChecked(True)

    def create_column_combo_box(self):
        self.column_combo_box = StyledComboBox()
        self.main_layout.addWidget(self.column_combo_box)

    def fill_column_combo_box(self):
        last_item_index = 0
        for i, (column, values) in enumerate(self.stype.get_columns_info().items()):
            self.column_combo_box.addItem(gf.prettify_text(column))
            self.column_combo_box.setItemData(i, column, QtCore.Qt.UserRole)
            last_item_index = i+1

        self.column_combo_box.addItem('**Expression')
        self.column_combo_box.setItemData(last_item_index, '_expression', QtCore.Qt.UserRole)

    def changed_column_combo_box_index(self, idx):
        column = self.column_combo_box.itemData(idx, QtCore.Qt.UserRole)

        self.filter = (column, self.filter[1], self.filter[2])

        self.query_line_edit.set_suggest_column(column)

        self.fill_match_by_combo_box(column)
        self.changed_match_by_combo_box_index(0)

    def create_match_by_combo_box(self):
        self.match_combo_box = StyledComboBox()
        self.main_layout.addWidget(self.match_combo_box)

    def fill_match_by_combo_box(self, column=None):
        self.match_combo_box.clear()

        if not column:
            if self.filter:
                column = self.filter[0]
            else:
                column = self.column_combo_box.itemData(self.column_combo_box.currentIndex(), QtCore.Qt.UserRole)

        column_type = self.stype.get_column_data_type(column)

        match_list = get_match_list_by_type(column_type)

        for i, match in enumerate(match_list):
            self.match_combo_box.addItem(match[0])
            self.match_combo_box.setItemData(i, match[1], QtCore.Qt.UserRole)

    def changed_match_by_combo_box_index(self, idx):
        match = self.match_combo_box.itemData(idx, QtCore.Qt.UserRole)
        self.filter = (self.filter[0], match, self.filter[2])

    def changed_op_combo_box_index(self, idx):
        self.op = self.op_combo_box.currentText()

    def valid_filter(self):
        query_tex = self.query_line_edit.text()
        if query_tex.strip() and self.enabled_check_box.isChecked():
            return True

    def create_query_line_edit(self):
        self.query_line_edit = SuggestedLineEdit(self.stype, self.project, parent=self.parent().parent())
        self.query_line_edit.set_autofill_selected_items(True)
        self.main_layout.addWidget(self.query_line_edit)

    def changed_line_edit_text(self):
        text = self.query_line_edit.text()
        self.filter = (self.filter[0], self.filter[1], text)

    def edited_line_edit_text(self):
        search_widget = self.get_search_widget()
        search_widget.update_current_search_results()

    def create_link_button(self):

        # This link button is supposed to be a link to main search (will make first filter behave as main search line)

        self.link_button = StyledToolButton(small=True, square_type=True)
        self.main_layout.addWidget(self.link_button)
        self.link_button.setAutoRaise(True)
        self.link_button.setIcon(gf.get_icon('link', icons_set='mdi', scale_factor=1.1))
        self.link_button.setVisible(False)
        self.link_button.setCheckable(True)
        self.link_button.setChecked(False)
        if self.default:
            self.link_button.setVisible(True)

    def create_op_combo_box(self):
        self.op_combo_box = StyledComboBox()
        self.main_layout.addWidget(self.op_combo_box)
        if self.default:
            self.op_combo_box.setVisible(False)

    def fill_op_combo_box(self):
        self.op_combo_box.clear()
        self.op_combo_box.addItems(['and', 'or'])
        if self.op:
            self.set_op(self.op)

    def get_op(self):
        if self.op != 'begin':
            return self.op_combo_box.currentText()
        else:
            return self.op

    def set_op(self, op):
        self.op = op
        if self.op == 'or':
            self.op_combo_box.setCurrentIndex(1)
        else:
            self.op_combo_box.setCurrentIndex(0)

    def create_remove_self_tool_button(self):
        self.remove_self_tool_button = StyledToolButton(small=True)
        self.remove_self_tool_button.setAutoRaise(True)
        self.main_layout.addWidget(self.remove_self_tool_button)
        self.remove_self_tool_button.setIcon(gf.get_icon('close', icons_set='mdi', scale_factor=1.1))
        if self.default:
            self.remove_self_tool_button.setHidden(True)

    def create_add_filter_tool_button(self):
        self.add_filter_tool_button = StyledToolButton(small=True)
        self.add_filter_tool_button.setAutoRaise(True)
        self.main_layout.addWidget(self.add_filter_tool_button)
        self.add_filter_tool_button.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1.2))
        if not self.default:
            self.add_filter_tool_button.setHidden(True)

    def get_filter(self):
        return self.filter

    def set_filter(self, fltr):
        self.filter = fltr

    def init_filter(self):

        if self.filter:
            self.set_column_combo_box_value(self.filter[0])
            self.set_match_combo_box_value(self.filter[1])
            self.set_query_line_edit_value(self.filter[2])
        else:
            self.filter = (
                self.column_combo_box.itemData(0, QtCore.Qt.UserRole),
                self.match_combo_box.itemData(0, QtCore.Qt.UserRole),
                ''
            )

    def set_column_combo_box_value(self, column_code):
        index = self.column_combo_box.findData(column_code, QtCore.Qt.UserRole)
        if index == -1:
            index = 0
        self.column_combo_box.setCurrentIndex(index)

        self.query_line_edit.set_suggest_column(column_code)

    def set_match_combo_box_value(self, match):
        index = self.match_combo_box.findData(match, QtCore.Qt.UserRole)
        self.match_combo_box.setCurrentIndex(index)

    def set_query_line_edit_value(self, query_text):
        self.query_line_edit.setText(query_text)

    def change_enable_state(self, state):
        if bool(state):
            self.column_combo_box.setEnabled(True)
            self.match_combo_box.setEnabled(True)
            self.query_line_edit.setReadOnly(False)
        else:
            self.column_combo_box.setEnabled(False)
            self.match_combo_box.setEnabled(False)
            self.query_line_edit.setReadOnly(True)

    def add_filter_widget(self):
        adv_search_widget = self.get_advanced_search_widget()
        adv_search_widget.add_empty_filter()

    def close_self(self):
        adv_search_widget = self.get_advanced_search_widget()
        adv_search_widget.remove_filter(self)

    def closeEvent(self, event):
        event.accept()
        self.deleteLater()


class Ui_searchOptionsWidget(QtGui.QWidget):
    def __init__(self, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = self.stype.get_project()

        self.create_ui()

        self.controls_actions()

    def create_ui(self):
        # self.setMaximumHeight(46)
        # self.setMinimumHeight(46)

        self.create_main_layout()

        self.create_tab_name_editor()
        self.create_presets_combo_box()

    def controls_actions(self):
        self.tab_name_edit.textEdited.connect(self.tab_name_edit_text_edited)
        self.tab_name_edit.returnPressed.connect(self.tab_name_edit_text_edited)

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout()
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.main_layout.setSpacing(6)
        self.setLayout(self.main_layout)

    def create_tab_name_editor(self):
        self.tab_name_layout = QtGui.QGridLayout()

        self.tab_name_label = QtGui.QLabel('Search Tab Name: ')

        self.tab_name_edit = QtGui.QLineEdit()

        self.tab_name_layout.addWidget(self.tab_name_label, 0, 0, 1, 1)
        self.tab_name_layout.addWidget(self.tab_name_edit, 0, 1, 1, 1)

        self.tab_name_layout.setColumnStretch(1, 0)

        self.main_layout.addLayout(self.tab_name_layout, 0, 0)

    def create_presets_combo_box(self):
        self.presets_layout = QtGui.QGridLayout()

        self.presets_combo_box = QtGui.QComboBox()

        self.add_new_preset_button = QtGui.QToolButton()
        self.add_new_preset_button.setAutoRaise(True)
        self.add_new_preset_button.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1.2))
        # self.add_new_preset_button.clicked.connect(self.add_new_preset)
        self.add_new_preset_button.setToolTip('Create new Preset and Save (from current state)')
        # self.add_new_preset_button.setHidden(True)

        self.save_new_preset_button = QtGui.QToolButton()
        self.save_new_preset_button.setAutoRaise(True)
        self.save_new_preset_button.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        # self.save_new_preset_button.clicked.connect(self.save_preset_to_server)
        self.save_new_preset_button.setToolTip('Save Current Preset Changes')
        # self.save_new_preset_button.setHidden(True)

        self.remove_preset_button = QtGui.QToolButton()
        self.remove_preset_button.setAutoRaise(True)
        self.remove_preset_button.setIcon(gf.get_icon('delete', icons_set='mdi', scale_factor=1))
        self.remove_preset_button.clicked.connect(self.close)
        self.remove_preset_button.setToolTip('Remove Current Preset')
        # self.remove_preset_button.setHidden(True)

        self.presets_layout.addWidget(self.remove_preset_button, 0, 0, 1, 1)
        self.presets_layout.addWidget(self.presets_combo_box, 0, 1, 1, 1)
        self.presets_layout.addWidget(self.save_new_preset_button, 0, 2, 1, 1)
        self.presets_layout.addWidget(self.add_new_preset_button, 0, 3, 1, 1)

        self.presets_layout.setColumnStretch(1, 0)

        self.main_layout.addLayout(self.presets_layout, 1, 0)

    def get_current_checkin_out_widget(self):
        return env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

    def get_search_widget(self):
        checkin_out_widget = self.get_current_checkin_out_widget()
        return checkin_out_widget.get_search_widget()

    def get_advanced_search_widget(self):
        checkin_out_widget = self.get_current_checkin_out_widget()
        return checkin_out_widget.get_advanced_search_widget()

    def set_edit_tab_title(self, text):
        self.tab_name_edit.setText(text)

    def tab_name_edit_text_edited(self, text=None):
        checkin_out_widget = self.get_current_checkin_out_widget()
        search_widget = checkin_out_widget.get_search_widget()
        search_widget.set_current_tab_title(self.get_edit_tab_title())

    def get_edit_tab_title(self):
        return self.tab_name_edit.text()


class Ui_advancedSearchWidget(QtGui.QWidget):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project

        self.default_filter_widget = None
        self.filter_widgets = []

        self.create_ui()

    def create_ui(self):
        self.create_main_layout()
        self.create_filters_scroll_area()
        self.create_search_filters_widget()
        self.create_search_presets_widget()

        self.controls_actions()

    def controls_actions(self):
        self.clear_button.clicked.connect(self.clear_filters_button_action)
        self.do_search_button.clicked.connect(self.do_search_button_action)

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def create_filters_scroll_area(self):
        self.filters_scroll_area = QtGui.QScrollArea()
        self.filters_scroll_area_contents = QtGui.QWidget()
        self.filters_scroll_area.setStyleSheet('QScrollArea > #qt_scrollarea_viewport > QWidget {background-color: rgba(128, 128, 128, 48);}')
        self.filters_scroll_area.setFrameShape(QtGui.QScrollArea.NoFrame)

        self.filters_scroll_area.setWidgetResizable(True)
        self.filters_scroll_area.setWidget(self.filters_scroll_area_contents)

        self.filters_scroll_widgets_layout = QtGui.QVBoxLayout()
        self.filters_scroll_widgets_layout.setSpacing(4)
        self.filters_scroll_widgets_layout.setContentsMargins(2, 2, 2, 2)
        self.filters_scroll_widgets_layout.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)
        self.filters_scroll_area_contents.setLayout(self.filters_scroll_widgets_layout)

    def create_search_filters_widget(self):

        self.filters_collapsable = Ui_collapsableWidget(state=False)
        self.filters_collapsable.setLayout(QtGui.QVBoxLayout())
        self.filters_collapsable.setText('Search Filters:')
        self.filters_collapsable.setCollapsedText('Search Filters:')
        self.filters_collapsable.add_widget(self.filters_scroll_area)

        self.main_layout.addWidget(self.filters_collapsable)
        # self.filters_collapsable.collapsed.connect(self.fit_to_contets)

        self.do_search_button = QtGui.QToolButton()
        self.do_search_button.setAutoRaise(True)
        self.do_search_button.setIcon(gf.get_icon('refresh', icons_set='mdi', scale_factor=1))

        self.clear_button = QtGui.QToolButton()
        self.clear_button.setAutoRaise(True)
        self.clear_button.setIcon(gf.get_icon('delete', icons_set='mdi', scale_factor=1))

        self.filters_collapsable.add_overlay_widget(self.do_search_button)
        self.filters_collapsable.add_overlay_widget(self.clear_button)

    def create_search_presets_widget(self):

        self.search_options_collapsable = Ui_collapsableWidget(state=False)
        self.search_options_collapsable.setLayout(QtGui.QVBoxLayout())
        self.search_options_collapsable.setText('Search Options:')
        self.search_options_collapsable.setCollapsedText('Search Options:')
        self.main_layout.addWidget(self.search_options_collapsable)

        # self.search_options_collapsable.collapsed.connect(self.fit_to_contets)

        self.tab_search_options_widget = Ui_searchOptionsWidget(self.stype)
        self.search_options_collapsable.add_widget(self.tab_search_options_widget)

    def get_tab_search_options_widget(self):
        return self.tab_search_options_widget

    def update_default_filter(self, filter_text):
        self.default_filter_widget.set_filter(filter_text)
        self.default_filter_widget.init_filter()

    def add_default_filter(self, filter_text):
        # Default filter can not be removed and have + button

        filter_widget = Ui_filterWidget(
            project=self.project,
            stype=self.stype,
            parent=self,
            filter=filter_text,
            default=True
        )
        self.filters_scroll_area.setMaximumHeight(filter_widget.height()+4)
        self.filters_scroll_widgets_layout.addWidget(filter_widget)
        self.filter_widgets.append(filter_widget)
        self.default_filter_widget = filter_widget

        self.fit_to_contets()

    def add_predefined_filter(self, filter_text, op='and'):
        # Predefined filter can be removed, and have X button

        filter_widget = Ui_filterWidget(
            project=self.project,
            stype=self.stype,
            parent=self,
            filter=filter_text,
            default=False,
            op=op,
        )
        self.filters_scroll_area.setMaximumHeight(filter_widget.height() + 4)
        self.filters_scroll_widgets_layout.addWidget(filter_widget)
        self.filter_widgets.append(filter_widget)

        self.fit_to_contets()

    def add_empty_filter(self):
        # Empty filter created when + button pushed, it starts from first column of search type

        filter_widget = Ui_filterWidget(
            project=self.project,
            stype=self.stype,
            parent=self,
            filter=None,
            default=False
        )
        self.filters_scroll_area.setMaximumHeight(filter_widget.height() + 4)
        self.filters_scroll_widgets_layout.addWidget(filter_widget)
        self.filter_widgets.append(filter_widget)

        self.fit_to_contets()

    def remove_filter(self, filter_widget):
        filter_widget.close()
        self.filter_widgets.remove(filter_widget)

        self.fit_to_contets()

    def do_search_button_action(self):
        search_widget = self.get_search_widget()
        search_widget.update_current_search_results()

    def clear_filters_button_action(self):
        self.clear_all_filters()
        self.add_default_filter(DEFAULT_FILTER)

    def clear_all_filters(self):
        if self.default_filter_widget:
            self.default_filter_widget.close()
            self.default_filter_widget = None

        for filter_widget in self.filter_widgets:
            filter_widget.close()
        self.filter_widgets = []

    @staticmethod
    def append_filter(filter_widget, filter_list, cnt):
        if filter_widget.get_op() == 'begin':
            if cnt > 1:
                filter_list.append(filter_widget.get_op())
            filter_list.append(filter_widget.get_filter())
        else:
            filter_list.append(filter_widget.get_filter())
            if cnt > 1:
                filter_list.append(filter_widget.get_op())

    def get_filters(self, check_valid=False):
        filters = []
        for filter_widget in self.filter_widgets:
            if check_valid:
                if filter_widget.valid_filter():
                    self.append_filter(filter_widget, filters, len(self.filter_widgets))
            else:
                self.append_filter(filter_widget, filters, len(self.filter_widgets))
        return filters

    def get_default_filter(self):
        return self.default_filter_widget.get_filter()

    def set_filters(self, filters):
        if filters:
            self.clear_all_filters()

            default_op = 'and'

            if filters[0] != 'begin':
                # if filter did not have begin - add it
                filters.insert(0, 'begin')

            # setting and defining default operator at the end
            if filters[-1] not in ['and', 'or']:
                filters.append(default_op)
            else:
                default_op = filters[-1]

            ops_list = []
            filters_list = []
            op_added = False

            # Making two lists of OP and filters
            for fl in filters:
                # if we found op we add it to list, and mark op is added
                if isinstance(fl, (str, unicode)):
                    ops_list.append(fl)
                    op_added = True
                else:
                    # if there is no OP provided, we add default OP
                    if not op_added:
                        # searching for next closing op
                        next_op = default_op
                        idx = filters.index(fl)
                        for i in filters[idx:]:
                            if isinstance(i, (str, unicode)):
                                next_op = i
                                break
                        # adding next closing OP
                        ops_list.append(next_op)
                    filters_list.append(fl)
                    op_added = False

            if ops_list[0] == 'begin':
                filters_tuple = zip(ops_list[1:], filters_list)
            else:
                filters_tuple = zip(ops_list, filters_list)

            # Now we adding our ready filters with proper operators
            default_added = False
            for oper, fltr in filters_tuple:
                if default_added:
                    self.add_predefined_filter(fltr, oper)
                else:
                    self.add_default_filter(fltr)
                    default_added = True

    def fit_to_contets(self):
        total_height = self.filters_scroll_area.height()

        if len(self.filter_widgets) > 0:
            filter_widget_height = self.filter_widgets[0].height() + 4
            total_height = filter_widget_height * len(self.filter_widgets)

        if total_height < 280:
            self.filters_scroll_area.setMinimumHeight(total_height)
        self.filters_scroll_area.setMaximumHeight(total_height)

    def get_checkin_out_widget(self):
        return env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

    def get_search_widget(self):
        checkin_out_widget = self.get_checkin_out_widget()
        return checkin_out_widget.get_search_widget()

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'filters_collapsable_state': True,
                'search_options_collaspable_state': True,
                'visible': False
            }

        self.setVisible(settings_dict.get('visible'))
        if settings_dict.get('filters_collapsable_state'):
            self.filters_collapsable.setCollapseState(True)
        if settings_dict.get('search_options_collaspable_state'):
            self.search_options_collapsable.setCollapseState(True)

    def get_settings_dict(self):

        settings_dict = {
            'filters_collapsable_state': self.filters_collapsable.isCollapsed(),
            'search_options_collaspable_state': self.search_options_collapsable.isCollapsed(),
            'visible': self.isVisible()
        }

        return settings_dict


class Ui_navigationWidget(QtGui.QWidget):
    refresh_search = QtCore.Signal(object, object)

    def __init__(self, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.stype = stype

        self.display_limit = 0
        self.display_offset = 0
        self.total_count = 0
        self.total_query_count = 0
        self.current_page = 1
        self.last_page = 0

        self.create_ui()

    def create_ui(self):

        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.create_main_layout()

        self.create_button_controls()
        self.create_navigation_label()

        self.controls_actions()

    def set_initial_state(self):
        self.display_limit = 0
        self.display_offset = 0
        self.total_count = 0
        self.total_query_count = 0
        self.current_page = 1
        self.last_page = 0

    def controls_actions(self):

        self.back_button.enterEvent = self.back_button_enter_event
        self.back_button.leaveEvent = self.back_button_leave_event
        self.forward_button.enterEvent = self.forward_button_enter_event
        self.forward_button.leaveEvent = self.forward_button_leave_event

        self.navigation_label.linkActivated.connect(self.navigation_label_link_clicked)
        self.forward_button.clicked.connect(self.next_page)
        self.back_button.clicked.connect(self.prev_page)

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def back_button_enter_event(self, event):
        self.back_button_hover_animation.start()
        event.accept()

    def back_button_leave_event(self, event):
        self.back_button_leave_animation.setStartValue(self.back_button_opacity_effect.opacity())
        self.back_button_leave_animation.start()
        event.accept()

    def forward_button_enter_event(self, event):
        self.forward_button_hover_animation.start()
        event.accept()

    def forward_button_leave_event(self, event):
        self.forward_button_leave_animation.setStartValue(self.forward_button_opacity_effect.opacity())
        self.forward_button_leave_animation.start()
        event.accept()

    def create_navigation_label(self):
        self.navigation_label = QtGui.QLabel('')
        self.navigation_label.setTextFormat(QtCore.Qt.RichText)
        self.navigation_label.setAlignment(QtCore.Qt.AlignCenter)

        self.main_layout.addWidget(self.navigation_label, 0, 1, 1, 1)

    def create_button_controls(self):
        self.back_button = QtGui.QPushButton('')
        self.back_button_opacity_effect = QtGui.QGraphicsOpacityEffect()
        self.back_button_opacity_effect.setOpacity(0.2)
        self.back_button.setGraphicsEffect(self.back_button_opacity_effect)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.back_button.setSizePolicy(sizePolicy)
        self.back_button.setIcon(gf.get_icon('chevron-left'))

        self.back_button.setStyleSheet('QPushButton {background-color: transparent; border-style: none; outline: none; border-width: 0px;}')

        self.back_button_hover_animation = QtCore.QPropertyAnimation(self.back_button_opacity_effect, "opacity", self)
        self.back_button_hover_animation.setDuration(200)
        self.back_button_hover_animation.setEasingCurve(QtCore.QEasingCurve.InSine)
        self.back_button_hover_animation.setStartValue(0.2)
        self.back_button_hover_animation.setEndValue(1)

        self.back_button_leave_animation = QtCore.QPropertyAnimation(self.back_button_opacity_effect, "opacity", self)
        self.back_button_leave_animation.setDuration(200)
        self.back_button_leave_animation.setEasingCurve(QtCore.QEasingCurve.OutSine)
        self.back_button_leave_animation.setEndValue(0.2)

        # forward button
        self.forward_button = QtGui.QPushButton('')
        self.forward_button_opacity_effect = QtGui.QGraphicsOpacityEffect(self)
        self.forward_button_opacity_effect.setOpacity(0.2)
        self.forward_button.setGraphicsEffect(self.forward_button_opacity_effect)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.forward_button.setSizePolicy(sizePolicy)
        self.forward_button.setIcon(gf.get_icon('chevron-right'))
        self.forward_button.setStyleSheet('QPushButton {background-color: transparent; border-style: none; outline: none; border-width: 0px;}')

        self.forward_button_hover_animation = QtCore.QPropertyAnimation(self.forward_button_opacity_effect, "opacity", self)
        self.forward_button_hover_animation.setDuration(200)
        self.forward_button_hover_animation.setEasingCurve(QtCore.QEasingCurve.InSine)
        self.forward_button_hover_animation.setStartValue(0.2)
        self.forward_button_hover_animation.setEndValue(1)

        self.forward_button_leave_animation = QtCore.QPropertyAnimation(self.forward_button_opacity_effect, "opacity", self)
        self.forward_button_leave_animation.setDuration(200)
        self.forward_button_leave_animation.setEasingCurve(QtCore.QEasingCurve.OutSine)
        self.forward_button_leave_animation.setEndValue(0.2)

        self.main_layout.addWidget(self.forward_button, 0, 2, 1, 1)
        self.main_layout.addWidget(self.back_button, 0, 0, 1, 1)

        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setColumnStretch(2, 1)

    def navigation_label_link_clicked(self, link):
        if link:
            page, offset = link.split(':')
            self.current_page = int(page)
            self.refresh_search.emit(self.display_limit, int(offset))

    def next_page(self):
        if self.current_page < self.last_page:
            self.current_page += 1
            self.display_offset = self.display_offset + self.display_limit
            self.refresh_search.emit(self.display_limit, self.display_offset)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_offset = self.display_offset - self.display_limit
            self.refresh_search.emit(self.display_limit, self.display_offset)

    def init_navigation(self, query_info):

        if query_info:
            self.set_initial_state()

            self.total_count = query_info['total_sobjects_count']
            self.total_query_count = query_info['total_sobjects_query_count']
            self.current_page = query_info.get('current_page')

            self.display_limit = query_info['limit']
            self.display_offset = query_info['offset']

            # Making shure we do not pass invisible pages
            if self.total_query_count < self.display_offset:
                self.display_offset = 0

            self.gen_pages_line(self.display_limit, self.total_query_count, widget_width=self.width())

            # Checking if we need nav bar
            if self.total_query_count <= 0 or self.total_query_count < self.display_limit:
                self.setHidden(True)
            else:
                self.setHidden(False)
        else:
            self.setHidden(True)

    def resizeEvent(self, event):
        self.gen_pages_line(self.display_limit, self.total_query_count, widget_width=self.width())
        super(self.__class__, self).resizeEvent(event)

    def get_offset(self):
        return self.display_offset

    def gen_pages_line(self, display_limit, total_count, widget_width=None):
        pages = []
        page_number = 1

        for i in range(total_count):
            if i % display_limit == 0:
                page_dict = {
                    'offset': i,
                    'page_number': page_number
                }
                pages.append(page_dict)
                page_number += 1
        if pages:

            self.total_pages_count = len(pages)

            # guessing how much pages to show in a row
            self.fit_pages_count = widget_width / 32
            if self.fit_pages_count > pages[-1]['page_number']:
                self.fit_pages_count = pages[-1]['page_number']

            # guessing page by offset
            for i in range(self.total_pages_count):
                if pages[i]['offset'] == self.display_offset:
                    self.current_page = pages[i]['page_number']

            final_page_line = ''
            start_page = 0

            if self.fit_pages_count >= self.total_pages_count:
                offset = self.fit_pages_count
            else:
                offset = self.fit_pages_count / 2

            if self.current_page:
                start_page = self.current_page - offset
                last_page = self.current_page + offset

                if last_page < self.fit_pages_count:
                    last_page = self.fit_pages_count

                if last_page > self.total_pages_count:
                    last_page = self.total_pages_count
                    start_page -= offset

                if start_page < 0:
                    start_page = 0

                page_ranges = range(start_page, last_page)
            else:
                page_ranges = range(self.last_page)

            for i in page_ranges:

                if i+1 == self.current_page:
                    page_line = '<b>{0}</b>'.format(i+1)
                else:
                    page_line = i+1

                final_page_line += '<a href="{1}:{2}" style="color:#bfbfbf">{0}</a> '.format(
                    page_line,
                    pages[i]['page_number'],
                    pages[i]['offset']
                )

            first_items = self.display_offset+1
            second_items = self.display_limit + self.display_offset
            if second_items > total_count:
                second_items = total_count

            # links for last page
            if pages[-1]['page_number'] > last_page:
                final_page_line = '{0} ... <a href="{1}:{2}" style="color:#bfbfbf">{1}</a>'.format(
                    final_page_line,
                    pages[-1]['page_number'],
                    pages[-1]['offset'])

            if start_page > 0:
                final_page_line = '<a href="{0}:{1}" style="color:#bfbfbf">{0}</a> .. {2}'.format(
                    pages[0]['page_number'],
                    pages[0]['offset'],
                    final_page_line)

            self.navigation_label.setText(
                '<span style=" color:#828282;">Showing {0} - {1} of {2}<br>{3}</span>'.format(
                    first_items,
                    second_items,
                    total_count,
                    final_page_line
                ))

            self.last_page = last_page


class Ui_searchResultsWidget(QtGui.QWidget):
    def __init__(self, project, stype, info, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.create_layout()
        self.create_items_view()
        self.create_tiles_view()

        self.create_overlay_layout()
        self.create_loading_overlay_widget()

        self.info = info
        self.stype = stype
        self.project = project
        self.created = False

        self.checkin_out_config = cfg_controls.get_checkin()

        self.bottom_navigataion_widget = None

        self.current_tree_widget_item = None
        self.current_results_tree_widget_item = None
        self.current_results_versions_tree_widget_item = None

    def create_layout(self):
        self.resultsLayout = QtGui.QVBoxLayout(self)
        self.resultsLayout.setSpacing(0)
        self.resultsLayout.setContentsMargins(0, 0, 0, 0)
        self.resultsLayout.setObjectName("resultsLayout")

    def create_tiles_view(self):
        self.results_tiles_view = Ui_assetsBrowserWidget(self)

        self.resultsLayout.addWidget(self.results_tiles_view)

        self.results_tiles_view.setHidden(True)

    def create_items_view(self):

        self.items_view_splitter = QtGui.QSplitter(self)
        self.items_view_splitter.setOrientation(QtCore.Qt.Horizontal)
        self.items_view_splitter.setObjectName("items_view_splitter")

        self.resultsTreeWidget = Ui_extendedTreeWidget(self.items_view_splitter)
        self.resultsTreeWidget.setRootIsDecorated(False)
        self.resultsTreeWidget.setIndentation(0)
        self.resultsTreeWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.resultsTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.resultsTreeWidget.setTabKeyNavigation(True)
        self.resultsTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.resultsTreeWidget.setAllColumnsShowFocus(True)
        self.resultsTreeWidget.setWordWrap(True)
        self.resultsTreeWidget.setHeaderHidden(True)
        self.resultsTreeWidget.setObjectName("resultsTreeWidget")

        self.resultsVersionsTreeWidget = Ui_extendedTreeWidget(self.items_view_splitter)
        self.resultsVersionsTreeWidget.setTabKeyNavigation(True)
        self.resultsVersionsTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.resultsVersionsTreeWidget.setRootIsDecorated(False)
        self.resultsVersionsTreeWidget.setAllColumnsShowFocus(True)
        self.resultsVersionsTreeWidget.setWordWrap(True)
        self.resultsVersionsTreeWidget.setHeaderHidden(True)
        self.resultsVersionsTreeWidget.setIndentation(0)
        self.resultsVersionsTreeWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.resultsVersionsTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.resultsVersionsTreeWidget.setObjectName("resultsVersionsTreeWidget")

        self.resultsLayout.addWidget(self.items_view_splitter)
        self.items_view_splitter.setHidden(True)

    def create_simple_view_ui(self):

        self.sep_versions = False
        self.resultsTreeWidget.setRootIsDecorated(False)

        self.create_progress_bar()
        self.create_bottom_navigation_widget()

        self.set_results_view('continious', False)

        self.customize_ui()

        self.initial_load_results()

        self.created = True

    def create_ui(self):

        # self.create_separate_versions_tree()

        self.sep_versions = gf.get_value_from_config(self.checkin_out_config, 'versionsSeparateCheckinCheckBox')
        if self.sep_versions:
            self.sep_versions = bool(int(self.sep_versions))

        self.create_progress_bar()
        self.create_bottom_navigation_widget()

        self.set_results_view(self.info.get('view'), False)

        self.customize_ui()

        self.initial_load_results()

        self.controls_actions()

        self.created = True

    def create_overlay_layout(self):

        self.overlay_layout_widget = QtGui.QWidget(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.overlay_layout_widget.setSizePolicy(sizePolicy)

        self.overlay_layout = QtGui.QVBoxLayout(self.overlay_layout_widget)
        self.overlay_layout.setSpacing(0)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)

        self.overlay_layout_widget.setLayout(self.overlay_layout)
        self.overlay_layout_widget.setHidden(True)

    def show_overlay(self):

        self.overlay_layout_widget.raise_()
        self.overlay_layout_widget.show()

        self.loading_anm_open.start()

    def hide_overlay(self):

        self.loading_anm_close.start()

    def hide_overlay_at_animation_end(self, val):
        if val == 0.0:
            self.overlay_layout_widget.lower()
            self.overlay_layout_widget.hide()

    def create_loading_overlay_widget(self):

        self.loading_widget = QtGui.QToolButton()

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.loading_widget.setSizePolicy(sizePolicy)

        self.loading_widget.setMinimumSize(64, 64)
        self.loading_widget.setIconSize(QtCore.QSize(64, 64))
        self.loading_widget.setStyleSheet("QToolButton { border: 0px; background-color: rgba(0, 0, 0, 96);}")
        self.loading_widget.setIcon(gf.get_icon('loading', icons_set='mdi', scale_factor=1, spin=[self.loading_widget, 30, 45]))

        effect = QtGui.QGraphicsOpacityEffect(self.loading_widget)

        self.loading_anm_close = QtCore.QPropertyAnimation(effect, 'opacity', self.loading_widget)
        self.loading_anm_close.setDuration(200)
        self.loading_anm_close.setStartValue(1)
        self.loading_anm_close.setEndValue(0)
        self.loading_anm_close.setEasingCurve(QtCore.QEasingCurve.OutSine)
        self.loading_anm_open = QtCore.QPropertyAnimation(effect, 'opacity', self.loading_widget)
        self.loading_anm_open.setDuration(200)
        self.loading_anm_open.setStartValue(0)
        self.loading_anm_open.setEndValue(1)
        self.loading_anm_open.setEasingCurve(QtCore.QEasingCurve.InSine)

        self.loading_anm_close.valueChanged.connect(self.hide_overlay_at_animation_end)

        self.loading_widget.setGraphicsEffect(effect)

        self.overlay_layout.addWidget(self.loading_widget)

    def update_default_filter(self, query_text):
        checkin_out_widget = self.get_current_checkin_out_widget()
        adv_search_widget = checkin_out_widget.get_advanced_search_widget()
        df = adv_search_widget.get_default_filter()
        adv_search_widget.update_default_filter((df[0], df[1], query_text))

    def initial_load_results(self, limit=None, offset=None):

        if limit is None:
            limit = self.get_limit()

        if offset is None:
            offset = self.get_offset()

        group_by = self.get_group_by()
        if group_by:
            print 'Filling groups by: ', group_by
            self.query_group_by_sobjects(
                search_type=self.stype.get_code(),
                project_code=self.project.get_code(),
                group_by=group_by,
            )
        else:
            order_bys = ['name']

            self.query_sobjects(
                filters=self.get_filters(),
                stype=self.stype.get_code(),
                project=self.project.get_code(),
                order_bys=order_bys,
                limit=limit,
                offset=offset,
            )

    def set_results_view(self, view='splitted_vertical', refresh=True):

        print 'toggling', view
        self.set_cuttent_view(view)

        if view == 'continious':
            self.results_tiles_view.setHidden(True)
            self.resultsVersionsTreeWidget.setHidden(True)
            self.items_view_splitter.setHidden(False)
            self.sep_versions = False
        elif view == 'splitted_horizontal':
            self.results_tiles_view.setHidden(True)
            self.items_view_splitter.setHidden(False)
            self.resultsVersionsTreeWidget.setHidden(False)
            self.items_view_splitter.setOrientation(QtCore.Qt.Vertical)
            self.sep_versions = True
        elif view == 'splitted_vertical':
            self.results_tiles_view.setHidden(True)
            self.items_view_splitter.setHidden(False)
            self.resultsVersionsTreeWidget.setHidden(False)
            self.items_view_splitter.setOrientation(QtCore.Qt.Horizontal)
            self.sep_versions = True
        elif view == 'tiles':
            self.items_view_splitter.setHidden(True)
            self.results_tiles_view.setHidden(False)

        if refresh:
            self.update_search_results(refresh=True)

    def search_query(self, search_query):
        if not self.info.get('simple_view'):
            self.update_default_filter(search_query)

        self.set_offset(0)

        if not self.info.get('simple_view'):
            self.update_filters(True)

        self.update_search_results()

    def update_search_results(self, limit=None, offset=None,  refresh=False):

        # collecting new filters, limit, offset, etc...
        # self.get_info_dict()

        if limit is None:
            limit = self.get_limit()

        if offset is None:
            offset = self.get_offset()

        if refresh:
            # marking this as refreshing
            self.info['refresh'] = True

            # collecting current tree widget state
            self.info['state'] = gf.tree_state(self.resultsTreeWidget, {})

        order_bys = ['name']

        # making query for current search with current search options
        self.query_sobjects(
            filters=self.get_filters(),
            stype=self.stype.get_code(),
            project=self.project.get_code(),
            order_bys=order_bys,
            limit=limit,
            offset=offset,
        )

    def get_info_dict(self):

        current_state = self.collect_state()
        if current_state:
            self.info['state'] = current_state

        self.info['title'] = self.get_tab_title()
        self.info['offset'] = self.collect_offset()
        self.info['limit'] = self.get_limit()
        self.info['filters'] = self.get_filters()

        self.info['items_count'] = self.get_items_count()
        self.info['search_line_text'] = self.get_search_line_text()
        self.info['current_index'] = self.get_current_index()

        self.info['view'] = self.get_cuttent_view()

        return self.info

    def get_state(self):
        return self.info['state']

    def set_state(self, state):
        self.info['state'] = state

    def collect_state(self):
        self.info['state'] = gf.tree_state(self.resultsTreeWidget, {})
        return self.info['state']

    def apply_state(self, state=None):
        if not state:
            gf.tree_state_revert(self.resultsTreeWidget, self.info['state'])
        else:
            gf.tree_state_revert(self.resultsTreeWidget, state)

    def get_offset(self):
        return self.info['offset']

    def collect_offset(self):
        if self.bottom_navigataion_widget:
            return self.bottom_navigataion_widget.get_offset()
        else:
            return self.info['offset']

    def set_offset(self, offset):
        self.info['offset'] = offset

    def get_group_by(self):
        return self.info['group_by']

    def get_limit(self):
        return self.info['limit']

    def set_limit(self, limit):
        self.info['limit'] = limit

    def get_current_index(self):
        checkin_out_widget = self.get_current_checkin_out_widget()
        search_widget = checkin_out_widget.get_search_widget()
        results_tab_widget = search_widget.get_results_tab_widget()
        current_idx = results_tab_widget.indexOf(self)

        return current_idx

    def set_search_line_text(self, text):
        self.info['search_line_text'] = text

    def get_cuttent_view(self):
        return self.info.get('view')

    def set_cuttent_view(self, view):
        self.info['view'] = view

    def get_search_line_text(self):
        return self.info.get('search_line_text')

    def get_tab_title(self):
        return self.info['title']

    def set_tab_title(self, title=u''):
        self.info['title'] = title
        checkin_out_widget = self.get_current_checkin_out_widget()
        search_widget = checkin_out_widget.get_search_widget()
        results_tab_widget = search_widget.get_results_tab_widget()
        current_idx = results_tab_widget.indexOf(self)
        if self.get_items_count():
            tab_title = u'{0} <b><span style=" font-size:7pt; color:#999999;">| {1}</span></b>'.format(title, self.get_items_count())
            #     <span style=" font-size:8pt; color:#00ff00;">Getting Search Types</span>
        else:
            tab_title = title

        tab_label = results_tab_widget.tabBar().tabButton(current_idx, QtGui.QTabBar.RightSide)
        tab_label.close()
        tab_label = gf.create_tab_label(tab_title)
        tab_label.setParent(self)
        results_tab_widget.tabBar().setTabButton(current_idx, QtGui.QTabBar.RightSide, tab_label)

        # results_tab_widget.setTabText(current_idx, tab_title)

    def get_filters(self):
        return self.info['filters']

    def set_filters(self, filters):
        self.info['filters'] = filters

    def get_items_count(self):
        return self.info.get('items_count')

    def set_items_count(self, items_count):
        self.info['items_count'] = items_count

    def update_filters(self, check_valid=False):
        checkin_out_widget = self.get_current_checkin_out_widget()
        adv_search_widget = checkin_out_widget.get_advanced_search_widget()

        self.set_filters(adv_search_widget.get_filters(check_valid))

    def controls_actions(self):
        self.resultsTreeWidget.itemSelectionChanged.connect(self.selection_changed)
        self.resultsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsTreeWidget.customContextMenuRequested.connect(self.open_item_context_menu)

        self.resultsTreeWidget.itemCollapsed.connect(self.send_collapse_event_to_item)
        self.resultsTreeWidget.itemExpanded.connect(self.send_expand_event_to_item)
        self.resultsTreeWidget.itemDoubleClicked.connect(self.send_item_double_click)

        # Separate Snapshots tree widget actions
        self.resultsVersionsTreeWidget.itemPressed.connect(lambda: self.set_current_results_versions_tree_widget_item(
            self.resultsVersionsTreeWidget))

        self.resultsVersionsTreeWidget.itemPressed.connect(self.load_preview)
        self.resultsVersionsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsVersionsTreeWidget.customContextMenuRequested.connect(self.open_item_context_menu)
        self.resultsVersionsTreeWidget.itemDoubleClicked.connect(self.send_item_double_click)

    def customize_ui(self):

        # self.resultsTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        self.resultsTreeWidget.setAlternatingRowColors(True)
        self.resultsTreeWidget.setStyleSheet(gf.get_qtreeview_style(True))
        self.resultsTreeWidget.setFocusPolicy(QtCore.Qt.NoFocus)

        self.resultsVersionsTreeWidget.setAlternatingRowColors(True)
        self.resultsVersionsTreeWidget.setStyleSheet(gf.get_qtreeview_style(True))
        self.resultsVersionsTreeWidget.setFocusPolicy(QtCore.Qt.NoFocus)

    def get_results_tree_widget(self):
        return self.resultsTreeWidget

    def get_results_versions_tree_widget(self):
        return self.resultsVersionsTreeWidget

    def selection_changed(self):
        if self.resultsTreeWidget.selectedItems():
            current_index = self.resultsTreeWidget.currentIndex()

            if current_index.row() == -1:
                last_item = self.resultsTreeWidget.selectedItems()[-1]
                current_index = self.resultsTreeWidget.indexFromItem(last_item)

            current_tree_item = self.resultsTreeWidget.itemFromIndex(current_index)

            gf.filter_multiple_selected_items(
                self.resultsTreeWidget,
                self.resultsTreeWidget.selectedItems(),
                current_tree_item
            )

            self.fill_versions_items(current_tree_item, 0)
            self.current_tree_widget_item = self.resultsTreeWidget.itemWidget(current_tree_item, 0)

            items_list = []
            for item in self.resultsTreeWidget.selectedItems():
                items_list.append(self.resultsTreeWidget.itemWidget(item, 0))

            self.load_preview(items_list)

    def open_item_context_menu(self):
        checkin_out_widget = self.get_current_checkin_out_widget()
        checkin_out_widget.open_item_menu(self.get_current_tree_widget_item())

    def query_sobjects(self, filters, stype, project, order_bys=[], limit=None, offset=None):

        search_type = tc.server_start().build_search_type(stype, project)

        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Getting SObjects</span>')

        self.show_overlay()

        def get_sobjects_agent():
            """ If we have traceback, it points us here"""
            return tc.get_sobjects(
                search_type=search_type,
                filters=filters,
                order_bys=order_bys,
                project_code=project,
                limit=limit,
                offset=offset,
                check_snapshots_updates=tc.get_snapshots_updates_list(stype, project)
            )

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        query_sobjects_worker = gf.get_thread_worker(
            get_sobjects_agent,
            thread_pool=env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=self.fill_items,
            error_func=gf.error_handle
        )
        query_sobjects_worker.start()

    def query_group_by_sobjects(self, search_type, project_code, group_by=[]):

        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Getting SObjects</span>')

        def get_sobjects_agent():
            return tc.get_group_sobjects(
                search_type=search_type,
                project_code=project_code,
                groups_list=group_by,
            )

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        query_sobjects_worker = gf.get_thread_worker(
            get_sobjects_agent,
            thread_pool=env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=self.fill_group_by_items,
            error_func=gf.error_handle
        )
        query_sobjects_worker.start()

    @gf.catch_error
    def fill_items(self, result):
        self.hide_overlay()
        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Filling SObjects</span>')

        self.sobjects = result[0]
        self.query_info = result[1]

        gf.recursive_close_tree_item_widgets(self.resultsTreeWidget)
        self.resultsTreeWidget.clear()
        # self.resultsVersionsTreeWidget.clear()
        # self.resultsTreeWidget.setUniformRowHeights(True)
        self.progress_bar.setVisible(True)
        total_sobjects = len(self.sobjects.keys()) - 1

        # s = gf.time_it()

        # tree_items_list = []
        # tree_widgets_list = []
        for i, sobject in enumerate(self.sobjects.values()):
            last_state = None
            if self.info['state']:
                last_state = self.info['state'].get(i)

            item_info = {
                'relates_to': 'checkin_out',
                'sep_versions': self.sep_versions,
                'children_states': last_state,
                'simple_view': self.info.get('simple_view'),
            }
            gf.add_sobject_item(
                self.resultsTreeWidget,
                self,
                sobject,
                self.stype,
                item_info,
                ignore_dict=None,
            )

            # tree_items_list.append(tree_widget.tree_item)
            # tree_widgets_list.append(tree_widget)
            if total_sobjects:
                if i+1 % 20 == 0:
                    self.progress_bar.setValue(int(i+1 * 100 / total_sobjects))

        # gf.time_it(s)
        # s = gf.time_it()
        # self.resultsTreeWidget.addTopLevelItems(tree_items_list)
        # for tree_item, tree_item_widget in zip(tree_items_list, tree_widgets_list):
        #     tree_item_widget.setParent(self.resultsTreeWidget)
        #     self.resultsTreeWidget.setItemWidget(tree_item, 0, tree_item_widget)
        #
        # # print tree_items_list
        # gf.time_it(s)
        self.set_items_count(int(self.query_info.get('total_sobjects_query_count')))

        if not self.info.get('simple_view'):
            if not self.info['title'] and not self.get_tab_title():
                self.set_tab_title(self.stype.get_pretty_name())
            else:
                self.set_tab_title(self.info['title'])

            if self.get_state():

                if self.info.get('refresh'):
                    self.info['refresh'] = None

                self.info['state'] = None

        self.progress_bar.setVisible(False)

        self.bottom_navigataion_widget.init_navigation(self.query_info)

        if not self.info.get('simple_view'):
            self.update_filters(True)

        self.resultsTreeWidget.resizeColumnToContents(0)

        env_inst.ui_main.set_info_status_text('')

    @gf.catch_error
    def fill_group_by_items(self, result):

        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Filling SObjects</span>')
        self.group_by_column = []
        self.group_by_list = []

        for group in result:
            self.group_by_column, self.group_by_list = itertools.takewhile(list, group)

        gf.recursive_close_tree_item_widgets(self.resultsTreeWidget)
        self.resultsTreeWidget.clear()
        self.resultsVersionsTreeWidget.clear()

        self.progress_bar.setVisible(True)
        total_sobjects = len(self.group_by_list) - 1

        for i, group in enumerate(self.group_by_list):

            last_state = None
            # if self.info['state']:
            #     last_state = self.info['state'].get(i)

            item_info = {
                'relates_to': 'checkin_out',
                'sep_versions': self.sep_versions,
                'children_states': last_state,
                'simple_view': self.info.get('simple_view'),
            }
            gf.add_group_by_item(
                self.resultsTreeWidget,
                self,
                group,
                self.group_by_column,
                [],
                self.stype,
                item_info,
            )
            if total_sobjects:
                if i+1 % 20 == 0:
                    self.progress_bar.setValue(int(i+1 * 100 / total_sobjects))

        # self.set_items_count(int(self.query_info.get('total_sobjects_query_count')))

        # if not self.info.get('simple_view'):
        #     if not self.info['title'] and not self.get_tab_title():
        #         self.set_tab_title(self.stype.get_pretty_name())
        #     else:
        #         self.set_tab_title(self.info['title'])
        #
        #     if self.get_state():
        #
        #         if self.info.get('refresh'):
        #             self.info['refresh'] = None
        #
        #         self.info['state'] = None

        self.progress_bar.setVisible(False)

        # self.bottom_navigataion_widget.init_navigation(self.query_info)

        # if not self.info.get('simple_view'):
        #     self.update_filters(True)

        self.resultsTreeWidget.resizeColumnToContents(0)

        env_inst.ui_main.set_info_status_text('')

    def create_bottom_navigation_widget(self):
        self.bottom_navigataion_widget = Ui_navigationWidget(project=self.project, stype=self.stype)
        self.bottom_navigataion_widget.refresh_search.connect(self.update_search_results)

        self.bottom_navigataion_widget.setHidden(True)

        self.resultsLayout.addWidget(self.bottom_navigataion_widget)

    @gf.catch_error
    def send_item_double_click(self, *args):
        modifiers = QtGui.QApplication.keyboardModifiers()

        checkin_out_widget = self.get_current_checkin_out_widget()

        checkin_options_widget = checkin_out_widget.get_checkin_options_widget_config()

        # current_widget = checkin_out_widget.get_current_tree_widget()
        # current_tree_widget_item = current_widget.get_current_tree_widget_item()

        current_tree_widget_item = self.get_current_tree_widget_item()

        if modifiers == QtCore.Qt.ShiftModifier and checkin_options_widget.doubleClickOpenCheckBox.isChecked():
            if current_tree_widget_item.type == 'snapshot':
                checkin_out_widget.open_file()
        if checkin_options_widget.doubleClickSaveCheckBox.isChecked():
            if current_tree_widget_item.type in ['process', 'snapshot', 'sobject']:
                checkin_out_widget.save_file()

    @gf.catch_error
    def set_current_results_tree_widget_item(self, tree_widget):
        self.current_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)
        self.current_results_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)

    @gf.catch_error
    def set_current_results_versions_tree_widget_item(self, tree_widget):
        self.current_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)
        self.current_results_versions_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)

    def get_current_checkin_out_widget(self):
        return env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

    def get_current_tree_widget_item(self):
        if not self.current_tree_widget_item:
            self.set_current_results_tree_widget_item(self.resultsTreeWidget)
        return self.current_tree_widget_item

    def get_current_results_tree_widget_item(self):
        return self.current_results_tree_widget_item

    def get_current_results_versions_tree_widget_item(self):
        return self.current_results_versions_tree_widget_item

    def update_current_items_trees(self, force_full_update=False):
        if env_inst.get_thread_pool('server_query/server_thread_pool'):
            if env_inst.get_thread_pool('server_query/server_thread_pool').activeThreadCount() == 0:
                if force_full_update:
                    self.search_widget.search_results_widget.update_item_tree(force_full_update=True)
                elif self.current_results_versions_tree_widget_item:
                    self.current_results_versions_tree_widget_item = None
                    self.search_widget.search_results_widget.update_item_tree(self.current_results_versions_tree_widget_item)
                elif self.current_results_tree_widget_item:
                    self.current_results_tree_widget_item = None
                    self.search_widget.search_results_widget.update_item_tree(self.current_results_tree_widget_item)

    @gf.catch_error
    def send_collapse_event_to_item(self, tree_item):
        tree_widget = self.resultsTreeWidget.itemWidget(tree_item, 0)
        tree_widget.collapse_tree_item()

        if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            tree_widget.collapse_recursive()

    @gf.catch_error
    def send_expand_event_to_item(self, tree_item):
        tree_widget = self.resultsTreeWidget.itemWidget(tree_item, 0)
        tree_widget.expand_tree_item()

        if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            tree_widget.expand_recursive()

    @gf.catch_error
    def fill_versions_items(self, widget, *args):

        if self.resultsVersionsTreeWidget.isVisible():
            item_widget = self.resultsTreeWidget.itemWidget(widget, 0)

            if item_widget.type == 'snapshot':
                process = item_widget.process
                context = item_widget.context
                snapshots = item_widget.sobject.process[process].contexts[context].versions

                self.resultsVersionsTreeWidget.clear()
                gf.add_versions_snapshot_item(
                    self.resultsVersionsTreeWidget,
                    self,
                    item_widget.sobject,
                    item_widget.stype,
                    item_widget.get_current_process_pipeline(),
                    snapshots,
                    item_widget.info,
                )

            elif item_widget.type == 'sobject':

                snapshots = item_widget.get_all_snapshots()

                if snapshots:
                    ready_snapshots = None
                    self.resultsVersionsTreeWidget.clear()

                    if snapshots.get('publish'):
                        ready_snapshots = item_widget.get_snapshots('publish')
                    elif snapshots.get('icon'):
                        ready_snapshots = item_widget.get_snapshots('icon')
                    else:
                        processes = item_widget.get_all_snapshots()
                        process = processes.keys()[0]
                        if process:
                            ready_snapshots = item_widget.get_snapshots(process)

                    if ready_snapshots:
                        gf.add_versions_snapshot_item(
                            self.resultsVersionsTreeWidget,
                            self,
                            item_widget.sobject,
                            item_widget.stype,
                            item_widget.get_current_process_pipeline(),
                            ready_snapshots,
                            item_widget.info,
                        )
                else:
                    self.resultsVersionsTreeWidget.clear()

            elif item_widget.type == 'process':
                snapshots = item_widget.get_snapshots()

                versions = False
                if not snapshots:
                    versions = True
                    snapshots = item_widget.get_snapshots(versionless=False)

                if snapshots:
                    self.resultsVersionsTreeWidget.clear()
                    if versions:
                        ready_snapshots = snapshots[0]
                    else:
                        ready_snapshots = collections.OrderedDict()
                        for snapshot in snapshots:
                            if snapshot:
                                ready_snapshots[snapshot.keys()[0]] = snapshot.values()[0]

                    gf.add_versions_snapshot_item(
                        self.resultsVersionsTreeWidget,
                        self,
                        item_widget.sobject,
                        item_widget.stype,
                        item_widget.get_current_process_pipeline(),
                        ready_snapshots,
                        item_widget.info,
                    )

                else:
                    self.resultsVersionsTreeWidget.clear()

            elif item_widget.type == 'child':
                self.resultsVersionsTreeWidget.clear()
            else:
                self.resultsVersionsTreeWidget.clear()

            self.resultsVersionsTreeWidget.resizeColumnToContents(0)

    def clear_versionless_tree_widget(self):
        gf.recursive_close_tree_item_widgets(self.resultsTreeWidget)
        self.resultsTreeWidget.clear()

    def clear_versions_tree_widget(self):
        gf.recursive_close_tree_item_widgets(self.resultsVersionsTreeWidget)
        self.resultsVersionsTreeWidget.clear()

    def clear_tree_widgets(self):
        self.clear_versionless_tree_widget()
        self.clear_versions_tree_widget()

    def browse_snapshot(self, item):

        checkin_out_widget = self.get_current_checkin_out_widget()
        snapshot_browser = checkin_out_widget.get_snapshot_browser()

        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.AltModifier:
            checkin_out_widget.bring_snapshot_browser_dock_up()

        # if not snapshot_browser.visibleRegion().isEmpty():
        snapshot_browser.set_item_widget(item)

    def browse_tasks(self, items_list):

        checkin_out_widget = self.get_current_checkin_out_widget()
        tasks_widget = checkin_out_widget.get_tasks_widget()
        sobjects_list = []
        for item in items_list:
            sobjects_list.append(item.sobject)

        if sobjects_list:
            tasks_widget.set_sobjects(sobjects_list)

    def browse_task(self, item):

        checkin_out_widget = self.get_current_checkin_out_widget()
        tasks_widget = checkin_out_widget.get_tasks_widget()

        tasks_widget.set_sobject(item.sobject)

    @gf.catch_error
    def load_preview(self, selected_items_list, *args):
        nested_item = self.current_tree_widget_item

        checkin_out_widget = self.get_current_checkin_out_widget()

        description_widget = checkin_out_widget.get_description_widget()

        columns_viewer_widget = checkin_out_widget.get_columns_viewer_widget()

        fast_controls_widget = checkin_out_widget.get_fast_controls_widget()

        if nested_item.type in ['sobject', 'snapshot', 'process']:
            fast_controls_widget.set_item(nested_item)
            description_widget.set_item(nested_item)
            if isinstance(selected_items_list, list):
                if len(selected_items_list) > 1:
                    columns_viewer_widget.set_items(selected_items_list)
                    self.browse_tasks(selected_items_list)
                else:
                    columns_viewer_widget.set_item(nested_item)
                    self.browse_task(nested_item)
            else:
                columns_viewer_widget.set_item(nested_item)
                self.browse_task(nested_item)

            self.browse_snapshot(nested_item)

        else:
            fast_controls_widget.set_item(None)
            description_widget.set_item(None)

    def get_is_separate_versions(self):
        return self.sep_versions

    # def create_separate_versions_tree(self):
    #
    #     self.sep_versions = gf.get_value_from_config(self.checkin_out_config, 'versionsSeparateCheckinCheckBox')
    #     if self.sep_versions:
    #         self.sep_versions = bool(int(self.sep_versions))
    #
    #     if not self.sep_versions:
    #         self.resultsVersionsTreeWidget.setHidden(True)
    #     else:
    #         if gf.get_value_from_config(self.checkin_out_config, 'bottomVersionsRadioButton'):
    #             self.items_view_splitter.setOrientation(QtCore.Qt.Vertical)
    #         else:
    #             self.items_view_splitter.setOrientation(QtCore.Qt.Horizontal)

    def create_progress_bar(self):
        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.hide()
        self.resultsLayout.addWidget(self.progress_bar)

    def showEvent(self, event):

        if not self.created:
            if self.info.get('simple_view'):
                self.create_simple_view_ui()
            else:
                self.create_ui()

        event.accept()

    def resizeEvent(self, event):
        if self.overlay_layout_widget:
            self.overlay_layout_widget.resize(self.size())
        event.accept()
