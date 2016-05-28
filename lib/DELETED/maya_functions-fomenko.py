# file maya_functions.py
# Maya Functions Module

import PySide.QtGui as QtGui
import uuid
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel
import shiboken
import tactic_classes as tc
import environment as env


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
        print('Opening: ' + file_path)
        set_workspace(dir_path, all_process)
        cmds.file(file_path, o=True)

        # cmds.file(q=True, location=True)  #prtint current scene path


def import_scene(file_path):
    print('Importing: ' + file_path)
    cmds.file(file_path, i=True)


def reference_scene(file_path):
    print('Referencing: ' + file_path)
    cmds.file(file_path, r=True)


def save_scene(search_key, context, description, all_process):

    # add info about particular scene
    skey_link = 'skey://{0}&context={1}'.format(search_key, context)
    if not cmds.attributeQuery('tacticHandler_skey', node='defaultObjectSet', exists=True):
        cmds.addAttr('defaultObjectSet', longName='tacticHandler_skey', dataType='string')
    cmds.setAttr('defaultObjectSet.tacticHandler_skey', skey_link, type='string')

    # get template names for scene and playblast image
    temp_dir = env.Env().get_temp_dir()
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

    from pprint import pprint
    pprint(snapshot)
    # retrieve checked in snapshot file info
    asset_dir = env.Env().get_asset_dir()
    file_sobject = snapshot['__file_sobjects__'][0]
    relative_dir = file_sobject['relative_dir']
    file_name = file_sobject['file_name']

    # make proper file path, and dir path to set workspace
    new_file = '{0}/{1}/{2}'.format(asset_dir, relative_dir, file_name)
    split_path = relative_dir.split('/')
    dir_path = '{0}/{1}'.format(asset_dir, '{0}/{1}/{2}'.format(*split_path))
    set_workspace(dir_path, all_process)

    # check in playblast
    tc.checkin_playblast(snapshot['code'], temp_playblast)

    # set proper scene name
    cmds.file(rename=new_file)

    # print(new_file)
    # tc.create_snapshot()
    # tc.checkin_file()


def create_workspace(dir_path, all_process):
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
    # TODO https://groups.google.com/forum/?utm_medium=email&utm_source=footer#!msg/python_inside_maya/GYWCJFcf1mo/P1dgGBFHkY0J
    # http://forums.cgsociety.org/archive/index.php?t-968015.html
    # cmds.workspace(q=True, dir=True)
    create_workspace(dir_path, all_process)
    print('Setting Workspace: {0}'.format(dir_path))
    mel.eval('setProject "{0}";'.format(dir_path))
    cmds.workspace(u=True)
    # cmds.workspace(dir=dir_path)
    # cmds.workspace(q=True, dir=True)


def make_playblast():
    pass


def scene_info():
    if not cmds.attributeQuery('scene_info', n='particleCloud1', exists=True):
        cmds.addAttr('particleCloud1', longName='scene_info', dataType='string')
    cmds.setAttr('particleCloud1.scene_info', 'MAZAZasdasdA', type='string')
