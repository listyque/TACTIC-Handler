"""Batch catalog controller owner."""
from __future__ import annotations

from PySide6.QtCore import Slot
from .domain import (
    _discover_queue,
    _query_episodes,
    _queue_entry,
    _set_episode_task_status,
    _shot_job,
)
from .queue_state import _TERMINAL


class CatalogControllerMixin:
    def _replace_episode_filters(self, records):
        current = {
            row["value"]: row["active"]
            for row in self.episode_filters.records()
        }
        self.episode_filters.replace(
            [
                {
                    **record,
                    "title": record["title"] or self._text("No render status"),
                    "active": current.get(
                        record["value"],
                        record["value"] in self._filter_preferences if self._filter_preferences is not None
                        else record["value"] != self._config["terminal_status"],
                    ),
                }
                for record in records
            ]
        )
        self.episodeFiltersChanged.emit()

    @Slot(str)
    def toggleEpisodeStatusFilter(self, status):
        records = self.episode_filters.records()
        row = next(
            (index for index, value in enumerate(records) if value["value"] == status),
            -1,
        )
        if row < 0:
            return
        self.episode_filters.set_value(row, "active", not records[row]["active"])
        self.episodeFiltersChanged.emit()
        self._filter_episodes()
        self.catalogFilterChanged.emit()

    @Slot(str)
    def setEpisodeSearch(self, value):
        self._episode_search = str(value).strip().casefold()
        self._filter_episodes()
        self.catalogFilterChanged.emit()

    def _filter_episodes(self):
        statuses = set(self.visibleEpisodeStatuses)
        queued = {entry["episodeKey"] for entry in self._entries}
        self.episodes.replace([dict(row, selected=row["searchKey"] == self._selected_episode)
            for row in self._catalog if row["renderStatus"] in statuses
            and row["searchKey"] not in queued
            and (not self._episode_search or self._episode_search in
                 (row["title"] + " " + row["subtitle"] + " " + row["code"]).casefold())])
        self.stateChanged.emit()

    @Slot()
    def refresh(self):
        if self._offline or not self._ready or self._close_requested:
            return
        if self._busy:
            self._refresh_pending = True
            return
        self._poll_timer.stop()
        self._generation += 1
        generation = self._generation
        self._busy = True
        self.stateChanged.emit()
        config = dict(self._config)
        self._submit(
            lambda: _query_episodes(
                self._api,
                self._project_code,
                config,
            ),
            lambda payload: self._episodes_ready(generation, payload),
            lambda error: self._refresh_failed(generation, error),
        )

    def _refresh_failed(self, generation, error):
        if generation != self._generation:
            return
        self._busy = False
        self._error_message(error)
        self._finish_refresh()

    def _finish_refresh(self):
        if self._refresh_pending:
            self._refresh_pending = False
            self.refresh()
        else:
            self._schedule_poll()

    def _schedule_poll(self):
        if self._watch_server and not self._close_requested:
            self._poll_timer.start(max(5, int(self._config["update_interval"])) * 1000)

    def _episodes_ready(self, generation, payload):
        if generation != self._generation:
            return
        records = payload["episodes"]
        self._catalog = records
        queued_records = payload["queuedEpisodes"]
        local_queue = {
            entry["episodeKey"]
            for entry in self._entries
            if entry["state"] not in _TERMINAL
        }
        queued_keys = {entry["episodeKey"] for entry in self._entries}
        visible_records = []
        for index, row in enumerate(records):
            row["selected"] = row["searchKey"] == self._selected_episode
            row["queued"] = row["searchKey"] in local_queue
            if row["searchKey"] in queued_keys:
                self._hidden_episodes[row["searchKey"]] = (index, row)
            else:
                visible_records.append(row)
        self._replace_episode_filters(payload["filters"])
        previews = {
            row["searchKey"]: row.get("previewUrl", "")
            for row in [*records, *queued_records]
        }
        for entry in self._entries:
            if entry["episodeKey"] in previews:
                entry["previewUrl"] = previews[entry["episodeKey"]]
        if self._entries:
            self._publish_queue()
        self._filter_episodes()
        self._busy = False
        previous_seen = set(self._server_seen)
        queued = {row["searchKey"] for row in queued_records}
        self._server_seen.intersection_update(
            queued
            | {
                entry["episodeKey"]
                for entry in self._entries
                if entry["state"] not in _TERMINAL
            }
        )
        if self._watch_server:
            for row in queued_records:
                if row["searchKey"] not in self._server_seen:
                    self._server_seen.add(row["searchKey"])
                    self._enqueue(
                        row["searchKey"], False, origin="server", episode=row
                    )
        if self._server_seen != previous_seen:
            self._persist()
        self.stateChanged.emit()
        self._finish_refresh()

    @Slot(int)
    def selectEpisode(self, row):
        key = self.episodes.get(row).get("searchKey")
        if not key:
            return
        entry = next(
            (entry for entry in reversed(self._entries) if entry["episodeKey"] == key),
            None,
        )
        if entry:
            self.selectQueue(entry["id"], True)
        else:
            self._selected_queue = ""
            self._select_episode(key)
            self._publish_queue()
            self.queueSelected.emit(-1, False)
            self.logScopeChanged.emit()
            self.logChanged.emit()
            self._status = "Use + to add this episode to the queue"
            self.stateChanged.emit()

    @Slot(int, bool)
    def renderEpisode(self, row, test_render=False):
        key = self.episodes.get(row).get("searchKey")
        if key:
            self._enqueue(key, bool(test_render))

    def _enqueue(self, key, test_render, origin="manual", episode=None):
        if not self._ready or self._close_requested:
            return
        existing = next(
            (
                entry
                for entry in self._entries
                if entry["episodeKey"] == key and entry["state"] not in _TERMINAL
            ),
            None,
        )
        if existing:
            self.selectQueue(existing["id"])
            self._status = "Episode already queued"
            self.stateChanged.emit()
            return
        if len(self._entries) >= 200:
            self._error_message(
                ValueError("Queue history is full; clear completed entries")
            )
            return
        episode = episode or self.episodes.lookup("searchKey", key)
        entry = _queue_entry(key, episode, test_render, origin)
        self._entries.append(entry)
        for row, record in enumerate(self.episodes.records()):
            if record["searchKey"] == key:
                self._hidden_episodes[key] = (row, record)
                self.episodes.remove(row)
                break
        if not test_render:
            self._server_seen.add(key)
        self.selectQueue(entry["id"])
        self._discover_entry(entry)

    def _discover_entry(self, entry):
        config = dict(self._config)
        entry.update(state="discovering", stage="Loading shot list", error="")
        self._flush_queue()
        if self._discovery_entry is not None:
            return
        self._discovery_entry = entry
        status = config["queue_statuses"][-1] if (entry["origin"] == "manual") else ""
        self._submit(
            lambda: _discover_queue(
                self._api, entry["episodeKey"], config, entry["test"], status
            ),
            lambda records: self._discovery_finished(entry, records),
            lambda error: self._discovery_failed(entry, error),
        )

    def _discovery_finished(self, entry, records):
        try:
            if entry not in self._entries or entry["state"] == "cancelled":
                return
            jobs = [_shot_job(row, entry["test"]) for row in records]
            if not jobs:
                raise ValueError("No shots to render")
            entry.update(jobs=jobs, state="waiting", stage="Waiting")
            self._log(f"{entry['title']}: {len(jobs)} shots queued", entry)
            self._flush_queue()
            self._pump()
        except Exception as error:
            self._mark_discovery_failed(entry, error)
        finally:
            self._continue_discovery(entry)

    def _discovery_failed(self, entry, error):
        try:
            self._mark_discovery_failed(entry, error)
        finally:
            self._continue_discovery(entry)

    def _mark_discovery_failed(self, entry, error):
        if entry not in self._entries or entry["state"] == "cancelled":
            return
        entry.update(state="failed", stage="Discovery failed", error=str(error))
        self._error_message(error)
        self._flush_queue()
        self._pump()

    def _continue_discovery(self, entry):
        if self._discovery_entry is entry:
            self._discovery_entry = None
        pending = next(
            (row for row in self._entries if row["state"] == "discovering"),
            None,
        )
        if pending is not None and not self._close_requested:
            self._discover_entry(pending)

    @Slot(int, str)
    def setEpisodeStatus(self, row, status):
        key = self.episodes.get(row).get("searchKey")
        if key:
            process = self._config["render_process"]
            self._submit(
                lambda: _set_episode_task_status(
                    self._api.sobject(key), process, status
                ),
                lambda _value: self.refresh(),
            )
