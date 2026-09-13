"""Object-shaped public boundaries over the native Handler object model."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import threading
from types import MappingProxyType
from typing import Callable

from .errors import ConcurrentEdit, DirtyObject, NotFound, NotReady
from .identity import SearchKey


@dataclass(frozen=True)
class SearchResult:
    """A bounded set of found sObjects, with explicit loading of more results."""

    items: tuple[SObject, ...]
    offset: int
    limit: int
    total: int | None
    has_more: bool
    _fetch: Callable[[int], SearchResult] = field(repr=False, compare=False)

    def next(self) -> SearchResult:
        if not self.has_more:
            return SearchResult(
                (),
                self.offset + len(self.items),
                self.limit,
                self.total,
                False,
                self._fetch,
            )
        return self._fetch(self.offset + len(self.items))


class Project:
    def __init__(self, api, native):
        self._api = api
        self._native = native
        self._info = deepcopy(native.get_info())

    def get_code(self) -> str:
        return self._info["code"]

    def get_info(self):
        return MappingProxyType(deepcopy(self._info))

    def stypes(self) -> list["SType"]:
        self._api._check()
        with self._api._catalog_lock:
            return [
                SType(self, native) for native in self._native.get_stypes().values()
            ]

    def stype(self, search_type: str) -> "SType":
        for stype in self.stypes():
            if stype.get_code() == search_type:
                return stype
        if search_type.startswith("sthpw/") and self.get_code() != "sthpw":
            native = self._api.project("sthpw").stype(search_type)._native
            return SType(self, native)
        raise NotFound(
            f"Search Type {search_type!r} is unavailable in {self.get_code()!r}"
        )

    def workflow(self):
        self.stypes()  # Native metadata owner hydrates workflow along with types.
        return self._native.get_workflow()

    def download_scripts(self):
        self._api._check()
        scripts = self._api._core.get_custom_scripts(project=self.get_code())
        return [deepcopy(value.get_info()) for value in scripts.values()]

    @property
    def definitions(self):
        from .definitions import DefinitionCatalog

        return DefinitionCatalog(self._api, self.get_code())


class SType:
    def __init__(self, project: Project, native):
        self._project = project
        self._api = project._api
        self._native = native
        self._info = deepcopy(native.get_info())

    def get_code(self) -> str:
        return self._info["code"]

    def get_project(self) -> Project:
        return self._project

    def get_info(self):
        return MappingProxyType(deepcopy(self._info))

    def get_columns_info(self):
        return MappingProxyType(deepcopy(self._info.get("column_info") or {}))

    def get(self, *, code: str | None = None, id: int | None = None) -> "SObject":
        if (code is None) == (id is None):
            raise ValueError("Specify exactly one code or id")
        identity = SearchKey(
            self.get_code(),
            self._project.get_code(),
            "code" if code is not None else "id",
            str(code if code is not None else id),
        )
        return self._api.sobject(str(identity))

    def query(
        self,
        filters=(),
        *,
        order_by=(),
        limit: int = 50,
        offset: int = 0,
        include_snapshots: bool = False,
    ) -> SearchResult:
        return self._api._query(
            self,
            filters,
            order_by,
            limit,
            offset,
            include_snapshots,
        )

    def new(
        self,
        values: dict | None = None,
        *,
        parent=None,
        relation: str | None = None,
        direction: str = "child",
    ) -> "SObject":
        if direction not in ("child", "parent"):
            raise ValueError("direction must be child or parent")
        if relation is not None and parent is None:
            raise ValueError("A relationship requires a parent object")
        parent_key = self._api._key(parent) if parent is not None else None
        if (
            parent_key is not None
            and parent_key.project_code != self._project.get_code()
        ):
            raise ValueError("Parent and new object must belong to the same project")
        obj = SObject(self._api, self, None, {})
        obj._creation = {
            "parent_key": str(parent_key) if parent_key else None,
            "instance_type": relation,
            "instance_path": direction if parent_key else None,
        }
        for column, value in (values or {}).items():
            obj.set_value(column, value)
        return obj

    def pipelines(self):
        self._api._check()
        return list((self._native.get_pipeline() or {}).values())

    def schema(self):
        self._api._check()
        return self._native.get_schema()

    @property
    def definitions(self):
        from .definitions import DefinitionCatalog

        return DefinitionCatalog(self._api, self._project.get_code(), self.get_code())


class SObject:
    def __init__(self, api, stype: SType, native, info: dict):
        self._api = api
        self._stype = stype
        self._native = native
        self._info = deepcopy(info)
        self._changes = {}
        self._creation = None
        self._lock = threading.RLock()
        self._busy = False

    def get_search_key(self) -> str:
        if not self._info.get("__search_key__"):
            raise NotReady("Commit the new object before using its search key")
        return self._info["__search_key__"]

    def get_code(self) -> str | None:
        return self._info.get("code")

    def get_project(self) -> Project:
        return self._stype.get_project()

    def get_stype(self) -> SType:
        return self._stype

    def get_info(self):
        with self._lock:
            return MappingProxyType(deepcopy({**self._info, **self._changes}))

    def get_value(self, column: str):
        return self.get_info().get(column)

    def set_value(self, column: str, value) -> None:
        if not isinstance(column, str) or not column or column.startswith("__"):
            raise ValueError("Expected a writable TACTIC column")
        with self._lock:
            if self._busy:
                raise ConcurrentEdit("This object's commit/refresh is in progress")
            if self._native is not None and column in {"code", "id"}:
                raise ValueError("An existing object's identity cannot be changed")
            if column in self._info and self._info[column] == value:
                self._changes.pop(column, None)
            else:
                self._changes[column] = deepcopy(value)

    def changes(self) -> dict:
        with self._lock:
            return deepcopy(self._changes)

    def discard_changes(self) -> None:
        with self._lock:
            if self._busy:
                raise ConcurrentEdit("This object's commit/refresh is in progress")
            self._changes.clear()

    def _begin_write(self, *, require_clean=False):
        self._api._check()
        with self._lock:
            if self._busy:
                raise ConcurrentEdit("This object's commit/refresh is in progress")
            if require_clean and self._changes:
                raise DirtyObject("Commit or discard changes before refreshing")
            self._busy = True
            return deepcopy(self._changes)

    def commit(self, *, triggers: bool = True) -> "SObject":
        if not isinstance(triggers, bool):
            raise TypeError("triggers must be a boolean")
        changes = self._begin_write()
        try:
            if self._native is not None and not changes:
                return self
            project = self.get_project()
            if self._native is None:
                result = self._api._core.insert_sobjects(
                    self._stype.get_code(),
                    project.get_code(),
                    changes,
                    triggers=triggers,
                    **(self._creation or {}),
                )
            else:
                # A private native editing object preserves legacy commit semantics
                # without publishing speculative state into the UI's native object.
                editor = self._api._core.SObject(deepcopy(self._info), project._native)
                for column, value in changes.items():
                    editor.set_value(column, value)
                result = editor.commit(triggers=triggers)
            if not isinstance(result, dict) or not result.get("__search_key__"):
                raise RuntimeError("TACTIC did not confirm the committed sObject")
            with self._lock:
                self._info = deepcopy(result)
                self._changes.clear()
                self._creation = None
                if self._native is None:
                    self._native = self._api._core.SObject(
                        deepcopy(result), project._native
                    )
            self._api._invalidate(project.get_code())
            return self
        finally:
            with self._lock:
                self._busy = False

    def refresh(self) -> "SObject":
        self._begin_write(require_clean=True)
        try:
            fresh = self._api.sobject(self.get_search_key())
            with self._lock:
                self._info = deepcopy(fresh._info)
                self._native = fresh._native
            return self
        finally:
            with self._lock:
                self._busy = False

    def dependencies(self):
        self._api._check()
        return self._api._core.get_all_dependency(
            [self.get_search_key()],
            project_code=self.get_project().get_code(),
        )

    def delete(self, *, dependencies=()):
        self.get_search_key()
        self._begin_write(require_clean=True)
        try:
            result = self._native.delete_sobject(list_dependencies=list(dependencies))
            self._api._invalidate(self.get_project().get_code())
            return result
        finally:
            with self._lock:
                self._busy = False

    def link(self, target, *, relation: str, path: str | None = None) -> None:
        self._api._check()
        if not isinstance(relation, str) or not relation:
            raise ValueError("A relationship Search Type is required")
        target_key = self._api._key(target)
        project_code = self.get_project().get_code()
        if target_key.project_code != project_code:
            raise ValueError("Linked objects must belong to the same project")
        self._api._core.edit_multiple_instance_sobjects(
            project_code,
            insert_search_keys=[str(target_key)],
            parent_key=self.get_search_key(),
            instance_type=relation,
            path=path,
        )
        self._api._invalidate(project_code)

    def related(self, *, search_type: str, direction: str = "child", filters=()):
        self._api._check()
        self.get_search_key()
        if direction not in ("child", "parent"):
            raise ValueError("direction must be child or parent")
        related_stype = self.get_project().stype(search_type)._native
        native = self._native.get_related_sobjects(
            child_stype=related_stype if direction == "child" else None,
            parent_stype=related_stype if direction == "parent" else None,
            path=direction,
            filters=list(filters),
        )
        if isinstance(native, tuple):
            native = native[0]
        return [
            self._api._wrap(value, self.get_project())
            for value in (native or {}).values()
        ]

    def tasks(self, process: str | None = None):
        self._api._check()
        self.get_search_key()
        native, _info = self._native.get_tasks_sobjects(process=process)
        return [self._api._wrap(value, self.get_project()) for value in native.values()]

    def notes(self, process: str | None = None, context: str | None = None):
        self._api._check()
        self.get_search_key()
        native, _info = self._native.get_notes_sobjects(process=process)
        return [
            self._api._wrap(value, self.get_project())
            for value in native.values()
            if context is None or value.get_value("context") == context
        ]

    def snapshots(self, *, process: str | None = None):
        self._api._check()
        self.get_search_key()
        server = self._api._core.server_start(project=self.get_project().get_code())
        search_type = server.build_search_type(
            self._stype.get_code(),
            project_code=self.get_project().get_code(),
        )
        records = self._native.query_snapshots(
            s_code=self.get_code(),
            s_id=self._info.get("id") if not self.get_code() else None,
            process=process,
            filters=[("search_type", search_type)],
        )
        return [
            Snapshot(self._api, self._api._core.Snapshot(deepcopy(value)))
            for value in records
        ]


class Snapshot:
    def __init__(self, api, native):
        self._api = api
        self._native = native
        self._info = deepcopy(native.get_info())

    def get_search_key(self):
        return self._info["__search_key__"]

    def get_code(self):
        return self._info["code"]

    def get_version(self):
        return self._info.get("version")

    def get_info(self):
        return MappingProxyType(deepcopy(self._info))

    def get_files_objects(self):
        self._api._check()
        # Keep the native File API: repository, identity and preview semantics
        # must not be reconstructed by the public façade.
        return self._native.get_files_objects()

    def get_previewable_files_objects(self):
        self._api._check()
        return self._native.get_previewable_files_objects()

    def is_latest(self):
        self._api._check()
        return self._native.is_latest()

    def is_versionless(self):
        self._api._check()
        return self._native.is_versionless()
