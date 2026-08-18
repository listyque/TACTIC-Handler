"""Application controller: connection."""
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
class ConnectionMixin:
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
        if force:
            env_mode.set_online()
        retired = []
        if force:
            try:
                retired = tc.server_start(project="sthpw").query(
                    "sthpw/project",
                    filters=[("s_status", "retired")],
                    show_retired=True,
                )
            except Exception:
                retired = []
        for info in retired or []:
            code = info.get("code")
            if not code or code == "sthpw" or code in env_inst.projects:
                continue
            project = tc.Project(info)
            project.init_snapshots([])
            env_inst.projects[code] = project
        return sorted(
            (
                project
                for code, project in (env_inst.projects or {}).items()
                if code != "sthpw"
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
            cached_identity = self._settings.value(
                "server/bootstrapCacheIdentity", "", type=str
            )
            current_identity = self._bootstrap_cache_identity()
            if cached_identity and cached_identity != current_identity:
                return
            saved_project = self._settings.value(
                "server/currentProject", "", type=str
            )
            projects = self._load_projects(force=False, cache_only=True)
            if not projects:
                return
            selectable = [
                project for project in projects
                if not bool(project.is_template())
            ]
            selected = next(
                (
                    project for project in selectable
                    if project.get_code() == saved_project
                ),
                (selectable or projects)[0],
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
        self._bootstrap_started_at = time.perf_counter()
        self._set_loading(True, "Loading TACTIC projects and workspace")
        self._set_server_state(
            "connecting", "Loading TACTIC projects and workspace"
        )
        try:
            saved_project = self._settings.value("server/currentProject", "", type=str)
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            request_id = uuid.uuid4().hex
            worker = env_inst.server_pool.add_task(
                self._bootstrap_server_task,
                saved_project,
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
            self._bootstrap_failed(error)

    def _bootstrap_server_task(self, saved_project: str):
        from thlib.environment import env_inst, env_server

        projects = self._load_projects(force=True)
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
        active = [
            project for project in selectable
            if str(
                project.get_info().get("status")
                or project.get_info().get("s_status")
                or ""
            ).lower() != "retired"
        ]
        selected = next(
            (
                project for project in selectable
                if project.get_code() == saved_project
            ),
            (active or selectable or projects)[0],
        )
        selection = self._prepare_project_selection(
            selected.get_code(),
            selected.get_title() or selected.get_code(),
        )
        return (projects, display_name, *selection)

    @Slot(object)
    def _async_bootstrap_result(self, result) -> None:
        (
            projects,
            display_name,
            project_code,
            title,
            entries,
            project,
            request_id,
        ) = result
        if request_id != self._bootstrap_request_id:
            return
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
            self._settings.setValue(
                "server/bootstrapCacheIdentity",
                self._bootstrap_cache_identity(),
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
            self._bootstrap_failed(error)

    @Slot(object)
    def _async_bootstrap_error(self, error) -> None:
        payload, worker = error
        if worker.get_result_data() != self._bootstrap_request_id:
            return
        exception = (
            payload.get("exception")
            if isinstance(payload, dict) else payload
        )
        self._bootstrap_failed(exception or RuntimeError(str(error)))

    def _bootstrap_failed(self, error) -> None:
        self._bootstrap_worker = None
        self._bootstrap_request_id = ""
        self.project_model.replace([])
        self.navigation_model.replace([])
        self.workspace_model.clear()
        error_type = (
            self.debug_log.classify_error(error)
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
            self._notify(str(error))

    def _cancel_bootstrap(self) -> None:
        worker = self._bootstrap_worker
        self._bootstrap_worker = None
        self._bootstrap_request_id = ""
        if worker is not None:
            worker.cancel()
    @Slot(str)
    def select_project(self, project_code: str) -> None:
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
        env_inst.set_current_project(project_code)
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
        entries = self.navigation_model.build_project_entries(
            project,
            env_inst.get_current_login_object(),
        )
        return project_code, title, entries, project
    def _apply_cached_project_shell(
        self, project_code, title, entries, project
    ) -> None:
        """Project local navigation and tabs without starting server work."""
        self._current_project_code = project_code
        self._current_project_title = title
        self._current_project_preview = self.project_model.preview_for(project)
        self.workspace_state.load_project(project)
        self.navigation_model.replace(entries)
        self._sessions.clear()
        self._current_section_key = ""
        self.section_model.replace([])
        self.workspace_state.set_tabs([])
        self.workspace_model.clear()
        links = {
            entry.key: entry for entry in entries
            if entry.entry_type == "link"
        }
        search_cache = self._load_search_cache(project_code)
        restored = [
            key for key in self._opened_section_keys(project_code)
            if key in links
        ]
        if not restored and links:
            restored = [next(iter(links))]
        for key in restored:
            entry = links[key]
            section = self._create_section(
                entry.key, entry.title, entry.accent
            )
            if key in search_cache:
                self._restore_section_tabs(section, search_cache[key])
        if restored:
            saved_active = self._saved_active_section_key(project_code)
            self._current_section_key = (
                saved_active if saved_active in restored else restored[0]
            )
            self._sync_section_model()
            self._sync_search_tabs()
        self.project_state_changed.emit()
        self.section_state_changed.emit()
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
        if (
            self._current_project_code
            and self._current_project_code != project_code
        ):
            self._search_cache_save_timer.stop()
            self._write_search_cache()
        self._current_project_code = project_code
        self._current_project_title = title
        self._current_project_preview = self.project_model.preview_for(project)
        self._settings.setValue("server/currentProject", project_code)
        self.workspace_state.load_project(project)
        self.navigation_model.replace(entries)
        self._sessions.clear()
        self._current_section_key = ""
        self.section_model.replace([])
        self.workspace_state.set_tabs([])
        self.workspace_model.clear()
        self.project_changed.emit(project_code, title)
        self.project_state_changed.emit()
        links = {entry.key: entry for entry in entries if entry.entry_type == "link"}
        search_cache = self._load_search_cache(project_code)
        restored = [key for key in self._opened_section_keys(project_code) if key in links]
        saved_active = self._saved_active_section_key(project_code)
        if not restored and links:
            restored = [next(iter(links))]
        for key in restored:
            entry = links[key]
            section = self._create_section(entry.key, entry.title, entry.accent)
            if key in search_cache:
                self._restore_section_tabs(section, search_cache[key])
        if search_cache:
            self._save_search_cache()
        if restored:
            self.activate_section(
                saved_active if saved_active in restored else restored[0]
            )

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
    @Slot(int)
    def set_ping_interval(self, seconds: int) -> None:
        seconds = seconds if seconds in {0, 10, 60} else 0
        if self._ping_interval == seconds:
            return
        self._ping_interval = seconds
        self._settings.setValue("server/pingInterval", seconds)
        if seconds:
            self._ping_timer.start(seconds * 1000)
            self._append_activity(f"Automatic ping: every {seconds} seconds")
        else:
            self._ping_timer.stop()
            self._append_activity("Automatic ping: off")
        self.connection_settings_changed.emit()
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
        self._ping_timer.stop()
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

    @Slot()
    def logout(self) -> None:
        from thlib.environment import env_server

        self._ping_timer.stop()
        self._active_request_id = ""
        self._project_request_id = ""
        env_server.set_ticket(None)
        env_server.save_defaults()
        self.project_model.replace([])
        self.navigation_model.replace([])
        self.section_model.replace([])
        self.workspace_model.clear()
        self.versions_model.clear()
        self.workspace_state.clear_selection()
        self._sessions.clear()
        self._current_section_key = ""
        self._current_project_code = ""
        self._current_project_title = ""
        self._current_user_initials = ""
        self._authentication_busy = False
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
        self.authentication_changed.emit()
        self._set_loading(True, "Generating a new TACTIC ticket")
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(
                self._authenticate_task, login, password
            )
            worker.result.connect(self._authentication_result)
            worker.error.connect(self._authentication_error_result)
            worker.start()
        except Exception as error:
            self._authentication_busy = False
            self._authentication_error = str(error)
            self.authentication_changed.emit()
            self._set_loading(False, f"Authentication failed | {error}")
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
        env_server.set_user(login)
        env_server.set_ticket(ticket)
        env_server.save_defaults()
        self._settings.setValue("server/lastLogin", login)
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
    @Slot(object)
    def _authentication_error_result(self, error) -> None:
        payload, _worker = error
        raw_message = str(payload.get("exception") or error)
        lowered = raw_message.lower()
        if self.debug_log:
            self.debug_log.log(
                "EXCEPTION",
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
        else:
            message = "Authentication failed. See Debug Log for details."
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
    def apply_server_configuration(
        self, server_url: str, preset_name: str,
        preserve_values: bool = False,
    ) -> None:
        server_url = str(server_url or "").strip().rstrip("/")
        if server_url.lower().endswith("/tactic"):
            server_url = server_url[:-7].rstrip("/")
        preset_name = str(preset_name or "").strip()
        if not server_url.startswith(("http://", "https://")):
            self._notify("Server address must start with http:// or https://")
            return
        from thlib.environment import cfg_controls, env_server, env_tactic

        self._cancel_bootstrap()
        presets = env_server.get_server_presets().get("presets_list", [])
        if preset_name not in presets:
            self._notify("Select an existing server preset")
            return
        env_server.set_cur_srv_preset(preset_name)
        env_server.save_server_presets_defaults()
        env_server.load_current_preset(preserve_values)
        cfg_controls.reset()
        env_tactic.reset()
        env_server.set_server(server_url)
        env_server.set_ticket(None)
        env_server.save_defaults()
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
