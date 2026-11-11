import unittest

from src.release import downloads


class ReleaseDownloadsTests(unittest.TestCase):
    def test_release_tag_valid(self) -> None:
        self.assertEqual(downloads.release_tag("1.0.7"), "v1.0.7")

    def test_release_tag_invalid(self) -> None:
        with self.assertRaises(ValueError):
            downloads.release_tag("1.0")

    def test_release_notes_mentions_three_platforms(self) -> None:
        notes = downloads.release_notes("2.0.0")
        self.assertIn("macOS", notes)
        self.assertIn("Linux", notes)
        self.assertIn("Windows", notes)

    def test_download_url(self) -> None:
        url = downloads.download_url("v1.0.7", downloads.MAC_ASSET)
        self.assertIn("fgalyasz/DarkLab", url)
        self.assertTrue(url.endswith(downloads.MAC_ASSET))

    def test_gateway_html_lists_assets(self) -> None:
        assets = [("macOS", downloads.MAC_ASSET), ("Linux", downloads.LINUX_ASSET)]
        html = downloads.gateway_html("1.0.7", assets)
        self.assertIn(downloads.MAC_ASSET, html)
        self.assertIn(downloads.LINUX_ASSET, html)

    def test_platforms_for_paths_filters_missing(self) -> None:
        present = {
            downloads.MAC_ASSET: True,
            downloads.LINUX_ASSET: False,
            downloads.WINDOWS_ASSET: True,
        }
        rows = downloads.platforms_for_paths(present)
        names = [filename for _, filename in rows]
        self.assertEqual(names, [downloads.MAC_ASSET, downloads.WINDOWS_ASSET])
