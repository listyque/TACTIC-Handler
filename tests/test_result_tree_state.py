from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from thlib.ui.controllers.result_tree import ResultTreeMixin
from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


def _loaded_tree() -> WorkspaceNode:
    snapshot = WorkspaceNode(
        node_id="asset:process:render:snapshot:SNAPSHOT001",
        node_type="snapshot",
        search_key="sthpw/snapshot?code=SNAPSHOT001",
        code="SNAPSHOT001",
        title="render_v001.ma",
        depth=2,
        parent_id="asset:process:render",
        loaded=True,
    )
    process = WorkspaceNode(
        node_id="asset:process:render",
        node_type="process",
        search_key="demo/asset?code=ASSET001",
        code="render",
        title="Render",
        depth=1,
        parent_id="asset",
        expanded=True,
        has_children=True,
        loaded=True,
        children=[snapshot],
    )
    return WorkspaceNode(
        node_id="asset",
        node_type="sobject",
        search_key="demo/asset?code=ASSET001",
        code="ASSET001",
        title="Asset",
        expanded=True,
        has_children=True,
        loaded=True,
        children=[process],
    )


class _Snapshot:
    def __init__(self, code, version, versionless=False):
        self.code = code
        self.version = version
        self.versionless = versionless

    def get_snapshot(self):
        return {
            "code": self.code,
            "version": -1 if self.versionless else self.version,
            "context": "render",
            "login": "artist",
            "timestamp": "2026-08-29 12:00:00",
        }

    def get_search_key(self):
        return "sthpw/snapshot?code={0}".format(self.code)

    @staticmethod
    def get_files_objects(*_args, **_kwargs):
        return []

    @staticmethod
    def get_timestamp(**_kwargs):
        return "2026-08-29 12:00:00"

    def is_latest(self):
        return not self.versionless

    def is_versionless(self):
        return self.versionless


class _SnapshotContext:
    def __init__(self, context, current, versions):
        self.context = context
        self.current = current
        self.versions = versions

    def get_versionless(self):
        return {self.current.code: self.current}

    def get_versions(self):
        return {snapshot.code: snapshot for snapshot in self.versions}


class _SnapshotProcess:
    def __init__(self, context, current, versions):
        self.context = _SnapshotContext(context, current, versions)

    def get_contexts(self):
        return {self.context.context: self.context}


class _SnapshotSource:
    def __init__(self, processes):
        self.processes = processes
        self.refresh_calls = []

    def update_snapshots(self, **kwargs):
        self.refresh_calls.append(dict(kwargs))

    def get_all_processes(self):
        return self.processes

    def get_process(self, process):
        return self.processes.get(process)


class _RootPipeline:
    info = {"code": "asset_pipeline"}
    pipeline = {"render": {"type": "manual"}}

    @staticmethod
    def get_process_info(process):
        return {"type": "manual", "name": process}

    @staticmethod
    def get_process_label(process):
        return process.replace("_", " ").title()


class _RootSType:
    pipeline = _RootPipeline()

    @classmethod
    def get_pipeline(cls):
        return {"asset_pipeline": cls.pipeline}

    @staticmethod
    def get_schema():
        return SimpleNamespace(children=[])

    @staticmethod
    def get_project():
        return SimpleNamespace(stypes={})


class _RootSnapshotSource(_SnapshotSource):
    @staticmethod
    def get_stype():
        return _RootSType()

    @staticmethod
    def get_pipeline_code():
        return "asset_pipeline"

    @staticmethod
    def is_snapshots_need_update():
        return False

    @staticmethod
    def get_project():
        return None

    @staticmethod
    def get_notes_count():
        return {}

    @staticmethod
    def get_tasks_count():
        return {}

    @staticmethod
    def set_notes_count(*_args):
        return None

    @staticmethod
    def set_tasks_count(*_args):
        return None


class ResultTreeStateTests(unittest.TestCase):
    def test_child_filter_keeps_the_canonical_tree_and_other_branches(self):
        model = WorkspaceItemModel()
        root = _loaded_tree()
        branch = root.children[0]
        first = branch.children[0]
        from dataclasses import replace
        second = replace(first, node_id='other', search_key='sthpw/snapshot?code=SECOND', code='SECOND', title='Other', parent_id=branch.node_id)
        branch.children.append(second)
        model.replace_nodes([root])
        model.filter_children(branch.node_id, 'Other', ['other'])
        self.assertEqual([node.node_id for node in model._items], [root.node_id, branch.node_id, 'other'])
        self.assertEqual(branch.children, [first, second])
        model.toggle_node(branch.node_id)
        model.toggle_node(branch.node_id)
        self.assertEqual(model._items[-1].node_id, 'other')
        model.filter_children(branch.node_id, 'absent', [])
        self.assertEqual(len(model._items), 2)
        model.filter_children(branch.node_id, '', [])
        self.assertIs(model._items[-2], first)
        self.assertIs(model._items[-1], second)

    def test_failed_preview_does_not_immediately_request_missing_file_again(self):
        model = WorkspaceItemModel()
        node = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            preview_url="pending-preview:missing",
            card_preview_url="pending-preview:missing",
            preview_requested=True,
            card_preview_requested=True,
        )
        model.replace_nodes([node])

        model.fail_preview("missing")

        self.assertEqual(node.preview_url, "")
        self.assertEqual(node.card_preview_url, "")
        self.assertTrue(node.preview_requested)
        self.assertTrue(node.card_preview_requested)
        self.assertIsNone(model.begin_preview_request(node.node_id))
        self.assertIsNone(model.begin_card_preview_request(node.node_id))

    def test_category_labels_resolve_configured_expressions_and_reuse_cache(self):
        from thlib.tactic_classes import parse_tactic_xml
        from thlib.ui.controllers.search_runtime import SearchRuntimeMixin

        definition = parse_tactic_xml('''<config><edit_definition>
            <element name="assets_category_code"><display>
            <values_expr>@GET(demo/category.code)</values_expr>
            <labels_expr>@GET(demo/category.name)</labels_expr>
            </display></element></edit_definition></config>''')
        stype = SimpleNamespace(
            get_definition=lambda *args, **kwargs: definition,
            get_code=lambda: "demo/asset",
        )
        record = {"assets_category_code": "props", "description": "Ready"}
        obj = SimpleNamespace(get_info=lambda: record)
        with patch("thlib.server_cache.read_entry", return_value=None), \
                patch("thlib.server_cache.token", return_value="token"), \
                patch("thlib.server_cache.write_entry") as write, \
                patch("thlib.tactic_classes.server_start") as server:
            server.return_value.eval.side_effect = [["props"], ["Equipment"]]
            SearchRuntimeMixin._resolve_category_labels([obj], stype, "demo")
            self.assertEqual(record["__category_labels__"], {
                "assets_category_code": "Equipment",
            })
            self.assertEqual(WorkspaceItemModel._sobject_subtitle(None, record),
                             "Ready · Equipment")
            write.assert_called_once()
        record.pop("__category_labels__")
        with patch("thlib.server_cache.read_entry", return_value={"props": "Equipment"}), \
                patch("thlib.tactic_classes.server_start") as server:
            SearchRuntimeMixin._resolve_category_labels([obj], stype, "demo")
            server.assert_not_called()
            self.assertEqual(record["__category_labels__"]["assets_category_code"],
                             "Equipment")

    def test_sobject_subtitle_uses_pipeline_title_not_code(self):
        class Pipeline:
            @staticmethod
            def get_info():
                return {"code": "niki_friends/assets", "name": "3D Asset"}

            @staticmethod
            def get_processes_info_by_type(_kind):
                return []

        class SearchType:
            @staticmethod
            def get_pipeline():
                return {"niki_friends/assets": Pipeline()}

            @staticmethod
            def get_stype_color(**_kwargs):
                return "#607d8b"

        class SObject:
            info = {
                "code": "ASSET0001",
                "description": "Added",
                "pipeline_code": "niki_friends/assets",
                "assets_category_code": "objects/equipment",
            }

            @classmethod
            def get_info(cls):
                return cls.info

            @staticmethod
            def get_search_key():
                return "niki_friends/assets?code=ASSET0001"

            @staticmethod
            def get_title():
                return "aid_kit"

            @staticmethod
            def get_notes_count():
                return {}

            @staticmethod
            def get_tasks_count():
                return {}

            @staticmethod
            def get_pipeline_code():
                return "niki_friends/assets"

        model = WorkspaceItemModel()
        model.replace_sobjects([SObject()], SearchType())

        index = model.index(0, 0)
        self.assertEqual(
            model.data(index, model.SubtitleRole),
            "Added · 3D Asset · objects/equipment",
        )
        model.update_description(SObject.get_search_key(), "Ready")
        self.assertEqual(
            model.data(index, model.SubtitleRole),
            "Ready · 3D Asset · objects/equipment",
        )

    def test_root_load_shows_attachment_process_that_has_snapshots(self):
        current = _Snapshot("ATTACHMENT_CURRENT", -1, versionless=True)
        created = _Snapshot("ATTACHMENT001", 1)
        source = _RootSnapshotSource({
            "attachment": _SnapshotProcess(
                "attachment", current, [created]
            )
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            accent="#445566",
            source=source,
        )
        model = WorkspaceItemModel()

        with (
            patch.object(model, "_checkin_option", return_value=False),
            patch(
                "thlib.tactic_classes.get_notes_count",
                return_value={"notes": {}, "tasks": {}, "stypes": {}},
            ),
        ):
            model._load_root(root, register=False)

        attachment = next(
            child for child in root.children
            if child.node_type == "process"
            and child.process == "attachment"
        )
        self.assertTrue(attachment.has_children)
        self.assertEqual(attachment.children[0].context, "attachment")

    def test_attachment_checkin_materializes_missing_process_row(self):
        model = WorkspaceItemModel()
        relation = WorkspaceNode(
            node_id="asset:relation:shots",
            node_type="relation",
            search_key="demo/asset?code=ASSET001",
            code="demo/shot",
            title="Shots",
            depth=1,
            parent_id="asset",
        )
        current = _Snapshot("ATTACHMENT_CURRENT", -1, versionless=True)
        created = _Snapshot("ATTACHMENT001", 1)
        source = _SnapshotSource({
            "attachment": _SnapshotProcess(
                "attachment", current, [created]
            )
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            has_children=True,
            loaded=True,
            source=source,
            children=[relation],
        )
        model.replace_nodes([root])

        _search_key, refresh = model.prepare_snapshot_branch_refresh(
            root.search_key,
            "attachment",
            "attachment",
            "ATTACHMENT001",
        )
        reveal_node_id = model.apply_snapshot_branch_refresh(refresh)

        attachment = model.node_for("asset:process:attachment")
        self.assertIsNotNone(attachment)
        self.assertTrue(attachment.expanded)
        self.assertEqual(attachment.children[0].context, "attachment")
        self.assertEqual(model.node_for(reveal_node_id).code, "ATTACHMENT001")
        self.assertIs(model.node_for(relation.node_id), relation)

    def test_attachment_checkin_respects_explicit_builtin_filter(self):
        model = WorkspaceItemModel()
        model.set_process_ignore({"builtins": ["attachment"]})
        current = _Snapshot("ATTACHMENT_CURRENT", -1, versionless=True)
        created = _Snapshot("ATTACHMENT001", 1)
        source = _SnapshotSource({
            "attachment": _SnapshotProcess(
                "attachment", current, [created]
            )
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            loaded=True,
            source=source,
        )
        model.replace_nodes([root])

        _search_key, refresh = model.prepare_snapshot_branch_refresh(
            root.search_key,
            "attachment",
            "attachment",
            "ATTACHMENT001",
        )
        reveal_node_id = model.apply_snapshot_branch_refresh(refresh)

        self.assertEqual(reveal_node_id, "")
        self.assertIsNone(model.node_for("asset:process:attachment"))

    def test_first_process_checkin_notifies_the_existing_process_row(self):
        model = WorkspaceItemModel()
        process_node = WorkspaceNode(
            node_id="asset:process:render",
            node_type="process",
            search_key="demo/asset?code=ASSET001",
            code="render",
            title="Render",
            depth=1,
            parent_id="asset",
            process="render",
            expanded=False,
            has_children=False,
            loaded=True,
        )
        current = _Snapshot("CURRENT", -1, versionless=True)
        created = _Snapshot("SNAPSHOT001", 1)
        source = _SnapshotSource({
            "render": _SnapshotProcess("render", current, [created])
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            has_children=True,
            loaded=True,
            source=source,
            children=[process_node],
        )
        model.replace_nodes([root])
        process_row = model.row_for_node(process_node.node_id)
        changes = []
        model.dataChanged.connect(
            lambda first, _last, roles: changes.append(
                (first.row(), set(roles))
            )
        )

        _search_key, refresh = model.prepare_snapshot_branch_refresh(
            root.search_key, "render", "render", "SNAPSHOT001"
        )
        reveal_node_id = model.apply_snapshot_branch_refresh(refresh)

        refreshed_process = model.node_for(process_node.node_id)
        self.assertIsNot(refreshed_process, process_node)
        self.assertTrue(refreshed_process.has_children)
        self.assertTrue(refreshed_process.expanded)
        self.assertGreater(refreshed_process.child_count, 0)
        self.assertEqual(model.node_for(reveal_node_id).code, "SNAPSHOT001")
        process_changes = [
            roles for row, roles in changes if row == process_row
        ]
        self.assertTrue(process_changes)
        changed_roles = set().union(*process_changes)
        self.assertTrue({
            model.ExpandedRole,
            model.HasChildrenRole,
            model.ChildCountRole,
            model.ControlsRole,
        }.issubset(changed_roles))

    def test_completed_checkin_replaces_only_its_snapshot_branch(self):
        model = WorkspaceItemModel()
        old_snapshot = WorkspaceNode(
            node_id="asset:process:render:snapshot:old",
            node_type="snapshot",
            search_key="sthpw/snapshot?code=OLD",
            code="OLD",
            title="render_v001.ma",
            depth=2,
            parent_id="asset:process:render",
            process="render",
            context="render",
            loaded=True,
        )
        process_node = WorkspaceNode(
            node_id="asset:process:render",
            node_type="process",
            search_key="demo/asset?code=ASSET001",
            code="render",
            title="Render",
            depth=1,
            parent_id="asset",
            process="render",
            expanded=True,
            has_children=True,
            loaded=True,
            children=[old_snapshot],
        )
        relation = WorkspaceNode(
            node_id="asset:relation:shots",
            node_type="relation",
            search_key="demo/asset?code=ASSET001",
            code="demo/shot",
            title="Shots",
            depth=1,
            parent_id="asset",
            expanded=True,
            has_children=True,
            loaded=True,
        )
        current = _Snapshot("CURRENT", -1, versionless=True)
        created = _Snapshot("SNAPSHOT002", 2)
        source = _SnapshotSource({
            "render": _SnapshotProcess(
                "render", current, [created, _Snapshot("SNAPSHOT001", 1)]
            )
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            has_children=True,
            loaded=True,
            source=source,
            children=[relation, process_node],
        )
        model.replace_nodes([root])

        search_key, refresh = model.prepare_snapshot_branch_refresh(
            root.search_key, "render", "render", "SNAPSHOT002"
        )
        reveal_node_id = model.apply_snapshot_branch_refresh(refresh)

        self.assertEqual(search_key, root.search_key)
        self.assertEqual(source.refresh_calls, [{
            "order_bys": ["timestamp desc"], "force": True,
        }])
        self.assertIs(model.node_for(relation.node_id), relation)
        self.assertIsNone(model.node_for(old_snapshot.node_id))
        self.assertEqual(model.node_for(reveal_node_id).code, "SNAPSHOT002")
        self.assertGreaterEqual(model.row_for_node(reveal_node_id), 0)
        self.assertTrue(model.node_for(process_node.node_id).expanded)

    def test_publish_checkin_refreshes_direct_top_branch(self):
        model = WorkspaceItemModel()
        old_publish = WorkspaceNode(
            node_id="asset:snapshot:old-publish",
            node_type="snapshot",
            search_key="sthpw/snapshot?code=OLDPUB",
            code="OLDPUB",
            title="publish_v001.mov",
            depth=1,
            parent_id="asset",
            process="publish",
            context="publish",
            loaded=True,
        )
        relation = WorkspaceNode(
            node_id="asset:relation:shots",
            node_type="relation",
            search_key="demo/asset?code=ASSET001",
            code="demo/shot",
            title="Shots",
            depth=1,
            parent_id="asset",
        )
        current = _Snapshot("PUBLISH_CURRENT", -1, versionless=True)
        created = _Snapshot("PUBLISH002", 2)
        source = _SnapshotSource({
            "publish": _SnapshotProcess(
                "publish", current, [created, _Snapshot("PUBLISH001", 1)]
            )
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            has_children=True,
            loaded=True,
            source=source,
            children=[old_publish, relation],
        )
        model.replace_nodes([root])

        _search_key, refresh = model.prepare_snapshot_branch_refresh(
            root.search_key, "publish", "publish", "PUBLISH002"
        )
        reveal_node_id = model.apply_snapshot_branch_refresh(refresh)

        self.assertEqual(model.node_for(reveal_node_id).code, "PUBLISH002")
        self.assertIs(model.node_for(relation.node_id), relation)
        self.assertIsNone(model.node_for(old_publish.node_id))
        self.assertEqual(root.children[0].process, "publish")
        self.assertTrue(root.expanded)

    def test_sobject_publish_reveals_direct_snapshot_not_process_branch(self):
        model = WorkspaceItemModel()
        process_node = WorkspaceNode(
            node_id="asset:process:publish",
            node_type="process",
            search_key="demo/asset?code=ASSET001",
            code="publish",
            title="Publish",
            depth=1,
            parent_id="asset",
            process="publish",
            expanded=False,
            has_children=True,
            loaded=True,
        )
        current = _Snapshot("PUBLISH_CURRENT", -1, versionless=True)
        created = _Snapshot("PUBLISH002", 2)
        source = _SnapshotSource({
            "publish": _SnapshotProcess("publish", current, [created])
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=False,
            has_children=True,
            loaded=True,
            source=source,
            children=[process_node],
        )
        model.replace_nodes([root])

        _search_key, refresh = model.prepare_snapshot_branch_refresh(
            root.search_key,
            "publish",
            "publish",
            "PUBLISH002",
            keep_publish_process_collapsed=True,
        )
        reveal_node_id = model.apply_snapshot_branch_refresh(
            refresh, keep_publish_process_collapsed=True,
        )

        self.assertEqual(
            model.node_for(reveal_node_id).code, "PUBLISH_CURRENT",
        )
        self.assertTrue(root.expanded)
        self.assertFalse(model.node_for(process_node.node_id).expanded)
        direct_publish = [
            child for child in root.children
            if child.node_type == "snapshot" and child.process == "publish"
        ]
        self.assertTrue(direct_publish)
        self.assertFalse(any(child.expanded for child in direct_publish))
        self.assertIs(model.node_for(reveal_node_id), direct_publish[0])

    def test_sobject_publish_completion_selects_direct_snapshot(self):
        model = WorkspaceItemModel()
        process = WorkspaceNode(
            node_id="asset:process:publish",
            node_type="process",
            search_key="demo/asset?code=ASSET001",
            code="publish",
            title="Publish",
            depth=1,
            parent_id="asset",
            process="publish",
            expanded=False,
            loaded=True,
        )
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=False,
            has_children=True,
            loaded=True,
            children=[process],
        )
        model.replace_nodes([root])
        direct_current = WorkspaceNode(
            node_id="asset:snapshot:publish",
            node_type="snapshot",
            search_key="sthpw/snapshot?code=PUBLISH_CURRENT",
            code="PUBLISH_CURRENT",
            title="publish.png",
            depth=1,
            parent_id=root.node_id,
            process="publish",
            context="publish",
            expanded=False,
            has_children=True,
            loaded=False,
        )
        process_snapshot = WorkspaceNode(
            node_id="asset:process:publish:snapshot:PUBLISH002",
            node_type="snapshot",
            search_key="sthpw/snapshot?code=PUBLISH002",
            code="PUBLISH002",
            title="publish_v002.png",
            depth=2,
            parent_id=process.node_id,
            process="publish",
            context="publish",
            loaded=True,
        )
        tab = SimpleNamespace(
            tab_id="tab",
            workspace_model=model,
            selected_node_id=root.node_id,
            view_mode="continious",
            workspace_roots=[],
            workspace_projection={},
            tree_state_dirty=False,
        )
        section = SimpleNamespace(entry_key="assets")
        selected = []
        revealed = []
        browser_refreshes = []
        controller = SimpleNamespace(
            _checkin_tree_refresh_requests={"request": (
                section.entry_key,
                tab.tab_id,
                model,
                root.search_key,
                root.node_id,
                True,
            )},
            _current_section=lambda: section,
            _current_tab=lambda: tab,
            _current_tree_keeps_checkin_parent=lambda *_args: True,
            select_result_node=lambda *args: selected.append(args),
            result_node_reveal_requested=SimpleNamespace(
                emit=revealed.append,
            ),
            refresh_snapshot_browser_for=browser_refreshes.append,
            _save_search_cache=lambda: None,
        )
        refresh = {"roots": [{
            "rootId": root.node_id,
            "directSnapshots": [direct_current],
            "processBranches": [{
                "nodeId": process.node_id,
                "processObject": object(),
                "snapshots": [process_snapshot],
            }],
            "revealNodeId": direct_current.node_id,
        }]}

        ResultTreeMixin._checkin_tree_refresh_ready(
            controller,
            (root.search_key, refresh, "request"),
        )

        self.assertEqual(selected, [(
            direct_current.node_id,
            direct_current.search_key,
            direct_current.node_type,
        )])
        self.assertEqual(revealed, [direct_current.node_id])
        self.assertEqual(browser_refreshes, [])
        self.assertTrue(root.expanded)
        self.assertFalse(model.node_for(process.node_id).expanded)

    def test_publish_versionless_refresh_discards_stale_preview_state(self):
        model = WorkspaceItemModel()
        versionless_id = (
            "asset:snapshot:sthpw/snapshot?code=PUBLISH_CURRENT"
        )
        old_current = WorkspaceNode(
            node_id=versionless_id,
            node_type="snapshot",
            search_key="sthpw/snapshot?code=PUBLISH_CURRENT",
            code="PUBLISH_CURRENT",
            title="publish.png",
            depth=1,
            parent_id="asset",
            process="publish",
            context="publish",
            is_versionless=True,
            preview_url="file:///publish-preview.jpg?revision=old",
            card_preview_url="pending-preview:old-card",
            preview_requested=True,
            card_preview_requested=True,
            preview_revealed=True,
            loaded=True,
        )
        current = _Snapshot("PUBLISH_CURRENT", -1, versionless=True)
        created = _Snapshot("PUBLISH002", 2)
        source = _SnapshotSource({
            "publish": _SnapshotProcess("publish", current, [created])
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            has_children=True,
            loaded=True,
            source=source,
            preview_source=source,
            preview_url="file:///object-preview.jpg?revision=old",
            card_preview_url="pending-preview:old-root-card",
            preview_requested=True,
            card_preview_requested=True,
            preview_revealed=True,
            children=[old_current],
        )
        model.replace_nodes([root])
        model._pending_preview_paths.update({
            "pending-preview:old-card": "D:/cache/old-card.jpg",
            "pending-preview:old-root-card": "D:/cache/old-root.jpg",
        })

        _search_key, refresh = model.prepare_snapshot_branch_refresh(
            root.search_key,
            "publish",
            "publish",
            "PUBLISH002",
            update_versionless=True,
        )
        model.apply_snapshot_branch_refresh(refresh)

        refreshed = model.node_for(versionless_id)
        self.assertIsNotNone(refreshed)
        self.assertEqual(refreshed.preview_url, "")
        self.assertEqual(refreshed.card_preview_url, "")
        self.assertFalse(refreshed.preview_requested)
        self.assertFalse(refreshed.card_preview_requested)
        self.assertFalse(refreshed.preview_revealed)
        self.assertEqual(root.preview_url, "")
        self.assertEqual(root.card_preview_url, "")
        self.assertFalse(root.preview_requested)
        self.assertFalse(root.card_preview_requested)
        self.assertEqual(model._pending_preview_paths, {})

    def test_versionless_refresh_rejects_inflight_old_preview_result(self):
        model = WorkspaceItemModel()
        old_current = _Snapshot("PUBLISH_CURRENT", -1, versionless=True)
        fresh_current = _Snapshot("PUBLISH_CURRENT", -1, versionless=True)
        created = _Snapshot("PUBLISH002", 2)
        versionless_id = (
            "asset:snapshot:sthpw/snapshot?code=PUBLISH_CURRENT"
        )
        old_node = WorkspaceNode(
            node_id=versionless_id,
            node_type="snapshot",
            search_key=old_current.get_search_key(),
            code="PUBLISH_CURRENT",
            title="publish.png",
            depth=1,
            parent_id="asset",
            process="publish",
            context="publish",
            is_versionless=True,
            preview_source=old_current,
            source=old_current,
            loaded=True,
        )
        source = _SnapshotSource({
            "publish": _SnapshotProcess(
                "publish", fresh_current, [created]
            )
        })
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            has_children=True,
            loaded=True,
            source=source,
            preview_source=source,
            children=[old_node],
        )
        model.replace_nodes([root])
        self.assertIsNotNone(model.begin_preview_request(versionless_id))
        old_versionless_token = model.preview_request_token(versionless_id)
        self.assertIsNotNone(model.begin_preview_request(root.node_id))
        old_root_token = model.preview_request_token(root.node_id)
        self.assertIsNotNone(model.begin_card_preview_request(root.node_id))
        old_root_card_token = model.preview_request_token(
            root.node_id, card=True,
        )

        _search_key, refresh = model.prepare_snapshot_branch_refresh(
            root.search_key,
            "publish",
            "publish",
            "PUBLISH002",
            update_versionless=True,
        )
        model.apply_snapshot_branch_refresh(refresh)

        refreshed = model.node_for(versionless_id)
        self.assertIs(refreshed.preview_source, fresh_current)
        with patch.object(
            model, "_preview_url", return_value="file:///stale-preview.jpg"
        ):
            model.apply_preview(
                versionless_id,
                old_current,
                [object()],
                old_versionless_token,
            )
        self.assertEqual(refreshed.preview_url, "")

        fresh_request = model.begin_preview_request(versionless_id)
        self.assertEqual(fresh_request, ("snapshot", fresh_current))
        fresh_versionless_token = model.preview_request_token(versionless_id)
        with patch.object(
            model, "_preview_url", return_value="file:///fresh-preview.jpg"
        ):
            model.apply_preview(
                versionless_id,
                fresh_current,
                [object()],
                fresh_versionless_token,
            )
        self.assertEqual(refreshed.preview_url, "file:///fresh-preview.jpg")

        self.assertIsNotNone(model.begin_preview_request(root.node_id))
        fresh_root_token = model.preview_request_token(root.node_id)
        self.assertNotEqual(old_root_token, fresh_root_token)
        with patch.object(
            model, "_preview_url", return_value="file:///stale-root.jpg"
        ):
            model.apply_preview(
                root.node_id,
                source,
                [object()],
                old_root_token,
            )
        self.assertEqual(root.preview_url, "")
        with patch.object(
            model, "_preview_url", return_value="file:///fresh-root.jpg"
        ):
            model.apply_preview(
                root.node_id,
                source,
                [object()],
                fresh_root_token,
            )
        self.assertEqual(root.preview_url, "file:///fresh-root.jpg")

        self.assertIsNotNone(model.begin_card_preview_request(root.node_id))
        fresh_root_card_token = model.preview_request_token(
            root.node_id, card=True,
        )
        self.assertNotEqual(old_root_card_token, fresh_root_card_token)
        with patch.object(
            model, "_preview_url", return_value="file:///stale-card.jpg"
        ):
            model.apply_card_preview(
                root.node_id,
                source,
                [object()],
                old_root_card_token,
            )
        self.assertEqual(root.card_preview_url, "")
        with patch.object(
            model, "_preview_url", return_value="file:///fresh-card.jpg"
        ):
            model.apply_card_preview(
                root.node_id,
                source,
                [object()],
                fresh_root_card_token,
            )
        self.assertEqual(root.card_preview_url, "file:///fresh-card.jpg")

    def test_refresh_gate_closes_after_user_selects_another_parent(self):
        model = WorkspaceItemModel()
        first = _loaded_tree()
        first.source = object()
        second = WorkspaceNode(
            node_id="other",
            node_type="sobject",
            search_key="demo/asset?code=OTHER",
            code="OTHER",
            title="Other",
            loaded=True,
            has_children=True,
            source=object(),
        )
        model.replace_nodes([first, second])
        section = SimpleNamespace(entry_key="assets")
        tab = SimpleNamespace(
            tab_id="tab",
            selected_node_id=first.children[0].node_id,
            workspace_model=model,
            view_mode="continious",
        )
        controller = SimpleNamespace(
            _current_section=lambda: section,
            _current_tab=lambda: tab,
            _selected_tree_owner=lambda current_model, current_tab:
                ResultTreeMixin._selected_tree_owner(
                    current_model, current_tab
                ),
        )

        self.assertTrue(ResultTreeMixin._current_tree_keeps_checkin_parent(
            controller, "assets", "tab", model, first.search_key,
        ))
        tab.selected_node_id = second.node_id
        self.assertFalse(ResultTreeMixin._current_tree_keeps_checkin_parent(
            controller, "assets", "tab", model, first.search_key,
        ))

    def test_refresh_gate_tracks_the_exact_parent_tree_instance(self):
        model = WorkspaceItemModel()
        first = _loaded_tree()
        first.source = object()
        duplicate = _loaded_tree()
        duplicate.node_id = "related-asset"
        duplicate.children[0].parent_id = duplicate.node_id
        duplicate.search_key = first.search_key
        duplicate.source = object()
        model.replace_nodes([first, duplicate])
        section = SimpleNamespace(entry_key="assets")
        tab = SimpleNamespace(
            tab_id="tab",
            selected_node_id=first.node_id,
            workspace_model=model,
            view_mode="continious",
        )
        controller = SimpleNamespace(
            _current_section=lambda: section,
            _current_tab=lambda: tab,
            _selected_tree_owner=lambda current_model, current_tab:
                ResultTreeMixin._selected_tree_owner(
                    current_model, current_tab
                ),
        )

        self.assertTrue(ResultTreeMixin._current_tree_keeps_checkin_parent(
            controller,
            "assets",
            "tab",
            model,
            first.search_key,
            first.node_id,
        ))
        tab.selected_node_id = duplicate.node_id
        self.assertFalse(ResultTreeMixin._current_tree_keeps_checkin_parent(
            controller,
            "assets",
            "tab",
            model,
            first.search_key,
            first.node_id,
        ))

    def test_abandoned_checkin_refresh_clears_loading_without_repaint(self):
        model = WorkspaceItemModel()
        root = _loaded_tree()
        model.replace_nodes([root])
        changes = []
        model.dataChanged.connect(lambda *_args: changes.append(True))

        model.set_search_key_loading(root.search_key, True)
        self.assertTrue(changes)
        changes.clear()

        model.set_search_key_loading(
            root.search_key, False, notify=False,
        )

        self.assertEqual(changes, [])
        self.assertFalse(root.loading)
        self.assertFalse(root.children[0].loading)

    def test_viewport_restore_waits_for_all_expanded_branches(self):
        tab = SimpleNamespace(
            tab_id="tab", viewport_restore_pending=True
        )
        restored = []
        controller = SimpleNamespace(
            _current_tab=lambda: tab,
            _restoring_nodes={"asset-one"},
            _restore_result_viewport=lambda current: restored.append(current),
        )

        ResultTreeMixin._restore_viewport_if_tree_idle(controller, "tab")
        self.assertEqual(restored, [])
        self.assertTrue(tab.viewport_restore_pending)

        controller._restoring_nodes.clear()
        ResultTreeMixin._restore_viewport_if_tree_idle(controller, "tab")

        self.assertEqual(restored, [tab])
        self.assertFalse(tab.viewport_restore_pending)

    def test_tab_projection_reuses_existing_model_slots(self):
        model = WorkspaceItemModel()
        removed = []
        inserted = []
        changed = []
        model.rowsRemoved.connect(lambda *_args: removed.append(True))
        model.rowsInserted.connect(lambda *_args: inserted.append(True))
        model.dataChanged.connect(lambda *_args: changed.append(True))
        model.replace_nodes([
            WorkspaceNode(
                node_id="first-a", node_type="sobject",
                search_key="demo/asset?code=FIRST_A", code="FIRST_A",
                title="First A",
            ),
            WorkspaceNode(
                node_id="first-b", node_type="sobject",
                search_key="demo/asset?code=FIRST_B", code="FIRST_B",
                title="First B",
            ),
        ])
        removed.clear()
        inserted.clear()
        changed.clear()

        model.replace_nodes([
            WorkspaceNode(
                node_id="second-a", node_type="sobject",
                search_key="demo/asset?code=SECOND_A", code="SECOND_A",
                title="Second A",
            ),
            WorkspaceNode(
                node_id="second-b", node_type="sobject",
                search_key="demo/asset?code=SECOND_B", code="SECOND_B",
                title="Second B",
            ),
        ], preserve_slots=True)

        self.assertEqual(removed, [])
        self.assertEqual(inserted, [])
        self.assertEqual(model.row_for_node("second-a"), 0)
        self.assertEqual(model.row_for_node("second-b"), 1)
        self.assertTrue(changed)

    def test_cached_projection_restores_ready_rows_without_tree_rebuild(self):
        model = WorkspaceItemModel()
        original = _loaded_tree()
        model.replace_nodes([original])
        projection = model.capture_projection()

        model.replace_nodes([
            WorkspaceNode(
                node_id="other", node_type="sobject",
                search_key="demo/asset?code=OTHER", code="OTHER",
                title="Other",
            ),
        ])
        restored = model.restore_projection(projection)

        self.assertTrue(restored)
        self.assertIs(model.node_for("asset"), original)
        self.assertEqual(model.row_for_node("asset"), 0)
        self.assertEqual(model.row_for_node("asset:process:render"), 1)
        self.assertEqual(
            model.collect_projection_tree_state(
                projection,
                "asset:process:render:snapshot:SNAPSHOT001",
            ),
            model.collect_tree_state(
                "asset:process:render:snapshot:SNAPSHOT001"
            ),
        )

    def test_live_projection_restore_emits_no_delegate_updates(self):
        model = WorkspaceItemModel()
        node = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
        )
        model.replace_nodes([node])
        projection = model.capture_projection()
        changes = []
        model.dataChanged.connect(lambda *_args: changes.append(True))

        self.assertTrue(model.restore_projection(projection))

        self.assertEqual(changes, [])
        self.assertIs(model.node_for("asset"), node)

    def test_tree_cache_omits_default_collapsed_rows(self):
        children = [
            WorkspaceNode(
                node_id=f"asset:process:{index}",
                node_type="process",
                search_key="demo/asset?code=ASSET001",
                code=f"process-{index}",
                title=f"Process {index}",
                parent_id="asset",
                loaded=True,
            )
            for index in range(2_000)
        ]
        children[250].expanded = True
        root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            expanded=True,
            has_children=True,
            loaded=True,
            children=children,
        )
        model = WorkspaceItemModel()
        model.replace_nodes([root])

        state = model.collect_tree_state(children[1_750].node_id)

        self.assertEqual(set(state), {0})
        self.assertEqual(set(state[0]["s"]), {250, 1_750})
        self.assertTrue(state[0]["s"][250]["d"]["e"])
        self.assertTrue(state[0]["s"][1_750]["d"]["s"])

    def test_lazy_refresh_restores_expanded_process_rows_and_selection(self):
        model = WorkspaceItemModel()
        original = _loaded_tree()
        model.replace_nodes([original])
        selected_snapshot_id = original.children[0].children[0].node_id
        state = model.collect_tree_state(selected_snapshot_id)

        refreshed_root = WorkspaceNode(
            node_id="asset",
            node_type="sobject",
            search_key="demo/asset?code=ASSET001",
            code="ASSET001",
            title="Asset",
            has_children=True,
            loaded=False,
        )
        model.replace_nodes([refreshed_root])
        pending, restored_selection = model.apply_tree_state(state)

        self.assertEqual(pending, ["asset"])
        self.assertEqual(restored_selection, "")

        prepared = _loaded_tree()
        prepared.expanded = False
        prepared.children[0].expanded = False
        self.assertTrue(model.apply_loaded_node("asset", prepared))
        model.toggle_node("asset")
        pending, restored_selection = model.apply_node_restore_state("asset")

        self.assertEqual(pending, [])
        self.assertEqual(restored_selection, selected_snapshot_id)
        self.assertTrue(model.node_for("asset:process:render").expanded)
        self.assertGreaterEqual(model.row_for_node(selected_snapshot_id), 0)


if __name__ == "__main__":
    unittest.main()
