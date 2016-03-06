# module Main Ui Classes
# file ui_main_classes.py
# Main Window interface

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import environment as env
import tactic_classes as tc

if env.Mode().get == 'maya':
    import maya_functions as mf
import lib.ui.ui_main as ui_main
import ui_checkin_out_tabs_classes
import ui_conf_classes
import ui_my_tactic_classes
import ui_assets_browser_classes
import ui_float_notify_classes

reload(ui_main)
reload(ui_checkin_out_tabs_classes)
reload(ui_conf_classes)
reload(ui_my_tactic_classes)
reload(ui_assets_browser_classes)


class Ui_Main(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui_main()

    def create_ui_main(self):

        env.Inst().ui_main = self

        self.setupUi(self)

        # instance attributes
        self.menu = None
        self.ui_checkout = None
        self.ui_checkin = None
        self.settings = None
        # instance attributes

        self.tabs_items, self.context_items = self.query_tabs()

        self.create_ui_checkout()

        self.create_ui_checkin()

        self.create_ui_my_tactic()

        self.create_ui_assets_browser()

        # self.create_ui_float_notify()

        self.menu_bar_actions()

        self.skeyLineEdit_actions()

        self.readSettings()

        self.setIcon()

        self.setProjectInfo()

    def setIcon(self):
        icon = QtGui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    def setProjectInfo(self):
        self.currentProjectLabel.setText('Current Porject: <b>{0}</b> '.format(env.Env().get_project().replace('_', ' ').capitalize()))

    def click_on_skeyLineEdit(self, event):
        self.skeyLineEdit.selectAll()

    def skeyLineEdit_actions(self):
        self.skeyLineEdit.mousePressEvent = self.click_on_skeyLineEdit
        self.skeyLineEdit.returnPressed.connect(self.go_by_skey)

    def menu_bar_actions(self):
        """
        Actions for the main menu bar
        """

        def close_routine():
            if env.Mode().get == 'maya':
                maya_dock_instances = mf.get_maya_dock_window()
                for maya_dock_instance in maya_dock_instances:
                    maya_dock_instance.close()
                    maya_dock_instance.deleteLater()
            if env.Mode().get == 'standalone':
                self.close()

        self.actionExit.triggered.connect(close_routine)

        self.actionConfiguration.triggered.connect(lambda: ui_conf_classes.Ui_configuration_dialogWidget(self).show())

        self.actionApply_to_all_Tabs.triggered.connect(lambda: self.apply_current_view())

        self.main_tabWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.menu = QtGui.QAction("Copy Tab", self.main_tabWidget)
        self.menu.triggered.connect(
            lambda: self.copy_current_tab(self.main_tabWidget.currentIndex()))
        self.main_tabWidget.addAction(self.menu)

    def go_by_skey(self, skey_in=None, relates_to=None):
        if relates_to:
            self.relates_to = relates_to
        else:
            self.relates_to = None
            if self.main_tabWidget.currentWidget().objectName() == 'checkOutTab':
                self.relates_to = 'checkout'
            if self.main_tabWidget.currentWidget().objectName() == 'checkInTab':
                self.relates_to = 'checkin'

        print(self.relates_to)

        if skey_in:
            skey = tc.parce_skey(skey_in)
        else:
            skey = tc.parce_skey(self.skeyLineEdit.text())

        print(skey)

        common_pipeline_codes = ['snapshot', 'task']
        pipeline_code = None
        if skey:
            if skey.get('pipeline_code') and skey.get('project'):
                if skey.get('project') == env.Env().get_project():
                    if skey['pipeline_code'] not in common_pipeline_codes:
                        pipeline_code = u'{namespace}/{pipeline_code}'.format(**skey)
                else:
                    self.wrong_project_message(skey)

        if pipeline_code and self.relates_to in ['checkin', 'checkout']:
            tab_wdg = env.Inst().ui_check_tabs[self.relates_to].sObjTabWidget
            for i in range(tab_wdg.count()):
                if tab_wdg.widget(i).objectName() == pipeline_code:
                    tab_wdg.setCurrentIndex(i)

            tree_wdg = tab_wdg.currentWidget()
            tree_wdg.go_by_skey[0] = True

            if skey.get('context'):
                tree_wdg.go_by_skey[1] = skey

            search_code = skey.get('code')
            tree_wdg.searchLineEdit.setText(search_code)
            tree_wdg.searchOptionsGroupBox.searchCodeRadioButton.setChecked(True)
            tree_wdg.add_items_to_results(search_code)

    def wrong_project_message(self, skey):
        print(skey)
        msb = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                'Item {code}, not belongs to current project!'.format(**skey),
                                '<p>Current project is <b>{0}</b>, switch to <b>{project}</b> related to this item?</p>'.format(
                                    env.Env().get_project(), **skey) + '<p>This will restart TACTIC Handler!</p>',
                                QtGui.QMessageBox.NoButton, env.Inst().ui_main)
        msb.addButton("Switch to Project", QtGui.QMessageBox.YesRole)
        msb.addButton("Cancel", QtGui.QMessageBox.NoRole)
        msb.exec_()

        reply = msb.buttonRole(msb.clickedButton())

        if reply == QtGui.QMessageBox.YesRole:
            env.Env().set_project(skey['project'])
            skey_link = self.skeyLineEdit.text()
            self.close()
            self.create_ui_main()
            self.show()
            self.skeyLineEdit.setText(skey_link)
            self.go_by_skey()

    def apply_current_view(self):
        if self.main_tabWidget.currentIndex() == 0:
            self.ui_checkout.apply_current_view_to_all()
        if self.main_tabWidget.currentIndex() == 1:
            self.ui_checkin.apply_current_view_to_all()

    def copy_current_tab(self, current_index):

        if current_index == 0:
            self.ext_window = QtGui.QMainWindow(self)
            self.ext_window.setContentsMargins(9, 9, 9, 9)
            self.ext_window.closeEvent = self.closeEventExt
            self.ui_checkout.writeSettings()
            self.ext_window.setWindowTitle('Check Out Tab')
            self.ext_window.resize(self.size())
            self.ext_window.setCentralWidget(self.create_ui_checkout(True))
            self.ext_window.show()
        else:
            self.ext_window = QtGui.QMainWindow(self)
            self.ext_window.setContentsMargins(9, 9, 9, 9)
            self.ext_window.closeEvent = self.closeEventExt
            self.ui_checkin.writeSettings()
            self.ext_window.setWindowTitle('Check In Tab')
            self.ext_window.resize(self.size())
            self.ext_window.setCentralWidget(self.create_ui_checkin(True))
            self.ext_window.show()

    def create_ui_checkout(self, ext=False):
        """
        Create Check Out Tab
        """
        if ext:
            return ui_checkin_out_tabs_classes.Ui_checkOutTabWidget(self.context_items, self.tabs_items, self)
        else:
            self.ui_checkout = ui_checkin_out_tabs_classes.Ui_checkOutTabWidget(self.context_items, self.tabs_items,
                                                                                self)
            self.checkOutLayout.addWidget(self.ui_checkout)

    def create_ui_checkin(self, ext=False):
        """
        Create Check In Tab
        """

        if ext:
            return ui_checkin_out_tabs_classes.Ui_checkInTabWidget(self.context_items, self.tabs_items, self)
        else:
            self.ui_checkin = ui_checkin_out_tabs_classes.Ui_checkInTabWidget(self.context_items, self.tabs_items, self)
            self.checkInLayout.addWidget(self.ui_checkin)

    def create_ui_my_tactic(self):
        """
        Create My Tactic Tab
        """
        self.ui_my_tactic = ui_my_tactic_classes.Ui_myTacticWidget(self)
        self.myTacticLayout.addWidget(self.ui_my_tactic)

    def create_ui_float_notify(self):
        """
        Create My Tactic Tab
        """
        self.float_notify = ui_float_notify_classes.Ui_floatNotifyWidget(self)
        self.float_notify.show()
        self.float_notify.setSizeGripEnabled(True)

    def create_ui_assets_browser(self):
        """
        Create Assets Browser Tab
        """
        self.ui_assets_browser = ui_assets_browser_classes.Ui_assetsBrowserWidget(self)
        self.assetsBrowserLayout.addWidget(self.ui_assets_browser)

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')
        self.settings.beginGroup(env.Mode().get + '/ui_main')
        self.move(self.settings.value('pos', self.pos()))
        self.resize(self.settings.value('size', self.size()))
        state = str(self.settings.value("windowState"))
        if state == 'true':
            self.setWindowState(QtCore.Qt.WindowMaximized)
        self.main_tabWidget.setCurrentIndex(self.settings.value('main_tabWidget_currentIndex', 0))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_main')
        if self.windowState() == QtCore.Qt.WindowMaximized:
            state = True
        else:
            state = False
            self.settings.setValue('pos', self.pos())
            self.settings.setValue('size', self.size())
        self.settings.setValue("windowState", state)
        self.settings.setValue('main_tabWidget_currentIndex', self.main_tabWidget.currentIndex())
        print('Done main_ui settings write')
        self.settings.endGroup()

    def closeEvent(self, event):
        # event.ignore()
        self.ui_checkout.close()
        self.ui_checkin.close()
        # self.float_notify.close()
        self.writeSettings()
        event.accept()

    @staticmethod
    def query_tabs():
        tab_names = tc.query_tab_names()
        return tab_names, tc.context_query(tab_names['codes'])

    def closeEventExt(self, event):
        self.ext_window.deleteLater()
        event.accept()
