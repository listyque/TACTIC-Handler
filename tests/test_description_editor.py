import unittest

from thlib.ui.workspace_models.state import WorkspaceState


class _SObject:
    def __init__(self, code, description):
        self.info = {"code": code, "description": description}

    def get_info(self):
        return self.info

    def get_search_key(self):
        return f"demo/asset?code={self.info['code']}"


class _Snapshot:
    def __init__(self, code, description):
        self.info = {"code": code, "description": description}

    def get_snapshot(self):
        return self.info

    def get_search_key(self):
        return f"sthpw/snapshot?code={self.info['code']}"


class DescriptionEditorStateTests(unittest.TestCase):
    def setUp(self):
        self.state = WorkspaceState()

    def test_edit_is_saved_only_after_explicit_commit(self):
        target = _SObject("ASSET001", "Original")
        requested = []
        self.state.description_save_requested.connect(requested.append)

        self.state.set_description_target(target, "sobject", "Asset")
        self.state.begin_description_edit()
        self.state.set_description("Changed")

        self.assertTrue(self.state.descriptionDirty)
        self.assertEqual(requested, [])

        self.state.commit_description()
        self.assertEqual(requested, ["Changed"])
        self.assertTrue(self.state.descriptionSaving)

        self.state.description_save_succeeded(
            target.get_search_key(), "Changed"
        )
        self.assertFalse(self.state.descriptionDirty)
        self.assertFalse(self.state.descriptionSaving)

    def test_cancel_restores_server_value(self):
        target = _SObject("ASSET001", "Original")
        self.state.set_description_target(target, "sobject", "Asset")
        self.state.begin_description_edit()
        self.state.set_description("Discard me")

        self.state.cancel_description_edit()

        self.assertEqual(self.state.description, "Original")
        self.assertFalse(self.state.descriptionEditing)
        self.assertFalse(self.state.descriptionDirty)

    def test_pinned_text_survives_selection_change(self):
        first = _SObject("ASSET001", "First")
        second = _SObject("ASSET002", "Second")
        self.state.set_description_target(first, "sobject", "First asset")
        self.state.begin_description_edit()
        self.state.set_description("Check-in note")
        self.state.freeze_description()

        self.state.set_description_target(second, "sobject", "Second asset")

        self.assertTrue(self.state.descriptionPinned)
        self.assertEqual(self.state.checkinDescription, "Check-in note")
        self.assertEqual(self.state.description, "Check-in note")

        self.state.unfreeze_description()
        self.assertEqual(self.state.description, "Second")

    def test_snapshot_has_its_own_save_target(self):
        snapshot = _Snapshot("SNAPSHOT001", "Snapshot description")
        self.state.set_description_target(
            snapshot, "snapshot", "Snapshot v001"
        )

        self.assertTrue(self.state.descriptionCanSave)
        self.assertEqual(self.state.description, "Snapshot description")
        self.assertEqual(
            self.state._description_target_key,
            "sthpw/snapshot?code=SNAPSHOT001",
        )


if __name__ == "__main__":
    unittest.main()
