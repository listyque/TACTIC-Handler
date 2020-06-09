# module Main Ui Classes
# file ui_main_classes.py
# Main Window interface

import collections
from functools import partial
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_mode, env_inst, dl, env_write_config, env_read_config, cfg_controls, env_api, env_server
import thlib.tactic_classes as tc
import thlib.update_functions as uf
import thlib.global_functions as gf
import thlib.ui.ui_main as ui_main
from thlib.ui_classes.ui_script_editor_classes import Ui_ScriptEditForm
from thlib.ui_classes.ui_update_classes import Ui_updateDialog
import thlib.ui.misc.ui_create_update as ui_create_update
from thlib.ui_classes.ui_repo_sync_queue_classes import Ui_repoSyncQueueWidget
from thlib.ui_classes.ui_custom_qwidgets import Ui_debugLogWidget, Ui_messagesWidget, StyledToolButton, Ui_extendedTreeWidget, StyledChooserToolButton
import ui_checkin_out_tabs_classes
import ui_conf_classes

if env_mode.get_mode() == 'maya':
    import thlib.maya_functions as mf
    reload(mf)


reload(ui_main)
reload(ui_create_update)
reload(ui_checkin_out_tabs_classes)
reload(ui_conf_classes)
reload(tc)
reload(uf)
reload(gf)


class Ui_projectIconWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui_raw()

        self.project = None

        self.create_ui()

    def create_ui_raw(self):
        self.setObjectName('Ui_projectIconWidget')
        self.setMaximumSize(60, 48)
        self.setMinimumSize(60, 48)
        self.setContentsMargins(0, 0, 0, 0)

        self.horizontal_layout = QtGui.QHBoxLayout(self)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.horizontal_layout.setSpacing(0)

        self.previewLabel = QtGui.QLabel(self)
        self.previewLabel.setMinimumSize(QtCore.QSize(60, 48))
        self.previewLabel.setMaximumSize(QtCore.QSize(60, 48))
        self.previewLabel.setStyleSheet('QLabel {background: transparent; border: 0px; border-radius: 0px;padding: 0px 0px;}')
        self.previewLabel.setTextFormat(QtCore.Qt.RichText)
        self.previewLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.previewLabel.setSizePolicy(sizePolicy)

        self.horizontal_layout.addWidget(self.previewLabel)

    def create_ui(self):

        self.fill_info()
        self.setCursor(Qt4Gui.QCursor(QtCore.Qt.PointingHandCursor))

    def set_project(self, project):

        self.project = project

    def get_snapshot(self, process='publish'):

        snapshot_process = self.project.process.get(process)
        if snapshot_process:
            context = snapshot_process.contexts.values()[0]
            if context.versionless:
                return context.versionless.values()[0]
            else:
                return context.versions.values()[0]

    def fill_info(self):
        if self.project:

            if self.project.process:

                if gf.get_value_from_config(cfg_controls.get_checkin(), 'getPreviewsThroughHttpCheckbox') == 1:
                    self.set_web_preview()
                else:
                    self.set_preview()
            else:
                self.previewLabel.setText(u'<span style=" font-size:9pt; font-weight:600; color:{0};">{1}</span>'.format(
                        'rgb(128,128,128)', gf.gen_acronym(self.project.get_title())))
        else:
            self.previewLabel.setText(u'<span style=" font-size:9pt; font-weight:600; color:{0};">{1}</span>'.format(
                'rgb(128,128,128)', ''))

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
                    if icon_previw.is_exists():
                        if icon_previw.get_file_size() == icon_previw.get_file_size(True):
                            self.set_preview()
                        else:
                            self.download_and_set_preview_file(icon_previw)
                    else:
                        self.download_and_set_preview_file(icon_previw)

    def download_and_set_preview_file(self, file_object):
        if not file_object.is_downloaded():
            if file_object.get_unique_id() not in env_inst.ui_repo_sync_queue.queue_dict.keys():
                repo_sync_item = env_inst.ui_repo_sync_queue.schedule_file_object(file_object)
                repo_sync_item.downloaded.connect(self.set_preview_pixmap)
                repo_sync_item.download()

    def set_preview_pixmap(self, file_object):
        pixmap = self.get_preview_pixmap(file_object.get_full_abs_path())
        if pixmap:
            self.previewLabel.setPixmap(pixmap)

    def get_preview_pixmap(self, image_path):
        pixmap = Qt4Gui.QPixmap(image_path)
        if not pixmap.isNull():

            pix_width = 48
            pix_height = 48

            pixmap = pixmap.scaledToHeight(pix_width, QtCore.Qt.SmoothTransformation)

            painter = Qt4Gui.QPainter()
            pixmap_mask = Qt4Gui.QPixmap(pix_width, pix_height)
            pixmap_mask.fill(QtCore.Qt.transparent)
            painter.begin(pixmap_mask)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.setBrush(Qt4Gui.QBrush(Qt4Gui.QColor(0, 0, 0, 255)))
            painter.drawRoundedRect(QtCore.QRect(4, 4, pix_width-8, pix_height-8), 4, 4)
            painter.end()

            rounded_pixmap = Qt4Gui.QPixmap(pixmap.size())
            rounded_pixmap.fill(QtCore.Qt.transparent)
            painter.begin(rounded_pixmap)
            painter.setRenderHint(Qt4Gui.QPainter.Antialiasing)
            painter.drawPixmap(QtCore.QRect((pixmap.width() - pix_width) / 2, 0, pix_width, pix_width), pixmap_mask)
            painter.setCompositionMode(Qt4Gui.QPainter.CompositionMode_SourceIn)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            return rounded_pixmap


class Ui_userIconWidget(QtGui.QWidget):
    def __init__(self, project=None, login=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui_raw()

        self.project = project
        self.login = login

        self.create_ui()

    def create_ui_raw(self):
        self.setObjectName('Ui_userIconWidget')
        self.setMaximumSize(60, 36)
        self.setMinimumSize(60, 36)
        self.setContentsMargins(0, 0, 0, 0)

        self.horizontal_layout = QtGui.QHBoxLayout(self)
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.horizontal_layout.setSpacing(0)

        self.previewLabel = QtGui.QLabel(self)
        self.previewLabel.setMinimumSize(QtCore.QSize(32, 32))
        self.previewLabel.setMaximumSize(QtCore.QSize(32, 32))
        self.previewLabel.setStyleSheet('QLabel {background: rgba(175, 175, 175, 64); border: 0px; border-radius: 16px;padding: 0px 0px;}')
        self.previewLabel.setTextFormat(QtCore.Qt.RichText)
        self.previewLabel.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.previewLabel.setSizePolicy(sizePolicy)

        self.horizontal_layout.addWidget(self.previewLabel)

    def create_ui(self):

        self.fill_info()
        self.setCursor(Qt4Gui.QCursor(QtCore.Qt.PointingHandCursor))

    def fill_info(self):
        self.previewLabel.setText(u'<span style=" font-size:9pt; font-weight:600; color:{0};">{1}</span>'.format(
            'rgb(64,64,64)', gf.gen_acronym('Alex Miarsky')))


class Ui_mainTabs(QtGui.QWidget):

    def __init__(self, project_code, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        env_inst.ui_main_tabs[project_code] = self

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()
        self.isCreated = False

        self.project = env_inst.projects.get(project_code)
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']

        self.create_ui()

    def create_ui(self):

        self.ui_checkin_checkout = None
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.create_loading_label()

    def get_tab_index(self, tab_widget):
        return self.main_tabWidget.indexOf(tab_widget)

    def raise_tab(self, tab_widget):
        self.main_tabWidget.setCurrentIndex(self.get_tab_index(tab_widget))

    def get_stypes(self, result=None, run_thread=False):

        if result:
            if self.project.stypes:
                self.create_checkin_checkout_ui()
                self.toggle_loading_label()
                self.ui_checkin_checkout.setHidden(False)
            env_inst.ui_main.set_info_status_text('')

        if run_thread:

            env_inst.ui_main.set_info_status_text(
                '<span style=" font-size:8pt; color:#00ff00;">Getting Search Types</span>')

            def get_stypes_agent():
                return self.project.get_stypes()

            env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

            stypes_items_worker = gf.get_thread_worker(
                get_stypes_agent,
                env_inst.get_thread_pool('server_query/server_thread_pool'),
                result_func=self.get_stypes,
                error_func=gf.error_handle
            )
            stypes_items_worker.start()

    def create_checkin_checkout_ui(self):
        self.ui_checkin_checkout = ui_checkin_out_tabs_classes.Ui_checkInOutTabWidget(
            self.project,
            self,
        )
        self.ui_checkin_checkout.setHidden(True)
        self.main_layout.addWidget(self.ui_checkin_checkout, 0, 0, 0, 0)

    def create_loading_label(self):
        self.loading_label = QtGui.QLabel()
        self.loading_label.setText('Loading...')
        self.loading_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.loading_label.setVisible(False)

        self.main_layout.addWidget(self.loading_label, 0, 0, 0, 0)

    def toggle_loading_label(self):
        if self.loading_label.isVisible():
            self.loading_label.setVisible(False)
        else:
            self.loading_label.setVisible(True)

    def showEvent(self, *args, **kwargs):

        if not self.isCreated:
            self.isCreated = True
            self.toggle_loading_label()
            self.get_stypes(run_thread=True)

        env_inst.set_current_project(self.project.info['code'])

    def closeEvent(self, event):

        if self.ui_checkin_checkout:
            self.ui_checkin_checkout.close()

        event.accept()


class Ui_topBarWidget(QtGui.QWidget):
    hamburger_clicked = QtCore.Signal()

    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.current_project = None
        self.shown = False
        self.hamburger_connected_method = None

        self.create_ui()

    def create_ui(self):

        self.create_layout()

        self.create_hamburger_button()

        self.create_project_icon_widget()
        self.create_projects_combo()

        self.create_spacer()

        self.create_info_label()

        self.create_user_icon_widget()
        self.create_config_button()

        self.fill_config_menu()
        # self.fill_projects_menu()

    def create_layout(self):
        self.main_layout = QtGui.QHBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    def create_info_label(self):
        self.info_label = QtGui.QLabel()
        self.info_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.info_label.setText('')

        self.main_layout.addWidget(self.info_label)

    def set_current_project(self, project=None):

        self.current_project = project

        if self.current_project:
            self.hamburger_tab_button.setHidden(False)
            self.projects_chooser_button.setText(self.current_project.info.get('title'))
            self.fill_project_icon()
        else:
            self.hamburger_tab_button.setHidden(True)
            self.projects_chooser_button.setText('Projects')
            self.fill_project_icon()

    def set_info_status_text(self, status_text=''):
        self.info_label.setText(status_text)

    def create_hamburger_button(self):

        self.hamburger_tab_button = StyledToolButton(shadow_enabled=True, small=True, square_type=True)
        self.hamburger_tab_button.setIcon(gf.get_icon('menu', icons_set='mdi', scale_factor=1.2))
        self.hamburger_tab_button.clicked.connect(self.hamburger_tab_button_click)
        self.hamburger_tab_button.setHidden(True)

        self.left_buttons_layout = QtGui.QHBoxLayout()
        self.left_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.left_buttons_layout.setSpacing(0)

        self.left_buttons_widget = QtGui.QWidget(self)
        self.left_buttons_widget.setLayout(self.left_buttons_layout)
        self.left_buttons_widget.setMinimumSize(60, 36)

        self.left_buttons_layout.addWidget(self.hamburger_tab_button)

        self.main_layout.addWidget(self.left_buttons_widget)

    def hamburger_tab_button_click(self):
        self.hamburger_clicked.emit()

    def connect_hamburger(self, method):
        if self.hamburger_connected_method:
            self.hamburger_clicked.disconnect(self.hamburger_connected_method)

        self.hamburger_connected_method = method
        self.hamburger_clicked.connect(self.hamburger_connected_method)

    def create_project_icon_widget(self):
        self.project_icon_widget = Ui_projectIconWidget()

        effect = QtGui.QGraphicsOpacityEffect(self)
        effect.setOpacity(0.7)
        self.project_icon_widget.setGraphicsEffect(effect)

        self.main_layout.addWidget(self.project_icon_widget)

    def fill_project_icon(self):

        self.project_icon_widget.set_project(self.current_project)
        self.project_icon_widget.fill_info()

    def create_spacer(self):
        spacer_item = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Ignored)
        self.main_layout.addItem(spacer_item)

    def create_config_button(self):
        self.config_button = StyledToolButton()
        self.config_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.config_button.setArrowType(QtCore.Qt.NoArrow)

        self.config_button.setIcon(gf.get_icon('settings', icons_set='mdi'))

        self.main_layout.addWidget(self.config_button)

    def create_user_icon_widget(self):
        self.user_icon_widget = Ui_userIconWidget()

        self.main_layout.addWidget(self.user_icon_widget)

    def create_projects_combo(self):
        self.projects_chooser_button = StyledChooserToolButton()
        self.projects_chooser_button.setText('Projects')

        self.main_layout.addWidget(self.projects_chooser_button)

    def fill_projects_menu(self):
        pass
        # self.menuProject = self.projects_chooser_button.get_menu()
        # self.menuProject.setObjectName("menuProject")
        # self.menuProject.setTitle(u"Projects")

        # self.projects_chooser_button.setMenu(self.menuProject)

    def fill_config_menu(self):

        self.menuConfig = QtGui.QMenu(self.config_button)
        self.menuConfig.setObjectName("menuConfig")
        self.menuConfig.setTitle(u"Menu")

        self.actionConfiguration = QtGui.QAction(self)
        self.actionConfiguration.setObjectName("actionConfiguration")
        self.actionUpdate = QtGui.QAction(self)
        self.actionUpdate.setObjectName("actionUpdate")
        self.actionExit = QtGui.QAction(self)
        self.actionExit.setObjectName("actionExit")
        self.actionApply_to_all_Tabs = QtGui.QAction(self)
        self.actionApply_to_all_Tabs.setObjectName("actionApply_to_all_Tabs")
        self.actionScriptEditor = QtGui.QAction(self)
        self.actionScriptEditor.setObjectName("actionScriptEditor")
        self.actionDock_undock = QtGui.QAction(self)
        self.actionDock_undock.setObjectName("actionDock_undock")
        self.actionDebug_Log = QtGui.QAction(self)
        self.actionDebug_Log.setObjectName("actionDebug_Log")
        self.actionSave_Preferences = QtGui.QAction(self)
        self.actionSave_Preferences.setObjectName("actionSave_Preferences")
        self.actionReloadCache = QtGui.QAction(self)
        self.actionReloadCache.setObjectName("actionReloadCache")

        self.menuConfig.addAction(self.actionConfiguration)
        self.menuConfig.addAction(self.actionSave_Preferences)
        self.menuConfig.addAction(self.actionReloadCache)
        self.menuConfig.addAction(self.actionApply_to_all_Tabs)
        self.menuConfig.addAction(self.actionDock_undock)
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionScriptEditor)
        self.menuConfig.addAction(self.actionDebug_Log)
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionUpdate)
        self.menuConfig.addSeparator()
        self.menuConfig.addSeparator()
        self.menuConfig.addAction(self.actionExit)

        self.actionConfiguration.setText(u"Configuration")
        self.actionUpdate.setText(u"Update")
        self.actionExit.setText(u"Exit")
        self.actionApply_to_all_Tabs.setText(u"Current view to All Tabs")
        self.actionScriptEditor.setText(u"Script Editor")
        self.actionDock_undock.setText(u"Dock/undock")
        self.actionDebug_Log.setText(u"Debug Log")
        self.actionSave_Preferences.setText(u"Save Preferences")
        self.actionReloadCache.setText(u"Reload Cache")

        self.actionExit.setIcon(gf.get_icon('window-close', icons_set='mdi'))
        self.actionConfiguration.setIcon(gf.get_icon('settings', icons_set='mdi'))
        self.actionSave_Preferences.setIcon(gf.get_icon('content-save', icons_set='mdi'))
        self.actionReloadCache.setIcon(gf.get_icon('reload', icons_set='mdi'))
        self.actionApply_to_all_Tabs.setIcon(gf.get_icon('hexagon-multiple', icons_set='mdi'))
        self.actionScriptEditor.setIcon(gf.get_icon('script', icons_set='mdi'))
        self.actionDebug_Log.setIcon(gf.get_icon('bug', icons_set='mdi'))
        self.actionUpdate.setIcon(gf.get_icon('update', icons_set='mdi'))

        if env_mode.get_mode() == 'standalone':
            self.actionDock_undock.setVisible(False)

        self.config_button.setMenu(self.menuConfig)
        self.config_button.setPopupMode(QtGui.QToolButton.InstantPopup)

    def paintEvent(self, event):
        super(self.__class__, self).paintEvent(event)
        painter = Qt4Gui.QPainter()
        painter.begin(self)
        rect = self.rect()
        painter.fillRect(rect.x(), rect.y(), rect.width(), rect.height(), Qt4Gui.QColor(48, 48, 48))


class Ui_projectsChooserWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.bg_widget = None

        self.create_ui()

    def create_ui(self):
        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        self.tree_widget = Ui_extendedTreeWidget(self)
        # self.tree_widget.setMaximumSize(QtCore.QSize(0, 16777215))
        self.tree_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tree_widget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tree_widget.setIndentation(0)
        self.tree_widget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tree_widget.setTabKeyNavigation(True)
        self.tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tree_widget.setAllColumnsShowFocus(True)
        self.tree_widget.setRootIsDecorated(False)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setExpandsOnDoubleClick(False)
        self.tree_widget.setObjectName('projects_chooser_widget')
        # self.tree_widget.setMinimumHeight(400)
        self.tree_widget.setMinimumWidth(250)
        self.tree_widget.setFocusPolicy(QtCore.Qt.NoFocus)

        self.tree_widget.setStyleSheet(gf.get_qtreeview_style(True))

        self.main_layout.addWidget(self.tree_widget)

        self.controls_actions()

    def controls_actions(self):
        pass

    def set_bg_widget(self, widget):
        # This is workaround to get window drop shadow effect working in qt5+
        self.bg_widget = widget
        self.bg_widget.lower()

    def initial_fill(self):

        self.tree_widget.clear()

        all_projects_dicts = []

        for project_name, project in env_inst.projects.items():
            if project.get_code() != 'sthpw':
                all_projects_dicts.append(project.info)

        projects_by_categories = gf.group_dict_by(all_projects_dicts, 'category')

        for cat_name, projects in projects_by_categories.items():

            if cat_name:
                cat_name = gf.prettify_text(cat_name, True)
            else:
                cat_name = 'No Category'

            item_info = {
                'title': cat_name,
                'item_type': 'cat',
            }

            gf.add_project_item(
                tree_widget=self.tree_widget,
                projects=projects,
                item_info=item_info,
            )

        self.tree_widget.resizeColumnToContents(0)

    def resizeEvent(self, event):
        if self.bg_widget:
            self.bg_widget.resize(self.size())

        event.accept()

    def moveEvent(self, event):
        if self.bg_widget:
            self.bg_widget.move(self.pos())

        event.accept()

    def hideEvent(self, event):
        if self.bg_widget:
            self.bg_widget.hide()
        event.accept()

    def showEvent(self, event):
        if self.bg_widget:
            self.bg_widget.show()

        event.accept()


class Ui_Main(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.ui_settings_dict = {}
        self.created = False

        self.create_ui_raw()

        if env_mode.is_offline():
            self.create_ui_main_offline()
        else:
            self.create_ui_main()

    def create_ui_raw(self):
        self.setObjectName("MainWindow")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.resize(820, 800)
        self.setMinimumSize(QtCore.QSize(600, 600))
        self.setStyleSheet(
            """
            QSplitter::handle {
                border: 0px;
                background: transparent;
                margin: 0px 0px 0px 0px;
            }
    
            QSplitter::handle:horizontal {
                width: 4px;
            }
    
            QSplitter::handle:vertical {
                height: 4px;
            }
    
            QSplitter::handle:pressed {
                border: 0px;
                background: rgb(128,128,128);
            }
            QSplitter::handle:hover {
                border: 0px;
                background: rgb(128,128,128);
            }
            QMainWindow::separator
            {
                width: 4px;
                border: 0px;
                background: transparent;
            }
            QMainWindow::separator:hover {
                border: 0px;
                background: rgb(128,128,128);
            }
            """
            "QTabWidget::pane {\n"
            "    border: 0px;\n"
            "}\n"
            "QTabBar::tab {\n"
            "    background: transparent;\n"
            "    border: 2px solid transparent;\n"
            "    border-top-right-radius: 0px;\n"
            "    border-top-left-radius: 0px;\n"
            "    border-bottom-right-radius: 3px;\n"
            "    border-bottom-left-radius: 3px;\n"
            "    padding: 4px;\n"
            "}\n"
            "QTabBar::tab:selected, QTabBar::tab:hover {\n"
            "    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(255, 255, 255, 32), stop: 1 rgba(255, 255, 255, 48));\n"
            "}\n"
            "QTabBar::tab:selected {\n"
            "    border-color: transparent;\n"
            "}\n"
            "QTabBar::tab:!selected {\n"
            "    margin-top: 0px;\n"
            "}\n"
            "QDockWidget::title{\n"
            "    padding: 6px;\n"
            "    font-size: 10pt;\n"
            "    border: 1px;\n"
            "    border-radius: 0px;\n"
            "    padding-left: 10px;\n"
            "    background-color: rgb(72, 72, 72);\n"
            "}\n"
            "QDockWidget::close-button, QDockWidget::float-button {\n"
            "    padding: 0px;\n"
            "    color: rgb(0,0,128);\n"
            "    border: none;\n"
            "}\n"
            "\n"
            "QDockWidget {\n"
            "    border: 0px ;\n"
            "    border-radius: 0px;\n"
            "    font-size: 10pt;\n"
            "}\n"
            "QGroupBox {\n"
            "    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 16), stop: 1 rgba(0, 0, 0, 0));\n"
            "    border: 0px;\n"
            "    border-radius: 4px;\n"
            "    padding: 0px 8px;\n"
            "}\n"
            "\n"
            "QGroupBox::title {\n"
            "    subcontrol-origin: margin;\n"
            "    subcontrol-position: left top; \n"
            "    padding: 2 6px;\n"
            "    background-color: transparent;\n"
            "    border-bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 64), stop:1 rgba(128, 128,128, 0));\n"
            "}\n"
            "")
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.setWindowFilePath("")
        self.mainwidget = QtGui.QWidget(self)
        self.mainwidget.setObjectName("mainwidget")
        self.setCentralWidget(self.mainwidget)
        self.statusBar().close()

    def create_central_widget(self):

        self.central_widget = QtGui.QWidget()

        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.central_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.central_widget)

    def create_top_bar(self):

        self.top_bar_widget = Ui_topBarWidget()

        self.main_layout.addWidget(self.top_bar_widget)
        self.main_layout.setStretch(0, 0)

        self.top_bar_widget.projects_chooser_button.clicked.connect(self.show_projects_cooser)

    def get_top_bar_widget(self):
        return self.top_bar_widget

    def create_projects_chooser(self):

        self.projects_chooser_widget_bg = QtGui.QFrame(self)
        self.projects_chooser_widget_bg.setStyleSheet("QFrame { border: 0px; background-color: black;}")
        self.projects_chooser_widget_bg.setHidden(True)
        effect = QtGui.QGraphicsDropShadowEffect(self)
        effect.setOffset(0, 0)
        effect.setColor(Qt4Gui.QColor(0, 0, 0, 128))
        effect.setBlurRadius(64)
        self.projects_chooser_widget_bg.setGraphicsEffect(effect)

        self.projects_chooser_widget = Ui_projectsChooserWidget(self)
        self.projects_chooser_widget.set_bg_widget(self.projects_chooser_widget_bg)

        self.projects_chooser_widget.setMinimumWidth(800)
        self.projects_chooser_widget.setMaximumWidth(800)
        self.projects_chooser_widget.setMinimumHeight(400)
        self.projects_chooser_widget.setMaximumHeight(1600)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.projects_chooser_widget.setSizePolicy(sizePolicy)

        grid_layout = QtGui.QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)

        grid_layout.addWidget(self.projects_chooser_widget, 1, 1, 1, 1)

        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Minimum)
        grid_layout.addItem(spacerItem, 1, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Minimum)
        grid_layout.addItem(spacerItem1, 1, 2, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Ignored)
        grid_layout.addItem(spacerItem2, 0, 0, 1, 3)
        spacerItem3 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Ignored)
        grid_layout.addItem(spacerItem3, 2, 0, 1, 3)

        self.main_layout.addLayout(grid_layout)

    def show_projects_cooser(self):

        if self.projects_chooser_widget.isVisible():
            self.projects_chooser_widget.setHidden(True)

            current_project = env_inst.get_current_project()
            if current_project:
                current_project_dock = self.projects_docks.get(current_project)
                current_project_dock.setHidden(False)
            else:
                self.projects_chooser_widget.setHidden(False)
        else:
            for opened_project in self.projects_docks.values():
                opened_project.setHidden(True)

            self.projects_chooser_widget.setHidden(False)

    def create_project_dock(self, project_code, dummy=None):

        if project_code not in self.projects_docks.keys():

            for opened_project in self.projects_docks.values():
                opened_project.setHidden(True)

            project = env_inst.projects.get(project_code)

            if project:
                if not project.is_template():
                    main_tabs_widget = Ui_mainTabs(project_code, self)
                    self.projects_docks[project_code] = main_tabs_widget

                    self.projects_chooser_widget.setHidden(True)
                    self.main_layout.addWidget(main_tabs_widget, 1)

                    self.top_bar_widget.set_current_project(project)
            else:
                print('No project with code: {0}'.format(project_code))
        else:
            for opened_project in self.projects_docks.values():
                opened_project.setHidden(True)

            project = env_inst.projects.get(project_code)

            if project:
                project_dock = self.projects_docks.get(project_code)
                project_dock.setHidden(False)
                self.projects_chooser_widget.setHidden(True)

                self.top_bar_widget.set_current_project(project)

    def create_ui_main_offline(self):
        self.setWindowTitle('TACTIC-handler (OFFLINE)')

        self.projects_docks = collections.OrderedDict()

        env_inst.ui_main = self

        self.create_debuglog_widget()

        # instance attributes
        self.menu = None

        self.create_central_widget()
        self.create_top_bar()
        self.create_projects_chooser()

        self.menu_bar_actions()

        self.readSettings()
        self.setIcon()

        self.created = True

    def create_ui_main(self):
        self.setWindowTitle('TACTIC-Handler')

        self.projects_docks = collections.OrderedDict()

        env_inst.ui_main = self

        self.create_debuglog_widget()

        # instance attributes
        self.menu = None

        self.create_central_widget()
        self.create_top_bar()
        self.create_projects_chooser()

        self.query_projects()

        self.menu_bar_actions()

        self.readSettings()
        self.setIcon()

        self.create_script_editor_widget()
        # self.create_messages_widget()

        self.created = True

    @staticmethod
    def execute_after_all_ui_started():
        # This func is executed after all ui started. File execute_after_start can contain any useful code that
        # should be executed after ui loaded

        from execute_after_start import execute

        execute()

        env_api.start_api_server_app()

    def create_debuglog_widget(self):
        env_inst.ui_debuglog = Ui_debugLogWidget(self)
        env_inst.ui_debuglog.setWindowState(QtCore.Qt.WindowMinimized)

        env_inst.ui_debuglog.show()
        env_inst.ui_debuglog.hide()
        env_inst.ui_debuglog.setWindowState(QtCore.Qt.WindowNoState)

    def create_script_editor_widget(self):
        env_inst.ui_script_editor = Ui_ScriptEditForm(self)

    def create_messages_widget(self):
        env_inst.ui_messages = Ui_messagesWidget(self)

    def set_info_status_text(self, status_text=''):
        self.top_bar_widget.set_info_status_text(status_text)

    # def check_for_update(self):
    #     if uf.check_need_update():
    #         self.info_label.setText('<span style=" font-size:8pt; color:#ff0000;">Need update</span>')

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    # def customize_ui(self):
    #     if env_mode.get_mode() == 'standalone':
    #         self.actionDock_undock.setVisible(False)
    #
    #     self.actionExit.setIcon(gf.get_icon('window-close', icons_set='mdi'))
    #     self.actionConfiguration.setIcon(gf.get_icon('settings', icons_set='mdi'))
    #     self.actionSave_Preferences.setIcon(gf.get_icon('content-save', icons_set='mdi'))
    #     self.actionReloadCache.setIcon(gf.get_icon('reload', icons_set='mdi'))
    #     self.actionApply_to_all_Tabs.setIcon(gf.get_icon('hexagon-multiple', icons_set='mdi'))
    #     self.actionScriptEditor.setIcon(gf.get_icon('script', icons_set='mdi'))
    #     self.actionDebug_Log.setIcon(gf.get_icon('bug', icons_set='mdi'))
    #     self.actionUpdate.setIcon(gf.get_icon('update', icons_set='mdi'))
    #
    #     self.statusBar().close()

    def menu_bar_actions(self):
        """
        Actions for the main menu bar
        """

        def close_routine():
            if env_mode.get_mode() == 'maya':

                self.close()

                from thlib.ui_classes.ui_maya_dock import close_all_instances
                close_all_instances()

                # Removing path from sys, so we can run other instance from different path
                import sys
                sys.path.remove(env_mode.get_current_path())

            if env_mode.get_mode() == 'standalone':

                self.close()

        self.top_bar_widget.actionExit.triggered.connect(close_routine)

        self.top_bar_widget.actionConfiguration.triggered.connect(self.open_config_dialog)

        self.top_bar_widget.actionApply_to_all_Tabs.triggered.connect(self.apply_current_view)
        self.top_bar_widget.actionReloadCache.triggered.connect(self.reload_cache)

        self.top_bar_widget.actionUpdate.triggered.connect(self.update_self)
        self.top_bar_widget.actionScriptEditor.triggered.connect(self.open_script_editor)
        self.top_bar_widget.actionDebug_Log.triggered.connect(lambda: env_inst.ui_debuglog.show())

        # User Menu items
        # self.top_bar_widget.actionMessages.triggered.connect(lambda: env_inst.ui_messages.show())
        # self.top_bar_widget.actionEdit_My_Account.triggered.connect(self.edit_my_account)

        self.top_bar_widget.actionDock_undock.triggered.connect(self.undock_window)

    def undock_window(self):
        env_inst.ui_maya_dock.toggle_docking()

    def edit_my_account(self):

        print 'Edit my Account'
        from thlib.ui_classes.ui_addsobject_classes import Ui_addTacticSobjectWidget

        login_stype = env_inst.get_stype_by_code('sthpw/login')
        # parent_stype = self.parent_sobject.get_stype()
        # search_key = self.parent_sobject.get_search_key()

        # print search_key

        add_sobject = Ui_addTacticSobjectWidget(
            stype=login_stype,
            parent_stype=None,
            # search_key=search_key,
            parent_search_key=None,
            # view='edit',
            parent=self,
        )

        add_sobject.show()

    # def create_ui_float_notify(self):
    #     self.float_notify = ui_float_notify_classes.Ui_floatNotifyWidget(self)
    #     self.float_notify.show()
    #     self.float_notify.setSizeGripEnabled(True)

    def open_script_editor(self):
        env_inst.ui_script_editor.show()

    def update_self(self):
        if env_mode.is_online():
            self.update_dialog = Ui_updateDialog(self)

            self.update_dialog.show()

    def reload_cache(self):
        tc.get_all_projects_and_logins(True)
        for project in env_inst.projects.values():
            project.query_search_types(True)

        if env_mode.get_mode() == 'maya':
            self.restart_ui_main()
        else:
            self.close()
            gf.restart_app()

    def open_config_dialog(self):
        conf_dialog = ui_conf_classes.Ui_configuration_dialogWidget(parent=self)
        conf_dialog.show()

    def restart_for_update_ui_main(self):

        if env_mode.get_mode() == 'maya':
            # import main_maya
            # thread = main_maya.main.restart()
            from thlib.ui_classes.ui_maya_dock import close_all_instances
            close_all_instances()
            # self.restart_ui_main()
        else:
            self.close()
            gf.restart_app()

        # if env_mode.get_mode() == 'standalone':
        #     import main_standalone
        #     thread = main_standalone.restart()
        #     thread.finished.connect(self.close)
        # if env_mode.get_mode() == 'maya':
        #     import main_maya
        #     thread = main_maya.main.restart()
        #     thread.finished.connect(main_maya.main.close_all_instances)

    def restart_ui_main(self, server_preset=None):
        if server_preset:
            new_server_preset = env_server.get_cur_srv_preset()
            env_server.set_cur_srv_preset(server_preset)

        # Closing main app itself
        self.close()

        # Closing server api
        env_api.close_server()

        if server_preset:
            env_server.set_cur_srv_preset(new_server_preset)

        if env_mode.is_online():
            self.create_ui_main()
        else:
            self.create_ui_main_offline()

        self.show()
        return self

    def apply_current_view(self):
        # TODO may be need to be rewriten to use env instance
        if env_inst.get_current_project():
            current_project_widget = self.projects_docks[env_inst.get_current_project()].widget()

            current_project_widget.ui_checkin_checkout.apply_current_view_to_all()

            # widget_name = current_project_widget.main_tabWidget.currentWidget().objectName()

            # if widget_name == 'checkInOutTab':
            #     current_project_widget.ui_checkin_checkout.apply_current_view_to_all()
            #
            # if widget_name == 'checkOutTab':
            #     current_project_widget.ui_checkout.apply_current_view_to_all()
            #
            # if widget_name == 'checkInTab':
            #     current_project_widget.ui_checkin.apply_current_view_to_all()

    def fill_projects_to_projects_chooser(self):
        self.projects_chooser_widget.initial_fill()

    # def fill_projects_to_menu(self):
    #
    #     all_projects_dicts = []
    #
    #     for project_name, project in env_inst.projects.items():
    #         if project.get_code() != 'sthpw':
    #             all_projects_dicts.append(project.info)
    #
    #     projects_by_categories = gf.group_dict_by(all_projects_dicts, 'category')
    #
    #     for cat_name, projects in projects_by_categories.items():
    #         if cat_name:
    #             cat_name = gf.prettify_text(cat_name, True)
    #         else:
    #             cat_name = 'No Category'
    #         if cat_name != 'Template':
    #             category = self.top_bar_widget.menuProject.addMenu(cat_name)
    #
    #         for e, project in enumerate(projects):
    #             if not project.get('is_template'):
    #                 project_code = project.get('code')
    #
    #                 menu_action = QtGui.QAction(self)
    #                 # menu_action.setCheckable(True)
    #
    #                 if self.opened_projects:
    #                     if project_code in self.opened_projects:
    #                         menu_action.setChecked(True)
    #                 menu_action.setText(project.get('title'))
    #                 # Don't know why lambda did not work here
    #                 menu_action.triggered.connect(partial(self.create_project_dock, project_code))
    #                 category.addAction(menu_action)

    def restore_opened_projects(self):
        if self.ui_settings_dict:
            self.opened_projects = self.ui_settings_dict.get('opened_projects')
        else:
            self.opened_projects = None
        if not isinstance(self.opened_projects, list):
            if self.opened_projects:
                self.opened_projects = [self.opened_projects]

        if self.opened_projects:
            # for project in self.opened_projects:
            #     if project:
            #         self.create_project_dock(project)

            current_project_code = self.ui_settings_dict.get('current_active_project')
            self.create_project_dock(current_project_code)

            if current_project_code:
                if self.projects_docks.get(current_project_code):
                    self.projects_docks[current_project_code].show()
                    self.projects_docks[current_project_code].raise_()

    def create_repo_sync_queue_ui(self):
        env_inst.ui_repo_sync_queue = Ui_repoSyncQueueWidget(parent=self)

    def get_settings_dict(self):

        settings_dict = {}

        if self.windowState() == QtCore.Qt.WindowMaximized:
            state = True
            if self.ui_settings_dict:
                settings_dict['pos'] = self.ui_settings_dict['pos']
                settings_dict['size'] = self.ui_settings_dict['size']
            else:
                settings_dict['pos'] = self.pos().toTuple()
                settings_dict['size'] = self.size().toTuple()
        else:
            state = False
            settings_dict['pos'] = self.pos().toTuple()
            settings_dict['size'] = self.size().toTuple()
        settings_dict['windowState'] = state

        if self.projects_docks.keys():
            settings_dict['opened_projects'] = self.projects_docks.keys()
            if env_inst.get_current_project():
                settings_dict['current_active_project'] = str(env_inst.get_current_project())
        else:
            settings_dict['opened_projects'] = ''
            settings_dict['current_active_project'] = ''

        return settings_dict

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'pos': self.pos().toTuple(),
                'size': self.size().toTuple(),
                'windowState': False,
                'opened_projects': '',
                'current_active_project': '',
            }

        self.move(settings_dict['pos'][0], settings_dict['pos'][1])
        self.resize(settings_dict['size'][0], settings_dict['size'][1])

        if settings_dict['windowState']:
            self.setWindowState(QtCore.Qt.WindowMaximized)

    def readSettings(self):
        self.ui_settings_dict = env_read_config(filename='ui_settings', unique_id='ui_main', long_abs_path=True)
        self.set_settings_from_dict(self.ui_settings_dict)

    def writeSettings(self):
        env_write_config(self.get_settings_dict(), filename='ui_settings', unique_id='ui_main', long_abs_path=True)

    def closeEvent(self, event):

        # Closing server api
        env_api.close_server(self)

        for dock in self.projects_docks.values():
            # project_code = dock.widget().project.get_code()
            # dock.widget().close()
            dock.close()
            dock.deleteLater()
            del dock
            # env_inst.cleanup(project_code)

        self.writeSettings()

        event.accept()

    def query_projects_finished(self, result=None):
        if result:
            self.create_repo_sync_queue_ui()

            self.restore_opened_projects()
            # self.fill_projects_to_menu()
            self.fill_projects_to_projects_chooser()
            env_inst.ui_main.set_info_status_text('')

            self.execute_after_all_ui_started()

    def query_projects(self):
        env_inst.ui_main.set_info_status_text(
            '<span style=" font-size:8pt; color:#00ff00;">Getting projects</span>')

        def get_all_projects_and_logins_agent():
            return tc.get_all_projects_and_logins()

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        projects_items_worker = gf.get_thread_worker(
            get_all_projects_and_logins_agent,
            env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=self.query_projects_finished,
            error_func=gf.error_handle
        )
        projects_items_worker.start()

    # def closeEventExt(self, event):
    #     self.ext_window.deleteLater()
    #     event.accept()
