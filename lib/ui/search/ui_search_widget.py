# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'search\ui_search_widget.ui'
#
# Created: Sun Jan 08 00:36:57 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_searchWidget(object):
    def setupUi(self, searchWidget):
        searchWidget.setObjectName("searchWidget")
        self.searchWidgetGridLayout = QtGui.QGridLayout(searchWidget)
        self.searchWidgetGridLayout.setContentsMargins(0, 0, 0, 0)
        self.searchWidgetGridLayout.setSpacing(0)
        self.searchWidgetGridLayout.setObjectName("searchWidgetGridLayout")
        self.searchLineEdit = QtGui.QLineEdit(searchWidget)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.searchLineEdit.setFont(font)
        self.searchLineEdit.setStyleSheet("QLineEdit {\n"
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
        self.searchLineEdit.setFrame(False)
        self.searchLineEdit.setObjectName("searchLineEdit")
        self.searchWidgetGridLayout.addWidget(self.searchLineEdit, 0, 0, 1, 1)
        self.expandingLayout = QtGui.QVBoxLayout()
        self.expandingLayout.setSpacing(0)
        self.expandingLayout.setObjectName("expandingLayout")
        self.searchWidgetGridLayout.addLayout(self.expandingLayout, 0, 1, 1, 1)
        self.gearMenuToolButton = QtGui.QToolButton(searchWidget)
        self.gearMenuToolButton.setMaximumSize(QtCore.QSize(22, 22))
        self.gearMenuToolButton.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.gearMenuToolButton.setAutoRaise(True)
        self.gearMenuToolButton.setArrowType(QtCore.Qt.NoArrow)
        self.gearMenuToolButton.setObjectName("gearMenuToolButton")
        self.searchWidgetGridLayout.addWidget(self.gearMenuToolButton, 0, 2, 1, 1)
        self.searchOptionsSplitter = QtGui.QSplitter(searchWidget)
        self.searchOptionsSplitter.setOrientation(QtCore.Qt.Vertical)
        self.searchOptionsSplitter.setObjectName("searchOptionsSplitter")
        self.searchWidgetGridLayout.addWidget(self.searchOptionsSplitter, 1, 0, 1, 3)
        self.searchWidgetGridLayout.setColumnStretch(0, 1)

        self.retranslateUi(searchWidget)
        QtCore.QMetaObject.connectSlotsByName(searchWidget)

    def retranslateUi(self, searchWidget):
        pass

import lib.ui.resources_rc
