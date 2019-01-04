# main_nuke.py
# Start here to run as The Foundry dock

import os
import sys

CURRENT_PATH = '/home/krivospickiy_a/MEGA/Work/CGProjects/tacticbase_dev/TACTIC-handler'

import sys
if CURRENT_PATH not in sys.path:
    sys.path.append(CURRENT_PATH)
import thlib.ui_classes.ui_nuke_dock as main
#reload(main)

main.init_env(CURRENT_PATH)
nuke.pluginAddPath(CURRENT_PATH)

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from nukescripts import panels
import thlib.ui_classes.ui_main_classes as ui_main_classes


class TacticDock(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.setObjectName('TacticDock')
        self.setLayout(QtGui.QVBoxLayout())
        self.window = ui_main_classes.Ui_Main()
        #env.Inst.ui_standalone = self.window
        self.layout().addWidget(self.window)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding))

pane = nuke.getPaneFor('Properties.1')
nuke_panel = panels.registerWidgetAsPanel('TacticDock', 'TACTIC handler', 'uk.co.thefoundry.TacticDock', True).addToPane(pane)

#dir(nuke_panel.customKnob.getObject().widgetClass)
#print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().setContentsMargins(-20,-20,-20,-20))
#print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().parent())  # #MainWindow QMainWindow
#print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent().parent().parent().parent())  # CentralWidget #QSplitter
#print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent().parent().parent())  # MainDock QWidget
#print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent().parent())  # Self Dock QStackedWidget
#print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent().parent())  # Self Dock QDialog
#print(nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent())  # Self Dock QScrollArea

#scrollAreaContents = QtGui.QWidget()
#lay = QtGui.QVBoxLayout(scrollAreaContents)
#lay.addWidget(QtGui.QPushButton('ASSSAAA WIN!'))
#lay.addWidget(lib.ui_main_classes.Ui_Main())
#scroll_area = nuke_panel.customKnob.getObject().widget.parent().parent().parent().parent().parent().parent()

#scroll_area.setWidget(scrollAreaContents)
#scroll_area.setFrameShape(QtGui.QFrame.NoFrame)


"""
from PySide import QtGui, QtCore
import nuke

class MyWidget(QtGui.QWidget):

    def __init__(self, node):
        super(self.__class__, self).__init__()

        self.node = node

        layout = QtGui.QHBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

        btn1 = QtGui.QPushButton('Node Name')
        btn1.clicked.connect(self.btn1Clicked)

        btn2 = QtGui.QPushButton('Print Stuff')
        btn2.clicked.connect(self.btn2Clicked)

        dial = QtGui.QDial()
        dial.valueChanged.connect(self.dialValueChanged)

        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(dial)


    def btn1Clicked(self):
        print self.node.name()

    def btn2Clicked(self):
        print 'Hi, I\'m a button.'
        self.createWrite('asd', 05, 01)

    def dialValueChanged(self):
        print 'Value was just changed!'

    def makeUI(self):
        return self

    def updateValue(self):
        pass

    def createWrite(self, project, shot, version):
        w = nuke.createNode('Write', inpanel=True)
        w['file'].setValue("/projects/{0}/shots/{1}/renders/{2}/{0}_shot{1}_comp_v{2}".format(project, shot, version))

if __name__ == '__main__':
    node = nuke.selectedNode()
    knob = nuke.PyCustom_Knob( "MyWidget", "", "MyWidget(nuke.thisNode())" ) 
    node.addKnob(knob)

"""