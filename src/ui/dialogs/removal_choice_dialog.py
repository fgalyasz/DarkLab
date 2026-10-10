from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget


class RemovalChoiceDialog(QDialog):
    def __init__(self, parent: QWidget | None, count: int) -> None:
        super().__init__(parent)
        self._delete_original = False
        self.setWindowTitle("Remove from Catalog")
        self._build(count)

    def _build(self, count: int) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Remove {count} index image(s) from the catalog?"))
        self.index_button = self._choice_button("Delete index image only", self._index_only)
        self.original_button = self._choice_button("Also delete the original from disk", self._with_original)
        self.cancel_button = self._choice_button("Cancel", self.reject)
        layout.addWidget(self.index_button)
        layout.addWidget(self.original_button)
        layout.addWidget(self.cancel_button)

    def deletes_original(self) -> bool:
        return self._delete_original

    def _choice_button(self, title: str, handler) -> QPushButton:
        button = QPushButton(title)
        button.clicked.connect(handler)
        return button

    def _index_only(self) -> None:
        self._delete_original = False
        self.accept()

    def _with_original(self) -> None:
        self._delete_original = True
        self.accept()
