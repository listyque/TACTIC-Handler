
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
