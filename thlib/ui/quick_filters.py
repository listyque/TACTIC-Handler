"""Metadata-driven facets for the Search workspace Quick Filters."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field

from .tel_filters import CURRENT_LOGIN_FILTER
from .workflow_data import process_task_configuration


@dataclass
class QuickFilterRuntime:
    """One owner for the active facet projection and its worker lifecycle."""

    cache: dict[str, dict] = field(default_factory=dict)
    workers: dict[str, object] = field(default_factory=dict)
    context_key: str = ""
    records: list[dict] = field(default_factory=list)
    loading: bool = False
    error: str = ""

    def invalidate(self) -> None:
        self.cache.clear()
        self.context_key = ""
        self.records.clear()
        self.loading = False
        self.error = ""
        for worker in tuple(self.workers.values()):
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        self.workers.clear()


class QuickFilterCatalog:
    """Build quick-filter groups from one Search Type and its records.

    The catalog deliberately owns no executable filtering. Selected values are
    materialized as Advanced Search records by the controller, so pagination,
    totals, saved tabs, and refreshes all use the same server query.
    """

    CURRENT_LOGIN_FILTER = CURRENT_LOGIN_FILTER
    MAX_DISCOVERED_OPTIONS = 64
    _TASK_KEYS = frozenset({"process", "status", "assigned"})
    _EXCLUDED_COLUMNS = frozenset({
        "id", "code", "name", "title", "description", "keywords",
        "tags", "tag", "search_code", "search_id", "search_type",
        "project_code", "login", "timestamp", "last_updated",
        "created", "updated", "relative_dir", "file_name", "file_path",
        "web_path", "lib_path", "sandbox_path", "repo", "repository",
        "metadata", "data", "xml", "config",
    })
    _EXCLUDED_SUFFIXES = (
        "_date", "_time", "_timestamp", "_path", "_url", "_size",
    )
    _NON_CATEGORICAL_TYPES = (
        "blob", "binary", "bytea", "json", "xml", "date", "time", "serial",
    )

    def __init__(self) -> None:
        self._configurations: dict[str, dict] = {}

    def set_configuration(self, scope_key, configuration) -> None:
        key = str(scope_key or "")
        if not configuration:
            self._configurations.pop(key, None)
            return
        validated = self.validate_configuration(configuration)
        if validated["groups"] or validated["defaultSelections"]:
            self._configurations[key] = validated
        else:
            self._configurations.pop(key, None)

    @staticmethod
    def validate_configuration(configuration) -> dict:
        """Validate the one unversioned server configuration contract."""
        if not isinstance(configuration, Mapping):
            raise TypeError("Quick-filter configuration must be a mapping")
        unexpected = set(configuration) - {"groups", "defaultSelections"}
        if unexpected:
            raise ValueError(
                "Unexpected quick-filter configuration fields: "
                + ", ".join(sorted(str(field) for field in unexpected))
            )
        groups = configuration.get("groups")
        defaults = configuration.get("defaultSelections")
        if not isinstance(groups, list):
            raise ValueError(
                "Quick-filter configuration groups must be a list"
            )
        if not isinstance(defaults, Mapping):
            raise ValueError(
                "Quick-filter defaultSelections must be a mapping"
            )
        if any(
                not str(key or "") or not isinstance(values, list)
                for key, values in defaults.items()):
            raise ValueError(
                "Quick-filter defaultSelections values must be lists"
            )
        return {
            "groups": deepcopy(groups),
            "defaultSelections": {
                str(key): list(values) for key, values in defaults.items()
            },
        }

    def configuration(self, scope_key) -> dict:
        return deepcopy(self._configurations.get(str(scope_key or ""), {}))

    def clear_configurations(self) -> None:
        """Drop project-scoped policy when the active project changes."""
        self._configurations.clear()

    def sanitize_selection(
        self, scope_key, selection, *, configuration=None,
    ) -> dict[str, set[str]]:
        """Apply the shared visibility policy to one local selection.

        The policy may hide a group or restrict its values, but it never
        invents a selection. This keeps the user's local state independent
        from the supervisor-owned starting state.
        """
        if configuration is None:
            configuration = self.configuration(scope_key)
        settings = {
            str(record.get("key") or ""): record
            for record in configuration.get("groups", ())
            if isinstance(record, Mapping) and record.get("key")
        }
        result: dict[str, set[str]] = {}
        if not isinstance(selection, Mapping):
            return result
        for raw_key, raw_values in selection.items():
            key = str(raw_key or "")
            if not key:
                continue
            group = settings.get(key)
            if group and group.get("enabled", True) is False:
                continue
            if isinstance(raw_values, str):
                values = {raw_values} if raw_values else set()
            else:
                try:
                    values = {
                        str(value) for value in raw_values
                        if str(value or "")
                    }
                except TypeError:
                    values = set()
            allowed = group.get("options") if group else None
            if isinstance(allowed, list):
                values.intersection_update(str(value) for value in allowed)
            if values:
                result[key] = values
        return result

    def default_selections(self, scope_key) -> dict[str, set[str]]:
        configuration = self.configuration(scope_key)
        return self.sanitize_selection(
            scope_key, configuration.get("defaultSelections") or {}
        )

    @staticmethod
    def _info(sobject) -> dict:
        if isinstance(sobject, Mapping):
            return dict(sobject)
        try:
            return dict(sobject.get_info() or {})
        except (AttributeError, TypeError, ValueError):
            return dict(getattr(sobject, "info", {}) or {})

    @staticmethod
    def _stype_code(stype) -> str:
        try:
            return str(stype.get_code() or "")
        except AttributeError:
            return str((getattr(stype, "info", {}) or {}).get("code") or "")

    @staticmethod
    def _columns_info(stype) -> dict:
        try:
            return dict(stype.get_columns_info() or {})
        except (AttributeError, TypeError, ValueError):
            return {}

    @staticmethod
    def _group_title(column: str, info: Mapping) -> str:
        return str(
            info.get("title")
            or info.get("label")
            or info.get("display")
            or column.replace("_", " ").title()
        )

    @classmethod
    def _metadata_options(cls, info: Mapping) -> list[dict]:
        source = info.get("values") or info.get("choices") or info.get("options")
        records: dict[str, dict] = {}
        if isinstance(source, Mapping):
            iterable = source.items()
        elif isinstance(source, (list, tuple, set)):
            iterable = enumerate(source)
        elif isinstance(source, str):
            separator = "|" if "|" in source else ","
            iterable = enumerate(source.split(separator))
        else:
            iterable = ()
        for source_key, source_value in iterable:
            if isinstance(source_value, Mapping):
                value = source_value.get("value")
                if value is None:
                    value = source_value.get("code", source_key)
                key = str(value if value is not None else "").strip()
                title = str(
                    source_value.get("title")
                    or source_value.get("label")
                    or source_value.get("name")
                    or key
                ).strip()
                accent = str(source_value.get("color") or "")
            elif isinstance(source, Mapping):
                key = str(source_key if source_key is not None else "").strip()
                title = str(source_value or key).strip()
                accent = ""
            else:
                key = str(source_value if source_value is not None else "").strip()
                title = key
                accent = ""
            if key:
                records[key] = {
                    "key": key,
                    "title": title or key,
                    "count": 0,
                    "accent": accent,
                    "showAccentMarker": bool(accent),
                }
        return list(records.values())

    @classmethod
    def facet_columns(cls, stype) -> list[dict]:
        """Return categorical schema columns eligible for facet discovery."""
        records = []
        for column, raw_info in cls._columns_info(stype).items():
            column = str(column or "")
            info = dict(raw_info or {})
            lowered = column.casefold()
            choices = cls._metadata_options(info)
            data_type = str(
                info.get("data_type") or info.get("type") or ""
            ).casefold()
            if (
                not column
                or column.startswith("__")
                or lowered in cls._EXCLUDED_COLUMNS
                or lowered.endswith(cls._EXCLUDED_SUFFIXES)
            ):
                continue
            if not choices and any(
                token in data_type for token in cls._NON_CATEGORICAL_TYPES
            ):
                continue
            records.append({
                "key": f"column:{column}",
                "column": column,
                "title": cls._group_title(column, info),
                "accent": str(info.get("color") or "#607d8b"),
                "metadataOptions": choices,
            })
        return records

    @classmethod
    def discover_facets(
        cls, stype, rows: Iterable, facet_columns: Iterable[Mapping] | None = None
    ) -> list[dict]:
        """Aggregate distinct values from actual Search Type records."""
        groups = (
            deepcopy(list(facet_columns))
            if facet_columns is not None else cls.facet_columns(stype)
        )
        by_column = {group["column"]: group for group in groups}
        values: dict[str, dict[str, dict]] = {}
        for group in groups:
            values[group["column"]] = {
                option["key"]: dict(option)
                for option in group.get("metadataOptions", ())
            }
        for row in rows or ():
            info = cls._info(row)
            for column in by_column:
                # Once a field exceeds the facet limit it cannot become a
                # quick filter. Do not retain its remaining distinct values.
                if len(values[column]) > cls.MAX_DISCOVERED_OPTIONS:
                    continue
                raw_value = info.get(column)
                if raw_value in (None, ""):
                    continue
                key = str(raw_value)
                record = values[column].setdefault(key, {
                    "key": key,
                    "title": key,
                    "count": 0,
                    "accent": "",
                    "showAccentMarker": False,
                })
                record["count"] = int(record.get("count") or 0) + 1
        result = []
        for group in groups:
            options = list(values[group["column"]].values())
            if (
                not options
                or len(options) > cls.MAX_DISCOVERED_OPTIONS
            ):
                continue
            options.sort(key=lambda option: str(option["title"]).casefold())
            result.append({
                "key": group["key"],
                "column": group["column"],
                "title": group["title"],
                "accent": group["accent"],
                "source": "column",
                "options": options,
            })
        return result

    @classmethod
    def _decorate_direct_groups(cls, groups, stype, sobjects) -> list[dict]:
        pipeline_options = {
            record["key"]: record
            for record in cls._pipeline_options(stype, sobjects)
        }
        result = []
        for source in groups or ():
            group = deepcopy(source)
            if group.get("column") == "pipeline_code":
                group["options"] = [
                    {**option, **pipeline_options.get(option["key"], {})}
                    for option in group.get("options", ())
                ]
            result.append(group)
        return result

    @classmethod
    def _task_groups(
        cls, stype, sobjects, task_records, current_login, selected
    ) -> list[dict]:
        processes = cls._task_process_options(stype, sobjects, task_records)
        statuses = cls._task_status_options(stype, sobjects, task_records)
        has_task_context = bool(processes or statuses or any(
            task_records.values()
        ) or cls._TASK_KEYS.intersection(selected))
        if not has_task_context:
            return []
        return [
            {
                "key": "process", "column": "", "title": "PROCESSES",
                "accent": "#607d8b", "source": "task",
                "options": processes,
            },
            {
                "key": "status", "column": "", "title": "STATUSES",
                "accent": "#607d8b", "source": "task",
                "options": statuses,
            },
            {
                "key": "assigned", "column": "", "title": "ASSIGNED TO",
                "accent": "#607d8b", "source": "task",
                "options": cls._task_assignee_options(
                    task_records, current_login
                ),
                "userPicker": True,
            },
        ]

    @staticmethod
    def configured_groups(
        groups: list[dict], configuration: dict, *, include_hidden: bool,
    ) -> list[dict]:
        settings = {
            str(record.get("key") or ""): record
            for record in configuration.get("groups", ())
            if isinstance(record, dict) and record.get("key")
        }
        order = [
            str(record.get("key") or "")
            for record in configuration.get("groups", ())
            if isinstance(record, dict)
        ]
        by_key = {str(group.get("key") or ""): group for group in groups}
        order.extend(key for key in by_key if key not in order)
        result = []
        for key in order:
            source = by_key.get(key)
            if not source:
                continue
            group = deepcopy(source)
            group_settings = settings.get(key, {})
            enabled = group_settings.get("enabled", group.get("enabled", True)) is not False
            if not enabled and not include_hidden:
                continue
            allowed = group_settings.get("options")
            if isinstance(allowed, list):
                allowed_keys = {str(value) for value in allowed}
                if include_hidden:
                    for option in group.get("options", ()):
                        option["enabled"] = option["key"] in allowed_keys
                else:
                    group["options"] = [
                        option for option in group.get("options", ())
                        if option["key"] in allowed_keys
                    ]
            elif include_hidden:
                for option in group.get("options", ()):
                    option.setdefault("enabled", True)
            group["enabled"] = enabled
            result.append(group)
        return result

    def base_groups(
        self, stype, sobjects, task_records=None, current_login="",
        selected=None, facet_records=None,
    ) -> list[dict]:
        direct = (
            deepcopy(facet_records)
            if facet_records is not None
            else self.discover_facets(stype, sobjects)
        )
        direct = self._decorate_direct_groups(direct, stype, sobjects)
        return direct + self._task_groups(
            stype,
            sobjects,
            task_records or {},
            current_login,
            selected or {},
        )

    def groups(
        self, scope_key, stype, sobjects, selected,
        task_records=None, current_login="", facet_records=None, local_groups=None,
    ) -> list[dict]:
        selected = self.sanitize_selection(scope_key, selected)
        selected = self.sanitize_selection(
            scope_key, selected, configuration={"groups": local_groups or []},
        )
        groups = self.configured_groups(
            self.base_groups(
                stype, sobjects, task_records, current_login,
                selected, facet_records,
            ),
            self.configuration(scope_key),
            include_hidden=False,
        )
        groups = self.configured_groups(
            groups, {"groups": local_groups or []}, include_hidden=False,
        )
        known_group_keys = {
            str(group.get("key") or "") for group in groups
        }
        for key in selected:
            if not key.startswith("column:") or key in known_group_keys:
                continue
            column = key.partition(":")[2]
            groups.append({
                "key": key,
                "column": column,
                "title": column.replace("_", " ").title(),
                "accent": "#607d8b",
                "source": "column",
                "options": [],
                "enabled": True,
            })
        records = []
        for group in groups:
            key = group["key"]
            selected_keys = set(selected.get(key, ()))
            options = [dict(option) for option in group.get("options", ())]
            known = {option["key"] for option in options}
            options.extend({
                "key": value,
                "title": value,
                "accent": "",
                "showAccentMarker": False,
                "count": 0,
            } for value in sorted(selected_keys - known))
            record = {
                **group,
                "allSelected": not selected_keys,
                "options": [
                    {
                        **option,
                        "selected": option["key"] in selected_keys,
                        "accent": option.get("accent") or group["accent"],
                        "showAccentMarker": bool(
                            option.get("showAccentMarker")
                        ),
                    }
                    for option in options
                ],
            }
            if group.get("userPicker"):
                record.update({
                    "myTasksKey": self.CURRENT_LOGIN_FILTER,
                    "myTasksSelected": (
                        self.CURRENT_LOGIN_FILTER in selected_keys
                    ),
                    "selectedUserCount": len(
                        selected_keys - {self.CURRENT_LOGIN_FILTER}
                    ),
                })
            records.append(record)
        return records

    def editor_groups(
        self, scope_key, stype, sobjects, task_records=None,
        facet_records=None, *, include_hidden=True, local_groups=None,
    ) -> list[dict]:
        groups = self.configured_groups(
            self.base_groups(
                stype, sobjects, task_records, selected={},
                facet_records=facet_records,
            ),
            self.configuration(scope_key),
            include_hidden=include_hidden,
        )
        if local_groups is not None:
            groups = self.configured_groups(
                groups, {"groups": local_groups}, include_hidden=True,
            )
        return [{
            "key": group["key"],
            "title": group["title"],
            "accent": group["accent"],
            "enabled": group.get("enabled", True),
            "options": [] if group.get("userPicker") else [
                {
                    "key": option["key"],
                    "title": option["title"],
                    "accent": option.get("accent") or group["accent"],
                    "showAccentMarker": bool(
                        option.get("showAccentMarker")
                    ),
                    "enabled": option.get("enabled", True),
                }
                for option in group.get("options", ())
            ],
        } for group in groups]

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
            name = (
                process.get("process") or process.get("name")
                if isinstance(process, dict) else ""
            )
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
            color = str(info.get("color") or "")
            records[code] = {
                "key": code,
                "title": str(
                    info.get("title") or info.get("name") or code
                ),
                "accent": color,
                "showAccentMarker": bool(color),
            }
        return sorted(records.values(), key=lambda item: item["title"].casefold())

    @classmethod
    def _task_process_options(cls, stype, sobjects, task_records) -> list[dict]:
        records = {}
        for pipeline in cls._ordered_pipelines(stype, sobjects):
            for name in cls._pipeline_process_names(pipeline):
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
                color = str(configuration.get("color") or "")
                records.setdefault(key, {
                    "key": key,
                    "title": str(configuration.get("label") or key),
                    "accent": color,
                    "showAccentMarker": bool(color),
                })
        for tasks in task_records.values():
            for task in tasks or ():
                key = str(cls._info(task).get("process") or "")
                if key:
                    records.setdefault(key, {
                        "key": key, "title": key, "accent": "",
                        "showAccentMarker": False,
                    })
        return sorted(records.values(), key=lambda item: item["title"].casefold())

    @classmethod
    def _task_status_options(cls, stype, sobjects, task_records) -> list[dict]:
        records = {}
        try:
            workflow = stype.get_workflow()
        except AttributeError:
            workflow = None
        for pipeline in cls._ordered_pipelines(stype, sobjects):
            for name in cls._pipeline_process_names(pipeline):
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
                    task_pipeline.pipeline.items() if task_pipeline else ()
                ):
                    key = str(status)
                    color = str((status_info or {}).get("color") or "")
                    records.setdefault(key, {
                        "key": key, "title": key,
                        "accent": color,
                        "showAccentMarker": bool(color),
                    })
        for tasks in task_records.values():
            for task in tasks or ():
                key = str(cls._info(task).get("status") or "")
                if key:
                    records.setdefault(key, {
                        "key": key, "title": key, "accent": "",
                        "showAccentMarker": False,
                    })
        return sorted(records.values(), key=lambda item: item["title"].casefold())

    @classmethod
    def _task_assignee_options(
        cls, task_records, current_login=""
    ) -> list[dict]:
        if not current_login:
            try:
                from thlib.environment import env_server
                current_login = str(env_server.get_user() or "")
            except (AttributeError, TypeError):
                current_login = ""
        records = {}
        try:
            from thlib.environment import env_inst
            logins = env_inst.get_all_logins() or {}
        except (AttributeError, TypeError):
            logins = {}
        for login_code, login in logins.items():
            key = str(login_code or "")
            if not key or key == current_login:
                continue
            try:
                title = str(login.get_display_name() or login.get_login() or key)
            except (AttributeError, TypeError):
                title = key
            records[key] = {"key": key, "title": title}
        for tasks in task_records.values():
            for task in tasks or ():
                key = str(cls._info(task).get("assigned") or "")
                if key and key != current_login:
                    records.setdefault(key, {"key": key, "title": key})
        options = []
        if current_login:
            options.append({
                "key": cls.CURRENT_LOGIN_FILTER,
                "title": "MY TASKS",
            })
        options.extend(sorted(
            records.values(), key=lambda item: item["title"].casefold()
        ))
        return options

    @classmethod
    def task_group_processes(
        cls, stype, sobjects, task_records=None
    ) -> list[dict]:
        return cls._task_process_options(stype, sobjects, task_records or {})

    @classmethod
    def task_group_statuses(
        cls, stype, sobjects, task_records, process
    ) -> list[dict]:
        records = {}
        try:
            workflow = stype.get_workflow()
        except AttributeError:
            workflow = None
        for pipeline in cls._ordered_pipelines(stype, sobjects):
            if str(process or "") not in cls._pipeline_process_names(pipeline):
                continue
            configuration = process_task_configuration(pipeline, process)
            pipeline_code = configuration.get("task_pipeline")
            process_type = configuration.get("type")
            try:
                task_pipeline = (
                    workflow.get_by_pipeline_code("sthpw/task", pipeline_code)
                    if pipeline_code else (
                        workflow.get_by_pipeline_code("sthpw/task", "task")
                        or workflow.get_by_process_node_type(
                            "sthpw/task", process_type
                        )
                    )
                )
            except (AttributeError, KeyError, TypeError):
                task_pipeline = None
            for status, status_info in (
                task_pipeline.pipeline.items() if task_pipeline else ()
            ):
                key = str(status)
                records.setdefault(key, {
                    "key": key,
                    "title": key,
                    "accent": str((status_info or {}).get("color") or ""),
                })
        for tasks in (task_records or {}).values():
            for task in tasks or ():
                info = cls._info(task)
                if str(info.get("process") or "") != str(process or ""):
                    continue
                key = str(info.get("status") or "")
                if key:
                    records.setdefault(key, {
                        "key": key, "title": key, "accent": "",
                    })
        return list(records.values())
