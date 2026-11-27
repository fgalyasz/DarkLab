from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from src.ui.density import Density


class ModuleBar(QWidget):
    module_selected = pyqtSignal(str)

    def __init__(self, modules: tuple[tuple[str, str], ...], catalog_name: str) -> None:
        super().__init__()
        self._buttons: dict[str, QPushButton] = {}
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(Density.MODULE_BAR_HEIGHT)
        self._build(modules, catalog_name)

    def set_current(self, module_id: str) -> None:
        for key, button in self._buttons.items():
            button.setChecked(key == module_id)

    def _build(self, modules: tuple[tuple[str, str], ...], catalog_name: str) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 2, 10, 2)
        row.setSpacing(2)
        row.addWidget(self._identity())
        row.addStretch()
        self._add_module_tabs(row, modules)
        row.addStretch()
        row.addWidget(self._catalog_label(catalog_name))

    def _add_module_tabs(self, row: QHBoxLayout, modules: tuple[tuple[str, str], ...]) -> None:
        for index, (module_id, title) in enumerate(modules):
            if index > 0:
                row.addWidget(self._separator())
            row.addWidget(self._module_button(module_id, title))

    def _separator(self) -> QLabel:
        label = QLabel("|")
        label.setStyleSheet(f"color: rgb(68, 68, 68); font-size: {Density.BODY_PX}px; background: transparent;")
        return label

    def _identity(self) -> QLabel:
        label = QLabel("DarkLab")
        label.setStyleSheet(
            f"color: rgb(224, 224, 224); font-size: {Density.HEADER_PX}px; font-weight: 600; background: transparent;"
        )
        return label

    def _catalog_label(self, catalog_name: str) -> QLabel:
        label = QLabel(catalog_name)
        label.setStyleSheet(f"color: rgb(164, 164, 164); font-size: {Density.HINT_PX}px; background: transparent;")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _module_button(self, module_id: str, title: str) -> QPushButton:
        button = QPushButton(title)
        button.setCheckable(True)
        button.setProperty("module_id", module_id)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
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
            "QPushButton { background: transparent; border: none;"
            f" color: rgb(152, 152, 152); font-size: {Density.BODY_PX}px; padding: 2px 6px; }}"
            "QPushButton:hover { color: rgb(232, 232, 232); }"
            "QPushButton:checked { color: rgb(246, 246, 246); font-weight: 600; }"
        )
