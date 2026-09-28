"""Every command-line script documents itself and answers ``--help`` offline."""

import ast
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = sorted((ROOT / "scripts").glob("*.py"))


class ScriptsCliTest(unittest.TestCase):
    def test_scripts_exist(self):
        self.assertTrue(SCRIPTS)

    def test_each_script_has_module_docstring(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                docstring = ast.get_docstring(ast.parse(script.read_text()))
                self.assertTrue(docstring and docstring.strip())

    def test_each_script_answers_help(self):
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                result = subprocess.run(
                    [sys.executable, str(script), "--help"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
