---
group: Configuration
icon: cached
order: 36
---
# Cache configuration

> Cache configuration separates saved Search Tab structure from cached server records. Refresh
> actions still request current data from TACTIC, regardless of these switches.

## Workspace cache

| Setting or action | What it controls |
| --- | --- |
| **Cache process tabs** | Restores persistent process-tab structure instead of rebuilding every tab from project data during startup. |
| **Clear tabs cache** | Deletes only cached Search Tab structure. Tabs are rebuilt from current project data on their next load. |

## Cached server data

An enabled switch allows unchanged records in that category to be restored locally. Disabling a
switch makes later loads request the data again; it does not disable the feature.

| Category | Cached data |
| --- | --- |
| **Projects and reference data** | Projects, Search Types, pipelines, processes, statuses, users, groups, and tags. |
| **Search results and sObjects** | Ordered search pages and unchanged object fields used by Search Tabs. |
| **Snapshots and files** | Snapshot and file metadata. Actual repository files remain owned by Repository Sync. |
| **Children and relations** | Expanded child branches and linked-object membership. |
| **Tasks** | Task Manager scopes, pages, and task metadata. |
| **Notes** | Object and process note histories plus attachment metadata. |
| **Messages** | A bounded recent set of conversations and attachment metadata. |
| **Activity Feed** | Recent activity pages and complete calendar day counts. |
| **Work hours** | Timesheet and report query results for ranges opened before. |

## Cache maintenance

**Clear all cached server data** removes all categories above but keeps Search Tab layout, drafts,
and window layout. Data downloads again on demand. Before clearing, the cache generation advances,
so an older background request cannot put stale records back after the operation. The confirmation
dialog lists the affected data; **Cancel** leaves the cache unchanged and **Clear cache** proceeds.
