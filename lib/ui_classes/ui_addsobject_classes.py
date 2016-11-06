# module Adding sObject Classes
# file ui_addsobject_classes.py
# Adding new sObject window

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import json
# import lib.environment as env
from lib.environment import env_mode, env_server
import lib.tactic_classes as tc
import lib.tactic_widgets as tw
import lib.tactic_query as tq
import lib.ui_classes.ui_tactic_widgets_classes as twc


# DEPRECATED
class Ui_addSObjectFormWidget(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        import lib.ui_classes.ui_tactic_widgets_classes as tc_cl

        self.b = tc_cl.QtTacticEditWidget(self)

        self.setupUi(self)

        self.gridLayout.addWidget(self.b)

        self.tab_name = None
        self.setSizeGripEnabled(True)

        self.window_actions()

        self.readSettings()

    def window_actions(self):
        self.cancelButton.clicked.connect(lambda: self.close())
        self.browseImageButton.clicked.connect(lambda: self.browse_for_preview())
        self.addNewButton.clicked.connect(lambda: self.add_item())

    def browse_for_preview(self):
        options = QtGui.QFileDialog.Options()
        options |= QtGui.QFileDialog.DontUseNativeDialog
        file_name, filter = QtGui.QFileDialog.getOpenFileName(self, 'Browse for Preview Image',
                                                              self.previewImageLineEdit.text(),
                                                              'All Images (*.jpg | *.jpeg | *.png);;'
                                                              'JPEG Files (*.jpg | *.jpeg);;'
                                                              'PNG Files (*.png)',
                                                              '', options)
        if file_name:
            self.previewImageLineEdit.setText(file_name)

    def add_item(self):
        """
        Adding s object item
        :return: None
        """
        image = self.previewImageLineEdit.text()
        name = self.nameLineEdit.text()
        description = self.descriptionTextEdit.toPlainText()
        keywords = self.keywordsTextEdit.toPlainText()
        if name:
            filters = [('name', name)]
            existing = tc.server_start().query(self.tab_name, filters)
            if existing:
                msb = QtGui.QMessageBox(QtGui.QMessageBox.Question, 'This Name already used!',
                                        "Do you want to use this name anyway?",
                                        QtGui.QMessageBox.NoButton, self)
                msb.addButton("Yes", QtGui.QMessageBox.YesRole)
                msb.addButton("No", QtGui.QMessageBox.NoRole)
                msb.exec_()
                reply = msb.buttonRole(msb.clickedButton())

                if reply == QtGui.QMessageBox.YesRole:
                    sobject = tc.create_sobject(name, description, keywords, self.tab_name)
                    if image:
                        snapshot = tc.create_snapshot(sobject['__search_key__'], 'icon')
                        tc.checkin_icon(snapshot['__search_key__'], image)
                    self.close()
                elif reply == QtGui.QMessageBox.NoRole:
                    pass
            else:
                sobject = tc.create_sobject(name, description, keywords, self.tab_name)
                if image:
                    snapshot = tc.create_snapshot(sobject['__search_key__'], 'icon')
                    tc.checkin_icon(snapshot['code'], image)
                self.close()


class Ui_addTacticSobjectWidget(QtGui.QDialog):
    def __init__(self, stype, item=None, view='insert', parent=None):
        super(self.__class__, self).__init__(parent=parent)
        #TODO get title from within
        self.settings = QtCore.QSettings('{0}/settings/{1}/{2}/{3}/main_ui_config.ini'.format(
            env_mode.get_current_path(),
            env_mode.get_node(),
            env_server.get_cur_srv_preset(),
            env_mode.get_mode()),
            QtCore.QSettings.IniFormat)

        self.parent_ui = parent

        self.item = item
        self.stype = stype
        self.search_type = self.stype.info.get('code')

        self.view = view
        if self.item:
            if self.item.type == 'sobject':
                skey = self.item.sobject.info['__search_key__']
            if self.item.type == 'snapshot':
                skey = self.item.snapshot['__search_key__']
        else:
            skey = None

        kwargs_edit = {
            'args': {
                'input_prefix': 'edit',
                'search_key': skey,
                'view': 'edit',
            },
            'search_type': self.search_type,
        }

        kwargs_insert = {
            'args': {
                'input_prefix': 'insert',
                'parent_key': '',
                'search_type': self.search_type,
                'view': 'insert',
            },
            'search_type': self.search_type,
        }

        if self.view == 'edit':
            kwargs = kwargs_edit
        else:
            kwargs = kwargs_insert

        code = tc.prepare_serverside_script(tq.query_EditWdg, kwargs, return_dict=True)

        result = tc.server_start().execute_python_script('', kwargs=code)

        result_dict = json.loads(result['info']['spt_ret_val'])

        input_widgets_list = []

        for widget_dict in result_dict['InputWidgets']:
            tactic_widget_name = tw.get_widget_name(widget_dict['class_name'], 'input')

            tactic_widget = getattr(tw, tactic_widget_name)
            qt_widget = getattr(twc, 'Q{0}'.format(tactic_widget_name))
            tactic_widget_instance = tactic_widget(options_dict=widget_dict)
            qt_widget_instance = qt_widget(tactic_widget=tactic_widget_instance)

            input_widgets_list.append(qt_widget_instance)

        tactic_edit_widget = tw.TacticEditWdg(result_dict['EditWdg'])

        self.edit_window = twc.QtTacticEditWidget(
            tactic_widget=tactic_edit_widget,
            qt_widgets=input_widgets_list,
            parent=self
        )

        self.grid_layout = QtGui.QGridLayout(self)

        self.grid_layout.addWidget(self.edit_window)

        self.setSizeGripEnabled(True)

        self.readSettings()

    def refresh_results(self):
        self.parent_ui.refresh_current_results()

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup('ui_main')
        self.setGeometry(self.settings.value('geometry', QtCore.QRect(500, 400, 500, 350)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup('ui_main')
        self.settings.setValue('geometry', self.geometry())
        self.settings.endGroup()

    def closeEvent(self, event):
        # event.ignore()
        self.writeSettings()
        event.accept()