import datetime
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.global_functions as gf
import thlib.tactic_classes as tc
from thlib.environment import env_inst, env_server, env_tactic, dl
import thlib.ui.misc.ui_collapsable as ui_collapsable
import thlib.ui.misc.ui_debuglog as ui_debuglog


class Ui_collapsableWidget(QtGui.QWidget, ui_collapsable.Ui_collapsableWidget):
    collapsed = QtCore.Signal(object)

    def __init__(self, text=None, state=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.collapse_state = False
        self.__collapsedTex = ''
        self.__text = ''

        self.setText(text)
        self.setCollapsed(state)

        self.create_ui()

    def create_ui(self):
        self.collapseToolButton.setMaximumHeight(26)

        self.controls_actions()

        self.custom_style_sheet()

    def custom_style_sheet(self):
        self.collapseToolButton.setStyleSheet(
            'QToolButton {'
            'background: rgba(96, 96, 96, 32);'
            'border: 0px; border-radius: 3px; padding: 0px 0px;'
            'border-left: 2px solid rgb(128, 128, 128); border-right: 2px solid rgb(128, 128, 128);}'
            'QToolButton:pressed {'
            'background: rgba(128, 128, 128, 32)}'
        )

    def controls_actions(self):
        self.collapseToolButton.toggled.connect(self.__toggleCollapseState)

    def setText(self, text):
        self.__text = text
        self.collapseToolButton.setText(self.__text)

    def setCollapsedText(self, text):
        self.__collapsedTex = text
        self.collapseToolButton.setText(self.__collapsedTex)

    def setLayout(self, layout):
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.widget.setLayout(layout)

    def setCollapsed(self, state):
        if state:
            self.collapse_state = True
            self.collapseToolButton.setIcon(gf.get_icon('angle-right'))
            self.widget.setHidden(True)
            self.collapseToolButton.setChecked(False)
            if self.__collapsedTex:
                self.setCollapsedText(self.__collapsedTex)
        else:
            self.collapse_state = False
            self.collapseToolButton.setIcon(gf.get_icon('angle-down'))
            self.widget.setHidden(False)
            self.collapseToolButton.setChecked(True)
            self.setText(self.__text)

    def setCollapseState(self, state):
        if state:
            self.collapseToolButton.toggle()

    def __toggleCollapseState(self):
        if self.collapse_state:
            self.setCollapsed(False)
            self.collapsed.emit(False)
        else:
            self.setCollapsed(True)
            self.collapsed.emit(True)

    def isCollapsed(self):
        if self.collapse_state:
            return True
        else:
            return False


class Ui_horizontalCollapsableWidget(QtGui.QWidget):
    def __init__(self, text=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()

        self.collapse_state = False
        self.__collapsedTex = ''
        self.__text = ''

        self.setText(text)
        self.__controlsActions()

    def create_ui(self):
        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget = QtGui.QWidget(self)
        self.widget.setObjectName("widget")
        self.horizontalLayout.addWidget(self.widget)
        self.collapseToolButton = QtGui.QToolButton(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.collapseToolButton.sizePolicy().hasHeightForWidth())
        self.collapseToolButton.setSizePolicy(sizePolicy)
        self.collapseToolButton.setMaximumWidth(12)
        self.collapseToolButton.setAutoRaise(True)
        self.collapseToolButton.setObjectName("collapseToolButton")
        self.horizontalLayout.addWidget(self.collapseToolButton)
        self.horizontalLayout.setStretch(1, 1)

    def __controlsActions(self):
        self.collapseToolButton.clicked.connect(self.__toggleCollapseState)

    def setText(self, text):
        self.__text = text
        self.collapseToolButton.setText(self.__text)

    def setCollapsedText(self, text):
        self.__collapsedTex = text
        self.collapseToolButton.setText(self.__collapsedTex)

    def setLayout(self, layout):

        self.widget.setLayout(layout)

    def setCollapsed(self, state):

        if state:
            self.collapse_state = True
            self.collapseToolButton.setIcon(gf.get_icon('angle-left'))
            self.widget.setHidden(True)
            if self.__collapsedTex:
                self.setCollapsedText(self.__collapsedTex)
        else:
            self.collapse_state = False
            self.collapseToolButton.setIcon(gf.get_icon('angle-right'))
            self.widget.setHidden(False)
            self.setText(self.__text)

    def isCollapsed(self):
        if self.collapse_state:
            return True
        else:
            return False

    def __toggleCollapseState(self):

        if self.collapse_state:
            self.setCollapsed(False)
        else:
            self.setCollapsed(True)


class Ui_namingEditorWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        print('Now you can edit your names :)')


class Ui_serverPresetsEditorWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()

    def create_ui(self):
        self.setWindowTitle('Editing Server Presets')
        self.resize(550, 450)
        self.setSizeGripEnabled(True)

        self.creat_layout()
        self.create_edit()
        self.create_presets_tree_widget()
        self.create_buttons()

        self.fill_presets_tree()

        self.controls_actions()

    def controls_actions(self):

        self.add_new_button.clicked.connect(self.add_new_preset)
        self.remove_button.clicked.connect(self.delete_selected_preset)
        self.save_button.clicked.connect(self.save_and_close)
        self.close_button.clicked.connect(self.close)

    def creat_layout(self):

        self.main_layout = QtGui.QGridLayout()
        self.main_layout.setContentsMargins(9, 9, 9, 9)
        self.main_layout.setColumnStretch(0, 1)
        self.setLayout(self.main_layout)

    def create_presets_tree_widget(self):

        self.presets_tree_widget = QtGui.QTreeWidget()
        self.presets_tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.presets_tree_widget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.presets_tree_widget.setRootIsDecorated(False)
        self.presets_tree_widget.setHeaderHidden(True)
        self.presets_tree_widget.setObjectName('presets_tree_widget')

        self.main_layout.addWidget(self.presets_tree_widget, 1, 0, 2, 1)

    def save_and_close(self):
        env_server.save_server_presets_defaults()

        env_inst.ui_conf.serverPageWidget.readSettings()

        self.close()

    def fill_presets_tree(self):

        presets = env_server.get_server_presets()
        if presets:
            for preset in presets['presets_list']:
                root_item = QtGui.QTreeWidgetItem()
                root_item.setText(0, preset)
                self.presets_tree_widget.addTopLevelItem(root_item)

    def create_edit(self):

        self.line_edit = QtGui.QLineEdit()

        self.main_layout.addWidget(self.line_edit, 0, 0, 1, 1)

    def create_buttons(self):

        self.add_new_button = QtGui.QPushButton('Add')
        self.add_new_button.setMinimumWidth(90)
        self.remove_button = QtGui.QPushButton('Remove')
        self.remove_button.setMinimumWidth(90)
        self.save_button = QtGui.QPushButton('Save and Close')
        self.save_button.setMinimumWidth(90)
        self.close_button = QtGui.QPushButton('Cancel')
        self.close_button.setMinimumWidth(90)

        self.main_layout.addWidget(self.add_new_button, 0, 1, 1, 1)
        self.main_layout.addWidget(self.remove_button, 1, 1, 1, 1)
        self.main_layout.addWidget(self.save_button, 3, 0, 1, 1)
        self.main_layout.addWidget(self.close_button, 3, 1, 1, 1)

        spacer = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.main_layout.addItem(spacer, 2, 1, 1, 1)

    def add_new_preset(self):

        new_preset_name = self.line_edit.text()

        exclude_list = ['environment_config']
        presets = env_server.get_server_presets()
        exclude_list.extend(presets['presets_list'])

        if new_preset_name and new_preset_name not in exclude_list:
            self.line_edit.setText('')
            root_item = QtGui.QTreeWidgetItem()
            root_item.setText(0, new_preset_name)

            env_server.add_server_preset(new_preset_name)

            self.presets_tree_widget.addTopLevelItem(root_item)
        elif new_preset_name in exclude_list:
            message_box = QtGui.QMessageBox(
                QtGui.QMessageBox.Information,
                'Already exists',
                '<p>Server Preset named <b>{0}</b> already in Presets List.</p><p>Choose another Name.</p>'.format(new_preset_name),
                QtGui.QMessageBox.StandardButton,
                self,
            )
            message_box.exec_()

    def delete_selected_preset(self):
        for item in self.presets_tree_widget.selectedItems():
            preset_name = item.text(0)
            if preset_name != 'default':
                idx = self.presets_tree_widget.indexFromItem(item).row()
                self.presets_tree_widget.takeTopLevelItem(idx)
                env_server.remove_server_preset(preset_name)

    def closeEvent(self, event):
        event.accept()

        # resetting changes to server presets
        env_server.server_presets = None
        env_server.get_server_presets_defaults()
        env_server.get_server_presets()


class Ui_previewsEditorDialog(QtGui.QDialog):
    def __init__(self, files_objects, screenshots, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.files_objects = files_objects
        self.screenshots = screenshots

        self.create_ui()

    def create_ui(self):

        self.setWindowTitle('Preview Images list')

        self.resize(500, 400)
        self.setMinimumSize(QtCore.QSize(500, 400))

        self.create_widgets()

        self.contorls_actions()

        self.fill_items_tree_widget(self.files_objects)
        self.fill_screenshot_items_tree_widget(self.screenshots)

    def contorls_actions(self):

        pass

    def fill_items_tree_widget(self, items=None):
        if items:
            for file_object in items.get('file'):
                gf.add_preview_item(self.items_tree_widget, file_object=file_object)

    def fill_screenshot_items_tree_widget(self, items=None):
        if items:
            for screenshot in items:
                gf.add_preview_item(self.items_tree_widget, screenshot=screenshot)

    def create_widgets(self):

        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)

        self.items_tree_widget = QtGui.QTreeWidget()
        self.items_tree_widget.setAlternatingRowColors(True)
        self.items_tree_widget.setHeaderHidden(True)
        # self.treeWidget_vls.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.items_tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.items_tree_widget.setRootIsDecorated(False)
        self.items_tree_widget.setStyleSheet('QTreeView::item {padding: 2px;}')

        self.main_layout.addWidget(self.items_tree_widget)


class Ui_screenShotMakerDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.__dragging = True
        self.__drawn = False
        self.__resizing = False
        self.__offset_pos = None

        self.create_ui()

    def create_ui(self):

        self.setWindowTitle('Making Screenshot')

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        # if do not work on linux, try "apt install xcompmgr" and run it, or compiz
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.setGeometry(Qt4Gui.QCursor.pos().x()-12, Qt4Gui.QCursor.pos().y()-12, 24, 24)

        self.label_lay = QtGui.QVBoxLayout()
        self.setLayout(self.label_lay)
        self.screenshot_pixmap = None

        self.label_lay.setContentsMargins(0, 0, 0, 0)
        self.label_lay.setSpacing(0)

        self.bg_wd = QtGui.QLabel()
        self.bg_wd.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.bg_wd.setPixmap(gf.get_icon('crosshairs', color=Qt4Gui.QColor(255, 255, 255)).pixmap(24, 24))
        self.bg_wd.setStyleSheet(
            'QLabel {padding: 0px;border: 0px dashed rgb(255,255,255); background-color: rgba(0,0,0,1);}')
        self.label_lay.addWidget(self.bg_wd)

        self.bg_wd.setMouseTracking(True)

        self.button_lay = QtGui.QHBoxLayout(self.bg_wd)
        self.button_lay.setContentsMargins(0, 0, 0, 0)
        self.button_lay.setSpacing(0)

        self.move_under_mouse_timer = QtCore.QTimer()
        self.move_under_mouse_timer.setInterval(50)
        self.move_under_mouse_timer.timeout.connect(self.move_under_mouse)
        self.move_under_mouse_timer.start()

        self.create_take_screenshot_button()

        self.setIcon()
        self.setMouseTracking(True)

        self.controls_actions()

    def controls_actions(self):
        self.take_screenshot_button.clicked.connect(self.take_screenshot)

    def create_take_screenshot_button(self):
        self.take_screenshot_button = QtGui.QToolButton()
        self.take_screenshot_button.setText('Take Screenshot')
        self.button_lay.addWidget(self.take_screenshot_button)
        self.take_screenshot_button.setHidden(True)

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    def move_under_mouse(self):
        self.move(Qt4Gui.QCursor.pos().x() - 12, Qt4Gui.QCursor.pos().y() - 12)

    def take_screenshot(self):
        self.hide()
        width = self.geometry().width()
        height = self.geometry().height()
        top = self.geometry().top()
        left = self.geometry().left()
        self.screenshot_pixmap = Qt4Gui.QPixmap.grabWindow(
            QtGui.QApplication.desktop().winId(),
            left,
            top,
            width,
            height
        )

    def dragging(self, pos):
        result_pos = pos + self.__offset_pos
        self.move(result_pos)

    def resizing(self, pos):
        result_pos = pos - self.__offset_pos
        self.resize(result_pos.toTuple()[0], result_pos.toTuple()[1])

    def mouseMoveEvent(self, event):

        if self.underMouse() and not self.__resizing:
            if self.__dragging and self.__offset_pos:
                self.dragging(Qt4Gui.QCursor.pos())
        if self.__resizing and self.__offset_pos:
            self.resizing(Qt4Gui.QCursor.pos())
        elif self.__dragging and not self.__drawn:
            self.move(Qt4Gui.QCursor.pos().x() - 12, Qt4Gui.QCursor.pos().y() - 12)

        event.accept()

    def mouseReleaseEvent(self, event):
        self.__resizing = False
        self.__dragging = False
        self.setMinimumSize(128, 128)
        self.setSizeGripEnabled(True)
        self.take_screenshot_button.setHidden(False)
        event.accept()

    def mousePressEvent(self, event):
        widget_pos = self.pos()
        offset_pos = widget_pos - Qt4Gui.QCursor.pos()
        self.__offset_pos = offset_pos

        if self.__drawn:
            self.__resizing = False
            self.__dragging = True
        else:
            self.move(Qt4Gui.QCursor.pos())
            self.resize(24, 24)
            self.__offset_pos = Qt4Gui.QCursor.pos()
            self.__resizing = True
            self.__dragging = False
            self.__drawn = True
            self.bg_wd.setStyleSheet('QLabel {padding: 0px;border: 2px dashed rgb(255,255,255); background-color: rgba(0,0,0,25);}')
            self.bg_wd.setPixmap(None)
            self.move_under_mouse_timer.stop()

        event.accept()


class Ui_debugLogWidget(QtGui.QDialog, ui_debuglog.Ui_DebugLog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.create_ui()

    def create_ui(self):

        self.setSizeGripEnabled(True)

        self.controls_actions()
        # self.debugLogTextEdit.setWordWrapMode(Qt4Gui.QTextOption.NoWrap)

    def controls_actions(self):

        self.debugLogTextEdit.textChanged.connect(self.fill_modules_tree)

    def fill_modules_tree(self):
        if self.isVisible():
            scrollbar = self.debugLogTextEdit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            # self.treeWidget.clear()
            if not self.check_if_items_exists(self.treeWidget, 'FULL LOG'):
                self.full_log_item = QtGui.QTreeWidgetItem()
                self.full_log_item.setText(0, ' -- FULL LOG -- ')
                self.full_log_item.setData(0, 12, 'FULL LOG')
                self.treeWidget.addTopLevelItem(self.full_log_item)

            for debuglog_dict in [dl.info_dict, dl.warning_dict, dl.log_dict]:
                self.add_items_by_debuglog_dict(debuglog_dict)

    def add_items_by_debuglog_dict(self, debuglog_dict):
        for key, val in debuglog_dict.items():
            module_item = QtGui.QTreeWidgetItem()
            # module_item.setText(0, '{1} ({0})'.format(len(val), key))
            module_item.setText(0, '{1} ({0})'.format(len(val), key))
            module_item.setData(0, 12, key)
            module_item.setData(0, QtCore.Qt.UserRole, val)
            exist_item = self.check_if_items_exists(self.treeWidget, key)
            if not exist_item:
                self.treeWidget.addTopLevelItem(module_item)
            else:
                # exist_val = exist_item.data(0, QtCore.Qt.UserRole)
                # extended_val = exist_val + val
                # exist_item.setText(0, '{1} ({0})'.format(len(extended_val), key))
                exist_item.setText(0,  '{1} ({0})'.format(len(val), key))
                exist_item.setData(0, 12, exist_item.data(0, 12))
                exist_item.setData(0, QtCore.Qt.UserRole, val)
                module_item = exist_item

            unique_ids = set()
            for i in val:
                if i[1]['unique_id']:
                    unique_ids.add(i[1]['unique_id'])
            if unique_ids:
                for unique_id in unique_ids:
                    subgroup_list = unique_id.split('/')
                    subgroup_list.reverse()
                    self.recursive_add_items(module_item, subgroup_list)

    @staticmethod
    def check_if_items_exists(root_item, item_text):
        if type(root_item) == QtGui.QTreeWidget:
            for i in range(root_item.topLevelItemCount()):
                top_item = root_item.topLevelItem(i)
                if item_text == top_item.data(0, 12):
                    return top_item
        else:
            for i in range(root_item.childCount()):
                top_item = root_item.child(i)
                if item_text == top_item.data(0, 12):
                    return top_item

    def recursive_add_items(self, root_item, subgroup_list):
        item_text = subgroup_list.pop()
        group_item = QtGui.QTreeWidgetItem()
        if self.check_if_items_exists(root_item, item_text):
            group_item = self.check_if_items_exists(root_item, item_text)
        else:
            root_item.addChild(group_item)
            val = root_item.data(0, QtCore.Qt.UserRole)
            if val:
                group_item.setText(0, '{0} ({1})'.format(item_text, len(val)))
            else:
                group_item.setText(0, item_text)
            group_item.setData(0, 12, item_text)
            group_item.setData(0, QtCore.Qt.UserRole, val)

        if subgroup_list:
            return self.recursive_add_items(group_item, subgroup_list)

    def add_debuglog(self, debuglog_dict, message_type, print_log=False):
        self.debugLogTextEdit.append(self.format_debuglog(debuglog_dict[1], message_type))
        if print_log:
            print(self.format_debuglog(debuglog_dict[1], message_type, False))

    def format_debuglog(self, debuglog_dict, message_type, html=True):

        trace_str = '{0} {1} {2} ----- //{3:04d} : Module: {4}, Function: {5}()'.format(
            datetime.date.strftime(debuglog_dict['datetime'], '[%d.%m.%Y - %H:%M:%S]'),
            message_type,
            debuglog_dict['message_text'],
            int(debuglog_dict['line_number']),
            debuglog_dict['module_path'],
            debuglog_dict['function_name'])

        if html:
            if message_type == '[ INF ]':
                color = '009933'
            elif message_type == '[ WRN ]':
                color = 'ffcc00'
            elif message_type == '[ ERR ]':
                color = 'ff1a1a'
            elif message_type == '[ CRL ]':
                color = '3385ff'
            elif message_type == '[ EXC ]':
                color = 'ff8080'
            else:
                color = 'a5a5a5'
            return '<span style="color:#{0};">{1}</span>'.format(color, trace_str)
        else:
            return trace_str

    def showEvent(self, event):
        event.accept()
        self.fill_modules_tree()


# class SuggestedSearchWidget(QtGui.QWidget):
#
#     def __init__(self, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#
#         self.create_ui()
#
#     def create_ui(self):
#         pass


# class CustomCompleter(QtGui.QCompleter):
#     def __init__(self, *args, **kwargs):
#         super(CustomCompleter, self).__init__(*args, **kwargs)
#         self.setCompletionMode(QtGui.QCompleter.PopupCompletion)
#         self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
#
#     def complete(self):
#         super(CustomCompleter, self).complete()
#         popup = self.popup()
#         if not popup.isVisible():
#             popup.show()


class CompleterLineEdit(QtGui.QLineEdit):
    def __init__(self, *args, **kwargs):
        super(CompleterLineEdit, self).__init__(*args, **kwargs)

        self.completer = QtGui.QCompleter()
        self.completer.setCompletionMode(QtGui.QCompleter.UnfilteredPopupCompletion)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.completer.popup().setStyleSheet("""
        QListView {
            font-size:10pt;
            selection-background-color: #ffaa00;
            selection-color: black;
            background-color: #7A7A7A;
            border-style: solid;
            border: 0px solid #EBEBEB;
            border-radius: 6;
            color: #EBEBEB;
            padding: 0px 0px 0px 0px; }
        """)
        self.setCompleter(self.completer)
        completer_strings = QtCore.QStringListModel([], self)
        self.completer.setModel(completer_strings)

    def update_items_list(self, string_list):
        self.completer.model().setStringList(string_list)

    def clear_items_list(self):
        self.completer.model().setStringList([])
        self.completer.popup().hide()

    # def mousePressEvent(self, event):
    #     super(CompleterLineEdit, self).mousePressEvent(event)
    #     self.completer.complete()

    # def keyPressEvent(self, event):
    #     super(CustomLineEdit, self).keyPressEvent(event)


class SuggestedLineEdit(CompleterLineEdit):

    def __init__(self, stype, project, style='flat', parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.style = style
        self.stype = stype
        self.project = project
        self.return_pressed = False
        self.single_click_select_all = True
        self.display_limit = 50
        self.suggest_column = 'name'

        self.create_ui()

    def create_ui(self):

        self.customize_ui()

        self.controls_actions()

        # limiting available search characters
        self.setValidator(Qt4Gui.QRegExpValidator(QtCore.QRegExp('\w+'), self))
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFrame(False)

    def controls_actions(self):
        # self.returnPressed.connect(self.set_return_pressed)
        self.textEdited.connect(self.search_suggestions)

    def customize_ui(self):

        if self.style == 'flat':
            self.setStyleSheet("""
            QLineEdit {
                border: 0px;
                border-radius: 8px;
                show-decoration-selected: 1;
                padding: 0px 8px;
                background: rgba(255, 255, 255, 48);
                background-position: bottom left;
                background-repeat: fixed;
                selection-background-color: darkgray;
                padding-left: 8px;
            }
                QLineEdit:hover{
                color: white;
            }
            """)
        else:
            self.setStyleSheet("""
            QLineEdit {
                border: 0px;
                border-radius: 8px;
                show-decoration-selected: 1;
                padding: 0px 8px;
                background: rgba(255, 255, 255, 48);
                background-position: bottom left;
                background-image: url(":/ui_check/gliph/search_16.png");
                background-repeat: fixed;
                selection-background-color: darkgray;
                padding-left: 15px;
            }
            QLineEdit:hover{
                color: white;
                background-image: url(":/ui_check/gliph/searchHover_16.png");
            }
            """)

    def set_return_pressed(self):
        self.return_pressed = True

    def set_suggest_column(self, column_name):
        self.suggest_column = column_name

    # def mousePressEvent(self, event):
    #     event.accept()
    #     # if self.single_click_select_all:
    #     #     self.selectAll()

    @gf.catch_error
    def search_suggestions(self, key=None):

        if key:
            code = self.stype.info.get('code')
            project = self.project.info.get('code')
            columns = [self.suggest_column]

            filters = [(self.suggest_column, 'EQI', key)]

            def assets_query_new_agent():
                return tc.server_query(
                    filters=filters,
                    stype=code,
                    columns=columns,
                    project=project,
                    limit=self.display_limit,
                    offset=0,
                )

            server_thread_pool = QtCore.QThreadPool()
            server_thread_pool.setMaxThreadCount(env_tactic.max_threads())
            env_inst.set_thread_pool(server_thread_pool, 'server_query/server_thread_pool')

            search_suggestions_worker = gf.get_thread_worker(
                assets_query_new_agent,
                thread_pool=env_inst.get_thread_pool('server_query/server_thread_pool'),
                result_func=self.search_suggestions_end,
                error_func=gf.error_handle
            )
            search_suggestions_worker.try_start()

    def search_suggestions_end(self, result=None):

        if result:
            suggestions_list = []

            for item in result:
                item_text = item.get(self.suggest_column)
                if item_text:
                    suggestions_list.append(item_text)

            self.update_items_list(suggestions_list)
            self.completer.complete()
        else:
            self.clear_items_list()


class StyledComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()

    def create_ui(self):

        self.customize_ui()

        self.controls_actions()

    def controls_actions(self):
        pass

    def customize_ui(self):
        pass


class StyledTabWidget(QtGui.QTabWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.create_ui()

    def create_ui(self):

        self.customize_ui()

        self.controls_actions()

    def controls_actions(self):
        pass

    def customize_ui(self):
        pass
