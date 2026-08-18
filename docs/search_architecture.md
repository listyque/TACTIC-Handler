# Search architecture

Search Tab is the single owner of a running search. Its `filter_records` are
the canonical definition shown by Advanced Search and saved by Search Views.
TACTIC query filters are always derived from those records.

The primary search field edits only the first `name` record. Advanced Search
edits the complete record list. A saved preset restores that same list.
Sidebar entries only provide an initial Search View and open a Search Tab;
they do not implement another search or filtering engine.

All entry points use `modern_ui.search_contract`:

`sidebar / primary field / Advanced Search / preset / relation / skey`

`-> filter records -> SearchTabSession -> executable TACTIC filters`

Server serialization and discovery of legacy-compatible Search Views remains
in `modern_ui.search_presets`; it is storage, not a second runtime model.
