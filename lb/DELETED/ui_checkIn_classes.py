# ui_checkIn_classes.py
# Check in interface

import xml.etree.ElementTree as Et
import PySide.QtCore as QtCore
import PySide.QtGui as QtGui
import environment as env
import lib.ui.ui_checkIn as ui_checkin
import ui_addsobject_classes
import tactic_classes as tc

reload(ui_checkin)
reload(ui_addsobject_classes)


class Ui_checkInTabWidget(QtGui.QWidget, ui_checkin.Ui_checkIn):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings('TACTIC Handler', 'TACTIC Handling Tool')

        self.setupUi(self)

        self.createTabs()

        self.fillContextComboBox()

        self.tabActions()

        self.readSettings()

    def createTabs(self):
        """
        Create Tabs from maya-type sTypes
        """
        search_type = 'sthpw/search_object'
        filters = [('type', 'maya'), ('namespace', env.TACTIC_PROJECT)]
        assets = tc.server_query(search_type, filters)
        self.code = []
        for asset in assets:
            asset_get = asset.get
            title = asset_get('title')
            self.code.append(asset_get('code'))
            # print(self.code)
            self.checkInTabWidget.addTab(QtGui.QWidget(), title)
            # print(self.checkOutTabWidget.tabText(self.checkOutTabWidget.currentIndex()))

    def assetSearch(self, query):
        """
        Query for searching assets
        """
        search_type = self.tab_name
        filters = [('name', 'like', '%' + query + '%')]
        assets = tc.server_query(search_type, filters)

        search_type = 'sthpw/snapshot'
        # print(tc.server_start().query_snapshots('sthpw/pipeline?code=exam/props'))
        filters = [('process', ('Modeling', 'Texturing', 'Refs', 'Sculpt')), ('project_code', env.TACTIC_PROJECT),
                   ('search_code', 'PROPS00003')]
        print(filters)
        snapshots = tc.server_query(search_type, filters)
        print(snapshots)
        for snapshot in snapshots:
            snapshot_get = snapshot.get
            print(snapshot_get('description') + ' ' + snapshot_get('context'))

        if query != '':
            self.resultsTreeWidget.clear()
            for i in range(len(assets)):
                self.resultsTreeWidget.addTopLevelItem(QtGui.QTreeWidgetItem())
                self.resultsTreeWidget.topLevelItem(i).setText(0, assets[i].get('name'))
                for j in range(1000):
                    self.resultsTreeWidget.topLevelItem(i).addChild(QtGui.QTreeWidgetItem())
                    self.resultsTreeWidget.topLevelItem(i).child(j).setText(0,
                                                                               'child ' + str(j + 1) + '\nComment...')

    def fillContextComboBox(self):
        """
        Add elements to Context ComboBox
        """
        self.tab_name = self.code[self.checkInTabWidget.currentIndex()]
        self.contextComboBox.clear()
        self.contextComboBox.addItem('All')
        search_type = 'sthpw/pipeline?code=' + self.tab_name
        filters = [('search_type', self.tab_name)]
        assets = tc.server_query(search_type, filters)
        if assets:
            xml = assets[0].get('pipeline')
            root = Et.fromstring(xml)
            for process in root.iter('process'):
                if process.attrib['name']:
                    self.contextComboBox.addItem(process.attrib['name'])

    def get_snapshots(self):
        """
        Getting snapshots and all info of it
        """
        pass

    def add_new_sobject(self):
        """
        Open window for adding new sobject
        """
        self.add_sobject = ui_addsobject_classes.Ui_addSObjectFormWidget(self)
        self.add_sobject.nameLineEdit.setText(
            self.searchLineEdit.text()[0].title() + self.searchLineEdit.text()[1:])
        self.add_sobject.descriptionTextEdit.setPlainText(self.descriptionTextEdit.toPlainText())
        self.add_sobject.setWindowTitle(self.add_sobject.windowTitle() + self.tab_name)
        self.add_sobject.show()

    def tabActions(self):
        """
        Actions for the check in tab
        """
        self.searchLineEdit.returnPressed.connect(lambda: self.assetSearch(self.searchLineEdit.text()))
        self.checkInTabWidget.currentChanged.connect(lambda: self.fillContextComboBox())
        self.contextComboBox.activated.connect(lambda: self.assetSearch(self.searchLineEdit.text()))
        self.addNewtButton.clicked.connect(lambda: self.add_new_sobject())
        # self.saveDescriprionButton.clicked.connect(lambda: self.detachTab())

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup('ui_checkIn')
        # self.commentsSplitter.restoreState(self.settings.value('commentsSplitter'))
        self.checkInTabWidget.setCurrentIndex(self.settings.value('checkOutTabWidget', 0))
        self.searchLineEdit.setText(self.settings.value('searchLineEdit_text', ''))
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup('ui_checkIn')
        # self.settings.setValue('commentsSplitter', self.commentsSplitter.saveState())
        self.settings.setValue('checkOutTabWidget', self.checkInTabWidget.currentIndex())
        self.settings.setValue('searchLineEdit_text', self.searchLineEdit.text())
        print('Done ui_checkIn settings write')
        self.settings.endGroup()

    def closeEvent(self, event):
        # event.ignore()
        self.writeSettings()
        event.accept()
