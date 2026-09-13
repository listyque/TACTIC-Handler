"""Application controller: item editing."""

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

class ItemEditingMixin:
    @staticmethod
    def _editable_node_values(node) -> dict:
        """Return scalar DB values for roots and dynamically loaded children."""
        values = dict(node.values or {})
        if node.source:
            try:
                source_info = node.source.get_info() or {}
            except (AttributeError, KeyError, TypeError):
                source_info = getattr(node.source, "info", {}) or {}
            for key, value in dict(source_info).items():
                if (
                    not str(key).startswith("__")
                    and isinstance(value, (str, int, float, bool, type(None)))
                ):
                    values[str(key)] = value
        return values

    @classmethod
    def _editable_columns_for_node(cls, node) -> list[str]:
        values = cls._editable_node_values(node)
        schema_columns = {}
        if node.source:
            try:
                stype = node.source.get_stype()
                schema_columns = dict(stype.get_columns_info() or {})
            except (AttributeError, KeyError, TypeError, ValueError):
                schema_columns = {}
        hidden = {
            "id", "code", "search_type", "project_code", "timestamp",
            "last_updated", "login", "__search_key__", "__search_type__",
        }
        candidates = schema_columns.keys() if schema_columns else values.keys()
        return sorted(
            str(column)
            for column in candidates
            if (
                column not in hidden
                and not str(column).startswith("__")
                and isinstance(
                    values.get(column),
                    (str, int, float, bool, type(None)),
                )
            )
        )

    @Slot(str, result="QVariantList")
    def editable_result_field_records(self, node_id: str) -> list[dict]:
        node = self.workspace_model.node_for(str(node_id or ""))
        if not node:
            return []
        values = self._editable_node_values(node)
        column_info = {}
        if node.source:
            try:
                stype = node.source.get_stype()
                column_info = dict(stype.get_columns_info() or {})
            except (AttributeError, KeyError, TypeError, ValueError):
                column_info = {}
        return [
            {
                "fieldName": column,
                "fieldLabel": column.replace("_", " ").title(),
                "fieldType": str(
                    (column_info.get(column) or {}).get("data_type") or "text"
                ),
                "fieldValue": "" if values.get(column) is None
                    else str(values.get(column)),
            }
            for column in self._editable_columns_for_node(node)
        ]



    @Slot(str, str)
    def update_selected_items(self, column: str, value: str) -> None:
        """Apply one changed column to every compatible selected item."""
        column = str(column or "").strip()
        if not column or column not in self.selected_result_fields:
            self._notify("Select an editable database column")
            return
        tab = self._current_tab()
        nodes = [
            self.workspace_model.node_for(node_id)
            for node_id in (tab.selected_node_ids if tab else [])
        ]
        nodes = [node for node in nodes if node and node.source]
        if not nodes:
            self._notify("No editable items are selected")
            return

        sample = (nodes[0].values or {}).get(column)
        converted: object = value
        try:
            if isinstance(sample, bool):
                converted = value.strip().lower() in {"1", "true", "yes", "on"}
            elif isinstance(sample, int) and not isinstance(sample, bool):
                converted = int(value)
            elif isinstance(sample, float):
                converted = float(value)
            elif sample is None and not value:
                converted = None
        except ValueError:
            self._notify(f"Invalid value for {column}")
            return

        search_keys = [node.source.get_search_key() for node in nodes]
        project_code = self._current_project_code
        request_id = uuid.uuid4().hex
        self._selected_update_started_at = time.perf_counter()
        self._set_loading(True, f"Updating {len(search_keys)} selected item(s)")
        data = {
            search_key: {column: converted}
            for search_key in search_keys
        }
        self._start_selected_update(
            data, project_code, request_id, len(search_keys), column
        )

    def _start_selected_update(
        self, data: dict, project_code: str, request_id: str,
        count: int, label: str,
    ) -> None:
        targets = [{
            "search_key": str(search_key),
            "search_type": str(search_key).removeprefix("skey://").split("?", 1)[0],
        } for search_key in data]
        event = (
            "task.update"
            if targets and all(
                target["search_type"] == "sthpw/task" for target in targets
            )
            else "object.update"
        )
        context = {
            "project_code": project_code,
            "targets": targets,
            "values_by_search_key": {
                str(key): dict(value) for key, value in data.items()
            },
        }

        def start(success=True, error=""):
            if not success:
                self._selected_update_triggers.pop(request_id, None)
                self._set_loading(False, "Update blocked by script trigger")
                return
            self._start_selected_update_worker(
                data, project_code, request_id, count, label
            )

        if not hasattr(self, "_selected_update_triggers"):
            self._selected_update_triggers = {}
        self._selected_update_triggers[request_id] = (event, context)
        triggers = getattr(self, "_script_triggers", None)
        if triggers is None:
            start()
        else:
            triggers.run_before(event, context, start)

    def _start_selected_update_worker(
        self, data: dict, project_code: str, request_id: str,
        count: int, label: str,
    ) -> None:
        try:
            import thlib.tactic_classes as tc
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()

            def update_multiple():
                server = tc.server_start(project=project_code)
                return (server.update_multiple(
                    data=data,
                    triggers=True,
                ),)

            worker = env_inst.server_pool.add_task(update_multiple)
            worker.add_result_data((request_id, count, label))
            worker.result.connect(self._selected_update_result)
            worker.error.connect(self._selected_update_error)
            worker.start()
        except Exception as error:
            self._set_loading(False, f"Update failed · {error}")
            self._notify(str(error))

    @Slot(str, "QVariantMap")
    def update_selected_item_fields(self, node_id: str, changes: dict) -> None:
        """Persist staged table edits for one selected result in one request."""
        node = self.workspace_model.node_for(str(node_id or ""))
        if not node or not node.source:
            self._notify("The selected item is no longer available")
            return

        allowed = set(self._editable_columns_for_node(node))
        original = self._editable_node_values(node)
        converted_changes: dict[str, object] = {}
        for raw_column, raw_value in dict(changes or {}).items():
            column = str(raw_column or "").strip()
            if column not in allowed:
                continue
            value = "" if raw_value is None else str(raw_value)
            sample = original.get(column)
            try:
                if isinstance(sample, bool):
                    converted: object = value.strip().lower() in {
                        "1", "true", "yes", "on"
                    }
                elif isinstance(sample, int) and not isinstance(sample, bool):
                    converted = int(value)
                elif isinstance(sample, float):
                    converted = float(value)
                elif sample is None and not value:
                    converted = None
                else:
                    converted = value
            except ValueError:
                self._notify(f"Invalid value for {column}")
                return
            converted_changes[column] = converted

        if not converted_changes:
            self._notify("No database changes to save")
            return

        search_key = node.source.get_search_key()
        project_code = self._current_project_code
        request_id = uuid.uuid4().hex
        field_count = len(converted_changes)
        self._selected_update_started_at = time.perf_counter()
        self._set_loading(True, f"Saving {field_count} field(s)")
        self._start_selected_update(
            {search_key: converted_changes},
            project_code,
            request_id,
            1,
            f"{field_count} field(s)",
        )

    @Slot(object)
    def _selected_update_result(self, result) -> None:
        server_result, metadata = result
        request_id, count, column = metadata
        self._set_loading(
            False,
            f"Updated {count} item(s) · {column} · "
            f"{self._transaction_metrics(self._selected_update_started_at, server_result)}",
        )
        self._notify(f"{column} updated for {count} item(s)")
        trigger = self._selected_update_triggers.pop(request_id, None)
        triggers = getattr(self, "_script_triggers", None)
        if trigger and triggers is not None:
            triggers.run_after(*trigger)
        self.refresh_current()

    @Slot(object)
    def _selected_update_error(self, error) -> None:
        payload, worker = error
        metadata = worker.get_result_data()
        if isinstance(metadata, (tuple, list)) and metadata:
            self._selected_update_triggers.pop(str(metadata[0]), None)
        self._report_error_payload(payload, "items/mass_edit", worker)
        message = str(payload.get("exception") or error)
        self._set_loading(
            False,
            "Update failed · "
            f"{self._transaction_metrics(self._selected_update_started_at)} · {message}",
        )
        self._notify(message)
