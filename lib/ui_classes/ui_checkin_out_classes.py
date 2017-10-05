# file ui_checkout_tree_classes.py

import json
# import xml.etree.ElementTree as Et
# import PySide.QtCore as QtCore
# import PySide.QtGui as QtGui
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

from lib.environment import env_mode, env_inst, env_server, env_tactic
# from lib.configuration import cfg_controls
import lib.tactic_classes as tc
import lib.global_functions as gf
# import lib.ui.checkin_out.ui_checkin_out_widget as ui_checkin_out_widget
import lib.ui.checkin_out.ui_checkin_out_options_dialog as ui_checkin_out_options_dialog
# import lib.ui_classes.ui_misc_classes as ui_misc_classes
import ui_item_classes as item_widget
# import ui_icons_classes as icons_widget
import ui_richedit_classes as richedit_widget
import ui_addsobject_classes as addsobject_widget
import ui_drop_plate_classes as drop_plate_widget
import ui_maya_dialogs_classes as maya_dialogs
import ui_search_classes as search_classes
import lib.ui_classes.ui_snapshot_browser_classes as snapshot_browser_widget
import lib.ui.checkin_out.ui_fast_controls as fast_controls
import lib.ui.checkin_out.ui_description_widget as description_widget

if env_mode.get_mode() == 'maya':
    import lib.maya_functions as mf
    reload(mf)

# reload(ui_checkin_out_widget)
reload(item_widget)
# reload(icons_widget)
reload(richedit_widget)
reload(addsobject_widget)
reload(drop_plate_widget)
reload(maya_dialogs)
reload(search_classes)
reload(tc)
reload(snapshot_browser_widget)
reload(fast_controls)


class Ui_descriptionWidget(QtGui.QWidget, description_widget.Ui_descriptionWidget):
    def __init__(self, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project
        self.item = None
        self.descriptionTextEdit_freezed = False
        self.descriptionTextEdit_edited = False

        self.setupUi(self)

        self.create_ui()

    def create_ui(self):

        self.update_desctiption_thread = tc.ServerThread(self)

        self.create_float_buttons()
        self.create_rich_edit()

        self.controls_actions()
        self.threads_actions()

    def threads_actions(self):
        self.update_desctiption_thread.finished.connect(lambda: self.update_desctiption(update_description=True))

    def controls_actions(self):
        self.descriptionTextEdit.textChanged.connect(self.freeze_text_edit)
        self.descriptionTextEdit.selectionChanged.connect(self.text_edit_select)
        self.clear_button.clicked.connect(self.unfreeze_text_edit)
        self.edit_button.clicked.connect(self.set_edit_mode)
        self.save_button.clicked.connect(self.unset_edit_mode)

        self.save_button.clicked.connect(lambda: self.update_desctiption(run_thread=True))

    def set_item(self, item):
        self.item = item
        if self.item:
            self.customize_with_item()
        else:
            self.customize_without_item()

    def customize_with_item(self):
        # self.search_widget.get_description_text_edit().setText(nested_item.get_description())

        # self.descriptionTextEdit.setText(self.item.get_description())

        if not self.descriptionTextEdit_freezed or self.descriptionTextEdit.toPlainText() == '':
            self.descriptionTextEdit.setText(self.item.get_description())
            self.unfreeze_text_edit()
            self.unset_edit_mode()

    def customize_without_item(self):
        self.unfreeze_text_edit()
        self.unset_edit_mode()

    def create_rich_edit(self):
        self.ui_richedit = richedit_widget.Ui_richeditWidget(self.descriptionTextEdit)
        self.editorLayout.addWidget(self.ui_richedit)

    def keyPressEvent(self, key):
        if key.key() == QtCore.Qt.Key_Escape:
            if self.item:
                self.customize_with_item()
            else:
                self.customize_without_item()

    def create_float_buttons(self):
        self.descriptionTextEdit.setViewportMargins(0, 0, 0, 24)
        self.clear_button_layout = QtGui.QGridLayout(self.descriptionTextEdit)
        self.clear_button_layout.setContentsMargins(0, 0, 0, 0)
        self.clear_button_layout.setSpacing(0)
        self.clear_button = QtGui.QToolButton()
        self.clear_button.setFixedSize(24, 24)
        self.clear_button.setIcon(
            gf.get_icon('unlock', icons_set='ei', color=Qt4Gui.QColor(0, 192, 255, 192), scale_factor=0.8))

        self.clear_button_layout.addWidget(self.clear_button, 1, 2, 1, 1)
        self.clear_button_layout.addItem(QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum), 1, 2, 1, 1)
        self.edit_button = QtGui.QToolButton()
        self.edit_button.setFixedSize(24, 24)
        self.edit_button.setIcon(
            gf.get_icon('edit', icons_set='ei', scale_factor=0.8))
        self.clear_button_layout.addWidget(self.edit_button, 1, 0, 1, 1)
        self.clear_button_layout.addItem(QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 0, 0, 1, 3)

        self.save_button = QtGui.QToolButton()
        self.save_button.setFixedSize(24, 24)
        self.save_button.setIcon(
            gf.get_icon('ok', icons_set='ei', color=Qt4Gui.QColor(0, 255, 128, 192), scale_factor=0.8))
        self.clear_button_layout.addWidget(self.save_button, 1, 1, 1, 1)

        self.clear_button.setHidden(True)
        self.save_button.setHidden(True)

    def update_desctiption(self, run_thread=False, update_description=False):
        if run_thread:
            if self.item and self.item.type in ['snapshot', 'sobject']:
                self.update_desctiption_thread.kwargs = dict(
                    search_key=self.item.get_skey(only=True),
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
                self.item.update_description(self.descriptionTextEdit.toPlainText())

    def set_edit_mode(self):
        self.unfreeze_text_edit()
        self.descriptionTextEdit.setStyleSheet('QTextEdit{border: 2px solid rgba(0,255,128,192); border-radius: 3px;}')
        self.descriptionTextEdit_edited = True
        self.edit_button.setHidden(True)
        self.save_button.setHidden(False)

    def unset_edit_mode(self):
        self.descriptionTextEdit.setStyleSheet('')
        self.descriptionTextEdit_edited = False
        self.edit_button.setHidden(False)
        self.save_button.setHidden(True)

    def freeze_text_edit(self):
        if not self.descriptionTextEdit_edited:
            self.descriptionTextEdit.setStyleSheet('QTextEdit{border: 2px solid rgba(0,192,255,192); border-radius: 3px;}')
            self.descriptionTextEdit_freezed = True
            self.clear_button.setHidden(False)
            self.edit_button.setHidden(True)

    def text_edit_select(self):
        if not self.descriptionTextEdit_edited and not self.descriptionTextEdit_freezed:
            self.descriptionTextEdit.clear()

    def get_description(self, fmt='html'):
        if self.descriptionTextEdit_freezed:
            if fmt == 'html':
                return self.descriptionTextEdit.toHtml()
            elif fmt == 'plain':
                return self.descriptionTextEdit.toPlainText()
        else:
            return 'No Description'

    def unfreeze_text_edit(self):
        self.descriptionTextEdit.setStyleSheet('')
        self.descriptionTextEdit_freezed = False
        self.clear_button.setHidden(True)
        self.edit_button.setHidden(False)


class Ui_checkInOutOptionsWidget(QtGui.QWidget, ui_checkin_out_options_dialog.Ui_checkinOutOptions):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.stype = stype
        self.project = project
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']
        self.tab_name = self.parent().objectName()

        # env_inst.get_check_tree(self.current_project, 'checkin_out', self.tab_name)

        self.create_ui()
        self.controls_actions()
        self.changed = False

    def create_ui(self):

        from lib.ui_classes.ui_conf_classes import Ui_checkinPageWidget

        self.checkinPageWidget = Ui_checkinPageWidget(self)
        # self.checkinPageWidget.checkinPageWidgetLayout.setContentsMargins(9, 9, 9, 9)

        self.create_scroll_area()
        self.scroll_area.setWidget(self.checkinPageWidget)

        # this is potentially useful, but not necessary at this time
        self.checkinPageWidget.defaultRepoPathsGroupBox.setHidden(True)
        self.checkinPageWidget.customRepoPathsGroupBox.setHidden(True)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.checkinPageWidget.checkinPageWidgetLayout.addItem(spacerItem)

        self.checkinPageWidget.collect_defaults(apply_values=True, custom_parent=self)
        self.checkinPageWidget.custom_save_config(custom_parent=self)

    def create_scroll_area(self):
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area_contents = QtGui.QWidget()
        self.scroll_area.setStyleSheet('QScrollArea > #qt_scrollarea_viewport > QWidget {background-color: rgba(128, 128, 128, 48);}')
        self.scroll_area.setFrameShape(QtGui.QScrollArea.NoFrame)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_contents)

        self.settingsVerticalLayout.addWidget(self.scroll_area)

    def controls_actions(self):
        pass
        # self.checkinPageWidget.showEvent = self.showEvent
        # self.applyPushButton.clicked.connect(self.checkinPageWidget.save_config)
        # self.applyToAllPushButton.clicked.connect(self.apply_current_to_all_tabs)

    # def apply_current_to_all_tabs(self):
    #     current_settings = self.get_settings_dict()
    #     for tab in env_inst.ui_check_tree.get(self.parent_ui.relates_to).itervalues():
    #         tab.checkin_options_widget.set_settings_from_dict(current_settings)

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
        if event.type() in [QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.Wheel, QtCore.QEvent.KeyPress] and isinstance(widget, (
            QtGui.QCheckBox,
            QtGui.QGroupBox,
            QtGui.QRadioButton,
            QtGui.QSpinBox,
            QtGui.QComboBox,
        )):
            self.changed = True

        return QtGui.QWidget.eventFilter(self, widget, event)

    def showEvent(self, event):
        self.checkinPageWidget.collect_defaults(apply_values=True, custom_parent=self)
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


class SquareLabel(QtGui.QLabel):
    clicked = QtCore.Signal()

    def __init__(self, menu, action, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.menu = menu
        self.action = action

    def mousePressEvent(self, event):
        self.clicked.emit()
        event.accept()

    def enterEvent(self, event):
        self.setAutoFillBackground(False)
        self.menu.setActiveAction(self.action)

    def leaveEvent(self, event):
        self.setAutoFillBackground(True)


class MenuWithLayout(QtGui.QMenu):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.set_styling()

        self.layout = QtGui.QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 1, 1, 1)
        self.layout.setColumnStretch(0, 1)

        self.setLayout(self.layout)

    def set_styling(self):

        self.setStyleSheet("QMenu::separator { height: 2px;}")

    def addAction(self, action, edit_label=False):

        w = QtGui.QWidget()
        l = QtGui.QGridLayout(w)

        b = SquareLabel(menu=self, action=action)
        b.setAlignment(QtCore.Qt.AlignCenter)
        b.setPixmap(gf.get_icon('edit', icons_set='ei').pixmap(13, 13))
        w.setMinimumSize(22, 13)

        b.setAutoFillBackground(True)

        b.setBackgroundRole(Qt4Gui.QPalette.Background)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        l.setSpacing(0)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(b)

        self.layout.addWidget(w, len(self.actions()), 1, 1, 1)

        spacerItem = QtGui.QSpacerItem(self.sizeHint().width()-5, 2, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        self.layout.addItem(spacerItem, len(self.actions()), 0, 1, 1)

        self.layout.setRowStretch(len(self.actions()), 1)

        super(MenuWithLayout, self).addAction(action)

        w.setFixedHeight(self.actionGeometry(action).height())

        if edit_label:
            return b
        else:
            b.setHidden(True)
            return action

    def addSeparator(self):
        spacerItem = QtGui.QSpacerItem(0, 2, QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        self.layout.addItem(spacerItem, len(self.actions()), 0, 1, 2)

        return super(MenuWithLayout, self).addSeparator()


class Ui_fastControlsWidget(QtGui.QWidget, fast_controls.Ui_fastControls):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project
        self.item = None

        self.create_ui()

    def create_ui(self):
        self.setupUi(self)
        self.customize_ui()

        # self.fill_process_combo_box()
        self.create_context_combo_box()
        self.controls_actions()

    def controls_actions(self):

        self.contextComboBox.editTextChanged.connect(self.freeze_context_combo_box)
        self.contextComboBox_clear_button.clicked.connect(self.unfreeze_context_combo_box)

    def set_item(self, item):
        self.item = item
        if self.item:
            self.customize_with_item()
        else:
            self.customize_without_item()

    def customize_with_item(self):

        self.savePushButton.setEnabled(True)
        self.openPushButton.setEnabled(True)
        self.contextComboBox.setEnabled(True)
        self.processComboBox.setEnabled(True)

        if not self.contextComboBox_freezed:
            self.fill_context_combo_box(self.item.get_context_options(), self.item.get_context())
            self.unfreeze_context_combo_box()

        self.fill_process_combo_box(self.item.get_full_process_list(), self.item.get_current_process_info())

    def customize_without_item(self):

        self.savePushButton.setEnabled(False)
        self.openPushButton.setEnabled(False)
        self.contextComboBox.setEnabled(False)
        self.processComboBox.setEnabled(False)
        self.unfreeze_context_combo_box()

    def customize_ui(self):
        # self.savePushButton.setVisible(False)
        # self.openPushButton.setVisible(False)
        self.savePushButton.setIcon(gf.get_icon('save'))
        self.openPushButton.setIcon(gf.get_icon('folder'))
        # self.toggleSaveOptionsToolButton.setIcon(gf.get_icon('toggle-off'))
        # self.toggleOpenOptionsToolButton.setIcon(gf.get_icon('toggle-off'))

    def set_save_button_menu(self, menu):
        self.savePushButton.addActions(menu.actions())
        self.savePushButton.setMenu(menu)

    def set_open_button_menu(self, menu):
        self.openPushButton.addActions(menu.actions())
        self.openPushButton.setMenu(menu)

    def fill_context_combo_box(self, contexts_list, current_context=None):
        self.contextComboBox.clear()
        if contexts_list:
            self.contextComboBox.addItems(contexts_list)

        if current_context != None:
            if current_context == '':
                self.contextComboBox.setEditText('')
            else:
                self.contextComboBox.addItem(current_context)
                self.contextComboBox.setCurrentIndex(self.contextComboBox.count()-1)

    def fill_process_combo_box(self, process_dict, current_process=None):
        if current_process:
            current_process = current_process.get('name')

        if process_dict:
            process_list = process_dict.keys()
            process_list.append('publish')
        else:
            process_list = ['publish']  # may be need to add attachment

        self.processComboBox.clear()
        for i, process in enumerate(process_list):
            self.processComboBox.addItem(process)
            if current_process and current_process == process:
                self.processComboBox.setCurrentIndex(i)

    def create_context_combo_box(self):
        self.contextComboBox_freezed = False
        self.contextComboBox.clear()

        self.contextComboBox_clear_button_layout = QtGui.QHBoxLayout(self.contextComboBox)
        self.contextComboBox_clear_button_layout.setContentsMargins(0, 0, 20, 0)
        self.contextComboBox_clear_button_layout.setSpacing(0)
        self.contextComboBox_clear_button = QtGui.QToolButton()
        self.contextComboBox_clear_button.setFixedSize(16, 16)
        self.contextComboBox_clear_button.setIcon(gf.get_icon('unlock', icons_set='ei', color=Qt4Gui.QColor(0, 196, 255, 192), scale_factor=0.8))
        self.contextComboBox_clear_button_layout.insertStretch(0)
        self.contextComboBox_clear_button_layout.addWidget(self.contextComboBox_clear_button)
        self.contextComboBox_clear_button.setHidden(True)

    def freeze_context_combo_box(self):
        self.contextComboBox.setStyleSheet('QComboBox{background-color: rgba(0,192,255,192);}')
        self.contextComboBox_freezed = True
        self.contextComboBox_clear_button.setHidden(False)

    def unfreeze_context_combo_box(self):
        self.contextComboBox.setStyleSheet('')
        self.contextComboBox_freezed = False
        self.contextComboBox_clear_button.setHidden(True)


class Ui_checkInOutWidget(QtGui.QMainWindow):
    def __init__(self, stype, tab_widget, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.tab_name = stype.info['code']
        self.setObjectName(self.tab_name)

        self.is_created = False
        self.is_showed = False

        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/checkin_out_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        # self vars
        self.stype = stype
        self.project = project

        self.tab_widget = tab_widget
        self.tab_label = None
        # self.current_namespace =

        self.process_tree_widget = None
        # self.checkin_options_widget = None

        self.relates_to = 'checkin_checkout'
        # self.checkin_config = cfg_controls.get_checkin()

        env_inst.set_check_tree(self.project.info['code'], 'checkin_out', self.tab_name, self)

        # self.do_creating_ui()

    def get_tab_label(self):
        self.tab_label = gf.create_tab_label(self.tab_widget.objectName(), self.stype)
        return self.tab_label

    def do_creating_ui(self):
        if not self.is_created:
            self.create_ui()

    def create_ui(self):
        self.is_created = True

        # Query Threads
        self.search_suggestions_thread = tc.ServerThread(self)
        self.update_desctiption_thread = tc.ServerThread(self)

        # self.setAcceptDrops(True)
        self.create_search_widget()

        self.create_fast_controls_tool_bar()
        self.create_drop_plate_dock()
        self.create_snapshot_browser_dock()
        self.create_description_dock()
        self.create_search_options_dock()
        self.create_checkin_options_dock()

        self.fill_gear_menu()
        self.fill_collapsable_toolbar()

        self.add_items_to_formats_combo()

        self.controls_actions()
        self.threads_actions()

        # self.readSettings()

    def create_search_widget(self):
        print 'creating search_widget'

        self.search_widget = search_classes.Ui_searchWidget(stype=self.stype, project=self.project, parent_ui=self, parent=self)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.search_widget.sizePolicy().hasHeightForWidth())
        self.search_widget.setSizePolicy(sizePolicy)
        self.setCentralWidget(self.search_widget)

    def create_fast_controls_tool_bar(self):
        self.fast_controls_tool_bar_widget = Ui_fastControlsWidget(stype=self.stype, project=self.project, parent=self)

        self.fast_controls_tool_bar = QtGui.QToolBar()
        self.fast_controls_tool_bar.addWidget(self.fast_controls_tool_bar_widget)
        self.fast_controls_tool_bar.setWindowTitle('Fast controls')
        self.fast_controls_tool_bar.setObjectName('Fast fast_controls_tool_bar')
        # self.fast_controls_tool_bar.toggleViewAction()
        # self.fast_controls_tool_bar.visibilityChanged.connect(lambda: self.fast_controls_tool_bar.setVisible(True))

        self.fast_controls_tool_bar.setFloatable(False)
        self.fast_controls_tool_bar.setAllowedAreas(QtCore.Qt.BottomToolBarArea | QtCore.Qt.TopToolBarArea)

        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.fast_controls_tool_bar)

    def create_drop_plate_dock(self):
        print 'creating drop_plate_dock'

        self.drop_plate_widget = drop_plate_widget.Ui_dropPlateWidget(self)

        self.drop_plate_dock = QtGui.QDockWidget(self)
        self.drop_plate_dock.setWidget(self.drop_plate_widget)
        self.drop_plate_dock.setWindowTitle('Drop Plate')
        self.drop_plate_dock.setObjectName('drop_plate_dock')

        self.drop_plate_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.drop_plate_dock)

    def create_snapshot_browser_dock(self):
        print 'creating snapshot_browser_dock'

        self.snapshot_browser_widget = snapshot_browser_widget.Ui_snapshotBrowserWidget(self)

        self.snapshot_browser_dock = QtGui.QDockWidget(self)
        self.snapshot_browser_dock.setWidget(self.snapshot_browser_widget)
        self.snapshot_browser_dock.setWindowTitle('Snapshot Browser')
        self.snapshot_browser_dock.setObjectName('snapshot_browser_dock')

        self.snapshot_browser_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.snapshot_browser_dock)

    def create_description_dock(self):
        print 'creating description_dock'

        self.description_widget = Ui_descriptionWidget(self.project, self.stype, parent=self)

        self.description_dock = QtGui.QDockWidget(self)
        self.description_dock.setWidget(self.description_widget)
        self.description_dock.setWindowTitle('Description')
        self.description_dock.setObjectName('description_dock')

        self.description_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.description_dock)

    def create_search_options_dock(self):
        print 'creating search_options_dock'

        self.search_options_widget = search_classes.Ui_searchOptionsWidget(parent_ui=self, parent=self)

        self.search_options_dock = QtGui.QDockWidget(self)
        self.search_options_dock.setWidget(self.search_options_widget)
        self.search_options_dock.setWindowTitle('Search Options')
        self.search_options_dock.setObjectName('search_options_dock')

        self.search_options_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.search_options_dock.setHidden(True)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.search_options_dock)

    def create_checkin_options_dock(self):
        print 'creating checkin_options_dock'

        self.checkin_options_widget = Ui_checkInOutOptionsWidget(stype=self.stype, project=self.project, parent=self)

        self.checkin_options_dock = QtGui.QDockWidget(self)
        self.checkin_options_dock.setWidget(self.checkin_options_widget)
        self.checkin_options_dock.setWindowTitle('Checkin Options')
        self.checkin_options_dock.setObjectName('checkin_options_dock')

        self.checkin_options_dock.setFeatures(
            QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

        self.checkin_options_dock.setHidden(True)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.checkin_options_dock)

        # IMPORTANT
        # print self.checkin_options_widget.get_config()
        # print gf.get_value_from_config(self.checkin_options_widget.get_config(), 'askBeforeSaveCheckBox')

    # def create_ui(self):
    #     self.is_created = True
    #
    #     # Query Threads
    #     self.update_desctiption_thread = tc.ServerThread(self)
    #
    #     self.create_serachline()
    #     self.create_save_button()
    #     self.create_search_options_group_box()
    #     self.create_search_results_group_box()
    #     self.create_checkin_options_dialog()
    #     self.create_gear_menu_popup()
    #     self.create_richedit()
    #     self.create_snapshot_browser()
    #     self.create_drop_plate()
    #
    #     # self.add_items_to_formats_combo()
    #     print 'ADDING MAYA FORMATS'
    #     self.controls_actions()
    #     self.threads_actions()
    #
    #     self.readSettings()

    # def dragEnterEvent(self, event):
    #     if event.mimeData().hasUrls:
    #         event.accept()
    #         self.ui_drop_plate.setMinimumWidth(350)
    #     else:
    #         event.ignore()
    #
    # def dropEvent(self, event):
    #     if event.mimeData().hasUrls:
    #         self.ui_drop_plate.setMinimumWidth(0)
    #     else:
    #         event.ignore()
    #         self.ui_drop_plate.setMinimumWidth(0)

    def add_items_to_formats_combo(self):
        if env_mode.get_mode() == 'maya':
            self.fast_controls_tool_bar_widget.formatTypeComboBox.addItem('mayaAscii')
            self.fast_controls_tool_bar_widget.formatTypeComboBox.addItem('mayaBinary')
        else:
            self.fast_controls_tool_bar_widget.formatTypeComboBox.setVisible(False)
            # self.fast_controls_tool_bar_widget.formatTypeComboBox.addItem('all')

    # def create_serachline(self):
    #     effect = QtGui.QGraphicsDropShadowEffect(self.searchLineEdit)
    #     effect.setOffset(2, 2)
    #     tab_color = self.stype.info['color']
    #     if tab_color:
    #         t_c = gf.hex_to_rgb(tab_color, alpha=128, tuple=True)
    #         effect.setColor(Qt4Gui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
    #         effect.setBlurRadius(15)
    #     else:
    #         effect.setColor(Qt4Gui.QColor(0, 0, 0, 96))
    #         effect.setBlurRadius(5)
    #     self.searchLineEdit.setGraphicsEffect(effect)

    # def create_drop_plate(self):
    #     self.ui_drop_plate = drop_plate_widget.Ui_dropPlateWidget(self)
    #     self.dropPlateLayout.addWidget(self.ui_drop_plate)

    # def create_richedit(self):
    #     self.ui_richedit = richedit_widget.Ui_richeditWidget(self.descriptionTextEdit)
    #     self.editorLayout.addWidget(self.ui_richedit)

    # def create_snapshot_browser(self):
    #     self.snapshot_browser_widget = snapshot_browser_widget.Ui_snapshotBrowserWidget(self)
    #     self.snapshotBrowserLayout.addWidget(self.snapshot_browser_widget)

    def get_fast_controls_widget(self):
        return self.fast_controls_tool_bar_widget

    def get_snapshot_browser(self):
        return self.snapshot_browser_widget

    def get_description_widget(self):
        return self.description_widget

    def get_drop_plate_widget(self):
        return self.drop_plate_widget

    def get_search_widget(self):
        return self.search_widget

    def get_search_options_widget(self):
        return self.search_options_widget

    def get_checkin_options_widget(self):
        return self.checkin_options_widget

    def get_checkin_options_widget_config(self):
        return self.checkin_options_widget.checkinPageWidget

    # def create_gear_menu_popup(self):
    #     self.gearMenuToolButton.setIcon(gf.get_icon('cog'))
    #     self.gearMenuToolButton.setMinimumSize(22, 22)
    #
    #     self.filter_process = QtGui.QAction('Filter Process', self.gearMenuToolButton)
    #     self.filter_process.triggered.connect(self.create_process_tree_widget)
    #     self.refresh_results = QtGui.QAction('Refresh results', self.gearMenuToolButton)
    #     self.refresh_results.triggered.connect(self.refresh_results)
    #     self.clear_results = QtGui.QAction('Close all Search-Tabs', self.gearMenuToolButton)
    #     self.clear_results.triggered.connect(self.close_all_search_tabs)
    #     self.search_options = QtGui.QAction('Toggle Search options', self.gearMenuToolButton)
    #     self.search_options.triggered.connect(self.toggle_search_group_box)
    #
    #     self.gearMenuToolButton.addAction(self.filter_process)
    #     self.gearMenuToolButton.addAction(self.refresh_results)
    #     self.gearMenuToolButton.addAction(self.clear_results)
    #     self.gearMenuToolButton.addAction(self.search_options)

    @gf.catch_error
    def create_process_tree_widget(self):
        if not self.process_tree_widget:
            self.process_tree_widget = search_classes.Ui_processFilterDialog(
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
            self.process_tree_widget = search_classes.Ui_processFilterDialog(
                parent_ui=self,
                parent=self,
                project=self.project,
                stype=self.stype
            )
            return self.process_tree_widget.get_ignore_dict()

    def refresh_current_results(self):
        self.search_widget.refresh_current_results()

    # def close_all_search_tabs(self):
    #     self.search_results_widget.close_all_tabs()

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

    def checkin_context_menu(self, tool_button=True, mode=None):

        menu = MenuWithLayout()

        edit_info = QtGui.QAction('Edit Info', self)
        edit_info.setIcon(gf.get_icon('edit'))
        edit_info.triggered.connect(self.edit_existing_sobject)

        delete_sobject = QtGui.QAction('Delete', self)
        delete_sobject.setIcon(gf.get_icon('remove'))
        delete_sobject.triggered.connect(self.delete_sobject)

        save_snapshot = QtGui.QAction('Save snapshot', self)
        save_snapshot.setIcon(gf.get_icon('save'))

        save_snapshot.triggered.connect(self.save_file)

        open_snapshot = QtGui.QAction('Open snapshot', self)
        open_snapshot.setIcon(gf.get_icon('folder'))

        open_snapshot.triggered.connect(self.open_file)

        save_selected_snapshot = QtGui.QAction('Save selected objects', self)
        save_selected_snapshot.triggered.connect(lambda: self.save_file(selected_objects=[True]))

        save_snapshot_revision = QtGui.QAction('Add revision (override current file)', self)
        save_snapshot_revision.triggered.connect(lambda: self.save_file(save_revision=True))

        save_selected_snapshot_revision = QtGui.QAction('Add revision for selected objects', self)
        save_selected_snapshot_revision.triggered.connect(lambda: self.save_file(selected_objects=[True], save_revision=True))

        update_snapshot = QtGui.QAction('Update file only (without revision)', self)
        update_snapshot.triggered.connect(lambda: self.save_file(update_snapshot=True))

        # update_selected_snapshot = QtGui.QAction('Update selected', self.savePushButton)
        # update_selected_snapshot.triggered.connect(lambda: self.prnt(0))

        # update_playblast = QtGui.QAction('Update Playblast', self.savePushButton)
        # update_playblast.triggered.connect(lambda: self.prnt(0))

        delete_snapshot = QtGui.QAction('Delete', self)
        delete_snapshot.setIcon(gf.get_icon('remove'))
        delete_snapshot.triggered.connect(self.delete_sobject)

        # checkin_options = QtGui.QAction('Checkin Options toggle', self.savePushButton)
        # checkin_options.triggered.connect(self.toggle_checkin_options_group_box)

        # if not tool_button:
        if mode == 'sobject':
            open_snapshot_additional = menu.addAction(open_snapshot, True)
            open_snapshot_additional.clicked.connect(self.open_file_options)

            menu.addSeparator()
            save_snapshot_additional = menu.addAction(save_snapshot, True)
            save_snapshot_additional.clicked.connect(self.save_file_options)

            save_selected_snapshot_additional = menu.addAction(save_selected_snapshot, True)
            save_selected_snapshot_additional.clicked.connect(self.export_selected_file_options)

            menu.addSeparator()

            save_snapshot_revision_additional = menu.addAction(save_snapshot_revision, True)
            save_snapshot_revision_additional.clicked.connect(self.save_file_options)

            save_selected_snapshot_revision_additional = menu.addAction(save_selected_snapshot_revision, True)
            save_selected_snapshot_revision_additional.clicked.connect(self.export_selected_file_options)

            menu.addSeparator()

            update_snapshot_additional = menu.addAction(update_snapshot, True)
            update_snapshot_additional.clicked.connect(self.export_selected_file_options)

            # menu.addAction(update_selected_snapshot)
            # menu.addAction(update_playblast)
            menu.addSeparator()
            menu.addAction(edit_info)
            menu.addSeparator()
            menu.addAction(delete_sobject)
            # menu.addSeparator()
            # menu.addAction(checkin_options)

        if mode == 'snapshot':
            open_snapshot_additional = menu.addAction(open_snapshot, True)
            open_snapshot_additional.clicked.connect(self.open_file_options)

            menu.addSeparator()

            save_snapshot_additional = menu.addAction(save_snapshot, True)
            save_snapshot_additional.clicked.connect(self.save_file_options)

            save_selected_snapshot_additional = menu.addAction(save_selected_snapshot, True)
            save_selected_snapshot_additional.clicked.connect(self.export_selected_file_options)

            menu.addSeparator()

            save_snapshot_revision_additional = menu.addAction(save_snapshot_revision, True)
            save_snapshot_revision_additional.clicked.connect(self.save_file_options)

            save_selected_snapshot_revision_additional = menu.addAction(save_selected_snapshot_revision, True)
            save_selected_snapshot_revision_additional.clicked.connect(self.export_selected_file_options)

            menu.addSeparator()

            update_snapshot_additional = menu.addAction(update_snapshot, True)
            update_snapshot_additional.clicked.connect(self.export_selected_file_options)

            menu.addSeparator()
            menu.addAction(edit_info)
            menu.addSeparator()
            menu.addAction(delete_snapshot)
            # menu.addSeparator()
            # menu.addAction(checkin_options)

        if mode == 'process':
            save_snapshot_additional = menu.addAction(save_snapshot, True)
            save_snapshot_additional.clicked.connect(self.save_file_options)
            # menu.addAction(save_snapshot)
            save_selected_snapshot_additional = menu.addAction(save_selected_snapshot, True)
            save_selected_snapshot_additional.clicked.connect(self.export_selected_file_options)

            # menu.addAction(save_selected_snapshot)

            # menu.addSeparator()
            # menu.addAction(save_snapshot_revision)
            # menu.addAction(save_selected_snapshot_revision)
            # menu.addSeparator()
            # menu.addAction(update_snapshot)
            # menu.addAction(update_selected_snapshot)
            # menu.addAction(update_playblast)
            # menu.addSeparator()
            # menu.addAction(checkin_options)

        # if mode == 'child':
        #     menu.addAction(checkin_options)

        return menu

    # def create_search_results_group_box(self):
    #     self.search_results_widget = search_classes.Ui_resultsGroupBoxWidget(parent_ui=self, parent=self)
    #     self.searchOptionsSplitter.addWidget(self.search_results_widget)
    #     # self.search_results_widget.add_tab()

    # def create_checkin_options_dialog(self):
    #     self.checkin_options_widget = Ui_checkInOutOptionsWidget(stype=self.stype, project=self.project, parent=self)
    #
    #     # self.checkin_options_widget.show()
    #
    #     # self.dropPlateLayout.addWidget(self.checkin_options_widget, 2)
    #     # self.checkinOptionsLayout.addWidget(self.checkin_options_widget)
    #     # self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.DownArrow)
    #     self.toggleSaveOptionsToolButton.setIcon(gf.get_icon('toggle-on'))

    # def toggle_checkin_options_group_box(self):
    #     if self.checkin_options_widget.isVisible():
    #         self.set_checkin_options_group_box_state(True)
    #     else:
    #         self.set_checkin_options_group_box_state(False)
    #
    # def set_checkin_options_group_box_state(self, hidden=False):
    #     if hidden:
    #         # self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.UpArrow)
    #         self.toggleSaveOptionsToolButton.setIcon(gf.get_icon('toggle-off'))
    #         self.checkin_options_widget.hide()
    #     else:
    #         # self.toggleSaveOptionsToolButton.setArrowType(QtCore.Qt.DownArrow)
    #         self.toggleSaveOptionsToolButton.setIcon(gf.get_icon('toggle-on'))
    #         self.checkin_options_widget.show()

    # def create_save_button(self):
    #     self.fast_controls_tool_bar_widget.savePushButton.setMenu(self.checkin_context_menu())

    def create_search_options_group_box(self):
        self.searchOptionsGroupBox = search_classes.Ui_searchOptionsWidget(parent_ui=self, parent=self)
        self.searchOptionsSplitter.addWidget(self.searchOptionsGroupBox)
        # self.searchOptionsLayout.addWidget(self.searchOptionsGroupBox)

    @gf.catch_error
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

    def controls_actions(self):
        """
        Actions for the check tab
        """
        # # Search line, and combo box with context
        # self.searchLineEdit.returnPressed.connect(self.do_search)
        # # self.searchLineEdit.mouseDoubleClickEvent = self.searchLineDoubleClick
        # self.searchLineEdit.mousePressEvent = self.searchLineSingleClick
        #
        # self.searchLineEdit.textEdited.connect(self.search_suggestions_start)
        # self.search_suggestions_elapsed = QtCore.QElapsedTimer()
        # self.search_suggestions_timer = QtCore.QTimer()
        # self.search_suggestions_elapsed.start()
        # self.search_suggestions_timer.timeout.connect(lambda: self.search_suggestions_end(key=self.searchLineEdit.text()))

        # self.saveDescriprionButton.clicked.connect(lambda: self.update_desctiption(run_thread=True))

        # self.findOpenedPushButton.clicked.connect(self.find_opened_sobject)

        # Save, Update, Add New buttons
        self.fast_controls_tool_bar_widget.savePushButton.clicked.connect(self.save_file)

        # self.toggleSaveOptionsToolButton.clicked.connect(self.toggle_checkin_options_group_box)

    # def customize_ui(self):
    #     # if env_mode.get_mode() == 'standalone':
    #     # self.findOpenedPushButton.setVisible(False)
    #     # self.addNewtButton.setIcon(gf.get_icon('plus-square-o'))
    #     self.create_collapsable_toolbar()

    def fill_gear_menu(self):

        self.filter_process = QtGui.QAction('Filter Process', self)
        self.filter_process.triggered.connect(self.create_process_tree_widget)
        self.refresh_results = QtGui.QAction('Refresh results', self)
        # self.refresh_results.triggered.connect(self.refresh_current_results)
        self.clear_results = QtGui.QAction('Close all Search-Tabs', self)
        # self.clear_results.triggered.connect(self.close_all_search_tabs)
        self.search_options = QtGui.QAction('Toggle Search options', self)
        self.search_options.triggered.connect(self.toggle_search_group_box)

        self.search_widget.add_action_to_gear_menu(self.filter_process)
        self.search_widget.add_action_to_gear_menu(self.refresh_results)
        self.search_widget.add_action_to_gear_menu(self.clear_results)
        self.search_widget.add_action_to_gear_menu(self.search_options)

    def fill_collapsable_toolbar(self):
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

        self.add_new_sobject_button = QtGui.QToolButton()
        self.add_new_sobject_button.setMaximumSize(22, 22)
        self.add_new_sobject_button.setAutoRaise(True)
        self.add_new_sobject_button.setIcon(gf.get_icon('plus-square-o'))
        self.add_new_sobject_button.clicked.connect(self.add_new_sobject)

        self.find_opened_sobject_button = QtGui.QToolButton()
        self.find_opened_sobject_button.setMaximumSize(22, 22)
        self.find_opened_sobject_button.setAutoRaise(True)
        self.find_opened_sobject_button.setIcon(gf.get_icon('bolt'))
        self.find_opened_sobject_button.clicked.connect(self.find_opened_sobject)

        self.search_widget.add_widget_to_collapsable_toolbar(self.filter_process_button)
        self.search_widget.add_widget_to_collapsable_toolbar(self.toggle_search_options_button)
        self.search_widget.add_widget_to_collapsable_toolbar(self.add_new_sobject_button)
        if env_mode.get_mode() == 'maya':
            self.search_widget.add_widget_to_collapsable_toolbar(self.find_opened_sobject_button)

    def threads_actions(self):
        # Threads Actions
        self.search_suggestions_thread.finished.connect(lambda: self.search_suggestions_end(popup_suggestion=True))
        self.update_desctiption_thread.finished.connect(lambda: self.update_desctiption(update_description=True))

    # def do_search(self, search_query=None, search_by=None, new_tab=False):
    #     self.search_results_widget.do_search(
    #         search_query=search_query,
    #         search_by=search_by,
    #         new_tab=new_tab
    #     )

    @gf.catch_error
    def find_opened_sobject(self):
        skey = mf.get_skey_from_scene()
        env_inst.ui_main.go_by_skey(skey, 'checkin')

    # def search_suggestions_start(self):
    #     if self.search_suggestions_elapsed.elapsed() > 500:
    #         self.search_suggestions_timer.start(200)

    # def update_desctiption(self, run_thread=False, update_description=False):
    #     current_widget = self.search_results_widget.get_current_widget()
    #     current_tree_widget_item = current_widget.get_current_tree_widget_item()
    #
    #     if run_thread:
    #         if current_tree_widget_item and current_tree_widget_item.type in ['snapshot', 'sobject']:
    #             self.update_desctiption_thread.kwargs = dict(
    #                 search_key=current_tree_widget_item.get_skey(only=True),
    #                 description=gf.simplify_html(self.descriptionTextEdit.toHtml())
    #             )
    #             self.update_desctiption_thread.routine = tc.update_description
    #             self.update_desctiption_thread.start()
    #
    #     if update_description:
    #         update = tc.treat_result(self.update_desctiption_thread)
    #         if update.isFailed():
    #             if update.result == QtGui.QMessageBox.ApplyRole:
    #                 update.run()
    #                 self.update_desctiption(update_description=True)
    #             elif update.result == QtGui.QMessageBox.ActionRole:
    #                 env_inst.offline = True
    #                 env_inst.ui_main.open_config_dialog()
    #
    #         if not update.isFailed():
    #             current_tree_widget_item.update_description(self.descriptionTextEdit.toPlainText())

    def get_current_tree_widget(self):
        return self.search_widget.get_current_tree_widget()

    # def get_is_separate_versions(self):
    #     current_tabbed_widget = self.search_results_widget.get_current_widget()
    #     return current_tabbed_widget.get_is_separate_versions()
    #
    def refresh_current_snapshot_tree(self, item):
        # self.search_results_widget.update_item(item)
        self.search_widget.search_results_widget.update_item_tree(item)

    def get_current_item_paths(self):
        # TODO REWRITE THIS THING with multiple file in one snapshot in mind
        current_widget = self.get_current_tree_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()
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

    # Opening functions
    @gf.catch_error
    def open_file_options(self):
        file_path = self.get_current_item_paths()[0]
        current_widget = self.search_results_widget.get_current_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        self.open_dialog = maya_dialogs.Ui_openOptionsWidget(file_path, current_tree_widget_item)
        self.open_dialog.show()

    def import_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.current_tree_item_widget

        if env_mode.get_mode() == 'maya':
            self.import_dialog = maya_dialogs.Ui_importOptionsWidget(file_path, nested_item)
            self.import_dialog.show()

    def reference_file_options(self):
        file_path = self.get_current_item_paths()[0]
        nested_item = self.current_tree_item_widget

        if env_mode.get_mode() == 'maya':
            self.reference_dialog = maya_dialogs.Ui_referenceOptionsWidget(file_path, nested_item)
            self.reference_dialog.show()

    @gf.catch_error
    def open_file(self):
        print 'getting paths'
        file_path, dir_path, all_process = self.get_current_item_paths()

        print 'opening'

        if env_mode.get_mode() == 'maya':
            print 'opening maya'
            mf.open_scene(file_path, dir_path, all_process)
        else:
            print 'opening standalone'
            current_widget = self.get_current_tree_widget()
            current_tree_widget_item = current_widget.get_current_tree_widget_item()
            current_snapshot = current_tree_widget_item.get_snapshot()
            for tp, fl in current_snapshot.get_files_objects(group_by='type').items():
                if tp not in ['web', 'icon']:
                    fl[0].open_file()
                    break

            # gf.open_file_associated(file_path)

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

    # Saving functions
    def checkin_from_droplist(self, search_key, context, description, save_revision=False, snapshot_version=None, create_icon=True):

        selected_items = self.drop_plate_widget.get_selected_items()

        print selected_items

        # selected_items = None
        if selected_items:

            file_types = []
            file_names = []
            file_paths = []
            exts = []
            subfolders = []
            postfixes = []

            for item in selected_items:
                if item.get_type() == 'fl':
                    postfixes.append('')
                    subfolders.append('')
                    exts.append(item.get_file_ext())
                    file_types.append(item.get_base_file_type())
                    file_names.append(item.get_file_name())
                    file_paths.append(gf.form_path(item.get_all_files_list(True)))
                elif item.get_type() == 'seq':
                    print 'sequence'
                elif item.get_type() == 'udim':
                    print 'UDIM'

            mode = 'inplace'

            return tc.checkin_file(
                search_key=search_key,
                context=context,
                description=description,
                version=snapshot_version,
                is_revision=save_revision,
                update_versionless=self.get_update_versionless(),
                file_types=file_types,
                file_names=file_names,
                file_paths=file_paths,
                exts=exts,
                subfolders=subfolders,
                postfixes=postfixes,
                keep_file_name=False,
                repo_name=self.get_current_repo(),
                mode=mode,
                create_icon=create_icon,
                parent_wdg=self,
                ignore_keep_file_name=False,
            )

    def checkin_from_path(self, search_key, context, description, explicit_paths=None):

        if explicit_paths:

            file_types = []
            file_names = []
            file_paths = []
            exts = []
            subfolders = []
            postfixes = []

            for path in explicit_paths:
                file_types.append('main')
                file_names.append(gf.extract_filename(path))
                exts.append(gf.extract_extension(path)[0])
                subfolders.append('')
                postfixes.append('')
                file_path = gf.form_path(path)
                file_paths.append(file_path)

            mode = 'inplace'

            create_icon = False
            if context == 'icon':
                create_icon = True

            return tc.checkin_file(
                search_key=search_key,
                context=context,
                description=description,
                version=None,
                update_versionless=self.get_update_versionless(),
                file_types=file_types,
                file_names=file_names,
                file_paths=file_paths,
                exts=exts,
                subfolders=subfolders,
                postfixes=postfixes,
                keep_file_name=False,
                repo_name=self.get_current_repo(),
                mode=mode,
                create_icon=create_icon,
                parent_wdg=self,
            )

    def checkin_from_maya(self, search_key, context, description, save_revision=False, snapshot_version=None,
                          selected_objects=None):

        ext_type = self.fast_controls_tool_bar_widget.formatTypeComboBox.currentText()
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

        file_types = ['main', 'playblast']
        file_names = ['scene', 'playblast']
        file_paths = ['', '']
        exts = [types[ext_type], 'jpg']
        subfolders = ['', '__preview']
        postfixes = ['', 'playblast']

        mode = 'inplace'

        return tc.checkin_file(
            search_key=search_key,
            context=context,
            description=description,
            version=snapshot_version,
            is_revision=save_revision,
            update_versionless=self.get_update_versionless(),
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
            parent_wdg=self,
            ignore_keep_file_name=True,
            checkin_app='maya',
            selected_objects=selected_objects[0],
            ext_type=ext_type,
            setting_workspace=False
        )

    @gf.catch_error
    def save_file_options(self):

        if env_mode.get_mode() == 'maya':
            mf.wrap_save_options(self.project.info['code'], 'checkin_out', self.tab_name)

    @gf.catch_error
    def export_selected_file_options(self):

        if env_mode.get_mode() == 'maya':
            mf.wrap_export_selected_options(self.project.info['code'], 'checkin_out', self.tab_name)

    def fast_save(self):
        print 'SAVING FAST'
        skey = mf.get_skey_from_scene()

        print skey
        skey_dict = tc.parce_skey(skey, True)

        saved = self.checkin_from_maya(
            search_key=skey_dict['search_key'],
            context=skey_dict['context'],
            description=None,
            save_revision=False,
            snapshot_version=None,
            selected_objects=False,
        )

        if saved:
            print 'ALL GOOD ;)'
            current_widget = self.get_current_tree_widget()
            # self.description_widget.set_item(None)
            # self.fast_controls_tool_bar_widget.set_item(None)
            current_widget.update_current_items_trees()
            # self.drop_plate_widget.fromDropListCheckBox.setChecked(False)

    @gf.catch_error
    def save_file(self, selected_objects=None, save_revision=False, update_snapshot=False):
        current_widget = self.get_current_tree_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        print current_widget, 'current_widget'
        print current_tree_widget_item, 'current_tree_widget_item'

        current_snapshot_version = None
        if current_tree_widget_item.type == 'snapshot' and save_revision:
            snapshot = current_tree_widget_item.get_snapshot()
            if snapshot:
                current_snapshot_version = snapshot.info.get('version')
                if current_snapshot_version in [-1, 0]:
                    current_snapshot_version = None

        if current_tree_widget_item:
            # self.fast_controls_tool_bar_widget.set_save_button_enabled(False)
            search_key = current_tree_widget_item.get_skey(parent=True)
            print search_key
            context = current_tree_widget_item.get_context(True, self.fast_controls_tool_bar_widget.contextComboBox.currentText()).replace(' ', '_')

            description = self.description_widget.get_description('plain')
            print description

            checkin_from_droplist = self.drop_plate_widget.fromDropListCheckBox.isChecked()

            if env_mode.get_mode() == 'maya':
                if checkin_from_droplist:
                    saved = self.checkin_from_droplist(
                        search_key=search_key,
                        context=context,
                        description=description,
                        save_revision=save_revision,
                        snapshot_version=current_snapshot_version,
                    )
                else:
                    saved = self.checkin_from_maya(
                        search_key=search_key,
                        context=context,
                        description=description,
                        save_revision=save_revision,
                        snapshot_version=current_snapshot_version,
                        selected_objects=selected_objects,
                    )
                if saved:
                    self.description_widget.set_item(None)
                    self.fast_controls_tool_bar_widget.set_item(None)
                    current_widget.update_current_items_trees()
                    self.drop_plate_widget.fromDropListCheckBox.setChecked(False)

            if env_mode.get_mode() == 'standalone':
                saved = self.checkin_from_droplist(
                    search_key=search_key,
                    context=context,
                    description=description,
                    save_revision=save_revision,
                    snapshot_version=current_snapshot_version,
                )
                if saved:
                    self.description_widget.set_item(None)
                    self.fast_controls_tool_bar_widget.set_item(None)
                    current_widget.update_current_items_trees()
        else:
            print 'nothing happen'
            self.savePushButton.setEnabled(False)

    def get_update_versionless(self):

        current_widget = self.get_current_tree_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()
        if not current_tree_widget_item:
            return True
        elif current_tree_widget_item.get_checkin_mode_options() == 'multi_file':
            return False
        else:
            return self.checkin_options_widget.checkinPageWidget.updateVersionlessCheckBox.isChecked()

    def get_current_repo(self):
        current_idx = self.checkin_options_widget.checkinPageWidget.repositoryComboBox.currentIndex()
        return self.checkin_options_widget.checkinPageWidget.repositoryComboBox.itemData(current_idx, QtCore.Qt.UserRole)

    @gf.catch_error
    def add_new_sobject(self):
        """
        Open window for adding new sobject
        """
        self.add_sobject = addsobject_widget.Ui_addTacticSobjectWidget(stype=self.stype, parent=self)
        self.add_sobject.show()

    @gf.catch_error
    def delete_snapshot_sobject(self):

        current_widget = self.get_current_tree_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if current_tree_widget_item:
            # self.savePushButton.setEnabled(False)
            search_key = current_tree_widget_item.get_skey(only=True)

            print(search_key, 'deleting...')
            print current_tree_widget_item.snapshot
            print current_tree_widget_item.files
            snapshot_del_confirm = tc.snapshot_delete_confirm(snapshot=current_tree_widget_item.snapshot, files=current_tree_widget_item.files)

            if snapshot_del_confirm[0]:
                if tc.delete_sobject_snapshot(
                        sobject=search_key,
                        delete_snapshot=snapshot_del_confirm[3],
                        search_keys=snapshot_del_confirm[1],
                        files_paths=snapshot_del_confirm[2]
                ):
                    self.update_snapshot_tree(current_tree_widget_item)

    @gf.catch_error
    def delete_sobject(self):


        current_widget = self.get_current_tree_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()
        print current_tree_widget_item
        current_tree_widget_item.delete_current_sobject()

        stype = current_tree_widget_item.stype

        print stype
        print self.stype

        # self.edit_sobject = addsobject_widget.Ui_addTacticSobjectWidget(
        #     stype=stype,
        #     parent_stype=self.stype,
        #     item=current_tree_widget_item,
        #     view='edit',
        #     parent=self,
        # )
        # self.edit_sobject.setWindowTitle('Editing info for {0}'.format(current_tree_widget_item.sobject.info.get('name')))
        # self.edit_sobject.show()


        # current_widget = self.get_current_tree_widget()
        # current_tree_widget_item = current_widget.get_current_tree_widget_item()

        # if current_tree_widget_item:
        #     # self.savePushButton.setEnabled(False)
        #     search_key = current_tree_widget_item.get_skey(parent=True)
        #
        #     tc.delete_sobject_item(skey=search_key)
        #
        #     print(search_key, 'deleting...')

    @gf.catch_error
    def edit_existing_sobject(self):
        """
        Open window for Editing sobject
        """
        current_widget = self.get_current_tree_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()
        stype = current_tree_widget_item.stype

        print stype
        print self.stype

        self.edit_sobject = addsobject_widget.Ui_addTacticSobjectWidget(
            stype=stype,
            parent_stype=self.stype,
            item=current_tree_widget_item,
            view='edit',
            parent=self,
        )
        self.edit_sobject.setWindowTitle('Editing info for {0}'.format(current_tree_widget_item.sobject.info.get('name')))
        self.edit_sobject.show()

    def open_menu(self):
        current_widget = self.get_current_tree_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if current_tree_widget_item:
            menu = self.checkin_context_menu(False, mode=current_tree_widget_item.type)
            if menu:
                menu.exec_(Qt4Gui.QCursor.pos())

    def set_save_button_menu(self):
        current_widget = self.get_current_tree_widget()
        current_tree_widget_item = current_widget.get_current_tree_widget_item()

        if current_tree_widget_item:
            self.fast_controls_tool_bar_widget.set_save_button_menu(
                self.checkin_context_menu(True, mode=current_tree_widget_item.type))

    def set_settings_from_dict(self, settings_dict=None, apply_checkin_options=True, apply_search_options=True):
        self.do_creating_ui()
        self.is_showed = True

        if not settings_dict:
            settings_dict = {}
        else:
            settings_dict = json.loads(settings_dict)

        self.search_widget.set_settings_from_dict(settings_dict.get('search_widget'))
        self.drop_plate_widget.set_settings_from_dict(settings_dict.get('drop_plate_dock'))
        self.snapshot_browser_widget.set_settings_from_dict(settings_dict.get('snapshot_browser_dock'))
        self.checkin_options_widget.set_settings_from_dict(settings_dict.get('checkin_options_dock'))

        self.restoreState(QtCore.QByteArray.fromHex(str(settings_dict.get('main_state'))))

        # self.searchLineEdit.setText(settings_dict.get('searchLineEdit'))
        # self.set_checkin_options_group_box_state(bool(int(settings_dict.get('checkinOptionsToggle'))))
        # self.set_search_group_box_state((bool(int(settings_dict.get('searchOptionsToggle')))))
        # self.commentsSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('commentsSplitter')))
        # self.descriptionSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('descriptionSplitter')))
        # # self.imagesSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('imagesSplitter')))
        # self.dropPlateSplitter.restoreState(QtCore.QByteArray.fromHex(settings_dict.get('dropPlateSplitter')))
        # # self.get_current_tree_widget().resultsSplitter.restoreState(
        # #     QtCore.QByteArray.fromHex(settings_dict.get('resultsSplitter')))
        #
        # if apply_checkin_options:
        #     checkin_options_settings_dict = settings_dict.get('checkin_options_settings_dict')
        #     if checkin_options_settings_dict:
        #         checkin_options_settings_dict = ast.literal_eval(checkin_options_settings_dict)
        #     self.checkin_options_widget.set_settings_from_dict(checkin_options_settings_dict)
        #
        # if apply_search_options:
        #     search_options_settings_dict = settings_dict.get('search_options_settings_dict')
        #     if search_options_settings_dict:
        #         search_options_settings_dict = ast.literal_eval(search_options_settings_dict)
        #     self.searchOptionsGroupBox.set_settings_from_dict(search_options_settings_dict)

    def get_settings_dict(self, force=False):

        if force and not self.is_created:
            self.do_creating_ui()
        elif not self.is_created:
            return None

        # print self.checkin_options_widget.get_settings_dict()

        settings_dict = {
            'search_widget': self.search_widget.get_settings_dict(),
            'drop_plate_dock': self.drop_plate_widget.get_settings_dict(),
            'snapshot_browser_dock': self.snapshot_browser_widget.get_settings_dict(),
            'search_options_dock': {},
            'checkin_options_dock': self.checkin_options_widget.get_settings_dict(),
            'main_state': str(self.saveState().toHex()),
        }

        return settings_dict

    def readSettings(self):
        """
        Reading Settings
        """

        # print 'MAINWINDOW SETTING READ'

        tab_name = self.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(
            self.project.info['type'],
            self.project.info['code'],
            tab_name[1]
        )
        self.settings.beginGroup(group_path)

        settings_dict = self.settings.value('settings_dict', None)

        self.set_settings_from_dict(settings_dict)
        # print settings_dict, self, 'settings_dict'

        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """

        # print 'MAINWINDOW SETTING WRITTEN'

        group_path = '{0}/{1}/{2}'.format(
            self.project.info['type'],
            self.project.info['code'],
            self.tab_name.split('/')[1]
        )
        self.settings.beginGroup(group_path)

        settings_dict = self.get_settings_dict()

        # self.settings.setValue('geom', self.geometry())

        if settings_dict:
            self.settings.setValue('settings_dict', json.dumps(settings_dict))
        self.settings.endGroup()

    def closeEvent(self, event):
        if self.is_showed:
            self.writeSettings()
            # closing search_widget
            self.search_widget.close()

        event.accept()

    def showEvent(self, event):
        event.accept()

        self.do_creating_ui()

    def paintEvent(self, event):
        event.accept()

        if not self.is_showed:
            self.readSettings()
            self.is_showed = True
