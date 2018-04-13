# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items/ui_item.ui'
#
# Created: Tue Dec 26 15:29:02 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

class Ui_item(object):
    def setupUi(self, item):
        item.setObjectName("item")
        self.gridLayout = QtGui.QGridLayout(item)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.itemColorLine = QtGui.QFrame(item)
        self.itemColorLine.setMaximumSize(QtCore.QSize(4, 16777215))
        self.itemColorLine.setStyleSheet("QFrame { border: 0px; background-color: black;}")
        self.itemColorLine.setFrameShadow(QtGui.QFrame.Plain)
        self.itemColorLine.setLineWidth(4)
        self.itemColorLine.setFrameShape(QtGui.QFrame.VLine)
        self.itemColorLine.setFrameShadow(QtGui.QFrame.Sunken)
        self.itemColorLine.setObjectName("itemColorLine")
        self.gridLayout.addWidget(self.itemColorLine, 0, 0, 3, 1)
        self.previewVerticalLayout = QtGui.QVBoxLayout()
        self.previewVerticalLayout.setSpacing(0)
        self.previewVerticalLayout.setContentsMargins(4, 4, 4, 4)
        self.previewVerticalLayout.setObjectName("previewVerticalLayout")
        self.previewLabel = QtGui.QLabel(item)
        self.previewLabel.setMinimumSize(QtCore.QSize(64, 64))
        self.previewLabel.setMaximumSize(QtCore.QSize(64, 64))
        self.previewLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 16), stop: 1 rgba(0, 0, 0, 0));\n"
"    border: 0px;\n"
"    border-radius: 4px;\n"
"    padding: 0px 0px;\n"
"}")
        self.previewLabel.setTextFormat(QtCore.Qt.RichText)
        self.previewLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.previewLabel.setObjectName("previewLabel")
        self.previewVerticalLayout.addWidget(self.previewLabel)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Ignored)
        self.previewVerticalLayout.addItem(spacerItem)
        self.previewVerticalLayout.setStretch(1, 1)
        self.gridLayout.addLayout(self.previewVerticalLayout, 0, 1, 3, 1)
        self.toolsVerticalLayout = QtGui.QVBoxLayout()
        self.toolsVerticalLayout.setSpacing(6)
        self.toolsVerticalLayout.setContentsMargins(3, 4, 6, -1)
        self.toolsVerticalLayout.setObjectName("toolsVerticalLayout")
        self.tasksToolButton = QtGui.QToolButton(item)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tasksToolButton.sizePolicy().hasHeightForWidth())
        self.tasksToolButton.setSizePolicy(sizePolicy)
        self.tasksToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.tasksToolButton.setAutoRaise(True)
        self.tasksToolButton.setArrowType(QtCore.Qt.NoArrow)
        self.tasksToolButton.setObjectName("tasksToolButton")
        self.toolsVerticalLayout.addWidget(self.tasksToolButton)
        self.relationsToolButton = QtGui.QToolButton(item)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.relationsToolButton.sizePolicy().hasHeightForWidth())
        self.relationsToolButton.setSizePolicy(sizePolicy)
        self.relationsToolButton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
        self.relationsToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.relationsToolButton.setAutoRaise(True)
        self.relationsToolButton.setArrowType(QtCore.Qt.NoArrow)
        self.relationsToolButton.setObjectName("relationsToolButton")
        self.toolsVerticalLayout.addWidget(self.relationsToolButton)
        spacerItem1 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Ignored)
        self.toolsVerticalLayout.addItem(spacerItem1)
        self.toolsVerticalLayout.setStretch(2, 1)
        self.gridLayout.addLayout(self.toolsVerticalLayout, 0, 2, 3, 1)
        self.nameVerticalLayout = QtGui.QVBoxLayout()
        self.nameVerticalLayout.setSpacing(0)
        self.nameVerticalLayout.setContentsMargins(-1, -1, -1, 3)
        self.nameVerticalLayout.setObjectName("nameVerticalLayout")
        self.fileNameLabel = QtGui.QLabel(item)
        self.fileNameLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.fileNameLabel.setMaximumSize(QtCore.QSize(16777215, 24))
        font = Qt4Gui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.fileNameLabel.setFont(font)
        self.fileNameLabel.setStyleSheet("QLabel {\n"
"    background-color: transparent;\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 64), stop:1 rgba(128, 128,128, 0));\n"
"}")
        self.fileNameLabel.setTextFormat(QtCore.Qt.PlainText)
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.nameVerticalLayout.addWidget(self.fileNameLabel)
        self.gridLayout.addLayout(self.nameVerticalLayout, 0, 3, 1, 2)
        self.checkBoxHorizontalLayout = QtGui.QHBoxLayout()
        self.checkBoxHorizontalLayout.setSpacing(0)
        self.checkBoxHorizontalLayout.setObjectName("checkBoxHorizontalLayout")
        self.selectedCheckBox = QtGui.QCheckBox(item)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectedCheckBox.sizePolicy().hasHeightForWidth())
        self.selectedCheckBox.setSizePolicy(sizePolicy)
        self.selectedCheckBox.setMinimumSize(QtCore.QSize(30, 0))
        self.selectedCheckBox.setObjectName("selectedCheckBox")
        self.checkBoxHorizontalLayout.addWidget(self.selectedCheckBox)
        self.gridLayout.addLayout(self.checkBoxHorizontalLayout, 1, 4, 1, 1)
        self.descriptionLerticalLayout = QtGui.QVBoxLayout()
        self.descriptionLerticalLayout.setSpacing(0)
        self.descriptionLerticalLayout.setObjectName("descriptionLerticalLayout")
        self.commentLabel = QtGui.QLabel(item)
        self.commentLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.commentLabel.setWordWrap(True)
        self.commentLabel.setMargin(2)
        self.commentLabel.setObjectName("commentLabel")
        self.descriptionLerticalLayout.addWidget(self.commentLabel)
        self.gridLayout.addLayout(self.descriptionLerticalLayout, 2, 3, 1, 2)
        self.infoHorizontalLayout = QtGui.QHBoxLayout()
        self.infoHorizontalLayout.setSpacing(0)
        self.infoHorizontalLayout.setObjectName("infoHorizontalLayout")
        self.gridLayout.addLayout(self.infoHorizontalLayout, 1, 3, 1, 1)
        self.gridLayout.setColumnStretch(3, 1)
        self.gridLayout.setRowStretch(2, 1)

        self.retranslateUi(item)
        QtCore.QMetaObject.connectSlotsByName(item)

    def retranslateUi(self, item):
        item.setWindowTitle(QtGui.QApplication.translate("item", "Form", None))

