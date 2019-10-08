# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'items\ui_notes_outcom.ui'
#
# Created: Sat Oct  5 00:17:16 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_outcom(object):
    def setupUi(self, outcom):
        outcom.setObjectName("outcom")
        outcom.resize(154, 156)
        self.horizontalLayout = QtGui.QHBoxLayout(outcom)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.groupBox_2 = QtGui.QGroupBox(outcom)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setStyleSheet("QGroupBox {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(104, 190, 104, 40));\n"
"    border: 2px solid gray;\n"
"    border-radius: 2px;\n"
"}")
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_5 = QtGui.QGridLayout(self.groupBox_2)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setSpacing(0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.dateLabel = QtGui.QLabel(self.groupBox_2)
        self.dateLabel.setMinimumSize(QtCore.QSize(0, 18))
        font = Qt4Gui.QFont()
        font.setPointSize(10)
        self.dateLabel.setFont(font)
        self.dateLabel.setToolTip("")
        self.dateLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 150, 128, 175));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));\n"
"    padding: 0px;\n"
"}")
        self.dateLabel.setTextFormat(QtCore.Qt.PlainText)
        self.dateLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.dateLabel.setMargin(2)
        self.dateLabel.setObjectName("dateLabel")
        self.gridLayout_5.addWidget(self.dateLabel, 0, 1, 1, 1)
        self.authorFullLabel = QtGui.QLabel(self.groupBox_2)
        self.authorFullLabel.setMinimumSize(QtCore.QSize(0, 50))
        font = Qt4Gui.QFont()
        font.setPointSize(10)
        self.authorFullLabel.setFont(font)
        self.authorFullLabel.setAccessibleDescription("")
        self.authorFullLabel.setStyleSheet("QLabel {\n"
"    padding: 4px;\n"
"}")
        self.authorFullLabel.setTextFormat(QtCore.Qt.PlainText)
        self.authorFullLabel.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.authorFullLabel.setObjectName("authorFullLabel")
        self.gridLayout_5.addWidget(self.authorFullLabel, 2, 0, 1, 1)
        self.commentLabel = QtGui.QLabel(self.groupBox_2)
        self.commentLabel.setTextFormat(QtCore.Qt.RichText)
        self.commentLabel.setScaledContents(True)
        self.commentLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.commentLabel.setWordWrap(True)
        self.commentLabel.setOpenExternalLinks(True)
        self.commentLabel.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard|QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextBrowserInteraction|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.commentLabel.setObjectName("commentLabel")
        self.gridLayout_5.addWidget(self.commentLabel, 1, 1, 2, 1)
        self.authorPicLabel = QtGui.QLabel(self.groupBox_2)
        self.authorPicLabel.setMinimumSize(QtCore.QSize(120, 80))
        self.authorPicLabel.setMaximumSize(QtCore.QSize(120, 120))
        self.authorPicLabel.setTextFormat(QtCore.Qt.RichText)
        self.authorPicLabel.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.authorPicLabel.setMargin(2)
        self.authorPicLabel.setObjectName("authorPicLabel")
        self.gridLayout_5.addWidget(self.authorPicLabel, 1, 0, 1, 1)
        self.authorLabel = QtGui.QLabel(self.groupBox_2)
        self.authorLabel.setMinimumSize(QtCore.QSize(0, 18))
        font = Qt4Gui.QFont()
        font.setPointSize(10)
        font.setWeight(75)
        font.setBold(True)
        self.authorLabel.setFont(font)
        self.authorLabel.setStyleSheet("QLabel {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 150, 128, 175), stop:1 rgba(64, 64,64, 0));\n"
"    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(64, 64, 64, 175), stop:1 rgba(255, 255,255, 0));\n"
"    padding: 0px;\n"
"}")
        self.authorLabel.setTextFormat(QtCore.Qt.PlainText)
        self.authorLabel.setObjectName("authorLabel")
        self.gridLayout_5.addWidget(self.authorLabel, 0, 0, 1, 1)
        self.gridLayout_5.setColumnStretch(1, 1)
        self.gridLayout_5.setRowStretch(2, 1)
        self.horizontalLayout.addWidget(self.groupBox_2)

        self.retranslateUi(outcom)
        QtCore.QMetaObject.connectSlotsByName(outcom)

    def retranslateUi(self, outcom):
        outcom.setWindowTitle(u"Form")
        self.authorFullLabel.setText(u"Алексей Мерзкий\n"
"listy@live.ru")
        self.authorPicLabel.setText(u"<img src=\"D:/APS/OneDrive/Exam_(work_title)/root/admin/login/listy/icon/listy_icon_icon.png\">")

