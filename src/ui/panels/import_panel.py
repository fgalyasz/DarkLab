"""
Import Panel for Photo Editor
Wraps the existing import workflow UI.
"""

from src.config.config_manager import ConfigManager
from src.ui.panels.library_panel import LibraryPanel


class ImportPanel(LibraryPanel):
    """Import panel using the existing library import workflow."""

    IMPORT_PRESET_CONFIG_KEY = "panels.import.import_settings"
    LEGACY_IMPORT_PRESET_CONFIG_KEY = "panels.library.import_settings"

    def __init__(self):
        self._migrate_legacy_import_config()
        super().__init__()
        self.panel_name = "import"
        if hasattr(self, "title_label") and self.title_label is not None:
            self.title_label.setText("Import")

    def _migrate_legacy_import_config(self) -> None:
        config_manager = ConfigManager()
        current_import_config = config_manager.get(self.IMPORT_PRESET_CONFIG_KEY)
        legacy_import_config = config_manager.get(self.LEGACY_IMPORT_PRESET_CONFIG_KEY)

        if isinstance(current_import_config, dict) and current_import_config:
            return
        if not isinstance(legacy_import_config, dict) or not legacy_import_config:
            return

        config_manager.set(self.IMPORT_PRESET_CONFIG_KEY, legacy_import_config)
