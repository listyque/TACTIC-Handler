# file maya_functions.py
# Maya Functions Module

import os
import PySide.QtGui as QtGui
# import PySide.QtCore as QtCore
# import uuid
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import shiboken
import tactic_classes as tc
# import environment as env
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


def new_save_scene(search_key, context, description, all_process, repo, update_versionless, version, ext, is_current, is_revision, create_playblast=True):

    # print repo

    types = {
        'mayaBinary': 'mb',
        'mayaAscii': 'ma',
    }

    # ask user to confirm saving
    save_confirm, virtual_snapshot = tc.checkin_virtual_snapshot(
        search_key,
        context,
        is_revision=is_revision,
        ext='',
        visible_ext=types[ext],
        repo=repo['name'],
        update_versionless=update_versionless,
        version=version,
        file_type='main'
    )

    if save_confirm:

        dest_file = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['relative_path'] + '/' + virtual_snapshot['file_name'] + '.' + types[ext])
        dest_path = gf.form_path(repo['value'][0] + '/' + virtual_snapshot['relative_path'])

        # create dest dirs
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        # add info about particular scene
        skey_link = 'skey://{0}&context={1}'.format(search_key, context)
        if not cmds.attributeQuery('tacticHandler_skey', node='defaultObjectSet', exists=True):
            cmds.addAttr('defaultObjectSet', longName='tacticHandler_skey', dataType='string')
        cmds.setAttr('defaultObjectSet.tacticHandler_skey', skey_link, type='string')

        # saving maya scene
        try:
            cmds.file(rename=dest_file)
            renamed = True
        except:
            renamed = False
        try:
            cmds.file(save=True, type=ext)
            saved = True
        except:
            saved = False

        if renamed and saved:
            # make proper file path, and dir path to set workspace TODO: make it proper, to work with naming
            # new_file = '{0}/{1}/{2}'.format(asset_dir, relative_dir, file_name)
            split_path = dest_path.split('/')

            dir_path = '/'.join(split_path[:-3])

            # print dir_path
            set_workspace(dir_path, all_process)

            dest_playblast = '{0}/{1}.jpg'.format(dest_path, virtual_snapshot['file_name'])

            if create_playblast:

                current_frame = cmds.currentTime(query=True)
                cmds.playblast(
                    forceOverwrite=True,
                    format='image',
                    completeFilename=dest_playblast,
                    showOrnaments=False,
                    widthHeight=[960, 540],
                    sequenceTime=False,
                    frame=[current_frame],
                    compression='jpg',
                    offScreen=True,
                    viewer=False,
                    percent=100
                )

            #create empty snapshot
            snapshot = tc.new_checkin_snapshot(
                search_key,
                context,
                is_current=is_current,
                is_revision=is_revision,
                ext='',
                description=description,
                repo=repo,
                version=version,
            )

            # checkin saved scene to dest path
            tc.server_start().add_file(
                snapshot.get('code'),
                dest_file,
                file_type='maya',
                create_icon=False,
                checkin_type='auto',
                mode='preallocate',
                custom_repo_path=repo['value'][0],
                do_update_versionless=update_versionless,
            )
            if create_playblast:
                # check in playblast
                tc.checkin_playblast(snapshot['code'], dest_playblast, repo['value'][0])

            # adding info about repository to snapshots
            tc.add_repo_info(search_key, context, snapshot, repo)

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
        'images': 'renders',
        'offlineEdit': '',
        'furShadowMap': '',
        'iprImages': '',
        'scripts': '',
        'renderData': '',
        'fileCache': '',
        'eps': '',
        'shaders': '',
        '3dPaintTextures': 'textures/3dPaintTextures',
        'translatorData': '',
        'mel': '',
        'furFiles': '',
        'OBJ': '',
        'particles': 'particles',
        'scene': '',
        'sourceImages': 'textures',
        'furEqualMap': '',
        'clips': '',
        'furImages': '',
        'depth': '',
        'movie': 'playblast',
        'audio': '',
        'bifrostCache': '',
        'autoSave': 'autosave',
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
