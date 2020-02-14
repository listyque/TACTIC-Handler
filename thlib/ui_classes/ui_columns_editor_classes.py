from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.tactic_classes as tc
from thlib.environment import env_inst
import thlib.global_functions as gf
from thlib.ui_classes.ui_custom_qwidgets import Ui_horizontalCollapsableWidget
from thlib.ui_classes.ui_tactic_column_classes import Ui_tacticColumnEditorWidget


class Ui_columnsEditorWidget(QtGui.QWidget):
    def __init__(self, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.project = project
        self.stype = stype
        self.item = None
        self.items = []
        self.columns_widgets = []
        self.multiple_mode = False

        self.current_active_tab = 0

        self.create_ui()

    def create_ui(self):

        self.create_main_layout()

        self.create_toolbar()
        self.create_options_toolbar()
        self.create_stretch()

        self.create_tabbed_widget()

        self.controls_actions()

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)

    def controls_actions(self):
        self.save_button.clicked.connect(self.save_all_changes)
        self.refresh_button.clicked.connect(self.refresh)
        self.definition_combo_box.currentIndexChanged.connect(self.refresh)

    def create_toolbar(self):

        self.collapsable_toolbar = Ui_horizontalCollapsableWidget()
        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.setSpacing(0)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.collapsable_toolbar.set_direction('right')
        self.collapsable_toolbar.setLayout(buttons_layout)
        self.collapsable_toolbar.setCollapsed(False)

        self.save_button = QtGui.QToolButton()
        self.save_button.setAutoRaise(True)
        self.save_button.setIcon(gf.get_icon('content-save-all', icons_set='mdi', scale_factor=1))
        self.save_button.setToolTip('Save Current Changes')

        self.refresh_button = QtGui.QToolButton()
        self.refresh_button.setAutoRaise(True)
        self.refresh_button.setIcon(gf.get_icon('refresh', icons_set='mdi', scale_factor=1.3))
        self.refresh_button.setToolTip('Refresh Current Tasks')

        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.refresh_button)

        self.main_layout.addWidget(self.collapsable_toolbar, 0, 0, 1, 1)

    def create_options_toolbar(self):

        self.collapsable_options_toolbar = Ui_horizontalCollapsableWidget()
        buttons_layout = QtGui.QHBoxLayout()
        buttons_layout.setSpacing(9)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.collapsable_options_toolbar.set_direction('right')
        self.collapsable_options_toolbar.setLayout(buttons_layout)
        self.collapsable_options_toolbar.setCollapsed(True)

        self.auto_save_check_box = QtGui.QCheckBox('Autosave')
        self.auto_save_check_box.setChecked(False)

        self.definition_label = QtGui.QLabel('Definition: ')

        self.definition_combo_box = QtGui.QComboBox()

        buttons_layout.addWidget(self.definition_label)
        buttons_layout.addWidget(self.definition_combo_box)
        buttons_layout.addWidget(self.auto_save_check_box)

        self.main_layout.addWidget(self.collapsable_options_toolbar, 0, 1, 1, 1)

    def create_stretch(self):
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.main_layout.addItem(spacerItem, 0, 2, 1, 1)
        self.main_layout.setColumnStretch(2, 1)

    def fill_definition_combo_box(self):

        self.definition_combo_box.clear()

        stype = self.item.stype

        if stype.info.get('definition'):
            current_idx = 0
            default_current_definition = 'table'

            for idx, definition in enumerate(stype.info['definition'].keys()):
                if definition == default_current_definition:
                    current_idx = idx
                self.definition_combo_box.addItem(gf.prettify_text(definition))
                self.definition_combo_box.setItemData(idx, definition, QtCore.Qt.UserRole)

            self.definition_combo_box.setCurrentIndex(current_idx)

    def save_all_changes(self):

        if self.multiple_mode:
            data_to_update = {}

            for item in self.items:
                update_dict = {}
                for column_widget in self.columns_widgets:
                    changed_data = column_widget.get_changed_data()
                    if changed_data is not None:
                        update_dict[column_widget.get_column()] = changed_data

                if self.item.type == 'snapshot':
                    sobject = item.get_snapshot()
                    sobject.project = self.project  # Snapshot class created without project in it
                else:
                    sobject = item.get_sobject()

                data_to_update[sobject.get_search_key()] = update_dict

            return tc.server_start(project=self.project.get_code()).update_multiple(
                data=data_to_update,
                triggers=True
            )
        else:

            if self.item.type == 'snapshot':
                sobject = self.item.get_snapshot()
                sobject.project = self.project  # Snapshot class created without project in it
            else:
                sobject = self.item.get_sobject()

            for column_widget in self.columns_widgets:
                changed_data = column_widget.get_changed_data()
                if changed_data is not None:
                    sobject.set_value(column_widget.get_column(), changed_data)

            sobject.commit()

    def set_dock_title(self, title_string):

        checkin_out_widget = env_inst.get_check_tree(self.project.get_code(), 'checkin_out', self.stype.get_code())

        columns_viewer_widget = checkin_out_widget.get_columns_viewer_widget()

        dock_widget = columns_viewer_widget.parent()
        if dock_widget:
            if isinstance(dock_widget, QtGui.QDockWidget):
                dock_widget.setWindowTitle(title_string)

    def refresh(self):
        if self.multiple_mode:
            self.customize_with_multiple_items()
        else:
            self.customize_with_item()

    def set_items(self, items_list):

        if not self.visibleRegion().isEmpty():
            self.items = items_list

            self.fill_definition_combo_box()

            if self.items:
                self.customize_with_multiple_items()
            else:
                self.customize_without_item()

    def set_item(self, item):
        if not self.visibleRegion().isEmpty():
            self.item = item

            self.fill_definition_combo_box()

            if self.item:
                self.customize_with_item()
            else:
                self.customize_without_item()

    def customize_with_multiple_items(self):

        self.multiple_mode = True

        self.current_active_tab = self.columns_tab_widget.currentIndex()

        self.columns_tab_widget.clear()
        self.columns_widgets = []

        self.set_dock_title(u'Multiple Editing Mode for: {0} items'.format(len(self.items)))

        table_columns = []
        stype = self.item.stype

        idx = self.definition_combo_box.currentIndex()
        current_definition = self.definition_combo_box.itemData(idx, QtCore.Qt.UserRole)
        if not current_definition:
            current_definition = 'table'

        for i in stype.get_definition(current_definition):
            table_columns.append(i.get('name'))

        exclude_columns = ['__search_type__', '__search_key__', '__tasks_count__', '__notes_count__', '__snapshots__']

        if self.item.type == 'snapshot':
            sobject = self.item.get_snapshot()
        else:
            sobject = self.item.get_sobject()

        if sobject:
            sobject_dict = sobject.get_info()
            for column, val in sobject_dict.items():
                if column not in exclude_columns:
                    if column in table_columns:
                        column_editor = Ui_tacticColumnEditorWidget(sobject, column, stype, multiple_mode=True)

                        column_title = None
                        for j in stype.get_definition('definition'):
                            if j.get('name') == column:
                                column_title = j.get('title')

                        if not column_title:
                            column_title = gf.prettify_text(column)

                        self.columns_widgets.append(column_editor)
                        self.columns_tab_widget.addTab(column_editor, u'{0} | {1}'.format(column_title, len(self.items)))

            self.columns_tab_widget.setCurrentIndex(self.current_active_tab)

    def customize_with_item(self):

        self.multiple_mode = False

        self.current_active_tab = self.columns_tab_widget.currentIndex()

        self.columns_tab_widget.clear()
        self.columns_widgets = []

        table_columns = []
        stype = self.item.stype

        idx = self.definition_combo_box.currentIndex()
        current_definition = self.definition_combo_box.itemData(idx, QtCore.Qt.UserRole)
        if not current_definition:
            current_definition = 'table'

        for i in stype.get_definition(current_definition):
            table_columns.append(i.get('name'))

        exclude_columns = ['__search_type__', '__search_key__', '__tasks_count__', '__notes_count__', '__snapshots__']

        if self.item.type == 'snapshot':
            sobject = self.item.get_snapshot()
        else:
            sobject = self.item.get_sobject()

        if sobject:
            self.set_dock_title(u'Editing Columns of: {0}'.format(sobject.get_title()))

            sobject_dict = sobject.get_info()
            for column, val in sobject_dict.items():
                if column not in exclude_columns:
                    if column in table_columns:
                        column_editor = Ui_tacticColumnEditorWidget(sobject, column, stype)

                        column_title = None
                        for j in stype.get_definition('definition'):
                            if j.get('name') == column:
                                column_title = j.get('title')

                        if not column_title:
                            column_title = gf.prettify_text(column)

                        self.columns_widgets.append(column_editor)
                        self.columns_tab_widget.addTab(column_editor, column_title)

            self.columns_tab_widget.setCurrentIndex(self.current_active_tab)

    def customize_without_item(self):
        self.multiple_mode = False
        self.item = None
        self.items = []
        self.columns_widgets = []

        self.columns_tab_widget.clear()

        self.set_dock_title(u'Columns Editor')

    def create_tabbed_widget(self):
        self.columns_tab_widget = QtGui.QTabWidget(self)

        self.columns_tab_widget.setMovable(True)
        self.columns_tab_widget.setTabsClosable(False)
        self.columns_tab_widget.setObjectName("notes_tab_widget")
        self.columns_tab_widget.setStyleSheet(
            '#notes_tab_widget > QTabBar::tab {background: transparent;border: 2px solid transparent;'
            'border-top-left-radius: 3px;border-top-right-radius: 3px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;padding: 4px;}'
            '#notes_tab_widget > QTabBar::tab:selected, #notes_tab_widget > QTabBar::tab:hover {'
            'background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(255, 255, 255, 48), stop: 1 rgba(255, 255, 255, 32));}'
            '#notes_tab_widget > QTabBar::tab:selected {border-color: transparent;}'
            '#notes_tab_widget > QTabBar::tab:!selected {margin-top: 0px;}')

        self.main_layout.addWidget(self.columns_tab_widget, 1, 0, 1, 3)
