import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from lib.environment import env_inst


# edit/input widgets
class QtTacticEditWidget(QtGui.QWidget):
    def __init__(self, tactic_widget=None, qt_widgets=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.tactic_widget = tactic_widget

        self.parent_ui = parent

        self.qt_widgets = qt_widgets

        self.create_main_layout()
        self.create_scroll_area()

        self.create_control_buttons()
        self.controls_actions()

        self.add_widgets_to_scroll_area()

    def controls_actions(self):
        self.addNewButton.clicked.connect(self.commit_insert)
        self.saveButton.clicked.connect(self.commit_update)
        self.cancelButton.clicked.connect(lambda: self.parent_ui.close())

    def get_data(self):
        data = {}
        ignore = ['preview']

        for widget in self.qt_widgets:
            column = widget.get_column()
            if column not in ignore:
                data[column] = widget.get_data()

        return data

    def commit_update(self):
        data = self.get_data()
        self.tactic_widget.commit(data)

        self.parent_ui.refresh_results()
        self.parent_ui.close()

    def commit_insert(self):
        data = self.get_data()
        self.tactic_widget.commit(data)

        self.parent_ui.refresh_results()
        self.parent_ui.close()

    def create_control_buttons(self):
        self.addNewButton = QtGui.QPushButton('Add')
        self.saveButton = QtGui.QPushButton('Save')
        self.cancelButton = QtGui.QPushButton('Cancel')

        if self.tactic_widget.view == 'insert':
            self.main_layout.addWidget(self.addNewButton, 1, 0, 1, 1)
        else:
            self.main_layout.addWidget(self.saveButton, 1, 0, 1, 1)
        self.main_layout.addWidget(self.cancelButton, 1, 1, 1, 1)

        self.main_layout.setColumnStretch(0, 1)

    def add_widgets_to_scroll_area(self):
        # self.ws = QTacticSelectWdg(parent=self, tactic_widget=None)
        # self.scroll_area_layout.addWidget(self.ws)

        for widget in self.qt_widgets:
            widget.setParent(self)
            self.scroll_area_layout.addWidget(widget)
        # for i in range(50):
        #     self.scroll_area_layout.addWidget(QtGui.QPushButton('DSA' + str(i)))

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(9, 9, 9, 9)

    def create_scroll_area(self):
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area_contents = QtGui.QWidget()
        self.scroll_area_layout = QtGui.QVBoxLayout(self.scroll_area_contents)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_contents)
        self.scroll_area_layout.setAlignment(QtCore.Qt.AlignTop)

        self.main_layout.addWidget(self.scroll_area, 0, 0, 1, 0)


class QTacticBasicInputWdg(object):
    def __init__(self):
        self.init_ui()

    def init_ui(self):
        self.create_main_layout()
        self.create_label()

    def create_main_layout(self):
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setContentsMargins(9, 9, 9, 9)
        self.main_layout.setColumnStretch(1, 1)

    def create_label(self):
        self.label = QtGui.QLabel()
        self.main_layout.addWidget(self.label, 0, 0)
        self.label.setMinimumWidth(100)
        self.label.setAlignment(QtCore.Qt.AlignRight)

    def create_conrol(self, control_widget):
        self.main_layout.addWidget(control_widget, 0, 1)

    def set_control_widget(self, control_widget):
        self.create_conrol(control_widget)

    def set_title(self, title):
        self.label.setText(title)


class QTacticSelectWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_combo_box()

        self.set_title(self.tactic_widget.get_title())
        self.set_control_widget(self.combo_box)

        self.add_items_to_combo_box()

    def get_data(self):
        if self.combo_box.currentIndex() > 0:
            return self.combo_box.currentText()
        else:
            return ''

    def get_column(self):
        action_options = self.tactic_widget.get_action_options()
        column = action_options.get('column')
        if column:
            return column

    def create_combo_box(self):
        self.combo_box = QtGui.QComboBox()
        self.combo_box.setEditable(True)
        self.combo_box.setCurrentIndex(0)

    def add_items_to_combo_box(self):
        labels = self.tactic_widget.get_labels()
        for label in labels:
            self.combo_box.addItem(label)


class QTacticSimpleUploadWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_upload_wdg()

        self.set_title(self.tactic_widget.get_title())
        self.set_control_widget(self.upload_wdg)

        self.controls_actions()

    def controls_actions(self):

        self.browse_button.clicked.connect(self.browse_for_preview)

    def get_data(self):
        return None

    def get_column(self):
        return self.tactic_widget.get_name()

    def browse_for_preview(self):
        options = QtGui.QFileDialog.Options()
        options |= QtGui.QFileDialog.DontUseNativeDialog
        file_name, filter = QtGui.QFileDialog.getOpenFileName(self, 'Browse for Preview Image',
                                                              self.text_edit.text(),
                                                              'All Images (*.jpg | *.jpeg | *.png);;'
                                                              'JPEG Files (*.jpg | *.jpeg);;'
                                                              'PNG Files (*.png)',
                                                              '', options)
        if file_name:
            self.text_edit.setText(file_name)


    def create_upload_wdg(self):
        self.create_browse_button()
        self.create_edit()
        self.create_drop_plate()

        self.upload_wdg = QtGui.QWidget()
        self.upload_wdg_layout = QtGui.QGridLayout()
        self.upload_wdg.setLayout(self.upload_wdg_layout)
        self.upload_wdg_layout.setSpacing(6)
        self.upload_wdg_layout.setContentsMargins(0, 0, 0, 0)

        self.upload_wdg_layout.addWidget(self.browse_button, 0, 0, 1, 1)
        self.upload_wdg_layout.addWidget(self.text_edit, 0, 1, 1, 1)
        self.upload_wdg_layout.addWidget(self.drop_plate, 1, 0, 1, 2)

    def create_edit(self):
        self.text_edit = QtGui.QLineEdit()

    def create_drop_plate(self):
        self.drop_plate = QtGui.QWidget()
        self.drop_plate.setMinimumWidth(200)
        self.drop_plate.setMinimumHeight(50)
        self.drop_plate_layout = QtGui.QHBoxLayout()
        self.drop_plate_layout.setSpacing(0)
        self.drop_plate_layout.setContentsMargins(0, 0, 0, 0)
        self.drop_plate.setLayout(self.drop_plate_layout)
        self.drop_plate_label = QtGui.QLabel('DROP HERE')
        self.drop_plate_label.setAlignment(QtCore.Qt.AlignCenter)
        self.drop_plate_layout.addWidget(self.drop_plate_label)
        self.drop_plate_label.setStyleSheet('QLabel{border: 1px solid gray;border-radius: 4px;background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 0, 0, 32), stop:1 rgba(0, 0, 0, 0));}')

    def create_browse_button(self):
        self.browse_button = QtGui.QPushButton('Browse')


class QTacticTextWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_text_edit()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()
        self.set_control_widget(self.text_edit)

    def get_data(self):
        return unicode(self.text_edit.text())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        values = self.tactic_widget.get_values()
        if values:
            self.text_edit.setText(values[0])

    def create_text_edit(self):
        self.text_edit = QtGui.QLineEdit()


class QTacticTextAreaWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        self.create_text_area()

        self.set_title(self.tactic_widget.get_title())
        self.fill_default_values()
        self.set_control_widget(self.text_area)

    def get_data(self):
        return unicode(self.text_area.toPlainText())

    def get_column(self):
        return self.tactic_widget.get_name()

    def fill_default_values(self):
        values = self.tactic_widget.get_values()
        if values:
            self.text_area.setText(values[0])

    def create_text_area(self):
        self.text_area = QtGui.QTextEdit()


class QTacticCurrentCheckboxWdg(QtGui.QWidget, QTacticBasicInputWdg):
    def __init__(self, tactic_widget, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.init_ui()
        self.tactic_widget = tactic_widget

        # self.create_text_area()

        self.set_title(self.tactic_widget.get_title())
        # self.fill_default_values()
        # self.set_control_widget(self.text_area)

    def get_data(self):
        return 0

    def get_column(self):
        return self.tactic_widget.get_name()
    #
    # def fill_default_values(self):
    #     values = self.tactic_widget.get_values()
    #     if values:
    #         self.text_area.setText(values[0])
    #
    # def create_text_area(self):
    #     self.text_area = QtGui.QTextEdit()
