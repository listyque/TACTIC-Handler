import os
from pathlib import Path

import maya.cmds as cmds

from tactic_handler_api import get_api
from tactic_handler_dcc import maya as handler_maya


api = get_api()
work_path = Path(cmds.workspace(rootDirectory=True, query=True)).as_posix()


def get_category_and_sub(file_path, sobject_category=''):
    category = ''
    sub_category = ''

    possible_categories = 'locations|objects|characters|objects/environment|objects/equipment|objects/vehicles'.split('|')
    file_name = Path(file_path).name

    trim_line = file_path.find('sourceimages/')
    if trim_line != -1:
        file_path = file_path[trim_line+13:]

    only_categories_string = file_path.replace('/'+file_name, '')

    for cat in possible_categories:
        if only_categories_string.find(cat) != -1:
            category = cat
  
    if category not in possible_categories:
        return sobject_category, sub_category
  
    sub_category = only_categories_string.replace(category, '').replace('/', '')
    if sub_category == category:
        sub_category = ''
    
    return category, sub_category


def get_texture_type(file_path):
    possible_types = 'mask|diffuse|specular|reflection|roughness|glossiness|bump|displace|normals|incandencence'.split('|')
    for tex_type in possible_types:
        if file_path.find(tex_type) != -1:
            return tex_type

    return ''


def check_attached_textures(search_key=None):
    '''
    Checking for already attached texture instances to current opened scene/sObject
    '''
    
    if not search_key:
        search_key = handler_maya.get_skey_from_scene()
    
    if search_key:
    
        cmds.progressWindow(title='Checking-in Textures', progress=0, status='Checking attached Textures: 0%', isInterruptable=True)

        parent_sobject = api.sobject(search_key)
        sobjects = parent_sobject.related(search_type='dolly3d/texture')
        return sobjects, parent_sobject
    else:
        cmds.confirmDialog(title='Scene is not opened!', message='Your scene hasn\'t been saved with TacticHandler, or not opened with it.Please open scene saved with TacticHandler!' , button=['Ok'], defaultButton='Ok')
        return None, None


def get_texture_files_list(check_existence=True, abs_paths=False, return_file_nodes=False, cleanup_unused=False):

    # get list of all textures in current maya scene
    
    file_nodes = cmds.ls(type='file')
    redshift_normal_map_nodes = cmds.ls(type='RedshiftNormalMap')
    redshift_sprite_nodes = cmds.ls(type='RedshiftSprite')
    redshift_environment_nodes = cmds.ls(type='RedshiftEnvironment')
    
    redshift_nodes = (
        redshift_normal_map_nodes
        + redshift_sprite_nodes
        + redshift_environment_nodes
    )

    # default maya file routine
    file_nodes_list = []
    for file_node in file_nodes:
        connections = cmds.listConnections(file_node, source=False) or []
        if len(connections) > 1:
            file_nodes_list.append(file_node)
        elif cleanup_unused:
            cmds.delete(file_node)
    
    # redshift nodes routine
    redshift_nodes_list = []
    for redshift_node in redshift_nodes:
        connections = cmds.listConnections(redshift_node, source=False) or []
        if len(connections) > 1:
            redshift_nodes_list.append(redshift_node)
        elif cleanup_unused:
            cmds.delete(redshift_node)

    if return_file_nodes:
        return file_nodes_list + redshift_nodes_list
    
    files_set = set()
    
    # default maya file routine
    for file_node in file_nodes_list:

        file_path = cmds.getAttr('{}.fileTextureName'.format(file_node))
        if file_path and (not check_existence or os.path.exists(file_path)):
            files_set.add(file_path)

    # redshift nodes routine
    for redshift_node in redshift_nodes_list:
        file_path = cmds.getAttr('{}.tex0'.format(redshift_node))
        if file_path and (not check_existence or os.path.exists(file_path)):
            files_set.add(file_path)

    files_list = []
    files_list_abs = []

    for fl in sorted(files_set):
        relative_path = Path(fl).as_posix().replace(work_path, '')
        files_list.append(relative_path)
        files_list_abs.append(Path(fl).as_posix())
    
    if abs_paths:
        return files_list_abs
    else:
        return files_list


def check_and_create_textures(attached_textures_list, parent_sobject):
    '''
    check for already existent texture sobjects in this category
    create if this doesn't exitsts
    attach if exists and not attached
    '''
        
    files_lst = get_texture_files_list()
    
    for i, fl in enumerate(files_lst):
        progress = int(i * 100 / len(files_lst))

        cmds.progressWindow(edit=True, progress=progress, status=('Creating Textures SObjects: {}%'.format(progress)))

        if cmds.progressWindow(query=True, isCancelled=True):
            break

        tex_category, tex_sub_category = get_category_and_sub(fl, parent_sobject.get_value('assets_category_code'))
    
        only_file_name = Path(fl).stem
    
        filters = [('name', only_file_name)]
        if tex_category:
            filters.append(('assets_category_code', tex_category))
        if tex_sub_category:
            filters.append(('sub_type', tex_sub_category))
        
        attached_already = False
        
        # check if texture is attached (for performance reasons)
        for attached in attached_textures_list:
            a_filters = [('name', attached.get_value('name'))]
            if attached.get_value('assets_category_code'):
                a_filters.append(('assets_category_code', attached.get_value('assets_category_code')))
            if attached.get_value('sub_type'):
                a_filters.append(('sub_type', attached.get_value('sub_type')))
        
            if filters == a_filters:
                attached_already = True
        
        if not attached_already:
            texture_type = parent_sobject.get_project().stype('dolly3d/texture')
            assets = texture_type.query(filters=filters, limit=1).items
            
            data = {
                'keywords': '',
                'name': only_file_name,
                'assets_category_code': tex_category,
                'description': '',
                'texture_type': get_texture_type(fl),
                'sub_type': tex_sub_category,
                }
        
            if not assets:
                texture_type.new(
                    data,
                    parent=parent_sobject,
                    relation='dolly3d/texture_in_assets',
                ).commit()
            else:
                parent_sobject.link(
                    assets[0], relation='dolly3d/texture_in_assets'
                )


def check_for_textures_is_checked_in(textures_sobjects_list, parent_sobject):
    """
    The process of check-in texture files to server
    If files already exists it will skip
    If files have been updated then it will check-in new version
    """

    textures_in_scene_list = get_texture_files_list(abs_paths=False)
    textures_in_scene_abs_list = get_texture_files_list(abs_paths=True)
 
    textures_sobjects_tuple = []
    
    # matching texture to sobject
    for fl, fl_abs in zip(textures_in_scene_list, textures_in_scene_abs_list):

        tex_category, tex_sub_category = get_category_and_sub(fl, parent_sobject.get_value('assets_category_code'))
    
        only_file_name = Path(fl).stem
    
        filters = [('name', only_file_name)]
        if tex_category:
            filters.append(('assets_category_code', tex_category))
        if tex_sub_category:
            filters.append(('sub_type', tex_sub_category))
        
        # check if texture is attached (for performance reasons)
        for attached in textures_sobjects_list:

            a_filters = [('name', attached.get_value('name'))]
            if attached.get_value('assets_category_code'):
                a_filters.append(('assets_category_code', attached.get_value('assets_category_code')))
            if attached.get_value('sub_type'):
                a_filters.append(('sub_type', attached.get_value('sub_type')))
        
            if filters == a_filters:
                textures_sobjects_tuple.append((attached, fl_abs))
    
    commit_queue_ui = None
    # getting relative paths from sobjects
    for sobject, texture_path in textures_sobjects_tuple:
        formed_texture_path = Path(texture_path).as_posix()
        if check_texture_is_up_to_date(sobject, formed_texture_path):
            print(sobject, formed_texture_path)
            print(u'Texture {} is up to date'.format(sobject.get_value('name') or sobject.get_code()))
        else:
            print(u'Making server checkin for texture {}'.format(sobject.get_value('name') or sobject.get_code()))
            print(formed_texture_path)
            commit_queue_ui = checkin_texture_file(sobject, formed_texture_path)
    
    return commit_queue_ui

def resolve_file_nodes(resolved_path, original_path):
    # UGLY BUT TIME IS MONEY
    # Should you attribute query and check them all

    file_nodes_list = get_texture_files_list(return_file_nodes=True)
    for file_node in file_nodes_list:
        if cmds.attributeQuery('fileTextureName', node=file_node, exists=True):
            file_path = cmds.getAttr('{}.fileTextureName'.format(file_node))
            if file_path == original_path:
                cmds.setAttr('{}.fileTextureName'.format(file_node), resolved_path, type='string')
        elif cmds.attributeQuery('tex0', node=file_node, exists=True):
            file_path = cmds.getAttr('{}.tex0'.format(file_node))
            if file_path == original_path:
                cmds.setAttr('{}.tex0'.format(file_node), resolved_path, type='string')



def check_texture_is_up_to_date(sobject, texture_path):
    versionless_snapshots = [
        snapshot for snapshot in sobject.snapshots(process='publish')
        if snapshot.is_versionless()
        and snapshot.get_info().get('context') == 'publish'
    ]
    if not versionless_snapshots:
        return False

    files = versionless_snapshots[0].get_files_objects()
    texture_file_object = next(
        (file for file in files if file.get_type() == 'image'), None
    ) or next((file for file in files if file.get_type() == 'main'), None)
    if texture_file_object is None:
        return False

    if texture_file_object.is_exists():
        print(os.path.getsize(texture_path), texture_file_object.get_file_size(), texture_file_object)

        if os.path.getsize(texture_path) == texture_file_object.get_file_size():
        
            resolved_path = Path(texture_file_object.get_full_abs_path()).as_posix()
            
            # Making path relative
            resolved_path = resolved_path.replace(work_path, '')
            resolve_file_nodes(resolved_path, texture_path)
        
            return True
    return False


def checkin_texture_file(sobject, texture_path):
    print('Making checking files')
    return api.ui.checkin_files(
        sobject.get_search_key(),
        'publish',
        '',
        [texture_path],
    ).wait()

def begin_process_textures(search_key=None):

    commit_queue_ui = None
    textures_sobjects_list, parent_sobject = check_attached_textures(search_key)
    if parent_sobject:
        check_and_create_textures(textures_sobjects_list, parent_sobject)
        # after adding unattached textures check for them again
        textures_sobjects_list, parent_sobject = check_attached_textures(search_key)
        # then we must check for textures files is checked in
        commit_queue_ui = check_for_textures_is_checked_in(
            textures_sobjects_list, parent_sobject
        )

    cmds.progressWindow(endProgress=1)
    return commit_queue_ui
