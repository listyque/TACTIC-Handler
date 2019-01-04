# file ui_menu_classes.py

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import thlib.ui.misc.ui_menu as ui_menu
import thlib.global_functions as gf

reload(ui_menu)


class Ui_menuWidget(QtGui.QWidget, ui_menu.Ui_menu):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.horizontalLayout = QtGui.QHBoxLayout(self.buttonLabel)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        self.toolButton = QtGui.QToolButton(self)
        self.toolButton.setAutoRaise(True)
        self.toolButton.setArrowType(QtCore.Qt.DownArrow)
        self.horizontalLayout.addWidget(self.toolButton)
