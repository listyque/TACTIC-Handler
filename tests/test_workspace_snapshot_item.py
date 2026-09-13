from __future__ import annotations

from pathlib import Path
import unittest

from thlib.ui.workspace_models.results import WorkspaceItemModel


ROOT = Path(__file__).resolve().parents[1]


class WorkspaceSnapshotItemTests(unittest.TestCase):
    def test_snapshot_chips_include_legacy_maya_product_version(self):
        class File:
            @staticmethod
            def get_meta_file_object():
                return None

            @staticmethod
            def get_metadata():
                return {"app_info": {"p": "Autodesk Maya 2025"}}

        self.assertEqual(
            WorkspaceItemModel._snapshot_chips(File(), "publish"),
            [
                {"label": "Context", "value": "publish", "url": ""},
                {
                    "label": "Maya",
                    "value": "Autodesk Maya 2025",
                    "url": "",
                },
            ],
        )

    def test_snapshot_uses_native_pretty_and_simple_timestamp_values(self):
        class Snapshot:
            timestamp_calls = []

            @staticmethod
            def get_snapshot():
                return {
                    "code": "SNAPSHOT00001",
                    "version": 12,
                    "timestamp": "2026-08-23 10:52:28.123456",
                }

            @staticmethod
            def get_search_key():
                return "sthpw/snapshot?code=SNAPSHOT00001"

            @staticmethod
            def get_files_objects():
                return []

            @classmethod
            def get_timestamp(cls, **options):
                cls.timestamp_calls.append(options)
                if options.get("pretty"):
                    return "2 hours ago"
                if options.get("simple"):
                    return "2026 August 23 10:52:28"
                return ""

            @staticmethod
            def is_latest():
                return True

            @staticmethod
            def is_versionless():
                return False

        model = WorkspaceItemModel()
        snapshot = Snapshot()
        node = model._make_snapshot_node(
            snapshot,
            process_name="publish",
            context_name="publish",
            depth=1,
            accent="#607d8b",
            parent_id="asset:1",
        )

        self.assertEqual(node.timestamp, "2026-08-23 10:52:28")
        self.assertEqual(node.timestamp_pretty, "2 hours ago")
        self.assertEqual(node.timestamp_simple, "2026 August 23 10:52:28")
        self.assertEqual(
            Snapshot.timestamp_calls,
            [{"pretty": True}, {"simple": True}],
        )
        self.assertEqual(
            model.roleNames()[model.TimestampPrettyRole], b"timestampPretty"
        )
        self.assertEqual(
            model.roleNames()[model.TimestampSimpleRole], b"timestampSimple"
        )

    def test_snapshot_size_uses_legacy_two_decimal_precision(self):
        self.assertEqual(
            WorkspaceItemModel._snapshot_size(4_300_800),
            "4.10 MB",
        )
        self.assertEqual(WorkspaceItemModel._snapshot_size(512), "512.00 B")

    def test_snapshot_item_keeps_legacy_information_hierarchy(self):
        source = (
            ROOT / "thlib" / "ui" / "qml" / "WorkspaceResultItem.qml"
        ).read_text(encoding="utf-8")
        start = source.index("id: snapshotBodyComponent")
        end = source.index("id: processBodyComponent", start)
        snapshot = source[start:end]

        self.assertNotIn("contentTrailingReserve", snapshot)
        self.assertNotIn('opacity: nodeType === "snapshot"', source)
        self.assertIn("Controls.StatusChip {", snapshot)
        self.assertIn('objectName: "workspaceSnapshotSizeBadge"', snapshot)
        self.assertIn(
            'objectName: "workspaceCompactSnapshotSizeBadge"', source
        )
        self.assertIn('objectName: "workspaceSnapshotDate"', snapshot)
        self.assertIn("root.timestampPretty", snapshot)
        self.assertIn("root.timestampSimple", snapshot)
        self.assertNotIn('root.timestamp.replace(" ", "\\n")', snapshot)
        self.assertNotIn("orientation: Gradient.Horizontal", snapshot)
        self.assertIn('qsTr("File Offline")', snapshot)
        self.assertIn('text: qsTr("Latest")', snapshot)
        self.assertIn("font.italic: true", snapshot)
        self.assertIn("root.theme.primaryText", snapshot)
        self.assertIn("id: snapshotAuthorMetrics", snapshot)
        self.assertIn("snapshotAuthorMetrics.advanceWidth", snapshot)
        self.assertNotIn("Math.min(implicitWidth", snapshot)


if __name__ == "__main__":
    unittest.main()
