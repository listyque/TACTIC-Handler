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

Names, folders, pins and archives belong to the signed-in user and current
project and persist across clients/restarts. Existing conversations are retained.
Conflicting saves require a refresh. Switching conversations keeps unsent text
and attachments in this client session; send them to preserve them as messages.
For an unnamed initial draft, send it or name it before switching away.

**Archive conversation** hides a finished chat from the ordinary library.
Enable **Archived conversations** in **Conversation view** to find it and **Restore conversation** before
continuing. Running requests cannot be archived. The library does not delete
messages, undo project changes, start an agent or grant new permissions.
Only **Send** submits project context and attachments to the chosen connection.
