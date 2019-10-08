# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out\ui_drop_plate.ui'
#
# Created: Sat Oct  5 00:17:19 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_dropPlate(object):
    def setupUi(self, dropPlate):
        dropPlate.setObjectName("dropPlate")
        self.gridLayout = QtGui.QGridLayout(dropPlate)
        self.gridLayout.setContentsMargins(4, 4, 4, 6)
        self.gridLayout.setHorizontalSpacing(4)
        self.gridLayout.setObjectName("gridLayout")
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
        self.gridLayout.addWidget(self.dropTreeWidget, 0, 0, 1, 5)
        self.progressBarLayout = QtGui.QHBoxLayout()
        self.progressBarLayout.setSpacing(0)
        self.progressBarLayout.setObjectName("progressBarLayout")
        self.gridLayout.addLayout(self.progressBarLayout, 1, 0, 1, 5)
        self.filterLineEdit = QtGui.QLineEdit(dropPlate)
        self.filterLineEdit.setEnabled(False)
        self.filterLineEdit.setStyleSheet("QLineEdit {\n"
"    border: 0px;\n"
"    border-radius: 8px;\n"
"    show-decoration-selected: 1;\n"
"    padding: 0px 8px;\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 64), stop:1 rgba(255, 255, 255, 0));\n"
"    background-position: bottom left;\n"
"    background-image: url(\":/ui_check/gliph/search_16.png\");\n"
"    background-repeat: fixed;\n"
"    selection-background-color: darkgray;\n"
"    padding-left: 15px;\n"
"}\n"
"QLineEdit:hover{\n"
"    color: white;\n"
"    background-image: url(\":/ui_check/gliph/searchHover_16.png\");\n"
"}")
        self.filterLineEdit.setObjectName("filterLineEdit")
        self.gridLayout.addWidget(self.filterLineEdit, 2, 0, 1, 1)
        self.expandingLayout = QtGui.QHBoxLayout()
        self.expandingLayout.setObjectName("expandingLayout")
        self.enableFilterCheckBox = QtGui.QCheckBox(dropPlate)
        self.enableFilterCheckBox.setChecked(False)
        self.enableFilterCheckBox.setObjectName("enableFilterCheckBox")
        self.expandingLayout.addWidget(self.enableFilterCheckBox)
        self.filterComboBox = QtGui.QComboBox(dropPlate)
        self.filterComboBox.setEnabled(False)
        self.filterComboBox.setObjectName("filterComboBox")
        self.filterComboBox.addItem("")
        self.filterComboBox.addItem("")
        self.expandingLayout.addWidget(self.filterComboBox)
        self.fromDropListCheckBox = QtGui.QCheckBox(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.fromDropListCheckBox.sizePolicy().hasHeightForWidth())
        self.fromDropListCheckBox.setSizePolicy(sizePolicy)
        self.fromDropListCheckBox.setObjectName("fromDropListCheckBox")
        self.expandingLayout.addWidget(self.fromDropListCheckBox)
        self.groupCheckinCheckBox = QtGui.QCheckBox(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupCheckinCheckBox.sizePolicy().hasHeightForWidth())
        self.groupCheckinCheckBox.setSizePolicy(sizePolicy)
        self.groupCheckinCheckBox.setObjectName("groupCheckinCheckBox")
        self.expandingLayout.addWidget(self.groupCheckinCheckBox)
        self.keepFileNameCheckBox = QtGui.QCheckBox(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.keepFileNameCheckBox.sizePolicy().hasHeightForWidth())
        self.keepFileNameCheckBox.setSizePolicy(sizePolicy)
        self.keepFileNameCheckBox.setObjectName("keepFileNameCheckBox")
        self.expandingLayout.addWidget(self.keepFileNameCheckBox)
        self.includeSubfoldersCheckBox = QtGui.QCheckBox(dropPlate)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.includeSubfoldersCheckBox.sizePolicy().hasHeightForWidth())
        self.includeSubfoldersCheckBox.setSizePolicy(sizePolicy)
        self.includeSubfoldersCheckBox.setObjectName("includeSubfoldersCheckBox")
        self.expandingLayout.addWidget(self.includeSubfoldersCheckBox)
        self.gridLayout.addLayout(self.expandingLayout, 2, 1, 1, 2)
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
        self.gridLayout.addWidget(self.configPushButton, 2, 3, 1, 1)
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
        self.gridLayout.addWidget(self.clearPushButton, 2, 4, 1, 1)
        self.gridLayout.setRowStretch(0, 1)

        self.retranslateUi(dropPlate)
        QtCore.QObject.connect(self.enableFilterCheckBox, QtCore.SIGNAL("toggled(bool)"), self.filterComboBox.setEnabled)
        QtCore.QObject.connect(self.enableFilterCheckBox, QtCore.SIGNAL("toggled(bool)"), self.filterLineEdit.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(dropPlate)

    def retranslateUi(self, dropPlate):
        dropPlate.setWindowTitle(QtGui.QApplication.translate("dropPlate", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.setSortingEnabled(True)
        self.dropTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("dropPlate", "File Name", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("dropPlate", "Range/Tiles/Layer", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("dropPlate", "Class/Ext", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("dropPlate", "Type", None, QtGui.QApplication.UnicodeUTF8))
        self.dropTreeWidget.headerItem().setText(4, QtGui.QApplication.translate("dropPlate", "File Path", None, QtGui.QApplication.UnicodeUTF8))
        self.enableFilterCheckBox.setText(QtGui.QApplication.translate("dropPlate", "Filter:", None, QtGui.QApplication.UnicodeUTF8))
        self.filterComboBox.setItemText(0, QtGui.QApplication.translate("dropPlate", "By Extension", None, QtGui.QApplication.UnicodeUTF8))
        self.filterComboBox.setItemText(1, QtGui.QApplication.translate("dropPlate", "By Filename", None, QtGui.QApplication.UnicodeUTF8))
        self.fromDropListCheckBox.setText(QtGui.QApplication.translate("dropPlate", "From Droplist", None, QtGui.QApplication.UnicodeUTF8))
        self.groupCheckinCheckBox.setText(QtGui.QApplication.translate("dropPlate", "Group Checkin", None, QtGui.QApplication.UnicodeUTF8))
        self.keepFileNameCheckBox.setText(QtGui.QApplication.translate("dropPlate", "Keep Filename", None, QtGui.QApplication.UnicodeUTF8))
        self.includeSubfoldersCheckBox.setText(QtGui.QApplication.translate("dropPlate", "Include Subfolders", None, QtGui.QApplication.UnicodeUTF8))

