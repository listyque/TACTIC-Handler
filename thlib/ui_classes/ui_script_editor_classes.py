# -*- coding: utf-8 -*-

# Copyright (c) 2019, Krivospitskiy Alexey, <listy@live.ru>, https://github.com/listyque/TACTIC-Handler
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0


__all__ = ['Ui_ScriptEditForm']


import os
import io
import time
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.tactic_classes as tc
import thlib.global_functions as gf
from thlib.environment import env_inst, env_mode, env_read_config, env_write_config, env_write_file
from thlib.ui_classes.ui_misc_classes import Ui_horizontalCollapsableWidget
from thlib.side.console.core import console, stream
from thlib.side.console.ui import editor_window, output_window


class Ui_ScriptEditForm(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.sripts_languages = [
            ('Local-Python', 'local_python'),
            ('Server-Python', 'python'),
            ('Javascript', 'javascript'),
            ('Server-JS', 'server_js'),
            ('Expression', 'expression'),
            ('Xml', 'xml'),
        ]

        env_inst.ui_script_editor = self

        self.ui_settings_dict = {}

        self.create_ui()

        self.controls_actions()

    def create_ui(self):

        self.setWindowTitle('Script editor')
        self.setObjectName("scriptEditForm")
        self.resize(720, 550)
        self.setSizeGripEnabled(True)
        self.setWindowFlags(QtCore.Qt.Window)

        font = Qt4Gui.QFont()
        font.setPointSize(10)
        font.setFamily('Courier')

        self.main_grid_layout = QtGui.QGridLayout(self)
        self.setLayout(self.main_grid_layout)

        self.main_grid_layout.setObjectName("main_grid_layout")

        self.main_splitter = QtGui.QSplitter(self)
        self.main_splitter.setOrientation(QtCore.Qt.Horizontal)
        self.main_splitter.setObjectName("main_splitter")

        self.verticalLayoutWidget = QtGui.QWidget(self.main_splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")

        self.script_editor_vertical_layout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.script_editor_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.script_editor_vertical_layout.setObjectName("script_editor_vertical_layout")

        self.script_path_horizontal_layout = QtGui.QHBoxLayout()
        self.script_path_horizontal_layout.setObjectName("script_path_horizontal_layout")

        self.path_label = QtGui.QLabel(self.verticalLayoutWidget)
        self.path_label.setObjectName("path_label")
        self.path_label.setText('Script path: ')

        self.first_path_part_line_edit = QtGui.QLineEdit(self.verticalLayoutWidget)
        self.first_path_part_line_edit.setObjectName("first_path_part_line_edit")

        self.slash_label = QtGui.QLabel(self.verticalLayoutWidget)
        self.slash_label.setObjectName("slash_label")
        self.slash_label.setText(' / ')

        self.second_path_part_line_edit = QtGui.QLineEdit(self.verticalLayoutWidget)
        self.second_path_part_line_edit.setObjectName("second_path_part_line_edit")

        self.script_language_combo_box = QtGui.QComboBox(self.verticalLayoutWidget)
        for script in self.sripts_languages:
            self.script_language_combo_box.addItem(script[0])

        self.create_left_collapsable_toolbar()
        self.create_right_collapsable_toolbar()

        self.script_path_horizontal_layout.addWidget(self.left_collapsable_toolbar)
        self.script_path_horizontal_layout.setStretch(0, 0)
        self.script_path_horizontal_layout.addWidget(self.path_label)
        self.script_path_horizontal_layout.setStretch(1, 0)
        self.script_path_horizontal_layout.addWidget(self.first_path_part_line_edit)
        self.script_path_horizontal_layout.setStretch(2, 1)
        self.script_path_horizontal_layout.addWidget(self.slash_label)
        self.script_path_horizontal_layout.setStretch(3, 0)
        self.script_path_horizontal_layout.addWidget(self.second_path_part_line_edit)
        self.script_path_horizontal_layout.setStretch(4, 1)
        self.script_path_horizontal_layout.addWidget(self.script_language_combo_box)
        self.script_path_horizontal_layout.setStretch(5, 0)
        self.script_path_horizontal_layout.addWidget(self.right_collapsable_toolbar)
        self.script_path_horizontal_layout.setStretch(6, 0)

        self.script_editor_vertical_layout.addLayout(self.script_path_horizontal_layout)

        self.splitter = QtGui.QSplitter(self.verticalLayoutWidget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")

        self.output = output_window.OutputWindow(self)
        self.output.setFont(font)
        self.splitter.addWidget(self.output)

        self.console = editor_window.EditorWindow(self)
        self.console.setFont(font)
        self.splitter.addWidget(self.console)

        self.script_editor_vertical_layout.addWidget(self.splitter)

        self.down_buttons_horizontal_layout = QtGui.QHBoxLayout()
        self.down_buttons_horizontal_layout.setObjectName("down_buttons_horizontal_layout")

        self.run_script_button = QtGui.QPushButton(self.verticalLayoutWidget)
        self.run_script_button.setObjectName("run_script_button")
        self.run_script_button.setText('Run Script')
        self.run_script_button.setFlat(True)
        self.run_script_button.setIcon(gf.get_icon('play', icons_set='mdi'))

        self.execute_label = QtGui.QLabel(self.verticalLayoutWidget)
        self.execute_label.setObjectName("execute_label")
        self.execute_label.setText('Execute: ')

        self.run_type_combo_box = QtGui.QComboBox(self.verticalLayoutWidget)
        self.run_type_combo_box.setObjectName("run_type_combo_box")
        self.run_type_combo_box.addItem('Locally')
        self.run_type_combo_box.addItem('Server-Side')

        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)

        self.down_buttons_horizontal_layout.addWidget(self.run_script_button)
        self.down_buttons_horizontal_layout.addItem(spacerItem)
        self.down_buttons_horizontal_layout.addWidget(self.execute_label)
        self.down_buttons_horizontal_layout.addWidget(self.run_type_combo_box)

        self.script_editor_vertical_layout.addLayout(self.down_buttons_horizontal_layout)

        self.scripts_tree_widget = QtGui.QTreeWidget(self.main_splitter)
        self.scripts_tree_widget.setAlternatingRowColors(True)
        self.scripts_tree_widget.setAllColumnsShowFocus(True)
        self.scripts_tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.scripts_tree_widget.setStyleSheet('QTreeView::item {padding: 2px;}')
        self.scripts_tree_widget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.scripts_tree_widget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.scripts_tree_widget.setRootIsDecorated(True)
        self.scripts_tree_widget.setHeaderHidden(True)
        self.scripts_tree_widget.setObjectName('scripts_tree_widget')

        self.scripts_tree_widget.setColumnCount(2)

        self.main_grid_layout.addWidget(self.main_splitter)

        self.stream = stream.Stream.get_stream()
        if self.stream is None:
            self.stream = stream.Stream()

        self.console_obj = console.Console()

        if env_inst.get_current_project():
            self.fill_sctipts_tree_widget()

    def controls_actions(self):
        self.run_script_button.clicked.connect(self.run_script)

        self.stream.outputWritten.connect(self.output.write_output)
        self.stream.errorWritten.connect(self.output.write_error)
        self.stream.inputWritten.connect(self.output.write_input)

        self.scripts_tree_widget.itemSelectionChanged.connect(self.scripts_tree_widget_items_selection_changed)

        self.scripts_tree_widget.itemExpanded.connect(lambda: self.scripts_tree_widget.resizeColumnToContents(0))


        self.add_new_script_button.clicked.connect(self.create_new_script)
        self.save_current_script_button.clicked.connect(self.save_current_script)
        self.refresh_serverside_scripts_button.clicked.connect(self.refresh_scripts_tree)
        self.cleanup_output_button.clicked.connect(self.cleanup_output)

        self.script_language_combo_box.currentIndexChanged.connect(self.handle_scripts_language_combo_box)

    def create_right_collapsable_toolbar(self):
        self.right_collapsable_toolbar = Ui_horizontalCollapsableWidget()
        self.right_collapsable_toolbar.setCollapsed(False)

        self.right_buttons_layout = QtGui.QHBoxLayout()
        self.right_buttons_layout.setSpacing(0)
        self.right_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.right_collapsable_toolbar.setLayout(self.right_buttons_layout)

        self.refresh_serverside_scripts_button = QtGui.QToolButton()
        self.refresh_serverside_scripts_button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.refresh_serverside_scripts_button.setAutoRaise(True)
        self.refresh_serverside_scripts_button.setMinimumSize(QtCore.QSize(24, 24))
        self.refresh_serverside_scripts_button.setMaximumSize(QtCore.QSize(24, 24))
        self.refresh_serverside_scripts_button.setIcon(gf.get_icon('refresh', icons_set='mdi'))
        self.refresh_serverside_scripts_button.setToolTip('Refresh all Scripts Tree from Server')

        self.right_buttons_layout.addWidget(self.refresh_serverside_scripts_button)

    def create_left_collapsable_toolbar(self):
        self.left_collapsable_toolbar = Ui_horizontalCollapsableWidget()
        self.left_collapsable_toolbar.setCollapsed(False)

        self.left_buttons_layout = QtGui.QHBoxLayout()
        self.left_buttons_layout.setSpacing(0)
        self.left_buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.left_collapsable_toolbar.setLayout(self.left_buttons_layout)

        self.add_new_script_button = QtGui.QToolButton()
        self.add_new_script_button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.add_new_script_button.setAutoRaise(True)
        self.add_new_script_button.setMinimumSize(QtCore.QSize(24, 24))
        self.add_new_script_button.setMaximumSize(QtCore.QSize(24, 24))
        self.add_new_script_button.setIcon(gf.get_icon('plus-box', icons_set='mdi'))
        self.add_new_script_button.setToolTip('Create New Script')

        self.cleanup_output_button = QtGui.QToolButton()
        self.cleanup_output_button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.cleanup_output_button.setAutoRaise(True)
        self.cleanup_output_button.setMinimumSize(QtCore.QSize(24, 24))
        self.cleanup_output_button.setMaximumSize(QtCore.QSize(24, 24))
        self.cleanup_output_button.setIcon(gf.get_icon('eraser', icons_set='mdi'))
        self.cleanup_output_button.setToolTip('Clean-up Output Window')

        self.save_current_script_button = QtGui.QToolButton()
        self.save_current_script_button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.save_current_script_button.setAutoRaise(True)
        self.save_current_script_button.setMinimumSize(QtCore.QSize(24, 24))
        self.save_current_script_button.setMaximumSize(QtCore.QSize(24, 24))
        self.save_current_script_button.setIcon(gf.get_icon('content-save', icons_set='mdi'))
        self.save_current_script_button.setToolTip('Save current Script to Sever')

        self.left_buttons_layout.addWidget(self.add_new_script_button)
        self.left_buttons_layout.addWidget(self.save_current_script_button)
        self.left_buttons_layout.addWidget(self.cleanup_output_button)

    def scripts_tree_widget_items_selection_changed(self):

        if self.scripts_tree_widget.selectedItems():
            current_scripts_tree_widget_item = self.scripts_tree_widget.selectedItems()[0]
            script_sobject = current_scripts_tree_widget_item.data(0, QtCore.Qt.UserRole)

            if not isinstance(script_sobject, list):
                self.fill_by_sobject(script_sobject)

    def fill_by_sobject(self, sobject):
        # QtGui.QPlainTextEdit.setPlainText()
        self.console.setPlainText(sobject.get_value('script'))
        self.first_path_part_line_edit.setText(sobject.get_value('folder'))
        self.second_path_part_line_edit.setText(sobject.get_value('title'))

    def handle_scripts_language_combo_box(self, i):
        if i is not None:
            self.run_type_combo_box.setEnabled(True)
            self.run_script_button.setEnabled(True)
            selected_language = self.sripts_languages[int(i)]
            if selected_language[1] == 'local_python':
                self.run_type_combo_box.setCurrentIndex(0)
            elif selected_language[1] in ['server_js', 'python', 'expression']:
                self.run_type_combo_box.setCurrentIndex(1)
            else:
                self.run_type_combo_box.setEnabled(False)
                self.run_script_button.setEnabled(False)

    @staticmethod
    def get_scripts_from_server():
        search_type = tc.server_start().build_search_type('config/custom_script', project_code=env_inst.get_current_project())
        scripts_sobjects, data = tc.get_sobjects_new(search_type)
        return scripts_sobjects

    @env_inst.async_engine
    def fill_sctipts_tree_widget(self):

        # getting all the scripts from db
        scripts_sobjects = yield env_inst.async_task(self.get_scripts_from_server)

        if scripts_sobjects:
            scripts_sobjects_by_folder = tc.group_sobject_by(scripts_sobjects, 'folder')

            # adding scripts to tree widget
            for folder_path, sobjects_list in scripts_sobjects_by_folder.items():
                subgroup_list = folder_path.split('/')
                if len(subgroup_list) > 1:
                    subgroup_list.reverse()
                    top_item_title = subgroup_list.pop()
                    exist_item = gf.check_tree_items_exists(self.scripts_tree_widget, top_item_title)
                    if exist_item:
                        gf.recursive_add_items(exist_item, subgroup_list)
                    else:
                        root_item = QtGui.QTreeWidgetItem(self.scripts_tree_widget)
                        root_item.setText(0, top_item_title)
                        root_item.setData(0, 12, top_item_title)
                        root_item.setData(0, QtCore.Qt.UserRole, sobjects_list)
                        root_item.setIcon(0, gf.get_icon('folder', icons_set='mdi'))
                        self.scripts_tree_widget.addTopLevelItem(root_item)
                        gf.recursive_add_items(root_item, subgroup_list)
                else:
                    root_item = QtGui.QTreeWidgetItem(self.scripts_tree_widget)
                    root_item.setText(0, folder_path)
                    root_item.setData(0, 12, folder_path)
                    root_item.setData(0, QtCore.Qt.UserRole, sobjects_list)
                    root_item.setIcon(0, gf.get_icon('folder', icons_set='mdi'))
                    exist_item = gf.check_tree_items_exists(self.scripts_tree_widget, folder_path)
                    if not exist_item:
                        self.scripts_tree_widget.addTopLevelItem(root_item)

                    # adding child items with scripts sobjects itself
                    for sobject in sobjects_list:
                        gf.add_child_items(root_item, sobject)

            paths_to_create_init_set = set()
            sub_path = env_inst.get_current_project()

            # writing scripts to local folder
            for folder_path, sobjects_list in scripts_sobjects_by_folder.items():
                for sobject in sobjects_list:
                    ext = 'py'
                    if sobject.get_value('language') == 'javascript':
                        ext = 'js'
                    file_name = u'{}.{}'.format(sobject.get_value('title'), ext)
                    env_write_file(
                        sobject.get_value('script'),
                        folder_path,
                        file_name,
                        sub_path
                    )
                paths_list = folder_path.split('/')

                if paths_list:
                    path_parts = ''
                    for path in paths_list:
                        path_parts = u'{}/{}'.format(path_parts, path)
                        if path_parts:
                            if sub_path:
                                full_path = u'{0}/custom_scripts/{1}/{2}/__init__.py'.format(
                                    env_mode.get_current_path(),
                                    sub_path,
                                    path_parts)
                            else:
                                full_path = u'{0}/custom_scripts/{1}/__init__.py'.format(
                                    env_mode.get_current_path(),
                                    path_parts)
                            paths_to_create_init_set.add(full_path)

            if sub_path:
                paths_to_create_init_set.add(u'{0}/custom_scripts/{1}/__init__.py'.format(
                    env_mode.get_current_path(),
                    sub_path))

            paths_to_create_init_set.add(u'{0}/custom_scripts/__init__.py'.format(
                env_mode.get_current_path()))

            # create __init__ files so we can access files from script editor
            for init_path in paths_to_create_init_set:
                formed_init_path = gf.form_path(init_path)
                if not os.path.exists(formed_init_path):
                    with io.open(formed_init_path, 'w+') as init_py_file:
                        init_py_file.write(u'')
                    init_py_file.close()

    def get_current_script(self):
        return self.console.toPlainText()

    def run_locally(self, whole=False):
        if self.run_script_button.isEnabled():
            if whole:
                text = self.console.toPlainText()
            else:
                text = self.console.selectedText()
                self.stream.input(text)

            text = text.replace(u"\u2029", "\n")
            text = text.replace(u"\u2028", "\n")
            if not text or text == "":
                text = self.console.toPlainText()

            self.output.moveCursor(Qt4Gui.QTextCursor.End)

            self.output.scroll_to_bottom()
            self.console_obj.enter(text)

    def run_serverside(self, whole=True):
        if self.run_script_button.isEnabled():
            if whole:
                text = self.console.toPlainText()
            else:
                text = self.console.selectedText()
                self.stream.input(text)

            text = text.replace(u"\u2029", "\n")
            text = text.replace(u"\u2028", "\n")
            if not text or text == "":
                text = self.console.toPlainText()

            self.output.moveCursor(Qt4Gui.QTextCursor.End)

            self.output.scroll_to_bottom()

            code_dict = {
                'code': text
            }
            start = time.time()
            result = tc.server_start().execute_python_script('', kwargs=code_dict)
            print('\nServe-Side execution time: {}\n'.format(time.time() - start))

            from pprint import pprint
            if not result['info']['spt_ret_val']:
                print(result['status'])
            else:
                pprint(result['info']['spt_ret_val'])

    def run_script(self):
        if self.run_type_combo_box.currentIndex() == 0:
            self.run_locally()
        elif self.run_type_combo_box.currentIndex() == 1:
            self.run_serverside()

    def run_script_path(self, script_path, local=True, serverside=False):

        pass

    def cleanup_output(self):

        self.output.clear()

    def refresh_scripts_tree(self):

        self.scripts_tree_widget.clear()
        self.fill_sctipts_tree_widget()

    def create_new_script(self):

        self.console.clear()
        self.first_path_part_line_edit.setText('')
        self.second_path_part_line_edit.setText('')

        self.refresh_scripts_tree()

    def save_current_script(self):

        script_folder = self.first_path_part_line_edit.text()
        script_title = self.second_path_part_line_edit.text()
        if script_folder and script_title:
            search_type = tc.server_start().build_search_type('config/custom_script', project_code=env_inst.get_current_project())
            filters = [('folder', script_folder), ('title', script_title)]
            script_sobjects, data = tc.get_sobjects_new(search_type, filters)

            if len(script_sobjects) > 0:
                script_sobject = script_sobjects.values()[0]

                script_sobject.set_data('script', self.get_current_script())
                script_sobject.commit(False)
            else:
                tc.server_start().insert(search_type, dict(filters))

            self.refresh_scripts_tree()

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
            'pos': self.pos().toTuple(),
            'size': self.size().toTuple(),
            'windowState': False,
            'main_splitter': None,
            'splitter': None,
            'scripts_tree_widget': None,
            }

        self.move(settings_dict['pos'][0], settings_dict['pos'][1])
        self.resize(settings_dict['size'][0], settings_dict['size'][1])

        if settings_dict['windowState']:
            self.setWindowState(QtCore.Qt.WindowMaximized)

        if settings_dict.get('main_splitter'):
            self.main_splitter.restoreState(QtCore.QByteArray.fromHex(str(settings_dict.get('main_splitter'))))

        if settings_dict.get('splitter'):
            self.splitter.restoreState(QtCore.QByteArray.fromHex(str(settings_dict.get('splitter'))))

        if settings_dict.get('scripts_tree_widget'):
            state = gf.from_json(settings_dict.get('scripts_tree_widget'), use_ast=True)
            gf.tree_state_revert(self.scripts_tree_widget, state, use_item_widgets=False)

    def get_settings_dict(self):
        settings_dict = {
            'windowState': False,
            'main_splitter': str(self.main_splitter.saveState().toHex()),
            'splitter': str(self.splitter.saveState().toHex()),
            'scripts_tree_widget': gf.to_json(gf.tree_state(self.scripts_tree_widget, {}), use_ast=True)
        }

        if self.windowState() == QtCore.Qt.WindowMaximized:
            state = True
            if self.ui_settings_dict:
                settings_dict['pos'] = self.ui_settings_dict['pos']
                settings_dict['size'] = self.ui_settings_dict['size']
            else:
                settings_dict['pos'] = self.pos().toTuple()
                settings_dict['size'] = self.size().toTuple()
        else:
            state = False
            settings_dict['pos'] = self.pos().toTuple()
            settings_dict['size'] = self.size().toTuple()

        settings_dict['windowState'] = state

        return settings_dict

    def readSettings(self):
        self.ui_settings_dict = env_read_config(filename='ui_script_editor', unique_id='ui_main', long_abs_path=True)
        self.set_settings_from_dict(self.ui_settings_dict)

    def writeSettings(self):
        env_write_config(self.get_settings_dict(), filename='ui_script_editor', unique_id='ui_main', long_abs_path=True)

    def showEvent(self, event):
        self.refresh_scripts_tree()
        self.readSettings()

        event.accept()

    def closeEvent(self, event):
        self.writeSettings()

        event.accept()
