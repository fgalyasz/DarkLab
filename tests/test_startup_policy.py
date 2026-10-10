import tempfile
import unittest
from pathlib import Path

from src.catalog.database import create_catalog
from src.catalog.session import remember_catalog
from src.catalog.startup_policy import ASK, FIXED, RECENT, fixed_catalog_error, plan_startup, require_catalog


class Choice:
    def __init__(self, path: Path | None) -> None:
        self.path = path

    def pick(self) -> Path | None:
        return self.path


class StartupPolicyTests(unittest.TestCase):
    def test_ask_ignores_an_existing_recent_catalog(self) -> None:
        catalog = self._catalog("wedding")
        settings = {"startup_mode": ASK, "catalog_path": str(catalog)}
        self.assertEqual(plan_startup(settings), ("ask", None))

    def test_recent_opens_the_last_catalog(self) -> None:
        catalog = self._catalog("wedding")
        settings = {"startup_mode": RECENT, "catalog_path": str(catalog)}
        self.assertEqual(plan_startup(settings), ("open", catalog))

    def test_recent_without_a_file_must_choose(self) -> None:
        self.assertEqual(plan_startup({}), ("ask", None))
        missing = {"startup_mode": "nope", "catalog_path": "/missing.darklab"}
        self.assertEqual(plan_startup(missing), ("ask", None))

    def test_require_catalog_skips_the_chooser_when_one_exists(self) -> None:
        catalog = self._catalog("wedding")
        settings = {"startup_mode": RECENT, "catalog_path": str(catalog)}
        self.assertEqual(require_catalog(settings, self._refuse_choice), catalog)

    def test_require_catalog_uses_the_chooser_or_quits(self) -> None:
        chosen = self._catalog("wedding")
        self.assertEqual(require_catalog({}, Choice(chosen).pick), chosen)
        self.assertIsNone(require_catalog({}, Choice(None).pick))

    def _refuse_choice(self) -> Path | None:
        raise AssertionError("chooser should not run")

    def test_fixed_opens_the_pinned_file(self) -> None:
        pinned = self._catalog("wedding")
        other = self._catalog("personal")
        settings = {"startup_mode": FIXED, "fixed_catalog": str(pinned), "catalog_path": str(other)}
        self.assertEqual(plan_startup(settings), ("open", pinned))

    def test_missing_pin_asks(self) -> None:
        settings = {"startup_mode": FIXED, "fixed_catalog": "/missing.darklab"}
        self.assertEqual(plan_startup(settings), ("ask", None))

    def test_fixed_path_must_exist(self) -> None:
        self.assertEqual(fixed_catalog_error(""), "Choose a catalog file.")
        self.assertEqual(fixed_catalog_error("/missing.darklab"), "That catalog file does not exist.")
        catalog = self._catalog("wedding")
        self.assertIsNone(fixed_catalog_error(str(catalog)))

    def test_remember_does_not_change_the_pin(self) -> None:
        settings = {"startup_mode": FIXED, "fixed_catalog": "/pin.darklab", "catalog_path": "/old.darklab"}
        updated = remember_catalog(settings, Path("/new.darklab"))
        self.assertEqual(updated["startup_mode"], FIXED)
        self.assertEqual(updated["fixed_catalog"], "/pin.darklab")
        self.assertEqual(updated["catalog_path"], "/new.darklab")

    def _catalog(self, name: str) -> Path:
        return create_catalog(Path(tempfile.mkdtemp()) / name)
