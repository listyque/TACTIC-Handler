# file ui_checkout_tree_classes.py

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import environment as env
import tactic_classes as tc
import global_functions as gf
import lib.ui.ui_checkout_tree as ui_checkout_tree
import ui_item_classes as item_widget
import ui_icons_classes as icons_widget
import ui_richedit_classes as richedit_widget
import ui_menu_classes as menu_widget
import ui_maya_dialogs_classes as maya_dialogs

if env.Mode().get == 'maya':
    import maya_functions as mf

    reload(mf)

reload(ui_checkout_tree)
reload(item_widget)
reload(icons_widget)
reload(richedit_widget)
reload(menu_widget)
reload(maya_dialogs)


class Ui_checkOutTreeWidget(QtGui.QWidget, ui_checkout_tree.Ui_checkOutTree):
    def __init__(self, name_index_context=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        # self vars
        self.tab_name, self.tab_index, self.context_items = name_index_context
        self.toggle = False
        self.go_by_skey = [False, None]

        self.setupUi(self)

        # Query Threads
        self.names_query = tc.ServerThread(self)
        self.sobjects_query = tc.ServerThread(self)

        effect = QtGui.QGraphicsDropShadowEffect(self.searchLineEdit)
        effect.setOffset(2, 2)
        effect.setColor(QtGui.QColor(0, 0, 0, 96))
        effect.setBlurRadius(5)
        self.searchLineEdit.setGraphicsEffect(effect)

        self.setObjectName(self.tab_name)
        self.relates_to = 'checkout'
        env.Inst().ui_check_tree['checkout'][self.tab_name] = self
        self.add_items_to_context_combo_box()
        self.create_search_group_box()
        self.create_refresh_popup()
        self.create_progress_bar()

        self.controls_actions()

        self.ui_richedit = richedit_widget.Ui_richeditWidget(self.descriptionTextEdit)

        self.editorLayout.addWidget(self.ui_richedit)

        # self.readSettings()
        self.saverole = QtCore.Qt.UserRole
        self.expanded = []

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

    def add_items_to_results(self, query=None, refresh=False, revert=None):
        """
        Adding queried items to results tree widget
        :param query:
        :param refresh:
        :param revert:
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

    def fill_items(self):
        self.sobjects = self.sobjects_query.result
        gf.add_items_to_tree(self, self.resultsTreeWidget, item_widget, self.sobjects, self.process,
                             self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked(), snapshots=False)

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

    def create_search_group_box(self):
        self.searchOptionsGroupBox = icons_widget.Ui_searchOptionsWidget(self)
        self.searchOptionsLayout.addWidget(self.searchOptionsGroupBox)

    def searchLineDoubleClick(self, event):
        if not self.toggle:
            self.toggle = True
            self.searchOptionsGroupBox.setMinimumHeight(130)
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
        if env.Mode().get == 'standalone':
            self.findOpenedPushButton.setVisible(False)
        self.findOpenedPushButton.clicked.connect(self.find_opened_sobject)

        # Tree widget actions
        self.resultsTreeWidget.itemPressed.connect(self.load_preview)
        # self.resultsTreeWidget.itemSelectionChanged.connect(self.load_preview)
        self.resultsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsTreeWidget.customContextMenuRequested.connect(self.open_menu)
        self.saveDescriprionButton.clicked.connect(self.update_desctiption)
        self.resultsTreeWidget.itemExpanded.connect(self.fill_notes_count)

        # Threads Actions
        self.names_query.finished.connect(self.assets_names)
        self.sobjects_query.finished.connect(self.fill_items)

    def find_opened_sobject(self):
        skey = mf.get_skey_from_scene()
        env.Inst().ui_main.go_by_skey(skey, self.relates_to)

    def update_desctiption(self):
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        if nested_item and nested_item.type in ['snapshot', 'sobject']:
            # tc.update_description(nested_item.get_skey(only=True), gf.simplify_html(self.descriptionTextEdit.toHtml()))

            thread_update = tc.ServerThread(self)

            thread_update.kwargs = dict(search_key=nested_item.get_skey(only=True),
                                        description=gf.simplify_html(self.descriptionTextEdit.toHtml()))
            thread_update.routine = tc.update_description
            thread_update.start()
            nested_item.update_description(self.descriptionTextEdit.toPlainText())

    def fill_notes_count(self, widget):
        parent_widget = self.resultsTreeWidget.itemWidget(widget, 0)
        process = []
        if self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked():
            process = self.process
        else:
            for p in parent_widget.sobject.process.iterkeys():
                process.append(p)

        if parent_widget.type == 'sobject':

            gf.add_snapshots_items_to_tree(self, self.resultsTreeWidget, widget, item_widget, parent_widget, process)

            def notes_fill():
                notes_counts = notes_counts_query.result
                for i in range(widget.childCount()):
                    process_widget = self.resultsTreeWidget.itemWidget(widget.child(i), 0)

                    if process_widget.type == 'process':
                        process_widget.notesToolButton.setText('Notes ({0})'.format(notes_counts[i]))

            notes_counts_query = tc.ServerThread(self)
            notes_counts_query.kwargs = dict(sobject=parent_widget.sobject, process=process)
            notes_counts_query.routine = tc.get_notes_count
            notes_counts_query.start()

            notes_counts_query.finished.connect(notes_fill)

    def load_preview(self, position):
        # loading preview image
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        indexes = self.resultsTreeWidget.selectedIndexes()
        level = None

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

        env.Inst().ui_main.skeyLineEdit.setText(nested_item.get_skey(skey=True))
        self.descriptionTextEdit.setText(nested_item.get_description())

    def open_menu(self, position):
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        indexes = self.resultsTreeWidget.selectedIndexes()
        # if self.resultsTreeWidget.currentItem().isExpanded():
        #     print('EXPANDED')
        level = None
        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        if level > 1 and nested_item.files:
            print(level)
            self.custom_menu = QtGui.QMenu()

            open_action = QtGui.QWidgetAction(self)
            open_widget = menu_widget.Ui_menuWidget(self)
            open_widget.label.setText('Open')
            open_action.setDefaultWidget(open_widget)
            open_action.triggered.connect(self.open_file)
            open_widget.toolButton.clicked.connect(self.open_file_options)

            reference_action = QtGui.QWidgetAction(self)
            reference_widget = menu_widget.Ui_menuWidget(self)
            reference_widget.label.setText('Reference')
            reference_action.setDefaultWidget(reference_widget)
            reference_action.triggered.connect(self.reference_file)
            reference_widget.toolButton.clicked.connect(self.reference_file_options)

            import_action = QtGui.QWidgetAction(self)
            import_widget = menu_widget.Ui_menuWidget(self)
            import_widget.label.setText('Import')
            import_action.setDefaultWidget(import_widget)
            import_action.triggered.connect(self.import_file)
            import_widget.toolButton.clicked.connect(self.import_file_options)

            self.custom_menu.addAction(open_action)
            if env.Mode().get == 'maya':
                self.custom_menu.addAction(reference_action)
                self.custom_menu.addAction(import_action)
            self.custom_menu.exec_(self.resultsTreeWidget.viewport().mapToGlobal(position))

    def reference_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)

        if env.Mode().get == 'maya':
            self.reference_dialog = maya_dialogs.Ui_referenceOptionsWidget(file_path, nested_item)
            self.reference_dialog.show()

    def open_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)

        if env.Mode().get == 'maya':
            self.open_dialog = maya_dialogs.Ui_openOptionsWidget(file_path, nested_item)
            self.open_dialog.show()

    def import_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)

        if env.Mode().get == 'maya':
            self.import_dialog = maya_dialogs.Ui_importOptionsWidget(file_path, nested_item)
            self.import_dialog.show()

    def open_file(self):

        file_path, dir_path, all_process = self.get_current_item_paths()

        if env.Mode().get == 'maya':
            mf.open_scene(file_path, dir_path, all_process)
        else:
            gf.open_file_associated(file_path)

    def import_file(self):
        file_path = self.get_current_item_paths()[0]

        if env.Mode().get == 'maya':
            mf.import_scene(file_path)
        else:
            pass

    def reference_file(self):
        file_path = self.get_current_item_paths()[0]

        if env.Mode().get == 'maya':
            mf.reference_scene(file_path)
        else:
            pass

    def get_current_item_paths(self):
        nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
        file_path = None
        dir_path = None
        all_process = None

        modes = env.Mode().mods
        modes.append('main')
        for mode in modes:
            if nested_item.files.get(mode):
                main_file = nested_item.files[mode][0]
                asset_dir = env.Env().get_asset_dir()
                file_path = '{0}/{1}/{2}'.format(asset_dir, main_file['relative_dir'], main_file['file_name'])
                split_path = main_file['relative_dir'].split('/')
                dir_path = '{0}/{1}'.format(asset_dir, '{0}/{1}/{2}'.format(*split_path))
                all_process = nested_item.sobject.all_process

        return file_path, dir_path, all_process

    def prnt(self, idx):
        print('Current index: ' + str(idx))

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_checkout')
        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(env.Env().get_namespace(), env.Env().get_project(), tab_name[1])
        self.settings.beginGroup(group_path)
        self.commentsSplitter.restoreState(self.settings.value('commentsSplitter'))
        self.descriptionSplitter.restoreState(self.settings.value('descriptionSplitter'))
        self.imagesSplitter.restoreState(self.settings.value('imagesSplitter'))
        self.searchLineEdit.setText(self.settings.value('searchLineEdit_text', ''))
        self.contextComboBox.setCurrentIndex(self.settings.value('contextComboBox', 0))
        revert = self.settings.value('resultsTreeWidget_isExpanded', None), \
                 self.settings.value('resultsTreeWidget_isSelected', None)
        self.add_items_to_results(self.searchLineEdit.text(), refresh=True, revert=revert)
        self.settings.endGroup()
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_checkout')
        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(env.Env().get_namespace(), env.Env().get_project(), tab_name[1])
        self.settings.beginGroup(group_path)
        self.settings.setValue('commentsSplitter', self.commentsSplitter.saveState())
        self.settings.setValue('descriptionSplitter', self.descriptionSplitter.saveState())
        self.settings.setValue('imagesSplitter', self.imagesSplitter.saveState())
        self.settings.setValue('searchLineEdit_text', self.searchLineEdit.text())
        self.settings.setValue('contextComboBox', self.contextComboBox.currentIndex())
        self.settings.setValue('searchOptionsSplitter', self.searchOptionsSplitter.saveState())
        self.settings.setValue('searchByCodeRadioButton', self.searchOptionsGroupBox.searchCodeRadioButton.isChecked())
        self.settings.setValue('searchByNameRadioButton', self.searchOptionsGroupBox.searchNameRadioButton.isChecked())
        self.settings.setValue('searchAllProcessCheckBox',
                               self.searchOptionsGroupBox.showAllProcessCheckBox.isChecked())
        # print(gf.save(self.resultsTreeWidget))
        # if self.resultsTreeWidget.topLevelItemCount() > 0:
        self.settings.setValue('resultsTreeWidget_isSelected',
                               gf.expanded_state(self.resultsTreeWidget, is_selected=True))
        self.settings.setValue('resultsTreeWidget_isExpanded',
                               gf.expanded_state(self.resultsTreeWidget, is_expanded=True))
        print('Done ui_checkout_tree ' + self.objectName() + ' settings write')
        self.settings.endGroup()
        self.settings.endGroup()

    def showEvent(self, event):
        if self.resultsTreeWidget.topLevelItemCount() == 0:
            self.readSettings()

    def closeEvent(self, event):
        event.accept()
