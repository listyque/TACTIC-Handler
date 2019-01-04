# module Adding sObject Classes
# file ui_addsobject_classes.py
# Adding new sObject window

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

import json
from thlib.environment import env_inst, env_tactic, env_write_config, env_read_config
import thlib.global_functions as gf
import thlib.tactic_classes as tc
import thlib.tactic_widgets as tw
import thlib.tactic_query as tq
import thlib.ui_classes.ui_tactic_widgets_classes as twc
import thlib.ui.misc.ui_db_table_editor as ui_db_table_editor


class Ui_editDBTableWidget(QtGui.QMainWindow, ui_db_table_editor.Ui_editDBTable):
    def __init__(self, stype, parent_stype=None, item=None, view='edit', search_key=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.setupUi(self)

        self.item = item
        self.sobject = self.item.get_sobject()
        self.stype = stype
        self.parent_stype = parent_stype
        self.search_type = self.stype.info.get('code')

        self.view = view

        self.search_key = search_key
        self.parent_search_key = None

        if self.item:
            if not search_key:
                self.search_key = self.item.get_search_key()
            self.parent_search_key = self.item.get_parent_search_key()

        # self.grid_layout = QtGui.QGridLayout(self)

        self.create_ui()

    def create_ui(self):

        self.setWindowModality(QtCore.Qt.WindowModal)

        self.fill_table_widget()

    def fill_table_widget(self, pipeline=None):

        # def get_current_process_info(self):
        #     pipeline = self.get_current_process_pipeline()
        #     process_info = None
        #     if pipeline:
        #         process_info = pipeline.process.get(self.process)
        #
        #     return process_info
        #
        # self.tablesTreeWidget.addTopLevelItem(QtGui.QTreeWidgetItem())

        def recursive_add_sub_processes(ppln):
            for child_process in ppln.get_all_processes_names():
                subprocess_item = QtGui.QTreeWidgetItem()
                subprocess_item.setText(0, child_process)
                process_item.addChild(subprocess_item)

        # getting all possible processes here
        pipeline_code = self.sobject.info.get('pipeline_code')
        if pipeline_code and self.stype.pipeline:
            pipeline = self.stype.pipeline.get(pipeline_code)

        for process in pipeline.get_all_processes_names():
            process_item = QtGui.QTreeWidgetItem()
            process_item.setText(0, process)
            self.tablesTreeWidget.addTopLevelItem(process_item)
            process_info = pipeline.process.get(process)

            if process_info.get('type') == 'hierarchy':
                workflow = self.stype.get_workflow()
                child_pipeline = workflow.get_child_pipeline_by_process_code(pipeline, process)

                recursive_add_sub_processes(child_pipeline)

        # print self.sobject.process.items()

        process = self.sobject.get_process('modeling')
        contexts = process.get_contexts()
        if contexts:
            for key, val in contexts.items():
                # print key, val

                for snapshot in val.get_versions().values():
                    # from pprint import pprint
                    # pprint(snapshot.get_snapshot())
                    self.fill_edit_table_tree_widget(snapshot.get_snapshot())

    def add_edit_table_tree_widget_header(self, dicts_list):

        self.editTableWidget.setColumnCount(len(dicts_list))

        for i, (key, val) in enumerate(sorted(dicts_list.items())):
            # self.editTableWidget.headerItem().setText(i, key)
            item = QtGui.QTableWidgetItem()
            item.setText(key)
            self.editTableWidget.setHorizontalHeaderItem(i, item)
            # top_item.setText(i, str(val))
        # self.tableEditorTreeWidget.addTopLevelItem(top_item)

    def fill_edit_table_tree_widget(self, dicts_list):
        print dicts_list

        self.editTableWidget.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.editTableWidget.setAlternatingRowColors(True)
        self.editTableWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.editTableWidget.setGridStyle(QtCore.Qt.DashLine)

        self.add_edit_table_tree_widget_header(dicts_list)
        # self.editTableWidget.clear()

        self.editTableWidget.setRowCount(10)
        vertical_item = QtGui.QTableWidgetItem()
        vertical_item.setText('aas')
        self.editTableWidget.setVerticalHeaderItem(0, vertical_item)

        for i, (key, val) in enumerate(sorted(dicts_list.items())):
            item = QtGui.QTableWidgetItem()
            item.setText(key)
            self.editTableWidget.setHorizontalHeaderItem(i, item)

            # attr_val = cmds.getAttr('{0}.{1}'.format(from_node, attr))
            value_item = QtGui.QTableWidgetItem()
            value_item.setText(str(val))
            # value_item.setData(1, [str(from_node), attr])
            self.editTableWidget.setItem(0, i, value_item)


class Ui_addTacticSobjectWidget(QtGui.QDialog):
    def __init__(self, stype, parent_stype=None, item=None, view='insert', search_key=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        # TODO get title from within

        self.item = item
        self.stype = stype
        self.parent_stype = parent_stype
        self.search_type = self.stype.info.get('code')

        self.view = view

        self.search_key = search_key
        self.parent_search_key = None

        if self.item:
            if not search_key:
                self.search_key = self.item.get_search_key()
            self.parent_search_key = self.item.get_parent_search_key()

        self.grid_layout = QtGui.QGridLayout(self)

        self.create_ui()

        # self.add_multiple()

    def add_multiple(self):
        self.wnd = QtGui.QDialog(self)
        self.wnd.show()
        self.l = QtGui.QVBoxLayout()

        self.b = QtGui.QPushButton('Begin')

        self.wnd.setLayout(self.l)

        self.l.addWidget(self.b)
        self.b.clicked.connect(self.begin_inst)

    def begin_inst(self):

        # tactic_edit_widget = tw.TacticEditWdg(wdg_dict)
        print self.stype.get_code()
        # tactic_edit_widget.set_stype(self.stype)

        # {u'episode_code': u'EPISODE00010', u'name': u'test'}

        lst = {}
        for i, ep in enumerate(sorted(lst.keys())):
            print ep, i, 'out of:', len(lst)
            data = {'name': ep}
            wd = {u'input_prefix': u'insert', u'element_titles': [u'Preview', u'Name', u'Description', u'Keywords'], u'title': u'', u'element_names': [u'preview', u'name', u'description', u'keywords'], u'kwargs': {u'search_type': u'melnitsapipeline/episode', u'code': u'', u'title_width': u'', u'parent_key': None, u'title': u'', u'default': u'', u'search_key': u'', u'input_prefix': u'insert', u'config_base': u'', u'single': u'', u'cbjs_edit_path': u'', u'access': u'', u'width': u'', u'show_header': u'', u'cbjs_cancel': u'', u'mode': u'insert', u'cbjs_insert_path': u'', u'ignore': u'', u'show_action': u'', u'search_id': u'', u'view': u'insert'}, u'element_descriptions': [None, u'Name', u'Description', u'Keywords'], u'mode': u'insert', u'security_denied': False}
            tactic_edit_widget = tw.TacticEditWdg(wd)
            tactic_edit_widget.set_stype(self.stype.project.get_stypes()['melnitsapipeline/episode'])

            episode_sobj = tactic_edit_widget.commit(data)
            print episode_sobj
            for j, sc in enumerate(sorted(lst[ep])):
                print sc, j, 'out of:', len(ep)

                sc['episode_code'] = episode_sobj['code']

                scene_sobj = self.edit_window.tactic_widget.commit(sc)
                print scene_sobj

    def create_ui(self):

        self.setWindowModality(QtCore.Qt.WindowModal)

        self.create_loading_label()
        self.toggle_loading_label()

        kwargs_edit = {
            'args': {
                'input_prefix': 'edit',
                'search_key': self.search_key,
                'parent_key': self.parent_search_key,
                'view': 'edit',
            },
            'search_type': self.search_type,
            'project': self.stype.project.get_code(),
        }

        kwargs_insert = {
            'args': {
                'mode': 'insert',
                'input_prefix': 'insert',
                'parent_key': self.parent_search_key,
                'search_type': self.search_type,
                'view': 'insert',
            },
            'search_type': self.search_type,
            'project': self.stype.project.get_code(),
        }

        if self.view == 'edit':
            kwargs = kwargs_edit
        else:
            kwargs = kwargs_insert

        self.get_widgets(kwargs)
        self.setSizeGripEnabled(True)
        self.set_title()

    def create_widgets_ui(self, result_dict):
        self.toggle_loading_label()
        
        input_widgets_list = []
        if self.item:
            result_dict['EditWdg']['sobject'] = self.item.get_sobject()
            result_dict['EditWdg']['parent_sobject'] = self.item.get_parent_sobject()

        tactic_edit_widget = tw.TacticEditWdg(result_dict['EditWdg'])
        tactic_edit_widget.set_stype(self.stype)

        self.edit_window = twc.QtTacticEditWidget(
            tactic_widget=tactic_edit_widget,
            qt_widgets=input_widgets_list,
            stype=self.stype,
            parent=self
        )

        for widget_dict in result_dict['InputWidgets']:
            tactic_widget_name = tw.get_widget_name(widget_dict['class_name'], 'input')

            widget_dict['sobject'] = result_dict['EditWdg'].get('sobject')
            widget_dict['parent_sobject'] = result_dict['EditWdg'].get('parent_sobject')

            if not tactic_widget_name:
                tactic_widget_name = 'TacticCurrentCheckboxWdg'

            tactic_widget = getattr(tw, tactic_widget_name)
            qt_widget = getattr(twc, 'Q{0}'.format(tactic_widget_name))

            widget_dict['stype'] = self.stype

            tactic_widget_instance = tactic_widget(options_dict=widget_dict)
            qt_widget_instance = qt_widget(tactic_widget=tactic_widget_instance, parent=self.edit_window)

            input_widgets_list.append(qt_widget_instance)

        self.grid_layout.addWidget(self.edit_window)

        self.edit_window.create_ui()
        self.readSettings()

    def create_loading_label(self):
        self.loading_label = QtGui.QLabel()
        self.loading_label.setText('Loading...')
        self.loading_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.loading_label.setVisible(False)

        self.grid_layout.addWidget(self.loading_label, 0, 0)

    def toggle_loading_label(self):
        if self.loading_label.isVisible():
            self.loading_label.setVisible(False)
        else:
            self.loading_label.setVisible(True)

    def get_widgets(self, kwargs):

        def query_widgets_agent():
            return self.query_widgets(kwargs)

        server_thread_pool = QtCore.QThreadPool()
        server_thread_pool.setMaxThreadCount(env_tactic.max_threads())
        env_inst.set_thread_pool(server_thread_pool, 'server_query/server_thread_pool')

        worker = gf.get_thread_worker(
            query_widgets_agent,
            env_inst.get_thread_pool('server_query/server_thread_pool'),
            self.create_widgets_ui,
            gf.error_handle
        )

        worker.start()

    @staticmethod
    def query_widgets(kwargs):
        code = tq.prepare_serverside_script(tq.query_EditWdg, kwargs, return_dict=True)
        result = tq.get_result(tc.server_start(project=kwargs['project']).execute_python_script('', kwargs=code))

        return json.loads(result)

    def set_title(self):
        stype_tytle = self.stype.info.get('title')
        stype_code = self.stype.info.get('code')
        if stype_tytle:
            title = stype_tytle.capitalize()
        else:
            title = 'Unknown'

        self.setWindowTitle('Adding new SObject {0} ({1})'.format(title, stype_code))

    def add_new_tab(self, sobject):
        checkin_out_tab = self.get_checkin_out_tab()
        search_widget = checkin_out_tab.get_search_widget()

        tab_title = sobject.get('name')
        if not tab_title:
            tab_title = sobject.get('code')
        elif not tab_title:
            tab_title = 'New created'

        search_widget.add_tab(
            search_title=tab_title,
            filters=[('code', '=', sobject.get('code'))],
        )

    def get_checkin_out_tab(self):

        stype = self.parent_stype
        if not stype:
            stype = self.stype

        return env_inst.get_check_tree(
            project_code=stype.project.info.get('code'),
            tab_code='checkin_out',
            wdg_code=stype.info.get('code'))

    def refresh_results(self):
        checkin_out_tab = self.get_checkin_out_tab()
        checkin_out_tab.refresh_current_results()
        # tree_wdg = checkin_out_tab.get_current_tree_widget()
        #
        # tree_wdg.update_current_items_trees()

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'geometry': None,
                'edit_widndow_settings_dict': self.edit_window.get_settings_dict(),
            }
        geo = settings_dict['geometry']
        if geo:
            self.setGeometry(QtCore.QRect(geo[0], geo[1], geo[2], geo[3]))
        else:
            self.resize(600, 500)
        self.edit_window.set_settings_from_dict(settings_dict['edit_widndow_settings_dict'])

    def get_settings_dict(self):

        settings_dict = {
            'geometry': self.geometry().getRect(),
            'edit_widndow_settings_dict': self.edit_window.get_settings_dict(),
        }

        return settings_dict

    def readSettings(self):
        """
        Reading Settings
        """
        self.set_settings_from_dict(
            env_read_config(
                filename='ui_addsobject',
                unique_id='ui_main',
                long_abs_path=True
            )
        )

    def writeSettings(self):
        """
        Writing Settings
        """
        # TODO need to decide save settings per project, or per sobject, or globally

        env_write_config(
            self.get_settings_dict(),
            filename='ui_addsobject',
            unique_id='ui_main',
            long_abs_path=True)

    def closeEvent(self, event):
        self.writeSettings()
        event.accept()


# import ast
# import maya.cmds as cmds
# import PyQt4.QtGui as QtGui
# import PyQt4.QtCore as QtCore


class QtWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.CenterSplitter = QtGui.QSplitter()
        self.CenterSplitter.setOrientation(QtCore.Qt.Horizontal)

        self.LeftSplitter = QtGui.QSplitter(self.CenterSplitter)
        self.LeftSplitter.setOrientation(QtCore.Qt.Vertical)

        self.rightSplitter = QtGui.QSplitter(self.CenterSplitter)
        self.rightSplitter.setOrientation(QtCore.Qt.Vertical)
        self.layout.addWidget(self.CenterSplitter, 0, 0, 1, 0)

        self.create_trees()
        self.create_tables()
        self.create_button()
        self.create_options()

        self.controls_actions()

    def create_options(self):
        self.shapes_checkbox = QtGui.QCheckBox()
        self.shapes_checkbox.setText('Shapes')
        self.shapes_checkbox.setChecked(True)
        self.transforms_checkbox = QtGui.QCheckBox()
        self.transforms_checkbox.setText('Transforms')
        self.transforms_checkbox.setChecked(True)

        self.filter_edit = QtGui.QLineEdit()

        self.layout.addWidget(self.shapes_checkbox, 3, 0, 1, 1)
        self.layout.addWidget(self.transforms_checkbox, 3, 1, 1, 1)

        self.layout.addWidget(self.filter_edit, 4, 0, 1, 1)

    def create_trees(self):
        self.from_tree = QtGui.QTreeWidget(self.LeftSplitter)
        self.from_tree.setHeaderHidden(True)

        self.to_tree = QtGui.QTreeWidget(self.rightSplitter)
        self.to_tree.setHeaderHidden(True)

    def create_tables(self):
        self.edit_attrs_table = QtGui.QTableWidget(self.LeftSplitter)
        self.edit_attrs_table.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.edit_attrs_table.setAlternatingRowColors(True)
        self.edit_attrs_table.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.edit_attrs_table.setGridStyle(QtCore.Qt.DashLine)

        self.edit_attrs_to_table = QtGui.QTableWidget(self.rightSplitter)
        self.edit_attrs_to_table.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.edit_attrs_to_table.setAlternatingRowColors(True)
        self.edit_attrs_to_table.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.edit_attrs_to_table.setGridStyle(QtCore.Qt.DashLine)

    def add_table_header(self):
        self.edit_attrs_table.setColumnCount(2)
        item = QtGui.QTableWidgetItem()
        item.setText('Attribute')
        self.edit_attrs_table.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        item.setText('Value')
        self.edit_attrs_table.setHorizontalHeaderItem(1, item)

        self.edit_attrs_table.setRowCount(0)

    def create_button(self):

        self.get_from = QtGui.QPushButton('FROM')
        self.get_to = QtGui.QPushButton('TO')

        self.conn = QtGui.QPushButton('CONNECT')

        self.list_all_attr_button = QtGui.QPushButton('LIST ALL ATTRS')
        self.select_frobj_button = QtGui.QPushButton('Select Fobj')

        self.layout.addWidget(self.get_from, 1, 0, 1, 1)
        self.layout.addWidget(self.get_to, 1, 1, 1, 1)
        self.layout.addWidget(self.conn, 2, 0, 1, 1)
        self.layout.addWidget(self.list_all_attr_button, 2, 1, 1, 1)
        self.layout.addWidget(self.select_frobj_button, 4, 1, 1, 1)

    def select_fobj(self):
        transforms = bool(self.transforms_checkbox.isChecked())
        shapes = bool(self.shapes_checkbox.isChecked())

        selection_list = []

        for key, value in self.attr_shape_dict.iteritems():

            if 'rmanFobjIndex' in value:
                selection_list.append(key)
        cmds.select(selection_list)

    def get_from_tree(self):

        transforms = bool(self.transforms_checkbox.isChecked())
        shapes = bool(self.shapes_checkbox.isChecked())

        from_list = cmds.ls(sl=True, dag=True, shapes=shapes, transforms=transforms)

        self.from_tree.clear()
        final_from_list = []
        filter_text = self.filter_edit.text()
        if filter_text:
            for node in from_list:
                if node.find(filter_text) != -1:
                    final_from_list.append(node)
        else:
            final_from_list = from_list

        for shape in final_from_list:
            item = QtGui.QTreeWidgetItem()
            self.from_tree.addTopLevelItem(item)
            item.setText(0, shape)

    def get_to_tree(self):
        to_list = cmds.ls(sl=True, dag=True)
        self.to_tree.clear()

        for shape in to_list:
            item = QtGui.QTreeWidgetItem()
            self.to_tree.addTopLevelItem(item)
            item.setText(0, shape)

    def connecting_attrs(self):

        from_node = self.from_tree.selectedItems()[0].text(0)
        attr_list = cmds.listAttr(str(from_node), userDefined=True)

        print attr_list
        print from_node

        to_items_list = []
        for i in range(self.to_tree.topLevelItemCount()):
            to_it = self.to_tree.topLevelItem(i)
            to_items_list.append(str(to_it.text(0)))

        print to_items_list

        # connecting attr
        for to_item in to_items_list:
            for attr in attr_list:
                try:
                    cmds.connectAttr('{0}.{1}'.format(from_node, attr), '{0}.{1}'.format(to_item, attr), force=True)
                except Exception as ex:
                    print ex, to_item, attr

    def tree_item_click(self, item):

        from_node = item.text(0)

        attr_list = cmds.listAttr(str(from_node), userDefined=True)

        self.edit_attrs_table.clear()
        self.add_table_header()
        if attr_list:
            self.edit_attrs_table.setColumnCount(int(len(attr_list)))

            self.edit_attrs_table.setRowCount(1)
            vertical_item = QtGui.QTableWidgetItem()
            vertical_item.setText(from_node)
            self.edit_attrs_table.setVerticalHeaderItem(0, vertical_item)

            for i, attr in enumerate(attr_list):
                item = QtGui.QTableWidgetItem()
                item.setText(attr)
                self.edit_attrs_table.setHorizontalHeaderItem(i, item)

                attr_val = cmds.getAttr('{0}.{1}'.format(from_node, attr))
                value_item = QtGui.QTableWidgetItem()
                value_item.setText(str(attr_val))
                value_item.setData(1, [str(from_node), attr])
                self.edit_attrs_table.setItem(0, i, value_item)

    def list_all_attrs(self):
        self.attr_shape_dict = {}

        self.edit_attrs_table.clear()
        rows_count = 0
        col_count = 0
        all_attrs_list = []
        all_nodes_with_attrs = []

        # make lists
        for j in range(self.from_tree.topLevelItemCount()):
            from_item = self.from_tree.topLevelItem(j)
            from_node = from_item.text(0)
            attr_list = cmds.listAttr(str(from_node), userDefined=True)
            if attr_list:
                rows_count += 1
                all_attrs_list.extend(attr_list)
                all_nodes_with_attrs.append(from_node)

        # filling Table
        truncated_attrs_list = set(all_attrs_list)
        col_count = len(truncated_attrs_list)
        self.edit_attrs_table.setRowCount(rows_count)
        self.edit_attrs_table.setColumnCount(col_count)
        for j, node in enumerate(all_nodes_with_attrs):
            vertical_item = QtGui.QTableWidgetItem()
            vertical_item.setText(node)

            self.edit_attrs_table.setVerticalHeaderItem(j, vertical_item)
            attr_list = []
            for i, attr in enumerate(truncated_attrs_list):
                item = QtGui.QTableWidgetItem()
                item.setText(attr)
                self.edit_attrs_table.setHorizontalHeaderItem(i, item)
                exists = cmds.attributeQuery(attr, node=str(node), exists=True)
                if exists:
                    attr_val = cmds.getAttr('{0}.{1}'.format(str(node), attr))

                    value_item = QtGui.QTableWidgetItem()
                    value_item.setText(str(attr_val))
                    value_item.setData(1, [str(node), attr])
                    self.edit_attrs_table.setItem(j, i, value_item)

                    attr_list.append(attr)
            self.attr_shape_dict[str(node)] = attr_list

    def commit_and_check_attr(self, item, e_item, commit=False):
        value = str(e_item.data(0).toPyObject())
        node = str(e_item.data(1).toPyObject()[0])
        attr = str(e_item.data(1).toPyObject()[1])
        exists = cmds.attributeQuery(attr, node=node, exists=True)

        if commit:
            result_value = cmds.getAttr('{0}.{1}'.format(node, attr))
            print result_value
            # item.setText(str(result_value))
        else:
            if exists:
                attr_type = cmds.getAttr('{0}.{1}'.format(node, attr), type=True)
                if attr_type == 'string':
                    cmds.setAttr('{0}.{1}'.format(node, attr), str(value), type='string')
                elif attr_type == 'double':
                    cmds.setAttr('{0}.{1}'.format(node, attr), float(value))
                elif attr_type == 'bool':
                    cmds.setAttr('{0}.{1}'.format(node, attr), bool(int(value)))
                else:
                    cmds.setAttr('{0}.{1}'.format(node, attr), int(value))

    def edit_table_item(self, item):
        selected_items = self.edit_attrs_table.selectedItems()
        value = item.text()
        for s_item in selected_items:
            s_item.setText(value)
            self.commit_and_check_attr(s_item, item)

            # for s_item in selected_items:
            #    self.commit_and_check_attr(s_item, item, commit=True)

    def controls_actions(self):

        self.get_from.clicked.connect(self.get_from_tree)
        self.get_to.clicked.connect(self.get_to_tree)

        self.conn.clicked.connect(self.connecting_attrs)

        self.list_all_attr_button.clicked.connect(self.list_all_attrs)

        self.select_frobj_button.clicked.connect(self.select_fobj)

        self.from_tree.itemClicked.connect(self.tree_item_click)

        self.to_tree.itemClicked.connect(self.tree_item_click)

        self.edit_attrs_table.itemChanged.connect(self.edit_table_item)


# wnd = QtWindow()
# wnd.setSizeGripEnabled(True)
# wnd.show()