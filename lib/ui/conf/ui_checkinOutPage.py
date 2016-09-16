# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf/ui_checkinOutPage.ui'
#
# Created: Fri Sep  9 19:16:52 2016
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_checkinOutPageWidget(object):
    def setupUi(self, checkinOutPageWidget):
        checkinOutPageWidget.setObjectName("checkinOutPageWidget")
        checkinOutPageWidget.resize(729, 471)
        self.checkinOutPageWidgetLayout = QtGui.QGridLayout(checkinOutPageWidget)
        self.checkinOutPageWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.checkinOutPageWidgetLayout.setObjectName("checkinOutPageWidgetLayout")
        self.processTabsFilterGroupBox = QtGui.QGroupBox(checkinOutPageWidget)
        self.processTabsFilterGroupBox.setFlat(True)
        self.processTabsFilterGroupBox.setCheckable(True)
        self.processTabsFilterGroupBox.setChecked(False)
        self.processTabsFilterGroupBox.setObjectName("processTabsFilterGroupBox")
        self.processTabsFilterLayout = QtGui.QVBoxLayout(self.processTabsFilterGroupBox)
        self.processTabsFilterLayout.setContentsMargins(0, -1, 0, -1)
        self.processTabsFilterLayout.setObjectName("processTabsFilterLayout")
        self.processTreeWidget = QtGui.QTreeWidget(self.processTabsFilterGroupBox)
        self.processTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}")
        self.processTreeWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.processTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.processTreeWidget.setObjectName("processTreeWidget")
        self.processTreeWidget.header().setDefaultSectionSize(240)
        self.processTreeWidget.header().setMinimumSectionSize(170)
        self.processTabsFilterLayout.addWidget(self.processTreeWidget)
        self.checkinOutPageWidgetLayout.addWidget(self.processTabsFilterGroupBox, 1, 1, 1, 1)
        self.controlsTabsFilterGroupBox = QtGui.QGroupBox(checkinOutPageWidget)
        self.controlsTabsFilterGroupBox.setFlat(True)
        self.controlsTabsFilterGroupBox.setCheckable(True)
        self.controlsTabsFilterGroupBox.setChecked(False)
        self.controlsTabsFilterGroupBox.setObjectName("controlsTabsFilterGroupBox")
        self.controlsTabsFilterLayout = QtGui.QGridLayout(self.controlsTabsFilterGroupBox)
        self.controlsTabsFilterLayout.setSpacing(6)
        self.controlsTabsFilterLayout.setContentsMargins(0, -1, 0, -1)
        self.controlsTabsFilterLayout.setObjectName("controlsTabsFilterLayout")
        self.controlsTabsTreeWidget = QtGui.QTreeWidget(self.controlsTabsFilterGroupBox)
        self.controlsTabsTreeWidget.setMaximumSize(QtCore.QSize(16777215, 160))
        self.controlsTabsTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}")
        self.controlsTabsTreeWidget.setTabKeyNavigation(True)
        self.controlsTabsTreeWidget.setAlternatingRowColors(True)
        self.controlsTabsTreeWidget.setRootIsDecorated(False)
        self.controlsTabsTreeWidget.setUniformRowHeights(True)
        self.controlsTabsTreeWidget.setItemsExpandable(False)
        self.controlsTabsTreeWidget.setAnimated(True)
        self.controlsTabsTreeWidget.setExpandsOnDoubleClick(False)
        self.controlsTabsTreeWidget.setObjectName("controlsTabsTreeWidget")
        self.controlsTabsTreeWidget.header().setDefaultSectionSize(240)
        self.controlsTabsTreeWidget.header().setMinimumSectionSize(170)
        self.controlsTabsFilterLayout.addWidget(self.controlsTabsTreeWidget, 0, 0, 3, 4)
        self.controlsTabsMoveUpToolButton = QtGui.QToolButton(self.controlsTabsFilterGroupBox)
        self.controlsTabsMoveUpToolButton.setArrowType(QtCore.Qt.UpArrow)
        self.controlsTabsMoveUpToolButton.setObjectName("controlsTabsMoveUpToolButton")
        self.controlsTabsFilterLayout.addWidget(self.controlsTabsMoveUpToolButton, 0, 4, 1, 1)
        self.applyToAllProjectsRadioButton = QtGui.QRadioButton(self.controlsTabsFilterGroupBox)
        self.applyToAllProjectsRadioButton.setChecked(True)
        self.applyToAllProjectsRadioButton.setObjectName("applyToAllProjectsRadioButton")
        self.controlsTabsFilterLayout.addWidget(self.applyToAllProjectsRadioButton, 3, 0, 1, 1)
        self.controlsTabsMoveDownToolButton = QtGui.QToolButton(self.controlsTabsFilterGroupBox)
        self.controlsTabsMoveDownToolButton.setArrowType(QtCore.Qt.DownArrow)
        self.controlsTabsMoveDownToolButton.setObjectName("controlsTabsMoveDownToolButton")
        self.controlsTabsFilterLayout.addWidget(self.controlsTabsMoveDownToolButton, 1, 4, 1, 1)
        self.applyToAllProjectsPushButton = QtGui.QPushButton(self.controlsTabsFilterGroupBox)
        self.applyToAllProjectsPushButton.setEnabled(False)
        self.applyToAllProjectsPushButton.setObjectName("applyToAllProjectsPushButton")
        self.controlsTabsFilterLayout.addWidget(self.applyToAllProjectsPushButton, 3, 2, 1, 1)
        self.applyPerProjectsRadioButton = QtGui.QRadioButton(self.controlsTabsFilterGroupBox)
        self.applyPerProjectsRadioButton.setObjectName("applyPerProjectsRadioButton")
        self.controlsTabsFilterLayout.addWidget(self.applyPerProjectsRadioButton, 3, 1, 1, 1)
        self.checkinOutPageWidgetLayout.addWidget(self.controlsTabsFilterGroupBox, 0, 1, 1, 1)
        self.projectsDisplayTreeWidget = QtGui.QTreeWidget(checkinOutPageWidget)
        self.projectsDisplayTreeWidget.setMaximumSize(QtCore.QSize(300, 16777215))
        self.projectsDisplayTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}")
        self.projectsDisplayTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.projectsDisplayTreeWidget.setRootIsDecorated(False)
        self.projectsDisplayTreeWidget.setObjectName("projectsDisplayTreeWidget")
        self.projectsDisplayTreeWidget.header().setDefaultSectionSize(87)
        self.checkinOutPageWidgetLayout.addWidget(self.projectsDisplayTreeWidget, 0, 0, 3, 1)
        self.checkinOutPageWidgetLayout.setColumnStretch(0, 1)
        self.checkinOutPageWidgetLayout.setRowStretch(1, 1)

        self.retranslateUi(checkinOutPageWidget)
        QtCore.QObject.connect(self.applyPerProjectsRadioButton, QtCore.SIGNAL("toggled(bool)"), self.applyToAllProjectsPushButton.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(checkinOutPageWidget)

    def retranslateUi(self, checkinOutPageWidget):
        self.processTabsFilterGroupBox.setTitle(QtGui.QApplication.translate("checkinOutPageWidget", "Filter Process Tabs (Per Project only)", None, QtGui.QApplication.UnicodeUTF8))
        self.processTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("checkinOutPageWidget", "Type/Title", None, QtGui.QApplication.UnicodeUTF8))
        self.processTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("checkinOutPageWidget", "Code", None, QtGui.QApplication.UnicodeUTF8))
        self.controlsTabsFilterGroupBox.setTitle(QtGui.QApplication.translate("checkinOutPageWidget", "Filter Control Tabs", None, QtGui.QApplication.UnicodeUTF8))
        self.controlsTabsTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("checkinOutPageWidget", "Tab Name", None, QtGui.QApplication.UnicodeUTF8))
        self.controlsTabsTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("checkinOutPageWidget", "Tab Label (Dbl click to Edit)", None, QtGui.QApplication.UnicodeUTF8))
        self.controlsTabsMoveUpToolButton.setText(QtGui.QApplication.translate("checkinOutPageWidget", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.applyToAllProjectsRadioButton.setText(QtGui.QApplication.translate("checkinOutPageWidget", "Choose globally", None, QtGui.QApplication.UnicodeUTF8))
        self.controlsTabsMoveDownToolButton.setText(QtGui.QApplication.translate("checkinOutPageWidget", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.applyToAllProjectsPushButton.setText(QtGui.QApplication.translate("checkinOutPageWidget", "Apply current to All", None, QtGui.QApplication.UnicodeUTF8))
        self.applyPerProjectsRadioButton.setText(QtGui.QApplication.translate("checkinOutPageWidget", "Choose per Project", None, QtGui.QApplication.UnicodeUTF8))
        self.projectsDisplayTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("checkinOutPageWidget", "Category/Title", None, QtGui.QApplication.UnicodeUTF8))
        self.projectsDisplayTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("checkinOutPageWidget", "Code", None, QtGui.QApplication.UnicodeUTF8))

