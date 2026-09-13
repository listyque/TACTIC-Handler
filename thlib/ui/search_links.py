"""Stable shareable links for server-backed TACTIC Saved Searches."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse


SAVED_SEARCH_SCHEME = "tactic-search"


def build_saved_search_link(
    project_code: str,
    search_type: str,
    view: str,
) -> str:
    values = {
        "project": str(project_code or "").strip(),
        "search_type": str(search_type or "").strip(),
        "view": str(view or "").strip(),
    }
    if not all(values.values()):
        return ""
    return f"{SAVED_SEARCH_SCHEME}://open?{urlencode(values)}"


def parse_saved_search_link(value: str) -> dict[str, str] | None:
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme.casefold() != SAVED_SEARCH_SCHEME:
        return None
    if parsed.netloc not in {"", "open"}:
        return None
    values = dict(parse_qsl(parsed.query, keep_blank_values=False))
    result = {
        "project": str(values.get("project") or "").strip(),
        "search_type": str(values.get("search_type") or "").strip(),
        "view": str(values.get("view") or "").strip(),
    }
    return result if all(result.values()) else None
