from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFormLayout, QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout,
)

from src.catalog.optimize_policy import DEFAULT_IDLE_MINUTES, OptimizePolicy


class OptimizeAutomationDialog(QDialog):
    def __init__(self, policy: OptimizePolicy, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Optimize Automation")
        self._on_quit = QCheckBox("Optimize catalog on quit")
        self._idle = QSpinBox()
        self._idle.setRange(0, 24 * 60)
        self._idle.setSuffix(" min idle (0 = off)")
        self._idle.setValue(DEFAULT_IDLE_MINUTES)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow(self._on_quit)
        form.addRow("Run after", self._idle)
        layout.addLayout(form)
        layout.addLayout(self._buttons())
        self._on_quit.setChecked(policy.on_quit_enabled)
        self._idle.setValue(policy.on_idle_minutes)

    def chosen_policy(self) -> OptimizePolicy:
        return OptimizePolicy(self._on_quit.isChecked(), self._idle.value())

    def _buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        row.addWidget(cancel)
        row.addWidget(ok)
        return row
