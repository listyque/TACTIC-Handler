---
group: Workflows
icon: comment
order: 20
---
# External agent

Connection, model and reasoning choices stay compact in the bottom message toolbar. They wrap only when the chat is too narrow, retaining bounded widths.

Open a project/page, select objects, then choose **More options → External agent**.
An administrator account and an external host connected for the same login/project
are required. Context chips show the project, page, type and selection count;
**Context details** reveals the saved page/view and exact selected keys.

You can also choose **External agent** directly from the object's basic context
menu. It starts a new conversation with the clicked object, or all selected
objects when that object is part of the selection. Previous conversations remain
in history. Send or clear an unsent message/attachments before changing objects.

Describe your task in the chat. **Attach files**, drop files onto the window, or
press **Ctrl+V** in the message to paste files/images. Image thumbnails and file
names appear before sending; remove an unwanted attachment with its cross.
Up to 20 files per message, 64 MB each. Images sent to this model are limited to
20 MB; arbitrary binary originals can be checked in without being decoded.
The Paste button may require browser clipboard permission; on an ordinary HTTP
LAN address use Ctrl+V in the message. Browser clipboard formats depend on the browser; use drop or file selection for other formats. Normal text paste remains available.

Choose **Reasoning effort** next to the model when the connected agent offers it.
The choices belong to that model; **Agent default** keeps the provider setting.
Change model/effort between turns. Switching models resets the effort choice.

You can send attachments without text. Sent images have private thumbnails, including
after reopening the chat. On desktop, Enter sends; Shift+Enter adds a line. On phones,
Enter adds a line and the Send button sends. Activity describes actual tool
starts/completions and commentary in the transcript column.

Enable **Allow internet access** before starting a new conversation to let Codex use
native live web search and download public HTTPS files into the chat. It remains disabled by default. Search is separate from
permission to edit TACTIC. Downloads retain source URLs/hashes and use the normal
private attachment/check-in tools. Anonymous public HTTPS, up to 64 MB per file;
private addresses and redirects into local networks are refused. Shell and local
file access remain disabled. Do not include confidential data in web search requests.

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

The agent can create project records and children through the existing schema,
using native defaults and code generation. For example: “Create Episode 03 with
10 shots.” Answers use display names; technical codes remain separate details.
Operation details follow the same transcript column as the assistant's answer.
For “add selected assets to Episode 03”, the agent can find that episode and
link the captured selection with one native command. Existing links are skipped;
there is no operation ID to enter, no file-naming setup and no asset duplication.

The agent can use native existing-project workflow/field tools and check attached
files into an object's workflow process. For example: “For this asset, create
reference → model → texture → rig and check these reference images into reference.”
Open created resources through ordinary navigation; refresh the cache when needed.
The agent can read native file history and continue an existing version series
under the current naming rule. It cannot overwrite an existing file to bypass a
naming collision. Open the object's **Snapshot Browser** to view published files
and earlier versions; identical source filenames normally form one version series.
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

## AI connections

Open **Configuration → AI providers → Manage AI connections**, or the settings
button beside **AI connection** in the chat. Profiles belong to your TACTIC login.
Keep the existing **Codex account**, or add **OpenAI**, **OpenAI-compatible API**,
**Local model server**, **Anthropic**, or **Gemini**. Enter the API base URL and
key when required. An optional host environment variable can supply the key
instead. Localhost refers to the external host computer. Compatible endpoints
use Chat Completions; OpenAI uses Responses; Anthropic and Gemini use their native APIs.

Save, then choose **Check connection**. The connected external host retrieves
models using that connection's credentials. Checks send no conversation, project
or attachments. Choose a returned default model and save it, or select a model
in the chat. Account Codex retains its own available models and reasoning levels.
Other connections show only the model capabilities they advertise; tool/image
support depends on the model. Built-in web search is available through Codex,
OpenAI and Anthropic when allowed; other connections can use direct download tools.

Choose **AI connection** and **Model** before sending. Connection/model changes
are allowed between turns. Only the selected connection receives the submitted
conversation, captured project/page/selection and attachments after **Send**.
TACTIC tickets/passwords and other connections' keys are not sent to the model.
Changing or disabling a connection before execution stops that turn; send again
to authorize a changed destination. Corrections and cancellation remain available.

Stored keys are write-only: a blank field keeps the existing key; use **Remove
stored API key** to clear it. Windows encrypts keys for the server's OS account.
Linux requires the administrator to configure a private vault key file first.
The external host receives credentials encrypted for its temporary host key.
Closing the editor preserves an unsaved draft; **Discard** restores saved values.

Activity, waiting and completion status appear inside the conversation, aligned with the agent's messages. They follow the transcript as new messages arrive.

The agent can create native tasks for selected project objects and edit their descriptions, assignments, supervisors, planned dates/hours, progress and statuses through the ordinary task inspector. It prepares actual workflow choices and revisions before saving a checked batch. Existing tasks are retained, exact retries do not create duplicates, and conflicts roll back the packet. Scoped MCP connections must explicitly include the task preparation/save tools. These task operations are outside the field-only Undo button.

## MCP connections

The **MCP connections** window grants access only to the captured project and
the checked tools. Each permission row shows its name, description and **Read
only** or **Write** access. Click the row or use Space to toggle it. The counter
shows the selected total. **Select all tools** selects the complete available
catalogue, including write tools. **Select read tools** selects only tools marked read-only
by the server; **Clear** removes the selection. Neither button issues access.
Creation requires a name and at least one selected tool. Existing connections
and revocation remain below the form; scroll to reach them.

Choose **No expiration** for access without a calendar deadline. It remains
revocable and depends on the owner's enabled account and current permissions.
It uses a separate server-held session and does not extend the browser login.
Revoking access also removes that connection's dedicated session.
Existing connections keep their configured deadlines. The option appears only
when the connected server supports it. Scrollbars have reserved space so fields,
row captions and panel borders remain visible with classic Windows scrollbars.

## Conversation library

Conversation history is a separate left panel, with **Search conversations** and
grouping **By time**, **By Search Type**, or **By folder** under **Conversation
view** (three dots in the panel header). The search icon opens the search field.
Use **Show/Hide
conversations** to collapse it. On narrow windows the history opens as a separate
panel; selecting a conversation returns to the chat. The divider changes its
width on desktop. Dates use the client's local day; pinned conversations remain
easy to find. Search includes message text, titles and Search Type identifiers,
with **Load more conversations** for long histories.

**New conversation** creates an empty saved draft without running a model.
Use the pencil beside the title or the conversation's three dots to set its
name, choose a folder and pin/unpin it. An unnamed chat uses its first message
as its title. Create folders in **Conversation view** and edit them from folder
headings in **By folder**. Removing a folder moves its conversations to
**Ungrouped**, preserving the messages. Pinned chats inside folders stay in
their folder; other pinned chats have their own section.

Names, folders, pins and archives belong to the signed-in user and the
conversation's project and persist across clients/restarts. Existing conversations are retained.
Conflicting saves require a refresh. Switching conversations keeps unsent text
and attachments in this client session; send them to preserve them as messages.
For an unnamed initial draft, send it or name it before switching away.

**Archive conversation** hides a finished chat from the ordinary library.
Enable **Archived conversations** in **Conversation view** to find it and **Restore conversation** before
continuing. Running requests cannot be archived. The library does not delete
messages, undo project changes, start an agent or grant new permissions.
Only **Send** submits project context and attachments to the chosen connection.

The sidebar starts with **All projects**, including your older chats after you
switch to a new project. Each conversation shows its project. Use **Conversation
project** to narrow the list; search also matches project names. Only your own
chats in accessible projects are listed. Filtering never changes the open chat's
project or selection. Opening an old chat restores its original context.

**New conversation** uses the selected project filter, or the current workspace
project when **All projects** is selected. A different project's new chat starts
without the workspace's page or selected objects. Folders remain project-specific.
A warning identifies project histories whose databases are unavailable.

If the connection drops, keep the chat open: automatic reads resume and clear the
connection error when the server responds. The refresh arrow rereads the same
conversation without resending the task. A lost connection does not prove that
work stopped; inspect its saved answer and actual changes before continuing.
Rejected operation errors remain visible until a deliberate refresh or retry.

**External agent is offline** refers to the selected chat's project, not the
whole server. The external host can use `--all-projects` to discover accessible
projects with the installed agent schema, including new projects, at its regular
heartbeat. Explicit repeated `--project` options keep their restricted scope.
Discovery reads configuration only; a model receives a task only after **Send**.

Use **Agent permissions** (the sliders in the composer toolbar) for **Allow
requested changes**, **Allow internet access** and **AI providers**. These settings
use a compact menu; the checked marks show the current choices. Permissions stay
fixed after the first Send, as before. The separate checkbox rows are removed.

The agent can find and read your saved conversations across accessible projects
when you ask it to continue earlier work. It searches history before asking you
to paste a task that is already saved. History is read in bounded pages; earlier
messages do not grant permissions or change the current project/selection.

For an explicit source, keep the target chat open, find the old chat in the
sidebar (All projects), open that row's three dots and choose **Use in current
conversation**. The **Conversation context** caption shows the link. Up to five
finished source chats can be linked to a saved draft or finished conversation.
Send a follow-up such as “Continue” to let the selected connection read them.
Linking alone does not start a model. Existing messages are preserved. Earlier
attachments are listed by name; they are not copied to the new chat's uploads.

Choose **Run agent on** in the chat or **Configuration → AI providers**, then **Connect agent**.
- **This computer** in TH uses your local Codex CLI sign-in and local provider API addresses. First connection installs the agent dependencies into a separate cached Python environment; global Python is unchanged. Codex CLI must already be installed and signed in.
- In TS, choose a connected TH computer signed in to the same TACTIC account. The browser sends fixed start/stop commands through TACTIC; it does not launch local programs itself. Keep TH open.
- **TACTIC server** is a separate, explicit option. It uses the server OS account, its Codex sign-in and its local API addresses. It is never selected silently as a fallback.

Nothing starts on opening the chat or pressing Send. **Disconnect agent** stops the selected managed executor; applied changes remain. Closing the chat leaves it running. Closing/signing out of TH stops that TH's local executors; the server option continues independently. Externally launched hosts must be stopped where they were launched. Existing running connections remain visible until disconnected.

In **All projects**, the project name appears beneath each conversation title; the working indicator stays beside the text.


The agent can read and add task/process comments through the native discussion tools. A comment does not change task status or description. Repeated delivery in one chat turn does not add duplicates; an intentional follow-up can add the same text again. Comments appear in the ordinary Task Inspector, with your author identity and native triggers. Group tool permissions apply to `ts_notes_read` and `ts_note_add`.

For an actual object preview, the agent checks one image into the built-in `icon` context. It does not need an artificial icon node in the workflow; a reference file in a work process is a separate operation. Existing files and applied changes are preserved when a task is only partly completed. Operation details open from a compact disclosure aligned with the assistant's answer.
