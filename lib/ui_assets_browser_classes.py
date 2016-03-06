# file ui_assets_browser_classes.py
# Assets Browser

import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from lib.flowlayout import ScrollingFlowWidget
from pprint import pprint
import tactic_classes as tc
import lib.ui.ui_assets_browser as ui_assets_browser
import lib.ui.ui_sobject as ui_sobject
import environment as env

reload(ui_assets_browser)


class Ui_sobjectWidget(QtGui.QGroupBox, ui_sobject.Ui_sobjectGroupBox):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

    def leaveEvent(self, *args, **kwargs):
        self.setStyleSheet("""
        QGroupBox {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 75), stop: 1 rgba(0, 0, 0, 30));
            border: 1px solid rgb(96, 96, 96);
            border-radius: 2px;
            padding: 0px 0px;
            margin-top: 5ex;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
            background-color: transparent;
        }
        """)

    def enterEvent(self, *args, **kwargs):
        self.setStyleSheet("""
        QGroupBox {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(175, 175, 175, 150), stop: 1 rgba(128, 128, 128, 30));
            border: 1px solid rgb(150, 150, 150);
            border-radius: 2px;
            padding: 0px 0px;
            margin-top: 5ex;
        }

        QGroupBox::title {
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

        self.asstes_tree = None
        self.dyn_list = []
        self.current_stype = None

        self.create_scroll_layout()

        self.controls_actions()
        # self.subscriptions_query()

    def controls_actions(self):
        self.zoomSpinBox.valueChanged.connect(self.sobject_widget_zoom)
        self.assetsTreeWidget.itemClicked.connect(self.load_results)

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

        sobjects = tc.get_sobjects([], sobjects_list)

        return sobjects

    def subscriptions_query(self):
        import collections

        stub = tc.server_start()

        all_sobjects = tc.query_tab_names(True)

        filters = [('login', env.Env().get_user()), ('project_code', env.Env().get_project())]

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
            sobj_widget = Ui_sobjectWidget()
            sobj_widget.setMinimumWidth(150 * self.zoomSpinBox.value() / 100)
            sobj_widget.setMinimumHeight(150 * self.zoomSpinBox.value() / 100)
            image_size = 140 * self.zoomSpinBox.value() / 100

            effect = QtGui.QGraphicsDropShadowEffect(self.assetsTreeWidget)
            effect.setOffset(3, 3)
            effect.setColor(QtGui.QColor(0, 0, 0, 160))
            effect.setBlurRadius(30)

            sobj_widget.setGraphicsEffect(effect)
            sobj_widget.setTitle(self.dyn_list.values()[i].info['name'])
            try:
                web_file = self.dyn_list.values()[i].process['icon'].contexts['icon'].versionless.values()[0].files['web']
                web_full_path = '{0}/{1}/{2}'.format(env.Env().get_asset_dir(), web_file[0]['relative_dir'], web_file[0]['file_name'])
                sobj_widget.picLabel.setText("<img src=\"{0}\" width=\"{1}\" ".format(web_full_path, image_size))
            except:
                sobj_widget.picLabel.setText('No preview')

            self.scroller.addWidget(sobj_widget)
            self.sobjects_widgets.append(sobj_widget)

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
                self.child_item.setText(0, item['title'].capitalize())
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

