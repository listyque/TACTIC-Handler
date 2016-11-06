# file maya_functions.py
# Maya Functions Module

import os
import PySide.QtGui as QtGui
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import shiboken
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
    maya_dock_instances = get_maya_window().findChildren(QtGui.QMainWindow, 'TacticDockWindow')
    return maya_dock_instances


def open_scene(file_path, dir_path, all_process):
    # check if scene need saving
    new_scene = mel.eval('saveChanges("file -f -new")')
    if new_scene:
        # print('Opening: ' + file_path)
        set_workspace(dir_path, all_process)
        cmds.file(file_path, o=True)

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


def new_save_scene(search_key, context, description, snapshot_type='file', all_process=None, repo=None, update_versionless=True, file_types='maya', postfixes=None, version=None, ext_type=None, is_current=False, is_revision=False, mode=None, create_playblast=True):

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

    print exts, 'exts'
    print file_types, ''
    print file_names, ''
    print postfixes, ''
    print subfolders, ''

    if create_playblast:
        exts.extend(['jpg', 'jpg', 'png'])
        file_types.extend(['playblast', 'web', 'icon'])
        file_names.extend(['', '', ''])
        postfixes.extend(['playblast', '', ''])
        subfolders.extend(['__preview', '__preview', '__preview'])

    # ask user to confirm saving
    virtual_snapshot = tc.checkin_virtual_snapshot(
        search_key,
        context,
        snapshot_type=snapshot_type,
        ext=exts,
        file_type=file_types,
        file_name=file_names,
        file_postfix=postfixes,
        subfolders=subfolders,
        is_revision=is_revision,
        repo=repo,
        update_versionless=update_versionless,
        keep_file_name=False,
        version=version,
    )

    if virtual_snapshot:
        # save maya scene to destined folder
        dest_path_ver = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['versioned']['paths'][0])
        dest_scene_ver = dest_path_ver + '/' + virtual_snapshot['versioned']['names'][0]

        dest_path_playblast_ver = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['versioned']['paths'][1])
        dest_playblast_ver = dest_path_playblast_ver + '/' + virtual_snapshot['versioned']['names'][1]
        dest_web_ver = dest_path_playblast_ver + '/' + virtual_snapshot['versioned']['names'][2]
        dest_icon_ver = dest_path_playblast_ver + '/' + virtual_snapshot['versioned']['names'][3]

        # create dest dirs
        if not os.path.exists(dest_path_ver):
            os.makedirs(dest_path_ver)
        if not os.path.exists(dest_path_playblast_ver):
            os.makedirs(dest_path_playblast_ver)

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
            cmds.file(save=True, type=ext_type)
            saved = True
        except:
            saved = False

        progres_bar = env_inst.ui_check_tree['checkin'][search_key.split('?')[0]].progres_bar
        check_ok = True

        if renamed and saved:
            if setting_workspace:
                set_workspace(dest_scene_ver, all_process)

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
                offScreen=True,
                viewer=False,
                percent=100
            )

            mode = 'inplace'

            tc.generate_web_and_icon(dest_playblast_ver, dest_web_ver, dest_icon_ver)

            file_paths = [dest_scene_ver, dest_playblast_ver, dest_web_ver, dest_icon_ver]

            check_ok = tc.inplace_checkin(
                file_paths,
                progres_bar,
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
            progres_bar.setValue(100)

        progres_bar.setVisible(False)

        if check_ok:
            return True
        else:
            return False
    else:
        return False

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
