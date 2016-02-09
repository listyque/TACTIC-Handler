# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_my_tasks.ui'
#
# Created: Thu Jan 28 18:03:10 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(695, 425)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.treeWidget = QtGui.QTreeWidget(Form)
        self.treeWidget.setObjectName("treeWidget")
        item_0 = QtGui.QTreeWidgetItem(self.treeWidget)
        item_0 = QtGui.QTreeWidgetItem(self.treeWidget)
        self.gridLayout.addWidget(self.treeWidget, 0, 0, 1, 1)
        self.comboBox = QtGui.QComboBox(Form)
        self.comboBox.setEditable(True)
        self.comboBox.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.gridLayout.addWidget(self.comboBox, 1, 0, 1, 1)
        self.gridLayout.setRowStretch(0, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(0, QtGui.QApplication.translate("Form", "Tasks:", None, QtGui.QApplication.UnicodeUTF8))
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.topLevelItem(0).setText(0, QtGui.QApplication.translate("Form", "Task00001", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).setText(0, QtGui.QApplication.translate("Form", "Task00002", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.setSortingEnabled(__sortingEnabled)
        self.comboBox.setItemText(0, QtGui.QApplication.translate("Form", "Толстый Админ, Admin", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBox.setItemText(1, QtGui.QApplication.translate("Form", "Алексей Кривоспицкий, listy", None, QtGui.QApplication.UnicodeUTF8))

