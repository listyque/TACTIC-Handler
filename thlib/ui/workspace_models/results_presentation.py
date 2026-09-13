"""WorkspaceItemModel: presentation."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QModelIndex, Qt, QUrl, Slot

from .results_types import WorkspaceNode
from .watch_folders import _watch_folder_record


class PresentationMixin:
    @staticmethod
    def _build_info_items(stype, info: dict) -> list[dict]:
        """Project TACTIC table definitions into compact interactive values."""
        if stype is None:
            return []

        try:
            table_elements = stype.get_definition("table") or []
        except (AttributeError, KeyError, TypeError, ValueError):
            return []
        table_columns = {
            str(element.get("name") or ""): str(
                element.get("title")
                or str(element.get("name") or "").replace("_", " ").title()
            )
            for element in table_elements
            if element.get("name")
        }
        if not table_columns:
            return []

        try:
            color_definition = stype.get_definition("color", bs=True)
        except (AttributeError, KeyError, TypeError, ValueError):
            color_definition = None
        color_column = ""
        color_values: dict[str, str] = {}
        try:
            color_element = getattr(color_definition, "element", None)
            if color_element:
                color_column = str(color_element.get("name") or "")
            colors = getattr(color_definition, "colors", None)
            if colors:
                for element in colors.find_all():
                    name = str(element.get("name") or "")
                    value = str(element.text or "").strip()
                    if name and value:
                        color_values[name] = value
        except (AttributeError, KeyError, TypeError, ValueError):
            color_column = ""
            color_values = {}

        try:
            edit_definition = stype.get_definition(
                "edit_definition", bs=True
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            edit_definition = None
        edit_labels: dict[str, dict[str, str]] = {}
        try:
            edit_root = getattr(edit_definition, "edit_definition", None)
            if getattr(edit_definition, "element", None) and edit_root:
                for element in edit_root.find_all():
                    column = str(element.get("name") or "")
                    values = getattr(element, "values", None)
                    labels = getattr(element, "labels", None)
                    if not column or not values or not labels:
                        continue
                    edit_labels[column] = dict(zip(
                        str(values.text or "").split("|"),
                        str(labels.text or "").split("|"),
                    ))
        except (AttributeError, KeyError, TypeError, ValueError):
            edit_labels = {}

        excluded = {
            "__search_type__", "__search_key__", "__tasks_count__",
            "__notes_count__", "__snapshots__", "name", "code",
            "keywords", "description", "timestamp",
        }
        items = []
        for column, raw_value in info.items():
            if (
                not raw_value
                or column not in table_columns
                or column in excluded
            ):
                continue

            try:
                value = edit_labels.get(column, {}).get(raw_value, raw_value)
            except TypeError:
                value = raw_value
            text_value = str(value)
            color = (
                color_values.get(str(raw_value), "")
                if column == color_column else ""
            )
            column_title = table_columns[column]
            if text_value.lower().startswith(
                ("https://", "http://", "ftp://")
            ):
                items.append({
                    "column": str(column),
                    "kind": "link",
                    "text": column_title,
                    "tooltip": text_value,
                    "url": text_value,
                    "color": color,
                })
            elif isinstance(value, bool):
                items.append({
                    "column": str(column),
                    "kind": "boolean",
                    "text": column_title,
                    "tooltip": f"{column_title}: {value}",
                    "url": "",
                    "color": color,
                })
            else:
                items.append({
                    "column": str(column),
                    "kind": "text",
                    "text": text_value[:30],
                    "tooltip": text_value,
                    "url": "",
                    "color": color,
                })
        return items

    @staticmethod
    def _pretty_size(value) -> str:
        try:
            size = float(value or 0)
        except (TypeError, ValueError):
            return ""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024 or unit == "TB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return ""

    def _controls_for(self, node: WorkspaceNode | None = None) -> list[dict]:
        # Keep the historical class-call form used by a few isolated model
        # tests while normal model access can include project decoration state.
        if node is None:
            node = self
            knowledge_articles = ()
        else:
            knowledge_articles = self._knowledge_index.get(
                self._normalized_search_key(node.search_key), ()
            )
        signature = (
            node.node_type,
            node.needs_sync,
            node.watch_state,
            knowledge_articles,
            node.relationship,
            node.linkable_relation,
            node.child_count,
        )
        if node.controls_signature == signature:
            return node.controls_cache
        if node.node_type == "sobject":
            watch_configured = node.watch_state != "none"
            controls = [
                {
                    "command": "repo_sync",
                    "icon": "repository-sync",
                    "tip": "Open Repository Sync Dialog",
                    "active": node.needs_sync,
                },
                {
                    "command": "watch_folder",
                    "icon": "visibility" if watch_configured else "visibility_off",
                    "tip": "Open Watch-Folder Dialog",
                    "active": watch_configured,
                    "persistent": watch_configured,
                    "success": watch_configured,
                },
            ]
            controls.append({
                "command": "relations",
                "icon": "sitemap",
                "tip": "Related and child sObjects",
                "active": False,
            })
            if knowledge_articles:
                controls.append({
                    "command": "knowledge_article",
                    "icon": "book-open",
                    "tip": QCoreApplication.translate(
                        "WorkspaceItemModel",
                        "Open linked Knowledge Base article",
                    ),
                    "active": True,
                    "persistent": True,
                    "success": True,
                })
            node.controls_cache = controls
            node.controls_signature = signature
            return controls
        if node.node_type == "process":
            node.controls_cache = []
            node.controls_signature = signature
            return node.controls_cache
        if node.node_type == "relation":
            controls = [{
                "command": "add_related",
                "icon": "add",
                "tip": "Add new Related sObject",
                # A non-zero child count is information, not an active/toggled
                # state.  The count is rendered separately by the row.
                "active": False,
            }]
            if node.linkable_relation:
                controls.insert(0, {
                    "command": "link_related",
                    "icon": "link",
                    "tip": "Link sObjects Interface",
                    "active": False,
                })
            node.controls_cache = controls
            node.controls_signature = signature
            return controls
        node.controls_cache = []
        node.controls_signature = signature
        return node.controls_cache

    @staticmethod
    def _safe_file_url(file_object) -> str:
        if not file_object:
            return ""
        try:
            path = file_object.get_full_abs_path()
            if path and file_object.is_local_current():
                resolved = Path(path).resolve()
                stat = resolved.stat()
                url = QUrl.fromLocalFile(str(resolved))
                # Versionless previews deliberately reuse their repository
                # path.  Qt caches decoded images by URL, so returning the
                # bare path after an overwrite keeps showing the previous
                # texture even though TACTIC and the filesystem are current.
                # The local stat is the content revision already verified by
                # File.is_local_current(); no hash or parallel cache is needed.
                url.setQuery(
                    "revision={0}-{1}".format(
                        int(stat.st_mtime_ns), int(stat.st_size),
                    )
                )
                return url.toString()
        except (AttributeError, KeyError, TypeError, OSError):
            pass
        return ""

    @staticmethod
    def _is_image_file(file_object) -> bool:
        try:
            filename = str(file_object.get_filename_with_ext() or "")
        except (AttributeError, KeyError, TypeError):
            try:
                info = file_object.get_dict() or {}
                filename = str(info.get("file_name") or info.get("name") or "")
            except (AttributeError, KeyError, TypeError):
                return False
        return Path(filename).suffix.lower() in {
            ".bmp", ".gif", ".ico", ".jpeg", ".jpg", ".png",
            ".svg", ".tga", ".tif", ".tiff", ".webp",
        }

    def _preview_url(self, file_object) -> str:
        if not file_object or not self._is_image_file(file_object):
            return ""
        local_url = self._safe_file_url(file_object)
        if local_url:
            return local_url
        if (
            self.repository_sync
            and self.repository_sync.previews_through_http_enabled()
        ):
            try:
                local_path = str(file_object.get_full_abs_path() or "")
                if local_path:
                    handle = self.repository_sync.schedule_file_object(
                        file_object, process="preview", auto_start=True,
                        is_ui_preview=True,
                    )
                    token = f"pending-preview:{handle.task_id}"
                    self._pending_preview_paths[token] = local_path
                    return token
            except (AttributeError, KeyError, TypeError, ValueError, OSError):
                pass
        return ""

    def localize_preview(
        self, local_path: str, pending_paths: dict[str, str] | None = None
    ) -> None:
        local_path = str(Path(local_path).resolve())
        ready_url = (
            QUrl.fromLocalFile(local_path).toString()
            + f"?ready={int(time.time() * 1000)}"
        )
        changed_rows = []
        changed_tokens = set()
        for row, node in enumerate(self._items):
            changed = False
            for attribute in ("preview_url", "card_preview_url"):
                token = getattr(node, attribute)
                pending_path = self._pending_preview_paths.get(token)
                if not pending_path or str(Path(pending_path).resolve()) != local_path:
                    continue
                changed_tokens.add(token)
                setattr(node, attribute, ready_url)
                changed = True
            if changed:
                node.preview_revealed = False
                changed_rows.append(row)
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(
                index, index,
                [self.PreviewUrlRole, self.CardPreviewUrlRole]
            )
        self._pending_preview_paths = {
            token: path
            for token, path in self._pending_preview_paths.items()
            if str(Path(path).resolve()) != local_path
        }
        self._failed_preview_tokens.difference_update(changed_tokens)

    def fail_preview(self, task_id: str) -> None:
        token = f"pending-preview:{task_id}"
        self._failed_preview_tokens.add(token)
        changed_rows = []
        for row, node in enumerate(self._items):
            changed = False
            if node.preview_url == token:
                node.preview_url = ""
                node.preview_requested = False
                changed = True
            if node.card_preview_url == token:
                node.card_preview_url = ""
                node.card_preview_requested = False
                changed = True
            if changed:
                changed_rows.append(row)
        self._pending_preview_paths.pop(token, None)
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(
                index, index,
                [self.PreviewUrlRole, self.CardPreviewUrlRole],
            )

    def begin_preview_request(self, node_id: str):
        node = self._nodes.get(node_id)
        if (
            not node
            or node.preview_requested
            or node.preview_url
            or not node.preview_source
        ):
            return None
        node.preview_requested = True
        self._preview_request_sequence += 1
        self._preview_request_sources[node_id] = (
            node.preview_source, self._preview_request_sequence,
        )
        return node.node_type, node.preview_source

    def begin_card_preview_request(self, node_id: str):
        node = self._nodes.get(node_id)
        if (
            not node
            or node.card_preview_requested
            or node.card_preview_url
            or not node.preview_source
        ):
            return None
        node.card_preview_requested = True
        self._preview_request_sequence += 1
        self._card_preview_request_sources[node_id] = (
            node.preview_source, self._preview_request_sequence,
        )
        return node.node_type, node.preview_source

    def preview_request_token(self, node_id: str, card: bool = False) -> int:
        requests = (
            self._card_preview_request_sources
            if card else self._preview_request_sources
        )
        request = requests.get(node_id)
        return int(request[1]) if request else 0

    @staticmethod
    def _preview_request_matches(
        requests: dict[str, tuple[object, int]],
        node_id: str,
        source,
        request_token: int | None,
    ) -> bool:
        current = requests.get(node_id)
        return bool(
            current
            and current[0] is source
            and (
                request_token is None
                or current[1] == int(request_token)
            )
        )

    @classmethod
    def prepare_preview(cls, node_type: str, source) -> list:
        if node_type == "sobject":
            return cls._root_preview_candidates(source)
        if node_type == "snapshot":
            return cls._snapshot_preview_candidates(source)
        return []

    @classmethod
    def prepare_card_preview(cls, node_type: str, source) -> list:
        if node_type == "sobject":
            return cls._root_card_preview_candidates(source)
        if node_type == "snapshot":
            return cls._snapshot_card_preview_candidates(source)
        return []

    @staticmethod
    def _preview_source_matches(node: WorkspaceNode, source) -> bool:
        if node.preview_source is source:
            return True
        if source is None or not node.search_key:
            return False
        try:
            return str(source.get_search_key() or "") == node.search_key
        except (AttributeError, KeyError, TypeError):
            return False

    def cancel_preview_request(
        self, node_id: str, source, request_token: int | None = None,
    ) -> None:
        if not self._preview_request_matches(
            self._preview_request_sources,
            node_id,
            source,
            request_token,
        ):
            return
        self._preview_request_sources.pop(node_id, None)
        node = self._nodes.get(node_id)
        if (
            node and self._preview_source_matches(node, source)
            and not node.preview_url
        ):
            node.preview_requested = False

    def cancel_card_preview_request(
        self, node_id: str, source, request_token: int | None = None,
    ) -> None:
        if not self._preview_request_matches(
            self._card_preview_request_sources,
            node_id,
            source,
            request_token,
        ):
            return
        self._card_preview_request_sources.pop(node_id, None)
        node = self._nodes.get(node_id)
        if (
            node and self._preview_source_matches(node, source)
            and not node.card_preview_url
        ):
            node.card_preview_requested = False

    def apply_preview(
        self,
        node_id: str,
        source,
        candidates: list,
        request_token: int | None = None,
    ) -> None:
        node = self._nodes.get(node_id)
        if (
            not self._preview_request_matches(
                self._preview_request_sources,
                node_id,
                source,
                request_token,
            )
            or not node
            or not self._preview_source_matches(node, source)
        ):
            return
        for candidate in candidates or []:
            node.preview_url = self._preview_url(candidate)
            if node.preview_url:
                break
        if not node.preview_url:
            self.cancel_preview_request(node_id, source)
            return
        self._preview_request_sources.pop(node_id, None)
        row = self._row_by_node_id.get(node_id, -1)
        if row < 0:
            return
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [self.PreviewUrlRole])

    def apply_card_preview(
        self,
        node_id: str,
        source,
        candidates: list,
        request_token: int | None = None,
    ) -> None:
        node = self._nodes.get(node_id)
        if (
            not self._preview_request_matches(
                self._card_preview_request_sources,
                node_id,
                source,
                request_token,
            )
            or not node
            or not self._preview_source_matches(node, source)
        ):
            return
        for candidate in candidates or []:
            node.card_preview_url = self._preview_url(candidate)
            if node.card_preview_url:
                break
        if not node.card_preview_url:
            # A worker can finish before a newly appended item's snapshot
            # data exposes a usable derivative. Do not leave the item
            # permanently marked as requested: a pooled GridView delegate
            # must be able to retry when it becomes visible again.
            self.cancel_card_preview_request(node_id, source)
            return
        self._card_preview_request_sources.pop(node_id, None)
        row = self._row_by_node_id.get(node_id, -1)
        if row < 0:
            return
        index = self.index(row, 0)
        self.dataChanged.emit(index, index, [self.CardPreviewUrlRole])

    def request_preview(self, node_id: str) -> None:
        request = self.begin_preview_request(node_id)
        if not request:
            return
        node_type, source = request
        request_token = self.preview_request_token(node_id)
        self.apply_preview(
            node_id,
            source,
            self.prepare_preview(node_type, source),
            request_token,
        )

    def refresh_previews(self) -> list[str]:
        requested = [
            node.node_id for node in self._nodes.values()
            if node.preview_requested or node.card_preview_requested
        ]
        self._pending_preview_paths.clear()
        self._failed_preview_tokens.clear()
        self._preview_request_sources.clear()
        self._card_preview_request_sources.clear()
        changed_rows = []
        for node_id in requested:
            node = self._nodes.get(node_id)
            if not node:
                continue
            node.preview_requested = False
            node.card_preview_requested = False
            node.preview_url = ""
            node.card_preview_url = ""
            node.preview_revealed = False
            row = self._row_by_node_id.get(node_id, -1)
            if row >= 0:
                changed_rows.append(row)
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(
                index,
                index,
                [
                    self.PreviewUrlRole,
                    self.CardPreviewUrlRole,
                    self.PreviewRevealedRole,
                ],
            )
        return requested

    def mark_preview_revealed(self, node_id: str) -> None:
        node = self._nodes.get(node_id)
        if not node or node.preview_revealed:
            return
        node.preview_revealed = True
        row = self._row_by_node_id.get(node_id, -1)
        if row < 0:
            return
        index = self.index(row, 0)
        self.dataChanged.emit(
            index,
            index,
            [self.PreviewRevealedRole],
        )

    @staticmethod
    def _file_exists(file_object) -> bool:
        try:
            return bool(file_object.is_exists())
        except (AttributeError, KeyError, TypeError, OSError):
            return False

    @staticmethod
    def _snapshot_size(value) -> str:
        try:
            size = float(value or 0)
        except (TypeError, ValueError):
            return ""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size <= 1024 or unit == "TB":
                return f"{size:.2f} {unit}"
            size /= 1024
        return ""

    def _file_object_size(self, file_object) -> str:
        try:
            return self._snapshot_size(file_object.get_file_size())
        except (AttributeError, KeyError, TypeError, OSError):
            return ""

    @classmethod
    def _snapshot_preview_candidates(cls, snapshot) -> list:
        try:
            grouped = snapshot.get_files_objects(group_by="type") or {}
        except (AttributeError, KeyError, TypeError):
            return []
        result = []
        for kind in ("icon", "web", "image", "playblast", "main"):
            candidates = grouped.get(kind) or []
            for candidate in candidates:
                try:
                    preview = candidate.get_icon_preview()
                    if preview:
                        candidate = preview
                except (AttributeError, KeyError, TypeError):
                    pass
                if candidate and cls._is_image_file(candidate):
                    result.append(candidate)
        return result

    @classmethod
    def _snapshot_card_preview_candidates(cls, snapshot) -> list:
        """Prefer the larger native web preview used by tile cards."""
        try:
            grouped = snapshot.get_files_objects(group_by="type") or {}
        except (AttributeError, KeyError, TypeError):
            return []
        result = []
        seen = set()
        # TACTIC commonly stores icon and web derivatives on the same File
        # object. Ask that native object for its web preview instead of
        # reconstructing a path or assuming that a separate `web` row exists.
        for kind in ("web", "icon", "image", "playblast", "main"):
            for file_object in grouped.get(kind) or []:
                try:
                    candidate = file_object.get_web_preview()
                except (AttributeError, KeyError, TypeError):
                    candidate = None
                if (
                    candidate and cls._is_image_file(candidate)
                    and id(candidate) not in seen
                ):
                    result.append(candidate)
                    seen.add(id(candidate))
        # Old snapshots may not contain a web derivative. Keep their icon as
        # a final fallback without changing previews used by list/item views.
        for candidate in cls._snapshot_preview_candidates(snapshot):
            if id(candidate) not in seen:
                result.append(candidate)
        return result

    def _snapshot_preview(self, snapshot) -> str:
        for candidate in self._snapshot_preview_candidates(snapshot):
            preview_url = self._preview_url(candidate)
            if preview_url:
                return preview_url
        return ""

    def _snapshot_preview_items(self, snapshot) -> list[dict]:
        """Return preview items in browser display order."""
        try:
            preview_objects = list(snapshot.get_previewable_files_objects() or [])
        except (AttributeError, KeyError, TypeError):
            preview_objects = []
        if not preview_objects:
            try:
                preview_objects = [fo for fo in (snapshot.get_files_objects() or [])
                                   if fo.get_type() == "web"]
            except (AttributeError, KeyError, TypeError):
                preview_objects = []
        result = []
        for file_object in preview_objects:
            candidate = file_object
            try:
                web_object = file_object.get_web_preview()
                if web_object:
                    candidate = web_object
            except (AttributeError, KeyError, TypeError):
                pass
            url = self._preview_url(candidate)
            if not url:
                try:
                    icon = file_object.get_icon_preview()
                    url = self._preview_url(icon)
                except (AttributeError, KeyError, TypeError):
                    pass
            if url:
                try:
                    name = file_object.get_filename_with_ext() or "Preview"
                except (AttributeError, KeyError, TypeError):
                    name = "Preview"
                result.append({"url": url, "title": str(name),
                               "kind": str(file_object.get_type() or "preview")})
        return result

    @staticmethod
    def _snapshot_file_records(snapshot) -> list[dict]:
        records = []
        try:
            grouped = snapshot.get_files_objects(group_by="type") or {}
        except (AttributeError, KeyError, TypeError):
            grouped = {}
        for file_type, files in grouped.items():
            for file_object in files:
                try:
                    name = file_object.get_filename_with_ext() or ""
                except (AttributeError, KeyError, TypeError):
                    name = ""
                try:
                    path = file_object.get_abs_path() or file_object.get_full_abs_path() or ""
                except (AttributeError, KeyError, TypeError):
                    path = ""
                try:
                    size = PresentationMixin._pretty_size(
                        file_object.get_file_size()
                    )
                except (AttributeError, KeyError, TypeError, OSError):
                    size = ""
                try:
                    base_type = file_object.get_base_type() or ""
                except (AttributeError, KeyError, TypeError):
                    base_type = ""
                try:
                    exists = bool(file_object.is_exists())
                except (AttributeError, KeyError, TypeError, OSError):
                    exists = False
                records.append({"type": str(file_type), "name": str(name),
                                "path": str(path), "size": str(size),
                                "baseType": str(base_type), "exists": exists})
        return records

    @staticmethod
    def _snapshot_chips(file_object, context: str = "") -> list[dict]:
        chips = []
        if context:
            chips.append({
                "label": "Context",
                "value": str(context),
                "url": "",
            })
        if not file_object:
            return chips
        try:
            meta = file_object.get_meta_file_object()
        except (AttributeError, KeyError, TypeError):
            meta = None
        if meta:
            getters = (
                ("Range", "get_sequence_frameranges_string", {"brackets": "[]"}),
                ("Frames", "get_sequence_lenght", {}),
                ("Layer", "get_layer", {}),
                ("Tiles", "get_tiles_count", {}),
            )
            for label, getter_name, kwargs in getters:
                try:
                    value = getattr(meta, getter_name)(**kwargs)
                except (AttributeError, KeyError, TypeError):
                    value = None
                if value not in (None, "", 0):
                    chips.append({"label": label, "value": str(value), "url": ""})
        try:
            metadata = file_object.get_metadata() or {}
            maya_version = (metadata.get("app_info") or {}).get("p")
        except (AttributeError, KeyError, TypeError):
            maya_version = None
        if maya_version:
            chips.append({"label": "Maya", "value": str(maya_version), "url": ""})
        return chips

    @staticmethod
    def _snapshot_author(login: str) -> str:
        if not login:
            return ""
        try:
            from thlib.environment import env_inst
            login_object = env_inst.get_all_logins(login)
            if login_object:
                return str(login_object.get_display_name() or login)
        except (AttributeError, KeyError, TypeError):
            pass
        return str(login)

    @staticmethod
    def _repository_title(repository: str) -> str:
        if not repository:
            return ""
        try:
            from thlib.environment import env_tactic
            base_dir = env_tactic.get_base_dir(repository) or {}
            value = base_dir.get("value") or ()
            if len(value) > 1 and value[1]:
                return str(value[1])
        except (AttributeError, KeyError, TypeError):
            pass
        return str(repository)

    @staticmethod
    def _repository_color(repository: str, fallback: str) -> str:
        if not repository:
            return fallback
        try:
            from thlib.environment import env_tactic
            value = (env_tactic.get_base_dir(repository) or {}).get("value") or ()
            color = value[2] if len(value) > 2 else None
            if isinstance(color, str) and color:
                return color if color.startswith("#") else f"#{color}"
            if isinstance(color, (list, tuple)) and len(color) >= 3:
                return "#{:02x}{:02x}{:02x}".format(
                    *[max(0, min(255, int(channel))) for channel in color[:3]]
                )
        except (AttributeError, KeyError, TypeError, ValueError):
            pass
        return fallback

    @classmethod
    def _root_preview_candidates(cls, sobject) -> list:
        result = []
        for process_name in ("icon", "publish", "attachment"):
            process = (sobject.get_all_processes() or {}).get(process_name)
            if not process:
                continue
            for context in (process.get_contexts() or {}).values():
                snapshots = list((context.get_versionless() or {}).values())
                snapshots.extend((context.get_versions() or {}).values())
                for snapshot in snapshots:
                    result.extend(
                        cls._snapshot_preview_candidates(snapshot)
                    )
        return result

    @classmethod
    def _root_card_preview_candidates(cls, sobject) -> list:
        result = []
        for process_name in ("icon", "publish", "attachment"):
            process = (sobject.get_all_processes() or {}).get(process_name)
            if not process:
                continue
            for context in (process.get_contexts() or {}).values():
                snapshots = list((context.get_versionless() or {}).values())
                snapshots.extend((context.get_versions() or {}).values())
                for snapshot in snapshots:
                    result.extend(
                        cls._snapshot_card_preview_candidates(snapshot)
                    )
        return result

    def _root_preview(self, sobject) -> str:
        for candidate in self._root_preview_candidates(sobject):
            preview = self._preview_url(candidate)
            if preview:
                return preview
        return ""

    @staticmethod
    def _progress_items(sobject, stype) -> list[dict]:
        try:
            pipeline = (stype.get_pipeline() or {}).get(sobject.get_pipeline_code())
            progress_processes = pipeline.get_processes_info_by_type("progress") if pipeline else []
        except (AttributeError, KeyError, TypeError):
            return []
        items = []
        for process in progress_processes or []:
            name = process.get("name")
            if not name:
                continue
            approved = sobject.get_progress_count(name, "approved_count") or 0
            total = sobject.get_progress_count(name, "total_count") or 0
            color = stype.get_stype_color(fmt="hex") or "#607d8b"
            process_info = pipeline.get_pipeline_process(name) or {}
            workflow = process_info.get("workflow") or {}
            related_search_type = str(workflow.get("search_type") or "")
            try:
                progress_stype = stype.get_project().get_search_type(
                    related_search_type
                )
                color = progress_stype.get_stype_color(fmt="hex") or color
            except (AttributeError, KeyError, TypeError):
                pass
            items.append({
                "name": str(name),
                "label": f"{approved} / {total}",
                "color": str(color),
                "approved": approved,
                "total": total,
                "searchType": related_search_type,
            })
        return items

    @staticmethod
    def _needs_sync(sobject) -> bool:
        try:
            return bool(sobject.is_snapshots_need_update())
        except (AttributeError, KeyError, TypeError):
            return False

    @staticmethod
    def _watch_state(sobject) -> str:
        try:
            from thlib.environment import env_inst
            project = sobject.get_project()
            project_code = project.get_code() if project else ""
            watch_ui = env_inst.watch_folders.get(project_code)
            watch = watch_ui.get_watch_dict_by_skey(sobject.get_search_key()) if watch_ui else None
            if not watch:
                watch = _watch_folder_record(project, sobject.get_search_key())
            if not watch:
                return "none"
            return "enabled" if watch.get("status") else "disabled"
        except (AttributeError, KeyError, TypeError):
            return "none"
