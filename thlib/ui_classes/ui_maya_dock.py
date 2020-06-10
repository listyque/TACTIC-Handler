# module General Ui
# file ui_maya_dock.py
# Main Dock Window interface

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore
from thlib.environment import env_inst, env_mode, env_read_config, env_write_config
import thlib.maya_functions as mf
import thlib.tactic_classes as tc
import thlib.global_functions as gf
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.cmds as cmds
import ui_main_classes

reload(ui_main_classes)


class Ui_DockMain(MayaQWidgetDockableMixin, QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        env_inst.ui_maya_dock = self

        self.setObjectName('TacticHandlerDock')

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

        self.catch_maya_closing()

    def create_ui(self):
        if self.docked:
            self.set_docked()
        else:
            self.set_undocked()

    def toggle_docking(self):
        if self.toggle_dock:
            self.set_undocked()
        else:
            self.set_docked()

    def create_ui_main(self):
        env_inst.ui_main = ui_main_classes.Ui_Main()
        self.setCentralWidget(env_inst.ui_main)
        self.setWindowTitle(env_inst.ui_main.windowTitle())
        self.move(self.dock_pos)

    def set_docked(self):
        # status_bar = env_inst.ui_main.statusBar()

        # if status_bar:
        #     status_bar.show()

        self.toggle_dock = True
        self.setDockableParameters(
            dockable=True,
            floating=self.dock_is_floating,
            area=self.dock_area,
            width=self.dock_size.width(),
            height=self.dock_size.height()
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
            print self.maya_dock
            self.removeDockWidget(self.maya_dock)
            self.maya_dock.close()
            self.maya_dock.deleteLater()
        self.docked = False
        # status_bar = env_inst.ui_main.statusBar()
        # status_bar.show()

    def set_settings_from_dict(self, settings_dict=None):

        ref_settings_dict = {
            'docked': 0,
            'dock_pos': (200, 200),
            'dock_size': (427, 690),
            'dock_isFloating': 0,
            'dock_tabArea': 1,
        }

        settings = gf.check_config(ref_settings_dict, settings_dict)

        self.docked = bool(int(settings['docked']))

        self.dock_pos = gf.tuple_to_qsize(settings['dock_pos'], 'pos')
        self.dock_size = gf.tuple_to_qsize(settings['dock_size'], 'size')

        self.dock_is_floating = bool(int(settings['dock_isFloating']))

        if int(settings['dock_tabArea']) == 2:
            self.dock_area = 'right'
        else:
            self.dock_area = 'left'

    def get_settings_dict(self):
        settings_dict = {
            'docked': int(self.docked),
        }
        if self.docked:
            maya_dock = self.parent()

            settings_dict['dock_pos'] = gf.qsize_to_tuple(maya_dock.pos())
            settings_dict['dock_size'] = gf.qsize_to_tuple(maya_dock.size())
            settings_dict['dock_isFloating'] = int(bool(self.isFloating()))
            settings_dict['dock_tabArea'] = int(env_inst.ui_super.dockWidgetArea(self.maya_dock))
        else:
            settings_dict['dock_pos'] = gf.qsize_to_tuple(self.pos())
            settings_dict['dock_size'] = gf.qsize_to_tuple(self.size())
            settings_dict['dock_isFloating'] = 0
            settings_dict['dock_tabArea'] = 1

        return settings_dict

    def readSettings(self):

        self.set_settings_from_dict(
            env_read_config(filename='ui_maya_settings', unique_id='ui_main', long_abs_path=True)
        )

    def writeSettings(self):

        env_write_config(self.get_settings_dict(), filename='ui_maya_settings', unique_id='ui_main', long_abs_path=True)

    def raise_window(self):
        if self.isMaximized():
            self.showMaximized()
        else:
            self.showNormal()

        QtGui.QDialog.activateWindow(self)

    def catch_maya_closing(self):
        QtGui.QApplication.instance().aboutToQuit.connect(env_inst.ui_main.close)
        QtGui.QApplication.instance().aboutToQuit.connect(self.close)

    def closeEvent(self, event):

        if self.docked:
            self.removeDockWidget(self.maya_dock)
            self.maya_dock.close()
            self.maya_dock.deleteLater()
        self.writeSettings()

        event.accept()


def init_env(current_path):
    env_mode.set_current_path(current_path)
    env_mode.set_mode('maya')


def close_all_instances():

    try:
        main_docks = mf.get_maya_dock_window()
        for dock in main_docks:
            dock.writeSettings()
            dock.close()
            dock.deleteLater()
            if env_inst.ui_main:
                env_inst.ui_main.close()

        if cmds.workspaceControl('TacticHandlerDockWorkspaceControl', e=True, exists=True):
            cmds.deleteUI('TacticHandlerDockWorkspaceControl', control=True)
    except:
        raise


@gf.catch_error
def create_ui(error_tuple=None):

    if error_tuple:
        env_mode.set_offline()
        main_tab = Ui_DockMain()
        gf.error_handle(error_tuple)
    else:
        env_mode.set_online()
        main_tab = Ui_DockMain()

    main_tab.show()
    main_tab.raise_()


@gf.catch_error
def startup(restart=False, *args, **kwargs):
    if restart:
        close_all_instances()

    env_inst.ui_super = mf.get_maya_window()

    try:
        main_tab = mf.get_maya_dock_window()[0]
        main_tab.show()
        main_tab.raise_()
        main_tab.raise_window()
    except:

        def server_ping_agent():
            return tc.server_ping()

        ping_worker = gf.get_thread_worker(
            server_ping_agent,
            finished_func=lambda: create_ui(None),
            error_func=create_ui
        )

        ping_worker.start()
