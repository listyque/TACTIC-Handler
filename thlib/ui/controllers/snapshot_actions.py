"""Application controller: snapshot actions."""

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

class SnapshotActionsMixin:
    @Slot(str, str)
    def invoke_snapshot_file_action(self, command: str, token: str) -> None:
        if self.debug_log:
            self.debug_log.log(
                "LOG",
                f"Snapshot browser file action: {command}",
                group="snapshot_browser/file",
                source="ApplicationController",
                command=command,
                details=f"token={token}",
                caller=2,
            )
        file_object = self.workspace_state.snapshot_file_for(token)
        if not file_object:
            self._notify("Snapshot file is no longer available")
            return
        try:
            if command == "open":
                self.open_file_object(file_object)
            elif command == "folder":
                meta = file_object.get_meta_file_object() if file_object.is_meta_file_obj() else None
                (meta or file_object).open_folder()
            elif command in {"copy_path", "copy_web_path"}:
                if (
                    command == "copy_path"
                    and ":preview:" in token
                    and file_object.is_meta_file_obj()
                ):
                    meta = file_object.get_meta_file_object()
                    copied_path = meta.get_all_files_list(True)
                else:
                    getter = (
                        "get_full_web_path"
                        if command == "copy_web_path"
                        else "get_full_abs_path"
                    )
                    copied_path = getattr(file_object, getter)()
                QGuiApplication.clipboard().setText(str(copied_path))
                self._notify("Path copied")
            elif command == "copy_image":
                from thlib.environment import env_inst
                if env_inst.local_pool.is_stopped:
                    env_inst.local_pool.start()
                worker = env_inst.local_pool.add_task(
                    self._load_clipboard_image,
                    str(file_object.get_full_abs_path()),
                )
                worker.result.connect(self._snapshot_image_loaded)
                worker.error.connect(
                    lambda error: self._report_error_payload(
                        error[0],
                        "snapshot_browser/copy_image",
                        error[1],
                    )
                )
                worker.start()
            elif command == "edit":
                # The selected TACTIC File is the edit target.  Its owning
                # business sObject supplies the project-aware editor schema,
                # matching the original Snapshot Browser workflow.
                owner = (
                    getattr(self, "_task_snapshot_source", None)
                    or self.workspace_state._selected_sobject
                )
                if owner is None:
                    self._notify("The snapshot owner is no longer available")
                    return
                stype = owner.get_stype()
                if not stype:
                    self._notify("The current search type is unavailable")
                    return
                self._sobject_editor_request = {
                    "mode": "edit",
                    "stype": stype,
                    "sobject": file_object,
                    "parent_sobject": None,
                    "_prepared": True,
                }
                self.open_window("add_sobject")
            elif command == "delete":
                delete_controller = getattr(self, "sobject_delete", None)
                if delete_controller is None:
                    self._notify("Delete SObject editor is unavailable")
                    return
                delete_controller.begin([file_object], "snapshot_file")
        except Exception as error:
            if self.debug_log:
                self.debug_log.raise_error(
                    error,
                    group="snapshot_browser/action",
                )
            self._notify(str(error))

    @staticmethod
    def _load_clipboard_image(path: str):
        return (QImage(path),)

    @Slot(object)
    def _snapshot_image_loaded(self, result) -> None:
        image = result[0] if isinstance(result, tuple) else result
        if not image or image.isNull():
            self._notify("The selected file is not an image")
            return
        QGuiApplication.clipboard().setImage(image)
        self._notify("Image copied")
