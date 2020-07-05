from thlib.side.Qt import QtNetwork
from .p_socket import Socket
from .p_logger import logger


class TcpServer(QtNetwork.QTcpServer):

    def incomingConnection(self, ptr):

        """
        handle incoming connection

        :param ptr: socket descriptor (long)
        """

        logger.debug("handle new incoming connection " + repr(ptr))

        socket = Socket(self)
        socket.setSocketDescriptor(ptr)
        self.addPendingConnection(socket)
