"""WorkspaceItemModel: records."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, QSettings, Qt, QUrl, Slot

from .results_types import WorkspaceNode


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

    def set_search_key_loading(self, search_key: str, loading: bool) -> None:
        for row, node in enumerate(self._items):
            if node.search_key != search_key or node.loading == loading:
                continue
            node.loading = loading
            model_index = self.index(row, 0)
            self.dataChanged.emit(
                model_index,
                model_index,
                [self.LoadingRole],
            )

    def _replace_visible_items(self, items: list[WorkspaceNode]) -> None:
        """Replace flat tree rows without invalidating incubating delegates."""
        incoming = list(items)
        old_count = len(self._items)
        new_count = len(incoming)
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
        remove_count = old_count - prefix - suffix
        if remove_count:
            self.beginRemoveRows(
                QModelIndex(), prefix, prefix + remove_count - 1
            )
            del self._items[prefix:prefix + remove_count]
            self.endRemoveRows()
        insert_items = incoming[prefix:new_count - suffix]
        if insert_items:
            self.beginInsertRows(
                QModelIndex(), prefix, prefix + len(insert_items) - 1
            )
            self._items[prefix:prefix] = insert_items
            self.endInsertRows()
        changed_roles = list(self.roleNames())
        stable_rows = list(range(prefix)) + list(
            range(new_count - suffix, new_count)
        )
        for row in stable_rows:
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

    def clear(self) -> None:
        self._replace_visible_items([])
        self._roots = []
        self._nodes = {}
        self._row_by_node_id = {}
        self._failed_preview_tokens.clear()

    def replace_sobjects(self, sobjects, stype=None) -> None:
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
            chips = self._build_info_chips(stype, info)
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
                chips=chips,
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
        self._replace_visible_items(records)

    def replace_nodes(self, nodes: list[WorkspaceNode], stype=None) -> None:
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
        self._replace_visible_items(items)

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
        first = len(self._items)
        last = first + len(new_roots) - 1
        self.beginInsertRows(QModelIndex(), first, last)
        self._roots.extend(new_roots)
        self._items.extend(new_roots)
        for node in new_roots:
            self._register_tree(node)
        self.endInsertRows()
        self._rebuild_row_map()
