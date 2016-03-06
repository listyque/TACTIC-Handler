# file ui_tasks_classes.py
# Main Window of tasks

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import lib.ui.ui_tasks as ui_tasks
import ui_richedit_classes as richedit_widget
import ui_notes_classes as notes_widget
import ui_item_task_classes as task_item_widget
import tactic_classes as tc
import global_functions as gf

reload(ui_tasks)
reload(richedit_widget)
reload(notes_widget)
reload(task_item_widget)


class Ui_tasksWidgetMain(QtGui.QMainWindow):
    def __init__(self, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.task_widget = Ui_tasksWidget(sobject, self)
        self.setWindowTitle('Tasks for: ' + sobject.info['name'])
        self.setCentralWidget(self.task_widget)
        self.setContentsMargins(0, 4, 0, 0)
        self.statusBar()

    def closeEvent(self, event):
        print('Save Ui_tasksWidgetMain')
        self.task_widget.close()
        self.task_widget.deleteLater()
        self.close()
        self.deleteLater()
        event.accept()


class Ui_tasksWidget(QtGui.QWidget, ui_tasks.Ui_tasks):
    def __init__(self, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.dock_widget = None

        self.sobject = sobject

        # Query to get all task for current sobject
        self.sobject.get_tasks()

        self.users = tc.users_query()
        self.priority = tc.task_priority_query(self.sobject.info['__search_key__'])
        self.task_process = tc.task_process_query(self.sobject.info['__search_key__'])
        # print(self.task_process)

        self.initial_fill_info()

        self.ui_richedit = richedit_widget.Ui_richeditWidget(self.descriptionTextEdit)
        self.editorLayout.addWidget(self.ui_richedit)

        self.add_process_items()

        self.ui_actions()

    def ui_actions(self):
        self.processTreeWidget.clicked.connect(self.fill_tasks_info)
        self.showNotesButton.clicked.connect(self.create_notes_widget)
        self.priorityComboBox.currentIndexChanged.connect(self.priority_combo_color)
        self.statusComboBox.currentIndexChanged.connect(self.status_combo_color)

        self.skeyLineEdit_actions()

    def click_on_skeyLineEdit(self, event):
        self.skeyLineEdit.selectAll()

    def skeyLineEdit_actions(self):
        self.skeyLineEdit.mousePressEvent = self.click_on_skeyLineEdit
        self.skeyLineEdit.returnPressed.connect(lambda: tc.parce_skey(self.skeyLineEdit.text()))

    def fill_status(self):
        status_combo_box = self.statusComboBox.model()
        for value, color in zip(self.task_process['process'], self.task_process['color']):
            item = QtGui.QStandardItem(u'{0}'.format(value))
            sc = gf.hex_to_rgb(color, tuple=True)
            sc_item = QtGui.QColor(sc[0], sc[1], sc[2], 128)
            item.setBackground(sc_item)
            item.setData(sc_item, 1)
            item.setData(value, 2)
            status_combo_box.appendRow(item)

    def status_combo_color(self):
        item_color = self.statusComboBox.itemData(self.statusComboBox.currentIndex(), 1)
        if item_color:
            pc = item_color.toTuple()
            self.statusComboBox.setStyleSheet('QComboBox {background: ' +
                                              'rgba({0}, {1}, {2}, {3})'.format(pc[0], pc[1], pc[2], 192) +
                                              ';}')
        else:
            self.priorityComboBox.setStyleSheet('')

    def fill_priority(self):
        # priority combo box with colors
        priority_combo_box = self.priorityComboBox.model()
        step = len(self.priority) - 1
        int_range = 255 / step * step
        r = range(0, int_range, 255 / step)
        g = range(0, int_range, 255 / step)
        b = 0
        a = 64
        r.reverse()
        pc = []
        for i in range(step):
            color = r[i], g[i], b, a
            pc.append(color)
        for i, (label, value) in enumerate(self.priority):
            item = QtGui.QStandardItem(u'{0}, {1}'.format(label, value))
            color = QtGui.QColor(pc[i - 1][0], pc[i - 1][1], pc[i - 1][2], pc[i - 1][3])
            if i > 0:
                item.setBackground(color)
                item.setData(color, 1)
            priority_combo_box.appendRow(item)

    def priority_combo_color(self):
        item_color = self.priorityComboBox.itemData(self.priorityComboBox.currentIndex(), 1)
        if item_color:
            pc = item_color.toTuple()
            self.priorityComboBox.setStyleSheet('QComboBox {background: ' +
                                                'rgba({0}, {1}, {2}, {3})'.format(pc[0], pc[1], pc[2], 192) +
                                                ';}')
        else:
            self.priorityComboBox.setStyleSheet('')

    def initial_fill_info(self):

        self.fill_priority()
        self.fill_status()
        current_datetime = QtCore.QDateTime.currentDateTime()
        self.startedDateTimeEdit.setDateTime(current_datetime)
        self.endDateTimeEdit.setDateTime(current_datetime)

        for user in self.users.itervalues():
            self.assignedToComboBox.addItem(u'{last_name} {first_name}, {login}'.format(**user))
            self.superviserComboBox.addItem(u'{last_name} {first_name}, {login}'.format(**user))

    def fill_tasks_info(self):
        current_item = self.processTreeWidget.currentItem().data(0, QtCore.Qt.UserRole)
        if current_item:
            self.descriptionTextEdit.setText(current_item.info['description'])
            for i, user in enumerate(self.users.itervalues()):

                if current_item.info['assigned'] == user['login']:
                    self.assignedToComboBox.setCurrentIndex(i)
                if not current_item.info['assigned']:
                    self.assignedToComboBox.setCurrentIndex(0)
                    self.assignedToComboBox.setEditText('Not Assigned')

                if current_item.info['supervisor'] == user['login']:
                    self.superviserComboBox.setCurrentIndex(i)
                if not current_item.info['supervisor']:
                    self.superviserComboBox.setCurrentIndex(0)
                    self.superviserComboBox.setEditText('Not Assigned')

            if current_item.info['priority']:
                self.priorityComboBox.setCurrentIndex(int(current_item.info['priority']))
            else:
                self.priorityComboBox.setCurrentIndex(0)

            if current_item.info['status']:
                for i, status in enumerate(self.task_process['process']):
                    if current_item.info['status'] == status:
                        self.statusComboBox.setCurrentIndex(i)

            start_date = QtCore.QDateTime.fromString(current_item.info['bid_start_date'], 'yyyy-MM-dd HH:mm:ss')
            end_date = QtCore.QDateTime.fromString(current_item.info['bid_end_date'], 'yyyy-MM-dd HH:mm:ss')
            self.startedDateTimeEdit.setDateTime(start_date)
            self.endDateTimeEdit.setDateTime(end_date)
            self.skeyLineEdit.setText('skey://' + current_item.info['__search_key__'])
            self.contextLineEdit.setText(current_item.info['context'])
            if self.dock_widget:
                self.ui_notes.task_item = current_item
                self.ui_notes.fill_notes()

            show_notes_text = '{0} ({1})'.format('Show Task Notes', str(10))
            print(show_notes_text)
            self.showNotesButton.setText(show_notes_text)

    def add_process_items(self):
        # print(self.sobject.tasks)
        # Top level, process of tasks
        for process in self.sobject.all_process:

            self.top_item = QtGui.QTreeWidgetItem()
            self.top_item.setText(0, process)
            self.top_item_widget = task_item_widget.Ui_taskItemWidget(self.top_item, self)
            self.processTreeWidget.addTopLevelItem(self.top_item)
            self.processTreeWidget.setItemWidget(self.top_item, 0, self.top_item_widget)

            # Second level, contexts of tasks
            if self.sobject.tasks.get(process):
                for context, task in self.sobject.tasks[process].contexts.iteritems():
                    self.child_item = QtGui.QTreeWidgetItem()
                    self.child_item.setText(0, context)
                    self.top_item.addChild(self.child_item)
                    self.top_item.setExpanded(True)

                    # Third level, Tasks items
                    for sub, item in self.sobject.tasks[process].contexts[context].items.iteritems():
                        self.sub_item = QtGui.QTreeWidgetItem()
                        self.sub_item.setData(0, QtCore.Qt.UserRole, item)
                        # self.sub_item.setText(0, sub)
                        self.sub_item_widget = task_item_widget.Ui_taskItemDetailWidget(self)
                        self.child_item.addChild(self.sub_item)
                        self.processTreeWidget.setItemWidget(self.sub_item, 0, self.sub_item_widget)
                        # self.child_item.setExpanded(True)
                        # print(context)
                        # print(sub)
                        # print(item)

    def create_notes_widget(self):
        current_item = self.processTreeWidget.currentItem().data(0, QtCore.Qt.UserRole)
        try:
            self.dock_widget.show()
            self.dock_widget.raise_()
        except:
            self.dock_widget = QtGui.QDockWidget()
            self.dock_widget.setObjectName('notes_dock')
            self.dock_widget.setWindowTitle('Notes')
            self.dock_widget.setMinimumWidth(500)
            self.ui_notes = notes_widget.Ui_notesWidget()
            if current_item:
                self.ui_notes.task_item = current_item
                self.ui_notes.fill_notes()
            self.dock_widget.setWidget(self.ui_notes)
            self.parent().addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)
            self.dock_widget.show()
            self.dock_widget.raise_()

            self.ui_notes.conversationScrollArea.verticalScrollBar().setValue(
                self.ui_notes.conversationScrollArea.verticalScrollBar().maximum())

    def closeEvent(self, event):
        try:
            self.dock_widget.close()
            self.dock_widget.deleteLater()
            self.ui_notes.close()
        except:
            pass
        # self.ui_notes.close()
        print('Save Ui_tasksWidget')
        event.accept()
