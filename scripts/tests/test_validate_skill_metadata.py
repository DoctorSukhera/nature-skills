from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "validate-skill-metadata.py"
SPEC = importlib.util.spec_from_file_location("validate_skill_metadata", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class SkillFrontmatterTests(unittest.TestCase):
    def parse(self, content: str):
        original_root = VALIDATOR.ROOT
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                skill = root / "skills" / "demo" / "SKILL.md"
                skill.parent.mkdir(parents=True)
                skill.write_text(content, encoding="utf-8")
                VALIDATOR.ROOT = root
                return VALIDATOR.parse_skill_frontmatter(skill)
        finally:
            VALIDATOR.ROOT = original_root

    def test_supported_metadata_is_valid(self) -> None:
        frontmatter, errors = self.parse(
            """---
name: demo
description: Demonstrate valid metadata.
license: MIT
metadata:
  author: Example Author
---
"""
        )

        self.assertEqual([], errors)
        self.assertEqual("demo", frontmatter["name"])

    def test_legacy_version_and_author_are_rejected(self) -> None:
        _frontmatter, errors = self.parse(
            """---
name: demo
description: Demonstrate invalid metadata.
version: 1.0.0
author: Example Author
---
"""
        )

        self.assertTrue(any("author, version" in error for error in errors), errors)

    def test_required_fields_must_be_non_empty(self) -> None:
        _frontmatter, errors = self.parse(
            """---
name: ""
metadata:
  author: Example Author
---
"""
        )

        self.assertTrue(any("missing required" in error for error in errors), errors)
        self.assertTrue(any("name must be a non-empty string" in error for error in errors), errors)

    def test_frontmatter_requires_a_closing_fence(self) -> None:
        _frontmatter, errors = self.parse(
            """---
name: demo
description: Missing closing fence.
"""
        )

        self.assertTrue(any("missing its closing" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
