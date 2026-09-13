"""WorkspaceItemModel: loading."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, replace
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl, Slot

from .results_types import WorkspaceNode


logger = logging.getLogger(__name__)


class LoadingMixin:
    _builtin_process_names = ("icon", "attachment", "publish")

    @staticmethod
    def _relation_node_key(relation: dict, child_code: str) -> str:
        """Return a stable identity for one schema relation."""
        relationship = str(relation.get("relationship") or "related")
        instance_type = str(relation.get("instance_type") or "")
        path = str(relation.get("path") or "")
        return ":".join(
            (str(child_code), relationship, instance_type, path)
        )


    @staticmethod
    def _checkin_option(name: str, default=False):
        try:
            import thlib.global_functions as gf
            from thlib.environment import cfg_controls
            value = gf.get_value_from_config(cfg_controls.get_checkin(), name)
            if value in (None, ""):
                return default
            return bool(int(value))
        except (AttributeError, KeyError, TypeError, ValueError):
            return default

    def _process_is_hidden(
        self,
        process_name: str,
        pipeline_code: str = "",
    ) -> bool:
        process_name = str(process_name or "")
        ignored_processes = (
            (self._process_ignore.get("processes") or {})
            .get(str(pipeline_code or "")) or []
        )
        if process_name in ignored_processes:
            return True
        return (
            process_name in self._builtin_process_names
            and process_name in (
                self._process_ignore.get("builtins") or []
            )
        )

    @staticmethod
    def _cached_process_count(source, accessor: str, process_name: str) -> int:
        try:
            values = getattr(source, accessor)() or {}
            return int(values.get(process_name) or 0)
        except (AttributeError, TypeError, ValueError):
            return 0

    def _make_process_node(
        self,
        root: WorkspaceNode,
        process_name: str,
        process_object,
        process_info: dict,
        title: str,
        accent: str,
        depth: int,
        parent_id: str,
        children: list[WorkspaceNode],
        *,
        expanded: bool = False,
    ) -> WorkspaceNode:
        children = self._deduplicate_siblings(children)
        is_expanded = bool(expanded and children)
        return WorkspaceNode(
            node_id=f"{parent_id}:process:{process_name}",
            node_type="process",
            search_key=root.search_key,
            code=process_name,
            title=str(title or process_name),
            subtitle=str(process_info.get("type") or "process"),
            accent=accent,
            comments=self._cached_process_count(
                root.source, "get_notes_count", process_name,
            ),
            tasks=self._cached_process_count(
                root.source, "get_tasks_count", process_name,
            ),
            comments_updated=(
                process_name in root.updated_comment_processes
            ),
            tasks_updated=(
                process_name in root.updated_task_processes
            ),
            child_count=len(children),
            depth=depth,
            parent_id=parent_id,
            process=process_name,
            expanded=is_expanded,
            restore_expanded=is_expanded,
            has_children=bool(children),
            loaded=True,
            source=process_object,
            children=children,
        )

    @staticmethod
    def _snapshot_timestamp_values(snapshot, fallback: str) -> tuple[str, str]:
        """Use the native TACTIC date presentation without changing its value."""
        timestamp = str(fallback or "").split(".")[0]
        if not timestamp:
            return "", ""
        try:
            pretty = str(snapshot.get_timestamp(pretty=True) or timestamp)
            simple = str(snapshot.get_timestamp(simple=True) or timestamp)
        except (AttributeError, KeyError, TypeError, ValueError):
            return timestamp, timestamp
        return pretty, simple

    def _make_snapshot_node(
        self,
        snapshot,
        process_name: str,
        context_name: str,
        depth: int,
        accent: str,
        parent_id: str,
    ) -> WorkspaceNode:
        info = snapshot.get_snapshot() or {}
        version_number = int(info.get("version") or -1)
        version = (
            "latest" if version_number in (-1, 0)
            else f"v{version_number:03d}"
        )
        revision_number = int(info.get("revision") or 0)
        revision = f"r{revision_number:03d}" if revision_number else ""
        source_key = str(
            snapshot.get_search_key()
            or f"{process_name}:{context_name}:{version}"
        )
        snapshot_id = f"{parent_id}:snapshot:{source_key}"
        try:
            files = list(snapshot.get_files_objects() or [])
        except (AttributeError, KeyError, TypeError):
            files = []
        visible_files = [
            file_object for file_object in files
            if file_object.get_type() not in {"icon", "web", "playblast"}
        ]
        visible_groups: dict[str, list] = {}
        for file_object in visible_files:
            try:
                file_type = str(file_object.get_type() or "main")
            except (AttributeError, KeyError, TypeError):
                file_type = "main"
            visible_groups.setdefault(file_type, []).append(file_object)
        primary_group = next(
            (group for group in visible_groups.values() if group),
            [],
        )
        primary = primary_group[0] if primary_group else None
        timestamp = str(info.get("timestamp") or "").split(".")[0]
        timestamp_pretty, timestamp_simple = self._snapshot_timestamp_values(
            snapshot, timestamp,
        )
        multiple_checkin = len(primary_group) > 1
        title = str(context_name)
        if multiple_checkin:
            title = f"Multiple files | {len(primary_group)}"
        elif primary:
            try:
                meta = primary.get_meta_file_object()
                title = (
                    meta.get_pretty_file_name()
                    if meta else primary.get_filename_with_ext()
                )
            except (AttributeError, KeyError, TypeError):
                pass
        try:
            file_path = str(primary.get_full_abs_path()) if primary else ""
        except (AttributeError, KeyError, TypeError):
            file_path = ""
        return WorkspaceNode(
            node_id=snapshot_id,
            node_type="snapshot",
            search_key=str(snapshot.get_search_key() or ""),
            code=str(info.get("code") or ""),
            title=title,
            subtitle=str(info.get("description") or ""),
            status=str(info.get("repo") or ""),
            accent=accent,
            depth=depth,
            parent_id=parent_id,
            process=process_name,
            context=str(context_name),
            version=version,
            revision=revision,
            author=self._snapshot_author(str(info.get("login") or "")),
            timestamp=timestamp,
            timestamp_pretty=timestamp_pretty,
            timestamp_simple=timestamp_simple,
            repository=self._repository_title(str(info.get("repo") or "")),
            repository_color=self._repository_color(
                str(info.get("repo") or ""), accent,
            ),
            file_path=file_path,
            file_size=self._file_object_size(primary) if primary else "",
            file_exists=self._file_exists(primary),
            is_latest=bool(snapshot.is_latest()),
            is_versionless=bool(snapshot.is_versionless()),
            is_multiple=multiple_checkin,
            preview_source=snapshot,
            chips=self._snapshot_chips(primary, str(context_name)),
            loaded=True,
            source=snapshot,
        )

    @staticmethod
    def _missing_snapshot_node(
        process_name: str,
        context_name: str,
        depth: int,
        accent: str,
        parent_id: str,
    ) -> WorkspaceNode:
        return WorkspaceNode(
            node_id=f"{parent_id}:snapshot:{context_name}:missing-versionless",
            node_type="snapshot",
            search_key="",
            code="",
            title=f"Commit without versionless in {context_name}",
            subtitle="Versionless for this commit is not present",
            accent=accent,
            depth=depth,
            parent_id=parent_id,
            process=process_name,
            context=str(context_name),
            file_exists=False,
            is_versionless=True,
            loaded=True,
        )

    def _snapshot_nodes(
        self,
        process_name: str,
        process_obj,
        depth: int,
        accent: str,
        parent_id: str,
        separate_versions: bool,
    ) -> list[WorkspaceNode]:

        children: list[WorkspaceNode] = []
        contexts = process_obj.get_contexts() if process_obj else {}
        for context_name, context_obj in (contexts or {}).items():
            versionless = list((context_obj.get_versionless() or {}).values())
            versions = list((context_obj.get_versions() or {}).values())
            versions.sort(
                key=lambda item: int((item.get_snapshot() or {}).get("version") or 0),
                reverse=True,
            )
            current = (
                self._make_snapshot_node(
                    versionless[0], process_name, context_name,
                    depth, accent, parent_id,
                )
                if versionless else self._missing_snapshot_node(
                    process_name, context_name, depth, accent, parent_id,
                )
            )
            if separate_versions:
                current.lazy_versions = versions
                current.has_children = bool(versions)
                current.loaded = not current.has_children
            else:
                version_nodes = self._deduplicate_siblings([
                    self._make_snapshot_node(
                        version, process_name, context_name,
                        depth + 1, accent, current.node_id,
                    )
                    for version in versions
                ])
                current.children.extend(version_nodes)
                current.has_children = bool(current.children)
            children.append(current)
        return self._deduplicate_siblings(children)

    def _load_snapshot_versions(
        self,
        node: WorkspaceNode,
        register: bool = True,
    ) -> None:
        node.children = self._deduplicate_siblings([
            self._make_snapshot_node(
                snapshot,
                node.process,
                node.context,
                node.depth + 1,
                node.accent,
                node.node_id,
            )
            for snapshot in node.lazy_versions
        ])
        node.lazy_versions = []
        node.child_count = len(node.children)
        node.loaded = True
        if register:
            for child in node.children:
                self._register_tree(child)

    @staticmethod
    def _relation_count_key(item: WorkspaceNode) -> str:
        if item.relationship != "instance":
            return item.code
        relation = (item.relation or {}).get("definition") or {}
        return str(relation.get("instance_type") or item.code)

    @classmethod
    def _apply_relation_counts(
        cls,
        relation_nodes: list[WorkspaceNode],
        stype_counts: dict,
    ) -> None:
        for item in relation_nodes:
            # Legacy Ui_itemWidget.get_notes_count() uses the instance Search
            # Type count for instance relations. A direct count for the
            # related Search Type can include the reverse side of a
            # self-relation and produce a false child indicator.
            count_key = cls._relation_count_key(item)
            item.child_count = int(stype_counts.get(count_key) or 0)
            item.has_children = item.child_count > 0

    def _load_root(
        self,
        node: WorkspaceNode,
        register: bool = True,
    ) -> None:
        sobject = node.source
        try:
            stype = sobject.get_stype() or self._stype
        except AttributeError:
            stype = self._stype
        try:
            sobject.update_snapshots(order_bys=["timestamp desc"])
        except (AttributeError, KeyError, TypeError):
            pass
        try:
            available_processes = sobject.get_all_processes() or {}
        except (AttributeError, KeyError, TypeError):
            available_processes = {}
        node.needs_sync = self._needs_sync(sobject)
        node.watch_state = self._watch_state(sobject)
        pipeline = None
        try:
            pipelines = stype.get_pipeline() or {}
            pipeline = pipelines.get(sobject.get_pipeline_code())
        except (AttributeError, KeyError, TypeError):
            pass
        builtins = list(self._builtin_process_names)
        pipeline_processes = list((getattr(pipeline, "pipeline", None) or {}).keys())
        process_names = list(pipeline_processes)
        if self._checkin_option("showAllProcessCheckBox"):
            process_names.extend(name for name in builtins if name not in process_names)
        if not process_names:
            process_names = builtins
        # An attachment is user content rather than an empty convenience row.
        # Keep it discoverable when snapshots exist even if the project's
        # workflow does not declare the built-in process.
        elif (
            available_processes.get("attachment") is not None
            and "attachment" not in process_names
        ):
            process_names.append("attachment")
        process_names = list(dict.fromkeys(process_names))
        separate_versions = True

        def build_process(
            process_name: str,
            process_pipeline,
            depth: int,
            parent_id: str,
            filter_special: bool = False,
        ) -> WorkspaceNode | None:
            pipeline_info = getattr(process_pipeline, "info", {}) or {}
            pipeline_code = str(pipeline_info.get("code") or "")
            if self._process_is_hidden(process_name, pipeline_code):
                return None
            process_info = None
            try:
                process_info = process_pipeline.get_process_info(process_name)
            except (AttributeError, KeyError, TypeError):
                pass
            if not process_info:
                process_info = {"type": "manual", "name": process_name}
            if filter_special and process_info.get("type") in {
                "action", "condition", "dependency", "progress",
            }:
                return None
            process_obj = sobject.get_process(process_name)
            process_id = f"{parent_id}:process:{process_name}"
            process_color = str(process_info.get("color") or node.accent)
            process_children: list[WorkspaceNode] = []
            if process_info.get("type") == "hierarchy":
                try:
                    workflow = stype.get_workflow()
                    child_pipeline = workflow.get_child_pipeline_by_process_code(
                        process_pipeline,
                        process_name,
                    )
                    child_names = list(dict.fromkeys(
                        child_pipeline.get_all_pipeline_names()
                    )) if child_pipeline else []
                except (AttributeError, KeyError, TypeError):
                    child_pipeline, child_names = None, []
                for child_name in child_names:
                    child = build_process(
                        child_name,
                        child_pipeline,
                        depth + 1,
                        process_id,
                    )
                    if child:
                        process_children.append(child)
            process_children.extend(self._snapshot_nodes(
                process_name,
                process_obj,
                depth + 1,
                process_color,
                process_id,
                separate_versions,
            ))
            try:
                label = process_pipeline.get_process_label(process_name)
            except (AttributeError, KeyError, TypeError):
                label = process_name.replace("_", " ").title()
            return self._make_process_node(
                node,
                process_name,
                process_obj,
                process_info,
                str(label or process_name),
                process_color,
                depth,
                parent_id,
                process_children,
            )

        relation_nodes: list[WorkspaceNode] = []
        ancestor_stype_codes: set[str] = set()
        # Ui_itemWidget.check_for_child_recursion() adds the parent sObject
        # type only after entering a relation branch. Keep a valid first-level
        # self-relation, but prevent A -> B -> A and deeper cycles.
        for ancestor in self._ancestor_nodes(node)[1:]:
            if ancestor.node_type != "sobject" or not ancestor.source:
                continue
            try:
                ancestor_stype = ancestor.source.get_stype()
                ancestor_code = ancestor_stype.get_code() if ancestor_stype else ""
            except (AttributeError, KeyError, TypeError):
                ancestor_code = ""
            if ancestor_code:
                ancestor_stype_codes.add(str(ancestor_code))
        try:
            schema = stype.get_schema()
            project = stype.get_project()
            for relation in (schema.children or []):
                if relation.get("type") == "many_to_many":
                    continue
                child_code = relation.get("from")
                if not child_code or child_code in ancestor_stype_codes:
                    continue
                if child_code in (
                    self._process_ignore.get("children") or []
                ):
                    continue
                child_stype = project.stypes.get(child_code)
                if not child_stype:
                    continue
                relation_nodes.append(WorkspaceNode(
                    node_id=(
                        f"{node.node_id}:relation:"
                        f"{self._relation_node_key(relation, child_code)}"
                    ),
                    node_type="relation",
                    search_key=node.search_key,
                    code=child_code,
                    title=child_stype.get_pretty_name(),
                    subtitle=str(relation.get("relationship") or "related"),
                    accent=child_stype.get_stype_color(fmt="hex") or node.accent,
                    depth=node.depth + 1,
                    parent_id=node.node_id,
                    relationship=str(relation.get("relationship") or ""),
                    linkable_relation=(
                        str(relation.get("relationship") or "") == "instance"
                    ),
                    has_children=True,
                    source=sobject,
                    relation={"definition": relation, "stype": child_stype},
                ))
        except (AttributeError, KeyError, TypeError):
            pass

        process_nodes = []
        for process_name in process_names:
            process_node = build_process(
                process_name,
                pipeline,
                node.depth + 1,
                node.node_id,
                filter_special=True,
            )
            if process_node:
                process_nodes.append(process_node)

        process_items = []

        def collect_processes(items):
            for item in items:
                if item.node_type == "process":
                    process_items.append(item)
                collect_processes(item.children)

        collect_processes(process_nodes)
        count_processes = list(dict.fromkeys(
            item.process for item in process_items if item.process
        ))
        relation_counts = []
        for item in relation_nodes:
            if not item.code:
                continue
            count_key = self._relation_count_key(item)
            try:
                expression = sobject.get_related_sobjects_tel_string(
                    item.relation["stype"], stype, path="child",
                )
            except (AttributeError, KeyError, TypeError, ValueError):
                relation_counts.append(count_key)
                continue
            relation_counts.append({
                "key": count_key,
                "searchType": item.code,
                "expression": expression,
            })
        if count_processes or relation_counts:
            try:
                from thlib import tactic_classes as tc

                counts = tc.get_notes_count(
                    sobject,
                    count_processes,
                    relation_counts,
                ) or {}
                notes = counts.get("notes") or {}
                tasks = counts.get("tasks") or {}
                for item in process_items:
                    item.comments = int(notes.get(item.process) or 0)
                    item.tasks = int(tasks.get(item.process) or 0)
                    sobject.set_notes_count(item.process, item.comments)
                    sobject.set_tasks_count(item.process, item.tasks)
                stype_counts = counts.get("stypes") or {}
                self._apply_relation_counts(relation_nodes, stype_counts)
            except Exception:
                logger.exception(
                    "Unable to load task and note counts for %s",
                    node.search_key,
                )

        direct_publish = []
        publish_process = (
            available_processes.get("publish")
            if "publish" not in (
                self._process_ignore.get("builtins") or []
            ) else None
        )
        if publish_process:
            publish_color = node.accent
            try:
                publish_info = pipeline.get_process_info("publish") or {}
                publish_color = str(
                    publish_info.get("color") or publish_color
                )
            except (AttributeError, KeyError, TypeError):
                pass
            direct_publish = self._snapshot_nodes(
                "publish",
                publish_process,
                node.depth + 1,
                publish_color,
                node.node_id,
                separate_versions,
            )

        # add_snapshot_item(..., insert_at_top=True) puts direct publish
        # contexts above relation and process rows in the original QTreeWidget.
        children = self._deduplicate_siblings(
            list(reversed(direct_publish)) + relation_nodes + process_nodes
        )
        node.children = children
        node.loaded = True
        node.child_count = len(children)
        node.has_children = bool(children)
        if register:
            for child in children:
                self._register_tree(child)

    def _load_relation(
        self,
        node: WorkspaceNode,
        register: bool = True,
    ) -> None:
        relation_payload = node.relation or {}
        relation = relation_payload.get("definition") or {}
        child_stype = relation_payload.get("stype")
        child_code = relation.get("from")
        try:
            related = node.source.get_related_sobjects(
                child_stype=child_stype,
                parent_stype=node.source.get_stype(),
                path="child",
                # Relation rows are immediately rendered as normal sObject
                # items.  Fetch their snapshot metadata in the same batched
                # relation query so their native preview API has data when
                # QML requests the preview for the newly inserted row.
                get_all_snapshots=True,
            )
            if isinstance(related, tuple):
                related = related[0]
            if isinstance(related, dict):
                related = list(related.values())
            related = list(related or [])
        except (AttributeError, KeyError, TypeError):
            related = []
        accent = child_stype.get_stype_color(fmt="hex") if child_stype else node.accent
        node.children = []
        ancestor_search_keys = {
            ancestor.search_key
            for ancestor in self._ancestor_nodes(node)
            if ancestor.node_type == "sobject" and ancestor.search_key
        }
        seen_related: set[str] = set()
        for sobject in related:
            info = sobject.get_info() or {}
            search_key = str(sobject.get_search_key() or "")
            identity = search_key or str(info.get("code") or info.get("id") or "")
            if not identity or identity in seen_related or identity in ancestor_search_keys:
                continue
            seen_related.add(identity)
            child = WorkspaceNode(
                node_id=f"{node.node_id}:{identity}",
                node_type="sobject",
                search_key=search_key,
                code=str(info.get("code") or ""),
                title=str(sobject.get_title() or info.get("code") or ""),
                subtitle=str(info.get("description") or ""),
                status=str(info.get("status") or ""),
                accent=accent or node.accent,
                depth=node.depth + 1,
                parent_id=node.node_id,
                relationship=str(relation.get("relationship") or ""),
                watch_state=self._watch_state(sobject),
                needs_sync=self._needs_sync(sobject),
                progress_items=self._progress_items(sobject, child_stype),
                has_children=True,
                source=sobject,
                preview_source=sobject,
                chips=self._build_info_items(child_stype, info),
            )
            node.children.append(child)
        node.children = self._deduplicate_siblings(node.children)
        if register:
            for child in node.children:
                self._register_tree(child)
        node.child_count = len(node.children)
        node.has_children = bool(node.children)
        node.loaded = True
