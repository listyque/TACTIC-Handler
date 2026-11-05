"""Queue selection and shot inclusion, shared by native and web commands."""
from PySide6.QtCore import Slot


class SelectionMixin:
    @Slot(str, int)
    def selectQueueRange(self, identity, modifiers):
        self._select_queue(identity, modifiers, False)

    def _select_queue(self, identity, modifiers=0, reveal=False):
        if modifiers & ~3:
            raise ValueError('Unknown selection modifiers')
        entry, job = self._find(identity)
        if identity and entry is None:
            return
        previous = self._selected_queue
        if job is None:
            self._selected_shots.clear()
            self._selection_anchor = ''
        elif modifiers & 1:
            anchor_entry, anchor_job = self._find(self._selection_anchor)
            if anchor_entry is entry and anchor_job is not None:
                start, end = sorted((entry['jobs'].index(anchor_job), entry['jobs'].index(job)))
                selected = {row['id'] for row in entry['jobs'][start:end+1]}
                self._selected_shots = self._selected_shots | selected if modifiers & 2 else selected
            else:
                self._selected_shots = {identity}
                self._selection_anchor = identity
        elif modifiers & 2:
            self._selected_shots.symmetric_difference_update({identity})
            self._selection_anchor = identity
        else:
            self._selected_shots = {identity}
            self._selection_anchor = identity
        self._selected_queue = identity
        self._select_episode(entry['episodeKey'] if entry else '')
        self._update_selection()
        if reveal:
            index = self._queue_rows.get(identity, -1)
            self.queueSelected.emit(index, False)
        if previous != identity:
            self.logScopeChanged.emit()
            self.logChanged.emit()
            self.previewsChanged.emit()

    def _update_selection(self):
        selected = set(self._selected_shots)
        entry, job = self._find(self._selected_queue)
        if entry is not None and job is None:
            selected.add(entry['id'])
        previous = getattr(self, '_highlighted_rows', set())
        for identity in previous | selected:
            index = self._queue_rows.get(identity)
            if index is not None:
                self.queue.set_value(index, 'selected', identity in selected)
        self._highlighted_rows = selected
        self.detailChanged.emit()

    @Slot(str)
    def selectAllShots(self, identity):
        entry, job = self._find(identity)
        if entry is None:
            return
        self._selected_shots = {row['id'] for row in entry['jobs']}
        self._selection_anchor = entry['jobs'][0]['id'] if entry['jobs'] else ''
        self._update_selection()

    @Slot(str, int, int)
    def navigateQueue(self, identity, delta, modifiers):
        index = self._queue_rows.get(identity, -1) + delta
        record = self.queue.get(index)
        if record:
            self._select_queue(record['jobId'], modifiers, True)

    def _episode_include_state(self, entry):
        jobs = [job for job in entry['jobs'] if 'include' in self._allowed_actions(entry,job)]
        count = sum(job['state'] != 'skipped' for job in jobs)
        return 2 if jobs and count == len(jobs) else 1 if count else 0

    @Slot(str, bool)
    def setEpisodeIncluded(self, identity, included):
        entry, job = self._find(identity)
        if entry is not None:
            self._set_shots_included([(entry,row) for row in entry['jobs']], included)

    @Slot(bool)
    def setSelectedIncluded(self, included):
        self._set_shots_included([(entry,job) for entry in self._entries for job in entry['jobs']
                                 if job['id'] in self._selected_shots], included)

    def _set_shots_included(self, targets, included):
        changed = False
        for entry, job in targets:
            if 'include' not in self._allowed_actions(entry,job):
                continue
            state = 'waiting' if included else 'skipped'
            if job['state'] == state:
                continue
            job.update(state=state, stage='Waiting' if included else 'Excluded')
            if included and entry['state'] in {'completed','failed','cancelled','skipped'}:
                entry.update(state='waiting',stage='Ready · press Start queue',prepared=False,error='',startRequested=False)
            changed = True
        if changed:
            self._flush_queue()
            self._pump()
