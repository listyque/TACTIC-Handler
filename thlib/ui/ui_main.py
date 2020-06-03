# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui_main.ui'
#
# Created: Tue Sep 24 18:40:26 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(u"TACTIC handler")
        self.menuConfig.setTitle(u"Menu")
        self.menuProject.setTitle(u"Projects")
        self.menuUser.setTitle(u"User")
        self.actionConfiguration.setText(u"Configuration")
        self.actionUpdate.setText(u"Update")
        self.actionExit.setText(u"Exit")
        self.actionApply_to_all_Tabs.setText(u"Current view to All Tabs")
        self.actionScriptEditor.setText(u"Script Editor")
        self.actionDock_undock.setText(u"Dock/undock")
        self.actionDebug_Log.setText(u"Debug Log")
        self.actionCheckin_Checkout.setText(u"Checkin / Checkout")
        self.actionMy_Tactic.setText(u"My Tactic")
        self.actionAssets_browser.setText(u"Assets browser")
        self.actionEdit_My_Account.setText(u"Edit My Account")
        self.actionMessages.setText(u"My Messages")
        self.actionDashboard.setText(u"My Dashboard")
        self.actionSave_Preferences.setText(u"Save Preferences")
        self.actionReloadCache.setText(u"Reload Cache")

