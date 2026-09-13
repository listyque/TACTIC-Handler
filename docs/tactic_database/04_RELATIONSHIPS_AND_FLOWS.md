# Relationships and Correct Write Flows

## Search type creation

```text
Search Type Manager
  → physical project table/migration
  → sthpw/search_object registry
  → sthpw/schema relationships
  → config/widget_config default views
  → optional config/pipeline + config/process
  → optional config/naming
  → security rules
```

Do not stop after inserting into `sthpw/search_object`.

## Workflow and tasks

```text
sthpw/pipeline or config/pipeline (graph XML)
  └─ config/process (node/check-in configuration)
       └─ sthpw/task (task instance for SObject+process)
            └─ sthpw/status_log (generated status history)

config/process_state = workflow runtime state, not task
```

## Check-in / DAM

```text
config/naming + config/process + repository config
  → FileCheckin/FileAppendCheckin
  → sthpw/snapshot
  → sthpw/file[]
  → versionless/current/latest files
  → triggers, logs, change timestamp
```

Never create `snapshot` or `file` rows independently.

## Object comments

```text
any SObject
  └─ sthpw/note (search_type/search_id, process/context)
       └─ child notes through parent_id
       └─ attachments through normal snapshot/file + relation
```

## Chat / message center

```text
sthpw/message          = channel/container/current message state
sthpw/message_log      = message entries/history
sthpw/subscription     = participant/subscriber + last_cleared watermark
sthpw/connection       = optional generic links, e.g. attachment to log entry
sthpw/snapshot/file    = attachment storage
```

Use `log_message`/chat commands and Subscription APIs, not direct message_log inserts.

## Notification subsystem

```text
sthpw/notification       = rule/template/configuration
sthpw/group_notification = groups receiving rule
sthpw/notification_log   = generated delivery log
sthpw/notification_login = per-login delivery association
```

Do not use `notification` as a user inbox row.

## Security

```text
sthpw/login
  ↔ sthpw/login_in_group ↔ sthpw/login_group(access_rules XML)
  → AccessManager effective access / search filters
  → sthpw/ticket authenticated session
```

Never authorize by group-name substring in new server code.

## Audit

```text
transaction manager
  → sthpw/transaction_log (full transaction)
  → sthpw/sobject_log (per-object index)
  → sthpw/change_timestamp (change detection)
  → sthpw/status_log / retire_log where applicable
```

These are generated tables. Read them for history/diagnostics, do not hand-write them.

## Generic relationships

Use `sthpw/connection` only through `connect_sobjects`/SObjectConnection. `sthpw/schema` describes model relationships; `connection` represents runtime links between concrete records.
