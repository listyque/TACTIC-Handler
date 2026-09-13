"""Project Knowledge Base state, search, editing, and attachment workflow."""

from __future__ import annotations

from copy import deepcopy
from html import unescape
from pathlib import Path
import re
import uuid
from urllib.parse import parse_qsl, urlparse

from PySide6.QtCore import QObject, Property, QTimer, QUrl, Qt, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication

from .knowledge_api import knowledge_request
from .activity import activity_timestamp_labels
from .rich_text import (
    fit_rich_html_images,
    headings_from_html,
    rich_text_blocks,
)
from .rich_text_document import (
    plain_text_from_markdown,
    rich_html_from_markdown,
)
from .workspace_models.records import RecordListModel


_NAVIGATION_ROLES = (
    "identity", "title", "description", "excerpt", "kind", "parentCode",
    "sortOrder", "updatedBy", "timestamp", "searchKey", "depth",
    "hasChildren", "expanded", "draft", "localDraft",
)

_ATTACHMENT_ROLES = (
    "token", "snapshotKey", "title", "extension", "sizeText",
    "previewUrl", "webUrl", "isImage",
)

_HISTORY_ROLES = (
    "revisionId", "timestampPretty", "timestampFull", "actor",
    "actorDisplay", "summary", "current", "selected",
)

_EDITOR_IMAGE_TAG = re.compile(
    r'(<img\b[^>]*\bsrc=")([^"]+)(")', re.IGNORECASE
)
_EDITOR_IMAGE_PLACEHOLDER = QUrl.fromLocalFile(str(
    Path(__file__).with_name("assets") / "knowledge_image_placeholder.svg"
)).toString()

class KnowledgeController(QObject):
    stateChanged = Signal()
    editorDocumentChanged = Signal()
    schemaInitialized = Signal()
    linkIndexChanged = Signal(object)
    visibilityChanged = Signal(bool)

    def __init__(
        self,
        application,
        attachments,
        rich_text_document,
        skey_previews=None,
        clock=None,
        user_model=None,
        draft_state=None,
        config_queue=None,
        parent=None,
    ) -> None:
        super().__init__(parent or application)
        self._application = application
        self.attachments = attachments
        self.rich_text_document = rich_text_document
        self._skey_previews = skey_previews
        self._clock = clock
        self._user_model = user_model
        self.navigation = RecordListModel(_NAVIGATION_ROLES)
        self.uploaded_attachments = RecordListModel(_ATTACHMENT_ROLES)
        self.history = RecordListModel(_HISTORY_ROLES)
        self._catalog: list[dict] = []
        stored_projects = (
            dict(draft_state or {}).get("projects", {})
            if isinstance(draft_state, dict) else {}
        )
        self._local_drafts_by_project = {
            str(project_code): {
                str(identity): deepcopy(state)
                for identity, state in drafts.items()
                if identity and isinstance(state, dict)
            }
            for project_code, drafts in (
                stored_projects.items()
                if isinstance(stored_projects, dict) else ()
            )
            if project_code and isinstance(drafts, dict)
        }
        self._local_drafts: dict[str, dict] = {}
        self._config_queue = config_queue
        self._organization_original: list[dict] | None = None
        self._loaded = False
        self._document: dict = {}
        self._article_metadata: dict = {}
        self._history_records: list[dict] = []
        self._history_identity = ""
        self._history_preview: dict = {}
        self._document_complete = False
        self._original: dict = {}
        self._references: list[dict] = []
        self._linked_objects: list[dict] = []
        self._table_of_contents: list[dict] = []
        self._reference_keys: set[str] = set()
        self._linked_object_keys: set[str] = set()
        self._link_index: dict[str, list[str]] = {}
        self._collapsed: set[str] = set()
        self._project_code = ""
        self._identity = ""
        self._navigation_identity = ""
        self._open_article_pending = False
        self._search_key = ""
        self._revision = ""
        self._query = ""
        self._busy = False
        self._error = ""
        self._initialized = False
        self._can_edit = False
        self._can_initialize = False
        self._editing = False
        self._creating = False
        self._visible = False
        self._worker = None
        self._worker_action = ""
        self._generation = 0
        self._pending_identity = ""
        self._pending_search = False
        self._pending_delete_identity = ""
        self._attachment_snapshot_keys: dict[str, str] = {}
        self._image_source_candidates: dict[str, list[str]] = {}
        self._closed = False
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(220)
        self._search_timer.timeout.connect(self._search_now)
        application.project_changed.connect(self._project_changed)
        selection_changed = getattr(
            application, "selected_node_changed", None
        )
        if selection_changed is not None:
            selection_changed.connect(self._selected_objects_changed)
        attachments.uploaded.connect(self._attachments_uploaded)
        attachments.failed.connect(self._attachment_failed)
        attachments.stateChanged.connect(self.stateChanged)
        if skey_previews is not None:
            skey_previews.previewReady.connect(self._reference_ready)
            skey_previews.previewsReady.connect(self._references_ready)
        if clock is not None:
            clock.changed.connect(self.stateChanged)
        if user_model is not None:
            user_model.contentReplaced.connect(self.stateChanged)
        self._delete_controller = getattr(
            application, "sobject_delete", None
        )
        if self._delete_controller is not None:
            self._delete_controller.deletionFinished.connect(
                self._sobject_deletion_finished
            )

    @Property(QObject, constant=True)
    def navigationModel(self):
        return self.navigation

    @Property(QObject, constant=True)
    def uploadedAttachmentModel(self):
        return self.uploaded_attachments

    @Property(QObject, constant=True)
    def historyModel(self):
        return self.history

    @Property(bool, notify=stateChanged)
    def busy(self) -> bool:
        return self._busy or bool(self.attachments.busy)

    @Property(str, notify=stateChanged)
    def error(self) -> str:
        return self._error or str(self.attachments.error or "")

    @Slot()
    def dismiss_error(self) -> None:
        changed = bool(self._error or self.attachments.error)
        self._error = ""
        dismiss_attachment_error = getattr(
            self.attachments, "dismiss_error", None
        )
        if callable(dismiss_attachment_error):
            dismiss_attachment_error()
        if changed:
            self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def initialized(self) -> bool:
        return self._initialized

    @Property(bool, notify=stateChanged)
    def canInitialize(self) -> bool:
        return self._can_initialize

    @Property(bool, notify=stateChanged)
    def canEdit(self) -> bool:
        return self._can_edit

    @Property(bool, notify=stateChanged)
    def editing(self) -> bool:
        return self._editing

    @Property(bool, notify=stateChanged)
    def creating(self) -> bool:
        return self._creating

    @Property(bool, notify=stateChanged)
    def draft(self) -> bool:
        return bool(self._document.get("draft"))

    @Property(bool, notify=stateChanged)
    def localDraft(self) -> bool:
        return self._identity in self._local_drafts

    @Property(bool, notify=stateChanged)
    def dirty(self) -> bool:
        return self._editing and self._document != self._original

    @Property(bool, notify=stateChanged)
    def organizationDirty(self) -> bool:
        return self._organization_original is not None

    @Property(str, notify=stateChanged)
    def query(self) -> str:
        return self._query

    @Property(str, notify=stateChanged)
    def identity(self) -> str:
        return self._identity

    @Property(str, notify=stateChanged)
    def navigationIdentity(self) -> str:
        """Identity receiving immediate navigation selection feedback."""
        return self._navigation_identity

    @Property(bool, notify=stateChanged)
    def openArticlePending(self) -> bool:
        """Whether an external link still needs to reveal the article page."""
        return self._open_article_pending

    @Slot()
    def acknowledge_article_open(self) -> None:
        if not self._open_article_pending:
            return
        self._open_article_pending = False
        self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def searchKey(self) -> str:
        return self._search_key

    @Property("QVariantMap", notify=stateChanged)
    def document(self) -> dict:
        return deepcopy(self._document)

    @Property(str, notify=editorDocumentChanged)
    def editorMarkdown(self) -> str:
        """Canonical Markdown loaded when the active article is replaced."""
        return str(self._document.get("contentMarkdown") or "")

    @staticmethod
    def _editor_document(markdown: str) -> tuple[str, list[str]]:
        storage_sources = []

        def replace_image(match: re.Match) -> str:
            storage_sources.append(unescape(match.group(2)))
            return (
                match.group(1) + _EDITOR_IMAGE_PLACEHOLDER + match.group(3)
            )

        rich_html = rich_html_from_markdown(markdown) or "<p></p>"
        return _EDITOR_IMAGE_TAG.sub(replace_image, rich_html), storage_sources

    @Property(str, notify=editorDocumentChanged)
    def editorHtml(self) -> str:
        """HTML loaded by the visual editor for the active Markdown article."""
        return self._editor_document(self.editorMarkdown)[0]

    @Property("QVariantList", notify=editorDocumentChanged)
    def editorImageStorageSources(self) -> list[str]:
        return self._editor_document(self.editorMarkdown)[1]

    @Property(str, notify=stateChanged)
    def displayHtml(self) -> str:
        return rich_html_from_markdown(
            str(self._document.get("contentMarkdown") or "")
        )

    @Slot(float, result=str)
    def display_html_for_width(self, maximum_width: float) -> str:
        return fit_rich_html_images(
            rich_html_from_markdown(
                str(self._document.get("contentMarkdown") or "")
            ),
            maximum_width,
            linkify=True,
        )

    @Property(int, notify=stateChanged)
    def readingMinutes(self) -> int:
        return self._reading_minutes(self._document)

    @staticmethod
    def _reading_minutes(document: dict) -> int:
        if document.get("kind") != "article":
            return 0
        words = re.findall(
            r"[^\W_]+(?:['’\-][^\W_]+)*",
            str(document.get("contentText") or ""),
            flags=re.UNICODE,
        )
        return max(1, (len(words) + 199) // 200) if words else 0

    @staticmethod
    def _normalized_document(document) -> dict:
        return deepcopy(document or {})

    @Property("QVariantMap", notify=stateChanged)
    def articleMetadata(self) -> dict:
        return self._present_article_metadata(self._article_metadata)

    def _present_article_metadata(self, source) -> dict:
        metadata = dict(source or {})
        created_pretty, created_full = activity_timestamp_labels(
            metadata.get("createdAt"), self._clock,
        )
        updated_pretty, updated_full = activity_timestamp_labels(
            metadata.get("updatedAt"), self._clock,
        )
        metadata.update({
            "authorDisplay": self._user_display_name(
                metadata.get("author")
            ),
            "createdLabel": created_full or created_pretty,
            "updatedLabel": updated_full or updated_pretty,
        })
        return metadata

    @Property(bool, notify=stateChanged)
    def historyLoaded(self) -> bool:
        return bool(
            self._identity
            and self._history_identity == self._identity
        )

    @Property(bool, notify=stateChanged)
    def historyLoading(self) -> bool:
        return self._worker_action in {"history", "history_revision"}

    @Property(int, notify=stateChanged)
    def historyCount(self) -> int:
        return len(self._history_records)

    @Property(bool, notify=stateChanged)
    def historyPreviewActive(self) -> bool:
        return bool(self._history_preview)

    @Property("QVariantMap", notify=stateChanged)
    def historyPreview(self) -> dict:
        preview = deepcopy(self._history_preview)
        if preview:
            preview["actorDisplay"] = self._user_display_name(
                preview.get("actor")
            )
            pretty, full = activity_timestamp_labels(
                preview.get("timestamp"), self._clock,
            )
            preview["timestampPretty"] = pretty
            preview["timestampFull"] = full or pretty
        return preview

    @Property("QVariantMap", notify=stateChanged)
    def viewerDocument(self) -> dict:
        if self._history_preview:
            return deepcopy(self._history_preview.get("document") or {})
        return deepcopy(self._document)

    @Property("QVariantMap", notify=stateChanged)
    def viewerArticleMetadata(self) -> dict:
        if self._history_preview:
            return self._present_article_metadata(
                self._history_preview.get("articleMetadata") or {}
            )
        return self.articleMetadata

    @Property("QVariantList", notify=stateChanged)
    def viewerTableOfContents(self) -> list[dict]:
        if self._history_preview:
            document = self._history_preview.get("document") or {}
            if document.get("kind") != "article":
                return []
            return headings_from_html(rich_html_from_markdown(
                document.get("contentMarkdown") or ""
            ))
        return self.tableOfContents

    @Property(int, notify=stateChanged)
    def viewerReadingMinutes(self) -> int:
        return self._reading_minutes(self.viewerDocument)

    @Slot(float, result=str)
    def viewer_html_for_width(self, maximum_width: float) -> str:
        document = self.viewerDocument
        return fit_rich_html_images(
            rich_html_from_markdown(
                str(document.get("contentMarkdown") or "")
            ),
            maximum_width,
            linkify=True,
        )

    @Slot(float, result="QVariantList")
    def viewer_blocks_for_width(self, maximum_width: float) -> list[dict]:
        return self._viewer_blocks(maximum_width)

    @Slot(result="QVariantList")
    def viewer_blocks(self) -> list[dict]:
        """Return intrinsic article blocks for retained responsive delegates."""
        return self._viewer_blocks(None)

    def _viewer_blocks(
        self,
        maximum_width: float | None,
    ) -> list[dict]:
        document = self.viewerDocument
        blocks = rich_text_blocks(
            rich_html_from_markdown(
                str(document.get("contentMarkdown") or "")
            ),
            maximum_width,
        )
        for block in blocks:
            if block.get("kind") != "image":
                continue
            source = str(block.get("source") or "")
            candidates = self._image_source_candidates.get(source, [])
            block["sources"] = list(dict.fromkeys(
                [*candidates, source]
            ))
        return blocks

    def _user_display_name(self, login) -> str:
        login = str(login or "").strip()
        if not login or self._user_model is None:
            return login
        for row in range(self._user_model.rowCount()):
            record = self._user_model.get(row)
            if str(record.get("login") or "") == login:
                return str(record.get("displayName") or login)
        return login

    def _clear_history_state(self) -> None:
        self._history_records = []
        self._history_identity = ""
        self._history_preview = {}
        self.history.replace([])

    def _history_summary(self, record: dict) -> str:
        if str(record.get("action") or "") == "create":
            return self.tr("Article created")
        labels = {
            "content": self.tr("Content"),
            "description": self.tr("Summary"),
            "kind": self.tr("Page type"),
            "linked_skeys": self.tr("Linked objects"),
            "name": self.tr("Title"),
            "parent_code": self.tr("Parent section"),
            "sort_order": self.tr("Page order"),
            "s_status": self.tr("Publication status"),
        }
        changed = [
            labels.get(str(field), str(field).replace("_", " "))
            for field in record.get("changedFields") or []
        ]
        changed = list(dict.fromkeys(filter(None, changed)))
        if not changed:
            return self.tr("Saved revision")
        return self.tr("Changed: {fields}").format(
            fields=", ".join(changed)
        )

    def _refresh_history_model(self) -> None:
        selected_revision = str(
            self._history_preview.get("revisionId") or ""
        )
        records = []
        for raw_record in self._history_records:
            record = dict(raw_record)
            pretty, full = activity_timestamp_labels(
                record.get("timestamp"), self._clock,
            )
            record.update({
                "timestampPretty": pretty,
                "timestampFull": full or pretty,
                "actorDisplay": self._user_display_name(
                    record.get("actor")
                ),
                "summary": self._history_summary(record),
                "selected": bool(
                    selected_revision
                    and selected_revision == str(
                        record.get("revisionId") or ""
                    )
                ),
            })
            records.append(record)
        self.history.replace(records)

    @Slot(result=bool)
    def load_history(self) -> bool:
        if (
            not self._identity
            or self._local_identity(self._identity)
            or self._document.get("kind") != "article"
        ):
            return False
        if self.historyLoaded:
            return True
        return self._run(
            "history",
            identity=self._identity,
            handler=self._history_ready,
        )

    def _history_ready(self, result: dict) -> None:
        if result.get("entryMissing"):
            self._clear_history_state()
            self._error = self.tr(
                "The Knowledge Base entry no longer exists"
            )
            self.stateChanged.emit()
            return
        if str(result.get("identity") or "") != self._identity:
            return
        self._history_records = [
            dict(record) for record in result.get("history") or []
        ]
        self._history_identity = self._identity
        self._history_preview = {}
        self._refresh_history_model()
        self.stateChanged.emit()

    @Slot(str, result=bool)
    def preview_history_revision(self, revision_id: str) -> bool:
        revision_id = str(revision_id or "")
        record = next((
            value for value in self._history_records
            if str(value.get("revisionId") or "") == revision_id
        ), None)
        if record is None:
            return False
        if record.get("current"):
            self.clear_history_preview()
            return True
        if self.historyLoading:
            return False
        return self._run(
            "history_revision",
            identity=self._identity,
            history_revision=revision_id,
            handler=self._history_revision_ready,
        )

    def _history_revision_ready(self, result: dict) -> None:
        if result.get("entryMissing"):
            self._clear_history_state()
            self._error = self.tr(
                "The Knowledge Base entry no longer exists"
            )
            self.stateChanged.emit()
            return
        if str(result.get("identity") or "") != self._identity:
            return
        preview = dict(result.get("historyRevision") or {})
        if not preview:
            self._error = self.tr("This article revision is unavailable")
            self.stateChanged.emit()
            return
        self._history_preview = deepcopy(preview)
        self._history_preview["document"] = self._normalized_document(
            self._history_preview.get("document") or {}
        )
        self._refresh_history_model()
        self.stateChanged.emit()

    @Slot()
    def clear_history_preview(self) -> None:
        if not self._history_preview:
            return
        self._history_preview = {}
        self._refresh_history_model()
        self.stateChanged.emit()

    @Property("QVariantList", notify=stateChanged)
    def references(self) -> list[dict]:
        return [dict(record) for record in self._references]

    @Property("QVariantList", notify=stateChanged)
    def linkedObjects(self) -> list[dict]:
        return [dict(record) for record in self._linked_objects]

    @Property("QVariantList", notify=stateChanged)
    def selectedLinkCandidates(self) -> list[dict]:
        records = getattr(
            self._application, "selected_result_records", []
        )
        candidates = []
        seen = set()
        for record in records or []:
            if str(record.get("type") or "") != "sobject":
                continue
            search_key = self._normalize_search_key(
                record.get("searchKey")
            )
            if not search_key or search_key in seen:
                continue
            seen.add(search_key)
            candidates.append({
                "searchKey": search_key,
                "title": str(record.get("title") or ""),
                "description": str(record.get("description") or ""),
            })
        return candidates

    @Property("QVariantMap", notify=stateChanged)
    def parentSection(self) -> dict:
        parent_identity = str(self._document.get("parentCode") or "")
        parent = self._catalog_record(parent_identity)
        return {
            "identity": parent_identity if parent else "",
            "title": str(parent.get("title") or "") if parent else "",
            "description": str(parent.get("description") or "") if parent else "",
        }

    @Property("QVariantList", notify=stateChanged)
    def linkableSelectedObjects(self) -> list[dict]:
        linked = {
            self._normalize_search_key(value)
            for value in self._document.get("linkedSearchKeys") or []
        }
        return [
            dict(record) for record in self.selectedLinkCandidates
            if record["searchKey"] not in linked
        ]

    @Property("QVariantList", notify=stateChanged)
    def tableOfContents(self) -> list[dict]:
        return [dict(record) for record in self._table_of_contents]

    @Property(str, notify=stateChanged)
    def projectCode(self) -> str:
        return self._project_code

    def _set_busy(self, value: bool, error: str = "") -> None:
        self._busy = bool(value)
        self._error = str(error or "")
        self.stateChanged.emit()

    @staticmethod
    def _normalize_search_key(value) -> str:
        search_key = str(value or "").strip()
        if search_key and not search_key.startswith("skey://"):
            search_key = "skey://" + search_key
        return search_key

    @Slot()
    def _selected_objects_changed(self) -> None:
        if self._visible:
            self.stateChanged.emit()

    @staticmethod
    def _worker_error(error) -> tuple[str, str]:
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        return str(payload or "Knowledge Base request failed"), stacktrace

    def _release_worker(self, *, cancel: bool = False) -> None:
        worker = self._worker
        self._worker = None
        self._worker_action = ""
        if worker is not None and cancel:
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass

    def _ensure_project_context(self) -> bool:
        """Recover the active project when presentation arrived before lifecycle sync."""
        if not self._project_code:
            self._project_code = str(
                self._application.current_project_code or ""
            )
            if self._project_code:
                self._local_drafts = (
                    self._local_drafts_by_project.setdefault(
                        self._project_code, {}
                    )
                )
        if self._project_code:
            return True
        self._set_busy(False, self.tr("Select a project first"))
        return False

    def _run(
        self,
        action: str,
        *,
        identity: str = "",
        document=None,
        organization=None,
        attachment_key: str = "",
        history_revision: str = "",
        handler=None,
    ) -> bool:
        if self._closed:
            return False
        if self._worker is not None:
            return False
        if not self._ensure_project_context():
            return False
        from thlib.environment import env_inst

        self._generation += 1
        generation = self._generation
        project_code = self._project_code
        arguments = {
            "action": action,
            "project_code": project_code,
            "identity": str(identity or ""),
            "document": deepcopy(document) if document is not None else None,
            "organization": (
                deepcopy(organization) if organization is not None else None
            ),
            "expected_revision": self._revision if identity == self._identity else "",
            "query": self._query,
            "attachment_key": str(attachment_key or ""),
            "history_revision": str(history_revision or ""),
        }

        def operation():
            import thlib.tactic_classes as tc
            return tc.execute_procedure_serverside(
                knowledge_request, arguments, project=project_code
            )

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._set_busy(False, self.tr("Server worker pool is unavailable"))
            return False
        self._worker = worker
        self._worker_action = action

        def ready(result):
            if self._closed or generation != self._generation:
                return
            self._release_worker()
            try:
                payload = dict(result or {})
            except (TypeError, ValueError) as error:
                self._set_busy(False, str(error))
                return
            stale_list = (
                action == "list"
                and str(payload.get("query") or "") != self._query
            )
            if stale_list:
                payload.pop("catalog", None)
                self._apply_common(payload)
                self._pending_search = False
                self.stateChanged.emit()
                self._search_now()
                return
            self._apply_common(payload)
            if handler is not None:
                handler(payload)
            else:
                self.stateChanged.emit()
            if self._pending_search and self._visible:
                self._pending_search = False
                self._search_now()
            elif self._pending_identity and action != "list":
                pending_identity = self._pending_identity
                self._pending_identity = ""
                self.select(pending_identity)

        def failed(error):
            if self._closed or generation != self._generation:
                return
            self._release_worker()
            message, stacktrace = self._worker_error(error)
            if action == "load" and not self._pending_identity:
                self._navigation_identity = (
                    self._identity if self._document else ""
                )
            self._set_busy(False, message)
            debug_log = getattr(self._application, "debug_log", None)
            if debug_log:
                debug_log.raise_error(
                    message,
                    stacktrace=stacktrace,
                    group="knowledge-base",
                )
            if self._pending_search and self._visible:
                self._pending_search = False
                self._search_now()
            elif self._pending_identity and action != "list":
                pending_identity = self._pending_identity
                self._pending_identity = ""
                self.select(pending_identity)

        worker.result.connect(ready, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(failed, Qt.ConnectionType.QueuedConnection)
        self._set_busy(True)
        worker.start()
        return True

    def _apply_common(self, result: dict) -> None:
        self._busy = False
        self._error = ""
        self._initialized = bool(result.get("initialized"))
        self._can_edit = bool(result.get("canEdit"))
        self._can_initialize = bool(result.get("canInitialize"))
        if "catalog" in result and (
            not self.organizationDirty or result.get("organizationSaved")
        ):
            self._replace_catalog(result.get("catalog") or [])
        if "links" in result:
            self._replace_link_index(result.get("links") or [])

    def _replace_catalog(self, records) -> None:
        catalog = [dict(record) for record in records or []]
        for record in catalog:
            record.setdefault("draft", False)
            record.setdefault("localDraft", False)
        positions = {
            str(record.get("identity") or ""): index
            for index, record in enumerate(catalog)
        }
        for identity, state in self._local_drafts.items():
            draft_record = dict(state.get("catalogRecord") or {})
            if not draft_record:
                continue
            if identity in positions:
                catalog[positions[identity]] = draft_record
            else:
                positions[identity] = len(catalog)
                catalog.append(draft_record)
        self._catalog = catalog
        self._rebuild_navigation()

    @staticmethod
    def _local_identity(identity: str) -> bool:
        return str(identity or "").startswith("local:")

    def _draft_catalog_record(self, identity: str) -> dict:
        document = self._document
        return {
            "identity": identity,
            "title": str(document.get("title") or identity),
            "description": str(document.get("description") or ""),
            "excerpt": str(document.get("contentText") or "")[:240],
            "kind": str(document.get("kind") or "article"),
            "parentCode": str(document.get("parentCode") or ""),
            "sortOrder": int(document.get("sortOrder") or 0),
            "updatedBy": "",
            "timestamp": "",
            "searchKey": self._search_key,
            "draft": bool(document.get("draft")),
            "localDraft": True,
        }

    def _persist_local_drafts(self) -> None:
        if self._config_queue is None:
            return
        if self._project_code:
            self._local_drafts_by_project[self._project_code] = (
                self._local_drafts
            )
        self._config_queue.submit(
            {
                "projects": {
                    code: drafts
                    for code, drafts in self._local_drafts_by_project.items()
                    if drafts
                }
            },
            filename="drafts",
            unique_id="cache/knowledge",
            long_abs_path=True,
        )

    def _store_current_draft(self, *, keep_editing: bool) -> bool:
        if not self._editing or not self._identity:
            return False
        identity = self._identity
        if not self.dirty and identity not in self._local_drafts:
            self._editing = False
            self._creating = False
            self.stateChanged.emit()
            return False
        previous = self._local_drafts.get(identity) or {}
        base_record = previous.get("baseCatalogRecord")
        if base_record is None:
            current_record = self._catalog_record(identity)
            base_record = (
                {} if self._local_identity(identity) else current_record
            )
        attachment_context = str(previous.get("attachmentContext") or "")
        if not attachment_context:
            attachment_context = (
                self._search_key or "knowledge:draft:" + identity
            )
        self._local_drafts[identity] = {
            "document": deepcopy(self._document),
            "articleMetadata": deepcopy(self._article_metadata),
            "original": deepcopy(self._original),
            "searchKey": self._search_key,
            "revision": self._revision,
            "creating": self._creating,
            "attachmentContext": attachment_context,
            "attachments": self.uploaded_attachments.records(),
            "attachmentSnapshotKeys": dict(self._attachment_snapshot_keys),
            "baseCatalogRecord": deepcopy(base_record),
            "catalogRecord": self._draft_catalog_record(identity),
        }
        self._persist_local_drafts()
        self._replace_catalog([
            record for record in self._catalog
            if not record.get("localDraft")
        ])
        if not keep_editing:
            self._editing = False
            self._creating = False
        self._error = ""
        self.stateChanged.emit()
        return True

    def _restore_local_draft(self, identity: str) -> bool:
        state = self._local_drafts.get(str(identity or ""))
        if not state:
            return False
        self._clear_history_state()
        self._identity = str(identity)
        self._navigation_identity = self._identity
        self._search_key = str(state.get("searchKey") or "")
        self._revision = str(state.get("revision") or "")
        self._document = self._normalized_document(
            state.get("document") or {}
        )
        self._article_metadata = deepcopy(
            state.get("articleMetadata") or {}
        )
        self._original = deepcopy(state.get("original") or {})
        self._document_complete = True
        self._editing = True
        self._creating = bool(state.get("creating"))
        self._table_of_contents = headings_from_html(
            rich_html_from_markdown(
                self._document.get("contentMarkdown") or ""
            )
        )
        self.attachments.activate_context(str(
            state.get("attachmentContext") or self._search_key
        ))
        self.uploaded_attachments.replace(
            state.get("attachments") or []
        )
        self._attachment_snapshot_keys = dict(
            state.get("attachmentSnapshotKeys") or {}
        )
        self._update_references()
        self._update_linked_objects()
        self._error = ""
        self.editorDocumentChanged.emit()
        self.stateChanged.emit()
        return True

    def _drop_local_draft(self, identity: str) -> None:
        identity = str(identity or "")
        state = self._local_drafts.pop(identity, None)
        if state is None:
            return
        base_record = dict(state.get("baseCatalogRecord") or {})
        records = [
            dict(record) for record in self._catalog
            if str(record.get("identity") or "") != identity
        ]
        if base_record:
            records.append(base_record)
        self._replace_catalog([
            record for record in records if not record.get("localDraft")
        ])
        self._persist_local_drafts()

    def _retarget_local_parent(
        self,
        local_identity: str,
        server_identity: str,
    ) -> None:
        """Keep nested local drafts attached after their parent is saved."""
        if (
            not self._local_identity(local_identity)
            or not server_identity
        ):
            return
        for state in self._local_drafts.values():
            document = state.get("document") or {}
            if str(document.get("parentCode") or "") != local_identity:
                continue
            document["parentCode"] = server_identity
            original = state.get("original") or {}
            if str(original.get("parentCode") or "") == local_identity:
                original["parentCode"] = server_identity
            catalog_record = state.get("catalogRecord") or {}
            catalog_record["parentCode"] = server_identity

    @Slot(result=bool)
    def stash_current_draft(self) -> bool:
        return self._store_current_draft(keep_editing=False)

    @Slot(result=bool)
    def checkpoint_current_draft(self) -> bool:
        return self._store_current_draft(keep_editing=True)

    def _replace_link_index(self, records) -> None:
        link_index: dict[str, list[str]] = {}
        for record in records or []:
            identity = str(record.get("identity") or "")
            if not identity:
                continue
            for raw_search_key in record.get("linkedSearchKeys") or []:
                search_key = self._normalize_search_key(raw_search_key)
                if not search_key:
                    continue
                identities = link_index.setdefault(search_key, [])
                if identity not in identities:
                    identities.append(identity)
        if link_index == self._link_index:
            return
        self._link_index = link_index
        self.linkIndexChanged.emit({
            key: list(identities)
            for key, identities in link_index.items()
        })

    def _rebuild_navigation(self) -> None:
        if self._query:
            records = [dict(record, depth=0, hasChildren=False, expanded=True)
                       for record in self._catalog]
            self.navigation.replace(records)
            return
        by_parent: dict[str, list[dict]] = {}
        identities = {
            str(record.get("identity") or "") for record in self._catalog
        }
        for record in self._catalog:
            parent = str(record.get("parentCode") or "")
            if parent not in identities:
                parent = ""
            by_parent.setdefault(parent, []).append(record)
        for children in by_parent.values():
            children.sort(key=lambda record: (
                int(record.get("sortOrder") or 0),
                str(record.get("kind") or "article") != "section",
                str(record.get("title") or "").casefold(),
            ))
        flat = []
        visited = set()

        def mark_hidden_branch(parent: str) -> None:
            for source in by_parent.get(parent, []):
                identity = str(source.get("identity") or "")
                if not identity or identity in visited:
                    continue
                visited.add(identity)
                mark_hidden_branch(identity)

        def append_branch(parent: str, depth: int) -> None:
            for source in by_parent.get(parent, []):
                identity = str(source.get("identity") or "")
                if not identity or identity in visited:
                    continue
                visited.add(identity)
                children = by_parent.get(identity, [])
                expanded = identity not in self._collapsed
                flat.append(dict(
                    source,
                    depth=depth,
                    hasChildren=bool(children),
                    expanded=expanded,
                ))
                if children and expanded:
                    append_branch(identity, depth + 1)
                elif children:
                    mark_hidden_branch(identity)

        append_branch("", 0)
        for record in self._catalog:
            if str(record.get("identity") or "") not in visited:
                flat.append(dict(
                    record, depth=0, hasChildren=False, expanded=True,
                ))
        self.navigation.replace(flat)

    def _catalog_record(self, identity: str) -> dict:
        identity = str(identity or "")
        return next((
            dict(record) for record in self._catalog
            if str(record.get("identity") or "") == identity
        ), {})

    def _catalog_section_contents(self, section_identity: str) -> list[dict]:
        """Build a section outline from the catalog already shown on screen."""
        by_parent: dict[str, list[dict]] = {}
        for record in self._catalog:
            parent = str(record.get("parentCode") or "")
            by_parent.setdefault(parent, []).append(record)
        for children in by_parent.values():
            children.sort(key=lambda record: (
                int(record.get("sortOrder") or 0),
                str(record.get("kind") or "article") != "section",
                str(record.get("title") or "").casefold(),
            ))

        contents = []
        visited = set()

        def append_children(parent: str, level: int) -> None:
            for child in by_parent.get(parent, []):
                child_identity = str(child.get("identity") or "")
                if not child_identity or child_identity in visited:
                    continue
                visited.add(child_identity)
                contents.append({
                    "identity": child_identity,
                    "title": str(child.get("title") or child_identity),
                    "description": str(child.get("description") or ""),
                    "kind": str(child.get("kind") or "article"),
                    "level": level,
                })
                append_children(child_identity, level + 1)

        append_children(str(section_identity or ""), 1)
        return contents

    def _present_catalog_entry(self, identity: str) -> bool:
        """Present an immediate page shell while its full body is loading."""
        record = self._catalog_record(identity)
        if not record:
            return False
        kind = str(record.get("kind") or "article")
        self._identity = str(identity or "")
        self._search_key = str(record.get("searchKey") or "")
        self._revision = ""
        self._document = {
            "title": str(record.get("title") or ""),
            "description": str(record.get("description") or ""),
            "kind": kind,
            "parentCode": str(record.get("parentCode") or ""),
            "contentMarkdown": "",
            "contentText": "",
            "linkedSearchKeys": [],
            "sortOrder": int(record.get("sortOrder") or 0),
            "draft": bool(record.get("draft")),
        }
        self._article_metadata = {}
        self._table_of_contents = (
            self._catalog_section_contents(identity)
            if kind == "section" else []
        )
        self._original = deepcopy(self._document)
        self._references = []
        self._linked_objects = []
        self._reference_keys.clear()
        self._linked_object_keys.clear()
        self._replace_attachment_snapshots([])
        self._editing = False
        self._document_complete = False
        return True

    def _sync_document_organization(self) -> None:
        if not self._identity or not self._document:
            return
        record = self._catalog_record(self._identity)
        if not record:
            return
        for target in (self._document, self._original):
            if target:
                target["parentCode"] = str(record.get("parentCode") or "")
                target["sortOrder"] = int(record.get("sortOrder") or 0)
        if self._document.get("kind") == "section":
            self._table_of_contents = self._catalog_section_contents(
                self._identity
            )

    def _list_ready(self, _result: dict) -> None:
        self._loaded = True
        pending = self._pending_identity
        self._pending_identity = ""
        self.stateChanged.emit()
        if pending:
            self.select(pending)
        elif self._identity and any(
            str(record.get("identity") or "") == self._identity
            for record in self._catalog
        ):
            self.select(self._identity)
        elif self._catalog and not self._query:
            first_article = next((
                record for record in self._catalog
                if record.get("kind") == "article"
            ), self._catalog[0])
            self.select(str(first_article.get("identity") or ""))
        else:
            self._clear_document()

    def _initialization_ready(self, result: dict) -> None:
        self._list_ready(result)
        self.schemaInitialized.emit()

    def _load_ready(self, result: dict) -> None:
        if result.get("entryMissing"):
            current_identity = self._identity
            current_is_available = current_identity and any(
                str(record.get("identity") or "") == current_identity
                for record in self._catalog
            )
            if (
                current_is_available
                and self._document
                and self._document_complete
            ):
                if not self._pending_identity:
                    self._navigation_identity = current_identity
                self.stateChanged.emit()
                return
            self._clear_document()
            self.stateChanged.emit()
            if self._catalog:
                self.select(str(self._catalog[0].get("identity") or ""))
            return
        self._clear_history_state()
        self._identity = str(result.get("identity") or "")
        if not self._pending_identity:
            self._navigation_identity = self._identity
        self._search_key = str(result.get("searchKey") or "")
        self._revision = str(result.get("revision") or "")
        self._document = self._normalized_document(
            result.get("document") or {}
        )
        self._article_metadata = deepcopy(
            result.get("articleMetadata") or {}
        )
        self._document_complete = True
        self._table_of_contents = (
            [dict(record) for record in result.get("sectionContents") or []]
            if self._document.get("kind") == "section"
            else headings_from_html(rich_html_from_markdown(
                self._document.get("contentMarkdown") or ""
            ))
        )
        self._original = deepcopy(self._document)
        self._sync_document_organization()
        self._editing = bool(
            self._can_edit
            and self._document.get("draft")
        )
        self._creating = bool(self._document.get("draft"))
        self.attachments.activate_context(self._search_key)
        self._replace_attachment_snapshots(
            result.get("attachmentSnapshots") or []
        )
        self._update_references()
        self._update_linked_objects()
        self.editorDocumentChanged.emit()
        self.stateChanged.emit()

    def _apply_saved_document(
        self,
        result: dict,
        *,
        keep_editing: bool,
    ) -> None:
        if result.get("entryMissing"):
            self._editing = True
            self._store_current_draft(keep_editing=True)
            self._error = self.tr(
                "This page was archived or deleted on the server. "
                "Your changes remain as a local draft, and you can "
                "continue with another page."
            )
            self.stateChanged.emit()
            return
        previous_identity = self._identity
        self._clear_history_state()
        self._identity = str(result.get("identity") or "")
        if not self._pending_identity:
            self._navigation_identity = self._identity
        self._search_key = str(result.get("searchKey") or "")
        self._revision = str(result.get("revision") or "")
        self._document = self._normalized_document(
            result.get("document") or {}
        )
        self._article_metadata = deepcopy(
            result.get("articleMetadata") or {}
        )
        self._document_complete = True
        self._table_of_contents = (
            [dict(record) for record in result.get("sectionContents") or []]
            if self._document.get("kind") == "section"
            else headings_from_html(rich_html_from_markdown(
                self._document.get("contentMarkdown") or ""
            ))
        )
        self._original = deepcopy(self._document)
        if self._local_identity(previous_identity):
            self._retarget_local_parent(
                previous_identity, self._identity
            )
            retarget_context = getattr(
                self.attachments, "retarget_context", None
            )
            if callable(retarget_context):
                retarget_context(self._search_key)
        self._drop_local_draft(previous_identity)
        if "catalog" in result:
            self._replace_catalog(result.get("catalog") or [])
        self._sync_document_organization()
        self.attachments.activate_context(self._search_key)
        self._replace_attachment_snapshots(
            result.get("attachmentSnapshots") or []
        )
        self._update_references()
        self._update_linked_objects()
        self._editing = keep_editing
        self._creating = keep_editing and self.draft
        self.editorDocumentChanged.emit()
        self.stateChanged.emit()

    def _save_ready(self, result: dict) -> None:
        self._apply_saved_document(result, keep_editing=False)

    def _draft_save_ready(self, result: dict) -> None:
        self._apply_saved_document(result, keep_editing=True)

    @Slot(str)
    def _sobject_deletion_finished(self, context: str) -> None:
        if str(context or "") != "knowledge":
            return
        deleted_identity = self._pending_delete_identity
        self._pending_delete_identity = ""
        if not deleted_identity:
            return
        self._drop_local_draft(deleted_identity)
        if self._identity == deleted_identity:
            self._clear_document()
        self.stateChanged.emit()
        self.reload()

    def _clear_document(self) -> None:
        self._clear_history_state()
        self._identity = ""
        self._navigation_identity = ""
        self._search_key = ""
        self._revision = ""
        self._document = {}
        self._article_metadata = {}
        self._document_complete = False
        self._table_of_contents = []
        self._original = {}
        self._references = []
        self._linked_objects = []
        self._reference_keys.clear()
        self._linked_object_keys.clear()
        self._editing = False
        self._creating = False
        self._replace_attachment_snapshots([])
        self.editorDocumentChanged.emit()

    def _replace_attachment_snapshots(self, values) -> None:
        """Project server snapshots through the native TACTIC File API."""
        records = []
        snapshot_keys: dict[str, str] = {}
        image_source_candidates: dict[str, list[str]] = {}
        if values:
            import thlib.global_functions as gf
            import thlib.tactic_classes as tc

            for raw_snapshot in values:
                try:
                    snapshot = tc.Snapshot(deepcopy(raw_snapshot))
                    snapshot_key = self._normalize_search_key(
                        snapshot.get_search_key()
                    )
                    files = snapshot.get_files_objects() or []
                except (KeyError, TypeError, ValueError):
                    continue
                for file_object in files:
                    try:
                        if file_object.get_type() in {"web", "icon"}:
                            continue
                        stored_title = str(
                            file_object.get_filename_with_ext() or ""
                        )
                        metadata = file_object.get_metadata() or {}
                        original_title = (
                            str(metadata.get("filename") or "")
                            if isinstance(metadata, dict) else ""
                        ).replace("\\", "/").rsplit("/", 1)[-1]
                        title = original_title or stored_title
                        extension = str(file_object.get_ext() or "").upper()
                        web_url = str(file_object.get_full_web_path() or "")
                        preview = file_object.get_web_preview()
                        is_image = bool(file_object.is_previewable())
                        if preview is None and is_image:
                            preview = file_object
                        preview_url = str(
                            preview.get_full_web_path() if preview else ""
                        )
                        candidates = []
                        for candidate_file in (preview, file_object):
                            if candidate_file is None:
                                continue
                            is_exists = getattr(
                                candidate_file, "is_exists", None
                            )
                            full_abs_path = getattr(
                                candidate_file, "get_full_abs_path", None
                            )
                            if (
                                callable(is_exists)
                                and callable(full_abs_path)
                                and is_exists()
                            ):
                                candidates.append(QUrl.fromLocalFile(
                                    full_abs_path()
                                ).toString())
                            candidate_web_url = str(
                                candidate_file.get_full_web_path() or ""
                            )
                            if candidate_web_url:
                                candidates.append(candidate_web_url)
                        candidates = list(dict.fromkeys(filter(
                            None, candidates
                        )))
                        for remote_source in (web_url, preview_url):
                            if remote_source:
                                image_source_candidates[remote_source] = list(
                                    candidates
                                )
                        size_text = str(
                            gf.sizes(file_object.get_file_size()) or ""
                        )
                    except (
                        AttributeError, KeyError, OSError, TypeError,
                        ValueError,
                    ):
                        continue
                    token = "|".join((snapshot_key, title))
                    records.append({
                        "token": token,
                        "snapshotKey": snapshot_key,
                        "title": title or self.tr("Attachment"),
                        "extension": extension,
                        "sizeText": size_text,
                        "previewUrl": preview_url,
                        "webUrl": web_url,
                        "isImage": is_image,
                    })
                    snapshot_keys[token] = snapshot_key
        self._attachment_snapshot_keys = snapshot_keys
        self._image_source_candidates = image_source_candidates
        self.uploaded_attachments.replace(records)

    def _update_references(self) -> None:
        if self._skey_previews is None:
            self._references = []
            self._reference_keys.clear()
            return
        value = str(self._document.get("contentMarkdown") or "")
        records = self._skey_previews.records_for_text(value)
        self._references = [dict(record) for record in records]
        self._reference_keys = {
            str(record.get("searchKey") or "") for record in records
        }

    def _update_linked_objects(self) -> None:
        search_keys = [
            self._normalize_search_key(value)
            for value in self._document.get("linkedSearchKeys") or []
        ]
        search_keys = list(filter(None, dict.fromkeys(search_keys)))
        self._linked_object_keys = set(search_keys)
        if not search_keys:
            self._linked_objects = []
            return
        if self._skey_previews is None:
            self._linked_objects = [
                {
                    "searchKey": search_key,
                    "status": "loading",
                    "kind": "sobject",
                    "title": search_key,
                    "description": "",
                    "previewUrl": "",
                }
                for search_key in search_keys
            ]
            return
        records_for_keys = getattr(
            self._skey_previews, "records_for_keys", None
        )
        if callable(records_for_keys):
            records = records_for_keys(search_keys)
        else:
            records = self._skey_previews.records_for_text(
                "\n".join(search_keys)
            )
        self._linked_objects = [dict(record) for record in records]

    @Slot(str, object)
    def _reference_ready(self, search_key: str, descriptor) -> None:
        if not self._visible:
            return
        search_key = self._normalize_search_key(search_key)
        update_references = search_key in self._reference_keys
        update_linked = search_key in self._linked_object_keys
        if not update_references and not update_linked:
            return
        if update_references:
            self._update_references()
        if update_linked:
            self._update_linked_objects()
        self.stateChanged.emit()

    @Slot(object)
    def _references_ready(self, descriptors) -> None:
        if not self._visible:
            return
        keys = {
            self._normalize_search_key(record.get("searchKey"))
            for record in descriptors or []
        }
        update_references = bool(self._reference_keys.intersection(keys))
        update_linked = bool(self._linked_object_keys.intersection(keys))
        if update_references:
            self._update_references()
        if update_linked:
            self._update_linked_objects()
        if update_references or update_linked:
            self.stateChanged.emit()

    @Slot(str, str)
    def _project_changed(self, code: str, _title: str) -> None:
        self._generation += 1
        self._release_worker(cancel=True)
        if self._editing:
            self._store_current_draft(keep_editing=False)
        if self._project_code:
            self._local_drafts_by_project[self._project_code] = (
                self._local_drafts
            )
        self._project_code = str(code or "")
        self._local_drafts = self._local_drafts_by_project.setdefault(
            self._project_code, {}
        ) if self._project_code else {}
        self._catalog = []
        self._organization_original = None
        self._loaded = False
        self.navigation.clear()
        self._clear_document()
        self._initialized = False
        self._can_edit = False
        self._can_initialize = False
        self._error = ""
        self._pending_search = False
        self._replace_link_index([])
        self.stateChanged.emit()
        if self._project_code:
            if self._visible:
                self.reload()
            else:
                self.refresh_link_index()

    @Slot(bool)
    def set_visible(self, visible: bool) -> None:
        visible = bool(visible)
        if visible == self._visible:
            return
        self._visible = visible
        self.visibilityChanged.emit(visible)
        if not visible:
            # Search Tab layouts own presentation only.  Keep a catalog or
            # article request authoritative so it can populate this retained
            # controller while another section is shown.
            self._search_timer.stop()
            self._pending_search = False
            return
        self._project_code = str(self._application.current_project_code or "")
        if self._document:
            # Preview resolution is owned by a separate lifecycle. A result
            # may have arrived while this dock was hidden, so re-project the
            # cached descriptors before presenting the retained article.
            self._update_references()
            self._update_linked_objects()
            self.stateChanged.emit()
        if self._project_code and not self._loaded:
            self.reload()

    @Slot()
    def refresh_link_index(self) -> None:
        if self._worker is None and self._ensure_project_context():
            self._run("link_index", handler=self._link_index_ready)

    def _link_index_ready(self, _result: dict) -> None:
        if self._visible and not self._loaded:
            self.reload()
            return
        self.stateChanged.emit()

    @Slot()
    def reload(self) -> None:
        if self.organizationDirty:
            self._error = self.tr(
                "Save or discard navigation changes first"
            )
            self.stateChanged.emit()
            return
        if self._worker is None and self._ensure_project_context():
            self._run("list", handler=self._list_ready)

    @Slot()
    def initialize(self) -> None:
        if self._worker is None and self._can_initialize:
            self._run("initialize", handler=self._initialization_ready)

    @Slot()
    def apply_schema_initialization(self) -> None:
        self._loaded = False
        self._can_initialize = False
        if self._visible:
            self._project_code = str(
                self._application.current_project_code or ""
            )
            self.reload()
            return
        self._initialized = True
        self.stateChanged.emit()
        self.refresh_link_index()

    @Slot(str)
    def set_query(self, value: str) -> None:
        value = str(value or "").strip()
        if value == self._query:
            return
        if self.organizationDirty:
            self._error = self.tr(
                "Save or discard navigation changes first"
            )
            self.stateChanged.emit()
            return
        self._query = value
        self.stateChanged.emit()
        if self._visible:
            # Starting an active single-shot QTimer resets its deadline. Qt's
            # Python binding has no restart() method.
            self._search_timer.start()

    @Slot()
    def _search_now(self) -> None:
        if not self._visible:
            return
        if self._worker is not None:
            self._pending_search = True
            return
        self._pending_search = False
        self._run("list", handler=self._list_ready)

    @Slot(str)
    def select(self, identity: str) -> None:
        identity = str(identity or "")
        if not identity:
            return
        if not self._ensure_project_context():
            return
        if identity != self._identity and self._editing:
            self._store_current_draft(keep_editing=False)
        if identity != self._identity:
            self._clear_history_state()
        if identity != self._navigation_identity:
            self._navigation_identity = identity
            self._error = ""
            self.stateChanged.emit()
        if identity in self._local_drafts:
            if not self._interrupt_read_request():
                self._pending_identity = identity
                return
            self._pending_identity = ""
            self._restore_local_draft(identity)
            return
        if identity != self._identity or not self._document:
            if self._present_catalog_entry(identity):
                self.stateChanged.emit()
        if self._worker is not None:
            self._pending_identity = identity
            return
        if (
            identity == self._identity
            and self._document
            and self._document_complete
        ):
            return
        self._run(
            "load",
            identity=identity,
            handler=lambda result, requested=identity:
                self._selection_load_ready(requested, result),
        )

    def _selection_load_ready(self, requested_identity: str, result: dict) -> None:
        """Do not let an older page response replace a newer click."""
        if str(requested_identity or "") != self._navigation_identity:
            return
        self._load_ready(result)

    @Slot(str)
    def toggle_section(self, identity: str) -> None:
        identity = str(identity or "")
        if identity in self._collapsed:
            self._collapsed.remove(identity)
        else:
            self._collapsed.add(identity)
        self._rebuild_navigation()

    @Slot(str, str, str, result=bool)
    def move_entry(
        self,
        source_identity: str,
        target_identity: str,
        placement: str,
    ) -> bool:
        source_identity = str(source_identity or "")
        target_identity = str(target_identity or "")
        placement = str(placement or "").casefold()
        if (
            not self._can_edit
            or self.busy
            or self.dirty
            or self._query
            or source_identity in self._local_drafts
            or target_identity in self._local_drafts
            or source_identity == target_identity
            or placement not in {"before", "after", "inside"}
        ):
            return False
        source_index = next((
            index for index, record in enumerate(self._catalog)
            if str(record.get("identity") or "") == source_identity
        ), -1)
        target_index = next((
            index for index, record in enumerate(self._catalog)
            if str(record.get("identity") or "") == target_identity
        ), -1)
        if source_index < 0 or target_index < 0:
            return False
        source = self._catalog[source_index]
        target = self._catalog[target_index]
        if placement == "inside":
            if str(target.get("kind") or "article") != "section":
                return False
            new_parent = target_identity
        else:
            new_parent = str(target.get("parentCode") or "")

        parents = {
            str(record.get("identity") or ""):
                str(record.get("parentCode") or "")
            for record in self._catalog
        }
        current = new_parent
        while current:
            if current == source_identity:
                self._error = self.tr(
                    "A section cannot be moved inside its child"
                )
                self.stateChanged.emit()
                return False
            current = parents.get(current, "")

        if self._organization_original is None:
            self._organization_original = deepcopy(self._catalog)
        old_parent = str(source.get("parentCode") or "")
        source["parentCode"] = new_parent

        def siblings(parent_identity: str, *, exclude: str = "") -> list[dict]:
            records = [
                record for record in self._catalog
                if str(record.get("parentCode") or "") == parent_identity
                and str(record.get("identity") or "") != exclude
            ]
            records.sort(key=lambda record: (
                int(record.get("sortOrder") or 0),
                str(record.get("kind") or "article") != "section",
                str(record.get("title") or "").casefold(),
            ))
            return records

        destination = siblings(new_parent, exclude=source_identity)
        if placement == "inside":
            insert_at = len(destination)
        else:
            insert_at = next((
                index for index, record in enumerate(destination)
                if str(record.get("identity") or "") == target_identity
            ), len(destination))
            if placement == "after":
                insert_at += 1
        destination.insert(insert_at, source)
        for index, record in enumerate(destination, 1):
            record["sortOrder"] = index * 10
        if old_parent != new_parent:
            for index, record in enumerate(siblings(old_parent), 1):
                record["sortOrder"] = index * 10

        self._error = ""
        self._sync_document_organization()
        self._rebuild_navigation()
        self.stateChanged.emit()
        return True

    @Slot()
    def save_organization(self) -> None:
        if not self.organizationDirty or self._worker is not None:
            return
        original = {
            str(record.get("identity") or ""): record
            for record in self._organization_original or []
        }
        changes = []
        for record in self._catalog:
            identity = str(record.get("identity") or "")
            before = original.get(identity, {})
            parent_code = str(record.get("parentCode") or "")
            sort_order = int(record.get("sortOrder") or 0)
            if (
                parent_code == str(before.get("parentCode") or "")
                and sort_order == int(before.get("sortOrder") or 0)
            ):
                continue
            changes.append({
                "identity": identity,
                "parentCode": parent_code,
                "sortOrder": sort_order,
            })
        if not changes:
            self._organization_original = None
            self.stateChanged.emit()
            return
        self._run(
            "organize",
            organization=changes,
            handler=self._organization_ready,
        )

    def _organization_ready(self, _result: dict) -> None:
        self._organization_original = None
        self._sync_document_organization()
        self.stateChanged.emit()

    @Slot()
    def discard_organization(self) -> None:
        if not self.organizationDirty or self._worker is not None:
            return
        self._catalog = deepcopy(self._organization_original or [])
        self._organization_original = None
        self._error = ""
        self._sync_document_organization()
        self._rebuild_navigation()
        self.stateChanged.emit()

    def _interrupt_read_request(self) -> bool:
        if self._worker is None:
            return True
        if self._worker_action not in {
            "history", "history_revision", "link_index", "list", "load",
        }:
            return False
        self._generation += 1
        self._release_worker(cancel=True)
        self._busy = False
        self._pending_identity = ""
        self._pending_search = False
        return True

    @Slot(str, str)
    def create(
        self,
        kind: str,
        parent_code: str = "",
    ) -> None:
        kind = str(kind or "article").casefold()
        if kind not in {"article", "section"} or not self._can_edit:
            return
        if not self._ensure_project_context():
            return
        if self._editing:
            self._store_current_draft(keep_editing=False)
        if self.organizationDirty:
            self._error = self.tr(
                "Save or discard navigation changes first"
            )
            self.stateChanged.emit()
            return
        if not self._interrupt_read_request():
            self._error = self.tr("Wait for the current operation to finish")
            self.stateChanged.emit()
            return
        if self._query:
            self._query = ""
            self._search_timer.stop()
            self._pending_search = False
            self.stateChanged.emit()
        title = (
            self.tr("Untitled article")
            if kind == "article"
            else self.tr("New section")
        )
        document = {
            "title": title,
            "description": "",
            "kind": kind,
            "parentCode": str(parent_code or ""),
            "contentMarkdown": "",
            "contentText": "",
            "linkedSearchKeys": [],
            "sortOrder": len(self._catalog) * 10,
            "draft": False,
        }
        local_identity = "local:" + uuid.uuid4().hex
        self._clear_history_state()
        self._identity = local_identity
        self._navigation_identity = local_identity
        self._search_key = ""
        self._revision = ""
        self._document = document
        self._article_metadata = {}
        self._document_complete = True
        self._original = {}
        self._references = []
        self._linked_objects = []
        self._reference_keys.clear()
        self._linked_object_keys.clear()
        self._table_of_contents = []
        self._editing = True
        self._creating = True
        self._error = ""
        self._replace_attachment_snapshots([])
        self.attachments.activate_context(
            "knowledge:draft:" + local_identity
        )
        self.editorDocumentChanged.emit()
        self._store_current_draft(keep_editing=True)

    @Slot(result=int)
    def link_selected_objects(self) -> int:
        if (
            not self._editing
            or self._document.get("kind") != "article"
            or self.busy
        ):
            return 0
        candidates = self.linkableSelectedObjects
        if not candidates:
            return 0
        linked = [
            self._normalize_search_key(value)
            for value in self._document.get("linkedSearchKeys") or []
        ]
        linked = list(filter(None, dict.fromkeys(linked)))
        linked.extend(record["searchKey"] for record in candidates)
        self._document["linkedSearchKeys"] = linked
        self._update_linked_objects()
        if self.localDraft:
            self._store_current_draft(keep_editing=True)
        else:
            self.stateChanged.emit()
        return len(candidates)

    @Slot(str, result=bool)
    def unlink_object(self, search_key: str) -> bool:
        if (
            not self._editing
            or self._document.get("kind") != "article"
            or self.busy
        ):
            return False
        search_key = self._normalize_search_key(search_key)
        if not search_key:
            return False
        linked = [
            self._normalize_search_key(value)
            for value in self._document.get("linkedSearchKeys") or []
        ]
        linked = list(dict.fromkeys(filter(None, linked)))
        if search_key not in linked:
            return False
        self._document["linkedSearchKeys"] = [
            value for value in linked if value != search_key
        ]
        self._update_linked_objects()
        if self.localDraft:
            self._store_current_draft(keep_editing=True)
        else:
            self.stateChanged.emit()
        return True

    @Slot()
    def begin_edit(self) -> None:
        if not self._can_edit or not self._identity or self._busy:
            return
        self._history_preview = {}
        self._refresh_history_model()
        self._editing = True
        self._creating = False
        self._error = ""
        self.stateChanged.emit()

    @Slot(str, "QVariant")
    def set_field(self, name: str, value) -> None:
        if not self._editing or self._busy:
            return
        if name not in {
            "title", "description", "parentCode", "sortOrder",
        }:
            return
        self._document[name] = value
        if self.localDraft:
            self._store_current_draft(keep_editing=True)
        else:
            self.stateChanged.emit()

    @Slot(str)
    def set_content(self, markdown: str) -> None:
        if not self._editing or self._busy:
            return
        markdown = str(markdown or "")
        plain_text = plain_text_from_markdown(markdown)
        if (
            self._document.get("contentMarkdown") == markdown
            and self._document.get("contentText") == plain_text
        ):
            return
        self._document["contentMarkdown"] = markdown
        self._document["contentText"] = plain_text
        if self.localDraft:
            self._store_current_draft(keep_editing=True)
        else:
            self.stateChanged.emit()

    @Slot()
    def save(self) -> None:
        if not self._can_edit or not self._editing or self._busy:
            return
        if not self.dirty and not self.draft and not self.localDraft:
            self._editing = False
            self._creating = False
            self.stateChanged.emit()
            return
        self._run(
            "save",
            identity=(
                "" if self._local_identity(self._identity)
                else self._identity
            ),
            document=self._document,
            handler=self._save_ready,
        )

    @Slot()
    def save_draft(self) -> None:
        if not self._can_edit or not self._editing or self._busy:
            return
        if not self.dirty and self.draft and not self.localDraft:
            return
        self._run(
            "save_draft",
            identity=(
                "" if self._local_identity(self._identity)
                else self._identity
            ),
            document=self._document,
            handler=self._draft_save_ready,
        )

    @Slot()
    def discard(self) -> None:
        if self._busy:
            return
        identity = self._identity
        local_only = self._local_identity(identity)
        state = self._local_drafts.get(identity) or {}
        attachment_context = str(state.get("attachmentContext") or "")
        self._drop_local_draft(identity)
        self._document = deepcopy(self._original)
        self._editing = False
        self._creating = False
        self._error = ""
        self._update_references()
        self._update_linked_objects()
        if local_only:
            clear_context = getattr(self.attachments, "clear_context", None)
            if callable(clear_context) and attachment_context:
                clear_context(attachment_context)
            self._clear_document()
        else:
            self.editorDocumentChanged.emit()
        self.stateChanged.emit()
        if local_only:
            self.reload()

    @Slot()
    def delete_selected(self) -> None:
        if self.organizationDirty:
            self._error = self.tr(
                "Save or discard navigation changes first"
            )
            self.stateChanged.emit()
            return
        if self.localDraft and self._local_identity(self._identity):
            identity = self._identity
            state = self._local_drafts.get(identity) or {}
            attachment_context = str(state.get("attachmentContext") or "")
            self._drop_local_draft(identity)
            clear_context = getattr(self.attachments, "clear_context", None)
            if callable(clear_context) and attachment_context:
                clear_context(attachment_context)
            self._clear_document()
            self.stateChanged.emit()
            if self._catalog:
                self.select(str(self._catalog[0].get("identity") or ""))
        elif self._can_edit and self._identity and not self._busy:
            if self._delete_controller is None:
                self._error = self.tr(
                    "Delete SObject editor is unavailable"
                )
                self.stateChanged.emit()
                return
            target = {
                "searchKey": self._search_key,
                "title": str(
                    self._document.get("title") or self._identity
                ),
                "projectCode": self._project_code,
            }
            self._pending_delete_identity = self._identity
            if not self._delete_controller.begin_search_keys(
                    [target], "knowledge"):
                self._pending_delete_identity = ""

    @Slot(result=bool)
    def upload_attachments(self) -> bool:
        if (
            not self._editing
            or self._document.get("kind") != "article"
            or self.attachments.count < 1
        ):
            return False
        if not self._search_key:
            return self._run(
                "reserve",
                document=self._document,
                handler=self._reserved_for_upload,
            )
        return self._begin_attachment_upload()

    def _begin_attachment_upload(self) -> bool:
        return self.attachments.begin_named_target(
            self._search_key,
            "attachment/knowledge",
            "Knowledge Base attachment",
            self._attachment_owner_code(),
        )

    def _attachment_owner_code(self) -> str:
        query = dict(parse_qsl(urlparse(self._search_key).query))
        return str(
            query.get("code") or query.get("id") or self._identity
        )

    def _reserved_for_upload(self, result: dict) -> None:
        previous_identity = self._identity
        search_key = str(result.get("searchKey") or "")
        retarget_context = getattr(self.attachments, "retarget_context", None)
        if callable(retarget_context):
            retarget_context(search_key)
        self._load_ready(result)
        self._retarget_local_parent(
            previous_identity, self._identity
        )
        self._drop_local_draft(previous_identity)
        if "catalog" in result:
            self._replace_catalog(result.get("catalog") or [])
        self._begin_attachment_upload()

    @Slot(object)
    def _attachments_uploaded(self, snapshot_keys) -> None:
        if not snapshot_keys:
            self.stateChanged.emit()
            return
        self.attachments.clear()
        self._run(
            "attachments",
            identity=self._identity,
            handler=self._attachments_ready,
        )

    def _attachments_ready(self, result: dict) -> None:
        self._revision = str(result.get("revision") or self._revision)
        self._replace_attachment_snapshots(
            result.get("attachmentSnapshots") or []
        )
        self.stateChanged.emit()

    @Slot(str)
    def copy_attachment_web_url(self, token: str) -> None:
        record = self._attachment_record(token)
        web_url = str(record.get("webUrl") or "")
        if web_url:
            QGuiApplication.clipboard().setText(web_url)

    @Slot(str)
    def remove_attachment(self, token: str) -> None:
        snapshot_key = self._attachment_snapshot_keys.get(str(token or ""), "")
        if not snapshot_key or not self._identity or self._busy:
            return
        self._run(
            "delete_attachment",
            identity=self._identity,
            attachment_key=snapshot_key,
            handler=self._attachments_ready,
        )

    def _attachment_record(self, token: str) -> dict:
        token = str(token or "")
        return next((
            dict(record) for record in self.uploaded_attachments.records()
            if str(record.get("token") or "") == token
        ), {})

    @Slot(str, str)
    def _attachment_failed(self, message: str, stacktrace: str) -> None:
        self._error = str(message or self.tr("Attachment upload failed"))
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                self._error,
                stacktrace=str(stacktrace or ""),
                group="knowledge-base/attachments",
            )
        self.stateChanged.emit()

    @Slot()
    def copy_search_key(self) -> None:
        if self._search_key:
            QGuiApplication.clipboard().setText(self._search_key)

    @staticmethod
    def _knowledge_identity(value: str) -> str:
        parsed = urlparse(str(value or ""))
        search_type = "/".join(filter(None, (
            parsed.netloc, parsed.path.lstrip("/"),
        )))
        if not search_type.endswith("/th_knowledge_article"):
            return ""
        values = dict(parse_qsl(parsed.query, keep_blank_values=True))
        return str(values.get("code") or values.get("id") or "")

    @Slot(str, result=bool)
    def is_knowledge_key(self, value: str) -> bool:
        return bool(self._knowledge_identity(value))

    @Slot(str)
    def open_search_key(self, value: str) -> None:
        identity = self._knowledge_identity(value)
        if not identity:
            return
        self.open_identity(identity)

    @Slot(str)
    def open_identity(self, identity: str) -> None:
        identity = str(identity or "")
        if not identity:
            return
        self._pending_identity = identity
        self._application.dock_model.show_panel("knowledge")
        # The dock may be created only after show_panel() returns.  Keep this
        # navigation intent until the QML view consumes it so opening the same
        # already-selected article still leaves the narrow navigation page.
        self._open_article_pending = True
        self.stateChanged.emit()
        self.set_visible(True)
        if any(
            str(record.get("identity") or "") == identity
            for record in self._catalog
        ):
            self._pending_identity = ""
            self.select(identity)
        elif self._worker is None:
            self._pending_identity = ""
            self.select(identity)

    @Slot(str, result=bool)
    def open_for_object(self, search_key: str) -> bool:
        search_key = self._normalize_search_key(search_key)
        identities = self._link_index.get(search_key) or []
        if not identities:
            return False
        self.open_identity(identities[0])
        return True

    @Slot(str)
    def open_link(self, value: str) -> None:
        value = str(value or "").strip()
        if not value:
            return
        if self._knowledge_identity(value):
            self.open_search_key(value)
        elif value.startswith("skey://") and self._skey_previews is not None:
            self._skey_previews.open(value)
        elif value.startswith("tactic-search://"):
            self._application.search(value)
        elif value.startswith(("http://", "https://", "ftp://")):
            QDesktopServices.openUrl(QUrl(value))

    @Slot(str)
    def open_reference(self, search_key: str) -> None:
        self.open_link(search_key)

    def shutdown(self) -> None:
        if self._editing:
            self._store_current_draft(keep_editing=True)
        self._closed = True
        self._generation += 1
        self._search_timer.stop()
        self._release_worker(cancel=True)
        if self._delete_controller is not None:
            try:
                self._delete_controller.deletionFinished.disconnect(
                    self._sobject_deletion_finished
                )
            except (RuntimeError, TypeError):
                pass
