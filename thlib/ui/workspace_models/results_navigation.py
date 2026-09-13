"""WorkspaceItemModel: navigation."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .results_types import WorkspaceNode


class NavigationMixin:
    def _flatten(self) -> list[WorkspaceNode]:
        organized = self.organized_flatten()
        if organized is not None:
            return organized
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

    def show_table_rows(self) -> None:
        organized = self.organized_flatten()
        rows = organized if organized is not None else self._roots
        self._replace_visible_items([
            node for node in rows if node.node_type == "sobject"
        ])

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
        node.has_children = prepared.has_children
        node.needs_sync = prepared.needs_sync
        node.watch_state = prepared.watch_state
        for child in node.children:
            self._register_tree(child)
        row = self._row_by_node_id.get(node_id, -1)
        if row >= 0:
            model_index = self.index(row, 0)
            self.dataChanged.emit(
                model_index,
                model_index,
                [
                    self.HasChildrenRole,
                    self.ChildCountRole,
                    self.ControlsRole,
                ],
            )
        return True

    @Slot(str)
    def toggle_node(self, node_id: str) -> None:
        node = self._nodes.get(node_id)
        if not node or not node.has_children:
            return
        if not node.loaded:
            return
        if node.node_type == "group":
            node.expanded = not node.expanded
            node.restore_expanded = node.expanded
            self._replace_visible_items(self._flatten())
            row = self._row_by_node_id.get(node_id, -1)
            if row >= 0:
                model_index = self.index(row, 0)
                self.dataChanged.emit(
                    model_index, model_index,
                    [self.ExpandedRole, self.ChildCountRole],
                )
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

    @Slot(str, result=int)
    def descendant_end_row(self, node_id: str) -> int:
        """Return the last currently visible row owned by ``node_id``."""
        row = self._row_by_node_id.get(node_id, -1)
        node = self._nodes.get(node_id)
        if row < 0 or node is None:
            return -1
        end_row = row
        while (
            end_row + 1 < len(self._items)
            and self._items[end_row + 1].depth > node.depth
        ):
            end_row += 1
        return end_row

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

    def has_loaded_sobject(
        self,
        search_key: str,
        visible_only: bool = False,
    ) -> bool:
        """Return whether this retained tree can refresh ``search_key``."""
        return any(
            node.node_type == "sobject"
            and node.search_key == search_key
            and node.loaded
            and node.source is not None
            and (
                not visible_only
                or self._row_by_node_id.get(node.node_id, -1) >= 0
            )
            for node in self._nodes.values()
        )

    @staticmethod
    def _snapshot_context_matches(
        candidate: str,
        requested: str,
        process: str,
    ) -> bool:
        candidate = str(candidate or "")
        requested = str(requested or "")
        process = str(process or "")
        if requested:
            return candidate == requested
        return candidate == process

    def _prepare_refreshed_snapshot_nodes(
        self,
        process_object,
        old_nodes: list[WorkspaceNode],
        process: str,
        context: str,
        snapshot_code: str,
        depth: int,
        accent: str,
        parent_id: str,
    ) -> tuple[list[WorkspaceNode], str]:
        expanded_contexts = {
            str(node.context or "")
            for node in old_nodes
            if node.node_type == "snapshot" and node.expanded
        }
        refreshed = self._snapshot_nodes(
            process,
            process_object,
            depth,
            accent,
            parent_id,
            separate_versions=True,
        )
        reveal_node_id = ""
        fallback_node_id = ""
        for node in refreshed:
            target_context = self._snapshot_context_matches(
                node.context, context, process,
            )
            should_expand = (
                str(node.context or "") in expanded_contexts
                or target_context
            )
            if should_expand and node.has_children and not node.loaded:
                self._load_snapshot_versions(node, register=False)
            node.expanded = bool(should_expand and node.children)
            node.restore_expanded = node.expanded
            if not target_context:
                continue
            fallback_node_id = node.node_id
            if str(node.code or "") == snapshot_code:
                reveal_node_id = node.node_id
            if snapshot_code:
                exact = next((
                    child for child in node.children
                    if str(child.code or "") == snapshot_code
                ), None)
                if exact is not None:
                    reveal_node_id = exact.node_id
        return refreshed, reveal_node_id or fallback_node_id

    def prepare_snapshot_branch_refresh(
        self,
        search_key: str,
        process: str,
        context: str = "",
        snapshot_code: str = "",
        root_node_id: str = "",
        update_versionless: bool = False,
    ) -> tuple[str, dict]:
        """Prepare fresh snapshot branches without mutating Qt model rows."""
        process = str(process or "publish")
        refreshes = []
        for root in self._matching_sobject_nodes(search_key=search_key):
            if (
                (root_node_id and root.node_id != root_node_id)
                or not root.loaded
                or root.source is None
            ):
                continue
            try:
                root.source.update_snapshots(
                    order_bys=["timestamp desc"], force=True,
                )
                processes = root.source.get_all_processes() or {}
            except (AttributeError, KeyError, TypeError):
                continue
            process_object = processes.get(process)
            if process_object is None:
                try:
                    process_object = root.source.get_process(process)
                except (AttributeError, KeyError, TypeError):
                    process_object = None
            if process_object is None:
                continue

            direct_nodes = None
            new_process_nodes = []
            reveal_node_id = ""
            if process == "publish":
                old_direct = [
                    child for child in root.children
                    if child.node_type == "snapshot"
                    and child.process == "publish"
                ]
                direct_nodes, reveal_node_id = (
                    self._prepare_refreshed_snapshot_nodes(
                        process_object,
                        old_direct,
                        process,
                        context,
                        snapshot_code,
                        root.depth + 1,
                        root.accent,
                        root.node_id,
                    )
                )

            process_branches = []
            for process_node in self._walk_process_nodes(root):
                if str(process_node.process or "") != process:
                    continue
                old_snapshots = [
                    child for child in process_node.children
                    if child.node_type == "snapshot"
                ]
                snapshots, branch_reveal = (
                    self._prepare_refreshed_snapshot_nodes(
                        process_object,
                        old_snapshots,
                        process,
                        context,
                        snapshot_code,
                        process_node.depth + 1,
                        process_node.accent,
                        process_node.node_id,
                    )
                )
                process_branches.append({
                    "nodeId": process_node.node_id,
                    "processObject": process_object,
                    "snapshots": snapshots,
                })
                if not reveal_node_id and branch_reveal:
                    reveal_node_id = branch_reveal

            if process == "attachment" and not process_branches:
                try:
                    pipeline_code = str(
                        root.source.get_pipeline_code() or ""
                    )
                except (AttributeError, KeyError, TypeError):
                    pipeline_code = ""
                if not self._process_is_hidden(process, pipeline_code):
                    process_node_id = f"{root.node_id}:process:{process}"
                    snapshots, branch_reveal = (
                        self._prepare_refreshed_snapshot_nodes(
                            process_object,
                            [],
                            process,
                            context,
                            snapshot_code,
                            root.depth + 2,
                            root.accent,
                            process_node_id,
                        )
                    )
                    if snapshots:
                        new_process_nodes.append(self._make_process_node(
                            root,
                            process,
                            process_object,
                            {"type": "manual", "name": process},
                            process.replace("_", " ").title(),
                            root.accent,
                            root.depth + 1,
                            root.node_id,
                            snapshots,
                            expanded=True,
                        ))
                        if not reveal_node_id and branch_reveal:
                            reveal_node_id = branch_reveal

            reset_preview_node_ids = []
            refreshed_snapshot_branches = (
                ([direct_nodes] if direct_nodes is not None else [])
                + [
                    branch.get("snapshots") or []
                    for branch in process_branches
                ]
                + [
                    process_node.children
                    for process_node in new_process_nodes
                ]
            )
            if update_versionless:
                for branch_nodes in refreshed_snapshot_branches:
                    reset_preview_node_ids.extend(
                        node.node_id
                        for node in branch_nodes
                        if (
                            node.is_versionless
                            and self._snapshot_context_matches(
                                node.context, context, process,
                            )
                        )
                    )
            if process in {"publish", "icon", "attachment"}:
                reset_preview_node_ids.append(root.node_id)

            refreshes.append({
                "rootId": root.node_id,
                "directSnapshots": direct_nodes,
                "newProcessNodes": new_process_nodes,
                "processBranches": process_branches,
                "revealNodeId": reveal_node_id,
                "resetPreviewNodeIds": reset_preview_node_ids,
            })
        return search_key, {"roots": refreshes}

    def _unregister_snapshot_tree(self, node: WorkspaceNode) -> None:
        for child in node.children:
            self._unregister_snapshot_tree(child)
        self._nodes.pop(node.node_id, None)

    def apply_snapshot_branch_refresh(self, refresh: dict) -> str:
        """Publish prepared snapshot branches and return the row to reveal."""
        reveal_node_id = ""
        changed = False
        changed_node_ids: set[str] = set()
        reset_preview_node_ids: set[str] = set()
        for root_refresh in (refresh or {}).get("roots") or []:
            root = self._nodes.get(str(root_refresh.get("rootId") or ""))
            if root is None or root.node_type != "sobject":
                continue
            reset_preview_node_ids.update(
                str(node_id)
                for node_id in root_refresh.get("resetPreviewNodeIds") or []
                if node_id
            )

            direct_nodes = root_refresh.get("directSnapshots")
            if direct_nodes is not None:
                old_direct = [
                    child for child in root.children
                    if child.node_type == "snapshot"
                    and child.process == "publish"
                ]
                for child in old_direct:
                    self._unregister_snapshot_tree(child)
                remaining = [
                    child for child in root.children
                    if child not in old_direct
                ]
                root.children = list(reversed(direct_nodes)) + remaining
                for child in direct_nodes:
                    self._register_tree(child)
                changed = True
                changed_node_ids.add(root.node_id)

            for process_node in root_refresh.get("newProcessNodes") or []:
                if self._nodes.get(process_node.node_id) is not None:
                    continue
                root.children.append(process_node)
                self._register_tree(process_node)
                changed = True
                changed_node_ids.update({root.node_id, process_node.node_id})

            for branch in root_refresh.get("processBranches") or []:
                process_node = self._nodes.get(
                    str(branch.get("nodeId") or "")
                )
                if process_node is None or process_node.node_type != "process":
                    continue
                parent = self._nodes.get(process_node.parent_id)
                if parent is None:
                    continue
                old_snapshots = [
                    child for child in process_node.children
                    if child.node_type == "snapshot"
                ]
                for child in old_snapshots:
                    self._unregister_snapshot_tree(child)
                retained = [
                    child for child in process_node.children
                    if child not in old_snapshots
                ]
                snapshots = list(branch.get("snapshots") or [])
                process_node = replace(
                    process_node,
                    children=retained + snapshots,
                    source=branch.get("processObject"),
                    child_count=len(retained) + len(snapshots),
                    has_children=bool(retained or snapshots),
                    expanded=True,
                    restore_expanded=True,
                )
                parent.children = [
                    process_node
                    if child.node_id == process_node.node_id else child
                    for child in parent.children
                ]
                self._nodes[process_node.node_id] = process_node
                for child in snapshots:
                    self._register_tree(child)
                ancestor = parent
                while ancestor is not None and ancestor is not root:
                    ancestor.expanded = True
                    ancestor.restore_expanded = True
                    changed_node_ids.add(ancestor.node_id)
                    ancestor = self._nodes.get(ancestor.parent_id)
                changed = True

            root.expanded = True
            root.restore_expanded = True
            root.child_count = len(root.children)
            root.has_children = bool(root.children)
            changed_node_ids.add(root.node_id)
            candidate = str(root_refresh.get("revealNodeId") or "")
            if candidate:
                reveal_node_id = candidate

        if not changed:
            return ""
        self._replace_visible_items(
            self._flatten(),
            reset_preview_node_ids=reset_preview_node_ids,
        )
        roles = [
            self.ExpandedRole,
            self.HasChildrenRole,
            self.ChildCountRole,
            self.ControlsRole,
            self.PreviewUrlRole,
            self.PreviewRequestedRole,
            self.CardPreviewUrlRole,
            self.CardPreviewRequestedRole,
            self.PreviewRevealedRole,
        ]
        for node_id in changed_node_ids:
            node = self._nodes.get(node_id)
            if node is not None:
                self._emit_node_roles(node, roles)
        return (
            reveal_node_id
            if self._row_by_node_id.get(reveal_node_id, -1) >= 0
            else ""
        )

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
                if refresh:
                    root.source.update_snapshots(
                        order_bys=["timestamp desc"], force=True,
                    )
                else:
                    root.source.update_snapshots(
                        order_bys=["timestamp desc"],
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
                if refresh:
                    source.update_snapshots(
                        order_bys=["timestamp desc"], force=True,
                    )
                else:
                    source.update_snapshots(
                        order_bys=["timestamp desc"],
                    )
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
