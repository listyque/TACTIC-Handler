from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel
try:
    import PySide6.QtWidgets as QtWidgets
except ImportError:
    import PySide2.QtWidgets as QtWidgets

from tactic_handler_api import get_api
from tactic_handler_dcc import maya as handler_maya


PROJECT = "niki_friends"
api = get_api()


def _title(sobject):
    return sobject.get_value("name") or sobject.get_code()


def generate_batch():
    shot_sobject, scene_sobject = get_scene_and_parent_sobjects()
    if not shot_sobject:
        return

    print('Generating batch for {} Episode'.format(_title(scene_sobject)))

    related_shots = scene_sobject.related(
        search_type=shot_sobject.get_stype().get_code()
    )
    print(related_shots)

    # getting all versionless snapshots
    versionless_snapshots_list = []
    for sobj in related_shots:
        snapshot = next(
            snapshot
            for snapshot in sobj.snapshots(process="publish")
            if snapshot.is_versionless()
        )
        versionless_snapshots_list.append(snapshot)

    # getting all full abs paths list
    full_abs_paths_list = []
    for sn in versionless_snapshots_list:
        for s_fl in sn.get_files_objects():
            if s_fl.get_type() == 'main':
                full_abs_paths_list.append(s_fl.get_filename_with_ext())

    # getting abs path
    for snap in versionless_snapshots_list:
        if snap.get_info()['process'] == 'publish':
            for fl in snap.get_files_objects():
                if fl.get_type() == 'main':
                    file_path = fl.get_abs_path()
                    break

    # getting all descriptions and writing render.txt
    ranges_list = []
    with open('{}/render.txt'.format(file_path), 'w+') as render_file:
        for i, sobject in enumerate(related_shots):
            range_str = '{}-{}'.format(
                sobject.get_value('start_frame'),
                sobject.get_value('end_frame'),
            )
            ranges_list.append(range_str)
            render_file.write('Sh{0} {1}'.format(i + 1, ranges_list[i]))

    # writing batch file
    scene_num = file_path.split('Ep')[-1].replace('\\', '')

    first_part = '''@echo.
@echo AUTOMATICALLY GENERATED FOR EPISODE {0}
@echo Total {1} shots
@pause
'''.format(scene_num, len(full_abs_paths_list))
    end_part = '''
@echo Rendering completed
@pause'''
    print(file_path, scene_num)
    full = Path(file_path, 'episode_{}_render.bat'.format(scene_num))
    with full.open('w+') as batch_render_file:
        batch_render_file.write(first_part)
        for i, _sobject in enumerate(related_shots):
            part01 = r'"C:\Program Files\Autodesk\Maya2022\bin\Render.exe" -r file -s'
            part02 = r'-cam ubercam -rd "D:\YandexDisk\storage\Dolly_Render_YD" "D:\storage\dolly_repo_terminator\dolly3d\episodes\episode_{0}'.format(
                scene_num)
            first_frame = ranges_list[i].split('-')[0]
            last_frame = ranges_list[i].split('-')[-1]
            batch_render_file.write(
                r'{0} {1} -e {2} {3}\render\{4}'.format(
                    part01, first_frame, last_frame, part02,
                    full_abs_paths_list[i],
                )
            )
        batch_render_file.write(end_part)

    test_path = Path(file_path, 'episode_{}_render_test.bat'.format(scene_num))
    with test_path.open('w+') as batch_render_test_file:
        for i, _sobject in enumerate(related_shots):
            part01 = r'"C:\Program Files\Autodesk\Maya2022\bin\Render.exe" -r file -s'
            part02 = '-cam ubercam -rd "{0}\\test_render" "{0}'.format(file_path)
            batch_render_test_file.write(
                '{0} {1} -e {2} {3}\\{4}'.format(
                    part01, 1, 1, part02, full_abs_paths_list[i]
                )
            )
    print('DONE!')


def create_tactic_episode(episode_num, shots_count):
    filters = [('name', u'Ep{}'.format(episode_num))]
    project = api.project(PROJECT)
    episodes = project.stype('complex/scenes')
    found = episodes.query(filters=filters, limit=1).items
    episode = found[0] if found else episodes.new({
        'keywords': '',
        'sequence_code': '',
        'name': 'Ep{}'.format(episode_num),
        'description': '',
    }).commit()
    
    print(episode)
    shots = project.stype('complex/shot')
    for sh in range(1, shots_count + 1):
        print(shots.new({
            'keywords': '',
            'name': 'Sh{:02d}'.format(sh),
            'scenes_code': episode.get_code(),
            'description': '',
        }, parent=episode).commit())


def get_scene_and_parent_sobjects(search_key=None):
    search_key = search_key or handler_maya.get_skey_from_scene()
    if not search_key:
        cmds.confirmDialog(
            title='Scene is not opened!',
            message=(
                "Your scene hasn't been saved with TacticHandler, or not "
                "opened with it. Please open a scene saved with TacticHandler!"
            ),
            button=['Ok'],
            defaultButton='Ok',
        )
        return None, None

    shot = api.sobject(search_key)
    episode = api.project(PROJECT).stype('complex/scenes').get(
        code=shot.get_value('scenes_code')
    )
    return shot, episode


def add_frame_ranges_to_shot(start_frame, end_frame):

    framerange = '{0}-{1}'.format(start_frame, end_frame)
    
    shot_sobject, scene_sobject = get_scene_and_parent_sobjects()

    if shot_sobject and scene_sobject:
        print('Adding framerange {0} to {1} of {2}'.format(
            framerange, _title(shot_sobject), _title(scene_sobject)
        ))
        shot_sobject.set_value('start_frame', start_frame)
        shot_sobject.set_value('end_frame', end_frame)
        shot_sobject.commit()


def make_only_ubercam_renderable():
    # making renderable only ubercam

    # List all cameras
    all_cameras = cmds.listCameras()
    
    # Fix for constrained cameras
    for cam in all_cameras:
        camera_shape = cmds.listRelatives(cam, parent=True, fullPath=False)
        if camera_shape:
            if camera_shape[0] not in all_cameras:
                all_cameras.append(camera_shape[0])

    found_ubercam = False
    
    
    for cam in all_cameras:
        camera_shapes = cmds.listRelatives(cam, shapes=True, fullPath=True)

        if camera_shapes:
            for camera_shape in camera_shapes:
                
                if str(cmds.objectType(camera_shape)) == 'camera':
                
                    if found_ubercam:
                        print('Ubercamera Already Set as renderable. Please Check for ubercamera duplicates.')
                        cmds.setAttr('{}.renderable'.format(camera_shape), 0)
                    else:
                        if camera_shape.find('ubercam') != -1:
                            cmds.setAttr('{}.renderable'.format(camera_shape), 1)
                            print('UberCam Found. Making it renderable.')
                            cmds.setAttr('{}.rsCameraMotionBlur'.format(camera_shape), 1)
                            cmds.lookThru(camera_shape)
                            found_ubercam = True
                        else:
                            cmds.setAttr('{}.renderable'.format(camera_shape), 0)

    return found_ubercam


def create_uber_camera():
    print('Creating UberCam')
    cmds.SequenceEditor()
    return cmds.ubercam('ubercam')


def get_frame_ranges_from_sequencer():
    all_shots = cmds.sequenceManager(listShots=True)

    if not all_shots:
        return None, None

    all_frames = []
    for sh in all_shots:
        all_frames.append(cmds.shot(sh, q=True, sequenceStartTime=True))
        all_frames.append(cmds.shot(sh, q=True, sequenceEndTime=True))

    start_frame = min(all_frames)
    end_frame = max(all_frames)

    return start_frame, end_frame


def apply_redshift_preset():
    print('Applying Preset niki_rs3_prod')
    #mel.eval('loadNodePresets "niki_rs3_prod";')
    import maya.app.renderSetup.views.renderSetupPreferences as prefs
    prefs.loadUserPreset('niki_rs3_prod')


def apply_fast_redshift_preset():
    print('Applying Preset niki_rs3_fast')
    import maya.app.renderSetup.views.renderSetupPreferences as prefs
    prefs.loadUserPreset('niki_rs3_fast')


def setting_rander_globals(episode, shot, start_frame, end_frame):
    print('Applying Render Globals')

    shot_sobject, scene_sobject = get_scene_and_parent_sobjects()
    
    episode = _title(scene_sobject)
    shot = _title(shot_sobject)


    shot_string = '{0}/{1}/{1}'.format(episode, shot)
    cmds.setAttr('defaultRenderGlobals.ifp', shot_string, type='string')
    cmds.setAttr('defaultRenderGlobals.animation', 1)
    cmds.setAttr('defaultRenderGlobals.animationRange', 1)

    print('Setting frame range: {0}-{1}'.format(start_frame, end_frame))
    cmds.setAttr('defaultRenderGlobals.startFrame', int(start_frame))
    cmds.setAttr('defaultRenderGlobals.endFrame', int(end_frame))

    cmds.setAttr('defaultRenderGlobals.byFrameStep', 1)
    cmds.setAttr('defaultRenderGlobals.extensionPadding', 4)

    cmds.setAttr('redshiftOptions.imageFormat', 2)

    cmds.setAttr('defaultResolution.width', 1920)
    cmds.setAttr('defaultResolution.height', 1080)


def enshure_redshift_started():
    print('Loading Redshift')
    cmds.setAttr('defaultRenderGlobals.currentRenderer', 'redshift', type='string')


def cleanup_unknown_nodes():
    print('Cleanup Unknown Nodes')
    #mel.eval('putenv "MAYA_TESTING_CLEANUP" "1";scOpt_performOneCleanup( { "unknownNodesOption" } );putenv "MAYA_TESTING_CLEANUP" "0";hideOptionBox;')
    mel.eval("source cleanUpScene;deleteUnknownNodes()")


def connect_redshift_nodes():
    redshift_options = cmds.ls(type='RedshiftOptions')[0]

    lens = cmds.ls(type='RedshiftLensDistortion')
    if lens:
        out_connect = '{}.message'.format(lens[0])
        in_connect = '{}.lensDistortion'.format(redshift_options)
        if not cmds.isConnected(out_connect, in_connect):
            cmds.connectAttr(out_connect, in_connect)

    volume = cmds.ls(type='RedshiftVolumeScattering')
    if volume:
        out_connect = '{}.message'.format(volume[0])
        in_connect = '{}.atmosphere'.format(redshift_options)
        if not cmds.isConnected(out_connect, in_connect):
            cmds.connectAttr(out_connect, in_connect)

    sky = cmds.ls(type='RedshiftPhysicalSky')
    if sky:
        out_connect = '{}.message'.format(sky[0])
        in_connect = '{}.environment'.format(redshift_options)
        if not cmds.isConnected(out_connect, in_connect):
            try:
                cmds.connectAttr(out_connect, in_connect)
            except:
                print('!!! RedshiftPhysicalSky ALREADY CONNECTED !!!')

    exposure = cmds.ls(type='RedshiftPhotographicExposure')
    if exposure:
        out_connect = '{}.message'.format(exposure[0])
        in_connect = '{}.exposure'.format(redshift_options)
        if not cmds.isConnected(out_connect, in_connect):
            try:
                cmds.connectAttr(out_connect, in_connect)
            except:
                print('!!! RedshiftPhotographicExposure ALREADY CONNECTED !!!')

    post = cmds.ls(type='RedshiftPostEffects')
    if post:
        out_connect = '{}.message'.format(post[0])
        in_connect = '{}.postEffects'.format(redshift_options)
        if not cmds.isConnected(out_connect, in_connect):
            try:
                cmds.connectAttr(out_connect, in_connect)
            except:
                print('!!! RedshiftPostEffects ALREADY CONNECTED !!!')

    bokeh = cmds.ls(type='RedshiftBokeh')
    if bokeh:
        out_connect = '{}.message'.format(bokeh[0])
        in_connect = '{}.bokeh'.format(redshift_options)
        if not cmds.isConnected(out_connect, in_connect):
            try:
                cmds.connectAttr(out_connect, in_connect)
            except:
                print('!!! RedshiftBokeh ALREADY CONNECTED !!!')


def open_needed_widnows():
    print('Init Render Settings')
    mel.eval('unifiedRenderGlobalsWindow;fillSelectedTabForCurrentRenderer;')


def dolly_render_setup(episode=None, shot=None, start_frame=None, end_frame=None, fast=False):
    open_needed_widnows()
    enshure_redshift_started()
    if fast:
        apply_fast_redshift_preset()
    else:
        apply_redshift_preset()
    setting_rander_globals(episode, shot, start_frame, end_frame)

    if not make_only_ubercam_renderable():
        create_uber_camera()
        make_only_ubercam_renderable()

    cleanup_unknown_nodes()
    
    connect_redshift_nodes()


def create_render_setup_dialog():
    main_dialog = QtWidgets.QDialog(handler_maya.get_maya_window())
    main_dialog.setWindowTitle('Dolly 3D Render Setup')

    # Setting Main Dialog Attributes
    main_dialog.setMinimumWidth(420)
    main_dialog.setMinimumHeight(140)

    main_layout = QtWidgets.QVBoxLayout()
    main_dialog.setLayout(main_layout)

    # Creating Render Setup Button
    render_setup_button = QtWidgets.QPushButton('Start Render Setup')
    fast_render_setup_button = QtWidgets.QPushButton('Fast Render Setup')
    #generate_batch_button = QtWidgets.QPushButton('Generate Batch')

    def render_setup_button_action():
        fill_frame_ranges()
    
        episode_str = str(episode_edit.text())
        shot_str = str(shot_edit.text())
        start_frame_str = int(start_frame_edit.text())
        end_frame_str = int(end_frame_edit.text())

        dolly_render_setup(episode_str, shot_str, start_frame_str, end_frame_str)

    def fast_render_setup_button_action():
        fill_frame_ranges()
    
        episode_str = str(episode_edit.text())
        shot_str = str(shot_edit.text())
        start_frame_str = int(start_frame_edit.text())
        end_frame_str = int(end_frame_edit.text())

        dolly_render_setup(episode_str, shot_str, start_frame_str, end_frame_str, fast=True)

    render_setup_button.clicked.connect(render_setup_button_action)
    fast_render_setup_button.clicked.connect(fast_render_setup_button_action)
    #generate_batch_button.clicked.connect(generate_batch)

    # def create_tactic_episode_dlg():
    #     dlg = QtWidgets.QDialog(handler_maya.get_maya_window())
    #     dlg.setMinimumWidth(320)
    #     dlg.setMinimumHeight(80)
    #     l = QtWidgets.QVBoxLayout()
    #     dlg.setLayout(l)
    #
    #     episode_num_edit = QtWidgets.QLineEdit()
    #     episode_num_edit.setText('')
    #     shots_count_edit = QtWidgets.QLineEdit()
    #     shots_count_edit.setText('')
    #     create_episode_button = QtWidgets.QPushButton('Create')
    #     create_episode_button.clicked.connect(lambda: create_tactic_episode(int(episode_num_edit.text()), int(shots_count_edit.text())))
    #
    #     l.addWidget(episode_num_edit)
    #     l.addWidget(shots_count_edit)
    #     l.addWidget(create_episode_button)
    #
    #     dlg.show()

    def add_framerange_to_shot():
        fill_frame_ranges()
    
        #episode = episode_edit.text()
        #shot = shot_edit.text()

        start_frame = start_frame_edit.text()
        end_frame = end_frame_edit.text()


        #add_description_to_shot(episode, shot, framerange)
        add_frame_ranges_to_shot(start_frame, end_frame)

    def fill_frame_ranges():
        # getting frame ranges from camera sequencer
        start_frame, end_frame = get_frame_ranges_from_sequencer()
        if start_frame:
            start_frame_edit.setText(str(int(start_frame)))
        if end_frame:
            end_frame_edit.setText(str(int(end_frame)))

    # Creating Shot Attributes
    shot_attr_layout = QtWidgets.QHBoxLayout()

    episode_label = QtWidgets.QLabel('Episode Number:')
    shot_label = QtWidgets.QLabel('Shot Number:')

    episode_edit = QtWidgets.QLineEdit()
    episode_edit.setText('1')
    shot_edit = QtWidgets.QLineEdit()
    shot_edit.setText('1')

    create_tactic_episode_button = QtWidgets.QPushButton('Create Episode')
    create_tactic_episode_button.clicked.connect(lambda: create_tactic_episode(int(episode_edit.text()), int(shot_edit.text())))

    shot_attr_layout.addWidget(episode_label)
    shot_attr_layout.addWidget(episode_edit)
    shot_attr_layout.addWidget(shot_label)
    shot_attr_layout.addWidget(shot_edit)
    shot_attr_layout.addWidget(create_tactic_episode_button)

    # Creating Ranges
    frame_range_layout = QtWidgets.QHBoxLayout()

    start_frame_label = QtWidgets.QLabel('Start Frame:')
    end_frame_label = QtWidgets.QLabel('End Frame:')

    start_frame_edit = QtWidgets.QLineEdit()
    start_frame_edit.setText('1')
    end_frame_edit = QtWidgets.QLineEdit()
    end_frame_edit.setText('10')

    update_frame_ranges_button = QtWidgets.QPushButton('Update')
    update_frame_ranges_button.clicked.connect(fill_frame_ranges)

    apply_frameranges_button = QtWidgets.QPushButton('Apply Frameranges')
    apply_frameranges_button.clicked.connect(add_framerange_to_shot)

    frame_range_layout.addWidget(start_frame_label)
    frame_range_layout.addWidget(start_frame_edit)
    frame_range_layout.addWidget(end_frame_label)
    frame_range_layout.addWidget(end_frame_edit)
    frame_range_layout.addWidget(update_frame_ranges_button)
    frame_range_layout.addWidget(apply_frameranges_button)

    # Adding all to Main Layout

    main_layout.addLayout(shot_attr_layout)
    main_layout.addLayout(frame_range_layout)
    main_layout.addWidget(render_setup_button)
    main_layout.addWidget(fast_render_setup_button)
    #main_layout.addWidget(generate_batch_button)

    fill_frame_ranges()

    main_dialog.show()
