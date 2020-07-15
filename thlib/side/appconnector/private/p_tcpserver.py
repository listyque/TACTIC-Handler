import uuid
from ..qt import QtNetwork, QtCore
from .p_socket import Socket
from .p_logger import logger
from .p_connection import Connection


class TcpServer(QtNetwork.QTcpServer):

    accepted = QtCore.Signal(Connection)
    connected = QtCore.Signal(Connection)
    disconnected = QtCore.Signal(Connection)
    received = QtCore.Signal(Connection, QtCore.QByteArray)

    def __init__(self, *args, **kwargs):

        """
        initialise server
        """

        super(TcpServer, self).__init__(*args, **kwargs)

        self._client_map = {}

    def incomingConnection(self, ptr):

        """
        handle incoming connection

        :param ptr: socket descriptor (long)
        """

        logger.debug("handle new incoming connection " + repr(ptr))

        socket = Socket()
        socket.setSocketDescriptor(ptr)

        con = Connection(socket)

        self._client_map[con.key] = con

        logger.debug("accept new connection " + repr(con.key))

        con.disconnected.connect(lambda c=con: self.__delitem__(c))
        con.connected.connect(lambda c=con: self.connected.emit(c))
        con.received.connect(lambda d, c=con: self.received.emit(c, d))

        con.start()

        self.accepted.emit(con)
        self.connected.emit(con)

    def close(self):

        """
        stop server listening
        """

        key_list = list(self._client_map.keys())
        if key_list:
            logger.info("close server active connections")
            while key_list:
                key = key_list.pop()
                del self[key]

        super(TcpServer, self).close()

    def send(self, key, data):

        """
        send message to connection with given key

        :param key: key (uuid.UUID)
        :param data: (QtCore.QByteArray)
        """

        logger.debug("server send message " + repr(key))
        con = self[key]
        if con:
            con.send(data)

    def broadcast(self, data):

        """
        send broadcast message

        :param data: (QtCore.QByteArray)
        """

        logger.debug("server broadcast message")
        for key in self:
            self.send(key, data)

    def __iter__(self):

        """
        iterate connection item list

        :return: connection item (Connection)
        """

        for key in self._client_map:
            yield key

    def __getitem__(self, key):

        """
        get connection item by given key

        :param key: key (uuid.UUID)
        :return: connection item (Connection)
        """

        if not isinstance(key, uuid.UUID):
            if isinstance(key, Connection):
                key = key.key

            else:
                key = None

        if key in self._client_map:
            return self._client_map[key]

        return None

    def __delitem__(self, key):

        """
        remove connection item by given key

        :param key: key (uuid.UUID)
        """

        if not isinstance(key, uuid.UUID):
            if isinstance(key, Connection):
                key = key.key

            else:
                key = None

        if key in self._client_map:
            con = self._client_map[key]

            con.disconnected.disconnect()
            con.connected.disconnect()
            con.received.disconnect()

            self.disconnected.emit(con)
            del self._client_map[key]

            con.close()
            con.deleteLater()
            del con
