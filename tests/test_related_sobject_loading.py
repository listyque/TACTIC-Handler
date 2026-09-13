import unittest
from unittest.mock import patch

from thlib.ui.workspace_models.results import WorkspaceItemModel
from thlib.ui.workspace_models.results_types import WorkspaceNode


class _SType:
    @staticmethod
    def get_stype_color(fmt="hex"):
        return "#42a5f5"

    @staticmethod
    def get_definition(_view):
        return []


class _RelatedSObject:
    def __init__(self):
        self.info = {
            "code": "SHOT001",
            "name": "Shot 001",
            "description": "Related shot",
        }

    def get_info(self):
        return self.info

    @staticmethod
    def get_search_key():
        return "asset/shot?code=SHOT001"

    def get_title(self):
        return self.info["name"]

    @staticmethod
    def get_stype():
        return _SType()

    @staticmethod
    def get_snapshots(_process=None):
        return None


class _ParentSObject:
    def __init__(self, related):
        self.related = related
        self.request = {}

    def get_related_sobjects(self, **kwargs):
        self.request = dict(kwargs)
        return [self.related]

    @staticmethod
    def get_stype():
        return _SType()


class _EmptyParentSObject(_ParentSObject):
    def __init__(self):
        super().__init__(None)

    def get_related_sobjects(self, **kwargs):
        self.request = dict(kwargs)
        return []


class RelatedSObjectLoadingTests(unittest.TestCase):
    def test_same_target_instance_relations_keep_distinct_identities(self):
        model = WorkspaceItemModel()
        first_definition = {
            "from": "demo/asset",
            "relationship": "instance",
            "instance_type": "asset_in_scene",
        }
        second_definition = {
            "from": "demo/asset",
            "relationship": "instance",
            "instance_type": "reference_in_scene",
        }
        first = WorkspaceNode(
            node_id="root:relation:" + model._relation_node_key(
                first_definition, "demo/asset"
            ),
            node_type="relation",
            search_key="demo/scene?code=SCENE001",
            title="Assets",
            code="demo/asset",
            relationship="instance",
            relation={"definition": first_definition},
        )
        second = WorkspaceNode(
            node_id="root:relation:" + model._relation_node_key(
                second_definition, "demo/asset"
            ),
            node_type="relation",
            search_key="demo/scene?code=SCENE001",
            title="References",
            code="demo/asset",
            relationship="instance",
            relation={"definition": second_definition},
        )

        result = model._deduplicate_siblings([first, second])
        self.assertEqual(len(result), 2)
        self.assertNotEqual(first.node_id, second.node_id)

    def test_root_load_exposes_link_for_native_instance_relation(self):
        relation_definition = {
            "from": "demo/asset",
            "relationship": "instance",
            "instance_type": "asset_in_scene",
        }

        class ChildSType(_SType):
            @staticmethod
            def get_pretty_name():
                return "Assets"

        child_stype = ChildSType()

        class Project:
            stypes = {"demo/asset": child_stype}

        class RootSType(_SType):
            @staticmethod
            def get_schema():
                return type("Schema", (), {
                    "children": [relation_definition]
                })()

            @staticmethod
            def get_project():
                return Project()

            @staticmethod
            def get_pipeline():
                return {}

        root_stype = RootSType()

        class RootSObject:
            @staticmethod
            def get_stype():
                return root_stype

            @staticmethod
            def update_snapshots(**_kwargs):
                return None

            @staticmethod
            def is_snapshots_need_update():
                return False

            @staticmethod
            def get_project():
                return None

            @staticmethod
            def get_pipeline_code():
                return ""

            @staticmethod
            def get_process(_process):
                return None

            @staticmethod
            def get_notes_count():
                return {}

            @staticmethod
            def get_tasks_count():
                return {}

            @staticmethod
            def get_all_processes():
                return {}

            @staticmethod
            def set_notes_count(*_args):
                return None

            @staticmethod
            def set_tasks_count(*_args):
                return None

            @staticmethod
            def get_search_key():
                return "demo/scene?code=SCENE001"

            @staticmethod
            def get_related_sobjects_tel_string(
                _child_stype, _parent_stype, path="child"
            ):
                return "@SOBJECT(demo/asset['scene_code','SCENE001'])"

        root = WorkspaceNode(
            node_id="scene-root",
            node_type="sobject",
            search_key="demo/scene?code=SCENE001",
            code="SCENE001",
            title="Scene 001",
            accent="#445566",
            source=RootSObject(),
        )
        model = WorkspaceItemModel()

        with patch(
            "thlib.tactic_classes.get_notes_count",
            return_value={
                "notes": {},
                "tasks": {},
                "stypes": {"asset_in_scene": 0},
            },
        ) as get_counts:
            model._load_root(root, register=False)

        self.assertEqual(get_counts.call_args.args[2], [{
            "key": "asset_in_scene",
            "searchType": "demo/asset",
            "expression": "@SOBJECT(demo/asset['scene_code','SCENE001'])",
        }])

        relation = next(
            child for child in root.children
            if child.node_type == "relation"
        )
        self.assertTrue(relation.linkable_relation)
        self.assertIn(
            "link_related",
            [item["command"] for item in model._controls_for(relation)],
        )



    def test_children_keep_native_sobject_as_preview_source(self):
        related = _RelatedSObject()
        parent = _ParentSObject(related)
        child_stype = _SType()
        relation = WorkspaceNode(
            node_id="root:relation:asset/shot",
            node_type="relation",
            search_key="asset/asset?code=ASSET001",
            code="asset/shot",
            title="Shots",
            source=parent,
            relation={
                "definition": {
                    "from": "asset/shot",
                    "relationship": "code",
                },
                "stype": child_stype,
            },
        )
        model = WorkspaceItemModel()

        model._load_relation(relation, register=False)

        self.assertEqual(len(relation.children), 1)
        child = relation.children[0]
        self.assertIs(child.source, related)
        self.assertIs(child.preview_source, related)
        self.assertEqual(child.search_key, related.get_search_key())
        self.assertIs(parent.request["get_all_snapshots"], True)
        self.assertTrue(relation.has_children)
        controls = model._controls_for(relation)
        add_control = next(
            item for item in controls if item["command"] == "add_related"
        )
        self.assertEqual(add_control["icon"], "add")
        self.assertFalse(add_control["active"])

    def test_link_control_requires_validated_instance_relation(self):
        model = WorkspaceItemModel()
        false_positive = WorkspaceNode(
            node_id="invalid-instance", node_type="relation",
            search_key="asset/asset?code=ASSET001", code="asset/shot",
            title="Shots", relationship="instance",
            linkable_relation=False,
        )
        valid = WorkspaceNode(
            node_id="valid-instance", node_type="relation",
            search_key="asset/asset?code=ASSET001", code="asset/shot",
            title="Shots", relationship="instance",
            linkable_relation=True,
        )

        self.assertNotIn(
            "link_related",
            [item["command"] for item in model._controls_for(false_positive)],
        )
        self.assertIn(
            "link_related",
            [item["command"] for item in model._controls_for(valid)],
        )

    def test_self_instance_relation_uses_separate_instance_count(self):
        model = WorkspaceItemModel()
        direct = WorkspaceNode(
            node_id="direct-assets",
            node_type="relation",
            search_key="asset/asset?code=ASSET002",
            code="asset/asset",
            title="Assets",
            relationship="code",
            has_children=True,
        )
        instance = WorkspaceNode(
            node_id="linked-assets",
            node_type="relation",
            search_key="asset/asset?code=ASSET002",
            code="asset/asset",
            title="Linked assets",
            relationship="instance",
            has_children=True,
            relation={
                "definition": {
                    "from": "asset/asset",
                    "relationship": "instance",
                    "instance_type": "asset/asset_in_asset",
                },
            },
        )

        self.assertEqual(
            model._relation_count_key(direct), "asset/asset"
        )
        self.assertEqual(
            model._relation_count_key(instance), "asset/asset_in_asset"
        )
        model._apply_relation_counts(
            [direct, instance],
            {
                "asset/asset": 1,
                "asset/asset_in_asset": 0,
            },
        )

        self.assertEqual(direct.child_count, 1)
        self.assertTrue(direct.has_children)
        self.assertEqual(instance.child_count, 0)
        self.assertFalse(instance.has_children)

        model._apply_relation_counts(
            [instance], {"asset/asset_in_asset": 2}
        )

        self.assertEqual(instance.child_count, 2)
        self.assertTrue(instance.has_children)

    def test_empty_relation_stops_advertising_expandable_children(self):
        parent = _EmptyParentSObject()
        relation = WorkspaceNode(
            node_id="root:relation:asset/shot",
            node_type="relation",
            search_key="asset/asset?code=ASSET001",
            code="asset/shot",
            title="Shots",
            source=parent,
            has_children=True,
            relation={
                "definition": {
                    "from": "asset/shot",
                    "relationship": "code",
                },
                "stype": _SType(),
            },
        )
        model = WorkspaceItemModel()

        model._load_relation(relation, register=False)

        self.assertTrue(relation.loaded)
        self.assertEqual(relation.child_count, 0)
        self.assertEqual(relation.children, [])
        self.assertFalse(relation.has_children)

    def test_empty_relation_state_is_applied_to_visible_node(self):
        parent = _EmptyParentSObject()
        relation = WorkspaceNode(
            node_id="root:relation:asset/shot",
            node_type="relation",
            search_key="asset/asset?code=ASSET001",
            code="asset/shot",
            title="Shots",
            source=parent,
            has_children=True,
            relation={
                "definition": {
                    "from": "asset/shot",
                    "relationship": "code",
                },
                "stype": _SType(),
            },
        )
        model = WorkspaceItemModel()
        model.replace_nodes([relation])

        node_id, loaded, prepared = model.load_node(relation.node_id)

        self.assertTrue(loaded)
        self.assertTrue(model.apply_loaded_node(node_id, prepared))
        self.assertFalse(model.node_for(node_id).has_children)
        self.assertEqual(
            model.data(model.index(0, 0), model.HasChildrenRole),
            False,
        )


if __name__ == "__main__":
    unittest.main()
