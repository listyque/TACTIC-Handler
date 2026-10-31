# Tactic Frame: Configuration and projects

Handler's authenticated project bootstrap publishes `server_api` from the native
server API implementation. `env_inst.server_api` binds the result to the exact
address/login/ticket; cached catalogs cannot promote an unknown session to
Stream. The application exposes `server_api` and `is_stream_server` and hides
Stream-only pages, process controls, AI/MCP/drafts and remote System Info in
legacy/unknown sessions. Direct controller entries and automatic companion/SSE
requests use the same guard. Legacy polling preserves a saved SSE preference.
Standard administration, DCC and legacy script-hook CRUD stay available. HTTP
error handling retains the original status when a response is empty or HTML.

This contract describes source ownership, behavior and verification scope.
TH and TS ship independently; native-only actions remain native capabilities.
Use [the shared contract](contract.md) and [the feature index](index.md).

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

## Verification

Run the focused drivers under `tools/frame_configuration/` from the Stream development
checkout, with the actual Handler checkout supplied using `--handler-root`
where supported. The complete shared gate is:

```powershell
python tools/frame_foundation/check_platform.py --handler-root "../../TH"
```

Adjust that path relative to the working directory; in the two-repository
workspace, Stream commands run from `TS/tactic_stream` and Handler is `../../TH`.
Use isolated data, actual input, fresh source fingerprints and independent-package
checks. Generated reports belong in the ignored tool `output/` directories.
Historical release counts and captures are local archive material, not current
acceptance. Offscreen checks do not establish physical touch/IME, compositor,
DCC or deployment readiness; exercise those when the feature requires them.


## Database resources

`features/configuration/database_resources.ui.mjs` owns the connection form,
responsive field grid, protected password field, bindings, operations and
confirmations. Browser DatabaseResources and native DatabaseResourcesEditor use
the same administrator-only `/admin/configuration/database-resources/{action}`
contract. Configuration includes its dirty/busy/unknown-write state and resumes
Save only after a confirmed remote commit. Cancellation clears pending Close.
Resource passwords are omitted from read documents and undo snapshots; revisions
include only their digest. Project routing resolves credentials internally while
client/expression reads retain their administrator guard. External project
configuration migrations use the existing upgrade path, serialize per PostgreSQL
database and roll back failures. Database creation, data movement and distributed
transactions are outside this page.

Focused checks: `tests/test_database_resources.py`, browser
`frontend/tests/database_resources.mjs`, native
`tests/test_configuration_database_resources.py`. The PostgreSQL opt-in uses a
unique test database and deletes only that database without FORCE.
