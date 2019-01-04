# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf/ui_projectPage.ui'
#
# Created: Thu Apr 27 14:15:16 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore


class Ui_projectPageWidget(object):
    def setupUi(self, projectPageWidget):
        projectPageWidget.setObjectName("projectPageWidget")
        projectPageWidget.resize(546, 233)
        self.projectPageWidgetLayout = QtGui.QGridLayout(projectPageWidget)
        self.projectPageWidgetLayout.setContentsMargins(6, 6, 6, 6)
        self.projectPageWidgetLayout.setObjectName("projectPageWidgetLayout")
        self.projectsTreeWidget = QtGui.QTreeWidget(projectPageWidget)
        self.projectsTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}")
        self.projectsTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.projectsTreeWidget.setObjectName("projectsTreeWidget")
        self.projectsTreeWidget.header().setDefaultSectionSize(87)
        self.projectPageWidgetLayout.addWidget(self.projectsTreeWidget, 0, 0, 1, 6)
        self.createProjectsLable = QtGui.QLabel(projectPageWidget)
        self.createProjectsLable.setObjectName("createProjectsLable")
        self.projectPageWidgetLayout.addWidget(self.createProjectsLable, 1, 0, 1, 1)
        self.createProjectPushButton = QtGui.QPushButton(projectPageWidget)
        self.createProjectPushButton.setEnabled(False)
        self.createProjectPushButton.setObjectName("createProjectPushButton")
        self.projectPageWidgetLayout.addWidget(self.createProjectPushButton, 1, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.projectPageWidgetLayout.addItem(spacerItem, 1, 2, 1, 1)
        self.colorSchemeHintLabel = QtGui.QLabel(projectPageWidget)
        self.colorSchemeHintLabel.setObjectName("colorSchemeHintLabel")
        self.projectPageWidgetLayout.addWidget(self.colorSchemeHintLabel, 1, 3, 1, 1)
        self.currentProjectLabel = QtGui.QLabel(projectPageWidget)
        self.currentProjectLabel.setStyleSheet("QLabel {background : rgb(165, 175, 25);}")
        self.currentProjectLabel.setTextFormat(QtCore.Qt.PlainText)
        self.currentProjectLabel.setObjectName("currentProjectLabel")
        self.projectPageWidgetLayout.addWidget(self.currentProjectLabel, 1, 4, 1, 1)
        self.templateProjectsLabel = QtGui.QLabel(projectPageWidget)
        self.templateProjectsLabel.setStyleSheet("QLabel {background :rgb(50, 150, 175)}")
        self.templateProjectsLabel.setTextFormat(QtCore.Qt.PlainText)
        self.templateProjectsLabel.setObjectName("templateProjectsLabel")
        self.projectPageWidgetLayout.addWidget(self.templateProjectsLabel, 1, 5, 1, 1)

        self.retranslateUi(projectPageWidget)
        QtCore.QMetaObject.connectSlotsByName(projectPageWidget)

    def retranslateUi(self, projectPageWidget):
        self.projectsTreeWidget.setToolTip(QtGui.QApplication.translate("projectPageWidget", "Right click for menu", None))
        self.projectsTreeWidget.setStatusTip(QtGui.QApplication.translate("projectPageWidget", "Right click for menu", None))
        self.projectsTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("projectPageWidget", "Category/Title", None))
        self.projectsTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("projectPageWidget", "Code", None))
        self.projectsTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("projectPageWidget", "Namespace (template)", None))
        self.projectsTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("projectPageWidget", "Status", None))
        self.createProjectsLable.setText(QtGui.QApplication.translate("projectPageWidget", "Create new Project:", None))
        self.createProjectPushButton.setText(QtGui.QApplication.translate("projectPageWidget", "Create", None))
        self.colorSchemeHintLabel.setText(QtGui.QApplication.translate("projectPageWidget", "Legend: ", None))
        self.currentProjectLabel.setText(QtGui.QApplication.translate("projectPageWidget", " Current Projects ", None))
        self.templateProjectsLabel.setText(QtGui.QApplication.translate("projectPageWidget", " Template Projects ", None))

