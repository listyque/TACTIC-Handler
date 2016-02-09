import sys
from PySide.QtCore import *
from PySide.QtGui import *
  
class RightClickMenuButton(QPushButton):
      
    def __init__(self, name, parent = None):
        super(RightClickMenuButton, self).__init__(name)
          
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        delete = QAction(self)
        delete.setText("remove")
        delete.triggered.connect(self.removeButton)
        self.addAction(delete)
          
    def removeButton(self):
        self.deleteLater()
          
  
if __name__ == '__main__':
    app = QApplication(sys.argv)
    test = QWidget()
      
    layout = QHBoxLayout()
    layout.addWidget(RightClickMenuButton("Test Btn"))
    test.setLayout(layout)
      
    test.show()
    app.exec_()