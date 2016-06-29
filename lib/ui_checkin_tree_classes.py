# file ui_checkout_tree_classes.py

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import environment as env
import tactic_classes as tc
import global_functions as gf
import lib.ui.ui_checkin_tree as ui_checkin_tree
import lib.ui.ui_checkin_options as ui_checkin_options
import ui_item_classes as item_widget
import ui_icons_classes as icons_widget
import ui_richedit_classes as richedit_widget
import ui_addsobject_classes as addsobject_widget
import ui_drop_plate_classes as drop_plate_widget

if env.Mode.get == 'maya':
    import maya_functions as mf

reload(ui_checkin_tree)
reload(item_widget)
reload(icons_widget)
reload(richedit_widget)
reload(addsobject_widget)
reload(drop_plate_widget)


class Ui_checkInOptionsWidget(QtGui.QGroupBox, ui_checkin_options.Ui_checkinOptionsGroupBox):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.setupUi(self)
        self.tab_name = self.parent().objectName()

        self.create_checkin_options()

    def create_checkin_options(self):
        rep_dirs = env.Env.rep_dirs

        # Default repo states
        for name, value in rep_dirs.iteritems():
            if name != 'custom_asset_dir' and name.find('linux'):
                if value[2]:
                    self.repositoryComboBox.addItem(value[1])
                    # print self.repositoryComboBox.count()-1
                    def_val = {'name': name, 'value': value}
                    self.repositoryComboBox.setItemData(self.repositoryComboBox.count()-1, def_val)

        # Custom repo states
        if rep_dirs['custom_asset_dir']['enabled']:
            for i in rep_dirs['custom_asset_dir']['current']:
                if rep_dirs['custom_asset_dir']['visible'][i]:
                    self.repositoryComboBox.addItem(rep_dirs['custom_asset_dir']['name'][i])
                    val = [rep_dirs['custom_asset_dir']['path'][i], rep_dirs['custom_asset_dir']['name'][i],
                           rep_dirs['custom_asset_dir']['visible'][i]]
                    custom_val = {'name': 'custom_asset_dir', 'value': val}
                    self.repositoryComboBox.setItemData(self.repositoryComboBox.count() - 1, custom_val)

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(env.Mode.get + '/ui_checkin')
        tab_name = self.tab_name.split('/')
        group_path = '{0}/{1}/{2}'.format(env.Env.get_namespace(), env.Env.get_project(), tab_name[1])
        self.settings.beginGroup(group_path)
        self.repositoryComboBox.setCurrentIndex(int(self.settings.value('default_repo', 0)))
        self.createMayaDirsCheckBox.setChecked(bool(self.settings.value('createMayaDirsCheckBox', False)))
        self.askBeforeSaveCheckBox.setChecked(bool(self.settings.value('askBeforeSaveCheckBox', True)))
        self.createPlayblastCheckBox.setChecked(bool(self.settings.value('createPlayblastCheckBox', True)))
        self.updateVersionlessCheckBox.setChecked(bool(self.settings.value('updateVersionlessCheckBox', True)))

        self.settings.endGroup()
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode.get + '/ui_checkin')
        tab_name = self.tab_name.split('/')
        group_path = '{0}/{1}/{2}'.format(env.Env.get_namespace(), env.Env.get_project(), tab_name[1])
        self.settings.beginGroup(group_path)
        self.settings.setValue('default_repo', int(self.repositoryComboBox.currentIndex()))
        self.settings.setValue('createMayaDirsCheckBox', int(self.createMayaDirsCheckBox.isChecked()))
        self.settings.setValue('askBeforeSaveCheckBox', int(self.askBeforeSaveCheckBox.isChecked()))
        self.settings.setValue('createPlayblastCheckBox', int(self.createPlayblastCheckBox.isChecked()))
        self.settings.setValue('updateVersionlessCheckBox', int(self.updateVersionlessCheckBox.isChecked()))

        print('Done ui_checkin_tree_options ' + tab_name[1] + ' settings write')
        self.settings.endGroup()
        self.settings.endGroup()

    def showEvent(self, event):
        self.readSettings()

    # def hideEvent(self, event):
    #     self.writeSettings()

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()


class Ui_checkInTreeWidget(QtGui.QWidget, ui_checkin_tree.Ui_checkInTree):
    def __init__(self, name_index_context=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')
        self.current_project = env.Env.get_project()
        self.current_namespace = env.Env.get_namespace()

        self.setAcceptDrops(True)

        # self vars
        self.tab_name, self.tab_index, self.context_items = name_index_context
        self.toggle = False
        self.go_by_skey = [False, None]

        self.setupUi(self)

        # Query Threads
        self.names_query = tc.ServerThread(self)
        self.sobjects_query = tc.ServerThread(self)

        self.setObjectName(self.tab_name)
        self.relates_to = 'checkin'
        env.Inst.ui_check_tree['checkin'][self.tab_name] = self
        self.add_items_to_context_combo_box()

        self.create_serachline()
        self.create_save_button()
        self.create_search_group_box()
        self.create_checkin_options_group_box()
        self.create_refresh_popup()
        self.create_richedit()
        self.create_drop_plate()
        self.create_progress_bar()

        self.controls_actions()

        self.add_items_to_formats_combo()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
            self.ui_drop_plate.setMinimumWidth(350)
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            self.ui_drop_plate.setMinimumWidth(0)
        else:
            event.ignore()
            self.ui_drop_plate.setMinimumWidth(0)

    def add_items_to_formats_combo(self):
        if env.Mode.get == 'maya':
            self.formatTypeComboBox.addItem('mayaAscii')
            self.formatTypeComboBox.addItem('mayaBinary')
        else:
            self.formatTypeComboBox.addItem('all')

    def create_serachline(self):
        effect = QtGui.QGraphicsDropShadowEffect(self.searchLineEdit)
        effect.setOffset(2, 2)
        effect.setColor(QtGui.QColor(0, 0, 0, 96))
        effect.setBlurRadius(5)
        self.searchLineEdit.setGraphicsEffect(effect)

    def create_drop_plate(self):
        self.ui_drop_plate = drop_plate_widget.Ui_dropPlateWidget(self)
        self.dropPlateLayout.addWidget(self.ui_drop_plate)

    def create_richedit(self):
        self.ui_richedit = richedit_widget.Ui_richeditWidget(self.descriptionTextEdit)
        self.editorLayout.addWidget(self.ui_richedit)

    def create_progress_bar(self):
        self.progres_bar = QtGui.QProgressBar()
        self.progres_bar.setMaximum(100)
        self.progres_bar.hide()
        self.resultsLayout.addWidget(self.progres_bar)

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

    def search_mode_state(self):
        if self.searchOptionsGroupBox.searchNameRadioButton.isChecked():
            return 0
        if self.searchOptionsGroupBox.searchCodeRadioButton.isChecked():
            return 1
        if self.searchOptionsGroupBox.searchParentCodeRadioButton.isChecked():
            return 2
        if self.searchOptionsGroupBox.searchDescriptionRadioButton.isChecked():
            return 3
        if self.searchOptionsGroupBox.searchKeywordsRadioButton.isChecked():
            return 4

    def add_items_to_results(self, query=None, refresh=False, revert=None, update=None):
        """
        Adding queried items to results tree widget
        :param query:
        :param refresh:
        :param update:
        :return:
        """
        query_tuple = query, self.search_mode_state()
        self.refresh = refresh
        if self.contextComboBox.currentIndex() == 0:
            self.process = self.context_items
        else:
            self.process = [self.context_items[self.contextComboBox.currentIndex() - 1]]

        if query_tuple[0]:

            # Run first thread
            if not self.names_query.isRunning():
                self.names_query.kwargs = dict(query=query_tuple, process=self.tab_name, raw=True)
                self.names_query.routine = tc.assets_query
                self.names_query.start()

            # save current state
            if revert:
                self.expanded_state, self.selected_state = revert
            else:
                self.expanded_state = gf.expanded_state(self.resultsTreeWidget, is_expanded=True)
                self.selected_state = gf.expanded_state(self.resultsTreeWidget, is_selected=True)

        if update:
            # save current state
            expanded_state = gf.expanded_state(self.resultsTreeWidget, is_expanded=True)
            selected_state = gf.expanded_state(self.resultsTreeWidget, is_selected=True)

            # Take item we need to update
            self.resultsTreeWidget.takeTopLevelItem(update[0])

            sobject = {update[1]: self.sobjects[update[1]]}
            self.root_snapshots_items_count = gf.add_items_to_tree(
                self,
                self.resultsTreeWidget,
                item_widget,
                sobject,
                self.process,
                self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked(),
                update[0],
                snapshots=False
            )

            try:
                gf.revert_expanded_state(self.resultsTreeWidget, expanded_state, expand=True)
                gf.revert_expanded_state(self.resultsTreeWidget, selected_state, select=True)
            except:
                pass

    def fill_items(self):
        self.sobjects = self.sobjects_query.result

        self.root_snapshots_items_count = gf.add_items_to_tree(
            self,
            self.resultsTreeWidget,
            item_widget,
            self.sobjects,
            self.process,
            self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked(),
            snapshots=False
        )

        if self.go_by_skey[0]:
            gf.expand_to_snapshot(self, self.resultsTreeWidget)
            self.go_by_skey[0] = False
            self.go_by_skey[1] = ''

        if self.refresh:
            try:
                gf.revert_expanded_state(self.resultsTreeWidget, self.expanded_state, expand=True)
                gf.revert_expanded_state(self.resultsTreeWidget, self.selected_state, select=True)
            except:
                pass

    def assets_names(self):
        names = self.names_query.result

        if not self.sobjects_query.isRunning():
            self.sobjects_query.kwargs = dict(process_list=self.process, sobjects_list=names)
            self.sobjects_query.routine = tc.get_sobjects
            self.sobjects_query.start()

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

    def checkin_context_menu(self, tool_button=True):
        self.save_snapshot = QtGui.QAction('Save', self.savePushButton)
        self.save_snapshot.triggered.connect(self.save_file)
        self.save_selected_snapshot = QtGui.QAction('Save selected', self.savePushButton)
        self.save_selected_snapshot.triggered.connect(lambda: self.prnt(0))
        self.save_snapshot_revision = QtGui.QAction('Save revision', self.savePushButton)
        self.save_snapshot_revision.triggered.connect(lambda: self.prnt(0))
        self.save_selected_snapshot_revision = QtGui.QAction('Save selected revision', self.savePushButton)
        self.save_selected_snapshot_revision.triggered.connect(lambda: self.prnt(0))
        self.update_snapshot = QtGui.QAction('Update', self.savePushButton)
        self.update_snapshot.triggered.connect(lambda: self.prnt(0))
        self.update_selected_snapshot = QtGui.QAction('Update selected', self.savePushButton)
        self.update_selected_snapshot.triggered.connect(lambda: self.prnt(0))
        self.update_playblast = QtGui.QAction('Update Playblast', self.savePushButton)
        self.update_playblast.triggered.connect(lambda: self.prnt(0))
        self.delete_snapshot = QtGui.QAction('Delete', self.savePushButton)
        self.delete_snapshot.triggered.connect(self.delete_snapshot_sobject)
        self.checkin_options = QtGui.QAction('Checkin Options toggle', self.savePushButton)
        self.checkin_options.triggered.connect(self.toggle_checkin_options_group_box)

        snapshot_menu = QtGui.QMenu()

        if not tool_button:
            snapshot_menu.addAction(self.save_snapshot)
        snapshot_menu.addAction(self.save_selected_snapshot)
        snapshot_menu.addSeparator()
        snapshot_menu.addAction(self.save_snapshot_revision)
        snapshot_menu.addAction(self.save_selected_snapshot_revision)
        snapshot_menu.addSeparator()
        snapshot_menu.addAction(self.update_snapshot)
        snapshot_menu.addAction(self.update_selected_snapshot)
        snapshot_menu.addAction(self.update_playblast)
        snapshot_menu.addSeparator()
        snapshot_menu.addAction(self.delete_snapshot)
        snapshot_menu.addSeparator()
        snapshot_menu.addAction(self.checkin_options)

        return snapshot_menu

    def create_checkin_options_group_box(self):
        self.checkin_options_widget = Ui_checkInOptionsWidget(self)
        self.checkinOptionsLayout.addWidget(self.checkin_options_widget)
        self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.DownArrow)

    def toggle_checkin_options_group_box(self):
        if self.checkin_options_widget.isVisible():
            self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.UpArrow)
            self.checkin_options_widget.hide()
        else:
            self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.DownArrow)
            self.checkin_options_widget.show()

    def create_save_button(self):
        self.savePushButton.setMenu(self.checkin_context_menu())

    def create_search_group_box(self):
        self.searchOptionsGroupBox = icons_widget.Ui_searchOptionsWidget(self)
        self.searchOptionsLayout.addWidget(self.searchOptionsGroupBox)

    def toggle_search_group_box(self):
        if not self.toggle:
            self.toggle = True
            self.searchOptionsGroupBox.setMinimumHeight(130)
        else:
            self.toggle = False
            self.searchOptionsGroupBox.setMinimumHeight(0)
            self.searchOptionsSplitter.setSizes([0, 1])

    def searchLineDoubleClick(self, event):
        self.toggle_search_group_box()

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
        if env.Mode.get == 'standalone':
            self.findOpenedPushButton.setVisible(False)
        self.findOpenedPushButton.clicked.connect(self.find_opened_sobject)

        # Tree widget actions
        self.resultsTreeWidget.itemPressed.connect(self.load_preview)
        self.resultsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsTreeWidget.customContextMenuRequested.connect(self.open_menu)
        self.resultsTreeWidget.doubleClicked.connect(self.double_click_snapshot)
        self.resultsTreeWidget.itemExpanded.connect(self.fill_notes_count)

        # Save, Update, Add New buttons
        self.addNewtButton.clicked.connect(self.add_new_sobject)
        self.savePushButton.clicked.connect(self.save_file)

        self.toggleSaveOptionsToolButton.clicked.connect(self.toggle_checkin_options_group_box)

        # Threads Actions
        self.names_query.finished.connect(self.assets_names)
        self.sobjects_query.finished.connect(self.fill_items)

    def find_opened_sobject(self):
        skey = mf.get_skey_from_scene()
        env.Inst.ui_main.go_by_skey(skey, 'checkin')

    def fill_notes_count(self, widget):

        parent_widget = self.resultsTreeWidget.itemWidget(widget, 0)
        process = []
        if self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked():
            process = self.process
        else:
            for p in parent_widget.sobject.process.iterkeys():
                process.append(p)

        if parent_widget.type == 'sobject':

            root_item_count = self.root_snapshots_items_count[self.resultsTreeWidget.indexOfTopLevelItem(widget)]

            gf.add_snapshots_items_to_tree(
                self,
                self.resultsTreeWidget,
                widget,
                item_widget,
                parent_widget,
                process,
                root_item_count
            )

            notes_counts = tc.get_notes_count(parent_widget.sobject, process)

            for i in range(widget.childCount() - root_item_count):
                process_widget = self.resultsTreeWidget.itemWidget(widget.child(i + root_item_count), 0)

                if process_widget.type == 'process':
                    process_widget.notesToolButton.setText('Notes ({0})'.format(notes_counts[i]))

    def update_snapshot_tree(self, item):
        # update current tree item to see saving results
        item.sobject.update_snapshots()
        update = item.row, item.sobject.info['code']

        self.add_items_to_results(update=update)

    def save_file(self):
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        if nested_item:
            self.savePushButton.setEnabled(False)
            search_key = nested_item.get_skey(parent=True)
            context = nested_item.get_context(True, self.contextLineEdit.text()).replace(' ', '_')

            if self.descriptionTextEdit.toPlainText() != '':
                description = gf.simplify_html(self.descriptionTextEdit.toHtml())
            else:
                description = 'No Description'

            if env.Mode.get == 'maya':
                version = None
                # print self.formatTypeComboBox.currentText()
                ext = self.formatTypeComboBox.currentText()

                scene_saved = mf.new_save_scene(
                    search_key,
                    context,
                    description,
                    nested_item.sobject.all_process,
                    self.get_current_repo(),
                    self.checkin_options_widget.updateVersionlessCheckBox.isChecked(),
                    version,
                    ext,
                    True,
                    False,
                )
                if scene_saved:
                    self.descriptionTextEdit.clear()
                    self.update_snapshot_tree(nested_item)

            if env.Mode.get == 'standalone':
                print(env.Mode.get)
                # self.get_current_repo()
                tc.new_checkin_snapshot(
                    search_key,
                    context,
                    is_current=True,
                    is_revision=False,
                    ext='ma',
                    description=description,
                    repo=self.get_current_repo(),
                    version=None,
                )

                self.update_snapshot_tree(nested_item)

        else:
            self.savePushButton.setEnabled(False)

    def get_current_repo(self):
        current_idx = self.checkin_options_widget.repositoryComboBox.currentIndex()
        return self.checkin_options_widget.repositoryComboBox.itemData(current_idx, QtCore.Qt.UserRole)

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

    def delete_snapshot_sobject(self):

        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        if nested_item:
            self.savePushButton.setEnabled(False)
            search_key = nested_item.get_skey(only=True)

            print(search_key, 'deleting...')

            snapshot_del_confirm = tc.snapshot_delete_confirm(snapshot=nested_item.snapshot, files=nested_item.files)

            if snapshot_del_confirm[0]:
                if tc.delete_sobject_snapshot(
                    sobject=search_key,
                    delete_snapshot=snapshot_del_confirm[3],
                    search_keys=snapshot_del_confirm[1],
                    files_paths=snapshot_del_confirm[2]
                ):
                    self.update_snapshot_tree(nested_item)

    def delete_sobject(self):

        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        if nested_item:
            self.savePushButton.setEnabled(False)
            search_key = nested_item.get_skey(parent=True)

            # tc.delete_sobject(skey=search_key)

            print(search_key, 'deleting...')

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
            self.contextLineEdit.setEnabled(False)
        if level == 1:
            self.savePushButton.setEnabled(True)
            self.contextLineEdit.setEnabled(True)
        if level > 1:
            self.savePushButton.setEnabled(True)
            self.contextLineEdit.setEnabled(True)

        env.Inst.ui_main.skeyLineEdit.setText(nested_item.get_skey(skey=True))
        print nested_item.get_context(process=True)
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
            sobject_menu.actions()[2].triggered.connect(self.delete_sobject)
            sobject_menu.exec_(self.resultsTreeWidget.viewport().mapToGlobal(position))

        if level > 1:
            snapshot_menu = self.checkin_context_menu(False)
            snapshot_menu.exec_(self.resultsTreeWidget.viewport().mapToGlobal(position))

    def double_click_snapshot(self, index):

        level = 0
        while index.parent().isValid():
            index = index.parent()
            level += 1

        if level > 1:
            if self.savePushButton.isEnabled():
                self.save_file()

    def prnt(self, idx):
        print('Current index: ' + str(idx))

    def readSettings(self, update_tree=False):
        """
        Reading Settings
        """

        self.settings.beginGroup(env.Mode.get + '/ui_checkin')
        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(env.Env.get_namespace(), env.Env.get_project(), tab_name[1])
        self.settings.beginGroup(group_path)
        # self.toggle_checkin_options_group_box(self.settings.value('checkinOptionsToggle', True))
        # self.checkin_options_widget.setVisible(self.settings.value('checkinOptionsToggle', True))

        # self.toggle = self.settings.value('searchOptionsToggle', False)

        self.commentsSplitter.restoreState(self.settings.value('commentsSplitter'))
        self.descriptionSplitter.restoreState(self.settings.value('descriptionSplitter'))
        self.imagesSplitter.restoreState(self.settings.value('imagesSplitter'))
        self.dropPlateSplitter.restoreState(self.settings.value('dropPlateSplitter'))
        self.searchLineEdit.setText(self.settings.value('searchLineEdit_text', ''))
        self.contextComboBox.setCurrentIndex(int(self.settings.value('contextComboBox', 0)))
        if update_tree:
            revert = self.settings.value('resultsTreeWidget_isExpanded', None), \
                     self.settings.value('resultsTreeWidget_isSelected', None)

            self.add_items_to_results(self.searchLineEdit.text(), refresh=True, revert=revert)
        self.settings.endGroup()
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode.get + '/ui_checkin')
        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(self.current_namespace, self.current_project, tab_name[1])
        self.settings.beginGroup(group_path)
        self.settings.setValue('checkinOptionsToggle', int(self.checkin_options_widget.isVisible()))
        self.settings.setValue('searchOptionsToggle', int(self.toggle))
        self.settings.setValue('commentsSplitter', self.commentsSplitter.saveState())
        self.settings.setValue('descriptionSplitter', self.descriptionSplitter.saveState())
        self.settings.setValue('imagesSplitter', self.imagesSplitter.saveState())
        self.settings.setValue('dropPlateSplitter', self.dropPlateSplitter.saveState())
        self.settings.setValue('searchOptionsSplitter', self.searchOptionsSplitter.saveState())
        self.settings.setValue('searchLineEdit_text', self.searchLineEdit.text())
        self.settings.setValue('contextComboBox', int(self.contextComboBox.currentIndex()))
        # if self.resultsTreeWidget.topLevelItemCount() > 0:
        self.settings.setValue('resultsTreeWidget_isSelected',
                               gf.expanded_state(self.resultsTreeWidget, is_selected=True))
        self.settings.setValue('resultsTreeWidget_isExpanded',
                               gf.expanded_state(self.resultsTreeWidget, is_expanded=True))
        print('Done ui_checkin_tree ' + self.objectName() + ' settings write')
        self.settings.endGroup()
        self.settings.endGroup()

        # additional settings write
        self.checkin_options_widget.writeSettings()
        self.searchOptionsGroupBox.writeSettings()

    def showEvent(self, event):
        if self.resultsTreeWidget.topLevelItemCount() == 0:
            self.readSettings(update_tree=True)
        else:
            self.readSettings(update_tree=False)

    def closeEvent(self, event):
        # if self.resultsTreeWidget.topLevelItemCount() > 0:
        # self.writeSettings()

        # self.checkin_options_widget.close()
        # self.searchOptionsGroupBox.close()
        event.accept()