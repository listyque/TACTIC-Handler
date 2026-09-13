---
group: Docks
icon: bar-chart
order: 34
---
# Work Reports dock

> Work Reports aggregates task and work-hour data for a date range without changing the source
> records. Available detail follows server permissions.

## Report types

| Report | Question it answers |
| --- | --- |
| My hours | How much regular and overtime work did I record? |
| Bid versus actual | How do planned task hours compare with recorded work? |
| Approval | Which entries are approved or still pending? |
| Team | How are hours distributed among accessible users? |
| Process | How are hours distributed by project process? |
| Labor cost | What labor cost is visible to an authorized account? |

## Controls

Choose a report, date range and available grouping or user scope, then Refresh. Totals and breakdowns
are calculated from the currently loaded server response; changing presentation never edits tasks or
work-hour entries.

## Reading a report

Read the headline total first, then its user, task or process breakdown. A bid/actual difference is
meaningful only where tasks have configured bid values. Approval totals reflect work-hour record state,
not task status.

## Permissions and missing data

- User and team details are limited to records visible to the current account.
- Labor cost requires the corresponding wage and reporting permissions.
- Missing bids, wages or work-hour records are shown as unavailable rather than guessed.
- Project-configured names and currencies are not translated or hardcoded by the UI.
- Refresh errors preserve the chosen report and date range for retry.
