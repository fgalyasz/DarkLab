from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QProgressDialog, QWidget


class ProgressReporter:
    def __init__(self, parent: QWidget, title: str) -> None:
        self._dialog = QProgressDialog("", "", 0, 0, parent)
        self._dialog.setWindowTitle(title)
        self._dialog.setCancelButton(None)
        self._dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._dialog.setMinimumDuration(0)

    def __call__(self, done: int, total: int, label: str) -> None:
        self._dialog.setMaximum(total)
        self._dialog.setLabelText(label)
        self._dialog.setValue(done)
        QApplication.processEvents()

    @property
    def text(self) -> str:
        return self._dialog.labelText()

    @property
    def value(self) -> int:
        return self._dialog.value()

    def close(self) -> None:
        self._dialog.close()


class CancellableProgressReporter(ProgressReporter):
    def __init__(self, parent: QWidget, title: str) -> None:
        super().__init__(parent, title)
        self._dialog.setCancelButtonText("Cancel")

    def cancelled(self) -> bool:
        return self._dialog.wasCanceled()

    def __call__(self, done: int, total: int, label: str) -> None:
        super().__call__(done, total, label)
        if self.cancelled():
            return
