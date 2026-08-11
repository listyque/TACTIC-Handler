import unittest
from unittest.mock import patch

from modern_ui.workspace_models.results import WorkspaceItemModel
from modern_ui.workspace_models.state import WorkspaceState
from modern_ui.workspace_models.results_types import WorkspaceNode


class _File:
    def __init__(self, code, url=""):
        self._code = code
        self.url = url

    def get_code(self):
        return self._code

    def get_filename_with_ext(self):
        return "preview.png"

    def get_abs_path(self):
        return "C:/repository/preview.png"

    def get_full_abs_path(self):
        return self.get_abs_path()

    def get_file_size(self):
        return 1024

    def get_base_type(self):
        return "file"

    def get_type(self):
        return "icon" if self.url else "main"

    def get_web_preview(self):
        return self

    def get_icon_preview(self):
        return self

    def get_meta_file_object(self):
        return None


class _Snapshot:
    def __init__(self, code, file_object, preview_objects=None):
        self._code = code
        self._file = file_object
        self._preview_objects = list(preview_objects or [])

    def get_code(self):
        return self._code

    def get_snapshot(self):
        return {"code": self._code, "version": 1, "repo": "base"}

    def get_files_objects(self, group_by=None):
        if group_by == "type":
            return {"main": [self._file], "file": [self._file]}
        return [self._file]

    def get_previewable_files_objects(self):
        return list(self._preview_objects)


class _Node:
    def __init__(self, node_id, snapshot):
        self.node_id = node_id
        self.source = snapshot
        self.version = "v001"


class SnapshotBrowserModelTests(unittest.TestCase):
    def test_duplicate_snapshot_and_file_codes_are_ignored(self):
        state = WorkspaceState()
        file_object = _File("FILE00001")
        snapshot = _Snapshot("SNAPSHOT00001", file_object)

        state._build_snapshot_browser_models([
            _Node("snapshot-one", snapshot),
            _Node("snapshot-copy", snapshot),
        ])

        rows = state.snapshot_file_model._records
        self.assertEqual(
            1,
            sum(row["rowType"] == "snapshot" for row in rows),
        )
        self.assertEqual(
            1,
            sum(row["rowType"] == "file" for row in rows),
        )

    def test_icon_preview_is_first_without_duplicating_selected_preview(self):
        state = WorkspaceState()
        selected_file = _File("FILE00001", "file:///selected.png")
        icon_file = _File("FILE00002", "file:///icon.png")
        duplicate_icon = _File("FILE00003", "file:///icon.png")
        selected = _Snapshot(
            "SNAPSHOT00001", selected_file,
            [selected_file, duplicate_icon],
        )
        icon = _Snapshot("SNAPSHOT00002", icon_file, [icon_file])

        with patch.object(
            state._preview_helper, "_preview_url",
            side_effect=lambda file_object: file_object.url,
        ):
            state._build_snapshot_browser_models(
                [_Node("selected", selected)],
                [_Node("icon", icon)],
            )

        previews = state.snapshot_preview_model._records
        self.assertEqual(previews[0]["url"], "file:///icon.png")
        self.assertEqual(
            [item["url"] for item in previews].count("file:///icon.png"),
            1,
        )
        self.assertEqual(previews[1]["url"], "file:///selected.png")

    def test_task_projection_loads_full_snapshot_data_once_when_needed(self):
        class Source:
            def __init__(self):
                self.processes = {"icon": object()}
                self.update_count = 0

            def get_all_processes(self):
                return self.processes

            def update_snapshots(self, order_bys=None):
                self.update_count += 1
                self.processes = {
                    "icon": object(), "model": object(),
                }

        source = Source()
        model = WorkspaceItemModel()

        def snapshot_nodes(process, *_args, **_kwargs):
            return [WorkspaceNode(
                node_id=process,
                node_type="snapshot",
                search_key="snapshot-" + process,
                code="SNAPSHOT-" + process,
                title=process,
                process=process,
                context="model/main" if process == "model" else "icon",
                source=object(),
            )]

        with patch.object(model, "_snapshot_nodes", snapshot_nodes):
            selected, icons = model.snapshot_nodes_for_source(
                source, "prod/asset?code=ASSET001",
                "model", "model/main",
            )

        self.assertEqual(source.update_count, 1)
        self.assertEqual([node.process for node in selected], ["model"])
        self.assertEqual([node.process for node in icons], ["icon"])


if __name__ == "__main__":
    unittest.main()
