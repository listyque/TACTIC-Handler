# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf\ui_globalPage.ui'
#
# Created: Fri Sep 16 20:39:27 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_globalPageWidget(object):
    def setupUi(self, globalPageWidget):
        globalPageWidget.setObjectName("globalPageWidget")
        self.verticalLayout = QtGui.QVBoxLayout(globalPageWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.flushTabsCachePushButton = QtGui.QPushButton(globalPageWidget)
        self.flushTabsCachePushButton.setObjectName("flushTabsCachePushButton")
        self.verticalLayout.addWidget(self.flushTabsCachePushButton)
        self.cacheProcessTabsCheckBox = QtGui.QCheckBox(globalPageWidget)
        self.cacheProcessTabsCheckBox.setObjectName("cacheProcessTabsCheckBox")
        self.verticalLayout.addWidget(self.cacheProcessTabsCheckBox)
        self.snapshotDisplayOptionsGroupBox = QtGui.QGroupBox(globalPageWidget)
        self.snapshotDisplayOptionsGroupBox.setFlat(True)
        self.snapshotDisplayOptionsGroupBox.setObjectName("snapshotDisplayOptionsGroupBox")
        self.snapshotDisplayOptionsLayout = QtGui.QHBoxLayout(self.snapshotDisplayOptionsGroupBox)
        self.snapshotDisplayOptionsLayout.setContentsMargins(0, -1, 0, -1)
        self.snapshotDisplayOptionsLayout.setObjectName("snapshotDisplayOptionsLayout")
        self.snapshotDescriptionLimitCheckBox = QtGui.QCheckBox(self.snapshotDisplayOptionsGroupBox)
        self.snapshotDescriptionLimitCheckBox.setChecked(True)
        self.snapshotDescriptionLimitCheckBox.setObjectName("snapshotDescriptionLimitCheckBox")
        self.snapshotDisplayOptionsLayout.addWidget(self.snapshotDescriptionLimitCheckBox)
        self.snapshotDescriptionLimitSpinBox = QtGui.QSpinBox(self.snapshotDisplayOptionsGroupBox)
        self.snapshotDescriptionLimitSpinBox.setMinimum(20)
        self.snapshotDescriptionLimitSpinBox.setMaximum(50000)
        self.snapshotDescriptionLimitSpinBox.setSingleStep(5)
        self.snapshotDescriptionLimitSpinBox.setProperty("value", 80)
        self.snapshotDescriptionLimitSpinBox.setObjectName("snapshotDescriptionLimitSpinBox")
        self.snapshotDisplayOptionsLayout.addWidget(self.snapshotDescriptionLimitSpinBox)
        self.verticalLayout.addWidget(self.snapshotDisplayOptionsGroupBox)
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
        self.flushTabsCachePushButton.setText(QtGui.QApplication.translate("globalPageWidget", "Flush Tabs cache", None, QtGui.QApplication.UnicodeUTF8))
        self.cacheProcessTabsCheckBox.setText(QtGui.QApplication.translate("globalPageWidget", "Cache Tabs (faster launch)", None, QtGui.QApplication.UnicodeUTF8))
        self.snapshotDisplayOptionsGroupBox.setTitle(QtGui.QApplication.translate("globalPageWidget", "Snapshots display options:", None, QtGui.QApplication.UnicodeUTF8))
        self.snapshotDescriptionLimitCheckBox.setText(QtGui.QApplication.translate("globalPageWidget", "Limit snapshot description preview (symbols)", None, QtGui.QApplication.UnicodeUTF8))
        self.configPathGroupBox.setTitle(QtGui.QApplication.translate("globalPageWidget", "Configuration files path:", None, QtGui.QApplication.UnicodeUTF8))

