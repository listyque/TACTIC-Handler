# TACTIC Database Rules

## 1. The search type matters more than the physical table

Code must use a logical name such as `sthpw/task`, `config/process`, or
`my_project/asset`, not a bare table name. `sthpw/search_object` defines the
database, physical table, and Python class. For `config/*`, the physical tables
are named `spt_*` and exist in every project database.

## 2. Direct SQL is not the normal write path

The standard flow is
`SearchType.create()`/a specialized factory -> `SObject.set_value()` ->
`commit()`, or the command/ServerStub API. This preserves security, triggers,
the transaction log, change timestamps, and caches. Direct SQL is allowed only
for migrations and diagnostic repair.

## 3. Do not create derived records manually

- `snapshot` and `file` records are created by the check-in system.
- `status_log`, `transaction_log`, `sobject_log`, `change_timestamp`, and
  notification logs are created by the system.
- `message_log` is created by the messaging API.
- `process_state` is created by the workflow engine.
- `login` and `ticket` are changed through the security API.

## 4. Polymorphic relationships

Many tables use `search_type + search_id`; newer areas also use `search_code`.
Do not add a custom foreign key to every project table. Pass a search key or
SObject to the native API and let TACTIC populate the relationship.

## 5. Retire instead of delete

For user and configuration SObjects, normally use retirement (`s_status`) and
the native retire API. Reserve hard deletion for system cleanup or uninstall
operations; otherwise audit records, dependencies, and references are lost.

## 6. `project_code` and data scope

`sthpw/*` tables are global, but many rows belong to a project through
`project_code`. `config/*` tables physically reside in a project database. Do
not mix global definitions with project-scoped definitions.

## 7. XML and JSON are subsystem contracts

The `pipeline`, `schema`, `config`, `snapshot`, `access_rules`, `manifest`,
`status`, `data`, and `metadata` fields are not unrestricted text containers.
Preserve unknown keys, use the owning parser or manager, and do not partially
rewrite a payload without merging it.

## 8. Cache and reload behavior

Changes to `config/naming`, `config/widget_config`, triggers, security groups,
pipeline/process definitions, and settings may be cached. After an
administrative write, use the standard manager or command that invalidates or
reloads the cache.

## 9. Security is always server-side

Hiding a button in the client is only a UX measure. Every mutation must execute
under the user's ticket and be checked by the server-side `AccessManager`.

## 10. The source of truth is the live database plus code

The consolidated SQL describes the 5.0 branch, but an installed server may have
additional upgrades or plugins. Before implementing a new module, run the live
inventory and compare the registry and columns.
