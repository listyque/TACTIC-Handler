"""Dependency-aware sObject duplication wizard controller."""

from __future__ import annotations

import time
from collections.abc import Mapping

from PySide6.QtCore import QObject, Property, Signal, Slot

from thlib.environment import env_read_config, env_write_config
from thlib.ui.sobject_editor import SObjectEditorController, SObjectFieldModel
from thlib.ui.workspace_models.records import RecordListModel


RELATION_ROLES = (
    "key", "direction", "kind", "relationship", "searchType", "title",
    "count", "mode", "defaultMode", "localColumn", "path",
    "instanceType", "options", "items",
)
PROCESS_ROLES = (
    "name", "snapshotCount", "fileCount", "taskCount",
    "processMessageCount", "taskMessageCount", "processAttachmentCount",
    "taskAttachmentCount", "copySnapshots", "copyTasks",
    "copyProcessMessages", "copyTaskMessages",
    "copyProcessAttachments", "copyTaskAttachments",
)


def _search_key(source) -> str:
    try:
        return str(source.get_search_key() or "")
    except (AttributeError, KeyError, TypeError):
        return ""


def _search_type(source) -> str:
    try:
        value = source.get_plain_search_type()
    except (AttributeError, KeyError, TypeError):
        value = ""
    return str(value or _search_key(source).split("?", 1)[0])


def _project_code(source) -> str:
    try:
        return str(source.get_project().get_code() or "")
    except (AttributeError, KeyError, TypeError):
        pass
    try:
        return str(source.get_stype().get_project().get_code() or "")
    except (AttributeError, KeyError, TypeError):
        pass
    search_key = _search_key(source)
    for part in search_key.split("?", 1)[-1].split("&"):
        if part.startswith("project="):
            return part.split("=", 1)[1]
    return ""


def _profile_key(source) -> str:
    return "{}|{}".format(_project_code(source), _search_type(source))


def apply_duplicate_profile(
    relations: list[dict], processes: list[dict], profile: Mapping | None,
) -> tuple[list[dict], list[dict]]:
    """Apply only stable choices; never reuse object-specific field values."""
    profile = dict(profile or {})
    relation_choices = dict(profile.get("relations") or {})
    process_choices = dict(profile.get("processes") or {})
    resolved_relations = []
    for relation in relations or []:
        record = dict(relation)
        available = {
            str(option.get("value") or "")
            for option in record.get("options") or []
        }
        saved_mode = str(
            relation_choices.get(str(record.get("key") or "")) or ""
        )
        if saved_mode in available:
            record["mode"] = saved_mode
        resolved_relations.append(record)

    resolved_processes = []
    for process in processes or []:
        record = dict(process)
        saved = dict(
            process_choices.get(str(record.get("name") or "")) or {}
        )
        for name in (
            "copySnapshots", "copyTasks", "copyProcessMessages",
            "copyTaskMessages", "copyProcessAttachments",
            "copyTaskAttachments",
        ):
            if name in saved:
                record[name] = bool(saved[name])
        if record.get("copyTaskMessages"):
            record["copyTasks"] = True
        if record.get("copyProcessAttachments"):
            record["copyProcessMessages"] = True
        if record.get("copyTaskAttachments"):
            record["copyTaskMessages"] = True
            record["copyTasks"] = True
        resolved_processes.append(record)
    return resolved_relations, resolved_processes


class SObjectDuplicateController(QObject):
    """Own analysis, per-Search-Type profiles and asynchronous duplication."""

    stateChanged = Signal()
    duplicationFinished = Signal(str)

    _settings_file = "ui_sobject_duplicate"
    _settings_id = "profiles"

    def __init__(self, application, debug_log=None, parent=None):
        super().__init__(parent)
        self._application = application
        self._debug_log = debug_log
        self.fields = SObjectFieldModel(self)
        self._field_catalog = SObjectEditorController(
            lambda: {}, parent=self
        )
        self.relations = RecordListModel(RELATION_ROLES)
        self.processes = RecordListModel(PROCESS_ROLES)
        self._profiles = dict(env_read_config(
            filename=self._settings_file,
            unique_id=self._settings_id,
            long_abs_path=True,
        ) or {})
        self._source = None
        self._profile_key_value = ""
        self._search_type = ""
        self._title = ""
        self._step = 0
        self._busy = False
        self._duplicating = False
        self._ready = False
        self._error = ""
        self._remember_settings = True
        self._quick_after_analysis = False
        self._generation = 0
        self._worker = None
        self._duplicate_started_at = 0.0
        self._script_triggers = None
        self._trigger_payload = {}

    def attach_script_triggers(self, triggers) -> None:
        self._script_triggers = triggers

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def duplicating(self) -> bool:
        return self._duplicating

    @Property(bool, notify=stateChanged)
    def ready(self) -> bool:
        return self._ready

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(str, notify=stateChanged)
    def title(self) -> str:
        return self._title

    @Property(str, notify=stateChanged)
    def searchType(self) -> str:
        return self._search_type

    @Property(int, notify=stateChanged)
    def step(self) -> int:
        return self._step

    @Property(bool, notify=stateChanged)
    def rememberSettings(self) -> bool:
        return self._remember_settings

    @rememberSettings.setter
    def rememberSettings(self, value: bool) -> None:
        value = bool(value)
        if value == self._remember_settings:
            return
        self._remember_settings = value
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def hasRememberedProfile(self) -> bool:
        return bool(self._profile_key_value in self._profiles)

    @Property(int, notify=stateChanged)
    def selectedRelationCount(self) -> int:
        return sum(
            int(record.get("count") or 0)
            for record in self.relations._records
            if record.get("mode") != "none"
        )

    @Property(int, notify=stateChanged)
    def selectedSnapshotCount(self) -> int:
        return sum(
            int(record.get("snapshotCount") or 0)
            for record in self.processes._records
            if record.get("copySnapshots")
        )

    @Property(int, notify=stateChanged)
    def selectedTaskCount(self) -> int:
        return sum(
            int(record.get("taskCount") or 0)
            for record in self.processes._records
            if record.get("copyTasks")
        )

    @Property(int, notify=stateChanged)
    def selectedMessageCount(self) -> int:
        return sum(
            (
                int(record.get("processMessageCount") or 0)
                if record.get("copyProcessMessages") else 0
            ) + (
                int(record.get("taskMessageCount") or 0)
                if record.get("copyTaskMessages") else 0
            )
            for record in self.processes._records
        )

    @Property(int, notify=stateChanged)
    def selectedAttachmentCount(self) -> int:
        return sum(
            (
                int(record.get("processAttachmentCount") or 0)
                if record.get("copyProcessAttachments") else 0
            ) + (
                int(record.get("taskAttachmentCount") or 0)
                if record.get("copyTaskAttachments") else 0
            )
            for record in self.processes._records
        )

    @Property(int, notify=stateChanged)
    def availableSnapshotCount(self) -> int:
        return sum(
            int(record.get("snapshotCount") or 0)
            for record in self.processes._records
        )

    @Property(int, notify=stateChanged)
    def availableTaskMessageCount(self) -> int:
        return sum(
            int(record.get("taskCount") or 0)
            + int(record.get("processMessageCount") or 0)
            + int(record.get("taskMessageCount") or 0)
            for record in self.processes._records
        )

    def has_profile_for_source(self, source) -> bool:
        return bool(source and _profile_key(source) in self._profiles)

    def begin(self, source, quick=False) -> bool:
        search_key = _search_key(source)
        if not search_key:
            self._application._notify("Selected item is no longer available")
            return False
        self._generation += 1
        generation = self._generation
        self._source = source
        self._profile_key_value = _profile_key(source)
        self._search_type = _search_type(source)
        self._title = ""
        self._step = 0
        self._busy = True
        self._duplicating = False
        self._ready = False
        self._error = ""
        self._quick_after_analysis = bool(quick)
        self.fields.clear()
        self.relations.clear()
        self.processes.clear()
        self.stateChanged.emit()
        if not quick:
            self._application.window_model.show_window("duplicate_sobject")
        try:
            import thlib.tactic_classes as tc
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            analysis_search_type = self._search_type
            analysis_project_code = _project_code(source)

            def load_analysis():
                from thlib import tactic_query as tq

                analysis = tc.analyze_sobject_duplicate(search_key)
                if quick:
                    return analysis
                edit_view = tc.execute_procedure_serverside(
                    tq.query_EditWdg,
                    {
                        "args": {
                            "mode": "edit",
                            "input_prefix": "edit",
                            "search_key": search_key,
                            "parent_key": None,
                            "search_type": analysis_search_type,
                            "view": "edit",
                        },
                        "search_type": analysis_search_type,
                        "project": analysis_project_code,
                    },
                    project=analysis_project_code,
                )
                return {"analysis": analysis, "editView": edit_view}

            worker = env_inst.server_pool.add_task(load_analysis)
            self._worker = worker
            worker.result.connect(
                lambda result, current=generation:
                self._analysis_ready(current, result)
            )
            worker.error.connect(
                lambda error, current=generation:
                self._operation_failed(current, error, "analysis")
            )
            worker.start()
        except Exception as error:
            self._operation_failed(generation, error, "analysis")
        return True

    def quick_duplicate(self, source) -> bool:
        if not self.has_profile_for_source(source):
            self._application._notify(
                "Open Duplicate… once to save choices for this Search Type"
            )
            return False
        return self.begin(source, quick=True)

    def _analysis_ready(self, generation: int, payload) -> None:
        if generation != self._generation:
            return
        self._worker = None
        envelope = dict(payload or {})
        edit_view = dict(envelope.get("editView") or {})
        payload = dict(envelope.get("analysis") or envelope)
        profile = self._profiles.get(self._profile_key_value) or {}
        relations, processes = apply_duplicate_profile(
            list(payload.get("relations") or []),
            list(payload.get("processes") or []),
            profile,
        )
        fields = self._edit_view_fields(edit_view)
        if not fields:
            fields = self._fallback_fields(payload.get("fields") or [])
        self.fields.replace(fields)
        self.relations.reset_records(relations)
        self.processes.reset_records(processes)
        self._title = str(payload.get("title") or "")
        self._search_type = str(
            payload.get("searchType") or self._search_type
        )
        self._busy = False
        self._ready = True
        self._error = ""
        quick = self._quick_after_analysis
        self._quick_after_analysis = False
        self.stateChanged.emit()
        if quick:
            self.duplicate()

    @Slot(int)
    def set_step(self, step: int) -> None:
        step = min(4, max(0, int(step)))
        if step == self._step:
            return
        self._step = step
        self.stateChanged.emit()

    @Slot()
    def next_step(self) -> None:
        self.set_step(self._step + 1)

    @Slot()
    def previous_step(self) -> None:
        self.set_step(self._step - 1)

    @Slot(int, str)
    def set_field_value(self, row: int, value: str) -> None:
        self.fields.setValue(row, value)

    def _edit_view_fields(self, edit_view: Mapping) -> list[dict]:
        sources = list(edit_view.get("InputWidgets") or [])
        if not sources or self._source is None:
            return []
        try:
            stype = self._source.get_stype()
        except AttributeError:
            return []
        context = {
            "stype": stype,
            "sobject": self._source,
            "parent_sobject": None,
            "info_dict": None,
        }
        return self._field_catalog.build_descriptors(
            stype, context, sources, mode="edit"
        )

    @staticmethod
    def _fallback_fields(fields) -> list[dict]:
        type_aliases = {
            "bool": "bool", "boolean": "bool",
            "int": "integer", "integer": "integer",
            "int2": "integer", "int4": "integer", "int8": "integer",
            "smallint": "integer", "bigint": "integer",
            "float": "float", "real": "float", "double": "float",
            "numeric": "float", "decimal": "float",
            "date": "date", "datetime": "datetime",
            "timestamp": "datetime",
        }
        descriptors = []
        for source in fields or []:
            source = dict(source or {})
            name = str(source.get("name") or "")
            if not name:
                continue
            original_type = str(source.get("dataType") or "text")
            field_type = type_aliases.get(original_type.lower(), "string")
            if source.get("multiline"):
                field_type = "multiline"
            value = source.get("value")
            if value is None:
                value = ""
            descriptors.append({
                "fieldName": name,
                "submitName": name,
                "title": str(source.get("label") or name),
                "fieldType": field_type,
                "originalType": original_type,
                "fieldValue": value,
                "defaultValue": value,
                "fieldRequired": False,
                "fieldReadOnly": False,
                "fieldOptions": [],
                "fieldError": "",
                "fieldDescription": name,
                "fieldIcon": SObjectEditorController._field_icons.get(
                    field_type, "type"
                ),
                "widgetClass": "",
            })
        return descriptors

    @Slot(int, str)
    def set_relation_mode(self, row: int, mode: str) -> None:
        record = self.relations.get(row)
        available = {
            str(option.get("value") or "")
            for option in record.get("options") or []
        }
        if mode not in available:
            return
        if self.relations.update_record(row, {"mode": mode}):
            self.stateChanged.emit()

    @Slot(int, str, bool)
    def set_process_choice(
        self, row: int, choice: str, checked: bool,
    ) -> None:
        if choice not in {
            "copySnapshots", "copyTasks", "copyProcessMessages",
            "copyTaskMessages", "copyProcessAttachments",
            "copyTaskAttachments",
        }:
            return
        values = {choice: bool(checked)}
        if choice == "copyTaskMessages" and checked:
            values["copyTasks"] = True
        elif choice == "copyTasks" and not checked:
            values["copyTaskMessages"] = False
            values["copyTaskAttachments"] = False
        if choice == "copyProcessAttachments" and checked:
            values["copyProcessMessages"] = True
        elif choice == "copyProcessMessages" and not checked:
            values["copyProcessAttachments"] = False
        if choice == "copyTaskAttachments" and checked:
            values["copyTasks"] = True
            values["copyTaskMessages"] = True
        elif choice == "copyTaskMessages" and not checked:
            values["copyTaskAttachments"] = False
        if self.processes.update_record(row, values):
            self.stateChanged.emit()

    def _profile(self) -> dict:
        return {
            "relations": {
                str(record.get("key") or ""): str(record.get("mode") or "none")
                for record in self.relations._records
                if record.get("key")
            },
            "processes": {
                str(record.get("name") or ""): {
                    name: bool(record.get(name))
                    for name in (
                        "copySnapshots", "copyTasks",
                        "copyProcessMessages", "copyTaskMessages",
                        "copyProcessAttachments", "copyTaskAttachments",
                    )
                }
                for record in self.processes._records
                if record.get("name")
            },
        }

    def _options(self) -> dict:
        return {
            "fields": self.fields.submission_values("insert"),
            "relations": {
                str(record.get("key") or ""): str(record.get("mode") or "none")
                for record in self.relations._records
                if record.get("key")
            },
            "processes": {
                str(record.get("name") or ""): {
                    name: bool(record.get(name))
                    for name in (
                        "copySnapshots", "copyTasks",
                        "copyProcessMessages", "copyTaskMessages",
                        "copyProcessAttachments", "copyTaskAttachments",
                    )
                }
                for record in self.processes._records
                if record.get("name")
            },
        }

    def _updated_profile_config(self) -> dict | None:
        if not self._profile_key_value:
            return None
        profiles = dict(self._profiles)
        profiles[self._profile_key_value] = self._profile()
        self._profiles = profiles
        return profiles

    @classmethod
    def _write_profile_config(cls, profiles: Mapping) -> None:
        env_write_config(
            dict(profiles),
            filename=cls._settings_file,
            unique_id=cls._settings_id,
            long_abs_path=True,
        )

    @Slot()
    def duplicate(self) -> None:
        if self._busy or self._duplicating or not self._ready:
            return
        if not self.fields.valid:
            self._error = "Correct the highlighted fields"
            self.stateChanged.emit()
            return
        search_key = _search_key(self._source)
        if not search_key:
            self._operation_failed(
                self._generation,
                RuntimeError("Selected item is no longer available"),
                "duplicate",
            )
            return
        self._trigger_payload = {
            "project_code": _project_code(self._source),
            "search_key": search_key,
            "search_type": _search_type(self._source),
            "values": self.fields.submission_values("insert"),
            "options": self._options(),
        }
        triggers = self._script_triggers
        if triggers is not None:
            self._duplicating = True
            self._error = ""
            self.stateChanged.emit()

            def start(success: bool, error: str) -> None:
                if not success:
                    self._duplicating = False
                    self._error = str(error or "Script trigger failed")
                    self.stateChanged.emit()
                    return
                self._duplicate_now(search_key)

            triggers.run_before(
                "object.duplicate", self._trigger_payload, start
            )
            return
        self._duplicate_now(search_key)

    def _duplicate_now(self, search_key: str) -> None:
        profile_config = (
            self._updated_profile_config()
            if self._remember_settings else None
        )
        write_profile_config = type(self)._write_profile_config
        options = self._options()
        project_code = _project_code(self._source)
        self._generation += 1
        generation = self._generation
        self._duplicating = True
        self._duplicate_started_at = time.monotonic()
        self._error = ""
        self.stateChanged.emit()
        if self._debug_log:
            self._debug_log.log(
                "INFO",
                "sObject duplication started",
                group="sobject-duplicate/duplicate",
                source="Duplicate SObject",
                details="searchType={}".format(self._search_type),
            )
        try:
            import thlib.tactic_classes as tc
            from thlib.environment import env_inst

            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()

            def operation():
                from thlib import server_cache

                if profile_config is not None:
                    write_profile_config(profile_config)
                result = tc.duplicate_sobject_advanced(
                    search_key, options
                )
                server_cache.invalidate_domains(
                    (
                        "reference", "search", "snapshots", "relations",
                        "tasks", "notes", "messages", "activity",
                    ),
                    project_code,
                )
                return result

            worker = env_inst.server_pool.add_task(operation)
            self._worker = worker
            worker.result.connect(
                lambda result, current=generation:
                self._duplicate_finished(current, result)
            )
            worker.error.connect(
                lambda error, current=generation:
                self._operation_failed(current, error, "duplicate")
            )
            worker.start()
        except Exception as error:
            self._operation_failed(generation, error, "duplicate")

    def _duplicate_finished(self, generation: int, result) -> None:
        if generation != self._generation:
            return
        self._worker = None
        self._busy = False
        self._duplicating = False
        self._ready = False
        self._error = ""
        elapsed = max(0.0, time.monotonic() - self._duplicate_started_at)
        self._duplicate_started_at = 0.0
        self.stateChanged.emit()
        if self._debug_log:
            self._debug_log.log(
                "LOG",
                "sObject duplication completed",
                group="sobject-duplicate/duplicate",
                source="Duplicate SObject",
                duration=elapsed,
            )
        self._application.window_model.close_window("duplicate_sobject")
        self._application._notify("sObject duplicated")
        self._application.refresh_current()
        search_key = ""
        if isinstance(result, Mapping):
            search_key = str(result.get("searchKey") or "")
        self.duplicationFinished.emit(search_key)
        if self._script_triggers is not None:
            payload = dict(self._trigger_payload)
            payload["result_search_key"] = search_key
            self._script_triggers.run_after("object.duplicate", payload)

    def _operation_failed(self, generation: int, error, phase: str) -> None:
        if generation != self._generation:
            return
        self._worker = None
        payload = error[0] if isinstance(error, tuple) else error
        if isinstance(payload, Mapping):
            exception = payload.get("exception") or payload
            stacktrace = payload.get("stacktrace") or ""
        else:
            exception = payload
            stacktrace = ""
        self._busy = False
        self._duplicating = False
        self._ready = phase == "duplicate"
        self._duplicate_started_at = 0.0
        self._error = str(exception or error)
        self.stateChanged.emit()
        self._application._notify(self._error)
        if self._debug_log:
            self._debug_log.raise_error(
                exception,
                stacktrace=stacktrace,
                group="sobject-duplicate/{}".format(phase),
            )

    @Slot()
    def retry(self) -> None:
        if self._busy or self._duplicating or not self._source:
            return
        self.begin(self._source, quick=False)

    @Slot()
    def cancel(self) -> None:
        self._generation += 1
        worker = self._worker
        self._worker = None
        if worker is not None:
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        self._busy = False
        self._duplicating = False
        self._ready = False
        self._duplicate_started_at = 0.0
        self._quick_after_analysis = False
        self.stateChanged.emit()
        self._application.window_model.close_window("duplicate_sobject")
