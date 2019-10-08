import os
import shutil
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore
from thlib.environment import env_inst, env_tactic, cfg_controls, env_read_config, env_write_config, dl
import thlib.global_functions as gf
import thlib.tactic_classes as tc
from thlib.ui.misc.ui_watch_folders import Ui_ProjectWatchFolder


class Ui_projectWatchFoldersWidget(QtGui.QDialog, Ui_ProjectWatchFolder):
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

        self.fs_watcher.set_created_signal(self.handle_watch_created_event)

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

        self.fs_watcher.append_watch(watch_name=skey, paths=paths, repos=watch_dict['rep'], pipeline=watch_dict['asset_pipeline'], recursive=recursive)

    def remove_item_from_fs_watch(self, skey):

        self.fs_watcher.remove_watch(watch_name=skey)

    def handle_watch_created_event(self, event, watch):
        dl.log('File dropped to watch folder {}'.format(event.src_path), group_id='watch_folder')

        self.show()

        self.setWindowState(self.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
        QtGui.QDialog.activateWindow(self)
        self.show()
        self.hide()

        search_key = watch.watch_name
        pipeline = watch.pipeline

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

        checkin_mode = None
        if pipelines:

            # here we do pipelines routine
            current_pipeline = pipelines.get(pipeline)
            if not current_pipeline:
                # looks like we don't have pipeline with Search Type name, so we take first of all
                # Also this is totally wrong, cause we should know exactly the pipeline and its processes, so need to write proper pipeline_code when creating watch folder
                current_pipeline = pipelines.values()[0]

            current_process = current_pipeline.get_process(context)

            if current_process:
                checkin_mode = current_process.get('checkin_mode')
            else:
                context = 'publish'

            checkin_widget.checkin_file_objects(
                search_key=search_key,
                context=context,
                description=description,
                files_objects=files_objects_dict.get('file'),
                checkin_type=checkin_mode,
                keep_file_name=False
            )
        else:
            # here we go with publish, without pipeline
            checkin_widget.checkin_file_objects(
                search_key=search_key,
                context='publish',
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
                        dl.warning('Folders structure for: {0} is not created. '
                                   'Watch will be ignored.'.format(abs_path),
                                   group_id='watch_folders_ui')

        if all_folders_exists:
            self.watched_items.add(sobject_item)
            self.fill_watch_folders_tree_widget()

    def remove_item_from_watch(self, sobject_item):
        self.watched_items.discard(sobject_item)

    def add_asset_to_watch(self, sobject_item):

        # in case of some bugs double checking
        if not self.get_watch_dict_by_skey(sobject_item.sobject.get_search_key()):
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

            # creating folder for publish
            if not os.path.exists(gf.form_path(abs_path)):
                os.makedirs(gf.form_path(abs_path))

            # creating folders by processes
            if sobject_item.get_process_list(include_hierarchy=True):
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
        self.watch_folders_dict['assets_pipelines'].append(sobject_item.sobject.get_pipeline_code())
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
            self.watch_folders_dict['assets_pipelines'][idx] = sobject_item.sobject.get_pipeline_code()
            self.watch_folders_dict['paths'][idx] = sobject_item.get_watch_folder_path()
            self.watch_folders_dict['repos'][idx] = repos_list

            self.create_watch_folders(repos_list, sobject_item)

            sobject_item.check_watch_folder()
            self.writeSettings()

    def edit_watch_to_watch_folders_dict(self, sobject_item, asset_name=None, asset_code=None,asset_stype=None,
                                         asset_skey=None, asset_pipeline=None, path=None, repo=None, status=False):

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
            if asset_pipeline:
                self.watch_folders_dict['assets_pipelines'][idx] = sobject_item.sobject.get_pipeline_code()
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
            self.watch_folders_dict['assets_pipelines'].pop(idx)
            self.watch_folders_dict['paths'].pop(idx)
            repos = self.watch_folders_dict['repos'].pop(idx)
            self.watch_folders_dict['statuses'].pop(idx)

            sobject_item.check_watch_folder(True)
            self.writeSettings()
            if delete_files:
                self.delete_watch_folders_and_files(repos, sobject_item)

    def create_repo_editor_ui(self, sobject_item, mode='create'):
        add_watch_ui = Ui_repositoryEditorWidget(sobject_item=sobject_item, mode=mode, parent=env_inst.ui_main)
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
                        'asset_pipeline': self.watch_folders_dict['assets_pipelines'][i],
                        'path': self.watch_folders_dict['paths'][i],
                        'rep': self.watch_folders_dict['repos'][i],
                        'status': self.watch_folders_dict['statuses'][i],
                        'idx': i,
                    }

    @staticmethod
    def get_watch_folders_dict():
        return {
            'assets_codes': [],
            'assets_names': [],
            'assets_stypes': [],
            'assets_skeys': [],
            'assets_pipelines': [],
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
