# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_assets_browser.ui'
#
# Created: Tue Jan 26 20:02:05 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_assetsBrowser(object):
    def setupUi(self, assetsBrowser):
        assetsBrowser.setObjectName("assetsBrowser")
        assetsBrowser.resize(811, 656)
        self.gridLayout = QtGui.QGridLayout(assetsBrowser)
        self.gridLayout.setObjectName("gridLayout")
        self.treeWidget = QtGui.QTreeWidget(assetsBrowser)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidget.sizePolicy().hasHeightForWidth())
        self.treeWidget.setSizePolicy(sizePolicy)
        self.treeWidget.setMinimumSize(QtCore.QSize(180, 0))
        self.treeWidget.setMaximumSize(QtCore.QSize(180, 16777215))
        self.treeWidget.setObjectName("treeWidget")
        item_0 = QtGui.QTreeWidgetItem(self.treeWidget)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_0 = QtGui.QTreeWidgetItem(self.treeWidget)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        item_1 = QtGui.QTreeWidgetItem(item_0)
        self.treeWidget.header().setVisible(False)
        self.gridLayout.addWidget(self.treeWidget, 0, 0, 1, 1)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.verticalLayout, 0, 1, 1, 1)

        self.retranslateUi(assetsBrowser)
        QtCore.QMetaObject.connectSlotsByName(assetsBrowser)

    def retranslateUi(self, assetsBrowser):
        assetsBrowser.setWindowTitle(QtGui.QApplication.translate("assetsBrowser", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.headerItem().setText(0, QtGui.QApplication.translate("assetsBrowser", "all", None, QtGui.QApplication.UnicodeUTF8))
        __sortingEnabled = self.treeWidget.isSortingEnabled()
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.topLevelItem(0).setText(0, QtGui.QApplication.translate("assetsBrowser", "Assets", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(0).child(0).setText(0, QtGui.QApplication.translate("assetsBrowser", "Sets", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(0).child(1).setText(0, QtGui.QApplication.translate("assetsBrowser", "Scenes", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(0).child(2).setText(0, QtGui.QApplication.translate("assetsBrowser", "Characters", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(0).child(3).setText(0, QtGui.QApplication.translate("assetsBrowser", "Props", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).setText(0, QtGui.QApplication.translate("assetsBrowser", "Vfx", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).child(0).setText(0, QtGui.QApplication.translate("assetsBrowser", "VFX", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).child(1).setText(0, QtGui.QApplication.translate("assetsBrowser", "Dynamics", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).child(2).setText(0, QtGui.QApplication.translate("assetsBrowser", "Fluids", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.topLevelItem(1).child(3).setText(0, QtGui.QApplication.translate("assetsBrowser", "Cloth", None, QtGui.QApplication.UnicodeUTF8))
        self.treeWidget.setSortingEnabled(__sortingEnabled)

