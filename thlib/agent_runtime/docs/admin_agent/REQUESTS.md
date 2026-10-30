# Requests from the ordinary TH and TS interfaces

TS 0.112.217 and TH 0.6.0.159 add **External agent** to the shared main options
menu. This is an administrator entry point. Both clients use the same Frame
description and native controls; the browser never embeds a desktop window.

## User workflow

Open a project and page, select objects, then choose External agent. The window
shows the captured client, project, navigation entry, Search Type, table view and
exact selected search keys. Enter a task. Without **Allow the requested
configuration changes**, the agent receives only reads/previews. Checking it
allows native naming/page/project/template writes, existing-project workflow and entity edits, attachment check-ins and inactive TH script drafts,
limited by the host's own launch permissions and the authenticated account.
It does not expose script activation.

Send starts one durable conversation. The model selector uses the connected host's model/list result; it is fixed during an active turn. Context chips show the frozen project/page/type/selection; Context details reveals exact keys. Files can be chosen, dropped or pasted into the composer (Ctrl+V), where the browser exposes that clipboard format. Each file is limited to 64 MB, at most 20 per message; image model input is limited to 20 MB. Arbitrary binary originals can be checked in, but text/image input is not a universal document/audio/video decoder.

Send starts a turn. Progress and the final answer appear in the
same window; the agent's results are ordinary TACTIC resources. Closing the window
leaves the request running. Reopen it or select a recent request to inspect its
captured context and result. Choose New conversation to capture the current page and
selection. Changing project/page/selection after sending never retargets the task.
A follow-up retains ordered user/assistant history and the original authorization. While working, Send correction uses turn/steer. Undelivered corrections remain queued if completion races submission; message UUIDs prevent duplicates. A new conversation captures a new scope. A clear outcome distinguishes verified completion, a question and a blocked task.

Undo field change is available only for the latest ordinary field patch, after completion. It refuses changed after-images and never invokes global undo. Workflow/schema/file/page/naming/project/script changes are outside this button; inspect their native editors/history.

Cancellation stops pending work or asks the external host to stop its current
process tree. Completed native operations are preserved. Inspect them before a
new request. A disconnected running request becomes interrupted after 90 seconds;
it is never automatically executed again. An expired queued host also produces
an explicit interrupted state. Refresh/reopen does not resubmit anything.

## Connect the existing Codex host

Use **Run agent on** and **Connect agent** in the chat or AI providers.
TH prefers its own registered desktop when no executor is active. TS offers the
current account's connected desktops. The server is an explicit alternative,
never a default/fallback. Existing active connections retain their target.

`AgentExecutorCmd` requires an administrator and the current `project_code`.
`state` returns `targets` (id/kind/label/state/error) and the active/default desktop
`target`; `start`/`stop` require an explicit target UUID or `server`. An unselected
or unavailable target is rejected. Starts across targets are serialized per owner;
repeated starts are idempotent and a running project must be disconnected first.
These controls are not exposed as model tools.

TH registers its ephemeral device UUID using `desktop_poll` in the authenticated
admin project. The server returns only fixed start/stop operations for that same
login. Reports and acknowledgements carry an operation UUID; stale reports cannot
overwrite newer commands and retries do not create a second process. Devices expire
from the selector after 20 seconds without a poll; unaccepted commands expire after
60 seconds. Relay metadata under `data/agent_desktops` contains no credentials.
The desktop uses its own captured session and server address, never a browser-supplied
command, path, URL or ticket. Signing out invalidates pending callbacks and stops
owned local processes; a server outage does not replay completed work.

TH owns a separate `tactic_stream.agent_worker` subprocess, using the portable
HTTP/MCP modules bundled under `thlib/agent_runtime`. It never imports a sibling
Stream checkout or its server/database packages. `tools/sync_agent_runtime.py
--stream-root <TS/tactic_stream> --check` verifies the exact source/reference copies.
First explicit Connect prepares a private cached venv (`cache/agent_python`) with
its own cross-process installation lock. No dependencies are installed on normal
TH startup and global Python is unchanged. Codex CLI and its sign-in must exist
on the selected machine. Provider localhost addresses are relative to that machine.

The optional server runner still uses its own OS account, optional agent dependencies
and Codex/provider setup. It receives the session through private process environment,
with metadata/stop markers under `data/agent_executors` and an OS lease preventing
duplicates. Neither runner writes tickets/passwords into command lines or state files.

Disconnect stops owned model/MCP children, interrupting an active turn while preserving
committed changes. Closing the chat leaves either runner connected. Closing/signing
out of TH stops its local runners; the server runner continues independently.
Externally launched hosts are detected but cannot be stopped by this control.
There is no autostart on Send, OS service installation or silent server fallback.

The same host can also be started manually. The web worker never runs a
model or imports Handler. Provider credentials are stored encrypted on TS and
exported only as host-bound encrypted packages; see [PROVIDERS](PROVIDERS.md).
Install the optional agent
extra and sign in to Codex CLI first, following [CODEX](CODEX.md). For this
checkout-based connection, run in a private operator terminal:

```text
python -m tactic_stream.agent_host --server http://<server>:8081 --project <code> --stream-root <TS/tactic_stream> --handler-root <TH> --login <TACTIC-login> --allow-changes
```

The password is entered privately at the prompt. Alternatively omit --login and
inject a valid TACTIC_AGENT_TICKET into the process environment. Never supply a
ticket/password as a command argument. Repeat --project for each allowed project;
newly created projects need explicit host reconnection. The connection is scoped
to the same TACTIC login as the user submitting requests. An offline connection
disables sending. Other external hosts may consume the same fixed Command
contract without changing either UI; this shipped executor specifically uses
Codex CLI and its existing authentication.

The host disables shell, source edits and other apps. Native web search is optional
per conversation and disabled by default. The host uses an empty working
directory and invocation-only MCP configuration; user MCP servers, plugins and hooks are disabled, and does not modify global
Codex settings. Its tools are the existing [MCP operations](CONNECTION.md).
Naming/page/project operations retain native revision/receipt checks. Add the
trusted --trial-image and --trial-directory options from [SCRIPT_TRIALS](SCRIPT_TRIALS.md)
to expose isolated Linux trials. Activate reviewed drafts separately in the
ordinary Script Editor; generated Python is never executed by the request UI
or on the operator's Windows host.

## Native contract and ownership

### Conversation library

The shared history panel is `features/scripts/history.ui.mjs`; TH owns native
transport/draft state in `thlib/ui/agent_request.py`, and TS owns web transport in
`frontend/src/features/scripts/AgentRequest.vue`. Neither adapter edits storage.

`AgentRequestCmd` actions `draft`, `organize`, `group_save` and `group_remove`
use `tactic_stream/server/agent_library.py` under the normal authenticated Command
transaction. Requests remain owner/project scoped in `spt_agent_request`; optional
`library` metadata contains `title`, `group`, `pinned`, `archived`. Folder definitions
use native user/project `WidgetSettings`, key `external_agent.library`. No schema
or model execution is required to name a draft or organize history.

`state(query, archived, offset)` returns summaries (100/page), `next_offset`,
`total`, `groups`, `groups_revision` and an independent unfiltered
`active_requests` list. Queue/idle checks must inspect `active_requests`, since
the selected history page may exclude running requests. Search scans owned saved
messages, titles and type identifiers; this is not indexed full-text search.
`read` adds `library_summary`. `organize` requires its `library_revision`;
folder writes require `groups_revision`. Stale revisions fail without overwriting.
Removing a folder ungroups its chats and never deletes messages or operations.
Archive rejects active requests and archived chats require restoration before Send.

A saved draft captures context but has no model host or messages. Its first
`submit` uses the same request ID and verifies the captured context, preserving
library metadata. Only Send starts execution or transmits data to a provider.
Existing records without metadata retain their original prompt-derived title.

Messages accept empty text only when they contain finished, owner-scoped attachments.
Image thumbnails use authenticated AgentAttachmentCmd.preview, which decodes a
bounded JPEG thumbnail; originals remain immutable and available for native check-in.
Do not embed attachment tickets in URLs. agent_context includes the conversation's
attachment metadata, including files from follow-ups. Tool start/completion events
and model commentary describe the current turn in the shared transcript column.

The optional boolean `document.allow_web` is fixed before submitting a conversation,
independent of TACTIC write permission. A host advertises `web_search`; the server
rejects enabling it on an unsupported host. Codex uses native `web_search=live` only
for an enabled conversation and permits its webSearch events. Other conversations
retain disabled search; shell, source editing, apps and local file tools remain
disabled. Search results are untrusted data. The host-bound `agent_web_download`
tool fetches anonymous public HTTPS files (443, at most 64 MB) into private
conversation attachments. Each redirect is checked, validated DNS addresses are
pinned while TLS verifies the original hostname, and no TACTIC ticket/cookies are
sent to the source. operation_id is a durable attachment/message UUID; reusing it
with another URL is refused. Native check-in still requires allow_changes.
The normal UI labels the combined permission **Allow internet access**.

The host discovers model-specific `efforts` and the configured default model through
Codex `model/list` and `config/read`. Both clients offer **Reasoning effort** only
for a model with advertised options, including the configured **Agent default**.
The request document and follow-up accept `effort` (empty means provider default).
The server validates it against the selected host/model and freezes model/effort
during execution; the host forwards it as `turn/start.effort`. Changing model clears
the draft effort. Omitted effort remains compatible with older clients/hosts.

`tactic.ui.panel.agent_request_cmd.AgentRequestCmd`, through normal execute_cmd,
owns state, submit, read, selection, cancel, heartbeat, disconnect, claim, update, message, ack, downloaded attachment registration and guarded field undo. Normal
authentication, API command authorization and administrator permission apply.
Private per-project spt_agent_request/spt_agent_host tables are created by the
standard config upgrade. They store user-owned metadata and results, never
tickets or provider credentials. Collection locks serialize submit/claim/update.
The request UUID plus exact document makes submission idempotent. A claim binds
one host; another host cannot complete its request. Native receipts prevent
remote configuration replay; request interruption cannot roll back writes already
committed through other commands. Host reports are not independent attestation.

The MCP adapter's host-bound --request-id adds agent_context and agent_selection.
The model cannot choose another request, ticket or origin. Selection reading
projects only public identity/title/parent fields from the exact captured keys;
it fails on deleted/unavailable objects. Broader schemas and configuration are
read through the existing task tools and curated knowledge pack.

TS captures its working workspace selection; TH captures its native section,
table view and script-shelf selection provider. This is an immutable handoff,
not a live TH runtime connection: th_runtime_connected remains false. Native TH
hooks and shelf scripts still belong to TH, not browser uploads or a DCC client.

AgentAttachmentCmd owns retry-safe chunked private uploads under data/agent_inputs, scoped by authenticated owner and project; include this directory with request databases in backups. AgentActionsCmd exposes bounded [existing-project editing](EDITING.md) through the same native owners. Codex app-server protocol: [official reference](https://learn.chatgpt.com/docs/app-server).

`library(project_filter, query, archived, offset)` aggregates only the current
login's summaries across accessible registered project databases, 100/page. It
returns project-qualified `key`, `project`, `project_title`, all project choices,
project-qualified folders, `group_revisions` per project and
`unavailable_projects`. Empty `project_filter` means all projects. This read does
not expire foreign requests or alter their queues. `state` stays local and keeps
its independent unfiltered `active_requests`; hosts/idle checks must not use the
aggregate library. The authenticated caller project is restored after aggregation.

Clients default to all projects. Filtering changes only the library. Reading,
writing, continuing, attachment transfers and folder changes route to their
original project with the captured login ticket. Native TH copies its captured
server stub before changing the ticket's project; it never mutates the original
stub or retrieves a different account's current ticket. Draft caches use
`project:request_id`; a new chat in an explicitly filtered foreign project clears
workspace page/type/selection. With no project filter, new chats use the workspace.

Client `refreshError` is distinct from a failed user operation (`error`). A full
successful state/library/read clears only the former. Read polling never replays
submit/message/undo/library writes; an uncertain write retains its pending ID for
explicit reconciliation. Provider/host failures remain the saved request's error.

Host scope: repeat `--project` for an explicit list, or opt into `--all-projects`
for periodic discovery through owner-authenticated `AgentRequestCmd.host_projects`.
This read-only catalogue checks installed inbox/host tables and restores caller
project; it returns no chat messages. It skips missing/unupgraded databases.
New projects join the ordinary heartbeat/claim loop. Discovery never invokes a
model; connection selection and explicit Send still govern data transfer.

## Earlier conversation context

`AgentRequestCmd.history_search(query, project_filter, offset)` is a read-only
owner-filtered history page (20 summaries); `history_read(source_project,
source_request, offset)` reads 6000 transcript characters and returns next_offset.
It preserves caller project and does not expire/replay the source. Source access
uses the same authenticated owner and ordinary project access check.

`link_source(request_id, source_project, source_request)` adds an idempotent
reference to `related_conversations` on a saved draft/finished target. Limit five,
no self-link, active targets/sources and empty sources rejected. First submit
preserves references; message context, permission flags, provider and model stay
independent. This is chat metadata, never a business-object migration or undo.

MCP exposes `agent_conversations`/`agent_conversation_read` only in a host-bound
request. `agent_context` supplies related_conversations. History search/read and
explicit references pass through the chosen connection only after Send invokes
the model; the model should look up earlier context before asking to repeat a
saved task. Reference content is data, not authorization. Attachments in older
transcripts are names, not implicit cross-project check-in inputs.

Frame `request.ui.mjs.permissionActions` owns the three toolbar-menu actions.
Both native ActionMenu and web AppMenu render it; checked permission items use
checkbox semantics. The composer reserves 60 fewer pixels; frozen/pending guards
and default-denied change/internet permissions are retained.


## Last-used composer choices

The five last-used composer values (provider/model/effort and change/web permissions) are restored for new drafts and reopened clients. These are local working-state choices, not project configuration or an expansion of tool authority. TH reads/writes `ui_agent_chat` through the normal login/server-preset-scoped `env_read_config`/`env_write_config` under `ui_main`. TS uses `tactic_stream.agentChat.<login>` in the current origin's localStorage; the application supplies its authenticated login. Only bounded string model/connection choices and boolean flags are retained. No ticket, key, prompt, attachment or selection enters this record.

Only explicit control changes update the saved values; loading history does not. A new draft uses remembered choices, its own existing draft state takes precedence, and an existing sent conversation keeps its captured permissions/model values. Changing model/effort on a finished conversation updates those future model choices without copying that conversation's permissions into defaults. Server validation and per-group tool restrictions still apply to every submitted request.
