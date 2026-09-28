"""The demo server must not expose repository or local secret files."""

import unittest

from scripts.serve_demo import ROOT, resolve_demo_path


class DemoServerPathsTest(unittest.TestCase):
    def test_public_assets_are_served(self):
        self.assertEqual(resolve_demo_path("/"), ROOT / "web/index.html")
        self.assertEqual(resolve_demo_path("/web"), ROOT / "web/index.html")
        self.assertEqual(resolve_demo_path("/web/"), ROOT / "web/index.html")
        self.assertEqual(
            resolve_demo_path("/web/investigation.html"), ROOT / "web/investigation.html"
        )
        self.assertEqual(resolve_demo_path("/data/replay-52.json"), ROOT / "data/replay-52.json")
        self.assertEqual(
            resolve_demo_path("/poc/trace-52-pipeline.json"), ROOT / "poc/trace-52-pipeline.json"
        )

    def test_private_and_escaped_paths_are_denied(self):
        for path in (
            "/.env",
            "/.git/config",
            "/evaluation/held-out-52.json",
            "/poc/run.py",
            "/web/../.env",
            "/web/%2e%2e/.env",
            "/web/%2e%2e/evaluation/held-out-52.json",
            "/web/%252e%252e/.env",
            "/web/assets/../../.env",
            "/web/secret.py",
            "/web/.private.png",
        ):
            with self.subTest(path=path):
                self.assertIsNone(resolve_demo_path(path))


if __name__ == "__main__":
    unittest.main()
