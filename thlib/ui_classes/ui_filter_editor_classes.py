import copy
from functools import partial
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtNetwork
from thlib.side.Qt import QtCore
from thlib.environment import env_inst, env_read_config, env_write_config
import thlib.global_functions as gf
import thlib.tactic_classes as tc
import thlib.ui_classes.ui_search_classes as ui_search_classes


class Ui_filterEditorDialog(QtGui.QDialog):

    def __init__(self, stype, tab_name=None, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        # self.sobject = sobject
        self.tab_name = tab_name

        self.get_all_presets_from_server()

        self.create_ui()

    def create_ui(self):
        if self.tab_name:
            self.setWindowTitle('Search Presets Editor: {0}'.format(self.tab_name))
        else:
            self.setWindowTitle('Search Presets Editor: {0}'.format(self.stype.get_pretty_name()))

        self.setSizeGripEnabled(True)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.create_advanced_search_widget()
        self.fill_presets_combo_box()
        self.create_controls()
        self.controls_actions()

        self.resize(960, 300)

        self.readSettings()

    def controls_actions(self):

        # self.none_button.clicked.connect(lambda: self.switch_items('none'))
        # self.all_process_button.clicked.connect(lambda: self.switch_items('process'))
        # self.all_with_builtins_button.clicked.connect(lambda: self.switch_items('builtins'))
        # self.all_children_button.clicked.connect(lambda: self.switch_items('children'))

        # self.tree_widget.itemChanged.connect(self.check_tree_items)
        self.presets_combo_box.currentIndexChanged.connect(self.apply_search_preset)

        # self.save_current_as_preset_button.clicked.connect(self.save_current_as_preset)

    # def check_tree_items(self, changed_item):
    #     if len(self.tree_widget.selectedItems()) > 1:
    #         for item in self.tree_widget.selectedItems():
    #             item.setCheckState(0, changed_item.checkState(0))
    def create_controls(self):

        # self.versionChooserHorizontalLayout = QtGui.QHBoxLayout()
        # self.versionChooserHorizontalLayout.setContentsMargins(0, 0, 0, 0)
        # self.versionChooserHorizontalLayout.setObjectName("versionChooserHorizontalLayout")
        #
        # self.versionlessSyncRadioButton = QtGui.QRadioButton()
        # self.versionlessSyncRadioButton.setChecked(True)
        # self.versionlessSyncRadioButton.setObjectName("versionlessSyncRadioButton")
        # self.versionlessSyncRadioButton.setText('Versionless Sync')
        #
        # self.fullSyncRadioButton = QtGui.QRadioButton()
        # self.fullSyncRadioButton.setObjectName("fullSyncRadioButton")
        # self.fullSyncRadioButton.setText('Full Sync')
        #
        # self.versionChooserHorizontalLayout.addWidget(self.versionlessSyncRadioButton)
        # self.versionChooserHorizontalLayout.addWidget(self.fullSyncRadioButton)

        # self.none_button = QtGui.QPushButton('Toggle All')
        # self.none_button.setIcon(gf.get_icon('checkbox-multiple-marked-outline', icons_set='mdi', scale_factor=1))
        # self.none_button.setFlat(True)
        #
        # self.all_process_button = QtGui.QPushButton('Toggle Process')
        # self.all_process_button.setIcon(gf.get_icon('checkbox-blank-circle', icons_set='mdi', scale_factor=0.6))
        # self.all_process_button.setFlat(True)
        #
        # self.all_with_builtins_button = QtGui.QPushButton('Toggle Builtin Processes')
        # self.all_with_builtins_button.setIcon(gf.get_icon('checkbox-blank-circle', icons_set='mdi', scale_factor=0.6))
        # self.all_with_builtins_button.setFlat(True)
        #
        # self.all_children_button = QtGui.QPushButton('Toggle Children')
        # self.all_children_button.setIcon(gf.get_icon('view-sequential', icons_set='mdi', scale_factor=1))
        # self.all_children_button.setFlat(True)

        # self.togglers_widget = QtGui.QWidget()
        # self.togglers_layout = QtGui.QGridLayout()
        # self.togglers_layout.setContentsMargins(0, 0, 0, 0)
        # self.togglers_layout.setSpacing(6)
        # self.togglers_widget.setLayout(self.togglers_layout)
        #
        # self.togglers_layout.addWidget(self.none_button, 0, 0, 1, 1)
        # self.togglers_layout.addWidget(self.all_process_button, 0, 1, 1, 1)
        # self.togglers_layout.addWidget(self.all_with_builtins_button, 1, 0, 1, 1)
        # self.togglers_layout.addWidget(self.all_children_button, 1, 1, 1, 1)
        #
        # self.togglers_layout.addLayout(self.versionChooserHorizontalLayout, 2, 0, 1, 2)

        # Creating collapsable
        # self.controls_collapsable = Ui_collapsableWidget(state=True)
        # layout_colapsable = QtGui.QVBoxLayout()
        # self.controls_collapsable.setLayout(layout_colapsable)
        # self.controls_collapsable.setText('Hide Togglers')
        # self.controls_collapsable.setCollapsedText('Show Togglers')
        # layout_colapsable.addWidget(self.togglers_widget)
        #
        # self.controls_collapsable.collapsed.connect(self.toggle_presets_edit_buttons)

        self.save_current_as_preset_button = QtGui.QPushButton('Save current Tab as Preset')
        self.save_current_as_preset_button.setFlat(True)

        save_preset_color = Qt4Gui.QColor(16, 160, 16)
        save_preset_color_active = Qt4Gui.QColor(16, 220, 16)

        self.save_current_as_preset_button.setIcon(gf.get_icon('content-save', color=save_preset_color, color_active=save_preset_color_active, icons_set='mdi', scale_factor=1))
        self.save_current_as_preset_button.setHidden(True)

        # self.progress_bar = QtGui.QProgressBar()
        # self.progress_bar.setMaximum(100)
        # self.progress_bar.setTextVisible(True)
        # self.progress_bar.setHidden(True)
        #
        # self.downloads_progress_bar = QtGui.QProgressBar()
        # self.downloads_progress_bar.setMaximum(100)
        # self.downloads_progress_bar.setTextVisible(True)
        # self.downloads_progress_bar.setHidden(True)

        # self.grid.addWidget(self.controls_collapsable, 2, 0, 1, 1)
        self.grid.addWidget(self.save_current_as_preset_button, 3, 0, 1, 1)
        # self.grid.addWidget(self.progress_bar, 4, 0, 1, 4)
        # self.grid.addWidget(self.downloads_progress_bar, 5, 0, 1, 4)

    # def toggle_presets_edit_buttons(self, state):
    #
    #     if state:
    #         self.add_new_preset_button.setHidden(True)
    #         self.save_new_preset_button.setHidden(True)
    #         self.remove_preset_button.setHidden(True)
    #     else:
    #         self.add_new_preset_button.setHidden(False)
    #         self.save_new_preset_button.setHidden(False)
    #         self.remove_preset_button.setHidden(False)

    def create_advanced_search_widget(self):

        self.grid = QtGui.QGridLayout()
        self.grid.setContentsMargins(9, 9, 9, 9)
        self.grid.setSpacing(6)
        self.setLayout(self.grid)

        self.create_presets_combo_box()

        self.advanced_search_widget = ui_search_classes.Ui_advancedSearchWidget(
            stype=self.stype,
            project=self.stype.get_project(),
            tab_name=self.get_tab_name(),
            editor_mode=True,
            parent=self
        )
        self.advanced_search_widget.clear_filters_button_action()

        self.grid.addWidget(self.advanced_search_widget, 1, 0, 1, 0)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.grid.addItem(spacerItem, 2, 0, 1, 0)
        self.grid.setRowStretch(1, 0)
        self.grid.setRowStretch(2, 1)

    def create_presets_combo_box(self):
        self.grid_presets = QtGui.QGridLayout()

        self.presets_combo_box = QtGui.QComboBox()

        self.add_new_preset_button = QtGui.QToolButton()
        self.add_new_preset_button.setAutoRaise(True)
        self.add_new_preset_button.setIcon(gf.get_icon('plus-box', icons_set='mdi', scale_factor=1.2))
        self.add_new_preset_button.clicked.connect(self.add_new_preset)
        self.add_new_preset_button.setToolTip('Create new Preset and Save (from current state)')

        self.save_new_preset_button = QtGui.QToolButton()
        self.save_new_preset_button.setAutoRaise(True)
        self.save_new_preset_button.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        self.save_new_preset_button.clicked.connect(self.save_preset_to_server)
        self.save_new_preset_button.setToolTip('Save Current Preset Changes')

        self.remove_preset_button = QtGui.QToolButton()
        self.remove_preset_button.setAutoRaise(True)
        self.remove_preset_button.setIcon(gf.get_icon('delete', icons_set='mdi', scale_factor=1))
        self.remove_preset_button.clicked.connect(self.delete_preset_from_server)
        self.remove_preset_button.setToolTip('Remove Current Preset')

        self.grid_presets.addWidget(self.remove_preset_button, 0, 0, 1, 1)
        self.grid_presets.addWidget(self.presets_combo_box, 0, 1, 1, 1)
        self.grid_presets.addWidget(self.save_new_preset_button, 0, 2, 1, 1)
        self.grid_presets.addWidget(self.add_new_preset_button, 0, 3, 1, 1)

        self.grid_presets.setColumnStretch(1, 0)

        self.grid.addLayout(self.grid_presets, 0, 0, 1, 0)

    def fill_presets_combo_box(self, current_preset=None):
        self.presets_combo_box.clear()

        current_idx = 0

        for i, preset in enumerate(self.presets_list):
            title = preset['title']
            if not title:
                title = preset['view']
            self.presets_combo_box.addItem(title)
            self.presets_combo_box.setItemData(i, preset)
            if preset['view'] == current_preset:
                current_idx = i

        self.presets_combo_box.setCurrentIndex(current_idx)

    def add_new_preset(self):

        add_preset_dialog = QtGui.QDialog(self)
        add_preset_dialog.setWindowTitle('Save as new Preset {}'.format(self.stype.get_pretty_name()))
        add_preset_dialog.setMinimumSize(320, 80)
        add_preset_dialog.setMaximumSize(450, 80)

        add_preset_dialog_layout = QtGui.QVBoxLayout()
        add_preset_dialog.setLayout(add_preset_dialog_layout)

        add_preset_dialog_line_edit = QtGui.QLineEdit('New Preset')

        add_preset_dialog_button = QtGui.QPushButton('Create and Save')

        add_preset_dialog_layout.addWidget(add_preset_dialog_line_edit)
        add_preset_dialog_layout.addWidget(add_preset_dialog_button)

        add_preset_dialog_button.clicked.connect(lambda: self.save_new_preset_to_server(
            pretty_preset_name=add_preset_dialog_line_edit.text()
        ))
        add_preset_dialog_button.clicked.connect(add_preset_dialog.close)

        add_preset_dialog.exec_()
        self.fill_presets_combo_box()

    def get_current_preset_name(self):
        current_index = self.presets_combo_box.currentIndex()
        return self.presets_combo_box.itemData(current_index)

    def get_current_preset_dict(self):
        preset_dict = self.get_preset_config(self.get_current_preset_name(), json=False)
        return preset_dict['data']

    def apply_search_preset(self, current_index=None, preset=None):

        if not preset:
            preset = self.presets_combo_box.itemData(current_index)

        if preset:
            filters_list = tc.unpack_tactic_search_view(preset['config_xml'])
            self.advanced_search_widget.set_filters(filters_list)
            tab_search_options = self.advanced_search_widget.get_tab_search_options_widget()
            tab_search_options.set_edit_tab_title(preset.get('title'))

    def get_preset_by_name(self, preset_name):
        # Only used on initial items filling
        if self.presets_list:
            for preset in self.presets_list:
                if preset['preset_name'] == preset_name:
                    return preset

    def get_presets_list(self):
        return self.presets_list

    def get_all_presets_from_server(self):

        project = env_inst.get_project_by_code()
        views = project.get_config_views()

        filters = [('view', 'like', '%{0}'.format(self.get_tab_name())), ('search_type', self.stype.get_code())]
        # filters = [('view', 'like', '{0}%'.format('link_search')), ('search_type', self.stype.get_code())]

        self.presets_list = []

        # actual server request
        presets = views.update_views(filters)

        if presets:
            self.presets_list = presets
            views_list = views.get_views(presets, bs=True)
            for preset, view in zip(self.presets_list, views_list):
                preset['config_xml'] = view

    def get_preset_config(self, preset_name=None, pretty_preset_name=None, view=None):

        if not preset_name:
            preset_name = 'default'

        if not pretty_preset_name:
            pretty_preset_name = preset_name.capitalize().replace('_', ' ')

        if not view:
            view = 'link_search:{0}:{1}'.format(preset_name, self.get_tab_name())

        category = 'search_filter'
        search_type = self.stype.get_code()
        title = pretty_preset_name

        filters_list = self.advanced_search_widget.get_filters_state()
        filters_list = tc.pack_tactic_search_view(filters_list)

        # we dont have metadata, so user description for metadata
        data_dict = {'data': 'assa'}

        config = '<config>\n    <filter>\n        <values type="json">{0}</values>\n    </filter>\n</config>'.format(filters_list)

        data = {
            'description': data_dict,
            'view': view,
            'login': '',
            'category': category,
            'search_type': search_type,
            'title': title,
            'config': config
        }

        return data

    # def save_current_preset(self):
    #     print('SAVED PRESET')
    #     self.save_preset_to_server('new_preset', 'New Preset')

    def delete_preset_from_server(self, preset=None):

        if not preset:
            idx = self.presets_combo_box.currentIndex()
            preset = self.presets_combo_box.itemData(idx)

        if preset:

            # ask before delete
            buttons = (('Yes', QtGui.QMessageBox.YesRole), ('Cancel', QtGui.QMessageBox.NoRole))

            title = preset['title']
            if not title:
                title = preset['view']

            reply = gf.show_message_predefined(
                'Removing preset from server',
                u'Are You sure want to remove <b>" {0} "</b> preset from Server?'.format(title),
                buttons=buttons,
                message_type='question',
                parent=self
            )

            if reply == QtGui.QMessageBox.YesRole:

                server = tc.server_start(project=env_inst.get_current_project())

                search_type = 'config/widget_config'

                # Checking for existing key
                filters = [('code', preset['code'])]

                widget_settings = server.query(search_type, filters, single=True)

                search_key = widget_settings['__search_key__']

                server.delete_sobject(search_key)

                self.get_all_presets_from_server()
                self.fill_presets_combo_box()

    def save_preset_to_server(self, preset=None, pretty_preset_name=None):

        if not preset:
            idx = self.presets_combo_box.currentIndex()
            preset = self.presets_combo_box.itemData(idx)

        if preset:

            view = preset.get('view')

            if not pretty_preset_name:
                tab_search_options = self.advanced_search_widget.get_tab_search_options_widget()
                edit_tab_title = tab_search_options.get_edit_tab_title()
                if edit_tab_title:
                    pretty_preset_name = edit_tab_title
                else:
                    pretty_preset_name = preset.get('title')

            data = self.get_preset_config(pretty_preset_name=pretty_preset_name, view=view)
            search_type = 'config/widget_config'

            # Checking for existing view
            filters = [('view', data['view']), ('search_type', data['search_type'])]
            columns = ['code']

            server = tc.server_start(project=env_inst.get_current_project())
            widget_config = server.query(search_type, filters, columns, single=True)

            if widget_config:
                code = widget_config['code']
                search_key = server.build_search_key(search_type, code, project_code=env_inst.get_current_project())

                server.insert_update(search_key, data, triggers=False)
            else:
                server.insert(search_type, data, triggers=False)

            self.get_all_presets_from_server()
            self.fill_presets_combo_box(preset)

    def save_new_preset_to_server(self, pretty_preset_name=None):
        preset_name = pretty_preset_name.lower().replace(' ', '_')
        print(preset_name)
        print(pretty_preset_name)
        preset = self.get_preset_config(preset_name, pretty_preset_name)

        # if not preset:
        #     idx = self.presets_combo_box.currentIndex()
        #     preset = self.presets_combo_box.itemData(idx)

        view = preset.get('view')

        # if not pretty_preset_name:
        #     tab_search_options = self.advanced_search_widget.get_tab_search_options_widget()
        #     edit_tab_title = tab_search_options.get_edit_tab_title()
        #     if edit_tab_title:
        #         pretty_preset_name = edit_tab_title
        #     else:
        #         pretty_preset_name = preset.get('title')

        data = self.get_preset_config(pretty_preset_name=pretty_preset_name, view=view)
        search_type = 'config/widget_config'

        # Checking for existing view
        filters = [('view', data['view']), ('search_type', data['search_type'])]
        columns = ['code']

        server = tc.server_start(project=env_inst.get_current_project())
        widget_config = server.query(search_type, filters, columns, single=True)

        if widget_config:
            code = widget_config['code']
            search_key = server.build_search_key(search_type, code, project_code=env_inst.get_current_project())

            server.insert_update(search_key, data, triggers=False)
        else:
            server.insert(search_type, data, triggers=False)

        self.get_all_presets_from_server()
        self.fill_presets_combo_box(preset)

    def get_settings_dict(self):
        settings_dict = {
            'presets_combo_box': self.presets_combo_box.currentIndex(),
        }
        return settings_dict

    def set_settings_from_dict(self, settings_dict=None):
        ref_settings_dict = {
            'presets_combo_box': 0,
        }

        settings = gf.check_config(ref_settings_dict, settings_dict)

        initial_index = self.presets_combo_box.currentIndex()

        self.presets_combo_box.setCurrentIndex(int(settings['presets_combo_box']))

        if initial_index == int(settings['presets_combo_box']):
            self.apply_search_preset(initial_index)

    def refresh_search_widget(self):

        checkin_out = env_inst.get_check_tree(self.stype.get_project().get_code(), 'checkin_out', self.get_tab_name())

        if checkin_out:
            checkin_out.refresh_current_results()

    def get_tab_name(self):
        return self.tab_name

    def readSettings(self):
        group_path = 'ui_search/{0}/{1}/{2}'.format(
            self.stype.project.info['type'],
            self.stype.project.info['code'],
            self.get_tab_name()
        )
        self.set_settings_from_dict(
            env_read_config(
                filename='ui_filter_editor',
                unique_id=group_path,
                long_abs_path=True
            )
        )

    def writeSettings(self):
        group_path = 'ui_search/{0}/{1}/{2}'.format(
            self.stype.project.info['type'],
            self.stype.project.info['code'],
            self.get_tab_name()
        )
        env_write_config(
            self.get_settings_dict(),
            filename='ui_filter_editor',
            unique_id=group_path,
            long_abs_path=True
        )

    def closeEvent(self, event):
        self.writeSettings()
        self.deleteLater()
        event.accept()
