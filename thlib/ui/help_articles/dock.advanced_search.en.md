---
group: Docks
icon: advanced-search
order: 39
---
# Advanced Search dock

> Advanced Search builds explicit field, relation and expression rules for the active Search tab.
> It complements text, tags and Quick Filters rather than replacing them.

## Scope

When opened from a result tab, the dock edits that tab's Search Type and preset scope. When opened
from Sidebar Editor, it works with the complete saved-search library for the selected Search Type.
Always confirm the displayed Search Type before applying or saving rules.

## Filter structure

Each enabled row contains a field or expression, operator and value. Rows are joined with **AND** or
**OR** in the existing flat condition editor. Disable a row to test the query without deleting it.

| Element | Purpose |
| --- | --- |
| Field | Chooses a column defined by the active Search Type. |
| Operator | Equality, comparison, range, membership, text or empty-state test supported by the field. |
| Value | Literal value, catalog choice, date or expression input. |
| AND / OR | Requires both branches or accepts either branch. |
| Move up/down | Changes condition order and preserves values. |
| Apply | Sends the built filter to the active Search tab. |
| Reset | Returns the editor to its initial rules without changing server data. |

## Quick Filters and custom rules

A Quick Filter can contribute one or several rules. Detach it when you need to edit those rules as a
normal custom filter. After detaching, later changes to the source Quick Filter no longer rewrite the
custom copy.

Text, tags, Quick Filters and Advanced Search are combined. A surprising empty result usually means
that a valid rule in another layer is still active.

## Expressions and relations

Use expression rows for TEL or relation traversal that a direct field cannot express. Expression
suggestions come from the selected Search Type and project schema. Keep server-defined identifiers
exactly as returned; do not translate Search Type, process or field codes.

## Presets

Presets store the complete intended filter document for their scope. Use **Update selected preset**
to replace the selected preset and **Save as new preset** to preserve the old one. A generated saved-
search link reopens the stored custom search rather than a copy of the current result rows.

## Typical workflow

1. Verify the active Search Type and tab.
2. Add the narrowest direct field rules first.
3. Add relations or expressions only where direct fields cannot describe the condition.
4. Check AND/OR order and temporarily disable rows to verify them.
5. Apply and inspect the result count.
6. Save a preset only after the combined text, tag, Quick Filter and custom state is correct.

## Errors

- An invalid value or expression stays in the editor with its validation message.
- A field removed from server configuration must be replaced; the UI does not reinterpret its name.
- Applying an empty filter clears only the Advanced Search layer.
- A server error preserves the current draft so it can be corrected or retried.

## Advanced Search and Quick Filter ownership

Quick Filters appear as managed cards in Advanced Search. **Edit as custom filter** keeps the executable condition and detaches it from its Quick Filter chips. Process, assignee and status facets refer to the same related task. Removing a managed card removes that part of the quick selection when applied. Expressions entered in this search editor are read-only; the general Script Editor/API permission contract above is unchanged.

**Filter Processes** changes which process, built-in and child branches are visible. Cancel keeps the previous visibility. Save applies the draft, and Save and close also hides the editor. This changes presentation without re-running the object query. Repeated schema links share a logical setting; the togglers and Ctrl/Shift selection work across the tree. Tag search and its clear/reload actions retain the selected tags in the current search tab.

## Dock lifetime and legacy groups

Applying keeps this dock open. Closing it retains the current tab draft during the session. The first WHERE row has an Add action; value suggestions support arrows, Enter and Escape. Save replies with an unknown result must be reconciled through Refresh saved searches before another write.

The current editor represents flat condition cards. Legacy nested saved-search groups that it cannot represent are reported explicitly; they are not silently flattened.
