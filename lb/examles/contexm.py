import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

data = [
    ("Alice", [
        ("Keys", []),
        ("Purse", [
            ("Cellphone", [])
            ])
        ]),
    ("Bob", [
        ("Wallet", [
            ("Credit card", []),
            ("Money", [])
            ])
        ])
    ]

class Window(QWidget):

    def __init__(self):
    
        QWidget.__init__(self)
        
        self.treeView = QTreeView()
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.openMenu)
        
        self.model = QStandardItemModel()
        self.addItems(self.model, data)
        self.treeView.setModel(self.model)
        
        self.model.setHorizontalHeaderLabels([self.tr("Object")])
        
        layout = QVBoxLayout()
        layout.addWidget(self.treeView)
        self.setLayout(layout)
    
    def addItems(self, parent, elements):
    
        for text, children in elements:
            item = QStandardItem(text)
            parent.appendRow(item)
            if children:
                self.addItems(item, children)
    
    def openMenu(self, position):
    
        indexes = self.treeView.selectedIndexes()
        if len(indexes) > 0:
        
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        
        menu = QMenu()
        if level == 0:
            menu.addAction(self.tr("Edit person"))
        elif level == 1:
            menu.addAction(self.tr("Edit object/container"))
        elif level == 2:
            menu.addAction(self.tr("Edit object"))
        
        menu.exec_(self.treeView.viewport().mapToGlobal(position))


if __name__ == "__main__":

    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())