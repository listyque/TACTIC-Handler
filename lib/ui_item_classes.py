# module Tree widget item Classes
# file ui_item_classes.py
# Main Item for TreeWidget

import PySide.QtGui as QtGui
import environment as env
import global_functions as gf
import lib.ui.ui_item
import lib.ui.ui_item_process
import lib.ui.ui_item_snapshot
import ui_tasks_classes as tasks_widget
import ui_notes_classes as notes_widget

reload(lib.ui.ui_item)
reload(lib.ui.ui_item_process)
reload(lib.ui.ui_item_snapshot)
reload(tasks_widget)
reload(notes_widget)


class Ui_itemWidget(QtGui.QWidget, lib.ui.ui_item.Ui_item):
    def __init__(self, row, sobject, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'sobject'
        self.relates_to = parent.relates_to
        self.row = row
        self.tree_item = tree_item
        # self.item_info = {}
        self.sobject = sobject

        self.fileNameLabel.setText(self.sobject.info['name'])
        self.commentLabel.setText(gf.to_plain_text(self.sobject.info['description']))
        # TODO correct date time
        # dateLabel = QtCore.QDateTime.fromString(self.sobject.info['timestamp'], 'yyyy-MM-dd HH:mm:ss')
        self.dateLabel.setText(self.sobject.info['timestamp'])

        self.tasksToolButton.clicked.connect(lambda: self.create_tasks_window())
        self.childrenToolButton.clicked.connect(lambda: self.prnt())

        # fill item info
        # self.item_info['description'] = self.sobject.info['description']

    def prnt(self):
        # shot_tab = env.Inst().ui_check_tree[self.relates_to]['cgshort/shot']
        print(env.Inst().ui_check_tabs[self.relates_to].sObjTabWidget.count())
        tab_wdg = env.Inst().ui_check_tabs[self.relates_to].sObjTabWidget
        for i in range(tab_wdg.count()):
            if tab_wdg.widget(i).objectName() == 'cgshort/shot':
                tab_wdg.setCurrentIndex(i)

        tree_wdg = tab_wdg.currentWidget()

        tree_wdg.searchLineEdit.setText('SCENES00001')
        tree_wdg.searchOptionsGroupBox.searchParentCodeRadioButton.setChecked(True)
        tree_wdg.add_items_to_results('SCENES00001')

    def check_for_children(self):
        pass

    def create_tasks_window(self):
        try:
            self.tasks_widget.show()
        except:
            # print(self.item_info)
            # current_tab_context = env.Inst().ui_checkout_tree[self.sobject.info['pipeline_code']].context_items
            # print(env.Inst().ui_checkout_tree)
            self.tasks_widget = tasks_widget.Ui_tasksWidgetMain(self.sobject, self)
            self.tasks_widget.show()

    def get_context(self, process=False, custom=None):
        return ''

    def get_skey(self, skey=False, only=False, parent=False):
        """skey://cgshort/props?project=the_pirate&code=PROPS00001"""
        if parent or only:
            return self.sobject.info['__search_key__']
        if skey:
            return 'skey://' + self.sobject.info['__search_key__']

    def get_description(self):
        return self.sobject.info['description']

    def update_description(self, new_description):
        self.sobject.info['description'] = new_description
        self.commentLabel.setText(new_description)


class Ui_processItemWidget(QtGui.QWidget, lib.ui.ui_item_process.Ui_processItem):
    def __init__(self, row, process, sobject, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'process'
        self.tree_item = tree_item
        # print(tree_item.text(0))
        # self.item_info = {}
        self.sobject = sobject
        self.process = process

        self.row = row

        self.notesToolButton.clicked.connect(lambda: self.create_notes_widget())

        # self.item_info[
        #     'description'] = 'This is {0} process item, there is no description, better click on Notes button'.format(
        #     self.process)

    def create_notes_widget(self):
        self.note_widget = notes_widget.Ui_notesOwnWidget(self)
        self.note_widget.setWindowTitle(
            'Notes for: {0}, with process: {1}'.format(self.sobject.info['name'], self.process))
        self.sobject.info['process'] = self.process
        self.sobject.info['context'] = self.process
        # print(self.sobject.info)
        if self.sobject:
            self.note_widget.ui_notes.task_item = self.sobject
            self.note_widget.ui_notes.fill_notes()
        self.note_widget.show()
        self.note_widget.ui_notes.conversationScrollArea.verticalScrollBar().setValue(self.note_widget.ui_notes.conversationScrollArea.verticalScrollBar().maximum())

    def prnt(self):
        # print(str(self.item_index))
        # print(self.tree_item.parent().setExpanded(False))
        print(self.sobject.process)
        self.sobject.update_snapshots()
        print(self.sobject.process)

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return '{0}/{1}'.format(self.process, custom)
            else:
                return self.process
                # else:
                #     return ''

    def get_description(self):
        return 'No Description for this item "{0}"'.format(self.process)

    def get_skey(self, skey=False, only=False, parent=False):
        if parent or only:
            return self.sobject.info['__search_key__']
        if skey:
            return 'skey://' + self.sobject.info['__search_key__']


class Ui_snapshotItemWidget(QtGui.QWidget, lib.ui.ui_item_snapshot.Ui_snapshotItem):
    def __init__(self, row, snapshot, sobject, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'snapshot'
        self.tree_item = tree_item
        # self.item_info = {}
        self.sobject = sobject

        self.snapshot = None
        self.row = row
        self.files = {}

        if snapshot:
            self.snapshot = snapshot.values()[0].snapshot
            self.files = snapshot.values()[0].files
        hidden = ['icon', 'web', 'playblast']

        if self.snapshot:
            self.commentLabel.setText(gf.to_plain_text(self.snapshot['description'], 80))
            self.dateLabel.setText(self.snapshot['timestamp'])
            self.authorLabel.setText(self.snapshot['login'] + ':')
            for key, fl in self.files.iteritems():
                if key not in hidden:
                    self.fileNameLabel.setText(fl[0]['file_name'])
                    self.sizeLabel.setText(gf.sizes(fl[0]['st_size']))
        else:
            self.fileNameLabel.setText('Versionless not found')
            self.commentLabel.setText('Check this snapshot, and update versionless')
            self.dateLabel.deleteLater()
            self.sizeLabel.deleteLater()
            self.authorLabel.deleteLater()

        # if snapshot:
        #     self.item_info = self.snapshot

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return '{0}/{1}'.format(self.snapshot['process'], custom)
            else:
                return self.snapshot['process']
        else:
            context = self.snapshot['context'].split('/')[-1]
            if context == self.snapshot['process']:
                context = ''
            return context

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
            return 'No skey for this item!'

    def get_description(self):
        if self.snapshot:
            return self.snapshot['description']
        else:
            return 'No Description for this item!'

    def update_description(self, new_description):
        self.snapshot['description'] = new_description
        self.commentLabel.setText(new_description)
