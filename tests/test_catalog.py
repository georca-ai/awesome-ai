import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(ROOT / "data", self.root / "data")
        shutil.copytree(ROOT / "scripts", self.root / "scripts")

    def run_catalog(self, *args):
        return subprocess.run(
            [sys.executable, "scripts/build_catalog.py", *args],
            cwd=self.root, capture_output=True, text=True,
        )

    def edit_json(self, path, edit):
        path = self.root / "data" / path
        payload = json.loads(path.read_text(encoding="utf-8"))
        edit(payload)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_generation_and_stale_output(self):
        result = self.run_catalog()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_catalog("--check").returncode, 0)
        page = self.root / "docs/ja/README.md"
        self.assertIn("[English](../../README.md)", page.read_text())
        page.write_text("stale")
        result = self.run_catalog("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("docs/ja/README.md", result.stderr)
        self.assertEqual(page.read_text(), "stale")

    def test_missing_translation_prevents_writes(self):
        self.edit_json("locales/ja.json", lambda data: data["tools"].pop("chatgpt"))
        result = self.run_catalog()
        self.assertEqual(result.returncode, 1)
        self.assertIn("ja", result.stderr)
        self.assertIn("chatgpt", result.stderr)
        self.assertFalse((self.root / "README.md").exists())

    def test_duplicate_tool(self):
        self.edit_json("catalog.json", lambda data: data["tools"].append(data["tools"][0]))
        result = self.run_catalog()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Duplicate tool ID: chatgpt", result.stderr)

    def test_unknown_category(self):
        self.edit_json("catalog.json", lambda data: data["tools"][0].update(category="other"))
        result = self.run_catalog()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown category for chatgpt: other", result.stderr)
