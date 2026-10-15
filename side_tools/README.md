# Side tools

- `tactic_db/`: PostgreSQL backup and restore scripts, plus a TACTIC Server
  Python helper that stages a database-upgrade command. See
  [`docs/tactic_database/README.md`](../docs/tactic_database/README.md).
- `batch_scheduler/`: batch dispatcher source, test fixtures, and focused tests.
  The `batch/batch_dispatcher_dev` custom script in TACTIC imports this package.
- `tactic_demo/`: optional demo-project seed and its offline test.
- `custom_script_migration/`: working copies of migrated custom-script modules
  and runners. TACTIC remains the source of truth for published scripts.

These tools are not run automatically. The database scripts are intended for
the server; the batch dispatcher runs from the Handler workspace.
