import uuid
from thlib.side.Qt import QtCore, QtNetwork
from .p_socketthread import SocketThread
from .p_logger import logger


class Connection(QtCore.QObject):

    connected = QtCore.Signal()
    disconnected = QtCore.Signal()
    error = QtCore.Signal(QtNetwork.QAbstractSocket.SocketError)

    received = QtCore.Signal(QtCore.QByteArray)

    def __init__(self, socket=None):

        """
        initialise connection object
        """

        self.key = uuid.uuid4()
        logger.debug("initialise connection object " + repr(self.key))

        super(self.__class__, self).__init__()

        self._socket = socket
        self._thread = SocketThread(self)

        self._socket.disconnected.connect(self.disconnected.emit)
        self._socket.connected.connect(self.connected.emit)
        self._socket.error.connect(self.error.emit)
        self._socket.received.connect(self.received)

        self._socket.moveToThread(self._thread)
        self._thread.opening.connect(self._socket.connectToHost)
        self._thread.sending.connect(self._socket.send)
        self._thread.finished.connect(self._thread.deleteLater)

        logger.debug("begin connection thread " + repr(self.key))
        self._thread.start()

    @property
    def is_connected(self):

        """
        is connected

        :return - is connected state (bool)
        """

        if self._socket is not None:
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

    def close(self):

        """
        close connection
        """

        if self._socket is not None and self.is_connected:
            logger.debug("close connection " + repr(self.key))
            self._socket.moveToThread(QtCore.QThread.currentThread())
            self._socket.close()
            self._socket.deleteLater()

        else:
            logger.warning("can`t close already closed connection " + repr(self.key))

        if self._thread is not None:
            logger.debug("cancel connection thread " + repr(self.key))
            if self._thread.isRunning():
                self._thread.exit(0)

            self._thread.deleteLater()
            self._thread = None

        else:
            logger.debug("can`t cancel non-existing connection thread " + repr(self.key))

    def abort(self):

        """
        abort connection
        """

        if self._socket is not None:
            logger.debug("abort connection " + repr(self.key))
            self._socket.abort()

        else:
            logger.warning("can`t abort already closed connection " + repr(self.key))

    def send(self, data):

        """
        send data
        """

        logger.warning("send data to connection " + repr(self.key))
        self._thread.send(data)
