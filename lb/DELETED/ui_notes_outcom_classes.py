# file ui_notes_outcom_classes.py

import PySide.QtGui as QtGui
import lib.ui.ui_notes_outcom as ui_outcom

reload(ui_outcom)


class Ui_outcomWidget(QtGui.QWidget, ui_outcom.Ui_outcom):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
