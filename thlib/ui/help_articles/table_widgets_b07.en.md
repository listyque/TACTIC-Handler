---
group: Workflows
icon: table
order: 36
---

# Table View: B07 typed cells

B07 is still in progress. The catalogue contains 41 server classes and 98 named aliases. This article documents the added value adapters; it does not certify every historical option. Unsupported options remain explicit errors. Keep existing view definitions and replace only the intended element.

## L02: legacy cells using existing panels

The catalogue now includes 41 classes / 98 named aliases. These four adapters
reuse the existing notes/Task Inspector, task drafts and table controls; they do
not create another Messages or Task Manager window.

```xml
<element name="notes">
  <display class="pyasm.widget.DiscussionWdg">
    <include_submission>false</include_submission>
  </display>
</element>
<element name="tasks">
  <display class="pyasm.widget.SObjectTaskTableElement">
    <width>280</width><supe>true</supe><bid_edit>true</bid_edit>
    <simple_date>true</simple_date>
  </display>
</element>
<!-- Use this column in sthpw/task. -->
<element name="context"><display class="pyasm.widget.TaskParentSpacingTableElement"/></element>
<!-- Use this column in sthpw/message or sthpw/message_log. -->
<element name="message"><display class="tactic.ui.app.MessageTableElementWdg"/></element>
```

Discussion reads existing notes and offers setting/append_setting process
choices, including empty branches. Clicking a branch opens the existing owner;
saving/editing/deleting a note uses its ordinary permission/revision checks.
Task cells show the existing compact cards; status, assignee and dates use the
existing editors and explicit Save/Discard. `supe` enables inline assignment,
`bid_edit` enables inline dates; these display options do not grant server rights.
`simple_date` uses short month-day dates instead of full ISO dates when the row
has room for dates. The old HTML CalendarBar is not embedded. Explicit column
width overrides the 250px default. TaskParentSpacing displays the context before
its first slash, retaining the complete context as a tooltip.

Formatted messages show plain/chat text and note/task/snapshot changes, the
author and progress. Message markup is displayed as text. The old HTML preview
is not recreated. Invalid JSON/non-finite progress is an explicit cell error.

`include_submission=true` remains unsupported: old Submission is part of the
agreed excluded pyasm.prod subsystem. Slash subcontexts in old setting choices
and CGI filter state are not implemented; modern Discussion supports an explicit
context option. `scroll=false` is an old HTML layout hint; the modern owner keeps
its shared scrollbar. Unknown options stay explicit rather than being ignored.
The current shipped/CG census has 38 adapted / 36 pending classes. B07 is open.

### L02: paired cell examples

Fresh production Qt/Vue captures use the same data, MD3 dark theme, language and 280px column width. These examples cover the four cell adapters, not every historical HTML option.

| Cell | Tactic Handler | TACTIC Stream |
| --- | --- | --- |
| `DiscussionWdg` | ![DiscussionWdg native](media/frame-table-l02-legacy_notes-native-en.png) | ![DiscussionWdg stream](media/frame-table-l02-legacy_notes-stream-en.png) |
| `SObjectTaskTableElement` | ![SObjectTaskTableElement native](media/frame-table-l02-legacy_tasks-native-en.png) | ![SObjectTaskTableElement stream](media/frame-table-l02-legacy_tasks-stream-en.png) |
| `TaskParentSpacingTableElement` | ![TaskParentSpacingTableElement native](media/frame-table-l02-legacy_context-native-en.png) | ![TaskParentSpacingTableElement stream](media/frame-table-l02-legacy_context-stream-en.png) |
| `MessageTableElementWdg` | ![MessageTableElementWdg native](media/frame-table-l02-message_progress-native-en.png) | ![MessageTableElementWdg stream](media/frame-table-l02-message_progress-stream-en.png) |

## Snapshot lock

Snapshot context lock; read only.

```xml
<element name="locked" width="180">
  <display class="tactic.ui.table.SnapshotLockedElementWdg"></display>
</element>
```

## Snapshot file

Original filename, sequence range and safe repository link.

```xml
<element name="file" width="180">
  <display class="tactic.ui.table.SnapshotFileElementWdg"></display>
</element>
```

## Milestone completion

Use on sthpw/milestone; task visibility still applies.

```xml
<element name="completion" width="180">
  <display class="tactic.ui.table.MilestoneCompletionWdg"></display>
</element>
```

## Grouped completion

Average of the tasks matching each context group.

```xml
<element name="completion" width="180">
  <display class="tactic.ui.table.TaskGroupCompletionWdg"><options>[{"label":"MODEL","context":["model"]}]</options></display>
</element>
```

## Due date

Use on tasks. Labels and urgency follow the original thresholds.

```xml
<element name="due" width="180">
  <display class="tactic.ui.table.TaskDaysDueElementWdg"><due_date_col>bid_end_date</due_date_col></display>
</element>
```

## Subcontext

Preserves all text after the first slash in context.

```xml
<element name="subcontext" width="180">
  <display class="tactic.ui.table.SubContextElementWdg"></display>
</element>
```

## Selection

A second view of the same row selection; not a database checkbox.

```xml
<element name="select" width="180">
  <display class="CheckboxColWdg"></display>
</element>
```

## Search Type title

Displays the native title for the row search_type value.

```xml
<element name="search_type" width="180">
  <display class="SearchTypeElementWdg"></display>
</element>
```

## Compact task summary

Click the process to inspect that exact task; default mode uses full task cards.

```xml
<element name="tasks" width="180">
  <display class="tactic.ui.table.TaskSummaryElementWdg"><mode>minimal</mode></display>
</element>
```

## Older completion

Integer result and obsolete-process filtering differ from the modern widget.

```xml
<element name="completion" width="180">
  <display class="pyasm.widget.TaskCompletionWdg"></display>
</element>
```

## Discussion

Uses the existing process note counts and inspector. This is not pyasm.widget.DiscussionWdg.

```xml
<element name="notes" width="180">
  <display class="tactic.ui.widget.DiscussionWdg"></display>
</element>
```

## Project database

Use on sthpw/project. Reads database existence and version without creating a database.

```xml
<element name="database" width="180">
  <display class="tactic.ui.table.ProjectWdg"></display>
</element>
```

## Table availability

Use on sthpw/search_object. Checks the physical table.

```xml
<element name="table" width="180">
  <display class="tactic.ui.app.SearchTypeHasTableElementWdg"></display>
</element>
```

## Preference description

Use on sthpw/pref_list; includes the original contextual hints.

```xml
<element name="description" width="180">
  <display class="tactic.ui.table.PreferenceDescriptionWdg"></display>
</element>
```

## Recipients

Use on sthpw/notification_log. Reads linked notification_login rows. Sending email and public recipient insertion remain unfinished.

```xml
<element name="recipients" width="180">
  <display class="tactic.ui.table.RecipientElementWdg"></display>
</element>
```

## Related value

Replace the relationship path/column with your schema. Native joins select the related record.

```xml
<element name="category" width="180">
  <display class="tactic.ui.table.RelatedElementWdg"><template>cg/assets.cg/assets_category</template><column>name</column></display>
</element>
```

## Editor and limits

The same Frame scene defines text, multiline, choice/user, switch, date/datetime, color and multi-value editor composition. Enter commits a single line; multiline Enter adds a newline and Save commits. Escape cancels. Existing revision/ACL/rollback and uncertain-write checks stay active. Native tags retain their specialized editor. Thirty-six referenced widget classes still require complete workflows: nested tables, schedules, work hours, loader/publish and configurable action forms.

## Current paired examples

![table](media/frame-table-table-en.png)

![fields](media/frame-table-fields-en.png)

![summary](media/frame-table-summary-en.png)

![groups](media/frame-table-groups-en.png)
