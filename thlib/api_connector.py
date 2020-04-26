# import os
# import logging
import uuid
import ctypes

from thlib.side.Qt import QtCore, QtNetwork


class AppClient(QtCore.QObject):

    connected = QtCore.Signal()
    disconnected = QtCore.Signal()
    received = QtCore.Signal(QtCore.QByteArray)

    def __init__(self, port, host="127.0.0.1", parent=None):

        super(AppClient, self).__init__(parent)

        self.__port = port
        self.__host = host

        self.__key = None

        # temp = os.path.abspath(os.environ.get("TEMP", os.path.expanduser("~/temp"))).replace("\\", "/").rstrip("/") + "/AppConnection"
        # if not os.path.exists(temp):
        #     os.makedirs(temp)
        #
        # logging.basicConfig(filename=temp + "/AppClient_{0}.{1}.log".format(host, port), level=logging.INFO, format="%(asctime)s - %(message)s")
        # self.__logger = logging.getLogger("AppClient_{0}.{1}.log".format(host, port))

        self.__blocksize = 0
        self.__blockdata = None
        self.__blockstream = None

        self.__keep_connection = 0
        self.__connection = 0

        self.__connection_timer = QtCore.QTimer(self)
        self.__connection_attempt = 0

        self.__client = None

    def reset(self):

        self.__blocksize = 0
        self.__blockdata = None
        self.__blockstream = None

    def isConnected(self):

        if self.__client:
            state = self.__client.state()
            if state == QtNetwork.QAbstractSocket.UnconnectedState or state == QtNetwork.QAbstractSocket.ClosingState:
                return False

            return True

        return False

    def waitForReadyRead(self):

        return self.__client.waitForReadyRead()

    def waitForConnected(self):

        return self.__client.waitForConnected()

    def run(self):

        # self.__logger.info("connect to server  [{0}]".format(self.__key))
        self.__connection = 1

        if self.__client is None:
            self.__client = QtNetwork.QTcpSocket(self)
            self.__client.connected.connect(self.__connected)
            self.__client.disconnected.connect(self.__disconnected)
            self.__client.readyRead.connect(self.__received)
            self.__client.error.connect(self.__error)

        self.__client.blockSignals(False)
        self.__run()

        self.__connection_timer.timeout.connect(self.__run)
        self.__connection_timer.start(3000)

    def __run(self):

        # self.__logger.info("connect to server  [{0}]".format(self.__key))

        if self.__connection:
            state = self.__client.state()
            if state == QtNetwork.QAbstractSocket.UnconnectedState or state == QtNetwork.QAbstractSocket.ClosingState:
                self.__connection_attempt += 1
                if state == QtNetwork.QAbstractSocket.ConnectedState:
                    self.__connection_timer.stop()
                    self.__connection_attempt = 0

                elif self.__connection_attempt > 10 and not self.__keep_connection:
                    self.__client.abort()
                    self.__connection_timer.stop()
                    self.__connection_attempt = 0

                elif state == QtNetwork.QAbstractSocket.UnconnectedState or state == QtNetwork.QAbstractSocket.HostLookupState:
                    self.__client.connectToHost(QtNetwork.QHostAddress(self.__host), self.__port)

        elif self.__connection_timer.isActive():
            self.__connection_timer.stop()

    def stop(self):

        # self.__logger.info("disconnect from server [{0}]".format(self.__key))
        self.__connection = 0
        if self.__connection_timer.isActive():
            self.__connection_timer.stop()

        if self.__client:
            self.__client.blockSignals(True)
            self.__client.close()
            self.__client.deleteLater()
            del self.__client
            self.__client = None

        self.reset()

        self.blockSignals(True)
        self.deleteLater()

    def __connected(self):

        # self.__logger.info("connected to server [{0}]".format(self.__key))
        if self.__connection_timer.isActive():
            self.__connection_timer.stop()

        self.connected.emit()

    def __disconnected(self):

        # self.__logger.info("disconnected from server [{0}]".format(self.__key))

        if self.__client:
            self.__client.blockSignals(True)
            self.__client.close()
            self.__client.deleteLater()
            del self.__client
            self.__client = None

        self.reset()

        self.disconnected.emit()

        if self.__connection_timer.isActive():
            self.__connection_timer.stop()

        if self.__keep_connection and self.__connection:
            self.run()

    def __received(self):

        # self.__logger.info("receive message from server [{0}]".format(self.__key))
        if self.__client:
            stream = QtCore.QDataStream(self.__client)
            stream.setVersion(QtCore.QDataStream.Qt_4_7)

            while True:
                if not self.__client:
                    break

                if not self.__blocksize:
                    if self.__client.bytesAvailable() < ctypes.sizeof(ctypes.c_long):
                        break

                    self.__blocksize = stream.readUInt64()

                if self.__client.bytesAvailable() < self.__blocksize:
                    break

                if self.__blocksize and self.__blockdata is None:
                    self.__blockdata = QtCore.QByteArray()
                    self.__blockstream = QtCore.QDataStream(self.__blockdata, QtCore.QIODevice.ReadWrite)
                    self.__blockstream.setVersion(QtCore.QDataStream.Qt_4_7)
                    self.__blockstream.writeUInt64(self.__blocksize)

                data = QtCore.QByteArray()
                stream >> data

                if self.__blocksize:
                    self.__blockstream << data
                    if self.__blockdata.size() - ctypes.sizeof(ctypes.c_long) == self.__blocksize:
                        self.__blockstream.device().seek(0)
                        size = self.__blockstream.readUInt64()
                        message = QtCore.QByteArray()
                        self.__blockstream >> message

                        self.__blockdata = None
                        self.__blocksize = 0
                        self.__blockstream = 0

                        # system = 0
                        if message[:7] == "system:":
                            # system = 1
                            if message[:11] == "system:key:" and message.size() == 47:
                                self.__key = None
                                try:
                                    self.__key = uuid.UUID(str(message[11:]))

                                except:
                                    self.stop()

                            elif self.__key is None:
                                self.stop()

                            elif message == "system:stop":
                                self.stop()

                        # if system:
                            # self.__logger.info("received system message from server with size " + repr(size) + " [{0}]".format(self.__key))

                        else:
                            # self.__logger.info("received message from server with size " + repr(size) + " [{0}]".format(self.__key))
                            self.received.emit(message)

        # else:
            # self.__logger.warning("can`t receive message from server [{0}]".format(self.__key))

    def send(self, data):

        if self.isConnected():
            # self.__logger.info("send message to server  [{0}]".format(self.__key))
            block = QtCore.QByteArray()
            
            stream = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
            stream.setVersion(QtCore.QDataStream.Qt_4_7)
            stream.writeUInt64(0)
            stream << QtCore.QByteArray(data)
            stream.device().seek(0)
            stream.writeUInt64(block.size() - ctypes.sizeof(ctypes.c_long))
            stream.device().seek(block.size())
            stream.writeUInt64(0)

            s = 0
            while s < block.size():
                if self.__client.state() != QtNetwork.QAbstractSocket.ConnectedState:
                    # self.__logger.warning("is not connected to server [{0}]".format(self.__key))
                    break

                w = self.__client.write(block)
                s += w

        # else:
        #     self.__logger.warning("is not connected to server [{0}]".format(self.__key))

    def __error(self):

        # self.__logger.warning("error  [{0}]".format(self.__key))
        if self.__client.state() == QtNetwork.QAbstractSocket.UnconnectedState:
            restore = True

        else:
            self.__client.abort()
            restore = True

        if restore and self.__keep_connection and self.__connection:
            self.reset()
            # self.__connection_timer.timeout.connect(self.__run)
            self.__connection_timer.start(3000)
        elif self.__connection_timer.isActive():
            self.__connection_timer.stop()

    def setKeepConnection(self, value):

        if value:
            self.__keep_connection = 1

        else:
            self.__keep_connection = 0

    def keepConnection(self):

        if self.__keep_connection:
            return True

        return False


class AppServer(QtCore.QObject):

    started = QtCore.Signal()
    finished = QtCore.Signal()
    accepted = QtCore.Signal(QtNetwork.QTcpSocket)
    connected = QtCore.Signal(QtNetwork.QTcpSocket)
    disconnected = QtCore.Signal(QtNetwork.QTcpSocket)
    received = QtCore.Signal(QtNetwork.QTcpSocket, QtCore.QByteArray)

    def __init__(self, port, host="127.0.0.1", parent=None):

        super(AppServer, self).__init__(parent)

        self.__port = port
        self.__host = host

        # temp = os.path.abspath(os.environ.get("TEMP", os.path.expanduser("~/temp"))).replace("\\", "/").rstrip("/") + "/AppConnection"
        # if not os.path.exists(temp):
        #     os.makedirs(temp)
        #
        # logging.basicConfig(filename=temp + "/AppServer_{0}.{1}.log".format(host, port), level=logging.INFO, format="%(asctime)s - %(message)s")
        # self.__logger = logging.getLogger("AppServer_{0}.{1}.log".format(host, port))

        self.__client_data = {}

        self.__server_timer = QtCore.QTimer(self)
        self.__server_timer.setSingleShot(True)
        self.__server_timer.timeout.connect(self.__run)
        self.__server_attempt = 0

        self.__server = None

    def run(self):

        self.__server_attempt = 0
        self.__run()

    def __run_request(self):

        self.__server_timer.start(1000)

    # def __del__(self):
    #
    #     self.stop()

    def __run(self):

        # self.__logger.info("run server")
        if self.__server is None:
            self.__server = QtNetwork.QTcpServer(self)
            self.__server.newConnection.connect(self.__accepted)

        if not self.__server.isListening():
            if self.__port != 0 and self.__host != "":
                port = self.__port
                host = QtNetwork.QHostAddress(self.__host)

                while True:
                    listen = self.__server.listen(host, port)
                    if not listen:
                        listen = self.__server.isListening()

                    if not listen:
                        self.__server_attempt += 1
                        if self.__server_attempt == 3:
                            s_client = AppClient(self.__port, self.__host)
                            s_client.setKeepConnection(False)
                            s_client.connected.connect(lambda c=s_client: c.send("system:stop"))
                            s_client.run()
                            break

                        else:
                            self.__server.close()

                    else:
                        break

                if self.__server.isListening():
                    # self.__logger.info("server is running")
                    self.started.emit()

                elif self.__server_attempt < 3:
                    self.__server_timer.start(1000)

            else:
                # self.__logger.info("server is running")
                self.started.emit()

        else:
            # self.__logger.info("server is running")
            self.started.emit()

    def stop(self):

        # self.__logger.info("stop server")
        key_list = self.__client_data.keys()
        while key_list:
            key = key_list.pop()
            m_client = self.__client_data[key][0]
            self.send(m_client, "system:stop")
            m_client.close()
            m_client.deleteLater()
            del self.__client_data[key]

        self.finished.emit()
        if self.__server:
            self.__server.close()
            self.__server.deleteLater()
            del self.__server
            self.__server = None

    def isListening(self):

        return self.__server and self.__server.isListening() or False

    def broadcast(self, data):

        # self.__logger.info("broadcast message '%s'" % data)
        for key in self.__client_data:
            self.send(self.__client_data[key][0], data)

    def __accepted(self):

        key = uuid.uuid4()

        # self.__logger.info("accepted connection from client [{0}]".format(key))
        if self.__server:
            m_client = self.__server.nextPendingConnection()

            m_client.disconnected.connect(lambda c=m_client: self.__closed(c))
            m_client.connected.connect(lambda c=m_client: self.__connected(c))
            m_client.readyRead.connect(lambda c=m_client: self.__received(c))

            m_client.setProperty("key", key)
            self.__client_data[key] = [m_client, 0, None, None]

            # self.send(m_client, "system:key:" + str(key))

            self.accepted.emit(m_client)

        # else:
        #     self.__logger.info("can`t accept connection from client [{0}]".format(key))

    def __closed(self, m_client):

        # self.__logger.info("client closed")
        if isinstance(m_client, QtNetwork.QTcpSocket):
            self.disconnected.emit(m_client)
            key = m_client.property("key")
            del self.__client_data[key]

            m_client.deleteLater()

            # self.__logger.info("closed connection from client [{0}]".format(key))

    def __connected(self, m_client):

        # self.__logger.info("client connected")
        if isinstance(m_client, QtNetwork.QTcpSocket):
            self.connected.emit(m_client)

            # key = m_client.property("key")
            # self.__logger.info("connection from client [{0}]".format(key))

    def __received(self, m_client):

        key = m_client.property("key")

        # self.__logger.info("receive message from client  [{0}]".format(key))
        stream = QtCore.QDataStream(m_client)
        stream.setVersion(QtCore.QDataStream.Qt_4_7)

        if key in self.__client_data:
            while True:
                if not self.__client_data[key][1]:
                    if m_client.bytesAvailable() < ctypes.sizeof(ctypes.c_long):
                        break

                    self.__client_data[key][1] = stream.readUInt64()

                if m_client.bytesAvailable() < self.__client_data[key][1]:
                    break

                if self.__client_data[key][2] is None:
                    self.__client_data[key][2] = QtCore.QByteArray()
                    self.__client_data[key][3] = QtCore.QDataStream(self.__client_data[key][2], QtCore.QIODevice.ReadWrite)
                    self.__client_data[key][3].setVersion(QtCore.QDataStream.Qt_4_7)
                    self.__client_data[key][3].writeUInt64(self.__client_data[key][1])

                data = QtCore.QByteArray()
                stream >> data

                if self.__client_data[key][1]:
                    self.__client_data[key][3] << data
                    if self.__client_data[key][2].size() - ctypes.sizeof(ctypes.c_long) == self.__client_data[key][1]:
                        self.__client_data[key][3].device().seek(0)
                        size = self.__client_data[key][3].readUInt64()
                        message = QtCore.QByteArray()
                        self.__client_data[key][3] >> message

                        self.__client_data[key][2] = None
                        self.__client_data[key][3] = None
                        self.__client_data[key][1] = 0

                        # system = 0
                        if message[:7] == "system:":
                            # system = 1

                            if message[:11] == "system:key:" and message.size() == 47:
                                try:
                                    replace_key = uuid.UUID(str(message[11:]))

                                except:
                                    replace_key = key

                                if key != replace_key:
                                    # self.__logger.info("update client key from " + repr(key) + " to " + repr(replace_key))
                                    self.__client_data[replace_key] = self.__client_data[key]
                                    del self.__client_data[key]
                                    key = replace_key

                            elif message == "system:stop":
                                self.stop()

                        # if system:
                        #     self.__logger.info("received system message from client with size " + repr(size) + " [{0}]".format(key))

                        else:
                            # self.__logger.info("received message from client with size " + repr(size) + " [{0}]".format(key))
                            self.received.emit(m_client, message)

    def send(self, m_client, data):

        key = m_client.property("key")

        # self.__logger.info("send message to client [{0}]".format(key))
        block = QtCore.QByteArray()
        stream = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        stream.setVersion(QtCore.QDataStream.Qt_4_7)
        stream.writeUInt64(0)
        stream << QtCore.QByteArray(data)
        stream.device().seek(0)
        stream.writeUInt64(block.size() - ctypes.sizeof(ctypes.c_long))
        stream.device().seek(block.size())
        stream.writeUInt64(0)

        s = 0
        while s < block.size():
            if m_client.state() != QtNetwork.QAbstractSocket.ConnectedState:
                m_client.warning("is not connected to server [{0}]".format(key))
                break

            w = m_client.write(block)
            s += w
