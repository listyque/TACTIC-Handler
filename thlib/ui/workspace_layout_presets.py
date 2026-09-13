"""Project-owned presets for the existing workspace dock layout."""

from __future__ import annotations

import json
import traceback
import uuid
from xml.etree import ElementTree

from PySide6.QtCore import QObject, Property, Signal, Slot

from .workspace_models.records import RecordListModel


WORKSPACE_LAYOUT_CATEGORY = "workspace_layout"
WORKSPACE_LAYOUT_SEARCH_TYPE = "SideBarWdg"
WORKSPACE_LAYOUT_VIEW_PREFIX = "workspace_layout@"


def layout_configuration_from_xml(value: object, view: str) -> dict:
    """Read one exact WidgetDbConfig named-view payload."""
    root = ElementTree.fromstring(str(value or ""))
    if root.tag != "config":
        raise ValueError("Workspace layout configuration must have a config root")
    view_node = next(
        (
            node for node in root.findall("view")
            if str(node.get("name") or "") == view
        ),
        None,
    )
    values = view_node.find("values") if view_node is not None else None
    if values is None or not str(values.text or "").strip():
        raise ValueError("Workspace layout configuration values are missing")
    result = json.loads(values.text)
    if not isinstance(result, dict) or set(result) != {"panels", "layout"}:
        raise ValueError("Workspace layout configuration has an invalid shape")
    if not isinstance(result["panels"], list) or not isinstance(
        result["layout"], dict
    ):
        raise ValueError("Workspace layout panels or layout tree are invalid")
    return result


def layout_configuration_xml(configuration: dict, view: str) -> str:
    """Write the native named-view wrapper required by WidgetDbConfig."""
    root = ElementTree.Element("config")
    view_node = ElementTree.SubElement(root, "view", {"name": view})
    values = ElementTree.SubElement(view_node, "values", {"type": "json"})
    values.text = json.dumps(
        configuration, ensure_ascii=False, separators=(",", ":")
    )
    return ElementTree.tostring(root, encoding="unicode")


class WorkspaceLayoutPresetController(QObject):
    """Own shared layout-preset persistence and its in-memory projection."""

    stateChanged = Signal()
    presetsChanged = Signal(str)

    def __init__(self, application, users, dock_model, parent=None) -> None:
        super().__init__(parent)
        self._application = application
        self._users = users
        self._dock_model = dock_model
        self._project_code = ""
        self._project = None
        self._payloads: dict[str, dict] = {}
        self._busy = False
        self._error = ""
        self._active_view = ""
        self._generation = 0
        self._workers = set()
        self.presets = RecordListModel(
            (
                "code", "view", "title", "panelCount", "assignedCount",
                "valid", "error",
            ),
            identity_role="view",
        )
        try:
            application.project_changed.connect(self._project_changed)
        except (AttributeError, TypeError):
            pass
        try:
            users.stateChanged.connect(self.stateChanged.emit)
        except (AttributeError, TypeError):
            pass
        self.ensure_loaded()

    @Property(QObject, constant=True)
    def model(self):
        return self.presets

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def canManage(self) -> bool:
        try:
            return bool(self._users.canManageUsers)
        except (AttributeError, RuntimeError):
            return False

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def activeView(self) -> str:
        return self._active_view

    @Property("QVariantList", notify=stateChanged)
    def options(self) -> list[dict]:
        return [
            {"value": "", "label": self.tr("Do not change workspace layout")},
            *[
                {
                    "value": str(record.get("view") or ""),
                    "label": str(record.get("title") or ""),
                }
                for record in self.presets.records()
                if record.get("valid")
            ],
        ]

    def _current_project(self):
        project_code = str(
            getattr(self._application, "current_project_code", "") or ""
        )
        if not project_code:
            return "", None
        try:
            from thlib.environment import env_inst

            project = (env_inst.projects or {}).get(project_code)
        except (AttributeError, ImportError):
            project = None
        return project_code, project

    @Slot()
    def ensure_loaded(self) -> None:
        project_code, project = self._current_project()
        if (
            project_code == self._project_code
            and project is self._project
            and project is not None
        ):
            return
        self._adopt_project(project_code, project)

    @Slot()
    def reload_from_project(self) -> None:
        """Reproject already-loaded config after another editor saves it."""
        self.ensure_loaded()
        self._sync_from_project()

    def _adopt_project(self, project_code: str, project) -> None:
        self._generation += 1
        for worker in tuple(self._workers):
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        self._project_code = str(project_code or "")
        self._project = project
        self._active_view = ""
        self._error = ""
        self._sync_from_project()

    @Slot(str, str)
    def _project_changed(self, project_code: str, _title: str) -> None:
        try:
            from thlib.environment import env_inst

            project = (env_inst.projects or {}).get(str(project_code or ""))
        except (AttributeError, ImportError):
            project = None
        self._adopt_project(project_code, project)

    @staticmethod
    def _is_preset_record(record: dict) -> bool:
        return (
            str(record.get("category") or "") == WORKSPACE_LAYOUT_CATEGORY
            and str(record.get("search_type") or "")
            == WORKSPACE_LAYOUT_SEARCH_TYPE
            and str(record.get("view") or "").startswith(
                WORKSPACE_LAYOUT_VIEW_PREFIX
            )
            and not record.get("login")
        )

    def _project_records(self) -> list[dict]:
        try:
            views = self._project.get_config_views()
            return [dict(record) for record in (views.config_dict or [])]
        except (AttributeError, TypeError):
            return []

    @staticmethod
    def _sidebar_assignments(records: list[dict]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for record in records:
            if (
                str(record.get("search_type") or "") != "SideBarWdg"
                or str(record.get("category") or "")
                == WORKSPACE_LAYOUT_CATEGORY
            ):
                continue
            try:
                root = ElementTree.fromstring(str(record.get("config") or ""))
            except ElementTree.ParseError:
                continue
            for element in root.iter("element"):
                node = element.find("./display/layout_preset")
                view = str(node.text or "").strip() if node is not None else ""
                if view:
                    result.setdefault(view, []).append(
                        str(
                            element.get("title")
                            or element.get("name")
                            or view
                        )
                    )
        return result

    def _sync_from_project(self) -> None:
        records = self._project_records()
        assignments = self._sidebar_assignments(records)
        payloads = {}
        projected = []
        for record in records:
            if not self._is_preset_record(record):
                continue
            view = str(record.get("view") or "")
            valid = True
            error = ""
            try:
                payload = layout_configuration_from_xml(
                    record.get("config"), view
                )
            except (ElementTree.ParseError, TypeError, ValueError) as exception:
                valid = False
                error = str(exception)
                payload = {}
            if valid:
                payloads[view] = payload
            projected.append({
                "code": str(record.get("code") or ""),
                "view": view,
                "title": str(record.get("title") or self.tr("Untitled layout")),
                "panelCount": len(payload.get("panels") or ()),
                "assignedCount": len(assignments.get(view, ())),
                "valid": valid,
                "error": error,
            })
        projected.sort(key=lambda item: item["title"].casefold())
        self._payloads = payloads
        self.presets.replace(projected)
        if self._active_view not in payloads:
            self._active_view = ""
        self.stateChanged.emit()

    def _record(self, identity: str) -> dict:
        identity = str(identity or "")
        return next(
            (
                record for record in self.presets.records()
                if record.get("code") == identity
                or record.get("view") == identity
            ),
            {},
        )

    @Slot(str, result=bool)
    def apply_preset(self, identity: str) -> bool:
        return self._apply(identity, notify=True)

    def apply_assigned(self, view: str) -> bool:
        return self._apply(view, notify=False)

    def _apply(self, identity: str, *, notify: bool) -> bool:
        self.ensure_loaded()
        record = self._record(identity)
        view = str(record.get("view") or identity or "")
        payload = self._payloads.get(view)
        if not payload or not self._dock_model.apply_layout(payload):
            if notify:
                self._application._notify(self.tr(
                    "This workspace layout preset is unavailable or invalid"
                ))
            return False
        self._active_view = view
        self._error = ""
        self.stateChanged.emit()
        if notify:
            self._application._notify(
                self.tr("Workspace layout applied")
            )
        return True

    def _replace_project_record(self, saved: dict) -> None:
        if self._project is None:
            return
        try:
            views = self._project.get_config_views()
            current = list(views.config_dict or [])
        except AttributeError:
            return
        code = str(saved.get("code") or "")
        view = str(saved.get("view") or "")
        views.config_dict = [
            record for record in current
            if not (
                self._is_preset_record(record)
                and (
                    (code and str(record.get("code") or "") == code)
                    or str(record.get("view") or "") == view
                )
            )
        ] + [dict(saved)]

    def _remove_project_record(self, code: str, view: str) -> None:
        if self._project is None:
            return
        try:
            views = self._project.get_config_views()
            current = list(views.config_dict or [])
        except AttributeError:
            return
        views.config_dict = [
            record for record in current
            if not (
                self._is_preset_record(record)
                and (
                    (code and str(record.get("code") or "") == code)
                    or str(record.get("view") or "") == view
                )
            )
        ]

    @staticmethod
    def _query_server_records(server) -> list[dict]:
        records = server.query(
            "config/widget_config",
            [
                ("category", WORKSPACE_LAYOUT_CATEGORY),
                ("search_type", WORKSPACE_LAYOUT_SEARCH_TYPE),
            ],
        ) or []
        if isinstance(records, dict):
            records = [records]
        return [dict(record) for record in records if not record.get("login")]

    @Slot()
    def refresh(self) -> None:
        self.ensure_loaded()
        if self._busy or not self._project_code:
            return
        project_code = self._project_code
        generation = self._generation

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            return project_code, generation, self._query_server_records(server)

        self._run(operation, self._refreshed)

    @Slot(str)
    def save_as(self, title: str) -> None:
        self.ensure_loaded()
        title = str(title or "").strip()
        if not self.canManage or self._busy or not self._project_code:
            return
        if not title:
            self._set_error(self.tr("Enter a layout preset name"))
            return
        if any(
            str(record.get("title") or "").casefold() == title.casefold()
            for record in self.presets.records()
        ):
            self._set_error(self.tr("A layout preset with this name already exists"))
            return
        view = WORKSPACE_LAYOUT_VIEW_PREFIX + uuid.uuid4().hex
        self._save_record(title, view, "")

    @Slot(str)
    def update(self, identity: str) -> None:
        self.ensure_loaded()
        if not self.canManage or self._busy:
            return
        record = self._record(identity)
        if not record:
            self._set_error(self.tr("Select a layout preset first"))
            return
        self._save_record(
            str(record.get("title") or self.tr("Untitled layout")),
            str(record.get("view") or ""),
            str(record.get("code") or ""),
        )

    def _save_record(self, title: str, view: str, code: str) -> None:
        project_code = self._project_code
        generation = self._generation
        configuration = self._dock_model.capture_layout()
        config_xml = layout_configuration_xml(configuration, view)

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            data = {
                "view": view,
                "login": "",
                "category": WORKSPACE_LAYOUT_CATEGORY,
                "search_type": WORKSPACE_LAYOUT_SEARCH_TYPE,
                "title": title,
                "config": config_xml,
            }
            saved_code = code
            if code:
                search_key = server.build_search_key(
                    "config/widget_config", code,
                    project_code=project_code,
                )
                server.insert_update(search_key, data, triggers=True)
            else:
                created = server.insert(
                    "config/widget_config", data, triggers=True
                ) or {}
                saved_code = str(created.get("code") or "")
            restored = server.query(
                "config/widget_config",
                [
                    ("view", view),
                    ("search_type", WORKSPACE_LAYOUT_SEARCH_TYPE),
                    ("category", WORKSPACE_LAYOUT_CATEGORY),
                ],
            ) or []
            if isinstance(restored, dict):
                restored = [restored]
            restored = [row for row in restored if not row.get("login")]
            if len(restored) != 1:
                raise RuntimeError(
                    "The server did not retain one workspace layout preset"
                )
            saved = {**data, **dict(restored[0])}
            if saved_code and not saved.get("code"):
                saved["code"] = saved_code
            restored_configuration = layout_configuration_from_xml(
                saved.get("config"), view,
            )
            if restored_configuration != configuration:
                raise RuntimeError(
                    "The server changed the workspace layout preset payload"
                )
            return project_code, generation, saved

        self._run(operation, self._saved)

    @Slot(str)
    def delete_preset(self, identity: str) -> None:
        self.ensure_loaded()
        if not self.canManage or self._busy:
            return
        record = self._record(identity)
        if not record:
            self._set_error(self.tr("Select a layout preset first"))
            return
        if int(record.get("assignedCount") or 0) > 0:
            self._set_error(self.tr(
                "Remove this preset from sidebar items before deleting it"
            ))
            return
        project_code = self._project_code
        generation = self._generation
        code = str(record.get("code") or "")
        view = str(record.get("view") or "")
        if not code:
            self._set_error(self.tr(
                "This layout preset has no server identity; refresh and try again"
            ))
            return

        def operation():
            import thlib.tactic_classes as tc

            server = tc.server_start(project=project_code)
            search_key = server.build_search_key(
                "config/widget_config", code,
                project_code=project_code,
            )
            server.delete_sobject(search_key)
            remaining = server.query(
                "config/widget_config",
                [
                    ("view", view),
                    ("search_type", WORKSPACE_LAYOUT_SEARCH_TYPE),
                    ("category", WORKSPACE_LAYOUT_CATEGORY),
                ],
            ) or []
            if isinstance(remaining, dict):
                remaining = [remaining]
            if any(not record.get("login") for record in remaining):
                raise RuntimeError(self.tr(
                    "The server did not delete the workspace layout preset"
                ))
            return project_code, generation, code, view

        self._run(operation, self._deleted)

    def _run(self, operation, handler) -> None:
        try:
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            worker = env_inst.server_pool.add_task(operation)
            if worker is None:
                raise RuntimeError(self.tr("Server worker is unavailable"))
            self._workers.add(worker)
            worker.result.connect(handler)
            worker.error.connect(self._failed)

            def release():
                self._workers.discard(worker)
                self._busy = bool(self._workers)
                self.stateChanged.emit()

            worker.finished.connect(release)
            self._busy = True
            self._error = ""
            self.stateChanged.emit()
            worker.start()
        except Exception as exception:
            self._set_error(str(exception))

    @Slot(object)
    def _refreshed(self, payload) -> None:
        project_code, generation, records = payload
        if project_code != self._project_code or generation != self._generation:
            return
        current = self._project_records()
        retained = [record for record in current if not self._is_preset_record(record)]
        try:
            self._project.get_config_views().config_dict = [*retained, *records]
        except AttributeError:
            return
        self._sync_from_project()
        self.presetsChanged.emit(project_code)

    @Slot(object)
    def _saved(self, payload) -> None:
        project_code, generation, saved = payload
        if project_code != self._project_code or generation != self._generation:
            return
        self._replace_project_record(saved)
        self._sync_from_project()
        self._active_view = str(saved.get("view") or "")
        self._application._notify(self.tr("Workspace layout preset saved"))
        self.presetsChanged.emit(project_code)

    @Slot(object)
    def _deleted(self, payload) -> None:
        project_code, generation, code, view = payload
        if project_code != self._project_code or generation != self._generation:
            return
        self._remove_project_record(code, view)
        self._sync_from_project()
        self._application._notify(self.tr("Workspace layout preset deleted"))
        self.presetsChanged.emit(project_code)

    def _set_error(self, message: str) -> None:
        self._busy = bool(self._workers)
        message = str(message or "")
        changed = message != self._error
        self._error = message
        self.stateChanged.emit()
        if message and changed:
            try:
                self._application._notify(message)
            except AttributeError:
                pass

    @Slot(object)
    def _failed(self, error) -> None:
        payload, worker = error
        self._workers.discard(worker)
        message = str(payload.get("exception") or error)
        stacktrace = str(
            payload.get("traceback")
            or payload.get("stacktrace")
            or traceback.format_exc()
        )
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.log(
                "ERROR", message,
                group="ui/workspace-layout-presets",
                source="WorkspaceLayoutPresetController",
                stacktrace=stacktrace,
                caller=2,
            )
        self._set_error(message)
