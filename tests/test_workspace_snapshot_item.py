from __future__ import annotations

from pathlib import Path
import unittest

from modern_ui.workspace_models.results import WorkspaceItemModel


ROOT = Path(__file__).resolve().parents[1]


class WorkspaceSnapshotItemTests(unittest.TestCase):
    def test_snapshot_size_uses_legacy_two_decimal_precision(self):
        self.assertEqual(
            WorkspaceItemModel._snapshot_size(4_300_800),
            "4.10 MB",
        )
        self.assertEqual(WorkspaceItemModel._snapshot_size(512), "512.00 B")

    def test_snapshot_item_keeps_legacy_information_hierarchy(self):
        source = (
            ROOT / "modern_ui" / "qml" / "WorkspaceResultItem.qml"
        ).read_text(encoding="utf-8")
        start = source.index("id: snapshotBodyComponent")
        end = source.index("id: processBodyComponent", start)
        snapshot = source[start:end]

        self.assertNotIn("contentTrailingReserve", snapshot)
        self.assertNotIn('opacity: nodeType === "snapshot"', source)
        self.assertIn("id: snapshotSizeBackdrop", snapshot)
        self.assertIn("orientation: Gradient.Horizontal", snapshot)
        self.assertIn('qsTr("File Offline")', snapshot)
        self.assertIn('text: qsTr("Latest")', snapshot)
        self.assertIn("font.italic: true", snapshot)
        self.assertIn("root.theme.primaryText", snapshot)


if __name__ == "__main__":
    unittest.main()