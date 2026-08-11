from __future__ import annotations

from PySide6.QtCore import QObject, Property, QSettings, Signal, Slot


class MayaOptionsController(QObject):
    stateChanged = Signal()

    def __init__(self, checkin_controller, parent=None):
        super().__init__(parent)
        self._checkin = checkin_controller
        self._settings = QSettings("TACTIC-Handler", "modern-qml")
        self._mode = "open"
        self._count = 1
        self._setup_workdir = True
        self._error = ""
        self._load()
        self._checkin.checkoutChanged.connect(self.stateChanged)

    def _load(self):
        prefix = f"mayaOptions/{self._mode}"
        self._count = max(1, min(
            100, self._settings.value(f"{prefix}/count", 1, type=int)
        ))
        self._setup_workdir = self._settings.value(
            f"{prefix}/setupWorkdir", True, type=bool
        )

    def _save(self):
        prefix = f"mayaOptions/{self._mode}"
        self._settings.setValue(f"{prefix}/count", self._count)
        self._settings.setValue(
            f"{prefix}/setupWorkdir", self._setup_workdir
        )

    @Property(str, notify=stateChanged)
    def mode(self): return self._mode

    @Property(str, notify=stateChanged)
    def title(self):
        return {
            "open": "Open scene",
            "import": "Import scene",
            "reference": "Reference scene",
        }[self._mode]

    @Property(str, notify=stateChanged)
    def fileTitle(self):
        return str(self._checkin.selectedCheckoutFile.get("title") or "")

    @Property(int, notify=stateChanged)
    def count(self): return self._count

    @Property(bool, notify=stateChanged)
    def setupWorkdir(self): return self._setup_workdir

    @Property(bool, notify=stateChanged)
    def available(self):
        return (
            self._checkin.hasCheckoutFile
            and self._checkin.dcc_operation_availability(self._mode)[0]
            and not self._checkin.checkoutBusy
        )

    @Property(str, notify=stateChanged)
    def unavailableReason(self):
        if not self._checkin.hasCheckoutFile:
            return "Select a snapshot file in Check-in/Out first."
        available, reason = self._checkin.dcc_operation_availability(
            self._mode
        )
        return "" if available else reason

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error or self._checkin.checkoutError

    @Slot(str)
    def activate(self, mode):
        mode = str(mode or "")
        if mode not in {"open", "import", "reference"}:
            return
        self._mode = mode
        self._error = ""
        self._load()
        self.stateChanged.emit()

    @Slot(int)
    def set_count(self, value):
        value = max(1, min(100, int(value)))
        if value == self._count:
            return
        self._count = value
        self._save()
        self.stateChanged.emit()

    @Slot(bool)
    def set_setup_workdir(self, value):
        value = bool(value)
        if value == self._setup_workdir:
            return
        self._setup_workdir = value
        self._save()
        self.stateChanged.emit()

    @Slot()
    def confirm(self):
        if not self.available:
            self._error = self.unavailableReason
            self.stateChanged.emit()
            return
        self._save()
        repeats = self._count if self._mode in {"import", "reference"} else 1
        self._checkin.request_checkout_action(
            self._mode, repeats,
            {"setup_workdir": self._setup_workdir},
        )
        self.stateChanged.emit()

    @Slot()
    def cancel(self):
        if self._checkin.checkoutBusy:
            self._checkin.cancel_checkout()
