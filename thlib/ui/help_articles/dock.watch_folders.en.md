---
group: Docks
icon: folder-eye
order: 41
---
# Watch Folders dock

> Watch Folders monitors explicitly configured local directories and prepares matching new or changed
> files for the chosen Handler workflow.

## Folder definitions

A watch definition stores the local root, project scope, matching rules and enabled state. Use the
Watch Folder editor to create or change a definition; disabling it preserves the configuration
without monitoring the directory.

## Monitoring

The dock shows active folders, last activity, discovered files and errors. Monitoring discovers
candidates; it does not bypass normal validation, repository ownership or Commit Queue review.

Use refresh to reload definitions, enable or disable a folder, open its editor, reveal the local
directory, or delete the definition after confirmation.

## Typical workflow

1. Create a definition for one explicit local folder.
2. Choose its project and matching behavior.
3. Enable it and verify the displayed path.
4. Add or change a test file and inspect the discovered result.
5. Review any prepared operation in its normal queue before check-in.

## States and safety

- An unavailable directory is reported and retried only through the folder's normal lifecycle.
- Disabling monitoring does not delete local files or server records.
- Deleting a definition removes the watcher configuration, not the watched directory.
- Duplicate filesystem events are deduplicated by stable path identity.
- Large directory work runs outside the UI thread; the dock keeps a visible scrollbar for long lists.
