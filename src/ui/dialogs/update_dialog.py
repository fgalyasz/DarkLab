from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTextEdit, QVBoxLayout

from src.release.update_check import ReleaseInfo


class UpdateDialog(QDialog):
    def __init__(self, current: str, release: ReleaseInfo, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Update DarkLab")
        self._choice = "later"
        self._build(current, release)

    def choice(self) -> str:
        return self._choice

    def _build(self, current: str, release: ReleaseInfo) -> None:
        layout = QVBoxLayout(self)
        summary = QLabel(f"DarkLab {release.version} is available (you have {current}).")
        summary.setWordWrap(True)
        layout.addWidget(summary)
        notes = QTextEdit()
        notes.setReadOnly(True)
        notes.setPlainText(release.notes.strip() or "No release notes.")
        notes.setMinimumHeight(140)
        layout.addWidget(notes)
        layout.addWidget(self._buttons())

    def _buttons(self) -> QDialogButtonBox:
        buttons = QDialogButtonBox()
        update = buttons.addButton("Update", QDialogButtonBox.ButtonRole.AcceptRole)
        later = buttons.addButton("Later", QDialogButtonBox.ButtonRole.RejectRole)
        skip = buttons.addButton("Skip this version", QDialogButtonBox.ButtonRole.DestructiveRole)
        update.clicked.connect(self._choose_update)
        later.clicked.connect(self._choose_later)
        skip.clicked.connect(self._choose_skip)
        return buttons

    def _choose_update(self) -> None:
        self._choice = "update"
        self.accept()

    def _choose_later(self) -> None:
        self._choice = "later"
        self.reject()

    def _choose_skip(self) -> None:
        self._choice = "skip"
        self.accept()
