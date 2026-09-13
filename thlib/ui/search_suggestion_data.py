"""Shared TACTIC search-suggestion query and presentation data."""


SEARCH_SUGGESTION_ROLES = (
    "title", "description", "keyword", "code", "values", "selected",
)


def search_suggestion_spec(stype, text: str) -> tuple[str, list[str], list]:
    """Build the native TACTIC suggestion query for a Search Type."""
    from thlib.search_helpers import get_suggestion_filter

    columns_info = (stype.get_columns_info() or {}) if stype else {}
    suggest_column = "name"
    if suggest_column not in columns_info:
        suggest_column = "title"
        if suggest_column not in columns_info:
            suggest_column = "code"
    columns = [suggest_column]
    for column in ("keywords", "code", "description"):
        if column in columns_info and column not in columns:
            columns.append(column)
    filters = get_suggestion_filter(suggest_column, text, columns)
    return suggest_column, columns, filters


def search_suggestion_records(
    records, key: str, title_column: str,
) -> list[dict]:
    """Project native query records into the shared search-field roles."""
    suggestions = []
    seen = set()
    folded_key = str(key or "").casefold()
    for record in records or []:
        title = record.get(title_column)
        if title in (None, ""):
            continue
        title = str(title)
        description = " ".join(
            str(record.get("description") or "").splitlines()
        )
        keyword = ""
        for candidate in str(
                record.get("keywords") or "").replace(",", " ").split():
            if folded_key in candidate.casefold():
                keyword = candidate
                break
        identity = (title, description, keyword)
        if identity in seen:
            continue
        seen.add(identity)
        values = {title_column: title}
        for column in ("keywords", "description"):
            value = record.get(column)
            if value not in (None, ""):
                values[column] = value
        suggestions.append({
            "title": title,
            "description": description,
            "keyword": keyword,
            "code": str(record.get("code") or ""),
            "values": values,
            "selected": False,
        })
        if len(suggestions) >= 20:
            break
    return suggestions
