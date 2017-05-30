# import PySide.QtGui as QtGui
# import PySide.QtCore as QtCore
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore
import lib.environment as env
import lib.ui.tasks.ui_float_notify as ui_notifications

reload(ui_notifications)


class Ui_floatNotifyWidget(QtGui.QDialog, ui_notifications.Ui_floatNotify):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')
        self.setWindowFlags(QtCore.Qt.ToolTip)
        self.update_secs = 1000

        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.setGeometry(screen.width() - size.width() - 5, screen.height() - size.height() - 45, self.width(),
                         self.height())

        # self.readSettings()

        self.createActions()
        self.createTrayIcon()
        self.setIcon()
        self.trayIcon.show()
        self.controls_actions()

    def controls_actions(self):
        self.hideToolButton.clicked.connect(self.hide)
        self.skipToolButton.clicked.connect(self.manual_update)

        self.trayIcon.activated.connect(self.show)

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.trayIcon.setIcon(icon)

    def createActions(self):
        self.updateNotify = QtGui.QAction("Updates notifications", self,
                                        triggered=self.manual_update)

        self.enableNotify = QtGui.QAction("Enable notifications", self,
                                        triggered=self.start_update)

        self.disableNotify = QtGui.QAction("Disable notifications", self,
                                        triggered=self.objectName)

        self.showNotify = QtGui.QAction("Show notify-window", self,
                                        triggered=self.show)

        self.hideNotify = QtGui.QAction("Hide notify-window", self,
                                        triggered=self.hide)

    def createTrayIcon(self):
        self.trayIconMenu = QtGui.QMenu(self)
        self.trayIconMenu.addAction(self.updateNotify)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.enableNotify)
        self.trayIconMenu.addAction(self.disableNotify)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.showNotify)
        self.trayIconMenu.addAction(self.hideNotify)

        self.trayIcon = QtGui.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)

    def manual_update(self):
        print "performing update!"
        now = QtCore.QDateTime.currentDateTimeUtc()
        self.settings.setValue("float_notify_lastUpdate", now)
        self.start_update(self.update_secs)

    def start_update(self, secs):
        print "Starting update timer for %d seconds" % secs
        try:
            self._updateTimer.stop()
        except:
            pass
        self._updateTimer = QtCore.QTimer()
        self._updateTimer.timeout.connect(self.manual_update)
        self._updateTimer.start(secs * 1000)

    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        x = event.globalX()
        y = event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x - x_w, y - y_w)

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(env.Mode.get_mode() + '/ui_main')
        self.move(self.settings.value('float_notify_pos', self.pos()))
        self.resize(self.settings.value('float_notify_size', self.size()))

        lastUpdate = self.settings.value('float_notify_lastUpdate')

        now = QtCore.QDateTime.currentDateTimeUtc()
        # update_time = 60*60*24*5
        secs = self.update_secs

        if not lastUpdate:
            # secs = abs(lastUpdate.secsTo(now))
            if secs >= self.update_secs:
                print "Update is past due at load time"
                self.manual_update()
                return
            else:
                print "Still %d seconds left from last load, until next update" % secs

        self.start_update(secs)
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode.get_mode() + '/ui_main')
        self.settings.setValue('float_notify_pos', self.pos())
        self.settings.setValue('float_notify_size', self.size())
        print('Done ui_float_notify settings write')
        self.settings.endGroup()

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()
