# file ui_checkout_tree_classes.py

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import environment as env
import tactic_classes as tc
import global_functions as gf
import lib.ui.ui_checkin_tree as ui_checkin_tree
import ui_item_classes as item_widget
import ui_icons_classes as icons_widget
import ui_richedit_classes as richedit_widget
import ui_addsobject_classes as addsobject_widget

if env.Mode().get == 'maya':
    import maya_functions as mf

reload(ui_checkin_tree)
reload(item_widget)
reload(icons_widget)
reload(richedit_widget)
reload(addsobject_widget)


class Ui_checkInTreeWidget(QtGui.QWidget, ui_checkin_tree.Ui_checkInTree):
    def __init__(self, name_index_context=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        # self vars
        self.tab_name, self.tab_index, self.context_items = name_index_context
        self.toggle = False

        self.setupUi(self)
        self.setObjectName(self.tab_name)
        env.Inst().ui_checkout_tree.setdefault(self.tab_name, self)
        self.add_items_to_context_combo_box()
        self.create_search_group_box()
        self.create_refresh_popup()

        self.controls_actions()

        self.create_richedit()
        self.add_items_to_formats_combo()

    def add_items_to_formats_combo(self):
        if env.Mode().get == 'maya':
            self.formatTypeComboBox.addItem('mayaAscii')
            self.formatTypeComboBox.addItem('mayaBinary')
        else:
            self.formatTypeComboBox.addItem('all')

    def create_richedit(self):
        self.ui_richedit = richedit_widget.Ui_richeditWidget(self.descriptionTextEdit)
        self.editorLayout.addWidget(self.ui_richedit)

    def create_refresh_popup(self):
        self.refresh_results = QtGui.QAction('Refresh results', self.refreshToolButton)
        self.refresh_results.triggered.connect(lambda: self.add_items_to_results(self.searchLineEdit.text(), True))
        self.clear_results = QtGui.QAction('Clear results', self.refreshToolButton)
        self.clear_results.triggered.connect(self.resultsTreeWidget.clear)
        self.search_options = QtGui.QAction('Toggle Search options', self.refreshToolButton)
        self.search_options.triggered.connect(lambda: self.searchLineDoubleClick(event=True))
        self.refreshToolButton.addAction(self.refresh_results)
        self.refreshToolButton.addAction(self.clear_results)
        self.refreshToolButton.addAction(self.search_options)

    def add_items_to_context_combo_box(self):
        """
        Add elements to Context ComboBox
        """
        self.contextComboBox.clear()
        self.contextComboBox.addItem('All')
        self.contextComboBox.addItems(self.context_items)
        self.contextComboBox.setCurrentIndex(0)

    def add_items_to_results(self, query=None, refresh=False, update=None):
        """
        Adding queried items to results tree widget
        :param query:
        :param refresh:
        :param update:
        :return:
        """
        if self.contextComboBox.currentIndex() == 0:
            self.process = self.context_items
        else:
            self.process = [self.context_items[self.contextComboBox.currentIndex() - 1]]

        if query:

            items_count = self.resultsTreeWidget.topLevelItemCount()
            # save current state
            selected_state = gf.expanded_state(self.resultsTreeWidget, is_selected=True)
            expanded_state = gf.expanded_state(self.resultsTreeWidget, is_expanded=True)

            # database query
            self.assets_names = tc.assets_query(query, self.tab_name, True)
            self.sobjects = tc.get_sobjects(self.process, self.assets_names)


            # clear previous results
            self.resultsTreeWidget.clear()
            # TODO maybe need to make loading items dinamically on expand http://stackoverflow.com/questions/11996756/qtreewidget-select-first-item

            gf.add_items_to_tree(self, self.resultsTreeWidget, item_widget, self.sobjects, self.process,
                                 self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked())

            if refresh:
                if items_count:
                    try:
                        gf.revert_expanded_state(self.resultsTreeWidget, expanded_state, expand=True)
                        gf.revert_expanded_state(self.resultsTreeWidget, selected_state, select=True)
                    except:
                        pass

        if update:
            # save current state
            selected_state = gf.expanded_state(self.resultsTreeWidget, is_selected=True)
            expanded_state = gf.expanded_state(self.resultsTreeWidget, is_expanded=True)

            # Take item we need to update
            self.resultsTreeWidget.takeTopLevelItem(update[0])

            sobject = {update[1]: self.sobjects[update[1]]}
            gf.add_items_to_tree(self, self.resultsTreeWidget, item_widget, sobject, self.process,
                                 self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked(), update[0])

            try:
                gf.revert_expanded_state(self.resultsTreeWidget, expanded_state, expand=True)
                gf.revert_expanded_state(self.resultsTreeWidget, selected_state, select=True)
            except:
                pass

    def load_images(self, nested_item, icon=False, playblast=False):
        if icon:
            self.icons_widget = icons_widget.Ui_iconsWidget(nested_item, True, False, self)
            self.imagesSplitter.resize(self.imagesSplitter.width() + 1,
                                       self.imagesSplitter.height())  # duct tape

            for i in range(self.iconsLayout.count()):
                self.iconsLayout.itemAt(i).widget().close()

            self.iconsLayout.addWidget(self.icons_widget)

        if playblast:
            self.playblast_widget = icons_widget.Ui_iconsWidget(nested_item, True, True, self)
            self.imagesSplitter.resize(self.imagesSplitter.width() + 1,
                                       self.imagesSplitter.height())  # duct tape

            for i in range(self.playblastLayout.count()):
                self.playblastLayout.itemAt(i).widget().close()

            self.playblastLayout.addWidget(self.playblast_widget)

    def create_search_group_box(self):
        self.searchOptionsGroupBox = icons_widget.Ui_searchOptionsWidget(self)
        self.searchOptionsLayout.addWidget(self.searchOptionsGroupBox)

    def searchLineDoubleClick(self, event):
        if not self.toggle:
            self.toggle = True
            self.searchOptionsGroupBox.setMinimumHeight(55)
        else:
            self.toggle = False
            self.searchOptionsGroupBox.setMinimumHeight(0)
            self.searchOptionsSplitter.setSizes([0, 1])

    def searchLineSingleClick(self, event):
        self.searchLineEdit.selectAll()

    def controls_actions(self):
        """
        Actions for the check tab
        """
        # Search line, and combo box with context
        self.searchLineEdit.returnPressed.connect(lambda: self.add_items_to_results(self.searchLineEdit.text()))
        self.searchLineEdit.mouseDoubleClickEvent = self.searchLineDoubleClick
        self.searchLineEdit.mousePressEvent = self.searchLineSingleClick
        self.contextComboBox.activated.connect(lambda: self.add_items_to_results(self.searchLineEdit.text()))

        # Tree widget actions
        self.resultsTreeWidget.itemPressed.connect(self.load_preview)
        self.resultsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsTreeWidget.customContextMenuRequested.connect(self.open_menu)

        # Save, Update, Add New buttons
        self.addNewtButton.clicked.connect(self.add_new_sobject)
        self.savePushButton.clicked.connect(self.save_file)

    def save_file(self):
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        search_key = nested_item.get_skey(parent=True)
        context = nested_item.get_context(True, self.contextLineEdit.text()).replace(' ', '_')

        if self.descriptionTextEdit.toPlainText() != '':
            description = gf.simplify_html(self.descriptionTextEdit.toHtml())
        else:
            description = 'No Description'

        self.descriptionTextEdit.clear()

        if env.Mode().get == 'maya':
            mf.save_scene(search_key, context, description, nested_item.sobject.all_process)

        # update current tree item to see saving results
        nested_item.sobject.update_snapshots()
        update = nested_item.row, nested_item.sobject.info['code']
        self.add_items_to_results(update=update)

    def add_new_sobject(self):
        """
        Open window for adding new sobject
        """

        self.add_sobject = addsobject_widget.Ui_addSObjectFormWidget(self)
        if self.searchLineEdit.text():
            self.add_sobject.nameLineEdit.setText(self.searchLineEdit.text())
        self.add_sobject.descriptionTextEdit.appendHtml(self.descriptionTextEdit.toPlainText())
        self.add_sobject.setWindowTitle(self.add_sobject.windowTitle() + self.tab_name)

        self.add_sobject.tab_name = self.tab_name

        self.add_sobject.show()

    def edit_existing_sobject(self):
        """
        Open window for Editing sobject
        """
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)

        self.edit_sobject = addsobject_widget.Ui_addSObjectFormWidget(self)
        self.edit_sobject.setWindowTitle('Edit info for ' + nested_item.sobject.info['name'])
        self.edit_sobject.nameLineEdit.setText(nested_item.sobject.info['name'])
        self.edit_sobject.descriptionTextEdit.appendHtml(nested_item.sobject.info['description'])
        self.edit_sobject.keywordsTextEdit.setPlainText(nested_item.sobject.info['keywords'])
        self.edit_sobject.addNewButton.setText('Save changes')
        self.edit_sobject.tab_name = self.tab_name

        self.edit_sobject.show()


    def load_preview(self, position):
        # loading preview image
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        indexes = self.resultsTreeWidget.selectedIndexes()

        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1
        if level == 0 and nested_item.sobject.process.get('icon'):
            self.load_images(nested_item, True, False)

        if level > 1 and nested_item.files.get('playblast'):
            self.load_images(nested_item, False, True)

        # enabling/disabling controls...
        if level == 0:
            self.savePushButton.setEnabled(False)
            self.updatePushButton.setEnabled(False)
            self.contextLineEdit.setEnabled(False)
        if level == 1:
            self.savePushButton.setEnabled(True)
            self.updatePushButton.setEnabled(False)
            self.contextLineEdit.setEnabled(True)
        if level > 1:
            self.savePushButton.setEnabled(True)
            self.updatePushButton.setEnabled(True)
            self.contextLineEdit.setEnabled(True)

        env.Inst().ui_main.skeyLineEdit.setText(nested_item.get_skey(skey=True))
        self.contextLineEdit.setText(nested_item.get_context())
        # self.descriptionTextEdit.setText(nested_item.get_description())

    def open_menu(self, position):
        indexes = self.resultsTreeWidget.selectedIndexes()
        level = None

        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        if level == 0:
            sobject_menu = QtGui.QMenu()
            sobject_menu.addAction('Edit Info')
            sobject_menu.addSeparator()
            sobject_menu.addAction('Delete')
            sobject_menu.actions()[0].triggered.connect(lambda: self.edit_existing_sobject())
            sobject_menu.actions()[2].triggered.connect(lambda: self.prnt(0))
            sobject_menu.exec_(self.resultsTreeWidget.viewport().mapToGlobal(position))

        if level > 1:
            snapshot_menu = QtGui.QMenu()
            snapshot_menu.addAction('Save')
            snapshot_menu.addAction('Update')
            snapshot_menu.addAction('Update Playblast')
            snapshot_menu.addSeparator()
            snapshot_menu.addAction('Delete')
            snapshot_menu.exec_(self.resultsTreeWidget.viewport().mapToGlobal(position))

    def prnt(self, idx):
        print('Current index: ' + str(idx))

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_checkin')
        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(tab_name[0], env.Env().get_project(), tab_name[1])
        self.settings.beginGroup(group_path)
        self.commentsSplitter.restoreState(self.settings.value('commentsSplitter'))
        self.descriptionSplitter.restoreState(self.settings.value('descriptionSplitter'))
        self.imagesSplitter.restoreState(self.settings.value('imagesSplitter'))
        self.searchLineEdit.setText(self.settings.value('searchLineEdit_text', ''))
        self.contextComboBox.setCurrentIndex(self.settings.value('contextComboBox', 0))
        self.add_items_to_results(self.searchLineEdit.text())
        try:
            gf.revert_expanded_state(self.resultsTreeWidget,
                                     self.settings.value('resultsTreeWidget_isExpanded', None), expand=True)
            gf.revert_expanded_state(self.resultsTreeWidget,
                                     self.settings.value('resultsTreeWidget_isSelected', None), select=True)
        except:
            pass
        self.settings.endGroup()
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_checkin')
        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(tab_name[0], env.Env().get_project(), tab_name[1])
        self.settings.beginGroup(group_path)
        self.settings.setValue('commentsSplitter', self.commentsSplitter.saveState())
        self.settings.setValue('descriptionSplitter', self.descriptionSplitter.saveState())
        self.settings.setValue('imagesSplitter', self.imagesSplitter.saveState())
        self.settings.setValue('searchLineEdit_text', self.searchLineEdit.text())
        self.settings.setValue('contextComboBox', self.contextComboBox.currentIndex())
        self.settings.setValue('searchOptionsSplitter', self.searchOptionsSplitter.saveState())
        self.settings.setValue('searchByCodeRadioButton', self.searchOptionsGroupBox.byCodeRadioButton.isChecked())
        self.settings.setValue('searchByNameRadioButton', self.searchOptionsGroupBox.byNameRadioButton.isChecked())
        self.settings.setValue('searchAllProcessCheckBox', self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked())
        if self.resultsTreeWidget.topLevelItemCount() > 0:
            self.settings.setValue('resultsTreeWidget_isSelected',
                                   gf.expanded_state(self.resultsTreeWidget, is_selected=True))
            self.settings.setValue('resultsTreeWidget_isExpanded',
                                   gf.expanded_state(self.resultsTreeWidget, is_expanded=True))
        print('Done ui_checkin_tree ' + self.objectName() + ' settings write')
        self.settings.endGroup()
        self.settings.endGroup()

    def showEvent(self, event):
        if self.resultsTreeWidget.topLevelItemCount() == 0:
            self.readSettings()

    def closeEvent(self, event):
        if self.resultsTreeWidget.topLevelItemCount() > 0:
            self.writeSettings()
        event.accept()
