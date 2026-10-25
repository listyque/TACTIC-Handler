---
group: Workflows
icon: comment
order: 20
---
# External agent

Open a project and page, select objects, then choose **More options → External
agent**. The native modal captures your project, navigation page, Search Type,
table view and exact selected object keys. Inspect that context and describe the
result you want. The feature currently requires an administrator account and a
connected external host for the same TACTIC login and project.

**Allow the requested configuration changes** permits the host to expose native
configuration writes and inactive script drafts. Without it, only reads and
previews are available. Send once and follow progress and the answer in this
window. Results are ordinary TACTIC pages/projects/configuration; refresh the
relevant catalogue or reload cache to see them.

Closing the modal leaves work running. Reopening preserves the request, and the
list offers recent requests. **New request** captures the current page and
selection. Requests are independent; include necessary earlier details in a
follow-up. Project/selection changes after sending never retarget existing work.
Changing the signed-in account clears the local window context.

Cancel stops pending work or the external host's process. Native operations
already committed are preserved. A disconnected request becomes interrupted and
is never automatically rerun. Inspect actual changes before another attempt.
An offline host disables sending; the operator must reconnect it.

The agent works through existing TACTIC APIs, not source-tree edits. It can
prepare and, when configured, test check-in hooks and shelf buttons in isolated
Linux trials. Review exact source/binding/reports in **Script Editor → Agent
drafts** and activate separately. This handoff does not give the agent live
control of your desktop or permission to run generated Python on Windows.
Handler check-in hooks remain local Handler behavior; they do not enforce
browser/API uploads. Windows programs and studio plugins need their own manual
acceptance in the normal client.
