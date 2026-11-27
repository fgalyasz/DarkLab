from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPolygon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from src.ui.density import Density

HEADER_HEIGHT = Density.PANEL_HEADER_HEIGHT
TRIANGLE_COLOR = QColor(186, 186, 186)


class DisclosureTriangle(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._expanded = True
        self.setFixedSize(12, 12)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = expanded
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(TRIANGLE_COLOR)
        painter.drawPolygon(QPolygon(self._points()))
        painter.end()

    def _points(self) -> list[QPoint]:
        if self._expanded:
            return [QPoint(2, 4), QPoint(10, 4), QPoint(6, 9)]
        return [QPoint(4, 2), QPoint(4, 10), QPoint(9, 6)]


class PanelHeader(QWidget):
    clicked = pyqtSignal()

    def __init__(self, title: str, arrow_on_left: bool) -> None:
        super().__init__()
        self._arrow_on_left = arrow_on_left
        self._triangle = DisclosureTriangle()
        self.setFixedHeight(HEADER_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("panelHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build(title, arrow_on_left)

    @property
    def arrow_on_left(self) -> bool:
        return self._arrow_on_left

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
        row.addStretch()
        row.addWidget(title_label)
        row.addWidget(self._triangle)

    def _title(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("panelTitle")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        label.setWordWrap(False)
        return label


class CollapsibleSection(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(
        self,
        title: str,
        content: QWidget,
        expanded: bool = True,
        arrow_on_left: bool = False,
        fill: bool = False,
    ) -> None:
        super().__init__()
        self.setObjectName("collapsibleSection")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
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
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self._header)
        layout.addWidget(self._content, 1 if self._fill else 0)
        self.setStyleSheet(_section_style())

    def _apply_expanded(self) -> None:
        self._content.setVisible(self._expanded)
        self._header.set_expanded(self._expanded)
        self._header.setStyleSheet(_header_edge_style(self._expanded))
        self._apply_size_policy()
        self.toggled.emit(self._expanded)
        self._relayout_ancestors()

    def _relayout_ancestors(self) -> None:
        widget = self
        while widget is not None:
            widget.updateGeometry()
            layout = widget.layout()
            if layout is not None:
                layout.activate()
            widget = widget.parentWidget()

    def _apply_size_policy(self) -> None:
        if self._expanded:
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
            vertical = QSizePolicy.Policy.Expanding if self._fill else QSizePolicy.Policy.Maximum
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
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(2)
        self.setObjectName("panelColumn")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def add_section(self, section: CollapsibleSection, stretch: int = 0) -> None:
        self._entries.append((section, stretch))
        self._layout.addWidget(section)
        section.toggled.connect(self._apply_stretches)
        self._apply_stretches()

    def _apply_stretches(self) -> None:
        for index, (section, stretch) in enumerate(self._entries):
            self._layout.setStretch(index, stretch if section.is_expanded() else 0)


def _section_style() -> str:
    radius = Density.PANEL_CORNER_RADIUS_PX
    return (
        "#collapsibleSection {"
        " background-color: rgb(80, 80, 80);"
        " border: 1px solid rgb(14, 14, 14);"
        f" border-radius: {radius}px; }}"
        "#panelHeader {"
        " background-color: rgb(50, 50, 50);"
        " border: none; border-top: 1px solid rgb(62, 62, 62);"
        " border-bottom: 1px solid rgb(12, 12, 12); }"
        f"#panelTitle {{ color: rgb(210, 210, 210); font-size: {Density.HEADER_PX}px;"
        " font-weight: 500; background: transparent; }"
        "#panelColumn { background-color: rgb(50, 50, 50); }"
    )


def _header_edge_style(expanded: bool) -> str:
    radius = Density.PANEL_CORNER_RADIUS_PX
    bottom = "1px solid rgb(12, 12, 12)" if expanded else "none"
    return f"#panelHeader {{ border-radius: {radius}px; border-bottom: {bottom}; }}"
