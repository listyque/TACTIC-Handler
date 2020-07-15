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
import thlib.ui_classes.ui_checkin_out_classes as checkin_out
import thlib.ui.misc.ui_watch_folders as ui_watch_folders
from thlib.ui_classes.ui_commit_queue_classes import Ui_commitQueueWidget
from thlib.ui_classes.ui_watch_folder_classes import Ui_projectWatchFoldersWidget
from thlib.ui_classes.ui_custom_qwidgets import Ui_extendedTabBarWidget, Ui_extendedLeftTabBarWidget, Ui_extendedTreeWidget, StyledToolButton, Ui_sideBarWidget


class Ui_tacticSidebarWidget(QtGui.QWidget):
    clicked = QtCore.Signal(object)
    def __init__(self, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()

        self.create_ui()

    def create_ui(self):
        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self.tree_widget = Ui_extendedTreeWidget(self)
        self.tree_widget.setMaximumSize(QtCore.QSize(0, 16777215))
        self.tree_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tree_widget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tree_widget.setIndentation(0)
        self.tree_widget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tree_widget.setTabKeyNavigation(True)
        self.tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tree_widget.setAllColumnsShowFocus(True)
        self.tree_widget.setRootIsDecorated(False)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setExpandsOnDoubleClick(False)
        self.tree_widget.setObjectName('sidebar_widget')
        self.tree_widget.setMinimumHeight(400)
        self.tree_widget.setMinimumWidth(250)
        self.tree_widget.setFocusPolicy(QtCore.Qt.NoFocus)

        self.tree_widget.setStyleSheet(gf.get_qtreeview_style(True))

        self.main_layout.addWidget(self.tree_widget)

        self.controls_actions()

    def controls_actions(self):

        self.tree_widget.itemClicked.connect(self.tree_widget_item_click)

    def tree_widget_item_click(self, item):

        item_widget = self.tree_widget.itemWidget(item, 0)
        self.clicked.emit(item_widget)

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

    def initial_fill(self):

        self.tree_widget.clear()

        sidebar = self.project.get_sidebar()

        if sidebar.has_definition():

            # making shure if there is *special TH* definition
            project_definition = sidebar.get_definition(bs=True)
            tactic_handler_definition = sidebar.get_definition('tactic_handler')

            if not tactic_handler_definition:
                tactic_handler_definition = sidebar.get_definition('project_view')

            tactic_handler_sidebar = []
            for th_def in tactic_handler_definition:
                th_def_name = th_def['name']
                for prj_def in project_definition:
                    if prj_def['name'] == th_def_name:
                        tactic_handler_sidebar.append(prj_def)

            for sidebar_item in tactic_handler_sidebar:

                stype_code = None
                view_definition = None
                sub_definitions = []
                layout = 'default'

                if sidebar_item.search_type:
                    stype_code = sidebar_item.search_type.string

                if sidebar_item.layout:
                    layout = sidebar_item.layout.string

                if sidebar_item.view:
                    view_definition = sidebar.get_definition(sidebar_item.view.string)

                    for sub_def in view_definition:
                        sub_def_name = sub_def['name']

                        for sub_prj_def in project_definition:
                            if sub_prj_def['name'] == sub_def_name:
                                sub_definitions.append(sub_prj_def)

                if stype_code and stype_code.startswith('sthpw'):
                    stype = env_inst.get_stype_by_code(stype_code)
                else:
                    stype = self.project.stypes.get(stype_code)

                item_info = {
                    'title': sidebar_item.get('title'),
                    'name': sidebar_item.get('name'),
                    'display_class': sidebar_item.display.get('class'),
                    'search_type': stype_code,
                    'layout': layout,
                    'view_definition': view_definition,
                    'sub_definitions': sub_definitions,
                    'item': sidebar_item,
                }

                gf.add_sidebar_item(
                    tree_widget=self.tree_widget,
                    stype=stype,
                    project=self.project,
                    item_info=item_info,
                )
                self.tree_widget.resizeColumnToContents(0)


class Ui_checkInOutTabWidget(QtGui.QWidget):
    def __init__(self, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project

        env_inst.set_control_tab(self.project.get_code(), 'checkin_out', self)

        self.create_overlay_layout()
        self.create_ui()

        self.all_search_tabs = []
        self.current_tab_idx = 0

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()

        self.is_created = False
        self.overlay_visible = False

    def create_ui(self):

        self.setObjectName('sobject_tab_widget')

        self.create_main_layout()
        self.create_stypes_tab_widget()

        self.create_left_sidebar_widget()

    def init_ui(self):
        if self.project.stypes:
            self.is_created = True

            self.readSettings()

            self.fill_tactic_sidebar_widget()

            self.fill_stypes_tab_widget()

            self.controls_actions()

            self.create_watch_folders_ui()
            self.create_commit_queue_ui()

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
        self.overlay_visible = True

        self.overlay_layout_widget.raise_()
        self.overlay_layout_widget.show()

        self.sidebar_widget.open_sidebar()

    def hide_overlay(self):
        self.overlay_visible = False

        self.sidebar_widget.close_sidebar()

    def hide_overlay_at_hiding(self):
        self.overlay_layout_widget.lower()
        self.overlay_layout_widget.hide()

    def controls_actions(self):

        self.sidebar_widget.clicked.connect(self.hide_overlay)
        self.sidebar_widget.hidden.connect(self.hide_overlay_at_hiding)

        self.tactic_sidebar_widget.clicked.connect(self.tactic_sidebar_item_click)

        self.stypes_tab_widget.middle_mouse_pressed.connect(self.middle_mouse_press)

    def create_main_layout(self):
        self.main_layout = QtGui.QHBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setObjectName('maint_layout')

    def create_left_sidebar_widget(self):

        self.sidebar_widget = Ui_sideBarWidget(parent=self, underlayer_widget=self.stypes_tab_widget)

        self.tactic_sidebar_widget = Ui_tacticSidebarWidget(self.project)

        self.sidebar_widget.add_sidebar_widget(self.tactic_sidebar_widget)

        self.overlay_layout.addWidget(self.sidebar_widget)

    def create_stypes_tab_widget(self):
        self.stypes_tab_widget = Ui_extendedLeftTabBarWidget(self)

        self.stypes_tab_widget.setMovable(True)
        self.stypes_tab_widget.setObjectName('stypes_tab_widget')
        self.stypes_tab_widget.customize_ui()

        self.main_layout.addWidget(self.stypes_tab_widget)

    def middle_mouse_press(self, tab_pos):
        widget = self.stypes_tab_widget.widget(tab_pos)
        tab = self.get_stype_tab_by_widget(widget)
        self.toggle_stype_tab(code=tab.stype.get_code(), hide=True)

        # saving changes to config
        self.save_ignore_stypes_list()

    def tactic_sidebar_item_click(self, item_widget):
        if item_widget.get_type() == 'link':
            self.toggle_stype_tab(code=item_widget.get_code(), hide=False)
            self.raise_stype_tab(code=item_widget.get_code())

            # saving changes to config
            self.save_ignore_stypes_list()
            self.hide_overlay()

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
                self.set_opened_stypes_tabs_list(code, store=False)
            else:
                if idx == -1:
                    self.stypes_tab_widget.addTab(tab, '')

                    self.set_opened_stypes_tabs_list(code, store=True)
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

    def hamburger_button_click(self):

        if self.overlay_visible:
            self.hide_overlay()
        else:
            self.show_overlay()

    def fill_tactic_sidebar_widget(self):

        self.tactic_sidebar_widget.initial_fill()

    def get_opened_stypes_tabs_list(self):
        ignore_tabs_list = []
        if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.project.get_code()):
            if not gf.get_value_from_config(self.checkin_out_config, 'processTabsFilterGroupBox'):
                ignore_tabs_list = []
            else:
                ignore_tabs_list = self.checkin_out_config_projects[self.project.get_code()]['stypes_list']
                if not ignore_tabs_list:
                    ignore_tabs_list = []

        return ignore_tabs_list

    def set_opened_stypes_tabs_list(self, stype_code, store=True):

        self.init_stypes_config()

        # TODO this code will reset all previous projects states
        if not self.checkin_out_config_projects.get(self.project.get_code()):
            self.init_stypes_config(True)

        if self.checkin_out_config_projects:
            if not self.checkin_out_config_projects[self.project.get_code()]['stypes_list']:
                stypes_list = []
            else:
                stypes_list = self.checkin_out_config_projects[self.project.get_code()]['stypes_list']

            if store:
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

        opened_tabs_list = self.get_opened_stypes_tabs_list()

        stypes_list = self.project.stypes.values()

        sthpw_stypes = env_inst.get_stypes()
        if sthpw_stypes:
            stypes_list.extend(sthpw_stypes.values())

        # we creating all Stype Widgets, so we can access them if we need in all_search_tabs
        for stype in stypes_list:
            tab = checkin_out.Ui_checkInOutWidget(stype, self.project)
            tab.setParent(self)
            self.all_search_tabs.append(tab)

            # but only adding currenly visible tabs
            if tab.stype.get_code() in opened_tabs_list:
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

    def set_settings_from_dict(self, settings_dict):

        ref_settings_dict = {
            'stypes_tab_widget_currentIndex': 0
        }

        settings = gf.check_config(ref_settings_dict, settings_dict)

        self.current_tab_idx = int(settings['stypes_tab_widget_currentIndex'])

    def get_settings_dict(self):
        settings_dict = {
            # 'stypes_tree_visible': int(self.stypes_tree_visible),
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
        # Connecting to hamburger button click event
        top_bar_widget = env_inst.ui_main.get_top_bar_widget()
        top_bar_widget.connect_hamburger(self.hamburger_button_click)

        if not self.is_created:
            self.init_ui()
        event.accept()

    def resizeEvent(self, event):
        if self.overlay_layout_widget:
            self.overlay_layout_widget.resize(self.size())
        event.accept()

    def closeEvent(self, event):
        self.writeSettings()

        for tab in self.all_search_tabs:
            tab.close()
            tab.deleteLater()

        self.all_search_tabs = []
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.hide_overlay()
        else:
            super(Ui_checkInOutTabWidget, self).keyPressEvent(event)
