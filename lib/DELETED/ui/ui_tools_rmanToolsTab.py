# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_tools_rmanToolsTab.ui'
#
# Created: Fri Dec 04 17:39:15 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_rmanToolsTab(object):
    def setupUi(self, rmanToolsTab):
        rmanToolsTab.setObjectName("rmanToolsTab")
        rmanToolsTab.resize(440, 604)
        self.formLayout = QtGui.QGridLayout(rmanToolsTab)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setSpacing(0)
        self.formLayout.setObjectName("formLayout")
        self.rmanToolsTabLayout = QtGui.QGridLayout()
        self.rmanToolsTabLayout.setSpacing(0)
        self.rmanToolsTabLayout.setObjectName("rmanToolsTabLayout")
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.rmanToolsTabLayout.addItem(spacerItem, 2, 1, 1, 1)
        self.AddRenderAttrsButton = QtGui.QPushButton(rmanToolsTab)
        self.AddRenderAttrsButton.setMinimumSize(QtCore.QSize(100, 0))
        self.AddRenderAttrsButton.setObjectName("AddRenderAttrsButton")
        self.rmanToolsTabLayout.addWidget(self.AddRenderAttrsButton, 0, 1, 1, 1)
        self.makeSubdivButton = QtGui.QPushButton(rmanToolsTab)
        self.makeSubdivButton.setObjectName("makeSubdivButton")
        self.rmanToolsTabLayout.addWidget(self.makeSubdivButton, 1, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.rmanToolsTabLayout.addItem(spacerItem1, 0, 0, 2, 1)
        self.formLayout.addLayout(self.rmanToolsTabLayout, 0, 0, 1, 1)

        self.retranslateUi(rmanToolsTab)
        QtCore.QMetaObject.connectSlotsByName(rmanToolsTab)

    def retranslateUi(self, rmanToolsTab):
        rmanToolsTab.setWindowTitle(QtGui.QApplication.translate("rmanToolsTab", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.AddRenderAttrsButton.setText(QtGui.QApplication.translate("rmanToolsTab", "Add Render Attrs", None, QtGui.QApplication.UnicodeUTF8))
        self.makeSubdivButton.setText(QtGui.QApplication.translate("rmanToolsTab", "Convert to subd", None, QtGui.QApplication.UnicodeUTF8))

