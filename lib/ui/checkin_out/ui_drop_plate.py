# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out/ui_drop_plate.ui'
#
# Created: Mon Oct 30 14:43:59 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

class Ui_dropPlate(object):
    def setupUi(self, dropPlate):
        dropPlate.setObjectName("dropPlate")
        self.dropPlateGridLayout = QtGui.QGridLayout(dropPlate)
        self.dropPlateGridLayout.setContentsMargins(0, 0, 0, 0)
        self.dropPlateGridLayout.setSpacing(4)
        self.dropPlateGridLayout.setObjectName("dropPlateGridLayout")
        self.fromDropListCheckBox = QtGui.QCheckBox(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fromDropListCheckBox.sizePolicy().hasHeightForWidth())
        self.fromDropListCheckBox.setSizePolicy(sizePolicy)
        self.fromDropListCheckBox.setObjectName("fromDropListCheckBox")
        self.dropPlateGridLayout.addWidget(self.fromDropListCheckBox, 1, 0, 1, 1)
        self.groupCheckinCheckBox = QtGui.QCheckBox(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupCheckinCheckBox.sizePolicy().hasHeightForWidth())
        self.groupCheckinCheckBox.setSizePolicy(sizePolicy)
        self.groupCheckinCheckBox.setObjectName("groupCheckinCheckBox")
        self.dropPlateGridLayout.addWidget(self.groupCheckinCheckBox, 1, 1, 1, 1)
        self.keepFileNameCheckBox = QtGui.QCheckBox(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.keepFileNameCheckBox.sizePolicy().hasHeightForWidth())
        self.keepFileNameCheckBox.setSizePolicy(sizePolicy)
        self.keepFileNameCheckBox.setObjectName("keepFileNameCheckBox")
        self.dropPlateGridLayout.addWidget(self.keepFileNameCheckBox, 1, 2, 1, 1)
        self.includeSubfoldersCheckBox = QtGui.QCheckBox(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.includeSubfoldersCheckBox.sizePolicy().hasHeightForWidth())
        self.includeSubfoldersCheckBox.setSizePolicy(sizePolicy)
        self.includeSubfoldersCheckBox.setObjectName("includeSubfoldersCheckBox")
        self.dropPlateGridLayout.addWidget(self.includeSubfoldersCheckBox, 1, 3, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.dropPlateGridLayout.addItem(spacerItem, 1, 4, 1, 1)
        self.clearPushButton = QtGui.QToolButton(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.clearPushButton.sizePolicy().hasHeightForWidth())
        self.clearPushButton.setSizePolicy(sizePolicy)
        self.clearPushButton.setMinimumSize(QtCore.QSize(24, 24))
        self.clearPushButton.setMaximumSize(QtCore.QSize(24, 24))
        self.clearPushButton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.clearPushButton.setAutoRaise(True)
        self.clearPushButton.setObjectName("clearPushButton")
        self.dropPlateGridLayout.addWidget(self.clearPushButton, 1, 6, 1, 1)
        self.dropTreeWidget = QtGui.QTreeWidget(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Expanding)
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
        self.dropPlateGridLayout.addWidget(self.dropTreeWidget, 0, 0, 1, 7)
        self.configPushButton = QtGui.QToolButton(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.configPushButton.sizePolicy().hasHeightForWidth())
        self.configPushButton.setSizePolicy(sizePolicy)
        self.configPushButton.setMinimumSize(QtCore.QSize(24, 24))
        self.configPushButton.setMaximumSize(QtCore.QSize(24, 24))
        self.configPushButton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.configPushButton.setAutoRaise(True)
        self.configPushButton.setObjectName("configPushButton")
        self.dropPlateGridLayout.addWidget(self.configPushButton, 1, 5, 1, 1)

        self.retranslateUi(dropPlate)
        QtCore.QMetaObject.connectSlotsByName(dropPlate)

    def retranslateUi(self, dropPlate):
        dropPlate.setWindowTitle(QtGui.QApplication.translate("dropPlate", "Form", None))
        self.fromDropListCheckBox.setText(QtGui.QApplication.translate("dropPlate", "From Droplist", None))
        self.groupCheckinCheckBox.setText(QtGui.QApplication.translate("dropPlate", "Group Checkin", None))
        self.keepFileNameCheckBox.setText(QtGui.QApplication.translate("dropPlate", "Keep Filename", None))
        self.includeSubfoldersCheckBox.setText(QtGui.QApplication.translate("dropPlate", "Include Subfolders", None))
        self.dropTreeWidget.setSortingEnabled(True)
        self.dropTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("dropPlate", "File Name", None))
        self.dropTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("dropPlate", "Range/Tiles/Layer", None))
        self.dropTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("dropPlate", "Class/Ext", None))
        self.dropTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("dropPlate", "Type", None))
        self.dropTreeWidget.headerItem().setText(4, QtGui.QApplication.translate("dropPlate", "File Path", None))

