"""Icon-name boundary between TACTIC sidebar XML and modern UI glyphs."""

from __future__ import annotations


_TACTIC_ICON_PREFIXES = {"FA", "FAR", "FAS", "FAB", "MDI"}


def icon_name_from_tactic(value: object) -> str:
    """Return the glyph name expected by ``MaterialIcon``.

    Legacy Handler passed sidebar values such as ``FAS_FOLDER_OPEN`` through
    ``get_icon(tactic_icon=...)`` which removed the family prefix and changed
    the remaining underscores to hyphens.  Keep that compatibility at the
    server-data boundary while still accepting unprefixed project icons.
    """
    raw = str(value or "").strip()
    prefix, separator, name = raw.partition("_")
    if separator and prefix.upper() in _TACTIC_ICON_PREFIXES and name:
        return name.replace("_", "-").lower()
    return raw


def icon_name_for_tactic(value: object) -> str:
    """Encode an Icon Manager glyph for legacy-compatible sidebar XML."""
    clean = icon_name_from_tactic(value).strip()
    if not clean:
        return ""
    return "FAS_" + clean.replace("-", "_").upper()
