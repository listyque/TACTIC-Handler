import os
import sys
import random
import urllib
import zipfile
import maya.mel as mel


try:
    import PySide.QtGui as QtGui
except:
    import PySide2.QtWidgets as QtGui


def get_file_path():
    return os.path.dirname(__file__)


SHELF_NAME = 'TacticHandler'

# This can be used to create preconfigured installations, with custom shelf buttons and configs,
# just add more presets and urls
INSTALL_PRESETS = {
    'Default': 'https://github.com/listyque/TACTIC-Handler/archive/stable.zip',
}
DROP_PATH = get_file_path()
INSTALLED_PATH = ''
SERVER_NAME = 'localhost:9123'


def preconfigure_tactic_handler(repo_path=None, login=None, server_url=None):

    if INSTALLED_PATH not in sys.path:
        sys.path.append(INSTALLED_PATH)

    import thlib.environment as thenv
    thenv.env_mode.set_current_path(INSTALLED_PATH)
    thenv.env_mode.set_mode('maya')

    if login:
        print 'setting login', login
        thenv.env_server.set_server(
            server_name=server_url,
        )
        thenv.env_server.set_timeout(
            timeout=180,
        )
        thenv.env_server.set_user(
            user_name=login,
        )

        thenv.env_server.set_site(
            site_name='',
            enabled=False,
        )

        thenv.env_server.set_proxy(
            proxy_login='',
            proxy_pass='',
            proxy_server='',
            enabled=False,
        )

        kwargs = thenv.tc().generate_new_ticket(login)
        thenv.tc().server_auth(**kwargs)

        if thenv.env_server.get_ticket():
            thenv.env_server.set_ticket(thenv.env_server.get_ticket())

        thenv.env_server.save_server_presets_defaults()
        thenv.env_server.save_defaults()

    if repo_path:
        thenv.env_tactic.get_base_dirs()

        print 'setting repo', repo_path
        base_dir = [u'{0}'.format(repo_path), u'General', [128, 128, 128], u'base', True]
        thenv.env_tactic.set_base_dir('base', base_dir)
        thenv.env_tactic.save_base_dirs()


def check_shelf_exists(shelf_name):
    mel.eval("""
global proc int check_shelf_exists(string $shelf_name)
//procedure from validateShelfName
{
    int $fileExists = false;
    string $shelfDirs = `internalVar -userShelfDir`;
    string $shelfArray[];
    string $PATH_SEPARATOR = `about -win`? ";" : ":";
    tokenize($shelfDirs, $PATH_SEPARATOR, $shelfArray);
    for( $i = 0; $i < size($shelfArray); $i++ ) {
        string $fileName = ($shelfArray[$i] + "shelf_" + $shelf_name + ".mel");
        if (`file -q -exists $fileName`) {
            $fileExists = true;
            break;
        }
    }
    return $fileExists;
}
""")
    exists = mel.eval('int $shelf_exists = check_shelf_exists("{0}");'.format(shelf_name))
    return bool(int(exists))


def download_archive(url=None, dest_path=None):
    archive_path = u'{0}/TACTIC-handler.zip'.format(dest_path)

    if os.path.exists(archive_path):
        os.remove(archive_path)

    rand_url = u'{0}?{1}'.format(url, random.randint(0, 99999))

    urllib.urlretrieve(rand_url, archive_path)

    return archive_path


def unpdack_archive(install_path, url=None):

    from_git = False
    if url.find('github.com') != -1:
        from_git = True

    archive_path = download_archive(url, install_path)

    extract_path = u'{0}/TACTIC-handler'.format(install_path)

    if from_git:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            members = []
            for member in zip_ref.infolist():
                sub_dir = member.filename.split('/')[0]
                member.filename = member.filename.replace(sub_dir, '')
                members.append(member)

            zip_ref.extractall(extract_path, members)
        zip_ref.close()
    else:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

    if os.path.exists(archive_path):
        os.remove(archive_path)


def add_shelf(shelf):
    delete_shelf(shelf)
    if not check_shelf_exists(shelf):
        mel.eval('addNewShelfTab "{0}";'.format(shelf))


def delete_shelf(shelf):
    if check_shelf_exists(shelf):
        mel.eval('deleteShelfTab "{}";'.format(shelf))
        mel.eval('global proc shelf_{} () '.format(shelf) + '{global string $gBuffStr;global string $gBuffStr0;global string $gBuffStr1;}')


def add_button_to_maya_shelf(shelf, procedure='', image=u'', annotation='', label='', overlay_label=''):

    mel_command = """shelfButton -parent {0}
-command "{1}"
-image1 "{2}"
-ann "{3}"
-label "{4}"
-imageOverlayLabel "{5}"
-sourceType "python"
-overlayLabelColor 0.89 0.89 0.89
-overlayLabelBackColor 0 0 0 0.6
-style `shelfLayout -q -style "{0}"`
-width `shelfLayout -q -cellWidth "{0}"`
-height `shelfLayout -q -cellHeight "{0}"`;
""".format(
        shelf,
        procedure,
        image,
        annotation,
        label,
        overlay_label
    )

    mel.eval(mel_command)


def add_th_button(shelf):

    extract_path = u'{0}/TACTIC-handler'.format(DROP_PATH)
    path_to_app = "CURRENT_PATH = '{0}'".format(extract_path)
    procedure = r"{0}\nimport sys\nif CURRENT_PATH not in sys.path:\n    sys.path.append(CURRENT_PATH)\nimport thlib.environment as thenv\nthenv.env_mode.set_current_path(CURRENT_PATH)\nthenv.env_mode.set_mode('maya')\nimport thlib.ui_classes.ui_maya_dock as main\nreload(main)\nmain.startup(hotkeys=None)".format(path_to_app)

    global INSTALLED_PATH
    INSTALLED_PATH = extract_path

    image = u'{0}/thlib/ui/gliph/maya_shelf/tactic_logo.png'.format(extract_path)
    annotation = 'This will Start Main Window of Tactic Handler'
    label = 'Tactic Handler'
    overlay_label = ''

    add_button_to_maya_shelf(
        shelf=shelf,
        procedure=procedure,
        image=image,
        annotation=annotation,
        label=label,
        overlay_label=overlay_label
    )


def add_append_save_button(shelf):
    procedure = r"\nimport thlib.environment as thenv\n\ndef append_checkin_current_scene():\n    search_key = thenv.mf().get_skey_from_scene()\n        \n    skey = thenv.tc().parce_skey(search_key, True)\n    split_skey = thenv.tc().split_search_key(skey['search_key'])\n    sobject, add_data1 = thenv.tc().get_sobjects_new(search_type=split_skey['search_type'], filters=[(u'code', split_skey['asset_code'])], order_bys=['name'])\n    if sobject:\n        sobject = sobject.values()[0]\n        print u'Making server checkin for current scene {}'.format(sobject.get_title())\n        search_key = sobject.get_search_key()\n        scene_search_key = thenv.mf().get_skey_from_scene()\n        skey = thenv.tc().parce_skey(scene_search_key, True)\n        skey_dict = thenv.tc().parce_skey(scene_search_key, return_sobject=False)\n        # Opening project and creating desired checkin UI\n\n        thenv.env_inst.ui_main.create_project_dock(skey_dict['project'], False)\n        checkin_widget = thenv.env_inst.get_check_tree(project_code=skey_dict['project'], tab_code='checkin_out', wdg_code='{0}/{1}'.format(skey_dict['namespace'], skey_dict['pipeline_code']))\n        checkin_widget.do_creating_ui()\n        \n        commit_queue_ui = checkin_widget.checkin_from_maya(search_key, skey['context'], 'Fast Save')\n        \nappend_checkin_current_scene()\n"

    image = u'{0}/TACTIC-handler/thlib/ui/gliph/maya_shelf/content-save-edit.png'.format(DROP_PATH)
    annotation = 'Click to Save Current Scene As a new Version'
    label = 'Append Save Current Scene'
    overlay_label = 'save'

    add_button_to_maya_shelf(
        shelf=shelf,
        procedure=procedure,
        image=image,
        annotation=annotation,
        label=label,
        overlay_label=overlay_label
    )


def add_buttons(shelf_name, preset):
    add_th_button(shelf_name)

    if preset == 'Default':
        add_append_save_button(shelf_name)


def create_main_dialog():
    main_window = QtGui.QDialog()
    main_window.setWindowTitle('Drag and Drop Installation')
    main_window.resize(550, 80)
    main_layout = QtGui.QGridLayout()

    main_window.setLayout(main_layout)

    input_label = QtGui.QLabel('Install Path: ')
    install_path_line_edit = QtGui.QLineEdit(main_window)
    install_path_line_edit.setText(get_file_path())

    server_path_label = QtGui.QLabel('TACTIC Server Url : ')
    server_path_line_edit = QtGui.QLineEdit(main_window)
    server_path_line_edit.setText(SERVER_NAME)

    repo_path_label = QtGui.QLabel('Repository Path (empty if reinstall) : ')
    repo_path_line_edit = QtGui.QLineEdit(main_window)
    repo_path_line_edit.setText('')

    login_label = QtGui.QLabel('Tactic Login (empty if reinstall): ')
    login_line_edit = QtGui.QLineEdit(main_window)
    login_line_edit.setText('')

    install_button = QtGui.QPushButton('Install / Reinstall')
    uninstall_button = QtGui.QPushButton('Uninstall')

    main_layout.addWidget(input_label, 0, 0)
    main_layout.addWidget(install_path_line_edit, 0, 1)

    main_layout.addWidget(server_path_label, 1, 0)
    main_layout.addWidget(server_path_line_edit, 1, 1)

    main_layout.addWidget(repo_path_label, 2, 0)
    main_layout.addWidget(repo_path_line_edit, 2, 1)

    main_layout.addWidget(login_label, 3, 0)
    main_layout.addWidget(login_line_edit, 3, 1)

    buttons_layout = QtGui.QHBoxLayout()
    buttons_layout.addWidget(install_button)
    buttons_layout.addWidget(uninstall_button)
    main_layout.addLayout(buttons_layout, 4, 0, 1, 0)

    presets_combo_box = QtGui.QComboBox()

    for preset in INSTALL_PRESETS.keys():
        presets_combo_box.addItem(preset)

    main_layout.addWidget(presets_combo_box, 5, 0, 1, 0)

    install_button.clicked.connect(lambda: install(install_path_line_edit.text(), server_path_line_edit.text(), presets_combo_box.currentText(), repo_path_line_edit.text(), login_line_edit.text()))
    uninstall_button.clicked.connect(lambda: delete_shelf(SHELF_NAME))

    return main_window


def install(install_path, server_url, preset=None, repo_path=None, login=None):

    main_window.close()

    url = INSTALL_PRESETS.get(preset)

    unpdack_archive(install_path, url=url)
    add_shelf(SHELF_NAME)
    add_buttons(SHELF_NAME, preset)

    preconfigure_tactic_handler(repo_path, login, server_url)


def begin_shelf_install():
    main_window = create_main_dialog()
    global main_window
    main_window.exec_()
