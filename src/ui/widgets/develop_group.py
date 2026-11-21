from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from src.ui.density import Density
from src.ui.widgets.collapsible_section import DisclosureTriangle


class DevelopGroupHeader(QWidget):
    clicked = pyqtSignal()

    def __init__(self, title: str) -> None:
        super().__init__()
        self._triangle = DisclosureTriangle()
        self.setObjectName("developHeading")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(Density.GROUP_HEADER_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build(title)

    def set_expanded(self, expanded: bool) -> None:
        self._triangle.set_expanded(expanded)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _build(self, title: str) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(6, 0, 6, 0)
        row.setSpacing(4)
        row.addWidget(self._triangle)
        row.addWidget(self._title(title), 1)

    def _title(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("developHeadingTitle")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        label.setWordWrap(False)
        return label


class DevelopGroup(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, title: str, expanded: bool = True) -> None:
        super().__init__()
        self.setObjectName("developGroup")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._expanded = expanded
        self._header = DevelopGroupHeader(title)
        self._body = QWidget()
        self._body.setObjectName("developGroupBody")
        self._body_layout = QVBoxLayout(self._body)
        self._configure_body_layout()
        self._header.clicked.connect(self.toggle)
        self._build()
        self._apply_expanded()

    def body_layout(self) -> QVBoxLayout:
        return self._body_layout

    def title(self) -> str:
        return self._header.findChild(QLabel, "developHeadingTitle").text()

    def is_expanded(self) -> bool:
        return self._expanded

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self._apply_expanded()

    def _configure_body_layout(self) -> None:
        self._body.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._body_layout.setContentsMargins(4, 1, 4, 2)
        self._body_layout.setSpacing(0)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._header)
        layout.addWidget(self._body)

    def _apply_expanded(self) -> None:
        self._body.setVisible(self._expanded)
        self._header.set_expanded(self._expanded)
        self._header.setStyleSheet(self._header_style())
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

    def _header_style(self) -> str:
        radius = Density.PANEL_CORNER_RADIUS_PX
        if self._expanded:
            return (
                "#developHeading {"
                f" border-top-left-radius: {radius}px; border-top-right-radius: {radius}px;"
                " border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; }"
            )
        collapsed = max(4, radius // 2)
        return (
            "#developHeading {"
            f" border-radius: {collapsed}px; border-bottom: none; }}"
        )

    def _apply_size_policy(self) -> None:
        if self._expanded:
            self.setMaximumHeight(16777215)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            return
        self.setMaximumHeight(Density.GROUP_HEADER_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
