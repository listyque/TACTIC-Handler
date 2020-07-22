import six
from ..qt import QtCore, QtNetwork
from .p_socket import Socket


@six.add_metaclass(Socket)
class LocalSocket(QtNetwork.QLocalSocket):

    pass
