# module Rman tools Classes
# file ui_tools_rman_tools_tab_classes.py

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import environment as env
if env.Mode().get == 'maya':
    import maya.cmds as cmds
import lib.ui.ui_tools_rmanToolsTab as ui_tools_rmanToolsTab

reload(ui_tools_rmanToolsTab)


class Ui_rmanToolsTabWidget(QtGui.QWidget, ui_tools_rmanToolsTab.Ui_rmanToolsTab):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.setupUi(self)

        self.tabActions()

    def tabActions(self):
        """
        Actions for the rman tools tab
        """
        attributes = [
            ('rman__torattr___subdivScheme', 0),
            ('rman__torattr___subdivFacevaryingInterp', 3),
            ('rman__riattr__derivatives_extrapolate', True),
            ('rman__riattr__derivatives_centered', False),
            ('rman__riattr__trace_displacements', 1)
        ]
        self.AddRenderAttrsButton.clicked.connect(lambda: self.add_attr(attributes))

    @staticmethod
    def add_attr(attr_list=None):
        """
        Adding custom rmanAtrrs
        """
        selCur = cmds.ls(shapes=True, sl=True, dag=True)
        for node in selCur:
            for attribute, value in attr_list:
                try:
                    if not cmds.attributeQuery(attribute, n=node, exists=True):
                        cmds.addAttr(node, longName=attribute, defaultValue=value)
                    else:
                        cmds.warning('Some Attributes already added! -- ' + attribute + ' on ' + node)
                except:
                    cmds.warning('Some Assert while adding attribute: ' + attribute + ' on ' + node)
                    raise

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup('ui_tools')
        self.settings.beginGroup('rmanToolsTab')
        self.settings.endGroup()
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup('ui_tools')
        self.settings.beginGroup('rmanToolsTab')
        self.settings.setValue('pos', self.pos())
        print('Done ui_tools_rmanToolsTab settings write')
        self.settings.endGroup()
        self.settings.endGroup()

    def closeEvent(self, event):
        # event.ignore()
        self.writeSettings()
        event.accept()
