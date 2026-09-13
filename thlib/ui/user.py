from __future__ import annotations

import uuid
from pathlib import Path

from PySide6.QtCore import QObject, Property, Qt, QUrl, Signal, Slot

from thlib.ui.workspace_models.records import RecordListModel
from thlib.ui.group_authority import primary_group, ranked_groups
from thlib.ui.activity import (
    JOURNAL_ACTIVITY_KINDS,
    activity_record,
    present_activity_records,
)
from thlib.ui.user_identity import (
    user_avatar_color,
    user_avatar_file_candidates,
    user_initials,
)


class UserController(QObject):
    stateChanged = Signal()
    heartbeatIntervalChanged = Signal(int)
    profileSaved = Signal()
    avatarQueued = Signal()
    avatarsChanged = Signal()

    def __init__(self, application, parent=None) -> None:
        super().__init__(parent or application)
        self._application = application
        self._settings = application._settings
        self._heartbeat_interval = int(
            self._settings.get("network/presenceHeartbeatInterval", 120)
            or 120
        )
        if self._heartbeat_interval not in {30, 60, 120, 300}:
            self._heartbeat_interval = 120
        self._selected_login = ""
        self._directory_visible = False
        self._profile = {}
        self._busy = False
        self._error = ""
        self._activity_error = ""
        self._presence_by_login = {}
        self._request_id = ""
        self._worker = None
        self._loading_scope = None
        self._loaded_scope = None
        self._queued_refresh = False
        self._edit_worker = None
        self._edit_busy = False
        self._edit_error = ""
        self._checkin_controller = None
        self._tasks_controller = None
        self._skey_previews = None
        self._activity_feed = None
        self._task_summary = self._empty_task_summary()
        self._work_hour_summary = self._empty_work_hour_summary()
        self._can_view_work_hours = False
        self._task_status_summary = []
        self._task_process_summary = []
        self._pending_avatar_paths: set[str] = set()
        self.users = RecordListModel((
            "login", "displayName", "initials", "email", "avatarUrl",
            "avatarColor", "groups",
            "primaryGroup", "current", "selected", "presenceKnown", "online",
            "lastSeen",
        ))
        self.activity = RecordListModel((
            "searchKey", "targetSearchKey", "targetTitle", "targetType",
            "targetTypeTitle",
            "kind", "title", "detail", "actor", "actorLabel",
            "actorAvatar", "actorInitials", "actorColor", "timestamp", "timestampPretty",
            "timestampFull", "itemCode", "itemTitle", "pipelineCode",
            "typeColor", "processColor", "project", "process",
            "context", "version", "statusBefore", "statusAfter",
            "statusBeforeColor", "statusAfterColor", "changes",
            "taskCode", "serverGenerated", "itemType", "itemTypeTitle",
            "itemTypeColor", "relationAction", "hours", "workDay",
            "workDayPretty", "workHourAction", "workHourCategory",
            "workHourStatus", "workHourOwner",
        ))
        self.groups = RecordListModel((
            "code", "label", "description", "member", "accessLevel",
            "projectCode", "isDefault",
        ))
        application._registry.register("show_user_profile", self.open_current)
        application._registry.register("show_users", self.open_users)
        application._registry.register(
            "show_user_activity", self.open_current
        )
        application._registry.register("sign_out", self.logout)
        application.server_state_changed.connect(self._application_changed)
        application.project_changed.connect(self._project_changed)
        application.authentication_changed.connect(self._application_changed)
        application.repository_sync.task_finished.connect(
            self._repository_file_ready
        )
        self._rebuild()
        # Presence is normally carried by ServerUpdateService's batched poll.
        # Keep the timer stopped so opening the user UI cannot create a second
        # periodic server request.

    def attach_tasks_controller(self, controller) -> None:
        if self._tasks_controller is controller:
            return
        self._tasks_controller = controller

    @Property(int, notify=stateChanged)
    def heartbeat_interval(self) -> int:
        return self._heartbeat_interval

    @Slot(int)
    def set_heartbeat_interval(self, seconds: int) -> None:
        seconds = int(seconds)
        if seconds not in {30, 60, 120, 300}:
            return
        if self._heartbeat_interval == seconds:
            return
        self._heartbeat_interval = seconds
        self._settings["network/presenceHeartbeatInterval"] = seconds
        self._application._write_settings()
        self.heartbeatIntervalChanged.emit(seconds)
        self.stateChanged.emit()

    def attach_checkin_controller(self, controller) -> None:
        self._checkin_controller = controller

    def attach_skey_previews(self, resolver) -> None:
        self._skey_previews = resolver

    def attach_activity_feed(self, controller) -> None:
        self._activity_feed = controller

    @Slot()
    def open_full_activity(self) -> None:
        login = str(
            self._profile.get("login")
            or self._selected_login
            or self._current_login()
        ).strip()
        if not login or self._activity_feed is None:
            return
        self._activity_feed.select_user_feed(login)
        self._application.window_model.show_window("activity_feed")

    @Slot(str)
    def open_activity(self, search_key: str) -> None:
        search_key = str(search_key or "").strip()
        if not search_key:
            return
        if self._skey_previews is not None:
            record = next((
                item for item in self.activity._records
                if str(item.get("searchKey") or "") == search_key
            ), {})
            process = str(record.get("process") or "").strip()
            if not process:
                process = str(record.get("context") or "").partition("/")[0]
            self._skey_previews.open_in_context(
                search_key,
                str(record.get("targetSearchKey") or ""),
                process,
            )
        else:
            self._application.open_search_key(search_key)

    @Slot(str)
    def open_activity_target(self, search_key: str) -> None:
        search_key = str(search_key or "").strip()
        if search_key:
            self._application.open_search_key(search_key)

    @Slot(str, str, str)
    def open_task_activity(
            self, search_key: str, task_code: str, process: str) -> None:
        search_key = str(search_key or "").strip()
        if search_key and self._tasks_controller is not None:
            self._tasks_controller.open_object_context(
                search_key, str(task_code or ""), str(process or "")
            )

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def activityError(self) -> str:
        return self._activity_error

    @Property(bool, notify=stateChanged)
    def editingBusy(self) -> bool:
        return self._edit_busy

    @Property(str, notify=stateChanged)
    def editingError(self) -> str:
        return self._edit_error

    @Property(bool, notify=stateChanged)
    def canManageUsers(self) -> bool:
        current = self._current_login()
        if current.lower() == "admin":
            return True
        login_object = self._login_object(current)
        return any(
            code == "admin" or "supervisor" in code
            for code in (
                str(group.get("code") or "").lower()
                for group in self._group_records(login_object)
            )
        )

    @Property(bool, notify=stateChanged)
    def canEdit(self) -> bool:
        return bool(
            self._profile.get("login")
            and (self._profile.get("current") or self.canManageUsers)
        )

    @Property(bool, notify=stateChanged)
    def directoryVisible(self) -> bool:
        return self._directory_visible

    @Property(bool, notify=stateChanged)
    def tasksBusy(self) -> bool:
        return self._busy

    @staticmethod
    def _empty_task_summary() -> dict:
        return {
            "total": 0,
            "incomplete": 0,
            "overdue": 0,
            "dueThisWeek": 0,
        }

    @staticmethod
    def _empty_work_hour_summary() -> dict:
        return {
            "loggedHours": 0.0,
            "approvedHours": 0.0,
            "pendingHours": 0.0,
            "periodStart": "",
            "periodEnd": "",
        }

    @Property("QVariantMap", notify=stateChanged)
    def taskSummary(self) -> dict:
        return dict(self._task_summary)

    @Property("QVariantMap", notify=stateChanged)
    def workHourSummary(self) -> dict:
        return dict(self._work_hour_summary)

    @Property(bool, notify=stateChanged)
    def canViewWorkHours(self) -> bool:
        return self._can_view_work_hours

    @Property("QVariantList", notify=stateChanged)
    def taskStatusSummary(self) -> list:
        return [dict(item) for item in self._task_status_summary]

    @Property("QVariantList", notify=stateChanged)
    def taskProcessSummary(self) -> list:
        return [dict(item) for item in self._task_process_summary]

    @Property("QVariantMap", notify=stateChanged)
    def profile(self) -> dict:
        return dict(self._profile)

    @Property(str, notify=stateChanged)
    def login(self) -> str:
        return self._current_login()

    def _current_user_record(self) -> dict:
        login = self.login
        return next((
            record for record in self.users._records
            if str(record.get("login") or "") == login
        ), {})

    @Property(str, notify=stateChanged)
    def displayName(self) -> str:
        return str(self._current_user_record().get("displayName")
                   or self.login or "User")

    @Property(str, notify=stateChanged)
    def initials(self) -> str:
        return str(
            self._current_user_record().get("initials")
            or self._initials(self.displayName)
        )

    @Property(str, notify=stateChanged)
    def avatarColor(self) -> str:
        return str(
            self._current_user_record().get("avatarColor")
            or user_avatar_color(self.login)
        )

    @Property(str, notify=stateChanged)
    def avatarUrl(self) -> str:
        return str(self._current_user_record().get("avatarUrl") or "")

    @staticmethod
    def _current_login() -> str:
        from thlib.environment import env_server
        if not env_server.get_ticket():
            return ""
        return str(env_server.get_user() or "")

    @staticmethod
    def _login_object(login: str):
        from thlib.environment import env_inst
        return (env_inst.get_all_logins() or {}).get(str(login or ""))

    @staticmethod
    def _info(login_object) -> dict:
        if not login_object:
            return {}
        try:
            return dict(login_object.get_info() or {})
        except (AttributeError, TypeError, ValueError):
            return {}

    @staticmethod
    def _initials(value: str) -> str:
        return user_initials(value)

    @classmethod
    def _present_activity_records(
            cls, sources, users, profile: dict | None = None
    ) -> list[dict]:
        return present_activity_records(sources, users, profile)

    def _refresh_activity_identities(self) -> None:
        current = [dict(record) for record in self.activity._records]
        presented = self._present_activity_records(
            current, self.users._records, self._profile
        )
        if presented != current:
            self.activity.replace(presented)

    @classmethod
    def _display_name(cls, login_object, login: str) -> str:
        try:
            value = login_object.get_display_name()
        except (AttributeError, KeyError, TypeError):
            value = ""
        info = cls._info(login_object)
        name = ' '.join(str(info.get(key) or '').strip()
                        for key in ('first_name', 'last_name')).strip()
        return str(value or name or login or "User")

    @staticmethod
    def _group_records(login_object) -> list[dict]:
        try:
            groups = login_object.get_login_groups() or []
        except (AttributeError, KeyError, TypeError):
            groups = []
        records = []
        for group in groups:
            try:
                code = str(group.get_login_group() or group.get_code() or "")
                label = str(group.get_pretty_name() or code)
                info = dict(group.get_info() or {})
            except (AttributeError, KeyError, TypeError):
                continue
            if code:
                subgroups = info.get("sub_groups") or []
                if isinstance(subgroups, str):
                    subgroups = [
                        value.strip() for value in subgroups.split(",")
                        if value.strip()
                    ]
                records.append({
                    "code": code,
                    "label": label,
                    "accessLevel": str(info.get("access_level") or ""),
                    "accessRules": str(info.get("access_rules") or ""),
                    "projectCode": str(info.get("project_code") or ""),
                    "isDefault": bool(info.get("is_default")),
                    "subGroups": list(subgroups or []),
                })
        return records

    @staticmethod
    def _roles(info: dict) -> list[str]:
        value = info.get("roles")
        if value in (None, ""):
            value = info.get("role")
        if isinstance(value, (list, tuple, set)):
            values = value
        elif value:
            values = str(value).replace("|", ",").split(",")
        else:
            values = ()
        return [str(item).strip() for item in values if str(item).strip()]

    def _avatar_url(self, login_object) -> str:
        if not login_object:
            return ""
        for candidate in user_avatar_file_candidates(login_object):
            try:
                local_path = str(candidate.get_full_abs_path() or "")
            except (AttributeError, KeyError, TypeError):
                local_path = ""
            if local_path and candidate.is_local_current():
                return QUrl.fromLocalFile(
                    str(Path(local_path).resolve())
                ).toString()
            repository_sync = self._application.repository_sync
            if (
                local_path
                and repository_sync.previews_through_http_enabled()
            ):
                try:
                    repository_sync.schedule_file_object(
                        candidate,
                        process="preview",
                        auto_start=True,
                        is_ui_preview=True,
                    )
                except (AttributeError, TypeError, ValueError):
                    continue
                self._pending_avatar_paths.add(
                    str(Path(local_path).resolve())
                )
                return ""
        return ""

    def identity_record(self, login: str, login_object) -> dict:
        """Project one native Login through the shared avatar/identity path."""
        name = self._display_name(login_object, login)
        return {
            "login": login, "displayName": name,
            "initials": user_initials(name, login),
            "avatarUrl": self._avatar_url(login_object),
            "avatarColor": user_avatar_color(login),
        }

    def _profile_record(self, login: str, login_object) -> dict:
        info = self._info(login_object)
        groups = ranked_groups(
            self._group_records(login_object),
            str(self._application._current_project_code or ""),
        )
        contact = ""
        for key in ("phone_number", "phone", "telephone", "mobile"):
            if info.get(key):
                contact = str(info[key])
                break
        return {
            **self.identity_record(str(login or ""), login_object),
            "email": str(info.get("email") or ""),
            "contact": contact,
            "address": str(info.get("address") or ""),
            "firstName": str(info.get("first_name") or ""),
            "lastName": str(info.get("last_name") or ""),
            "phoneNumber": str(
                info.get("phone_number") or contact or ""
            ),
            "department": str(info.get("department") or ""),
            "upn": str(info.get("upn") or ""),
            "namespace": str(info.get("namespace") or ""),
            "status": str(info.get("s_status") or ""),
            "accountProject": str(info.get("project_code") or ""),
            "licenseType": str(info.get("license_type") or ""),
            "hourlyWage": str(info.get("hourly_wage") or ""),
            "groups": groups,
            "loginGroup": str(
                primary_group(
                    groups,
                    str(self._application._current_project_code or ""),
                ).get("label") or ""
            ),
            "roles": self._roles(info),
        }

    def _presence(self, login: str, current_login: str,
                  connection: str) -> dict:
        record = dict(self._presence_by_login.get(str(login or "")) or {})
        if record:
            return {
                "presenceKnown": True,
                "online": bool(record.get("online")),
                "lastSeen": str(record.get("lastSeen") or ""),
            }
        is_current = bool(login) and login == current_login
        return {
            "presenceKnown": is_current,
            "online": is_current and connection == "online",
            "lastSeen": "",
        }

    def _rebuild(self) -> None:
        from thlib.environment import env_inst

        current = self._current_login()
        records = []
        for login, login_object in sorted(
                (env_inst.get_all_logins() or {}).items(),
                key=lambda item: self._display_name(
                    item[1], str(item[0])
                ).lower()):
            profile = self._profile_record(str(login), login_object)
            presence = self._presence(
                str(login), current, self._application.server_state
            )
            records.append({
                "login": profile["login"],
                "displayName": profile["displayName"],
                "initials": profile["initials"],
                "email": profile["email"],
                "avatarUrl": profile["avatarUrl"],
                "avatarColor": profile["avatarColor"],
                "groups": [group["label"] for group in profile["groups"]],
                "primaryGroup": str(
                    profile.get("loginGroup") or "Ungrouped"
                ),
                "current": str(login) == current,
                "selected": str(login) == self._selected_login,
                **presence,
            })
        self.users.replace(sorted(
            records,
            key=lambda record: (
                str(record.get("primaryGroup") or "").casefold(),
                str(record.get("displayName") or "").casefold(),
            ),
        ))
        selected = self._selected_login or current
        login_object = (env_inst.get_all_logins() or {}).get(selected)
        self._profile = self._profile_record(selected, login_object)
        self._profile.update({
            "current": selected == current,
            "project": self._application._current_project_title,
            "projectCode": self._application._current_project_code,
            "server": self._application.server_url,
            "connection": self._application.server_state,
            **self._presence(
                selected, current, self._application.server_state
            ),
        })
        self._rebuild_groups(login_object)
        self._refresh_activity_identities()
        self.stateChanged.emit()

    def _rebuild_groups(self, login_object) -> None:
        if not login_object:
            self.groups.clear()
            return
        member_codes = {
            str(group.get("code") or "")
            for group in self._group_records(login_object)
        }
        try:
            available = login_object.get_all_login_groups() or []
        except (AttributeError, KeyError, TypeError):
            available = []
        records = []
        for group in available:
            try:
                code = str(group.get_login_group() or group.get_code() or "")
                label = str(group.get_pretty_name() or code)
                description = str(group.get_description() or "")
                info = dict(group.get_info() or {})
            except (AttributeError, KeyError, TypeError):
                continue
            if code:
                records.append({
                    "code": code,
                    "label": label,
                    "description": description,
                    "member": code in member_codes,
                    "accessLevel": str(info.get("access_level") or ""),
                    "projectCode": str(info.get("project_code") or ""),
                    "isDefault": bool(info.get("is_default")),
                })
        self.groups.replace(sorted(
            records, key=lambda item: item["label"].casefold()
        ))

    @Slot(str, str)
    def _repository_file_ready(self, _task_id: str, local_path: str) -> None:
        if not self._pending_avatar_paths:
            return
        resolved = str(Path(local_path).resolve())
        if resolved not in self._pending_avatar_paths:
            return
        self._pending_avatar_paths.discard(resolved)
        self._rebuild()
        self.avatarsChanged.emit()

    def _application_changed(self, *_args) -> None:
        if self._application.server_state != "online":
            self.activity.clear()
            self._presence_by_login.clear()
        self._rebuild()

    @Slot(object)
    def apply_server_batch(self, batch) -> None:
        if not isinstance(batch, dict):
            return
        presence = batch.get("presence")
        if presence is None:
            return
        self._presence_ready(presence)

    @Slot(object)
    def _presence_ready(self, result) -> None:
        values = result[0] if isinstance(result, tuple) else result
        self._presence_by_login = {
            str(record.get("login") or ""): dict(record)
            for record in (values or [])
            if isinstance(record, dict) and record.get("login")
        }
        self._rebuild()

    def _project_changed(self, *_args) -> None:
        self._rebuild()
        if any(
                self._application.window_model.is_window_visible(window_id)
                for window_id in ("user_profile", "users")):
            self.refresh()

    @Slot()
    def open_current(self) -> None:
        self._show_profile(self._current_login(), directory_visible=False)

    @Slot()
    def open_users(self) -> None:
        self._show_profile(
            self._selected_login or self._current_login(),
            directory_visible=True,
        )

    @Slot(str)
    def open_profile(self, login: str) -> None:
        self._show_profile(login, directory_visible=False)

    @Slot(str)
    def select_profile(self, login: str) -> None:
        self._show_profile(login, directory_visible=True)

    def _show_profile(self, login: str, *, directory_visible: bool) -> None:
        login = str(login or "").strip()
        if not login:
            self._application.request_authentication()
            return
        self._directory_visible = bool(directory_visible)
        self._selected_login = login
        self._rebuild()
        window_id = "users" if directory_visible else "user_profile"
        other_window_id = "user_profile" if directory_visible else "users"
        # These are two presentation modes of the same controller. Keep only
        # one mode visible so its shared selection cannot repaint the other,
        # while the window model still persists their geometry independently.
        self._application.window_model.close_window(other_window_id)
        self._application.window_model.show_window(window_id)
        self.refresh()

    @Slot()
    def window_opened(self) -> None:
        if not self._selected_login:
            self._selected_login = self._current_login()
        self._rebuild()
        self.refresh()

    @Slot()
    def refresh(self) -> None:
        login = self._selected_login or self._current_login()
        project_code = self._application._current_project_code
        if (
                not login or not project_code
                or self._application.server_state != "online"):
            return
        scope = (str(login), str(project_code))
        if self._busy:
            if scope != self._loading_scope:
                self._queued_refresh = True
            return
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._loading_scope = scope
        if scope != self._loaded_scope:
            self.activity.clear()
            self._task_summary = self._empty_task_summary()
            self._work_hour_summary = self._empty_work_hour_summary()
            self._can_view_work_hours = False
            self._task_status_summary = []
            self._task_process_summary = []
        self._busy = True
        self._error = ""
        self._activity_error = ""
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(
            self._load_related, login, project_code
        )
        self._worker = worker
        worker.result.connect(
            lambda result: self._loaded(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @staticmethod
    def _objects(result) -> list:
        values = result[0] if isinstance(result, tuple) else result
        if isinstance(values, dict):
            return list(values.values())
        return list(values or [])

    @classmethod
    def _load_related(cls, login: str, project_code: str) -> dict:
        import thlib.tactic_classes as tc
        from thlib.environment import env_inst

        payload = dict(tc.get_user_profile_data(
            login, project_code=project_code
        ) or {})
        activity_payload = tc.get_user_recent_activity(
            "",
            project_code=project_code,
            limit=25,
            offset=0,
            kinds=JOURNAL_ACTIVITY_KINDS,
            logins=[login],
        )
        activity_values = (
            activity_payload.get("records") or ()
            if isinstance(activity_payload, dict)
            else activity_payload or ()
        )
        projects = getattr(env_inst, "projects", None) or {}
        project = projects.get(project_code)
        activity_records = [
            activity_record(
                info, default_actor=login, default_project=project_code
            )
            for info in activity_values
        ]
        def styled_summary(values, color_key):
            records = []
            for value in values or []:
                value = dict(value or {})
                style = cls._workflow_task_style(value, project)
                records.append({
                    "label": str(value.get("label") or "Unspecified"),
                    "count": int(value.get("count") or 0),
                    "color": str(style.get(color_key) or ""),
                })
            return records

        return {
            "activity": activity_records,
            "activityError": "",
            "activityTraceback": "",
            "taskSummary": dict(payload.get("taskSummary") or {}),
            "workHourSummary": dict(payload.get("workHourSummary") or {}),
            "canViewWorkHours": bool(
                (payload.get("permissions") or {}).get("viewWorkHours")
            ),
            "statusSummary": styled_summary(
                payload.get("statusSummary"), "statusColor"
            ),
            "processSummary": styled_summary(
                payload.get("processSummary"), "processColor"
            ),
            "taskError": "",
            "taskTraceback": "",
        }

    @staticmethod
    def _workflow_task_style(info, project):
        """Resolve task labels/colors from the loaded project workflow."""
        info = dict(info or {})
        process = str(info.get("process") or "")
        status = str(info.get("status") or "")
        task_pipeline_code = str(info.get("pipeline_code") or "")
        task_search_type = str(
            info.get("search_type") or ""
        ).split("?", 1)[0]
        result = {
            "processLabel": process,
            "processColor": "",
            "statusColor": "",
        }
        if project is None:
            return result

        try:
            workflow = project.get_workflow()
            task_pipeline = (
                workflow.get_by_pipeline_code(
                    "sthpw/task", task_pipeline_code
                ) if task_pipeline_code else None
            )
            status_info = (
                task_pipeline.pipeline.get(status)
                if task_pipeline and status else None
            ) or {}
            result["statusColor"] = str(status_info.get("color") or "")
        except (AttributeError, KeyError, TypeError):
            pass

        best_score = -1
        try:
            stypes = (project.get_stypes() or {}).values()
        except AttributeError:
            stypes = ()
        for stype in stypes:
            try:
                stype_code = str(stype.get_code() or "")
                pipelines = (stype.get_pipeline() or {}).values()
            except AttributeError:
                continue
            for pipeline in pipelines:
                try:
                    process_info = dict(
                        pipeline.get_process_info(process) or {}
                    )
                    process_object = dict(
                        pipeline.get_pipeline_process(process) or {}
                    )
                except (AttributeError, TypeError, ValueError):
                    continue
                if not process_info and not process_object:
                    continue
                workflow_info = dict(
                    process_object.get("workflow") or {}
                )
                properties = dict(workflow_info.get("properties") or {})
                configured_task_pipeline = str(
                    process_info.get("task_pipeline")
                    or properties.get("task_pipeline") or ""
                )
                score = 0
                if task_search_type and stype_code == task_search_type:
                    score += 2
                if (
                        task_pipeline_code and configured_task_pipeline
                        == task_pipeline_code):
                    score += 4
                if score < best_score:
                    continue
                best_score = score
                result["processLabel"] = str(
                    process_info.get("label")
                    or process_info.get("name") or process
                )
                result["processColor"] = str(
                    process_info.get("color")
                    or process_object.get("color") or ""
                )
        if not result["statusColor"]:
            result["statusColor"] = result["processColor"]
        return result

    def _loaded(self, request_id: str, result) -> None:
        if request_id != self._request_id:
            return
        values = result[0] if isinstance(result, tuple) else result
        values = dict(values or {})
        activity_records = self._present_activity_records(
            values.get("activity") or [], self.users._records, self._profile
        )
        self.activity.replace(activity_records)
        if self._skey_previews is not None:
            self._skey_previews.request_many([
                str(record.get("searchKey") or "")
                for record in activity_records
                if record.get("searchKey")
            ])
        self._task_summary = self._empty_task_summary()
        self._task_summary.update(dict(values.get("taskSummary") or {}))
        self._work_hour_summary = self._empty_work_hour_summary()
        self._work_hour_summary.update(
            dict(values.get("workHourSummary") or {})
        )
        self._can_view_work_hours = bool(values.get("canViewWorkHours"))
        self._task_status_summary = sorted(
            (dict(item) for item in values.get("statusSummary") or []),
            key=lambda item: (
                -int(item.get("count") or 0),
                str(item.get("label") or ""),
            ),
        )[:6]
        self._task_process_summary = sorted(
            (dict(item) for item in values.get("processSummary") or []),
            key=lambda item: (
                -int(item.get("count") or 0),
                str(item.get("label") or ""),
            ),
        )[:6]
        self._loaded_scope = self._loading_scope
        self._error = str(values.get("taskError") or "")
        if self._error and self._application.debug_log:
            self._application.debug_log.log(
                "WARNING",
                f"User task summary is unavailable: {self._error}",
                group="user/tasks",
                source="UserController",
                stacktrace=str(values.get("taskTraceback") or ""),
                caller=2,
            )
        self._activity_error = str(values.get("activityError") or "")
        if self._activity_error and self._application.debug_log:
            self._application.debug_log.log(
                "WARNING",
                f"User activity is unavailable: {self._activity_error}",
                group="user/activity",
                source="UserController",
                stacktrace=str(values.get("activityTraceback") or ""),
                caller=2,
            )
        self._finish()

    def _failed(self, request_id: str, error) -> None:
        if request_id != self._request_id:
            return
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        self._error = str(payload or "Could not load user profile")
        if self._application.debug_log:
            self._application.debug_log.raise_error(
                payload, stacktrace=stacktrace, group="user/profile"
            )
        self._finish()

    def _finish(self) -> None:
        self._busy = False
        self._worker = None
        self._loading_scope = None
        self.stateChanged.emit()
        if self._queued_refresh:
            self._queued_refresh = False
            self.refresh()

    def _start_profile_mutation(
            self, values: dict, password: str = "", groups=None,
            group_access_levels=None) -> bool:
        login = str(self._profile.get("login") or "")
        if (
                self._edit_busy or not login or not self.canEdit
                or ((groups is not None or group_access_levels is not None)
                    and not self.canManageUsers)):
            return False
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        self._edit_busy = True
        self._edit_error = ""
        self.stateChanged.emit()

        def operation():
            import thlib.tactic_classes as tc
            return tc.mutate_user_profile(
                login, values=values, password=password, groups=groups,
                group_access_levels=group_access_levels,
            )

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._edit_busy = False
            self._edit_error = "Server worker pool is unavailable"
            self.stateChanged.emit()
            return False
        self._edit_worker = worker
        worker.result.connect(
            lambda result: self._profile_mutated(
                login, groups, group_access_levels, result
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._profile_mutation_failed,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        return True

    @Slot("QVariantMap", "QVariantList", result=bool)
    def create_user(self, values: dict, groups: list) -> bool:
        if self._edit_busy or not self.canManageUsers:
            return False
        payload = dict(values or {})
        login = str(payload.pop("login", "") or "").strip()
        password = str(payload.pop("password", "") or "")
        if not login:
            self._edit_error = "A login is required"
            self.stateChanged.emit()
            return False
        allowed = {
            "first_name", "last_name", "display_name", "email",
            "phone_number", "address", "department", "upn", "namespace",
            "s_status",
            "project_code", "license_type", "hourly_wage",
        }
        payload = {
            key: value for key, value in payload.items() if key in allowed
        }
        selected_groups = [
            str(value or "") for value in (groups or []) if value
        ]
        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        self._edit_busy = True
        self._edit_error = ""
        self.stateChanged.emit()

        def operation():
            import thlib.tactic_classes as tc
            result = tc.create_user_profile(
                login, values=payload, password=password,
                groups=selected_groups,
            )
            tc.get_all_projects_and_logins(force=True)
            return result

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._edit_busy = False
            self._edit_error = "Server worker pool is unavailable"
            self.stateChanged.emit()
            return False
        self._edit_worker = worker
        worker.result.connect(
            lambda result: self._user_created(login, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._profile_mutation_failed,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        return True

    @Slot("QVariantMap", result=bool)
    def save_profile(self, values: dict) -> bool:
        payload = dict(values or {})
        password = str(payload.pop("password", "") or "")
        allowed = {
            "first_name", "last_name", "display_name", "email",
            "phone_number", "address", "department",
        }
        if self.canManageUsers:
            allowed.update({
                "upn", "namespace", "s_status", "project_code",
                "license_type", "hourly_wage",
            })
        payload = {
            key: value for key, value in payload.items() if key in allowed
        }
        return self._start_profile_mutation(payload, password=password)

    @Slot("QVariantList", result=bool)
    def save_groups(self, groups: list) -> bool:
        return self._start_profile_mutation(
            {}, groups=[str(value or "") for value in (groups or []) if value]
        )

    @Slot("QVariantList", "QVariantMap", result=bool)
    def save_group_settings(self, groups: list, access_levels: dict) -> bool:
        normalized_levels = {
            str(code or "").strip(): str(level or "").strip()
            for code, level in dict(access_levels or {}).items()
            if str(code or "").strip()
        }
        return self._start_profile_mutation(
            {},
            groups=[str(value or "") for value in (groups or []) if value],
            group_access_levels=normalized_levels,
        )

    def _profile_mutated(
            self, login: str, groups, group_access_levels, result) -> None:
        values = result[0] if isinstance(result, tuple) else result
        values = dict(values or {})
        login_object = self._login_object(login)
        if login_object is not None:
            info = self._info(login_object)
            info.update({
                key: value for key, value in values.items()
                if key not in {"password", "groups", "group_access_levels"}
            })
            login_object.info.update(info)
            if groups is not None:
                memberships = getattr(login_object, "login_in_groups", None)
                if isinstance(memberships, list):
                    memberships[:] = [
                        item for item in memberships
                        if str(item.get("login") or "") != login
                    ]
                    memberships.extend({
                        "login": login, "login_group": str(group)
                    } for group in groups)
            if group_access_levels is not None:
                try:
                    all_groups = login_object.get_all_login_groups() or []
                except (AttributeError, KeyError, TypeError):
                    all_groups = []
                for group_object in all_groups:
                    try:
                        code = str(
                            group_object.get_login_group()
                            or group_object.get_code() or ""
                        )
                        if code in group_access_levels:
                            group_object.get_info()["access_level"] = str(
                                group_access_levels[code] or ""
                            )
                    except (AttributeError, KeyError, TypeError):
                        continue
        self._edit_worker = None
        self._edit_busy = False
        self._edit_error = ""
        self._rebuild()
        self.profileSaved.emit()

    def _user_created(self, login: str, _result) -> None:
        self._edit_worker = None
        self._edit_busy = False
        self._edit_error = ""
        self._selected_login = login
        self._rebuild()
        self.refresh()
        self.profileSaved.emit()

    def _profile_mutation_failed(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        self._edit_worker = None
        self._edit_busy = False
        self._edit_error = str(payload or "Could not update user profile")
        if self._application.debug_log:
            self._application.debug_log.raise_error(
                self._edit_error,
                stacktrace=stacktrace,
                group="user/profile-edit",
            )
        self.stateChanged.emit()

    @Slot(QUrl, result=bool)
    def queue_avatar(self, value: QUrl) -> bool:
        controller = self._checkin_controller
        login = str(self._profile.get("login") or "")
        login_object = self._login_object(login)
        path = Path(
            value.toLocalFile() if value.isLocalFile() else value.toString()
        )
        if controller is None or login_object is None or not self.canEdit:
            return False
        try:
            path = path.resolve(strict=True)
        except OSError as error:
            self._edit_error = str(error)
            self.stateChanged.emit()
            return False
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            self._edit_error = "Choose a JPG, PNG, or WEBP image"
            self.stateChanged.emit()
            return False
        try:
            controller.prepare_external_checkin(
                login_object.get_search_key(), login_object, "sthpw",
                str(self._profile.get("displayName") or login),
                login_object.get_code(), "icon",
                "User avatar", [str(path)], update_versionless=True,
                queue_when_ready=True,
            )
        except Exception as error:
            self._edit_error = str(error)
            self.stateChanged.emit()
            return False
        self._edit_error = ""
        self.stateChanged.emit()
        self.avatarQueued.emit()
        return True

    @Slot()
    def logout(self) -> None:
        self._application.window_model.close_window("user_profile")
        self._application.window_model.close_window("users")
        self._application.logout()
        self._selected_login = ""
        self.activity.clear()
        self._task_summary = self._empty_task_summary()
        self._work_hour_summary = self._empty_work_hour_summary()
        self._can_view_work_hours = False
        self._task_status_summary = []
        self._task_process_summary = []
        self._rebuild()
