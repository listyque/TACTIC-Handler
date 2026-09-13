"""Load and expose the icon fonts bundled with TACTIC-Handler."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QObject, Property, Slot
from PySide6.QtGui import QFontDatabase


_ICON_LIBRARY_SETS = (
    {"value": "fontawesome-solid", "label": "Font Awesome Solid"},
    {"value": "fontawesome-outline", "label": "Font Awesome Outline"},
    {"value": "material-design", "label": "Material Design Icons"},
    {"value": "fluent-regular", "label": "Fluent Regular"},
    {"value": "fluent-filled", "label": "Fluent Filled"},
)

_MATERIAL_SEMANTIC_NAMES = {
    "account", "account-group", "account-multiple-plus", "account-plus",
    "alert", "alert-circle", "archive", "arrow-down",
    "arrow-expand-all", "arrow-left", "arrow-right", "arrow-up",
    "briefcase", "bug", "cached", "calendar-check", "calendar-month",
    "calendar-today", "camera", "chart-gantt",
    "chart-timeline-variant", "check", "check-all", "check-circle",
    "checkbox-blank-circle", "checkbox-marked-circle",
    "checkbox-multiple-marked-outline", "chevron-down", "chevron-left",
    "chevron-right", "chevron-up", "circle-double", "close",
    "close-circle", "cloud", "cloud-download", "cloud-sync",
    "cloud-upload", "cog", "cogs", "comment", "content-copy", "content-cut",
    "content-duplicate", "content-paste", "content-save", "cube",
    "cube-scan", "database", "delete", "delete-forever",
    "delete-sweep", "dots-horizontal", "dots-vertical", "drag",
    "code-block-tags", "drag-horizontal", "file", "file-document-plus",
    "file-tree", "filter", "folder",
    "folder-open", "folder-plus", "folder-star", "format-font-size-decrease",
    "format-header-1", "format-header-2", "format-header-3",
    "format-header-4", "format-header-5", "format-header-6",
    "format-list-bulleted", "format-paragraph", "format-quote-open",
    "forum", "group", "harddisk", "help", "history", "image",
    "image-edit", "image-multiple", "inbox", "key", "lan-connect",
    "language-javascript", "language-python", "layers", "link",
    "link-off", "logout", "magnify-plus", "message", "message-text",
    "minus", "movie", "note-text", "open-in-new", "palette", "paperclip",
    "phone", "picture-in-picture-bottom-right", "play", "playlist-plus",
    "plus-box", "priority-high", "publish", "radiobox-blank", "redo",
    "refresh", "rename-box", "reply", "restart", "select-all", "send",
    "server", "settings", "shape", "shape-outline", "share",
    "shield-account", "sort-alphabetical-ascending",
    "sort-alphabetical-descending", "stop", "subdirectory-arrow-right",
    "swap-horizontal", "sync", "tab", "table", "theme-light-dark",
    "timer-sand", "tune", "undo", "update", "view-agenda",
    "view-column", "view-grid", "view-list", "view-sequential",
    "window-restore", "wrap", "xml",
    "account-circle", "account-cog", "access-point", "alarm-plus",
    "bell", "book-open", "calendar", "calendar-clock", "chart-bar",
    "chart-donut", "clipboard-check", "clipboard-plus", "clipboard-text",
    "code-tags", "cog-refresh", "console", "contacts", "email",
    "emoticon", "eye", "filter-off", "flag", "format-font", "hub",
    "image-plus", "information", "lightning-bolt", "lock",
    "lock-open-variant", "login", "magnify", "magnify-minus", "memory",
    "mouse", "note-edit", "pencil", "pin", "play-box-multiple", "plus",
    "pulse", "routes", "ruler-square", "source-branch", "speedometer",
    "sync-alert", "tag-multiple", "text-box", "translate", "upload",
    "view-dashboard-edit", "view-stream",
}


def _read_charmap(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8") as stream:
        charmap = json.load(stream)
    return {
        name: chr(
            int(codepoint, 16)
            if isinstance(codepoint, str)
            else int(codepoint)
        )
        for name, codepoint in charmap.items()
    }


def _register_font(path: Path) -> str:
    font_id = QFontDatabase.addApplicationFont(str(path))
    families = (
        QFontDatabase.applicationFontFamilies(font_id)
        if font_id >= 0 else []
    )
    return families[0] if families else "Segoe UI"


def fontawesome_assets(
    project_root: Path,
) -> tuple[dict[str, str], str, dict[str, str], str]:
    fonts_dir = project_root / "thlib" / "ui" / "assets" / "fonts"
    solid_path = fonts_dir / "fontawesome5-solid-webfont.ttf"
    regular_path = fonts_dir / "fontawesome5-regular-webfont.ttf"
    solid_glyphs = _read_charmap(
        fonts_dir / "fontawesome5-solid-webfont-charmap.json"
    )
    regular_glyphs = _read_charmap(
        fonts_dir / "fontawesome5-regular-webfont-charmap.json"
    )

    return (
        solid_glyphs,
        _register_font(solid_path),
        regular_glyphs,
        _register_font(regular_path),
    )


def material_design_icon_assets(
    project_root: Path,
    *,
    complete: bool = False,
) -> tuple[dict[str, str], str]:
    """Load the bundled Material Design icon font.

    The shared QML icon facade can select this complete vocabulary as a user
    preference while retaining Font Awesome fallbacks for project-specific
    semantic names.
    """

    fonts_dir = project_root / "thlib" / "ui" / "assets" / "fonts"
    font_path = fonts_dir / "materialdesignicons-webfont.ttf"
    glyphs = _read_charmap(
        fonts_dir / "materialdesignicons-webfont-charmap.json"
    )
    family = _register_font(font_path)
    if complete:
        return glyphs, family

    return material_design_semantic_glyphs(glyphs), family


def material_design_semantic_glyphs(
    glyphs: dict[str, str],
) -> dict[str, str]:
    """Keep repeated MaterialIcon delegates on a compact semantic map."""

    return {
        name: glyphs[name]
        for name in _MATERIAL_SEMANTIC_NAMES
        if name in glyphs
    }


def fluent_system_icon_assets(
    project_root: Path,
) -> tuple[dict[str, str], dict[str, str], str]:
    """Load canonical Regular and Filled names from Fluent Resizable."""

    fonts_dir = project_root / "thlib" / "ui" / "assets" / "fonts"
    font_path = fonts_dir / "fluent-system-icons-resizable.ttf"
    raw_glyphs = _read_charmap(
        fonts_dir / "fluent-system-icons-resizable.json"
    )
    glyphs = {"regular": {}, "filled": {}}
    prefix = "ic_fluent_"
    for raw_name, glyph in raw_glyphs.items():
        if not raw_name.startswith(prefix):
            continue
        for style in glyphs:
            suffix = f"_20_{style}"
            if raw_name.endswith(suffix):
                name = raw_name[len(prefix):-len(suffix)].replace("_", "-")
                glyphs[style][name] = glyph
                break
    return glyphs["regular"], glyphs["filled"], _register_font(font_path)


class IconFontCatalog(QObject):
    """Lazy searchable access to complete icon maps for picker surfaces."""

    def __init__(
        self,
        sets: dict[str, tuple[dict[str, str], str]],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._sets = sets
        self._names = {
            set_id: tuple(sorted(glyphs))
            for set_id, (glyphs, _family) in sets.items()
        }

    @Property("QVariantList", constant=True)
    def sets(self) -> list[dict[str, str]]:
        return [
            dict(record)
            for record in _ICON_LIBRARY_SETS
            if record["value"] in self._sets
        ]

    @Slot(str, str, result="QStringList")
    def search(self, set_id: str, query: str = "") -> list[str]:
        names = self._names.get(str(set_id or ""), ())
        terms = str(query or "").strip().lower().replace("_", "-").split()
        if not terms:
            return list(names)
        return [
            name for name in names
            if all(term in name for term in terms)
        ]

    @Slot(str, str, result="QVariantMap")
    def resolve(self, set_id: str, name: str) -> dict[str, str]:
        set_id = str(set_id or "")
        glyphs, family = self._sets.get(set_id, ({}, ""))
        normalized = str(name or "").strip().lower().replace("_", "-")
        glyph = glyphs.get(normalized, "")
        if not glyph and set_id in {"fluent-regular", "fluent-filled"}:
            fallback_id = (
                "fluent-filled"
                if set_id == "fluent-regular"
                else "fluent-regular"
            )
            fallback_glyphs, fallback_family = self._sets.get(
                fallback_id, ({}, "")
            )
            glyph = fallback_glyphs.get(normalized, "")
            family = fallback_family if glyph else family
        return {
            "glyph": glyph,
            "fontFamily": family if glyph else "",
        }


def qml_icon_bindings(
    project_root: Path,
    parent: QObject | None = None,
) -> dict[str, object]:
    """Build the single QML icon-font boundary for an application engine."""

    solid, solid_family, regular, regular_family = fontawesome_assets(
        project_root
    )
    material, material_family = material_design_icon_assets(
        project_root, complete=True
    )
    fluent_regular, fluent_filled, fluent_family = (
        fluent_system_icon_assets(project_root)
    )
    catalog = IconFontCatalog({
        "fontawesome-solid": (solid, solid_family),
        "fontawesome-outline": (regular, regular_family),
        "material-design": (material, material_family),
        "fluent-regular": (fluent_regular, fluent_family),
        "fluent-filled": (fluent_filled, fluent_family),
    }, parent)
    return {
        "fontAwesomeSolidGlyphs": solid,
        "fontAwesomeSolidFontFamily": solid_family,
        "fontAwesomeRegularGlyphs": regular,
        "fontAwesomeRegularFontFamily": regular_family,
        "materialDesignIconGlyphs": material_design_semantic_glyphs(
            material
        ),
        "materialDesignIconFontFamily": material_family,
        "iconFontCatalog": catalog,
    }
