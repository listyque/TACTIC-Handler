# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_search_results_tree.ui'
#
# Created: Wed Nov 16 13:24:58 2016
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_resultsForm(object):
    def setupUi(self, resultsForm):
        resultsForm.setObjectName("resultsForm")
        self.resultsLayout = QtGui.QVBoxLayout(resultsForm)
        self.resultsLayout.setSpacing(0)
        self.resultsLayout.setContentsMargins(0, 0, 0, 0)
        self.resultsLayout.setObjectName("resultsLayout")
        self.resultsSplitter = QtGui.QSplitter(resultsForm)
        self.resultsSplitter.setOrientation(QtCore.Qt.Vertical)
        self.resultsSplitter.setObjectName("resultsSplitter")
        self.resultsTreeWidget = QtGui.QTreeWidget(self.resultsSplitter)
        self.resultsTreeWidget.setTabKeyNavigation(True)
        self.resultsTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.resultsTreeWidget.setAllColumnsShowFocus(True)
        self.resultsTreeWidget.setWordWrap(True)
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
        self.resultsVersionsTreeWidget.setRootIsDecorated(False)
        self.resultsVersionsTreeWidget.setAllColumnsShowFocus(True)
        self.resultsVersionsTreeWidget.setWordWrap(True)
        self.resultsVersionsTreeWidget.setHeaderHidden(True)
        self.resultsVersionsTreeWidget.setObjectName("resultsVersionsTreeWidget")
        self.resultsVersionsTreeWidget.headerItem().setText(0, "1")
        self.versionsLayout.addWidget(self.resultsVersionsTreeWidget)
        self.resultsLayout.addWidget(self.resultsSplitter)

        self.retranslateUi(resultsForm)
        QtCore.QMetaObject.connectSlotsByName(resultsForm)

    def retranslateUi(self, resultsForm):
        pass

