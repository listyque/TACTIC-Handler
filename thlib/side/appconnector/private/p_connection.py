import uuid
from ..qt import QtCore, QtNetwork, __qt_version_info__
from .p_socketthread import SocketThread
from .p_logger import logger


class Connection(QtCore.QObject):

    connected = QtCore.Signal(uuid.UUID)
    disconnected = QtCore.Signal(uuid.UUID)
    received = QtCore.Signal(uuid.UUID, QtCore.QByteArray)
    sent = QtCore.Signal(uuid.UUID, QtCore.QByteArray)
    errorOccurred = QtCore.Signal(uuid.UUID, QtNetwork.QAbstractSocket.SocketError)

    def __init__(self, socket=None):

        """
        initialise connection object
        """

        self.key = uuid.uuid4()
        logger.debug("initialise connection object " + repr(self.key))

        super(Connection, self).__init__()

        self._thread = None
        self._socket = socket

        self._socket.received.connect(self.received_slot)
        self._socket.sent.connect(self.sent_slot)
        self._socket.disconnected.connect(self.disconnected_slot)
        self._socket.connected.connect(self.connected_slot)
        if __qt_version_info__ < (5, 15):
            self._socket.error.connect(self.error_occurred_slot)

        else:
            self._socket.errorOccurred.connect(self.error_occurred_slot)

    def received_slot(self, data):

        """
        received data slot
        """

        self.received.emit(self.key, data)

    def disconnected_slot(self):

        """
        disconnected slot
        """

        self.disconnected.emit(self.key)

    def connected_slot(self):

        """
        connected slot
        """

        self.connected.emit(self.key)

    def sent_slot(self, data):

        """
        sent slot
        """

        self.sent.emit(self.key, data)

    def error_occurred_slot(self, error):

        self.errorOccurred.emit(self.key, error)

    def start(self):

        """
        start connection thread
        """

        logger.debug("begin connection thread " + repr(self.key))

        self._thread = SocketThread(self)

        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.opening.connect(self._socket.open)
        self._thread.sending.connect(self._socket.send)
        self._thread.closing.connect(self._socket.close)

        self._socket.moveToThread(self._thread)

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

        if self._socket is not None:
            logger.debug("close connection " + repr(self.key))

            self._thread.opening.disconnect()
            self._thread.sending.disconnect()

            self._thread.close()
            self._thread.wait(10)
            self._thread.quit()
            self._thread.wait(10)

            self._thread = None
            self._socket = None

        else:
            logger.warning("can`t close already closed connection " + repr(self.key))

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

        logger.debug("send data to connection " + repr(self.key))
        self._thread.send(data)
