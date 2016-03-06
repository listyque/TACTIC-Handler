# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_assets_browser.ui'
#
# Created: Fri Feb 12 18:50:49 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_assetsBrowser(object):
    def setupUi(self, assetsBrowser):
        assetsBrowser.setObjectName("assetsBrowser")
        assetsBrowser.resize(545, 192)
        self.verticalLayout = QtGui.QVBoxLayout(assetsBrowser)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtGui.QSplitter(assetsBrowser)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.assetsTreeWidget = QtGui.QTreeWidget(self.splitter)
        self.assetsTreeWidget.setMinimumSize(QtCore.QSize(120, 0))
        self.assetsTreeWidget.setMaximumSize(QtCore.QSize(200, 16777215))
        self.assetsTreeWidget.setBaseSize(QtCore.QSize(60, 0))
        self.assetsTreeWidget.setObjectName("assetsTreeWidget")
        self.assetsTreeWidget.header().setVisible(False)
        self.verticalLayoutWidget_3 = QtGui.QWidget(self.splitter)
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.searchLineEdit = QtGui.QLineEdit(self.verticalLayoutWidget_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.searchLineEdit.sizePolicy().hasHeightForWidth())
        self.searchLineEdit.setSizePolicy(sizePolicy)
        self.searchLineEdit.setMaximumSize(QtCore.QSize(16777215, 20))
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
        self.verticalLayout_2.addWidget(self.searchLineEdit)
        self.sobjectScrollLayout = QtGui.QVBoxLayout()
        self.sobjectScrollLayout.setSpacing(0)
        self.sobjectScrollLayout.setObjectName("sobjectScrollLayout")
        self.verticalLayout_2.addLayout(self.sobjectScrollLayout)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.countLabel = QtGui.QLabel(self.verticalLayoutWidget_3)
        self.countLabel.setObjectName("countLabel")
        self.horizontalLayout.addWidget(self.countLabel)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label_2 = QtGui.QLabel(self.verticalLayoutWidget_3)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.limitSpinBox = QtGui.QSpinBox(self.verticalLayoutWidget_3)
        self.limitSpinBox.setMinimum(5)
        self.limitSpinBox.setMaximum(500)
        self.limitSpinBox.setSingleStep(5)
        self.limitSpinBox.setProperty("value", 20)
        self.limitSpinBox.setObjectName("limitSpinBox")
        self.horizontalLayout.addWidget(self.limitSpinBox)
        self.label = QtGui.QLabel(self.verticalLayoutWidget_3)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.zoomSpinBox = QtGui.QSpinBox(self.verticalLayoutWidget_3)
        self.zoomSpinBox.setMinimum(25)
        self.zoomSpinBox.setMaximum(400)
        self.zoomSpinBox.setSingleStep(25)
        self.zoomSpinBox.setProperty("value", 100)
        self.zoomSpinBox.setObjectName("zoomSpinBox")
        self.horizontalLayout.addWidget(self.zoomSpinBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout_2.setStretch(1, 1)
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(assetsBrowser)
        QtCore.QMetaObject.connectSlotsByName(assetsBrowser)

    def retranslateUi(self, assetsBrowser):
        assetsBrowser.setWindowTitle(QtGui.QApplication.translate("assetsBrowser", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.assetsTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("assetsBrowser", "all", None, QtGui.QApplication.UnicodeUTF8))
        self.countLabel.setText(QtGui.QApplication.translate("assetsBrowser", "(10/150)", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("assetsBrowser", "Load Limit:", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("assetsBrowser", "Zoom:", None, QtGui.QApplication.UnicodeUTF8))
        self.zoomSpinBox.setSuffix(QtGui.QApplication.translate("assetsBrowser", "%", None, QtGui.QApplication.UnicodeUTF8))

