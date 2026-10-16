# Tactic Frame B04: support, identity and connection

The portable descriptions live in `src/tactic_stream/shared_ui/features/support`.
Handler ships physical copies in `thlib/ui/qml/tactic_frame/features/support`;
neither runtime imports the other checkout or an embedded browser.

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

## Evidence and reproduction

Run these commands from the Stream source directory, using its virtual
environment and a writable private TEMP/TMP directory.
Qt and browser drivers create only isolated data and stop their own servers.

```powershell
python -B -X utf8 tools/frame_support/capture.py
node frontend/tests/frame_support.mjs
python -B -X utf8 tools/frame_support/report.py
python -B -X utf8 tools/frame_foundation/check_platform.py --handler-root D:/code/th_codex
```

`tools/frame_support/output/index.html` compares eight support surfaces, 28 named
states, three styles, light/dark, EN/RU and desktop/narrow/phone widths. Original
captures cover 1100/800 px; current captures add 360 px. Sign-in uses its existing
bounded window size. Quick or single-screen captures are rejected by the final
report builder. The report verifies the exact complete matrix, source hashes in
both checkouts, browser source hashes, driver hashes and archive SHA-256.

The original is the pre-migration tracked Handler archive
`backups/2026-10-15_103116_before_shared_ui_foundation/TH_git_HEAD_reference.zip`,
commit `fa3f594c5cd09ce565ea14acb533302e79c9308a` and SHA-256
`910e61c6fa96b00bd7c48468fd9b315fe1f08eaeb09aba1a4e2108af90aab057`.
It is kept separately from the earlier dirty-working-tree backup. Original UI
diagnostics are recorded beside its captures; current QML must have no warnings.

Real behavior is checked independently of the comparison fixture:

- Handler `tests.test_frame_support`, `test_user_profile_qml`,
  `test_debug_logging`, `test_debug_request`, `test_user_profile_completion`,
  `test_login_configuration`, `test_update_controller`, `test_update_functions`,
  `test_window_content_qml`, localization, update prompt and Help suites.
- Stream `frontend/tests/frame_support_state.mjs`, `debug_log_data.mjs`, the real
  HTTP/browser support workflow in `tests/test_transport.py`, and the mobile
  profile/activity scenario. The support workflow covers recording settings,
  search/levels/sources, copy, full native JSONL import/export, read-only owned
  details, mobile lists, measurement phases, focus, logout/relogin, persisted
  profile fields, discard and a committed request whose response is lost.
- The existing platform gate checks independent packaging, shared copies,
  renderer registration, native/browser input, IME, scales, shell/session races
  and retained Help behavior. A screenshot fixture alone is never completion.

## Explicit limits

Activity cards remain narrow existing domain components placed by the profile
skeleton; their full migration belongs to B11. Request highlighting and changelog
documents remain the existing native/browser readers. Qt/Chromium glyph rendering,
document wrapping, system title bars and local file dialogs are platform output;
this batch does not claim identical rasterized text. Browser animation callbacks
bound a paint opportunity rather than prove GPU presentation. Automated Qt and
browser input does not replace physical touch/IME/compositor checks or a production
PostgreSQL deployment check.
