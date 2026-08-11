from __future__ import annotations

from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET

from .workflow_data import process_task_configuration


class QuickFilterCatalog:

    def __init__(self, source: Path | None = None) -> None:
        source = source or Path(__file__).with_name("quick_filters.xml")
        self._definitions = self._read(source)
        self._configurations: dict[str, dict] = {}

    @staticmethod
    def _read(source: Path) -> dict[str, list[dict]]:
        definitions = {}
        root = ET.parse(source).getroot()
        for search_type in root.findall("search-type"):
            groups = []
            for element in search_type.findall("group"):
                groups.append({
                    "key": element.get("key", ""),
                    "title": element.get("title", ""),
                    "source": element.get("source", "values"),
                    "columns": [
                        value.strip()
                        for value in element.get("columns", "").split(",")
                        if value.strip()
                    ],
                    "accent": element.get("accent", "#607d8b"),
                    "options": [
                        {
                            "key": option.get("key", ""),
                            "title": option.get("title", ""),
                            "minimum": option.get("minimum"),
                            "maximum": option.get("maximum"),
                        }
                        for option in element.findall("option")
                    ],
                })
            definitions[search_type.get("code", "")] = groups
        return definitions

    def _definitions_for(self, search_type) -> list[dict]:
        specific = list(self._definitions.get(str(search_type or ""), ()))
        known = {definition["key"] for definition in specific}
        definitions = specific + [
            definition for definition in self._definitions.get("*", ())
            if definition["key"] not in known
        ]
        return self._configured_definitions(search_type, definitions)

    def _base_definitions_for(self, search_type) -> list[dict]:
        specific = list(self._definitions.get(str(search_type or ""), ()))
        known = {definition["key"] for definition in specific}
        return deepcopy(specific + [
            definition for definition in self._definitions.get("*", ())
            if definition["key"] not in known
        ])

    def _configured_definitions(self, search_type, definitions) -> list[dict]:
        configuration = self._configurations.get(str(search_type or "")) or {}
        configured = {
            str(record.get("key") or ""): record
            for record in configuration.get("groups", ())
            if isinstance(record, dict) and record.get("key")
        }
        if not configured:
            return deepcopy(definitions)
        by_key = {definition["key"]: definition for definition in definitions}
        ordered_keys = [
            str(record.get("key") or "")
            for record in configuration.get("groups", ())
            if isinstance(record, dict)
        ]
        ordered_keys.extend(key for key in by_key if key not in ordered_keys)
        result = []
        for key in ordered_keys:
            definition = by_key.get(key)
            if not definition:
                continue
            settings = configured.get(key, {})
            if settings.get("enabled", True) is False:
                continue
            definition = deepcopy(definition)
            allowed = settings.get("options")
            if isinstance(allowed, list):
                allowed = {str(value) for value in allowed}
                definition["allowed_options"] = allowed
                if definition["source"] == "ranges":
                    definition["options"] = [
                        option for option in definition["options"]
                        if option["key"] in allowed
                    ]
            result.append(definition)
        return result

    def set_configuration(self, search_type, configuration) -> None:
        key = str(search_type or "")
        if configuration and configuration.get("groups"):
            self._configurations[key] = deepcopy(configuration)
        else:
            self._configurations.pop(key, None)

    def configuration(self, search_type) -> dict:
        return deepcopy(self._configurations.get(str(search_type or ""), {}))

    def editor_groups(
            self, search_type, stype, sobjects, task_records=None
    ) -> list[dict]:
        """Return every available group, including groups hidden by config."""
        definitions = self._base_definitions_for(search_type)
        configuration = self.configuration(search_type)
        settings_by_key = {
            str(record.get("key") or ""): record
            for record in configuration.get("groups", ())
            if isinstance(record, dict)
        }
        order = [
            str(record.get("key") or "")
            for record in configuration.get("groups", ())
            if isinstance(record, dict)
        ]
        by_key = {definition["key"]: definition for definition in definitions}
        order.extend(key for key in by_key if key not in order)
        records = []
        for key in order:
            definition = by_key.get(key)
            if not definition:
                continue
            options = self._options(
                definition, stype, sobjects, task_records or {}
            )
            settings = settings_by_key.get(key, {})
            configured_options = settings.get("options")
            enabled_options = (
                {str(value) for value in configured_options}
                if isinstance(configured_options, list) else None
            )
            records.append({
                "key": key,
                "title": self._group_title(definition, stype),
                "accent": definition["accent"],
                "enabled": settings.get("enabled", True) is not False,
                "options": [
                    {
                        "key": option["key"],
                        "title": option["title"],
                        "accent": option.get("accent", definition["accent"]),
                        "showAccentMarker": bool(
                            option.get("showAccentMarker")
                        ),
                        "enabled": (
                            enabled_options is None
                            or option["key"] in enabled_options
                        ),
                    }
                    for option in options
                ],
            })
        return records

    def requires_tasks(self, search_type) -> bool:
        return any(
            definition["source"] in {"task_processes", "task_statuses"}
            for definition in self._definitions_for(search_type)
        )

    def groups(
            self, search_type, stype, sobjects, selected,
            task_records=None) -> list[dict]:
        definitions = self._definitions_for(search_type)
        records = []
        for definition in definitions:
            options = self._options(
                definition, stype, sobjects, task_records or {}
            )
            selected_keys = selected.get(definition["key"], set())
            if not options and not selected_keys:
                continue
            known_keys = {option["key"] for option in options}
            options.extend(
                {
                    "key": value,
                    "title": str(value).replace("_", " ").upper(),
                    "accent": definition["accent"],
                    "showAccentMarker": False,
                }
                for value in sorted(selected_keys - known_keys)
            )
            records.append({
                "key": definition["key"],
                "title": self._group_title(definition, stype),
                "accent": definition["accent"],
                "allSelected": not selected_keys,
                "options": [
                    {
                        "key": option["key"],
                        "title": option["title"],
                        "selected": option["key"] in selected_keys,
                        "accent": option.get("accent", definition["accent"]),
                        "showAccentMarker": bool(
                            option.get("showAccentMarker")
                        ),
                    }
                    for option in options
                ],
            })
        return records

    def filter(
            self, search_type, sobjects, selected, task_records=None,
            loaded_task_codes=None) -> list:
        definitions = self._definitions_for(search_type)
        active = {
            key: set(values)
            for key, values in selected.items()
            if values
        }
        if not active:
            return list(sobjects)
        return [
            sobject
            for sobject in sobjects
            if all(
                self._matches(
                    sobject,
                    definition,
                    active[definition["key"]],
                    task_records or {},
                    loaded_task_codes or set(),
                )
                for definition in definitions
                if definition["key"] in active
            )
        ]

    def _options(self, definition, stype, sobjects, task_records) -> list[dict]:
        if definition["source"] == "ranges":
            return self._limit_options(definition, definition["options"])
        if definition["source"] == "task_processes":
            return self._limit_options(
                definition,
                self._task_process_options(stype, sobjects, task_records),
            )
        if definition["source"] == "task_statuses":
            return self._limit_options(
                definition,
                self._task_status_options(stype, sobjects, task_records),
            )
        if definition["source"] == "pipelines":
            return self._limit_options(definition, (
                self._pipeline_options(stype, sobjects)
                if self._is_asset_stype(stype) else []
            ))
        if (
                definition["source"] == "asset_categories"
                and not self._is_asset_stype(stype)):
            return []
        values = set()
        if definition["source"] == "processes":
            values.update(self._pipeline_processes(stype))
            for sobject in sobjects:
                try:
                    values.update((sobject.get_all_processes() or {}).keys())
                except (AttributeError, TypeError):
                    continue
        else:
            values.update(self._column_choices(stype, definition["columns"]))
            for sobject in sobjects:
                value = self._first_value(sobject, definition["columns"])
                if value not in (None, ""):
                    values.add(str(value))
        options = [
            {
                "key": value,
                "title": str(value).replace("_", " ").upper(),
            }
            for value in sorted(values, key=lambda item: str(item).lower())
        ]
        return self._limit_options(definition, options)

    @staticmethod
    def _limit_options(definition, options):
        allowed = definition.get("allowed_options")
        if allowed is None:
            return options
        return [option for option in options if option["key"] in allowed]

    @staticmethod
    def _column_choices(stype, columns) -> set[str]:
        try:
            columns_info = stype.get_columns_info() or {}
        except (AttributeError, TypeError):
            return set()
        values = set()
        for column in columns:
            info = columns_info.get(column) or {}
            source = (
                info.get("values")
                or info.get("choices")
                or info.get("options")
            )
            if isinstance(source, dict):
                values.update(str(value) for value in source)
            elif isinstance(source, (list, tuple, set)):
                for value in source:
                    if isinstance(value, dict):
                        value = (
                            value.get("value")
                            or value.get("code")
                            or value.get("label")
                        )
                    if value not in (None, ""):
                        values.add(str(value))
            elif isinstance(source, str):
                separator = "|" if "|" in source else ","
                values.update(
                    value.strip()
                    for value in source.split(separator)
                    if value.strip()
                )
        return values

    @staticmethod
    def _pipeline_processes(stype) -> set[str]:
        values = set()
        try:
            pipelines = (stype.get_pipeline() or {}).values()
        except (AttributeError, TypeError):
            return values
        for pipeline in pipelines:
            try:
                values.update(pipeline.get_process_names() or ())
            except (AttributeError, TypeError):
                values.update((getattr(pipeline, "pipeline", None) or {}).keys())
        return {str(value) for value in values if value}

    @staticmethod
    def _info(sobject) -> dict:
        try:
            return dict(sobject.get_info() or {})
        except (AttributeError, TypeError, ValueError):
            return dict(getattr(sobject, "info", {}) or {})

    @classmethod
    def _first_value(cls, sobject, columns):
        info = cls._info(sobject)
        for column in columns:
            value = info.get(column)
            if value not in (None, ""):
                return value
        return None

    @classmethod
    def _matches(
            cls, sobject, definition, selected, task_records,
            loaded_task_codes) -> bool:
        source = definition["source"]
        if source in {"task_processes", "task_statuses"}:
            code = cls._sobject_code(sobject)
            # Keep the result stable while the one batch query is in flight.
            # Once the code is marked loaded an empty list correctly means the
            # parent has no matching task.
            if code not in loaded_task_codes:
                return True
            column = "process" if source == "task_processes" else "status"
            values = {
                str(cls._info(task).get(column) or "")
                for task in task_records.get(code, ())
            }
            return bool(values.intersection(selected))
        if source == "pipelines":
            try:
                value = str(sobject.get_pipeline_code() or "")
            except AttributeError:
                value = str(cls._info(sobject).get("pipeline_code") or "")
            return value in selected
        if source == "processes":
            try:
                processes = set((sobject.get_all_processes() or {}).keys())
            except (AttributeError, TypeError):
                processes = set()
            return bool(processes.intersection(selected))
        if source == "ranges":
            value = cls._duration_seconds(
                cls._first_value(sobject, definition["columns"])
            )
            if value is None:
                return False
            ranges = {
                option["key"]: option
                for option in definition["options"]
            }
            return any(
                cls._inside_range(value, ranges[key])
                for key in selected
                if key in ranges
            )
        value = cls._first_value(sobject, definition["columns"])
        return str(value) in selected

    @classmethod
    def _sobject_code(cls, sobject) -> str:
        try:
            return str(sobject.get_code() or "")
        except AttributeError:
            return str(cls._info(sobject).get("code") or "")

    @classmethod
    def _ordered_pipelines(cls, stype, sobjects):
        try:
            pipelines = dict(stype.get_pipeline() or {})
        except (AttributeError, TypeError, ValueError):
            return []
        preferred = []
        for sobject in sobjects:
            try:
                code = str(sobject.get_pipeline_code() or "")
            except AttributeError:
                code = str(cls._info(sobject).get("pipeline_code") or "")
            if code and code not in preferred:
                preferred.append(code)
        ordered_codes = list(dict.fromkeys([*preferred, *pipelines]))
        return [pipelines[code] for code in ordered_codes if code in pipelines]

    @classmethod
    def _pipeline_process_names(cls, pipeline) -> list[str]:
        names = []
        try:
            names.extend(pipeline.get_all_pipeline_names() or ())
        except AttributeError:
            names.extend((getattr(pipeline, "pipeline", {}) or {}).keys())
        try:
            configured = pipeline.get_all_pipeline_process() or ()
        except (AttributeError, KeyError, TypeError):
            configured = ()
        for process in configured:
            if isinstance(process, dict):
                name = process.get("process") or process.get("name")
            else:
                name = ""
            if name:
                names.append(str(name))
        return list(dict.fromkeys(str(name) for name in names if name))

    @classmethod
    def _pipeline_options(cls, stype, sobjects) -> list[dict]:
        records = {}
        for pipeline in cls._ordered_pipelines(stype, sobjects):
            try:
                info = dict(pipeline.get_info() or {})
            except (AttributeError, TypeError, ValueError):
                info = dict(getattr(pipeline, "info", {}) or {})
            code = str(info.get("code") or "")
            if not code:
                continue
            records[code] = {
                "key": code,
                "title": str(
                    info.get("title") or info.get("name") or code
                ).replace("_", " ").upper(),
                "accent": str(info.get("color") or "#607d8b"),
                "showAccentMarker": bool(info.get("color")),
            }
        for sobject in sobjects:
            try:
                code = str(sobject.get_pipeline_code() or "")
            except AttributeError:
                code = str(cls._info(sobject).get("pipeline_code") or "")
            if code:
                records.setdefault(code, {
                    "key": code,
                    "title": code.replace("_", " ").upper(),
                    "accent": "#607d8b",
                    "showAccentMarker": False,
                })
        return sorted(records.values(), key=lambda item: item["title"].lower())

    @staticmethod
    def _stype_code(stype) -> str:
        try:
            return str(stype.get_code() or "")
        except AttributeError:
            return str((getattr(stype, "info", {}) or {}).get("code") or "")

    @classmethod
    def _is_asset_stype(cls, stype) -> bool:
        code = cls._stype_code(stype).lower().replace("-", "_")
        leaf = code.rsplit("/", 1)[-1]
        return leaf in {"asset", "assets"}

    @classmethod
    def _group_title(cls, definition, stype) -> str:
        if (
                definition["source"] == "pipelines"
                and cls._is_asset_stype(stype)):
            return "ASSET PIPELINES"
        return definition["title"]

    @classmethod
    def _task_process_options(cls, stype, sobjects, task_records) -> list[dict]:
        records = {}
        for pipeline in cls._ordered_pipelines(stype, sobjects):
            names = cls._pipeline_process_names(pipeline)
            for name in names:
                configuration = process_task_configuration(pipeline, name)
                process_type = str(
                    configuration.get("type")
                    or configuration.get("node_type") or ""
                )
                if process_type in {
                    "action", "condition", "dependency", "progress",
                }:
                    continue
                key = str(name)
                records.setdefault(key, {
                    "key": key,
                    "title": str(configuration.get("label") or key)
                        .replace("_", " ").upper(),
                    "accent": str(configuration.get("color") or "#607d8b"),
                    "showAccentMarker": True,
                })
        for tasks in task_records.values():
            for task in tasks or ():
                key = str(cls._info(task).get("process") or "")
                if key:
                    records.setdefault(key, {
                        "key": key,
                        "title": key.replace("_", " ").upper(),
                        "accent": "#607d8b",
                        "showAccentMarker": True,
                    })
        return sorted(records.values(), key=lambda item: item["title"].lower())

    @classmethod
    def _task_status_options(cls, stype, sobjects, task_records) -> list[dict]:
        records = {}
        try:
            workflow = stype.get_workflow()
        except AttributeError:
            workflow = None
        for pipeline in cls._ordered_pipelines(stype, sobjects):
            names = cls._pipeline_process_names(pipeline)
            for name in names:
                configuration = process_task_configuration(pipeline, name)
                pipeline_code = configuration.get("task_pipeline")
                process_type = configuration.get("type")
                try:
                    task_pipeline = (
                        workflow.get_by_pipeline_code(
                            "sthpw/task", pipeline_code
                        ) if pipeline_code else
                        workflow.get_by_process_node_type(
                            "sthpw/task", process_type
                        )
                    )
                except (AttributeError, KeyError, TypeError):
                    task_pipeline = None
                for status, status_info in (
                        task_pipeline.pipeline.items() if task_pipeline else ()):
                    key = str(status)
                    records.setdefault(key, {
                        "key": key,
                        "title": key.replace("_", " ").upper(),
                        "accent": str(
                            (status_info or {}).get("color") or "#607d8b"
                        ),
                        "showAccentMarker": True,
                    })
        for tasks in task_records.values():
            for task in tasks or ():
                key = str(cls._info(task).get("status") or "")
                if key:
                    records.setdefault(key, {
                        "key": key,
                        "title": key.replace("_", " ").upper(),
                        "accent": "#607d8b",
                        "showAccentMarker": True,
                    })
        return sorted(records.values(), key=lambda item: item["title"].lower())

    @staticmethod
    def _inside_range(value: float, option: dict) -> bool:
        minimum = option.get("minimum")
        maximum = option.get("maximum")
        return (
            (minimum is None or value >= float(minimum))
            and (maximum is None or value <= float(maximum))
        )

    @staticmethod
    def _duration_seconds(value) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            pass
        parts = text.split(":")
        if not all(part.replace(".", "", 1).isdigit() for part in parts):
            return None
        values = [float(part) for part in parts]
        result = 0.0
        for part in values:
            result = result * 60 + part
        return result
