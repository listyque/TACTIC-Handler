# Child file ingest

`IngestFilesController` owns batch ingest for a selected child-relation row.
Dropping files on that relation uses the built-in rule immediately and does not
open a window. The relation's **Add files** action opens `IngestFilesView` so the
same batch can be reviewed and a project rule can be selected or edited.

Each accepted file is uploaded and passed to TACTIC's native
`tactic.ui.tools.IngestUploadCmd`. That command creates one child Search Object,
connects it to the relation parent, maps the filename without its extension to
`name` (or `code` when the type has no `name`), and checks the file into the
configured process and context. The built-in rule uses `publish` for both.

Saved `config/ingest_rule` records are optional. Their filters, path tags, extra
values, update mode, keywords, context behavior, icon generation, validation
script, and process script are projected into the editor. Rule scripts run on
the TACTIC server with the legacy `path`, `sobject`, `parent`, and `snapshot`
inputs before the native command commits anything. A validation rejection skips
only that file. A file failure does not discard successful siblings.

All uploads and server commands run through the server pool. Cancellation stops
between files. Results are applied to the Qt models on the owning thread, cache
domains are invalidated once per successful batch, and the active search is
refreshed only while the originating relation still exists.
