# Modern client release readiness

Block F is the final non-destructive release and cutover gate. It does not infer
that a QML file is functional, does not run server mutations against an implicit
project, and does not remove the legacy/core source while environment-dependent
acceptance is still outstanding.

## Automated gate

Run the strict gate from the repository root:

```powershell
python tests/run_release_gate.py
```

The command requires a clean worktree, runs `git diff --check`, compiles the modern
client, Handler Server, thin DCC SDK and both launchers, executes every test module
in an isolated process, runs the legacy compatibility smoke, and loads both modern
entry points from another working directory. The isolated suite includes the real
offscreen QML composition root, twice-reopened standalone windows, ordered shutdown,
architecture and cache boundaries, public core contracts, request budgets, and all
six stabilized workflow verticals.

During development only, `--allow-dirty` keeps the same checks while allowing a
dirty worktree. It is not the merge command.

The machine-readable source of truth is
`tests/contracts/release_acceptance.json`. A failed automated check blocks merge.

## Manual acceptance gate

Automation cannot truthfully certify the following environments:

1. login/logout, presets, project navigation, search and skey routing on the target
   TACTIC server;
2. server mutations with real permissions and triggers in an explicitly isolated
   test project;
3. repository mapping, transfer, Check-in/Out, Commit Queue, Drop Plate,
   attachments, previews, retry and cancellation against real storage;
4. Windows tray, multi-display geometry, restart and close during active work;
5. Maya thin-client discovery, routing and native scene operations;
6. visual acceptance for both themes, English/Russian localization and supported
   responsive minimum sizes.

Each item is required before a release candidate is declared production-ready.
Read-only live vertical checks may support the first item, but they do not replace
mutation, repository, DCC or visual acceptance.

## Cutover policy

- The modern QML launcher is the primary development line.
- `launch.py` selects QML by default; legacy remains available explicitly through
  `--ui legacy` or `TACTIC_HANDLER_UI=legacy`.
- `thlib` remains the native TACTIC domain/core layer; it must not depend on
  `modern_ui`.
- The legacy launcher remains a comparison and compatibility oracle until manual
  acceptance is signed off and a dedicated removal change inventories its remaining
  consumers.
- No compatibility façade or QWidget UI is removed as an incidental release-gate
  cleanup.
- Remaining manual-only or intentionally legacy-only interfaces retain their
  parity-report status; Block F does not promote them based on automated loading.

## Release decision

There are three distinct states:

- **automated gate failed** — not mergeable;
- **automated gate passed, manual gate pending** — mergeable as continued modern
  development, not a production release candidate;
- **automated and manual gates passed** — eligible for the explicit cutover/release
  decision.
