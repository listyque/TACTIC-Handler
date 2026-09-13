# Vertical workflow stabilization

A feature is considered stable only when its complete user workflow is covered.
The source of truth is `tests/contracts/vertical_workflows.json`; it maps each
workflow to isolated test modules, real QML components, registered windows, and
read-only live checks. Every vertical also runs the shared API contracts and the
offscreen QML reopen/shutdown smoke harness.

## Running the suite

Run one workflow while iterating:

```powershell
python tests/run_vertical_suite.py login_configuration
python tests/run_vertical_suite.py navigation_search
python tests/run_vertical_suite.py tasks_notes_work_hours
python tests/run_vertical_suite.py checkin_files
python tests/run_vertical_suite.py messages_users_activity
python tests/run_vertical_suite.py handler_server_dcc
```

Run the complete workflow gate:

```powershell
python tests/run_vertical_suite.py all
```

The runner starts every module in a fresh process. This prevents Qt, settings,
environment, singleton, worker, and server-stub state from leaking between
workflows. Use `--verbose` for individual unittest names and `--timeout` to change
the per-module deadline.

## Workflow coverage

### Login and Configuration

- authentication result persists user, ticket, server defaults, and settings before
  workspace bootstrap;
- logout clears the ticket and session-bound models before showing authentication;
- server URL normalization, presets, repositories, proxy password preservation,
  polling defaults, localization, discard, and startup restoration are covered;
- live check: active ticket, server ping, login identity, preset, and repositories.

### Navigation, Search, and skey

- selected objects, preset-filter tabs, Quick Filters, pagination, result-store
  reuse, code-based skey routing, and request budgets are covered;
- compact/cards/continuous QML uses the shared composition and window registries;
- live check: a bounded search with snapshots and server total-count metadata.

### Tasks, Notes, and Work Hours

- object/search-type/project/user scopes, task create/edit, workflow defaults,
  statuses, notes process selection, milestones, Gantt data, work hours, and Task
  Inspector are covered by the controller and QML scenarios;
- worker generations reject stale pages and project switches invalidate caches;
- live check: one bounded native task workspace page.

### Check-in and Files

- Drop Plate, Commit Queue, naming, preview/screenshot state, repository sync,
  Snapshot Browser, cancel/retry, and check-in payload preparation are covered;
- the final operation test verifies native file structures, repository semantics,
  snapshot identity, and a code-based snapshot skey;
- live check is read-only and queries only a bounded snapshot catalog. Actual
  check-in mutations belong to the isolated test-project seeder.

### Messages, Users, and Activity

- conversations, unread state, attachments, replies, reactions, pins, profiles,
  presence, activity aggregation, polling cursors, and related-object navigation are
  covered;
- live check reads bounded conversations, user activity, and incremental updates.

### Handler Server and DCC

- discovery, handshake, registration, active-client routing, capabilities, scene
  commands, reconnect, timeout, cancel, disconnect, SDK compatibility, and
  controller state are covered using the real localhost protocol;
- no TACTIC live connection is required: thin clients never own TACTIC or check-in.

## Guarded live checks

Live checks are opt-in and read-only. They refuse an implicit target and validate
the project against `tests/fixtures/tactic_test_project.json` before connecting.

```powershell
$env:TACTIC_RUN_LIVE_VERTICALS = "1"
$env:TACTIC_TEST_PROJECT_CODE = "<isolated test project>"
$env:TACTIC_TEST_SEARCH_TYPE = "<test search type>"
python tests/run_live_vertical_checks.py navigation_search
```

Never point the live runner or mutation seeder at a production project. Server-side
create/edit/check-in/delete scenarios must use the separately guarded isolated test
project described in `docs/tactic_test_project.md`.

## Manual acceptance boundary

Automation validates contracts, handlers, state transitions, QML construction,
window reopen, shutdown, request budgets, and the localhost DCC protocol. Human
acceptance remains necessary for server-specific permissions, real repository and
proxy infrastructure, actual file transfer/check-in, Maya-side execution, tray
behavior on Windows, and visual interaction at supported window sizes.
