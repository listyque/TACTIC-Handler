# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_my_tactic.ui'
#
# Created: Tue Feb 16 16:38:41 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

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
        myTactic.setWindowTitle(QtGui.QApplication.translate("myTactic", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.mainTab.setTabText(self.mainTab.indexOf(self.tasksTab), QtGui.QApplication.translate("myTactic", "Tasks", None, QtGui.QApplication.UnicodeUTF8))
        self.mainTab.setTabText(self.mainTab.indexOf(self.notificationsTab), QtGui.QApplication.translate("myTactic", "Notifications", None, QtGui.QApplication.UnicodeUTF8))

