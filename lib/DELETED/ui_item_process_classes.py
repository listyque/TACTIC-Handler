# module Tree widget item Classes
# file ui_item_process_classes.py
# Process Item for TreeWidget

import PySide.QtGui as QtGui
import lib.ui.ui_item_process as ui_item

reload(ui_item)


class Ui_processItemWidget(QtGui.QWidget, ui_item.Ui_processItem):
    def __init__(self, item_index, process, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'process'
        self.tree_item = None
        # print(tree_item.text(0))
        self.item_info = {}
        self.sobject = sobject
        self.process = process
        self.item_index = item_index

        self.notesToolButton.clicked.connect(lambda: self.prnt())

        self.item_info[
            'description'] = 'This is {0} process item, there is no description, better click on Notes button'.format(
            self.process)

    def prnt(self):
        print(str(self.item_index))
        print(self.tree_item.parent().setExpanded(False))

    def get_description(self):
        return 'No Description for this item "{0}"'.format(self.process)

    def get_skey(self):
        return 'No skey for this item "{0}"'.format(self.process)
