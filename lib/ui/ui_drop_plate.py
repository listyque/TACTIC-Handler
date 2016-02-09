# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_drop_plate.ui'
#
# Created: Tue Feb 09 15:27:51 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_dropPlateGroupBox(object):
    def setupUi(self, dropPlateGroupBox):
        dropPlateGroupBox.setObjectName("dropPlateGroupBox")
        dropPlateGroupBox.resize(267, 38)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(dropPlateGroupBox.sizePolicy().hasHeightForWidth())
        dropPlateGroupBox.setSizePolicy(sizePolicy)
        dropPlateGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        dropPlateGroupBox.setFlat(True)
        self.gridLayout = QtGui.QGridLayout(dropPlateGroupBox)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setHorizontalSpacing(6)
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.clearPushButton = QtGui.QPushButton(dropPlateGroupBox)
        self.clearPushButton.setMinimumSize(QtCore.QSize(75, 0))
        self.clearPushButton.setObjectName("clearPushButton")
        self.gridLayout.addWidget(self.clearPushButton, 2, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 1, 1, 1)
        self.dropTreeWidget = QtGui.QTreeWidget(dropPlateGroupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dropTreeWidget.sizePolicy().hasHeightForWidth())
        self.dropTreeWidget.setSizePolicy(sizePolicy)
        self.dropTreeWidget.setAlternatingRowColors(True)
        self.dropTreeWidget.setRootIsDecorated(False)
        self.dropTreeWidget.setUniformRowHeights(True)
        self.dropTreeWidget.setItemsExpandable(False)
        self.dropTreeWidget.setAllColumnsShowFocus(True)
        self.dropTreeWidget.setHeaderHidden(False)
        self.dropTreeWidget.setObjectName("dropTreeWidget")
        self.dropTreeWidget.header().setCascadingSectionResizes(True)
        self.gridLayout.addWidget(self.dropTreeWidget, 0, 0, 1, 3)
        self.fromDropListCheckBox = QtGui.QCheckBox(dropPlateGroupBox)
        self.fromDropListCheckBox.setObjectName("fromDropListCheckBox")
        self.gridLayout.addWidget(self.fromDropListCheckBox, 2, 0, 1, 1)

        self.retranslateUi(dropPlateGroupBox)
        QtCore.QMetaObject.connectSlotsByName(dropPlateGroupBox)

    def retranslateUi(self, dropPlateGroupBox):
        dropPlateGroupBox.setWindowTitle(QtGui.QApplication.translate("dropPlateGroupBox", "GroupBox", None, QtGui.QApplication.UnicodeUTF8))
        dropPlateGroupBox.setTitle(QtGui.QApplication.translate("dropPlateGroupBox", "Drop Files/Folders/Sequences Here:", None, QtGui.QApplication.UnicodeUTF8))
        self.clearPushButton.setText(QtGui.QApplication.translate("dropPlateGroupBox", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.setSortingEnabled(True)
        self.dropTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("dropPlateGroupBox", "File Names", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("dropPlateGroupBox", "Type/Ext", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("dropPlateGroupBox", "File Path", None, QtGui.QApplication.UnicodeUTF8))
        self.fromDropListCheckBox.setText(QtGui.QApplication.translate("dropPlateGroupBox", "From Droplist", None, QtGui.QApplication.UnicodeUTF8))

