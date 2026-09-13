"""WorkspaceItemModel: tree state."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .results_types import WorkspaceNode, WorkspaceProjection


class TreeStateMixin:
    def _register_tree(self, node: WorkspaceNode) -> None:
        self._nodes[node.node_id] = node
        for child in node.children:
            self._register_tree(child)

    @staticmethod
    def _node_identity(node: WorkspaceNode) -> tuple:
        if node.node_type == "sobject":
            return node.node_type, node.search_key or node.code
        if node.node_type == "snapshot":
            return (
                node.node_type,
                node.search_key or (
                    node.process,
                    node.context,
                    node.version,
                    node.is_versionless,
                    node.title,
                ),
            )
        if node.node_type == "process":
            return node.node_type, node.process or node.code
        if node.node_type == "relation":
            definition = (node.relation or {}).get("definition") or {}
            return (
                node.node_type,
                node.code,
                node.relationship,
                str(definition.get("instance_type") or ""),
                str(definition.get("path") or ""),
            )
        if node.node_type == "file":
            return node.node_type, node.file_path or node.search_key or node.title
        return node.node_type, node.node_id

    def _deduplicate_siblings(
        self,
        nodes: list[WorkspaceNode],
    ) -> list[WorkspaceNode]:
        unique: list[WorkspaceNode] = []
        seen: set[tuple] = set()
        for node in nodes:
            identity = self._node_identity(node)
            if identity in seen:
                continue
            seen.add(identity)
            if node.children:
                node.children = self._deduplicate_siblings(node.children)
                node.has_children = bool(node.children)
            unique.append(node)
        return unique

    def _ancestor_nodes(self, node: WorkspaceNode) -> list[WorkspaceNode]:
        ancestors: list[WorkspaceNode] = []
        current = node
        visited: set[str] = set()
        while current and current.node_id not in visited:
            visited.add(current.node_id)
            ancestors.append(current)
            current = self._nodes.get(current.parent_id)
        return ancestors

    @staticmethod
    def _state_entry(state: dict, row: int) -> dict:
        if not isinstance(state, dict):
            return {}
        return state.get(row) or state.get(str(row)) or {}

    @staticmethod
    def _collect_nodes_state(
        nodes: list[WorkspaceNode],
        selected_node_id: str = "",
    ) -> dict:
        def collect(nodes: list[WorkspaceNode]) -> dict:
            state: dict = {}
            for row, node in enumerate(nodes):
                child_state = (
                    collect(node.children)
                    if node.children else node.restore_state
                )
                selected = node.node_id == selected_node_id
                expanded = bool(
                    node.expanded
                    or (not node.loaded and node.restore_expanded)
                )
                # Collapsed leaves are the default state. Persisting an entry
                # for every one made cache work grow with the complete loaded
                # result set even when the user had opened only one branch.
                if not (selected or expanded or child_state):
                    continue
                state[row] = {
                    "d": {
                        "s": selected,
                        "e": expanded,
                    },
                    "s": child_state,
                }
            return state

        return collect(nodes)

    def collect_tree_state(self, selected_node_id: str = "") -> dict:
        """Serialize the active tree only when durable state is required."""
        return self._collect_nodes_state(self._roots, selected_node_id)

    def collect_projection_tree_state(
        self,
        projection: WorkspaceProjection,
        selected_node_id: str = "",
    ) -> dict:
        """Serialize an inactive tab's retained tree for the disk cache."""
        if not isinstance(projection, WorkspaceProjection):
            return {}
        return self._collect_nodes_state(
            projection.roots,
            selected_node_id,
        )

    def _apply_state_level(
        self,
        nodes: list[WorkspaceNode],
        state: dict,
    ) -> tuple[list[str], str]:
        pending: list[str] = []
        selected_node_id = ""
        for row, node in enumerate(nodes):
            entry = self._state_entry(state, row)
            data = entry.get("d") or {}
            node.restore_state = entry.get("s") or {}
            if data.get("s"):
                selected_node_id = node.node_id
            should_expand = bool(data.get("e")) and node.has_children
            node.restore_expanded = should_expand
            if not should_expand:
                node.expanded = False
                continue
            if not node.loaded:
                node.expanded = False
                pending.append(node.node_id)
                continue
            node.expanded = True
            child_pending, child_selected = self._apply_state_level(
                node.children,
                node.restore_state,
            )
            pending.extend(child_pending)
            if child_selected:
                selected_node_id = child_selected
        return pending, selected_node_id

    def apply_tree_state(self, state: dict) -> tuple[list[str], str]:
        """Apply tree_state_revert() semantics and return lazy branches to load."""
        pending, selected_node_id = self._apply_state_level(
            self._roots,
            state or {},
        )
        self._replace_visible_items(self._flatten())
        return list(dict.fromkeys(pending)), selected_node_id

    def apply_node_restore_state(self, node_id: str) -> tuple[list[str], str]:
        node = self._nodes.get(node_id)
        if not node or not node.loaded:
            return [], ""
        pending, selected_node_id = self._apply_state_level(
            node.children,
            node.restore_state,
        )
        self._replace_visible_items(self._flatten())
        return list(dict.fromkeys(pending)), selected_node_id
