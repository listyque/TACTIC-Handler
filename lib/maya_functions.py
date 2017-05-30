# file maya_functions.py
# Maya Functions Module

import os
import collections
# import PySide.QtGui as QtGui
from lib.side.Qt import QtWidgets as QtGui

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
try:
    import shiboken as shiboken
except:
    import shiboken2 as shiboken

import tactic_classes as tc
from lib.environment import env_inst
import global_functions as gf


def get_maya_window():
    """
    Get the main Maya window as a QtGui.QMainWindow instance
    @return: QtGui.QMainWindow instance of the Maya windows
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if main_window_ptr is not None:
        return shiboken.wrapInstance(long(main_window_ptr), QtGui.QMainWindow)


def get_maya_dock_window():
    """
    Get the Maya dock window instance of Tactic Dock Window
    @return: QMayaDockWidget
    """
    maya_dock_instances = get_maya_window().findChildren(QtGui.QMainWindow, 'TacticHandlerDock')
    return maya_dock_instances


def open_scene(file_path, dir_path, all_process):
    # check if scene need saving
    new_scene = mel.eval('saveChanges("file -f -new")')
    if bool(new_scene):
        print('Opening: ' + file_path)
        # set_workspace(dir_path, all_process)
        cmds.file(file_path, open=True, force=True)

        # cmds.file(q=True, location=True)  #prtint current scene path


def import_scene(file_path):
    print('Importing: ' + file_path)
    cmds.file(file_path, i=True)


def reference_scene(file_path):
    print('Referencing: ' + file_path)
    cmds.file(file_path, r=True)


def get_skey_from_scene():
    skey = cmds.getAttr('defaultObjectSet.tacticHandler_skey')
    return skey


def export_selected(project_code, tab_code, wdg_code):

    current_type = cmds.optionVar(q='defaultFileExportActiveType')
    current_ext = cmds.translator(str(current_type), q=True, filter=True)
    current_ext = current_ext.split(';')[0]

    current_checkin_widget = env_inst.get_check_tree(project_code, tab_code, wdg_code)

    current_checkin_widget.save_file(selected_objects=[True, {current_type: current_ext[2:]}])


def save_as(project_code, tab_code, wdg_code):

    current_type = cmds.optionVar(q='defaultFileSaveType')
    current_ext = cmds.translator(str(current_type), q=True, filter=True)
    current_ext = current_ext.split(';')[0]

    current_checkin_widget = env_inst.get_check_tree(project_code, tab_code, wdg_code)

    current_checkin_widget.save_file(selected_objects=[False, {current_type: current_ext[2:]}])


def wrap_export_selected_options(project_code, tab_code, wdg_code):
    mel.eval('proc export_selection_maya(){python("' +
             "main.mf.export_selected('{0}', '{1}', '{2}')".format(project_code, tab_code, wdg_code) +
             '");}fileOptions "ExportActive" "export_selection_maya";')


def wrap_save_options(project_code, tab_code, wdg_code):
    mel.eval('proc save_as_maya(){python("' +
             "main.mf.save_as('{0}', '{1}', '{2}')".format(project_code, tab_code, wdg_code) +
             '");}fileOptions "SaveAs" "save_as_maya";')


def new_save_scene(search_key, context, description, snapshot_type='file', all_process=None, repo=None, update_versionless=True, file_types='maya', postfixes=None, version=None, ext_type=None, is_current=False, is_revision=False, mode=None, create_playblast=True, selected_objects=False, parent_wdg=None):

    types = {
        'mayaBinary': 'mb',
        'mayaAscii': 'ma',
    }

    setting_workspace = False

    exts = [types[ext_type]]
    file_types = [file_types]
    file_names = ['']
    postfixes = ['']
    subfolders = ['']

    files_dict = collections.OrderedDict()

    for i, fn in enumerate(file_names):
        file_dict = dict()
        file_dict['t'] = [file_types[i]]
        file_dict['p'] = [postfixes[i]]
        file_dict['s'] = [subfolders[i]]
        file_dict['e'] = [exts[i]]

        files_dict[fn] = file_dict

    # extending files which can have thumbnails
    for key, val in files_dict.items():
        val['e'].extend(['jpg', 'jpg', 'png'])
        val['p'].extend(['playblast', '', ''])
        val['t'].extend(['playblast', 'web', 'icon'])
        val['s'].extend(['__preview', '__preview/web', '__preview/web'])

    virtual_snapshot = tc.checkin_virtual_snapshot(
        search_key,
        context,
        snapshot_type=snapshot_type,
        files_dict=files_dict,
        is_revision=is_revision,
        repo=repo,
        update_versionless=update_versionless,
        version=version,
    )

    if virtual_snapshot:
        # save maya scene to destined folder
        dest_path_ver = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['versioned']['paths'][0])
        dest_scene_ver = dest_path_ver + '/' + virtual_snapshot['versioned']['names'][0]
        dest_path_playblast_ver = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['versioned']['paths'][1])
        dest_playblast_ver = dest_path_playblast_ver + '/' + virtual_snapshot['versioned']['names'][1]
        dest_path_web_ver = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['versioned']['paths'][2])
        dest_web_ver = dest_path_web_ver + '/' + virtual_snapshot['versioned']['names'][2]
        dest_path_icon_ver = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['versioned']['paths'][3])
        dest_icon_ver = dest_path_icon_ver + '/' + virtual_snapshot['versioned']['names'][3]

        # create dest dirs
        if not os.path.exists(dest_path_ver):
            os.makedirs(dest_path_ver)
        if not os.path.exists(dest_path_playblast_ver):
            os.makedirs(dest_path_playblast_ver)
        if not os.path.exists(dest_path_web_ver):
            os.makedirs(dest_path_web_ver)

        # add info about particular scene
        skey_link = 'skey://{0}&context={1}'.format(search_key, context)
        if not cmds.attributeQuery('tacticHandler_skey', node='defaultObjectSet', exists=True):
            cmds.addAttr('defaultObjectSet', longName='tacticHandler_skey', dataType='string')
        cmds.setAttr('defaultObjectSet.tacticHandler_skey', skey_link, type='string')

        # saving maya scene
        try:
            cmds.file(rename=dest_scene_ver)
            renamed = True
        except:
            renamed = False
        try:
            if selected_objects:
                cmds.file(exportSelected=selected_objects, type=ext_type, preserveReferences=True, exportUnloadedReferences=True)
            else:
                cmds.file(save=True, type=ext_type)
            saved = True
        except:
            saved = False

        progress_bar = parent_wdg.search_results_widget.get_progress_bar()
        check_ok = True

        if renamed and saved:
            if setting_workspace:
                set_workspace(dest_scene_ver, all_process)

            # isolate selected to create proper playblast
            current_panel = cmds.paneLayout('viewPanes', q=True, pane1=True)
            if selected_objects:
                cmds.isolateSelect(current_panel, state=True)
                mel.eval('enableIsolateSelect {0} 1;'.format(current_panel))

            current_frame = cmds.currentTime(query=True)
            cmds.playblast(
                forceOverwrite=True,
                format='image',
                completeFilename=dest_playblast_ver,
                showOrnaments=False,
                widthHeight=[960, 540],
                sequenceTime=False,
                frame=[current_frame],
                compression='jpg',
                offScreen=False,
                viewer=False,
                percent=100
            )
            if selected_objects:
                cmds.isolateSelect(current_panel, state=False)
                mel.eval('enableIsolateSelect {0} 0;'.format(current_panel))
            mode = 'inplace'

            tc.generate_web_and_icon(dest_playblast_ver, dest_web_ver, dest_icon_ver)

            file_paths = [dest_scene_ver, dest_playblast_ver, dest_web_ver, dest_icon_ver]

            check_ok = tc.inplace_checkin(
                file_paths,
                progress_bar,
                virtual_snapshot,
                repo,
                update_versionless,
                check_ok
            )

            if check_ok:
                relative_paths = []
                file_sizes = []
                for fp in file_paths:
                    file_sizes.append(gf.get_st_size(fp))

                tc.checkin_snapshot(
                    search_key,
                    context,
                    snapshot_type=snapshot_type,
                    is_revision=is_revision,
                    description=description,
                    version=version,
                    update_versionless=update_versionless,
                    file_types=file_types,
                    file_names=file_names,
                    file_paths=file_paths,
                    relative_paths=relative_paths,
                    file_sizes=file_sizes,
                    exts=exts,
                    keep_file_name=False,
                    repo_name=repo['value'][3],
                    virtual_snapshot=virtual_snapshot,
                    mode=mode,
                    create_icon=False
                )
            progress_bar.setValue(100)

        progress_bar.setVisible(False)

        if check_ok:
            return True
        else:
            return False
    else:
        return False


def set_info_to_scene(search_key, context):
    # add info about particular scene
    skey_link = 'skey://{0}&context={1}'.format(search_key, context)
    if not cmds.attributeQuery('tacticHandler_skey', node='defaultObjectSet', exists=True):
        cmds.addAttr('defaultObjectSet', longName='tacticHandler_skey', dataType='string')
    cmds.setAttr('defaultObjectSet.tacticHandler_skey', skey_link, type='string')


def inplace_checkin(progress_bar, virtual_snapshot, repo_name, update_versionless, generate_icons=True,
                    selected_objects=False, ext_type='mayaAscii', setting_workspace=False):

    scene_name = None
    playblast_name = None
    scene_path = None
    playblast_path = None

    for snapshot in virtual_snapshot:
        # pprint(snapshot)
        if snapshot[0] == 'scene':
            scene_name = snapshot[1]['versioned']['names'][0]
            scene_path = gf.form_path(repo_name['value'][0] + '/' + snapshot[1]['versioned']['paths'][0])
        else:
            playblast_name = snapshot[1]['versioned']['names'][0]
            playblast_path = gf.form_path(repo_name['value'][0] + '/' + snapshot[1]['versioned']['paths'][0])

    full_scene_path = scene_path + '/' + scene_name
    full_playblast_path = playblast_path + '/' + playblast_name

    # create dest dirs
    if not os.path.exists(scene_path):
        os.makedirs(scene_path)
    if not os.path.exists(playblast_path):
        os.makedirs(playblast_path)

    print ext_type
    print full_playblast_path
    print full_scene_path

    # saving maya scene
    try:
        cmds.file(rename=full_scene_path)
        renamed = True
    except:
        renamed = False
    try:
        if selected_objects:
            cmds.file(exportSelected=selected_objects, type=ext_type, pr=True, eur=True)
        else:
            cmds.file(save=True, type=ext_type)
        saved = True
    except:
        saved = False

    check_ok = True

    if renamed and saved:
        if setting_workspace:
            print 'SETTING WORKSPACE'
            # set_workspace(dest_scene_ver, all_process)

        # isolate selected to create proper playblast
        current_panel = cmds.paneLayout('viewPanes', q=True, pane1=True)
        if selected_objects:
            cmds.isolateSelect(current_panel, state=True)
            mel.eval('enableIsolateSelect {0} 1;'.format(current_panel))

        current_frame = cmds.currentTime(query=True)
        cmds.playblast(
            forceOverwrite=True,
            format='image',
            completeFilename=full_playblast_path,
            showOrnaments=False,
            widthHeight=[960, 540],
            sequenceTime=False,
            frame=[current_frame],
            compression='jpg',
            offScreen=False,
            viewer=False,
            percent=100
        )
        if selected_objects:
            cmds.isolateSelect(current_panel, state=False)
            mel.eval('enableIsolateSelect {0} 0;'.format(current_panel))

        # mode = 'inplace'

        file_paths = [full_scene_path, full_playblast_path]

        check_ok = tc.inplace_checkin(
            file_paths,
            progress_bar,
            virtual_snapshot,
            repo_name,
            update_versionless,
            generate_icons,
        )

    return check_ok

# deprecated
"""
def save_scene(search_key, context, description, all_process, repo):
    print repo

    # add info about particular scene
    skey_link = 'skey://{0}&context={1}'.format(search_key, context)
    if not cmds.attributeQuery('tacticHandler_skey', node='defaultObjectSet', exists=True):
        cmds.addAttr('defaultObjectSet', longName='tacticHandler_skey', dataType='string')
    cmds.setAttr('defaultObjectSet.tacticHandler_skey', skey_link, type='string')

    # get template names for scene and playblast image
    temp_dir = env.Env.get_temp_dir()
    random_uuid = uuid.uuid4()

    types = {
        'mayaBinary': 'mb',
        'mayaAscii': 'ma',
    }
    temp_file = '{0}/{1}.ma'.format(temp_dir, random_uuid)
    temp_playblast = '{0}/{1}.jpg'.format(temp_dir, random_uuid)

    # rename file, save scene, playblast, get saving format
    cmds.file(rename=temp_file)
    cmds.file(save=True, type='mayaAscii')
    current_frame = cmds.currentTime(query=True)
    cmds.playblast(
        forceOverwrite=True,
        format='image',
        completeFilename=temp_playblast,
        showOrnaments=False,
        widthHeight=[960, 540],
        sequenceTime=False,
        frame=[current_frame],
        compression='jpg',
        offScreen=True,
        viewer=False,
        percent=100
    )

    # check in snapshot
    snapshot = tc.checkin_snapshot(search_key, context, temp_file, file_type='maya', is_current=True,
                                   description=description)

    # from pprint import pprint
    # pprint(snapshot)
    # retrieve checked in snapshot file info
    asset_dir = env.Env.get_asset_dir()
    file_sobject = snapshot['__file_sobjects__'][0]
    relative_dir = file_sobject['relative_dir']
    file_name = file_sobject['file_name']

    # make proper file path, and dir path to set workspace
    new_file = '{0}/{1}/{2}'.format(asset_dir, relative_dir, file_name)
    split_path = relative_dir.split('/')

    dir_path = '{0}/{1}'.format(asset_dir, '/'.join(split_path[:-3]))

    # set proper scene name
    cmds.file(rename=new_file)

    set_workspace(dir_path, all_process)

    # check in playblast
    tc.checkin_playblast(snapshot['code'], temp_playblast)

    # playblast = tc.ServerThread()
    # playblast.kwargs = dict(snapshot_code=snapshot['code'], file_name=temp_playblast)
    # playblast.routine = tc.checkin_playblast
    # playblast.start()
"""


def create_workspace(dir_path, all_process):
    # TODO create maya definition editor, with presets
    workspace = ['//Maya 2016 Project Definition\n\n']
    consts_list = {
        'fluidCache': '',
        'images': '',
        'offlineEdit': '',
        'furShadowMap': '',
        'iprImages': '',
        'scripts': '',
        'renderData': '',
        'fileCache': '',
        'eps': '',
        'shaders': '',
        '3dPaintTextures': '',
        'translatorData': '',
        'mel': '',
        'furFiles': '',
        'OBJ': '',
        'particles': '',
        'scene': '',
        'sourceImages': '',
        'furEqualMap': '',
        'clips': '',
        'furImages': '',
        'depth': '',
        'movie': '',
        'audio': '',
        'bifrostCache': '',
        'autoSave': '',
        'mayaAscii': '',
        'move': '',
        'sound': '',
        'diskCache': '',
        'illustrator': '',
        'mayaBinary': '',
        'templates': '',
        'OBJexport': '',
        'furAttrMap': '',
    }

    for const, val in consts_list.iteritems():
        if (const == 'scene') or (const == 'mayaAscii') or (const == 'mayaBinary'):
            for process in all_process:
                val += 'work/{0};'.format(process)
        workspace.append('workspace -fr "{0}" "{1}";\n'.format(const, val))

    workspace_file = open(dir_path + "/workspace.mel", "w")
    workspace_file.writelines(workspace)
    workspace_file.close()


def set_workspace(dir_path, all_process):
    create_workspace(dir_path, all_process)
    # print('Setting Workspace: {0}'.format(dir_path))
    mel.eval('setProject "{0}";'.format(dir_path))
    mel.eval('projectWindow;np_editCurrentProjectCallback;')
