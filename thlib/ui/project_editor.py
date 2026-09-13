from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot


class ProjectEditorController(QObject):
    stateChanged = Signal()
    saved = Signal(str)

    def __init__(
        self,
        context,
        checkin_controller,
        notify=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._context = context
        self._checkin = checkin_controller
        self._notify = notify or (lambda _message: None)
        self._project = None
        self._busy = False
        self._error = ""
        self._code = ""
        self._title = ""
        self._category = ""
        self._project_type = ""
        self._description = ""
        self._preview = ""
        self._preview_path = ""
        self._archived = False
        self._template = False
        self._worker = None

    @Slot()
    def begin_session(self) -> None:
        context = dict(self._context() or {})
        project = context.get("project")
        if project is None:
            self._set_error(self.tr("Select a project first"))
            return
        info = dict(project.get_info() or {})
        try:
            builtin = bool(project.is_builtin())
        except AttributeError:
            builtin = bool(info.get("__builtin__"))
        if builtin:
            self._set_error(self.tr("Built-in TACTIC projects cannot be edited"))
            return
        self._project = project
        self._code = str(project.get_code() or "")
        self._title = str(project.get_title() or self._code)
        self._category = str(info.get("category") or "")
        self._project_type = str(project.get_type() or "")
        self._description = str(info.get("description") or "")
        self._preview = str(context.get("preview") or "")
        self._preview_path = ""
        self._archived = str(info.get("s_status") or "").lower() == "retired"
        self._template = bool(project.is_template())
        self._busy = False
        self._error = ""
        self.stateChanged.emit()

    @Slot(str)
    def set_title(self, value: str) -> None:
        self._set_text("_title", value)

    @Slot(str)
    def set_category(self, value: str) -> None:
        self._set_text("_category", value)

    @Slot(str)
    def set_project_type(self, value: str) -> None:
        self._set_text("_project_type", value)

    @Slot(str)
    def set_description(self, value: str) -> None:
        self._set_text("_description", value)

    @Slot(bool)
    def set_archived(self, value: bool) -> None:
        self._set_value("_archived", bool(value))

    @Slot(bool)
    def set_template(self, value: bool) -> None:
        self._set_value("_template", bool(value))

    @Slot("QVariant")
    def set_preview_path(self, value) -> None:
        if isinstance(value, QUrl):
            path = value.toLocalFile() or value.toString()
        else:
            text = str(value or "")
            url = QUrl(text)
            path = url.toLocalFile() if text.startswith("file:") else text
        path = str(Path(path).expanduser()) if path else ""
        if self._preview_path == path:
            return
        self._preview_path = path
        self.stateChanged.emit()

    def _set_text(self, attribute: str, value: str) -> None:
        self._set_value(attribute, str(value or ""))

    def _set_value(self, attribute: str, value) -> None:
        if getattr(self, attribute) == value:
            return
        setattr(self, attribute, value)
        self.stateChanged.emit()

    @Slot()
    def submit(self) -> None:
        if self._busy or self._project is None:
            return
        if not self._title.strip():
            self._set_error(self.tr("Project name is required"))
            return
        if self._preview_path and not Path(self._preview_path).is_file():
            self._set_error(self.tr("The selected preview file does not exist"))
            return

        info = dict(self._project.get_info() or {})
        title_column = "name" if "name" in info else "title"
        values = {
            title_column: self._title.strip(),
            "category": self._category.strip(),
            "type": self._project_type.strip(),
            "description": self._description.strip(),
            "is_template": bool(self._template),
        }
        archived_before = str(info.get("s_status") or "").lower() == "retired"
        self._busy = True
        self._error = ""
        self.stateChanged.emit()

        from thlib.environment import env_inst

        worker = env_inst.server_pool.add_task(
            self._save_project,
            self._project,
            values,
            archived_before,
            self._archived,
        )
        if worker is None:
            self._set_error(self.tr("Project worker pool is unavailable"))
            return
        self._worker = worker
        worker.result.connect(self._save_finished)
        worker.error.connect(self._save_failed)
        worker.start()

    @staticmethod
    def _save_project(project, values, archived_before, archived_after):
        from thlib import tactic_classes as tc

        for key, value in values.items():
            project.set_value(key, value)
        project.commit()

        if archived_before != archived_after:
            server = tc.server_start(project="sthpw")
            if archived_after:
                result = server.retire_sobject(project.get_search_key())
            else:
                result = server.reactivate_sobject(project.get_search_key())
            if isinstance(result, dict):
                project.info.update(result)
            else:
                project.info["s_status"] = "retired" if archived_after else ""
        return project

    @Slot(object)
    def _save_finished(self, project) -> None:
        self._busy = False
        self._worker = None
        context = dict(self._context() or {})
        refresh = context.get("refresh")
        if callable(refresh):
            refresh(project)

        if self._preview_path:
            try:
                self._checkin.prepare_external_checkin(
                    search_key=project.get_search_key(),
                    source=project,
                    project_code="sthpw",
                    title=project.get_title(),
                    code=project.get_code(),
                    context="icon",
                    description="Project preview",
                    paths=[self._preview_path],
                    update_versionless=True,
                    queue_when_ready=True,
                )
                self._notify(self.tr("Project preview added to Commit Queue"))
            except (AttributeError, OSError, TypeError, ValueError) as error:
                self._error = str(error)
                self.stateChanged.emit()
                self._notify(self.tr(
                    "Project updated, but its preview could not be queued"
                ))
                return
        self._preview_path = ""
        self.stateChanged.emit()
        self.saved.emit(str(project.get_code() or ""))
        self._notify(self.tr("Project updated"))

    @Slot(object)
    def _save_failed(self, error) -> None:
        payload = error[0] if isinstance(error, (tuple, list)) else error
        if isinstance(payload, dict):
            message = str(
                payload.get("exception")
                or payload.get("message")
                or payload.get("traceback")
                or payload
            )
        else:
            message = str(payload)
        self._set_error(message or self.tr("The server rejected the project changes"))
        self._notify(self._error)

    def _set_error(self, message: str) -> None:
        self._busy = False
        self._worker = None
        self._error = str(message or "")
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def code(self) -> str:
        return self._code

    @Property(str, notify=stateChanged)
    def title(self) -> str:
        return self._title

    @Property(str, notify=stateChanged)
    def category(self) -> str:
        return self._category

    @Property(str, notify=stateChanged)
    def projectType(self) -> str:
        return self._project_type

    @Property(str, notify=stateChanged)
    def description(self) -> str:
        return self._description

    @Property(str, notify=stateChanged)
    def preview(self) -> str:
        return self._preview

    @Property(str, notify=stateChanged)
    def previewUrl(self) -> str:
        return QUrl.fromLocalFile(self._preview_path).toString() if self._preview_path else self._preview

    @Property(str, notify=stateChanged)
    def previewPath(self) -> str:
        return self._preview_path

    @Property(bool, notify=stateChanged)
    def archived(self) -> bool:
        return self._archived

    @Property(bool, notify=stateChanged)
    def isTemplate(self) -> bool:
        return self._template
