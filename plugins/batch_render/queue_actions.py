"""Batch queue actions owner."""
from __future__ import annotations

import uuid
from PySide6.QtCore import Slot
from .domain import _parse_frame_spec
from .queue_state import _TERMINAL, _ACTIVE


class QueueActionsMixin:
    @Slot(str)
    def cancelQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return
        if entry is self._active_entry and (
            job is None or job is self._active_job or job["id"] == self._run_only
        ):
            self._render_pause.clear()
            self._cancel_job_only = job is not None
            self._cancel.set()
            entry.update(stage="Stopping · waiting for active operation")
            if self._active_job:
                self._active_job["stage"] = (
                    "Stopping renderer / finishing current transfer"
                )
            elif job:
                job.update(state="cancelled", stage="Cancelled")
            if self._stage_operation is None:
                self._cancel_remainder()
        else:
            for row in [job] if job else [entry, *entry["jobs"]]:
                if row["state"] not in _TERMINAL:
                    row.update(state="cancelled", stage="Cancelled")
        self._flush_queue()

    @Slot()
    def interruptRender(self):
        self._paused = True
        self._render_pause.clear()
        self._run_only = ""
        self._status = "Stopping queue" if self._active_entry else "Queue stopped"
        if self._active_entry:
            self.cancelQueue(self._active_entry["id"])
        else:
            self.stateChanged.emit()

    @Slot(str)
    def retryQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None or entry["state"] in _ACTIVE:
            return
        if entry is self._active_entry and self._stage_operation is not None:
            return
        if entry.get("saveFailed") or any(
            row.get("saveFailed") for row in ([job] if job else entry["jobs"])
        ):
            self._error_message(
                ValueError(
                    "Server save was not confirmed. Check TACTIC before rerendering; add a new run explicitly."
                )
            )
            return
        if not entry["jobs"]:
            self._discover_entry(entry)
            return
        targets = [
            row
            for row in ([job] if job else entry["jobs"])
            if row["state"] in {"failed", "cancelled"}
        ]
        if not targets:
            return
        for row in targets:
            self._reset_for_retry(row)
        entry.update(
            state="waiting",
            stage="Retry queued",
            prepared=False,
            error="",
            logPath="",
            preparationErrors=[],
        )
        self.selectQueue(entry["id"])
        self._persist()
        self._pump()

    @staticmethod
    def _reset_for_retry(job):
        job.update(
            id=uuid.uuid4().hex,  # Keep the previous attempt's log file.
            state="waiting",
            stage="Waiting",
            progress=0.0,
            error="",
            frame="",
            framesDone=0,
            renderElapsed=0.0,
            pid="",
            logPath="",
            renderOutput="",
            renderFiles=[],
            preparationErrors=[],
            command="",
            exitCode="",
            attempt=job.get("attempt", 1) + 1,
        )

    @Slot(str)
    def holdQueue(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return
        active_job = self._active_job
        if (
            entry is self._active_entry
            and active_job is not None
            and (job is None or job is active_job)
            and active_job["state"] in {"rendering", "paused"}
        ):
            paused = not self._render_pause.is_set()
            state = "paused" if paused else "rendering"
            stage = "Render pause requested" if paused else "Resuming render"
            if paused:
                self._render_pause.set()
                self._status = f"Render paused: {active_job['title']}"
            else:
                self._render_pause.clear()
                self._status = (
                    "Pause after current shot" if self._paused else "Queue running"
                )
            active_job.update(state=state, stage=stage)
            entry.update(state=state, stage=stage)
            self._flush_queue()
            self.stateChanged.emit()
            return
        row = job or entry
        if row["state"] not in {"waiting", "held"}:
            return
        row["state"] = "waiting" if row["state"] == "held" else "held"
        row["stage"] = row["state"].capitalize()
        if job is not None and entry["state"] == "held" and row["state"] == "waiting":
            entry.update(state="waiting", stage="Waiting")
        self._flush_queue()
        self._pump()

    @Slot(str, int)
    def moveQueue(self, identity, delta):
        movable = self._movable_queue_row(identity)
        if movable is None:
            return
        values, row = movable
        index = values.index(row)
        destination = max(0, min(len(values) - 1, index + delta))
        values.insert(destination, values.pop(index))
        self._flush_queue()

    @Slot(str, str)
    def moveQueueTo(self, identity, target_identity):
        movable = self._movable_queue_row(identity)
        _target_entry, target_job = self._find(target_identity)
        if movable is None:
            return
        values, row = movable
        target = _target_entry if values is self._entries else target_job
        if target not in values or target is row:
            return
        destination = values.index(target)
        values.insert(destination, values.pop(values.index(row)))
        self._flush_queue()

    def _movable_queue_row(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return None
        row = job or entry
        if "move" not in self._allowed_actions(entry, job):
            return None
        return (entry["jobs"] if job else self._entries), row

    def _remove_entries(self, entries):
        if not entries:
            return
        identities = {
            identity
            for entry in entries
            for identity in [entry["id"], *(job["id"] for job in entry["jobs"])]
        }
        discarded = {id(entry) for entry in entries}
        removed_ids = {entry["id"] for entry in entries}
        if self._pending_removal in removed_ids:
            self._pending_removal = ""
        self._entries = [entry for entry in self._entries if id(entry) not in discarded]
        queued_keys = {entry["episodeKey"] for entry in self._entries}
        restored = self.episodes.records()
        restored_rows = []
        for entry in entries:
            key = entry["episodeKey"]
            if key in queued_keys:
                continue
            hidden = self._hidden_episodes.pop(key, None)
            if hidden:
                row, episode = hidden
                episode.update(selected=False, queued=False)
                restored_rows.append((row, episode))
        for row, episode in sorted(restored_rows):
            restored.insert(min(row, len(restored)), episode)
        self.episodes.replace(restored)
        if self._catalog:
            self._filter_episodes()
        self._events = [event for event in self._events if event[0] not in identities]
        if self._selected_queue in identities:
            self._selected_queue = ""
            self.logScopeChanged.emit()
            self.logChanged.emit()
        self._flush_queue()

    @Slot()
    def clearCompleted(self):
        self._remove_entries(
            [
                entry
                for entry in self._entries
                if entry["state"] in {"completed", "cancelled"}
            ]
        )

    @Slot(str, result=bool)
    def removeEpisode(self, identity):
        entry, job = self._find(identity)
        if (
            entry is None
            or job is not None
            or "remove" not in self._allowed_actions(entry)
        ):
            return False
        if entry is self._active_entry:
            self._pending_removal = entry["id"]
            self.cancelQueue(entry["id"])
            self._status = f"Stopping and removing: {entry['title']}"
            self.stateChanged.emit()
            return True
        self._remove_entries([entry])
        self._status = f"Removed from queue: {entry['title']}"
        self.stateChanged.emit()
        self._pump()
        return True

    @Slot(str)
    @Slot(str, bool)
    def selectQueue(self, identity, align_top=False):
        self._select_queue(identity, 0, bool(align_top))

    def _select_episode(self, key, reveal=False):
        self._selected_episode = key
        episode_index = -1
        for index, row in enumerate(self.episodes.records()):
            selected = row["searchKey"] == key
            self.episodes.set_value(index, "selected", selected)
            if selected:
                episode_index = index
        if reveal:
            self.episodeSelected.emit(episode_index)

    @Slot(str)
    def toggleExpanded(self, identity):
        entry, job = self._find(identity)
        if entry is not None and job is None:
            entry["expanded"] = not entry["expanded"]
            self._publish_queue()

    @Slot(str)
    def toggleIncluded(self, identity):
        entry, job = self._find(identity)
        if entry is None or job is None:
            return
        included = job['state'] == 'skipped'
        if identity in self._selected_shots and len(self._selected_shots) > 1:
            self.setSelectedIncluded(included)
        else:
            self._set_shots_included([(entry,job)],included)

    @Slot(str, str, result=bool)
    def setFrameSpec(self, identity, value):
        entry, job = self._find(identity)
        if entry is None or "frames" not in self._allowed_actions(entry, job):
            return False
        try:
            ranges = _parse_frame_spec(value, job["start"], job["end"])
        except ValueError as error:
            self._error_message(error)
            return False
        job["frameRanges"] = [list(pair) for pair in ranges]
        job["frameSpec"] = value.strip()
        self._error = ""
        self._flush_queue()
        self.stateChanged.emit()
        return True
