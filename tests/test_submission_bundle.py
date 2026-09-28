"""The release is deterministic, explicit, and free of nonpublic inputs."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from submission import build_bundle


class SubmissionBundleTests(unittest.TestCase):
    def test_allowlist_covers_current_demo_and_excludes_outcomes(self) -> None:
        names = set(build_bundle.PUBLIC_FILES + build_bundle.TRACE_FILES + build_bundle.V2_FILES)
        self.assertTrue(
            {
                "poc/system2.py",
                "poc/temporal_tools.py",
                "evaluation/cycle4/RESULTS.md",
                "evaluation/cycle4/traces/domain-29.json",
                "web/system2.html",
                "web/assets/system2-29.json",
                "web/assets/system2-case29-trend.png",
                "submission/slides/Plant_Reliability_Agent_submission.pptx",
                "integrations/nat_live.py",
                "integrations/nat-live-case52.json",
                "evaluation/readiness/SCORECARD.md",
                "evaluation/readiness/content-review/CONTENT_RESULTS.md",
                "evaluation/held-out-32.json",
                "evaluation/held-out-52.json",
                "evaluation/held-out-62.json",
                "uv.lock",
            }.issubset(names)
        )
        self.assertFalse(any("holdout-outcomes" in name for name in names))
        self.assertFalse(any(name.endswith((".pdf", ".mp4", ".zip")) for name in names))
        self.assertEqual(
            len(names),
            len(build_bundle.PUBLIC_FILES + build_bundle.TRACE_FILES + build_bundle.V2_FILES),
        )

    def test_deterministic_archive_manifest_and_private_exclusion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "submission").mkdir()
            (root / "README.md").write_text("Public instructions\n")
            (root / "submission/SUBMISSION_GUIDE.md").write_text("Run demo\n")
            (root / ".env").write_text("NVIDIA_API_KEY=private\n")
            (root / "evaluation/holdout-outcomes").mkdir(parents=True)
            (root / "evaluation/holdout-outcomes/holdout-29.json").write_text("secret")
            output = root / "submission/release.zip"
            with (
                patch.object(build_bundle, "ROOT", root),
                patch.object(
                    build_bundle, "PUBLIC_FILES", ("README.md", "submission/SUBMISSION_GUIDE.md")
                ),
                patch.object(build_bundle, "TRACE_FILES", ()),
                patch.object(build_bundle, "V2_FILES", ()),
            ):
                count, size = build_bundle.build(output)
                first_hash = hashlib.sha256(output.read_bytes()).hexdigest()
                self.assertEqual(count, 3)
                self.assertLess(size, build_bundle.MAX_ZIP_BYTES)
                build_bundle.build(output)
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), first_hash)
                with zipfile.ZipFile(output) as archive:
                    self.assertEqual(
                        archive.namelist(),
                        [
                            "README.md",
                            "submission/SUBMISSION_GUIDE.md",
                            "submission/RELEASE_MANIFEST.json",
                        ],
                    )
                    manifest = json.loads(archive.read(build_bundle.MANIFEST_NAME))
                    self.assertEqual(
                        archive.read(build_bundle.MANIFEST_NAME),
                        (root / build_bundle.MANIFEST_NAME).read_bytes(),
                    )
                    self.assertEqual(
                        [entry["path"] for entry in manifest["files"]],
                        [
                            "README.md",
                            "submission/SUBMISSION_GUIDE.md",
                        ],
                    )
                    self.assertEqual(
                        manifest["files"][0]["sha256"],
                        hashlib.sha256(b"Public instructions\n").hexdigest(),
                    )
                    self.assertEqual(manifest["files"][0]["bytes"], len(b"Public instructions\n"))

                (root / "submission/SUBMISSION_GUIDE.md").write_text(
                    "NVIDIA_API_KEY=" + "abcdefghijklmnop" + "0123456789ABCDEFG\n"
                )
                with self.assertRaisesRegex(ValueError, "Potential secret"):
                    build_bundle.build(output)
                self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), first_hash)
                (root / "submission/SUBMISSION_GUIDE.md").write_text(
                    "Private workspace path: /Users/" + "example/private\n"
                )
                with self.assertRaisesRegex(ValueError, "private path"):
                    build_bundle.build(output)

    def test_rejects_symlink_and_output_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "submission").mkdir()
            (root / "README.md").write_text("public")
            (root / "submission/linked.md").symlink_to("../README.md")
            with (
                patch.object(build_bundle, "ROOT", root),
                patch.object(build_bundle, "PUBLIC_FILES", ("submission/linked.md",)),
                patch.object(build_bundle, "TRACE_FILES", ()),
                patch.object(build_bundle, "V2_FILES", ()),
            ):
                with self.assertRaisesRegex(ValueError, "Symlink"):
                    build_bundle.build(root / "submission/out.zip")
            with patch.object(build_bundle, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "inside repository"):
                    build_bundle.build(root.parent / "outside.zip")


if __name__ == "__main__":
    unittest.main()
