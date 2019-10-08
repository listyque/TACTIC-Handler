# module Tree widget item Classes
# file ui_item_classes.py
# Main Item for TreeWidget

import os
from xml.etree.ElementPath import get_parent_map

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtNetwork
from thlib.side.Qt import QtCore

from thlib.environment import env_tactic, env_inst, cfg_controls, dl
from thlib.ui_classes.ui_repo_sync_queue_classes import Ui_repoSyncDialog
import thlib.global_functions as gf
import thlib.tactic_classes as tc
import thlib.ui.items.ui_commit_item as ui_commit_item
import thlib.ui.items.ui_preview_item as ui_preview_item
import thlib.ui.items.ui_item as ui_item
import thlib.ui.items.ui_item_children as ui_item_children
import thlib.ui.items.ui_item_process as ui_item_process
import thlib.ui.items.ui_item_snapshot as ui_item_snapshot
import ui_tasks_classes as tasks_widget
import ui_notes_classes
import ui_addsobject_classes

# reload(ui_item)
# reload(ui_item_process)
# reload(ui_item_snapshot)
# reload(tasks_widget)
# reload(ui_notes_classes)


class Ui_infoItemsWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()
        self.items = []
        self.items_ = []

    def create_ui(self):

        self.main_layout = QtGui.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.items_layout = QtGui.QHBoxLayout()
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(4)
        self.items_layout.setSizeConstraint(QtGui.QLayout.SetMinAndMaxSize)

        self.items_right_layout = QtGui.QHBoxLayout()
        self.items_right_layout.setContentsMargins(0, 0, 10, 0)
        self.items_right_layout.setSpacing(4)

        self.main_layout.addLayout(self.items_layout)
        spacer = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        self.main_layout.addItem(spacer)

        self.main_layout.addLayout(self.items_right_layout)

    def add_item(self, widget):
        if len(self.items) > 0:
            self.items_layout.addWidget(self.get_line_delimiter())
        self.items_layout.addWidget(widget)
        self.items.append(widget)

    def add_item_to_right(self, widget):
        if len(self.items) > 0:
            self.items_right_layout.addWidget(self.get_line_delimiter())
        self.items_right_layout.addWidget(widget)
        self.items.append(widget)

    def get_line_delimiter(self):
        line = QtGui.QFrame(self)
        line.setMaximumSize(QtCore.QSize(1, 12))
        line.setStyleSheet('QFrame { border: 0px; background-color: grey;}')
        # line.setFrameShadow(QtGui.QFrame.Plain)
        line.setFrameShape(QtGui.QFrame.VLine)
        return line

    def get_items(self):
        return self.items

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_previewItemWidget(QtGui.QWidget, ui_preview_item.Ui_previewItem):
    def __init__(self, file_object=None, screenshot=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'preview'
        self.file_object = file_object
        self.screenshot = screenshot

        self.create_ui()

    def create_ui(self):

        if self.file_object:
            self.fill_info_with_file_object()
        if self.screenshot:
            self.fill_info_with_screenshot()

    def set_title(self, title=u''):
        self.fileNameLabel.setText(title)

    def fill_info_with_file_object(self):
        self.set_title(self.file_object.get_pretty_file_name())

        self.set_preview()

    def fill_info_with_screenshot(self):
        self.set_title('Screen Shot Image')

        self.set_preview(self.screenshot)

    def set_preview(self, pix=None):
        pixmap = None

        if pix:
            pixmap = pix
        else:
            icon = None
            if self.file_object.is_exists() and self.file_object.is_previewable():
                source_image_path = self.file_object.get_all_files_list(True)
                image = Qt4Gui.QImage(0, 0, Qt4Gui.QImage.Format_ARGB32)
                icon = None
                if image.load(source_image_path):
                    icon = image.scaledToWidth(120, QtCore.Qt.SmoothTransformation)

            if icon:
                pixmap = Qt4Gui.QPixmap(icon)

        if pixmap:
            if not pixmap.isNull():
                pixmap = pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation)

                painter = Qt4Gui.QPainter()
                pixmap_mask = Qt4Gui.QPixmap(64, 64)
                pixmap_mask.fill(QtCore.Qt.transparent)
                painter.begin(pixmap_mask)
                painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
                painter.setBrush(Qt4Gui.QBrush(Qt4Gui.QColor(0, 0, 0, 255)))
                painter.drawRoundedRect(QtCore.QRect(0, 0, 64, 64), 4, 4)
                painter.end()

                rounded_pixmap = Qt4Gui.QPixmap(pixmap.size())
                rounded_pixmap.fill(QtCore.Qt.transparent)
                painter.begin(rounded_pixmap)
                painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
                painter.drawPixmap(QtCore.QRect((pixmap.width() - 64) / 2, 0, 64, 64), pixmap_mask)
                painter.setCompositionMode(Qt4Gui.QPainter.CompositionMode_SourceIn)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()

                self.previewLabel.setPixmap(rounded_pixmap)

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_commitItemWidget(QtGui.QWidget, ui_commit_item.Ui_commitItem):
    def __init__(self, item_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'commit'
        self.commit_widget = None
        self.args_dict = None
        self.item_widget = item_widget
        self.progress_wdg = QtGui.QWidget(self)
        self.progress_wdg.setHidden(True)
        self.commited = False
        self.create_ui()

    def create_ui(self):
        self.set_title('Loading...')
        self.create_progress_indicator()

    def set_args_dict(self, args_dict):
        self.args_dict = args_dict

    def get_args_dict(self):
        return self.args_dict

    def set_commit_widget(self, commit_widget):
        self.commit_widget = commit_widget

    def get_commit_widget(self):
        return self.commit_widget

    def set_title(self, title=u''):
        self.fileNameLabel.setText(title)

    def set_new_title(self, new_title=u''):
        file_object = self.args_dict.get('files_objects')[0]
        self.fileNameLabel.setText(u'{} > {}'.format(file_object.get_pretty_file_name(), new_title))

    def set_description(self, description=u''):
        self.commentLabel.setText(description)

    def fill_info(self):
        file_object = self.args_dict.get('files_objects')[0]

        self.set_title(file_object.get_pretty_file_name())

        self.set_description(self.commit_widget.description)

        self.set_preview()

    def set_preview(self, pix=None, image_path=None):
        pixmap = None

        if pix:
            pixmap = pix

        elif image_path:
            # print('MAKING PREVIEW FROM IMAGE PATH')
            source_image_path = image_path
            image = Qt4Gui.QImage(0, 0, Qt4Gui.QImage.Format_ARGB32)
            icon = None
            if image.load(source_image_path):
                icon = image.scaledToWidth(120, QtCore.Qt.SmoothTransformation)

            if icon:
                pixmap = Qt4Gui.QPixmap(icon)

        else:
            icon = None
            file_object = self.args_dict.get('files_objects')[0]
            if file_object.is_exists() and file_object.is_previewable():
                source_image_path = file_object.get_all_files_list(True)
                image = Qt4Gui.QImage(0, 0, Qt4Gui.QImage.Format_ARGB32)
                icon = None
                if image.load(source_image_path):
                    icon = image.scaledToWidth(120, QtCore.Qt.SmoothTransformation)

            if icon:
                pixmap = Qt4Gui.QPixmap(icon)

        if pixmap:
            if not pixmap.isNull():
                pixmap = pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation)

                painter = Qt4Gui.QPainter()
                pixmap_mask = Qt4Gui.QPixmap(64, 64)
                pixmap_mask.fill(QtCore.Qt.transparent)
                painter.begin(pixmap_mask)
                painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
                painter.setBrush(Qt4Gui.QBrush(Qt4Gui.QColor(0, 0, 0, 255)))
                painter.drawRoundedRect(QtCore.QRect(0, 0, 64, 64), 4, 4)
                painter.end()

                rounded_pixmap = Qt4Gui.QPixmap(pixmap.size())
                rounded_pixmap.fill(QtCore.Qt.transparent)
                painter.begin(rounded_pixmap)
                painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
                painter.drawPixmap(QtCore.QRect((pixmap.width() - 64) / 2, 0, 64, 64), pixmap_mask)
                painter.setCompositionMode(Qt4Gui.QPainter.CompositionMode_SourceIn)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()

                self.previewLabel.setPixmap(rounded_pixmap)

    def create_progress_indicator(self):
        if self.progress_wdg.isHidden():
            self.lay = QtGui.QVBoxLayout(self.progress_wdg)
            self.lay.setSpacing(0)
            self.lay.setContentsMargins(0, 0, 0, 0)
            self.progress_wdg.setLayout(self.lay)
            self.progress_bar_wdg = QtGui.QProgressBar()
            self.progress_bar_wdg.setTextVisible(True)
            self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,160,200,64);}')
            self.progress_bar_wdg.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
            self.progress_bar_wdg.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.lay.addWidget(self.progress_bar_wdg)
            self.progress_wdg.show()
            self.progress_wdg.resize(self.size())

    def set_progress_indicator_on(self):
        self.progress_wdg.setHidden(False)

    def set_progress_indicator_off(self):
        self.progress_wdg.setHidden(True)

    def set_progress_status(self, progress, info_dict):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,160,200,64);}')
        self.progress_bar_wdg.setMaximum(info_dict['total_count'])
        self.progress_bar_wdg.setValue(progress + 1)
        self.progress_bar_wdg.setFormat(u'%v / %m {status_text}'.format(**info_dict))

    def is_commit_finished(self):
        return self.commited

    def set_commit_finished(self):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,160,30,128);}')
        self.progress_bar_wdg.setFormat('Commit Finished')
        self.commited = True

    def set_commit_ufinished(self):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,160,200,64);}')
        self.commited = False

    def set_commit_failed(self):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(200,20,10,64);}')
        self.progress_bar_wdg.setFormat('Commit Failed')
        self.commited = False

    def resizeEvent(self, event):
        self.progress_wdg.resize(self.size())

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_repoSyncItemWidget(QtGui.QWidget):
    downloaded = QtCore.Signal(object)

    def __init__(self, file_object, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.type = 'repo_sync'
        self.file_object = file_object
        self.network_manager = None
        self.progress_wdg = QtGui.QWidget(self)
        self.progress_wdg.setHidden(True)
        self.is_downloaded = False

        self.create_ui()

    def create_ui(self):
        self.setMinimumSize(280, 40)
        self.create_main_layout()
        self.create_file_name_label()

        self.fill_info()
        self.create_progress_indicator()

    def create_main_layout(self):

        self.main_layout = QtGui.QGridLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 4, 0, 0)

    def create_file_name_label(self):
        self.file_name_label = QtGui.QLabel()
        self.file_name_label.setStyleSheet('QLabel {padding-left: 4px;}')
        self.main_layout.addWidget(self.file_name_label)

    def set_title(self, title=u''):
        self.file_name_label.setText(title)

    def set_description(self, description=u''):
        self.commentLabel.setText(description)

    def fill_info(self):
        self.set_title(self.file_object.get_filename_with_ext())
        # self.set_description(self.commit_widget.description)

    def create_progress_indicator(self):
        if self.progress_wdg.isHidden():
            self.lay = QtGui.QVBoxLayout(self.progress_wdg)
            self.lay.setSpacing(0)
            self.lay.setContentsMargins(0, 0, 0, 0)
            self.progress_wdg.setLayout(self.lay)
            self.progress_bar_wdg = QtGui.QProgressBar()
            self.progress_bar_wdg.setTextVisible(True)
            self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,160,200,64);}')
            self.progress_bar_wdg.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
            self.progress_bar_wdg.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            self.lay.addWidget(self.progress_bar_wdg)
            self.progress_wdg.show()
            # self.progress_wdg.resize(self.size())
            self.main_layout.addWidget(self.progress_wdg)

    def set_progress_indicator_on(self):
        self.progress_wdg.setHidden(False)

    def set_progress_indicator_off(self):
        self.progress_wdg.setHidden(True)

    def set_progress_status(self, progress, info_dict):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,160,200,64);}')
        self.progress_bar_wdg.setMaximum(info_dict['total_count'])
        self.progress_bar_wdg.setValue(progress + 1)
        self.progress_bar_wdg.setFormat(u'%v / %m {status_text}'.format(**info_dict))

    def is_download_finished(self):
        return self.is_downloaded

    def set_download_finished(self):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,160,30,128);}')
        self.progress_bar_wdg.setFormat('Download Finished')
        self.is_downloaded = True

    def set_download_ufinished(self):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,160,200,64);}')
        self.is_downloaded = False

    def set_download_already_exists(self):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(30,60,120,128);}')
        self.progress_bar_wdg.setFormat('File Already In Repo')
        self.is_downloaded = True

    def set_download_failed(self):
        self.progress_bar_wdg.setStyleSheet('QProgressBar {border:0px; background-color: transparent;}'
                                            'QProgressBar::chunk {background-color: rgba(200,20,10,64);}')
        self.progress_bar_wdg.setFormat('Download Failed')
        self.is_downloaded = False

    def download_done(self):

        self.set_download_finished()

        self.is_downloaded = True
        self.downloaded.emit(self.file_object)

    def download_progress(self, progress, info_dict=None):
        self.set_progress_indicator_on()
        self.set_progress_status(progress, info_dict)

    def download_def(self):

        def download_file_agent():
            # print '5.1 Begin downloading'
            info_dict = {
                'status_text': 'Downloading File',
                'total_count': 2
            }
            download_file_worker.emit_progress(0, info_dict)

            self.file_object.download_file()
            download_file_worker.emit_progress(1, info_dict)

        # print '4 Getting thread pool'
        # print env_inst.get_thread_pool('server_query/http_download_pool')
        download_file_worker = gf.get_thread_worker(
            download_file_agent,
            env_inst.get_thread_pool('server_query/http_download_pool'),
            finished_func=self.download_done,
            progress_func=self.download_progress,
            error_func=gf.error_handle,
        )
        # print '5 Starting worker'
        # stypes_items_worker.setAutoDelete(True)
        download_file_worker.start()

    def set_network_manager(self, network_manager):
        self.network_manager = network_manager

    def file_already_in_repo(self):

        if os.path.exists(self.file_object.get_full_abs_path()):
            if self.file_object.get_file_size() == self.file_object.get_file_size(True):
                return True

    def download(self):
        if not self.file_already_in_repo():
            url = QtCore.QUrl(self.file_object.get_full_web_path())
            request = QtNetwork.QNetworkRequest(url)
            # print url.toString()
            # print request
            request.setAttribute(QtNetwork.QNetworkRequest.User, self.file_object)
            request.setAttribute(QtNetwork.QNetworkRequest.HttpPipeliningAllowedAttribute, True)

            # print request.attribute()

            # print self.file_object.get_unique_id()
            info_dict = {
                'status_text': 'Downloading File',
                'total_count': 4
            }
            self.download_progress(0, info_dict)

            self.network_manager.get(request)
            self.download_progress(1, info_dict)
        else:
            info_dict = {
                'status_text': 'Downloading File',
                'total_count': 2
            }
            self.download_progress(0, info_dict)
            self.download_progress(1, info_dict)
            self.set_download_already_exists()
            self.downloaded.emit(self.file_object)

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_itemWidget(QtGui.QWidget, ui_item.Ui_item):
    def __init__(self, sobject, stype, info, ignore_dict, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.closed = False
        self.created = False
        self.overlay_layout_widget = None
        self.type = 'sobject'
        self.sobject = sobject
        self.stype = stype

        self.info = info
        self.tree_item = None
        self.sep_versions = self.info['sep_versions']
        self.process_items = []
        self.child_items = []
        self.snapshots_items = []
        self.search_widget = None

        self.project = self.stype.get_project()
        self.relates_to = 'checkin_out'
        self.ignore_dict = ignore_dict

        self.expand_state = False
        self.selected_state = False
        self.have_watch_folder = False
        self.watch_folder_path = None

        self.parents_stypes = None
        self.children_stypes = None

        if self.stype.schema:
            self.check_for_children()
        # self.check_for_downloadable()

        self.forced_creation()

    def controls_actions(self):
        self.tasksToolButton.clicked.connect(self.create_tasks_window)
        self.relationsToolButton.clicked.connect(self.drop_down_children)
        self.syncWithRepoToolButton.clicked.connect(self.create_sync_dialog)
        self.notesToolButton.clicked.connect(self.show_notes_widget)

    def create_simple_view_ui(self):

        self.create_overlay_layout()

        self.setMinimumWidth(260)

        self.previewLabel.setText(u'<span style=" font-size:14pt; font-weight:600; color:#828282;">{0}</span>'.format(
            gf.gen_acronym(self.get_title()))
        )
        self.itemColorLine.setStyleSheet('QFrame { border: 0px; background-color: %s;}' % self.stype.get_stype_color())

        self.tasksToolButton.setHidden(True)
        self.relationsToolButton.setHidden(True)
        self.notesToolButton.setHidden(True)
        self.watchFolderToolButton.setHidden(True)
        self.syncWithRepoToolButton.setHidden(True)

        self.create_item_info_widget()

        if self.sobject:
            self.fill_sobject_info()
            self.fill_info_items()
            if gf.get_value_from_config(cfg_controls.get_checkin(), 'getPreviewsThroughHttpCheckbox') == 1:
                self.set_web_preview()
            else:
                self.set_preview()

    def create_ui(self):
        # self.drop_wdg = QtGui.QWidget(self)

        self.create_overlay_layout()

        self.setMinimumWidth(260)

        self.previewLabel.setText(u'<span style=" font-size:14pt; font-weight:600; color:#828282;">{0}</span>'.format(
            gf.gen_acronym(self.get_title()))
        )
        self.itemColorLine.setStyleSheet('QFrame { border: 0px; background-color: %s;}' % self.stype.get_stype_color())

        self.tasksToolButton.setIcon(gf.get_icon('tasks'))
        self.relationsToolButton.setIcon(gf.get_icon('sitemap', icons_set='mdi'))

        self.notesToolButton.setIcon(gf.get_icon('commenting-o'))

        self.create_item_info_widget()
        self.create_sync_with_repo_button()
        self.create_watch_folder_button()

        if self.sobject:
            self.fill_sobject_info()
            self.fill_info_items()
            if gf.get_value_from_config(cfg_controls.get_checkin(), 'getPreviewsThroughHttpCheckbox') == 1:
                self.set_web_preview()
            else:
                self.set_preview()

        self.check_watch_folder()

        self.check_expand_state(self.get_children_states())

        self.controls_actions()

    def create_overlay_layout(self):
        # when use this, layout should have only one widget, use add_overlay_widget()

        self.overlay_layout_widget = QtGui.QWidget(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.overlay_layout_widget.setSizePolicy(sizePolicy)

        self.overlay_layout = QtGui.QVBoxLayout(self.overlay_layout_widget)
        self.overlay_layout.setSpacing(0)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)

        self.overlay_layout_widget.setLayout(self.overlay_layout)
        self.overlay_layout_widget.setHidden(True)

    def show_overlay(self):
        self.overlay_layout_widget.setHidden(False)
        self.show()

    def create_tasks_window(self):
        try:
            self.tasks_widget.show()
        except:
            self.tasks_widget = tasks_widget.Ui_tasksWidgetMain(self.sobject, self)
            self.tasks_widget.show()

    def create_watch_folder_button(self):
        self.watchFolderToolButton.setIcon(gf.get_icon('eye-slash', color=Qt4Gui.QColor(160, 160, 160)))
        self.watchFolderToolButton.toggled.connect(self.toggle_watch_folder_button)
        self.watchFolderToolButton.clicked.connect(self.save_watch_status)

    def create_sync_with_repo_button(self):
        self.syncWithRepoToolButton.setIcon(gf.get_icon('cloud-sync', color=Qt4Gui.QColor(250, 250, 250), icons_set='mdi'))
        # self.syncWithRepoToolButton.clicked.connect(self.save_watch_status)

    def create_item_info_widget(self):
        self.item_info_widget = Ui_infoItemsWidget(self)
        self.infoHorizontalLayout.addWidget(self.item_info_widget)

    def create_sync_dialog(self):
        sync_dialog = Ui_repoSyncDialog(parent=env_inst.ui_main, stype=self.stype, sobject=self.sobject)
        sync_dialog.exec_()

    def add_overlay_widget(self, widget):
        self.overlay_layout.addWidget(widget)

    def get_overlay_layout(self):
        return self.overlay_layout

    def get_overlay_widget(self):
        return self.overlay_layout.itemAt(0).widget()

    def get_type(self):
        return self.type

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.selected_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def get_children_states(self):
        return self.info.get('children_states')

    def set_children_states(self, states):
        self.info['children_states'] = states

    def is_checked(self):
        return False

    def set_tasks_count(self, tasks_count):
        if tasks_count > 0:
            self.tasksToolButton.setIcon(gf.get_icon('tasks'))
        self.tasksToolButton.setText('| {0}'.format(tasks_count))

    def set_notes_count(self, notes_count):
        if notes_count > 0:
            self.notesToolButton.setIcon(gf.get_icon('commenting'))
        self.notesToolButton.setText('| {0}'.format(notes_count))

    def is_have_watch_folder(self):
        if self.have_watch_folder:
            if self.watchFolderToolButton.isChecked():
                return True

    def check_watch_folder(self, remove_watch=False):
        watch_folder_ui = env_inst.watch_folders.get(self.project.get_code())
        watch_dict = watch_folder_ui.get_watch_dict_by_skey(self.get_search_key())

        if watch_dict and not self.have_watch_folder:
            self.have_watch_folder = True
            if watch_dict['status']:
                self.set_watch_folder_enabled()
            else:
                self.set_watch_folder_disabled()
            watch_folder_ui.add_item_to_watch(self)
            self.set_watch_folder_path(watch_dict['path'])
        elif not self.have_watch_folder:
            self.watchFolderToolButton.setIcon(gf.get_icon('eye-slash', color=Qt4Gui.QColor(160, 160, 160)))

        if remove_watch:
            self.have_watch_folder = False
            self.watchFolderToolButton.setChecked(False)
            self.watchFolderToolButton.setIcon(gf.get_icon('eye-slash', color=Qt4Gui.QColor(160, 160, 160)))

    def save_watch_status(self):
        if self.have_watch_folder:
            watch_folder_ui = env_inst.watch_folders.get(self.project.get_code())
            if self.watchFolderToolButton.isChecked():
                watch_folder_ui.edit_watch_to_watch_folders_dict(self, status=True)
            else:
                watch_folder_ui.edit_watch_to_watch_folders_dict(self, status=False)
        else:
            self.watchFolderToolButton.setChecked(False)
            watch_folders_ui = env_inst.watch_folders.get(self.project.get_code())
            watch_folders_ui.add_asset_to_watch(self)

    def toggle_watch_folder_button(self, state):
        if state:
            if self.have_watch_folder:
                self.watchFolderToolButton.setIcon(gf.get_icon(
                    'eye',
                    color=Qt4Gui.QColor(100, 200, 100),
                    color_active=Qt4Gui.QColor(120, 220, 120),
                ))
        else:
            if self.have_watch_folder:
                self.watchFolderToolButton.setIcon(gf.get_icon(
                    'eye-slash',
                    color=Qt4Gui.QColor(200, 100, 100),
                    color_active=Qt4Gui.QColor(220, 120, 120),
                ))

    def set_watch_folder_enabled(self):
        self.watchFolderToolButton.setChecked(True)
        self.toggle_watch_folder_button(True)

    def set_watch_folder_disabled(self):
        self.watchFolderToolButton.setChecked(False)
        self.toggle_watch_folder_button(False)

    def set_watch_folder_path(self, path):
        self.watch_folder_path = path

    def get_watch_folder_path(self):
        return self.watch_folder_path

    def get_watch_folder_dict(self):
        watch_folder_ui = env_inst.watch_folders.get(self.project.get_code())
        watch_dict = watch_folder_ui.get_watch_dict_by_skey(self.get_search_key())

        return watch_dict

    def show_notes_widget(self):
        project = self.sobject.get_project()
        notes_widget = env_inst.get_check_tree(project.get_code(), 'checkin_out_instanced_widgets', 'notes_dock')
        notes_widget.add_notes_tab(self.sobject, 'publish')

    def set_drop_indicator_on(self):
        if self.drop_wdg.isHidden():
            self.lay = QtGui.QVBoxLayout(self.drop_wdg)
            self.lay.setSpacing(0)
            self.lay.setContentsMargins(0, 0, 0, 0)
            self.drop_wdg.setLayout(self.lay)
            self.drop_wdg.setStyleSheet('QLabel {padding: 0px;border: 0px dashed grey; background-color: rgba(0,0,100,128);}')
            self.label = QtGui.QLabel('DROP HERE')
            self.lay.addWidget(self.label)
            self.drop_wdg.show()
            self.drop_wdg.resize(self.size())

    def set_drop_indicator_off(self):
        self.drop_wdg.setHidden(True)

    @staticmethod
    def get_item_info_label():
        font = Qt4Gui.QFont()
        font.setPointSize(7)
        label = QtGui.QLabel()
        label.setFont(font)
        label.setTextFormat(QtCore.Qt.PlainText)
        label.setAlignment(QtCore.Qt.AlignCenter)
        return label

    @staticmethod
    def get_item_info_html_label():
        font = Qt4Gui.QFont()
        font.setPointSize(7)
        label = QtGui.QLabel()
        label.setFont(font)
        label.setOpenExternalLinks(True)
        label.setTextFormat(QtCore.Qt.RichText)
        label.setAlignment(QtCore.Qt.AlignCenter)
        return label

    def fill_sobject_info(self):

        # self.dateLabel = self.get_item_info_label()
        self.tasksLabel = self.get_item_info_label()
        self.snapshotsLabel = self.get_item_info_label()
        # self.item_info_widget.add_item_to_right(self.dateLabel)

        self.fileNameLabel.setText(self.get_title())
        limit_enabled = bool(gf.get_value_from_config(cfg_controls.get_checkin(), 'snapshotDescriptionLimitCheckBox'))
        limit = gf.get_value_from_config(cfg_controls.get_checkin(), 'snapshotDescriptionLimitSpinBox')
        if limit_enabled:
            self.commentLabel.setText(gf.to_plain_text(self.sobject.info.get('description'), limit))
        else:
            self.commentLabel.setText(gf.to_plain_text(self.sobject.info.get('description'), None))
        # timestamp = datetime.strptime(self.sobject.info.get('timestamp').split('.')[0], '%Y-%m-%d %H:%M:%S')
        # date = str(self.sobject.info.get('timestamp')).split('.')[0].replace(' ', ' \n')
        # self.dateLabel.setText(date)
        # self.item_info_widget.add_item(self.dateLabel)
        self.tasksLabel.setText('0 Tasks')
        self.snapshotsLabel.setText('0 Snapshots')

        self.set_notes_count(self.sobject.get_notes_count('publish'))
        self.set_tasks_count(self.sobject.get_tasks_count('__total__'))

    def fill_info_items(self):
        table_columns = []

        # may be it's slow to getting definition this way

        color_definition = self.stype.get_definition('color', bs=True)

        edit_definition = self.stype.get_definition('edit_definition', bs=True)

        # TODO May be it should be special TACTIC-Handler definition if it is exists
        for i in self.stype.get_definition('table'):
            table_columns.append(i.get('name'))

        exclude_columns = ['__search_type__', '__search_key__', '__tasks_count__', '__notes_count__',
                           '__snapshots__', 'name', 'code', 'keywords', 'description', 'timestamp']
        for column, data in self.sobject.get_info().items():
            if data:
                if column in table_columns and column not in exclude_columns:
                    info_label = self.get_item_info_label()
                    name = None

                    # Getting color from db
                    if color_definition.element:
                        name = color_definition.element.get('name')
                    if column == name:
                        if color_definition.colors:
                            for colors in color_definition.colors.find_all():
                                if colors.get('name') == data:
                                    info_label.setStyleSheet('color: {}'.format(gf.hex_to_rgb(colors.text)))

                    # Getting edit definition from db, just to freely get labels
                    if edit_definition.element:
                        for element in edit_definition.edit_definition.find_all():
                            if column == element.get('name'):
                                if element.values and element.labels:
                                    for val, label in zip(element.values.text.split('|'), element.labels.text.split('|')):
                                        if val == data:
                                            data = label
                    if unicode(data).lower().startswith(('https://', 'http://', 'ftp://')):
                        info_label = self.get_item_info_html_label()
                        info_label.setPixmap(gf.get_icon('crosshairs', color=Qt4Gui.QColor(255, 255, 255)).pixmap(24, 24))
                        info_label.setText(u'<p><a href="{1}" style="color:#66a3ff;text-decoration:none;">{0} Link</a></p>'.format(column.capitalize(), data))
                    else:
                        # at this time we don't need long text, as it will not fit to item
                        data = unicode(data)[0:30]
                        info_label.setText(data)
                    self.item_info_widget.add_item(info_label)

    def set_preview(self):

        snapshots = self.get_snapshot('icon')
        if not snapshots:
            snapshots = self.get_snapshot('publish')

        if snapshots:
            preview_files_objects = snapshots.get_files_objects(group_by='type').get('icon')
            if preview_files_objects:
                icon_previw = preview_files_objects[0].get_icon_preview()
                if icon_previw:
                    pixmap = self.get_preview_pixmap(icon_previw.get_full_abs_path())
                    if pixmap:
                        self.previewLabel.setPixmap(pixmap)

    def set_web_preview(self):

        snapshots = self.get_snapshot('icon')
        if not snapshots:
            snapshots = self.get_snapshot('publish')

        if snapshots:
            preview_files_objects = snapshots.get_files_objects(group_by='type').get('icon')
            if preview_files_objects:
                icon_previw = preview_files_objects[0].get_icon_preview()
                if icon_previw:
                    if os.path.exists(icon_previw.get_full_abs_path()):
                        # TODO This should be more complicated, and check hash not just size
                        if icon_previw.get_file_size() == icon_previw.get_file_size(True):
                            self.set_preview()
                        else:
                            self.download_and_set_preview_file(icon_previw)
                    else:
                        self.download_and_set_preview_file(icon_previw)

    def download_and_set_preview_file(self, file_object):
        repo_sync_item = env_inst.ui_repo_sync_queue.download_file_object(file_object)
        repo_sync_item.downloaded.connect(self.set_preview_pixmap)
        repo_sync_item.download()

    def set_preview_pixmap(self, file_object):
        pixmap = self.get_preview_pixmap(file_object.get_full_abs_path())
        if pixmap:
            self.previewLabel.setPixmap(pixmap)

    def get_preview_pixmap(self, image_path):
        pixmap = Qt4Gui.QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation)

            painter = Qt4Gui.QPainter()
            pixmap_mask = Qt4Gui.QPixmap(64, 64)
            pixmap_mask.fill(QtCore.Qt.transparent)
            painter.begin(pixmap_mask)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.setBrush(Qt4Gui.QBrush(Qt4Gui.QColor(0, 0, 0, 255)))
            painter.drawRoundedRect(QtCore.QRect(0, 0, 64, 64), 4, 4)
            painter.end()

            rounded_pixmap = Qt4Gui.QPixmap(pixmap.size())
            rounded_pixmap.fill(QtCore.Qt.transparent)
            painter.begin(rounded_pixmap)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.drawPixmap(QtCore.QRect((pixmap.width() - 64) / 2, 0, 64, 64), pixmap_mask)
            painter.setCompositionMode(Qt4Gui.QPainter.CompositionMode_SourceIn)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            return rounded_pixmap

    def drop_down_children(self):
        self.relationsToolButton.showMenu()

    def check_expand_state(self, state=None):

        if state:
            if state.get('d'):
                expanded = state['d']['e']
                selected = state['d']['s']

                if expanded:
                    self.set_expand_state(expanded)
                if selected:
                    self.set_selected_state(selected)

                # state for current item was applied and then replaced with children states
                self.set_children_states(state['s'])

    def collapse_self(self):
        parent = self.get_parent_item()
        return parent.takeChild(self.get_row())

    @gf.catch_error
    def expand_recursive(self):
        gf.tree_recursive_expand(self.tree_item, True)

    @gf.catch_error
    def collapse_recursive(self):
        gf.tree_recursive_expand(self.tree_item, False)

    def collapse_tree_item(self):
        pass

    @gf.catch_error
    def expand_tree_item(self):
        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            self.fill_child_items()
            self.fill_process_items()

            self.query_snapshots()

        self.get_notes_count()

    def collapse_all_children(self):
        return self.tree_item.takeChildren()

    def check_sub_items_expand_state(self, state=None):
        if state:
            gf.tree_state_revert(self.tree_item, state)

    def check_for_children(self):
        if self.stype.schema.parents:
            self.parents_stypes = self.stype.schema.parents
            for parent in self.stype.schema.parents:
                parent_code = parent.get('to')
                parent_title = self.project.stypes.get(parent_code)
                if parent_title:
                    parent_title = parent_title.info.get('title')
                else:
                    parent_title = parent_code
                parent_action = QtGui.QAction(parent_title, self.relationsToolButton)
                self.relationsToolButton.addAction(parent_action)

        if self.stype.schema.children:
            self.children_stypes = self.stype.schema.children
            child_sep = QtGui.QAction('Children', self.relationsToolButton)
            child_sep.setSeparator(True)
            self.relationsToolButton.addAction(child_sep)

            for child in self.stype.schema.children:
                child_code = child.get('from')
                child_title = self.project.stypes.get(child_code)
                if child_title:
                    child_title = child_title.info.get('title')
                else:
                    child_title = child_code
                child_action = QtGui.QAction(child_title, self.relationsToolButton)
                self.relationsToolButton.addAction(child_action)

        if not (self.stype.schema.children or self.stype.schema.parents):
            self.relationsToolButton.hide()

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return u'{0}/{1}'.format('publish', custom)
            else:
                return 'publish'
        else:
            return ''

    def get_context_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process('publish')
        if process:
            context_options = process.get('context_options')
            if context_options:
                return context_options.split('|')

    def get_checkin_mode_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process('publish')

        if process:
            return process.get('checkin_mode')

    @staticmethod
    def get_current_process_info():
        process_info = {'name': 'publish'}
        return process_info

    def get_current_process_pipeline(self):

        search_type = self.stype.info.get('search_type')
        if search_type and self.stype.pipeline:
            return self.stype.pipeline.get(search_type)

    def get_skey(self, skey=False, only=False, parent=False):
        """skey://cgshort/props?project=the_pirate&code=PROPS00001"""
        if parent or only:
            return self.sobject.info['__search_key__']
        if skey:
            return 'skey://' + self.sobject.info['__search_key__']

    def get_description(self):
        return self.sobject.info.get('description')

    def update_description(self, new_description):
        self.sobject.info['description'] = new_description
        self.commentLabel.setText(new_description)

    def query_snapshots(self):

        order_bys = ['timestamp desc']

        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Getting snapshots</span>')

        def update_snapshots_agent():
            return self.sobject.update_snapshots(order_bys=order_bys)

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        query_worker = gf.get_thread_worker(
            update_snapshots_agent,
            thread_pool=env_inst.get_thread_pool('server_query/server_thread_pool'),
            finished_func=self.fill_snapshots_items,
            error_func=gf.error_handle
        )
        query_worker.start()

    def check_for_child_recursion(self):
        """
        This function checks for the recursively added relations,
        for example asset > texture_in_asset > asset_in_texture > asset.
        Currently it is implemeted through items relations and should be rewritten on the SObject level.
        """
        parent_item = self.get_parent_item_widget()
        if parent_item:
            if parent_item.type == 'child':
                child_item_parent = parent_item.get_parent_item_widget()
                if child_item_parent:
                    if not self.ignore_dict:
                        self.ignore_dict = {}
                    self.ignore_dict.setdefault('children', []).append(child_item_parent.stype.info['code'])

    def fill_child_items(self):
        # checking for unnecessary recursion
        self.check_for_child_recursion()

        # adding child items
        if self.children_stypes:
            for child in self.children_stypes:
                child_stype = self.project.stypes.get(child.get('from'))
                relationship_type = child.get('type')
                if child_stype:
                    ignored = False
                    if self.ignore_dict:
                        if self.ignore_dict.get('children'):
                            if child_stype.info['code'] in self.ignore_dict['children']:
                                ignored = True

                    if not ignored and relationship_type not in ['many_to_many']:
                        self.child_items.append(gf.add_child_item(
                            self.tree_item,
                            self.search_widget,
                            self.sobject,
                            child_stype,
                            child,
                            self.info
                        ))

    def fill_process_items(self):

        # getting all possible processes here
        processes = []
        pipeline_code = self.sobject.info.get('pipeline_code')
        curent_pipeline = None
        if pipeline_code and self.stype.pipeline:
            curent_pipeline = self.stype.pipeline.get(pipeline_code)
            if curent_pipeline:
                processes = curent_pipeline.process.keys()

        if self.ignore_dict:
            if self.ignore_dict.get('show_builtins'):
                show_all = True
                for builtin in ['icon', 'attachment', 'publish']:
                    if builtin not in self.ignore_dict['builtins']:
                        processes.append(builtin)
                        show_all = False
                if show_all:
                    processes.extend(['icon', 'attachment', 'publish'])

        for process in processes:
            process_info = curent_pipeline.get_process_info(process)

            ignored = False

            # Ignoring PROGRESS, ACTION, CONDITION processes
            # TODO Special case for progress, we should fetch completeness of progress node as in tactic.
            if process_info.get('type') in ['action', 'condition', 'dependency', 'progress']:
                ignored = True

            if self.ignore_dict:
                if self.ignore_dict.get('processes'):
                    if process in self.ignore_dict['processes'].get(pipeline_code):
                        ignored = True
            if not ignored:
                process_item = gf.add_process_item(
                    self.tree_item,
                    self.search_widget,
                    self.sobject,
                    self.stype,
                    process,
                    self.info
                )
                self.process_items.append(process_item)
                # filling sub processes
                process_item.fill_subprocesses()

        # if process_items:
        #     self.process_items = process_items
        # else:
        #     # this loads root 'publish' items on expand !my favorite duct tape!
        #     self.tree_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)

    def fill_snapshots_items(self):
        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Filling snapshots</span>')

        # adding snapshots to publish
        for key, val in self.sobject.process.iteritems():
            if key == 'publish':
                self.snapshots_items.append(gf.add_snapshot_item(
                        self.tree_item,
                        self.search_widget,
                        self.sobject,
                        self.stype,
                        'publish',
                        None,
                        val,
                        self.info,
                        self.sep_versions,
                        True,
                    ))

        # adding snapshots per process
        for proc in self.process_items:
            if proc.process_items:
                # may be buggy...
                proc.info['is_expanded'] = True
                proc.fill_snapshots_items()

            for key, val in self.sobject.process.iteritems():
                # because it is dict, items could be in any position
                if key == proc.process:
                    proc.snapshots_items.append(proc.add_snapshots_items(val))

        # print time.time() - start

        self.check_sub_items_expand_state(self.get_children_states())

        env_inst.ui_main.set_info_status_text('')

    def get_current_results_widget(self):
        current_tree = self.search_widget.get_current_results_tree_widget()
        return current_tree

    def get_depth(self):
        idx = 0
        item = self.tree_item

        while item.parent():
            item = item.parent()
            idx += 1

        return idx

    def get_row(self):
        return self.get_index().row()

    def get_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item.parent())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_results_widget()
        parent_item_widget = current_tree.itemWidget(self.tree_item.parent(), 0)
        return parent_item_widget

    def get_full_process_list(self):
        pipeline = self.get_current_process_pipeline()
        if pipeline:
            return pipeline.process

    def get_process_list(self, include_builtins=False, include_hierarchy=False):
        # process = []
        # for process_widget in self.process_items:
        #     process.append(process_widget.process)
        # return process
        if self.stype.pipeline:
            builtins = ['icon', 'attachment', 'publish']
            current_pipeline = self.stype.pipeline.get(self.sobject.get_pipeline_code())
            workflow = self.stype.get_workflow()
            processes_list = current_pipeline.get_all_processes_names()
            sub_processes_list = []

            # getting sub-processes from workflow
            for process, process_info in current_pipeline.process.items():
                if process_info.get('type') == 'hierarchy':
                    child_pipeline = workflow.get_child_pipeline_by_process_code(
                        current_pipeline,
                        process
                    )
                    if child_pipeline:
                        sub_processes_list.extend(child_pipeline.get_all_processes_names())

            if include_hierarchy:
                processes_list.extend(sub_processes_list)
                if include_builtins:
                    processes_list.extend(builtins)

            if include_builtins:
                processes_list.extend(builtins)

            return processes_list

    def get_children_list(self):
        children_list = []
        if self.children_stypes:
            for child in self.children_stypes:
                children_list.append(child.get('from'))
            return children_list
        else:
            return []

    @gf.catch_error
    def get_notes_count(self):

        #@gf.catch_error
        def notes_fill(result):
            if not self.closed:
                notes_counts = result['notes']
                process_items_dict = {item.process: item for item in self.process_items}
                for key, val in notes_counts.iteritems():
                    process_item = process_items_dict.get(key)
                    if process_item:
                        process_item.set_notes_count(val)

                children_counts = result['stypes']
                child_items_dict = {item.child.get('from'): item for item in self.child_items}
                for key, val in children_counts.iteritems():
                    child_item = child_items_dict.get(key)
                    if child_item:
                        child_item.set_child_count_title(val)

        def get_notes_counts_agent():
            return tc.get_notes_count(
                sobject=self.sobject,
                process=self.get_process_list(),
                children_stypes=self.get_children_list()
            )
        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        notes_counts_query_worker = gf.get_thread_worker(
            get_notes_counts_agent,
            thread_pool=env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=notes_fill,
            error_func=gf.error_handle
        )
        notes_counts_query_worker.start()

    def get_relationship(self):
        parent_item_widget = self.get_parent_item_widget()
        if parent_item_widget:
            if parent_item_widget.type == 'child':
                return parent_item_widget.get_relationship()

    def get_schema(self):
        parent_item_widget = self.get_parent_item_widget()
        if parent_item_widget:
            if parent_item_widget.type == 'child':
                return parent_item_widget.child

    def get_search_key(self):
        return self.sobject.get_search_key()

    def get_parent_search_key(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_search_key()

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

    def get_title(self):
        title = u'No Title'
        if self.sobject.info.get('name'):
            title = self.sobject.info.get('name')
        elif self.sobject.info.get('title'):
            title = self.sobject.info.get('title')
        elif self.sobject.info.get('code'):
            title = self.sobject.info.get('code')

        return title

    def get_all_versions_snapshots(self, process='publish'):
        process = self.sobject.process.get(process)
        if process:
            context = process.contexts.get(process)
            if context:
                return context.versions
            else:
                context = process.contexts.values()[0]
                return context.versions

    def get_snapshots(self, process='publish'):

        snapshot_process = self.sobject.process.get(process)

        if snapshot_process:
            context = snapshot_process.contexts.get(process)

            if not context:
                context = snapshot_process.contexts.values()[0]
            if context.versionless:
                return context.versionless
            else:
                return context.versions

    def get_all_snapshots(self):
        return self.sobject.process

    def get_snapshot(self, process='publish'):

        snapshot_process = self.sobject.process.get(process)
        if snapshot_process:
            context = snapshot_process.contexts.values()[0]
            if context.versionless:
                return context.versionless.values()[0]
            else:
                return context.versions.values()[0]

    def unlink_current_sobject(self):
        sobject = self.get_sobject()
        parent_sobject = self.get_parent_sobject()
        child = self.get_schema()

        tc.edit_multiple_instance_sobjects(
            self.project.get_code(),
            exclude_search_keys=[sobject.get_search_key()],
            parent_key=parent_sobject.get_search_key(),
            instance_type=child.get('instance_type')
        )

    def delete_current_sobject(self):
        # DISABLED TILL READY
        print 'Deleting of Sobjects Disabled.'
        # sobject = self.get_sobject()

        # sobject.delete_sobject()

    def delete_current_snapshot_sobject(self):

        print 'DELETING SNAPSHOT', self.get_sobject()

    def forced_creation(self):
        if self.info.get('forced_creation'):

            if not self.created:
                self.created = True
                if self.info['simple_view']:
                    self.create_simple_view_ui()
                else:
                    self.create_ui()

    def showEvent(self, event):
        if not self.created:
            self.created = True
            if self.info['simple_view']:
                self.create_simple_view_ui()
            else:
                self.create_ui()
        event.accept()

    def closeEvent(self, event):
        if self.have_watch_folder:
            watch_folder_ui = env_inst.watch_folders.get(self.project.get_code())
            watch_folder_ui.remove_item_from_watch(self)
        self.closed = True
        self.deleteLater()
        event.accept()

    def resizeEvent(self, event):
        if self.overlay_layout_widget:
            self.overlay_layout_widget.resize(self.size())
        event.accept()

    def mouseDoubleClickEvent(self, event):
        do_dbl_click = None
        if self.relates_to == 'checkin_out':
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin(), 'doubleClickSaveCheckBox')

        if not do_dbl_click:
            super(Ui_itemWidget, self).mouseDoubleClickEvent(event)
        else:
            if self.relates_to == 'checkin_out':
                self.search_widget.save_file()


class Ui_processItemWidget(QtGui.QWidget, ui_item_process.Ui_processItem):
    def __init__(self, sobject, stype, process, info, pipeline, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.created = False
        self.closed = False
        self.type = 'process'
        self.sobject = sobject
        self.stype = stype
        self.process = process
        self.pipeline = pipeline
        self.info = info
        self.tree_item = None
        self.sep_versions = self.info['sep_versions']
        self.process_info = self.get_current_process_info()
        self.workflow = self.stype.project.workflow
        self.process_items = []
        self.snapshots_items = []
        # print(tree_item.text(0))
        # self.item_info = {}

        self.expand_state = False
        self.selected_state = False
        self.have_watch_folder = False

        self.search_widget = None
        self.relates_to = 'checkin_out'

    def controls_actions(self):
        self.notesToolButton.clicked.connect(lambda: self.show_notes_widget())

    def create_ui(self):
        # self.drop_wdg = QtGui.QWidget(self)
        self.setMinimumWidth(260)
        item_color = Qt4Gui.QColor(200, 200, 200)
        pipeline = self.get_current_process_pipeline()
        process = pipeline.get_process(self.process)
        if process:
            hex_color = process.get('color')
            color = None
            if hex_color:
                color = gf.hex_to_rgb(hex_color, tuple=True)
            if color:
                item_color = Qt4Gui.QColor(*color)

        if self.process:
            title = self.process.capitalize()
        else:
            title = 'Unnamed'
        if self.process_info.get('type') == 'hierarchy':
            self.tree_item.setIcon(0, gf.get_icon('fork', icons_set='ei', color=item_color, scale_factor=0.9))
        else:
            self.tree_item.setIcon(0, gf.get_icon('circle', color=item_color, scale_factor=0.55))

        self.label.setContentsMargins(4, 0, 0, 0)
        self.label.setText(title)

        self.notesToolButton.setIcon(gf.get_icon('commenting-o'))

        self.controls_actions()

    def get_type(self):
        return self.type

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.selected_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def get_children_states(self):
        return self.info.get('children_states')

    def set_children_states(self, states):
        self.info['children_states'] = states

    # def check_expand_state(self, state=None):
    #     # if not state:
    #     #     state = self.get_children_states()
    #
    #     if state:
    #         from pprint import pprint
    #         pprint(state)
    #         # expanded = state[self.get_row()]['d']['e']
    #         # selected = state[self.get_row()]['d']['s']
    #         #
    #         # self.set_expand_state(expanded)
    #         # self.set_selected_state(selected)
    #         #
    #         # for i in range(self.get_depth()):
    #         #     state = state[self.get_row()]['s']
    #         #
    #         # self.set_children_states(state)

    @gf.catch_error
    def get_notes_count(self):

        #@gf.catch_error
        def notes_fill(result):
            if not self.closed:
                notes_counts = result['notes']
                process_items_dict = {item.process: item for item in self.process_items}
                for key, val in notes_counts.iteritems():
                    process_item = process_items_dict.get(key)
                    if process_item:
                        process_item.set_notes_count(val)

        def get_notes_counts_agent():
            return tc.get_notes_count(
                sobject=self.sobject,
                process=self.get_process_list(),
                children_stypes=[]
            )

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        notes_counts_query_worker = gf.get_thread_worker(
            get_notes_counts_agent,
            thread_pool=env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=notes_fill,
            error_func=gf.error_handle
        )
        notes_counts_query_worker.start()

    def get_full_process_list(self):
        pipeline = self.get_current_process_pipeline()
        if pipeline:
            return pipeline.process

    def get_process_list(self):
        process = []
        for process_widget in self.process_items:
            process.append(process_widget.process)
        return process

    def get_snapshot(self):
        return None

    def get_current_process(self):
        return self.sobject.get_process(self.process)

    def get_current_process_info(self):
        pipeline = self.get_current_process_pipeline()
        process_info = None
        if pipeline:
            process_info = pipeline.process.get(self.process)

        return process_info

    def get_current_process_pipeline(self):
        # pipeline_code = self.sobject.info.get('pipeline_code')
        # pipeline = self.stype.pipeline.get(pipeline_code)
        if self.pipeline:
            return self.pipeline
        else:
            pipeline_code = self.sobject.info.get('pipeline_code')
            pipeline = self.stype.pipeline.get(pipeline_code)
            return pipeline

    def set_drop_indicator_on(self):
        if self.drop_wdg.isHidden():
            self.lay = QtGui.QVBoxLayout(self.drop_wdg)
            self.lay.setSpacing(0)
            self.lay.setContentsMargins(0, 0, 0, 0)
            self.drop_wdg.setLayout(self.lay)
            self.drop_wdg.setStyleSheet('QLabel {padding: 0px;border: 0px dashed grey; background-color: rgba(0,0,100,128);}')
            self.label = QtGui.QLabel('DROP HERE')
            self.lay.addWidget(self.label)
            self.drop_wdg.show()
            self.drop_wdg.resize(self.size())

    def set_drop_indicator_off(self):
        self.drop_wdg.setHidden(True)

    def fill_subprocesses(self):
        if self.process_info:
            if self.process_info.get('type') == 'hierarchy':
                child_pipeline = self.workflow.get_child_pipeline_by_process_code(
                    self.get_current_process_pipeline(),
                    self.process
                )
                self.add_process_items(child_pipeline)

    def set_notes_count(self, notes_count):
        if notes_count > 0:
            self.notesToolButton.setIcon(gf.get_icon('commenting'))
        self.notesToolButton.setText('| {0}'.format(notes_count))

    def show_notes_widget(self):
        project = self.sobject.get_project()
        notes_widget = env_inst.get_check_tree(project.get_code(), 'checkin_out_instanced_widgets', 'notes_dock')
        notes_widget.add_notes_tab(self.sobject, self.process)

    def get_current_results_widget(self):
        current_tree = self.search_widget.get_current_results_tree_widget()
        return current_tree

    def get_current_progress_bar(self):
        return self.search_widget.get_progress_bar()

    def get_depth(self):
        idx = 0
        item = self.tree_item

        while item.parent():
            item = item.parent()
            idx += 1

        return idx

    def get_row(self):
        return self.get_index().row()

    def get_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item.parent())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_results_widget()
        parent_item_widget = current_tree.itemWidget(self.tree_item.parent(), 0)
        return parent_item_widget

    def collapse_self(self):
        parent = self.get_parent_item()
        return parent.takeChild(self.get_index().row())

    def collapse_all_children(self):
        return self.tree_item.takeChildren()

    def add_process_items(self, pipeline):

        # TODO when i get my hands to recursive filtering, make it respect filtering.

        # processes = []
        # pipeline_code = self.sobject.info.get('pipeline_code')
        # if pipeline_code and self.stype.pipeline:
        processes = []
        if pipeline:
            processes = pipeline.process.keys()

        # if self.ignore_dict:
        #     if self.ignore_dict['show_builtins']:
        #         show_all = True
        #         for builtin in ['icon', 'attachment', 'publish']:
        #             if builtin not in self.ignore_dict['builtins']:
        #                 processes.append(builtin)
        #                 show_all = False
        #         if show_all:
        #             processes.extend(['icon', 'attachment', 'publish'])

        # progress_bar = self.get_current_progress_bar()
        # progress_bar.setVisible(True)
        for i, process in enumerate(processes):
            ignored = False
            # if self.ignore_dict:
            #     if process in self.ignore_dict['processes'].get(pipeline_code):
            #         ignored = True
            if not ignored:
                # print self.tree_item.treeWidget()
                # print 'adding', process
                process_item = gf.add_process_item(
                    self.tree_item,
                    self.search_widget,
                    self.sobject,
                    self.stype,
                    process,
                    self.info,
                    pipeline=pipeline
                )
                self.process_items.append(process_item)
                process_item.fill_subprocesses()
                # progress_bar.setValue(int(i * 100 / len(processes)))

        # progress_bar.setVisible(False)

    def fill_snapshots_items(self):
        # print self.children_states, 'CHILDREN STATES, fill_snapshots_items'
        # progress_bar = self.get_current_progress_bar()
        # progress_bar.setVisible(True)
        # adding snapshots per process

        # import time
        # start = time.time()

        for i, proc in enumerate(self.process_items):
            # progress_bar.setValue(int(i * 100 / len(self.process_items)))
            for key, val in self.sobject.process.iteritems():
                # because it is dict, items could be in any position
                if key == proc.process:
                    proc.add_snapshots_items(val)

        # progress_bar.setVisible(False)

        # print time.time() - start

    def add_snapshots_items(self, snapshots):

        return gf.add_snapshot_item(
            self.tree_item,
            self.search_widget,
            self.sobject,
            self.stype,
            self.process,
            self.pipeline,
            snapshots,
            self.info,
            self.sep_versions,
            False,
        )
        # if self.children_states:
        #     gf.tree_state_revert(self.tree_item, self.children_states)

    # def update_items(self):
    #     self.sobject.update_snapshots()
    #     self.collapse_all_children()
    #
    #     gf.add_snapshot_item(
    #         self.tree_item,
    #         self.search_widget,
    #         self.sobject,
    #         self.stype,
    #         self.process,
    #         self.pipeline,
    #         self.sobject.process.get(self.process),
    #         self.info,
    #         self.sep_versions,
    #         False,
    #     )

    def prnt(self):
        # print(str(self.item_index))
        # print(self.tree_item.parent().setExpanded(False))
        print(self.sobject.process)
        self.sobject.update_snapshots()
        print(self.sobject.process)

    def get_snapshots(self, versionless=True):
        process = self.get_current_process()
        if process:
            contexts = process.get_contexts()
            snapshots = []
            if contexts:
                for context in contexts.values():
                    if versionless:
                        snapshots.append(context.get_versionless())
                    else:
                        snapshots.append(context.get_versions())
                return snapshots

    def get_context(self, process=False, custom=None):

        # pipeline = self.get_current_process_pipeline()
        # print pipeline.get_pipeline()
        # print pipeline.get_process(self.process)
        # print pipeline.get_info()
        # print pipeline.get_processes()

        if process:
            if custom:
                return u'{0}/{1}'.format(self.process, custom)
            else:
                return self.process
                # else:
                #     return ''

    def get_context_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process(self.process)
        if process:
            context_options = process.get('context_options')
            if context_options:
                return context_options.split('|')

    def get_checkin_mode_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process(self.process)
        if process:
            return process.get('checkin_mode')

    def get_description(self):
        return 'No Description for this item "{0}"'.format(self.process)

    def get_skey(self, skey=False, only=False, parent=False):
        if parent or only:
            return self.sobject.info['__search_key__']
        if skey:
            return 'skey://' + self.sobject.info['__search_key__']

    def get_search_key(self):
        return self.sobject.info.get('__search_key__')

    def get_parent_search_key(self):
        pass

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

    @gf.catch_error
    def expand_tree_item(self):
        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            self.fill_snapshots_items()

        # if self.process_items:
        self.get_notes_count()

    @gf.catch_error
    def expand_recursive(self):
        gf.tree_recursive_expand(self.tree_item, True)

    @gf.catch_error
    def collapse_recursive(self):
        gf.tree_recursive_expand(self.tree_item, False)

    def collapse_tree_item(self):
        pass

    def is_checked(self):
        return False

    def mouseDoubleClickEvent(self, event):
        do_dbl_click = None
        if self.relates_to == 'checkin_out':
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin_out(), 'doubleClickSaveCheckBox')

        if not do_dbl_click:
            super(Ui_processItemWidget, self).mouseDoubleClickEvent(event)
        else:
            if self.relates_to == 'checkin_out':
                self.search_widget.save_file()

    def showEvent(self, event):
        if not self.created:
            self.created = True
            self.create_ui()
        event.accept()

    def closeEvent(self, event):
        self.closed = True
        self.deleteLater()
        event.accept()


class Ui_snapshotItemWidget(QtGui.QWidget, ui_item_snapshot.Ui_snapshotItem):
    def __init__(self, sobject, stype, process, pipeline, context, snapshot, info, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.created = False
        self.type = 'snapshot'
        self.sobject = sobject
        self.stype = stype
        self.process = process
        self.pipeline = pipeline
        self.context = context
        self.snapshot = None
        self.current_snapshot = snapshot
        self.info = info
        self.tree_item = None
        self.expand_state = False
        self.selected_state = False
        self.multiple_checkin = False
        self.have_watch_folder = False

        self.search_widget = None

        self.relates_to = 'checkin_out'

        self.files = {}

        if snapshot:
            self.snapshot = snapshot[0].snapshot
            self.files = snapshot[0].files

        # self.create_ui()

    def get_type(self):
        return self.type

    def create_ui(self):
        # self.drop_wdg = QtGui.QWidget(self)
        # self.drop_wdg.setHidden(True)

        self.setMinimumWidth(260)

        self.create_item_info_widget()

        self.dateLabel = self.get_item_info_label()
        self.dateLabel.setAlignment(QtCore.Qt.AlignRight)
        self.verLabel = self.get_item_info_label()
        self.verLabel.setTextFormat(QtCore.Qt.RichText)
        self.revLabel = self.get_item_info_label()
        self.revLabel.setTextFormat(QtCore.Qt.RichText)
        self.repoLabel = self.get_item_info_label()
        self.repoLabel.setTextFormat(QtCore.Qt.RichText)

        self.itemColorLine.setStyleSheet('QFrame { border: 0px; background-color: black;}')

        # print 'Checkin expand state of SNAPSHOT Item from within'
        # self.check_expand_state()

        if self.snapshot:

            self.item_info_widget.add_item_to_right(self.dateLabel)
            if gf.get_ver_rev(ver=self.snapshot['version'], rev=0):
                self.item_info_widget.add_item(self.verLabel)
            if gf.get_ver_rev(rev=self.snapshot['revision'], ver=0):
                self.item_info_widget.add_item(self.revLabel)
            if self.snapshot.get('repo'):
                self.sizeLabel.setStyleSheet(self.get_repo_color())
                repo_name = env_tactic.get_base_dir(self.snapshot['repo'])['value'][1]
                hex_color = ['{:02x}'.format(i) for i in self.get_repo_color(True)]
                self.repoLabel.setTextFormat(QtCore.Qt.RichText)
                self.repoLabel.setText('<span style="color:#{0};">{1}</span>'.format(
                    ''.join(hex_color),
                    repo_name
                ))
                self.item_info_widget.add_item(self.repoLabel)

            self.check_main_file()

            limit_enabled = bool(gf.get_value_from_config(cfg_controls.get_checkin(), 'snapshotDescriptionLimitCheckBox'))
            limit = gf.get_value_from_config(cfg_controls.get_checkin(), 'snapshotDescriptionLimitSpinBox')
            if limit_enabled:
                self.commentLabel.setText(gf.to_plain_text(self.snapshot['description'], limit))
            else:
                self.commentLabel.setText(gf.to_plain_text(self.snapshot['description'], None))
            self.dateLabel.setText(self.snapshot['timestamp'].split('.')[0].replace(' ', ' \n'))
            self.authorLabel.setText(self.snapshot['login'] + ':')
            self.verLabel.setText(gf.get_ver_rev(ver=self.snapshot['version'], rev=0))
            self.revLabel.setText(gf.get_ver_rev(rev=self.snapshot['revision'], ver=0))

            hidden = ['icon', 'web', 'playblast']
            snapshot = self.get_snapshot()
            files_objects = snapshot.get_files_objects(group_by='type')

            for key, fls in files_objects.items():
                if key not in hidden:
                    if len(fls) > 1:
                        self.fill_info_with_multiple_checkin(fls)
                    elif len(fls) != 0:
                        if fls[0].is_meta_file_obj():
                            file_obj = fls[0].get_meta_file_object()
                            self.fill_info_with_meta_file_object(file_obj, fls[0])
                        else:
                            self.fill_info_with_tactic_file_object(fls[0])
            self.highlight_xontext_in_file_name()
        else:
            if self.get_checkin_mode_options() == 'multi_file':
                self.set_multiple_files_view()
            else:
                self.set_no_versionless_view()

    def set_drop_indicator_on(self):
        if self.drop_wdg.isHidden():
            self.lay = QtGui.QVBoxLayout(self.drop_wdg)
            self.lay.setSpacing(0)
            self.lay.setContentsMargins(0, 0, 0, 0)
            self.drop_wdg.setLayout(self.lay)
            self.drop_wdg.setStyleSheet('QLabel {padding: 0px;border: 0px dashed grey; background-color: rgba(0,0,100,128);}')
            self.label = QtGui.QLabel('DROP HERE')
            self.lay.addWidget(self.label)
            self.drop_wdg.show()
            self.drop_wdg.resize(self.size())

    def set_drop_indicator_off(self):
        self.drop_wdg.setHidden(True)

    def highlight_xontext_in_file_name(self):
        context = self.get_context()
        file_name_text = self.fileNameLabel.text()
        if file_name_text and context:
            until_context = file_name_text.find(context)
            if until_context != -1:
                self.fileNameLabel.setTextFormat(QtCore.Qt.RichText)
                first_part = file_name_text[:until_context]
                second_part = file_name_text[len(first_part) + len(context):]

                highlighted_text = '{0}<font color="{1}">{2}</font>{3}'.format(first_part, '#808080', context, second_part)
                self.fileNameLabel.setText(highlighted_text)

    def fill_info_with_multiple_checkin(self, files_list):
        self.set_is_multiple_checkin(True)
        pixmap = gf.get_icon('folder', icons_set='ei', opacity=0.5, scale_factor=0.5).pixmap(64, Qt4Gui.QIcon.Normal)
        self.previewLabel.setPixmap(pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation))
        self.fileNameLabel.setText('Multiple files | {0}'.format(len(files_list)))
        self.sizeLabel.deleteLater()

    def fill_info_with_meta_file_object(self, meta_file_object, tactic_file_object):
        if not self.isEnabled():
            self.fileNameLabel.setText('{0}, (File Offline)'.format(meta_file_object.get_pretty_file_name()))
        else:
            self.fileNameLabel.setText(meta_file_object.get_pretty_file_name())

        self.sizeLabel.setText(gf.sizes(tactic_file_object.get_file_size()))

        if gf.get_value_from_config(cfg_controls.get_checkin(), 'getPreviewsThroughHttpCheckbox') == 1:
            self.set_web_preview(tactic_file_object)
        else:
            self.set_preview(tactic_file_object)
            # file_ext = tactic_file_object.get_ext()
            # if not file_ext:
            #     file_ext = 'err'
            # self.previewLabel.setText(
            #     '<span style=" font-size:12pt; font-weight:600; color:#828282;">{0}</span>'.format(file_ext))

        # getting extra info from meta
        seq_range = meta_file_object.get_sequence_frameranges_string(brackets='[]')
        frames_count = meta_file_object.get_sequence_lenght()
        layer = meta_file_object.get_layer()
        tiles = meta_file_object.get_tiles_count()
        metadata = tactic_file_object.get_metadata()
        maya_version = None
        if metadata:
            app_info = metadata.get('app_info')
            if app_info:
                maya_version = app_info.get('p')
        snapshot = self.get_snapshot()
        if snapshot:
            if snapshot.is_latest():
                self.isLatestLabel = self.get_item_info_label()
                self.isLatestLabel.setTextFormat(QtCore.Qt.RichText)
                self.isLatestLabel.setText('<span style="color:#2eb82e;">Latest</span>')
                self.item_info_widget.add_item(self.isLatestLabel)
        if seq_range:
            self.framerange_label = self.get_item_info_label()
            self.item_info_widget.add_item(self.framerange_label)
            self.framerange_label.setText(seq_range)
        if frames_count:
            self.frames_count_label = self.get_item_info_label()
            self.item_info_widget.add_item(self.frames_count_label)
            self.frames_count_label.setText('Frames: {0}'.format(frames_count))
        if layer:
            self.flayer_label = self.get_item_info_label()
            self.item_info_widget.add_item(self.flayer_label)
            self.flayer_label.setText(layer)
        if tiles:
            self.tiles_label = self.get_item_info_label()
            self.item_info_widget.add_item(self.tiles_label)
            self.tiles_label.setText('Tiles: {0}'.format(tiles))
        if maya_version:
            self.mayaVerLabel = self.get_item_info_label()
            self.item_info_widget.add_item(self.mayaVerLabel)
            self.mayaVerLabel.setText(maya_version)

    def fill_info_with_tactic_file_object(self, tactic_file_object):
        if not self.isEnabled():
            self.fileNameLabel.setText('{0}, (File Offline)'.format(tactic_file_object.get_filename_with_ext()))
        else:
            self.fileNameLabel.setText(tactic_file_object.get_filename_with_ext())

        self.sizeLabel.setText(gf.sizes(tactic_file_object.get_file_size()))

        if gf.get_value_from_config(cfg_controls.get_checkin(), 'getPreviewsThroughHttpCheckbox') == 1:
            self.set_web_preview()
        else:
            self.set_preview()
            # self.set_ext_preview()

    def set_ext_preview(self, tactic_file_object=None):
        if tactic_file_object:
            file_ext = tactic_file_object.get_ext()
            if not file_ext:
                file_ext = 'err'
            self.previewLabel.setText(
                '<span style=" font-size:12pt; font-weight:600; color:#828282;">{0}</span>'.format(file_ext))

    @staticmethod
    def get_item_info_label():
        font = Qt4Gui.QFont()
        font.setPointSize(7)
        label = QtGui.QLabel()
        label.setFont(font)
        label.setTextFormat(QtCore.Qt.PlainText)
        label.setAlignment(QtCore.Qt.AlignCenter)
        return label

    def create_item_info_widget(self):
        self.item_info_widget = Ui_infoItemsWidget(self)
        self.infoHorizontalLayout.addWidget(self.item_info_widget)

    def is_versionless(self):
        snapshot = self.get_snapshot()
        if snapshot:
            return snapshot.is_versionless()
        else:
            # only versionless can be displayed without snapshot!
            return True

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.selected_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def get_children_states(self):
        return self.info.get('children_states')

    def set_children_states(self, states):
        self.info['children_states'] = states

    def check_expand_state(self, state=None):
        # if not state:
        #     state = self.get_children_states()

        if state:
            expanded = state[self.get_row()]['d']['e']
            selected = state[self.get_row()]['d']['s']

            self.set_expand_state(expanded)
            self.set_selected_state(selected)

            for i in range(self.get_depth()):
                state = state[self.get_row()]['s']

            self.set_children_states(state)

    def set_is_multiple_checkin(self, is_multiple):
        self.multiple_checkin = is_multiple

    def get_is_multiple_checkin(self):
        return self.multiple_checkin

    def check_main_file(self):
        snapshot = self.get_snapshot()
        if snapshot:
            files_objects = snapshot.get_files_objects()
            if files_objects:
                first_file = files_objects[0]
                if first_file:
                    if first_file.is_meta_file_obj():
                        meta_file_object = first_file.get_meta_file_object()
                        if meta_file_object.is_exists():
                            self.setEnabled(True)
                        else:
                            self.setDisabled(True)
                    else:
                        if first_file.is_exists():
                            self.setEnabled(True)
                        else:
                            self.setDisabled(True)

    def set_multiple_files_view(self):
        pixmap = gf.get_icon('folder-sign', icons_set='ei', opacity=0.5, scale_factor=0.5).pixmap(64, Qt4Gui.QIcon.Normal)
        self.previewLabel.setPixmap(pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation))
        self.fileNameLabel.setText('Multiple checkin: {0} '.format(self.context))
        self.commentLabel.setText('Snapshots count: {0}; Files count: {1};'.format(len(self.get_all_versions_snapshots()), len(self.get_all_versions_files())))

        self.dateLabel.deleteLater()
        self.sizeLabel.deleteLater()
        self.authorLabel.deleteLater()

    def set_no_versionless_view(self):
        pixmap = gf.get_icon('exclamation-circle', opacity=0.5, scale_factor=0.6).pixmap(64, Qt4Gui.QIcon.Normal)
        self.previewLabel.setPixmap(pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation))
        self.fileNameLabel.setText('Commit without versionless in {0}'.format(self.context))
        self.commentLabel.setText('Versionless for this commit is not present')
        self.dateLabel.deleteLater()
        self.sizeLabel.deleteLater()
        self.authorLabel.deleteLater()

    def set_preview(self, tactic_file_object=None):
        snapshot = self.get_snapshot()
        if snapshot:
            preview_files_objects = snapshot.get_files_objects(group_by='type').get('icon')
            if preview_files_objects:
                icon_previw = preview_files_objects[0].get_icon_preview()
                if icon_previw:
                    if not self.set_preview_pixmap(icon_previw):
                        self.set_ext_preview(tactic_file_object)

    def set_web_preview(self, tactic_file_object=None):
        snapshot = self.get_snapshot()
        if snapshot:
            preview_files_objects = snapshot.get_files_objects(group_by='type').get('icon')
            if preview_files_objects:
                icon_previw = preview_files_objects[0].get_icon_preview()
                if icon_previw:
                    if os.path.exists(icon_previw.get_full_abs_path()):
                        if icon_previw.get_file_size() == icon_previw.get_file_size(True):
                            self.set_preview()
                        else:
                            self.download_and_set_preview_file(icon_previw)
                    else:
                        self.download_and_set_preview_file(icon_previw)
            else:
                self.set_ext_preview(tactic_file_object)

    def download_and_set_preview_file(self, file_object):
        repo_sync_item = env_inst.ui_repo_sync_queue.download_file_object(file_object)
        repo_sync_item.downloaded.connect(self.set_preview_pixmap)
        repo_sync_item.download()

    def set_preview_pixmap(self, file_object):
        pixmap = self.get_preview_pixmap(file_object.get_full_abs_path())
        if pixmap:
            self.previewLabel.setPixmap(pixmap)
            return True
        else:
            return False

    def get_preview_pixmap(self, image_path):
        pixmap = Qt4Gui.QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(64, QtCore.Qt.SmoothTransformation)

            painter = Qt4Gui.QPainter()
            pixmap_mask = Qt4Gui.QPixmap(64, 64)
            pixmap_mask.fill(QtCore.Qt.transparent)
            painter.begin(pixmap_mask)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.setBrush(Qt4Gui.QBrush(Qt4Gui.QColor(0, 0, 0, 255)))
            painter.drawRoundedRect(QtCore.QRect(0, 0, 64, 64), 4, 4)
            painter.end()

            rounded_pixmap = Qt4Gui.QPixmap(pixmap.size())
            rounded_pixmap.fill(QtCore.Qt.transparent)
            painter.begin(rounded_pixmap)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.drawPixmap(QtCore.QRect((pixmap.width() - 64) / 2, 0, 64, 64), pixmap_mask)
            painter.setCompositionMode(Qt4Gui.QPainter.CompositionMode_SourceIn)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            return rounded_pixmap

    def get_all_versions_snapshots(self):
        process = self.sobject.process.get(self.process)
        context = process.contexts.get(self.context)
        return context.versions

    def get_all_versions_files(self):
        files = []
        for sn in self.get_all_versions_snapshots().values():
            files.extend(sn.get_files_objects())

        return files

    def get_snapshot(self):
        if self.current_snapshot:
            return self.current_snapshot[0]

    def get_current_results_widget(self):
        current_tree = self.search_widget.get_current_results_tree_widget()
        return current_tree

    def get_depth(self):
        idx = 0
        item = self.tree_item

        while item.parent():
            item = item.parent()
            idx += 1

        return idx

    def get_row(self):
        return self.get_index().row()

    def get_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.get_parent_item())

    def get_parent_item(self):
        # temporary duckt tape
        self.tree_item = self.get_current_results_widget().currentItem()
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_results_widget()
        parent_item_widget = current_tree.itemWidget(self.get_parent_item(), 0)
        return parent_item_widget

    def collapse_self(self):
        parent = self.get_parent_item()
        return parent.takeChild(self.get_index().row())

    def collapse_all_children(self):
        return self.tree_item.takeChildren()

    # def update_items(self):
    #     self.sobject.update_snapshots()
    #
    #     parent_item_widget = self.get_parent_item_widget()
    #     if parent_item_widget:
    #         if parent_item_widget.type == 'snapshot':
    #             # if we have snapshot, so go upper to get parent of upper snapshot
    #             parent_item_widget = parent_item_widget.get_parent_item_widget()
    #             # TODO. SOMETHING STRANGE HERE, we need to refresh after update
    #             if parent_item_widget != self:
    #                 parent_item_widget.update_items()
    #         else:
    #             parent_item_widget.update_items()

    def get_repo_color(self, only_color=False):
        config = cfg_controls.get_checkin()
        if config:
            repo_colors = env_tactic.get_base_dir(self.snapshot['repo'])['value'][2]
        else:
            repo_colors = [96, 96, 96]
        if only_color:
            return repo_colors
        stylesheet = 'QLabel{background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(%s, %s, %s, 96));' \
                     'border - bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));' \
                     'padding: 0px;}' % tuple(repo_colors)

        return stylesheet

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return u'{0}/{1}'.format(self.process, custom)
            else:
                return self.process
        else:
            context = self.context.split('/')[-1]
            if context == self.process:
                context = ''
            return context

    def get_context_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process(self.process)
        if process:
            context_options = process.get('context_options')
            if context_options:
                return context_options.split('|')

    def get_checkin_mode_options(self):
        pipeline = self.get_current_process_pipeline()
        process = None
        if pipeline:
            process = pipeline.get_process(self.process)
        if process:
            return process.get('checkin_mode')

    def get_current_process_pipeline(self):
        if self.pipeline:
            return self.pipeline
        else:
            pipeline_code = self.sobject.info.get('pipeline_code')
            if pipeline_code and self.stype.pipeline:
                return self.stype.pipeline.get(pipeline_code)

    def get_current_process_info(self):
        pipeline = self.get_current_process_pipeline()
        process_info = None
        if pipeline:
            process_info = pipeline.process.get(self.process)
        if not process_info and self.process:
            process_info = {'name': self.process}

        return process_info

    def get_full_process_list(self):
        pipeline = self.get_current_process_pipeline()
        if pipeline:
            return pipeline.process

    def get_process_list(self):
        pipeline = self.get_current_process_pipeline()
        if pipeline:
            return pipeline.process.keys()
        else:
            return []

    def get_search_key(self):
        if self.snapshot:
            return self.snapshot.get('__search_key__')

    def get_parent_search_key(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_search_key()

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

    def delete_current_sobject(self):

        snapshot = self.get_snapshot()
        # print 'DELETING FROM ITEM', snapshot
        snapshot.delete_sobject()

    def get_skey(self, skey=False, only=False, parent=False):
        """skey://sthpw/snapshot?code=SNAPSHOT00000028"""
        if self.snapshot:
            if only:
                return self.snapshot['__search_key__']
            if skey:
                return 'skey://{0}'.format(self.snapshot['__search_key__'])
        if parent:
            return self.sobject.info['__search_key__']
        else:
            return 'skey://{0}'.format(self.sobject.info['__search_key__'])

    def get_description(self):
        if self.snapshot:
            return self.snapshot['description']
        else:
            return 'No Description for this item!'

    def update_description(self, new_description):
        self.snapshot['description'] = new_description
        self.commentLabel.setText(new_description)

    @gf.catch_error
    def expand_tree_item(self):
        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

    @gf.catch_error
    def expand_recursive(self):
        gf.tree_recursive_expand(self.tree_item, True)

    @gf.catch_error
    def collapse_recursive(self):
        gf.tree_recursive_expand(self.tree_item, False)

    def collapse_tree_item(self):
        pass

    def is_checked(self):
        return False
        # return self.selectedCheckBox.isChecked()

    # def resizeEvent(self, event):
    #     self.tree_item.setSizeHint(0, QtCore.QSize(self.width(), 25 + self.commentLabel.height()))

    def mouseDoubleClickEvent(self, event):
        if self.relates_to == 'checkin_out':
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin_out(), 'doubleClickSaveCheckBox')
        else:
            do_dbl_click = gf.get_value_from_config(cfg_controls.get_checkin_out(), 'doubleClickOpenCheckBox')

        if not do_dbl_click:
            super(Ui_snapshotItemWidget, self).mouseDoubleClickEvent(event)
        else:
            if self.relates_to == 'checkin_out':
                self.search_widget.save_file()
            else:
                self.search_widget.open_file()

    def showEvent(self, event):
        if not self.created:
            self.created = True
            self.create_ui()
        event.accept()

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_childrenItemWidget(QtGui.QWidget):
    def __init__(self, sobject, stype, child, info, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        # self.setupUi(self)

        self.created = False
        self.type = 'child'
        self.sobject = sobject
        self.stype = stype
        self.child = child
        self.info = info
        self.tree_item = None

        self.expand_state = False
        self.selected_state = False

        self.search_widget = None
        self.project = self.stype.get_project()

        self.create_layout()
        self.customize_ui()

    def get_type(self):
        return self.type

    def create_ui(self):
        # self.drop_wdg = QtGui.QWidget(self)

        self.tree_item.setExpanded = self.tree_item_set_expanded_override

        self.controls_actions()

    # def set_drop_indicator_on(self):
    #     if self.drop_wdg.isHidden():
    #         self.lay = QtGui.QVBoxLayout(self.drop_wdg)
    #         self.lay.setSpacing(0)
    #         self.lay.setContentsMargins(0, 0, 0, 0)
    #         self.drop_wdg.setLayout(self.lay)
    #         self.drop_wdg.setStyleSheet('QLabel {padding: 0px;border: 0px dashed grey; background-color: rgba(0,0,100,128);}')
    #         self.label = QtGui.QLabel('DROP HERE')
    #         self.lay.addWidget(self.label)
    #         self.drop_wdg.show()
    #         self.drop_wdg.resize(self.size())
    #
    # def set_drop_indicator_off(self):
    #     self.drop_wdg.setHidden(True)

    def customize_ui(self):
        self.setMinimumWidth(260)

        self.create_children_tool_button()

        self.create_link_sobjects_button()

        self.create_add_sobjects_button()

    def create_layout(self):
        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.resize(52, 25)
        self.setStyleSheet("QTreeView::item {border-width: 0px;    border-radius: 0px;padding: 0px;}")

    def create_children_tool_button(self):

        title = self.stype.get_pretty_name()
        if not title:
                title = 'untitled'
        self.title = title.capitalize()

        clr = self.stype.get_stype_color(tuple=True)
        stype_color = None
        if clr:
            stype_color = Qt4Gui.QColor(clr[0], clr[1], clr[2], 255)

        self.childrenToolButton = QtGui.QToolButton(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.childrenToolButton.sizePolicy().hasHeightForWidth())
        self.childrenToolButton.setSizePolicy(sizePolicy)
        self.childrenToolButton.setMinimumSize(QtCore.QSize(0, 24))
        self.childrenToolButton.setMaximumSize(QtCore.QSize(16777215, 24))
        self.childrenToolButton.setCheckable(False)
        self.childrenToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.childrenToolButton.setObjectName("childrenToolButton")
        self.childrenToolButton.setIcon(gf.get_icon('view-sequential', color=stype_color, icons_set='mdi', scale_factor=1.1))
        self.childrenToolButton.setText(self.title)
        self.childrenToolButton.setStyleSheet('QToolButton {background-color: transparent;}')

        self.horizontalLayout.addWidget(self.childrenToolButton)

    def create_link_sobjects_button(self):
        self.link_sobjects_tool_button = QtGui.QToolButton(self)
        self.link_sobjects_tool_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.link_sobjects_tool_button.setAutoRaise(True)
        self.link_sobjects_tool_button.setMinimumSize(QtCore.QSize(22, 22))
        self.link_sobjects_tool_button.setMaximumSize(QtCore.QSize(28, 22))

        self.link_sobjects_tool_button.setObjectName("link_sobjects_tool_button")
        self.link_sobjects_tool_button.setIcon(gf.get_icon('link-variant', icons_set='mdi'))

        self.horizontalLayout.addWidget(self.link_sobjects_tool_button)

        self.link_sobjects_tool_button.setHidden(True)  # hidden by default

        if self.child.get('relationship') == 'instance':
            self.link_sobjects_tool_button.setHidden(False)

    def create_add_sobjects_button(self):
        self.add_sobjects_tool_button = QtGui.QToolButton(self)
        self.add_sobjects_tool_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.add_sobjects_tool_button.setAutoRaise(True)
        self.add_sobjects_tool_button.setObjectName("link_sobjects_tool_button")
        self.add_sobjects_tool_button.setIcon(gf.get_icon('plus-square-o'))

        self.horizontalLayout.addWidget(self.add_sobjects_tool_button)

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.selected_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def get_children_states(self):
        return self.info.get('children_states')

    def set_children_states(self, states):
        self.info['children_states'] = states

    # def check_expand_state(self, state=None):
    #     # if not state:
    #     #     state = self.get_children_states()
    #
    #     if state:
    #         from pprint import pprint
    #         pprint(state)
    #
    #         # expanded = state[self.get_row()]['d']['e']
    #         # selected = state[self.get_row()]['d']['s']
    #         #
    #         # self.set_expand_state(expanded)
    #         # self.set_selected_state(selected)
    #         #
    #         # for i in range(self.get_depth()):
    #         #     state = state[self.get_row()]['s']
    #         #
    #         # self.set_children_states(state)

    def tree_item_set_expanded_override(self, state):
        if state:
            self.toggle_cildren_button()
        self.tree_item.treeWidget().setItemExpanded(self.tree_item, state)

    def controls_actions(self):
        self.childrenToolButton.clicked.connect(self.toggle_cildren_button)
        self.add_sobjects_tool_button.clicked.connect(self.add_new_sobject)
        self.link_sobjects_tool_button.clicked.connect(self.link_sobjects)

    def set_child_count_title(self, count):
        if count > 0:
            self.add_sobjects_tool_button.setIcon(gf.get_icon('plus-square'))
            self.tree_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        self.add_sobjects_tool_button.setText('| {0}'.format(count))

    @gf.catch_error
    def add_new_sobject(self):

        self.add_sobject = ui_addsobject_classes.Ui_addTacticSobjectWidget(
            stype=self.stype,
            parent_stype=self.search_widget.stype,
            item=self,
            parent=self)

        self.add_sobject.show()

    @gf.catch_error
    def link_sobjects(self):
        link_sobjects_widget = ui_addsobject_classes.Ui_linkSobjectsWidget(
            stype=self.stype,
            parent_stype=self.search_widget.stype,
            item=self,
            parent=env_inst.ui_main)

        link_sobjects_widget.show()

    @gf.catch_error
    def expand_tree_item(self):
        # if not self.info['is_expanded']:
        #     self.info['is_expanded'] = True

        self.add_child_sobjects()
        self.childrenToolButton.setCheckable(True)
        self.childrenToolButton.setChecked(True)

    @gf.catch_error
    def expand_recursive(self):
        gf.tree_recursive_expand(self.tree_item, True)

    @gf.catch_error
    def collapse_recursive(self):
        gf.tree_recursive_expand(self.tree_item, False)

    def collapse_tree_item(self):
        self.childrenToolButton.setChecked(False)

    def get_current_results_widget(self):
        current_tree = self.search_widget.get_current_results_tree_widget()
        return current_tree

    def get_depth(self):
        idx = 0
        item = self.tree_item

        while item.parent():
            item = item.parent()
            idx += 1

        return idx

    def get_row(self):
        return self.get_index().row()

    def get_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item.parent())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_results_widget()
        parent_item_widget = current_tree.itemWidget(self.tree_item.parent(), 0)
        return parent_item_widget

    @gf.catch_error
    def toggle_cildren_button(self):
        if self.tree_item.isExpanded():
            self.tree_item.treeWidget().setItemExpanded(self.tree_item, False)
            self.childrenToolButton.setChecked(False)
            # self.childrenToolButton.setArrowType(QtCore.Qt.RightArrow)
        else:
            self.add_child_sobjects()
            if self.tree_item.childCount() > 0:
                self.childrenToolButton.setCheckable(True)
                self.tree_item.treeWidget().setItemExpanded(self.tree_item, True)
                self.childrenToolButton.setChecked(True)
                # self.childrenToolButton.setArrowType(QtCore.Qt.DownArrow)

    def get_relationship(self):
        relationship = self.child.get('relationship')

        child_col = self.child.get('from_col')
        # instance_type = None
        # related_type = None

        if relationship and not child_col:
            if relationship == 'search_type':
                child_col = 'search_code'
            elif relationship == 'code':
                child_col = '{0}_code'.format(self.child.get('to').split('/')[-1])
            elif relationship == 'instance':
                child_col = 'code'
                # instance_type = self.child.get('instance_type')
                # related_type = self.child.get('to')

            return relationship


    def add_child_sobjects(self):

        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            # TODO The whole thing can be replace with this one
            # self.sobject.get_related_sobjects(child_stype=self.stype)

            relationship = self.child.get('relationship')

            child_col = self.child.get('from_col')
            instance_type = None
            related_type = None

            if relationship and not child_col:
                if relationship == 'search_type':
                    child_col = 'search_code'
                elif relationship == 'code':
                    child_col = '{0}_code'.format(self.child.get('to').split('/')[-1])
                elif relationship == 'instance':
                    child_col = 'code'
                    instance_type = self.child.get('instance_type')
                    related_type = self.child.get('to')

            child_code = self.sobject.info.get('code')

            # may be it is workaround, but i can't see any faster way
            # if parent-child switched in schema we search another direction
            # TODO It is workaroud and should be rewritten
            if self.sobject.info.get('relative_dir') == self.child.get('to'):
                if self.child.get('to_col'):
                    child_code = self.sobject.info.get(self.child.get('to_col'))

            filters = [(child_col, child_code)]

            order_bys = ['name']
            built_process = tc.server_start(project=self.project.get_code()).build_search_type(self.child.get('from'), self.project.get_code())

            # Logging info
            dl.log('Getting children for {}'.format(self.stype.get_pretty_name()), group_id=self.stype.get_code())
            if instance_type:
                runtime_command = 'thenv.get_tc().get_sobjects_new(search_type="{0}", filters={1}, order_bys={2}, instance_type={3}, related_type={4})'.format(built_process, filters, order_bys, instance_type, related_type)
            else:
                runtime_command = 'thenv.get_tc().get_sobjects_new(search_type="{0}", filters={1}, order_bys={2})'.format(
                    built_process, filters, order_bys)
            dl.info(runtime_command, group_id=self.stype.get_code())

            def get_sobjects_agent():
                return tc.get_sobjects_new(
                    search_type=built_process,
                    filters=filters,
                    order_bys=order_bys,
                    instance_type=instance_type,
                    related_type=related_type,
                )

            get_sobjects_worker = gf.get_thread_worker(
                get_sobjects_agent,
                env_inst.get_thread_pool('server_query/http_download_pool'),
                result_func=self.fill_child_items,
                # progress_func=self.download_progress,
                error_func=gf.error_handle,
            )
            get_sobjects_worker.start()

    def fill_child_items(self, sobjects):
        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Filling SObjects</span>')
        sobject_item_widget = self.get_parent_item_widget()
        ignore_dict = None
        if sobject_item_widget:
            ignore_dict = sobject_item_widget.ignore_dict

        for i, sobject in enumerate(sobjects[0].itervalues()):
            children_states = None
            if self.info['children_states']:
                children_states = self.info['children_states'].get(i)
            item_info_dict = {
                'relates_to': self.info['relates_to'],
                'is_expanded': self.info['is_expanded'],
                'sep_versions': self.info['sep_versions'],
                'children_states': children_states,
                'simple_view': False,
            }
            gf.add_sobject_item(
                self.tree_item,
                self.search_widget,
                sobject,
                self.stype,
                item_info_dict,
                ignore_dict=ignore_dict
            )
            # if i+1 % 20 == 0:
            #     QtGui.QApplication.processEvents()

        env_inst.ui_main.set_info_status_text('')

    def get_skey(self, skey=False, only=False, parent=False):
        pass

    def get_description(self):
        return 'No Description for this item "{0}"'.format('AZAZAZ')

    def is_checked(self):
        return False

    def get_search_key(self):
        return self.sobject.info.get('__search_key__')

    def get_parent_search_key(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_search_key()

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

    def showEvent(self, event):
        if not self.created:
            self.created = True
            self.create_ui()
        event.accept()

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_groupItemWidget(QtGui.QWidget):
    def __init__(self, sobject, stype, info, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        # self.setupUi(self)

        self.created = False
        self.type = 'group'
        self.sobject = sobject
        self.stype = stype
        # self.child = child
        self.info = info
        self.tree_item = None

        self.expand_state = False
        self.selected_state = False

        self.search_widget = None
        self.project = self.stype.get_project()

        self.create_layout()
        self.customize_ui()

    def get_type(self):
        return self.type

    def create_ui(self):
        # self.drop_wdg = QtGui.QWidget(self)

        self.tree_item.setExpanded = self.tree_item_set_expanded_override

        self.controls_actions()

    # def set_drop_indicator_on(self):
    #     if self.drop_wdg.isHidden():
    #         self.lay = QtGui.QVBoxLayout(self.drop_wdg)
    #         self.lay.setSpacing(0)
    #         self.lay.setContentsMargins(0, 0, 0, 0)
    #         self.drop_wdg.setLayout(self.lay)
    #         self.drop_wdg.setStyleSheet('QLabel {padding: 0px;border: 0px dashed grey; background-color: rgba(0,0,100,128);}')
    #         self.label = QtGui.QLabel('DROP HERE')
    #         self.lay.addWidget(self.label)
    #         self.drop_wdg.show()
    #         self.drop_wdg.resize(self.size())
    #
    # def set_drop_indicator_off(self):
    #     self.drop_wdg.setHidden(True)

    def customize_ui(self):
        self.setMinimumWidth(260)

        self.create_children_tool_button()

        # self.create_link_sobjects_button()

        # self.create_add_sobjects_button()

    def create_layout(self):
        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.resize(52, 25)
        self.setStyleSheet("QTreeView::item {border-width: 0px;    border-radius: 0px;padding: 0px;}")

    def create_children_tool_button(self):

        title = self.stype.get_pretty_name()
        if not title:
                title = 'untitled'
        self.title = title.capitalize()

        clr = self.stype.get_stype_color(tuple=True)
        stype_color = None
        if clr:
            stype_color = Qt4Gui.QColor(clr[0], clr[1], clr[2], 255)

        self.childrenToolButton = QtGui.QToolButton(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.childrenToolButton.sizePolicy().hasHeightForWidth())
        self.childrenToolButton.setSizePolicy(sizePolicy)
        self.childrenToolButton.setMinimumSize(QtCore.QSize(0, 24))
        self.childrenToolButton.setMaximumSize(QtCore.QSize(16777215, 24))
        self.childrenToolButton.setCheckable(False)
        self.childrenToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.childrenToolButton.setObjectName("childrenToolButton")
        self.childrenToolButton.setIcon(gf.get_icon('view-sequential', color=stype_color, icons_set='mdi', scale_factor=1.1))
        self.childrenToolButton.setText(self.title)
        self.childrenToolButton.setStyleSheet('QToolButton {background-color: transparent;}')

        self.horizontalLayout.addWidget(self.childrenToolButton)

    def create_link_sobjects_button(self):
        self.link_sobjects_tool_button = QtGui.QToolButton(self)
        self.link_sobjects_tool_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.link_sobjects_tool_button.setAutoRaise(True)
        self.link_sobjects_tool_button.setMinimumSize(QtCore.QSize(22, 22))
        self.link_sobjects_tool_button.setMaximumSize(QtCore.QSize(28, 22))

        self.link_sobjects_tool_button.setObjectName("link_sobjects_tool_button")
        self.link_sobjects_tool_button.setIcon(gf.get_icon('link-variant', icons_set='mdi'))

        self.horizontalLayout.addWidget(self.link_sobjects_tool_button)

        self.link_sobjects_tool_button.setHidden(True)  # hidden by default

        if self.child.get('relationship') == 'instance':
            self.link_sobjects_tool_button.setHidden(False)

    def create_add_sobjects_button(self):
        self.add_sobjects_tool_button = QtGui.QToolButton(self)
        self.add_sobjects_tool_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.add_sobjects_tool_button.setAutoRaise(True)
        self.add_sobjects_tool_button.setObjectName("link_sobjects_tool_button")
        self.add_sobjects_tool_button.setIcon(gf.get_icon('plus-square-o'))

        self.horizontalLayout.addWidget(self.add_sobjects_tool_button)

    def get_expand_state(self):
        return self.expand_state

    def set_expand_state(self, state):
        self.expand_state = state
        self.tree_item.setExpanded(state)

    def get_selected_state(self):
        return self.selected_state

    def set_selected_state(self, state):
        self.selected_state = state
        self.tree_item.setSelected(state)

    def get_children_states(self):
        return self.info.get('children_states')

    def set_children_states(self, states):
        self.info['children_states'] = states

    # def check_expand_state(self, state=None):
    #     # if not state:
    #     #     state = self.get_children_states()
    #
    #     if state:
    #         from pprint import pprint
    #         pprint(state)
    #
    #         # expanded = state[self.get_row()]['d']['e']
    #         # selected = state[self.get_row()]['d']['s']
    #         #
    #         # self.set_expand_state(expanded)
    #         # self.set_selected_state(selected)
    #         #
    #         # for i in range(self.get_depth()):
    #         #     state = state[self.get_row()]['s']
    #         #
    #         # self.set_children_states(state)

    def tree_item_set_expanded_override(self, state):
        if state:
            self.toggle_cildren_button()
        self.tree_item.treeWidget().setItemExpanded(self.tree_item, state)

    def controls_actions(self):
        self.childrenToolButton.clicked.connect(self.toggle_cildren_button)
        self.add_sobjects_tool_button.clicked.connect(self.add_new_sobject)
        self.link_sobjects_tool_button.clicked.connect(self.link_sobjects)

    def set_child_count_title(self, count):
        if count > 0:
            self.add_sobjects_tool_button.setIcon(gf.get_icon('plus-square'))
            self.tree_item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        self.add_sobjects_tool_button.setText('| {0}'.format(count))

    @gf.catch_error
    def add_new_sobject(self):

        self.add_sobject = ui_addsobject_classes.Ui_addTacticSobjectWidget(
            stype=self.stype,
            parent_stype=self.search_widget.stype,
            item=self,
            parent=self)

        self.add_sobject.show()

    @gf.catch_error
    def link_sobjects(self):
        link_sobjects_widget = ui_addsobject_classes.Ui_linkSobjectsWidget(
            stype=self.stype,
            parent_stype=self.search_widget.stype,
            item=self,
            parent=env_inst.ui_main)

        link_sobjects_widget.show()

    @gf.catch_error
    def expand_tree_item(self):
        # if not self.info['is_expanded']:
        #     self.info['is_expanded'] = True

        self.add_child_sobjects()
        self.childrenToolButton.setCheckable(True)
        self.childrenToolButton.setChecked(True)

    @gf.catch_error
    def expand_recursive(self):
        gf.tree_recursive_expand(self.tree_item, True)

    @gf.catch_error
    def collapse_recursive(self):
        gf.tree_recursive_expand(self.tree_item, False)

    def collapse_tree_item(self):
        self.childrenToolButton.setChecked(False)

    def get_current_results_widget(self):
        current_tree = self.search_widget.get_current_results_tree_widget()
        return current_tree

    def get_depth(self):
        idx = 0
        item = self.tree_item

        while item.parent():
            item = item.parent()
            idx += 1

        return idx

    def get_row(self):
        return self.get_index().row()

    def get_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item)

    def get_parent_index(self):
        current_tree = self.get_current_results_widget()
        return current_tree.indexFromItem(self.tree_item.parent())

    def get_parent_item(self):
        return self.tree_item.parent()

    def get_parent_item_widget(self):
        current_tree = self.get_current_results_widget()
        parent_item_widget = current_tree.itemWidget(self.tree_item.parent(), 0)
        return parent_item_widget

    @gf.catch_error
    def toggle_cildren_button(self):
        if self.tree_item.isExpanded():
            self.tree_item.treeWidget().setItemExpanded(self.tree_item, False)
            self.childrenToolButton.setChecked(False)
            # self.childrenToolButton.setArrowType(QtCore.Qt.RightArrow)
        else:
            self.add_child_sobjects()
            if self.tree_item.childCount() > 0:
                self.childrenToolButton.setCheckable(True)
                self.tree_item.treeWidget().setItemExpanded(self.tree_item, True)
                self.childrenToolButton.setChecked(True)
                # self.childrenToolButton.setArrowType(QtCore.Qt.DownArrow)

    def get_relationship(self):
        relationship = self.child.get('relationship')

        child_col = self.child.get('from_col')
        # instance_type = None
        # related_type = None

        if relationship and not child_col:
            if relationship == 'search_type':
                child_col = 'search_code'
            elif relationship == 'code':
                child_col = '{0}_code'.format(self.child.get('to').split('/')[-1])
            elif relationship == 'instance':
                child_col = 'code'
                # instance_type = self.child.get('instance_type')
                # related_type = self.child.get('to')

            return relationship


    def add_child_sobjects(self):

        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            # TODO The whole thing can be replace with this one
            # self.sobject.get_related_sobjects(child_stype=self.stype)

            relationship = self.child.get('relationship')

            child_col = self.child.get('from_col')
            instance_type = None
            related_type = None

            if relationship and not child_col:
                if relationship == 'search_type':
                    child_col = 'search_code'
                elif relationship == 'code':
                    child_col = '{0}_code'.format(self.child.get('to').split('/')[-1])
                elif relationship == 'instance':
                    child_col = 'code'
                    instance_type = self.child.get('instance_type')
                    related_type = self.child.get('to')

            child_code = self.sobject.info.get('code')

            # may be it is workaround, but i can't see any faster way
            # if parent-child switched in schema we search another direction
            # TODO It is workaroud and should be rewritten
            if self.sobject.info.get('relative_dir') == self.child.get('to'):
                if self.child.get('to_col'):
                    child_code = self.sobject.info.get(self.child.get('to_col'))

            filters = [(child_col, child_code)]

            order_bys = ['name']
            built_process = tc.server_start(project=self.project.get_code()).build_search_type(self.child.get('from'), self.project.get_code())

            # Logging info
            dl.log('Getting children for {}'.format(self.stype.get_pretty_name()), group_id=self.stype.get_code())
            if instance_type:
                runtime_command = 'thenv.get_tc().get_sobjects_new(search_type="{0}", filters={1}, order_bys={2}, instance_type={3}, related_type={4})'.format(built_process, filters, order_bys, instance_type, related_type)
            else:
                runtime_command = 'thenv.get_tc().get_sobjects_new(search_type="{0}", filters={1}, order_bys={2})'.format(
                    built_process, filters, order_bys)
            dl.info(runtime_command, group_id=self.stype.get_code())

            def get_sobjects_agent():
                return tc.get_sobjects_new(
                    search_type=built_process,
                    filters=filters,
                    order_bys=order_bys,
                    instance_type=instance_type,
                    related_type=related_type,
                )

            get_sobjects_worker = gf.get_thread_worker(
                get_sobjects_agent,
                env_inst.get_thread_pool('server_query/http_download_pool'),
                result_func=self.fill_child_items,
                # progress_func=self.download_progress,
                error_func=gf.error_handle,
            )
            get_sobjects_worker.start()

    def fill_child_items(self, sobjects):
        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Filling SObjects</span>')
        sobject_item_widget = self.get_parent_item_widget()
        ignore_dict = None
        if sobject_item_widget:
            ignore_dict = sobject_item_widget.ignore_dict

        for i, sobject in enumerate(sobjects[0].itervalues()):
            children_states = None
            if self.info['children_states']:
                children_states = self.info['children_states'].get(i)
            item_info_dict = {
                'relates_to': self.info['relates_to'],
                'is_expanded': self.info['is_expanded'],
                'sep_versions': self.info['sep_versions'],
                'children_states': children_states,
                'simple_view': False,
            }
            gf.add_sobject_item(
                self.tree_item,
                self.search_widget,
                sobject,
                self.stype,
                item_info_dict,
                ignore_dict=ignore_dict
            )
            # if i+1 % 20 == 0:
            #     QtGui.QApplication.processEvents()

        env_inst.ui_main.set_info_status_text('')

    def get_skey(self, skey=False, only=False, parent=False):
        pass

    def get_description(self):
        return 'No Description for this item "{0}"'.format('AZAZAZ')

    def is_checked(self):
        return False

    def get_search_key(self):
        return self.sobject.info.get('__search_key__')

    def get_parent_search_key(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_search_key()

    def get_sobject(self):
        return self.sobject

    def get_parent_sobject(self):
        parent_item = self.get_parent_item_widget()
        if parent_item:
            return parent_item.get_sobject()

    def showEvent(self, event):
        if not self.created:
            self.created = True
            self.create_ui()
        event.accept()

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()


class Ui_layoutWrapWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.widget = None
        self.setObjectName('layout_widget')

    def set_widget(self, widget):
        self.widget = widget
        self.setMinimumSize(self.widget.sizeHint())
        self.widget.setParent(self)

    def take_widget(self, parent=None):
        if parent:
            self.widget.setParent(parent)
        else:
            self.widget.setParent(None)
        return self.widget

    def get_widget(self):
        return self.widget

    def resizeEvent(self, event):
        if self.widget:
            self.widget.resize(self.size())
        event.accept()