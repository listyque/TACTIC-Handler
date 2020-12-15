# file ui_assets_browser_classes.py
# Assets Browser

import math
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import thlib.tactic_classes as tc
import thlib.global_functions as gf
from thlib.environment import env_inst
import thlib.ui.browser.ui_assets_browser as ui_assets_browser
import thlib.ui.browser.ui_sobject as ui_sobject
import thlib.ui.browser.ui_sobject_info as ui_sobject_info
import thlib.ui_classes.ui_tasks_classes
import thlib.ui_classes.ui_addsobject_classes as addsobject_widget
# import ui_icons_classes as icons_widget

#reload(ui_assets_browser)


class Ui_sobjectInfoWidget(QtGui.QMainWindow, ui_sobject_info.Ui_sobjectInfo):
    def __init__(self, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        # self.statusBar()

        self.setupUi(self)

        self.sobject = sobject

        # self.create_tasks_widget()
        # self.create_edit_widget()

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


class Ui_assetsBrowserWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.sobjects_widgets = None
        self.all_width = 10

        self.create_ui_raw()

        self.relates_to = 'assets_browser'

        self.asstes_tree = None
        self.dyn_list = []
        # self.tabs_items, self.context_items = self.query_tabs()
        self.toggle = False
        self.current_stype = None

        self.create_scroll_layout()

        self.controls_actions()

        # self.create_search_group_box()

        # self.subscriptions_query()

    def create_ui_raw(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtGui.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.assetsTreeWidget = QtGui.QTreeWidget(self.splitter)
        self.assetsTreeWidget.setMinimumSize(QtCore.QSize(120, 0))
        self.assetsTreeWidget.setMaximumSize(QtCore.QSize(200, 16777215))
        self.assetsTreeWidget.setBaseSize(QtCore.QSize(60, 0))
        self.assetsTreeWidget.setObjectName("assetsTreeWidget")
        self.assetsTreeWidget.header().setVisible(False)
        self.verticalLayoutWidget_3 = QtGui.QWidget(self.splitter)
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.searchLineEdit = QtGui.QLineEdit(self.verticalLayoutWidget_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.searchLineEdit.sizePolicy().hasHeightForWidth())
        self.searchLineEdit.setSizePolicy(sizePolicy)
        self.searchLineEdit.setMaximumSize(QtCore.QSize(16777215, 20))
        font = Qt4Gui.QFont()
        font.setPointSize(9)
        self.searchLineEdit.setFont(font)
        self.searchLineEdit.setStyleSheet("QLineEdit {\n"
                                          "    color: rgb(192, 192, 192);\n"
                                          "    border: 2px solid darkgray;\n"
                                          "    border-radius: 10px;\n"
                                          "    show-decoration-selected: 1;\n"
                                          "    padding: 0px 8px;\n"
                                          "    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(128, 128, 128, 255), stop:1 rgba(64, 64,64, 255));\n"
                                          "    background-position: bottom left;\n"
                                          "    background-image: url(\":/ui_check/gliph/search_16.png\");\n"
                                          "    background-repeat: fixed;\n"
                                          "    selection-background-color: darkgray;\n"
                                          "    padding-left: 15px;\n"
                                          "}\n"
                                          "QLineEdit:hover{\n"
                                          "    color: white;\n"
                                          "    background-image: url(\":/ui_check/gliph/searchHover_16.png\");\n"
                                          "}")
        self.searchLineEdit.setFrame(False)
        self.searchLineEdit.setObjectName("searchLineEdit")
        self.verticalLayout_2.addWidget(self.searchLineEdit)
        self.searchOptionsLayout = QtGui.QVBoxLayout()
        self.searchOptionsLayout.setSpacing(0)
        self.searchOptionsLayout.setObjectName("searchOptionsLayout")
        self.verticalLayout_2.addLayout(self.searchOptionsLayout)
        self.sobjectScrollLayout = QtGui.QVBoxLayout()
        self.sobjectScrollLayout.setSpacing(0)
        self.sobjectScrollLayout.setObjectName("sobjectScrollLayout")
        self.verticalLayout_2.addLayout(self.sobjectScrollLayout)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.countLabel = QtGui.QLabel(self.verticalLayoutWidget_3)
        self.countLabel.setObjectName("countLabel")
        self.horizontalLayout.addWidget(self.countLabel)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label_2 = QtGui.QLabel(self.verticalLayoutWidget_3)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.limitSpinBox = QtGui.QSpinBox(self.verticalLayoutWidget_3)
        self.limitSpinBox.setMinimum(5)
        self.limitSpinBox.setMaximum(500)
        self.limitSpinBox.setSingleStep(5)
        self.limitSpinBox.setProperty("value", 20)
        self.limitSpinBox.setObjectName("limitSpinBox")
        self.horizontalLayout.addWidget(self.limitSpinBox)
        self.label = QtGui.QLabel(self.verticalLayoutWidget_3)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.zoomSpinBox = QtGui.QSpinBox(self.verticalLayoutWidget_3)
        self.zoomSpinBox.setMinimum(25)
        self.zoomSpinBox.setMaximum(400)
        self.zoomSpinBox.setSingleStep(25)
        self.zoomSpinBox.setProperty("value", 100)
        self.zoomSpinBox.setObjectName("zoomSpinBox")
        self.horizontalLayout.addWidget(self.zoomSpinBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout_2.setStretch(2, 1)
        self.verticalLayout.addWidget(self.splitter)

        self.assetsTreeWidget.headerItem().setText(0, u"all")
        self.countLabel.setText(u"(10/150)")
        self.label_2.setText(u"Load Limit:")
        self.label.setText(u"Zoom:")
        self.zoomSpinBox.setSuffix(u"%")

    # def create_search_group_box(self):
    #     self.searchOptionsGroupBox = icons_widget.Ui_searchOptionsWidget(self)
    #     self.searchOptionsLayout.addWidget(self.searchOptionsGroupBox)
    #     self.searchOptionsGroupBox.miscGroupBox.hide()

    # def searchLineDoubleClick(self, event):
    #     if not self.toggle:
    #         self.toggle = True
    #         self.searchOptionsGroupBox.setMinimumHeight(95)
    #     else:
    #         self.toggle = False
    #         self.searchOptionsGroupBox.setMinimumHeight(0)

    # def searchLineSingleClick(self, event):
    #     self.searchLineEdit.selectAll()

    def controls_actions(self):
        self.zoomSpinBox.valueChanged.connect(self.sobject_widget_zoom)
        self.assetsTreeWidget.itemClicked.connect(self.load_results)

        # self.searchLineEdit.mouseDoubleClickEvent = self.searchLineDoubleClick
        # self.searchLineEdit.mousePressEvent = self.searchLineSingleClick

    def sobject_widget_zoom(self, value):
        for sobj_widget in self.sobjects_widgets:
            sobj_widget.setMinimumWidth(150 * value / 100)
            sobj_widget.setMinimumHeight(150 * value / 100)
            image_size = 140 * self.zoomSpinBox.value() / 100
            # if sobj_widget.picLabel.text() != 'No preview':
            #     old_path_split = sobj_widget.picLabel.text().split('=')
            #     old_path_join = '{0}={1}='.format(*old_path_split) + '"{0}"'.format(image_size)
            #     sobj_widget.picLabel.setText(old_path_join)

    # def resizeEvent(self, event):
    #     if self.sobjects_widgets:
    #         self.scroll_area_contents.setUpdatesEnabled(False)
    #
    #         width = self.scroll_area_contents.width()-2
    #         current = self.sobjects_widgets[0].width()
    #         max_width = 300
    #         min_width = 200
    #
    #         if width % 2 != 0:
    #             width -= 1
    #
    #         if current < max_width:
    #             self.all_width = width / max_width
    #
    #         if current > min_width:
    #             self.all_width = width / min_width
    #
    #         wdg_width = width / self.all_width
    #
    #         if wdg_width < min_width:
    #             wdg_width = min_width
    #
    #         if wdg_width > max_width:
    #             wdg_width = max_width
    #
    #         if wdg_width % 2 != 0:
    #             wdg_width -= 1
    #
    #         print(wdg_width, width, self.all_width)
    #
    #         for sobj_widget in self.sobjects_widgets:
    #             sobj_widget.setFixedSize(wdg_width, wdg_width)
    #             # sobj_widget.setMinimumWidth(wdg_width)
    #             # sobj_widget.setMinimumHeight(wdg_width)
    #
    #             # sobj_widget.setMinimumWidth(150 * 150 / 100)
    #             # sobj_widget.setMinimumHeight(150 * 150 / 100)
    #             # image_size = 140 * self.zoomSpinBox.value() / 100
    #
    #         self.scroll_area_contents.setUpdatesEnabled(True)
    #     event.accept()

    def dynamic_query(self, limit=0, offset=0):

        filters = []
        order_bys = ['timestamp desc']
        columns = []
        # sobjects_list = tc.server_start(project=env_inst.current_project).query(self.current_stype, filters, columns, order_bys, limit=limit, offset=offset)
        # print self.current_stype
        # print sobjects_list
        # print filters

        search_type = tc.server_start().build_search_type(self.current_stype, env_inst.current_project)

        # all_process = self.context_items[self.current_stype]
        # sobjects = tc.get_sobjects(all_process, sobjects_list)
        # sobjects = tc.get_sobjects_objects(sobjects_list, env_inst.current_project)

        sobjects = tc.get_sobjects(
            search_type=search_type,
            project_code=env_inst.current_project,
            filters=filters,
            order_bys=order_bys,
            limit=limit,
            offset=offset,
            include_info=False,
            include_snapshots=True,
        )

        return sobjects

    # def subscriptions_query(self):
    #     import collections
    #
    #     stub = tc.server_start()
    #
    #     all_sobjects = tc.query_tab_names(True)
    #
    #     filters = [('login', env.Env.get_user()), ('project_code', env.Env.get_project())]
    #
    #     subscriptions = stub.query('sthpw/subscription', filters)
    #
    #     spl = collections.defaultdict(list)
    #
    #     for sub in subscriptions:
    #         split = stub.split_search_key(sub['message_code'])
    #         spl[split[0]].append(split[1])
    #
    #     parents = collections.defaultdict(list)
    #     for key, values in spl.items():
    #         parents[key.split('?')[0]] = \
    #             tc.get_sobjects(sobjects_list=stub.query(key, [('code', values)]), get_snapshots=False)
    #
    #     pprint(all_sobjects)
    #     pprint(dict(parents))
    #
    #     # print(stub.get_parent('cgshort/shot?project=the_pirate&code=SHOT00001'))
    #
    #     server = tc.server_start()
    #     expr = "@GET(cgshort/shot.cgshort/scenes.code)"
    #     result = server.eval(expr)
    #     pprint(result)
    #     pprint(stub.query('cgshort/shot', [('scenes_code', 'SCENES00001')]))

    def create_scroll_layout(self):
        # self.scroller = FlowLayout()
        # self.scroller.setContentsMargins(20, 20, 20, 20)
        # self.scroller.setSpacing(12)
        # self.scroller.wheelEvent = self.wheelEvent
        # self.sobjectScrollLayout.addWidget(self.scroller)

        self.scroll_area_contents = QtGui.QWidget()
        self.scroll_area_contents.setContentsMargins(0, 0, 0, 0)

        self.scroller = QtGui.QScrollArea()
        self.scroller.setWidgetResizable(True)
        self.scroller.setWidget(self.scroll_area_contents)
        self.scroller.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.scroll_area_layout = StretchFlowLayout(self.scroll_area_contents)
        # self.scroll_area_layout = QtGui.QGridLayout(self.scroll_area_contents)

        self.scroll_area_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area_layout.setSpacing(0)

        self.sobjectScrollLayout.addWidget(self.scroller)

    def fill_results(self):
        self.dyn_list = self.dynamic_query(self.limitSpinBox.value(), self.scroll_area_layout.count())

        for i in range(len(self.dyn_list)):
            # QtGui.qApp.processEvents()
            self.sobj_widget = Ui_sobjectWidget(list(self.dyn_list.values())[i], self)
            # self.sobj_widget = QtGui.QPushButton('SOBJ')
            self.sobj_widget.setMinimumWidth(150 * self.zoomSpinBox.value() / 100)
            self.sobj_widget.setMinimumHeight(150 * self.zoomSpinBox.value() / 100)
            image_size = 140 * self.zoomSpinBox.value() / 100

            # effect = QtGui.QGraphicsDropShadowEffect(self.assetsTreeWidget)
            # effect.setOffset(3, 3)
            # effect.setColor(Qt4Gui.QColor(0, 0, 0, 160))
            # effect.setBlurRadius(30)

            # self.sobj_widget.setGraphicsEffect(effect)
            self.sobj_widget.setTitle(list(self.dyn_list.values())[i].info['name'])
            try:
                # web_file = self.dyn_list.values()[i].process['icon'].contexts['icon'].versionless.values()[0].files['web']
                # web_full_path = '{0}/{1}/{2}'.format(env.Env.get_asset_dir(), web_file[0]['relative_dir'], web_file[0]['file_name'])
                sobject = list(self.dyn_list.values())[i]

                publish_process = sobject.get_process('publish')
                context = publish_process.contexts.get('publish')

                versionless_snapshots = context.get_versionless()

                file_obj = list(versionless_snapshots.values())[0].get_previewable_files_objects()

                # print file_obj[0].get_full_abs_path()
                # print file_obj[0].get_web_preview()

                web_preview = file_obj[0].get_web_preview()

                web_full_path = web_preview.get_full_abs_path()

                self.sobj_widget.picLabel.setText("<img src=\"{0}\" width=\"{1}\" ".format(web_full_path, image_size))
            except:
                self.sobj_widget.picLabel.setText('No preview')

            self.scroll_area_layout.addWidget(self.sobj_widget)
            self.sobjects_widgets.append(self.sobj_widget)

    def wheelEvent(self, QWheelEvent):
        if QWheelEvent.delta() < 0 and self.current_stype:
            self.fill_results()

    def create_assets_tree(self):
        stypes = env_inst.get_current_stypes()
        self.asstes_tree = tc.group_sobject_by(stypes, 'type')
        # self.asstes_tree = tc.query_assets_names()
        for name, value in self.asstes_tree.items():
            self.top_item = QtGui.QTreeWidgetItem()
            if not name:
                name = 'Untyped'
            self.top_item.setText(0, name.capitalize())
            self.assetsTreeWidget.addTopLevelItem(self.top_item)
            for item in value:
                # print(item)
                self.child_item = QtGui.QTreeWidgetItem()
                if item.info['title']:
                    item_title = item.info['title'].capitalize()
                else:
                    item_title = 'Unnamed'
                self.child_item.setText(0, item_title)
                self.child_item.setData(0, QtCore.Qt.UserRole, item.info)
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


class StretchFlowLayout(QtGui.QLayout):

    def __init__(self, parent=None):
        super(StretchFlowLayout, self).__init__(parent)
        self.itemList = []
        self.m_hSpace = 0
        self.m_vSpace = 0
        self.m_minSize = QtCore.QSize(64, 64)
        self.m_maxSize = QtCore.QSize(256, 256)
        self.m_maxItemPerLine = -2
        self.m_maxItemPerLineDefaultMax = (QtGui.QApplication.desktop().geometry().width() + self.spacing()) // (
                    self.m_minSize.width() + self.spacing())
        self.m_maxItemPerLineDefaultMin = (QtGui.QApplication.desktop().geometry().width() + self.spacing()) // (
                    self.m_minSize.width() + self.spacing())

    def maximumItemPerLine(self):
        return self.m_maxItemPerLine

    def setMaximumItemPerLine(self, count):
        self.m_maxItemPerLine = count

    def minimumItemSize(self):
        return self.m_minSize

    def setMinimumSize(self, size):
        self.m_minSize = size
        self.m_maxItemPerLineDefaultMin = (QtGui.QApplication.desktop().geometry().width() + self.spacing()) // (
                    self.m_minSize.width() + self.spacing())

    def maximumItemSize(self):
        return self.m_maxSize

    def setMaximumSize(self, size):
        self.m_maxSize = size
        self.m_maxItemPerLineDefaultMax = (QtGui.QApplication.desktop().geometry().width() + self.spacing()) // (
                    self.m_maxSize.width() + self.spacing())

    def addItem(self, item):
        self.itemList.append(item)

    def horizontalSpacing(self):
        if self.m_hSpace > 0:
            return self.m_hSpace
        else:
            return self.smartSpacing(QtGui.QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self.m_vSpace > 0:
            return self.m_vSpace
        else:
            return self.smartSpacing(QtGui.QStyle.PM_LayoutVerticalSpacing)

    def expandingDirections(self):
        return QtCore.Qt.Horizontal | QtCore.Qt.Vertical

    def hasHeightForWidth(self):
        return True

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
            break
        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def setGeometry(self, rect):
        QtGui.QLayout.setGeometry(self, rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def doLayout(self, rect, testOnly=False):
        left, top, right, bottom = self.getContentsMargins()
        effectiveRect = rect
        x = effectiveRect.x()
        y = effectiveRect.y()
        lineHeight = 0
        itemSize = self.m_minSize
        if self.itemList:
            itemSize = QtCore.QSize(
                max([self.m_minSize.width(), min([self.m_maxSize.width(), self.itemList[0].sizeHint().width()])]),
                max([self.m_minSize.height(), min([self.m_maxSize.height(), self.itemList[0].sizeHint().height()])])
            )
        lineItemCount = min(
            [(effectiveRect.width() + self.spacing()) // (itemSize.width() + self.spacing()), self.count()])
        if self.m_maxItemPerLine >= 1:
            if lineItemCount > self.m_maxItemPerLine:
                lineItemCount = self.m_maxItemPerLine
        elif self.m_maxItemPerLine == -1:
            if lineItemCount > self.m_maxItemPerLineDefaultMax:
                lineItemCount = self.m_maxItemPerLineDefaultMax
        elif self.m_maxItemPerLine < -1:
            for i in range(self.m_maxItemPerLineDefaultMin):
                if self.m_minSize.width() * i <= effectiveRect.width() <= self.m_maxSize.width() * i:
                    lineItemCount = i
                    break

        if lineItemCount < 1:
            lineItemCount = 1

        lineCount = math.ceil(len(self.itemList) / lineItemCount)
        freeWidth = effectiveRect.width() - (itemSize.width() + self.spacing()) * lineItemCount
        itemSize = QtCore.QSize(
            max([self.m_minSize.width(), min([self.m_maxSize.width(), itemSize.width() + freeWidth / lineItemCount])]),
            max([self.m_minSize.height(),
                 min([self.m_maxSize.height(), itemSize.height() + freeWidth / lineItemCount])])
        )
        itemIndex = 0
        for line in range(int(lineCount)):
            lineX = x
            for lineItem in range(lineItemCount):
                item = self.itemAt(itemIndex)
                if not item:
                    break

                itemIndex += 1
                itemWidget = item.widget()
                if not testOnly:
                    pos = QtCore.QPoint(lineX, y)
                    lineX += itemSize.width() + self.spacing()
                    itemGeometry = QtCore.QRect(pos, itemSize)

                    itemWidget.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
                    itemWidget.setMinimumSize(self.m_minSize)
                    itemWidget.setMaximumSize(self.m_maxSize)
                    item.setGeometry(itemGeometry)

            y += itemSize.height() + self.spacing()

        return y + lineHeight - rect.y() + bottom

    def smartSpacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            pw = parent
            return pw.style().pixelMetric(pm, None, pw)
        else:
            pl = parent
            return pl.spacing()

