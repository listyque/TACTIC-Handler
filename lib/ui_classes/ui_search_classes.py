import ast
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from lib.environment import env_mode, env_inst, env_server
from lib.configuration import cfg_controls
import lib.global_functions as gf
import lib.tactic_classes as tc
import lib.ui.misc.ui_search_options as ui_search_options
import lib.ui.misc.ui_search_results as ui_search_results
import lib.ui.misc.ui_search_results_tree as ui_search_results_tree


class QPopupTreeWidget(QtGui.QDialog):
    def __init__(self, parent_ui, project, stype, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings(
            '{0}/settings/{1}/{2}/{3}/search_cache.ini'.format(
                env_mode.get_current_path(),
                env_mode.get_node(),
                env_server.get_cur_srv_preset(),
                env_mode.get_mode()),
            QtCore.QSettings.IniFormat
        )

        self.setSizeGripEnabled(True)
        # self.setWindowFlags(QtCore.Qt.ToolTip)
        # self.setWindowFlags(QtCore.Qt.Popup)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.parent_ui = parent_ui
        self.project = project
        self.stype = stype
        self.all_items_dict = {
            'children': [],
            'processes': {},
            'builtins': [],
        }

        title = self.stype.info.get('title')
        if not title:
            title = self.stype.info.get('name')
        elif not title:
            title = self.stype.info.get('code')

        self.setWindowTitle('Pipeline for: {0}'.format(title))

        self.create_tree_widget()
        self.fill_tree_widget()
        self.fit_to_content_tree_widget()
        self.create_buttons()

        self.none = True

        self.controls_actions()
        self.readSettings()

    def get_ignore_dict(self):
        ignore_dict = {
            'children': [],
            'processes': {},
            'builtins': [],
            'show_builtins': self.parent_ui.searchOptionsGroupBox.showAllProcessCheckBox.isChecked()
        }

        build_dict = False

        # get builtins ignore list
        for builtin in self.all_items_dict['builtins']:
            if builtin.checkState(0) == QtCore.Qt.Unchecked:
                build_dict = True
                ignore_dict['builtins'].append(builtin.data(1, 0))

        # get children ignore list
        for child in self.all_items_dict['children']:
            if child.checkState(0) == QtCore.Qt.Unchecked:
                build_dict = True
                ignore_dict['children'].append(child.data(1, 0))

        # get processes ignore list
        for name, processes in self.all_items_dict['processes'].iteritems():
            ignored_process = []
            for process in processes:
                if process.checkState(0) == QtCore.Qt.Unchecked:
                    build_dict = True
                    ignored_process.append(process.data(1, 0))
            ignore_dict['processes'][name] = ignored_process

        if build_dict:
            return ignore_dict
        else:
            return ''

    def set_from_ignore_dict(self, ignore_dict):
        if ignore_dict:
            # return from builtins ignore list
            for builtin in self.all_items_dict['builtins']:
                if builtin.data(1, 0) in ignore_dict['builtins']:
                    builtin.setCheckState(0, QtCore.Qt.Unchecked)

            # get children ignore list
            for child in self.all_items_dict['children']:
                if child.data(1, 0) in ignore_dict['children']:
                    child.setCheckState(0, QtCore.Qt.Unchecked)

            # get processes ignore list
            for name, processes in self.all_items_dict['processes'].iteritems():
                for process in processes:
                    ignore_list = ignore_dict['processes'].get(name)
                    if not ignore_list:
                        ignore_list = []
                    if process.data(1, 0) in ignore_list:
                        process.setCheckState(0, QtCore.Qt.Unchecked)

    def controls_actions(self):

        self.none_button.clicked.connect(lambda: self.switch_items('none'))
        self.all_process_button.clicked.connect(lambda: self.switch_items('process'))
        self.all_with_builtins_button.clicked.connect(lambda: self.switch_items('builtins'))
        self.all_children_button.clicked.connect(lambda: self.switch_items('children'))

        self.save_button.clicked.connect(self.save_and_refresh)
        self.save_close_button.clicked.connect(self.close)

        self.tree_widget.itemChanged.connect(self.check_tree_items)

    def check_tree_items(self, changed_item):
        if len(self.tree_widget.selectedItems()) > 1:
            for item in self.tree_widget.selectedItems():
                item.setCheckState(0, changed_item.checkState(0))

    def switch_items(self, item_type='none'):

        # TODO Remove this, and make it work through ignore dict

        if item_type == 'none':
            for item in self.child_items + self.process_items + self.builtin_items:
                if self.none:
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)
            if self.none:
                self.none = False
            else:
                self.none = True

        if item_type == 'process':
            for item in self.process_items:
                if item.checkState(0):
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

        if item_type == 'builtins':
            for item in self.builtin_items:
                if item.checkState(0):
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

        if item_type == 'children':
            for item in self.child_items:
                if item.checkState(0):
                    item.setCheckState(0, QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(0, QtCore.Qt.Checked)

    def create_buttons(self):

        self.none_button = QtGui.QPushButton('None / All')
        self.all_process_button = QtGui.QPushButton('All Process')
        self.all_with_builtins_button = QtGui.QPushButton('All Builtins')
        self.all_children_button = QtGui.QPushButton('All Children')

        self.save_button = QtGui.QPushButton('Save')
        self.save_close_button = QtGui.QPushButton('Save and close')

        self.grid.addWidget(self.none_button, 1, 0, 1, 1)
        self.grid.addWidget(self.all_process_button, 1, 1, 1, 1)
        self.grid.addWidget(self.all_with_builtins_button, 2, 0, 1, 1)
        self.grid.addWidget(self.all_children_button, 2, 1, 1, 1)

        self.grid.addWidget(self.save_button, 3, 0, 1, 1)
        self.grid.addWidget(self.save_close_button, 3, 1, 1, 1)

    def create_tree_widget(self):

        self.grid = QtGui.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(0)
        self.setLayout(self.grid)

        self.tree_widget = QtGui.QTreeWidget(self)
        self.tree_widget.setTabKeyNavigation(True)
        self.tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tree_widget.setAllColumnsShowFocus(True)
        self.tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setObjectName('tree_widget')
        self.tree_widget.setStyleSheet('QTreeView::item {padding: 2px;}')
        # self.tree_widget.setRootIsDecorated(False)

        self.grid.addWidget(self.tree_widget, 0, 0, 1, 2)

    def fill_tree_widget(self):
        self.child_items = []
        self.process_items = []
        self.builtin_items = []

        # Children process
        for child in self.stype.schema.children:
            child_stype = self.project.stypes.get(child['from'])
            if child_stype:
                stype_title = child_stype.info.get('title')
                if not stype_title:
                    stype_title = child_stype.info.get('code')
                top_item = QtGui.QTreeWidgetItem()
                top_item.setText(0, stype_title.capitalize() + ' (child)')
                top_item.setCheckState(0, QtCore.Qt.Checked)
                top_item.setData(1, 0, child_stype.info.get('code'))
                self.tree_widget.addTopLevelItem(top_item)
                self.child_items.append(top_item)
                if child_stype.pipeline:
                    for pipeline in child_stype.pipeline.itervalues():
                        title = pipeline.info.get('name')
                        if not title:
                            title = pipeline.info.get('code')

                        item = QtGui.QTreeWidgetItem()
                        item.setText(0, title.capitalize())
                        item.setData(1, 0, pipeline.info.get('code'))
                        top_item.addChild(item)
                        top_item.setExpanded(True)
                        child_items = []
                        for key, val in pipeline.process.iteritems():
                            child_item = QtGui.QTreeWidgetItem()
                            child_item.setText(0, key.capitalize())
                            child_item.setCheckState(0, QtCore.Qt.Checked)
                            child_item.setData(1, 0, key)
                            item.addChild(child_item)
                            item.setExpanded(True)
                            self.process_items.append(child_item)
                            child_items.append(child_item)

                        self.all_items_dict['processes'][pipeline.info.get('code')] = child_items
                self.all_items_dict['children'].append(top_item)

        # Actual process
        if self.stype.pipeline:

            for pipeline in self.stype.pipeline.itervalues():
                title = pipeline.info.get('name')
                if not title:
                    title = pipeline.info.get('code')

                top_item = QtGui.QTreeWidgetItem()
                top_item.setText(0, title.capitalize())
                top_item.setData(1, 0, pipeline.info.get('code'))
                self.tree_widget.addTopLevelItem(top_item)

                child_items = []
                for key, val in pipeline.process.iteritems():
                    child_item = QtGui.QTreeWidgetItem()
                    child_item.setText(0, key.capitalize())
                    child_item.setCheckState(0, QtCore.Qt.Checked)
                    child_item.setData(1, 0, key)
                    top_item.addChild(child_item)
                    top_item.setExpanded(True)
                    self.process_items.append(child_item)
                    child_items.append(child_item)

                self.all_items_dict['processes'][pipeline.info.get('code')] = child_items

        # Hidden process
        builtin_items = []
        for key in ['publish', 'attachment', 'icon']:
            # print key
            top_item = QtGui.QTreeWidgetItem()
            top_item.setText(0, key.capitalize() + ' (builtin)')
            top_item.setCheckState(0, QtCore.Qt.Checked)
            top_item.setData(1, 0, key)
            self.tree_widget.addTopLevelItem(top_item)
            self.builtin_items.append(top_item)
            builtin_items.append(top_item)

        self.all_items_dict['builtins'] = builtin_items

    def fit_to_content_tree_widget(self):

        items_count = 0
        for item in QtGui.QTreeWidgetItemIterator(self.tree_widget):
            items_count += 1

        row_height = items_count * self.tree_widget.sizeHintForRow(0) + 80
        mouse_pos = QtGui.QCursor.pos()
        self.setGeometry(mouse_pos.x(), mouse_pos.y(), 250, row_height)

    # def leaveEvent(self, event):
    #     print event, 'Leave Event'
    #
    # def focusOutEvent(self, event):
    #
    #     print event, 'Focus Out'

    def readSettings(self):
        tab_name = self.parent_ui.objectName().split('/')
        group_path = '{0}/{1}/{2}/{3}'.format(
            self.parent_ui.relates_to,
            self.parent_ui.current_namespace,
            self.parent_ui.current_project,
            tab_name[1]
        )
        self.settings.beginGroup(group_path)
        self.set_from_ignore_dict(gf.from_json(self.settings.value('process_ignore_dict')))
        self.settings.endGroup()

    def writeSettings(self):
        tab_name = self.parent_ui.objectName().split('/')
        group_path = '{0}/{1}/{2}/{3}'.format(
            self.parent_ui.relates_to,
            self.parent_ui.current_namespace,
            self.parent_ui.current_project,
            tab_name[1]
        )
        self.settings.beginGroup(group_path)
        self.settings.setValue('process_ignore_dict', gf.to_json(self.get_ignore_dict()))
        self.settings.endGroup()

    def save_and_refresh(self):
        self.writeSettings()
        self.parent_ui.refresh_current_results()

    # def mousePressEvent(self, event):
    #     self.offset = event.pos()
    #
    # def mouseMoveEvent(self, event):
    #     x = event.globalX()
    #     y = event.globalY()
    #     x_w = self.offset.x()
    #     y_w = self.offset.y()
    #     self.move(x - x_w, y - y_w)

    def closeEvent(self, event):
        self.save_and_refresh()
        event.accept()


class Ui_searchOptionsWidget(QtGui.QGroupBox, ui_search_options.Ui_searchOptionsGroupBox):
    def __init__(self, parent_ui, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.parent_ui = parent_ui

        self.project = self.parent_ui.project
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']

        self.tab_name = self.parent_ui.objectName()
        self.tab_related_to = self.parent_ui.relates_to

        self.controls_actions()

    def controls_actions(self):

        self.saveAsDefaultsPushButton.clicked.connect(self.apply_current_to_all_tabs)

    def apply_current_to_all_tabs(self):
        current_settings = self.get_settings_dict()
        for tab in env_inst.ui_check_tree.get(self.parent_ui.relates_to).itervalues():
            tab.searchOptionsGroupBox.set_settings_from_dict(current_settings)

    def get_custom_process_list(self):
        return ['AZZA']

    def set_search_by(self, search_by):

        if search_by == 0:
            self.searchNameRadioButton.setChecked(True)
        elif search_by == 1:
            self.searchCodeRadioButton.setChecked(True)
        elif search_by == 2:
            self.searchDescriptionRadioButton.setChecked(True)
        elif search_by == 3:
            self.searchKeywordsRadioButton.setChecked(True)
        elif search_by == 4:
            self.searchParentCodeRadioButton.setChecked(True)

    def get_search_by(self):

        if self.searchNameRadioButton.isChecked():
            return 0
        elif self.searchCodeRadioButton.isChecked():
            return 1
        elif self.searchDescriptionRadioButton.isChecked():
            return 2
        elif self.searchKeywordsRadioButton.isChecked():
            return 3
        elif self.searchParentCodeRadioButton.isChecked():
            return 4

    def set_sort_by(self, sort_by):

        if sort_by == 0:
            self.sortNameRadioButton.setChecked(True)
        elif sort_by == 1:
            self.sortCodeRadioButton.setChecked(True)
        elif sort_by == 2:
            self.sortTimestampRadioButton.setChecked(True)
        elif sort_by == 3:
            self.sortNothingRadioButton.setChecked(True)

    def get_sort_by(self):

        if self.sortNameRadioButton.isChecked():
            return 0
        elif self.sortCodeRadioButton.isChecked():
            return 1
        elif self.sortTimestampRadioButton.isChecked():
            return 2
        elif self.sortNothingRadioButton.isChecked():
            return 3

    def set_search_options(self, options_dict):
        if options_dict:
            self.set_search_by(options_dict['search_by'])
            self.set_sort_by(options_dict['sort_by'])

    def get_search_options(self):

        options_dict = {
            'search_by': self.get_search_by(),
            'sort_by': self.get_sort_by()
        }

        return options_dict

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'search_options': None,
                'showAllProcessCheckBox': False,
                'displayLimitSpinBox': 10,
            }

        self.set_search_options(ast.literal_eval(str(settings_dict.get('search_options'))))
        self.showAllProcessCheckBox.setChecked(settings_dict['showAllProcessCheckBox'])
        self.displayLimitSpinBox.setValue(settings_dict['displayLimitSpinBox'])

    def get_settings_dict(self):

        settings_dict = {
            'search_options': str(self.get_search_options()),
            'showAllProcessCheckBox': int(self.showAllProcessCheckBox.isChecked()),
            'displayLimitSpinBox': int(self.displayLimitSpinBox.value()),
        }

        return settings_dict


class Ui_resultsFormWidget(QtGui.QWidget, ui_search_results_tree.Ui_resultsForm):
    def __init__(self, parent_ui, info, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.parent_ui = parent_ui
        self.relates_to = self.parent_ui.relates_to
        self.info = info

        self.checkout_config = cfg_controls.get_checkout()
        self.checkin_config = cfg_controls.get_checkin()
        self.current_tree_widget_item = None

        self.create_separate_versions_tree()
        self.create_progress_bar()
        self.controls_actions()

    def controls_actions(self):
        # Tree widget actions
        self.resultsTreeWidget.itemPressed.connect(lambda:  self.set_current_tree_widget_item(self.resultsTreeWidget))
        self.resultsTreeWidget.itemPressed.connect(self.load_preview)
        self.resultsTreeWidget.itemPressed.connect(self.fill_versions_items)
        self.resultsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsTreeWidget.customContextMenuRequested.connect(self.parent_ui.open_menu)

        self.resultsTreeWidget.itemCollapsed.connect(self.send_collapse_event_to_item)
        self.resultsTreeWidget.itemExpanded.connect(self.send_expand_event_to_item)

        # Separate Snapshots tree widget actions
        self.resultsVersionsTreeWidget.itemPressed.connect(lambda: self.set_current_tree_widget_item(self.resultsVersionsTreeWidget))
        self.resultsVersionsTreeWidget.itemPressed.connect(self.load_preview)
        self.resultsVersionsTreeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.resultsVersionsTreeWidget.customContextMenuRequested.connect(self.parent_ui.open_menu)

    def set_current_tree_widget_item(self, tree_widget):
        self.current_tree_widget_item = tree_widget.itemWidget(tree_widget.currentItem(), 0)

    def get_current_tree_widget_item(self):
        return self.current_tree_widget_item

    def send_collapse_event_to_item(self, tree_item):
        tree_widget = self.resultsTreeWidget.itemWidget(tree_item, 0)
        tree_widget.collapse_tree_item()

    def send_expand_event_to_item(self, tree_item):
        tree_widget = self.resultsTreeWidget.itemWidget(tree_item, 0)
        tree_widget.expand_tree_item()

    def fill_versions_items(self, widget):
        if self.resultsVersionsTreeWidget.isVisible():
            parent_widget = self.resultsTreeWidget.itemWidget(widget, 0)

            if parent_widget.type == 'snapshot':
                process = parent_widget.process
                context = parent_widget.context
                snapshots = parent_widget.sobject.process[process].contexts[context].versions

                self.resultsVersionsTreeWidget.clear()

                gf.add_versions_snapshot_item(
                    self.resultsVersionsTreeWidget,
                    self.parent_ui,
                    parent_widget.sobject,
                    parent_widget.stype,
                    process,
                    context,
                    snapshots,
                    parent_widget.info,
                )

            if parent_widget.type == 'sobject':
                self.resultsVersionsTreeWidget.clear()

            if parent_widget.type == 'process':
                self.resultsVersionsTreeWidget.clear()

            if parent_widget.type == 'child':
                self.resultsVersionsTreeWidget.clear()

    def update_versions_items(self, item_widget):
        if self.resultsVersionsTreeWidget.isVisible():

            if item_widget.type == 'snapshot':
                process = item_widget.process
                context = item_widget.context

                snapshots = item_widget.sobject.process[process].contexts[context].versions

                self.resultsVersionsTreeWidget.clear()

                gf.add_versions_snapshot_item(
                    self.resultsVersionsTreeWidget,
                    self.parent_ui,
                    item_widget.sobject,
                    item_widget.stype,
                    process,
                    context,
                    snapshots,
                    item_widget.info,
                )

    def load_preview(self):
        # loading preview image
        nested_item = self.current_tree_widget_item

        if nested_item.type == 'sobject' and nested_item.sobject.process.get('icon'):
            self.parent_ui.load_images(nested_item, True, False)

        if nested_item.type == 'snapshot' and nested_item.files.get('playblast'):
            self.parent_ui.load_images(nested_item, False, True)

        env_inst.ui_main_tabs[self.parent_ui.current_project].skeyLineEdit.setText(nested_item.get_skey(skey=True))
        # env_inst.ui_main.skeyLineEdit.setText(nested_item.get_skey(skey=True))
        if self.parent_ui.relates_to == 'checkout':
            self.parent_ui.descriptionTextEdit.setText(nested_item.get_description())

        if self.parent_ui.relates_to == 'checkin':
            if nested_item.type in ['sobject', 'snapshot', 'process']:
                self.parent_ui.savePushButton.setEnabled(True)
                self.parent_ui.contextLineEdit.setEnabled(True)
                self.parent_ui.contextLineEdit.setText(nested_item.get_context())
            else:
                self.parent_ui.savePushButton.setEnabled(False)
                self.parent_ui.contextLineEdit.setEnabled(False)

    def get_is_separate_versions(self):
        return self.sep_versions

    def create_separate_versions_tree(self):
        if self.parent_ui.relates_to == 'checkout' and self.checkout_config:
            self.sep_versions = bool(int(
                gf.get_value_from_config(self.checkout_config, 'versionsSeparateCheckoutCheckBox', 'QCheckBox')
            ))
        elif self.parent_ui.relates_to == 'checkin' and self.checkin_config:
            self.sep_versions = bool(int(
                gf.get_value_from_config(self.checkin_config, 'versionsSeparateCheckinCheckBox', 'QCheckBox')
            ))
        else:
            self.sep_versions = False

        if not self.sep_versions:
            self.verticalLayoutWidget_3.close()
            # current_widget = self.search_results_widget.get_current_widget()
            # current_widget.verticalLayoutWidget_3.close()

    def create_progress_bar(self):
        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.hide()
        self.resultsLayout.addWidget(self.progress_bar)

    def showEvent(self, event):
        # self.parent_ui.searchOptionsGroupBox.set_search_options(self.info['options'])
        # self.info['options'] = self.parent_ui.searchOptionsGroupBox.get_search_options()
        if self.resultsTreeWidget.topLevelItemCount() == 0:
            self.parent_ui.search_results_widget.add_items_to_results(self.info['title'], refresh=False, revert=True)


class Ui_resultsGroupBoxWidget(QtGui.QGroupBox, ui_search_results.Ui_resultsGroupBox):
    def __init__(self, parent_ui, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.settings = QtCore.QSettings(
            '{0}/settings/{1}/{2}/{3}/search_cache.ini'.format(
                env_mode.get_current_path(),
                env_mode.get_node(),
                env_server.get_cur_srv_preset(),
                env_mode.get_mode()),
            QtCore.QSettings.IniFormat
        )

        self.setupUi(self)
        self.create_ui_search_results()
        self.parent_ui = parent_ui
        self.readSettings()

    def create_ui_search_results(self):
        # Query Threads
        self.names_query_thread = tc.ServerThread(self)
        self.sobjects_query_thread = tc.ServerThread(self)

        self.resultsTabWidget.setTabsClosable(True)
        self.create_new_tab_button()
        # self.add_tab()
        self.controls_actions()
        self.threads_actions()

    def controls_actions(self):
        self.add_new_tab_button.clicked.connect(self.add_tab)
        self.refresh_tab_button.clicked.connect(self.refresh_restults)
        self.resultsTabWidget.tabCloseRequested.connect(self.close_tab)

    def threads_actions(self):
        self.names_query_thread.finished.connect(self.assets_names)
        self.sobjects_query_thread.finished.connect(self.fill_items)

    def get_current_widget(self):
        return self.resultsTabWidget.currentWidget()

    def get_current_tab_text(self):
        return self.resultsTabWidget.tabText(self.resultsTabWidget.currentIndex())

    def set_current_tab_text(self, text):
        self.resultsTabWidget.setTabText(
            self.resultsTabWidget.currentIndex(),
            text
        )

    def get_process_list(self):
        # this only needed to get all snapshots for all processes, when query them

        # get process list from pipeline
        if self.parent_ui.stype.pipeline:
            process = []
            for pipe in self.parent_ui.stype.pipeline.values():
                process.extend(pipe.process.keys())
        else:
            process = []

        # Add builting process
        process.extend((['icon', 'attachment', 'publish']))

        all_ignored_process = []
        # Filter ignored process
        ignore_list = self.parent_ui.get_process_ignore_list()

        if ignore_list:
            for val in ignore_list['processes'].itervalues():
                all_ignored_process.extend(val)
        if all_ignored_process:
            ready_process_list = [x for x in process if x not in all_ignored_process]
        else:
            ready_process_list = process

        if ready_process_list:
            return set(ready_process_list)
        else:
            return []

    def refresh_restults(self):
        self.add_items_to_results(self.get_current_tab_text(), refresh=True)
        # self.animation.start()

    def close_all_tabs(self):

        # while self.resultsTabWidget.count() == 0:
        #     self.resultsTabWidget.count() - 1
        #     print self.resultsTabWidget.tabBar().removeTab()
            # QtGui.QTabBar
        self.resultsTabWidget.clear()
        self.add_tab()

        # print self.resultsTabWidget.count(), 'FIRST COUNT'
        # for i in range(self.resultsTabWidget.count()+1):
        #     # print 'delete ', i
        #     # print self.resultsTabWidget.widget(i).close()
        #     # self.resultsTabWidget.removeTab(i)
        #     print self.resultsTabWidget.tabBar().removeTab(i)
        #     # self.close_tab(tab_index=i, self_close=False)
        #
        # print self.resultsTabWidget.count(), 'END COUNT'
        # self.add_tab()

    def do_search(self, search_query=None, search_by=None, new_tab=False):
        if not search_query:
            search_query = self.parent_ui.get_search_query_text()
        if new_tab:
            self.add_tab()
        self.set_current_tab_text(search_query)

        self.add_items_to_results(search_query, search_by=search_by)

    def add_items_to_results(self, query=None, refresh=False, revert=False, search_by=None):
        """
        Adding queried items to results tree widget
        :param query:
        :param refresh:
        :param revert:
        :param search_by:
        :return:
        """
        # TODO What is revert??
        current_widget = self.get_current_widget()

        if refresh:
            current_widget.info['state'] = gf.tree_state(current_widget.resultsTreeWidget, {})
        elif not revert:
            current_widget.info['state'] = None
        # else:
        #     current_widget.info['state'] =
        if not search_by:
            search_by = self.parent_ui.search_mode_state()

        query_tuple = query, search_by

        if query:
            # Run first thread
            if not self.names_query_thread.isRunning():
                self.names_query_thread.kwargs = dict(
                    query=query_tuple,
                    stype=self.parent_ui.tab_name,
                    project=self.parent_ui.current_project
                )
                self.names_query_thread.routine = tc.assets_query_new
                self.names_query_thread.start()

    def assets_names(self):
        names = tc.treat_result(self.names_query_thread)
        if names.isFailed():
            if names.result == QtGui.QMessageBox.ApplyRole:
                names.run()
                self.assets_names()
            elif names.result == QtGui.QMessageBox.ActionRole:
                env_inst.offline = True
                env_inst.ui_main.open_config_dialog()

        if not names.isFailed():
            # pretty name for new single tab
            if len(names.result) == 1:
                tab_name = names.result[0].get('name')
                if tab_name:
                    self.set_current_tab_text(tab_name)

            if not self.sobjects_query_thread.isRunning():
                self.sobjects_query_thread.kwargs = dict(process_list=self.get_process_list(), sobjects_list=names.result, project_code=self.parent_ui.current_project)
                self.sobjects_query_thread.routine = tc.get_sobjects
                self.sobjects_query_thread.start()

    def fill_items(self):
        self.sobjects = self.sobjects_query_thread.result

        current_widget = self.get_current_widget()
        current_tree_widget = current_widget.resultsTreeWidget

        current_tree_widget.clear()

        current_widget.progress_bar.setVisible(True)
        total_sobjects = len(self.sobjects.keys()) - 1

        for p, sobject in enumerate(self.sobjects.itervalues()):
            item_info = {
                'relates_to': self.parent_ui.relates_to,
                'is_expanded': False,
            }

            gf.add_sobject_item(
                current_tree_widget,
                self.parent_ui,
                sobject,
                self.parent_ui.stype,
                item_info,
                ignore_dict=self.parent_ui.get_process_ignore_list()
            )

            if total_sobjects:
                current_widget.progress_bar.setValue(int(p * 100 / total_sobjects))

        if current_widget.info['state']:
            gf.tree_state_revert(current_tree_widget, current_widget.info['state'])

        current_widget.progress_bar.setVisible(False)

    def update_item_tree(self, item):
        current_widget = self.get_current_widget()
        current_tree_widget = current_widget.resultsTreeWidget
        current_widget.info['state'] = gf.tree_state(current_tree_widget, {})
        current_widget.progress_bar.setVisible(True)

        item.update_items()
        current_widget.update_versions_items(item)

        if current_widget.info['state']:
            gf.tree_state_revert(current_tree_widget, current_widget.info['state'])
        current_widget.progress_bar.setVisible(False)

    def add_to_history_list(self, tab_title, widget):
        #TODO remove cleared widgets to resolve memory leak
        if tab_title:
            filter_process = QtGui.QAction(tab_title, self.history_tab_button)
            filter_process.triggered.connect(lambda: self.restore_tab_from_history(filter_process, widget))

            try:
                if self.clear_history:
                    pass
            except:
                self.clear_history = QtGui.QAction('Clear History', self.history_tab_button)
                self.clear_history.triggered.connect(self.clear_tabs_history)
                self.history_tab_button.addAction(self.clear_history)
                self.sep = QtGui.QAction('', self.history_tab_button)
                self.sep.setSeparator(True)
                self.history_tab_button.addAction(self.sep)

            self.history_tab_button.addAction(filter_process)

    def clear_tabs_history(self):
        for action in self.history_tab_button.actions():
            self.history_tab_button.removeAction(action)
        del self.clear_history

    def restore_tab_from_history(self, action, widget):

        self.resultsTabWidget.addTab(widget, action.text())
        self.resultsTabWidget.setCurrentWidget(widget)
        self.history_tab_button.removeAction(action)

    def close_tab(self, tab_index):
        if self.resultsTabWidget.count() > 1:
            self.add_to_history_list(self.resultsTabWidget.tabText(tab_index), self.resultsTabWidget.widget(tab_index))
            self.resultsTabWidget.removeTab(tab_index)

    def create_new_tab_button(self):
        self.add_new_tab_button = QtGui.QToolButton()
        self.add_new_tab_button.setAutoRaise(True)
        self.add_new_tab_button.setMinimumWidth(22)
        self.add_new_tab_button.setMinimumHeight(22)
        self.add_new_tab_button.setIcon(gf.get_icon('plus'))

        self.history_tab_button = QtGui.QToolButton()
        self.history_tab_button.setAutoRaise(True)
        self.history_tab_button.setMinimumWidth(22)
        self.history_tab_button.setMinimumHeight(22)
        self.history_tab_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.history_tab_button.setIcon(gf.get_icon('history'))

        self.refresh_tab_button = QtGui.QToolButton()
        self.refresh_tab_button.setAutoRaise(True)
        self.refresh_tab_button.setMinimumWidth(22)
        self.refresh_tab_button.setMinimumHeight(22)

        # effect = QtGui.QGraphicsColorizeEffect(self.refresh_tab_button)
        # self.animation = QtCore.QPropertyAnimation(effect, "color", self)
        # self.animation.setDuration(500)
        # self.animation.setStartValue(QtGui.QColor(0, 0, 0, 0))
        # self.animation.setEndValue(QtGui.QColor(49, 140, 72, 128))
        # self.animation.start()
        # self.refresh_tab_button.setGraphicsEffect(effect)
        self.refresh_tab_button.setIcon(gf.get_icon('refresh'))

        self.right_buttons_layout = QtGui.QHBoxLayout()
        self.right_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.right_buttons_layout.setSpacing(2)
        self.right_buttons_widget= QtGui.QWidget(self)
        self.right_buttons_widget.setLayout(self.right_buttons_layout)
        self.right_buttons_layout.addWidget(self.refresh_tab_button)
        self.right_buttons_layout.addWidget(self.history_tab_button)

        self.resultsTabWidget.setCornerWidget(self.right_buttons_widget, QtCore.Qt.TopRightCorner)
        self.resultsTabWidget.setCornerWidget(self.add_new_tab_button, QtCore.Qt.TopLeftCorner)

    def add_tab(self, search_title='', state=None, options=None, search_column=None, search_text=None):
        info = {
            'title': search_title,
            'state': state,
            'options': options,
            'search_column': search_column,
            'search_text': search_text,
        }
        search_results_tree = Ui_resultsFormWidget(parent_ui=self.parent_ui, info=info, parent=self)
        self.resultsTabWidget.addTab(search_results_tree, search_title)
        self.resultsTabWidget.setCurrentWidget(search_results_tree)
        return search_results_tree.resultsTreeWidget

    def readSettings(self):
        """
        Reading Settings
        """
        self.settings.beginGroup(self.parent_ui.relates_to)
        tab_name = self.parent_ui.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(self.parent_ui.current_namespace, self.parent_ui.current_project, tab_name[1])
        self.settings.beginGroup(group_path)

        search_cache = gf.hex_to_html(self.settings.value('last_search_tabs'))

        if search_cache:
            search_cache = ast.literal_eval(search_cache)
            tab_added = 0
            for tab, state, options in zip(search_cache[0], search_cache[1], search_cache[3]):
                self.add_tab(tab, state, options)
                tab_added += 1
            if not tab_added:
                self.add_tab()
            self.resultsTabWidget.setCurrentIndex(int(search_cache[2]))
        else:
            self.add_tab()
        self.settings.endGroup()
        self.settings.endGroup()

    def writeSettings(self):
        """
        Writing Settings
        """
        self.settings.beginGroup(self.parent_ui.relates_to)
        tab_name = self.parent_ui.objectName().split('/')
        group_path = '{0}/{1}/{2}'.format(self.parent_ui.current_namespace, self.parent_ui.current_project, tab_name[1])
        self.settings.beginGroup(group_path)

        tab_names_list = []
        tab_state_list = []
        tab_options_list = []

        # FIXME bug when saving tabs when there is empty tab...

        for tab in range(self.resultsTabWidget.count()):
            current_state = gf.tree_state(self.resultsTabWidget.widget(tab).resultsTreeWidget, {})
            old_state = self.resultsTabWidget.widget(tab).info['state']

            if current_state:
                tab_state_list.append(current_state)
            elif old_state:
                tab_state_list.append(old_state)

            tab_names_list.append(self.resultsTabWidget.tabText(tab))
            tab_options_list.append(self.parent_ui.searchOptionsGroupBox.get_search_options())

        search_cache = (tab_names_list, tab_state_list, self.resultsTabWidget.currentIndex(), tab_options_list)

        # self.settings.setValue('last_search_tabs', str(search_cache))
        self.settings.setValue('last_search_tabs', gf.html_to_hex(str(search_cache)))

        print('Done ui_search ' + self.parent_ui.objectName() + ' settings write')
        self.settings.endGroup()
        self.settings.endGroup()
