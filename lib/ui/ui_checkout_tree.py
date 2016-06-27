# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/mnt/drive_d/Alexey/Dropbox/Work/CGProjects/tacticbase_dev/TACTIC-handler/lib/ui/ui_checkout_tree.ui'
#
# Created: Thu Jun  9 12:07:02 2016
#      by: pyside-uic 0.2.14 running on PySide 1.2.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_checkOutTree(object):
    def setupUi(self, checkOutTree):
        checkOutTree.setObjectName("checkOutTree")
        checkOutTree.setMinimumSize(QtCore.QSize(400, 250))
        self.verticalLayout = QtGui.QVBoxLayout(checkOutTree)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.commentsSplitter = QtGui.QSplitter(checkOutTree)
        self.commentsSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.commentsSplitter.setObjectName("commentsSplitter")
        self.layoutWidget = QtGui.QWidget(self.commentsSplitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtGui.QGridLayout(self.layoutWidget)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.searchOptionsSplitter = QtGui.QSplitter(self.layoutWidget)
        self.searchOptionsSplitter.setOrientation(QtCore.Qt.Vertical)
        self.searchOptionsSplitter.setHandleWidth(4)
        self.searchOptionsSplitter.setObjectName("searchOptionsSplitter")
        self.verticalLayoutWidget_2 = QtGui.QWidget(self.searchOptionsSplitter)
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.searchOptionsLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget_2)
        self.searchOptionsLayout.setSpacing(0)
        self.searchOptionsLayout.setContentsMargins(0, 0, 0, 0)
        self.searchOptionsLayout.setObjectName("searchOptionsLayout")
        self.resultsGroupBox = QtGui.QGroupBox(self.searchOptionsSplitter)
        self.resultsGroupBox.setFlat(True)
        self.resultsGroupBox.setObjectName("resultsGroupBox")
        self.resultsLayout = QtGui.QVBoxLayout(self.resultsGroupBox)
        self.resultsLayout.setSpacing(0)
        self.resultsLayout.setContentsMargins(0, 0, 0, 0)
        self.resultsLayout.setObjectName("resultsLayout")
        self.resultsSplitter = QtGui.QSplitter(self.resultsGroupBox)
        self.resultsSplitter.setOrientation(QtCore.Qt.Vertical)
        self.resultsSplitter.setObjectName("resultsSplitter")
        self.resultsTreeWidget = QtGui.QTreeWidget(self.resultsSplitter)
        self.resultsTreeWidget.setTabKeyNavigation(True)
        self.resultsTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.resultsTreeWidget.setAllColumnsShowFocus(True)
        self.resultsTreeWidget.setHeaderHidden(True)
        self.resultsTreeWidget.setObjectName("resultsTreeWidget")
        self.resultsTreeWidget.headerItem().setText(0, "1")
        self.verticalLayoutWidget_3 = QtGui.QWidget(self.resultsSplitter)
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.versionsLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget_3)
        self.versionsLayout.setContentsMargins(0, 0, 0, 0)
        self.versionsLayout.setObjectName("versionsLayout")
        self.resultsVersionsTreeWidget = QtGui.QTreeWidget(self.verticalLayoutWidget_3)
        self.resultsVersionsTreeWidget.setTabKeyNavigation(True)
        self.resultsVersionsTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.resultsVersionsTreeWidget.setAllColumnsShowFocus(True)
        self.resultsVersionsTreeWidget.setHeaderHidden(True)
        self.resultsVersionsTreeWidget.setObjectName("resultsVersionsTreeWidget")
        self.resultsVersionsTreeWidget.headerItem().setText(0, "1")
        self.versionsLayout.addWidget(self.resultsVersionsTreeWidget)
        self.resultsLayout.addWidget(self.resultsSplitter)
        self.gridLayout.addWidget(self.searchOptionsSplitter, 1, 0, 1, 5)
        self.searchLineEdit = QtGui.QLineEdit(self.layoutWidget)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.searchLineEdit.setFont(font)
        self.searchLineEdit.setStyleSheet("QLineEdit {\n"
"    color: rgb(192, 192, 192);\n"
"    border: 2px solid darkgray;\n"
"    border-radius: 10px;\n"
"    show-decoration-selected: 1;\n"
"    padding: 0px 8px;\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 255), stop:1 rgba(64, 64,64, 255));\n"
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
        self.searchLineEdit.setFrame(False)
        self.searchLineEdit.setObjectName("searchLineEdit")
        self.gridLayout.addWidget(self.searchLineEdit, 0, 0, 1, 1)
        self.refreshToolButton = QtGui.QToolButton(self.layoutWidget)
        self.refreshToolButton.setMaximumSize(QtCore.QSize(16777215, 20))
        self.refreshToolButton.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.refreshToolButton.setAutoRaise(True)
        self.refreshToolButton.setArrowType(QtCore.Qt.RightArrow)
        self.refreshToolButton.setObjectName("refreshToolButton")
        self.gridLayout.addWidget(self.refreshToolButton, 0, 1, 1, 1)
        self.findOpenedPushButton = QtGui.QPushButton(self.layoutWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.findOpenedPushButton.sizePolicy().hasHeightForWidth())
        self.findOpenedPushButton.setSizePolicy(sizePolicy)
        self.findOpenedPushButton.setMinimumSize(QtCore.QSize(75, 0))
        self.findOpenedPushButton.setMaximumSize(QtCore.QSize(16777215, 20))
        self.findOpenedPushButton.setObjectName("findOpenedPushButton")
        self.gridLayout.addWidget(self.findOpenedPushButton, 0, 3, 1, 1)
        self.contextComboBox = QtGui.QComboBox(self.layoutWidget)
        self.contextComboBox.setMinimumSize(QtCore.QSize(80, 0))
        self.contextComboBox.setEditable(True)
        self.contextComboBox.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.contextComboBox.setObjectName("contextComboBox")
        self.gridLayout.addWidget(self.contextComboBox, 0, 2, 1, 1)
        self.gridLayoutWidget_2 = QtGui.QWidget(self.commentsSplitter)
        self.gridLayoutWidget_2.setObjectName("gridLayoutWidget_2")
        self.commentsLayout = QtGui.QGridLayout(self.gridLayoutWidget_2)
        self.commentsLayout.setSpacing(0)
        self.commentsLayout.setContentsMargins(0, 0, 0, 0)
        self.commentsLayout.setObjectName("commentsLayout")
        self.descriptionSplitter = QtGui.QSplitter(self.gridLayoutWidget_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.descriptionSplitter.sizePolicy().hasHeightForWidth())
        self.descriptionSplitter.setSizePolicy(sizePolicy)
        self.descriptionSplitter.setOrientation(QtCore.Qt.Vertical)
        self.descriptionSplitter.setObjectName("descriptionSplitter")
        self.playblastGroupBox = QtGui.QGroupBox(self.descriptionSplitter)
        self.playblastGroupBox.setFlat(True)
        self.playblastGroupBox.setObjectName("playblastGroupBox")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.playblastGroupBox)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.imagesSplitter = QtGui.QSplitter(self.playblastGroupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.imagesSplitter.sizePolicy().hasHeightForWidth())
        self.imagesSplitter.setSizePolicy(sizePolicy)
        self.imagesSplitter.setMinimumSize(QtCore.QSize(0, 376))
        self.imagesSplitter.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.imagesSplitter.setOrientation(QtCore.Qt.Vertical)
        self.imagesSplitter.setObjectName("imagesSplitter")
        self.layoutWidget1 = QtGui.QWidget(self.imagesSplitter)
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.iconsLayout = QtGui.QVBoxLayout(self.layoutWidget1)
        self.iconsLayout.setSpacing(0)
        self.iconsLayout.setContentsMargins(0, 0, 0, 0)
        self.iconsLayout.setObjectName("iconsLayout")
        self.verticalLayoutWidget = QtGui.QWidget(self.imagesSplitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.playblastLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.playblastLayout.setSpacing(0)
        self.playblastLayout.setContentsMargins(0, 0, 0, 0)
        self.playblastLayout.setContentsMargins(0, 0, 0, 0)
        self.playblastLayout.setObjectName("playblastLayout")
        self.verticalLayout_4.addWidget(self.imagesSplitter)
        self.commentsGroupBox = QtGui.QGroupBox(self.descriptionSplitter)
        self.commentsGroupBox.setMaximumSize(QtCore.QSize(16777215, 250))
        self.commentsGroupBox.setFlat(True)
        self.commentsGroupBox.setObjectName("commentsGroupBox")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.commentsGroupBox)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.editorLayout = QtGui.QVBoxLayout()
        self.editorLayout.setSpacing(0)
        self.editorLayout.setObjectName("editorLayout")
        self.verticalLayout_2.addLayout(self.editorLayout)
        self.descriptionTextEdit = QtGui.QTextEdit(self.commentsGroupBox)
        self.descriptionTextEdit.setObjectName("descriptionTextEdit")
        self.verticalLayout_2.addWidget(self.descriptionTextEdit)
        self.saveDescriprionButton = QtGui.QPushButton(self.commentsGroupBox)
        self.saveDescriprionButton.setObjectName("saveDescriprionButton")
        self.verticalLayout_2.addWidget(self.saveDescriprionButton)
        self.commentsLayout.addWidget(self.descriptionSplitter, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.commentsSplitter)

        self.retranslateUi(checkOutTree)
        QtCore.QMetaObject.connectSlotsByName(checkOutTree)
        checkOutTree.setTabOrder(self.searchLineEdit, self.saveDescriprionButton)
        checkOutTree.setTabOrder(self.saveDescriprionButton, self.descriptionTextEdit)

    def retranslateUi(self, checkOutTree):
        self.resultsGroupBox.setTitle(QtGui.QApplication.translate("checkOutTree", "Results:", None, QtGui.QApplication.UnicodeUTF8))
        self.refreshToolButton.setText(QtGui.QApplication.translate("checkOutTree", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.findOpenedPushButton.setText(QtGui.QApplication.translate("checkOutTree", "Find Opened", None, QtGui.QApplication.UnicodeUTF8))
        self.playblastGroupBox.setTitle(QtGui.QApplication.translate("checkOutTree", "Preview images:", None, QtGui.QApplication.UnicodeUTF8))
        self.commentsGroupBox.setTitle(QtGui.QApplication.translate("checkOutTree", "Description:", None, QtGui.QApplication.UnicodeUTF8))
        self.descriptionTextEdit.setHtml(QtGui.QApplication.translate("checkOutTree", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<table style=\"-qt-table-type: root; margin-top:4px; margin-bottom:4px; margin-left:4px; margin-right:4px;\">\n"
"<tr>\n"
"<td style=\"border: none;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-size:8pt;\"><br /></span></p></td></tr></table></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.saveDescriprionButton.setText(QtGui.QApplication.translate("checkOutTree", "Save description", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
