# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf/ui_mayaPage.ui'
#
# Created: Mon Jul 11 18:07:48 2016
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_mayaScenePageWidget(object):
    def setupUi(self, mayaScenePageWidget):
        mayaScenePageWidget.setObjectName("mayaScenePageWidget")
        self.mayaScenePageWidgetLayout = QtGui.QGridLayout(mayaScenePageWidget)
        self.mayaScenePageWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.mayaScenePageWidgetLayout.setObjectName("mayaScenePageWidgetLayout")
        self.currentWorkdirLable = QtGui.QLabel(mayaScenePageWidget)
        self.currentWorkdirLable.setObjectName("currentWorkdirLable")
        self.mayaScenePageWidgetLayout.addWidget(self.currentWorkdirLable, 0, 0, 1, 1)
        self.currentWorkdirLineEdit = QtGui.QLineEdit(mayaScenePageWidget)
        self.currentWorkdirLineEdit.setReadOnly(True)
        self.currentWorkdirLineEdit.setObjectName("currentWorkdirLineEdit")
        self.mayaScenePageWidgetLayout.addWidget(self.currentWorkdirLineEdit, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.mayaScenePageWidgetLayout.addItem(spacerItem, 1, 1, 1, 1)
        self.mayaScenePageWidgetLayout.setColumnMinimumWidth(1, 100)

        self.retranslateUi(mayaScenePageWidget)
        QtCore.QMetaObject.connectSlotsByName(mayaScenePageWidget)

    def retranslateUi(self, mayaScenePageWidget):
        self.currentWorkdirLable.setText(QtGui.QApplication.translate("mayaScenePageWidget", "Current Workdir:", None, QtGui.QApplication.UnicodeUTF8))

