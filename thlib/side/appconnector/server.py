from thlib.side.Qt import QtCore, QtNetwork
import uuid
from .private.p_tcpserver import TcpServer
from .private.p_connection import Connection
from .private.p_logger import logger


class Server(QtCore.QObject):

    started = QtCore.Signal()
    finished = QtCore.Signal()
    accepted = QtCore.Signal(Connection)
    connected = QtCore.Signal(Connection)
    disconnected = QtCore.Signal(Connection)
    received = QtCore.Signal(Connection, QtCore.QByteArray)

    def __init__(self, host="127.0.0.1", port=8080):

        """
        initialise server

        :param host: host name (string)
        :param port: port (int)
        """

        logger.debug("initialise server object")
        logger.setLevel('CRITICAL')

        super(self.__class__, self).__init__()

        self.host = host
        self.port = port

        self._attempt_timer = QtCore.QTimer(self)
        self._attempt_timer.setSingleShot(True)
        self._attempt_timer.timeout.connect(self.start)
        self._attempt_count = 0
        self._attempt_limit = 3
        self._attempt_timeout = 30

        self._client_map = {}

        self._server = None

    def start(self):

        """
        start server listening
        """

        if self._server is None:
            self._server = TcpServer(self)
            self._server.newConnection.connect(self._accept)

        if not self._server.isListening():
            logger.info("begin server listening")
            if self.port != 0 and self.host != "":
                port = self.port
                host = QtNetwork.QHostAddress(self.host)

                while True:
                    listen = self._server.listen(host, port)
                    if not listen:
                        listen = self._server.isListening()

                    if not listen:
                        self._attempt_count += 1
                        if self._attempt_count >= self._attempt_limit:
                            logger.warning("waiting for server listening. next attempt in " + str(self._attempt_timeout) + " sec")
                            self._attempt_count = 0
                            self._attempt_timer.start(self._attempt_timeout * 1000)
                            return

                        else:
                            self._server.close()

                    else:
                        break

                if self._server.isListening():
                    logger.info("server is listening")
                    self.started.emit()

                elif self._attempt_count < self._attempt_limit:
                    logger.warning("waiting for server listening")
                    self._attempt_timer.start(3000)

            else:
                logger.info("server is listening")
                self.started.emit()

        else:
            logger.info("server is already listening")
            self.started.emit()

    def stop(self):

        """
        stop server listening
        """

        key_list = list(self._client_map.keys())
        if key_list:
            logger.info("close server active connections")
            while key_list:
                key = key_list.pop()
                con = self._client_map[key]

                con.disconnected.disconnect()
                con.connected.disconnect()
                con.received.disconnect()

                con.close()
                con.deleteLater()
                del self._client_map[key]
                del con

        self.finished.emit()
        if self._server:
            logger.info("stop server listening")
            self._server.close()
            self._server.deleteLater()
            del self._server
            self._server = None

        else:
            logger.warning("server is already stopped")

    @property
    def is_listening(self):

        """
        is listening

        :return: server is active and listening for the new connection (bool)
        """

        return self._server and self._server.isListening() or False

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
        for key in self._client_map:
            self._client_map[key].send(data)

    def _accept(self):

        """
        accept new connection event
        """

        if self._server is not None:
            socket = self._server.nextPendingConnection()
            con = Connection(socket)
            self._client_map[con.key] = con
            logger.debug("accept new connection " + repr(con.key))

            con.disconnected.connect(lambda c=con: self._remove(c))
            con.connected.connect(lambda c=con: self._connect(c))
            con.received.connect(lambda d, c=con: self.received.emit(c, d))

            self._connect(con)

            self.accepted.emit(con)

    def _connect(self, key):

        """
        handle connection with given key

        :param key: key (uuid.UUID)
        """

        con = self[key]
        if con:
            self.connected.emit(con)

    def _remove(self, key):

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
