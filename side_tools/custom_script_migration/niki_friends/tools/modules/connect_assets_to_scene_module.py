from pathlib import Path

import maya.cmds as cmds

from tactic_handler_api import get_api
from tactic_handler_dcc import maya as handler_maya


PROJECT = "niki_friends"
api = get_api()


def check_attached_assets(search_key=None):
    """Return the assets attached to the current asset or shot episode."""
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


def check_and_connect_assets(attached_assets, parent):
    files = get_assets_files_list()
    attached_names = {asset.get_value("name") for asset in attached_assets}
    asset_type = api.project(PROJECT).stype("dolly3d/assets")

    for index, path in enumerate(files):
        progress = int(index * 100 / len(files))
        cmds.progressWindow(
            edit=True,
            progress=progress,
            status="Connecting Assets SObjects: {}%".format(progress),
        )
        if cmds.progressWindow(query=True, isCancelled=True):
            break

        name = Path(path).stem
        if name in attached_names:
            continue
        assets = asset_type.query(filters=[("name", name)], limit=1).items
        if not assets:
            continue

        asset = assets[0]
        print("Attaching asset {}".format(asset.get_value("name")))
        if parent.get_stype().get_code() == "dolly3d/assets":
            parent.link(
                asset,
                relation="dolly3d/assets_in_assets",
                path="parent",
            )
        else:
            parent.link(asset, relation="dolly3d/assets_in_scenes")


def begin_process_assets(search_key=None):
    attached_assets, parent = check_attached_assets(search_key)
    if parent:
        check_and_connect_assets(attached_assets, parent)
    cmds.progressWindow(endProgress=1)
    return True
