from pathlib import Path
from typing import Optional, List, Dict
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QFontMetrics
import logging

logger = logging.getLogger(__name__)


class GridImageWidget(QWidget):
    """Custom grid widget for displaying images with pixel-perfect layout control."""
    
    selection_changed = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.images: List[Path] = []
        self.thumbnails: Dict[Path, QPixmap] = {}
        self.selected_images: List[Path] = []
        self.hovered_index: int = -1
        self.selection_anchor_index: int = -1
        
        self.columns = 5
        self.cell_width = 200
        self.cell_height = 224
        self.spacing = 8
        self.card_margin = 6
        self.filename_height = 24
        self.image_padding = 10
        
        self.left_margin = 0
        self.right_margin = 0
        
        self.bg_color = QColor(35, 35, 40)
        self.card_bg_color = QColor(45, 45, 50)
        self.card_hover_color = QColor(55, 55, 60)
        self.card_selected_color = QColor(70, 130, 180)
        self.text_color = QColor(220, 220, 220)
        
        self.setStyleSheet(f"background-color: rgb({self.bg_color.red()}, {self.bg_color.green()}, {self.bg_color.blue()});")
    
    def set_images(self, images: List[Path]) -> None:
        """Set the list of images to display."""
        self.images = images
        self.thumbnails.clear()
        self.selected_images = []
        self.hovered_index = -1
        self.selection_anchor_index = -1
        self._update_size()
        self.update()
    
    def add_image(self, image_path: Path, thumbnail: Optional[QPixmap] = None) -> None:
        """Add a single image to the grid."""
        if image_path not in self.images:
            self.images.append(image_path)
            if thumbnail:
                self.thumbnails[image_path] = thumbnail
            self._update_size()
            self.update()
    
    def set_thumbnail(self, image_path: Path, thumbnail: QPixmap) -> None:
        """Set thumbnail for an image."""
        if image_path in self.images:
            self.thumbnails[image_path] = thumbnail
            self.update()
    
    def set_grid_layout(self, columns: int, cell_width: int, cell_height: int, 
                       spacing: int, left_margin: int, right_margin: int) -> None:
        """Set grid layout parameters."""
        self.columns = columns
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.spacing = spacing
        self.left_margin = left_margin
        self.right_margin = right_margin
        self._update_size()
        self.update()
    
    def set_cell_metrics(self, card_margin: int, filename_height: int, image_padding: int) -> None:
        """Set cell internal metrics."""
        self.card_margin = card_margin
        self.filename_height = filename_height
        self.image_padding = image_padding
        self.update()
    
    def _update_size(self) -> None:
        """Update widget size based on grid layout."""
        if not self.images:
            self.setMinimumSize(0, 0)
            return
        
        rows = (len(self.images) + self.columns - 1) // self.columns
        total_width = self.left_margin + self.columns * self.cell_width + (self.columns - 1) * self.spacing + self.right_margin
        total_height = rows * self.cell_height + (rows - 1) * self.spacing
        
        self.setMinimumSize(total_width, total_height)
    
    def _get_cell_rect(self, index: int) -> QRect:
        """Get the rectangle for a cell at given index."""
        if index < 0 or index >= len(self.images):
            return QRect()
        
        row = index // self.columns
        col = index % self.columns
        
        x = self.left_margin + col * (self.cell_width + self.spacing)
        y = row * (self.cell_height + self.spacing)
        
        return QRect(x, y, self.cell_width, self.cell_height)
    
    def _get_index_at_pos(self, pos: QPoint) -> int:
        """Get the image index at the given position."""
        for i in range(len(self.images)):
            if self._get_cell_rect(i).contains(pos):
                return i
        return -1
    
    def paintEvent(self, event) -> None:
        """Paint the grid of images."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for i, image_path in enumerate(self.images):
            cell_rect = self._get_cell_rect(i)
            if not cell_rect.intersects(event.rect()):
                continue
            
            is_selected = image_path in self.selected_images
            is_hovered = i == self.hovered_index
            
            if is_selected:
                bg_color = self.card_selected_color
            elif is_hovered:
                bg_color = self.card_hover_color
            else:
                bg_color = self.card_bg_color
            
            painter.fillRect(cell_rect, bg_color)
            
            image_rect = QRect(
                cell_rect.x() + self.card_margin,
                cell_rect.y() + self.card_margin,
                cell_rect.width() - 2 * self.card_margin,
                cell_rect.height() - 2 * self.card_margin - self.filename_height
            )
            
            if image_path in self.thumbnails:
                thumbnail = self.thumbnails[image_path]
                thumb_size = thumbnail.size()
                
                available_width = image_rect.width() - 2 * self.image_padding
                available_height = image_rect.height() - 2 * self.image_padding
                
                scale = min(available_width / thumb_size.width(), 
                           available_height / thumb_size.height())
                
                scaled_width = int(thumb_size.width() * scale)
                scaled_height = int(thumb_size.height() * scale)
                
                thumb_x = image_rect.x() + self.image_padding + (available_width - scaled_width) // 2
                thumb_y = image_rect.y() + self.image_padding + (available_height - scaled_height) // 2
                
                thumb_rect = QRect(thumb_x, thumb_y, scaled_width, scaled_height)
                painter.drawPixmap(thumb_rect, thumbnail)
            
            text_rect = QRect(
                cell_rect.x() + self.card_margin,
                cell_rect.bottom() - self.card_margin - self.filename_height,
                cell_rect.width() - 2 * self.card_margin,
                self.filename_height
            )
            
            painter.setPen(QPen(self.text_color))
            font = QFont()
            font.setPointSize(9)
            painter.setFont(font)
            
            fm = QFontMetrics(font)
            elided_text = fm.elidedText(image_path.name, Qt.TextElideMode.ElideMiddle, text_rect.width())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided_text)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for hover effect."""
        index = self._get_index_at_pos(event.pos())
        if index != self.hovered_index:
            self.hovered_index = index
            self.update()
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse click for selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            index = self._get_index_at_pos(event.pos())
            if index >= 0:
                image_path = self.images[index]
                modifiers = event.modifiers()
                use_toggle = bool(
                    modifiers & Qt.KeyboardModifier.ControlModifier
                    or modifiers & Qt.KeyboardModifier.MetaModifier
                )
                use_range = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

                if use_range:
                    self._select_range(index, extend_selection=use_toggle)
                elif use_toggle:
                    if image_path in self.selected_images:
                        self.selected_images = [
                            selected_image
                            for selected_image in self.selected_images
                            if selected_image != image_path
                        ]
                    else:
                        self.selected_images.append(image_path)
                    self.selection_anchor_index = index
                else:
                    self.selected_images = [image_path]
                    self.selection_anchor_index = index

                self.selection_changed.emit(list(self.selected_images))
                self.update()
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave to clear hover."""
        if self.hovered_index != -1:
            self.hovered_index = -1
            self.update()
    
    def select_image(self, image_path: Optional[Path]) -> None:
        """Programmatically select a single image."""
        self.set_selected_images([image_path] if image_path is not None else [])

    def set_selected_images(self, image_paths: List[Path]) -> None:
        """Programmatically set the selected images."""
        filtered_image_paths = [image_path for image_path in image_paths if image_path in self.images]
        if self.selected_images != filtered_image_paths:
            self.selected_images = filtered_image_paths
            self.selection_anchor_index = self.images.index(filtered_image_paths[-1]) if filtered_image_paths else -1
            self.update()

    def select_all_images(self) -> None:
        """Select all loaded images."""
        self.selected_images = list(self.images)
        self.selection_anchor_index = len(self.images) - 1 if self.images else -1
        self.selection_changed.emit(list(self.selected_images))
        self.update()

    def clear_selection(self) -> None:
        """Clear the current selection."""
        if not self.selected_images:
            return
        self.selected_images = []
        self.selection_anchor_index = -1
        self.selection_changed.emit([])
        self.update()

    def _select_range(self, index: int, extend_selection: bool) -> None:
        """Select a contiguous range from anchor to the given index."""
        if not self.images:
            return
        anchor_index = self.selection_anchor_index
        if anchor_index < 0:
            anchor_index = self.images.index(self.selected_images[-1]) if self.selected_images else index
        start_index = min(anchor_index, index)
        end_index = max(anchor_index, index)
        range_images = self.images[start_index:end_index + 1]
        if extend_selection:
            selected_set = list(self.selected_images)
            for image_path in range_images:
                if image_path not in selected_set:
                    selected_set.append(image_path)
            self.selected_images = selected_set
        else:
            self.selected_images = list(range_images)
        self.selection_anchor_index = anchor_index

    def get_selected_images(self) -> List[Path]:
        """Return selected images."""
        return list(self.selected_images)
    
    def clear(self) -> None:
        """Clear all images."""
        self.images.clear()
        self.thumbnails.clear()
        self.selected_images = []
        self.hovered_index = -1
        self.selection_anchor_index = -1
        self._update_size()
        self.update()
