---
group: Docks
icon: table-view
order: 40
---
# Database Editor dock

> Database Editor applies controlled field changes to the exact selected sObjects of one Search
> Type. It is a batch editor, not a raw database console.

## Selection and scope

The dock follows the current Search selection and records a selection fingerprint. Only compatible
objects from the active Search Type can share one edit operation. The header shows selected-object
and dirty-field counts so a changed selection is visible before Apply.

## Edit fields

Choose a server-provided field, inspect its current value and enter a replacement accepted by that
field's editor. **Apply to all selected** stages the value for every selected object; otherwise edit
the intended rows individually.

Available columns, data types, required values and catalogs come from TACTIC. Search Type names,
statuses and other project labels are never inferred or translated by the editor.

## Save and discard

- Changed cells remain staged and visibly marked until **Save changes** succeeds.
- Review the dirty count and selected identities before a batch save.
- Discard restores loaded server values without issuing a write.
- A partial or failed server operation reports the affected object and keeps unresolved edits visible.

## Safe workflow

1. Build and verify the Search result first.
2. Select only the objects that should change.
3. Confirm the Search Type and selection count in Database Editor.
4. Stage one field at a time and review changed cells.
5. Save, then Refresh Search to verify the server result.

## Limits and permissions

- Read-only, identity and unsupported fields cannot be edited.
- Server validation and access rules remain authoritative.
- Database Editor does not create missing workflow records or linked objects as a side effect.
- Losing selection does not redirect a staged batch to a new object set.
