"""Bulk child-sObject ingest through TACTIC's native ingest command."""

from __future__ import annotations

import json
import os
from pathlib import Path
import threading
import traceback
import uuid
from PySide6.QtCore import QObject, Property, Qt, QUrl, Signal, Slot
from .ingest_preflight import IngestPreflightCoordinator, prepare_ingest_path
from .ingest_relation import execute_ingest_with_relation, relation_job_metadata
from .workspace_models.records import RecordListModel
_RULE_OPTION_DEFAULTS = {
    "title": "Quick ingest",
    "filter": "",
    "ignore": "",
    "pattern": "",
    "usePattern": False,
    "column": "name",
    "ignoreExtension": True,
    "updateMode": "insert",
    "process": "publish",
    "context": "publish",
    "contextMode": "case_sensitive",
    "keywords": "",
    "keywordMode": "default",
    "extraDataJson": "{}",
    "validationScript": "",
    "processScript": "",
    "createIcon": True,
}
class IngestFilesController(QObject):
    """Own one explicit relation ingest session and its background batch."""

    stateChanged = Signal()
    rulesChanged = Signal()
    batchFinished = Signal(int, int)

    _file_roles = (
        "path", "title", "extension", "status", "error",
    )
    _rule_roles = (
        "ruleId", "searchKey", "title", "subtitle", "selected",
        "builtIn", "applicable", "validationScript", "processScript",
    )
    _editable_options = frozenset(_RULE_OPTION_DEFAULTS)

    def __init__(self, application, debug_log=None, parent=None) -> None:
        super().__init__(parent)
        self._application = application
        self._debug_log = debug_log
        self.files = RecordListModel(self._file_roles)
        self.rules = RecordListModel(self._rule_roles)
        self._rule_payloads: dict[str, dict] = {}
        self._selected_rule_id = "builtin"
        self._options = dict(_RULE_OPTION_DEFAULTS)
        self._relation_node_id = ""
        self._parent_source = None
        self._parent_key = ""
        self._parent_title = ""
        self._target_stype = None
        self._target_search_type = ""
        self._target_title = ""
        self._relation_metadata = {}
        self._project_code = ""
        self._busy = False
        self._rules_busy = False
        self._progress = 0.0
        self._message = ""
        self._error = ""
        self._worker = None
        self._rules_worker = None
        self._rule_mutation_worker = None
        self._generation = 0
        self._rules_generation = 0
        self._cancel_event = threading.Event()
        self._silent = False
        self._preflight = IngestPreflightCoordinator(self)
        self._replace_rules([])
    def _relation_context(self, node_id: str) -> dict:
        node = self._application.workspace_model.node_for(str(node_id or ""))
        relation = dict(getattr(node, "relation", None) or {}) if node else {}
        definition = dict(relation.get("definition") or {})
        stype = relation.get("stype")
        parent = getattr(node, "source", None) if node else None
        if (
            node is None or node.node_type != "relation"
            or stype is None or parent is None
        ):
            return {}
        try:
            project_code = str(stype.get_project().get_code() or "")
            search_type = str(stype.get_code() or "")
            parent_key = str(parent.get_search_key() or "")
            parent_title = str(parent.get_title() or parent_key)
            target_title = str(stype.get_pretty_name() or search_type)
        except (AttributeError, KeyError, TypeError):
            return {}
        if not project_code or not search_type or not parent_key:
            return {}
        column = "name"
        try:
            if not stype.column_exists("name") and stype.column_exists("code"):
                column = "code"
        except (AttributeError, TypeError):
            pass
        relation_metadata = relation_job_metadata(definition, stype)
        if relation_metadata["relationship"] not in {
            "code", "search_type", "search_code", "search_id", "instance",
        }:
            return {}
        return {
            "node": node,
            "stype": stype,
            "parent": parent,
            "projectCode": project_code,
            "searchType": search_type,
            "parentKey": parent_key,
            "parentTitle": parent_title,
            "targetTitle": target_title,
            "column": column,
            "relation": relation_metadata,
        }
    def _apply_context(
        self, node_id: str, context: dict, *, load_rules: bool,
    ) -> None:
        self._generation += 1
        self._relation_node_id = str(node_id or "")
        self._parent_source = context["parent"]
        self._parent_key = context["parentKey"]
        self._parent_title = context["parentTitle"]
        self._target_stype = context["stype"]
        self._target_search_type = context["searchType"]
        self._target_title = context["targetTitle"]
        self._relation_metadata = dict(context.get("relation") or {})
        self._project_code = context["projectCode"]
        self._selected_rule_id = "builtin"
        self._options = dict(_RULE_OPTION_DEFAULTS)
        self._options["column"] = context["column"]
        self.files.clear()
        self._error = ""
        self._message = ""
        self._progress = 0.0
        self._preflight.reset()
        self._replace_rules([])
        self.stateChanged.emit()
        if load_rules:
            self._load_rules()
    @Slot(str)
    def open_for_relation(self, node_id: str) -> None:
        if self._busy or self._preflight.pending:
            self._application.notify(self.tr("An ingest batch is already running"))
            return
        context = self._relation_context(node_id)
        if not context:
            self._application.notify(
                self.tr("Select a child relation before ingesting files")
            )
            return
        self._silent = False
        self._apply_context(node_id, context, load_rules=True)
        self._application.window_model.show_window("ingest_files")
    def quick_ingest(self, node_id: str, paths: list[str]) -> None:
        if self._busy or self._preflight.pending:
            self._application.notify(self.tr("An ingest batch is already running"))
            return
        context = self._relation_context(node_id)
        if not context:
            self._application.notify(
                self.tr("This child relation cannot ingest files")
            )
            return
        self._silent = True
        self._apply_context(node_id, context, load_rules=False)
        self._add_local_paths(paths)
        if self.files._records:
            self.start()
    @staticmethod
    def _path_from_value(value) -> str:
        url = value if isinstance(value, QUrl) else QUrl(str(value))
        path = url.toLocalFile()
        if not path and not url.scheme():
            path = str(value)
        return os.path.normpath(path) if path else ""
    @Slot("QVariantList")
    def add_paths(self, values: list) -> None:
        self._add_local_paths([
            path for value in values
            if (path := self._path_from_value(value))
        ])
    def _add_local_paths(self, paths: list[str]) -> None:
        known = {
            os.path.normcase(str(record.get("path") or ""))
            for record in self.files._records
        }
        records = list(self.files._records)
        for value in paths:
            path = os.path.normpath(str(value or ""))
            identity = os.path.normcase(path)
            if not path or identity in known:
                continue
            known.add(identity)
            file_path = Path(path)
            records.append({
                "path": path,
                "title": file_path.name or path,
                "extension": file_path.suffix.lstrip(".").lower(),
                "status": "Ready",
                "error": "",
            })
        self.files.replace(records)
        self._error = ""
        self.stateChanged.emit()

    @Slot(int)
    def remove_file(self, row: int) -> None:
        if self._busy:
            return
        self.files.remove(row)
        self.stateChanged.emit()

    @Slot()
    def clear_files(self) -> None:
        if self._busy:
            return
        self.files.clear()
        self._error = ""
        self._message = ""
        self._progress = 0.0
        self.stateChanged.emit()

    def _replace_rules(self, server_records: list[dict]) -> None:
        builtin = {
            "ruleId": "builtin",
            "searchKey": "",
            "title": self.tr("Quick ingest"),
            "subtitle": self.tr(
                "Create one child item per file and publish immediately"
            ),
            "selected": self._selected_rule_id == "builtin",
            "builtIn": True,
            "applicable": True,
            "validationScript": "",
            "processScript": "",
        }
        payloads = {"builtin": dict(_RULE_OPTION_DEFAULTS)}
        rows = [builtin]
        for index, source in enumerate(server_records):
            raw_data = source.get("data") or {}
            if isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except (TypeError, ValueError):
                    raw_data = {}
            data = dict(raw_data or {})
            search_type = str(data.get("search_type") or "")
            action = str(data.get("action") or "file")
            action_type = str(data.get("action_type") or "checkin")
            applicable = (
                (not search_type or search_type == self._target_search_type)
                and action in {"", "file"}
                and action_type in {"", "checkin"}
            )
            rule_id = str(
                source.get("code") or source.get("__search_key__")
                or f"rule-{index}"
            )
            options = self._options_from_rule(source, data)
            payloads[rule_id] = options
            scripts = [
                value for value in (
                    options["validationScript"], options["processScript"],
                ) if value
            ]
            rows.append({
                "ruleId": rule_id,
                "searchKey": str(source.get("__search_key__") or ""),
                "title": str(source.get("title") or rule_id),
                "subtitle": (
                    self.tr("Scripts: %1").replace("%1", ", ".join(scripts))
                    if scripts else self.tr("Saved server ingest rule")
                ),
                "selected": rule_id == self._selected_rule_id,
                "builtIn": False,
                "applicable": applicable,
                "validationScript": options["validationScript"],
                "processScript": options["processScript"],
            })
        self._rule_payloads = payloads
        if self._selected_rule_id not in payloads:
            self._selected_rule_id = "builtin"
        for row in rows:
            row["selected"] = row["ruleId"] == self._selected_rule_id
        self.rules.replace(rows)
        self.rulesChanged.emit()

    def _options_from_rule(self, source: dict, data: dict) -> dict:
        options = dict(_RULE_OPTION_DEFAULTS)
        options.update({
            "title": str(source.get("title") or options["title"]),
            "filter": str(data.get("filter") or ""),
            "ignore": str(data.get("ignore") or ""),
            "pattern": str(data.get("rule") or source.get("rule") or ""),
            "usePattern": bool(data.get("rule") or source.get("rule")),
            "column": str(data.get("column") or self._options["column"]),
            "ignoreExtension": self._flag(data.get("ignore_ext", True)),
            "updateMode": (
                "update" if self._flag(data.get("update_mode")) else "insert"
            ),
            "process": str(data.get("process") or "publish"),
            "context": str(data.get("context") or "publish"),
            "contextMode": str(
                data.get("context_mode") or "case_sensitive"
            ),
            "keywords": str(data.get("keywords") or ""),
            "keywordMode": str(data.get("keyword_mode") or "default"),
            "validationScript": str(data.get("validation_script") or ""),
            "processScript": str(data.get("process_script") or ""),
            "createIcon": self._flag(data.get("create_icon", True)),
        })
        extra_data = data.get("extra_data") or {}
        if not extra_data:
            names = list(data.get("extra_name") or [])
            values = list(data.get("extra_value") or [])
            extra_data = {
                name: value for name, value in zip(names, values) if name
            }
        if isinstance(extra_data, str):
            try:
                extra_data = json.loads(extra_data)
            except (TypeError, ValueError):
                extra_data = {}
        options["extraDataJson"] = json.dumps(
            extra_data or {}, ensure_ascii=False, indent=2
        )
        return options

    @staticmethod
    def _flag(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on", "update"}
        return bool(value)

    def _load_rules(self) -> None:
        if not self._project_code:
            return
        self._rules_generation += 1
        generation = self._rules_generation
        self._rules_busy = True
        self.rulesChanged.emit()
        from thlib.environment import env_inst

        worker = env_inst.server_pool.add_task(
            self._query_rules, self._project_code
        )
        self._rules_worker = worker
        worker.result.connect(
            lambda result: self._rules_loaded(generation, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._rules_failed(generation, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @staticmethod
    def _query_rules(project_code: str) -> list[dict]:
        from thlib import tactic_classes as tc

        server = tc.server_start(project=project_code)
        return list(server.query(
            "config/ingest_rule", [], order_bys=["title"]
        ) or [])

    def _rules_loaded(self, generation: int, result) -> None:
        if generation != self._rules_generation:
            return
        self._rules_worker = None
        self._rules_busy = False
        self._replace_rules(list(result or []))
        self.rulesChanged.emit()

    def _rules_failed(self, generation: int, error) -> None:
        if generation != self._rules_generation:
            return
        self._rules_worker = None
        self._rules_busy = False
        # Ingest tables are optional in TACTIC. The built-in rule remains fully
        # functional and the missing optional table is not a blocking error.
        self._replace_rules([])
        self.rulesChanged.emit()

    @Slot(int)
    def select_rule(self, row: int) -> None:
        record = self.rules.get(row)
        rule_id = str(record.get("ruleId") or "")
        if not rule_id or not record.get("applicable") or self._busy:
            return
        self._selected_rule_id = rule_id
        self._options = dict(self._rule_payloads.get(
            rule_id, _RULE_OPTION_DEFAULTS
        ))
        if not self._options.get("column"):
            self._options["column"] = "name"
        records = [dict(item) for item in self.rules._records]
        for item in records:
            item["selected"] = item.get("ruleId") == rule_id
        self.rules.replace(records)
        self.rulesChanged.emit()
        self.stateChanged.emit()

    @Slot(str, "QVariant")
    def set_option(self, name: str, value) -> None:
        if name not in self._editable_options or self._busy:
            return
        if name in {"ignoreExtension", "usePattern", "createIcon"}:
            value = bool(value)
        else:
            value = str(value or "")
        if self._options.get(name) == value:
            return
        self._options[name] = value
        self.stateChanged.emit()

    def _validated_options(self) -> dict:
        options = dict(self._options)
        try:
            extra_data = json.loads(options.get("extraDataJson") or "{}")
        except (TypeError, ValueError) as error:
            raise ValueError(self.tr("Extra values must be a JSON object")) from error
        if not isinstance(extra_data, dict):
            raise ValueError(self.tr("Extra values must be a JSON object"))
        options["extraData"] = extra_data
        options["column"] = (
            "code" if options.get("column") == "code" else "name"
        )
        options["process"] = str(options.get("process") or "publish")
        options["context"] = str(
            options.get("context") or options["process"]
        )
        return options

    @Slot()
    def start(self) -> None:
        if self._busy or self._preflight.pending:
            return
        if not self._target_search_type or not self._parent_key:
            self._set_error(self.tr("Select a child relation first"))
            return
        paths = [str(row.get("path") or "") for row in self.files._records]
        if not paths:
            self._set_error(self.tr("Add at least one file"))
            return
        try:
            options = self._validated_options()
        except ValueError as error:
            self._set_error(str(error))
            return
        self._generation += 1
        generation = self._generation
        self._busy = True
        self._error = ""
        self._progress = 0.0
        self._message = self.tr("Checking for existing items")
        self._cancel_event.clear()
        self.files.replace([
            {**record, "status": "Checking", "error": ""}
            for record in self.files._records
        ])
        self.stateChanged.emit()
        job = {
            "projectCode": self._project_code,
            "searchType": self._target_search_type,
            "parentKey": self._parent_key,
            "relationNodeId": self._relation_node_id,
            "paths": paths,
            "options": options,
            "relation": dict(self._relation_metadata),
        }
        self._preflight.begin(generation, job)

    @Slot(str)
    def resolve_ingest_conflict(self, action: str) -> None:
        self._preflight.resolve(action)

    def _start_batch(self, generation: int, job: dict) -> None:
        self._busy = True
        self._error = ""
        self._message = self.tr("Starting ingest")
        self.files.replace([
            {**record, "status": "Queued", "error": ""}
            for record in self.files._records
        ])
        self.stateChanged.emit()
        if not self._silent:
            self._application.notify(
                self.tr("Ingesting %1 file(s)").replace(
                    "%1", str(len(job["paths"]))
                )
            )
        from thlib.environment import env_inst

        worker = env_inst.server_pool.add_task(
            self._ingest_batch, job, self._cancel_event
        )
        self._worker = worker
        worker.connect_progress(self._batch_progressed)
        worker.result.connect(
            lambda result: self._batch_finished(generation, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._batch_failed(generation, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @staticmethod
    def _ingest_batch(
        job: dict, cancel_event: threading.Event,
        progress_signal=None,
    ) -> list[dict]:
        from thlib import server_cache
        from thlib import tactic_classes as tc
        from thlib import tactic_query as tq

        project_code = str(job["projectCode"])
        paths = list(job["paths"])
        options = dict(job["options"])
        existing_by_path = dict(job.get("existingByPath") or {})
        prepared_by_path = dict(job.get("preparedByPath") or {})
        skip_paths = set(job.get("skipPaths") or ())
        message_batch = uuid.uuid4().hex
        results = []
        for index, path in enumerate(paths):
            if cancel_event.is_set():
                results.extend({
                    "path": pending,
                    "status": "Cancelled",
                    "error": "",
                } for pending in paths[index:])
                break
            try:
                if path in skip_paths:
                    record = {
                        "path": path,
                        "status": "Skipped",
                        "error": "Matching item already exists",
                    }
                    results.append(record)
                    if progress_signal is not None:
                        progress_signal.emit({
                            **record,
                            "progress": float(index + 1) / len(paths),
                        })
                    continue
                prepared = prepared_by_path.get(path)
                if prepared is None:
                    prepared = prepare_ingest_path(path, options)
                if not prepared["accepted"]:
                    record = {
                        "path": path,
                        "status": "Skipped",
                        "error": str(prepared.get("reason") or ""),
                    }
                    results.append(record)
                    if progress_signal is not None:
                        progress_signal.emit({
                            **record,
                            "progress": float(index + 1) / len(paths),
                        })
                    continue

                filename = os.path.basename(path)
                server = tc.server_start(project=project_code)
                server.upload_file(path)
                extra_data = dict(prepared.get("extraData") or {})
                search_keys = list(existing_by_path.get(path) or [])
                search_key = str(search_keys[0]) if len(search_keys) == 1 else ""
                update_existing = bool(search_key)
                validation_script = str(
                    options.get("validationScript") or ""
                )
                process_script = str(options.get("processScript") or "")
                if (
                    validation_script or process_script
                    or update_existing
                ):
                    preflight = tc.execute_procedure_serverside(
                        tq.ingest_rule_preflight,
                        {
                            "search_type": job["searchType"],
                            "parent_key": job["parentKey"],
                            "filename": filename,
                            "column": options["column"],
                            "ignore_ext": options["ignoreExtension"],
                            "extra_data": extra_data,
                            "validation_script": validation_script,
                            "process_script": process_script,
                            "search_key": search_key,
                        },
                        project=project_code,
                        server=server,
                    )
                    if not preflight.get("accepted"):
                        record = {
                            "path": path,
                            "status": "Skipped",
                            "error": str(preflight.get("reason") or ""),
                        }
                        results.append(record)
                        if progress_signal is not None:
                            progress_signal.emit({
                                **record,
                                "progress": float(index + 1) / len(paths),
                            })
                        continue
                    script_data = dict(preflight.get("data") or {})
                    for protected_name in (
                        "id", "__search_key__", "_search_type",
                        "search_type", "search_id", "timestamp",
                    ):
                        script_data.pop(protected_name, None)
                    extra_data.update(script_data)
                    snapshot_data = dict(
                        preflight.get("snapshot_data") or {}
                    )
                    prepared["context"] = str(
                        snapshot_data.get("context")
                        or prepared["context"]
                    )
                    search_key = str(
                        preflight.get("search_key") or search_key
                    )

                arguments = {
                    "search_type": job["searchType"],
                    "parent_key": job["parentKey"],
                    "filenames": [filename],
                    "update_data": {},
                    "extra_data": json.dumps(extra_data, ensure_ascii=False),
                    "process": options["process"],
                    "context": prepared["context"],
                    "update_mode": (
                        "true" if update_existing else "false"
                    ),
                    "ignore_ext": "true" if options["ignoreExtension"] else "false",
                    "column": options["column"],
                    "keywords": options.get("keywords", ""),
                    "keyword_mode": options.get("keywordMode", "default"),
                    "context_mode": options.get(
                        "contextMode", "case_sensitive"
                    ),
                    "create_icon": bool(options.get("createIcon", True)),
                    "project_code": project_code,
                    "message_key": "IngestUploadCmd|%s|%s-%s" % (
                        job["parentKey"], message_batch, index,
                    ),
                }
                if search_key:
                    arguments["search_key"] = search_key
                command_result = execute_ingest_with_relation(
                    server, arguments, job,
                    update_existing=update_existing,
                )
                results.append({
                    "path": path,
                    "status": "Completed",
                    "error": "",
                    "result": command_result,
                })
            except Exception as error:
                results.append({
                    "path": path,
                    "status": "Failed",
                    "error": str(error),
                    "stacktrace": traceback.format_exc(),
                })
            if progress_signal is not None:
                progress_signal.emit({
                    **results[-1],
                    "progress": float(index + 1) / len(paths),
                })
        if any(record["status"] == "Completed" for record in results):
            server_cache.invalidate_domains(
                ("search", "snapshots", "relations", "activity"),
                project_code,
            )
        return results

    @Slot(object)
    def _batch_progressed(self, value) -> None:
        if not isinstance(value, dict):
            return
        path = str(value.get("path") or "")
        records = [dict(record) for record in self.files._records]
        for record in records:
            if str(record.get("path") or "") == path:
                record["status"] = str(value.get("status") or "Running")
                record["error"] = self._display_result_error(
                    value.get("error")
                )
                break
        self.files.replace(records)
        self._progress = max(0.0, min(1.0, float(value.get("progress") or 0.0)))
        self._message = self.tr("Ingesting %1").replace(
            "%1", os.path.basename(path)
        )
        self.stateChanged.emit()

    def _batch_finished(self, generation: int, result) -> None:
        if generation != self._generation:
            return
        self._worker = None
        self._busy = False
        self._progress = 1.0
        results = list(result or [])
        by_path = {str(row.get("path") or ""): row for row in results}
        records = [dict(record) for record in self.files._records]
        for record in records:
            outcome = by_path.get(str(record.get("path") or ""))
            if outcome:
                record["status"] = str(outcome.get("status") or "Completed")
                record["error"] = self._display_result_error(
                    outcome.get("error")
                )
        self.files.replace(records)
        completed = sum(row.get("status") == "Completed" for row in results)
        failed = sum(row.get("status") == "Failed" for row in results)
        skipped = sum(row.get("status") == "Skipped" for row in results)
        self._message = self.tr("Ingest complete: %1 created").replace(
            "%1", str(completed)
        )
        self._error = "" if not failed else self.tr(
            "%1 file(s) failed; details remain in the ingest list"
        ).replace("%1", str(failed))
        for row in results:
            if row.get("status") != "Failed" or not self._debug_log:
                continue
            self._debug_log.log(
                "ERROR",
                str(row.get("error") or "Ingest failed"),
                stacktrace=str(row.get("stacktrace") or ""),
                group="ingest/files",
                source="Ingest Files",
            )
        if completed and self._application.workspace_model.node_for(
            self._relation_node_id
        ):
            self._application.refresh_current()
        summary = self.tr("Created %1 child item(s)").replace(
            "%1", str(completed)
        )
        if failed:
            summary += self.tr(", %1 failed").replace("%1", str(failed))
        if skipped:
            summary += self.tr(", %1 skipped").replace("%1", str(skipped))
        self._application.notify(summary)
        self.stateChanged.emit()
        self.batchFinished.emit(completed, failed)

    def _display_result_error(self, value) -> str:
        message = str(value or "")
        if message == "Matching item already exists":
            return self.tr("Matching item already exists")
        if message == "Matching item no longer exists":
            return self.tr("Matching item no longer exists")
        return message

    def _batch_failed(self, generation: int, error) -> None:
        if generation != self._generation:
            return
        payload = error[0] if isinstance(error, (tuple, list)) and error else error
        message = (
            payload.get("exception") if isinstance(payload, dict) else payload
        )
        stacktrace = (
            str(payload.get("stacktrace") or "")
            if isinstance(payload, dict) else ""
        )
        self._worker = None
        self._busy = False
        self._error = str(message or self.tr("Ingest failed"))
        if self._debug_log:
            self._debug_log.raise_error(
                message,
                stacktrace=stacktrace,
                group="ingest/files",
            )
        self.stateChanged.emit()

    @Slot()
    def cancel(self) -> None:
        if not self._busy:
            return
        self._cancel_event.set()
        self._message = self.tr("Stopping after the current file")
        self.stateChanged.emit()

    def _set_error(self, message: str) -> None:
        self._error = str(message or "")
        self.stateChanged.emit()

    @Slot(str)
    def save_rule(self, title: str) -> None:
        if self._busy or self._rule_mutation_worker is not None:
            return
        title = str(title or "").strip()
        if not title:
            self._set_error(self.tr("Enter a rule title"))
            return
        try:
            options = self._validated_options()
        except ValueError as error:
            self._set_error(str(error))
            return
        search_key = ""
        for record in self.rules._records:
            if record.get("ruleId") == self._selected_rule_id:
                search_key = str(record.get("searchKey") or "")
                break
        data = {
            "scan_type": "list",
            "action_type": "checkin",
            "action": "file",
            "search_type": self._target_search_type,
            "rule": options["pattern"],
            "filter": options["filter"],
            "ignore": options["ignore"],
            "column": options["column"],
            "ignore_ext": options["ignoreExtension"],
            "update_mode": options["updateMode"] == "update",
            "process": options["process"],
            "context": options["context"],
            "context_mode": options["contextMode"],
            "keywords": options["keywords"],
            "keyword_mode": options["keywordMode"],
            "extra_data": options["extraData"],
            "validation_script": options["validationScript"],
            "process_script": options["processScript"],
            "create_icon": options["createIcon"],
        }
        payload = {
            "title": title,
            "base_dir": "",
            "rule": options["pattern"],
            "data": json.dumps(data, ensure_ascii=False),
        }
        from thlib.environment import env_inst

        worker = env_inst.server_pool.add_task(
            self._save_rule_server,
            self._project_code,
            search_key,
            payload,
        )
        self._rule_mutation_worker = worker
        worker.result.connect(self._rule_saved)
        worker.error.connect(self._rule_mutation_failed)
        worker.start()

    @staticmethod
    def _save_rule_server(
        project_code: str, search_key: str, payload: dict,
    ) -> dict:
        from thlib import server_cache
        from thlib import tactic_classes as tc

        server = tc.server_start(project=project_code)
        if search_key:
            result = server.update(search_key, payload, triggers=True)
        else:
            result = server.insert(
                "config/ingest_rule", payload, triggers=True
            )
        server_cache.invalidate_domains(("reference",), project_code)
        return result

    @Slot()
    def delete_selected_rule(self) -> None:
        if (
            self._selected_rule_id == "builtin" or self._busy
            or self._rule_mutation_worker is not None
        ):
            return
        search_key = next((
            str(record.get("searchKey") or "")
            for record in self.rules._records
            if record.get("ruleId") == self._selected_rule_id
        ), "")
        if not search_key:
            return
        from thlib.environment import env_inst

        worker = env_inst.server_pool.add_task(
            self._delete_rule_server, self._project_code, search_key
        )
        self._rule_mutation_worker = worker
        worker.result.connect(self._rule_saved)
        worker.error.connect(self._rule_mutation_failed)
        worker.start()

    @staticmethod
    def _delete_rule_server(project_code: str, search_key: str) -> bool:
        from thlib import server_cache
        from thlib import tactic_classes as tc

        server = tc.server_start(project=project_code)
        server.delete_sobject(search_key)
        server_cache.invalidate_domains(("reference",), project_code)
        return True

    def _rule_saved(self, _result) -> None:
        self._rule_mutation_worker = None
        self._selected_rule_id = "builtin"
        self._application.notify(self.tr("Ingest rules updated"))
        self._load_rules()

    def _rule_mutation_failed(self, error) -> None:
        self._rule_mutation_worker = None
        payload = error[0] if isinstance(error, (tuple, list)) and error else error
        message = (
            payload.get("exception") if isinstance(payload, dict) else payload
        )
        self._set_error(str(message or self.tr("Could not save ingest rule")))

    def shutdown(self) -> None:
        self._cancel_event.set()
        self._preflight.reset()
        self._generation += 1
        self._rules_generation += 1

    @Property(str, notify=stateChanged)
    def parentTitle(self) -> str:
        return self._parent_title

    @Property(str, notify=stateChanged)
    def targetTitle(self) -> str:
        return self._target_title

    @Property(str, notify=stateChanged)
    def searchType(self) -> str:
        return self._target_search_type

    @Property("QVariantMap", notify=stateChanged)
    def options(self) -> dict:
        return dict(self._options)

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=rulesChanged)
    def rulesBusy(self) -> bool:
        return self._rules_busy

    @Property(bool, notify=stateChanged)
    def canDeleteRule(self) -> bool:
        return self._selected_rule_id != "builtin" and not self._busy

    @Property(bool, notify=stateChanged)
    def conflictPending(self) -> bool:
        return bool(self._preflight.pending)

    @Property(int, notify=stateChanged)
    def conflictCount(self) -> int:
        return len(self._preflight.pending.get("conflicts") or ())

    @Property("QVariantList", notify=stateChanged)
    def conflictNames(self) -> list[str]:
        names = []
        for row in self._preflight.pending.get("conflicts") or ():
            name = str(row.get("name") or "")
            if name and name not in names:
                names.append(name)
        return names

    @Property(bool, notify=stateChanged)
    def canUpdateConflicts(self) -> bool:
        return bool(self._preflight.pending.get("canUpdate"))

    @Property(int, notify=stateChanged)
    def fileCount(self) -> int:
        return len(self.files._records)

    @Property(float, notify=stateChanged)
    def progress(self) -> float:
        return self._progress

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error
