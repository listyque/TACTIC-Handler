import os
import codecs
import inspect
from thlib.side.Qt import QtCore
from thlib.side.Qt import QtWidgets as QtGui

import thlib.ui_classes.ui_float_notify_classes as ui_float_notify_classes
from thlib.ui_classes.ui_custom_qwidgets import Ui_debugLogWidget
from thlib.ui_classes.ui_script_editor_classes import Ui_ScriptEditForm
import thlib.tactic_classes as tc
import thlib.global_functions as gf
from thlib.environment import env_inst, env_api, dl

path = inspect.getfile( inspect.currentframe() )
path = path.replace("\\", "/")
parts = path.split("/tactic_handler")
base_dir = parts[0]

TACTIC_DIR = base_dir


class mayaBatchClass(QtCore.QObject):

    progress_out = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.batch_process = QtCore.QProcess(self)

        self.actions()

    def start_batch(self):
        self.batch_process.setProcessChannelMode(QtCore.QProcess.MergedChannels)

        self.batch_process.readyRead.connect(self.progress_output)

        self.batch_process.waitForReadyRead(True)

        self.batch_process.start(u'{0}/python3/App/Python/python.exe'.format(TACTIC_DIR), ['{0}/bin/startup_standalone.py'.format(TACTIC_DIR)])

    def progress_output(self):

        log_output = str(self.batch_process.readAllStandardOutput())

        self.progress_out.emit(log_output)

        self.write_log(log_output)

    def write_log(self, log_text):
        log_path = u'{0}/log_out.log'.format(TACTIC_DIR)

        if os.path.exists(gf.extract_dirname(log_path)):
            with codecs.open(log_path, 'a+', 'utf-8') as log_file:
                log_file.write(log_text)
        else:
            os.makedirs(gf.extract_dirname(log_path))
            with codecs.open(log_path, 'w+', 'utf-8') as log_file:
                log_file.write(log_text)

        log_file.close()

    def actions(self):
        self.batch_process.error.connect(self.error_handle)
        #self.batch_process.stateChanged.connect(self.state_changed_handle)
        #self.batch_process.readyRead.connect(self.progress_output)

    def error_handle(self, message=None):
        if message:
            print('Some errors', message)

class Ui_TacticServer(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

    def create_ui(self):

        self.mainwidget = QtGui.QWidget(self)
        self.mainwidget.setObjectName("mainwidget")
        self.setCentralWidget(self.mainwidget)

        # Spawning server
        dl.log('Spawning Tactic Server')
        print('Spawning Tactic Server')

        self.create_batch_object()

        self.create_float_notify()

        self.create_debuglog_widget()
        self.create_script_editor_widget()

    def create_batch_object(self):
        self.batch_object = mayaBatchClass(self)

        self.actions()
        self.batch_object.start_batch()
    
    def progress_log(self, log):
        print(log)
    
    def actions(self):
        #self.batch_object.render_finished.connect(self.batch_render_finished)
        #self.batch_object.render_interrupted.connect(self.batch_render_interrupted)
        self.batch_object.progress_out.connect(self.progress_log)
    
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
