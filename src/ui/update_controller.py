from __future__ import annotations

import logging
import platform
import tempfile
from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QWidget

from src.config.config_manager import ConfigManager
from src.release import update_apply, update_check, update_download, versioning
from src.release.update_check import ReleaseInfo, UpdateCheckError
from src.ui.dialogs.update_dialog import UpdateDialog
from src.ui.progress_reporter import CancellableProgressReporter


class CheckWorker(QThread):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            self.succeeded.emit(update_check.fetch_latest_release())
        except UpdateCheckError as error:
            self.failed.emit(str(error))


class DownloadWorker(QThread):
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)
    progressed = pyqtSignal(int, int)

    def __init__(self, url: str, destination: Path) -> None:
        super().__init__()
        self._url = url
        self._destination = destination
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            self._download()
        except UpdateCheckError as error:
            self.failed.emit(str(error))

    def _download(self) -> None:
        update_download.download_release_asset(
            self._url,
            self._destination,
            on_progress=self._on_progress,
        )
        if not self._cancelled:
            self.succeeded.emit(str(self._destination))

    def _on_progress(self, done: int, total: int) -> None:
        if self._cancelled:
            raise UpdateCheckError("Download cancelled")
        self.progressed.emit(done, total)


class UpdateController(QObject):
    def __init__(self, parent: QWidget, config: ConfigManager) -> None:
        super().__init__(parent)
        self._parent = parent
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._worker: QThread | None = None
        self._progress: CancellableProgressReporter | None = None
        self._quiet = False
        self._busy = False

    def schedule_startup_check(self) -> None:
        if not update_apply.is_frozen_app():
            return
        if bool(self._config.get("updates.check_on_startup", True)):
            self.check_for_updates(quiet=True)

    def check_for_updates(self, quiet: bool = False) -> None:
        if self._busy:
            return
        self._quiet = quiet
        self._busy = True
        worker = CheckWorker(self)
        self._worker = worker
        worker.succeeded.connect(self._on_check_ok)
        worker.failed.connect(self._on_check_fail)
        worker.finished.connect(self._clear_busy)
        worker.start()

    def _clear_busy(self) -> None:
        self._busy = False
        self._worker = None

    def _on_check_fail(self, message: str) -> None:
        self._logger.warning("%s", message)
        if not self._quiet:
            QMessageBox.warning(self._parent, "Check for Updates", message)

    def _on_check_ok(self, info: object) -> None:
        if not isinstance(info, ReleaseInfo):
            return
        try:
            current = versioning.app_version()
        except (OSError, ValueError) as error:
            self._on_check_fail(str(error))
            return
        self._handle_release(current, info)

    def _handle_release(self, current: str, release: ReleaseInfo) -> None:
        skipped = str(self._config.get("updates.skipped_version", "") or "")
        if update_check.should_offer_update(current, release, skipped):
            self._offer(current, release)
            return
        if not self._quiet:
            QMessageBox.information(
                self._parent,
                "Check for Updates",
                f"DarkLab {current} is up to date.",
            )

    def _offer(self, current: str, release: ReleaseInfo) -> None:
        dialog = UpdateDialog(current, release, self._parent)
        dialog.exec()
        if dialog.choice() == "skip":
            self._config.set("updates.skipped_version", release.version)
            return
        if dialog.choice() == "update":
            self._start_download(release)

    def _start_download(self, release: ReleaseInfo) -> None:
        try:
            filename, url = update_check.select_asset(release)
        except UpdateCheckError as error:
            QMessageBox.warning(self._parent, "Update DarkLab", str(error))
            return
        if not update_apply.is_frozen_app():
            update_apply.open_download_page(url)
            return
        self._download_frozen(filename, url)

    def _download_frozen(self, filename: str, url: str) -> None:
        destination = Path(tempfile.mkdtemp(prefix="darklab-dl-")) / filename
        worker = DownloadWorker(url, destination)
        self._worker = worker
        self._busy = True
        self._progress = CancellableProgressReporter(self._parent, "Downloading update")
        worker.progressed.connect(self._on_progress)
        worker.succeeded.connect(self._on_download_ok)
        worker.failed.connect(self._on_download_fail)
        worker.finished.connect(self._clear_busy)
        worker.start()

    def _on_progress(self, done: int, total: int) -> None:
        if self._progress is not None:
            self._progress(done, max(total, 1), "Downloading update")

    def _on_download_fail(self, message: str) -> None:
        if self._progress is not None:
            self._progress.close()
        QMessageBox.warning(self._parent, "Update DarkLab", message)

    def _on_download_ok(self, path: str) -> None:
        if self._progress is not None:
            self._progress.close()
        try:
            update_apply.apply_update(Path(path))
        except UpdateCheckError as error:
            QMessageBox.warning(self._parent, "Update DarkLab", str(error))
            return
        self._quit_if_replaced()

    def _quit_if_replaced(self) -> None:
        if update_apply.is_frozen_app():
            self._parent.close()
