# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'search/ui_search_results.ui'
#
# Created: Thu Apr 27 14:15:17 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore


class Ui_resultsGroupBox(object):
    def setupUi(self, resultsGroupBox):
        resultsGroupBox.setObjectName("resultsGroupBox")
        resultsGroupBox.setFlat(True)
        self.resultsLayout = QtGui.QVBoxLayout(resultsGroupBox)
        self.resultsLayout.setSpacing(0)
        self.resultsLayout.setContentsMargins(0, 0, 0, 0)
        self.resultsLayout.setObjectName("resultsLayout")
        self.resultsTabWidget = QtGui.QTabWidget(resultsGroupBox)
        self.resultsTabWidget.setStyleSheet("QTabWidget::pane {\n"
"    border: 0px;\n"
"}\n"
"QTabWidget::tab-bar {\n"
"    alignment: left;\n"
"}")
        self.resultsTabWidget.setMovable(True)
        self.resultsTabWidget.setObjectName("resultsTabWidget")
        self.resultsLayout.addWidget(self.resultsTabWidget)

        self.retranslateUi(resultsGroupBox)
        QtCore.QMetaObject.connectSlotsByName(resultsGroupBox)

    def retranslateUi(self, resultsGroupBox):
        resultsGroupBox.setWindowTitle(QtGui.QApplication.translate("resultsGroupBox", "GroupBox", None))
        resultsGroupBox.setTitle(QtGui.QApplication.translate("resultsGroupBox", "Results:", None))

