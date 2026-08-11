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
    QSettings,
    Qt,
    QTimer,
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
                from thlib.environment import cfg_controls
                import thlib.global_functions as gf
                checkout_http = int(
                    gf.get_value_from_config(
                        cfg_controls.get_checkin(), "checkoutMethodComboBox",
                    ) or 0
                ) != 0
                if checkout_http:
                    from thlib.environment import env_inst
                    sync_item = env_inst.ui_repo_sync_queue.schedule_file_object(file_object)
                    sync_item.downloaded.connect(file_object.open_file)
                    sync_item.download()
                else:
                    file_object.open_file()
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
                # This is the original schema-driven TACTIC EditWdg path,
                # not the generic placeholder previously opened here.
                from thlib.ui_classes.ui_addsobject_classes import (
                    Ui_addTacticSobjectWidget,
                )
                sobject = self.workspace_state._selected_sobject
                stype = sobject.get_stype() if sobject else None
                if not stype:
                    self._notify("The current search type is unavailable")
                    return
                tab = self._current_tab()
                editor = Ui_addTacticSobjectWidget(
                    stype=stype,
                    view="edit",
                    tab_name=tab.title if tab else None,
                    search_key=file_object.get_search_key(),
                )
                editor.setWindowTitle(
                    "Editing file info for {0}".format(
                        sobject.get_title() if sobject else "snapshot"
                    )
                )
                editor.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
                self._snapshot_editors.append(editor)

                def release_editor(*_args, dialog=editor):
                    try:
                        self._snapshot_editors.remove(dialog)
                    except ValueError:
                        pass

                editor.destroyed.connect(release_editor)
                editor.show()
            elif command == "delete":
                import thlib.tactic_classes as tc
                delete_confirm = tc.sobject_delete_confirm([file_object])
                if delete_confirm:
                    from thlib.environment import env_inst
                    if env_inst.server_pool.is_stopped:
                        env_inst.server_pool.start()
                    worker = env_inst.server_pool.add_task(
                        tc.delete_sobjects,
                        [file_object.get_search_key()],
                        delete_confirm,
                    )
                    worker.result.connect(self._snapshot_file_deleted)
                    worker.error.connect(self._snapshot_file_delete_failed)
                    self._set_loading(True, "Deleting snapshot file")
                    worker.start()
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

    @Slot(object)
    def _snapshot_file_deleted(self, _result) -> None:
        self._set_loading(False, "Snapshot file deleted")
        self._notify("Snapshot file deleted")
        self.refresh_snapshot_browser()

    @Slot(object)
    def _snapshot_file_delete_failed(self, error) -> None:
        payload, worker = error
        self._report_error_payload(
            payload,
            "snapshot_browser/delete_file",
            worker,
        )
        message = str(payload.get("exception") or error)
        self._set_loading(False, f"Snapshot file deletion failed · {message}")
        self._notify(message)
