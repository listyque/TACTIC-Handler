---
group: Docks
icon: payments
order: 35
---
# Cost Reports dock

> Cost Reports is the permission-gated labor-cost view of Work Reports. It converts accessible work
> hours and configured wage data into project cost totals.

## Required data

A meaningful result needs all of the following:

- work-hour records in the selected date range;
- tasks, processes and users visible to the current account;
- configured wage or cost data for those users;
- permission to read labor-cost reporting data.

The UI never substitutes a guessed wage or currency.

## Controls and breakdowns

Choose date range, scope and grouping, then Refresh. Available views can break totals down by user,
task or process using the same underlying report owner as Work Reports.

## Interpreting results

An empty report can mean no hours, missing cost configuration, or insufficient access. Read the
permission or data message above the report before treating zero as a real financial total.

## Security and errors

- Cost values are shown only when the server authorizes the current account.
- Hiding this dock does not change permissions or source data.
- Project labels and currency come from server configuration.
- Refresh is read-only and preserves the selected range after a temporary failure.
