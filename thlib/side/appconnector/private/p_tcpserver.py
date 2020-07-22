import six
from ..qt import QtNetwork, QtCore
from .p_server import Server


@six.add_metaclass(Server)
class TcpServer(QtNetwork.QTcpServer):

    pass
