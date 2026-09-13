"""Search helpers shared by QWidget and QML presentation layers."""


def get_suggestion_filter(
    column,
    search_text,
    possible_columns,
    default_filter=None,
):
    filters = ["begin", (column, "EQI", search_text)]
    if "keywords" in possible_columns:
        filters.append(("keywords", "EQI", search_text))
    if "description" in possible_columns:
        filters.append(("description", "EQI", search_text))
    filters.append("or")
    if default_filter:
        filters.extend((default_filter, "and"))
    return filters
