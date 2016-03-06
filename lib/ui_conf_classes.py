# ui_conf_classes.py
# Configuration window classes

import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import environment as env
import lib.ui.ui_conf as ui_conf
import tactic_classes as tc
if env.Mode().get == 'maya':
    import ui_maya_dock
    import maya.cmds as cmds

reload(ui_conf)


class Ui_configuration_dialogWidget(QtGui.QDialog, ui_conf.Ui_configuration_dialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.tactic_project = env.Env().get_project()

        self.setupUi(self)

        self.readSettings()

        self.tab_actions()

    def tab_actions(self):
        """
        Actions for the configuration tab
        """

        self.buttonBox.button(QtGui.QDialogButtonBox.Close).clicked.connect(lambda: self.close())

        self.buttonBox.button(QtGui.QDialogButtonBox.Reset).clicked.connect(lambda: self.close())

        self.buttonBox.button(QtGui.QDialogButtonBox.Save).clicked.connect(
            lambda: self.perform_save())

        self.getProjectsButton.clicked.connect(lambda: self.getProjectsList(self.tactic_project))
        self.currentProjectComboBox.currentIndexChanged.connect(
            lambda: self.getProjectsInfo(self.currentProjectComboBox.currentText()))

    def perform_save(self):
        """
        Scope all Edits for save
        :return:
        """
        if self.projectInfoCodeLabel.text():
            env.Env().set_project(self.projectInfoCodeLabel.text())
            self.restart()

    def getProjectsInfo(self, title):
        """
        Getting info from user created Tactic Projects
        :param title:
        """
        search_type = 'sthpw/project'
        filters = [('title', title)]
        assets = tc.server_query(search_type, filters)
        for asset in assets:
            asset_get = asset.get
            if asset_get('title'):
                self.projectInfoTitleLabel.setText(asset_get('title'))
                self.projectInfoCodeLabel.setText(asset_get('code'))
                self.tactic_project = asset_get('code')
                self.projectInfoStatusLabel.setText(asset_get('status'))
                self.projectInfoLastUpdLabel.setText(asset_get('last_db_update'))

    def getProjectsList(self, current_project):
        """
        Getting all user created Projects from Tactic
        :param current_project:
        """
        self.currentProjectComboBox.clear()
        search_type = 'sthpw/project'
        filters = []
        assets = tc.server_query(search_type, filters)
        for asset in assets:
            asset_get = asset.get
            if asset_get('title'):
                self.tactic_project = asset_get('code')
                if current_project == self.tactic_project:
                    current_project_title = asset_get('title')
                self.currentProjectComboBox.addItem(asset_get('title'))
        self.currentProjectComboBox.setCurrentIndex(self.currentProjectComboBox.findText(current_project_title))

    def restart(self):
        ask_restart = QtGui.QMessageBox.question(self, 'Restart TACTIC Handler?',
                                                 "<p>Looks like You have made changes which require restarting</p>"
                                                 "<p>Perform restart?</p>",
                                                 QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if ask_restart == QtGui.QMessageBox.Yes:
            self.close()
            # if env.Mode().get == 'maya':
            #     reload(ui_maya_dock)
            #     ui_maya_dock.startup(restart=True)
            # else:
            self.parent().close()
            self.parent().create_ui_main()
            self.parent().show()

    def readSettings(self):
        """
        Reading Settings
        """
        self.userNameLineEdit.setText(env.Env().get_user())
        self.passwordLineEdit.setText(env.Env().get_user())
        self.tacticEnvLineEdit.setText(env.Env().get_data_dir())
        self.tacticAssetDirLineEdit.setText(env.Env().get_asset_dir())
        self.tacticInstallDirLineEdit.setText(env.Env().get_install_dir())
        self.tacticServerLineEdit.setText(env.Env().get_server())
        if env.Mode().get == 'maya':
            self.currentWorkdirLineEdit.setText(cmds.workspace(q=True, dir=True))

        self.settings.beginGroup(env.Mode().get + '/ui_conf')
        self.configToolBox.setCurrentIndex(self.settings.value('configToolBox', 0))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(env.Mode().get + '/ui_conf')
        self.settings.setValue('configToolBox', self.configToolBox.currentIndex())
        print('Done ui_conf settings write')
        self.settings.endGroup()

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()
