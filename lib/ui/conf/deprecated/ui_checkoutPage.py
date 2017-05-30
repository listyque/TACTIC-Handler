# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf/ui_checkoutPage.ui'
#
# Created: Thu Apr 27 14:15:16 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_checkoutPageWidget(object):
    def setupUi(self, checkoutPageWidget):
        checkoutPageWidget.setObjectName("checkoutPageWidget")
        self.checkoutPageWidgetLayout = QtGui.QVBoxLayout(checkoutPageWidget)
        self.checkoutPageWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.checkoutPageWidgetLayout.setObjectName("checkoutPageWidgetLayout")
        self.checkoutMiscOpitionsGroupBox = QtGui.QGroupBox(checkoutPageWidget)
        self.checkoutMiscOpitionsGroupBox.setFlat(True)
        self.checkoutMiscOpitionsGroupBox.setObjectName("checkoutMiscOpitionsGroupBox")
        self.checkoutMiscOptionsLayout = QtGui.QGridLayout(self.checkoutMiscOpitionsGroupBox)
        self.checkoutMiscOptionsLayout.setContentsMargins(0, -1, 0, 0)
        self.checkoutMiscOptionsLayout.setObjectName("checkoutMiscOptionsLayout")
        self.doubleClickOpenCheckBox = QtGui.QCheckBox(self.checkoutMiscOpitionsGroupBox)
        self.doubleClickOpenCheckBox.setObjectName("doubleClickOpenCheckBox")
        self.checkoutMiscOptionsLayout.addWidget(self.doubleClickOpenCheckBox, 0, 0, 1, 1)
        self.versionsSeparateCheckoutCheckBox = QtGui.QCheckBox(self.checkoutMiscOpitionsGroupBox)
        self.versionsSeparateCheckoutCheckBox.setObjectName("versionsSeparateCheckoutCheckBox")
        self.checkoutMiscOptionsLayout.addWidget(self.versionsSeparateCheckoutCheckBox, 1, 0, 1, 1)
        self.checkoutPageWidgetLayout.addWidget(self.checkoutMiscOpitionsGroupBox)
        spacerItem = QtGui.QSpacerItem(20, 58, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.checkoutPageWidgetLayout.addItem(spacerItem)

        self.retranslateUi(checkoutPageWidget)
        QtCore.QMetaObject.connectSlotsByName(checkoutPageWidget)

    def retranslateUi(self, checkoutPageWidget):
        self.checkoutMiscOpitionsGroupBox.setTitle(QtGui.QApplication.translate("checkoutPageWidget", "Misc:", None))
        self.doubleClickOpenCheckBox.setText(QtGui.QApplication.translate("checkoutPageWidget", "DoubleClick for Open", None))
        self.versionsSeparateCheckoutCheckBox.setText(QtGui.QApplication.translate("checkoutPageWidget", "Display versions separate", None))

