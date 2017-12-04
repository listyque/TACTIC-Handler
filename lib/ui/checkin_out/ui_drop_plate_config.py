# -*- coding: utf-8 -*-

<<<<<<< HEAD
# Form implementation generated from reading ui file 'checkin_out\ui_drop_plate_config.ui'
#
# Created: Thu Nov 23 00:13:03 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
=======
# Form implementation generated from reading ui file 'checkin_out/ui_drop_plate_config.ui'
#
# Created: Fri Nov 10 17:56:09 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
>>>>>>> origin/master
#
# WARNING! All changes made in this file will be lost!

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

class Ui_matchingTemplateConfig(object):
    def setupUi(self, matchingTemplateConfig):
        matchingTemplateConfig.setObjectName("matchingTemplateConfig")
<<<<<<< HEAD
=======
        matchingTemplateConfig.resize(756, 495)
>>>>>>> origin/master
        matchingTemplateConfig.setSizeGripEnabled(True)
        self.gridLayout_2 = QtGui.QGridLayout(matchingTemplateConfig)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.matchingTamplateLabel = QtGui.QLabel(matchingTemplateConfig)
        self.matchingTamplateLabel.setObjectName("matchingTamplateLabel")
        self.gridLayout_2.addWidget(self.matchingTamplateLabel, 0, 0, 1, 1)
<<<<<<< HEAD
=======
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 1, 1, 1)
>>>>>>> origin/master
        self.editSelectedItemButton = QtGui.QToolButton(matchingTemplateConfig)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.editSelectedItemButton.sizePolicy().hasHeightForWidth())
        self.editSelectedItemButton.setSizePolicy(sizePolicy)
        self.editSelectedItemButton.setMinimumSize(QtCore.QSize(70, 0))
        self.editSelectedItemButton.setObjectName("editSelectedItemButton")
        self.gridLayout_2.addWidget(self.editSelectedItemButton, 0, 2, 1, 1)
<<<<<<< HEAD
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 1, 1, 1)
=======
>>>>>>> origin/master
        self.addNewItemButton = QtGui.QToolButton(matchingTemplateConfig)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addNewItemButton.sizePolicy().hasHeightForWidth())
        self.addNewItemButton.setSizePolicy(sizePolicy)
        self.addNewItemButton.setMinimumSize(QtCore.QSize(70, 0))
        self.addNewItemButton.setObjectName("addNewItemButton")
        self.gridLayout_2.addWidget(self.addNewItemButton, 0, 3, 1, 1)
        self.templatesTreeWidget = QtGui.QTreeWidget(matchingTemplateConfig)
        self.templatesTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}\n"
"\n"
"QTreeView::item:selected:active{\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
"    border: 1px solid transparent;\n"
"}\n"
"QTreeView::item:selected:!active {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
"    border: 1px solid transparent;\n"
"}\n"
"")
        self.templatesTreeWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.templatesTreeWidget.setAlternatingRowColors(True)
        self.templatesTreeWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.templatesTreeWidget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.templatesTreeWidget.setRootIsDecorated(False)
        self.templatesTreeWidget.setItemsExpandable(True)
        self.templatesTreeWidget.setObjectName("templatesTreeWidget")
        self.templatesTreeWidget.header().setVisible(True)
        self.gridLayout_2.addWidget(self.templatesTreeWidget, 1, 0, 1, 4)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(matchingTemplateConfig)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.horizontalSlider = QtGui.QSlider(matchingTemplateConfig)
        self.horizontalSlider.setMinimum(1)
        self.horizontalSlider.setMaximum(9)
        self.horizontalSlider.setProperty("value", 3)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.gridLayout.addWidget(self.horizontalSlider, 0, 2, 1, 1)
        self.minFramesPaddingSpinBox = QtGui.QSpinBox(matchingTemplateConfig)
        self.minFramesPaddingSpinBox.setMinimum(1)
        self.minFramesPaddingSpinBox.setMaximum(9)
        self.minFramesPaddingSpinBox.setProperty("value", 3)
        self.minFramesPaddingSpinBox.setObjectName("minFramesPaddingSpinBox")
        self.gridLayout.addWidget(self.minFramesPaddingSpinBox, 0, 1, 1, 1)
<<<<<<< HEAD
        self.oneFrameSequenceDetectionCheckBox = QtGui.QCheckBox(matchingTemplateConfig)
        self.oneFrameSequenceDetectionCheckBox.setChecked(True)
        self.oneFrameSequenceDetectionCheckBox.setObjectName("oneFrameSequenceDetectionCheckBox")
        self.gridLayout.addWidget(self.oneFrameSequenceDetectionCheckBox, 1, 0, 1, 2)
        self.oneUdimDetectionCheckBox = QtGui.QCheckBox(matchingTemplateConfig)
        self.oneUdimDetectionCheckBox.setChecked(True)
        self.oneUdimDetectionCheckBox.setObjectName("oneUdimDetectionCheckBox")
        self.gridLayout.addWidget(self.oneUdimDetectionCheckBox, 1, 2, 1, 1)
=======
>>>>>>> origin/master
        self.gridLayout_2.addLayout(self.gridLayout, 2, 0, 1, 4)

        self.retranslateUi(matchingTemplateConfig)
        QtCore.QObject.connect(self.horizontalSlider, QtCore.SIGNAL("valueChanged(int)"), self.minFramesPaddingSpinBox.setValue)
        QtCore.QObject.connect(self.minFramesPaddingSpinBox, QtCore.SIGNAL("valueChanged(int)"), self.horizontalSlider.setValue)
        QtCore.QMetaObject.connectSlotsByName(matchingTemplateConfig)

    def retranslateUi(self, matchingTemplateConfig):
        matchingTemplateConfig.setWindowTitle(QtGui.QApplication.translate("matchingTemplateConfig", "Dialog", None))
        self.matchingTamplateLabel.setText(QtGui.QApplication.translate("matchingTemplateConfig", "Matching Templates (could interfere with each other):", None))
        self.editSelectedItemButton.setText(QtGui.QApplication.translate("matchingTemplateConfig", "Edit", None))
        self.addNewItemButton.setText(QtGui.QApplication.translate("matchingTemplateConfig", "Add new", None))
        self.templatesTreeWidget.headerItem().setText(0, QtGui.QApplication.translate("matchingTemplateConfig", "Active", None))
        self.templatesTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("matchingTemplateConfig", "Template", None))
        self.templatesTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("matchingTemplateConfig", "Preview", None))
        self.templatesTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("matchingTemplateConfig", "Type", None))
        self.label.setText(QtGui.QApplication.translate("matchingTemplateConfig", "Minimum Frames padding: ", None))
<<<<<<< HEAD
        self.oneFrameSequenceDetectionCheckBox.setText(QtGui.QApplication.translate("matchingTemplateConfig", "Allow Single Frame Sequence", None))
        self.oneUdimDetectionCheckBox.setText(QtGui.QApplication.translate("matchingTemplateConfig", "Allow single UDIM/UV", None))
=======
>>>>>>> origin/master

