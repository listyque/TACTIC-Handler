# module Adding sObject Classes
# file ui_addsobject_classes.py
# Adding new sObject window

from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtCore

import json
from thlib.environment import env_inst, env_write_config, env_read_config
import thlib.global_functions as gf
import thlib.tactic_classes as tc
import thlib.tactic_widgets as tw
import thlib.tactic_query as tq
import thlib.ui_classes.ui_tactic_widgets_classes as twc


class Ui_linkSobjectsWidget(QtGui.QDialog):
    def __init__(self, stype, parent_stype=None, item=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.item = item
        self.stype = stype
        self.parent_stype = parent_stype
        self.current_mode = 'add'
        self.include_set = set()
        self.exclude_set = set()
        self.current_set = set()

        self.create_ui()

    def create_ui(self):
        self.create_layout()

        self.resize(750, 800)
        self.setMinimumSize(600, 500)

        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setSizeGripEnabled(True)
        self.setWindowFlags(QtCore.Qt.Dialog)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.create_all_layouts()

        self.create_parent_search_line()
        self.create_instances_search_line()

        self.create_parent_widget()
        self.create_instances_widget()

        self.create_buttons()

        self.set_title()

        self.controls_actions()

        self.parent_search_line_edit.setFocus()

    def controls_actions(self):

        self.parent_tree_widget.itemSelectionChanged.connect(self.set_arrow_right)
        self.parent_search_line_edit.returnPressed.connect(self.do_parent_search)
        self.parent_search_line_edit.item_selected.connect(self.do_parent_search)
        self.parent_search_line_edit.item_clicked.connect(self.do_parent_search)

        self.instances_search_line_edit.returnPressed.connect(self.do_instance_search)
        self.instances_search_line_edit.item_selected.connect(self.do_instance_search)
        self.instances_search_line_edit.item_clicked.connect(self.do_instance_search)

        self.instances_tree_widget.itemSelectionChanged.connect(self.set_arrow_left)

        self.add_remove_tool_button.clicked.connect(self.add_remove_tool_button_clicked)

        self.cancel_button.clicked.connect(self.close)
        self.save_button.clicked.connect(self.save_instances_state)

    def keyPressEvent(self, event):
        event.ignore()

    def save_instances_state(self):
        tc.edit_multiple_instance_sobjects(
            self.stype.project.get_code(),
            insert_search_keys=self.include_set,
            exclude_search_keys=self.exclude_set,
            parent_key=self.item.sobject.get_search_key(),
            instance_type=self.item.child.get('instance_type')
        )

        self.close()

    def set_arrow_right(self):
        self.add_remove_tool_button.setIcon(gf.get_icon('arrow-right-bold', icons_set='mdi'))
        self.instances_tree_widget.clearSelection()

        self.current_mode = 'add'

    def set_arrow_left(self):
        self.add_remove_tool_button.setIcon(gf.get_icon('arrow-left-bold', icons_set='mdi'))
        self.parent_tree_widget.clearSelection()

        self.current_mode = 'remove'

    def add_remove_tool_button_clicked(self):
        for sobject in self.instances_search_results_widget.sobjects:
            self.current_set.add(sobject)

        # TODO DUPLICATES CHECK

        if self.current_mode == 'remove':
            selected_instaces = self.instances_tree_widget.selectedItems()
            for item in selected_instaces:

                item_widget = self.instances_tree_widget.itemWidget(item, 0)

                item_info = {
                    'relates_to': 'checkin_out',
                    'sep_versions': True,
                    'children_states': None,
                    'simple_view': True,
                }
                gf.add_sobject_item(
                    self.parent_tree_widget,
                    self,
                    item_widget.sobject,
                    self.stype,
                    item_info,
                    ignore_dict=None,
                )

                sobject = item_widget.sobject
                search_key = sobject.get_search_key()

                if search_key not in self.include_set:
                    self.exclude_set.add(search_key)

                if search_key in self.include_set:
                    self.include_set.remove(search_key)

                idx = self.instances_tree_widget.indexFromItem(item)
                self.instances_tree_widget.takeTopLevelItem(idx.row())

        elif self.current_mode == 'add':
            selected_parents = self.parent_tree_widget.selectedItems()
            for item in selected_parents:

                item_widget = self.parent_tree_widget.itemWidget(item, 0)
                sobject = item_widget.sobject
                search_key = sobject.get_search_key()

                item_info = {
                    'relates_to': 'checkin_out',
                    'sep_versions': True,
                    'children_states': None,
                    'simple_view': True,
                }
                gf.add_sobject_item(
                    self.instances_tree_widget,
                    self,
                    item_widget.sobject,
                    self.stype,
                    item_info,
                    ignore_dict=None,
                )

                if search_key in self.exclude_set:
                    self.exclude_set.remove(search_key)

                if search_key not in self.current_set:
                    self.include_set.add(search_key)

                idx = self.parent_tree_widget.indexFromItem(item)
                self.parent_tree_widget.takeTopLevelItem(idx.row())

    def create_layout(self):

        self.grid_layout = QtGui.QGridLayout(self)

    def create_all_layouts(self):
        self.splitter = QtGui.QSplitter(self)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")

        self.gridLayoutWidget = QtGui.QWidget(self.splitter)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")

        self.parent_grid_layout = QtGui.QGridLayout(self.gridLayoutWidget)
        self.parent_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.parent_grid_layout.setObjectName("parent_grid_layout")

        self.add_remove_tool_button = QtGui.QToolButton(self.gridLayoutWidget)

        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.add_remove_tool_button.sizePolicy().hasHeightForWidth())

        self.add_remove_tool_button.setSizePolicy(sizePolicy)
        self.add_remove_tool_button.setObjectName("add_remove_tool_button")
        self.add_remove_tool_button.setAutoRaise(True)

        self.parent_grid_layout.addWidget(self.add_remove_tool_button, 0, 1, 1, 1)

        self.add_remove_tool_button.setIcon(gf.get_icon('arrow-right-bold', icons_set='mdi'))

        self.parent_vertical_layout = QtGui.QVBoxLayout()

        self.parent_vertical_layout.setObjectName("parent_vertical_layout")

        self.parent_grid_layout.addLayout(self.parent_vertical_layout, 0, 0, 1, 1)

        self.verticalLayoutWidget = QtGui.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")

        self.instances_vertical_layout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.instances_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.instances_vertical_layout.setObjectName("instances_vertical_layout")

        self.buttons_layout = QtGui.QHBoxLayout()
        self.buttons_layout.setObjectName("buttons_layout")
        self.grid_layout.addLayout(self.buttons_layout, 1, 0, 1, 1)

        self.grid_layout.addWidget(self.splitter, 0, 0, 1, 1)

    def create_buttons(self):

        self.save_button = QtGui.QPushButton('Save')
        self.save_button.setMaximumWidth(80)
        self.save_button.setIcon(gf.get_icon('content-save', icons_set='mdi'))
        self.save_button.setFlat(True)
        self.save_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self.cancel_button = QtGui.QPushButton('Close')
        self.cancel_button.setMaximumWidth(80)
        self.cancel_button.setIcon(gf.get_icon('close', icons_set='mdi'))
        self.cancel_button.setFlat(True)
        self.cancel_button.setFocusPolicy(QtCore.Qt.NoFocus)

        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)

        self.buttons_layout.addItem(spacerItem)

        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.cancel_button)

    def create_parent_search_line(self):
        from thlib.ui_classes.ui_custom_qwidgets import SuggestedLineEdit

        self.parent_search_line_edit = SuggestedLineEdit(self.stype, self.stype.project, parent=self)
        self.parent_search_line_edit.setObjectName("parent_search_line_edit")
        self.parent_search_line_edit.setToolTip('Enter Your search query here')
        self.parent_vertical_layout.addWidget(self.parent_search_line_edit)
        self.parent_search_line_edit.set_autofill_selected_items(True)

    def create_instances_search_line(self):
        from thlib.ui_classes.ui_custom_qwidgets import SuggestedLineEdit

        self.instances_search_line_edit = SuggestedLineEdit(self.stype, self.stype.project, parent=self)
        self.instances_search_line_edit.setObjectName("instances_search_line_edit")
        self.instances_search_line_edit.setToolTip('Enter Your search query here')
        self.instances_vertical_layout.addWidget(self.instances_search_line_edit)
        self.instances_search_line_edit.set_autofill_selected_items(True)

        # parent_sobject = self.item.get_sobject()
        # related_expr = parent_sobject.get_related_sobjects_tel_string(self.stype)
        # self.instances_search_line_edit.set_default_filter(('_expression', 'in', related_expr))

    def create_parent_widget(self):

        from thlib.ui_classes.ui_search_classes import Ui_resultsTabWidget, DEFAULT_FILTER

        info = {
            'title': '',
            'filters': [DEFAULT_FILTER],
            'state': None,
            'offset': 0,
            'limit': 20,
            'simple_view': True
        }

        self.search_results_widget = Ui_resultsTabWidget(
            project=self.stype.project,
            stype=self.stype,
            info=info,
            parent=self
        )

        self.parent_tree_widget = self.search_results_widget.get_results_tree_widget()

        self.parent_vertical_layout.addWidget(self.search_results_widget)

    def do_parent_search(self):
        query_text = self.parent_search_line_edit.text()
        if query_text:
            self.search_results_widget.set_filters([('name', 'EQI', query_text)])
            self.search_results_widget.search_query(query_text)
        else:
            self.search_results_widget.set_filters([])
            self.search_results_widget.search_query('')

    def do_instance_search(self):
        query_text = self.instances_search_line_edit.text()

        parent_sobject = self.item.get_sobject()

        related_expr = parent_sobject.get_related_sobjects_tel_string(child_stype=self.stype, parent_stype=parent_sobject.get_stype())

        if query_text:
            self.instances_search_results_widget.set_filters([
                ('name', 'EQI', query_text),
                ('_expression', 'in', related_expr)
            ])
            self.instances_search_results_widget.search_query(query_text)
        else:
            self.instances_search_results_widget.set_filters([('_expression', 'in', related_expr)])
            self.instances_search_results_widget.search_query('')

    @env_inst.async_engine
    def create_instances_widget(self):
        from thlib.ui_classes.ui_search_classes import Ui_resultsTabWidget

        parent_sobject = self.item.get_sobject()
        related_expr = parent_sobject.get_related_sobjects_tel_string(child_stype=self.stype, parent_stype=parent_sobject.get_stype())

        filters = [('_expression', 'in', related_expr)]

        info = {
            'title': '',
            'filters': filters,
            'state': None,
            'offset': 0,
            'limit': 20,
            'simple_view': True
        }

        self.instances_search_results_widget = Ui_resultsTabWidget(
            project=self.stype.project,
            stype=self.stype,
            info=info,
            parent=self
        )

        self.instances_tree_widget = self.instances_search_results_widget.get_results_tree_widget()

        self.instances_vertical_layout.addWidget(self.instances_search_results_widget)

    def set_title(self):
        stype_tytle = self.stype.info.get('title')
        stype_code = self.stype.info.get('code')
        if stype_tytle:
            title = stype_tytle.capitalize()
        else:
            title = 'Unknown'

        self.setWindowTitle('Linking SObjects {0} ({1})'.format(title, stype_code))

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


class Ui_addTacticSobjectWidget(QtGui.QDialog):
    def __init__(self, stype, parent_stype=None, item=None, view='insert', search_key=None, parent_search_key=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.item = item
        self.stype = stype
        self.parent_stype = parent_stype
        self.search_type = self.stype.info.get('code')

        self.view = view

        self.search_key = search_key
        self.parent_search_key = parent_search_key

        if self.item:
            if not search_key:
                self.search_key = self.item.get_search_key()
            if not parent_search_key:
                self.parent_search_key = self.item.get_parent_search_key()

        self.grid_layout = QtGui.QGridLayout(self)

        self.create_ui()

        # self.add_multiple()

    # def add_multiple(self):
    #     self.wnd = QtGui.QDialog(self)
    #     self.wnd.show()
    #     self.l = QtGui.QVBoxLayout()
    #
    #     self.b = QtGui.QPushButton('Begin')
    #
    #     self.wnd.setLayout(self.l)
    #
    #     self.l.addWidget(self.b)
    #     self.b.clicked.connect(self.begin_inst)
    #
    # def begin_inst(self):
    #
    #     # tactic_edit_widget = tw.TacticEditWdg(wdg_dict)
    #     print self.stype.get_code()
    #     # tactic_edit_widget.set_stype(self.stype)
    #
    #     # {u'episode_code': u'EPISODE00010', u'name': u'test'}
    #
    #     lst = {}
    #     for i, ep in enumerate(sorted(lst.keys())):
    #         print ep, i, 'out of:', len(lst)
    #         data = {'name': ep}
    #         wd = {u'input_prefix': u'insert', u'element_titles': [u'Preview', u'Name', u'Description', u'Keywords'], u'title': u'', u'element_names': [u'preview', u'name', u'description', u'keywords'], u'kwargs': {u'search_type': u'melnitsapipeline/episode', u'code': u'', u'title_width': u'', u'parent_key': None, u'title': u'', u'default': u'', u'search_key': u'', u'input_prefix': u'insert', u'config_base': u'', u'single': u'', u'cbjs_edit_path': u'', u'access': u'', u'width': u'', u'show_header': u'', u'cbjs_cancel': u'', u'mode': u'insert', u'cbjs_insert_path': u'', u'ignore': u'', u'show_action': u'', u'search_id': u'', u'view': u'insert'}, u'element_descriptions': [None, u'Name', u'Description', u'Keywords'], u'mode': u'insert', u'security_denied': False}
    #         tactic_edit_widget = tw.TacticEditWdg(wd)
    #         tactic_edit_widget.set_stype(self.stype.project.get_stypes()['melnitsapipeline/episode'])
    #
    #         episode_sobj = tactic_edit_widget.commit(data)
    #         print episode_sobj
    #         for j, sc in enumerate(sorted(lst[ep])):
    #             print sc, j, 'out of:', len(ep)
    #
    #             sc['episode_code'] = episode_sobj['code']
    #
    #             scene_sobj = self.edit_window.tactic_widget.commit(sc)
    #             print scene_sobj

    def create_ui(self):

        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setSizeGripEnabled(True)
        self.resize(400, 300)

        self.create_loading_label()
        self.toggle_loading_label()

        if self.view == 'edit':
            kwargs = {
                'args': {
                    'input_prefix': 'edit',
                    'search_key': self.search_key,
                    'parent_key': self.parent_search_key,
                    'view': 'edit',
                },
                'search_type': self.search_type,
                'project': self.stype.project.get_code(),
            }
        else:
            kwargs = {
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

        self.get_widgets(kwargs)

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
            return tc.execute_procedure_serverside(tq.query_EditWdg, kwargs, project=kwargs['project'])

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        worker = gf.get_thread_worker(
            query_widgets_agent,
            env_inst.get_thread_pool('server_query/server_thread_pool'),
            self.create_widgets_ui,
            gf.error_handle
        )

        worker.start()

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

