import ctypes
from ..qt import QtCore, QtNetwork
from .p_logger import logger


class Socket(type(QtCore.QObject)):

    def __new__(cls, name, bases, attrs):

        """
        create new class instance
        """

        # signals
        attrs["received"] = QtCore.Signal(QtCore.QByteArray)
        attrs["sent"] = QtCore.Signal(QtCore.QByteArray)

        # methods
        attrs["__init__"] = Socket.__init_override__
        attrs["_buffer_remove"] = Socket._buffer_remove
        attrs["_buffer_update"] = Socket._buffer_update
        attrs["recv"] = Socket.recv
        attrs["send"] = Socket.send
        attrs["open"] = Socket.open
        attrs["close"] = Socket.close
        attrs["setup"] = Socket.setup

        return super(Socket, cls).__new__(cls, name, bases, attrs)

    @staticmethod
    def setup(obj):

        """
        setup
        """

        pass

    @staticmethod
    def __init_override__(obj, *args, **kwargs):

        """
        initialise socket object
        """

        logger.debug("initialise socket object")
        super(obj.__class__, obj).__init__(*args, **kwargs)

        obj._message_size = 0
        obj._message_remaining_size = 0

        obj._packet_data = QtCore.QByteArray()
        obj._packet_stream = QtCore.QDataStream(obj._packet_data, QtCore.QIODevice.ReadWrite)
        obj._packet_stream.setVersion(QtCore.QDataStream.Qt_4_7)

        obj._buffer_data = QtCore.QByteArray()
        obj._buffer_stream = QtCore.QDataStream(obj._buffer_data, QtCore.QIODevice.ReadWrite)
        obj._buffer_stream.setVersion(QtCore.QDataStream.Qt_4_7)

        obj.readyRead.connect(obj.recv)

        obj._close = False
        obj.setup()

    @staticmethod
    def open(obj, host, port):

        """
        open connection

        :param host: host name (str)
        :param port: port (int)
        """

        if port == -1:
            obj.connectToServer(host)

        else:
            obj.connectToHost(host, port)

    @staticmethod
    def close(obj):

        """
        close connection
        """

        if obj.state() != QtNetwork.QAbstractSocket.UnconnectedState:
            if isinstance(obj, QtNetwork.QLocalSocket) and obj.state() != QtNetwork.QAbstractSocket.ClosingState:
                if not obj._close:
                    obj._close = True
                    super(obj.__class__, obj).disconnectFromServer()

                else:
                    obj._close = False
                    super(obj.__class__, obj).close()

            else:
                super(obj.__class__, obj).close()

    @staticmethod
    def _buffer_remove(obj, size):

        """
        remove first buffer stream data by given size

        :param size: size (int)
        """

        if size:
            logger.debug("buffer remove begin " + str(size) + " from " + repr(obj._buffer_data.size()))
            obj._buffer_stream.device().seek(0)
            replace_raw_data = obj._buffer_stream.readRawData(obj._buffer_data.size())
            replace_data = QtCore.QByteArray.fromRawData(replace_raw_data)

            replace_stream = QtCore.QDataStream(replace_data)
            replace_stream.skipRawData(size)

            obj._buffer_data.clear()
            obj._buffer_stream.device().reset()

            obj._buffer_update(replace_stream)
            logger.debug("buffer remove is done " + repr(obj._buffer_data.size()))

    @staticmethod
    def _buffer_update(obj, stream):

        """
        update buffer stream from data stream

        :param stream: data stream (QDataStream)
        """

        if stream.device().bytesAvailable():
            logger.debug("buffer update begin from " + repr(obj._buffer_data.size()))
            obj._buffer_stream.device().seek(obj._buffer_data.size())

            buffer_raw_size = stream.device().bytesAvailable()
            buffer_raw_data = stream.readRawData(buffer_raw_size)
            obj._buffer_stream.device().write(QtCore.QByteArray.fromRawData(buffer_raw_data))
            obj._buffer_stream.device().seek(0)
            logger.debug("buffer update done to " + repr(obj._buffer_data.size()))

    @staticmethod
    def recv(obj):

        """
        receive data
        """

        logger.debug("socket object handle receive event")

        stream = QtCore.QDataStream(obj)
        stream.setVersion(QtCore.QDataStream.Qt_4_7)

        while True:
            # get message size and reset message stream
            if not obj._message_size:
                if obj._buffer_stream.device().bytesAvailable():
                    if obj._buffer_stream.device().bytesAvailable() < ctypes.sizeof(ctypes.c_uint64):
                        logger.debug("header data is too small for receiving from buffer, waiting for the next message")
                        break

                    obj._message_size = obj._buffer_stream.readUInt64()
                    obj._message_remaining_size = obj._message_size
                    logger.info("wait for message with size " + repr(obj._message_size) + " (buffer)")

                else:
                    if obj.bytesAvailable() < ctypes.sizeof(ctypes.c_uint64):
                        logger.debug("header data is too small for receiving from stream, waiting for the next message")
                        break

                    obj._message_size = stream.readUInt64()
                    obj._message_remaining_size = obj._message_size
                    logger.info("wait for message with size " + repr(obj._message_size) + " (stream)")

                obj._packet_data.clear()
                obj._packet_stream.device().reset()
                obj._packet_stream.writeUInt64(obj._message_size)

            if obj._message_size:
                # get available data for the current block
                if obj._buffer_stream.device().bytesAvailable():
                    block_raw_size = obj._buffer_stream.device().bytesAvailable()

                else:
                    block_raw_size = obj.bytesAvailable()

                if block_raw_size > obj._message_remaining_size:
                    block_raw_size = obj._message_remaining_size

                if block_raw_size:
                    obj._message_remaining_size -= block_raw_size

                    if obj._buffer_stream.device().bytesAvailable():
                        block_raw_data = obj._buffer_stream.readRawData(block_raw_size)

                    else:
                        block_raw_data = stream.readRawData(block_raw_size)

                    # get message
                    obj._packet_stream.device().write(QtCore.QByteArray.fromRawData(block_raw_data))

                    if obj._packet_data.size() - ctypes.sizeof(ctypes.c_uint64) == obj._message_size:
                        obj._packet_stream.device().seek(0)
                        size = obj._packet_stream.readUInt64()
                        message = QtCore.QByteArray()
                        obj._packet_stream >> message

                        obj._message_size = 0

                        logger.info("received message with size " + repr(size))
                        obj.received.emit(message)

                else:
                    logger.debug("received empty packet")

                    # buffer remove
                    obj._buffer_remove(obj._buffer_stream.device().pos())

                    # buffer update
                    obj._buffer_update(stream)

                    break

            else:
                logger.debug("received empty data")

            # buffer remove
            obj._buffer_remove(obj._buffer_stream.device().pos())

            # buffer update
            obj._buffer_update(stream)

        # buffer update
        obj._buffer_update(stream)

    @staticmethod
    def send(obj, data):

        """
        send data

        :param data - data (serializable data)

        :return - is sending done (bool)
        """

        logger.debug("socket object handle send event")

        done = True

        block = QtCore.QByteArray()
        stream = QtCore.QDataStream(block, QtCore.QIODevice.WriteOnly)
        stream.setVersion(QtCore.QDataStream.Qt_4_7)
        stream.writeUInt64(0)
        byte_data = QtCore.QByteArray(bytes(data))
        stream << byte_data
        stream.device().seek(0)
        size = block.size() - ctypes.sizeof(ctypes.c_uint64)
        stream.writeUInt64(size)
        stream.device().seek(block.size())
        stream.writeUInt64(0)

        s = 0
        while s < block.size():
            if obj.state() != QtNetwork.QAbstractSocket.ConnectedState:
                logger.warning("socket object close connection while sending data. data sending stopped")
                done = False
                break

            logger.debug("socket object sending next data block")
            w = obj.write(block)
            s += w

        if done:
            logger.debug("socket object send event is done")
            obj.sent.emit(byte_data)

        else:
            logger.warning("socket object can`t send data")

        return done
