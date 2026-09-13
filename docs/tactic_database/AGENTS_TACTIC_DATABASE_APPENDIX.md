# TACTIC Database Rules for Codex

Before creating a table, column, wrapper model or server procedure:

1. Read `docs/tactic_db/README.md` and `01_DATABASE_RULES.md`.
2. Search `05_WRITE_POLICY_MATRIX.md` and machine JSON for an existing native entity.
3. Query the live `sthpw/search_object` registry.
4. Inspect the registered server class and an existing native write path.
5. Do not direct-write system-derived tables.
6. Do not create parallel task, note, chat, snapshot/file, connection, notification-rule, workflow-state or audit tables without an explicit gap analysis.
7. Prefer native search types and relationships; custom tables are for genuinely new domain concepts.
8. Every schema change requires migration, live capability check and rollback.
9. Preserve unknown XML/JSON fields and use owning managers for configs.
10. Server security is authoritative.
