# Checking a Live TACTIC Database

The source schemas are a baseline, not proof of the installed DB. Run the scripts in `tools/` against the `sthpw` database and every project database.

## Compare these three layers

1. `information_schema.columns` — physical truth.
2. `sthpw.search_object` — logical registry and class mapping.
3. Source classes/plugins — semantic owner and creation/update APIs.

## Red flags

- registered search type whose table does not exist;
- physical table not registered as a search type;
- class_name no longer importable;
- columns expected by Handler but missing;
- duplicate `config/naming` defaults;
- `config/process` rows missing from pipeline XML or vice versa;
- project tables in a different DB/schema than registry says;
- direct custom tables duplicating task/note/message/snapshot/connection functionality.

## Codex procedure before writing a new module

1. Run inventory.
2. Search this catalog by proposed entity name.
3. Search `sthpw/search_object` by title/search_type/table_name.
4. Inspect registered class and all creation/update methods.
5. Trace one existing native UI/server command that writes it.
6. Only then decide whether a new table/column is required.
