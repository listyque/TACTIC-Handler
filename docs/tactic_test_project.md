# Isolated TACTIC test project

The application integration suite must use a dedicated TACTIC project whose code
starts with `th_test_`. Production projects are never valid fixture targets.

## Fixture definition

`tests/fixtures/tactic_test_project.json` defines two search types/pipelines, isolated
users and groups, objects, tasks, a milestone, work hours, a note, a snapshot/file,
and a group chat. Every fixture belongs to the marker `tactic-handler-test-v1`.

Create the empty project, search types, pipelines, and security groups through the
TACTIC Project Manager and security APIs. This follows the database write policy in
`docs/tactic_database`: tests must not insert project schemas, snapshots/files,
status history, or message logs directly.

## Safety gates

`tests/support/tactic_test_project.py` supplies the seed/cleanup engine and guard:

1. the project code must start with the manifest prefix (`th_test_`);
2. it must not equal the configured production project;
3. mutation requires `TACTIC_ALLOW_TEST_PROJECT_MUTATION=1`;
4. every record carries the exact fixture marker;
5. cleanup removes only records with that marker;
6. repeated seed and repeated cleanup are idempotent.

Normal unit tests use `MemoryFixtureBackend`; they cannot contact TACTIC. A live
backend must implement the same `ensure(kind, key, values, marker)` and
`cleanup(marker)` protocol using these native pathways:

| Fixture | Required live API |
|---|---|
| Search types/pipelines | verify only; create with Project Manager |
| Users/groups | TACTIC security APIs |
| Objects | `insert_sobjects` / native `SObject.commit` |
| Tasks | task APIs / `edit_multiple_tasks_sobjects` |
| Milestones | milestone API |
| Work hours | `WorkHour.create` and mutation API |
| Notes | `add_note` / native note API |
| Snapshot and file | normal check-in operation with native `File` semantics |
| Chats/messages | conversation and message APIs |

The live adapter is intentionally not invoked by test discovery. It should be wired
only in a controlled CI environment whose server preset points at the isolated test
server/project. Before enabling it, run the read-only schema checks documented in
`docs/tactic_database/06_LIVE_DATABASE_CHECK.md`.
