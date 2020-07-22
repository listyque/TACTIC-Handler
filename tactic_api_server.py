# tactic_api_client.py
# Start here to run client for tactic api

import sys
import datetime
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore as QtCore
from thlib.side.Qt import QtNetwork as QtNetwork

import main_standalone
import thlib.global_functions as gf
from thlib.environment import env_mode, env_inst, dl
import thlib.ui_classes.ui_tactic_api_server_classes as ui_tactic_api_server_classes


class QSingleApplication(QtGui.QApplication):

    def start_single(self, main_window):
        self.main_window = main_window

        # Creating local Socket
        self.socket = QtNetwork.QLocalSocket()

        # socket Actions
        self.socket.connected.connect(self.connected_to_server)
        self.socket.error.connect(self.start_app)

        # Trying to connect to existing, previeous executed server
        self.socket.connectToServer(self.applicationName(), QtCore.QIODevice.ReadOnly)

    def connected_to_server(self):
        sys.exit()

    def start_app(self):

        self.server = QtNetwork.QLocalServer()
        listen = self.server.listen(self.applicationName())
        if listen:
            self.server.newConnection.connect(self.handle_new_connections)
        else:
            QtGui.QMessageBox.critical(None, self.tr('Error'), self.tr('Error listening the socket.'))

        self.main_window.create_ui()

    def handle_new_connections(self):
        print('Checking for the Server is Up')
        incom_socket = self.server.nextPendingConnection()

        incom_socket.readyRead.connect(lambda: self.readSocket(incom_socket))

    def readSocket(self, new_socket):

        new_socket.waitForReadyRead(20000)
        new_socket.readAll()


@gf.catch_error
def startup():

    env_inst.ui_super = QSingleApplication(sys.argv)
    env_inst.ui_super.setApplicationName('TacticHandler_TacticApiServer')
    if env_mode.qt5:
        env_inst.ui_super.setStyle('fusion')
    else:
        env_inst.ui_super.setStyle('plastique')

    env_mode.set_mode('api_server')

    date_str = datetime.date.strftime(dl.session_start, '%d_%m_%Y_%H_%M_%S')
    stdout_path = u'{0}/log/api_server_stdout_{1}.log'.format(env_mode.get_current_path(), date_str)
    sys.stdout = open(stdout_path, 'w')

    main_standalone.setPaletteFromDct(main_standalone.palette)

    env_inst.ui_super.start_single(ui_tactic_api_server_classes.Ui_TacticApiClient())

    sys.exit(env_inst.ui_super.exec_())


if __name__ == '__main__':
    startup()
