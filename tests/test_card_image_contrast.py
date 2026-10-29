"""Real card paint keeps object text readable over white and black previews."""

import os
import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage, QColor
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
import tests.test_frame_table as frames
import tests.test_workspace_result_item as items


def luminance(color):
    channels = [color.redF(), color.greenF(), color.blueF()]
    channels = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return sum(
        value * weight for value, weight in zip(channels, [0.2126, 0.7152, 0.0722])
    )


class CardImageContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = frames.gui_test_application()

    create = frames.FrameTableTests.create
    close = frames.FrameTableTests.close

    def test_real_object_card_text_contrast_on_light_and_dark_images(self):
        captures = []
        with TemporaryDirectory() as temporary:
            for image_color in ("white", "black"):
                path = Path(temporary) / (image_color + ".png")
                image = QImage(16, 16, QImage.Format_RGB32)
                image.fill(QColor(image_color))
                self.assertTrue(image.save(str(path)))
                for dark in (True, False):
                    for selected in (False, True):
                        with self.subTest(
                            image=image_color, dark=dark, selected=selected
                        ):
                            values = items.WorkspaceResultItemTests.card_properties(
                                None,
                                width=260,
                                height=244,
                                title="Workshop",
                                subtitle="Bright preview and readable description",
                                selected=selected,
                                cardPreviewUrl=QUrl.fromLocalFile(str(path)).toString(),
                                previewRevealed=True,
                            )
                            values.pop("theme")
                            values.pop("width")
                            values.pop("height")
                            window, card = self.create(
                                "WorkspaceCard.qml",
                                values,
                                width=260,
                                height=244,
                                context=dict(
                                    appController=items._WorkspaceAppController()
                                ),
                            )
                            card.property("theme").setProperty("dark", dark)
                            source = card.findChild(QQuickItem, "previewSourceImage")
                            preview = source.parentItem()
                            while preview.metaObject().indexOfProperty("sourcePixelWidth") < 0:
                                preview = preview.parentItem()
                            deadline = time.monotonic() + 2
                            while (
                                not preview.property("sourcePixelWidth")
                                and time.monotonic() < deadline
                            ):
                                QTest.qWait(10)
                            self.assertGreater(preview.property("sourcePixelWidth"), 0)
                            frames.frame(window)
                            painted = window.grabWindow()
                            ratio = painted.width() / 260
                            background = painted.pixelColor(
                                round(250 * ratio), round(78 * ratio)
                            )
                            for name in (
                                "workspaceCardTitle",
                                "workspaceCardDescription",
                            ):
                                label = card.findChild(QQuickItem, name)
                                first, second = sorted(
                                    (
                                        luminance(label.property("color")),
                                        luminance(background),
                                    )
                                )
                                self.assertGreaterEqual(
                                    (second + 0.05) / (first + 0.05), 4.5
                                )
                            foreground = card.findChild(
                                QQuickItem, "workspaceCardDescription"
                            ).property("color")
                            captures.append(
                                dict(
                                    name=f"{image_color}-{dark}-{selected}",
                                    text=[
                                        foreground.red(),
                                        foreground.green(),
                                        foreground.blue(),
                                    ],
                                )
                            )
                            output = os.environ.get("CARD_CONTRAST_OUTPUT")
                            if output:
                                target = Path(output)
                                target.mkdir(parents=True, exist_ok=True)
                                painted.save(
                                    str(
                                        target
                                        / f"native-{image_color}-{dark}-{selected}.png"
                                    )
                                )
                            self.doCleanups()
        if os.environ.get("CARD_CONTRAST_OUTPUT"):
            (Path(os.environ["CARD_CONTRAST_OUTPUT"]) / "native.json").write_text(
                json.dumps(captures), encoding="utf-8"
            )


if __name__ == "__main__":
    unittest.main()
