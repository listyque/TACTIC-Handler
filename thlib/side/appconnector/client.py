from .qt import QtCore, QtNetwork, __qt_version_info__
from .private.p_tcpsocket import TcpSocket
from .private.p_localsocket import LocalSocket
from .private.p_socketthread import SocketThread
from .private.p_logger import logger


class Client(QtCore.QObject):

    connected = QtCore.Signal()
    disconnected = QtCore.Signal()
    errorOccurred = QtCore.Signal(QtNetwork.QAbstractSocket.SocketError)
    received = QtCore.Signal(QtCore.QByteArray)
    sent = QtCore.Signal(QtCore.QByteArray)

    def __init__(self, host="127.0.0.1", port=8080, local=None):

        """
        initialise client object
        """

        logger.debug("initialise client object")

        super(Client, self).__init__()

        self.host = host
        self.port = not local and port or 0

        self._socket = None
        self._thread = None

        self._attempt_timer = QtCore.QTimer(self)
        self._attempt_timer.setSingleShot(True)
        self._attempt_timer.timeout.connect(self.check_connection)

        self._manual_close = False

        self.keep_alive = True

    def error_occurred_slot(self, error):

        """
        handle error

        :param error: error (QAbstractSocket::SocketError)
        """

        if self._socket:
            logger.warning("handle client error " + repr(self._socket.errorString()))

        else:
            logger.warning("no client socket found")

        self.errorOccurred.emit(error)
        self.disconnected_slot()

    def disconnected_slot(self):

        """
        disconnected slot
        """

        self.disconnected.emit()
        if self.keep_alive and not self._manual_close:
            self._attempt_timer.start(3000)

    def check_connection(self):

        """
        check connection
        """

        if self.keep_alive and not self._manual_close:
            logger.debug("restore connection")
            if self.is_connected:
                self.abort()

            self.open()

    @property
    def is_connected(self):

        """
        is connected

        :return - is connected state (bool)
        """

        return self.state == QtNetwork.QAbstractSocket.ConnectedState

    @property
    def state(self):

        """
        get socket connection state

        :return - connection state (QtNetwork.QAbstractSocket.ConnectionState)
        """

        if self._socket is not None:
            return self._socket.state()

        return QtNetwork.QAbstractSocket.UnconnectedState

    def open(self, host=None, port=None, force=False):

        """
        open connection
        :param host - host name (string)
        :param port - port (int)
        :param force - force re-connect (bool)

        :return - connection state (bool)
        """

        logger.debug("open client connection")

        self._manual_close = False

        if not host or not port:
            if not host:
                host = self.host

            if not port:
                port = self.port

        update = self._socket is None
        if host != self.host or port != self.port:
            update = True

        if self.is_connected:
            if force or update:
                self.close()

            else:
                return True

        if update:
            logger.debug("update client connection parameters")
            self.host = host
            self.port = port

        is_local = self.port < 1
        if self._socket is not None:
            self._socket.close()

        if is_local:
            self._socket = LocalSocket()

        else:
            self._socket = TcpSocket()

        self._socket.received.connect(self.received)
        self._socket.sent.connect(self.sent)
        self._socket.disconnected.connect(self.disconnected_slot)
        self._socket.connected.connect(self.connected.emit)
        if __qt_version_info__ < (5, 15):
            self._socket.error.connect(self.error_occurred_slot)
        else:
            self._socket.errorOccurred.connect(self.error_occurred_slot)

        self._thread = SocketThread(self)

        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.opening.connect(self._socket.open)
        self._thread.sending.connect(self._socket.send)
        self._thread.closing.connect(self._socket.close)

        self._socket.moveToThread(self._thread)

        self._thread.start()

        logger.info("open client connection to host " + repr(self.host) + " with port " + repr(self.port))
        self._thread.open(self.host, self.port)

    def close(self):

        """
        close connection
        """

        self._manual_close = True

        if self._socket is not None:
            logger.debug("close client connection")

            self._thread.opening.disconnect()
            self._thread.sending.disconnect()

            self._thread.close()
            self._thread.wait(10)
            self._thread.quit()
            self._thread.wait(10)

            if self._thread.isRunning():
                self._thread.terminate()

            self._thread.deleteLater()
            self._socket.close()

            self._thread = None
            self._socket = None

        else:
            logger.warning("client connection already closed")

    def abort(self):

        """
        abort connection
        """

        self._manual_close = True

        if self._socket is not None:
            logger.debug("abort client connection")
            self._socket.abort()

        else:
            logger.warning("can`t abort already closed connection")

    def send(self, data):

        """
        send data

        :param data - message data (QByteArray)
        """

        if self.is_connected:
            logger.debug("send client data to server")
            self._thread.send(data)

        else:
            logger.warning("client is not connected")
