# file ui_tasks_classes.py
# Main Window of tasks

# TODO Add stacked tasks, so when multiple contex can be choosen by context, of same context and status add more users
# TODO button to add more task, of more users to current task (plus button near user combo)
# TODO save on close (and autosave checkbox)
# TODO Highlight or add only one task process if Process Selected, not sobject or snapshot
# TODO Select all text in combo boxes (for fast search - click and type)
# TODO Filter combo box

from functools import partial

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.ui.tasks.ui_tasks as ui_tasks
from thlib.environment import env_inst, env_write_config, env_read_config
import ui_richedit_classes as richedit_widget
import ui_notes_classes as notes_widget
# import ui_item_task_classes as task_item_widget
import thlib.tactic_classes as tc
import thlib.global_functions as gf
from thlib.ui_classes.ui_custom_qwidgets import Ui_horizontalCollapsableWidget

reload(ui_tasks)
reload(richedit_widget)
reload(notes_widget)
# reload(task_item_widget)


class Ui_coloredComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setEditable(True)

        self.customize()

        self.controls_actions()

    def controls_actions(self):
        self.currentIndexChanged.connect(self.index_changed)

    def add_item(self, item_text, item_color=None, hex_color=None, item_data=None):
        if hex_color:
            c = gf.hex_to_rgb(hex_color, tuple=True)
            item_color = Qt4Gui.QColor(c[0], c[1], c[2], 128)

        if not item_color:
            self.addItem(item_text)
        else:
            model = self.model()
            item = Qt4Gui.QStandardItem(u'{0}'.format(item_text))
            item.setBackground(item_color)
            item.setData(item_color, 1)
            item.setData(item_text, 2)
            if item_data:
                item.setData(item_data, 3)
            model.appendRow(item)

    def index_changed(self):
        item_color = self.itemData(self.currentIndex(), 1)
        if item_color:
            c = item_color.toTuple()
            rgba_color = 'rgba({0}, {1}, {2}, {3})'.format(c[0], c[1], c[2], 192)
            self.setStyleSheet('QComboBox {background: ' + rgba_color + ';}')
            self.customize(rgba_color)
        else:
            self.setStyleSheet('')

    def customize(self, rgba_color=None):
        if not rgba_color:
            rgba_color = 'rgba(255, 255, 255, 48)'
        line_edit = self.lineEdit()
        line_edit.setStyleSheet("""
            QLineEdit {
                border: 0px;
                border-radius: 2px;
                show-decoration-selected: 1;
                padding: 0px 0px;
            """ + """background: {};""".format(rgba_color) +
                                """ background-position: bottom left;
                                    background-repeat: fixed;
                                    selection-background-color: darkgray;
                                    padding-left: 0px;
                                }
                                """)


class Ui_simpleTaskWidget(QtGui.QFrame):
    def __init__(self, process, parent_sobject, tasks_sobjects_list=None, parent_sobjects_list=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.process = process
        self.parent_sobject = parent_sobject
        self.tasks_sobjects_list = tasks_sobjects_list
        self.parent_sobjects_list = parent_sobjects_list
        self.current_task_sobject = None
        self.multiple_mode = False
        self.total_tasks = 0

        self.task_data_dict = {}
        self.initial_task_data_dict = {}

        self.create_ui()

        self.create_filler()

        self.controls_actions()

    def controls_actions(self):
        self.statuses_combo_box.currentIndexChanged.connect(self.statuses_combo_box_changed)
        self.users_combo_box.currentIndexChanged.connect(self.users_combo_box_changed)

        self.tasks_options_button.clicked.connect(self.open_task_menu)
        self.save_task_button.clicked.connect(self.simple_save_task)

    def create_ui(self):

        self.setMinimumWidth(160)
        self.setObjectName('simple_task_widget')

        self.setStyleSheet('QFrame#simple_task_widget { border-radius: 3px; background-color: rgba(255,255,255,0);}')

        self.create_main_layout()
        self.setAutoFillBackground(True)
        self.create_status_color_line()

    def reset_ui(self):
        self.tasks_sobjects_list = []
        self.parent_sobjects_list = []
        self.current_task_sobject = None
        self.task_data_dict = {}
        self.initial_task_data_dict = {}

        self.statuses_combo_box.setCurrentIndex(0)
        self.users_combo_box.setCurrentIndex(0)

    def get_process(self):
        return self.process

    def is_task_changed(self):
        return True

    def set_something_changed(self):
        self.setStyleSheet('QFrame#simple_task_widget { border-radius: 3px; background-color: rgba(255,255,255,24);}')

        if self.multiple_mode:
            self.show_save_multiple_button()
        else:
            self.show_save_button()

    def set_empty_task(self):
        self.setStyleSheet('QFrame#simple_task_widget { border-radius: 3px; background-color: rgba(255,255,255,0);}')
        self.hide_save_button()

    def statuses_combo_box_changed(self, index):
        self.set_something_changed()

    def users_combo_box_changed(self, index):
        self.set_something_changed()

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(0, 0, 4, 4)
        self.setLayout(self.main_layout)

    def create_status_color_line(self):
        self.process_color_line = QtGui.QFrame(self)
        self.process_color_line.setMaximumSize(QtCore.QSize(2, 32))
        self.process_color_line.setStyleSheet('QFrame { border: 0px; background-color: grey;}')
        self.process_color_line.setFrameShadow(QtGui.QFrame.Plain)
        self.process_color_line.setFrameShape(QtGui.QFrame.VLine)
        self.process_color_line.setLineWidth(2)
        self.process_color_line.setObjectName('status_color_line')
        self.main_layout.addWidget(self.process_color_line, 0, 0, 1, 1)

    def create_process_label(self):

        self.process_label = QtGui.QLabel()
        self.process_label.setText(self.process)

        self.main_layout.addWidget(self.process_label, 0, 1)

    def create_tasks_buttons(self):
        self.tasks_options_button = QtGui.QToolButton()
        self.tasks_options_button.setIcon(gf.get_icon('menu', icons_set='mdi', scale_factor=1))
        self.tasks_options_button.setToolTip('Tasks Options')
        self.tasks_options_button.setMaximumSize(24, 24)
        self.tasks_options_button.setAutoRaise(True)

        self.save_task_button = QtGui.QToolButton()
        self.save_task_button.setToolTip('Save Task')
        self.save_task_button.setMaximumSize(24, 24)
        self.save_task_button.setAutoRaise(True)
        self.save_task_button_opacity = QtGui.QGraphicsOpacityEffect(self.save_task_button)
        self.save_task_button.setGraphicsEffect(self.save_task_button_opacity)
        self.hide_save_button()

        self.main_layout.addWidget(self.save_task_button, 0, 2)
        self.main_layout.addWidget(self.tasks_options_button, 0, 3)

    def hide_save_button(self):
        self.save_task_button_opacity.setOpacity(0)
        self.save_task_button.setEnabled(False)

    def show_save_button(self):
        self.save_task_button_opacity.setOpacity(1)
        self.save_task_button.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        self.save_task_button.setEnabled(True)

    def hide_save_multiple_button(self):
        self.save_task_button_opacity.setOpacity(0)
        self.save_task_button.setEnabled(False)

    def show_save_multiple_button(self):
        self.save_task_button_opacity.setOpacity(1)
        self.save_task_button.setIcon(gf.get_icon('content-save-all', icons_set='mdi', scale_factor=1))
        self.save_task_button.setEnabled(True)

    def open_task_menu(self):
        menu = self.watch_items_menu()
        if menu:
            menu.exec_(Qt4Gui.QCursor.pos())

    def watch_items_menu(self):

        add_task = QtGui.QAction('Add Task', self.tasks_options_button)
        add_task.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1))
        add_task.triggered.connect(self.add_new_task)

        edit_task = QtGui.QAction('Edit Task', self.tasks_options_button)
        edit_task.setIcon(gf.get_icon('square-edit-outline', icons_set='mdi', scale_factor=1))
        edit_task.triggered.connect(self.edit_task)

        delete_task = QtGui.QAction('Delete Task', self.tasks_options_button)
        delete_task.setIcon(gf.get_icon('delete-forever', icons_set='mdi', scale_factor=1))
        delete_task.triggered.connect(self.delete_task)

        # enable_watch = QtGui.QAction('Enable Watch', self.tasks_options_button)
        # enable_watch.setIcon(gf.get_icon('eye'))
        #
        # disable_watch = QtGui.QAction('Disable Watch', self.tasks_options_button)
        # disable_watch.setIcon(gf.get_icon('eye-slash'))

        menu = QtGui.QMenu()

        menu.addAction(add_task)

        if self.tasks_sobjects_list:

            menu.addAction(edit_task)
            menu.addAction(delete_task)
            menu.addSeparator()

            for task_sobject in self.tasks_sobjects_list:
                task_action = QtGui.QAction(u'Task: {0} / {1}'.format(
                    task_sobject.get_value('context'),
                    task_sobject.get_value('assigned')
                ), self.tasks_options_button)

                task_action.setCheckable(True)

                if task_sobject == self.current_task_sobject:
                    task_action.setChecked(True)
                elif task_sobject.get_value('login') == env_inst.get_current_login():
                    task_action.setChecked(True)

                task_action.triggered.connect(partial(self.customize_by_task_sobject, task_sobject))

                menu.addAction(task_action)

        return menu

    def create_statuses_combo(self):
        self.statuses_combo_box = Ui_coloredComboBox()
        self.statuses_combo_box.add_item('--status--', hex_color='#303030')

        self.main_layout.addWidget(self.statuses_combo_box, 1, 1, 1, 3)

    def create_users_combo(self):
        self.users_combo_box = Ui_coloredComboBox()
        self.users_combo_box.add_item('--user--', hex_color='#303030')

        self.main_layout.addWidget(self.users_combo_box, 2, 1, 1, 3)

    def add_tasks_sobjects(self, tasks_sobjects_list=None, parent_sobjects_list=None):
        if tasks_sobjects_list:
            if not self.tasks_sobjects_list:
                self.tasks_sobjects_list = []
            self.tasks_sobjects_list.extend(tasks_sobjects_list)

        if parent_sobjects_list:
            self.parent_sobjects_list = parent_sobjects_list

    def init_with_multiple_tasks(self):
        self.multiple_mode = True

        if self.tasks_sobjects_list:
            self.current_task_sobject = self.tasks_sobjects_list[0]
            self.customize_statuses_combo(self.current_task_sobject)
            self.customize_users_combo(self.current_task_sobject)
            self.customize_process_label()
            self.hide_save_button()
            self.hide_save_multiple_button()

    def set_tasks_sobjects(self, tasks_sobjects_list):

        self.multiple_mode = False

        if tasks_sobjects_list:
            self.tasks_sobjects_list = tasks_sobjects_list

        if self.tasks_sobjects_list:
            self.current_task_sobject = self.tasks_sobjects_list[0]
            self.customize_by_task_sobject(self.current_task_sobject)

        self.hide_save_button()

    def customize_by_task_sobject(self, task_sobject):
        self.current_task_sobject = task_sobject

        if self.current_task_sobject:
            self.customize_statuses_combo(task_sobject)
            self.customize_users_combo(task_sobject)
            self.customize_process_label()

    def create_filler(self):

        self.create_process_label()

        self.create_tasks_buttons()

        self.create_statuses_combo()
        self.fill_statuses_combo()

        self.create_users_combo()
        self.fill_users_combo()

    def get_process_info(self):
        stype = self.parent_sobject.get_stype()
        parent_sobject_pipeline_code = self.parent_sobject.get_pipeline_code()

        current_pipeline = stype.get_pipeline().get(parent_sobject_pipeline_code)
        process_info = current_pipeline.get_process_info(self.process)

        return process_info

    def get_process_label(self):
        process_info = self.get_process_info()

        if process_info:
            process_label = process_info.get('label')
            if process_label:
                return process_label
            else:
                return self.process
        else:
            return self.process

    def fill_statuses_combo(self):
        stype = self.parent_sobject.get_stype()
        parent_sobject_pipeline_code = self.parent_sobject.get_pipeline_code()
        workflow = stype.get_workflow()

        current_pipeline = stype.get_pipeline().get(parent_sobject_pipeline_code)
        process_info = self.get_process_info()

        if process_info:
            process_label = process_info.get('label')
            if process_label:
                self.process_label.setText(process_label)

            process_color = process_info.get('color')
            if not process_color:
                process = current_pipeline.get_pipeline_process(self.process)
                if process:
                    process_color = process.get('color')
            if process_color:
                self.process_color_line.setStyleSheet('QFrame { border: 0px; background-color: %s;}' % process_color)

            task_pipeline_code = process_info.get('task_pipeline')

            # Getting tasks pipeline, if it is not created, we use default builtin pipelines
            if task_pipeline_code:
                task_pipeline = workflow.get_by_pipeline_code('sthpw/task', task_pipeline_code)
            else:
                process_type = process_info.get('type')
                task_pipeline = workflow.get_by_process_node_type('sthpw/task', process_type)

            if task_pipeline:
                for process, value in task_pipeline.pipeline.items():
                    self.statuses_combo_box.add_item(process, hex_color=value.get('color'))

    def customize_statuses_combo(self, task_sobject):

        task_status = task_sobject.get_value('status')
        self.initial_task_data_dict['status'] = task_status
        status_index = self.statuses_combo_box.findText(task_status)
        if status_index != -1:
            self.statuses_combo_box.setCurrentIndex(status_index)

    def fill_users_combo(self):

        current_login = env_inst.get_current_login_object()

        stype = self.parent_sobject.get_stype()
        parent_sobject_pipeline_code = self.parent_sobject.get_pipeline_code()

        current_pipeline = stype.get_pipeline().get(parent_sobject_pipeline_code)
        process_info = current_pipeline.get_process_info(self.process)

        if process_info:
            assigned_login_group_code = process_info.get('assigned_login_group')
            assigned_login_group = current_login.get_login_group(assigned_login_group_code)

            if assigned_login_group:
                group_logins = assigned_login_group.get_logins()
                if group_logins:
                    for i, login in enumerate(group_logins):
                        self.users_combo_box.setItemData(i, login.get_login(), QtCore.Qt.UserRole)
                        self.users_combo_box.add_item(login.get_display_name(), hex_color='#484848')
            else:
                all_logins = env_inst.get_all_logins().values()
                for i, login in enumerate(all_logins):
                    self.users_combo_box.setItemData(i, login.get_login(), QtCore.Qt.UserRole)
                    self.users_combo_box.add_item(login.get_display_name(), hex_color='#484848')

    def customize_users_combo(self, task_sobject):

        task_login = task_sobject.get_value('assigned')
        self.initial_task_data_dict['assigned'] = task_login
        user_index = self.users_combo_box.findData(task_login)
        if user_index != -1:
            self.users_combo_box.setCurrentIndex(user_index+1)

    def customize_process_label(self):
        if self.multiple_mode:
            self.process_label.setText(u'{} ~'.format(self.get_process_label()))
        elif len(self.tasks_sobjects_list) > 0:
            self.process_label.setText(u'{} | {}'.format(self.get_process_label(), len(self.tasks_sobjects_list)))
        else:
            self.process_label.setText(self.get_process_label())

    def get_changed_data(self):

        users_combo_index = self.users_combo_box.currentIndex()
        new_login = self.users_combo_box.itemData(users_combo_index-1, QtCore.Qt.UserRole)
        new_login_text = self.users_combo_box.itemText(users_combo_index)

        status_combo_index = self.statuses_combo_box.currentIndex()
        new_status = self.statuses_combo_box.itemText(status_combo_index)

        if new_login_text == '--user--':
            self.task_data_dict['assigned'] = new_login_text
        elif new_login:
            # we only get data if something changed
            initial_login = self.initial_task_data_dict.get('assigned')
            if initial_login:
                if initial_login != new_login:
                    self.task_data_dict['assigned'] = new_login
            else:
                self.task_data_dict['assigned'] = new_login

        if new_status:
            # we only get data if something changed
            initial_status = self.initial_task_data_dict.get('status')
            if initial_status:
                if initial_status != new_status:
                    self.task_data_dict['status'] = new_status
            else:
                self.task_data_dict['status'] = new_status

        return self.task_data_dict

    def fill_process_label(self, label_text):
        if self.tasks_sobjects_list:
            self.process_label.setText(u'{} | {}'.format(label_text, len(self.tasks_sobjects_list)))
        else:
            self.process_label.setText(u'{}'.format(label_text))

    def add_new_task(self):
        print 'Adding new task'
        from thlib.ui_classes.ui_addsobject_classes import Ui_addTacticSobjectWidget

        tasks_stype = env_inst.get_stype_by_code('sthpw/task')
        parent_stype = self.parent_sobject.get_stype()
        search_key = self.parent_sobject.get_search_key()

        print search_key

        add_sobject = Ui_addTacticSobjectWidget(
            stype=tasks_stype,
            parent_stype=parent_stype,
            # search_key=search_key,
            parent_search_key=search_key,
            # view='edit',
            parent=self,
        )

        add_sobject.show()

        return add_sobject

    def edit_task(self):
        print 'Editing task'
        from thlib.ui_classes.ui_addsobject_classes import Ui_addTacticSobjectWidget

        tasks_stype = env_inst.get_stype_by_code('sthpw/task')
        parent_stype = self.parent_sobject.get_stype()
        search_key = self.current_task_sobject.get_search_key()
        parent_search_key = self.parent_sobject.get_search_key()


        print search_key

        add_sobject = Ui_addTacticSobjectWidget(
            stype=tasks_stype,
            parent_stype=parent_stype,
            search_key=search_key,
            parent_search_key=parent_search_key,
            view='edit',
            parent=self,
        )

        add_sobject.show()

        return add_sobject

    def refresh_tasks_sobjects(self):
        tasks_sobjects, info = self.parent_sobject.get_tasks_sobjects(process=self.process)
        if tasks_sobjects:
            self.set_tasks_sobjects(tasks_sobjects.values())
        else:
            self.reset_ui()
            self.set_empty_task()
            self.customize_process_label()

    def delete_task(self):
        self.current_task_sobject.delete_sobject(include_dependencies=True)
        self.refresh_tasks_sobjects()

    def simple_save_task(self):

        self.hide_save_button()
        changed_data = self.get_changed_data()

        # fetching data to commit
        if changed_data:
            if self.multiple_mode:
                self.commit_multiple_task(changed_data)
            else:
                self.commit_single_task(changed_data)

    def commit_multiple_task(self, changed_data):
        print 'COMMINT MULTIPLE', self.current_task_sobject
        do_commit = False
        data = {}
        for column, val in changed_data.items():
            if val not in ['--user--', '--status--']:
                do_commit = True
                if self.current_task_sobject:
                    self.current_task_sobject.set_value(column, val)
                else:
                    # If no current tasks we create it later
                    data[column] = val
            elif self.initial_task_data_dict.get(column) != val:
                if self.current_task_sobject:
                    do_commit = True
                    self.current_task_sobject.set_value(column, '')

        print do_commit, data
        if do_commit:
            data['process'] = self.process

            # update multiple sobjects
            for task_sobject in self.tasks_sobjects_list:
                print task_sobject.get_search_key()

            # insert new sobjects if it doesn't created earlier
            print data
            for sobject in self.parent_sobjects_list:
                print sobject.get_search_key()



            tc.server_start(project=self.parent_sobject.project.get_code()).insert_multiple(
                'sthpw/task',
                data,
                parent_key=self.parent_sobject.get_search_key(),
                triggers=True
            )

    def commit_single_task(self, changed_data):
        do_commit = False
        data = {}
        for column, val in changed_data.items():
            if val not in ['--user--', '--status--']:
                do_commit = True
                if self.current_task_sobject:
                    self.current_task_sobject.set_value(column, val)
                else:
                    # If no current tasks we create it later
                    data[column] = val
            elif self.initial_task_data_dict.get(column) != val:
                if self.current_task_sobject:
                    do_commit = True
                    self.current_task_sobject.set_value(column, '')
        if do_commit:
            if self.current_task_sobject:
                self.current_task_sobject.commit(triggers=True)
            else:
                data['process'] = self.process
                tc.server_start(project=self.parent_sobject.project.get_code()).insert(
                    'sthpw/task',
                    data,
                    parent_key=self.parent_sobject.get_search_key(),
                    triggers=True
                )
                self.refresh_tasks_sobjects()
        else:
            self.set_empty_task()


class Ui_tasksDockWidget(QtGui.QWidget):
    def __init__(self, project=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.sobject = None
        self.sobjects_list = []
        self.task_widgets_list = []
        self.tasks_sobjects = None
        self.multiple_mode = False

        self.create_ui()
        self.controls_actions()

    def controls_actions(self):
        self.save_button.clicked.connect(self.save_tasks)
        self.refresh_button.clicked.connect(self.refresh_tasks)

    def create_ui(self):

        self.create_main_layout()

        self.create_toolbar()
        self.create_options_toolbar()

        self.create_stretch()

        self.create_scroll_area()

        self.create_no_notes_label()

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def create_toolbar(self):

        self.collapsable_toolbar = Ui_horizontalCollapsableWidget()
        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.setSpacing(0)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.collapsable_toolbar.set_direction('right')
        self.collapsable_toolbar.setLayout(buttons_layout)
        self.collapsable_toolbar.setCollapsed(False)

        self.save_button = QtGui.QToolButton()
        self.save_button.setAutoRaise(True)
        self.save_button.setIcon(gf.get_icon('content-save-all', icons_set='mdi', scale_factor=1))
        self.save_button.setToolTip('Save Current Changes')

        self.refresh_button = QtGui.QToolButton()
        self.refresh_button.setAutoRaise(True)
        self.refresh_button.setIcon(gf.get_icon('refresh', icons_set='mdi', scale_factor=1.3))
        self.refresh_button.setToolTip('Refresh Current Tasks')

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.refresh_button)

        self.main_layout.addWidget(self.collapsable_toolbar, 0, 0, 1, 1)

    def create_options_toolbar(self):

        self.collapsable_options_toolbar = Ui_horizontalCollapsableWidget()
        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.setSpacing(0)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.collapsable_options_toolbar.set_direction('right')
        self.collapsable_options_toolbar.setLayout(buttons_layout)
        self.collapsable_options_toolbar.setCollapsed(True)

        self.auto_save_check_box = QtGui.QCheckBox('Autosave')
        self.auto_save_check_box.setChecked(False)

        self.filter_process_check_box = QtGui.QCheckBox('Filter')
        self.filter_process_check_box.setChecked(False)

        self.process_combo_box = Ui_coloredComboBox()
        self.process_combo_box.setEnabled(False)

        QtCore.QObject.connect(
            self.filter_process_check_box,
            QtCore.SIGNAL("toggled(bool)"),
            self.process_combo_box.setEnabled)

        buttons_layout.addWidget(self.filter_process_check_box)
        buttons_layout.addWidget(self.process_combo_box)
        buttons_layout.addWidget(self.auto_save_check_box)

        self.main_layout.addWidget(self.collapsable_options_toolbar, 0, 1, 1, 1)

    def create_stretch(self):
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.main_layout.addItem(spacerItem, 0, 2, 1, 1)
        self.main_layout.setColumnStretch(2, 1)

    def create_scroll_area(self):
        from thlib.side.flowlayout import FlowLayout

        self.scroll_area_contents = QtGui.QWidget()
        self.scroll_area_contents.setContentsMargins(9, 9, 0, 0)

        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_contents)

        self.scroll_area_layout = FlowLayout(self.scroll_area_contents)

        self.scroll_area_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area_layout.setContentsMargins(9, 9, 0, 0)
        self.scroll_area_layout.setSpacing(9)

        self.main_layout.addWidget(self.scroll_area, 1, 0, 1, 3)

    def create_no_notes_label(self):
        self.no_notes_label = QtGui.QLabel()
        self.no_notes_label.setMinimumSize(0, 0)
        self.no_notes_label.setText('Select Item to See Tasks...')
        self.no_notes_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.scroll_area_layout.addWidget(self.no_notes_label)

    def toggle_no_notes_label(self):
        if self.no_notes_label.isVisible():
            self.no_notes_label.setHidden(True)
        else:
            self.no_notes_label.setHidden(False)

    def save_tasks(self):
        # groupped_tasks_sobjects = tc.group_sobject_by(self.tasks_sobjects, 'process')

        # for process, task_sobjects in groupped_tasks_sobjects.items():
        for task_widget in self.task_widgets_list:
            print task_widget.is_task_changed()
            # if task_widget.get_process() == process:
            #     task_widget.set_tasks_sobjects(task_sobjects)

    def refresh_tasks(self):

        if self.multiple_mode:
            if self.sobjects_list:
                self.task_widgets_list = []
                self.create_filler_tasks()
        elif self.sobject:
            self.task_widgets_list = []
            self.create_filler_tasks()

            self.query_tasks()

    def query_multiple_tasks(self):
        def get_tasks_sobjects_agent():
            return tc.SObject.get_multiple_tasks_sobjects(sobjects_list=self.sobjects_list)

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        get_tasks_sobjects_worker = gf.get_thread_worker(
            get_tasks_sobjects_agent,
            env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=self.fill_multiple_tasks,
            error_func=gf.error_handle,
        )
        get_tasks_sobjects_worker.try_start()

    def query_tasks(self):

        def get_tasks_sobjects_agent():
            return self.sobject.get_tasks_sobjects()

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        get_tasks_sobjects_worker = gf.get_thread_worker(
            get_tasks_sobjects_agent,
            env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=self.fill_tasks,
            error_func=gf.error_handle,
        )
        get_tasks_sobjects_worker.try_start()

    def create_filler_tasks(self):
        self.clear_scroll_area()
        self.process_combo_box.clear()

        stype = self.sobject.get_stype()
        # getting all possible processes here
        processes = []
        pipeline_code = self.sobject.get_pipeline_code()
        current_pipeline = None
        if pipeline_code and stype.pipeline:
            current_pipeline = stype.pipeline.get(pipeline_code)
            if current_pipeline:
                processes = current_pipeline.pipeline.keys()

        # if self.ignore_dict:
        #     if self.ignore_dict.get('show_builtins'):
        #         show_all = True
        #         for builtin in ['icon', 'attachment', 'publish']:
        #             if builtin not in self.ignore_dict['builtins']:
        #                 processes.append(builtin)
        #                 show_all = False
        #         if show_all:
        #             processes.extend(['icon', 'attachment', 'publish'])

        for process in processes:
            process_info = current_pipeline.get_process_info(process)

            ignored = False

            # Ignoring PROGRESS, ACTION, CONDITION processes
            # TODO Special case for progress, we should fetch completeness of progress node as in tactic.
            if process_info.get('type') in ['action', 'condition', 'dependency', 'progress']:
                ignored = True

            if not ignored:
                # Filling process combo box
                if process_info:
                    process_color = process_info.get('color')
                    if not process_color:
                        process_object = current_pipeline.get_pipeline_process(process)
                        if process_object:
                            process_color = process_object.get('color')

                    process_label = process_info.get('label')
                    if process_label:
                        if process_color:
                            self.process_combo_box.add_item(process_label, hex_color=process_color, item_data=process)
                        else:
                            self.process_combo_box.add_item(process_label, hex_color='#484848', item_data=process)
                    else:
                        self.process_combo_box.add_item(process, hex_color='#484848', item_data=process)
                else:
                    self.process_combo_box.add_item(process, hex_color='#484848', item_data=process)

                # creating and adding Simple task widgets
                task_widget = Ui_simpleTaskWidget(process, self.sobject)
                self.task_widgets_list.append(task_widget)
                self.scroll_area_layout.addWidget(task_widget)

    def clear_scroll_area(self):
        self.scroll_area_layout.clear_items()

    def fill_multiple_tasks(self, query_result):
        if query_result:
            for code, tasks_sobjects in query_result.items():
                groupped_tasks_sobjects = tc.group_sobject_by(tasks_sobjects, 'process')
                for task_widget in self.task_widgets_list:
                    task_widget.add_tasks_sobjects(groupped_tasks_sobjects.get(task_widget.get_process()), self.sobjects_list)

            for task_widget in self.task_widgets_list:
                task_widget.init_with_multiple_tasks()

    def fill_tasks(self, query_result):

        self.tasks_sobjects, info = query_result

        self.create_filler_tasks()

        groupped_tasks_sobjects = tc.group_sobject_by(self.tasks_sobjects, 'process')

        for process, task_sobjects in groupped_tasks_sobjects.items():
            for task_widget in self.task_widgets_list:
                if task_widget.get_process() == process:
                    task_widget.set_tasks_sobjects(task_sobjects)

        self.set_dock_title(u'Tasks For: {0}'.format(self.sobject.get_title()))

    def bring_dock_widget_up(self):

        related_tasks_dock = env_inst.get_check_tree(
            self.project.get_code(), 'checkin_out_instanced_widgets', 'tasks_dock')

        dock_widget = related_tasks_dock.parent()
        if dock_widget:
            if isinstance(dock_widget, QtGui.QDockWidget):
                dock_widget.setHidden(False)
                dock_widget.raise_()

    def set_dock_title(self, title_string):

        related_tasks_dock = env_inst.get_check_tree(
            self.project.get_code(), 'checkin_out_instanced_widgets', 'tasks_dock')

        dock_widget = related_tasks_dock.parent()
        if dock_widget:
            if isinstance(dock_widget, QtGui.QDockWidget):
                dock_widget.setWindowTitle(title_string)

    def set_sobject(self, sobject, force=False):

        self.multiple_mode = False

        # Do something only if widget is visible to user
        if force:
            self.task_widgets_list = []
            self.sobject = sobject
            self.query_tasks()
        elif not self.visibleRegion().isEmpty():
            self.task_widgets_list = []
            self.sobject = sobject
            self.query_tasks()

    def set_sobjects(self, sobjects_list, force=False):

        self.multiple_mode = True

        # Do something only if widget is visible to user
        if force:
            self.set_dock_title(u'Multiple Tasks Editing Mode for: {0} items'.format(len(sobjects_list)))
            self.task_widgets_list = []
            self.sobjects_list = sobjects_list
            self.create_filler_tasks()
            self.query_multiple_tasks()
        elif not self.visibleRegion().isEmpty():
            self.set_dock_title(u'Multiple Tasks Editing Mode for: {0} items'.format(len(sobjects_list)))
            self.task_widgets_list = []
            self.sobjects_list = sobjects_list
            self.create_filler_tasks()
            self.query_multiple_tasks()


# class Ui_tasksWidgetMain(QtGui.QMainWindow):
#     def __init__(self, sobject, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#
#         self.task_widget = Ui_tasksWidget(sobject, self)
#         self.setWindowTitle('Tasks for: ' + sobject.get_title())
#         self.setCentralWidget(self.task_widget)
#         self.setContentsMargins(0, 4, 0, 0)
#         self.statusBar()
#
#     def closeEvent(self, event):
#         print('Save Ui_tasksWidgetMain')
#         self.task_widget.close()
#         self.task_widget.deleteLater()
#         self.close()
#         self.deleteLater()
#         event.accept()
#
#
# class Ui_tasksWidget(QtGui.QWidget, ui_tasks.Ui_tasks):
#     def __init__(self, sobject, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#
#         self.setupUi(self)
#         self.dock_widget = None
#
#         self.sobject = sobject
#
#         # Query to get all task for current sobject
#         self.sobject.get_tasks()
#
#         self.users = tc.users_query()
#         self.priority = tc.task_priority_query(self.sobject.info['__search_key__'])
#         self.task_process = tc.task_process_query(self.sobject.info['__search_key__'])
#         # print(self.task_process)
#
#         self.initial_fill_info()
#
#         self.ui_richedit = richedit_widget.Ui_richeditWidget(self.descriptionTextEdit)
#         self.editorLayout.addWidget(self.ui_richedit)
#
#         self.add_process_items()
#
#         self.ui_actions()
#
#     def ui_actions(self):
#         self.processTreeWidget.clicked.connect(self.fill_tasks_info)
#         self.showNotesButton.clicked.connect(self.create_notes_widget)
#         self.priorityComboBox.currentIndexChanged.connect(self.priority_combo_color)
#         self.statusComboBox.currentIndexChanged.connect(self.status_combo_color)
#
#         self.skeyLineEdit_actions()
#
#     def click_on_skeyLineEdit(self, event):
#         self.skeyLineEdit.selectAll()
#
#     def skeyLineEdit_actions(self):
#         self.skeyLineEdit.mousePressEvent = self.click_on_skeyLineEdit
#         self.skeyLineEdit.returnPressed.connect(lambda: tc.parce_skey(self.skeyLineEdit.text()))
#
#     def fill_status(self):
#         status_combo_box = self.statusComboBox.model()
#         for value, color in zip(self.task_process['process'], self.task_process['color']):
#             item = Qt4Gui.QStandardItem(u'{0}'.format(value))
#             sc = gf.hex_to_rgb(color, tuple=True)
#             sc_item = Qt4Gui.QColor(sc[0], sc[1], sc[2], 128)
#             item.setBackground(sc_item)
#             item.setData(sc_item, 1)
#             item.setData(value, 2)
#             status_combo_box.appendRow(item)
#
#     def status_combo_color(self):
#         item_color = self.statusComboBox.itemData(self.statusComboBox.currentIndex(), 1)
#         if item_color:
#             pc = item_color.toTuple()
#             self.statusComboBox.setStyleSheet('QComboBox {background: ' +
#                                               'rgba({0}, {1}, {2}, {3})'.format(pc[0], pc[1], pc[2], 192) +
#                                               ';}')
#         else:
#             self.priorityComboBox.setStyleSheet('')
#
#     def fill_priority(self):
#         # priority combo box with colors
#         priority_combo_box = self.priorityComboBox.model()
#         step = len(self.priority) - 1
#         int_range = 255 / step * step
#         r = range(0, int_range, 255 / step)
#         g = range(0, int_range, 255 / step)
#         b = 0
#         a = 64
#         r.reverse()
#         pc = []
#         for i in range(step):
#             color = r[i], g[i], b, a
#             pc.append(color)
#         for i, (label, value) in enumerate(self.priority):
#             item = Qt4Gui.QStandardItem(u'{0}, {1}'.format(label, value))
#             color = Qt4Gui.QColor(pc[i - 1][0], pc[i - 1][1], pc[i - 1][2], pc[i - 1][3])
#             if i > 0:
#                 item.setBackground(color)
#                 item.setData(color, 1)
#             priority_combo_box.appendRow(item)
#
#     def priority_combo_color(self):
#         item_color = self.priorityComboBox.itemData(self.priorityComboBox.currentIndex(), 1)
#         if item_color:
#             pc = item_color.toTuple()
#             self.priorityComboBox.setStyleSheet('QComboBox {background: ' +
#                                                 'rgba({0}, {1}, {2}, {3})'.format(pc[0], pc[1], pc[2], 192) +
#                                                 ';}')
#         else:
#             self.priorityComboBox.setStyleSheet('')
#
#     def initial_fill_info(self):
#
#         self.fill_priority()
#         self.fill_status()
#         current_datetime = QtCore.QDateTime.currentDateTime()
#         self.startedDateTimeEdit.setDateTime(current_datetime)
#         self.endDateTimeEdit.setDateTime(current_datetime)
#
#         for user in self.users.itervalues():
#             print user
#             # self.assignedToComboBox.addItem(u'{last_name} {first_name}, {login}'.format(**user).decode('utf-8'))
#             # self.superviserComboBox.addItem(u'{last_name} {first_name}, {login}'.format(**user).decode('utf-8'))
#
#     def fill_tasks_info(self):
#         current_item = self.processTreeWidget.currentItem().data(0, QtCore.Qt.UserRole)
#         if current_item:
#             self.descriptionTextEdit.setText(current_item.info['description'])
#             for i, user in enumerate(self.users.itervalues()):
#
#                 if current_item.info['assigned'] == user['login']:
#                     self.assignedToComboBox.setCurrentIndex(i)
#                 if not current_item.info['assigned']:
#                     self.assignedToComboBox.setCurrentIndex(0)
#                     self.assignedToComboBox.setEditText('Not Assigned')
#
#                 if current_item.info['supervisor'] == user['login']:
#                     self.superviserComboBox.setCurrentIndex(i)
#                 if not current_item.info['supervisor']:
#                     self.superviserComboBox.setCurrentIndex(0)
#                     self.superviserComboBox.setEditText('Not Assigned')
#
#             if current_item.info['priority']:
#                 self.priorityComboBox.setCurrentIndex(int(current_item.info['priority']))
#             else:
#                 self.priorityComboBox.setCurrentIndex(0)
#
#             if current_item.info['status']:
#                 for i, status in enumerate(self.task_process['process']):
#                     if current_item.info['status'] == status:
#                         self.statusComboBox.setCurrentIndex(i)
#
#             start_date = QtCore.QDateTime.fromString(current_item.info['bid_start_date'], 'yyyy-MM-dd HH:mm:ss')
#             end_date = QtCore.QDateTime.fromString(current_item.info['bid_end_date'], 'yyyy-MM-dd HH:mm:ss')
#             self.startedDateTimeEdit.setDateTime(start_date)
#             self.endDateTimeEdit.setDateTime(end_date)
#             self.skeyLineEdit.setText('skey://' + current_item.info['__search_key__'])
#             self.contextLineEdit.setText(current_item.info['context'])
#             if self.dock_widget:
#                 self.ui_notes.task_item = current_item
#                 self.ui_notes.fill_notes()
#
#             show_notes_text = '{0} ({1})'.format('Show Task Notes', str(10))
#             print(show_notes_text)
#             self.showNotesButton.setText(show_notes_text)
#
#     def add_process_items(self):
#         # print(self.sobject.tasks)
#         # print(self.sobject.all_process)
#         # Top level, process of tasks
#         for process in self.sobject.all_process:
#
#             self.top_item = QtGui.QTreeWidgetItem()
#             self.top_item.setText(0, process)
#             self.top_item_widget = task_item_widget.Ui_taskItemWidget(self.top_item, self)
#             self.processTreeWidget.addTopLevelItem(self.top_item)
#             self.processTreeWidget.setItemWidget(self.top_item, 0, self.top_item_widget)
#
#             # Second level, contexts of tasks
#             if self.sobject.tasks.get(process):
#                 for context, task in self.sobject.tasks[process].contexts.items():
#                     self.child_item = QtGui.QTreeWidgetItem()
#                     self.child_item.setText(0, context)
#                     self.top_item.addChild(self.child_item)
#                     self.top_item.setExpanded(True)
#
#                     # Third level, Tasks items
#                     for sub, item in self.sobject.tasks[process].contexts[context].items.items():
#                         self.sub_item = QtGui.QTreeWidgetItem()
#                         self.sub_item.setData(0, QtCore.Qt.UserRole, item)
#                         # self.sub_item.setText(0, sub)
#                         self.sub_item_widget = task_item_widget.Ui_taskItemDetailWidget(self)
#                         self.child_item.addChild(self.sub_item)
#                         self.processTreeWidget.setItemWidget(self.sub_item, 0, self.sub_item_widget)
#                         # self.child_item.setExpanded(True)
#                         # print(context)
#                         # print(sub)
#                         # print(item)
#
#     def create_notes_widget(self):
#         current_item = self.processTreeWidget.currentItem().data(0, QtCore.Qt.UserRole)
#         try:
#             self.dock_widget.show()
#             self.dock_widget.raise_()
#         except:
#             self.dock_widget = QtGui.QDockWidget()
#             self.dock_widget.setObjectName('notes_dock')
#             self.dock_widget.setWindowTitle('Notes')
#             # self.dock_widget.setMinimumWidth(500)
#             self.ui_notes = notes_widget.Ui_notesWidget()
#             if current_item:
#                 self.ui_notes.task_item = current_item
#                 self.ui_notes.fill_notes()
#             self.dock_widget.setWidget(self.ui_notes)
#             self.parent().addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
#             self.dock_widget.show()
#             self.dock_widget.raise_()
#
#             self.ui_notes.conversationScrollArea.verticalScrollBar().setValue(
#                 self.ui_notes.conversationScrollArea.verticalScrollBar().maximum())
#
#     def closeEvent(self, event):
#         try:
#             self.dock_widget.close()
#             self.dock_widget.deleteLater()
#             self.ui_notes.close()
#         except:
#             pass
#         # self.ui_notes.close()
#         print('Save Ui_tasksWidget')
#         event.accept()
