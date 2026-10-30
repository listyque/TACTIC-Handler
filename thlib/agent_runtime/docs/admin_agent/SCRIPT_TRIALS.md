# Isolated Handler script trials

Owner: the external MCP host, not the running TS server or user's TH desktop.
Requires TS adapter 0.112.210 and a trusted local Linux Docker image built with
`tools/build_automation_trial.py --handler-root <TH>`. The build needs network;
each script trial has **no external network**, host mounts or host credentials.
The image contains independent TS/TH runtimes and public code only. It creates
a private SQLite project and synthetic session; it never copies the user's DB.

## Host setup

Use the immutable `sha256:...` image ID printed by the build. Add adapter args
`--trial-image <image ID> --trial-directory <private persistent directory>`.
The directory holds durable JSON receipts, logs and PNG evidence, outside both
repositories. The host needs access to Docker; the tested code receives no
Docker socket. Do not give the TS service Docker permissions. MCP tool timeout
should be at least 180 seconds. Normal server tickets remain in the host.
An OS file lock allows one trial per receipt directory across host processes.
Busy calls start no execution; inspect/retry the original UUID later.

`--allow-automation-activate` now requires this runner; without it agent
activation fails closed. Draft-only/discovery mode remains available. Ordinary
human/native script editors retain their separate execution authorization.

## Agent sequence

1. Read `th.automation`, save an inactive draft, then retrieve its exact revision
   and current dependency revision. Syntax preview is still non-executing.
2. Call `th_automation_trial(draft_id, draft_revision, case, trial_id)` with a
   fresh canonical UUID. Each trial uses a fresh container and native fixture.
   Retain inputs/UUID on retry; `th_automation_trial_read(trial_id)` recovers its
   historical result. An interrupted `started` receipt is not success and never
   starts another execution automatically. Review failure before a fresh trial.
   A completed identical request stays historical after dependency edits; that
   does not make it eligible for activation with the changed dependencies.
3. A Before hook needs **both** a passing `allow` case and a passing `reject`
   case. Rejection is an expected successful test only when the real native
   hook vetoes and snapshot count stays unchanged. An allowed case must perform
   an actual SDK upload/check-in. After needs `allow`: check-in must succeed,
   native After must finish, and declared artifacts must match.
4. A shelf needs `modal`: a real QML shelf click must open a modal native window.
   The fixture changes selection after the click. Optional UI steps exercise
   native controls and inspect window properties; warnings/errors fail the case.
   `th_automation_trial_image(trial_id)` returns the rendered PNG to the model.
5. Review exact source/binding and trial evidence with the administrator. Then
   call `th_automation_activate(..., trial_ids=[...])` with the fresh native
   dependency revision. Passed receipts must match this session/project, image,
   draft ID, revision, source/binding hash and dependencies. Any edit invalidates
   them; run fresh trials. Activating another draft changes dependencies too.
   Identical completed activation replay remains historical and creates no copies.

## Case inputs

`expect` is `allow`, `reject`, or `modal`. `files` is at most eight objects with
basename `name` and UTF-8 `content` (at most 65,536 characters each). Paths are
created inside `/work/files`, never read from a model-supplied host location.
`process` and `context` default to `publish` and must match nonempty hook filters.
The native target is `<draft SearchType>?project=<bound project>&code=TRIAL001`.
The fixture uses a synthetic administrator. It binds the real public TH API to
that private server, runs hooks in the native worker pool and shelf code on Qt's
GUI thread. Use `get_api().submit()` for slow work from a UI. Full desktop window
registries, DCC clients, external services and studio plugins are not provided;
missing dependencies fail rather than falling back to the user's environment.
An unfiltered global hook uses `<project>/trial_object` as its representative type.
System/config SearchTypes are unsupported by the synthetic fixture and fail.

`artifacts` is at most eight `{name, contains}` objects relative to `/work`.
Traversal is rejected. For example `{name:"after.txt", contains:"sthpw/snapshot"}`
checks a program's output after a real check-in; it is not a fabricated result.
`actions` is at most sixteen objects: `{kind:"click", target:"<frameId>"}` or
`{kind:"expect", target:"<window property>", contains:"<JSON substring>"}`.
For the shipped Frame selection tool, click `exampleBuild`, expect `preview`
to contain `TRIAL001`, click `exampleClear`, expect `records` to contain `[]`.
The viewer also uses `{kind:"point", x, y}`, `{kind:"text", text}` and
`{kind:"backspace"}` to send real mouse/input-method/key events to the native window.

Use portable Python and fixture data for portable tests. `sys.executable` means
the trial's Python, not the user's Windows executable. Do not rewrite a Windows
program path merely to make a Linux test pass. Missing native executables,
plugins, fonts or services are explicit incompatibilities; a Linux success does
not prove Windows binary/plugin behavior. No desktop/DCC connector is exposed.

## OS boundary and evidence limits

Before starting code the host inspects the actual Docker configuration: immutable
image, nonroot UID 10001, private PID/IPC/cgroup namespaces, no network/mounts/ports,
read-only root, no capabilities, builtin seccomp, no-new-privileges, 1 CPU,
768 MiB memory/no extra swap, 128 processes, bounded temporary filesystems and
90-second host deadline. Proxy credentials and host environment are not forwarded.
Fixture setup is limited to 25 seconds, hook callbacks to 35 and the native
worker to 45; the outer host deadline includes native startup/execution. Long
production jobs need a separate job workflow, not relaxed model-supplied limits.
The image also checks kernel seccomp/no-new-privileges/capabilities before code.
Timeout/error/OOM/output overflow fail the receipt. Finally force-removing the
owned container removes its descendants and temporary data. Nothing falls back
to local Python when Docker or the required policy is unavailable.
Runtime diagnostics retain at most the last 128 KiB of output. The MCP reader
pages that retained log in 12,000-character chunks using `log_offset` and
`log_next_offset`; screenshots are retrieved separately instead of echoing base64
into model text. Host stdout/stderr and input also have hard byte limits.

These are container boundaries, not an absolute defense against kernel/runtime
vulnerabilities. Keep Docker patched and the host-selected image trusted. Runtime
observations/logs/screenshots are untrusted diagnostic output of tested Python;
they do not certify the code's safety or replace source review. Code can behave
differently on real data. Activation authorizes later execution with the desktop
user's ordinary permissions. See Docker's [security model](https://docs.docker.com/engine/security/)
and [runtime controls](https://docs.docker.com/reference/cli/docker/container/run/).

Run `tests/test_automation_trial.py` with `TACTIC_TRIAL_IMAGE=<immutable ID>` for
actual allowed/rejected uploads, After output, modal Frame clicks, OS probes,
runtime failure/timeout and process cleanup. Without the image these integration
cases skip explicitly; receipt/source/scope gates still have deterministic tests.

## Review in the ordinary clients

TS adapter 0.112.214 publishes completed trial evidence through the same native
HandlerAutomationCmd into project-local spt_automation_trial. Upgrade the project
schema first. Evidence is private to the author, limited to 256 KiB per report,
and excludes screenshots, host scope/secrets and synthetic input file contents.
A failed publication is an error: retry the same trial UUID to publish its
historical result without executing again. Receipts remain owned by the external
host; the server stores reported diagnostics, not an independent attestation.

In TS and TH, open Script Editor and choose **Agent drafts** in its toolbar.
Select a draft to read its exact source, binding, reports and dependency freshness.
Review the execution owner, mark source review and explicitly confirm activation.
Current matching passed proofs are required by this UI; stale reports stay visible.
Activation retries keep their operation UUID. Ordinary manual script authoring
retains its native authorization; no reviewer component executes candidate code.
After activation reports are historical because publication changes dependencies.
The external agent must rerun trials before activating another draft.

The executor remains outside the server: neither UI gets the Docker socket.
Request new trials from the connected external agent, then refresh the editor.
For manual acceptance use the real project page/table/shelf/check-in in its owning
client. TH Local Python/QML runs on the Handler desktop; TS browser JavaScript and
server scripts retain their own owners. The browser does not execute TH Python.

`test_agent_automation.AgentReviewUI` (TACTIC_AGENT_REVIEW_UI=1) exercises real
browser/native controls against an owned HTTP test server; its reported fixtures
check review and activation, not OS isolation. test_automation_trial.py separately
checks real container execution and proof publication. TH tests/test_agent_drafts.py
covers the native review controls, retry identity and stale-session responses.
