from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QEvent, QObject, QTimer
from PyQt6.QtWidgets import QWidget

from src.catalog.optimize_policy import OptimizePolicy, read_optimize_policy
from src.ui.optimize_on_quit import import_copy_active, run_optimize_catalog

ACTIVITY_EVENTS = frozenset(
    {
        QEvent.Type.KeyPress,
        QEvent.Type.MouseButtonPress,
        QEvent.Type.MouseButtonRelease,
        QEvent.Type.Wheel,
        QEvent.Type.TouchBegin,
        QEvent.Type.ShortcutOverride,
    },
)


def idle_timeout_ms(minutes: int) -> int:
    return max(0, minutes) * 60 * 1000


def resets_idle_timer(event_type: QEvent.Type) -> bool:
    return event_type in ACTIVITY_EVENTS


class OptimizeIdleWatcher(QObject):
    def __init__(self, window: QWidget) -> None:
        super().__init__(window)
        self._window = window
        self._catalog: Path | None = None
        self._minutes = 0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_idle)
        window.installEventFilter(self)

    def apply(self, catalog: Path | None, policy: OptimizePolicy) -> None:
        self._catalog = catalog
        self._minutes = policy.on_idle_minutes if catalog is not None else 0
        self._arm()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._window and resets_idle_timer(event.type()):
            self._arm()
        return False

    def _arm(self) -> None:
        self._timer.stop()
        if self._catalog is None or self._minutes <= 0:
            return
        self._timer.start(idle_timeout_ms(self._minutes))

    def _on_idle(self) -> None:
        if self._catalog is None or self._minutes <= 0 or import_copy_active():
            self._arm()
            return
        policy = read_optimize_policy(self._catalog)
        if policy.on_idle_minutes <= 0:
            return
        run_optimize_catalog(self._window, self._catalog)
        self._arm()
