# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items/ui_item_snapshot.ui'
#
# Created: Thu Apr 27 14:15:16 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

class Ui_snapshotItem(object):
    def setupUi(self, snapshotItem):
        snapshotItem.setObjectName("snapshotItem")
        snapshotItem.setWindowTitle("")
        snapshotItem.setStyleSheet("QLabel {\n"
"    border: 0px;\n"
"    background: background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(255, 255, 255, 40));\n"
"    padding: 3px;\n"
"}")
        self.versionedLayout = QtGui.QGridLayout(snapshotItem)
        self.versionedLayout.setSizeConstraint(QtGui.QLayout.SetNoConstraint)
        self.versionedLayout.setContentsMargins(0, 0, 0, 0)
        self.versionedLayout.setSpacing(0)
        self.versionedLayout.setObjectName("versionedLayout")
        self.sizeLabel = QtGui.QLabel(snapshotItem)
        self.sizeLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.sizeLabel.setMaximumSize(QtCore.QSize(16777215, 20))
        self.sizeLabel.setToolTip("")
        self.sizeLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(64, 64, 64, 175));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));\n"
"    padding: 0px;\n"
"}")
        self.sizeLabel.setTextFormat(QtCore.Qt.PlainText)
        self.sizeLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.sizeLabel.setMargin(2)
        self.sizeLabel.setObjectName("sizeLabel")
        self.versionedLayout.addWidget(self.sizeLabel, 0, 4, 1, 1)
        self.authorLabel = QtGui.QLabel(snapshotItem)
        self.authorLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.authorLabel.setTextFormat(QtCore.Qt.PlainText)
        self.authorLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.authorLabel.setMargin(2)
        self.authorLabel.setObjectName("authorLabel")
        self.versionedLayout.addWidget(self.authorLabel, 1, 1, 1, 1)
        self.commentLabel = QtGui.QLabel(snapshotItem)
        self.commentLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.commentLabel.setWordWrap(True)
        self.commentLabel.setMargin(2)
        self.commentLabel.setObjectName("commentLabel")
        self.versionedLayout.addWidget(self.commentLabel, 1, 2, 1, 2)
        self.dateLabel = QtGui.QLabel(snapshotItem)
        self.dateLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.dateLabel.setTextFormat(QtCore.Qt.PlainText)
        self.dateLabel.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing)
        self.dateLabel.setMargin(2)
        self.dateLabel.setObjectName("dateLabel")
        self.versionedLayout.addWidget(self.dateLabel, 1, 4, 1, 1)
        self.fileNameLabel = QtGui.QLabel(snapshotItem)
        self.fileNameLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.fileNameLabel.setMaximumSize(QtCore.QSize(16777215, 20))
        self.fileNameLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 175), stop:1 rgba(64, 64,64, 0));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(64, 64, 64, 175), stop:1 rgba(255, 255,255, 0));\n"
"    padding: 0px;\n"
"}")
        self.fileNameLabel.setTextFormat(QtCore.Qt.PlainText)
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.versionedLayout.addWidget(self.fileNameLabel, 0, 1, 1, 2)
        self.verRevLabel = QtGui.QLabel(snapshotItem)
        self.verRevLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.verRevLabel.setMaximumSize(QtCore.QSize(16777215, 20))
        self.verRevLabel.setTextFormat(QtCore.Qt.RichText)
        self.verRevLabel.setObjectName("verRevLabel")
        self.versionedLayout.addWidget(self.verRevLabel, 0, 3, 1, 1)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.versionedLayout.addItem(spacerItem, 2, 2, 1, 1)
        self.previewLabel = QtGui.QLabel(snapshotItem)
        self.previewLabel.setMinimumSize(QtCore.QSize(64, 32))
        self.previewLabel.setMaximumSize(QtCore.QSize(64, 64))
        self.previewLabel.setStyleSheet("#label {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 40), stop: 1 rgba(0, 0, 0, 30));\n"
"    border: 1px solid rgb(96, 96, 96, 64);\n"
"    border-radius: 1px;\n"
"    padding: 0px 0px;\n"
"}")
        self.previewLabel.setTextFormat(QtCore.Qt.RichText)
        self.previewLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.previewLabel.setObjectName("previewLabel")
        self.versionedLayout.addWidget(self.previewLabel, 0, 0, 3, 1)
        self.versionedLayout.setColumnStretch(0, 1)
        self.versionedLayout.setColumnStretch(2, 1)
        self.versionedLayout.setRowStretch(2, 1)

        self.retranslateUi(snapshotItem)
        QtCore.QMetaObject.connectSlotsByName(snapshotItem)

    def retranslateUi(self, snapshotItem):
        pass

