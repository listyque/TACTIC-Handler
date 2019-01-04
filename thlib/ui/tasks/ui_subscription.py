# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tasks/ui_subscription.ui'
#
# Created: Thu Apr 27 14:15:15 2017
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore


class Ui_subscription(object):
    def setupUi(self, subscription):
        subscription.setObjectName("subscription")
        subscription.resize(765, 544)

        self.retranslateUi(subscription)
        QtCore.QMetaObject.connectSlotsByName(subscription)

    def retranslateUi(self, subscription):
        subscription.setWindowTitle(QtGui.QApplication.translate("subscription", "Form", None))

