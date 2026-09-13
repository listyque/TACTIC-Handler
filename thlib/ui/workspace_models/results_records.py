"""WorkspaceItemModel: records."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from difflib import SequenceMatcher
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .results_types import WorkspaceNode, WorkspaceProjection


class RecordsMixin:
    def set_process_ignore(self, value: dict | None) -> None:
        self._process_ignore = dict(value or {})

    def update_description(self, search_key: str, value: str) -> None:
        node = next((
            item for item in self._nodes.values()
            if item.search_key == search_key
        ), None)
        if not node:
            return
        description = str(value or "")
        node.subtitle = description
        if node.source is not None:
            try:
                info = (
                    node.source.get_snapshot()
                    if node.node_type == "snapshot"
                    else node.source.get_info()
                )
                if info is not None:
                    info["description"] = description
                    if node.node_type == "sobject":
                        node.subtitle = " · ".join(
                            str(info[key])
                            for key in (
                                "description", "pipeline_code", "category"
                            )
                            if info.get(key)
                        )
            except (AttributeError, KeyError, TypeError):
                pass
        row = self._row_by_node_id.get(node.node_id, -1)
        if row >= 0:
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [self.SubtitleRole])

    @Slot(str, str)
    def update_watch_state(self, search_key: str, state: str) -> None:
        """Update visible copies of an sObject after Watch Folder changes."""
        normalized = state if state in {"none", "enabled", "disabled"} else "none"
        for node in self._nodes.values():
            if node.node_type != "sobject" or node.search_key != search_key:
                continue
            if node.watch_state == normalized:
                continue
            node.watch_state = normalized
            node.controls_signature = ()
            node.controls_cache = []
            row = self._row_by_node_id.get(node.node_id, -1)
            if row < 0:
                continue
            index = self.index(row, 0)
            self.dataChanged.emit(
                index,
                index,
                [self.WatchStateRole, self.ControlsRole],
            )

    @staticmethod
    def _normalized_search_key(value: str) -> str:
        search_key = str(value or "").strip()
        if search_key and not search_key.startswith("skey://"):
            search_key = "skey://" + search_key
        return search_key

    def set_knowledge_index(self, values) -> None:
        normalized = {
            self._normalized_search_key(search_key): tuple(
                str(identity or "")
                for identity in identities or []
                if str(identity or "")
            )
            for search_key, identities in dict(values or {}).items()
            if self._normalized_search_key(search_key)
        }
        if normalized == self._knowledge_index:
            return
        previous = self._knowledge_index
        self._knowledge_index = normalized
        changed_keys = {
            search_key
            for search_key in set(previous).union(normalized)
            if previous.get(search_key) != normalized.get(search_key)
        }
        changed_rows = []
        for row, node in enumerate(self._items):
            if node.node_type != "sobject":
                continue
            if self._normalized_search_key(node.search_key) not in changed_keys:
                continue
            node.controls_signature = ()
            node.controls_cache = []
            changed_rows.append(row)
        for row in changed_rows:
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [self.ControlsRole])

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.SearchKeyRole: b"searchKey",
            self.CodeRole: b"itemCode",
            self.TitleRole: b"title",
            self.SubtitleRole: b"subtitle",
            self.StatusRole: b"status",
            self.AccentRole: b"accent",
            self.CommentsRole: b"comments",
            self.TasksRole: b"tasks",
            self.ValuesRole: b"values",
            self.NodeIdRole: b"nodeId",
            self.NodeTypeRole: b"nodeType",
            self.DepthRole: b"depth",
            self.ExpandedRole: b"expanded",
            self.HasChildrenRole: b"hasChildren",
            self.ContextRole: b"context",
            self.VersionRole: b"version",
            self.FilePathRole: b"filePath",
            self.FileSizeRole: b"fileSize",
            self.ChipsRole: b"infoChips",
            self.ParentIdRole: b"parentId",
            self.ProcessRole: b"process",
            self.AuthorRole: b"author",
            self.TimestampRole: b"timestamp",
            self.TimestampPrettyRole: b"timestampPretty",
            self.TimestampSimpleRole: b"timestampSimple",
            self.RevisionRole: b"revision",
            self.RepositoryRole: b"repository",
            self.PreviewUrlRole: b"previewUrl",
            self.RelationshipRole: b"relationship",
            self.WatchStateRole: b"watchState",
            self.FileExistsRole: b"fileExists",
            self.IsLatestRole: b"isLatest",
            self.IsVersionlessRole: b"isVersionless",
            self.IsMultipleRole: b"isMultiple",
            self.NeedsSyncRole: b"needsSync",
            self.ChildCountRole: b"childCount",
            self.ControlsRole: b"itemControls",
            self.ProgressRole: b"progressItems",
            self.LoadingRole: b"nodeLoading",
            self.RepositoryColorRole: b"repositoryColor",
            self.PreviewRevealedRole: b"previewRevealed",
            self.PreviewRequestedRole: b"previewRequested",
            self.CardPreviewUrlRole: b"cardPreviewUrl",
            self.CardPreviewRequestedRole: b"cardPreviewRequested",
            self.CommentsUpdatedRole: b"commentsUpdated",
            self.TasksUpdatedRole: b"tasksUpdated",
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        if role == self.PreviewUrlRole:
            return (
                "" if item.preview_url in self._failed_preview_tokens
                else item.preview_url
            )
        if role == self.CardPreviewUrlRole:
            return (
                "" if item.card_preview_url in self._failed_preview_tokens
                else item.card_preview_url
            )
        if role == self.ControlsRole:
            return self._controls_for(item)
        attribute = self._role_attributes.get(role)
        return getattr(item, attribute) if attribute else None

    def _rebuild_row_map(self) -> None:
        self._row_by_node_id = {
            node.node_id: row for row, node in enumerate(self._items)
        }

    def set_node_loading(self, node_id: str, loading: bool) -> None:
        node = self._nodes.get(node_id)
        if not node or node.loading == loading:
            return
        node.loading = loading
        row = self._row_by_node_id.get(node_id, -1)
        if row < 0:
            return
        model_index = self.index(row, 0)
        self.dataChanged.emit(
            model_index,
            model_index,
            [self.LoadingRole],
        )

    def set_search_key_loading(
        self,
        search_key: str,
        loading: bool,
        notify: bool = True,
    ) -> None:
        for row, node in enumerate(self._items):
            if node.search_key != search_key or node.loading == loading:
                continue
            node.loading = loading
            if not notify:
                continue
            model_index = self.index(row, 0)
            self.dataChanged.emit(
                model_index,
                model_index,
                [self.LoadingRole],
            )

    @staticmethod
    def _plain_search_type(search_key: str) -> str:
        value = str(search_key or "")
        if value.startswith("skey://"):
            value = value[7:]
        return value.split("?", 1)[0]

    def _matching_sobject_nodes(
        self,
        search_key: str = "",
        search_type: str = "",
        search_code: str = "",
    ) -> list[WorkspaceNode]:
        plain_type = self._plain_search_type(search_type)
        exact_key = str(search_key or "")
        code = str(search_code or "")
        matches = []
        for node in self._nodes.values():
            if node.node_type != "sobject":
                continue
            if exact_key and node.search_key == exact_key:
                matches.append(node)
                continue
            if code and node.code != code:
                continue
            if plain_type and self._plain_search_type(node.search_key) != plain_type:
                continue
            if code:
                matches.append(node)
        return matches

    @staticmethod
    def _walk_process_nodes(node: WorkspaceNode):
        for child in node.children:
            if child.node_type == "process":
                yield child
            yield from RecordsMixin._walk_process_nodes(child)

    def _emit_node_roles(
        self,
        node: WorkspaceNode,
        roles: list[int],
    ) -> None:
        row = self._row_by_node_id.get(node.node_id, -1)
        if row < 0:
            return
        model_index = self.index(row, 0)
        self.dataChanged.emit(model_index, model_index, roles)

    @staticmethod
    def _process_counts(source, panel: str) -> dict[str, int]:
        if source is None:
            return {}
        getter_name = "get_notes_count" if panel == "notes" else "get_tasks_count"
        try:
            values = dict(getattr(source, getter_name)() or {})
        except (AttributeError, TypeError, ValueError):
            return {}
        result = {}
        for process, count in values.items():
            process_name = str(process or "")
            if not process_name or process_name.startswith("__"):
                continue
            try:
                result[process_name] = int(count or 0)
            except (TypeError, ValueError):
                result[process_name] = 0
        return result

    def _set_process_count(
        self,
        node: WorkspaceNode,
        panel: str,
        process: str,
        count: int,
    ) -> None:
        source = node.source
        setter_name = "set_notes_count" if panel == "notes" else "set_tasks_count"
        try:
            getattr(source, setter_name)(process, int(count))
        except (AttributeError, TypeError, ValueError):
            pass
        counts = self._process_counts(source, panel)
        if panel == "notes":
            node.comments = sum(counts.values())
            count_role = self.CommentsRole
        else:
            total = sum(counts.values())
            try:
                current_total = int(
                    (source.get_tasks_count() or {}).get("__total__") or 0
                )
                source.set_tasks_count("__total__", max(current_total, total))
                total = max(current_total, total)
            except (AttributeError, TypeError, ValueError):
                pass
            node.tasks = total
            count_role = self.TasksRole
        self._emit_node_roles(node, [count_role])
        for process_node in self._walk_process_nodes(node):
            if process_node.process != process:
                continue
            if panel == "notes":
                process_node.comments = int(count)
            else:
                process_node.tasks = int(count)
            self._emit_node_roles(process_node, [count_role])

    def _remember_activity_event(self, event_key: str) -> bool:
        if not event_key or event_key in self._seen_activity_events:
            return False
        self._seen_activity_events.add(event_key)
        self._seen_activity_event_order.append(event_key)
        if len(self._seen_activity_event_order) > 4096:
            expired = self._seen_activity_event_order[:1024]
            del self._seen_activity_event_order[:1024]
            self._seen_activity_events.difference_update(expired)
        return True

    @Slot(object)
    def apply_server_batch(self, batch) -> None:
        """Mark live task/note activity without persisting read state."""
        batch = dict(batch or {})
        if batch.get("initialActivity"):
            return
        for raw_event in batch.get("activity") or ():
            event = dict(raw_event or {})
            kind = str(event.get("__kind__") or "")
            panel = "notes" if kind == "note" else "tasks" if kind == "task" else ""
            if not panel:
                continue
            process = str(event.get("process") or "publish")
            search_type = str(event.get("search_type") or "")
            search_code = str(event.get("search_code") or "")
            if not search_code:
                continue
            event_key = "|".join((
                kind,
                str(event.get("code") or ""),
                str(
                    event.get("__event_timestamp__")
                    or event.get("timestamp") or ""
                ),
            ))
            if not self._remember_activity_event(event_key):
                continue
            for node in self._matching_sobject_nodes(
                    search_type=search_type, search_code=search_code):
                updated_processes = (
                    node.updated_comment_processes
                    if panel == "notes" else node.updated_task_processes
                )
                updated_processes.add(process)
                if panel == "notes":
                    node.comments_updated = True
                    updated_role = self.CommentsUpdatedRole
                else:
                    node.tasks_updated = True
                    updated_role = self.TasksUpdatedRole
                counts = self._process_counts(node.source, panel)
                current_count = int(counts.get(process) or 0)
                # Activity rows are change notifications, not authoritative
                # count deltas: edits can emit the same kind of event as new
                # records. Establish process presence here; opening the panel
                # refreshes the exact native count.
                self._set_process_count(
                    node,
                    panel,
                    process,
                    max(1, current_count),
                )
                self._emit_node_roles(node, [updated_role])
                for process_node in self._walk_process_nodes(node):
                    if process_node.process != process:
                        continue
                    if panel == "notes":
                        process_node.comments_updated = True
                    else:
                        process_node.tasks_updated = True
                    self._emit_node_roles(process_node, [updated_role])

    @Slot(str, str, int, object)
    def update_note_count(
        self,
        search_key: str,
        process: str,
        count: int,
        _note_codes=None,
    ) -> None:
        for node in self._matching_sobject_nodes(search_key=search_key):
            self._set_process_count(node, "notes", process, int(count or 0))

    @Slot(str, str, str)
    def mark_process_seen(
        self,
        node_id: str,
        panel: str,
        process: str,
    ) -> None:
        if panel not in {"tasks", "notes"}:
            return
        node = self._nodes.get(str(node_id or ""))
        visited = set()
        while node and node.node_type != "sobject" and node.node_id not in visited:
            visited.add(node.node_id)
            node = self._nodes.get(node.parent_id)
        if node is None or node.node_type != "sobject":
            return
        updated_processes = (
            node.updated_comment_processes
            if panel == "notes" else node.updated_task_processes
        )
        updated_processes.discard(str(process or "publish"))
        if panel == "notes":
            node.comments_updated = bool(updated_processes)
            updated_role = self.CommentsUpdatedRole
        else:
            node.tasks_updated = bool(updated_processes)
            updated_role = self.TasksUpdatedRole
        self._emit_node_roles(node, [updated_role])
        for process_node in self._walk_process_nodes(node):
            if process_node.process != process:
                continue
            if panel == "notes":
                process_node.comments_updated = False
            else:
                process_node.tasks_updated = False
            self._emit_node_roles(process_node, [updated_role])

    def _replace_visible_items(
        self,
        items: list[WorkspaceNode],
        preserve_slots: bool = False,
        preserve_item_state: bool = True,
        ready_row_map: dict[str, int] | None = None,
        reset_preview_node_ids: set[str] | None = None,
    ) -> None:
        """Replace flat tree rows without invalidating incubating delegates."""
        self._projection_revision += 1
        incoming = list(items)
        reset_preview_node_ids = set(reset_preview_node_ids or ())
        if preserve_item_state:
            previous_by_id = {node.node_id: node for node in self._items}
            for node in incoming:
                previous = previous_by_id.get(node.node_id)
                reset_preview = node.node_id in reset_preview_node_ids
                if reset_preview:
                    self._preview_request_sources.pop(node.node_id, None)
                    self._card_preview_request_sources.pop(node.node_id, None)
                    previous_urls = (
                        (previous.preview_url, previous.card_preview_url)
                        if previous is not None else ()
                    )
                    for preview_url in previous_urls:
                        self._pending_preview_paths.pop(preview_url, None)
                        self._failed_preview_tokens.discard(preview_url)
                    node.preview_url = ""
                    node.card_preview_url = ""
                    node.preview_requested = False
                    node.card_preview_requested = False
                    node.preview_revealed = False
                if (
                    previous is None
                    or previous is node
                    or previous.node_type != node.node_type
                    or not node.search_key
                    or previous.search_key != node.search_key
                ):
                    continue
                # Quick filters and result refreshes may rebuild the Python
                # wrapper for an sObject while the QML delegate for its stable
                # node id stays alive. Keep completed and in-flight preview
                # state attached to that semantic row.
                if not reset_preview:
                    node.preview_url = previous.preview_url
                    node.card_preview_url = previous.card_preview_url
                    node.preview_requested = previous.preview_requested
                    node.card_preview_requested = previous.card_preview_requested
                    node.preview_revealed = previous.preview_revealed
                node.updated_comment_processes = set(
                    previous.updated_comment_processes
                )
                node.updated_task_processes = set(
                    previous.updated_task_processes
                )
                node.comments_updated = bool(node.updated_comment_processes)
                node.tasks_updated = bool(node.updated_task_processes)
        old_count = len(self._items)
        new_count = len(incoming)
        if preserve_slots:
            common_count = min(old_count, new_count)
            if common_count:
                self._items[:common_count] = incoming[:common_count]
            if old_count > new_count:
                self.beginRemoveRows(
                    QModelIndex(), new_count, old_count - 1
                )
                del self._items[new_count:]
                self.endRemoveRows()
            elif new_count > old_count:
                self.beginInsertRows(
                    QModelIndex(), old_count, new_count - 1
                )
                self._items.extend(incoming[old_count:])
                self.endInsertRows()
            if ready_row_map is None:
                self._rebuild_row_map()
            else:
                self._row_by_node_id = dict(ready_row_map)
            if common_count:
                self.dataChanged.emit(
                    self.index(0, 0),
                    self.index(common_count - 1, 0),
                    list(self.roleNames()),
                )
            return
        prefix = 0
        while (
            prefix < old_count
            and prefix < new_count
            and self._items[prefix].node_id == incoming[prefix].node_id
        ):
            prefix += 1
        suffix = 0
        while (
            suffix < old_count - prefix
            and suffix < new_count - prefix
            and self._items[old_count - suffix - 1].node_id
                == incoming[new_count - suffix - 1].node_id
        ):
            suffix += 1
        # A fetched page can sort between existing rows. Replacing the entire
        # changed middle would destroy the viewport's anchor and its delegates.
        # Match stable identities there, as RecordListModel does, and insert
        # only the new ranges. Reverse edits keep the old indices valid.
        old_middle = self._items[prefix:old_count - suffix]
        new_middle = incoming[prefix:new_count - suffix]
        edits = SequenceMatcher(
            None,
            [node.node_id for node in old_middle],
            [node.node_id for node in new_middle],
            autojunk=False,
        ).get_opcodes()
        for operation, start, end, new_start, new_end in reversed(edits):
            if operation == "equal":
                continue
            first = prefix + start
            if end > start:
                self.beginRemoveRows(
                    QModelIndex(), first, prefix + end - 1,
                )
                del self._items[first:prefix + end]
                self.endRemoveRows()
            if new_end > new_start:
                self.beginInsertRows(
                    QModelIndex(), first, first + new_end - new_start - 1,
                )
                self._items[first:first] = new_middle[new_start:new_end]
                self.endInsertRows()
        changed_roles = list(self.roleNames())
        for row in range(new_count):
            if self._items[row] is incoming[row]:
                continue
            self._items[row] = incoming[row]
            model_index = self.index(row, 0)
            self.dataChanged.emit(
                model_index,
                model_index,
                changed_roles,
            )
        self._rebuild_row_map()

    def capture_projection(self) -> WorkspaceProjection:
        """Retain the already organized rows for an instant tab restore."""
        return WorkspaceProjection(
            roots=list(self._roots),
            root_groups=list(self._root_groups),
            items=list(self._items),
            nodes=dict(self._nodes),
            row_by_node_id=dict(self._row_by_node_id),
            stype=self._stype,
            owner_model=self,
            owner_revision=self._projection_revision,
        )

    def restore_projection(self, projection: WorkspaceProjection) -> bool:
        """Publish a cached tab without rebuilding its result tree."""
        if not isinstance(projection, WorkspaceProjection):
            return False
        if (
            projection.owner_model is self
            and projection.owner_revision == self._projection_revision
        ):
            return True
        self._stype = projection.stype
        self._roots = list(projection.roots)
        self._root_groups = list(projection.root_groups)
        self._nodes = dict(projection.nodes)
        self._replace_visible_items(
            projection.items,
            preserve_slots=True,
            preserve_item_state=False,
            ready_row_map=projection.row_by_node_id,
        )
        return True

    def clear(self) -> None:
        self._replace_visible_items([])
        self._roots = []
        self._root_groups = []
        self._nodes = {}
        self._row_by_node_id = {}
        self._failed_preview_tokens.clear()
        self._preview_request_sources.clear()
        self._card_preview_request_sources.clear()
        self._seen_activity_events.clear()
        self._seen_activity_event_order.clear()

    def replace_sobjects(
        self,
        sobjects,
        stype=None,
        preserve_slots: bool = False,
    ) -> None:
        """Project SObject values into roles suitable for QML."""
        self._stype = stype
        accent = "#607d8b"
        if stype:
            try:
                accent = stype.get_stype_color(fmt="hex") or accent
            except (AttributeError, KeyError, TypeError):
                pass
        records: list[WorkspaceNode] = []
        seen_sobjects: set[str] = set()
        for sobject in sobjects:
            info = dict(sobject.get_info() or {})
            code = str(info.get("code") or info.get("id") or "")
            search_key = str(sobject.get_search_key() or code)
            if search_key in seen_sobjects:
                continue
            seen_sobjects.add(search_key)
            notes = sobject.get_notes_count() or {}
            tasks = sobject.get_tasks_count() or {}
            values = {
                str(key): value
                for key, value in info.items()
                if not str(key).startswith("__")
                and isinstance(value, (str, int, float, bool, type(None)))
            }
            subtitle = " · ".join(
                str(info[key])
                for key in ("description", "pipeline_code", "category")
                if info.get(key)
            )
            info_items = self._build_info_items(stype, info)
            records.append(WorkspaceNode(
                node_id=search_key,
                node_type="sobject",
                search_key=str(sobject.get_search_key() or ""),
                code=code,
                title=str(sobject.get_title() or code),
                subtitle=subtitle,
                status=str(info.get("status") or info.get("state") or ""),
                accent=accent,
                comments=sum(int(value or 0) for value in notes.values()),
                tasks=int(tasks.get("__total__") or 0),
                values=values,
                chips=info_items,
                source=sobject,
                has_children=True,
                needs_sync=self._needs_sync(sobject),
                watch_state=self._watch_state(sobject),
                preview_source=sobject,
                progress_items=self._progress_items(sobject, stype),
            ))
        self._roots = records
        self._nodes = {item.node_id: item for item in records}
        self._failed_preview_tokens.intersection_update(
            url for item in records
            for url in (item.preview_url, item.card_preview_url)
        )
        self._rebuild_organized_rows(preserve_slots=preserve_slots)

    def replace_nodes(
        self,
        nodes: list[WorkspaceNode],
        stype=None,
        preserve_slots: bool = False,
    ) -> None:
        self._stype = stype
        self._roots = self._deduplicate_siblings(list(nodes))
        self._nodes = {}
        for node in self._roots:
            self._register_tree(node)
        items = self._flatten()
        self._failed_preview_tokens.intersection_update(
            url for item in items
            for url in (item.preview_url, item.card_preview_url)
        )
        self._rebuild_organized_rows(preserve_slots=preserve_slots)

    def append_sobjects(self, sobjects, stype=None) -> None:
        known = {node.search_key for node in self._roots}
        incoming = [sobject for sobject in sobjects if sobject.get_search_key() not in known]
        if not incoming:
            return
        incoming_model = type(self)()
        incoming_model.replace_sobjects(incoming, stype or self._stype)
        new_roots = incoming_model._roots
        if not new_roots:
            return
        self._roots.extend(new_roots)
        for node in new_roots:
            self._register_tree(node)
        self._rebuild_organized_rows()
