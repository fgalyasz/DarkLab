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
        self.filename_height = 24
        self.corner_radius = 8
        self.cell_side = 120
        self.card_margin = 6
        self.image_padding = 10

    def set_layout_metrics(
        self,
        *,
        cell_side: int,
        filename_height: int,
        card_margin: int,
        image_padding: int,
    ) -> None:
        """Update paint geometry based on the current grid layout settings."""
        self.cell_side = max(1, cell_side)
        self.filename_height = max(12, filename_height)
        self.card_margin = max(0, card_margin)
        self.image_padding = max(0, image_padding)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        painter.save()
        rect = option.rect.adjusted(
            self.card_margin,
            self.card_margin,
            -self.card_margin,
            -self.card_margin,
        )
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        bg_color = self._background_color(is_selected, is_hovered)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self.selection_color if is_selected else self.border_color)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)

        image_area_side = max(1, self.cell_side - (self.image_padding * 2))
        image_area = QRect(
            rect.left() + self.image_padding,
            rect.top() + self.image_padding,
            image_area_side,
            image_area_side,
        )

        pixmap: Optional[QPixmap] = index.data(ImageListModel.PIXMAP_ROLE)
        if pixmap:
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
            rect.left() + self.image_padding,
            image_area.bottom() + 2,
            image_area.width(),
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
