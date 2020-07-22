import six
from ..qt import QtCore, QtNetwork
from .p_socket import Socket


@six.add_metaclass(Socket)
class TcpSocket(QtNetwork.QTcpSocket):

    pass
