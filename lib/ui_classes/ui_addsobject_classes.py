# module Adding sObject Classes
# file ui_addsobject_classes.py
# Adding new sObject window

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import lib.ui.misc.ui_addsobject as ui_addsobject
# import lib.environment as env
from lib.environment import env_mode
import lib.tactic_classes as tc

reload(ui_addsobject)


class Ui_addSObjectFormWidget(QtGui.QDialog, ui_addsobject.Ui_addSObjectForm):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.setupUi(self)
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

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(env_mode.get_mode() + '/ui_addsobject')
        self.setGeometry(self.settings.value('geometry', QtCore.QRect(500, 400, 500, 350)))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env_mode.get_mode() + '/ui_addsobject')
        self.settings.setValue('geometry', self.geometry())
        print('Done ui_addsobject settings write')
        self.settings.endGroup()

    def closeEvent(self, event):
        # event.ignore()
        self.writeSettings()
        event.accept()
