# ui_checkin_out_tabs_classes.py
# Check In Tabs interface

import os
import shutil
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore
from thlib.environment import env_inst, env_tactic, cfg_controls, env_read_config, env_write_config, dl
import thlib.global_functions as gf
import thlib.tactic_classes as tc
import ui_checkin_out_classes as checkin_out
import thlib.ui.misc.ui_watch_folders as ui_watch_folders
from thlib.ui_classes.ui_commit_queue_classes import Ui_commitQueueWidget
from thlib.ui_classes.ui_repo_sync_queue_classes import Ui_repoSyncQueueWidget
from thlib.ui_classes.ui_watch_folder_classes import Ui_projectWatchFoldersWidget
from thlib.ui_classes.ui_custom_qwidgets import Ui_extendedTabBarWidget, Ui_extendedTreeWidget



class Ui_checkInOutTabWidget(QtGui.QWidget):
    def __init__(self, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project

        env_inst.set_control_tab(self.project.get_code(), 'checkin_out', self)

        self.create_ui()

        self.all_search_tabs = []
        self.current_tab_idx = 0

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()

        self.is_created = False
        self.stypes_tree_visible = False

        self.tab_bar_customization()

    def create_ui(self):

        self.setObjectName('sobject_tab_widget')

        self.create_main_layout()
        self.create_stypes_tree_widget()
        self.create_stypes_tab_widget()

        self.maint_layout.setStretch(1, 1)

    def init_ui(self):
        if self.project.stypes:
            self.is_created = True

            self.add_items_to_stypes_tree()
            self.readSettings()

            self.fill_stypes_tab_widget()

            self.controls_actions()

            self.create_watch_folders_ui()
            self.create_commit_queue_ui()
            self.create_repo_sync_queue_ui()

    def controls_actions(self):
        self.hamburger_tab_button.clicked.connect(self.hamburger_button_click)

        self.stypes_tree_widget.itemClicked.connect(self.stypes_tree_item_click)
        self.stypes_tree_widget.itemChanged.connect(self.stypes_tree_item_change)

        # self.stypes_tab_widget.mousePressEvent = self.sobj_tab_middle_mouse_event
        self.stypes_tab_widget.middle_mouse_pressed.connect(self.middle_mouse_press)

    def create_main_layout(self):
        self.maint_layout = QtGui.QHBoxLayout(self)
        self.maint_layout.setSpacing(0)
        self.maint_layout.setContentsMargins(0, 0, 0, 0)
        self.maint_layout.setObjectName('maint_layout')

    def create_stypes_tree_widget(self):
        self.stypes_tree_widget = Ui_extendedTreeWidget(self)
        self.stypes_tree_widget.setMaximumSize(QtCore.QSize(0, 16777215))
        self.stypes_tree_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.stypes_tree_widget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.stypes_tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.stypes_tree_widget.setRootIsDecorated(False)
        self.stypes_tree_widget.setAnimated(True)
        self.stypes_tree_widget.setHeaderHidden(True)
        self.stypes_tree_widget.setObjectName('stypes_tree_widget')

        self.maint_layout.addWidget(self.stypes_tree_widget)

    def create_stypes_tab_widget(self):
        self.stypes_tab_widget = Ui_extendedTabBarWidget(self)

        self.stypes_tab_widget.setMovable(True)
        self.stypes_tab_widget.setObjectName('stypes_tab_widget')
        self.stypes_tab_widget.customize_ui()
        self.stypes_tab_widget.set_corner_offset(26)

        self.maint_layout.addWidget(self.stypes_tab_widget)

    # def sobj_tab_middle_mouse_event(self, event):
    #     if event.button() == QtCore.Qt.MouseButton.MiddleButton:
    #         pos = event.pos()
    #         # This offset is because hamburger button on the left
    #         tab_pos = self.stypes_tab_widget.tabBar().tabAt(QtCore.QPoint(pos.x() - 26, pos.y()))
    #         if tab_pos != -1:
    #             widget = self.stypes_tab_widget.widget(tab_pos)
    #             tab = self.get_stype_tab_by_widget(widget)
    #             self.toggle_stype_tab(tab=tab, hide=True)
    #             tree_item = self.get_tree_item_by_code(tab.stype.get_code())
    #             if tree_item:
    #                 tree_item.setCheckState(0, QtCore.Qt.Unchecked)
    #
    #     event.accept()

    def middle_mouse_press(self, tab_pos):
        widget = self.stypes_tab_widget.widget(tab_pos)
        tab = self.get_stype_tab_by_widget(widget)
        self.toggle_stype_tab(tab=tab, hide=True)
        tree_item = self.get_tree_item_by_code(tab.stype.get_code())
        if tree_item:
            tree_item.setCheckState(0, QtCore.Qt.Unchecked)

    def stypes_tree_item_click(self, item):
        item_data = item.data(0, QtCore.Qt.UserRole)
        if item_data:
            self.raise_stype_tab(code=item_data.get('code'))

    def stypes_tree_item_change(self, item):
        if item.childCount() > 0:
            for i in range(item.childCount()):
                if item.checkState(0) == QtCore.Qt.CheckState.Unchecked:
                    item.child(i).setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.child(i).setCheckState(0, QtCore.Qt.Checked)
                self.toggle_tree_item(item.child(i))
        else:
            self.toggle_tree_item(item)

    def toggle_tree_item(self, item):
        item_data = item.data(0, QtCore.Qt.UserRole)
        if item_data:
            if item.checkState(0):
                self.toggle_stype_tab(code=item_data.get('code'), hide=False)
            else:
                self.toggle_stype_tab(code=item_data.get('code'), hide=True)

        # saving changes to config
        self.save_ignore_stypes_list()

    def get_stype_tab_by_widget(self, widget):
        for tab in self.all_search_tabs:
            if tab == widget:
                return tab

    def get_stype_tab_by_code(self, code):
        for tab in self.all_search_tabs:
            if tab.get_tab_code() == code:
                return tab

    def get_tree_item_by_code(self, code):

        for i in range(self.stypes_tree_widget.topLevelItemCount()):
            top = self.stypes_tree_widget.topLevelItem(i)
            for j in range(top.childCount()):
                child = top.child(j)
                item_data = child.data(0, QtCore.Qt.UserRole)
                if item_data:
                    if item_data.get('code') == code:
                        return child

    def raise_stype_tab(self, code=None, tab=None):
        if code:
            tab = self.get_stype_tab_by_code(code)
        if tab:
            idx = self.stypes_tab_widget.indexOf(tab)
            self.stypes_tab_widget.setCurrentIndex(idx)

    def toggle_stype_tab(self, code=None, tab=None, hide=False):

        if code:
            tab = self.get_stype_tab_by_code(code)
        if tab:
            idx = self.stypes_tab_widget.indexOf(tab)
            if hide:
                self.stypes_tab_widget.removeTab(idx)
                self.set_ignore_stypes_list(code, hide=True)
            else:
                self.stypes_tab_widget.addTab(tab, '')

                self.set_ignore_stypes_list(code, hide=False)
                self.stypes_tab_widget.tabBar().setTabButton(self.stypes_tab_widget.count()-1, QtGui.QTabBar.LeftSide, tab.get_tab_label())

    def apply_current_view_to_all(self):
        current_settings = None
        current_tab = self.get_current_tab_widget()
        if current_tab:
            current_settings = current_tab.get_settings_dict()

        if current_settings:
            for tab in self.all_search_tabs:
                tab.set_settings_from_dict(current_settings, apply_checkin_options=False, apply_search_options=False)

    def fast_save(self, **kargs):
        current_tab = self.get_current_tab_widget()

        current_tab.fast_save(**kargs)

    def get_current_tab_widget(self):
        current_widget = self.stypes_tab_widget.currentWidget()
        for tab in self.all_search_tabs:
            if current_widget == tab:
                return tab

    def tab_bar_customization(self):
        self.hamburger_tab_button = QtGui.QToolButton()
        self.hamburger_tab_button.setAutoRaise(True)
        self.hamburger_tab_button.setMinimumWidth(24)
        self.hamburger_tab_button.setMinimumHeight(24)
        self.animation_close = QtCore.QPropertyAnimation(self.stypes_tree_widget, "maximumWidth", self)
        self.animation_open = QtCore.QPropertyAnimation(self.stypes_tree_widget, "maximumWidth", self)
        self.hamburger_tab_button.setIcon(gf.get_icon('menu', icons_set='mdi', scale_factor=1.2))

        self.stypes_tab_widget.add_left_corner_widget(self.hamburger_tab_button)

    def hamburger_button_click(self):
        content_width = self.stypes_tree_widget.sizeHintForColumn(0) + 40

        if self.stypes_tree_visible:
            self.animation_close.setDuration(200)
            self.animation_close.setStartValue(content_width)
            self.animation_close.setEndValue(0)
            self.animation_close.setEasingCurve(QtCore.QEasingCurve.OutSine)
            self.animation_close.start()
            self.stypes_tree_visible = False
        else:
            self.animation_open.setDuration(200)
            self.animation_open.setStartValue(0)
            self.animation_open.setEndValue(content_width)
            self.animation_open.setEasingCurve(QtCore.QEasingCurve.InSine)
            self.animation_open.start()

            self.stypes_tree_visible = True

    def add_items_to_stypes_tree(self):
        exclude_list = self.get_ignore_stypes_list()
        self.stypes_tree_widget.clear()

        all_stypes = []

        for stype in env_inst.projects[self.project.get_code()].stypes.itervalues():
            all_stypes.append(stype.info)

        grouped = gf.group_dict_by(all_stypes, 'type')

        for type_name, value in grouped.items():
            top_item = QtGui.QTreeWidgetItem()

            if not type_name:
                type_name = 'No Category'
            top_item.setText(0, type_name.capitalize())
            top_item.setCheckState(0, QtCore.Qt.Checked)
            self.stypes_tree_widget.addTopLevelItem(top_item)
            for item in value:
                child_item = QtGui.QTreeWidgetItem()

                stype = env_inst.projects[self.project.get_code()].stypes.get(item.get('code'))

                item_code = stype.get_code()
                child_item.setText(0, stype.get_pretty_name())
                child_item.setText(1, item_code)
                child_item.setData(0, QtCore.Qt.UserRole, item)
                child_item.setCheckState(0, QtCore.Qt.Checked)
                if exclude_list:
                    if item_code in exclude_list:
                        child_item.setCheckState(0, QtCore.Qt.Unchecked)
                top_item.addChild(child_item)

            top_item.setExpanded(True)

    def get_ignore_stypes_list(self):
        ignore_tabs_list = []
        if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.project.get_code()):
            if not gf.get_value_from_config(self.checkin_out_config, 'processTabsFilterGroupBox'):
                ignore_tabs_list = []
            else:
                ignore_tabs_list = self.checkin_out_config_projects[self.project.get_code()]['stypes_list']
                if not ignore_tabs_list:
                    ignore_tabs_list = []

        return ignore_tabs_list

    def set_ignore_stypes_list(self, stype_code, hide=False):

        self.init_stypes_config()

        # TODO this code will reset all previous projects states
        if not self.checkin_out_config_projects.get(self.project.get_code()):
            self.init_stypes_config(True)

        if self.checkin_out_config_projects:
            if not self.checkin_out_config_projects[self.project.get_code()]['stypes_list']:
                stypes_list = []
            else:
                stypes_list = self.checkin_out_config_projects[self.project.get_code()]['stypes_list']

            if hide:
                if stype_code not in stypes_list:
                    stypes_list.append(stype_code)
            else:
                if stype_code in stypes_list:
                    stypes_list.remove(stype_code)

            self.checkin_out_config_projects[self.project.get_code()]['stypes_list'] = stypes_list

    def init_stypes_config(self, force=False):
        if not self.checkin_out_config_projects or force:
            from thlib.ui_classes.ui_conf_classes import Ui_checkinOutPageWidget
            self.checkinOutPageWidget = Ui_checkinOutPageWidget(self)

            self.checkinOutPageWidget.processTabsFilterGroupBox.setChecked(True)
            self.checkinOutPageWidget.init_per_projects_config_dict()

            self.checkinOutPageWidget.collect_defaults(apply_values=True)
            self.checkinOutPageWidget.save_config()

            self.checkin_out_config_projects = self.checkinOutPageWidget.page_init_projects

    def save_ignore_stypes_list(self):
        self.init_stypes_config()

        if self.checkin_out_config_projects:
            cfg_controls.set_checkin_out_projects(self.checkin_out_config_projects)

    def fill_stypes_tab_widget(self):

        ignore_tabs_list = self.get_ignore_stypes_list()

        # we creating all Stype Widgets, so we can access them if we need in all_search_tabs
        for stype in self.project.stypes.values():
            tab = checkin_out.Ui_checkInOutWidget(stype, self.project)
            tab.setParent(self)
            self.all_search_tabs.append(tab)
            # but only adding currenly visible tabs
            if tab.stype.get_code() not in ignore_tabs_list:
                self.stypes_tab_widget.add_tab(tab, tab.get_tab_label())

        self.stypes_tab_widget.setCurrentIndex(self.current_tab_idx)

    def create_watch_folders_ui(self):
        env_inst.watch_folders[self.project.get_code()] = Ui_projectWatchFoldersWidget(
            parent=self,
            project=self.project)

    def create_commit_queue_ui(self):
        env_inst.commit_queue[self.project.get_code()] = Ui_commitQueueWidget(
            parent=self,
            project=self.project)

    def create_repo_sync_queue_ui(self):
        env_inst.ui_repo_sync_queue = Ui_repoSyncQueueWidget(parent=self)

    def set_settings_from_dict(self, settings_dict):

        if not settings_dict:
            settings_dict = {
                'stypes_tree_visible': 0,
                'stypes_tab_widget_currentIndex': 0
            }

        if bool(int(settings_dict.get('stypes_tree_visible'))):
            self.hamburger_button_click()

        if settings_dict.get('stypes_tab_widget_currentIndex'):
            self.current_tab_idx = int(settings_dict['stypes_tab_widget_currentIndex'])

    def get_settings_dict(self):
        settings_dict = {
            'stypes_tree_visible': int(self.stypes_tree_visible),
            'stypes_tab_widget_currentIndex': int(self.stypes_tab_widget.currentIndex()),
        }

        return settings_dict

    def readSettings(self):
        """
        Reading Settings
        """

        group_path = 'ui_main/{0}/{1}'.format(
                self.project.get_type(),
                self.project.get_code()
            )

        self.set_settings_from_dict(
            env_read_config(
                filename='ui_checkin_out_tabs',
                unique_id=group_path,
                long_abs_path=True
            )
        )

    def writeSettings(self):
        """
        Writing Settings
        """
        group_path = 'ui_main/{0}/{1}'.format(
            self.project.get_type(),
            self.project.get_code(),
        )

        env_write_config(
            self.get_settings_dict(),
            filename='ui_checkin_out_tabs',
            unique_id=group_path,
            long_abs_path=True
        )

    def showEvent(self, event):
        if not self.is_created:
            self.init_ui()
        event.accept()

    def closeEvent(self, event):
        self.writeSettings()

        for tab in self.all_search_tabs:
            tab.close()
            tab.deleteLater()

        self.all_search_tabs = []
        event.accept()
