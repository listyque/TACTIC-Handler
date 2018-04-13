# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'conf/ui_conf_main.ui'
#
# Created: Wed Jan 24 13:57:26 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

class Ui_uiConfMainWidget(object):
    def setupUi(self, uiConfMainWidget):
        uiConfMainWidget.setObjectName("uiConfMainWidget")
        uiConfMainWidget.resize(750, 700)
        self.uiConfMainWidgetLayout = QtGui.QVBoxLayout(uiConfMainWidget)
        self.uiConfMainWidgetLayout.setContentsMargins(0, 0, 0, 0)
        self.uiConfMainWidgetLayout.setObjectName("uiConfMainWidgetLayout")
        self.configToolBox = QtGui.QToolBox(uiConfMainWidget)
        palette = Qt4Gui.QPalette()
        self.configToolBox.setPalette(palette)
        self.configToolBox.setStyleSheet("QToolBox > *,\n"
"QToolBox > QScrollArea > #qt_scrollarea_viewport > QWidget {\n"
"    background-color: rgba(128, 128, 128, 48);\n"
"}\n"
"\n"
"QToolBox::tab {\n"
"    border-style: outset;\n"
"    border-width: 1px;\n"
"    border-color:  rgba(75, 75, 75, 75);\n"
"    border-radius: 3px;\n"
"    padding: 1px;\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 25), stop: 1 rgba(175, 175, 175, 0));\n"
"}\n"
"/*\n"
"QToolBox::tab:hover {\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 50), stop: 1 rgba(175, 175, 175, 0));\n"
"    border: 1px solid rgba(128, 128, 128, 75);\n"
"}\n"
"*/\n"
"QToolBox::tab:selected {\n"
"    font: italic;\n"
"    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 50), stop: 1 rgba(175, 175, 175, 0));\n"
"    border-style: outset;\n"
"    border-width: 1px;\n"
"    border-color:  rgba(128, 128, 128, 75);\n"
"    border-radius: 3px;\n"
"}")
        self.configToolBox.setObjectName("configToolBox")
        self.serverPage = QtGui.QWidget()
        self.serverPage.setGeometry(QtCore.QRect(0, 0, 750, 513))
        self.serverPage.setObjectName("serverPage")
        self.serverPageLayout = QtGui.QVBoxLayout(self.serverPage)
        self.serverPageLayout.setContentsMargins(6, 6, 6, 6)
        self.serverPageLayout.setObjectName("serverPageLayout")
        self.configToolBox.addItem(self.serverPage, "")
        self.projectPage = QtGui.QWidget()
        self.projectPage.setGeometry(QtCore.QRect(0, 0, 759, 494))
        self.projectPage.setObjectName("projectPage")
        self.projectPageLayout = QtGui.QVBoxLayout(self.projectPage)
        self.projectPageLayout.setContentsMargins(6, 6, 6, 6)
        self.projectPageLayout.setObjectName("projectPageLayout")
        self.configToolBox.addItem(self.projectPage, "")
        self.checkinOutOptionsPage = QtGui.QWidget()
        self.checkinOutOptionsPage.setGeometry(QtCore.QRect(0, 0, 759, 494))
        self.checkinOutOptionsPage.setObjectName("checkinOutOptionsPage")
        self.checkinPageLayout = QtGui.QVBoxLayout(self.checkinOutOptionsPage)
        self.checkinPageLayout.setContentsMargins(6, 6, 6, 6)
        self.checkinPageLayout.setObjectName("checkinPageLayout")
        self.configToolBox.addItem(self.checkinOutOptionsPage, "")
        self.checkinOutAppPage = QtGui.QWidget()
        self.checkinOutAppPage.setGeometry(QtCore.QRect(0, 0, 759, 494))
        self.checkinOutAppPage.setObjectName("checkinOutAppPage")
        self.checkinOutPageLayout = QtGui.QVBoxLayout(self.checkinOutAppPage)
        self.checkinOutPageLayout.setContentsMargins(6, 6, 6, 6)
        self.checkinOutPageLayout.setObjectName("checkinOutPageLayout")
        self.configToolBox.addItem(self.checkinOutAppPage, "")
        self.globalCofigPage = QtGui.QWidget()
        self.globalCofigPage.setGeometry(QtCore.QRect(0, 0, 759, 494))
        self.globalCofigPage.setObjectName("globalCofigPage")
        self.globalCofigPageLayout = QtGui.QVBoxLayout(self.globalCofigPage)
        self.globalCofigPageLayout.setContentsMargins(6, 6, 6, 6)
        self.globalCofigPageLayout.setObjectName("globalCofigPageLayout")
        self.configToolBox.addItem(self.globalCofigPage, "")
        self.currentEnvironmentPage = QtGui.QWidget()
        self.currentEnvironmentPage.setGeometry(QtCore.QRect(0, 0, 759, 494))
        self.currentEnvironmentPage.setObjectName("currentEnvironmentPage")
        self.currentEnvironmentPageLayout = QtGui.QVBoxLayout(self.currentEnvironmentPage)
        self.currentEnvironmentPageLayout.setContentsMargins(6, 6, 6, 6)
        self.currentEnvironmentPageLayout.setObjectName("currentEnvironmentPageLayout")
        self.configToolBox.addItem(self.currentEnvironmentPage, "")
        self.uiConfMainWidgetLayout.addWidget(self.configToolBox)
        self.buttonBox = QtGui.QDialogButtonBox(uiConfMainWidget)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Reset)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.uiConfMainWidgetLayout.addWidget(self.buttonBox)

        self.retranslateUi(uiConfMainWidget)
        self.configToolBox.setCurrentIndex(0)
        self.configToolBox.layout().setSpacing(2)
        QtCore.QMetaObject.connectSlotsByName(uiConfMainWidget)

    def retranslateUi(self, uiConfMainWidget):
        uiConfMainWidget.setWindowTitle(QtGui.QApplication.translate("uiConfMainWidget", "TACTIC Handler configuration", None))
        self.configToolBox.setItemText(self.configToolBox.indexOf(self.serverPage), QtGui.QApplication.translate("uiConfMainWidget", "TACTIC Server", None))
        self.configToolBox.setItemText(self.configToolBox.indexOf(self.projectPage), QtGui.QApplication.translate("uiConfMainWidget", "Project", None))
        self.configToolBox.setItemText(self.configToolBox.indexOf(self.checkinOutOptionsPage), QtGui.QApplication.translate("uiConfMainWidget", "Checkin/Checkout Options", None))
        self.configToolBox.setItemText(self.configToolBox.indexOf(self.checkinOutAppPage), QtGui.QApplication.translate("uiConfMainWidget", "Checkin/Checkout Appearance", None))
        self.configToolBox.setItemText(self.configToolBox.indexOf(self.globalCofigPage), QtGui.QApplication.translate("uiConfMainWidget", "Global Config", None))
        self.configToolBox.setItemText(self.configToolBox.indexOf(self.currentEnvironmentPage), QtGui.QApplication.translate("uiConfMainWidget", "Current Environment Options", None))

