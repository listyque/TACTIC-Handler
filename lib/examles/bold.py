import sys
from PySide import QtGui, QtCore


class BoldDelegate(QtGui.QStyledItemDelegate):
    def paint(self, painter, option, index):
        # decide here if item should be bold and set font weight to bold if needed 
        option.font.setWeight(QtGui.QFont.Bold)
        QtGui.QStyledItemDelegate.paint(self, painter, option, index)


class MainForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainForm, self).__init__(parent)

        model = QtGui.QStandardItemModel()

        for k in range(0, 4):
            parentItem = model.invisibleRootItem()
            for i in range(0, 4):
                item = QtGui.QStandardItem("item {} {}".format(k, i))
                item.setText('asd')
                parentItem.appendRow(item)
                parentItem = item


        self.view = QtGui.QTreeView()
        self.view.setModel(model)
        self.view.setItemDelegate(BoldDelegate(self))
        # self.view.clicked.connect(lambda: curr_idx(self))

        self.setCentralWidget(self.view)


def curr_idx(idx):
    print(idx)


def main():
    app = QtGui.QApplication(sys.argv)
    form = MainForm()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()