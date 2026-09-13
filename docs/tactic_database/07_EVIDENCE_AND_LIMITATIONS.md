# Evidence Levels and Limitations

This reference does not replace the source code or live schema. Three evidence
levels are used for each table:

1. **DDL evidence** - the table and fields exist in the consolidated PostgreSQL
   schema for the `5.0` branch.
2. **Registry evidence** - `sthpw/search_object` connects the logical search
   type, physical table, and Python class.
3. **Behavior evidence** - an owning class, manager, or command was found that
   actually creates or changes the records.

## Confidence values

- `high` - confirmed by DDL, the registry, and/or an explicit owning API.
- `medium` - the purpose follows from DDL/registry and partial usage, but the
  complete lifecycle has not been traced.
- `low` - the table exists in the schema, but its current owner or relevance is
  unconfirmed. Trace the installed version's code before writing to it.

## What is not included as a final list

- arbitrary project search types and their tables;
- plugin tables;
- changes from commercial or closed branches;
- studio-specific local migrations;
- columns added by later upgrade scripts after the consolidated schema
  snapshot;
- deployment-specific repository or configuration storage.

## Rule for Codex

Even with `high` confidence, application modules must not write through direct
SQL. Find the owning API first. If it does not exist or does not cover the
required operation, document the gap and propose a server-side command or
migration instead of bypassing the table lifecycle.
