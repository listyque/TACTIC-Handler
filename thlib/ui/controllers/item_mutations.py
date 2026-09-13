"""Application controller: item mutations."""

from __future__ import annotations

from collections.abc import Callable
import json
import math
import re
import sys
import time
import traceback
import uuid

from PySide6.QtCore import (
    QDateTime,
    QObject,
    Property,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtGui import QGuiApplication, QImage

from ..menu_schema import MenuRegistry
from ..quick_filters import QuickFilterCatalog
from ..repository_sync import RepositorySyncController
from ..models import NavigationModel, ProjectModel
from ..workspace import (
    DockPanelModel,
    FloatingWindowModel,
    SectionTab,
    SectionTabModel,
    WorkspaceItemModel,
    WorkspaceState,
)
from .types import ActionRegistry, SearchTabSession, SectionSession

class ItemMutationsMixin:
    def _start_item_mutation(
        self,
        title: str,
        callback,
        metadata: tuple,
        result_handler,
    ) -> None:
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        started_at = time.perf_counter()
        self._set_loading(True, title)
        worker = env_inst.server_pool.add_task(callback)
        worker.add_result_data((*metadata, started_at))
        worker.result.connect(result_handler)
        worker.error.connect(self._item_mutation_error)
        worker.start()

    @Slot(str, str)
    def _repository_file_ready(self, task_id: str, local_path: str) -> None:
        token = f"pending-preview:{task_id}"
        pending_sources = (
            self.project_model._pending_preview_paths,
            self.workspace_model._pending_preview_paths,
            self.versions_model._pending_preview_paths,
            self.workspace_state._preview_helper._pending_preview_paths,
        )
        # A full repository sync emits this signal for every downloaded file.
        # Only preview tasks owned by these models require localization; the
        # early O(1) lookup prevents thousands of unrelated model scans.
        if not any(token in pending for pending in pending_sources):
            return
        pending_paths = dict(self.workspace_model._pending_preview_paths)
        pending_paths.update(self.versions_model._pending_preview_paths)
        self.project_model.localize_preview(local_path)
        self.workspace_model.localize_preview(local_path)
        self.versions_model.localize_preview(local_path)
        self.workspace_state.localize_preview(local_path, pending_paths)

    @Slot(str)
    def _repository_preview_failed(self, task_id: str) -> None:
        self.project_model.fail_preview(task_id)
        self.workspace_model.fail_preview(task_id)
        self.versions_model.fail_preview(task_id)
        self.workspace_state.fail_preview(task_id)

    @Slot(str)
    def _save_description_async(self, value: str) -> None:
        target = self.workspace_state._description_target
        search_key = self.workspace_state._description_target_key
        if not target or not search_key:
            return

        def save_description():
            import thlib.tactic_classes as tc
            return (tc.update_description(search_key, value),)

        try:
            self._start_item_mutation(
                "Saving description",
                save_description,
                ("description", search_key, value),
                self._item_mutation_result,
            )
        except Exception as error:
            self._notify(str(error))

    @Slot(str)
    def _add_note_async(self, value: str) -> None:
        sobject = self.workspace_state._selected_sobject
        if not sobject:
            return
        search_key = sobject.get_search_key()

        def add_note():
            import thlib.tactic_classes as tc
            from thlib.environment import env_server
            result = tc.add_note(
                search_key, "publish", "publish", value, env_server.get_user()
            )
            return ((result, env_server.get_user()),)

        try:
            self._start_item_mutation(
                "Adding note",
                add_note,
                ("note", search_key, value),
                self._item_mutation_result,
            )
        except Exception as error:
            self._notify(str(error))

    @Slot(int, str)
    def _set_task_status_async(self, row: int, status: str) -> None:
        if not 0 <= row < len(self.workspace_state._task_sobjects):
            return
        task = self.workspace_state._task_sobjects[row]

        def set_status():
            task.set_value("status", status)
            return (task.commit(),)

        try:
            self._start_item_mutation(
                "Updating task status",
                set_status,
                ("task_status", row, status),
                self._item_mutation_result,
            )
        except Exception as error:
            self._notify(str(error))

    @Slot(object)
    def _item_mutation_result(self, result) -> None:
        server_result, metadata = result
        kind, target, value, started_at = metadata
        if kind == "description":
            description_target = self.workspace_state._description_target
            if (
                description_target
                and self.workspace_state._description_target_key == target
            ):
                try:
                    info = (
                        description_target.get_snapshot()
                        if self.workspace_state._description_target_kind
                        == "snapshot"
                        else description_target.get_info()
                    )
                    if info is not None:
                        info["description"] = value
                except (AttributeError, KeyError, TypeError):
                    pass
            self.workspace_model.update_description(target, value)
            self.versions_model.update_description(target, value)
            self.workspace_state.description_save_succeeded(target, value)
        elif kind == "note":
            _note_result, author = server_result
            records = list(self.workspace_state.note_model._records)
            records.append({
                "author": author,
                "time": QDateTime.currentDateTime().toString(Qt.ISODate),
                "body": value,
                "status": "",
                "attachments": 0,
            })
            self.workspace_state.note_model.replace(records)
        elif kind == "task_status":
            self.workspace_state.task_model.set_status(int(target), value)
        elif kind == "unlink":
            self._notify("sObject unlinked")
            self.refresh_current()
        self._set_loading(
            False,
            f"{kind.replace('_', ' ').title()} saved · "
            f"{self._transaction_metrics(started_at, server_result)}",
        )

    @Slot(object)
    def _item_mutation_error(self, error) -> None:
        payload, worker = error
        self._report_error_payload(payload, "items/update", worker)
        metadata = worker.get_result_data() if worker else ()
        started_at = metadata[-1] if metadata else time.perf_counter()
        message = str(payload.get("exception") or error)
        if metadata and metadata[0] == "description":
            self.workspace_state.description_save_failed(
                str(metadata[1]), message
            )
        self._set_loading(
            False,
            f"Item update failed · {self._transaction_metrics(started_at)} · {message}",
        )
        self._notify(message)
