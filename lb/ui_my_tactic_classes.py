# file ui_my_tactic.py
# My Tactic

import PySide.QtGui as QtGui

import lib.ui.ui_my_tactic as ui_my_tactic

reload(ui_my_tactic)


class Ui_myTacticWidget(QtGui.QWidget, ui_my_tactic.Ui_myTactic):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
