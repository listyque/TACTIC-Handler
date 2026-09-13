from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
QML_ROOT = ROOT / "thlib" / "ui" / "qml"
SMALL_PIXEL_FONT = re.compile(
    r"font\.pixelSize:\s*(?:7|8|9|10|11)(?:\D|$)"
)


class TypographyPolicyTests(unittest.TestCase):
    def test_small_text_uses_shared_point_scale(self) -> None:
        offenders: list[str] = []
        for path in QML_ROOT.rglob("*.qml"):
            source = path.read_text(encoding="utf-8")
            if SMALL_PIXEL_FONT.search(source):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(
            offenders,
            [],
            "Small literal pixel fonts bypass the shared DPI-safe scale: "
            + ", ".join(offenders),
        )

    def test_typography_scale_has_readable_96_dpi_floor(self) -> None:
        source = (QML_ROOT / "Typography.js").read_text(encoding="utf-8")
        values = {
            name: float(value)
            for name, value in re.findall(
                r"var\s+(micro|caption|label|body|bodyLarge)\s*=\s*([0-9.]+)",
                source,
            )
        }
        self.assertGreaterEqual(values["micro"], 8.0)
        self.assertEqual(
            sorted(values.values()),
            list(values.values()),
            "Typography scale must increase monotonically",
        )

    def test_scalable_renderer_and_resize_layer_policy(self) -> None:
        source = (ROOT / "thlib/ui/application.py").read_text(encoding="utf-8")
        self.assertIn("TextRenderType.QtTextRendering", source)
        self.assertNotIn("TextRenderType.NativeTextRendering", source)

        dock_source = (QML_ROOT / "DockPanel.qml").read_text(encoding="utf-8")
        self.assertNotIn("layer.enabled:", dock_source)
        self.assertNotIn("layer.effect:", dock_source)
        self.assertNotIn("Qt5Compat.GraphicalEffects", dock_source)
        self.assertIn("clip: true", dock_source)


if __name__ == "__main__":
    unittest.main()
