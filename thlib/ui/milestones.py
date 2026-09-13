from __future__ import annotations

import uuid
from datetime import date

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot

from thlib.ui.workspace_models.records import RecordListModel


MILESTONE_ROLES = (
    "code", "description", "dueDate", "isNew", "dirty", "saving",
    "error", "completion", "taskCount", "completedCount", "overdueCount",
    "planStartDate", "processSummary", "plannedHours",
)


def _objects(result):
    values = result[0] if isinstance(result, tuple) else result
    if isinstance(values, dict):
        return list(values.values())
    return list(values or [])


class MilestoneController(QObject):
    """Project milestone CRUD used by task editors."""

    stateChanged = Signal()
    milestonesChanged = Signal()

    def __init__(self, application, parent=None):
        super().__init__(parent or application)
        self._application = application
        self.model = RecordListModel(MILESTONE_ROLES)
        self._records = []
        self._objects = {}
        self._originals = {}
        self._filter = ""
        self._busy = False
        self._error = ""
        self._worker = None
        self._request_id = ""
        self._loaded_project_code = ""
        project_changed = getattr(application, "project_changed", None)
        if project_changed is not None:
            project_changed.connect(self._project_changed)

    @Property(str, notify=stateChanged)
    def projectCode(self):
        return str(self._application._current_project_code or "")

    @Property(bool, notify=stateChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(int, notify=stateChanged)
    def count(self):
        return len(self._records)

    @Property(int, notify=stateChanged)
    def visibleCount(self):
        return self.model.count()

    @Property(bool, notify=stateChanged)
    def hasDirtyRows(self):
        return any(bool(record.get("dirty")) for record in self._records)

    @Property("QVariantList", notify=milestonesChanged)
    def ganttMarkers(self):
        """The project milestone plan shared by the editor and Gantt."""
        return [
            {
                "code": str(record.get("code") or ""),
                "label": str(record.get("description") or "Milestone"),
                "dueDate": str(record.get("dueDate") or ""),
                "completion": int(record.get("completion") or 0),
                "taskCount": int(record.get("taskCount") or 0),
            }
            for record in self._records
            if not record.get("isNew") and record.get("dueDate")
        ]

    @Property(bool, notify=stateChanged)
    def loaded(self):
        return bool(
            self.projectCode
            and self._loaded_project_code == self.projectCode
        )

    @Slot()
    def open_manager(self):
        self._application.open_window("milestone_manager")
        if not self.hasDirtyRows:
            self.refresh()

    @Slot()
    def refresh(self):
        project_code = self.projectCode
        if self._busy or self.hasDirtyRows or not project_code:
            return
        self._start_worker(
            self._load_records,
            (project_code,),
            self._records_loaded,
        )

    @Slot()
    def ensure_loaded(self):
        if (
                not self._busy
                and not self.hasDirtyRows
                and self._loaded_project_code != self.projectCode):
            self.refresh()

    def _project_changed(self, project_code, *_args):
        project_code = str(project_code or "")
        if project_code == self._loaded_project_code:
            return
        cancel = getattr(self._worker, "cancel", None)
        if callable(cancel):
            cancel()
        self._request_id = ""
        self._worker = None
        self._busy = False
        self._error = ""
        self._loaded_project_code = ""
        self._records = []
        self._objects = {}
        self._originals = {}
        self._apply_filter()
        self.milestonesChanged.emit()
        if project_code:
            self.refresh()

    @staticmethod
    def _load_records(project_code):
        from thlib import tactic_classes as tc

        milestones = tc.get_sobjects(
            "sthpw/milestone",
            filters=[("project_code", project_code)],
            order_bys=["due_date", "description"],
            project_code=project_code,
            include_snapshots=False,
            include_info=True,
            include_status_log=False,
        )
        milestone_objects = _objects(milestones)
        codes = [
            str((item.get_info() or {}).get("code") or "")
            for item in milestone_objects
        ]
        codes = [code for code in codes if code]
        tasks = []
        if codes:
            tasks = tc.get_sobjects(
                "sthpw/task",
                filters=[
                    ("project_code", project_code),
                    ("milestone_code", "in", "|".join(codes)),
                ],
                project_code=project_code,
                include_snapshots=False,
                include_info=False,
                include_status_log=False,
                include_progress=False,
                include_total_count=False,
            )
        return {"milestones": milestone_objects, "tasks": _objects(tasks)}

    @staticmethod
    def _task_completion(task, info):
        """Match tactic.ui.table.MilestoneCompletionWdg exactly."""
        try:
            value = task.get_attr("status").get_percent_completion()
        except (AttributeError, KeyError, TypeError, ValueError):
            value = info.get("completion") or info.get("progress") or 0
        try:
            return max(0.0, float(str(value or 0).rstrip("%")))
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _milestone_plan(cls, tasks):
        completion = []
        starts = []
        processes = []
        overdue = 0
        planned_hours = 0.0
        today = date.today().isoformat()
        for task in tasks:
            info = dict(task.get_info() or {})
            percent = cls._task_completion(task, info)
            completion.append(percent)
            start = str(info.get("bid_start_date") or "")[:10]
            end = str(info.get("bid_end_date") or "")[:10]
            if start:
                starts.append(start)
            if end and end < today and percent < 100:
                overdue += 1
            process = str(info.get("process") or info.get("context") or "")
            if process and process not in processes:
                processes.append(process)
            try:
                planned_hours += float(info.get("bid_duration") or 0)
            except (TypeError, ValueError):
                pass
        return {
            "completion": round(sum(completion) / len(completion))
                if completion else 0,
            "taskCount": len(completion),
            "completedCount": sum(value >= 100 for value in completion),
            "overdueCount": overdue,
            "planStartDate": min(starts) if starts else "",
            "processSummary": " / ".join(processes),
            "plannedHours": round(planned_hours, 1),
        }

    def _records_loaded(self, request_id, result):
        if request_id != self._request_id:
            return
        if isinstance(result, dict) and "milestones" in result:
            objects = list(result.get("milestones") or [])
            task_objects = list(result.get("tasks") or [])
        else:
            # Keep direct callback tests and older workers harmless.
            objects = _objects(result)
            task_objects = []
        tasks_by_milestone = {}
        for task in task_objects:
            info = dict(task.get_info() or {})
            milestone_code = str(info.get("milestone_code") or "")
            if milestone_code:
                tasks_by_milestone.setdefault(milestone_code, []).append(task)
        records = []
        self._objects = {}
        self._originals = {}
        for item in objects:
            info = dict(item.get_info() or {})
            code = str(info.get("code") or "")
            if not code:
                continue
            record = {
                "code": code,
                "description": str(info.get("description") or code),
                "dueDate": str(info.get("due_date") or "")[:10],
                "isNew": False,
                "dirty": False,
                "saving": False,
                "error": "",
            }
            record.update(self._milestone_plan(
                tasks_by_milestone.get(code, [])
            ))
            records.append(record)
            self._objects[code] = item
            self._originals[code] = dict(record)
        self._records = records
        self._loaded_project_code = self.projectCode
        self._apply_filter()
        self._finish_worker()
        self.milestonesChanged.emit()

    @Slot(str)
    def set_filter(self, value):
        value = str(value or "").strip().casefold()
        if value == self._filter:
            return
        self._filter = value
        self._apply_filter()

    @Slot()
    def create_milestone(self):
        if self._busy:
            return
        code = "new:" + uuid.uuid4().hex
        record = {
            "code": code,
            "description": "",
            "dueDate": date.today().isoformat(),
            "isNew": True,
            "dirty": True,
            "saving": False,
            "error": "",
            "completion": 0,
            "taskCount": 0,
            "completedCount": 0,
            "overdueCount": 0,
            "planStartDate": "",
            "processSummary": "",
            "plannedHours": 0.0,
        }
        self._records.insert(0, record)
        self._filter = ""
        self._apply_filter()

    @Slot(str, str, "QVariant")
    def stage_value(self, code, field, value):
        code = str(code or "")
        field = str(field or "")
        if self._busy or field not in {"description", "dueDate"}:
            return
        record = self._record(code)
        if not record:
            return
        value = str(value or "").strip()
        if record.get(field) == value:
            return
        record[field] = value
        original = self._originals.get(code, {})
        record["dirty"] = bool(record.get("isNew")) or any(
            str(record.get(key) or "") != str(original.get(key) or "")
            for key in ("description", "dueDate")
        )
        record["error"] = ""
        self._apply_filter()

    @Slot(str)
    def discard(self, code):
        code = str(code or "")
        record = self._record(code)
        if not record or self._busy:
            return
        if record.get("isNew"):
            self._records.remove(record)
        else:
            record.update(dict(self._originals.get(code) or record))
        self._apply_filter()

    @Slot(str)
    def save(self, code):
        code = str(code or "")
        record = self._record(code)
        if not record or self._busy:
            return
        description = str(record.get("description") or "").strip()
        due_date = str(record.get("dueDate") or "").strip()[:10]
        if not description:
            self._set_row_error(code, "Milestone name is required")
            return
        duplicate = next((
            candidate for candidate in self._records
            if str(candidate.get("code") or "") != code
            and str(candidate.get("description") or "").strip().casefold()
                == description.casefold()
        ), None)
        if duplicate is not None:
            self._set_row_error(
                code, "A milestone with this name already exists"
            )
            return
        try:
            date.fromisoformat(due_date)
        except ValueError:
            self._set_row_error(code, "Choose a valid due date")
            return
        record["saving"] = True
        record["error"] = ""
        self._apply_filter()
        if record.get("isNew"):
            operation = self._insert_record
            args = (self.projectCode, description, due_date)
        else:
            operation = self._update_record
            args = (self._objects.get(code), description, due_date)
        self._start_worker(operation, args, self._mutation_finished)

    @Slot()
    def discard_all_and_refresh(self):
        if self._busy:
            return
        self._records = [
            dict(self._originals.get(str(record.get("code") or "")) or record)
            for record in self._records
            if not record.get("isNew")
        ]
        self._apply_filter()
        self.refresh()

    @staticmethod
    def _insert_record(project_code, description, due_date):
        from thlib import tactic_classes as tc

        return tc.insert_sobjects(
            "sthpw/milestone",
            project_code,
            {
                "project_code": project_code,
                "description": description,
                "due_date": due_date,
            },
            triggers=True,
        )

    @staticmethod
    def _update_record(item, description, due_date):
        if item is None:
            raise RuntimeError("Milestone is no longer available")
        item.set_value("description", description)
        item.set_value("due_date", due_date)
        return item.commit(triggers=True)

    @Slot(str)
    def delete_milestone(self, code):
        code = str(code or "")
        record = self._record(code)
        if not record or self._busy:
            return
        if record.get("isNew"):
            self._records.remove(record)
            self._apply_filter()
            return
        self._start_worker(
            self._delete_record,
            (self.projectCode, code, self._objects.get(code)),
            self._mutation_finished,
        )

    @staticmethod
    def _delete_record(project_code, code, item):
        from thlib import tactic_classes as tc

        linked = _objects(tc.get_sobjects(
            "sthpw/task",
            filters=[("project_code", project_code), ("milestone_code", code)],
            project_code=project_code,
            limit=1,
            include_snapshots=False,
            include_info=False,
            include_status_log=False,
        ))
        if linked:
            raise RuntimeError(
                "This milestone is assigned to tasks and cannot be deleted"
            )
        if item is None:
            raise RuntimeError("Milestone is no longer available")
        return item.delete_sobject()

    def _mutation_finished(self, request_id, _result):
        if request_id != self._request_id:
            return
        for record in self._records:
            if not record.get("saving"):
                continue
            record["saving"] = False
            record["dirty"] = False
            record["error"] = ""
            if not record.get("isNew"):
                self._originals[str(record.get("code") or "")] = dict(record)
        self._apply_filter()
        self._finish_worker()
        self.milestonesChanged.emit()
        self.refresh()

    def _start_worker(self, operation, args, callback):
        from thlib.environment import env_inst

        if env_inst.server_pool.is_stopped:
            env_inst.server_pool.start()
        worker = env_inst.server_pool.add_task(operation, *args)
        if worker is None:
            self._error = "Server worker pool is unavailable"
            for record in self._records:
                record["saving"] = False
            self.stateChanged.emit()
            self._apply_filter()
            return
        request_id = uuid.uuid4().hex
        self._request_id = request_id
        self._worker = worker
        self._busy = True
        self._error = ""
        self.stateChanged.emit()
        worker.result.connect(
            lambda result: callback(request_id, result),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error.connect(
            lambda error: self._operation_failed(request_id, error),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.start()

    def _operation_failed(self, request_id, error):
        if request_id != self._request_id:
            return
        payload = error[0] if isinstance(error, (tuple, list)) and error else error
        if isinstance(payload, dict):
            payload = payload.get("exception") or payload.get("message") or payload
        self._error = str(payload or "Milestone operation failed")
        for record in self._records:
            if record.get("saving"):
                record["saving"] = False
                record["error"] = self._error
        if self._application.debug_log:
            self._application.debug_log.raise_error(
                error, group="tasks/milestones"
            )
        self._finish_worker(keep_error=True)
        self._apply_filter()

    def _finish_worker(self, keep_error=False):
        self._busy = False
        self._worker = None
        self._request_id = ""
        if not keep_error:
            self._error = ""
        self.stateChanged.emit()

    def _set_row_error(self, code, message):
        record = self._record(code)
        if not record:
            return
        record["error"] = str(message)
        self._apply_filter()

    def _record(self, code):
        return next((
            record for record in self._records
            if str(record.get("code") or "") == str(code or "")
        ), None)

    def _apply_filter(self):
        if self._filter:
            visible = [
                record for record in self._records
                if self._filter in str(record.get("description") or "").casefold()
                or self._filter in str(record.get("dueDate") or "").casefold()
            ]
        else:
            visible = list(self._records)
        self.model.replace(visible)
        self.stateChanged.emit()
