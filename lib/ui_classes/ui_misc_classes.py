import datetime
from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtGui as Qt4Gui
from lib.side.Qt import QtCore

import lib.global_functions as gf
from lib.environment import env_inst, env_server, dl
import lib.ui.misc.ui_collapsable as ui_collapsable
import lib.ui.misc.ui_horizontal_collapsable as ui_horizontal_collapsable
import lib.ui.misc.ui_debuglog as ui_debuglog


class Ui_collapsableWidget(QtGui.QWidget, ui_collapsable.Ui_collapsableWidget):
    def __init__(self, text=None, state=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.collapse_state = False
        self.__collapsedTex = ''
        self.__text = ''

        self.setText(text)
        self.setCollapsed(state)
        self.__controlsActions()

    def __controlsActions(self):
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
            self.collapseToolButton.setArrowType(QtCore.Qt.RightArrow)
            self.widget.setHidden(True)
            self.collapseToolButton.setChecked(False)
            if self.__collapsedTex:
                self.setCollapsedText(self.__collapsedTex)
        else:
            self.collapse_state = False
            self.collapseToolButton.setArrowType(QtCore.Qt.DownArrow)
            self.widget.setHidden(False)
            self.collapseToolButton.setChecked(True)
            self.setText(self.__text)

    def __toggleCollapseState(self):
        if self.collapse_state:
            self.setCollapsed(False)
        else:
            self.setCollapsed(True)


class Ui_horizontalCollapsableWidget(QtGui.QWidget, ui_horizontal_collapsable.Ui_horizontalCollapsableWidget):
    def __init__(self, text=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.collapse_state = False
        self.__collapsedTex = ''
        self.__text = ''

        self.setText(text)
        self.__controlsActions()

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
        self.presets_tree_widget.setObjectName("presets_tree_widget")

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


class Ui_screenShotMakerDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.setWindowTitle('Making Screenshot')

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # self.setWindowOpacity(0.5)

        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # self.setSizeGripEnabled(True)

        mouse_pos = Qt4Gui.QCursor.pos()
        self.setGeometry(mouse_pos.x()-16, mouse_pos.y()-16, 32, 32)

        # self.resize(150, 150)
        # self.move()

        self.label_lay = QtGui.QVBoxLayout()
        self.setLayout(self.label_lay)
        self.screenshot_pixmap = None

        self.label_lay.setContentsMargins(0, 0, 0, 0)
        self.label_lay.setSpacing(0)

        self.bg_wd = QtGui.QLabel()
        self.bg_wd.setStyleSheet('QLabel {padding: 0px;border: 2px dashed grey; background-color: rgba(0,0,0,25);}')
        self.label_lay.addWidget(self.bg_wd)
        self.bg_wd.setMouseTracking(True)

        self.button_lay = QtGui.QHBoxLayout(self.bg_wd)
        self.button_lay.setContentsMargins(0, 0, 0, 0)
        self.button_lay.setSpacing(0)

        self.pb = QtGui.QToolButton()
        self.pb.setText('Take Screenshot')
        self.pb.setAutoRaise(True)
        # self.button_lay.addWidget(self.pb)

        self.pb.clicked.connect(self.ru)

        self.__dragging = False
        self.__resizing = False
        self.__offset_pos = None

        self.single_click_timer = QtCore.QTimer()
        self.single_click_timer.setInterval(1000)
        self.single_click_timer.timeout.connect(self.ts)

        self.create_ui()

    def create_ui(self):

        self.setIcon()
        self.setMouseTracking(True)
        self.installEventFilter(self)

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    def ts(self):
        self.single_click_timer.stop()
        width = self.geometry().width()
        height = self.geometry().height()
        top = self.geometry().top()
        left = self.geometry().left()
        self.screenshot_pixmap = Qt4Gui.QPixmap.grabWindow(QtGui.QApplication.desktop().winId(), left, top, width, height)
        self.close()

    def ru(self):
        self.hide()
        self.single_click_timer.start()

    def dragging(self, pos):
        result_pos = pos + self.__offset_pos
        self.move(result_pos)

    def resizing(self, pos):
        result_pos = pos - self.__offset_pos
        self.resize(result_pos.toTuple()[0], result_pos.toTuple()[1])

    def mouseMoveEvent(self, event):
        # print event.globalPos()
        global_pos = event.globalPos()
        self.move(global_pos.x()-16, global_pos.y()-16)

        # if self.underMouse() and not self.__resizing:
        #     if self.__dragging and self.__offset_pos:
        #         self.dragging(event.globalPos())
        # else:
        #     if self.__resizing and self.__offset_pos:
        #         self.resizing(event.globalPos())

        event.accept()

    # def mouseReleaseEvent(self, event):
    #     self.__dragging = False
    #     self.__resizing = False
    #     event.accept()
    #
    # def mousePressEvent(self, event):
    #     widget_pos = self.pos()
    #     offset_pos = widget_pos - event.globalPos()
    #     self.__offset_pos = offset_pos
    #
    #     if self.underMouse():
    #         self.__dragging = True
    #     else:
    #         self.move(event.globalPos())
    #         self.resize(0, 0)
    #         self.__offset_pos = event.globalPos()
    #         self.__resizing = True
    #
    #     event.accept()


class Ui_debugLogWidget(QtGui.QDialog, ui_debuglog.Ui_DebugLog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.create_ui()

    def create_ui(self):

        self.setSizeGripEnabled(True)

        self.controls_actions()
        self.debugLogTextEdit.setWordWrapMode(Qt4Gui.QTextOption.NoWrap)

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

    def add_debuglog(self, debuglog_dict, message_type):
        self.debugLogTextEdit.append(self.format_debuglog(debuglog_dict, message_type))

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
            else:
                color = 'a5a5a5'
            return '<br><span style="color:#{0};">{1}</span></br>'.format(color, trace_str)
        else:
            return trace_str

    def showEvent(self, event):
        event.accept()
        self.fill_modules_tree()
