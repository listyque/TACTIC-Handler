from __future__ import annotations

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    Property,
    Qt,
    Signal,
    Slot,
)


class LinkObjectModel(QAbstractListModel):
    SearchKeyRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    SubtitleRole = Qt.UserRole + 3

    countChanged = Signal()
    _roles = {
        SearchKeyRole: b"searchKey",
        TitleRole: b"title",
        SubtitleRole: b"subtitle",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._records: list[dict] = []

    def roleNames(self) -> dict[int, bytes]:
        return self._roles

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._records)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._records):
            return None
        key = self._roles.get(role)
        return self._records[index.row()].get(key.decode()) if key else None

    def replace(self, records) -> None:
        self.beginResetModel()
        self._records = [dict(record) for record in records]
        self.endResetModel()
        self.countChanged.emit()

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._records)


class SObjectLinkController(QObject):
    stateChanged = Signal()
    saved = Signal()

    def __init__(self, context, notify=None, parent=None) -> None:
        super().__init__(parent)
        self._context = context
        self._notify = notify or (lambda _message: None)
        self._context_data = {}
        self._available: dict[str, object] = {}
        self._linked: dict[str, object] = {}
        self._initial_keys: set[str] = set()
        self._request_id = 0
        self._worker = None
        self._busy = False
        self._dirty = False
        self._error = ""
        self._query = ""
        self.available_model = LinkObjectModel(self)
        self.linked_model = LinkObjectModel(self)

    @Slot()
    def begin_session(self) -> None:
        context = dict(self._context() or {})
        if (
            context.get("stype") is None
            or context.get("parent_sobject") is None
            or not context.get("project_code")
        ):
            self._set_error("Select a relation first")
            self.available_model.replace([])
            self.linked_model.replace([])
            return
        self._context_data = context
        self._query = ""
        self._dirty = False
        self._load()

    @Slot(str)
    def search(self, query: str) -> None:
        if self._busy:
            return
        self._query = str(query or "").strip()
        self._load()

    def _load(self) -> None:
        self._request_id += 1
        request_id = self._request_id
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        from thlib.environment import env_inst
        worker = env_inst.server_pool.add_task(
            self._load_objects,
            self._context_data,
            self._query,
        )
        self._worker = worker
        worker.result.connect(
            lambda result: self._loaded(request_id, result)
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error)
        )
        worker.start()

    @staticmethod
    def _load_objects(context: dict, query: str):
        import thlib.tactic_classes as tc

        stype = context["stype"]
        parent = context["parent_sobject"]
        filters = [("name", "EQI", query)] if query else []
        result = tc.get_sobjects(
            stype.get_code(),
            filters=filters,
            project_code=context["project_code"],
            limit=100,
            include_snapshots=False,
            include_info=False,
        )
        if isinstance(result, tuple):
            result = result[0]
        if isinstance(result, dict):
            available = list(result.values())
        else:
            available = list(result or [])
        related = parent.get_related_sobjects(
            child_stype=stype,
            parent_stype=parent.get_stype(),
            path="child",
            get_all_snapshots=False,
        )
        if isinstance(related, tuple):
            related = related[0]
        if isinstance(related, dict):
            related = list(related.values())
        return available, list(related or [])

    def _loaded(self, request_id: int, result) -> None:
        if request_id != self._request_id:
            return
        available, linked = result
        if not self._dirty:
            self._linked = {
                str(sobject.get_search_key()): sobject for sobject in linked
            }
            self._initial_keys = set(self._linked)
        linked_keys = set(self._linked)
        self._available = {
            str(sobject.get_search_key()): sobject
            for sobject in available
            if str(sobject.get_search_key()) not in linked_keys
        }
        self._sync_models()
        self._busy = False
        self._worker = None
        self.stateChanged.emit()

    @staticmethod
    def _record(sobject) -> dict:
        info = sobject.get_info() or {}
        return {
            "searchKey": str(sobject.get_search_key() or ""),
            "title": str(
                sobject.get_title()
                or info.get("name")
                or info.get("code")
                or ""
            ),
            "subtitle": str(
                info.get("description")
                or info.get("status")
                or info.get("code")
                or ""
            ),
        }

    def _sync_models(self) -> None:
        self.available_model.replace([
            self._record(sobject) for sobject in self._available.values()
        ])
        self.linked_model.replace([
            self._record(sobject) for sobject in self._linked.values()
        ])

    @Slot(str)
    def add(self, search_key: str) -> None:
        if self._busy:
            return
        sobject = self._available.pop(str(search_key), None)
        if sobject is None:
            return
        self._linked[str(search_key)] = sobject
        self._dirty = set(self._linked) != self._initial_keys
        self._sync_models()
        self.stateChanged.emit()

    @Slot(str)
    def remove(self, search_key: str) -> None:
        if self._busy:
            return
        sobject = self._linked.pop(str(search_key), None)
        if sobject is None:
            return
        self._available[str(search_key)] = sobject
        self._dirty = set(self._linked) != self._initial_keys
        self._sync_models()
        self.stateChanged.emit()

    @Slot()
    def save(self) -> None:
        if self._busy or not self._dirty:
            return
        context = self._context_data
        relation = dict(context.get("relation") or {})
        instance_type = relation.get("instance_type")
        if not instance_type:
            self._set_error("This relation has no instance type")
            return
        current_keys = set(self._linked)
        insert_keys = sorted(current_keys - self._initial_keys)
        exclude_keys = sorted(self._initial_keys - current_keys)
        stype = context["stype"]
        path = None
        parent_relation = stype.get_schema().get_parent_instance(
            instance_type,
            stype.get_code(),
        )
        if parent_relation:
            path = parent_relation.get("path")

        import thlib.tactic_classes as tc
        from thlib.environment import env_inst
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        request_id = self._request_id
        worker = env_inst.server_pool.add_task(
            tc.edit_multiple_instance_sobjects,
            context["project_code"],
            insert_search_keys=insert_keys,
            exclude_search_keys=exclude_keys,
            parent_key=context["parent_sobject"].get_search_key(),
            instance_type=instance_type,
            path=path,
        )
        self._worker = worker
        worker.result.connect(
            lambda _result: self._save_finished(request_id)
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error)
        )
        worker.start()

    def _save_finished(self, request_id: int) -> None:
        if request_id != self._request_id:
            return
        self._busy = False
        self._dirty = False
        self._initial_keys = set(self._linked)
        self._worker = None
        refresh = self._context_data.get("refresh")
        if callable(refresh):
            refresh()
        self._notify("Links updated")
        self.stateChanged.emit()
        self.saved.emit()

    def _failed(self, request_id: int, error) -> None:
        if request_id != self._request_id:
            return
        payload = error[0] if isinstance(error, (tuple, list)) else error
        message = (
            payload.get("exception") or payload.get("message") or str(payload)
            if isinstance(payload, dict) else str(payload)
        )
        self._set_error(message or "The server request failed")
        self._notify(self._error)

    def _set_error(self, message: str) -> None:
        self._busy = False
        self._worker = None
        self._error = str(message)
        self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return self._dirty

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error
