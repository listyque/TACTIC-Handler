# module Tree widget item Classes
# file ui_item_classes.py
# Main Item for TreeWidget

import os
import PySide.QtGui as QtGui
import lib.environment as env
import lib.configuration as cfg
import lib.global_functions as gf
import lib.tactic_classes as tc
import lib.ui.items.ui_item as ui_item
import lib.ui.items.ui_item_children as ui_item_children
import lib.ui.items.ui_item_process as ui_item_process
import lib.ui.items.ui_item_snapshot as ui_item_snapshot
import ui_tasks_classes as tasks_widget
import ui_notes_classes as notes_widget

reload(ui_item)
reload(ui_item_process)
reload(ui_item_snapshot)
reload(tasks_widget)
reload(notes_widget)


class Ui_itemWidget(QtGui.QWidget, ui_item.Ui_item):
    def __init__(self, sobject, stype, info, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'sobject'
        self.sobject = sobject
        self.stype = stype
        self.info = info
        self.tree_item = tree_item
        self.process_items = []
        self.snapshot_items = []
        self.child_items = []
        self.tree_widget = parent
        self.project = self.tree_widget.project

        # if parent:
        #     self.relates_to = parent.relates_to
        # print self.sobject.info
        # print self.stype.info
        # print self.info
        #
        # self.row = row
        # self.item_info = {}

        if self.sobject:
            self.fill_sobject_info()

        self.controls_actions()

        self.parents_stypes = None
        self.children_stypes = None
        self.check_for_children()

        # fill item info
        # self.item_info['description'] = self.sobject.info['description']

    def controls_actions(self):
        self.tasksToolButton.setHidden(True) # Temporaty hide tasks button
        self.tasksToolButton.clicked.connect(lambda: self.create_tasks_window())
        self.relationsToolButton.clicked.connect(self.check_for_children)

    def fill_sobject_info(self):
        title = 'No Title'
        if self.sobject.info.get('name'):
            title = self.sobject.info.get('name')
        elif self.sobject.info.get('title'):
            title = self.sobject.info.get('title')
        elif self.sobject.info.get('code'):
            title = self.sobject.info.get('code')

        self.fileNameLabel.setText(title)
        self.commentLabel.setText(gf.to_plain_text(self.sobject.info.get('description')))
        # TODO correct date time
        # dateLabel = QtCore.QDateTime.fromString(self.sobject.info['timestamp'], 'yyyy-MM-dd HH:mm:ss')
        self.dateLabel.setText(self.sobject.info.get('timestamp'))

    def prnt(self):
        # shot_tab = env.Inst.ui_check_tree[self.relates_to]['cgshort/shot']
        print(env.Inst.ui_check_tabs[self.relates_to].sObjTabWidget.count())
        tab_wdg = env.Inst.ui_check_tabs[self.relates_to].sObjTabWidget
        for i in range(tab_wdg.count()):
            print tab_wdg.widget(i).objectName()
            if tab_wdg.widget(i).objectName() == 'cgshort/shot':
                tab_wdg.setCurrentIndex(i)

        tree_wdg = tab_wdg.currentWidget()

        tree_wdg.searchLineEdit.setText('SCENES00001')
        tree_wdg.searchOptionsGroupBox.searchParentCodeRadioButton.setChecked(True)
        tree_wdg.add_items_to_results('SCENES00001')

    def check_for_children(self):
        if self.stype.schema.parents:
            self.parents_stypes = self.stype.schema.parents
            for parent in self.stype.schema.parents:
                parent_code = parent.get('to')
                parent_title = self.project.stypes.get(parent_code)
                if parent_title:
                    parent_title = parent_title.info.get('title')
                else:
                    parent_title = parent_code
                parent_action = QtGui.QAction(parent_title, self.relationsToolButton)
                self.relationsToolButton.addAction(parent_action)

        if self.stype.schema.children:
            self.children_stypes = self.stype.schema.children
            child_sep = QtGui.QAction('Children', self.relationsToolButton)
            child_sep.setSeparator(True)
            self.relationsToolButton.addAction(child_sep)

            for child in self.stype.schema.children:
                child_code = child.get('from')
                child_title = self.project.stypes.get(child_code)
                if child_title:
                    child_title = child_title.info.get('title')
                else:
                    child_title = child_code
                child_action = QtGui.QAction(child_title, self.relationsToolButton)
                self.relationsToolButton.addAction(child_action)

        if not (self.stype.schema.children or self.stype.schema.parents):
            self.relationsToolButton.hide()

            # print self.sobject.info
            # server = tc.server_start()
            # RESHENO SOBSTVENNY CLASS FOR SCHEMA!
            # print server.get_all_children('sthpw/search_object?id=86', 'cgshort/shot')
            # print server.get_parent_type(['cgshort/scenes'])
            # print server.build_search_type('the_pirate/scenes')
            # print server.get_related_types('cgshort/scenes')

            # print server.get_connected_sobjects('sthpw/search_object?id=86')
            # print server.get_all_children(self.sobject.info['__search_key__'], 'sthpw/snapshot')

    def create_tasks_window(self):
        try:
            self.tasks_widget.show()
        except:
            # print(self.item_info)
            # current_tab_context = env.Inst.ui_checkout_tree[self.sobject.info['pipeline_code']].context_items
            # print(env.Inst.ui_checkout_tree)
            self.tasks_widget = tasks_widget.Ui_tasksWidgetMain(self.sobject, self)
            self.tasks_widget.show()

    def get_context(self, process=False, custom=None):
        if process:
            if custom:
                return '{0}/{1}'.format('publish', custom)
            else:
                return 'publish'
        else:
            return ''

    def get_skey(self, skey=False, only=False, parent=False):
        """skey://cgshort/props?project=the_pirate&code=PROPS00001"""
        if parent or only:
            return self.sobject.info['__search_key__']
        if skey:
            return 'skey://' + self.sobject.info['__search_key__']

    def get_description(self):
        return self.sobject.info.get('description')

    def update_description(self, new_description):
        self.sobject.info['description'] = new_description
        self.commentLabel.setText(new_description)


class Ui_processItemWidget(QtGui.QWidget, ui_item_process.Ui_processItem):
    def __init__(self, sobject, stype, process, info, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'process'
        self.sobject = sobject
        self.stype = stype
        self.process = process
        self.info = info
        self.tree_item = tree_item
        self.snapshot_items = []
        # print(tree_item.text(0))
        # self.item_info = {}
        self.tree_item.setText(0, process)

        # self.row = row

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
        self.note_widget.ui_notes.conversationScrollArea.verticalScrollBar().setValue(
            self.note_widget.ui_notes.conversationScrollArea.verticalScrollBar().maximum())

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


class Ui_snapshotItemWidget(QtGui.QWidget, ui_item_snapshot.Ui_snapshotItem):
    def __init__(self, sobject, stype, process, context, snapshot, info, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'snapshot'
        self.sobject = sobject
        self.stype = stype
        self.process = process
        self.context = context
        self.snapshot = None
        self.info = info
        self.tree_item = tree_item

        # self.item_info = {}
        # print self.sobject.process

        # self.row = row
        self.files = {}
        # print self.tree_item

        if snapshot:
            self.snapshot = snapshot[0].snapshot
            self.files = snapshot[0].files
        hidden = ['icon', 'web', 'playblast']

        if self.snapshot:
            abs_path = gf.get_abs_path(self)

            if abs_path:
                if not os.path.exists(abs_path):
                    self.setDisabled(True)
            else:
                self.setDisabled(True)

            self.commentLabel.setText(gf.to_plain_text(self.snapshot['description'], 80))
            self.dateLabel.setText(self.snapshot['timestamp'])
            self.authorLabel.setText(self.snapshot['login'] + ':')
            self.verRevLabel.setText(gf.get_ver_rev(self.snapshot['version'], self.snapshot['revision']))

            for key, fl in self.files.iteritems():
                if key not in hidden:
                    if self.snapshot.get('repo'):
                        self.sizeLabel.setStyleSheet(self.get_repo_color())
                    if not self.isEnabled():
                        self.fileNameLabel.setText('{0}, (File Missing)'.format(fl[0]['file_name']))
                    else:
                        self.fileNameLabel.setText(fl[0]['file_name'])
                    self.sizeLabel.setText(gf.sizes(fl[0]['st_size']))
        else:
            self.fileNameLabel.setText('Versionless for {0} not found'.format(self.context))
            self.commentLabel.setText('Check this snapshot, and update versionless')
            self.dateLabel.deleteLater()
            self.sizeLabel.deleteLater()
            self.authorLabel.deleteLater()

            # if snapshot:
            #     self.item_info = self.snapshot

    def get_repo_color(self):
        config = cfg.Controls.get_checkin()
        if config:
            if self.snapshot['repo'] == 'asset_base_dir':
                repo = gf.get_value_from_config(config, 'assetBaseDirColorToolButton', 'QToolButton')
            if self.snapshot['repo'] == 'win32_local_repo_dir':
                repo = gf.get_value_from_config(config, 'localRepoDirColorToolButton', 'QToolButton')
            if self.snapshot['repo'] == 'win32_sandbox_dir':
                repo = gf.get_value_from_config(config, 'sandboxDirColorToolButton', 'QToolButton')
            if self.snapshot['repo'] == 'win32_client_repo_dir':
                repo = gf.get_value_from_config(config, 'clientRepoDirColorToolButton', 'QToolButton')
            if self.snapshot['repo'] == 'custom_asset_dir':
                repo = gf.get_value_from_config(config, 'customRepoDirColorToolButton', 'QToolButton')

            color = repo[repo.find('rgb'):repo.find('rgb') + 16]
            repo_colors = color.replace('rgb(', '').replace(')', '').split(',')
        else:
            repo_colors = [96, 96, 96]

        stylesheet = 'QLabel{background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(%s, %s, %s, 96));' \
                     'border - bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));' \
                     'padding: 0px;}' % tuple(repo_colors)

        return stylesheet

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


class Ui_childrenItemWidget(QtGui.QWidget, ui_item_children.Ui_childrenItem):
    def __init__(self, sobject, stype, child, info, tree_item, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)
        self.type = 'child'
        self.sobject = sobject
        self.stype = stype
        # print self.stype.info
        self.child = child
        self.info = info
        self.tree_item = tree_item
        self.tree_item.setExpanded = self.tree_item_set_expanded_override

        self.tree_widget = parent
        self.project = self.tree_widget.project

        name = '{0} ({1})'.format(self.stype.info.get('title'), self.child.get('from'))
        self.childrenToolButton.setText(name)
        # self.childrenToolButton.setStyleSheet("QToolButton {color: blue;background-color: transparent;}")

        self.set_style()
        self.controls_actions()

    def tree_item_set_expanded_override(self, state):
        if state:
            self.add_child_sobjects()
        self.tree_item.treeWidget().setItemExpanded(self.tree_item, state)

    def controls_actions(self):
        self.childrenToolButton.clicked.connect(self.add_child_sobjects)

        # Override events
        # self.tree_item.setExpanded = self.tree_item_set_expanded

    def set_style(self):
        # tab_label = QtGui.QLabel(tab_name)
        # tab_label.setAlignment(QtCore.Qt.AlignCenter)
        # tab_color = stype.info['color']
        button_color = '0000ff'

        if button_color:
            effect = QtGui.QGraphicsDropShadowEffect(self.childrenToolButton)
            # blur = QtGui.QGraphicsBlurEffect(tab_label)
            # QtGui.QGraphicsItemAnimation

            t_c = gf.hex_to_rgb(button_color, alpha=255, tuple=True)
            # print t_c
            effect.setOffset(1, 1)
            effect.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
            # blur.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
            # print blur.strength()
            # blur.setStrength(.5)
            # blur.setBlurRadius()
            # print blur.blurHints()
            # print blur.blurRadius()
            # blur.setBlurRadius(2)

            effect.setBlurRadius(20)
            self.childrenToolButton.setGraphicsEffect(effect)
            # tab_label.setGraphicsEffect(blur)

            # tab_color_rgb = gf.hex_to_rgb(button_color, alpha=8)
            self.childrenToolButton.setStyleSheet('QToolButton {background-color: transparent;}')

    def add_child_sobjects(self):
        if not self.info['is_expanded']:
            self.info['is_expanded'] = True

            server = tc.server_start()
            builded_process = server.build_search_type(self.child.get('from'), self.project.info.get('code'))

            filters = [(self.child.get('from_col'), self.sobject.info.get('code'))]

            assets = server.query(builded_process, filters)

            if self.stype.pipeline:
                process = self.stype.pipeline.process.keys()
            else:
                process = []

            sobjects = tc.get_sobjects(process, assets, project_code=self.project.info.get('code'))
            stype = self.stype

            for sobject in sobjects.itervalues():
                item_info = {
                    'relates_to': self.info['relates_to'],
                    'is_expanded': False,
                }
                gf.add_sobject_item(self.tree_item, self.tree_widget, sobject, stype, process, item_info)

            self.tree_item.setExpanded(True)

    def get_skey(self, skey=False, only=False, parent=False):
        pass

    def get_description(self):
        return 'No Description for this item "{0}"'.format('AZAZAZ')


# class Ui_itemWidget(QtGui.QWidget, ui_item.Ui_item):
#     def __init__(self, row, sobject, tree_item, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#
#         self.setupUi(self)
#         self.type = 'sobject'
#         self.relates_to = parent.relates_to
#         self.tree_widget = parent
#         self.row = row
#         self.tree_item = tree_item
#         # self.item_info = {}
#         self.sobject = sobject
#
#         if self.sobject:
#             self.fill_sobject_info()
#
#         self.controls_actions()
#         self.parents_stypes = None
#         self.children_stypes = None
#         self.check_for_children()
#
#         # fill item info
#         # self.item_info['description'] = self.sobject.info['description']
#
#     def controls_actions(self):
#         self.tasksToolButton.clicked.connect(lambda: self.create_tasks_window())
#         self.relationsToolButton.clicked.connect(self.check_for_children)
#
#     def fill_sobject_info(self):
#         title = 'No Title'
#         if self.sobject.info.get('name'):
#             title = self.sobject.info.get('name')
#         elif self.sobject.info.get('title'):
#             title = self.sobject.info.get('title')
#         elif self.sobject.info.get('code'):
#             title = self.sobject.info.get('code')
#
#         self.fileNameLabel.setText(title)
#         self.commentLabel.setText(gf.to_plain_text(self.sobject.info.get('description')))
#         # TODO correct date time
#         # dateLabel = QtCore.QDateTime.fromString(self.sobject.info['timestamp'], 'yyyy-MM-dd HH:mm:ss')
#         self.dateLabel.setText(self.sobject.info.get('timestamp'))
#
#     def prnt(self):
#         # shot_tab = env.Inst.ui_check_tree[self.relates_to]['cgshort/shot']
#         print(env.Inst.ui_check_tabs[self.relates_to].sObjTabWidget.count())
#         tab_wdg = env.Inst.ui_check_tabs[self.relates_to].sObjTabWidget
#         for i in range(tab_wdg.count()):
#             print tab_wdg.widget(i).objectName()
#             if tab_wdg.widget(i).objectName() == 'cgshort/shot':
#                 tab_wdg.setCurrentIndex(i)
#
#         tree_wdg = tab_wdg.currentWidget()
#
#         tree_wdg.searchLineEdit.setText('SCENES00001')
#         tree_wdg.searchOptionsGroupBox.searchParentCodeRadioButton.setChecked(True)
#         tree_wdg.add_items_to_results('SCENES00001')
#
#     def check_for_children(self):
#
#         if self.tree_widget.stype.schema.parents:
#             self.parents_stypes = self.tree_widget.stype.schema.parents
#             for parent in self.tree_widget.stype.schema.parents:
#                 parent_code = parent.get('to')
#                 parent_title = self.tree_widget.project.stypes.get(parent_code)
#                 if parent_title:
#                     parent_title = parent_title.info.get('title')
#                 else:
#                     parent_title = parent_code
#                 parent_action = QtGui.QAction(parent_title, self.relationsToolButton)
#                 self.relationsToolButton.addAction(parent_action)
#
#         if self.tree_widget.stype.schema.children:
#             self.children_stypes = self.tree_widget.stype.schema.children
#             child_sep = QtGui.QAction('Children', self.relationsToolButton)
#             child_sep.setSeparator(True)
#             self.relationsToolButton.addAction(child_sep)
#
#             for child in self.tree_widget.stype.schema.children:
#                 child_code = child.get('from')
#                 child_title = self.tree_widget.project.stypes.get(child_code)
#                 if child_title:
#                     child_title = child_title.info.get('title')
#                 else:
#                     child_title = child_code
#                 child_action = QtGui.QAction(child_title, self.relationsToolButton)
#                 self.relationsToolButton.addAction(child_action)
#
#         if not (self.tree_widget.stype.schema.children or self.tree_widget.stype.schema.parents):
#             self.relationsToolButton.hide()
#
#             # print self.sobject.info
#             # server = tc.server_start()
#             # RESHENO SOBSTVENNY CLASS FOR SCHEMA!
#             # print server.get_all_children('sthpw/search_object?id=86', 'cgshort/shot')
#             # print server.get_parent_type(['cgshort/scenes'])
#             # print server.build_search_type('the_pirate/scenes')
#             # print server.get_related_types('cgshort/scenes')
#
#             # print server.get_connected_sobjects('sthpw/search_object?id=86')
#             # print server.get_all_children(self.sobject.info['__search_key__'], 'sthpw/snapshot')
#
#     def create_tasks_window(self):
#         try:
#             self.tasks_widget.show()
#         except:
#             # print(self.item_info)
#             # current_tab_context = env.Inst.ui_checkout_tree[self.sobject.info['pipeline_code']].context_items
#             # print(env.Inst.ui_checkout_tree)
#             self.tasks_widget = tasks_widget.Ui_tasksWidgetMain(self.sobject, self)
#             self.tasks_widget.show()
#
#     def get_context(self, process=False, custom=None):
#         return ''
#
#     def get_skey(self, skey=False, only=False, parent=False):
#         """skey://cgshort/props?project=the_pirate&code=PROPS00001"""
#         if parent or only:
#             return self.sobject.info['__search_key__']
#         if skey:
#             return 'skey://' + self.sobject.info['__search_key__']
#
#     def get_description(self):
#         return self.sobject.info['description']
#
#     def update_description(self, new_description):
#         self.sobject.info['description'] = new_description
#         self.commentLabel.setText(new_description)
#
#
# class Ui_childrenItemWidget(QtGui.QWidget, ui_item_children.Ui_childrenItem):
#     def __init__(self, child, parent_widget, tree_item, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#
#         self.setupUi(self)
#         self.tree_widget = parent
#         self.project = env.Inst.projects[self.tree_widget.current_project]
#         self.type = 'child'
#         self.tree_item = tree_item
#         self.stype = self.tree_widget
#         self.child = child
#         self.parent_widget = parent_widget
#         # print self.child
#         name = '{0} ({1})'.format(self.project.stypes[self.child.get('from')].info.get('title'), self.child.get('from'))
#         # print name
#         self.childrenToolButton.setText(name)
#         # self.childrenToolButton.setStyleSheet("QToolButton {color: blue;background-color: transparent;}")
#
#         self.childrenToolButton.clicked.connect(self.prnt)
#         self.set_style()
#
#     def set_style(self):
#         # tab_label = QtGui.QLabel(tab_name)
#         # tab_label.setAlignment(QtCore.Qt.AlignCenter)
#         # tab_color = stype.info['color']
#         button_color = '0000ff'
#
#         if button_color:
#             effect = QtGui.QGraphicsDropShadowEffect(self.childrenToolButton)
#             # blur = QtGui.QGraphicsBlurEffect(tab_label)
#             # QtGui.QGraphicsItemAnimation
#
#             t_c = gf.hex_to_rgb(button_color, alpha=255, tuple=True)
#             # print t_c
#             effect.setOffset(1, 1)
#             effect.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
#             # blur.setColor(QtGui.QColor(t_c[0], t_c[1], t_c[2], t_c[3]))
#             # print blur.strength()
#             # blur.setStrength(.5)
#             # blur.setBlurRadius()
#             # print blur.blurHints()
#             # print blur.blurRadius()
#             # blur.setBlurRadius(2)
#
#             effect.setBlurRadius(20)
#             self.childrenToolButton.setGraphicsEffect(effect)
#             # tab_label.setGraphicsEffect(blur)
#
#             # tab_color_rgb = gf.hex_to_rgb(button_color, alpha=8)
#             self.childrenToolButton.setStyleSheet('QToolButton {background-color: transparent;}')
#
#     def prnt(self):
#         # self.tree_item.addChild(QtGui.QTreeWidgetItem(0, 'AZZA'))
#         # QtGui.QTreeWidgetItem.treeWidget()
#         # print self.project.stypes['cgshort/scenes'].info
#         # print self.project.stypes['cgshort/scenes'].pipeline
#         # print self.project.stypes['cgshort/scenes'].pipeline.process
#         # print self.project.stypes['cgshort/scenes'].pipeline.info
#         # print self.project.stypes['cgshort/scenes'].schema
#         # print self.project.stypes['cgshort/scenes'].schema.info
#         # print self.project.stypes['cgshort/scenes'].schema.parents
#         # print self.project.stypes['cgshort/scenes'].schema.children
#
#         # ls = [{'code': u'SCENES00002', 'description': u'new ep', 'episode_code': u'EPISODE00001', 's_status': None,
#         #        'pipeline_code': u'the_pirate/scenes', 'keywords': None, 'sets_code': None, 'id': 2, 'name': u'ep01sc01',
#         #        '__search_key__': u'cgshort/scenes?project=the_pirate&code=SCENES00002',
#         #        'timestamp': '2016-02-12 21:29:47', 'login': None},
#         #       {'code': u'SCENES00003', 'description': None, 'episode_code': u'EPISODE00002', 's_status': None,
#         #        'pipeline_code': u'the_pirate/scenes', 'keywords': None, 'sets_code': None, 'id': 3,
#         #        'name': u'ep002sc001', '__search_key__': u'cgshort/scenes?project=the_pirate&code=SCENES00003',
#         #        'timestamp': '2016-07-13 15:36:10', 'login': None},
#         #       {'code': u'SCENES00004', 'description': None, 'episode_code': u'EPISODE00002', 's_status': None,
#         #        'pipeline_code': u'the_pirate/scenes', 'keywords': None, 'sets_code': None, 'id': 4,
#         #        'name': u'ep002sc002', '__search_key__': u'cgshort/scenes?project=the_pirate&code=SCENES00004',
#         #        'timestamp': '2016-07-13 15:36:37', 'login': None}]
#
#         server = tc.server_start()
#         builded_process = server.build_search_type(self.child.get('from'), self.project.info.get('code'))
#
#         filters = [(self.child.get('from_col'), self.parent_widget.sobject.info.get('code'))]
#
#         print self.child, '!!!CHILD!!!'
#         print filters, '!!!FILTERS!!!'
#
#         assets = server.query(builded_process, filters)
#
#         print(assets)
#
#         # print(self.project.stypes[self.child.get('from')].pipeline.process.keys())
#
#         if self.project.stypes[self.child.get('from')].pipeline:
#             process = self.project.stypes[self.child.get('from')].pipeline.process.keys()
#         else:
#             process = []
#
#         sobjects = tc.get_sobjects(process, assets, project_code=self.project.info.get('code'))
#         print sobjects, '!!!SOBJECTS!!!'
#         print process, '!!!PROCESS!!!'
#
#         gf.add_sub_items_to_tree(
#             self.tree_widget,
#             self.tree_item.treeWidget(),
#             sobjects,
#             process,
#             searh_all=True,
#             child_widget_item=self,
#         )
#         self.tree_item.setExpanded(True)
#
#     def get_skey(self, skey=False, only=False, parent=False):
#         pass
#
#     def get_description(self):
#         return 'No Description for this item "{0}"'.format('AZAZAZ')
#
#
# class Ui_processItemWidget(QtGui.QWidget, ui_item_process.Ui_processItem):
#     def __init__(self, row, process, sobject, tree_item, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#
#         self.setupUi(self)
#         self.type = 'process'
#         self.tree_item = tree_item
#         # print(tree_item.text(0))
#         # self.item_info = {}
#         self.sobject = sobject
#         self.process = process
#
#         self.row = row
#
#         self.notesToolButton.clicked.connect(lambda: self.create_notes_widget())
#
#         # self.item_info[
#         #     'description'] = 'This is {0} process item, there is no description, better click on Notes button'.format(
#         #     self.process)
#
#     def create_notes_widget(self):
#         self.note_widget = notes_widget.Ui_notesOwnWidget(self)
#         self.note_widget.setWindowTitle(
#             'Notes for: {0}, with process: {1}'.format(self.sobject.info['name'], self.process))
#         self.sobject.info['process'] = self.process
#         self.sobject.info['context'] = self.process
#         # print(self.sobject.info)
#         if self.sobject:
#             self.note_widget.ui_notes.task_item = self.sobject
#             self.note_widget.ui_notes.fill_notes()
#         self.note_widget.show()
#         self.note_widget.ui_notes.conversationScrollArea.verticalScrollBar().setValue(
#             self.note_widget.ui_notes.conversationScrollArea.verticalScrollBar().maximum())
#
#     def prnt(self):
#         # print(str(self.item_index))
#         # print(self.tree_item.parent().setExpanded(False))
#         print(self.sobject.process)
#         self.sobject.update_snapshots()
#         print(self.sobject.process)
#
#     def get_context(self, process=False, custom=None):
#         if process:
#             if custom:
#                 return '{0}/{1}'.format(self.process, custom)
#             else:
#                 return self.process
#                 # else:
#                 #     return ''
#
#     def get_description(self):
#         return 'No Description for this item "{0}"'.format(self.process)
#
#     def get_skey(self, skey=False, only=False, parent=False):
#         if parent or only:
#             return self.sobject.info['__search_key__']
#         if skey:
#             return 'skey://' + self.sobject.info['__search_key__']
#
#
# class Ui_snapshotItemWidget(QtGui.QWidget, ui_item_snapshot.Ui_snapshotItem):
#     def __init__(self, row, snapshot, sobject, tree_item, parent=None):
#         super(self.__class__, self).__init__(parent=parent)
#
#         self.setupUi(self)
#         self.type = 'snapshot'
#         self.tree_item = tree_item
#         # self.item_info = {}
#         self.sobject = sobject
#         # print self.sobject.process
#         self.snapshot = None
#         self.row = row
#         self.files = {}
#
#         if snapshot:
#             self.snapshot = snapshot.values()[0].snapshot
#             self.files = snapshot.values()[0].files
#         hidden = ['icon', 'web', 'playblast']
#
#         if self.snapshot:
#             abs_path = gf.get_abs_path(self)
#             if abs_path:
#                 if not os.path.exists(abs_path):
#                     self.setDisabled(True)
#             else:
#                 self.setDisabled(True)
#
#             self.commentLabel.setText(gf.to_plain_text(self.snapshot['description'], 80))
#             self.dateLabel.setText(self.snapshot['timestamp'])
#             self.authorLabel.setText(self.snapshot['login'] + ':')
#             self.verRevLabel.setText(gf.get_ver_rev(self.snapshot['version'], self.snapshot['revision']))
#
#             for key, fl in self.files.iteritems():
#                 if key not in hidden:
#                     if self.snapshot.get('repo'):
#                         self.sizeLabel.setStyleSheet(self.get_repo_color())
#                     self.fileNameLabel.setText(fl[0]['file_name'])
#                     self.sizeLabel.setText(gf.sizes(fl[0]['st_size']))
#         else:
#             self.fileNameLabel.setText('Versionless not found')
#             self.commentLabel.setText('Check this snapshot, and update versionless')
#             self.dateLabel.deleteLater()
#             self.sizeLabel.deleteLater()
#             self.authorLabel.deleteLater()
#
#             # if snapshot:
#             #     self.item_info = self.snapshot
#
#     def get_repo_color(self):
#         config = env.Conf.get_checkin()
#         if config:
#             if self.snapshot['repo'] == 'asset_base_dir':
#                 repo = gf.get_value_from_config(config, 'assetBaseDirColorToolButton', 'QToolButton')
#             if self.snapshot['repo'] == 'win32_local_repo_dir':
#                 repo = gf.get_value_from_config(config, 'localRepoDirColorToolButton', 'QToolButton')
#             if self.snapshot['repo'] == 'win32_sandbox_dir':
#                 repo = gf.get_value_from_config(config, 'sandboxDirColorToolButton', 'QToolButton')
#             if self.snapshot['repo'] == 'win32_client_repo_dir':
#                 repo = gf.get_value_from_config(config, 'clientRepoDirColorToolButton', 'QToolButton')
#             if self.snapshot['repo'] == 'custom_asset_dir':
#                 repo = gf.get_value_from_config(config, 'customRepoDirColorToolButton', 'QToolButton')
#
#             repo_colors = repo.replace('background-color:rgb(', '').replace(')', '').split(',')
#         else:
#             repo_colors = [96, 96, 96]
#         stylesheet = 'QLabel{background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(%s, %s, %s, 96));' \
#                      'border - bottom: 2px solid qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255, 255, 255, 0), stop:1 rgba(128, 128, 128, 175));' \
#                      'padding: 0px;}' % tuple(repo_colors)
#
#         return stylesheet
#
#     def get_context(self, process=False, custom=None):
#         if process:
#             if custom:
#                 return '{0}/{1}'.format(self.snapshot['process'], custom)
#             else:
#                 return self.snapshot['process']
#         else:
#             context = self.snapshot['context'].split('/')[-1]
#             if context == self.snapshot['process']:
#                 context = ''
#             return context
#
#     def get_skey(self, skey=False, only=False, parent=False):
#         """skey://sthpw/snapshot?code=SNAPSHOT00000028"""
#         if self.snapshot:
#             if only:
#                 return self.snapshot['__search_key__']
#             if skey:
#                 return 'skey://{0}'.format(self.snapshot['__search_key__'])
#             if parent:
#                 return self.sobject.info['__search_key__']
#         else:
#             return 'No skey for this item!'
#
#     def get_description(self):
#         if self.snapshot:
#             return self.snapshot['description']
#         else:
#             return 'No Description for this item!'
#
#     def update_description(self, new_description):
#         self.snapshot['description'] = new_description
#         self.commentLabel.setText(new_description)
