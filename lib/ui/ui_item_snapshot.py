# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_item_snapshot.ui'
#
# Created: Sat Jan 23 22:05:42 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_snapshotItem(object):
    def setupUi(self, snapshotItem):
        snapshotItem.setObjectName("snapshotItem")
        snapshotItem.resize(187, 44)
        snapshotItem.setWindowTitle("")
        snapshotItem.setStyleSheet("QLabel {\n"
"    border: 0px;\n"
"    background: background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(255, 255, 255, 40));\n"
"    padding: 3px;\n"
"}")
        self.versionedLayout = QtGui.QGridLayout(snapshotItem)
        self.versionedLayout.setContentsMargins(0, 0, 0, 0)
        self.versionedLayout.setSpacing(0)
        self.versionedLayout.setObjectName("versionedLayout")
        self.sizeLabel = QtGui.QLabel(snapshotItem)
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
        self.versionedLayout.addWidget(self.sizeLabel, 0, 2, 1, 1)
        self.authorLabel = QtGui.QLabel(snapshotItem)
        self.authorLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.authorLabel.setTextFormat(QtCore.Qt.PlainText)
        self.authorLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.authorLabel.setMargin(2)
        self.authorLabel.setObjectName("authorLabel")
        self.versionedLayout.addWidget(self.authorLabel, 1, 0, 1, 1)
        self.commentLabel = QtGui.QLabel(snapshotItem)
        self.commentLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.commentLabel.setWordWrap(True)
        self.commentLabel.setMargin(2)
        self.commentLabel.setObjectName("commentLabel")
        self.versionedLayout.addWidget(self.commentLabel, 1, 1, 1, 1)
        self.dateLabel = QtGui.QLabel(snapshotItem)
        self.dateLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.dateLabel.setAccessibleDescription("")
        self.dateLabel.setStyleSheet("QLabel {\n"
"    padding: 4px;\n"
"}")
        self.dateLabel.setTextFormat(QtCore.Qt.PlainText)
        self.dateLabel.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing)
        self.dateLabel.setObjectName("dateLabel")
        self.versionedLayout.addWidget(self.dateLabel, 1, 2, 1, 1)
        self.fileNameLabel = QtGui.QLabel(snapshotItem)
        self.fileNameLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 175), stop:1 rgba(64, 64,64, 0));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(64, 64, 64, 175), stop:1 rgba(255, 255,255, 0));\n"
"    padding: 0px;\n"
"}")
        self.fileNameLabel.setTextFormat(QtCore.Qt.PlainText)
        self.fileNameLabel.setObjectName("fileNameLabel")
        self.versionedLayout.addWidget(self.fileNameLabel, 0, 0, 1, 2)
        self.versionedLayout.setColumnStretch(1, 1)

        self.retranslateUi(snapshotItem)
        QtCore.QMetaObject.connectSlotsByName(snapshotItem)

    def retranslateUi(self, snapshotItem):
        pass

