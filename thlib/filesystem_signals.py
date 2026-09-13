"""Qt signal adapter for the legacy filesystem watcher."""

from thlib.side.Qt import QtCore
from thlib.side.watchdog.events import (
    FileSystemEventHandler, EVENT_TYPE_MOVED, EVENT_TYPE_CREATED,
    EVENT_TYPE_DELETED, EVENT_TYPE_MODIFIED,
)


class EventHandler(FileSystemEventHandler, QtCore.QObject):
    created = QtCore.Signal(object, object)
    deleted = QtCore.Signal(object, object)
    moved = QtCore.Signal(object, object)
    modified = QtCore.Signal(object, object)
    any = QtCore.Signal(object, object)

    def __init__(self):
        super(EventHandler, self).__init__()

    def dispatch(self, event, watch):
        self.on_any_event(event, watch)
        _method_map = {
            EVENT_TYPE_MODIFIED: self.on_modified,
            EVENT_TYPE_MOVED: self.on_moved,
            EVENT_TYPE_CREATED: self.on_created,
            EVENT_TYPE_DELETED: self.on_deleted,
        }
        event_type = event.event_type
        _method_map[event_type](event, watch)

    def on_any_event(self, event, watch):
        self.any.emit(event, watch)

    def on_created(self, event, watch):
        self.created.emit(event, watch)

    def on_deleted(self, event, watch):
        self.deleted.emit(event, watch)

    def on_moved(self, event, watch):
        self.moved.emit(event, watch)

    def on_modified(self, event, watch):
        self.modified.emit(event, watch)

