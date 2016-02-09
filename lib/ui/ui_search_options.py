# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_search_options.ui'
#
# Created: Sat Jan 30 13:06:46 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_searchOptionsGroupBox(object):
    def setupUi(self, searchOptionsGroupBox):
        searchOptionsGroupBox.setObjectName("searchOptionsGroupBox")
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(searchOptionsGroupBox.sizePolicy().hasHeightForWidth())
        searchOptionsGroupBox.setSizePolicy(sizePolicy)
        searchOptionsGroupBox.setFlat(True)
        self.gridLayout = QtGui.QGridLayout(searchOptionsGroupBox)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(4, 2, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.byNameRadioButton = QtGui.QRadioButton(searchOptionsGroupBox)
        self.byNameRadioButton.setChecked(True)
        self.byNameRadioButton.setObjectName("byNameRadioButton")
        self.gridLayout.addWidget(self.byNameRadioButton, 0, 0, 1, 1)
        self.byCodeRadioButton = QtGui.QRadioButton(searchOptionsGroupBox)
        self.byCodeRadioButton.setObjectName("byCodeRadioButton")
        self.gridLayout.addWidget(self.byCodeRadioButton, 0, 1, 1, 1)
        self.showAllProcessCheckBox = QtGui.QCheckBox(searchOptionsGroupBox)
        self.showAllProcessCheckBox.setChecked(True)
        self.showAllProcessCheckBox.setObjectName("showAllProcessCheckBox")
        self.gridLayout.addWidget(self.showAllProcessCheckBox, 1, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 5, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 2, 0, 1, 1)
        self.byDescriptionRadioButton = QtGui.QRadioButton(searchOptionsGroupBox)
        self.byDescriptionRadioButton.setObjectName("byDescriptionRadioButton")
        self.gridLayout.addWidget(self.byDescriptionRadioButton, 0, 3, 1, 1)
        self.byKeywordsRadioButton = QtGui.QRadioButton(searchOptionsGroupBox)
        self.byKeywordsRadioButton.setObjectName("byKeywordsRadioButton")
        self.gridLayout.addWidget(self.byKeywordsRadioButton, 0, 2, 1, 1)
        self.saveAsDefaultToolButton = QtGui.QToolButton(searchOptionsGroupBox)
        self.saveAsDefaultToolButton.setAutoRaise(True)
        self.saveAsDefaultToolButton.setObjectName("saveAsDefaultToolButton")
        self.gridLayout.addWidget(self.saveAsDefaultToolButton, 0, 4, 1, 1)

        self.retranslateUi(searchOptionsGroupBox)
        QtCore.QMetaObject.connectSlotsByName(searchOptionsGroupBox)

    def retranslateUi(self, searchOptionsGroupBox):
        searchOptionsGroupBox.setWindowTitle(QtGui.QApplication.translate("searchOptionsGroupBox", "GroupBox", None, QtGui.QApplication.UnicodeUTF8))
        searchOptionsGroupBox.setTitle(QtGui.QApplication.translate("searchOptionsGroupBox", "Search Options:", None, QtGui.QApplication.UnicodeUTF8))
        self.byNameRadioButton.setText(QtGui.QApplication.translate("searchOptionsGroupBox", "by Name", None, QtGui.QApplication.UnicodeUTF8))
        self.byCodeRadioButton.setText(QtGui.QApplication.translate("searchOptionsGroupBox", "by Search Code", None, QtGui.QApplication.UnicodeUTF8))
        self.showAllProcessCheckBox.setText(QtGui.QApplication.translate("searchOptionsGroupBox", "Show all Process", None, QtGui.QApplication.UnicodeUTF8))
        self.byDescriptionRadioButton.setText(QtGui.QApplication.translate("searchOptionsGroupBox", "by Description", None, QtGui.QApplication.UnicodeUTF8))
        self.byKeywordsRadioButton.setText(QtGui.QApplication.translate("searchOptionsGroupBox", "by Keywords", None, QtGui.QApplication.UnicodeUTF8))
        self.saveAsDefaultToolButton.setText(QtGui.QApplication.translate("searchOptionsGroupBox", "Save as Default", None, QtGui.QApplication.UnicodeUTF8))

