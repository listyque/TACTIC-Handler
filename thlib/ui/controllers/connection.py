"""Application controller: connection."""
from __future__ import annotations
from collections.abc import Callable
from copy import deepcopy
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
class ConnectionMixin:
    def _flush_config_writes(self) -> None:
        queue = getattr(self, "_config_write_queue", None)
        if queue is not None:
            queue.flush()

    @staticmethod
    def _load_projects(*, force=True, cache_only=False):
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst, env_mode

        # The bootstrap query below is itself the authoritative connection and
        # authentication check.  A separate fast_ping adds a full XML-RPC
        # round trip and can disagree with the real API endpoint/proxy path.
        project_map = tc.get_all_projects_and_logins(
            force=force, cache_only=cache_only,
        )
        if cache_only and not project_map:
            return []
        if not cache_only:
            env_mode.set_online()
        return sorted(
            (
                project
                for code, project in (env_inst.projects or {}).items()
            ),
            key=lambda project: (
                str(project.get_info().get("category") or "Projects"),
                str(project.get_title() or "").lower(),
            ),
        )

    def _bootstrap_cache_identity(self) -> str:
        from thlib.environment import env_server

        return "{}|{}".format(
            str(env_server.get_server() or "").strip().rstrip("/"),
            str(env_server.get_user() or "").strip(),
        )

    @Slot()
    def restore_cached_workspace(self) -> None:
        """Restore the project shell from disk without touching the server."""
        try:
            cached_identity = str(
                self._search_cache.get("bootstrapIdentity", "") or ""
            )
            current_identity = self._bootstrap_cache_identity()
            if cached_identity and cached_identity != current_identity:
                return
            saved_project = str(
                self._settings.get("server/currentProject", "") or ""
            )
            projects = self._load_projects(force=False, cache_only=True)
            if not projects:
                return
            selectable = [
                project for project in projects
                if not bool(project.is_template())
            ]
            regular = [
                project for project in selectable
                if not bool(project.is_builtin())
            ]
            selected = next(
                (
                    project for project in selectable
                    if project.get_code() == saved_project
                ),
                (regular or selectable or projects)[0],
            )
            selection = self._prepare_project_selection(
                selected.get_code(),
                selected.get_title() or selected.get_code(),
                force_search_types=False,
                cache_only=True,
            )
            if not selection:
                return
            self.project_model.replace(projects)
            self._apply_cached_project_shell(*selection)
            self._set_loading(True, "Refreshing TACTIC workspace")
        except Exception as error:
            if self.debug_log:
                self.debug_log.log(
                    "WARNING",
                    f"Cached workspace could not be restored: {error}",
                    group="startup/cache",
                    source="ApplicationController",
                    caller=2,
                )
    @Slot()
    def bootstrap_server(self) -> None:
        if self._bootstrap_worker is not None:
            return
        from thlib.environment import env_inst, env_server

        server_url = str(env_server.get_server() or "").strip()
        if not server_url.startswith(("http://", "https://")):
            self._set_loading(False, "TACTIC server is not configured")
            self._set_server_state(
                "unconfigured", "Configure a TACTIC server to continue"
            )
            return
        if not env_server.get_ticket():
            self._set_loading(False, "TACTIC sign-in required")
            self._set_server_state(
                "authentication", "Generate a ticket to continue"
            )
            self._request_authentication()
            return
        self._cancel_project_catalog()
        self._bootstrap_started_at = time.perf_counter()
        self._set_loading(True, "Loading TACTIC projects and workspace")
        self._set_server_state(
            "connecting", "Loading TACTIC projects and workspace"
        )
        try:
            saved_project = str(
                self._settings.get("server/currentProject", "") or ""
            )
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            request_id = uuid.uuid4().hex
            worker = env_inst.server_pool.add_task(
                self._bootstrap_server_task,
                saved_project,
                request_id,
            )
            if worker is None:
                raise RuntimeError("Server worker pool is unavailable")
            self._bootstrap_request_id = request_id
            self._bootstrap_worker = worker
            worker.add_result_data(request_id)
            worker.result.connect(
                self._async_bootstrap_result,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.error.connect(
                self._async_bootstrap_error,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            self._bootstrap_failed(error, stacktrace=traceback.format_exc())

    def _bootstrap_server_task(self, saved_project: str, request_id: str):
        import thlib.tactic_classes as tc
        from thlib import server_cache
        from thlib.environment import env_inst, env_server

        if request_id != self._bootstrap_request_id:
            return None
        # A saved project may belong to the previous server. Resolve it from
        # the new server's catalog before sending any project-scoped request.
        projects = self._load_projects(force=True)
        if request_id != self._bootstrap_request_id:
            return None
        if not projects:
            raise RuntimeError("TACTIC returned no available projects")
        login = (env_inst.logins or {}).get(env_server.get_user())
        display_name = (
            login.get_display_name() if login else env_server.get_user()
        )
        selectable = [
            project for project in projects
            if not bool(project.is_template())
        ]
        regular = [
            project for project in selectable
            if not bool(project.is_builtin())
        ]
        active = [
            project for project in regular
            if str(
                project.get_info().get("s_status") or ""
            ).lower() != "retired"
        ]
        selected = next(
            (
                project for project in selectable
                if project.get_code() == saved_project
            ),
            (active or regular or selectable or projects)[0],
        )
        project_code = selected.get_code()
        cache_cursor = server_cache.read_cursor(
            "server_changes", project_code
        )
        if request_id != self._bootstrap_request_id:
            return None
        updates = tc.get_server_updates(
            project_code=project_code,
            include_activity=False,
            include_messages=False,
            include_reactions=False,
            include_presence=False,
            heartbeat_presence=False,
            cache_after=cache_cursor,
        ) or {}
        changes = list(updates.get("cacheChanges") or [])
        retired = list(updates.get("cacheRetired") or [])
        cold_cache = not cache_cursor
        invalidated = server_cache.apply_change_batch(changes, retired)
        if request_id != self._bootstrap_request_id:
            return None
        selection = self._prepare_project_selection(
            project_code,
            selected.get_title() or project_code,
            force_search_types=(
                cold_cache
                or "reference" in invalidated.get(selected.get_code(), ())
            ),
        )
        if request_id != self._bootstrap_request_id:
            return None
        next_cache_cursor = str(updates.get("cacheCursor") or "")
        if next_cache_cursor:
            server_cache.write_cursor(
                "server_changes", next_cache_cursor, project_code
            )
        can_administer = bool(login and login.get_info().get('__is_admin__') is True)
        return (projects, display_name, *selection, can_administer)

    @Slot(object)
    def _async_bootstrap_result(self, result) -> None:
        if not self._bootstrap_request_id or result[-1] != self._bootstrap_request_id:
            return
        (
            projects,
            display_name,
            project_code,
            title,
            entries,
            project,
            can_administer,
            request_id,
        ) = result
        self._bootstrap_worker = None
        self._bootstrap_request_id = ""
        try:
            self._current_user_initials = "".join(
                part[0] for part in str(display_name or "").split()[:2]
            ).upper()
            self.project_model.replace(projects)
            self._authentication_required = False
            self._authentication_dialog_visible = False
            self._authentication_error = ""
            self._apply_selected_project(
                project_code, title, entries, project
            )
            self._search_cache["bootstrapIdentity"] = (
                self._bootstrap_cache_identity()
            )
            self._write_search_cache_config()
            self._administration_identity = (
                (self.server_url, self.server_user) if can_administer else None
            )
            self._set_server_state("online", "Connected")
            self.authentication_changed.emit()
            self._set_loading(
                False,
                "Connected to TACTIC · {}".format(
                    self._transaction_metrics(
                        self._bootstrap_started_at, projects
                    )
                ),
            )
        except Exception as error:
            self._bootstrap_failed(error, stacktrace=traceback.format_exc())

    @Slot(object)
    def _async_bootstrap_error(self, error) -> None:
        payload, worker = error
        if worker.get_result_data() != self._bootstrap_request_id:
            return
        if isinstance(payload, dict):
            exception = payload.get("exception")
            stacktrace = str(payload.get("stacktrace") or "")
        else:
            exception = payload
            stacktrace = ""
        self._bootstrap_failed(
            exception or RuntimeError(str(error)),
            stacktrace=stacktrace,
            retry_worker=worker,
        )

    def _bootstrap_failed(
        self,
        error,
        *,
        stacktrace: str = "",
        retry_worker=None,
    ) -> None:
        self._bootstrap_worker = None
        if retry_worker is None:
            self._bootstrap_request_id = ""
        self.project_model.replace([])
        self.navigation_model.replace([])
        self.workspace_model.clear()
        if self.debug_log:
            self.debug_log.raise_error(
                error,
                stacktrace=stacktrace,
                group="server/bootstrap",
                retry_worker=retry_worker,
            )
        error_type = (
            self.debug_log.classify_error(error, stacktrace)
            if self.debug_log else ""
        )
        authentication_error = error_type in {
            "ticket_error", "login_pass_error"
        }
        self._set_server_state(
            "authentication" if authentication_error else "error",
            "Generate a ticket to continue"
            if authentication_error else str(error),
        )
        self._set_loading(
            False,
            "Connection failed · {} · {}".format(
                self._transaction_metrics(self._bootstrap_started_at), error
            ),
        )
        if authentication_error:
            self._request_authentication()
        else:
            self.notification_changed.emit(str(error))

    def _cancel_bootstrap(self) -> None:
        worker = self._bootstrap_worker
        self._bootstrap_worker = None
        self._bootstrap_request_id = ""
        if worker is not None:
            worker.cancel()

    @Slot()
    def refresh_projects(self) -> None:
        """Refresh the catalog without rebuilding the active workspace."""
        if (
            self._bootstrap_worker is not None
            or self._project_catalog_worker is not None
        ):
            return
        from thlib.environment import env_inst, env_server

        if not env_server.get_ticket():
            return
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(self._load_projects, force=True)
        if worker is None:
            return
        request_id = uuid.uuid4().hex
        self._project_catalog_request_id = request_id
        self._project_catalog_worker = worker
        worker.add_result_data(request_id)
        worker.result.connect(
            self._async_project_catalog_result,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._async_project_catalog_error,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot(object)
    def _async_project_catalog_result(self, result) -> None:
        projects, request_id = result
        if request_id != self._project_catalog_request_id:
            return
        self._project_catalog_worker = None
        self._project_catalog_request_id = ""
        if projects:
            self.project_model.replace(projects)

    @Slot(object)
    def _async_project_catalog_error(self, error) -> None:
        payload, worker = error
        if worker.get_result_data() != self._project_catalog_request_id:
            return
        self._project_catalog_worker = None
        self._project_catalog_request_id = ""
        self._report_error_payload(payload, "server/projects", worker)

    def _cancel_project_catalog(self) -> None:
        worker = self._project_catalog_worker
        self._project_catalog_worker = None
        self._project_catalog_request_id = ""
        if worker is not None:
            worker.cancel()

    @Slot(str)
    def edit_project(self, project_code: str) -> None:
        from thlib.environment import env_inst

        project = (env_inst.projects or {}).get(str(project_code or ""))
        if project is None:
            self._notify(self.tr("Select a project first"))
            return
        try:
            if project.is_builtin():
                self._notify(self.tr("Built-in TACTIC projects cannot be edited"))
                return
        except AttributeError:
            pass
        self._project_editor_request = {
            "project": project,
            "preview": self.project_model.preview_for(project),
            "refresh": self._refresh_edited_project,
        }
        self.window_model.show_window("project_editor")
        self.projectEditRequested.emit()

    @Slot()
    def deactivate_project(self) -> None:
        from thlib.environment import env_inst

        self._persist_current_project_workspace()
        self._cancel_bootstrap()
        self._project_request_id = ""
        self._active_request_id = ""
        self._skey_request_id = ""
        self._suggestion_request_id = ""
        self._invalidate_sidebar_preset_requests()
        self._selection_load_timer.stop()
        self._pending_selection_load = None
        self._pending_versions_node_id = ""
        self._detail_request_id = ""
        self._versions_request_id = ""
        self._cancel_selected_payload_worker()
        self._cancel_versions_worker()
        self.workspace_state.clear_selection()
        self.workspace_state.load_project(None)
        self.workspace_state.load_stype(None)
        self.versions_model.clear()
        self.workspace_state.set_result_surfaces([])
        self._dispose_all_tab_workspace_models()
        self._sessions.clear()
        self.workspace_state.set_tabs([])
        self.workspace_model.clear()
        self.navigation_model.replace([])
        self.section_model.replace([])
        self._current_section_key = ""
        self._current_project_code = ""
        self._current_project_title = ""
        self._current_project_preview = ""
        env_inst.set_current_project(None)
        self._settings["server/currentProject"] = ""
        self._write_settings()
        self._clear_result_state()
        self._set_loading(False, self.tr("Project deactivated"))
        self.project_changed.emit("", "")
        if hasattr(self, 'accent_changed'):
            self.accent_changed.emit()
        if hasattr(self, 'theme_style_changed'):
            self.theme_style_changed.emit(self.theme_style)
        self.project_state_changed.emit()
        self.section_state_changed.emit()

    def project_editor_context(self) -> dict:
        return dict(self._project_editor_request or {})

    def _refresh_edited_project(self, project) -> None:
        entries = list(self.project_model._all_entries)
        self.project_model.replace(entries)
        if (
            project is not None
            and project.get_code() == self._current_project_code
        ):
            self._current_project_title = (
                project.get_title() or project.get_code()
            )
            self._current_project_preview = (
                self.project_model.preview_for(project)
            )
            self.project_state_changed.emit()

    def apply_project_metadata(self, fresh, entries: list) -> None:
        """Publish an administrative metadata refresh without replacing tabs."""
        from thlib.environment import env_inst

        code = fresh.get_code()
        project = (env_inst.projects or {}).get(code)
        if project is None:
            return
        previous = project.stypes or {}
        stypes = {}
        for identity, incoming in (fresh.stypes or {}).items():
            retained = previous.get(identity)
            if retained is not None:
                retained.info = incoming.info
                retained.schema = incoming.schema
                retained.pipeline = incoming.pipeline
            else:
                retained = incoming
            retained.project = project
            stypes[identity] = retained
        project.stypes = stypes
        project.workflow = fresh.workflow
        project.plugin_theme = getattr(fresh, 'plugin_theme', None)
        project.views = fresh.views
        project.views.project = project
        if code != self._current_project_code:
            return
        self.navigation_model.replace(entries)
        self.workspace_state.load_project(project)
        self.apply_cache_invalidation({code: ['reference', 'search', 'relations', 'tasks']})
        self.project_state_changed.emit()
        if hasattr(self, 'accent_changed'):
            self.accent_changed.emit()
        if hasattr(self, 'theme_style_changed'):
            self.theme_style_changed.emit(self.theme_style)
    @Slot(str)
    def select_project(self, project_code: str) -> None:
        files = getattr(self, 'file_workspace', None)
        if files and project_code != self._current_project_code and not files.can_leave():
            self._notify(self.tr('Save or reset Depot and Storage changes before leaving this project.'))
            return
        self._skey_request_id = ""
        self._suggestion_request_id = ""
        try:
            from thlib.environment import env_inst
            project = env_inst.projects.get(project_code)
            if not project:
                raise RuntimeError(f"Project is unavailable: {project_code}")
            title = project.info.get("title") or project.info.get("name") or project_code
            if project_code == self._current_project_code:
                return
            # A manual project choice supersedes the startup selection.  Its
            # late bootstrap completion must not publish a different project.
            self._cancel_bootstrap()
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            request_id = uuid.uuid4().hex
            self._project_request_id = request_id
            self._project_started_at[request_id] = time.perf_counter()
            self._set_loading(True, f"Loading project: {title}")
            worker = env_inst.server_pool.add_task(
                self._prepare_project_selection,
                project_code,
                title,
            )
            worker.add_result_data(request_id)
            worker.result.connect(self._async_project_result)
            worker.error.connect(self._async_project_error)
            worker.start()
        except Exception as error:
            self._set_loading(False, f"Project load failed: {error}")
            self._notify(str(error))
    def _select_project(self, project_code: str, title: str) -> None:
        project_code, title, entries, project = self._prepare_project_selection(
            project_code,
            title,
        )
        self._apply_selected_project(project_code, title, entries, project)
    def _prepare_project_selection(
        self, project_code: str, title: str, *,
        force_search_types: bool = True, cache_only: bool = False,
    ):
        from thlib.environment import env_inst
        project = env_inst.projects[project_code]
        # Warm the project metadata in the server worker. WorkspaceState then
        # only projects the cached objects into Qt models on the GUI thread.
        # The project object may already contain pipeline metadata loaded by a
        # previous session state.  Use the original Project API to refresh the
        # native Pipeline/config-process objects before any task editor reads
        # workflow properties such as bid_duration.
        loaded = project.query_search_types(
            force=force_search_types, cache_only=cache_only,
        )
        if cache_only and not loaded:
            return None
        if not cache_only and getattr(self, 'is_stream_server', False):
            from thlib.ui.theme_catalog import read_project_theme
            project.plugin_theme = read_project_theme(project_code)
        entries = self.navigation_model.build_project_entries(
            project,
            env_inst.get_current_login_object(),
        )
        return project_code, title, entries, project

    def _persist_current_project_workspace(self) -> dict[str, dict]:
        """Capture the current section before its project session is replaced."""
        if not self._current_project_code:
            return {}
        self._section_state_save_timer.stop()
        self._search_cache_save_timer.stop()
        # Capture the active Search tab even when the optional process-tab disk
        # cache is disabled, because a same-project metadata refresh replaces
        # the section sessions.
        self._capture_current_workspace_layout()
        retained_layouts = {
            key: {
                "current_tab_id": section.current_tab_id,
                "tabs": {
                    tab.tab_id: deepcopy(tab.workspace_layout)
                    for tab in section.tabs
                    if isinstance(tab.workspace_layout, dict)
                },
            }
            for key, section in self._sessions.items()
        }
        self._write_opened_sections()
        self._write_search_cache()
        return retained_layouts

    @staticmethod
    def _restore_retained_workspace_layouts(section, retained) -> None:
        """Restore exact per-tab layouts after a same-project refresh."""
        if not isinstance(retained, dict):
            return
        layouts = retained.get("tabs")
        if not isinstance(layouts, dict):
            return
        matched = False
        for tab in section.tabs:
            layout = layouts.get(tab.tab_id)
            if isinstance(layout, dict):
                tab.workspace_layout = deepcopy(layout)
                matched = True
        if matched:
            return
        active_layout = layouts.get(str(retained.get("current_tab_id") or ""))
        if not isinstance(active_layout, dict):
            return
        current = next(
            (
                tab for tab in section.tabs
                if tab.tab_id == section.current_tab_id
            ),
            None,
        )
        if current is not None:
            current.workspace_layout = deepcopy(active_layout)

    def _apply_cached_project_shell(
        self, project_code, title, entries, project
    ) -> None:
        """Project local navigation and tabs without starting server work."""
        previous_project_code = self._current_project_code
        retained_layouts = self._persist_current_project_workspace()
        if previous_project_code != project_code:
            retained_layouts = {}
        self._invalidate_sidebar_preset_requests()
        from thlib.environment import env_inst

        env_inst.set_current_project(project_code)
        self._current_project_code = project_code
        self._current_project_title = title
        self._current_project_preview = self.project_model.preview_for(project)
        self.workspace_state.load_project(project)
        self.navigation_model.replace(entries)
        self.workspace_state.set_result_surfaces([])
        self._dispose_all_tab_workspace_models()
        self._sessions.clear()
        self._current_section_key = ""
        self.section_model.replace([])
        self.workspace_state.set_tabs([])
        self.workspace_model.clear()
        links = {
            entry.key: entry for entry in entries
            if entry.entry_type == "link" and entry.available and entry.search_type
        }
        search_cache = self._load_search_cache(project_code)
        restored = [
            key for key in self._opened_section_keys(project_code)
            if key in links
        ]
        for key in restored:
            entry = links[key]
            section = self._create_section(
                entry.key, entry.title, entry.accent
            )
            if key in search_cache:
                self._restore_section_tabs(section, search_cache[key])
            if key in retained_layouts:
                self._restore_retained_workspace_layouts(
                    section, retained_layouts[key]
                )
        if restored:
            saved_active = self._saved_active_section_key(project_code)
            self._current_section_key = (
                saved_active if saved_active in restored else restored[0]
            )
            active_section = self._current_section()
            active_tab = self._current_tab()
            if active_section and active_tab and active_tab.workspace_layout:
                self._apply_tab_workspace_layout(active_section, active_tab)
            self._sync_section_model()
            self._sync_search_tabs()
        else:
            self._clear_result_state()
        self.project_state_changed.emit()
        self.section_state_changed.emit()
        if hasattr(self, 'accent_changed'):
            self.accent_changed.emit()
        if hasattr(self, 'theme_style_changed'):
            self.theme_style_changed.emit(self.theme_style)
    @Slot(object)
    def _async_project_result(self, result) -> None:
        project_code, title, entries, project, request_id = result
        if request_id != self._project_request_id:
            return
        self._apply_selected_project(project_code, title, entries, project)
        started_at = self._project_started_at.pop(request_id, time.perf_counter())
        self._set_loading(
            False,
            "Project loaded: {} · {}".format(
                title,
                self._transaction_metrics(started_at, (entries, project.info)),
            ),
        )
    @Slot(object)
    def _async_project_error(self, error) -> None:
        payload, worker = error
        if worker.get_result_data() != self._project_request_id:
            return
        self._report_error_payload(payload, "server/project", worker)
        started_at = self._project_started_at.pop(
            self._project_request_id, time.perf_counter()
        )
        message = str(payload.get("exception") or error)
        self._set_loading(
            False,
            "Project load failed · {} · {}".format(
                self._transaction_metrics(started_at), message
            ),
        )
        self._notify(message)
    def _apply_selected_project(self, project_code, title, entries, project) -> None:
        previous_project_code = self._current_project_code
        reuse_sessions = (
            previous_project_code == project_code and bool(self._sessions)
        )
        retained_layouts = self._persist_current_project_workspace()
        if previous_project_code != project_code:
            retained_layouts = {}
        self._invalidate_sidebar_preset_requests()
        from thlib.environment import env_inst

        env_inst.set_current_project(project_code)
        self._current_project_code = project_code
        self._current_project_title = title
        self._current_project_preview = self.project_model.preview_for(project)
        self._settings["server/currentProject"] = project_code
        self._write_settings()
        self.workspace_state.load_project(project)
        self.navigation_model.replace(entries)
        links = {
            entry.key: entry for entry in entries
            if entry.entry_type == "link" and entry.available and entry.search_type
        }
        search_cache = self._load_search_cache(project_code)
        restored = [key for key in self._opened_section_keys(project_code) if key in links]
        saved_active = self._saved_active_section_key(project_code)
        if reuse_sessions:
            for key in list(self._sessions):
                if key not in restored:
                    removed = self._sessions.pop(key)
                    self._dispose_section_workspace_models(removed)
            if self._current_section_key not in self._sessions:
                self._current_section_key = ""
            stypes = getattr(project, "stypes", None) or {}
            for key in restored:
                entry = links[key]
                section = self._sessions.get(key)
                if section is not None:
                    section.title = entry.title
                    section.accent = entry.accent or "#607d8b"
                    section.search_type = entry.search_type
                    section.search_view = str(entry.search_view or "")
                    section.layout_preset = str(entry.layout_preset or "")
                    stype = stypes.get(section.search_type)
                    for tab in (*section.tabs, *section.closed_tabs):
                        if stype is not None or tab.stype is not None:
                            tab.stype = stype
                        if tab.tab_kind == "base":
                            tab.table_view = entry.table_view or "table"
                            tab.layout_view = entry.layout_view or ""
                    if key in retained_layouts:
                        self._restore_retained_workspace_layouts(
                            section, retained_layouts[key]
                        )
                    continue
                section = self._create_section(entry.key, entry.title, entry.accent)
                if key in search_cache:
                    self._restore_section_tabs(section, search_cache[key])
                if key in retained_layouts:
                    self._restore_retained_workspace_layouts(
                        section, retained_layouts[key]
                    )
            self._sessions = {
                key: self._sessions[key]
                for key in restored
                if key in self._sessions
            }
            if not restored:
                self.workspace_state.set_result_surfaces([])
                self._current_section_key = ""
                self.section_model.replace([])
                self.workspace_state.set_tabs([])
                self.workspace_model.clear()
        else:
            self.workspace_state.set_result_surfaces([])
            self._dispose_all_tab_workspace_models()
            self._sessions.clear()
            self._current_section_key = ""
            self.section_model.replace([])
            self.workspace_state.set_tabs([])
            self.workspace_model.clear()
        self.project_changed.emit(project_code, title)
        if hasattr(self, 'accent_changed'):
            self.accent_changed.emit()
        if hasattr(self, 'theme_style_changed'):
            self.theme_style_changed.emit(self.theme_style)
        self.project_state_changed.emit()
        if not reuse_sessions:
            for key in restored:
                entry = links[key]
                section = self._create_section(entry.key, entry.title, entry.accent)
                if key in search_cache:
                    self._restore_section_tabs(section, search_cache[key])
                if key in retained_layouts:
                    self._restore_retained_workspace_layouts(
                        section, retained_layouts[key]
                    )
        if search_cache:
            self._save_search_cache()
        if restored:
            if reuse_sessions:
                self._sync_section_model()
            self.activate_section(
                saved_active if saved_active in restored else restored[0]
            )
        else:
            self._clear_result_state()
            self.section_state_changed.emit()

    @Slot(str, str)
    def _project_preview_ready(self, project_code: str, preview_url: str) -> None:
        if project_code != self._current_project_code:
            return
        self._current_project_preview = preview_url
        self.project_state_changed.emit()
    @Slot()
    def ping_server(self) -> None:
        if self._ping_in_progress or self._loading:
            return
        self._ping_started_at = time.perf_counter()
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            self._ping_in_progress = True
            self._set_loading(True, "Pinging TACTIC server")
            worker = env_inst.server_pool.add_task(self._server_ping_task)
            worker.result.connect(self._async_ping_result)
            worker.error.connect(self._async_ping_error)
            worker.start()
        except Exception as error:
            self._ping_in_progress = False
            self._set_server_state("error", str(error))
            self._set_loading(
                False,
                "Ping failed · {} · {}".format(
                    self._transaction_metrics(self._ping_started_at), error
                ),
            )
    @staticmethod
    def _server_ping_task() -> bool:
        import thlib.tactic_classes as tc
        return bool(tc.server_ping())
    @Slot(object)
    def _async_ping_result(self, online) -> None:
        self._ping_in_progress = False
        metrics = self._transaction_metrics(self._ping_started_at, online)
        if online:
            self._set_server_state("online", "TACTIC server responded")
            self._set_loading(False, f"Ping successful · {metrics}")
        else:
            self._set_server_state("error", "TACTIC server did not respond")
            self._set_loading(False, f"Ping failed · {metrics}")
    @Slot(object)
    def _async_ping_error(self, error) -> None:
        payload, worker = error
        self._report_error_payload(payload, "server/ping", worker)
        self._ping_in_progress = False
        message = str(payload.get("exception") or error)
        self._set_server_state("error", message)
        self._set_loading(
            False,
            "Ping failed · {} · {}".format(
                self._transaction_metrics(self._ping_started_at), message
            ),
        )
        self._notify(message)
    @Slot(bool)
    def server_updates_connection_checked(self, online: bool) -> None:
        if not self.has_ticket or self._authentication_required:
            return
        if (
            online
            and self._server_state == "error"
            and self._server_message in {
                "Cannot reach TACTIC server",
                "TACTIC server did not respond",
            }
        ):
            self._set_server_state("online", "Connected")
        elif not online and self._server_state == "online":
            self._set_server_state("error", "Cannot reach TACTIC server")

    def _notify(self, text: str) -> None:
        if self.debug_log and text:
            level = "ERROR" if any(
                token in str(text).lower()
                for token in ("error", "failed", "cannot ", "exception")
            ) else "LOG"
            self.debug_log.log(
                level,
                text,
                group="ui/notification",
                source="Controller",
                caller=2,
            )
        self.notification_changed.emit(text)

    def notify(self, text: str) -> None:
        """Publish a user-facing application notification."""
        self._notify(text)

    def _report_error_payload(
        self,
        payload,
        group: str,
        worker=None,
        command: str = "",
    ) -> None:
        if not self.debug_log:
            return
        if isinstance(payload, dict):
            exception = payload.get("exception") or RuntimeError(str(payload))
            stacktrace = str(payload.get("stacktrace") or "")
        else:
            exception = payload
            stacktrace = ""
        self.debug_log.raise_error(
            exception,
            stacktrace=stacktrace,
            group=group,
            command=command,
            retry_worker=worker,
        )
    def _request_authentication(self) -> None:
        if self._authentication_busy:
            return
        self._authentication_required = True
        self._authentication_busy = False
        from thlib.environment import env_server

        self._authentication_error = (
            "Your TACTIC session has expired. Generate a new ticket."
            if env_server.get_ticket()
            else "Enter your TACTIC login and password to generate a ticket."
        )
        if self._server_state != "authentication":
            self._set_server_state(
                "authentication", "Generate a ticket to continue"
            )
        self.authentication_changed.emit()

    @Slot()
    def request_authentication(self) -> None:
        self._request_authentication()
        if self._authentication_busy:
            return
        self._authentication_dialog_visible = True
        self.authentication_changed.emit()
    @Slot(str)
    def _error_dialog_dismissed(self, error_type: str) -> None:
        if (
            error_type in {"ticket_error", "login_pass_error"}
            and self._authentication_required
            and not self._authentication_busy
        ):
            self.cancel_authentication()
    @Slot()
    def cancel_authentication(self) -> None:
        if self._authentication_busy:
            return
        from thlib.environment import env_server

        self._authentication_dialog_visible = False
        self._authentication_required = not bool(
            env_server.get_ticket() and self._server_state == "online"
        )
        self._authentication_error = ""
        self.authentication_changed.emit()

    def _cancel_authentication(self) -> None:
        self._authentication_request_id = ""
        worker = self._authentication_worker
        self._authentication_worker = None
        self._authentication_busy = False
        if worker is not None:
            try:
                worker.cancel()
            except RuntimeError:
                pass

    @Slot()
    def logout(self) -> None:
        from thlib.environment import env_inst, env_server

        self._persist_current_project_workspace()
        self._invalidate_sidebar_preset_requests()
        self._cancel_bootstrap()
        self._cancel_project_catalog()
        self._active_request_id = ""
        self._project_request_id = ""
        self._cancel_authentication()
        self.signing_out.emit()
        self._flush_config_writes()
        env_server.set_ticket(None)
        env_server.set_user(None)
        env_server.save_defaults()
        env_inst.logins = {}
        env_inst.projects = {}
        self.project_model.replace([])
        self.navigation_model.replace([])
        self.section_model.replace([])
        self.versions_model.clear()
        self.workspace_state.clear_selection()
        self.workspace_state.set_result_surfaces([])
        self._dispose_all_tab_workspace_models()
        self._sessions.clear()
        self.workspace_state.set_tabs([])
        self.workspace_model.clear()
        self._current_section_key = ""
        self._current_project_code = ""
        self._current_project_title = ""
        self._current_user_initials = ""
        self._authentication_required = True
        self._authentication_dialog_visible = True
        self._authentication_error = (
            "Enter your TACTIC login and password to generate a ticket."
        )
        self._set_loading(False, "Signed out")
        self._set_server_state(
            "authentication", "Sign in to continue"
        )
        self.project_changed.emit("", "")
        self.project_state_changed.emit()
        self.section_state_changed.emit()
        self.authentication_changed.emit()
    @Slot(str, str)
    def authenticate(self, login: str, password: str) -> None:
        login = (login or "").strip()
        if self._authentication_busy:
            return
        if not login or not password:
            self._authentication_error = "Enter both login and password."
            self.authentication_changed.emit()
            return
        self._authentication_busy = True
        self._authentication_error = ""
        self._authentication_started_at = time.perf_counter()
        request_id = uuid.uuid4().hex
        self._authentication_request_id = request_id
        self.authentication_changed.emit()
        self._set_loading(True, "Generating a new TACTIC ticket")
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(
                self._authenticate_task, login, password
            )
            self._authentication_worker = worker
            worker.add_result_data(request_id)
            worker.result.connect(
                self._async_authentication_result,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.error.connect(
                self._async_authentication_error,
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except Exception as error:
            self._authentication_error_result_for(request_id, ({
                "exception": error,
                "stacktrace": traceback.format_exc(),
            }, None))

    @Slot(object)
    def _async_authentication_result(self, payload) -> None:
        *result, request_id = payload
        self._authentication_result_for(request_id, tuple(result))

    @Slot(object)
    def _async_authentication_error(self, error) -> None:
        worker = error[1] if isinstance(error, tuple) and len(error) > 1 else None
        request_id = (
            worker.get_result_data()
            if worker is not None
            else self._authentication_request_id
        )
        self._authentication_error_result_for(request_id, error)

    def _authentication_result_for(self, request_id: str, result) -> None:
        if request_id != self._authentication_request_id:
            return
        self._authentication_request_id = ""
        self._authentication_worker = None
        self._authentication_result(result)

    def _authentication_error_result_for(self, request_id: str, error) -> None:
        if request_id != self._authentication_request_id:
            return
        self._authentication_request_id = ""
        self._authentication_worker = None
        self._authentication_error_result(error)

    @staticmethod
    def _authenticate_task(login: str, password: str):
        import thlib.tactic_classes as tc
        from thlib.environment import env_server
        site = (env_server.get_site() or {}).get("site_name")
        server = tc.server_auth(
            env_server.get_server(),
            project="sthpw",
            login=login,
            password=password,
            site=site,
            get_ticket=True,
        )
        ticket = server.get_login_ticket()
        if not ticket:
            raise PermissionError("TACTIC did not issue an authentication ticket.")
        if server.ping() != "OK":
            raise ConnectionError("TACTIC did not accept the generated ticket.")
        return login, ticket
    @Slot(object)
    def _authentication_result(self, result) -> None:
        login, ticket = result
        from thlib.environment import env_server
        self._flush_config_writes()
        env_server.set_user(login)
        env_server.set_ticket(ticket)
        env_server.save_defaults()
        config_identity = str(getattr(self, "_config_identity", "") or "")
        if login != config_identity:
            # The new process reads every controller from the new user's tree.
            # Keep shutdown writes in the tree that owns the live UI state.
            env_server.set_user(config_identity or None)
            self.restart_requested.emit()
            return
        self._reset_cached_sidebar_presets_for_identity(
            self._bootstrap_cache_identity()
        )
        self._settings["server/lastLogin"] = login
        self._write_settings()
        self._login_name = login
        self._authentication_busy = False
        self._authentication_required = False
        self._authentication_dialog_visible = False
        self._authentication_error = ""
        self.authentication_changed.emit()
        self.server_state_changed.emit()
        self._set_loading(
            False,
            "Authenticated | {}".format(
                self._transaction_metrics(self._authentication_started_at)
            ),
        )
        self.bootstrap_server()

    def _reset_cached_sidebar_presets_for_identity(
        self,
        identity: str,
    ) -> None:
        """Drop login-scoped preset catalogs while retaining personal UI state."""
        cached_identity = str(
            self._search_cache.get("bootstrapIdentity", "") or ""
        )
        if not self._search_cache or cached_identity == identity:
            return
        for project_code, payload in tuple(self._search_cache.items()):
            if project_code == "bootstrapIdentity" or not isinstance(
                payload, dict
            ):
                continue
            sections = payload.get("sections")
            if not isinstance(sections, list):
                continue
            normalized_sections = []
            for raw_section in sections:
                if not isinstance(raw_section, dict):
                    normalized_sections.append(raw_section)
                    continue
                section = dict(raw_section)
                section["sidebar_presets_initialized"] = False
                tabs = section.get("tabs")
                if isinstance(tabs, list):
                    section["tabs"] = [
                        tab for tab in tabs
                        if not isinstance(tab, dict)
                        or tab.get("tab_kind") != "preset"
                    ]
                normalized_sections.append(section)
            project_payload = dict(payload)
            project_payload["sections"] = normalized_sections
            self._search_cache[project_code] = project_payload
        self._search_cache["bootstrapIdentity"] = identity
        self._write_search_cache_config()
    @Slot(object)
    def _authentication_error_result(self, error) -> None:
        payload, _worker = error
        raw_message = str(payload.get("exception") or error)
        lowered = raw_message.lower()
        if self.debug_log:
            self.debug_log.log(
                "ERROR",
                raw_message,
                group="server/authentication",
                source="Authentication",
                stacktrace=str(payload.get("stacktrace") or ""),
                caller=2,
            )
        if "login/password combination incorrect" in lowered:
            message = "Incorrect login or password."
        elif "timed out" in lowered or "timeout" in lowered:
            message = "The TACTIC server did not respond in time."
        elif any(token in lowered for token in (
            "connection refused", "actively refused", "unreachable",
            "getaddrinfo failed", "no connection could be made",
        )):
            message = "Cannot connect to the configured TACTIC server."
        elif "did not issue an authentication ticket" in lowered:
            message = "TACTIC did not issue an authentication ticket."
        elif "did not accept the generated ticket" in lowered:
            message = "TACTIC did not accept the generated ticket."
        else:
            message = "{}: {}".format(
                self.tr("Authentication failed"), raw_message
            )
        self._authentication_busy = False
        self._authentication_required = True
        self._authentication_error = message
        self.authentication_changed.emit()
        self._set_loading(
            False,
            "Authentication failed | {} | {}".format(
                self._transaction_metrics(self._authentication_started_at),
                message,
            ),
        )
    @Slot(str, str)
    @Slot(str, str, bool, str)
    def apply_server_configuration(
        self, server_url: str, preset_name: str,
        preserve_values: bool = False,
        rpc_transport: str | None = None,
    ) -> None:
        from thlib.ui.server_address import (
            is_valid_tactic_server_url,
            normalize_tactic_server_url,
        )

        server_url = normalize_tactic_server_url(server_url)
        preset_name = str(preset_name or "").strip()
        if rpc_transport not in (None, "xmlrpc", "json"):
            self._notify("Select XML-RPC or JSON (TACTIC Stream)")
            return
        if not is_valid_tactic_server_url(server_url):
            self._notify("Enter a valid TACTIC server address")
            return
        from thlib.environment import cfg_controls, env_inst, env_server, env_tactic

        self._cancel_bootstrap()
        self._cancel_project_catalog()
        presets = env_server.get_server_presets().get("presets_list", [])
        if preset_name not in presets:
            self._notify("Select an existing server preset")
            return
        self._cancel_authentication()
        self.signing_out.emit()
        self._flush_config_writes()
        env_server.set_cur_srv_preset(preset_name)
        env_server.save_server_presets_defaults()
        env_server.load_current_preset(preserve_values)
        cfg_controls.reset()
        env_tactic.reset()
        env_server.set_server(server_url)
        if rpc_transport is not None:
            env_server.set_rpc_transport(rpc_transport)
        env_server.set_ticket(None)
        env_server.save_defaults()
        env_inst.logins = {}
        env_inst.projects = {}
        self._authentication_required = False
        self._authentication_error = ""
        self.authentication_changed.emit()
        self.server_state_changed.emit()
        self._set_server_state(
            "authentication", "Generate a ticket to continue"
        )
        self._request_authentication()

    @Slot(str)
    def select_server_preset(self, preset_name: str) -> None:
        from thlib.environment import env_server

        preset_name = str(preset_name or "").strip()
        presets = env_server.get_server_presets().get("presets_list", [])
        if preset_name not in presets:
            self._notify("Select an existing server preset")
            return
        values = dict(env_server.get_server_preset(preset_name) or {})
        self.apply_server_configuration(
            str(values.get("server") or ""), preset_name
        )
