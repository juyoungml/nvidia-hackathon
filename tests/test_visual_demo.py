"""Keep the illustrative bbox UI aligned with its data and disclosure."""

from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VisualDemoTests(unittest.TestCase):
    def test_hotspots_fit_canvas_and_have_provenance(self) -> None:
        hotspots = json.loads((ROOT / "web/hotspots.json").read_text())
        ids = [item["id"] for item in hotspots]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 3)
        for item in hotspots:
            self.assertIn(item["status"], {"observed", "missing", "context"})
            self.assertTrue(item["source"])
            self.assertTrue(item["provenance"])
            x, y, width, height = item["bbox"]
            self.assertTrue(0 <= x < 1 and 0 <= y < 1)
            self.assertTrue(0 < width <= 1 and 0 < height <= 1)
            self.assertLessEqual(x + width, 1)
            self.assertLessEqual(y + height, 1)

    def test_schematic_is_svg_with_stated_role(self) -> None:
        root = ET.parse(ROOT / "web/substation.svg").getroot()
        self.assertTrue(root.tag.endswith("svg"))
        self.assertEqual(root.attrib["viewBox"], "0 0 1200 700")


if __name__ == "__main__":
    unittest.main()
