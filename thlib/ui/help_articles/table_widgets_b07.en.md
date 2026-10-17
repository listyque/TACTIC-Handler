---
group: Workflows
icon: table
order: 36
---

# Table View: B07 typed cells

B07 is still in progress. The catalogue contains 37 server classes and 87 named aliases. This article documents the added value adapters; it does not certify every historical option. Unsupported options remain explicit errors. Keep existing view definitions and replace only the intended element.

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

The same Frame scene defines text, multiline, choice/user, switch, date/datetime, color and multi-value editor composition. Enter commits a single line; multiline Enter adds a newline and Save commits. Escape cancels. Existing revision/ACL/rollback and uncertain-write checks stay active. Native tags retain their specialized editor. Forty referenced usable widget classes still require complete workflows: nested tables, schedules, work hours, loader/publish and configurable action forms.

## Current paired examples

![table](media/frame-table-table-en.png)

![fields](media/frame-table-fields-en.png)

![summary](media/frame-table-summary-en.png)

![groups](media/frame-table-groups-en.png)
