# file ui_checkout_tree_classes.py

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
from lib.environment import env_mode, env_inst, env_server, env_tactic
from lib.configuration import cfg_controls
import lib.global_functions as gf
import lib.tactic_classes as tc
import lib.ui.checkout.ui_checkout_tree as ui_checkout_tree
import lib.ui_classes.ui_misc_classes as ui_misc_classes
import ui_item_classes as item_widget
import ui_maya_dialogs_classes as maya_dialogs
import ui_menu_classes as menu_widget
import ui_richedit_classes as richedit_widget
import ui_search_classes as search_classes
import lib.ui_classes.ui_snapshot_browser_classes as snapshot_browser_widget


if env_mode.get_mode() == 'maya':
    import lib.maya_functions as mf

    reload(mf)

reload(ui_checkout_tree)
reload(item_widget)
reload(richedit_widget)
reload(menu_widget)
reload(maya_dialogs)
reload(gf)
reload(search_classes)
reload(snapshot_browser_widget)


class Ui_checkOutTreeWidget(QtGui.QWidget, ui_checkout_tree.Ui_checkOutTree):
    def __init__(self, stype, index, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/checkout_ui_config.ini'.format(
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

        self.relates_to = 'checkout'
        self.go_by_skey = [False, None]

        self.checkut_config = cfg_controls.get_checkout()

        self.is_created = False

        self.setupUi(self)
        self.setObjectName(self.tab_name)
        env_inst.set_check_tree(self.current_project, 'checkout', self.tab_name, self)
        self.customize_ui()

    def do_creating_ui(self):
        if not self.is_created:
            self.create_ui_checkout()

    def create_ui_checkout(self):
        self.is_created = True

        # Query Threads
        self.update_desctiption_thread = tc.ServerThread(self)
        self.search_suggestions_thread = tc.ServerThread(self)

        self.create_searchline()
        self.create_search_options_group_box()
        self.create_search_results_group_box()
        self.create_refresh_popup()
        # self.create_separate_versions_tree()
        self.create_snapshot_browser()

        self.controls_actions()
        self.threads_actions()

        self.create_ui_richedit()

        self.readSettings()

        # self.saverole = QtCore.Qt.UserRole
        # self.expanded = []

    def create_searchline(self):
        effect = QtGui.QGraphicsDropShadowEffect(self.searchLineEdit)
        effect.setOffset(2, 2)

        tab_color = self.stype.info['color']
        if tab_color:
            t_c = gf.hex_to_rgb(tab_color, alpha=128, tuple=True)
            effect.setColor(Qt4Gui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
            effect.setBlurRadius(15)
        else:
            effect.setColor(Qt4Gui.QColor(0, 0, 0, 128))
            effect.setBlurRadius(15)
        self.searchLineEdit.setGraphicsEffect(effect)

    def create_ui_richedit(self):
        self.ui_richedit = richedit_widget.Ui_richeditWidget(self.descriptionTextEdit)
        self.editorLayout.addWidget(self.ui_richedit)

    def create_snapshot_browser(self):
        self.snapshot_browser_widget = snapshot_browser_widget.Ui_snapshotBrowserWidget(self)
        self.snapshotBrowserLayout.addWidget(self.snapshot_browser_widget)

    def get_snapshot_browser(self):
        return self.snapshot_browser_widget

    def create_refresh_popup(self):
        self.refreshToolButton.setIcon(gf.get_icon('cog'))
        self.refreshToolButton.setMinimumSize(22, 22)

        self.switch_to_checkin = QtGui.QAction('Copy tab to checkin', self.refreshToolButton)
        self.switch_to_checkin.triggered.connect(self.refresh_results)
        self.filter_process = QtGui.QAction('Filter Process', self.refreshToolButton)
        self.filter_process.triggered.connect(self.create_process_tree_widget)
        self.refresh_results = QtGui.QAction('Refresh results', self.refreshToolButton)
        self.refresh_results.triggered.connect(self.refresh_results)
        self.clear_results = QtGui.QAction('Close all Search-Tabs', self.refreshToolButton)
        self.clear_results.triggered.connect(self.close_all_search_tabs)
        self.search_options = QtGui.QAction('Toggle Search options', self.refreshToolButton)
        self.search_options.triggered.connect(lambda: self.searchLineDoubleClick(event=True))

        self.refreshToolButton.addAction(self.switch_to_checkin)
        self.refreshToolButton.addAction(self.filter_process)
        self.refreshToolButton.addAction(self.refresh_results)
        self.refreshToolButton.addAction(self.clear_results)
        self.refreshToolButton.addAction(self.search_options)

        # self.custom_action = CustomAction('ZOOM', self.refreshToolButton)
        # self.refreshToolButton.setMenu(self.custom_action)
        # self.custom_action.addAction(QtGui.QAction('AZZA', self.refreshToolButton))

    def create_process_tree_widget(self):
        if not self.process_tree_widget:
            self.process_tree_widget = search_classes.QPopupTreeWidget(
                parent_ui=self,
                parent=self,
                project=self.project,
                stype=self.stype
            )
            self.process_tree_widget.show()
        else:
            self.process_tree_widget.show()

    def get_process_ignore_list(self):
        if self.process_tree_widget:
            return self.process_tree_widget.get_ignore_dict()
        else:
            self.process_tree_widget = search_classes.QPopupTreeWidget(
                parent_ui=self,
                parent=self,
                project=self.project,
                stype=self.stype
            )
            return self.process_tree_widget.get_ignore_dict()

    def get_current_tree_widget(self):
        return self.search_results_widget.get_current_widget()

    def get_is_separate_versions(self):
        current_tabbed_widget = self.search_results_widget.get_current_widget()
        return current_tabbed_widget.get_is_separate_versions()

    def refresh_results(self):
        self.search_results_widget.refresh_results()

    def close_all_search_tabs(self):
        self.search_results_widget.close_all_tabs()

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

    def get_search_process_list(self):

        return self.searchOptionsGroupBox.get_custom_process_list()

    def create_search_results_group_box(self):
        self.search_results_widget = search_classes.Ui_resultsGroupBoxWidget(parent_ui=self, parent=self)
        self.searchOptionsSplitter.addWidget(self.search_results_widget)

    def create_search_options_group_box(self):
        self.searchOptionsGroupBox = search_classes.Ui_searchOptionsWidget(parent_ui=self, parent=self)
        self.searchOptionsSplitter.addWidget(self.searchOptionsGroupBox)

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
        self.searchLineEdit.returnPressed.connect(self.do_search)
        # self.searchLineEdit.mouseDoubleClickEvent = self.searchLineDoubleClick
        self.searchLineEdit.mousePressEvent = self.searchLineSingleClick
        self.searchLineEdit.textEdited.connect(self.search_suggestions)
        # if env_mode.get_mode() == 'standalone':
        #     self.findOpenedPushButton.setVisible(False)

        # self.findOpenedPushButton.clicked.connect(self.find_opened_sobject)
        self.saveDescriprionButton.clicked.connect(lambda: self.update_desctiption(run_thread=True))

    def customize_ui(self):
        # if env_mode.get_mode() == 'standalone':
        # self.findOpenedPushButton.setVisible(False)
        # self.addNewtButton.setIcon(gf.get_icon('plus-square-o'))
        self.create_collapsable_toolbar()

    def create_collapsable_toolbar(self):
        self.collap = ui_misc_classes.Ui_horizontalCollapsableWidget()

        self.buttons_layout = QtGui.QHBoxLayout()
        self.buttons_layout.setSpacing(0)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.filter_process_button = QtGui.QToolButton()
        self.filter_process_button.setMaximumSize(22, 22)
        self.filter_process_button.setAutoRaise(True)
        self.filter_process_button.setIcon(gf.get_icon('filter'))
        self.filter_process_button.clicked.connect(self.create_process_tree_widget)

        self.toggle_search_options_button = QtGui.QToolButton()
        self.toggle_search_options_button.setMaximumSize(22, 22)
        self.toggle_search_options_button.setAutoRaise(True)
        self.toggle_search_options_button.setIcon(gf.get_icon('sliders'))
        self.toggle_search_options_button.clicked.connect(self.toggle_search_group_box)

        self.find_opened_sobject_button = QtGui.QToolButton()
        self.find_opened_sobject_button.setMaximumSize(22, 22)
        self.find_opened_sobject_button.setAutoRaise(True)
        self.find_opened_sobject_button.setIcon(gf.get_icon('bolt'))
        self.find_opened_sobject_button.clicked.connect(self.find_opened_sobject)

        self.buttons_layout.addWidget(self.filter_process_button)
        self.buttons_layout.addWidget(self.toggle_search_options_button)
        if env_mode.get_mode() == 'maya':
            self.buttons_layout.addWidget(self.find_opened_sobject_button)

        self.collap.setLayout(self.buttons_layout)
        self.collap.setCollapsed(True)

        self.expandingLayout.addWidget(self.collap)

    def threads_actions(self):
        # Threads Actions
        self.update_desctiption_thread.finished.connect(lambda: self.update_desctiption(update_description=True))
        self.search_suggestions_thread.finished.connect(lambda: self.search_suggestions(popup_suggestion=True))

    def get_search_query_text(self):
        return self.searchLineEdit.text()

    def get_search_options_widget(self):
        return self.searchOptionsGroupBox

    def do_search(self, search_query=None, search_by=None, new_tab=False):
        self.search_results_widget.do_search(
            search_query=search_query,
            search_by=search_by,
            new_tab=new_tab
        )

    def find_opened_sobject(self):
        skey = mf.get_skey_from_scene()
        env_inst.ui_main.go_by_skey(skey, self.relates_to)

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

    def update_desctiption(self, run_thread=False, update_description=False):
        current_widget = self.search_results_widget.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if run_thread:
            if current_tree_widget_item and current_tree_widget_item.type in ['snapshot', 'sobject']:
                self.update_desctiption_thread.kwargs = dict(
                    search_key=current_tree_widget_item.get_skey(only=True),
                    description=gf.simplify_html(self.descriptionTextEdit.toHtml())
                )
                self.update_desctiption_thread.routine = tc.update_description
                self.update_desctiption_thread.start()

        if update_description:
            update = tc.treat_result(self.update_desctiption_thread)
            if update.isFailed():
                if update.result == QtGui.QMessageBox.ApplyRole:
                    update.run()
                    self.update_desctiption(update_description=True)
                elif update.result == QtGui.QMessageBox.ActionRole:
                    env_inst.offline = True
                    env_inst.ui_main.open_config_dialog()

            if not update.isFailed():
                current_tree_widget_item.update_description(self.descriptionTextEdit.toPlainText())

    def open_menu(self):
        current_widget = self.search_results_widget.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if current_tree_widget_item and current_tree_widget_item.type == 'snapshot' and current_tree_widget_item.files:
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
            if env_mode.get_mode() == 'maya':
                self.custom_menu.addAction(reference_action)
                self.custom_menu.addAction(import_action)
            if env_mode.get_mode() == 'standalone':
                open_widget.toolButton.setDisabled(True)

            self.custom_menu.exec_(Qt4Gui.QCursor.pos())

    def double_click_snapshot(self):
        if self.checkut_config:
            double_click = bool(int(
                gf.get_value_from_config(self.checkut_config, 'doubleClickOpenCheckBox', 'QCheckBox')
            ))
        else:
            double_click = False
        if double_click:
            current_widget = self.search_results_widget.get_current_widget()
            current_tree_widget_item = current_widget.get_current_tree_widget_item()
            if current_tree_widget_item.type == 'snapshot' and current_tree_widget_item.files:
                self.open_file()

    def reference_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.current_tree_item_widget

        if env_mode.get_mode() == 'maya':
            self.reference_dialog = maya_dialogs.Ui_referenceOptionsWidget(file_path, nested_item)
            self.reference_dialog.show()

    def open_file_options(self):
        file_path = self.get_current_item_paths()[0]
        current_widget = self.search_results_widget.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if env_mode.get_mode() == 'maya':
            self.open_dialog = maya_dialogs.Ui_openOptionsWidget(file_path, current_tree_widget_item)
            self.open_dialog.show()

    def import_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.current_tree_item_widget

        if env_mode.get_mode() == 'maya':
            self.import_dialog = maya_dialogs.Ui_importOptionsWidget(file_path, nested_item)
            self.import_dialog.show()

    def open_file(self):

        file_path, dir_path, all_process = self.get_current_item_paths()

        if env_mode.get_mode() == 'maya':
            mf.open_scene(file_path, dir_path, all_process)
        else:
            gf.open_file_associated(file_path)

    def import_file(self):
        file_path = self.get_current_item_paths()[0]

        if env_mode.get_mode() == 'maya':
            mf.import_scene(file_path)
        else:
            pass

    def reference_file(self):
        file_path = self.get_current_item_paths()[0]

        if env_mode.get_mode() == 'maya':
            mf.reference_scene(file_path)
        else:
            pass

    def get_current_item_paths(self):
        # TODO REWRITE THIS THING with multiple file in one snapshot in mind

        current_widget = self.search_results_widget.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()
        file_path = None
        dir_path = None
        all_process = None

        modes = env_mode.modes
        modes.append('main')
        for mode in modes:
            if current_tree_widget_item.files.get(mode):
                main_file = current_tree_widget_item.files[mode][0]
                repo_name = current_tree_widget_item.snapshot.get('repo')
                if repo_name:
                    asset_dir = env_tactic.get_base_dir(repo_name)['value'][0]
                else:
                    asset_dir = env_tactic.get_base_dir('client')['value'][0]
                file_path = gf.form_path(
                    '{0}/{1}/{2}'.format(asset_dir, main_file['relative_dir'], main_file['file_name']))

                # print file_path
                split_path = main_file['relative_dir'].split('/')
                dir_path = gf.form_path('{0}/{1}'.format(asset_dir, '{0}/{1}/{2}'.format(*split_path)))
                all_process = current_tree_widget_item.sobject.all_process

        return file_path, dir_path, all_process

    def set_settings_from_dict(self, settings_dict=None, apply_search_options=True):
        self.do_creating_ui()

        if not settings_dict:
            settings_dict = {
                'searchLineEdit': '',
                'contextComboBox': 0,
                'searchOptionsToggle': True,
            }
        else:
            settings_dict = ast.literal_eval(settings_dict)

        self.searchLineEdit.setText(settings_dict.get('searchLineEdit'))
        self.set_search_group_box_state((bool(int(settings_dict.get('searchOptionsToggle')))))
        self.commentsSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('commentsSplitter')))
        self.descriptionSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('descriptionSplitter')))
        # self.imagesSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('imagesSplitter')))
        # print self.tab_name, ': '
        self.search_results_widget.get_current_widget().resultsSplitter.restoreState(
            QtCore.QByteArray.fromHex(settings_dict.get('resultsSplitter')))

        if apply_search_options:
            search_options_settings_dict = settings_dict.get('search_options_settings_dict')
            if search_options_settings_dict:
                search_options_settings_dict = ast.literal_eval(search_options_settings_dict)
            self.searchOptionsGroupBox.set_settings_from_dict(search_options_settings_dict)

    def get_settings_dict(self):
        self.do_creating_ui()

        settings_dict = {
            'searchLineEdit': unicode(self.searchLineEdit.text()),
            'searchOptionsToggle': int(self.searchOptionsGroupBox.isHidden()),
            'commentsSplitter': str(self.commentsSplitter.saveState().toHex()),
            'descriptionSplitter': str(self.descriptionSplitter.saveState().toHex()),
            # 'imagesSplitter': str(self.imagesSplitter.saveState().toHex()),
            'resultsSplitter': str(self.search_results_widget.get_current_widget().resultsSplitter.saveState().toHex()),
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
        self.search_results_widget.writeSettings()

    def showEvent(self, event):
        self.do_creating_ui()
        event.accept()

    def closeEvent(self, event):
        event.accept()
