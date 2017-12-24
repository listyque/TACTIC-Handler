# ui_checkin_out_tabs_classes.py
# Check In Tabs interface

import json
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore
from lib.environment import env_mode, env_inst, env_server
from lib.configuration import cfg_controls
import lib.global_functions as gf
import lib.ui.checkin_out.ui_checkin_out_tabs as checkin_out_tabs
import ui_checkin_out_classes as checkin_out

reload(checkin_out_tabs)
reload(checkin_out)


class Ui_checkInOutTabWidget(QtGui.QWidget, checkin_out_tabs.Ui_sObjTabs):
    def __init__(self, project, layout_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.current_project = self.project.info['code']
        env_inst.set_control_tab(self.current_project, 'checkin_out', self)

        self.setupUi(self)
        # self.ui_tree = []
        self.all_search_tabs = []
        self.current_tab_idx = 0
        # self.visible_search_tabs = []
        self.main_tabs_widget = parent  # main tabs widget
        self.layout_widget = layout_widget

        self.current_namespace = self.project.info['type']
        self.stypes_items = self.project.stypes

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/checkin_out_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()

        # self.context_items = context_items

        self.is_created = False
        self.stypes_tree_visible = False
        self.tab_bar_customization()

    def create_ui(self):
        if self.stypes_items:
            self.is_created = True
            self.add_items_to_stypes_tree()
            self.readSettings()
            self.add_items_to_tabs()
            self.controls_actions()

    def controls_actions(self):
        self.hamburger_tab_button.clicked.connect(self.hamburger_button_click)

        self.sTypesTreeWidget.itemClicked.connect(self.stypes_tree_item_click)
        self.sTypesTreeWidget.itemChanged.connect(self.stypes_tree_item_change)

        self.sObjTabWidget.mousePressEvent = self.sobj_tab_middle_mouse_event

    def sobj_tab_middle_mouse_event(self, event):
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:
            pos = event.pos()
            # This is because hamburger button
            tab_pos = self.sObjTabWidget.tabBar().tabAt(QtCore.QPoint(pos.x() - 26, pos.y()))
            if tab_pos != -1:
                widget = self.sObjTabWidget.widget(tab_pos)
                tab = self.get_stype_tab_by_widget(widget)
                self.toggle_stype_tab(tab=tab, hide=True)
                tree_item = self.get_tree_item_by_code(tab.get_tab_code())
                if tree_item:
                    tree_item.setCheckState(0, QtCore.Qt.Unchecked)

        event.accept()

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
            if tab.tab_widget == widget:
                return tab

    def get_stype_tab_by_code(self, code):
        for tab in self.all_search_tabs:
            if tab.tab_name == code:
                return tab

    def get_tree_item_by_code(self, code):

        for i in range(self.sTypesTreeWidget.topLevelItemCount()):
            top = self.sTypesTreeWidget.topLevelItem(i)
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
            idx = self.sObjTabWidget.indexOf(tab.tab_widget)
            self.sObjTabWidget.setCurrentIndex(idx)

    def toggle_stype_tab(self, code=None, tab=None, hide=False):

        if code:
            tab = self.get_stype_tab_by_code(code)
        if tab:
            idx = self.sObjTabWidget.indexOf(tab.tab_widget)
            if hide:
                self.sObjTabWidget.removeTab(idx)
                self.set_ignore_stypes_list(code, hide=True)
            else:
                self.sObjTabWidget.addTab(tab.tab_widget, '')

                self.set_ignore_stypes_list(code, hide=False)
                self.sObjTabWidget.tabBar().setTabButton(self.sObjTabWidget.count()-1, QtGui.QTabBar.LeftSide, tab.get_tab_label())

    def raise_tab(self):
        self.main_tabs_widget.raise_tab(self.layout_widget)

    def apply_current_view_to_all(self):
        current_settings = None
        current_tab = self.get_current_tab_widget()
        if current_tab:
            current_settings = current_tab.get_settings_dict()

        if current_settings:
            for tab in self.all_search_tabs:
                tab.set_settings_from_dict(json.dumps(current_settings), apply_checkin_options=False, apply_search_options=False)

    def fast_save(self):
        current_tab = self.get_current_tab_widget()

        current_tab.fast_save()

    def get_current_tab_widget(self):
        current_widget = self.sObjTabWidget.currentWidget()
        for tab in self.all_search_tabs:
            if current_widget == tab.tab_widget:
                return tab

    def tab_bar_customization(self):
        self.hamburger_tab_button = QtGui.QToolButton()
        self.hamburger_tab_button.setAutoRaise(True)
        self.hamburger_tab_button.setMinimumWidth(20)
        self.hamburger_tab_button.setMinimumHeight(20)
        self.animation_close = QtCore.QPropertyAnimation(self.sTypesTreeWidget, "maximumWidth", self)
        self.animation_open = QtCore.QPropertyAnimation(self.sTypesTreeWidget, "maximumWidth", self)
        self.hamburger_tab_button.setIcon(gf.get_icon('navicon'))

        self.sObjTabWidget.setCornerWidget(self.hamburger_tab_button, QtCore.Qt.BottomLeftCorner)

    def hamburger_button_click(self):
        content_width = self.sTypesTreeWidget.sizeHintForColumn(0) + 40
        if self.stypes_tree_visible:
            self.animation_close.setDuration(100)
            self.animation_close.setStartValue(content_width)
            self.animation_close.setEndValue(0)
            self.animation_close.start()
            self.stypes_tree_visible = False
        else:
            self.animation_open.setDuration(150)
            self.animation_open.setStartValue(0)
            self.animation_open.setEndValue(content_width)
            self.animation_open.start()

            self.stypes_tree_visible = True

    def add_items_to_stypes_tree(self):
        exclude_list = self.get_ignore_stypes_list()
        self.sTypesTreeWidget.clear()

        all_stypes = []

        for stype in env_inst.projects[self.current_project].stypes.itervalues():
            all_stypes.append(stype.info)

        grouped = gf.group_dict_by(all_stypes, 'type')

        for name, value in grouped.iteritems():
            top_item = QtGui.QTreeWidgetItem()
            # self.top_item.setCheckState(0, QtCore.Qt.Checked)
            if not name:
                name = 'Untyped'
            top_item.setText(0, name.capitalize())
            top_item.setCheckState(0, QtCore.Qt.Checked)
            self.sTypesTreeWidget.addTopLevelItem(top_item)
            for item in value:
                child_item = QtGui.QTreeWidgetItem()
                if item.get('title'):
                    item_title = item['title'].capitalize()
                else:
                    item_title = 'Unnamed'
                item_code = item['code']
                child_item.setText(0, item_title)
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
        if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.current_project):
            if not gf.get_value_from_config(self.checkin_out_config, 'processTabsFilterGroupBox'):
                ignore_tabs_list = []
            else:
                ignore_tabs_list = self.checkin_out_config_projects[self.current_project]['stypes_list']
                if not ignore_tabs_list:
                    ignore_tabs_list = []

        return ignore_tabs_list

    def set_ignore_stypes_list(self, stype_code, hide=False):

        self.init_stypes_config()

        if self.checkin_out_config_projects:
            if not self.checkin_out_config_projects[self.current_project]['stypes_list']:
                stypes_list = []
            else:
                stypes_list = self.checkin_out_config_projects[self.current_project]['stypes_list']

            if hide:
                if stype_code not in stypes_list:
                    stypes_list.append(stype_code)
            else:
                if stype_code in stypes_list:
                    stypes_list.remove(stype_code)

            self.checkin_out_config_projects[self.current_project]['stypes_list'] = stypes_list

    def init_stypes_config(self):
        if not self.checkin_out_config_projects:
            from lib.ui_classes.ui_conf_classes import Ui_checkinOutPageWidget
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

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """

        ignore_tabs_list = self.get_ignore_stypes_list()

        for i, stype in enumerate(self.stypes_items.itervalues()):

            if stype.info['title']:
                tab_name = stype.info['title'].capitalize()
            else:
                if stype.info['code']:
                    tab_name = stype.info['code']
                else:
                    tab_name = 'Unnamed'

            tab_widget = QtGui.QWidget(self)
            tab_widget_layout = QtGui.QVBoxLayout()
            tab_widget_layout.setContentsMargins(0, 0, 0, 0)
            tab_widget_layout.setSpacing(0)
            tab_widget.setLayout(tab_widget_layout)
            tab_widget.setObjectName(tab_name)

            self.all_search_tabs.append(checkin_out.Ui_checkInOutWidget(stype, tab_widget, self.project, self))

        # Add tabs
        added_labels = []
        for i, tab in enumerate(self.all_search_tabs):
            if tab.tab_name not in ignore_tabs_list:
                added_labels.append(tab.get_tab_label())
                self.sObjTabWidget.addTab(tab.tab_widget, '')

        self.sObjTabWidget.setCurrentIndex(self.current_tab_idx)

        self.sObjTabWidget.setStyleSheet(
            '#sObjTabWidget > QTabBar::tab {background: transparent;border: 2px solid transparent;'
            'border-top-left-radius: 3px;border-top-right-radius: 3px;padding: 0px;}'
            '#sObjTabWidget > QTabBar::tab:selected, #sObjTabWidget > QTabBar::tab:hover {'
            'background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(255, 255, 255, 48), stop: 1 rgba(255, 255, 255, 32));}'
            '#sObjTabWidget > QTabBar::tab:selected {border-color: transparent;}'
            '#sObjTabWidget > QTabBar::tab:!selected {margin-top: 0px;}')

        # all this complicated adding, is to avoid added widget automatically loads ui
        for i, tab in enumerate(self.all_search_tabs):
            # actually adding search tab widgets
            if i == self.current_tab_idx:
                # this is needed because of Qt restore setting bug
                tab.do_creating_ui()
            tab.tab_widget.layout().addWidget(tab)

        # Add labels
        for i, label in enumerate(added_labels):
            self.sObjTabWidget.tabBar().setTabButton(i, QtGui.QTabBar.LeftSide, label)

    def readSettings(self):
        """
        Reading Settings
        """
        group_path = '{0}/{1}/{2}'.format(
            self.current_namespace,
            self.current_project,
            'checkin_out',
        )
        self.settings.beginGroup(group_path)

        if bool(int(self.settings.value('stypes_tree_visible', 0))):
            self.hamburger_button_click()
        self.current_tab_idx = int(self.settings.value('sObjTabWidget_currentIndex', 0))

        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        group_path = '{0}/{1}/{2}'.format(
            self.current_namespace,
            self.current_project,
            'checkin_out',
        )
        self.settings.beginGroup(group_path)
        self.settings.setValue('sObjTabWidget_currentIndex', int(self.sObjTabWidget.currentIndex()))
        self.settings.setValue('stypes_tree_visible', int(self.stypes_tree_visible))
        print('Done ui_checkin_out_tab settings write')
        self.settings.endGroup()
        # for tab in self.ui_tree:
        #     tab.writeSettings()

    def showEvent(self, event):
        if not self.is_created:
            self.create_ui()
        event.accept()

    def closeEvent(self, event):
        self.writeSettings()
        for tab in self.all_search_tabs:
            tab.close()
        event.accept()
