# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_sobj_tabs.ui'
#
# Created: Tue Jan 05 14:28:35 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_sObjTabs(object):
    def setupUi(self, sObjTabs):
        sObjTabs.setObjectName("sObjTabs")
        sObjTabs.setMinimumSize(QtCore.QSize(400, 250))
        self.verticalLayout = QtGui.QVBoxLayout(sObjTabs)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.sObjTabWidget = QtGui.QTabWidget(sObjTabs)
        self.sObjTabWidget.setTabPosition(QtGui.QTabWidget.North)
        self.sObjTabWidget.setDocumentMode(True)
        self.sObjTabWidget.setObjectName("sObjTabWidget")
        self.verticalLayout.addWidget(self.sObjTabWidget)

        self.retranslateUi(sObjTabs)
        self.sObjTabWidget.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(sObjTabs)

    def retranslateUi(self, sObjTabs):
        sObjTabs.setWindowTitle(QtGui.QApplication.translate("sObjTabs", "Checkout", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
