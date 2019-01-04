# ui_checkin_out_tabs_classes.py
# Check In Tabs interface

import os
import shutil
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore
from thlib.environment import env_inst, env_tactic, cfg_controls, env_read_config, env_write_config, dl
import thlib.global_functions as gf
import thlib.tactic_classes as tc
import thlib.ui.checkin_out.ui_checkin_out_tabs as checkin_out_tabs
import ui_checkin_out_classes as checkin_out
import thlib.ui.misc.ui_watch_folders as ui_watch_folders
from thlib.ui_classes.ui_dialogs_classes import Ui_commitQueueWidget

reload(checkin_out_tabs)
reload(checkin_out)
reload(ui_watch_folders)


class Ui_projectWatchFoldersWidget(QtGui.QDialog, ui_watch_folders.Ui_ProjectWatchFolder):
    def __init__(self, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.watch_folders_dict = self.get_watch_folders_dict()
        self.watched_items = set()

        # env_inst.watch_folders[self.project.get_code()] = self

        self.setupUi(self)

        self.create_ui()

    def create_ui(self):

        self.watchFoldersTreeWidget.setStyleSheet('QTreeView::item {padding: 2px;}')
        self.setSizeGripEnabled(True)
        self.setWindowTitle('Watched Assets for Project: {0}'.format(self.project.info.get('title')))

        self.create_fs_watcher()
        self.create_watch_folders_tree_context_menu()

        self.controls_actions()
        self.readSettings()

        self.watchEnabledCheckBox.setEnabled(False)

    def create_fs_watcher(self):

        self.fs_watcher = gf.FSObserver()

        self.fs_watcher.set_created_signal(self.prnt)

    def create_watch_folders_tree_context_menu(self):
        self.watchFoldersTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.watchFoldersTreeWidget.customContextMenuRequested.connect(self.open_menu)

    def watch_items_menu(self):

        # TODO Make this work

        enable_watch = QtGui.QAction('Enable Watch', self.watchFoldersTreeWidget)
        enable_watch.setIcon(gf.get_icon('eye'))
        # enable_watch.triggered.connect(self.open_file_from_tree)

        disable_watch = QtGui.QAction('Disable Watch', self.watchFoldersTreeWidget)
        disable_watch.setIcon(gf.get_icon('eye-slash'))
        # disable_watch.triggered.connect(self.open_file_from_tree)

        edit_watch = QtGui.QAction('Edit Watch', self.watchFoldersTreeWidget)
        edit_watch.setIcon(gf.get_icon('edit'))
        # edit_watch.triggered.connect(self.open_file_from_tree)

        delete_watch = QtGui.QAction('Delete Watch', self.watchFoldersTreeWidget)
        delete_watch.setIcon(gf.get_icon('remove'))
        # edit_watch.triggered.connect(self.open_file_from_tree)

        menu = QtGui.QMenu()

        menu.addAction(enable_watch)
        menu.addAction(disable_watch)
        menu.addAction(edit_watch)
        menu.addAction(delete_watch)

        return menu

    def open_menu(self):
        item = self.watchFoldersTreeWidget.currentItem()
        if item:
            if item.data(0, QtCore.Qt.UserRole):
                menu = self.watch_items_menu()
                if menu:
                    menu.exec_(Qt4Gui.QCursor.pos())

    def add_item_to_fs_watch(self, skey, path=None, recursive=True):

        watch_dict = self.get_watch_dict_by_skey(skey)

        if not path:
            path = watch_dict['path']

        paths = []
        for repo in watch_dict['rep']:
            abs_path = env_tactic.get_base_dir(repo)['value'][0] + '/' + path
            paths.append(gf.form_path(abs_path))

        self.fs_watcher.append_watch(watch_name=skey, paths=paths, repos=watch_dict['rep'], recursive=recursive)

    def remove_item_from_fs_watch(self, skey):

        self.fs_watcher.remove_watch(watch_name=skey)

    def prnt(self, event, watch):

        self.show()

        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        QtGui.QDialog.activateWindow(self)
        self.show()
        self.hide()

        search_key = watch.watch_name

        commit_path = gf.extract_dirname(event.src_path)

        if watch.path == commit_path:
            context = 'publish'
        else:
            context = gf.form_path(commit_path, 'linux').split('/')[-1]

        description = 'From watch folder'

        skey_dict = tc.split_search_key(search_key)

        checkin_widget = env_inst.get_check_tree(
            project_code=skey_dict['project_code'],
            tab_code='checkin_out',
            wdg_code=skey_dict['pipeline_code'],

        )

        checkin_widget.do_creating_ui()

        match_template = gf.MatchTemplate(['$FILENAME.$EXT'])
        files_objects_dict = match_template.get_files_objects([event.src_path])

        stypes = self.project.get_stypes()
        current_stype = stypes.get(skey_dict['pipeline_code'])
        pipelines = current_stype.get_pipeline()
        print(skey_dict['pipeline_code'])
        current_pipeline = pipelines.get(skey_dict['pipeline_code'])
        print(current_pipeline)
        current_process = current_pipeline.get_process(context)
        print(current_pipeline.process)
        print(current_process)

        checkin_mode = None
        if current_process:
            checkin_mode = current_process.get('checkin_mode')

        checkin_widget.checkin_file_objects(
            search_key=search_key,
            context=context,
            description=description,
            files_objects=files_objects_dict.get('file'),
            checkin_type=checkin_mode,
            keep_file_name=False
        )

    def controls_actions(self):
        pass

    def fill_watch_folders_tree_widget(self):
        self.watchFoldersTreeWidget.clear()

        if self.watch_folders_dict:

            for i, asset_skey in enumerate(self.watch_folders_dict.get('assets_skeys')):
                root_item = QtGui.QTreeWidgetItem()
                root_item.setData(0, QtCore.Qt.UserRole, asset_skey)

                root_item.setText(1, self.watch_folders_dict['assets_stypes'][i])
                root_item.setText(2, self.watch_folders_dict['assets_names'][i])
                repos_names = []

                for repo in self.watch_folders_dict['repos'][i]:
                    repos_names.append(env_tactic.get_base_dir(repo)['value'][1])

                root_item.setText(3, ', '.join(repos_names))

                # setting actual watch status
                if self.watch_folders_dict['statuses'][i]:
                    if self.check_for_item_in_watch(asset_skey):
                        root_item.setText(0, 'Watching')
                        self.start_watch_by_skey(asset_skey)
                    else:
                        root_item.setText(0, 'Waiting')
                else:
                    root_item.setText(0, 'Stopped')
                    self.stop_watch_by_skey(asset_skey)

                self.watchFoldersTreeWidget.addTopLevelItem(root_item)

            self.watchFoldersTreeWidget.resizeColumnToContents(0)
            self.watchFoldersTreeWidget.resizeColumnToContents(1)
            self.watchFoldersTreeWidget.resizeColumnToContents(2)
            self.watchFoldersTreeWidget.resizeColumnToContents(3)

        if self.watched_items:
            self.start_watching()
        else:
            self.stop_watching()

    def start_watching(self):
        if not self.fs_watcher.is_started():
            self.fs_watcher.start()

    def stop_watching(self):
        if self.fs_watcher.is_started():
            self.fs_watcher.stop()

    def stop_watch_by_skey(self, skey):
        for item in self.watched_items:
            if item.get_search_key() == skey:
                self.remove_item_from_fs_watch(skey)
                item.watchFolderToolButton.setChecked(False)

    def start_watch_by_skey(self, skey):
        for item in self.watched_items:
            if item.get_search_key() == skey:
                self.add_item_to_fs_watch(skey, item.get_watch_folder_path(), True)
                item.watchFolderToolButton.setChecked(True)

    def check_for_item_in_watch(self, skey):
        for item in self.watched_items:
            if item.get_search_key() == skey:
                if item.is_have_watch_folder():
                    return True

    def add_item_to_watch(self, sobject_item):
        # checking if watch folder exists
        watch_dict = self.get_watch_dict_by_skey(sobject_item.get_search_key())
        all_folders_exists = True
        base_dirs = env_tactic.get_all_base_dirs()

        for key, val in base_dirs:
            if val['value'][4] and val['value'][3] in watch_dict['rep']:
                    abs_path = u'{0}/{1}'.format(val['value'][0], watch_dict['path'])
                    if not os.path.exists(gf.form_path(abs_path)):
                        all_folders_exists = False
                        dl.warning('Folders structure for: {0} repo is not created.'
                                   'Watch will be ignored.'.format(val['value'][1]),
                                   group_id='watch_folders_ui')

        if all_folders_exists:
            self.watched_items.add(sobject_item)
            self.fill_watch_folders_tree_widget()

    def remove_item_from_watch(self, sobject_item):
        self.watched_items.discard(sobject_item)

    def add_aseet_to_watch(self, sobject_item):

        watch_dict = self.get_watch_dict_by_skey(sobject_item.sobject.get_search_key())
        if not watch_dict:
            self.create_repo_editor_ui(sobject_item)
        else:
            sobject_item.check_watch_folder()

    def edit_aseet_watch(self, sobject_item):
        watch_dict = self.get_watch_dict_by_skey(sobject_item.sobject.get_search_key())
        if watch_dict:
            self.create_repo_editor_ui(sobject_item, mode='edit')
        else:
            sobject_item.check_watch_folder(True)

    def delete_aseet_from_watch(self, sobject_item):
        watch_dict = self.get_watch_dict_by_skey(sobject_item.sobject.get_search_key())
        if watch_dict:
            self.delete_watch_from_watch_folders_dict(sobject_item)
        else:
            sobject_item.check_watch_folder(True)

    @gf.catch_error
    def create_watch_folders(self, repos_list, sobject_item):

        # creating base folders with paths
        for repo in repos_list:
            abs_path = env_tactic.get_base_dir(repo)['value'][0] + '/' + sobject_item.get_watch_folder_path()

            # creating folders by processes
            for process in sobject_item.get_process_list(include_hierarchy=True):
                process_abs_path = abs_path + '/' + process

                if not os.path.exists(gf.form_path(process_abs_path)):
                    os.makedirs(gf.form_path(process_abs_path))

    @gf.catch_error
    def delete_watch_folders_and_files(self, repos_list, sobject_item):

        def onerror(func, path, exc_info):
            """
            Error handler for ``shutil.rmtree``.

            If the error is due to an access error (read only file)
            it attempts to add write permission and then retries.

            If the error is for another reason it re-raises the error.

            Usage : ``shutil.rmtree(path, onerror=onerror)``
            """
            import stat
            if not os.access(path, os.W_OK):
                # Is the error an access error ?
                os.chmod(path, stat.S_IWUSR)
                func(path)
            # else:
                # raise

        for repo in repos_list:
            abs_path = env_tactic.get_base_dir(repo)['value'][0] + '/' + sobject_item.get_watch_folder_path()

            if os.path.exists(gf.form_path(abs_path)):
                shutil.rmtree(gf.form_path(abs_path), ignore_errors=True, onerror=onerror)

    def add_watch_to_watch_folders_dict(self, repos_list, sobject_item):

        self.watch_folders_dict['assets_names'].append(sobject_item.get_title())
        self.watch_folders_dict['assets_codes'].append(sobject_item.sobject.info.get('code'))
        self.watch_folders_dict['assets_stypes'].append(sobject_item.stype.get_pretty_name())
        self.watch_folders_dict['assets_skeys'].append(sobject_item.sobject.get_search_key())
        self.watch_folders_dict['paths'].append(sobject_item.get_watch_folder_path())
        self.watch_folders_dict['repos'].append(repos_list)
        self.watch_folders_dict['statuses'].append(True)

        self.create_watch_folders(repos_list, sobject_item)

        sobject_item.check_watch_folder()

        self.writeSettings()

    def save_watch_to_watch_folders_dict(self, repos_list, sobject_item):

        watch_dict = self.get_watch_dict_by_skey(sobject_item.sobject.get_search_key())
        if watch_dict:
            idx = watch_dict['idx']

            self.watch_folders_dict['assets_names'][idx] = sobject_item.get_title()
            self.watch_folders_dict['assets_codes'][idx] = sobject_item.sobject.info.get('code')
            self.watch_folders_dict['assets_stypes'][idx] = sobject_item.stype.get_pretty_name()
            self.watch_folders_dict['assets_skeys'][idx] = sobject_item.sobject.get_search_key()
            self.watch_folders_dict['paths'][idx] = sobject_item.get_watch_folder_path()
            self.watch_folders_dict['repos'][idx] = repos_list

            self.create_watch_folders(repos_list, sobject_item)

            sobject_item.check_watch_folder()
            self.writeSettings()

    def edit_watch_to_watch_folders_dict(self, sobject_item, asset_name=None, asset_code=None,asset_stype=None,
                                         asset_skey=None, path=None, repo=None, status=False):

        watch_dict = self.get_watch_dict_by_skey(sobject_item.sobject.get_search_key())
        if watch_dict:
            idx = watch_dict['idx']

            if asset_name:
                self.watch_folders_dict['assets_names'][idx] = sobject_item.get_title()
            if asset_code:
                self.watch_folders_dict['assets_codes'][idx] = sobject_item.sobject.info.get('code')
            if asset_stype:
                self.watch_folders_dict['assets_stypes'][idx] = sobject_item.stype.get_pretty_name()
            if asset_skey:
                self.watch_folders_dict['assets_skeys'][idx] = sobject_item.sobject.get_search_key()
            if path:
                self.watch_folders_dict['paths'][idx] = path
            if repo:
                self.watch_folders_dict['repos'][idx] = repo

            self.watch_folders_dict['statuses'][idx] = status

            sobject_item.check_watch_folder()
            self.fill_watch_folders_tree_widget()
            self.writeSettings()

    def delete_watch_from_watch_folders_dict(self, sobject_item):

        buttons = (('Remove', QtGui.QMessageBox.YesRole), ('Keep', QtGui.QMessageBox.ActionRole), ('Cancel', QtGui.QMessageBox.NoRole))

        reply = gf.show_message_predefined(
            'Remove Watch Folder dirs from repos?',
            'Watch Folder Directories and Files can also be removed from Your Repositories'
            '<br>Remove or Keep this Dirs and Files?</br>',
            buttons=buttons,
            message_type='question'
        )

        delete_files = False
        delete_watch_folder = False

        if reply == QtGui.QMessageBox.YesRole:
            delete_files = True
            delete_watch_folder = True
        elif reply == QtGui.QMessageBox.ActionRole:
            delete_files = False
            delete_watch_folder = True

        if delete_watch_folder:

            self.stop_watch_by_skey(sobject_item.sobject.get_search_key())

            idx = self.get_watch_dict_by_skey(sobject_item.sobject.get_search_key())['idx']

            self.watch_folders_dict['assets_names'].pop(idx)
            self.watch_folders_dict['assets_codes'].pop(idx)
            self.watch_folders_dict['assets_stypes'].pop(idx)
            self.watch_folders_dict['assets_skeys'].pop(idx)
            self.watch_folders_dict['paths'].pop(idx)
            repos = self.watch_folders_dict['repos'].pop(idx)
            self.watch_folders_dict['statuses'].pop(idx)

            sobject_item.check_watch_folder(True)
            self.writeSettings()
            if delete_files:
                self.delete_watch_folders_and_files(repos, sobject_item)

    def create_repo_editor_ui(self, sobject_item, mode='create'):

        add_watch_ui = Ui_repositoryEditorWidget(sobject_item=sobject_item, mode=mode, parent=self)
        add_watch_ui.saved_signal.connect(self.add_watch_to_watch_folders_dict)
        add_watch_ui.edited_signal.connect(self.save_watch_to_watch_folders_dict)
        add_watch_ui.exec_()

    def set_watch_folders_from_dict(self, watch_folders_dict=None):

        if watch_folders_dict:
            print('FILLING WATCH FOLDER')

    def get_watch_dict_by_skey(self, skey):

        if self.watch_folders_dict:
            for i, asset_skey in enumerate(self.watch_folders_dict.get('assets_skeys')):
                if skey == asset_skey:
                    return {
                        'asset_code': self.watch_folders_dict['assets_codes'][i],
                        'asset_name': self.watch_folders_dict['assets_names'][i],
                        'asset_stype': self.watch_folders_dict['assets_stypes'][i],
                        'asset_skey': self.watch_folders_dict['assets_skeys'][i],
                        'path': self.watch_folders_dict['paths'][i],
                        'rep': self.watch_folders_dict['repos'][i],
                        'status': self.watch_folders_dict['statuses'][i],
                        'idx': i,
                    }

    def get_watch_folders_dict(self):
        return {
            'assets_codes': [],
            'assets_names': [],
            'assets_stypes': [],
            'assets_skeys': [],
            'paths': [],
            'repos': [],
            'statuses': [],
        }

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'watch_folders_dict': self.watch_folders_dict,
            }

        self.watch_folders_dict = settings_dict['watch_folders_dict']

    def get_settings_dict(self):
        settings_dict = {
            'watch_folders_dict': self.watch_folders_dict,
        }

        return settings_dict

    def readSettings(self):
        self.set_settings_from_dict(env_read_config(
            filename='ui_watch_folder',
            unique_id='ui_main/{0}/{1}'.format(self.project.get_type(), self.project.get_code()),
            long_abs_path=True))

    def writeSettings(self):

        env_write_config(
            self.get_settings_dict(),
            filename='ui_watch_folder',
            unique_id='ui_main/{0}/{1}'.format(self.project.get_type(), self.project.get_code()),
            long_abs_path=True)

    def showEvent(self, event):
        event.accept()
        self.fill_watch_folders_tree_widget()

    def closeEvent(self, event):

        self.writeSettings()
        event.accept()


class Ui_repositoryEditorWidget(QtGui.QDialog):
    saved_signal = QtCore.Signal(object, object)
    edited_signal = QtCore.Signal(object, object)

    def __init__(self, sobject_item, mode='create', parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.sobject_item = sobject_item
        self.mode = mode
        self.saved = False
        self.exclude_repo_list = self.get_exclude_repo_list()

        self.create_ui()

    def create_ui(self):
        if self.mode == 'create':
            self.setWindowTitle('Choose Repositories to Watch')
        else:
            self.setWindowTitle('Editing Watch Folders')

        self.resize(600, 420)
        self.setSizeGripEnabled(True)

        self.creat_layout()
        self.create_repo_path_line_edit()
        self.create_repo_combo_box()
        self.create_repos_tree_widget()
        self.create_buttons()

        if self.mode == 'edit':
            self.fill_repo_combo_box(self.exclude_repo_list)
            self.fill_repo_tree_widget(self.exclude_repo_list)
        else:
            self.fill_repo_combo_box()
            self.fill_repo_tree_widget()

        self.check_save_ability()

        self.controls_actions()

    def controls_actions(self):

        self.add_new_button.clicked.connect(self.add_new_repo)
        self.remove_button.clicked.connect(self.delete_selected_repo)
        self.save_button.clicked.connect(self.save_and_close)
        self.close_button.clicked.connect(self.close)

    def creat_layout(self):

        self.main_layout = QtGui.QGridLayout()
        self.main_layout.setContentsMargins(9, 9, 9, 9)
        self.main_layout.setColumnStretch(0, 1)
        self.setLayout(self.main_layout)

    def create_repos_tree_widget(self):

        self.repos_tree_widget = QtGui.QTreeWidget()
        self.repos_tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.repos_tree_widget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.repos_tree_widget.setRootIsDecorated(False)
        self.repos_tree_widget.setHeaderHidden(True)
        self.repos_tree_widget.setObjectName('repos_tree_widget')

        self.main_layout.addWidget(self.repos_tree_widget, 2, 0, 2, 1)

    def create_repo_path_line_edit(self):
        self.repo_path_line_edit_layout = QtGui.QHBoxLayout()
        self.repo_path_line_edit_layout.addWidget(QtGui.QLabel('Relative Watch Path:'))

        self.repo_path_line_edit = QtGui.QLineEdit()
        self.repo_path_line_edit_layout.addWidget(self.repo_path_line_edit)
        if self.mode == 'create':
            paths = tc.get_dirs_with_naming(self.sobject_item.get_search_key(), process_list=['watch_folder'])
            self.repo_path_line_edit.setText(paths['versionless'][0])
        elif self.mode == 'edit':
            self.repo_path_line_edit.setText(self.sobject_item.get_watch_folder_path())

        self.main_layout.addLayout(self.repo_path_line_edit_layout, 0, 0, 1, 2)

    def create_repo_combo_box(self):
        self.repo_combo_box = QtGui.QComboBox()

        self.main_layout.addWidget(self.repo_combo_box, 1, 0, 1, 1)

    def check_save_ability(self):
        if self.repos_tree_widget.topLevelItemCount() < 1:
            self.save_button.setEnabled(False)
        else:
            self.save_button.setEnabled(True)

    def get_exclude_repo_list(self):
        watch_folder_ui = env_inst.watch_folders.get(self.sobject_item.project.get_code())
        watch_dict = watch_folder_ui.get_watch_dict_by_skey(self.sobject_item.get_search_key())
        if watch_dict:
            return watch_dict['rep']
        else:
            return []

    def fill_repo_combo_box(self, exlude_list=None):

        self.repo_combo_box.clear()

        if not exlude_list:
            exlude_list = []

        base_dirs = env_tactic.get_all_base_dirs()

        # Default repo states
        for key, val in base_dirs:
            if val['value'][4] and val['value'][3] not in exlude_list:
                self.repo_combo_box.addItem(val['value'][1])
                self.repo_combo_box.setItemData(self.repo_combo_box.count() - 1, val)

        self.repo_combo_box.addItem('All Repos')

        current_repo = gf.get_value_from_config(cfg_controls.get_checkin(), 'repositoryComboBox')

        if current_repo:
            self.repo_combo_box.setCurrentIndex(current_repo)

    def fill_repo_tree_widget(self, exlude_list=None):

        self.repos_tree_widget.clear()

        if not exlude_list:
            exlude_list = []

        base_dirs = env_tactic.get_all_base_dirs()

        # Default repo states
        for key, val in base_dirs:
            if val['value'][4] and val['value'][3] in exlude_list:
                root_item = QtGui.QTreeWidgetItem()
                root_item.setText(0, val['value'][1])
                root_item.setData(0, QtCore.Qt.UserRole, val)

                self.repos_tree_widget.addTopLevelItem(root_item)

    def create_buttons(self):

        self.add_new_button = QtGui.QPushButton('Add')
        self.add_new_button.setMinimumWidth(90)
        self.remove_button = QtGui.QPushButton('Remove')
        self.remove_button.setMinimumWidth(90)
        self.save_button = QtGui.QPushButton('Save and Close')
        self.save_button.setMinimumWidth(90)
        self.close_button = QtGui.QPushButton('Cancel')
        self.close_button.setMinimumWidth(90)

        self.main_layout.addWidget(self.add_new_button, 1, 1, 1, 1)
        self.main_layout.addWidget(self.remove_button, 2, 1, 1, 1)
        self.main_layout.addWidget(self.save_button, 4, 0, 1, 1)
        self.main_layout.addWidget(self.close_button, 4, 1, 1, 1)

        spacer = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.main_layout.addItem(spacer, 3, 1, 1, 1)

    def add_new_repo(self):
        current_repo_index = self.repo_combo_box.currentIndex()

        current_repo = self.repo_combo_box.itemData(current_repo_index)
        if current_repo:
            self.repo_combo_box.removeItem(current_repo_index)

            root_item = QtGui.QTreeWidgetItem()
            root_item.setText(0, current_repo['value'][1])
            root_item.setData(0, QtCore.Qt.UserRole, current_repo)

            self.exclude_repo_list.append(current_repo['value'][3])

            self.repos_tree_widget.addTopLevelItem(root_item)
        else:
            for i in range(self.repo_combo_box.count()-1):
                current_repo = self.repo_combo_box.itemData(i)

                root_item = QtGui.QTreeWidgetItem()
                root_item.setText(0, current_repo['value'][1])
                root_item.setData(0, QtCore.Qt.UserRole, current_repo)

                self.exclude_repo_list.append(current_repo['value'][3])

                self.repos_tree_widget.addTopLevelItem(root_item)

        self.fill_repo_combo_box(self.exclude_repo_list)

        self.check_save_ability()

    def delete_selected_repo(self):
        current_repo_item = self.repos_tree_widget.currentItem()
        if current_repo_item:
            current_repo = current_repo_item.data(0, QtCore.Qt.UserRole)
            self.exclude_repo_list.remove(current_repo['value'][3])

            self.repos_tree_widget.takeTopLevelItem(self.repos_tree_widget.currentIndex().row())
            self.fill_repo_combo_box(self.exclude_repo_list)

        self.check_save_ability()

    def set_saved(self):
        self.saved = True

    def save_and_close(self):
        self.set_saved()
        params = (self.get_repos_list(), self.sobject_item)
        self.sobject_item.set_watch_folder_path(str(self.repo_path_line_edit.text()))

        if self.mode == 'create':
            self.saved_signal.emit(*params)

        if self.mode == 'edit':
            self.edited_signal.emit(*params)

        self.close()

    def get_repos_list(self):

        repos_list = []

        for i in range(self.repos_tree_widget.topLevelItemCount()):
            top_item = self.repos_tree_widget.topLevelItem(i)
            repo_dict = top_item.data(0, QtCore.Qt.UserRole)
            repos_list.append(repo_dict['value'][3])

        return repos_list


class Ui_checkInOutTabWidget(QtGui.QWidget, checkin_out_tabs.Ui_sObjTabs):
    def __init__(self, project, layout_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.current_project = self.project.get_code()
        env_inst.set_control_tab(self.current_project, 'checkin_out', self)

        self.setupUi(self)
        # self.ui_tree = []
        self.all_search_tabs = []
        self.current_tab_idx = 0
        # self.visible_search_tabs = []
        self.main_tabs_widget = parent  # main tabs widget
        self.layout_widget = layout_widget

        self.current_namespace = self.project.info['type']
        self.stypes_items = self.project.stypes

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()

        # self.context_items = context_items
        self.is_created = False
        self.stypes_tree_visible = False
        self.tab_bar_customization()

    def create_ui(self):

        if self.stypes_items:
            self.is_created = True
            self.add_items_to_stypes_tree()
            self.readSettings()
            self.add_items_to_tabs()
            self.controls_actions()
            self.create_watch_folders_ui()
            self.create_commit_queue_ui()

    def controls_actions(self):
        self.hamburger_tab_button.clicked.connect(self.hamburger_button_click)

        self.sTypesTreeWidget.itemClicked.connect(self.stypes_tree_item_click)
        self.sTypesTreeWidget.itemChanged.connect(self.stypes_tree_item_change)

        self.sObjTabWidget.mousePressEvent = self.sobj_tab_middle_mouse_event

    def sobj_tab_middle_mouse_event(self, event):
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:
            pos = event.pos()
            # This is because hamburger button
            tab_pos = self.sObjTabWidget.tabBar().tabAt(QtCore.QPoint(pos.x() - 26, pos.y()))
            if tab_pos != -1:
                widget = self.sObjTabWidget.widget(tab_pos)
                tab = self.get_stype_tab_by_widget(widget)
                self.toggle_stype_tab(tab=tab, hide=True)
                tree_item = self.get_tree_item_by_code(tab.stype.get_code())
                if tree_item:
                    tree_item.setCheckState(0, QtCore.Qt.Unchecked)

        event.accept()

    def stypes_tree_item_click(self, item):
        item_data = item.data(0, QtCore.Qt.UserRole)
        if item_data:
            self.raise_stype_tab(code=item_data.get('code'))

    def stypes_tree_item_change(self, item):
        if item.childCount() > 0:
            for i in range(item.childCount()):
                if item.checkState(0) == QtCore.Qt.CheckState.Unchecked:
                    item.child(i).setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.child(i).setCheckState(0, QtCore.Qt.Checked)
                self.toggle_tree_item(item.child(i))
        else:
            self.toggle_tree_item(item)

    def toggle_tree_item(self, item):
        item_data = item.data(0, QtCore.Qt.UserRole)
        if item_data:
            if item.checkState(0):
                self.toggle_stype_tab(code=item_data.get('code'), hide=False)
            else:
                self.toggle_stype_tab(code=item_data.get('code'), hide=True)

        # saving changes to config
        self.save_ignore_stypes_list()

    def get_stype_tab_by_widget(self, widget):
        for tab in self.all_search_tabs:
            if tab.tab_widget == widget:
                return tab

    def get_stype_tab_by_code(self, code):
        for tab in self.all_search_tabs:
            if tab.get_tab_code() == code:
                return tab

    def get_tree_item_by_code(self, code):

        for i in range(self.sTypesTreeWidget.topLevelItemCount()):
            top = self.sTypesTreeWidget.topLevelItem(i)
            for j in range(top.childCount()):
                child = top.child(j)
                item_data = child.data(0, QtCore.Qt.UserRole)
                if item_data:
                    if item_data.get('code') == code:
                        return child

    def raise_stype_tab(self, code=None, tab=None):
        if code:
            tab = self.get_stype_tab_by_code(code)
        if tab:
            idx = self.sObjTabWidget.indexOf(tab.tab_widget)
            self.sObjTabWidget.setCurrentIndex(idx)

    def toggle_stype_tab(self, code=None, tab=None, hide=False):

        if code:
            tab = self.get_stype_tab_by_code(code)
        if tab:
            idx = self.sObjTabWidget.indexOf(tab.tab_widget)
            if hide:
                self.sObjTabWidget.removeTab(idx)
                self.set_ignore_stypes_list(code, hide=True)
            else:
                self.sObjTabWidget.addTab(tab.tab_widget, '')

                self.set_ignore_stypes_list(code, hide=False)
                self.sObjTabWidget.tabBar().setTabButton(self.sObjTabWidget.count()-1, QtGui.QTabBar.LeftSide, tab.get_tab_label())

    def raise_tab(self):
        self.main_tabs_widget.raise_tab(self.layout_widget)

    def apply_current_view_to_all(self):
        current_settings = None
        current_tab = self.get_current_tab_widget()
        if current_tab:
            current_settings = current_tab.get_settings_dict()

        if current_settings:
            for tab in self.all_search_tabs:
                tab.set_settings_from_dict(current_settings, apply_checkin_options=False, apply_search_options=False)

    def fast_save(self, **kargs):
        current_tab = self.get_current_tab_widget()

        current_tab.fast_save(**kargs)

    def get_current_tab_widget(self):
        current_widget = self.sObjTabWidget.currentWidget()
        for tab in self.all_search_tabs:
            if current_widget == tab.tab_widget:
                return tab

    def tab_bar_customization(self):
        self.hamburger_tab_button = QtGui.QToolButton()
        self.hamburger_tab_button.setAutoRaise(True)
        self.hamburger_tab_button.setMinimumWidth(20)
        self.hamburger_tab_button.setMinimumHeight(20)
        self.animation_close = QtCore.QPropertyAnimation(self.sTypesTreeWidget, "maximumWidth", self)
        self.animation_open = QtCore.QPropertyAnimation(self.sTypesTreeWidget, "maximumWidth", self)
        self.hamburger_tab_button.setIcon(gf.get_icon('navicon'))

        self.sObjTabWidget.setCornerWidget(self.hamburger_tab_button, QtCore.Qt.BottomLeftCorner)

    def hamburger_button_click(self):
        content_width = self.sTypesTreeWidget.sizeHintForColumn(0) + 40
        if self.stypes_tree_visible:
            self.animation_close.setDuration(100)
            self.animation_close.setStartValue(content_width)
            self.animation_close.setEndValue(0)
            self.animation_close.start()
            self.stypes_tree_visible = False
        else:
            self.animation_open.setDuration(150)
            self.animation_open.setStartValue(0)
            self.animation_open.setEndValue(content_width)
            self.animation_open.start()

            self.stypes_tree_visible = True

    def add_items_to_stypes_tree(self):
        exclude_list = self.get_ignore_stypes_list()
        self.sTypesTreeWidget.clear()

        all_stypes = []

        for stype in env_inst.projects[self.current_project].stypes.itervalues():
            all_stypes.append(stype.info)

        grouped = gf.group_dict_by(all_stypes, 'type')

        for type_name, value in grouped.iteritems():
            top_item = QtGui.QTreeWidgetItem()

            if not type_name:
                type_name = 'Category'
            top_item.setText(0, type_name.capitalize())
            top_item.setCheckState(0, QtCore.Qt.Checked)
            self.sTypesTreeWidget.addTopLevelItem(top_item)
            for item in value:
                child_item = QtGui.QTreeWidgetItem()

                stype = env_inst.projects[self.current_project].stypes.get(item.get('code'))

                item_code = stype.get_code()
                child_item.setText(0, stype.get_pretty_name())
                child_item.setText(1, item_code)
                child_item.setData(0, QtCore.Qt.UserRole, item)
                child_item.setCheckState(0, QtCore.Qt.Checked)
                if exclude_list:
                    if item_code in exclude_list:
                        child_item.setCheckState(0, QtCore.Qt.Unchecked)
                top_item.addChild(child_item)

            top_item.setExpanded(True)

    def get_ignore_stypes_list(self):
        ignore_tabs_list = []
        if self.checkin_out_config and self.checkin_out_config_projects and self.checkin_out_config_projects.get(self.current_project):
            if not gf.get_value_from_config(self.checkin_out_config, 'processTabsFilterGroupBox'):
                ignore_tabs_list = []
            else:
                ignore_tabs_list = self.checkin_out_config_projects[self.current_project]['stypes_list']
                if not ignore_tabs_list:
                    ignore_tabs_list = []

        return ignore_tabs_list

    def set_ignore_stypes_list(self, stype_code, hide=False):

        self.init_stypes_config()

        # TODO this code will reset all previous projects states
        if not self.checkin_out_config_projects.get(self.current_project):
            self.init_stypes_config(True)

        if self.checkin_out_config_projects:
            if not self.checkin_out_config_projects[self.current_project]['stypes_list']:
                stypes_list = []
            else:
                stypes_list = self.checkin_out_config_projects[self.current_project]['stypes_list']

            if hide:
                if stype_code not in stypes_list:
                    stypes_list.append(stype_code)
            else:
                if stype_code in stypes_list:
                    stypes_list.remove(stype_code)

            self.checkin_out_config_projects[self.current_project]['stypes_list'] = stypes_list

    def init_stypes_config(self, force=False):
        if not self.checkin_out_config_projects or force:
            from thlib.ui_classes.ui_conf_classes import Ui_checkinOutPageWidget
            self.checkinOutPageWidget = Ui_checkinOutPageWidget(self)

            self.checkinOutPageWidget.processTabsFilterGroupBox.setChecked(True)
            self.checkinOutPageWidget.init_per_projects_config_dict()

            self.checkinOutPageWidget.collect_defaults(apply_values=True)
            self.checkinOutPageWidget.save_config()

            self.checkin_out_config_projects = self.checkinOutPageWidget.page_init_projects

    def save_ignore_stypes_list(self):
        self.init_stypes_config()

        if self.checkin_out_config_projects:
            cfg_controls.set_checkin_out_projects(self.checkin_out_config_projects)

    def add_items_to_tabs(self):
        """
        Adding process tabs marked for Maya
        """
        self.sObjTabWidget.setHidden(True)

        ignore_tabs_list = self.get_ignore_stypes_list()

        for i, stype in enumerate(self.stypes_items.itervalues()):

            tab_widget = QtGui.QWidget(self)
            tab_widget_layout = QtGui.QVBoxLayout()
            tab_widget_layout.setContentsMargins(0, 0, 0, 0)
            tab_widget_layout.setSpacing(0)
            tab_widget.setLayout(tab_widget_layout)
            tab_widget.setObjectName(stype.get_pretty_name())

            self.all_search_tabs.append(checkin_out.Ui_checkInOutWidget(stype, tab_widget, self.project, self))

        # Add tabs
        added_labels = []
        for i, tab in enumerate(self.all_search_tabs):
            if tab.stype.get_code() not in ignore_tabs_list:
                added_labels.append(tab.get_tab_label())
                self.sObjTabWidget.addTab(tab.tab_widget, '')

        self.sObjTabWidget.setCurrentIndex(self.current_tab_idx)

        self.sObjTabWidget.setStyleSheet(
            '#sObjTabWidget > QTabBar::tab {background: transparent;border: 2px solid transparent;'
            'border-top-left-radius: 3px;border-top-right-radius: 3px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;padding: 0px;}'
            '#sObjTabWidget > QTabBar::tab:selected, #sObjTabWidget > QTabBar::tab:hover {'
            'background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(255, 255, 255, 48), stop: 1 rgba(255, 255, 255, 32));}'
            '#sObjTabWidget > QTabBar::tab:selected {border-color: transparent;}'
            '#sObjTabWidget > QTabBar::tab:!selected {margin-top: 0px;}')

        for i, tab in enumerate(self.all_search_tabs):
            tab.tab_widget.layout().addWidget(tab)

        if gf.get_value_from_config(cfg_controls.get_checkin_out(), 'lastViewOnAllTabscheckBox'):
            # Every tab will read the widget seetings when creating ui
            current_tab = self.get_current_tab_widget()
            if current_tab:
                current_settings = current_tab.get_settings_dict(force=True)
                for tab in self.all_search_tabs:
                    tab.set_settings_from_dict(current_settings, apply_checkin_options=False, apply_search_options=False)

        # Add labels
        for i, label in enumerate(added_labels):
            self.sObjTabWidget.tabBar().setTabButton(i, QtGui.QTabBar.LeftSide, label)

        self.sObjTabWidget.setHidden(False)

    def create_watch_folders_ui(self):
        env_inst.watch_folders[self.project.get_code()] = Ui_projectWatchFoldersWidget(
            parent=self,
            project=self.project)

    def create_commit_queue_ui(self):
        env_inst.commit_queue[self.project.get_code()] = Ui_commitQueueWidget(
            parent=self,
            project=self.project)

    def set_settings_from_dict(self, settings_dict):
        if not settings_dict:
            settings_dict = {
                'stypes_tree_visible': 0,
                'sObjTabWidget_currentIndex': 0
            }

        if bool(int(settings_dict['stypes_tree_visible'])):
            self.hamburger_button_click()
        self.current_tab_idx = int(settings_dict['sObjTabWidget_currentIndex'])

    def get_settings_dict(self):
        settings_dict = {
            'stypes_tree_visible': int(self.stypes_tree_visible),
            'sObjTabWidget_currentIndex': int(self.sObjTabWidget.currentIndex()),
        }

        return settings_dict

    def readSettings(self):
        """
        Reading Settings
        """

        group_path = 'ui_main/{0}/{1}'.format(
                self.current_namespace,
                self.current_project
            )

        self.set_settings_from_dict(
            env_read_config(
                filename='ui_checkin_out_tabs',
                unique_id=group_path,
                long_abs_path=True
            )
        )

    def writeSettings(self):
        """
        Writing Settings
        """
        group_path = 'ui_main/{0}/{1}'.format(
            self.current_namespace,
            self.current_project,
        )

        env_write_config(
            self.get_settings_dict(),
            filename='ui_checkin_out_tabs',
            unique_id=group_path,
            long_abs_path=True
        )

    def showEvent(self, event):
        if not self.is_created:
            self.create_ui()
        event.accept()

    def closeEvent(self, event):
        self.writeSettings()
        for tab in self.all_search_tabs:
            tab.close()
        event.accept()
