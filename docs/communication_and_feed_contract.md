# Communication and Activity Feed contract

## Scope and evidence

The current client already had `NotificationController` and `NotificationStack.qml`
for transient client events. `CommunicationController` and
`CommunicationView.qml` implement notes attached to the selected sObject; they are
not TACTIC chat. The original `Ui_messagesWidget` used the current `Login`, chat
subscriptions, `Message`, `MessageLog`, `subscribe()` and `log_message()`.
`Ui_floatNotifyWidget` refreshed subscriptions and messages, but did not provide a
complete notification centre. No usable Git history is present in this workspace,
so deleted prototypes could not be recovered from revisions; current and original
source trees are the evidence for this contract.

## 1. Local UI notifications

Purpose: report work performed by this running client. This layer never queries or
updates TACTIC messages, subscriptions, notes, or unread state.

| Event | Source | Presentation | Lifetime |
|---|---|---|---|
| success / completion | controller completion signals | toast and session history | toast auto-dismisses; history remains |
| info | `ApplicationController.notification_changed` | toast and session history | same |
| warning | classified client warning | toast and session history | same |
| error | controller error signals | toast and session history; traceback remains in Debug Log | same |
| progress | application loading state | non-dismissible transient toast | removed when work finishes |
| background completion | check-in and repository sync signals | completion or error toast | same |

The centre is session-scoped and capped at 200 entries. Dismissing a toast does not
remove its history entry. Clearing this history has no server-side effect. Duplicate
active errors are coalesced by the existing controller.

## 2. TACTIC messages and correspondence

Data source: the current TACTIC `Login`, `sthpw/subscription`, `sthpw/message`, and
`sthpw/message_log`. The original `Message` and `Subscription` objects remain the
authority; the QML controller exposes only records and identifiers.

| Capability | Source / rule | Current status |
|---|---|---|
| conversations | chat subscriptions containing the current login | implemented |
| sender / recipients | subscription members and message-log login | implemented |
| message body and time | `sthpw/message_log` | implemented |
| replies | existing `server.log_message(..., category="chat")` | implemented asynchronously |
| history | message-log query, newest page first | implemented, 30 rows per page |
| unread | compare message timestamp with subscription `last_cleared` | implemented with top-bar and conversation badges |
| mark read | update only the current login's chat subscription | implemented after visible history is loaded |
| notes | selected-sObject note API and `CommunicationController` | implemented separately in Notes dock |
| note attachments | snapshot attachment process used by notes | implemented in Notes dock |
| chat attachments | existing snapshot check-in, repository sync and `sthpw/connection` | implemented; download is membership-checked |
| linked sObject / task | `skey://` text delegates to the normal workspace search-key path | implemented |
| new conversation | `sthpw/message` plus chat subscriptions for the exact participant set | implemented; duplicate participant sets are reused |

No password or server object is exposed to QML. Refresh, send, attachment and read
operations use the existing server/commit pools. A shared five-second incremental
poll supplies message and activity deltas, with a 30-second error backoff.

## 3. Activity Feed

The feed is a read-only aggregation over existing TACTIC records. It has no event
database and does not create notifications. Opening an actionable row delegates its
search key to the normal workspace search/navigation path.

| Filter | Source | Meaning | Pagination |
|---|---|---|---|
| All | `sthpw/status_log` for current project | available status changes | 25 rows |
| My tasks | `sthpw/task.assigned=current login` | current assigned tasks ordered by update | 25 rows |
| My objects | `sthpw/status_log.login=current login` | activity performed by the current login; ownership is not represented reliably | 25 rows |
| Messages | current login chat subscriptions and latest available log | conversation activity | incremental conversation slice |
| Publications | `sthpw/snapshot` for current project | snapshots / published versions | 25 rows |

### Event support

| Requested event | Available source | Status |
|---|---|---|
| object created / updated | `sthpw/change_timestamp` | supported for incremental updates |
| snapshot created / new version | snapshot timestamp and version | supported as publication |
| check-in completed | snapshot may imply publication but does not prove operation type | not labelled as check-in |
| task status changed | status log when TACTIC writes it | supported |
| user assigned | current task state is available; historical assignment event is not guaranteed | partial |
| note added | `sthpw/note` timestamp | supported for incremental updates |
| attachment added | attachment snapshots have no confirmed global event type | unsupported in feed |

The feed loads history on open, filter change, explicit refresh, or **Load more**.
The shared incremental service appends new supported records without reloading the
whole model. Push/WebSocket transport and typing state remain outside this stage.

## Entry points and isolation

- Top bar: Messages, Activity Feed, and Notifications have separate buttons.
- Temporary tools menu: all three open singleton windows through the existing
  action and window registries.
- Notes remains an object-scoped dock and is not presented as chat.
- Toast visibility never changes TACTIC unread state; visible loaded message
  history advances only that conversation's `last_cleared` value.

## Manual verification

- Verify a conversation with two distinct logins, including unread state on the
  receiving login.
- Verify `status_log.search_type/search_code` navigation for each project schema.
- Verify snapshot navigation and paging with more than 25 publications.
- Verify attachment upload/download against a non-admin login and its repository.
