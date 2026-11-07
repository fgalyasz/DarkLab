from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QFormLayout, QHBoxLayout, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from src.catalog.preview_policy import (
    DEFAULT_DISCARD_DAYS,
    DEFAULT_FULL_EDGE,
    DEFAULT_FULL_QUALITY,
    DEFAULT_STANDARD_EDGE,
    DEFAULT_STANDARD_QUALITY,
    MAX_DISCARD_DAYS,
    MAX_EDGE,
    MAX_QUALITY,
    MIN_DISCARD_DAYS,
    MIN_EDGE,
    MIN_QUALITY,
    PreviewPolicy,
)


class PreviewCacheDialog(QDialog):
    def __init__(self, policy: PreviewPolicy, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preview Cache Settings")
        self._build_fields()
        self._build_layout()
        self._apply_policy(policy)

    def chosen_policy(self) -> PreviewPolicy:
        return PreviewPolicy(
            self._standard_edge.value(),
            self._standard_quality.value(),
            self._full_edge.value(),
            self._full_quality.value(),
            self._discard_enabled.isChecked(),
            self._discard_days.value(),
        )

    def _build_fields(self) -> None:
        self._standard_edge = _edge_spin(DEFAULT_STANDARD_EDGE)
        self._standard_quality = _quality_spin(DEFAULT_STANDARD_QUALITY)
        self._full_edge = _edge_spin(DEFAULT_FULL_EDGE)
        self._full_quality = _quality_spin(DEFAULT_FULL_QUALITY)
        self._discard_enabled = QCheckBox("Discard 1:1 cache files older than")
        self._discard_days = _discard_spin(DEFAULT_DISCARD_DAYS)

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.addLayout(_form(self))
        layout.addLayout(_buttons(self))

    def _apply_policy(self, policy: PreviewPolicy) -> None:
        self._standard_edge.setValue(policy.standard_long_edge)
        self._standard_quality.setValue(policy.standard_quality)
        self._full_edge.setValue(policy.full_long_edge)
        self._full_quality.setValue(policy.full_quality)
        self._discard_enabled.setChecked(policy.discard_full_enabled)
        self._discard_days.setValue(policy.discard_full_days)
        self._discard_days.setEnabled(policy.discard_full_enabled)
        self._discard_enabled.toggled.connect(self._discard_days.setEnabled)


def _form(dialog: PreviewCacheDialog) -> QFormLayout:
    form = QFormLayout()
    form.addRow("Grid preview long edge (px)", dialog._standard_edge)
    form.addRow("Grid JPEG quality", dialog._standard_quality)
    form.addRow("1:1 cache long edge (px, 0 = full)", dialog._full_edge)
    form.addRow("1:1 JPEG quality", dialog._full_quality)
    row = QHBoxLayout()
    row.addWidget(dialog._discard_enabled)
    row.addWidget(dialog._discard_days)
    form.addRow(row)
    return form


def _buttons(dialog: QDialog) -> QHBoxLayout:
    row = QHBoxLayout()
    row.addStretch()
    cancel = QPushButton("Cancel")
    cancel.clicked.connect(dialog.reject)
    ok = QPushButton("OK")
    ok.clicked.connect(dialog.accept)
    row.addWidget(cancel)
    row.addWidget(ok)
    return row


def _edge_spin(default: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(MIN_EDGE, MAX_EDGE)
    spin.setValue(default)
    return spin


def _quality_spin(default: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(MIN_QUALITY, MAX_QUALITY)
    spin.setValue(default)
    return spin


def _discard_spin(default: int) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(MIN_DISCARD_DAYS, MAX_DISCARD_DAYS)
    spin.setSuffix(" days")
    spin.setValue(default)
    return spin

