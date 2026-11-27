from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QSizePolicy, QWidget

MAJOR_HEIGHT = 2
SOFT_HEIGHT = 12
MAJOR_DARK = QColor(24, 24, 24)
MAJOR_LIGHT = QColor(92, 92, 92)
SOFT_DARK = QColor(70, 70, 70)
SOFT_LIGHT = QColor(88, 88, 88)


class EtchedDivider(QWidget):
    def __init__(self, kind: str = "major") -> None:
        super().__init__()
        self._kind = kind
        self.setObjectName("softDivider" if kind == "soft" else "developDivider")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(SOFT_HEIGHT if kind == "soft" else MAJOR_HEIGHT)

    @property
    def kind(self) -> str:
        return self._kind

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        y = (self.height() - 2) // 2
        dark, light = _palette(self._kind)
        painter.fillRect(0, y, self.width(), 1, dark)
        painter.fillRect(0, y + 1, self.width(), 1, light)
        painter.end()


def _palette(kind: str) -> tuple[QColor, QColor]:
    if kind == "soft":
        return SOFT_DARK, SOFT_LIGHT
    return MAJOR_DARK, MAJOR_LIGHT
