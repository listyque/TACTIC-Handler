"""WorkspaceItemModel: navigation."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, QSettings, Qt, QUrl, Slot

from .results_types import WorkspaceNode


class NavigationMixin:
    def _flatten(self) -> list[WorkspaceNode]:
        result: list[WorkspaceNode] = []
        def visit(node: WorkspaceNode) -> None:
            result.append(node)
            if node.expanded:
                for child in node.children:
                    visit(child)
        for root in self._roots:
            visit(root)
        return result

    def show_card_level(self, node_id: str = "") -> None:
        if not node_id:
            self._replace_visible_items(list(self._roots))
            return
        node = self._nodes.get(node_id)
        if node and node.loaded:
            self._replace_visible_items(list(node.children))

    def show_tree_rows(self) -> None:
        self._replace_visible_items(self._flatten())

    def _visible_children(self, node: WorkspaceNode) -> list[WorkspaceNode]:
        result: list[WorkspaceNode] = []

        def visit(child: WorkspaceNode) -> None:
            result.append(child)
            if child.expanded:
                for descendant in child.children:
                    visit(descendant)

        for child in node.children:
            visit(child)
        return result

    def load_node(self, node_id: str) -> tuple[str, bool, list[WorkspaceNode]]:
        """Load a node's children without touching Qt model rows.

        This method is safe to run through the existing TACTIC server pool;
        the GUI thread publishes the prepared children afterwards.
        """
        node = self._nodes.get(node_id)
        if not node or not node.has_children or node.loaded:
            return node_id, False, None
        prepared = replace(
            node,
            children=[],
            expanded=False,
            loaded=False,
            loading=False,
        )
        if prepared.node_type == "relation":
            self._load_relation(prepared, register=False)
        elif prepared.node_type == "sobject":
            self._load_root(prepared, register=False)
        elif prepared.node_type == "snapshot":
            self._load_snapshot_versions(prepared, register=False)
        return node_id, prepared.loaded, prepared

    def apply_loaded_node(
        self,
        node_id: str,
        prepared: WorkspaceNode | None,
    ) -> bool:
        node = self._nodes.get(node_id)
        if not node or not prepared or not prepared.loaded:
            return False
        node.children = list(prepared.children)
        node.lazy_versions = list(prepared.lazy_versions)
        node.loaded = True
        node.child_count = prepared.child_count
        node.needs_sync = prepared.needs_sync
        node.watch_state = prepared.watch_state
        for child in node.children:
            self._register_tree(child)
        return True

    @Slot(str)
    def toggle_node(self, node_id: str) -> None:
        node = self._nodes.get(node_id)
        if not node or not node.has_children:
            return
        if not node.loaded:
            return
        row = self._row_by_node_id.get(node_id, -1)
        if row < 0:
            return

        if node.expanded:
            remove_start = row + 1
            remove_end = remove_start
            while (
                remove_end < len(self._items)
                and self._items[remove_end].depth > node.depth
            ):
                remove_end += 1
            node.expanded = False
            node.restore_expanded = False
            if remove_end > remove_start:
                self.beginRemoveRows(
                    QModelIndex(),
                    remove_start,
                    remove_end - 1,
                )
                del self._items[remove_start:remove_end]
                self.endRemoveRows()
        else:
            children = self._visible_children(node)
            node.expanded = True
            node.restore_expanded = True
            if children:
                insert_at = row + 1
                self.beginInsertRows(
                    QModelIndex(),
                    insert_at,
                    insert_at + len(children) - 1,
                )
                self._items[insert_at:insert_at] = children
                self.endInsertRows()

        self._rebuild_row_map()

        model_index = self.index(row, 0)
        self.dataChanged.emit(
            model_index,
            model_index,
            [
                self.ExpandedRole,
                self.ChildCountRole,
                self.PreviewUrlRole,
                self.NeedsSyncRole,
                self.WatchStateRole,
                self.ControlsRole,
            ],
        )

    def source_for(self, node_id: str):
        node = self._nodes.get(node_id)
        return node.source if node else None

    def source_for_search_key(self, search_key: str):
        node = next(
            (
                node for node in self._nodes.values()
                if node.search_key == search_key and node.source
            ),
            None,
        )
        return node.source if node else None

    def preview_url_for_search_key(self, search_key: str) -> str:
        node = next(
            (
                value for value in self._nodes.values()
                if value.node_type == "sobject"
                and value.search_key == search_key
            ),
            None,
        )
        return str(node.preview_url or "") if node else ""

    def node_for(self, node_id: str) -> WorkspaceNode | None:
        return self._nodes.get(node_id)

    @Slot(str, result=int)
    def row_for_node(self, node_id: str) -> int:
        node = self._nodes.get(node_id)
        if not node:
            return -1
        return self._row_by_node_id.get(node_id, -1)

    def snapshot_nodes_for(
        self,
        search_key: str,
        refresh: bool = False,
    ) -> list[WorkspaceNode]:
        root = next(
            (
                candidate for candidate in self._nodes.values()
                if candidate.node_type == "sobject"
                and candidate.search_key == search_key
            ),
            None,
        )
        if not root:
            return []
        if refresh or not root.loaded:
            try:
                root.source.update_snapshots(
                    order_bys=["timestamp desc"]
                )
                processes = root.source.get_all_processes() or {}
            except (AttributeError, KeyError, TypeError):
                processes = {}
            snapshots = []
            for process_name, process_obj in processes.items():
                contexts = self._snapshot_nodes(
                    str(process_name),
                    process_obj,
                    0,
                    root.accent,
                    f"details:{root.node_id}:{process_name}",
                    separate_versions=False,
                )
                for current in contexts:
                    snapshots.append(current)
                    snapshots.extend(current.children)
            return self._deduplicate_siblings(snapshots)
        snapshots = []

        def visit(node: WorkspaceNode) -> None:
            if node.node_type == "snapshot":
                snapshots.append(node)
                for version in node.lazy_versions:
                    snapshots.append(self._make_snapshot_node(
                        version,
                        node.process,
                        node.context,
                        node.depth + 1,
                        node.accent,
                        node.node_id,
                    ))
            for child in node.children:
                visit(child)

        for child in root.children:
            visit(child)
        return snapshots

    def snapshot_nodes_for_source(
        self,
        source,
        search_key: str,
        process: str = "",
        context: str = "",
        refresh: bool = False,
    ) -> tuple[list[WorkspaceNode], list[WorkspaceNode]]:
        """Build a detached Snapshot Browser projection from an sObject."""
        try:
            processes = source.get_all_processes() or {}
        except (AttributeError, KeyError, TypeError):
            processes = {}
        if refresh or not processes or (process and process not in processes):
            try:
                source.update_snapshots(order_bys=["timestamp desc"])
                processes = source.get_all_processes() or {}
            except (AttributeError, KeyError, TypeError):
                processes = {}

        process = str(process or "")
        context = str(context or "")
        if not process:
            process = next(
                (
                    name for name in ("publish", "icon")
                    if processes.get(name)
                ),
                next(iter(processes), ""),
            )

        def nodes_for(process_name: str) -> list[WorkspaceNode]:
            process_object = processes.get(process_name)
            if not process_object:
                return []
            nodes = self._snapshot_nodes(
                process_name,
                process_object,
                0,
                "#607d8b",
                "task-details:{0}:{1}".format(search_key, process_name),
                separate_versions=False,
            )
            result = []
            for node in nodes:
                if node.source:
                    result.append(node)
                result.extend(
                    child for child in node.children if child.source
                )
            return self._deduplicate_siblings(result)

        selected = nodes_for(process)
        if context:
            exact = [
                node for node in selected
                if str(node.context or "") == context
            ]
            if exact:
                selected = exact
        icon_nodes = nodes_for("icon") if process != "icon" else []
        return selected, icon_nodes

    def version_nodes_for(self, node_id: str) -> list[WorkspaceNode]:
        """Build the original resultsVersionsTreeWidget payload.

        This method may touch lazy TACTIC snapshot wrappers and is therefore
        called exclusively from a server worker by ApplicationController.
        """
        node = self._nodes.get(node_id)
        if not node:
            return []
        root = next(
            (
                ancestor for ancestor in self._ancestor_nodes(node)
                if ancestor.node_type == "sobject"
            ),
            node if node.node_type == "sobject" else None,
        )
        if not root or not root.source:
            return []

        process_name = node.process if node.node_type in {"process", "snapshot"} else ""
        context_name = node.context if node.node_type == "snapshot" else ""
        processes = root.source.get_all_processes() or {}
        if not process_name:
            process_name = (
                "publish" if processes.get("publish")
                else "icon" if processes.get("icon")
                else next(iter(processes), "")
            )
        process_obj = processes.get(process_name)
        if not process_obj:
            try:
                process_obj = root.source.get_process(process_name)
            except (AttributeError, KeyError, TypeError):
                process_obj = None
        if not process_obj:
            return []

        contexts = self._snapshot_nodes(
            process_name,
            process_obj,
            0,
            node.accent or root.accent,
            f"versions:{root.node_id}:{process_name}",
            separate_versions=False,
        )
        versions: list[WorkspaceNode] = []
        for current in contexts:
            if context_name and current.context != context_name:
                continue
            candidates = current.children or [current]
            for candidate in candidates:
                versions.append(replace(
                    candidate,
                    node_id=f"versions:{candidate.node_id}",
                    depth=0,
                    parent_id="",
                    expanded=False,
                    has_children=False,
                    children=[],
                    restore_state={},
                    restore_expanded=False,
                ))
        return self._deduplicate_siblings(versions)

    def node_type_for(self, node_id: str) -> str:
        node = self._nodes.get(node_id)
        return node.node_type if node else ""

    def search_key_for(self, node_id: str) -> str:
        node = self._nodes.get(node_id)
        return node.search_key if node else ""
