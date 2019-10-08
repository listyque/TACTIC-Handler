# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'misc\ui_snapshot_browser.ui'
#
# Created: Sat Oct  5 00:17:11 2019
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

class Ui_snapshotBrowser(object):
    def setupUi(self, snapshotBrowser):
        snapshotBrowser.setObjectName("snapshotBrowser")
        self.snapshotBrowserLayout = QtGui.QVBoxLayout(snapshotBrowser)
        self.snapshotBrowserLayout.setSpacing(0)
        self.snapshotBrowserLayout.setContentsMargins(0, 0, 0, 0)
        self.snapshotBrowserLayout.setObjectName("snapshotBrowserLayout")
        self.browserSplitter = QtGui.QSplitter(snapshotBrowser)
        self.browserSplitter.setOrientation(QtCore.Qt.Vertical)
        self.browserSplitter.setObjectName("browserSplitter")
        self.verticalLayoutWidget = QtGui.QWidget(self.browserSplitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.imageViewerLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.imageViewerLayout.setSpacing(0)
        self.imageViewerLayout.setContentsMargins(0, 0, 0, 0)
        self.imageViewerLayout.setObjectName("imageViewerLayout")
        self.imagesSlider = QtGui.QSlider(self.verticalLayoutWidget)
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
        self.imageViewerLayout.addWidget(self.imagesSlider)
        self.previewGraphicsView = QtGui.QGraphicsView(self.verticalLayoutWidget)
        self.previewGraphicsView.setFrameShape(QtGui.QFrame.NoFrame)
        self.previewGraphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewGraphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewGraphicsView.setRenderHints(Qt4Gui.QPainter.Antialiasing|Qt4Gui.QPainter.HighQualityAntialiasing|Qt4Gui.QPainter.SmoothPixmapTransform|Qt4Gui.QPainter.TextAntialiasing)
        self.previewGraphicsView.setOptimizationFlags(QtGui.QGraphicsView.DontAdjustForAntialiasing|QtGui.QGraphicsView.DontSavePainterState)
        self.previewGraphicsView.setObjectName("previewGraphicsView")
        self.imageViewerLayout.addWidget(self.previewGraphicsView)
        self.imageViewerLayout.setStretch(1, 1)
        self.gridLayoutWidget = QtGui.QWidget(self.browserSplitter)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.filesBrowserLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.filesBrowserLayout.setContentsMargins(0, 0, 0, 0)
        self.filesBrowserLayout.setObjectName("filesBrowserLayout")
        self.showAllCheckBox = QtGui.QCheckBox(self.gridLayoutWidget)
        self.showAllCheckBox.setObjectName("showAllCheckBox")
        self.filesBrowserLayout.addWidget(self.showAllCheckBox, 1, 0, 1, 1)
        self.showMoreInfoCheckBox = QtGui.QCheckBox(self.gridLayoutWidget)
        self.showMoreInfoCheckBox.setObjectName("showMoreInfoCheckBox")
        self.filesBrowserLayout.addWidget(self.showMoreInfoCheckBox, 1, 1, 1, 1)
        self.filesTreeWidget = QtGui.QTreeWidget(self.gridLayoutWidget)
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
        self.filesBrowserLayout.addWidget(self.filesTreeWidget, 0, 0, 1, 2)
        self.snapshotBrowserLayout.addWidget(self.browserSplitter)

        self.retranslateUi(snapshotBrowser)
        QtCore.QMetaObject.connectSlotsByName(snapshotBrowser)

    def retranslateUi(self, snapshotBrowser):
        self.showAllCheckBox.setText(u"Show All Files")
        self.showMoreInfoCheckBox.setText(u"Show More Info")
        self.filesTreeWidget.headerItem().setText(1, u"Size:")
        self.filesTreeWidget.headerItem().setText(2, u"Path:")
        self.filesTreeWidget.headerItem().setText(3, u"Repo:")
        self.filesTreeWidget.headerItem().setText(4, u"Base Type:")

