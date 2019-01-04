# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tactic/ui_my_tactic.ui'
#
# Created: Thu Apr 27 14:15:15 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore


class Ui_myTactic(object):
    def setupUi(self, myTactic):
        myTactic.setObjectName("myTactic")
        myTactic.resize(206, 43)
        self.verticalLayout = QtGui.QVBoxLayout(myTactic)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mainTab = QtGui.QTabWidget(myTactic)
        self.mainTab.setDocumentMode(True)
        self.mainTab.setObjectName("mainTab")
        self.tasksTab = QtGui.QWidget()
        self.tasksTab.setObjectName("tasksTab")
        self.tasksTabLayout = QtGui.QVBoxLayout(self.tasksTab)
        self.tasksTabLayout.setSpacing(0)
        self.tasksTabLayout.setContentsMargins(0, 0, 0, 0)
        self.tasksTabLayout.setObjectName("tasksTabLayout")
        self.mainTab.addTab(self.tasksTab, "")
        self.notificationsTab = QtGui.QWidget()
        self.notificationsTab.setObjectName("notificationsTab")
        self.notificationsTabLayout = QtGui.QVBoxLayout(self.notificationsTab)
        self.notificationsTabLayout.setSpacing(0)
        self.notificationsTabLayout.setContentsMargins(0, 0, 0, 0)
        self.notificationsTabLayout.setObjectName("notificationsTabLayout")
        self.mainTab.addTab(self.notificationsTab, "")
        self.verticalLayout.addWidget(self.mainTab)

        self.retranslateUi(myTactic)
        self.mainTab.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(myTactic)

    def retranslateUi(self, myTactic):
        myTactic.setWindowTitle(QtGui.QApplication.translate("myTactic", "Form", None))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tasksTab), QtGui.QApplication.translate("myTactic", "Tasks", None))
        self.mainTab.setTabText(self.mainTab.indexOf(self.notificationsTab), QtGui.QApplication.translate("myTactic", "Notifications", None))

