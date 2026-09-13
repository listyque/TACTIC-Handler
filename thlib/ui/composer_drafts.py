"""Context-scoped composer text; attachments retain their own storage owner."""

from PySide6.QtCore import QObject, QTimer, Signal

from thlib.environment import env_write_config
from .config_persistence import ConfigWriteQueue


class ComposerDrafts(QObject):
    changed = Signal()

    def __init__(self, namespace: str, state: dict, *, attachments=None,
                 queue=None, writer=env_write_config, parent=None):
        super().__init__(parent)
        contexts = state.get("contexts") if not set(state) - {"contexts"} else {}
        self.contexts = {
            str(key): str(value) for key, value in (contexts or {}).items()
            if key and value
        } if isinstance(contexts, dict) else {}
        self.context = ""
        self.text = ""
        self._namespace = namespace
        self._attachments = attachments
        self._owns_queue = queue is None
        self.queue = queue if queue is not None else ConfigWriteQueue(self, writer=writer)
        self._dirty = False
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.flush)

    def set_text(self, value: str) -> None:
        value = str(value or "")
        if value == self.text:
            return
        self.text = value
        if self.context:
            if value:
                self.contexts[self.context] = value
            else:
                self.contexts.pop(self.context, None)
            self._dirty = True
            self.timer.start()
        self.changed.emit()

    def activate(self, context: str) -> None:
        context = str(context or "")
        if context == self.context:
            return
        self.flush()
        self.context = context
        previous = self.text
        self.text = self.contexts.get(context, "")
        if self._attachments:
            self._attachments.activate_context(context)
        if previous != self.text:
            self.changed.emit()

    def clear(self, context: str) -> None:
        if not context:
            return
        if self.contexts.pop(context, None) is not None:
            self._dirty = True
        if self._attachments:
            self._attachments.clear_context(context)
        if context == self.context and self.text:
            self.text = ""
            self.changed.emit()
        self.flush()

    def flush(self) -> None:
        self.timer.stop()
        if self._dirty:
            if not self.queue.submit(
                    {"contexts": self.contexts}, filename="drafts",
                    unique_id=self._namespace, long_abs_path=True):
                raise RuntimeError("The composer configuration queue is closed")
            self._dirty = False

    def shutdown(self) -> None:
        self.flush()
        if self._owns_queue:
            self.queue.shutdown()
