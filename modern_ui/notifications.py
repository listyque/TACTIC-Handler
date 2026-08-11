from __future__ import annotations

import time
import uuid

from PySide6.QtCore import QDateTime, QObject, Property, QTimer, Qt, Signal, Slot

from .workspace_models.records import RecordListModel


class NotificationController(QObject):
    changed = Signal()

    _history_roles = (
        "notificationId", "kind", "group", "message", "detail",
        "timestamp",
    )
    _history_groups = {"all", "server", "repository", "checkin", "client"}

    def __init__(
        self, application, checkin=None, communication=None, tasks=None,
        messages=None,
        parent=None,
    ):
        super().__init__(parent)
        self._application = application
        self._messages = messages
        self.model = RecordListModel((
            "notificationId", "kind", "message", "detail", "progress",
            "dismissible", "action", "actionData",
        ))
        self.history = RecordListModel(self._history_roles)
        self.filtered_history = RecordListModel(self._history_roles)
        self._history_group = "all"
        self._seen_activity = set()
        self._timers = {}
        self._recent = {}
        self._active_signatures = set()
        self._controller_errors = {}
        self._last_progress_message = ""
        application.notification_changed.connect(self.notify)
        application.loading_changed.connect(self._loading_changed)
        application.activity_log_changed.connect(self._activity_changed)
        application.repository_sync.downloads_finished.connect(
            lambda: self._push(
                "complete", "Repository downloads completed",
                group="repository",
            )
        )
        application.repository_sync.task_failed.connect(
            lambda _task_id: self._push(
                "error", "A repository download failed",
                group="repository",
            )
        )
        if checkin:
            checkin.operationFinished.connect(self._checkin_finished)
        if communication:
            communication.stateChanged.connect(
                lambda: self._controller_error(
                    "communication", communication.error
                )
            )
        if tasks:
            tasks.stateChanged.connect(
                lambda: self._controller_error("tasks", tasks.error)
            )
        if messages:
            messages.newMessage.connect(self._new_message)

    @Property(int, notify=changed)
    def count(self):
        return len(self.model._records)

    @Property(str, notify=changed)
    def historyGroup(self):
        return self._history_group

    @Property("QVariantList", constant=True)
    def historyGroups(self):
        return [
            {"key": "all", "title": "All"},
            {"key": "server", "title": "Server"},
            {"key": "repository", "title": "Repository sync"},
            {"key": "checkin", "title": "Check-in"},
            {"key": "client", "title": "Client"},
        ]

    @Slot(str)
    def set_history_group(self, group):
        group = str(group or "all")
        if group not in self._history_groups or group == self._history_group:
            return
        self._history_group = group
        self._rebuild_filtered_history()
        self.changed.emit()

    @staticmethod
    def _kind_for_message(message):
        text = str(message or "").lower()
        if any(word in text for word in (
            "error", "failed", "cannot ", "exception", "unavailable",
        )):
            return "error"
        if any(word in text for word in (
            "warning", "invalid", "missing", "not available",
        )):
            return "warning"
        if any(word in text for word in (
            "completed", "saved", "updated", "deleted", "finished",
        )):
            return "complete"
        return "info"

    @Slot(str)
    def notify(self, message):
        message = str(message or "").strip()
        if message:
            self._push(self._kind_for_message(message), message, group="client")

    @Slot(str, str)
    def push(self, kind, message):
        self._push(kind, message)

    def _push(
        self, kind, message, detail="", action="", action_data="",
        group="client",
    ):
        kind = kind if kind in {
            "info", "warning", "error", "progress", "complete",
        } else "info"
        message = str(message or "").strip()
        if not message:
            return
        now = time.monotonic()
        signature = f"{kind}:{message}"
        if (
            signature in self._active_signatures
            or now - self._recent.get(signature, 0.0) < 5.0
        ):
            return
        self._recent[signature] = now
        self._recent = {
            key: stamp for key, stamp in self._recent.items()
            if now - stamp < 30.0
        }
        record = {
            "notificationId": uuid.uuid4().hex,
            "kind": kind,
            "message": message,
            "detail": str(detail or ""),
            "progress": -1.0,
            "dismissible": True,
            "action": str(action or ""),
            "actionData": str(action_data or ""),
        }
        self._append_history({
            "notificationId": record["notificationId"],
            "kind": kind,
            "group": group,
            "message": message,
            "detail": str(detail or ""),
            "timestamp": QDateTime.currentDateTime().toString(Qt.ISODate),
        })
        records = list(self.model._records)
        records.append(record)
        while len(records) > 3:
            removed = records.pop(0)
            self._stop_timer(removed["notificationId"])
        self.model.replace(records)
        self._sync_active_signatures()
        self._start_timer(
            record["notificationId"],
            5000 if kind in {"error", "warning"} else 3200,
        )
        self.changed.emit()

    def _new_message(self, conversation_id, title, excerpt):
        self._push(
            "info",
            "New message in {0}".format(title or "Messages"),
            excerpt,
            "messages",
            conversation_id,
            "server",
        )

    @staticmethod
    def _activity_group(message):
        value = str(message or "").casefold()
        if any(token in value for token in (
            "repository", "repo sync", "download", "local file",
        )):
            return "repository"
        if any(token in value for token in (
            "check-in", "checkin", "commit queue", "snapshot upload",
        )):
            return "checkin"
        if any(token in value for token in (
            "qml", "qt ", "warning", "missing", "directwrite",
        )):
            return "client"
        return "server"

    def _append_history(self, record):
        history = list(self.history._records)
        history.insert(0, dict(record))
        self.history.replace(history[:200])
        self._rebuild_filtered_history()

    def _rebuild_filtered_history(self):
        records = list(self.history._records)
        if self._history_group != "all":
            records = [
                record for record in records
                if record.get("group") == self._history_group
            ]
        self.filtered_history.replace(records)

    def _activity_changed(self):
        records = list(self._application.activity_log)
        for message in records:
            message = str(message or "").strip()
            if not message or message in self._seen_activity:
                continue
            self._seen_activity.add(message)
            self._append_history({
                "notificationId": "activity:" + uuid.uuid4().hex,
                "kind": self._kind_for_message(message),
                "group": self._activity_group(message),
                "message": message,
                "detail": "",
                "timestamp": QDateTime.currentDateTime().toString(Qt.ISODate),
            })
        if len(self._seen_activity) > 300:
            self._seen_activity = set(records[-100:])
        self.changed.emit()

    def _upsert_progress(self, message):
        records = list(self.model._records)
        row = next(
            (
                index for index, record in enumerate(records)
                if record["notificationId"] == "application-progress"
            ),
            -1,
        )
        record = {
            "notificationId": "application-progress",
            "kind": "progress",
            "message": str(message or "Working"),
            "detail": "",
            "progress": -1.0,
            "dismissible": False,
            "action": "",
            "actionData": "",
        }
        if row >= 0:
            records[row] = record
        else:
            records.append(record)
            records = records[-3:]
        self.model.replace(records)
        self.changed.emit()

    def _loading_changed(self):
        if self._application.loading:
            self._last_progress_message = (
                self._application.loading_message or "Working"
            )
            self._upsert_progress(self._last_progress_message)
            return
        records = [
            record for record in self.model._records
            if record["notificationId"] != "application-progress"
        ]
        self.model.replace(records)
        self.changed.emit()

    def _controller_error(self, source, message):
        message = str(message or "").strip()
        previous = self._controller_errors.get(source, "")
        self._controller_errors[source] = message
        if message and message != previous:
            self._push("error", message, group="server")

    def _checkin_finished(self, succeeded, error):
        if succeeded:
            self._push("complete", "Check-in completed", group="checkin")
        elif error:
            self._push("error", str(error), group="checkin")

    def _start_timer(self, notification_id, interval):
        self._stop_timer(notification_id)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(interval)
        timer.timeout.connect(
            lambda: self.dismiss_id(notification_id)
        )
        self._timers[notification_id] = timer
        timer.start()

    def _stop_timer(self, notification_id):
        timer = self._timers.pop(notification_id, None)
        if timer:
            timer.stop()
            timer.deleteLater()

    @Slot(int)
    def dismiss(self, row):
        if 0 <= row < len(self.model._records):
            self.dismiss_id(
                self.model._records[row]["notificationId"]
            )

    @Slot(int)
    def activate(self, row):
        if not 0 <= row < len(self.model._records):
            return
        record = self.model._records[row]
        if record.get("action") == "messages":
            self._messages.open_conversation(
                record.get("actionData") or ""
            )
        self.dismiss(row)

    def dismiss_id(self, notification_id):
        self._stop_timer(notification_id)
        records = [
            record for record in self.model._records
            if record["notificationId"] != notification_id
        ]
        if len(records) != len(self.model._records):
            self.model.replace(records)
            self._sync_active_signatures()
            self.changed.emit()

    def _sync_active_signatures(self):
        self._active_signatures = {
            f"{record['kind']}:{record['message']}"
            for record in self.model._records
            if record.get("kind") != "progress"
        }

    @Slot()
    def clear(self):
        for notification_id in list(self._timers):
            self._stop_timer(notification_id)
        self.model.clear()
        self._active_signatures.clear()
        self.changed.emit()

    @Slot()
    def clear_history(self):
        self.history.clear()
        self.filtered_history.clear()
        self.changed.emit()

    def shutdown(self):
        self.clear()
