from multiprocessing.connection import Listener

from thlib.side.Qt import QtWidgets as QtGui

import thlib.ui_classes.ui_float_notify_classes as ui_float_notify_classes
import thlib.global_functions as gf
from thlib.environment import env_inst


class Ui_TacticApiClient(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()
        # self.listen()

    def getArgsFromOtherInstance(self, args):
        # print args
        from cPickle import loads
        import binascii

        print loads(binascii.a2b_hex(args))
        # QtGui.QMessageBox.information(self, self.tr("Received args from another instance"), args)

    def create_ui(self):
        print 'CREATING UI'
        self.mainwidget = QtGui.QWidget(self)
        self.mainwidget.setObjectName("mainwidget")
        self.setCentralWidget(self.mainwidget)

        self.create_float_notify()

    def create_float_notify(self):
        self.float_notify = ui_float_notify_classes.Ui_floatNotifyWidget(self)
        self.float_notify.show()
        self.float_notify.setSizeGripEnabled(True)

    def listen(self):

        def listen_agent():
            from array import array

            address = ('localhost', 6000)  # family is deduced to be 'AF_INET'
            listener = Listener(address, authkey='secret password')

            conn = listener.accept()
            print 'connection accepted from', listener.last_accepted

            conn.send([2.25, None, 'junk', float])

            conn.send_bytes('hello')

            conn.send_bytes(array('i', [42, 1729]))

            conn.close()
            listener.close()

            return 'Done'

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        worker = gf.get_thread_worker(
            listen_agent,
            env_inst.get_thread_pool('server_query/server_thread_pool'),
            self.create_ui,
            gf.error_handle
        )

        worker.start()

