# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_sobj_tabs.ui'
#
# Created: Mon Sep 05 00:35:39 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_sObjTabs(object):
    def setupUi(self, sObjTabs):
        sObjTabs.setObjectName("sObjTabs")
        sObjTabs.resize(400, 250)
        sObjTabs.setMinimumSize(QtCore.QSize(400, 250))
        self.verticalLayout = QtGui.QVBoxLayout(sObjTabs)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.sObjTabWidget = QtGui.QTabWidget(sObjTabs)
        self.sObjTabWidget.setStyleSheet("QTabWidget::pane {\n"
"    border: 0px;\n"
"}\n"
"QTabWidget::tab-bar {\n"
"    alignment: left;\n"
"}")
        self.sObjTabWidget.setObjectName("sObjTabWidget")
        self.verticalLayout.addWidget(self.sObjTabWidget)

        self.retranslateUi(sObjTabs)
        QtCore.QMetaObject.connectSlotsByName(sObjTabs)

    def retranslateUi(self, sObjTabs):
        sObjTabs.setWindowTitle(QtGui.QApplication.translate("sObjTabs", "Checkout", None, QtGui.QApplication.UnicodeUTF8))

