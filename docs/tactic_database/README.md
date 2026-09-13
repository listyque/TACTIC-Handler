# TACTIC 5.0 Database Reference for Codex

This reference was assembled from the consolidated PostgreSQL schemas and
`sthpw/search_object` registry in the Southpaw TACTIC `5.0` branch. Extraction
date: 2026-08-06.

## Coverage

- 6 bootstrap tables;
- 50 tables in the main `sthpw` schema;
- 15 project-local `config/*` (`spt_*`) tables;
- logical search types, physical names, registered classes, and fields;
- safe-write rules and subsystem owners;
- relationships among workflow, DAM, messaging, security, and audit;
- SQL for comparison with a live installed database.

## Important limitation

TACTIC supports arbitrary project search types. Their physical tables are
created by a user or template and registered in `sthpw/search_object`, so the
source tree cannot contain a final list of one studio's tables. This package
documents the **platform core**. `tools/live_schema_inventory.sql` supplements
it with the tables from a specific server.

## Recommended reading order for Codex

1. `01_DATABASE_RULES.md` - data model and mandatory rules.
2. `02_CORE_TABLE_CATALOG.md` - all `sthpw` and bootstrap tables.
3. `03_CONFIG_TABLE_CATALOG.md` - all project-local `config/*` tables.
4. `04_RELATIONSHIPS_AND_FLOWS.md` - common write flows.
5. `05_WRITE_POLICY_MATRIX.md` - concise guidance on where and how to write.
6. `06_LIVE_DATABASE_CHECK.md` - how to avoid blindly trusting an old SQL
   schema.
7. `07_EVIDENCE_AND_LIMITATIONS.md` - evidence boundaries and confidence.
8. `machine/` - JSON and CSV data for automated lookup.

## Primary rule

Do not design a new table until all of the following have been checked:

- `sthpw/search_object`;
- the tables and classes in this catalog;
- existing server stub methods and server-side classes;
- `sthpw/schema`, `sthpw/connection`, `sthpw/note`, `sthpw/task`,
  `sthpw/snapshot`, `sthpw/message*`, and `config/*`;
- the actual live database schema.

## Primary sources

- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/upgrade/postgresql/bootstrap_schema.sql
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/upgrade/postgresql/sthpw_schema.sql
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/upgrade/postgresql/config_schema.sql
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/search.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/search/transaction.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/security/security.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/security/access_manager.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/task.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/note.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/snapshot.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/file.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/pipeline.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/subscription.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/tactic/ui/app/message_wdg.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/command/workflow.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/biz/naming.py
- https://raw.githubusercontent.com/Southpaw-TACTIC/TACTIC/refs/heads/5.0/src/pyasm/checkin/file_checkin.py
