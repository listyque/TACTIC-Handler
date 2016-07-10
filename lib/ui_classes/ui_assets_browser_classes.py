# file ui_assets_browser_classes.py
# Assets Browser

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from lib.side.flowlayout import ScrollingFlowWidget
from pprint import pprint
import lib.tactic_classes as tc
import lib.environment as env
import lib.ui.ui_assets_browser as ui_assets_browser
import lib.ui.ui_sobject as ui_sobject
import lib.ui.ui_sobject_info as ui_sobject_info
import ui_tasks_classes
import ui_addsobject_classes as addsobject_widget
import ui_icons_classes as icons_widget

reload(ui_assets_browser)


class Ui_sobjectInfoWidget(QtGui.QMainWindow, ui_sobject_info.Ui_sobjectInfo):
    def __init__(self, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        # self.statusBar()

        self.setupUi(self)

        self.sobject = sobject

        self.create_tasks_widget()
        self.create_edit_widget()

    def create_tasks_widget(self):
        tasks_wdg = ui_tasks_classes.Ui_tasksWidgetMain(self.sobject, self)
        tasks_wdg.statusBar().hide()

        self.tasksLayout.addWidget(tasks_wdg)

    def create_edit_widget(self):
        edit_wdg = addsobject_widget.Ui_addSObjectFormWidget(self)
        edit_wdg.setSizeGripEnabled(False)
        self.editLayout.addWidget(edit_wdg)


class Ui_sobjectWidget(QtGui.QGroupBox, ui_sobject.Ui_sobjectGroupBox):
    def __init__(self, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.sobject = sobject

        self.picLabel.mousePressEvent = self.mousePressEvent
        self.picLabel.mouseReleaseEvent = self.mouseReleaseEvent
        self.picLabel.mouseDoubleClickEvent = self.mouseDoubleClickEvent

    def mouseDoubleClickEvent(self, *args, **kwargs):
        self.mousePressEvent()
        self.sobject_info = Ui_sobjectInfoWidget(self.sobject, self)
        self.sobject_info.show()

    def mousePressEvent(self, *args, **kwargs):
        self.setStyleSheet("""
        #sobjectGroupBox {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(128, 128, 128, 150), stop: 1 rgba(175, 175, 175, 60));
            border: 1px solid rgb(192, 192, 192);
            border-radius: 2px;
            padding: 0px 0px;
            margin-top: 5ex;
        }

        #sobjectGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: transparent;
        }
        """)

    def mouseReleaseEvent(self, *args, **kwargs):
        self.setStyleSheet("""
        #sobjectGroupBox {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 150), stop: 1 rgba(128, 128, 128, 30));
            border: 1px solid rgb(150, 150, 150);
            border-radius: 2px;
            padding: 0px 0px;
            margin-top: 5ex;
        }

        #sobjectGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: transparent;
        }
        """)

    def leaveEvent(self, *args, **kwargs):
        self.setStyleSheet("""
        #sobjectGroupBox {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 75), stop: 1 rgba(0, 0, 0, 30));
            border: 1px solid rgb(96, 96, 96);
            border-radius: 2px;
            padding: 0px 0px;
            margin-top: 5ex;
        }

        #sobjectGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: transparent;
        }
        """)

    def enterEvent(self, *args, **kwargs):
        self.setStyleSheet("""
        #sobjectGroupBox {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 150), stop: 1 rgba(128, 128, 128, 30));
            border: 1px solid rgb(150, 150, 150);
            border-radius: 2px;
            padding: 0px 0px;
            margin-top: 5ex;
        }

        #sobjectGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: transparent;
        }
        """)


class Ui_assetsBrowserWidget(QtGui.QWidget, ui_assets_browser.Ui_assetsBrowser):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.relates_to = 'assets_browser'

        self.asstes_tree = None
        self.dyn_list = []
        self.tabs_items, self.context_items = self.query_tabs()
        self.toggle = False
        self.current_stype = None

        self.create_scroll_layout()

        self.controls_actions()

        self.create_search_group_box()

        # self.subscriptions_query()

    def create_search_group_box(self):
        self.searchOptionsGroupBox = icons_widget.Ui_searchOptionsWidget(self)
        self.searchOptionsLayout.addWidget(self.searchOptionsGroupBox)
        self.searchOptionsGroupBox.miscGroupBox.hide()

    def searchLineDoubleClick(self, event):
        if not self.toggle:
            self.toggle = True
            self.searchOptionsGroupBox.setMinimumHeight(95)
        else:
            self.toggle = False
            self.searchOptionsGroupBox.setMinimumHeight(0)

    def searchLineSingleClick(self, event):
        self.searchLineEdit.selectAll()

    def controls_actions(self):
        self.zoomSpinBox.valueChanged.connect(self.sobject_widget_zoom)
        self.assetsTreeWidget.itemClicked.connect(self.load_results)

        self.searchLineEdit.mouseDoubleClickEvent = self.searchLineDoubleClick
        self.searchLineEdit.mousePressEvent = self.searchLineSingleClick

    def sobject_widget_zoom(self, value):
        for sobj_widget in self.sobjects_widgets:
            sobj_widget.setMinimumWidth(150 * value / 100)
            sobj_widget.setMinimumHeight(150 * value / 100)
            image_size = 140 * self.zoomSpinBox.value() / 100
            if sobj_widget.picLabel.text() != 'No preview':
                old_path_split = sobj_widget.picLabel.text().split('=')
                old_path_join = '{0}={1}='.format(*old_path_split) + '"{0}"'.format(image_size)
                sobj_widget.picLabel.setText(old_path_join)

    def dynamic_query(self, limit=0, offset=0):

        filters = []
        order_bys = ['timestamp desc']
        columns = []
        sobjects_list = tc.server_start().query(self.current_stype, filters, columns, order_bys, limit=limit, offset=offset)
        print self.current_stype
        print sobjects_list
        print filters
        all_process = self.context_items[self.current_stype]
        sobjects = tc.get_sobjects(all_process, sobjects_list)

        return sobjects

    def subscriptions_query(self):
        import collections

        stub = tc.server_start()

        all_sobjects = tc.query_tab_names(True)

        filters = [('login', env.Env.get_user()), ('project_code', env.Env.get_project())]

        subscriptions = stub.query('sthpw/subscription', filters)

        spl = collections.defaultdict(list)

        for sub in subscriptions:
            split = stub.split_search_key(sub['message_code'])
            spl[split[0]].append(split[1])

        parents = collections.defaultdict(list)
        for key, values in spl.iteritems():
            parents[key.split('?')[0]] = \
                tc.get_sobjects(sobjects_list=stub.query(key, [('code', values)]), get_snapshots=False)

        pprint(all_sobjects)
        pprint(dict(parents))

        # print(stub.get_parent('cgshort/shot?project=the_pirate&code=SHOT00001'))

        server = tc.server_start()
        expr = "@GET(cgshort/shot.cgshort/scenes.code)"
        result = server.eval(expr)
        pprint(result)
        pprint(stub.query('cgshort/shot', [('scenes_code', 'SCENES00001')]))

    def create_scroll_layout(self):
        self.scroller = ScrollingFlowWidget()
        self.scroller.setContentsMargins(20, 20, 20, 20)
        self.scroller.setSpacing(12)
        self.scroller.wheelEvent = self.wheelEvent
        self.sobjectScrollLayout.addWidget(self.scroller)

    def fill_results(self):
        self.dyn_list = self.dynamic_query(self.limitSpinBox.value(), self.scroller.flowLayout.count())
        for i in range(len(self.dyn_list)):
            QtGui.qApp.processEvents()
            self.sobj_widget = Ui_sobjectWidget(self.dyn_list.values()[i], self)
            self.sobj_widget.setMinimumWidth(150 * self.zoomSpinBox.value() / 100)
            self.sobj_widget.setMinimumHeight(150 * self.zoomSpinBox.value() / 100)
            image_size = 140 * self.zoomSpinBox.value() / 100

            effect = QtGui.QGraphicsDropShadowEffect(self.assetsTreeWidget)
            effect.setOffset(3, 3)
            effect.setColor(QtGui.QColor(0, 0, 0, 160))
            effect.setBlurRadius(30)

            self.sobj_widget.setGraphicsEffect(effect)
            self.sobj_widget.setTitle(self.dyn_list.values()[i].info['name'])
            try:
                web_file = self.dyn_list.values()[i].process['icon'].contexts['icon'].versionless.values()[0].files['web']
                web_full_path = '{0}/{1}/{2}'.format(env.Env.get_asset_dir(), web_file[0]['relative_dir'], web_file[0]['file_name'])
                self.sobj_widget.picLabel.setText("<img src=\"{0}\" width=\"{1}\" ".format(web_full_path, image_size))
            except:
                self.sobj_widget.picLabel.setText('No preview')

            self.scroller.addWidget(self.sobj_widget)
            self.sobjects_widgets.append(self.sobj_widget)

    def wheelEvent(self, QWheelEvent):
        if QWheelEvent.delta() < 0 and self.current_stype:
            self.fill_results()

    def create_assets_tree(self):
        self.asstes_tree = tc.query_assets_names()
        for name, value in self.asstes_tree.iteritems():
            self.top_item = QtGui.QTreeWidgetItem()
            if not name:
                name = 'Untyped'
            self.top_item.setText(0, name.capitalize())
            self.assetsTreeWidget.addTopLevelItem(self.top_item)
            for item in value:
                # print(item)
                self.child_item = QtGui.QTreeWidgetItem()
                if item['title']:
                    item_title = item['title'].capitalize()
                else:
                    item_title = 'Unnamed'
                self.child_item.setText(0, item_title)
                self.child_item.setData(0, QtCore.Qt.UserRole, item)
                self.top_item.addChild(self.child_item)

    def load_results(self, position):
        item = self.assetsTreeWidget.currentItem()
        indexes = self.assetsTreeWidget.selectedIndexes()

        if len(indexes) > 0:
            level = 0
            index = indexes[0]
            while index.parent().isValid():
                index = index.parent()
                level += 1

        if level > 0:
            data = item.data(0, QtCore.Qt.UserRole)
            self.sobjects_widgets = []
            self.current_stype = data['code']
            self.scroller.close()
            self.scroller.deleteLater()
            self.create_scroll_layout()
            self.fill_results()

            # print(item.data(0, QtCore.Qt.UserRole))

    def showEvent(self, *args, **kwargs):
        if self.assetsTreeWidget.topLevelItemCount() == 0:
            self.create_assets_tree()

    @staticmethod
    def query_tabs():
        tab_names = tc.query_tab_names()
        return tab_names, tc.context_query(tab_names['codes'])
