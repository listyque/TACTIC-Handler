# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_main_tabs.ui'
#
# Created: Mon Sep 05 00:35:39 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_mainTabsForm(object):
    def setupUi(self, mainTabsForm):
        mainTabsForm.setObjectName("mainTabsForm")
        mainTabsForm.resize(137, 229)
        self.mainTabsLayout = QtGui.QVBoxLayout(mainTabsForm)
        self.mainTabsLayout.setSpacing(0)
        self.mainTabsLayout.setContentsMargins(2, 0, 2, 3)
        self.mainTabsLayout.setObjectName("mainTabsLayout")
        self.main_tabWidget = QtGui.QTabWidget(mainTabsForm)
        self.main_tabWidget.setStyleSheet("QTabWidget::pane {\n"
"    border: 0px;\n"
"}\n"
"QTabWidget::tab-bar {\n"
"    alignment: center;\n"
"}")
        self.main_tabWidget.setTabPosition(QtGui.QTabWidget.West)
        self.main_tabWidget.setObjectName("main_tabWidget")
        self.checkOutTab = QtGui.QWidget()
        self.checkOutTab.setObjectName("checkOutTab")
        self.checkOutLayout = QtGui.QVBoxLayout(self.checkOutTab)
        self.checkOutLayout.setSpacing(0)
        self.checkOutLayout.setContentsMargins(0, 0, 0, 0)
        self.checkOutLayout.setObjectName("checkOutLayout")
        self.main_tabWidget.addTab(self.checkOutTab, "")
        self.checkInTab = QtGui.QWidget()
        self.checkInTab.setObjectName("checkInTab")
        self.checkInLayout = QtGui.QVBoxLayout(self.checkInTab)
        self.checkInLayout.setSpacing(0)
        self.checkInLayout.setContentsMargins(0, 0, 0, 0)
        self.checkInLayout.setObjectName("checkInLayout")
        self.main_tabWidget.addTab(self.checkInTab, "")
        self.myTacticTab = QtGui.QWidget()
        self.myTacticTab.setObjectName("myTacticTab")
        self.myTacticLayout = QtGui.QVBoxLayout(self.myTacticTab)
        self.myTacticLayout.setSpacing(0)
        self.myTacticLayout.setContentsMargins(0, 0, 0, 0)
        self.myTacticLayout.setObjectName("myTacticLayout")
        self.main_tabWidget.addTab(self.myTacticTab, "")
        self.assetsBrowserTab = QtGui.QWidget()
        self.assetsBrowserTab.setObjectName("assetsBrowserTab")
        self.assetsBrowserLayout = QtGui.QVBoxLayout(self.assetsBrowserTab)
        self.assetsBrowserLayout.setSpacing(0)
        self.assetsBrowserLayout.setContentsMargins(0, 0, 0, 0)
        self.assetsBrowserLayout.setObjectName("assetsBrowserLayout")
        self.main_tabWidget.addTab(self.assetsBrowserTab, "")
        self.mainTabsLayout.addWidget(self.main_tabWidget)
        self.skeyLineEdit = QtGui.QLineEdit(mainTabsForm)
        self.skeyLineEdit.setObjectName("skeyLineEdit")
        self.mainTabsLayout.addWidget(self.skeyLineEdit)

        self.retranslateUi(mainTabsForm)
        self.main_tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(mainTabsForm)

    def retranslateUi(self, mainTabsForm):
        mainTabsForm.setWindowTitle(QtGui.QApplication.translate("mainTabsForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.checkOutTab), QtGui.QApplication.translate("mainTabsForm", "Checkout", None, QtGui.QApplication.UnicodeUTF8))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.checkInTab), QtGui.QApplication.translate("mainTabsForm", "Checkin", None, QtGui.QApplication.UnicodeUTF8))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.myTacticTab), QtGui.QApplication.translate("mainTabsForm", "My Tactic", None, QtGui.QApplication.UnicodeUTF8))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.assetsBrowserTab), QtGui.QApplication.translate("mainTabsForm", "Assets browser", None, QtGui.QApplication.UnicodeUTF8))
        self.skeyLineEdit.setText(QtGui.QApplication.translate("mainTabsForm", "skey://", None, QtGui.QApplication.UnicodeUTF8))

