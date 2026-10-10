from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class ModuleBar(QWidget):
    module_selected = pyqtSignal(str)

    def __init__(self, modules: tuple[tuple[str, str], ...], catalog_name: str) -> None:
        super().__init__()
        self._buttons: dict[str, QPushButton] = {}
        self.setFixedHeight(42)
        self._build(modules, catalog_name)

    def set_current(self, module_id: str) -> None:
        for key, button in self._buttons.items():
            button.setChecked(key == module_id)

    def _build(self, modules: tuple[tuple[str, str], ...], catalog_name: str) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 4, 12, 4)
        row.addWidget(self._identity())
        row.addStretch()
        for module_id, title in modules:
            row.addWidget(self._module_button(module_id, title))
        row.addStretch()
        row.addWidget(self._catalog_label(catalog_name))

    def _identity(self) -> QLabel:
        label = QLabel("DarkLab")
        label.setStyleSheet("color: rgb(230, 230, 230); font-size: 13px; font-weight: 600;")
        return label

    def _catalog_label(self, catalog_name: str) -> QLabel:
        label = QLabel(catalog_name)
        label.setStyleSheet("color: rgb(190, 190, 190); font-size: 12px;")
        return label

    def _module_button(self, module_id: str, title: str) -> QPushButton:
        button = QPushButton(title)
        button.setCheckable(True)
        button.setProperty("module_id", module_id)
        button.setStyleSheet(self._button_style())
        button.clicked.connect(self._on_module_clicked)
        self._buttons[module_id] = button
        return button

    def _on_module_clicked(self) -> None:
        button = self.sender()
        if isinstance(button, QPushButton):
            self._choose(str(button.property("module_id")))

    def _choose(self, module_id: str) -> None:
        self.set_current(module_id)
        self.module_selected.emit(module_id)

    def _button_style(self) -> str:
        return (
            "QPushButton { background: transparent; border: none; color: rgb(168, 168, 168);"
            " font-size: 13px; padding: 4px 10px; }"
            "QPushButton:hover { color: white; }"
            "QPushButton:checked { color: white; font-weight: 600; }"
        )
