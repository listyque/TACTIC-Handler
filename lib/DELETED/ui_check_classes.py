# ui_check.py
# Check Out interface


import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import lib.ui.ui_check as ui_check
import lib.ui_item_versionless_classes as item_vles_widget
import lib.ui_item_versioned_classes as item_ved_widget
import lib.ui_item_process_classes as item_process_widget
import lib.ui_item_classes as item_widget
import lib.ui_icons_classes as icons_widget
import tactic_classes as tc

reload(ui_check)
reload(item_vles_widget)
reload(item_ved_widget)
reload(item_process_widget)
reload(item_widget)
reload(icons_widget)


class Ui_checkTabWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        # global vars
        # Tabs:
        self.tabs_items = {}
        self.context_items = []
        # global vars

        self.ui = ui_check.Ui_checkOut()
        self.ui.setupUi(self)

        self.add_items_to_tabs()

        self.add_items_to_context_combo_box(self.ui.checkOutTabWidget.currentIndex())

        self.tabActions()

        self.readSettings()

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """
        self.tabs_items = tc.query_tab_names()

        print(self.tabs_items['colors'])
        for tab_name in self.tabs_items['names']:
            self.ui.checkOutTabWidget.addTab(QtGui.QWidget(), tab_name)

        self.context_items = tc.context_query(self.tabs_items['codes'])

    def add_items_to_results(self, query):
        """
        Adding queried items to results tree widget
        """
        current_tab_code = self.tabs_items['codes'][self.ui.checkOutTabWidget.currentIndex()]

        if self.ui.contextComboBox.currentText() == 'All':
            process = self.context_items[self.ui.checkOutTabWidget.currentIndex()]
        else:
            process = [str(self.ui.contextComboBox.currentText())]

        if query:
            assets_names = tc.assets_query(query, current_tab_code)
            snapshots_names = tc.snapshots_query(process, assets_names['codes'])

            self.ui.resultsTreeWidget.clear()
            top_items = []
            process_child_items = []
            versionless_child_items = []
            versioned_child_items = []
            icons = []
            for item_idx, asset_name in enumerate(assets_names['names']):

                for ic in snapshots_names[assets_names['codes'][item_idx]]['icon']:
                    icons.append(ic)

                top_items.append(QtGui.QTreeWidgetItem())
                # top_items[len(top_items) - 1].setText(0, asset_name)
                main_widget_items = item_widget.Ui_itemWidget(assets_names, item_idx, icons, self)
                self.ui.resultsTreeWidget.addTopLevelItems(top_items)
                self.ui.resultsTreeWidget.setItemWidget(
                    self.ui.resultsTreeWidget.topLevelItem(item_idx), 0, main_widget_items)

            for i, asset_code in enumerate(assets_names['codes']):
                # print(assets_names)

                for j, proc in enumerate(process):
                    process_child_items.append(QtGui.QTreeWidgetItem())
                    self.ui.resultsTreeWidget.topLevelItem(i).addChildren(process_child_items)
                    self.ui.resultsTreeWidget.topLevelItem(i).child(j).setText(0, proc)
                    proc_items = item_process_widget.Ui_processItemWidget(j, self)
                    self.ui.resultsTreeWidget.setItemWidget(
                        self.ui.resultsTreeWidget.topLevelItem(i).child(j), 0, proc_items)
                    # print(proc)
                    # TODO: Check if snapshot did not have any versionless file

                    # Split versions, and versionless items
                    versionless, versioned = tc.split_snapshots_versions(process, snapshots_names, asset_code, proc)
                    # print(versionless)
                    # getting icons by items
                    # icons = tc.split_snapshots_icons(snapshots_names, asset_code)

                    # splitting by different context
                    versioned_context = []
                    for k, v_les in enumerate(versionless):
                        # print(v_les)
                        if v_les['type'] == 'main':
                            versionless_child_items.append(QtGui.QTreeWidgetItem())
                            vles_items = item_vles_widget.Ui_versionlessItemWidget(v_les, self)
                            self.ui.resultsTreeWidget.topLevelItem(i).child(j).addChildren(versionless_child_items)
                            self.ui.resultsTreeWidget.setItemWidget(
                                self.ui.resultsTreeWidget.topLevelItem(i).child(j).child(k), 0, vles_items)
                            versioned_context.append(v_les['context'])

                    for idx, cont in enumerate(versioned_context):
                        ved_cnt = []
                        for m, v_ed in enumerate(versioned):
                            if v_ed['type'] == 'main':
                                if v_ed['context'] == versioned_context[idx]:
                                    versioned_child_items.append(QtGui.QTreeWidgetItem())
                                    self.ui.resultsTreeWidget.topLevelItem(i).child(j).child(idx).addChildren(
                                        versioned_child_items)
                                    ved_cnt.append(v_ed)

                        for cnt, ved in enumerate(ved_cnt):
                            ved_items = item_ved_widget.Ui_versionedItemWidget(ved, self)
                            self.ui.resultsTreeWidget.setItemWidget(
                                self.ui.resultsTreeWidget.topLevelItem(i).child(j).child(idx).child(cnt), 0, ved_items)

    def add_items_to_context_combo_box(self, current_index=None):
        """
        Add elements to Context ComboBox
        """
        self.ui.contextComboBox.clear()
        self.ui.contextComboBox.addItem('All')
        self.ui.contextComboBox.addItems(self.context_items[current_index])

    def load_images(self, nested_item, preview=None, playblast=None):
        if preview:
            self.icons_widget = icons_widget.Ui_iconsWidget(nested_item, self)
            self.ui.imagesSplitter.resize(self.ui.imagesSplitter.width() + 1,
                                          self.ui.imagesSplitter.height())  # duct tape

            for i in range(self.ui.iconsLayout.count()):
                self.ui.iconsLayout.itemAt(i).widget().close()

            self.ui.iconsLayout.addWidget(self.icons_widget)
        else:
            self.ui.iconsLayout.removeWidget(self.icons_widget)

        if playblast:
            self.playblastImage = QtGui.QImage(0, 0, QtGui.QImage.Format_ARGB32)
            self.playblastImage.load(playblast)
            self.playblastPixmap = QtGui.QPixmap.fromImage(self.previewImage).scaled(self.ui.playblastLabel.size(),
                                                                                     QtCore.Qt.KeepAspectRatio,
                                                                                     QtCore.Qt.SmoothTransformation)
            self.ui.playblastLabel.setPixmap(self.playblastPixmap)

    def tabActions(self):
        """
        Actions for the check tab
        """
        self.ui.searchLineEdit.returnPressed.connect(lambda: self.add_items_to_results(self.ui.searchLineEdit.text()))
        self.ui.checkOutTabWidget.setStyleSheet("""
        QTabBar{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(0,0,128, 20), stop: 1 rgba(0, 0, 0, 0));
        }
        """)
        self.ui.checkOutTabWidget.currentChanged.connect(
            lambda: self.add_items_to_context_combo_box(self.ui.checkOutTabWidget.currentIndex()))
        self.ui.contextComboBox.activated.connect(lambda: self.add_items_to_results(self.ui.searchLineEdit.text()))

        self.ui.saveDescriprionButton.clicked.connect(lambda: self.load_images(
            r'D:\APS\OneDrive\Exam_(work title)\root\exam\props\Mushroom\work\icon\Mushroom_mushroom_web_icon.jpg',
            r'D:\APS\OneDrive\Exam_(work title)\root\exam\props\Mushroom\work\icon\Mushroom_mushroom_web_icon.jpg'))

        # print(len(indexes))
        # if len(indexes) == 0:
        self.ui.resultsTreeWidget.clicked.connect(self.load_preview)

        self.ui.resultsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.resultsTreeWidget.customContextMenuRequested.connect(self.open_menu)

    def load_preview(self, position):
        nested_item = self.ui.resultsTreeWidget.itemWidget(self.ui.resultsTreeWidget.currentItem(), 0)
        indexes = self.ui.resultsTreeWidget.selectedIndexes()
        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        if level == 0:
            try:
                self.load_images(nested_item, 'as')
            except:
                pass

        try:
            self.ui.descriptionTextEdit.setText(nested_item.item_info['description'])
        except:
            self.ui.descriptionTextEdit.setText('No Description')

    def open_menu(self, position):
        indexes = self.ui.resultsTreeWidget.selectedIndexes()

        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        if level > 1:
            print(level)
            self.custom_menu = QtGui.QMenu()
            self.custom_menu.addAction(self.ui.resultsTreeWidget.tr('Open'))
            self.custom_menu.addAction(self.ui.resultsTreeWidget.tr('Reference'))
            self.custom_menu.addAction(self.ui.resultsTreeWidget.tr('Import'))
            self.custom_menu.exec_(self.ui.resultsTreeWidget.viewport().mapToGlobal(position))

    def prnt(self, idx):
        print('Current index: ' + str(idx))

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup('ui_check')
        self.ui.commentsSplitter.restoreState(self.settings.value('commentsSplitter'))
        self.ui.descriptionSplitter.restoreState(self.settings.value('descriptionSplitter'))
        self.ui.imagesSplitter.restoreState(self.settings.value('imagesSplitter'))
        self.ui.checkOutTabWidget.setCurrentIndex(self.settings.value('checkOutTabWidget', 0))
        self.ui.searchLineEdit.setText(self.settings.value('searchLineEdit_text', ''))
        self.ui.contextComboBox.setCurrentIndex(self.settings.value('contextComboBox', 0))
        self.add_items_to_results(self.ui.searchLineEdit.text())
        try:
            self.revert_expanded_state(self.ui.resultsTreeWidget,
                                       self.settings.value('resultsTreeWidget_isExpanded', None), expand=True)
            self.revert_expanded_state(self.ui.resultsTreeWidget,
                                       self.settings.value('resultsTreeWidget_isSelected', None), select=True)
        except:
            pass
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup('ui_check')
        self.settings.setValue('commentsSplitter', self.ui.commentsSplitter.saveState())
        self.settings.setValue('descriptionSplitter', self.ui.descriptionSplitter.saveState())
        self.settings.setValue('imagesSplitter', self.ui.imagesSplitter.saveState())
        self.settings.setValue('checkOutTabWidget', self.ui.checkOutTabWidget.currentIndex())
        self.settings.setValue('searchLineEdit_text', self.ui.searchLineEdit.text())
        self.settings.setValue('contextComboBox', self.ui.contextComboBox.currentIndex())
        self.settings.setValue('resultsTreeWidget_isSelected',
                               self.expanded_state(self.ui.resultsTreeWidget, is_selected=True))
        self.settings.setValue('resultsTreeWidget_isExpanded',
                               self.expanded_state(self.ui.resultsTreeWidget, is_expanded=True))
        print('Done ui_check settings write')
        self.settings.endGroup()

    @staticmethod
    def revert_expanded_state(tree, state, select=False, expand=False):
        """
        Self explanatory
        :param tree: treeWidget
        :param state: dict of true or false
        """
        lv = tree.topLevelItemCount()

        for i in range(lv):
            t = tree.topLevelItem(i).childCount()
            if state['lv'][lv + i][0]:
                if expand:
                    tree.expandItem(tree.topLevelItem(i))
                if select:
                    tree.setItemSelected(tree.topLevelItem(i), 1)

            for j in range(t):
                l = tree.topLevelItem(i).child(j).childCount()
                if state['lv'][i]['t'][t + j]:
                    if expand:
                        tree.expandItem(tree.topLevelItem(i).child(j))
                    if select:
                        tree.setItemSelected(tree.topLevelItem(i).child(j), 1)

                for k in range(l):
                    if state['lv'][i]['t'][j]['l'][0]:
                        if expand:
                            tree.expandItem(tree.topLevelItem(i).child(j).child(k))
                        if select:
                            tree.setItemSelected(tree.topLevelItem(i).child(j).child(k), 1)

    @staticmethod
    def expanded_state(tree, is_expanded=False, is_selected=False):
        """
        Saving full tree of Tree Widget
        :param tree: treeWidget
        :return: dict of true/false
        """
        lv = tree.topLevelItemCount()

        results = dict(
            lv=[
                {
                    't': [
                        {'l': []} for j in range(tree.topLevelItem(i).childCount())]
                }
                for i in range(tree.topLevelItemCount())
                ],
        )

        for i in range(lv):
            if is_expanded:
                results['lv'].append([tree.isItemExpanded(tree.topLevelItem(i))])
            if is_selected:
                results['lv'].append([tree.isItemSelected(tree.topLevelItem(i))])

            t = tree.topLevelItem(i).childCount()
            for j in range(t):
                if is_expanded:
                    results['lv'][i]['t'].append(tree.isItemExpanded(tree.topLevelItem(i).child(j)))
                if is_selected:
                    results['lv'][i]['t'].append(tree.isItemSelected(tree.topLevelItem(i).child(j)))

                l = tree.topLevelItem(i).child(j).childCount()
                for k in range(l):
                    if is_expanded:
                        results['lv'][i]['t'][j]['l'].append(
                            tree.isItemExpanded(tree.topLevelItem(i).child(j).child(k)))
                    if is_selected:
                        results['lv'][i]['t'][j]['l'].append(
                            tree.isItemSelected(tree.topLevelItem(i).child(j).child(k)))

        return results

    def closeEvent(self, event):
        # event.ignore()
        self.writeSettings()
        event.accept()
