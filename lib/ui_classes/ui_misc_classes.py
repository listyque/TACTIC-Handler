import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import lib.ui.misc.ui_collapsable as ui_collapsable


class Ui_collapsableWidget(QtGui.QWidget, ui_collapsable.Ui_collapsableWidget):
    def __init__(self, text=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.collapse_state = False
        self.__collapsedTex = ''
        self.__text = ''

        self.setText(text)
        self.__controlsActions()

    def __controlsActions(self):
        self.collapseToolButton.toggled.connect(self.__toggleCollapseState)

    def setText(self, text):
        self.__text = text
        self.collapseToolButton.setText(self.__text)

    def setCollapsedText(self, text):
        self.__collapsedTex = text
        self.collapseToolButton.setText(self.__collapsedTex)

    def setLayout(self, layout):

        self.widget.setLayout(layout)

    def setCollapsed(self, state):

        if state:
            self.collapse_state = True
            self.collapseToolButton.setArrowType(QtCore.Qt.RightArrow)
            self.widget.setHidden(True)
            if self.__collapsedTex:
                self.setCollapsedText(self.__collapsedTex)
        else:
            self.collapse_state = False
            self.collapseToolButton.setArrowType(QtCore.Qt.DownArrow)
            self.widget.setHidden(False)
            self.setText(self.__text)

    def __toggleCollapseState(self):

        if self.collapse_state:
            self.setCollapsed(False)
        else:
            self.setCollapsed(True)
