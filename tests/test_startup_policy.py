import tempfile
import unittest
from pathlib import Path

from src.catalog.database import create_catalog
from src.catalog.session import remember_catalog
from src.catalog.startup_policy import ASK, FIXED, RECENT, fixed_catalog_error, plan_startup


class StartupPolicyTests(unittest.TestCase):
    def test_ask_ignores_an_existing_recent_catalog(self) -> None:
        catalog = self._catalog("wedding")
        settings = {"startup_mode": ASK, "catalog_path": str(catalog)}
        self.assertEqual(plan_startup(settings), ("ask", None))

    def test_recent_opens_the_last_catalog(self) -> None:
        catalog = self._catalog("wedding")
        settings = {"startup_mode": RECENT, "catalog_path": str(catalog)}
        self.assertEqual(plan_startup(settings), ("open", catalog))

    def test_recent_without_a_file_does_not_ask(self) -> None:
        self.assertEqual(plan_startup({}), ("none", None))
        missing = {"startup_mode": "nope", "catalog_path": "/missing.darklab"}
        self.assertEqual(plan_startup(missing), ("none", None))

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
