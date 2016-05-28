# main_nuke.py
# Start here to run as The Foundry dock

import os
import sys

DATA_DIR = os.environ['TACTIC_DATA_DIR'] + '/TACTIC-handler'
nuke.pluginAddPath(DATA_DIR)

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from nukescripts import panels
import lib.environment as env
env.STANDALONE = True
import lib.ui_main_classes


class TacticDock(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.setObjectName('TacticDock')
        self.setLayout(QtGui.QVBoxLayout())
        self.window = lib.ui_main_classes.Ui_Main()
        env.Inst.ui_standalone = self.window
        self.layout().addWidget(self.window)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))

pane = nuke.getPaneFor('Properties.1')
nuke_panel = panels.registerWidgetAsPanel('TacticDock', 'TACTIC handler', 'uk.co.thefoundry.TacticDock', True).addToPane(pane)

dir(nuke_panel.customKnob.getObject().widgetClass)
print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().setContentsMargins(-20,-20,-20,-20))
print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().parent())  # MainWindow QMainWindow
print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent().parent().parent().parent())  # CentralWidget QSplitter
print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent().parent().parent())  # MainDock QWidget
print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent().parent())  # Self Dock QStackedWidget
print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent())  # Self Dock QDialog
print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent())  # Self Dock QScrollArea

scrollAreaContents = QtGui.QWidget()
lay = QtGui.QVBoxLayout(scrollAreaContents)
# lay.addWidget(QtGui.QPushButton('ASSSAAA WIN!'))
lay.addWidget(lib.ui_main_classes.Ui_Main())
scroll_area = nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent()

scroll_area.setWidget(scrollAreaContents)
scroll_area.setFrameShape(QtGui.QFrame.NoFrame)
