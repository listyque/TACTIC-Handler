# file maya_functions.py
# Maya Functions Module

import os
from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtCore

import maya.OpenMayaUI as omui
import maya
import maya.cmds as cmds
import maya.mel as mel
try:
    import shiboken as shiboken
except:
    import shiboken2 as shiboken

import tactic_classes as tc
from thlib.environment import env_inst, dl
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


def open_scene(file_object):
    # check if scene need saving
    file_path = file_object.get_full_abs_path()
    new_scene = mel.eval('saveChanges("file -f -new")')
    if bool(new_scene):
        dl.log('Opening: ' + file_path, group_id='maya_log')
        # set_workspace(dir_path, all_process)
        cmds.file(file_path, open=True, force=True, ignoreVersion=True)


def import_scene(file_object):
    file_path = file_object.get_full_abs_path()
    dl.log('Importing: ' + file_path, group_id='maya_log')
    namespace = gf.extract_filename(file_path, no_ext=True)
    cmds.file(file_path, namespace=namespace.replace('.', '_'), i=True, ignoreVersion=True)


def reference_scene(file_object):
    file_path = file_object.get_full_abs_path()
    dl.log('Referencing: ' + file_path, group_id='maya_log')
    namespace = gf.extract_filename(file_path, no_ext=True)
    cmds.file(file_path, namespace=namespace.replace('.', '_'), reference=True, ignoreVersion=True)


def get_current_scene_format():
    scene_format = cmds.file(query=True, type=True)

    if scene_format:
        return scene_format[0]
    else:
        return 'mayaBinary'


def get_skey_from_scene():
    if cmds.attributeQuery('tacticHandler_skey', node='defaultObjectSet', exists=True):
        skey = cmds.getAttr('defaultObjectSet.tacticHandler_skey')
        return skey


def wrap_export_selected_options(project_code, tab_code, wdg_code):
    mel.eval('proc export_selection_maya(){python("' +
             "main.mf.export_selected('{0}', '{1}', '{2}')".format(project_code, tab_code, wdg_code) +
             '");}fileOptions "ExportActive" "export_selection_maya";')


def export_selected(project_code, tab_code, wdg_code):

    current_type = cmds.optionVar(q='defaultFileExportActiveType')
    current_ext = cmds.translator(str(current_type), q=True, filter=True)
    current_ext = current_ext.split(';')[0]

    current_checkin_widget = env_inst.get_check_tree(project_code, tab_code, wdg_code)

    current_checkin_widget.save_file(selected_objects=[True, {current_type: current_ext[2:]}], maya_checkin=True)


def wrap_save_options(project_code, tab_code, wdg_code):
    mel.eval('proc save_as_maya(){python("' +
             "main.mf.save_as('{0}', '{1}', '{2}')".format(project_code, tab_code, wdg_code) +
             '");}fileOptions "SaveAs" "save_as_maya";')


def save_as(project_code, tab_code, wdg_code):

    current_type = cmds.optionVar(q='defaultFileSaveType')
    current_ext = cmds.translator(str(current_type), q=True, filter=True)
    current_ext = current_ext.split(';')[0]

    current_checkin_widget = env_inst.get_check_tree(project_code, tab_code, wdg_code)

    current_checkin_widget.save_file(selected_objects=[False, {current_type: current_ext[2:]}], maya_checkin=True)


def set_info_to_scene(search_key, context):
    # add info about particular scene
    skey_link = 'skey://{0}&context={1}'.format(search_key, context)
    if not cmds.attributeQuery('tacticHandler_skey', node='defaultObjectSet', exists=True):
        cmds.addAttr('defaultObjectSet', longName='tacticHandler_skey', dataType='string')
    cmds.setAttr('defaultObjectSet.tacticHandler_skey', skey_link, type='string')


def get_maya_info_dict():
    import maya.cmds as cmds

    info_dict = {
        'cs': cmds.about(cs=True),
        'uil': cmds.about(uil=True),
        'osv': cmds.about(osv=True),
        'os': cmds.about(os=True),
        'env': cmds.about(env=True),
        'a': cmds.about(a=True),
        'b': cmds.about(b=True),
        'p': cmds.about(p=True),
        'v': cmds.about(v=True),
    }
    return info_dict


def get_temp_playblast():
    current_frame = cmds.currentTime(query=True)
    playblast_image = cmds.playblast(
        forceOverwrite=True,
        format='image',
        completeFilename='tactic_handler_temp_playblast.jpg',
        showOrnaments=False,
        widthHeight=[960, 540],
        sequenceTime=False,
        frame=[current_frame],
        compression='jpg',
        offScreen=False,
        viewer=False,
        percent=100
    )

    return playblast_image


def inplace_checkin(virtual_snapshot, repo_name, update_versionless, only_versionless=False, generate_icons=True,
                    selected_objects=False, ext_type='mayaAscii', setting_workspace=False):

    main_version = 'versioned'
    if only_versionless:
        main_version = 'versionless'

    scene_name = virtual_snapshot[0][1][main_version]['names'][0]
    scene_path = gf.form_path(repo_name['value'][0] + '/' + virtual_snapshot[0][1][main_version]['paths'][0])
    playblast_name = virtual_snapshot[1][1][main_version]['names'][0]
    playblast_path = gf.form_path(repo_name['value'][0] + '/' + virtual_snapshot[1][1][main_version]['paths'][0])

    full_scene_path = scene_path + '/' + ''.join(scene_name)
    full_playblast_path = playblast_path + '/' + ''.join(playblast_name)
    # create dest dirs
    if not os.path.exists(scene_path):
        os.makedirs(scene_path)
    if not os.path.exists(playblast_path):
        os.makedirs(playblast_path)
    # saving maya scene
    try:
        if ext_type in ['mayaAscii', 'mayaBinary']:
            cmds.file(rename=full_scene_path)
        renamed = True
    except:
        renamed = False
    try:
        if selected_objects:
            if ext_type in ['mayaAscii', 'mayaBinary']:
                cmds.file(exportSelected=selected_objects, type=ext_type, pr=True, eur=True)
            else:
                cmds.file(full_scene_path, exportSelected=selected_objects, type=ext_type, pr=True, eur=True)
        else:
            cmds.file(save=True, type=ext_type)
        saved = True
    except:
        saved = False

    # check_ok = True

    files_objects_list = []

    if renamed and saved:
        if setting_workspace:
            pass
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

        match_template = gf.MatchTemplate(['$FILENAME.$EXT'])

        files_objects_dict = match_template.get_files_objects([full_scene_path, full_playblast_path], sort=False)
        maya_app_info_dict = get_maya_info_dict()

        for fl in files_objects_dict.get('file'):
            fl.set_app_info(maya_app_info_dict)
            files_objects_list.append(fl)
        file_paths = [[full_scene_path], [full_playblast_path]]

        check_ok = tc.inplace_checkin(
            file_paths,
            virtual_snapshot,
            repo_name,
            update_versionless,
            only_versionless,
            generate_icons,
            files_objects_list,
        )
    else:
        check_ok = False

    maya.utils.processIdleEvents()

    return check_ok, files_objects_list


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

    for const, val in consts_list.items():
        if (const == 'scene') or (const == 'mayaAscii') or (const == 'mayaBinary'):
            for process in all_process:
                val += 'work/{0};'.format(process)
        workspace.append('workspace -fr "{0}" "{1}";\n'.format(const, val))

    with open(dir_path + "/workspace.mel", "w") as workspace_file:
        workspace_file.writelines(workspace)
    workspace_file.close()


def set_workspace(dir_path, all_process):
    create_workspace(dir_path, all_process)
    # print('Setting Workspace: {0}'.format(dir_path))
    mel.eval('setProject "{0}";'.format(dir_path))
    mel.eval('projectWindow;np_editCurrentProjectCallback;')


# def UpdateCustomMarkingMenu(menu=None, parent=None, remove=False, update=True):
#     if menu is None:
#         menu = 'CustomPopupMenu'
#
#     if not remove:
#         if parent is None:
#             parent = cmds.playblast(activeEditor=True)
#
#         if not cmds.popupMenu(menu, exists=True):
#             print('Create menu')
#             cmds.popupMenu(
#                 menu,
#                 markingMenu=True,
#                 parent=parent,
#                 button=2,
#                 ctl=True,
#                 postMenuCommand=UpdateCustomMarkingMenu,
#             )
#         else:
#             print('Update menu')
#             cmds.popupMenu(
#                 menu,
#                 edit=True,
#                 parent=parent,
#             )
#
#         if update:
#             cmds.popupMenu(
#                 menu,
#                 edit=True,
#                 deleteAllItems=True,
#             )
#
#             cmds.menuItem(parent=menu, radialPosition='SE')
#             cmds.menuItem(parent=menu, radialPosition='E')
#             cmds.menuItem(parent=menu, radialPosition='N')
#
#     else:
#         if cmds.popupMenu(menu, exists=True):
#             cmds.deleteUI(menu)

from functools import partial

MENU_NAME = "markingMenu"


class markingMenu():
    '''The main class, which encapsulates everything we need to build and rebuild our marking menu. All
    that is done in the constructor, so all we need to do in order to build/update our marking menu is
    to initialize this class.'''

    def __init__(self):

        self._removeOld()
        self._build()

    def _build(self):
        '''Creates the marking menu context and calls the _buildMarkingMenu() method to populate it with all items.'''
        menu = cmds.popupMenu(MENU_NAME, mm=1, aob=1, sh=0, p="viewPanes", pmo=1, pmc=self._buildMarkingMenu)

    def _removeOld(self):
        '''Checks if there is a marking menu with the given name and if so deletes it to prepare for creating a new one.
        We do this in order to be able to easily update our marking menus.'''
        if cmds.popupMenu(MENU_NAME, ex=1):
            cmds.deleteUI(MENU_NAME)

    def _buildMarkingMenu(self, menu, parent):
        '''This is where all the elements of the marking menu our built.'''

        # Radial positioned
        cmds.menuItem(p=menu, l="South West Button", rp="SW", c="print 'SouthWest'")
        cmds.menuItem(p=menu, l="South East Button", rp="SE", c=exampleFunction)
        cmds.menuItem(p=menu, l="North East Button", rp="NE", c="cmds.circle()")

        subMenu = cmds.menuItem(p=menu, l="North Sub Menu", rp="N", subMenu=1)
        cmds.menuItem(p=subMenu, l="North Sub Menu Item 1")
        cmds.menuItem(p=subMenu, l="North Sub Menu Item 2")

        cmds.menuItem(p=menu, l="South", rp="S", c="print 'South'")
        cmds.menuItem(p=menu, ob=1, c="print 'South with Options'")

        # List
        cmds.menuItem(p=menu, l="First menu item")
        cmds.menuItem(p=menu, l="Second menu item")
        cmds.menuItem(p=menu, l="Third menu item")
        cmds.menuItem(p=menu, l="Create poly cube", c="cmds.polyCube()")

        # Rebuild
        cmds.menuItem(p=menu, l="Rebuild Marking Menu", c=rebuildMarkingMenu)

# markingMenu()


def exampleFunction(*args):
    '''Example function to demonstrate how to pass functions to menuItems'''
    print "example function"


def rebuildMarkingMenu(*args):
    '''This function assumes that this file has been imported in the userSetup.py
    and all it does is reload the module and initialize the markingMenu class which
    rebuilds our marking menu'''
    cmds.evalDeferred("""
reload(markingMenu)
markingMenu.markingMenu()
""")


def shortcutActivated(shortcut):

    print(shortcut)
    # markingMenu()
    name = 'markingMenu'
    print('MARKING')

    popup = cmds.popupMenu(name, b=1, sh=1, alt=0, ctl=0, aob=1, p="viewPanes", mm=1)

    # if "scriptEditor" in cmds.getPanel(wf=1):
    #     cmds.scriptEditorInfo(clearHistory=1)
    # else:
    #     shortcut.setEnabled(0)
    #
    #     e = Qt4Gui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_H, QtCore.Qt.CTRL)
    #     QtCore.QCoreApplication.postEvent(get_maya_window(), e)
    #     cmds.evalDeferred(partial(shortcut.setEnabled, 1))


def initShortcut():
    shortcut = QtGui.QShortcut(Qt4Gui.QKeySequence(QtCore.Qt.CTRL + QtCore.Qt.Key_H), get_maya_window())
    shortcut.setContext(QtCore.Qt.ApplicationShortcut)
    shortcut.activated.connect(partial(shortcutActivated, shortcut))