# module General Ui
# file ui_maya_dock.py
# Main Dock Window interface

# import PySide.QtCore as QtCore
# import PySide.QtGui as QtGui
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore
from lib.environment import env_inst, env_mode, env_server
import lib.maya_functions as mf
import lib.tactic_classes as tc
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import ui_main_classes

reload(ui_main_classes)


class Ui_DockMain(MayaQWidgetDockableMixin, QtGui.QMainWindow):
    def __init__(self, hotkeys=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env_inst.ui_maya_dock = self
        self.setObjectName('TacticHandlerDock')
        self.maya_window = self.parent()
        print self.maya_window, 'WINDOW'

        self.hotkeys_dict = hotkeys

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/main_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.docked = None
        self.dock_pos = None
        self.dock_area = None
        self.dock_size = None
        self.dock_is_floating = None

        self.readSettings()

        self.toggle_dock = None
        self.maya_dock = None
        self.status_bar = None

        self.create_ui_main()

        self.create_ui()

        # overriding QMayaDockWidget buggy resize event
        # self.maya_window.resizeEvent = self.resizeEvent

        self.catch_maya_closing()

    def create_ui(self):
        # if self.docked:
        #     self.set_docked()
        # else:
            self.set_undocked()

    def toggle_docking(self):
        if self.toggle_dock:
            self.set_undocked()
        else:
            self.set_docked()

    def create_ui_main(self):
        env_inst.ui_main = ui_main_classes.Ui_Main()
        # env_inst.ui_main.show()
        # asz = QtGui.QPushButton('AASD')
        # self.setCentralWidget(asz)
        # print env_inst.ui_main.parent()
        self.setCentralWidget(env_inst.ui_main)
        self.setWindowTitle(env_inst.ui_main.windowTitle())
        self.move(self.dock_pos)

    def handle_hotkeys(self):
        if self.hotkeys_dict:
            project_code = self.hotkeys_dict.get('project')
            control_tab = self.hotkeys_dict.get('control_tab')
            action = self.hotkeys_dict.get('action')

            if project_code:
                env_inst.ui_main.create_project_dock(project_code, close_project=False, raise_tab=True)

            if control_tab:
                if control_tab in ['checkin_out']:
                    if project_code:
                        current_control = env_inst.get_control_tab(project_code, tab_code=control_tab)
                    else:
                        current_control = env_inst.get_control_tab(tab_code=control_tab)
                    if current_control:
                        current_control.raise_tab()
                        if action:
                            if action == 'save':
                                current_control.fast_save()

            self.hotkeys_dict = None

    def set_docked(self):
        if self.status_bar:
            self.status_bar.hide()

        self.toggle_dock = True
        self.setDockableParameters(
            dockable=True,
            floating=self.dock_is_floating,
            area=self.dock_area,
            width=self.dock_size.width(),
            height=self.dock_size.height()
        )
        self.maya_dock = self.parent()
        self.maya_dock.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea |
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.show()
        self.raise_()
        self.docked = True

    def set_undocked(self):
        self.toggle_dock = False
        self.setDockableParameters(
            dockable=False,
            floating=self.dock_is_floating,
            area=self.dock_area,
            width=self.dock_size.width(),
            height=self.dock_size.height()
        )
        if self.maya_dock:
            self.removeDockWidget(self.maya_dock)
            self.maya_dock.close()
            self.maya_dock.deleteLater()
        self.docked = False
        self.status_bar = env_inst.ui_main.statusBar()
        self.status_bar.show()

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup('ui_maya_dock')
        self.docked = bool(int(self.settings.value('docked', 1)))
        self.dock_pos = self.settings.value('dock_pos', QtCore.QPoint(200, 200))
        if self.docked:
            self.move(self.dock_pos)
        self.dock_is_floating = bool(int(self.settings.value('dock_isFloating', 0)))
        self.dock_size = self.settings.value('dock_size', QtCore.QSize(427, 690))
        if int(self.settings.value('dock_tabArea', 1)) == 2:
            self.dock_area = 'right'
        else:
            self.dock_area = 'left'

        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup('ui_maya_dock')
        if self.docked:
            self.settings.setValue('dock_pos', self.maya_dock.pos())
            self.settings.setValue('dock_size', self.maya_dock.size())
            self.settings.setValue('dock_isFloating', int(bool(self.isFloating())))
            self.settings.setValue('dock_tabArea', int(self.maya_window.dockWidgetArea(self.maya_dock)))
        else:
            self.settings.setValue('dock_pos', self.pos())
            self.settings.setValue('dock_size', self.size())
        self.settings.setValue('docked', int(self.docked))
        print('Done ui_maya_dock settings write')
        self.settings.endGroup()

    def catch_maya_closing(self):
        QtGui.QApplication.instance().aboutToQuit.connect(env_inst.ui_main.close)
        QtGui.QApplication.instance().aboutToQuit.connect(self.close)

    def closeEvent(self, event):
        event.accept()
        if self.docked:
            self.removeDockWidget(self.maya_dock)
            self.maya_dock.close()
            self.maya_dock.deleteLater()
        self.writeSettings()


def close_all_instances():
    try:
        main_docks = mf.get_maya_dock_window()
        for dock in main_docks:
            dock.close()
            if env_inst.ui_main:
                env_inst.ui_main.close()
    except:
        raise


def create_ui(thread, hotkeys=None):
    thread = tc.treat_result(thread)

    if thread.result == QtGui.QMessageBox.ApplyRole:
        retry_startup(thread)
    else:
        if thread.isFailed():
            env_mode.set_offline()
            main_tab = Ui_DockMain()
        else:
            env_mode.set_online()
            main_tab = Ui_DockMain(hotkeys=hotkeys)
        main_tab.show()
        main_tab.raise_()

        if thread.result == QtGui.QMessageBox.ActionRole:
            env_inst.ui_main.open_config_dialog()


def retry_startup(thread):
    thread.run()
    create_ui(thread)


def restart():
    reload(ui_main_classes)
    ping_thread = tc.get_server_thread(dict(), tc.server_ping, lambda: create_ui(ping_thread), parent=env_inst.ui_super)
    ping_thread.start()
    return ping_thread


def startup(restart=False, hotkeys=None):
    if restart:
        close_all_instances()

    env_inst.ui_super = mf.get_maya_window()

    try:
        main_tab = mf.get_maya_dock_window()[0]
        main_tab.hotkeys_dict = hotkeys
        main_tab.handle_hotkeys()
        main_tab.show()
        main_tab.raise_()
    except:
        ping_thread = tc.get_server_thread(dict(), tc.server_ping, lambda: create_ui(ping_thread, hotkeys), parent=env_inst.ui_super)
        ping_thread.start()
