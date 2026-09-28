"""The demo server must not expose repository or local secret files."""

import unittest

from scripts.serve_demo import PUBLIC_FILES, ROOT, resolve_demo_path
from submission.build_bundle import PUBLIC_FILES as BUNDLE_FILES


class DemoServerPathsTest(unittest.TestCase):
    def test_server_only_lists_release_files(self):
        self.assertTrue(PUBLIC_FILES.issubset(set(BUNDLE_FILES)))

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
        for public in (
            "web/system2.html",
            "web/system2.css",
            "web/system2.js",
            "web/assets/system2-29.json",
            "web/assets/system2-52.json",
            "web/assets/system2-case29-trend.png",
            "submission/SUBMISSION_GUIDE.md",
            "submission/slides/Plant_Reliability_Agent_submission.pptx",
        ):
            self.assertEqual(resolve_demo_path("/" + public), ROOT / public)

    def test_private_and_escaped_paths_are_denied(self):
        for path in (
            "/.env",
            "/.git/config",
            "/evaluation/held-out-52.json",
            "/evaluation/held-out-32.json",
            "/evaluation/held-out-62.json",
            "/poc/run.py",
            "/web/../.env",
            "/web/%2e%2e/.env",
            "/web/%2e%2e/evaluation/held-out-52.json",
            "/web/%252e%252e/.env",
            "/web/assets/../../.env",
            "/web/secret.py",
            "/web/secret.json",
            "/web/assets/unreviewed.json",
            "/evaluation/cycle4/results.json",
            "/evaluation/holdout-outcomes/holdout-29.json",
            "/submission/build_bundle.py",
            "/web/.private.png",
        ):
            with self.subTest(path=path):
                self.assertIsNone(resolve_demo_path(path))


if __name__ == "__main__":
    unittest.main()
