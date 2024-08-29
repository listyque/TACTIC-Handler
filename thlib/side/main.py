import os
import sys
from PySide2.QtWidgets import QApplication
from editor import CodeEditor


os.environ['QT_AUTO_SCREEN_SCALE_FACTOR '] = '1'
os.environ['QT_SCALE_FACTOR'] = '1'


if __name__ == '__main__':
    app = QApplication(sys.argv)

    editor = CodeEditor()
    editor.show()

    app.exec_()
