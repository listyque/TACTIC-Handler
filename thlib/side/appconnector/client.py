from thlib.side.Qt import QtCore, QtNetwork
from .private.p_socket import Socket
from .private.p_socketthread import SocketThread
from .private.p_logger import logger


class Client(QtCore.QObject):

    connected = QtCore.Signal()
    disconnected = QtCore.Signal()
    error = QtCore.Signal(QtNetwork.QAbstractSocket.SocketError)
    received = QtCore.Signal(QtCore.QByteArray)

    def __init__(self, host="127.0.0.1", port=8080):

        """
        initialise client object
        """

        logger.debug("initialise client object")
        logger.setLevel('CRITICAL')

        super(self.__class__, self).__init__()

        self.host = host
        self.port = port

        self._socket = None
        self._thread = None

        self._manual_close = False
        self._attempt_timer = QtCore.QTimer()
        self._attempt_timer.setSingleShot(True)
        self._attempt_timer.timeout.connect(self.check_connection)
        self.keepalive = True

    def error_occurred(self, error):

        """
        handle error

        :param error: error (QAbstractSocket::SocketError)
        """

        if self._socket:
            logger.warning("handle client error " + repr(self._socket.errorString()))

        else:
            logger.warning("no client socket found")

        self._attempt_timer.start(1000)

    def check_connection(self):

        """
        check connection
        """

        if self.keepalive and not self._manual_close:
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

        if self.state != QtNetwork.QAbstractSocket.UnconnectedState and self.state != QtNetwork.QAbstractSocket.ClosingState:
            return True

        return False

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

            self._thread = SocketThread(self)

            self._socket = Socket(self)
            self._socket.disconnected.connect(self.check_connection)
            self._socket.disconnected.connect(self.disconnected.emit)
            self._socket.error.connect(self.error_occurred)
            self._socket.error.connect(self.error.emit)
            self._socket.connected.connect(self.connected.emit)
            self._socket.received.connect(self.received)

            self._socket.moveToThread(self._thread)
            self._thread.opening.connect(self._socket.connectToHost)
            self._thread.sending.connect(self._socket.send)
            self._thread.finished.connect(self._thread.deleteLater)

            self._thread.start()

        logger.info("open client connection to host " + repr(self.host) + " with port " + repr(self.port))
        self._thread.open(self.host, self.port)

    def close(self):

        """
        close connection
        """

        self._manual_close = True

        if self._socket is not None and self.is_connected:
            logger.debug("close client connection")
            self._socket.moveToThread(QtCore.QThread.currentThread())
            self._socket.close()
            self._socket.deleteLater()
            self._socket = None

        else:
            logger.warning("client connection already closed")

        if self._thread is not None:
            logger.debug("cancel client connection thread")
            if self._thread.isRunning():
                self._thread.exit(0)

            self._thread.deleteLater()
            self._thread = None

        else:
            logger.warning("client connection thread already canceled")

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
        """

        if self.is_connected:
            logger.debug("send client data to server")
            self._thread.send(data)

        else:
            logger.warning("client is not connected")
