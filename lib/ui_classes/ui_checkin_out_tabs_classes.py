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


class ColoredTabBar(QtGui.QTabBar):

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.setMovable(True)

        self.colors = []

    def set_tab_color(self, index, color):
        if not self.colors:
            for i in range(self.count()):
                self.colors.append('gray')

        self.colors[index] = color

        self.update()

    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionTab()

        if not self.colors:
            for i in range(self.count()):
                self.colors.append('gray')

        for i, tab_color in enumerate(self.colors):
            self.initStyleOption(option, i)
            color = Qt4Gui.QColor(tab_color)
            color.setAlpha(96)
            linearGrad = QtGui.QLinearGradient(QtCore.QPointF(0, 0), QtCore.QPointF(0, 1))
            linearGrad.setColorAt(0, color)
            linearGrad.setColorAt(1, QtCore.Qt.transparent)
            brush = QtGui.QBrush(linearGrad)

            color_selected = Qt4Gui.QColor(tab_color)
            color_selected.setAlpha(168)
            linearGrad = QtGui.QLinearGradient(QtCore.QPointF(0, 0), QtCore.QPointF(0, 20))
            linearGrad.setColorAt(0, color_selected)
            linearGrad.setColorAt(1, QtCore.Qt.transparent)

            brush_selected = QtGui.QBrush(linearGrad)

            option.palette.setBrush(Qt4Gui.QPalette.Normal, Qt4Gui.QPalette.Button, brush)
            option.palette.setBrush(Qt4Gui.QPalette.Normal, Qt4Gui.QPalette.Background, brush_selected)

            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Lighten)
            painter.drawControl(QtGui.QStyle.CE_TabBarTab, option)


class Ui_checkInOutTabWidget(QtGui.QWidget, checkin_out_tabs.Ui_sObjTabs):
    def __init__(self, project, layout_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.current_project = self.project.info['code']
        env_inst.set_control_tab(self.current_project, 'checkin_out', self)

        self.setupUi(self)
        # self.ui_tree = []
        self.all_search_tabs = []
        self.visible_search_tabs = []
        self.parent_ui = parent  # main tabs widget
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
            self.add_items_to_tabs()
            self.add_items_to_stypes_tree()
            self.controls_actions()

            self.readSettings()

    def controls_actions(self):
        self.hamburger_tab_button.clicked.connect(self.hamburger_button_click)

        self.sTypesTreeWidget.itemClicked.connect(self.stypes_tree_item_click)
        self.sTypesTreeWidget.itemChanged.connect(self.stypes_tree_item_change)

        self.sObjTabWidget.mousePressEvent = self.sobj_tab_middle_mouse_event

    def sobj_tab_middle_mouse_event(self, event):
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:
            tab_pos = self.sObjTabWidget.tabBar().tabAt(event.pos())
            print self.sObjTabWidget.widget(tab_pos)
            print self.visible_search_tabs[tab_pos].tab_widget
            print self.visible_search_tabs[tab_pos]
            self.toggle_stype_tab(tab=self.visible_search_tabs[tab_pos], hide=True)
            self.visible_search_tabs.pop(tab_pos)

        event.accept()

    def stypes_tree_item_click(self, item):
        item_data = item.data(0, QtCore.Qt.UserRole)
        if item_data:
            self.raise_stype_tab(code=item_data.get('code'))

    def stypes_tree_item_change(self, item):
        item_data = item.data(0, QtCore.Qt.UserRole)
        if item_data:
            if item.checkState(0):
                self.toggle_stype_tab(code=item_data.get('code'), hide=False)
            else:
                self.toggle_stype_tab(code=item_data.get('code'), hide=True)

    def get_stype_tab_by_code(self, code):
        for tab in self.all_search_tabs:
            if tab.tab_name == code:
                return tab

    def raise_stype_tab(self, code=None, tab=None):
        if code:
            tab = self.get_stype_tab_by_code(code)
        if tab:
            idx = self.sObjTabWidget.indexOf(tab.tab_widget)
            self.sObjTabWidget.setCurrentIndex(idx)

    def toggle_stype_tab(self, code=None, tab=None, hide=False):

        print code

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
        self.parent_ui.raise_tab(self.layout_widget)  # parent here is widget with layout

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
            self.top_item = QtGui.QTreeWidgetItem()
            # self.top_item.setCheckState(0, QtCore.Qt.Checked)
            if not name:
                name = 'Untyped'
            self.top_item.setText(0, name.capitalize())
            self.top_item.setCheckState(0, QtCore.Qt.Checked)
            self.sTypesTreeWidget.addTopLevelItem(self.top_item)
            for item in value:
                self.child_item = QtGui.QTreeWidgetItem()
                if item.get('title'):
                    item_title = item['title'].capitalize()
                else:
                    item_title = 'Unnamed'
                item_code = item['code']
                self.child_item.setText(0, item_title)
                self.child_item.setText(1, item_code)
                self.child_item.setData(0, QtCore.Qt.UserRole, item)
                self.child_item.setCheckState(0, QtCore.Qt.Checked)
                if exclude_list:
                    if item_code in exclude_list:
                        self.child_item.setCheckState(0, QtCore.Qt.Unchecked)
                self.top_item.addChild(self.child_item)

            self.top_item.setExpanded(True)

    def get_ignore_stypes_list(self):
        ignore_tabs_list = []
        if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.current_project):
            if not gf.get_value_from_config(self.checkin_out_config, 'processTabsFilterGroupBox', 'QGroupBox'):
                ignore_tabs_list = []
            else:
                ignore_tabs_list = self.checkin_out_config_projects[self.current_project]['stypes_list']
                if not ignore_tabs_list:
                    ignore_tabs_list = []

        return ignore_tabs_list

    def set_ignore_stypes_list(self, stype_code, hide=False):
        print self.checkin_out_config_projects
        if self.checkin_out_config_projects:
            stypes_list = self.checkin_out_config_projects[self.current_project]['stypes_list']
            if hide:
                stypes_list.append(stype_code)
            else:
                stypes_list.remove(stype_code)

            self.checkin_out_config_projects[self.current_project]['stypes_list'] = stypes_list

            cfg_controls.set_checkin_out_projects(self.checkin_out_config_projects)

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """

        # self.sObjTabWidget.setTabBar(ColoredTabBar(self))

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

            tab_widget_layout.addWidget(self.all_search_tabs[i])

        # Add tabs
        added_labels = []
        for tab in self.all_search_tabs:
            if tab.tab_name not in ignore_tabs_list:
                added_labels.append(tab.get_tab_label())
                self.visible_search_tabs.append(tab)
                self.sObjTabWidget.addTab(tab.tab_widget, '')

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

        idx = int(self.settings.value('sObjTabWidget_currentIndex', 0))
        # this is needed because of restore setting bug
        if len(self.visible_search_tabs)-1 >= idx:
            self.visible_search_tabs[idx].do_creating_ui()
        else:
            self.visible_search_tabs[len(self.visible_search_tabs)-1].do_creating_ui()
        self.sObjTabWidget.setCurrentIndex(idx)
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


# class Ui_checkOutTabWidget(QtGui.QWidget, sobj_tabs.Ui_sObjTabs):
#     def __init__(self, project, layout_widget, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#         self.project = project
#         self.current_project = self.project.info['code']
#         env_inst.set_control_tab(self.current_project, 'checkout', self)
#
#         self.current_namespace = self.project.info['type']
#         self.stypes_items = self.project.stypes
#
#         self.setupUi(self)
#         self.ui_tree = []
#         self.parent_ui = parent  # main tabs widget
#         self.layout_widget = layout_widget
#
#         self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/checkin_out__ui_config.ini'.format(
#             env_mode.get_current_path(),
#             env_mode.get_node(),
#             env_server.get_cur_srv_preset(),
#             env_mode.get_mode()),
#             QtCore.QSettings.IniFormat)
#
#         self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
#         self.checkin_out_config = cfg_controls.get_checkin_out()
#
#         # self.context_items = context_items
#
#         self.is_created = False
#
#     def create_ui(self):
#         if self.stypes_items:
#             self.is_created = True
#             self.add_items_to_tabs()
#             self.readSettings()
#
#     def apply_current_view_to_all(self):
#         current_tab = self.sObjTabWidget.currentWidget()
#         current_settings = current_tab.get_settings_dict()
#
#         for tab in self.ui_tree:
#             tab.set_settings_from_dict(str(current_settings), apply_search_options=False)
#
#     def raise_tab(self):
#         self.parent_ui.raise_tab(self.layout_widget)  # parent here is widget with layout
#
#     def add_items_to_tabs(self):
#         """
#         Adding process tabs marked for Maya
#         """
#
#         # self.sObjTabWidget.setTabBar(ColoredTabBar(self))
#
#         self.all_tabs_label = []
#
#         ignore_tabs_list = []
#         if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.current_project):
#             if not gf.get_value_from_config(self.checkin_out_config, 'processTabsFilterGroupBox', 'QGroupBox'):
#                 ignore_tabs_list = []
#             else:
#                 ignore_tabs_list = self.checkin_out_config_projects[self.current_project]['stypes_list']
#
#         for i, stype in enumerate(self.stypes_items.itervalues()):
#             self.ui_tree.append(checkout_tree_widget.Ui_checkOutTreeWidget(stype, i, self.project, self))
#             if stype.info['title']:
#                 tab_name = stype.info['title'].capitalize()
#             else:
#                 if stype.info['code']:
#                     tab_name = stype.info['code']
#                 else:
#                     tab_name = 'Unnamed'
#             self.sObjTabWidget.addTab(self.ui_tree[i], '')
#
#             tab_label = gf.create_tab_label(tab_name, stype)
#             self.all_tabs_label.append(tab_label)
#
#             # effect = QtGui.QGraphicsColorizeEffect(self.sObjTabWidget.tabBar())
#             # self.animation = QtCore.QPropertyAnimation(effect, "color", self)
#             # self.animation.setDuration(500)
#             # self.animation.setStartValue(Qt4Gui.QColor(0, 0, 0, 0))
#             # self.animation.setEndValue(Qt4Gui.QColor(49, 140, 72, 128))
#             # self.animation.start()
#             # print effect.boundingRectFor(self.sObjTabWidget.tabBar().tabRect(0))
#
#             # effect.updateBoundingRect()
#             # print effect.sourceBoundingRect()
#             # print effect.set
#             # effect.update()
#             # self.sObjTabWidget.tabBar().setGraphicsEffect(effect)
#             # print self.sObjTabWidget.tabBar().drawBase()
#             # QtGui.QTabBar.drawBase()
#
#             self.sObjTabWidget.tabBar().setTabButton(i, QtGui.QTabBar.LeftSide, tab_label)
#
#         # Remove hidden tabs
#         if ignore_tabs_list:
#             for tab in self.ui_tree:
#                 if tab.tab_name in ignore_tabs_list:
#                     self.sObjTabWidget.removeTab(self.sObjTabWidget.indexOf(tab))
#
#     def readSettings(self):
#         """
#         Reading Settings
#         """
#         group_path = '{0}/{1}/{2}'.format(
#             self.current_namespace,
#             self.current_project,
#             'checkout',
#         )
#         self.settings.beginGroup(group_path)
#         self.sObjTabWidget.setCurrentIndex(int(self.settings.value('sObjTabWidget_currentIndex', 0)))
#         self.settings.endGroup()
#
#     def writeSettings(self):
#         """
#         Writing Settings
#         """
#         group_path = '{0}/{1}/{2}'.format(
#             self.current_namespace,
#             self.current_project,
#             'checkout',
#         )
#         self.settings.beginGroup(group_path)
#         self.settings.setValue('sObjTabWidget_currentIndex', self.sObjTabWidget.currentIndex())
#         print('Done ui_checkout_tab settings write')
#         self.settings.endGroup()
#         for tab in self.ui_tree:
#             tab.writeSettings()
#
#     def showEvent(self, event):
#         if not self.is_created:
#             self.create_ui()
#         event.accept()
#
#     def closeEvent(self, event):
#         self.writeSettings()
#         for tab in self.ui_tree:
#             tab.close()
#         event.accept()
