from ..qt import QtCore, QtNetwork
import ctypes
from .p_logger import logger


class Socket(QtNetwork.QTcpSocket):

    received = QtCore.Signal(QtCore.QByteArray)

    def __init__(self, *args):

        """
        initialise socket object
        """

        logger.debug("initialise socket object")

        super(Socket, self).__init__(*args)

        self._message_size = 0
        self._message_remaining_size = 0

        self._packet_data = QtCore.QByteArray()
        self._packet_stream = QtCore.QDataStream(self._packet_data, QtCore.QIODevice.ReadWrite)
        self._packet_stream.setVersion(QtCore.QDataStream.Qt_4_7)

        self._buffer_data = QtCore.QByteArray()
        self._buffer_stream = QtCore.QDataStream(self._buffer_data, QtCore.QIODevice.ReadWrite)
        self._buffer_stream.setVersion(QtCore.QDataStream.Qt_4_7)

        self.readyRead.connect(self.recv)

    def _buffer_remove(self, size):

        """
        remove first buffer stream data by given size

        :param size: size (int)
        """

        if size:
            logger.debug("buffer remove begin " + str(size) + " from " + repr(self._buffer_data.size()))
            self._buffer_stream.device().seek(0)
            replace_raw_data = self._buffer_stream.readRawData(self._buffer_data.size())
            replace_data = QtCore.QByteArray.fromRawData(replace_raw_data)

            replace_stream = QtCore.QDataStream(replace_data)
            replace_stream.skipRawData(size)

            self._buffer_data.clear()
            self._buffer_stream.device().reset()

            self._buffer_update(replace_stream)
            logger.debug("buffer remove is done " + repr(self._buffer_data.size()))

    def _buffer_update(self, stream):

        """
        update buffer stream from data stream

        :param stream: data stream (QDataStream)
        """

        if stream.device().bytesAvailable():
            logger.debug("buffer update begin from " + repr(self._buffer_data.size()))
            self._buffer_stream.device().seek(self._buffer_data.size())

            buffer_raw_size = stream.device().bytesAvailable()
            buffer_raw_data = stream.readRawData(buffer_raw_size)
            self._buffer_stream.device().write(QtCore.QByteArray.fromRawData(buffer_raw_data))
            self._buffer_stream.device().seek(0)
            logger.debug("buffer update done to " + repr(self._buffer_data.size()))

    def recv(self):

        """
        receive data
        """

        logger.debug("socket object handle receive event")

        stream = QtCore.QDataStream(self)
        stream.setVersion(QtCore.QDataStream.Qt_4_7)

        while True:
            # get message size and reset message stream
            if not self._message_size:
                if self._buffer_stream.device().bytesAvailable():
                    if self._buffer_stream.device().bytesAvailable() < ctypes.sizeof(ctypes.c_uint64):
                        logger.debug("header data is too small for receiving from buffer, waiting for the next message")
                        break

                    self._message_size = self._buffer_stream.readUInt64()
                    self._message_remaining_size = self._message_size
                    logger.info("wait for message with size " + repr(self._message_size) + " (buffer)")

                else:
                    if self.bytesAvailable() < ctypes.sizeof(ctypes.c_uint64):
                        logger.debug("header data is too small for receiving from stream, waiting for the next message")
                        break

                    self._message_size = stream.readUInt64()
                    self._message_remaining_size = self._message_size
                    logger.info("wait for message with size " + repr(self._message_size) + " (stream)")

                self._packet_data.clear()
                self._packet_stream.device().reset()
                self._packet_stream.writeUInt64(self._message_size)

            if self._message_size:
                # get available data for the current block
                if self._buffer_stream.device().bytesAvailable():
                    block_raw_size = self._buffer_stream.device().bytesAvailable()

                else:
                    block_raw_size = self.bytesAvailable()

                if block_raw_size > self._message_remaining_size:
                    block_raw_size = self._message_remaining_size

                if block_raw_size:
                    self._message_remaining_size -= block_raw_size

                    if self._buffer_stream.device().bytesAvailable():
                        block_raw_data = self._buffer_stream.readRawData(block_raw_size)

                    else:
                        block_raw_data = stream.readRawData(block_raw_size)

                    # get message
                    self._packet_stream.device().write(QtCore.QByteArray.fromRawData(block_raw_data))

                    if self._packet_data.size() - ctypes.sizeof(ctypes.c_uint64) == self._message_size:
                        self._packet_stream.device().seek(0)
                        size = self._packet_stream.readUInt64()
                        message = QtCore.QByteArray()
                        self._packet_stream >> message

                        self._message_size = 0

                        logger.info("received message with size " + repr(size))
                        self.received.emit(message)

                else:
                    logger.debug("received empty packet")

                    # buffer remove
                    self._buffer_remove(self._buffer_stream.device().pos())

                    # buffer update
                    self._buffer_update(stream)

                    break

            else:
                logger.debug("received empty data")

            # buffer remove
            self._buffer_remove(self._buffer_stream.device().pos())

            # buffer update
            self._buffer_update(stream)

        # buffer update
        self._buffer_update(stream)

    def send(self, data):

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
        stream << QtCore.QByteArray(bytes(data))
        stream.device().seek(0)
        size = block.size() - ctypes.sizeof(ctypes.c_uint64)
        stream.writeUInt64(size)
        stream.device().seek(block.size())
        stream.writeUInt64(0)

        s = 0
        while s < block.size():
            if self.state() != QtNetwork.QAbstractSocket.ConnectedState:
                logger.warning("socket object close connection while sending data. data sending stopped")
                done = False
                break

            logger.debug("socket object sending next data block")
            w = self.write(block)
            s += w

        if done:
            logger.debug("socket object send event is done")

        else:
            logger.warning("socket object can`t send data")

        return done
