# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items\ui_item_snapshot.ui'
#
# Created: Sat Dec 23 23:34:03 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

class Ui_snapshotItem(object):
    def setupUi(self, snapshotItem):
        snapshotItem.setObjectName("snapshotItem")
        self.gridLayout = QtGui.QGridLayout(snapshotItem)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.previewVerticalLayout = QtGui.QVBoxLayout()
        self.previewVerticalLayout.setSpacing(0)
        self.previewVerticalLayout.setContentsMargins(4, 4, 4, 4)
        self.previewVerticalLayout.setObjectName("previewVerticalLayout")
        self.previewLabel = QtGui.QLabel(snapshotItem)
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
        self.nameVerticalLayout = QtGui.QHBoxLayout()
        self.nameVerticalLayout.setSpacing(0)
        self.nameVerticalLayout.setContentsMargins(-1, -1, -1, 3)
        self.nameVerticalLayout.setObjectName("nameVerticalLayout")
        self.fileNameLabel = QtGui.QLabel(snapshotItem)
        self.fileNameLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.fileNameLabel.setMaximumSize(QtCore.QSize(16777215, 20))
        font = Qt4Gui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.fileNameLabel.setFont(font)
        self.fileNameLabel.setStyleSheet("QLabel {\n"
"    background-color: transparent;\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 64), stop:1 rgba(128, 128,128, 0));\n"
"}")
        self.fileNameLabel.setTextFormat(QtCore.Qt.PlainText)
        self.fileNameLabel.setWordWrap(True)
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.nameVerticalLayout.addWidget(self.fileNameLabel)
        self.sizeLabel = QtGui.QLabel(snapshotItem)
        self.sizeLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.sizeLabel.setMaximumSize(QtCore.QSize(16777215, 20))
        self.sizeLabel.setToolTip("")
        self.sizeLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(64, 64, 64, 175));\n"
"}")
        self.sizeLabel.setTextFormat(QtCore.Qt.PlainText)
        self.sizeLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.sizeLabel.setMargin(2)
        self.sizeLabel.setObjectName("sizeLabel")
        self.nameVerticalLayout.addWidget(self.sizeLabel)
        self.nameVerticalLayout.setStretch(0, 1)
        self.gridLayout.addLayout(self.nameVerticalLayout, 0, 2, 1, 2)
        self.infoHorizontalLayout = QtGui.QHBoxLayout()
        self.infoHorizontalLayout.setSpacing(0)
        self.infoHorizontalLayout.setObjectName("infoHorizontalLayout")
        self.gridLayout.addLayout(self.infoHorizontalLayout, 1, 2, 1, 1)
        self.descriptionLorizontalLayout = QtGui.QHBoxLayout()
        self.descriptionLorizontalLayout.setSpacing(0)
        self.descriptionLorizontalLayout.setObjectName("descriptionLorizontalLayout")
        self.authorLabel = QtGui.QLabel(snapshotItem)
        self.authorLabel.setMinimumSize(QtCore.QSize(0, 25))
        font = Qt4Gui.QFont()
        font.setItalic(True)
        self.authorLabel.setFont(font)
        self.authorLabel.setStyleSheet("color:grey;")
        self.authorLabel.setTextFormat(QtCore.Qt.PlainText)
        self.authorLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.authorLabel.setMargin(2)
        self.authorLabel.setObjectName("authorLabel")
        self.descriptionLorizontalLayout.addWidget(self.authorLabel)
        self.commentLabel = QtGui.QLabel(snapshotItem)
        self.commentLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.commentLabel.setWordWrap(True)
        self.commentLabel.setMargin(2)
        self.commentLabel.setObjectName("commentLabel")
        self.descriptionLorizontalLayout.addWidget(self.commentLabel)
        self.descriptionLorizontalLayout.setStretch(1, 1)
        self.gridLayout.addLayout(self.descriptionLorizontalLayout, 2, 2, 1, 2)
        self.checkBoxHorizontalLayout = QtGui.QHBoxLayout()
        self.checkBoxHorizontalLayout.setSpacing(0)
        self.checkBoxHorizontalLayout.setObjectName("checkBoxHorizontalLayout")
        spacerItem1 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.checkBoxHorizontalLayout.addItem(spacerItem1)
        self.selectedCheckBox = QtGui.QCheckBox(snapshotItem)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selectedCheckBox.sizePolicy().hasHeightForWidth())
        self.selectedCheckBox.setSizePolicy(sizePolicy)
        self.selectedCheckBox.setMinimumSize(QtCore.QSize(30, 0))
        self.selectedCheckBox.setObjectName("selectedCheckBox")
        self.checkBoxHorizontalLayout.addWidget(self.selectedCheckBox)
        self.gridLayout.addLayout(self.checkBoxHorizontalLayout, 1, 3, 1, 1)
        self.itemColorLine = QtGui.QFrame(snapshotItem)
        self.itemColorLine.setMaximumSize(QtCore.QSize(4, 16777215))
        self.itemColorLine.setStyleSheet("QFrame { border: 0px; background-color: green;}\n"
"")
        self.itemColorLine.setFrameShadow(QtGui.QFrame.Plain)
        self.itemColorLine.setLineWidth(4)
        self.itemColorLine.setFrameShape(QtGui.QFrame.VLine)
        self.itemColorLine.setFrameShadow(QtGui.QFrame.Sunken)
        self.itemColorLine.setObjectName("itemColorLine")
        self.gridLayout.addWidget(self.itemColorLine, 0, 0, 3, 1)
        self.gridLayout.setRowStretch(2, 1)

        self.retranslateUi(snapshotItem)
        QtCore.QMetaObject.connectSlotsByName(snapshotItem)

    def retranslateUi(self, snapshotItem):
        snapshotItem.setWindowTitle(QtGui.QApplication.translate("snapshotItem", "Form", None))

