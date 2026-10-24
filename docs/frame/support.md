# Tactic Frame: Identity, connections and support

This contract describes source ownership, behavior and verification scope.
TH and TS ship independently; native-only actions remain native capabilities.
Use [the shared contract](contract.md) and [the feature index](index.md).

## Composition and command owners

| Portable description | Native adapter | Browser adapter | Existing side-effect owner |
| --- | --- | --- | --- |
| `help/help.ui.mjs`, `help.state.mjs` | `features/support/help/HelpView.qml` | `features/help/HelpView.vue` | Existing article controllers, document readers and shell ownership |
| `diagnostics/debug.ui.mjs` | `DebugLogView.qml` | `features/debug/DebugLog.vue` | Native `DebugLogController`; browser `debugLog.js` and IndexedDB |
| `diagnostics/performance.ui.mjs` | `UiPerformanceView.qml` | `features/debug/UiPerformance.vue` | Existing `UiPerformanceMonitor` / `uiPerformance.js` |
| `identity/profile.ui.mjs` | `UserProfileView.qml`, public `UserWorkSummary.qml` | `features/users/UserProfile.vue` | Native `UserController`; existing profile/summary/activity HTTP APIs |
| `identity/profile.editor.ui.mjs`, `profile.editor.state.mjs` | `UserProfileEditorDialog.qml` | Owned editor in `UserProfile.vue` | Existing account ACL, revision checks, group/access commands and avatar queue/API |
| `connection/sign_in.ui.mjs` | `LoginDialog.qml` | `features/connection/SignIn.vue` | Existing native authentication and browser `App.vue` session owner |
| `connection/presets.ui.mjs` | `ServerPresetsView.qml` | Comparison fixture only | Existing native presets and Configuration persistence |
| `connection/updates.ui.mjs` | `UpdateView.qml` | Comparison fixture only | Existing native release polling, ZIP creation/install/cancellation owner |
| `feedback/error.ui.mjs` | `ErrorDialog.qml` | `features/debug/ErrorDetails.vue` | Existing error classification/retry owner; browser HTTP notifications remain intact |
| `controls/feedback/confirmation.ui.mjs` | `UpdatePrompt.qml`, install confirmation, profile discard | Profile discard | Calling window owns modality and the command |

Descriptions own bounds, labels, enabled/selected states, responsive layout and
action records. Adapters dispatch those actions to the existing owners. The
profile draft module owns only immutable edits, close decisions and password
clearing; it cannot authorize a field or commit an account. Vue unwraps its draft
at this boundary so a saved immutable copy contains no nested reactive proxies.
Native Save submits profile fields, password and group/access edits through one
existing `mutate_user_profile` operation; changing tabs cannot skip the other
page. The one-argument `UserController.save_profile` entry remains supported.

`SummaryChip` is an explicit Frame kind backed by the existing house control in
each renderer. Lists use the common `revealListOffset` when keyboard selection
crosses their viewport. Native branches forward focus through the recursive URL
loader; Vue waits for the virtualized row before focusing it. Read-only diagnostic
areas can disable wrapping, preserving complete commands without laying out a
huge single line as thousands of wrapped paragraphs.

## Capabilities and lifecycle

- Handler retains local JSONL files and copies their path; Stream imports and
  downloads JSONL using browser-owned history. Leaving history does not overwrite
  its file. Stream invalidates late imports/history reads on session changes and
  closes owned event details on logout.
- Help and Debug Log are available on sign-in. Other account-owned tools keep
  their existing authentication gates. Connection menu/status composition was
  already shared in the shell and retains the same reconnect/session owners.
- Handler retains ticket generation, preset address/proxy/site routing and native
  file pickers. Stream authenticates against its current origin. A Vue fixture
  for presets or ZIP generation proves composition, not an available browser
  operation. No native installer was added to the web client.
- Profile editing is an owned dialog. Changed drafts require an explicit discard;
  busy writes cannot be closed. Unknown write results require reload before
  another Save. Submission and close clear entered passwords. Handler's existing
  avatar queue starts immediately for an existing user; discarding text does not
  undo a completed avatar upload. Stream uploads its selected avatar on Save.
- Inspecting a historical event cannot acquire Retry from an earlier live error.
  Native Retry exists only when the existing owner supplies a retryable worker.
- Existing update selection, portable eligibility, polling, cancellation, install
  confirmation, changelog and maintainer Ctrl-double-click generator remain in
  the native release owner. Frame modules use `connection/updates.ui.mjs` because
  the release packager intentionally excludes runtime directories named `updates`.

## Explicit limits

Activity cards remain narrow existing domain components placed by the profile
skeleton; their full migration belongs to B11. Request highlighting and changelog
documents remain the existing native/browser readers. Qt/Chromium glyph rendering,
document wrapping, system title bars and local file dialogs are platform output;
this batch does not claim identical rasterized text. Browser animation callbacks
bound a paint opportunity rather than prove GPU presentation. Automated Qt and
browser input does not replace physical touch/IME/compositor checks or a production
PostgreSQL deployment check.

## Lazy activity cards

Collapsed profiles instantiate only the preview cards through their row Loaders.
Expanding creates the remaining cards at the assigned width; collapsing releases
them while retaining records and preview-card identities. Do not instantiate
hidden rich-text documents at zero width. Check actual Show more/less input
and retained identities in both native and browser fixtures.

## Verification

Run the focused drivers under `tools/frame_support/` from the Stream development
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
