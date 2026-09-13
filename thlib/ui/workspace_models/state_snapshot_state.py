"""Workspace state: snapshot state."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .records import RecordListModel
from .results import WorkspaceItemModel
from .watch_folders import _watch_folder_record


class SnapshotStateMixin:
    def _publish_snapshot_presentation(self) -> None:
        if not getattr(self, "_snapshot_presentation_visible", True):
            return
        self.snapshot_model.replace(self._snapshot_records)
        self.snapshot_preview_model.replace(
            self._snapshot_preview_records
        )
        self.snapshot_file_model.replace(
            self._snapshot_file_records_cache
        )

    @Slot(bool)
    def set_snapshot_presentation_visible(self, value: bool) -> None:
        value = bool(value)
        if value == getattr(
            self, "_snapshot_presentation_visible", True
        ):
            return
        if not value:
            self._snapshot_records = self.snapshot_model.records()
            self._snapshot_preview_records = (
                self.snapshot_preview_model.records()
            )
            self._snapshot_file_records_cache = (
                self.snapshot_file_model.records()
            )
        self._snapshot_presentation_visible = value
        if value:
            self._publish_snapshot_presentation()

    @staticmethod
    def _object_code(tactic_object) -> str:
        try:
            return str(tactic_object.get_code() or "")
        except (AttributeError, KeyError, TypeError):
            return ""

    def _snapshot_preview_items(self, snapshot) -> list[dict]:
        return self._preview_helper._snapshot_preview_items(snapshot)

    @staticmethod
    def _snapshot_file_records(snapshot) -> list[dict]:
        return WorkspaceItemModel._snapshot_file_records(snapshot)

    def replace_snapshot_nodes(
        self, snapshot_nodes, priority_preview_nodes=None,
    ) -> None:
        records = []
        for index, node in enumerate(snapshot_nodes or []):
            source = node.source
            records.append({
                "nodeId": node.node_id,
                "searchKey": node.search_key,
                "title": node.title,
                "path": node.file_path or node.subtitle,
                "version": node.version,
                "revision": node.revision,
                "context": node.context,
                "kind": "snapshot",
                "selected": index == 0,
                "previewUrl": node.preview_url,
                "accent": node.accent,
                "fileExists": node.file_exists,
                "isLatest": node.is_latest,
                "repository": node.repository,
                "author": node.author,
                "timestamp": node.timestamp,
                "previewItems": (
                    self._snapshot_preview_items(source) if source else []
                ),
                "files": (
                    self._snapshot_file_records(source) if source else []
                ),
            })
        self._snapshot_records = records
        self._build_snapshot_browser_models(
            snapshot_nodes, priority_preview_nodes
        )

    def _preview_records_for_nodes(self, snapshot_nodes, token_prefix="preview"):
        records = []
        seen_snapshots = set()
        seen_files = set()
        for snapshot_index, node in enumerate(snapshot_nodes or []):
            snapshot = node.source
            if not snapshot:
                continue
            snapshot_code = self._object_code(snapshot)
            if snapshot_code and snapshot_code in seen_snapshots:
                continue
            if snapshot_code:
                seen_snapshots.add(snapshot_code)
            try:
                grouped = snapshot.get_files_objects(group_by="type") or {}
                preview_objects = list(
                    snapshot.get_previewable_files_objects() or []
                )
            except (AttributeError, KeyError, TypeError):
                grouped, preview_objects = {}, []
            if not preview_objects:
                preview_objects = list(grouped.get("web") or [])
            for preview_index, file_object in enumerate(preview_objects):
                file_code = self._object_code(file_object)
                if file_code and file_code in seen_files:
                    continue
                if file_code:
                    seen_files.add(file_code)
                token = "{}:{}:{}".format(
                    token_prefix, snapshot_index, preview_index
                )
                self._snapshot_file_objects[token] = file_object
                candidate = file_object
                try:
                    candidate = file_object.get_web_preview() or file_object
                except (AttributeError, KeyError, TypeError):
                    pass
                url = self._preview_helper._preview_url(candidate)
                if not url:
                    try:
                        url = self._preview_helper._preview_url(
                            file_object.get_icon_preview()
                        )
                    except (AttributeError, KeyError, TypeError):
                        url = ""
                if not url:
                    continue
                try:
                    title = str(
                        file_object.get_filename_with_ext() or "Preview"
                    )
                    kind = str(file_object.get_type() or "preview")
                except (AttributeError, KeyError, TypeError):
                    title, kind = "Preview", "preview"
                records.append({
                    "token": token,
                    "title": title,
                    "url": url,
                    "kind": kind,
                    "snapshotNodeId": node.node_id,
                })
        return records

    def _build_snapshot_browser_models(
        self, snapshot_nodes, priority_preview_nodes=None,
    ) -> None:
        preview_records = []
        file_records = []
        self._snapshot_file_objects.clear()
        preview_types = {"icon", "playblast", "web"}
        seen_snapshot_codes = set()

        for snapshot_index, node in enumerate(snapshot_nodes or []):
            snapshot = node.source
            if not snapshot:
                continue
            snapshot_code = self._object_code(snapshot)
            if snapshot_code and snapshot_code in seen_snapshot_codes:
                continue
            if snapshot_code:
                seen_snapshot_codes.add(snapshot_code)
            info = snapshot.get_snapshot() or {}
            snapshot_label = "Snapshot ({0}), Version: {1}".format(
                info.get("id") or "", info.get("version") or "",
            )
            file_records.append({
                "rowType": "snapshot", "token": "", "title": snapshot_label,
                "fileType": "", "size": "", "path": "",
                "repository": str(info.get("repo") or ""), "baseType": "",
                "depth": 0, "exists": True, "previewType": False,
                "snapshotNodeId": node.node_id, "version": node.version,
                "checking": False, "matchesRemote": True,
            })

            try:
                grouped = snapshot.get_files_objects(group_by="type") or {}
            except (AttributeError, KeyError, TypeError):
                grouped = {}

            seen_file_codes = set()
            for file_type, file_objects in grouped.items():
                file_type = str(file_type)
                unique_files = []
                for file_object in file_objects or []:
                    file_code = self._object_code(file_object)
                    if file_code and file_code in seen_file_codes:
                        continue
                    if file_code:
                        seen_file_codes.add(file_code)
                    unique_files.append(file_object)
                if not unique_files:
                    continue
                file_records.append({
                    "rowType": "type", "token": "", "title": file_type,
                    "fileType": file_type, "size": "", "path": "",
                    "repository": str(info.get("repo") or ""), "baseType": "",
                    "depth": 1, "exists": True,
                    "previewType": file_type in preview_types,
                    "snapshotNodeId": node.node_id, "version": node.version,
                    "checking": False, "matchesRemote": True,
                })
                for file_index, file_object in enumerate(unique_files):
                    token = f"{snapshot_index}:{file_type}:{file_index}"
                    self._snapshot_file_objects[token] = file_object
                    try:
                        title = str(file_object.get_filename_with_ext() or "")
                    except (AttributeError, KeyError, TypeError):
                        title = ""
                    try:
                        path = str(file_object.get_abs_path() or file_object.get_full_abs_path() or "")
                    except (AttributeError, KeyError, TypeError):
                        path = ""
                    try:
                        size = WorkspaceItemModel._pretty_size(file_object.get_file_size())
                    except (AttributeError, KeyError, TypeError, OSError):
                        size = ""
                    try:
                        base_type = str(file_object.get_base_type() or "")
                    except (AttributeError, KeyError, TypeError):
                        base_type = ""
                    file_records.append({
                        "rowType": "file", "token": token, "title": title,
                        "fileType": file_type, "size": size, "path": path,
                        "repository": str(info.get("repo") or ""),
                        "baseType": base_type, "depth": 2, "exists": True,
                        "previewType": file_type in preview_types,
                        "snapshotNodeId": node.node_id, "version": node.version,
                        "checking": True, "matchesRemote": True,
                    })
                    try:
                        meta = file_object.get_meta_file_object()
                        meta_names = meta.get_all_files_list(filenames=True) if meta else []
                    except (AttributeError, KeyError, TypeError):
                        meta_names = []
                    if len(meta_names) > 1:
                        for meta_name in meta_names:
                            file_records.append({
                                "rowType": "file", "token": token,
                                "title": str(meta_name), "fileType": file_type,
                                "size": "", "path": path,
                                "repository": str(info.get("repo") or ""),
                                "baseType": base_type, "depth": 3,
                                "exists": True,
                                "previewType": file_type in preview_types,
                                "snapshotNodeId": node.node_id,
                                "version": node.version,
                                "checking": True, "matchesRemote": True,
                            })

        priority_records = self._preview_records_for_nodes(
            priority_preview_nodes, "priority-preview"
        )
        preview_records.extend(
            self._preview_records_for_nodes(snapshot_nodes)
        )
        if priority_records:
            priority_urls = {record["url"] for record in priority_records}
            preview_records = priority_records + [
                record for record in preview_records
                if record["url"] not in priority_urls
            ]

        self._snapshot_preview_records = preview_records
        self._snapshot_file_records_cache = file_records
        self._publish_snapshot_presentation()

    def localize_preview(
        self,
        local_path: str,
        pending_paths: dict[str, str] | None = None,
    ) -> None:
        local_path = str(Path(local_path).resolve())
        ready_url = (
            QUrl.fromLocalFile(local_path).toString()
            + f"?ready={int(time.time() * 1000)}"
        )
        all_pending = dict(pending_paths or {})
        all_pending.update(self._preview_helper._pending_preview_paths)
        for record in self._snapshot_preview_records:
            pending = all_pending.get(
                str(record.get("url") or "")
            )
            if pending and str(Path(pending).resolve()) == local_path:
                record["url"] = ready_url
        for record in self._snapshot_records:
            pending = all_pending.get(str(record.get("previewUrl") or ""))
            if pending and str(Path(pending).resolve()) == local_path:
                record["previewUrl"] = ready_url
            items = list(record.get("previewItems") or [])
            items_changed = False
            for item in items:
                pending = all_pending.get(str(item.get("url") or ""))
                if pending and str(Path(pending).resolve()) == local_path:
                    item["url"] = ready_url
                    items_changed = True
            if items_changed:
                record["previewItems"] = items
        self._publish_snapshot_presentation()
        self._preview_helper._pending_preview_paths = {
            token: path
            for token, path in self._preview_helper._pending_preview_paths.items()
            if str(Path(path).resolve()) != local_path
        }

    def fail_preview(self, task_id: str) -> None:
        token = f"pending-preview:{task_id}"
        for record in self._snapshot_preview_records:
            if record.get("url") != token:
                continue
            record["url"] = ""
        self._publish_snapshot_presentation()
        self._preview_helper._pending_preview_paths.pop(token, None)

    def snapshot_file_for(self, token: str):
        return self._snapshot_file_objects.get(token)

    def update_snapshot_file_status(
        self,
        token: str,
        exists: bool,
        matches_remote: bool,
    ) -> None:
        for record in self._snapshot_file_records_cache:
            if record.get("token") != token:
                continue
            record["exists"] = bool(exists)
            record["checking"] = False
            record["matchesRemote"] = bool(matches_remote)
        self._publish_snapshot_presentation()
