---
group: Workflows
icon: comment
order: 17
---
# Notes and messages

> Notes belong to an sObject or process; Messages provide personal and group conversations.

## Main controls

Activity Feed resolves linked objects using the selected project's schema, including when the
activity journal is read through the system project. Schema-defined link columns are preserved.

Both composers support text, attachments, clipboard images, emoji, replies, send state, and drag-
and-drop file attachments. Drop local files over an active Notes or Messages view to add them to the
same attachment staging list used by the attachment button.

Messages also support mentions, reactions, forwarding, pins, search, members, delivery state, and
conversation files. Text and staged attachments are separate for every note target and every
conversation.
Each message send uses a stable, unique attachment context and file names. A failed send keeps its
staged files for retry; an unavailable snapshot or failed attachment link is reported as an error.
An incomplete upload cannot send the text alone; the staged files remain available for retry.
Image attachments expand the chat bubble to the available media width. A web preview keeps its
aspect ratio, stays at its natural width when smaller, and appears above the message text.

Every user has an empty Favorites chat by default. It appears when Messages first loads, even
before the user sends anything there. Favorites belongs to the login across projects; an empty
history does not show an old message preview. Existing messages remain visible even when an older
TACTIC message log did not originally have a code.

For one task, Notes remain on the process branch. When the same process has additional tasks, the
primary task keeps that branch and every additional task receives its own note and attachment
timeline.

New messages and Activity Feed events use the application's own notification stack anchored to the
bottom-right work area of the active screen. Message cards show the conversation, sender avatar and
name, and a readable content preview.

Activity cards reuse the feed's author identity, event category, and semantic action text instead of
transport fields. Windows system notification balloons are not used.

Message notifications and Activity feed notifications have independent switches in Global Settings.
Disabling a switch hides only its pop-ups; history and unread counters continue updating.
After sign-in, Messages fetches current unread conversation summaries from the server, including
messages received while the app was closed. It updates its badge and shows the latest unread
notification from each conversation without opening the window.
Delivery and read receipts keep updating while Messages is hidden. Message groups use compact
metadata spacing and stable delegates so scrolling does not leave stale bubble fragments.
While a conversation is visible in the active Messages window, that conversation alone refreshes
every five seconds so replies, reactions, and receipts arrive quickly. The fast refresh stops when
the window is hidden or inactive. New-message pop-ups use the platform's standard notification beep.
The pop-up shows a circular sender avatar and stays visible for 15 seconds. Select Reply to type
and send without opening the chat; it stays open while you compose or while sending, and shows
any send error without discarding your text.
Background refresh keeps previously loaded older messages in place. Grabbing the scrollbar
stops the wheel animation, so it does not compete with dragging.
The scrollbar uses the measured height of loaded messages and does not change size
as you scroll past different-height cards. At the end, layout changes keep the last
message above the composer; loading older messages preserves your reading position.
The people icon in the chat header opens its members; its badge shows the member count.
The header shows a progress indicator only while a chat operation is running; otherwise its actions use that space. The timeline aligns with the header instead of adding a second side margin.
Right-click a chat in the list to select it and open its actions menu. It uses
the same permissions as the header menu, including clearing Favorites, your private chat.
A new message is revealed once, without highlighting it. Switching chats or
reactivating the window preserves each chat's position unless another new message
has arrived. Delayed read receipts do not repeat the scroll.
Server updates also preserve the position of inactive chats; returning to one
refreshes its messages in place without recreating the conversation view.
Switching chats keeps reaction rows at their existing height, so messages with
reactions do not shrink and expand or change the scrollbar when you return.
Signing out clears loaded chats and cancels their pending updates; signing in as another user
loads only that user's conversations. Per-user unsent drafts remain available on the next sign-in.

A raw server update never becomes an Activity Feed notification by itself. The app resolves the
matching journal event first, so the notification shows the same author, avatar, object and readable
change details as the feed card.

The shared emoji picker provides the complete Unicode 17 catalog with consistent Noto Color Emoji
artwork, category navigation, and name search. On a new server, an administrator confirms one schema
initialization for Messages and Knowledge Base.

The confirmation lists every Search Type and column that will be added and does not delete existing
data.

## Usage notes

- Press Enter to send and Ctrl+Enter for a new line.
- New entries stay anchored at the bottom like a messenger.
- Consecutive Messages from one author form a compact visual group: the name appears only on its
  first bubble, while one external avatar and bubble tail mark the final bubble.
  Bubbles share one corner radius; the tail and selection outline form one continuous contour.
  A modest gap separates sender details from the text, with consistent padding along the bubble edges.
- Notes keep their compact status-oriented layout unchanged.
- The author can edit or delete their own note or message for one hour after publication.
  Administrators and supervisors can edit or delete other people's notes and messages at any time.
  Unavailable actions are omitted from the item menu.
- A link to a deleted TACTIC item remains unavailable without interrupting work with an error popup.
- Direct conversations show the other user's shared live presence and last-seen time in the header;
  group conversations keep participant counts instead.
- The conversation timeline keeps a usable minimum width when its divider is dragged.
- Unsent text and attachments are restored after closing a window or restarting TACTIC Handler.
- Click an application's custom notification card to open its conversation or Activity Feed event.
- The main close button sends TACTIC Handler to the system tray by default.
- Disable Close to system tray in Global Settings to exit completely instead.

- When a session expires, background chat reads and server updates pause until you sign in again, including while the application is in the tray. Reopening the window does not retry a rejected ticket. Unsent chat drafts are retained.
