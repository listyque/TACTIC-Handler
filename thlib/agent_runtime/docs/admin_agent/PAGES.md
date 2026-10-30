# Create a filtered native page

Owner: TS server, `tactic.ui.panel.page_cmd.PageCmd`, baseline 0.112.205.
MCP calls this fixed Command. The result is ordinary TACTIC configuration consumed
by TS and TH, not a generated web application. Read [MODEL](MODEL.md) first;
[connection setup](CONNECTION.md) supplies the host-bound project and ticket.

## Translate the request

For “a shot review page, showing my lighting tasks in progress, with code and
description in a table and the inspector on the right”:

1. Discover the actual SearchType with `ts_types` / `ts_type_read`. Never assume
   a production schema or invent process/status values. Read `ts_page_read` for
   that base type. Keep its dependency `revision` and inspect existing navigation.
2. Choose a new stable lowercase `name`, a human `title`, ordered `columns`,
   native `records` and optional `task_filters`. Column records accept `name`,
   optional `title` and pixel `width` (40–1200). `widget` defaults to `field`;
   discovered alternatives are native `preview`, `tasks`, `notes` widgets.
3. Use `task_filters` for related tasks: `assigned`, `process`, `status` contain
   lists of values. `assigned:["__current_login__"]` stays dynamic for the person
   opening the page. All selected task facets must match the **same task**.
   Keep the current-login token alone; mixing it with literal logins is rejected.
   These are compiled by the existing quick-filter implementation to native
   search expressions. They are not independent EXISTS tests.
4. Ordinary conditions use `column`, `relation`, `value`, `rowEnabled:true` and
   `operator` (`begin`, `and`, `or`). Relations and columns come from
   `state.search`. Existing flat-filter semantics apply; this creation tool does
   not flatten or modify nested legacy searches. Arbitrary `_expression` input
   is rejected; use the native editor for custom expressions.
5. `order_bys` contains native sort clauses. For an explicit workspace layout,
   provide the existing `{panels, layout}` dock configuration. Panel IDs come
   from `workspace_panels`; geometry is normalized, not pixels. A tree node is
   a stack (`panels`, `active`) or split (`orientation`, `ratio`, `first`, `second`).
   Each panel is an object with `panel_id`, `x`, `y`, `width`, `height`, `z`,
   `visible`, and `dock_area`; panel ID strings alone are invalid. Tree nodes
   require explicit `type:"stack"` or `type:"split"`. Keep `results` present.
   Use `workspace.presets[].configuration` as examples when any exist; otherwise
   use the complete example below. Do not guess shapes after a rejected preview.
   Omitting `workspace_layout` leaves the normal workspace arrangement in use.
6. Call `ts_page_preview(search_type, document, expected_revision)`. Inspect the
   native table descriptor, generated search records, sample rows/count and
   sidebar draft. A valid page may have zero matching rows. Explain that honestly.
   This is a renderer description and data preview; it is not a screenshot.
7. Show the concrete proposal. If the host exposes `ts_page_save`, submit the
   same document/revision and one canonical UUID `operation_id`. Retain exact
   inputs across retries. Then read page state again and inspect the new native
   sources, search preset, navigation entry and dock assignment.

Example document after discovering the corresponding fields and process values:

```json
{
  "name": "lighting_review",
  "title": "Lighting review",
  "columns": [
    {"name": "code", "title": "Shot", "width": 180},
    {"name": "description", "width": 360}
  ],
  "records": [],
  "task_filters": {"assigned": ["__current_login__"], "process": ["lighting"], "status": ["In Progress"]},
  "order_bys": ["code"],
  "workspace_layout": {
    "panels": [
      {"panel_id": "results", "title": "Results", "kind": "results", "x": 0, "y": 0, "width": 0.7, "height": 1, "visible": true, "z": 1, "dock_area": "center"},
      {"panel_id": "description", "title": "Object inspector", "kind": "description", "x": 0.7, "y": 0, "width": 0.3, "height": 1, "visible": true, "z": 2, "dock_area": "right"}
    ],
    "layout": {
      "type": "split", "orientation": "horizontal", "ratio": 0.7,
      "first": {"type": "stack", "panels": ["results"], "active": "results"},
      "second": {"type": "stack", "panels": ["description"], "active": "description"}
    }
  }
}
```

## Persistence and recovery

The host enables writes with `--allow-page-save`; the model cannot enable the
flag. Server administrator authorization still applies. Tools are `ts_page_read`,
`ts_page_preview`, `ts_page_save`, `ts_page_operation`. Save calls the existing
widget configuration, saved search, workspace layout and sidebar editors inside
one outer native Command. It creates `page_<name>`, a `link_search` preset scoped
to `<search_type>@<name>`, an optional workspace preset, and a sidebar reference.
The active `tactic_handler` / `project_view` source is retained. Unrelated
definitions and default table configuration are preserved. Group grants are not
changed; visibility remains governed by existing project/link permissions.
The normal unfiltered tab remains available alongside the selected saved-search
tab. A search filter selects data for presentation; it does not change access rules.

Revision checks include current configuration rows, table resolution, column
metadata, sidebar dependencies and a database generation. SQLite/PostgreSQL
triggers increment `spt_widget_config_revision` on native config writes, including
API/import edits and A -> B -> A. Save checks under the native collection lock.
It does not freeze project data or installed extension code: preview re-evaluates
on save and opening the page queries current data.

`spt_page_operation` stores an actor/project-scoped UUID receipt and fingerprint
in the same project transaction as the configuration. Same ID/content returns
historical success; different content fails. A failed pre-commit operation rolls
back its configurations and receipt. System history may use a separate database;
this does not provide a distributed transaction for history or external triggers.
After an uncertain reply, inspect `ts_page_operation` and current page state,
then retry only the original ID/payload. Receipts persist without expiration;
back them up with project configuration. Template export excludes them.

This tool creates new pages. It refuses an occupied view/name/search namespace;
subsequent editing uses ordinary editors. Inherited navigation without a local
editable root must first be materialized in the sidebar editor. “Workspace
layout” means dock panels; SObject card layouts, arbitrary widget classes,
executable scripts and custom QML are separate native mechanisms, not arguments
to this tool. Trusted installed definitions/extensions remain trusted runtime.

## Source contracts and checks

- [Page composition](../../src/tactic/ui/panel/page_cmd.py)
- [Search/filter owner](../../src/tactic_stream/server/search_configuration.py)
- [Table XML editor](../../src/tactic_stream/server/widget_configuration.py)
- [Navigation editor](../../src/tactic_stream/server/sidebar_editor.py)
- [Dock presets](../../src/tactic_stream/server/workspace_layout.py)
- TH client [navigation model](../../../../TH/thlib/ui/models.py) and
  [controller](../../../../TH/thlib/ui/controllers/navigation.py),
  [search presets](../../../../TH/thlib/ui/search_presets.py),
  [dock owner](../../../../TH/thlib/ui/workspace_layout_presets.py).
  These are client consumers, not TS APIs.

Run `python -B -X utf8 -m unittest discover -s tests -p test_agent_pages.py -v`.
Run `python -B -X utf8 tests/test_agent_pages.py --postgres` for native persistence
on a disposable PostgreSQL instance. These tests never modify the installed project.
Set `TACTIC_PAGE_UI_CHECK=1` when running `test_agent_pages.py` to additionally open
the saved page through real browser navigation, check filtered rows and right-hand
inspector geometry, reload it, and decode the same records through TH's actual
navigation/filter/dock classes. This requires the browser test dependencies/cache
and the adjacent TH checkout. It checks TH consumers, not a full TH GUI session.
