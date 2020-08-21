# file ui_snapshot_browser_classes.py
# Snaphsot file manager Widget

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.side.six as six
#import thlib.ui.misc.ui_snapshot_browser as ui_snapshot_browser
from thlib.ui_classes.ui_custom_qwidgets import Ui_horizontalCollapsableWidget, StyledToolButton
import thlib.ui_classes.ui_addsobject_classes as addsobject_widget
from thlib.environment import env_inst, env_mode, cfg_controls
import thlib.global_functions as gf
import thlib.tactic_classes as tc

#reload(ui_snapshot_browser)


class Ui_snapshotBrowserWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.scene = QtGui.QGraphicsScene(self)
        self.shown = False
        self.scene_created = False
        self.downloading_in_progress = False

        self.item_widget = None
        self.snapshots = None

        self.create_ui()

        self.controls_actions()

        self.installEventFilter(self)

    def create_ui_raw(self):

        self.snapshotBrowserLayout = QtGui.QVBoxLayout(self)
        self.snapshotBrowserLayout.setSpacing(0)
        self.snapshotBrowserLayout.setContentsMargins(0, 0, 0, 0)
        self.snapshotBrowserLayout.setObjectName("snapshotBrowserLayout")

        self.create_toolbar()

        self.browserSplitter = QtGui.QSplitter(self)
        self.browserSplitter.setOrientation(QtCore.Qt.Vertical)
        self.browserSplitter.setObjectName("browserSplitter")
        self.verticalLayoutWidget = QtGui.QWidget(self.browserSplitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayoutWidget.setContentsMargins(0, 0, 0, 0)

        self.imageViewerLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.imageViewerLayout.setSpacing(0)
        self.imageViewerLayout.setContentsMargins(0, 0, 0, 0)
        self.imageViewerLayout.setObjectName("imageViewerLayout")

        self.previewGraphicsView = QtGui.QGraphicsView(self.verticalLayoutWidget)
        self.previewGraphicsView.setFrameShape(QtGui.QFrame.NoFrame)
        self.previewGraphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewGraphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.previewGraphicsView.setRenderHints(
            Qt4Gui.QPainter.Antialiasing | Qt4Gui.QPainter.HighQualityAntialiasing | Qt4Gui.QPainter.SmoothPixmapTransform | Qt4Gui.QPainter.TextAntialiasing)
        self.previewGraphicsView.setOptimizationFlags(
            QtGui.QGraphicsView.DontAdjustForAntialiasing | QtGui.QGraphicsView.DontSavePainterState | QtGui.QGraphicsView.IndirectPainting)
        self.previewGraphicsView.setViewportUpdateMode(QtGui.QGraphicsView.BoundingRectViewportUpdate)
        self.previewGraphicsView.setObjectName("previewGraphicsView")
        self.imageViewerLayout.addWidget(self.previewGraphicsView)
        self.imageViewerLayout.setStretch(1, 1)

        self.imagesSlider = QtGui.QSlider(self.verticalLayoutWidget)
        self.imagesSlider.setStyleSheet("QSlider::groove:horizontal {\n"
                                        "    border: 0px solid rgb(96, 96, 96);\n"
                                        "    height: 8px;\n"
                                        "    background: rgb(72,72,72);\n"
                                        "    margin: 0px;\n"
                                        "}\n"
                                        "\n"
                                        "QSlider::handle:horizontal {\n"
                                        "    background: rgb(96,96,96);\n"
                                        "    border: 0px;\n"
                                        "    width: 18px;\n"
                                        "    margin: 0px 0;\n"
                                        "    border-radius: 4px;\n"
                                        "    width: 40px;\n"
                                        "}")
        self.imagesSlider.setMaximum(1)
        self.imagesSlider.setPageStep(1)
        self.imagesSlider.setTracking(True)
        self.imagesSlider.setOrientation(QtCore.Qt.Horizontal)
        self.imagesSlider.setTickPosition(QtGui.QSlider.TicksAbove)
        self.imagesSlider.setObjectName("imagesSlider")
        self.imagesSlider.setMaximumHeight(12)
        self.imageViewerLayout.addWidget(self.imagesSlider)

        self.gridLayoutWidget = QtGui.QWidget(self.browserSplitter)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.filesBrowserLayout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.filesBrowserLayout.setContentsMargins(0, 0, 0, 0)
        self.filesBrowserLayout.setObjectName("filesBrowserLayout")

        self.showAllCheckBox = QtGui.QCheckBox(self.gridLayoutWidget)
        # self.showAllCheckBox.setObjectName("showAllCheckBox")
        self.filesBrowserLayout.addWidget(self.showAllCheckBox, 1, 0, 1, 1)
        self.showAllCheckBox.setHidden(True)

        self.showMoreInfoCheckBox = QtGui.QCheckBox(self.gridLayoutWidget)
        # self.showMoreInfoCheckBox.setObjectName("showMoreInfoCheckBox")
        self.filesBrowserLayout.addWidget(self.showMoreInfoCheckBox, 1, 1, 1, 1)
        self.showMoreInfoCheckBox.setHidden(True)

        self.filesTreeWidget = QtGui.QTreeWidget(self.gridLayoutWidget)
        self.filesTreeWidget.setStyleSheet("QTreeView::item {\n"
                                           "    padding: 2px;\n"
                                           "}\n"
                                           "QTreeView::item:selected:active{\n"
                                           "    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
                                           "    border: 1px solid transparent;\n"
                                           "}\n"
                                           "QTreeView::item:selected:!active {\n"
                                           "    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(82, 133, 166, 255), stop:1 rgba(82, 133, 166, 255));\n"
                                           "    border: 1px solid transparent;\n"
                                           "}\n"
                                           "")
        self.filesTreeWidget.setAlternatingRowColors(True)
        self.filesTreeWidget.setHeaderHidden(True)
        self.filesTreeWidget.setObjectName("filesTreeWidget")
        self.filesTreeWidget.headerItem().setText(0, "Snapshot / Type / Name:")

        self.filesBrowserLayout.addWidget(self.filesTreeWidget, 0, 0, 1, 2)

        self.snapshotBrowserLayout.addWidget(self.browserSplitter)

        # self.showAllCheckBox.setText(u"Show All Files")
        # self.showMoreInfoCheckBox.setText(u"Show More Info")

        self.filesTreeWidget.headerItem().setText(1, u"Size:")
        self.filesTreeWidget.headerItem().setText(2, u"Path:")
        self.filesTreeWidget.headerItem().setText(3, u"Repo:")
        self.filesTreeWidget.headerItem().setText(4, u"Base Type:")

    def create_toolbar(self):

        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.setSpacing(0)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.settings_button = StyledToolButton(size='small')
        self.settings_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.settings_button.setArrowType(QtCore.Qt.NoArrow)
        self.settings_button.setIcon(gf.get_icon('settings', icons_set='mdi'))
        self.settings_button.setToolTip('Config Snapshot Browser')


        self.show_all_action = QtGui.QAction(u"Show All Files", self)
        self.show_all_action.triggered.connect(lambda: self.toggle_files_view('all'))
        self.show_all_action.setIcon(gf.get_icon('playlist-check', icons_set='mdi', scale_factor=1.3))

        self.show_more_action = QtGui.QAction(u"Show More Info", self)
        self.show_more_action.triggered.connect(lambda: self.toggle_files_view('more'))
        self.show_more_action.setIcon(gf.get_icon('playlist-plus', icons_set='mdi', scale_factor=1.3))

        self.horizontal_orientation_action = QtGui.QAction(u"Horizontal orientation", self)
        self.horizontal_orientation_action.triggered.connect(lambda: self.switch_splitter_layout('horizontal'))
        self.horizontal_orientation_action.setIcon(gf.get_icon('view-sequential', icons_set='mdi', scale_factor=1))

        self.vertical_orientation_action = QtGui.QAction(u"Vertical orientation", self)
        self.vertical_orientation_action.triggered.connect(lambda: self.switch_splitter_layout('vertical'))
        self.vertical_orientation_action.setIcon(gf.get_icon('view-parallel', icons_set='mdi', scale_factor=1))

        self.settings_button.addAction(self.show_all_action)
        self.settings_button.addAction(self.show_more_action)
        self.settings_button.addAction(self.horizontal_orientation_action)
        self.settings_button.addAction(self.vertical_orientation_action)

        self.refresh_button = StyledToolButton(size='small')
        self.refresh_button.setAutoRaise(True)
        self.refresh_button.setIcon(gf.get_icon('refresh', icons_set='mdi', scale_factor=1.3))
        self.refresh_button.setToolTip('Refresh Current Tasks')

        buttons_layout.addWidget(self.settings_button)
        buttons_layout.addWidget(self.refresh_button)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        buttons_layout.addItem(spacerItem)
        buttons_layout.setStretch(3, 1)

        self.snapshotBrowserLayout.addLayout(buttons_layout)

    def switch_splitter_layout(self, orientation):

        if orientation == 'vertical':
            self.browserSplitter.setOrientation(QtCore.Qt.Horizontal)
        elif orientation == 'horizontal':
            self.browserSplitter.setOrientation(QtCore.Qt.Vertical)

    def toggle_files_view(self, view):

        if view == 'all':
            self.showAllCheckBox.toggle()
        elif view == 'more':
            self.showMoreInfoCheckBox.toggle()

    def controls_actions(self):

        self.showMoreInfoCheckBox.toggled.connect(self.fill_files_tree)
        self.showAllCheckBox.toggled.connect(self.fill_files_tree)

        self.create_files_tree_context_menu()
        self.create_graphics_view_context_menu()

        self.back_button.clicked.connect(self.move_slider_backward)
        self.forward_button.clicked.connect(self.move_slider_forward)
        self.previewGraphicsView.mouseDoubleClickEvent = self.previewGraphicsView_doubleClickEvent
        self.filesTreeWidget.doubleClicked.connect(self.open_file_from_tree)

    def customize_ui(self):

        self.filesTreeWidget.setStyleSheet(gf.get_qtreeview_style())

    def create_files_tree_context_menu(self):
        self.filesTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.filesTreeWidget.customContextMenuRequested.connect(self.open_menu)

    def create_graphics_view_context_menu(self):
        self.previewGraphicsView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self.menu_actions = []

        open_external = QtGui.QAction('Open File', self.previewGraphicsView)
        open_external.setIcon(gf.get_icon('folder'))
        open_external.triggered.connect(self.open_file_from_graphics_view)

        open_file_folder = QtGui.QAction('Show Folder', self.previewGraphicsView)
        open_file_folder.setIcon(gf.get_icon('folder-open'))
        open_file_folder.triggered.connect(self.open_folder_from_graphics_view)

        copy_path = QtGui.QAction('Copy File Path', self.previewGraphicsView)
        copy_path.setIcon(gf.get_icon('copy'))
        copy_path.triggered.connect(self.copy_path_from_graphics_view)

        copy_web_path = QtGui.QAction('Copy Web Link', self.previewGraphicsView)
        copy_web_path.setIcon(gf.get_icon('link', icons_set='mdi', scale_factor=1))
        copy_web_path.triggered.connect(self.copy_web_path_from_graphics_view)

        copy_to_clipboard = QtGui.QAction('Copy To Clipboard', self.previewGraphicsView)
        copy_to_clipboard.setIcon(gf.get_icon('link', icons_set='mdi', scale_factor=1))
        copy_to_clipboard.triggered.connect(self.copy_to_clipboard_from_graphics_view)

        previews_maya = QtGui.QAction('', self.previewGraphicsView)
        previews_maya.setSeparator(True)

        add_imageplane = QtGui.QAction('Add as Imageplane', self.previewGraphicsView)
        add_imageplane.triggered.connect(lambda: self.add_as_image_plane(self.imagesSlider.value()))

        previews_sep = QtGui.QAction('', self.previewGraphicsView)
        previews_sep.setSeparator(True)

        add_new_image = QtGui.QAction('Add new Image', self.previewGraphicsView)
        add_new_image.triggered.connect(lambda: self.open_ext(self.imagesSlider.value()))

        add_new_playblast = QtGui.QAction('Capture new playblast', self.previewGraphicsView)
        add_new_playblast.triggered.connect(lambda: self.open_ext(self.imagesSlider.value()))

        self.menu_actions.append(open_external)
        self.menu_actions.append(open_file_folder)
        self.menu_actions.append(copy_path)
        self.menu_actions.append(copy_web_path)
        self.menu_actions.append(copy_to_clipboard)
        self.menu_actions.append(previews_maya)
        # self.menu_actions.append(add_imageplane)
        # self.menu_actions.append(previews_sep)
        # self.menu_actions.append(add_new_image)
        # self.menu_actions.append(add_new_playblast)

        self.previewGraphicsView.addActions(self.menu_actions)

    def previewGraphicsView_doubleClickEvent(self, event):
        self.open_file_from_graphics_view()

    def previewGraphicsView_wheelEvent(self, event):
        event.accept()
        if event.delta() < 0:
            self.move_slider_forward()
        else:
            self.move_slider_backward()

    def create_preview_widget(self):

        self.pm1 = None
        self.pm2 = None
        self.pm3 = None

        self.previewGraphicsView.setScene(self.scene)
        self.previewGraphicsView.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        self.create_on_scene_layout()

        self.previewGraphicsView.wheelEvent = self.previewGraphicsView_wheelEvent
        self.back_button.enterEvent = self.back_button_enter_event
        self.back_button.leaveEvent = self.back_button_leave_event
        self.back_button.wheelEvent = self.previewGraphicsView_wheelEvent
        self.forward_button.enterEvent = self.forward_button_enter_event
        self.forward_button.leaveEvent = self.forward_button_leave_event
        self.forward_button.wheelEvent = self.previewGraphicsView_wheelEvent

        self.current_pix = 0
        self.pix_list = []
        self.file_list = []
        self.pm_list = []

    def back_button_enter_event(self, event):
        self.back_button_hover_animation.start()
        event.accept()

    def back_button_leave_event(self, event):
        self.back_button_leave_animation.setStartValue(self.back_button_opacity_effect.opacity())
        self.back_button_leave_animation.start()
        event.accept()

    def forward_button_enter_event(self, event):
        self.forward_button_hover_animation.start()
        event.accept()

    def forward_button_leave_event(self, event):
        self.forward_button_leave_animation.setStartValue(self.forward_button_opacity_effect.opacity())
        self.forward_button_leave_animation.start()
        event.accept()

    def open_menu(self):
        item = self.filesTreeWidget.currentItem()
        if item:
            if item.data(0, QtCore.Qt.UserRole):
                menu = self.file_context_menu()
                if menu:
                    menu.exec_(Qt4Gui.QCursor.pos())

    @gf.catch_error
    def open_file_from_graphics_view(self):
        if self.file_list:

            if gf.get_value_from_config(cfg_controls.get_checkin(), 'checkoutMethodComboBox') == 0:
                checkout_method = 'local'
            else:
                checkout_method = 'http'

            file_object = self.file_list[self.current_pix]

            if checkout_method == 'http':
                repo_sync_widget = env_inst.ui_repo_sync_queue.schedule_file_object(file_object)

                # preventing double opening of the file
                connected = False
                if not connected:
                    repo_sync_widget.downloaded.connect(file_object.open_file)
                    connected = True
                repo_sync_widget.download()

            elif checkout_method == 'local':
                file_object.open_file()

    @gf.catch_error
    def open_folder_from_graphics_view(self):
        if self.file_list:
            file_object = self.file_list[self.current_pix]
            if file_object.is_meta_file_obj():
                meta_file_object = file_object.get_meta_file_object()
                meta_file_object.open_folder()
            else:
                file_object.open_folder()

    @gf.catch_error
    def copy_path_from_graphics_view(self):
        if self.file_list:
            clipboard = QtGui.QApplication.instance().clipboard()
            file_object = self.file_list[self.current_pix]
            if file_object.is_meta_file_obj():
                meta_file_object = file_object.get_meta_file_object()
                clipboard.setText(meta_file_object.get_all_files_list(True))
            else:
                clipboard.setText(file_object.get_full_abs_path())

    @gf.catch_error
    def copy_web_path_from_graphics_view(self):
        if self.file_list:
            clipboard = QtGui.QApplication.instance().clipboard()
            file_object = self.file_list[self.current_pix]
            clipboard.setText(file_object.get_full_web_path())

    @gf.catch_error
    def copy_to_clipboard_from_graphics_view(self):
        if self.file_list:
            clipboard = QtGui.QApplication.instance().clipboard()
            file_object = self.file_list[self.current_pix]

            image = Qt4Gui.QImage(0, 0, Qt4Gui.QImage.Format_ARGB32)
            image.load(file_object.get_full_abs_path())

            if not image.isNull():
                clipboard.setImage(image)

    @gf.catch_error
    def open_file_from_tree(self, index=None):

        if gf.get_value_from_config(cfg_controls.get_checkin(), 'checkoutMethodComboBox') == 0:
            checkout_method = 'local'
        else:
            checkout_method = 'http'

        item = self.filesTreeWidget.currentItem()
        file_object = item.data(0, QtCore.Qt.UserRole)

        if checkout_method == 'http':
            repo_sync_widget = env_inst.ui_repo_sync_queue.schedule_file_object(file_object)

            # preventing double opening of the file
            connected = False
            if not connected:
                repo_sync_widget.downloaded.connect(file_object.open_file)
                connected = True
            repo_sync_widget.download()

        elif checkout_method == 'local':
            file_object.open_file()

    @gf.catch_error
    def open_folder_from_tree(self):
        item = self.filesTreeWidget.currentItem()
        file_object = item.data(0, QtCore.Qt.UserRole)
        if file_object.is_meta_file_obj():
            meta_file_object = file_object.get_meta_file_object()
            meta_file_object.open_folder()
        else:
            file_object.open_folder()

    def copy_path_from_tree(self):
        item = self.filesTreeWidget.currentItem()
        file_object = item.data(0, QtCore.Qt.UserRole)

        clipboard = QtGui.QApplication.instance().clipboard()
        clipboard.setText(file_object.get_full_abs_path())

    def copy_web_path_from_tree(self):
        item = self.filesTreeWidget.currentItem()
        file_object = item.data(0, QtCore.Qt.UserRole)

        clipboard = QtGui.QApplication.instance().clipboard()
        clipboard.setText(file_object.get_full_web_path())

    def copy_to_clipboard_from_tree(self):
        item = self.filesTreeWidget.currentItem()
        file_object = item.data(0, QtCore.Qt.UserRole)

        clipboard = QtGui.QApplication.instance().clipboard()

        image = Qt4Gui.QImage(0, 0, Qt4Gui.QImage.Format_ARGB32)
        image.load(file_object.get_full_abs_path())

        if not image.isNull():
            clipboard.setImage(image)

    def file_context_menu(self):
        open_file = QtGui.QAction('Open File', self.filesTreeWidget)
        open_file.setIcon(gf.get_icon('folder'))
        open_file.triggered.connect(lambda: self.open_file_from_tree(self.filesTreeWidget.currentIndex()))

        open_file_folder = QtGui.QAction('Show Folder', self.filesTreeWidget)
        open_file_folder.setIcon(gf.get_icon('folder-open'))
        open_file_folder.triggered.connect(self.open_folder_from_tree)

        copy_path = QtGui.QAction('Copy File Path', self.filesTreeWidget)
        copy_path.setIcon(gf.get_icon('copy'))
        copy_path.triggered.connect(self.copy_path_from_tree)

        copy_web_path = QtGui.QAction('Copy Web Link', self.filesTreeWidget)
        copy_web_path.setIcon(gf.get_icon('link', icons_set='mdi', scale_factor=1))
        copy_web_path.triggered.connect(self.copy_web_path_from_tree)

        copy_to_clipboard = QtGui.QAction('Copy to Clipboard', self.filesTreeWidget)
        copy_to_clipboard.setIcon(gf.get_icon('link', icons_set='mdi', scale_factor=1))
        copy_to_clipboard.triggered.connect(self.copy_to_clipboard_from_tree)

        edit_info = QtGui.QAction('Edit Info', self.filesTreeWidget)
        edit_info.setIcon(gf.get_icon('edit'))
        edit_info.triggered.connect(self.edit_file_sobject)

        delete_sobject = QtGui.QAction('Delete', self.filesTreeWidget)
        delete_sobject.setIcon(gf.get_icon('remove'))
        delete_sobject.triggered.connect(self.delete_file_sobject)

        menu = QtGui.QMenu()

        menu.addAction(open_file)
        menu.addAction(open_file_folder)
        menu.addAction(copy_path)
        menu.addAction(copy_web_path)
        menu.addAction(copy_to_clipboard)
        menu.addAction(edit_info)
        menu.addAction(delete_sobject)

        return menu

    def edit_file_sobject(self):

        item = self.filesTreeWidget.currentItem()

        file_object = item.data(0, QtCore.Qt.UserRole)

        stype = self.item_widget.stype
        self.edit_sobject = addsobject_widget.Ui_addTacticSobjectWidget(
            stype=stype,
            item=self.item_widget,
            view='edit',
            search_key=file_object.get_search_key(),
            parent=self
        )
        self.edit_sobject.setWindowTitle('Editing info for {0}'.format(self.item_widget.sobject.info.get('name')))
        self.edit_sobject.show()

    def delete_file_sobject(self):

        # TODO Refresh after deleting

        item = self.filesTreeWidget.currentItem()

        file_object = item.data(0, QtCore.Qt.UserRole)

        delete_confirm = tc.sobject_delete_confirm([file_object])

        if delete_confirm:
            tc.delete_sobjects([file_object.get_search_key()], delete_confirm)

    def init_snapshot(self, multiple_sapshots=False):
        if multiple_sapshots:
            snapshots = list(self.snapshots.values())
        else:
            snapshots = [self.snapshots]

        self.snapshots = snapshots

    @staticmethod
    def check_file_object_exists(file_object):

        # TODO This should be more complicated, and check hash not just size
        # TODO Warning if file did not match local-remote
        exists = file_object.is_exists()
        match = file_object.get_file_size() == file_object.get_file_size(True)

        return exists, match, file_object

    def check_file_object_threaded(self, file_object):

        worker = env_inst.local_pool.add_task(self.check_file_object_exists, file_object)
        worker.result.connect(self.process_checked_file)
        worker.error.connect(gf.error_handle)
        worker.start()

    def process_checked_file(self, args=None):
        exists = args[0]
        match = args[1]
        file_object = args[2]

        if exists:
            if not match:
                self.download_web_preview(file_object)
        else:
            self.download_web_preview(file_object)

    def fill_files_tree(self):
        self.filesTreeWidget.clear()

        show_more_info = self.showMoreInfoCheckBox.isChecked()
        show_all_files = self.showAllCheckBox.isChecked()

        if not show_more_info:
            self.filesTreeWidget.setHeaderHidden(True)
            self.filesTreeWidget.setColumnCount(1)
        else:
            self.filesTreeWidget.setHeaderHidden(False)
            self.filesTreeWidget.setColumnCount(5)

        icon_provider = QtGui.QFileIconProvider()
        known_icon_ext = {}
        if self.snapshots:

            # Making versionless on top of tree
            if self.item_widget.type == 'snapshot':
                if self.item_widget.is_versionless():
                    versionless_snapshot = self.item_widget.get_snapshot()
                    if versionless_snapshot and versionless_snapshot not in self.snapshots:
                        self.snapshots.insert(0, versionless_snapshot)

            for snapshot in self.snapshots:
                snapshot_info = snapshot.get_snapshot()
                snapshot_files_objects = snapshot.get_files_objects(group_by='type')

                if show_all_files:
                    sn_item = QtGui.QTreeWidgetItem()
                    sn_item.setText(0, 'Snapshot ({0}), Version: {1}'.format(snapshot_info.get('id'), snapshot_info.get('version')))
                    self.filesTreeWidget.addTopLevelItem(sn_item)
                    sn_item.setExpanded(True)

                # Download from http
                for file_type, files_objects in snapshot_files_objects.items():
                    for file_object in files_objects:

                        if gf.get_value_from_config(cfg_controls.get_checkin(), 'getPreviewsThroughHttpCheckbox') == 1:
                            if file_type in ['icon', 'playblast', 'web', 'image']:
                                self.check_file_object_threaded(file_object)

                preview = []
                if not show_all_files:
                    preview = ['icon', 'playblast', 'web']

                # Adding files to tree
                for i, (file_type, files_objects) in enumerate(snapshot_files_objects.items()):
                    type_item = QtGui.QTreeWidgetItem()
                    if file_type not in preview:
                        if show_all_files:
                            type_item.setText(0, file_type)
                            sn_item.addChild(type_item)
                            type_item.setExpanded(True)

                        for file_object in files_objects:

                            # removing unnecessary calls to icon provider
                            file_ext = file_object.get_ext()
                            if known_icon_ext.get(file_ext):
                                file_icon = known_icon_ext[file_ext]
                            else:
                                file_icon = icon_provider.icon(file_object.get_full_abs_path())
                                known_icon_ext[file_ext] = file_icon

                            # multiple files in snapshot
                            if file_object.is_meta_file_obj():
                                self.add_item_with_meta_file_object(file_object, show_more_info, show_all_files, snapshot_info, type_item, file_icon)
                            else:
                                self.add_item_with_tactic_file_object(file_object, show_more_info, show_all_files, snapshot_info, type_item, file_icon)

            self.filesTreeWidget.resizeColumnToContents(0)
            if show_more_info:
                self.filesTreeWidget.resizeColumnToContents(1)
                self.filesTreeWidget.resizeColumnToContents(2)
                self.filesTreeWidget.resizeColumnToContents(4)
                self.filesTreeWidget.resizeColumnToContents(5)

    def add_item_with_meta_file_object(self, file_object, show_more_info, show_all_files, snapshot_info, type_item, file_icon):

        meta_file_object = file_object.get_meta_file_object()
        child_item = QtGui.QTreeWidgetItem()
        file_name = file_object.get_filename_with_ext()

        def set_name(**kwargs):
            if not kwargs['result']:
                kwargs['file_name'] += ' (File Offline)'
            kwargs['child_item'].setText(0, kwargs['file_name'])

        worker = env_inst.local_pool.add_task(meta_file_object.is_exists)
        worker.result.connect(lambda result=None, child_item=child_item, file_name=file_name:
                              set_name(result=result, child_item=child_item, file_name=file_name))
        worker.error.connect(gf.error_handle)
        worker.start()

        child_item.setData(0, QtCore.Qt.UserRole, file_object)
        if show_more_info:
            child_item.setText(1, gf.sizes(file_object.get_file_size()))
            child_item.setText(2, file_object.get_abs_path())
            child_item.setText(3, snapshot_info.get('repo'))
            child_item.setText(4, file_object.get_base_type())
        if show_all_files:
            type_item.addChild(child_item)
        else:
            self.filesTreeWidget.addTopLevelItem(child_item)

        child_item.setIcon(0, file_icon)
        if len(meta_file_object.get_all_files_list()) > 1:
            # if this is meta with sequence or udims etc...
            for meta_file_name in meta_file_object.get_all_files_list(filenames=True):
                sub_child_item = QtGui.QTreeWidgetItem()
                child_item.addChild(sub_child_item)
                sub_child_item.setText(0, meta_file_name)
                sub_child_item.setData(0, QtCore.Qt.UserRole, file_object)
                sub_child_item.setIcon(0, file_icon)

        child_item.setExpanded(True)

    def add_item_with_tactic_file_object(self, file_object, show_more_info, show_all_files, snapshot_info, type_item, file_icon):
        child_item = QtGui.QTreeWidgetItem()
        file_name = file_object.get_filename_with_ext()

        def set_name(**kwargs):
            if not kwargs['result']:
                kwargs['file_name'] += ' (File Offline)'
            kwargs['child_item'].setText(0, kwargs['file_name'])

        worker = env_inst.local_pool.add_task(file_object.is_exists)
        worker.result.connect(lambda result=None, child_item=child_item, file_name=file_name:
                              set_name(result=result, child_item=child_item, file_name=file_name))
        worker.error.connect(gf.error_handle)
        worker.start()

        child_item.setText(0, file_name)
        child_item.setData(0, QtCore.Qt.UserRole, file_object)
        if show_more_info:
            child_item.setText(1, gf.sizes(file_object.get_file_size()))
            child_item.setText(2, file_object.get_abs_path())
            child_item.setText(3, snapshot_info.get('repo'))
            child_item.setText(4, file_object.get_base_type())
        if show_all_files:
            type_item.addChild(child_item)
        else:
            self.filesTreeWidget.addTopLevelItem(child_item)
        child_item.setIcon(0, file_icon)
        child_item.setExpanded(True)

    def init_images_slider(self):
        self.imagesSlider.setValue(0)
        if self.pix_list:
            self.imagesSlider.setMaximum(len(self.pix_list)-1)
        else:
            self.imagesSlider.setMaximum(0)

        self.imagesSlider.valueChanged.connect(self.emi_dec)
        self.imagesSlider.valueChanged.connect(self.emi_inc)

    def getting_pixmaps(self):

        for snapshot in self.snapshots:

            preview_files_objects = snapshot.get_previewable_files_objects()

            if not preview_files_objects:
                # Trying to gen any preview if possible
                for fo in snapshot.get_files_objects():
                    if fo.get_type() == 'web':
                        if fo not in preview_files_objects:
                            preview_files_objects.append(fo)

            for preview_file_obj in preview_files_objects:

                web_file_obj = preview_file_obj.get_web_preview()

                if not web_file_obj:
                    web_file_obj = preview_file_obj
                if web_file_obj.is_meta_file_obj():
                    meta_file_object = web_file_obj.get_meta_file_object()
                    pixmap_path = meta_file_object.get_all_files_list(first=True)
                else:
                    pixmap_path = web_file_obj.get_full_abs_path()

                self.pix_list.append(pixmap_path)
                self.file_list.append(preview_file_obj)

    def download_web_preview(self, file_object):
        self.downloading_in_progress = True

        if not file_object.is_downloaded():
            if file_object.get_unique_id() not in list(env_inst.ui_repo_sync_queue.queue_dict.keys()):
                repo_sync_widget = env_inst.ui_repo_sync_queue.schedule_file_object(file_object)
                repo_sync_widget.downloaded.connect(self.download_ready)
                repo_sync_widget.download()

    def download_ready(self, file_obj=None):

        self.downloading_in_progress = False

        env_inst.ui_main.set_info_status_text('')
        file_obj.set_downloaded()
        if env_inst.ui_repo_sync_queue.is_all_downloads_done():
            self.refresh_with_item_widget(self.item_widget)

    def create_on_scene_layout(self):
        self.previewGraphicsView_layout = QtGui.QGridLayout(self.previewGraphicsView)
        self.previewGraphicsView_layout.setContentsMargins(0, 0, 0, 0)
        self.previewGraphicsView_layout.setSpacing(0)
        self.back_button = QtGui.QPushButton('')
        self.back_button_opacity_effect = QtGui.QGraphicsOpacityEffect()
        self.back_button_opacity_effect.setOpacity(0)
        self.back_button.setGraphicsEffect(self.back_button_opacity_effect)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.back_button.setSizePolicy(sizePolicy)
        self.back_button.setIcon(gf.get_icon('chevron-left'))
        self.back_button.setStyleSheet('QPushButton {background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 64), stop:1 rgba(0, 0, 0, 0)); border-style: none; outline: none; border-width: 0px;}')

        self.back_button_hover_animation = QtCore.QPropertyAnimation(self.back_button_opacity_effect, QtCore.QByteArray(b'opacity'), self)
        self.back_button_hover_animation.setDuration(200)
        self.back_button_hover_animation.setEasingCurve(QtCore.QEasingCurve.InSine)
        self.back_button_hover_animation.setStartValue(0)
        self.back_button_hover_animation.setEndValue(1)

        self.back_button_leave_animation = QtCore.QPropertyAnimation(self.back_button_opacity_effect, QtCore.QByteArray(b'opacity'), self)
        self.back_button_leave_animation.setDuration(200)
        self.back_button_leave_animation.setEasingCurve(QtCore.QEasingCurve.OutSine)
        self.back_button_leave_animation.setEndValue(0)

        # forward button
        self.forward_button = QtGui.QPushButton('')
        self.forward_button_opacity_effect = QtGui.QGraphicsOpacityEffect(self)
        self.forward_button_opacity_effect.setOpacity(0)
        self.forward_button.setGraphicsEffect(self.forward_button_opacity_effect)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.forward_button.setSizePolicy(sizePolicy)
        self.forward_button.setIcon(gf.get_icon('chevron-right'))
        self.forward_button.setStyleSheet('QPushButton {background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(0, 0, 0, 64)); border-style: none; outline: none; border-width: 0px;}')

        self.forward_button_hover_animation = QtCore.QPropertyAnimation(self.forward_button_opacity_effect, QtCore.QByteArray(b'opacity'), self)
        self.forward_button_hover_animation.setDuration(200)
        self.forward_button_hover_animation.setEasingCurve(QtCore.QEasingCurve.InSine)
        self.forward_button_hover_animation.setStartValue(0)
        self.forward_button_hover_animation.setEndValue(1)

        self.forward_button_leave_animation = QtCore.QPropertyAnimation(self.forward_button_opacity_effect, QtCore.QByteArray(b'opacity'), self)
        self.forward_button_leave_animation.setDuration(200)
        self.forward_button_leave_animation.setEasingCurve(QtCore.QEasingCurve.OutSine)
        self.forward_button_leave_animation.setEndValue(0)

        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.previewGraphicsView_layout.addWidget(self.forward_button, 0, 2, 1, 1)
        self.previewGraphicsView_layout.addWidget(self.back_button, 0, 0, 1, 1)
        self.previewGraphicsView_layout.addItem(spacerItem, 0, 1, 1, 1)
        self.previewGraphicsView_layout.setColumnStretch(0, 1)
        self.previewGraphicsView_layout.setColumnStretch(1, 1)
        self.previewGraphicsView_layout.setColumnStretch(2, 1)

    def clear_scene(self):
        if self.scene_created:
            self.pm1.add_pixmap(Qt4Gui.QPixmap())
            self.pm2.add_pixmap(Qt4Gui.QPixmap())
            self.pm3.add_pixmap(Qt4Gui.QPixmap())

    def load_file(self, file_path):

        qfile = QtCore.QFile(file_path)
        qfile.open(QtCore.QIODevice.ReadOnly)
        data = qfile.readAll()
        return data

    def get_files_data_list(self):
        self.pm_list = [self.pm1, self.pm2, self.pm3]
        paths_list = []
        if self.pix_list:
            for i, pm in enumerate(self.pm_list):
                paths_list.append(self.pix_list[i % len(self.pix_list)])

        data_list = []
        for path in paths_list:
            data_list.append(self.load_file(path))

        return data_list

    def initial_prepare_pixmaps_threaded(self):

        worker = env_inst.local_pool.add_task(self.get_files_data_list)
        worker.result.connect(self.initial_prepare_scene)
        worker.error.connect(gf.error_handle)
        worker.start()

    def initial_prepare_scene(self, data_list):

        for data, pm in zip(data_list, self.pm_list):
            pixmap = Qt4Gui.QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                pm.add_pixmap(pixmap.scaledToWidth(640, QtCore.Qt.SmoothTransformation))

        self.previewGraphicsView.setSceneRect(self.pm1.pixmap_item.boundingRect())
        self.previewGraphicsView.fitInView(self.pm1.pixmap_item.boundingRect(), QtCore.Qt.KeepAspectRatio)

    def prepare_pixmaps_threaded(self):

        if self.pix_list and not self.downloading_in_progress:

            worker = env_inst.local_pool.add_task(self.get_files_data_list)
            worker.result.connect(self.do_update_scene)
            worker.error.connect(gf.error_handle)
            worker.start()

    def do_update_scene(self, data_list):

        self.clear_scene()

        for data, pm in zip(data_list, self.pm_list):
            pixmap = Qt4Gui.QPixmap()
            pixmap.loadFromData(data)
            if pixmap.isNull():
                pm.set_op(0.0)
            else:
                pm.add_pixmap(pixmap.scaledToWidth(640, QtCore.Qt.SmoothTransformation))

        self.pm1.set_op(1.0)
        self.previewGraphicsView.setSceneRect(self.pm1.pixmap_item.boundingRect())
        self.previewGraphicsView.fitInView(self.pm1.pixmap_item.boundingRect(), QtCore.Qt.KeepAspectRatio)

        self.imagesSlider.setValue(0)

    def update_scene(self):

        self.prepare_pixmaps_threaded()

        # if self.pix_list and not self.downloading_in_progress:
        #
        #     self.clear_scene()
        #
        #     self.pm_list = [self.pm1, self.pm2, self.pm3]
        #
        #     for i, pm in enumerate(self.pm_list):
        #         s = gf.time_it()
        #         pixmap = Qt4Gui.QPixmap(self.pix_list[i % len(self.pix_list)])
        #         gf.time_it(s, 'UPDATE SCENE PIXMAPS')
        #         if pixmap.isNull():
        #             pm.set_op(0.0)
        #         else:
        #             pm.add_pixmap(pixmap.scaledToWidth(640, QtCore.Qt.SmoothTransformation))
        #
        #     self.pm1.set_op(1.0)
        #     self.previewGraphicsView.setSceneRect(self.pm1.pixmap_item.boundingRect())
        #     self.previewGraphicsView.fitInView(self.pm1.pixmap_item.boundingRect(), QtCore.Qt.KeepAspectRatio)
        #
        #     self.imagesSlider.setValue(0)

        if not self.machine.isRunning():
            self.machine.start()

    def create_scene(self):
        self.scene_created = True

        self.pm1 = Pixmap(self)
        self.pm2 = Pixmap(self)
        self.pm3 = Pixmap(self)

        self.scene.addItem(self.pm1.pixmap_item)
        self.scene.addItem(self.pm2.pixmap_item)
        self.scene.addItem(self.pm3.pixmap_item)

        # animation
        self.machine = QtCore.QStateMachine()
        self.state1 = QtCore.QState()
        self.state2 = QtCore.QState()
        self.state3 = QtCore.QState()

        self.state1.assignProperty(self.pm1, 'pos', QtCore.QPoint(0, 0))
        self.state1.assignProperty(self.pm1, 'opacity', 1)

        self.state2.assignProperty(self.pm1, 'pos', QtCore.QPoint(-255, 0))
        self.state2.assignProperty(self.pm1, 'opacity', 0)

        self.state3.assignProperty(self.pm1, 'pos', QtCore.QPoint(255, 0))
        self.state3.assignProperty(self.pm1, 'opacity', 0)

        self.state1.assignProperty(self.pm2, 'pos', QtCore.QPoint(255, 0))
        self.state1.assignProperty(self.pm2, 'opacity', 0)

        self.state2.assignProperty(self.pm2, 'pos', QtCore.QPoint(0, 0))
        self.state2.assignProperty(self.pm2, 'opacity', 1)

        self.state3.assignProperty(self.pm2, 'pos', QtCore.QPoint(-255, 0))
        self.state3.assignProperty(self.pm2, 'opacity', 0)

        self.state1.assignProperty(self.pm3, 'pos', QtCore.QPoint(-255, 0))
        self.state1.assignProperty(self.pm3, 'opacity', 0)

        self.state2.assignProperty(self.pm3, 'pos', QtCore.QPoint(255, 0))
        self.state2.assignProperty(self.pm3, 'opacity', 0)

        self.state3.assignProperty(self.pm3, 'pos', QtCore.QPoint(0, 0))
        self.state3.assignProperty(self.pm3, 'opacity', 1)

        self.pm1_anm = QtCore.QPropertyAnimation(self.pm1, b'pos', self)
        self.pm1_anm.setEasingCurve(QtCore.QEasingCurve.OutExpo)
        self.pm1_anm.setDuration(300)

        self.pm1_anm_o = QtCore.QPropertyAnimation(self.pm1, b'opacity', self)
        self.pm1_anm_o.setEasingCurve(QtCore.QEasingCurve.OutExpo)
        self.pm1_anm_o.setDuration(200)

        self.pm2_anm = QtCore.QPropertyAnimation(self.pm2, b'pos', self)
        self.pm2_anm.setEasingCurve(QtCore.QEasingCurve.OutExpo)
        self.pm2_anm.setDuration(300)

        self.pm2_anm_o = QtCore.QPropertyAnimation(self.pm2, b'opacity', self)
        self.pm2_anm_o.setEasingCurve(QtCore.QEasingCurve.OutExpo)
        self.pm2_anm_o.setDuration(200)

        self.pm3_anm = QtCore.QPropertyAnimation(self.pm3, b'pos', self)
        self.pm3_anm.setEasingCurve(QtCore.QEasingCurve.OutExpo)
        self.pm3_anm.setDuration(300)

        self.pm3_anm_o = QtCore.QPropertyAnimation(self.pm3, b'opacity', self)
        self.pm3_anm_o.setEasingCurve(QtCore.QEasingCurve.OutExpo)
        self.pm3_anm_o.setDuration(200)

        self.t4 = self.state1.addTransition(self.value_decreased, self.state3)
        self.t4.addAnimation(self.pm1_anm)
        self.t4.addAnimation(self.pm1_anm_o)
        self.t4.addAnimation(self.pm2_anm)
        self.t4.addAnimation(self.pm2_anm_o)
        self.t4.addAnimation(self.pm3_anm)
        self.t4.addAnimation(self.pm3_anm_o)

        self.t5 = self.state2.addTransition(self.value_decreased, self.state1)
        self.t5.addAnimation(self.pm1_anm)
        self.t5.addAnimation(self.pm1_anm_o)
        self.t5.addAnimation(self.pm2_anm)
        self.t5.addAnimation(self.pm2_anm_o)
        self.t5.addAnimation(self.pm3_anm)
        self.t5.addAnimation(self.pm3_anm_o)

        self.t6 = self.state3.addTransition(self.value_decreased, self.state2)
        self.t6.addAnimation(self.pm1_anm)
        self.t6.addAnimation(self.pm1_anm_o)
        self.t6.addAnimation(self.pm2_anm)
        self.t6.addAnimation(self.pm2_anm_o)
        self.t6.addAnimation(self.pm3_anm)
        self.t6.addAnimation(self.pm3_anm_o)

        self.t1 = self.state1.addTransition(self.value_increased, self.state2)
        self.t1.addAnimation(self.pm1_anm)
        self.t1.addAnimation(self.pm1_anm_o)
        self.t1.addAnimation(self.pm2_anm)
        self.t1.addAnimation(self.pm2_anm_o)
        self.t1.addAnimation(self.pm3_anm)
        self.t1.addAnimation(self.pm3_anm_o)

        self.t2 = self.state2.addTransition(self.value_increased, self.state3)
        self.t2.addAnimation(self.pm1_anm)
        self.t2.addAnimation(self.pm1_anm_o)
        self.t2.addAnimation(self.pm2_anm)
        self.t2.addAnimation(self.pm2_anm_o)
        self.t2.addAnimation(self.pm3_anm)
        self.t2.addAnimation(self.pm3_anm_o)

        self.t3 = self.state3.addTransition(self.value_increased, self.state1)
        self.t3.addAnimation(self.pm1_anm)
        self.t3.addAnimation(self.pm1_anm_o)
        self.t3.addAnimation(self.pm2_anm)
        self.t3.addAnimation(self.pm2_anm_o)
        self.t3.addAnimation(self.pm3_anm)
        self.t3.addAnimation(self.pm3_anm_o)

        # initial fill
        if self.pix_list:
            self.initial_prepare_pixmaps_threaded()

        self.imagesSlider.setValue(0)

        if not self.machine.isRunning():
            self.machine.addState(self.state1)
            self.machine.addState(self.state2)
            self.machine.addState(self.state3)
            self.machine.setInitialState(self.state1)
            self.machine.start()

    def create_ui(self):
        self.create_ui_raw()

        self.create_preview_widget()

        self.customize_ui()

    @QtCore.Signal
    def value_increased(self, int):
        return int

    def emi_inc(self, int):
        if self.current_pix < int:
            self.value_increased.emit()
            self.current_pix += 1
            self.rotate_pixmaps(self.current_pix)

    @QtCore.Signal
    def value_decreased(self, int):
        return int

    def emi_dec(self, int):
        if self.current_pix > int:
            self.value_decreased.emit()
            self.current_pix -= 1
            self.rotate_pixmaps(self.current_pix)

    # rotating
    def rotate_pixmaps(self, index=None):

        if self.pix_list and self.pm_list:

            idx = index % len(self.pix_list)
            pm_idx = index % len(self.pm_list)

            pixmap = Qt4Gui.QPixmap(self.pix_list[idx])

            if not pixmap.isNull():
                self.pm_list[pm_idx].add_pixmap(pixmap.scaledToWidth(640, QtCore.Qt.SmoothTransformation))

            self.previewGraphicsView.setSceneRect(self.pm_list[pm_idx].pixmap_item.boundingRect())
            self.previewGraphicsView.fitInView(self.pm_list[pm_idx].pixmap_item.boundingRect(), QtCore.Qt.KeepAspectRatio)

    def move_slider_forward(self):
        value = self.imagesSlider.value() + 1
        self.imagesSlider.setValue(value)

    def move_slider_backward(self):
        value = self.imagesSlider.value() - 1
        self.imagesSlider.setValue(value)

    def do_preview(self):
        self.pm_list = []
        self.pix_list = []
        self.file_list = []
        self.downloading_in_progress = False

        self.getting_pixmaps()
        self.init_images_slider()

        if self.pix_list:
            if self.scene_created:
                self.update_scene()
            else:
                self.create_scene()
        else:
            self.clear_scene()

    def set_item_widget(self, item_widget):
        self.item_widget = item_widget

        if self.visibleRegion().isEmpty():
            self.shown = False
        else:
            self.refresh_with_item_widget(self.item_widget)

    def refresh_with_item_widget(self, item_widget):
        # Refer to paint event to see where refreshing is
        self.shown = True

        if self.item_widget.type == 'snapshot':
            is_versionless = self.item_widget.is_versionless()
            if is_versionless:
                self.snapshots = self.item_widget.get_all_versions_snapshots()
                if not self.snapshots:
                    self.snapshots = self.item_widget.get_snapshot()
                    is_versionless = False
            else:
                self.snapshots = self.item_widget.get_snapshot()

            if self.snapshots:
                if is_versionless:
                    self.init_snapshot(True)
                else:
                    self.init_snapshot(False)
                self.previewGraphicsView.resizeEvent = self.graphicsSceneResizeEvent
                self.fill_files_tree()
                self.do_preview()
            else:
                self.clear()
        elif self.item_widget.type == 'sobject':

            # checking if we have any snapshots, we can show it in snapshot browser
            # versionless here have priority
            # getting any possible snapshot for Item widget
            snapshots = self.item_widget.get_all_snapshots()
            self.snapshots = None

            if snapshots.get('publish'):
                self.snapshots = self.item_widget.get_snapshots('publish')
            elif snapshots.get('icon'):
                self.snapshots = self.item_widget.get_snapshots('icon')
            else:
                processes = self.item_widget.get_all_snapshots()
                if processes:
                    process = list(processes.keys())[0]
                    if process:
                        self.snapshots = self.item_widget.get_snapshots(process)

            if self.snapshots:
                self.init_snapshot(True)
                self.previewGraphicsView.resizeEvent = self.graphicsSceneResizeEvent
                self.fill_files_tree()
                self.do_preview()
            else:
                self.clear()
        elif self.item_widget.type == 'process':

            self.snapshots = []
            snapshots = self.item_widget.get_snapshots()
            if snapshots:
                for snapshot in snapshots:
                    if snapshot:
                        for sn in snapshot.values():
                            self.snapshots.append(sn)
            else:
                snapshots = self.item_widget.get_snapshots(versionless=False)
                if snapshots:
                    for snapshot in snapshots:
                        if snapshot:
                            for sn in snapshot.values():
                                self.snapshots.append(sn)

            if self.snapshots:
                self.previewGraphicsView.resizeEvent = self.graphicsSceneResizeEvent
                self.fill_files_tree()
                self.do_preview()
            else:
                self.clear()
        else:
            self.clear()

    def clear(self):
        self.clear_scene()

        self.pix_list = []
        self.file_list = []
        self.filesTreeWidget.clear()

        self.previewGraphicsView.resizeEvent = self.resize_event
        self.imagesSlider.setMaximum(0)
        self.imagesSlider.setMinimum(0)

    def set_settings_from_dict(self, settings_dict=None):

        ref_settings_dict = {
            'showAllCheckBox': False,
            'showMoreInfoCheckBox': False,
            'browserSplitter': None,
        }

        settings = gf.check_config(ref_settings_dict, settings_dict)

        self.showAllCheckBox.setChecked(settings['showAllCheckBox'])
        self.showMoreInfoCheckBox.setChecked(settings['showMoreInfoCheckBox'])
        if settings['browserSplitter']:
            self.browserSplitter.restoreState(QtCore.QByteArray.fromHex(six.ensure_binary(settings['browserSplitter'])))

    def get_settings_dict(self):
        settings_dict = {
            'showAllCheckBox': int(self.showAllCheckBox.isChecked()),
            'showMoreInfoCheckBox': int(self.showMoreInfoCheckBox.isChecked()),
            'browserSplitter': gf.do_str(self.browserSplitter.saveState().toHex())
        }
        return settings_dict

    def graphicsSceneResizeEvent(self, event):
        if self.pm1:
            if self.pm1.pixmap_item:
                rect = self.pm1.pixmap_item.boundingRect()
            else:
                rect = QtCore.QRect(0, 0, 512, 512)

            self.previewGraphicsView.setSceneRect(rect)
            self.previewGraphicsView.fitInView(rect, QtCore.Qt.KeepAspectRatio)

        event.accept()

    def resize_event(self, event):
        event.accept()

    def paintEvent(self, event):

        # may be it is hack, but it's the only event occuring when window shown
        if not self.shown:
            if self.item_widget:
                self.refresh_with_item_widget(self.item_widget)
            self.shown = True

        event.accept()

class Pixmap(QtCore.QObject):
    def __init__(self, parent=None):
        super(Pixmap, self).__init__(parent=parent)

        self.pixmap_item = QtGui.QGraphicsPixmapItem()
        self.pixmap_item.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.pixmap_item.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)

    def add_pixmap(self, pix):
        self.pixmap_item.setPixmap(pix)

    def set_pos(self, pos):
        self.pixmap_item.setPos(pos)

    def get_pos(self):
        return self.pixmap_item.pos()

    def set_op(self, op):
        self.pixmap_item.setOpacity(op)

    def get_op(self):
        return self.pixmap_item.opacity()

    pos = QtCore.Property(QtCore.QPointF, get_pos, set_pos)
    opacity = QtCore.Property(float, get_op, set_op)
