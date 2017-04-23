# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin/ui_drop_plate.ui'
#
# Created: Thu Dec 29 15:49:47 2016
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_dropPlateGroupBox(object):
    def setupUi(self, dropPlateGroupBox):
        dropPlateGroupBox.setObjectName("dropPlateGroupBox")
        dropPlateGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        dropPlateGroupBox.setFlat(True)
        self.gridLayout = QtGui.QGridLayout(dropPlateGroupBox)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName("gridLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 4, 1, 1)
        self.dropTreeWidget = QtGui.QTreeWidget(dropPlateGroupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dropTreeWidget.sizePolicy().hasHeightForWidth())
        self.dropTreeWidget.setSizePolicy(sizePolicy)
        self.dropTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}\n"
"\n"
"QTreeView::item:selected:active{\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
"    border: 1px solid transparent;\n"
"}\n"
"QTreeView::item:selected:!active {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
"    border: 1px solid transparent;\n"
"}\n"
"")
        self.dropTreeWidget.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.dropTreeWidget.setTabKeyNavigation(True)
        self.dropTreeWidget.setAlternatingRowColors(True)
        self.dropTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.dropTreeWidget.setTextElideMode(QtCore.Qt.ElideMiddle)
        self.dropTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.dropTreeWidget.setIndentation(20)
        self.dropTreeWidget.setRootIsDecorated(True)
        self.dropTreeWidget.setUniformRowHeights(True)
        self.dropTreeWidget.setItemsExpandable(True)
        self.dropTreeWidget.setAllColumnsShowFocus(True)
        self.dropTreeWidget.setWordWrap(True)
        self.dropTreeWidget.setHeaderHidden(False)
        self.dropTreeWidget.setObjectName("dropTreeWidget")
        self.dropTreeWidget.header().setCascadingSectionResizes(True)
        self.gridLayout.addWidget(self.dropTreeWidget, 0, 0, 1, 6)
        self.fromDropListCheckBox = QtGui.QCheckBox(dropPlateGroupBox)
        self.fromDropListCheckBox.setObjectName("fromDropListCheckBox")
        self.gridLayout.addWidget(self.fromDropListCheckBox, 2, 0, 1, 1)
        self.groupCheckinCheckBox = QtGui.QCheckBox(dropPlateGroupBox)
        self.groupCheckinCheckBox.setObjectName("groupCheckinCheckBox")
        self.gridLayout.addWidget(self.groupCheckinCheckBox, 2, 1, 1, 1)
        self.keepFileNameCheckBox = QtGui.QCheckBox(dropPlateGroupBox)
        self.keepFileNameCheckBox.setObjectName("keepFileNameCheckBox")
        self.gridLayout.addWidget(self.keepFileNameCheckBox, 2, 2, 1, 1)
        self.clearPushButton = QtGui.QToolButton(dropPlateGroupBox)
        self.clearPushButton.setMinimumSize(QtCore.QSize(75, 0))
        self.clearPushButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.clearPushButton.setAutoRaise(True)
        self.clearPushButton.setObjectName("clearPushButton")
        self.gridLayout.addWidget(self.clearPushButton, 2, 5, 1, 1)
        self.digSubfoldersCheckBox = QtGui.QCheckBox(dropPlateGroupBox)
        self.digSubfoldersCheckBox.setObjectName("digSubfoldersCheckBox")
        self.gridLayout.addWidget(self.digSubfoldersCheckBox, 2, 3, 1, 1)

        self.retranslateUi(dropPlateGroupBox)
        QtCore.QMetaObject.connectSlotsByName(dropPlateGroupBox)

    def retranslateUi(self, dropPlateGroupBox):
        dropPlateGroupBox.setWindowTitle(QtGui.QApplication.translate("dropPlateGroupBox", "DropPlate", None, QtGui.QApplication.UnicodeUTF8))
        dropPlateGroupBox.setTitle(QtGui.QApplication.translate("dropPlateGroupBox", "Drop Files/Folders/Sequences Here:", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.setSortingEnabled(True)
        self.dropTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("dropPlateGroupBox", "File Name", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("dropPlateGroupBox", "Class/Ext", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("dropPlateGroupBox", "Type", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("dropPlateGroupBox", "File Path", None, QtGui.QApplication.UnicodeUTF8))
        self.fromDropListCheckBox.setText(QtGui.QApplication.translate("dropPlateGroupBox", "From Droplist", None, QtGui.QApplication.UnicodeUTF8))
        self.groupCheckinCheckBox.setText(QtGui.QApplication.translate("dropPlateGroupBox", "Group Checkin", None, QtGui.QApplication.UnicodeUTF8))
        self.keepFileNameCheckBox.setText(QtGui.QApplication.translate("dropPlateGroupBox", "Keep Filename", None, QtGui.QApplication.UnicodeUTF8))
        self.clearPushButton.setText(QtGui.QApplication.translate("dropPlateGroupBox", "Clear", None, QtGui.QApplication.UnicodeUTF8))
        self.digSubfoldersCheckBox.setText(QtGui.QApplication.translate("dropPlateGroupBox", "Dig Subfolders", None, QtGui.QApplication.UnicodeUTF8))

