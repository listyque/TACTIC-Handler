# ui_checkin_out_tabs_classes.py
# Check In Tabs interface

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
from lib.environment import env_mode, env_inst, env_server
from lib.configuration import cfg_controls
import lib.global_functions as gf
import lib.ui.misc.ui_sobj_tabs as sobj_tabs
import ui_checkin_tree_classes as checkin_tree_widget
import ui_checkout_tree_classes as checkout_tree_widget

reload(sobj_tabs)
reload(checkin_tree_widget)
reload(checkout_tree_widget)


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
            color = QtGui.QColor(tab_color)
            color.setAlpha(96)
            linearGrad = QtGui.QLinearGradient(QtCore.QPointF(0, 0), QtCore.QPointF(0, 1))
            linearGrad.setColorAt(0, color)
            linearGrad.setColorAt(1, QtCore.Qt.transparent)
            brush = QtGui.QBrush(linearGrad)

            color_selected = QtGui.QColor(tab_color)
            color_selected.setAlpha(168)
            linearGrad = QtGui.QLinearGradient(QtCore.QPointF(0, 0), QtCore.QPointF(0, 20))
            linearGrad.setColorAt(0, color_selected)
            linearGrad.setColorAt(1, QtCore.Qt.transparent)

            brush_selected = QtGui.QBrush(linearGrad)

            option.palette.setBrush(QtGui.QPalette.Normal, QtGui.QPalette.Button, brush)
            option.palette.setBrush(QtGui.QPalette.Normal, QtGui.QPalette.Background, brush_selected)

            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Lighten)
            painter.drawControl(QtGui.QStyle.CE_TabBarTab, option)


class Ui_checkInTabWidget(QtGui.QWidget, sobj_tabs.Ui_sObjTabs):
    def __init__(self, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env_inst.ui_check_tabs['checkin'] = self

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/checkin_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()

        self.setupUi(self)
        self.ui_tree = []

        # self.context_items = context_items
        self.project = project
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']
        self.stypes_items = project.stypes

        if self.stypes_items:
            self.add_items_to_tabs()
            self.add_items_to_stypes_tree()
            self.tab_bar_customization()
            self.controls_actions()
            self.stypes_tree_visible = False

            self.readSettings()

    def controls_actions(self):
        self.hamburger_tab_button.clicked.connect(self.hamburger_button_click)

    def apply_current_view_to_all(self):
        current_tab = self.sObjTabWidget.currentWidget()
        current_settings = current_tab.get_settings_dict()

        for tab in self.ui_tree:
            tab.set_settings_from_dict(str(current_settings), apply_checkin_options=False, apply_search_options=False)

    def tab_bar_customization(self):
        self.hamburger_tab_button = QtGui.QToolButton()
        self.hamburger_tab_button.setAutoRaise(True)
        self.hamburger_tab_button.setMinimumWidth(22)
        self.hamburger_tab_button.setMinimumHeight(22)
        self.animation_close = QtCore.QPropertyAnimation(self.sTypesTreeWidget, "maximumWidth", self)
        self.animation_open = QtCore.QPropertyAnimation(self.sTypesTreeWidget, "maximumWidth", self)
        self.hamburger_tab_button.setIcon(gf.get_icon('navicon'))

        self.sObjTabWidget.setCornerWidget(self.hamburger_tab_button, QtCore.Qt.TopLeftCorner)

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
            self.top_item.setCheckState(0, QtCore.Qt.Checked)
            if not name:
                name = 'Untyped'
            self.top_item.setText(0, name.capitalize())
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

        return ignore_tabs_list

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """

        # self.sObjTabWidget.setTabBar(ColoredTabBar(self))

        self.all_tabs_label = []

        ignore_tabs_list = self.get_ignore_stypes_list()

        for i, stype in enumerate(self.stypes_items.itervalues()):

            self.ui_tree.append(checkin_tree_widget.Ui_checkInTreeWidget(stype, i, self.project, self))
            if stype.info['title']:
                tab_name = stype.info['title'].capitalize()
            else:
                if stype.info['code']:
                    tab_name = stype.info['code']
                else:
                    tab_name = 'Unnamed'
            self.sObjTabWidget.addTab(self.ui_tree[i], '')

            tab_label = gf.create_tab_label(tab_name, stype)
            self.all_tabs_label.append(tab_label)
            self.sObjTabWidget.tabBar().setTabButton(i, QtGui.QTabBar.LeftSide, tab_label)

        # Remove hidden tabs
        if ignore_tabs_list:
            for tab in self.ui_tree:
                if tab.tab_name in ignore_tabs_list:
                    self.sObjTabWidget.removeTab(self.sObjTabWidget.indexOf(tab))

    def readSettings(self):
        """
        Reading Settings
        """
        group_path = '{0}/{1}/{2}'.format(
            self.current_namespace,
            self.current_project,
            'checkin',
        )
        self.settings.beginGroup(group_path)
        self.sObjTabWidget.setCurrentIndex(int(self.settings.value('sObjTabWidget_currentIndex', 0)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        group_path = '{0}/{1}/{2}'.format(
            self.current_namespace,
            self.current_project,
            'checkin',
        )
        self.settings.beginGroup(group_path)
        self.settings.setValue('sObjTabWidget_currentIndex', self.sObjTabWidget.currentIndex())
        print('Done ui_checkin_tab settings write')
        self.settings.endGroup()
        for tab in self.ui_tree:
            tab.writeSettings()

    def closeEvent(self, event):
        self.writeSettings()
        for tab in self.ui_tree:
            tab.close()
        event.accept()


class Ui_checkOutTabWidget(QtGui.QWidget, sobj_tabs.Ui_sObjTabs):
    def __init__(self, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env_inst.ui_check_tabs['checkout'] = self

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/checkin_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()

        self.setupUi(self)
        self.ui_tree = []

        # self.context_items = context_items
        self.project = project
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']
        self.stypes_items = project.stypes
        if self.stypes_items:
            self.add_items_to_tabs()

        self.readSettings()

    def apply_current_view_to_all(self):
        current_tab = self.sObjTabWidget.currentWidget()
        current_settings = current_tab.get_settings_dict()

        for tab in self.ui_tree:
            tab.set_settings_from_dict(str(current_settings), apply_search_options=False)

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """

        # self.sObjTabWidget.setTabBar(ColoredTabBar(self))

        self.all_tabs_label = []

        ignore_tabs_list = []
        if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.current_project):
            if not gf.get_value_from_config(self.checkin_out_config, 'processTabsFilterGroupBox', 'QGroupBox'):
                ignore_tabs_list = []
            else:
                ignore_tabs_list = self.checkin_out_config_projects[self.current_project]['stypes_list']

        for i, stype in enumerate(self.stypes_items.itervalues()):
            self.ui_tree.append(checkout_tree_widget.Ui_checkOutTreeWidget(stype, i, self.project, self))
            if stype.info['title']:
                tab_name = stype.info['title'].capitalize()
            else:
                if stype.info['code']:
                    tab_name = stype.info['code']
                else:
                    tab_name = 'Unnamed'
            self.sObjTabWidget.addTab(self.ui_tree[i], '')

            tab_label = gf.create_tab_label(tab_name, stype)
            self.all_tabs_label.append(tab_label)

            # effect = QtGui.QGraphicsColorizeEffect(self.sObjTabWidget.tabBar())
            # self.animation = QtCore.QPropertyAnimation(effect, "color", self)
            # self.animation.setDuration(500)
            # self.animation.setStartValue(QtGui.QColor(0, 0, 0, 0))
            # self.animation.setEndValue(QtGui.QColor(49, 140, 72, 128))
            # self.animation.start()
            # print effect.boundingRectFor(self.sObjTabWidget.tabBar().tabRect(0))

            # effect.updateBoundingRect()
            # print effect.sourceBoundingRect()
            # print effect.set
            # effect.update()
            # self.sObjTabWidget.tabBar().setGraphicsEffect(effect)
            # print self.sObjTabWidget.tabBar().drawBase()
            # QtGui.QTabBar.drawBase()

            self.sObjTabWidget.tabBar().setTabButton(i, QtGui.QTabBar.LeftSide, tab_label)

        # Remove hidden tabs
        if ignore_tabs_list:
            for tab in self.ui_tree:
                if tab.tab_name in ignore_tabs_list:
                    self.sObjTabWidget.removeTab(self.sObjTabWidget.indexOf(tab))

    def readSettings(self):
        """
        Reading Settings
        """
        group_path = '{0}/{1}/{2}'.format(
            self.current_namespace,
            self.current_project,
            'checkout',
        )
        self.settings.beginGroup(group_path)
        self.sObjTabWidget.setCurrentIndex(int(self.settings.value('sObjTabWidget_currentIndex', 0)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        group_path = '{0}/{1}/{2}'.format(
            self.current_namespace,
            self.current_project,
            'checkout',
        )
        self.settings.beginGroup(group_path)
        self.settings.setValue('sObjTabWidget_currentIndex', self.sObjTabWidget.currentIndex())
        print('Done ui_checkout_tab settings write')
        self.settings.endGroup()
        for tab in self.ui_tree:
            tab.writeSettings()

    # def showEvent(self, event):
    #     env_inst.ui_main.projects_docks[self.current_project].setWindowTitle(self.project.info.get('title') + ', (Checkout)')

    def closeEvent(self, event):
        self.writeSettings()
        for tab in self.ui_tree:
            tab.close()
        event.accept()
