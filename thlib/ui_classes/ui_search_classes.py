from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_inst, env_tactic, cfg_controls, env_read_config, env_write_config
import thlib.global_functions as gf
import thlib.tactic_classes as tc
import thlib.ui_classes.ui_misc_classes as ui_misc_classes
import thlib.ui.search.ui_search_results_tree as ui_search_results_tree

# reload(ui_search_options)
reload(ui_search_results_tree)


class Ui_processFilterDialog(QtGui.QDialog):
    def __init__(self, parent_ui, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setSizeGripEnabled(True)
        # self.setWindowFlags(QtCore.Qt.ToolTip)
        # self.setWindowFlags(QtCore.Qt.Popup)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.checkin_out_widget = parent_ui
        self.project = project
        self.stype = stype
        self.all_items_dict = {
            'children': [],
            'processes': {},
            'builtins': [],
        }

        title = self.stype.info.get('title')
        if not title:
            title = self.stype.info.get('name')
        elif not title:
            title = self.stype.info.get('code')

        self.setWindowTitle('Pipeline for: {0}'.format(title))

        self.create_tree_widget()
        self.fill_tree_widget()
        self.fit_to_content_tree_widget()
        self.create_buttons()

        self.none = False

        self.controls_actions()
        self.readSettings()

    def get_ignore_dict(self):
        ignore_dict = {
            'children': [],
            'processes': {},
            'builtins': [],
            'show_builtins': False
        }

        build_dict = False

        # get builtins ignore list
        for builtin in self.all_items_dict['builtins']:
            if builtin.checkState(0) == QtCore.Qt.Unchecked:
                build_dict = True
                ignore_dict['builtins'].append(builtin.data(1, 0))

        # get children ignore list
        for child in self.all_items_dict['children']:
            if child.checkState(0) == QtCore.Qt.Unchecked:
                build_dict = True
                ignore_dict['children'].append(child.data(1, 0))

        # get processes ignore list
        for name, processes in self.all_items_dict['processes'].iteritems():
            ignored_process = []
            for process in processes:
                if process.checkState(0) == QtCore.Qt.Unchecked:
                    build_dict = True
                    ignored_process.append(process.data(1, 0))
            ignore_dict['processes'][name] = ignored_process

        if build_dict:
            return ignore_dict
        else:
            return ''

    def set_from_ignore_dict(self, ignore_dict):
        if ignore_dict:
            # return from builtins ignore list
            for builtin in self.all_items_dict['builtins']:
                if builtin.data(1, 0) in ignore_dict['builtins']:
                    builtin.setCheckState(0, QtCore.Qt.Unchecked)

            # get children ignore list
            for child in self.all_items_dict['children']:
                if child.data(1, 0) in ignore_dict['children']:
                    child.setCheckState(0, QtCore.Qt.Unchecked)

            # get processes ignore list
            for name, processes in self.all_items_dict['processes'].iteritems():
                for process in processes:
                    ignore_list = ignore_dict['processes'].get(name)
                    if not ignore_list:
                        ignore_list = []
                    if process.data(1, 0) in ignore_list:
                        process.setCheckState(0, QtCore.Qt.Unchecked)

    def controls_actions(self):

        self.none_button.clicked.connect(lambda: self.switch_items('none'))
        self.all_process_button.clicked.connect(lambda: self.switch_items('process'))
        self.all_with_builtins_button.clicked.connect(lambda: self.switch_items('builtins'))
        self.all_children_button.clicked.connect(lambda: self.switch_items('children'))

        self.save_button.clicked.connect(self.save_and_refresh)
        self.save_close_button.clicked.connect(self.close)

        self.tree_widget.itemChanged.connect(self.check_tree_items)

    def check_tree_items(self, changed_item):
        if len(self.tree_widget.selectedItems()) > 1:
            for item in self.tree_widget.selectedItems():
                item.setCheckState(0, changed_item.checkState(0))

    def switch_items(self, item_type='none'):

        # TODO Remove this, and make it work through ignore dict

        if self.none:
            self.none = False
        else:
            self.none = True

        if item_type == 'none':
            for item in self.child_items + self.process_items + self.builtin_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

        if item_type == 'process':
            for item in self.process_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

        if item_type == 'builtins':
            for item in self.builtin_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

        if item_type == 'children':
            for item in self.child_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

    def create_buttons(self):

        self.none_button = QtGui.QPushButton('None / All')
        self.all_process_button = QtGui.QPushButton('Toggle Process')
        self.all_with_builtins_button = QtGui.QPushButton('Toggle Builtins')
        self.all_children_button = QtGui.QPushButton('Toggle Children')

        self.save_button = QtGui.QPushButton('Save')
        self.save_close_button = QtGui.QPushButton('Save and close')

        self.grid.addWidget(self.none_button, 1, 0, 1, 1)
        self.grid.addWidget(self.all_process_button, 1, 1, 1, 1)
        self.grid.addWidget(self.all_with_builtins_button, 2, 0, 1, 1)
        self.grid.addWidget(self.all_children_button, 2, 1, 1, 1)

        self.grid.addWidget(self.save_button, 3, 0, 1, 1)
        self.grid.addWidget(self.save_close_button, 3, 1, 1, 1)

    def create_tree_widget(self):

        self.grid = QtGui.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.setLayout(self.grid)

        self.tree_widget = QtGui.QTreeWidget(self)
        self.tree_widget.setTabKeyNavigation(True)
        self.tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tree_widget.setAllColumnsShowFocus(True)
        self.tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setObjectName('tree_widget')
        self.tree_widget.setStyleSheet('QTreeView::item {padding: 2px;}')
        # self.tree_widget.setRootIsDecorated(False)

        self.grid.addWidget(self.tree_widget, 0, 0, 1, 2)

    def fill_tree_widget(self):
        self.child_items = []
        self.process_items = []
        self.builtin_items = []

        # Children process
        for child in self.stype.schema.children:
            child_stype = self.project.stypes.get(child['from'])
            if child_stype:
                stype_title = child_stype.info.get('title')
                if not stype_title:
                    stype_title = child_stype.info.get('code')
                top_item = QtGui.QTreeWidgetItem()
                top_item.setText(0, stype_title.capitalize() + ' (child)')
                top_item.setCheckState(0, QtCore.Qt.Checked)
                top_item.setData(1, 0, child_stype.info.get('code'))
                self.tree_widget.addTopLevelItem(top_item)
                self.child_items.append(top_item)
                if child_stype.pipeline:
                    for pipeline in child_stype.pipeline.itervalues():
                        title = pipeline.info.get('name')
                        if not title:
                            title = pipeline.info.get('code')

                        item = QtGui.QTreeWidgetItem()
                        item.setText(0, title.capitalize())
                        item.setData(1, 0, pipeline.info.get('code'))
                        top_item.addChild(item)
                        top_item.setExpanded(True)
                        child_items = []
                        for key, val in pipeline.process.iteritems():
                            child_item = QtGui.QTreeWidgetItem()
                            child_item.setText(0, key.capitalize())
                            child_item.setCheckState(0, QtCore.Qt.Checked)
                            child_item.setData(1, 0, key)
                            item.addChild(child_item)
                            item.setExpanded(True)
                            self.process_items.append(child_item)
                            child_items.append(child_item)

                        self.all_items_dict['processes'][pipeline.info.get('code')] = child_items
                self.all_items_dict['children'].append(top_item)

        # Actual process
        if self.stype.pipeline:

            for pipeline in self.stype.pipeline.itervalues():
                title = pipeline.info.get('name')
                if not title:
                    title = pipeline.info.get('code')

                top_item = QtGui.QTreeWidgetItem()
                top_item.setText(0, title.capitalize())
                top_item.setData(1, 0, pipeline.info.get('code'))
                self.tree_widget.addTopLevelItem(top_item)

                child_items = []
                for key, val in pipeline.process.iteritems():
                    child_item = QtGui.QTreeWidgetItem()
                    child_item.setText(0, key.capitalize())
                    child_item.setCheckState(0, QtCore.Qt.Checked)
                    child_item.setData(1, 0, key)
                    top_item.addChild(child_item)
                    top_item.setExpanded(True)
                    self.process_items.append(child_item)
                    child_items.append(child_item)

                self.all_items_dict['processes'][pipeline.info.get('code')] = child_items

        # Hidden process
        builtin_items = []
        for key in ['publish', 'attachment', 'icon']:
            # print key
            top_item = QtGui.QTreeWidgetItem()
            top_item.setText(0, key.capitalize() + ' (builtin)')
            top_item.setCheckState(0, QtCore.Qt.Checked)
            top_item.setData(1, 0, key)
            self.tree_widget.addTopLevelItem(top_item)
            self.builtin_items.append(top_item)
            builtin_items.append(top_item)

        self.all_items_dict['builtins'] = builtin_items

    def fit_to_content_tree_widget(self):

        items_count = 0
        for item in QtGui.QTreeWidgetItemIterator(self.tree_widget):
            items_count += 1

        row_height = items_count * self.tree_widget.sizeHintForRow(0) + 80
        mouse_pos = Qt4Gui.QCursor.pos()
        self.setGeometry(mouse_pos.x(), mouse_pos.y(), 250, row_height)

    # def leaveEvent(self, event):
    #     print event, 'Leave Event'
    #
    # def focusOutEvent(self, event):
    #
    #     print event, 'Focus Out'

    def readSettings(self):
        tab_name = self.checkin_out_widget.objectName().split('/')
        group_path = 'ui_search/{0}/{1}/{2}/{3}'.format(
            self.checkin_out_widget.relates_to,
            self.project.info['type'],
            self.project.info['code'],
            tab_name[1]
        )

        self.set_from_ignore_dict(
            env_read_config(
                filename='process_ignore_dict',
                unique_id=group_path,
                long_abs_path=True
            )
        )

    def writeSettings(self):
        tab_name = self.checkin_out_widget.objectName().split('/')
        group_path = 'ui_search/{0}/{1}/{2}/{3}'.format(
            self.checkin_out_widget.relates_to,
            self.project.info['type'],
            self.project.info['code'],
            tab_name[1]
        )
        env_write_config(
            self.get_ignore_dict(),
            filename='process_ignore_dict',
            unique_id=group_path,
            long_abs_path=True
        )

    def save_and_refresh(self):
        self.writeSettings()

        search_wdg = self.checkin_out_widget.get_search_widget()
        search_wdg.search_results_widget.refresh_current_results()
        # self.parent_ui.refresh_current_results()

    # def mousePressEvent(self, event):
    #     self.offset = event.pos()
    #
    # def mouseMoveEvent(self, event):
    #     x = event.globalX()
    #     y = event.globalY()
    #     x_w = self.offset.x()
    #     y_w = self.offset.y()
    #     self.move(x - x_w, y - y_w)

    def closeEvent(self, event):
        self.save_and_refresh()
        event.accept()


class Ui_searchWidget(QtGui.QWidget):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.stype = stype
        self.project = project

        self.create_ui()

    def create_ui(self):

        self.searchWidgetGridLayout = QtGui.QGridLayout(self)
        self.searchWidgetGridLayout.setContentsMargins(0, 0, 0, 0)
        self.searchWidgetGridLayout.setSpacing(0)
        self.searchWidgetGridLayout.setObjectName("searchWidgetGridLayout")
        self.expandingLayout = QtGui.QVBoxLayout()
        self.expandingLayout.setSpacing(0)
        self.expandingLayout.setObjectName("expandingLayout")
        self.searchWidgetGridLayout.addLayout(self.expandingLayout, 0, 1, 1, 1)
        self.gearMenuToolButton = QtGui.QToolButton(self)
        self.gearMenuToolButton.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.gearMenuToolButton.setAutoRaise(True)
        self.gearMenuToolButton.setArrowType(QtCore.Qt.NoArrow)
        self.gearMenuToolButton.setObjectName("gearMenuToolButton")
        self.searchWidgetGridLayout.addWidget(self.gearMenuToolButton, 0, 2, 1, 1)
        self.searchFiltersVerticalLayout = QtGui.QVBoxLayout()
        self.searchFiltersVerticalLayout.setSpacing(0)
        self.searchFiltersVerticalLayout.setObjectName("searchFiltersVerticalLayout")
        self.searchWidgetGridLayout.addLayout(self.searchFiltersVerticalLayout, 1, 0, 1, 3)
        self.searchWidgetGridLayout.setColumnStretch(0, 1)

        self.create_search_line_edit()

        self.create_search_results_widget()
        self.create_gear_menu_popup()
        self.create_collapsable_toolbar()

        self.controls_actions()

    def controls_actions(self):
        self.searchLineEdit.returnPressed.connect(self.do_search)

        self.add_new_tab_button.clicked.connect(self.add_tab)
        self.refresh_tab_button.clicked.connect(self.update_current_search_results)
        self.resultsTabWidget.tabCloseRequested.connect(self.close_tab)
        self.resultsTabWidget.currentChanged.connect(self.changed_tab)

    def create_search_line_edit(self):
        self.searchLineEdit = ui_misc_classes.SuggestedLineEdit(self.stype, self.project, 'search')
        self.searchLineEdit.setObjectName("searchLineEdit")
        self.searchLineEdit.setToolTip('Enter Your search query here')
        self.searchWidgetGridLayout.addWidget(self.searchLineEdit, 0, 0, 1, 1)

    def create_search_results_widget(self):

        self.search_results_widget = QtGui.QWidget()

        self.resultsLayout = QtGui.QVBoxLayout()
        self.resultsLayout.setSpacing(0)
        self.resultsLayout.setContentsMargins(0, 0, 0, 0)
        self.search_results_widget.setLayout(self.resultsLayout)

        self.create_results_tab_widget()
        self.resultsLayout.addWidget(self.resultsTabWidget)
        self.create_tool_buttons()

        self.searchWidgetGridLayout.addWidget(self.search_results_widget, 2, 0, 1, 3)
        self.searchWidgetGridLayout.setRowStretch(2, 1)
        # print self.searchWidgetGridLayout.rowStretch()

    def create_results_tab_widget(self):
        self.resultsTabWidget = QtGui.QTabWidget()
        self.resultsTabWidget.setMovable(True)
        self.resultsTabWidget.setTabsClosable(True)
        self.resultsTabWidget.setObjectName("resultsTabWidget")

        self.resultsTabWidget.setStyleSheet(
            '#resultsTabWidget > QTabBar::tab {background: transparent;border: 2px solid transparent;'
            'border-top-left-radius: 3px;border-top-right-radius: 3px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;padding: 4px;}'
            '#resultsTabWidget > QTabBar::tab:selected, #resultsTabWidget > QTabBar::tab:hover {'
            'background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(255, 255, 255, 48), stop: 1 rgba(255, 255, 255, 32));}'
            '#resultsTabWidget > QTabBar::tab:selected {border-color: transparent;}'
            '#resultsTabWidget > QTabBar::tab:!selected {margin-top: 0px;}')

    def create_tool_buttons(self):
        self.add_new_tab_button = QtGui.QToolButton()
        self.add_new_tab_button.setAutoRaise(True)
        self.add_new_tab_button.setMinimumWidth(20)
        self.add_new_tab_button.setMinimumHeight(20)
        self.add_new_tab_button.setIcon(gf.get_icon('plus', icons_set='mdi', scale_factor=1.3))
        self.add_new_tab_button.setToolTip('Add new Search Tab')

        self.history_tab_button = QtGui.QToolButton()
        self.history_tab_button.setAutoRaise(True)
        self.history_tab_button.setMinimumWidth(20)
        self.history_tab_button.setMinimumHeight(20)
        self.history_tab_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.history_tab_button.setIcon(gf.get_icon('history', icons_set='mdi', scale_factor=1.3))
        self.history_tab_button.setToolTip('History of closed Search Results')

        self.refresh_tab_button = QtGui.QToolButton()
        self.refresh_tab_button.setAutoRaise(True)
        self.refresh_tab_button.setMinimumWidth(20)
        self.refresh_tab_button.setMinimumHeight(20)
        self.refresh_tab_button.setIcon(gf.get_icon('refresh', icons_set='mdi', scale_factor=1.3))
        self.refresh_tab_button.setToolTip('Refresh current Results')

        self.right_buttons_layout = QtGui.QHBoxLayout()
        self.right_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.right_buttons_layout.setSpacing(2)

        # self.l = QtGui.QHBoxLayout()
        # self.l.setSpacing(0)
        # self.l.setContentsMargins(0, 0, 0, 0)
        #
        # spacer = QtGui.QSpacerItem(500, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        # self.l.addItem(spacer)
        #
        # self.b = QtGui.QPushButton('asd')
        # self.b.setMaximumWidth(20)
        # self.b.setMaximumHeight(20)
        # self.b.setStyleSheet('QPushButton {margin-right: 5px;padding: 6px;}')
        # self.l.addWidget(self.b)

        # self.resultsTabWidget.tabBar().setTabButton(1, QtGui.QTabBar.RightSide, self.b)
        # QtGui.QTabBar.styleSheet()


        # self.resultsTabWidget.tabBar().setLayout(self.l)

        self.right_buttons_widget = QtGui.QWidget(self)
        self.right_buttons_widget.setLayout(self.right_buttons_layout)

        self.sobject_items_sorting_button = QtGui.QToolButton()
        self.sobject_items_sorting_button.setAutoRaise(True)
        self.sobject_items_sorting_button.setMinimumWidth(20)
        self.sobject_items_sorting_button.setMinimumHeight(20)
        self.sobject_items_sorting_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.sobject_items_sorting_button.setIcon(gf.get_icon('sort-variant', icons_set='mdi', scale_factor=1.3))
        self.sobject_items_sorting_button.setToolTip('SObject Items Sorting')

        self.sort_so_by_name_action = QtGui.QAction('Sort by Name', self.sobject_items_sorting_button, checkable=True)
        self.sort_so_by_name_action.setIcon(gf.get_icon('sort-alphabetical', icons_set='mdi', scale_factor=1.3))
        self.sort_so_by_name_action.triggered.connect(lambda: self.change_items_sorting('sobject', 'name'))
        self.sort_so_by_name_action.setChecked(True)

        self.sobject_items_sorting_button.addAction(self.sort_so_by_name_action)

        self.snapshot_items_sorting_button = QtGui.QToolButton()
        self.snapshot_items_sorting_button.setAutoRaise(True)
        self.snapshot_items_sorting_button.setMinimumWidth(20)
        self.snapshot_items_sorting_button.setMinimumHeight(20)
        self.snapshot_items_sorting_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.snapshot_items_sorting_button.setIcon(gf.get_icon('sort-variant', icons_set='mdi', scale_factor=1.3))
        self.snapshot_items_sorting_button.setToolTip('Snapshot Items Sorting')

        self.sort_sn_by_name_action = QtGui.QAction('Sort by Name', self.snapshot_items_sorting_button, checkable=True)
        self.sort_sn_by_name_action.setIcon(gf.get_icon('sort-alphabetical', icons_set='mdi', scale_factor=1.3))
        self.sort_sn_by_name_action.triggered.connect(lambda: self.change_items_sorting('snapshot', 'name'))
        self.sort_sn_by_name_action.setChecked(True)

        self.snapshot_items_sorting_button.addAction(self.sort_sn_by_name_action)

        self.change_view_tab_button = QtGui.QToolButton()
        self.change_view_tab_button.setAutoRaise(True)
        self.change_view_tab_button.setMinimumWidth(20)
        self.change_view_tab_button.setMinimumHeight(20)
        self.change_view_tab_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.change_view_tab_button.setIcon(gf.get_icon('view-list', icons_set='mdi', scale_factor=1.3))
        self.change_view_tab_button.setToolTip('Change Search Results View Style')

        self.items_view_action = QtGui.QMenu('Items View', self.change_view_tab_button)
        self.items_view_action.setIcon(gf.get_icon('view-list', icons_set='mdi', scale_factor=1.3))
        # self.items_view_action.triggered.connect(self.clear_tabs_history)

        self.split_view_horizontal_action = QtGui.QAction('Splitted Horizontal View', self.change_view_tab_button, checkable=True)
        self.split_view_horizontal_action.setIcon(gf.get_icon('view-sequential', icons_set='mdi', scale_factor=1.3))
        self.split_view_horizontal_action.triggered.connect(lambda: self.toggle_current_view('splitted_horizontal'))

        self.split_view_vertical_action = QtGui.QAction('Splitted Vertical View', self.change_view_tab_button, checkable=True)
        self.split_view_vertical_action.setIcon(gf.get_icon('view-parallel', icons_set='mdi', scale_factor=1.3))
        self.split_view_vertical_action.triggered.connect(lambda: self.toggle_current_view('splitted_vertical'))
        self.split_view_vertical_action.setChecked(True)

        self.continious_view_action = QtGui.QAction('Continious View', self.change_view_tab_button, checkable=True)
        self.continious_view_action.setIcon(gf.get_icon('view-dashboard-variant', icons_set='mdi', scale_factor=1.3))
        self.continious_view_action.triggered.connect(lambda: self.toggle_current_view('continious'))

        self.items_view_action.addAction(self.split_view_horizontal_action)
        self.items_view_action.addAction(self.split_view_vertical_action)
        self.items_view_action.addAction(self.continious_view_action)
        # print self.get_current_results_widget()

        self.tiles_view_action = QtGui.QAction('Tiles View', self.change_view_tab_button, checkable=True)
        self.tiles_view_action.setIcon(gf.get_icon('view-grid', icons_set='mdi', scale_factor=1.3))
        self.tiles_view_action.triggered.connect(lambda: self.toggle_current_view('tiles'))

        self.change_view_tab_button.addAction(self.items_view_action.menuAction())
        self.change_view_tab_button.addAction(self.tiles_view_action)

        self.additional_collapsable_toolbar = ui_misc_classes.Ui_horizontalCollapsableWidget()
        self.additional_buttons_layout = QtGui.QHBoxLayout()
        self.additional_buttons_layout.setSpacing(0)
        self.additional_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.additional_collapsable_toolbar.setLayout(self.additional_buttons_layout)
        self.additional_collapsable_toolbar.setCollapsed(True)

        self.additional_buttons_layout.addWidget(self.sobject_items_sorting_button)
        self.additional_buttons_layout.addWidget(self.snapshot_items_sorting_button)
        self.additional_buttons_layout.addWidget(self.change_view_tab_button)

        self.main_collapsable_toolbar = ui_misc_classes.Ui_horizontalCollapsableWidget()
        self.main_buttons_layout = QtGui.QHBoxLayout()
        self.main_buttons_layout.setSpacing(0)
        self.main_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.main_collapsable_toolbar.setLayout(self.main_buttons_layout)
        self.main_collapsable_toolbar.setCollapsed(False)

        self.main_buttons_layout.addWidget(self.refresh_tab_button)
        self.main_buttons_layout.addWidget(self.history_tab_button)

        # self.expandingLayout.addWidget(self.collapsable_toolbar)

        self.right_buttons_layout.addWidget(self.additional_collapsable_toolbar)
        self.right_buttons_layout.addWidget(self.main_collapsable_toolbar)

        # self.right_buttons_layout.addWidget(self.refresh_tab_button)
        # self.right_buttons_layout.addWidget(self.history_tab_button)

        # effect = QtGui.QGraphicsColorizeEffect(self.refresh_tab_button)
        # self.animation = QtCore.QPropertyAnimation(effect, "color", self)
        # self.animation.setDuration(500)
        # self.animation.setStartValue(Qt4Gui.QColor(0, 0, 0, 0))
        # self.animation.setEndValue(Qt4Gui.QColor(49, 140, 72, 128))
        # self.animation.start()
        # self.refresh_tab_button.setGraphicsEffect(effect)

        self.resultsTabWidget.setCornerWidget(self.right_buttons_widget, QtCore.Qt.TopRightCorner)
        self.resultsTabWidget.setCornerWidget(self.add_new_tab_button, QtCore.Qt.TopLeftCorner)

    def change_items_sorting(self, items_type='sobject', sort='name'):
        print('MAKING SORT BY ', items_type, sort)

    def toggle_current_view(self, view='splitted_vertical'):

        current_results_widget = self.get_current_results_widget()
        current_results_widget.toggle_results_view(view)

    @gf.catch_error
    def add_tab(self, search_title='', filters=[], state=None, offset=0, limit=None, reverting=False):

        if not limit:
            limit = self.get_display_limit()

        info = {
            'title': search_title,
            'filters': filters,
            'state': state,
            'offset': offset,
            'limit': limit,
        }

        search_results_widget = Ui_resultsFormWidget(
            project=self.project,
            stype=self.stype,
            info=info,
            parent=self.resultsTabWidget
        )
        # self.sep_versions = search_results_tree.get_is_separate_versions()
        self.resultsTabWidget.addTab(search_results_widget, search_title)

        if not reverting:
            self.resultsTabWidget.setCurrentWidget(search_results_widget)

    def set_current_tab_title(self, title):
        idx = self.resultsTabWidget.currentIndex()
        self.resultsTabWidget.setTabText(idx, title)

    def get_current_tab_title(self):
        idx = self.resultsTabWidget.currentIndex()
        return self.resultsTabWidget.tabText(idx)

    def get_display_limit(self):

        return 10

    def get_results_tab_widget(self):
        return self.resultsTabWidget

    def add_to_history_list(self, tab_title, widget):
        if tab_title:
            filter_process = QtGui.QAction(tab_title, self.history_tab_button)
            filter_process.triggered.connect(lambda: self.restore_tab_from_history(filter_process, widget))
            filter_process.setData(widget)

            try:
                if self.clear_history:
                    pass
            except:
                self.clear_history = QtGui.QAction('Clear History', self.history_tab_button)
                self.clear_history.triggered.connect(self.clear_tabs_history)
                self.history_tab_button.addAction(self.clear_history)
                self.sep = QtGui.QAction('', self.history_tab_button)
                self.sep.setSeparator(True)
                self.history_tab_button.addAction(self.sep)

            self.history_tab_button.addAction(filter_process)

    def clear_tabs_history(self):
        for action in self.history_tab_button.actions():
            results_wdg = action.data()
            if results_wdg:
                results_wdg.clear_tree_widgets()
                results_wdg.close()
                results_wdg.deleteLater()
            self.history_tab_button.removeAction(action)

        del self.clear_history

    def restore_tab_from_history(self, action, widget):

        self.resultsTabWidget.addTab(widget, action.text())
        self.resultsTabWidget.setCurrentWidget(widget)
        self.history_tab_button.removeAction(action)

    @gf.catch_error
    def close_tab(self, tab_index):
        if self.resultsTabWidget.count() > 1:
            self.add_to_history_list(self.resultsTabWidget.tabText(tab_index), self.resultsTabWidget.widget(tab_index))
            self.resultsTabWidget.removeTab(tab_index)

    def changed_tab(self, idx):

        search_results_widget = self.resultsTabWidget.widget(idx)
        checkin_out_widget = self.get_current_checkin_out_widget()
        adv_search_widget = checkin_out_widget.get_advanced_search_widget()
        adv_search_widget.clear_all_filters()

        filters = search_results_widget.get_filters()
        if filters:
            adv_search_widget.set_filters(filters)
        else:
            adv_search_widget.add_default_filter(('name', 'EQI', ''))

    def get_current_checkin_out_widget(self):
        return env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

    # def get_search_results_widget(self):
    #     return self.search_results_widget
    #
    # def get_progress_bar(self):
    #     return self.search_results_widget.get_progress_bar()
    #
    # def get_search_query_text(self):
    #     return self.searchLineEdit.text()
    #
    # def get_process_ignore_list(self):
    #     return self.checkin_out_widget.get_process_ignore_list()
    #
    # def get_current_tree_widget(self):
    #     return self.search_results_widget.get_current_widget()
    #
    # def get_fast_controls_widget(self):
    #     return self.checkin_out_widget.get_fast_controls_widget()
    #
    # def get_snapshot_browser(self):
    #     return self.checkin_out_widget.snapshot_browser_widget
    #
    # def get_description_widget(self):
    #     return self.checkin_out_widget.description_widget
    #
    # def get_drop_plate_widget(self):
    #     return self.checkin_out_widget.drop_plate_widget
    #
    # def get_search_options_widget(self):
    #     return self.checkin_out_widget.search_options_widget
    #
    def get_current_results_widget(self):
        return self.resultsTabWidget.currentWidget()

    # @gf.catch_error
    # def open_items_context_menu(self, *args):
    #     return self.checkin_out_widget.open_menu()

    @gf.catch_error
    def do_search(self, search_query=None):

        results_widget = self.get_current_results_widget()
        if search_query:
            results_widget.update_default_filter(search_query)
        else:
            search_query = self.searchLineEdit.text()
            results_widget.update_default_filter(search_query)

        results_widget.set_offset(0)

        # checkin_out_widget = self.get_current_checkin_out_widget()
        # adv_search_widget = checkin_out_widget.get_advanced_search_widget()

        results_widget.update_filters(True)
        results_widget.update_search_results()

        self.set_current_tab_title(search_query)

    @gf.catch_error
    def update_current_search_results(self):
        results_widget = self.get_current_results_widget()

        # collecting current advanced search options
        results_widget.update_filters(True)
        results_widget.update_search_results(refresh=True, offset=results_widget.collect_offset())

    def create_gear_menu_popup(self):
        self.gearMenuToolButton.setIcon(gf.get_icon('cog'))
        self.gearMenuToolButton.setMinimumSize(22, 22)

    def add_action_to_gear_menu(self, action):
        self.gearMenuToolButton.addAction(action)

    def create_collapsable_toolbar(self):
        self.collapsable_toolbar = ui_misc_classes.Ui_horizontalCollapsableWidget()

        self.buttons_layout = QtGui.QHBoxLayout()
        self.buttons_layout.setSpacing(0)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.collapsable_toolbar.setLayout(self.buttons_layout)
        self.collapsable_toolbar.setCollapsed(True)

        self.expandingLayout.addWidget(self.collapsable_toolbar)

    def add_widget_to_collapsable_toolbar(self, widget):
        self.buttons_layout.addWidget(widget)

    def set_search_cache(self, search_cache, current_index=0):
        search_cache = gf.hex_to_html(search_cache)

        # work around for preventing tab widgets showing when tab adding
        self.resultsTabWidget.setHidden(True)

        if search_cache:
            search_cache = gf.from_json(search_cache, use_ast=True)

            tab_added = 0
            for cache in search_cache:
                tab_added += 1
                self.add_tab(
                    search_title=cache['title'],
                    filters=cache['filters'],
                    state=cache['state'],
                    offset=cache['offset'],
                    limit=cache['limit'],
                    reverting=True
                )

            if not tab_added:
                self.add_tab()

            if current_index:
                self.resultsTabWidget.setCurrentIndex(current_index)
        else:
            self.add_tab()

        self.resultsTabWidget.setHidden(False)

    def get_search_cache(self):

        tab_info_list = []

        for tab in range(self.resultsTabWidget.count()):
            results_form_widget = self.resultsTabWidget.widget(tab)

            tab_info_list.append(results_form_widget.get_info_dict())

        return gf.html_to_hex(gf.to_json(tab_info_list, use_ast=True))

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'collapsable_toolbar': True,
                'searchLineEdit_text': '',
                'search_cache': None,
                'resultsTabWidget_current_index': 0,
            }

        self.collapsable_toolbar.setCollapsed(settings_dict['collapsable_toolbar'])
        self.searchLineEdit.setText(settings_dict['searchLineEdit_text'])
        self.set_search_cache(settings_dict.get('search_cache'), settings_dict.get('resultsTabWidget_current_index'))

    def get_settings_dict(self):

        settings_dict = {
            'collapsable_toolbar': int(self.collapsable_toolbar.isCollapsed()),
            'searchLineEdit_text': unicode(self.searchLineEdit.text()),
            'search_cache': self.get_search_cache(),
            'resultsTabWidget_current_index': self.resultsTabWidget.currentIndex(),
        }

        return settings_dict

    def closeEvent(self, event):

        event.accept()
        self.search_results_widget.close()


class Ui_filterWidget(QtGui.QWidget):
    def __init__(self, stype, project, filter, default, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project

        self.default = default
        self.filter = filter

        self.create_ui()

    def create_ui(self):
        self.create_main_layout()

        self.create_enabled_check_box()
        self.create_column_combo_box()
        self.create_match_by_combo_box()
        self.create_query_line_edit()
        self.create_remove_self_tool_button()
        self.create_add_filter_tool_button()

        self.fill_column_combo_box()
        self.fill_match_by_combo_box()

        self.init_filter()

        self.controls_actions()

    def controls_actions(self):
        self.remove_self_tool_button.clicked.connect(self.close_self)
        self.add_filter_tool_button.clicked.connect(self.add_filter_widget)
        self.enabled_check_box.stateChanged.connect(self.change_enable_state)

        self.column_combo_box.currentIndexChanged.connect(self.changed_column_combo_box_index)
        self.match_combo_box.currentIndexChanged.connect(self.changed_match_by_combo_box_index)
        self.query_line_edit.textChanged.connect(self.changed_line_edit_text)
        self.query_line_edit.returnPressed.connect(self.edited_line_edit_text)

    def get_checkin_out_widget(self):
        return env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

    def get_search_widget(self):
        checkin_out_widget = self.get_checkin_out_widget()
        return checkin_out_widget.get_search_widget()

    def get_advanced_search_widget(self):
        checkin_out_widget = self.get_checkin_out_widget()
        return checkin_out_widget.get_advanced_search_widget()

    def create_main_layout(self):
        self.main_layout = QtGui.QHBoxLayout()
        self.main_layout.setSpacing(9)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def create_enabled_check_box(self):
        self.enabled_check_box = QtGui.QCheckBox()
        self.main_layout.addWidget(self.enabled_check_box)
        self.enabled_check_box.setChecked(True)

    def create_column_combo_box(self):
        self.column_combo_box = QtGui.QComboBox()
        self.main_layout.addWidget(self.column_combo_box)

    def changed_column_combo_box_index(self, idx):
        column = self.column_combo_box.itemData(idx, QtCore.Qt.UserRole)
        self.filter = (column, self.filter[1], self.filter[2])

        self.query_line_edit.set_suggest_column(column)

    def create_match_by_combo_box(self):
        self.match_combo_box = QtGui.QComboBox()
        self.main_layout.addWidget(self.match_combo_box)

    def valid_filter(self):
        query_tex = self.query_line_edit.text()
        if query_tex.strip() and self.enabled_check_box.isChecked():
            return True

    def fill_column_combo_box(self):
        for i, (column, values) in enumerate(self.stype.get_columns_info().items()):
            self.column_combo_box.addItem(gf.prettify_text(column))
            self.column_combo_box.setItemData(i, column, QtCore.Qt.UserRole)

    def fill_match_by_combo_box(self):

        match_list = [
            ('is', '='),
            ('is not', '!='),
            ('contains', 'EQI'),
            ('does not contain', 'NEQI'),
            ('is empty', 'like'),
            ('is not empty', 'like'),
            ('starts with', ''),
            ('ends with', ''),
            ('does not starts with', ''),
            ('does not end with', ''),
            ('in', 'in'),
            ('not in', 'not in'),
            ('is distinct', ''),
        ]

        for i, match in enumerate(match_list):
            self.match_combo_box.addItem(match[0])
            self.match_combo_box.setItemData(i, match[1], QtCore.Qt.UserRole)

    def changed_match_by_combo_box_index(self, idx):
        match = self.match_combo_box.itemData(idx, QtCore.Qt.UserRole)
        self.filter = (self.filter[0], match, self.filter[2])

    def create_query_line_edit(self):
        self.query_line_edit = ui_misc_classes.SuggestedLineEdit(self.stype, self.project, 'flat')
        self.main_layout.addWidget(self.query_line_edit)

    def changed_line_edit_text(self):
        text = self.query_line_edit.text()
        self.filter = (self.filter[0], self.filter[1], text)

    def edited_line_edit_text(self):
        search_widget = self.get_search_widget()
        # search_widget.do_search()
        search_widget.update_current_search_results()
        # results_widget.update_filters(True)
        # results_widget.update_search_results()

    def create_remove_self_tool_button(self):
        self.remove_self_tool_button = QtGui.QToolButton()
        self.main_layout.addWidget(self.remove_self_tool_button)
        self.remove_self_tool_button.setIcon(gf.get_icon('close'))
        if self.default:
            self.remove_self_tool_button.setHidden(True)

    def create_add_filter_tool_button(self):
        self.add_filter_tool_button = QtGui.QToolButton()
        self.main_layout.addWidget(self.add_filter_tool_button)
        self.add_filter_tool_button.setIcon(gf.get_icon('plus'))
        if not self.default:
            self.add_filter_tool_button.setHidden(True)

    def get_filter(self):
        return self.filter

    def set_filter(self, fltr):
        self.filter = fltr

    def init_filter(self):

        if self.filter:
            self.set_column_combo_box_value(self.filter[0])
            self.set_match_combo_box_value(self.filter[1])
            self.set_query_line_edit_value(self.filter[2])
        else:
            self.filter = (
                self.column_combo_box.itemData(0, QtCore.Qt.UserRole),
                self.match_combo_box.itemData(0, QtCore.Qt.UserRole),
                ''
            )

    def set_column_combo_box_value(self, column_code):
        index = self.column_combo_box.findData(column_code, QtCore.Qt.UserRole)
        self.column_combo_box.setCurrentIndex(index)

        self.query_line_edit.set_suggest_column(column_code)

    def set_match_combo_box_value(self, match):
        index = self.match_combo_box.findData(match, QtCore.Qt.UserRole)
        self.match_combo_box.setCurrentIndex(index)

    def set_query_line_edit_value(self, query_text):
        self.query_line_edit.setText(query_text)

    def change_enable_state(self, state):
        if bool(state):
            self.column_combo_box.setEnabled(True)
            self.match_combo_box.setEnabled(True)
            self.query_line_edit.setEnabled(True)
        else:
            self.column_combo_box.setEnabled(False)
            self.match_combo_box.setEnabled(False)
            self.query_line_edit.setEnabled(False)

    def add_filter_widget(self):
        adv_search_widget = self.get_advanced_search_widget()
        adv_search_widget.add_empty_filter()

    def close_self(self):
        adv_search_widget = self.get_advanced_search_widget()
        adv_search_widget.remove_filter(self)

    def closeEvent(self, event):
        event.accept()
        self.deleteLater()


class Ui_advancedSearchWidget(QtGui.QWidget):
    def __init__(self, stype, project, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project

        self.default_filter_widget = None
        self.filter_widgets = []

        self.create_ui()

    def create_ui(self):
        self.create_main_layout()
        self.create_scroll_area()
        self.create_search_filters_widget()
        # self.create_spacer()

        self.add_default_filter(('name', 'EQI', ''))

        self.controls_actions()

    def controls_actions(self):
        pass

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def create_scroll_area(self):
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area_contents = QtGui.QWidget()
        self.scroll_area.setStyleSheet('QScrollArea > #qt_scrollarea_viewport > QWidget {background-color: rgba(128, 128, 128, 48);}')
        self.scroll_area.setFrameShape(QtGui.QScrollArea.NoFrame)
        # self.scroll_area.setMinimumHeight(48)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_contents)

        # self.main_layout.addWidget(self.scroll_area)
        self.scroll_widgets_layout = QtGui.QVBoxLayout()
        self.scroll_widgets_layout.setSpacing(4)
        self.scroll_widgets_layout.setContentsMargins(2, 2, 2, 2)
        self.scroll_area_contents.setLayout(self.scroll_widgets_layout)

    def create_search_filters_widget(self):

        self.filters_collapsable = ui_misc_classes.Ui_collapsableWidget(state=False)
        layout_filters = QtGui.QVBoxLayout()
        self.filters_collapsable.setLayout(layout_filters)
        self.filters_collapsable.setText('Search Filters:')
        self.filters_collapsable.setCollapsedText('Search Filters:')
        layout_filters.addWidget(self.scroll_area)

        self.main_layout.addWidget(self.filters_collapsable)
        self.filters_collapsable.collapsed.connect(self.collapable_widget_collapsed)

    def collapable_widget_collapsed(self, collapsed):
        if collapsed:
            self.setMaximumHeight(25)
            self.setMinimumHeight(25)
        else:
            self.fit_to_contets()

    def add_filters(self, filters):
        for filter_text in filters:
            self.add_predefined_filter(filter_text)

    def update_default_filter(self, filter_text):
        self.default_filter_widget.set_filter(filter_text)
        self.default_filter_widget.init_filter()

    def add_default_filter(self, filter_text):
        filter_widget = Ui_filterWidget(
            project=self.project,
            stype=self.stype,
            parent=self,
            filter=filter_text,
            default=True
        )
        self.scroll_widgets_layout.addWidget(filter_widget)
        self.filter_widgets.append(filter_widget)
        self.default_filter_widget = filter_widget

        self.fit_to_contets()

    def add_predefined_filter(self, filter_text):
        filter_widget = Ui_filterWidget(
            project=self.project,
            stype=self.stype,
            parent=self,
            filter=filter_text,
            default=False
        )
        self.scroll_widgets_layout.addWidget(filter_widget)
        self.filter_widgets.append(filter_widget)

        self.fit_to_contets()

    def add_empty_filter(self):
        filter_widget = Ui_filterWidget(
            project=self.project,
            stype=self.stype,
            parent=self,
            filter=None,
            default=False
        )
        self.scroll_widgets_layout.addWidget(filter_widget)
        self.filter_widgets.append(filter_widget)

        self.fit_to_contets()

    def remove_filter(self, filter_widget):
        filter_widget.close()
        self.filter_widgets.remove(filter_widget)

        self.fit_to_contets()

    def create_spacer(self):
        self.main_layout.addItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 1, 0, 1, 1)
        self.main_layout.setRowStretch(0, 1)

    def clear_all_filters(self):
        if self.default_filter_widget:
            self.default_filter_widget.close()
            self.default_filter_widget = None

        for filter_widget in self.filter_widgets:
            filter_widget.close()
        self.filter_widgets = []

        self.fit_to_contets()

    def get_filters(self, check_valid=False):
        filters = []
        for filter_widget in self.filter_widgets:
            if check_valid:
                if filter_widget.valid_filter():
                    filters.append(filter_widget.get_filter())
            else:
                filters.append(filter_widget.get_filter())

        return filters

    def get_default_filter(self):
        return self.default_filter_widget.get_filter()

    def set_filters(self, filters):
        if filters:
            self.add_default_filter(filters[0])

            for fltr in filters[1:]:
                self.add_predefined_filter(fltr)

    def fit_to_contets(self):
        contents_height = 30
        for filter_widget in self.filter_widgets:
            contents_height += 30

        if contents_height < 330 and not self.filters_collapsable.collapse_state:
            self.setMaximumHeight(contents_height)
            self.setMinimumHeight(contents_height)

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'filters_collapsable_state': False,
                'visible': False
            }

        self.setVisible(settings_dict.get('visible'))
        if settings_dict.get('filters_collapsable_state'):
            self.filters_collapsable.setCollapseState(True)

    def get_settings_dict(self):

        settings_dict = {
            'filters_collapsable_state': self.filters_collapsable.isCollapsed(),
            'visible': self.isVisible()
        }

        return settings_dict


# DEPRECATED
# class Ui_searchOptionsWidget(QtGui.QGroupBox, ui_search_options.Ui_searchOptionsGroupBox):
#     def __init__(self, parent_ui, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#
#         self.setupUi(self)
#         self.parent_ui = parent_ui
#
#         self.project = self.parent_ui.project
#         self.current_project = self.project.info['code']
#         self.current_namespace = self.project.info['type']
#
#         self.tab_name = self.parent_ui.objectName()
#         self.tab_related_to = self.parent_ui.relates_to
#
#         self.controls_actions()
#
#     def controls_actions(self):
#
#         self.saveAsDefaultsPushButton.clicked.connect(self.apply_current_to_all_tabs)
#
#     def apply_current_to_all_tabs(self):
#         current_settings = self.get_settings_dict()
#         for tab in env_inst.check_tree.get(self.parent_ui.relates_to).itervalues():
#             tab.searchOptionsGroupBox.set_settings_from_dict(current_settings)
#
#     def get_custom_process_list(self):
#         return ['AZZA']
#
#     def set_search_by(self, search_by):
#
#         if search_by == 0:
#             self.searchNameRadioButton.setChecked(True)
#         elif search_by == 1:
#             self.searchCodeRadioButton.setChecked(True)
#         elif search_by == 2:
#             self.searchDescriptionRadioButton.setChecked(True)
#         elif search_by == 3:
#             self.searchKeywordsRadioButton.setChecked(True)
#         elif search_by == 4:
#             self.searchParentCodeRadioButton.setChecked(True)
#
#     def get_search_by(self):
#
#         if self.searchNameRadioButton.isChecked():
#             return 0
#         elif self.searchCodeRadioButton.isChecked():
#             return 1
#         elif self.searchDescriptionRadioButton.isChecked():
#             return 2
#         elif self.searchKeywordsRadioButton.isChecked():
#             return 3
#         elif self.searchParentCodeRadioButton.isChecked():
#             return 4
#
#     def set_sort_by(self, sort_by):
#
#         if sort_by == 0:
#             self.sortNameRadioButton.setChecked(True)
#         elif sort_by == 1:
#             self.sortCodeRadioButton.setChecked(True)
#         elif sort_by == 2:
#             self.sortTimestampRadioButton.setChecked(True)
#         elif sort_by == 3:
#             self.sortNothingRadioButton.setChecked(True)
#
#     def get_sort_by(self):
#
#         if self.sortNameRadioButton.isChecked():
#             return 0
#         elif self.sortCodeRadioButton.isChecked():
#             return 1
#         elif self.sortTimestampRadioButton.isChecked():
#             return 2
#         elif self.sortNothingRadioButton.isChecked():
#             return 3
#
#     def set_search_options(self, options_dict):
#         if options_dict:
#             self.set_search_by(options_dict['search_by'])
#             self.set_sort_by(options_dict['sort_by'])
#
#     def get_search_options(self):
#
#         options_dict = {
#             'search_by': self.get_search_by(),
#             'sort_by': self.get_sort_by()
#         }
#
#         return options_dict
#
#     def set_settings_from_dict(self, settings_dict=None):
#
#         if not settings_dict:
#             settings_dict = {
#                 'search_options': None,
#                 'showAllProcessCheckBox': False,
#                 'displayLimitSpinBox': 10,
#             }
#
#         self.set_search_options(gf.from_json(settings_dict.get('search_options')))
#         self.showAllProcessCheckBox.setChecked(settings_dict['showAllProcessCheckBox'])
#         self.displayLimitSpinBox.setValue(settings_dict['displayLimitSpinBox'])
#
#     def get_settings_dict(self):
#
#         settings_dict = {
#             'search_options': str(self.get_search_options()),
#             'showAllProcessCheckBox': int(self.showAllProcessCheckBox.isChecked()),
#             'displayLimitSpinBox': int(self.displayLimitSpinBox.value()),
#         }
#
#         return settings_dict

class Ui_navigationWidget(QtGui.QWidget):
    refresh_search = QtCore.Signal(object, object)

    def __init__(self, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.stype = stype

        self.display_limit = 0
        self.display_offset = 0
        self.total_count = 0
        self.total_query_count = 0
        self.current_page = 1
        self.last_page = 0

        self.create_ui()

    def create_ui(self):

        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.create_main_layout()

        self.create_button_controls()
        self.create_navigation_label()

        self.controls_actions()

    def controls_actions(self):

        self.back_button.enterEvent = self.back_button_enter_event
        self.back_button.leaveEvent = self.back_button_leave_event
        self.forward_button.enterEvent = self.forward_button_enter_event
        self.forward_button.leaveEvent = self.forward_button_leave_event

        self.navigation_label.linkActivated.connect(self.navigation_label_link_clicked)
        self.forward_button.clicked.connect(self.next_page)
        self.back_button.clicked.connect(self.prev_page)

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

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

    def create_navigation_label(self):
        self.navigation_label = QtGui.QLabel('')
        self.navigation_label.setTextFormat(QtCore.Qt.RichText)
        self.navigation_label.setAlignment(QtCore.Qt.AlignCenter)

        self.main_layout.addWidget(self.navigation_label, 0, 1, 1, 1)

    def create_button_controls(self):
        self.back_button = QtGui.QPushButton('')
        self.back_button_opacity_effect = QtGui.QGraphicsOpacityEffect()
        self.back_button_opacity_effect.setOpacity(0.2)
        self.back_button.setGraphicsEffect(self.back_button_opacity_effect)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.back_button.setSizePolicy(sizePolicy)
        self.back_button.setIcon(gf.get_icon('chevron-left'))

        # self.back_button.setStyleSheet('QPushButton {background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0.5, y2:0.5, stop:0 rgba(128, 128, 128, 128), stop:1 rgba(0, 0, 0, 0)); border-style: none; outline: none; border-width: 0px; border-radius: 10px;}')
        self.back_button.setStyleSheet('QPushButton {background-color: transparent; border-style: none; outline: none; border-width: 0px;}')

        self.back_button_hover_animation = QtCore.QPropertyAnimation(self.back_button_opacity_effect, "opacity", self)
        self.back_button_hover_animation.setDuration(200)
        self.back_button_hover_animation.setEasingCurve(QtCore.QEasingCurve.InSine)
        self.back_button_hover_animation.setStartValue(0.2)
        self.back_button_hover_animation.setEndValue(1)

        self.back_button_leave_animation = QtCore.QPropertyAnimation(self.back_button_opacity_effect, "opacity", self)
        self.back_button_leave_animation.setDuration(200)
        self.back_button_leave_animation.setEasingCurve(QtCore.QEasingCurve.OutSine)
        self.back_button_leave_animation.setEndValue(0.2)

        # forward button
        self.forward_button = QtGui.QPushButton('')
        self.forward_button_opacity_effect = QtGui.QGraphicsOpacityEffect(self)
        self.forward_button_opacity_effect.setOpacity(0.2)
        self.forward_button.setGraphicsEffect(self.forward_button_opacity_effect)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        self.forward_button.setSizePolicy(sizePolicy)
        self.forward_button.setIcon(gf.get_icon('chevron-right'))
        # self.forward_button.setStyleSheet('QPushButton {background-color: qlineargradient(spread:pad, x1:1, y1:1, x2:0.5, y2:0.5, stop:0 rgba(128, 128, 128, 128), stop:1 rgba(0, 0, 0, 0)); border-style: none; outline: none; border-width: 0px; border-radius: 10px;}')
        self.forward_button.setStyleSheet('QPushButton {background-color: transparent; border-style: none; outline: none; border-width: 0px;}')

        self.forward_button_hover_animation = QtCore.QPropertyAnimation(self.forward_button_opacity_effect, "opacity", self)
        self.forward_button_hover_animation.setDuration(200)
        self.forward_button_hover_animation.setEasingCurve(QtCore.QEasingCurve.InSine)
        self.forward_button_hover_animation.setStartValue(0.2)
        self.forward_button_hover_animation.setEndValue(1)

        self.forward_button_leave_animation = QtCore.QPropertyAnimation(self.forward_button_opacity_effect, "opacity", self)
        self.forward_button_leave_animation.setDuration(200)
        self.forward_button_leave_animation.setEasingCurve(QtCore.QEasingCurve.OutSine)
        self.forward_button_leave_animation.setEndValue(0.2)

        self.main_layout.addWidget(self.forward_button, 0, 2, 1, 1)
        self.main_layout.addWidget(self.back_button, 0, 0, 1, 1)

        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setColumnStretch(2, 1)

    def navigation_label_link_clicked(self, link):
        if link:
            page, offset = link.split(':')
            self.current_page = int(page)
            self.refresh_search.emit(self.display_limit, int(offset))

    def next_page(self):
        if self.current_page < self.last_page:
            self.current_page += 1
            self.display_offset = self.display_offset + self.display_limit
            self.refresh_search.emit(self.display_limit, self.display_offset)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_offset = self.display_offset - self.display_limit
            self.refresh_search.emit(self.display_limit, self.display_offset)

    def hide(self):
        self.setHidden(True)

    def unhide(self):

        # if self.display_limit <= self.total_query_count:
        self.setHidden(False)
            # return True
        # else:
        #     return False

    def init_navigation(self, query_info):
        if query_info:

            self.total_count = query_info['total_sobjects_count']
            self.total_query_count = query_info['total_sobjects_query_count']
            self.current_page = query_info.get('current_page')

            self.display_limit = query_info['limit']
            self.display_offset = query_info['offset']

            self.gen_pages_line(self.display_limit, self.total_query_count, widget_width=self.width())

            self.resizeEvent = self.main_widget_resizeEvent

            # Checking if we need nav bar
            if self.total_query_count <= 0:
                self.setHidden(True)
            else:
                self.setHidden(False)
        else:
            self.setHidden(True)

    def main_widget_resizeEvent(self, event):
        self.gen_pages_line(self.display_limit, self.total_query_count, widget_width=self.width())
        event.accept()

    def get_offset(self):
        return self.display_offset

    def gen_pages_line(self, display_limit, total_count, widget_width=None):
        pages = []
        page_number = 1
        for i in range(total_count):
            if i % display_limit == 0:
                page_dict = {
                    'offset': i,
                    'page_number': page_number
                }
                pages.append(page_dict)
                page_number += 1
        if pages:
            # guessing how much pages to show in a row
            pages_to_show = widget_width / 32
            if pages_to_show > pages[-1]['page_number']:
                pages_to_show = pages[-1]['page_number']

            self.last_page = pages_to_show

            final_page_line = ''
            last_page = 0
            for i in range(pages_to_show):

                # guessing page by offset
                if pages[i]['offset'] == self.display_offset:
                    self.current_page = pages[i]['page_number']

                # generating links line
                last_page = i+1
                if i+1 == self.current_page:
                    page_line = '<b>{0}</b>'.format(i+1)
                else:
                    page_line = i+1

                final_page_line += '<a href="{1}:{2}" style="color:#bfbfbf">{0}</a> '.format(
                    page_line,
                    pages[i]['page_number'],
                    pages[i]['offset']
                )

            first_items = self.display_offset+1
            second_items = self.display_limit + self.display_offset
            if second_items > total_count:
                second_items = total_count

            # links for last page
            if pages[-1]['page_number'] > last_page:
                final_page_line = '{0} ... <a href="{1}:{2}" style="color:#bfbfbf">{1}</a>'.format(
                    final_page_line,
                    pages[-1]['page_number'],
                    pages[-1]['offset'])
            # font-size:11pt;
            self.navigation_label.setText(
                '<span style=" color:#828282;">Showing {0} - {1} of {2}<br>{3}</span>'.format(
                    first_items,
                    second_items,
                    total_count,
                    final_page_line
                ))


class Ui_resultsFormWidget(QtGui.QWidget, ui_search_results_tree.Ui_resultsForm):
    def __init__(self, project, stype, info, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.setupUi(self)

        self.info = info
        self.stype = stype
        self.project = project
        self.created = False

        self.checkin_out_config = cfg_controls.get_checkin()

        self.bottom_navigataion_widget = None

        self.current_tree_widget_item = None
        self.current_results_tree_widget_item = None
        self.current_results_versions_tree_widget_item = None

    def create_ui(self):

        self.create_separate_versions_tree()
        self.create_progress_bar()
        # self.setAcceptDrops(True)
        self.create_bottom_navigation_widget()

        self.resultsTreeWidget.setAlternatingRowColors(True)
        self.resultsVersionsTreeWidget.setAlternatingRowColors(True)

        # self.create_results_tree_widgets()
        # self.update_search_results()
        self.initial_load_results()

        self.controls_actions()

        self.created = True

    def update_default_filter(self, query_text):
        checkin_out_widget = self.get_current_checkin_out_widget()
        adv_search_widget = checkin_out_widget.get_advanced_search_widget()
        df = adv_search_widget.get_default_filter()
        adv_search_widget.update_default_filter((df[0], df[1], query_text))

    def initial_load_results(self, limit=None, offset=None):
        if limit is None:
            limit = self.get_limit()

        if offset is None:
            offset = self.get_offset()

        order_bys = ['name']

        self.query_sobjects_new(
            filters=self.get_filters(),
            stype=self.stype.get_code(),
            project=self.project.get_code(),
            order_bys=order_bys,
            limit=limit,
            offset=offset,
        )

    def toggle_results_view(self, view='separate_vertical'):

        print 'toggling', view

    def update_search_results(self, limit=None, offset=None,  refresh=False):
        # collecting new filters, limit, offset, etc...
        # self.get_info_dict()

        if limit is None:
            limit = self.get_limit()

        if offset is None:
            offset = self.get_offset()

        if refresh:
            # marking this as refreshing
            self.info['refresh'] = True

            # collecting current tree widget state
            self.info['state'] = gf.tree_state(self.resultsTreeWidget, {})

        order_bys = ['name']

        # making query for current search with current search options
        self.query_sobjects_new(
            filters=self.get_filters(),
            stype=self.stype.get_code(),
            project=self.project.get_code(),
            order_bys=order_bys,
            limit=limit,
            offset=offset,
        )

    def get_info_dict(self):

        current_state = self.collect_state()
        if current_state:
            self.info['state'] = current_state

        self.info['title'] = self.get_tab_title()
        self.info['offset'] = self.collect_offset()
        self.info['limit'] = self.get_limit()
        self.info['filters'] = self.get_filters()

        self.info['current_index'] = self.get_current_index()

        return self.info

    def get_state(self):
        return self.info['state']

    def set_state(self, state):
        self.info['state'] = state

    def collect_state(self):
        self.info['state'] = gf.tree_state(self.resultsTreeWidget, {})
        return self.info['state']

    def apply_state(self, state=None):
        if not state:
            gf.tree_state_revert(self.resultsTreeWidget, self.info['state'])
        else:
            gf.tree_state_revert(self.resultsTreeWidget, state)

    def get_offset(self):
        return self.info['offset']

    def collect_offset(self):
        if self.bottom_navigataion_widget:
            return self.bottom_navigataion_widget.get_offset()
        else:
            return self.info['offset']

    def set_offset(self, offset):
        self.info['offset'] = offset

    def get_limit(self):
        return self.info['limit']

    def set_limit(self, limit):
        self.info['limit'] = limit

    def get_current_index(self):
        checkin_out_widget = self.get_current_checkin_out_widget()
        search_widget = checkin_out_widget.get_search_widget()
        results_tab_widget = search_widget.get_results_tab_widget()
        current_idx = results_tab_widget.indexOf(self)

        return current_idx

    def get_tab_title(self):
        checkin_out_widget = self.get_current_checkin_out_widget()
        search_widget = checkin_out_widget.get_search_widget()
        results_tab_widget = search_widget.get_results_tab_widget()
        current_idx = results_tab_widget.indexOf(self)

        results_tab_widget.tabText(current_idx)
        self.info['title'] = results_tab_widget.tabText(current_idx)

        return self.info['title']

    def set_tab_title(self, title=''):
        checkin_out_widget = self.get_current_checkin_out_widget()
        search_widget = checkin_out_widget.get_search_widget()
        results_tab_widget = search_widget.get_results_tab_widget()
        current_idx = results_tab_widget.indexOf(self)

        self.info['title'] = title
        results_tab_widget.setTabText(current_idx, title)

    def get_filters(self):
        return self.info['filters']

    def set_filters(self, filters):
        self.info['filters'] = filters

    def update_filters(self, check_valid=False):
        checkin_out_widget = self.get_current_checkin_out_widget()
        adv_search_widget = checkin_out_widget.get_advanced_search_widget()

        self.set_filters(adv_search_widget.get_filters(check_valid))

    # def create_results_tree_widgets(self):
    #
    #     self.resultsTreeWidget.setAcceptDrops(True)
    #     self.resultsTreeWidget.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
    #
    #     self.resultsTreeWidget.dragEnterEvent = self.resultsTreeWidget_dragEnterEvent
    #     self.resultsTreeWidget.dragLeaveEvent = self.resultsTreeWidget_dragLeaveEvent
    #     self.resultsTreeWidget.dragMoveEvent = self.resultsTreeWidget_dragMoveEvent
    #     self.resultsTreeWidget.dropEvent = self.resultsTreeWidget_dropEvent
    #
    #     # self.resultsVersionsTreeWidget.setAcceptDrops(True)
    #     # self.resultsVersionsTreeWidget.setDragDropMode(QtGui.QAbstractItemView.DragOnly)
    #     self.trees_items = set()
    #
    # def resultsTreeWidget_dragLeaveEvent(self, event):
    #
    #     for i in self.trees_items:
    #         i.set_drop_indicator_off()
    #
    #     self.trees_items = set()
    #
    #     event.accept()
    #
    # def resultsTreeWidget_dragEnterEvent(self, event):
    #
    #     if event.mimeData().hasUrls:
    #         event.accept()
    #     else:
    #         event.ignore()
    #
    # def resultsTreeWidget_dragMoveEvent(self, event):
    #
    #     tree_item = self.resultsTreeWidget.itemAt(event.pos())
    #     tree_item_widget = self.resultsTreeWidget.itemWidget(tree_item, 0)
    #     self.trees_items.add(tree_item_widget)
    #
    #     if tree_item_widget:
    #         tree_item_widget.set_drop_indicator_on()
    #
    #     if event.mimeData().hasUrls:
    #         event.setDropAction(QtCore.Qt.CopyAction)
    #         event.accept()
    #     else:
    #         event.ignore()
    #
    # def resultsTreeWidget_dropEvent(self, event):
    #     if event.mimeData().hasUrls:
    #         event.setDropAction(QtCore.Qt.CopyAction)
    #         event.accept()
    #         links = []
    #         for url in event.mimeData().urls():
    #             links.append(unicode(url.toLocalFile()))
    #         # self.append_items_to_tree(links)
    #         print links
    #     else:
    #         event.ignore()

    def controls_actions(self):
        # Tree widget actions
        # self.resultsTreeWidget.itemPressed.connect(lambda:  self.set_current_results_tree_widget_item(
        #     self.resultsTreeWidget))
        # self.resultsTreeWidget.itemPressed.connect(self.load_preview)
        # self.resultsTreeWidget.itemPressed.connect(self.fill_versions_items)
        self.resultsTreeWidget.itemSelectionChanged.connect(self.selection_changed)
        self.resultsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsTreeWidget.customContextMenuRequested.connect(self.open_item_context_menu)

        self.resultsTreeWidget.itemCollapsed.connect(self.send_collapse_event_to_item)
        self.resultsTreeWidget.itemExpanded.connect(self.send_expand_event_to_item)
        self.resultsTreeWidget.itemDoubleClicked.connect(self.send_item_double_click)

        # Separate Snapshots tree widget actions
        self.resultsVersionsTreeWidget.itemPressed.connect(lambda: self.set_current_results_versions_tree_widget_item(
            self.resultsVersionsTreeWidget))

        self.resultsVersionsTreeWidget.itemPressed.connect(self.load_preview)
        self.resultsVersionsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsVersionsTreeWidget.customContextMenuRequested.connect(self.open_item_context_menu)
        self.resultsVersionsTreeWidget.itemDoubleClicked.connect(self.send_item_double_click)

    def get_current_results_tree_widget(self):
        return self.resultsTreeWidget

    def get_results_tree_widget(self):
        return self.resultsTreeWidget

    def get_results_versions_tree_widget(self):
        return self.resultsVersionsTreeWidget

    def selection_changed(self):

        if self.resultsTreeWidget.selectedItems():
            current_tree_item = self.resultsTreeWidget.selectedItems()[0]
            self.fill_versions_items(current_tree_item, 0)
            self.current_tree_widget_item = self.resultsTreeWidget.itemWidget(current_tree_item, 0)
            self.load_preview()

    def open_item_context_menu(self):
        checkin_out_widget = self.get_current_checkin_out_widget()
        checkin_out_widget.open_item_menu(self.get_current_tree_widget_item())

    def query_sobjects_new(self, filters, stype, project, order_bys=[], limit=None, offset=None):

        search_type = tc.server_start().build_search_type(stype, project)

        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Getting SObjects</span>')

        def get_sobjects_new_agent():
            """ If we have traceback, it points us here"""
            return tc.get_sobjects_new(
                search_type=search_type,
                filters=filters,
                order_bys=order_bys,
                limit=limit,
                offset=offset
            )

        server_thread_pool = QtCore.QThreadPool()
        server_thread_pool.setMaxThreadCount(env_tactic.max_threads())
        env_inst.set_thread_pool(server_thread_pool, 'server_query/server_thread_pool')

        query_sobjects_worker = gf.get_thread_worker(
            get_sobjects_new_agent,
            thread_pool=env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=self.fill_items,
            error_func=gf.error_handle
        )
        query_sobjects_worker.start()

    @gf.catch_error
    def fill_items(self, result):
        env_inst.ui_main.set_info_status_text('<span style=" font-size:8pt; color:#00ff00;">Filling SObjects</span>')

        self.res = True

        self.sobjects = result[0]
        self.query_info = result[1]

        gf.recursive_close_tree_item_widgets(self.resultsTreeWidget)
        self.resultsTreeWidget.clear()

        self.progress_bar.setVisible(True)
        total_sobjects = len(self.sobjects.keys()) - 1

        for p, sobject in enumerate(self.sobjects.itervalues()):
            item_info = {
                'relates_to': 'checkin_out',
                'is_expanded': False,
                'sep_versions': self.sep_versions,
            }

            gf.add_sobject_item(
                self.resultsTreeWidget,
                self,
                sobject,
                self.stype,
                item_info,
                ignore_dict=None,
            )
            if total_sobjects:
                if p % 5 == 0:
                    self.progress_bar.setValue(int(p * 100 / total_sobjects))

        if not self.info['title'] and not self.get_tab_title():
            self.set_tab_title('Found {0} {1}'.format(int(self.query_info.get('total_sobjects_query_count')), self.stype.get_pretty_name()))

        if self.get_state():
            self.apply_state(self.info.get('state'))

            if self.info.get('refresh'):
                self.info['refresh'] = None

            self.info['state'] = None

        self.progress_bar.setVisible(False)

        self.bottom_navigataion_widget.init_navigation(self.query_info)
        self.update_filters(True)

        env_inst.ui_main.set_info_status_text('')

    def create_bottom_navigation_widget(self):
        # self.gridLayout = QtGui.QGridLayout(self.resultsTreeWidget.viewport())
        # self.gridLayout.setContentsMargins(0, 0, 0, 0)
        # spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        # self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)

        self.bottom_navigataion_widget = Ui_navigationWidget(project=self.project, stype=self.stype)
        self.bottom_navigataion_widget.refresh_search.connect(self.update_search_results)

        self.bottom_navigataion_widget.setHidden(True)

        self.resultsLayout.addWidget(self.bottom_navigataion_widget)

        # self.gridLayout.addWidget(self.bottom_navigataion_widget)

        # self.bottom_navigataion_widget.setHidden(True)

        # scroll = self.resultsTreeWidget.verticalScrollBar()
        #
        # self.maximum = 0
        # self.resized = True
        #
        # def range_changing(v):
        #
        #     # print v, 'range_changing'
        #
        #     # print 'Hiding', self.resized
        #     # if self.resized:
        #     #     self.bottom_navigataion_widget.hide()
        #
        #     self.maximum = scroll.maximum()
        #     self.resized = True
        #     # if v == 0:
        #     #     self.bottom_navigataion_widget.hide()
        #
        # def value_changing(v1):
        #     # print v1, 'value_changing'
        #
        #     if self.resized:
        #         scroll.setMaximum(self.maximum + self.bottom_navigataion_widget.height())
        #         self.resized = False
        #
        #     if v1 > scroll.maximum()-1:
        #         x = self.bottom_navigataion_widget.pos().x()
        #         self.bottom_navigataion_widget.move(x, self.resultsTreeWidget.viewport().height() - self.bottom_navigataion_widget.height())
        #
        #     self.bottom_navigataion_widget.unhide()
        #
        # scroll.valueChanged.connect(value_changing)
        # scroll.rangeChanged.connect(range_changing)

    @gf.catch_error
    def send_item_double_click(self, *args):
        modifiers = QtGui.QApplication.keyboardModifiers()

        checkin_out_widget = self.get_current_checkin_out_widget()

        checkin_options_widget = checkin_out_widget.get_checkin_options_widget_config()

        # current_widget = checkin_out_widget.get_current_tree_widget()
        # current_tree_widget_item = current_widget.get_current_tree_widget_item()

        current_tree_widget_item = self.get_current_tree_widget_item()

        if modifiers == QtCore.Qt.ShiftModifier and checkin_options_widget.doubleClickOpenCheckBox.isChecked():
            if current_tree_widget_item.type == 'snapshot':
                checkin_out_widget.open_file()
        if checkin_options_widget.doubleClickSaveCheckBox.isChecked():
            if current_tree_widget_item.type in ['process', 'snapshot', 'sobject']:
                checkin_out_widget.save_file()

    @gf.catch_error
    def set_current_results_tree_widget_item(self, tree_widget):
        self.current_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)
        self.current_results_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)

    @gf.catch_error
    def set_current_results_versions_tree_widget_item(self, tree_widget):
        self.current_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)
        self.current_results_versions_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)

    def get_current_checkin_out_widget(self):
        return env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

    def get_current_tree_widget_item(self):
        if not self.current_tree_widget_item:
            self.set_current_results_tree_widget_item(self.resultsTreeWidget)
        return self.current_tree_widget_item

    def get_current_results_tree_widget_item(self):
        return self.current_results_tree_widget_item

    def get_current_results_versions_tree_widget_item(self):
        return self.current_results_versions_tree_widget_item

    def update_current_items_trees(self, force_full_update=False):
        if env_inst.get_thread_pool('server_query/server_thread_pool'):
            if env_inst.get_thread_pool('server_query/server_thread_pool').activeThreadCount() == 0:
                if force_full_update:
                    self.search_widget.search_results_widget.update_item_tree(force_full_update=True)
                elif self.current_results_versions_tree_widget_item:
                    self.current_results_versions_tree_widget_item = None
                    self.search_widget.search_results_widget.update_item_tree(self.current_results_versions_tree_widget_item)
                elif self.current_results_tree_widget_item:
                    self.current_results_tree_widget_item = None
                    self.search_widget.search_results_widget.update_item_tree(self.current_results_tree_widget_item)

    @gf.catch_error
    def send_collapse_event_to_item(self, tree_item):
        tree_widget = self.resultsTreeWidget.itemWidget(tree_item, 0)
        tree_widget.collapse_tree_item()

        if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            tree_widget.collapse_recursive()

    @gf.catch_error
    def send_expand_event_to_item(self, tree_item):
        tree_widget = self.resultsTreeWidget.itemWidget(tree_item, 0)
        tree_widget.expand_tree_item()

        if QtGui.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            tree_widget.expand_recursive()

    @gf.catch_error
    def fill_versions_items(self, widget, *args):
        if self.resultsVersionsTreeWidget.isVisible():
            parent_widget = self.resultsTreeWidget.itemWidget(widget, 0)

            if parent_widget.type == 'snapshot':
                process = parent_widget.process
                context = parent_widget.context
                snapshots = parent_widget.sobject.process[process].contexts[context].versions

                self.resultsVersionsTreeWidget.clear()
                gf.add_versions_snapshot_item(
                    self.resultsVersionsTreeWidget,
                    self,
                    parent_widget.sobject,
                    parent_widget.stype,
                    process,
                    parent_widget.pipeline,
                    context,
                    snapshots,
                    parent_widget.info,
                )

            if parent_widget.type == 'sobject':
                self.resultsVersionsTreeWidget.clear()

            if parent_widget.type == 'process':
                self.resultsVersionsTreeWidget.clear()

            if parent_widget.type == 'child':
                self.resultsVersionsTreeWidget.clear()

    def update_versions_items(self, item_widget):
        if self.resultsVersionsTreeWidget.isVisible():

            if item_widget.type == 'snapshot':
                process = item_widget.process
                context = item_widget.context

                snapshots = item_widget.sobject.process[process].contexts[context].versions

                self.resultsVersionsTreeWidget.clear()

                gf.add_versions_snapshot_item(
                    self.resultsVersionsTreeWidget,
                    self,
                    item_widget.sobject,
                    item_widget.stype,
                    process,
                    item_widget.pipeline,
                    context,
                    snapshots,
                    item_widget.info,
                )

    def clear_versionless_tree_widget(self):
        gf.recursive_close_tree_item_widgets(self.resultsTreeWidget)
        self.resultsTreeWidget.clear()

    def clear_versions_tree_widget(self):
        gf.recursive_close_tree_item_widgets(self.resultsVersionsTreeWidget)
        self.resultsVersionsTreeWidget.clear()

    def clear_tree_widgets(self):
        self.clear_versionless_tree_widget()
        self.clear_versions_tree_widget()

    def browse_snapshot(self, item):
        checkin_out_widget = self.get_current_checkin_out_widget()
        snapshot_browser = checkin_out_widget.get_snapshot_browser()
        snapshot_browser.set_item_widget(item)

    @gf.catch_error
    def load_preview(self, *args):
        nested_item = self.current_tree_widget_item
        self.browse_snapshot(nested_item)

        # TODO Make skey line
        # env_inst.ui_main_tabs[self.project.get_code()].skeyLineEdit.setText(nested_item.get_skey(True))

        checkin_out_widget = self.get_current_checkin_out_widget()

        description_widget = checkin_out_widget.get_description_widget()

        columns_viewer_widget = checkin_out_widget.get_columns_viewer_widget()

        fast_controls_widget = checkin_out_widget.get_fast_controls_widget()

        if nested_item.type in ['sobject', 'snapshot', 'process']:
            fast_controls_widget.set_item(nested_item)
            description_widget.set_item(nested_item)
            columns_viewer_widget.set_item(nested_item)
        else:
            fast_controls_widget.set_item(None)
            description_widget.set_item(None)

    def get_is_separate_versions(self):
        return self.sep_versions

    def create_separate_versions_tree(self):

        self.sep_versions = gf.get_value_from_config(self.checkin_out_config, 'versionsSeparateCheckinCheckBox')
        if self.sep_versions:
            self.sep_versions = bool(int(self.sep_versions))

        if not self.sep_versions:
            self.verticalLayoutWidget_3.close()
        else:
            if gf.get_value_from_config(self.checkin_out_config, 'bottomVersionsRadioButton'):
                self.resultsSplitter.setOrientation(QtCore.Qt.Vertical)
            else:
                self.resultsSplitter.setOrientation(QtCore.Qt.Horizontal)

    def create_progress_bar(self):
        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.hide()
        self.resultsLayout.addWidget(self.progress_bar)

    def showEvent(self, event):

        if not self.created:
            self.create_ui()

        event.accept()
