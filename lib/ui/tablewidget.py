# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './tablewidget.ui'
#
# Created: Sun Oct 30 11:07:32 2016
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        self.layout = QtGui.QGridLayout(Form)
        self.layout.setObjectName("layout")
        self.CenterSplitter = QtGui.QSplitter(Form)
        self.CenterSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.CenterSplitter.setObjectName("CenterSplitter")
        self.LeftSplitter = QtGui.QSplitter(self.CenterSplitter)
        self.LeftSplitter.setOrientation(QtCore.Qt.Vertical)
        self.LeftSplitter.setObjectName("LeftSplitter")
        self.LeftTopTreeWidget = QtGui.QTreeWidget(self.LeftSplitter)
        self.LeftTopTreeWidget.setObjectName("LeftTopTreeWidget")
        self.LeftTopTreeWidget.headerItem().setText(0, "1")
        self.leftBottomTableWidget = QtGui.QTableWidget(self.LeftSplitter)
        self.leftBottomTableWidget.setObjectName("leftBottomTableWidget")
        self.leftBottomTableWidget.setColumnCount(0)
        self.leftBottomTableWidget.setRowCount(0)
        self.rightSplitter = QtGui.QSplitter(self.CenterSplitter)
        self.rightSplitter.setOrientation(QtCore.Qt.Vertical)
        self.rightSplitter.setObjectName("rightSplitter")
        self.RightTopTreeWidget = QtGui.QTreeWidget(self.rightSplitter)
        self.RightTopTreeWidget.setObjectName("RightTopTreeWidget")
        self.RightTopTreeWidget.headerItem().setText(0, "1")
        self.rightBottomTableWidget = QtGui.QTableWidget(self.rightSplitter)
        self.rightBottomTableWidget.setObjectName("rightBottomTableWidget")
        self.rightBottomTableWidget.setColumnCount(0)
        self.rightBottomTableWidget.setRowCount(0)
        self.layout.addWidget(self.CenterSplitter, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
