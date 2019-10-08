# - When creating forlders structure now, versions and versionless folders will be created. Hyerarchy processes will also be created.
# - Added "Show folder" to processes, and snapshots, to quick access to folders.
# - QSettings from maya dock removed.
# - When exproting selected from maya, only ma/mb formats will be current scene.
# - Fixed bug in snapshot browser, doubling versionless.
# - Fixed bug when selecting snapshot with multiple files.
#
# 0.2.0.3
#
# - Added watch folder functionality
# - "Show Versionless Folder", "Show Versions Folder" added to processes.
# - Created Show watch folder in menu.
# - Watch folder editing UI
# - Fixes to Config style, and other style fixes
#
# 0.2.0.5
#
# - Save confirmation replaced with the file queue
# - Show folder now works everywhere
#
# 0.3.0.14
#
# - Added confirm when adding same item to commit queue
# - Added confirm when deleting watch folder
# - Refresh after commit queue added
# - Delete, and single commits in commit queue
# - When refreshed separated versions tree now updated too
# - Preview no displays after restart
# - Fixes to commit queue
# - Partially fixes refreshing

import sys
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore


class TabBarPlus(QtGui.QTabBar):
    """Tab bar that has a plus button floating to the right of the tabs."""

    plusClicked = QtCore.Signal()

    def __init__(self):
        super(self.__class__, self).__init__()

        # Plus Button
        self.plusButton = QtGui.QPushButton("+")
        self.plusButton.setParent(self)
        # self.plusButton.setFixedSize(20, 20)  # Small Fixed size
        self.plusButton.setMaximumWidth(20)
        self.plusButton.clicked.connect(self.plusClicked.emit)
        self.movePlusButton() # Move to the correct location
    # end Constructor

    def sizeHint(self):
        """Return the size of the TabBar with increased width for the plus button."""
        sizeHint = QtGui.QTabBar.sizeHint(self)
        width = sizeHint.width()
        height = sizeHint.height()
        return QtCore.QSize(width+25, height)
    # end tabSizeHint

    def resizeEvent(self, event):
        """Resize the widget and make sure the plus button is in the correct location."""
        super(self.__class__, self).resizeEvent(event)

        self.movePlusButton()
    # end resizeEvent

    def tabLayoutChange(self):
        """This virtual handler is called whenever the tab layout changes.
        If anything changes make sure the plus button is in the correct location.
        """
        super(self.__class__, self).tabLayoutChange()

        self.movePlusButton()
    # end tabLayoutChange

    def movePlusButton(self):
        """Move the plus button to the correct location."""
        # Find the width of all of the tabs
        size = sum([self.tabRect(i).width() for i in range(self.count())])
        # size = 0
        # for i in range(self.count()):
        #     size += self.tabRect(i).width()

        # Set the plus button location in a visible area
        h = self.geometry().top()
        w = self.width()
        if size > w: # Show just to the left of the scroll buttons
            self.plusButton.move(w-54, h)
        else:
            self.plusButton.move(size, h)
    # end movePlusButton
# end class MyClass

class CustomTabWidget(QtGui.QTabWidget):
    """Tab Widget that that can have new tabs easily added to it."""

    def __init__(self):
        super(self.__class__, self).__init__()

        # Tab Bar
        self.tab = TabBarPlus()
        self.setTabBar(self.tab)

        # Properties
        self.setMovable(True)
        self.setTabsClosable(True)

        # Signals
        self.tab.plusClicked.connect(self.addTab)
        # self.tab.tabMoved.connect(self.moveTab)
        self.tabCloseRequested.connect(self.removeTab)
    # end Constructor
# end class CustomTabWidget

def startup():
    app = QtGui.QApplication(sys.argv)
    asd = QtGui.QDialog()
    l = QtGui.QVBoxLayout()

    asd.setLayout(l)
    tab = CustomTabWidget()
    l.addWidget(tab)
    asd.show()
    tab.addTab(QtGui.QPushButton('sad'), 'Tab1')
    tab.addTab(QtGui.QPushButton('sad'), 'Tab2')
    sys.exit(app.exec_())


if __name__ == '__main__':
    startup()
