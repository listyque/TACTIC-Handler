# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf\ui_globalPage.ui'
#
# Created: Sat Oct  5 00:17:17 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_globalPageWidget(object):
    def setupUi(self, globalPageWidget):
        globalPageWidget.setObjectName("globalPageWidget")
        self.verticalLayout = QtGui.QVBoxLayout(globalPageWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.cacheProcessTabsCheckBox = QtGui.QCheckBox(globalPageWidget)
        self.cacheProcessTabsCheckBox.setObjectName("cacheProcessTabsCheckBox")
        self.verticalLayout.addWidget(self.cacheProcessTabsCheckBox)
        self.flushTabsCachePushButton = QtGui.QPushButton(globalPageWidget)
        self.flushTabsCachePushButton.setObjectName("flushTabsCachePushButton")
        self.verticalLayout.addWidget(self.flushTabsCachePushButton)
        self.configPathGroupBox = QtGui.QGroupBox(globalPageWidget)
        self.configPathGroupBox.setFlat(True)
        self.configPathGroupBox.setObjectName("configPathGroupBox")
        self.horizontalLayout = QtGui.QHBoxLayout(self.configPathGroupBox)
        self.horizontalLayout.setContentsMargins(0, -1, 0, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.configPathLineEdit = QtGui.QLineEdit(self.configPathGroupBox)
        self.configPathLineEdit.setObjectName("configPathLineEdit")
        self.horizontalLayout.addWidget(self.configPathLineEdit)
        self.changeConfigPathToolButton = QtGui.QToolButton(self.configPathGroupBox)
        self.changeConfigPathToolButton.setObjectName("changeConfigPathToolButton")
        self.horizontalLayout.addWidget(self.changeConfigPathToolButton)
        self.verticalLayout.addWidget(self.configPathGroupBox)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)

        self.retranslateUi(globalPageWidget)
        QtCore.QMetaObject.connectSlotsByName(globalPageWidget)

    def retranslateUi(self, globalPageWidget):
        globalPageWidget.setWindowTitle(QtGui.QApplication.translate("globalPageWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.cacheProcessTabsCheckBox.setText(QtGui.QApplication.translate("globalPageWidget", "Cache Tabs (faster launch)", None, QtGui.QApplication.UnicodeUTF8))
        self.flushTabsCachePushButton.setText(QtGui.QApplication.translate("globalPageWidget", "Flush Tabs cache", None, QtGui.QApplication.UnicodeUTF8))
        self.configPathGroupBox.setTitle(QtGui.QApplication.translate("globalPageWidget", "Configuration files path:", None, QtGui.QApplication.UnicodeUTF8))

