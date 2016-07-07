# ui_checkin_out_tabs_classes.py
# Check In Tabs interface

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import lib.ui.ui_sobj_tabs as sobj_tabs
import ui_checkin_tree_classes as checkin_tree_widget
import ui_checkout_tree_classes as checkout_tree_widget
import environment as env

reload(sobj_tabs)
reload(checkin_tree_widget)
reload(checkout_tree_widget)


class Ui_checkInTabWidget(QtGui.QWidget, sobj_tabs.Ui_sObjTabs):
    def __init__(self, context_items, tabs_items,  parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env.Inst.ui_check_tabs['checkin'] = self

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.setupUi(self)
        self.ui_tree = []

        self.context_items = context_items
        self.tabs_items = tabs_items
        self.add_items_to_tabs()

        self.readSettings()

    def apply_current_view_to_all(self):
        current_tab = self.sObjTabWidget.currentWidget()
        commentsSplitter = current_tab.commentsSplitter.saveState()
        descriptionSplitter = current_tab.descriptionSplitter.saveState()
        imagesSplitter = current_tab.imagesSplitter.saveState()
        dropPlateSplitter = current_tab.dropPlateSplitter.saveState()

        for tab in self.ui_tree:
            tab.commentsSplitter.restoreState(commentsSplitter)
            tab.descriptionSplitter.restoreState(descriptionSplitter)
            tab.imagesSplitter.restoreState(imagesSplitter)
            tab.dropPlateSplitter.restoreState(dropPlateSplitter)
            tab.writeSettings()

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """

        for i, (key, val) in enumerate(self.context_items.iteritems()):
            name_index_context = (key, i, val)
            self.ui_tree.append(checkin_tree_widget.Ui_checkInTreeWidget(name_index_context, self))
            self.sObjTabWidget.addTab(self.ui_tree[i], self.tabs_items['names'][i])
            if key == 'empty/empty':
                self.sObjTabWidget.setDisabled(True)

    def tabActions(self):
        """
        Actions for the check_out tab
        """

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(env.Mode.get + '/ui_checkin')
        self.sObjTabWidget.setCurrentIndex(int(self.settings.value('sObjTabWidget', 0)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode.get + '/ui_checkin')
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


class Ui_checkOutTabWidget(QtGui.QWidget, sobj_tabs.Ui_sObjTabs):
    def __init__(self, context_items, tabs_items, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        env.Inst.ui_check_tabs['checkout'] = self

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.setupUi(self)
        self.ui_tree = []

        self.context_items = context_items
        self.tabs_items = tabs_items
        self.add_items_to_tabs()

        self.readSettings()

    def apply_current_view_to_all(self):
        current_tab = self.sObjTabWidget.currentWidget()
        commentsSplitter = current_tab.commentsSplitter.saveState()
        descriptionSplitter = current_tab.descriptionSplitter.saveState()
        imagesSplitter = current_tab.imagesSplitter.saveState()

        for tab in self.ui_tree:
            tab.commentsSplitter.restoreState(commentsSplitter)
            tab.descriptionSplitter.restoreState(descriptionSplitter)
            tab.imagesSplitter.restoreState(imagesSplitter)
            tab.writeSettings()

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """
        checkout_config = env.Conf.get_checkout()
        for i, (key, val) in enumerate(self.context_items.iteritems()):
            name_index_context = (key, i, val)
            self.ui_tree.append(checkout_tree_widget.Ui_checkOutTreeWidget(name_index_context, self))
            self.sObjTabWidget.addTab(self.ui_tree[i], self.tabs_items['names'][i])
            if key == 'empty/empty':
                self.sObjTabWidget.setDisabled(True)

    def tabActions(self):
        """
        Actions for the check_out tab
        """

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(env.Mode.get + '/ui_checkout')
        self.sObjTabWidget.setCurrentIndex(int(self.settings.value('sObjTabWidget', 0)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode.get + '/ui_checkout')
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
