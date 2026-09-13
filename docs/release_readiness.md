# Application release readiness

The release gate is non-destructive. It does not infer
that a QML file is functional, does not run server mutations against an implicit
project while environment-dependent acceptance is still outstanding.

## Automated gate

Run the strict gate from the repository root:

```powershell
python -m pip install -r requirements-dev.txt
python tests/run_release_gate.py
```

The command requires a clean worktree, runs `git diff --check`, mandatory Ruff and
`qmllint` checks, compiles the application client, Handler Server, thin DCC SDK and
both launchers, executes every test module in an isolated process, and loads both
application entry points from another working directory. `qmllint` is excluded from
the later isolated suite because it already ran as its own gate step. The isolated suite includes the real
offscreen QML composition root, twice-reopened standalone windows, ordered shutdown,
architecture and cache boundaries, public core contracts, request budgets, and all
six stabilized workflow verticals.

During development, `--allow-dirty` keeps the same checks while allowing a dirty
worktree. It is not the release-candidate command.

The application runtime dependency is pinned in `requirements.txt`. Verify it in
a newly created Python environment rather than reusing the development interpreter:

```powershell
python tests/run_clean_environment_smoke.py
```

Use `--wheelhouse PATH` for a controlled offline installation source.

The machine-readable source of truth is
`tests/contracts/release_acceptance.json`. A failed automated check blocks merge.
The human-readable scenarios are in
[release_acceptance_checklist.md](release_acceptance_checklist.md).

## Manual acceptance gate

Automation cannot truthfully certify the following environments:

1. login/logout, presets, project navigation, search and skey routing on the target
   TACTIC server;
2. generated read-only procedures on the supported TACTIC server Python runtime;
3. server mutations with real permissions and triggers in an explicitly isolated
   test project;
4. repository mapping, transfer, Check-in/Out, Commit Queue, Drop Plate,
   attachments, previews, retry and cancellation against real storage;
5. Windows tray, multi-display geometry, restart and close during active work;
6. dependency installation and launcher smoke in a clean Windows Python environment;
7. Maya thin-client discovery, routing and native scene operations;
8. visual acceptance for both themes, English/Russian localization and supported
   responsive minimum sizes.

Each item is required before a release candidate is declared production-ready.
Read-only live vertical checks may support the first item, but they do not replace
mutation, repository, DCC or visual acceptance.

Run the guarded server-runtime compatibility check only with an isolated project:

```powershell
$env:TACTIC_RUN_LIVE_SERVER_SMOKE = "1"
$env:TACTIC_TEST_PROJECT_CODE = "th_test_handler"
python tests/run_live_server_procedure_smoke.py
```

Record every environment-dependent result with a tester and concrete evidence:

```powershell
python tests/record_release_acceptance.py --list
python tests/record_release_acceptance.py --pass windows-lifecycle
  --tester "Name" --evidence "Windows 11, two displays, close during repository sync"
```

The local evidence file is `.release/acceptance.json` and is intentionally ignored
by Git. A release candidate must pass the strict command:

```powershell
python tests/run_release_gate.py --require-manual
  --manual-results .release/acceptance.json
```

## Cutover policy

- `launch.py` and `launch.pyw` are the supported application entry points.
- `thlib/ui` is the only application UI package.
- `thlib` remains the native TACTIC domain/core layer; core modules outside `thlib.ui` do not depend on presentation modules.
- Removed QWidget UI packages, compatibility launchers, adapters, migrations, and fallback readers are not release paths.

## Release decision

There are three distinct states:

- **automated gate failed** — not mergeable;
- **automated gate passed, manual gate pending** — mergeable as continued application
  development, not a production release candidate;
- **automated and manual gates passed** — eligible for the explicit cutover/release
  decision.
