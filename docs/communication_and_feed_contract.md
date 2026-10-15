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

On a stock TACTIC schema, Handler requires one explicit administrator bootstrap
before chat starts. A single confirmation shared with Knowledge Base adds the
`metadata` text column to `sthpw/message` and `sthpw/message_log`, creates the
current project's `PROJECT/th_knowledge_article` Search Type when absent, and
adds its content columns. The confirmation names all affected Search Types and
columns. It never deletes or rewrites existing columns or data. Until the two
message columns exist, chat, reactions, delivery receipts, and presence polling
stay idle while unrelated activity/cache polling continues.
TACTIC versions that expose an unregistered Search Type as an `Undefined`
object follow this same uninitialized path; schema discovery never turns that
expected first-run state into an XML-RPC fault. A registered Search Type whose
physical table is absent follows the same path without issuing TACTIC's failing
`SELECT ... LIMIT 0` column probe.

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

Selecting a conversation preserves the conversation-list viewport while the
selection roles update; switching chats never jumps that list back to the top.

No password or server object is exposed to QML. Refresh, send, attachment and read
operations use the existing server/commit pools. A shared configurable incremental
poll (30 seconds by default, selectable from 5 to 60 seconds) supplies message and
activity deltas, with a 30-second error backoff.
The shared update service starts as soon as authentication succeeds. It polls chat
subscriptions even when the Messages window has never been created; its first
result establishes a silent baseline, and later messages drive unread badges and
the application's custom notification window. Windows notification balloons are
not used. Opening Messages only enables visible history and reaction work, not
the notification subscription. **Message notifications** in Global Settings
independently disables those pop-up cards without pausing subscription polling,
conversation history, or unread counters. The value is owned by
`MessagesController` and persisted through the configuration API.
Live message popups are deduplicated by message identity. A conversation
summary may reach the client before its message delta, so its latest timestamp
must not suppress that unseen message's popup.
While one conversation is visible and its window is active, its latest history
page is refreshed every five seconds. This scoped refresh updates messages,
reactions, and delivery/read receipts without accelerating polling for other
conversations; it stops when Messages is hidden or inactive. New-message cards
also play the platform's standard application beep.
Background history refreshes retain the loaded older prefix and pagination
offset instead of replacing it with the latest page. A burst that exceeds one
page is fetched through to an overlapping message before merging by identity.
The timeline exposes the shared scrollbar's `cancelWheelScroll` hook so grabbing
the thumb stops wheel and jump animations before native dragging takes over.
Loaded message cards use a Column inside a Flickable, not a virtualized ListView.
Rich text, emoji, reactions, and previews produce different row heights; estimating
unseen heights changed the scroll extent during wheel input. The column exposes
its measured height, keeping the scrollbar range independent of scroll position.
An end anchor follows real layout/viewport height changes until the reader scrolls
away. Away from the end, a retained card and its viewport offset anchor older-page
insertion. Server pagination and the 12-conversation cache still bound initial
loading; rendering cost now grows with loaded pages, not just visible rows.
The regression uses unequal-height messages and checks invariant contentHeight
during wheel events, last-card viewport coordinates after resize/layout changes,
and the visible anchor after prepending history.
Each retained timeline owns the identity of its last automatically revealed
message. Activation, history completion, and message notifications request a
reveal, but only a different latest message can move that timeline. Background
arrivals wait for the visible, active window; a reveal is immediate after layout
and never highlights a message. Explicit search/reply navigation alone uses
`messageFocusRequested`. Neither activation nor unread flags issue that signal.
Switching chats, duplicate notifications, and delayed read receipts leave an
already presented message and the reader's scroll position unchanged.
A conversation's first presentation waits for the history request and
deferred delegate layout before positioning at the end and revealing the list.
Leaving a timeline cancels its scroll animations and flick rather than letting
them change its retained position while hidden. The full MessagesView regression
exercises real conversation clicks, initial asynchronous loading, a background
arrival, window reactivation, duplicate notifications, and an empty Favorites
chat, checking both retained contentY and the absence of automatic highlights.
The regression loads the view through the production `WindowContent` loader with
history already populated. `WindowContent` waits until its initial properties are
installed before creating content once; loading on initial property notifications
created and destroyed intermediate views with pending presentation callbacks.
Server-cache invalidation marks conversations dirty without discarding their
retained models or QML surfaces. Returning to a dirty chat refreshes its data in
the background with the transport cache bypassed, keeping the same viewport.
The regression invalidates message data while another chat is selected and checks
surface identity, scroll position, and the background refresh request.
Reaction rows use Flow's natural implicit height. Their preferred height must not
depend on effective `visible`: hiding an ancestor chat otherwise collapses every
reaction row, changes the scroll range, and lets anchor restoration move contentY
before those rows expand again. The mixed-content regression includes reactions,
emoji-only messages, missing-link previews, replies, and image attachments. It
observes card-height and content-height signals as well as contentY across chat
switches, so a transient collapse cannot pass by returning to the same final size.
The online roster is read on every shared poll so newly connected peers appear
within one poll interval. The current login's heartbeat is still written only at
the configured presence interval, avoiding a write on every roster refresh.

## 3. Activity Feed

Instance endpoints use `Schema.get(project_code=project_code)`, even when the journal procedure
runs in `sthpw`. A real XML-RPC regression in Stream exercises both procedure bodies with custom
link columns; Handler query tests assert the requested project reaches schema lookup.

The feed is a read-only aggregation over existing TACTIC records. It has no event
database. New incremental events from other logins are projected into the existing
bounded bottom-right custom notification window only after one coalesced, bounded
journal lookup resolves the same enriched event used by the feed card. The raw
server-update row is a cursor and invalidation signal, never notification copy.
Opening an activity notification opens the feed; opening an
actionable row delegates its
search key to the normal workspace search/navigation path.

| Filter | Source | Meaning | Pagination |
|---|---|---|---|
| All | shared activity journal | every supported non-chat event in the current project, including notes, publications, tasks, status changes, object mutations, and work hours | 25 rows |
| My tasks | `sthpw/task.assigned=current login` | current assigned tasks ordered by update | 25 rows |
| My objects | `sthpw/status_log.login=current login` | activity performed by the current login; ownership is not represented reliably | 25 rows |
| Notes | `sthpw/note` for current project | notes in the shared activity journal | 25 rows |
| Publications | `sthpw/snapshot` for current project | snapshots / published versions | 25 rows |

The profile's **Recent activity** block and the feed's user scope use this same
activity-journal query and event-kind contract. A profile is not allowed to
surface a note that the **All** feed silently excludes. Chat correspondence
remains in **Messages**, where it has separate membership and unread semantics.

### Event support

| Requested event | Available source | Status |
|---|---|---|
| object created / updated / deleted | `sthpw/sobject_log` joined to `sthpw/transaction_log`; `sthpw/change_timestamp` fills missing latest changes | supported for project sObjects; technical columns and events already represented by dedicated sources are excluded |
| snapshot created / new version | snapshot timestamp and version | supported as publication |
| check-in completed | snapshot may imply publication but does not prove operation type | not labelled as check-in |
| task status changed | status log when TACTIC writes it | supported |
| user assigned | current task state is available; historical assignment event is not guaranteed | partial |
| note added | `sthpw/note` timestamp | supported for incremental updates |
| work hours logged / changed | `sthpw/transaction_log` operation plus `sthpw/work_hour` and its Task parent | supported with operation author/time, work date, duration, category, approval state, description, process, and task navigation |
| attachment added | attachment snapshots have no confirmed global event type | unsupported in feed |

Object audit events are reconstructed from the transaction XML. The transaction
`namespace` is the project code, and transaction XML must be read through
`TransactionLog.get_xml_value("transaction")` because TACTIC compresses payloads
larger than 10 KiB. `sobject_log` is used only as a per-object correlation index:
TACTIC deliberately omits delete entries and does not build the index for large
transactions. `change_timestamp` is a last-change fallback, not history;
`timestamp` is the row event time, while `changed_on` and `changed_by` are JSON
maps keyed by changed column. Create, update, and delete cards show the object
type/name and render meaningful field changes as separate readable rows.
Instance connector rows are classified from every `relationship="instance"`
definition in the current project schema; connector Search Type names are never
hardcoded. The client passes the schema-derived pair of endpoint Search Types to
the read-only server query, which resolves both real object titles and search
keys. The card therefore describes a readable link or unlink action for arbitrary
instance relations, including self-relations, and hides the connector code,
foreign-key columns, and `relative_dir` metadata.
Work-hour cards use the transaction timestamp for journal ordering rather than
mistaking the recorded work day for the operation time. The current WorkHour row
provides duration, category, approval state, description, and owner; its Task
provides the project sObject and process/context navigation target. A changed
WorkHour records received after an incremental invalidation are returned through
the same enriched query and shape.

The feed loads history on open, filter change, explicit refresh, or **Load more**.
The shared update poll returns a four-point clock observation. Presentation maps
both timezone differences and server clock drift onto the workstation's local
time, while raw server timestamps remain unchanged for cursors and pagination.
Events performed by the current stable login remain in feed history by default,
but never contribute to its unread badge or activity notifications. **Exclude my
activity** is an explicit feed-only switch. When enabled, the server removes those
events before pagination and calendar aggregation, and the controller repeats the
identity check when publishing cached or live data. The switch does not change
unread or notification semantics. **Activity notifications** independently enables
or disables bottom-right pop-ups. Its value is owned by `ActivityFeedController`,
persisted through the configuration API, and exposed by both Activity Feed and
Global Settings; disabling it marks incoming identities as observed so enabling it
cannot replay a backlog. Message and activity notification preferences are separate;
neither switch changes history loading or unread accounting.
The shared incremental service uses its lightweight activity rows only to advance
the unread cursor and invalidate activity data. A visible feed coalesces those rows
into one asynchronous first-page query through the same enriched journal path as
explicit Refresh; raw snapshot, file, and change-timestamp rows are never inserted
into the visible model. The previous page remains visible until the authoritative
result is ready. Activity received while the feed is hidden performs no query or
model publication and is reconciled when the feed is next opened. A batch received
while another page query is running schedules exactly one follow-up reconciliation.
Push/WebSocket transport and typing state remain outside this stage.
The first page never waits for calendar aggregation: it requests only the bounded
activity page. Full-history day counts are requested by a separate worker when the
calendar is opened and are cached for the current project, category, and user scope.
When direct activity already fills the requested page, its oldest candidate becomes
the lower timestamp bound for transaction and change-log enrichment; older audit XML
cannot enter that page and is not loaded or parsed.
Normal activity-cache invalidation marks calendar counts stale without discarding
known historical days. An open calendar requests a full recount; a closed one
defers work until opened. Invalidation during an active recount retains its
displayable result but does not persist it as current, and coalesces a follow-up
request. Explicit Refresh bypasses the calendar query cache and recounts all days,
not just the last cached day. Hard cache reset still clears the calendar projection.
The calendar loading indicator does not change its geometry or move day buttons.

Feed pagination consumes the shared scrollbar's gesture permit after ListView
layout, including wheel intent with disabled animations or at an existing end.
It rechecks on page completion to fill a short/locally filtered viewport. Hidden,
busy, failed, and exhausted feeds do not automatically query; thumb drags only
navigate loaded content. Adjacent offset pages are merged by stable `eventId`,
because activity inserted while paging can move an already loaded boundary event
into the next server page. The retained event wins, the source offset still
advances by the consumed page size, and the keyed Qt model never receives a
duplicate identity. `tests/test_activity_feed_loading.py` exercises real
wheel input, queued controller results, older calendar day selection, refresh,
invalidation, and stale-response rejection; `tests/test_activity_feed_qml.py`
covers scrollbar dragging and narrow/wide layout.

The cache is persisted through the application configuration API and records
whether it covers complete history. Only a verified complete cache may recount the
last cached activity day and request newer rows; missing, obsolete, or partial
caches are rebuilt from full history. A complete calendar from an older activity
revision remains visible as a stale lower bound across application restarts while
that full recount runs; an explicit cache clear or cache-preference generation
change still discards it. While the full **All** calendar is loading,
complete Notes and Publications caches provide a summed lower bound, so **All**
cannot expose fewer known events than either category. The calendar opens
immediately and updates its badges when the worker completes.
Activity and profile reads retry temporary HTTP 502, 503, and 504 gateway failures
in their existing background workers, with three bounded attempts and short
backoff. Intermediate failures remain diagnostic warnings and never open the error
surface; the final failure retains its complete command and traceback. Procedures
that can mutate TACTIC are deliberately excluded because retrying after a lost
response could duplicate a completed server operation.
When event cards exceed the viewport, the feed keeps the shared vertical scrollbar
visible and reserves a gutter so the bar never covers card content.
Task events display the parent sObject plus their process/context rather than a
technical task code. Activating one opens the parent-object Task Manager scope,
selects the exact task, and synchronizes Task Inspector; it never opens an
`sthpw/task` Search Tab. A task enters **My tasks** through its `assigned`
column, which is not treated as the event author. The author is resolved from
the task's latest `change_timestamp.transaction_code` and `transaction_log`,
with the latest `sobject_log.login` as a fallback. Only a resolved audit
operation whose login is empty is labelled as a server trigger; a blank
`sthpw/task.login` by itself is not evidence of server generation.
System and configuration objects such as `config/widget_config` keep the
project context encoded by their search key. They can open as direct generic
results without a project SearchType and must not request repository-sync
snapshot state, which exists only for project Search Types.

## Entry points and isolation

- Top bar: Messages, Activity Feed, and Notifications have separate buttons.
- Notes remains an object-scoped dock and is not presented as chat.
- Toast visibility never changes TACTIC unread state; visible loaded message
  history advances only that conversation's `last_cleared` value.
- Activity and Messages cards use one application-owned frameless window. They
  suppress duplicates by stable event identity, never include the current login,
  and do not load the hidden feed model. A pending activity notification may run
  one bounded read-only journal lookup while the feed window is hidden; requests
  arriving together share that lookup.
- The notification stack is anchored to the bottom-right work area of the active
  screen and repositions when its height or screen changes. Message cards show the
  conversation, sender avatar/name, and the same readable content preview used by
  Messages. Activity cards reuse the feed's resolved author identity, event kind,
  object identity, field changes, and semantic action sentence; transport field
  dumps are not presentation data.

## Manual verification

- Verify a conversation with two distinct logins, including unread state on the
  receiving login.
- Verify `status_log.search_type/search_code` navigation for each project schema.
- Verify snapshot navigation and paging with more than 25 publications.
- Verify attachment upload/download against a non-admin login and its repository.

### Expired session suspension

`ApplicationController.authentication_required` is authoritative while an expired ticket and cached login objects remain present. MessagesController stops its active-history timer and clears deferred summary/history reads when authentication is requested; load, refresh, history and read receipts remain idle until sign-in. Explicit sign-out still clears session models. ServerUpdateService stops both polling and SSE during re-authentication. Successful authentication resumes the existing lifecycle; expiry does not erase composer drafts.

`test_expired_ticket_does_not_requeue_hidden_chat_reads` exercises the real Debug Log authentication signal while a summary request and a deferred refresh are pending. The update-service test keeps the old ticket/login objects to verify suspension and restart. Stream's matching JSON authentication failure closes its background-read gate before notifying the application; `frontend/tests/session_expiry.mjs` checks cancellation, focus/timers and sign-in without a live server.
