"""Page layout drafts reuse the asynchronous administration document owner."""

import copy
import re
from uuid import uuid4
from PySide6.QtCore import QObject, Slot, QTimer, Qt
from .editor import AdminDocumentEditor
from .dashboard_api import dashboard_editor_request


class DashboardEditor(AdminDocumentEditor):
    def __init__(self, application, parent=None):
        super().__init__(application, dashboard_editor_request, parent)
        self._pending_save = None
        self._preview_owner = None
        self._preview_worker = None
        self._checked_document = None
        self._preview_serial = 0
        self._detail_key = ""
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._preview)

    def _catalog_loaded(self):
        self._revision = self._metadata.get("revision", self._revision)

    def _document_loaded(self):
        self._preview_serial += 1
        if self._metadata.get("checkedDocument") == self._document:
            self._checked_document = copy.deepcopy(self._document)
            self._update_preview()
        else:
            self._checked_document = None
            if self._document:
                self._timer.start()

    def _update_preview(self):
        if not isinstance(self._application, QObject):
            return
        if self._preview_owner is None:
            from .page_preview import PagePreview

            self._preview_owner = PagePreview(self._application, self)
            self._preview_owner.items.stateChanged.connect(self._samples_changed)
        self._preview_owner.update(self._metadata["compiled"], self._project)
        self._metadata["previewOwner"] = self._preview_owner
        self._metadata["application"] = self._application
        self._samples_changed()

    def _samples_changed(self):
        if self._closed:
            return
        model = self._metadata.get("compiled") or {}
        if not self._preview_owner or not model.get("layoutHasDetails"):
            self._detail_key = ""
            return
        rows = self._preview_owner.items.model.get("sampleItems") or []
        key = (rows[0].get("record") or {}).get("__search_key__", "") if rows else ""
        if key and (key != self._detail_key or not model.get("layoutDetail")):
            self._detail_key = key
            self._preview_serial += 1
            self._timer.start()

    @property
    def checked(self):
        return self._checked_document == self._document

    def _execute_request(self, arguments, project, original):
        from thlib import tactic_classes as tc

        if arguments["action"] == "save":
            pending = self._pending_save
            assert pending and pending["document"] == arguments["document"]
            arguments["operation_id"] = pending["operation_id"]
        return tc.execute_procedure_serverside(
            self._endpoint, arguments, project=project
        )

    @Slot("QVariantMap")
    def replace_document(self, document):
        if self.busy or self.writeUncertain or not self.canWrite:
            return
        self._document = copy.deepcopy(document)
        self._error = ""
        self._preview_serial += 1
        self._timer.start()
        self.stateChanged.emit()

    def _preview(self):
        if (
            self._closed
            or self.busy
            or self.writeUncertain
            or self._preview_worker is not None
            or not self._document
        ):
            return
        from thlib import tactic_classes as tc
        from thlib.environment import env_inst

        generation, serial = self._generation, self._preview_serial
        document, revision, project = (
            copy.deepcopy(self._document),
            self._revision,
            self._project,
        )
        detail_key = self._detail_key
        server = tc.server_start(project=project)
        worker = env_inst.server_pool.add_task(
            lambda: tc.execute_procedure_serverside(
                self._endpoint,
                dict(
                    action="preview",
                    project_code=project,
                    document=document,
                    expected_revision=revision,
                    detail_key=detail_key,
                ),
                project=project,
                server=server,
            )
        )
        if worker is None:
            self.fail(self.tr("Server worker pool is unavailable"))
            return
        self._preview_worker = worker

        def loaded(result):
            self._preview_worker = None
            if self._closed:
                return
            if generation != self._generation or serial != self._preview_serial:
                if self.dirty:
                    self._timer.start()
                return
            self._metadata["compiled"] = result["model"]
            self._metadata["checkedDocument"] = document
            self._checked_document = document
            self._update_preview()
            self.stateChanged.emit()

        def failed(error):
            self._preview_worker = None
            if (
                not self._closed
                and generation == self._generation
                and serial == self._preview_serial
            ):
                self.fail(str(error[0].get("exception") or error))
            elif not self._closed and self.dirty:
                self._timer.start()

        worker.result.connect(loaded, Qt.QueuedConnection)
        worker.error.connect(failed, Qt.QueuedConnection)
        worker.start()

    @Slot(str, str)
    def create(self, name, title):
        if self.busy or self.dirty or self.writeUncertain or not self.canWrite:
            return
        if (
            not re.fullmatch(r"[a-z][a-z0-9_]{0,47}", name)
            or not title.strip()
            or len(title) > 256
        ):
            self.fail(self.tr("Enter a page name and title"))
            return
        if any(row["identity"] == name for row in self._catalog):
            self.fail(self.tr("A view with this name already exists"))
            return
        # A fresh revision is loaded by the regular read operation before editing.
        self._preview_serial += 1
        self._revision = self._metadata.get("revision", self._revision)
        self._identity = name
        self._document = dict(name=name, title=title, blocks=[])
        self._original = {}
        self._checked_document = None
        self._timer.start()
        self.stateChanged.emit()

    @Slot()
    def save(self):
        if (
            self.canWrite
            and self.checked
            and self.dirty
            and not self.busy
            and not self.writeUncertain
        ):
            payload = dict(
                document=copy.deepcopy(self._document), expected_revision=self._revision
            )
            if not self._pending_save or any(
                self._pending_save.get(k) != v for k, v in payload.items()
            ):
                self._pending_save = dict(payload, operation_id=str(uuid4()))
            self._request("save", self._identity)

    @Slot(bool)
    def reload_document(self, force=False):
        if self.busy or self.dirty and not force:
            return
        self._presentation_dirty = False
        self._document = copy.deepcopy(self._original)
        self._request("load", self._identity) if self._identity else self._request(
            "list"
        )

    @Slot()
    def open_saved(self):
        if self.dirty or self.busy or not self._identity:
            return
        from urllib.parse import quote
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from thlib.environment import env_server
        from ..server_address import normalize_tactic_server_url

        QDesktopServices.openUrl(
            QUrl(
                normalize_tactic_server_url(env_server.get_server())
                + "/projects/"
                + quote(self._project, safe="")
                + "/dashboard/"
                + quote(self._identity, safe="")
            )
        )

    def shutdown(self):
        self._closed = True
        self._timer.stop()
        self._preview_serial += 1
        if self._preview_worker:
            self._preview_worker.cancel()
        if self._preview_owner:
            self._preview_owner.shutdown()
        super().shutdown()
