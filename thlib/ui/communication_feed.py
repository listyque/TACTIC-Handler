from __future__ import annotations

import hashlib
import html
import json
import re
import traceback
import uuid
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl

from PySide6.QtCore import (
    QObject,
    Property,
    QTimer,
    QUrl,
    Qt,
    Signal,
    Slot,
)

from thlib.environment import env_read_config, env_write_config
from .composer_drafts import ComposerDrafts
from .workspace_models.records import RecordListModel
from .activity import (
    JOURNAL_ACTIVITY_KINDS,
    activity_actor_logins,
    activity_record,
    activity_timestamp_labels,
    present_activity_records,
)
from .skey_previews import display_html_without_skeys, extract_skeys
from .rich_text import linkify_plain_text
from .user_identity import user_avatar_color
from .ui_performance import measure_ui


def _worker_error(error):
    payload = error[0] if isinstance(error, tuple) and error else error
    stacktrace = ""
    if isinstance(payload, dict):
        stacktrace = str(payload.get("stacktrace") or "")
        payload = payload.get("exception") or payload.get("message") or payload
    return str(payload or "Server request failed"), stacktrace


def _message_identity(value):
    value = str(value or "").strip()
    if value.startswith("skey://"):
        value = value[7:]
    search_type, separator, query = value.partition("?")
    if not separator:
        return value
    values = dict(parse_qsl(query, keep_blank_values=True))
    identity = values.get("code") or values.get("id")
    return str(identity or value)


def _message_skey(value):
    value = str(value or "").strip()
    if not value:
        return ""
    if value.startswith("skey://"):
        return value
    if "?" in value:
        return "skey://" + value
    return "skey://sthpw/message_log?code=" + value


def _link_user_mentions(value, logins):
    lookup = {
        str(login).casefold(): str(login)
        for login in (logins or []) if str(login or "").strip()
    }
    if not lookup:
        return str(value or "")
    pattern = re.compile(r"(?<![A-Za-z0-9_./@-])@([A-Za-z0-9_.-]+)")

    def replace(match):
        login = lookup.get(match.group(1).casefold())
        if not login:
            return match.group(0)
        escaped_login = html.escape(login, quote=True)
        return '<a href="user://{0}">@{1}</a>'.format(
            escaped_login, html.escape(match.group(1))
        )

    return pattern.sub(replace, str(value or ""))


def _chat_data(bypass_cache=False):
    from thlib.environment import env_inst
    from thlib import server_cache
    import thlib.tactic_classes as tc

    if env_inst.get_current_login_object() is None:
        return ([], {})
    cache_key = "conversations"
    if bypass_cache:
        server_cache.invalidate_domains(("messages",), "sthpw")
    cache_token = server_cache.token("messages", "sthpw")
    cached = None if bypass_cache else server_cache.read_entry(
        "messages", cache_key, "sthpw",
    )
    if isinstance(cached, dict):
        return cached
    result = tc.get_chat_conversations()
    if cache_token is not None and isinstance(result, dict):
        server_cache.write_entry(
            "messages", cache_key, result, "sthpw",
            expected_token=cache_token,
        )
    return result


class MessagesController(QObject):
    CONVERSATION_CACHE_LIMIT = 12
    MESSAGE_GROUP_WINDOW_SECONDS = 5 * 60
    stateChanged = Signal()
    schemaInitialized = Signal()
    messageSent = Signal()
    newMessage = Signal(str, str, str)
    newMessageNotification = Signal("QVariantMap")
    notificationsEnabledChanged = Signal()
    conversationChanging = Signal(str)
    conversationRestored = Signal(str)
    conversationLoaded = Signal()
    messageFocusRequested = Signal(str)
    userProfileRequested = Signal(str)
    replyStarted = Signal()
    forwardStarted = Signal()
    messageSentForConversation = Signal(str)
    messageAppendedForConversation = Signal(str)
    visibilityChanged = Signal(bool)
    draftChanged = Signal()

    def __init__(
        self, application, attachments=None, parent=None, users=None,
        skey_previews=None, clock=None, config_queue=None,
    ):
        super().__init__(parent or application)
        self._application = application
        self._performance = getattr(application, "ui_performance", None)
        self._settings = dict(env_read_config(
            filename="ui_state",
            unique_id="cache/messages",
            long_abs_path=True,
        ) or {})
        self._notification_preferences = dict(env_read_config(
            filename="ui_settings",
            unique_id="ui_messages",
            long_abs_path=True,
        ) or {})
        self._notifications_enabled = bool(
            self._notification_preferences.get(
                "notifications/enabled", True
            )
        )
        self._settings_flush_timer = QTimer(self)
        self._settings_flush_timer.setSingleShot(True)
        self._settings_flush_timer.setInterval(750)
        self._settings_flush_timer.timeout.connect(self._write_settings)
        draft_state = dict(env_read_config(
            filename="drafts",
            unique_id="cache/messages",
            long_abs_path=True,
        ) or {})
        self._composer = ComposerDrafts(
            "cache/messages", draft_state, attachments=attachments,
            queue=config_queue, writer=env_write_config, parent=self,
        )
        self._composer.changed.connect(self.draftChanged)
        self.attachments = attachments
        self._users = users
        self._skey_previews = skey_previews
        self._clock = clock
        self.conversations = RecordListModel((
            "conversationId", "title", "recipients", "status",
            "lastCleared", "unread", "mentionCount", "selected", "lastMessage",
            "lastMessageSummary", "lastMessageLinkedCount",
            "lastTimestamp", "lastSender", "avatarUrl", "initials",
            "participantCount", "recipientNames", "memberSummary",
            "messageCount", "attachmentCount", "createdBy", "createdAt",
            "canManage", "canRename", "canDelete", "canAddMembers",
            "canClearPersonal", "isPersonalNotes", "acronym", "colorIndex",
            "createdPretty", "activePretty", "peerLogin",
            "presenceKnown", "online", "lastSeen", "lastSeenPretty",
        ))
        self.messages = RecordListModel((
            "messageId", "sender", "body", "bodyHtml", "displayHtml",
            "skeyPreviews", "timestamp",
            "isOwn", "unread", "attachments", "attachmentCount",
            "senderDisplay", "avatarUrl", "initials", "senderColor",
            "timePretty", "timeSimple", "canEdit", "edited", "editedBy",
            "editedAt", "editHistory", "pinned", "replyTo", "forwardedFrom",
            "forwardSelected", "reactions", "reactionPending",
            "deliveryStatus", "deliveryRecipientCount",
            "deliveryDeliveredCount", "deliveryReadCount",
            "groupFirst", "groupLast",
        ), identity_role="messageId")
        self.messages.setParent(self)
        self.message_surfaces = RecordListModel((
            "conversationId", "messageModel", "current", "historyHasMore",
        ))
        self.message_surfaces.replace([{
            "conversationId": "", "messageModel": self.messages, "current": True,
            "historyHasMore": False,
        }])
        self._conversation_id = ""
        self._initialized = False
        self._can_initialize = False
        self._busy = False
        self._sending = False
        self._sending_conversation_id = ""
        self._error = ""
        self._request_id = ""
        self._offset = 0
        self._page_size = 30
        self._has_more = False
        self._message_search = ""
        self._pending_message_focus = ""
        self._pinned_message = {}
        self._pin_history = []
        self._reply_target = {}
        self._forward_selection = set()
        self._worker = None
        self._history_worker = None
        self._history_request_id = ""
        self._history_conversation_id = ""
        self._history_busy = False
        self._history_background = False
        self._pending_history_load = None
        self._loaded_conversation_id = ""
        self._loaded_server_timestamp = ""
        self._conversation_cache = OrderedDict()
        self._conversation_cache_limit = self.CONVERSATION_CACHE_LIMIT
        self._dirty_conversations = set()
        self._read_worker = None
        self._visible = False
        self._timestamp_presentation_dirty = False
        self._conversation_opened = False
        self._can_create_group = False
        self._can_delete_messages = False
        self._pending_body = ""
        self._pending_send = {}
        self._pending_draft_context = ""
        self._pending_refresh = False
        self._schema_refresh_pending = False
        self._follow_latest_after_history = ""
        self._pending_edits = {}
        self._pending_reactions = {}
        self._reaction_workers = {}
        self._files = {}
        self._preview_files = {}
        self._open_after_download = set()
        self._conversation_preview_files = {}
        self._download_workers = {}
        self._seen_server_messages = set()
        self._seen_server_message_order = []
        self._notification_cursors = {}
        self._notification_session = None
        application.project_changed.connect(self._project_changed)
        application.repository_sync.file_download_done.connect(
            self._attachment_downloaded
        )
        if skey_previews:
            skey_previews.previewReady.connect(self._skey_preview_ready)
            skey_previews.previewsReady.connect(self._skey_previews_ready)
        if attachments:
            attachments.uploaded.connect(self._attachments_uploaded)
            attachments.failed.connect(self._attachments_failed)
            attachments.stateChanged.connect(self.stateChanged)
        if users:
            users.contentReplaced.connect(self._sync_conversation_profiles)
        if self._clock is not None:
            self._clock.changed.connect(self._clock_changed)

    @Property(bool, notify=stateChanged)
    def busy(self):
        return (
            self._busy
            or (self._history_busy and not self._history_background)
            or bool(self.attachments and self.attachments.busy)
        )

    @Property(bool, notify=stateChanged)
    def sending(self):
        return (
            self._sending
            and self._sending_conversation_id == self._conversation_id
        )

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(bool, notify=stateChanged)
    def initialized(self):
        return self._initialized

    @Property(bool, notify=stateChanged)
    def canInitialize(self):
        return self._can_initialize

    @Property(str, notify=stateChanged)
    def projectCode(self):
        return str(
            getattr(self._application, "current_project_code", "") or ""
        )

    @Slot()
    def dismiss_error(self):
        if self._error:
            self._error = ""
            self.stateChanged.emit()

    @Property(str, notify=stateChanged)
    def conversationId(self):
        return self._conversation_id

    @Property(str, notify=draftChanged)
    def draftText(self):
        return self._composer.text

    def _composer_context(self, conversation_id=None, session=None):
        conversation_id = str(
            conversation_id
            if conversation_id is not None else self._conversation_id
        )
        if not conversation_id:
            return ""
        server, login = session or self._current_session()
        identity = "\0".join((str(server or ""), str(login or "")))
        return "{0}/{1}".format(
            hashlib.sha1(identity.encode("utf-8")).hexdigest(),
            conversation_id,
        )

    def _activate_draft_context(self, conversation_id=None, session=None):
        self._composer.activate(self._composer_context(conversation_id, session))

    @Slot(str)
    def set_draft_text(self, value):
        self._composer.set_text(value)

    @Slot()
    def shutdown(self):
        if self._settings_flush_timer.isActive():
            self._settings_flush_timer.stop()
            self._write_settings()
        self._composer.shutdown()

    @Property(bool, notify=stateChanged)
    def hasMore(self):
        return self._has_more

    @Property(int, notify=stateChanged)
    def unreadCount(self):
        return sum(int(record.get("unread") or 0) for record in self.conversations._records)

    @Property(bool, notify=notificationsEnabledChanged)
    def notificationsEnabled(self):
        return self._notifications_enabled

    @Slot(bool)
    def set_notifications_enabled(self, value):
        value = bool(value)
        if value == self._notifications_enabled:
            return
        self._notifications_enabled = value
        self._notification_preferences["notifications/enabled"] = value
        env_write_config(
            self._notification_preferences,
            filename="ui_settings",
            unique_id="ui_messages",
            long_abs_path=True,
        )
        self.notificationsEnabledChanged.emit()

    @Property(bool, notify=stateChanged)
    def canCreateGroup(self):
        return self._can_create_group

    @Property(bool, notify=stateChanged)
    def canDeleteMessages(self):
        return self._can_delete_messages or bool(
            self.selectedConversation.get("canClearPersonal")
        )

    @Property("QVariantMap", notify=stateChanged)
    def selectedConversation(self):
        return dict(next((
            record for record in self.conversations._records
            if record.get("conversationId") == self._conversation_id
        ), {}))

    @Property(str, notify=stateChanged)
    def messageSearch(self):
        return self._message_search

    @Property("QVariantMap", notify=stateChanged)
    def pinnedMessage(self):
        return dict(self._pinned_message)

    @Property("QVariantList", notify=stateChanged)
    def pinHistory(self):
        return list(self._pin_history)

    @Property("QVariantMap", notify=stateChanged)
    def replyTarget(self):
        return dict(self._reply_target)

    @Property(int, notify=stateChanged)
    def forwardSelectionCount(self):
        return len(self._forward_selection)

    @Property("QVariantList", notify=stateChanged)
    def conversationMembers(self):
        record = self.selectedConversation
        recipients = list(record.get("recipients") or [])
        names = list(record.get("recipientNames") or [])
        try:
            from thlib.environment import env_server
            current = str(env_server.get_user() or "")
        except AttributeError:
            current = ""
        logins = ([current] if current else []) + recipients
        name_by_login = dict(zip(recipients, names))
        profiles = {
            str(user.get("login") or ""): user
            for user in (self._users._records if self._users else [])
        }
        result = []
        for login in dict.fromkeys(value for value in logins if value):
            profile = profiles.get(login, {})
            display = str(
                profile.get("displayName") or name_by_login.get(login) or login
            )
            result.append({
                "login": login,
                "displayName": display,
                "avatarUrl": str(profile.get("avatarUrl") or ""),
                "initials": str(profile.get("initials") or self._initials(display)),
                "avatarColor": str(
                    profile.get("avatarColor") or user_avatar_color(login)
                ),
                "current": login == current,
            })
        return result

    @Property("QVariantList", notify=stateChanged)
    def conversationAttachments(self):
        result = []
        for row, message in enumerate(self.messages._records):
            for attachment in message.get("attachments") or []:
                record = dict(attachment)
                record.update({
                    "messageId": str(message.get("messageId") or ""),
                    "messageRow": row,
                    "sender": str(message.get("senderDisplay") or ""),
                    "timestamp": str(message.get("timePretty") or ""),
                })
                result.append(record)
        return result

    def _project_changed(self, project_code, _title):
        # projectCode is exposed through stateChanged, so the first-run
        # confirmation must follow the project selected in the shell.
        self.stateChanged.emit()

    def _run(self, callback, handler):
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(callback)
        if worker is None:
            self._busy = False
            self._error = "Server worker pool is unavailable."
            self.stateChanged.emit()
            return
        self._worker = worker
        worker.result.connect(
            lambda result: handler(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @staticmethod
    def _cache_message_mutation(result):
        from thlib import server_cache

        server_cache.invalidate_domains(("messages",), "sthpw")
        return result

    def _run_mutation(self, callback, handler):
        def operation():
            return self._cache_message_mutation(callback())

        self._run(operation, handler)

    @Slot()
    def load(self):
        if self._busy:
            self._pending_refresh = True
            return
        if self._schema_refresh_pending:
            self._schema_refresh_pending = False
            self.refresh()
            return
        self._run(_chat_data, self._conversations_ready)

    @Slot()
    def refresh(self):
        if self._busy:
            self._pending_refresh = True
            return
        self._run(lambda: _chat_data(True), self._conversations_ready)

    @Slot()
    def refresh_current(self):
        if self._conversation_id:
            self._dirty_conversations.add(self._conversation_id)
        self.refresh()

    @Slot()
    def initialize(self):
        if self._busy or not self._can_initialize:
            return
        project_code = str(
            getattr(self._application, "current_project_code", "") or ""
        )
        if not project_code:
            self._error = self.tr(
                "Select a project before initialization"
            )
            self.stateChanged.emit()
            return

        def operation():
            import thlib.tactic_classes as tc
            from thlib.ui.knowledge_api import knowledge_request

            return tc.execute_procedure_serverside(
                knowledge_request,
                {
                    "action": "initialize",
                    "project_code": project_code,
                    "identity": "",
                    "document": None,
                    "expected_revision": "",
                    "query": "",
                },
                project=project_code,
            )

        self._run(operation, self._initialization_ready)

    def _initialization_ready(self, request_id, result):
        if request_id != self._request_id:
            return
        value = (
            result[0]
            if isinstance(result, tuple) and len(result) == 1
            else result
        )
        self._initialized = bool(
            (value or {}).get("messagesInitialized", True)
        )
        self._can_initialize = False
        self._pending_refresh = True
        self._finish()
        self.schemaInitialized.emit()

    @Slot()
    def apply_schema_initialization(self):
        self._initialized = True
        self._can_initialize = False
        self.stateChanged.emit()
        if self._busy:
            self._pending_refresh = True
            return
        if self._visible:
            # Another surface may have cached the uninitialized response. The
            # first post-bootstrap read must bypass it and discover real chats.
            self.refresh()
        else:
            self._schema_refresh_pending = True

    @Slot(object)
    def apply_cache_invalidation(self, payload):
        """Drop only hot server records; drafts and UI state are user data."""
        payload = dict(payload or {})
        hard_reset = bool(payload.get("all"))
        domains = {
            str(domain) for domain in payload.get("domains") or ()
        }
        domains.update(str(domain) for domain in payload.get("sthpw") or ())
        if not (
            hard_reset
            or "messages" in domains
        ):
            return
        generation_reset = bool(hard_reset or payload.get("preferences"))
        if generation_reset and self._history_worker is not None:
            self._history_request_id = ""
            self._history_conversation_id = ""
            self._history_busy = False
            self._pending_history_load = None
            try:
                self._history_worker.cancel()
            except (AttributeError, RuntimeError):
                pass
            self._history_worker = None
        self._conversation_cache.clear()
        self._sync_message_surfaces()
        self._dirty_conversations.update(
            str(record.get("conversationId") or "")
            for record in self.conversations._records
            if record.get("conversationId")
        )

    def _conversations_ready(self, request_id, result):
        if request_id != self._request_id:
            return
        from thlib.environment import env_server

        session = (
            str(env_server.get_server() or ""),
            str(env_server.get_user() or ""),
        )
        previous_session = self._notification_session
        if session != previous_session:
            self._notification_session = session
            self._notification_cursors.clear()
            self._seen_server_messages.clear()
            self._seen_server_message_order.clear()
            if previous_session is not None:
                self._conversation_cache.clear()
                self._dirty_conversations.clear()
                self._clear_active_history()
                self._conversation_id = ""
        value = (
            result[0]
            if isinstance(result, tuple) and len(result) == 1
            else result
        )
        if isinstance(value, tuple):
            value = {"conversations": list(value[0] or [])}
        self._initialized = bool((value or {}).get("initialized", True))
        self._can_initialize = bool(
            (value or {}).get("canInitialize", False)
        )
        if not self._initialized:
            self._can_create_group = False
            self._can_delete_messages = False
            self.conversations.clear()
            self._conversation_id = ""
            self._conversation_opened = False
            self._activate_draft_context("")
            self._clear_active_history()
            self._finish()
            return
        self._can_create_group = bool((value or {}).get("canCreateGroup"))
        self._can_delete_messages = bool(
            (value or {}).get("canDeleteMessages")
        )
        records = list((value or {}).get("conversations") or [])
        records.sort(
            key=lambda record: (
                bool(record.get("isPersonalNotes")),
                str(record.get("lastTimestamp") or record.get("createdAt") or ""),
            ),
            reverse=True,
        )
        selected = self._conversation_id or self._saved_conversation(session)
        for record in records:
            conversation_id = str(record.get("conversationId") or "")
            if conversation_id and conversation_id not in self._notification_cursors:
                self._notification_cursors[conversation_id] = str(
                    record.get("lastTimestamp") or ""
                )
            self._apply_cached_history_counts(record)
            record["selected"] = record.get("conversationId") == selected
            record.update(self._conversation_profile(record))
        self.conversations.replace(records)
        self._finish()
        if selected and any(record.get("conversationId") == selected for record in records):
            switching_history = self._loaded_conversation_id != selected
            self._conversation_id = selected
            self._conversation_opened = True
            self._remember_conversation(selected, session)
            self._activate_draft_context(selected, session)
            restored = False
            if switching_history:
                restored = self._restore_cached_history(selected)
                if not restored:
                    self.conversationChanging.emit(selected)
            history_current = self._loaded_conversation_id == selected
            server_timestamp = self._conversation_timestamp(selected)
            needs_reload = (
                not history_current
                or selected in self._dirty_conversations
                or self._loaded_server_timestamp != server_timestamp
            )
            if restored:
                self.stateChanged.emit()
                self.conversationRestored.emit(selected)
                self.conversationLoaded.emit()
                if self._visible:
                    self._mark_read()
            if needs_reload:
                self._load_messages(
                    reset=True,
                    background=restored,
                    bypass_cache=selected in self._dirty_conversations,
                )
        else:
            if selected:
                self._forget_conversation(session)
            self._conversation_id = ""
            self._conversation_opened = False
            self._activate_draft_context("", session)
            self._clear_active_history()
            self.stateChanged.emit()

    @staticmethod
    def _conversation_settings_key(session):
        server, login = session
        identity = "\0".join((str(server or ""), str(login or "")))
        digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()
        return "messages/lastConversation/" + digest

    def _current_session(self):
        from thlib.environment import env_server

        return (
            str(env_server.get_server() or ""),
            str(env_server.get_user() or ""),
        )

    def _saved_conversation(self, session=None):
        key = self._conversation_settings_key(session or self._current_session())
        return str(self._settings.get(key, "") or "")

    def _remember_conversation(self, conversation_id, session=None):
        conversation_id = str(conversation_id or "")
        if not conversation_id:
            return
        key = self._conversation_settings_key(session or self._current_session())
        if self._settings.get(key, "") != conversation_id:
            self._settings[key] = conversation_id
            self._settings_flush_timer.start()

    def _forget_conversation(self, session=None):
        key = self._conversation_settings_key(session or self._current_session())
        if key in self._settings:
            self._settings.pop(key, None)
            self._settings_flush_timer.start()

    def _write_settings(self):
        env_write_config(
            self._settings,
            filename="ui_state",
            unique_id="cache/messages",
            long_abs_path=True,
        )

    def _conversation_timestamp(self, conversation_id=None):
        conversation_id = str(conversation_id or self._conversation_id)
        record = next((
            item for item in self.conversations._records
            if str(item.get("conversationId") or "") == conversation_id
        ), {})
        return str(record.get("lastTimestamp") or "")

    @staticmethod
    def _complete_history_counts(records):
        records = list(records or [])
        return {
            "messageCount": len(records),
            "attachmentCount": sum(
                len(record.get("attachments") or []) for record in records
            ),
        }

    def _reconcile_complete_history_counts(self, conversation_id, records):
        """Replace a stale chat summary once the complete history is known."""
        if self._has_more or self._message_search:
            return
        conversation_id = str(conversation_id or "")
        if not conversation_id:
            return
        counts = self._complete_history_counts(records)
        for row, record in enumerate(self.conversations._records):
            if str(record.get("conversationId") or "") != conversation_id:
                continue
            for role, value in counts.items():
                if int(record.get(role) or 0) != value:
                    self.conversations.set_value(row, role, value)
            break

    def _apply_cached_history_counts(self, record):
        conversation_id = str(record.get("conversationId") or "")
        cached = self._conversation_cache.get(conversation_id)
        if (
            not cached
            or cached.get("hasMore") is not False
            or str(cached.get("serverTimestamp") or "")
            != str(record.get("lastTimestamp") or "")
        ):
            return
        record.update(self._complete_history_counts(cached["model"]._records))

    def _cache_current_history(self):
        conversation_id = self._conversation_id
        if (
            not conversation_id
            or self._loaded_conversation_id != conversation_id
            or self._message_search
        ):
            return
        self._conversation_cache.pop(conversation_id, None)
        self._conversation_cache[conversation_id] = {
            "model": self.messages,
            "pinnedMessage": dict(self._pinned_message),
            "pinHistory": [dict(record) for record in self._pin_history],
            "replyTarget": dict(self._reply_target),
            "hasMore": self._has_more,
            "offset": self._offset,
            "files": dict(self._files),
            "previewFiles": dict(self._preview_files),
            "serverTimestamp": self._loaded_server_timestamp,
        }
        while len(self._conversation_cache) > self._conversation_cache_limit:
            self._conversation_cache.popitem(last=False)
        self._sync_message_surfaces()

    def _sync_message_surfaces(self):
        keep = {value["model"] for value in self._conversation_cache.values()}
        has_more = {
            value["model"]: bool(value["hasMore"])
            for value in self._conversation_cache.values()
        }
        has_more[self.messages] = self._has_more
        keep.add(self.messages)
        records = []
        for record in self.message_surfaces._records:
            model = record["messageModel"]
            if model in keep:
                records.append({
                    **record, "current": model is self.messages,
                    "conversationId": self._conversation_id if model is self.messages else record["conversationId"],
                    "historyHasMore": has_more[model],
                })
        if not any(row["messageModel"] is self.messages for row in records):
            records.append({
                "conversationId": self._conversation_id,
                "messageModel": self.messages, "current": True,
                "historyHasMore": self._has_more,
            })
        removed = [row["messageModel"] for row in self.message_surfaces._records
                   if row["messageModel"] not in keep]
        # Reconcile by stable model identity: an LRU eviction must not rebind
        # the surviving timelines to a different conversation.
        old = self.message_surfaces
        for row in reversed(range(old.count())):
            if old._records[row]["messageModel"] not in keep:
                old.remove(row)
        old.replace(records)
        for model in removed:
            model.deleteLater()

    def _restore_cached_history(self, conversation_id):
        cached = self._conversation_cache.pop(conversation_id, None)
        if cached is None:
            return False
        self._conversation_cache[conversation_id] = cached
        self.messages = cached["model"]
        self._refresh_message_timestamps(self.messages)
        self._pinned_message = dict(cached.get("pinnedMessage") or {})
        self._pin_history = [
            dict(record) for record in cached.get("pinHistory") or []
        ]
        self._reply_target = dict(cached.get("replyTarget") or {})
        self._has_more = bool(cached.get("hasMore"))
        self._offset = int(cached.get("offset") or 0)
        self._files = dict(cached.get("files") or {})
        self._preview_files = dict(cached.get("previewFiles") or {})
        self._loaded_conversation_id = conversation_id
        self._loaded_server_timestamp = str(
            cached.get("serverTimestamp") or ""
        )
        self._sync_message_surfaces()
        return True

    def _clear_active_history(self):
        if any(value["model"] is self.messages for value in self._conversation_cache.values()):
            self.messages = RecordListModel(self.messages._roles, identity_role="messageId")
            self.messages.setParent(self)
        else:
            self.messages.clear()
        self._pinned_message = {}
        self._pin_history = []
        self._has_more = False
        self._offset = 0
        self._files.clear()
        self._preview_files.clear()
        self._loaded_conversation_id = ""
        self._loaded_server_timestamp = ""
        self._sync_message_surfaces()

    @staticmethod
    def _initials(value):
        parts = [part for part in str(value or "").split() if part]
        return "".join(part[0] for part in parts[:2]).upper() or "?"

    def _conversation_profile(self, record):
        recipients = list(record.get("recipients") or [])
        names = list(record.get("recipientNames") or [])
        direct_peer = (
            str(recipients[0] or "")
            if len(recipients) == 1
            and not bool(record.get("isPersonalNotes"))
            else ""
        )
        profile = {}
        if direct_peer and self._users:
            profile = next((
                user for user in self._users._records
                if user.get("login") == direct_peer
            ), {})
        title = str(record.get("title") or "Chat")
        acronym = self._initials(title)
        preview_url = self._conversation_preview_url(record)
        created_pretty = self._message_timestamp(record.get("createdAt"))[0]
        active_pretty = self._message_timestamp(record.get("lastTimestamp"))[0]
        last_seen = str(profile.get("lastSeen") or "")
        last_seen_pretty = (
            self._message_timestamp(last_seen)[0] if last_seen else ""
        )
        last_message = self._message_content_preview(
            record.get("lastMessage"), empty_text=""
        )
        return {
            "avatarUrl": str(
                preview_url or profile.get("avatarUrl") or ""
            ),
            "initials": str(
                profile.get("initials") or acronym
            ),
            "participantCount": max(1, len(recipients) + 1),
            "memberSummary": ", ".join(["You"] + (names or recipients)),
            "acronym": acronym,
            "colorIndex": min(4, max(0, len(recipients))),
            "createdPretty": created_pretty,
            "activePretty": active_pretty,
            "peerLogin": direct_peer,
            "presenceKnown": bool(
                direct_peer and profile.get("presenceKnown")
            ),
            "online": bool(direct_peer and profile.get("online")),
            "lastSeen": last_seen,
            "lastSeenPretty": last_seen_pretty,
            "lastMessageSummary": last_message["summary"],
            "lastMessageLinkedCount": last_message["linkedCount"],
        }

    def _conversation_preview_url(self, record):
        snapshot_data = dict(record.get("preview") or {})
        if not snapshot_data:
            return ""
        try:
            import thlib.tactic_classes as tc

            snapshot = tc.Snapshot(snapshot_data)
            grouped = snapshot.get_files_objects(group_by="type") or {}
            files = []
            for file_type in ("icon", "web", "preview", "main"):
                files.extend(grouped.get(file_type) or [])
            file_object = files[0] if files else None
            if not file_object:
                return ""
            candidate = file_object.get_icon_preview() or file_object
            conversation_id = str(record.get("conversationId") or "")
            self._conversation_preview_files[conversation_id] = candidate
            if candidate.is_local_current():
                return QUrl.fromLocalFile(
                    str(candidate.get_full_abs_path())
                ).toString()
            if self._application.repository_sync.previews_through_http_enabled():
                self._application.repository_sync.schedule_file_object(
                    candidate, process="preview", auto_start=True,
                    is_ui_preview=True,
                )
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            return ""
        return ""

    def _sync_conversation_profiles(self):
        for row, record in enumerate(self.conversations._records):
            for role, value in self._conversation_profile(record).items():
                self.conversations.set_value(row, role, value)
        for row, record in enumerate(self.messages._records):
            for role, value in self._message_profile(record.get("sender")).items():
                self.messages.set_value(row, role, value)
            reply_to = dict(record.get("replyTo") or {})
            if reply_to and reply_to.get("sender"):
                reply_profile = self._message_profile(reply_to.get("sender"))
                reply_to["senderDisplay"] = str(
                    reply_profile.get("senderDisplay")
                    or reply_to.get("sender") or ""
                )
                self.messages.set_value(row, "replyTo", reply_to)
            self.messages.set_value(
                row, "displayHtml", self._message_display_html(record.get("body"))
            )
            reaction_values = {
                str(item.get("emoji") or ""): list(item.get("logins") or [])
                for item in (record.get("reactions") or [])
                if item.get("emoji")
            }
            self.messages.set_value(
                row, "reactions", self._reaction_records(reaction_values)
            )
        self.stateChanged.emit()

    def _message_profile(self, login):
        profile = {}
        if self._users:
            profile = next((
                user for user in self._users._records
                if str(user.get("login") or "") == str(login or "")
            ), {})
        display_name = str(profile.get("displayName") or login or "Removed user")
        return {
            "senderDisplay": display_name,
            "avatarUrl": str(profile.get("avatarUrl") or ""),
            "initials": str(profile.get("initials") or self._initials(display_name)),
            "senderColor": str(
                profile.get("avatarColor") or user_avatar_color(login)
            ),
        }

    @staticmethod
    def _delivery_record(value):
        delivery = dict(value or {})
        recipients = dict(delivery.get("recipients") or {})
        recipient_count = int(
            delivery.get("recipientCount") or len(recipients)
        )
        delivered_count = int(delivery.get("deliveredCount") or len([
            receipt for receipt in recipients.values()
            if receipt.get("deliveredAt")
        ]))
        read_count = int(delivery.get("readCount") or len([
            receipt for receipt in recipients.values()
            if receipt.get("readAt")
        ]))
        status = str(delivery.get("status") or "")
        if not status:
            if recipient_count and read_count == recipient_count:
                status = "read"
            elif recipient_count and delivered_count == recipient_count:
                status = "delivered"
            else:
                status = "sent"
        return {
            "deliveryStatus": status,
            "deliveryRecipientCount": recipient_count,
            "deliveryDeliveredCount": delivered_count,
            "deliveryReadCount": read_count,
        }

    def _reaction_records(self, value):
        from thlib.environment import env_server

        current = str(env_server.get_user() or "")
        profiles = {
            str(record.get("login") or ""): str(
                record.get("displayName") or record.get("login") or ""
            )
            for record in (self._users._records if self._users else [])
        }
        records = []
        for emoji, reaction_logins in dict(value or {}).items():
            logins = list(dict.fromkeys(
                str(login) for login in (reaction_logins or []) if login
            ))
            if not logins:
                continue
            display_names = [profiles.get(login, login) for login in logins]
            records.append({
                "emoji": str(emoji),
                "count": len(logins),
                "reactedByMe": current in logins,
                "logins": logins,
                "displayNames": display_names,
                "namesText": ", ".join(display_names),
            })
        return records

    def _optimistic_reactions(self, records, emoji):
        from thlib.environment import env_server

        current = str(env_server.get_user() or "")
        values = {
            str(record.get("emoji") or ""): list(record.get("logins") or [])
            for record in (records or []) if record.get("emoji")
        }
        logins = values.setdefault(str(emoji), [])
        if current in logins:
            logins.remove(current)
            if not logins:
                values.pop(str(emoji), None)
        else:
            logins.append(current)
        return self._reaction_records(values)

    @staticmethod
    def _message_content_preview(body, attachment_count=0, has_reply=False,
                                 forwarded=False, empty_text="Message"):
        body = str(body or "")
        links = extract_skeys(body)
        summary = body
        for search_key in links:
            summary = summary.replace(search_key, " ")
        summary = " ".join(summary.split()).strip(" ·,;:-|")
        message_links = sum(
            1 for search_key in links if "/message_log?" in search_key
        )
        if not summary:
            if links and message_links == len(links):
                summary = "Linked messages"
            elif links:
                summary = "Linked TACTIC items"
            elif attachment_count:
                summary = "Attached files"
            elif forwarded:
                summary = "Forwarded message"
            elif has_reply:
                summary = "Reply"
            else:
                summary = empty_text
        return {
            "summary": summary,
            "linkedCount": len(links),
            "linkedMessageCount": message_links,
            "attachmentCount": int(attachment_count or 0),
            "hasReply": bool(has_reply),
            "forwarded": bool(forwarded),
        }

    def _pin_preview(self, value, messages=()):
        record = dict(value or {})
        identity = _message_identity(record.get("messageId"))
        message = next((
            item for item in messages
            if _message_identity(item.get("messageId")) == identity
        ), {})
        body = str(message.get("body") or record.get("body") or "")
        content = self._message_content_preview(
            body,
            attachment_count=(
                message.get("attachmentCount")
                or len(message.get("attachments") or [])
            ),
            has_reply=bool(message.get("replyTo")),
            forwarded=bool(message.get("forwardedFrom")),
            empty_text="Pinned message",
        )
        sender = str(message.get("sender") or record.get("sender") or "")
        record.update(
            content,
            sender=sender,
            senderDisplay=str(
                message.get("senderDisplay")
                or self._message_profile(sender).get("senderDisplay") or sender
            ),
        )
        return record

    def _message_timestamp(self, timestamp):
        if self._clock is not None:
            pretty, full = activity_timestamp_labels(
                timestamp, self._clock
            )
            if pretty or full:
                return pretty, full
        try:
            import thlib.global_functions as gf
            value = gf.parce_timestamp(str(timestamp or ""))
            return (
                str(gf.get_pretty_datetime(value)),
                str(gf.get_full_datetime(value)),
            )
        except (AttributeError, TypeError, ValueError):
            value = str(timestamp or "")
            return value, value

    def _refresh_message_timestamps(self, model):
        records = []
        changed = False
        for source in model._records:
            record = dict(source)
            pretty, full = self._message_timestamp(record.get("timestamp"))
            if (
                record.get("timePretty") != pretty
                or record.get("timeSimple") != full
            ):
                record["timePretty"] = pretty
                record["timeSimple"] = full
                changed = True
            records.append(record)
        if changed:
            model.replace(records)
        return changed

    def _refresh_timestamp_presentation(self):
        conversations = []
        conversations_changed = False
        for source in self.conversations._records:
            record = dict(source)
            values = {
                "createdPretty": self._message_timestamp(
                    record.get("createdAt")
                )[0],
                "activePretty": self._message_timestamp(
                    record.get("lastTimestamp")
                )[0],
                "lastSeenPretty": (
                    self._message_timestamp(record.get("lastSeen"))[0]
                    if record.get("lastSeen") else ""
                ),
            }
            if any(record.get(role) != value for role, value in values.items()):
                record.update(values)
                conversations_changed = True
            conversations.append(record)
        if conversations_changed:
            self.conversations.replace(conversations)
        messages_changed = self._refresh_message_timestamps(self.messages)
        self._timestamp_presentation_dirty = False
        if conversations_changed or messages_changed:
            self.stateChanged.emit()

    def _clock_changed(self):
        self._timestamp_presentation_dirty = True
        if self._visible:
            self._refresh_timestamp_presentation()

    @Slot(int)
    @measure_ui("Messages: switch conversation")
    def select_conversation(self, row):
        record = self.conversations.get(row)
        conversation_id = str(record.get("conversationId") or "")
        if not conversation_id:
            return
        if (
            conversation_id == self._conversation_id
            and (
                self._loaded_conversation_id == conversation_id
                or (
                    self._history_busy
                    and self._history_conversation_id == conversation_id
                )
            )
        ):
            return
        self._cache_current_history()
        self._conversation_id = conversation_id
        self._conversation_opened = True
        self._remember_conversation(conversation_id)
        self._activate_draft_context(conversation_id)
        self._message_search = ""
        self._pending_message_focus = ""
        self.conversations.select_row(row)
        self._pinned_message = {}
        self._pin_history = []
        self._reply_target = {}
        restored = self._restore_cached_history(conversation_id)
        if not restored:
            self.conversationChanging.emit(conversation_id)
            self._clear_active_history()
        self.stateChanged.emit()
        needs_reload = (
            not restored
            or conversation_id in self._dirty_conversations
            or self._loaded_server_timestamp
                != str(record.get("lastTimestamp") or "")
        )
        if restored:
            self.conversationRestored.emit(conversation_id)
            self.conversationLoaded.emit()
            if self._visible:
                self._mark_read()
        if needs_reload:
            self._load_messages(reset=True, background=restored)

    @Slot(str)
    def open_conversation(self, conversation_id):
        conversation_id = str(conversation_id or "")
        if not conversation_id:
            return
        self._application.window_model.show_window("messages")
        row = next((
            index for index, record in enumerate(self.conversations._records)
            if record.get("conversationId") == conversation_id
        ), -1)
        if row >= 0:
            self.select_conversation(row)
        else:
            self._cache_current_history()
            self.conversationChanging.emit(conversation_id)
            self._conversation_id = conversation_id
            self._conversation_opened = True
            self._activate_draft_context(conversation_id)
            self._clear_active_history()
            self.stateChanged.emit()
            if not self._busy:
                self.refresh()
            else:
                self._pending_refresh = True

    @Slot(str, result=bool)
    def open_direct_conversation(self, login):
        login = str(login or "").strip()
        if not login or self._busy:
            return False
        self._application.window_model.show_window("messages")
        conversation_id = next((
            str(record.get("conversationId") or "")
            for record in self.conversations._records
            if (
                not record.get("isPersonalNotes")
                and list(record.get("recipients") or []) == [login]
            )
        ), "")
        if conversation_id:
            self.open_conversation(conversation_id)
            return True
        # The native server operation also checks the participant set, so an
        # unloaded direct conversation is returned instead of duplicated.
        return self.create_conversation([login])

    @Slot("QVariantList", result=bool)
    @Slot("QVariantList", str, result=bool)
    def create_conversation(self, recipients, title=""):
        recipients = [str(value or "").strip() for value in recipients or []]
        recipients = [value for value in recipients if value]
        title = str(title or "").strip()
        if self._busy or not recipients or (len(recipients) > 1 and not title):
            return False

        def operation():
            import thlib.tactic_classes as tc
            return tc.create_chat_conversation(recipients, title=title)

        self._run_mutation(operation, self._conversation_created)
        return True

    @Slot(str, result=bool)
    def rename_conversation(self, title):
        title = str(title or "").strip()
        record = self.selectedConversation
        if self._busy or not title or not record.get("canRename"):
            return False
        conversation_id = self._conversation_id

        def operation():
            import thlib.tactic_classes as tc
            return tc.update_chat_conversation(conversation_id, title)

        self._run_mutation(operation, self._chat_updated)
        return True

    @Slot("QVariantList", result=bool)
    def add_members(self, recipients):
        recipients = [str(value or "").strip() for value in recipients or []]
        recipients = [value for value in recipients if value]
        record = self.selectedConversation
        if self._busy or not recipients or not record.get("canAddMembers"):
            return False
        conversation_id = self._conversation_id

        def operation():
            import thlib.tactic_classes as tc
            return tc.add_chat_members(conversation_id, recipients)

        self._run_mutation(operation, self._chat_updated)
        return True

    @Slot("QVariantList", result=bool)
    def set_members(self, recipients):
        recipients = [str(value or "").strip() for value in recipients or []]
        recipients = list(dict.fromkeys(value for value in recipients if value))
        record = self.selectedConversation
        if self._busy or not recipients or not record.get("canAddMembers"):
            return False
        conversation_id = self._conversation_id

        def operation():
            import thlib.tactic_classes as tc
            return tc.set_chat_members(conversation_id, recipients)

        self._run_mutation(operation, self._chat_updated)
        return True

    @Slot(result=bool)
    def delete_conversation(self):
        record = self.selectedConversation
        if self._busy or not record.get("canDelete"):
            return False
        conversation_id = self._conversation_id

        def operation():
            import thlib.tactic_classes as tc
            return tc.delete_chat_conversation(conversation_id)

        self._run_mutation(operation, self._chat_deleted)
        return True

    @Slot(result=bool)
    def clear_personal_chat(self):
        record = self.selectedConversation
        if self._busy or not record.get("canClearPersonal"):
            return False
        conversation_id = self._conversation_id

        def operation():
            import thlib.tactic_classes as tc
            return tc.clear_personal_chat(conversation_id)

        self._run_mutation(operation, self._chat_updated)
        return True

    @Slot(str, result=bool)
    def delete_message(self, message_id):
        message_id = str(message_id or "")
        can_delete = self._can_delete_messages or bool(
            self.selectedConversation.get("canClearPersonal")
        )
        if self._busy or not can_delete or not message_id:
            return False

        def operation():
            import thlib.tactic_classes as tc
            return tc.delete_chat_message(message_id)

        self._run_mutation(operation, self._chat_updated)
        return True

    @Slot(str, str, result=bool)
    def edit_message(self, message_id, message):
        message_id = str(message_id or "")
        message = str(message or "").strip()
        record = next((
            item for item in self.messages._records
            if item.get("messageId") == message_id
        ), {})
        if self._busy or not message or not record.get("canEdit"):
            return False
        original_body = str(record.get("body") or "")
        edit_history = list(record.get("editHistory") or [])

        def operation():
            import thlib.tactic_classes as tc
            return tc.edit_chat_message(message_id, message)

        self._run_mutation(
            operation,
            lambda request_id, result: self._message_edited(
                request_id, result, message_id, message,
                original_body, edit_history,
            ),
        )
        return True

    def _message_edited(
        self, request_id, result, message_id, message,
        original_body, previous_history,
    ):
        if request_id != self._request_id:
            return
        value = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        value = dict(value or {})
        if not value.get("edited"):
            self._finish()
            return
        history = list(value.get("editHistory") or previous_history)
        if len(history) <= len(previous_history):
            history.append({
                "body": original_body,
                "editedBy": str(value.get("editedBy") or ""),
                "editedAt": str(value.get("editedAt") or ""),
            })
        pending = {
            "body": message,
            "history": history,
            "editedBy": str(value.get("editedBy") or ""),
            "editedAt": str(value.get("editedAt") or ""),
        }
        self._pending_edits[_message_identity(message_id)] = pending
        if _message_identity(self._pinned_message.get("messageId")) == _message_identity(
            message_id
        ):
            self._pinned_message["body"] = message
        row = self.message_index(message_id)
        if row >= 0:
            for role, role_value in (
                ("body", message),
                ("bodyHtml", self._display_html(message)),
                ("displayHtml", self._message_display_html(message)),
                ("skeyPreviews", self._preview_records(message)),
                ("edited", True),
                ("editedBy", pending["editedBy"]),
                ("editedAt", pending["editedAt"]),
                ("editHistory", history),
            ):
                self.messages.set_value(row, role, role_value)
            if row == self.messages.count - 1:
                for conversation_row, conversation in enumerate(
                        self.conversations._records):
                    if conversation.get("conversationId") == self._conversation_id:
                        self.conversations.set_value(
                            conversation_row, "lastMessage", message
                        )
                        break
            self._cache_current_history()
        self._finish()

    @Slot(str, str, result=bool)
    def toggle_reaction(self, message_id, emoji):
        message_id = str(message_id or "")
        emoji = str(emoji or "").strip()
        identity = _message_identity(message_id)
        row = self.message_index(message_id)
        if not identity or not emoji or row < 0 or identity in self._pending_reactions:
            return False
        record = self.messages.get(row)
        previous = [dict(value) for value in (record.get("reactions") or [])]
        optimistic = self._optimistic_reactions(previous, emoji)
        self._pending_reactions[identity] = optimistic
        self.messages.set_value(row, "reactions", optimistic)
        self.messages.set_value(row, "reactionPending", True)

        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()

        def operation():
            import thlib.tactic_classes as tc
            return self._cache_message_mutation(
                tc.toggle_chat_message_reaction(message_id, emoji)
            )

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._pending_reactions.pop(identity, None)
            self.messages.set_value(row, "reactions", previous)
            self.messages.set_value(row, "reactionPending", False)
            self._error = "Server worker pool is unavailable."
            self.stateChanged.emit()
            return False
        request_id = uuid.uuid4().hex
        self._reaction_workers[identity] = (request_id, worker, previous)
        worker.result.connect(
            lambda result: self._reaction_ready(identity, request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._reaction_failed(identity, request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        return True

    def _reaction_ready(self, identity, request_id, result):
        pending = self._reaction_workers.get(identity)
        if not pending or pending[0] != request_id:
            return
        value = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        reactions = self._reaction_records((value or {}).get("reactions") or {})
        self._reaction_workers.pop(identity, None)
        self._pending_reactions.pop(identity, None)
        row = self.message_index(identity)
        if row >= 0:
            self.messages.set_value(row, "reactions", reactions)
            self.messages.set_value(row, "reactionPending", False)
        self.stateChanged.emit()

    def _reaction_failed(self, identity, request_id, error):
        pending = self._reaction_workers.get(identity)
        if not pending or pending[0] != request_id:
            return
        previous = pending[2]
        self._reaction_workers.pop(identity, None)
        self._pending_reactions.pop(identity, None)
        row = self.message_index(identity)
        if row >= 0:
            self.messages.set_value(row, "reactions", previous)
            self.messages.set_value(row, "reactionPending", False)
        self._error, stacktrace = _worker_error(error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                self._error,
                stacktrace=stacktrace,
                group="communication/message-reactions",
            )
        self.stateChanged.emit()

    @Slot(str, result=bool)
    def pin_message(self, message_id):
        message_id = str(message_id or "")
        if self._busy or not message_id or not self._conversation_id:
            return False

        def operation():
            import thlib.tactic_classes as tc
            return tc.pin_chat_message(message_id)

        self._run_mutation(operation, self._chat_updated)
        return True

    @Slot(str, result=bool)
    def unpin_message(self, message_id):
        message_id = str(message_id or "")
        if self._busy or not message_id or not self._conversation_id:
            return False
        if _message_identity(self._pinned_message.get("messageId")) != _message_identity(
            message_id
        ):
            return False

        def operation():
            import thlib.tactic_classes as tc
            return tc.unpin_chat_message(message_id)

        self._run_mutation(operation, self._chat_updated)
        return True

    @Slot(QUrl, result=bool)
    def set_conversation_preview(self, value):
        record = self.selectedConversation
        if self._busy or not record.get("canManage"):
            return False
        path = Path(value.toLocalFile() if value.isLocalFile() else value.toString())
        try:
            path = path.resolve(strict=True)
        except OSError:
            self._error = "Preview file does not exist"
            self.stateChanged.emit()
            return False
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            self._error = "Choose a JPG, PNG, or WEBP image"
            self.stateChanged.emit()
            return False
        from thlib.environment import env_inst, env_tactic
        from .message_attachments import ChatAttachmentController
        from thlib.checkin_operation import execute_checkin_payload

        repository = env_tactic.get_current_repo() or {}
        values = repository.get("value") or []
        if len(values) < 4 or not values[0]:
            self._error = "No active repository is configured"
            self.stateChanged.emit()
            return False
        request_id = uuid.uuid4().hex
        payload = ChatAttachmentController._payload(
            self._conversation_id,
            {
                "path": str(path),
                "fileType": "preview",
                "title": path.name,
            },
            request_id,
        )
        payload.update({
            "context": "icon",
            "description": "Chat preview",
            "updateVersionless": True,
        })
        if env_inst.commit_pool.is_stopped:
            env_inst.commit_pool.start()
        self._request_id = request_id
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        worker = env_inst.commit_pool.add_task(
            execute_checkin_payload, payload, repository
        )
        if worker is None:
            self._busy = False
            self._error = "Check-in worker pool is unavailable"
            self.stateChanged.emit()
            return False
        self._worker = worker
        worker.result.connect(
            lambda result: self._preview_updated(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()
        return True

    def _chat_updated(self, request_id, _result):
        if request_id != self._request_id:
            return
        if self._conversation_id:
            self._dirty_conversations.add(self._conversation_id)
        self._finish()
        self.refresh()

    def _chat_deleted(self, request_id, _result):
        if request_id != self._request_id:
            return
        deleted_id = self._conversation_id
        deleted_draft_context = self._composer.context
        self._conversation_id = ""
        self._conversation_opened = False
        self._activate_draft_context("")
        self._composer.clear(deleted_draft_context)
        self._conversation_cache.pop(deleted_id, None)
        self._dirty_conversations.discard(deleted_id)
        self._clear_active_history()
        self._finish()
        self.refresh()

    def _preview_updated(self, request_id, _result):
        if request_id != self._request_id:
            return
        self._finish()
        self.refresh()

    def _conversation_created(self, request_id, result):
        if request_id != self._request_id:
            return
        value = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        self._conversation_id = str((value or {}).get("conversationId") or "")
        self._conversation_opened = bool(self._conversation_id)
        self._remember_conversation(self._conversation_id)
        self._activate_draft_context(self._conversation_id)
        self._finish()
        self.refresh()

    def _load_messages(
            self, reset=False, background=False, bypass_cache=False):
        if not self._conversation_id:
            return
        conversation_id = self._conversation_id
        if self._history_busy:
            if self._history_conversation_id != conversation_id:
                self._pending_history_load = (
                    conversation_id, bool(reset), bool(background),
                    bool(bypass_cache),
                )
            return
        offset = 0 if reset else self._offset
        page_size = self._page_size
        search_text = self._message_search

        def operation():
            import json
            from thlib import server_cache
            import thlib.tactic_classes as tc

            cache_key = json.dumps(
                {
                    "conversation": conversation_id,
                    "offset": offset,
                    "limit": page_size + 1,
                    "search": search_text,
                },
                ensure_ascii=False, separators=(",", ":"), sort_keys=True,
            )
            if bypass_cache:
                server_cache.invalidate_domains(("messages",), "sthpw")
            cache_token = server_cache.token("messages", "sthpw")
            cached = None if bypass_cache else server_cache.read_entry(
                "messages", cache_key, "sthpw",
            )
            if isinstance(cached, dict):
                return cached
            result = tc.get_chat_history(
                conversation_id, limit=page_size + 1, offset=offset,
                search_text=search_text,
            )
            if cache_token is not None and isinstance(result, dict):
                server_cache.write_entry(
                    "messages", cache_key, result, "sthpw",
                    expected_token=cache_token,
                )
            return result

        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        self._history_request_id = request_id
        self._history_conversation_id = conversation_id
        self._history_busy = True
        self._history_background = bool(background)
        self._error = ""
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            self._history_busy = False
            self._history_background = False
            self._error = "Server worker pool is unavailable."
            self.stateChanged.emit()
            return
        self._history_worker = worker
        worker.result.connect(
            lambda result: self._messages_ready(
                request_id, result, reset, offset, conversation_id
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._history_failed(
                request_id, conversation_id, error
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot()
    def load_more(self):
        if self._has_more:
            self._load_messages(reset=False)

    @Slot(str)
    def search_messages(self, value):
        value = str(value or "").strip()
        if self.busy or value == self._message_search:
            return
        self._message_search = value
        self._clear_active_history()
        self.stateChanged.emit()
        self._load_messages(reset=True)

    @Slot(str, result=int)
    def message_index(self, message_id):
        message_id = _message_identity(message_id)
        return next((
            row for row, record in enumerate(self.messages._records)
            if _message_identity(record.get("messageId")) == message_id
        ), -1)

    @Slot(str, result=bool)
    def copy_message_skey(self, message_id):
        selected = [
            _message_skey(record.get("messageId"))
            for record in self.messages._records
            if _message_identity(record.get("messageId"))
            in self._forward_selection
        ]
        values = [value for value in selected if value]
        if not values:
            value = _message_skey(message_id)
            values = [value] if value else []
        if not values:
            return False
        from PySide6.QtGui import QGuiApplication

        QGuiApplication.clipboard().setText("\n".join(values))
        return True

    @Slot(str, result=bool)
    def show_message(self, message_id):
        message_id = str(message_id or "")
        if not message_id or not self._conversation_id:
            return False
        self._pending_message_focus = message_id
        row = self.message_index(message_id)
        if row >= 0:
            self._pending_message_focus = ""
            self.messageFocusRequested.emit(message_id)
            return True
        if self._message_search:
            self._message_search = ""
            self.messages.clear()
            self._files.clear()
            self._preview_files.clear()
            self.stateChanged.emit()
            if not self._history_busy:
                self._load_messages(reset=True)
            return True
        if not self._history_busy and self._has_more:
            self._load_messages(reset=False)
        return True

    @Slot(str, str, result=bool)
    def open_forwarded_message(self, conversation_id, message_id):
        conversation_id = str(conversation_id or "")
        message_id = str(message_id or "")
        if not conversation_id or not message_id:
            return False
        self._application.window_model.show_window("messages")
        if self._conversation_id == conversation_id:
            row = self.message_index(message_id)
            if row >= 0:
                self._pending_message_focus = ""
                self.messageFocusRequested.emit(message_id)
                return True
            self._pending_message_focus = message_id
            if not self._history_busy and self._has_more:
                self._load_messages(reset=False)
            return True
        self.open_conversation(conversation_id)
        if self._conversation_id != conversation_id:
            return False
        self._pending_message_focus = message_id
        if self.message_index(message_id) >= 0:
            self._pending_message_focus = ""
            self.messageFocusRequested.emit(message_id)
        return True

    @Slot(str, result=bool)
    def begin_reply(self, message_id):
        row = self.message_index(message_id)
        if row < 0:
            return False
        record = self.messages.get(row)
        self._reply_target = {
            "messageId": str(record.get("messageId") or ""),
            "sender": str(record.get("sender") or ""),
            "senderDisplay": str(record.get("senderDisplay") or ""),
            "body": str(record.get("body") or ""),
        }
        self.stateChanged.emit()
        self.replyStarted.emit()
        return True

    @Slot()
    def cancel_reply(self):
        if self._reply_target:
            self._reply_target = {}
            self.stateChanged.emit()

    def _set_forward_selected(self, message_id, selected):
        identity = _message_identity(message_id)
        if not identity:
            return False
        if selected:
            self._forward_selection.add(identity)
        else:
            self._forward_selection.discard(identity)
        row = self.message_index(message_id)
        if row >= 0:
            self.messages.set_value(row, "forwardSelected", bool(selected))
        self.stateChanged.emit()
        return True

    @Slot(str, result=bool)
    def begin_forward(self, message_id):
        if self._busy or self.message_index(message_id) < 0:
            return False
        self.clear_forward_selection()
        self._set_forward_selected(message_id, True)
        self.forwardStarted.emit()
        return True

    @Slot(str, result=bool)
    def toggle_forward_selection(self, message_id):
        if self._busy or self.message_index(message_id) < 0:
            return False
        identity = _message_identity(message_id)
        return self._set_forward_selected(
            message_id, identity not in self._forward_selection
        )

    @Slot()
    def clear_forward_selection(self):
        if not self._forward_selection:
            return
        self._forward_selection.clear()
        for row, record in enumerate(self.messages._records):
            if record.get("forwardSelected"):
                self.messages.set_value(row, "forwardSelected", False)
        self.stateChanged.emit()

    @Slot(result=bool)
    def request_forward(self):
        if self._busy or not self._forward_selection:
            return False
        self.forwardStarted.emit()
        return True

    @Slot("QVariantList", result=bool)
    def forward_messages(self, conversation_ids):
        targets = list(dict.fromkeys(
            str(value or "").strip() for value in (conversation_ids or [])
            if str(value or "").strip()
        ))
        selected = [
            str(record.get("messageId") or "")
            for record in self.messages._records
            if _message_identity(record.get("messageId")) in self._forward_selection
        ]
        if self._busy or not selected or not targets:
            return False

        def operation():
            import thlib.tactic_classes as tc
            return tc.forward_chat_messages(selected, targets)

        self._run_mutation(operation, self._messages_forwarded)
        return True

    def _messages_forwarded(self, request_id, _result):
        if request_id != self._request_id:
            return
        self.clear_forward_selection()
        self._finish()
        self.refresh()

    @classmethod
    def _display_html(cls, value):
        return linkify_plain_text(value)

    def _message_display_html(self, value):
        logins = [
            record.get("login") for record in self._users._records
        ] if self._users else []
        return _link_user_mentions(
            display_html_without_skeys(value), logins
        )

    def _preview_records(self, value):
        if not self._skey_previews:
            return []
        return self._skey_previews.records_for_text(value)

    @Slot(str, object)
    def _skey_preview_ready(self, search_key, descriptor):
        self._apply_skey_previews({search_key: dict(descriptor or {})})

    @Slot(object)
    def _skey_previews_ready(self, descriptors):
        self._apply_skey_previews({
            str(item.get("searchKey") or ""): dict(item)
            for item in descriptors or []
            if item.get("searchKey")
        })

    def _apply_skey_previews(self, descriptors):
        if not descriptors:
            return
        changed = False
        for row, record in enumerate(self.messages._records):
            previews = [dict(item) for item in record.get("skeyPreviews") or []]
            row_changed = False
            for index, item in enumerate(previews):
                descriptor = descriptors.get(str(item.get("searchKey") or ""))
                if descriptor is not None:
                    previews[index] = descriptor
                    row_changed = True
            if row_changed:
                self.messages.set_value(row, "skeyPreviews", previews)
                changed = True
        if changed:
            self.stateChanged.emit()

    @Slot(str)
    def open_skey_preview(self, search_key):
        if self._skey_previews:
            self._skey_previews.open(search_key)
        else:
            self._application.open_search_key(search_key)

    @Slot(str)
    def copy_skey_preview(self, search_key):
        if self._skey_previews:
            self._skey_previews.copy(search_key)

    @Slot(str)
    def retry_skey_preview(self, search_key):
        if self._skey_previews:
            self._skey_previews.retry(search_key)

    def _attachment_records(self, snapshots):
        import thlib.tactic_classes as tc

        records = []
        for snapshot_data in snapshots or []:
            try:
                snapshot = tc.Snapshot(dict(snapshot_data))
            except (KeyError, TypeError, ValueError):
                continue
            files = [
                file_object for file_object in snapshot.get_files_objects() or []
                if file_object.get_type() not in {"web", "icon"}
            ]
            for file_object in files:
                token = uuid.uuid4().hex
                self._files[token] = file_object
                preview_object = file_object.get_web_preview()
                if not preview_object and file_object.is_previewable():
                    preview_object = file_object
                if preview_object:
                    self._preview_files[token] = preview_object
                preview_url = ""
                if preview_object:
                    try:
                        if preview_object.is_local_current():
                            preview_url = QUrl.fromLocalFile(
                                str(preview_object.get_full_abs_path())
                            ).toString()
                        elif self._application.repository_sync.previews_through_http_enabled():
                            self._application.repository_sync.schedule_file_object(
                                preview_object, process="attachment", auto_start=True,
                                is_ui_preview=True,
                            )
                    except (AttributeError, OSError, RuntimeError, ValueError):
                        preview_url = ""
                records.append({
                    "token": token,
                    "title": str(file_object.get_filename_with_ext() or "File"),
                    "size": int(file_object.get_file_size() or 0),
                    "extension": str(file_object.get_ext() or "").upper(),
                    "previewUrl": preview_url,
                    "local": bool(file_object.is_exists()),
                    "snapshotCode": str(snapshot.get_code() or ""),
                })
        return records

    def _message_record(self, info, last_cleared, current):
        sender = str(info.get("login") or "")
        timestamp = str(info.get("timestamp") or "")
        attachments = self._attachment_records(info.get("__attachments__") or [])
        time_pretty, time_simple = self._message_timestamp(timestamp)
        message_id = str(
            info.get("__search_key__")
            or info.get("code")
            or ""
        )
        edit_history = list(info.get("__edit_history__") or [])
        body = str(info.get("message") or "")
        pending_key = _message_identity(message_id)
        pending = self._pending_edits.get(pending_key)
        if pending:
            pending_history = list(pending.get("history") or [])
            if len(edit_history) >= len(pending_history):
                self._pending_edits.pop(pending_key, None)
            else:
                edit_history = pending_history
                body = str(pending.get("body") or body)
        reactions = self._reaction_records(info.get("__reactions__") or {})
        pending_reactions = self._pending_reactions.get(pending_key)
        if pending_reactions is not None:
            reactions = list(pending_reactions)
        last_edit = edit_history[-1] if edit_history else {}
        reply_to = dict(info.get("__reply__") or {})
        if reply_to:
            reply_profile = self._message_profile(reply_to.get("sender"))
            reply_to["senderDisplay"] = str(
                reply_profile.get("senderDisplay") or reply_to.get("sender") or ""
            )
            if not reply_to.get("available"):
                reply_to["body"] = "Original message is unavailable"
        forwarded_from = dict(info.get("__forwarded_from__") or {})
        if forwarded_from:
            forward_profile = self._message_profile(forwarded_from.get("sender"))
            forwarded_from["senderDisplay"] = str(
                forward_profile.get("senderDisplay")
                or forwarded_from.get("sender") or ""
            )
            forwarded_from["attachments"] = self._attachment_records(
                forwarded_from.get("attachments") or []
            )
            if not forwarded_from.get("available"):
                forwarded_from["body"] = "Original message is unavailable"
        record = {
            "messageId": message_id,
            "sender": sender,
            "body": body,
            "bodyHtml": self._display_html(body),
            "displayHtml": self._message_display_html(body),
            "skeyPreviews": self._preview_records(body),
            "timestamp": timestamp,
            "isOwn": sender == current,
            "unread": bool(
                sender != current
                and (
                    not str(last_cleared or "")[:19]
                    or timestamp[:19] > str(last_cleared or "")[:19]
                )
            ),
            "attachments": attachments,
            "attachmentCount": len(attachments),
            "timePretty": time_pretty,
            "timeSimple": time_simple,
            "canEdit": sender == current or self._can_delete_messages,
            "edited": bool(edit_history),
            "editedBy": str(last_edit.get("editedBy") or ""),
            "editedAt": str(last_edit.get("editedAt") or ""),
            "editHistory": edit_history,
            "pinned": _message_identity(
                self._pinned_message.get("messageId")
            ) == _message_identity(message_id),
            "replyTo": reply_to,
            "forwardedFrom": forwarded_from,
            "forwardSelected": pending_key in self._forward_selection,
            "reactions": reactions,
            "reactionPending": pending_reactions is not None,
        }
        record.update(self._delivery_record(info.get("__delivery__") or {}))
        record.update(self._message_profile(sender))
        return record

    @staticmethod
    def _message_epoch(value):
        text = str(value or "").strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is not None:
            return parsed.timestamp()
        return (parsed - datetime(1970, 1, 1)).total_seconds()

    @classmethod
    def _messages_share_visual_group(cls, first, second):
        first_sender = str((first or {}).get("sender") or "").strip()
        second_sender = str((second or {}).get("sender") or "").strip()
        if (
            not first_sender
            or first_sender.casefold() != second_sender.casefold()
        ):
            return False
        first_time = cls._message_epoch((first or {}).get("timestamp"))
        second_time = cls._message_epoch((second or {}).get("timestamp"))
        if first_time is None or second_time is None:
            return True
        return abs(second_time - first_time) <= cls.MESSAGE_GROUP_WINDOW_SECONDS

    @classmethod
    def _group_message_records(cls, records):
        grouped = [dict(record) for record in (records or [])]
        for index, record in enumerate(grouped):
            previous = grouped[index - 1] if index > 0 else None
            following = grouped[index + 1] if index + 1 < len(grouped) else None
            record["groupFirst"] = not cls._messages_share_visual_group(
                previous, record
            )
            record["groupLast"] = not cls._messages_share_visual_group(
                record, following
            )
        return grouped

    @measure_ui("Messages: publish history")
    def _messages_ready(
        self, request_id, result, reset, offset, conversation_id
    ):
        if request_id != self._history_request_id:
            return
        if conversation_id != self._conversation_id:
            self._finish_history()
            return
        from thlib.environment import env_server

        value = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        rows = list((value or {}).get("messages") or [])
        self._pinned_message = dict((value or {}).get("pinnedMessage") or {})
        pin_history = list((value or {}).get("pinHistory") or [])
        self._has_more = len(rows) > self._page_size
        rows = rows[:self._page_size]
        last_cleared = ""
        for record in self.conversations._records:
            if record.get("conversationId") == self._conversation_id:
                last_cleared = str(record.get("lastCleared") or "")
                break
        current = str(env_server.get_user() or "")
        records = [
            self._message_record(info, last_cleared, current)
            for info in reversed(rows)
        ]
        existing = [] if reset else list(self.messages._records)
        preview_messages = records + existing
        self._pinned_message = self._pin_preview(
            self._pinned_message, preview_messages
        )
        self._pin_history = [
            self._pin_preview(item, preview_messages)
            for item in pin_history
        ]
        history_records = self._group_message_records(records + existing)
        if reset and self._loaded_conversation_id != conversation_id:
            self.messages.reset_records(history_records)
        else:
            self.messages.replace(history_records)
        self._reconcile_complete_history_counts(
            conversation_id, history_records
        )
        follow_latest = (
            self._follow_latest_after_history == conversation_id
        )
        if follow_latest:
            self._follow_latest_after_history = ""
        self._offset = offset + len(rows)
        self._loaded_conversation_id = conversation_id
        self._loaded_server_timestamp = self._conversation_timestamp(
            conversation_id
        )
        self._dirty_conversations.discard(conversation_id)
        self._cache_current_history()
        self._finish_history()
        if reset:
            self.conversationLoaded.emit()
        if follow_latest:
            self.messageAppendedForConversation.emit(conversation_id)
        if self._pending_message_focus:
            message_id = self._pending_message_focus
            if self.message_index(message_id) >= 0:
                self._pending_message_focus = ""
                self.messageFocusRequested.emit(message_id)
            elif self._has_more:
                self._load_messages(reset=False)
            else:
                self._pending_message_focus = ""
        if self._visible and self._conversation_opened:
            self._mark_read()

    def _history_failed(self, request_id, conversation_id, error):
        if request_id != self._history_request_id:
            return
        if conversation_id == self._conversation_id:
            self._error, stacktrace = _worker_error(error)
            debug_log = getattr(self._application, "debug_log", None)
            if debug_log:
                debug_log.raise_error(
                    self._error,
                    stacktrace=stacktrace,
                    group="communication/messages/history",
                )
        current_failed = conversation_id == self._conversation_id
        self._finish_history()
        if current_failed and not self._history_busy:
            self.conversationLoaded.emit()

    def _finish_history(self):
        self._history_busy = False
        self._history_background = False
        self._history_worker = None
        self._history_conversation_id = ""
        self.stateChanged.emit()
        pending = self._pending_history_load
        self._pending_history_load = None
        if pending and pending[0] == self._conversation_id:
            self._load_messages(
                reset=pending[1],
                background=pending[2] if len(pending) > 2 else False,
                bypass_cache=pending[3] if len(pending) > 3 else False,
            )

    @Slot(bool)
    def set_visible(self, value):
        value = bool(value)
        if value == self._visible:
            return
        self._visible = value
        self.visibilityChanged.emit(value)
        if (
            self._visible
            and self._schema_refresh_pending
            and not self._busy
        ):
            self._schema_refresh_pending = False
            self.refresh()
        if self._visible and self._timestamp_presentation_dirty:
            self._refresh_timestamp_presentation()
        if self._visible and self._conversation_opened:
            self._mark_read()

    def _mark_read(self):
        conversation = self.selectedConversation
        if (
            self._read_worker
            or not self._visible
            or not self._conversation_opened
            or not self._conversation_id
            or not self.messages._records
            or not (
                int(conversation.get("unread") or 0) > 0
                or int(conversation.get("mentionCount") or 0) > 0
                or any(
                    bool(record.get("unread"))
                    for record in self.messages._records
                )
            )
        ):
            return
        timestamp = max(
            str(record.get("timestamp") or "") for record in self.messages._records
        )
        if not timestamp:
            return
        conversation_id = self._conversation_id
        from thlib.environment import env_inst

        def operation():
            import thlib.tactic_classes as tc
            return tc.mark_chat_read(conversation_id, timestamp)

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            return
        self._read_worker = worker
        worker.result.connect(
            lambda result: self._read_ready(conversation_id, timestamp, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._read_failed(error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _read_ready(self, conversation_id, timestamp, _result):
        self._read_worker = None
        if conversation_id != self._conversation_id:
            return
        for row, record in enumerate(self.conversations._records):
            if record.get("conversationId") == conversation_id:
                self.conversations.set_value(row, "lastCleared", timestamp)
                self.conversations.set_value(row, "unread", 0)
                self.conversations.set_value(row, "mentionCount", 0)
                break
        for row, record in enumerate(self.messages._records):
            if record.get("unread"):
                self.messages.set_value(row, "unread", False)
        self.stateChanged.emit()

    def _read_failed(self, error):
        self._read_worker = None
        message, stacktrace = _worker_error(error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                message, stacktrace=stacktrace, group="communication/messages/read"
            )

    @Slot(str, result=bool)
    def send(self, body):
        body = str(body or "").strip()
        has_attachments = bool(self.attachments and self.attachments.count)
        if self.busy or not self._conversation_id or (not body and not has_attachments):
            return False
        self._pending_body = body
        self._sending = True
        self._sending_conversation_id = self._conversation_id
        self._pending_send = {
            "conversationId": self._conversation_id,
            "body": body,
            "replyTo": str(self._reply_target.get("messageId") or ""),
        }
        self._pending_draft_context = self._composer.context
        if has_attachments:
            self._busy = True
            self._error = ""
            self.stateChanged.emit()
            if not self.attachments.begin(self._conversation_id):
                self._busy = False
                self._sending = False
                self._sending_conversation_id = ""
                self._pending_send = {}
                self._pending_draft_context = ""
                self._error = self.attachments.error
                self.stateChanged.emit()
                return False
            return True
        self._send_payload([])
        return True

    def _attachments_uploaded(self, snapshot_keys):
        self._busy = False
        self._send_payload(list(snapshot_keys or []))

    def _attachments_failed(self, message, stacktrace):
        self._busy = False
        self._sending = False
        self._sending_conversation_id = ""
        self._pending_send = {}
        self._pending_draft_context = ""
        self._error = str(message or "Attachment upload failed")
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log and "cancelled" not in self._error.casefold():
            debug_log.raise_error(
                self._error, stacktrace=stacktrace,
                group="communication/messages/attachments",
            )
        self.stateChanged.emit()

    def _send_payload(self, snapshot_keys):
        pending = dict(self._pending_send)
        conversation_id = str(pending.get("conversationId") or "")
        body = str(pending.get("body") or "")
        reply_to = str(pending.get("replyTo") or "")
        self._pending_send["hasAttachments"] = bool(snapshot_keys)

        def operation():
            import thlib.tactic_classes as tc
            return tc.send_chat_message(
                conversation_id, body, attachment_keys=snapshot_keys,
                reply_to=reply_to,
            )

        self._run_mutation(operation, self._sent)

    def _sent(self, request_id, result):
        if request_id != self._request_id:
            return
        value = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        sent = dict((value or {}).get("message") or {})
        self._remember_server_message(
            str(
                sent.get("__search_key__")
                or sent.get("code")
                or sent.get("id")
                or ""
            )
        )
        conversation_id = str(
            sent.get("message_code")
            or self._pending_send.get("conversationId")
            or self._conversation_id
        )
        timestamp = str(sent.get("timestamp") or "")
        if conversation_id and timestamp:
            self._notification_cursors[conversation_id] = timestamp
            self._dirty_conversations.add(conversation_id)
        pending = dict(self._pending_send)
        locally_applied = (
            conversation_id == self._conversation_id
            and not pending.get("hasAttachments")
            and not pending.get("replyTo")
            and self._append_live_message(sent)
        )
        self._update_conversation_from_message(sent, increment=True)
        self._pending_body = ""
        self._pending_send = {}
        self._reply_target = {}
        sent_draft_context = self._pending_draft_context
        self._pending_draft_context = ""
        self._composer.clear(sent_draft_context)
        self._finish()
        self.messageSent.emit()
        self.messageSentForConversation.emit(conversation_id)
        if locally_applied:
            self._dirty_conversations.discard(conversation_id)
            self.conversations.replace(sorted(
                (dict(record) for record in self.conversations._records),
                key=lambda record: (
                    bool(record.get("isPersonalNotes")),
                    str(record.get("lastTimestamp") or record.get("createdAt") or ""),
                ),
                reverse=True,
            ))
            self.stateChanged.emit()
        else:
            self._follow_latest_after_history = conversation_id
            self.refresh()

    @staticmethod
    def _message_metadata(info):
        raw = (info or {}).get("metadata") or {}
        if isinstance(raw, dict):
            return dict(raw)
        try:
            return json.loads(str(raw))
        except (TypeError, ValueError):
            return {}

    def _append_live_message(self, info):
        """Append a complete-enough live row without re-querying chat history."""
        if not isinstance(info, dict) or not self._conversation_id:
            return False
        metadata = self._message_metadata(info)
        if (
            int(info.get("__attachment_count__") or 0)
            or metadata.get("attachmentKeys")
            or metadata.get("replyTo")
            or metadata.get("forwardedFrom")
        ):
            return False
        message_id = str(info.get("__search_key__") or info.get("code") or "")
        if not message_id or self.message_index(message_id) >= 0:
            return bool(message_id)
        decorated = dict(info)
        decorated["__edit_history__"] = list(metadata.get("editHistory") or [])
        decorated["__reactions__"] = dict(metadata.get("reactions") or {})
        decorated["__attachments__"] = []
        decorated["__reply__"] = {}
        decorated["__forwarded_from__"] = {}
        from thlib.environment import env_server
        last_cleared = ""
        for conversation in self.conversations._records:
            if conversation.get("conversationId") == self._conversation_id:
                last_cleared = str(conversation.get("lastCleared") or "")
                break
        record = self._message_record(
            decorated, last_cleared, str(env_server.get_user() or "")
        )
        tail = self.messages._records[-1:] + [record]
        grouped_tail = self._group_message_records(tail)
        if len(grouped_tail) == 2:
            self.messages.update_record(self.messages.count() - 1, {
                "groupLast": grouped_tail[0]["groupLast"],
            })
        self.messages.append_records([grouped_tail[-1]])
        self._offset += 1
        self._loaded_server_timestamp = max(
            self._loaded_server_timestamp,
            str(info.get("timestamp") or ""),
        )
        self._dirty_conversations.discard(self._conversation_id)
        self._cache_current_history()
        if self._visible and self._conversation_opened:
            self._mark_read()
        self.messageAppendedForConversation.emit(self._conversation_id)
        return True

    def _update_conversation_from_message(self, info, *, increment):
        conversation_id = str((info or {}).get("message_code") or "")
        if not conversation_id:
            return False
        metadata = self._message_metadata(info)
        for row, conversation in enumerate(self.conversations._records):
            if conversation.get("conversationId") != conversation_id:
                continue
            body = (
                "Forwarded message"
                if metadata.get("forwardedFrom")
                else str(info.get("message") or "")
            )
            values = {
                "lastMessage": body,
                "lastTimestamp": str(
                    info.get("__event_timestamp__")
                    or info.get("timestamp") or ""
                ),
                "lastSender": str(info.get("login") or ""),
            }
            if increment:
                values["messageCount"] = int(
                    conversation.get("messageCount") or 0
                ) + 1
                values["attachmentCount"] = int(
                    conversation.get("attachmentCount") or 0
                ) + int(info.get("__attachment_count__") or 0)
            for role, value in values.items():
                self.conversations.set_value(row, role, value)
            return True
        return False

    @Slot(str)
    def open_link(self, value):
        value = str(value or "").strip()
        if value.startswith("skey://"):
            self.open_skey_preview(value)
        elif value.startswith("tactic-search://"):
            self._application.search(value)
        elif value.startswith("user://"):
            login = value[7:].strip()
            matched_login = next((
                str(record.get("login") or "")
                for record in (self._users._records if self._users else [])
                if str(record.get("login") or "").casefold() == login.casefold()
            ), "")
            if matched_login:
                self.userProfileRequested.emit(matched_login)
        elif value.startswith(("http://", "https://", "ftp://")):
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(value))

    @Slot(str)
    def download_attachment(self, token):
        self._request_attachment(token, False)

    def _request_attachment(self, token, open_after):
        token = str(token or "")
        file_object = self._files.get(token)
        if not file_object or not self._conversation_id:
            return
        if not any(
            record.get("conversationId") == self._conversation_id
            for record in self.conversations._records
        ):
            self._error = "This attachment is not available to the current chat"
            self.stateChanged.emit()
            return
        conversation_id = self._conversation_id
        snapshot_code = ""
        for message in self.messages._records:
            for attachment in message.get("attachments") or []:
                if attachment.get("token") == token:
                    snapshot_code = str(attachment.get("snapshotCode") or "")
                    break
        if not snapshot_code:
            return
        from thlib.environment import env_inst

        def operation():
            import thlib.tactic_classes as tc
            return tc.authorize_chat_attachment(
                conversation_id, snapshot_code
            )

        worker = env_inst.server_pool.add_task(operation)
        if worker is None:
            return
        worker_id = uuid.uuid4().hex
        self._download_workers[worker_id] = worker
        worker.result.connect(
            lambda result: self._attachment_authorized(
                worker_id, token, open_after, result
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._attachment_authorization_failed(
                worker_id, error
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot(str, str)
    def attachment_action(self, token, action):
        token = str(token or "")
        action = str(action or "")
        if action in {"download", "open"}:
            self._request_attachment(token, action == "open")
            return
        file_object = self._files.get(token)
        if not file_object:
            return
        try:
            if action == "folder":
                file_object.open_folder()
            elif action == "copy_path":
                from PySide6.QtGui import QGuiApplication
                QGuiApplication.clipboard().setText(
                    str(file_object.get_full_abs_path() or "")
                )
            elif action == "copy_web":
                from PySide6.QtGui import QGuiApplication
                QGuiApplication.clipboard().setText(
                    str(file_object.get_full_web_path() or "")
                )
            elif action == "copy_image":
                from PySide6.QtGui import QGuiApplication, QImage
                image = QImage(str(file_object.get_full_abs_path() or ""))
                if image.isNull():
                    raise ValueError("The attachment is not a local image")
                QGuiApplication.clipboard().setImage(image)
        except Exception as error:
            self._error = str(error)
            self.stateChanged.emit()
            debug_log = getattr(self._application, "debug_log", None)
            if debug_log:
                debug_log.raise_error(
                    error,
                    stacktrace=traceback.format_exc(),
                    group="communication/messages/attachments",
                )

    def _attachment_authorized(self, worker_id, token, open_after, result):
        self._download_workers.pop(worker_id, None)
        value = result[0] if isinstance(result, tuple) and len(result) == 1 else result
        if not bool((value or {}).get("allowed")):
            self._error = "This attachment is not available to the current chat"
            self.stateChanged.emit()
            return
        file_object = self._files.get(token)
        if not file_object:
            return
        try:
            if file_object.is_exists():
                if open_after:
                    file_object.open_file()
                return
            if open_after:
                self._open_after_download.add(token)
            self._application.repository_sync.schedule_file_object(
                file_object, process="attachment", auto_start=True
            )
        except (OSError, RuntimeError, ValueError) as error:
            self._open_after_download.discard(token)
            self._error = str(error)
            self.stateChanged.emit()

    def _attachment_authorization_failed(self, worker_id, error):
        self._download_workers.pop(worker_id, None)
        self._error, stacktrace = _worker_error(error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                self._error, stacktrace=stacktrace,
                group="communication/messages/attachments",
            )
        self.stateChanged.emit()

    def _attachment_downloaded(self, file_object):
        tracked_files = (
            *self._conversation_preview_files.values(),
            *self._files.values(),
            *self._preview_files.values(),
        )
        if not any(tracked is file_object for tracked in tracked_files):
            return
        changed = False
        for row, conversation in enumerate(self.conversations._records):
            tracked = self._conversation_preview_files.get(
                conversation.get("conversationId")
            )
            if tracked is not file_object or not tracked.is_exists():
                continue
            self.conversations.set_value(
                row,
                "avatarUrl",
                QUrl.fromLocalFile(str(tracked.get_full_abs_path())).toString(),
            )
            changed = True
        for row, message in enumerate(self.messages._records):
            attachments = [dict(record) for record in message.get("attachments") or []]
            row_changed = False
            for attachment in attachments:
                token = attachment.get("token")
                tracked = self._files.get(token)
                preview = self._preview_files.get(token)
                if tracked is not file_object and preview is not file_object:
                    continue
                attachment["local"] = bool(tracked and tracked.is_exists())
                if preview and preview.is_exists():
                    attachment["previewUrl"] = QUrl.fromLocalFile(
                        str(preview.get_full_abs_path())
                    ).toString()
                if tracked is file_object and token in self._open_after_download:
                    self._open_after_download.discard(token)
                    if tracked.is_exists():
                        tracked.open_file()
                row_changed = True
            if row_changed:
                self.messages.set_value(row, "attachments", attachments)
                changed = True
        if changed:
            self.stateChanged.emit()

    @Slot(object)
    def apply_server_batch(self, batch):
        messages = list((batch or {}).get("messages") or [])
        reaction_updates = list((batch or {}).get("reactions") or [])
        reactions_changed = False
        for update in reaction_updates:
            if str(update.get("messageCode") or "") != self._conversation_id:
                continue
            identity = _message_identity(update.get("messageId"))
            if not identity or identity in self._pending_reactions:
                continue
            row = self.message_index(identity)
            if row < 0:
                continue
            reactions = self._reaction_records(update.get("reactions") or {})
            if reactions != self.messages.get(row).get("reactions"):
                self.messages.set_value(row, "reactions", reactions)
                reactions_changed = True
            delivery = self._delivery_record(update.get("delivery") or {})
            current_record = self.messages.get(row)
            for role, value in delivery.items():
                if current_record.get(role) != value:
                    self.messages.set_value(row, role, value)
                    reactions_changed = True
        if not messages:
            if reactions_changed:
                self.stateChanged.emit()
            return
        initial = bool((batch or {}).get("initialMessages"))
        from thlib.environment import env_server
        current = str(env_server.get_user() or "").casefold()
        conversation_rows = {
            str(record.get("conversationId") or ""): row
            for row, record in enumerate(self.conversations._records)
        }
        conversation_records = [
            dict(record) for record in self.conversations._records
        ]
        unknown_conversation = False
        records_changed = False
        active_history_changed = False
        messages.sort(key=lambda info: str(
            info.get("__event_timestamp__") or info.get("timestamp") or ""
        ))
        for info in messages:
            code = str(
                info.get("__search_key__")
                or info.get("code")
                or ""
            )
            conversation_id = str(info.get("message_code") or "")
            if not conversation_id:
                continue
            sender = str(info.get("login") or "")
            timestamp = str(
                info.get("__event_timestamp__")
                or info.get("timestamp") or ""
            )
            row = conversation_rows.get(conversation_id, -1)
            conversation = (
                conversation_records[row] if row >= 0 else {}
            )
            raw_metadata = info.get("metadata") or {}
            if isinstance(raw_metadata, dict):
                metadata = dict(raw_metadata)
            else:
                try:
                    metadata = json.loads(str(raw_metadata))
                except (TypeError, ValueError):
                    metadata = {}
            forwarded = bool(
                metadata.get("forwardedFrom")
                or info.get("__forwarded_from__")
            )
            has_reply = bool(
                metadata.get("replyTo") or info.get("__reply__")
            )
            attachment_count = int(
                info.get("__attachment_count__") or 0
            )
            content_preview = self._message_content_preview(
                info.get("message"),
                attachment_count=attachment_count,
                has_reply=has_reply,
                forwarded=forwarded,
                empty_text="New message",
            )
            notification_excerpt = str(
                content_preview.get("summary") or "New message"
            )[:240]
            last_known = self._notification_cursors.get(conversation_id)
            if last_known is None:
                last_known = str(conversation.get("lastTimestamp") or "")
                self._notification_cursors[conversation_id] = last_known
            already_seen = code and code in self._seen_server_messages
            self._remember_server_message(code)
            if not initial and not already_seen:
                self._dirty_conversations.add(conversation_id)
            if timestamp and (not last_known or timestamp > last_known):
                self._notification_cursors[conversation_id] = timestamp
            if not initial and not already_seen:
                if row < 0:
                    unknown_conversation = True
                else:
                    body = (
                        "Forwarded message"
                        if forwarded
                        else str(info.get("message") or "")
                    )
                    conversation.update({
                        "lastMessage": body,
                        "lastTimestamp": timestamp,
                        "lastSender": sender,
                        "messageCount": int(
                            conversation.get("messageCount") or 0
                        ) + 1,
                        "attachmentCount": int(
                            conversation.get("attachmentCount") or 0
                        ) + attachment_count,
                    })
                    is_open = (
                        self._visible
                        and self._conversation_opened
                        and conversation_id == self._conversation_id
                    )
                    if sender.casefold() != current and not is_open:
                        conversation["unread"] = int(
                            conversation.get("unread") or 0
                        ) + 1
                        if (
                            int(conversation.get("participantCount") or 0) > 2
                            and re.search(
                                r"(^|[^A-Za-z0-9_.@-])@{0}($|[^A-Za-z0-9_.-])".format(
                                    re.escape(str(env_server.get_user() or ""))
                                ),
                                str(info.get("message") or ""),
                                re.IGNORECASE,
                            )
                        ):
                            conversation["mentionCount"] = int(
                                conversation.get("mentionCount") or 0
                            ) + 1
                    conversation.update(
                        self._conversation_profile(conversation)
                    )
                    records_changed = True
                    if conversation_id == self._conversation_id:
                        active_history_changed = not self._append_live_message(info)
            if (
                already_seen
                or sender.casefold() == current
                or initial
                or not self._notifications_enabled
                or (last_known and timestamp and timestamp <= last_known)
                or (
                    self._visible
                    and self._conversation_opened
                    and conversation_id == self._conversation_id
                )
            ):
                continue
            self.newMessage.emit(
                conversation_id,
                str(conversation.get("title") or sender or "Messages"),
                notification_excerpt[:160],
            )
            sender_profile = self._message_profile(sender)
            self.newMessageNotification.emit({
                "conversationId": conversation_id,
                "conversationTitle": str(
                    conversation.get("title") or "Messages"
                ),
                "senderLogin": sender,
                "senderTitle": str(
                    sender_profile.get("senderDisplay") or sender
                    or "Removed user"
                ),
                "excerpt": notification_excerpt,
                "avatarUrl": str(sender_profile.get("avatarUrl") or ""),
                "initials": str(sender_profile.get("initials") or ""),
                "avatarColor": str(
                    sender_profile.get("senderColor") or ""
                ),
            })
        if records_changed:
            conversation_records.sort(
                key=lambda record: (
                    bool(record.get("isPersonalNotes")),
                    str(
                        record.get("lastTimestamp")
                        or record.get("createdAt") or ""
                    ),
                ),
                reverse=True,
            )
            self.conversations.replace(conversation_records)
            self.stateChanged.emit()
        if active_history_changed and not self._history_busy:
            self._follow_latest_after_history = self._conversation_id
            self._load_messages(reset=True, background=True)
        if unknown_conversation:
            self.refresh()

    def _remember_server_message(self, code):
        code = str(code or "")
        if not code or code in self._seen_server_messages:
            return
        self._seen_server_messages.add(code)
        self._seen_server_message_order.append(code)
        overflow = len(self._seen_server_message_order) - 2000
        if overflow <= 0:
            return
        removed = self._seen_server_message_order[:overflow]
        del self._seen_server_message_order[:overflow]
        self._seen_server_messages.difference_update(removed)

    def _failed(self, request_id, error):
        if request_id != self._request_id:
            return
        self._error, stacktrace = _worker_error(error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                self._error, stacktrace=stacktrace, group="communication/messages"
            )
        self._finish()

    def _finish(self):
        self._busy = False
        self._sending = False
        self._sending_conversation_id = ""
        self._worker = None
        self.stateChanged.emit()
        if self._pending_refresh:
            self._pending_refresh = False
            self.refresh()


class ActivityFeedController(QObject):
    stateChanged = Signal()
    visibilityChanged = Signal(bool)
    calendarInvalidated = Signal()
    notificationsEnabledChanged = Signal()
    activityNotification = Signal("QVariantMap")

    CACHE_CONTRACT = "complete-journal-activity-v2"
    FILTERS = {
        "all", "my_tasks", "my_objects", "notes", "publications",
    }
    def __init__(
            self, application, skey_previews=None, users=None,
            tasks=None, parent=None, clock=None,
    ):
        super().__init__(parent or application)
        self._application = application
        self._skey_previews = skey_previews
        self._performance = getattr(application, "ui_performance", None)
        self._users = users
        self._tasks = tasks
        self._clock = clock
        self._settings = dict(env_read_config(
            filename="read_state",
            unique_id="cache/activity_feed",
            long_abs_path=True,
        ) or {})
        self._notification_preferences = dict(env_read_config(
            filename="ui_settings",
            unique_id="ui_activity_feed",
            long_abs_path=True,
        ) or {})
        self._notifications_enabled = bool(
            self._notification_preferences.get(
                "notifications/enabled", True,
            )
        )
        self.model = RecordListModel((
            "eventId", "kind", "title", "detail", "actor", "timestamp",
            "timestampPretty", "timestampFull", "actorLabel",
            "actorAvatar", "actorInitials", "actorColor", "itemCode", "itemTitle",
            "searchKey", "targetSearchKey", "targetTitle", "targetType",
            "targetTypeTitle",
            "pipelineCode", "typeColor", "processColor", "project",
            "process", "context", "version", "statusBefore", "statusAfter",
            "changes", "taskCode", "serverGenerated",
            "itemType", "itemTypeTitle", "itemTypeColor", "relationAction",
            "hours", "workDay", "workDayPretty", "workHourAction",
            "workHourCategory", "workHourStatus", "workHourOwner",
            "statusBeforeColor", "statusAfterColor", "canOpen", "dayKey",
        ), identity_role="eventId")
        self._all_records = []
        self._calendar_counts = {}
        self._calendar_counts_loaded = False
        self._calendar_cache_complete = False
        self._calendar_busy = False
        self._calendar_request_id = ""
        self._calendar_worker = None
        self._calendar_invalidated_during_request = False
        self._calendar_bypass_cache = False
        self._selected_day = ""
        self._filter = "all"
        self._selected_users = []
        self._exclude_own_activity = False
        self._restore_calendar_counts()
        self._search_text = ""
        self._busy = False
        self._error = ""
        self._offset = 0
        self._page_size = 25
        self._has_more = False
        self._request_id = ""
        self._worker = None
        self._live_refresh_pending = False
        self._visible = False
        self._presentation_managed = False
        self._presentation_dirty = False
        self._unread_event_ids = set()
        self._notification_event_ids = OrderedDict()
        self._pending_notification_events = OrderedDict()
        self._notification_worker = None
        self._notification_request_id = ""
        self._notification_revision = 0
        self._notification_sink_active = False
        self._latest_activity_timestamp = ""
        self._read_cursor = ""
        self._read_cursor_exists = False
        self._load_read_cursor()
        application.project_changed.connect(self._project_changed)
        if self._users is not None:
            self._users.contentReplaced.connect(self._refresh_identities)
        if self._clock is not None:
            self._clock.changed.connect(self._clock_changed)

    def _present_records(self, records):
        users = self._users.records() if self._users is not None else ()
        return present_activity_records(records, users)

    @staticmethod
    def _without_actor(records, login):
        login = str(login or "").strip().casefold()
        if not login:
            return [dict(record or {}) for record in records or ()]
        return [
            dict(record or {}) for record in records or ()
            if login not in activity_actor_logins(record)
        ]

    def _without_own_activity(self, records):
        from thlib.environment import env_server

        return self._without_actor(records, env_server.get_user())

    def _feed_records(self, records):
        if self._exclude_own_activity:
            return self._without_own_activity(records)
        return [dict(record or {}) for record in records or ()]

    @Slot(object)
    def apply_cache_invalidation(self, payload):
        payload = dict(payload or {})
        hard_reset = bool(payload.get("all"))
        domains = {
            str(domain) for domain in payload.get("domains") or ()
        }
        project_code = str(self._application.current_project_code or "")
        domains.update(
            str(domain) for domain in payload.get(project_code) or ()
        )
        if not (
            hard_reset
            or "activity" in domains
        ):
            return
        if hard_reset or payload.get("preferences"):
            self._cancel_notification_enrichment(clear_pending=True)
            self._request_id = ""
            self._calendar_request_id = ""
            for worker in (self._worker, self._calendar_worker):
                if worker is None:
                    continue
                try:
                    worker.cancel()
                except (AttributeError, RuntimeError):
                    pass
            self._worker = None
            self._calendar_worker = None
            self._busy = False
            self._calendar_busy = False
            self._calendar_counts = {}
        self._calendar_counts_loaded = False
        self._calendar_cache_complete = False
        self._calendar_invalidated_during_request = self._calendar_busy
        self.stateChanged.emit()
        self.calendarInvalidated.emit()

    def _refresh_identities(self):
        current = list(self._all_records or self.model.records())
        presented = self._present_records(current)
        if presented != current:
            self._replace_records(presented)

    @staticmethod
    def _day_key(record):
        timestamp = str(record.get("timestamp") or "").strip()
        match = re.match(r"^(\d{4}-\d{2}-\d{2})", timestamp)
        return match.group(1) if match else ""

    def _merged_day_counts(self):
        loaded_counts = {}
        for record in self._all_records:
            day_key = self._day_key(record)
            if day_key:
                loaded_counts[day_key] = loaded_counts.get(day_key, 0) + 1
        counts = dict(self._calendar_counts)
        for day_key, count in loaded_counts.items():
            counts[day_key] = max(counts.get(day_key, 0), count)
        return counts

    def _calendar_cache_unique_id(
            self, feed_filter=None, selected_users=None):
        from thlib.environment import env_server

        cache_filter = str(feed_filter or self._filter)
        cache_users = (
            self._selected_users
            if selected_users is None else selected_users
        )
        identity = "\0".join((
            self.CACHE_CONTRACT,
            "exclude" if self._exclude_own_activity else "include",
            str(env_server.get_server() or ""),
            str(env_server.get_user() or ""),
            str(self._application.current_project_code or ""),
            cache_filter,
            "\0".join(sorted(str(value) for value in cache_users)),
        ))
        digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()
        return "cache/activity_feed/calendar/" + digest

    def _read_calendar_cache(self, feed_filter=None, selected_users=None):
        from thlib import server_cache

        cache_key = "calendar:" + self._calendar_cache_unique_id(
            feed_filter, selected_users
        )
        project_code = str(self._application.current_project_code or "")
        payload = server_cache.read_entry(
            "activity", cache_key, project_code,
        )
        current = payload is not None
        if payload is None:
            # Activity invalidation advances the shared domain revision.  The
            # last complete calendar is still a much better immediate view
            # than counts reconstructed from the first feed page, so retain
            # it visibly while a full recount runs in the background.
            payload = server_cache.read_stale_entry(
                "activity", cache_key, project_code,
            )
        payload = dict(payload or {})
        complete = (
            set(payload) == {"completeHistory", "dayCounts"}
            and payload.get("completeHistory") is True
            and isinstance(payload.get("dayCounts"), dict)
        )
        if not complete:
            return {}, False
        return {
            str(day_key): int(count or 0)
            for day_key, count in dict(
                payload.get("dayCounts") or {}
            ).items()
            if re.match(r"^\d{4}-\d{2}-\d{2}$", str(day_key))
        }, bool(current)

    def _restore_calendar_counts(self):
        self._calendar_request_id = ""
        self._calendar_busy = False
        self._calendar_worker = None
        self._calendar_invalidated_during_request = False
        self._calendar_bypass_cache = False
        self._calendar_counts_loaded = False
        counts, complete = self._read_calendar_cache()

        # Category caches are disjoint subsets of the full journal.  Reuse
        # them as an immediate lower bound while a missing/stale full-history
        # cache is rebuilt; the full calendar must never show fewer notes and
        # publications than those category calendars already know about.
        if self._filter == "all":
            category_totals = {}
            for category in ("notes", "publications"):
                category_counts, category_complete = (
                    self._read_calendar_cache(
                        category, self._selected_users
                    )
                )
                if not category_complete:
                    continue
                for day_key, count in category_counts.items():
                    category_totals[day_key] = (
                        category_totals.get(day_key, 0) + count
                    )
            for day_key, count in category_totals.items():
                counts[day_key] = max(counts.get(day_key, 0), count)

        self._calendar_counts = counts
        self._calendar_cache_complete = complete

    def _save_calendar_counts(self):
        from thlib import server_cache

        project_code = str(self._application.current_project_code or "")
        server_cache.write_entry(
            "activity",
            "calendar:" + self._calendar_cache_unique_id(),
            {
                "completeHistory": True,
                "dayCounts": dict(self._calendar_counts),
            },
            project_code,
        )

    def _calendar_delta_start(self):
        if not self._calendar_cache_complete:
            return ""
        return max(self._calendar_counts, default="")

    def _validate_selected_day(self):
        counts = self._merged_day_counts()
        if self._selected_day and self._selected_day not in counts:
            self._selected_day = ""

    @staticmethod
    def _matches_search(record, search_text):
        if not search_text:
            return True
        searchable_fields = (
            "actorLabel", "actor", "title", "detail", "targetTitle",
            "targetTypeTitle", "itemTitle", "itemTypeTitle", "process",
            "context", "statusBefore",
            "statusAfter", "version",
            "workDay", "workDayPretty", "workHourCategory",
            "workHourStatus", "workHourOwner",
        )
        haystack = "\n".join(
            str(record.get(field) or "") for field in searchable_fields
        ).casefold()
        return all(part in haystack for part in search_text.split())

    @measure_ui("Activity: filter and publish")
    def _apply_day_filter(self):
        if self._presentation_managed and not self._visible:
            self._presentation_dirty = True
            return
        records = self._all_records
        if self._selected_day:
            records = [
                record for record in records
                if self._day_key(record) == self._selected_day
            ]
        search_text = self._search_text.casefold().strip()
        if search_text:
            records = [
                record for record in records
                if self._matches_search(record, search_text)
            ]
        self.model.replace([
            {**record, "dayKey": self._day_key(record)}
            for record in records
        ])
        self._presentation_dirty = False

    @staticmethod
    def _unique_records(records):
        """Keep the first row for every stable feed event identity."""
        unique = []
        seen = set()
        for source in records or ():
            record = dict(source or {})
            event_id = str(record.get("eventId") or "")
            if not event_id:
                raise ValueError("Activity records require an eventId")
            if event_id in seen:
                continue
            seen.add(event_id)
            unique.append(record)
        return unique

    def _replace_records(self, records, day_counts=None):
        # Offset pages can overlap when newer server activity arrives between
        # requests. Preserve the retained row and discard the repeated page
        # boundary event before publishing into the keyed Qt model.
        self._all_records = self._unique_records(self._feed_records(records))
        if day_counts is not None:
            self._calendar_counts = {
                str(record.get("dateKey") or ""): int(record.get("count") or 0)
                for record in day_counts
                if record.get("dateKey")
            }
            self._calendar_counts_loaded = True
            self._calendar_cache_complete = True
        self._validate_selected_day()
        self._apply_day_filter()

    def _project_changed(self, project_code, _title):
        self._cancel_notification_enrichment(clear_pending=True)
        self._request_id = ""
        self._busy = False
        self._worker = None
        self._live_refresh_pending = False
        self._unread_event_ids.clear()
        self._notification_event_ids.clear()
        self._latest_activity_timestamp = ""
        self._all_records = []
        self._restore_calendar_counts()
        self._selected_day = ""
        self._search_text = ""
        self.model.clear()
        self._load_read_cursor()
        if project_code and self._visible:
            self._load(reset=True)
        else:
            self._error = ""
            self._has_more = False
            self.stateChanged.emit()

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(str, notify=stateChanged)
    def currentFilter(self):
        return self._filter

    @Property(bool, notify=stateChanged)
    def excludeOwnActivity(self):
        return self._exclude_own_activity

    @Property(bool, notify=notificationsEnabledChanged)
    def notificationsEnabled(self):
        return self._notifications_enabled

    @Property(str, notify=stateChanged)
    def selectedDay(self):
        return self._selected_day

    @Property("QVariantList", notify=stateChanged)
    def selectedUsers(self):
        return list(self._selected_users)

    @Property(str, notify=stateChanged)
    def searchText(self):
        return self._search_text

    @Property("QVariantMap", notify=stateChanged)
    def calendarCounts(self):
        return self._merged_day_counts()

    @Property(bool, notify=stateChanged)
    def calendarBusy(self):
        return self._calendar_busy

    @Property(bool, notify=stateChanged)
    def hasMore(self):
        return self._has_more

    @Property(int, notify=stateChanged)
    def unreadCount(self):
        return len(self._unread_event_ids)

    def _read_cursor_key(self):
        from thlib.environment import env_server

        identity = "\0".join((
            str(env_server.get_server() or ""),
            str(env_server.get_user() or ""),
            str(self._application.current_project_code or ""),
        ))
        digest = hashlib.sha1(identity.encode("utf-8")).hexdigest()
        return "activityFeed/lastRead/" + digest

    def _load_read_cursor(self):
        key = self._read_cursor_key()
        self._read_cursor_exists = key in self._settings
        self._read_cursor = str(self._settings.get(key, "") or "")

    def _save_read_cursor(self, timestamp):
        timestamp = str(timestamp or "")
        if not timestamp:
            return
        self._read_cursor = timestamp
        self._read_cursor_exists = True
        self._settings[self._read_cursor_key()] = timestamp
        env_write_config(
            self._settings,
            filename="read_state",
            unique_id="cache/activity_feed",
            long_abs_path=True,
        )

    @Slot(bool)
    def set_visible(self, value):
        value = bool(value)
        first_managed_state = not self._presentation_managed
        self._presentation_managed = True
        if value == self._visible and not first_managed_state:
            return
        self._visible = value
        self.visibilityChanged.emit(value)
        if value:
            if self._presentation_dirty:
                self._apply_day_filter()
            self.mark_read()
            if self._live_refresh_pending:
                self._reconcile_live_activity()
            elif not self.model._records and not self._busy:
                self._load(reset=True)

    @Slot()
    def mark_read(self):
        timestamp = self._latest_activity_timestamp
        if not timestamp:
            timestamps = [
                str(record.get("timestamp") or "")
                for record in self._all_records
                if record.get("timestamp")
            ]
            timestamp = max(timestamps) if timestamps else ""
        if timestamp:
            self._save_read_cursor(timestamp)
        if self._unread_event_ids:
            self._unread_event_ids.clear()
            self.stateChanged.emit()

    @staticmethod
    def _activity_identity(info):
        event_id = str(info.get("eventId") or "").strip()
        if event_id:
            return event_id
        kind = str(info.get("__kind__") or info.get("kind") or "change")
        timestamp = str(
            info.get("__event_timestamp__") or info.get("timestamp") or ""
        )
        source = str(
            info.get("code") or info.get("id")
            or info.get("__search_key__") or info.get("searchKey")
            or info.get("search_code") or ""
        )
        return ":".join((kind, source, timestamp))

    @staticmethod
    def _activity_actor(info):
        info = dict(info or {})
        for key in ("actor", "__actor__", "login"):
            value = str(info.get(key) or "").strip()
            if value:
                return value
        changed_by = info.get("changed_by") or info.get("changedBy") or {}
        if isinstance(changed_by, str):
            try:
                changed_by = json.loads(changed_by)
            except (TypeError, ValueError):
                changed_by = {}
        values = (
            changed_by.values()
            if isinstance(changed_by, dict) else changed_by
            if isinstance(changed_by, (list, tuple, set)) else ()
        )
        return next((
            str(value).strip() for value in values
            if str(value or "").strip()
        ), "")

    def _activity_notification_payload(self, source):
        source = dict(source or {})
        kind = str(
            source.get("kind") or source.get("__kind__") or "activity"
        )
        timestamp = str(
            source.get("timestamp")
            or source.get("__event_timestamp__") or ""
        )
        actor = self._activity_actor(source)
        target_title = str(
            source.get("targetTitle")
            or source.get("itemTitle")
            or source.get("name")
            or source.get("title")
            or source.get("search_code") or ""
        )
        normalized_source = dict(source)
        normalized_source.update({
            "eventId": self._activity_identity(source),
            "kind": kind,
            "timestamp": timestamp,
            "actor": actor,
            "actorLabel": str(source.get("actorLabel") or actor),
            "targetTitle": target_title,
            "targetSearchKey": str(
                source.get("targetSearchKey")
                or source.get("searchKey")
                or source.get("__search_key__") or ""
            ),
            "process": str(source.get("process") or ""),
            "context": str(source.get("context") or ""),
            "detail": str(
                source.get("detail") or source.get("description") or ""
            ),
        })
        normalized = self._present_records([
            activity_record(normalized_source, clock=self._clock)
        ])[0]
        actor_label = str(
            normalized.get("actorLabel") or actor
            or self.tr("Server trigger")
        )
        process = str(
            normalized.get("process")
            or normalized.get("context") or ""
        ).partition("/")[0].strip()
        target = str(
            normalized.get("targetTitle")
            or normalized.get("itemTitle")
            or self.tr("the related object")
        )
        target_type = str(
            normalized.get("targetTypeTitle")
            or normalized.get("targetType") or ""
        ).split("?", 1)[0].rsplit("/", 1)[-1].replace("_", " ")
        target_reference = (
            f"{target_type} / {target}" if target_type else target
        )
        process_phrase = (
            self.tr(" in process {process}").format(process=process)
            if process else ""
        )
        detail = str(normalized.get("detail") or "").strip()
        if kind == "publication":
            summary = self.tr("Published {target}{process}.").format(
                target=target, process=process_phrase,
            )
        elif kind == "note":
            summary = self.tr(
                "Added a note to {target}{process}: {detail}"
            ).format(
                target=target,
                process=process_phrase,
                detail=detail or self.tr("No text"),
            )
        elif kind == "task":
            task_detail = str(
                normalized.get("statusAfter") or detail
                or self.tr("Task updated")
            )
            summary = self.tr(
                "Updated task for {target}{process}: {detail}"
            ).format(
                target=target,
                process=process_phrase,
                detail=task_detail,
            )
        elif kind == "status":
            before = str(normalized.get("statusBefore") or "—")
            after = str(normalized.get("statusAfter") or "—")
            summary = self.tr(
                "Changed status for {target}{process}: "
                "{before} → {after}."
            ).format(
                target=target, process=process_phrase,
                before=before, after=after,
            )
        elif kind == "create":
            summary = self.tr("Created {target}.").format(
                target=target_reference,
            )
        elif kind == "delete":
            summary = self.tr("Deleted {target}.").format(
                target=target_reference,
            )
        elif kind == "change":
            summary = self.tr("Updated object: {target}.").format(
                target=target_reference,
            )
            changes = []
            for change in normalized.get("changes") or ():
                change = dict(change or {})
                field = str(change.get("field") or "").replace("_", " ")
                before = str(change.get("before") or "")
                after = str(change.get("after") or "")
                values_known = change.get("valuesKnown", True) is not False
                if not field:
                    continue
                if before or after or values_known:
                    changes.append(
                        f"{field}: "
                        f"{before or self.tr('empty')} → "
                        f"{after or self.tr('empty')}"
                    )
                else:
                    changes.append(field)
                if len(changes) == 2:
                    break
            if changes:
                summary += " " + "; ".join(changes)
            elif detail:
                summary += " " + detail
        elif kind == "work_hour":
            summary = self.tr(
                "Updated work hours for {target}{process}: {hours} h."
            ).format(
                target=target,
                process=process_phrase,
                hours=normalized.get("hours") or 0,
            )
        else:
            summary = detail or str(
                normalized.get("title") or self.tr("New activity")
            )
        titles = {
            "status": self.tr("Status changed"),
            "publication": self.tr("New publication"),
            "note": self.tr("New note"),
            "task": self.tr("Task updated"),
            "create": self.tr("Object created"),
            "change": self.tr("Object updated"),
            "delete": self.tr("Object deleted"),
            "work_hour": self.tr("Work hours updated"),
        }
        icons = {
            "status": "system-activity",
            "publication": "snapshot",
            "note": "notes",
            "task": "task",
            "create": "add",
            "change": "edit",
            "delete": "delete",
            "work_hour": "schedule",
        }
        event_title = titles.get(kind, self.tr("New activity"))
        return {
            "eventId": self._activity_identity(normalized),
            "kind": kind,
            "title": event_title,
            "detail": summary,
            "actorTitle": actor_label,
            "avatarUrl": str(normalized.get("actorAvatar") or ""),
            "initials": str(normalized.get("actorInitials") or ""),
            "avatarColor": str(normalized.get("actorColor") or ""),
            "previewUrl": str(
                normalized.get("actorAvatar")
                or source.get("previewUrl")
                or source.get("__preview_url__") or ""
            ),
            "sourceIcon": icons.get(kind, "activity-feed"),
        }

    def _track_activity(self, records, initial=False):
        from thlib.environment import env_server

        records = list(records or [])
        current_login = str(env_server.get_user() or "").strip().casefold()
        timestamps = [
            str(record.get("__event_timestamp__") or record.get("timestamp") or "")
            for record in records
            if record.get("__event_timestamp__") or record.get("timestamp")
        ]
        if timestamps:
            self._latest_activity_timestamp = max(
                [self._latest_activity_timestamp, *timestamps]
            )
        establish_initial_cursor = initial and not self._read_cursor_exists
        for record in records:
            timestamp = str(
                record.get("__event_timestamp__")
                or record.get("timestamp") or ""
            )
            is_own_activity = (
                bool(current_login)
                and current_login in activity_actor_logins(record)
            )
            identity = self._activity_identity(record)
            first_notification = identity not in self._notification_event_ids
            if first_notification:
                self._notification_event_ids[identity] = None
            if (
                    not establish_initial_cursor
                    and timestamp
                    and timestamp > self._read_cursor
                    and not is_own_activity):
                self._unread_event_ids.add(identity)
                if (
                        not initial and first_notification
                        and self._notifications_enabled
                        and self._notification_sink_active):
                    self._pending_notification_events[identity] = dict(record)
                    self._notification_revision += 1
        while len(self._notification_event_ids) > 500:
            self._notification_event_ids.popitem(last=False)
        while len(self._pending_notification_events) > 100:
            self._pending_notification_events.popitem(last=False)
        if establish_initial_cursor:
            self._save_read_cursor(self._latest_activity_timestamp)
        if self._visible:
            self.mark_read()
        else:
            self.stateChanged.emit()

    def set_notification_sink_active(self, active):
        """Attach the single application-owned toast consumer."""
        active = bool(active)
        if active == self._notification_sink_active:
            return
        self._notification_sink_active = active
        if active:
            self._request_notification_enrichment()
        else:
            self._cancel_notification_enrichment(clear_pending=True)

    def _cancel_notification_enrichment(self, *, clear_pending=False):
        self._notification_request_id = ""
        worker = self._notification_worker
        self._notification_worker = None
        if worker is not None:
            try:
                worker.cancel()
            except (AttributeError, RuntimeError):
                pass
        if clear_pending:
            self._pending_notification_events.clear()

    @staticmethod
    def _notification_match_score(raw, enriched):
        raw = dict(raw or {})
        enriched = dict(enriched or {})
        raw_kind = str(raw.get("__kind__") or raw.get("kind") or "change")
        if raw_kind != str(enriched.get("kind") or ""):
            return -1

        score = 0
        raw_code = str(raw.get("code") or raw.get("id") or "").strip()
        event_id = str(enriched.get("eventId") or "")
        if raw_code and (
                event_id.endswith(":" + raw_code)
                or f":{raw_code}:" in event_id):
            score += 100

        raw_target = str(
            raw.get("search_code") or raw.get("searchCode") or ""
        ).strip()
        enriched_identities = {
            str(enriched.get(key) or "").strip()
            for key in ("itemCode", "taskCode")
        }
        enriched_keys = "\n".join((
            str(enriched.get("searchKey") or ""),
            str(enriched.get("targetSearchKey") or ""),
        ))
        if raw_target and (
                raw_target in enriched_identities
                or f"code={raw_target}" in enriched_keys):
            score += 60

        raw_timestamp = str(
            raw.get("__event_timestamp__") or raw.get("timestamp") or ""
        )[:19]
        enriched_timestamp = str(enriched.get("timestamp") or "")[:19]
        if raw_timestamp and raw_timestamp == enriched_timestamp:
            score += 30
        return score

    def _publish_pending_notifications(self, records, pending_ids):
        from thlib.environment import env_server

        current_login = str(env_server.get_user() or "").strip().casefold()
        candidates = [dict(record or {}) for record in records or ()]
        used_indexes = set()
        state_changed = False
        for pending_id in pending_ids:
            raw = self._pending_notification_events.get(pending_id)
            if raw is None:
                continue
            ranked = sorted(
                (
                    (self._notification_match_score(raw, record), index)
                    for index, record in enumerate(candidates)
                    if index not in used_indexes
                ),
                reverse=True,
            )
            if not ranked or ranked[0][0] <= 0:
                continue
            _score, index = ranked[0]
            used_indexes.add(index)
            enriched = candidates[index]
            self._pending_notification_events.pop(pending_id, None)
            if (
                    current_login
                    and current_login in activity_actor_logins(enriched)):
                state_changed = (
                    pending_id in self._unread_event_ids or state_changed
                )
                self._unread_event_ids.discard(pending_id)
                continue
            self.activityNotification.emit(
                self._activity_notification_payload(enriched)
            )
        if state_changed:
            self.stateChanged.emit()

    def _request_notification_enrichment(self):
        if (
                not self._notification_sink_active
                or not self._notifications_enabled
                or not self._pending_notification_events
                or self._notification_worker is not None):
            return
        project_code = str(self._application.current_project_code or "")
        if not project_code:
            return

        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        request_revision = self._notification_revision
        pending_ids = tuple(self._pending_notification_events)
        page_size = max(25, min(100, len(pending_ids) * 4))
        worker = env_inst.server_pool.add_task(
            self._query, "all", project_code, 0, page_size, "", False, [],
            False, "", True, False, False,
        )
        if worker is None:
            return
        self._notification_request_id = request_id
        self._notification_worker = worker
        worker.result.connect(
            lambda result: self._notification_records_ready(
                request_id, project_code, request_revision, pending_ids, result,
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._notification_records_failed(
                request_id, request_revision, error,
            ),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _notification_records_ready(
            self, request_id, project_code, request_revision,
            pending_ids, result):
        if (
                request_id != self._notification_request_id
                or project_code
                != str(self._application.current_project_code or "")):
            return
        self._notification_request_id = ""
        self._notification_worker = None
        payload = dict(result or {}) if isinstance(result, dict) else {}
        source_records = payload.get("records") if payload else result
        records = self._present_records([
            self._normalize_record(record) for record in source_records or ()
        ])
        self._publish_pending_notifications(records, pending_ids)
        if self._notification_revision != request_revision:
            self._request_notification_enrichment()

    def _notification_records_failed(
            self, request_id, request_revision, error):
        if request_id != self._notification_request_id:
            return
        self._notification_request_id = ""
        self._notification_worker = None
        message, stacktrace = _worker_error(error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.log(
                "ERROR", message,
                stacktrace=stacktrace,
                group="communication/feed/notifications",
                source="Controller",
            )
        if self._notification_revision != request_revision:
            self._request_notification_enrichment()

    @Slot(bool)
    def set_notifications_enabled(self, value):
        value = bool(value)
        if value == self._notifications_enabled:
            return
        self._notifications_enabled = value
        if not value:
            self._cancel_notification_enrichment(clear_pending=True)
        self._notification_preferences["notifications/enabled"] = value
        env_write_config(
            self._notification_preferences,
            filename="ui_settings",
            unique_id="ui_activity_feed",
            long_abs_path=True,
        )
        self.notificationsEnabledChanged.emit()

    @Slot(str)
    @measure_ui("Activity: select feed")
    def set_filter(self, value):
        value = str(value or "")
        if value not in self.FILTERS or value == self._filter:
            return
        self._filter = value
        self._selected_day = ""
        self._restore_calendar_counts()
        self.stateChanged.emit()
        if self._busy:
            self._request_id = ""
            self._busy = False
            self._worker = None
        self._load(reset=True)

    @Slot(bool)
    @measure_ui("Activity: toggle own events")
    def set_exclude_own_activity(self, value):
        value = bool(value)
        if value == self._exclude_own_activity:
            return
        self._exclude_own_activity = value
        self._selected_day = ""
        self._restore_calendar_counts()
        if value:
            self._replace_records(self._all_records)
        self.stateChanged.emit()
        if self._busy:
            self._request_id = ""
            self._busy = False
            self._worker = None
        self._load(reset=True)

    @Slot(str)
    def set_search_text(self, value):
        value = str(value or "")
        if value == self._search_text:
            return
        self._search_text = value
        self._apply_day_filter()
        self.stateChanged.emit()

    @Slot("QVariantList")
    def set_users(self, values):
        self._set_user_filter(values)

    @Slot(str)
    def select_user_feed(self, login):
        self._set_user_filter([login], force_all=True)

    def _set_user_filter(self, values, *, force_all=False):
        normalized = list(dict.fromkeys(
            str(value or "").strip()
            for value in (values or [])
            if str(value or "").strip()
        ))
        target_filter = (
            "all" if force_all
            or (normalized and self._filter in {"my_tasks", "my_objects"})
            else self._filter
        )
        if (
                normalized == self._selected_users
                and target_filter == self._filter):
            return
        self._selected_users = normalized
        self._filter = target_filter
        self._selected_day = ""
        self._restore_calendar_counts()
        self.stateChanged.emit()
        if self._busy:
            self._request_id = ""
            self._busy = False
            self._worker = None
        self._load(reset=True)

    @Slot(str)
    @measure_ui("Activity: select day")
    def select_day(self, value):
        value = str(value or "")
        if value == self._selected_day:
            return
        self._selected_day = value
        self._validate_selected_day()
        self._apply_day_filter()
        self.stateChanged.emit()
        if self._busy:
            self._request_id = ""
            self._busy = False
            self._worker = None
        self._load(reset=True)

    @Slot()
    def refresh(self):
        self._calendar_request_id = ""
        if self._calendar_worker is not None:
            self._calendar_worker.cancel()
        self._calendar_busy = False
        self._calendar_worker = None
        self._calendar_counts_loaded = False
        self._calendar_cache_complete = False
        self._calendar_bypass_cache = True
        self._load(reset=True, bypass_cache=True)
        self.calendarInvalidated.emit()

    @Slot()
    def ensure_calendar_counts(self):
        if self._calendar_counts_loaded or self._calendar_busy:
            return
        project_code = str(self._application.current_project_code or "")
        if not project_code:
            return

        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        counts_from_day = self._calendar_delta_start()
        self._calendar_request_id = request_id
        self._calendar_busy = True
        self._calendar_invalidated_during_request = False
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(
            self._query, self._filter, project_code, 0, 1, "", True,
            list(self._selected_users), True, counts_from_day,
            self._calendar_bypass_cache, self._exclude_own_activity,
        )
        if worker is None:
            self._calendar_busy = False
            self._error = "Server worker pool is unavailable."
            self.stateChanged.emit()
            return
        self._calendar_worker = worker
        worker.result.connect(
            lambda result: self._calendar_ready(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._calendar_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @Slot()
    def load_more(self):
        if self._has_more:
            self._load(reset=False)

    def _load(self, reset, bypass_cache=False):
        if self._busy:
            return
        offset = 0 if reset else self._offset
        feed_filter = self._filter
        page_size = self._page_size
        project_code = str(self._application.current_project_code or "")
        if not project_code:
            self.model.clear()
            self._error = "Select a project to load activity."
            self._has_more = False
            self.stateChanged.emit()
            return

        from thlib.environment import env_inst
        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        worker = env_inst.server_pool.add_task(
            self._query, feed_filter, project_code, offset, page_size,
            self._selected_day, False,
            list(self._selected_users),
            False, "", bypass_cache, self._exclude_own_activity,
        )
        if worker is None:
            self._busy = False
            self._error = "Server worker pool is unavailable."
            self.stateChanged.emit()
            return
        if reset:
            # Any successfully scheduled first-page query uses the
            # authoritative enriched feed shape and therefore consumes a
            # pending raw server-update signal.
            self._live_refresh_pending = False
        self._worker = worker
        worker.result.connect(
            lambda result: self._ready(request_id, result, reset, offset),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    @classmethod
    def _instance_relation_catalog(cls, project_code):
        """Return schema-declared endpoint types for every instance table."""
        from thlib.environment import env_inst

        project = (env_inst.projects or {}).get(str(project_code or ""))
        if project is None:
            return {}
        try:
            stypes = project.get_stypes() or {}
        except (AttributeError, KeyError, TypeError):
            stypes = getattr(project, "stypes", None) or {}

        catalog = {}
        for stype_key, stype in dict(stypes).items():
            try:
                current_type = str(stype.get_code() or stype_key or "")
                schema = stype.get_schema()
            except (AttributeError, KeyError, TypeError):
                continue
            for direction, definitions in (
                ("children", getattr(schema, "children", None) or ()),
                ("parents", getattr(schema, "parents", None) or ()),
            ):
                for raw_definition in definitions:
                    definition = dict(raw_definition or {})
                    if str(definition.get("relationship") or "") != "instance":
                        continue
                    instance_type = str(
                        definition.get("instance_type") or ""
                    )
                    if not instance_type or not current_type:
                        continue
                    if direction == "children":
                        endpoint_types = (
                            str(definition.get("from") or ""),
                            current_type,
                        )
                    else:
                        endpoint_types = (
                            current_type,
                            str(definition.get("to") or ""),
                        )
                    if (
                        all(endpoint_types)
                        and instance_type not in endpoint_types
                    ):
                        catalog.setdefault(
                            instance_type, list(endpoint_types)
                        )
        return catalog

    @classmethod
    def _query(
            cls, feed_filter, project_code, offset, page_size, day="",
            include_day_counts=False, selected_users=None,
            counts_only=False, counts_from_day="", bypass_cache=False,
            exclude_own_activity=False, invalidate_cache=True):
        from thlib import server_cache
        import thlib.tactic_classes as tc
        from thlib.environment import env_server

        login = str(env_server.get_user() or "")
        excluded_login = login if exclude_own_activity else ""
        limit = page_size + 1
        kinds = {
            "publications": ("publication",),
            "notes": ("note",),
            "my_tasks": ("task",),
            "my_objects": JOURNAL_ACTIVITY_KINDS,
            "all": JOURNAL_ACTIVITY_KINDS,
        }.get(feed_filter, ())
        cache_key = json.dumps(
            {
                "contract": cls.CACHE_CONTRACT,
                "filter": feed_filter,
                "offset": int(offset or 0),
                "limit": int(page_size or 0),
                "day": str(day or ""),
                "dayCounts": bool(include_day_counts),
                "users": sorted(str(value) for value in selected_users or ()),
                "countsOnly": bool(counts_only),
                "countsFromDay": str(counts_from_day or ""),
                "excludeLogin": excluded_login.casefold(),
            },
            ensure_ascii=False, separators=(",", ":"), sort_keys=True,
        )
        # A calendar-only recount must not invalidate the concurrently loaded
        # feed page. Refreshing that page owns activity-domain invalidation.
        if bypass_cache and not counts_only and invalidate_cache:
            server_cache.invalidate_domains(("activity",), project_code)
        cache_token = server_cache.token("activity", project_code)
        cached = None if bypass_cache else server_cache.read_entry(
            "activity", cache_key, project_code,
        )
        if isinstance(cached, dict):
            return cached
        instance_relations = (
            cls._instance_relation_catalog(project_code)
            if {"create", "delete"}.intersection(kinds)
            else {}
        )
        records = tc.get_user_recent_activity(
            login if feed_filter == "my_objects" else "",
            project_code=project_code,
            limit=limit,
            offset=offset,
            kinds=kinds,
            assigned_login=login if feed_filter == "my_tasks" else "",
            include_day_counts=include_day_counts,
            counts_only=counts_only,
            counts_from_day=counts_from_day,
            day=day,
            logins=list(selected_users or ()),
            instance_relations=instance_relations,
            exclude_login=excluded_login,
        )
        if isinstance(records, dict):
            normalized_records = [
                activity_record(record)
                for record in records.get("records") or ()
            ]
            payload = {
                "records": (
                    cls._without_actor(normalized_records, login)
                    if exclude_own_activity else normalized_records
                ),
            }
            if include_day_counts:
                payload["dayCounts"] = list(records.get("dayCounts") or ())
                payload["countsFromDay"] = str(
                    records.get("countsFromDay") or ""
                )
            result = payload
        else:
            normalized_records = [
                activity_record(record) for record in records or ()
            ]
            result = {
                "records": (
                    cls._without_actor(normalized_records, login)
                    if exclude_own_activity else normalized_records
                ),
                **({"dayCounts": []} if include_day_counts else {}),
            }
        if cache_token is not None:
            server_cache.write_entry(
                "activity", cache_key, result, project_code,
                expected_token=cache_token,
            )
        return result

    def _calendar_ready(self, request_id, result):
        if request_id != self._calendar_request_id:
            return
        payload = dict(result or {}) if isinstance(result, dict) else {}
        counts_from_day = str(payload.get("countsFromDay") or "")
        if counts_from_day:
            self._calendar_counts = {
                day_key: count
                for day_key, count in self._calendar_counts.items()
                if day_key < counts_from_day
            }
        else:
            self._calendar_counts = {}
        self._calendar_counts.update({
            str(record.get("dateKey") or ""): int(record.get("count") or 0)
            for record in payload.get("dayCounts") or ()
            if record.get("dateKey")
        })
        # Keep the complete history visible while a newer invalidation is
        # recounted, but never persist that in-flight result as current truth.
        stale = self._calendar_invalidated_during_request
        if not stale:
            self._save_calendar_counts()
            self._calendar_bypass_cache = False
        self._calendar_counts_loaded = not stale
        self._calendar_cache_complete = not stale
        self._calendar_busy = False
        self._calendar_request_id = ""
        self._calendar_worker = None
        self._validate_selected_day()
        self.stateChanged.emit()
        if stale:
            self.calendarInvalidated.emit()

    def _calendar_failed(self, request_id, error):
        if request_id != self._calendar_request_id:
            return
        self._error, stacktrace = _worker_error(error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                self._error, stacktrace=stacktrace,
                group="communication/feed/calendar",
            )
        self._calendar_busy = False
        self._calendar_request_id = ""
        self._calendar_worker = None
        self.stateChanged.emit()

    def _normalize_record(self, source):
        return activity_record(source, clock=self._clock)

    def _clock_changed(self):
        if not self._all_records:
            return
        self._replace_records(self._present_records([
            self._normalize_record(record) for record in self._all_records
        ]))

    @Slot(object)
    def apply_server_batch(self, batch):
        activity = list((batch or {}).get("activity") or [])
        initial = bool((batch or {}).get("initialActivity"))
        self._track_activity(activity, initial)
        self._request_notification_enrichment()
        visible_activity = (
            self._without_own_activity(activity)
            if self._exclude_own_activity else activity
        )
        if initial or not visible_activity:
            return
        # The update service deliberately publishes lightweight transport
        # records.  They are sufficient for unread tracking and cache
        # invalidation, but not for user-facing cards: check-in alone can emit
        # snapshot, file, and change_timestamp rows before their parent titles
        # and audit details are resolved.  Reconcile through the same enriched
        # query as Refresh so live and manually refreshed presentation cannot
        # diverge.
        self._live_refresh_pending = True
        self._reconcile_live_activity()

    def _reconcile_live_activity(self):
        if (
                not self._live_refresh_pending
                or not self._visible
                or self._busy):
            return
        self._load(reset=True, bypass_cache=True)

    def _ready(self, request_id, result, reset, offset):
        if request_id != self._request_id:
            return
        payload = dict(result or {}) if isinstance(result, dict) else {}
        source_records = payload.get("records") if payload else result
        presented_records = self._present_records([
            self._normalize_record(record) for record in source_records or ()
        ])
        if self._pending_notification_events:
            self._publish_pending_notifications(
                presented_records, tuple(self._pending_notification_events),
            )
        records = self._feed_records(presented_records)
        self._has_more = len(records) > self._page_size
        records = records[:self._page_size]
        existing = [] if reset else list(self._all_records)
        self._replace_records(
            existing + records,
            payload.get("dayCounts")
            if payload and "dayCounts" in payload else None,
        )
        self._offset = offset + len(records)
        self._finish()

    @Slot(int)
    def open_item(self, row):
        record = self.model.get(row)
        if record.get("taskCode") and self._tasks is not None:
            target_key = str(record.get("targetSearchKey") or "")
            if target_key:
                self._tasks.open_object_context(
                    target_key,
                    str(record.get("taskCode") or ""),
                    str(record.get("process") or ""),
                )
            return
        search_key = str(record.get("searchKey") or "")
        if search_key and self._skey_previews is not None:
            process = str(record.get("process") or "").strip()
            if not process:
                process = str(
                    record.get("context") or ""
                ).partition("/")[0]
            self._skey_previews.open_in_context(
                search_key,
                str(record.get("targetSearchKey") or ""),
                process,
            )
        elif search_key:
            self._application.open_search_key(search_key)

    @Slot(int)
    def open_target(self, row):
        record = self.model.get(row)
        if record.get("taskCode"):
            self.open_item(row)
            return
        search_key = str(record.get("targetSearchKey") or "")
        if search_key:
            self._application.open_search_key(search_key)

    def _failed(self, request_id, error):
        if request_id != self._request_id:
            return
        self._error, stacktrace = _worker_error(error)
        debug_log = getattr(self._application, "debug_log", None)
        if debug_log:
            debug_log.raise_error(
                self._error, stacktrace=stacktrace, group="communication/feed"
            )
        self._finish(reconcile_live=False)

    def _finish(self, reconcile_live=True):
        self._busy = False
        self._worker = None
        self.stateChanged.emit()
        if reconcile_live:
            self._reconcile_live_activity()
