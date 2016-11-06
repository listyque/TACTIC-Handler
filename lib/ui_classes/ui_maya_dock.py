# module General Ui
# file ui_maya_dock.py
# Main Dock Window interface

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
# import lib.environment as env
from lib.environment import env_inst, env_mode, env_server
import lib.maya_functions as mf
import lib.tactic_classes as tc
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import ui_main_classes

reload(mf)
reload(tc)
reload(ui_main_classes)


class Ui_DockMain(MayaQWidgetDockableMixin, QtGui.QMainWindow):
    def __init__(self, tab_index=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env_inst.ui_maya_dock = self

        self.tab_index = tab_index

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/main_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.ui_main_window = ui_main_classes.Ui_Main(self.parent())
        self.setCentralWidget(self.ui_main_window)
        env_inst.ui_main = self.ui_main_window

        self.setObjectName('TacticDockWindow')

        self.readSettings()

        # overriding QMayaDockWidget buggy resize event
        self.parent().resizeEvent = self.resizeEvent

        self.switch_tab()

        self.catch_maya_closing()

    @staticmethod
    def restarting(tab_index):
        try:
            main_dock = mf.get_maya_dock_window()
            for i in range(len(main_dock)):
                main_dock[i].close()
                print('TACTIC Handler is already running! Restarting...')
        except:
            raise

        Ui_DockMain(tab_index)

    def switch_tab(self, tab_index=None):
        # Open current tab when app starting
        if self.tab_index is not None:
            self.ui_main_window.main_tabWidget.setCurrentIndex(self.tab_index)

        if tab_index is not None:
            self.ui_main_window.main_tabWidget.setCurrentIndex(tab_index)

    def readSettings(self):
        """
        Reading Settings
        """
        self.setWindowTitle(self.ui_main_window.windowTitle())
        self.settings.beginGroup('ui_maya_dock')
        is_floating = self.settings.value('isFloating', 'false') == 'true' and True or False
        self.move(self.settings.value('pos', QtCore.QPoint(200, 200)))
        size = self.settings.value('size', QtCore.QSize(427, 690))
        if self.settings.value('tabArea', self) == 2:
            area = 'right'
        else:
            area = 'left'
        self.settings.endGroup()

        self.setDockableParameters(dockable=True, floating=is_floating, area=area, width=size.width(),
                                   height=size.height())
        self.parent().setAllowedAreas(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea | QtCore.Qt.DockWidgetArea.LeftDockWidgetArea)

        self.show()
        self.raise_()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup('ui_maya_dock')
        self.settings.setValue('pos', self.parent().pos())
        self.settings.setValue('size', self.size())
        self.settings.setValue('isFloating', self.isFloating())
        self.settings.setValue('tabArea', self.parent().parent().dockWidgetArea(self.parent()))
        print('Done ui_maya_dock settings write')
        self.settings.endGroup()
        self.deleteLater()

    def catch_maya_closing(self):

        def exiting():
            self.close()

        QtGui.QApplication.instance().aboutToQuit.connect(exiting)

    def closeEvent(self, event):
        event.accept()
        self.parent().close()
        self.parent().deleteLater()
        self.ui_main_window.close()
        self.writeSettings()


def create_ui(thread, tab_index):
    thread = tc.treat_result(thread)
    if thread.result == QtGui.QMessageBox.ApplyRole:
        retry_startup(thread, tab_index)
    else:
        if thread.isFailed():
            env_mode.set_offline()
            main_tab = Ui_DockMain(tab_index=tab_index)
        else:
            env_mode.set_online()
            main_tab = Ui_DockMain(tab_index=tab_index)

        env_inst.ui_maya_dock = main_tab
        main_tab.switch_tab(tab_index)
        main_tab.show()
        main_tab.raise_()

        if thread.result == QtGui.QMessageBox.ActionRole:
            env_inst.ui_main.open_config_dialog()


def retry_startup(thread, tab_index):
    thread.run()
    create_ui(thread, tab_index)


def startup(tab_index=None, restart=False):
    if restart:
        Ui_DockMain.restarting(tab_index)

    env_inst.ui_super = mf.get_maya_window()

    try:
        main_tab = mf.get_maya_dock_window()[0]
        main_tab.switch_tab(tab_index)
        main_tab.show()
        main_tab.raise_()
    except:
        ping_thread = tc.get_server_thread(dict(), tc.server_ping, lambda: create_ui(ping_thread, tab_index), parent=env_inst.ui_super)
        ping_thread.start()
