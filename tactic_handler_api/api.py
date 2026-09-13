"""Session-scoped public domain API over the native TACTIC implementation."""

from __future__ import annotations

from copy import deepcopy
import threading

from .errors import NotFound, NotReady
from .identity import SearchKey
from .objects import Project, SearchResult, SObject, Snapshot
from .operations import Executor, check_blocking_call


class HandlerAPI:
    def __init__(
        self,
        core,
        environment,
        *,
        files=None,
        ui=None,
        repositories=None,
        queue_gateway=None,
        max_workers: int = 4,
        max_pending: int = 64,
    ):
        self._core = core
        self._environment = environment
        self._file_module = files
        self._ui_backend = ui
        self._repositories = repositories or (lambda: [])
        self._queue_gateway = queue_gateway
        self._transfer_lock = threading.Lock()
        self._executor = Executor(max_workers, max_pending)
        self._catalog_lock = threading.RLock()
        self._closed = False

    def _check(self):
        if self._closed and not self._executor.running_here:
            raise RuntimeError("The API session is closed")
        check_blocking_call()

    def __enter__(self):
        return self

    def __exit__(self, *error):
        self.close()

    def close(self, *, wait: bool = True) -> None:
        _unbind_current(self)
        if wait:
            check_blocking_call()
        self._executor.close(wait=False)
        self._closed = True
        if wait:
            self._executor.close(wait=True)

    def submit(self, function, *args, **kwargs):
        if self._closed:
            raise RuntimeError("The API session is closed")
        return self._executor.submit(function, *args, **kwargs)

    def projects(self) -> list[Project]:
        self._check()
        with self._catalog_lock:
            native = self._environment.projects
            if native is None:
                native = self._core.get_all_projects_and_logins()
            return [Project(self, item) for item in native.values()]

    def project(self, project_code: str) -> Project:
        if not project_code:
            raise ValueError("An explicit project code is required")
        for project in self.projects():
            if project.get_code() == project_code:
                return project
        raise NotFound(f"Project {project_code!r} is unavailable")

    def _key(self, target) -> SearchKey:
        if isinstance(target, SObject):
            if target._api is not self:
                raise ValueError("The object belongs to a different API session")
            target = target.get_search_key()
        return SearchKey.parse(target)

    def sobject(self, search_key: str) -> SObject:
        self._check()
        identity = self._key(search_key)
        stype = self.project(identity.project_code).stype(identity.search_type)
        result = self._query(
            stype, [(identity.column, "=", identity.value)], (), 2, 0, False
        )
        if not result.items:
            raise NotFound(f"sObject {str(identity)!r} is unavailable")
        if len(result.items) != 1:
            raise ValueError("TACTIC returned an ambiguous object identity")
        return result.items[0]

    def _wrap(self, native, project: Project) -> SObject:
        info = native.get_info()
        identity = SearchKey.parse(info["__search_key__"])
        stype = project.stype(identity.search_type)
        return SObject(self, stype, native, info)

    def snapshot(self, search_key: str) -> Snapshot:
        self._check()
        identity = self._key(search_key)
        if identity.search_type != "sthpw/snapshot":
            raise ValueError("Expected a sthpw/snapshot search key")
        server = self._core.server_start(project=identity.project_code)
        records = server.query_snapshots(
            filters=[(identity.column, identity.value)],
            limit=2,
            include_files=True,
        )
        if len(records) != 1:
            raise NotFound(f"Snapshot {str(identity)!r} is unavailable or ambiguous")
        return Snapshot(self, self._core.Snapshot(deepcopy(records[0])))

    def _query(self, stype, filters, order_by, limit, offset, include_snapshots):
        self._check()
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= 1000
        ):
            raise ValueError("limit must be an integer between 1 and 1000")
        if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
            raise ValueError("offset must be a nonnegative integer")
        if isinstance(filters, (str, bytes)) or isinstance(order_by, (str, bytes)):
            raise TypeError("filters and order_by must be collections")
        filters, order_by = deepcopy(list(filters)), list(order_by)
        if any(not isinstance(value, str) or not value.strip() for value in order_by):
            raise ValueError("order_by contains an invalid column expression")
        identity = "code" if "code" in stype.get_columns_info() else "id"
        if not any(value.split()[0] == identity for value in order_by):
            order_by.append(identity)
        result = self._core.get_sobjects(
            stype.get_code(),
            project_code=stype.get_project().get_code(),
            filters=filters,
            order_bys=order_by,
            limit=limit,
            offset=offset,
            include_info=True,
            include_snapshots=include_snapshots,
            include_total_count=True,
        )
        if not isinstance(result, (list, tuple)) or len(result) != 2:
            raise RuntimeError("TACTIC returned an invalid query result")
        values, info = result
        items = tuple(
            SObject(self, stype, native, native.get_info())
            for native in values.values()
        )
        total = info.get("total_sobjects_query_count")
        total = int(total) if total is not None else None
        more = bool(items) and (
            offset + len(items) < total if total is not None else len(items) == limit
        )
        return SearchResult(
            items,
            offset,
            limit,
            total,
            more,
            lambda next_offset: self._query(
                stype,
                filters,
                order_by,
                limit,
                next_offset,
                include_snapshots,
            ),
        )

    def logins(self):
        self.projects()
        return list((self._environment.get_all_logins() or {}).values())

    def login(self, login_name: str):
        for login in self.logins():
            if login.get_login() == login_name:
                return login
        raise NotFound(f"Login {login_name!r} is unavailable")

    def _invalidate(self, project_code, *, definitions=False):
        if getattr(self._core, "__name__", "") == "thlib.tactic_classes":
            from thlib import server_cache

            server_cache.invalidate_domains(
                ("reference",)
                if definitions
                else ("search", "relations", "tasks", "notes", "snapshots"),
                project_code,
            )
            if definitions:
                self.project(project_code)._native.get_config_views().update_views()

    @property
    def ui(self):
        from .ui import UIAPI

        return UIAPI(self, self._ui_backend)

    @property
    def files(self):
        from .files import FilesAPI

        return FilesAPI(self)

    @property
    def repositories(self):
        from .files import RepositoriesAPI

        return RepositoriesAPI(self)

    def commit_queue(self, project_code=None):
        from .checkin import CommitQueue, HeadlessQueue

        with self._catalog_lock:
            if self._queue_gateway is None:
                self._queue_gateway = HeadlessQueue(self._repositories)
        return CommitQueue(self, self._queue_gateway, project_code)


_current_api = None


def get_api() -> HandlerAPI:
    if _current_api is None:
        raise NotReady("TACTIC Handler API is not running")
    return _current_api


def _bind_current(api: HandlerAPI) -> None:
    global _current_api
    _current_api = api


def _unbind_current(api: HandlerAPI) -> None:
    global _current_api
    if _current_api is api:
        _current_api = None


def local(*, ui=None, queue_gateway=None, max_workers=4, max_pending=64) -> HandlerAPI:
    """Borrow the configured standalone/headless Handler session; never start UI."""
    import thlib.tactic_classes as core
    import thlib.global_functions as files
    from thlib.environment import env_inst, env_tactic

    def repositories():
        env_tactic.get_base_dirs()
        return [
            deepcopy(value)
            for _name, value in env_tactic.get_all_base_dirs()
            if len(value.get("value") or []) > 4 and value["value"][4]
        ]

    return HandlerAPI(
        core,
        env_inst,
        files=files,
        ui=ui,
        repositories=repositories,
        queue_gateway=queue_gateway,
        max_workers=max_workers,
        max_pending=max_pending,
    )


def from_client(
    client, *, target="@tactic_handler", timeout=60.0, max_workers=4, max_pending=64
) -> HandlerAPI:
    """Borrow an existing ThinClient, without reconnecting or importing Maya."""
    from .remote import API

    return API(
        client, target, timeout, max_workers=max_workers, max_pending=max_pending
    )
