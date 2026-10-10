import unittest

from src.pdlc.outline import parent_key, parse_outline

SAMPLE = """
# Intro

## Epic List

1. Ignored

## Epic 1: Catalog and Import

A shoot lands safely.

### Story 1.1: Create a Catalog

As a Photographer,
I want a Catalog,
So that the shoot has a home.

**Acceptance Criteria:**

**Given** no Catalog
**When** one is created
**Then** a file exists

## Epic 2: Library culling

Grid and marks.

### Story 2.1: Grid

As a Photographer,
I want a grid,
So that I can cull.
"""


class OutlineTests(unittest.TestCase):
    def test_splits_epics_and_stories(self) -> None:
        items = parse_outline(SAMPLE)
        numbers = [item["number"] for item in items]
        self.assertEqual(numbers, ["1", "1.1", "2", "2.1"])

    def test_epic_body_stops_before_story(self) -> None:
        epic = parse_outline(SAMPLE)[0]
        self.assertEqual(epic["title"], "Catalog and Import")
        self.assertIn("A shoot lands safely.", epic["body"])
        self.assertNotIn("Story 1.1", epic["body"])

    def test_preamble_is_ignored(self) -> None:
        titles = [item["title"] for item in parse_outline(SAMPLE)]
        self.assertNotIn("Intro", titles)
        self.assertNotIn("Epic List", titles)

    def test_parent_key(self) -> None:
        story = parse_outline(SAMPLE)[1]
        self.assertIsNone(parent_key(parse_outline(SAMPLE)[0]))
        self.assertEqual(parent_key(story), "1")

    def test_unheaded_text_returns_nothing(self) -> None:
        self.assertEqual(parse_outline("no headings here"), [])
