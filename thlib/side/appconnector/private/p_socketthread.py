from ..qt import QtCore
from .p_logger import logger


class SocketThread(QtCore.QThread):

    opening = QtCore.Signal(str, int)
    sending = QtCore.Signal(QtCore.QByteArray)
    closing = QtCore.Signal()

    def open(self, host, port):

        """
        handle open socket event

        :param host: host name (string)
        :param port: port (int)
        """

        logger.debug("map open connection call to thread with host " + repr(host) + " and port " + repr(port))
        self.opening.emit(host, port)

    def send(self, data):

        """
        handle send data event

        :param data: data (QtCore.QByteArray)
        """

        logger.debug("map send data call to thread")
        self.sending.emit(data)

    def close(self):

        """
        handle close event
        """

        self.closing.emit()
