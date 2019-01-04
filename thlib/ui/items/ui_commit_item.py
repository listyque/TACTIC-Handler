# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items/ui_commit_item.ui'
#
# Created: Tue May  8 15:31:12 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_commitItem(object):
    def setupUi(self, commitItem):
        commitItem.setObjectName("commitItem")
        commitItem.resize(84, 72)
        self.gridLayout = QtGui.QGridLayout(commitItem)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.previewVerticalLayout = QtGui.QVBoxLayout()
        self.previewVerticalLayout.setSpacing(0)
        self.previewVerticalLayout.setContentsMargins(4, 4, 4, 4)
        self.previewVerticalLayout.setObjectName("previewVerticalLayout")
        self.previewLabel = QtGui.QLabel(commitItem)
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
        self.gridLayout.addLayout(self.previewVerticalLayout, 0, 0, 3, 1)
        self.nameVerticalLayout = QtGui.QVBoxLayout()
        self.nameVerticalLayout.setSpacing(0)
        self.nameVerticalLayout.setContentsMargins(-1, -1, -1, 3)
        self.nameVerticalLayout.setObjectName("nameVerticalLayout")
        self.fileNameLabel = QtGui.QLabel(commitItem)
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
        self.gridLayout.addLayout(self.nameVerticalLayout, 0, 1, 1, 2)
        self.descriptionLerticalLayout = QtGui.QVBoxLayout()
        self.descriptionLerticalLayout.setSpacing(0)
        self.descriptionLerticalLayout.setObjectName("descriptionLerticalLayout")
        self.commentLabel = QtGui.QLabel(commitItem)
        self.commentLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.commentLabel.setWordWrap(True)
        self.commentLabel.setMargin(2)
        self.commentLabel.setObjectName("commentLabel")
        self.descriptionLerticalLayout.addWidget(self.commentLabel)
        self.gridLayout.addLayout(self.descriptionLerticalLayout, 2, 1, 1, 2)
        self.infoHorizontalLayout = QtGui.QHBoxLayout()
        self.infoHorizontalLayout.setSpacing(0)
        self.infoHorizontalLayout.setObjectName("infoHorizontalLayout")
        self.gridLayout.addLayout(self.infoHorizontalLayout, 1, 1, 1, 2)
        self.gridLayout.setColumnStretch(1, 1)
        self.gridLayout.setColumnStretch(2, 1)

        self.retranslateUi(commitItem)
        QtCore.QMetaObject.connectSlotsByName(commitItem)

    def retranslateUi(self, commitItem):
        commitItem.setWindowTitle(QtGui.QApplication.translate("commitItem", "Form", None))

