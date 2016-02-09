# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_my_tactic.ui'
#
# Created: Thu Jan 28 18:03:09 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_myTactic(object):
    def setupUi(self, myTactic):
        myTactic.setObjectName("myTactic")
        myTactic.resize(655, 550)
        self.verticalLayout = QtGui.QVBoxLayout(myTactic)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tabWidget = QtGui.QTabWidget(myTactic)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_5 = QtGui.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.tabWidget.addTab(self.tab_5, "")
        self.verticalLayout.addWidget(self.tabWidget)

        self.retranslateUi(myTactic)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(myTactic)

    def retranslateUi(self, myTactic):
        myTactic.setWindowTitle(QtGui.QApplication.translate("myTactic", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("myTactic", "Tasks", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("myTactic", "Notifications", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QtGui.QApplication.translate("myTactic", "Schedule", None, QtGui.QApplication.UnicodeUTF8))

