# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_main_tabs.ui'
#
# Created: Mon May 29 16:20:01 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

class Ui_mainTabsForm(object):
    def setupUi(self, mainTabsForm):
        mainTabsForm.setObjectName("mainTabsForm")
        self.mainTabsLayout = QtGui.QVBoxLayout(mainTabsForm)
        self.mainTabsLayout.setSpacing(0)
        self.mainTabsLayout.setContentsMargins(2, 0, 2, 3)
        self.mainTabsLayout.setObjectName("mainTabsLayout")
        self.main_tabWidget = QtGui.QTabWidget(mainTabsForm)
        self.main_tabWidget.setStyleSheet("#main_tabWidget::pane {\n"
"    border: 0px;\n"
"}\n"
"#main_tabWidget::tab-bar {\n"
"    alignment: center;\n"
"}\n"
"\n"
"#main_tabWidget > QTabBar::tab {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 rgba(175, 175, 175, 16), stop: 1 rgba(175, 175, 175, 0));\n"
"    border: 0px solid transparent;\n"
"    border-top-left-radius: 2px;\n"
"    border-top-right-radius: 2px;\n"
"    padding: 4px;\n"
"}\n"
"#main_tabWidget > QTabBar::tab:selected, #main_tabWidget > QTabBar::tab:hover {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 rgba(255, 255, 255, 64), stop: 1 rgba(255, 255, 255, 8));\n"
"}\n"
"#main_tabWidget > QTabBar::tab:selected {\n"
"    border-color: transparent;\n"
"}\n"
"#main_tabWidget > QTabBar::tab:!selected {\n"
"    margin-left: 2px;\n"
"}")
        self.main_tabWidget.setTabPosition(QtGui.QTabWidget.West)
        self.main_tabWidget.setObjectName("main_tabWidget")
        self.checkInOutTab = QtGui.QWidget()
        self.checkInOutTab.setObjectName("checkInOutTab")
        self.checkInOutLayout = QtGui.QVBoxLayout(self.checkInOutTab)
        self.checkInOutLayout.setSpacing(0)
        self.checkInOutLayout.setContentsMargins(0, 0, 0, 0)
        self.checkInOutLayout.setObjectName("checkInOutLayout")
        self.main_tabWidget.addTab(self.checkInOutTab, "")
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
        mainTabsForm.setWindowTitle(QtGui.QApplication.translate("mainTabsForm", "Form", None))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.checkInOutTab), QtGui.QApplication.translate("mainTabsForm", "Checkin / Checkout", None))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.myTacticTab), QtGui.QApplication.translate("mainTabsForm", "My Tactic", None))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.assetsBrowserTab), QtGui.QApplication.translate("mainTabsForm", "Assets browser", None))
        self.skeyLineEdit.setText(QtGui.QApplication.translate("mainTabsForm", "skey://", None))

