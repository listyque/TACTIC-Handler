from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore
from thlib.environment import env_inst, env_mode, env_tactic, env_api, cfg_controls, dl
import thlib.global_functions as gf
import thlib.tactic_classes as tc
from thlib.ui_classes.ui_custom_qwidgets import Ui_previewsEditorDialog, Ui_screenShotMakerDialog, Ui_collapsableWidget
from thlib.ui.checkin_out.ui_commit_queue import Ui_commitQueue


class commitWidget(QtGui.QWidget):
    def __init__(self, args_dict, commit_queue_ui=None, multiple_edit_mode=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.args_dict = args_dict

        self.commit_queue_ui = commit_queue_ui
        self.multiple_edit_mode = multiple_edit_mode

        self.item_widget = self.args_dict['item_widget']
        self.commit_item = None
        self.commit_items_list = None
        self.repo = self.args_dict['repo_name']
        self.context = self.args_dict['context']
        self.update_versionless = self.args_dict['update_versionless']
        self.only_versionless = False
        self.description = self.args_dict['description']
        self.virtual_snapshot = None
        self.shown = False
        self.single_commit = False
        self.single_threaded = False
        self.links_to_upload_list = set()
        self.screenshots_to_upload_list = []

        self.virtual_snapshot_worker = None
        # self.snapshot_checkin_worker = None
        self.inplace_checkin_worker = None
        self.upload_checkin_worker = None

    def create_ui(self):
        self.shown = True
        self.create_main_layout()
        self.create_info_label_widget()
        self.create_label_widget()
        self.create_checkboxes_widget()
        self.create_versionless_widget()
        self.create_versions_widget()
        self.create_description_widget()
        self.create_edits_widgets()

        self.main_layout.setRowStretch(8, 1)

        self.switch_versionless_checkbox()
        self.switch_only_versionless_checkbox()
        if self.multiple_edit_mode:
            self.collapse_wdg_vls.setEnabled(False)
            self.collapse_wdg_vers.setEnabled(False)
            self.collapse_wdg_descr.setEnabled(False)
            self.explicit_file_name_edit.setEnabled(False)
            self.explicit_file_name_label.setEnabled(False)
            self.context_as_file_name_checkbox.setEnabled(False)
            self.previews_widget.setEnabled(False)
            self.description_widget.setEnabled(False)
        else:
            self.refresh_virtual_snapshot()

        self.controls_actions()

    def set_commit_items_list(self, commit_items_list):
        self.commit_items_list = commit_items_list

    def edit_previews(self):
        files_objects = self.get_upload_list_files_objects()
        screenshots = self.get_screenshots_to_upload_list()
        if files_objects or screenshots:
            self.edit_previews_dialog = Ui_previewsEditorDialog(
                files_objects=files_objects,
                screenshots=screenshots,
                parent=self)

            self.edit_previews_dialog.exec_()

    def clear_all(self):

        self.links_to_upload_list = set()
        self.screenshots_to_upload_list = []

        self.drop_plate_label.setText(
            'Drop Images Here ({0})'.format(len(self.get_upload_list()) + len(self.screenshots_to_upload_list)))

    @gf.catch_error
    def browse_for_preview(self):
        options = QtGui.QFileDialog.Options()
        options |= QtGui.QFileDialog.DontUseNativeDialog
        file_name, filter = QtGui.QFileDialog.getOpenFileName(self, 'Browse for Preview Image',
                                                              '',
                                                              'All Images (*.jpg | *.jpeg | *.png | *.tif);;'
                                                              'JPEG Images (*.jpg | *.jpeg);;'
                                                              'PNG Images (*.png);;'
                                                              'TIF Images (*.tif)',
                                                              '', options)
        if file_name:
            ext = gf.extract_extension(file_name)
            if ext[3] == 'preview':
                self.add_links_to_upload_list([file_name])

    def make_screenshot(self):
        screen_shot_maker_dialog = Ui_screenShotMakerDialog()

        # Hiding all app windows before making screenshot
        if env_mode.get_mode() == 'standalone':
            env_inst.ui_main.setHidden(True)
        elif env_mode.get_mode() == 'maya':
            env_inst.ui_maya_dock.setHidden(True)
        for val in env_inst.commit_queue.values():
            val.setHidden(True)

        screen_shot_maker_dialog.exec_()

        if env_mode.get_mode() == 'standalone':
            env_inst.ui_main.setHidden(False)
        elif env_mode.get_mode() == 'maya':
            env_inst.ui_maya_dock.setHidden(False)
        for val in env_inst.commit_queue.values():
            val.setHidden(False)

        self.screenshots_to_upload_list.append(screen_shot_maker_dialog.screenshot_pixmap)

        self.drop_plate_label.setText(
            'Drop Images Here ({0})'.format(len(self.get_upload_list()) + len(self.screenshots_to_upload_list)))

        return screen_shot_maker_dialog.screenshot_pixmap

    def set_preview_to_commit_item(self, tp='screenshot'):
        if tp == 'screenshot':
            self.commit_item.set_preview(self.make_screenshot())

    def update_args_dict(self):

        # updating args_dict
        self.args_dict['explicit_filename'] = u'{0}'.format(self.explicit_file_name_edit.text().strip().replace(' ', '_'))
        self.args_dict['description'] = u'{0}'.format(self.description_widget.get_description('plain'))
        self.args_dict['update_versionless'] = self.update_versionless_checkbox.isChecked()
        self.args_dict['only_versionless'] = self.only_versionless

    def showEvent(self, event):
        if not self.shown:
            self.create_ui()

    def checkin_progress(self, progress, info_dict):
        self.commit_item.set_progress_indicator_on()
        self.commit_item.set_progress_status(progress, info_dict)

        commit_queue_ui = self.commit_queue_ui

        if not commit_queue_ui:
            project_code = tc.split_search_key(self.args_dict['search_key'])
            commit_queue_ui = env_inst.get_commit_queue(project_code['project_code'])

        commit_queue_ui.set_progress_indicator_on()
        commit_queue_ui.set_progress(progress, info_dict)

    def interrupt_commit(self):
        if self.virtual_snapshot_worker:
            self.virtual_snapshot_worker.disable_signals()
        # if self.snapshot_checkin_worker:
        #     self.snapshot_checkin_worker.disable_signals()
        if self.inplace_checkin_worker:
            self.inplace_checkin_worker.disable_signals()
        if self.upload_checkin_worker:
            self.upload_checkin_worker.disable_signals()

    def commit(self, single_commit=False, single_threaded=False):
        self.single_commit = single_commit
        self.single_threaded = single_threaded

        checkin_method = self.args_dict['mode']
        # print checkin_method

        # TODO here will be checkin variants 'upload, etc'
        if not self.commit_item.is_commit_finished():

            run_before_checkin = self.args_dict['run_before_checkin']
            if run_before_checkin:
                setattr(run_before_checkin, 'checkin_widget', self)
                run_before_checkin()

            if checkin_method in ['inplace', 'preallocate']:
                self.begin_commit_inplace()
            elif checkin_method == 'upload':
                self.begin_commit_upload()

    @gf.catch_error
    def upload_chekin(self):

        if self.args_dict['checkin_app'] == 'standalone':
            def upload_checkin_agent():
                info_dict = {
                    'status_text': 'Copying Files to Repo',
                    'total_count': 6
                }
                dl.log('Preparing files', group_id='server/checkin')
                # for in-lace checkin in local repos
                self.upload_checkin_worker.emit_progress(3, info_dict)
                check_ok = tc.inplace_checkin(
                    self.args_dict['file_paths'],
                    self.virtual_snapshot,
                    self.args_dict['repo_name'],
                    self.args_dict['update_versionless'],
                    self.args_dict['only_versionless'],
                    self.args_dict['create_icon'],
                    self.args_dict['files_objects'],
                    self.args_dict['padding'],
                    progress_callback=self.upload_checkin_worker.emit_progress,
                )
                self.upload_checkin_worker.emit_progress(4, info_dict)
                return check_ok

            self.upload_checkin_worker, thread_pool = gf.get_thread_worker(
                upload_checkin_agent,
                thread_pool=env_inst.get_thread_pool('commit_queue/server_thread_pool'),
                result_func=self.upload_chekin_snapshot,
                # finished_func=self.checkin_done,
                progress_func=self.checkin_progress,
                error_func=gf.error_handle
            )
            thread_pool.start(self.upload_checkin_worker)

        if self.args_dict['checkin_app'] == 'maya':
            dl.log('Preparing files', group_id='server/checkin')

            import thlib.maya_functions as mf
            mf.set_info_to_scene(self.args_dict['search_key'], self.args_dict['context'])

            check_ok, files_objects = mf.inplace_checkin(
                self.virtual_snapshot,
                self.args_dict['repo_name'],
                self.args_dict['update_versionless'],
                self.args_dict['only_versionless'],
                self.args_dict['create_icon'],
                selected_objects=self.args_dict['selected_objects'],
                ext_type=self.args_dict['ext_type'],
                setting_workspace=self.args_dict['setting_workspace'],
            )

            if check_ok:
                self.args_dict['files_objects'] = files_objects
                self.upload_chekin_snapshot()
            else:
                self.commit_item.set_progress_indicator_on()
                self.commit_item.set_commit_failed()

    @gf.catch_error
    def upload_chekin_snapshot(self, result=None):

        if env_mode.get_platform() != 'Windows':
            self.upload_chekin_snapshot_legacy()
        else:
            self.update_args_dict()

            info_dict = {
                'status_text': 'Saving Snapshot To DB',
                'total_count': 6
            }
            dl.log('Begin snapshot Ceheckin', group_id='server/checkin')
            self.checkin_progress(5, info_dict)
            api_client = env_api.execute_method('checkin_snapshot',
                search_key=self.args_dict['search_key'],
                context=self.args_dict['context'],
                snapshot_type=self.args_dict['snapshot_type'],
                is_revision=self.args_dict['is_revision'],
                description=self.args_dict['description'],
                version=self.args_dict['version'],
                update_versionless=self.args_dict['update_versionless'],
                only_versionless=self.args_dict['only_versionless'],
                keep_file_name=self.args_dict['keep_file_name'],
                repo_name=self.args_dict['repo_name'],
                virtual_snapshot=self.virtual_snapshot,
                files_dict=self.args_dict['files_dict'],
                mode=self.args_dict['mode'],
                create_icon=self.args_dict['create_icon'],
                files_objects=self.args_dict['files_objects'],)

            env_api.get_results(api_client, self.checkin_done)

            self.checkin_progress(6, info_dict)

    @gf.catch_error
    def upload_chekin_snapshot_legacy(self, result=None):
        self.update_args_dict()

        def upload_checkin_snapshot_agent():
            info_dict = {
                'status_text': 'Saving Snapshot To DB',
                'total_count': 6
            }
            snapshot_checkin_worker.emit_progress(5, info_dict)

            snapshot = tc.checkin_snapshot(
                search_key=self.args_dict['search_key'],
                context=self.args_dict['context'],
                snapshot_type=self.args_dict['snapshot_type'],
                is_revision=self.args_dict['is_revision'],
                description=self.args_dict['description'],
                version=self.args_dict['version'],
                update_versionless=self.args_dict['update_versionless'],
                only_versionless=self.args_dict['only_versionless'],
                keep_file_name=self.args_dict['keep_file_name'],
                repo_name=self.args_dict['repo_name'],
                virtual_snapshot=self.virtual_snapshot,
                files_dict=self.args_dict['files_dict'],
                mode=self.args_dict['mode'],
                create_icon=self.args_dict['create_icon'],
                files_objects=self.args_dict['files_objects'],
            )
            snapshot_checkin_worker.emit_progress(6, info_dict)
            # self.commit_item.set_commit_finished()
            return snapshot

        snapshot_checkin_worker, thread_pool = gf.get_thread_worker(
            upload_checkin_snapshot_agent,
            thread_pool=env_inst.get_thread_pool('commit_queue/checkin_snapshot_pool'),
            result_func=self.checkin_done,
            # finished_func=self.commit_item.set_commit_finished,
            progress_func=self.checkin_progress,
            error_func=gf.error_handle
        )
        if self.single_threaded:
            self.checkin_done(self.commit_item)
        else:
            thread_pool.start(snapshot_checkin_worker)

    @gf.catch_error
    def inplace_chekin(self):

        if self.args_dict['checkin_app'] == 'standalone':
            def inplace_checkin_agent():
                # for in-place checkin
                check_ok = tc.inplace_checkin(
                    self.args_dict['file_paths'],
                    self.virtual_snapshot,
                    self.args_dict['repo_name'],
                    self.args_dict['update_versionless'],
                    self.args_dict['only_versionless'],
                    self.args_dict['create_icon'],
                    self.args_dict['files_objects'],
                    self.args_dict['padding'],
                    progress_callback=self.inplace_checkin_worker.emit_progress,
                )
                return check_ok

            self.inplace_checkin_worker, thread_pool = gf.get_thread_worker(
                inplace_checkin_agent,
                thread_pool=env_inst.get_thread_pool('commit_queue/server_thread_pool'),
                result_func=self.inplace_checkin_done,
                finished_func=self.inplace_chekin_snapshot,
                progress_func=self.checkin_progress,
                error_func=gf.error_handle
            )
            if self.single_threaded:
                inplace_checkin_agent()
                self.chekin_snapshot()
            else:
                thread_pool.start(self.inplace_checkin_worker)

        if self.args_dict['checkin_app'] == 'maya':
            import thlib.maya_functions as mf
            mf.set_info_to_scene(self.args_dict['search_key'], self.args_dict['context'])

            # for in-place checkin
            check_ok, files_objects = mf.inplace_checkin(
                self.virtual_snapshot,
                self.args_dict['repo_name'],
                self.args_dict['update_versionless'],
                self.args_dict['only_versionless'],
                self.args_dict['create_icon'],
                selected_objects=self.args_dict['selected_objects'],
                ext_type=self.args_dict['ext_type'],
                setting_workspace=self.args_dict['setting_workspace'],
            )

            if check_ok:
                self.args_dict['files_objects'] = files_objects
                self.inplace_chekin_snapshot()
            else:
                self.commit_item.set_progress_indicator_on()
                self.commit_item.set_commit_failed()

    def inplace_checkin_done(self, result):
        pass

    @gf.catch_error
    def inplace_chekin_snapshot(self):
        self.update_args_dict()
        # print 'begin checkin snapshot'

        def inplace_checkin_agent():
            info_dict = {
                'status_text': 'Saving Snapshot To DB',
                'total_count': 2
            }
            snapshot_checkin_worker.emit_progress(0, info_dict)
            snapshot = tc.checkin_snapshot(
                search_key=self.args_dict['search_key'],
                context=self.args_dict['context'],
                snapshot_type=self.args_dict['snapshot_type'],
                is_revision=self.args_dict['is_revision'],
                description=self.args_dict['description'],
                version=self.args_dict['version'],
                update_versionless=self.args_dict['update_versionless'],
                only_versionless=self.args_dict['only_versionless'],
                keep_file_name=self.args_dict['keep_file_name'],
                repo_name=self.args_dict['repo_name'],
                virtual_snapshot=self.virtual_snapshot,
                files_dict=self.args_dict['files_dict'],
                mode=self.args_dict['mode'],
                create_icon=self.args_dict['create_icon'],
                files_objects=self.args_dict['files_objects'],
            )
            snapshot_checkin_worker.emit_progress(1, info_dict)
            return snapshot

        snapshot_checkin_worker, thread_pool = gf.get_thread_worker(
            inplace_checkin_agent,
            thread_pool=env_inst.get_thread_pool('commit_queue/server_thread_pool'),
            result_func=self.checkin_done,
            progress_func=self.checkin_progress,
            error_func=gf.error_handle
        )
        if self.single_threaded:
            self.checkin_done(inplace_checkin_agent())
        else:
            thread_pool.start(snapshot_checkin_worker)

    def checkin_done(self, result=None):
        # print 'checkin done'

        run_after_checkin = self.args_dict['run_after_checkin']
        if run_after_checkin:
            setattr(run_after_checkin, 'checkin_widget', self)
            run_after_checkin()

        self.commit_item.set_commit_finished()

        commit_queue_ui = self.commit_queue_ui

        if not commit_queue_ui:
            project_code = tc.split_search_key(self.args_dict['search_key'])
            commit_queue_ui = env_inst.get_commit_queue(project_code['project_code'])

        # print 'refreshing'

        if self.single_commit:
            commit_queue_ui.remove_item_from_queue(self.commit_item)
            commit_queue_ui.refresh_result_after_commit()
        else:
            commit_queue_ui.commit_queue()
            commit_queue_ui.clear_queue_after_checkin()

    def set_commit_item(self, commit_item):
        self.commit_item = commit_item

    def refresh_commit_item_description(self):

        if self.commit_item:
            self.commit_item.set_description(self.description_widget.get_description('plain'))

    def controls_actions(self):

        self.update_versionless_checkbox.stateChanged.connect(self.switch_versionless_checkbox)
        self.only_versionless_checkbox.stateChanged.connect(self.switch_only_versionless_checkbox)

        if self.multiple_edit_mode:
            self.update_versionless_checkbox.stateChanged.connect(self.apply_to_multiple_items)
            self.only_versionless_checkbox.stateChanged.connect(self.apply_to_multiple_items)
            self.context_edit.editingFinished.connect(self.apply_to_multiple_items)
            self.repo_combo_box.currentIndexChanged.connect(self.apply_to_multiple_items)
            self.keep_file_name_checkbox.stateChanged.connect(self.apply_to_multiple_items)
        else:
            self.context_as_file_name_checkbox.stateChanged.connect(self.switch_context_as_filename)
            self.keep_file_name_checkbox.stateChanged.connect(self.switch_keep_filename)
            self.description_widget.descriptionTextEdit.textChanged.connect(self.refresh_commit_item_description)
            self.context_edit.editingFinished.connect(self.refresh_virtual_snapshot)
            self.context_edit.textEdited.connect(self.edit_context)
            self.explicit_file_name_edit.textEdited.connect(self.edit_explicit_filename)
            self.explicit_file_name_edit.editingFinished.connect(self.refresh_virtual_snapshot)
            self.make_screenshot_button.clicked.connect(lambda: self.set_preview_to_commit_item('screenshot'))
            self.choose_preview_button.clicked.connect(self.browse_for_preview)
            self.edit_previews_button.clicked.connect(self.edit_previews)
            self.clear_previews_button.clicked.connect(self.clear_all)
            self.repo_combo_box.currentIndexChanged.connect(self.change_current_repo)

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def create_checkboxes_widget(self):
        self.update_versionless_checkbox = QtGui.QCheckBox('Update Versionless')
        self.only_versionless_checkbox = QtGui.QCheckBox('Commit Versionless Only')
        if self.update_versionless:
            self.update_versionless_checkbox.setChecked(True)
        else:
            self.update_versionless_checkbox.setChecked(False)
        self.main_layout.addWidget(self.update_versionless_checkbox, 4, 0, 1, 1)

        self.main_layout.addWidget(self.only_versionless_checkbox, 4, 1, 1, 2)

    def create_drop_plate(self):

        self.drop_plate = QtGui.QWidget()
        self.drop_plate.setMinimumWidth(200)
        self.drop_plate.setMinimumHeight(32)
        self.drop_plate_layout = QtGui.QHBoxLayout()
        self.drop_plate_layout.setSpacing(0)
        self.drop_plate_layout.setContentsMargins(0, 0, 0, 0)
        self.drop_plate.setLayout(self.drop_plate_layout)
        self.drop_plate_label = QtGui.QLabel('Drop Images Here (0)')
        self.drop_plate_label.setAlignment(QtCore.Qt.AlignCenter)
        self.drop_plate_layout.addWidget(self.drop_plate_label)
        self.drop_plate_label.setStyleSheet('QLabel{border: 1px solid grey;border-radius: 4px;background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 0, 0, 16), stop:1 rgba(0, 0, 0, 24));}')
        self.drop_plate.setAcceptDrops(True)
        self.drop_plate.dragEnterEvent = self.drop_plate_dragEnterEvent
        self.drop_plate.dragMoveEvent = self.drop_plate_dragMoveEvent
        self.drop_plate.dropEvent = self.drop_plate_dropEvent

    def apply_to_multiple_items(self):

        for commit_item in self.commit_items_list:
            commit_widget = commit_item.get_commit_widget()
            commit_widget.update_versionless_checkbox.setChecked(self.update_versionless_checkbox.checkState())
            commit_widget.only_versionless_checkbox.setChecked(self.only_versionless_checkbox.checkState())
            commit_widget.context_edit.setText(self.context_edit.text())
            commit_widget.edit_context(self.context_edit.text())
            commit_widget.repo_combo_box.setCurrentIndex(self.repo_combo_box.currentIndex())
            commit_widget.keep_file_name_checkbox.setCheckState(self.keep_file_name_checkbox.checkState())
            commit_widget.refresh_virtual_snapshot()

    def add_links_to_upload_list(self, links):
        for link in links:
            ext = gf.extract_extension(link)
            if ext[3] == 'preview':
                self.links_to_upload_list.add(link)

        self.links_to_upload_list = set(self.links_to_upload_list)

        self.drop_plate_label.setText(
            'Drop Images Here ({0})'.format(len(self.get_upload_list()) + len(self.screenshots_to_upload_list)))

    def get_upload_list(self):
        return self.links_to_upload_list

    def get_upload_list_files_objects(self):
        files_list = self.get_upload_list()

        if files_list:
            match_template = gf.MatchTemplate(['$FILENAME.$EXT'])
            return match_template.get_files_objects(files_list)

    def get_screenshots_to_upload_list(self):

        return self.screenshots_to_upload_list

    def drop_plate_dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def drop_plate_dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def drop_plate_dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            links = []
            for url in event.mimeData().urls():
                links.append(unicode(url.toLocalFile()))

            self.add_links_to_upload_list(links)
        else:
            event.ignore()

    def create_edits_widgets(self):

        self.context_edit = QtGui.QLineEdit()
        self.context_edit.setText(self.get_only_context())

        self.context_edit_label = QtGui.QLabel('Context:')

        self.explicit_file_name_edit = QtGui.QLineEdit()
        self.explicit_file_name_edit.setText(self.args_dict['explicit_filename'])
        self.explicit_file_name_label = QtGui.QLabel('Explicit File Name:')

        self.context_as_file_name_checkbox = QtGui.QCheckBox('Context as Explicit File Name')
        self.keep_file_name_checkbox = QtGui.QCheckBox('Keep File Name')

        self.previews_layout = QtGui.QHBoxLayout()
        self.previews_layout.setContentsMargins(0, 0, 0, 0)
        self.previews_widget = QtGui.QWidget()
        self.previews_widget.setLayout(self.previews_layout)

        self.make_screenshot_button = QtGui.QToolButton()
        self.make_screenshot_button.setAutoRaise(True)
        self.make_screenshot_button.setIcon(gf.get_icon('camera'))

        self.choose_preview_button = QtGui.QToolButton()
        self.choose_preview_button.setAutoRaise(True)
        self.choose_preview_button.setIcon(gf.get_icon('folder-open'))

        self.edit_previews_button = QtGui.QToolButton()
        self.edit_previews_button.setAutoRaise(True)
        self.edit_previews_button.setIcon(gf.get_icon('edit'))

        self.clear_previews_button = QtGui.QToolButton()
        self.clear_previews_button.setAutoRaise(True)
        self.clear_previews_button.setIcon(gf.get_icon('trash'))

        self.create_drop_plate()

        self.previews_layout.addWidget(self.make_screenshot_button)
        self.previews_layout.addWidget(self.choose_preview_button)
        self.previews_layout.addWidget(self.drop_plate)
        self.previews_layout.addWidget(self.edit_previews_button)
        self.previews_layout.addWidget(self.clear_previews_button)

        self.repo_combo_box = QtGui.QComboBox()
        self.repo_label = QtGui.QLabel('Repository:')
        self.fill_repo_combo_box()

        self.main_layout.addWidget(self.context_edit, 9, 1, 1, 1)
        self.main_layout.addWidget(self.context_edit_label, 9, 0, 1, 1)
        self.main_layout.addWidget(self.explicit_file_name_edit, 10, 1, 1, 1)
        self.main_layout.addWidget(self.explicit_file_name_label, 10, 0, 1, 1)
        self.main_layout.addWidget(self.repo_combo_box, 11, 1, 1, 1)
        self.main_layout.addWidget(self.repo_label, 11, 0, 1, 1)
        self.main_layout.addWidget(self.context_as_file_name_checkbox, 12, 0, 1, 2)
        self.main_layout.addWidget(self.keep_file_name_checkbox, 13, 0, 1, 2)
        self.main_layout.addWidget(self.previews_widget, 0, 0, 1, 2)

    def create_info_label_widget(self):
        self.info_label_widget = QtGui.QLabel()
        self.fill_info_label_widget()
        self.main_layout.addWidget(self.info_label_widget, 1, 0, 1, 2)

    def fill_info_label_widget(self):
        self.info_label_widget.setText(
            u'Context: <b>{0}</b>; '
            u'Repository: <span style="color:{2};"><b>{1}</b></span>; '.format(
                self.context,
                self.repo['value'][1],
                u'rgb({},{},{})'.format(*self.repo['value'][2]),))

    def create_label_widget(self):
        self.update_versionless_label = QtGui.QLabel()
        self.only_versionless_label = QtGui.QLabel()
        self.main_layout.addWidget(self.update_versionless_label, 3, 0, 1, 2)
        self.main_layout.addWidget(self.only_versionless_label, 3, 0, 1, 2)

    def switch_versionless_label_text(self):
        if self.update_versionless:
            self.update_versionless_label.setText('<p>Versionless files will be <span style="color:#00aa00;"><b>Updated</b></span></p>')
        else:
            self.update_versionless_label.setText('<p>Versionless files will <span style="color:#aa0000;"><b>not be</b></span> Updated</p>')

    def switch_only_versionless_label_text(self):
        if self.only_versionless:
            self.only_versionless_label.setText('<p><span style="color:#00aa00;"><b>Only Versionless</b></span> files will be Committed</p>')
        else:
            self.only_versionless_label.setText('')

    def switch_versionless_checkbox(self):

        if self.update_versionless_checkbox.isChecked():
            self.update_versionless = True
            self.collapse_wdg_vls.setVisible(True)
        else:
            self.update_versionless = False
            self.collapse_wdg_vls.setVisible(False)

        self.switch_versionless_label_text()

    def switch_only_versionless_checkbox(self):
        if self.only_versionless_checkbox.isChecked():
            self.only_versionless = True
            self.collapse_wdg_vers.setVisible(False)
            self.update_versionless_label.setVisible(False)
            self.update_versionless_checkbox.setChecked(True)
            self.update_versionless_checkbox.setEnabled(False)
        else:
            self.only_versionless = False
            self.collapse_wdg_vers.setVisible(True)
            self.update_versionless_label.setVisible(True)
            self.update_versionless_checkbox.setEnabled(True)

        self.switch_only_versionless_label_text()

    def switch_context_as_filename(self):
        if self.context_as_file_name_checkbox.isChecked():
            self.context_edit.setEnabled(False)
            if self.context_edit.text():
                self.explicit_file_name_edit.setText(self.context_edit.text())
            else:
                self.context_edit.setText(self.explicit_file_name_edit.text())
            self.context_edit.textEdited.emit(self.context_edit.text())
            self.refresh_virtual_snapshot()
        else:
            self.context_edit.setEnabled(True)

    def switch_keep_filename(self):
        if self.keep_file_name_checkbox.isChecked():
            self.args_dict['keep_file_name'] = True
        else:
            self.args_dict['keep_file_name'] = False

        self.refresh_virtual_snapshot()

    @gf.catch_error
    def begin_commit_inplace(self):
        self.update_args_dict()

        def update_virtual_snapshot_agent():
            info_dict = {
                'status_text': 'Updating Snapshot Info',
                'total_count': 2
            }
            self.virtual_snapshot_worker.emit_progress(0, info_dict)
            virtual_snapshot = tc.get_virtual_snapshot(
                search_key=self.args_dict['search_key'],
                context=self.args_dict['context'],
                snapshot_type=self.args_dict['snapshot_type'],
                files_dict=self.args_dict['files_dict'],
                is_revision=self.args_dict['is_revision'],
                keep_file_name=self.args_dict['keep_file_name'],
                explicit_filename=self.args_dict['explicit_filename'],
                version=self.args_dict['version'],
                checkin_type=self.args_dict['checkin_type'],
                ignore_keep_file_name=self.args_dict['ignore_keep_file_name'],
                )
            self.virtual_snapshot_worker.emit_progress(1, info_dict)
            return virtual_snapshot

        self.virtual_snapshot_worker, thread_pool = gf.get_thread_worker(
            update_virtual_snapshot_agent,
            thread_pool=env_inst.get_thread_pool('commit_queue/server_thread_pool'),
            result_func=self.fill_virtual_snapshot,
            finished_func=self.inplace_chekin,
            progress_func=self.checkin_progress,
            error_func=gf.error_handle
        )
        if self.single_threaded:
            # TODO this will cause CRASHES
            self.fill_virtual_snapshot(update_virtual_snapshot_agent())
            self.inplace_chekin()
        else:
            thread_pool.start(self.virtual_snapshot_worker)

    @gf.catch_error
    def begin_commit_upload(self):
        self.update_args_dict()

        def update_virtual_snapshot_agent():
            info_dict = {
                'status_text': 'Updating Snapshot Info',
                'total_count': 6
            }

            dl.log('Begin Upload Commit', group_id='server/checkin')
            self.virtual_snapshot_worker.emit_progress(0, info_dict)

            virtual_snapshot = tc.get_virtual_snapshot(
                search_key=self.args_dict['search_key'],
                context=self.args_dict['context'],
                snapshot_type=self.args_dict['snapshot_type'],
                files_dict=self.args_dict['files_dict'],
                is_revision=self.args_dict['is_revision'],
                keep_file_name=self.args_dict['keep_file_name'],
                explicit_filename=self.args_dict['explicit_filename'],
                version=self.args_dict['version'],
                checkin_type=self.args_dict['checkin_type'],
                ignore_keep_file_name=self.args_dict['ignore_keep_file_name'],
                )
            self.virtual_snapshot_worker.emit_progress(1, info_dict)

            return virtual_snapshot

        self.virtual_snapshot_worker, thread_pool = gf.get_thread_worker(
            update_virtual_snapshot_agent,
            thread_pool=env_inst.get_thread_pool('commit_queue/server_thread_pool'),
            result_func=self.fill_virtual_snapshot,
            finished_func=self.upload_chekin,
            progress_func=self.checkin_progress,
            error_func=gf.error_handle
        )
        thread_pool.start(self.virtual_snapshot_worker)

    def refresh_virtual_snapshot(self):

        self.update_args_dict()

        def refresh_virtual_snapshot_agent():
            info_dict = {
                'status_text': 'Updating Snapshot Info',
                'total_count': 2
            }
            self.virtual_snapshot_worker.emit_progress(0, info_dict)

            virtual_snapshot = tc.get_virtual_snapshot(
                search_key=self.args_dict['search_key'],
                context=self.args_dict['context'],
                snapshot_type=self.args_dict['snapshot_type'],
                files_dict=self.args_dict['files_dict'],
                is_revision=self.args_dict['is_revision'],
                keep_file_name=self.args_dict['keep_file_name'],
                explicit_filename=self.args_dict['explicit_filename'],
                version=self.args_dict['version'],
                checkin_type=self.args_dict['checkin_type'],
                ignore_keep_file_name=self.args_dict['ignore_keep_file_name'],
                )

            self.virtual_snapshot_worker.emit_progress(1, info_dict)

            return virtual_snapshot

        self.virtual_snapshot_worker, thread_pool = gf.get_thread_worker(
            refresh_virtual_snapshot_agent,
            thread_pool=env_inst.get_thread_pool('commit_queue/server_thread_pool'),
            result_func=self.fill_virtual_snapshot,
            progress_func=self.checkin_progress,
            error_func=gf.error_handle,
        )

        thread_pool.start(self.virtual_snapshot_worker)

    @gf.catch_error
    def fill_virtual_snapshot(self, result):
        self.virtual_snapshot = result
        self.fill_versionless_widget(self.virtual_snapshot)
        self.fill_versions_widget(self.virtual_snapshot)
        self.commit_item.set_progress_indicator_off()

        if self.args_dict['checkin_app'] == 'maya':
            import thlib.maya_functions as mf

            temp_playblast = mf.get_temp_playblast()

            self.commit_item.set_preview(image_path=temp_playblast)

    def create_versionless_widget(self):

        self.collapse_wdg_vls = Ui_collapsableWidget(state=False)
        layout_files = QtGui.QVBoxLayout()
        self.collapse_wdg_vls.setLayout(layout_files)
        self.collapse_wdg_vls.setText('Hide Versionless Files')
        self.collapse_wdg_vls.setCollapsedText('Show Versionless Files')

        self.treeWidget_vls = QtGui.QTreeWidget()
        self.treeWidget_vls.setAlternatingRowColors(True)
        self.treeWidget_vls.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.treeWidget_vls.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.treeWidget_vls.setRootIsDecorated(False)
        self.treeWidget_vls.headerItem().setText(0, "File")
        self.treeWidget_vls.headerItem().setText(1, "Path")
        self.treeWidget_vls.setStyleSheet(gf.get_qtreeview_style())
        self.treeWidget_vls.setTextElideMode(QtCore.Qt.ElideLeft)

        layout_files.addWidget(self.treeWidget_vls)

        self.main_layout.addWidget(self.collapse_wdg_vls, 6, 0, 1, 2)

    def create_versions_widget(self):

        self.collapse_wdg_vers = Ui_collapsableWidget(state=False)
        layout_files = QtGui.QVBoxLayout()
        self.collapse_wdg_vers.setLayout(layout_files)
        self.collapse_wdg_vers.setText('Hide Versions Files')
        self.collapse_wdg_vers.setCollapsedText('Show Versions Files')

        self.treeWidget_vers = QtGui.QTreeWidget()
        self.treeWidget_vers.setAlternatingRowColors(True)
        self.treeWidget_vers.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.treeWidget_vers.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.treeWidget_vers.setRootIsDecorated(False)
        self.treeWidget_vers.headerItem().setText(0, "File")
        self.treeWidget_vers.headerItem().setText(1, "Path")
        self.treeWidget_vers.setStyleSheet(gf.get_qtreeview_style())
        self.treeWidget_vers.setTextElideMode(QtCore.Qt.ElideLeft)

        layout_files.addWidget(self.treeWidget_vers)

        self.main_layout.addWidget(self.collapse_wdg_vers, 7, 0, 1, 2)

    def fill_versionless_widget(self, paths):
        self.treeWidget_vls.clear()
        # print paths
        for keys, values in paths:
            for i, fl in enumerate(values['versionless']['names']):
                full_path = gf.form_path(self.repo['value'][0] + '/' + values['versionless']['paths'][i])
                item = QtGui.QTreeWidgetItem()
                item.setText(0, u''.join(fl))
                item.setText(1, full_path)
                self.treeWidget_vls.addTopLevelItem(item)
        self.treeWidget_vls.resizeColumnToContents(0)

    def fill_versions_widget(self, paths):
        self.treeWidget_vers.clear()
        file_names = []
        for keys, values in paths:
            for i, fl in enumerate(values['versioned']['names']):
                full_path = gf.form_path(self.repo['value'][0] + '/' + values['versioned']['paths'][i])
                item = QtGui.QTreeWidgetItem()
                item.setText(0, u''.join(fl))
                file_names.append(u''.join(fl))
                item.setText(1, full_path)
                self.treeWidget_vers.addTopLevelItem(item)

        if self.commit_item:
            self.commit_item.set_new_title(file_names[0])
        self.treeWidget_vers.resizeColumnToContents(0)

    def create_description_widget(self):

        self.collapse_wdg_descr = Ui_collapsableWidget(state=False)
        layout_files = QtGui.QVBoxLayout()
        self.collapse_wdg_descr.setLayout(layout_files)
        self.collapse_wdg_descr.setText('Hide Description')
        self.collapse_wdg_descr.setCollapsedText('Show Description')

        from thlib.ui_classes.ui_description_classes import Ui_descriptionWidget

        self.description_widget = Ui_descriptionWidget(None, None, parent=self)
        self.description_widget.descriptionTextEdit.setViewportMargins(0, 20, 0, 0)

        self.description_widget.setMinimumHeight(100)
        # self.description_widget.setMinimumWidth(400)

        self.description_widget.set_description(self.description)

        layout_files.addWidget(self.description_widget)
        self.main_layout.addWidget(self.collapse_wdg_descr, 8, 0, 1, 2)

        # if not self.description:
            # self.collapse_wdg_descr.setHidden(True)

    def get_only_context(self):

        if len(self.context.split('/')) > 1:
            return self.context.split('/')[-1]
        else:
            return ''

    def set_only_context(self, context):
        if context:
            self.context = u'{0}/{1}'.format(self.context.split('/')[0], context.strip().replace(' ', '_'))
        else:
            self.context = self.context.split('/')[0]

    def edit_context(self, text):
        self.set_only_context(text)
        self.args_dict['context'] = self.context
        self.fill_info_label_widget()

    def edit_explicit_filename(self, text):
        if self.context_as_file_name_checkbox.isChecked():
            self.context_edit.setText(text)
            self.context_edit.textEdited.emit(text)

        self.args_dict['explicit_filename'] = text.strip().replace(' ', '_')

    def change_current_repo(self, idx):
        self.repo = self.repo_combo_box.itemData(idx)
        self.args_dict['repo_name'] = self.repo
        self.fill_info_label_widget()
        self.refresh_virtual_snapshot()

    def fill_repo_combo_box(self):

        self.repo_combo_box.clear()

        base_dirs = env_tactic.get_all_base_dirs()

        for key, val in base_dirs:
            if val['value'][4]:
                self.repo_combo_box.addItem(val['value'][1])
                self.repo_combo_box.setItemData(self.repo_combo_box.count() - 1, val)

        current_repo = gf.get_value_from_config(cfg_controls.get_checkin(), 'repositoryComboBox')

        if current_repo:
            self.repo_combo_box.setCurrentIndex(current_repo)


class Ui_commitQueueWidget(QtGui.QMainWindow, Ui_commitQueue):
    def __init__(self, project=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.queue_list = []
        self.single_threaded = False

        self.setupUi(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.create_ui()

    def create_ui(self):
        if self.project:
            self.setWindowTitle('Commit Queue for Project: {0}'.format(self.project.info.get('title')))
        else:
            self.setWindowTitle('Global Commit Queue')

        # self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlags(QtCore.Qt.Window)

        self.create_files_queue_tree_context_menu()
        self.create_progress_bar_widget()

        self.clearQueuePushButton.setIcon(gf.get_icon('trash'))
        self.clearQueuePushButton.setEnabled(False)
        self.commitAllPushButton.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        self.commitAllPushButton.setEnabled(False)

        self.create_empty_queue_label()

        self.customize_ui()

        self.controls_actions()

    def set_single_threaded(self, single_threaded=True):
        self.single_threaded = single_threaded

    def customize_ui(self):
        self.filesQueueTreeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.filesQueueTreeWidget.setStyleSheet(gf.get_qtreeview_style())
        self.filesQueueTreeWidget.setFocusPolicy(QtCore.Qt.NoFocus)

    def create_files_queue_tree_context_menu(self):
        self.filesQueueTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.filesQueueTreeWidget.customContextMenuRequested.connect(self.open_menu)

    def queue_items_menu(self):

        commit_current = QtGui.QAction('Commit Current', self.filesQueueTreeWidget)
        commit_current.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        commit_current.triggered.connect(self.commit_current_item)

        delete_current = QtGui.QAction('Remove From Queue', self.filesQueueTreeWidget)
        delete_current.setIcon(gf.get_icon('remove'))
        delete_current.triggered.connect(self.remove_item_from_queue)

        menu = QtGui.QMenu()

        menu.addAction(commit_current)
        menu.addAction(delete_current)

        return menu

    def open_menu(self):
        item = self.filesQueueTreeWidget.currentItem()
        if item:
            # if item.data(0, QtCore.Qt.UserRole):
                menu = self.queue_items_menu()
                if menu:
                    menu.exec_(Qt4Gui.QCursor.pos())

    def controls_actions(self):
        self.filesQueueTreeWidget.itemSelectionChanged.connect(self.select_current_commit_widget)
        self.clearQueuePushButton.clicked.connect(self.clear_queue)
        self.closePushButton.clicked.connect(self.close)
        self.commitAllPushButton.clicked.connect(self.commit_queue)

    def create_empty_queue_label(self):
        self.empty_label = QtGui.QLabel()
        self.empty_label.setText('Queue is empty...')
        self.empty_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.empty_label.setMinimumWidth(450)

        self.commitEditorLayout.addWidget(self.empty_label)

    def select_current_commit_widget(self):

        selected_items = self.filesQueueTreeWidget.selectedItems()
        if selected_items:
            if len(selected_items) > 1:
                commit_items = []
                for item in selected_items:
                    commit_items.append(self.filesQueueTreeWidget.itemWidget(item, 0))
                self.set_multiple_commit_widget(commit_items)
            else:
                current_item_widget = self.filesQueueTreeWidget.itemWidget(selected_items[0], 0)
                self.set_current_commit_widget(current_item_widget.get_commit_widget())

    def commit_queue(self):

        self.stop_progress()

        self.commitAllPushButton.setEnabled(False)
        self.closePushButton.setEnabled(False)
        self.clearQueuePushButton.setEnabled(False)

        next_in_queue = 0
        for commit_item in self.queue_list:
            if commit_item.is_commit_finished():
                next_in_queue += 1

        if next_in_queue < len(self.queue_list):
            commit_item = self.queue_list[next_in_queue]
            commit_widget = commit_item.get_commit_widget()
            commit_widget.commit(single_threaded=self.single_threaded)

    def commit_current_item(self):
        self.commitAllPushButton.setEnabled(False)
        self.closePushButton.setEnabled(False)
        self.clearQueuePushButton.setEnabled(False)

        commit_item = self.filesQueueTreeWidget.itemWidget(self.filesQueueTreeWidget.currentItem(), 0)

        if commit_item in self.queue_list:
            commit_widget = commit_item.get_commit_widget()
            if env_inst.get_thread_pool('commit_queue/server_thread_pool').activeThreadCount() == 0:
                commit_widget.commit(single_commit=True)

    def clear_queue_after_checkin(self):
        all_committed = False
        for commit_item in self.queue_list:
            all_committed = commit_item.is_commit_finished()

        if all_committed:
            self.refresh_result_after_commit()
            self.clear_queue()
            self.close()

    def refresh_result_after_commit(self):
        updated_list = []

        for commit_item in self.queue_list:
            item_widget = commit_item.get_args_dict()['item_widget']
            if item_widget:
                pipeline_code = item_widget.search_widget.stype.get_code()

                search_key = tc.split_search_key(commit_item.get_args_dict()['search_key'])

                checkin_ui = env_inst.get_check_tree(search_key['project_code'], 'checkin_out', pipeline_code)

                if checkin_ui not in updated_list:
                    checkin_ui.refresh_results()
                    updated_list.append(checkin_ui)

    def create_progress_bar_widget(self):

        self.progress_bar_widget = QtGui.QProgressBar()
        self.progress_bar_widget.setTextVisible(True)
        self.progress_bar_widget.setVisible(True)
        self.progress_bar_widget.setHidden(True)
        self.statusbar.addPermanentWidget(self.progress_bar_widget)

    def set_progress_indicator_on(self):
        self.progress_bar_widget.setHidden(False)

    def set_progress_indicator_off(self):
        self.progress_bar_widget.setHidden(True)
        self.statusbar.showMessage('')

    def set_progress(self, progress, info_dict):
        self.progress_bar_widget.setMaximum(info_dict['total_count'])
        self.statusbar.showMessage(info_dict['status_text'])
        self.progress_bar_widget.setValue(progress + 1)
        if self.progress_bar_widget.maximum() == progress + 1:
            self.set_progress_indicator_off()

    def stop_progress(self):
        for commit_item in self.queue_list:
            commit_widget = commit_item.get_commit_widget()
            commit_widget.interrupt_commit()

    def clear_queue(self):

        self.stop_progress()

        self.filesQueueTreeWidget.clear()
        self.queue_list = []

        self.check_queue()
        self.empty_label.close()
        self.create_empty_queue_label()

        self.closePushButton.setEnabled(True)
        self.close()

    def check_queue(self):

        for i in range(self.commitEditorLayout.count()):
            child = self.commitEditorLayout.takeAt(0)
            if child:
                if child.widget():
                    child.widget().hide()
                    self.commitEditorLayout.removeWidget(child.widget())

        if self.queue_list:
            self.filesCountLabel.setText(str(len(self.queue_list)))
        else:
            self.filesCountLabel.setText('0')

        if self.queue_list and not self.empty_label.isVisible():
            self.empty_label.setVisible(False)
            self.clearQueuePushButton.setEnabled(True)
            self.closePushButton.setEnabled(True)
            self.commitAllPushButton.setEnabled(True)
        else:
            self.empty_label.setVisible(True)
            self.clearQueuePushButton.setEnabled(False)
            self.closePushButton.setEnabled(False)
            self.commitAllPushButton.setEnabled(False)

    def check_for_duplicates(self, args_dict):
        for commit_item in self.queue_list:
            if commit_item.get_args_dict()['file_paths'] == args_dict['file_paths']:
                return commit_item
        return False

    def set_multiple_commit_widget(self, commit_items):
        self.check_queue()
        if self.queue_list:

            commit_widget = commit_items[-1].get_commit_widget()
            commit_widget.update_args_dict()

            new_commit_widget = commitWidget(
                args_dict=commit_widget.args_dict,
                commit_queue_ui=self,
                multiple_edit_mode=True
            )

            self.commitEditorLayout.addWidget(new_commit_widget)

            new_commit_widget.set_commit_items_list(commit_items)
            new_commit_widget.show()

    def set_current_commit_widget(self, commit_widget):

        self.check_queue()

        if self.queue_list:
            self.commitEditorLayout.addWidget(commit_widget)
            commit_widget.show()

    def remove_item_from_queue(self, commit_item=None):
        if not commit_item:
            commit_item = self.filesQueueTreeWidget.itemWidget(self.filesQueueTreeWidget.currentItem(), 0)

        self.queue_list.remove(commit_item)
        commit_item.close()
        commit_item.deleteLater()
        self.filesQueueTreeWidget.takeTopLevelItem(self.filesQueueTreeWidget.currentIndex().row())
        self.check_queue()
        if self.queue_list:
            self.set_current_commit_widget(self.queue_list[-1].get_commit_widget())
        else:
            self.empty_label.close()
            self.create_empty_queue_label()

    @gf.catch_error
    def add_item_to_queue(self, args_dict, commit_queue_ui=None, force=False):
        if not self.check_for_duplicates(args_dict) or force:
            commit_item = gf.add_commit_item(self.filesQueueTreeWidget, args_dict['item_widget'])
            commit_item.set_args_dict(args_dict)
            self.queue_list.append(commit_item)
            commit_widget = commitWidget(args_dict=args_dict, commit_queue_ui=commit_queue_ui)
            commit_item.set_commit_widget(commit_widget)
            commit_item.fill_info()
            commit_widget.set_commit_item(commit_item)
            self.set_current_commit_widget(commit_widget)
        else:
            buttons = (('Update Current', QtGui.QMessageBox.YesRole), ('Add New', QtGui.QMessageBox.AcceptRole), ('Ignore File', QtGui.QMessageBox.RejectRole))
            reply = gf.show_message_predefined(
                'Already in Commit Queue?',
                'File you are trying to Add Already '
                'in Commit Queue.<br>Update This commit?</br>',
                buttons=buttons,
                message_type='question'
            )
            if reply == QtGui.QMessageBox.YesRole:
                commit_item = self.check_for_duplicates(args_dict)
                commit_item.set_args_dict(args_dict)
                commit_item.fill_info()

                old_commit_widget = commit_item.get_commit_widget()
                old_commit_widget.close()
                old_commit_widget.deleteLater()

                commit_widget = commitWidget(args_dict)

                commit_item.set_commit_widget(commit_widget)
                commit_item.fill_info()

                commit_widget.set_commit_item(commit_item)

                self.set_current_commit_widget(commit_widget)

            if reply == QtGui.QMessageBox.AcceptRole:
                self.add_item_to_queue(args_dict=args_dict, commit_queue_ui=commit_queue_ui, force=True)
