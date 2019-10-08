from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.tactic_classes as tc
import thlib.global_functions as gf


class Ui_columnsViewerWidget(QtGui.QWidget):
    def __init__(self, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.project = project
        self.item = None

        self.create_ui()

    def create_ui(self):

        self.create_layout()
        self.create_tabbed_widget()

    def controls_actions(self):
        pass

    def set_item(self, item):
        self.item = item
        if self.item:
            self.customize_with_item()
        else:
            self.customize_without_item()

    def customize_with_item(self):
        self.columns_tab_widget.clear()

        table_columns = []
        stype = self.item.stype

        for i in stype.get_definition('table'):
            table_columns.append(i.get('name'))

        exclude_columns = ['__search_type__', '__search_key__', '__tasks_count__', '__notes_count__', '__snapshots__']

        if self.item.type == 'snapshot':
            snapshot_obj = self.item.get_snapshot()
            if snapshot_obj:
                snapshot = snapshot_obj.get_snapshot()
                for column, val in snapshot.items():
                    if column not in exclude_columns:
                        if column in table_columns:
                            text_edit = QtGui.QTextEdit()
                            text_edit.setText(unicode(val))

                            column_title = None
                            for j in stype.get_definition('definition'):
                                if j.get('name') == column:
                                    column_title = j.get('title')

                            if not column_title:
                                column_title = gf.prettify_text(column)

                            self.columns_tab_widget.addTab(text_edit, column_title)

        if self.item.type == 'sobject':
            sobject_obj = self.item.get_sobject()
            if sobject_obj:
                sobject = sobject_obj.get_info()
                for column, val in sobject.items():
                    if column not in exclude_columns:
                        if column in table_columns:
                            text_edit = QtGui.QTextEdit()
                            text_edit.setText(unicode(val))

                            column_title = None
                            for j in stype.get_definition('definition'):
                                if j.get('name') == column:
                                    column_title = j.get('title')

                            if not column_title:
                                column_title = gf.prettify_text(column)

                            self.columns_tab_widget.addTab(text_edit, column_title)

    def customize_without_item(self):
        self.columns_tab_widget.clear()

    def create_layout(self):
        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)

    def create_tabbed_widget(self):
        self.columns_tab_widget = QtGui.QTabWidget(self)

        self.columns_tab_widget.setMovable(True)
        self.columns_tab_widget.setTabsClosable(True)
        self.columns_tab_widget.setObjectName("notes_tab_widget")
        self.columns_tab_widget.setStyleSheet(
            '#notes_tab_widget > QTabBar::tab {background: transparent;border: 2px solid transparent;'
            'border-top-left-radius: 3px;border-top-right-radius: 3px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;padding: 4px;}'
            '#notes_tab_widget > QTabBar::tab:selected, #notes_tab_widget > QTabBar::tab:hover {'
            'background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(255, 255, 255, 48), stop: 1 rgba(255, 255, 255, 32));}'
            '#notes_tab_widget > QTabBar::tab:selected {border-color: transparent;}'
            '#notes_tab_widget > QTabBar::tab:!selected {margin-top: 0px;}')

        self.main_layout.addWidget(self.columns_tab_widget)
