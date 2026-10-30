# Native Handler automation from a description

TS stores configuration; TH executes it on the user's computer. Start from
[MODEL](MODEL.md) and retrieve this recipe as `th.automation`. TH's
[public API](../../../../TH/docs/handler_api.md),
[Script Triggers Help](../../../../TH/thlib/ui/help_articles/script_triggers.en.md),
[Script Shelf Help](../../../../TH/thlib/ui/help_articles/script_shelf.en.md) and
[Frame script contract](../../../../TH/docs/frame/scripts.md) describe the separate
client execution environment. Never run a desktop program through server Python.

Requires TS 0.112.207 with upgraded project schema and TH 0.6.0.151. The external
adapter uses the host's existing server/project/ticket; it does not connect to a
running TH process. Refresh saved scripts, triggers and navigation in TH after
publication (or reopen the project). The browser can display the shared
configuration but cannot execute Local Python or open a native desktop tool.

## Draft, check, save, then enable

1. `th_automation_read()` discovers current hooks, native script paths/languages,
   shelves, navigation and a dependency revision. Preserve existing configuration.
2. `th_automation_preview(document)` validates binding fields and compiles Python
   syntax **without executing it**. It is not a script trial or an import check.
3. `th_automation_save_draft(document, expected_revision, operation_id)` requires
   the preview's revision and host flag `--allow-automation-draft`. It stores
   private inactive draft metadata; it creates no script, hook or shelf action.
4. `th_automation_drafts()` lists the author's drafts in this project.
   `th_automation_draft(draft_id)` returns that administrator's exact source,
   draft revision and current dependency revision. Show the concrete code,
   execution owner, program paths/arguments and binding to the administrator.
   Completed trials are also published for normal TS/TH Script Editor review.
   To revise an inactive draft, preview the new document and pass `draft_id`
   and its original `draft_revision` to `th_automation_save_draft`, retaining
   the new preview `expected_revision` and a new write UUID. Old reports stay
   visible but no longer qualify; an activated draft cannot be rewritten here.
5. `th_automation_activate(draft_id, draft_revision, expected_revision, operation_id, trial_ids)`
   requires the separate host flag `--allow-automation-activate` and authorization
   for this exact code and binding. Server administrator and native script
   execution checks still apply. It creates a normal `local_python` saved script
   and enables the hook or shelf assignment in the same project transaction.

The optional external-host [isolated trial runner](SCRIPT_TRIALS.md), retrieved
as `th.trials`, executes exact inactive drafts in a verified offline Linux
container with synthetic data and native TH consumers. Agent activation requires
matching passed trial IDs and a configured host runner. Before needs both allow
and reject cases; After needs allow; shelf needs a modal UI case. Preview remains
syntax-only. Native/human activation remains a separate authorized operation.
Inspect capabilities rather than assuming the runner is configured. Activation
still authorizes later execution with the desktop user's ordinary permissions.

Use one canonical UUID and identical arguments through each write's retries.
`th_automation_operation(operation_id)` recovers historical success after a lost
reply or restart. Changed-payload reuse fails; a receipt never reapplies a later
deleted binding. Draft, script, binding and receipt use the native project DB;
separate system history retains TACTIC's existing cross-database limitations.
Native INSERT/UPDATE/DELETE generation triggers track script, hook and widget
changes, including API/import writes with business triggers disabled. Human edits
invalidate activation's dependency revision. Runtime draft/receipt tables are
private metadata, excluded from native template export; back them up with the DB.

## Check a program before publication, run another afterwards

Create two `kind:"hook"` drafts. Their fixed native action is `snapshot.save`;
`phase` is `before` or `after`. Optional `search_type`, `process` and `context`
restrict the hook. Every field must use discovered server identifiers. Example:

```python
document = {
    "kind": "hook", "title": "Validate shot file", "phase": "before",
    "search_type": "studio/shot", "process": "publish", "context": "publish",
    "source": """from tactic_handler_api.automation import run_checkin_program
RESULT = run_checkin_program(
    [r'C:/StudioTools/validator.exe', '--input', '{file}'],
    TACTIC_SCRIPT_KWARGS, timeout=60, per_file=True)
"""
}
```

The executable path belongs to the **client computer**. Get it from the user's
environment; a server-side file check cannot establish its availability. The
helper accepts an existing absolute program and explicit argv, uses no shell,
rejects Windows batch files, captures stdout/stderr, and requires exit code zero.
Missing executable, nonzero exit or timeout raises and blocks a Before action.
`timeout` is in seconds, greater than zero and at most 300. `per_file=True` runs
each captured input; a `{file}` token with multiple inputs otherwise fails.

Supported argument substitutions: `{file}`, `{project_code}`, `{search_key}`,
`{process}`, `{context}`, `{operation_id}`, `{result_search_key}`. They are data,
not shell commands. An After hook can pass `{result_search_key}` to its program;
the completed snapshot descriptor is also in `TACTIC_SCRIPT_KWARGS['snapshot']`.
The TH payload contains `files` as a list of **descriptors**, not strings:
`[{"path": "<captured client file path>", ...}]`. There is no singular `file`
payload key. To derive a sibling output path use
`Path(TACTIC_SCRIPT_KWARGS["files"][0]["path"]).parent / "after.txt"`.
`{file}` is the helper's argv substitution, not a payload field. Other captured
fields include `project_code`, `search_key`, `process`, `context`, `operation_id`;
`result_search_key` and `snapshot` are populated for After publication.
File paths are captured before enqueueing; normal queue operation IDs survive
restart. An exception must escape a Before script: returning False does not veto.

After errors are logged and shown in Script Editor; they cannot undo publication
and do not stop later After hooks. Before cancellation is checked again when
the hook finishes. An unrelated Before operation is rejected while a hook runs,
never silently allowed; After hooks are deferred. Changing projects rejects stale
work. These are client hooks: headless API uploads and other clients can bypass
them. They are not server enforcement or exactly-once external side effects.
Retrying an action can run its program again. Trusted programs own cleanup of
their own child processes and any external side effects after timeout.

## A shelf button opening a native custom UI

Choose an existing sidebar identity from `th_automation_read.navigation` and
form `entry_key` as `<display search_type>@<entry name>`. A `kind:"shelf"` draft
requires that exact key, a title, Local Python source and optional icon/description.
Activation preserves the currently effective shared buttons in a new tab shelf,
adds the action and assigns it only to the selected sidebar entry. Personal and
other tabs' shelf documents stay separate. Reusing an existing shelf title fails
explicitly rather than overwriting it. Existing editors remain the owner of
subsequent edits/removal; do not rewrite merged definitions through a generic API.

The saved script receives a captured `TACTIC_SCRIPT_KWARGS` with `project_code`,
`entryKey`, `tab_id` and selected `search_keys`. Local Python executes on TH's GUI
thread for UI creation. Use native workers/public API `submit` for slow work.
The original context is restored after the script returns. Example source:

```python
from side_tools.frame_tool.showcase import show

show([
    {"id": key, "title": key}
    for key in TACTIC_SCRIPT_KWARGS["search_keys"]
], modal=True)
```

This existing [small Frame tool](../../../../TH/side_tools/frame_tool/README.md)
demonstrates shared controls, a virtualized selection, existing engine ownership,
modal native window and cleanup. For a different tool compose the existing Frame
controls and native window owners according to the script contract. Do not create
another QApplication, browser/WebView, background UI thread or a copy of the
application's window controls. UI callbacks must retain the captured project and
selection rather than looking at whichever tab is current when a worker finishes.

## Native tools and verification

In a Handler worker/API session use `th.project(code).automation` with methods
`read`, `preview`, `save_draft`, `draft`, `activate`, `operation` and `save_hooks`.
These same fixed methods are in the existing remote domain contract; no Qt
objects or arbitrary native attribute names cross it. `save_hooks(rules,
expected_revision, operation_id)` atomically replaces only Handler hook records
and is also used by the ordinary trigger editor. It preserves unrelated server
triggers. An outdated TS server/schema fails explicitly; there is no fallback
to the old multi-RPC write sequence.

Owners: [server command](../../src/tactic/ui/panel/handler_automation_cmd.py),
[input](../../src/tactic_stream/automation_plan.py),
[TH public API/helper](../../../../TH/tactic_handler_api/automation.py),
[TH hooks](../../../../TH/thlib/ui/script_triggers.py),
[TH shelf](../../../../TH/thlib/ui/script_shelf.py).

[test_agent_automation.py](../../tests/test_agent_automation.py) uses actual MCP,
HTTP, native Handler public API, rejection before upload, real SDK check-in, the
After program, a real shelf click and modal QML lifecycle on owned data. Native
SQLite/PostgreSQL cases cover inactive drafts, revision conflicts, durable replay
and rollback. TH's focused script/editor/queue/API suites cover errors, cancellation
and controls. This is not a full installed EXE acceptance run or evidence of an
external model's reasoning. Test fixtures are trusted test code, not an isolated
trial service for generated user code; [test_automation_trial.py](../../tests/test_automation_trial.py)
checks the separate OCI runner and its exact-source activation gate.
