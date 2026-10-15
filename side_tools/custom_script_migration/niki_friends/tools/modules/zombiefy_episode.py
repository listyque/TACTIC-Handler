from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import maya.cmds as cmds
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


def get_all_zombie_assets():
    return api.project(PROJECT).stype("dolly3d/assets").query(
        filters=[("name", "like", "%Zombie")],
        order_by=["name"],
        limit=1000,
    ).items


def check_attached_assets(search_key=None):
    """Return assets attached to the current asset or shot episode."""
    search_key = search_key or handler_maya.get_skey_from_scene()
    if not search_key:
        cmds.confirmDialog(
            title="Scene is not opened!",
            message=(
                "Your scene hasn't been saved with TacticHandler, or not "
                "opened with it. Please open a scene saved with TacticHandler!"
            ),
            button=["Ok"],
            defaultButton="Ok",
        )
        return None, None

    cmds.progressWindow(
        title="Checking Assets",
        progress=0,
        status="Checking attached Assets: 0%",
        isInterruptable=True,
    )
    parent = api.sobject(search_key)
    if parent.get_stype().get_code() != "dolly3d/assets":
        parent = api.project(PROJECT).stype("complex/scenes").get(
            code=parent.get_value("scenes_code")
        )
    return parent.related(search_type="dolly3d/assets"), parent


def get_assets_files_list():
    assets = set()
    for node in cmds.ls(type="reference"):
        try:
            assets.add(cmds.referenceQuery(
                node, filename=True, withoutCopyNumber=True
            ))
        except RuntimeError:
            print("BUGGED NODE", node)
    return assets


def zombiefy_all_episode_assets():
    """Replace scene references with matching Zombie asset publishes."""
    files = get_assets_files_list()
    zombie_assets = get_all_zombie_assets()

    for index, path in enumerate(files):
        progress = int(index * 100 / len(files))
        cmds.progressWindow(
            edit=True,
            progress=progress,
            status="Replacing Assets with Zombies: {}%".format(progress),
        )
        if cmds.progressWindow(query=True, isCancelled=True):
            break

        asset_name = Path(path).stem
        for zombie_asset in zombie_assets:
            zombie_name = zombie_asset.get_value("name").split("Zombie")[0][:-1]
            if asset_name != zombie_name:
                continue

            snapshot = next((
                snapshot
                for snapshot in zombie_asset.snapshots(process="publish")
                if snapshot.is_versionless()
            ), None)
            if not snapshot:
                continue
            main_file = next((
                file_object
                for file_object in snapshot.get_files_objects()
                if file_object.get_type() == "main"
            ), None)
            if not main_file:
                continue

            reference = cmds.file(path, rfn=True, query=True)
            cmds.file(
                Path(main_file.get_full_abs_path()).as_posix(),
                loadReference=reference,
            )


def begin_zombiefy_assets(search_key=None):
    _assets, parent = check_attached_assets(search_key)
    if parent:
        zombiefy_all_episode_assets()
    cmds.progressWindow(endProgress=1)
    return True


def checkin_current_shot():
    current_shot, episode = get_scene_and_parent_sobjects()
    if not current_shot:
        return False

    episode_name = _title(episode)
    if not episode_name.endswith("_Zombie"):
        episode_name += "_Zombie"

    episodes = api.project(PROJECT).stype("complex/scenes")
    zombie_episodes = episodes.query(
        filters=[("name", episode_name)], limit=1
    ).items
    if not zombie_episodes:
        raise RuntimeError("Create the Zombie episode before saving this shot")

    zombie_shots = api.project(PROJECT).stype("complex/shot").query(
        filters=[
            ("scenes_code", zombie_episodes[0].get_code()),
            ("name", current_shot.get_value("name")),
        ],
        limit=1,
    ).items
    if not zombie_shots:
        raise RuntimeError("The matching Zombie shot does not exist")

    zombie_shot = zombie_shots[0]
    search_key = handler_maya.get_skey_from_scene() or ""
    context = parse_qs(urlsplit(search_key).query).get("context", [""])[0]
    runtime = handler_maya.runtime()
    if runtime is None or not runtime.connected:
        raise RuntimeError("TACTIC Handler is not connected to Maya")

    print("Making server checkin for current scene {}".format(
        _title(zombie_shot)
    ))
    api.ui.checkin_from_maya(
        zombie_shot.get_search_key(),
        context,
        "Fast Save",
        runtime.client_id,
    ).wait()
    return True


def get_scene_and_parent_sobjects(search_key=None):
    search_key = search_key or handler_maya.get_skey_from_scene()
    if not search_key:
        cmds.confirmDialog(
            title="Scene is not opened!",
            message=(
                "Your scene hasn't been saved with TacticHandler, or not "
                "opened with it. Please open a scene saved with TacticHandler!"
            ),
            button=["Ok"],
            defaultButton="Ok",
        )
        return None, None

    shot = api.sobject(search_key)
    episode = api.project(PROJECT).stype("complex/scenes").get(
        code=shot.get_value("scenes_code")
    )
    return shot, episode


def create_zombie_episode(episode_name, source_episode, related_shots):
    project = api.project(PROJECT)
    episodes = project.stype("complex/scenes")
    found = episodes.query(filters=[("name", episode_name)], limit=1).items

    print("Inserting", episode_name, len(related_shots))
    if found:
        episode = found[0]
    else:
        source = source_episode.get_info()
        fields = (
            "keywords", "description", "duration", "pipeline_code", "script",
            "storyboard",
        )
        data = {field: source[field] for field in fields if source.get(field) is not None}
        data["name"] = episode_name
        episode = episodes.new(data).commit(triggers=False)

    print("Episode created!")
    shots = project.stype("complex/shot")
    fields = "start_frame description end_frame pipeline_code name".split()
    for shot in related_shots:
        source = shot.get_info()
        data = {field: source[field] for field in fields if source.get(field) is not None}
        created = shots.new(data, parent=episode).commit(triggers=False)
        print("Created shot:", created)


def create_render_setup_dialog():
    dialog = QtWidgets.QDialog(handler_maya.get_maya_window())
    dialog.setWindowTitle("Dolly 3D Episodes Zombiefier")
    dialog.setMinimumWidth(320)
    dialog.setMinimumHeight(80)

    layout = QtWidgets.QVBoxLayout(dialog)
    shot, episode = get_scene_and_parent_sobjects()
    if not shot:
        return None
    related_shots = episode.related(search_type=shot.get_stype().get_code())
    episode_name = _title(episode)
    zombiefied = episode_name.endswith("_Zombie")

    row = QtWidgets.QHBoxLayout()
    episode_edit = QtWidgets.QLineEdit(
        episode_name if zombiefied else "{}_Zombie".format(episode_name)
    )
    shot_edit = QtWidgets.QLineEdit(str(len(related_shots)))
    row.addWidget(QtWidgets.QLabel("Episode Name:"))
    row.addWidget(episode_edit)
    row.addWidget(QtWidgets.QLabel("Shots Count:"))
    row.addWidget(shot_edit)

    create_episode = QtWidgets.QPushButton("Zombiefy this Episode")
    zombiefy_shot = QtWidgets.QPushButton("Zombiefy opened Shot!")
    save_shot = QtWidgets.QPushButton("Save Shot")
    create_episode.clicked.connect(
        lambda: create_zombie_episode(
            episode_edit.text(), episode, related_shots
        )
    )
    zombiefy_shot.clicked.connect(begin_zombiefy_assets)
    save_shot.clicked.connect(checkin_current_shot)

    if zombiefied:
        episode_edit.setEnabled(False)
        shot_edit.setEnabled(False)
        create_episode.setEnabled(False)

    layout.addLayout(row)
    layout.addWidget(create_episode)
    layout.addWidget(zombiefy_shot)
    layout.addWidget(save_shot)
    dialog.show()
    return dialog
