from __future__ import annotations

import html
import re
import traceback
from collections import OrderedDict
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from PySide6.QtCore import QObject, QUrl, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

from .workspace_models.results_presentation import PresentationMixin
from .activity import activity_timestamp_labels
from .request_metrics import request_metrics
from .user_identity import user_avatar_color


SKEY_PATTERN = re.compile(r"skey://[^\s<>\"]+")
WEB_PATTERN = re.compile(r"(?:https?|ftp|tactic-search)://[^\s<>\"]+")


def extract_skeys(value):
    result = []
    for match in SKEY_PATTERN.finditer(str(value or "")):
        key = match.group(0).rstrip(".,;:!?)]}")
        if key and key not in result:
            result.append(key)
    return result


def display_html_without_skeys(value):
    def remove_key(match):
        raw = match.group(0)
        key = raw.rstrip(".,;:!?)]}")
        return raw[len(key):]

    text = SKEY_PATTERN.sub(remove_key, str(value or "")).strip()
    escaped = html.escape(text)
    def link(match):
        raw = match.group(0)
        target = raw.rstrip(".,;:!?)]}")
        return '<a href="{0}">{0}</a>{1}'.format(
            target, raw[len(target):]
        )

    linked = WEB_PATTERN.sub(link, escaped)
    return linked.replace("\n", "<br>")


class SearchKeyPreviewResolver(QObject):
    CACHE_LIMIT = 768
    previewReady = Signal(str, object)
    previewsReady = Signal(object)
    _flushRequested = Signal()

    _kind_icons = {
        "sobject": "inventory_2",
        "task": "task_alt",
        "snapshot": "photo_library",
        "file": "description",
        "note": "sticky_note_2",
        "message": "chat",
        "user": "person",
        "project": "folder_special",
        "knowledge": "article",
    }
    def __init__(self, application, parent=None, clock=None):
        super().__init__(parent or application)
        self._application = application
        self._clock = clock
        self._cache = OrderedDict()
        self._cache_limit = self.CACHE_LIMIT
        self._queued = set()
        self._flush_scheduled = False
        self._pending = set()
        self._visual_pending = set()
        self._preview_files = {}
        self._messages = None
        self._users = None
        self._communication = None
        self._knowledge = None
        application.repository_sync.file_download_done.connect(
            self._preview_downloaded
        )
        self._flushRequested.connect(
            self._flush,
            Qt.ConnectionType.QueuedConnection,
        )

    def _store_cache(self, key, descriptor):
        self._cache[key] = dict(descriptor)
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_limit:
            expired_key, _descriptor = self._cache.popitem(last=False)
            search_key = expired_key[-1]
            self._preview_files.pop(search_key, None)

    def attach_navigation(
            self, messages=None, users=None, communication=None,
            knowledge=None):
        self._messages = messages
        self._users = users
        self._communication = communication
        self._knowledge = knowledge

    @staticmethod
    def _normalize(value):
        value = str(value or "").strip()
        if value and not value.startswith("skey://"):
            value = "skey://" + value
        return value

    @staticmethod
    def _scope():
        try:
            from thlib.environment import env_server
            return (
                str(env_server.get_server() or ""),
                str(env_server.get_user() or ""),
            )
        except (AttributeError, ImportError):
            return ("", "")

    @staticmethod
    def _search_type(search_key):
        parsed = urlparse(search_key)
        return "/".join(filter(None, (parsed.netloc, parsed.path.lstrip("/"))))

    @classmethod
    def _guess_kind(cls, search_key):
        search_type = cls._search_type(search_key).split("?", 1)[0]
        if search_type.endswith("/th_knowledge_article"):
            return "knowledge"
        return {
            "sthpw/task": "task",
            "sthpw/snapshot": "snapshot",
            "sthpw/file": "file",
            "sthpw/note": "note",
            "sthpw/message_log": "message",
            "sthpw/login": "user",
            "sthpw/project": "project",
        }.get(search_type, "sobject")

    @classmethod
    def _placeholder(cls, search_key):
        kind = cls._guess_kind(search_key)
        query = dict(parse_qsl(urlparse(search_key).query))
        code = str(query.get("code") or query.get("id") or "TACTIC item")
        return {
            "searchKey": search_key,
            "status": "loading",
            "kind": kind,
            "title": code,
            "subtitle": kind.replace("_", " ").title(),
            "detail": "Resolving link",
            "description": "",
            "previewUrl": "",
            "icon": cls._kind_icons.get(kind, "link"),
            "openKey": search_key,
            "itemCode": code,
            "parentKey": "",
            "conversationId": "",
            "process": "",
            "error": "",
        }

    def records_for_text(self, value):
        return self.records_for_keys(extract_skeys(value))

    def records_for_keys(self, search_keys):
        records = []
        unresolved = []
        scope = self._scope()
        normalized = []
        for raw_search_key in search_keys or []:
            search_key = self._normalize(raw_search_key)
            if search_key and search_key not in normalized:
                normalized.append(search_key)
        for search_key in normalized:
            cached = self._cache.get((*scope, search_key))
            request_metrics.record_cache("cache.skey_preview", bool(cached))
            records.append(dict(cached or self._placeholder(search_key)))
            if not cached:
                unresolved.append(search_key)
        self.request_many(unresolved)
        return records

    def request_many(self, search_keys):
        changed = False
        scope = self._scope()
        for value in search_keys or []:
            search_key = self._normalize(value)
            cache_key = (*scope, search_key)
            if not search_key or cache_key in self._cache or cache_key in self._pending:
                continue
            self._queued.add(search_key)
            changed = True
        if changed and not self._flush_scheduled:
            self._flush_scheduled = True
            self._flushRequested.emit()

    @Slot(str)
    def retry(self, search_key):
        search_key = self._normalize(search_key)
        self._cache.pop((*self._scope(), search_key), None)
        self.request_many([search_key])
        self.previewReady.emit(search_key, self._placeholder(search_key))

    @Slot(str)
    def copy(self, search_key):
        QGuiApplication.clipboard().setText(self._normalize(search_key))

    @Slot(str)
    def open(self, search_key):
        search_key = self._normalize(search_key)
        descriptor = self._cache.get((*self._scope(), search_key), {})
        kind = str(descriptor.get("kind") or self._guess_kind(search_key))
        if kind == "knowledge" and self._knowledge:
            self._knowledge.open_search_key(search_key)
            return
        if kind == "message" and self._messages:
            if not descriptor.get("canOpen"):
                return
            conversation_id = str(descriptor.get("conversationId") or "")
            if conversation_id:
                message_id = str(descriptor.get("itemCode") or "")
                if str(self._messages.conversationId or "") == conversation_id:
                    self._messages.show_message(message_id)
                else:
                    self._messages.open_forwarded_message(
                        conversation_id, message_id
                    )
                return
        if kind == "user" and self._users:
            login = str(descriptor.get("itemCode") or "")
            if not login:
                parsed = self._direct_key(search_key) or {}
                login = str(parsed.get("identifier") or "")
            if login:
                self._users.open_profile(login)
            return
        if kind == "project":
            self._application.select_project(
                str(descriptor.get("itemCode") or "")
            )
            return
        process = str(descriptor.get("process") or "")
        if process:
            self._application._selected_detail_process = process
        self._application.open_search_key(
            str(descriptor.get("openKey") or search_key)
        )
        if kind == "task":
            self._application.dock_model.show_panel("tasks")
        elif kind == "note":
            self._application.dock_model.show_panel("notes")
            if self._communication:
                self._communication.show_note(search_key)
        elif kind in {"snapshot", "file"}:
            self._application.dock_model.show_panel("snapshot")

    def open_in_context(
            self, search_key, target_search_key="", process="",
            task_code=""):
        """Open a resolved activity without losing its process context."""
        search_key = self._normalize(search_key)
        target_search_key = self._normalize(target_search_key)
        process = str(process or "").strip()
        kind = self._guess_kind(search_key)
        if kind == "snapshot":
            # Opening the snapshot key itself lets SearchWorkspace preserve
            # its code, resolve the parent, expand the process, and select the
            # exact snapshot even when this resolver already cached a preview.
            self._application.open_search_key(search_key)
            self._application.dock_model.show_panel("snapshot")
            return
        if kind != "note":
            self.open(search_key)
            return
        descriptor = self._cache.get((*self._scope(), search_key), {})
        open_key = str(
            target_search_key or descriptor.get("openKey") or search_key
        )
        note_process = str(
            process or descriptor.get("process") or "publish"
        )
        task_code = str(task_code or "").strip()
        if self._communication and task_code:
            self._communication.activate_task_context(
                task_code, open_key, note_process
            )
        self._application.open_search_key_in_process(open_key, note_process)
        self._application.dock_model.show_panel("notes")
        if self._communication:
            self._communication.show_note(search_key)

    def _flush(self):
        self._flush_scheduled = False
        search_keys = list(self._queued)
        self._queued.clear()
        if not search_keys:
            return
        try:
            from thlib.environment import env_inst
            if env_inst.get_current_login_object() is None:
                for search_key in search_keys:
                    self._publish_error(search_key, "Sign in to resolve this link")
                return
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            scope = self._scope()
            self._pending.update((*scope, key) for key in search_keys)
            worker = env_inst.server_pool.add_task(
                lambda: self._resolve_batch(search_keys)
            )
            if worker is None:
                raise RuntimeError("Server worker pool is unavailable")
            worker.result.connect(
                lambda result, current_scope=scope: self._resolved(
                    current_scope, result
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            worker.error.connect(
                lambda error, keys=search_keys, current_scope=scope:
                    self._failed(current_scope, keys, error),
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except (AttributeError, ImportError, RuntimeError) as error:
            for search_key in search_keys:
                self._pending.discard((*self._scope(), search_key))
                self._publish_error(search_key, str(error))

    @classmethod
    def _direct_key(cls, search_key):
        parsed_url = urlparse(search_key)
        query = dict(parse_qsl(parsed_url.query))
        pipeline_code = parsed_url.path.lstrip("/")
        identifier_field = "code" if query.get("code") else (
            "id" if query.get("id") else ""
        )
        if (
            parsed_url.scheme != "skey"
            or not parsed_url.netloc
            or not pipeline_code
            or not identifier_field
        ):
            return None
        return {
            **query,
            "namespace": parsed_url.netloc,
            "pipeline_code": pipeline_code,
            "project": query.get("project") or query.get("project_code") or "",
            "identifier_field": identifier_field,
            "identifier": query.get(identifier_field),
            "item_code": query.get("code") or query.get("id"),
            "context": query.get("context") or "_no_context_",
            "type": "sobject",
        }

    @classmethod
    def _error_descriptor(cls, search_key, error):
        return {
            **cls._placeholder(search_key),
            "status": "error",
            "detail": "Link preview is unavailable",
            "error": str(error),
            "traceback": traceback.format_exc(),
        }

    def _hydrate_note_attachments(self, objects, tactic_classes):
        hydrated = dict(objects or {})
        groups = {}
        for search_key, note in hydrated.items():
            if self._note_attachments(note):
                continue
            info = dict(note.get_info() or {})
            project_code = str(info.get("project_code") or "")
            code = str(info.get("code") or "")
            if not code or not project_code:
                continue
            groups.setdefault(project_code, []).append((search_key, code))

        for project_code, entries in groups.items():
            notes = tactic_classes.get_notes_with_attachments(
                [code for _search_key, code in entries], project_code
            )
            for search_key, code in entries:
                if code in notes:
                    hydrated[search_key] = notes[code]
        return hydrated

    def _resolve_batch(self, search_keys, defer_visuals=True, expand_notes=True):
        import thlib.tactic_classes as tc

        groups = {}
        resolved = {}
        for search_key in search_keys:
            parsed = self._direct_key(search_key)
            if (
                not parsed
                or (
                    not defer_visuals
                    and self._guess_kind(search_key) == "snapshot"
                )
            ):
                resolved[search_key] = {
                    **self._placeholder(search_key),
                    "status": "error",
                    "detail": "Link preview is unavailable",
                    "error": "The link does not identify a TACTIC item",
                    "traceback": "",
                }
                continue
            search_type = "{}/{}".format(
                parsed["namespace"], parsed["pipeline_code"]
            )
            project = str(parsed.get("project") or "")
            if search_type.startswith("sthpw/"):
                project = "sthpw"
            groups.setdefault((
                search_type,
                project,
                parsed["identifier_field"],
            ), []).append(
                (search_key, parsed)
            )

        for (search_type, project, identifier_field), entries in groups.items():
            identifiers = list(dict.fromkeys(
                parsed.get("identifier")
                for _search_key, parsed in entries
            ))
            try:
                objects = tc.get_sobjects(
                    search_type,
                    [(
                        identifier_field,
                        "in",
                        "|".join(str(value) for value in identifiers),
                    )],
                    project_code=project or None,
                    include_info=False,
                    include_snapshots=True,
                ) or {}
                if isinstance(objects, tuple):
                    objects = objects[0]
                if search_type == "sthpw/note":
                    objects = self._hydrate_note_attachments(objects, tc)
                by_identifier = {}
                for item in objects.values():
                    info = dict(item.get_info() or {})
                    value = (
                        item.get_code() if identifier_field == "code"
                        else info.get("id")
                    )
                    by_identifier[str(value or "")] = item
                for search_key, parsed in entries:
                    sobject = by_identifier.get(
                        str(parsed.get("identifier") or "")
                    )
                    if not sobject:
                        resolved[search_key] = {
                            **self._placeholder(search_key),
                            "status": "error",
                            "detail": "Link preview is unavailable",
                            "error": "TACTIC item was not found",
                            "traceback": "",
                        }
                        continue
                    try:
                        if (
                            defer_visuals
                            and self._guess_kind(search_key) == "snapshot"
                        ):
                            resolved[search_key] = self._describe_snapshot_record(
                                search_key, sobject
                            )
                        else:
                            resolved[search_key] = self._describe(
                                search_key,
                                parsed,
                                sobject,
                                defer_preview=self._guess_kind(search_key)
                                    in {"task", "file", "note"},
                            )
                    except Exception as error:
                        resolved[search_key] = self._error_descriptor(
                            search_key, error
                        )
            except Exception as error:
                stacktrace = traceback.format_exc()
                for search_key, _parsed in entries:
                    resolved[search_key] = {
                        **self._placeholder(search_key),
                        "status": "error",
                        "detail": "Link preview is unavailable",
                        "error": str(error),
                        "traceback": stacktrace,
                    }

        if expand_notes:
            nested_keys = list(dict.fromkeys(
                nested_key
                for descriptor in resolved.values()
                for nested_key in descriptor.get("_nestedKeys", [])
                if nested_key not in search_keys
            ))
            nested = {
                descriptor.get("searchKey"): descriptor
                for descriptor in self._resolve_batch(
                    nested_keys, defer_visuals=True, expand_notes=False
                )
            } if nested_keys else {}
            for descriptor in resolved.values():
                keys = descriptor.pop("_nestedKeys", [])
                descriptor["nestedPreviewCount"] = len(keys)
                descriptor["nestedPreviews"] = [
                    dict(nested[key]) for key in keys if key in nested
                ][:4]
                for preview in descriptor["nestedPreviews"]:
                    preview.pop("_needsPreview", None)
                    preview.pop("_previewFile", None)
                    preview.pop("_nestedKeys", None)
                    preview.pop("traceback", None)
                    preview["attachments"] = [
                        {
                            key: value for key, value in attachment.items()
                            if not str(key).startswith("_")
                        }
                        for attachment in preview.get("attachments") or []
                    ]
        else:
            for descriptor in resolved.values():
                descriptor.pop("_nestedKeys", None)
                descriptor.setdefault("nestedPreviews", [])

        return [resolved[key] for key in search_keys if key in resolved]

    @staticmethod
    def _pretty_size(value):
        try:
            size = float(value or 0)
        except (TypeError, ValueError):
            return ""
        units = ("B", "KB", "MB", "GB", "TB")
        unit = 0
        while size >= 1024 and unit < len(units) - 1:
            size /= 1024
            unit += 1
        return "{:.0f} {}".format(size, units[unit]) if unit == 0 else (
            "{:.1f} {}".format(size, units[unit])
        )

    @classmethod
    def _note_attachments(cls, note):
        try:
            process = note.get_process("attachment")
            contexts = process.get_contexts() if process else {}
        except (AttributeError, TypeError):
            contexts = {}
        snapshots = []
        seen = set()
        for context in (contexts or {}).values():
            values = list((context.get_versions() or {}).values())
            values += list((context.get_versionless() or {}).values())
            for snapshot in values:
                code = str(snapshot.get_code() or "")
                if code in seen:
                    continue
                seen.add(code)
                snapshots.append(snapshot)
        records = []
        for snapshot in snapshots:
            snapshot_key = str(snapshot.get_search_key() or "")
            for file_object in snapshot.get_files_objects() or []:
                try:
                    if file_object.get_type() in {"web", "icon"}:
                        continue
                    title = str(file_object.get_filename_with_ext() or "File")
                    extension = str(file_object.get_ext() or "").upper()
                    size = cls._pretty_size(file_object.get_file_size())
                except (AttributeError, OSError, TypeError, ValueError):
                    continue
                try:
                    preview_file = file_object.get_web_preview()
                except (AttributeError, KeyError, TypeError):
                    preview_file = None
                if not preview_file:
                    try:
                        preview_file = (
                            file_object if file_object.is_previewable() else None
                        )
                    except (AttributeError, KeyError, TypeError):
                        preview_file = None
                records.append({
                    "title": title,
                    "extension": extension,
                    "size": size,
                    "searchKey": snapshot_key,
                    "previewUrl": "",
                    "_previewFile": preview_file,
                })
        return records

    def _note_time(self, note, fallback):
        clock = getattr(self, "_clock", None)
        if clock is not None:
            pretty, full = activity_timestamp_labels(
                fallback, clock
            )
            if pretty or full:
                return pretty, full
        try:
            return (
                str(note.get_timestamp(pretty=True) or fallback),
                str(note.get_timestamp(simple=True) or fallback),
            )
        except (AttributeError, TypeError, ValueError):
            value = str(fallback or "")
            return value, value

    @staticmethod
    def _author_color(login):
        return user_avatar_color(login)

    def _timestamp_labels(self, timestamp):
        clock = getattr(self, "_clock", None)
        if clock is not None:
            pretty, full = activity_timestamp_labels(
                timestamp, clock
            )
            if pretty or full:
                return pretty, full
        try:
            import thlib.global_functions as gf

            value = gf.parce_timestamp(str(timestamp or ""))
            return (
                str(gf.get_pretty_datetime(value)),
                str(gf.get_full_datetime(value)),
            )
        except (AttributeError, TypeError, ValueError):
            value = str(timestamp or "")
            return value, value

    @staticmethod
    def _parent_key(info):
        search_type = str(info.get("search_type") or "").split("?", 1)[0]
        search_code = str(info.get("search_code") or "")
        project = str(info.get("project_code") or "")
        if not search_type or not search_code:
            return ""
        query = "project={}&code={}".format(project, search_code) if project else (
            "code={}".format(search_code)
        )
        return "skey://{}?{}".format(search_type, query)

    @staticmethod
    def _snapshot_for(parent, snapshot_code):
        for process in (parent.get_all_processes() or {}).values():
            for context in (process.get_contexts() or {}).values():
                snapshots = {}
                snapshots.update(context.get_versions() or {})
                snapshots.update(context.get_versionless() or {})
                if snapshot_code in snapshots:
                    return snapshots[snapshot_code]
        return None

    @staticmethod
    def _preview_file(snapshot):
        candidates = PresentationMixin._snapshot_preview_candidates(snapshot)
        return candidates[0] if candidates else None

    @staticmethod
    def _sobject_preview_file(sobject):
        candidates = PresentationMixin._root_preview_candidates(sobject)
        return candidates[0] if candidates else None

    def _resolve(self, search_key):
        import thlib.tactic_classes as tc

        parsed, sobject = tc.parce_skey(search_key)
        if not parsed or not sobject:
            raise LookupError("TACTIC item was not found")
        return self._describe(search_key, parsed, sobject)

    def _describe_snapshot_record(self, search_key, snapshot):
        info = dict(snapshot.get_info() or {})
        code = str(info.get("code") or "")
        context = str(info.get("context") or "")
        version = info.get("version")
        parent_key = self._parent_key(info)
        return {
            **self._placeholder(search_key),
            "status": "ready",
            "kind": "snapshot",
            "title": str(info.get("search_code") or code or "Snapshot"),
            "subtitle": "Snapshot · {}".format(context or "No context"),
            "detail": "Version {}".format(version if version is not None else "?"),
            "itemCode": code,
            "parentKey": parent_key,
            "openKey": search_key,
            "process": str(info.get("process") or ""),
            "context": context,
            "version": self._version_label(version),
            "revision": self._revision_label(info.get("revision")),
            "author": PresentationMixin._snapshot_author(
                str(info.get("login") or "")
            ),
            "timestamp": str(info.get("timestamp") or "").split(".")[0],
            "description": str(info.get("description") or ""),
            "repository": PresentationMixin._repository_title(
                str(info.get("repo") or "")
            ),
            "repositoryColor": PresentationMixin._repository_color(
                str(info.get("repo") or ""), "#607d8b"
            ),
            "fileSize": "",
            "fileExtension": "",
            "fileExists": False,
            "isLatest": bool(info.get("is_latest")),
            "isVersionless": version in (-1, 0, "-1", "0"),
            "isMultiple": False,
            "infoChips": [],
            "_needsPreview": True,
        }

    @staticmethod
    def _version_label(value):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return str(value or "")
        return "latest" if number in (-1, 0) else "v{:03d}".format(number)

    @staticmethod
    def _revision_label(value):
        try:
            number = int(value or 0)
        except (TypeError, ValueError):
            return str(value or "")
        return "r{:03d}".format(number) if number else ""

    @classmethod
    def _snapshot_display(cls, snapshot):
        info = dict(snapshot.get_snapshot() or {})
        try:
            files = list(snapshot.get_files_objects() or [])
        except (AttributeError, KeyError, TypeError):
            files = []
        visible_groups = {}
        for file_object in files:
            try:
                file_type = str(file_object.get_type() or "main")
            except (AttributeError, KeyError, TypeError):
                file_type = "main"
            if file_type in {"icon", "web", "playblast"}:
                continue
            visible_groups.setdefault(file_type, []).append(file_object)
        primary_group = next(
            (group for group in visible_groups.values() if group), []
        )
        primary = primary_group[0] if primary_group else None
        multiple = len(primary_group) > 1
        title = str(info.get("context") or info.get("code") or "Snapshot")
        if multiple:
            title = "Multiple files | {}".format(len(primary_group))
        elif primary:
            try:
                meta = primary.get_meta_file_object()
                title = str(
                    meta.get_pretty_file_name()
                    if meta else primary.get_filename_with_ext()
                )
            except (AttributeError, KeyError, TypeError):
                pass
        try:
            file_size = PresentationMixin._pretty_size(
                primary.get_file_size()
            ) if primary else ""
        except (AttributeError, KeyError, TypeError, OSError):
            file_size = ""
        try:
            extension = str(primary.get_ext() or "").upper() if primary else ""
        except (AttributeError, KeyError, TypeError):
            extension = ""
        repository = str(info.get("repo") or "")
        version = info.get("version")
        return {
            "title": title,
            "subtitle": str(info.get("description") or ""),
            "detail": str(info.get("context") or ""),
            "context": str(info.get("context") or ""),
            "version": cls._version_label(version),
            "revision": cls._revision_label(info.get("revision")),
            "author": PresentationMixin._snapshot_author(
                str(info.get("login") or "")
            ),
            "timestamp": str(info.get("timestamp") or "").split(".")[0],
            "description": str(info.get("description") or ""),
            "repository": PresentationMixin._repository_title(repository),
            "repositoryColor": PresentationMixin._repository_color(
                repository, "#607d8b"
            ),
            "fileSize": file_size,
            "fileExtension": extension,
            "fileExists": PresentationMixin._file_exists(primary)
                if primary else False,
            "isLatest": bool(snapshot.is_latest()),
            "isVersionless": bool(snapshot.is_versionless()),
            "isMultiple": multiple,
            "fileCount": len(primary_group),
            "infoChips": PresentationMixin._snapshot_chips(
                primary, str(info.get("context") or "")
            ),
            "_previewFile": cls._preview_file(snapshot),
        }

    def _describe(self, search_key, parsed, sobject, defer_preview=False):
        import thlib.tactic_classes as tc

        info = dict(sobject.get_info() or {})
        kind = self._guess_kind(search_key)
        code = str(info.get("code") or parsed.get("item_code") or "")
        try:
            stype = sobject.get_stype()
            type_title = str(stype.get_pretty_name() or "") if stype else ""
        except (AttributeError, KeyError, TypeError):
            type_title = ""
        type_title = type_title or self._search_type(search_key).partition(
            "/"
        )[2].replace("_", " ").title()
        title = str(sobject.get_title() or code or type_title or "TACTIC item")
        project = str(
            info.get("project_code") or parsed.get("project")
            or parsed.get("project_code") or ""
        )
        parent_key = self._parent_key(info)
        descriptor = {
            **self._placeholder(search_key),
            "status": "ready",
            "kind": kind,
            "title": title,
            "subtitle": type_title,
            "detail": " · ".join(value for value in (code, project) if value),
            "description": str(info.get("description") or ""),
            "itemCode": code,
            "parentKey": parent_key,
            "openKey": parent_key or search_key,
        }
        preview_source = sobject
        parent_title = ""
        if parent_key and kind in {"task", "file", "note"}:
            if not defer_preview:
                try:
                    _parent_data, parent = tc.parce_skey(parent_key)
                    parent_title = str(parent.get_title() or "") if parent else ""
                except (
                    AttributeError, KeyError, LookupError, TypeError, ValueError
                ):
                    parent_title = ""

        if kind == "task":
            process = str(info.get("process") or "Task")
            assignee = str(info.get("assigned") or info.get("login") or "Unassigned")
            status = str(info.get("status") or "No status")
            descriptor.update(
                title=process.replace("_", " ").title(),
                subtitle="{} · {}".format(assignee, status),
                detail=" · ".join(value for value in (
                    parent_title or str(info.get("search_code") or ""),
                    str(info.get("bid_end_date") or info.get("end_date") or ""),
                ) if value),
                process=process,
            )
            preview_source = None
        elif kind == "snapshot":
            snapshot_code = str(parsed.get("item_code") or code)
            snapshot = self._snapshot_for(sobject, snapshot_code)
            if not snapshot:
                snapshots = sobject.query_snapshots(
                    filters=[("code", snapshot_code)]
                )
                snapshot = tc.Snapshot(snapshots[0]) if snapshots else None
            if snapshot:
                snapshot_info = dict(snapshot.get_snapshot() or {})
                descriptor.update(
                    itemCode=snapshot_code,
                    process=str(snapshot_info.get("process") or ""),
                    parentKey=str(sobject.get_search_key() or ""),
                    openKey=search_key,
                )
                descriptor.update(self._snapshot_display(snapshot))
            preview_source = None
        elif kind == "file":
            filename = str(info.get("file_name") or title)
            extension = Path(filename).suffix.lstrip(".").upper() or "FILE"
            descriptor.update(
                title=filename,
                subtitle="{} file · {}".format(
                    extension, str(info.get("type") or "main")
                ),
                detail=" · ".join(value for value in (
                    self._pretty_size(info.get("st_size")),
                    str(info.get("snapshot_code") or ""),
                    parent_title,
                ) if value),
                openKey=(
                    "skey://sthpw/snapshot?code={}".format(
                        info.get("snapshot_code")
                    ) if info.get("snapshot_code") else parent_key or search_key
                ),
            )
            preview_source = None
        elif kind == "note":
            author = str(info.get("login") or "Unknown user")
            raw_note = str(info.get("note") or "")
            note_text = " ".join(raw_note.split())
            body = SKEY_PATTERN.sub("", raw_note).strip()
            attachments = self._note_attachments(sobject)
            timestamp = str(info.get("timestamp") or "")
            time_pretty, time_simple = self._note_time(sobject, timestamp)
            descriptor.update(
                title="Note by {}".format(author),
                subtitle=" · ".join(value for value in (
                    str(info.get("process") or "publish"), parent_title
                ) if value),
                detail=timestamp,
                process=str(info.get("process") or "publish"),
                body=body,
                attachments=attachments[:6],
                attachmentCount=len(attachments),
                _nestedKeys=extract_skeys(note_text),
                author=author,
                authorDisplay=author,
                avatarUrl="",
                initials=(author[:2] or "?").upper(),
                authorColor=self._author_color(author),
                timePretty=time_pretty,
                timeSimple=time_simple,
            )
            preview_source = None
        elif kind == "message":
            author = str(info.get("login") or "Unknown user")
            message_body = str(info.get("message") or "")
            message_text = " ".join(message_body.split())
            timestamp = str(info.get("timestamp") or "")
            time_pretty, time_simple = self._timestamp_labels(timestamp)
            descriptor.update(
                title="Message by {}".format(author),
                subtitle=str(info.get("message_code") or "Conversation"),
                detail=message_text[:120] or str(info.get("timestamp") or ""),
                conversationId=str(info.get("message_code") or ""),
                itemCode=search_key,
                body=message_body,
                author=author,
                authorDisplay=author,
                avatarUrl="",
                initials=(author[:2] or "?").upper(),
                authorColor=self._author_color(author),
                timePretty=time_pretty,
                timeSimple=time_simple,
                canOpen=False,
            )
            preview_source = None
        elif kind == "user":
            descriptor.update(
                title=str(info.get("display_name") or info.get("name") or code),
                subtitle=str(info.get("email") or "TACTIC user"),
                itemCode=str(info.get("login") or code),
            )
        elif kind == "project":
            descriptor.update(
                title=str(info.get("title") or info.get("name") or code),
                subtitle="TACTIC project",
            )
        elif kind == "knowledge":
            article_kind = str(info.get("kind") or "article").casefold()
            if article_kind not in {"article", "section"}:
                article_kind = "article"
            excerpt = " ".join(
                str(info.get("content_text") or "").split()
            )[:180]
            descriptor.update(
                articleKind=article_kind,
                description=str(info.get("description") or ""),
                excerpt=excerpt,
                parentCode=str(info.get("parent_code") or ""),
                subtitle="",
                detail="",
                openKey=search_key,
            )
            preview_source = None

        if defer_preview and preview_source and "_previewFile" not in descriptor:
            descriptor["_needsPreview"] = True
        elif preview_source and "_previewFile" not in descriptor:
            candidate = self._sobject_preview_file(preview_source)
            if candidate:
                descriptor["_previewFile"] = candidate
        return descriptor

    def _resolved(self, scope, result):
        records = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        published = []
        visual_keys = []
        for descriptor in records or []:
            search_key = str(descriptor.get("searchKey") or "")
            self._pending.discard((*scope, search_key))
            self._decorate_user(descriptor)
            self._prepare_attachment_previews(search_key, descriptor)
            preview_file = descriptor.pop("_previewFile", None)
            needs_preview = bool(descriptor.pop("_needsPreview", False))
            stacktrace = str(descriptor.pop("traceback", "") or "")
            if preview_file:
                descriptor["previewUrl"] = self._preview_url(
                    search_key, preview_file
                )
            self._store_cache((*scope, search_key), descriptor)
            published.append(dict(descriptor))
            if needs_preview and descriptor.get("status") == "ready":
                visual_keys.append(search_key)
            if descriptor.get("status") == "error":
                self._log_error(
                    descriptor.get("error") or "Link preview failed",
                    stacktrace,
                )
        if published:
            self.previewsReady.emit(published)
        if visual_keys:
            self._request_visuals(scope, visual_keys)

    def _decorate_user(self, descriptor):
        kind = descriptor.get("kind")
        if kind == "message" and self._messages:
            conversation_id = str(descriptor.get("conversationId") or "")
            model = getattr(self._messages, "conversations", None)
            records = getattr(model, "_records", ())
            if any(
                str(record.get("conversationId") or "") == conversation_id
                for record in records
            ):
                descriptor["canOpen"] = True
        if kind not in {"note", "message"} or not self._users:
            return
        login = str(descriptor.get("author") or "")
        model = getattr(self._users, "users", None)
        records = getattr(model, "_records", ())
        user = next((
            record for record in records
            if str(record.get("login") or "") == login
        ), {})
        if not user:
            return
        descriptor.update(
            authorDisplay=str(user.get("displayName") or login or "User"),
            avatarUrl=str(user.get("avatarUrl") or ""),
            initials=str(user.get("initials") or "?")[:2].upper(),
        )

    def _prepare_attachment_previews(self, search_key, descriptor):
        attachments = [
            dict(record) for record in descriptor.get("attachments") or []
        ]
        for index, record in enumerate(attachments):
            preview_file = record.pop("_previewFile", None)
            if preview_file:
                token = "{}#attachment:{}".format(search_key, index)
                record["previewUrl"] = self._preview_url(token, preview_file)
        if attachments:
            descriptor["attachments"] = attachments

    def _request_visuals(self, scope, search_keys):
        keys = [
            key for key in search_keys
            if (*scope, key) not in self._visual_pending
        ]
        if not keys:
            return
        try:
            from thlib.environment import env_inst
            if env_inst.server_pool.is_stopped:
                env_inst.server_pool.start()
            self._visual_pending.update((*scope, key) for key in keys)
            worker = env_inst.server_pool.add_task(
                lambda: self._resolve_visual_batch(keys)
            )
            if worker is None:
                raise RuntimeError("Server worker pool is unavailable")
            worker.result.connect(
                lambda result, current_scope=scope: self._visuals_resolved(
                    current_scope, result
                ),
                Qt.ConnectionType.QueuedConnection,
            )
            worker.error.connect(
                lambda error, current_scope=scope, current_keys=keys:
                    self._visuals_failed(current_scope, current_keys, error),
                Qt.ConnectionType.QueuedConnection,
            )
            worker.start()
        except (AttributeError, ImportError, RuntimeError) as error:
            for search_key in keys:
                self._visual_pending.discard((*scope, search_key))
            self._log_error(str(error))

    def _resolve_visual_batch(self, search_keys):
        snapshot_keys = []
        regular_keys = []
        for search_key in search_keys:
            if self._guess_kind(search_key) != "snapshot":
                regular_keys.append(search_key)
                continue
            snapshot_keys.append(search_key)
        records = self._resolve_snapshot_visuals(snapshot_keys)
        if regular_keys:
            records.extend(self._resolve_batch(
                regular_keys, defer_visuals=False
            ))
        return records

    def _resolve_snapshot_visuals(self, search_keys):
        import thlib.tactic_classes as tc

        groups = {}
        invalid = []
        for search_key in search_keys:
            parsed = self._direct_key(search_key)
            if not parsed:
                invalid.append(search_key)
                continue
            groups.setdefault(parsed["identifier_field"], []).append(
                (search_key, str(parsed["identifier"]))
            )
        records = [
            {
                "searchKey": search_key,
                "_visualError": "The link does not identify a snapshot",
                "traceback": "",
            }
            for search_key in invalid
        ]
        server = tc.server_start(project="sthpw")
        for identifier_field, entries in groups.items():
            try:
                identifiers = list(dict.fromkeys(
                    identifier for _search_key, identifier in entries
                ))
                snapshots = server.query_snapshots(
                    filters=[(
                        identifier_field,
                        "in",
                        "|".join(identifiers),
                    )],
                    include_files=True,
                )
                by_identifier = {
                    str(snapshot.get(identifier_field) or ""): snapshot
                    for snapshot in snapshots or []
                }
                for search_key, identifier in entries:
                    snapshot_data = by_identifier.get(identifier)
                    if not snapshot_data:
                        records.append({
                            "searchKey": search_key,
                            "_visualError": "TACTIC snapshot was not found",
                            "traceback": "",
                        })
                        continue
                    snapshot = tc.Snapshot(dict(snapshot_data))
                    records.append({
                        "searchKey": search_key,
                        "status": "ready",
                        **self._snapshot_display(snapshot),
                    })
            except Exception as error:
                stacktrace = traceback.format_exc()
                records.extend({
                    "searchKey": search_key,
                    "_visualError": str(error),
                    "traceback": stacktrace,
                } for search_key, _identifier in entries)
        return records

    def _visuals_resolved(self, scope, result):
        records = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        published = []
        for descriptor in records or []:
            search_key = str(descriptor.get("searchKey") or "")
            self._visual_pending.discard((*scope, search_key))
            error = str(descriptor.pop("_visualError", "") or "")
            stacktrace = str(descriptor.pop("traceback", "") or "")
            if descriptor.get("status") == "error":
                error = str(descriptor.get("error") or "Link preview failed")
            if error:
                self._log_error(error, stacktrace)
                continue
            preview_file = descriptor.pop("_previewFile", None)
            descriptor.pop("_needsPreview", None)
            current = dict(
                self._cache.get((*scope, search_key))
                or self._placeholder(search_key)
            )
            current.update(descriptor)
            descriptor = current
            if preview_file:
                descriptor["previewUrl"] = self._preview_url(
                    search_key, preview_file
                )
            self._store_cache((*scope, search_key), descriptor)
            published.append(dict(descriptor))
        if published:
            self.previewsReady.emit(published)

    def _visuals_failed(self, scope, search_keys, error):
        for search_key in search_keys:
            self._visual_pending.discard((*scope, search_key))
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        self._log_error(str(payload or "Link preview failed"), stacktrace)

    def _preview_url(self, search_key, file_object):
        try:
            if file_object.is_local_current():
                return QUrl.fromLocalFile(
                    str(file_object.get_full_abs_path())
                ).toString()
            if self._application.repository_sync.previews_through_http_enabled():
                self._preview_files[search_key] = file_object
                self._application.repository_sync.schedule_file_object(
                    file_object, process="preview", auto_start=True,
                    is_ui_preview=True,
                )
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            return ""
        return ""

    def _preview_downloaded(self, file_object):
        if not any(
            tracked is file_object for tracked in self._preview_files.values()
        ):
            return
        for preview_key, tracked in list(self._preview_files.items()):
            if tracked is not file_object or not tracked.is_exists():
                continue
            search_key = preview_key
            attachment_index = -1
            if "#attachment:" in preview_key:
                search_key, raw_index = preview_key.rsplit("#attachment:", 1)
                try:
                    attachment_index = int(raw_index)
                except ValueError:
                    attachment_index = -1
            descriptor = self._cache.get((*self._scope(), search_key))
            if descriptor:
                ready_url = QUrl.fromLocalFile(
                    str(tracked.get_full_abs_path())
                ).toString()
                if attachment_index >= 0:
                    attachments = [
                        dict(record)
                        for record in descriptor.get("attachments") or []
                    ]
                    if attachment_index < len(attachments):
                        attachments[attachment_index]["previewUrl"] = ready_url
                        descriptor["attachments"] = attachments
                else:
                    descriptor["previewUrl"] = ready_url
                self.previewReady.emit(search_key, dict(descriptor))
            self._preview_files.pop(preview_key, None)

    def _failed(self, scope, search_keys, error):
        payload = error[0] if isinstance(error, tuple) and error else error
        stacktrace = ""
        if isinstance(payload, dict):
            stacktrace = str(payload.get("stacktrace") or "")
            payload = payload.get("exception") or payload.get("message") or payload
        for search_key in search_keys:
            self._pending.discard((*scope, search_key))
            self._publish_error(search_key, str(payload or "Link preview failed"))
        self._log_error(str(payload or "Link preview failed"), stacktrace)

    def _publish_error(self, search_key, message):
        descriptor = {
            **self._placeholder(search_key),
            "status": "error",
            "detail": "Link preview is unavailable",
            "error": str(message or "Link preview failed"),
        }
        self._store_cache((*self._scope(), search_key), descriptor)
        self.previewReady.emit(search_key, dict(descriptor))

    def _log_error(self, message, stacktrace=""):
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                message,
                stacktrace=stacktrace,
                group="communication/skey-preview",
            )
