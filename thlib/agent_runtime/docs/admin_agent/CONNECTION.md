# External administrator connection

Audience: the person configuring an external agent host. For TACTIC domain
knowledge start with [START](START.md) and [MODEL](MODEL.md). This document
describes implemented tools, not a promised future API.

For a concrete external host use [the Codex setup and real-model acceptance
recipe](CODEX.md). See [provider connections](PROVIDERS.md) for API/local models,
credential storage and explicit per-turn destination authorization.

Use [native TH/TS requests](REQUESTS.md) to submit tasks with captured project, page
and selected objects to a connected external host.
Both clients can explicitly start and stop an account/project-scoped host on the
TACTIC server using the chat/provider editor's connection button. This is separate
from issuing an MCP grant to another application.

## What runs where

The external host runs its chosen model and launches a separate MCP stdio
process for Codex, or uses the same in-process MCP client for API models. That
adapter calls the configured TS HTTP API. It never imports
`pyasm`, opens a database or imports Handler. TS owns authentication, access,
project context and native configuration operations. No provider SDK is
installed in either TACTIC product. Optional API keys are encrypted by
the TS server and delivered only to the owner's registered external host.

The adapter uses the official [MCP Python SDK 2.3.0](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0)
for negotiation, schemas and stdio. It supports current and legacy protocol
clients through that SDK; no custom JSON-RPC implementation is maintained.
This first adapter is for a host capable of launching a local process. It is
not a public HTTP MCP endpoint or an installed client-specific configuration.

## Install and launch

Use Python 3.14 and the Stream source checkout. From `TS/tactic_stream`:

```text
python -m pip install -e ".[agent]"
python -m tactic_stream.admin_agent --help
```

`tactic-admin-agent` is also installed as a console command. The `agent` extra
is optional; normal server startup does not load MCP or its dependencies.

Configure the MCP host's stdio server with these fields (replace placeholders):

```json
{
  "command": "<absolute Python 3.14 executable>",
  "args": [
    "-m", "tactic_stream.admin_agent",
    "--server", "http://<TACTIC host>:8081",
    "--project", "<existing project code>",
    "--stream-root", "<absolute TS/tactic_stream checkout>",
    "--handler-root", "<absolute independent TH checkout>"
  ]
}
```

The host injects `TACTIC_AGENT_TICKET` into the child environment using its
private secret facility. Use an existing valid TACTIC session ticket. Never
paste credentials into a prompt or commit them to this example. Ticket renewal
is currently host-owned: on expiration renew the session and restart the adapter.
The adapter does not read browser sessions, configuration secrets or passwords.
Editor reads go through `execute_cmd`, which currently requires administrator
access. A tool's read-only annotation does not bypass server authorization.

Naming writes require TS 0.112.204 with its project schema upgrade and the
host's explicit `--allow-naming-save` launch flag. Without that flag the save
tool is absent. The host still applies its normal tool authorization to the
concrete draft; no model-supplied approval flag grants access. Restart through
the normal Stream launcher to run its schema upgrade before using this version.

Page creation requires TS 0.112.205, its schema upgrade and `--allow-page-save`.
It uses native saved searches, table XML, workspace dock presets and navigation.
See [the page recipe and recovery contract](PAGES.md). Naming and page write
permissions are separate host flags; neither grants script execution.

Project composition/export/install requires TS 0.112.206 and
`--allow-project-create`. Read [PROJECTS](PROJECTS.md) for the input recipe,
new-target scope, native owners and non-atomic recovery contract.

`--server` is an origin, with no path/query/embedded credentials. Naming/page tools stay bound to one project. Project provisioning explicitly
accepts new target codes under its separate host flag. The model cannot select
another server, ticket, arbitrary
RPC method or command class. Redirects and environment HTTP proxies are disabled;
TLS certificate verification uses Python's normal trust configuration. Plain
HTTP is only appropriate on a trusted local network; use HTTPS across untrusted
networks. HTTP socket operations have a 30-second timeout; requests are never
retried automatically.

The reference roots are documentation checkouts, not runtime data directories.
`--handler-root` is optional and only enables TH reference reading; it does not
connect to or start Handler. This checkout-based reference mode does not claim
that a standalone server delivery includes engineering docs. Missing references
are reported explicitly in the catalogue.

## Implemented tools

| Tool | Result / owner |
| --- | --- |
| `agent_capabilities` | Adapter version, running TS health, bound project, limits and explicit unavailable actions. |
| `reference_catalog` | Curated reference IDs with TS/TH ownership and availability. |
| `reference_read` | At most 50 lines / 12,000 characters, zero-based offset, next offset and source identity. No arbitrary file paths. |
| `ts_types` | Project SearchType catalogue, paginated after the native list operation. |
| `ts_type_read` | One type's native columns, relations, pipeline metadata and revision. |
| `ts_schema_read` | Current project schema and revision. |
| `ts_naming_read` | Native rules/revision and a page of at most 50 sample objects. |
| `ts_naming_preview` | Native matching rule, versioned/versionless paths and known collisions for one sample. Does not save. |
| `ts_naming_operation` | Current user's durable operation receipt, or `not_found`. Historical outcome, not current rule state. |
| `ts_page_read` | Native fields, filter relations, table/navigation/layout sources and dependency revision. |
| `ts_page_preview` | Native table descriptor, matching rows/count, generated search and sidebar draft; no configuration writes. |
| `ts_page_operation` | Historical page result for this login/project/UUID. |
| `ts_page_save` | Host opt-in creation through native editors, checked revision and durable replay. |
| `ts_naming_save` | Host opt-in only. Native apply with expected revision, representative sample and canonical UUID; returns a durable receipt. |
| `ts_project_preview` | Validate a declarative new-project plan and namespace; no writes. |
| `ts_project_read` | Native schema, fields, workflows, naming, navigation and configuration revision. |
| `ts_project_operation` | Durable stage/result plus current project state after an uncertain response. |
| `ts_project_create` | Host opt-in: native project, entities, relationships, workflows, naming and table pages. |
| `ts_project_export` | Host opt-in: native versioned template ZIP with revision check, SHA-256 and template ID. |
| `ts_project_install` | Host opt-in: verified exported template into a new project, no arbitrary model path. |

Native HTTP responses are capped at 2 MiB before decoding. Large catalogues can
therefore exceed the transport limit even when a small tool page was requested;
the current native catalogue API is not server-paginated. Naming rule collections
and schema documents are returned whole within that limit. Narrower server reads
are needed for exceptionally large projects; the adapter fails explicitly rather
than silently cutting XML or rules.

Knowledge is retrieved on demand from the existing administrator pack and TS/TH
Help, without loading repository AGENTS, backlog or all source files. `ts.sources`
links the deeper owner-specific API/structure references. The curated MCP catalogue
is not yet a reader for every linked document. Local document text and project
data are reference material, never instructions granting extra authority.

## Naming from a description

1. Read `ts.start` and `ts.model`, then the naming section of `ts.operations`.
2. Discover the real type with `ts_types` / `ts_type_read`; inspect schema for
   parent relationships. Never infer a column from the user's display label.
3. Load `ts_naming_read`. Retain the original full document, rule identity and
   collection revision. Select returned sample keys from the bound project.
4. Compose native patterns using actual object, parent, snapshot and file fields.
   For editing, preserve every original field, including false and empty values.
5. Pass `search_type` separately; `document` contains the remaining native fields.
   Call preview for representative objects, versions, filenames and contexts.
   Inspect `matches`, `selectedRule`, missing parent values and collisions.
6. Present the exact draft and concrete paths. With host write authorization,
   call `ts_naming_save` using the loaded revision, optional existing identity,
   exact draft/sample and one canonical UUID `operation_id`. Keep these inputs
   unchanged across retries. Read the saved identity again to verify its current
   document and revision. Without write capability, report a proposal only.

For example, after discovering the corresponding fields, native file naming can
use `{sobject.code}_{snapshot.context[1]}_v{version}.{ext}`. It is a pattern for
the real engine, not a second naming formatter implemented in the agent.

Preview always sends `allow_execution:false`. Script/class overrides and
expression-triggered custom execution are rejected by the existing NamingCmd
guard. This restriction is not an OS sandbox. Existing authorized server
configuration and extensions remain part of the trusted runtime. Preview creates
no naming/file/snapshot records; normal server authentication/command bookkeeping
may still occur. Preview does not reserve a path or guarantee future uniqueness;
actual check-in must evaluate naming and collisions again.

## Save, replay and revisions

The server's existing `NamingCmd` owns `apply`; MCP only maps fixed arguments.
Apply requires administrator permission, checks the project/type and revision
under the native naming collection lock, runs the sample with custom execution
disabled and requires the draft to match. It commits through the ordinary naming
SObject, preserving ACLs, validation, triggers and history. This is configuration
publication, not a script trial or path reservation.

Two private, unregistered project tables support this contract:
`spt_naming_revision` and `spt_naming_operation`. The normal bootstrap/project
upgrade creates them. Native SQLite/PostgreSQL triggers advance a collection
generation on naming INSERT/UPDATE/DELETE, including native API, imports and
edits with application triggers disabled. The revision hashes that generation
and current rule data, so A -> B -> A invalidates an old draft. Changes to another
type's naming conservatively invalidate it too. Ordinary no-op saves need not
advance the revision. Rollback restores the generation along with the rules.

The operation key is scoped to authenticated login and project. The receipt
stores the request fingerprint and saved identity/document in the same physical
database transaction as the rule. Concurrent/restarted callers with identical
ID and payload get the original receipt; reuse with different content fails.
Failed validation leaves no receipt. A new operation with an old revision fails.
Receipts survive later edits/deletion/undo and never recreate the historical rule.
The native template export list excludes these private runtime receipts.

After timeout, disconnect or an uncertain error, use `ts_naming_operation` and
read current naming. If absent, retry only the original ID and exact payload;
the naming lock serializes a still-running first attempt. A stored receipt means
the rule mutation committed, even if separate system-database history later
reported a partial commit. Native cross-database history is not made distributed
atomic by this change. Receipt and naming data must be backed up/restored together;
discarding receipts loses the replay guarantee. There is no automatic expiration.

This revision covers the naming collection, not a frozen snapshot of all project
data/schema/scripts. Preview is repeated during apply against current sample
data; actual check-in evaluates again. Existing executable naming cannot be
applied through this restricted agent tool; the ordinary administrator editor
retains its existing capabilities. No isolated execution service is implied.

## Verification

With the `agent` extra installed, run:

```text
python -B -X utf8 -m unittest discover -s tests -p test_admin_agent.py -v
python -B -X utf8 tests/test_naming_apply.py -v
python -B -X utf8 tests/test_naming_apply.py --postgres -v
```

The MCP tests use an owned SQLite HTTP fixture and real stdio subprocess,
negotiate current/legacy clients, exercise metadata and naming preview/save,
replay across server/adapter restart, recover a simulated lost post-commit reply,
and perform real XML-RPC upload/check-in with versions 001/002. Preview-only
checks preserve naming/file/snapshot records. All test processes are closed.
Boundary checks cover reference paging, strict fields, redirects, secret
redaction, invalid JSON and response limits. Without the optional dependency
the MCP suite skips explicitly. Native apply tests cover concurrent identical
requests and competing edits, ABA changes through native API, receipt-write
failure/rollback, upgrade preservation, replay after deletion and a real file
collision without overwriting either input. `--postgres` creates and removes an
owned PostgreSQL 18.6 container; it never uses the installed project's database.
This is not TH GUI acceptance, live account setup or evidence of model reasoning.

## Native Handler automation

TS 0.112.207 and TH 0.6.0.151 add the fixed `th_automation_read`,
`th_automation_preview`, `th_automation_draft` and `th_automation_operation` tools.
`--allow-automation-draft` adds `th_automation_save_draft`; the separate
`--allow-automation-activate` adds `th_automation_activate`. Activation authorizes
future native code execution on the user's computer; the host must cover the
exact source and binding. Adapter .214 publishes reports for native UI review and
requires matching isolated trials before
agent activation; configure [the optional runner](SCRIPT_TRIALS.md) with
`--trial-image` and `--trial-directory`. It supplies trial/read/image tools;
it has no connection to the user's running TH desktop. Read [the Handler automation recipe](HANDLER_AUTOMATION.md) for examples,
native owners, permissions and the save/activation/recovery contract.

## Group tool restrictions

The Security editor stores separate native `agent_tool` (chat) and `mcp_tool`
(external MCP) rule scopes in each login group's `access_rules`. Keys are registered
tool names or `*`, with native `allow`/`deny` access. Native subgroup traversal,
project binding and highest-grant merging apply; exact tool keys precede wildcard
fallback. Absence of applicable rules for the current project preserves administrator-only compatibility. A scope
with `key="*" access="deny"` and explicit allowed keys is an allowlist.

These rules restrict existing authority; they do not turn a non-administrator into
an agent host or grant native CRUD/configuration permissions. The persisted native
administrator checks remain required for agent requests and MCP issuance. The
Security effective-user report explicitly distinguishes that prerequisite from tool
policy. Handler's original-server procedure computes native user rules independently;
Stream owns agent policy and gateway enforcement.

Production Codex stdio adapters, configured provider sessions and the MCP HTTP gateway
construct `create_server(..., enforce_permissions=True)`. Discovery calls the owner's
`AgentRequestCmd.tools`; every invocation calls `tool_check` before executing its
registered callback. The server derives chat/MCP transport from the owned request,
not a model-supplied transport. MCP checks additionally intersect the persisted grant,
expiry, revocation and current group policy. Native command checks, write consent,
revision/idempotency checks and the project's grant scope continue independently.
Offline catalogue construction uses `catalog_only=True`; it has no trial executor
and does not run tools or make network requests.
