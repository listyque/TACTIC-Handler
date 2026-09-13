"""Workspace state: project state."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .records import RecordListModel
from .results import WorkspaceItemModel
from .watch_folders import _watch_folder_record, _watch_folder_settings


_STYPE_NOT_LOADED = object()


class ProjectStateMixin:
    def load_project(self, project) -> None:
        """Fill project-dependent selectors from runtime data."""
        from thlib.environment import env_inst, env_server
        self._project = project
        self._loaded_stype = _STYPE_NOT_LOADED
        stypes = project.get_stypes() or {}
        self.search_type_model.replace([
            {"label": code} for code in sorted(stypes)
        ])
        self.database_table_model.replace([
            {"label": stype.info.get("table_name") or code}
            for code, stype in sorted(stypes.items())
        ])
        self.process_tabs_model.replace([
            {"label": stype.get_pretty_name()} for stype in stypes.values()
        ])
        self.user_model.replace([
            {"label": login.get_display_name() or login.get_login()}
            for login in (env_inst.logins or {}).values()
        ])
        self.server_preset_model.replace([
            {"label": preset}
            for preset in env_server.get_server_presets().get("presets_list", [])
        ])
        watch_settings = _watch_folder_settings(project)
        watch_keys = list(watch_settings.get("assets_skeys") or [])
        def watch_value(name, index, default=""):
            values = list(watch_settings.get(name) or [])
            return values[index] if index < len(values) else default
        self.watch_model.replace([
            {
                "title": str(watch_value("assets_names", index) or search_key),
                "path": str(watch_value("paths", index)),
                "watchEnabled": bool(watch_value("statuses", index, False)),
                "process": str(watch_value("assets_pipelines", index)),
            }
            for index, search_key in enumerate(watch_keys)
        ])

    @Slot(int, bool)
    def toggle_watch_folder(self, row: int, enabled: bool) -> None:
        settings = _watch_folder_settings(self._project)
        statuses = list(settings.get("statuses") or [])
        if not 0 <= row < len(statuses):
            return
        statuses[row] = bool(enabled)
        settings["statuses"] = statuses
        try:
            from thlib.environment import env_write_config
            env_write_config(
                {"watch_folders_dict": settings},
                filename="ui_watch_folder",
                unique_id=(
                    f"ui_main/{self._project.get_type()}/"
                    f"{self._project.get_code()}"
                ),
                long_abs_path=True,
            )
            self.watch_model._records[row]["watchEnabled"] = bool(enabled)
            model_index = self.watch_model.index(row, 0)
            self.watch_model.dataChanged.emit(
                model_index,
                model_index,
                [self.watch_model._role_ids["watchEnabled"]],
            )
        except (AttributeError, KeyError, TypeError, OSError):
            return

    def load_stype(self, stype) -> None:
        if getattr(self, "_loaded_stype", _STYPE_NOT_LOADED) is stype:
            return
        import thlib.tactic_classes as tc

        columns_info = stype.get_columns_info() if stype else {}
        # Preserve native TACTIC schema order. Alphabetic sorting changes the
        # first/default field shown by Advanced Search.
        columns = list((columns_info or {}).keys())
        self.columns_model.replace([
            {"title": column, "checked": True} for column in columns
        ])
        self.filter_column_model.replace([
            {
                "label": column.replace("_", " ").title(),
                "value": column,
                "dataType": stype.get_column_data_type(column),
            }
            for column in columns
        ] + [{
            "label": "**Expression",
            "value": "_expression",
            "dataType": "_expression",
        }])
        self.filter_relation_model.replace([
            {"label": label, "value": relation}
            for label, relation in tc.get_match_list_by_type("all")
        ])
        self._loaded_stype = stype
