# Batch Dispatcher

The entry point is `scheduler_classes.py`; the queue controller, Maya/TACTIC
work, QML, and optional-token LAN web UI live in `scheduler_core.py`,
`scheduler_domain.py`, `scheduler_ui.py`, `scheduler_web.py`, and
`scheduler_web_ui.py`. Launch it
through `batch/batch_dispatcher_dev` in Handler's Local Python script editor;
`run_scheduler.py` contains that runner. Close the existing dispatcher before
relaunching to load code changes. Invoking the runner while its window exists
brings that window forward without creating another scheduler.

The globe button opens the web dispatcher; the adjacent button copies its LAN
URL. The server can be disabled in Render settings. It uses port `92` by default;
the port persists with the other project settings. Protection is off by default,
so the plain address works across the LAN. Enable it to require the complete
token-bearing link. If Windows asks, allow Python on private networks only.
The browser follows the dispatcher's colors, dimensions, text font, and icon
set, using the same bundled Font Awesome and Material Design font files.

## Working with the queue

1. Check **Render settings**: Maya `Render.exe`, output directory, camera,
   optional per-shot timeout, log check-in mode, dependency-error handling,
   server polling interval, and whether a failed shot pauses the queue.
   The dispatcher uses the `mayabatch` executable beside that `Render.exe`.
2. **+** adds an episode to the queue. Its row shows loading while existing jobs
   remain visible, and the episode leaves the catalog until its queue entry is
   removed. Double-click an episode in the queue to expand or collapse its shots.
   Check or uncheck shots directly there; already-rendered shots start
   unchecked. Active, completed, failed and cancelled shots are locked; use Retry
   for failures/cancellations or add a new run for completed work.
   Adding work while paused does not start the renderer.
3. Press **Start queue**. Exactly one renderer runs at a time. Dependency
   discovery also runs serially so adding many episodes does not flood the API.
   By default a failed dependency download fails that episode. **Skip unavailable
   dependencies** instead records the error and continues its preparation; the
   main Maya scene remains required.
4. Header **Pause after shot** lets the current render and its result save
   finish, then stops queue advancement. The pause button on the active episode
   or shot is different: it finishes the current frame, pauses that same Maya
   process between frames, and resumes it without reopening the scene. A pause
   during preparation prevents Maya from launching. **Stop** cancels the active
   episode; a shot's **Cancel** only cancels that shot.
5. Episode and shot menus can queue a first-frame test render. They also provide
   hold/release, retry failed/cancelled work, ordering, cancellation, log/output access,
   and removal of a whole inactive episode from local queue history. Removing
   an episode does not change TACTIC or delete log files. Completed siblings are
   not rerendered by Retry. Add a new run to deliberately render them again.
6. **Run only this**, in the job menu or on its card, runs that shot or the
   selected episode's included shots, then pauses. Other episodes and sibling
   shots outside this selection are not launched. Wait for any active operation
   to finish first. Failed/cancelled targets use the existing retry path; completed
   shots stay protected. A single-shot run saves that shot and its log without
   changing the entire episode's server status.

Cards expose Run only, Hold/release or active-render Pause/resume, Retry and
Cancel; ordering and file actions remain in the menu. These buttons use the same
queue commands and availability rules as the menu. A shot's frame button accepts
comma-separated frames and
ranges, for example `1-20, 50, 66, 68, 70-150`. Values must stay inside the
shot range; overlaps and adjacent ranges are merged.

**Watch server queue** picks up episodes whose render-task status matches
`queue_statuses`. It does not override the queue's pause state. Repeated polls
do not repeatedly enqueue the same server request. Finishing an episode refreshes
the catalog without removing the currently displayed records first.
Episode cards show their preview, name, description and task status; the status
menu uses colors from that task's TACTIC pipeline. Queue cards retain previews
and indent each episode's shots. Splitters resize both the episode panel and the
log/preview panel.
Episode descriptions occupy one elided line; multiline source text cannot overlap the add button.

## Process visibility and results

An episode contains separate shot jobs. Rows show preparation/render/save stages,
frame progress, elapsed time, estimated remaining time, and a single-line status.
Disconnected ranges run in one `mayabatch` process under the same shot, log,
timeout, progress, and final save. A temporary runner opens the scene once and
invokes Maya's own `mayaBatchRenderProcedure` for each contiguous range. Thus
`1-20, 50, 66, 68, 70-150` starts Maya once, not five times. The runner lives in
the operating-system temp directory and is removed when the shot ends.
Unchecked shots do not contribute completed frames or inflate progress. Full
multiline errors remain in the log and **Details**, not in fixed-height rows. **Details**
shows the command, scene, output and log paths, PID, frame range, and exit code.
The panel header opens the selected render log and can hide the entire panel;
the queue header restores it.
The **Preview** tab follows the selected or active shot and shows the latest
twelve images created below the configured output directory, independently of
renderer log wording. The first arriving frame stays selected while later
thumbnails appear. The global folder button opens the configured sequences root;
each episode card opens that episode's latest output folder. Click a thumbnail to
inspect it and double-click an image to open the file.
A launched renderer is not assumed to be rendering frames yet: before frame
output arrives the stage says it is waiting for Maya. Silence duration remains
visible even when the process prints nothing.

The runner emits stable JSON events for start, completed frames, completed
ranges, success, and failure. Progress and completion therefore do not depend on
Arnold, Redshift, or Maya log wording. The scene's existing post-frame callback
is preserved and our event callback is appended only in the unsaved batch copy.
An exception produces a failure event with its traceback; missing completion is
also a failure. The owned process is stopped after the terminal event, so a Maya
launcher that stays alive cannot stall the queue.

Active-render pause is cooperative rather than an operating-system process
suspend: the post-frame callback waits on a temporary signal file. GPU and
renderer state are therefore left at a frame boundary. Paused time does not
consume the per-shot timeout.

Image discovery remains independent: the output directory is watched for real
image writes, including renderer-specific names and AOV subdirectories. This is
the source for preview thumbnails and the per-episode output-folder action.
ETA is explicitly approximate: it uses current frame progress or the last twenty
successful shots' mean seconds/frame. It excludes future transfer time and cannot
predict differences in scene complexity. Unknown ETA is shown as a dash.

Stdout and stderr go to one complete local file:
`<Handler root>/log/batch_dispatcher/<episode run id>/<shot attempt id>.log`.
The file includes the launch command. The UI retains the last 1000 complete log
events and can filter by episode/shot. Selecting text freezes its display until
selection is cleared; Follow and Freeze are explicit controls. Old attempt log
files remain on disk when a shot is retried.

Normal renders update the shot's configured `rendered_field`. Local logs are
always retained; their TACTIC check-in can be set to always, failures only, or
never. Render logs use episode context `render/<shot title>`. Preparation and
dependency errors use `render/preparation` and count as failures for the
failures-only mode. Cancellation does not mark a shot rendered. Test renders
use frame 1 and do not update server statuses, rendered flags, or logs.

On Windows, Stop terminates only the owned renderer PID and its descendants
using `taskkill /PID <pid> /T /F`. A running repository transfer/server request
must finish before cancellation can advance; cancellation is checked between
transfers and ZIP entries. No unrelated Maya session is terminated.

## Storage and recovery

Settings use `env_read_config` / `env_write_config`, filename
`ui_batch_dispatcher`, project-scoped. Queue state uses `batch_queue` under
`cache/<endpoint hash>/<project>`. The controller is the only queue-state writer;
saves are serialized, coalesced, and use the shared atomic config writer.

The queue retains up to 200 episode runs. Clear finished entries when needed.
Restored work starts held. Previously active shots become failed with an
interrupted-session message; they require explicit Retry after checking output.
The dispatcher does not attach to or relaunch a process from a previous session.
An unconfirmed server save pauses the queue and blocks automatic retry: verify
TACTIC before adding a new run, since that write might already have succeeded.
Close waits for active work and queue persistence before restoring Handler windows.

## Legacy TODO checklist

Source: `custom_scripts/niki_friends/batch/scheduler_classes.py` (read-only
reference). Both checked (`+`) and unchecked entries were traced.

| Original TODO | Implemented path |
| --- | --- |
| `+` Connection twice on restart/start | `show()` reuses its live window; one controller owns workers and timers. |
| `+` Fetch shot data | `_query_shots()` during serialized queue discovery; no request on selection. |
| `+` Test render | Frame 1; no server result/status writes. |
| `+` Extract caches | Repository preset dependencies, per-shot cache ZIPs, direct and one-child-level Alembic assets. |
| `+` Save render logs | `_finalize_shot()`, episode `render/<shot>` context, local log retained. |
| `+` Rendered means excluded | `_query_shots()` reads the configured field; queue checkboxes change inclusion. |
| `+` Global progress | Frame-weighted queue summary and overall progress bar. |
| Refresh schedule after render | `_entry_saved()` refreshes the catalog; stable-identity models retain delegates. |
| Interrupt render | Process-tree cancellation, shot/episode scope, optional timeout. |
| Shot menu actions | Queue checkboxes and job menus: first-frame test, reveal output, hold, retry, cancel, reorder. |
| Color shot statuses | Queue-row colors follow their actual state. |
| Prevent concurrent episodes / queue the next | Serialized episode/shot execution; normal manual enqueue sets the configured queued task status. |
| Restart shots | Retry only failed/cancelled jobs, with a new attempt id and log. |

## Verification

Run from the Handler root:

```powershell
python -m unittest discover -s side_tools/batch_scheduler -p test_scheduler_classes.py -v
$env:QT_SCALE_FACTOR = '1.5'
python -m unittest discover -s side_tools/batch_scheduler -p test_scheduler_classes.py -k qml -v
```

Tests use isolated config files and mocked TACTIC objects; native subprocess
checks launch only short-lived Python processes. Windows process-tree tests
need a context in which `taskkill` can inspect their own child processes.
The QML check creates the actual view at narrow/wide sizes, exercises episode
selection without requests, retained jobs during discovery, delivery of 1000 shots,
mouse/keyboard checkboxes, multiline-error bounds, queue activation,
colored status menus, settings, Escape, scrolling, mouse text selection, and
Ctrl+A, and rejects runtime warnings.
No production render or server check-in is performed by these tests.
