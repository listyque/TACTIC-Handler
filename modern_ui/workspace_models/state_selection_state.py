"""Workspace state: selection state."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, QSettings, Qt, QUrl, Slot

from .records import RecordListModel
from .results import WorkspaceItemModel
from .watch_folders import _watch_folder_record


class SelectionStateMixin:
    def load_sobject(
        self,
        sobject,
        tasks,
        notes,
        snapshot_nodes=None,
        selected_node=None,
        notes_process=None,
    ) -> None:
        """Populate dependent docks from the selected SObject."""
        info = sobject.get_info() or {}
        self._selected_sobject = sobject
        self._task_sobjects = list(tasks)
        self._note_sobjects = list(notes or [])
        self._notes_process = notes_process
        self._notes_loaded = True
        self._selected_title = str(sobject.get_title() or sobject.get_code() or "")
        self.selection_changed.emit()
        target = selected_node.source if selected_node else sobject
        target_kind = selected_node.node_type if selected_node else "sobject"
        target_title = selected_node.title if selected_node else self._selected_title
        self.set_description_target(target, target_kind, target_title)
        if snapshot_nodes is not None:
            self.replace_snapshot_nodes(snapshot_nodes)
        else:
            snapshots = info.get("__snapshots__") or []
            self.snapshot_model.replace([
                {
                    "nodeId": "",
                    "searchKey": snapshot.get("__search_key__") or "",
                    "title": snapshot.get("label") or snapshot.get("code") or "",
                    "path": snapshot.get("description") or "",
                    "version": "v{:03d}".format(int(snapshot.get("version") or 0)),
                    "revision": "",
                    "context": snapshot.get("context") or "",
                    "kind": snapshot.get("snapshot_type") or "",
                    "selected": index == 0,
                    "previewUrl": "",
                    "accent": "#607d8b",
                    "fileExists": False,
                    "isLatest": False,
                    "repository": snapshot.get("repo") or "",
                    "author": snapshot.get("login") or "",
                    "timestamp": str(snapshot.get("timestamp") or ""),
                    "previewItems": [],
                    "files": [],
                }
                for index, snapshot in enumerate(snapshots)
            ])
            self.snapshot_preview_model.clear()
            self.snapshot_file_model.clear()
            self._snapshot_file_objects.clear()
        self.replace_tasks(tasks)

    def replace_tasks(self, tasks) -> None:
        self._task_sobjects = list(tasks or [])
        task_records = []
        for task in self._task_sobjects:
            task_info = task.get_info() or {}
            progress_value = (
                task_info.get("progress")
                or task_info.get("completion")
                or 0
            )
            try:
                progress_value = int(float(str(progress_value).rstrip("%")))
            except (TypeError, ValueError):
                progress_value = 0
            task_records.append({
                "taskId": str(task_info.get("code") or task_info.get("id") or ""),
                "searchKey": str(task.get_search_key() or ""),
                "process": task_info.get("process") or "",
                "status": task_info.get("status") or "",
                "user": task_info.get("assigned") or task_info.get("login") or "",
                "start": str(task_info.get("bid_start_date") or ""),
                "end": str(task_info.get("bid_end_date") or ""),
                "due": str(task_info.get("bid_end_date") or task_info.get("end_date") or ""),
                "progress": progress_value,
                "description": str(task_info.get("description") or ""),
                "color": "#607d8b",
                "checked": False,
                "notes": sum(int(value or 0) for value in (task.get_notes_count() or {}).values()),
            })
        self.task_model.replace(task_records)
        self.task_status_model.replace([
            {"label": status}
            for status in sorted({record["status"] for record in task_records if record["status"]})
        ])

    def clear_selection(self) -> None:
        self._selected_title = ""
        self._selected_sobject = None
        self._task_sobjects = []
        self._note_sobjects = []
        self._notes_process = None
        self._notes_loaded = False
        self.selection_changed.emit()
        self._description_pinned = False
        self.set_description_target(None, "", "")
        self.snapshot_model.clear()
        self.snapshot_preview_model.clear()
        self.snapshot_file_model.clear()
        self._snapshot_file_objects.clear()
        self.task_model.clear()
        self.note_model.clear()

    def queue_dropped_files(self, paths: list[str], process: str) -> None:
        records = list(self.drop_model._records)
        known = {str(record.get("path") or "") for record in records}
        for path_value in paths:
            path = Path(path_value)
            normalized = str(path)
            if normalized in known:
                continue
            try:
                size = WorkspaceItemModel._pretty_size(path.stat().st_size)
            except OSError:
                size = ""
            records.append({
                "title": path.name,
                "path": normalized,
                "size": size,
                "process": process,
                "checked": True,
                "status": "Queued",
            })
            known.add(normalized)
        self.drop_model.replace(records)
