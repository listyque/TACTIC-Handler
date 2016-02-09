# module Tree widget item Classes
# file ui_item.py
# Item for TreeWidget

import PySide.QtGui as QtGui
import lib.ui.ui_item_versionless as ui_item

reload(ui_item)


class Ui_versionlessItemWidget(QtGui.QWidget, ui_item.Ui_versionlessItem):
    def __init__(self, item_info, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.item_info = item_info

        # print(self.item_info)
        self.fileNameLabel.setText(self.item_info['file_name'])
        self.sizeLabel.setText(self.item_info['st_size'])
        self.dateLabel.setText(self.item_info['timestamp'])
