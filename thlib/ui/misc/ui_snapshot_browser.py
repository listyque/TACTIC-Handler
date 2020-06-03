# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_snapshot_browser.ui'
#
# Created: Sat Oct  5 00:17:11 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_snapshotBrowser(object):
    def setupUi(self, snapshotBrowser):
        snapshotBrowser.setObjectName("snapshotBrowser")

        self.retranslateUi(snapshotBrowser)
        QtCore.QMetaObject.connectSlotsByName(snapshotBrowser)

    def retranslateUi(self, snapshotBrowser):
        self.showAllCheckBox.setText(u"Show All Files")
        self.showMoreInfoCheckBox.setText(u"Show More Info")
        self.filesTreeWidget.headerItem().setText(1, u"Size:")
        self.filesTreeWidget.headerItem().setText(2, u"Path:")
        self.filesTreeWidget.headerItem().setText(3, u"Repo:")
        self.filesTreeWidget.headerItem().setText(4, u"Base Type:")

