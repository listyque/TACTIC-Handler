from .qt import QtCore, QtNetwork
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

        super(Server, self).__init__()

        self.host = host
        self.port = port

        self._attempt_timer = QtCore.QTimer(self)
        self._attempt_timer.setSingleShot(True)
        self._attempt_timer.timeout.connect(self.start)
        self._attempt_count = 0
        self._attempt_limit = 3
        self._attempt_timeout = 30

        self._server = None

    @property
    def is_listening(self):

        """
        is listening

        :return: server is active and listening for the new connection (bool)
        """

        return self._server and self._server.isListening() or False

    def start(self):

        """
        start server listening
        """

        if self._server is None:
            self._server = TcpServer(self)

            self._server.accepted.connect(self.accepted.emit)
            self._server.connected.connect(self.connected.emit)
            self._server.received.connect(self.received.emit)
            self._server.disconnected.connect(self.disconnected.emit)

        if not self._server.isListening():
            logger.info("begin server listening")
            if self.port != 0 and self.host != "":
                port = self.port
                host = QtNetwork.QHostAddress(self.host)

                while True:
                    logger.info("begin server listening on " + repr(host) + " " + repr(port))
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

        self.finished.emit()
        if self._server:
            logger.info("stop server listening")
            self._server.close()
            self._server.deleteLater()
            del self._server
            self._server = None

        else:
            logger.warning("server is already stopped")

    def send(self, key, data):

        """
        send message to connection with given key

        :param key: key (uuid.UUID)
        :param data: (QtCore.QByteArray)
        """

        logger.debug("server send message " + repr(key))
        self._server.send(key, data)

    def broadcast(self, data):

        """
        send broadcast message

        :param data: (QtCore.QByteArray)
        """

        logger.debug("server broadcast message")
        self._server.broadcast(data)

    def __getitem__(self, key):

        """
        get connection item by given key

        :param key: key (uuid.UUID)
        :return: connection item (Connection)
        """

        if self._server:
            return self._server[key]

        return None

    def __iter__(self):

        """
        iterate connection item list

        :return: connection item (Connection)
        """

        if self._server:
            for key in self._server:
                yield key
