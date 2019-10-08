# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tasks\ui_float_notify.ui'
#
# Created: Sat Oct  5 00:17:08 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_floatNotify(object):
    def setupUi(self, floatNotify):
        floatNotify.setObjectName("floatNotify")
        floatNotify.resize(250, 87)
        floatNotify.setMinimumSize(QtCore.QSize(250, 80))
        self.gridLayout_2 = QtGui.QGridLayout(floatNotify)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.viewToolButton = QtGui.QToolButton(floatNotify)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.viewToolButton.sizePolicy().hasHeightForWidth())
        self.viewToolButton.setSizePolicy(sizePolicy)
        self.viewToolButton.setAutoRaise(True)
        self.viewToolButton.setObjectName("viewToolButton")
        self.gridLayout.addWidget(self.viewToolButton, 0, 0, 3, 1)
        self.nextToolButton = QtGui.QToolButton(floatNotify)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.nextToolButton.sizePolicy().hasHeightForWidth())
        self.nextToolButton.setSizePolicy(sizePolicy)
        self.nextToolButton.setMaximumSize(QtCore.QSize(30, 20))
        self.nextToolButton.setAutoRaise(True)
        self.nextToolButton.setArrowType(QtCore.Qt.RightArrow)
        self.nextToolButton.setObjectName("nextToolButton")
        self.gridLayout.addWidget(self.nextToolButton, 0, 5, 1, 1)
        self.prevToolButton = QtGui.QToolButton(floatNotify)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.prevToolButton.sizePolicy().hasHeightForWidth())
        self.prevToolButton.setSizePolicy(sizePolicy)
        self.prevToolButton.setMaximumSize(QtCore.QSize(30, 20))
        self.prevToolButton.setAutoRaise(True)
        self.prevToolButton.setArrowType(QtCore.Qt.LeftArrow)
        self.prevToolButton.setObjectName("prevToolButton")
        self.gridLayout.addWidget(self.prevToolButton, 0, 4, 1, 1)
        self.skipToolButton = QtGui.QToolButton(floatNotify)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.skipToolButton.sizePolicy().hasHeightForWidth())
        self.skipToolButton.setSizePolicy(sizePolicy)
        self.skipToolButton.setAutoRaise(True)
        self.skipToolButton.setObjectName("skipToolButton")
        self.gridLayout.addWidget(self.skipToolButton, 0, 1, 3, 1)
        self.hideToolButton = QtGui.QToolButton(floatNotify)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.hideToolButton.sizePolicy().hasHeightForWidth())
        self.hideToolButton.setSizePolicy(sizePolicy)
        self.hideToolButton.setMaximumSize(QtCore.QSize(16777215, 20))
        self.hideToolButton.setAutoRaise(True)
        self.hideToolButton.setArrowType(QtCore.Qt.DownArrow)
        self.hideToolButton.setObjectName("hideToolButton")
        self.gridLayout.addWidget(self.hideToolButton, 2, 4, 1, 2)
        self.posLabel = QtGui.QLabel(floatNotify)
        self.posLabel.setMaximumSize(QtCore.QSize(16777215, 18))
        self.posLabel.setAccessibleDescription("")
        self.posLabel.setStyleSheet("QLabel {\n"
"    padding: 4px;\n"
"}")
        self.posLabel.setTextFormat(QtCore.Qt.PlainText)
        self.posLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.posLabel.setObjectName("posLabel")
        self.gridLayout.addWidget(self.posLabel, 0, 2, 1, 1)
        self.dateLabel = QtGui.QLabel(floatNotify)
        self.dateLabel.setMaximumSize(QtCore.QSize(16777215, 18))
        self.dateLabel.setAccessibleDescription("")
        self.dateLabel.setStyleSheet("QLabel {\n"
"    padding: 4px;\n"
"}")
        self.dateLabel.setTextFormat(QtCore.Qt.PlainText)
        self.dateLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.dateLabel.setObjectName("dateLabel")
        self.gridLayout.addWidget(self.dateLabel, 2, 2, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 2, 0, 1, 3)
        self.noteNameLabel = QtGui.QLabel(floatNotify)
        self.noteNameLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.noteNameLabel.setMaximumSize(QtCore.QSize(16777215, 20))
        self.noteNameLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 0), stop:1 rgba(255, 255,255, 75));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 75), stop:1 rgba(255, 255,255, 0));\n"
"    padding: 0px;\n"
"}")
        self.noteNameLabel.setTextFormat(QtCore.Qt.PlainText)
        self.noteNameLabel.setObjectName("noteNameLabel")
        self.gridLayout_2.addWidget(self.noteNameLabel, 0, 0, 1, 2)
        self.notePathLabel = QtGui.QLabel(floatNotify)
        self.notePathLabel.setMinimumSize(QtCore.QSize(0, 20))
        self.notePathLabel.setMaximumSize(QtCore.QSize(16777215, 20))
        self.notePathLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 75), stop:1 rgba(64, 64,64, 0));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(64, 64, 64, 0), stop:1 rgba(255, 255,255, 75));\n"
"    padding: 0px;\n"
"}")
        self.notePathLabel.setTextFormat(QtCore.Qt.PlainText)
        self.notePathLabel.setObjectName("notePathLabel")
        self.gridLayout_2.addWidget(self.notePathLabel, 0, 2, 1, 1)
        self.authorLabel = QtGui.QLabel(floatNotify)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.authorLabel.sizePolicy().hasHeightForWidth())
        self.authorLabel.setSizePolicy(sizePolicy)
        self.authorLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.authorLabel.setTextFormat(QtCore.Qt.PlainText)
        self.authorLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.authorLabel.setMargin(2)
        self.authorLabel.setObjectName("authorLabel")
        self.gridLayout_2.addWidget(self.authorLabel, 1, 0, 1, 1)
        self.commentLabel = QtGui.QLabel(floatNotify)
        self.commentLabel.setMinimumSize(QtCore.QSize(0, 25))
        self.commentLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 0), stop:1 rgba(0, 0,0, 75));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(255, 255,255, 75));\n"
"}")
        self.commentLabel.setTextFormat(QtCore.Qt.PlainText)
        self.commentLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.commentLabel.setWordWrap(True)
        self.commentLabel.setMargin(2)
        self.commentLabel.setObjectName("commentLabel")
        self.gridLayout_2.addWidget(self.commentLabel, 1, 1, 1, 2)
        self.gridLayout_2.setRowStretch(1, 1)

        self.retranslateUi(floatNotify)
        QtCore.QMetaObject.connectSlotsByName(floatNotify)

    def retranslateUi(self, floatNotify):
        self.viewToolButton.setText(QtGui.QApplication.translate("floatNotify", "View", None, QtGui.QApplication.UnicodeUTF8))
        self.nextToolButton.setText(QtGui.QApplication.translate("floatNotify", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.prevToolButton.setText(QtGui.QApplication.translate("floatNotify", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.skipToolButton.setText(QtGui.QApplication.translate("floatNotify", "Skip", None, QtGui.QApplication.UnicodeUTF8))
        self.hideToolButton.setText(QtGui.QApplication.translate("floatNotify", "Hide", None, QtGui.QApplication.UnicodeUTF8))
        self.posLabel.setText(QtGui.QApplication.translate("floatNotify", "5/10", None, QtGui.QApplication.UnicodeUTF8))
        self.dateLabel.setText(QtGui.QApplication.translate("floatNotify", "2016-01-26 14:19:57", None, QtGui.QApplication.UnicodeUTF8))
        self.noteNameLabel.setText(QtGui.QApplication.translate("floatNotify", "Task changed in:", None, QtGui.QApplication.UnicodeUTF8))
        self.notePathLabel.setText(QtGui.QApplication.translate("floatNotify", "Props / Mushroom / The Pirate", None, QtGui.QApplication.UnicodeUTF8))
        self.authorLabel.setText(QtGui.QApplication.translate("floatNotify", "Author:", None, QtGui.QApplication.UnicodeUTF8))
        self.commentLabel.setText(QtGui.QApplication.translate("floatNotify", "Comment....", None, QtGui.QApplication.UnicodeUTF8))

