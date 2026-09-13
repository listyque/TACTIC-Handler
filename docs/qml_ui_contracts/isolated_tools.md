# Isolated tool contracts

These tools are separate functional windows or process modes. They do not create
parallel application state or import unavailable DCC runtimes into shared UI.

## Update and Create Update

Update is a standalone user workflow. Create Update is an administrative/release
workflow whose distribution availability is a product decision.

Both use the existing update API for current version, local history, remote
archive discovery, archive validation, applying an update, saving current
version, generating metadata, versions list, and creating an archive.

- Remote work and archive creation are asynchronous.
- Applying an update requires explicit confirmation and reports progress/error.
- Restart uses the existing application restart path.
- Failure must not leave a falsely completed version state.
- Create Update validates version/date/changes metadata and prevents accidental
  duplicate creation.
- Rollback and overwrite behavior require release-environment acceptance tests.

## DCC Open, Save, Import, and Reference options

`DccOptionsView` renders only the option fields declared by the selected
connector action. `DccOptionsController` validates and persists those values
under the application/action identity before calling the common item action.

- Standalone Open may use the associated application through the common
  download/open workflow.
- Maya Open routes `MayaConnector.open_scene` to the selected client id.
- Import routes `MayaConnector.import_file`.
- Reference routes `MayaConnector.reference_file`.
- DCC item menus expose the right-side options button when their manifest
  action declares fields.
- Save options select Maya ASCII or Maya Binary before the ordinary Commit
  Queue naming and standalone check-in workflow; Maya still performs only the
  final native scene save.
- Maya captures a temporary playblast for the Commit Queue preview, then
  creates the final playblast again at the resolved snapshot destination.
- Import/Reference are absent outside a compatible connected client.
- Standalone prepares/downloads the local file before sending the DCC command.
- Count, working-directory setup, format and other fields are exposed only when
  the connector manifest declares them.
- Shared presentation never imports Maya modules or changes process-wide
  environment mode.

## TACTIC API service

The external API is a separate service mode, not an always-on UI dock. It
preserves the existing endpoint and protocol contract and gives clients access
to the intended TACTIC Handler API.

The service owner handles single-instance lifecycle, client registration,
requests/results, errors, timeout, and shutdown. Debug Log records request ids
and redacts credentials. The service does not broaden allowed methods through
generated `eval` or `exec` payloads.

## Handler Server

Handler Server is the current process that coordinates thin DCC connectors. It
is not the old in-process QWidget application API.

- Standalone owns TACTIC, repository, and check-in.
- DCC clients expose fixed native capabilities only.
- Multiple clients are routed by explicit client id.
- Client errors owned by Maya remain in Maya unless they are failures of the
  routed Handler command itself.
- Server startup does not require opening a demo client or UI first.
- A DCC bootstrap detects an existing Handler, reports startup progress, and
  launches standalone as a separate process when needed.
- Repeated client start stops/replaces the old client cleanly.
- Closing the DCC unregisters and stops its client.
- Lifecycle, commands, results, timeout, disconnect, and tracebacks use the
  shared Debug Log.

## Maya connector package

`tactic_handler_dcc` is a working connector package, not an examples directory.
Its README documents bootstrap, connection, API access, UI actions, shutdown,
and custom script execution. The connector remains thin and does not upload to
TACTIC.

## Window and process requirements

- Functional tools use native top-level windows with shared minimum sizing,
  geometry clamping, theme/title-bar appearance, scrolling, and close guards.
- Long-lived processes expose state, PID/client id, output, structured error,
  and an explicit stop action.
- Stdout/stderr are consumed without blocking.
- Closing the UI cannot orphan an owned process or worker.
- Unsupported runtime state is visible and disabled, not simulated.

## Verification order

1. Standalone Open and Maya Open with one and multiple clients.
2. Maya Import and Reference capability routing.
3. Read-only update/history, then confirmed update application.
4. Create Update in a controlled release directory.
5. External API service protocol and shutdown.
6. Handler Server and DCC lifecycle under disconnect/reconnect and application
   shutdown.
