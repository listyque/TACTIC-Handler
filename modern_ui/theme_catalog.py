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


def normalize_theme_style(value):
    value = str(value or "md3").strip().lower()
    return value if value in THEME_STYLE_IDS else "md3"
