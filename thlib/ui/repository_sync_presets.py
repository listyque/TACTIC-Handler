"""Asynchronous Repository Sync preset discovery and caching."""

from __future__ import annotations

from PySide6.QtCore import QObject, Qt, Signal, Slot


class RepositoryPresetCache(QObject):
    """Keep live TACTIC preset queries away from QML-facing call paths."""

    changed = Signal()

    def __init__(self, log, parent=None) -> None:
        super().__init__(parent)
        self._log = log
        self._records: dict[tuple[str, str], list[dict]] = {}
        self._workers: dict[tuple[str, str], object] = {}
        self._shutting_down = False

    @staticmethod
    def _defaults() -> list[dict]:
        return [{
            "pretty_preset_name": "Default",
            "preset_name": "default",
        }]

    @staticmethod
    def _identity(source) -> tuple[str, str] | None:
        if not source:
            return None
        try:
            stype = source.get_stype()
        except AttributeError:
            stype = source
        try:
            project_code = str(stype.get_project().get_code() or "")
            stype_code = str(stype.get_code() or "")
        except (AttributeError, TypeError):
            return None
        if not project_code or not stype_code:
            return None
        return project_code, stype_code

    @classmethod
    def _query(cls, source) -> list[dict]:
        import thlib.global_functions as gf
        import thlib.tactic_classes as tc

        try:
            stype = source.get_stype()
        except AttributeError:
            stype = source
        project_code = str(stype.get_project().get_code() or "")
        records = tc.server_start(project=project_code).query(
            "sthpw/wdg_settings",
            [
                (
                    "key", "like",
                    f"search_type:{stype.get_code()}:preset_name:%",
                ),
                ("project_code", project_code),
            ],
            ["data"],
        )
        presets = []
        for record in records or []:
            preset = gf.from_json(record.get("data") or "")
            if isinstance(preset, dict):
                presets.append(preset)
        return presets or cls._defaults()

    @classmethod
    def _query_for_cache(cls, identity, source):
        return identity, cls._query(source)

    def records(self, source) -> list[dict]:
        identity = self._identity(source)
        if identity is None:
            return []
        records = self._records.get(identity)
        return [dict(record) for record in (
            records if records is not None else self._defaults()
        )]

    def populate(self, source, presets) -> None:
        identity = self._identity(source)
        if identity is None:
            return
        records = [dict(record) for record in presets or []]
        self._records[identity] = records or self._defaults()
        self.changed.emit()

    def request(self, source, force: bool = False) -> None:
        identity = self._identity(source)
        if (
            identity is None or self._shutting_down
            or identity in self._workers
            or (not force and identity in self._records)
        ):
            return
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(
            self._query_for_cache, identity, source,
        )
        self._workers[identity] = worker
        worker.result.connect(
            self._loaded, Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            self._failed, Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot(object)
    def _loaded(self, payload) -> None:
        identity, records = payload
        self._workers.pop(identity, None)
        self._records[identity] = [
            dict(record) for record in records or self._defaults()
        ]
        self.changed.emit()

    @Slot(object)
    def _failed(self, error) -> None:
        worker = (
            error[1]
            if isinstance(error, tuple) and len(error) > 1
            else None
        )
        for identity, candidate in tuple(self._workers.items()):
            if candidate is worker:
                self._workers.pop(identity, None)
                break
        payload = error[0] if isinstance(error, tuple) else error
        self._log(
            "WARNING", "Repository Sync presets could not be loaded",
            details=str(payload),
        )

    def shutdown(self) -> None:
        self._shutting_down = True
        for worker in tuple(self._workers.values()):
            try:
                worker.cancel()
            except RuntimeError:
                pass
        self._workers.clear()
        self._records.clear()


__all__ = ["RepositoryPresetCache"]
