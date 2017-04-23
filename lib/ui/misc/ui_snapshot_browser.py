# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_snapshot_browser.ui'
#
# Created: Mon Jan 09 23:51:08 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_snapshotBrowser(object):
    def setupUi(self, snapshotBrowser):
        snapshotBrowser.setObjectName("snapshotBrowser")
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(snapshotBrowser.sizePolicy().hasHeightForWidth())
        snapshotBrowser.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(snapshotBrowser)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.imagesSlider = QtGui.QSlider(snapshotBrowser)
        self.imagesSlider.setStyleSheet("QSlider::groove:horizontal {\n"
"    border: 1px solid rgba(128, 128, 128, 40);\n"
"    height: 8px;\n"
"    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(128, 128, 128, 75), stop:1  rgba(128, 128, 128, 40));\n"
"    margin: 2px 0;\n"
"}\n"
"\n"
"QSlider::handle:horizontal {\n"
"    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(128, 128, 128, 40), stop:1 rgba(128, 128, 128, 175));\n"
"    border: 1px solid rgba(128, 128, 128, 40);\n"
"    width: 18px;\n"
"    margin: -2px 0;\n"
"    border-radius: 3px;\n"
"}")
        self.imagesSlider.setMaximum(1)
        self.imagesSlider.setPageStep(1)
        self.imagesSlider.setTracking(True)
        self.imagesSlider.setOrientation(QtCore.Qt.Horizontal)
        self.imagesSlider.setTickPosition(QtGui.QSlider.TicksAbove)
        self.imagesSlider.setObjectName("imagesSlider")
        self.gridLayout.addWidget(self.imagesSlider, 0, 0, 1, 2)
        self.splitter = QtGui.QSplitter(snapshotBrowser)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.previewGraphicsView = QtGui.QGraphicsView(self.splitter)
        self.previewGraphicsView.setFrameShape(QtGui.QFrame.NoFrame)
        self.previewGraphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewGraphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewGraphicsView.setRenderHints(QtGui.QPainter.Antialiasing|QtGui.QPainter.HighQualityAntialiasing|QtGui.QPainter.SmoothPixmapTransform|QtGui.QPainter.TextAntialiasing)
        self.previewGraphicsView.setOptimizationFlags(QtGui.QGraphicsView.DontAdjustForAntialiasing|QtGui.QGraphicsView.DontSavePainterState)
        self.previewGraphicsView.setObjectName("previewGraphicsView")
        self.filesTreeWidget = QtGui.QTreeWidget(self.splitter)
        self.filesTreeWidget.setStyleSheet("QTreeView::item {\n"
"    padding: 2px;\n"
"}\n"
"QTreeView::item:selected:active{\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
"    border: 1px solid transparent;\n"
"}\n"
"QTreeView::item:selected:!active {\n"
"    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
"    border: 1px solid transparent;\n"
"}\n"
"")
        self.filesTreeWidget.setAlternatingRowColors(True)
        self.filesTreeWidget.setHeaderHidden(True)
        self.filesTreeWidget.setObjectName("filesTreeWidget")
        self.filesTreeWidget.headerItem().setText(0, "Snapshot / Type / Name:")
        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 2)
        self.showAllCheckBox = QtGui.QCheckBox(snapshotBrowser)
        self.showAllCheckBox.setObjectName("showAllCheckBox")
        self.gridLayout.addWidget(self.showAllCheckBox, 2, 0, 1, 1)
        self.showMoreInfoCheckBox = QtGui.QCheckBox(snapshotBrowser)
        self.showMoreInfoCheckBox.setObjectName("showMoreInfoCheckBox")
        self.gridLayout.addWidget(self.showMoreInfoCheckBox, 2, 1, 1, 1)

        self.retranslateUi(snapshotBrowser)
        QtCore.QMetaObject.connectSlotsByName(snapshotBrowser)

    def retranslateUi(self, snapshotBrowser):
        self.filesTreeWidget.headerItem().setText(1, QtGui.QApplication.translate("snapshotBrowser", "Size:", None, QtGui.QApplication.UnicodeUTF8))
        self.filesTreeWidget.headerItem().setText(2, QtGui.QApplication.translate("snapshotBrowser", "Path:", None, QtGui.QApplication.UnicodeUTF8))
        self.filesTreeWidget.headerItem().setText(3, QtGui.QApplication.translate("snapshotBrowser", "Repo:", None, QtGui.QApplication.UnicodeUTF8))
        self.filesTreeWidget.headerItem().setText(4, QtGui.QApplication.translate("snapshotBrowser", "Base Type:", None, QtGui.QApplication.UnicodeUTF8))
        self.showAllCheckBox.setText(QtGui.QApplication.translate("snapshotBrowser", "Show All Files", None, QtGui.QApplication.UnicodeUTF8))
        self.showMoreInfoCheckBox.setText(QtGui.QApplication.translate("snapshotBrowser", "Show More Info", None, QtGui.QApplication.UnicodeUTF8))

