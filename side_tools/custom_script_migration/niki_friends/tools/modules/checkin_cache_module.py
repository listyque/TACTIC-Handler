import os
import shutil
import zipfile
import fnmatch
import re
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import maya.cmds as cmds
import maya.mel as mel
from tactic_handler_api import get_api
from tactic_handler_dcc import maya as handler_maya

CURRENT_PROJECT = "niki_friends"
api = get_api()


CACHE_PATH = u'{0}/cache/nCache'.format(CURRENT_PROJECT)
ALEMBIC_CACHE_PATH = u'cache/alembic'
WORK_PATH = cmds.workspace(rootDirectory=True, query=True)
WORK_PATH = Path(WORK_PATH).as_posix()


def _title(sobject):
    return sobject.get_value("name") or sobject.get_code()


def _scene_context():
    search_key = handler_maya.get_skey_from_scene() or ""
    return parse_qs(urlsplit(search_key).query).get("context", [""])[0]


def check_path_validity(path):
    
    if os.path.exists(path):
        return path


def onerror(func, path, exc_info):
    '''
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    '''
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    # else:
        # raise


def checkin_current_scene(sobject):
    runtime = handler_maya.runtime()
    if runtime is None or not runtime.connected:
        raise RuntimeError("TACTIC Handler is not connected to Maya")
    return api.ui.checkin_from_maya(
        sobject.get_search_key(),
        _scene_context(),
        "Added Cache",
        runtime.client_id,
    ).wait()


def get_current_scene_sobject(search_key=None):
    search_key = search_key or handler_maya.get_skey_from_scene()
    if search_key:
        return api.sobject(search_key)
    cmds.confirmDialog(
        title="Scene is not opened!",
        message=(
            "Your scene hasn't been saved with TacticHandler, or not opened "
            "with it. Please open a scene saved with TacticHandler!"
        ),
        button=["Ok"],
        defaultButton="Ok",
    )
    return None


def check_attached_abc(search_key=None):
    '''
    Checking for already attached cache instances to current opened scene/sObject
    '''
    
    search_key = search_key or handler_maya.get_skey_from_scene()
    if search_key:
        cmds.progressWindow(title='Checking Assets', progress=0, status='Checking attached Assets: 0%', isInterruptable=True)
        parent = api.sobject(search_key)
        if parent.get_stype().get_code() != 'dolly3d/assets':
            parent = api.project(CURRENT_PROJECT).stype('complex/scenes').get(
                code=parent.get_value('scenes_code')
            )
        return parent.related(search_type='dolly3d/assets'), parent
    cmds.confirmDialog(
        title="Scene is not opened!",
        message=(
            "Your scene hasn't been saved with TacticHandler, or not opened "
            "with it. Please open a scene saved with TacticHandler!"
        ),
        button=["Ok"],
        defaultButton="Ok",
    )
    return None, None



def check_and_create_abc(attached_abc_list, alembic_files_list, parent_sobject):
    '''
    check for already existent abc sobjects in database
    create if this doesn't exitsts
    attach if exists and not attached
    '''
    
    abc_assets = []
    
    for i, fl in enumerate(alembic_files_list):

        attached_already = False
        progress = int(i * 100 / len(alembic_files_list))

        cmds.progressWindow(edit=True, progress=progress, status=('Creating Cache SObjects: {}%'.format(progress)))

        if cmds.progressWindow(query=True, isCancelled=True):
            break

        only_file_name = Path(fl).stem

 
        for attached in attached_abc_list:
        
            if only_file_name == attached.get_value('name'):
                abc_assets.append(attached)
                attached_already = True

        if not attached_already:
            filters = [('name', only_file_name)]
            asset_type = api.project(CURRENT_PROJECT).stype('dolly3d/assets')
            found = asset_type.query(filters=filters, limit=1).items
            asset = found[0] if found else None
            
            data = {
                'keywords': '',
                'name': only_file_name,
                'assets_category_code': 'cache/abc',
                'description': '',
                'pipeline_code': 'niki_friends/assets',                
                }
            
            if parent_sobject.get_stype().get_code() == 'dolly3d/assets':
                instance_type = 'dolly3d/assets_in_assets'
            else:
                instance_type = 'dolly3d/assets_in_scenes'
            
            
            if not asset:
                asset = asset_type.new(data).commit()
                parent_sobject.link(
                    asset,
                    relation=instance_type,
                    path=(
                        'parent'
                        if parent_sobject.get_stype().get_code()
                        == 'dolly3d/assets'
                        else None
                    ),
                )
                abc_assets.append(asset)
            else:
                abc_assets.append(asset)
                parent_sobject.link(
                    asset,
                    relation=instance_type,
                    path=(
                        'parent'
                        if parent_sobject.get_stype().get_code()
                        == 'dolly3d/assets'
                        else None
                    ),
                )
                    
    
    return abc_assets


def checkin_cache_file(sobject, cache_path, process='cache'):
    print('Making checking files')
    return api.ui.checkin_files(
        sobject.get_search_key(), process, '', [cache_path]
    ).wait()


def handle_abc(alembic_nodes):
    
    alembic_files = get_abc_files_list(alembic_nodes)
    alembic_files_paths = get_abc_files_list(alembic_nodes, abs_paths=True)
    
    attached_abc_list, parent_scene_sobject = check_attached_abc()
    
    check_and_create_abc(attached_abc_list, alembic_files_paths, parent_scene_sobject)
    
    

def get_abc_files_list(alembic_nodes, abs_paths=False):
    files_set = set()
    

    for alembic_node in alembic_nodes:

        file_path = cmds.getAttr('{}.abc_File'.format(alembic_node))
        files_set.add(file_path)
    
    files_list = []
    files_list_abs = []

    for fl in sorted(files_set):
        relative_path = Path(fl).stem
        
        # only adding path if abc file exists
        out_path = check_path_validity(Path(fl).as_posix())
        if out_path:
            files_list_abs.append(out_path)
            files_list.append(relative_path)
    
    if abs_paths:
        return files_list_abs
    else:
        return files_list


def create_cache_from_scene():
    cmds.progressWindow(title='Creating cache', progress=0, status='Generating cache: 0%', isInterruptable=True)
    
    cmds.select( clear=True )

    nucleus_nodes = cmds.ls(type='nucleus')
    hair_system_nodes = cmds.ls(type='hairSystem')
    ncloth_nodes = cmds.ls(type='nCloth')
    cache_nodes = cmds.ls(type='cacheFile')
    nparticle_nodes = cmds.ls(type='nParticle')
    alembic_nodes = cmds.ls(type='AlembicNode')
    
    print(nucleus_nodes)
    print(nparticle_nodes)
    print(alembic_nodes)
    nothing_to_cache = True
    
    if hair_system_nodes:
        nothing_to_cache = False
        
        all_nodes = []
        all_nodes.extend(nucleus_nodes)
        all_nodes.extend(hair_system_nodes)
        all_nodes.extend(ncloth_nodes)
        all_nodes.extend(nparticle_nodes)
        
        # enabling all nucleus nodes and select them
        for nucleous_node in nucleus_nodes:
            try:
                cmds.setAttr('{}.enable'.format(nucleous_node), 1)
            except:
                print('Locked node {}. Skipping.'.format(nucleous_node))

        for ncloth_node in ncloth_nodes:
            try:
                cmds.setAttr('{}.isDynamic'.format(ncloth_node), 1)
            except:
                print('Locked node {}. Skipping.'.format(ncloth_node))

        # generaing cache
        for i, node in enumerate(all_nodes):
            print(node)
            progress = int(i * 100 / len(all_nodes))

            cmds.progressWindow(edit=True, progress=progress, status=('Generating cache {1}: {0}%'.format(progress, node)))

            if cmds.progressWindow(query=True, isCancelled=True):
                break

            cmds.select(node, replace=True)
            #mel.eval('nClothCacheOpt;')
            try:
                mel.eval('doCreateNclothCache 5 { "2", "1", "10", "OneFilePerFrame", "1", "","0","","0", "replace", "1", "1", "1","0","1","mcx" } ;')
            except:
                print('Not valid node selected {}. Skipping.'.format(node))
        
        # enabling all cache nodes
        for cache_node in cache_nodes:
            try:
                cmds.setAttr('{}.enable'.format(cache_node), 1)
            except:
                print('Locked node {}. Skipping.'.format(cache_node))
    
    if nparticle_nodes:
        nothing_to_cache = False
        
        all_nodes = []
        all_nodes.extend(nucleus_nodes)
        all_nodes.extend(nparticle_nodes)
        
        # enabling all nucleus nodes and select them
        for nucleous_node in nucleus_nodes:
            try:
                cmds.setAttr('{}.enable'.format(nucleous_node), 1)
            except:
                print('Locked node {}. Skipping.'.format(nucleous_node))

        for nparticle_node in nparticle_nodes:
            try:
                cmds.setAttr('{}.isDynamic'.format(nparticle_node), 1)
            except:
                print('Locked node {}. Skipping.'.format(nparticle_node))

        # generaing cache
        for i, node in enumerate(all_nodes):
            print(node)
            progress = int(i * 100 / len(all_nodes))

            cmds.progressWindow(edit=True, progress=progress, status=('Generating cache {1}: {0}%'.format(progress, node)))

            if cmds.progressWindow(query=True, isCancelled=True):
                break

            cmds.select(node, replace=True)
            #mel.eval('nClothCacheOpt;')
            #try:
            #    #mel.eval('deleteCacheFile 2 { "delete", "" } ;')
            #    mel.eval('doCreateNclothCache 5 { "2", "1", "10", "OneFilePerFrame", "1", "","0","","0", "replace", "0", "1", "1","0","1","mcx" } ;')
            #except:
            #    print('Not valid node selected {}. Skipping.'.format(node))
        
        # enabling all cache nodes
        for cache_node in cache_nodes:
            try:
                cmds.setAttr('{}.enable'.format(cache_node), 1)
            except:
                print('Locked node {}. Skipping.'.format(cache_node))
    
    if alembic_nodes:
        nothing_to_cache = False
        
        print('Cache alembic')
        
        handle_abc(alembic_nodes)

    if nothing_to_cache:
        cmds.confirmDialog(title='No Cachable Objects!', message='Your scene does not have any Cachable Objects!' , button=['Ok'], defaultButton='Ok')
    
    cmds.progressWindow(endProgress=1)


def rename_cache_path(sobject, parent_sobject, cache_path):

    if cache_path.endswith('/'):
        cache_path = cache_path[:-1]
        if cache_path.endswith('/{}'.format(_title(sobject))):
            return cache_path

    split_path = cache_path.split('/')
    trim_path = u'/'.join(split_path[:-1])
    last_part = split_path[-1]
    
    
    print('cache_path', cache_path)
    print('trim_path', trim_path)
    print('last_part', last_part)
    
    new_cache_path = u'{0}/{1}/'.format(trim_path, _title(parent_sobject))
    new_cache_sub_path = u'{0}/{1}/{2}/'.format(trim_path, _title(parent_sobject), last_part)
    new_cache_final_path = u'{0}/{1}/{2}/'.format(trim_path, _title(parent_sobject), _title(sobject))
    
    print('new_cache_path', new_cache_path)
    print('new_cache_sub_path', new_cache_sub_path)
    print('new_cache_final_path', new_cache_final_path)

    if not os.path.exists(new_cache_path):
        os.makedirs(new_cache_path)
    if cache_path != new_cache_path:
        shutil.move(cache_path, new_cache_path)
    
    if os.path.exists(new_cache_final_path):
        shutil.rmtree(new_cache_final_path, ignore_errors=True, onerror=onerror)

    os.renames(new_cache_sub_path, new_cache_final_path)

    cache_nodes = cmds.ls(type='cacheFile')

    if cache_nodes:
        for cache_node in cache_nodes:
            cmds.setAttr(u'{0}.cachePath'.format(cache_node), new_cache_final_path, type='string')

        return new_cache_final_path


def rename_abc_cache_path(parent_sobject, cache_path, alembic_node=None):
    
    abc_file_is_the_same = False
    
    split_path = cache_path.split('/')
    trim_path = u'/'.join(split_path[:-1])
    last_part = split_path[-1]
    
    abc_cache_dir = u'{0}{1}'.format(WORK_PATH, ALEMBIC_CACHE_PATH)
    
    #new_cache_path = u'{0}/{1}_caches/'.format(abc_cache_dir, parent_sobject.get_value('name'))
    new_cache_path = u'{0}/'.format(abc_cache_dir)
    abs_cache_path_to_file = u'{0}{1}'.format(new_cache_path, last_part)


    if not os.path.exists(new_cache_path):
        os.makedirs(new_cache_path)
    
    if cache_path != abs_cache_path_to_file:
        shutil.copy(cache_path, abs_cache_path_to_file)
    else:
        abc_file_is_the_same = True
    
    if alembic_node:
        cmds.setAttr(u'{0}.abc_File'.format(alembic_node), abs_cache_path_to_file, type='string')

    return new_cache_path, abc_file_is_the_same


def get_cache_folder():

    file_nodes = cmds.ls(type='cacheFile')

    cache_path = None
    
    if file_nodes:
        cache_path = cmds.getAttr(u'{0}.cachePath'.format(file_nodes[0]))
    
    #if not cache_path:
    #    cmds.confirmDialog(title='Cache not found!', message='Your scene does not have any Cache Nodes!' , button=['Ok'], defaultButton='Ok')
    
    return cache_path

    

def create_files_list(walk_path):
    ignore_list = [
        'cache_file.zip',
    ]
    include_list = [
        '*.xml',
        '*.mcx',
    ]

    include_list = r'|'.join([fnmatch.translate(x) for x in include_list])
    ignore_list = '|'.join(ignore_list)

    files_list = []
    for root, dirs, files in os.walk(walk_path):
        if not re.search(ignore_list, root):
            files = [os.path.join(root, f) for f in files]
            files = [f for f in files if not re.search(ignore_list, f)]
            files = [f for f in files if re.search(include_list, f)]

            for fl in files:
                files_list.append(fl)

    return files_list


def create_cache_archive(archive_path, abs_path):
    zp = zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED)
    files_list = create_files_list(abs_path)

    for i, fl in enumerate(files_list):
        progress = int(i * 100 / len(files_list))

        cmds.progressWindow(edit=True, progress=progress, status=('Creating Cache Archive: {}%'.format(progress)))

        if cmds.progressWindow(query=True, isCancelled=True):
            break

        fl_rep = fl.replace
        zp.write(fl, arcname=fl_rep(abs_path, ''))
    zp.close()

def create_abc_cache_archive(archive_path, abs_path):
    zp = zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED)
    zp.write(abs_path, arcname=os.path.basename(abs_path))
    zp.close()


def get_sobject_and_parent_sobject():
    sobject = get_current_scene_sobject()
    if not sobject:
        return None, None
    if sobject.get_stype().get_code() == 'complex/shot':
        parent = api.project(CURRENT_PROJECT).stype('complex/scenes').get(
            code=sobject.get_value('scenes_code')
        )
        return sobject, parent
    if sobject.get_stype().get_code() == 'dolly3d/assets':
        return sobject, sobject
    return None, None
        

def prepare_all_caches():
    
    # nCache preparing routine
    
    def extract_cache(cache_snapshot, shot_sobject, episode_sobject):
        episode_title = _title(episode_sobject)
        shot_title = _title(shot_sobject)
        
        destination_path = u'{0}/{1}/{2}/{3}'.format(
            cache_snapshot.get_repo_path(),
            CACHE_PATH,
            episode_title,
            shot_title
        )

        print(destination_path, 1)
        print(cache_snapshot.get_full_abs_path(), 2)
        print(Path(destination_path).as_posix(), 3)

    
    
    sobject, parent_sobject = get_sobject_and_parent_sobject()    

    if parent_sobject.get_stype().get_code() == 'complex/scenes':
        shots_sobjects = parent_sobject.related(search_type='complex/shot')
        
        for shot_sobject in shots_sobjects:
            snapshot = next((
                snapshot
                for snapshot in shot_sobject.snapshots(process='cache')
                if snapshot.is_versionless()
            ), None)
            if not snapshot:
                continue
            for snapshot_file in snapshot.get_files_objects():
                if snapshot_file.get_type() == 'main':
                    print(snapshot_file)
                    if snapshot_file.get_ext() == 'zip':
                        extract_cache(snapshot_file, shot_sobject, parent_sobject)
                    else:
                        print('This is not a ZIP File! Skipping')
    
        cache_nodes = cmds.ls(type='cacheFile')
    
        if cache_nodes:
            episode_title = _title(parent_sobject)
            shot_title = _title(sobject)
            new_cache_final_path = u'cache/nCache/{0}/{1}'.format(
                episode_title,
                shot_title
            )
            for cache_node in cache_nodes:
                print(new_cache_final_path)
                cmds.setAttr(u'{0}.cachePath'.format(cache_node), new_cache_final_path, type='string')
    
    
    # Alembic caches preparing routine
    
    print('Getting all cache assets, extract them to proper folder')
    
    
    def extract_abc_cache(cache_snapshot, asset_sobject, episode_sobject):
        abc_cache_dir = u'{0}{1}'.format(WORK_PATH, ALEMBIC_CACHE_PATH)
        #new_cache_path = u'{0}/{1}_caches/'.format(abc_cache_dir, episode_title)
        new_cache_path = u'{0}/'.format(abc_cache_dir)

        print(new_cache_path, 1)
        print(cache_snapshot.get_full_abs_path(), 2)
        print(Path(new_cache_path).as_posix(), 3)

        with zipfile.ZipFile(cache_snapshot.get_full_abs_path()) as archive:
            archive.extractall(Path(new_cache_path).as_posix())


    sobject, parent_sobject = get_sobject_and_parent_sobject()
    
    filters = [('assets_category_code', 'cache/abc')]
    
    all_caches_assets_sobjects = {}
    
    # getting all cache assets for each asset added to the episode
    all_assets_sobjects = parent_sobject.related(
        search_type='dolly3d/assets'
    )
    for asset_sobject in all_assets_sobjects:
        asset_caches = asset_sobject.related(
            search_type='dolly3d/assets', filters=filters
        )
        all_caches_assets_sobjects.update(
            (cache.get_search_key(), cache) for cache in asset_caches
        )


    # getting only cache assets directly connected to episode
    assets_sobjects = parent_sobject.related(
        search_type='dolly3d/assets', filters=filters
    )
    all_caches_assets_sobjects.update(
        (cache.get_search_key(), cache) for cache in assets_sobjects
    )
    

    for asset_sobject in all_caches_assets_sobjects.values():
        snapshot = next((
            snapshot
            for snapshot in asset_sobject.snapshots(process='publish')
            if snapshot.is_versionless()
        ), None)
        if not snapshot:
            continue
        for snapshot_file in snapshot.get_files_objects():
            if snapshot_file.get_type() == 'main':
                print(snapshot_file)
                if snapshot_file.get_ext() == 'zip':
                    print('All set, getting things ready')
                    extract_abc_cache(
                        snapshot_file, asset_sobject, parent_sobject
                    )
                else:
                    print('This is not a ZIP File! Skipping')
    

def append_checkin_current_scene():
    sobject = get_current_scene_sobject()
    if sobject:
        print(u'Making server checkin for current scene {}'.format(
            _title(sobject)
        ))
        return checkin_current_scene(sobject)
    return None


def begin_process_caches(search_key=None):
    cmds.progressWindow(title='Preparing Cache to checkin', progress=0, status='Preparing Cache Archive: 0%', isInterruptable=True)
    
    caches_found = False
    
    cache_path = get_cache_folder()
    if cache_path:

        caches_found = True

        sobject = get_current_scene_sobject()

        if sobject:
            if sobject.get_stype().get_code() == 'dolly3d/assets':
                parent_sobject = sobject
            else:
                parent_sobject = api.project(CURRENT_PROJECT).stype(
                    'complex/scenes'
                ).get(code=sobject.get_value('scenes_code'))

            new_cache_path = rename_cache_path(sobject, parent_sobject, cache_path)

            archive_path = u'{0}/cache_file_{1}.zip'.format(
                new_cache_path, _title(sobject)
            )
            create_cache_archive(archive_path, new_cache_path)

            print(u'Making server checkin for cache {}'.format(_title(sobject)))
            checkin_cache_file(sobject, archive_path)


    alembic_nodes = cmds.ls(type='AlembicNode')
    
    alembic_files = get_abc_files_list(alembic_nodes)
    print('alembic_files', alembic_files)
    
        
    abc_cache_paths = get_abc_files_list(alembic_nodes, abs_paths=True)

    print('abc_cache_paths1', abc_cache_paths)

    if abc_cache_paths:

        caches_found = True
        
        attached_abc_list, parent_scene_sobject = check_attached_abc()

        abc_assets = check_and_create_abc(attached_abc_list, abc_cache_paths, parent_scene_sobject)
        
        sobject = get_current_scene_sobject()
        
        if sobject:
            for abc_cache_path, alembic_file, alembic_nodes in zip(abc_cache_paths, alembic_files, alembic_nodes):
                
                for i, abc_asset in enumerate(abc_assets):
                    print(abc_asset)
                    print(abc_asset.get_value('name'), alembic_file)

                    if abc_asset.get_value('name') == alembic_file:
                        
                        new_cache_path, abc_file_is_the_same = rename_abc_cache_path(parent_scene_sobject, abc_cache_path, alembic_nodes)
                       
                        if not abc_file_is_the_same:
                            archive_path = u'{0}{1}.zip'.format(new_cache_path, alembic_file)
                            abs_abc_path = u'{0}{1}.abc'.format(new_cache_path, alembic_file)
                            cmds.progressWindow(edit=True, progress=i, status=('Creating Cache Archive: {0}'.format(abc_asset)))
                            create_abc_cache_archive(archive_path, abs_abc_path)
                
                            print(u'Making server checkin for cache {}'.format(
                                _title(sobject)
                            ))

                            checkin_cache_file(abc_asset, archive_path, process='publish')
                        else:
                            caches_found = False
                            print(u'The file You are trying to update hasn''t been changed. Skip', alembic_file)

    if caches_found:
        print(u'Making server checkin for current scene {}'.format(
            _title(sobject)
        ))
        checkin_current_scene(sobject)

    cmds.progressWindow(endProgress=1)
