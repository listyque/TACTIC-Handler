# Tactic Frame B05: Configuration and projects

Configuration and project composition is portable JavaScript under
`shared_ui/features/configuration` and `shared_ui/features/projects`. Handler
ships a physical copy in `thlib/ui/qml/tactic_frame`. Neither runtime imports
the other checkout. QML uses native controls and QJSEngine; no embedded browser.

## Composition and command ownership

| Shared module | Native adapter | Browser adapter | Side-effect owner |
| --- | --- | --- | --- |
| configuration.ui | ConfigurationView | Configuration | Existing per-page drafts and Apply/Save/Reset/Close, shared dirty/clear confirmations |
| settings.fields, settings.ui | features/configuration/SettingsPage and public page facades | FrameSettings | ConfigurationController, browser preferences/appearance/network/debug owners |
| repository.ui | ConfigurationRepositoryPage, RepositoryEditorView | RepositorySettings, RepositoryEditor | RepositoryEditorController; existing server Config revision/validation and RepositoryPathsCmd |
| server.ui | Not a native XML editor | ServerConfiguration + FrameSettings | Existing admin configuration API, interprocess XML lock, revisions and restart policy |
| projects/catalog.ui | ConfigurationProjectPage | ProjectSettings | Native ProjectModel/application; existing project catalogue and workspace activation |
| projects/project.ui | ProjectWizardView | ProjectCreation | Existing creation/template commands, uploads and activation |
| projects/editor.ui | ProjectEditorView | ProjectEditorSurface inside RecordForm | Existing ProjectEditorController/queue; native EditCmd and UploadAction |
| projects/templates.ui | ProjectTemplatesView | ProjectTemplates | Existing template install/download/delete commands and modal host |

The shared layer owns geometry, captions, enabled states, responsive layout and
action records. Controllers retain validation, authorization and persistence.
Apply saves the current page, Save saves pending pages and keeps Configuration
open. Reset affects the current page. These are separate page writes, not a
cross-page transaction. Saving presets refreshes only a clean Server draft,
retaining pending changes elsewhere. Notifications still use their existing
immediate owners. Appearance previews until Apply or guarded discard.

Project editing is modal. The browser's named `configuration_edit` XML view adds
the original record fields and image upload, preserving extra status/palette
fields. Code is read-only. `ProjectArchiveAction` delegates lifecycle changes to
SObject.retire/reactivate after ordinary fields have committed inside EditCmd;
it must not write s_status directly and bypass retire history. The catalogue
returns each project's native search key. Unsupported extra inputs explicitly
block Save; they are never silently converted into text fields.

Creation has four steps, dirty guards, separate image/template operations and
an explicit retry-opening state. An unknown creation result blocks another
creation until the catalogue is refreshed. If the project exists, only opening
is retried. Ticket/context changes invalidate late reads and completions.

## Declared capabilities

- Handler retains endpoint presets, ticket generation, local repository platform
  paths, TEAM confirmation, disk cache, DCC schemas and rendering/tray options.
- Stream uses its current origin, browser-owned preferences/cache and supported
  server XML fields. Client paths and repository web paths remain available.
  Secrets are edited without reading stored values; clearing is explicit.
  Saving XML does not automatically restart the backend.
- Stream keeps project status/palette extras and its browser mode/notes choices.
  Repository Sync and S3 remain excluded; no nonworking browser buttons are added.
- ImagePicker and palette pickers are existing house Views inside shared bounds.
  Window chrome, native file dialogs and browser file inputs belong to the host.
  Project previews use a 160 px square crop; uploaded originals remain intact.
  Narrow selected-image states reserve room for Undo. Invalid images report
  through the containing form; Save waits for image validation.
- Matching-template editing remains with the file/check-in work in B12; its
  existing Configuration link is retained. Native presets already use the B04
  shared composition.

## Reproduction and evidence

From the Stream checkout, use its development Python with Qt installed:

```powershell
python tools/sync_tactic_frame.py --handler-root D:/code/th_codex --copy-from stream
node frontend/tests/frame_configuration_state.mjs
python tools/frame_configuration/capture.py
node frontend/tests/frame_configuration.mjs
python tools/frame_configuration/report.py
python tools/frame_foundation/check_platform.py --handler-root D:/code/th_codex
```

`tools/frame_configuration/output/index.html` is a local, generated comparison.
It includes actual original/current QML, Vue of the same portable native-capability
model, three themes, light/dark, EN/RU, 1100/800/360 px and alternate states.
Dirty-close, cache-clear and template confirmation pairs capture their real modal content; the legacy image
shows the original whole popup. Old screens come from the tracked pre-Frame ZIP;
the later template manager and its dependencies come from Handler commit
`dfd985c040a258d6fa793324f4e985542a4397a8`. Hash checks reject stale or partial
reports. Common coordinates, font settings, colors, indicators and corner radii
are measured; both engines reject truncated action captions. Actual ImagePicker
preview/Choose/Undo bounds are included. This does not assert identical
Qt/Chromium glyph rasterization.

Actual operations are checked separately by Handler's configuration/appearance/
layout/project tests and Stream Transport tests for browser Configuration,
project creation, project editor lifecycle, XML revision/secrets/validation,
repository paths and ACL. Browser scenes use a private SQLite installation and
real commands. They do not mutate the running user server. Native inputs use
isolated configuration and deterministic catalogues; controller worker tests
exercise command branches. Physical touch hardware, live production PostgreSQL
and installing a release on another machine are outside this evidence.

Settings captions reserve common word-wrap bounds for the shipped Segoe UI EN/RU text. Actual Qt and Chromium captures reject clipped descriptions. Arbitrary fonts or new scripts require measured font advances before that scope is advertised.

## Verified release

Handler 0.6.0.109 / Stream 0.112.158: 70 native tests, 456 portable scene
contracts, three disposable-server browser journeys and six focused API scenarios.
The platform gate passes 44/44 stages. The comparison contains 720 original and
1080 current QML images, 1080 Vue pairs, 32,210 rectangles, 18,840 styles and
228 control interiors. Original images are reference evidence; strict geometry
and control comparisons apply to the current native/browser pairs.

## Existing verification limits

The quality-baseline comparison keeps unrelated structure/lint failures visible;
passing it means no new debt and a clean native window smoke, not a clean whole
repository. Browser Transport journeys run in separate processes: its existing
class fixture deletes the temporary data directory between tests while the
update collector is running, which can produce a collector error in a combined run.

The unrelated Stream test
`tests.test_project_creation.ProjectCreation.test_lifecycle_sqlite_and_optional_postgres`
still fails its expected exception-text assertion. The same failure was reproduced
on clean pre-B05 commit `5cc76e9d96f686ec6c6ec059939f17c0137256d7`; B05 does not
claim that test as passed or change the file-transaction exception contract.
