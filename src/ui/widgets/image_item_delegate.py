"""Custom delegate that paints image thumbnails with rounded backgrounds."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle

from .image_list_model import ImageListModel


class ImageItemDelegate(QStyledItemDelegate):
    """Paints thumbnails and filenames inside QListView items."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.base_color = QColor(71, 71, 76)
        self.border_color = QColor(60, 60, 70)
        self.hover_color = QColor(55, 55, 65)
        self.selection_color = QColor(0, 122, 255)
        self.text_color = QColor(255, 255, 255)
        self.text_font = QFont("SF Pro Display", 10)
        self.filename_height = 20
        self.corner_radius = 8

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        # A paint() mindig az option.rect-et használja. Az item geometriát a
        # sizeHint() + QListView.gridSize határozza meg.
        rect = option.rect.adjusted(2, 2, -2, -2)
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        bg_color = self._background_color(is_selected, is_hovered)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self.selection_color if is_selected else self.border_color)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
        pixmap: Optional[QPixmap] = index.data(ImageListModel.PIXMAP_ROLE)
        if pixmap:
            # Képterület: töltse ki szinte az egész cellát, csak alul hagyjunk
            # sávot a fájlnévnek. Gondoskodjunk róla, hogy a magasság sose
            # legyen 0 vagy negatív, különben a skálázás eltünteti a képet.
            image_height = max(rect.height() - self.filename_height - 16, 12)
            image_area = QRect(
                rect.left() + 10,
                rect.top() + 8,
                rect.width() - 20,
                image_height,
            )
            scaled = pixmap.scaled(
                image_area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            image_pos = self._center_pixmap(image_area, scaled.size())
            painter.drawPixmap(image_pos, scaled)
        painter.setFont(self.text_font)
        painter.setPen(self.text_color)
        text_rect = QRect(
            rect.left() + 4,
            rect.bottom() - self.filename_height - 2,
            rect.width() - 8,
            self.filename_height,
        )
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            index.data(Qt.ItemDataRole.DisplayRole) or "",
        )
        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        view = option.widget
        if view is not None and hasattr(view, "gridSize"):
            grid_size = view.gridSize()
            if grid_size.isValid() and grid_size.width() > 0 and grid_size.height() > 0:
                return grid_size
        return super().sizeHint(option, index)

    def _background_color(self, is_selected: bool, is_hovered: bool) -> QColor:
        if is_selected:
            return self.selection_color
        if is_hovered:
            return self.hover_color
        return self.base_color

    @staticmethod
    def _center_pixmap(area: QRect, size: QSize) -> QRect:
        x = area.x() + (area.width() - size.width()) // 2
        y = area.y() + (area.height() - size.height()) // 2
        return QRect(x, y, size.width(), size.height())
