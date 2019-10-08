# module Main Ui Classes
# file ui_main_classes.py
# Main Window interface

import collections
from functools import partial
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

from thlib.environment import env_mode, env_inst, dl, env_write_config, env_read_config, cfg_controls
import thlib.tactic_classes as tc
import thlib.update_functions as uf
import thlib.global_functions as gf
import thlib.ui.ui_main as ui_main
from thlib.ui_classes.ui_script_editor_classes import Ui_ScriptEditForm
from thlib.ui_classes.ui_update_classes import Ui_updateDialog
import thlib.ui.misc.ui_create_update as ui_create_update
from thlib.ui_classes.ui_misc_classes import Ui_debugLogWidget, Ui_messagesWidget
import ui_checkin_out_tabs_classes
import ui_conf_classes
# import ui_my_tactic_classes
import ui_assets_browser_classes
import ui_float_notify_classes
if env_mode.get_mode() == 'maya':
    import thlib.maya_functions as mf
    reload(mf)


reload(ui_main)
reload(ui_create_update)
reload(ui_checkin_out_tabs_classes)
reload(ui_conf_classes)
# reload(ui_my_tactic_classes)
reload(ui_assets_browser_classes)
reload(ui_float_notify_classes)
reload(tc)
reload(uf)
reload(gf)


class Ui_mainTabs(QtGui.QWidget):
    def __init__(self, project_code, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        env_inst.ui_main_tabs[project_code] = self

        self.checkin_out_config_projects = cfg_controls.get_checkin_out_projects()
        self.checkin_out_config = cfg_controls.get_checkin_out()
        self.isCreated = False

        self.project = env_inst.projects.get(project_code)
        self.current_project = self.project.info['code']
        self.current_namespace = self.project.info['type']

        # if self.checkin_out_config_projects and self.checkin_out_config:
        #     if gf.get_value_from_config(self.checkin_out_config, 'controlsTabsFilterGroupBox'):
        #         self.customize_controls_tabs()

        self.create_ui()

    # def customize_controls_tabs(self):
    #     if self.checkin_out_config_projects:
    #         project_tabs_list = self.checkin_out_config_projects.get(self.current_project)
    #         if gf.get_value_from_config(self.checkin_out_config, 'applyToAllProjectsRadioButton'):
    #             tabs_list = self.checkin_out_config_projects.get('!tabs_list!')
    #         elif project_tabs_list:
    #             tabs_list = project_tabs_list['tabs_list']
    #         else:
    #             tabs_list = None
    #         if tabs_list:
    #             for i, tab in enumerate(tabs_list):
    #                 if tab[0] == 'Checkin / Checkout':
    #                     if not tab[2]:
    #                         self.main_tabWidget.removeTab(self.get_tab_index(self.checkInOutTab))
    #                     else:
    #                         self.main_tabWidget.insertTab(i, self.checkInOutTab, tab[1])
    #                 if tab[0] == 'My Tactic':
    #                     if not tab[2]:
    #                         self.main_tabWidget.removeTab(self.get_tab_index(self.myTacticTab))
    #                     else:
    #                         self.main_tabWidget.insertTab(i, self.myTacticTab, tab[1])
    #                 if tab[0] == 'Assets Browser':
    #                     if not tab[2]:
    #                         self.main_tabWidget.removeTab(self.get_tab_index(self.assetsBrowserTab))
    #                     else:
    #                         self.main_tabWidget.insertTab(i, self.assetsBrowserTab, tab[1])

    def create_ui(self):

        self.ui_checkin_checkout = None
        # self.skeyLineEdit_actions()
        # self.readSettings()
        self.main_layout = QtGui.QGridLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

    def get_tab_index(self, tab_widget):
        return self.main_tabWidget.indexOf(tab_widget)

    def raise_tab(self, tab_widget):
        self.main_tabWidget.setCurrentIndex(self.get_tab_index(tab_widget))

    def get_stypes(self, result=None, run_thread=False):

        if result:
            if self.project.stypes:
                self.create_checkin_checkout_ui()
                self.toggle_loading_label()
                if env_mode.get_mode() == 'maya':
                    dl.log('Handling Maya Hotkeys', group_id='Maya')
                    env_inst.ui_maya_dock.handle_hotkeys()

                self.ui_checkin_checkout.setHidden(False)
            env_inst.ui_main.set_info_status_text('')

        if run_thread:

            env_inst.ui_main.set_info_status_text(
                '<span style=" font-size:8pt; color:#00ff00;">Getting Search Types</span>')

            def get_stypes_agent():
                return self.project.get_stypes()

            env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

            stypes_items_worker = gf.get_thread_worker(
                get_stypes_agent,
                env_inst.get_thread_pool('server_query/server_thread_pool'),
                result_func=self.get_stypes,
                error_func=gf.error_handle
            )
            stypes_items_worker.start()

    def create_checkin_checkout_ui(self):
        self.ui_checkin_checkout = ui_checkin_out_tabs_classes.Ui_checkInOutTabWidget(
            self.project,
            self,
            parent=self
        )
        self.ui_checkin_checkout.setHidden(True)
        self.main_layout.addWidget(self.ui_checkin_checkout)

    # def create_ui_my_tactic(self):
    #     """
    #     Create My Tactic Tab
    #     """
    #     self.ui_my_tactic = ui_my_tactic_classes.Ui_myTacticWidget(self)
    #     self.myTacticLayout.addWidget(self.ui_my_tactic)

    # def create_ui_assets_browser(self):
    #     """
    #     Create Assets Browser Tab
    #     """
    #     self.ui_assets_browser = ui_assets_browser_classes.Ui_assetsBrowserWidget(self)
    #     self.assetsBrowserLayout.addWidget(self.ui_assets_browser)

    def create_loading_label(self):
        self.loading_label = QtGui.QLabel()
        self.loading_label.setText('Loading...')
        self.loading_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.loading_label.setVisible(False)

        self.main_layout.addWidget(self.loading_label, 0, 0, 0, 0)

    def toggle_loading_label(self):
        if self.loading_label.isVisible():
            self.loading_label.setVisible(False)
            # self.main_tabWidget.setVisible(True)
            # self.skeyLineEdit.setVisible(True)
        else:
            self.loading_label.setVisible(True)
            # self.main_tabWidget.setVisible(False)
            # self.skeyLineEdit.setVisible(False)

    # def readSettings(self):
    #     self.set_settings_from_dict(env_read_config(
    #         filename='ui_main_tab',
    #         unique_id='ui_main/{0}/{1}'.format(self.current_namespace, self.current_project),
    #         long_abs_path=True))
    #
    # def writeSettings(self):
    #     env_write_config(
    #         self.get_settings_dict(),
    #         filename='ui_main_tab',
    #         unique_id='ui_main/{0}/{1}'.format(self.current_namespace, self.current_project),
    #         long_abs_path=True)

    def paintEvent(self, event):
        if not self.isCreated:
            self.isCreated = True
            self.create_loading_label()
            self.toggle_loading_label()
            self.get_stypes(run_thread=True)

        # TODO This is bad and should be not used or removed
        env_inst.set_current_project(self.project.info['code'])

    def closeEvent(self, event):

        if self.ui_checkin_checkout:
            self.ui_checkin_checkout.close()

        # self.writeSettings()
        event.accept()


class Ui_Main(QtGui.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent=parent)
        self.ui_settings_dict = {}
        self.created = False

        self.create_debuglog_widget()

        if env_mode.is_offline():
            self.create_ui_main_offline()
        else:
            self.create_ui_main()

    def create_project_dock(self, project_code, close_project=True, raise_tab=False):
        if project_code not in self.projects_docks.keys():
            project = env_inst.projects.get(project_code)
            if project:
                if not project.is_template():
                    dock_widget = QtGui.QDockWidget(self)
                    dock_widget.setObjectName(project_code)
                    # print project.info['title'].replace('_', ' ').capitalize()
                    dock_widget.setWindowTitle(project.info.get('title'))
                    dock_widget.setMinimumWidth(200)
                    dock_widget.setFeatures(
                        QtGui.QDockWidget.DockWidgetMovable | QtGui.QDockWidget.DockWidgetClosable)

                    main_tabs_widget = Ui_mainTabs(project_code, dock_widget)
                    dock_widget.setWidget(main_tabs_widget)

                    self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_widget)
                    for dock in self.projects_docks.values():
                        self.tabifyDockWidget(dock, dock_widget)

                    self.projects_docks[project_code] = dock_widget

                    dock_widget.setStyleSheet(
                        '#complex_testing_phase_four > QTabBar::tab {background: transparent;border: 2px solid transparent;'
                        'border-top-left-radius: 3px;border-top-right-radius: 3px;border-bottom-left-radius: 0px;border-bottom-right-radius: 0px;padding: 4px;}'
                        '#complex_testing_phase_four > QTabBar::tab:selected, #complex_testing_phase_four > QTabBar::tab:hover {'
                        'background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 rgba(255, 255, 255, 48), stop: 1 rgba(255, 255, 255, 32));}'
                        '#complex_testing_phase_four > QTabBar::tab:selected {border-color: transparent;}'
                        '#complex_testing_phase_four > QTabBar::tab:!selected {margin-top: 0px;}')

                    dock_widget.show()
                    dock_widget.raise_()
            else:
                print('No project with code: {0}'.format(project_code))

        elif close_project:
            self.projects_docks[project_code].widget().close()
            self.projects_docks[project_code].close()
            self.projects_docks[project_code].deleteLater()
            del self.projects_docks[project_code]
            env_inst.cleanup(project_code)

        if raise_tab:
            project_dock = self.projects_docks.get(project_code)
            if project_dock:
                project_dock.show()
                project_dock.raise_()

    def create_ui_main_offline(self):
        self.projects_docks = collections.OrderedDict()

        env_inst.ui_main = self

        self.setupUi(self)
        self.setWindowTitle('TACTIC handler (OFFLINE)')

        # instance attributes
        self.menu = None
        self.menu_bar_actions()
        self.menuProject.setEnabled(False)
        self.readSettings()
        self.setIcon()

        self.customize_ui()

    def create_ui_main(self):
        self.projects_docks = collections.OrderedDict()

        env_inst.ui_main = self

        self.setupUi(self)
        self.setWindowTitle('TACTIC Handler')
        self.customize_ui()

        # instance attributes
        self.menu = None
        self.mainwidget.deleteLater()
        self.query_projects()
        self.menu_bar_actions()
        self.menuProject.setEnabled(True)
        self.readSettings()
        self.setIcon()
        self.create_script_editor_widget()
        self.create_messages_widget()

        self.created = True

    def create_debuglog_widget(self):
        env_inst.ui_debuglog = Ui_debugLogWidget(self)

    def create_script_editor_widget(self):
        env_inst.ui_script_editor = Ui_ScriptEditForm(self)

    def create_messages_widget(self):
        env_inst.ui_messages = Ui_messagesWidget(self)

    def create_info_label(self):
        self.label_layout = QtGui.QVBoxLayout(self.menubar)
        self.label_layout.setContentsMargins(0, 0, 6, 0)

        self.info_label = QtGui.QLabel()
        self.info_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.info_label.setText('')
        self.label_layout.addWidget(self.info_label)

    def set_status_text(self, text=''):
        self.setStatusTip(text)

    def set_info_status_text(self, status_text=''):
        self.info_label.setText(status_text)

    def check_for_update(self):
        if uf.check_need_update():
            self.info_label.setText('<span style=" font-size:8pt; color:#ff0000;">Need update</span>')

    def setIcon(self):
        icon = Qt4Gui.QIcon(':/ui_main/gliph/tactic_favicon.ico')
        self.setWindowIcon(icon)

    def customize_ui(self):
        if env_mode.get_mode() == 'standalone':
            self.actionDock_undock.setVisible(False)

        self.actionExit.setIcon(gf.get_icon('close'))
        self.actionConfiguration.setIcon(gf.get_icon('wrench'))
        self.create_info_label()

    def menu_bar_actions(self):
        """
        Actions for the main menu bar
        """

        def close_routine():
            if env_mode.get_mode() == 'maya':
                from thlib.ui_classes.ui_maya_dock import close_all_instances
                close_all_instances()
                self.close()
            if env_mode.get_mode() == 'standalone':
                self.close()

        self.actionExit.triggered.connect(close_routine)

        self.actionConfiguration.triggered.connect(self.open_config_dialog)

        self.actionApply_to_all_Tabs.triggered.connect(self.apply_current_view)
        self.actionReloadCache.triggered.connect(self.reload_cache)

        self.actionUpdate.triggered.connect(self.update_self)
        self.actionScriptEditor.triggered.connect(self.open_script_editor)
        self.actionDebug_Log.triggered.connect(lambda: env_inst.ui_debuglog.show())

        # User Menu items
        self.actionMessages.triggered.connect(lambda: env_inst.ui_messages.show())
        self.actionEdit_My_Account.triggered.connect(self.edit_my_account)

        self.actionDock_undock.triggered.connect(self.undock_window)

    def undock_window(self):
        env_inst.ui_maya_dock.toggle_docking()

    def edit_my_account(self):

        import thlib.tactic_widgets as tw
        import thlib.ui_classes.ui_tactic_widgets_classes as twc

        wd = {u'input_prefix': u'insert', u'element_titles': [u'Preview', u'Name', u'Description', u'Keywords'],
              u'title': u'', u'element_names': [u'preview', u'name', u'description', u'keywords'],
              u'kwargs': {u'search_type': u'melnitsapipeline/episode', u'code': u'', u'title_width': u'',
                          u'parent_key': None, u'title': u'', u'default': u'', u'search_key': u'',
                          u'input_prefix': u'insert', u'config_base': u'', u'single': u'', u'cbjs_edit_path': u'',
                          u'access': u'', u'width': u'', u'show_header': u'', u'cbjs_cancel': u'', u'mode': u'insert',
                          u'cbjs_insert_path': u'', u'ignore': u'', u'show_action': u'', u'search_id': u'',
                          u'view': u'insert'}, u'element_descriptions': [None, u'Name', u'Description', u'Keywords'],
              u'mode': u'insert', u'security_denied': False}
        tactic_edit_widget = tw.TacticEditWdg(wd)
        tactic_edit_widget.set_stype(env_inst.get_current_stypes()['tactichandler/bug'])

        input_widgets_list = []

        class Item(object):
            def __init__(self):
                self.get_pipeline = None
                self.type = 'fake'

        self.item = Item()
        # class item(object):
        def get_pipeline():
            return None
        self.item.get_pipeline = get_pipeline
        # self.item.get_pipeline = get_pipeline
        edit_window = twc.QtTacticEditWidget(
            tactic_widget=tactic_edit_widget,
            qt_widgets=input_widgets_list,
            stype=self.item,
            parent=self
        )

        edit_window.show()

        self.dlg = QtGui.QDialog(self)
        self.l = QtGui.QVBoxLayout()
        self.l.addWidget(edit_window)
        self.dlg.setLayout(self.l)
        self.dlg.show()

        import ui_addsobject_classes
        # edit_current_account = ui_addsobject_classes.Ui_addTacticSobjectWidget(
        #     stype=env_inst.get_current_stypes().values()[0],
        #     view='edit',
        #     parent=self,
        # )
        # edit_current_account.setWindowTitle(u'Editing User Account')
        # edit_current_account.show()

    def create_ui_float_notify(self):
        self.float_notify = ui_float_notify_classes.Ui_floatNotifyWidget(self)
        self.float_notify.show()
        self.float_notify.setSizeGripEnabled(True)

    def open_script_editor(self):
        env_inst.ui_script_editor.show()

    def update_self(self):
        if env_mode.is_online():
            self.update_dialog = Ui_updateDialog(self)

            self.update_dialog.show()

    def reload_cache(self):
        tc.get_all_projects_and_logins(True)
        for project in env_inst.projects.values():
            project.query_search_types(True)

        self.restart_ui_main()

    def open_config_dialog(self):
        conf_dialog = ui_conf_classes.Ui_configuration_dialogWidget(parent=self)
        conf_dialog.show()

    def restart_for_update_ui_main(self):
        if env_mode.get_mode() == 'standalone':
            import main_standalone
            thread = main_standalone.restart()
            thread.finished.connect(self.close)
        if env_mode.get_mode() == 'maya':
            import main_maya
            thread = main_maya.main.restart()
            thread.finished.connect(main_maya.main.close_all_instances)

    def restart_ui_main(self):
        self.close()
        self.projects_docks = collections.OrderedDict()

        if env_mode.is_online():
            self.create_ui_main()
        else:
            self.create_ui_main_offline()

        self.show()
        return self

    def apply_current_view(self):
        # TODO may be need to be rewriten to use env instance
        if env_inst.get_current_project():
            current_project_widget = self.projects_docks[env_inst.get_current_project()].widget()

            current_project_widget.ui_checkin_checkout.apply_current_view_to_all()

            # widget_name = current_project_widget.main_tabWidget.currentWidget().objectName()

            # if widget_name == 'checkInOutTab':
            #     current_project_widget.ui_checkin_checkout.apply_current_view_to_all()
            #
            # if widget_name == 'checkOutTab':
            #     current_project_widget.ui_checkout.apply_current_view_to_all()
            #
            # if widget_name == 'checkInTab':
            #     current_project_widget.ui_checkin.apply_current_view_to_all()

    def fill_projects_to_menu(self):

        all_projects_dicts = []

        for project_name, project in env_inst.projects.iteritems():
            all_projects_dicts.append(project.info)

        projects_by_categories = gf.group_dict_by(all_projects_dicts, 'category')

        for cat_name, projects in projects_by_categories.iteritems():
            if cat_name:
                cat_name = gf.prettify_text(cat_name, True)
            else:
                cat_name = 'No Category'
            if cat_name != 'Template':
                category = self.menuProject.addMenu(cat_name)

            for e, project in enumerate(projects):
                if not project.get('is_template'):
                    project_code = project.get('code')

                    menu_action = QtGui.QAction(self)
                    menu_action.setCheckable(True)

                    if self.opened_projects:
                        if project_code in self.opened_projects:
                            menu_action.setChecked(True)
                    menu_action.setText(project.get('title'))
                    # Don't know why lambda did not work here
                    menu_action.triggered.connect(partial(self.create_project_dock, project_code))
                    category.addAction(menu_action)

    def restore_opened_projects(self):
        if self.ui_settings_dict:
            self.opened_projects = self.ui_settings_dict.get('opened_projects')
        else:
            self.opened_projects = None
        if not isinstance(self.opened_projects, list):
            if self.opened_projects:
                self.opened_projects = [self.opened_projects]

        if self.opened_projects:
            for project in self.opened_projects:
                if project:
                    self.create_project_dock(project)

            current_project_code = self.ui_settings_dict.get('current_active_project')

            if current_project_code:
                if self.projects_docks.get(current_project_code):
                    self.projects_docks[current_project_code].show()
                    self.projects_docks[current_project_code].raise_()

    def get_settings_dict(self):

        settings_dict = {}

        if self.windowState() == QtCore.Qt.WindowMaximized:
            state = True
            if self.ui_settings_dict:
                settings_dict['pos'] = self.ui_settings_dict['pos']
                settings_dict['size'] = self.ui_settings_dict['size']
            else:
                settings_dict['pos'] = self.pos().toTuple()
                settings_dict['size'] = self.size().toTuple()
        else:
            state = False
            settings_dict['pos'] = self.pos().toTuple()
            settings_dict['size'] = self.size().toTuple()
        settings_dict['windowState'] = state

        if self.projects_docks.keys():
            settings_dict['opened_projects'] = self.projects_docks.keys()
            if env_inst.get_current_project():
                settings_dict['current_active_project'] = str(env_inst.get_current_project())
        else:
            settings_dict['opened_projects'] = ''
            settings_dict['current_active_project'] = ''

        return settings_dict

    def set_settings_from_dict(self, settings_dict=None):

        if not settings_dict:
            settings_dict = {
                'pos': self.pos().toTuple(),
                'size': self.size().toTuple(),
                'windowState': False,
                'opened_projects': '',
                'current_active_project': '',
            }

        self.move(settings_dict['pos'][0], settings_dict['pos'][1])
        self.resize(settings_dict['size'][0], settings_dict['size'][1])

        if settings_dict['windowState']:
            self.setWindowState(QtCore.Qt.WindowMaximized)

    def readSettings(self):
        self.ui_settings_dict = env_read_config(filename='ui_settings', unique_id='ui_main', long_abs_path=True)
        self.set_settings_from_dict(self.ui_settings_dict)

    def writeSettings(self):
        env_write_config(self.get_settings_dict(), filename='ui_settings', unique_id='ui_main', long_abs_path=True)

    def closeEvent(self, event):
        for dock in self.projects_docks.values():
            # project_code = dock.widget().project.get_code()
            dock.widget().close()
            dock.close()
            dock.deleteLater()
            del dock
            # env_inst.cleanup(project_code)
        self.writeSettings()
        event.accept()

    def query_projects_finished(self, result=None):
        if result:
            self.restore_opened_projects()
            self.fill_projects_to_menu()
            env_inst.ui_main.set_info_status_text('')

            # self.create_ui_float_notify()

    def query_projects(self):
        env_inst.ui_main.set_info_status_text(
            '<span style=" font-size:8pt; color:#00ff00;">Getting projects</span>')

        def get_all_projects_and_logins_agent():
            return tc.get_all_projects_and_logins()

        env_inst.set_thread_pool(None, 'server_query/server_thread_pool')

        projects_items_worker = gf.get_thread_worker(
            get_all_projects_and_logins_agent,
            env_inst.get_thread_pool('server_query/server_thread_pool'),
            result_func=self.query_projects_finished,
            error_func=gf.error_handle
        )
        projects_items_worker.start()

    # def closeEventExt(self, event):
    #     self.ext_window.deleteLater()
    #     event.accept()
