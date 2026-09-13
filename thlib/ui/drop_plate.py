from __future__ import annotations

import os
from pathlib import Path
import uuid

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot, Qt
from PySide6.QtGui import QGuiApplication

from thlib.environment import env_read_config, env_write_config
from .workspace_models.records import RecordListModel


class DropPlateController(QObject):
    stateChanged = Signal()

    def __init__(
        self, application_controller, checkin_controller,
        commit_queue, matching_templates, parent=None,
    ) -> None:
        super().__init__(parent)
        self._application = application_controller
        self._checkin = checkin_controller
        self._commit_queue = commit_queue
        self._matching_templates = matching_templates
        self._objects: dict[str, object] = {}
        self._busy_count = 0
        self._error = ""
        self._settings = dict(env_read_config(
            filename="ui_drop_plate",
            unique_id="ui_main",
            long_abs_path=True,
        ) or {})
        self._recursive = self._load_checkin_bool(
            "includeSubfoldersCheckBox", "dropPlate/includeSubfolders", False
        )
        self._group_checkin = self._load_group_checkin()
        self._rematch_pending = False
        self.model = RecordListModel((
            "groupId", "title", "path", "fileCount", "size", "process",
            "context", "checked", "status", "matchingType",
            "sequenceInfo", "extension", "mappedTarget", "error",
        ))
        self._matching_templates.templatesChanged.connect(
            self._templates_changed
        )
        self._commit_queue.operationCompleted.connect(
            self._queue_operation_completed
        )

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy_count > 0

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error

    @Property(bool, notify=stateChanged)
    def recursive(self) -> bool:
        return self._recursive

    @Property(int, notify=stateChanged)
    def count(self) -> int:
        return len(self.model._records)

    @Property(bool, notify=stateChanged)
    def hasChecked(self) -> bool:
        return any(record.get("checked") for record in self.model._records)

    @Property(int, notify=stateChanged)
    def checkedCount(self) -> int:
        return sum(
            1 for record in self.model._records if record.get("checked")
        )

    @Property(bool, notify=stateChanged)
    def groupCheckin(self) -> bool:
        return self._group_checkin

    @Slot(bool)
    def set_group_checkin(self, value: bool) -> None:
        value = bool(value)
        if value == self._group_checkin:
            return
        self._group_checkin = value
        self._settings["dropPlate/groupCheckin"] = value
        self._write_settings()
        self._save_checkin_bool("groupCheckinCheckBox", value)
        self.stateChanged.emit()

    def _load_group_checkin(self) -> bool:
        return self._load_checkin_bool(
            "groupCheckinCheckBox", "dropPlate/groupCheckin", False
        )

    def _load_checkin_bool(
        self, control: str, setting: str, default: bool,
    ) -> bool:
        fallback = bool(self._settings.get(setting, default))
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin() or {}, control
            )
            return fallback if value in (None, "") else bool(int(value))
        except (AttributeError, TypeError, ValueError):
            return fallback

    @staticmethod
    def _save_checkin_bool(control: str, value: bool) -> None:
        try:
            from thlib.environment import cfg_controls

            config = dict(cfg_controls.get_checkin() or {})
            bucket = dict(config.get("QCheckBox") or {})
            names = list(bucket.get("obj_name") or [])
            values = list(bucket.get("value") or [])
            if control in names:
                index = names.index(control)
                while len(values) <= index:
                    values.append(None)
                values[index] = int(value)
            else:
                names.append(control)
                values.append(int(value))
            bucket["obj_name"] = names
            bucket["value"] = values
            config["QCheckBox"] = bucket
            cfg_controls.set_checkin(config)
        except (AttributeError, TypeError):
            pass

    def _write_settings(self) -> None:
        env_write_config(
            self._settings,
            filename="ui_drop_plate",
            unique_id="ui_main",
            long_abs_path=True,
        )

    @Slot()
    def reload_configuration(self) -> None:
        value = self._load_group_checkin()
        recursive = self._load_checkin_bool(
            "includeSubfoldersCheckBox", "dropPlate/includeSubfolders", False
        )
        if value != self._group_checkin or recursive != self._recursive:
            self._group_checkin = value
            self._recursive = recursive
            self.stateChanged.emit()

    @Slot(bool)
    def set_recursive(self, value: bool) -> None:
        value = bool(value)
        if value == self._recursive:
            return
        self._recursive = value
        self._settings["dropPlate/includeSubfolders"] = value
        self._write_settings()
        self._save_checkin_bool("includeSubfoldersCheckBox", value)
        self.stateChanged.emit()

    @staticmethod
    def _local_paths(values: list) -> list[str]:
        paths = []
        for value in values or []:
            url = value if isinstance(value, QUrl) else QUrl(str(value))
            path = url.toLocalFile() if url.isLocalFile() else str(value)
            if path:
                paths.append(path)
        return paths

    @staticmethod
    def _minimum_frame_padding() -> int:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin() or {},
                "minFramesPaddingSpinBox",
                3,
            )
            return max(1, min(9, int(value)))
        except (AttributeError, TypeError, ValueError):
            return 3

    @Slot("QVariantList")
    def add_paths(self, values: list) -> None:
        self._start_add_paths(values, False)

    @Slot("QVariantList")
    def add_paths_and_queue(
        self, values: list, group_checkin: bool | None = None,
    ) -> None:
        queue_options = None
        patterns = None
        if group_checkin is not None:
            queue_options = {"groupCheckin": bool(group_checkin)}
            if not group_checkin:
                patterns = ("$FILENAME.$EXT", "$FILENAME")
        self._start_add_paths(
            values, True, queue_options=queue_options, patterns=patterns
        )

    def add_dropped_paths(
        self, values: list, icon_target: bool = False,
        group_checkin: bool = False,
    ) -> None:
        queue_options = {
            "description": "Drag-Drop Checkin",
            "groupCheckin": bool(group_checkin),
        }
        if icon_target:
            queue_options["updateVersionless"] = False
        self._start_add_paths(
            values,
            True,
            queue_options=queue_options,
            patterns=("$FILENAME.$EXT",),
            allow_directories=False,
        )

    def _start_add_paths(
        self, values: list, queue_when_ready: bool,
        replace_existing: bool = False,
        queue_options: dict | None = None,
        patterns: tuple[str, ...] | None = None,
        allow_directories: bool = True,
    ) -> None:
        paths = self._local_paths(values)
        if not paths:
            return
        from thlib.environment import env_inst

        worker = env_inst.local_pool.add_task(
            self._collect_groups,
            paths,
            self._recursive,
            patterns or tuple(self._matching_templates.active_patterns(
                self._checkin.process, self._checkin.context
            )),
            self._minimum_frame_padding(),
            allow_directories,
        )
        if worker is None:
            self._error = "Local worker pool is unavailable"
            self.stateChanged.emit()
            return
        self._busy_count += 1
        self._error = ""
        self.stateChanged.emit()
        worker.result.connect(
            lambda result, auto_queue=queue_when_ready,
            replace=replace_existing,
            options=dict(queue_options or {}): self._groups_ready(
                result, auto_queue=auto_queue, replace_existing=replace,
                queue_options=options,
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._groups_failed,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.finished.connect(
            self._collection_finished,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot("QVariantList", str, str, "QVariantList")
    def add_watch_paths(
        self, values: list, process: str, context: str, templates: list
    ) -> None:
        paths = self._local_paths(values)
        if not paths:
            return
        from thlib.environment import env_inst

        worker = env_inst.local_pool.add_task(
            self._collect_groups, paths, True, tuple(templates or ()),
            self._minimum_frame_padding(),
        )
        if worker is None:
            self._error = "Local worker pool is unavailable"
            self.stateChanged.emit()
            return
        self._busy_count += 1
        self._error = ""
        self.stateChanged.emit()
        worker.result.connect(
            lambda result: self._groups_ready(result, process, context),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._groups_failed, Qt.ConnectionType.QueuedConnection
        )
        worker.finished.connect(
            self._collection_finished, Qt.ConnectionType.QueuedConnection
        )
        worker.start()

    @staticmethod
    def _collect_groups(
        values: list[str], recursive: bool, templates: tuple[str, ...],
        padding: int, allow_directories: bool = True,
    ) -> dict:
        import thlib.global_functions as gf

        files = []
        errors = []
        known = set()
        for value in values:
            path = Path(value)
            try:
                path = path.resolve(strict=True)
            except OSError as error:
                errors.append(f"{path}: {error}")
                continue
            if path.is_file():
                key = os.path.normcase(str(path))
                if key not in known:
                    files.append(str(path))
                    known.add(key)
                continue
            if not path.is_dir():
                errors.append(f"{path}: unsupported path")
                continue
            if not allow_directories:
                errors.append(f"{path}: only files can be dropped on an item")
                continue
            iterator = path.rglob("*") if recursive else path.iterdir()
            try:
                for child in iterator:
                    try:
                        if not child.is_file():
                            continue
                        resolved = child.resolve(strict=True)
                    except OSError as error:
                        errors.append(f"{child}: {error}")
                        continue
                    key = os.path.normcase(str(resolved))
                    if key not in known:
                        files.append(str(resolved))
                        known.add(key)
            except OSError as error:
                errors.append(f"{path}: {error}")
        groups = gf.MatchTemplate(
            list(templates), padding=padding
        ).get_files_objects(files)
        return {"groups": groups, "errors": errors}

    @staticmethod
    def _pretty_size(value: int) -> str:
        size = float(value)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return (
                    f"{size:.0f} {unit}" if unit == "B"
                    else f"{size:.1f} {unit}"
                )
            size /= 1024
        return ""

    def _groups_ready(
        self, result, watch_process: str = "", watch_context: str = "",
        auto_queue: bool = False, replace_existing: bool = False,
        queue_options: dict | None = None,
    ) -> None:
        groups = (result or {}).get("groups") or {}
        errors = list((result or {}).get("errors") or [])
        records = [] if replace_existing else list(self.model._records)
        object_store = {} if replace_existing else self._objects
        identities = {
            tuple(
                os.path.normcase(path)
                for path in self._object_paths(self._objects.get(
                    record["groupId"]
                ))
            )
            for record in records
        }
        added_group_ids = []
        for matching_type, objects in groups.items():
            for file_object in objects:
                paths = self._object_paths(file_object)
                identity = tuple(os.path.normcase(path) for path in paths)
                if not paths or identity in identities:
                    continue
                group_id = uuid.uuid4().hex
                object_store[group_id] = file_object
                added_group_ids.append(group_id)
                identities.add(identity)
                try:
                    size = sum(Path(path).stat().st_size for path in paths)
                except OSError:
                    size = 0
                sequence_parts = []
                frames = file_object.get_sequence_frameranges_string("[]")
                tiles = file_object.get_tiles_count()
                layer = file_object.get_layer()
                if frames:
                    sequence_parts.append(str(frames))
                if tiles:
                    sequence_parts.append(f"{tiles} tile(s)")
                if layer:
                    sequence_parts.append(str(layer))
                process = watch_process
                context = watch_context
                records.append({
                    "groupId": group_id,
                    "title": file_object.get_pretty_file_name(),
                    "path": file_object.get_file_path(),
                    "fileCount": len(paths),
                    "size": self._pretty_size(size),
                    "process": process,
                    "context": context,
                    "checked": True,
                    "status": "Matched",
                    "matchingType": str(matching_type),
                    "sequenceInfo": " • ".join(sequence_parts),
                    "extension": str(file_object.get_file_ext() or "").lower(),
                    "mappedTarget": bool(watch_process or watch_context),
                    "error": "",
                })
        if replace_existing:
            self._objects = object_store
        self.model.replace(records)
        self._error = "; ".join(errors[:3])
        self.stateChanged.emit()
        if auto_queue and added_group_ids:
            self._add_group_ids_to_queue(added_group_ids, queue_options)

    @Slot(object)
    def _groups_failed(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) and error else error
        exception = (
            payload.get("exception")
            if isinstance(payload, dict) else payload
        )
        stacktrace = (
            str(payload.get("stacktrace") or "")
            if isinstance(payload, dict) else ""
        )
        self._error = str(exception or "File matching failed")
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                exception,
                stacktrace=stacktrace,
                group="drop_plate/matching",
            )
        self._collection_finished()
        self.stateChanged.emit()

    @Slot()
    def _collection_finished(self) -> None:
        self._busy_count = max(0, self._busy_count - 1)
        self.stateChanged.emit()
        if not self._busy_count and self._rematch_pending:
            self._rematch_pending = False
            self._templates_changed()

    @Slot()
    def _templates_changed(self) -> None:
        if self.busy:
            self._rematch_pending = True
            return
        paths = []
        for file_object in self._objects.values():
            paths.extend(self._object_paths(file_object))
        if paths:
            self._start_add_paths(paths, False, replace_existing=True)
        else:
            self.stateChanged.emit()

    @staticmethod
    def _object_paths(file_object) -> list[str]:
        if file_object is None:
            return []
        try:
            return [str(path) for path in file_object.get_all_files_list()]
        except (AttributeError, TypeError):
            return []

    @Slot(int)
    def toggle_checked(self, row: int) -> None:
        self.model.toggle_checked(row)
        self.stateChanged.emit()

    @Slot(str)
    def toggle_checked_id(self, group_id: str) -> None:
        row = self._row_for_group(group_id)
        if row >= 0:
            self.toggle_checked(row)

    @Slot(int)
    def remove(self, row: int) -> None:
        if not 0 <= row < len(self.model._records):
            return
        group_id = self.model._records[row]["groupId"]
        self._objects.pop(group_id, None)
        self.model.remove(row)
        self.stateChanged.emit()

    @Slot(str)
    def remove_id(self, group_id: str) -> None:
        row = self._row_for_group(group_id)
        if row >= 0:
            self.remove(row)

    def _row_for_group(self, group_id: str) -> int:
        return next((
            row for row, record in enumerate(self.model._records)
            if record.get("groupId") == group_id
        ), -1)

    @Slot(str)
    def open_file(self, group_id: str) -> None:
        file_object = self._objects.get(group_id)
        if file_object is not None:
            file_object.open_file()

    @Slot(str)
    def show_folder(self, group_id: str) -> None:
        file_object = self._objects.get(group_id)
        if file_object is not None:
            file_object.open_folder()

    @Slot(str, bool)
    def copy_path(self, group_id: str, all_files: bool = False) -> None:
        file_object = self._objects.get(group_id)
        if file_object is None:
            return
        paths = self._object_paths(file_object)
        text = "\n".join(paths) if all_files else str(
            file_object.get_file_path() or (paths[0] if paths else "")
        )
        QGuiApplication.clipboard().setText(text)

    @Slot()
    def paste_paths(self) -> None:
        clipboard = QGuiApplication.clipboard()
        mime = clipboard.mimeData()
        if mime.hasUrls():
            self.add_paths(list(mime.urls()))
            return
        values = [
            value.strip().strip('"')
            for value in clipboard.text().splitlines()
            if value.strip()
        ]
        self.add_paths(values)

    @Slot()
    def clear(self) -> None:
        self._objects.clear()
        self.model.clear()
        self._error = ""
        self.stateChanged.emit()

    @Slot()
    def add_selected_to_queue(
        self, group_checkin: bool | None = None,
    ) -> None:
        if not self._checkin.actionAvailable:
            self._error = "Select an object, process and context first"
            self.stateChanged.emit()
            return
        group_ids = [
            record["groupId"] for record in self.model._records
            if record.get("checked")
        ]
        queue_options = None
        if group_checkin is not None:
            queue_options = {"groupCheckin": bool(group_checkin)}
        self._add_group_ids_to_queue(group_ids, queue_options)

    def _add_group_ids_to_queue(
        self, group_ids: list[str], queue_options: dict | None = None,
    ) -> None:
        if not self._checkin.actionAvailable:
            self._error = "Select an object, process and context first"
            self.stateChanged.emit()
            return
        selected_ids = set(group_ids)
        base_payload = self._checkin.operation_payload()
        queue_options = dict(queue_options or {})
        force_individual = bool(queue_options.pop("forceIndividual", False))
        group_override = queue_options.pop("groupCheckin", None)
        base_payload.update(queue_options)
        title = str(
            self._checkin.currentObject.get("title")
            or self._checkin.currentObject.get("code")
            or "sObject"
        )
        selected_records = [
            record for record in self.model._records
            if record.get("groupId") in selected_ids
            and self._objects.get(record.get("groupId")) is not None
        ]
        added = 0
        queued_groups = set()
        group_checkin = (
            self._group_checkin
            if group_override is None
            else bool(group_override)
        ) and not force_individual
        if group_checkin:
            grouped_records = {}
            for record in selected_records:
                if record.get("mappedTarget"):
                    key = (
                        str(record.get("process") or self._checkin.process),
                        str(record.get("context") or self._checkin.context),
                    )
                else:
                    key = (
                        str(base_payload.get("process") or "publish"),
                        str(base_payload.get("context") or "publish"),
                    )
                grouped_records.setdefault(key, []).append(record)
            for (process, context), group_records in grouped_records.items():
                payload = dict(base_payload)
                payload["process"] = process
                payload["context"] = context
                payload["files"] = []
                payload["filesDict"] = []
                payload["dropPlateGroupIds"] = []
                for record in group_records:
                    files, files_dict = self._payload_files(
                        self._objects[record["groupId"]]
                    )
                    payload["files"].extend(files)
                    payload["filesDict"].extend(files_dict)
                    payload["dropPlateGroupIds"].append(record["groupId"])
                self._commit_queue.add_prepared(payload, title)
                queued_groups.update(
                    record["groupId"] for record in group_records
                )
                added += 1
        records = []
        for source_record in self.model._records:
            record = dict(source_record)
            if record.get("groupId") not in selected_ids:
                records.append(record)
                continue
            if group_checkin:
                if record.get("groupId") in queued_groups:
                    self._objects.pop(record["groupId"], None)
                    continue
                records.append(record)
                continue
            file_object = self._objects.get(record["groupId"])
            if file_object is None:
                records.append(record)
                continue
            payload = dict(base_payload)
            if record.get("mappedTarget"):
                payload["process"] = str(
                    record.get("process") or self._checkin.process
                )
                payload["context"] = str(
                    record.get("context") or self._checkin.context
                )
            payload["files"], payload["filesDict"] = self._payload_files(
                file_object
            )
            payload["dropPlateGroupIds"] = [record["groupId"]]
            self._commit_queue.add_prepared(payload, title)
            self._objects.pop(record["groupId"], None)
            added += 1
        if added:
            self.model.replace(records)
            self._application.window_model.show_window("commit_queue")
            self._error = ""
        else:
            self._error = "Select at least one matched item"
        self.stateChanged.emit()

    @staticmethod
    def _checkin_config_flag(control: str, default: bool) -> bool:
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls

            value = gf.get_value_from_config(
                cfg_controls.get_checkin() or {}, control
            )
            return default if value in (None, "") else bool(int(value))
        except (AttributeError, TypeError, ValueError):
            return default

    @Slot("QVariantMap")
    def _queue_operation_completed(self, payload: dict) -> None:
        group_ids = set(payload.get("dropPlateGroupIds") or [])
        if not group_ids:
            return
        clear_completed = self._checkin_config_flag(
            "clearDropPlateAfterCheckincheckBox", True
        )
        uncheck_completed = self._checkin_config_flag(
            "uncheckFromDropPlateCheckBox", True
        )
        records = []
        for source in self.model._records:
            record = dict(source)
            group_id = record.get("groupId")
            if group_id not in group_ids:
                records.append(record)
                continue
            if clear_completed:
                self._objects.pop(group_id, None)
                continue
            record["status"] = "Completed"
            if uncheck_completed:
                record["checked"] = False
            records.append(record)
        self.model.replace(records)
        self.stateChanged.emit()

    @staticmethod
    def _payload_files(file_object) -> tuple[list[dict], list]:
        paths = DropPlateController._object_paths(file_object)
        extension = str(file_object.get_file_ext() or "").lower()
        file_type = str(file_object.get_base_file_type() or "file")
        metadata = dict(file_object.get_metadata() or {})
        metadata["name_part"] = file_object.get_name_part()
        template = str(
            metadata.get("new_template")
            or metadata.get("template")
            or "$FILENAME.$EXT"
        )
        files = [{
            "path": paths[0] if paths else file_object.get_file_path(),
            "paths": paths,
            "template": template,
            "type": file_type,
            "extension": extension,
        }]
        values = {
            "t": [file_type],
            "s": [""],
            "e": [extension],
            "p": [""],
            "m": metadata,
        }
        return files, [(file_object.get_file_name(True), values)]
