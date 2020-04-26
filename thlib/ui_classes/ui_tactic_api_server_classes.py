from thlib.side.Qt import QtCore
from thlib.side.Qt import QtWidgets as QtGui

import thlib.ui_classes.ui_float_notify_classes as ui_float_notify_classes
from thlib.ui_classes.ui_custom_qwidgets import Ui_debugLogWidget
from thlib.ui_classes.ui_script_editor_classes import Ui_ScriptEditForm
import thlib.tactic_classes as tc
from thlib.environment import env_inst, env_api, dl


class Ui_TacticApiClient(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

    def create_ui(self):

        self.mainwidget = QtGui.QWidget(self)
        self.mainwidget.setObjectName("mainwidget")
        self.setCentralWidget(self.mainwidget)

        tc.get_all_projects_and_logins()

        self.create_float_notify()

        self.create_debuglog_widget()
        self.create_script_editor_widget()

        # Spawning api listener server
        dl.log('Spawning api listener Server')
        print 'Spawning api listener Server'
        env_api.spawn_api_server(self)

    def create_float_notify(self):
        self.float_notify = ui_float_notify_classes.Ui_floatNotifyWidget(self)
        # self.float_notify.show()
        self.float_notify.setSizeGripEnabled(True)

    def create_debuglog_widget(self):
        env_inst.ui_debuglog = Ui_debugLogWidget(self.float_notify)
        env_inst.ui_debuglog.setWindowState(QtCore.Qt.WindowMinimized)

        env_inst.ui_debuglog.show()
        env_inst.ui_debuglog.hide()
        env_inst.ui_debuglog.setWindowState(QtCore.Qt.WindowNoState)

    def create_script_editor_widget(self):
        env_inst.ui_script_editor = Ui_ScriptEditForm(self.float_notify)
        env_inst.ui_script_editor.setWindowState(QtCore.Qt.WindowMinimized)

        env_inst.ui_script_editor.show()
        env_inst.ui_script_editor.hide()
        env_inst.ui_script_editor.setWindowState(QtCore.Qt.WindowNoState)
