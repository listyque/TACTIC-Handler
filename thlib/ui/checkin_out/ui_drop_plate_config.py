# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'checkin_out\ui_drop_plate_config.ui'
#
# Created: Sat Oct  5 00:17:20 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_matchingTemplateConfig(object):
    def setupUi(self, matchingTemplateConfig):
        matchingTemplateConfig.setObjectName("matchingTemplateConfig")
        matchingTemplateConfig.resize(800, 450)
        matchingTemplateConfig.setSizeGripEnabled(True)
        self.gridLayout_2 = QtGui.QGridLayout(matchingTemplateConfig)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.matchingTamplateLabel = QtGui.QLabel(matchingTemplateConfig)
        self.matchingTamplateLabel.setObjectName("matchingTamplateLabel")
        self.gridLayout_2.addWidget(self.matchingTamplateLabel, 0, 0, 1, 1)
        self.editSelectedItemButton = QtGui.QToolButton(matchingTemplateConfig)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.editSelectedItemButton.sizePolicy().hasHeightForWidth())
        self.editSelectedItemButton.setSizePolicy(sizePolicy)
        self.editSelectedItemButton.setMinimumSize(QtCore.QSize(70, 0))
        self.editSelectedItemButton.setObjectName("editSelectedItemButton")
        self.gridLayout_2.addWidget(self.editSelectedItemButton, 0, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 1, 1, 1)
        self.addNewItemButton = QtGui.QToolButton(matchingTemplateConfig)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addNewItemButton.sizePolicy().hasHeightForWidth())
        self.addNewItemButton.setSizePolicy(sizePolicy)
        self.addNewItemButton.setMinimumSize(QtCore.QSize(70, 0))
        self.addNewItemButton.setObjectName("addNewItemButton")
        self.gridLayout_2.addWidget(self.addNewItemButton, 0, 3, 1, 1)
        self.templatesTreeWidget = QtGui.QTreeWidget(matchingTemplateConfig)
        self.templatesTreeWidget.setStyleSheet("QTreeView::item {\n"
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
        self.templatesTreeWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.templatesTreeWidget.setAlternatingRowColors(True)
        self.templatesTreeWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.templatesTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.templatesTreeWidget.setRootIsDecorated(False)
        self.templatesTreeWidget.setItemsExpandable(True)
        self.templatesTreeWidget.setObjectName("templatesTreeWidget")
        self.templatesTreeWidget.header().setVisible(True)
        self.gridLayout_2.addWidget(self.templatesTreeWidget, 1, 0, 1, 4)
        self.configGridLayout = QtGui.QGridLayout()
        self.configGridLayout.setObjectName("configGridLayout")
        self.gridLayout_2.addLayout(self.configGridLayout, 2, 0, 1, 4)
        self.gridLayout_2.setRowStretch(1, 1)

        self.retranslateUi(matchingTemplateConfig)
        QtCore.QMetaObject.connectSlotsByName(matchingTemplateConfig)

    def retranslateUi(self, matchingTemplateConfig):
        matchingTemplateConfig.setWindowTitle(u"Dialog")
        self.matchingTamplateLabel.setText(u"Matching Templates (could interfere with each other):")
        self.editSelectedItemButton.setText(u"Edit")
        self.addNewItemButton.setText(u"Add new")
        self.templatesTreeWidget.headerItem().setText(0, u"Active")
        self.templatesTreeWidget.headerItem().setText(1, u"Template")
        self.templatesTreeWidget.headerItem().setText(2, u"Preview")
        self.templatesTreeWidget.headerItem().setText(3, u"Type")

