"""Queue state categories shared by presentation and execution."""
_TERMINAL = {"completed", "failed", "cancelled", "skipped"}
_ACTIVE = {"preparing", "rendering", "paused", "saving", "stopping"}
_IDLE = {"waiting", "held"}
_RETRYABLE = {"failed", "cancelled"}
_RUNNABLE = _IDLE | _RETRYABLE
