# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc/ui_search_results.ui'
#
# Created: Sat Nov 19 16:15:34 2016
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

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
        resultsGroupBox.setWindowTitle(QtGui.QApplication.translate("resultsGroupBox", "GroupBox", None, QtGui.QApplication.UnicodeUTF8))
        resultsGroupBox.setTitle(QtGui.QApplication.translate("resultsGroupBox", "Results:", None, QtGui.QApplication.UnicodeUTF8))

