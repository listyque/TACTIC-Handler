from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

from thlib.environment import env_mode, env_inst
import thlib.update_functions as uf
import thlib.ui.misc.ui_create_update as ui_create_update
import thlib.ui.misc.ui_update as ui_update



class Ui_createUpdateDialog(QtGui.QDialog, ui_create_update.Ui_createUpdateDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        current_datetime = QtCore.QDateTime.currentDateTime()
        self.dateEdit.setDateTime(current_datetime)
        self.initial_fill_version_spinbox()

        self.controls_actions()

    def initial_fill_version_spinbox(self):
        version_dict = uf.get_current_version()
        self.majorSpinBox.setValue(int(version_dict['major']))
        self.minorSpinBox.setValue(int(version_dict['minor']))
        self.buildSpinBox.setValue(int(version_dict['build']))
        self.revisionSpinBox.setValue(int(version_dict['revision']))

    def controls_actions(self):
        self.createUpdatePushButton.clicked.connect(self.commit_update_to_json)

    def commit_update_to_json(self):
        args = self.majorSpinBox.text(),\
               self.minorSpinBox.text(),\
               self.buildSpinBox.text(),\
               self.revisionSpinBox.text()
        current_ver_dict = uf.get_version(*args)
        current_ver_str = uf.get_version(*args, string=True)
        data_dict = {
            'version': current_ver_dict,
            'date': self.dateEdit.text(),
            'changes': self.changesPlainTextEdit.toPlainText(),
            'misc': self.miscPlainTextEdit.toPlainText(),
            'remove_list': [],
            'update_archive': '{0}.zip'.format(current_ver_str)
        }
        uf.save_json_to_path('{0}/updates/{1}.json'.format(env_mode.get_current_path(), current_ver_str), data_dict)
        uf.create_updates_list()
        uf.save_current_version(current_ver_dict)
        uf.create_update_archive('{0}/updates/{1}.zip'.format(env_mode.get_current_path(), current_ver_str))
        self.close()

    def create_tar_gz_archive(self):
        pass


class Ui_updateDialog(QtGui.QDialog, ui_update.Ui_updateDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        # Disabled until it will be needed
        #uf.get_updates_from_server()

        self.updates = uf.get_info_from_updates_folder()

        self.last_version = None
        self.current_version = uf.get_current_version()

        self.load_local_updates()
        self.check_current_version()

        self.controls_actions()

        self.commitPushButton.setHidden(True)

    def load_local_updates(self):

        sort_list = []
        for update in self.updates:
            update_get = update.get
            item = QtGui.QTreeWidgetItem()
            sort_list.append(uf.get_version(sort_sum=True, **update_get('version')))
            # print(uf.get_version(string=True, **update_get('version')))
            # print(uf.get_version(sort_sum=True, **update_get('version')))

            item.setText(0, uf.get_version(string=True, **update_get('version')).replace('_', '.'))
            item.setText(1, update_get('date'))
            item.setText(2, update_get('changes'))
            item.setText(3, update_get('misc'))
            self.versionsTreeWidget.addTopLevelItem(item)
        if self.updates:
            self.last_version = self.updates[-1].get('version')

        # print(sorted(sort_list))
        self.versionsTreeWidget.sortByColumn(3, QtCore.Qt.DescendingOrder)
        self.versionsTreeWidget.scrollToBottom()

    def check_current_version(self):
        current_version = uf.get_version(string=True, **self.current_version)
        if self.last_version:
            last_version = uf.get_version(string=True, **self.last_version)
        else:
            last_version = current_version

        if current_version == last_version:
            self.updateToLastPushButton.setEnabled(True)
            self.currentVersionlabel.setText('<span style=" color:#00ff00;">{0} (up to date)</span>'.format(
                current_version.replace('_', '.')))
        else:
            self.updateToLastPushButton.setEnabled(True)
            self.currentVersionlabel.setText('<span style=" color:#ff0000;">{0} (new version available)</span>'.format(
                current_version.replace('_', '.')))

    def controls_actions(self):
        self.commitPushButton.clicked.connect(self.create_new_update)
        self.updateToLastPushButton.clicked.connect(self.update_to_last_version)
        self.updateToSelectedPushButton.clicked.connect(self.update_to_selected_version)
        self.currentVersionlabel.mouseDoubleClickEvent = self.currentVersionlabel_double_click

    def currentVersionlabel_double_click(self, event):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ControlModifier:
            self.commitPushButton.setHidden(False)

    def update_to_last_version(self):
        # uf.save_current_version(self.last_version)
        # self.current_version = uf.get_current_version()
        # self.check_current_version()
        # archive_path = uf.get_update_archive_from_server(self.updates[-1].get('update_archive'))
        # archive_path = r'D:\APS\OneDrive\MEGAsync\TACTIC-handler\updates\0_4_7_9.zip'

        # uf.update_from_archive(archive_path)
        env_inst.ui_main.restart_for_update_ui_main()

    def update_to_selected_version(self):
        pass

    def create_new_update(self):
        self.create_new_update_dialog = Ui_createUpdateDialog(self)
        self.create_new_update_dialog.show()
