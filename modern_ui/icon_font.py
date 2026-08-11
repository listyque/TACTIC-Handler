"""Load the Font Awesome assets already bundled with TACTIC-Handler."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtGui import QFontDatabase


def _read_charmap(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as stream:
        charmap = json.load(stream)
    return {
        name: chr(int(codepoint, 16))
        for name, codepoint in charmap.items()
    }


def fontawesome_assets(
    project_root: Path,
) -> tuple[dict[str, str], str, dict[str, str], str]:
    fonts_dir = project_root / "thlib" / "side" / "qtawesome" / "fonts"
    solid_path = fonts_dir / "fontawesome5-solid-webfont.ttf"
    regular_path = fonts_dir / "fontawesome5-regular-webfont.ttf"
    solid_glyphs = _read_charmap(
        fonts_dir / "fontawesome5-solid-webfont-charmap.json"
    )
    regular_glyphs = _read_charmap(
        fonts_dir / "fontawesome5-regular-webfont-charmap.json"
    )

    def register_font(path: Path) -> str:
        font_id = QFontDatabase.addApplicationFont(str(path))
        families = (
            QFontDatabase.applicationFontFamilies(font_id)
            if font_id >= 0 else []
        )
        return families[0] if families else "Segoe UI"

    return (
        solid_glyphs,
        register_font(solid_path),
        regular_glyphs,
        register_font(regular_path),
    )
