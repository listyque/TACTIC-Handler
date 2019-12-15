# file ui_checkout_tree_classes.py

from functools import partial
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_mode, env_inst, env_tactic, cfg_controls, dl, env_read_config, env_write_config
import thlib.tactic_classes as tc
import thlib.global_functions as gf

import ui_addsobject_classes
import ui_maya_dialogs_classes
import ui_search_classes
import ui_notes_classes

import thlib.ui.checkin_out.ui_checkin_out_options_dialog as ui_checkin_out_options_dialog
from thlib.ui_classes.ui_repo_sync_queue_classes import Ui_repoSyncDialog
from thlib.ui_classes.ui_custom_qwidgets import MenuWithLayout, Ui_namingEditorWidget
from thlib.ui_classes.ui_drop_plate_classes import Ui_dropPlateWidget
from thlib.ui_classes.ui_snapshot_browser_classes import Ui_snapshotBrowserWidget
from thlib.ui_classes.ui_fast_controls_classes import Ui_fastControlsWidget
from thlib.ui_classes.ui_description_classes import Ui_descriptionWidget
from thlib.ui_classes.ui_columns_editor_classes import Ui_columnsViewerWidget
from thlib.ui_classes.ui_tasks_classes import Ui_tasksDockWidget

if env_mode.get_mode() == 'maya':
    import thlib.maya_functions as mf
    reload(mf)

# reload(ui_richedit_classes)
# reload(ui_addsobject_classes)
# reload(ui_drop_plate_classes)
# reload(ui_maya_dialogs_classes)
# reload(ui_search_classes)
# reload(ui_snapshot_browser_classes)
# reload(ui_fast_controls)


class Ui_checkInOutOptionsWidget(QtGui.QWidget, ui_checkin_out_options_dialog.Ui_checkinOutOptions):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.changed = False
        self.stype = stype
        self.project = project

        self.create_ui()
        # self.controls_actions()

    def create_ui(self):

        from thlib.ui_classes.ui_conf_classes import Ui_checkinOptionsPageWidget

        self.checkinPageWidget = Ui_checkinOptionsPageWidget(self)

        self.create_scroll_area()
        self.scroll_area.setWidget(self.checkinPageWidget)

        # this is potentially useful, but not necessary at this time
        self.checkinPageWidget.dropPlateOptionsGroupBox.setHidden(True)
        self.checkinPageWidget.checkinMiscOptionsGroupBox.setHidden(True)
        self.checkinPageWidget.defaultRepoPathsGroupBox.setHidden(True)
        self.checkinPageWidget.customRepoPathsGroupBox.setHidden(True)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.checkinPageWidget.checkinPageWidgetLayout.addItem(spacerItem)

        self.checkinPageWidget.collect_defaults(apply_values=True, custom_parent=self)
        # self.checkinPageWidget.custom_save_config(custom_parent=self)

    def create_scroll_area(self):
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area_contents = QtGui.QWidget()
        self.scroll_area.setStyleSheet('QScrollArea > #qt_scrollarea_viewport > QWidget {background-color: rgba(128, 128, 128, 48);}')
        self.scroll_area.setFrameShape(QtGui.QScrollArea.NoFrame)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_contents)

        self.settingsVerticalLayout.addWidget(self.scroll_area)

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'settingsPerTabCheckBox': False,
            }

        self.settingsPerTabCheckBox.setChecked(int(settings_dict.get('settingsPerTabCheckBox')))

    def get_settings_dict(self):

        settings_dict = {
            'settingsPerTabCheckBox': int(self.settingsPerTabCheckBox.isChecked()),
        }

        return settings_dict

    def get_config(self):

        return self.checkinPageWidget.page_init

    def eventFilter(self, widget, event):
        if event.type() in [QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.Wheel, QtCore.QEvent.KeyPress, QtCore.QEvent.Paint] and isinstance(widget, (
            QtGui.QCheckBox,
            QtGui.QGroupBox,
            QtGui.QRadioButton,
            QtGui.QSpinBox,
            QtGui.QComboBox,
        )):
            self.changed = True

        return QtGui.QWidget.eventFilter(self, widget, event)

    def paintEvent(self, event):
        if self.changed:
            self.checkinPageWidget.custom_save_config(custom_parent=self)
            self.changed = False
        event.accept()

    def hideEvent(self, event):
        if self.changed:
            self.checkinPageWidget.custom_save_config(custom_parent=self)
            self.changed = False
        event.accept()

    def keyPressEvent(self, event):
        if self.changed:
            self.checkinPageWidget.custom_save_config(custom_parent=self)
            self.changed = False
        event.accept()

    def leaveEvent(self, event):
        if self.changed:
            self.checkinPageWidget.custom_save_config(custom_parent=self)
            self.changed = False
        event.accept()


class Ui_checkInOutWidget(QtGui.QMainWindow):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.is_created = False
        self.is_showed = False

        self.stype = stype
        self.project = project

        self.notes_dock = None
        self.tasks_dock = None
        self.checkin_options_dock = None

        # self.process_tree_widget = None
        self.drop_plate_dock = None
        # self.naming_editor_widget = None

        self.relates_to = 'checkin_out'

        env_inst.set_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code(), self)

    def get_tab_label(self):
        tab_label = gf.create_tab_label(self.stype.get_pretty_name(), self.stype)
        tab_label.setParent(self)
        return tab_label

    def get_tab_code(self):
        return self.stype.get_code()

    def do_creating_ui(self):
        if not self.is_created:
            self.create_ui()

    def create_ui(self):

        dl.log('Creating Checkin / Checkout UI', group_id=self.stype.get_code())

        self.setObjectName(self.stype.get_code())

        self.create_search_widget()

        self.create_fast_controls_tool_bar()
        self.create_drop_plate_dock()
        self.create_snapshot_browser_dock()
        self.create_description_dock()
        self.create_columns_viewer_dock()
        self.create_advanced_search_widget()
        self.create_checkin_options_dock()
        self.create_notes_dock()
        self.create_tasks_dock()

        self.fill_gear_menu()
        self.fill_collapsable_toolbar()

        self.is_created = True

    @gf.catch_error
    def create_notes_dock(self):

        self.notes_widget = env_inst.get_check_tree(
            self.project.get_code(), 'checkin_out_instanced_widgets', 'notes_dock')

        if not self.notes_widget:
            self.notes_widget = ui_notes_classes.Ui_notesTabbedWidget(project=self.project, parent=self)
            env_inst.set_check_tree(
                self.project.get_code(), 'checkin_out_instanced_widgets', 'notes_dock', self.notes_widget)

        self.notes_dock = QtGui.QDockWidget(self)
        self.notes_dock.setWidget(self.notes_widget)
        self.notes_dock.setWindowTitle('Notes Dock')
        self.notes_dock.setObjectName('notes_dock')

        self.notes_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.notes_dock.setHidden(True)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.notes_dock)

    @gf.catch_error
    def create_tasks_dock(self):

        self.tasks_widget = env_inst.get_check_tree(self.project.get_code(), 'checkin_out_instanced_widgets', 'tasks_dock')

        if not self.tasks_widget:
            self.tasks_widget = Ui_tasksDockWidget(project=self.project, parent=self)
            env_inst.set_check_tree(
                self.project.get_code(), 'checkin_out_instanced_widgets', 'tasks_dock', self.tasks_widget)

        self.tasks_dock = QtGui.QDockWidget(self)
        self.tasks_dock.setWidget(self.tasks_widget)
        self.tasks_dock.setWindowTitle('Tasks Dock')
        self.tasks_dock.setObjectName('tasks_dock')

        self.tasks_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.tasks_dock.setHidden(True)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.tasks_dock)

    def sync_instanced_widgets(self):
        if not self.notes_dock:
            self.create_notes_dock()
        if not self.tasks_dock:
            self.create_tasks_dock()

        if not self.drop_plate_dock:
            self.create_drop_plate_dock()
        if not self.checkin_options_dock:
            self.create_checkin_options_dock()

        if not self.notes_dock.widget():
            self.notes_dock.setWidget(env_inst.get_check_tree(self.project.get_code(), 'checkin_out_instanced_widgets', 'notes_dock'))
        if not self.tasks_dock.widget():
            self.tasks_dock.setWidget(env_inst.get_check_tree(self.project.get_code(), 'checkin_out_instanced_widgets', 'tasks_dock'))
        if not self.drop_plate_dock.widget():
            self.drop_plate_dock.setWidget(env_inst.get_check_tree(self.project.get_code(), 'checkin_out_instanced_widgets', 'drop_plate_dock'))
        if not self.checkin_options_dock.widget():
            self.checkin_options_dock.setWidget(env_inst.get_check_tree(self.project.get_code(), 'checkin_out_instanced_widgets', 'checkin_options_dock'))

    @gf.catch_error
    def create_search_widget(self):
        dl.log('Creating Search Widget', group_id=self.stype.get_code())

        self.search_widget = ui_search_classes.Ui_searchWidget(stype=self.stype, project=self.project, parent=self)

        self.setCentralWidget(self.search_widget)

    @gf.catch_error
    def create_fast_controls_tool_bar(self):
        dl.log('Creating Fast Controls ToolBar', group_id=self.stype.get_code())

        self.fast_controls_tool_bar_widget = Ui_fastControlsWidget(stype=self.stype, project=self.project, parent=self)

        self.fast_controls_tool_bar = QtGui.QToolBar()
        self.fast_controls_tool_bar.addWidget(self.fast_controls_tool_bar_widget)
        self.fast_controls_tool_bar.setWindowTitle('Fast controls')
        self.fast_controls_tool_bar.setObjectName('Fast fast_controls_tool_bar')

        self.fast_controls_tool_bar.setFloatable(False)
        self.fast_controls_tool_bar.setAllowedAreas(QtCore.Qt.BottomToolBarArea | QtCore.Qt.TopToolBarArea)

        self.fast_controls_tool_bar.setHidden(True)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.fast_controls_tool_bar)

    @gf.catch_error
    def create_drop_plate_dock(self):
        dl.log('Creating Drop Plate Dock', group_id=self.stype.get_code())

        self.drop_plate_widget = env_inst.get_check_tree(
            self.project.get_code(), 'checkin_out_instanced_widgets', 'drop_plate_dock')

        if not self.drop_plate_widget:
            self.drop_plate_widget = Ui_dropPlateWidget(self)
            env_inst.set_check_tree(
                self.project.get_code(), 'checkin_out_instanced_widgets', 'drop_plate_dock', self.drop_plate_widget)

        self.drop_plate_dock = QtGui.QDockWidget(self)
        self.drop_plate_dock.setWidget(self.drop_plate_widget)
        self.drop_plate_dock.setWindowTitle('Drop Plate')
        self.drop_plate_dock.setObjectName('drop_plate_dock')

        self.drop_plate_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.drop_plate_dock.setHidden(True)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.drop_plate_dock)

    @gf.catch_error
    def create_snapshot_browser_dock(self):
        dl.log('Creating Snapshot Browser Dock', group_id=self.stype.get_code())

        self.snapshot_browser_widget = Ui_snapshotBrowserWidget(self)

        self.snapshot_browser_dock = QtGui.QDockWidget(self)
        self.snapshot_browser_dock.setWidget(self.snapshot_browser_widget)
        self.snapshot_browser_dock.setWindowTitle('Snapshot Browser')
        self.snapshot_browser_dock.setObjectName('snapshot_browser_dock')

        self.snapshot_browser_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.snapshot_browser_dock)

    @gf.catch_error
    def create_description_dock(self):
        dl.log('Creating Description Dock', group_id=self.stype.get_code())

        self.description_widget = Ui_descriptionWidget(self.project, self.stype, parent=self)

        self.description_dock = QtGui.QDockWidget(self)
        self.description_dock.setWidget(self.description_widget)
        self.description_dock.setWindowTitle('Description')
        self.description_dock.setObjectName('description_dock')

        self.description_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.description_dock.setHidden(True)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.description_dock)

    @gf.catch_error
    def create_columns_viewer_dock(self):
        dl.log('Creating Columns Viewer Dock', group_id=self.stype.get_code())

        self.columns_viewer_widget = Ui_columnsViewerWidget(self.project, self.stype, parent=self)

        self.columns_viewer_dock = QtGui.QDockWidget(self)
        self.columns_viewer_dock.setWidget(self.columns_viewer_widget)
        self.columns_viewer_dock.setWindowTitle('Columns Viewer')
        self.columns_viewer_dock.setObjectName('columns_viewer_dock')

        self.columns_viewer_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.columns_viewer_dock.setHidden(True)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.columns_viewer_dock)

    @gf.catch_error
    def create_advanced_search_widget(self):
        dl.log('Creating Advanced Search Widget', group_id=self.stype.get_code())

        self.advanced_search_widget = ui_search_classes.Ui_advancedSearchWidget(
            stype=self.stype,
            project=self.project,
            parent=self
        )

        self.search_widget.searchFiltersVerticalLayout.addWidget(self.advanced_search_widget)

    @gf.catch_error
    def create_checkin_options_dock(self):
        dl.log('Creating Checkin Options Dock', group_id=self.stype.get_code())

        self.checkin_options_widget = env_inst.get_check_tree(
            self.project.get_code(), 'checkin_out_instanced_widgets', 'checkin_options_dock')

        if not self.checkin_options_widget:
            self.checkin_options_widget = Ui_checkInOutOptionsWidget(
                stype=self.stype,
                project=self.project,
                parent=self
            )

            env_inst.set_check_tree(
                self.project.get_code(),
                'checkin_out_instanced_widgets',
                'checkin_options_dock',
                self.checkin_options_widget
            )

        self.checkin_options_dock = QtGui.QDockWidget(self)
        self.checkin_options_dock.setWidget(self.checkin_options_widget)
        self.checkin_options_dock.setWindowTitle('Checkin Options')
        self.checkin_options_dock.setObjectName('checkin_options_dock')

        self.checkin_options_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.checkin_options_dock.setHidden(True)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.checkin_options_dock)

    def get_fast_controls_widget(self):
        return self.fast_controls_tool_bar_widget

    def get_snapshot_browser(self):
        return self.snapshot_browser_widget

    def bring_snapshot_browser_dock_up(self):
        self.snapshot_browser_dock.setHidden(False)
        self.snapshot_browser_dock.raise_()

    def get_tasks_widget(self):
        return self.tasks_widget

    def get_description_widget(self):
        return self.description_widget

    def get_columns_viewer_widget(self):
        return self.columns_viewer_widget

    def get_drop_plate_widget(self):
        return self.drop_plate_widget

    def get_search_widget(self):
        return self.search_widget

    def get_advanced_search_widget(self):
        return self.advanced_search_widget

    def get_checkin_options_widget(self):
        return self.checkin_options_widget

    def get_checkin_options_widget_config(self):
        return self.checkin_options_widget.checkinPageWidget

    @gf.catch_error
    def create_naming_editor_widget(self):
        if not self.naming_editor_widget:
            self.naming_editor_widget = Ui_namingEditorWidget()
            self.naming_editor_widget.exec_()
        else:
            self.naming_editor_widget.exec_()

    @gf.catch_error
    def create_process_tree_widget(self):
        if not self.process_tree_widget:
            self.process_tree_widget = ui_search_classes.Ui_processFilterDialog(
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
            self.process_tree_widget = ui_search_classes.Ui_processFilterDialog(
                parent_ui=self,
                parent=self,
                project=self.project,
                stype=self.stype
            )
            return self.process_tree_widget.get_ignore_dict()

    def refresh_current_results(self):
        self.search_widget.update_current_search_results()

    def checkin_context_menu(self, tool_button=True, mode=None):

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()
        current_tree_widget = current_tree_widget_item.get_current_tree_widget()

        multiple_selection = False
        if len(current_tree_widget.selectedItems()) > 1:
            multiple_selection = True

        menu = MenuWithLayout()

        copy_skey = QtGui.QAction('Copy Search Key', self)
        copy_skey.setIcon(gf.get_icon('copy'))
        copy_skey.triggered.connect(self.copy_search_key)

        edit_db_table = QtGui.QAction('Edit DB Table', self)
        edit_db_table.setIcon(gf.get_icon('edit'))
        edit_db_table.triggered.connect(self.edit_db_table)

        edit_info = QtGui.QAction('Edit Info', self)
        edit_info.setIcon(gf.get_icon('edit'))
        edit_info.triggered.connect(self.edit_existing_sobject)

        edit_info_for_selected = QtGui.QAction('Edit Info for Selected', self)
        edit_info_for_selected.setIcon(gf.get_icon('edit'))
        edit_info_for_selected.triggered.connect(self.edit_existing_sobject)

        delete_sobject = QtGui.QAction('Delete', self)
        delete_sobject.setIcon(gf.get_icon('remove'))
        delete_sobject.triggered.connect(self.delete_sobject)

        delete_selected = QtGui.QAction('Delete All Selected', self)
        delete_selected.setIcon(gf.get_icon('remove'))
        delete_selected.triggered.connect(self.delete_selected_sobjects)

        save_scene = QtGui.QAction('Save scene', self)
        save_scene.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        save_scene.triggered.connect(partial(self.save_file, maya_checkin=True))

        save_snapshot = QtGui.QAction('Save snapshot', self)
        save_snapshot.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        save_snapshot.triggered.connect(self.save_file)

        open_scene = QtGui.QAction('Open scene', self)
        open_scene.setIcon(gf.get_icon('folder'))
        open_scene.triggered.connect(self.open_file)

        open_snapshot = QtGui.QAction('Open snapshot', self)
        open_snapshot.setIcon(gf.get_icon('folder'))
        open_snapshot.triggered.connect(self.open_file)

        import_snapshot = QtGui.QAction('Import', self)
        import_snapshot.setIcon(gf.get_icon('import', icons_set='mdi'))
        import_snapshot.triggered.connect(self.import_file)

        reference_snapshot = QtGui.QAction('Create Reference', self)
        reference_snapshot.setIcon(gf.get_icon('import', icons_set='mdi'))
        reference_snapshot.triggered.connect(self.reference_file)

        open_folder = QtGui.QAction('Show Folder', self)
        open_folder.setIcon(gf.get_icon('folder-open'))

        open_folder.triggered.connect(self.open_folder)

        open_folder_vls = QtGui.QAction('Show Folder', self)
        open_folder_vls.setIcon(gf.get_icon('folder-open'))

        open_folder_vls.triggered.connect(lambda: self.open_folder('versionless'))

        open_folder_v = QtGui.QAction('Show Folder Versions', self)
        open_folder_v.setIcon(gf.get_icon('folder-open'))

        open_folder_v.triggered.connect(lambda: self.open_folder('versions'))

        open_folder_wf = QtGui.QAction('Show Watch folder', self)
        open_folder_wf.setIcon(gf.get_icon('folder-open'))

        open_folder_wf.triggered.connect(self.open_watch_folder)

        create_watch_folder = QtGui.QAction('Create Watch Folder', self)
        create_watch_folder.setIcon(gf.get_icon('eye'))

        create_watch_folder.triggered.connect(self.create_watch_folder)

        edit_watch_folder = QtGui.QAction('Edit Watch Folder', self)
        edit_watch_folder.setIcon(gf.get_icon('eye'))

        edit_watch_folder.triggered.connect(self.edit_watch_folder)

        remove_watch_folder = QtGui.QAction('Delete Watch Folder', self)
        remove_watch_folder.setIcon(gf.get_icon('eye-slash'))

        remove_watch_folder.triggered.connect(self.delete_watch_folder)

        save_selected_snapshot = QtGui.QAction('Save selected objects', self)
        save_selected_snapshot.triggered.connect(lambda: self.save_file(selected_objects=[True], maya_checkin=True))

        save_snapshot_revision = QtGui.QAction('Add revision (override current file)', self)
        save_snapshot_revision.triggered.connect(lambda: self.save_file(save_revision=True))

        save_selected_snapshot_revision = QtGui.QAction('Add revision for selected objects', self)
        save_selected_snapshot_revision.triggered.connect(lambda: self.save_file(selected_objects=[True], save_revision=True, maya_checkin=True))

        # update_snapshot = QtGui.QAction('Update file only (without revision)', self)
        # update_snapshot.triggered.connect(lambda: self.save_file(update_snapshot=True))

        # update_selected_snapshot = QtGui.QAction('Update selected', self.savePushButton)
        # update_selected_snapshot.triggered.connect(lambda: self.prnt(0))

        # update_playblast = QtGui.QAction('Update Playblast', self.savePushButton)
        # update_playblast.triggered.connect(lambda: self.prnt(0))

        unlink_sobject = QtGui.QAction('Unlink', self)
        unlink_sobject.setIcon(gf.get_icon('link-variant-off', icons_set='mdi'))
        unlink_sobject.triggered.connect(self.unlink_sobject)

        delete_snapshot = QtGui.QAction('Delete', self)
        delete_snapshot.setIcon(gf.get_icon('remove'))
        delete_snapshot.triggered.connect(self.delete_sobject)

        delete_snapshot_tree = QtGui.QAction('Delete Whole Tree', self)
        delete_snapshot_tree.setIcon(gf.get_icon('remove'))
        delete_snapshot_tree.triggered.connect(self.delete_sobject_with_context)

        # Children items only menu
        ingest_files = QtGui.QAction('Ingest Files', self)
        ingest_files.setIcon(gf.get_icon('edit'))
        ingest_files.triggered.connect(self.ingest_files)

        # ingest_maya_textures = QtGui.QAction('Ingest Maya Textures', self)
        # ingest_maya_textures.setIcon(gf.get_icon('edit'))
        # ingest_maya_textures.triggered.connect(self.ingest_maya_textures)

        if multiple_selection:
            if mode == 'sobject':
                menu.addAction(edit_info_for_selected)
                menu.addSeparator()
                menu.addAction(delete_selected)
            if mode == 'snapshot':
                menu.addAction(edit_info_for_selected)
                menu.addSeparator()
                menu.addAction(delete_selected)
        else:
            if mode == 'sobject':
                if current_tree_widget_item.get_snapshot():

                    if env_mode.get_mode() == 'maya':
                        open_snapshot_additional = menu.addAction(open_scene, True)
                        open_snapshot_additional.clicked.connect(self.open_file_options)

                    elif env_mode.get_mode() == 'standalone':
                        open_snapshot_additional = menu.addAction(open_snapshot, True)
                        open_snapshot_additional.clicked.connect(self.open_file_options)

                if env_mode.get_mode() == 'maya':
                    save_scene_additional = menu.addAction(save_scene, True)
                    save_scene_additional.clicked.connect(self.save_file_options)

                    save_selected_snapshot_additional = menu.addAction(save_selected_snapshot, True)
                    save_selected_snapshot_additional.clicked.connect(self.export_selected_file_options)

                    menu.addSeparator()
                    save_snapshot_additional = menu.addAction(save_snapshot, True)
                    save_snapshot_additional.clicked.connect(self.save_file_options)

                elif env_mode.get_mode() == 'standalone':
                    save_snapshot_additional = menu.addAction(save_snapshot, True)
                    save_snapshot_additional.clicked.connect(self.save_file_options)

                if current_tree_widget_item.get_snapshot():

                    if env_mode.get_mode() == 'maya':
                        menu.addSeparator()
                        import_snapshot_additional = menu.addAction(import_snapshot, True)
                        import_snapshot_additional.clicked.connect(self.import_file_options)

                        refence_snapshot_additional = menu.addAction(reference_snapshot, True)
                        refence_snapshot_additional.clicked.connect(self.reference_file_options)

                    menu.addSeparator()

                    save_snapshot_revision_additional = menu.addAction(save_snapshot_revision, True)
                    save_snapshot_revision_additional.clicked.connect(self.save_file_options)

                    if env_mode.get_mode() == 'maya':
                        save_selected_snapshot_revision_additional = menu.addAction(save_selected_snapshot_revision, True)
                        save_selected_snapshot_revision_additional.clicked.connect(self.export_selected_file_options)

                    # update_snapshot_additional = menu.addAction(update_snapshot, True)
                    # update_snapshot_additional.clicked.connect(self.export_selected_file_options)
                    menu.addSeparator()

                # menu.addAction(update_selected_snapshot)
                # menu.addAction(update_playblast)

                menu.addSeparator()

                menu.addAction(open_folder_vls)
                menu.addAction(open_folder_v)

                menu.addSeparator()
                if current_tree_widget_item.have_watch_folder:
                    menu.addAction(open_folder_wf)
                    menu.addAction(edit_watch_folder)
                    menu.addAction(remove_watch_folder)
                else:
                    menu.addAction(create_watch_folder)

                menu.addSeparator()
                menu.addAction(copy_skey)
                menu.addAction(edit_info)

                if multiple_selection:
                    menu.addAction(edit_info_for_selected)

                if current_tree_widget_item.get_relationship() == 'instance':
                    menu.addSeparator()
                    menu.addAction(unlink_sobject)
                menu.addSeparator()
                menu.addAction(delete_sobject)
                if multiple_selection:
                    menu.addAction(delete_selected)

            if mode == 'snapshot':
                if current_tree_widget_item.get_snapshot():
                    if current_tree_widget_item.get_is_multiple_checkin():
                        open_snapshot_additional = menu.addAction(open_folder, True)
                        open_snapshot_additional.clicked.connect(self.open_file_options)
                    else:
                        if env_mode.get_mode() == 'maya':
                            open_snapshot_additional = menu.addAction(open_scene, True)
                            open_snapshot_additional.clicked.connect(self.open_file_options)
                        elif env_mode.get_mode() == 'standalone':
                            open_snapshot_additional = menu.addAction(open_snapshot, True)
                            open_snapshot_additional.clicked.connect(self.open_file_options)

                    if env_mode.get_mode() == 'maya':
                        save_scene_additional = menu.addAction(save_scene, True)
                        save_scene_additional.clicked.connect(self.save_file_options)

                        save_selected_snapshot_additional = menu.addAction(save_selected_snapshot, True)
                        save_selected_snapshot_additional.clicked.connect(self.export_selected_file_options)

                        menu.addSeparator()
                        save_snapshot_additional = menu.addAction(save_snapshot, True)
                        save_snapshot_additional.clicked.connect(self.save_file_options)

                        menu.addSeparator()

                        import_snapshot_additional = menu.addAction(import_snapshot, True)
                        import_snapshot_additional.clicked.connect(self.import_file_options)

                        refence_snapshot_additional = menu.addAction(reference_snapshot, True)
                        refence_snapshot_additional.clicked.connect(self.reference_file_options)
                    elif env_mode.get_mode() == 'standalone':
                        save_snapshot_additional = menu.addAction(save_snapshot, True)
                        save_snapshot_additional.clicked.connect(self.save_file_options)

                    menu.addSeparator()

                    save_snapshot_revision_additional = menu.addAction(save_snapshot_revision, True)
                    save_snapshot_revision_additional.clicked.connect(self.save_file_options)

                    if env_mode.get_mode() == 'maya':
                        save_selected_snapshot_revision_additional = menu.addAction(save_selected_snapshot_revision, True)
                        save_selected_snapshot_revision_additional.clicked.connect(self.export_selected_file_options)

                        menu.addSeparator()

                    # update_snapshot_additional = menu.addAction(update_snapshot, True)
                    # update_snapshot_additional.clicked.connect(self.export_selected_file_options)

                    menu.addSeparator()
                    menu.addAction(open_folder)
                    menu.addSeparator()
                    menu.addAction(copy_skey)
                    menu.addAction(edit_info)

                    if multiple_selection:
                        menu.addAction(edit_info_for_selected)

                    menu.addSeparator()
                    menu.addAction(delete_snapshot)
                    if current_tree_widget_item.is_versionless():
                        menu.addAction(delete_snapshot_tree)

                    if multiple_selection:
                        menu.addAction(delete_selected)

                else:
                    if env_mode.get_mode() == 'maya':
                        save_scene_additional = menu.addAction(save_scene, True)
                        save_scene_additional.clicked.connect(self.save_file_options)

                        save_selected_snapshot_additional = menu.addAction(save_selected_snapshot, True)
                        save_selected_snapshot_additional.clicked.connect(self.export_selected_file_options)

                    elif env_mode.get_mode() == 'standalone':
                        save_snapshot_additional = menu.addAction(save_snapshot, True)
                        save_snapshot_additional.clicked.connect(self.save_file_options)

                    menu.addSeparator()
                    menu.addAction(open_folder_vls)
                    menu.addAction(open_folder_v)
            if mode == 'process':
                if env_mode.get_mode() == 'maya':
                    save_scene_additional = menu.addAction(save_scene, True)
                    save_scene_additional.clicked.connect(self.save_file_options)
                    save_selected_snapshot_additional = menu.addAction(save_selected_snapshot, True)
                    save_selected_snapshot_additional.clicked.connect(self.export_selected_file_options)
                    menu.addSeparator()
                    save_snapshot_additional = menu.addAction(save_snapshot, True)
                    save_snapshot_additional.clicked.connect(self.save_file_options)
                elif env_mode.get_mode() == 'standalone':
                    save_snapshot_additional = menu.addAction(save_snapshot, True)
                    save_snapshot_additional.clicked.connect(self.save_file_options)

                if current_tree_widget_item.have_watch_folder:
                    menu.addSeparator()
                    menu.addAction(open_folder_wf)
                menu.addSeparator()
                menu.addAction(open_folder_vls)
                menu.addAction(open_folder_v)

                menu.addSeparator()
                menu.addAction(edit_db_table)

            if mode == 'child':
                menu.addAction(ingest_files)
                # menu.addAction(ingest_maya_textures)

        return menu

    @gf.catch_error
    def toggle_advanced_search_widget(self):
        if self.advanced_search_widget.isHidden():
            self.advanced_search_widget.setHidden(False)
        else:
            self.advanced_search_widget.setHidden(True)

    @gf.catch_error
    def toggle_description_box(self):
        if self.description_dock.isHidden():
            self.description_dock.setHidden(False)
            self.description_dock.raise_()
        else:
            self.description_dock.setHidden(True)

    @gf.catch_error
    def toggle_snapshot_browser_box(self):
        if self.snapshot_browser_dock.isHidden():
            self.snapshot_browser_dock.setHidden(False)
            self.snapshot_browser_dock.raise_()
        else:
            self.snapshot_browser_dock.setHidden(True)

    @gf.catch_error
    def toggle_drop_plate_box(self):
        if self.drop_plate_dock.isHidden():
            self.drop_plate_dock.setHidden(False)
            self.drop_plate_dock.raise_()
        else:
            self.drop_plate_dock.setHidden(True)

    @gf.catch_error
    def toggle_checkin_options_box(self):
        if self.checkin_options_dock.isHidden():
            self.checkin_options_dock.setHidden(False)
            self.checkin_options_dock.raise_()
        else:
            self.checkin_options_dock.setHidden(True)

    @gf.catch_error
    def toggle_fast_controls_box(self):
        if self.fast_controls_tool_bar.isHidden():
            self.fast_controls_tool_bar.setHidden(False)
            self.fast_controls_tool_bar.raise_()
        else:
            self.fast_controls_tool_bar.setHidden(True)

    @gf.catch_error
    def toggle_watch_folders_ui(self):
        watch_folders_ui = env_inst.get_watch_folder(self.project.get_code())

        if watch_folders_ui:
            if watch_folders_ui.isHidden():
                watch_folders_ui.setHidden(False)
                watch_folders_ui.show()
            else:
                watch_folders_ui.hide()

    @gf.catch_error
    def toggle_repo_sync_queue_ui(self):
        repo_sync_queue_ui = env_inst.ui_repo_sync_queue

        if repo_sync_queue_ui:
            if repo_sync_queue_ui.isHidden():
                repo_sync_queue_ui.setHidden(False)
                repo_sync_queue_ui.show()
            else:
                repo_sync_queue_ui.hide()

    @gf.catch_error
    def toggle_commit_queue_ui(self):
        commit_queue_ui = env_inst.get_commit_queue(self.project.get_code())

        if commit_queue_ui:
            if commit_queue_ui.isHidden():
                commit_queue_ui.setHidden(False)
                commit_queue_ui.show()
            else:
                commit_queue_ui.hide()

    @gf.catch_error
    def toggle_notes_dock(self):
        if self.notes_dock.isHidden():
            self.notes_dock.setHidden(False)
            self.notes_dock.raise_()
        else:
            self.notes_dock.setHidden(True)

    @gf.catch_error
    def toggle_tasks_dock(self):
        if self.tasks_dock.isHidden():
            self.tasks_dock.setHidden(False)
            self.tasks_dock.raise_()
        else:
            self.tasks_dock.setHidden(True)

    def fill_gear_menu(self):

        self.add_new_sobject_action = QtGui.QAction('Add new {0}'.format(self.stype.get_pretty_name()), self)
        self.add_new_sobject_action.triggered.connect(self.add_new_sobject)
        self.add_new_sobject_action.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1.2))

        self.sync_sobjects_action = QtGui.QAction('Sync {0}'.format(self.stype.get_pretty_name()), self)
        self.sync_sobjects_action.triggered.connect(self.create_sync_dialog)
        self.sync_sobjects_action.setIcon(gf.get_icon('cloud-sync', icons_set='mdi'))

        self.filter_process_action = QtGui.QAction('Filter Processes', self)
        self.filter_process_action.triggered.connect(self.create_process_tree_widget)
        self.filter_process_action.setIcon(gf.get_icon('filter'))

        self.find_opened_sobject_action = QtGui.QAction('Find Current Opened Search Object', self)
        self.find_opened_sobject_action.triggered.connect(self.create_process_tree_widget)
        self.find_opened_sobject_action.setIcon(gf.get_icon('magic'))

        self.search_options_toggle_action = QtGui.QAction('Advanced Search Dock', self)
        self.search_options_toggle_action.triggered.connect(self.toggle_advanced_search_widget)
        self.search_options_toggle_action.setIcon(gf.get_icon('search', scale_factor=0.95))

        self.description_toggle_action = QtGui.QAction('Description Dock', self)
        self.description_toggle_action.triggered.connect(self.toggle_description_box)
        self.description_toggle_action.setIcon(gf.get_icon('keyboard-o'))

        self.snapshot_browser_toggle_action = QtGui.QAction('Snapshot Browser Dock', self)
        self.snapshot_browser_toggle_action.triggered.connect(self.toggle_snapshot_browser_box)
        self.snapshot_browser_toggle_action.setIcon(gf.get_icon('sitemap'))

        self.checkin_options_toggle_action = QtGui.QAction('Checkin Options Dock', self)
        self.checkin_options_toggle_action.triggered.connect(self.toggle_checkin_options_box)
        self.checkin_options_toggle_action.setIcon(gf.get_icon('sliders'))

        self.drop_plate_toggle_action = QtGui.QAction('Drop Plate Dock', self)
        self.drop_plate_toggle_action.triggered.connect(self.toggle_drop_plate_box)
        self.drop_plate_toggle_action.setIcon(gf.get_icon('inbox'))

        self.notes_dock_toggle_action = QtGui.QAction('Notes Dock', self)
        self.notes_dock_toggle_action.triggered.connect(self.toggle_notes_dock)
        self.notes_dock_toggle_action.setIcon(gf.get_icon('inbox'))

        self.tasks_dock_toggle_action = QtGui.QAction('Tasks Dock', self)
        self.tasks_dock_toggle_action.triggered.connect(self.toggle_tasks_dock)
        self.tasks_dock_toggle_action.setIcon(gf.get_icon('inbox'))

        self.fast_controls_toggle_action = QtGui.QAction('Fast Controls Tool Bar', self)
        self.fast_controls_toggle_action.triggered.connect(self.toggle_fast_controls_box)
        self.fast_controls_toggle_action.setIcon(gf.get_icon('tachometer'))

        self.repo_sync_queue_toggle_action = QtGui.QAction('Repository Sync Queue Ui', self)
        self.repo_sync_queue_toggle_action.triggered.connect(self.toggle_repo_sync_queue_ui)
        self.repo_sync_queue_toggle_action.setIcon(gf.get_icon('tasks'))

        self.commit_queue_toggle_action = QtGui.QAction('Commit Queue Ui', self)
        self.commit_queue_toggle_action.triggered.connect(self.toggle_commit_queue_ui)
        self.commit_queue_toggle_action.setIcon(gf.get_icon('tasks'))

        self.watch_folder_toggle_action = QtGui.QAction('Watch Folders Ui', self)
        self.watch_folder_toggle_action.triggered.connect(self.toggle_watch_folders_ui)
        self.watch_folder_toggle_action.setIcon(gf.get_icon('eye'))

        self.search_widget.add_action_to_gear_menu(self.add_new_sobject_action)
        self.search_widget.add_action_to_gear_menu(self.sync_sobjects_action)
        if env_mode.get_mode() == 'maya':
            self.search_widget.add_action_to_gear_menu(self.find_opened_sobject_action)
        self.search_widget.add_action_to_gear_menu(self.search_options_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.description_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.snapshot_browser_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.checkin_options_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.drop_plate_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.notes_dock_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.tasks_dock_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.fast_controls_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.repo_sync_queue_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.commit_queue_toggle_action)
        self.search_widget.add_action_to_gear_menu(self.watch_folder_toggle_action)

    def fill_collapsable_toolbar(self):

        # self.naming_editor_button = QtGui.QToolButton()
        # self.naming_editor_button.setMaximumSize(22, 22)
        # self.naming_editor_button.setAutoRaise(True)
        # self.naming_editor_button.setIcon(gf.get_icon('list-ul'))
        # self.naming_editor_button.clicked.connect(self.create_naming_editor_widget)
        # self.naming_editor_button.setToolTip('Naming Editor for Current Search Type')

        # self.filter_process_button = QtGui.QToolButton()
        # self.filter_process_button.setAutoRaise(True)
        # self.filter_process_button.setIcon(gf.get_icon('filter'))
        # self.filter_process_button.clicked.connect(self.create_process_tree_widget)
        # self.filter_process_button.setToolTip('Filter current Tree of Processes and Child Search Types')

        self.toggle_advanced_search_button = QtGui.QToolButton()
        self.toggle_advanced_search_button.setAutoRaise(True)
        self.toggle_advanced_search_button.setIcon(gf.get_icon('magnify', icons_set='mdi', scale_factor=1.2))
        self.toggle_advanced_search_button.clicked.connect(self.toggle_advanced_search_widget)
        self.toggle_advanced_search_button.setToolTip('Toggle Advanced Search')

        self.add_new_sobject_button = QtGui.QToolButton()
        self.add_new_sobject_button.setAutoRaise(True)
        self.add_new_sobject_button.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1.2))
        self.add_new_sobject_button.clicked.connect(self.add_new_sobject)
        self.add_new_sobject_button.setToolTip('Add new {0}'.format(self.stype.get_pretty_name()))

        self.multiple_add_new_sobject_button = QtGui.QToolButton()
        self.multiple_add_new_sobject_button.setAutoRaise(True)
        self.multiple_add_new_sobject_button.setIcon(gf.get_icon('plus-circle-multiple-outline', icons_set='mdi', scale_factor=1.2))
        self.multiple_add_new_sobject_button.clicked.connect(self.add_new_sobject)
        self.multiple_add_new_sobject_button.setToolTip('Multiple Add new {0}'.format(self.stype.get_pretty_name()))

        self.ingest_files_to_stype_button = QtGui.QToolButton()
        self.ingest_files_to_stype_button.setAutoRaise(True)
        self.ingest_files_to_stype_button.setIcon(gf.get_icon('database-plus', icons_set='mdi', scale_factor=1.2))
        self.ingest_files_to_stype_button.clicked.connect(self.add_new_sobject)
        self.ingest_files_to_stype_button.setToolTip('Ingest Files to {0}'.format(self.stype.get_pretty_name()))

        # self.find_opened_sobject_button = QtGui.QToolButton()
        # self.find_opened_sobject_button.setAutoRaise(True)
        # self.find_opened_sobject_button.setIcon(gf.get_icon('auto-fix', icons_set='mdi', scale_factor=1.2))
        # self.find_opened_sobject_button.clicked.connect(self.find_opened_sobject)
        # self.find_opened_sobject_button.setToolTip('Find Current Opened Search Object')

        self.search_widget.add_widget_to_collapsable_toolbar(self.add_new_sobject_button)
        # self.search_widget.add_widget_to_collapsable_toolbar(self.multiple_add_new_sobject_button)
        # self.search_widget.add_widget_to_collapsable_toolbar(self.ingest_files_to_stype_button)
        # self.search_widget.add_widget_to_collapsable_toolbar(self.filter_process_button)
        self.search_widget.add_widget_to_collapsable_toolbar(self.toggle_advanced_search_button)
        # removed until naming editor created
        # self.search_widget.add_widget_to_collapsable_toolbar(self.naming_editor_button)

        # if env_mode.get_mode() == 'maya':
        #     self.search_widget.add_widget_to_collapsable_toolbar(self.find_opened_sobject_button)

    @gf.catch_error
    def find_opened_sobject(self):
        skey = mf.get_skey_from_scene()
        env_inst.ui_main.go_by_skey(skey, 'checkin')

    def get_current_results_widget(self):
        return self.search_widget.get_current_results_widget()

    # def refresh_current_snapshot_tree(self, item):
    #     self.search_widget.search_results_widget.update_item_tree(item)

    def get_current_item_paths(self):
        # TODO REWRITE THIS THING with multiple file in one snapshot in mind
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        file_path = None
        dir_path = None
        all_process = None

        # Will be deprecated
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

    @gf.catch_error
    def create_sync_dialog(self):
        sync_dialog = Ui_repoSyncDialog(parent=env_inst.ui_main, stype=self.stype, sobject=None)
        sync_dialog.exec_()

    @gf.catch_error
    def create_watch_folder(self):

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        watch_folders_ui = env_inst.watch_folders.get(self.project.get_code())
        watch_folders_ui.add_asset_to_watch(current_tree_widget_item)

    @gf.catch_error
    def edit_watch_folder(self):

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        watch_folders_ui = env_inst.watch_folders.get(self.project.get_code())
        watch_folders_ui.edit_aseet_watch(current_tree_widget_item)

    @gf.catch_error
    def delete_watch_folder(self):

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        watch_folders_ui = env_inst.watch_folders.get(self.project.get_code())
        watch_folders_ui.delete_aseet_from_watch(current_tree_widget_item)

    # Opening functions
    @gf.catch_error
    def open_file_options(self):
        file_path = self.get_current_item_paths()[0]
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        self.open_dialog = ui_maya_dialogs_classes.Ui_openOptionsWidget(file_path, current_tree_widget_item)
        self.open_dialog.show()

    @gf.catch_error
    def import_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.current_tree_item_widget

        if env_mode.get_mode() == 'maya':
            self.import_dialog = ui_maya_dialogs_classes.Ui_importOptionsWidget(file_path, nested_item)
            self.import_dialog.show()

    @gf.catch_error
    def reference_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.current_tree_item_widget

        if env_mode.get_mode() == 'maya':
            self.reference_dialog = ui_maya_dialogs_classes.Ui_referenceOptionsWidget(file_path, nested_item)
            self.reference_dialog.show()

    def get_repo_menu(self, watch_folder_dict):

        base_dirs = env_tactic.get_all_base_dirs()

        repo_menu = QtGui.QMenu()

        for key, val in base_dirs:
            if val['value'][4]:
                if val['value'][3] in watch_folder_dict['rep']:
                    repo_action = QtGui.QAction(val['value'][1], self)
                    color = val['value'][2]
                    repo_action.setIcon(gf.get_icon('square', color=Qt4Gui.QColor(color[0], color[1], color[2])))
                    abs_path = gf.form_path(u'{0}/{1}'.format(val['value'][0], watch_folder_dict['path']))
                    repo_action.triggered.connect(partial(gf.open_folder, abs_path, False))
                    repo_menu.addAction(repo_action)

        return repo_menu

    @gf.catch_error
    def open_file(self):
        if gf.get_value_from_config(cfg_controls.get_checkin(), 'checkoutMethodComboBox') == 0:
            checkout_method = 'local'
        else:
            checkout_method = 'http'

        if env_mode.get_mode() == 'maya':
            current_results_widget = self.get_current_results_widget()
            current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

            current_snapshot = current_tree_widget_item.get_snapshot()
            if checkout_method == 'http':
                connected = False
                for fl in current_snapshot.get_files_objects():

                    args_dict = {'item_widget': current_tree_widget_item}

                    args_dict['file_object'] = fl
                    repo_sync_widget = env_inst.ui_repo_sync_queue.schedule_file_object(fl)
                    if fl.get_type() in ['main', 'maya']:
                        if not connected:
                            repo_sync_widget.downloaded.connect(mf.open_scene)
                            connected = True
                    repo_sync_widget.download()

            elif checkout_method == 'local':

                for fl in current_snapshot.get_files_objects():
                    if fl.get_type() in ['main', 'maya']:
                        mf.open_scene(fl)
                        break
        else:
            current_results_widget = self.get_current_results_widget()
            current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

            current_snapshot = current_tree_widget_item.get_snapshot()

            if checkout_method == 'http':
                connected = False
                for fl in current_snapshot.get_files_objects():

                    repo_sync_widget = env_inst.ui_repo_sync_queue.schedule_file_object(fl)
                    if fl.get_type() in ['main', 'maya', 'image']:
                        if not connected:
                            repo_sync_widget.downloaded.connect(fl.open_file)
                            connected = True
                    repo_sync_widget.download()

            elif checkout_method == 'local':

                for fl in current_snapshot.get_files_objects():
                    if fl.get_type() not in ['web', 'icon']:
                        fl.open_file()
                        break

    @gf.catch_error
    def import_file(self):
        if gf.get_value_from_config(cfg_controls.get_checkin(), 'checkoutMethodComboBox') == 0:
            checkout_method = 'local'
        else:
            checkout_method = 'http'

        if env_mode.get_mode() == 'maya':
            current_results_widget = self.get_current_results_widget()
            current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

            current_snapshot = current_tree_widget_item.get_snapshot()
            if checkout_method == 'http':
                connected = False
                for fl in current_snapshot.get_files_objects():

                    args_dict = {'item_widget': current_tree_widget_item}

                    args_dict['file_object'] = fl
                    repo_sync_widget = env_inst.ui_repo_sync_queue.schedule_file_object(fl)
                    if fl.get_type() in ['main', 'maya']:
                        if not connected:
                            repo_sync_widget.downloaded.connect(mf.import_scene)
                            connected = True
                    repo_sync_widget.download()

            elif checkout_method == 'local':

                for fl in current_snapshot.get_files_objects():
                    if fl.get_type() in ['main', 'maya']:
                        mf.import_scene(fl)
                        break

    @gf.catch_error
    def reference_file(self):
        if gf.get_value_from_config(cfg_controls.get_checkin(), 'checkoutMethodComboBox') == 0:
            checkout_method = 'local'
        else:
            checkout_method = 'http'

        if env_mode.get_mode() == 'maya':
            current_results_widget = self.get_current_results_widget()
            current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

            current_snapshot = current_tree_widget_item.get_snapshot()
            if checkout_method == 'http':
                connected = False
                for fl in current_snapshot.get_files_objects():

                    # args_dict = {'item_widget': current_tree_widget_item}
                    #
                    # args_dict['file_object'] = fl
                    repo_sync_widget = env_inst.ui_repo_sync_queue.schedule_file_object(fl)
                    if fl.get_type() in ['main', 'maya']:
                        if not connected:
                            repo_sync_widget.downloaded.connect(mf.reference_scene)
                            connected = True
                    repo_sync_widget.download()

            elif checkout_method == 'local':

                for fl in current_snapshot.get_files_objects():
                    if fl.get_type() in ['main', 'maya']:
                        mf.reference_scene(fl)
                        break

    @gf.catch_error
    def open_folder(self, typ='versionless'):

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        item_type = current_tree_widget_item.get_type()

        base_dirs = env_tactic.get_all_base_dirs()
        active_repo = []
        for key, val in base_dirs:
            if val['value'][4]:
                active_repo.append(val['value'][3])

        if item_type == 'sobject':
            sobject = current_tree_widget_item.get_sobject()
            paths = tc.get_dirs_with_naming(sobject.get_search_key(), ['publish'])
            paths_dict = {
                'path': paths.get(typ)[0],
                'rep': active_repo,
            }

            repo_menu = self.get_repo_menu(paths_dict)
            if len(repo_menu.actions()) > 1:
                repo_menu.exec_(Qt4Gui.QCursor.pos())
            else:
                repo_menu.actions()[0].triggered.emit()
        elif item_type == 'process':
            sobject = current_tree_widget_item.get_sobject()
            paths = tc.get_dirs_with_naming(sobject.get_search_key(), [current_tree_widget_item.process])
            paths_dict = {
                'path': paths.get(typ)[0],
                'rep': active_repo,
            }

            repo_menu = self.get_repo_menu(paths_dict)
            if len(repo_menu.actions()) > 1:
                repo_menu.exec_(Qt4Gui.QCursor.pos())
            else:
                repo_menu.actions()[0].triggered.emit()

        elif item_type == 'snapshot':
            snapshot = current_tree_widget_item.get_snapshot()
            if snapshot:
                files = snapshot.get_files_objects()
                if files:
                    files[0].open_folder()
            else:
                sobject = current_tree_widget_item.get_sobject()
                paths = tc.get_dirs_with_naming(sobject.get_search_key(), [current_tree_widget_item.process])
                paths_dict = {
                    'path': paths.get(typ)[0],
                    'rep': active_repo,
                }

                repo_menu = self.get_repo_menu(paths_dict)
                if len(repo_menu.actions()) > 1:
                    repo_menu.exec_(Qt4Gui.QCursor.pos())
                else:
                    repo_menu.actions()[0].triggered.emit()

    @gf.catch_error
    def open_watch_folder(self):

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        if current_tree_widget_item.get_type() == 'sobject':
            repo_menu = self.get_repo_menu(current_tree_widget_item.get_watch_folder_dict())
            if len(repo_menu.actions()) > 1:
                repo_menu.exec_(Qt4Gui.QCursor.pos())
            else:
                repo_menu.actions()[0].triggered.emit()

    # Saving functions
    def checkin_file_objects(self, search_key, context, description, save_revision=False, snapshot_version=None,
                             create_icon=True, files_objects=None, checkin_type=None, keep_file_name=None,
                             commit_silently=False, run_before_checkin=None, run_after_checkin=None, single_threaded=False):

        if files_objects is None:
            files_objects = self.drop_plate_widget.get_selected_items()
        if checkin_type is None:
            checkin_type = self.fast_controls_tool_bar_widget.get_checkin_mode()
        if keep_file_name is None:
            keep_file_name = self.drop_plate_widget.get_keep_filename()
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = None
        if current_results_widget:
            current_tree_widget_item = current_results_widget.get_current_tree_widget_item()
        if files_objects:

            file_types = []
            file_names = []
            file_paths = []
            exts = []
            subfolders = []
            postfixes = []
            files_dict = None
            metadata = []
            # need to check if this is sequence
            padding = 4
            for item in files_objects:
                postfixes.append('')
                subfolders.append('')
                exts.append(item.get_file_ext())
                file_types.append(item.get_base_file_type())
                file_names.append(item.get_file_name(True))
                file_paths.append(item.get_all_files_list())
                metadata_dict = item.get_metadata()
                metadata_dict['name_part'] = item.get_name_part()
                metadata.append(metadata_dict)

            checkin_mode = gf.get_value_from_config(cfg_controls.get_checkin(), 'checkinMethodComboBox')

            mode = 'upload'

            if checkin_mode == 0:
                mode = 'preallocate'
            elif checkin_mode == 1:
                mode = 'inplace'
            elif checkin_mode == 2:
                mode = 'copy'
            elif checkin_mode == 3:
                mode = 'move'
            elif checkin_mode == 4:
                mode = 'upload'

            update_versionless = self.get_update_versionless()
            if keep_file_name:
                update_versionless = False
            explicit_filename = self.fast_controls_tool_bar_widget.get_explicit_filename()
            only_versionless = False

            return tc.checkin_file(
                search_key=search_key,
                context=context,
                description=description,
                version=snapshot_version,
                is_revision=save_revision,
                update_versionless=update_versionless,
                only_versionless=only_versionless,
                file_types=file_types,
                file_names=file_names,
                file_paths=file_paths,
                exts=exts,
                subfolders=subfolders,
                postfixes=postfixes,
                metadata=metadata,
                padding=padding,
                keep_file_name=keep_file_name,
                repo_name=self.get_current_repo(),
                mode=mode,
                create_icon=create_icon,
                ignore_keep_file_name=False,
                files_dict=files_dict,
                checkin_type=checkin_type,
                item_widget=current_tree_widget_item,
                files_objects=files_objects,
                explicit_filename=explicit_filename,
                commit_silently=commit_silently,
                run_before_checkin=run_before_checkin,
                run_after_checkin=run_after_checkin,
                single_threaded=single_threaded,
            )

    def checkin_from_maya(self, search_key, context, description, save_revision=False, snapshot_version=None,
                          selected_objects=None):

        ext_type = mf.get_current_scene_format()

        types = {
            'mayaBinary': 'mb',
            'mayaAscii': 'ma',
        }

        if selected_objects:
            if len(selected_objects) > 1:
                ext_type = selected_objects[1].keys()[0]
                types = selected_objects[1]
        else:
            selected_objects = [False]

        update_versionless = self.get_update_versionless()
        explicit_filename = self.fast_controls_tool_bar_widget.get_explicit_filename()
        ignore_keep_file_name = True
        if explicit_filename:
            ignore_keep_file_name = False
            update_versionless = False

        file_types = ['main', 'playblast']

        if explicit_filename:
            file_names = [explicit_filename, explicit_filename]
        else:
            file_names = ['scene', 'playblast']
        file_paths = ['', '']
        exts = [types[ext_type], 'jpg']
        subfolders = ['', '']
        postfixes = ['', '']

        checkin_mode = gf.get_value_from_config(cfg_controls.get_checkin(), 'checkinMethodComboBox')

        mode = 'upload'

        if checkin_mode == 0:
            mode = 'preallocate'
        elif checkin_mode == 1:
            mode = 'inplace'
        elif checkin_mode == 2:
            mode = 'copy'
        elif checkin_mode == 3:
            mode = 'move'
        elif checkin_mode == 4:
            mode = 'upload'

        match_template = gf.MatchTemplate(['$FILENAME.$EXT'])

        files_objects_dict = match_template.get_files_objects(['path/maya.{0}'.format(types[ext_type])])

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = None
        if current_results_widget:
            current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        return tc.checkin_file(
            search_key=search_key,
            context=context,
            description=description,
            version=snapshot_version,
            is_revision=save_revision,
            update_versionless=update_versionless,
            file_types=file_types,
            file_names=file_names,
            file_paths=file_paths,
            exts=exts,
            subfolders=subfolders,
            postfixes=postfixes,
            keep_file_name=False,
            repo_name=self.get_current_repo(),
            mode=mode,
            create_icon=True,
            # parent_wdg=self,
            ignore_keep_file_name=ignore_keep_file_name,
            item_widget=current_tree_widget_item,
            checkin_app='maya',
            selected_objects=selected_objects[0],
            ext_type=ext_type,
            setting_workspace=False,
            files_objects=files_objects_dict.get('file'),
            explicit_filename=explicit_filename,
        )

    @gf.catch_error
    def save_file_options(self):

        if env_mode.get_mode() == 'maya':
            mf.wrap_save_options(self.project.get_code(), 'checkin_out', self.stype.get_code())

    @gf.catch_error
    def export_selected_file_options(self):

        if env_mode.get_mode() == 'maya':
            mf.wrap_export_selected_options(self.project.get_code(), 'checkin_out', self.stype.get_code())

    def fast_save(self, **kargs):
        print 'SAVING FAST', kargs
        skey = mf.get_skey_from_scene()

        print skey
        if skey:
            skey_dict = tc.parce_skey(skey, True)

            saved = self.checkin_from_maya(
                search_key=skey_dict['search_key'],
                context=skey_dict['context'],
                description=None,
                # save_revision=False,
                # snapshot_version=None,
                # selected_objects=False,
            )

            if saved:
                print 'ALL GOOD ;)'

    def save_revision_confirm(self, save_revision, selected_objects):

        confirm_revison = self.checkin_options_widget.checkinPageWidget.askReplaceRevisionCheckBox.isChecked()

        if save_revision and confirm_revison:
            buttons = (
                ('Replace', QtGui.QMessageBox.YesRole),
                ('Cancel', QtGui.QMessageBox.NoRole),
                ('Do not show again', QtGui.QMessageBox.RejectRole))
            if selected_objects:
                replace_result = gf.show_message_predefined(
                    'Files will be replaced!',
                    '<br>Attention! The file you are working on now will be <b>REPLACED</b> with this selected objects only.</br>'
                    '<br>Other work (objects) you have made in this file will disappear!</br>'
                    '<br>If you do not want this use "Save selected objects" command instead.</br>',
                    buttons=buttons,
                    parent=self)
            else:
                replace_result = gf.show_message_predefined(
                    'Files will be replaced!',
                    '<br>Attention! The file saved to this version will be <b>REPLACED</b> with new one.</br>'
                    '<br>Earlier file you have saved before will disappear!</br>'
                    '<br>If you do not want this use "Save selected" command instead.</br>',
                    buttons=buttons,
                    parent=self)
        else:
            return True

        if replace_result == QtGui.QMessageBox.ButtonRole.YesRole:
            return True
        if replace_result == QtGui.QMessageBox.ButtonRole.RejectRole:
            self.checkin_options_widget.checkinPageWidget.askReplaceRevisionCheckBox.setChecked(False)
            return True

    @gf.catch_error
    def save_file(self, selected_objects=None, save_revision=False, maya_checkin=False):

        commit_queue = env_inst.get_commit_queue(self.project.get_code())
        commit_queue.show()

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        current_snapshot_version = None
        if current_tree_widget_item.type == 'snapshot' and save_revision:
            snapshot = current_tree_widget_item.get_snapshot()
            if snapshot:
                current_snapshot_version = snapshot.info.get('version')
                if current_snapshot_version in [-1, 0]:
                    current_snapshot_version = None

        if current_tree_widget_item and self.save_revision_confirm(save_revision, selected_objects):

            search_key = current_tree_widget_item.get_skey(parent=True)
            context = current_tree_widget_item.get_context(True, self.fast_controls_tool_bar_widget.get_context()).replace(' ', '_')

            description = self.description_widget.get_description('plain')
            group_checkin = self.drop_plate_widget.groupCheckinCheckBox.isChecked()

            if env_mode.get_mode() == 'maya':
                if maya_checkin:
                    self.checkin_from_maya(
                        search_key=search_key,
                        context=context,
                        description=description,
                        save_revision=save_revision,
                        snapshot_version=current_snapshot_version,
                        selected_objects=selected_objects,
                    )
                elif not self.drop_plate_widget.get_selected_items():
                    def run_after_exec():
                        self.save_file(
                            selected_objects=selected_objects,
                            save_revision=save_revision,
                        )
                    self.drop_plate_widget.add_files_from_menu(exec_after_added=run_after_exec)
                else:
                    if group_checkin:
                        self.checkin_file_objects(
                            search_key=search_key,
                            context=context,
                            description=description,
                            save_revision=save_revision,
                            snapshot_version=current_snapshot_version,
                        )
                    else:
                        for file_object in self.drop_plate_widget.get_selected_items():
                            self.checkin_file_objects(
                                search_key=search_key,
                                context=context,
                                description=description,
                                save_revision=save_revision,
                                snapshot_version=current_snapshot_version,
                                files_objects=[file_object],
                            )

                        self.drop_plate_widget.remove_selected_items()

            if env_mode.get_mode() == 'standalone':
                if not self.drop_plate_widget.get_selected_items():
                    def run_after_exec():
                        self.save_file(
                            selected_objects=selected_objects,
                            save_revision=save_revision,
                        )
                    self.drop_plate_widget.add_files_from_menu(exec_after_added=run_after_exec)

                if group_checkin:
                    self.checkin_file_objects(
                        search_key=search_key,
                        context=context,
                        description=description,
                        save_revision=save_revision,
                        snapshot_version=current_snapshot_version,
                    )
                else:
                    for file_object in self.drop_plate_widget.get_selected_items():
                        self.checkin_file_objects(
                            search_key=search_key,
                            context=context,
                            description=description,
                            save_revision=save_revision,
                            snapshot_version=current_snapshot_version,
                            files_objects=[file_object],
                        )

                    self.drop_plate_widget.remove_selected_items()

    def refresh_results(self):
        self.description_widget.set_item(None)
        self.columns_viewer_widget.set_item(None)
        self.fast_controls_tool_bar_widget.set_item(None)

        self.refresh_current_results()

    def get_update_versionless(self):

        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = None
        if current_results_widget:
            current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        if not current_tree_widget_item:
            return True
        elif current_tree_widget_item.get_checkin_mode_options() in ['multi_file', 'dir', 'sequence']:
            return False
        else:
            return self.checkin_options_widget.checkinPageWidget.updateVersionlessCheckBox.isChecked()

    def get_current_repo(self):
        current_idx = self.checkin_options_widget.checkinPageWidget.repositoryComboBox.currentIndex()
        return self.checkin_options_widget.checkinPageWidget.repositoryComboBox.itemData(current_idx, QtCore.Qt.UserRole)

    @gf.catch_error
    def copy_search_key(self):
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()
        print current_tree_widget_item.get_skey(skey=True)
        clipboard = QtGui.QApplication.instance().clipboard()
        clipboard.setText(current_tree_widget_item.get_skey(skey=True))

    @gf.catch_error
    def add_new_sobject(self):
        """
        Open window for adding new sobject
        """
        add_sobject = ui_addsobject_classes.Ui_addTacticSobjectWidget(stype=self.stype, parent=self)

        dl.log('Adding new SObject to {}'.format(self.stype.get_pretty_name()), group_id=self.stype.get_code())

        runtime_command = 'thenv.env_inst.get_check_tree("{0}", "{1}", "{2}").add_new_sobject()'.format(
            self.project.get_code(), 'checkin_out', self.stype.get_code())
        dl.info(runtime_command, group_id=self.stype.get_code())

        add_sobject.show()

        return add_sobject

    @gf.catch_error
    def delete_selected_sobjects(self):
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()
        current_tree_widget = current_tree_widget_item.get_current_tree_widget()

        sobjects_list = []
        search_keys_list = []
        for item in current_tree_widget.selectedItems():
            item_wdg = current_tree_widget.itemWidget(item, 0)
            sobject = item_wdg.get_deletable_sobject()

            sobjects_list.append(sobject)
            search_keys_list.append(sobject.get_search_key())

        del_confirm = tc.sobject_delete_confirm(sobjects_list)

        if del_confirm:
            tc.delete_sobjects(search_keys_list, del_confirm)
            self.refresh_current_results()

    @gf.catch_error
    def unlink_sobject(self):
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        current_tree_widget_item.unlink_current_sobject()

        self.refresh_current_results()

    @gf.catch_error
    def delete_sobject_with_context(self):
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        versionless_sobject = current_tree_widget_item.get_deletable_sobject()
        versions_sobjects = current_tree_widget_item.get_all_versions_snapshots()

        sobjects_list = []
        search_keys_list = []
        for version_sobject in versions_sobjects.values():
            sobjects_list.append(version_sobject)
            search_keys_list.append(version_sobject.get_search_key())

        sobjects_list.append(versionless_sobject)
        search_keys_list.append(versionless_sobject.get_search_key())

        del_confirm = tc.sobject_delete_confirm(sobjects_list)

        if del_confirm:
            tc.delete_sobjects(search_keys_list, del_confirm)
            self.refresh_current_results()

    @gf.catch_error
    def delete_sobject(self):
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        deleted = current_tree_widget_item.delete_current_sobject()

        if deleted:
            self.refresh_current_results()

    @gf.catch_error
    def edit_existing_sobject(self):
        """
        Open window for Editing sobject
        """
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        stype = current_tree_widget_item.stype

        self.edit_sobject = ui_addsobject_classes.Ui_addTacticSobjectWidget(
            stype=stype,
            parent_stype=self.stype,
            item=current_tree_widget_item,
            view='edit',
            parent=self,
        )
        self.edit_sobject.setWindowTitle(u'Editing info for {0}'.format(current_tree_widget_item.sobject.info.get('name')))
        self.edit_sobject.show()

    @gf.catch_error
    def edit_db_table(self):
        """
        Open window for Editing Database Table, for mass Edits
        """
        current_results_widget = self.get_current_results_widget()
        current_tree_widget_item = current_results_widget.get_current_tree_widget_item()

        stype = current_tree_widget_item.stype

        edit_db_table = ui_addsobject_classes.Ui_editDBTableWidget(
            stype=stype,
            parent_stype=self.stype,
            item=current_tree_widget_item,
            view='edit',
            parent=self,
        )
        edit_db_table.setWindowTitle(u'Editing Database Table for {0}'.format(current_tree_widget_item.sobject.info.get('name')))
        edit_db_table.show()

    @gf.catch_error
    def ingest_files(self):
        print 'CREATING IGEST WINDOW'

    def ingest_maya_textures(self):
        print 'CREATING IGEST WINDOW'

    def open_item_menu(self, item_widget):
        if item_widget:
            menu = self.checkin_context_menu(False, mode=item_widget.get_type())
            if menu:
                menu.exec_(Qt4Gui.QCursor.pos())

    def set_settings_from_dict(self, settings_dict=None, apply_checkin_options=True, apply_search_options=True):
        self.do_creating_ui()
        self.is_showed = True

        if not settings_dict:
            settings_dict = {}

        if apply_search_options:
            self.search_widget.set_settings_from_dict(settings_dict.get('search_widget'))
        self.drop_plate_widget.set_settings_from_dict(settings_dict.get('drop_plate_dock'))
        self.snapshot_browser_widget.set_settings_from_dict(settings_dict.get('snapshot_browser_dock'))
        if apply_checkin_options:
            self.checkin_options_widget.set_settings_from_dict(settings_dict.get('checkin_options_dock'))

        self.advanced_search_widget.set_settings_from_dict(settings_dict.get('advanced_search_widget'))

        QtGui.QApplication.processEvents()

        self.restoreState(QtCore.QByteArray.fromHex(str(settings_dict.get('main_state'))))

    def get_settings_dict(self, force=False):

        if force and not self.is_created:
            self.do_creating_ui()
        elif not self.is_created:
            return None

        settings_dict = {
            'search_widget': self.search_widget.get_settings_dict(),
            'drop_plate_dock': self.drop_plate_widget.get_settings_dict(),
            'snapshot_browser_dock': self.snapshot_browser_widget.get_settings_dict(),
            'advanced_search_widget': self.advanced_search_widget.get_settings_dict(),
            'checkin_options_dock': self.checkin_options_widget.get_settings_dict(),
            'main_state': str(self.saveState().toHex()),
        }
        return settings_dict

    def readSettings(self):

        tab_name = self.objectName().split('/')
        group_path = 'ui_search/{0}/{1}/{2}'.format(
            self.project.info['type'],
            self.project.get_code(),
            tab_name[1]
        )
        self.set_settings_from_dict(
            env_read_config(
                filename='ui_checkin_out',
                unique_id=group_path,
                long_abs_path=True
            )
        )

    def writeSettings(self):

        group_path = 'ui_search/{0}/{1}/{2}'.format(
            self.project.info['type'],
            self.project.get_code(),
            self.stype.get_code().split('/')[1]
        )

        env_write_config(
            self.get_settings_dict(),
            filename='ui_checkin_out',
            unique_id=group_path,
            long_abs_path=True
        )

    def closeEvent(self, event):
        if self.is_showed:
            self.writeSettings()

            # closing search_widget
            self.search_widget.close()

            # empty instanced widgets, This is very important for Maya
            env_inst.set_check_tree(
                self.project.get_code(), 'checkin_out_instanced_widgets', 'drop_plate_dock', None)
            env_inst.set_check_tree(
                self.project.get_code(), 'checkin_out_instanced_widgets', 'checkin_options_dock', None)
            env_inst.set_check_tree(
                self.project.get_code(), 'checkin_out_instanced_widgets', 'notes_dock', None)
            env_inst.set_check_tree(
                self.project.get_code(), 'checkin_out_instanced_widgets', 'tasks_dock', None)

            self.close()
            self.deleteLater()

        event.accept()

    def showEvent(self, event):
        event.accept()

        self.do_creating_ui()

        if not self.is_showed:
            self.is_showed = True
            self.readSettings()

    def hideEvent(self, event):
        event.accept()

    def paintEvent(self, event):
        event.accept()

        self.sync_instanced_widgets()
