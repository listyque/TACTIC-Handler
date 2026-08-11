"""WorkspaceItemModel: presentation."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, QSettings, Qt, QUrl, Slot

from .results_types import WorkspaceNode
from .watch_folders import _watch_folder_record


class PresentationMixin:
    @staticmethod
    def _build_info_chips(stype, info: dict) -> list[dict]:
        hidden = {
            "id", "code", "name", "title", "description", "timestamp",
            "pipeline_code", "project_code", "status",
        }
        labels: dict[str, str] = {}
        try:
            for element in stype.get_definition("table") or []:
                name = element.get("name")
                if name:
                    labels[name] = element.get("title") or name.replace("_", " ").title()
        except (AttributeError, TypeError, KeyError):
            pass
        chips = []
        keys = labels or {
            key: key.replace("_", " ").title()
            for key in info
            if not str(key).startswith("__")
        }
        for key, label in keys.items():
            value = info.get(key)
            if key in hidden or value in (None, "") or isinstance(value, (dict, list, tuple)):
                continue
            text = str(value)
            chips.append({
                "label": str(label),
                "value": text,
                "url": text if text.startswith(("http://", "https://")) else "",
            })
            if len(chips) >= 6:
                break
        return chips

    @staticmethod
    def _pretty_size(value) -> str:
        try:
            size = float(value or 0)
        except (TypeError, ValueError):
            return ""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return ""

    @staticmethod
    def _controls_for(node: WorkspaceNode) -> list[dict]:
        signature = (
            node.node_type,
            node.needs_sync,
            node.watch_state,
            node.relationship,
            node.child_count,
        )
        if node.controls_signature == signature:
            return node.controls_cache
        if node.node_type == "sobject":
            controls = [
                {
                    "command": "repo_sync",
                    "icon": "cloud_sync",
                    "tip": "Open Repository Sync Dialog",
                    "active": node.needs_sync,
                },
                {
                    "command": "watch_folder",
                    "icon": "visibility" if node.watch_state == "enabled" else "visibility_off",
                    "tip": "Open Watch-Folder Dialog",
                    "active": node.watch_state != "none",
                },
            ]
            controls.append({
                "command": "relations",
                "icon": "sitemap",
                "tip": "Related and child sObjects",
                "active": False,
            })
            node.controls_cache = controls
            node.controls_signature = signature
            return controls
        if node.node_type == "process":
            node.controls_cache = []
            node.controls_signature = signature
            return node.controls_cache
        if node.node_type == "relation":
            controls = [{
                "command": "add_related",
                "icon": "add_circle",
                "tip": "Add new Related sObject",
                "active": node.child_count > 0,
            }]
            if node.relationship == "instance":
                controls.insert(0, {
                    "command": "link_related",
                    "icon": "link",
                    "tip": "Link sObjects Interface",
                    "active": False,
                })
            node.controls_cache = controls
            node.controls_signature = signature
            return controls
        node.controls_cache = []
        node.controls_signature = signature
        return node.controls_cache

    @staticmethod
    def _safe_file_url(file_object) -> str:
        if not file_object:
            return ""
        try:
            path = file_object.get_full_abs_path()
            if path and Path(path).is_file():
                return QUrl.fromLocalFile(str(Path(path).resolve())).toString()
        except (AttributeError, KeyError, TypeError, OSError):
            pass
        return ""

    @staticmethod
    def _is_image_file(file_object) -> bool:
        try:
            filename = str(file_object.get_filename_with_ext() or "")
        except (AttributeError, KeyError, TypeError):
            try:
                info = file_object.get_dict() or {}
                filename = str(info.get("file_name") or info.get("name") or "")
            except (AttributeError, KeyError, TypeError):
                return False
        return Path(filename).suffix.lower() in {
            ".bmp", ".gif", ".ico", ".jpeg", ".jpg", ".png",
            ".svg", ".tga", ".tif", ".tiff", ".webp",
        }

    def _preview_url(self, file_object) -> str:
        if not file_object or not self._is_image_file(file_object):
            return ""
        local_url = self._safe_file_url(file_object)
        if local_url:
            return local_url
        if (
            self.repository_sync
            and self.repository_sync.previews_through_http_enabled()
        ):
            try:
                local_path = str(file_object.get_full_abs_path() or "")
                if local_path:
                    handle = self.repository_sync.schedule_file_object(
                        file_object, process="preview", auto_start=True
                    )
                    token = f"pending-preview:{handle.task_id}"
                    self._pending_preview_paths[token] = local_path
                    return token
            except (AttributeError, KeyError, TypeError, ValueError, OSError):
                pass
        return ""

    def localize_preview(
        self, local_path: str, pending_paths: dict[str, str] | None = None
    ) -> None:
        local_path = str(Path(local_path).resolve())
        ready_url = (
            QUrl.fromLocalFile(local_path).toString()
            + f"?ready={int(time.time() * 1000)}"
        )
        changed_rows = []
        changed_tokens = set()
        for row, node in enumerate(self._items):
            pending_path = self._pending_preview_paths.get(node.preview_url)
            if pending_path and str(Path(pending_path).resolve()) == local_path:
                changed_tokens.add(node.preview_url)
                node.preview_url = ready_url
                node.preview_revealed = False
                changed_rows.append(row)
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(
                index, index, [self.PreviewUrlRole]
            )
        self._pending_preview_paths = {
            token: path
            for token, path in self._pending_preview_paths.items()
            if str(Path(path).resolve()) != local_path
        }
        self._failed_preview_tokens.difference_update(changed_tokens)

    def fail_preview(self, task_id: str) -> None:
        token = f"pending-preview:{task_id}"
        self._failed_preview_tokens.add(token)
        changed_rows = []
        for row, node in enumerate(self._items):
            if node.preview_url == token:
                node.preview_url = ""
                changed_rows.append(row)
        self._pending_preview_paths.pop(token, None)
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [self.PreviewUrlRole])

    def begin_preview_request(self, node_id: str):
        node = self._nodes.get(node_id)
        if (
            not node
            or node.preview_requested
            or node.preview_url
            or not node.preview_source
        ):
            return None
        node.preview_requested = True
        return node.node_type, node.preview_source

    @classmethod
    def prepare_preview(cls, node_type: str, source) -> list:
        if node_type == "sobject":
            return cls._root_preview_candidates(source)
        if node_type == "snapshot":
            return cls._snapshot_preview_candidates(source)
        return []

    def cancel_preview_request(self, node_id: str, source) -> None:
        node = self._nodes.get(node_id)
        if node and node.preview_source is source and not node.preview_url:
            node.preview_requested = False

    def apply_preview(
        self,
        node_id: str,
        source,
        candidates: list,
    ) -> None:
        node = self._nodes.get(node_id)
        if not node or node.preview_source is not source:
            return
        for candidate in candidates or []:
            node.preview_url = self._preview_url(candidate)
            if node.preview_url:
                break
        if not node.preview_url:
            return
        row = self._row_by_node_id.get(node_id, -1)
        if row < 0:
            return
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [self.PreviewUrlRole])

    def request_preview(self, node_id: str) -> None:
        request = self.begin_preview_request(node_id)
        if not request:
            return
        node_type, source = request
        self.apply_preview(
            node_id,
            source,
            self.prepare_preview(node_type, source),
        )

    def refresh_previews(self) -> list[str]:
        requested = [
            node.node_id for node in self._nodes.values()
            if node.preview_requested
        ]
        self._pending_preview_paths.clear()
        self._failed_preview_tokens.clear()
        changed_rows = []
        for node_id in requested:
            node = self._nodes.get(node_id)
            if not node:
                continue
            node.preview_requested = False
            node.preview_url = ""
            node.preview_revealed = False
            row = self._row_by_node_id.get(node_id, -1)
            if row >= 0:
                changed_rows.append(row)
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(
                index,
                index,
                [self.PreviewUrlRole, self.PreviewRevealedRole],
            )
        return requested

    def mark_preview_revealed(self, node_id: str) -> None:
        node = self._nodes.get(node_id)
        if not node or node.preview_revealed:
            return
        node.preview_revealed = True
        row = self._row_by_node_id.get(node_id, -1)
        if row < 0:
            return
        index = self.index(row, 0)
        self.dataChanged.emit(
            index,
            index,
            [self.PreviewRevealedRole],
        )

    @staticmethod
    def _file_exists(file_object) -> bool:
        try:
            return bool(file_object.is_exists())
        except (AttributeError, KeyError, TypeError, OSError):
            return False

    def _file_object_size(self, file_object) -> str:
        try:
            return self._pretty_size(file_object.get_file_size())
        except (AttributeError, KeyError, TypeError, OSError):
            return ""

    @classmethod
    def _snapshot_preview_candidates(cls, snapshot) -> list:
        try:
            grouped = snapshot.get_files_objects(group_by="type") or {}
        except (AttributeError, KeyError, TypeError):
            return []
        result = []
        for kind in ("icon", "web", "image", "playblast", "main"):
            candidates = grouped.get(kind) or []
            for candidate in candidates:
                try:
                    preview = candidate.get_icon_preview()
                    if preview:
                        candidate = preview
                except (AttributeError, KeyError, TypeError):
                    pass
                if candidate and cls._is_image_file(candidate):
                    result.append(candidate)
        return result

    def _snapshot_preview(self, snapshot) -> str:
        for candidate in self._snapshot_preview_candidates(snapshot):
            preview_url = self._preview_url(candidate)
            if preview_url:
                return preview_url
        return ""

    def _snapshot_preview_items(self, snapshot) -> list[dict]:
        """Return preview items in browser display order."""
        try:
            preview_objects = list(snapshot.get_previewable_files_objects() or [])
        except (AttributeError, KeyError, TypeError):
            preview_objects = []
        if not preview_objects:
            try:
                preview_objects = [fo for fo in (snapshot.get_files_objects() or [])
                                   if fo.get_type() == "web"]
            except (AttributeError, KeyError, TypeError):
                preview_objects = []
        result = []
        for file_object in preview_objects:
            candidate = file_object
            try:
                web_object = file_object.get_web_preview()
                if web_object:
                    candidate = web_object
            except (AttributeError, KeyError, TypeError):
                pass
            url = self._preview_url(candidate)
            if not url:
                try:
                    icon = file_object.get_icon_preview()
                    url = self._preview_url(icon)
                except (AttributeError, KeyError, TypeError):
                    pass
            if url:
                try:
                    name = file_object.get_filename_with_ext() or "Preview"
                except (AttributeError, KeyError, TypeError):
                    name = "Preview"
                result.append({"url": url, "title": str(name),
                               "kind": str(file_object.get_type() or "preview")})
        return result

    @staticmethod
    def _snapshot_file_records(snapshot) -> list[dict]:
        records = []
        try:
            grouped = snapshot.get_files_objects(group_by="type") or {}
        except (AttributeError, KeyError, TypeError):
            grouped = {}
        for file_type, files in grouped.items():
            for file_object in files:
                try:
                    name = file_object.get_filename_with_ext() or ""
                except (AttributeError, KeyError, TypeError):
                    name = ""
                try:
                    path = file_object.get_abs_path() or file_object.get_full_abs_path() or ""
                except (AttributeError, KeyError, TypeError):
                    path = ""
                try:
                    size = PresentationMixin._pretty_size(
                        file_object.get_file_size()
                    )
                except (AttributeError, KeyError, TypeError, OSError):
                    size = ""
                try:
                    base_type = file_object.get_base_type() or ""
                except (AttributeError, KeyError, TypeError):
                    base_type = ""
                try:
                    exists = bool(file_object.is_exists())
                except (AttributeError, KeyError, TypeError, OSError):
                    exists = False
                records.append({"type": str(file_type), "name": str(name),
                                "path": str(path), "size": str(size),
                                "baseType": str(base_type), "exists": exists})
        return records

    @staticmethod
    def _snapshot_chips(file_object, context: str = "") -> list[dict]:
        chips = []
        if context:
            chips.append({
                "label": "Context",
                "value": str(context),
                "url": "",
            })
        if not file_object:
            return chips
        try:
            meta = file_object.get_meta_file_object()
        except (AttributeError, KeyError, TypeError):
            meta = None
        if meta:
            getters = (
                ("Range", "get_sequence_frameranges_string", {"brackets": "[]"}),
                ("Frames", "get_sequence_lenght", {}),
                ("Layer", "get_layer", {}),
                ("Tiles", "get_tiles_count", {}),
            )
            for label, getter_name, kwargs in getters:
                try:
                    value = getattr(meta, getter_name)(**kwargs)
                except (AttributeError, KeyError, TypeError):
                    value = None
                if value not in (None, "", 0):
                    chips.append({"label": label, "value": str(value), "url": ""})
        try:
            metadata = file_object.get_metadata() or {}
            maya_version = (metadata.get("app_info") or {}).get("p")
        except (AttributeError, KeyError, TypeError):
            maya_version = None
        if maya_version:
            chips.append({"label": "Maya", "value": str(maya_version), "url": ""})
        return chips

    @staticmethod
    def _snapshot_author(login: str) -> str:
        if not login:
            return ""
        try:
            from thlib.environment import env_inst
            login_object = env_inst.get_all_logins(login)
            if login_object:
                return str(login_object.get_display_name() or login)
        except (AttributeError, KeyError, TypeError):
            pass
        return str(login)

    @staticmethod
    def _repository_title(repository: str) -> str:
        if not repository:
            return ""
        try:
            from thlib.environment import env_tactic
            base_dir = env_tactic.get_base_dir(repository) or {}
            value = base_dir.get("value") or ()
            if len(value) > 1 and value[1]:
                return str(value[1])
        except (AttributeError, KeyError, TypeError):
            pass
        return str(repository)

    @staticmethod
    def _repository_color(repository: str, fallback: str) -> str:
        if not repository:
            return fallback
        try:
            from thlib.environment import env_tactic
            value = (env_tactic.get_base_dir(repository) or {}).get("value") or ()
            color = value[2] if len(value) > 2 else None
            if isinstance(color, str) and color:
                return color if color.startswith("#") else f"#{color}"
            if isinstance(color, (list, tuple)) and len(color) >= 3:
                return "#{:02x}{:02x}{:02x}".format(
                    *[max(0, min(255, int(channel))) for channel in color[:3]]
                )
        except (AttributeError, KeyError, TypeError, ValueError):
            pass
        return fallback

    @classmethod
    def _root_preview_candidates(cls, sobject) -> list:
        result = []
        for process_name in ("icon", "publish", "attachment"):
            process = (sobject.get_all_processes() or {}).get(process_name)
            if not process:
                continue
            for context in (process.get_contexts() or {}).values():
                snapshots = list((context.get_versionless() or {}).values())
                snapshots.extend((context.get_versions() or {}).values())
                for snapshot in snapshots:
                    result.extend(
                        cls._snapshot_preview_candidates(snapshot)
                    )
        return result

    def _root_preview(self, sobject) -> str:
        for candidate in self._root_preview_candidates(sobject):
            preview = self._preview_url(candidate)
            if preview:
                return preview
        return ""

    @staticmethod
    def _progress_items(sobject, stype) -> list[dict]:
        try:
            pipeline = (stype.get_pipeline() or {}).get(sobject.get_pipeline_code())
            progress_processes = pipeline.get_processes_info_by_type("progress") if pipeline else []
        except (AttributeError, KeyError, TypeError):
            return []
        items = []
        for process in progress_processes or []:
            name = process.get("name")
            if not name:
                continue
            approved = sobject.get_progress_count(name, "approved_count") or 0
            total = sobject.get_progress_count(name, "total_count") or 0
            color = stype.get_stype_color(fmt="hex") or "#607d8b"
            try:
                workflow = (pipeline.get_pipeline_process(name) or {}).get("workflow") or {}
                progress_stype = stype.get_project().get_search_type(workflow.get("search_type"))
                color = progress_stype.get_stype_color(fmt="hex") or color
            except (AttributeError, KeyError, TypeError):
                pass
            items.append({
                "name": str(name),
                "label": f"{approved} / {total}",
                "color": str(color),
            })
        return items

    @staticmethod
    def _needs_sync(sobject) -> bool:
        try:
            return bool(sobject.is_snapshots_need_update())
        except (AttributeError, KeyError, TypeError):
            return False

    @staticmethod
    def _watch_state(sobject) -> str:
        try:
            from thlib.environment import env_inst
            project = sobject.get_project()
            project_code = project.get_code() if project else ""
            watch_ui = env_inst.watch_folders.get(project_code)
            watch = watch_ui.get_watch_dict_by_skey(sobject.get_search_key()) if watch_ui else None
            if not watch:
                watch = _watch_folder_record(project, sobject.get_search_key())
            if not watch:
                return "none"
            return "enabled" if watch.get("status") else "disabled"
        except (AttributeError, KeyError, TypeError):
            return "none"
