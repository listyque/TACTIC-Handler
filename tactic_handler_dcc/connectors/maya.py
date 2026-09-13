from __future__ import annotations

import code
import contextlib
import ctypes
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

from tactic_handler_api.operations import allow_blocking_calls

from . import STANDARD_ITEM_ACTIONS


DCC_MANIFEST = {
    "application": "maya",
    "title": "Maya DCC",
    "script_triggers": (
        ("scene.open", "Open scene", "folder_open"),
        ("scene.import", "Import scene", "input"),
        ("scene.reference", "Reference scene", "link"),
        ("scene.save", "Save scene", "save"),
    ),
    "ui": {
        "item_actions": (
            {
                **STANDARD_ITEM_ACTIONS[0],
                "options": ({
                    "key": "setup_workdir",
                    "type": "boolean",
                    "title": "Set project from the file directory",
                    "description": "Open the file directory as the Maya workspace.",
                    "default": True,
                },),
            },
            {
                **STANDARD_ITEM_ACTIONS[1],
                "options": ({
                    "key": "scene_type",
                    "type": "choice",
                    "title": "Scene format",
                    "description": "Format used when Commit Queue saves the final scene.",
                    "default": "mayaBinary",
                    "choices": (
                        {"label": "Maya Binary (.mb)", "value": "mayaBinary"},
                        {"label": "Maya ASCII (.ma)", "value": "mayaAscii"},
                    ),
                },),
            },
            {
                **STANDARD_ITEM_ACTIONS[2],
                "options": ({
                    "key": "repeat_count",
                    "type": "integer",
                    "title": "Import count",
                    "description": "Number of copies to import.",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 100,
                },),
            },
            {
                **STANDARD_ITEM_ACTIONS[3],
                "options": ({
                    "key": "repeat_count",
                    "type": "integer",
                    "title": "Reference count",
                    "description": "Number of references to create.",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 100,
                },),
            },
        ),
        "configuration": {
            "title": "Maya Scene",
            "description": "Scene integration and Maya defaults",
            "icon": "movie",
            "help_topic": "configuration.maya",
            "sections": (
                {
                    "title": "Maya scene environment",
                    "description": "Scene workspace and the preferred Maya file format.",
                    "icon": "movie",
                    "fields": (
                        {
                            "key": "current_workdir",
                            "type": "text",
                            "title": "Current work directory",
                            "description": "Workspace directory supplied by the Maya integration.",
                            "default": "",
                            "read_only": True,
                        },
                        {
                            "key": "scene_type",
                            "type": "choice",
                            "title": "Maya saving format",
                            "description": "Default format used to prepare a scene for check-in.",
                            "default": "mayaBinary",
                            "choices": (
                                {"label": "Maya ASCII (.ma)", "value": "mayaAscii"},
                                {"label": "Maya Binary (.mb)", "value": "mayaBinary"},
                            ),
                        },
                        {
                            "key": "create_maya_dirs",
                            "type": "boolean",
                            "title": "Create Maya directories",
                            "description": "Prepare the standard Maya project folder structure.",
                            "default": False,
                        },
                        {
                            "key": "create_playblast",
                            "type": "boolean",
                            "title": "Create playblast",
                            "description": "Prepare a playblast image when the workflow supports it.",
                            "default": True,
                        },
                    ),
                },
                {
                    "title": "Window behavior",
                    "description": "Choose which application receives focus after Maya actions.",
                    "icon": "window-restore",
                    "fields": (
                        {
                            "key": "focus_after_open",
                            "type": "boolean",
                            "title": "Return focus after opening a scene",
                            "description": "Bring Maya forward after opening, importing, or referencing.",
                            "default": True,
                        },
                        {
                            "key": "focus_after_save",
                            "type": "boolean",
                            "title": "Return focus after saving a scene",
                            "description": "Bring Maya forward after saving or preparing a check-in.",
                            "default": True,
                        },
                    ),
                },
            ),
        },
        "focus_preferences": {
            "open_scene": "focus_after_open",
            "import_file": "focus_after_open",
            "reference_file": "focus_after_open",
            "save_current_scene": "focus_after_save",
            "prepare_checkin": "focus_after_save",
        },
    },
}


class _TeeStream:
    def __init__(self, primary, capture):
        self._primary = primary
        self._capture = capture

    def write(self, value):
        self._capture.write(value)
        if self._primary is not None:
            self._primary.write(value)
        return len(value)

    def flush(self):
        self._capture.flush()
        flush = getattr(self._primary, "flush", None)
        if flush:
            flush()

    def __getattr__(self, name):
        return getattr(self._primary or self._capture, name)


class MayaConnector:
    """Maya-native capabilities and local script helpers.

    The connector owns Maya interaction only. TACTIC queries, repositories,
    snapshots, naming, and check-in remain in standalone TACTIC-Handler.
    """

    _instance = None
    _SHELF_ICON_ALIASES = {
        "content-save": "save",
        "play-arrow": "play",
    }

    def __init__(
        self, cmds=None, mel=None, dispatch=None, *, handler_path=None
    ):
        if cmds is None or mel is None or dispatch is None:
            import maya.cmds as maya_cmds
            import maya.mel as maya_mel
            import maya.utils as maya_utils

            cmds = cmds or maya_cmds
            mel = mel or maya_mel
            dispatch = (
                dispatch or maya_utils.executeInMainThreadWithResult
            )
        self.cmds = cmds
        self.mel = mel
        self.dispatch = dispatch
        self._script_console = code.InteractiveConsole({"__name__": "__main__"})
        self._script_editor_root = None
        if handler_path:
            self._set_handler_path(handler_path)

    @classmethod
    def instance(cls, handler_path=None):
        if cls._instance is None:
            cls._instance = cls(handler_path=handler_path)
        elif handler_path:
            cls._instance._set_handler_path(handler_path)
        return cls._instance

    def _set_handler_path(self, handler_path):
        self._script_editor_root = (
            Path(handler_path).resolve() / "custom_scripts" / ".temp"
        )

    def register(self, registry):
        """Register the fixed Maya command surface in ``registry``."""
        for name, handler in (
            ("get_application_info", self.get_application_info),
            ("get_current_scene", self.get_current_scene),
            ("prepare_scene", self.prepare_scene),
            ("validate_scene", self.validate_scene),
            ("save_current_scene", self.save_current_scene),
            ("prepare_checkin", self.prepare_checkin),
            ("get_temp_playblast", self.get_temp_playblast),
            ("focus_application", self.focus_application),
            ("open_scene", self.open_scene),
            ("import_file", self.import_file),
            ("reference_file", self.reference_file),
            ("execute_custom_script", self.execute_custom_script),
            ("execute_script_file", self.execute_script_file),
            ("create_script_shelf", self.create_script_shelf),
        ):
            registry.register(name, handler)
        return registry

    @staticmethod
    def install_exit_callback(callback):
        from maya.api import OpenMaya

        callback_id = OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kMayaExiting,
            lambda *_args: callback(),
        )
        return lambda: OpenMaya.MMessage.removeCallback(callback_id)

    def create_script_shelf(self, payload=None):
        payload = dict(payload or {})
        project = str(payload.get("project") or "").strip()
        shelf_title = " ".join(str(payload.get("name") or "").split())
        source = payload.get("buttons")
        if (
            not project
            or any(char in project for char in "/\\")
            or project in (".", "..")
            or not shelf_title
            or len(shelf_title) > 64
            or not isinstance(source, list)
        ):
            raise ValueError(
                "A safe project and Maya shelf name are required"
            )

        buttons = []
        for item in source:
            if not isinstance(item, dict):
                raise ValueError("Script shelf buttons must be objects")
            script = str(item.get("script") or "").strip().strip("/")
            if not script or ".." in Path(script).parts:
                raise ValueError("A safe custom script path is required")
            buttons.append({
                "title": str(item.get("title") or script.rsplit("/", 1)[-1]),
                "description": str(item.get("description") or script),
                "icon": str(item.get("icon") or "play-arrow"),
                "script": script,
            })

        shelf_top = self.mel.eval("$tmp = $gShelfTopLevel")
        legacy_name = self._legacy_shelf_layout_name(shelf_title)
        children = self.cmds.shelfTabLayout(
            shelf_top, query=True, childArray=True
        ) or []
        labels = self.cmds.shelfTabLayout(
            shelf_top, query=True, tabLabel=True
        ) or []
        existing = [
            child for child, label in zip(children, labels)
            if str(label).casefold() == shelf_title.casefold()
        ]
        if self.cmds.shelfLayout(legacy_name, exists=True):
            if legacy_name not in existing:
                existing.append(legacy_name)
            legacy_file = (
                Path(self.cmds.internalVar(userShelfDir=True))
                / ("shelf_" + legacy_name + ".mel")
            )
            if legacy_file.is_file():
                legacy_file.unlink()
        for child in existing:
            self.cmds.deleteUI(child)
        shelf = self.mel.eval(
            "addNewShelfTab {};".format(
                json.dumps(shelf_title, ensure_ascii=False)
            )
        )
        self.cmds.shelfTabLayout(
            shelf_top,
            edit=True,
            tabLabel=(shelf, shelf_title),
            selectTab=shelf,
        )
        handler_root = self._handler_root()
        logo = (
            handler_root / "thlib" / "ui" / "gliph"
            / "maya_shelf" / "tactic_logo.png"
        )
        self.cmds.shelfButton(
            parent=shelf,
            label="TACTIC Handler",
            annotation="Open TACTIC Handler",
            image1=str(logo) if logo.is_file() else "pythonFamily.png",
            imageOverlayLabel="TH",
            overlayLabelColor=(0.9, 0.9, 0.9),
            overlayLabelBackColor=(0.08, 0.08, 0.08, 0.85),
            command=self._shelf_command(handler_root),
            sourceType="python",
            scaleIcon=True,
            useAlpha=True,
        )
        icons = self._shelf_icons(handler_root, buttons)
        for button in buttons:
            icon = icons.get(button["icon"])
            self.cmds.shelfButton(
                parent=shelf,
                label=button["title"],
                annotation=button["description"],
                image1=icon or "pythonFamily.png",
                imageOverlayLabel=self._overlay(button["title"]),
                overlayLabelColor=(0.9, 0.9, 0.9),
                overlayLabelBackColor=(0.08, 0.08, 0.08, 0.85),
                command=self._shelf_command(
                    handler_root, project, button["script"]
                ),
                sourceType="python",
                scaleIcon=True,
                useAlpha=True,
            )
        self.mel.eval("saveAllShelves $gShelfTopLevel;")
        return {
            "shelf": shelf,
            "title": shelf_title,
            "buttons": len(buttons) + 1,
            "updated": bool(existing),
        }

    @staticmethod
    def _legacy_shelf_layout_name(title):
        digest = hashlib.sha256(str(title).encode("utf-8")).hexdigest()[:12]
        return "TACTIC_" + digest

    def _handler_root(self):
        if self._script_editor_root is None:
            raise RuntimeError("TACTIC Handler path is unavailable")
        return self._script_editor_root.parents[1]

    @staticmethod
    def _shelf_command(handler_root, project="", script=""):
        root = str(handler_root).replace("\\", "/")
        lines = [
            "import sys",
            "TACTIC_HANDLER_ROOT = {!r}".format(root),
            "if TACTIC_HANDLER_ROOT not in sys.path:",
            "    sys.path.insert(0, TACTIC_HANDLER_ROOT)",
            "from tactic_handler_dcc import maya as tactic_handler_maya",
        ]
        if script:
            lines.extend((
                "tactic_handler_runtime = tactic_handler_maya.runtime()",
                "if tactic_handler_runtime is None or "
                "tactic_handler_runtime.state in {'stopped', 'failed'}:",
                "    tactic_handler_runtime = "
                "tactic_handler_maya.startup(TACTIC_HANDLER_ROOT)",
                "tactic_handler_maya.execute_custom_script({!r}, project={!r})"
                .format(script, project)
            ))
        else:
            lines.append("tactic_handler_maya.startup(TACTIC_HANDLER_ROOT)")
        return "\n".join(lines)

    def _shelf_icons(self, handler_root, buttons):
        names = {
            str(button.get("icon") or "")
            for button in buttons
            if button.get("icon")
        }
        if not names:
            return {}
        fonts = handler_root / "thlib" / "ui" / "assets" / "fonts"
        families = (
            ("regular", "fontawesome5-regular-webfont"),
            ("solid", "fontawesome5-solid-webfont"),
        )
        charmaps = {}
        for family, stem in families:
            path = fonts / (stem + "-charmap.json")
            if path.is_file():
                with path.open("r", encoding="utf-8") as stream:
                    charmaps[family] = json.load(stream)
        if not charmaps:
            return {}

        try:
            from PySide6 import QtCore, QtGui
        except ImportError:
            from PySide2 import QtCore, QtGui

        shelf_dir = Path(self.cmds.internalVar(userShelfDir=True))
        icon_dir = shelf_dir / "tactic_handler_icons"
        icon_dir.mkdir(parents=True, exist_ok=True)
        font_names = {}
        result = {}
        for requested in names:
            name = self._SHELF_ICON_ALIASES.get(requested, requested)
            family = next((
                key for key, _stem in families
                if name in charmaps.get(key, {})
            ), "")
            if not family:
                continue
            path = icon_dir / (name + ".png")
            if not path.is_file():
                if family not in font_names:
                    stem = dict(families)[family]
                    font_id = QtGui.QFontDatabase.addApplicationFont(
                        str(fonts / (stem + ".ttf"))
                    )
                    loaded = QtGui.QFontDatabase.applicationFontFamilies(
                        font_id
                    )
                    font_names[family] = loaded[0] if loaded else ""
                if not font_names[family]:
                    continue
                image = QtGui.QImage(32, 32, QtGui.QImage.Format_ARGB32)
                image.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(image)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                font = QtGui.QFont(font_names[family])
                font.setPixelSize(20)
                painter.setFont(font)
                painter.setPen(QtGui.QColor("#e7e9ec"))
                painter.drawText(
                    image.rect(), QtCore.Qt.AlignCenter,
                    chr(int(charmaps[family][name], 16)),
                )
                painter.end()
                if not image.save(str(path), "PNG"):
                    continue
            if path.is_file():
                result[requested] = str(path)
        return result

    @staticmethod
    def _overlay(title):
        return str(title or "").strip()[:6] or "PY"

    def execute_script_file(self, payload=None):
        payload = dict(payload or {})
        root = self._script_editor_root
        path = Path(str(payload.get("path") or "")).resolve()
        if (
            root is None
            or path.suffix.lower() != ".py"
            or not path.is_relative_to(root)
            or not path.is_file()
        ):
            raise ValueError("A valid Script Editor staging file is required")
        return self._run_script(path)

    def execute_custom_script(self, payload=None):
        payload = dict(payload or {})
        project = str(payload.get("project") or "").strip()
        relative = (
            str(payload.get("script") or "")
            .strip()
            .replace("\\", "/")
            .strip("/")
        )
        if (
            self._script_editor_root is None
            or not project
            or any(char in project for char in "/\\")
            or project in (".", "..")
            or not relative
            or ".." in Path(relative).parts
        ):
            raise ValueError("A safe project and custom script path are required")
        root = self._script_editor_root.parent.resolve() / project
        path = (root / (relative + ".py")).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise FileNotFoundError(
                "Custom script was not found: {}".format(path)
            )
        kwargs = payload.get("kwargs") or {}
        if not isinstance(kwargs, dict):
            raise ValueError("Custom script kwargs must be an object")
        if kwargs:
            return self._run_custom_script(path, project, kwargs)
        return self._run_script(path)

    @staticmethod
    def _run_custom_script(path, project, kwargs):
        output = io.StringIO()
        module_name = "_tactic_handler_custom_{}".format(uuid.uuid4().hex)
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if not spec or not spec.loader:
            raise ImportError("Unable to load custom script: {}".format(path))
        module = importlib.util.module_from_spec(spec)
        module.TACTIC_SCRIPT_KWARGS = dict(kwargs)
        module.TACTIC_PROJECT_CODE = project
        sys.modules[module_name] = module
        stdout = _TeeStream(sys.stdout, output)
        stderr = _TeeStream(sys.stderr, output)
        try:
            with (
                allow_blocking_calls(),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                spec.loader.exec_module(module)
            return {
                "output": output.getvalue(),
                "result": repr(getattr(module, "RESULT", None)),
            }
        finally:
            sys.modules.pop(module_name, None)

    def _run_script(self, path):
        output = io.StringIO()
        self._script_console.locals["__file__"] = str(path)
        stdout = _TeeStream(sys.stdout, output)
        stderr = _TeeStream(sys.stderr, output)
        try:
            with (
                allow_blocking_calls(),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                incomplete = self._script_console.runsource(
                    path.read_text(encoding="utf-8"), str(path), "exec"
                )
        except (KeyboardInterrupt, SystemExit) as error:
            raise RuntimeError(
                f"{type(error).__name__}: {error}"
            ) from error
        if incomplete:
            raise SyntaxError("Script input is incomplete")
        return {"output": output.getvalue()}

    def get_application_info(self, _payload=None):
        return {
            "application": "maya",
            "version": str(self.cmds.about(version=True)),
            "process_id": os.getpid(),
            "details": self.get_maya_info_dict(),
        }

    def get_maya_info_dict(self):
        return {
            key: self.cmds.about(**{key: True})
            for key in ("cs", "uil", "osv", "os", "env", "a", "b", "p", "v")
        }

    def get_current_scene(self, payload=None):
        payload = dict(payload or {})
        scene_types = self.cmds.file(query=True, type=True) or []
        scene_type = str(
            scene_types[0] if scene_types and scene_types[0]
            else "mayaBinary"
        )
        result = {
            "path": str(self.cmds.file(query=True, sceneName=True) or ""),
            "modified": bool(self.cmds.file(query=True, modified=True)),
            "scene_type": scene_type,
            "extension": {
                "mayaAscii": "ma",
                "mayaBinary": "mb",
            }.get(scene_type, ""),
            "project": str(
                self.cmds.workspace(query=True, rootDirectory=True) or ""
            ),
            "workspace": str(
                self.cmds.workspace(query=True, fullName=True) or ""
            ),
        }
        if payload.get("include_selection"):
            result["selection"] = list(
                self.cmds.ls(selection=True, long=True) or []
            )
        return result

    def prepare_scene(self, payload=None):
        scene = self.get_current_scene(payload)
        scene["ready"] = bool(scene["path"])
        return scene

    def validate_scene(self, payload=None):
        scene = self.get_current_scene(payload)
        warnings = [] if scene["path"] else ["Scene has no path"]
        return {"valid": not warnings, "warnings": warnings, "scene": scene}

    def save_current_scene(self, payload=None):
        return self._save_current_scene(payload, return_focus=True)

    def _save_current_scene(self, payload=None, *, return_focus):
        payload = dict(payload or {})
        path = str(payload.get("path") or "")
        if path:
            target = Path(path).expanduser()
            target.parent.mkdir(parents=True, exist_ok=True)
            self.cmds.file(rename=str(target))
        elif not self.cmds.file(query=True, sceneName=True):
            raise RuntimeError(
                "An unnamed Maya scene needs a prepared save path"
            )
        scene_type = str(
            payload.get("scene_type") or self.get_current_scene_format()
        )
        options = {
            "save": True,
            "force": bool(payload.get("force", False)),
        }
        if scene_type:
            options["type"] = scene_type
        self._set_tactic_context(payload)
        self.cmds.file(**options)
        result = {
            "success": True,
            "cancelled": False,
            "path": str(self.cmds.file(query=True, sceneName=True) or ""),
            "prepared": self.prepare_scene(),
            "target": self._target_result(payload),
        }
        if return_focus:
            return self._finish_file_action(payload, result)
        return result

    def prepare_checkin(self, payload=None):
        payload = dict(payload or {})
        saved = self._save_current_scene(payload, return_focus=False)
        previews = []
        if bool(payload.get("generate_previews", True)):
            preview_path = str(payload.get("preview_path") or "")
            if preview_path:
                prefix = Path(preview_path).expanduser()
                prefix.parent.mkdir(parents=True, exist_ok=True)
            else:
                folder = Path(tempfile.gettempdir()) / "tactic_handler_maya"
                folder.mkdir(parents=True, exist_ok=True)
                prefix = folder / "scene_playblast"
            frame = self.cmds.currentTime(query=True)
            options = {
                "format": "image",
                "forceOverwrite": True,
                "viewer": False,
                "showOrnaments": False,
                "percent": 100,
                "compression": "jpg",
                "quality": 90,
                "widthHeight": (640, 360),
                "startTime": frame,
                "endTime": frame,
            }
            options[
                "completeFilename" if preview_path else "filename"
            ] = str(prefix)
            generated = self.cmds.playblast(**options)
            preview_path = self._playblast_path(generated, prefix)
            if preview_path:
                previews.append({
                    "path": preview_path,
                    "type": "playblast",
                    "role": "preview",
                })
        return self._finish_file_action(payload, {
            **saved,
            "application_info": self.get_maya_info_dict(),
            "files": [{
                "path": str(saved.get("path") or ""),
                "type": "maya",
                "role": "main",
            }],
            "previews": previews,
        })

    def focus_application(self, _payload=None):
        self._activate_main_window()
        return {"success": True}

    def open_scene(self, payload):
        source = self._payload(payload)
        path = self._path(payload)
        if source.get("focus_application", True):
            self._activate_main_window()
        if (
            self.cmds.file(query=True, modified=True)
            and not bool(source.get("force", False))
            and not bool(self.mel.eval('saveChanges("file -f -new")'))
        ):
            return {
                "success": False,
                "cancelled": True,
                "opened_path": "",
            }
        if bool(source.get("setup_workdir", False)):
            self.cmds.workspace(
                str(Path(path).parent), openWorkspace=True
            )
        try:
            self.cmds.file(
                path,
                open=True,
                force=True,
                ignoreVersion=bool(source.get("ignore_version", True)),
            )
        except RuntimeError:
            # Maya owns scene-load diagnostics. It already reports plug-in,
            # reference, script-node, and file-content failures in Maya; do
            # not turn those native diagnostics into Handler Server errors.
            pass
        return {
            "success": True,
            "cancelled": False,
            "opened_path": path,
            "target": self._target_result(source),
            "snapshot": dict(source.get("snapshot") or {}),
        }

    def import_file(self, payload):
        return self._load_file(payload, reference=False)

    def reference_file(self, payload):
        return self._load_file(payload, reference=True)

    def import_scene(self, file_object):
        return self.import_file(file_object)

    def reference_scene(self, file_object):
        return self.reference_file(file_object)

    def _load_file(self, payload, *, reference):
        source = self._payload(payload)
        path = self._path(payload)
        namespace = str(
            source.get("namespace") or Path(path).stem
        ).replace(".", "_")
        repeat_count = max(
            1, min(int(source.get("repeat_count") or 1), 100)
        )
        for index in range(repeat_count):
            current_namespace = (
                namespace if repeat_count == 1
                else f"{namespace}_{index + 1}"
            )
            options = {
                "namespace": current_namespace,
                "ignoreVersion": bool(source.get("ignore_version", True)),
                "reference" if reference else "i": True,
            }
            self.cmds.file(path, **options)
        return self._finish_file_action(source, {
            "success": True,
            "cancelled": False,
            "opened_path": path,
        })

    def _finish_file_action(self, payload, result):
        if not self._payload(payload).get("focus_application", True):
            return result
        self._activate_main_window()
        return result

    def _activate_main_window(self):
        try:
            self.cmds.showWindow("MayaWindow")
            self.cmds.setFocus("MayaWindow")
        except (AttributeError, RuntimeError):
            pass
        try:
            window = self.get_maya_window()
            if window.isMinimized():
                window.showNormal()
            else:
                window.show()
            window.raise_()
            window.activateWindow()
            if os.name == "nt":
                self._activate_windows_window(int(window.winId()))
        except (
            AttributeError, ImportError, OSError, RuntimeError,
            TypeError, ValueError,
        ):
            pass

    @staticmethod
    def get_maya_window():
        import maya.OpenMayaUI as maya_ui

        pointer = maya_ui.MQtUtil.mainWindow()
        if not pointer:
            raise RuntimeError("Maya main window is unavailable")
        try:
            from PySide6.QtWidgets import QWidget
            from shiboken6 import wrapInstance
        except ImportError:
            from PySide2.QtWidgets import QWidget
            from shiboken2 import wrapInstance
        return wrapInstance(int(pointer), QWidget)

    @staticmethod
    def _activate_windows_window(window_id):
        user32 = ctypes.windll.user32
        if user32.IsIconic(window_id):
            user32.ShowWindowAsync(window_id, 9)  # SW_RESTORE
        user32.SetForegroundWindow(window_id)
        user32.BringWindowToTop(window_id)
        user32.SetActiveWindow(window_id)
        user32.SetFocus(window_id)

    def get_current_scene_format(self):
        scene_format = self.cmds.file(query=True, type=True) or []
        return scene_format[0] if scene_format else "mayaBinary"

    def get_skey_from_scene(self):
        if self.cmds.attributeQuery(
            "tacticHandler_skey",
            node="defaultObjectSet",
            exists=True,
        ):
            return self.cmds.getAttr(
                "defaultObjectSet.tacticHandler_skey"
            )
        return None

    def set_info_to_scene(self, search_key, context):
        value = str(search_key or "")
        if not value.startswith("skey://"):
            value = f"skey://{value}"
        self._write_scene_search_key(
            f"{value}&context={str(context or 'publish')}"
        )

    def prepare_checkin_scene(self, selected_objects=None):
        scene_type = self.get_current_scene_format()
        extensions = {"mayaBinary": "mb", "mayaAscii": "ma"}
        if (
            isinstance(selected_objects, (list, tuple))
            and len(selected_objects) > 1
            and isinstance(selected_objects[1], dict)
            and selected_objects[1]
        ):
            scene_type = str(next(iter(selected_objects[1])))
            extensions.update(selected_objects[1])
        export_selected = bool(
            selected_objects[0]
            if isinstance(selected_objects, (list, tuple))
            and selected_objects
            else selected_objects
        )
        if export_selected:
            folder = Path(tempfile.gettempdir()) / "tactic-handler-dcc"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / (
                f"selected_scene.{extensions.get(scene_type, 'ma')}"
            )
            self.cmds.file(
                str(path),
                exportSelected=True,
                force=True,
                type=scene_type,
            )
        else:
            scene_path = str(
                self.cmds.file(query=True, sceneName=True) or ""
            )
            if not scene_path:
                raise RuntimeError(
                    "Save the current Maya scene before check-in"
                )
            path = Path(scene_path)
            if bool(self.cmds.file(query=True, modified=True)):
                self.cmds.file(save=True, force=True, type=scene_type)
        return {
            "path": str(path),
            "scene_type": scene_type,
            "modified": bool(self.cmds.file(query=True, modified=True)),
            "selected_objects": export_selected,
        }

    def get_temp_playblast(self, _payload=None):
        folder = Path(tempfile.gettempdir()) / "tactic_handler_maya"
        folder.mkdir(parents=True, exist_ok=True)
        capture_folder = Path(tempfile.mkdtemp(prefix="queue_", dir=folder))
        prefix = capture_folder / "playblast.jpg"
        frame = self.cmds.currentTime(query=True)
        generated = self.cmds.playblast(
            forceOverwrite=True,
            format="image",
            completeFilename=str(prefix),
            showOrnaments=False,
            widthHeight=[960, 540],
            sequenceTime=False,
            frame=[frame],
            compression="jpg",
            offScreen=False,
            viewer=False,
            percent=100,
        )
        preview_path = self._playblast_path(generated, prefix)
        if not preview_path:
            raise RuntimeError("Maya did not create the playblast preview")
        return {
            **self.get_current_scene(),
            "preview_path": preview_path,
            "preview_type": "playblast",
        }

    @staticmethod
    def _payload(payload):
        return dict(payload) if isinstance(payload, dict) else {}

    @staticmethod
    def _path(payload):
        source = payload.get("path") if isinstance(payload, dict) else payload
        if hasattr(source, "get_full_abs_path"):
            source = source.get_full_abs_path()
        path = Path(str(source or "")).expanduser()
        if not path.is_file():
            raise FileNotFoundError(
                f"Scene file does not exist: {path}"
            )
        return str(path.resolve())

    @staticmethod
    def _playblast_path(generated, prefix):
        candidate = Path(str(generated or ""))
        if candidate.is_file():
            return str(candidate.resolve())
        matches = sorted(prefix.parent.glob(f"{prefix.name}*"))
        return str(matches[-1].resolve()) if matches else ""

    def _set_tactic_context(self, payload):
        search_key = str(payload.get("search_key") or "")
        if search_key:
            self.set_info_to_scene(
                search_key,
                payload.get("context") or payload.get("process") or "publish",
            )

    def _write_scene_search_key(self, value):
        if not self.cmds.attributeQuery(
            "tacticHandler_skey",
            node="defaultObjectSet",
            exists=True,
        ):
            self.cmds.addAttr(
                "defaultObjectSet",
                longName="tacticHandler_skey",
                dataType="string",
            )
        self.cmds.setAttr(
            "defaultObjectSet.tacticHandler_skey",
            value,
            type="string",
        )

    @staticmethod
    def _target_result(payload):
        return {
            key: payload.get(key)
            for key in (
                "project_code",
                "search_key",
                "code",
                "title",
                "process",
                "context",
            )
            if payload.get(key) not in (None, "")
        }
