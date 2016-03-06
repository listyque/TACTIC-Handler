# file ui_item_task_classes.py
# Notes panel

import PySide.QtGui as QtGui
import lib.ui.ui_item_task as ui_task
import lib.ui.ui_item_task_detail as ui_task_detail

reload(ui_task)
reload(ui_task_detail)


class Ui_taskItemWidget(QtGui.QWidget, ui_task.Ui_taskItem):
    def __init__(self, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.tree_item = tree_item

        self.addToolButton.clicked.connect(self.printparent)

    def printparent(self):
        self.child_item = QtGui.QTreeWidgetItem()
        self.child_item.setText(0, 'Child' + str(self.tree_item.childCount()))
        self.tree_item.addChild(self.child_item)
        self.tree_item.setExpanded(True)
        # self.child_item.setSelected(True)
        # print(self)
        # print(self.parent())
        # print(self.parent().objectName())
        # print(self.parent().parent().objectName())


class Ui_taskItemDetailWidget(QtGui.QWidget, ui_task_detail.Ui_taskDetailItem):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

