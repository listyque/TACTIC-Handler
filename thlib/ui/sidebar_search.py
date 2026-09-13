"""Saved-search library and modal preview for the sidebar editor."""

from __future__ import annotations

import uuid

from PySide6.QtCore import QCoreApplication, Slot


class SidebarSearchMixin:
    @Slot()
    def refresh_search_presets(self) -> None:
        """Load saved Search Views for the selected server Search Type."""
        selected = self.selectedEntry
        search_type = str(selected.get("searchType") or "").strip()
        context = (self._project_code, search_type)
        current_view = str(selected.get("searchView") or "").strip()
        if not all(context):
            self._search_preset_context = context
            self._replace_search_preset_options([], current_view)
            return
        if context == self._search_preset_context and self._search_preset_options:
            self._ensure_current_search_view(current_view)
            return
        if self._search_preset_worker is not None:
            try:
                self._search_preset_worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        request_id = uuid.uuid4().hex
        self._search_preset_request = request_id
        self._search_preset_context = context
        project_code, search_type = context
        self._replace_search_preset_options([], current_view)

        def operation():
            from .search_presets import query_search_presets

            return (
                request_id,
                context,
                query_search_presets(project_code, search_type),
            )

        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(operation)
            if worker is None:
                return
            self._search_preset_worker = worker
            worker.result.connect(self._search_presets_loaded)
            worker.error.connect(self._search_presets_failed)
            worker.finished.connect(
                lambda target=worker: self._release_search_preset_worker(target)
            )
            worker.start()
            self.stateChanged.emit()
        except Exception as error:
            self._search_preset_worker = None
            self._error = str(error)
            self.stateChanged.emit()

    @Slot(str, str)
    def invalidate_search_presets(
            self, project_code: str = "", search_type: str = "") -> None:
        context = (str(project_code or ""), str(search_type or ""))
        if context != self._search_preset_context:
            return
        self._search_preset_context = ("", "")
        self.refresh_search_presets()

    @Slot(object)
    def _search_presets_loaded(self, payload) -> None:
        request_id, context, presets = payload
        if (
            request_id != self._search_preset_request
            or tuple(context) != self._search_preset_context
        ):
            return
        self._search_preset_worker = None
        current_view = str(self.selectedEntry.get("searchView") or "").strip()
        self._replace_search_preset_options(presets, current_view)

    @Slot(object)
    def _search_presets_failed(self, error) -> None:
        payload, worker = error
        if self._search_preset_worker is not worker:
            return
        self._search_preset_worker = None
        self._error = str(payload.get("exception") or error)
        self.stateChanged.emit()

    def _release_search_preset_worker(self, worker) -> None:
        if self._search_preset_worker is worker:
            self._search_preset_worker = None
            self.stateChanged.emit()

    def _replace_search_preset_options(
            self, presets, current_view: str = "") -> None:
        options = [{
            "value": "",
            "label": QCoreApplication.translate(
                "TacticHandler", "No predefined search"
            ),
        }]
        seen = {""}
        for preset in presets or []:
            value = str(preset.get("view") or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            options.append({
                "value": value,
                "label": str(preset.get("title") or value),
            })
        self._search_preset_options = options
        self._ensure_current_search_view(current_view, emit=False)
        self.stateChanged.emit()

    def _ensure_current_search_view(
            self, current_view: str, emit: bool = True) -> None:
        current_view = str(current_view or "").strip()
        if current_view and not any(
            option.get("value") == current_view
            for option in self._search_preset_options
        ):
            self._search_preset_options.append({
                "value": current_view,
                "label": current_view,
            })
            if emit:
                self.stateChanged.emit()

    @Slot()
    def open_search(self) -> None:
        """Host the saved tab's existing query owners in a native modal window."""
        if not self.canOpenSearch:
            return
        if self._application.current_project_code != self._project_code:
            self._set_busy(False, self.tr(
                "The project changed. Reopen Sidebar Editor before opening this search."
            ))
            return
        selected = self.selectedEntry
        key = f"{selected['searchType']}@{selected['name']}"
        entry = self._application.navigation_model.entry(key)
        if entry is None or not entry.available or not entry.visible:
            self._set_busy(False, self.tr(
                "Save and enable this sidebar item before opening its search."
            ))
            return
        self._application._create_section(key, entry.title, entry.accent)
        if self._preview_context is None:
            self._preview_return_section = self._application.current_section_key
        self._preview_context = (self._project_code, key)
        self._pending_search_open = (self._project_code, key)
        self._application.activate_section(key)
        self._finish_search_open()

    def _finish_search_open(self) -> None:
        if (self._preview_context is not None
                and self._application.current_project_code != self._preview_context[0]):
            self._pending_search_open = None
            self._preview_context = None
            self._application.window_model.close_window("sidebar_search_preview")
            return
        pending = self._pending_search_open
        if pending is None:
            return
        project, key = pending
        if self._application.current_project_code != project:
            self._pending_search_open = None
            return
        if self._application.current_section_key != key:
            return
        self._pending_search_open = None
        surfaces = self._application.workspace_state.result_surfaces_model
        current_role = next(role for role, name in surfaces.roleNames().items()
                            if name == b"current")
        self._preview_surfaces.setFilterRole(current_role)
        self._preview_surfaces.setFilterFixedString("true")
        self._preview_surfaces.setSourceModel(surfaces)
        if self._filter_editor is not None:
            self._filter_editor.prepare_search_type_library(
                str(self.selectedEntry.get("searchView") or ""))
            self._filter_editor.sync_search_session()
        self.stateChanged.emit()
        self._application.window_model.show_child_window("sidebar_search_preview", "sidebar_editor")

    def _close_search_preview(self) -> None:
        context = self._preview_context
        self._preview_context = None
        self._pending_search_open = None
        self._preview_surfaces.setSourceModel(None)
        if self._filter_editor is not None:
            self._filter_editor.end_search_type_library()
        if context and self._application.current_project_code == context[0]:
            self._application.activate_section(self._preview_return_section)
        self.stateChanged.emit()

    @Slot(str)
    def set_preview_view_mode(self, mode: str) -> None:
        """Preview a layout and stage the same sidebar default for saving."""
        if self._preview_context != (
                self._application.current_project_code,
                self._application.current_section_key):
            return
        if mode not in {option["value"] for option in self.resultViewOptions}:
            raise ValueError(f"Unsupported search result view: {mode}")
        self._application.set_results_view_mode(mode)
        self.update_selected("resultViewMode", mode)
