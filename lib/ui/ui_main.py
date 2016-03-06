# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_main.ui'
#
# Created: Fri Mar 04 23:06:28 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.ApplicationModal)
        MainWindow.setMinimumSize(QtCore.QSize(427, 276))
        MainWindow.setStyleSheet("QTreeView {\n"
"    show-decoration-selected: 1;\n"
"}\n"
"QTreeView::item {\n"
"    border-style: outset;\n"
"    border-width: 1px;\n"
"    border-color:  rgba(75, 75, 75, 75);\n"
"    border-radius: 1px;\n"
"    padding: 3px;\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 25), stop: 1 rgba(175, 175, 175, 0));\n"
"}\n"
"\n"
"QTreeView::item:hover {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 50), stop: 1 rgba(175, 175, 175, 0));\n"
"    border: 1px solid rgba(128, 128, 128, 75);\n"
"}\n"
"QTreeView::item:selected {\n"
"    border: 1px solid transparent;\n"
"}\n"
"QTreeView::item:selected:active{\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(0, 0, 0, 0));\n"
"    border: 1px solid transparent;\n"
"}\n"
"QTreeView::item:selected:!active {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(0, 0, 0, 0));\n"
"    border: 1px solid transparent;\n"
"}\n"
"QTreeView::item:selected{\n"
"    selection-background-color: transparent;\n"
"    border: 1px solid transparent;\n"
"}")
        MainWindow.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        MainWindow.setWindowFilePath("")
        self.mainwidget = QtGui.QWidget(MainWindow)
        self.mainwidget.setObjectName("mainwidget")
        self.main_layout = QtGui.QGridLayout(self.mainwidget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(2, 0, 2, 3)
        self.main_layout.setObjectName("main_layout")
        self.main_tabWidget = QtGui.QTabWidget(self.mainwidget)
        self.main_tabWidget.setTabPosition(QtGui.QTabWidget.South)
        self.main_tabWidget.setDocumentMode(True)
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
        self.main_layout.addWidget(self.main_tabWidget, 0, 0, 1, 3)
        self.currentProjectLabel = QtGui.QLabel(self.mainwidget)
        self.currentProjectLabel.setIndent(4)
        self.currentProjectLabel.setObjectName("currentProjectLabel")
        self.main_layout.addWidget(self.currentProjectLabel, 1, 1, 1, 1)
        self.skeyLineEdit = QtGui.QLineEdit(self.mainwidget)
        self.skeyLineEdit.setObjectName("skeyLineEdit")
        self.main_layout.addWidget(self.skeyLineEdit, 1, 0, 1, 1)
        MainWindow.setCentralWidget(self.mainwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 427, 21))
        self.menubar.setObjectName("menubar")
        self.menuConfig = QtGui.QMenu(self.menubar)
        self.menuConfig.setObjectName("menuConfig")
        MainWindow.setMenuBar(self.menubar)
        self.actionConfiguration = QtGui.QAction(MainWindow)
        self.actionConfiguration.setObjectName("actionConfiguration")
        self.actionUpdate = QtGui.QAction(MainWindow)
        self.actionUpdate.setObjectName("actionUpdate")
        self.actionVersion = QtGui.QAction(MainWindow)
        self.actionVersion.setObjectName("actionVersion")
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionApply_to_all_Tabs = QtGui.QAction(MainWindow)
        self.actionApply_to_all_Tabs.setObjectName("actionApply_to_all_Tabs")
        self.menuConfig.addAction(self.actionConfiguration)
        self.menuConfig.addAction(self.actionApply_to_all_Tabs)
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionUpdate)
        self.menuConfig.addAction(self.actionVersion)
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionExit)
        self.menuConfig.addSeparator()
        self.menubar.addAction(self.menuConfig.menuAction())

        self.retranslateUi(MainWindow)
        self.main_tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "TACTIC handler", None, QtGui.QApplication.UnicodeUTF8))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.checkOutTab), QtGui.QApplication.translate("MainWindow", "Checkout", None, QtGui.QApplication.UnicodeUTF8))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.checkInTab), QtGui.QApplication.translate("MainWindow", "Checkin", None, QtGui.QApplication.UnicodeUTF8))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.myTacticTab), QtGui.QApplication.translate("MainWindow", "My Tactic", None, QtGui.QApplication.UnicodeUTF8))
        self.main_tabWidget.setTabText(self.main_tabWidget.indexOf(self.assetsBrowserTab), QtGui.QApplication.translate("MainWindow", "Assets browser", None, QtGui.QApplication.UnicodeUTF8))
        self.currentProjectLabel.setText(QtGui.QApplication.translate("MainWindow", "Current Project:", None, QtGui.QApplication.UnicodeUTF8))
        self.skeyLineEdit.setText(QtGui.QApplication.translate("MainWindow", "skey://", None, QtGui.QApplication.UnicodeUTF8))
        self.menuConfig.setTitle(QtGui.QApplication.translate("MainWindow", "Menu", None, QtGui.QApplication.UnicodeUTF8))
        self.actionConfiguration.setText(QtGui.QApplication.translate("MainWindow", "Configuration", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUpdate.setText(QtGui.QApplication.translate("MainWindow", "Update", None, QtGui.QApplication.UnicodeUTF8))
        self.actionVersion.setText(QtGui.QApplication.translate("MainWindow", "Version", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExit.setText(QtGui.QApplication.translate("MainWindow", "Exit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionApply_to_all_Tabs.setText(QtGui.QApplication.translate("MainWindow", "Current view to All Tabs", None, QtGui.QApplication.UnicodeUTF8))

