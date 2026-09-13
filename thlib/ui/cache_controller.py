"""QML-facing configuration and lifecycle owner for server-data caches."""

from __future__ import annotations

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot

from thlib import server_cache


class ServerCacheController(QObject):
    stateChanged = Signal()
    invalidated = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._busy = False
        self._message = ""
        self._worker = None
        self._pending_changes: list[dict] = []
        self._pending_retired: list[dict] = []
        self._pending_domains: list[tuple[list[str], str]] = []

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def message(self) -> str:
        return self._message

    def configuration_values(self) -> dict:
        return dict(server_cache.preferences())

    def apply_configuration(self, values: dict) -> None:
        previous = server_cache.preferences()
        updated = server_cache.update_preferences(dict(values or {}))
        self._message = self.tr("Cache settings saved")
        self.stateChanged.emit()
        changed = [
            domain for domain in server_cache.CACHE_DOMAINS
            if previous.get(domain) != updated.get(domain)
        ]
        if changed:
            self.invalidated.emit({
                "preferences": True,
                "domains": changed,
            })

    def _start_local(self, operation, finished) -> bool:
        if self._busy:
            return False
        from thlib.environment import env_inst

        if env_inst.local_pool.is_stopped:
            env_inst.local_pool.start()
        worker = env_inst.local_pool.add_task(operation)
        if worker is None:
            self._message = self.tr("Local cache worker is unavailable")
            self.stateChanged.emit()
            return False
        self._worker = worker
        self._busy = True
        self._message = ""
        self.stateChanged.emit()
        worker.result.connect(finished, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(
            self._operation_failed, Qt.ConnectionType.QueuedConnection
        )
        worker.start()
        return True

    @Slot(result=bool)
    def clear_all(self) -> bool:
        return self._start_local(
            server_cache.clear_all, self._clear_finished
        )

    def _clear_finished(self, _result) -> None:
        self._worker = None
        self._busy = False
        self._message = self.tr("Cached server data cleared")
        self.stateChanged.emit()
        self.invalidated.emit({"all": True})

    @Slot(object)
    def apply_server_batch(self, batch) -> None:
        batch = dict(batch or {})
        changes = list(batch.get("cacheChanges") or [])
        retired = list(batch.get("cacheRetired") or [])
        if not changes and not retired:
            return
        self._pending_changes.extend(changes)
        self._pending_retired.extend(retired)
        if self._busy:
            return
        self._start_pending_invalidations()

    def _start_pending_invalidations(self) -> None:
        if self._busy or (
            not self._pending_changes
            and not self._pending_retired
            and not self._pending_domains
        ):
            return
        changes = self._pending_changes
        retired = self._pending_retired
        direct = self._pending_domains
        self._pending_changes = []
        self._pending_retired = []
        self._pending_domains = []

        def operation():
            result = server_cache.apply_change_batch(changes, retired)
            for domains, project_code in direct:
                changed = server_cache.invalidate_domains(
                    domains, project_code
                )
                if changed:
                    result.setdefault(project_code, [])
                    result[project_code] = list(dict.fromkeys(
                        list(result[project_code]) + list(changed)
                    ))
            return result

        self._start_local(operation, self._invalidations_finished)

    def _invalidations_finished(self, result) -> None:
        self._worker = None
        self._busy = False
        self.stateChanged.emit()
        if result:
            self.invalidated.emit(dict(result))
        self._start_pending_invalidations()

    def invalidate(self, domains, project_code: str = "") -> None:
        domains = list(domains or [])
        project_code = str(project_code or "")
        if not domains:
            return
        self._pending_domains.append((domains, project_code))
        self._start_pending_invalidations()

    def _operation_failed(self, error) -> None:
        payload = error[0] if isinstance(error, tuple) and error else error
        if isinstance(payload, dict):
            payload = payload.get("exception") or payload.get("message")
        self._worker = None
        self._busy = False
        self._message = str(
            payload or self.tr("Unable to update local cache")
        )
        self.stateChanged.emit()
        self._start_pending_invalidations()

    @Slot()
    def shutdown(self) -> None:
        worker = self._worker
        self._worker = None
        self._busy = False
        if worker is not None:
            cancel = getattr(worker, "cancel", None)
            if callable(cancel):
                cancel()
