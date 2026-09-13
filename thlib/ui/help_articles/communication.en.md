---
group: Workflows
icon: comment
order: 17
---
# Notes and messages

> Notes belong to an sObject or process; Messages provide personal and group conversations.

## Main controls

Both composers support text, attachments, clipboard images, emoji, replies, send state, and drag-
and-drop file attachments. Drop local files over an active Notes or Messages view to add them to the
same attachment staging list used by the attachment button.

Messages also support mentions, reactions, forwarding, pins, search, members, delivery state, and
conversation files. Text and staged attachments are separate for every note target and every
conversation.

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
- Notes keep their compact status-oriented layout unchanged.
- Use item menus to edit or delete content when permissions allow.
- Direct conversations show the other user's shared live presence and last-seen time in the header;
  group conversations keep participant counts instead.
- The conversation timeline keeps a usable minimum width when its divider is dragged.
- Unsent text and attachments are restored after closing a window or restarting TACTIC Handler.
- Click an application's custom notification card to open its conversation or Activity Feed event.
- The main close button sends TACTIC Handler to the system tray by default.
- Disable Close to system tray in Global Settings to exit completely instead.
