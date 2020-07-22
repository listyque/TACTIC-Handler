import uuid
from ..qt import QtNetwork, QtCore
from .p_tcpsocket import TcpSocket
from .p_localsocket import LocalSocket
from .p_logger import logger
from .p_connection import Connection


class Server(type(QtCore.QObject)):

    def __new__(cls, name, bases, attrs):

        """
        create new class instance
        """

        # signals
        attrs["accepted"] = QtCore.Signal(uuid.UUID)
        attrs["connected"] = QtCore.Signal(uuid.UUID)
        attrs["disconnected"] = QtCore.Signal(uuid.UUID)
        attrs["received"] = QtCore.Signal(uuid.UUID, QtCore.QByteArray)
        attrs["sent"] = QtCore.Signal(uuid.UUID, QtCore.QByteArray)
        attrs["errorOccurred"] = QtCore.Signal(uuid.UUID, QtNetwork.QAbstractSocket.SocketError)

        # methods
        attrs["__init__"] = Server.__init_override__
        attrs["incomingConnection"] = Server.incomingConnection
        attrs["add"] = Server.add
        attrs["get"] = Server.get
        attrs["get"] = Server.get
        attrs["remove"] = Server.remove
        attrs["close"] = Server.close
        attrs["send"] = Server.send
        attrs["broadcast"] = Server.broadcast
        attrs["__iter__"] = Server.__iter_override__
        attrs["__getitem__"] = Server.__getitem_override__
        if "setup" not in attrs:
            attrs["setup"] = Server.setup

        return super(Server, cls).__new__(cls, name, bases, attrs)

    @staticmethod
    def setup(obj):

        """
        setup
        """

        pass

    @staticmethod
    def __init_override__(obj, *args, **kwargs):

        """
        initialise server
        """

        logger.debug("initialise server object")
        super(obj.__class__, obj).__init__(*args, **kwargs)

        obj._client_map = {}

        obj.setup()

    @staticmethod
    def incomingConnection(obj, descriptor):

        """
        handle incoming connection

        :param descriptor: socket descriptor (qintptr)
        """

        logger.debug("handle new incoming connection " + repr(descriptor))

        key = obj.add(descriptor)

        obj.connected.emit(key)

    @staticmethod
    def add(obj, descriptor):

        """
        add socket

        :param descriptor: socket descriptor (qintptr)
        """

        if isinstance(obj, QtNetwork.QLocalServer):
            socket = LocalSocket()

        else:
            socket = TcpSocket()

        socket.setSocketDescriptor(descriptor)

        connection = Connection(socket)

        obj._client_map[connection.key] = connection

        logger.debug("accept new connection " + repr(connection.key))

        connection.disconnected.connect(obj.remove)
        connection.connected.connect(obj.connected.emit)
        connection.received.connect(obj.received.emit)
        connection.sent.connect(obj.sent.emit)
        connection.errorOccurred.connect(obj.errorOccurred.emit)

        obj.accepted.emit(connection.key)
        connection.start()

        return connection.key

    @staticmethod
    def get(obj, key):

        """
        get connection

        :param key: key (uuid.UUID)
        """

        if key in obj._client_map:
            return obj._client_map[key]

        return None

    @staticmethod
    def remove(obj, key):

        """
        remove connection

        :param key: key (uuid.UUID)
        """

        if key in obj._client_map:
            connection = obj._client_map[key]

            connection.disconnected.disconnect(obj.remove)
            connection.connected.disconnect(obj.connected.emit)
            connection.received.disconnect(obj.received.emit)
            connection.sent.disconnect(obj.sent.emit)
            connection.errorOccurred.disconnect(obj.errorOccurred.emit)

            obj.disconnected.emit(key)
            del obj._client_map[key]

            connection.close()
            connection.deleteLater()
            del connection

    @staticmethod
    def close(obj):

        """
        stop server listening
        """

        key_list = list(obj._client_map.keys())
        if key_list:
            logger.info("close server active connections")
            while key_list:
                key = key_list.pop()
                obj.remove(key)

        super(obj.__class__, obj).close()

    @staticmethod
    def send(obj, key, data):

        """
        send message to connection with given key

        :param key: key (uuid.UUID)
        :param data: data (QtCore.QByteArray)
        """

        logger.debug("server send message " + repr(key))
        connection = obj[key]
        if connection:
            connection.send(data)

    @staticmethod
    def broadcast(obj, data, owner=None):

        """
        send broadcast message

        :param data: data (QtCore.QByteArray)
        :param owner: owner connection key (uuid.UUID)
        """

        logger.debug("server broadcast message")
        for key in obj:
            if key == owner:
                continue

            obj.send(key, data)

    @staticmethod
    def __iter_override__(obj):

        """
        iterate connection item list

        :return: connection item (Connection)
        """

        for key in obj._client_map:
            yield key

    @staticmethod
    def __getitem_override__(obj, key):

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

        if key in obj._client_map:
            return obj._client_map[key]

        return None
