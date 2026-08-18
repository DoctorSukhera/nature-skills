from __future__ import annotations

import re
import unittest
from pathlib import Path

from support import SKILL_ROOT


class ProjectMetadataTests(unittest.TestCase):
    def test_readmes_are_mirrored_without_excluded_preview_assets(self) -> None:
        readme_cn = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (SKILL_ROOT / "README_EN.md").read_text(encoding="utf-8")
        self.assertIn("[English](README_EN.md)", readme_cn)
        self.assertIn("[中文说明](README.md)", readme_en)
        for readme in (readme_cn, readme_en):
            self.assertIn("https://github.com/Paul-Jeo/Image2PPT", readme)
            self.assertIn("config.example.yaml", readme)
            self.assertIn("config.yaml", readme)
            self.assertNotIn("assets/readme/", readme)
        self.assertEqual(
            len(re.findall(r"^## ", readme_cn, flags=re.MULTILINE)),
            len(re.findall(r"^## ", readme_en, flags=re.MULTILINE)),
        )

    def test_public_config_template_contains_no_secret(self) -> None:
        yaml_template = (SKILL_ROOT / "config.example.yaml").read_text(encoding="utf-8")
        self.assertRegex(yaml_template, r'(?m)^PADDLE_OCR_TOKEN:\s*""\s*$')
        self.assertNotIn("sk-", yaml_template)
        self.assertFalse((SKILL_ROOT / ".env.example").exists())

    def test_secret_files_and_generated_runs_are_ignored(self) -> None:
        ignore = (SKILL_ROOT / ".gitignore").read_text(encoding="utf-8")
        patterns = (".env", "config.yaml", "output/", "runs/", "__pycache__/", "assets/readme/", ".github/")
        for pattern in patterns:
            self.assertIn(pattern, ignore)

    def test_openai_metadata_has_required_user_facing_fields(self) -> None:
        metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Nature Image2PPT"', metadata)
        self.assertIn("$nature-image2ppt", metadata)
        match = re.search(r'^\s*short_description:\s*"([^"]+)"', metadata, flags=re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(len(match.group(1)), 25)
        self.assertLessEqual(len(match.group(1)), 64)


if __name__ == "__main__":
    unittest.main()
