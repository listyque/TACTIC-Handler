from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .registry import CommandRegistry


class MayaAdapter:
    def __init__(self):
        import maya.cmds as cmds
        import maya.mel as mel
        import maya.utils as maya_utils

        self.cmds = cmds
        self.mel = mel
        self.dispatch = maya_utils.executeInMainThreadWithResult

    def registry(self):
        registry = CommandRegistry()
        for name, handler in (
            ("get_application_info", self.get_application_info),
            ("get_current_scene", self.get_current_scene),
            ("prepare_scene", self.prepare_scene),
            ("validate_scene", self.validate_scene),
            ("save_current_scene", self.save_current_scene),
            ("prepare_checkin", self.prepare_checkin),
            ("open_scene", self.open_scene),
            ("import_file", self.import_file),
            ("reference_file", self.reference_file),
        ):
            registry.register(name, self._main_thread(handler))
        return registry

    def _main_thread(self, handler):
        return lambda payload: self.dispatch(handler, payload)

    def get_application_info(self, _payload):
        return {
            "application": "maya",
            "version": str(self.cmds.about(version=True)),
            "process_id": os.getpid(),
        }

    def get_current_scene(self, payload):
        scene_type = self.cmds.file(query=True, type=True) or []
        result = {
            "path": str(self.cmds.file(query=True, sceneName=True) or ""),
            "modified": bool(self.cmds.file(query=True, modified=True)),
            "scene_type": str(scene_type[0] if scene_type else ""),
            "project": str(self.cmds.workspace(query=True, rootDirectory=True) or ""),
            "workspace": str(self.cmds.workspace(query=True, fullName=True) or ""),
        }
        if payload.get("include_selection"):
            result["selection"] = list(self.cmds.ls(selection=True, long=True) or [])
        return result

    def prepare_scene(self, payload):
        scene = self.get_current_scene(payload)
        scene["ready"] = bool(scene["path"])
        return scene

    def validate_scene(self, payload):
        scene = self.get_current_scene(payload)
        warnings = []
        if not scene["path"]:
            warnings.append("Scene has no path")
        return {"valid": not warnings, "warnings": warnings, "scene": scene}

    def save_current_scene(self, payload):
        path = str(payload.get("path") or "")
        if path:
            self.cmds.file(rename=str(Path(path).expanduser()))
        scene_type = str(payload.get("scene_type") or "")
        kwargs = {"save": True, "force": bool(payload.get("force", False))}
        if scene_type:
            kwargs["type"] = scene_type
        self._set_tactic_context(payload)
        self.cmds.file(**kwargs)
        return {
            "success": True, "cancelled": False,
            "path": str(self.cmds.file(query=True, sceneName=True) or ""),
            "prepared": self.prepare_scene({}),
            "target": self._target_result(payload),
        }

    def prepare_checkin(self, payload):
        saved = self.save_current_scene(payload)
        scene_path = str(saved.get("path") or "")
        previews = []
        if bool(payload.get("generate_previews", True)):
            preview_root = Path(tempfile.gettempdir()) / "tactic_handler_maya"
            preview_root.mkdir(parents=True, exist_ok=True)
            preview_prefix = preview_root / "scene_playblast"
            frame = self.cmds.currentTime(query=True)
            generated = self.cmds.playblast(
                format="image",
                filename=str(preview_prefix),
                forceOverwrite=True,
                viewer=False,
                showOrnaments=False,
                percent=100,
                compression="jpg",
                quality=90,
                widthHeight=(640, 360),
                startTime=frame,
                endTime=frame,
            )
            preview_path = self._playblast_path(generated, preview_prefix)
            if preview_path:
                previews.append({
                    "path": preview_path,
                    "type": "playblast",
                    "role": "preview",
                })
        return {
            **saved,
            "files": [{
                "path": scene_path,
                "type": "maya",
                "role": "main",
            }],
            "previews": previews,
        }

    @staticmethod
    def _playblast_path(generated, prefix):
        candidate = Path(str(generated or ""))
        if candidate.is_file():
            return str(candidate.resolve())
        matches = sorted(prefix.parent.glob(f"{prefix.name}*"))
        return str(matches[-1].resolve()) if matches else ""

    def open_scene(self, payload):
        path = self._path(payload)
        if (
            self.cmds.file(query=True, modified=True)
            and not bool(payload.get("force", False))
            and not bool(self.mel.eval('saveChanges("file -f -new")'))
        ):
            return {"success": False, "cancelled": True, "opened_path": ""}
        self.cmds.file(
            path, open=True, force=True,
            ignoreVersion=bool(payload.get("ignore_version", True)),
        )
        return {
            "success": True, "cancelled": False, "opened_path": path,
            "target": self._target_result(payload),
            "snapshot": dict(payload.get("snapshot") or {}),
        }

    def import_file(self, payload):
        path = self._path(payload)
        namespace = str(payload.get("namespace") or Path(path).stem).replace(".", "_")
        repeat_count = max(1, min(int(payload.get("repeat_count") or 1), 100))
        for index in range(repeat_count):
            current_namespace = namespace if repeat_count == 1 else f"{namespace}_{index + 1}"
            self.cmds.file(
                path, i=True, namespace=current_namespace,
                ignoreVersion=bool(payload.get("ignore_version", True)),
            )
        return {"success": True, "cancelled": False, "opened_path": path}

    def reference_file(self, payload):
        path = self._path(payload)
        namespace = str(payload.get("namespace") or Path(path).stem).replace(".", "_")
        repeat_count = max(1, min(int(payload.get("repeat_count") or 1), 100))
        for index in range(repeat_count):
            current_namespace = namespace if repeat_count == 1 else f"{namespace}_{index + 1}"
            self.cmds.file(
                path, reference=True, namespace=current_namespace,
                ignoreVersion=bool(payload.get("ignore_version", True)),
            )
        return {"success": True, "cancelled": False, "opened_path": path}

    @staticmethod
    def _path(payload):
        path = Path(str(payload.get("path") or "")).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Scene file does not exist: {path}")
        return str(path.resolve())

    def _set_tactic_context(self, payload):
        search_key = str(payload.get("search_key") or "")
        if not search_key:
            return
        context = str(payload.get("context") or payload.get("process") or "publish")
        value = search_key if search_key.startswith("skey://") else f"skey://{search_key}"
        value = f"{value}&context={context}"
        if not self.cmds.attributeQuery(
            "tacticHandler_skey", node="defaultObjectSet", exists=True
        ):
            self.cmds.addAttr(
                "defaultObjectSet", longName="tacticHandler_skey",
                dataType="string",
            )
        self.cmds.setAttr(
            "defaultObjectSet.tacticHandler_skey", value, type="string"
        )

    @staticmethod
    def _target_result(payload):
        return {
            key: payload.get(key)
            for key in ("project_code", "search_key", "code", "title", "process", "context")
            if payload.get(key) not in (None, "")
        }
