from __future__ import annotations

import tempfile
from pathlib import Path


class MayaFunctions:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def _cmds():
        import maya.cmds as cmds
        return cmds

    def get_skey_from_scene(self):
        cmds = self._cmds()
        if cmds.attributeQuery(
            "tacticHandler_skey", node="defaultObjectSet", exists=True
        ):
            return cmds.getAttr("defaultObjectSet.tacticHandler_skey")
        return None

    def get_current_scene_format(self):
        scene_format = self._cmds().file(query=True, type=True) or []
        return scene_format[0] if scene_format else "mayaBinary"

    def set_info_to_scene(self, search_key, context):
        cmds = self._cmds()
        value = f"skey://{search_key}&context={context}"
        if not cmds.attributeQuery(
            "tacticHandler_skey", node="defaultObjectSet", exists=True
        ):
            cmds.addAttr(
                "defaultObjectSet", longName="tacticHandler_skey",
                dataType="string",
            )
        cmds.setAttr(
            "defaultObjectSet.tacticHandler_skey", value, type="string"
        )

    def prepare_checkin_scene(self, selected_objects=None):
        cmds = self._cmds()
        scene_types = cmds.file(query=True, type=True) or []
        scene_type = str(scene_types[0] if scene_types else "mayaBinary")
        extensions = {"mayaBinary": "mb", "mayaAscii": "ma"}
        if (
            isinstance(selected_objects, (list, tuple))
            and len(selected_objects) > 1
            and isinstance(selected_objects[1], dict)
            and selected_objects[1]
        ):
            scene_type = str(next(iter(selected_objects[1])))
            extensions.update(selected_objects[1])
        extension = str(extensions.get(scene_type) or "ma")
        export_selected = bool(
            selected_objects and selected_objects[0]
            if isinstance(selected_objects, (list, tuple))
            else selected_objects
        )
        if export_selected:
            folder = Path(tempfile.gettempdir()) / "tactic-handler-dcc"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"selected_scene.{extension}"
            cmds.file(
                str(path), exportSelected=True, force=True,
                type=scene_type,
            )
        else:
            scene_path = str(cmds.file(query=True, sceneName=True) or "")
            if not scene_path:
                raise RuntimeError(
                    "Save the current Maya scene before check-in"
                )
            path = Path(scene_path)
            if bool(cmds.file(query=True, modified=True)):
                cmds.file(save=True, force=True, type=scene_type)
        return {
            "path": str(path),
            "scene_type": scene_type,
            "modified": bool(cmds.file(query=True, modified=True)),
            "selected_objects": export_selected,
        }
