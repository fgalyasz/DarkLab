from pathlib import Path
from typing import Optional, List, Dict
import math
from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QPen, QFontMetrics, QAction
import logging

logger = logging.getLogger(__name__)


class GridImageWidget(QWidget):
    """Custom grid widget for displaying images with pixel-perfect layout control."""
    
    selection_changed = pyqtSignal(object)
    marker_changed = pyqtSignal(object, str, str)  # image_path, marker_type, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.images: List[Path] = []
        self.thumbnails: Dict[Path, QPixmap] = {}
        self.image_markers: Dict[Path, Dict[str, str]] = {}
        self.selected_images: List[Path] = []
        self.hovered_index: int = -1
        self.hovered_rating: int = 0  # Hover rating for star interaction
        self.selection_anchor_index: int = -1
        
        self.columns = 5
        self.cell_width = 200
        self.cell_height = 224
        self.spacing = 8
        self.card_margin = 6
        self.filename_height = 24
        self.image_padding = 10
        self.rating_height = 18  # Height for rating stars strip
        
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
        # Only clear thumbnails that are no longer in the images list
        thumbnails_to_remove = [path for path in self.thumbnails if path not in images]
        for path in thumbnails_to_remove:
            del self.thumbnails[path]
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

    def set_image_markers(self, markers: Dict[Path, Dict[str, str]]) -> None:
        """Set per-image marker properties for painting overlays."""
        self.image_markers = dict(markers)
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
        # Do not set maximum size - let the layout handle it
    
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
                cell_rect.height() - 2 * self.card_margin - self.filename_height - self.rating_height
            )
            
            if image_path in self.thumbnails:
                thumbnail = self.thumbnails[image_path]
                thumb_size = thumbnail.size()
                
                # Skip rendering if thumbnail has invalid dimensions
                if thumb_size.width() <= 0 or thumb_size.height() <= 0:
                    continue
                
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
            
            # Paint rating stars below image
            self._paint_rating_marker(painter, image_path, cell_rect, image_rect, bg_color)
            
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
            self._paint_markers(painter, image_path, cell_rect, bg_color)

    def _paint_markers(self, painter: QPainter, image_path: Path, cell_rect: QRect, bg_color: QColor) -> None:
        marker_data = self.image_markers.get(image_path, {})
        pick_value = str(marker_data.get("pick", "none")).strip().lower()
        color_value = str(marker_data.get("color", "none")).strip().lower()
        self._paint_pick_marker(painter, pick_value, cell_rect, bg_color)
        self._paint_color_marker(painter, color_value, cell_rect, bg_color)

    def _paint_pick_marker(self, painter: QPainter, pick_value: str, cell_rect: QRect, bg_color: QColor) -> None:
        """Paint pick marker (✓ or ✕) always visible with inactive checkbox when none."""
        is_active = pick_value in {"accepted", "rejected"}
        
        badge_rect = QRect(cell_rect.x() + 6, cell_rect.y() + 6, 24, 24)
        # Use cell background color
        painter.fillRect(badge_rect, bg_color)
        
        if is_active:
            symbol = "✓" if pick_value == "accepted" else "✕"
            color = QColor(80, 220, 120) if pick_value == "accepted" else QColor(235, 90, 90)
            painter.setPen(QPen(color, 2))
            font = QFont()
            font.setPointSize(11)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, symbol)
        else:
            # Draw checkbox-style square when inactive
            checkbox_rect = QRect(badge_rect.x() + 4, badge_rect.y() + 4, 16, 16)
            painter.setPen(QPen(QColor(80, 80, 85), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(checkbox_rect, 3, 3)
            painter.setBrush(Qt.BrushStyle.NoBrush)

    def _paint_rating_marker(self, painter: QPainter, image_path: Path, cell_rect: QRect, image_rect: QRect, bg_color: QColor) -> None:
        """Paint rating stars below the image. Always shows 5 stars with inactive ones dimmed."""
        marker_data = self.image_markers.get(image_path, {})
        current_rating = int(marker_data.get("rating", "0") or "0")
        
        # Determine effective rating (hover takes precedence for visual feedback)
        is_hovered = self.hovered_index == self.images.index(image_path) if image_path in self.images else False
        effective_rating = self.hovered_rating if is_hovered and self.hovered_rating > 0 else current_rating
        
        # Calculate rating strip position (below image, above filename)
        rating_y = image_rect.bottom() + 2
        rating_rect = QRect(
            cell_rect.x() + self.card_margin,
            rating_y,
            cell_rect.width() - 2 * self.card_margin,
            self.rating_height - 4
        )
        
        # Draw background for rating area using cell background color
        painter.fillRect(rating_rect, bg_color)
        
        # Draw 5 stars
        star_size = 14
        total_stars_width = 5 * star_size
        start_x = rating_rect.x() + (rating_rect.width() - total_stars_width) // 2
        
        for i in range(5):
            star_x = start_x + i * star_size
            star_rect = QRect(star_x, rating_rect.y() + 2, star_size, star_size)
            
            if i < effective_rating:
                # Active star - yellow/gold
                painter.setPen(QPen(QColor(245, 205, 70), 1))
                painter.setBrush(QColor(245, 205, 70))
            else:
                # Inactive star - dim gray
                painter.setPen(QPen(QColor(80, 80, 85), 1))
                painter.setBrush(QColor(60, 60, 65))
            
            # Draw star shape
            self._draw_star(painter, star_rect)
        
        # Reset brush
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _draw_star(self, painter: QPainter, rect: QRect) -> None:
        """Draw a 5-pointed star within the given rectangle."""
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        
        center_x = rect.x() + rect.width() / 2
        center_y = rect.y() + rect.height() / 2
        outer_radius = min(rect.width(), rect.height()) / 2 - 1
        inner_radius = outer_radius * 0.4
        
        points = []
        for i in range(10):
            angle = (i * 36 - 90) * math.pi / 180  # Start from top
            if i % 2 == 0:
                # Outer point
                x = center_x + outer_radius * math.cos(angle)
                y = center_y + outer_radius * math.sin(angle)
            else:
                # Inner point
                x = center_x + inner_radius * math.cos(angle)
                y = center_y + inner_radius * math.sin(angle)
            points.append(QPointF(x, y))
        
        polygon = QPolygonF(points)
        painter.drawPolygon(polygon)

    def _paint_color_marker(self, painter: QPainter, color_value: str, cell_rect: QRect, bg_color: QColor) -> None:
        """Paint color marker always visible with inactive state when none."""
        color_map = {
            "red": QColor(230, 70, 70),
            "orange": QColor(240, 150, 55),
            "yellow": QColor(245, 210, 70),
            "green": QColor(80, 210, 115),
            "blue": QColor(80, 145, 230),
            "purple": QColor(160, 100, 230),
        }
        
        marker_color = color_map.get(color_value)
        is_active = marker_color is not None
        
        if not is_active:
            marker_color = QColor(60, 60, 65)  # Dim gray for inactive
        
        marker_rect = QRect(cell_rect.right() - 20, cell_rect.y() + 8, 12, 12)
        # Use cell background color
        painter.fillRect(marker_rect, bg_color)
        
        painter.setPen(QPen(QColor(20, 20, 20), 1))
        painter.setBrush(marker_color)
        painter.drawEllipse(marker_rect)
        painter.setBrush(Qt.BrushStyle.NoBrush)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for hover effect and rating star interaction."""
        pos = event.pos()
        index = self._get_index_at_pos(pos)
        
        # Handle hover index change
        if index != self.hovered_index:
            self.hovered_index = index
            self.hovered_rating = 0
            self.update()
        
        # Check if hovering over rating stars area
        if index >= 0:
            self._update_hover_rating(pos, index)

    def _update_hover_rating(self, pos: QPoint, index: int) -> None:
        """Calculate hover rating based on mouse position over rating stars."""
        if index < 0 or index >= len(self.images):
            if self.hovered_rating != 0:
                self.hovered_rating = 0
                self.update()
            return
        
        image_path = self.images[index]
        cell_rect = self._get_cell_rect(index)
        
        # Calculate rating area rectangle (same as in _paint_rating_marker)
        image_rect = QRect(
            cell_rect.x() + self.card_margin,
            cell_rect.y() + self.card_margin,
            cell_rect.width() - 2 * self.card_margin,
            cell_rect.height() - 2 * self.card_margin - self.filename_height - self.rating_height
        )
        rating_y = image_rect.bottom() + 2
        rating_rect = QRect(
            cell_rect.x() + self.card_margin,
            rating_y,
            cell_rect.width() - 2 * self.card_margin,
            self.rating_height - 4
        )
        
        if not rating_rect.contains(pos):
            if self.hovered_rating != 0:
                self.hovered_rating = 0
                self.update()
            return
        
        # Calculate which star is being hovered
        star_size = 14
        total_stars_width = 5 * star_size
        start_x = rating_rect.x() + (rating_rect.width() - total_stars_width) // 2
        
        relative_x = pos.x() - start_x
        if relative_x < 0:
            new_hover_rating = 0
        else:
            new_hover_rating = min(5, max(0, int(relative_x / star_size) + 1))
        
        if new_hover_rating != self.hovered_rating:
            self.hovered_rating = new_hover_rating
            self.update()
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse click for selection and rating change."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            index = self._get_index_at_pos(event.pos())
            if index >= 0:
                # Check if clicking on rating stars
                if self.hovered_rating > 0 and self.hovered_index == index:
                    # Apply the hovered rating
                    image_path = self.images[index]
                    current_rating = int(self.image_markers.get(image_path, {}).get("rating", "0") or "0")
                    if self.hovered_rating != current_rating:
                        self._set_marker_for_selected("rating", str(self.hovered_rating))
                        return
                
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
    
    def contextMenuEvent(self, event) -> None:
        """Handle right-click context menu for markers."""
        index = self._get_index_at_pos(event.pos())
        if index < 0:
            return
        
        image_path = self.images[index]
        
        # Select the image if not already selected
        if image_path not in self.selected_images:
            self.selected_images = [image_path]
            self.selection_anchor_index = index
            self.selection_changed.emit(list(self.selected_images))
            self.update()
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgb(45, 45, 50);
                color: white;
                border: 1px solid rgb(70, 70, 80);
            }
            QMenu::item:selected {
                background-color: rgb(70, 130, 180);
            }
        """)
        
        # Pick submenu
        pick_menu = QMenu("Pick", self)
        pick_menu.setStyleSheet(menu.styleSheet())
        pick_actions = [
            ("None", "none"),
            ("Accepted ✓", "accepted"),
            ("Rejected ✕", "rejected"),
        ]
        for label, value in pick_actions:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, v=value: self._set_marker_for_selected("pick", v))
            pick_menu.addAction(action)
        menu.addMenu(pick_menu)
        
        # Rating submenu
        rating_menu = QMenu("Rating", self)
        rating_menu.setStyleSheet(menu.styleSheet())
        for i in range(6):
            stars = "★" * i if i > 0 else "No stars"
            action = QAction(f"{stars}", self)
            action.triggered.connect(lambda checked, r=i: self._set_marker_for_selected("rating", str(r)))
            rating_menu.addAction(action)
        menu.addMenu(rating_menu)
        
        # Color submenu
        color_menu = QMenu("Color", self)
        color_menu.setStyleSheet(menu.styleSheet())
        color_actions = [
            ("None", "none"),
            ("Red", "red"),
            ("Orange", "orange"),
            ("Yellow", "yellow"),
            ("Green", "green"),
            ("Blue", "blue"),
            ("Purple", "purple"),
        ]
        for label, value in color_actions:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, v=value: self._set_marker_for_selected("color", v))
            color_menu.addAction(action)
        menu.addMenu(color_menu)
        
        menu.exec(event.globalPos())
    
    def _set_marker_for_selected(self, marker_type: str, value: str) -> None:
        """Set marker for all selected images."""
        for image_path in self.selected_images:
            # Update local markers
            if image_path not in self.image_markers:
                self.image_markers[image_path] = {}
            self.image_markers[image_path][marker_type] = value
            # Emit signal for parent to handle persistence
            self.marker_changed.emit(image_path, marker_type, value)
        self.update()
    
    def keyPressEvent(self, event) -> None:
        """Handle keyboard shortcuts for rating, pick markers, and navigation."""
        key = event.key()
        key_text = event.text().upper()
        modifiers = event.modifiers()
        shift_pressed = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        
        # Navigation keys (work even without selection)
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down,
                   Qt.Key.Key_Home, Qt.Key.Key_End):
            self._handle_navigation(key, shift_pressed)
            return
        
        # Rating and pick shortcuts (require selection)
        if not self.selected_images:
            super().keyPressEvent(event)
            return
        
        # Rating shortcuts (0-5)
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_5:
            rating = key - Qt.Key.Key_0
            self._set_marker_for_selected("rating", str(rating))
        elif key_text in "012345" and len(key_text) == 1:
            rating = int(key_text)
            self._set_marker_for_selected("rating", str(rating))
        # Pick shortcuts
        elif key_text == "P":
            self._set_marker_for_selected("pick", "accepted")
        elif key_text == "X":
            self._set_marker_for_selected("pick", "rejected")
        elif key_text == "U":
            self._set_marker_for_selected("pick", "none")
        else:
            super().keyPressEvent(event)
    
    def _handle_navigation(self, key: int, shift_pressed: bool) -> None:
        """Handle navigation key presses to move selection in the grid."""
        if not self.images:
            return
        
        # Get current position
        if self.selected_images:
            try:
                current_index = self.images.index(self.selected_images[-1])
            except ValueError:
                current_index = 0
        else:
            current_index = -1
        
        new_index = current_index
        
        if key == Qt.Key.Key_Left:
            new_index = max(0, current_index - 1)
        elif key == Qt.Key.Key_Right:
            new_index = min(len(self.images) - 1, current_index + 1)
        elif key == Qt.Key.Key_Up:
            new_index = max(0, current_index - self.columns)
        elif key == Qt.Key.Key_Down:
            new_index = min(len(self.images) - 1, current_index + self.columns)
        elif key == Qt.Key.Key_Home:
            new_index = 0
        elif key == Qt.Key.Key_End:
            new_index = len(self.images) - 1
        
        if new_index != current_index:
            if shift_pressed and current_index >= 0:
                # Extend selection
                self._select_range(new_index, extend_selection=True)
            else:
                # Move selection
                self.selected_images = [self.images[new_index]]
                self.selection_anchor_index = new_index
            self.selection_changed.emit(list(self.selected_images))
            self.update()
            self._ensure_visible(new_index)
    
    def _ensure_visible(self, index: int) -> None:
        """Scroll to ensure the given index is visible in the viewport."""
        if index < 0 or index >= len(self.images):
            return
        
        cell_rect = self._get_cell_rect(index)
        
        # Get the parent scroll area if exists
        from PyQt6.QtWidgets import QScrollArea
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, QScrollArea):
                parent.ensureVisible(cell_rect.center().x(), cell_rect.center().y())
                return
            parent = parent.parent()
    
    def leaveEvent(self, event) -> None:
        """Handle mouse leave to clear hover."""
        needs_update = False
        if self.hovered_index != -1:
            self.hovered_index = -1
            needs_update = True
        if self.hovered_rating != 0:
            self.hovered_rating = 0
            needs_update = True
        if needs_update:
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
        self.image_markers.clear()
        self.selected_images = []
        self.hovered_index = -1
        self.selection_anchor_index = -1
        self._update_size()
        self.update()
