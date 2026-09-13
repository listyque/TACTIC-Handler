"""Workspace state: selection state."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .records import RecordListModel
from .results import WorkspaceItemModel
from .watch_folders import _watch_folder_record


@dataclass(slots=True)
class SelectionProjection:
    """Ready presentation state for the selected object in one search tab."""

    selected_sobject: object
    task_sobjects: list
    note_sobjects: list
    notes_process: object
    notes_loaded: bool
    selected_title: str
    description_state: dict
    snapshot_records: list[dict]
    snapshot_preview_records: list[dict]
    snapshot_file_records: list[dict]
    snapshot_file_objects: dict[str, object]
    task_records: list[dict]
    task_status_records: list[dict]
    note_records: list[dict]


class SelectionStateMixin:
    def _publish_detail_presentation(self) -> None:
        if not getattr(self, "_detail_presentation_visible", True):
            return
        self.task_model.replace(self._task_records_cache)
        self.task_status_model.replace(self._task_status_records_cache)
        self.note_model.replace(self._note_records_cache)

    @Slot(bool)
    def set_detail_presentation_visible(self, value: bool) -> None:
        value = bool(value)
        if value == getattr(
            self, "_detail_presentation_visible", True
        ):
            return
        if not value:
            self._task_records_cache = self.task_model.records()
            self._task_status_records_cache = (
                self.task_status_model.records()
            )
            self._note_records_cache = self.note_model.records()
        self._detail_presentation_visible = value
        if value:
            self._publish_detail_presentation()

    def replace_note_records(self, records) -> None:
        self._note_records_cache = [
            dict(record) for record in (records or [])
        ]
        if getattr(self, "_detail_presentation_visible", True):
            self.note_model.replace(self._note_records_cache)

    def capture_selection_projection(self) -> SelectionProjection | None:
        if self._selected_sobject is None:
            return None
        return SelectionProjection(
            selected_sobject=self._selected_sobject,
            task_sobjects=list(self._task_sobjects),
            note_sobjects=list(self._note_sobjects),
            notes_process=self._notes_process,
            notes_loaded=bool(self._notes_loaded),
            selected_title=self._selected_title,
            description_state={
                "value": self._description,
                "original": self._description_original,
                "editing": self._description_editing,
                "pinned": self._description_pinned,
                "saving": self._description_saving,
                "error": self._description_error,
                "target": self._description_target,
                "targetKey": self._description_target_key,
                "targetKind": self._description_target_kind,
                "targetTitle": self._description_target_title,
            },
            snapshot_records=(
                self.snapshot_model.records()
                if getattr(self, "_snapshot_presentation_visible", True)
                else [dict(record) for record in self._snapshot_records]
            ),
            snapshot_preview_records=(
                self.snapshot_preview_model.records()
                if getattr(self, "_snapshot_presentation_visible", True)
                else [
                    dict(record)
                    for record in self._snapshot_preview_records
                ]
            ),
            snapshot_file_records=(
                self.snapshot_file_model.records()
                if getattr(self, "_snapshot_presentation_visible", True)
                else [
                    dict(record)
                    for record in self._snapshot_file_records_cache
                ]
            ),
            snapshot_file_objects=dict(self._snapshot_file_objects),
            task_records=(
                self.task_model.records()
                if getattr(self, "_detail_presentation_visible", True)
                else [dict(record) for record in self._task_records_cache]
            ),
            task_status_records=(
                self.task_status_model.records()
                if getattr(self, "_detail_presentation_visible", True)
                else [
                    dict(record)
                    for record in self._task_status_records_cache
                ]
            ),
            note_records=(
                self.note_model.records()
                if getattr(self, "_detail_presentation_visible", True)
                else [dict(record) for record in self._note_records_cache]
            ),
        )

    def restore_selection_projection(self, projection) -> bool:
        if not isinstance(projection, SelectionProjection):
            return False
        self._selection_projection_restoring = True
        try:
            self._selected_sobject = projection.selected_sobject
            self._task_sobjects = list(projection.task_sobjects)
            self._note_sobjects = list(projection.note_sobjects)
            self._notes_process = projection.notes_process
            self._notes_loaded = projection.notes_loaded
            self._selected_title = projection.selected_title
            description = projection.description_state
            self._description = str(description.get("value") or "")
            self._description_original = str(
                description.get("original") or ""
            )
            self._description_editing = bool(description.get("editing"))
            self._description_pinned = bool(description.get("pinned"))
            self._description_saving = bool(description.get("saving"))
            self._description_error = str(description.get("error") or "")
            self._description_target = description.get("target")
            self._description_target_key = str(
                description.get("targetKey") or ""
            )
            self._description_target_kind = str(
                description.get("targetKind") or ""
            )
            self._description_target_title = str(
                description.get("targetTitle") or ""
            )
            self._snapshot_records = [
                dict(record) for record in projection.snapshot_records
            ]
            self._snapshot_preview_records = [
                dict(record)
                for record in projection.snapshot_preview_records
            ]
            self._snapshot_file_records_cache = [
                dict(record)
                for record in projection.snapshot_file_records
            ]
            self._snapshot_file_objects = dict(
                projection.snapshot_file_objects
            )
            publish_snapshots = getattr(
                self, "_publish_snapshot_presentation", None
            )
            if callable(publish_snapshots):
                publish_snapshots()
            else:
                self.snapshot_model.replace(self._snapshot_records)
                self.snapshot_preview_model.replace(
                    self._snapshot_preview_records
                )
                self.snapshot_file_model.replace(
                    self._snapshot_file_records_cache
                )
            self._task_records_cache = [
                dict(record) for record in projection.task_records
            ]
            self._task_status_records_cache = [
                dict(record)
                for record in projection.task_status_records
            ]
            self._note_records_cache = [
                dict(record) for record in projection.note_records
            ]
            publish_details = getattr(
                self, "_publish_detail_presentation", None
            )
            if callable(publish_details):
                publish_details()
            else:
                self.task_model.replace(self._task_records_cache)
                self.task_status_model.replace(
                    self._task_status_records_cache
                )
                self.note_model.replace(self._note_records_cache)
        finally:
            self._selection_projection_restoring = False
        self.selection_changed.emit()
        self.description_changed.emit(self._description)
        self.description_editor_changed.emit()
        return True

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
            self._snapshot_records = [
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
            ]
            self._snapshot_preview_records = []
            self._snapshot_file_records_cache = []
            self._snapshot_file_objects.clear()
            self._publish_snapshot_presentation()
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
        self._task_records_cache = task_records
        self._task_status_records_cache = [
            {"label": status}
            for status in sorted({record["status"] for record in task_records if record["status"]})
        ]
        self._publish_detail_presentation()

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
        self._snapshot_records = []
        self._snapshot_preview_records = []
        self._snapshot_file_records_cache = []
        self._snapshot_file_objects.clear()
        self._publish_snapshot_presentation()
        self._task_records_cache = []
        self._task_status_records_cache = []
        self._note_records_cache = []
        self._publish_detail_presentation()

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
