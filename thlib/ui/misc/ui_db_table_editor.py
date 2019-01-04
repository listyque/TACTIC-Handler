# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_db_table_editor.ui'
#
# Created: Wed May 30 19:54:53 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

class Ui_editDBTable(object):
    def setupUi(self, editDBTable):
        editDBTable.setObjectName("editDBTable")
        editDBTable.resize(800, 640)
        self.centralwidget = QtGui.QWidget(editDBTable)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(9, 9, 9, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtGui.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget_2 = QtGui.QWidget(self.splitter)
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tablesTreeWidget = QtGui.QTreeWidget(self.verticalLayoutWidget_2)
        self.tablesTreeWidget.setMinimumSize(QtCore.QSize(150, 0))
        self.tablesTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}\n"
"\n"
"QTreeView::item:selected:active{\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
"    border: 1px solid transparent;\n"
"}\n"
"QTreeView::item:selected:!active {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
"    border: 1px solid transparent;\n"
"}\n"
"")
        self.tablesTreeWidget.setRootIsDecorated(True)
        self.tablesTreeWidget.setHeaderHidden(True)
        self.tablesTreeWidget.setObjectName("tablesTreeWidget")
        item_0 = QtGui.QTreeWidgetItem(self.tablesTreeWidget)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_2 = QtGui.QTreeWidgetItem(item_1)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_2 = QtGui.QTreeWidgetItem(item_1)
        item_0 = QtGui.QTreeWidgetItem(self.tablesTreeWidget)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_2 = QtGui.QTreeWidgetItem(item_1)
        item_2 = QtGui.QTreeWidgetItem(item_1)
        item_3 = QtGui.QTreeWidgetItem(item_2)
        item_2 = QtGui.QTreeWidgetItem(item_1)
        item_3 = QtGui.QTreeWidgetItem(item_2)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        self.verticalLayout.addWidget(self.tablesTreeWidget)
        self.verticalLayoutWidget_3 = QtGui.QWidget(self.splitter)
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tableEditorLayout = QtGui.QVBoxLayout()
        self.tableEditorLayout.setObjectName("tableEditorLayout")
        self.editTableWidget = QtGui.QTableWidget(self.verticalLayoutWidget_3)
        self.editTableWidget.setObjectName("editTableWidget")
        self.editTableWidget.setColumnCount(0)
        self.editTableWidget.setRowCount(0)
        self.tableEditorLayout.addWidget(self.editTableWidget)
        self.verticalLayout_2.addLayout(self.tableEditorLayout)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.savePushButton = QtGui.QPushButton(self.verticalLayoutWidget_3)
        self.savePushButton.setMinimumSize(QtCore.QSize(120, 0))
        self.savePushButton.setObjectName("savePushButton")
        self.horizontalLayout.addWidget(self.savePushButton)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout_2.setStretch(0, 1)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)
        editDBTable.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(editDBTable)
        self.statusbar.setObjectName("statusbar")
        editDBTable.setStatusBar(self.statusbar)

        self.retranslateUi(editDBTable)
        QtCore.QMetaObject.connectSlotsByName(editDBTable)

    def retranslateUi(self, editDBTable):
        editDBTable.setWindowTitle(u"MainWindow")
        self.tablesTreeWidget.headerItem().setText(0, u"1")
        __sortingEnabled = self.tablesTreeWidget.isSortingEnabled()
        self.tablesTreeWidget.setSortingEnabled(False)
        self.tablesTreeWidget.topLevelItem(0).setText(0, u"Modeling")
        self.tablesTreeWidget.topLevelItem(0).child(0).setText(0, u"Notes")
        self.tablesTreeWidget.topLevelItem(0).child(1).setText(0, u"Snapshots")
        self.tablesTreeWidget.topLevelItem(0).child(1).child(0).setText(0, u"Files")
        self.tablesTreeWidget.topLevelItem(0).child(2).setText(0, u"Snapshots/modeling/context")
        self.tablesTreeWidget.topLevelItem(0).child(2).child(0).setText(0, u"Files")
        self.tablesTreeWidget.topLevelItem(1).setText(0, u"Render")
        self.tablesTreeWidget.topLevelItem(1).child(0).setText(0, u"Lighting")
        self.tablesTreeWidget.topLevelItem(1).child(0).child(0).setText(0, u"Notes")
        self.tablesTreeWidget.topLevelItem(1).child(0).child(1).setText(0, u"Snapshots")
        self.tablesTreeWidget.topLevelItem(1).child(0).child(1).child(0).setText(0, u"Files")
        self.tablesTreeWidget.topLevelItem(1).child(0).child(2).setText(0, u"Snapshots/lighting/context")
        self.tablesTreeWidget.topLevelItem(1).child(0).child(2).child(0).setText(0, u"Files")
        self.tablesTreeWidget.topLevelItem(1).child(1).setText(0, u"Render")
        self.tablesTreeWidget.setSortingEnabled(__sortingEnabled)
        self.savePushButton.setText(u"Save changes")

