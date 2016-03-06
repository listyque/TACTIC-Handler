# file ui_my_tactic.py
# My Tactic

import PySide.QtGui as QtGui

import lib.ui.ui_my_tactic as ui_my_tactic
import lib.ui.ui_my_notifications as ui_my_notifications
import lib.ui.ui_my_tasks as ui_my_tasks

reload(ui_my_tactic)
reload(ui_my_notifications)
reload(ui_my_tasks)


class Ui_myTacticWidget(QtGui.QWidget, ui_my_tactic.Ui_myTactic):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.create_my_notifications()
        self.create_my_tasks()

    # def prnt(self):
    #     self.create_my_notifications()

    def create_my_notifications(self):
        self.my_notifications = Ui_myNotificationsWidget(self)
        self.notificationsTabLayout.addWidget(self.my_notifications)

    def create_my_tasks(self):
        self.my_tasks = Ui_myTasksWidget(self)
        self.tasksTabLayout.addWidget(self.my_tasks)


class Ui_myNotificationsWidget(QtGui.QWidget, ui_my_notifications.Ui_myNotifications):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)


class Ui_myTasksWidget(QtGui.QWidget, ui_my_tasks.Ui_myTasks):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

