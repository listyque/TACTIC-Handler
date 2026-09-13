THEME_STYLES = (
    {
        "value": "md3",
        "label": "Material Design 3",
        "description": "Current TACTIC-Handler appearance",
    },
    {
        "value": "material5",
        "label": "Material Design 5 (preview)",
        "description": "Experimental project theme, not an official specification",
    },
    {
        "value": "fluent",
        "label": "Fluent Design",
        "description": "Compact Windows-oriented surfaces and motion",
    },
)

THEME_STYLE_IDS = {record["value"] for record in THEME_STYLES}

ACCENT_PRESETS = (
    {"value": "steel", "label": "Steel", "light": "#3d7599", "dark": "#78a6c4", "lightBase": "#d4dce1", "darkBase": "#292d30"},
    {"value": "silver", "label": "Silver", "light": "#67717a", "dark": "#b4bec6", "lightBase": "#d9dde0", "darkBase": "#303336"},
    {"value": "ash", "label": "Ash", "light": "#656662", "dark": "#adafaa", "lightBase": "#d8d8d6", "darkBase": "#2e2e2c"},
    {"value": "graphite", "label": "Graphite", "light": "#535a60", "dark": "#9da5ab", "lightBase": "#d2d4d5", "darkBase": "#27292b"},
    {"value": "charcoal", "label": "Charcoal", "light": "#41494f", "dark": "#89939a", "lightBase": "#ccd0d2", "darkBase": "#202326"},
    {"value": "blue", "label": "Blue", "light": "#2563a6", "dark": "#6ea8e6", "lightBase": "#d6dce8", "darkBase": "#272d36"},
    {"value": "azure", "label": "Azure", "light": "#0078b8", "dark": "#62b3dc", "lightBase": "#d2dfe5", "darkBase": "#253037"},
    {"value": "cyan", "label": "Cyan", "light": "#007c91", "dark": "#5bc0d1", "lightBase": "#d0dfe1", "darkBase": "#253234"},
    {"value": "teal", "label": "Teal", "light": "#087f6a", "dark": "#5abfa9", "lightBase": "#d2dfdc", "darkBase": "#263330"},
    {"value": "emerald", "label": "Emerald", "light": "#27824c", "dark": "#65b982", "lightBase": "#d5dfd8", "darkBase": "#29332c"},
    {"value": "green", "label": "Green", "light": "#4c7d28", "dark": "#86b85a", "lightBase": "#d9dfd3", "darkBase": "#2d3328"},
    {"value": "lime", "label": "Lime", "light": "#637a1b", "dark": "#a5bd4f", "lightBase": "#dde0d2", "darkBase": "#303326"},
    {"value": "amber", "label": "Amber", "light": "#946500", "dark": "#d5ad48", "lightBase": "#e3dccb", "darkBase": "#373126"},
    {"value": "orange", "label": "Orange", "light": "#a65316", "dark": "#e08b4e", "lightBase": "#e2d7cf", "darkBase": "#372d27"},
    {"value": "coral", "label": "Coral", "light": "#a4483c", "dark": "#de786b", "lightBase": "#e2d5d2", "darkBase": "#372b2a"},
    {"value": "red", "label": "Red", "light": "#a93f4d", "dark": "#de7180", "lightBase": "#e1d3d5", "darkBase": "#36292c"},
    {"value": "rose", "label": "Rose", "light": "#a83e78", "dark": "#dd75a9", "lightBase": "#e2d3db", "darkBase": "#362a31"},
    {"value": "violet", "label": "Violet", "light": "#76558d", "dark": "#b49ac8", "lightBase": "#ddd5e1", "darkBase": "#322d36"},
    {"value": "indigo", "label": "Indigo", "light": "#4f5ea8", "dark": "#8b99e0", "lightBase": "#d8d8e4", "darkBase": "#2d2e38"},
)

ACCENT_PRESET_IDS = {record["value"] for record in ACCENT_PRESETS}
ACCENT_PRESET_BY_ID = {
    record["value"]: record for record in ACCENT_PRESETS
}

DEFAULT_THEME_ACCENTS = {
    "md3": {"light": "steel", "dark": "steel"},
    "material5": {"light": "violet", "dark": "violet"},
    "fluent": {"light": "azure", "dark": "azure"},
}

ICON_SETS = (
    {
        "value": "automatic",
        "label": "Automatic",
        "description": "Material-first icons with safe fallbacks",
    },
    {
        "value": "fontawesome-solid",
        "label": "Font Awesome Solid",
        "description": "Bold, filled application icons",
    },
    {
        "value": "fontawesome-outline",
        "label": "Font Awesome Outline",
        "description": "Lighter outlined icons where available",
    },
    {
        "value": "material-design",
        "label": "Material Design Icons",
        "description": "Material Design icon vocabulary",
    },
    {
        "value": "fluent-regular",
        "label": "Fluent Regular",
        "description": "Modern outlined Fluent System icons",
    },
    {
        "value": "fluent-filled",
        "label": "Fluent Filled",
        "description": "Modern filled Fluent System icons",
    },
)

ICON_SET_IDS = {record["value"] for record in ICON_SETS}


def normalize_theme_style(value):
    value = str(value or "md3").strip().lower()
    return value if value in THEME_STYLE_IDS else "md3"


def normalize_accent_preset(value, fallback="steel"):
    value = str(value or fallback).strip().lower()
    return value if value in ACCENT_PRESET_IDS else fallback


def normalize_theme_accents(values=None):
    values = values if isinstance(values, dict) else {}
    result = {}
    for style in THEME_STYLE_IDS:
        defaults = DEFAULT_THEME_ACCENTS[style]
        source = values.get(style)
        source = source if isinstance(source, dict) else {}
        result[style] = {
            mode: normalize_accent_preset(
                source.get(mode), defaults[mode]
            )
            for mode in ("light", "dark")
        }
    return result


def accent_color(preset, dark):
    record = ACCENT_PRESET_BY_ID.get(
        normalize_accent_preset(preset),
        ACCENT_PRESET_BY_ID["steel"],
    )
    return record["dark" if dark else "light"]


def base_color(preset, dark):
    record = ACCENT_PRESET_BY_ID.get(
        normalize_accent_preset(preset),
        ACCENT_PRESET_BY_ID["steel"],
    )
    return record["darkBase" if dark else "lightBase"]


def normalize_icon_set(value):
    value = str(value or "material-design").strip().lower()
    return value if value in ICON_SET_IDS else "material-design"
