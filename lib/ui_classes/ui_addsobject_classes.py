# module Adding sObject Classes
# file ui_addsobject_classes.py
# Adding new sObject window

from lib.side.Qt import QtWidgets as QtGui
from lib.side.Qt import QtCore

import json
from lib.environment import env_inst, env_write_config, env_read_config
import lib.global_functions as gf
import lib.tactic_classes as tc
import lib.tactic_widgets as tw
import lib.tactic_query as tq
import lib.ui_classes.ui_tactic_widgets_classes as twc


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

        self.thread_pool = QtCore.QThreadPool()

        self.get_widgets(kwargs)
        self.setSizeGripEnabled(True)
        self.set_title()

    def create_widgets_ui(self, result_dict):
        self.toggle_loading_label()
        
        input_widgets_list = []
        if self.item:
            result_dict['EditWdg']['sobject'] = self.item.get_sobject()
            result_dict['EditWdg']['parent_sobject'] = self.item.get_parent_sobject()

        # print result_dict

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
        # self.edit_window.set_settings_from_dict(self.settings.value('edit_widndow_settings_dict', None))

    def create_loading_label(self):
        self.loading_label = QtGui.QLabel()
        self.loading_label.setText('Loading...')
        self.loading_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.loading_label.setVisible(False)

        self.grid_layout.addWidget(self.loading_label, 0, 0)

    def toggle_loading_label(self):
        if self.loading_label.isVisible():
            self.loading_label.setVisible(False)
            # self.main_tabWidget.setVisible(True)
            # self.skeyLineEdit.setVisible(True)
        else:
            self.loading_label.setVisible(True)
            # self.main_tabWidget.setVisible(False)
            # self.skeyLineEdit.setVisible(False)

    def get_widgets(self, kwargs):

        def query_widgets_agent():
            return self.query_widgets(kwargs)

        worker = gf.get_thread_worker(query_widgets_agent, self.thread_pool)
        worker.result_func(self.create_widgets_ui)
        worker.error_func(gf.error_handle)
        worker.try_start()

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
        search_widget.do_search(
            search_query=sobject.get('code'),
            search_by=1,
            new_tab=True
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
        tree_wdg = checkin_out_tab.get_current_tree_widget()

        tree_wdg.update_current_items_trees()

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
