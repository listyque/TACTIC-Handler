# tactic_api_client.py
# Start here to run client for tactic api

import sys
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore as QtCore
from thlib.side.Qt import QtNetwork as QtNetwork

import main_standalone
import thlib.global_functions as gf
import thlib.ui_classes.ui_tactic_api_client_classes as ui_tactic_api_client_classes


class QSingleApplication(QtGui.QApplication):

    def singleStart(self, mainWindow):
        self.mainWindow = mainWindow

        # Socket
        self.m_socket = QtNetwork.QLocalSocket()
        self.m_socket.connected.connect(self.connectToExistingApp)
        self.m_socket.error.connect(self.startApplication)
        self.m_socket.connectToServer(self.applicationName(), QtCore.QIODevice.WriteOnly)

    def connectToExistingApp(self):
        print 'CONNECTING TO EXISTING APP AS IT ALREADY RUNNING'
        print 'so quit now'
        sys.exit()

    def startApplication(self):
        print 'STARTING APP ON ERROR CONNECTION'
        self.m_server = QtNetwork.QLocalServer()
        if self.m_server.listen(self.applicationName()):
            self.m_server.newConnection.connect(self.getNewConnection)
        else:
            QtGui.QMessageBox.critical(None, self.tr('Error'), self.tr('Error listening the socket.'))

    def getNewConnection(self):
        new_socket = self.m_server.nextPendingConnection()

        new_socket.readyRead.connect(lambda: self.readSocket(new_socket))
        new_socket.readChannelFinished.connect(lambda: self.socketReadFinished(new_socket))

    def socketReadFinished(self, socket):
        #socket.open(QtCore.QIODevice.ReadWrite)
        #socket.write('ASD')
        #print socket.fullServerName()
        socket.flush()
        socket.write('ASD')
        #socket.deleteLater()

    def readSocket(self, new_socket):
        new_socket.waitForReadyRead(20000)
        f = new_socket.readAll()
        print 'PRINTING'
        self.mainWindow.getArgsFromOtherInstance(f)


@gf.catch_error
def startup():
    app = QSingleApplication(sys.argv)
    app.setApplicationName('TacticHandler_TacticApiClient')
    app.setStyle('plastique')

    main_standalone.setPaletteFromDct(main_standalone.palette)

    main_window = ui_tactic_api_client_classes.Ui_TacticApiClient()

    app.singleStart(main_window)
    main_window.setHidden(True)

    sys.exit(app.exec_())


if __name__ == '__main__':
    startup()

# from PySide2 import QtNetwork as QtNetwork
# from PySide2 import QtCore as QtCore
#
#
# from cPickle import dumps
# import binascii
#
# for i in range(100):
#     m_socket = QtNetwork.QLocalSocket()
#     m_socket.connectToServer('TacticHandler_TacticApiClient', QtCore.QIODevice.WriteOnly)
#     asd = []
#     for i in range(1000000):
#         asd.append('asd')
#
#     assa = dumps(asd)
#
#     m_socket.write(binascii.b2a_hex(assa))
#     m_socket.waitForBytesWritten(20000);
