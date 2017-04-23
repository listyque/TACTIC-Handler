# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_main.ui'
#
# Created: Mon Jan 09 23:30:57 2017
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
"    padding: 0px;\n"
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
"}\n"
"QDockWidget::title{\n"
"    padding: 0px;\n"
"}\n"
"QDockWidget::close-button, QDockWidget::float-button {\n"
"    padding: 0px;\n"
"}")
        MainWindow.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        MainWindow.setWindowFilePath("")
        MainWindow.setDockNestingEnabled(True)
        MainWindow.setDockOptions(QtGui.QMainWindow.AllowNestedDocks|QtGui.QMainWindow.AllowTabbedDocks|QtGui.QMainWindow.AnimatedDocks)
        self.mainwidget = QtGui.QWidget(MainWindow)
        self.mainwidget.setObjectName("mainwidget")
        MainWindow.setCentralWidget(self.mainwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 427, 21))
        self.menubar.setObjectName("menubar")
        self.menuConfig = QtGui.QMenu(self.menubar)
        self.menuConfig.setObjectName("menuConfig")
        self.menuProject = QtGui.QMenu(self.menubar)
        self.menuProject.setTearOffEnabled(True)
        self.menuProject.setObjectName("menuProject")
        MainWindow.setMenuBar(self.menubar)
        self.actionConfiguration = QtGui.QAction(MainWindow)
        self.actionConfiguration.setObjectName("actionConfiguration")
        self.actionUpdate = QtGui.QAction(MainWindow)
        self.actionUpdate.setObjectName("actionUpdate")
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionApply_to_all_Tabs = QtGui.QAction(MainWindow)
        self.actionApply_to_all_Tabs.setObjectName("actionApply_to_all_Tabs")
        self.actionServerside_Script = QtGui.QAction(MainWindow)
        self.actionServerside_Script.setObjectName("actionServerside_Script")
        self.actionDock_undock = QtGui.QAction(MainWindow)
        self.actionDock_undock.setObjectName("actionDock_undock")
        self.menuConfig.addAction(self.actionConfiguration)
        self.menuConfig.addAction(self.actionApply_to_all_Tabs)
        self.menuConfig.addAction(self.actionDock_undock)
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionServerside_Script)
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionUpdate)
        self.menuConfig.addSeparator()
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionExit)
        self.menubar.addAction(self.menuConfig.menuAction())
        self.menubar.addAction(self.menuProject.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "TACTIC handler", None, QtGui.QApplication.UnicodeUTF8))
        self.menuConfig.setTitle(QtGui.QApplication.translate("MainWindow", "Menu", None, QtGui.QApplication.UnicodeUTF8))
        self.menuProject.setTitle(QtGui.QApplication.translate("MainWindow", "Project", None, QtGui.QApplication.UnicodeUTF8))
        self.actionConfiguration.setText(QtGui.QApplication.translate("MainWindow", "Configuration", None, QtGui.QApplication.UnicodeUTF8))
        self.actionUpdate.setText(QtGui.QApplication.translate("MainWindow", "Update", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExit.setText(QtGui.QApplication.translate("MainWindow", "Exit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionApply_to_all_Tabs.setText(QtGui.QApplication.translate("MainWindow", "Current view to All Tabs", None, QtGui.QApplication.UnicodeUTF8))
        self.actionServerside_Script.setText(QtGui.QApplication.translate("MainWindow", "Serverside Script", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDock_undock.setText(QtGui.QApplication.translate("MainWindow", "Dock/undock", None, QtGui.QApplication.UnicodeUTF8))

