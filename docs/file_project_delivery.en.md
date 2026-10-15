# Perforce-like file projects: installation and acceptance

This feature uses new `file_project` projects alongside Classic projects. Handler
provides the working desktop; Stream provides inspection and administration.
The builtin `perforce_like` template ships in the server wheel; no database dump
or separately downloaded template is needed. Never change a Classic project's
type to install this mode.

## Installation

1. Back up the system database, every project database, configuration and private
   blob storage together before upgrading. On a fresh Python 3.14 installation,
   install the supplied wheel (`python -m pip install "./tactic_stream-VERSION-py3-none-any.whl[postgres]"`
   for PostgreSQL; omit `[postgres]` for SQLite). Existing installations use
   `python -m tactic_stream --data-dir PATH upgrade` with their own configuration.
   A new installation first uses `python -m tactic_stream --data-dir PATH init`;
   enter its new administrator password interactively.
2. In Stream Configuration, enable `files` alongside the current `tactic` and
   optional `queue` services: `services/enable=tactic|queue|files`. Save, then
   explicitly stop/start the server during a maintenance window. Save itself
   does not restart anything. The `files` worker performs verification, staging
   and retention/GC. Check the monitor's running services after restart; a
   configured service is not proof that its process is healthy.
3. Create a **new** project in the project wizard using **Perforce-like file
   project**. The native equivalent, on an authenticated administrator client
   whose current project is `admin`, is:

   ```python
   server.execute_cmd('tactic.command.ProjectTemplateInstallerCmd', {
       'template_code': 'perforce_like', 'project_code': 'files_demo',
       'project_title': 'Files Demo',
   })
   ```

   This goes through the existing Command/CreateProjectCmd/schema installation.
   Reusing an existing project code fails; the template does not overwrite it.
4. Create depot(s), a main stream and workspaces in the file project's Workspace
   actions. Bind each depot to an existing writable repository alias. Private
   blobs live in its sibling `NAME.file-projects`, outside public asset aliases;
   an unbound depot uses `DATA/file-projects`. Give the service account access to
   those directories. Database-only backups cannot restore file contents.
5. Grant users native project/search-type permissions and `file_depot` view/edit
   access for the intended project/depot. Test with an ordinary user: read-only
   users must not upload/checkout/submit; one user's tasks and pending changes
   must not become writable by another. Service execution rechecks the original
   owner's rights; it never publishes their files as administrator.
6. Extract the supplied Handler **source runtime** into a fresh application folder.
   Install its pinned `requirements.txt`, then use `launch.py`/`launch.pyw` and
   the existing server preset/login screen. No saved tickets/settings are shipped.
   Select the new project, create/select your workspace and set its local root.
   Use normalized depot-to-local mappings and exclusions; separate workspaces
   for independent clients. The Classic project keeps its Classic Commit Queue.
7. Set byte/file quotas, parallelism and retention in Stream Storage
   administration before a large run. Defaults are unlimited quotas, 4 byte
   transfers, 7-day abandoned-upload/task retention, 30-day reverted retention,
   permanent shelves and history. GC must preserve published history, shelves,
   Have and active tasks. Start with GC dry-run; never manually delete blobs.

Apache must proxy `/file-project/` as well as the normal API, preserve Range
responses, and permit streaming bodies of at least 64 MiB. Client metadata is
bounded to 1000 entries/3 MiB per command; data batches/blocks are bounded to
64 MiB. Use PostgreSQL for shared installations; SQLite serializes writers.
There is also a project storage-policy lock for quota/reference/GC fencing:
parallel byte transfer does not imply parallel publication transactions.
Contention before the storage-policy lock is acquired returns a marked HTTP 503;
the SDK repeats that same metadata request with bounded backoff. The worker keeps
the queued/running task on temporary contention. This does not retry arbitrary
503 responses, failed triggers, checksums or permission errors.

## Daily operation and recovery

| Scenario | Required result |
| --- | --- |
| Reconcile | Explicit scan shows new/modified/missing files against Have and current server content; hashing stays off the UI thread. |
| Checkout | Ordinary checkout permits multiple holders; exclusive checkout rejects another holder. Locks do not overwrite local files. |
| Upload | Aggregate files/bytes and current path are visible. Upload stages a draft; Submit separately publishes the whole changelist. |
| Shelve/unshelve | Shelf bytes/revisions remain immutable. Unshelve creates a bounded integration; resolve conflicts and finish before Submit. |
| Submit failure | Native rights, hooks and the complete changelist transaction are retained. No subset is published. Refresh before deciding whether to retry a lost response. |
| Get latest | Pinned manifests, SHA verification, durable local replacement, then Have acknowledgement. Modified/untracked local content is protected unless explicitly forced. |
| Stop waiting | Cooperatively stops client work, retaining the server task/journal/partial bytes for Resume. It is distinct from cancelling the server task. |
| Cancel server task | Cancels staging and restores the original pending draft; confirmed published data stays intact. Large integrations may need multiple cancellation chunks. |
| Connection loss | Sign in again if needed, keep the workspace root and upload journal, then Resume. Never create a replacement task merely because a reply was lost. |
| Worker/server restart | Durable tasks are discovered after restart. Retried offsets, manifests, seal, submit and Have do not duplicate versions. |
| Local source changed | Resume refuses a changed source fingerprint. Cancel the old task and start a fresh transfer for the new data. |
| Quota/checksum/ACL failure | Show the server error; do not publish. Correct the cause, inspect the retained draft/task and retry or cancel explicitly. |

Uploads keep their SQLite journals outside the workspace. Do not remove journals
or `.tactic-BLOB.part` download files when you intend to resume. If `files` is
disabled, new uploads fail before server allocation; completed uploads can still
be inspected/retried. Enabling it requires an explicit server restart. A temporary
worker failure with `files` enabled remains resumable and is visible in monitor
status and task progress.

## Qualification and release limits

Archive uploads read at most 1000 blob records in one native Search query. The
storage-policy and changelist locks cover transfer and legacy upload writers;
each blob retains its native edit authorization, SHA verification and commit
hooks. A failure rolls back all metadata and new private bytes in that batch.
Marked storage contention is retried for at most 120 seconds per command/block,
with visible waiting progress and cancellation. Failed upload lease cleanup
also retries marked contention; expiry remains the fallback after worker/network
loss. Ordinary permission, checksum and hook failures keep their refusal/rollback.

Run `tools/file_project_checks.py` (SQLite) and `--postgres` (a new disposable
PostgreSQL container), `tests/test_file_workspace_ui.py` (real Edge browser),
`tests/test_handler_file_workspace_ui.py` (real offscreen Qt), and
`test_monitor.Runtime.test_owned_file_worker_restart_and_real_transfer`.
`tools/file_transfer_benchmark.py` creates fresh random bytes and verifies an
HTTP upload/submit/download/Have roundtrip. `tools/file_project_scale.py` measures
catalog/version/Have metadata; it does not transfer a million physical files.
All fixtures own their resources and remove their processes/containers afterward.

The delivery's `verification/` contains portable native/transfer/monitor fixtures.
With the wheel installed, run `python verification/tools/file_project_checks.py`;
add `--postgres` for the disposable Docker checks. For worker recovery, set
`PYTHONPATH` to `verification/tests` and run `python -m unittest
test_monitor.Runtime.test_claimed_upload_recovers_after_file_worker_process_death`.
Its injected process death leaves a committed 60-second task lease; recovery is
bounded by that lease, not instantaneous. SHA-256 for each supplied file is in
`manifest.json`; the qualification report is separate from manual acceptance.

On the checked Python 3.14/PySide6 6.11.1 and 6.11.2 runtimes, enabling Python
ResourceWarning diagnostics reproduces an uncollectable `Property` at interpreter
shutdown even with one plain QObject property and no application/network/threads.
This warning is not suppressed or counted as a clean resource-acceptance pass.
The regression fixtures still stop their workers and delete their owned windows.

The delivery contains a server wheel, Handler sources and recorded evidence.
It is **not** a Windows EXE/Electron or a production acceptance certificate.
Physical million-file/TB runs, the target network/storage, installation on a
clean target Windows machine, and full Handler manual release acceptance must
be signed off separately. Keep the existing application release gates; never
mark those scenarios passed from an offscreen or metadata-only test.
