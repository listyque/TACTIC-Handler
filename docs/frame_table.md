# Tactic Frame B07: Table View checkpoint

B07 is **in progress**. The table host and adapted cells use shared Frame rules;
the widget-config census still contains 40 usable classes without a complete
native/browser implementation. A registered adapter is not proof that every old
display option or embedded action works.

| Portable module | Responsibility |
| --- | --- |
| `features/table/columns.mjs` | Width priority, hide order and auto-fit |
| `features/table/host.ui.mjs` | Row/header/selection/action geometry, paint and drag targets |
| `features/table/menus.ui.mjs` | Column and saved-view actions and availability |
| `features/table/cells.ui.mjs` | Typed labels, safe links, task-card geometry and compact summary/field scenes |
| `features/table/inline.ui.mjs` | Typed value editor body, explicit-save and uncertain-write states |
| `features/table/widgets.json` | 37 server classes, 87 named aliases, editor choices and native adapter categories |

Stream ships these under `src/tactic_stream/shared_ui`; Handler ships its own
copy under `thlib/ui/qml/tactic_frame`. The server still imports an explicit
allowlist of Python classes. Catalogue data cannot import arbitrary code.

## Owners

Qt ListView and the existing browser row virtualization retain delegates,
scrolling and real input. Application search sessions/ConfiguredView retain
queries and selection. ColumnsEditorController and widget-configuration API
retain definitions, revisions and saved views. Existing EditSObject/TableCellEditCmd
and task controllers retain writes, permissions, rollback and unknown outcomes.
No second database, query engine, script runtime or embedded browser is added.

Native `features/table/ValueEditor.qml` and Vue `TableInlineEditor` render the
same editor scene. Enter commits a single-line value; multiline Enter adds a
newline, and Save commits. Date/datetime/color/multiple values require explicit
Save. Escape cancels. The existing native keyword/tag editor remains specialized;
it has not yet been moved into the shared value scene.

Ordinary cell values are plain text in both hosts, including strings containing
markup. Body text uses the shared resolved pixel size, without point rounding
differences. Tiny fallback avatars stay centered and do not crop their glyph.
Explicit-save inputs keep their draft on an outside click. Progress
groups share their content width and scrollbar reserve; the comparison checks
the actual individual track rectangles as well as the containing table.

## Evidence and reproduction

Run from the Stream checkout using its Python environment:

```powershell
.venv/Scripts/python.exe tools/sync_tactic_frame.py --handler-root D:/code/th_codex --check
.venv/Scripts/python.exe tools/frame_table/inventory.py
.venv/Scripts/python.exe tools/frame_table/capture.py
$env:STREAM_BROWSER_CHANNEL = 'msedge'
node frontend/tests/frame_table.mjs
.venv/Scripts/python.exe tools/frame_table/report.py
```

`capture.py` requires the saved pre-B07 archive and commit identifier under
`.tmp/b07`, created from the tracked B06 Handler checkpoint. It never substitutes
current sources for a missing original. The output is ignored test evidence,
not a shipped application dependency. The report validates source fingerprints.
The archived checkpoint already includes previous Frame migrations; it is not
the original application before Frame.

The matrix contains three themes, light/dark, EN/RU, table widths 360/800/1496,
seven inline input modes and eleven typed/error cell examples. GUI fixtures
exercise production presenters; disposable HTTP/XML-RPC tests separately verify
queries and actual mutation effects. Qt/Chromium font rasterization can differ.

The old `handler_table.mjs` workflow now writes into
`tools/frame_table/output/legacy-driver`, preserving historical reports.

## Remaining B07 work

The executable inventory scans every shipped widget XML and CG template entry;
optional local databases use SQLite read-only mode. It records exact references,
deduplicates aliases and does not execute scripts. Current shipped/template
census: 239 entries, 34 referenced adapted classes, 40 pending classes,
27 previously excluded `pyasm.prod` classes and 3 explicitly unfinished originals.
The catalogue also includes three adapted classes not mentioned by this census.
A read-only scan including all four local project/system databases covers 449
entries and produces the same class/status counts.

Largest pending groups are nested/hidden-row table scopes, Gantt/timecard/work-hour
cells, loader/publish/checkout operations, configurable buttons/custom layouts,
legacy task/status/assignment editors and their child forms. These must preserve
the original workflow through existing owners. Opening a generic inspector does
not implement a configured nested table; drawing a button does not implement its
script. Unknown classes/options stay explicitly unsupported.

Notification recipient tables are bootstrapped through the existing schema
upgrade. This checkpoint adds read projection, not a public notification insert
or email-delivery implementation. PostgreSQL production data, physical touch
hardware and all historical widget options have not been certified.


## Snapshot history files: Stream .198 / Handler .144

Legacy HiddenRowElementWdg targeting tactic.ui.checkin.SnapshotFilesWdg now opens the existing nested table host with a read-only snapshot_files file view. Both shipped procedures resolve membership from Snapshot.get_all_file_objects(), including XML references, instead of selecting every file by parent type or project. Columns retain native web links, repository directory, file type, range, size and timestamp. A non-snapshot owner uses its original publish-context snapshots. The browser table-action Worker copies JSON record context before postMessage, including nested Vue proxies, and disposes its resources if serialization or sending fails. Native Qt script execution has no browser Worker boundary.

This checkpoint does not implement recursive directory-package browsing in this hidden row, downloading a whole frame sequence from its pattern link, or Maya/applet actions. Existing Submit/RV adapters and other legacy gaps are not certified by this fix. Source changes need a BAT server restart and browser reload; no new packaged EXE is qualified here.


The nested shared renderer now falls back to the configured record field when no computed cell is returned, preserving zero, false and deliberately empty computed cells. Both file-table filters prefer file_name over internal code. Validation includes 37 file/nested/value regressions, the browser Worker regression (including disposal after serialization failure), real browser/QML input on three AST001 files from the main SQLite fixture, and direct source reads of all 180 VFX snapshots / 516 files. Three live repository URLs returned byte-identical files. These renderer checks use extracted main-data responses in isolated test hosts; they do not claim that the running server has reloaded Python modules. The offscreen QML comparison uses MD3 dark, EN, Segoe UI, scale 1 at 600 x 320.

Final acceptance: all 156 Frame platform stages passed on unchanged final source fingerprints; native-file-workspace-journey passed its recorded serial retry. Gate: .test-tmp/snapshot-files-platform-verified.log and tools/frame_foundation/output/platform/gate.json (SHA-256 e21385aa7d7ac2b526038834c45dbefaf1a1d03f0807039ac0e2e7f12e6a5c14). Earlier incomplete/failed runs are not acceptance.


## Checkin Log owner captions: Stream .199 / Handler .145

The actual Checkin Log sidebar link uses sthpw/snapshot view log; it is distinct from checkin_history. Its Code cell still named pyasm.prod.web.SnapshotInfoWdg after the namespace exclusion. The original generic owner-caption behavior from legacy/src/pyasm/prod/web/prod_wdg.py now lives in tactic.ui.table.snapshot_element_wdg.SnapshotInfoWdg, with modern public imports only. Parent reads are batched by qualified type and code/id references are retained. Ordinary names/codes follow the original name-code format; missing or excluded owners display n/a. The excluded ShotInstance specialization is not restored. Handler uses its existing value adapter and native get_text_value projection. The built-in log no longer offers RenderLinkTableElement, whose original target is pyasm.prod.web.RenderSubmissionWdg.

The previous .198 checkpoint checked Files in table/checkin_history, but did not certify Code or the other columns of log. The new regression explicitly reads both log and checkin_history through Stream and Handler's query_table_layout and requires every remaining log column to be supported. Fresh HTTP reads of Files before this change already succeeded; the screenshot alone does not establish whether its Files error came from retained browser state or an earlier worker.


Checkin Log live verification for .199/.145: 40 targeted file/widget regressions pass. All 180 main VFX snapshots read through log without unsupported columns or cell errors. The shipped native procedure executed through the running main HTTP server agrees with Stream on 20 owner captions and file descriptors. A fresh browser opened the real Checkin Log twice with an intervening Assets navigation: 20 rows, zero unavailable widgets, zero cell errors, and three links after expanding Files. The main BAT server was gracefully restarted to load the new Python catalogue and left running at 0.112.199. Browser evidence is .test-tmp/checkin-log-browser.json/png; native projection is .test-tmp/checkin-native-live.json. These are test data/profile artifacts and are not packaged EXE acceptance.

Final Checkin Log Frame gate: all 156 stages passed on final source fingerprints, with recorded serial retries of native-file-workspace-journey and native-table. Report: tools/frame_foundation/output/platform/gate.json (SHA-256 a48b0fc52a3ffdb384ad91dcaaefc82defc2a0666c66dd2fd0b40478053e36b7); log: .test-tmp/checkin-log-platform-final.log. The earlier run with a JSON formatting failure is not the final acceptance.
