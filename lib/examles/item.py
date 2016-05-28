import PySide.QtGui as QtGui
import ui_item


class Ui_itemWidget(QtGui.QWidget, ui_item.Ui_item):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)