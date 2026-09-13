# TACTIC server-data cache and invalidation policy

`thlib.server_cache` is the single persistent store for immutable copies of
server query payloads. Domain controllers still own query meaning, native
TACTIC object construction, presentation state, and mutation behavior. The
cache never stores live `SObject`, `Task`, `Snapshot`, or `File` instances;
controllers rehydrate those objects from copied server dictionaries.

## Identity and storage

Every entry is scoped by normalized server endpoint, authenticated login, and
project code. The scope directory contains readable project, login, and server
labels plus a short identity digest, and each domain owns one clearly named
JSON document under `cache/server_data/*`. Entries are persisted exclusively
through `env_read_config` and `env_write_config`.
These documents have one strict current shape. They contain no format-version
field, migration reader, or alternate loader; an obsolete or malformed shape
is discarded and the next server result replaces it.
The following independently configurable domains are supported:

| Domain | Server data |
|---|---|
| `reference` | projects, Search Types, users, pipelines, processes, statuses, groups, roles, schemas, and tags |
| `search` | ordered sObject search pages and raw object fields |
| `snapshots` | snapshot and file metadata |
| `relations` | child and linked-object membership |
| `tasks` | Task Manager scopes, pages, and task records |
| `notes` | note histories, process counts, and attachment metadata |
| `messages` | bounded conversation lists and history pages |
| `activity` | activity pages and complete calendar counts |
| `work_hours` | timesheets and report query results |

Limits are enforced per domain and old entries are discarded by last-write
time. Cache entries have no time TTL: freshness is event-driven because TACTIC
already exposes change timestamps.

## Read, refresh, and mutation rules

- Ordinary navigation and reopening a previously queried scope may use the
  persistent cache. A native TACTIC object is reconstructed before data reaches
  an owning controller or model.
- Every user-facing Refresh command is a force reload. It invalidates the
  relevant domain scope first and then performs the server request with cache
  reads disabled.
- Check-in, sObject editing, task/note/message/work-hour mutations, relation
  changes, and destructive operations invalidate all affected domains after
  the server confirms success.
- The background server-update service advances a persistent change cursor and
  maps `change_timestamp` and retire records to affected domains. The first
  poll establishes a baseline instead of invalidating the entire server
  history.
- Startup uses that same cursor before loading reference data. Cached projects,
  logins, Search Types, schemas, pipelines, and views are reused when no
  matching server change exists; only invalidated reference scopes are fetched.
- Project, server, and login are part of the key. Data cannot cross those
  identity boundaries.

## Reliable reset and concurrency

Configuration reads and writes share an in-process lock; cache entry updates
also hold the cache lock across read/merge/write and generation validation.
JSON is serialized and flushed to a temporary file in the same directory,
then atomically replaced. A Windows or SMB reader outside these locks can
briefly deny that replacement (`WinError` 5, 32, or 33). The configuration
writer retries only `os.replace`, up to six attempts with 310 ms total backoff;
it does not repeat serialization or the server query. A successful first
attempt never waits. Task refresh performs this I/O in its server worker.
Persistent denial and other I/O failures still propagate with the original
exception; the previous document remains intact and the temporary file is
cleaned up. The writer never deletes/truncates the destination to force a save.

`tests.test_settings` covers a real Windows reader blocking rename, transient
and persistent errors, atomicity, cleanup, and concurrent configuration updates.
`tests.test_server_cache.ServerCacheFileTests` verifies concurrent disk-backed
cache writes and repeated task refreshes with a native Windows reader lock,
including server query counts and reloading the latest payload from disk.

Clear Cache first raises a global generation and each changed preference raises
the corresponding domain generation. A worker that started under an older
generation may still finish its server request, but its late cache write is
rejected. Every JSON document below the cache-owned `cache/server_data`
directory, including documents in unknown obsolete scope folders, and every
change cursor are then removed; reset never creates placeholder `{}` documents.
Already open controller projections remain live because they own interaction
state rather than cache data. Switching between open tabs never reloads them;
the owning Refresh command replaces the projection from the server explicitly.

Search-tab layout, window geometry, drafts, selections, message compose state,
downloaded repository files, and other user or presentation state are not
server-data cache and are never removed by Clear Cache.

Small bounded runtime-only projections remain with their domain owners (for
example rendered preview URLs and the currently displayed message history).
Their declared ownership and limits live in `thlib.ui.cache_policy`; they do not
create a second persistent server cache.
