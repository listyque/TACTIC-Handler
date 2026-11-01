# Handler boundaries to Stream services

`thlib.environment.get_server_api()` is the authority for the current connection.
Only an authenticated bootstrap for the same server URL, login and ticket can
enable Stream. Unknown sessions have the same restrictions as Legacy sessions;
cached project data cannot enable extensions.

The machine-readable [boundary inventory](stream_boundaries.json) records every
Handler-owned command dispatch, Stream server import and private HTTP route.
`tests.test_stream_api_inventory` detects new or stale entries. Each new boundary
needs an explicit legacy policy and a behavioral test; the inventory itself does
not prove that an operation is guarded.

## Behavior by domain

| Domain | Confirmed Stream | Legacy or unknown API |
| --- | --- | --- |
| Agent chat, providers, MCP, drafts, local agent host | Existing Stream commands and attachment routes | Hide entry points; reject direct/file requests; clear session state |
| Backend controls, database resources, System Info | Existing Stream tools | Hide and stop background requests; retain native connection settings |
| Plugins and page/card layout authoring | Existing Stream editors | Hide; reject queued reads, uploads, writes and previews |
| Table-view manager | `TableViewsCmd` manager | Hide manager; retain native view selection, column configuration and Save as |
| Search item layouts | Fetch Stream metadata | Ordinary search; discard cached Stream layout metadata |
| Custom HTML/Mako layouts | Native rendering plus Stream interactive actions | Retain HTML/Mako rendering; block modern detail/form/report/filter commands; identify typed Stream definitions before importing their modules |
| Nested table filters and saved searches | Stream access callbacks and expression write denial | Native `Search.eval`/`SearchWdg`; retain mandatory parent scope |
| Configured Stream URLs | Resolve to native workspace pages | Keep ordinary browser URL handling |
| File-project workspace | Stream file transport | Clear stale workspace; block actions, queued reads and transfers |
| Server check-in queue | Chunked Stream submission/status/cancellation | Hide switch; use native client check-in for local operations; retain remote batch references without replaying or cancelling them through legacy |
| Server updates | SSE or native polling | Native polling; cancel a previous SSE connection without changing the saved preference |
| Hook editor | Command when `class_exists` succeeds | Native hook CRUD when command is absent; never retry a failed write using another API |
| Project/template/schema/ingest/preferences commands | Native TACTIC commands | Keep their native contracts |

`file_project` read scopes apply to Stream's virtual search types. Server-defined
read-policy commands are used only when the native SearchType advertises that
method and policy. Handler's optional `tactic_handler_queries` plugin is a
separate native TACTIC extension, with the existing Local procedure mode; it is
not a reason to disable legacy search.

JSON RPC is the explicitly labelled **JSON (TACTIC Stream)** preset transport.
Legacy connections use **XML-RPC**, the default. Detection does not silently
rewrite saved transports. Bundled `agent_runtime/tactic_stream` imports execute
locally; its private HTTP calls are entered through the guarded desktop agent.
Standalone agent CLI commands explicitly target Stream.

## Verification and maintenance

- `python -m unittest tests.test_stream_api_inventory tests.test_legacy_server_mode`
  checks the ledger, session authority, hidden native queue controls, direct and
  deferred requests, retained batches, native search and effective polling.
- `tests.test_table_service_workflows`, `tests.test_custom_urls`,
  `tests.test_table_views_manager`, `tests.test_script_triggers` and agent/queue
  suites retain their positive Stream and original TACTIC behavior.
- Stream's `test_legacy_stream_boundaries.py` executes both transported Handler
  and native Stream procedure sources against real SQL while making the Stream
  namespace unavailable. HTML layouts and nested filters still work; typed
  layouts report that Stream is required. A broken installed Stream dependency
  must remain an error rather than bypassing access checks.
- `frontend/tests/legacy_table_menu.mjs` checks EN/RU menu filtering and preservation
  of the native view actions in the shared description.

Add policy at the owning domain rather than intercepting generic XML-RPC faults.
A missing extension is not a transient network failure. Background work keeps
its captured connection; session changes must not redirect it to another server
or replay an accepted remote write through a legacy path.
