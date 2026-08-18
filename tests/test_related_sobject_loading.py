import unittest

from modern_ui.workspace_models.results import WorkspaceItemModel
from modern_ui.workspace_models.results_types import WorkspaceNode


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
