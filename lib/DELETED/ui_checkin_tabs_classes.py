# ui_checkin_tabs_classes.py
# Check In Tabs interface


import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import lib.ui.ui_sobj_tabs as sobj_tabs
import ui_checkin_tree_classes as checkin_tree_widget
import tactic_classes as tc
import environment as env

reload(sobj_tabs)
reload(checkin_tree_widget)


class Ui_checkInTabWidget(QtGui.QWidget, sobj_tabs.Ui_sObjTabs):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.setupUi(self)
        self.ui_tree = []

        self.add_items_to_tabs()

        self.readSettings()

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """
        tabs_items = tc.query_tab_names()

        context_items = tc.context_query(tabs_items['codes'])

        for i, (key, val) in enumerate(context_items.iteritems()):
            name_index_context = (key, i, val)
            self.ui_tree.append(checkin_tree_widget.Ui_checkInTreeWidget(name_index_context, self))
            self.sObjTabWidget.addTab(self.ui_tree[i], tabs_items['names'][i])

    def tabActions(self):
        """
        Actions for the check_out tab
        """

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_checkin')
        self.sObjTabWidget.setCurrentIndex(self.settings.value('sObjTabWidget', 0))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_checkin')
        self.settings.setValue('sObjTabWidget', self.sObjTabWidget.currentIndex())
        print('Done ui_checkout_tab settings write')
        self.settings.endGroup()
        for tab in self.ui_tree:
            tab.writeSettings()

    def closeEvent(self, event):
        self.writeSettings()
        for tab in self.ui_tree:
            tab.close()
        event.accept()
