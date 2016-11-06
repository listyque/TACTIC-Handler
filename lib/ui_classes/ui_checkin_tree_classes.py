# file ui_checkout_tree_classes.py

import ast
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
# import lib.environment as env
from lib.environment import env_mode, env_inst, env_server, env_tactic
from lib.configuration import cfg_controls
# import lib.configuration as cfg
import lib.tactic_classes as tc
import lib.global_functions as gf
import lib.ui.checkin.ui_checkin_tree as ui_checkin_tree
import lib.ui.checkin.ui_checkin_options as ui_checkin_options
import ui_item_classes as item_widget
import ui_icons_classes as icons_widget
import ui_richedit_classes as richedit_widget
import ui_addsobject_classes as addsobject_widget
import ui_drop_plate_classes as drop_plate_widget
import ui_search_classes as search_classes

if env_mode.get_mode() == 'maya':
    import lib.maya_functions as mf
    reload(mf)

reload(ui_checkin_tree)
reload(item_widget)
reload(icons_widget)
reload(richedit_widget)
reload(addsobject_widget)
reload(drop_plate_widget)
reload(search_classes)
reload(tc)


class Ui_checkInOptionsWidget(QtGui.QGroupBox, ui_checkin_options.Ui_checkinOptionsGroupBox):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.stype = stype
        self.project = project
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']
        self.tab_name = self.parent().objectName()
        self.parent_ui = parent

        self.create_checkin_options()
        self.controls_actions()

    def controls_actions(self):

        self.saveAsDefaultsPushButton.clicked.connect(self.apply_current_to_all_tabs)

    def apply_current_to_all_tabs(self):
        current_settings = self.get_settings_dict()
        for tab in env_inst.ui_check_tree.get(self.parent_ui.relates_to).itervalues():
            tab.checkin_options_widget.set_settings_from_dict(current_settings)

    def create_checkin_options(self):
        base_dirs = env_tactic.get_all_base_dirs()

        # Default repo states
        for key, val in base_dirs:
            if val['value'][4]:
                self.repositoryComboBox.addItem(val['value'][1])
                self.repositoryComboBox.setItemData(self.repositoryComboBox.count() - 1, val)

                # Custom repo states
                # if rep_dirs['custom_asset_dir']['enabled']:
                #     for i in rep_dirs['custom_asset_dir']['current']:
                #         if rep_dirs['custom_asset_dir']['visible'][i]:
                #             self.repositoryComboBox.addItem(rep_dirs['custom_asset_dir']['name'][i])
                #             val = [rep_dirs['custom_asset_dir']['path'][i], rep_dirs['custom_asset_dir']['name'][i],
                #                    rep_dirs['custom_asset_dir']['visible'][i]]
                #             custom_val = {'name': 'custom_asset_dir', 'value': val}
                #             self.repositoryComboBox.setItemData(self.repositoryComboBox.count() - 1, custom_val)

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'default_repo': 0,
                'createMayaDirsCheckBox': False,
                'askBeforeSaveCheckBox': True,
                'createPlayblastCheckBox': True,
                'updateVersionlessCheckBox': True,
            }

        self.repositoryComboBox.setCurrentIndex(int(settings_dict.get('default_repo')))
        self.createMayaDirsCheckBox.setChecked(bool(int(settings_dict.get('createMayaDirsCheckBox'))))
        self.askBeforeSaveCheckBox.setChecked(bool(int(settings_dict.get('askBeforeSaveCheckBox'))))
        self.createPlayblastCheckBox.setChecked(bool(int(settings_dict.get('createPlayblastCheckBox'))))
        self.updateVersionlessCheckBox.setChecked(bool(int(settings_dict.get('updateVersionlessCheckBox'))))

    def get_settings_dict(self):

        settings_dict = {
            'default_repo': int(self.repositoryComboBox.currentIndex()),
            'createMayaDirsCheckBox': int(self.createMayaDirsCheckBox.isChecked()),
            'askBeforeSaveCheckBox': int(self.askBeforeSaveCheckBox.isChecked()),
            'createPlayblastCheckBox': int(self.createPlayblastCheckBox.isChecked()),
            'updateVersionlessCheckBox': int(self.updateVersionlessCheckBox.isChecked()),
        }

        return settings_dict


class Ui_checkInTreeWidget(QtGui.QWidget, ui_checkin_tree.Ui_checkInTree):
    def __init__(self, stype, index, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/checkin_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        # self vars
        self.tab_index = index
        self.stype = stype
        self.project = project
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']
        self.tab_name = stype.info['code']
        self.process_tree_widget = None

        self.relates_to = 'checkin'
        self.go_by_skey = [False, None]

        self.checkin_config = cfg_controls.get_checkin()
        self.create_ui_checkin()
        self.readSettings()

    def create_ui_checkin(self):
        self.setupUi(self)
        self.setObjectName(self.tab_name)
        env_inst.ui_check_tree['checkin'][self.tab_name] = self
        self.setAcceptDrops(True)

        # Query Threads
        self.search_suggestions_thread = tc.ServerThread(self)

        self.create_serachline()
        self.create_save_button()
        self.create_search_options_group_box()
        self.create_search_results_group_box()
        self.create_checkin_options_group_box()
        self.create_refresh_popup()
        self.create_richedit()
        self.create_drop_plate()
        self.create_progress_bar()
        self.add_items_to_formats_combo()

        self.controls_actions()
        self.threads_actions()

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
        if env_mode.get_mode() == 'maya':
            self.formatTypeComboBox.addItem('mayaAscii')
            self.formatTypeComboBox.addItem('mayaBinary')
        else:
            self.formatTypeComboBox.addItem('all')

    def create_serachline(self):
        effect = QtGui.QGraphicsDropShadowEffect(self.searchLineEdit)
        effect.setOffset(2, 2)
        tab_color = self.stype.info['color']
        if tab_color:
            t_c = gf.hex_to_rgb(tab_color, alpha=64, tuple=True)
            effect.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
            effect.setBlurRadius(15)
        else:
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
        self.checkinTreeLayout.addWidget(self.progres_bar)

    def create_refresh_popup(self):
        self.switch_to_checkout = QtGui.QAction('Copy tab to checkout', self.refreshToolButton)
        self.switch_to_checkout.triggered.connect(self.refresh_current_results)
        self.filter_process = QtGui.QAction('Filter Process', self.refreshToolButton)
        self.filter_process.triggered.connect(self.create_process_tree_widget)
        self.refresh_results = QtGui.QAction('Refresh results', self.refreshToolButton)
        self.refresh_results.triggered.connect(self.refresh_current_results)
        self.clear_results = QtGui.QAction('Close all Search-Tabs', self.refreshToolButton)
        self.clear_results.triggered.connect(self.close_all_search_tabs)
        self.search_options = QtGui.QAction('Toggle Search options', self.refreshToolButton)
        self.search_options.triggered.connect(lambda: self.searchLineDoubleClick(event=True))

        self.refreshToolButton.addAction(self.switch_to_checkout)
        self.refreshToolButton.addAction(self.filter_process)
        self.refreshToolButton.addAction(self.refresh_results)
        self.refreshToolButton.addAction(self.clear_results)
        self.refreshToolButton.addAction(self.search_options)

    def create_process_tree_widget(self):
        self.process_tree_widget = search_classes.QPopupTreeWidget(
            parent_ui=self,
            parent=self,
            project=self.project,
            stype=self.stype
        )
        self.process_tree_widget.show()

    def get_process_ignore_list(self):
        if self.process_tree_widget:
            return self.process_tree_widget.get_ignore_list()
        else:
            self.process_tree_widget = search_classes.QPopupTreeWidget(
                parent_ui=self,
                parent=self,
                project=self.project,
                stype=self.stype
            )
            return self.process_tree_widget.get_ignore_list()

    def refresh_current_results(self):
        self.results_group_box.refresh_restults()

    def close_all_search_tabs(self):
        self.results_group_box.close_all_tabs()

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

    def checkin_context_menu(self, tool_button=True, mode=None):


        edit_info = QtGui.QAction('Edit Info', self.savePushButton)
        edit_info.triggered.connect(lambda: self.edit_existing_sobject())

        delete_sobject = QtGui.QAction('Delete', self.savePushButton)
        delete_sobject.triggered.connect(self.delete_sobject)

        save_snapshot = QtGui.QAction('Save', self.savePushButton)
        save_snapshot.triggered.connect(self.save_file)

        save_selected_snapshot = QtGui.QAction('Save selected', self.savePushButton)
        save_selected_snapshot.triggered.connect(lambda: self.prnt(0))

        save_snapshot_revision = QtGui.QAction('Save revision', self.savePushButton)
        save_snapshot_revision.triggered.connect(lambda: self.prnt(0))

        save_selected_snapshot_revision = QtGui.QAction('Save selected revision', self.savePushButton)
        save_selected_snapshot_revision.triggered.connect(lambda: self.prnt(0))

        update_snapshot = QtGui.QAction('Update', self.savePushButton)
        update_snapshot.triggered.connect(lambda: self.prnt(0))

        update_selected_snapshot = QtGui.QAction('Update selected', self.savePushButton)
        update_selected_snapshot.triggered.connect(lambda: self.prnt(0))

        update_playblast = QtGui.QAction('Update Playblast', self.savePushButton)
        update_playblast.triggered.connect(lambda: self.prnt(0))

        delete_snapshot = QtGui.QAction('Delete', self.savePushButton)
        delete_snapshot.triggered.connect(self.delete_snapshot_sobject)

        checkin_options = QtGui.QAction('Checkin Options toggle', self.savePushButton)
        checkin_options.triggered.connect(self.toggle_checkin_options_group_box)

        menu = QtGui.QMenu()

        # if not tool_button:
        if mode == 'sobject':
            menu.addAction(save_snapshot)
            menu.addAction(save_selected_snapshot)
            menu.addSeparator()
            menu.addAction(save_snapshot_revision)
            menu.addAction(save_selected_snapshot_revision)
            menu.addSeparator()
            menu.addAction(update_snapshot)
            menu.addAction(update_selected_snapshot)
            menu.addAction(update_playblast)
            menu.addSeparator()
            menu.addAction(edit_info)
            menu.addSeparator()
            menu.addAction(delete_sobject)
            menu.addSeparator()
            menu.addAction(checkin_options)

        if mode == 'snapshot':
            menu.addAction(save_snapshot)
            menu.addAction(save_selected_snapshot)
            menu.addSeparator()
            menu.addAction(save_snapshot_revision)
            menu.addAction(save_selected_snapshot_revision)
            menu.addSeparator()
            menu.addAction(update_snapshot)
            menu.addAction(update_selected_snapshot)
            menu.addAction(update_playblast)
            menu.addSeparator()
            menu.addAction(edit_info)
            menu.addSeparator()
            menu.addAction(delete_snapshot)
            menu.addSeparator()
            menu.addAction(checkin_options)

        if mode == 'process':
            menu.addAction(save_snapshot)
            menu.addAction(save_selected_snapshot)
            menu.addSeparator()
            menu.addAction(save_snapshot_revision)
            menu.addAction(save_selected_snapshot_revision)
            menu.addSeparator()
            menu.addAction(update_snapshot)
            menu.addAction(update_selected_snapshot)
            menu.addAction(update_playblast)
            menu.addSeparator()
            menu.addAction(checkin_options)

        if mode == 'child':
            menu.addAction(checkin_options)

        return menu

    def create_search_results_group_box(self):
        self.results_group_box = search_classes.Ui_resultsGroupBoxWidget(parent_ui=self, parent=self)
        self.searchOptionsSplitter.addWidget(self.results_group_box)
        # self.results_group_box.add_tab()

    def create_checkin_options_group_box(self):
        self.checkin_options_widget = Ui_checkInOptionsWidget(stype=self.stype, project=self.project, parent=self)
        self.checkinOptionsSplitter.addWidget(self.checkin_options_widget)
        # self.checkinOptionsLayout.addWidget(self.checkin_options_widget)
        self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.DownArrow)

    def toggle_checkin_options_group_box(self):
        if self.checkin_options_widget.isVisible():
            self.set_checkin_options_group_box_state(True)
        else:
            self.set_checkin_options_group_box_state(False)

    def set_checkin_options_group_box_state(self, hidden=False):
        if hidden:
            self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.UpArrow)
            self.checkin_options_widget.hide()
        else:
            self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.DownArrow)
            self.checkin_options_widget.show()

    def create_save_button(self):
        self.savePushButton.setMenu(self.checkin_context_menu())

    def create_search_options_group_box(self):
        self.searchOptionsGroupBox = search_classes.Ui_searchOptionsWidget(parent_ui=self, parent=self)
        self.searchOptionsSplitter.addWidget(self.searchOptionsGroupBox)
        # self.searchOptionsLayout.addWidget(self.searchOptionsGroupBox)

    def toggle_search_group_box(self):
        if self.searchOptionsGroupBox.isVisible():
            self.set_search_group_box_state(True)
        else:
            self.set_search_group_box_state(False)

    def set_search_group_box_state(self, hidden=False):
        if hidden:
            self.searchOptionsGroupBox.hide()
        else:
            self.searchOptionsGroupBox.show()

    def searchLineDoubleClick(self, event):
        self.toggle_search_group_box()

    def searchLineSingleClick(self, event):
        self.searchLineEdit.selectAll()

    def controls_actions(self):
        """
        Actions for the check tab
        """
        # Search line, and combo box with context
        self.searchLineEdit.returnPressed.connect(
            lambda: self.results_group_box.add_items_to_results(self.searchLineEdit.text()))
        self.searchLineEdit.returnPressed.connect(self.results_group_box.set_current_tab_text)
        self.searchLineEdit.mouseDoubleClickEvent = self.searchLineDoubleClick
        self.searchLineEdit.mousePressEvent = self.searchLineSingleClick
        self.searchLineEdit.textEdited.connect(self.search_suggestions)
        if env_mode.get_mode() == 'standalone':
            self.findOpenedPushButton.setVisible(False)
        self.findOpenedPushButton.clicked.connect(self.find_opened_sobject)

        # Save, Update, Add New buttons
        self.addNewtButton.clicked.connect(self.add_new_sobject)
        self.savePushButton.clicked.connect(self.save_file)

        self.toggleSaveOptionsToolButton.clicked.connect(self.toggle_checkin_options_group_box)

    def threads_actions(self):
        # Threads Actions
        self.search_suggestions_thread.finished.connect(lambda: self.search_suggestions(popup_suggestion=True))

    def find_opened_sobject(self):
        skey = mf.get_skey_from_scene()
        env_inst.ui_main.go_by_skey(skey, 'checkin')

    def search_suggestions(self, key=None, popup_suggestion=False):
        if key:
            if not self.search_suggestions_thread.isRunning():
                query = (key, 0)
                code = self.stype.info.get('code')
                project = self.current_project
                columns = ['name']

                self.search_suggestions_thread.kwargs = dict(
                    query=query,
                    stype=code,
                    columns=columns,
                    project=project,
                    limit=15,
                    offset=0,
                    order_bys='timestamp desc',
                )
                self.search_suggestions_thread.routine = tc.assets_query_new
                self.search_suggestions_thread.start()

        if popup_suggestion:
            results = self.search_suggestions_thread.result
            suggestions_list = []

            for item in results:
                suggestions_list.append(item.get('name'))

            completer = QtGui.QCompleter(suggestions_list, self)
            completer.setCompletionMode(QtGui.QCompleter.PopupCompletion)
            completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
            completer.setCompletionPrefix(key)

            self.searchLineEdit.setCompleter(completer)

            completer.complete()

    def refresh_current_snapshot_tree(self, item):
        self.results_group_box.update_item(item)

    def checkin_from_droplist(self, search_key, context, description):

        selected_items = self.ui_drop_plate.dropTreeWidget.selectedItems()
        if selected_items:
            update_versionless = bool(self.checkin_options_widget.updateVersionlessCheckBox.isChecked())

            repo = self.get_current_repo()

            file_types = []
            file_names = []
            file_paths = []
            exts = []
            file_sizes = []

            for item in selected_items:
                file_types.append('main')
                file_names.append(item.text(0))
                file_path = gf.form_path(item.text(2) + '/' + item.text(0))
                file_paths.append(file_path)
                exts.append(item.data(1, QtCore.Qt.UserRole))
                file_sizes.append(gf.get_st_size(file_path))

            mode = 'inplace'

            return tc.checkin_file(
                search_key=search_key,
                context=context,
                description=description,
                version=None,
                update_versionless=update_versionless,
                file_types=file_types,
                file_names=file_names,
                file_paths=file_paths,
                file_sizes=file_sizes,
                exts=exts,
                keep_file_name=False,
                repo_name=repo,
                mode=mode,
                create_icon=False
            )

    def save_file(self):
        current_widget = self.results_group_box.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()
        if current_tree_widget_item:
            self.savePushButton.setEnabled(False)
            search_key = current_tree_widget_item.get_skey(parent=True)
            context = current_tree_widget_item.get_context(True, self.contextLineEdit.text()).replace(' ', '_')

            if self.descriptionTextEdit.toPlainText() != '':
                # description = gf.simplify_html(self.descriptionTextEdit.toHtml())
                description = self.descriptionTextEdit.toPlainText()
            else:
                description = 'No Description'

            postfixes = ['']

            if env_mode.get_mode() == 'maya':
                repo = self.get_current_repo()
                scene_saved = mf.new_save_scene(
                    search_key,
                    context,
                    description,
                    repo=repo,
                    ext_type=self.formatTypeComboBox.currentText(),
                    postfixes=postfixes,
                )
                if scene_saved:
                    self.descriptionTextEdit.clear()
                    self.refresh_current_snapshot_tree(current_tree_widget_item)

            if env_mode.get_mode() == 'standalone':
                saved = self.checkin_from_droplist(
                    search_key=search_key,
                    context=context,
                    description=description
                )
                if saved:
                    self.descriptionTextEdit.clear()
                    self.refresh_current_snapshot_tree(current_tree_widget_item)
        else:
            self.savePushButton.setEnabled(False)

    def get_current_repo(self):
        current_idx = self.checkin_options_widget.repositoryComboBox.currentIndex()
        return self.checkin_options_widget.repositoryComboBox.itemData(current_idx, QtCore.Qt.UserRole)

    def add_new_sobject(self):
        """
        Open window for adding new sobject
        """
        stype_tytle = self.stype.info.get('title')
        if stype_tytle:
            title = stype_tytle.capitalize()
        else:
            title = 'Unknown'

        self.add_sobject = addsobject_widget.Ui_addTacticSobjectWidget(stype=self.stype, parent=self)
        self.add_sobject.setWindowTitle('Adding new SObject {0} ({1})'.format(title, self.tab_name))
        self.add_sobject.show()

    def delete_snapshot_sobject(self):

        current_widget = self.results_group_box.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if current_tree_widget_item:
            self.savePushButton.setEnabled(False)
            search_key = current_tree_widget_item.get_skey(only=True)

            print(search_key, 'deleting...')

            snapshot_del_confirm = tc.snapshot_delete_confirm(snapshot=current_tree_widget_item.snapshot, files=current_tree_widget_item.files)

            if snapshot_del_confirm[0]:
                if tc.delete_sobject_snapshot(
                        sobject=search_key,
                        delete_snapshot=snapshot_del_confirm[3],
                        search_keys=snapshot_del_confirm[1],
                        files_paths=snapshot_del_confirm[2]
                ):
                    self.update_snapshot_tree(current_tree_widget_item)

    def delete_sobject(self):

        current_widget = self.results_group_box.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if current_tree_widget_item:
            self.savePushButton.setEnabled(False)
            search_key = current_tree_widget_item.get_skey(parent=True)

            # tc.delete_sobject(skey=search_key)

            print(search_key, 'deleting...')

    def edit_existing_sobject(self):
        """
        Open window for Editing sobject
        """
        current_widget = self.results_group_box.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()
        self.edit_sobject = addsobject_widget.Ui_addTacticSobjectWidget(stype=self.stype, item=current_tree_widget_item, view='edit', parent=self)
        self.edit_sobject.setWindowTitle('Edit info for ' + current_tree_widget_item.sobject.info['name'])
        self.edit_sobject.show()

    # def load_preview(self, position):
    #     # loading preview image
    #     nested_item = self.resultsTreeWidget.itemWidget(self.resultsTreeWidget.currentItem(), 0)
    #     indexes = self.resultsTreeWidget.selectedIndexes()
    #
    #     if len(indexes) > 0:
    #         level = 0
    #         index = indexes[0]
    #         while index.parent().isValid():
    #             index = index.parent()
    #             level += 1
    #     if level == 0 and nested_item.sobject.process.get('icon'):
    #         self.load_images(nested_item, True, False)
    #
    #     if level > 1 and nested_item.files.get('playblast'):
    #         self.load_images(nested_item, False, True)
    #
    #     # enabling/disabling controls...
    #     if level == 0:
    #         self.savePushButton.setEnabled(False)
    #         self.contextLineEdit.setEnabled(False)
    #     if level == 1:
    #         self.savePushButton.setEnabled(True)
    #         self.contextLineEdit.setEnabled(True)
    #     if level > 1:
    #         self.savePushButton.setEnabled(True)
    #         self.contextLineEdit.setEnabled(True)
    #
    #     env_inst.ui_main.skeyLineEdit.setText(nested_item.get_skey(skey=True))
    #     print nested_item.get_context(process=True)
    #     self.contextLineEdit.setText(nested_item.get_context())
    #     # self.descriptionTextEdit.setText(nested_item.get_description())

    def open_menu(self):
        current_widget = self.results_group_box.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if current_tree_widget_item:
            menu = self.checkin_context_menu(False, mode=current_tree_widget_item.type)
            if menu:
                menu.exec_(QtGui.QCursor.pos())
    #
    # def double_click_snapshot(self, index):
    #
    #     level = 0
    #     while index.parent().isValid():
    #         index = index.parent()
    #         level += 1
    #
    #     if level > 1:
    #         if self.savePushButton.isEnabled():
    #             self.save_file()

    def set_settings_from_dict(self, settings_dict=None, apply_checkin_options=True, apply_search_options=True):

        if not settings_dict:
            settings_dict = {
                'searchLineEdit': '',
                'contextComboBox': 0,
                'checkinOptionsToggle': True,
                'searchOptionsToggle': True,
            }
        else:
            settings_dict = ast.literal_eval(settings_dict)

        self.searchLineEdit.setText(settings_dict.get('searchLineEdit'))
        self.set_checkin_options_group_box_state(bool(int(settings_dict.get('checkinOptionsToggle'))))
        self.set_search_group_box_state((bool(int(settings_dict.get('searchOptionsToggle')))))
        self.commentsSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('commentsSplitter')))
        self.descriptionSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('descriptionSplitter')))
        self.imagesSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('imagesSplitter')))
        self.dropPlateSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('dropPlateSplitter')))
        # self.results_group_box.get_current_widget().resultsSplitter.restoreState(
        #     QtCore.QByteArray.fromHex(settings_dict.get('resultsSplitter')))

        if apply_checkin_options:
            checkin_options_settings_dict = settings_dict.get('checkin_options_settings_dict')
            if checkin_options_settings_dict:
                checkin_options_settings_dict = ast.literal_eval(checkin_options_settings_dict)
            self.checkin_options_widget.set_settings_from_dict(checkin_options_settings_dict)

        if apply_search_options:
            search_options_settings_dict = settings_dict.get('search_options_settings_dict')
            if search_options_settings_dict:
                search_options_settings_dict = ast.literal_eval(search_options_settings_dict)
            self.searchOptionsGroupBox.set_settings_from_dict(search_options_settings_dict)

    def get_settings_dict(self):

        settings_dict = {
            'searchLineEdit': unicode(self.searchLineEdit.text()),
            'checkinOptionsToggle': int(self.checkin_options_widget.isHidden()),
            'searchOptionsToggle': int(self.searchOptionsGroupBox.isHidden()),
            'commentsSplitter': str(self.commentsSplitter.saveState().toHex()),
            'descriptionSplitter': str(self.descriptionSplitter.saveState().toHex()),
            'imagesSplitter': str(self.imagesSplitter.saveState().toHex()),
            'dropPlateSplitter': str(self.dropPlateSplitter.saveState().toHex()),
            'resultsSplitter': str(self.results_group_box.get_current_widget().resultsSplitter.saveState().toHex()),
            'checkin_options_settings_dict': str(self.checkin_options_widget.get_settings_dict()),
            'search_options_settings_dict': str(self.searchOptionsGroupBox.get_settings_dict()),
        }

        return settings_dict

    def readSettings(self):
        """
        Reading Settings
        """
        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(
            self.current_namespace,
            self.current_project,
            tab_name[1]
        )
        self.settings.beginGroup(group_path)

        settings_dict = self.settings.value('settings_dict', None)

        self.set_settings_from_dict(settings_dict)

        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(
            self.current_namespace,
            self.current_project,
            tab_name[1]
        )
        self.settings.beginGroup(group_path)

        settings_dict = self.get_settings_dict()

        self.settings.setValue('settings_dict', str(settings_dict))
        self.settings.endGroup()

        # additional settings write
        self.results_group_box.writeSettings()

        # def showEvent(self, event):
        #
        #     self.create_ui_checkin()
        #     self.readSettings()
