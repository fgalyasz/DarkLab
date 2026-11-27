from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from src.ui.density import Density
from src.ui.widgets.etched_divider import MAJOR_HEIGHT, EtchedDivider

TRACK_INDENT = Density.SLIDER_ROW_MARGIN_X + Density.SLIDER_CAPTION_WIDTH + Density.SLIDER_ROW_SPACING


class DevelopGroupHeader(QWidget):
    clicked = pyqtSignal()

    def __init__(self, title: str, align_to_track: bool = True) -> None:
        super().__init__()
        self._expanded = True
        self.setObjectName("developHeading")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(Density.GROUP_HEADER_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build(title, align_to_track)

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = expanded
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _build(self, title: str, align_to_track: bool) -> None:
        row = QHBoxLayout(self)
        left = TRACK_INDENT if align_to_track else Density.SLIDER_ROW_MARGIN_X
        row.setContentsMargins(left, 2, Density.SLIDER_ROW_MARGIN_X, 0)
        row.setSpacing(4)
        row.addWidget(self._title(title), 1)

    def _title(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("developHeadingTitle")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        label.setWordWrap(False)
        return label


class DevelopGroup(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(
        self,
        title: str,
        expanded: bool = True,
        show_divider: bool = True,
        align_to_track: bool = True,
    ) -> None:
        super().__init__()
        self.setObjectName("developGroup")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._expanded = expanded
        self._show_divider = show_divider
        self._divider = EtchedDivider("major") if show_divider else None
        self._header = DevelopGroupHeader(title, align_to_track)
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
        self._body_layout.setContentsMargins(0, 2, 0, 6)
        self._body_layout.setSpacing(0)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if self._divider is not None:
            layout.addWidget(self._divider)
        layout.addWidget(self._header)
        layout.addWidget(self._body)

    def _apply_expanded(self) -> None:
        self._body.setVisible(self._expanded)
        self._header.set_expanded(self._expanded)
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
            self.setMaximumHeight(16777215)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
            return
        extra = MAJOR_HEIGHT if self._show_divider else 0
        self.setMaximumHeight(Density.GROUP_HEADER_HEIGHT + extra)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
