from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore
from thlib.environment import env_mode, env_inst, env_tactic, env_server, dl
import thlib.global_functions as gf
# import thlib.tactic_classes as tc
import thlib.ui.tasks.ui_float_notify as ui_notifications

reload(ui_notifications)


class Ui_floatNotifyWidget(QtGui.QDialog, ui_notifications.Ui_floatNotify):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        env_inst.ui_notify = self

        self.setupUi(self)
        self.update_interval = 3

        self.create_ui()

        self.subscriptions = None
        self.messages = None

        # self.perform_update()
        # self.start_update_timer()

    def create_ui(self):
        self.setWindowFlags(QtCore.Qt.ToolTip)
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.setGeometry(screen.width() - size.width() - 5, screen.height() - size.height() - 45, self.width(),
                         self.height())

        # self.readSettings()

        self.createActions()
        self.createTrayIcon()
        self.setIcon()
        self.trayIcon.show()

        self._updateTimer = QtCore.QTimer(self)

        self.controls_actions()

    def close_app(self):
        self.close()
        self.deleteLater()

        print 'closing_app'

    def controls_actions(self):
        self.hideToolButton.clicked.connect(self.hide_notify_window)
        # self.skipToolButton.clicked.connect(self.manual_update)

        self.trayIcon.activated.connect(self.show_notify_window)
        self._updateTimer.timeout.connect(self.perform_update)

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)
        self.trayIcon.setIcon(icon)

    def createActions(self):
        # self.updateNotify = QtGui.QAction("Updates notifications", self,
        #                                 triggered=self.manual_update)
        #
        # self.enableNotify = QtGui.QAction("Enable notifications", self,
        #                                 triggered=self.start_update)

        self.show_script_editor_action = QtGui.QAction('Script Editor', self, triggered=self.show_script_editor)

        self.disableNotify = QtGui.QAction('Disable notifications', self, triggered=self.objectName)

        self.showNotify = QtGui.QAction('Show notify-window', self, triggered=self.show)

        self.hideNotify = QtGui.QAction('Hide notify-window', self, triggered=self.hide)

        self.close_app_action = QtGui.QAction('Exit', self, triggered=self.close_app)

    def createTrayIcon(self):
        self.trayIconMenu = QtGui.QMenu(self)
        # self.trayIconMenu.addAction(self.updateNotify)
        # self.trayIconMenu.addSeparator()
        # self.trayIconMenu.addAction(self.enableNotify)
        self.trayIconMenu.addAction(self.show_script_editor_action)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.disableNotify)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.showNotify)
        self.trayIconMenu.addAction(self.hideNotify)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.close_app_action)

        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)

    def show_script_editor(self):
        env_inst.ui_script_editor.show()

    def hide_notify_window(self):
        self.setHidden(True)

    def show_notify_window(self):
        self.setHidden(False)

    def updating(self, result):
        self.check_whats_changed(result)
        self.start_update_timer()

    def check_whats_changed(self, result):
        subscriptions, messages = result

        print subscriptions
        print messages

        if not self.subscriptions:
            self.subscriptions = subscriptions

        if not self.messages:
            self.messages = messages

        if self.messages != messages:
            print 'Messages changed'
            self.messages = messages

        if self.subscriptions != subscriptions:
            print 'Subscription changed'
            self.subscriptions = subscriptions

        # print subscriptions
        #
        # print messages

    def perform_update(self):

        def get_subscriptions_and_messages_agent():

            current_login = env_inst.get_current_login_object()

            return current_login.get_subscriptions_and_messages(True)

        env_inst.set_thread_pool(None, 'server_query/server_update_thread_pool')
        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        query_worker = gf.get_thread_worker(
            get_subscriptions_and_messages_agent,
            thread_pool=env_inst.get_thread_pool('server_query/server_update_thread_pool'),
            result_func=self.updating,
            error_func=self.start_update_timer
        )
        server_thread_pool = env_inst.get_thread_pool('server_query/server_thread_pool')
        if server_thread_pool.activeThreadCount() == 0:
            self.stop_update_timer()
            # print query_worker.start(priority=1)
            # for i in range(50):
            query_worker.try_start()
            # print query_worker.start()
            # print query_worker.start()

    def start_update_timer(self):
        self._updateTimer.start(self.update_interval * 1000)

    def stop_update_timer(self):
        self._updateTimer.stop()

    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        x = event.globalX()
        y = event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x - x_w, y - y_w)

    def closeEvent(self, event):
        event.accept()

    # def readSettings(self):
    #     """
    #     Reading Settings
    #     """
    #     self.settings.beginGroup(env.Mode.get_mode() + '/ui_main')
    #     self.move(self.settings.value('float_notify_pos', self.pos()))
    #     self.resize(self.settings.value('float_notify_size', self.size()))
    #
    #     lastUpdate = self.settings.value('float_notify_lastUpdate')
    #
    #     now = QtCore.QDateTime.currentDateTimeUtc()
    #     # update_time = 60*60*24*5
    #     secs = self.update_secs
    #
    #     if not lastUpdate:
    #         # secs = abs(lastUpdate.secsTo(now))
    #         if secs >= self.update_secs:
    #             print "Update is past due at load time"
    #             self.manual_update()
    #             return
    #         else:
    #             print "Still %d seconds left from last load, until next update" % secs
    #
    #     self.start_update(secs)
    #     self.settings.endGroup()
    #
    # def writeSettings(self):
    #     """
    #     Writing Settings
    #     """
    #     self.settings.beginGroup(env.Mode.get_mode() + '/ui_main')
    #     self.settings.setValue('float_notify_pos', self.pos())
    #     self.settings.setValue('float_notify_size', self.size())
    #     print('Done ui_float_notify settings write')
    #     self.settings.endGroup()
