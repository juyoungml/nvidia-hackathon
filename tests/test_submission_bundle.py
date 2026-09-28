"""Verify the submission archive contains only reviewed public inputs."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from submission import build_bundle


class SubmissionBundleTests(unittest.TestCase):
    def test_manifest_covers_offline_demo_and_has_no_missing_files(self) -> None:
        root = build_bundle.ROOT
        files = build_bundle.public_files(
            root / "submission/Plant_Reliability_Agent_review.pdf",
            root / "submission/submission.zip",
        )
        for path in files:
            build_bundle.check_file(path)
        included = {path.relative_to(root).as_posix() for path in files}
        self.assertTrue(
            {
                "README.md",
                "pyproject.toml",
                "uv.lock",
                "scripts/serve_demo.py",
                "web/index.html",
                "web/investigation.html",
                "web/investigation.js",
                "web/assets/doe-steam-figure-1.png",
                "poc/trace-52-pipeline.json",
                "poc/trace-52-nvidia-nemotron-3-ultra-550b-a55b.json",
                "data/replay-52.json",
                "evaluation/results/comparison.json",
            }.issubset(included)
        )
        self.assertFalse(
            any(part.startswith(".") for name in included for part in Path(name).parts)
        )

    def test_archive_ignores_unlisted_private_files_and_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "submission").mkdir()
            (root / "README.md").write_text("Public instructions\n")
            (root / "submission/report.pdf").write_bytes(b"%PDF-1.4\n")
            (root / ".env").write_text("NVIDIA_API_KEY=private\n")
            (root / "data").mkdir()
            (root / "data/private.json").write_text('{"secret": true}\n')
            (root / "submission/build_demo_video.py").write_text("# Rebuild the public demo\n")
            (root / "submission/demo_walkthrough.mp4").write_bytes(b"public video")
            output = root / "submission/submission.zip"
            with (
                patch.object(build_bundle, "ROOT", root),
                patch.object(build_bundle, "PUBLIC_FILES", ("README.md",)),
            ):
                count, size = build_bundle.build(root / "submission/report.pdf", output)
                self.assertEqual(count, 4)
                self.assertLess(size, build_bundle.MAX_ZIP_BYTES)
                with zipfile.ZipFile(output) as archive:
                    self.assertEqual(
                        archive.namelist(),
                        [
                            "README.md",
                            "submission/build_demo_video.py",
                            "submission/demo_walkthrough.mp4",
                            "submission/report.pdf",
                        ],
                    )

                (root / "submission/link.pdf").symlink_to("report.pdf")
                with self.assertRaisesRegex(ValueError, "Symlink"):
                    build_bundle.build(root / "submission/link.pdf", output)
                self.assertTrue(output.is_file())

                (root / "submission/linked-output.zip").symlink_to("submission.zip")
                with self.assertRaisesRegex(ValueError, "Symlink"):
                    build_bundle.build(
                        root / "submission/report.pdf", root / "submission/linked-output.zip"
                    )

                with self.assertRaises(ValueError):
                    build_bundle.build(
                        root / "submission/../data/private.json", root / "submission/other.zip"
                    )


if __name__ == "__main__":
    unittest.main()
