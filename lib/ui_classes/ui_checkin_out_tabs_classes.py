# ui_checkin_out_tabs_classes.py
# Check In Tabs interface

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import lib.environment as env
import lib.configuration as cfg
import lib.global_functions as gf
import lib.ui.misc.ui_sobj_tabs as sobj_tabs
import ui_checkin_tree_classes as checkin_tree_widget
import ui_checkout_tree_classes as checkout_tree_widget

reload(sobj_tabs)
reload(checkin_tree_widget)
reload(checkout_tree_widget)


class Ui_checkInTabWidget(QtGui.QWidget, sobj_tabs.Ui_sObjTabs):
    def __init__(self, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env.Inst.ui_check_tabs['checkin'] = self

        self.settings = QtCore.QSettings('settings/{0}/checkin_ui_config.ini'.format(env.Mode.get), QtCore.QSettings.IniFormat)
        self.checkin_out_config_projects = cfg.Controls.get_checkin_out_projects()
        self.checkin_out_config = cfg.Controls.get_checkin_out()

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
            tab.set_settings_from_dict(str(current_settings), apply_checkin_options=False, apply_search_options=False)

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """
        self.all_tabs_label = []

        if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.current_project):
            ignore_tabs_list = self.checkin_out_config_projects[self.current_project]['stypes_list']
        else:
            ignore_tabs_list = []

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
        for tab in self.ui_tree:
            if tab.tab_name in ignore_tabs_list:
                self.sObjTabWidget.removeTab(self.sObjTabWidget.indexOf(tab))

    def readSettings(self):
        """
        Reading Settings
        """
        group_path = '{0}/{1}'.format(self.current_namespace, self.current_project)
        self.settings.beginGroup(group_path)
        self.sObjTabWidget.setCurrentIndex(int(self.settings.value('sObjTabWidget_currentIndex', 0)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        group_path = '{0}/{1}'.format(self.current_namespace, self.current_project)
        self.settings.beginGroup(group_path)
        self.settings.setValue('sObjTabWidget_currentIndex', self.sObjTabWidget.currentIndex())
        print('Done ui_checkout_tab settings write')
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
        env.Inst.ui_check_tabs['checkout'] = self

        self.settings = QtCore.QSettings('settings/{0}/checkout_ui_config.ini'.format(env.Mode.get), QtCore.QSettings.IniFormat)
        self.checkin_out_config_projects = cfg.Controls.get_checkin_out_projects()
        self.checkin_out_config = cfg.Controls.get_checkin_out()

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
        self.all_tabs_label = []

        if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.current_project):
            ignore_tabs_list = self.checkin_out_config_projects[self.current_project]['stypes_list']
        else:
            ignore_tabs_list = []

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
            self.sObjTabWidget.tabBar().setTabButton(i, QtGui.QTabBar.LeftSide, tab_label)

        # Remove hidden tabs
        for tab in self.ui_tree:
            if tab.tab_name in ignore_tabs_list:
                self.sObjTabWidget.removeTab(self.sObjTabWidget.indexOf(tab))

    def readSettings(self):
        """
        Reading Settings
        """
        group_path = '{0}/{1}'.format(self.current_namespace, self.current_project)
        self.settings.beginGroup(group_path)
        self.sObjTabWidget.setCurrentIndex(int(self.settings.value('sObjTabWidget_currentIndex', 0)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        group_path = '{0}/{1}'.format(self.current_namespace, self.current_project)
        self.settings.beginGroup(group_path)
        self.settings.setValue('sObjTabWidget_currentIndex', self.sObjTabWidget.currentIndex())
        print('Done ui_checkout_tab settings write')
        self.settings.endGroup()
        for tab in self.ui_tree:
            tab.writeSettings()

    # def showEvent(self, event):
    #     env.Inst.ui_main.projects_docks[self.current_project].setWindowTitle(self.project.info.get('title') + ', (Checkout)')

    def closeEvent(self, event):
        self.writeSettings()
        for tab in self.ui_tree:
            tab.close()
        event.accept()
