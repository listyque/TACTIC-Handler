---
group: Workflows
icon: comment
order: 20
---
# External agent

Open a project/page, select objects, then choose **More options → External agent**.
An administrator account and an external host connected for the same login/project
are required. Context chips show the project, page, type and selection count;
**Context details** reveals the saved page/view and exact selected keys.

Describe your task in the chat. **Attach files**, drop files onto the window, or
press **Ctrl+V** in the message to paste files/images. Image thumbnails and file
names appear before sending; remove an unwanted attachment with its cross.
Up to 20 files per message, 64 MB each. Images sent to this model are limited to
20 MB; arbitrary binary originals can be checked in without being decoded.
The Paste button may require browser clipboard permission; on an ordinary HTTP
LAN address use Ctrl+V in the message. Browser clipboard formats depend on the browser; use drop or file selection for other formats. Normal text paste remains available.

If the connected agent offers models, select one in **Model**. Its list comes
from that connection/account. Change it between turns. Enable **Allow the
requested configuration changes** before the first message to authorize the
requested edits. Otherwise the conversation is read-only. Authorization and
context remain fixed for that conversation.

**Send to agent** starts a turn. Responses render as readable messages with lists,
links and code. Tool activity is separate from the answer. You can write and send
**Send correction** while the agent works. After completion, send another message
in the same chat: the previous conversation and object identities are retained.
A green **Task completed** means the agent reported verified completion;
**Waiting for your reply** and **Task blocked — see the answer** explicitly show
that more information or capability is needed. Read the answer and actual results.

The agent can use native existing-project workflow/field tools and check attached
files into an object's workflow process. For example: “For this asset, create
reference → model → texture → rig and check these reference images into reference.”
Open created resources through ordinary navigation; refresh the cache when needed.
Download attached originals by clicking their filenames. In TH the downloaded
file's folder opens; files are not automatically executed.

Closing the window leaves work running. Reopen it or select a conversation from
the list. **New conversation** captures the current page/selection. Navigating to
another project never retargets a previously sent task. **Cancel request** stops
pending work; committed operations remain. Disconnected/interrupted tasks are
not automatically repeated.

**Undo field change** appears only for the latest reversible entity-field patch,
after work finishes. It refuses to overwrite a later edit. It does not undo
workflow/schema creation, check-ins, naming/pages/projects or script activation.

Generated executable scripts remain inactive drafts. Review source/trials in
**Script Editor → Agent drafts**, then activate explicitly. TH hooks/shelf scripts
execute in TH. Browser/API check-ins do not run local TH hooks. The agent has no
live control of the TH desktop, shell or application source tree.
