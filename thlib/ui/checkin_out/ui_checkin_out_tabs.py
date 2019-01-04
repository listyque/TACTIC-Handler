# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out/ui_checkin_out_tabs.ui'
#
# Created: Thu Apr 27 14:15:17 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

class Ui_sObjTabs(object):
    def setupUi(self, sObjTabs):
        sObjTabs.setObjectName("sObjTabs")
        sObjTabs.resize(131, 192)
        self.horizontalLayout = QtGui.QHBoxLayout(sObjTabs)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.sTypesTreeWidget = QtGui.QTreeWidget(sObjTabs)
        self.sTypesTreeWidget.setMaximumSize(QtCore.QSize(0, 16777215))
        self.sTypesTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}")
        self.sTypesTreeWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.sTypesTreeWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.sTypesTreeWidget.setProperty("showDropIndicator", False)
        self.sTypesTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.sTypesTreeWidget.setRootIsDecorated(False)
        self.sTypesTreeWidget.setAnimated(True)
        self.sTypesTreeWidget.setHeaderHidden(True)
        self.sTypesTreeWidget.setObjectName("sTypesTreeWidget")
        self.sTypesTreeWidget.headerItem().setText(0, "1")
        self.horizontalLayout.addWidget(self.sTypesTreeWidget)
        self.sObjTabWidget = QtGui.QTabWidget(sObjTabs)
        self.sObjTabWidget.setStyleSheet("QTabWidget::pane {\n"
"    border: 0px;\n"
"}\n"
"QTabWidget::tab-bar {\n"
"    alignment: left;\n"
"}")
        self.sObjTabWidget.setMovable(True)
        self.sObjTabWidget.setObjectName("sObjTabWidget")
        self.horizontalLayout.addWidget(self.sObjTabWidget)
        self.horizontalLayout.setStretch(1, 1)

        self.retranslateUi(sObjTabs)
        QtCore.QMetaObject.connectSlotsByName(sObjTabs)

    def retranslateUi(self, sObjTabs):
        pass

