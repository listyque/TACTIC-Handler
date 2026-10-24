# Work Hours, Costs and Reports

## Purpose

This subsystem extends task management with time entry, approval, capacity and
cost reporting without creating a second task or accounting model. Task effort
continues to use `sthpw/task.bid_duration`; actual time uses
`sthpw/work_hour`; user labor rates use `sthpw/login.hourly_wage` when the
current user has permission to see financial data.

## Source contract

TACTIC 5.0 registers `sthpw/work_hour` as `pyasm.biz.WorkHour`, a subclass of
`SObject`. Its defaults are the current project and current login. The original
work-hours element creates records with `SearchType.create`, connects each
record to the task parent, and writes `task_code`, `process`, `day`, `login`,
`category`, and either straight time or start/end time.

The original reports catalog defines:

- My Work Hours, grouped by day for the current login and project;
- Bid vs Actual Hours, comparing task `bid_duration` with work-hour
  `straight_time`;
- Approved vs Unapproved Hours;
- Approved and Unapproved Work Hour lists;
- Labor Cost reports attached to project search types;
- task schedule, due-date, completion and burndown reports.

The QML implementation keeps these meanings. It does not copy the original
widget limitation that assumed one time entry per task and day: multiple real
entries are preserved and aggregated.

## Data contract

### Task plan

- Planned effort: `sthpw/task.bid_duration`.
- Unit: `ProdSetting("bid_duration_unit")`; the normalized UI unit is hours.
- Schedule: `bid_start_date` and `bid_end_date`.
- Schedule delay and effort overrun are separate states.

### Work entry

- Identity: `code` and a code-based search key.
- Project: `project_code`.
- Target task: `task_code`.
- Target object: the native parent relationship (`search_type`, `search_id`).
- Process: copied from the task when created.
- User: `login`.
- Date: `day`.
- Duration: `straight_time` for regular entries and `over_time` when available;
  category remains `regular` or `overtime` for compatibility with the original
  UI.
- Optional interval: `start_time`, `end_time`.
- Description: `description`.
- Workflow state: `status`; `approved` is the financial approval state.

The simple editor accepts a date and duration. Start/end fields are an advanced
alternative and must never contradict duration. All calculations use decimal
hours; presentation rounds only at the UI boundary.

### Aggregates

- Logged = regular + overtime for every matching entry.
- Approved = logged hours whose status is `approved`.
- Pending = logged - approved.
- Remaining = max(planned - approved, 0).
- Over plan = max(approved - planned, 0).
- Overtime remains separately visible even when included in totals.

## Object API

`thlib.tactic_classes.WorkHour` is the client object. It inherits `SObject`,
owns category/status semantics, exposes decimal hour accessors and commits
through the existing object update path. Creation and permission-sensitive
state changes execute the corresponding TACTIC class workflow on the server.

Tasks and parent sObjects expose native work-hour queries. Multi-task screens
use one batch query by `task_code`; delegates never issue their own requests.
The server always generates code-based search keys.

## Permissions

- A user can create entries for themself.
- A user can edit or delete their own unapproved entries.
- Administrators and supervisor groups can enter time for another user,
  approve/reject entries and inspect team totals.
- Approved entries are immutable for ordinary users.
- Wage, rate and cost data are never sent to an unauthorized UI.
- Permission checks are enforced server-side; disabled controls are only a UX
  aid.

## User experience

### Task Inspector

The expanded inspector contains a compact Work section:

- planned, approved, pending, remaining and over-plan values;
- a proportional progress bar that does not confuse schedule status with labor;
- Log time and Open timesheet actions;
- direct access to the Timesheet, where entries and approval state are shown.

The collapsed inspector keeps only the useful `approved / planned h` summary.
No work controls are enabled without a real selected task.

### Task Browser

Task cards and table rows show a compact hours summary. The table can sort and
group by hours state without changing the task query. Visible task codes are
resolved in one asynchronous batch and cached only for the lifetime of the
current records; mutations invalidate affected codes.

### My Timesheet

The Timesheet dock provides week navigation, daily groups, totals, entry
creation/editing, regular/overtime distinction and approval state. It defaults
to the current login and current project. Network operations run in the server
pool.

### Supervisor Timesheet

Authorized users can switch login/team, see missing/pending/approved totals,
select multiple entries and approve or reject them. The same dock and model are
used; there is no parallel supervisor data store.

## Costs and pricing

Cost calculation is intentionally layered:

1. user labor = regular hours * effective user rate;
2. overtime labor = overtime hours * effective user rate * overtime factor;
3. optional process overhead = total hours * effective process rate;
4. actual internal cost = user labor + overtime premium + process overhead;
5. commercial unit price is independent from internal cost;
6. margin = unit price - actual internal cost.

`sthpw/login.hourly_wage` is the supported first source for a user rate. Future
effective-dated rate cards and unit prices must be registered TACTIC search
types, not local QSettings or hidden QML state. Historical reports must use the
rate effective on the work-entry day and never rewrite old entries. Currency
and overtime factor belong to project accounting configuration.

Until rate-card search types are configured, hours reports remain fully
functional and cost fields explicitly report that rates are not configured.

## Report docks

Two reusable dock surfaces are registered:

- Work Reports: hours, approval and capacity views available to users;
- Cost Reports: permission-gated labor cost and margin views.

They are driven by report descriptors rather than one QML file per report. The
initial descriptors reproduce the original report catalog. Each report declares
its source, date column, measures, grouping, required permission and supported
filters. This is the QML equivalent of TACTIC report/widget configuration,
while calculations remain in Python/server APIs rather than QML.

Initial report set:

- My Work Hours;
- Bid vs Actual Hours;
- Approved vs Pending Hours;
- Pending Approval;
- Team Hours by User and Process;
- Capacity and Over-plan Tasks;
- Labor Cost by Object/Process/User (only when rates are configured);
- Unit Economics and Margin (reserved until unit-price search types exist).

## Delivered capabilities

- `WorkHour` object API, server validation and batch query.
- Work-hours controller, entry/summary models and invalidation rules.
- Task Inspector, quick cards and Task Browser hours integration.
- My/Supervisor Timesheet dock and approval workflow.
- Rate resolver using authorized TACTIC data and an effective-rate extension point.
- Work and Cost report docks with descriptor-driven filters and summaries.
- Configuration coverage for accounting defaults, permission audit, automated
  tests, QML smoke loading and manual server checks.

## Implementation status

- Complete: native `Task` and `WorkHour` client objects, code-based identity,
  object creation/update/delete/approval methods and parent work-hour queries.
- Complete: server-side validation, ownership checks, supervisor checks,
  financial-report permission checks, one batch query for task collections and
  one batch mutation for multi-row approval.
- Complete: task summaries in Task Inspector and Task Browser, reusable time
  editor, user/supervisor Timesheet, overtime, edit/delete, approval and bulk
  approval.
- Complete: descriptor-driven Work Reports and a separately permission-gated
  Cost Reports dock. Both use server-side aggregation and the shared dock
  infrastructure.
- Complete: planned duration normalization from the project setting and labor
  cost based on the authorized `sthpw/login.hourly_wage` field.
- Reserved by schema, not faked in UI: effective-dated user/process rate cards,
  overtime multipliers, currencies, object unit prices, commercial price,
  margin and historical rate snapshots. These require registered project
  search types before implementation.
- Manual server verification required: actual group naming for financial
  access, custom status pipelines, installations without `hourly_wage`, and
  production reporting volumes.

Dock placement is stored in the shared dock layout.

## Verification matrix

- no task, no controls;
- task without a plan or entries;
- regular and overtime entries on the same day;
- several entries for one task/day;
- own pending entry edit/delete;
- approved entry protection;
- supervisor entry/approval/rejection;
- project/login/date filters;
- bid-duration minute and hour normalization;
- batch loading for many visible task rows;
- rate hidden from ordinary users;
- unavailable rate-card schema;
- repeated dock opening, background operation and application shutdown.
