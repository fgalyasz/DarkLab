from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPolygon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

HEADER_HEIGHT = 26


class DisclosureTriangle(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._expanded = True
        self.setFixedSize(16, 16)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = expanded
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(214, 214, 214))
        painter.drawPolygon(QPolygon(self._points()))
        painter.end()

    def _points(self) -> list[QPoint]:
        if self._expanded:
            return [QPoint(2, 5), QPoint(14, 5), QPoint(8, 12)]
        return [QPoint(5, 2), QPoint(5, 14), QPoint(12, 8)]


class PanelHeader(QWidget):
    clicked = pyqtSignal()

    def __init__(self, title: str, arrow_on_left: bool) -> None:
        super().__init__()
        self._triangle = DisclosureTriangle()
        self.setFixedHeight(HEADER_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("panelHeader")
        self._build(title, arrow_on_left)

    def set_expanded(self, expanded: bool) -> None:
        self._triangle.set_expanded(expanded)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _build(self, title: str, arrow_on_left: bool) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 0, 8, 0)
        row.setSpacing(6)
        title_label = self._title(title)
        if arrow_on_left:
            row.addWidget(self._triangle)
            row.addWidget(title_label)
            row.addStretch()
            return
        row.addWidget(title_label)
        row.addStretch()
        row.addWidget(self._triangle)

    def _title(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("panelTitle")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        return label


class CollapsibleSection(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, title: str, content: QWidget, expanded: bool = True, arrow_on_left: bool = False, fill: bool = False) -> None:
        super().__init__()
        self._content = content
        self._expanded = expanded
        self._fill = fill
        self._header = PanelHeader(title, arrow_on_left)
        self._header.clicked.connect(self.toggle)
        self._build()
        self._apply_expanded()

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self._apply_expanded()

    def is_expanded(self) -> bool:
        return self._expanded

    def header(self) -> PanelHeader:
        return self._header

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._header)
        layout.addWidget(self._content, 1)
        self.setStyleSheet(_section_style())

    def _apply_expanded(self) -> None:
        self._content.setVisible(self._expanded)
        self._header.set_expanded(self._expanded)
        self._apply_size_policy()
        self.toggled.emit(self._expanded)
        self.updateGeometry()

    def _apply_size_policy(self) -> None:
        if self._expanded:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            vertical = QSizePolicy.Policy.Expanding if self._fill else QSizePolicy.Policy.Preferred
            self.setSizePolicy(QSizePolicy.Policy.Preferred, vertical)
            return
        self.setMinimumHeight(HEADER_HEIGHT)
        self.setMaximumHeight(HEADER_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)


class PanelColumn(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._entries: list[tuple[CollapsibleSection, int]] = []
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setObjectName("panelColumn")

    def add_section(self, section: CollapsibleSection, stretch: int = 0) -> None:
        self._entries.append((section, stretch))
        self._layout.addWidget(section)
        section.toggled.connect(self._apply_stretches)
        self._apply_stretches()

    def _apply_stretches(self) -> None:
        for index, (section, stretch) in enumerate(self._entries):
            self._layout.setStretch(index, stretch if section.is_expanded() else 0)


def _section_style() -> str:
    return (
        "#panelHeader {"
        " background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(82, 82, 82), stop:1 rgb(54, 54, 54));"
        " border-top: 1px solid rgb(104, 104, 104); border-bottom: 1px solid rgb(16, 16, 16); }"
        "#panelTitle { color: rgb(236, 236, 236); font-size: 12px; font-weight: 600; background: transparent; }"
        "#panelColumn { background-color: rgb(45, 45, 45); }"
    )
