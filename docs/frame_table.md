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
